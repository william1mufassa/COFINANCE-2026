from django.urls import path
from .views import (
    ConversationListCreateView,
    ConversationDetailView,
    ConversationMessageListView,
    ConversationCloseView
)

urlpatterns = [
    path('conversations/', ConversationListCreateView.as_view(), name='conversation_list_create'),
    path('conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/<int:conversation_id>/messages/', ConversationMessageListView.as_view(), name='conversation_messages'),
    path('conversations/<int:pk>/close/', ConversationCloseView.as_view(), name='conversation_close'),
]
