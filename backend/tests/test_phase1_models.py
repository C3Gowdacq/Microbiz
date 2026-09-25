"""
backend/tests/test_phase1_models.py

Phase 1 validation tests.
Tests:
  - All new models can be created and queried
  - BusinessSettings has new threshold columns with correct defaults
  - Recommendation has entity_type/entity_id/module columns
  - Supplier CRUD
  - PurchaseOrder + PurchaseOrderItem creation and relationships
  - InventoryEvent creation
  - AgentRun creation
  - AuditLog creation
  - Existing models (Product, Sale, Customer) still work correctly
  - No existing data corrupted
"""

import sys
import os
import pytest
from datetime import datetime, date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import (
    Product, Customer, Sale, Expense, Invoice, Payment,
    BusinessSettings, Recommendation, HumanAction, Forecast,
    Supplier, PurchaseOrder, PurchaseOrderItem,
    InventoryEvent, AgentRun, AuditLog,
)

# Use an in-memory SQLite DB for tests (isolates from microbizai.db)
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def db():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


# ── 1. Test existing models still work ───────────────────────────────────────

def test_product_create(db):
    p = Product(
        id="test-product-1",
        sku="TEST-001",
        name="Test Product",
        selling_price=50.0,
        cost_price=30.0,
        current_stock=100.0,
        reorder_level=20.0,
        safety_stock=10.0,
        lead_time_days=3,
        store_type="a",
        assortment="a",
        promo_active=True,
    )
    db.add(p)
    db.commit()
    fetched = db.query(Product).filter(Product.id == "test-product-1").first()
    assert fetched is not None
    assert fetched.name == "Test Product"
    assert fetched.store_type == "a"
    assert fetched.promo_active is True


def test_customer_create(db):
    c = Customer(id="test-cust-1", name="Ravi Kumar", phone="9876543210")
    db.add(c)
    db.commit()
    fetched = db.query(Customer).filter(Customer.id == "test-cust-1").first()
    assert fetched is not None
    assert fetched.name == "Ravi Kumar"


def test_sale_create_and_product_relationship(db):
    s = Sale(
        product_id="test-product-1",
        quantity=5.0,
        unit_price=50.0,
        total_amount=250.0,
        date=date.today(),
    )
    db.add(s)
    db.commit()
    fetched = db.query(Sale).filter(Sale.product_id == "test-product-1").first()
    assert fetched is not None
    assert fetched.total_amount == 250.0
    assert fetched.product.name == "Test Product"


# ── 2. Test BusinessSettings new columns ─────────────────────────────────────

def test_business_settings_new_columns(db):
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
    fetched = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
    assert fetched is not None
    assert fetched.safety_stock_days == 3
    assert fetched.khata_overdue_days == 30
    assert fetched.expense_anomaly_threshold_pct == 30.0
    assert fetched.autonomous_mode is False


def test_business_settings_autonomous_mode_toggle(db):
    settings = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
    settings.autonomous_mode = True
    db.commit()
    db.refresh(settings)
    assert settings.autonomous_mode is True
    # Toggle back
    settings.autonomous_mode = False
    db.commit()


# ── 3. Test Recommendation entity context columns ────────────────────────────

def test_recommendation_entity_context(db):
    rec = Recommendation(
        primary_action="full_replenishment",
        priority="high",
        reason="Stock below reorder level",
        status="pending",
        module="inventory",
        entity_type="product",
        entity_id="test-product-1",
    )
    db.add(rec)
    db.commit()
    fetched = db.query(Recommendation).filter(Recommendation.entity_id == "test-product-1").first()
    assert fetched is not None
    assert fetched.module == "inventory"
    assert fetched.entity_type == "product"
    assert fetched.entity_id == "test-product-1"
    assert fetched.purchase_order_id is None


# ── 4. Test Supplier model ───────────────────────────────────────────────────

def test_supplier_create(db):
    sup = Supplier(
        name="Sharma Wholesale",
        contact_name="Mohan Sharma",
        phone="9988776655",
        category="Grains",
        is_active=True,
    )
    db.add(sup)
    db.commit()
    fetched = db.query(Supplier).filter(Supplier.name == "Sharma Wholesale").first()
    assert fetched is not None
    assert fetched.category == "Grains"
    assert fetched.is_active is True


# ── 5. Test PurchaseOrder + PurchaseOrderItem ────────────────────────────────

def test_purchase_order_create_with_items(db):
    supplier = db.query(Supplier).first()

    po = PurchaseOrder(
        po_number="PO-2024-00001",
        supplier_id=supplier.id if supplier else None,
        status="DRAFT",
        total_amount=1500.0,
        priority="high",
        reason="Stockout risk detected for Test Product",
    )
    db.add(po)
    db.commit()

    item = PurchaseOrderItem(
        purchase_order_id=po.id,
        product_id="test-product-1",
        quantity=30.0,
        unit_cost=30.0,
        total_cost=900.0,
    )
    db.add(item)
    db.commit()

    fetched_po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == "PO-2024-00001").first()
    assert fetched_po is not None
    assert fetched_po.status == "DRAFT"
    assert len(fetched_po.items) == 1
    assert fetched_po.items[0].quantity == 30.0
    assert fetched_po.items[0].product.name == "Test Product"


