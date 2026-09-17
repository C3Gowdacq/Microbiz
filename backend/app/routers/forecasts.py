"""
backend/app/routers/forecasts.py

Dedicated Sales Forecasting Router for MicroBizAI.
Provides decoupled, on-demand product sales forecasting, forecast history tracking
with real-world accuracy computation, and explicit human decision endpoints.

Endpoints:
  POST /api/products/{id}/forecast    -> Run and persist on-demand forecast
  GET  /api/products/{id}/forecasts   -> List forecast history with accuracy metrics
  POST /api/forecasts/{id}/act        -> Human action on forecast (trigger check, adjust stock, dismiss)
"""

import os
import sys
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Ensure ml/src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "src")))

from backend.app.database import get_db
from backend.app.models import Product, Forecast, Recommendation
from backend.app.schemas import (
    ForecastRequest,
    ForecastResponse,
    ForecastHistoryItem,
    ForecastActRequest,
    ForecastActResponse,
)
from backend.app.services.forecast_accuracy import compute_forecast_accuracy
from backend.app.services.feature_vector_builder import forecast_product_demand
from agents.inventory_agent import calculate_inventory_risk

router = APIRouter(tags=["Sales Forecasting"])


# ── 1. Run Dedicated Forecast ─────────────────────────────────────────────────

