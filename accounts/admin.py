from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'region', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'region')
    search_fields = ('username', 'email', 'phone', 'id_number')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profil COFINANCE', {'fields': ('role', 'phone', 'region', 'date_of_birth', 'id_number', 'is_verified')}),
    )
