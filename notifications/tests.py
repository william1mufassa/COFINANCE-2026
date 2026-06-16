from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from notifications.models import Notification

User = get_user_model()

class NotificationsTestCase(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client_notif',
            email='client_notif@cofinci.ci',
            password='ClientPassword123!',
            role='CLIENT'
        )
        self.other_user = User.objects.create_user(
            username='other_notif',
            email='other_notif@cofinci.ci',
            password='OtherPassword123!',
            role='CLIENT'
        )
        
        # Create notifications for client_user
        self.n1 = Notification.objects.create(
            recipient=self.client_user,
            title="Notif 1",
            message="Message 1",
            notification_type='ALERT',
            is_read=False
        )
        self.n2 = Notification.objects.create(
            recipient=self.client_user,
            title="Notif 2",
            message="Message 2",
            notification_type='PAYMENT',
            is_read=True
        )
        
        # Create notification for other_user
        self.n3 = Notification.objects.create(
            recipient=self.other_user,
            title="Notif 3",
            message="Message 3",
            notification_type='ALERT',
            is_read=False
        )

        self.list_url = reverse('notification_list')
        self.read_all_url = reverse('notification_mark_all_read')
        self.count_url = reverse('notification_unread_count')

    def test_list_notifications(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only list self notifications (2)
        self.assertEqual(len(response.data), 2)
        
        # Test filtering by is_read=false
        response_unread = self.client.get(self.list_url, {'is_read': 'false'})
        self.assertEqual(response_unread.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_unread.data), 1)
        self.assertEqual(response_unread.data[0]['title'], "Notif 1")

    def test_mark_as_read(self):
        self.client.force_authenticate(user=self.client_user)
        mark_read_url = reverse('notification_mark_read', kwargs={'pk': self.n1.id})
        response = self.client.patch(mark_read_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.n1.refresh_from_db()
        self.assertTrue(self.n1.is_read)

        # Try to mark another user's notification as read (should fail with 404 since it filters by recipient=user)
        mark_other_read_url = reverse('notification_mark_read', kwargs={'pk': self.n3.id})
        response = self.client.patch(mark_other_read_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_all_as_read(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(self.read_all_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.n1.refresh_from_db()
        self.assertTrue(self.n1.is_read)
        self.n2.refresh_from_db()
        self.assertTrue(self.n2.is_read)
        # Verify other user's notification is still unread
        self.n3.refresh_from_db()
        self.assertFalse(self.n3.is_read)

    def test_unread_count(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
