"""
models.py -- SQLAlchemy ORM models for MicroBizAI.

Tables (original):
  - Product, Customer, Sale, Expense, Invoice  (core business entities)
  - Payment                                    (payments recorded against invoices)
  - BusinessSettings                           (singleton row with shop-wide config)
  - Recommendation, HumanAction               (HITL persistence layer)
  - Forecast                                   (ML demand forecasting records)

Tables (Phase 1 additions):
  - Supplier                                   (vendor/supplier master)
  - PurchaseOrder, PurchaseOrderItem           (PO lifecycle management)
  - InventoryEvent                             (immutable stock audit trail)
  - AgentRun                                   (agent execution tracking)
  - AuditLog                                   (full actor/action/entity audit)
"""

import uuid
from datetime import datetime, date as date_type
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime,
    Text, ForeignKey, JSON, Boolean,
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


# ── 1. Core Business Entity Models ───────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id             = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    sku            = Column(String, index=True)
    name           = Column(String, nullable=False)
    selling_price  = Column(Float, default=0.0)
    cost_price     = Column(Float, default=0.0)
    current_stock  = Column(Float, default=0.0)
    reorder_level  = Column(Float, default=0.0)
    safety_stock   = Column(Float, default=0.0)
    lead_time_days = Column(Integer, default=1)

    # ── ML Store Profile (Rossmann feature mapping) ──────────────────────────
    # These fields map to the 25-feature vector the trained Random Forest model
    # expects. Products without store_type + assortment are not eligible for
    # ML-powered forecasting.
    store_type            = Column(String, nullable=True)    # 'a','b','c','d' → one-hot StoreType_*
    assortment            = Column(String, nullable=True)    # 'a','b','c'     → one-hot Assortment_*
    competition_distance  = Column(Float, nullable=True)     # meters to nearest competitor
    competition_open_date = Column(Date, nullable=True)      # when competitor opened → competition_open_days
    promo_active          = Column(Boolean, default=False)    # is a promotion running? → Promo
    promo2                = Column(Boolean, default=False)    # extended/continuous promo → Promo2
    school_holiday        = Column(Boolean, default=False)    # school holiday flag → SchoolHoliday

    sales            = relationship("Sale", back_populates="product")
    forecasts        = relationship("Forecast", back_populates="product", cascade="all, delete-orphan")
    inventory_events = relationship("InventoryEvent", back_populates="product", cascade="all, delete-orphan")
    po_items         = relationship("PurchaseOrderItem", back_populates="product")


class Customer(Base):
    __tablename__ = "customers"

    id    = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name  = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    invoices = relationship("Invoice", back_populates="customer")
    sales    = relationship("Sale",    back_populates="customer")


class Sale(Base):
    __tablename__ = "sales"

    id          = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id  = Column(String, ForeignKey("products.id"), index=True, nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), index=True, nullable=True)
    store_id    = Column(Integer, default=1)
    date        = Column(Date, nullable=True)
    quantity    = Column(Float, default=0.0)
    unit_price  = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)   # quantity * unit_price, stored for fast aggregation

    product  = relationship("Product",  back_populates="sales")
    customer = relationship("Customer", back_populates="sales")


class Expense(Base):
    __tablename__ = "expenses"

    id                    = Column(Integer, primary_key=True, autoincrement=True, index=True)
    category              = Column(String, index=True, nullable=False)
    description           = Column(String, nullable=True)
    current_period_amount = Column(Float, default=0.0)
    prior_period_amount   = Column(Float, default=0.0)
    date                  = Column(Date, nullable=True)


