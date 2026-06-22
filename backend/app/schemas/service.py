from pydantic import BaseModel
from datetime import date, datetime

class SubscriptionResponse(BaseModel):
    id: int
    customer_id: int
    plan_id: int
    status: str
    start_date: date
    end_date: date | None
    auto_renew: bool
    monthly_charge: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class DeviceResponse(BaseModel):
    id: int
    customer_id: int
    subscription_id: int | None
    device_type: str | None
    identifier: str | None
    status: str
    activated_at: datetime | None
    
    class Config:
        from_attributes = True
