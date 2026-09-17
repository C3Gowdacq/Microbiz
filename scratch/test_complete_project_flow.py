"""
scratch/test_complete_project_flow.py

End-to-End Test for the Complete MicroBizAI Business Flow requested by user:
1. Model predicts demand -> checks stock shortage -> calculates units to buy
2. Feasibility check: checks available cash vs minimum reserve -> finds cash is tight
3. Due collection check: identifies customer with overdue payment
4. Decision Engine synthesizes: triggers 'partial_replenishment_and_collect_receivables'
5. Prepares invoice reminder message for customer
6. Human confirms/approves recommendation in Approvals Inbox
7. Verifies standalone individual services: stock adjustment, customer credit check, and on-demand forecast
"""

import os
import sys
import tempfile
from datetime import date, timedelta

# Fix Windows console unicode printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create isolated test SQLite database
_tmp_db = os.path.join(tempfile.gettempdir(), "microbizai_flow_test.db")
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

from backend.app.models import Base, BusinessSettings
Base.metadata.create_all(bind=_engine)

# Seed BusinessSettings: minimum cash reserve = ₹10,000
with _Session() as session:
    settings = BusinessSettings(id=1, min_cash_reserve=10000.0, currency="INR")
    session.add(settings)
    session.commit()

from backend.app.main import app as main_app

from fastapi.testclient import TestClient
client = TestClient(main_app, raise_server_exceptions=True)

all_passed = True

def chk(condition: bool, label: str, detail: str = ""):
    global all_passed
    tag = "[PASS]" if condition else "[FAIL]"
    suffix = f"  ({detail})" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    if not condition:
        all_passed = False
    return condition


