"""
demo_inventory_agent.py -- End-to-end integration demo of the Inventory Agent.

Picks 5 real rows from the Rossmann test split, uses the trained Random Forest
(via sales_agent) to produce 7-day demand forecasts, then feeds those into
calculate_inventory_risk() with documented synthetic inventory assumptions.

SYNTHETIC INVENTORY ASSUMPTIONS (Rossmann has no real inventory data):
  - current_stock  = 1.5x the 7-day forecast demand (simulating a reasonably
                     stocked store that just received a delivery)
  - lead_time_days = 5 (typical retail replenishment lead time)
  - safety_stock   = 20% of forecast_demand
  - reorder_level  = forecast_demand (reorder when stock equals 1 week's demand)

These assumptions are from the project datasets document and are clearly
labeled as synthetic for the proof-of-concept pipeline.

Run with:  python ml/src/agents/demo_inventory_agent.py
"""

import os
import sys
import json
import numpy as np
import pandas as pd

# Ensure imports work
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from columns import FEATURE_COLS
from agents.sales_agent import predict_from_df, get_multi_day_forecast
from agents.inventory_agent import calculate_inventory_risk


def main():
    print("=" * 80)
    print("INVENTORY AGENT — END-TO-END INTEGRATION DEMO")
    print("=" * 80)

    # ── 1. Load real test data ───────────────────────────────────────────
    test_path = os.path.join("ml", "data", "processed", "rossmann_test.parquet")
    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Test data not found at {test_path}")

    test_df = pd.read_parquet(test_path)
    print(f"\nLoaded test split: {len(test_df):,} rows")

    # ── 2. Pick 5 diverse rows (different stores, days, promo states) ────
    # Use deterministic seed for reproducibility
    rng = np.random.RandomState(42)
    sample_indices = rng.choice(len(test_df), size=5, replace=False)
    sample_df = test_df.iloc[sample_indices].reset_index(drop=True)

    print(f"Selected {len(sample_df)} sample rows:")
    print(f"  Stores: {sample_df['Store'].tolist()}")
    print(f"  Dates:  {sample_df['Date'].dt.strftime('%Y-%m-%d').tolist()}")
    print(f"  Actual Sales: {sample_df['Sales'].tolist()}")

    # ── 3. Run sales_agent.predict() for 1-day predictions ───────────────
    print("\n" + "-" * 80)
    print("STEP 1: Single-day RF predictions (for reference)")
    print("-" * 80)

    one_day_preds = predict_from_df(sample_df)
    for i, (_, row) in enumerate(sample_df.iterrows()):
        print(f"  Store {int(row['Store'])}, Date {row['Date'].strftime('%Y-%m-%d')}: "
              f"Actual={int(row['Sales'])}, RF Prediction={one_day_preds[i]:.0f}")

    # ── 4. Run multi-day forecasts (7-day horizon) ───────────────────────
    print("\n" + "-" * 80)
    print("STEP 2: 7-day demand forecasts (multi-day rolling)")
    print("-" * 80)

    forecasts = []
    for i, (_, row) in enumerate(sample_df.iterrows()):
        demand_7d = get_multi_day_forecast(row, days=7)
        forecasts.append(demand_7d)
        print(f"  Store {int(row['Store'])}: 7-day forecast demand = {demand_7d:,.0f}")

    # ── 5. Run inventory risk assessment ─────────────────────────────────
    print("\n" + "-" * 80)
    print("STEP 3: Inventory Risk Assessment")
    print("-" * 80)
    print("\nSynthetic Inventory Assumptions:")
    print("  current_stock   = 1.5x forecast_demand (recently restocked)")
    print("  safety_stock    = 20% of forecast_demand")
    print("  lead_time_days  = 5 days")
    print("  reorder_level   = forecast_demand (1 week's demand)")
    print()

    results = []
    for i, (_, row) in enumerate(sample_df.iterrows()):
        forecast_demand = forecasts[i]

        # Synthetic inventory assumptions
        current_stock = forecast_demand * 1.5
        safety_stock = forecast_demand * 0.20
        lead_time_days = 5
        reorder_level = forecast_demand

        product_id = f"Store_{int(row['Store'])}"

        risk = calculate_inventory_risk(
            product_id=product_id,
            current_stock=current_stock,
            forecast_demand=forecast_demand,
            reorder_level=reorder_level,
            safety_stock=safety_stock,
            lead_time_days=lead_time_days,
            forecast_horizon_days=7,
        )
        results.append(risk)

        print(f"\n  === {product_id} (Date: {row['Date'].strftime('%Y-%m-%d')}) ===")
        print(f"    Forecast Demand (7d):     {risk['forecast_demand']:>10,.2f}")
        print(f"    Current Stock:            {risk['current_stock']:>10,.2f}")
        print(f"    Stock Gap:                {risk['stock_gap']:>10,.2f}")
        cov = risk['stock_coverage_days']
        cov_str = f"{cov:>10,.2f}" if cov is not None else "       inf"
        print(f"    Stock Coverage (days):    {cov_str}")
        print(f"    Stockout Risk:            {risk['stockout_risk']:>10}")
        print(f"    Recommended Order Qty:    {risk['recommended_order_quantity']:>10,.2f}")

    # ── 6. Print full JSON output for audit ──────────────────────────────
    print("\n" + "-" * 80)
    print("FULL JSON OUTPUT (for pipeline integration)")
    print("-" * 80)
    for r in results:
        print(json.dumps(r, indent=2))

    # ── 7. Simulate a HIGH-risk scenario ─────────────────────────────────
    print("\n" + "-" * 80)
    print("BONUS: Simulated HIGH-risk scenario (stock at 30% of demand)")
    print("-" * 80)

    # Take the first store and set stock dangerously low
    first_store = sample_df.iloc[0]
    demand = forecasts[0]
    low_stock = demand * 0.30  # Only 30% of what's needed

    risk_high = calculate_inventory_risk(
        product_id=f"Store_{int(first_store['Store'])}_LOW",
        current_stock=low_stock,
        forecast_demand=demand,
        reorder_level=demand,
        safety_stock=demand * 0.20,
        lead_time_days=5,
        forecast_horizon_days=7,
    )
    print(f"\n  Product: {risk_high['product_id']}")
    print(f"  Forecast Demand: {risk_high['forecast_demand']:,.2f}")
    print(f"  Current Stock:   {risk_high['current_stock']:,.2f} (critically low)")
    print(f"  Stock Gap:       {risk_high['stock_gap']:,.2f}")
    cov = risk_high['stock_coverage_days']
    print(f"  Coverage (days): {cov if cov is not None else 'inf'}")
    print(f"  Stockout Risk:   {risk_high['stockout_risk']}")
    print(f"  Order Needed:    {risk_high['recommended_order_quantity']:,.2f}")

    print("\n" + "=" * 80)
    print("DEMO COMPLETE — Inventory Agent is operational.")
    print("=" * 80)


if __name__ == "__main__":
    main()
