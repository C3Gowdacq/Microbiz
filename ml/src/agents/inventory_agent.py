"""
inventory_agent.py -- Standalone Inventory Risk Assessment Agent.

Takes structured inputs (product_id, current_stock, forecast_demand,
reorder_level, safety_stock, lead_time_days) and returns a structured
inventory risk assessment dict.

This module is a pure-function module with no database or API dependencies.
It is designed to be wired into the full agent pipeline later.

Public API:
  - calculate_inventory_risk(...) -> dict
"""

import math


def calculate_inventory_risk(
    product_id,
    current_stock,
    forecast_demand,
    reorder_level,
    safety_stock,
    lead_time_days,
    forecast_horizon_days=7,
):
    """
    Calculate inventory risk metrics for a single product/store.

    Args:
        product_id:           Identifier for the product or store (str or int).
        current_stock:        Current units on hand (float or int >= 0).
        forecast_demand:      Total predicted demand over forecast_horizon_days
                              (float, output of get_multi_day_forecast or similar).
        reorder_level:        Stock threshold that triggers a reorder alert (float).
        safety_stock:         Buffer stock to maintain above forecast demand (float).
        lead_time_days:       Days until a new order can arrive (int or float > 0).
        forecast_horizon_days: Number of days the forecast_demand covers (default 7).

    Returns:
        dict with the following keys:
            product_id               -- echo back the input identifier
            current_stock            -- echo back
            forecast_demand          -- echo back (rounded to 2 dp)
            stock_gap                -- max(0, forecast_demand - current_stock)
            stock_coverage_days      -- current_stock / avg_daily_demand
            stockout_risk            -- "HIGH" | "MEDIUM" | "LOW" | "N/A"
            recommended_order_quantity -- max(0, forecast_demand + safety_stock - current_stock)
    """
    # ── Core calculations ────────────────────────────────────────────────

    # 1. Stock gap: shortfall if demand exceeds current inventory
    stock_gap = max(0.0, forecast_demand - current_stock)

    # 2. Average daily demand (guard division by zero for discontinued products)
    if forecast_demand > 0 and forecast_horizon_days > 0:
        avg_daily_demand = forecast_demand / forecast_horizon_days
    else:
        avg_daily_demand = 0.0

    # 3. Stock coverage: how many days current stock can sustain demand
    if avg_daily_demand > 0:
        stock_coverage_days = current_stock / avg_daily_demand
    else:
        # No demand expected: infinite coverage conceptually
        stock_coverage_days = float("inf")

    # 4. Recommended order quantity
    recommended_order_quantity = max(0.0, forecast_demand + safety_stock - current_stock)

    # 5. Stockout risk classification
    if avg_daily_demand == 0:
        # No demand expected — no stockout risk (or product discontinued)
        stockout_risk = "N/A"
    elif stock_coverage_days < lead_time_days:
        stockout_risk = "HIGH"
    elif stock_coverage_days < lead_time_days * 1.5:
        stockout_risk = "MEDIUM"
    else:
        stockout_risk = "LOW"

    # ── Build output contract ────────────────────────────────────────────

    return {
        "product_id": product_id,
        "current_stock": round(float(current_stock), 2),
        "forecast_demand": round(float(forecast_demand), 2),
        "stock_gap": round(float(stock_gap), 2),
        "stock_coverage_days": (
            round(float(stock_coverage_days), 2)
            if math.isfinite(stock_coverage_days)
            else None  # JSON-serializable replacement for inf
        ),
        "stockout_risk": stockout_risk,
        "recommended_order_quantity": round(float(recommended_order_quantity), 2),
    }
