from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, Boolean, ForeignKey, DateTime, func, Numeric, Date
from datetime import datetime, date
from app.db.base import Base

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plans.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(Text, default="active") # 'active', 'paused', 'cancelled', 'expired'
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    monthly_charge: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Device(Base):
    __tablename__ = "devices"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    subscription_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("subscriptions.id"), nullable=True, index=True)
    device_type: Mapped[str | None] = mapped_column(Text, nullable=True) # 'sim', 'router', 'handset', 'set_top_box'
    identifier: Mapped[str | None] = mapped_column(Text, nullable=True) # MSISDN / IMEI / serial
    status: Mapped[str] = mapped_column(Text, default="active")
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
