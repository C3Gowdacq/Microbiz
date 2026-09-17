"""
main.py -- FastAPI Application instance for MicroBizAI API.

Wraps existing agent, decision, and orchestration logic (from ml/src/) into structured REST
API endpoints, and includes full CRUD routers for Products, Customers, Sales, Invoices,
Expenses, Dashboard, and Business Settings.
"""

import os
import sys
from datetime import date
from typing import Dict, Any, List, Optional

# Ensure ml/src/ is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "src")))

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import engine, Base, get_db
from backend.app.models import Recommendation, HumanAction

from backend.app.schemas import (
    SalesForecastRequest,
    InventoryRiskRequest,
    CashflowCheckRequest,
    ExpenseAnalyzeRequest,
    CreditAnalyzeRequest,
    ProfitabilityAnalyzeRequest,
    RunFullPipelineRequest,
    RecommendationResponse,
    ModifyRecommendationRequest,
    RecommendationAnalyticsResponse,
)

# Import CRUD routers
from backend.app.routers import products, customers, sales, invoices, expenses, dashboard, settings as settings_router
from backend.app.routers import agents as agents_router
from backend.app.routers import forecasts as forecasts_router

# Import agent data builder (real DB -> agent inputs)
from backend.app.services.agent_data_builder import (
    build_all_inventory_inputs,
    build_cashflow_input,
    build_all_overdue_credit_inputs,
    build_all_expense_inputs,
    build_all_profitability_inputs,
)

# Import existing agents and orchestration code
from agents.sales_agent import get_multi_day_forecast
from agents.inventory_agent import calculate_inventory_risk
from agents.cashflow_agent import calculate_cashflow_risk
from agents.expense_agent import analyze_expense_trend
from agents.credit_agent import analyze_customer_credit
from agents.profitability_agent import calculate_profitability
from orchestration.run_pipeline import run_full_pipeline

# Initialize all SQLite database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MicroBizAI API",
    description="AI-powered business intelligence API for small retail businesses.",
    version="2.0.0",
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register CRUD Routers ─────────────────────────────────────────────────────
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(sales.router)
app.include_router(invoices.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)
app.include_router(agents_router.router)     # targeted per-entity agent checks
app.include_router(forecasts_router.router)  # dedicated sales forecasting router


# ── Root ──────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Root endpoint verifying API status."""
    return {"status": "MicroBizAI API running", "version": "2.0.0"}


# ── Business Logic Agent Endpoints ────────────────────────────────────────────

