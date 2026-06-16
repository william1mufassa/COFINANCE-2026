from django.db import models
from django.conf import settings

class Conversation(models.Model):
    STATUS_CHOICES = [
        ('OUVERTE', 'Ouverte'),
        ('EN_ATTENTE', 'En attente'),
        ('FERMÉE', 'Fermée'),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_conversations'
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_conversations'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='OUVERTE')
    subject = models.CharField(max_length=300, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-created_at']

    def __str__(self):
        agent_name = self.agent.username if self.agent else "aucun agent"
        return f"Chat #{self.id} - Client: {self.client.username} (Agent: {agent_name}) - Statut: {self.status}"

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Message de chat"
        verbose_name_plural = "Messages de chat"
        ordering = ['sent_at']

    def __str__(self):
        return f"Msg #{self.id} in Chat #{self.conversation.id} by {self.sender.username}"
