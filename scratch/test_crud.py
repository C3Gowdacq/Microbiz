"""
test_crud.py -- Lightweight CRUD tests for MicroBizAI backend.

Creates a minimal FastAPI app with ONLY the CRUD routers (no ML pipeline imports).
This makes the test fast since it avoids loading LangGraph/Groq/VAE.

Run with:
  cd c:\\Chetan\\Major_Project
  .\\venv\\Scripts\\python scratch\\test_crud.py
"""

import sys
import os
import traceback
import tempfile
from datetime import date, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Point to a temp SQLite file ───────────────────────────────────────────────
_tmp_db = os.path.join(tempfile.gettempdir(), "microbizai_crud_test.db")
if os.path.exists(_tmp_db):
    os.remove(_tmp_db)

# Patch database module BEFORE any app imports
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

# Create tables
from backend.app.models import Base
Base.metadata.create_all(bind=_engine)

# Build a minimal FastAPI app with ONLY CRUD routers (no ML imports)
from fastapi import FastAPI
from backend.app.routers import products, customers, sales, invoices, expenses, dashboard, settings as settings_router
from backend.app.database import get_db

_app = FastAPI(title="MicroBizAI CRUD Test App")
_app.dependency_overrides[get_db] = _get_db

_app.include_router(products.router)
_app.include_router(customers.router)
_app.include_router(sales.router)
_app.include_router(invoices.router)
_app.include_router(expenses.router)
_app.include_router(dashboard.router)
_app.include_router(settings_router.router)

from fastapi.testclient import TestClient
client = TestClient(_app, raise_server_exceptions=True)

# ── Test helpers ──────────────────────────────────────────────────────────────

all_passed = True

def chk(condition: bool, label: str, detail: str = "") -> bool:
    global all_passed
    tag = "[PASS]" if condition else "[FAIL]"
    suffix = f"  ({detail})" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    if not condition:
        all_passed = False
    return condition


# ── Suite A: Products & Sales ─────────────────────────────────────────────────

def suite_a() -> str:
    print("\n============================================================")
    print("SUITE A: Products & Sales")
    print("============================================================")

    # A1 Create product
    r = client.post("/api/products", json={
        "sku": "TST-001", "name": "Test Widget",
        "selling_price": 29.99, "cost_price": 10.0,
        "current_stock": 100.0, "reorder_level": 20.0,
        "safety_stock": 5.0, "lead_time_days": 3,
    })
    chk(r.status_code == 201, "A1: Create product -> 201", str(r.status_code))
    pid = r.json().get("id", "")
    chk(len(pid) == 36, "A1: Product ID is UUID", pid[:8])
    chk(r.json().get("current_stock") == 100.0, "A1: Initial stock = 100")

    # A2 GET product
    r2 = client.get(f"/api/products/{pid}")
    chk(r2.status_code == 200 and r2.json().get("name") == "Test Widget", "A2: GET product OK")

    # A3 Update price
    r3 = client.put(f"/api/products/{pid}", json={"selling_price": 34.99})
    chk(r3.status_code == 200 and r3.json().get("selling_price") == 34.99, "A3: PUT price update -> 34.99")

    # A4 List products
    r4 = client.get("/api/products")
    chk(r4.status_code == 200 and len(r4.json()) >= 1, "A4: List products >= 1 item")

    # A5 Record sale qty=15 -> stock 85
    r5 = client.post("/api/sales", json={
        "product_id": pid, "quantity": 15.0, "unit_price": 34.99,
        "date": str(date.today()),
    })
    if r5.status_code != 201:
        print(f"     [A5 error] {r5.json()}")
    chk(r5.status_code == 201, "A5: Record sale -> 201", str(r5.status_code))
    chk(r5.json().get("total_amount") == round(15 * 34.99, 2), "A5: total_amount = qty*price", str(r5.json().get("total_amount")))

    # A6 Stock decremented
    r6 = client.get(f"/api/products/{pid}")
    chk(r6.json().get("current_stock") == 85.0, "A6: Stock decremented to 85", str(r6.json().get("current_stock")))

    # A7 Second sale qty=50 -> stock 35
    client.post("/api/sales", json={"product_id": pid, "quantity": 50.0, "unit_price": 34.99})
    r7 = client.get(f"/api/products/{pid}")
    chk(r7.json().get("current_stock") == 35.0, "A7: Stock after 2nd sale = 35", str(r7.json().get("current_stock")))

    # A8 Over-stock sale -> 422
    r8 = client.post("/api/sales", json={"product_id": pid, "quantity": 200.0, "unit_price": 34.99})
    chk(r8.status_code == 422, "A8: Over-stock sale -> 422", str(r8.status_code))

    # A9 Adjust stock directly (delivery)
    r9 = client.put(f"/api/products/{pid}/stock", json={"current_stock": 150.0})
    chk(r9.status_code == 200 and r9.json().get("current_stock") == 150.0, "A9: /stock sets to 150")

    # A10 List sales filtered
    r10 = client.get(f"/api/sales?product_id={pid}")
    chk(r10.status_code == 200 and len(r10.json()) == 2, "A10: 2 sales for product", str(len(r10.json())))

    return pid


# ── Suite B: Customers, Invoices & Payments ───────────────────────────────────

