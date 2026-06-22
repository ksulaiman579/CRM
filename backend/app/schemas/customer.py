from pydantic import BaseModel, EmailStr
from datetime import datetime, date

class CustomerBase(BaseModel):
    account_number: str
    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone_primary: str
    phone_secondary: str | None = None
    national_id: str | None = None
    company_name: str | None = None
    customer_type: str
    status: str = "active"
    segment: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    notes: str | None = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone_primary: str | None = None
    phone_secondary: str | None = None
    status: str | None = None
    segment: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    notes: str | None = None

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class InteractionCreate(BaseModel):
    customer_id: int
    ticket_id: int | None = None
    channel: str
    direction: str | None = None
    subject: str
    notes: str | None = None
    duration_sec: int | None = None

class InteractionResponse(InteractionCreate):
    id: int
    agent_id: int | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class BillingSummary(BaseModel):
    current_balance: float
    last_invoice_amount: float | None
    last_invoice_date: date | None
    overdue_invoices_count: int

class SubscriptionOverview(BaseModel):
    id: int
    plan_name: str
    status: str
    monthly_charge: float
    start_date: date

class CustomerOverviewResponse(BaseModel):
    profile: CustomerResponse
    billing_summary: BillingSummary
    active_subscriptions: list[SubscriptionOverview]
    recent_interactions: list[InteractionResponse]
    open_tickets_count: int
