from rest_framework import serializers
from .models import InsuranceProduct, InsuranceSubscription
from accounts.serializers import UserProfileSerializer
from dateutil.relativedelta import relativedelta
from datetime import date

class InsuranceProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceProduct
        fields = ('id', 'name', 'description', 'coverage_type', 'monthly_premium', 'coverage_amount', 'duration_months', 'is_active')

class InsuranceSubscriptionSerializer(serializers.ModelSerializer):
    client = UserProfileSerializer(read_only=True)
    product_details = InsuranceProductSerializer(source='product', read_only=True)

    class Meta:
        model = InsuranceSubscription
        fields = (
            'id', 'client', 'product', 'product_details', 'start_date', 
            'end_date', 'status', 'beneficiary_name', 'beneficiary_phone', 
            'policy_number', 'created_at'
        )
        read_only_fields = ('id', 'client', 'end_date', 'status', 'policy_number', 'created_at')

    def create(self, validated_data):
        request = self.context['request']
        client = request.user
        product = validated_data['product']
        start_date = validated_data.get('start_date', date.today())
        
        # Calculate end_date based on product duration
        end_date = start_date + relativedelta(months=product.duration_months)
        
        # Generate unique policy number
        last_sub = InsuranceSubscription.objects.order_by('-id').first()
        next_id = (last_sub.id + 1) if last_sub else 1
        policy_number = f"COFCI-ASSUR{next_id:04d}-{start_date.year}"

        sub = InsuranceSubscription.objects.create(
            client=client,
            product=product,
            start_date=start_date,
            end_date=end_date,
            beneficiary_name=validated_data['beneficiary_name'],
            beneficiary_phone=validated_data['beneficiary_phone'],
            policy_number=policy_number,
            status='ACTIVE'
        )
        
        # Notify the client
        from notifications.models import Notification
        Notification.objects.create(
            recipient=client,
            title="Souscription d'assurance confirmée",
            message=f"Votre souscription au produit {product.name} (N° de police : {policy_number}) a été activée.",
            notification_type='INSURANCE',
            related_object_id=sub.id
        )

        return sub
