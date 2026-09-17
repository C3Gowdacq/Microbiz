"""
backend/app/services/agent_data_builder.py

Functions that query the CRUD database layer and assemble the exact input dicts
each agent function expects — replacing hardcoded Rosa's Retail Store payloads.

KNOWN SIMPLIFICATIONS (documented):
  1. sales_agent / forecast_demand: The Rossmann RF model requires ~25 Rossmann-specific
     features (store_type, competition_distance, promo2, etc.) that have no equivalent in our
     generic retail DB. We use the product's recent average daily sales from our `sales` table
     as the forecast_demand directly, bypassing the RF model for real-data scenarios.
     Rationale: the RF model is a Rossmann proof-of-concept; for the CRUD layer the real
     historical sales velocity from the DB is more accurate and meaningful.

  2. build_cashflow_input: "current_cash" is computed as total_sales_revenue - total_expenses
     from the DB (net position). A production system would connect to a bank account or
     ledger API. "upcoming_expenses" uses the average of the last 30 days' expense total.

  3. build_expense_input: "current period" = last 30 days; "prior period" = the 30 days
     before that. Both windows are configurable via parameters.
"""

import os
import sys
from datetime import date, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

# Make ml/src importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "src")))

from backend.app.models import Product, Sale, Invoice, Expense, BusinessSettings, Customer


# ── Utility helpers ───────────────────────────────────────────────────────────

def _get_settings(db: Session) -> BusinessSettings:
    """Return the singleton BusinessSettings row (creates defaults if absent)."""
    s = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
    if not s:
        s = BusinessSettings(id=1, min_cash_reserve=25000.0, currency="INR")
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def _avg_daily_sales(product_id: str, db: Session, lookback_days: int = 30) -> float:
    """
    Compute average daily sales quantity for a product over the last `lookback_days`.
    Returns 0.0 if no sales exist (newly listed product).

    SIMPLIFICATION: Used instead of calling sales_agent's RF model because
    our generic DB doesn't store the Rossmann-specific features required by the model.
    """
    since = date.today() - timedelta(days=lookback_days)
    total_qty = db.query(func.coalesce(func.sum(Sale.quantity), 0.0)) \
        .filter(Sale.product_id == product_id, Sale.date >= since).scalar()
    return float(total_qty) / lookback_days


# ── 1. build_inventory_input ──────────────────────────────────────────────────

def build_inventory_input(product_id: str, db: Session, forecast_horizon_days: int = 7) -> Optional[Dict[str, Any]]:
    """
    Build the input dict that inventory_agent.calculate_inventory_risk() expects,
    populated from real DB rows.

    Uses the trained RF model (via feature_vector_builder) when the product has
    ML profile fields. Falls back to velocity average otherwise.

    Returns None if the product does not exist.
    """
    from backend.app.services.feature_vector_builder import forecast_product_demand

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    # Use ML-powered forecast or velocity fallback
    try:
        forecast_result = forecast_product_demand(product, db, forecast_horizon_days)
        forecast_demand = forecast_result["predicted_units"]
    except Exception:
        # If anything goes wrong with ML, fall back to velocity
        avg_daily = _avg_daily_sales(product_id, db, lookback_days=30)
        forecast_demand = avg_daily * forecast_horizon_days

    # If current_stock is below reorder_level or no sales yet, use reorder_level as minimum expected demand
    if (product.current_stock < product.reorder_level or forecast_demand == 0.0) and product.reorder_level > 0:
        forecast_demand = max(forecast_demand, product.reorder_level)

    return {
        "product_id": product_id,
        "current_stock": product.current_stock,
        "forecast_demand": round(forecast_demand, 2),
        "reorder_level": product.reorder_level,
        "safety_stock": product.safety_stock,
        "lead_time_days": product.lead_time_days,
    }


def build_all_inventory_inputs(db: Session, forecast_horizon_days: int = 7) -> List[Dict[str, Any]]:
    """Build inventory inputs for every product in the database."""
    products = db.query(Product).all()
    inputs = []
    for p in products:
        inp = build_inventory_input(p.id, db, forecast_horizon_days)
        if inp:
            inputs.append(inp)
    return inputs


# ── 2. build_cashflow_input ───────────────────────────────────────────────────

def build_cashflow_input(db: Session, forecast_horizon_days: int = 7) -> Dict[str, Any]:
    """
    Build the input dict that cashflow_agent.calculate_cashflow_risk() expects,
    derived from real DB data.

    SIMPLIFICATION:
    - current_cash = sum(all sales revenue) - sum(all expenses current_period_amount)
      (net position from DB; a real system would connect to a bank ledger)
    - expected_sales_revenue = avg daily sales over last 30 days * horizon
    - upcoming_expenses = avg daily expense over last 30 days * horizon
    - planned_purchase_cost = 0 (no purchase orders table yet — future work)
    - min_cash_reserve from business_settings
    """
    settings = _get_settings(db)

    total_sales = float(db.query(func.coalesce(func.sum(Sale.total_amount), 0.0)).scalar())
    total_expenses = float(db.query(func.coalesce(func.sum(Expense.current_period_amount), 0.0)).scalar())
    current_cash = total_sales - total_expenses

    # Recent average daily revenue (last 30 days)
    since_30 = date.today() - timedelta(days=30)
    recent_sales_total = float(
        db.query(func.coalesce(func.sum(Sale.total_amount), 0.0))
        .filter(Sale.date >= since_30)
        .scalar()
    )
    avg_daily_revenue = recent_sales_total / 30.0
    expected_sales_revenue = avg_daily_revenue * forecast_horizon_days

    # Recent average daily expenses (last 30 days)
    recent_expenses_total = float(
        db.query(func.coalesce(func.sum(Expense.current_period_amount), 0.0))
        .filter(Expense.date >= since_30)
        .scalar()
    )
    avg_daily_expense = recent_expenses_total / 30.0
    upcoming_expenses = avg_daily_expense * forecast_horizon_days

    return {
        "current_cash": round(current_cash, 2),
        "expected_sales_revenue": round(expected_sales_revenue, 2),
        "upcoming_expenses": round(upcoming_expenses, 2),
        "planned_purchase_cost": 0.0,   # future work: purchase orders table
        "min_cash_reserve": settings.min_cash_reserve,
    }


