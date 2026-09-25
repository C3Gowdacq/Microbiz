"""
backend/app/services/agent_orchestrator.py

Phase 7: Production-Grade Agent Orchestration.

Features:
  - Structured AgentResult dataclass
  - Isolated execution: failures in one agent do NOT crash other agents or transactions
  - Records persistent AgentRun entries with started_at, completed_at, status, input/output snapshots
  - Individual entity runners:
      * run_inventory_agent(product_id, db)
      * run_khata_agent(customer_id, db)
      * run_expense_agent(category, db)
      * run_cashflow_agent(db)
  - Comprehensive run_all_agents(db)
"""

import os
import sys
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Ensure paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "src")))

from backend.app.models import (
    Product,
    Customer,
    Expense,
    AgentRun,
    Recommendation,
    BusinessSettings,
)
from backend.app.services.inventory_risk_service import calculate_risk_metrics
from backend.app.services.replenishment_service import evaluate_and_trigger_replenishment
from backend.app.services.agent_data_builder import (
    build_credit_input,
    build_expense_input,
    build_cashflow_input,
)
from agents.credit_agent import analyze_customer_credit
from agents.expense_agent import analyze_expense_trend
from agents.cashflow_agent import calculate_cashflow_risk


@dataclass
class AgentResult:
    agent_name:        str
    status:            str                   # 'completed' | 'failed' | 'skipped'
    entity_type:       Optional[str] = None  # 'product' | 'customer' | 'expense_category' | 'business'
    entity_id:         Optional[str] = None
    recommendation_id: Optional[int] = None
    summary:           str = ""
    details:           Dict[str, Any] = None
    error:             Optional[str] = None
    duration_ms:       float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d["details"] is None:
            d["details"] = {}
        return d


