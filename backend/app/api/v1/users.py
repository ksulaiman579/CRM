from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from datetime import datetime, timezone
from app.schemas.user import AdminUserCreate, AdminPasswordReset, UserUpdate, StatusUpdate
from app.schemas.auth import UserResponse
from app.models.user import User, AuditLog
from app.core.deps import get_current_user, require_role, get_current_superuser
from app.core.security import hash_password
from app.core.errors import AppError
from app.core.events import broadcast_event

router = APIRouter()

ALLOWED_ROLES = {"agent", "supervisor", "superuser"}
ALLOWED_STATUSES = {"offline", "ready", "on_call", "wrap_up", "break", "lunch", "restroom", "meeting"}


@router.post("/me/status", response_model=UserResponse)
async def set_my_status(
    payload: StatusUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Self-service contact-center presence change. Only 'ready' agents receive calls."""
    if payload.status not in ALLOWED_STATUSES:
        raise AppError("CRM-USER-001", f"Invalid status '{payload.status}'", status.HTTP_400_BAD_REQUEST)

    result = await session.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one()
    user.status = payload.status
    user.status_changed_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(user)

    await broadcast_event("agent_status_changed", {
        "id": user.id, "full_name": user.full_name,
        "status": user.status, "team_id": user.team_id,
    })

    if user.status == "ready":
        # Pull the oldest queued call on the agent's team, if any.
        from app.core.acd import pull_queued_for_agent
        await pull_queued_for_agent(session, user)
    elif user.status != "on_call":
        # Stepping away (break/lunch/offline/etc.) — release any unanswered
        # ringing call back to the queue so it isn't stuck on this agent.
        from app.core.acd import requeue_ringing_for_agent
        await requeue_ringing_for_agent(session, user.id)

    return user


@router.get("", response_model=list[UserResponse])
async def list_users(
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("supervisor")),
):
    result = await session.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: AdminUserCreate,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_superuser),
):
    if request.role not in ALLOWED_ROLES:
        raise AppError("CRM-USER-001", f"Invalid role '{request.role}'", status.HTTP_400_BAD_REQUEST)

    existing = await session.execute(
        select(User).where((User.username == request.username) | (User.email == request.email))
    )
    if existing.scalar_one_or_none():
        raise AppError("CRM-AUTH-003", "Username or email already taken", status.HTTP_409_CONFLICT)

    new_user = User(
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        password_hash=hash_password(request.password),
        role=request.role,
        team_id=request.team_id,
        must_change_password=True,  # provisioned users set their own password on first login
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    session.add(AuditLog(
        user_id=current_user["id"], action="user_created",
        target_type="user", target_id=str(new_user.id),
        details={"role": new_user.role, "team_id": new_user.team_id},
    ))
    await session.commit()
    return new_user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_superuser),
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise AppError("CRM-USER-002", "User not found", status.HTTP_404_NOT_FOUND)

    if request.role is not None and request.role not in ALLOWED_ROLES:
        raise AppError("CRM-USER-001", f"Invalid role '{request.role}'", status.HTTP_400_BAD_REQUEST)

    # Guard: never strip/deactivate the last active superuser.
    demoting = request.role is not None and request.role != "superuser"
    deactivating = request.is_active is False
    if user.role == "superuser" and (demoting or deactivating):
        active_supers = await session.scalar(
            select(func.count()).select_from(User).where(User.role == "superuser", User.is_active == True)
        )
        if active_supers <= 1:
            raise AppError("CRM-USER-003", "Cannot deactivate or demote the last superuser", status.HTTP_409_CONFLICT)

    if request.full_name is not None:
        user.full_name = request.full_name
    if request.email is not None:
        user.email = request.email
    if request.role is not None:
        user.role = request.role
    if request.team_id is not None:
        user.team_id = request.team_id
    if request.is_active is not None:
        user.is_active = request.is_active

    await session.commit()
    await session.refresh(user)

    session.add(AuditLog(
        user_id=current_user["id"], action="user_updated",
        target_type="user", target_id=str(user.id),
        details=request.model_dump(exclude_none=True),
    ))
    await session.commit()
    return user


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    request: AdminPasswordReset,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_superuser),
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise AppError("CRM-USER-002", "User not found", status.HTTP_404_NOT_FOUND)

    user.password_hash = hash_password(request.new_password)
    user.must_change_password = True

    session.add(AuditLog(
        user_id=current_user["id"], action="admin_password_reset",
        target_type="user", target_id=str(user.id),
    ))
    await session.commit()
    return {"message": "Password reset successfully. User must change password on next login."}
