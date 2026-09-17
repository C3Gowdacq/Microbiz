"""
test_profitability_agent.py -- Unit tests for profitability_agent functions.

Run with:  python ml/src/agents/test_profitability_agent.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from profitability_agent import calculate_profitability, summarize_business_profitability


def test_highly_profitable():
    """Selling at 50% margin → highly_profitable."""
    result = calculate_profitability("PROD_A", selling_price=100, cost_price=50, quantity_sold=200)
    assert result["unit_profit"] == 50.0
    assert result["gross_profit"] == 10000.0
    assert result["profit_margin"] == 50.0
    assert result["classification"] == "highly_profitable"
    print("  [PASS] test_highly_profitable")


def test_healthy_margin():
    """Selling at 20% margin → healthy_margin."""
    result = calculate_profitability("PROD_B", selling_price=100, cost_price=80, quantity_sold=50)
    assert result["unit_profit"] == 20.0
    assert result["profit_margin"] == 20.0
    assert result["classification"] == "healthy_margin"
    print("  [PASS] test_healthy_margin")


def test_low_margin():
    """Selling at 5% margin → low_margin."""
    result = calculate_profitability("PROD_C", selling_price=100, cost_price=95, quantity_sold=100)
    assert result["unit_profit"] == 5.0
    assert result["profit_margin"] == 5.0
    assert result["classification"] == "low_margin"
    print("  [PASS] test_low_margin")


def test_loss_making():
    """Cost exceeds selling price → loss_making, negative profit."""
    result = calculate_profitability("PROD_D", selling_price=80, cost_price=120, quantity_sold=30)
    assert result["unit_profit"] == -40.0
    assert result["gross_profit"] == -1200.0
    assert result["classification"] == "loss_making"
    print("  [PASS] test_loss_making")


def test_zero_selling_price():
    """Zero selling price (e.g. giveaway) → no crash, margin=0."""
    result = calculate_profitability("PROD_FREE", selling_price=0, cost_price=10, quantity_sold=50)
    assert result["profit_margin"] == 0.0
    assert result["unit_profit"] == -10.0
    assert result["classification"] == "loss_making"
    print("  [PASS] test_zero_selling_price")


def test_zero_quantity():
    """No units sold → gross_profit = 0."""
    result = calculate_profitability("PROD_UNSOLD", selling_price=100, cost_price=60, quantity_sold=0)
    assert result["gross_profit"] == 0.0
    assert result["profit_margin"] == 40.0
    assert result["classification"] == "highly_profitable"
    print("  [PASS] test_zero_quantity")


def test_summarize_business():
    """Business summary aggregates multiple products correctly."""
    products = [
        calculate_profitability("P1", 100, 50, 200),   # highly_profitable, margin=50, gp=10000
        calculate_profitability("P2", 100, 80, 50),    # healthy_margin, margin=20, gp=1000
        calculate_profitability("P3", 80, 120, 30),    # loss_making, margin=-50, gp=-1200
    ]
    summary = summarize_business_profitability(products)

    assert summary["num_products"] == 3
    assert summary["total_gross_profit"] == 10000.0 + 1000.0 + (-1200.0)  # 9800
    assert abs(summary["average_profit_margin"] - (50.0 + 20.0 + (-50.0)) / 3) < 0.1
    assert summary["classification_counts"]["highly_profitable"] == 1
    assert summary["classification_counts"]["healthy_margin"] == 1
    assert summary["classification_counts"]["loss_making"] == 1
    print("  [PASS] test_summarize_business")


def test_summarize_empty():
    """Empty product list → zero aggregates."""
    summary = summarize_business_profitability([])
    assert summary["num_products"] == 0
    assert summary["total_gross_profit"] == 0.0
    assert summary["classification_counts"] == {}
    print("  [PASS] test_summarize_empty")


def main():
    print("=" * 60)
    print("PROFITABILITY AGENT UNIT TESTS")
    print("=" * 60)

    tests = [
        test_highly_profitable,
        test_healthy_margin,
        test_low_margin,
        test_loss_making,
        test_zero_selling_price,
        test_zero_quantity,
        test_summarize_business,
        test_summarize_empty,
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
