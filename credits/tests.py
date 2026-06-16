from decimal import Decimal
from datetime import date
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from credits.models import CreditRequest, CreditDocument
from credits.utils import calculate_eligibility_score, generate_repayment_schedule

User = get_user_model()

class CreditsTestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_credits',
            email='admin_credits@cofinci.ci',
            password='AdminPassword123!',
            role='ADMIN'
        )
        self.agent = User.objects.create_user(
            username='agent_credits',
            email='agent_credits@cofinci.ci',
            password='AgentPassword123!',
            role='AGENT'
        )
        self.client_user = User.objects.create_user(
            username='client_credits',
            email='client_credits@cofinci.ci',
            password='ClientPassword123!',
            role='CLIENT',
            phone='0707070707',
            region='Abidjan',
            id_number='CI00012345',
            is_verified=True
        )
        self.credit_list_create_url = reverse('credit_list_create')
        self.payment_list_create_url = reverse('payment_list_create')

    def test_calculate_eligibility_score(self):
        # 1. Verification/Profile completeness: is_verified (+10) + phone & id_number (+10) = 20
        # 2. No history: baseline (+25)
        # 3. Amount <= 200,000 (+20)
        # 4. Region is Abidjan (+20)
        # Total expected: 20 + 25 + 20 + 20 = 85
        score = calculate_eligibility_score(self.client_user, Decimal('150000.00'))
        self.assertEqual(score, 85)

        # Unverified user, empty phone/id, high amount, other region
        unverified_client = User.objects.create_user(
            username='unverified_test',
            email='unverified@test.com',
            password='Password123!',
            role='CLIENT',
            is_verified=False
        )
        score2 = calculate_eligibility_score(unverified_client, Decimal('1500000.00'))
        # 1. Completeness: 0
        # 2. No history: 25
        # 3. High amount (>1,000,000): 5
        # 4. No region: 5
        # Total: 0 + 25 + 5 + 5 = 35
        self.assertEqual(score2, 35)

    def test_generate_repayment_schedule(self):
        credit = CreditRequest.objects.create(
            client=self.client_user,
            amount=Decimal('120000.00'),
            duration_months=6,
            purpose='Test Schedule',
            interest_rate=Decimal('2.50'),
            status='SOUMISE'
        )
        generate_repayment_schedule(credit)
        schedules = credit.schedules.all()
        self.assertEqual(schedules.count(), 6)

        # Flat interest rate calculation:
        # principal = 120000 / 6 = 20000
        # interest = 120000 * 0.025 = 3000
        # total_amount = 23000
        first_schedule = schedules.first()
        self.assertEqual(first_schedule.principal_amount, Decimal('20000.00'))
        self.assertEqual(first_schedule.interest_amount, Decimal('3000.00'))
        self.assertEqual(first_schedule.total_amount, Decimal('23000.00'))
        self.assertEqual(first_schedule.status, 'EN_ATTENTE')

    def test_create_credit_request_api(self):
        self.client.force_authenticate(user=self.client_user)
        data = {
            'amount': '150000.00',
            'duration_months': 6,
            'purpose': 'Dépôt pour achat de fruits et légumes'
        }
        response = self.client.post(self.credit_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'SOUMISE')
        self.assertEqual(response.data['eligibility_score'], 85)
        self.assertEqual(response.data['interest_rate'], '2.50')

    def test_upload_document_api(self):
        self.client.force_authenticate(user=self.client_user)
        credit = CreditRequest.objects.create(
            client=self.client_user,
            amount=Decimal('100000.00'),
            duration_months=3,
            purpose='Test Doc'
        )
        upload_url = reverse('credit_document_upload', kwargs={'credit_id': credit.id})
        
        file = SimpleUploadedFile("cni.jpg", b"dummy_content", content_type="image/jpeg")
        data = {
            'document_type': 'CNI',
            'file': file
        }
        response = self.client.post(upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CreditDocument.objects.filter(credit=credit).exists())

    def test_credit_status_update_api(self):
        self.client.force_authenticate(user=self.client_user)
        credit = CreditRequest.objects.create(
            client=self.client_user,
            amount=Decimal('100000.00'),
            duration_months=3,
            purpose='Status Test'
        )
        
        # Client tries to update status (should fail)
        status_url = reverse('credit_status_update', kwargs={'pk': credit.id})
        response = self.client.patch(status_url, {'status': 'APPROUVÉE'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Agent passe en EN_ANALYSE (SOUMISE → EN_ANALYSE)
        self.client.force_authenticate(user=self.agent)
        response = self.client.patch(status_url, {'status': 'EN_ANALYSE'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        credit.refresh_from_db()
        self.assertEqual(credit.status, 'EN_ANALYSE')

        # Agent approuve (EN_ANALYSE → APPROUVÉE, génère l'échéancier)
        response = self.client.patch(status_url, {'status': 'APPROUVÉE'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        credit.refresh_from_db()
        self.assertEqual(credit.status, 'APPROUVÉE')
        self.assertEqual(credit.schedules.count(), 3)
        self.assertTrue(credit.client.notifications.filter(title="Statut de crédit mis à jour").exists())

        # Transition illégale doit être rejetée (APPROUVÉE → SOUMISE)
        response = self.client.patch(status_url, {'status': 'SOUMISE'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_repayment_payment_and_overdue_api(self):
        # Create approved credit with schedules
        credit = CreditRequest.objects.create(
            client=self.client_user,
            amount=Decimal('100000.00'),
            duration_months=2,
            purpose='Repayment Test',
            status='DÉCAISSÉE',
            disbursement_date=date.today()
        )
        generate_repayment_schedule(credit)
        first_schedule = credit.schedules.first()

        # Agent registers payment
        self.client.force_authenticate(user=self.agent)
        payment_data = {
            'schedule': first_schedule.id,
            'amount_paid': '52500.00', # total is 100000/2 + 2500 = 52500
            'payment_date': str(date.today()),
            'payment_method': 'MOBILE_MONEY',
            'transaction_reference': 'TXN-999999'
        }
        response = self.client.post(self.payment_list_create_url, payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        first_schedule.refresh_from_db()
        self.assertEqual(first_schedule.status, 'PAYÉE')
        self.assertTrue(self.client_user.notifications.filter(title="Remboursement enregistré").exists())
