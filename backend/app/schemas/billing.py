from pydantic import BaseModel
from datetime import date, datetime

class LineItemResponse(BaseModel):
    id: int
    invoice_id: int
    description: str | None
    quantity: int | None
    unit_price: float | None
    total: float | None
    item_type: str | None
    
    class Config:
        from_attributes = True

class InvoiceCreate(BaseModel):
    customer_id: int
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    subtotal: float | None = None
    tax_amount: float | None = None
    discount_amount: float | None = None
    total_amount: float | None = None
    due_date: date | None = None

class InvoiceResponse(InvoiceCreate):
    id: int
    invoice_number: str
    status: str
    paid_date: date | None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    amount: float
    payment_method: str | None = None
    transaction_ref: str | None = None
    notes: str | None = None

class PaymentResponse(PaymentCreate):
    id: int
    payment_ref: str
    invoice_id: int
    customer_id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
