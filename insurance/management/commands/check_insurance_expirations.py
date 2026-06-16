from django.core.management.base import BaseCommand
from datetime import date, timedelta
from insurance.models import InsuranceSubscription
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Checks for active insurance subscriptions expiring in 15 days and notifies clients'

    def handle(self, *args, **kwargs):
        today = date.today()
        target_date = today + timedelta(days=15)
        
        subscriptions = InsuranceSubscription.objects.filter(
            end_date=target_date,
            status='ACTIVE',
            notification_sent_15days=False
        )
        
        count = 0
        for sub in subscriptions:
            Notification.objects.create(
                recipient=sub.client,
                title="Expiration d'assurance imminente (J-15)",
                message=(
                    f"Votre assurance {sub.product.name} (N° de police : {sub.policy_number}) "
                    f"expirera dans 15 jours, soit le {sub.end_date}. "
                    f"Pensez à la renouveler en ligne pour rester couvert."
                ),
                notification_type='INSURANCE',
                related_object_id=sub.id
            )
            sub.notification_sent_15days = True
            sub.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f"[OK] {count} alertes de fin d'assurance (J-15) envoyees."))
