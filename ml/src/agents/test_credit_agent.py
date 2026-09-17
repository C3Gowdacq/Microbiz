"""
test_credit_agent.py -- Unit tests for credit_agent functions.

Run with:  python ml/src/agents/test_credit_agent.py
"""

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from credit_agent import analyze_customer_credit, compute_payment_reliability


def test_overdue_high_risk():
    """Invoice 45 days overdue → HIGH risk, payment_reminder."""
    result = analyze_customer_credit(
        customer_id="CUST_001",
        invoice_amount=5000,
        amount_paid=2000,
        due_date=date(2025, 6, 1),
        today=date(2025, 7, 16),  # 45 days overdue
    )
    assert result["outstanding_amount"] == 3000.0
    assert result["days_overdue"] == 45
    assert result["customer_risk"] == "HIGH"
    assert result["recommended_action"] == "payment_reminder"
    print("  [PASS] test_overdue_high_risk")


def test_overdue_medium_risk():
    """Invoice 15 days overdue → MEDIUM risk."""
    result = analyze_customer_credit(
        customer_id="CUST_002",
        invoice_amount=3000,
        amount_paid=1000,
        due_date=date(2025, 7, 1),
        today=date(2025, 7, 16),  # 15 days overdue
    )
    assert result["outstanding_amount"] == 2000.0
    assert result["days_overdue"] == 15
    assert result["customer_risk"] == "MEDIUM"
    assert result["recommended_action"] == "payment_reminder"
    print("  [PASS] test_overdue_medium_risk")


def test_overdue_low_risk():
    """Invoice 3 days overdue → LOW risk."""
    result = analyze_customer_credit(
        customer_id="CUST_003",
        invoice_amount=1000,
        amount_paid=500,
        due_date=date(2025, 7, 13),
        today=date(2025, 7, 16),  # 3 days overdue
    )
    assert result["outstanding_amount"] == 500.0
    assert result["days_overdue"] == 3
    assert result["customer_risk"] == "LOW"
    assert result["recommended_action"] == "payment_reminder"
    print("  [PASS] test_overdue_low_risk")


def test_fully_paid():
    """Fully paid invoice → NONE risk, monitor."""
    result = analyze_customer_credit(
        customer_id="CUST_004",
        invoice_amount=2000,
        amount_paid=2000,
        due_date=date(2025, 7, 1),
        today=date(2025, 7, 16),
    )
    assert result["outstanding_amount"] == 0.0
    assert result["days_overdue"] == 0
    assert result["customer_risk"] == "NONE"
    assert result["recommended_action"] == "monitor"
    print("  [PASS] test_fully_paid")


def test_not_yet_due():
    """Invoice not yet due (today < due_date) → LOW risk, monitor."""
    result = analyze_customer_credit(
        customer_id="CUST_005",
        invoice_amount=4000,
        amount_paid=0,
        due_date=date(2025, 7, 20),
        today=date(2025, 7, 16),  # 4 days before due
    )
    assert result["outstanding_amount"] == 4000.0
    assert result["days_overdue"] == 0
    assert result["customer_risk"] == "LOW"
    assert result["recommended_action"] == "monitor"
    print("  [PASS] test_not_yet_due")


def test_exactly_on_due_date():
    """Invoice exactly on due date → 0 days overdue, monitor."""
    result = analyze_customer_credit(
        customer_id="CUST_006",
        invoice_amount=1500,
        amount_paid=0,
        due_date=date(2025, 7, 16),
        today=date(2025, 7, 16),
    )
    assert result["outstanding_amount"] == 1500.0
    assert result["days_overdue"] == 0
    assert result["customer_risk"] == "LOW"
    assert result["recommended_action"] == "monitor"
    print("  [PASS] test_exactly_on_due_date")


def test_payment_reliability_normal():
    """Payment reliability with mixed early/late payments."""
    history = [
        {"due_date": date(2025, 1, 15), "payment_date": date(2025, 1, 20)},  # 5 days late
        {"due_date": date(2025, 2, 15), "payment_date": date(2025, 2, 10)},  # 5 days early → clipped to 0
        {"due_date": date(2025, 3, 15), "payment_date": date(2025, 3, 25)},  # 10 days late
    ]
    result = compute_payment_reliability("CUST_R1", history)
    # delays: [5, 0, 10] → avg = 5.0
    assert result["average_payment_delay_days"] == 5.0
    assert result["num_invoices_analyzed"] == 3
    print("  [PASS] test_payment_reliability_normal")


def test_payment_reliability_empty():
    """No history → 0 delay, 0 invoices."""
    result = compute_payment_reliability("CUST_R2", [])
    assert result["average_payment_delay_days"] == 0.0
    assert result["num_invoices_analyzed"] == 0
    print("  [PASS] test_payment_reliability_empty")


def main():
    print("=" * 60)
    print("CREDIT AGENT UNIT TESTS")
    print("=" * 60)

    tests = [
        test_overdue_high_risk,
        test_overdue_medium_risk,
        test_overdue_low_risk,
        test_fully_paid,
        test_not_yet_due,
        test_exactly_on_due_date,
        test_payment_reliability_normal,
        test_payment_reliability_empty,
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
