from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, Boolean, Numeric, ForeignKey, DateTime, func, Integer
from datetime import datetime
from app.db.base import Base

class Plan(Base):
    __tablename__ = "plans"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_type: Mapped[str] = mapped_column(Text, nullable=False) # 'mobile', 'fiber', 'dsl', 'satellite', 'bundle'
    speed_mbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_cap_gb: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    voice_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sms_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    monthly_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    setup_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    contract_months: Mapped[int] = mapped_column(Integer, default=12)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PlanFeature(Base):
    __tablename__ = "plan_features"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plans.id"), nullable=False, index=True)
    feature_name: Mapped[str] = mapped_column(Text, nullable=False)
    feature_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_included: Mapped[bool] = mapped_column(Boolean, default=True)

class Addon(Base):
    __tablename__ = "addons"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    addon_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
