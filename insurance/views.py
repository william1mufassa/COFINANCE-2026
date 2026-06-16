from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import InsuranceProduct, InsuranceSubscription
from .serializers import InsuranceProductSerializer, InsuranceSubscriptionSerializer
from accounts.permissions import IsClient, IsAdminUser, IsAgentOrAdmin
from datetime import date
from dateutil.relativedelta import relativedelta
from drf_spectacular.utils import extend_schema

from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class InsuranceProductListCreateView(generics.ListCreateAPIView):
    queryset = InsuranceProduct.objects.filter(is_active=True).order_by('id')
    serializer_class = InsuranceProductSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

class InsuranceProductDetailView(generics.RetrieveAPIView):
    queryset = InsuranceProduct.objects.all()
    serializer_class = InsuranceProductSerializer
    permission_classes = (permissions.IsAuthenticated,)

class InsuranceSubscriptionListCreateView(generics.ListCreateAPIView):
    serializer_class = InsuranceSubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            return InsuranceSubscription.objects.all()
        return InsuranceSubscription.objects.filter(client=user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsClient()]
        return super().get_permissions()

class InsuranceSubscriptionDetailView(generics.RetrieveAPIView):
    serializer_class = InsuranceSubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            return InsuranceSubscription.objects.all()
        return InsuranceSubscription.objects.filter(client=user)

class AdminInsuranceProductCreateView(generics.CreateAPIView):
    queryset = InsuranceProduct.objects.all()
    serializer_class = InsuranceProductSerializer
    permission_classes = (IsAdminUser,)

class InsuranceSubscriptionRenewView(generics.GenericAPIView):
    queryset = InsuranceSubscription.objects.all()
    serializer_class = InsuranceSubscriptionSerializer
    permission_classes = (IsClient,)

    @extend_schema(
        summary="Renouveler une souscription d'assurance",
        description="Permet à un client de renouveler sa souscription d'assurance mobile existante. La nouvelle période commence à la date de fin actuelle ou aujourd'hui si elle est déjà passée.",
        request=None,
        responses={200: InsuranceSubscriptionSerializer},
        tags=['Assurance Mobile'],
    )
    def patch(self, request, pk):
        subscription = get_object_or_404(InsuranceSubscription, id=pk, client=request.user)
        
        # Calculate new dates
        product = subscription.product
        new_start_date = max(subscription.end_date, date.today())
        new_end_date = new_start_date + relativedelta(months=product.duration_months)
        
        subscription.start_date = new_start_date
        subscription.end_date = new_end_date
        subscription.status = 'ACTIVE'
        subscription.notification_sent_15days = False
        subscription.save()

        # Notify
        from notifications.models import Notification
        Notification.objects.create(
            recipient=request.user,
            title="Assurance renouvelée",
            message=f"Votre assurance {product.name} (N° de police : {subscription.policy_number}) a été renouvelée avec succès.",
            notification_type='INSURANCE',
            related_object_id=subscription.id
        )

        serializer = InsuranceSubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)