# ── 3. build_credit_input / build_all_overdue_credit_inputs ──────────────────

def build_credit_input(customer_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Build the input dict for credit_agent.analyze_customer_credit() for the
    worst (most overdue / highest outstanding) unpaid invoice of this customer.

    Returns None if the customer has no unpaid invoices.
    """
    # Find all unpaid invoices for this customer, ordered by overdue severity
    invoices = (
        db.query(Invoice)
        .filter(
            Invoice.customer_id == customer_id,
            Invoice.status.in_(["unpaid", "partially_paid"]),
        )
        .order_by(Invoice.due_date)
        .all()
    )
    if not invoices:
        return None

    # Pick the oldest (most urgent) invoice
    inv = invoices[0]
    return {
        "customer_id": customer_id,
        "invoice_amount": inv.invoice_amount,
        "amount_paid": inv.amount_paid,
        "due_date": inv.due_date,
        "today": date.today(),
    }


def build_all_overdue_credit_inputs(db: Session) -> List[Dict[str, Any]]:
    """
    Return credit inputs for every customer who has at least one unpaid/
    partially-paid invoice that is past due today.
    """
    today = date.today()
    overdue_invoices = (
        db.query(Invoice)
        .filter(
            Invoice.status.in_(["unpaid", "partially_paid"]),
            Invoice.due_date < today,
        )
        .all()
    )

    seen_customers = set()
    inputs = []
    for inv in overdue_invoices:
        if inv.customer_id not in seen_customers:
            seen_customers.add(inv.customer_id)
            inp = build_credit_input(inv.customer_id, db)
            if inp:
                inputs.append(inp)
    return inputs


# ── 4. build_expense_input ────────────────────────────────────────────────────

def build_expense_input(
    category: str,
    db: Session,
    current_period_days: int = 30,
    prior_period_days: int = 30,
) -> Dict[str, Any]:
    """
    Build the input dict for expense_agent.analyze_expense_trend() for one category.

    Current period = last `current_period_days` days.
    Prior period   = the `prior_period_days` days before the current period.
    """
    today = date.today()
    current_start = today - timedelta(days=current_period_days)
    prior_end     = current_start
    prior_start   = prior_end - timedelta(days=prior_period_days)

    current_total = float(
        db.query(func.coalesce(func.sum(Expense.current_period_amount), 0.0))
        .filter(Expense.category == category, Expense.date >= current_start, Expense.date <= today)
        .scalar()
    )
    prior_total = float(
        db.query(func.coalesce(func.sum(Expense.current_period_amount), 0.0))
        .filter(Expense.category == category, Expense.date >= prior_start, Expense.date < prior_end)
        .scalar()
    )

    return {
        "category": category,
        "current_period_amount": round(current_total, 2),
        "prior_period_amount": round(prior_total, 2),
    }


def build_all_expense_inputs(db: Session) -> List[Dict[str, Any]]:
    """Build expense inputs for every distinct expense category in the DB."""
    categories = [
        row[0] for row in db.query(Expense.category).distinct().all()
    ]
    return [build_expense_input(cat, db) for cat in categories]


# ── 5. build_profitability_input ──────────────────────────────────────────────

def build_profitability_input(
    product_id: str,
    db: Session,
    lookback_days: int = 30,
) -> Optional[Dict[str, Any]]:
    """
    Build the input dict for profitability_agent.calculate_profitability().

    quantity_sold = sum of sale quantities in the last `lookback_days`.
    Returns None if the product does not exist.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    since = date.today() - timedelta(days=lookback_days)
    qty_sold = float(
        db.query(func.coalesce(func.sum(Sale.quantity), 0.0))
        .filter(Sale.product_id == product_id, Sale.date >= since)
        .scalar()
    )

    return {
        "product_id": product_id,
        "selling_price": product.selling_price,
        "cost_price": product.cost_price,
        "quantity_sold": qty_sold,
    }


def build_all_profitability_inputs(db: Session, lookback_days: int = 30) -> List[Dict[str, Any]]:
    """Build profitability inputs for every product."""
    products = db.query(Product).all()
    inputs = []
    for p in products:
        inp = build_profitability_input(p.id, db, lookback_days)
        if inp:
            inputs.append(inp)
    return inputs
