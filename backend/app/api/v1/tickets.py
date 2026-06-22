from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc, update
from app.db.session import get_db
from app.schemas.ticket import TicketResponse, TicketCreate, TicketUpdate, TicketCommentCreate, TicketCommentResponse
from app.schemas.kb import KbArticleResponse
from app.models.ticket import Ticket, TicketComment, SlaPolicy
from app.core.deps import get_current_user
from app.core.sla import compute_sla_due_dates
from app.core.errors import AppError
from app.core.events import broadcast_event, set_viewer, clear_viewer
import uuid
from datetime import datetime, timezone

router = APIRouter()


def assert_can_edit_ticket(ticket: Ticket, user: dict) -> None:
    """Authorization for ticket mutations.

    - superuser: any ticket.
    - supervisor: any ticket in their team (or unscoped tickets / unscoped supervisor).
    - agent: only tickets currently assigned to them (claim first to take one).
    """
    role = user["role"]
    if role == "superuser":
        return
    if role == "supervisor":
        if ticket.team_id and user.get("team_id") and ticket.team_id != user["team_id"]:
            raise AppError("CRM-SYS-403", "Ticket belongs to another team", status.HTTP_403_FORBIDDEN)
        return
    # agent
    if ticket.assigned_agent_id != user["id"]:
        raise AppError("CRM-SYS-403", "You can only edit tickets assigned to you", status.HTTP_403_FORBIDDEN)

@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    scope: str = Query("all", description="my|queue|team|all"),
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = select(Ticket)
    
    if scope == "my":
        query = query.where(Ticket.assigned_agent_id == current_user["id"])
    elif scope == "queue":
        query = query.where(Ticket.assigned_agent_id == None)
        if current_user.get("team_id"):
            query = query.where((Ticket.team_id == None) | (Ticket.team_id == current_user["team_id"]))
    elif scope == "team":
        if current_user.get("team_id"):
            query = query.where(Ticket.team_id == current_user["team_id"])
            
    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if priority:
        query = query.where(Ticket.priority == priority)
    if category:
        query = query.where(Ticket.category == category)
        
    query = query.order_by(asc(Ticket.sla_resolution_due)).offset((page - 1) * page_size).limit(page_size)
        
    result = await session.execute(query)
    return result.scalars().all()

@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: TicketCreate,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    ticket_num = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
    # lookup SLA policy
    policy_res = await session.execute(select(SlaPolicy).where(SlaPolicy.priority == request.priority, SlaPolicy.is_active == True))
    policy = policy_res.scalars().first()
    
    new_ticket = Ticket(
        ticket_number=ticket_num,
        customer_id=request.customer_id,
        subject=request.subject,
        description=request.description,
        category=request.category,
        priority=request.priority,
        channel=request.channel,
        team_id=request.team_id,
        assigned_agent_id=request.assigned_agent_id,
        created_by=current_user["id"]
    )
    
    if policy:
        new_ticket.sla_policy_id = policy.id
        resp_due, res_due = compute_sla_due_dates(policy)
        new_ticket.sla_response_due = resp_due
        new_ticket.sla_resolution_due = res_due
        
    session.add(new_ticket)
    await session.commit()
    await session.refresh(new_ticket)
    
    from app.core.cache import cache
    cache.delete("supervisor_dash_None")
    if new_ticket.team_id:
        cache.delete(f"supervisor_dash_{new_ticket.team_id}")
        
    await broadcast_event("ticket_created", {
        "id": new_ticket.id,
        "ticket_number": new_ticket.ticket_number,
        "subject": new_ticket.subject,
        "priority": new_ticket.priority,
        "category": new_ticket.category
    })
    
    return new_ticket

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise AppError("CRM-TKT-001", "Ticket not found", status.HTTP_404_NOT_FOUND)
    return ticket

