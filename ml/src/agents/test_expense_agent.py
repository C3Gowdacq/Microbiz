"""
test_expense_agent.py -- Unit tests for expense_agent.analyze_expense_trend().

Run with:  python ml/src/agents/test_expense_agent.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from expense_agent import analyze_expense_trend


def test_normal_increase():
    """Moderate 20% increase → MEDIUM risk, increasing trend."""
    result = analyze_expense_trend("Rent", 12000, 10000)
    assert result["increase_pct"] == 20.0
    assert result["trend"] == "increasing"
    assert result["risk"] == "MEDIUM"
    print("  [PASS] test_normal_increase")


def test_high_increase():
    """Severe 50% increase → HIGH risk."""
    result = analyze_expense_trend("Marketing", 15000, 10000)
    assert result["increase_pct"] == 50.0
    assert result["trend"] == "increasing"
    assert result["risk"] == "HIGH"
    print("  [PASS] test_high_increase")


def test_decrease():
    """Expense decreased → LOW risk, decreasing trend."""
    result = analyze_expense_trend("Utilities", 800, 1000)
    assert result["increase_pct"] == -20.0
    assert result["trend"] == "decreasing"
    assert result["risk"] == "LOW"
    print("  [PASS] test_decrease")


def test_stable():
    """No change → stable trend, LOW risk."""
    result = analyze_expense_trend("Insurance", 5000, 5000)
    assert result["increase_pct"] == 0.0
    assert result["trend"] == "stable"
    assert result["risk"] == "LOW"
    print("  [PASS] test_stable")


def test_zero_prior_period():
    """Prior period amount is 0 (new category) → no crash, new_category trend."""
    result = analyze_expense_trend("New Software", 3000, 0)
    assert result["trend"] == "new_category"
    assert result["risk"] == "LOW"
    assert result["increase_pct"] is None
    print("  [PASS] test_zero_prior_period")


def test_small_increase_low_risk():
    """5% increase → LOW risk (below 10% threshold)."""
    result = analyze_expense_trend("Office Supplies", 1050, 1000)
    assert result["increase_pct"] == 5.0
    assert result["trend"] == "increasing"
    assert result["risk"] == "LOW"
    print("  [PASS] test_small_increase_low_risk")


def main():
    print("=" * 60)
    print("EXPENSE AGENT UNIT TESTS")
    print("=" * 60)

    tests = [
        test_normal_increase,
        test_high_increase,
        test_decrease,
        test_stable,
        test_zero_prior_period,
        test_small_increase_low_risk,
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
