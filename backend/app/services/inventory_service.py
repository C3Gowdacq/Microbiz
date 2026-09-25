"""
backend/app/services/inventory_service.py

Inventory Transaction Engine — Phase 2.

All stock changes MUST go through this service. It:
  1. Validates the operation (cannot go negative, cannot use unknown product)
  2. Updates product.current_stock atomically
  3. Creates an immutable InventoryEvent record
  4. Writes an AuditLog entry

Public API:
  - get_stock(product_id, db)                -> float
  - increase_stock(product_id, qty, ..., db) -> InventoryEvent
  - decrease_stock(product_id, qty, ..., db) -> InventoryEvent
  - adjust_stock(product_id, new_qty, ..., db) -> InventoryEvent

IMPORTANT: This module does NOT call db.commit(). The caller is responsible
for committing the transaction. This allows the caller to include the
inventory change in a larger atomic transaction (e.g., a sale creation).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.models import Product, InventoryEvent, AuditLog


# ── Public constants for event types ─────────────────────────────────────────

class EventType:
    SALE               = "SALE"
    PURCHASE_RECEIVED  = "PURCHASE_RECEIVED"
    MANUAL_ADJUSTMENT  = "MANUAL_ADJUSTMENT"
    STOCK_ADD          = "STOCK_ADD"
    RETURN             = "RETURN"
    DAMAGE             = "DAMAGE"
    OPENING_STOCK      = "OPENING_STOCK"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_product_or_404(product_id: str, db: Session) -> Product:
    """Fetch a product or raise HTTP 404."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")
    return product


def _create_inventory_event(
    product: Product,
    event_type: str,
    quantity_change: float,
    reference_type: Optional[str],
    reference_id: Optional[str],
    notes: Optional[str],
    db: Session,
) -> InventoryEvent:
    """
    Create an InventoryEvent record capturing the before/after state.
    Does NOT commit — caller must commit.
    """
    quantity_before = round(product.current_stock, 4)
    quantity_after  = round(product.current_stock + quantity_change, 4)

    event = InventoryEvent(
        product_id      = product.id,
        event_type      = event_type,
        quantity_before = quantity_before,
        quantity_change = round(quantity_change, 4),
        quantity_after  = quantity_after,
        reference_type  = reference_type,
        reference_id    = reference_id,
        notes           = notes,
        created_at      = datetime.utcnow(),
    )
    db.add(event)
    return event


def _write_audit_log(
    actor_type: str,
    action: str,
    entity_id: str,
    old_stock: float,
    new_stock: float,
    reason: Optional[str],
    db: Session,
) -> None:
    """Write an AuditLog entry for a stock change. Does NOT commit."""
    log = AuditLog(
        actor_type = actor_type,
        actor_id   = "inventory_service",
        action     = action,
        entity     = "products",
        entity_id  = entity_id,
        old_value  = {"current_stock": old_stock},
        new_value  = {"current_stock": new_stock},
        reason     = reason,
        timestamp  = datetime.utcnow(),
    )
    db.add(log)


# ── Public API ────────────────────────────────────────────────────────────────

def get_stock(product_id: str, db: Session) -> float:
    """
    Return the current stock level for a product.
    Raises HTTP 404 if product not found.
    """
    product = _get_product_or_404(product_id, db)
    return product.current_stock


def decrease_stock(
    product_id:     str,
    quantity:       float,
    event_type:     str = EventType.SALE,
    reference_type: Optional[str] = None,
    reference_id:   Optional[str] = None,
    notes:          Optional[str] = None,
    db:             Session = None,
) -> InventoryEvent:
    """
    Decrease product stock by `quantity`.

    Args:
        product_id:     Product to decrease stock for.
        quantity:       Amount to decrease (must be > 0).
        event_type:     Reason category (EventType.SALE, DAMAGE, etc.).
        reference_type: Type of the triggering record ('sale', 'damage_report').
        reference_id:   ID of the triggering record.
        notes:          Optional human-readable explanation.
        db:             Database session.

    Raises:
        HTTPException 422: If quantity <= 0 or insufficient stock.
        HTTPException 404: If product not found.

    Returns:
        The created InventoryEvent (not yet committed).
    """
    if quantity <= 0:
        raise HTTPException(status_code=422, detail="Quantity to decrease must be > 0")

    product = _get_product_or_404(product_id, db)

    if product.current_stock < quantity:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Insufficient stock for '{product.name}' (SKU: {product.sku}): "
                f"available={product.current_stock:.2f}, requested={quantity:.2f}"
            ),
        )

    # IMPORTANT: Capture BEFORE value BEFORE mutating product.current_stock
    quantity_before = round(product.current_stock, 4)
    quantity_after  = round(product.current_stock - quantity, 4)

    # Mutate stock
    product.current_stock = quantity_after

    # Create the event using pre-computed before/after values
    event = InventoryEvent(
        product_id      = product_id,
        event_type      = event_type,
        quantity_before = quantity_before,
        quantity_change = round(-quantity, 4),
        quantity_after  = quantity_after,
        reference_type  = reference_type,
        reference_id    = reference_id,
        notes           = notes,
        created_at      = datetime.utcnow(),
    )
    db.add(event)

    _write_audit_log(
        actor_type = "SYSTEM",
        action     = "STOCK_DECREASED",
        entity_id  = product_id,
        old_stock  = quantity_before,
        new_stock  = quantity_after,
        reason     = notes or f"{event_type} of {quantity} units",
        db         = db,
    )

    return event