@app.post("/api/forecast/sales")
def forecast_sales(req: SalesForecastRequest):
    """Call sales_agent forecast functionality."""
    try:
        features = req.store_features or {}
        return get_multi_day_forecast(
            store_features=features,
            days=req.forecast_horizon_days,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sales forecast error: {str(e)}")


@app.post("/api/inventory/risk")
def check_inventory_risk(req: InventoryRiskRequest):
    """Call inventory_agent.calculate_inventory_risk()."""
    try:
        return calculate_inventory_risk(
            product_id=req.product_id,
            current_stock=req.current_stock,
            forecast_demand=req.forecast_demand,
            reorder_level=req.reorder_level,
            safety_stock=req.safety_stock,
            lead_time_days=req.lead_time_days,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory risk error: {str(e)}")


@app.post("/api/cashflow/check")
def check_cashflow_risk(req: CashflowCheckRequest):
    """Call cashflow_agent.calculate_cashflow_risk()."""
    try:
        return calculate_cashflow_risk(
            current_cash=req.current_cash,
            expected_sales_revenue=req.expected_sales_revenue,
            upcoming_expenses=req.upcoming_expenses,
            planned_purchase_cost=req.planned_purchase_cost,
            min_cash_reserve=req.min_cash_reserve,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cashflow check error: {str(e)}")


@app.post("/api/expenses/analyze")
def analyze_expenses(req: ExpenseAnalyzeRequest):
    """Call expense_agent.analyze_expense_trend()."""
    try:
        return analyze_expense_trend(
            category=req.category,
            current_period_amount=req.current_period_amount,
            prior_period_amount=req.prior_period_amount,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Expense analysis error: {str(e)}")


@app.post("/api/credit/analyze")
def analyze_credit(req: CreditAnalyzeRequest):
    """Call credit_agent.analyze_customer_credit()."""
    try:
        return analyze_customer_credit(
            customer_id=req.customer_id,
            invoice_amount=req.invoice_amount,
            amount_paid=req.amount_paid,
            due_date=req.due_date,
            today=req.today,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Credit analysis error: {str(e)}")


@app.post("/api/profitability/analyze")
def analyze_profitability(req: ProfitabilityAnalyzeRequest):
    """Call profitability_agent.calculate_profitability()."""
    try:
        return calculate_profitability(
            product_id=req.product_id,
            selling_price=req.selling_price,
            cost_price=req.cost_price,
            quantity_sold=req.quantity_sold,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profitability analysis error: {str(e)}")


@app.post("/api/agents/run-full")
def run_full_business_health_check(db: Session = Depends(get_db)):
    """
    Run the complete LangGraph pipeline using REAL data from the database.

    Loops over:
      - all products    -> inventory_agent + profitability_agent
      - all customers with overdue balances -> credit_agent
      - all expense categories -> expense_agent
      - business-wide -> cashflow_agent

    Aggregates all findings into ONE decision via the decision engine + LLM explanation.
    Saves a pending Recommendation row and returns it alongside the full result.
    """
    try:
        # ── Build inputs from real DB data ────────────────────────────────────
        inventory_inputs = build_all_inventory_inputs(db)
        cashflow_input = build_cashflow_input(db)
        expense_inputs = build_all_expense_inputs(db)
        credit_inputs = build_all_overdue_credit_inputs(db)
        profitability_inputs = build_all_profitability_inputs(db)

        # Provide defaults if DB is empty (fresh install)
        if not inventory_inputs:
            inventory_inputs = [{"product_id": "no_products", "current_stock": 0,
                                 "forecast_demand": 0, "reorder_level": 0,
                                 "safety_stock": 0, "lead_time_days": 1}]
        if not expense_inputs:
            expense_inputs = [{"category": "General", "current_period_amount": 0, "prior_period_amount": 0}]
        if not credit_inputs:
            credit_inputs = [{"customer_id": "no_customers", "invoice_amount": 0,
                              "amount_paid": 0, "due_date": None, "today": None}]
        if not profitability_inputs:
            profitability_inputs = [{"product_id": "no_products", "selling_price": 0,
                                     "cost_price": 0, "quantity_sold": 0}]

        state_dict = {
            "inventory_inputs":      inventory_inputs,
            "cashflow_input":        cashflow_input,
            "expense_inputs":        expense_inputs,
            "credit_inputs":         credit_inputs,
            "profitability_inputs":  profitability_inputs,
            "forecast_horizon_days": 7,
            "today":                 None,
        }

        pipeline_result = run_full_pipeline(state_dict)

        decision        = pipeline_result.get("decision")        or {}
        llm_explanation = pipeline_result.get("llm_explanation") or {}

        primary_rec = decision.get("primary_recommendation", {})
        sec_recs    = decision.get("secondary_recommendations", [])

        db_rec = Recommendation(
            primary_action=primary_rec.get("action", "no_action"),
            priority=primary_rec.get("priority", "medium"),
            reason=primary_rec.get("reason", ""),
            secondary_recommendations=sec_recs,
            llm_summary=llm_explanation.get("summary"),
            llm_reasoning=llm_explanation.get("reasoning"),
            suggested_customer_message=llm_explanation.get("suggested_customer_message"),
            status="pending",
        )
        db.add(db_rec)
        db.commit()
        db.refresh(db_rec)

        return {
            "recommendation_id": db_rec.id,
            "inputs_summary": {
                "products_checked":   len(inventory_inputs),
                "customers_checked":  len(credit_inputs),
                "expense_categories": len(expense_inputs),
            },
            "decision":          decision,
            "llm_explanation":   llm_explanation,
            "error":             pipeline_result.get("error"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full pipeline error: {str(e)}")


# ── HITL Recommendation Endpoints ────────────────────────────────────────────

@app.get("/api/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """List all stored recommendations, optionally filtered by status."""
    query = db.query(Recommendation)
    if status:
        query = query.filter(Recommendation.status == status)
    return query.order_by(Recommendation.id.desc()).all()


@app.get("/api/recommendations/analytics", response_model=RecommendationAnalyticsResponse)
def get_recommendation_analytics(db: Session = Depends(get_db)):
    """Return analytics on recommendation statuses and average decision resolution time."""
    total_count    = db.query(Recommendation).count()
    pending_count  = db.query(Recommendation).filter(Recommendation.status == "pending").count()
    approved_count = db.query(Recommendation).filter(Recommendation.status == "approved").count()
    modified_count = db.query(Recommendation).filter(Recommendation.status == "modified").count()
    rejected_count = db.query(Recommendation).filter(Recommendation.status == "rejected").count()

    actions = db.query(HumanAction).all()
    durations = []
    for act in actions:
        if act.recommendation and act.recommendation.created_at:
            delta = (act.timestamp - act.recommendation.created_at).total_seconds()
            if delta >= 0:
                durations.append(delta)

    avg_time = sum(durations) / len(durations) if durations else 0.0

    return {
        "total_count":                  total_count,
        "pending_count":                pending_count,
        "approved_count":               approved_count,
        "modified_count":               modified_count,
        "rejected_count":               rejected_count,
        "avg_time_to_decision_seconds": round(avg_time, 2),
    }


@app.get("/api/recommendations/{id}", response_model=RecommendationResponse)
def get_recommendation_by_id(id: int, db: Session = Depends(get_db)):
    """Retrieve a single stored recommendation by ID."""
    rec = db.query(Recommendation).filter(Recommendation.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation ID {id} not found")
    return rec


@app.post("/api/recommendations/{id}/approve", response_model=RecommendationResponse)
def approve_recommendation(id: int, db: Session = Depends(get_db)):
    """Approve a pending recommendation."""
    rec = db.query(Recommendation).filter(Recommendation.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation ID {id} not found")
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Recommendation has already been acted upon (status: {rec.status})")

    rec.status = "approved"
    db.add(HumanAction(recommendation_id=rec.id, action="approve", original_message=rec.suggested_customer_message))
    db.commit()
    db.refresh(rec)
    return rec


@app.post("/api/recommendations/{id}/modify", response_model=RecommendationResponse)
def modify_recommendation(id: int, req: ModifyRecommendationRequest, db: Session = Depends(get_db)):
    """Modify customer message or decision note on a pending recommendation."""
    rec = db.query(Recommendation).filter(Recommendation.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation ID {id} not found")
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Recommendation has already been acted upon (status: {rec.status})")

    rec.status = "modified"
    rec.modified_message = req.modified_message
    db.add(HumanAction(recommendation_id=rec.id, action="modify", original_message=rec.suggested_customer_message, modified_message=req.modified_message))
    db.commit()
    db.refresh(rec)
    return rec


@app.post("/api/recommendations/{id}/reject", response_model=RecommendationResponse)
def reject_recommendation(id: int, db: Session = Depends(get_db)):
    """Reject a pending recommendation."""
    rec = db.query(Recommendation).filter(Recommendation.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation ID {id} not found")
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Recommendation has already been acted upon (status: {rec.status})")

    rec.status = "rejected"
    db.add(HumanAction(recommendation_id=rec.id, action="reject", original_message=rec.suggested_customer_message))
    db.commit()
    db.refresh(rec)
    return rec
