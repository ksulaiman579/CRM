from datetime import datetime, timedelta, timezone
from app.models.ticket import SlaPolicy

def compute_sla_due_dates(policy: SlaPolicy, created_at: datetime | None = None) -> tuple[datetime, datetime]:
    """
    Computes SLA response and resolution due dates based on the given policy.
    Timestamps are in UTC.
    """
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    else:
        # ensure it's timezone-aware UTC
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
            
    response_due = created_at + timedelta(minutes=policy.first_response_mins)
    resolution_due = created_at + timedelta(minutes=policy.resolution_mins)
    
    return response_due, resolution_due

def check_sla_breach(response_due: datetime | None, resolution_due: datetime | None, 
                     first_response_at: datetime | None, resolved_at: datetime | None,
                     current_time: datetime | None = None) -> bool:
    """
    Returns True if the ticket has breached either response or resolution SLA.
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    else:
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
            
    # Check response SLA
    if response_due and not first_response_at:
        if current_time > response_due:
            return True
            
    # Check resolution SLA
    if resolution_due and not resolved_at:
        if current_time > resolution_due:
            return True
            
    return False
