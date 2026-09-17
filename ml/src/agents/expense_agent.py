"""
expense_agent.py -- Standalone Expense Trend Analysis Agent.

Takes structured inputs (expense category, current and prior period amounts)
and returns a trend analysis with risk classification.

This module is a pure-function module with no database or API dependencies.

Public API:
  - analyze_expense_trend(...) -> dict
"""


def analyze_expense_trend(category, current_period_amount, prior_period_amount):
    """
    Analyze expense trend between two periods for a given category.

    Args:
        category:              Name of the expense category (str).
        current_period_amount: Total expense in the current period (float >= 0).
        prior_period_amount:   Total expense in the prior period (float >= 0).

    Returns:
        dict with keys:
            category, current_period_amount, prior_period_amount,
            increase_pct (float, percentage change),
            trend ("increasing" | "decreasing" | "stable" | "new_category"),
            risk ("HIGH" | "MEDIUM" | "LOW")
    """
    # ── Guard against division by zero (new category) ────────────────────

    if prior_period_amount == 0:
        return {
            "category": category,
            "current_period_amount": round(float(current_period_amount), 2),
            "prior_period_amount": round(float(prior_period_amount), 2),
            "increase_pct": None,
            "trend": "new_category",
            "risk": "LOW",
        }

    # ── Core calculation ─────────────────────────────────────────────────

    increase_pct = ((current_period_amount - prior_period_amount) / prior_period_amount) * 100.0

    # ── Trend classification ─────────────────────────────────────────────

    if increase_pct > 0:
        trend = "increasing"
    elif increase_pct < 0:
        trend = "decreasing"
    else:
        trend = "stable"

    # ── Risk classification (based on magnitude of increase) ─────────────

    if increase_pct > 30:
        risk = "HIGH"
    elif increase_pct > 10:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    # ── Build output contract ────────────────────────────────────────────

    return {
        "category": category,
        "current_period_amount": round(float(current_period_amount), 2),
        "prior_period_amount": round(float(prior_period_amount), 2),
        "increase_pct": round(float(increase_pct), 2),
        "trend": trend,
        "risk": risk,
    }
