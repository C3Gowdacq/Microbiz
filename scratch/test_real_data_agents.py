"""
test_real_data_agents.py -- Tests that seed the database and verify each targeted
agent endpoint correctly detects issues from real stored data (not hardcoded payloads).

Test Scenarios Seeded:
  Products:
    P1: Electronics Premium  (healthy margin, good stock)
    P2: Budget Cables        (deliberately LOW STOCK: stock=5, reorder=50)
    P3: Clearance Mugs       (LOSS-MAKING: selling_price < cost_price)
    P4: T-Shirts             (healthy)

  Customers:
    C1: Reliable Corp        (paid all invoices)
    C2: Late Payer Ltd       (OVERDUE invoice: due 20 days ago, partially paid)

  Expenses:
    Rent:    current=3000, prior=3000  -> stable, LOW risk
    Utilities: current=2800, prior=1800 -> +55.6% SPIKE, HIGH risk

Run with:
  cd c:\\Chetan\\Major_Project
  .\\venv\\Scripts\\python scratch\\test_real_data_agents.py
"""

import sys
import os
import traceback
import tempfile
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Isolated temp DB ──────────────────────────────────────────────────────────
_tmp_db = os.path.join(tempfile.gettempdir(), "microbizai_agents_test.db")
if os.path.exists(_tmp_db):
    os.remove(_tmp_db)

import backend.app.database as _db_module
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = create_engine(f"sqlite:///{_tmp_db}", connect_args={"check_same_thread": False})
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
_db_module.engine = _engine
_db_module.SQLALCHEMY_DATABASE_URL = f"sqlite:///{_tmp_db}"

def _get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()

_db_module.get_db = _get_db

from backend.app.models import Base
Base.metadata.create_all(bind=_engine)

# Build minimal app with CRUD + agents routers (no ML pipeline needed for targeted endpoints)
from fastapi import FastAPI
from backend.app.routers import (
    products, customers, sales, invoices, expenses,
    dashboard, settings as settings_router,
)
from backend.app.routers import agents as agents_router
from backend.app.database import get_db

_app = FastAPI(title="MicroBizAI Agents Test App")
_app.dependency_overrides[get_db] = _get_db
_app.include_router(products.router)
_app.include_router(customers.router)
_app.include_router(sales.router)
_app.include_router(invoices.router)
_app.include_router(expenses.router)
_app.include_router(dashboard.router)
_app.include_router(settings_router.router)
_app.include_router(agents_router.router)

from fastapi.testclient import TestClient
client = TestClient(_app, raise_server_exceptions=True)

# ── Test helpers ──────────────────────────────────────────────────────────────
all_passed = True

def chk(condition, label, detail=""):
    global all_passed
    tag = "[PASS]" if condition else "[FAIL]"
    suffix = f"  ({detail})" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    if not condition:
        all_passed = False
    return condition


# ── Seed the database ─────────────────────────────────────────────────────────

