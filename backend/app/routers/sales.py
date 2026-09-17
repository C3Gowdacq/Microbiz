"""
routers/sales.py -- Endpoints for recording and listing sales.

Endpoints:
  POST  /api/sales        record a sale (decrements product current_stock)
  GET   /api/sales        list all sales, filterable by product_id or date range
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Sale, Product, Customer
from backend.app.schemas import SaleCreate, SaleResponse

router = APIRouter(prefix="/api/sales", tags=["Sales"])


@router.post("", response_model=SaleResponse, status_code=201)
def record_sale(req: SaleCreate, db: Session = Depends(get_db)):
    """
    Record a new sale.
    - Validates that the product exists.
    - Validates optional customer exists if provided.
    - Computes total_amount = quantity * unit_price.
    - Decrements product.current_stock by quantity (cannot go below 0).
    """
    # Validate product
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{req.product_id}' not found")

    if req.quantity <= 0:
        raise HTTPException(status_code=422, detail="quantity must be greater than 0")

    if product.current_stock < req.quantity:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Insufficient stock for '{product.name}': "
                f"available={product.current_stock}, requested={req.quantity}"
            ),
        )

    # Validate optional customer
    if req.customer_id:
        customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer '{req.customer_id}' not found")

    total_amount = round(req.quantity * req.unit_price, 2)

    sale = Sale(
        product_id=req.product_id,
        customer_id=req.customer_id,
        date=req.sale_date or date.today(),
        quantity=req.quantity,
        unit_price=req.unit_price,
        total_amount=total_amount,
    )
    db.add(sale)

    # Decrement stock
    product.current_stock = round(product.current_stock - req.quantity, 4)

    db.commit()
    db.refresh(sale)
    return sale


@router.get("", response_model=List[SaleResponse])
def list_sales(
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    date_from:  Optional[date] = Query(None, description="Filter sales on or after this date"),
    date_to:    Optional[date] = Query(None, description="Filter sales on or before this date"),
    db: Session = Depends(get_db),
):
    """List all sales, optionally filtered by product_id and/or date range."""
    query = db.query(Sale)
    if product_id:
        query = query.filter(Sale.product_id == product_id)
    if date_from:
        query = query.filter(Sale.date >= date_from)
    if date_to:
        query = query.filter(Sale.date <= date_to)
    return query.order_by(Sale.date.desc(), Sale.id.desc()).all()
