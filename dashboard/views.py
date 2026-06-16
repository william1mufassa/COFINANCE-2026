from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import serializers as drf_serializers
from django.db.models import Sum, Count, Q
from accounts.permissions import IsAgentOrAdmin
from credits.models import CreditRequest, RepaymentSchedule, Payment
from insurance.models import InsuranceSubscription
from django.apps import apps
from datetime import datetime, date
from decimal import Decimal
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


class DashboardSummaryResponseSerializer(drf_serializers.Serializer):
    volume_by_status = drf_serializers.DictField(child=drf_serializers.IntegerField())
    total_amount_disbursed = drf_serializers.FloatField()
    recovery_rate = drf_serializers.FloatField()
    active_subscriptions = drf_serializers.IntegerField()
    open_conversations = drf_serializers.IntegerField()
    active_clients = drf_serializers.IntegerField()
    overdue_schedules_count = drf_serializers.IntegerField()
    total_due_schedules = drf_serializers.FloatField()
    total_paid_schedules = drf_serializers.FloatField()


class DashboardSummaryView(APIView):
    permission_classes = (IsAgentOrAdmin,)

    @extend_schema(
        summary="Tableau de bord — Statistiques globales",
        description="Retourne les KPIs agrégés : volume de crédits par statut, montant décaissé, taux de recouvrement, souscriptions actives, conversations ouvertes et clients actifs.",
        parameters=[
            OpenApiParameter('start_date', OpenApiTypes.DATE, description='Date de début du filtre (YYYY-MM-DD)'),
            OpenApiParameter('end_date', OpenApiTypes.DATE, description='Date de fin du filtre (YYYY-MM-DD)'),
            OpenApiParameter('agent_id', OpenApiTypes.INT, description="ID de l'agent pour filtrer"),
            OpenApiParameter('region', OpenApiTypes.STR, description='Région pour filtrer'),
        ],
        responses={200: DashboardSummaryResponseSerializer},
        tags=['Dashboard'],
    )
    def get(self, request):
        # Retrieve filters from query parameters
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        agent_id = request.query_params.get('agent_id')
        region = request.query_params.get('region')

        # Base filters
        credit_filters = Q()
        schedule_filters = Q()
        subscription_filters = Q()

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            credit_filters &= Q(created_at__date__gte=start_date)
            schedule_filters &= Q(due_date__gte=start_date)
            subscription_filters &= Q(start_date__gte=start_date)
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            credit_filters &= Q(created_at__date__lte=end_date)
            schedule_filters &= Q(due_date__lte=end_date)
            subscription_filters &= Q(start_date__lte=end_date)
        if agent_id:
            credit_filters &= Q(agent_id=agent_id)
            # schedules belong to credits, so filter by credit's agent
            schedule_filters &= Q(credit__agent_id=agent_id)
        if region:
            credit_filters &= Q(client__region=region)
            schedule_filters &= Q(credit__client__region=region)
            subscription_filters &= Q(client__region=region)

        # 1. Credits volume by status
        credits_by_status = CreditRequest.objects.filter(credit_filters).values('status').annotate(count=Count('id'))
        credits_status_dict = {item['status']: item['count'] for item in credits_by_status}
        for status_choice in ['SOUMISE', 'EN_ANALYSE', 'APPROUVÉE', 'DÉCAISSÉE', 'REJETÉE']:
            credits_status_dict.setdefault(status_choice, 0)

        # 2. Total amount disbursed
        total_disbursed = CreditRequest.objects.filter(credit_filters, status='DÉCAISSÉE').aggregate(Sum('amount'))['amount__sum'] or 0.0

        # 3. Recovery rate (Taux de recouvrement)
        # Ratio of paid amounts on schedules versus total due amounts on schedules
        schedules_filtered = RepaymentSchedule.objects.filter(schedule_filters)
        total_due = schedules_filtered.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        
        # Total payments on these schedules
        total_paid = Payment.objects.filter(schedule__in=schedules_filtered).aggregate(Sum('amount_paid'))['amount_paid__sum'] or Decimal('0.00')
        
        recovery_rate = 100.00
        if total_due > 0:
            recovery_rate = float((total_paid / total_due) * 100)

        # 4. Active subscriptions
        active_subscriptions = InsuranceSubscription.objects.filter(subscription_filters, status='ACTIVE').count()

        # 5. Conversations count (Dynamic import to avoid circular dependency / missing app errors during migrations)
        open_conversations_count = 0
        try:
            Conversation = apps.get_model('chat', 'Conversation')
            open_conversations_count = Conversation.objects.filter(status='OUVERTE').count()
        except (LookupError, ValueError):
            pass

        # 6. Active clients count
        # Clients who have at least one disbursed credit or active subscription
        clients_with_credit = CreditRequest.objects.filter(status='DÉCAISSÉE').values_list('client_id', flat=True)
        clients_with_insurance = InsuranceSubscription.objects.filter(status='ACTIVE').values_list('client_id', flat=True)
        active_clients_count = len(set(list(clients_with_credit) + list(clients_with_insurance)))

        # 7. Late/Overdue schedules count
        overdue_schedules_count = RepaymentSchedule.objects.filter(schedule_filters, status='EN_RETARD').count()

        return Response({
            'volume_by_status': credits_status_dict,
            'total_amount_disbursed': float(total_disbursed),
            'recovery_rate': round(recovery_rate, 2),
            'active_subscriptions': active_subscriptions,
            'open_conversations': open_conversations_count,
            'active_clients': active_clients_count,
            'overdue_schedules_count': overdue_schedules_count,
            'total_due_schedules': float(total_due),
            'total_paid_schedules': float(total_paid)
        })
