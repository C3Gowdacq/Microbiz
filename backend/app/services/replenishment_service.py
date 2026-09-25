"""
backend/app/services/replenishment_service.py

Phase 5: Replenishment Engine with Deduplication.

Evaluates product inventory risk and automatically creates pending
HITL Recommendations for replenishment when stock is at risk.
Strictly prevents duplicate active recommendations for the same product.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

# Ensure paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "src")))

from backend.app.models import Product, Recommendation, BusinessSettings
from backend.app.services.inventory_risk_service import calculate_risk_metrics


ACTIVE_STATUSES = ["pending", "approved", "ordered"]


def get_active_replenishment_recommendation(
    product_id: str,
    db: Session,
) -> Optional[Recommendation]:
    """
    Check if an active (pending, approved, or ordered) recommendation
    already exists for this product in the inventory module.
    """
    return (
        db.query(Recommendation)
        .filter(
            Recommendation.module == "inventory",
            Recommendation.entity_type == "product",
            Recommendation.entity_id == product_id,
            Recommendation.status.in_(ACTIVE_STATUSES),
        )
        .first()
    )


def evaluate_and_trigger_replenishment(
    product_id: str,
    db: Session,
    force: bool = False,
) -> Tuple[Optional[Recommendation], bool]:
    """
    Evaluate inventory risk for a product and create a replenishment recommendation
    if necessary and not already active (deduplication).

    Args:
        product_id: Product ID
        db: Database session
        force: If True, bypass risk threshold check (still obeys deduplication)

    Returns:
        (Recommendation, was_created: bool)
        If an active recommendation already exists, returns (existing_rec, False).
        If a new recommendation was created, returns (new_rec, True).
        If no recommendation is needed, returns (None, False).
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return (None, False)

    # Calculate current risk metrics
    metrics = calculate_risk_metrics(product, db)

    # Check if replenishment is needed
    needs_reorder = (
        metrics["risk_level"] in ("CRITICAL", "HIGH", "MEDIUM")
        or metrics["reorder_needed"]
        or metrics["recommended_order_qty"] > 0
    )

    if not needs_reorder and not force:
        return (None, False)

    # Deduplication check: Do not create duplicate active recommendations
    existing = get_active_replenishment_recommendation(product_id, db)
    if existing:
        return (existing, False)

    # Format recommendation details
    risk_level = metrics["risk_level"]
    priority = "critical" if risk_level == "CRITICAL" else ("high" if risk_level == "HIGH" else "medium")
    action = "urgent_replenishment" if risk_level == "CRITICAL" else "full_replenishment"

    order_qty = metrics["recommended_order_qty"]
    if order_qty <= 0:
        order_qty = max(product.reorder_level, 10.0)

    unit_cost = product.cost_price if product.cost_price > 0 else round(product.selling_price * 0.7, 2)
    total_cost = round(order_qty * unit_cost, 2)
    cov_days_str = f"{metrics['coverage_days']} days" if metrics["coverage_days"] is not None else "N/A"

    reason = (
        f"Inventory alert ({risk_level}): '{product.name}' stock is {metrics['current_stock']} "
        f"(coverage: {cov_days_str}, ROP: {metrics['reorder_point']}). "
        f"Recommended reorder quantity: {order_qty} units (estimated cost: ₹{total_cost:,.2f})."
    )

    secondary = [
        {
            "action": "create_purchase_order",
            "product_id": product.id,
            "product_name": product.name,
            "quantity": order_qty,
            "unit_cost": unit_cost,
            "total_cost": total_cost,
            "lead_time_days": metrics["lead_time_days"],
        }
    ]

    rec = Recommendation(
        module="inventory",
        entity_type="product",
        entity_id=product.id,
        primary_action=action,
        priority=priority,
        reason=reason,
        secondary_recommendations=secondary,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )

    db.add(rec)
    db.commit()
    db.refresh(rec)

    return (rec, True)
