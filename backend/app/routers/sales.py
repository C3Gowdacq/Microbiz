"""
routers/sales.py -- Endpoints for recording and listing sales.

Endpoints:
  POST  /api/sales        record a sale (decrements product current_stock atomically)
  GET   /api/sales        list all sales, filterable by product_id or date range

Phase 2: Stock decrement now goes through inventory_service.decrease_stock(),
which creates an InventoryEvent + AuditLog in the same transaction as the sale.
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Sale, Product, Customer, BusinessSettings
from backend.app.schemas import SaleCreate, SaleResponse
from backend.app.services.inventory_service import decrease_stock, EventType
from backend.app.services.inventory_risk_service import calculate_risk_metrics
from backend.app.services.replenishment_service import evaluate_and_trigger_replenishment

router = APIRouter(prefix="/api/sales", tags=["Sales"])


@router.post("", response_model=SaleResponse, status_code=201)
def record_sale(req: SaleCreate, db: Session = Depends(get_db)):
    """
    Record a new sale atomically:
    1. Validates product and optional customer exist.
    2. Calls inventory_service.decrease_stock() which:
       - Validates sufficient stock
       - Decrements product.current_stock
       - Creates an InventoryEvent record
       - Creates an AuditLog entry
    3. Creates the Sale record.
    4. Commits the entire transaction in one shot.
    5. Evaluates real-time inventory risk for the product.
    6. If autonomous mode is ON and risk is HIGH/CRITICAL: triggers replenishment agent.
    7. Returns enriched SaleResponse with inventory_risk.
    """
    # Validate product
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{req.product_id}' not found")

    if req.quantity <= 0:
        raise HTTPException(status_code=422, detail="quantity must be greater than 0")

    # Validate optional customer
    if req.customer_id:
        customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer '{req.customer_id}' not found")

    total_amount = round(req.quantity * req.unit_price, 2)

    try:
        # Phase 2: Use inventory service — validates stock and creates InventoryEvent + AuditLog
        decrease_stock(
            product_id     = req.product_id,
            quantity       = req.quantity,
            event_type     = EventType.SALE,
            reference_type = "sale",
            reference_id   = None,
            notes          = f"Sale: {req.quantity} x {product.name} @ {req.unit_price}",
            db             = db,
        )

        sale = Sale(
            product_id   = req.product_id,
            customer_id  = req.customer_id,
            date         = req.sale_date or date.today(),
            quantity     = req.quantity,
            unit_price   = req.unit_price,
            total_amount = total_amount,
        )
        db.add(sale)

        # Single atomic commit: stock decrement + inventory event + audit log + sale record
        db.commit()
        db.refresh(sale)
        db.refresh(product)

        # Phase 3 & 4: Calculate inventory risk on the updated stock
        risk_metrics = calculate_risk_metrics(product, db)

        # Phase 4 & 5: Check autonomous mode
        settings = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
        if settings and settings.autonomous_mode:
            if risk_metrics["risk_level"] in ("CRITICAL", "HIGH") or risk_metrics["reorder_needed"]:
                evaluate_and_trigger_replenishment(product.id, db)

        # Attach inventory_risk to response
        sale.inventory_risk = risk_metrics
        return sale

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record sale: {str(e)}")


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
