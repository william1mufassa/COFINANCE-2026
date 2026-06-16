from django.urls import path
from .views import (
    PaymentListCreateView,
    CreditRepaymentHistoryView,
    OverdueSchedulesListView,
    PaymentReceiptView
)

urlpatterns = [
    path('', PaymentListCreateView.as_view(), name='payment_list_create'),
    path('<int:credit_id>/history/', CreditRepaymentHistoryView.as_view(), name='payment_history'),
    path('overdue/', OverdueSchedulesListView.as_view(), name='payment_overdue'),
    path('<int:pk>/receipt/', PaymentReceiptView.as_view(), name='payment_receipt'),
]
