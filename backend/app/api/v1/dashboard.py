from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.db.session import get_db
from app.schemas.dashboard import AgentDashboard, SupervisorDashboard
from app.schemas.ticket import TicketResponse
from app.core.deps import get_current_user, require_role
from app.models.ticket import Ticket
from datetime import datetime, timezone, timedelta

router = APIRouter()

@router.get("/agent", response_model=AgentDashboard)
async def get_agent_dashboard(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    # Base query for my tickets
    user_id = current_user["id"]
    
    # Open tickets
    open_count = await session.scalar(
        select(func.count()).select_from(Ticket).where(
            Ticket.assigned_agent_id == user_id,
            Ticket.status.in_(["open", "in_progress", "pending_customer"])
        )
    )
    
    # Breached
    breached_count = await session.scalar(
        select(func.count()).select_from(Ticket).where(
            Ticket.assigned_agent_id == user_id,
            Ticket.status.notin_(["resolved", "closed"]),
            Ticket.sla_breached == True
        )
    )
    
    # Due soon (within 2 hours)
    now = datetime.now(timezone.utc)
    due_soon_threshold = now + timedelta(hours=2)
    due_soon_count = await session.scalar(
        select(func.count()).select_from(Ticket).where(
            Ticket.assigned_agent_id == user_id,
            Ticket.status.notin_(["resolved", "closed"]),
            Ticket.sla_breached == False,
            Ticket.sla_resolution_due <= due_soon_threshold
        )
    )
    
    # Resolved today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    resolved_today = await session.scalar(
        select(func.count()).select_from(Ticket).where(
            Ticket.assigned_agent_id == user_id,
            Ticket.status == "resolved",
            Ticket.resolved_at >= today_start
        )
    )
    
    return AgentDashboard(
        my_open_tickets=open_count or 0,
        tickets_due_soon=due_soon_count or 0,
        tickets_breached=breached_count or 0,
        resolved_today=resolved_today or 0,
        avg_handle_time_mins=0.0 # Placeholder for now
    )

@router.get("/supervisor", response_model=SupervisorDashboard)
async def get_supervisor_dashboard(
    current_user: dict = Depends(require_role("admin", "supervisor")),
    session: AsyncSession = Depends(get_db)
):
    from app.core.cache import cache
    team_id = current_user.get("team_id")
    cache_key = f"supervisor_dash_{team_id}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
        
    # Queue depth (not resolved/closed)
    query_depth = select(func.count()).select_from(Ticket).where(Ticket.status.notin_(["resolved", "closed"]))
    if team_id:
        query_depth = query_depth.where(Ticket.team_id == team_id)
    depth = await session.scalar(query_depth) or 0
    
    # Unassigned
    query_unassigned = select(func.count()).select_from(Ticket).where(Ticket.assigned_agent_id == None, Ticket.status.notin_(["resolved", "closed"]))
    if team_id:
        query_unassigned = query_unassigned.where(Ticket.team_id == team_id)
    unassigned = await session.scalar(query_unassigned) or 0
    
    # Breach rate
    query_breached = select(func.count()).select_from(Ticket).where(Ticket.sla_breached == True, Ticket.status.notin_(["resolved", "closed"]))
    if team_id:
        query_breached = query_breached.where(Ticket.team_id == team_id)
    breached = await session.scalar(query_breached) or 0
    
    breach_rate = round((breached / depth * 100) if depth > 0 else 0.0, 1)
    
    # By Status
    query_status = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
    if team_id:
        query_status = query_status.where(Ticket.team_id == team_id)
    res_status = await session.execute(query_status)
    tickets_by_status = {row[0]: row[1] for row in res_status.all()}
    
    # By Category
    query_cat = select(Ticket.category, func.count(Ticket.id)).where(Ticket.status.notin_(["resolved", "closed"])).group_by(Ticket.category)
    if team_id:
        query_cat = query_cat.where(Ticket.team_id == team_id)
    res_cat = await session.execute(query_cat)
    tickets_by_cat = {row[0]: row[1] for row in res_cat.all()}
    
    # CSAT Statistics
    query_csat = select(func.avg(Ticket.csat_rating)).where(Ticket.csat_rating.isnot(None))
    if team_id:
        query_csat = query_csat.where(Ticket.team_id == team_id)
    avg_csat_val = await session.scalar(query_csat)
    avg_csat = round(float(avg_csat_val), 2) if avg_csat_val is not None else None
    
    query_csat_counts = select(Ticket.csat_rating, func.count(Ticket.id)).where(Ticket.csat_rating.isnot(None)).group_by(Ticket.csat_rating)
    if team_id:
        query_csat_counts = query_csat_counts.where(Ticket.team_id == team_id)
    res_csat_counts = await session.execute(query_csat_counts)
    csat_rating_counts = {i: 0 for i in range(1, 6)}
    for row in res_csat_counts.all():
        rating = int(row[0])
        if 1 <= rating <= 5:
            csat_rating_counts[rating] = row[1]
            
    dash = SupervisorDashboard(
        team_queue_depth=depth,
        unassigned_count=unassigned,
        sla_breach_rate_pct=breach_rate,
        tickets_by_status=tickets_by_status,
        tickets_by_category=tickets_by_cat,
        average_csat=avg_csat,
        csat_rating_counts=csat_rating_counts
    )
    
    cache.set(cache_key, dash, ttl_seconds=300)
    return dash

@router.get("/csat-feedback", response_model=list[TicketResponse])
async def get_csat_feedback(
    current_user: dict = Depends(require_role("admin", "supervisor")),
    session: AsyncSession = Depends(get_db)
):
    team_id = current_user.get("team_id")
    query = select(Ticket).where(Ticket.csat_rating.isnot(None))
    if team_id:
        query = query.where(Ticket.team_id == team_id)
    query = query.order_by(desc(Ticket.updated_at)).limit(5)
    result = await session.execute(query)
    return result.scalars().all()
