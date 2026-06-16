from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'sent_at', 'is_read')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'agent', 'status', 'subject', 'created_at', 'closed_at')
    list_filter = ('status',)
    search_fields = ('client__username', 'agent__username', 'subject')
    inlines = [MessageInline]
