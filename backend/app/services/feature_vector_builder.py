"""
backend/app/services/feature_vector_builder.py

Builds the exact 25-feature numpy array the trained Random Forest model expects
from real Product DB data + sales history + current date.

ARCHITECTURE:
  The RF model is a STORE-LEVEL daily revenue forecaster (trained on Rossmann data).
  It predicts: "How much total revenue will a store make on a given day?"

  To produce PRODUCT-LEVEL demand forecasts, we use the proportional allocation
  + scaling factor approach:

  1. RF model predicts total store revenue for the next N days
  2. DB history gives each product's share of total revenue
  3. Scaling factor = RF_prediction / historical_baseline
  4. Product forecast = product_avg_daily_sales × N × scaling_factor

  This way:
  - The ML model adds value by understanding promos, holidays, weekends, competition
  - The sales history adds product-level granularity
  - Together they produce meaningful per-product demand forecasts
"""

import os
import sys
from datetime import date, timedelta
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func

# Ensure ml/src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "src")))

from columns import FEATURE_COLS
from backend.app.models import Product, Sale


# ── Feature Vector Construction ───────────────────────────────────────────────

def _compute_rolling_avg(product_id: str, db: Session, days: int) -> float:
    """Average daily sales revenue for a product over the last `days` days."""
    since = date.today() - timedelta(days=days)
    total = float(
        db.query(func.coalesce(func.sum(Sale.total_amount), 0.0))
        .filter(Sale.product_id == product_id, Sale.date >= since)
        .scalar()
    )
    return total / max(days, 1)


