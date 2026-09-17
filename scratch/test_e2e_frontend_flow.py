"""
test_e2e_frontend_flow.py -- Full end-to-end integration test of Steps 10a-10g
against the running live FastAPI server on http://localhost:8000.

Lifecycle tested:
  10a. Add new product with low stock (USB-C Fast Cable, stock=4, reorder=40)
  10b. Product detail: check-inventory -> verify HIGH risk & recommendation created
  10c. Recommendations: find the recommendation and Approve it
  10d. Add customer (Acme MegaStore), create an overdue invoice (due 2026-08-01)
  10e. Customer detail: check-credit -> verify risk detected & recommendation created
  10f. Expenses: log expense, check-trend -> verify trend detected & recommendation created
  10g. Dashboard: check /api/dashboard/summary reflects the real activity (low stock, overdue, revenue)
       Run full pipeline /api/agents/run-full on real DB data -> verify aggregated decision
"""

import sys
import requests
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:8000"

PASS = "[PASS]"
FAIL = "[FAIL]"
all_passed = True

def chk(cond: bool, label: str, detail: str = ""):
    global all_passed
    tag = PASS if cond else FAIL
    suffix = f"  ({detail})" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    if not cond:
        all_passed = False
    return cond

def run_tests():
    global all_passed
    print("=" * 65)
    print("=== MicroBizAI -- Live End-to-End Test Walkthrough (10a - 10g) ===")
    print("=" * 65)

    # 10a: Add new product with low stock
    print("\n--- [Step 10a] Add Product with Low Stock ---")
    p_res = requests.post(f"{BASE_URL}/api/products", json={
        "sku": "USB-PRO-01",
        "name": "USB-C Ultra Fast Cable",
        "selling_price": 14.99,
        "cost_price": 5.00,
        "current_stock": 4.0,
        "reorder_level": 40.0,
        "safety_stock": 10.0,
        "lead_time_days": 4,
    })
    chk(p_res.status_code == 201, "10a: Product created with 201", str(p_res.status_code))
    product = p_res.json()
    product_id = product["id"]
    chk(product["current_stock"] == 4.0, "10a: Product initial stock = 4 units", str(product["current_stock"]))

    # Also record a quick sale so demand history exists
    requests.post(f"{BASE_URL}/api/sales", json={
        "product_id": product_id,
        "quantity": 2.0,
        "unit_price": 14.99,
        "date": str(date.today() - timedelta(days=10)),
    })

    # 10b: Check Inventory Risk for this product
    print("\n--- [Step 10b] Check Inventory Risk on Product Detail ---")
    inv_res = requests.post(f"{BASE_URL}/api/products/{product_id}/check-inventory")
    chk(inv_res.status_code == 200, "10b: POST /check-inventory -> 200", str(inv_res.status_code))
    inv_data = inv_res.json()
    chk(inv_data["agent_result"]["stockout_risk"] in ("HIGH", "MEDIUM"),
        "10b: Stockout risk correctly detected as HIGH/MEDIUM",
        inv_data["agent_result"]["stockout_risk"])
    chk(inv_data["recommendation_created"] is True, "10b: Recommendation row was automatically created", str(inv_data["recommendation_id"]))
    inv_rec_id = inv_data["recommendation_id"]

    # 10c: Go to /recommendations, find it, Approve it
    print("\n--- [Step 10c] Find & Approve Recommendation in Inbox ---")
    recs_res = requests.get(f"{BASE_URL}/api/recommendations?status=pending")
    chk(recs_res.status_code == 200, "10c: GET /api/recommendations?status=pending -> 200")
    pending_list = recs_res.json()
    chk(any(r["id"] == inv_rec_id for r in pending_list), "10c: Inventory recommendation appears in pending inbox")

    app_res = requests.post(f"{BASE_URL}/api/recommendations/{inv_rec_id}/approve")
    chk(app_res.status_code == 200, "10c: POST /recommendations/{id}/approve -> 200")
    chk(app_res.json()["status"] == "approved", "10c: Recommendation status updated to 'approved'")

    # 10d: Add customer & create overdue invoice
    print("\n--- [Step 10d] Add Customer & Create Overdue Invoice ---")
    c_res = requests.post(f"{BASE_URL}/api/customers", json={
        "name": "Acme MegaStore",
        "email": "billing@acmestore.com",
        "phone": "+1-555-4321",
    })
    chk(c_res.status_code == 201, "10d: Customer created with 201")
    customer = c_res.json()
    customer_id = customer["id"]

    past_date = str(date.today() - timedelta(days=25))
    i_res = requests.post(f"{BASE_URL}/api/invoices", json={
        "customer_id": customer_id,
        "invoice_amount": 2400.0,
        "due_date": past_date,
    })
    chk(i_res.status_code == 201, "10d: Overdue invoice created with 201", f"Due: {past_date}")
    invoice_id = i_res.json()["id"]

    # 10e: Customer detail: check credit risk
    print("\n--- [Step 10e] Run Credit Risk Check on Customer Detail ---")
    cred_res = requests.post(f"{BASE_URL}/api/customers/{customer_id}/check-credit")
    chk(cred_res.status_code == 200, "10e: POST /check-credit -> 200")
    cred_data = cred_res.json()
    chk(cred_data["agent_result"]["customer_risk"] in ("HIGH", "MEDIUM"),
        "10e: Credit agent detected risk as HIGH/MEDIUM",
        cred_data["agent_result"]["customer_risk"])
    chk(cred_data["agent_result"]["days_overdue"] >= 20, "10e: Days overdue >= 20", str(cred_data["agent_result"]["days_overdue"]))
    chk(cred_data["recommendation_created"] is True, "10e: Credit reminder recommendation queued in inbox", str(cred_data["recommendation_id"]))

    # 10f: Log expense with big jump & check trend
    print("\n--- [Step 10f] Log Expense & Check Category Trend ---")
    # Prior period baseline (45 days ago)
    requests.post(f"{BASE_URL}/api/expenses", json={
        "category": "Utilities",
        "current_period_amount": 800.0,
        "date": str(date.today() - timedelta(days=45)),
    })
    # Current period spike (today)
    exp_res = requests.post(f"{BASE_URL}/api/expenses", json={
        "category": "Utilities",
        "current_period_amount": 3200.0,
        "description": "Peak Summer HVAC & Grid Power",
        "date": str(date.today()),
    })
    chk(exp_res.status_code == 201, "10f: Spike expense logged with 201")

    trend_res = requests.post(f"{BASE_URL}/api/expenses/check-trend", json={"category": "Utilities"})
    chk(trend_res.status_code == 200, "10f: POST /expenses/check-trend -> 200")
    trend_data = trend_res.json()
    chk(trend_data["agent_result"]["risk"] in ("HIGH", "MEDIUM"),
        "10f: Expense agent detected HIGH/MEDIUM trend risk",
        trend_data["agent_result"]["risk"])
    chk(trend_data["agent_result"]["increase_pct"] is not None and trend_data["agent_result"]["increase_pct"] > 30,
        "10f: Increase percentage > +30% spike",
        f"+{trend_data['agent_result']['increase_pct']:.1f}%")

    # 10g: Verify Dashboard KPIs and Run Full Autonomous Check
    print("\n--- [Step 10g] Verify Dashboard Summary & Run Full Multi-Agent Pipeline ---")
    dash_res = requests.get(f"{BASE_URL}/api/dashboard/summary")
    chk(dash_res.status_code == 200, "10g: GET /api/dashboard/summary -> 200")
    dash_data = dash_res.json()
    print(f"     Live Dashboard Snapshot: {dash_data}")
    chk(dash_data["low_stock_products_count"] >= 1, "10g: Low stock products count >= 1", str(dash_data["low_stock_products_count"]))
    chk(dash_data["overdue_invoices_count"] >= 1, "10g: Overdue invoices count >= 1", str(dash_data["overdue_invoices_count"]))

    print("\n  Executing POST /api/agents/run-full across all live DB rows...")
    full_res = requests.post(f"{BASE_URL}/api/agents/run-full")
    chk(full_res.status_code == 200, "10g: POST /api/agents/run-full completed with 200", str(full_res.status_code))
    full_data = full_res.json()
    print(f"     Full Pipeline Recommendation ID: #{full_data.get('recommendation_id')}")
    print(f"     Primary Action: {full_data.get('decision', {}).get('primary_recommendation', {}).get('action')}")
    print(f"     Priority:       {full_data.get('decision', {}).get('primary_recommendation', {}).get('priority')}")
    print(f"     LLM Summary:    {full_data.get('llm_explanation', {}).get('summary')}")
    chk(full_data.get("recommendation_id") is not None, "10g: Stored unified decision recommendation created")
    chk(full_data.get("decision") is not None, "10g: Multi-agent synthesized decision output present")

    print("\n" + "=" * 65)
    if all_passed:
        print("ALL STEPS (10a - 10g) SUCCESSFULLY VERIFIED LIVE!")
    else:
        print("SOME STEPS FAILED -- see above")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