class Invoice(Base):
    __tablename__ = "invoices"

    id             = Column(Integer, primary_key=True, autoincrement=True, index=True)
    customer_id    = Column(String, ForeignKey("customers.id"), index=True, nullable=False)
    invoice_amount = Column(Float, default=0.0)
    amount_paid    = Column(Float, default=0.0)
    due_date       = Column(Date, nullable=True)
    created_date   = Column(Date, nullable=True)
    status         = Column(String, default="unpaid", index=True)
    # status values: 'unpaid' | 'partially_paid' | 'paid'

    customer = relationship("Customer", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


class Payment(Base):
    """Individual payment recorded against an invoice."""
    __tablename__ = "payments"

    id           = Column(Integer, primary_key=True, autoincrement=True, index=True)
    invoice_id   = Column(Integer, ForeignKey("invoices.id"), index=True, nullable=False)
    payment_date = Column(Date, nullable=False)
    amount       = Column(Float, nullable=False)

    invoice = relationship("Invoice", back_populates="payments")


class BusinessSettings(Base):
    """
    Singleton settings table — always exactly one row (id=1).
    Stores shop-wide config used across cashflow calculations and agent thresholds.

    Phase 1 additions:
      - safety_stock_days: days of demand buffer to maintain
      - review_period_days: how often stock is reviewed
      - khata_overdue_days: days after which invoice is flagged overdue
      - expense_anomaly_threshold_pct: % increase that triggers expense alert
      - high_risk_multiplier / medium_risk_multiplier: coverage day multipliers
      - autonomous_mode: whether agents run automatically on events
    """
    __tablename__ = "business_settings"

    id               = Column(Integer, primary_key=True, default=1)
    min_cash_reserve = Column(Float, default=25000.0)
    currency         = Column(String, default="INR")

    # Operational thresholds (Phase 1)
    safety_stock_days             = Column(Integer, default=3)
    review_period_days            = Column(Integer, default=7)
    khata_overdue_days            = Column(Integer, default=30)
    expense_anomaly_threshold_pct = Column(Float, default=30.0)
    high_risk_multiplier          = Column(Float, default=1.0)   # coverage < lead_time * this → HIGH
    medium_risk_multiplier        = Column(Float, default=1.5)   # coverage < lead_time * this → MEDIUM

    # Autonomous mode toggle (Phase 1)
    # When True: sale → inventory event → risk eval → replenishment recommendation
    # When False: all agent actions must be manually triggered
    autonomous_mode = Column(Boolean, default=False)


# ── 2. HITL Persistence Models ────────────────────────────────────────────────

class Recommendation(Base):
    __tablename__ = "recommendations"

    id                        = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at                = Column(DateTime, default=datetime.utcnow)
    primary_action            = Column(String, index=True)
    priority                  = Column(String)
    reason                    = Column(Text)
    secondary_recommendations = Column(JSON, nullable=True)
    llm_summary               = Column(Text, nullable=True)
    llm_reasoning             = Column(Text, nullable=True)
    suggested_customer_message = Column(Text, nullable=True)
    status                    = Column(String, default="pending", index=True)
    modified_message          = Column(Text, nullable=True)

    # Phase 1 additions: entity context for traceability
    module      = Column(String, nullable=True, index=True)    # 'inventory' | 'khata' | 'expense' | 'cashflow'
    entity_type = Column(String, nullable=True)                # 'product' | 'customer' | 'expense_category'
    entity_id   = Column(String, nullable=True, index=True)    # product.id or customer.id etc.

    # Phase 6 link: associated purchase order (set after PO is created from this recommendation)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)

    actions = relationship("HumanAction", back_populates="recommendation", cascade="all, delete-orphan")
    purchase_order = relationship("PurchaseOrder", back_populates="recommendation", foreign_keys=[purchase_order_id])


class HumanAction(Base):
    __tablename__ = "human_actions"

    id                = Column(Integer, primary_key=True, autoincrement=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), index=True)
    action            = Column(String, index=True)
    original_message  = Column(Text, nullable=True)
    modified_message  = Column(Text, nullable=True)
    timestamp         = Column(DateTime, default=datetime.utcnow)

    recommendation = relationship("Recommendation", back_populates="actions")


# ── 3. Sales Forecasting Models ───────────────────────────────────────────────

class Forecast(Base):
    """
    Dedicated persistent sales forecast record for a product.
    Allows independent decoupled forecasting and human decision tracking.
    """
    __tablename__ = "forecasts"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id      = Column(String, ForeignKey("products.id"), index=True, nullable=False)
    forecast_date   = Column(Date, default=date_type.today, nullable=False)
    horizon_days    = Column(Integer, default=7, nullable=False)
    predicted_sales = Column(Float, default=0.0, nullable=False)
    model_used      = Column(String, default="random_forest", nullable=False)
    status          = Column(String, default="active", index=True, nullable=False)
    # status values: 'active' | 'acted_on' | 'dismissed'
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="forecasts")


# ── 4. Supplier Model (Phase 1) ───────────────────────────────────────────────

class Supplier(Base):
    """
    Vendor/supplier master record.
    Used to associate purchase orders with a known supplier contact.
    """
    __tablename__ = "suppliers"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name            = Column(String, nullable=False, index=True)
    contact_name    = Column(String, nullable=True)
    phone           = Column(String, nullable=True)
    email           = Column(String, nullable=True)
    address         = Column(Text, nullable=True)
    category        = Column(String, nullable=True)   # e.g. 'Grains', 'FMCG', 'Fresh Produce'
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


# ── 5. Purchase Order Models (Phase 1) ────────────────────────────────────────