def increase_stock(
    product_id:     str,
    quantity:       float,
    event_type:     str = EventType.STOCK_ADD,
    reference_type: Optional[str] = None,
    reference_id:   Optional[str] = None,
    notes:          Optional[str] = None,
    db:             Session = None,
) -> InventoryEvent:
    """
    Increase product stock by `quantity`.

    Args:
        product_id:     Product to increase stock for.
        quantity:       Amount to increase (must be > 0).
        event_type:     Reason category (EventType.PURCHASE_RECEIVED, RETURN, etc.).
        reference_type: Type of the triggering record ('purchase_order').
        reference_id:   ID of the triggering record.
        notes:          Optional human-readable explanation.
        db:             Database session.

    Raises:
        HTTPException 422: If quantity <= 0.
        HTTPException 404: If product not found.

    Returns:
        The created InventoryEvent (not yet committed).
    """
    if quantity <= 0:
        raise HTTPException(status_code=422, detail="Quantity to increase must be > 0")

    product = _get_product_or_404(product_id, db)

    # IMPORTANT: Capture BEFORE value BEFORE mutating product.current_stock
    quantity_before = round(product.current_stock, 4)
    quantity_after  = round(product.current_stock + quantity, 4)

    product.current_stock = quantity_after

    event = InventoryEvent(
        product_id      = product_id,
        event_type      = event_type,
        quantity_before = quantity_before,
        quantity_change = round(quantity, 4),
        quantity_after  = quantity_after,
        reference_type  = reference_type,
        reference_id    = reference_id,
        notes           = notes,
        created_at      = datetime.utcnow(),
    )
    db.add(event)

    _write_audit_log(
        actor_type = "SYSTEM",
        action     = "STOCK_INCREASED",
        entity_id  = product_id,
        old_stock  = quantity_before,
        new_stock  = quantity_after,
        reason     = notes or f"{event_type} of {quantity} units",
        db         = db,
    )

    return event


def adjust_stock(
    product_id:   str,
    new_quantity: float,
    notes:        Optional[str] = None,
    db:           Session = None,
) -> InventoryEvent:
    """
    Set product stock to an absolute `new_quantity`.
    Used for manual adjustments and physical stock counts.

    Args:
        product_id:   Product to adjust.
        new_quantity: New absolute stock level (must be >= 0).
        notes:        Optional reason for adjustment.
        db:           Database session.

    Raises:
        HTTPException 422: If new_quantity < 0.
        HTTPException 404: If product not found.

    Returns:
        The created InventoryEvent (not yet committed).
    """
    if new_quantity < 0:
        raise HTTPException(status_code=422, detail="Stock cannot be set to a negative value")

    product = _get_product_or_404(product_id, db)

    # IMPORTANT: Capture BEFORE value BEFORE mutating product.current_stock
    quantity_before = round(product.current_stock, 4)
    quantity_after  = round(new_quantity, 4)
    quantity_change = round(new_quantity - quantity_before, 4)

    product.current_stock = quantity_after

    event = InventoryEvent(
        product_id      = product_id,
        event_type      = EventType.MANUAL_ADJUSTMENT,
        quantity_before = quantity_before,
        quantity_change = quantity_change,
        quantity_after  = quantity_after,
        reference_type  = "manual",
        reference_id    = None,
        notes           = notes or "Manual stock adjustment",
        created_at      = datetime.utcnow(),
    )
    db.add(event)

    _write_audit_log(
        actor_type = "MERCHANT",
        action     = "STOCK_ADJUSTED",
        entity_id  = product_id,
        old_stock  = quantity_before,
        new_stock  = quantity_after,
        reason     = notes or "Manual stock count/adjustment",
        db         = db,
    )

    return event
