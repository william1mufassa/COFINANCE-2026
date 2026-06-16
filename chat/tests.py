from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from chat.models import Conversation, Message

User = get_user_model()

class ChatTestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_chat',
            email='admin_chat@cofinci.ci',
            password='AdminPassword123!',
            role='ADMIN'
        )
        self.agent = User.objects.create_user(
            username='agent_chat',
            email='agent_chat@cofinci.ci',
            password='AgentPassword123!',
            role='AGENT'
        )
        self.client_user = User.objects.create_user(
            username='client_chat',
            email='client_chat@cofinci.ci',
            password='ClientPassword123!',
            role='CLIENT'
        )
        
        self.conv_list_url = reverse('conversation_list_create')
        self.admin_conv_list_url = reverse('admin_conversation_list')

    def test_create_and_list_conversation_api(self):
        self.client.force_authenticate(user=self.client_user)
        data = {'subject': 'Problème de connexion'}
        response = self.client.post(self.conv_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['subject'], 'Problème de connexion')
        
        # Verify in database that it was auto-assigned and has status OUVERTE
        conv = Conversation.objects.filter(client=self.client_user).first()
        self.assertIsNotNone(conv)
        self.assertEqual(conv.status, 'OUVERTE')
        self.assertEqual(conv.agent, self.agent)
        
        # Verify list contains this new conversation with full serialized details
        response_list = self.client.get(self.conv_list_url)
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_list.data), 1)
        self.assertEqual(response_list.data[0]['status'], 'OUVERTE')

    def test_conversation_detail_and_messages(self):
        conv = Conversation.objects.create(
            client=self.client_user,
            agent=self.agent,
            status='OUVERTE',
            subject='Dépôt non visible'
        )
        Message.objects.create(
            conversation=conv,
            sender=self.client_user,
            content='Bonjour, mon dépôt Orange Money de ce matin n\'est pas encore visible.'
        )
        
        # Access detail
        detail_url = reverse('conversation_detail', kwargs={'pk': conv.id})
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subject'], 'Dépôt non visible')
        
        # Access messages list
        messages_url = reverse('conversation_messages', kwargs={'conversation_id': conv.id})
        response_msg = self.client.get(messages_url)
        self.assertEqual(response_msg.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_msg.data), 1)
        self.assertEqual(response_msg.data[0]['content'], 'Bonjour, mon dépôt Orange Money de ce matin n\'est pas encore visible.')

    def test_close_conversation(self):
        conv = Conversation.objects.create(
            client=self.client_user,
            agent=self.agent,
            status='OUVERTE',
            subject='Dépôt non visible'
        )
        close_url = reverse('conversation_close', kwargs={'pk': conv.id})
        
        self.client.force_authenticate(user=self.client_user)
        response = self.client.patch(close_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conv.refresh_from_db()
        self.assertEqual(conv.status, 'FERMÉE')
        self.assertIsNotNone(conv.closed_at)

    def test_admin_conversation_assign(self):
        # Conversation with no agent (initially EN_ATTENTE if no agent available)
        conv = Conversation.objects.create(
            client=self.client_user,
            agent=None,
            status='EN_ATTENTE',
            subject='Aide requise'
        )
        
        assign_url = reverse('admin_conversation_assign', kwargs={'pk': conv.id})
        
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(assign_url, {'agent': self.agent.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        conv.refresh_from_db()
        self.assertEqual(conv.agent, self.agent)
        self.assertEqual(conv.status, 'OUVERTE')
        self.assertTrue(self.agent.notifications.filter(title="Chat support assigné").exists())
