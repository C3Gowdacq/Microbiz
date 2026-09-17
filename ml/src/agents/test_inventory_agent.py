"""
test_inventory_agent.py -- Unit tests for inventory_agent.calculate_inventory_risk().

Tests cover:
  1. Normal case with known inputs and expected outputs
  2. Zero stock edge case (current_stock=0)
  3. Overstocked edge case (current_stock >> forecast_demand)
  4. Zero forecast_demand edge case (discontinued product, no div-by-zero crash)

Run with:  python ml/src/agents/test_inventory_agent.py
   or:     pytest ml/src/agents/test_inventory_agent.py -v
"""

import os
import sys
import math

# Ensure the agents package is importable
sys.path.insert(0, os.path.dirname(__file__))

from inventory_agent import calculate_inventory_risk


# ── Helpers ──────────────────────────────────────────────────────────────────

def assert_close(actual, expected, tol=0.01, msg=""):
    """Assert two floats are within tolerance."""
    assert abs(actual - expected) < tol, (
        f"{msg}: expected {expected}, got {actual} (tol={tol})"
    )


# ── Test 1: Normal Case ─────────────────────────────────────────────────────

def test_normal_case():
    """
    forecast_demand=125, current_stock=80, safety_stock=20,
    lead_time_days=5, reorder_level=100, horizon=7
    """
    result = calculate_inventory_risk(
        product_id="STORE_123",
        current_stock=80,
        forecast_demand=125,
        reorder_level=100,
        safety_stock=20,
        lead_time_days=5,
        forecast_horizon_days=7,
    )

    # stock_gap = max(0, 125 - 80) = 45
    assert result["stock_gap"] == 45.0, f"Expected stock_gap=45, got {result['stock_gap']}"

    # avg_daily_demand = 125 / 7 ≈ 17.857
    avg_daily = 125.0 / 7.0

    # stock_coverage_days = 80 / 17.857 ≈ 4.48
    expected_coverage = 80.0 / avg_daily
    assert_close(result["stock_coverage_days"], expected_coverage, tol=0.1,
                 msg="stock_coverage_days")

    # coverage (4.48) < lead_time (5) → HIGH
    assert result["stockout_risk"] == "HIGH", (
        f"Expected HIGH risk, got {result['stockout_risk']} "
        f"(coverage={result['stock_coverage_days']}, lead_time=5)"
    )

    # recommended_order_quantity = max(0, 125 + 20 - 80) = 65
    assert result["recommended_order_quantity"] == 65.0, (
        f"Expected recommended_order=65, got {result['recommended_order_quantity']}"
    )

    # Echo fields
    assert result["product_id"] == "STORE_123"
    assert result["current_stock"] == 80.0
    assert result["forecast_demand"] == 125.0

    print("  [PASS] test_normal_case")


# ── Test 2: Zero Stock ───────────────────────────────────────────────────────

def test_zero_stock():
    """
    current_stock=0: maximum vulnerability.
    stock_gap = forecast_demand, coverage = 0 days, risk = HIGH.
    """
    result = calculate_inventory_risk(
        product_id="STORE_EMPTY",
        current_stock=0,
        forecast_demand=200,
        reorder_level=50,
        safety_stock=30,
        lead_time_days=3,
        forecast_horizon_days=7,
    )

    assert result["stock_gap"] == 200.0, f"stock_gap should be 200, got {result['stock_gap']}"
    assert result["stock_coverage_days"] == 0.0, (
        f"coverage should be 0 when stock=0, got {result['stock_coverage_days']}"
    )
    assert result["stockout_risk"] == "HIGH", (
        f"Expected HIGH with zero stock, got {result['stockout_risk']}"
    )
    # recommended = max(0, 200 + 30 - 0) = 230
    assert result["recommended_order_quantity"] == 230.0

    print("  [PASS] test_zero_stock")


# ── Test 3: Overstocked ─────────────────────────────────────────────────────

def test_overstocked():
    """
    current_stock=5000, forecast_demand=100: massively overstocked.
    stock_gap=0, risk=LOW, no reorder needed.
    """
    result = calculate_inventory_risk(
        product_id="STORE_SURPLUS",
        current_stock=5000,
        forecast_demand=100,
        reorder_level=50,
        safety_stock=20,
        lead_time_days=5,
        forecast_horizon_days=7,
    )

    assert result["stock_gap"] == 0.0, f"stock_gap should be 0, got {result['stock_gap']}"

    # avg_daily = 100/7 ≈ 14.29, coverage = 5000/14.29 ≈ 350 days
    assert result["stock_coverage_days"] > 100, (
        f"coverage should be very high, got {result['stock_coverage_days']}"
    )
    assert result["stockout_risk"] == "LOW", (
        f"Expected LOW with massive surplus, got {result['stockout_risk']}"
    )

    # recommended = max(0, 100 + 20 - 5000) = 0 (negative clamped)
    assert result["recommended_order_quantity"] == 0.0, (
        f"No reorder needed, got {result['recommended_order_quantity']}"
    )

    print("  [PASS] test_overstocked")


# ── Test 4: Zero Forecast Demand (Discontinued) ─────────────────────────────

def test_zero_demand():
    """
    forecast_demand=0: e.g. a discontinued product.
    Should NOT crash on division by zero.
    stock_gap=0, coverage=None (inf), risk=N/A.
    """
    result = calculate_inventory_risk(
        product_id="STORE_DISCONTINUED",
        current_stock=50,
        forecast_demand=0,
        reorder_level=10,
        safety_stock=5,
        lead_time_days=3,
        forecast_horizon_days=7,
    )

    assert result["stock_gap"] == 0.0, f"stock_gap should be 0, got {result['stock_gap']}"

    # With zero demand, coverage is effectively infinite → None in JSON output
    assert result["stock_coverage_days"] is None, (
        f"coverage should be None (inf), got {result['stock_coverage_days']}"
    )
    assert result["stockout_risk"] == "N/A", (
        f"Expected 'N/A' for zero demand, got {result['stockout_risk']}"
    )

    # recommended = max(0, 0 + 5 - 50) = 0
    assert result["recommended_order_quantity"] == 0.0

    print("  [PASS] test_zero_demand")


# ── Test 5: MEDIUM Risk Boundary ─────────────────────────────────────────────

def test_medium_risk():
    """
    Coverage between lead_time and lead_time * 1.5 → MEDIUM risk.
    lead_time_days=4, coverage ~5.6 days (between 4 and 6).
    """
    # avg_daily = 100/7 ≈ 14.286, coverage = 80/14.286 ≈ 5.6
    # lead_time=4, 1.5*lead_time=6  →  4 <= 5.6 < 6  →  MEDIUM
    result = calculate_inventory_risk(
        product_id="STORE_MEDIUM",
        current_stock=80,
        forecast_demand=100,
        reorder_level=50,
        safety_stock=10,
        lead_time_days=4,
        forecast_horizon_days=7,
    )

    assert result["stockout_risk"] == "MEDIUM", (
        f"Expected MEDIUM risk, got {result['stockout_risk']} "
        f"(coverage={result['stock_coverage_days']}, lead_time=4)"
    )

    print("  [PASS] test_medium_risk")


# ── Runner ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("INVENTORY AGENT UNIT TESTS")
    print("=" * 60)

    tests = [
        test_normal_case,
        test_zero_stock,
        test_overstocked,
        test_zero_demand,
        test_medium_risk,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {test_fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {test_fn.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print("-" * 60)
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    if failed > 0:
        sys.exit(1)
    else:
        print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