class PurchaseOrder(Base):
    """
    Full purchase-order lifecycle.

    Status flow:
      DRAFT → PENDING_APPROVAL → APPROVED → ORDERED → RECEIVED
      Any status → CANCELLED or REJECTED (terminal)
    """
    __tablename__ = "purchase_orders"

    id            = Column(Integer, primary_key=True, autoincrement=True, index=True)
    po_number     = Column(String, unique=True, index=True)   # e.g. PO-2024-00001
    supplier_id   = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    status        = Column(String, default="DRAFT", index=True, nullable=False)
    # DRAFT | PENDING_APPROVAL | APPROVED | MODIFIED | REJECTED | ORDERED | RECEIVED | CANCELLED

    total_amount  = Column(Float, default=0.0)
    priority      = Column(String, default="medium")          # high | medium | low
    reason        = Column(Text, nullable=True)               # why this PO was created
    notes         = Column(Text, nullable=True)               # merchant notes

    created_at    = Column(DateTime, default=datetime.utcnow)
    approved_at   = Column(DateTime, nullable=True)
    ordered_at    = Column(DateTime, nullable=True)
    received_at   = Column(DateTime, nullable=True)

    supplier      = relationship("Supplier", back_populates="purchase_orders")
    items         = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    recommendation = relationship("Recommendation", back_populates="purchase_order", foreign_keys="Recommendation.purchase_order_id")


class PurchaseOrderItem(Base):
    """Individual line item within a purchase order."""
    __tablename__ = "purchase_order_items"

    id                = Column(Integer, primary_key=True, autoincrement=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), index=True, nullable=False)
    product_id        = Column(String, ForeignKey("products.id"), index=True, nullable=False)
    quantity          = Column(Float, nullable=False)
    unit_cost         = Column(Float, default=0.0)
    total_cost        = Column(Float, default=0.0)  # quantity * unit_cost

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product        = relationship("Product", back_populates="po_items")


# ── 6. Inventory Event Model (Phase 1) ───────────────────────────────────────

class InventoryEvent(Base):
    """
    Immutable audit trail of every stock change.
    Every increase, decrease, or adjustment must create one of these records.

    event_type values:
      SALE               - stock decreased due to a customer sale
      PURCHASE_RECEIVED  - stock increased from a received purchase order
      MANUAL_ADJUSTMENT  - stock directly set by merchant
      STOCK_ADD          - manual stock addition (quick restock)
      RETURN             - customer return
      DAMAGE             - stock written off due to damage
      OPENING_STOCK      - initial stock entry
    """
    __tablename__ = "inventory_events"

    id               = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id       = Column(String, ForeignKey("products.id"), index=True, nullable=False)
    event_type       = Column(String, nullable=False, index=True)
    quantity_before  = Column(Float, nullable=False)
    quantity_change  = Column(Float, nullable=False)   # positive = increase, negative = decrease
    quantity_after   = Column(Float, nullable=False)
    reference_type   = Column(String, nullable=True)   # 'sale' | 'purchase_order' | 'manual' etc.
    reference_id     = Column(String, nullable=True)   # ID of the triggering record
    notes            = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="inventory_events")


# ── 7. Agent Run Model (Phase 1) ─────────────────────────────────────────────

class AgentRun(Base):
    """
    Records each time an agent executes, including its inputs, outputs, and status.
    Enables audit trail and debugging of autonomous agent behavior.
    """
    __tablename__ = "agent_runs"

    id           = Column(Integer, primary_key=True, autoincrement=True, index=True)
    agent_name   = Column(String, nullable=False, index=True)
    # 'inventory' | 'replenishment' | 'khata' | 'expense' | 'cashflow' | 'full_pipeline'

    started_at   = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status       = Column(String, default="running", index=True)
    # 'running' | 'completed' | 'failed' | 'skipped'

    trigger      = Column(String, nullable=True)   # 'sale_event' | 'manual' | 'scheduled'
    entity_type  = Column(String, nullable=True)   # 'product' | 'customer' | 'expense_category'
    entity_id    = Column(String, nullable=True)   # ID of the entity being analyzed

    input_data   = Column(JSON, nullable=True)     # agent input snapshot
    output_data  = Column(JSON, nullable=True)     # agent result snapshot
    error        = Column(Text, nullable=True)     # error message if status='failed'


# ── 8. Audit Log Model (Phase 1) ─────────────────────────────────────────────

class AuditLog(Base):
    """
    Full actor/action/entity audit trail.
    Records every significant state change in the system.

    actor_type: 'SYSTEM' | 'AGENT' | 'MERCHANT'
    """
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, autoincrement=True, index=True)
    timestamp   = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    actor_type  = Column(String, nullable=False)   # 'SYSTEM' | 'AGENT' | 'MERCHANT'
    actor_id    = Column(String, nullable=True)    # agent name or user id
    action      = Column(String, nullable=False, index=True)
    # e.g. 'SALE_CREATED' | 'STOCK_DECREASED' | 'PO_APPROVED' | 'RECOMMENDATION_REJECTED'

    entity      = Column(String, nullable=True)    # table name: 'products' | 'purchase_orders' etc.
    entity_id   = Column(String, nullable=True, index=True)
    old_value   = Column(JSON, nullable=True)      # snapshot before change
    new_value   = Column(JSON, nullable=True)      # snapshot after change
    reason      = Column(Text, nullable=True)      # human-readable explanation