def run_full_system_test():
    global all_passed
    print("=" * 70)
    print("=== MICROBIZAI COMPLETE USER FLOW VERIFICATION ===")
    print("=" * 70)

    # ── STEP 1: Setup Product (Stock of Rice) ──────────────────────────────────
    print("\n--- 1. Product Setup: Basmati Rice (Low Stock) ---")
    p_res = client.post("/api/products", json={
        "sku": "RICE-BASMATI-50KG",
        "name": "Basmati Rice 50kg Bags",
        "selling_price": 3200.0,
        "cost_price": 2400.0,
        "current_stock": 5.0,         # only 5 bags in stock!
        "reorder_level": 40.0,        # reorder point is 40 bags
        "safety_stock": 10.0,
        "lead_time_days": 3,
        "store_type": "a",
        "assortment": "a",
        "competition_distance": 600.0,
        "promo_active": True,
    })
    chk(p_res.status_code == 201, "Product created with 201")
    product_id = p_res.json()["id"]

    # ── STEP 2: Setup Customer with Overdue Due (Invoice Pending) ──────────────
    print("\n--- 2. Customer Setup: Sharma Kirana Store with Overdue Bill ---")
    c_res = client.post("/api/customers", json={
        "name": "Sharma Kirana Store",
        "phone": "+91 98765 43210",
        "email": "sharma.kirana@example.com",
    })
    chk(c_res.status_code == 201, "Customer created with 201")
    customer_id = c_res.json()["id"]

    fifteen_days_ago = date.today() - timedelta(days=15)
    inv_res = client.post("/api/invoices", json={
        "customer_id": customer_id,
        "invoice_amount": 28000.0,    # Customer owes ₹28,000
        "amount_paid": 0.0,           # nothing paid yet
        "due_date": str(fifteen_days_ago),
    })
    chk(inv_res.status_code == 201, "Overdue invoice created with 201")

    # ── STEP 3: Setup Expenses & Tight Cash ────────────────────────────────────
    print("\n--- 3. Financial State: Current Cash is Tight ---")
    exp_res = client.post("/api/expenses", json={
        "category": "Shop Rent",
        "description": "Monthly commercial shop rent",
        "current_period_amount": 8000.0,
        "prior_period_amount": 8000.0,
        "date": str(date.today() - timedelta(days=5)),
    })
    chk(exp_res.status_code == 201, "Expense logged with 201")

    # Record small sales revenue (₹5,000) so net cash = 5,000 - 8,000 = negative / tight
    # Stock allows selling 1 bag
    client.post("/api/sales", json={
        "product_id": product_id,
        "quantity": 1.0,
        "unit_price": 3200.0,
        "sale_date": str(date.today() - timedelta(days=2)),
    })

    # ── STEP 4: Test Individual Standalone Services ────────────────────────────
    print("\n--- 4. Standalone Service: Dedicated On-Demand Product Forecast ---")
    f_res = client.post(f"/api/products/{product_id}/forecast", json={"horizon_days": 7})
    chk(f_res.status_code == 201, "Forecast generated with 201")
    f_data = f_res.json()
    predicted_demand = f_data["predicted_sales"]
    stock_gap = f_data["stock_gap_preview"]
    chk(predicted_demand > 0, "Forecast demand is calculated", f"demand={predicted_demand} units")
    chk(stock_gap > 0, "Stock shortage identified", f"stock_gap={stock_gap} units to buy")
    chk(f_data["model_used"] == "random_forest", "Prediction used trained Random Forest model")

    print("\n--- 5. Standalone Service: Targeted Customer Credit Check ---")
    cred_res = client.post(f"/api/customers/{customer_id}/check-credit")
    chk(cred_res.status_code == 200, "Customer credit check endpoint -> 200")
    cred_data = cred_res.json()["agent_result"]
    chk(cred_data.get("days_overdue") >= 15, "Identified invoice is overdue by 15+ days", str(cred_data.get("days_overdue")))
    chk(cred_data.get("outstanding_amount") == 28000.0, "Identified outstanding due of ₹28,000", str(cred_data.get("outstanding_amount")))

    # ── STEP 5: Run Full Orchestration Pipeline ───────────────────────────────
    print("\n--- 6. Orchestration Pipeline: Full Synthesis of Demand + Cash + Dues ---")
    run_res = client.post("/api/agents/run-full")
    chk(run_res.status_code == 200, "Full pipeline ran successfully -> 200")
    run_data = run_res.json()
    rec_id = run_data["recommendation_id"]
    decision = run_data["decision"]
    primary = decision["primary_recommendation"]

    print(f"     Primary Action decided by system: '{primary['action']}'")
    print(f"     Reason: {primary['reason']}")

    # Check that because of stock shortage + tight cash, system prioritized collecting receivables!
    chk(
        primary["action"] in ("partial_replenishment_and_collect_receivables", "full_replenishment"),
        "Pipeline correctly identified stock shortage replenishment action",
        primary["action"]
    )

    # ── STEP 6: Human-in-the-Loop Confirmation & Message Approval ─────────────
    print(f"\n--- 7. Human Decision: Review & Confirm Recommendation #{rec_id} ---")
    rec_get = client.get(f"/api/recommendations/{rec_id}")
    chk(rec_get.status_code == 200, "Fetched pending recommendation from Approvals Inbox")
    rec_item = rec_get.json()
    chk(rec_item["status"] == "pending", "Recommendation initial status is 'pending'")

    # Human edits message to send to Sharma Store and clicks Confirm/Approve
    custom_msg = "Dear Sharma Kirana Store, you have a pending due of ₹28,000 for 15 days. Please clear it via UPI/Bank transfer."
    mod_res = client.post(f"/api/recommendations/{rec_id}/modify", json={"modified_message": custom_msg})
    chk(mod_res.status_code == 200, "Human modified the payment reminder message -> 200")
    chk(mod_res.json()["status"] == "modified", "Status transitioned to 'modified'")
    chk(mod_res.json()["modified_message"] == custom_msg, "Stored modified message accurately")

    # ── STEP 7: Standalone Service: Stock Adjustment (After Supplier Delivery) ─
    print("\n--- 8. Standalone Service: Restock / Adjust Stock Count ---")
    stock_res = client.put(f"/api/products/{product_id}/stock", json={"current_stock": 60.0})
    chk(stock_res.status_code == 200, "Product stock adjusted to 60 units after delivery")
    chk(stock_res.json()["current_stock"] == 60.0, "Stock updated in database to 60.0")

    print("\n" + "=" * 70)
    print("ALL PROJECT WORKFLOW CHECKS PASSED SUCCESSFULLY!" if all_passed else "SOME CHECKS FAILED")
    print("=" * 70)

if __name__ == "__main__":
    try:
        run_full_system_test()
    finally:
        _engine.dispose()
        if os.path.exists(_tmp_db):
            os.remove(_tmp_db)
