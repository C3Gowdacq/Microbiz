"""
cashflow_agent.py -- Standalone Cash Flow Risk Assessment Agent.

Takes structured inputs (current cash, expected revenue, upcoming expenses,
planned purchase costs, minimum cash reserve) and returns a cash flow risk
assessment dict.

This module is a pure-function module with no database or API dependencies.

Public API:
  - calculate_cashflow_risk(...) -> dict
"""


def calculate_cashflow_risk(
    current_cash,
    expected_sales_revenue,
    upcoming_expenses,
    planned_purchase_cost,
    min_cash_reserve,
):
    """
    Assess cash flow risk for a business over a planning period.

    Args:
        current_cash:           Cash on hand at the start of the period (float >= 0).
        expected_sales_revenue: Projected revenue from sales (float >= 0).
        upcoming_expenses:      Known upcoming expenses (rent, wages, utilities, etc.) (float >= 0).
        planned_purchase_cost:  Cost of planned inventory/supply purchases (float >= 0).
        min_cash_reserve:       Minimum acceptable cash balance to maintain (float >= 0).

    Returns:
        dict with keys:
            current_cash, expected_sales_revenue, upcoming_expenses,
            planned_purchase_cost, net_cash_flow, projected_cash_balance,
            cash_shortage_risk ("HIGH" | "MEDIUM" | "LOW"),
            liquidity_ok (bool)
    """
    # ── Core calculations ────────────────────────────────────────────────

    net_cash_flow = expected_sales_revenue - upcoming_expenses - planned_purchase_cost
    projected_cash_balance = current_cash + net_cash_flow

    # ── Risk classification ──────────────────────────────────────────────

    if projected_cash_balance < min_cash_reserve:
        cash_shortage_risk = "HIGH"
    elif projected_cash_balance < min_cash_reserve * 1.5:
        cash_shortage_risk = "MEDIUM"
    else:
        cash_shortage_risk = "LOW"

    liquidity_ok = projected_cash_balance >= min_cash_reserve

    # ── Build output contract ────────────────────────────────────────────

    return {
        "current_cash": round(float(current_cash), 2),
        "expected_sales_revenue": round(float(expected_sales_revenue), 2),
        "upcoming_expenses": round(float(upcoming_expenses), 2),
        "planned_purchase_cost": round(float(planned_purchase_cost), 2),
        "net_cash_flow": round(float(net_cash_flow), 2),
        "projected_cash_balance": round(float(projected_cash_balance), 2),
        "cash_shortage_risk": cash_shortage_risk,
        "liquidity_ok": liquidity_ok,
    }
