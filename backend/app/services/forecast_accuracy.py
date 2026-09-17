"""
backend/app/services/forecast_accuracy.py

Service to evaluate real-world forecasting accuracy for stored forecasts.
Once the forecast horizon period has passed (or in-progress), sums actual sales
for that product in that date range and computes deviation metrics.
"""

from datetime import date, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models import Forecast, Sale


def compute_forecast_accuracy(forecast_id: int, db: Session) -> Optional[Dict[str, Any]]:
    """
    Compute real-world forecast accuracy by comparing predicted_sales against
    actual recorded sales in the sales table for the forecast's product and horizon window.

    Window: [forecast.forecast_date, forecast.forecast_date + horizon_days]

    Args:
        forecast_id: Primary key of the Forecast row
        db: SQLAlchemy DB Session

    Returns:
        Dict with keys:
            forecast_id, product_id, forecast_date, horizon_days,
            predicted, actual, error, error_pct, is_completed, days_elapsed,
            accuracy_note
        Returns None if forecast_id is not found.
    """
    forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
    if not forecast:
        return None

    forecast_start = forecast.forecast_date
    horizon_days = forecast.horizon_days
    forecast_end = forecast_start + timedelta(days=horizon_days)

    today = date.today()
    days_elapsed = max(0, (today - forecast_start).days)
    is_completed = today >= forecast_end

    # Query actual sales recorded within the forecast window
    # If horizon has passed, query [start, end]. If still in-progress, query [start, today].
    actual_query_end = forecast_end if is_completed else today
    actual_sales_sum = db.query(func.coalesce(func.sum(Sale.quantity), 0.0)) \
        .filter(
            Sale.product_id == forecast.product_id,
            Sale.date >= forecast_start,
            Sale.date <= actual_query_end,
        ).scalar()

    actual = float(actual_sales_sum)
    predicted = float(forecast.predicted_sales)
    error = round(actual - predicted, 2)  # positive = underpredicted, negative = overpredicted

    # Compute percentage error relative to actual sales (or fallback if actual is 0)
    if actual > 0:
        error_pct = round((abs(actual - predicted) / actual) * 100.0, 2)
    elif predicted > 0:
        error_pct = 100.0
    else:
        error_pct = 0.0

    if is_completed:
        accuracy_note = f"Completed: Predicted {predicted:.1f}, Actual {actual:.1f} (Error: {abs(error):.1f} units, {error_pct:.1f}%)"
    else:
        days_left = max(0, (forecast_end - today).days)
        accuracy_note = f"In Progress ({days_left}d remaining): Current actual {actual:.1f} vs predicted {predicted:.1f}"

    return {
        "forecast_id": forecast.id,
        "product_id": forecast.product_id,
        "forecast_date": forecast.forecast_date,
        "horizon_days": forecast.horizon_days,
        "predicted": round(predicted, 2),
        "actual": round(actual, 2),
        "error": error,
        "error_pct": error_pct,
        "is_completed": is_completed,
        "days_elapsed": days_elapsed,
        "accuracy_note": accuracy_note,
    }
