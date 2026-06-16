from django.db import models
from django.conf import settings
from datetime import date

class InsuranceProduct(models.Model):
    COVERAGE_TYPES = [
        ('VIE', 'Assurance Vie'),
        ('DÉCÈS_INVALIDITÉ', 'Décès et Invalidité'),
        ('MULTIRISQUE', 'Multirisque'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    coverage_type = models.CharField(max_length=20, choices=COVERAGE_TYPES)
    monthly_premium = models.DecimalField(max_digits=12, decimal_places=2)
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.IntegerField(default=12)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Produit d'assurance"
        verbose_name_plural = "Produits d'assurance"

    def __str__(self):
        return f"{self.name} ({self.get_coverage_type_display()})"

class InsuranceSubscription(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRÉE', 'Expirée'),
        ('ANNULÉE', 'Annulée'),
        ('EN_ATTENTE', 'En attente'),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='insurance_subscriptions'
    )
    product = models.ForeignKey(
        InsuranceProduct,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    start_date = models.DateField(default=date.today)
    end_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    beneficiary_name = models.CharField(max_length=200)
    beneficiary_phone = models.CharField(max_length=20)
    policy_number = models.CharField(max_length=50, unique=True)
    notification_sent_15days = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Souscription d'assurance"
        verbose_name_plural = "Souscriptions d'assurance"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.policy_number} - {self.client.username} ({self.product.name})"
