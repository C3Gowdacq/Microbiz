"""
backend/tests/test_phase6_purchase_orders.py

Phase 6 validation tests for:
  - Suppliers CRUD
  - Purchase Orders lifecycle (create, approval, ordering)
  - PO receiving with automated stock increment and immutable InventoryEvent
"""

import os
import sys
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "src")))

from backend.app.database import Base
from backend.app.models import Product, Supplier, PurchaseOrder, PurchaseOrderItem, InventoryEvent, AuditLog
from backend.app.schemas import (
    SupplierCreate,
    SupplierUpdate,
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderStatusUpdate,
)
from backend.app.routers.suppliers import (
    create_supplier,
    list_suppliers,
    get_supplier,
    update_supplier,
    delete_supplier,
)
from backend.app.routers.purchase_orders import (
    create_purchase_order,
    list_purchase_orders,
    get_purchase_order,
    update_po_status,
    receive_purchase_order,
)


@pytest.fixture
def db():
    """Isolated in-memory DB for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    yield session
    session.close()


def test_supplier_crud(db):
    """Test full CRUD lifecycle for suppliers."""
    # Create
    req = SupplierCreate(
        name="Test Vendor Hub",
        contact_name="Vikas Roy",
        phone="+91 99999 88888",
        email="vikas@testvendor.in",
        category="Grains",
    )
    supplier = create_supplier(req, db)
    assert supplier.id is not None
    assert supplier.name == "Test Vendor Hub"
    assert supplier.is_active is True

    # Get
    s_get = get_supplier(supplier.id, db)
    assert s_get.id == supplier.id

    # Update
    up_req = SupplierUpdate(phone="+91 99999 77777")
    s_updated = update_supplier(supplier.id, up_req, db)
    assert s_updated.phone == "+91 99999 77777"

    # Soft Delete
    del_res = delete_supplier(supplier.id, db)
    assert "deactivated" in del_res["message"]
    s_deactivated = get_supplier(supplier.id, db)
    assert s_deactivated.is_active is False


def test_create_purchase_order_with_items(db):
    """Test PO creation with line items, total calculation, and audit entry."""
    supplier = Supplier(name="PO Supplier", is_active=True)
    prod1 = Product(name="Item A", sku="ITM-A", cost_price=50.0, current_stock=5.0)
    prod2 = Product(name="Item B", sku="ITM-B", cost_price=100.0, current_stock=2.0)
    db.add_all([supplier, prod1, prod2])
    db.commit()

    req = PurchaseOrderCreate(
        supplier_id=supplier.id,
        priority="high",
        reason="Stockout replenishment",
        items=[
            PurchaseOrderItemCreate(product_id=prod1.id, quantity=20.0, unit_cost=50.0),
            PurchaseOrderItemCreate(product_id=prod2.id, quantity=10.0, unit_cost=100.0),
        ],
    )
    po_resp = create_purchase_order(req, db)
    assert po_resp["id"] is not None
    assert po_resp["status"] == "PENDING_APPROVAL"
    assert po_resp["total_amount"] == (20.0 * 50.0) + (10.0 * 100.0)
    assert len(po_resp["items"]) == 2
    assert po_resp["supplier_name"] == "PO Supplier"

    # Check AuditLog
    audit = db.query(AuditLog).filter(AuditLog.entity_id == str(po_resp["id"])).first()
    assert audit is not None
    assert audit.action == "PURCHASE_ORDER_CREATED"


def test_po_status_transitions(db):
    """Test approving and ordering a PO."""
    prod = Product(name="Single Item", sku="SI-01", cost_price=40.0, current_stock=10.0)
    db.add(prod)
    db.commit()

    po_resp = create_purchase_order(
        PurchaseOrderCreate(
            priority="medium",
            items=[PurchaseOrderItemCreate(product_id=prod.id, quantity=15.0, unit_cost=40.0)],
        ),
        db,
    )
    po_id = po_resp["id"]

    # Approve
    approved = update_po_status(po_id, PurchaseOrderStatusUpdate(status="APPROVED"), db)
    assert approved["status"] == "APPROVED"
    assert approved["approved_at"] is not None

    # Order
    ordered = update_po_status(po_id, PurchaseOrderStatusUpdate(status="ORDERED"), db)
    assert ordered["status"] == "ORDERED"
    assert ordered["ordered_at"] is not None


def test_receive_purchase_order_increments_stock_and_creates_events(db):
    """
    Test receiving a PO:
    - Increments stock on each product
    - Creates immutable InventoryEvent (PURCHASE_RECEIVED) with exact before/after
    - Marks status RECEIVED
    """
    prod = Product(name="Rice Bag 25kg", sku="RICE-25", cost_price=1200.0, current_stock=5.0)
    db.add(prod)
    db.commit()

    po_resp = create_purchase_order(
        PurchaseOrderCreate(
            priority="high",
            items=[PurchaseOrderItemCreate(product_id=prod.id, quantity=20.0, unit_cost=1200.0)],
        ),
        db,
    )
    po_id = po_resp["id"]

    # Receive the PO
    received = receive_purchase_order(po_id, db)
    assert received["status"] == "RECEIVED"
    assert received["received_at"] is not None

    # Check product stock
    db.refresh(prod)
    assert prod.current_stock == 25.0  # 5.0 + 20.0

    # Check InventoryEvent
    event = (
        db.query(InventoryEvent)
        .filter(InventoryEvent.product_id == prod.id, InventoryEvent.event_type == "PURCHASE_RECEIVED")
        .first()
    )
    assert event is not None
    assert event.quantity_before == 5.0
    assert event.quantity_change == 20.0
    assert event.quantity_after == 25.0
    assert event.reference_type == "purchase_order"
    assert event.reference_id == str(po_id)


def test_cannot_receive_twice(db):
    """Attempting to receive an already received PO must raise 400."""
    prod = Product(name="Item Double", sku="DBL-01", cost_price=10.0, current_stock=5.0)
    db.add(prod)
    db.commit()

    po_resp = create_purchase_order(
        PurchaseOrderCreate(
            items=[PurchaseOrderItemCreate(product_id=prod.id, quantity=10.0, unit_cost=10.0)],
        ),
        db,
    )
    receive_purchase_order(po_resp["id"], db)

    # Second receive should fail
    with pytest.raises(HTTPException) as exc:
        receive_purchase_order(po_resp["id"], db)
    assert exc.value.status_code == 400
