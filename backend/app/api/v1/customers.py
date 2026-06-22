from fastapi import APIRouter, Depends, status, Query, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc
from app.db.session import get_db
from app.schemas.customer import CustomerResponse, CustomerCreate, CustomerOverviewResponse, BillingSummary, SubscriptionOverview
from app.schemas.ticket import TicketResponse
from app.schemas.customer import InteractionResponse
from app.models.customer import Customer, Interaction
from app.models.service import Subscription
from app.models.plan import Plan
from app.models.billing import Invoice
from app.models.ticket import Ticket
from app.core.deps import get_current_user

router = APIRouter()

@router.get("", response_model=list[CustomerResponse])
async def list_customers(
    q: str | None = Query(None, description="Search by name, account #, phone, email"),
    status_filter: str | None = Query(None, alias="status"),
    segment: str | None = Query(None),
    customer_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = select(Customer)
    
    if q:
        query = query.where(
            or_(
                Customer.first_name.ilike(f"%{q}%"),
                Customer.last_name.ilike(f"%{q}%"),
                Customer.account_number.ilike(f"%{q}%"),
                Customer.email.ilike(f"%{q}%"),
                Customer.phone_primary.ilike(f"%{q}%")
            )
        )
    if status_filter:
        query = query.where(Customer.status == status_filter)
    if segment:
        query = query.where(Customer.segment == segment)
    if customer_type:
        query = query.where(Customer.customer_type == customer_type)
        
    query = query.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    return result.scalars().all()

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CustomerCreate, 
    session: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    new_cust = Customer(**request.model_dump())
    session.add(new_cust)
    await session.commit()
    await session.refresh(new_cust)
    return new_cust

@router.get("/{id}", response_model=CustomerResponse)
async def get_customer(id: int, session: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cust = await session.get(Customer, id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")
    return cust

@router.get("/{id}/overview", response_model=CustomerOverviewResponse)
async def get_customer_overview(id: int, session: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cust = await session.get(Customer, id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Active Subscriptions
    subs_result = await session.execute(
        select(Subscription, Plan.name).join(Plan).where(
            Subscription.customer_id == id,
            Subscription.status == "active"
        )
    )
    active_subs = []
    for sub, plan_name in subs_result:
        active_subs.append(SubscriptionOverview(
            id=sub.id,
            plan_name=plan_name,
            status=sub.status,
            monthly_charge=float(sub.monthly_charge),
            start_date=sub.start_date
        ))
        
    # Billing Summary
    overdue_count = await session.scalar(
        select(func.count()).select_from(Invoice).where(
            Invoice.customer_id == id, Invoice.status == "overdue"
        )
    )
    
    # Get all unpaid invoices to calculate balance
    unpaid_total = await session.scalar(
        select(func.sum(Invoice.total_amount)).where(
            Invoice.customer_id == id, Invoice.status.in_(["pending", "overdue"])
        )
    )
    
    last_inv = await session.execute(
        select(Invoice).where(Invoice.customer_id == id).order_by(Invoice.created_at.desc()).limit(1)
    )
    last_inv = last_inv.scalar_one_or_none()
    
    billing_summary = BillingSummary(
        current_balance=float(unpaid_total or 0.0),
        last_invoice_amount=float(last_inv.total_amount) if last_inv else None,
        last_invoice_date=last_inv.created_at.date() if last_inv else None,
        overdue_invoices_count=overdue_count or 0
    )
    
    # Open Tickets Count
    open_tickets_count = await session.scalar(
        select(func.count()).select_from(Ticket).where(
            Ticket.customer_id == id, Ticket.status.in_(["open", "in_progress", "pending_customer", "escalated"])
        )
    )
    
    # Recent Interactions
    interactions_res = await session.execute(
        select(Interaction).where(Interaction.customer_id == id).order_by(Interaction.created_at.desc()).limit(3)
    )
    
    return CustomerOverviewResponse(
        profile=cust,
        billing_summary=billing_summary,
        active_subscriptions=active_subs,
        recent_interactions=interactions_res.scalars().all(),
        open_tickets_count=open_tickets_count or 0
    )

@router.get("/{id}/subscriptions")
async def get_customer_subscriptions(id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Subscription).where(Subscription.customer_id == id).order_by(desc(Subscription.start_date)))
    return result.scalars().all()

class ChangePlanRequest(BaseModel):
    plan_id: int


@router.post("/{id}/subscriptions/{sub_id}/change-plan")
async def change_subscription_plan(
    id: int, sub_id: int, payload: ChangePlanRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Switch a customer's subscription to a different plan and log the action
    as an interaction (the action a care agent takes on a plan-change call)."""
    sub = await session.get(Subscription, sub_id)
    if not sub or sub.customer_id != id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    new_plan = await session.get(Plan, payload.plan_id)
    if not new_plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    old_plan_name = await session.scalar(select(Plan.name).where(Plan.id == sub.plan_id))
    sub.plan_id = new_plan.id
    sub.monthly_charge = new_plan.monthly_price

    session.add(Interaction(
        customer_id=id, agent_id=current_user["id"], channel="call",
        subject="Plan change",
        notes=f"Plan changed from {old_plan_name} to {new_plan.name} "
              f"(now {float(new_plan.monthly_price):.2f}/mo) by {current_user['full_name']}.",
    ))
    await session.commit()
    await session.refresh(sub)
    return {
        "subscription_id": sub.id,
        "plan_id": new_plan.id,
        "plan_name": new_plan.name,
        "monthly_charge": float(sub.monthly_charge),
    }


@router.get("/{id}/billing")
async def get_customer_billing(id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Invoice).where(Invoice.customer_id == id).order_by(desc(Invoice.created_at)))
    return result.scalars().all()

@router.get("/{id}/interactions", response_model=list[InteractionResponse])
async def get_customer_interactions(id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Interaction).where(Interaction.customer_id == id).order_by(desc(Interaction.created_at)))
    return result.scalars().all()

@router.get("/{id}/tickets", response_model=list[TicketResponse])
async def get_customer_tickets(id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Ticket).where(Ticket.customer_id == id).order_by(desc(Ticket.created_at)))
    return result.scalars().all()
