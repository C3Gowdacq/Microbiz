"""
routers/settings.py -- Business Settings and Autonomous Mode endpoints.

Endpoints:
  GET   /api/settings                   get current settings (auto-creates defaults if missing)
  PUT   /api/settings                   update operational thresholds and settings
  POST  /api/settings/toggle-autonomous toggle autonomous agent mode on/off
  GET   /api/automation/status          system-wide automation status and recent runs
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import (
    BusinessSettings,
    AuditLog,
    AgentRun,
    Recommendation,
    Product,
    Customer,
    Invoice,
    PurchaseOrder,
    Expense,
    Sale,
)
from backend.app.schemas import BusinessSettingsResponse, BusinessSettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["Settings"])


def _get_or_create_settings(db: Session) -> BusinessSettings:
    """Return the singleton settings row, creating it with defaults if absent."""
    settings = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
    if not settings:
        settings = BusinessSettings(
            id=1,
            min_cash_reserve=25000.0,
            currency="INR",
            safety_stock_days=3,
            review_period_days=7,
            khata_overdue_days=30,
            expense_anomaly_threshold_pct=30.0,
            high_risk_multiplier=1.0,
            medium_risk_multiplier=1.5,
            autonomous_mode=False,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", response_model=BusinessSettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """Return current business settings."""
    return _get_or_create_settings(db)


@router.put("", response_model=BusinessSettingsResponse)
def update_settings(req: BusinessSettingsUpdate, db: Session = Depends(get_db)):
    """Update business settings and operational thresholds."""
    settings = _get_or_create_settings(db)

    if req.min_cash_reserve is not None:
        settings.min_cash_reserve = req.min_cash_reserve
    if req.currency is not None:
        settings.currency = req.currency.upper()
    if req.safety_stock_days is not None:
        settings.safety_stock_days = req.safety_stock_days
    if req.review_period_days is not None:
        settings.review_period_days = req.review_period_days
    if req.khata_overdue_days is not None:
        settings.khata_overdue_days = req.khata_overdue_days
    if req.expense_anomaly_threshold_pct is not None:
        settings.expense_anomaly_threshold_pct = req.expense_anomaly_threshold_pct
    if req.high_risk_multiplier is not None:
        settings.high_risk_multiplier = req.high_risk_multiplier
    if req.medium_risk_multiplier is not None:
        settings.medium_risk_multiplier = req.medium_risk_multiplier
    if req.autonomous_mode is not None:
        old_mode = settings.autonomous_mode
        settings.autonomous_mode = req.autonomous_mode
        if old_mode != req.autonomous_mode:
            audit = AuditLog(
                actor_type="MERCHANT",
                action="AUTONOMOUS_MODE_CHANGED",
                entity="business_settings",
                entity_id="1",
                old_value={"autonomous_mode": old_mode},
                new_value={"autonomous_mode": req.autonomous_mode},
                reason=f"Autonomous mode changed to {req.autonomous_mode}",
                timestamp=datetime.now(timezone.utc),
            )
            db.add(audit)

    db.commit()
    db.refresh(settings)
    return settings


@router.post("/toggle-autonomous", response_model=BusinessSettingsResponse)
def toggle_autonomous_mode(db: Session = Depends(get_db)):
    """Toggle autonomous mode on or off."""
    settings = _get_or_create_settings(db)
    old_mode = settings.autonomous_mode
    new_mode = not old_mode
    settings.autonomous_mode = new_mode

    audit = AuditLog(
        actor_type="MERCHANT",
        action="AUTONOMOUS_MODE_TOGGLED",
        entity="business_settings",
        entity_id="1",
        old_value={"autonomous_mode": old_mode},
        new_value={"autonomous_mode": new_mode},
        reason=f"Autonomous mode toggled from {old_mode} to {new_mode}",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit)

    db.commit()
    db.refresh(settings)
    return settings


# ── Global Automation Router (/api/automation) ───────────────────────────────

automation_router = APIRouter(prefix="/api/automation", tags=["Automation"])


@automation_router.get("/status")
def get_automation_status(db: Session = Depends(get_db)):
    """Return high-level autonomous operations overview, agent health, and recent runs."""
    settings = _get_or_create_settings(db)

    recent_runs = (
        db.query(AgentRun)
        .order_by(AgentRun.started_at.desc())
        .limit(10)
        .all()
    )

    pending_recs = db.query(Recommendation).filter(Recommendation.status == "pending").count()
    audit_count = db.query(AuditLog).count()

    # Lookups for human-readable entity labels
    product_map = {p.id: p.name for p in db.query(Product).all()}
    customer_map = {c.id: c.name for c in db.query(Customer).all()}

    runs_summary = []
    for r in recent_runs:
        label = r.entity_id or ""
        if r.entity_type == "product" and r.entity_id in product_map:
            label = product_map[r.entity_id]
        elif r.entity_type == "customer" and r.entity_id in customer_map:
            label = customer_map[r.entity_id]

        runs_summary.append({
            "id": r.id,
            "agent_name": r.agent_name,
            "status": r.status,
            "trigger": r.trigger,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "entity_label": label,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "error": r.error,
        })

    # 1. Real-time Inventory Risks
    critical_products = (
        db.query(Product)
        .filter(Product.current_stock <= Product.reorder_level)
        .order_by(Product.current_stock.asc())
        .limit(6)
        .all()
    )
    critical_inv_list = [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "current_stock": p.current_stock,
            "reorder_level": p.reorder_level,
            "urgency": "CRITICAL" if p.current_stock <= (p.reorder_level * 0.5) else "HIGH",
        }
        for p in critical_products
    ]

    # 2. Overdue Khata Credit
    today = datetime.now(timezone.utc).date()
    overdue_invoices = (
        db.query(Invoice)
        .filter(
            Invoice.status.in_(["unpaid", "partially_paid"]),
            Invoice.due_date < today,
        )
        .all()
    )
    overdue_total = sum(max(0.0, inv.invoice_amount - inv.amount_paid) for inv in overdue_invoices)
    overdue_list = [
        {
            "customer_name": customer_map.get(inv.customer_id, "Customer"),
            "amount": round(inv.invoice_amount - inv.amount_paid, 2),
            "days_overdue": (today - inv.due_date).days,
        }
        for inv in overdue_invoices[:4]
    ]

    # 3. Replenishment PO summary
    pending_pos = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.status.in_(["draft", "pending", "ordered"]))
        .all()
    )
    pending_pos_value = sum(po.total_amount for po in pending_pos)

    # 4. Solvency summary
    total_sales = float(db.query(func.coalesce(func.sum(Sale.total_amount), 0.0)).scalar())
    total_expenses = float(db.query(func.coalesce(func.sum(Expense.current_period_amount), 0.0)).scalar())
    current_cash = round(total_sales - total_expenses, 2)

    return {
        "autonomous_mode": settings.autonomous_mode,
        "operational_thresholds": {
            "safety_stock_days": settings.safety_stock_days,
            "review_period_days": settings.review_period_days,
            "khata_overdue_days": settings.khata_overdue_days,
            "expense_anomaly_threshold_pct": settings.expense_anomaly_threshold_pct,
            "high_risk_multiplier": settings.high_risk_multiplier,
            "medium_risk_multiplier": settings.medium_risk_multiplier,
        },
        "agents": [
            {"name": "inventory", "type": "reactive_on_sale", "status": "active"},
            {"name": "replenishment", "type": "hitl_recommendation", "status": "active"},
            {"name": "khata", "type": "credit_aging", "status": "active"},
            {"name": "expense", "type": "anomaly_spike", "status": "active"},
            {"name": "cashflow", "type": "solvency_guard", "status": "active"},
        ],
        "pending_recommendations_count": pending_recs,
        "audit_logs_count": audit_count,
        "recent_runs": runs_summary,
        "critical_inventory": critical_inv_list,
        "khata_summary": {
            "total_overdue": round(overdue_total, 2),
            "overdue_count": len(overdue_invoices),
            "top_overdue": overdue_list,
        },
        "replenishment_summary": {
            "pending_po_count": len(pending_pos),
            "total_po_value": round(pending_pos_value, 2),
        },
        "solvency_summary": {
            "current_cash": current_cash,
            "min_reserve": settings.min_cash_reserve,
            "status": "SOLVENT" if current_cash >= settings.min_cash_reserve else "LOW_RESERVE",
        },
    }
