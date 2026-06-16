from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from credits.models import RepaymentSchedule
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Sends payment reminders (J-3) and overdue alerts (J+1) to clients and agents'

    def handle(self, *args, **kwargs):
        today = date.today()
        
        # --- 1. Reminders (J-3) ---
        target_j3 = today + timedelta(days=3)
        schedules_j3 = RepaymentSchedule.objects.filter(
            due_date=target_j3,
            status='EN_ATTENTE'
        )
        
        reminders_sent = 0
        for schedule in schedules_j3:
            Notification.objects.create(
                recipient=schedule.credit.client,
                title="Rappel : Échéance de remboursement à venir",
                message=(
                    f"Bonjour {schedule.credit.client.first_name or schedule.credit.client.username}, "
                    f"votre échéance #{schedule.installment_number} d'un montant de {schedule.total_amount} FCFA "
                    f"arrive à échéance le {schedule.due_date}. Merci de régler via votre agent ou Mobile Money."
                ),
                notification_type='PAYMENT',
                related_object_id=schedule.id
            )
            reminders_sent += 1
            
        self.stdout.write(self.style.SUCCESS(f"[OK] {reminders_sent} rappels de paiement (J-3) envoyes."))

        # --- 2. Overdue Alerts (J+1) ---
        # Mark all pending past due schedules as EN_RETARD
        past_due_schedules = RepaymentSchedule.objects.filter(
            due_date__lt=today,
            status='EN_ATTENTE'
        )
        marked_overdue = past_due_schedules.update(status='EN_RETARD')
        self.stdout.write(self.style.SUCCESS(f"[OK] {marked_overdue} echeances marquees comme 'EN_RETARD'."))

        # Alert for J+1 specifically
        target_j_plus_1 = today - timedelta(days=1)
        schedules_j_plus_1 = RepaymentSchedule.objects.filter(
            due_date=target_j_plus_1,
            status='EN_RETARD'
        )
        
        alerts_sent = 0
        for schedule in schedules_j_plus_1:
            # Notify Client
            Notification.objects.create(
                recipient=schedule.credit.client,
                title="Alerte : Retard de remboursement",
                message=(
                    f"Attention ! Votre echeance #{schedule.installment_number} d'un montant de {schedule.total_amount} FCFA "
                    f"est en retard depuis le {schedule.due_date}. Des penalites de retard s'appliquent."
                ),
                notification_type='ALERT',
                related_object_id=schedule.id
            )
            
            # Notify Agent if assigned
            if schedule.credit.agent:
                Notification.objects.create(
                    recipient=schedule.credit.agent,
                    title="Alerte Agent : Retard client",
                    message=(
                        f"Le client {schedule.credit.client.get_full_name() or schedule.credit.client.username} "
                        f"a une echeance en retard de {schedule.total_amount} FCFA depuis le {schedule.due_date}."
                    ),
                    notification_type='ALERT',
                    related_object_id=schedule.id
                )
            
            alerts_sent += 1
            
        self.stdout.write(self.style.SUCCESS(f"[OK] {alerts_sent} alertes de retard (J+1) envoyees."))
