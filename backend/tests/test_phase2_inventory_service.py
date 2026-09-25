"""
backend/tests/test_phase2_inventory_service.py

Phase 2 validation tests for inventory_service.py.
Uses function-scoped sessions for test isolation.
"""

import sys
import os
import pytest
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import Product, InventoryEvent, AuditLog
from backend.app.services.inventory_service import (
    decrease_stock, increase_stock, adjust_stock, get_stock, EventType
)

TEST_DB_URL = "sqlite:///:memory:"

# Use function scope so each test has its own fresh DB
@pytest.fixture
def db():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed a test product
    p = Product(
        id="inv-test-001",
        sku="INV-001",
        name="Basmati Rice 5kg",
        selling_price=450.0,
        cost_price=350.0,
        current_stock=100.0,
        reorder_level=20.0,
        safety_stock=10.0,
        lead_time_days=3,
    )
    session.add(p)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


# ── 1. decrease_stock tests ───────────────────────────────────────────────────

def test_decrease_stock_basic(db):
    """decrease_stock should reduce current_stock and create InventoryEvent + AuditLog."""
    event = decrease_stock(
        product_id     = "inv-test-001",
        quantity       = 10.0,
        event_type     = EventType.SALE,
        reference_type = "sale",
        reference_id   = "1",
        notes          = "Test sale of 10 units",
        db             = db,
    )
    # Capture values BEFORE commit flushes them
    qb = event.quantity_before
    qc = event.quantity_change
    qa = event.quantity_after
    db.commit()

    # Check event records the correct before/after
    assert event is not None
    assert event.event_type == EventType.SALE
    assert qb == 100.0
    assert qc == -10.0
    assert qa == 90.0

    # Check product stock updated
    product = db.query(Product).filter(Product.id == "inv-test-001").first()
    assert product.current_stock == 90.0

    # Check AuditLog created
    log = db.query(AuditLog).filter(
        AuditLog.entity_id == "inv-test-001",
        AuditLog.action == "STOCK_DECREASED"
    ).first()
    assert log is not None
    assert log.old_value["current_stock"] == 100.0
    assert log.new_value["current_stock"] == 90.0


def test_decrease_stock_insufficient(db):
    """decrease_stock should raise 422 when requested quantity exceeds current stock."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        decrease_stock(
            product_id = "inv-test-001",
            quantity   = 999.0,
            db         = db,
        )
    db.rollback()
    assert exc_info.value.status_code == 422
    assert "Insufficient stock" in exc_info.value.detail

    # Stock should NOT have changed
    db.expire_all()
    product = db.query(Product).filter(Product.id == "inv-test-001").first()
    assert product.current_stock == 100.0


def test_decrease_stock_zero_quantity(db):
    """decrease_stock should raise 422 for quantity <= 0."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        decrease_stock(product_id="inv-test-001", quantity=0.0, db=db)
    assert exc_info.value.status_code == 422


def test_decrease_stock_negative_quantity(db):
    """decrease_stock should raise 422 for negative quantity."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        decrease_stock(product_id="inv-test-001", quantity=-5.0, db=db)
    assert exc_info.value.status_code == 422


# ── 2. increase_stock tests ───────────────────────────────────────────────────

def test_increase_stock_basic(db):
    """increase_stock should increase current_stock and create InventoryEvent + AuditLog."""
    event = increase_stock(
        product_id     = "inv-test-001",
        quantity       = 50.0,
        event_type     = EventType.PURCHASE_RECEIVED,
        reference_type = "purchase_order",
        reference_id   = "PO-001",
        notes          = "Received 50 bags",
        db             = db,
    )
    qb, qc, qa = event.quantity_before, event.quantity_change, event.quantity_after
    db.commit()

    assert qb == 100.0
    assert qc == 50.0
    assert qa == 150.0

    product = db.query(Product).filter(Product.id == "inv-test-001").first()
    assert product.current_stock == 150.0

    log = db.query(AuditLog).filter(
        AuditLog.entity_id == "inv-test-001",
        AuditLog.action == "STOCK_INCREASED"
    ).first()
    assert log is not None
    assert log.actor_type == "SYSTEM"


def test_increase_stock_zero_quantity(db):
    """increase_stock should raise 422 for quantity <= 0."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        increase_stock(product_id="inv-test-001", quantity=0.0, db=db)
    assert exc_info.value.status_code == 422


