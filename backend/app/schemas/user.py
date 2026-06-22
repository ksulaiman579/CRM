from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    team_id: int | None = None
    is_active: bool | None = None

class AdminUserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str
    role: str
    team_id: int | None = None

class AdminPasswordReset(BaseModel):
    new_password: str

class TeamResponse(BaseModel):
    id: int
    name: str
    description: str | None
    
    class Config:
        from_attributes = True
