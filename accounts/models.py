from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('CLIENT', 'Client'),
        ('AGENT', 'Agent de terrain'),
        ('ADMIN', 'Administrateur'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')
    phone = models.CharField(max_length=20, blank=True)
    region = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    id_number = models.CharField(max_length=50, blank=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

