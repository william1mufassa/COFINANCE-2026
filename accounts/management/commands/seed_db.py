from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from credits.models import CreditRequest, RepaymentSchedule, Payment
from credits.utils import generate_repayment_schedule
from insurance.models import InsuranceProduct, InsuranceSubscription
from chat.models import Conversation, Message
from decimal import Decimal
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with demonstration data for COFINANCE CI'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database...")

        # 1. Clean existing data
        self.stdout.write("Cleaning old records...")
        User.objects.all().delete()
        CreditRequest.objects.all().delete()
        InsuranceProduct.objects.all().delete()
        # Cascade takes care of schedules, payments, subscriptions, and messages

        # 2. Create Users
        self.stdout.write("Creating accounts...")
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@cofinci.ci',
            password='Admin1234!',
            role='ADMIN',
            first_name='Admin',
            last_name='COFINANCE'
        )
        
        agent = User.objects.create_user(
            username='agent1',
            email='agent@cofinci.ci',
            password='Agent1234!',
            role='AGENT',
            first_name='Kouassi',
            last_name='Koffi'
        )
        
        client = User.objects.create_user(
            username='client1',
            email='client@cofinci.ci',
            password='Client1234!',
            role='CLIENT',
            first_name='Aya',
            last_name="N'Guessan",
            phone='0707070707',
            region='Abidjan',
            id_number='CI00012345',
            is_verified=True
        )

        # 3. Create Insurance Products
        self.stdout.write("Creating insurance products...")
        prod_vie = InsuranceProduct.objects.create(
            name='Assurance Vie Essentielle',
            description='Garantit le versement d\'un capital en cas de décès ou d\'invalidité pour protéger vos proches.',
            coverage_type='VIE',
            monthly_premium=Decimal('2500.00'),
            coverage_amount=Decimal('500000.00'),
            duration_months=12
        )

        prod_deces = InsuranceProduct.objects.create(
            name='Sécurité Décès-Invalidité',
            description='Une couverture complète et sur-mesure pour faire face aux imprévus de la vie.',
            coverage_type='DÉCÈS_INVALIDITÉ',
            monthly_premium=Decimal('4000.00'),
            coverage_amount=Decimal('1000000.00'),
            duration_months=12
        )

        # 4. Create Credit Requests
        self.stdout.write("Creating credit requests and schedules...")
        credit = CreditRequest.objects.create(
            client=client,
            amount=Decimal('150000.00'),
            duration_months=6,
            purpose='Achat de marchandises pour étal commerce de fruits',
            status='DÉCAISSÉE',
            eligibility_score=85,
            agent=agent,
            disbursement_date=date.today() - timedelta(days=30)
        )
        # Generate schedule
        generate_repayment_schedule(credit)

        # 5. Record Payments
        self.stdout.write("Recording a payment...")
        first_schedule = credit.schedules.order_by('installment_number').first()
        Payment.objects.create(
            schedule=first_schedule,
            amount_paid=first_schedule.total_amount,
            payment_date=date.today() - timedelta(days=5),
            payment_method='MOBILE_MONEY',
            transaction_reference='TXN-' + str(random.randint(100000, 999999)),
            recorded_by=agent,
            notes='Premier versement reçu via Orange Money'
        )
        first_schedule.status = 'PAYÉE'
        first_schedule.save()

        # 6. Create Insurance Subscriptions
        self.stdout.write("Creating active subscription...")
        sub_end = date.today() + timedelta(days=335)  # almost 1 year
        InsuranceSubscription.objects.create(
            client=client,
            product=prod_vie,
            start_date=date.today() - timedelta(days=30),
            end_date=sub_end,
            status='ACTIVE',
            beneficiary_name='Koffi N\'Guessan',
            beneficiary_phone='0708080808',
            policy_number='COFCI-ASSUR0001-' + str(date.today().year)
        )

        # 7. Create Support Conversations and Messages
        self.stdout.write("Creating chat conversation history...")
        conv = Conversation.objects.create(
            client=client,
            agent=agent,
            status='OUVERTE',
            subject='Question sur mon taux de remboursement'
        )
        
        Message.objects.create(
            conversation=conv,
            sender=client,
            content='Bonjour, j\'ai une question concernant les pénalités sur mon échéance du mois prochain.'
        )
        
        Message.objects.create(
            conversation=conv,
            sender=agent,
            content='Bonjour Aya ! Je vous écoute. Les pénalités sont de 1% par jour après la date d\'échéance.'
        )

        self.stdout.write(self.style.SUCCESS("[OK] Database seeded successfully!"))
