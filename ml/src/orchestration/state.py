"""
state.py -- State schema definition for LangGraph orchestration.

Defines MicroBizState, the shared TypedDict passed between graph nodes
representing the complete state of a business health analysis run.
"""

from typing import TypedDict, Optional, List, Dict, Any


class MicroBizState(TypedDict, total=False):
    """
    Shared state passed through the LangGraph node graph.

    Contains raw inputs, intermediate agent calculation results,
    final decision engine outputs, and error tracking.
    """
    product_id: str
    store_features: dict          # raw feature dict or row for sales_agent
    forecast_horizon_days: int    # horizon days for sales forecasting
    sales_forecast: dict          # sales_agent output

    inventory_inputs: list        # list of inventory scenarios for inventory_agent
    inventory_result: list        # inventory_agent outputs (list of dicts)

    cashflow_input: dict          # raw inputs needed by cashflow_agent (current_cash, etc.)
    cashflow_result: dict         # cashflow_agent output

    expense_inputs: list          # list of category dicts for expense_agent
    expense_results: list         # expense_agent outputs (list of dicts)

    credit_inputs: list           # list of customer dicts for credit_agent
    credit_results: list          # credit_agent outputs (list of dicts)

    profitability_inputs: list    # list of product dicts for profitability_agent
    profitability_results: list   # profitability_agent outputs (list of dicts)

    decision: dict                # decision_engine output (primary, secondary, summary)
    llm_explanation: dict         # verified LLM explanation output (summary, reasoning, customer msg)
    requested_agents: list        # list of agent names for partial pipeline runs
    error: Optional[str]          # error message if any node fails
