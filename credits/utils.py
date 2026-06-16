from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from dateutil.relativedelta import relativedelta

def calculate_eligibility_score(client, amount):
    """
    Calculates an eligibility score from 0 to 100.
    Score >= 70 represents approval target.
    """
    score = 0
    
    # 1. Profile completeness & Verification (max 20 points)
    if client.is_verified:
        score += 10
    if client.phone and client.id_number:
        score += 10

    # 2. History of credit requests (max 40 points)
    # Check all requested credits for the client
    past_credits = client.credits_requested.all()
    if not past_credits.exists():
        # Baseline score for new clients
        score += 25
    else:
        # Check for active late payments
        from .models import RepaymentSchedule
        has_late = RepaymentSchedule.objects.filter(
            credit__client=client,
            status='EN_RETARD'
        ).exists()
        
        if has_late:
            score += 0  # Severe penalty
        else:
            # Check if they have successfully repaid a credit before
            has_completed = past_credits.filter(status='DÉCAISSÉE').exists()
            if has_completed:
                score += 40
            else:
                score += 30

    # 3. Request amount evaluation (max 20 points)
    # COFINANCE CI typical microcrédits are usually between 50,000 and 2,000,000 FCFA
    amount_dec = Decimal(str(amount))
    if amount_dec <= Decimal('200000'):
        score += 20
    elif amount_dec <= Decimal('500000'):
        score += 15
    elif amount_dec <= Decimal('1000000'):
        score += 10
    else:
        score += 5

    # 4. Region & demographics (max 20 points)
    # Major regions get higher score due to agent availability
    if client.region in ['Abidjan', 'Abidjan-Plateau', 'Bouaké', 'Yamoussoukro']:
        score += 20
    elif client.region:
        score += 15
    else:
        score += 5

    # Ensure score is capped between 0 and 100
    return max(0, min(100, score))


def generate_repayment_schedule(credit):
    """
    Generates the repayment schedule for a CreditRequest.
    Uses flat interest rate calculation.
    """
    from .models import RepaymentSchedule
    
    # Clean any existing schedules just in case
    credit.schedules.all().delete()
    
    duration = credit.duration_months
    amount = Decimal(str(credit.amount))
    monthly_rate = Decimal(str(credit.interest_rate)) / Decimal('100.00')
    
    # Simple Flat Interest Rate model:
    # Principal paid per month = total amount / duration
    # Interest paid per month = total amount * monthly_rate
    # Total monthly = principal + interest
    principal_per_month = amount / Decimal(str(duration))
    interest_per_month = amount * monthly_rate
    total_per_month = principal_per_month + interest_per_month
    
    # Starting date (default to today if disbursement_date not set)
    start_date = credit.disbursement_date or date.today()
    
    schedules = []
    for i in range(1, duration + 1):
        # Calculate due date: +i months from start_date
        due_date = start_date + relativedelta(months=i)
        
        schedules.append(
            RepaymentSchedule(
                credit=credit,
                installment_number=i,
                due_date=due_date,
                principal_amount=principal_per_month,
                interest_amount=interest_per_month,
                total_amount=total_per_month,
                status='EN_ATTENTE'
            )
        )
        
    RepaymentSchedule.objects.bulk_create(schedules)
