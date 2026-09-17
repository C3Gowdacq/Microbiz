"""
models.py -- SQLAlchemy ORM models for MicroBizAI.

Tables:
  - Product, Customer, Sale, Expense, Invoice  (core business entities)
  - Payment                                    (payments recorded against invoices)
  - BusinessSettings                           (singleton row with shop-wide config)
  - Recommendation, HumanAction               (HITL persistence layer)
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

    sales = relationship("Sale", back_populates="product")
    forecasts = relationship("Forecast", back_populates="product", cascade="all, delete-orphan")


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
    Stores shop-wide config used across cashflow calculations.
    """
    __tablename__ = "business_settings"

    id               = Column(Integer, primary_key=True, default=1)
    min_cash_reserve = Column(Float, default=25000.0)
    currency         = Column(String, default="INR")


# ── 2. HITL Persistence Models ────────────────────────────────────────────────

class Recommendation(Base):
    __tablename__ = "recommendations"

    id                       = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at               = Column(DateTime, default=datetime.utcnow)
    primary_action           = Column(String, index=True)
    priority                 = Column(String)
    reason                   = Column(Text)
    secondary_recommendations = Column(JSON, nullable=True)
    llm_summary              = Column(Text, nullable=True)
    llm_reasoning            = Column(Text, nullable=True)
    suggested_customer_message = Column(Text, nullable=True)
    status                   = Column(String, default="pending", index=True)
    modified_message         = Column(Text, nullable=True)

    actions = relationship("HumanAction", back_populates="recommendation", cascade="all, delete-orphan")


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
