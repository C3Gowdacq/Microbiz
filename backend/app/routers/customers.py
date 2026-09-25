"""
routers/customers.py -- CRUD endpoints for Customers.

Endpoints:
  POST  /api/customers
  GET   /api/customers
  GET   /api/customers/{id}
  GET   /api/customers/{id}/summary  (outstanding balance, days overdue, invoice history)
"""

import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Customer, Invoice
from backend.app.schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CustomerSummaryResponse, InvoiceSummaryItem,
)

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(req: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer."""
    customer = Customer(
        id=str(uuid.uuid4()),
        name=req.name,
        email=req.email,
        phone=req.phone,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=List[CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    """Return all customers ordered by name."""
    return db.query(Customer).order_by(Customer.name).all()


@router.get("/{customer_id}/summary", response_model=CustomerSummaryResponse)
def get_customer_summary(customer_id: str, db: Session = Depends(get_db)):
    """
    Return outstanding balance, days overdue on the oldest unpaid invoice,
    and full invoice + payment history for this customer.
    NOTE: This route must appear BEFORE /{customer_id} to prevent path conflict.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

    invoices = (
        db.query(Invoice)
        .filter(Invoice.customer_id == customer_id)
        .order_by(Invoice.due_date)
        .all()
    )

    outstanding_balance = sum(
        (inv.invoice_amount - inv.amount_paid)
        for inv in invoices
        if inv.status in ("unpaid", "partially_paid")
    )

    # Find oldest unpaid invoice and compute days overdue
    today = date.today()
    days_overdue: Optional[int] = None
    for inv in invoices:
        if inv.status in ("unpaid", "partially_paid") and inv.due_date:
            delta = (today - inv.due_date).days
            if delta > 0:
                days_overdue = delta
                break  # already ordered ASC by due_date, so first match = oldest

    invoice_history = [
        InvoiceSummaryItem(
            invoice_id=inv.id,
            invoice_amount=inv.invoice_amount,
            amount_paid=inv.amount_paid,
            due_date=inv.due_date,
            created_date=inv.created_date,
            status=inv.status,
        )
        for inv in invoices
    ]

    return CustomerSummaryResponse(
        customer_id=customer.id,
        customer_name=customer.name,
        outstanding_balance=round(outstanding_balance, 2),
        days_overdue=days_overdue,
        invoice_history=invoice_history,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Retrieve a single customer by ID."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    return customer


@router.post("/{customer_id}/send-reminder")
def send_customer_reminder(
    customer_id: str,
    channel: str = "sms",
    custom_message: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Send an SMS or WhatsApp payment reminder directly to a customer via Twilio.
    """
    from datetime import datetime, timezone
    from backend.app.models import AuditLog
    from backend.app.services.twilio_service import send_sms_or_whatsapp

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

    invoices = db.query(Invoice).filter(
        Invoice.customer_id == customer_id,
        Invoice.status.in_(["unpaid", "partially_paid"]),
    ).all()

    outstanding = sum(inv.invoice_amount - inv.amount_paid for inv in invoices)

    if custom_message:
        message_body = custom_message
    else:
        message_body = (
            f"Dear {customer.name}, this is a gentle reminder from MicroBiz Store regarding your "
            f"outstanding balance of INR {outstanding:,.2f}. Kindly arrange the payment at your convenience. Thank you!"
        )

    is_wa = (channel.lower() == "whatsapp")
    dispatch_res = send_sms_or_whatsapp(
        to_phone=customer.phone,
        message_body=message_body,
        is_whatsapp=is_wa,
    )

    now = datetime.now(timezone.utc)
    db.add(AuditLog(
        actor_type="MERCHANT",
        action="CUSTOMER_REMINDER_SENT",
        entity="customers",
        entity_id=customer.id,
        reason=f"Dispatched {channel.upper()} reminder: {dispatch_res.get('status')} to {dispatch_res.get('to')}",
        timestamp=now,
    ))
    db.commit()

    return {
        "customer_id": customer.id,
        "customer_name": customer.name,
        "phone": customer.phone,
        "channel": channel,
        "message": message_body,
        "twilio_result": dispatch_res,
    }