@router.post(
    "/api/products/{product_id}/forecast",
    response_model=ForecastResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run and persist a sales forecast for a product"
)
def create_product_forecast(
    product_id: str,
    req: ForecastRequest,
    db: Session = Depends(get_db),
):
    """
    Run a dedicated sales forecast for a product over `horizon_days` (default: 7).

    If the product has ML profile fields (store_type, assortment), the real trained
    Random Forest model is used with the proportional scaling factor approach.
    Otherwise, falls back to simple velocity average.

    Saves a persistent Forecast record with status='active'.
    Returns the predicted sales number, model used, and stock gap preview.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found",
        )

    # Use the feature_vector_builder to get ML-powered or fallback forecast
    try:
        forecast_result = forecast_product_demand(product, db, req.horizon_days)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    predicted_sales = forecast_result["predicted_units"]
    model_used = forecast_result["model_used"]
    scaling_factor = forecast_result["scaling_factor"]

    stock_gap = max(0.0, round(predicted_sales - product.current_stock, 2))

    # Calculate preview risk
    avg_daily_demand = predicted_sales / req.horizon_days if req.horizon_days > 0 else 0.0
    if avg_daily_demand > 0:
        coverage_days = product.current_stock / avg_daily_demand
    else:
        coverage_days = float("inf")

    if avg_daily_demand == 0:
        risk_preview = "N/A"
    elif coverage_days < product.lead_time_days:
        risk_preview = "HIGH"
    elif coverage_days < product.lead_time_days * 1.5:
        risk_preview = "MEDIUM"
    else:
        risk_preview = "LOW"

    # Persist the forecast record
    forecast_row = Forecast(
        product_id=product.id,
        forecast_date=date.today(),
        horizon_days=req.horizon_days,
        predicted_sales=predicted_sales,
        model_used=model_used,
        status="active",
        created_at=datetime.utcnow(),
    )
    db.add(forecast_row)
    db.commit()
    db.refresh(forecast_row)

    return ForecastResponse(
        id=forecast_row.id,
        product_id=product.id,
        product_name=product.name,
        product_sku=product.sku,
        forecast_date=forecast_row.forecast_date,
        horizon_days=forecast_row.horizon_days,
        predicted_sales=forecast_row.predicted_sales,
        model_used=forecast_row.model_used,
        status=forecast_row.status,
        created_at=forecast_row.created_at,
        current_stock=product.current_stock,
        stock_gap_preview=stock_gap,
        stockout_risk_preview=risk_preview,
    )


# ── 2. Get Forecast History for a Product ─────────────────────────────────────

@router.get(
    "/api/products/{product_id}/forecasts",
    response_model=List[ForecastHistoryItem],
    summary="List past forecasts and accuracy metrics for a product"
)
def get_product_forecast_history(
    product_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve all historical forecasts for a product, ordered by creation date descending.
    Each item includes real-world accuracy metrics comparing predicted vs actual sales.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found",
        )

    forecast_rows = (
        db.query(Forecast)
        .filter(Forecast.product_id == product_id)
        .order_by(Forecast.created_at.desc())
        .all()
    )

    history_items: List[ForecastHistoryItem] = []
    for f in forecast_rows:
        acc = compute_forecast_accuracy(f.id, db)
        history_items.append(
            ForecastHistoryItem(
                id=f.id,
                product_id=f.product_id,
                forecast_date=f.forecast_date,
                horizon_days=f.horizon_days,
                predicted_sales=f.predicted_sales,
                model_used=f.model_used,
                status=f.status,
                created_at=f.created_at,
                actual_sales=acc.get("actual") if acc else None,
                error=acc.get("error") if acc else None,
                error_pct=acc.get("error_pct") if acc else None,
                is_completed=acc.get("is_completed", False) if acc else False,
                accuracy_note=acc.get("accuracy_note") if acc else None,
            )
        )

    return history_items


# ── 3. Act on Forecast ────────────────────────────────────────────────────────

@router.post(
    "/api/forecasts/{forecast_id}/act",
    response_model=ForecastActResponse,
    summary="Act on a forecast (trigger inventory check, adjust stock, or dismiss)"
)
def act_on_forecast(
    forecast_id: int,
    req: ForecastActRequest,
    db: Session = Depends(get_db),
):
    """
    Allow the shopkeeper to explicitly decide what to do with a forecast:
      - 'trigger_inventory_check': Run inventory risk check using this forecast's
        predicted_sales, create a Recommendation if needed, set status='acted_on'.
      - 'adjust_stock': Update product current_stock to stock_adjustment, set status='acted_on'.
      - 'dismiss': Dismiss the forecast with status='dismissed'.
    """
    forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast with id '{forecast_id}' not found",
        )

    product = db.query(Product).filter(Product.id == forecast.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{forecast.product_id}' not found",
        )

    action = req.action.lower().strip()

    if action == "trigger_inventory_check":
        # Run inventory agent using the forecast's predicted_sales
        inv_result = calculate_inventory_risk(
            product_id=product.id,
            current_stock=product.current_stock,
            forecast_demand=forecast.predicted_sales,
            reorder_level=product.reorder_level,
            safety_stock=product.safety_stock,
            lead_time_days=product.lead_time_days,
            forecast_horizon_days=forecast.horizon_days,
        )

        risk = inv_result.get("stockout_risk", "LOW")
        rec_id = None
        if risk in ("HIGH", "MEDIUM"):
            rec = Recommendation(
                primary_action="full_replenishment" if risk == "HIGH" else "partial_replenishment",
                priority=risk.lower(),
                reason=(
                    f"Forecast #{forecast.id} ({forecast.horizon_days}d demand: {forecast.predicted_sales:.1f}) "
                    f"triggered inventory check for '{product.name}' (SKU: {product.sku}). "
                    f"Current stock is {product.current_stock:.1f}, stock gap is {inv_result.get('stock_gap', 0):.1f} units."
                ),
                secondary_recommendations=[],
                status="pending",
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
            rec_id = rec.id

        forecast.status = "acted_on"
        db.commit()
        db.refresh(forecast)

        msg = (
            f"Inventory check completed with {risk} risk. "
            + (f"Recommendation #{rec_id} created in Approvals Inbox." if rec_id else "Stock levels are currently sufficient.")
        )

        return ForecastActResponse(
            forecast_id=forecast.id,
            action=action,
            status=forecast.status,
            recommendation_id=rec_id,
            recommendation=inv_result,
            current_stock=product.current_stock,
            message=msg,
        )

    elif action == "adjust_stock":
        if req.stock_adjustment is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Field 'stock_adjustment' (numeric) is required when action is 'adjust_stock'",
            )
        if req.stock_adjustment < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Stock adjustment cannot be negative",
            )

        product.current_stock = float(req.stock_adjustment)
        forecast.status = "acted_on"
        db.commit()
        db.refresh(product)
        db.refresh(forecast)

        return ForecastActResponse(
            forecast_id=forecast.id,
            action=action,
            status=forecast.status,
            current_stock=product.current_stock,
            message=f"Stock for '{product.name}' updated to {product.current_stock:.1f} units.",
        )

    elif action == "dismiss":
        forecast.status = "dismissed"
        db.commit()
        db.refresh(forecast)

        return ForecastActResponse(
            forecast_id=forecast.id,
            action=action,
            status=forecast.status,
            current_stock=product.current_stock,
            message=f"Forecast #{forecast.id} has been dismissed.",
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action '{action}'. Allowed: 'trigger_inventory_check', 'adjust_stock', 'dismiss'",
        )