def _compute_sales_growth(product_id: str, db: Session) -> float:
    """
    Sales growth rate: (yesterday's sales - 8-days-ago sales) / (8-days-ago + 1).
    Mirrors the Rossmann preprocessing logic.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    eight_ago = today - timedelta(days=8)

    sales_yesterday = float(
        db.query(func.coalesce(func.sum(Sale.total_amount), 0.0))
        .filter(Sale.product_id == product_id, Sale.date == yesterday)
        .scalar()
    )
    sales_eight_ago = float(
        db.query(func.coalesce(func.sum(Sale.total_amount), 0.0))
        .filter(Sale.product_id == product_id, Sale.date == eight_ago)
        .scalar()
    )
    return (sales_yesterday - sales_eight_ago) / (sales_eight_ago + 1.0)


def build_feature_vector(product: Product, db: Session) -> np.ndarray:
    """
    Build the 25-feature numpy array that the trained RF model expects,
    from a Product's ML profile fields + sales history + current date.

    Raises ValueError if the product is missing required ML fields
    (store_type, assortment).

    Feature vector order matches FEATURE_COLS from columns.py:
      X_COLS: Promo, Promo2, promo_period_length, SchoolHoliday,
              day_of_week, month, is_weekend,
              rolling_avg_7, rolling_avg_30, sales_growth,
              StateHoliday_a, StateHoliday_b, StateHoliday_c, StateHoliday_none
      A_COLS: StoreType_a, StoreType_b, StoreType_c, StoreType_d,
              Assortment_a, Assortment_b, Assortment_c
      B_COLS: CompetitionDistance, competition_open_days,
              has_competition_data, has_promo2_data
    """
    # ── Validate required fields ──────────────────────────────────────────
    missing = []
    if not product.store_type:
        missing.append("store_type")
    if not product.assortment:
        missing.append("assortment")
    if missing:
        raise ValueError(
            f"Product '{product.name}' (ID: {product.id}) is missing required ML profile "
            f"fields: {', '.join(missing)}. Fill these in before running ML-powered forecasts."
        )

    # Validate enum values
    if product.store_type not in ('a', 'b', 'c', 'd'):
        raise ValueError(f"store_type must be one of 'a','b','c','d', got '{product.store_type}'")
    if product.assortment not in ('a', 'b', 'c'):
        raise ValueError(f"assortment must be one of 'a','b','c', got '{product.assortment}'")

    today = date.today()

    # ── Group X: Temporal / Promo features ────────────────────────────────
    promo = 1 if product.promo_active else 0
    promo2 = 1 if product.promo2 else 0

    # promo_period_length: days since promo2 started (0 if no promo2)
    # Known simplification: we don't have a promo2_start_date field,
    # so this defaults to 0. Document in project report.
    promo_period_length = 0

    school_holiday = 1 if product.school_holiday else 0
    day_of_week = today.weekday()  # Monday=0, Sunday=6
    month = today.month
    is_weekend = 1 if day_of_week in (5, 6) else 0

    # Rolling averages and growth from sales history (revenue-based to match Rossmann)
    rolling_avg_7 = _compute_rolling_avg(product.id, db, 7)
    rolling_avg_30 = _compute_rolling_avg(product.id, db, 30)
    sales_growth = _compute_sales_growth(product.id, db)

    # StateHoliday: default to 'none' (one-hot)
    # In a production system, this would come from a holiday calendar API
    state_holiday_a = 0
    state_holiday_b = 0
    state_holiday_c = 0
    state_holiday_none = 1

    # ── Group A: Store type & assortment (one-hot) ────────────────────────
    store_type_a = 1 if product.store_type == 'a' else 0
    store_type_b = 1 if product.store_type == 'b' else 0
    store_type_c = 1 if product.store_type == 'c' else 0
    store_type_d = 1 if product.store_type == 'd' else 0

    assortment_a = 1 if product.assortment == 'a' else 0
    assortment_b = 1 if product.assortment == 'b' else 0
    assortment_c = 1 if product.assortment == 'c' else 0

    # ── Group B: Competition features ─────────────────────────────────────
    competition_distance = product.competition_distance if product.competition_distance else 75860.0
    # 75860.0 is the max from the Rossmann dataset (signals "no known competitor nearby")

    has_competition_data = 1 if product.competition_distance is not None else 0

    competition_open_days = 0
    if product.competition_open_date and has_competition_data:
        delta = (today - product.competition_open_date).days
        competition_open_days = max(0, delta)

    has_promo2_data = 1 if product.promo2 else 0

    # ── Assemble in FEATURE_COLS order ────────────────────────────────────
    feature_vector = np.array([
        # X_COLS
        promo, promo2, promo_period_length, school_holiday,
        day_of_week, month, is_weekend,
        rolling_avg_7, rolling_avg_30, sales_growth,
        state_holiday_a, state_holiday_b, state_holiday_c, state_holiday_none,
        # A_COLS
        store_type_a, store_type_b, store_type_c, store_type_d,
        assortment_a, assortment_b, assortment_c,
        # B_COLS
        competition_distance, competition_open_days,
        has_competition_data, has_promo2_data,
    ], dtype=np.float64)

    assert len(feature_vector) == len(FEATURE_COLS), (
        f"Feature vector length {len(feature_vector)} != expected {len(FEATURE_COLS)}"
    )

    return feature_vector


# ── Proportional Product-Level Forecasting ────────────────────────────────────

def forecast_product_demand(
    product: Product,
    db: Session,
    horizon_days: int = 7,
) -> dict:
    """
    Produce a product-level demand forecast using the trained RF model +
    proportional allocation.

    Returns dict:
      {
        "predicted_sales": float,     # product's predicted demand in revenue
        "predicted_units": float,     # demand in units (revenue / selling_price)
        "model_used": str,            # "random_forest" or "velocity_fallback"
        "scaling_factor": float,      # RF uplift/decline factor vs historical baseline
        "store_predicted_total": float,  # total store revenue predicted by RF
        "store_historical_avg": float,   # historical daily avg for comparison
      }

    Falls back to simple velocity average if product lacks ML profile fields.
    """
    from agents.sales_agent import get_multi_day_forecast

    # Check if product has ML fields
    if not product.store_type or not product.assortment:
        # Fallback: simple velocity average
        avg_daily = _compute_product_avg_daily_units(product.id, db, 30)
        predicted_units = avg_daily * horizon_days
        if (product.current_stock < product.reorder_level or predicted_units == 0.0) and product.reorder_level > 0:
            predicted_units = max(predicted_units, product.reorder_level * (horizon_days / 7.0))
        predicted_sales = predicted_units * product.selling_price
        return {
            "predicted_sales": round(predicted_sales, 2),
            "predicted_units": round(predicted_units, 2),
            "model_used": "velocity_fallback",
            "scaling_factor": 1.0,
            "store_predicted_total": 0.0,
            "store_historical_avg": 0.0,
        }

    # Build real feature vector and call the RF model
    feature_vector = build_feature_vector(product, db)

    # RF model predicts total store revenue over horizon_days
    store_predicted_total = get_multi_day_forecast(feature_vector, days=horizon_days)

    # Historical baseline: store avg daily revenue × horizon
    store_avg_daily = _compute_store_avg_daily_revenue(db, 30)
    store_historical_total = store_avg_daily * horizon_days

    # Scaling factor: how much more/less the model expects vs history
    if store_historical_total > 0:
        scaling_factor = store_predicted_total / store_historical_total
    else:
        # No historical data yet; use RF prediction directly
        scaling_factor = 1.0

    # Clamp scaling factor to reasonable range to avoid extreme predictions
    scaling_factor = max(0.1, min(scaling_factor, 5.0))

    # Product's own average daily sales (in units)
    product_avg_daily_units = _compute_product_avg_daily_units(product.id, db, 30)

    # Scale product forecast by the model's uplift/decline factor
    predicted_units = product_avg_daily_units * horizon_days * scaling_factor

    # If current_stock is below reorder_level or no sales yet, use reorder_level as baseline
    if (product.current_stock < product.reorder_level or predicted_units == 0.0) and product.reorder_level > 0:
        predicted_units = max(predicted_units, product.reorder_level * (horizon_days / 7.0))

    predicted_sales = predicted_units * product.selling_price

    return {
        "predicted_sales": round(predicted_sales, 2),
        "predicted_units": round(predicted_units, 2),
        "model_used": "random_forest",
        "scaling_factor": round(scaling_factor, 4),
        "store_predicted_total": round(store_predicted_total, 2),
        "store_historical_avg": round(store_avg_daily, 2),
    }


def _compute_product_avg_daily_units(product_id: str, db: Session, days: int) -> float:
    """Average daily sales in UNITS for a product over the last `days`."""
    since = date.today() - timedelta(days=days)
    total_qty = float(
        db.query(func.coalesce(func.sum(Sale.quantity), 0.0))
        .filter(Sale.product_id == product_id, Sale.date >= since)
        .scalar()
    )
    return total_qty / max(days, 1)


def _compute_store_avg_daily_revenue(db: Session, days: int) -> float:
    """Average daily total revenue across ALL products over the last `days`."""
    since = date.today() - timedelta(days=days)
    total = float(
        db.query(func.coalesce(func.sum(Sale.total_amount), 0.0))
        .filter(Sale.date >= since)
        .scalar()
    )
    return total / max(days, 1)
