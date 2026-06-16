from django.urls import path
from .views import (
    AdminConversationListView,
    AdminConversationAssignView
)

urlpatterns = [
    path('conversations/', AdminConversationListView.as_view(), name='admin_conversation_list'),
    path('conversations/<int:pk>/assign/', AdminConversationAssignView.as_view(), name='admin_conversation_assign'),
]