def _record_agent_run_start(
    agent_name: str,
    entity_type: Optional[str],
    entity_id: Optional[str],
    trigger: str,
    input_data: Optional[Dict[str, Any]],
    db: Session,
) -> AgentRun:
    """Record the beginning of an agent execution."""
    run = AgentRun(
        agent_name=agent_name,
        started_at=datetime.now(timezone.utc),
        status="running",
        trigger=trigger,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        input_data=input_data,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _record_agent_run_end(
    run: AgentRun,
    status: str,
    output_data: Optional[Dict[str, Any]],
    error: Optional[str],
    db: Session,
):
    """Update AgentRun with final outcome."""
    run.status = status
    run.completed_at = datetime.now(timezone.utc)
    run.output_data = output_data
    run.error = error
    db.commit()


# ── 1. Inventory Agent Runner ─────────────────────────────────────────────────

def run_inventory_agent(
    product_id: str,
    db: Session,
    trigger: str = "manual",
) -> AgentResult:
    """Run inventory risk evaluation & trigger replenishment recommendation if needed."""
    start_t = time.perf_counter()
    run = _record_agent_run_start("inventory", "product", product_id, trigger, {"product_id": product_id}, db)

    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            _record_agent_run_end(run, "failed", None, f"Product {product_id} not found", db)
            return AgentResult(
                agent_name="inventory",
                status="failed",
                entity_type="product",
                entity_id=product_id,
                error=f"Product {product_id} not found",
                duration_ms=round((time.perf_counter() - start_t) * 1000, 2),
            )

        metrics = calculate_risk_metrics(product, db)
        rec, created = evaluate_and_trigger_replenishment(product.id, db)

        summary = f"Risk: {metrics['risk_level']}, stock: {metrics['current_stock']}, coverage: {metrics['coverage_days']}d"
        if rec:
            summary += f" (Recommendation #{rec.id} {'created' if created else 'already active'})"

        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        output_data = {
            "metrics": metrics,
            "recommendation_id": rec.id if rec else None,
            "recommendation_created": created,
        }

        _record_agent_run_end(run, "completed", output_data, None, db)

        return AgentResult(
            agent_name="inventory",
            status="completed",
            entity_type="product",
            entity_id=product_id,
            recommendation_id=rec.id if rec else None,
            summary=summary,
            details=output_data,
            duration_ms=duration_ms,
        )

    except Exception as e:
        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        _record_agent_run_end(run, "failed", None, str(e), db)
        return AgentResult(
            agent_name="inventory",
            status="failed",
            entity_type="product",
            entity_id=product_id,
            error=str(e),
            duration_ms=duration_ms,
        )


# ── 2. Khata (Credit) Agent Runner ────────────────────────────────────────────

def run_khata_agent(
    customer_id: str,
    db: Session,
    trigger: str = "manual",
) -> AgentResult:
    """Analyze customer credit and outstanding dues."""
    start_t = time.perf_counter()
    run = _record_agent_run_start("khata", "customer", customer_id, trigger, {"customer_id": customer_id}, db)

    try:
        cust = db.query(Customer).filter(Customer.id == customer_id).first()
        if not cust:
            _record_agent_run_end(run, "failed", None, f"Customer {customer_id} not found", db)
            return AgentResult(
                agent_name="khata",
                status="failed",
                entity_type="customer",
                entity_id=customer_id,
                error=f"Customer {customer_id} not found",
                duration_ms=round((time.perf_counter() - start_t) * 1000, 2),
            )

        inp = build_credit_input(customer_id, db)
        if not inp:
            # Customer has no unpaid invoices - healthy!
            duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
            summary = f"Customer '{cust.name}' has no unpaid invoices (Healthy)"
            _record_agent_run_end(run, "completed", {"status": "healthy", "outstanding_amount": 0.0}, None, db)
            return AgentResult(
                agent_name="khata",
                status="completed",
                entity_type="customer",
                entity_id=customer_id,
                summary=summary,
                details={"outstanding_amount": 0.0, "customer_risk": "NONE"},
                duration_ms=duration_ms,
            )

        analysis = analyze_customer_credit(
            customer_id=inp["customer_id"],
            invoice_amount=inp["invoice_amount"],
            amount_paid=inp["amount_paid"],
            due_date=inp["due_date"],
            today=inp.get("today"),
        )

        rec_id = None
        risk = analysis.get("customer_risk", "NONE")
        outstanding = analysis.get("outstanding_amount", 0.0)
        if risk in ("HIGH", "MEDIUM") and outstanding > 0:
            # Check dedup for customer
            existing = (
                db.query(Recommendation)
                .filter(
                    Recommendation.module == "khata",
                    Recommendation.entity_type == "customer",
                    Recommendation.entity_id == customer_id,
                    Recommendation.status.in_(["pending", "approved"]),
                )
                .first()
            )
            if existing:
                rec_id = existing.id
            else:
                action = "send_payment_reminder" if risk == "MEDIUM" else "suspend_credit_and_followup"
                rec = Recommendation(
                    module="khata",
                    entity_type="customer",
                    entity_id=customer_id,
                    primary_action=action,
                    priority=risk.lower(),
                    reason=(
                        f"Customer '{cust.name}' has ₹{outstanding:,.2f} "
                        f"outstanding ({analysis.get('days_overdue', 0)} days overdue, risk: {risk})."
                    ),
                    suggested_customer_message=f"Dear {cust.name}, this is a gentle reminder regarding your outstanding payment of ₹{outstanding:,.2f}. Kindly clear the dues at your earliest convenience.",
                    status="pending",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)
                rec_id = rec.id

        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        summary = f"Credit risk {risk}: ₹{outstanding:,.2f} balance"
        _record_agent_run_end(run, "completed", analysis, None, db)

        return AgentResult(
            agent_name="khata",
            status="completed",
            entity_type="customer",
            entity_id=customer_id,
            recommendation_id=rec_id,
            summary=summary,
            details=analysis,
            duration_ms=duration_ms,
        )

    except Exception as e:
        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        _record_agent_run_end(run, "failed", None, str(e), db)
        return AgentResult(
            agent_name="khata",
            status="failed",
            entity_type="customer",
            entity_id=customer_id,
            error=str(e),
            duration_ms=duration_ms,
        )


# ── 3. Expense Agent Runner ───────────────────────────────────────────────────

def run_expense_agent(
    category: str,
    db: Session,
    trigger: str = "manual",
) -> AgentResult:
    """Analyze expense spikes and anomalies for a category."""
    start_t = time.perf_counter()
    run = _record_agent_run_start("expense", "expense_category", category, trigger, {"category": category}, db)

    try:
        inp = build_expense_input(category, db)
        result = analyze_expense_trend(
            category=category,
            current_period_amount=inp["current_period_amount"],
            prior_period_amount=inp["prior_period_amount"],
        )

        rec_id = None
        risk = result.get("risk", "LOW")
        increase_pct = result.get("increase_pct")
        if risk in ("HIGH", "MEDIUM") and increase_pct is not None and increase_pct > 10.0:
            existing = (
                db.query(Recommendation)
                .filter(
                    Recommendation.module == "expense",
                    Recommendation.entity_type == "expense_category",
                    Recommendation.entity_id == category,
                    Recommendation.status.in_(["pending", "approved"]),
                )
                .first()
            )
            if existing:
                rec_id = existing.id
            else:
                rec = Recommendation(
                    module="expense",
                    entity_type="expense_category",
                    entity_id=category,
                    primary_action="audit_expense_category",
                    priority="high" if risk == "HIGH" else "medium",
                    reason=f"Expense spike of +{increase_pct:.1f}% detected in category '{category}'. Prior: ₹{inp['prior_period_amount']:,.2f}, Current: ₹{inp['current_period_amount']:,.2f}",
                    status="pending",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)
                rec_id = rec.id

        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        pct_str = f"+{increase_pct:.1f}%" if increase_pct is not None else "new"
        summary = f"Expense trend: {result.get('trend')} ({pct_str}, risk: {risk})"
        _record_agent_run_end(run, "completed", result, None, db)

        return AgentResult(
            agent_name="expense",
            status="completed",
            entity_type="expense_category",
            entity_id=category,
            recommendation_id=rec_id,
            summary=summary,
            details=result,
            duration_ms=duration_ms,
        )

    except Exception as e:
        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        _record_agent_run_end(run, "failed", None, str(e), db)
        return AgentResult(
            agent_name="expense",
            status="failed",
            entity_type="expense_category",
            entity_id=category,
            error=str(e),
            duration_ms=duration_ms,
        )


# ── 4. Cashflow Agent Runner ──────────────────────────────────────────────────

def run_cashflow_agent(
    db: Session,
    trigger: str = "manual",
) -> AgentResult:
    """Analyze shop-wide cashflow and solvency risk."""
    start_t = time.perf_counter()
    run = _record_agent_run_start("cashflow", "business", "singleton", trigger, {}, db)

    try:
        inp = build_cashflow_input(db)
        result = calculate_cashflow_risk(
            current_cash=inp["current_cash"],
            expected_sales_revenue=inp["expected_sales_revenue"],
            upcoming_expenses=inp["upcoming_expenses"],
            planned_purchase_cost=inp.get("planned_purchase_cost", 0.0),
            min_cash_reserve=inp["min_cash_reserve"],
        )

        rec_id = None
        risk = result.get("cash_shortage_risk", "LOW")
        projected_bal = result.get("projected_cash_balance", 0.0)
        if risk in ("CRITICAL", "HIGH"):
            existing = (
                db.query(Recommendation)
                .filter(
                    Recommendation.module == "cashflow",
                    Recommendation.status.in_(["pending", "approved"]),
                )
                .first()
            )
            if existing:
                rec_id = existing.id
            else:
                rec = Recommendation(
                    module="cashflow",
                    entity_type="business",
                    entity_id="singleton",
                    primary_action="preserve_liquidity",
                    priority="critical" if risk == "CRITICAL" else "high",
                    reason=f"Cashflow alert ({risk}): Projected cash balance ₹{projected_bal:,.2f} is below minimum cash reserve ₹{inp['min_cash_reserve']:,.2f}.",
                    status="pending",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)
                rec_id = rec.id

        result["cashflow_risk"] = risk
        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        summary = f"Cashflow risk: {risk}, projected balance: ₹{projected_bal:,.2f}"
        _record_agent_run_end(run, "completed", result, None, db)

        return AgentResult(
            agent_name="cashflow",
            status="completed",
            entity_type="business",
            entity_id="singleton",
            recommendation_id=rec_id,
            summary=summary,
            details=result,
            duration_ms=duration_ms,
        )

    except Exception as e:
        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        _record_agent_run_end(run, "failed", None, str(e), db)
        return AgentResult(
            agent_name="cashflow",
            status="failed",
            entity_type="business",
            entity_id="singleton",
            error=str(e),
            duration_ms=duration_ms,
        )


# ── 5. Run All Agents (Full Business Sweep) ───────────────────────────────────

def run_all_agents(
    db: Session,
    trigger: str = "manual",
) -> List[AgentResult]:
    """
    Execute full multi-agent business diagnostic across all entities:
    - All products (inventory risk & replenishment)
    - All customers with outstanding balances (credit risk)
    - All expense categories (expense spikes)
    - Shop-wide cashflow
    Isolated: one failing agent execution does NOT abort the remaining checks.
    """
    results: List[AgentResult] = []

    # 1. Inventory checks for all products
    products = db.query(Product).all()
    for prod in products:
        res = run_inventory_agent(prod.id, db, trigger=trigger)
        results.append(res)

    # 2. Credit checks for all customers
    customers = db.query(Customer).all()
    for cust in customers:
        res = run_khata_agent(cust.id, db, trigger=trigger)
        results.append(res)

    # 3. Expense checks by category
    categories = db.query(Expense.category).distinct().all()
    for (cat,) in categories:
        if cat:
            res = run_expense_agent(cat, db, trigger=trigger)
            results.append(res)

    # 4. Cashflow check
    cashflow_res = run_cashflow_agent(db, trigger=trigger)
    results.append(cashflow_res)

    return results
