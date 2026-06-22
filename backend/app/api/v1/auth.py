from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, ChangePasswordRequest, TokenRefreshRequest
from app.models.user import User, AuditLog
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.deps import get_current_user
from app.core.errors import AppError

router = APIRouter()

# NOTE: Public self-registration has been removed. Accounts are provisioned by
# the superuser via POST /api/v1/users (see app/api/v1/users.py). The superuser
# (admin/admin) is seeded at startup — demo-only, not for deployment.

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise AppError("CRM-AUTH-002", "Invalid credentials", status.HTTP_401_UNAUTHORIZED)
        
    if not user.is_active:
        raise AppError("CRM-AUTH-006", "Account deactivated", status.HTTP_403_FORBIDDEN)
        
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: TokenRefreshRequest, session: AsyncSession = Depends(get_db)):
    from jose import jwt, JWTError
    from app.core.security import ALGORITHM
    from app.config import settings
    
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise AppError("CRM-AUTH-004", "Token expired", status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        raise AppError("CRM-AUTH-005", "Token invalid / malformed", status.HTTP_401_UNAUTHORIZED)
        
    if not user_id:
        raise AppError("CRM-AUTH-005", "Token invalid / malformed", status.HTTP_401_UNAUTHORIZED)
        
    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise AppError("CRM-USER-002", "User not found", status.HTTP_404_NOT_FOUND)
        
    if not user.is_active:
        raise AppError("CRM-AUTH-006", "Account deactivated", status.HTTP_403_FORBIDDEN)
        
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.post("/change-password")
async def change_password(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    
    if not verify_password(request.current_password, user.password_hash):
        raise AppError("CRM-AUTH-008", "Current password incorrect", status.HTTP_400_BAD_REQUEST)
        
    user.password_hash = hash_password(request.new_password)
    user.must_change_password = False
    
    audit = AuditLog(user_id=user.id, action="password_changed", target_type="user", target_id=str(user.id))
    session.add(audit)
    await session.commit()
    return {"message": "Password updated successfully"}