@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    request: TicketUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise AppError("CRM-TKT-001", "Ticket not found", status.HTTP_404_NOT_FOUND)

    # Authorization: who may mutate this ticket.
    assert_can_edit_ticket(ticket, current_user)

    # Optimistic concurrency: reject stale writes from an out-of-date tab.
    if request.version is not None and request.version != ticket.version:
        raise AppError(
            "CRM-TKT-005",
            "This ticket was changed by someone else. Reload and try again.",
            status.HTTP_409_CONFLICT,
        )

    if request.status and request.status != ticket.status:
        if ticket.status == "closed":
            raise AppError("CRM-TKT-002", "Invalid status transition: Closed tickets cannot be reopened or modified", status.HTTP_409_CONFLICT)
        ticket.status = request.status
        if request.status in ["resolved", "closed"]:
            ticket.resolved_at = datetime.now(timezone.utc)
            if request.status == "closed":
                ticket.closed_at = datetime.now(timezone.utc)
    if request.priority:
        ticket.priority = request.priority
    if request.assigned_agent_id is not None:
        ticket.assigned_agent_id = request.assigned_agent_id
    if request.category:
        ticket.category = request.category
        
    # CSAT handling and validation
    if request.csat_rating is not None or request.csat_feedback is not None:
        target_status = request.status or ticket.status
        if target_status not in ["resolved", "closed"]:
            raise AppError("CRM-TKT-003", "CSAT rating can only be submitted for resolved or closed tickets", status.HTTP_400_BAD_REQUEST)
        if request.csat_rating is not None:
            ticket.csat_rating = request.csat_rating
        if request.csat_feedback is not None:
            ticket.csat_feedback = request.csat_feedback

    ticket.version += 1
    await session.commit()
    await session.refresh(ticket)

    from app.core.cache import cache
    cache.delete("supervisor_dash_None")
    if ticket.team_id:
        cache.delete(f"supervisor_dash_{ticket.team_id}")

    await broadcast_event("ticket_assigned", {
        "id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "assigned_agent_id": ticket.assigned_agent_id,
        "status": ticket.status
    })
    
    return ticket