def seed_database():
    print("\n--- Seeding database ---")

    # Products
    p1 = client.post("/api/products", json={
        "sku": "ELEC-001", "name": "Electronics Premium",
        "selling_price": 299.99, "cost_price": 180.0,
        "current_stock": 200.0, "reorder_level": 30.0,
        "safety_stock": 10.0, "lead_time_days": 5,
    }).json()["id"]

    p2 = client.post("/api/products", json={
        "sku": "CABLE-001", "name": "Budget Cables",
        "selling_price": 9.99, "cost_price": 3.0,
        "current_stock": 5.0,     # <-- deliberately LOW (reorder_level=50)
        "reorder_level": 50.0,
        "safety_stock": 10.0, "lead_time_days": 3,
    }).json()["id"]

    p3 = client.post("/api/products", json={
        "sku": "MUG-CLEAR", "name": "Clearance Mugs",
        "selling_price": 4.99, "cost_price": 8.0,  # <-- loss-making
        "current_stock": 300.0, "reorder_level": 20.0,
        "safety_stock": 5.0, "lead_time_days": 2,
    }).json()["id"]

    p4 = client.post("/api/products", json={
        "sku": "SHIRT-001", "name": "T-Shirts",
        "selling_price": 24.99, "cost_price": 8.0,
        "current_stock": 500.0, "reorder_level": 100.0,
        "safety_stock": 20.0, "lead_time_days": 4,
    }).json()["id"]

    # Customers
    c1 = client.post("/api/customers", json={"name": "Reliable Corp", "email": "pay@reliable.com"}).json()["id"]
    c2 = client.post("/api/customers", json={"name": "Late Payer Ltd", "email": "late@payers.co"}).json()["id"]

    # Record sales (to establish demand history for inventory builder)
    today = str(date.today())
    twenty_days_ago = str(date.today() - timedelta(days=20))

    # Electronics Premium: 10 units sold over last 20 days
    client.post("/api/sales", json={"product_id": p1, "quantity": 10.0, "unit_price": 299.99, "date": twenty_days_ago})

    # Budget Cables: 80 units sold recently (high demand, low stock -> triggers HIGH risk)
    client.post("/api/sales", json={"product_id": p2, "quantity": 80.0, "unit_price": 9.99, "date": twenty_days_ago})

    # Clearance Mugs: 50 units sold
    client.post("/api/sales", json={"product_id": p3, "quantity": 50.0, "unit_price": 4.99, "date": twenty_days_ago})

    # T-Shirts: 100 units sold
    client.post("/api/sales", json={"product_id": p4, "quantity": 100.0, "unit_price": 24.99, "date": twenty_days_ago})

    # Invoices: c1 fully paid (no risk), c2 overdue
    inv1 = client.post("/api/invoices", json={
        "customer_id": c1, "invoice_amount": 5000.0,
        "due_date": str(date.today() - timedelta(days=30)),
    }).json()["id"]
    client.post(f"/api/invoices/{inv1}/payments", json={"payment_date": today, "amount": 5000.0})  # fully paid

    inv2 = client.post("/api/invoices", json={
        "customer_id": c2, "invoice_amount": 8000.0,
        "due_date": str(date.today() - timedelta(days=20)),  # overdue!
    }).json()["id"]
    client.post(f"/api/invoices/{inv2}/payments", json={"payment_date": today, "amount": 3000.0})  # partial only

    # Expenses: seed CURRENT period (last 30 days) and PRIOR period (31-60 days ago)
    # build_expense_input() queries by date range so rows must be in correct windows.

    today_date = date.today()

    # Rent: stable - same amount in both periods
    # Current period rows (last 30 days)
    for i in range(30):
        d = str(today_date - timedelta(days=i))
        client.post("/api/expenses", json={"category": "Rent",
                                          "current_period_amount": 100.0,
                                          "prior_period_amount": 0.0, "date": d})
    # Prior period rows (31-60 days ago)
    for i in range(30, 60):
        d = str(today_date - timedelta(days=i))
        client.post("/api/expenses", json={"category": "Rent",
                                          "current_period_amount": 100.0,
                                          "prior_period_amount": 0.0, "date": d})

    # Utilities: current period total ~2800, prior period total ~1800 -> ~55% spike
    # Current period: 2800 / 30 per day
    for i in range(30):
        d = str(today_date - timedelta(days=i))
        client.post("/api/expenses", json={"category": "Utilities",
                                          "current_period_amount": round(2800 / 30, 2),
                                          "prior_period_amount": 0.0, "date": d})
    # Prior period: 1800 / 30 per day
    for i in range(30, 60):
        d = str(today_date - timedelta(days=i))
        client.post("/api/expenses", json={"category": "Utilities",
                                          "current_period_amount": round(1800 / 30, 2),
                                          "prior_period_amount": 0.0, "date": d})

    print(f"  Products:   P1={p1[:8]}  P2={p2[:8]}  P3={p3[:8]}  P4={p4[:8]}")
    print(f"  Customers:  C1={c1[:8]}  C2={c2[:8]}")
    print(f"  Invoices:   inv1={inv1} (paid), inv2={inv2} (20d overdue, partial)")
    print("  Expenses:   Rent (stable), Utilities (spike)")

    return {
        "p1": p1, "p2": p2, "p3": p3, "p4": p4,
        "c1": c1, "c2": c2,
        "inv2": inv2,
    }


