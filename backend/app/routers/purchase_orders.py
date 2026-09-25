"""
routers/purchase_orders.py -- Full lifecycle management for Purchase Orders.

Endpoints:
  GET    /api/purchase-orders             list all POs (filterable by status, supplier)
  POST   /api/purchase-orders             create a new PO with line items
  GET    /api/purchase-orders/{id}        get PO details with line items and supplier
  PATCH  /api/purchase-orders/{id}/status update PO status (approval, order dispatch)
  POST   /api/purchase-orders/{id}/receive mark received and automatically increment stock
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.app.database import get_db
from backend.app.models import (
    PurchaseOrder,
    PurchaseOrderItem,
    Product,
    Supplier,
    AuditLog,
)
from backend.app.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderStatusUpdate,
    PurchaseOrderResponse,
    PurchaseOrderItemResponse,
)
from backend.app.services.inventory_service import increase_stock, EventType

router = APIRouter(prefix="/api/purchase-orders", tags=["Purchase Orders"])


def _generate_po_number(db: Session) -> str:
    """Generate human-readable sequential PO number e.g. PO-2026-0001."""
    year = datetime.now(timezone.utc).year
    count = db.query(PurchaseOrder).count() + 1
    return f"PO-{year}-{count:04d}"


def _format_po_response(po: PurchaseOrder) -> Dict[str, Any]:
    """Format PurchaseOrder ORM model with supplier and product details."""
    items = []
    for item in po.items:
        items.append({
            "id": item.id,
            "purchase_order_id": item.purchase_order_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_cost": item.unit_cost,
            "total_cost": item.total_cost,
            "product_name": item.product.name if item.product else None,
            "product_sku": item.product.sku if item.product else None,
        })

    return {
        "id": po.id,
        "po_number": po.po_number,
        "supplier_id": po.supplier_id,
        "supplier_name": po.supplier.name if po.supplier else None,
        "status": po.status,
        "total_amount": round(po.total_amount, 2),
        "priority": po.priority,
        "reason": po.reason,
        "notes": po.notes,
        "created_at": po.created_at,
        "approved_at": po.approved_at,
        "ordered_at": po.ordered_at,
        "received_at": po.received_at,
        "items": items,
    }


@router.get("", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    db: Session = Depends(get_db),
):
    """List purchase orders with optional status or supplier filter."""
    query = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.supplier),
        joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
    )
    if status:
        query = query.filter(PurchaseOrder.status == status.upper())
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)

    pos = query.order_by(PurchaseOrder.created_at.desc(), PurchaseOrder.id.desc()).all()
    return [_format_po_response(po) for po in pos]


@router.post("", response_model=PurchaseOrderResponse, status_code=201)
def create_purchase_order(req: PurchaseOrderCreate, db: Session = Depends(get_db)):
    """Create a new purchase order with one or more line items."""
    if not req.items:
        raise HTTPException(status_code=422, detail="Purchase order must contain at least one item")

    if req.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == req.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail=f"Supplier #{req.supplier_id} not found")

    po_number = _generate_po_number(db)
    now = datetime.now(timezone.utc)

    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=req.supplier_id,
        status="PENDING_APPROVAL",
        priority=req.priority or "medium",
        reason=req.reason,
        notes=req.notes,
        created_at=now,
    )
    db.add(po)
    db.flush()

    total_amount = 0.0
    for itm in req.items:
        product = db.query(Product).filter(Product.id == itm.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Product '{itm.product_id}' not found")

        unit_cost = itm.unit_cost if itm.unit_cost > 0 else (product.cost_price or 0.0)
        item_total = round(itm.quantity * unit_cost, 2)
        total_amount += item_total

        po_item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=itm.product_id,
            quantity=itm.quantity,
            unit_cost=unit_cost,
            total_cost=item_total,
        )
        db.add(po_item)

    po.total_amount = round(total_amount, 2)

    # Audit log entry
    audit = AuditLog(
        actor_type="MERCHANT",
        action="PURCHASE_ORDER_CREATED",
        entity="purchase_orders",
        entity_id=str(po.id),
        reason=f"Created PO {po.po_number} with {len(req.items)} items, total ₹{po.total_amount:,.2f}",
        timestamp=now,
    )
    db.add(audit)

    db.commit()
    db.refresh(po)
    return _format_po_response(po)


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)):
    """Get purchase order details by ID."""
    po = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
        )
        .filter(PurchaseOrder.id == po_id)
        .first()
    )
    if not po:
        raise HTTPException(status_code=404, detail=f"Purchase order #{po_id} not found")
    return _format_po_response(po)


@router.patch("/{po_id}/status", response_model=PurchaseOrderResponse)
def update_po_status(
    po_id: int,
    req: PurchaseOrderStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Update purchase order status.
    Supported transitions:
      - PENDING_APPROVAL -> APPROVED | REJECTED | CANCELLED
      - APPROVED -> ORDERED | CANCELLED
      - ORDERED -> RECEIVED (or call /receive endpoint)
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail=f"Purchase order #{po_id} not found")

    new_status = req.status.upper()
    valid_statuses = ["DRAFT", "PENDING_APPROVAL", "APPROVED", "REJECTED", "ORDERED", "RECEIVED", "CANCELLED"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=422, detail=f"Invalid status '{req.status}'. Must be one of {valid_statuses}")

    now = datetime.now(timezone.utc)
    old_status = po.status
    po.status = new_status

    if new_status == "APPROVED" and not po.approved_at:
        po.approved_at = now
    elif new_status == "ORDERED" and not po.ordered_at:
        po.ordered_at = now

    if req.notes:
        po.notes = f"{po.notes}\n{req.notes}" if po.notes else req.notes

    audit = AuditLog(
        actor_type="MERCHANT",
        action="PO_STATUS_CHANGED",
        entity="purchase_orders",
        entity_id=str(po.id),
        reason=f"Status changed from {old_status} to {new_status} for {po.po_number}",
        timestamp=now,
    )
    db.add(audit)

    db.commit()
    db.refresh(po)
    return _format_po_response(po)


@router.post("/{po_id}/receive", response_model=PurchaseOrderResponse)
def receive_purchase_order(po_id: int, db: Session = Depends(get_db)):
    """
    Mark purchase order as RECEIVED and increment inventory:
    1. Validates PO is not already received or cancelled.
    2. Increments stock for each item via inventory_service.increase_stock().
    3. Creates immutable InventoryEvent (PURCHASE_RECEIVED) for each line item.
    4. Marks PO status as RECEIVED with received_at timestamp.
    5. Writes an AuditLog record.
    All committed atomically.
    """
    po = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
        )
        .filter(PurchaseOrder.id == po_id)
        .first()
    )
    if not po:
        raise HTTPException(status_code=404, detail=f"Purchase order #{po_id} not found")

    if po.status == "RECEIVED":
        raise HTTPException(status_code=400, detail=f"Purchase order {po.po_number} is already marked RECEIVED")
    if po.status in ("CANCELLED", "REJECTED"):
        raise HTTPException(status_code=400, detail=f"Cannot receive {po.status.lower()} purchase order {po.po_number}")

    now = datetime.now(timezone.utc)

    try:
        # Increment stock for each item
        for item in po.items:
            increase_stock(
                product_id=item.product_id,
                quantity=item.quantity,
                event_type=EventType.PURCHASE_RECEIVED,
                reference_type="purchase_order",
                reference_id=str(po.id),
                notes=f"Received via {po.po_number} ({item.quantity} units)",
                db=db,
            )

        po.status = "RECEIVED"
        po.received_at = now

        audit = AuditLog(
            actor_type="MERCHANT",
            action="PURCHASE_ORDER_RECEIVED",
            entity="purchase_orders",
            entity_id=str(po.id),
            reason=f"Received PO {po.po_number}: stock incremented for {len(po.items)} items",
            timestamp=now,
        )
        db.add(audit)

        db.commit()
        db.refresh(po)
        return _format_po_response(po)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to receive purchase order: {str(e)}")
