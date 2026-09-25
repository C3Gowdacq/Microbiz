"""
backend/app/services/inventory_risk_service.py

Phase 3: Demand & Inventory Risk Engine.

Combines ML-powered demand forecasting (or velocity fallback) with
inventory parameters (lead time, safety stock, reorder level) and
shop-wide operational settings from BusinessSettings to calculate
complete inventory risk metrics for any product.

Outputs:
  - avg_daily_demand: Expected units demanded per day
  - forecast_demand: Total predicted units over horizon_days
  - lead_time_days: Supplier lead time in days
  - lead_time_demand: avg_daily_demand * lead_time_days
  - safety_stock: Configured or computed safety buffer
  - reorder_point: Threshold where replenishment must trigger
  - current_stock: Units currently on hand
  - coverage_days: Days of demand remaining on hand
  - recommended_order_qty: Optimal reorder quantity to reach target inventory
  - risk_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "HEALTHY"
  - reorder_needed: bool
  - model_used: "random_forest" | "velocity_fallback"
"""

import os
import sys
import math
from typing import Optional, Dict, Any, List
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

# Ensure paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "src")))

from backend.app.models import Product, Sale, BusinessSettings
from backend.app.services.feature_vector_builder import forecast_product_demand


# ── Operational Settings Helper ───────────────────────────────────────────────