# ── 3. adjust_stock tests ─────────────────────────────────────────────────────

def test_adjust_stock_upward(db):
    """adjust_stock should set stock to exact value (upward) and create InventoryEvent."""
    event = adjust_stock(
        product_id   = "inv-test-001",
        new_quantity = 200.0,
        notes        = "Physical count: found 200 bags",
        db           = db,
    )
    qb, qc, qa = event.quantity_before, event.quantity_change, event.quantity_after
    et = event.event_type
    db.commit()

    assert et == EventType.MANUAL_ADJUSTMENT
    assert qb == 100.0
    assert qc == 100.0
    assert qa == 200.0

    product = db.query(Product).filter(Product.id == "inv-test-001").first()
    assert product.current_stock == 200.0


def test_adjust_stock_downward(db):
    """adjust_stock should set stock to exact value (downward) and create InventoryEvent."""
    event = adjust_stock(
        product_id   = "inv-test-001",
        new_quantity = 30.0,
        notes        = "Physical count correction",
        db           = db,
    )
    qb, qc, qa = event.quantity_before, event.quantity_change, event.quantity_after
    db.commit()

    assert qb == 100.0
    assert qc == -70.0
    assert qa == 30.0

    product = db.query(Product).filter(Product.id == "inv-test-001").first()
    assert product.current_stock == 30.0

    log = db.query(AuditLog).filter(
        AuditLog.entity_id == "inv-test-001",
        AuditLog.action == "STOCK_ADJUSTED"
    ).first()
    assert log is not None
    assert log.actor_type == "MERCHANT"


def test_adjust_stock_negative_raises(db):
    """adjust_stock should raise 422 for negative new_quantity."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        adjust_stock(product_id="inv-test-001", new_quantity=-10.0, db=db)
    assert exc_info.value.status_code == 422


# ── 4. get_stock test ─────────────────────────────────────────────────────────

def test_get_stock(db):
    """get_stock should return current product stock."""
    stock = get_stock("inv-test-001", db)
    assert isinstance(stock, float)
    assert stock == 100.0


def test_get_stock_not_found(db):
    """get_stock should raise 404 for unknown product."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        get_stock("does-not-exist", db)
    assert exc_info.value.status_code == 404


# ── 5. Verify InventoryEvent audit trail ─────────────────────────────────────

def test_inventory_event_created_on_sale(db):
    """A decrease_stock call should create exactly one InventoryEvent."""
    decrease_stock(product_id="inv-test-001", quantity=5.0, db=db)
    db.commit()

    events = db.query(InventoryEvent).filter(
        InventoryEvent.product_id == "inv-test-001"
    ).all()
    assert len(events) == 1
    assert events[0].event_type == EventType.SALE


def test_inventory_event_quantity_chain_consistency(db):
    """Every InventoryEvent must satisfy: quantity_after = quantity_before + quantity_change."""
    decrease_stock(product_id="inv-test-001", quantity=5.0, db=db)
    increase_stock(product_id="inv-test-001", quantity=20.0, db=db)
    adjust_stock(product_id="inv-test-001", new_quantity=50.0, db=db)
    db.commit()

    events = db.query(InventoryEvent).filter(
        InventoryEvent.product_id == "inv-test-001"
    ).order_by(InventoryEvent.id).all()

    assert len(events) == 3
    for event in events:
        expected_after = round(event.quantity_before + event.quantity_change, 4)
        assert abs(event.quantity_after - expected_after) < 0.001
