from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class AccountsTestCase(APITestCase):
    def setUp(self):
        # Create standard users for testing
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin_test@cofinci.ci',
            password='AdminPassword123!',
            role='ADMIN'
        )
        
        self.agent = User.objects.create_user(
            username='agent_test',
            email='agent_test@cofinci.ci',
            password='AgentPassword123!',
            role='AGENT'
        )
        
        self.client_user = User.objects.create_user(
            username='client_test',
            email='client_test@cofinci.ci',
            password='ClientPassword123!',
            role='CLIENT',
            phone='0102030405',
            region='Abidjan',
            id_number='CI12345678',
            is_verified=True
        )
        
        # URLs
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile')
        self.admin_users_url = reverse('user_list')

    def test_user_registration(self):
        data = {
            'username': 'new_client',
            'email': 'new_client@cofinci.ci',
            'password': 'NewPassword123!',
            'role': 'CLIENT',
            'phone': '0908070605',
            'region': 'Bouaké',
            'id_number': 'CI98765432'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'new_client')
        self.assertEqual(response.data['role'], 'CLIENT')
        self.assertTrue(User.objects.filter(username='new_client').exists())

    def test_user_registration_duplicate_email(self):
        data = {
            'username': 'another_username',
            'email': 'client_test@cofinci.ci', # Duplicate email
            'password': 'Password123!',
            'role': 'CLIENT'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_login(self):
        data = {
            'username': 'client_test',
            'password': 'ClientPassword123!'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'client_test')
        self.assertEqual(response.data['user']['role'], 'CLIENT')

    def test_get_profile(self):
        # Authenticate first
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'client_test')
        self.assertEqual(response.data['region'], 'Abidjan')

    def test_update_profile(self):
        self.client.force_authenticate(user=self.client_user)
        data = {
            'phone': '0505050505',
            'region': 'Yamoussoukro'
        }
        response = self.client.patch(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.phone, '0505050505')
        self.assertEqual(self.client_user.region, 'Yamoussoukro')

    def test_admin_permissions_on_user_list(self):
        # Client tries to access user list
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.admin_users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin tries to access user list
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.admin_users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 3) # should contain our setup users
