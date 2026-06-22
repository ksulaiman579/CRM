from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.schemas.customer import InteractionResponse, InteractionCreate
from app.models.customer import Interaction
from app.core.deps import get_current_user

router = APIRouter()

@router.get("", response_model=list[InteractionResponse])
async def list_interactions(
    customer_id: int | None = Query(None),
    ticket_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    query = select(Interaction)
    if customer_id:
        query = query.where(Interaction.customer_id == customer_id)
    if ticket_id:
        query = query.where(Interaction.ticket_id == ticket_id)
        
    query = query.order_by(desc(Interaction.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    return result.scalars().all()

@router.post("", response_model=InteractionResponse)
async def create_interaction(
    request: InteractionCreate, 
    session: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    new_int = Interaction(**request.model_dump(), agent_id=current_user["id"])
    session.add(new_int)
    await session.commit()
    await session.refresh(new_int)
    return new_int
