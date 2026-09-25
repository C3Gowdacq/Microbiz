"""
backend/tests/test_phase4_phase5.py

Validation tests for:
  - Phase 4: Real-time Sale -> Inventory -> Risk Pipeline (enriched SaleResponse)
  - Phase 5: Replenishment Engine with active recommendation deduplication
"""

import os
import sys
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "src")))

from backend.app.database import Base
from backend.app.models import Product, Sale, BusinessSettings, Recommendation, InventoryEvent
from backend.app.schemas import SaleCreate
from backend.app.routers.sales import record_sale
from backend.app.services.replenishment_service import (
    evaluate_and_trigger_replenishment,
    get_active_replenishment_recommendation,
)


@pytest.fixture
def db():
    """Create isolated in-memory DB for each test."""
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


def test_sale_enriched_with_inventory_risk(db):
    """Phase 4: Sale response must include real-time inventory risk metrics."""
    prod = Product(
        name="Atta 10kg",
        sku="ATTA-10",
        selling_price=450.0,
        cost_price=380.0,
        current_stock=20.0,
        reorder_level=15.0,
        safety_stock=5.0,
        lead_time_days=2,
    )
    db.add(prod)
    db.commit()

    req = SaleCreate(
        product_id=prod.id,
        quantity=5.0,
        unit_price=450.0,
        sale_date=date.today(),
    )

    sale = record_sale(req=req, db=db)
    assert sale.id is not None
    assert hasattr(sale, "inventory_risk")
    assert sale.inventory_risk is not None

    risk = sale.inventory_risk
    assert risk["product_id"] == prod.id
    assert risk["current_stock"] == 15.0
    assert "risk_level" in risk
    assert "recommended_order_qty" in risk


def test_autonomous_mode_triggers_replenishment_on_critical_sale(db):
    """Phase 4 & 5: When autonomous mode is ON and stock drops to critical, create Recommendation."""
    # Enable autonomous mode
    settings = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
    settings.autonomous_mode = True
    db.commit()

    prod = Product(
        name="Sunflower Oil 1L",
        sku="OIL-01",
        selling_price=160.0,
        cost_price=130.0,
        current_stock=5.0,
        reorder_level=10.0,
        safety_stock=5.0,
        lead_time_days=3,
    )
    db.add(prod)
    db.commit()

    # Sell 5 units -> stock drops to 0 (CRITICAL)
    req = SaleCreate(
        product_id=prod.id,
        quantity=5.0,
        unit_price=160.0,
        sale_date=date.today(),
    )
    sale = record_sale(req=req, db=db)
    assert sale.inventory_risk["risk_level"] == "CRITICAL"

    # Check that a pending Recommendation was automatically created
    rec = get_active_replenishment_recommendation(prod.id, db)
    assert rec is not None
    assert rec.status == "pending"
    assert rec.module == "inventory"
    assert rec.entity_id == prod.id
    assert rec.priority == "critical"
    assert rec.primary_action == "urgent_replenishment"


def test_deduplication_prevents_multiple_recommendations(db):
    """Phase 5: 4 consecutive sales on low-stock item must produce ONLY ONE active recommendation."""
    settings = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
    settings.autonomous_mode = True
    db.commit()

    prod = Product(
        name="Sugar 1kg",
        sku="SUGAR-01",
        selling_price=45.0,
        cost_price=35.0,
        current_stock=10.0,
        reorder_level=15.0,
        safety_stock=5.0,
        lead_time_days=2,
    )
    db.add(prod)
    db.commit()

    # 4 sales in a row
    for _ in range(4):
        req = SaleCreate(
            product_id=prod.id,
            quantity=1.0,
            unit_price=45.0,
            sale_date=date.today(),
        )
        record_sale(req=req, db=db)

    # Count total active recommendations for this product
    active_recs = (
        db.query(Recommendation)
        .filter(
            Recommendation.module == "inventory",
            Recommendation.entity_id == prod.id,
            Recommendation.status == "pending",
        )
        .all()
    )

    assert len(active_recs) == 1, f"Expected exactly 1 pending recommendation, got {len(active_recs)}"


def test_manual_mode_does_not_auto_create_recommendation(db):
    """When autonomous mode is OFF, low stock does NOT trigger auto-recommendation."""
    settings = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
    assert settings.autonomous_mode is False

    prod = Product(
        name="Salt 1kg",
        sku="SALT-01",
        selling_price=20.0,
        cost_price=12.0,
        current_stock=2.0,
        reorder_level=10.0,
        safety_stock=5.0,
        lead_time_days=2,
    )
    db.add(prod)
    db.commit()

    req = SaleCreate(
        product_id=prod.id,
        quantity=2.0,
        unit_price=20.0,
        sale_date=date.today(),
    )
    record_sale(req=req, db=db)

    rec = get_active_replenishment_recommendation(prod.id, db)
    assert rec is None, "In manual mode, recommendations should not be created automatically on sales"