# ── Test Suites ───────────────────────────────────────────────────────────────

def test_inventory(ids):
    print("\n============================================================")
    print("TEST: Inventory Check Endpoints")
    print("============================================================")

    # P2 (Budget Cables) should be HIGH risk — stock=5, reorder=50, sold 80 recently
    r = client.post(f"/api/products/{ids['p2']}/check-inventory")
    chk(r.status_code == 200, "INV-1: check-inventory for low-stock product -> 200", str(r.status_code))
    result = r.json()["agent_result"]
    risk = result.get("stockout_risk")
    chk(risk in ("HIGH", "MEDIUM"), "INV-2: Low-stock product detected as HIGH/MEDIUM", risk)
    chk(r.json()["recommendation_created"] is True, "INV-3: Recommendation created for risky product")
    print(f"     Budget Cables -> stockout_risk={risk}, stock_gap={result.get('stock_gap')}")

    # P1 (Electronics Premium) — healthy stock, LOW demand history
    r2 = client.post(f"/api/products/{ids['p1']}/check-inventory")
    chk(r2.status_code == 200, "INV-4: check-inventory for healthy product -> 200")
    risk2 = r2.json()["agent_result"].get("stockout_risk")
    print(f"     Electronics Premium -> stockout_risk={risk2}")

    # 404 for unknown product
    r3 = client.post("/api/products/nonexistent-id/check-inventory")
    chk(r3.status_code == 404, "INV-5: Unknown product -> 404", str(r3.status_code))


def test_profitability(ids):
    print("\n============================================================")
    print("TEST: Profitability Check Endpoints")
    print("============================================================")

    # P3 (Clearance Mugs): selling=4.99, cost=8.0 -> LOSS MAKING
    r = client.post(f"/api/products/{ids['p3']}/check-profitability")
    chk(r.status_code == 200, "PROF-1: check-profitability for loss-making product -> 200", str(r.status_code))
    result = r.json()["agent_result"]
    classification = result.get("classification")
    margin = result.get("profit_margin")
    chk(classification == "loss_making", "PROF-2: Clearance Mugs classified as 'loss_making'", classification)
    chk(margin < 0, "PROF-3: Profit margin is negative", str(margin))
    chk(r.json()["recommendation_created"] is True, "PROF-4: Recommendation created for loss-making product")
    print(f"     Clearance Mugs -> classification={classification}, margin={margin:.1f}%")

    # P1 (Electronics Premium): healthy margin
    r2 = client.post(f"/api/products/{ids['p1']}/check-profitability")
    chk(r2.status_code == 200, "PROF-5: check-profitability for healthy product -> 200")
    cls2 = r2.json()["agent_result"].get("classification")
    chk(cls2 not in ("loss_making",), "PROF-6: Electronics Premium not loss_making", cls2)
    print(f"     Electronics Premium -> classification={cls2}")


def test_credit(ids):
    print("\n============================================================")
    print("TEST: Credit Check Endpoints")
    print("============================================================")

    # C2 (Late Payer): overdue invoice 20 days ago, partially paid -> MEDIUM or HIGH
    r = client.post(f"/api/customers/{ids['c2']}/check-credit")
    chk(r.status_code == 200, "CRED-1: check-credit for overdue customer -> 200", str(r.status_code))
    result = r.json()["agent_result"]
    risk = result.get("customer_risk")
    days_overdue = result.get("days_overdue")
    chk(risk in ("HIGH", "MEDIUM"), "CRED-2: Late Payer has HIGH/MEDIUM credit risk", risk)
    chk(days_overdue >= 20, "CRED-3: Days overdue >= 20", str(days_overdue))
    chk(r.json()["recommendation_created"] is True, "CRED-4: Recommendation created for overdue customer")
    print(f"     Late Payer Ltd -> risk={risk}, days_overdue={days_overdue}, outstanding={result.get('outstanding_amount')}")

    # C1 (Reliable Corp): fully paid, no outstanding -> no recommendation
    r2 = client.post(f"/api/customers/{ids['c1']}/check-credit")
    chk(r2.status_code == 200, "CRED-5: check-credit for clean customer -> 200")
    chk(r2.json()["recommendation_created"] is False, "CRED-6: No recommendation for clean customer")
    print(f"     Reliable Corp -> no risk (all paid)")


