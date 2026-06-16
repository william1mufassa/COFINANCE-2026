from django.urls import path
from .views import (
    CreditRequestListCreateView,
    CreditRequestDetailView,
    CreditStatusUpdateView,
    CreditScheduleView,
    CreditDocumentUploadView,
    AdminCreditListView,
)

urlpatterns = [
    path('', CreditRequestListCreateView.as_view(), name='credit_list_create'),
    path('<int:pk>/', CreditRequestDetailView.as_view(), name='credit_detail'),
    path('<int:pk>/status/', CreditStatusUpdateView.as_view(), name='credit_status_update'),
    path('<int:credit_id>/schedule/', CreditScheduleView.as_view(), name='credit_schedule'),
    path('<int:credit_id>/documents/', CreditDocumentUploadView.as_view(), name='credit_document_upload'),
    path('admin/list/', AdminCreditListView.as_view(), name='admin_credit_list'),
]
