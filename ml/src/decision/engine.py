"""
engine.py -- Rule-Based Decision Engine for MicroBizAI.

Evaluates structured outputs from all 5 business agents (Inventory, Cash Flow,
Expense, Credit, Profitability) and produces a single, prioritized primary
recommendation along with a list of secondary actionable recommendations.

Pure rule-based logic (if/else), no machine learning, no LLM dependencies.
Deterministic and table-driven.

References:
  - MicroBizAI_Architecture.md Section 12
"""

from typing import List, Dict, Any, Union


def _to_list(val: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Helper to ensure input is always a list of dicts."""
    if val is None:
        return []
    if isinstance(val, dict):
        return [val]
    return list(val)


def make_decision(
    inventory_result: Union[Dict[str, Any], List[Dict[str, Any]]],
    cashflow_result: Dict[str, Any],
    credit_result: Union[Dict[str, Any], List[Dict[str, Any]]],
    expense_result: Union[Dict[str, Any], List[Dict[str, Any]]],
    profitability_result: Union[Dict[str, Any], List[Dict[str, Any]]],
    cost_price: float = None,
) -> Dict[str, Any]:
    """
    Synthesize outputs from all 5 agents into a prioritized business decision.

    Args:
        inventory_result:     Dict or list of dicts from inventory_agent.calculate_inventory_risk()
        cashflow_result:      Dict from cashflow_agent.calculate_cashflow_risk()
        credit_result:         Dict or list of dicts from credit_agent.analyze_customer_credit()
        expense_result:        Dict or list of dicts from expense_agent.analyze_expense_trend()
        profitability_result:  Dict or list of dicts from profitability_agent.calculate_profitability()
        cost_price:           Optional cost price override parameter (unused if embedded in profitability)

    Returns:
        Dict with keys:
            primary_recommendation: {action, priority, reason}
            secondary_recommendations: [{action, priority, reason}, ...]
            summary: 1-2 sentence plain-language overview
    """
    inventory_list = _to_list(inventory_result)
    credit_list = _to_list(credit_result)
    expense_list = _to_list(expense_result)
    profitability_list = _to_list(profitability_result)

    # ── 1. Evaluate Inventory & Cash Flow for Primary Recommendation ──────

    stockout_risks = [item.get("stockout_risk") for item in inventory_list]
    has_high_shortage = "HIGH" in stockout_risks
    has_medium_shortage = "MEDIUM" in stockout_risks
    has_stock_shortage = has_high_shortage or has_medium_shortage

    liquidity_ok = cashflow_result.get("liquidity_ok", True) if cashflow_result else True

    primary_recommendation = None

    # RULE 1: Stock shortage + Cash constrained
    if has_stock_shortage and not liquidity_ok:
        primary_recommendation = {
            "action": "partial_replenishment_and_collect_receivables",
            "priority": "high",
            "reason": (
                "Demand exceeds available stock, but full replenishment would breach the "
                "minimum cash reserve. Prioritize collecting overdue receivables to free up "
                "cash before ordering."
            ),
        }

    # RULE 2: Stock shortage + Cash sufficient
    elif has_stock_shortage and liquidity_ok:
        priority_level = "high" if has_high_shortage else "medium"
        primary_recommendation = {
            "action": "full_replenishment",
            "priority": priority_level,
            "reason": (
                "Demand exceeds available stock and sufficient cash reserve is available to "
                "replenish fully."
            ),
        }

    # RULE 6: No stock shortage
    else:
        primary_recommendation = {
            "action": "no_action",
            "priority": "low",
            "reason": (
                "Stock, cash, receivables, expenses, and profitability all within healthy ranges."
            ),
        }

    # ── 2. Evaluate Secondary Recommendations (Rules 3, 4, 5) ────────────

    secondary_recommendations = []

    # RULE 3: Overdue receivables
    for cust in credit_list:
        days_overdue = cust.get("days_overdue", 0)
        outstanding = cust.get("outstanding_amount", 0.0)
        cust_id = cust.get("customer_id", "Unknown")

        if days_overdue > 7 and outstanding > 0:
            priority_level = "high" if days_overdue > 30 else "medium"
            secondary_recommendations.append({
                "action": "send_payment_reminder",
                "priority": priority_level,
                "reason": f"Customer {cust_id} has outstanding overdue payment of EUR {outstanding:,.2f} for {days_overdue} days.",
            })

    # RULE 4: Expense category spike
    for exp in expense_list:
        risk = exp.get("risk")
        cat = exp.get("category", "Unknown")
        pct = exp.get("increase_pct")
        pct_str = f"{pct:.1f}%" if pct is not None else "N/A"

        if risk == "HIGH":
            secondary_recommendations.append({
                "action": "review_expense_category",
                "priority": "medium",
                "reason": f"{cat} costs increased {pct_str} compared to the prior period.",
            })

    # RULE 5: Loss-making product
    for prod in profitability_list:
        classification = prod.get("classification")
        prod_id = prod.get("product_id", "Unknown")
        margin = prod.get("profit_margin", 0.0)

        if classification == "loss_making":
            secondary_recommendations.append({
                "action": "review_product_pricing",
                "priority": "medium",
                "reason": f"{prod_id} is currently sold at a loss (margin: {margin:.1f}%).",
            })

    # Sort secondary recommendations by priority ("high" before "medium" before "low")
    priority_order = {"high": 0, "medium": 1, "low": 2}
    secondary_recommendations.sort(key=lambda r: priority_order.get(r["priority"], 3))

    # ── 3. Generate 1-2 Sentence Plain-Language Summary ─────────────────

    summary_parts = []
    primary_act = primary_recommendation["action"]

    if primary_act == "partial_replenishment_and_collect_receivables":
        summary_parts.append(
            "Primary concern: Stock shortage detected with cash constraints. Partial restocking is recommended alongside active collection of overdue receivables."
        )
    elif primary_act == "full_replenishment":
        summary_parts.append(
            "Primary recommendation: Full inventory replenishment recommended as demand exceeds stock and liquidity is sufficient."
        )
    else:
        summary_parts.append(
            "Primary status: Core operations are healthy with no urgent inventory replenishment required."
        )

    num_sec = len(secondary_recommendations)
    if num_sec > 0:
        summary_parts.append(
            f"Attention required for {num_sec} secondary alert(s) across credit collections, expense spikes, or product margins."
        )

    summary_text = " ".join(summary_parts)

    return {
        "primary_recommendation": primary_recommendation,
        "secondary_recommendations": secondary_recommendations,
        "summary": summary_text,
    }
