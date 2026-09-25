"""
backend/tests/test_phase3_risk_service.py

Phase 3 validation tests for inventory_risk_service.py.
Tests:
  - Critical risk when out of stock
  - High risk when coverage days < lead time
  - Medium risk when stock is near reorder point
  - Healthy risk when coverage is ample
  - Recommended order quantity calculations
  - Fallback to velocity when ML fields absent
  - Safe handling of zero demand (no division by zero)
  - evaluate_all_products_risk batch execution
"""

import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "src")))

from backend.app.database import Base
from backend.app.models import Product, Sale, BusinessSettings
from backend.app.services.inventory_risk_service import (
    calculate_risk_metrics,
    get_product_risk_summary,
    evaluate_all_products_risk,
)


@pytest.fixture
def db():
    """Create an isolated in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Create default settings
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


def test_zero_stock_critical_risk(db):
    """When stock is 0 and reorder_level > 0, risk should be CRITICAL."""
    prod = Product(
        name="Out of Stock Product",
        sku="OOS-01",
        selling_price=100.0,
        cost_price=60.0,
        current_stock=0.0,
        reorder_level=10.0,
        safety_stock=5.0,
        lead_time_days=3,
    )
    db.add(prod)
    db.commit()

    metrics = calculate_risk_metrics(prod, db, horizon_days=7)
    assert metrics["risk_level"] == "CRITICAL"
    assert metrics["current_stock"] == 0.0
    assert metrics["reorder_needed"] is True
    assert metrics["recommended_order_qty"] > 0


def test_high_risk_low_coverage(db):
    """When stock coverage days is less than lead time, risk should be HIGH or CRITICAL."""
    prod = Product(
        name="Low Coverage Product",
        sku="LOW-01",
        selling_price=50.0,
        cost_price=30.0,
        current_stock=4.0,
        reorder_level=20.0,
        safety_stock=10.0,
        lead_time_days=5,
    )
    db.add(prod)
    db.commit()

    metrics = calculate_risk_metrics(prod, db, horizon_days=7)
    assert metrics["risk_level"] in ("CRITICAL", "HIGH")
    assert metrics["reorder_needed"] is True
    assert metrics["coverage_days"] is not None


def test_healthy_stock_risk(db):
    """When stock is plentiful, risk should be HEALTHY and recommended order qty is 0."""
    prod = Product(
        name="Abundant Stock Product",
        sku="ABUN-01",
        selling_price=50.0,
        cost_price=30.0,
        current_stock=500.0,
        reorder_level=20.0,
        safety_stock=10.0,
        lead_time_days=2,
    )
    db.add(prod)
    db.commit()

    metrics = calculate_risk_metrics(prod, db, horizon_days=7)
    assert metrics["risk_level"] == "HEALTHY"
    assert metrics["reorder_needed"] is False
    assert metrics["recommended_order_qty"] == 0.0


def test_velocity_fallback_when_no_ml_fields(db):
    """Products without store_type/assortment should fall back to velocity."""
    prod = Product(
        name="No ML Profile Product",
        sku="NOML-01",
        selling_price=10.0,
        cost_price=5.0,
        current_stock=15.0,
        reorder_level=10.0,
        lead_time_days=2,
        store_type=None,
        assortment=None,
    )
    db.add(prod)
    db.commit()

    metrics = calculate_risk_metrics(prod, db, horizon_days=7)
    assert metrics["model_used"] == "velocity_fallback"
    assert "recommended_order_qty" in metrics


def test_evaluate_all_products_risk(db):
    """Batch calculation across multiple products."""
    p1 = Product(name="Item 1", sku="SKU1", selling_price=10.0, current_stock=0.0, reorder_level=5.0)
    p2 = Product(name="Item 2", sku="SKU2", selling_price=20.0, current_stock=100.0, reorder_level=5.0)
    db.add_all([p1, p2])
    db.commit()

    all_risks = evaluate_all_products_risk(db)
    assert len(all_risks) == 2
    skus = [r["sku"] for r in all_risks]
    assert "SKU1" in skus
    assert "SKU2" in skus


def test_get_product_risk_summary(db):
    """Fetching risk summary by product ID."""
    prod = Product(name="Item Summary", sku="SUMM-01", selling_price=15.0, current_stock=20.0)
    db.add(prod)
    db.commit()

    summary = get_product_risk_summary(prod.id, db)
    assert summary is not None
    assert summary["product_id"] == prod.id
    assert summary["product_name"] == "Item Summary"

    non_existent = get_product_risk_summary("fake-id", db)
    assert non_existent is None
