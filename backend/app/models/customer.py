from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, ForeignKey, DateTime, func, Integer
from datetime import datetime
from app.db.base import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_number: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True) # "TC-XXXXXX"
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_primary: Mapped[str] = mapped_column(Text, nullable=False)
    phone_secondary: Mapped[str | None] = mapped_column(Text, nullable=True)
    national_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    company_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_type: Mapped[str] = mapped_column(Text, nullable=False) # 'residential', 'business', 'enterprise'
    status: Mapped[str] = mapped_column(Text, default="active") # 'active', 'suspended', 'terminated', 'pending'
    segment: Mapped[str | None] = mapped_column(Text, nullable=True) # 'standard', 'premium', 'vip'
    address_line1: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_line2: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(Text, nullable=True)
    zip_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Interaction(Base):
    __tablename__ = "interactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    ticket_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tickets.id"), nullable=True, index=True)
    agent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    channel: Mapped[str] = mapped_column(Text, nullable=False) # 'call', 'email', 'chat', 'sms', 'in_person'
    direction: Mapped[str | None] = mapped_column(Text, nullable=True) # 'inbound', 'outbound'
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
