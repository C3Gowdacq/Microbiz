"""
routers/agents.py -- Targeted per-entity agent check endpoints.

Each endpoint reads REAL data from the database via agent_data_builder,
runs the appropriate agent, optionally saves a Recommendation row, and returns
the agent result alongside any newly created recommendation_id.

Endpoints:
  POST /api/products/{id}/check-inventory      check stockout risk for one product
  POST /api/products/{id}/check-profitability  check margin / loss-making for one product
  POST /api/customers/{id}/check-credit        check overdue credit for one customer
  POST /api/expenses/check-trend               body: {category} -> check expense spike
  POST /api/cashflow/check-real               business-wide cashflow check from DB

The existing /api/agents/run-full (in main.py) is also updated to loop all
entities from real DB data — see main.py.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "src")))

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.database import get_db
from backend.app.models import Recommendation
from backend.app.services.agent_data_builder import (
    build_inventory_input,
    build_profitability_input,
    build_credit_input,
    build_expense_input,
    build_cashflow_input,
)

from agents.inventory_agent import calculate_inventory_risk
from agents.profitability_agent import calculate_profitability
from agents.credit_agent import analyze_customer_credit
from agents.expense_agent import analyze_expense_trend
from agents.cashflow_agent import calculate_cashflow_risk

router = APIRouter(tags=["Targeted Agent Checks"])


# ── Helper: persist a recommendation if risk threshold is met ─────────────────

def _maybe_save_recommendation(
    db: Session,
    condition: bool,
    action: str,
    priority: str,
    reason: str,
) -> int | None:
    """Save a Recommendation row if condition is True. Returns new id or None."""
    if not condition:
        return None
    rec = Recommendation(
        primary_action=action,
        priority=priority,
        reason=reason,
        secondary_recommendations=[],
        status="pending",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.id


# ── 1. Inventory Check ────────────────────────────────────────────────────────

@router.post("/api/products/{product_id}/check-inventory")
def check_inventory_for_product(product_id: str, db: Session = Depends(get_db)):
    """
    Build real inventory inputs for this product from DB and run inventory_agent.
    Creates a pending Recommendation if risk is HIGH or MEDIUM.
    """
    inp = build_inventory_input(product_id, db)
    if inp is None:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")

    result = calculate_inventory_risk(
        product_id=inp["product_id"],
        current_stock=inp["current_stock"],
        forecast_demand=inp["forecast_demand"],
        reorder_level=inp["reorder_level"],
        safety_stock=inp["safety_stock"],
        lead_time_days=inp["lead_time_days"],
    )

    risk = result.get("stockout_risk", "LOW")
    rec_id = _maybe_save_recommendation(
        db,
        condition=risk in ("HIGH", "MEDIUM"),
        action="full_replenishment" if risk == "HIGH" else "partial_replenishment",
        priority=risk.lower(),
        reason=(
            f"Product '{product_id}' has stockout risk={risk}. "
            f"current_stock={inp['current_stock']}, "
            f"forecast_demand={inp['forecast_demand']} over 7 days, "
            f"stock_gap={result.get('stock_gap', 0)}."
        ),
    )

    return {
        "product_id": product_id,
        "agent_result": result,
        "recommendation_id": rec_id,
        "recommendation_created": rec_id is not None,
    }


# ── 2. Profitability Check ────────────────────────────────────────────────────

@router.post("/api/products/{product_id}/check-profitability")
def check_profitability_for_product(product_id: str, db: Session = Depends(get_db)):
    """
    Build real profitability inputs for this product from DB and run profitability_agent.
    Creates a pending Recommendation if classification is 'loss_making' or 'low_margin'.
    """
    inp = build_profitability_input(product_id, db)
    if inp is None:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")

    result = calculate_profitability(
        product_id=inp["product_id"],
        selling_price=inp["selling_price"],
        cost_price=inp["cost_price"],
        quantity_sold=inp["quantity_sold"],
    )

    classification = result.get("classification", "healthy_margin")
    is_problem = classification in ("loss_making", "low_margin")

    rec_id = _maybe_save_recommendation(
        db,
        condition=is_problem,
        action="review_product_pricing",
        priority="high" if classification == "loss_making" else "medium",
        reason=(
            f"Product '{product_id}' is {classification} with margin={result.get('profit_margin', 0):.1f}%. "
            f"selling_price={inp['selling_price']}, cost_price={inp['cost_price']}."
        ),
    )

    return {
        "product_id": product_id,
        "agent_result": result,
        "recommendation_id": rec_id,
        "recommendation_created": rec_id is not None,
    }


# ── 3. Credit Check ───────────────────────────────────────────────────────────

@router.post("/api/customers/{customer_id}/check-credit")
def check_credit_for_customer(customer_id: str, db: Session = Depends(get_db)):
    """
    Build real credit input for this customer from DB and run credit_agent.
    Creates a pending Recommendation if customer_risk is HIGH or MEDIUM.
    """
    inp = build_credit_input(customer_id, db)
    if inp is None:
        return {
            "customer_id": customer_id,
            "message": "No unpaid invoices found — no credit risk.",
            "agent_result": None,
            "recommendation_id": None,
            "recommendation_created": False,
        }

    result = analyze_customer_credit(
        customer_id=inp["customer_id"],
        invoice_amount=inp["invoice_amount"],
        amount_paid=inp["amount_paid"],
        due_date=inp["due_date"],
        today=inp.get("today"),
    )

    risk = result.get("customer_risk", "NONE")
    rec_id = _maybe_save_recommendation(
        db,
        condition=risk in ("HIGH", "MEDIUM"),
        action="send_payment_reminder",
        priority=risk.lower(),
        reason=(
            f"Customer '{customer_id}' has {risk} credit risk. "
            f"outstanding_amount={result.get('outstanding_amount', 0):.2f}, "
            f"days_overdue={result.get('days_overdue', 0)}."
        ),
    )

    return {
        "customer_id": customer_id,
        "agent_result": result,
        "recommendation_id": rec_id,
        "recommendation_created": rec_id is not None,
    }


# ── 4. Expense Trend Check ────────────────────────────────────────────────────

class ExpenseTrendRequest(BaseModel):
    category: str


@router.post("/api/expenses/check-trend")
def check_expense_trend(req: ExpenseTrendRequest, db: Session = Depends(get_db)):
    """
    Build real expense trend input for a category from DB and run expense_agent.
    Creates a pending Recommendation if risk is HIGH or MEDIUM.
    """
    inp = build_expense_input(req.category, db)
    result = analyze_expense_trend(
        category=inp["category"],
        current_period_amount=inp["current_period_amount"],
        prior_period_amount=inp["prior_period_amount"],
    )

    risk = result.get("risk", "LOW")
    rec_id = _maybe_save_recommendation(
        db,
        condition=risk in ("HIGH", "MEDIUM"),
        action="review_expense_category",
        priority=risk.lower(),
        reason=(
            f"Expense category '{req.category}' has {risk} trend risk. "
            f"current={inp['current_period_amount']:.2f}, prior={inp['prior_period_amount']:.2f}, "
            f"increase={result.get('increase_pct') or 0.0:.1f}%."
        ),
    )

    return {
        "category": req.category,
        "agent_result": result,
        "recommendation_id": rec_id,
        "recommendation_created": rec_id is not None,
    }


# ── 5. Cashflow Check (real DB data) ──────────────────────────────────────────

@router.post("/api/cashflow/check-real")
def check_cashflow_real(db: Session = Depends(get_db)):
    """
    Build real cashflow inputs from DB aggregates and run cashflow_agent.
    Does not create a Recommendation row (cashflow informs the full-pipeline decision).
    """
    inp = build_cashflow_input(db)
    result = calculate_cashflow_risk(
        current_cash=inp["current_cash"],
        expected_sales_revenue=inp["expected_sales_revenue"],
        upcoming_expenses=inp["upcoming_expenses"],
        planned_purchase_cost=inp["planned_purchase_cost"],
        min_cash_reserve=inp["min_cash_reserve"],
    )
    return {
        "inputs_used": inp,
        "agent_result": result,
    }