def test_expenses(ids):
    print("\n============================================================")
    print("TEST: Expense Trend Check Endpoints")
    print("============================================================")

    # Utilities: ~55% spike -> HIGH risk
    r = client.post("/api/expenses/check-trend", json={"category": "Utilities"})
    chk(r.status_code == 200, "EXP-1: check-trend for Utilities -> 200", str(r.status_code))
    result = r.json()["agent_result"]
    risk = result.get("risk")
    inc_pct = result.get("increase_pct")
    chk(risk in ("HIGH", "MEDIUM"), "EXP-2: Utilities detected as HIGH/MEDIUM risk", risk)
    chk(inc_pct is not None and inc_pct > 0, "EXP-3: Utilities show positive increase %", str(inc_pct))
    chk(r.json()["recommendation_created"] is True, "EXP-4: Recommendation created for spike")
    print(f"     Utilities -> risk={risk}, increase_pct={inc_pct or 0.0:.1f}%")

    # Rent: stable -> LOW risk
    r2 = client.post("/api/expenses/check-trend", json={"category": "Rent"})
    chk(r2.status_code == 200, "EXP-5: check-trend for Rent -> 200")
    risk2 = r2.json()["agent_result"].get("risk")
    chk(risk2 == "LOW", "EXP-6: Rent has LOW risk (stable)", risk2)
    chk(r2.json()["recommendation_created"] is False, "EXP-7: No recommendation for stable expense")
    print(f"     Rent -> risk={risk2}")

    # Unknown category -> returns new_category (no prior data)
    r3 = client.post("/api/expenses/check-trend", json={"category": "NewCategory"})
    chk(r3.status_code == 200, "EXP-8: check-trend for unknown category -> 200")
    trend = r3.json()["agent_result"].get("trend")
    chk(trend == "new_category", "EXP-9: Unknown category returns new_category trend", trend)


def test_cashflow(ids):
    print("\n============================================================")
    print("TEST: Cashflow Check (Real DB data)")
    print("============================================================")

    r = client.post("/api/cashflow/check-real")
    chk(r.status_code == 200, "CASH-1: check-real cashflow -> 200", str(r.status_code))
    data = r.json()
    inp = data.get("inputs_used", {})
    result = data.get("agent_result", {})

    chk("current_cash" in inp, "CASH-2: inputs_used has current_cash")
    chk("cash_shortage_risk" in result, "CASH-3: agent_result has cash_shortage_risk")
    chk("liquidity_ok" in result, "CASH-4: agent_result has liquidity_ok")

    print(f"     Inputs: current_cash={inp.get('current_cash'):.2f}, "
          f"expected_revenue={inp.get('expected_sales_revenue'):.2f}, "
          f"upcoming_expenses={inp.get('upcoming_expenses'):.2f}")
    print(f"     Result: risk={result.get('cash_shortage_risk')}, liquidity_ok={result.get('liquidity_ok')}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== MicroBizAI - Real-Data Agent Endpoint Tests ===")
    print(f"    DB: {_tmp_db}")

    try:
        ids = seed_database()
        test_inventory(ids)
        test_profitability(ids)
        test_credit(ids)
        test_expenses(ids)
        test_cashflow(ids)
    except Exception:
        print("\nUnexpected error:")
        traceback.print_exc()
        all_passed = False
    finally:
        _engine.dispose()
        if os.path.exists(_tmp_db):
            try:
                os.remove(_tmp_db)
                print(f"\n    [Cleaned up: {_tmp_db}]")
            except Exception as e:
                print(f"\n    [Could not delete temp DB: {e}]")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED -- see above")
    print("=" * 60)
    sys.exit(0 if all_passed else 1)
