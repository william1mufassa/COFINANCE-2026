from rest_framework import serializers
from .models import Payment, RepaymentSchedule, CreditRequest
from accounts.serializers import UserProfileSerializer
from notifications.models import Notification
from decimal import Decimal
from datetime import date

class PaymentSerializer(serializers.ModelSerializer):
    recorded_by = UserProfileSerializer(read_only=True)
    installment_number = serializers.IntegerField(source='schedule.installment_number', read_only=True)
    credit_id = serializers.IntegerField(source='schedule.credit.id', read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'schedule', 'installment_number', 'credit_id', 
            'amount_paid', 'payment_date', 'payment_method', 
            'transaction_reference', 'recorded_by', 'late_penalty', 'notes'
        )

class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('schedule', 'amount_paid', 'payment_date', 'payment_method', 'transaction_reference', 'notes')

    def validate_schedule(self, value):
        if value.status == 'PAYÉE':
            raise serializers.ValidationError("Cette échéance a déjà été entièrement payée.")
        return value

    def validate(self, attrs):
        schedule = attrs.get('schedule')
        amount_paid = attrs.get('amount_paid')
        
        # Calculate late penalty
        late_penalty = Decimal('0.00')
        if date.today() > schedule.due_date:
            days_late = (date.today() - schedule.due_date).days
            late_penalty = schedule.total_amount * Decimal('0.01') * days_late
        
        attrs['late_penalty'] = late_penalty
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        recorded_by = request.user
        schedule = validated_data['schedule']
        amount_paid = validated_data['amount_paid']
        late_penalty = validated_data['late_penalty']

        # Create the Payment record
        payment = Payment.objects.create(
            schedule=schedule,
            amount_paid=amount_paid,
            payment_date=validated_data['payment_date'],
            payment_method=validated_data['payment_method'],
            transaction_reference=validated_data.get('transaction_reference', ''),
            recorded_by=recorded_by,
            late_penalty=late_penalty,
            notes=validated_data.get('notes', '')
        )

        # Check total payments for this schedule
        total_schedule_paid = sum(p.amount_paid for p in schedule.payments.all())
        required_amount = schedule.total_amount + late_penalty
        
        if total_schedule_paid >= required_amount:
            schedule.status = 'PAYÉE'
        else:
            # Still pending or partial payment
            pass
        schedule.save()

        # Check if all schedules for this credit are paid
        credit = schedule.credit
        all_paid = not credit.schedules.exclude(status='PAYÉE').exists()
        
        # Send Notification to client
        Notification.objects.create(
            recipient=credit.client,
            title="Remboursement enregistré",
            message=f"Votre paiement de {amount_paid} FCFA pour l'échéance #{schedule.installment_number} a été enregistré avec succès.",
            notification_type='PAYMENT',
            related_object_id=payment.id
        )

        if all_paid:
            Notification.objects.create(
                recipient=credit.client,
                title="Crédit entièrement soldé",
                message=f"Félicitations ! Votre crédit #{credit.id} a été entièrement remboursé.",
                notification_type='CREDIT_STATUS',
                related_object_id=credit.id
            )

        return payment
