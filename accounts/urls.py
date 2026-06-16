from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, 
    CustomTokenObtainPairView, 
    ProfileView, 
    UserListView, 
    UserDetailView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('admin/users/', UserListView.as_view(), name='user_list'),
    path('admin/users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
]
