from pydantic import BaseModel
from datetime import datetime


class CallResponse(BaseModel):
    id: int
    call_number: str
    customer_id: int
    team_id: int | None = None
    intent: str
    opening_line: str | None = None
    status: str
    assigned_agent_id: int | None = None
    ticket_id: int | None = None
    notes: str | None = None
    queued_at: datetime | None = None
    answered_at: datetime | None = None
    ended_at: datetime | None = None

    class Config:
        from_attributes = True


class CallComplete(BaseModel):
    notes: str | None = None
    disposition: str = "completed"  # completed | missed | abandoned
    raise_ticket: bool = False
