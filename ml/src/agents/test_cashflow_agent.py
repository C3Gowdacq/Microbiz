"""
test_cashflow_agent.py -- Unit tests for cashflow_agent.calculate_cashflow_risk().

Run with:  python ml/src/agents/test_cashflow_agent.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from cashflow_agent import calculate_cashflow_risk


def test_healthy_cashflow():
    """Revenue exceeds expenses by a wide margin → LOW risk."""
    result = calculate_cashflow_risk(
        current_cash=50000,
        expected_sales_revenue=30000,
        upcoming_expenses=15000,
        planned_purchase_cost=5000,
        min_cash_reserve=10000,
    )
    # net = 30000 - 15000 - 5000 = 10000
    assert result["net_cash_flow"] == 10000.0
    # projected = 50000 + 10000 = 60000
    assert result["projected_cash_balance"] == 60000.0
    # 60000 >> 10000 * 1.5 = 15000 → LOW
    assert result["cash_shortage_risk"] == "LOW"
    assert result["liquidity_ok"] is True
    print("  [PASS] test_healthy_cashflow")


def test_tight_cashflow_medium():
    """Projected balance between min_reserve and 1.5x min_reserve → MEDIUM."""
    result = calculate_cashflow_risk(
        current_cash=20000,
        expected_sales_revenue=10000,
        upcoming_expenses=12000,
        planned_purchase_cost=6000,
        min_cash_reserve=10000,
    )
    # net = 10000 - 12000 - 6000 = -8000
    assert result["net_cash_flow"] == -8000.0
    # projected = 20000 + (-8000) = 12000
    assert result["projected_cash_balance"] == 12000.0
    # 10000 <= 12000 < 15000 → MEDIUM
    assert result["cash_shortage_risk"] == "MEDIUM"
    assert result["liquidity_ok"] is True
    print("  [PASS] test_tight_cashflow_medium")


def test_cash_shortage_high():
    """Projected balance below min_cash_reserve → HIGH risk."""
    result = calculate_cashflow_risk(
        current_cash=5000,
        expected_sales_revenue=3000,
        upcoming_expenses=8000,
        planned_purchase_cost=2000,
        min_cash_reserve=5000,
    )
    # net = 3000 - 8000 - 2000 = -7000
    assert result["net_cash_flow"] == -7000.0
    # projected = 5000 + (-7000) = -2000
    assert result["projected_cash_balance"] == -2000.0
    assert result["cash_shortage_risk"] == "HIGH"
    assert result["liquidity_ok"] is False
    print("  [PASS] test_cash_shortage_high")


def test_zero_revenue():
    """No expected revenue (e.g. seasonal shutdown) → all outflow."""
    result = calculate_cashflow_risk(
        current_cash=15000,
        expected_sales_revenue=0,
        upcoming_expenses=5000,
        planned_purchase_cost=0,
        min_cash_reserve=8000,
    )
    # net = 0 - 5000 - 0 = -5000, projected = 15000 - 5000 = 10000
    assert result["net_cash_flow"] == -5000.0
    assert result["projected_cash_balance"] == 10000.0
    # 10000 >= 8000 * 1.5 = 12000? No. 10000 >= 8000? Yes → MEDIUM
    assert result["cash_shortage_risk"] == "MEDIUM"
    assert result["liquidity_ok"] is True
    print("  [PASS] test_zero_revenue")


def test_exact_reserve_boundary():
    """Projected balance exactly equals min_cash_reserve → MEDIUM (< 1.5x)."""
    result = calculate_cashflow_risk(
        current_cash=10000,
        expected_sales_revenue=5000,
        upcoming_expenses=5000,
        planned_purchase_cost=0,
        min_cash_reserve=10000,
    )
    # net = 0, projected = 10000, min = 10000, 1.5x = 15000
    # 10000 < 15000 → MEDIUM
    assert result["projected_cash_balance"] == 10000.0
    assert result["cash_shortage_risk"] == "MEDIUM"
    assert result["liquidity_ok"] is True
    print("  [PASS] test_exact_reserve_boundary")


def main():
    print("=" * 60)
    print("CASHFLOW AGENT UNIT TESTS")
    print("=" * 60)

    tests = [
        test_healthy_cashflow,
        test_tight_cashflow_medium,
        test_cash_shortage_high,
        test_zero_revenue,
        test_exact_reserve_boundary,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {t.__name__}: {type(e).__name__}: {e}")
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
