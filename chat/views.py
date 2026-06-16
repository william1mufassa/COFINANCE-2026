from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Conversation, Message
from .serializers import (
    ConversationSerializer, 
    ConversationCreateSerializer, 
    ConversationAssignSerializer,
    MessageSerializer
)
from accounts.permissions import IsClient, IsAgentOrAdmin, IsAdminUser
from django.contrib.auth import get_user_model

User = get_user_model()

class ConversationListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            return Conversation.objects.all()
        return Conversation.objects.filter(client=user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsClient()]
        return super().get_permissions()

    def perform_create(self, serializer):
        client = self.request.user
        
        # Simple auto-assignment strategy:
        # Find an agent with role = 'AGENT' (or 'ADMIN')
        available_agent = User.objects.filter(role='AGENT', is_active=True).first()
        if not available_agent:
            # Fallback to an admin
            available_agent = User.objects.filter(role='ADMIN', is_active=True).first()
            
        conv_status = 'OUVERTE' if available_agent else 'EN_ATTENTE'
        
        conv = serializer.save(
            client=client,
            agent=available_agent,
            status=conv_status
        )

        # Send notification to the agent if assigned
        if available_agent:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=available_agent,
                title="Nouveau chat support assigné",
                message=f"Le client {client.username} a ouvert une conversation de chat. Sujet: {conv.subject or 'Support'}",
                notification_type='CHAT',
                related_object_id=conv.id
            )

class ConversationDetailView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            return Conversation.objects.all()
        return Conversation.objects.filter(client=user)

class ConversationMessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = get_object_or_404(Conversation, id=conversation_id, client=user)
        return conversation.messages.all()

class ConversationCloseView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, pk):
        user = request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            conversation = get_object_or_404(Conversation, id=pk)
        else:
            conversation = get_object_or_404(Conversation, id=pk, client=user)

        if conversation.status != 'FERMÉE':
            conversation.status = 'FERMÉE'
            conversation.closed_at = timezone.now()
            conversation.save()
            
            # Notify the client if closed by agent
            if user != conversation.client:
                from notifications.models import Notification
                Notification.objects.create(
                    recipient=conversation.client,
                    title="Conversation de support fermée",
                    message="Votre ticket de support de chat a été fermé par l'agent.",
                    notification_type='CHAT',
                    related_object_id=conversation.id
                )

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminConversationListView(generics.ListAPIView):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = (IsAgentOrAdmin,)

class AdminConversationAssignView(generics.UpdateAPIView):
    queryset = Conversation.objects.all()
    serializer_class = ConversationAssignSerializer
    permission_classes = (IsAdminUser,)

    def perform_update(self, serializer):
        conv = serializer.save()
        if conv.agent:
            conv.status = 'OUVERTE'
            conv.save()
            from notifications.models import Notification
            Notification.objects.create(
                recipient=conv.agent,
                title="Chat support assigné",
                message=f"La conversation #{conv.id} de {conv.client.username} vous a été assignée.",
                notification_type='CHAT',
                related_object_id=conv.id
            )
