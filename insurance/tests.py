from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from insurance.models import InsuranceProduct, InsuranceSubscription

User = get_user_model()

class InsuranceTestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_insur',
            email='admin_insur@cofinci.ci',
            password='AdminPassword123!',
            role='ADMIN'
        )
        self.client_user = User.objects.create_user(
            username='client_insur',
            email='client_insur@cofinci.ci',
            password='ClientPassword123!',
            role='CLIENT'
        )
        
        # Create standard product
        self.product = InsuranceProduct.objects.create(
            name='Vie Test',
            description='Test description',
            coverage_type='VIE',
            monthly_premium=Decimal('2500.00'),
            coverage_amount=Decimal('500000.00'),
            duration_months=12
        )
        
        self.product_list_url = reverse('product_list_create')
        self.subscription_list_url = reverse('subscription_list_create')

    def test_list_products_api(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.product_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Vie Test')

    def test_create_subscription_api(self):
        self.client.force_authenticate(user=self.client_user)
        data = {
            'product': self.product.id,
            'beneficiary_name': 'Koffi Test',
            'beneficiary_phone': '0707070707',
            'start_date': str(date.today())
        }
        response = self.client.post(self.subscription_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'ACTIVE')
        self.assertIn('COFCI-ASSUR', response.data['policy_number'])
        self.assertEqual(response.data['end_date'], str(date.today() + relativedelta(months=12)))
        
        # Verify notification
        self.assertTrue(self.client_user.notifications.filter(title="Souscription d'assurance confirmée").exists())

    def test_renew_subscription_api(self):
        sub = InsuranceSubscription.objects.create(
            client=self.client_user,
            product=self.product,
            start_date=date.today() - timedelta(days=365),
            end_date=date.today(),
            status='ACTIVE',
            beneficiary_name='Aya Renew',
            beneficiary_phone='0102030405',
            policy_number='COFCI-TESTRENEW-01'
        )
        
        renew_url = reverse('subscription_renew', kwargs={'pk': sub.id})
        self.client.force_authenticate(user=self.client_user)
        response = self.client.patch(renew_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'ACTIVE')
        # Check that end date is updated to +12 months from today
        expected_end_date = date.today() + relativedelta(months=12)
        self.assertEqual(sub.end_date, expected_end_date)
