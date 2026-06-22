from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, Boolean, ForeignKey, DateTime, func, Integer
from datetime import datetime
from app.db.base import Base

class SlaPolicy(Base):
    __tablename__ = "sla_policies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(Text, nullable=False) # 'low', 'medium', 'high', 'critical'
    first_response_mins: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_mins: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Ticket(Base):
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_number: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True) # "TKT-YYYYMM-XXXXX"
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(Text, nullable=False) # 'billing', 'network', 'technical', 'plan_change', 'complaint', 'provisioning', 'general'
    priority: Mapped[str] = mapped_column(Text, default="medium") # 'low', 'medium', 'high', 'critical'
    status: Mapped[str] = mapped_column(Text, default="open", index=True) # 'open', 'in_progress', 'pending_customer', 'escalated', 'resolved', 'closed'
    channel: Mapped[str | None] = mapped_column(Text, nullable=True) # 'call', 'email', 'chat', 'web', 'sms'
    assigned_agent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    team_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teams.id"), nullable=True)
    sla_policy_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sla_policies.id"), nullable=True)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_response_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_resolution_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    csat_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    csat_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optimistic-concurrency token: bumped on every mutation so stale tabs
    # cannot silently overwrite a newer change.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class TicketComment(Base):
    __tablename__ = "ticket_comments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    author_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
