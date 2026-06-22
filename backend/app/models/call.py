from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, ForeignKey, DateTime, func
from datetime import datetime
from app.db.base import Base


class Call(Base):
    """A (simulated) inbound customer call handled by the contact center.

    Lifecycle: queued -> ringing (offered to an agent) -> active (answered)
    -> completed | missed | abandoned.
    """
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_number: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    team_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    intent: Mapped[str] = mapped_column(Text, nullable=False)  # billing|outage|upgrade|complaint|general
    opening_line: Mapped[str | None] = mapped_column(Text, nullable=True)  # templated customer utterance
    status: Mapped[str] = mapped_column(Text, nullable=False, default="queued", server_default="queued", index=True)
    assigned_agent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    ticket_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tickets.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
