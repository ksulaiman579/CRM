import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.call import Call
from app.models.ticket import Ticket, SlaPolicy
from app.schemas.call import CallResponse, CallComplete
from app.core.deps import get_current_user
from app.core.errors import AppError
from app.core.events import broadcast_event
from app.core.sla import compute_sla_due_dates

router = APIRouter()

# intent -> ticket category (for tickets raised from a call)
INTENT_TO_CATEGORY = {
    "billing": "billing", "outage": "network", "upgrade": "plan_change",
    "complaint": "complaint", "general": "general",
}


def _assert_owns_call(call: Call, user: dict) -> None:
    if user["role"] in ("superuser", "supervisor"):
        return
    if call.assigned_agent_id != user["id"]:
        raise AppError("CRM-SYS-403", "This call is not assigned to you", status.HTTP_403_FORBIDDEN)


@router.get("", response_model=list[CallResponse])
async def list_calls(
    scope: str = Query("mine", description="mine|queue|team|all"),
    status_filter: str | None = Query(None, alias="status"),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    q = select(Call)
    if scope == "mine":
        q = q.where(Call.assigned_agent_id == current_user["id"])
    elif scope == "queue":
        q = q.where(Call.status == "queued", Call.team_id == current_user.get("team_id"))
    elif scope == "team":
        q = q.where(Call.team_id == current_user.get("team_id"))
    if status_filter:
        q = q.where(Call.status == status_filter)
    q = q.order_by(desc(Call.queued_at)).limit(100)
    return (await session.execute(q)).scalars().all()


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(call_id: int, session: AsyncSession = Depends(get_db),
                   current_user: dict = Depends(get_current_user)):
    call = (await session.execute(select(Call).where(Call.id == call_id))).scalar_one_or_none()
    if not call:
        raise AppError("CRM-CALL-001", "Call not found", status.HTTP_404_NOT_FOUND)
    return call


@router.post("/generate", response_model=CallResponse)
async def generate(session: AsyncSession = Depends(get_db),
                   current_user: dict = Depends(get_current_user)):
    """Manually inject a simulated inbound call (handy for demos/testing)."""
    from app.core.acd import generate_call
    call = await generate_call(session)
    if not call:
        raise AppError("CRM-CALL-002", "Could not generate a call (no customers)", status.HTTP_409_CONFLICT)
    return call


@router.post("/{call_id}/answer", response_model=CallResponse)
async def answer_call(call_id: int, session: AsyncSession = Depends(get_db),
                      current_user: dict = Depends(get_current_user)):
    call = (await session.execute(select(Call).where(Call.id == call_id))).scalar_one_or_none()
    if not call:
        raise AppError("CRM-CALL-001", "Call not found", status.HTTP_404_NOT_FOUND)
    _assert_owns_call(call, current_user)
    if call.status != "ringing":
        raise AppError("CRM-CALL-003", f"Call is not ringing (status={call.status})", status.HTTP_409_CONFLICT)

    call.status = "active"
    call.answered_at = datetime.now(timezone.utc)

    # Put the agent on-call.
    from app.models.user import User
    agent = (await session.execute(select(User).where(User.id == call.assigned_agent_id))).scalar_one()
    agent.status = "on_call"
    agent.status_changed_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(call)
    await broadcast_event("call_answered", {"id": call.id, "agent_id": call.assigned_agent_id})
    return call


@router.post("/{call_id}/complete", response_model=CallResponse)
async def complete_call(call_id: int, payload: CallComplete,
                        session: AsyncSession = Depends(get_db),
                        current_user: dict = Depends(get_current_user)):
    call = (await session.execute(select(Call).where(Call.id == call_id))).scalar_one_or_none()
    if not call:
        raise AppError("CRM-CALL-001", "Call not found", status.HTTP_404_NOT_FOUND)
    _assert_owns_call(call, current_user)

    call.status = payload.disposition if payload.disposition in ("completed", "missed", "abandoned") else "completed"
    call.ended_at = datetime.now(timezone.utc)
    if payload.notes:
        call.notes = payload.notes

    # Optionally raise a ticket from the call.
    if payload.raise_ticket and not call.ticket_id:
        category = INTENT_TO_CATEGORY.get(call.intent, "general")
        priority = "high" if call.intent in ("outage", "complaint") else "medium"
        policy = (await session.execute(
            select(SlaPolicy).where(SlaPolicy.priority == priority, SlaPolicy.is_active == True)
        )).scalars().first()
        ticket = Ticket(
            ticket_number=f"TKT-{uuid.uuid4().hex[:8].upper()}",
            customer_id=call.customer_id,
            subject=f"Call: {call.opening_line or call.intent}"[:120],
            description=call.opening_line,
            category=category,
            priority=priority,
            channel="call",
            team_id=call.team_id,
            assigned_agent_id=call.assigned_agent_id,
            created_by=current_user["id"],
        )
        if policy:
            ticket.sla_policy_id = policy.id
            resp_due, res_due = compute_sla_due_dates(policy)
            ticket.sla_response_due, ticket.sla_resolution_due = resp_due, res_due
        session.add(ticket)
        await session.flush()
        call.ticket_id = ticket.id

    # Agent moves to wrap-up after the call.
    from app.models.user import User
    if call.assigned_agent_id:
        agent = (await session.execute(select(User).where(User.id == call.assigned_agent_id))).scalar_one()
        agent.status = "wrap_up"
        agent.status_changed_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(call)
    await broadcast_event("call_completed", {
        "id": call.id, "agent_id": call.assigned_agent_id,
        "ticket_id": call.ticket_id, "status": call.status,
    })
    return call
