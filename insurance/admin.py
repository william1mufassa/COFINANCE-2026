from django.contrib import admin
from .models import InsuranceProduct, InsuranceSubscription


@admin.register(InsuranceProduct)
class InsuranceProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_months', 'monthly_premium', 'coverage_amount', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(InsuranceSubscription)
class InsuranceSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('policy_number', 'client', 'product', 'status', 'start_date', 'end_date', 'notification_sent_15days')
    list_filter = ('status', 'product', 'notification_sent_15days')
    search_fields = ('policy_number', 'client__username', 'client__email')
    readonly_fields = ('policy_number',)
