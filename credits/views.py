from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import CreditRequest, CreditDocument, RepaymentSchedule, Payment
from .serializers import (
    CreditRequestSerializer, 
    CreditDocumentSerializer, 
    RepaymentScheduleSerializer, 
    CreditStatusUpdateSerializer
)
from .serializers_payments import PaymentSerializer, PaymentCreateSerializer
from accounts.permissions import IsClient, IsAgent, IsAdminUser, IsAgentOrAdmin
from django.utils import timezone
from datetime import date
from decimal import Decimal

# --- Credit Request Views ---

class CreditRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = CreditRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            return CreditRequest.objects.all()
        return CreditRequest.objects.filter(client=user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsClient()]
        return super().get_permissions()

class CreditRequestDetailView(generics.RetrieveAPIView):
    serializer_class = CreditRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            return CreditRequest.objects.all()
        return CreditRequest.objects.filter(client=user)

class CreditStatusUpdateView(generics.UpdateAPIView):
    queryset = CreditRequest.objects.all()
    serializer_class = CreditStatusUpdateSerializer
    permission_classes = (IsAgentOrAdmin,)

class AdminCreditListView(generics.ListAPIView):
    queryset = CreditRequest.objects.all()
    serializer_class = CreditRequestSerializer
    permission_classes = (IsAgentOrAdmin,)

class CreditDocumentUploadView(generics.CreateAPIView):
    serializer_class = CreditDocumentSerializer
    permission_classes = (IsClient,)

    def perform_create(self, serializer):
        credit_id = self.kwargs.get('credit_id')
        credit = get_object_or_404(CreditRequest, id=credit_id, client=self.request.user)
        serializer.save(credit=credit)

class CreditScheduleView(generics.ListAPIView):
    serializer_class = RepaymentScheduleSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        credit_id = self.kwargs.get('credit_id')
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            credit = get_object_or_404(CreditRequest, id=credit_id)
        else:
            credit = get_object_or_404(CreditRequest, id=credit_id, client=user)
        return credit.schedules.all()

# --- Repayments & Payments Views ---

class PaymentListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentCreateSerializer
        return PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(schedule__credit__client=user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAgentOrAdmin()]
        return super().get_permissions()

class CreditRepaymentHistoryView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        credit_id = self.kwargs.get('credit_id')
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            credit = get_object_or_404(CreditRequest, id=credit_id)
        else:
            credit = get_object_or_404(CreditRequest, id=credit_id, client=user)
        return Payment.objects.filter(schedule__credit=credit)

class OverdueSchedulesListView(generics.ListAPIView):
    serializer_class = RepaymentScheduleSerializer
    permission_classes = (IsAgentOrAdmin,)

    def get_queryset(self):
        # Update overdue statuses on demand
        schedules = RepaymentSchedule.objects.filter(
            status='EN_ATTENTE',
            due_date__lt=date.today()
        )
        schedules.update(status='EN_RETARD')
        return RepaymentSchedule.objects.filter(status='EN_RETARD')

class PaymentReceiptView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(schedule__credit__client=user)
