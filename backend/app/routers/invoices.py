"""
routers/invoices.py -- Endpoints for Invoices and Payments.

Endpoints:
  POST  /api/invoices                   create an invoice for a customer
  GET   /api/invoices                   list invoices (filterable by customer_id or status)
  GET   /api/invoices/{id}              get a single invoice
  POST  /api/invoices/{id}/payments     record a payment against an invoice
                                         auto-updates status: unpaid -> partially_paid -> paid
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Invoice, Payment, Customer
from backend.app.schemas import (
    InvoiceCreate, InvoiceResponse,
    PaymentCreate, PaymentResponse,
)

router = APIRouter(prefix="/api/invoices", tags=["Invoices & Payments"])


@router.post("", response_model=InvoiceResponse, status_code=201)
def create_invoice(req: InvoiceCreate, db: Session = Depends(get_db)):
    """Create a new invoice for a customer."""
    customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{req.customer_id}' not found")

    if req.invoice_amount <= 0:
        raise HTTPException(status_code=422, detail="invoice_amount must be greater than 0")

    invoice = Invoice(
        customer_id=req.customer_id,
        invoice_amount=req.invoice_amount,
        amount_paid=0.0,
        due_date=req.due_date,
        created_date=req.created_date or date.today(),
        status="unpaid",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status:      Optional[str] = Query(None, description="Filter by status: unpaid | partially_paid | paid"),
    db: Session = Depends(get_db),
):
    """List invoices, optionally filtered by customer_id and/or status."""
    query = db.query(Invoice)
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    if status:
        query = query.filter(Invoice.status == status)
    return query.order_by(Invoice.id.desc()).all()


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Retrieve a single invoice by ID."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice ID {invoice_id} not found")
    return invoice


@router.post("/{invoice_id}/payments", response_model=PaymentResponse, status_code=201)
def record_payment(invoice_id: int, req: PaymentCreate, db: Session = Depends(get_db)):
    """
    Record a payment against an invoice.
    - Validates the invoice exists and is not already fully paid.
    - Validates payment amount does not exceed the outstanding balance.
    - Auto-updates invoice status:
        unpaid -> partially_paid  (if amount_paid < invoice_amount)
        *       -> paid           (if amount_paid >= invoice_amount)
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice ID {invoice_id} not found")

    if invoice.status == "paid":
        raise HTTPException(
            status_code=400,
            detail=f"Invoice {invoice_id} is already fully paid"
        )

    outstanding = round(invoice.invoice_amount - invoice.amount_paid, 2)
    if req.amount > outstanding + 0.001:  # small float tolerance
        raise HTTPException(
            status_code=422,
            detail=(
                f"Payment amount {req.amount} exceeds outstanding balance {outstanding:.2f} "
                f"for invoice {invoice_id}"
            ),
        )

    # Record the payment row
    payment = Payment(
        invoice_id=invoice_id,
        payment_date=req.payment_date,
        amount=req.amount,
    )
    db.add(payment)

    # Update invoice totals and status
    invoice.amount_paid = round(invoice.amount_paid + req.amount, 2)
    if invoice.amount_paid >= invoice.invoice_amount - 0.001:
        invoice.status = "paid"
    else:
        invoice.status = "partially_paid"

    db.commit()
    db.refresh(payment)
    db.refresh(invoice)

    return PaymentResponse(
        id=payment.id,
        invoice_id=payment.invoice_id,
        payment_date=payment.payment_date,
        amount=payment.amount,
        invoice_status=invoice.status,
        invoice_amount_paid=invoice.amount_paid,
    )
