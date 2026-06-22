from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_token
from app.core.errors import AppError
from fastapi import status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: AsyncSession = Depends(get_db)
) -> dict:
    # Decode token
    payload = decode_token(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise AppError("CRM-AUTH-005", "Token invalid / malformed", status.HTTP_401_UNAUTHORIZED)
    
    # Query user
    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise AppError("CRM-USER-002", "User not found", status.HTTP_404_NOT_FOUND)
    
    if not user.is_active:
        raise AppError("CRM-AUTH-006", "Account deactivated", status.HTTP_403_FORBIDDEN)

    # Return dict instead of ORM object to avoid DetachedInstanceError (P3)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "team_id": user.team_id,
        "status": user.status,
        "must_change_password": user.must_change_password,
        "is_active": user.is_active,
        "created_at": user.created_at
    }

# Role hierarchy: superuser > supervisor > agent. A superuser implicitly
# satisfies every require_role(...) gate.
ROLE_RANK = {"agent": 1, "supervisor": 2, "superuser": 3}

def require_role(*roles: str):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] == "superuser":
            return current_user
        if current_user["role"] not in roles:
            raise AppError("CRM-USER-001", "Insufficient role", status.HTTP_403_FORBIDDEN)
        return current_user
    return role_checker

async def get_current_superuser(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "superuser":
        raise AppError("CRM-USER-001", "Superuser access required", status.HTTP_403_FORBIDDEN)
    return current_user
