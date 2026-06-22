from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, Numeric, ForeignKey, DateTime, Date, func, Integer
from datetime import datetime, date
from app.db.base import Base

class Invoice(Base):
    __tablename__ = "invoices"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_number: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True) # "INV-YYYYMM-XXXX"
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    billing_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    billing_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    subtotal: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    tax_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    discount_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[str] = mapped_column(Text, default="pending") # 'pending', 'sent', 'paid', 'overdue', 'cancelled'
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Payment(Base):
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_ref: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="completed")
    transaction_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class LineItem(Base):
    __tablename__ = "line_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    total: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    item_type: Mapped[str | None] = mapped_column(Text, nullable=True)
