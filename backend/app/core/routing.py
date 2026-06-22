"""Skill-based routing: map a ticket/call category to the team that handles it."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Team

# Ticket category -> team code. Anything unmapped falls back to the call center.
CATEGORY_TO_TEAM_CODE = {
    "billing": "billing",
    "plan_change": "sales",
    "provisioning": "sales",
    "technical": "technical",
    "network": "technical",
    "complaint": "complaints",
    "general": "call_center",
}

DEFAULT_TEAM_CODE = "call_center"


async def resolve_team_id(session: AsyncSession, category: str | None) -> int | None:
    """Return the team id that should own a ticket/call of this category."""
    code = CATEGORY_TO_TEAM_CODE.get(category or "", DEFAULT_TEAM_CODE)
    team_id = await session.scalar(select(Team.id).where(Team.code == code))
    if team_id is None:  # fall back to call center if the specific team is absent
        team_id = await session.scalar(select(Team.id).where(Team.code == DEFAULT_TEAM_CODE))
    return team_id
