from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.schemas.billing import InvoiceResponse, InvoiceCreate, PaymentResponse, PaymentCreate
from app.models.billing import Invoice, Payment
from app.core.deps import get_current_user
import uuid

router = APIRouter()

@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    customer_id: int | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    query = select(Invoice)
    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)
    if status:
        query = query.where(Invoice.status == status)
        
    query = query.order_by(desc(Invoice.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, session: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    inv = await session.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv

@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(request: InvoiceCreate, session: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    inv = Invoice(**request.model_dump(), invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}")
    session.add(inv)
    await session.commit()
    await session.refresh(inv)
    return inv

@router.post("/invoices/{invoice_id}/payments", response_model=PaymentResponse)
async def create_payment(invoice_id: int, request: PaymentCreate, session: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    inv = await session.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    payment = Payment(
        **request.model_dump(),
        invoice_id=invoice_id,
        customer_id=inv.customer_id,
        payment_ref=f"PAY-{uuid.uuid4().hex[:8].upper()}",
        status="completed"
    )
    session.add(payment)
    
    # Simple logic to mark invoice paid if it covers it
    inv.status = "paid"
    
    await session.commit()
    await session.refresh(payment)
    return payment
