from pydantic import BaseModel, Field
from datetime import datetime

class TicketCreate(BaseModel):
    customer_id: int
    subject: str
    description: str | None = None
    category: str
    priority: str = "medium"
    channel: str | None = None
    team_id: int | None = None
    assigned_agent_id: int | None = None

class TicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    category: str | None = None
    assigned_agent_id: int | None = None
    team_id: int | None = None
    csat_rating: int | None = Field(None, ge=1, le=5)
    csat_feedback: str | None = None
    # Optimistic-concurrency token. When provided, the update is rejected
    # (CRM-TKT-005) if it no longer matches the ticket's current version.
    version: int | None = None

class TicketCommentCreate(BaseModel):
    body: str
    is_internal: bool = False

class TicketCommentResponse(TicketCommentCreate):
    id: int
    ticket_id: int
    author_id: int | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class TicketResponse(TicketCreate):
    id: int
    ticket_number: str
    status: str
    sla_policy_id: int | None = None
    first_response_at: datetime | None = None
    sla_response_due: datetime | None = None
    sla_resolution_due: datetime | None = None
    sla_breached: bool
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    csat_rating: int | None = None
    csat_feedback: str | None = None
    created_by: int | None = None
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
