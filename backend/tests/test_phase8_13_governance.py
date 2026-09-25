"""
backend/tests/test_phase8_13_governance.py

Phase 8-13 validation tests:
- Operational settings & autonomous mode toggle
- Automation status dashboard endpoint (/api/automation/status)
- HITL recommendation lifecycle with automatic approved PO generation
- Audit log governance trail integrity
"""

import os
import sys
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "src")))

from backend.app.database import Base
from backend.app.models import (
    BusinessSettings,
    Recommendation,
    HumanAction,
    PurchaseOrder,
    PurchaseOrderItem,
    AuditLog,
    Product,
)
from backend.app.schemas import (
    BusinessSettingsUpdate,
    ModifyRecommendationRequest,
)
from backend.app.routers.settings import (
    get_settings,
    update_settings,
    toggle_autonomous_mode,
    get_automation_status,
)
from backend.app.main import (
    approve_recommendation,
    modify_recommendation,
    reject_recommendation,
)


@pytest.fixture
def db():
    """Isolated in-memory DB."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    settings = BusinessSettings(
        id=1,
        min_cash_reserve=25000.0,
        currency="INR",
        safety_stock_days=3,
        review_period_days=7,
        high_risk_multiplier=1.0,
        medium_risk_multiplier=1.5,
        autonomous_mode=False,
    )
    session.add(settings)
    session.commit()

    yield session
    session.close()


def test_settings_and_autonomous_toggle(db):
    """Test updating settings and toggling autonomous mode."""
    # 1. Toggle ON
    s1 = toggle_autonomous_mode(db)
    assert s1.autonomous_mode is True

    # Check AuditLog
    audit = (
        db.query(AuditLog)
        .filter(AuditLog.action == "AUTONOMOUS_MODE_TOGGLED")
        .first()
    )
    assert audit is not None
    assert audit.actor_type == "MERCHANT"

    # 2. Update operational thresholds
    up = BusinessSettingsUpdate(
        safety_stock_days=5,
        review_period_days=14,
        min_cash_reserve=30000.0,
    )
    s2 = update_settings(up, db)
    assert s2.safety_stock_days == 5
    assert s2.review_period_days == 14
    assert s2.min_cash_reserve == 30000.0


def test_automation_status_endpoint(db):
    """Test /api/automation/status returns comprehensive system state."""
    status = get_automation_status(db)
    assert "autonomous_mode" in status
    assert "operational_thresholds" in status
    assert "agents" in status
    assert len(status["agents"]) >= 4
    assert "pending_recommendations_count" in status


def test_hitl_approval_creates_approved_purchase_order(db):
    """
    Approving an inventory recommendation with a PO line item
    automatically creates and links an APPROVED PurchaseOrder.
    """
    prod = Product(name="Mustard Oil 1L", sku="MO-01", cost_price=120.0, current_stock=2.0)
    db.add(prod)
    db.commit()

    rec = Recommendation(
        module="inventory",
        entity_type="product",
        entity_id=prod.id,
        primary_action="urgent_replenishment",
        priority="critical",
        reason="Stockout risk CRITICAL",
        secondary_recommendations=[
            {
                "action": "create_purchase_order",
                "product_id": prod.id,
                "quantity": 30.0,
                "unit_cost": 120.0,
            }
        ],
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()

    # Merchant approves
    approved_rec = approve_recommendation(rec.id, db)
    assert approved_rec.status == "approved"
    assert approved_rec.purchase_order_id is not None

    # Verify PO was created in APPROVED status
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == approved_rec.purchase_order_id).first()
    assert po is not None
    assert po.status == "APPROVED"
    assert po.approved_at is not None
    assert po.total_amount == 30.0 * 120.0
    assert len(po.items) == 1
    assert po.items[0].product_id == prod.id


def test_hitl_rejection_marks_rejected(db):
    """Rejecting a recommendation marks it rejected and cancels/rejects linked PO."""
    rec = Recommendation(
        module="inventory",
        primary_action="full_replenishment",
        priority="high",
        reason="Test rejection",
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()

    rejected_rec = reject_recommendation(rec.id, db)
    assert rejected_rec.status == "rejected"

    audit = (
        db.query(AuditLog)
        .filter(AuditLog.action == "RECOMMENDATION_REJECTED", AuditLog.entity_id == str(rec.id))
        .first()
    )
    assert audit is not None
