from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    team_id: int | None = None
    status: str = "offline"
    must_change_password: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str | None = None # Explicitly ignored by backend, but accepted in payload

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str
