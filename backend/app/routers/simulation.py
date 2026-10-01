"""
routers/simulation.py -- Monte Carlo Solvency Stress-Testing Engine & Kirana Digital Twin.
Simulates 1,000 stochastic cashflow paths over a configurable horizon to calculate
Probability of Insolvency P(Default), Value-at-Risk (VaR 95%), and comparative resiliency
with vs without MicroBiz Autonomous Multi-Agent safeguards.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import numpy as np
from datetime import date

from backend.app.database import get_db
from backend.app.models import Product, Customer, Invoice, Expense, BusinessSettings

router = APIRouter(prefix="/api/simulation", tags=["Monte Carlo Digital Twin"])


class MonteCarloRequest(BaseModel):
    demand_shock_pct: float = Field(0.0, description="Demand shock in % (-50 to +100)")
    supplier_inflation_pct: float = Field(0.0, description="Wholesale cost inflation in % (0 to 30)")
    credit_default_rate_pct: float = Field(10.0, description="Customer khata non-repayment rate in % (0 to 50)")
    horizon_days: int = Field(30, description="Simulation horizon in days (15 to 60)")
    num_simulations: int = Field(1000, description="Number of stochastic Monte Carlo runs (100 to 2000)")
    enable_ai_safeguards: bool = Field(True, description="Enable MicroBiz Multi-Agent Reserve Floor & PO Trimming")


class TrajectoryPoint(BaseModel):
    day: int
    p5: float
    p25: float
    p50: float
    p75: float
    p95: float
    unmanaged_p50: float


class MonteCarloResponse(BaseModel):
    horizon_days: int
    num_simulations: int
    starting_cash: float
    min_cash_reserve: float
    probability_of_insolvency_pct: float
    unmanaged_insolvency_pct: float
    value_at_risk_95: float
    expected_ending_cash: float
    unmanaged_ending_cash: float
    daily_cash_burn_rate: float
    stress_verdict: str
    risk_color: str
    executive_summary: str
    trajectories: List[TrajectoryPoint]


@router.post("/monte-carlo", response_model=MonteCarloResponse)
def run_monte_carlo_simulation(req: MonteCarloRequest, db: Session = Depends(get_db)):
    """
    Run stochastic Monte Carlo simulations to stress-test store liquidity
    under macroeconomic shocks, supplier inflation, and customer khata defaults.
    """
    # 1. Fetch live baseline parameters from database
    settings = db.query(BusinessSettings).first()
    min_cash_reserve = settings.min_cash_reserve if settings else 50000.0

    # Total liquid cash baseline (using default realistic cash balance if store ledger is fresh)
    starting_cash = 563000.0

    # Daily sales baseline from products
    products = db.query(Product).all()
    avg_daily_sales = sum(p.selling_price * 2.2 for p in products) if products else 18500.0

    # Monthly upcoming expenses prorated to daily
    expenses = db.query(Expense).all()
    total_monthly_expenses = sum(e.current_period_amount for e in expenses) if expenses else 38000.0
    daily_fixed_expenses = total_monthly_expenses / 30.0

    # Overdue receivables from customers
    unpaid_invoices = db.query(Invoice).filter(Invoice.status != "paid").all()
    total_receivables = sum(inv.invoice_amount - inv.amount_paid for inv in unpaid_invoices)
    if total_receivables == 0:
        total_receivables = 28500.0

    # 2. Adjust baselines based on scenario shock inputs
    demand_multiplier = 1.0 + (req.demand_shock_pct / 100.0)
    cost_inflation_multiplier = 1.0 + (req.supplier_inflation_pct / 100.0)
    default_rate = req.credit_default_rate_pct / 100.0

    # Daily replenishment purchases (COGS roughly 78% of retail revenue * inflation)
    daily_cogs_base = avg_daily_sales * 0.78 * cost_inflation_multiplier

    # Expected daily collections from receivables over horizon
    daily_collections = (total_receivables * (1.0 - default_rate)) / req.horizon_days

    # Volatility standard deviations (retail Kirana variance)
    sales_volatility = avg_daily_sales * 0.18
    cogs_volatility = daily_cogs_base * 0.14

    # 3. Vectorized Monte Carlo Simulation
    np.random.seed(42)  # Deterministic seed for reproducible evaluation
    N = req.num_simulations
    H = req.horizon_days

    # Paths: shape (N, H + 1)
    cash_paths_ai = np.zeros((N, H + 1))
    cash_paths_unmanaged = np.zeros((N, H + 1))

    cash_paths_ai[:, 0] = starting_cash
    cash_paths_unmanaged[:, 0] = starting_cash

    for t in range(1, H + 1):
        # Stochastic shocks for day t
        shock_sales = np.random.normal(avg_daily_sales * demand_multiplier, sales_volatility, N)
        shock_sales = np.maximum(0, shock_sales)

        shock_cogs = np.random.normal(daily_cogs_base, cogs_volatility, N)
        shock_cogs = np.maximum(0, shock_cogs)

        # UNMANAGED KIRANA:
        # Shopkeeper places orders without reserve protection
        net_flow_unmanaged = shock_sales + daily_collections - shock_cogs - daily_fixed_expenses
        cash_paths_unmanaged[:, t] = cash_paths_unmanaged[:, t - 1] + net_flow_unmanaged

        # MICROBIZ AUTONOMOUS AI SAFEGUARD:
        # Cashflow Guardian caps planned purchase disbursements if cash breaches min_cash_reserve floor
        adjusted_cogs = shock_cogs.copy()
        if req.enable_ai_safeguards:
            projected_pre_cash = cash_paths_ai[:, t - 1] + shock_sales + daily_collections - daily_fixed_expenses
            # If projected cash drops near reserve, AI trims purchase orders to essential stock only (40% reduction)
            reserve_gap = (projected_pre_cash - min_cash_reserve)
            tight_liquidity_mask = reserve_gap < adjusted_cogs
            adjusted_cogs[tight_liquidity_mask] = np.maximum(
                0, adjusted_cogs[tight_liquidity_mask] * 0.60
            )

        net_flow_ai = shock_sales + daily_collections - adjusted_cogs - daily_fixed_expenses
        cash_paths_ai[:, t] = cash_paths_ai[:, t - 1] + net_flow_ai

    # 4. Statistical Metrics Extraction
    final_cash_ai = cash_paths_ai[:, -1]
    final_cash_unmanaged = cash_paths_unmanaged[:, -1]

    # Insolvency probability: Fraction of paths where cash breached zero or reserve
    insolvent_paths_ai = np.sum(np.min(cash_paths_ai, axis=1) <= min_cash_reserve)
    prob_insolvency_ai = round((insolvent_paths_ai / N) * 100.0, 1)

    insolvent_paths_unmanaged = np.sum(np.min(cash_paths_unmanaged, axis=1) <= 0)
    prob_insolvency_unmanaged = round((insolvent_paths_unmanaged / N) * 100.0, 1)

    # 95% Value at Risk (VaR)
    p5_ending_cash = np.percentile(final_cash_ai, 5)
    value_at_risk_95 = max(0.0, round(starting_cash - p5_ending_cash, 2))

    expected_ending_cash = round(float(np.mean(final_cash_ai)), 2)
    unmanaged_ending_cash = round(float(np.mean(final_cash_unmanaged)), 2)
    daily_burn = round(float((starting_cash - expected_ending_cash) / H), 2)

    # Risk Verdict
    if prob_insolvency_ai > 25.0:
        verdict = "CRITICAL SOLVENCY ALERT"
        color = "#e11d48"
    elif prob_insolvency_ai > 10.0:
        verdict = "MODERATE LIQUIDITY VULNERABILITY"
        color = "#f59e0b"
    else:
        verdict = "HIGH CAPITAL RESILIENCY"
        color = "#10b981"

    summary_text = (
        f"Over {H} days under a {req.demand_shock_pct:+.0f}% demand shock and {req.supplier_inflation_pct:.0f}% wholesale inflation, "
        f"MicroBiz multi-agent reserve constraints maintain solvency probability at {100 - prob_insolvency_ai:.1f}%, "
        f"reducing default risk from {prob_insolvency_unmanaged:.1f}% down to {prob_insolvency_ai:.1f}%."
    )

    # 5. Extract trajectory percentiles for UI chart
    trajectories = []
    for d in range(H + 1):
        ai_slice = cash_paths_ai[:, d]
        unman_slice = cash_paths_unmanaged[:, d]
        trajectories.append(
            TrajectoryPoint(
                day=d,
                p5=round(float(np.percentile(ai_slice, 5)), 2),
                p25=round(float(np.percentile(ai_slice, 25)), 2),
                p50=round(float(np.percentile(ai_slice, 50)), 2),
                p75=round(float(np.percentile(ai_slice, 75)), 2),
                p95=round(float(np.percentile(ai_slice, 95)), 2),
                unmanaged_p50=round(float(np.percentile(unman_slice, 50)), 2),
            )
        )

    return MonteCarloResponse(
        horizon_days=H,
        num_simulations=N,
        starting_cash=starting_cash,
        min_cash_reserve=min_cash_reserve,
        probability_of_insolvency_pct=prob_insolvency_ai,
        unmanaged_insolvency_pct=prob_insolvency_unmanaged,
        value_at_risk_95=value_at_risk_95,
        expected_ending_cash=expected_ending_cash,
        unmanaged_ending_cash=unmanaged_ending_cash,
        daily_cash_burn_rate=daily_burn,
        stress_verdict=verdict,
        risk_color=color,
        executive_summary=summary_text,
        trajectories=trajectories,
    )
