"""Contact-center ACD: generate simulated inbound calls and distribute them
to agents who are 'ready' on the matching team.

Calls are templated/synthetic (no external telephony). Distribution rule:
only agents with status 'ready' and no active/ringing call receive offers.
"""
import uuid
import random
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call import Call
from app.models.customer import Customer
from app.models.user import User
from app.core.events import broadcast_event

# intent -> (team_code, [opening line templates]). {name} is the customer's first name.
INTENT_TEMPLATES = {
    "billing": ("billing", [
        "Hi, this is {name} — I was charged twice on my last bill.",
        "I don't understand the extra fee on my invoice this month.",
        "Can you explain why my bill went up?",
    ]),
    "outage": ("technical", [
        "My internet has been down since this morning.",
        "I keep losing signal — is there an outage in my area?",
        "My connection drops every few minutes, it's unusable.",
    ]),
    "upgrade": ("sales", [
        "I'd like to upgrade to a faster plan.",
        "Do you have any better deals than what I'm on now?",
        "I want to add a line to my account.",
    ]),
    "complaint": ("complaints", [
        "I've called three times and nobody has fixed my issue.",
        "I'm really unhappy with the service this month.",
        "I want to file a complaint about a technician visit.",
    ]),
    "general": ("call_center", [
        "I have a quick question about my account.",
        "Can you help me update my contact details?",
        "I just need some information about my services.",
    ]),
}


async def _team_id_for_code(session: AsyncSession, code: str) -> int | None:
    from app.models.user import Team
    tid = await session.scalar(select(Team.id).where(Team.code == code))
    if tid is None:
        tid = await session.scalar(select(Team.id).where(Team.code == "call_center"))
    return tid


async def generate_call(session: AsyncSession, team_id: int | None = None) -> Call | None:
    """Create one queued inbound call from a random customer, then try to route it.

    If team_id is given, the call is forced onto that team (used to send a test
    call straight to a specific team's queue); the intent is chosen to match.
    """
    cust = (await session.execute(
        select(Customer).order_by(func.random()).limit(1)
    )).scalar_one_or_none()
    if not cust:
        return None

    if team_id is not None:
        # Pick an intent whose template routes to this team (fallback: any).
        from app.models.user import Team
        code = await session.scalar(select(Team.code).where(Team.id == team_id))
        matching = [i for i, (tc, _) in INTENT_TEMPLATES.items() if tc == code]
        intent = random.choice(matching) if matching else random.choice(list(INTENT_TEMPLATES.keys()))
        lines = INTENT_TEMPLATES[intent][1]
    else:
        intent = random.choice(list(INTENT_TEMPLATES.keys()))
        team_code, lines = INTENT_TEMPLATES[intent]
        team_id = await _team_id_for_code(session, team_code)
    opening = random.choice(lines).format(name=cust.first_name)

    call = Call(
        call_number=f"CALL-{uuid.uuid4().hex[:8].upper()}",
        customer_id=cust.id,
        team_id=team_id,
        intent=intent,
        opening_line=opening,
        status="queued",
    )
    session.add(call)
    await session.commit()
    await session.refresh(call)

    await broadcast_event("call_queued", {
        "id": call.id, "call_number": call.call_number, "team_id": call.team_id,
        "intent": call.intent, "customer_id": call.customer_id,
    })
    await distribute_call(session, call)
    return call


async def _find_ready_agent(session: AsyncSession, team_id: int | None) -> User | None:
    """Longest-idle ready agent on the team who isn't already on a call."""
    q = select(User).where(
        User.role == "agent", User.is_active == True, User.status == "ready",
    )
    if team_id is not None:
        q = q.where(User.team_id == team_id)
    q = q.order_by(User.status_changed_at.asc().nulls_first())
    for agent in (await session.execute(q)).scalars().all():
        busy = await session.scalar(
            select(func.count()).select_from(Call).where(
                Call.assigned_agent_id == agent.id,
                Call.status.in_(["ringing", "active"]),
            )
        )
        if not busy:
            return agent
    return None


async def distribute_call(session: AsyncSession, call: Call) -> bool:
    """Offer a queued call to a ready agent. Returns True if offered."""
    if call.status != "queued":
        return False
    agent = await _find_ready_agent(session, call.team_id)
    if not agent:
        return False
    call.status = "ringing"
    call.assigned_agent_id = agent.id
    await session.commit()
    await session.refresh(call)
    await broadcast_event("call_offered", {
        "id": call.id, "call_number": call.call_number, "agent_id": agent.id,
        "intent": call.intent, "opening_line": call.opening_line,
        "customer_id": call.customer_id, "team_id": call.team_id,
    })
    return True


async def requeue_ringing_for_agent(session: AsyncSession, user_id: int) -> int:
    """Put any unanswered (ringing) calls offered to this agent back in the queue."""
    ringing = (await session.execute(
        select(Call).where(Call.assigned_agent_id == user_id, Call.status == "ringing")
    )).scalars().all()
    for c in ringing:
        c.status = "queued"
        c.assigned_agent_id = None
    if ringing:
        await session.commit()
        for c in ringing:
            await broadcast_event("call_queued", {
                "id": c.id, "call_number": c.call_number, "team_id": c.team_id,
                "intent": c.intent, "customer_id": c.customer_id,
            })
    return len(ringing)


async def find_any_ready_agent(session: AsyncSession) -> User | None:
    """Any ready, free agent across all teams (used to bias call generation)."""
    return await _find_ready_agent(session, None)


async def abandon_stale_calls(session: AsyncSession, minutes: int = 3) -> int:
    """Abandon calls left queued too long so the queue can't saturate forever."""
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    stale = (await session.execute(
        select(Call).where(Call.status == "queued", Call.queued_at < cutoff)
    )).scalars().all()
    for c in stale:
        c.status = "abandoned"
        c.ended_at = datetime.now(timezone.utc)
    if stale:
        await session.commit()
    return len(stale)


async def pull_queued_for_agent(session: AsyncSession, user: User) -> bool:
    """When an agent goes 'ready', offer them the next queued call on their team.

    VIP customers jump the queue: order by VIP-first, then oldest-waiting.
    """
    if user.role != "agent" or user.status != "ready":
        return False
    from sqlalchemy import case
    vip_first = case((Customer.segment == "vip", 0), else_=1)
    call = (await session.execute(
        select(Call)
        .join(Customer, Customer.id == Call.customer_id)
        .where(Call.status == "queued", Call.team_id == user.team_id)
        .order_by(vip_first.asc(), Call.queued_at.asc())
        .limit(1)
    )).scalar_one_or_none()
    if not call:
        return False
    return await distribute_call(session, call)
