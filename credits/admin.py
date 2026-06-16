from django.contrib import admin
from .models import CreditRequest, CreditDocument, RepaymentSchedule, Payment


class CreditDocumentInline(admin.TabularInline):
    model = CreditDocument
    extra = 0


class RepaymentScheduleInline(admin.TabularInline):
    model = RepaymentSchedule
    extra = 0
    readonly_fields = ('installment_number', 'due_date', 'principal_amount', 'interest_amount', 'total_amount')


@admin.register(CreditRequest)
class CreditRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'amount', 'duration_months', 'status', 'eligibility_score', 'agent', 'created_at')
    list_filter = ('status', 'agent', 'client__region')
    search_fields = ('client__username', 'client__email', 'id')
    readonly_fields = ('eligibility_score', 'created_at', 'updated_at')
    inlines = [CreditDocumentInline, RepaymentScheduleInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule', 'amount_paid', 'late_penalty', 'payment_method', 'payment_date', 'recorded_by')
    list_filter = ('payment_method',)
    search_fields = ('transaction_reference', 'schedule__credit__client__username')
