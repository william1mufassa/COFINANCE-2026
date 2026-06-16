from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import InsuranceProduct, InsuranceSubscription
from .serializers import InsuranceProductSerializer, InsuranceSubscriptionSerializer
from accounts.permissions import IsClient, IsAdminUser, IsAgentOrAdmin
from datetime import date
from dateutil.relativedelta import relativedelta

class InsuranceProductListCreateView(generics.ListCreateAPIView):
    queryset = InsuranceProduct.objects.filter(is_active=True)
    serializer_class = InsuranceProductSerializer

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

class InsuranceSubscriptionRenewView(APIView):
    permission_classes = (IsClient,)

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