def _get_business_settings(db: Session) -> BusinessSettings:
    """Retrieve or initialize singleton BusinessSettings."""
    settings = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
    if not settings:
        settings = BusinessSettings(
            id=1,
            min_cash_reserve=25000.0,
            currency="INR",
            safety_stock_days=3,
            review_period_days=7,
            khata_overdue_days=30,
            expense_anomaly_threshold_pct=30.0,
            high_risk_multiplier=1.0,
            medium_risk_multiplier=1.5,
            autonomous_mode=False,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def _compute_velocity_fallback(product_id: str, db: Session, lookback_days: int = 30) -> float:
    """Compute average daily units sold over past lookback_days."""
    since = date.today() - timedelta(days=lookback_days)
    total_qty = db.query(func.coalesce(func.sum(Sale.quantity), 0.0)) \
        .filter(Sale.product_id == product_id, Sale.date >= since).scalar()
    return float(total_qty) / max(lookback_days, 1)


# ── Core Risk Calculation ─────────────────────────────────────────────────────

def calculate_risk_metrics(
    product: Product,
    db: Session,
    horizon_days: int = 7,
) -> Dict[str, Any]:
    """
    Calculate comprehensive inventory risk metrics for a product.

    Args:
        product: SQLAlchemy Product instance
        db: Database session
        horizon_days: Forecasting horizon in days (default: 7)

    Returns:
        Structured dict with all risk and replenishment metrics.
    """
    settings = _get_business_settings(db)

    # 1. Obtain demand forecast
    model_used = "velocity_fallback"
    scaling_factor = 1.0
    try:
        forecast_res = forecast_product_demand(product, db, horizon_days=horizon_days)
        forecast_demand = float(forecast_res.get("predicted_units", 0.0))
        model_used = forecast_res.get("model_used", "random_forest")
        scaling_factor = float(forecast_res.get("scaling_factor", 1.0))
    except Exception:
        # Fallback directly to sales velocity
        avg_units = _compute_velocity_fallback(product.id, db, lookback_days=30)
        forecast_demand = avg_units * horizon_days
        model_used = "velocity_fallback"
        scaling_factor = 1.0

    # Ensure baseline demand if below reorder level but no historical sales
    if (product.current_stock < product.reorder_level or forecast_demand <= 0.0) and product.reorder_level > 0:
        forecast_demand = max(forecast_demand, product.reorder_level * (horizon_days / 7.0))

    avg_daily_demand = forecast_demand / max(horizon_days, 1)

    # 2. Parameters
    lead_time_days = max(1, int(product.lead_time_days or 1))
    lead_time_demand = avg_daily_demand * lead_time_days

    # Safety stock: use product explicit value or calculate from business settings
    if product.safety_stock is not None and product.safety_stock > 0:
        safety_stock = float(product.safety_stock)
    else:
        safety_stock_days = settings.safety_stock_days if settings.safety_stock_days is not None else 3
        safety_stock = avg_daily_demand * safety_stock_days

    # Reorder point: threshold where replenishment is required
    # reorder_point = lead_time_demand + safety_stock (or product.reorder_level if higher)
    computed_rop = lead_time_demand + safety_stock
    if product.reorder_level is not None and product.reorder_level > 0:
        reorder_point = max(float(product.reorder_level), computed_rop)
    else:
        reorder_point = computed_rop

    current_stock = float(product.current_stock or 0.0)

    # 3. Coverage days
    if avg_daily_demand > 0:
        coverage_days = current_stock / avg_daily_demand
    else:
        coverage_days = None

    # 4. Stock gap
    stock_gap = max(0.0, forecast_demand - current_stock)

    # 5. Risk Level Classification
    high_mult = settings.high_risk_multiplier if settings.high_risk_multiplier is not None else 1.0
    med_mult = settings.medium_risk_multiplier if settings.medium_risk_multiplier is not None else 1.5

    if current_stock <= 0:
        if avg_daily_demand > 0 or product.reorder_level > 0:
            risk_level = "CRITICAL"
        else:
            risk_level = "HEALTHY"
    elif coverage_days is not None:
        if coverage_days <= 1.0:
            risk_level = "CRITICAL"
        elif coverage_days <= (lead_time_days * high_mult) or current_stock <= (reorder_point * 0.75):
            risk_level = "HIGH"
        elif coverage_days <= (lead_time_days * med_mult) or current_stock <= reorder_point:
            risk_level = "MEDIUM"
        elif coverage_days <= (lead_time_days * 3.0):
            risk_level = "LOW"
        else:
            risk_level = "HEALTHY"
    else:
        # Zero demand expected
        if product.reorder_level > 0 and current_stock <= product.reorder_level:
            risk_level = "MEDIUM"
        else:
            risk_level = "HEALTHY"

    # 6. Recommended Order Quantity
    # Review period target stock = lead_time_demand + safety_stock + (avg_daily_demand * review_period_days)
    review_period = settings.review_period_days if settings.review_period_days is not None else 7
    target_inventory = lead_time_demand + safety_stock + (avg_daily_demand * review_period)

    reorder_needed = (current_stock <= reorder_point) or (risk_level in ("CRITICAL", "HIGH", "MEDIUM"))

    if reorder_needed:
        order_qty = max(0.0, target_inventory - current_stock)
        # Also ensure at least covers stock_gap + safety_stock
        order_qty = max(order_qty, forecast_demand + safety_stock - current_stock)
        recommended_order_qty = round(order_qty, 2)
    else:
        recommended_order_qty = 0.0

    return {
        "product_id": product.id,
        "product_name": product.name,
        "sku": product.sku,
        "current_stock": round(current_stock, 2),
        "avg_daily_demand": round(avg_daily_demand, 2),
        "forecast_demand": round(forecast_demand, 2),
        "horizon_days": horizon_days,
        "lead_time_days": lead_time_days,
        "lead_time_demand": round(lead_time_demand, 2),
        "safety_stock": round(safety_stock, 2),
        "reorder_point": round(reorder_point, 2),
        "coverage_days": round(coverage_days, 2) if coverage_days is not None else None,
        "stock_gap": round(stock_gap, 2),
        "risk_level": risk_level,
        "reorder_needed": reorder_needed,
        "recommended_order_qty": recommended_order_qty,
        "model_used": model_used,
        "scaling_factor": round(scaling_factor, 4),
    }


def get_product_risk_summary(
    product_id: str,
    db: Session,
    horizon_days: int = 7,
) -> Optional[Dict[str, Any]]:
    """Retrieve risk metrics for a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    return calculate_risk_metrics(product, db, horizon_days=horizon_days)


def evaluate_all_products_risk(
    db: Session,
    horizon_days: int = 7,
) -> List[Dict[str, Any]]:
    """Calculate risk metrics across all products in the database."""
    products = db.query(Product).all()
    results = []
    for p in products:
        results.append(calculate_risk_metrics(p, db, horizon_days=horizon_days))
    return results
