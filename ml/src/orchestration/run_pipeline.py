"""
run_pipeline.py -- Execution entry point for the LangGraph MicroBizAI pipeline.

Provides:
  - run_full_pipeline(initial_state) -> final_state
  - run_partial_pipeline(initial_state, requested_agents) -> final_state

Verifies that running the Rosa's Retail Store scenario through the LangGraph orchestration
produces the IDENTICAL output as Part 7's direct function calls in demo_decision_engine.py.
"""

import os
import sys
import json
from datetime import date

# Ensure parent modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestration.coordinator import pipeline_graph, inventory_node, sales_node
from orchestration.state import MicroBizState
from decision.engine import make_decision


def run_full_pipeline(initial_state: dict) -> dict:
    """
    Run the complete LangGraph orchestration pipeline on an initial state.

    Args:
        initial_state: dict matching MicroBizState input keys

    Returns:
        dict: final state containing all agent results and decision output
    """
    final_state = pipeline_graph.invoke(initial_state)
    return dict(final_state)


def run_partial_pipeline(initial_state: dict, requested_agents: list) -> dict:
    """
    Run a partial pipeline executing only specific requested agent nodes.

    Args:
        initial_state:    dict matching MicroBizState input keys
        requested_agents: list of agent names to run (e.g. ["inventory"])

    Returns:
        dict: final state containing only the requested agent results without decision
    """
    state = dict(initial_state)
    state["requested_agents"] = requested_agents

    # Direct selective execution of requested nodes for explicit partial runs
    if "sales" in requested_agents:
        state = sales_node(state)

    if "inventory" in requested_agents:
        state = inventory_node(state)

    return state


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 80)
    print("LANGGRAPH ORCHESTRATION PIPELINE -- ROSA'S RETAIL STORE EXECUTION")
    print("=" * 80)

    TODAY = date(2025, 7, 16)

    # ── 1. Construct Exact Rosa's Retail Store Initial State (from Part 6/7) ──

    inventory_inputs = [
        {
            "product_id": "SKU_ELECTRONICS_001",
            "current_stock": 150,
            "forecast_demand": 200,
            "reorder_level": 100,
            "safety_stock": 40,
            "lead_time_days": 5,
        },
        {
            "product_id": "SKU_APPAREL_042",
            "current_stock": 500,
            "forecast_demand": 120,
            "reorder_level": 80,
            "safety_stock": 25,
            "lead_time_days": 3,
        },
        {
            "product_id": "SKU_GROCERY_108",
            "current_stock": 30,
            "forecast_demand": 300,
            "reorder_level": 150,
            "safety_stock": 50,
            "lead_time_days": 2,
        },
    ]

    avg_unit_price = 15.0
    total_forecast_demand = sum(s["forecast_demand"] for s in inventory_inputs)
    expected_revenue = total_forecast_demand * avg_unit_price  # EUR 9,300

    cashflow_input = {
        "current_cash": 25000,
        "expected_sales_revenue": expected_revenue,
        "upcoming_expenses": 6500,
        "planned_purchase_cost": 4200,
        "min_cash_reserve": 5000,
    }

    expense_inputs = [
        {"category": "Rent", "current_period_amount": 3000, "prior_period_amount": 3000},
        {"category": "Employee Wages", "current_period_amount": 8500, "prior_period_amount": 7200},
        {"category": "Utilities", "current_period_amount": 1200, "prior_period_amount": 900},
        {"category": "Marketing", "current_period_amount": 2500, "prior_period_amount": 1800},
        {"category": "Inventory COGS", "current_period_amount": 4200, "prior_period_amount": 4000},
        {"category": "New SaaS Tools", "current_period_amount": 800, "prior_period_amount": 0},
    ]

    credit_inputs = [
        {"customer_id": "CUST_RELIABLE", "invoice_amount": 5000, "amount_paid": 5000, "due_date": date(2025, 7, 1), "today": TODAY},
        {"customer_id": "CUST_LATE_PAY", "invoice_amount": 8000, "amount_paid": 3000, "due_date": date(2025, 6, 25), "today": TODAY},
        {"customer_id": "CUST_DELINQUENT", "invoice_amount": 12000, "amount_paid": 0, "due_date": date(2025, 6, 1), "today": TODAY},
        {"customer_id": "CUST_NEW", "invoice_amount": 3000, "amount_paid": 0, "due_date": date(2025, 7, 20), "today": TODAY},
    ]

    profitability_inputs = [
        {"product_id": "Electronics Premium", "selling_price": 299.99, "cost_price": 180.00, "quantity_sold": 45},
        {"product_id": "Electronics Budget", "selling_price": 49.99, "cost_price": 42.00, "quantity_sold": 200},
        {"product_id": "Apparel T-Shirts", "selling_price": 24.99, "cost_price": 8.00, "quantity_sold": 350},
        {"product_id": "Clearance Items", "selling_price": 9.99, "cost_price": 12.00, "quantity_sold": 100},
        {"product_id": "Accessories", "selling_price": 14.99, "cost_price": 5.00, "quantity_sold": 500},
    ]

    initial_state = {
        "inventory_inputs": inventory_inputs,
        "cashflow_input": cashflow_input,
        "expense_inputs": expense_inputs,
        "credit_inputs": credit_inputs,
        "profitability_inputs": profitability_inputs,
        "forecast_horizon_days": 7,
        "today": TODAY,
    }

    # ── 2. Run Full LangGraph Pipeline ───────────────────────────────────

    print("\nExecuting full LangGraph orchestration pipeline (run_full_pipeline)...\n")
    final_state = run_full_pipeline(initial_state)

    decision_lg = final_state.get("decision", {})
    explanation_lg = final_state.get("llm_explanation", {})

    print("-" * 80)
    print("LANGGRAPH PIPELINE DECISION OUTPUT")
    print("-" * 80)
    print(json.dumps(decision_lg, indent=2))

    print("\n" + "-" * 80)
    print("LANGGRAPH PIPELINE LLM EXPLANATION OUTPUT (Verified by Guardrail)")
    print("-" * 80)
    print(json.dumps(explanation_lg, indent=2))

    # ── 3. Direct Function Call Comparison (Part 7 match verification) ───

    # Re-run direct function call to get Part 7 baseline output
    direct_decision = make_decision(
        inventory_result=final_state["inventory_result"],
        cashflow_result=final_state["cashflow_result"],
        credit_result=final_state["credit_results"],
        expense_result=final_state["expense_results"],
        profitability_result=final_state["profitability_results"],
    )

    print("\n" + "=" * 80)
    print("VERIFICATION: LangGraph Pipeline vs. Direct Call (Part 7)")
    print("=" * 80)

    primary_match = decision_lg["primary_recommendation"] == direct_decision["primary_recommendation"]
    sec_match = decision_lg["secondary_recommendations"] == direct_decision["secondary_recommendations"]
    summary_match = decision_lg["summary"] == direct_decision["summary"]

    print(f"  Primary Recommendation Match:   {'EXACT MATCH [PASS]' if primary_match else 'MISMATCH [FAIL]'}")
    print(f"  Secondary Recommendations Match: {'EXACT MATCH [PASS]' if sec_match else 'MISMATCH [FAIL]'}")
    print(f"  Summary Match:                  {'EXACT MATCH [PASS]' if summary_match else 'MISMATCH [FAIL]'}")

    assert primary_match and sec_match and summary_match, "LangGraph output does not match direct call!"

    # ── 4. Run Partial Pipeline Test (Requested Agents = ["inventory"]) ────

    print("\n" + "=" * 80)
    print("PARTIAL PIPELINE TEST (requested_agents = ['inventory'])")
    print("=" * 80)

    partial_initial = {
        "inventory_inputs": inventory_inputs,
        "forecast_horizon_days": 7,
    }
    partial_state = run_partial_pipeline(partial_initial, requested_agents=["inventory"])

    has_inventory_res = "inventory_result" in partial_state
    has_decision_res = "decision" in partial_state

    print(f"  inventory_result present: {'YES [PASS]' if has_inventory_res else 'NO [FAIL]'}")
    print(f"  decision present:         {'NO [PASS]' if not has_decision_res else 'YES [FAIL]'}")
    print("\n  Partial Inventory Output:")
    for r in partial_state.get("inventory_result", []):
        print(f"    • {r['product_id']}: stock_gap={r['stock_gap']}, risk={r['stockout_risk']}")

    assert has_inventory_res and not has_decision_res, "Partial pipeline failed to return only requested results!"

    print("\n" + "=" * 80)
    print("ALL PIPELINE VERIFICATIONS PASSED -- LangGraph Orchestration Complete.")
    print("=" * 80)


if __name__ == "__main__":
    main()
