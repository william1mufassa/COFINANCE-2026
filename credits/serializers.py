from rest_framework import serializers
from .models import CreditRequest, CreditDocument, RepaymentSchedule, Payment
from .utils import calculate_eligibility_score, generate_repayment_schedule
from accounts.serializers import UserProfileSerializer
from decimal import Decimal
from datetime import date

class CreditDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditDocument
        fields = ('id', 'credit', 'document_type', 'file', 'uploaded_at')
        read_only_fields = ('id', 'credit', 'uploaded_at')

class RepaymentScheduleSerializer(serializers.ModelSerializer):
    payments = serializers.SerializerMethodField()
    late_penalty = serializers.SerializerMethodField()

    class Meta:
        model = RepaymentSchedule
        fields = ('id', 'installment_number', 'due_date', 'principal_amount', 'interest_amount', 'total_amount', 'status', 'payments', 'late_penalty')

    def get_payments(self, obj) -> list:
        from .serializers_payments import PaymentSerializer
        return PaymentSerializer(obj.payments.all(), many=True).data

    def get_late_penalty(self, obj) -> Decimal:
        # 1% per day if late
        if obj.status != 'PAYÉE' and date.today() > obj.due_date:
            days_late = (date.today() - obj.due_date).days
            return obj.total_amount * Decimal('0.01') * days_late
        return Decimal('0.00')

class CreditRequestSerializer(serializers.ModelSerializer):
    client = UserProfileSerializer(read_only=True)
    agent = UserProfileSerializer(read_only=True)
    documents = CreditDocumentSerializer(many=True, read_only=True)
    schedules = RepaymentScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = CreditRequest
        fields = (
            'id', 'client', 'amount', 'duration_months', 'interest_rate', 
            'purpose', 'status', 'eligibility_score', 'agent', 
            'rejection_reason', 'disbursement_date', 'documents', 
            'schedules', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'client', 'interest_rate', 'status', 
            'eligibility_score', 'agent', 'rejection_reason', 
            'disbursement_date', 'created_at', 'updated_at'
        )

    def create(self, validated_data):
        request = self.context['request']
        client = request.user
        amount = validated_data['amount']
        
        # Calculate eligibility score
        score = calculate_eligibility_score(client, amount)
        
        credit = CreditRequest.objects.create(
            client=client,
            amount=amount,
            duration_months=validated_data['duration_months'],
            purpose=validated_data['purpose'],
            eligibility_score=score,
            status='SOUMISE'
        )
        return credit

class CreditStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditRequest
        fields = ('status', 'rejection_reason', 'disbursement_date', 'agent')

    # Allowed status transitions: {old_status: [allowed_new_statuses]}
    ALLOWED_TRANSITIONS = {
        'SOUMISE':    ['EN_ANALYSE', 'REJETÉE'],
        'EN_ANALYSE': ['APPROUVÉE', 'REJETÉE'],
        'APPROUVÉE':  ['DÉCAISSÉE', 'REJETÉE'],
        'DÉCAISSÉE':  [],
        'REJETÉE':    [],
    }

    def validate(self, attrs):
        new_status = attrs.get('status')
        rejection_reason = attrs.get('rejection_reason')

        if new_status == 'REJETÉE' and not rejection_reason:
            raise serializers.ValidationError({"rejection_reason": "Un motif est requis pour rejeter une demande."})

        if new_status and self.instance:
            old_status = self.instance.status
            allowed = self.ALLOWED_TRANSITIONS.get(old_status, [])
            if new_status != old_status and new_status not in allowed:
                raise serializers.ValidationError({
                    "status": f"Transition '{old_status}' → '{new_status}' non autorisée. "
                              f"Transitions valides depuis '{old_status}' : {allowed or ['aucune']}."
                })

        return attrs

    def update(self, instance, validated_data):
        old_status = instance.status
        instance = super().update(instance, validated_data)
        new_status = instance.status
        
        # Generate (or regenerate) schedule on approval or disbursement.
        # APPROUVÉE→DÉCAISSÉE must also regenerate so due dates use the actual disbursement_date.
        if new_status in ['APPROUVÉE', 'DÉCAISSÉE']:
            if new_status == 'DÉCAISSÉE' and not instance.disbursement_date:
                instance.disbursement_date = date.today()
                instance.save()
            if old_status not in ['APPROUVÉE', 'DÉCAISSÉE'] or new_status == 'DÉCAISSÉE':
                generate_repayment_schedule(instance)
            
            # Send internal notification to client
            from notifications.models import Notification
            Notification.objects.create(
                recipient=instance.client,
                title="Statut de crédit mis à jour",
                message=f"Votre demande de crédit #{instance.id} de {instance.amount} FCFA a été {instance.get_status_display().lower()}.",
                notification_type='CREDIT_STATUS',
                related_object_id=instance.id
            )
            
        elif new_status == 'REJETÉE' and old_status != 'REJETÉE':
            from notifications.models import Notification
            Notification.objects.create(
                recipient=instance.client,
                title="Statut de crédit mis à jour",
                message=f"Votre demande de crédit #{instance.id} a été rejetée. Motif: {instance.rejection_reason}",
                notification_type='CREDIT_STATUS',
                related_object_id=instance.id
            )
            
        return instance