def test_purchase_order_status_transitions(db):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == "PO-2024-00001").first()

    # DRAFT -> PENDING_APPROVAL
    po.status = "PENDING_APPROVAL"
    db.commit()
    db.refresh(po)
    assert po.status == "PENDING_APPROVAL"

    # PENDING_APPROVAL -> APPROVED
    po.status = "APPROVED"
    po.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(po)
    assert po.status == "APPROVED"
    assert po.approved_at is not None

    # APPROVED -> ORDERED
    po.status = "ORDERED"
    po.ordered_at = datetime.utcnow()
    db.commit()
    db.refresh(po)
    assert po.status == "ORDERED"

    # ORDERED -> RECEIVED
    po.status = "RECEIVED"
    po.received_at = datetime.utcnow()
    db.commit()
    db.refresh(po)
    assert po.status == "RECEIVED"
    assert po.received_at is not None


# ── 6. Test InventoryEvent ───────────────────────────────────────────────────

def test_inventory_event_create(db):
    event = InventoryEvent(
        product_id="test-product-1",
        event_type="SALE",
        quantity_before=100.0,
        quantity_change=-5.0,
        quantity_after=95.0,
        reference_type="sale",
        reference_id="1",
        notes="Customer sale",
    )
    db.add(event)
    db.commit()

    fetched = db.query(InventoryEvent).filter(InventoryEvent.product_id == "test-product-1").first()
    assert fetched is not None
    assert fetched.event_type == "SALE"
    assert fetched.quantity_before == 100.0
    assert fetched.quantity_change == -5.0
    assert fetched.quantity_after == 95.0


def test_inventory_event_product_relationship(db):
    events = db.query(InventoryEvent).filter(InventoryEvent.product_id == "test-product-1").all()
    assert len(events) >= 1
    assert events[0].product.name == "Test Product"


# ── 7. Test AgentRun ─────────────────────────────────────────────────────────

def test_agent_run_create(db):
    run = AgentRun(
        agent_name="inventory",
        status="completed",
        trigger="sale_event",
        entity_type="product",
        entity_id="test-product-1",
        output_data={"stockout_risk": "HIGH", "stock_gap": 15.0},
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    fetched = db.query(AgentRun).filter(AgentRun.agent_name == "inventory").first()
    assert fetched is not None
    assert fetched.status == "completed"
    assert fetched.output_data["stockout_risk"] == "HIGH"


def test_agent_run_failure(db):
    run = AgentRun(
        agent_name="replenishment",
        status="failed",
        trigger="manual",
        entity_id="test-product-1",
        error="Model file not found",
    )
    db.add(run)
    db.commit()
    fetched = db.query(AgentRun).filter(AgentRun.agent_name == "replenishment").first()
    assert fetched.status == "failed"
    assert "not found" in fetched.error


# ── 8. Test AuditLog ─────────────────────────────────────────────────────────

def test_audit_log_create(db):
    log = AuditLog(
        actor_type="SYSTEM",
        actor_id="inventory_agent",
        action="STOCK_DECREASED",
        entity="products",
        entity_id="test-product-1",
        old_value={"current_stock": 100.0},
        new_value={"current_stock": 95.0},
        reason="Customer sale of 5 units",
    )
    db.add(log)
    db.commit()

    fetched = db.query(AuditLog).filter(AuditLog.action == "STOCK_DECREASED").first()
    assert fetched is not None
    assert fetched.actor_type == "SYSTEM"
    assert fetched.old_value["current_stock"] == 100.0
    assert fetched.new_value["current_stock"] == 95.0


# ── 9. Test Recommendation <-> PurchaseOrder link ────────────────────────────

def test_recommendation_purchase_order_link(db):
    rec = db.query(Recommendation).filter(Recommendation.entity_id == "test-product-1").first()
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == "PO-2024-00001").first()

    rec.purchase_order_id = po.id
    db.commit()
    db.refresh(rec)

    assert rec.purchase_order_id == po.id
    assert rec.purchase_order.po_number == "PO-2024-00001"


# ── 10. Verify existing functionality not broken ─────────────────────────────

def test_existing_forecast_model(db):
    f = Forecast(
        product_id="test-product-1",
        forecast_date=date.today(),
        horizon_days=7,
        predicted_sales=35.0,
        model_used="random_forest",
        status="active",
    )
    db.add(f)
    db.commit()
    fetched = db.query(Forecast).filter(Forecast.product_id == "test-product-1").first()
    assert fetched is not None
    assert fetched.predicted_sales == 35.0
    assert fetched.product.name == "Test Product"


def test_product_has_inventory_events_relationship(db):
    product = db.query(Product).filter(Product.id == "test-product-1").first()
    assert hasattr(product, "inventory_events")
    assert len(product.inventory_events) >= 1


def test_product_has_po_items_relationship(db):
    product = db.query(Product).filter(Product.id == "test-product-1").first()
    assert hasattr(product, "po_items")
    assert len(product.po_items) >= 1
