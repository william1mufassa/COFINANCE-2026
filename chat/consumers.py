import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        # Get token from subprotocol first (Sec-WebSocket-Protocol)
        token_key = None
        subprotocols = self.scope.get('subprotocols', [])
        self.use_subprotocol = False
        
        if len(subprotocols) == 2 and subprotocols[0] == 'token':
            token_key = subprotocols[1]
            self.use_subprotocol = True
        else:
            # Fallback to query string
            query_string = self.scope['query_string'].decode()
            for param in query_string.split('&'):
                if param.startswith('token='):
                    token_key = param.split('=')[1]
                    break

        if token_key:
            self.user = await self.get_user_from_token(token_key)
        else:
            self.user = AnonymousUser()

        if self.user.is_anonymous:
            # Reject connection if unauthorized
            await self.close()
            return

        # Verify if the user is allowed to join this conversation
        is_participant = await self.check_conversation_participant()
        if not is_participant:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Echo back 'token' subprotocol if used
        if self.use_subprotocol:
            await self.accept(subprotocol='token')
        else:
            await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        event_type = data.get('type', 'message')

        if event_type == 'message':
            content = data.get('content')
            if content:
                # Save message to database
                message = await self.save_message(content)
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message_id': message.id,
                        'content': message.content,
                        'sender_id': self.user.id,
                        'sender_username': self.user.username,
                        'sender_role': self.user.role,
                        'sent_at': message.sent_at.isoformat()
                    }
                )
        elif event_type == 'typing':
            # Send typing status to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_typing',
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'is_typing': True
                }
            )
        elif event_type == 'stop_typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_typing',
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'is_typing': False
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'id': event['message_id'],
            'content': event['content'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'sender_role': event['sender_role'],
            'sent_at': event['sent_at']
        }))

    # Receive typing status from room group
    async def chat_typing(self, event):
        # Send typing status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'is_typing': event['is_typing']
        }))

    @database_sync_to_async
    def get_user_from_token(self, token_key):
        try:
            access_token = AccessToken(token_key)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except Exception:
            return AnonymousUser()

    @database_sync_to_async
    def check_conversation_participant(self):
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
            if self.user.is_staff or self.user.role == 'ADMIN':
                return True
            if self.user.role == 'AGENT':
                # Allow only the assigned agent, or any agent if the conversation is unassigned
                return conv.agent is None or conv.agent == self.user
            return conv.client == self.user
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        conv = Conversation.objects.get(id=self.conversation_id)
        return Message.objects.create(
            conversation=conv,
            sender=self.user,
            content=content
        )
