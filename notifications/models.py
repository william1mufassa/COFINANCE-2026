from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('CREDIT_STATUS', 'Changement de statut crédit'),
        ('PAYMENT', 'Remboursement enregistré'),
        ('INSURANCE', 'Assurance mobile'),
        ('CHAT', 'Chat support'),
        ('ALERT', 'Alerte générale'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    related_object_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification #{self.id} for {self.recipient.username} - {self.title}"