@router.post("/{ticket_id}/claim", response_model=TicketResponse)
async def claim_ticket(
    ticket_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Atomically claim an unassigned ticket. Concurrency-safe: a conditional
    UPDATE means only the first of two racing agents wins; the loser gets
    CRM-TKT-003 instead of silently overwriting the assignment."""
    stmt = (
        update(Ticket)
        .where(Ticket.id == ticket_id, Ticket.assigned_agent_id.is_(None))
        .values(
            assigned_agent_id=current_user["id"],
            status="in_progress",
            version=Ticket.version + 1,
        )
    )
    result = await session.execute(stmt)
    await session.commit()

    if result.rowcount == 0:
        exists = await session.scalar(select(Ticket.id).where(Ticket.id == ticket_id))
        if not exists:
            raise AppError("CRM-TKT-001", "Ticket not found", status.HTTP_404_NOT_FOUND)
        raise AppError("CRM-TKT-003", "Ticket already claimed by another agent", status.HTTP_409_CONFLICT)

    ticket = (await session.execute(select(Ticket).where(Ticket.id == ticket_id))).scalar_one()

    from app.core.cache import cache
    cache.delete("supervisor_dash_None")
    if ticket.team_id:
        cache.delete(f"supervisor_dash_{ticket.team_id}")

    await broadcast_event("ticket_assigned", {
        "id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "assigned_agent_id": ticket.assigned_agent_id,
        "status": ticket.status,
    })
    return ticket


@router.post("/{ticket_id}/release", response_model=TicketResponse)
async def release_ticket(
    ticket_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Release a ticket back to the unassigned queue. Agents may only release
    a ticket they currently hold; supervisors/superusers may release any."""
    result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise AppError("CRM-TKT-001", "Ticket not found", status.HTTP_404_NOT_FOUND)

    assert_can_edit_ticket(ticket, current_user)

    ticket.assigned_agent_id = None
    if ticket.status == "in_progress":
        ticket.status = "open"
    ticket.version += 1
    await session.commit()
    await session.refresh(ticket)

    await broadcast_event("ticket_assigned", {
        "id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "assigned_agent_id": None,
        "status": ticket.status,
    })
    return ticket


@router.post("/{ticket_id}/presence")
async def open_presence(
    ticket_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Mark the current agent as viewing this ticket and broadcast the viewer
    list so other open clients can show a collision banner."""
    viewers = set_viewer(ticket_id, current_user["id"], current_user["full_name"])
    await broadcast_event("ticket_viewing", {"ticket_id": ticket_id, "viewers": viewers})
    return {"viewers": viewers}


@router.delete("/{ticket_id}/presence")
async def close_presence(
    ticket_id: int,
    current_user: dict = Depends(get_current_user)
):
    viewers = clear_viewer(ticket_id, current_user["id"])
    await broadcast_event("ticket_released", {"ticket_id": ticket_id, "viewers": viewers})
    return {"viewers": viewers}


@router.post("/{ticket_id}/comments", response_model=TicketCommentResponse)
async def add_ticket_comment(
    ticket_id: int,
    request: TicketCommentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise AppError("CRM-TKT-001", "Ticket not found", status.HTTP_404_NOT_FOUND)
        
    if not ticket.first_response_at and not request.is_internal:
        ticket.first_response_at = datetime.now(timezone.utc)

    new_comment = TicketComment(
        ticket_id=ticket.id,
        author_id=current_user["id"],
        body=request.body,
        is_internal=request.is_internal
    )
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)
    return new_comment

@router.get("/{ticket_id}/suggested-kb", response_model=list[KbArticleResponse])
async def get_suggested_kb(
    ticket_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from app.models.kb import KbArticle, KbCategory
    
    # 1. Fetch ticket to get category and subject
    result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise AppError("CRM-TKT-001", "Ticket not found", status.HTTP_404_NOT_FOUND)
        
    # Map ticket category to KB category slug
    category_mapping = {
        "billing": "billing-faqs",
        "technical": "troubleshooting",
        "network": "troubleshooting",
        "plan_change": "product-manuals",
        "provisioning": "product-manuals",
        "complaint": "internal-procedures",
        "general": "internal-procedures"
    }
    
    kb_slug = category_mapping.get(ticket.category, "troubleshooting")
    
    # Get the KbCategory
    cat_res = await session.execute(select(KbCategory).where(KbCategory.slug == kb_slug))
    kb_category = cat_res.scalar_one_or_none()
    
    # Query articles: prioritising the matched category, but allowing others if needed. Stop words to ignore
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "my", "your", "his", "her", "their", "our", "its", "it", "to", "for", "in", "on", "at", "by", "with", "and", "or", "but", "not"}
    keywords = [w.strip(".,!?\"'").lower() for w in ticket.subject.split() if w.strip(".,!?\"'").lower() not in stop_words]
    
    # Build query
    query = select(KbArticle).where(KbArticle.status == "published")
    
    # If we have keywords, filter by title/body matching
    from sqlalchemy import or_
    if keywords:
        clauses = []
        for kw in keywords[:5]: # limit to first 5 keywords
            clauses.append(KbArticle.title.ilike(f"%{kw}%"))
            clauses.append(KbArticle.body.ilike(f"%{kw}%"))
        query = query.where(or_(*clauses))
        
    # Also prioritize matched category
    if kb_category:
        from sqlalchemy import case
        query = query.order_by(
            case((KbArticle.category_id == kb_category.id, 0), else_=1),
            desc(KbArticle.view_count)
        )
    else:
        query = query.order_by(desc(KbArticle.view_count))
        
    query = query.limit(5)
    
    res = await session.execute(query)
    articles = res.scalars().all()
    
    # If no articles were found matching keywords, fallback to category articles
    if not articles and kb_category:
        query_fallback = select(KbArticle).where(
            KbArticle.status == "published",
            KbArticle.category_id == kb_category.id
        ).order_by(desc(KbArticle.view_count)).limit(5)
        res_fallback = await session.execute(query_fallback)
        articles = res_fallback.scalars().all()
        
    return articles

@router.get("/{ticket_id}/comments", response_model=list[TicketCommentResponse])
async def list_ticket_comments(
    ticket_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await session.execute(
        select(TicketComment)
        .where(TicketComment.ticket_id == ticket_id)
        .order_by(asc(TicketComment.created_at))
    )
    return result.scalars().all()

