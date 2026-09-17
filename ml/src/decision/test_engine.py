"""
test_engine.py -- Unit tests for the Decision Engine (make_decision).

Tests cover all 8 required scenarios matching Section 12 of MicroBizAI_Architecture.md:
  1. High demand, low inventory, low cash, high receivables (Rule 1)
  2. High demand, low inventory, healthy cash (Rule 2 - HIGH priority)
  3. Healthy stock, cash, receivables, expenses, profitability (Rule 6)
  4. Everything healthy EXCEPT one HIGH expense category (Rule 4 secondary)
  5. Everything healthy EXCEPT one loss-making product (Rule 5 secondary)
  6. Everything healthy EXCEPT overdue customer > 7 days (Rule 3 secondary)
  7. Medium stock shortage, healthy cash (Rule 2 - MEDIUM priority)
  8. Multiple secondary issues triggering simultaneously (Rules 3, 4, 5)

Run with:  python ml/src/decision/test_engine.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from decision.engine import make_decision


# ── Scenario Data Helpers ───────────────────────────────────────────────────

def healthy_cashflow():
    return {
        "current_cash": 25000.0,
        "expected_sales_revenue": 10000.0,
        "upcoming_expenses": 5000.0,
        "planned_purchase_cost": 3000.0,
        "net_cash_flow": 2000.0,
        "projected_cash_balance": 27000.0,
        "cash_shortage_risk": "LOW",
        "liquidity_ok": True,
    }


def constrained_cashflow():
    return {
        "current_cash": 5000.0,
        "expected_sales_revenue": 3000.0,
        "upcoming_expenses": 7000.0,
        "planned_purchase_cost": 3000.0,
        "net_cash_flow": -7000.0,
        "projected_cash_balance": -2000.0,
        "cash_shortage_risk": "HIGH",
        "liquidity_ok": False,
    }


def healthy_inventory():
    return {
        "product_id": "SKU_HEALTHY",
        "current_stock": 500.0,
        "forecast_demand": 100.0,
        "stock_gap": 0.0,
        "stock_coverage_days": 35.0,
        "stockout_risk": "LOW",
        "recommended_order_quantity": 0.0,
    }


def high_shortage_inventory():
    return {
        "product_id": "SKU_SHORTAGE_HIGH",
        "current_stock": 20.0,
        "forecast_demand": 200.0,
        "stock_gap": 180.0,
        "stock_coverage_days": 0.7,
        "stockout_risk": "HIGH",
        "recommended_order_quantity": 220.0,
    }


def medium_shortage_inventory():
    return {
        "product_id": "SKU_SHORTAGE_MED",
        "current_stock": 80.0,
        "forecast_demand": 100.0,
        "stock_gap": 20.0,
        "stock_coverage_days": 5.6,
        "stockout_risk": "MEDIUM",
        "recommended_order_quantity": 40.0,
    }


def healthy_credit():
    return {
        "customer_id": "CUST_PAID",
        "outstanding_amount": 0.0,
        "days_overdue": 0,
        "customer_risk": "NONE",
        "recommended_action": "monitor",
    }


def overdue_credit_35d():
    return {
        "customer_id": "CUST_LATE_35D",
        "outstanding_amount": 5000.0,
        "days_overdue": 35,
        "customer_risk": "HIGH",
        "recommended_action": "payment_reminder",
    }


def overdue_credit_15d():
    return {
        "customer_id": "CUST_LATE_15D",
        "outstanding_amount": 2000.0,
        "days_overdue": 15,
        "customer_risk": "MEDIUM",
        "recommended_action": "payment_reminder",
    }


def healthy_expense():
    return {
        "category": "Rent",
        "current_period_amount": 3000.0,
        "prior_period_amount": 3000.0,
        "increase_pct": 0.0,
        "trend": "stable",
        "risk": "LOW",
    }


def high_expense_spike():
    return {
        "category": "Marketing",
        "current_period_amount": 5000.0,
        "prior_period_amount": 3000.0,
        "increase_pct": 66.7,
        "trend": "increasing",
        "risk": "HIGH",
    }


def healthy_profitability():
    return {
        "product_id": "PROD_GOOD",
        "selling_price": 100.0,
        "cost_price": 50.0,
        "unit_profit": 50.0,
        "gross_profit": 5000.0,
        "profit_margin": 50.0,
        "classification": "highly_profitable",
    }


def loss_making_profitability():
    return {
        "product_id": "PROD_LOSS",
        "selling_price": 80.0,
        "cost_price": 120.0,
        "unit_profit": -40.0,
        "gross_profit": -1200.0,
        "profit_margin": -50.0,
        "classification": "loss_making",
    }


# ── Scenario Tests ──────────────────────────────────────────────────────────

def test_scenario_1_shortage_constrained_cash():
    """Scenario 1: High demand, low inventory, low cash, high receivables (Rule 1)."""
    decision = make_decision(
        inventory_result=high_shortage_inventory(),
        cashflow_result=constrained_cashflow(),
        credit_result=overdue_credit_35d(),
        expense_result=healthy_expense(),
        profitability_result=healthy_profitability(),
    )
    p = decision["primary_recommendation"]
    assert p["action"] == "partial_replenishment_and_collect_receivables", f"Got action: {p['action']}"
    assert p["priority"] == "high"
    # Rule 3 should also trigger as secondary
    sec_actions = [s["action"] for s in decision["secondary_recommendations"]]
    assert "send_payment_reminder" in sec_actions
    print("  [PASS] Scenario 1: Shortage + Constrained Cash -> partial_replenishment_and_collect_receivables")


def test_scenario_2_shortage_healthy_cash():
    """Scenario 2: High demand, low inventory, healthy cash (Rule 2 - HIGH priority)."""
    decision = make_decision(
        inventory_result=high_shortage_inventory(),
        cashflow_result=healthy_cashflow(),
        credit_result=healthy_credit(),
        expense_result=healthy_expense(),
        profitability_result=healthy_profitability(),
    )
    p = decision["primary_recommendation"]
    assert p["action"] == "full_replenishment"
    assert p["priority"] == "high"
    assert len(decision["secondary_recommendations"]) == 0
    print("  [PASS] Scenario 2: Shortage + Healthy Cash -> full_replenishment (HIGH)")


def test_scenario_3_all_healthy():
    """Scenario 3: Healthy stock, cash, receivables, expenses, profitability (Rule 6)."""
    decision = make_decision(
        inventory_result=healthy_inventory(),
        cashflow_result=healthy_cashflow(),
        credit_result=healthy_credit(),
        expense_result=healthy_expense(),
        profitability_result=healthy_profitability(),
    )
    p = decision["primary_recommendation"]
    assert p["action"] == "no_action"
    assert p["priority"] == "low"
    assert len(decision["secondary_recommendations"]) == 0
    print("  [PASS] Scenario 3: All Healthy -> no_action")


def test_scenario_4_expense_spike_only():
    """Scenario 4: Everything healthy EXCEPT one HIGH expense category (Rule 4 secondary)."""
    decision = make_decision(
        inventory_result=healthy_inventory(),
        cashflow_result=healthy_cashflow(),
        credit_result=healthy_credit(),
        expense_result=high_expense_spike(),
        profitability_result=healthy_profitability(),
    )
    p = decision["primary_recommendation"]
    assert p["action"] == "no_action"
    sec = decision["secondary_recommendations"]
    assert len(sec) == 1
    assert sec[0]["action"] == "review_expense_category"
    assert sec[0]["priority"] == "medium"
    assert "Marketing" in sec[0]["reason"]
    print("  [PASS] Scenario 4: Expense Spike Only -> no_action + review_expense_category")


def test_scenario_5_loss_making_product_only():
    """Scenario 5: Everything healthy EXCEPT one loss-making product (Rule 5 secondary)."""
    decision = make_decision(
        inventory_result=healthy_inventory(),
        cashflow_result=healthy_cashflow(),
        credit_result=healthy_credit(),
        expense_result=healthy_expense(),
        profitability_result=loss_making_profitability(),
    )
    p = decision["primary_recommendation"]
    assert p["action"] == "no_action"
    sec = decision["secondary_recommendations"]
    assert len(sec) == 1
    assert sec[0]["action"] == "review_product_pricing"
    assert sec[0]["priority"] == "medium"
    assert "PROD_LOSS" in sec[0]["reason"]
    print("  [PASS] Scenario 5: Loss-Making Product Only -> no_action + review_product_pricing")


def test_scenario_6_overdue_credit_only():
    """Scenario 6: Everything healthy EXCEPT overdue customer > 7 days (Rule 3 secondary)."""
    decision = make_decision(
        inventory_result=healthy_inventory(),
        cashflow_result=healthy_cashflow(),
        credit_result=overdue_credit_15d(),
        expense_result=healthy_expense(),
        profitability_result=healthy_profitability(),
    )
    p = decision["primary_recommendation"]
    assert p["action"] == "no_action"
    sec = decision["secondary_recommendations"]
    assert len(sec) == 1
    assert sec[0]["action"] == "send_payment_reminder"
    assert sec[0]["priority"] == "medium"  # 15 days <= 30
    print("  [PASS] Scenario 6: Overdue Customer Only -> no_action + send_payment_reminder")


def test_scenario_7_medium_shortage_healthy_cash():
    """Scenario 7: Medium stock shortage, healthy cash (Rule 2 - MEDIUM priority)."""
    decision = make_decision(
        inventory_result=medium_shortage_inventory(),
        cashflow_result=healthy_cashflow(),
        credit_result=healthy_credit(),
        expense_result=healthy_expense(),
        profitability_result=healthy_profitability(),
    )
    p = decision["primary_recommendation"]
    assert p["action"] == "full_replenishment"
    assert p["priority"] == "medium"
    print("  [PASS] Scenario 7: Medium Shortage + Healthy Cash -> full_replenishment (MEDIUM)")


def test_scenario_8_multiple_secondary_issues():
    """Scenario 8: Multiple secondary issues triggering simultaneously (Rules 3, 4, 5)."""
    decision = make_decision(
        inventory_result=healthy_inventory(),
        cashflow_result=healthy_cashflow(),
        credit_result=[overdue_credit_35d(), overdue_credit_15d()],
        expense_result=[healthy_expense(), high_expense_spike()],
        profitability_result=[healthy_profitability(), loss_making_profitability()],
    )
    p = decision["primary_recommendation"]
    assert p["action"] == "no_action"
    sec = decision["secondary_recommendations"]
    assert len(sec) == 4  # 2 credit reminders + 1 expense review + 1 pricing review
    actions = [s["action"] for s in sec]
    assert actions.count("send_payment_reminder") == 2
    assert "review_expense_category" in actions
    assert "review_product_pricing" in actions
    # Confirm high priority recommendation is sorted first
    assert sec[0]["priority"] == "high"
    print("  [PASS] Scenario 8: Multiple Secondary Issues -> 4 sorted secondary recommendations")


def main():
    print("=" * 70)
    print("DECISION ENGINE UNIT TESTS")
    print("=" * 70)

    tests = [
        test_scenario_1_shortage_constrained_cash,
        test_scenario_2_shortage_healthy_cash,
        test_scenario_3_all_healthy,
        test_scenario_4_expense_spike_only,
        test_scenario_5_loss_making_product_only,
        test_scenario_6_overdue_credit_only,
        test_scenario_7_medium_shortage_healthy_cash,
        test_scenario_8_multiple_secondary_issues,
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

    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    if failed > 0:
        sys.exit(1)
    else:
        print("All tests passed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
