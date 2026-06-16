from django.db import models
from django.conf import settings
from decimal import Decimal

class CreditRequest(models.Model):
    STATUS_CHOICES = [
        ('SOUMISE', 'Soumise'),
        ('EN_ANALYSE', 'En analyse'),
        ('APPROUVÉE', 'Approuvée'),
        ('DÉCAISSÉE', 'Décaissée'),
        ('REJETÉE', 'Rejetée'),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='credits_requested'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.50'))  # % monthly
    purpose = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='SOUMISE')
    eligibility_score = models.IntegerField(null=True, blank=True)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credits_assigned'
    )
    rejection_reason = models.TextField(null=True, blank=True)
    disbursement_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Demande de crédit"
        verbose_name_plural = "Demandes de crédit"
        ordering = ['-created_at']

    def __str__(self):
        return f"Crédit #{self.id} - {self.client.username} ({self.amount} FCFA)"

class CreditDocument(models.Model):
    DOCUMENT_TYPES = [
        ('CNI', 'Carte Nationale d\'Identité / Passeport'),
        ('JUSTIFICATIF_REVENUS', 'Justificatif de revenus / Relevé'),
        ('AUTRE', 'Autre pièce'),
    ]

    credit = models.ForeignKey(
        CreditRequest,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='credit_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Document justificatif"
        verbose_name_plural = "Documents justificatifs"

    def __str__(self):
        return f"{self.get_document_type_display()} - Crédit #{self.credit.id}"

class RepaymentSchedule(models.Model):
    STATUS_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('PAYÉE', 'Payée'),
        ('EN_RETARD', 'En retard'),
    ]

    credit = models.ForeignKey(
        CreditRequest,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    installment_number = models.IntegerField()
    due_date = models.DateField()
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='EN_ATTENTE')

    class Meta:
        verbose_name = "Échéance de remboursement"
        verbose_name_plural = "Échéances de remboursement"
        ordering = ['installment_number']

    def __str__(self):
        return f"Échéance #{self.installment_number} - Crédit #{self.credit.id} ({self.total_amount} FCFA)"

class Payment(models.Model):
    METHOD_CHOICES = [
        ('MOBILE_MONEY', 'Mobile Money (Orange/Wave/MTN)'),
        ('ESPÈCES', 'Espèces'),
        ('VIREMENT', 'Virement bancaire'),
    ]

    schedule = models.ForeignKey(
        RepaymentSchedule,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    transaction_reference = models.CharField(max_length=100, unique=True, null=True, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments_recorded'
    )
    late_penalty = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-payment_date']

    def __str__(self):
        return f"Paiement #{self.id} - Échéance #{self.schedule.installment_number} ({self.amount_paid} FCFA)"
