"""
coordinator.py -- LangGraph StateGraph orchestration pipeline for MicroBizAI.

Wires together existing agent functions (sales, inventory, cashflow, expense, credit,
profitability) and the decision engine into a clean node-based workflow graph.

No new business logic is added here -- this module only orchestrates existing,
tested agent functions and handles error propagation and conditional routing.

References:
  - MicroBizAI_Architecture.md Section 13
"""

import os
import sys
from typing import Dict, Any, List

# Ensure parent modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langgraph.graph import StateGraph, END
from orchestration.state import MicroBizState

from agents.sales_agent import get_multi_day_forecast, predict_from_df
from agents.inventory_agent import calculate_inventory_risk
from agents.cashflow_agent import calculate_cashflow_risk
from agents.expense_agent import analyze_expense_trend
from agents.credit_agent import analyze_customer_credit
from agents.profitability_agent import calculate_profitability
from decision.engine import make_decision
from llm.explain_chain import explain_decision


# ── Node 1: Sales Node ───────────────────────────────────────────────────────

def sales_node(state: MicroBizState) -> MicroBizState:
    """Wrapper node for sales_agent."""
    try:
        store_features = state.get("store_features")
        horizon = state.get("forecast_horizon_days", 7)

        if store_features is not None:
            total_demand = get_multi_day_forecast(store_features, days=horizon)
            state["sales_forecast"] = {
                "forecast_demand_7d": round(float(total_demand), 2),
                "horizon_days": horizon,
            }
    except Exception as e:
        state["error"] = f"sales_node error: {str(e)}"

    return state


# ── Node 2: Inventory Node ───────────────────────────────────────────────────

def inventory_node(state: MicroBizState) -> MicroBizState:
    """Wrapper node for inventory_agent."""
    try:
        inv_inputs = state.get("inventory_inputs", [])
        results = []

        for item in inv_inputs:
            # If sales_forecast was produced, allow it to override forecast_demand if needed
            demand = item.get("forecast_demand")
            if demand is None and "sales_forecast" in state:
                demand = state["sales_forecast"].get("forecast_demand_7d", 0.0)

            res = calculate_inventory_risk(
                product_id=item["product_id"],
                current_stock=item["current_stock"],
                forecast_demand=demand if demand is not None else item.get("forecast_demand", 0.0),
                reorder_level=item.get("reorder_level", 0.0),
                safety_stock=item.get("safety_stock", 0.0),
                lead_time_days=item.get("lead_time_days", 5),
                forecast_horizon_days=state.get("forecast_horizon_days", 7),
            )
            results.append(res)

        state["inventory_result"] = results
    except Exception as e:
        state["error"] = f"inventory_node error: {str(e)}"

    return state


# ── Node 3: Cash Flow Node ───────────────────────────────────────────────────

def cashflow_node(state: MicroBizState) -> MicroBizState:
    """Wrapper node for cashflow_agent."""
    try:
        cf_input = state.get("cashflow_input", {})
        if cf_input:
            res = calculate_cashflow_risk(
                current_cash=cf_input.get("current_cash", 0.0),
                expected_sales_revenue=cf_input.get("expected_sales_revenue", 0.0),
                upcoming_expenses=cf_input.get("upcoming_expenses", 0.0),
                planned_purchase_cost=cf_input.get("planned_purchase_cost", 0.0),
                min_cash_reserve=cf_input.get("min_cash_reserve", 0.0),
            )
            state["cashflow_result"] = res
    except Exception as e:
        state["error"] = f"cashflow_node error: {str(e)}"

    return state


# ── Node 4: Expense Node ─────────────────────────────────────────────────────

def expense_node(state: MicroBizState) -> MicroBizState:
    """Wrapper node for expense_agent."""
    try:
        exp_inputs = state.get("expense_inputs", [])
        results = []
        for item in exp_inputs:
            res = analyze_expense_trend(
                category=item["category"],
                current_period_amount=item["current_period_amount"],
                prior_period_amount=item["prior_period_amount"],
            )
            results.append(res)
        state["expense_results"] = results
    except Exception as e:
        state["error"] = f"expense_node error: {str(e)}"

    return state


# ── Node 5: Credit Node ──────────────────────────────────────────────────────

def credit_node(state: MicroBizState) -> MicroBizState:
    """Wrapper node for credit_agent."""
    try:
        cred_inputs = state.get("credit_inputs", [])
        results = []
        for item in cred_inputs:
            res = analyze_customer_credit(
                customer_id=item["customer_id"],
                invoice_amount=item["invoice_amount"],
                amount_paid=item["amount_paid"],
                due_date=item["due_date"],
                today=item.get("today") or state.get("today"),
            )
            results.append(res)
        state["credit_results"] = results
    except Exception as e:
        state["error"] = f"credit_node error: {str(e)}"

    return state


# ── Node 6: Profitability Node ───────────────────────────────────────────────

