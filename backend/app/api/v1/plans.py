from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.schemas.plan import PlanResponse, AddonResponse
from app.models.plan import Plan, Addon
from app.core.deps import get_current_user

router = APIRouter()

@router.get("", response_model=list[PlanResponse])
async def list_plans(session: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await session.execute(select(Plan).where(Plan.is_active == True))
    return result.scalars().all()

@router.get("/addons", response_model=list[AddonResponse])
async def list_addons(session: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await session.execute(select(Addon).where(Addon.is_active == True))
    return result.scalars().all()
