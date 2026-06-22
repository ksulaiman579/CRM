from pydantic import BaseModel
from datetime import datetime

class PlanResponse(BaseModel):
    id: int
    plan_code: str
    name: str
    description: str | None
    plan_type: str
    speed_mbps: int | None
    data_cap_gb: float | None
    voice_minutes: int | None
    sms_count: int | None
    monthly_price: float
    setup_fee: float
    contract_months: int
    is_active: bool
    
    class Config:
        from_attributes = True

class AddonResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    addon_type: str | None
    is_active: bool
    
    class Config:
        from_attributes = True