def profitability_node(state: MicroBizState) -> MicroBizState:
    """Wrapper node for profitability_agent."""
    try:
        prof_inputs = state.get("profitability_inputs", [])
        results = []
        for item in prof_inputs:
            res = calculate_profitability(
                product_id=item["product_id"],
                selling_price=item["selling_price"],
                cost_price=item["cost_price"],
                quantity_sold=item["quantity_sold"],
            )
            results.append(res)
        state["profitability_results"] = results
    except Exception as e:
        state["error"] = f"profitability_node error: {str(e)}"

    return state


# ── Node 7: Decision Node ────────────────────────────────────────────────────

def decision_node(state: MicroBizState) -> MicroBizState:
    """Wrapper node for decision_engine."""
    try:
        inv_res = state.get("inventory_result", [])
        cf_res = state.get("cashflow_result", {})
        cred_res = state.get("credit_results", [])
        exp_res = state.get("expense_results", [])
        prof_res = state.get("profitability_results", [])

        decision = make_decision(
            inventory_result=inv_res,
            cashflow_result=cf_res,
            credit_result=cred_res,
            expense_result=exp_res,
            profitability_result=prof_res,
        )
        state["decision"] = decision
    except Exception as e:
        state["error"] = f"decision_node error: {str(e)}"

    return state


# ── Node 8: LLM Explain Node ─────────────────────────────────────────────────

def llm_explain_node(state: MicroBizState) -> MicroBizState:
    """Wrapper node for LLM explanation generation and guardrail verification."""
    try:
        decision = state.get("decision")
        if decision:
            supporting_facts = {
                "inventory_result": state.get("inventory_result", []),
                "cashflow_result": state.get("cashflow_result", {}),
                "expense_results": state.get("expense_results", []),
                "credit_results": state.get("credit_results", []),
                "profitability_results": state.get("profitability_results", []),
            }
            explanation = explain_decision(decision, supporting_facts)
            state["llm_explanation"] = explanation
    except Exception as e:
        state["error"] = f"llm_explain_node error: {str(e)}"

    return state


# ── Conditional Routing Functions ───────────────────────────────────────────

def route_next_node(state: MicroBizState) -> str:
    """
    Determine the next node to execute based on requested_agents in state.
    If requested_agents is not specified or contains all agents, proceed linearly.
    """
    reqs = state.get("requested_agents")
    if not reqs:
        # Full sequential pipeline
        return "continue"

    # If all 5 business agents have produced results, route to decision_node
    has_inv = "inventory_result" in state
    has_cf = "cashflow_result" in state
    has_exp = "expense_results" in state
    has_cred = "credit_results" in state
    has_prof = "profitability_results" in state

    if has_inv and has_cf and has_exp and has_cred and has_prof:
        return "decision"

    return "continue"


def check_partial_completion(state: MicroBizState) -> str:
    """
    Check after agent nodes whether to route to decision_node or end early.
    If requested_agents was specified and decision_node is not requested / inputs missing,
    skip decision_node and route to END.
    """
    reqs = state.get("requested_agents")
    if reqs:
        # If decision is not in requested agents and not all agent outputs exist, skip decision
        if "decision" not in reqs and not ("decision_engine" in reqs):
            has_all = all(k in state for k in [
                "inventory_result", "cashflow_result",
                "expense_results", "credit_results", "profitability_results"
            ])
            if not has_all:
                return "end"

    return "continue"


# ── Build & Compile Graph ────────────────────────────────────────────────────

def build_pipeline_graph():
    """
    Build and compile the LangGraph StateGraph pipeline.

    Graph topology:
      sales_node -> inventory_node -> cashflow_node -> expense_node
      -> credit_node -> profitability_node -> [check_partial] -> decision_node -> llm_explain_node -> END
    """
    workflow = StateGraph(MicroBizState)

    # Add nodes
    workflow.add_node("sales", sales_node)
    workflow.add_node("inventory", inventory_node)
    workflow.add_node("cashflow", cashflow_node)
    workflow.add_node("expense", expense_node)
    workflow.add_node("credit", credit_node)
    workflow.add_node("profitability", profitability_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("llm_explain", llm_explain_node)

    # Set entry point
    workflow.set_entry_point("sales")

    # Add linear transitions
    workflow.add_edge("sales", "inventory")
    workflow.add_edge("inventory", "cashflow")
    workflow.add_edge("cashflow", "expense")
    workflow.add_edge("expense", "credit")
    workflow.add_edge("credit", "profitability")

    # Conditional edge before decision node for partial run support
    workflow.add_conditional_edges(
        "profitability",
        check_partial_completion,
        {
            "continue": "decision",
            "end": END,
        }
    )

    workflow.add_edge("decision", "llm_explain")
    workflow.add_edge("llm_explain", END)

    return workflow.compile()


# Compiled singleton graph
pipeline_graph = build_pipeline_graph()
