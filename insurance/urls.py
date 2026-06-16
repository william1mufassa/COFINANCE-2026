from django.urls import path
from .views import (
    InsuranceProductListCreateView,
    InsuranceProductDetailView,
    InsuranceSubscriptionListCreateView,
    InsuranceSubscriptionDetailView,
    AdminInsuranceProductCreateView,
    InsuranceSubscriptionRenewView
)

urlpatterns = [
    # Products
    path('products/', InsuranceProductListCreateView.as_view(), name='product_list_create'),
    path('products/<int:pk>/', InsuranceProductDetailView.as_view(), name='product_detail'),
    path('products/create/', AdminInsuranceProductCreateView.as_view(), name='admin_product_create'),
    
    # Subscriptions
    path('subscriptions/', InsuranceSubscriptionListCreateView.as_view(), name='subscription_list_create'),
    path('subscriptions/<int:pk>/', InsuranceSubscriptionDetailView.as_view(), name='subscription_detail'),
    path('subscriptions/<int:pk>/renew/', InsuranceSubscriptionRenewView.as_view(), name='subscription_renew'),
]
