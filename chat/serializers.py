from rest_framework import serializers
from .models import Conversation, Message
from accounts.serializers import UserProfileSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserProfileSerializer(read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'conversation', 'sender', 'sender_id', 'content', 'is_read', 'sent_at', 'read_at')
        read_only_fields = ('id', 'conversation', 'sender', 'sender_id', 'is_read', 'sent_at', 'read_at')

class ConversationSerializer(serializers.ModelSerializer):
    client = UserProfileSerializer(read_only=True)
    agent = UserProfileSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ('id', 'client', 'agent', 'status', 'subject', 'created_at', 'closed_at', 'messages')
        read_only_fields = ('id', 'client', 'created_at', 'closed_at')

class ConversationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ('subject',)

class ConversationAssignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ('agent',)
        extra_kwargs = {
            'agent': {'required': True}
        }