def suite_b() -> str:
    print("\n============================================================")
    print("SUITE B: Customers, Invoices & Payments")
    print("============================================================")

    # B1 Create customer
    r = client.post("/api/customers", json={"name": "Rosa Retailer", "email": "rosa@example.com"})
    chk(r.status_code == 201, "B1: Create customer -> 201")
    cid = r.json().get("id", "")
    chk(len(cid) == 36, "B1: Customer ID is UUID")

    # B2 List
    r2 = client.get("/api/customers")
    chk(r2.status_code == 200 and any(c["id"] == cid for c in r2.json()), "B2: Customer appears in list")

    # B3 Create invoice (past due)
    past_due = str(date.today() - timedelta(days=10))
    r3 = client.post("/api/invoices", json={"customer_id": cid, "invoice_amount": 100.0, "due_date": past_due})
    chk(r3.status_code == 201, "B3: Create invoice -> 201", str(r3.status_code))
    inv = r3.json()
    iid = inv["id"]
    chk(inv["status"] == "unpaid", "B3: Status = 'unpaid'")
    chk(inv["amount_paid"] == 0.0, "B3: amount_paid = 0")

    # B4 List invoices by customer
    r4 = client.get(f"/api/invoices?customer_id={cid}")
    chk(r4.status_code == 200 and len(r4.json()) == 1, "B4: 1 invoice for customer")

    # B5 Partial payment €60 -> partially_paid
    r5 = client.post(f"/api/invoices/{iid}/payments", json={"payment_date": str(date.today()), "amount": 60.0})
    chk(r5.status_code == 201, "B5: Partial payment -> 201", str(r5.status_code))
    p = r5.json()
    chk(p["invoice_status"] == "partially_paid", "B5: Status = 'partially_paid'", p["invoice_status"])
    chk(p["invoice_amount_paid"] == 60.0, "B5: amount_paid = 60.0")

    # B6 Verify via GET
    r6 = client.get(f"/api/invoices/{iid}")
    chk(r6.json()["status"] == "partially_paid", "B6: GET invoice status = 'partially_paid'")
    chk(r6.json()["amount_paid"] == 60.0, "B6: GET amount_paid = 60.0")

    # B7 Remaining €40 -> paid
    r7 = client.post(f"/api/invoices/{iid}/payments", json={"payment_date": str(date.today()), "amount": 40.0})
    chk(r7.status_code == 201, "B7: Final payment -> 201")
    p2 = r7.json()
    chk(p2["invoice_status"] == "paid", "B7: Status = 'paid'", p2["invoice_status"])
    chk(p2["invoice_amount_paid"] == 100.0, "B7: amount_paid = 100.0")

    # B8 Pay on already-paid invoice -> 400
    r8 = client.post(f"/api/invoices/{iid}/payments", json={"payment_date": str(date.today()), "amount": 10.0})
    chk(r8.status_code == 400, "B8: Pay on paid invoice -> 400", str(r8.status_code))

    # B9 Over-payment -> 422
    r3b = client.post("/api/invoices", json={"customer_id": cid, "invoice_amount": 50.0})
    iid2 = r3b.json()["id"]
    r9 = client.post(f"/api/invoices/{iid2}/payments", json={"payment_date": str(date.today()), "amount": 999.0})
    chk(r9.status_code == 422, "B9: Over-payment -> 422", str(r9.status_code))

    # B10 Customer summary
    r10 = client.get(f"/api/customers/{cid}/summary")
    chk(r10.status_code == 200, "B10: GET /customers/{id}/summary -> 200")
    s = r10.json()
    chk(s["outstanding_balance"] == 50.0, "B10: Outstanding balance = 50.0 (2nd invoice unpaid)", str(s["outstanding_balance"]))
    chk(len(s["invoice_history"]) == 2, "B10: 2 invoices in history")

    return cid


# ── Suite C: Dashboard & Settings ─────────────────────────────────────────────

def suite_c():
    print("\n============================================================")
    print("SUITE C: Dashboard Summary & Settings")
    print("============================================================")

    # C1 Default settings
    r = client.get("/api/settings")
    chk(r.status_code == 200, "C1: GET /api/settings -> 200")
    chk(r.json()["min_cash_reserve"] == 5000.0, "C1: Default min_cash_reserve = 5000")
    chk(r.json()["currency"] == "EUR", "C1: Default currency = EUR")

    # C2 Update settings
    r2 = client.put("/api/settings", json={"min_cash_reserve": 8000.0, "currency": "GBP"})
    chk(r2.status_code == 200, "C2: PUT /api/settings -> 200")
    chk(r2.json()["currency"] == "GBP", "C2: Currency = GBP")
    chk(r2.json()["min_cash_reserve"] == 8000.0, "C2: min_cash_reserve = 8000")

    # C3 Dashboard summary
    r3 = client.get("/api/dashboard/summary")
    chk(r3.status_code == 200, "C3: GET /api/dashboard/summary -> 200")
    ds = r3.json()
    print(f"     Dashboard: {ds}")

    chk("today_sales_revenue" in ds, "C3: today_sales_revenue present")
    chk("total_cash_position" in ds, "C3: total_cash_position present")
    chk("low_stock_products_count" in ds, "C3: low_stock_products_count present")
    chk("overdue_invoices_count" in ds, "C3: overdue_invoices_count present")
    chk("pending_recommendations_count" in ds, "C3: pending_recommendations_count present")
    chk(ds["currency"] == "GBP", "C3: Currency = GBP (from settings)")
    # stock was set to 150 > reorder_level=20, so not low-stock
    chk(ds["low_stock_products_count"] == 0, "C3: low_stock=0 (stock=150, reorder=20)", str(ds["low_stock_products_count"]))
    # inv1 paid, inv2 no due_date -> no overdue
    chk(ds["overdue_invoices_count"] == 0, "C3: overdue=0 (inv1 paid, inv2 no due_date)", str(ds["overdue_invoices_count"]))


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== MicroBizAI - CRUD Layer Test Suite ===")
    print(f"    DB: {_tmp_db}")

    try:
        suite_a()
        suite_b()
        suite_c()
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
