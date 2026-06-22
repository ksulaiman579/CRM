from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, Boolean, ForeignKey, DateTime, func, JSON
from datetime import datetime
from app.db.base import Base

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # Stable routing key: 'sales' | 'complaints' | 'call_center' | 'technical' | 'billing'
    code: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="agent") # 'superuser', 'supervisor', 'agent'
    team_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teams.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Contact-center presence: 'offline' | 'ready' | 'on_call' | 'wrap_up'
    #   | 'break' | 'lunch' | 'restroom' | 'meeting'. Only 'ready' agents get calls.
    status: Mapped[str] = mapped_column(Text, nullable=False, default="offline", server_default="offline")
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    team: Mapped["Team | None"] = relationship()

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[int | str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
