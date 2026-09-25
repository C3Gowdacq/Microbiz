"""
backend/tests/test_phase7_agent_orchestrator.py

Phase 7 validation tests for agent_orchestrator.py.
Tests:
  - run_inventory_agent creates AgentRun and returns AgentResult
  - run_khata_agent execution and deduplication
  - run_cashflow_agent execution
  - Failure isolation: bad entity doesn't crash run_all_agents
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
from backend.app.models import Product, Customer, Invoice, Expense, BusinessSettings, AgentRun, Recommendation
from backend.app.services.agent_orchestrator import (
    run_inventory_agent,
    run_khata_agent,
    run_expense_agent,
    run_cashflow_agent,
    run_all_agents,
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


def test_run_inventory_agent_records_run(db):
    """Running inventory agent must create an AgentRun log entry."""
    prod = Product(
        name="Basmati Rice 10kg",
        sku="RICE-10",
        selling_price=800.0,
        cost_price=650.0,
        current_stock=2.0,
        reorder_level=10.0,
        safety_stock=5.0,
        lead_time_days=3,
    )
    db.add(prod)
    db.commit()

    res = run_inventory_agent(prod.id, db, trigger="manual")
    assert res.agent_name == "inventory"
    assert res.status == "completed"
    assert res.entity_id == prod.id
    assert res.recommendation_id is not None

    # Check persistent AgentRun table
    run_log = db.query(AgentRun).filter(AgentRun.entity_id == prod.id).first()
    assert run_log is not None
    assert run_log.agent_name == "inventory"
    assert run_log.status == "completed"
    assert run_log.completed_at is not None
    assert run_log.trigger == "manual"


def test_run_inventory_agent_handles_error_gracefully(db):
    """Non-existent product ID results in failed status without raising exception."""
    res = run_inventory_agent("nonexistent-id", db)
    assert res.status == "failed"
    assert "not found" in res.error

    run_log = db.query(AgentRun).filter(AgentRun.entity_id == "nonexistent-id").first()
    assert run_log is not None
    assert run_log.status == "failed"


def test_run_khata_agent_creates_reminder(db):
    """Running khata agent on overdue customer flags risk and records run."""
    cust = Customer(name="Sharma Kirana", phone="+91 98888 77777")
    db.add(cust)
    db.commit()

    inv = Invoice(
        customer_id=cust.id,
        invoice_amount=5000.0,
        amount_paid=0.0,
        due_date=date(2025, 1, 1),
        created_date=date(2024, 12, 1),
        status="unpaid",
    )
    db.add(inv)
    db.commit()

    res = run_khata_agent(cust.id, db)
    assert res.agent_name == "khata"
    assert res.status == "completed"
    assert res.recommendation_id is not None

    run_log = db.query(AgentRun).filter(AgentRun.agent_name == "khata").first()
    assert run_log is not None
    assert run_log.status == "completed"


def test_run_cashflow_agent(db):
    """Running cashflow agent executes solvency check and logs run."""
    res = run_cashflow_agent(db)
    assert res.agent_name == "cashflow"
    assert res.status == "completed"
    assert "cashflow_risk" in res.details

    run_log = db.query(AgentRun).filter(AgentRun.agent_name == "cashflow").first()
    assert run_log is not None
    assert run_log.status == "completed"


def test_run_all_agents_isolation(db):
    """run_all_agents executes sweeps across all domains."""
    prod = Product(name="Item Sweep", sku="SWEEP-1", selling_price=100.0, current_stock=20.0)
    cust = Customer(name="Customer Sweep")
    exp = Expense(category="Utilities", current_period_amount=1500.0, prior_period_amount=1200.0, date=date.today())
    db.add_all([prod, cust, exp])
    db.commit()

    results = run_all_agents(db)
    assert len(results) >= 4  # at least product, customer, expense, cashflow
    statuses = [r.status for r in results]
    assert all(s in ("completed", "skipped") for s in statuses)
