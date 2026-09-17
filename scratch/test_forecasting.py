"""
scratch/test_forecasting.py -- Automated test suite for dedicated Sales Forecasting.

Verifies:
  1. POST /api/products/{id}/forecast -> Generates decoupled forecast without creating recommendations
  2. GET /api/products/{id}/forecasts -> Retrieves history with compute_forecast_accuracy
  3. POST /api/forecasts/{id}/act with "trigger_inventory_check" -> Creates recommendation & sets status='acted_on'
  4. POST /api/forecasts/{id}/act with "dismiss" -> Sets status='dismissed'
  5. POST /api/forecasts/{id}/act with "adjust_stock" -> Sets current_stock & sets status='acted_on'
"""

import os
import sys
import tempfile
from datetime import date, timedelta

# Ensure root directory is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create isolated test SQLite database
_tmp_db = os.path.join(tempfile.gettempdir(), "microbizai_forecast_test.db")
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

from fastapi import FastAPI
from backend.app.routers import products, sales, forecasts, agents
from backend.app.database import get_db

_app = FastAPI(title="MicroBizAI Forecast Test App")
_app.dependency_overrides[get_db] = _get_db
_app.include_router(products.router)
_app.include_router(sales.router)
_app.include_router(forecasts.router)
_app.include_router(agents.router)

from fastapi.testclient import TestClient
client = TestClient(_app, raise_server_exceptions=True)

all_passed = True

def chk(condition: bool, label: str, detail: str = ""):
    global all_passed
    tag = "[PASS]" if condition else "[FAIL]"
    suffix = f"  ({detail})" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    if not condition:
        all_passed = False
    return condition


def run_tests():
    global all_passed
    print("=" * 65)
    print("=== Dedicated Sales Forecasting Test Suite ===")
    print("=" * 65)

    # ── 1. Create a Product & Sales History ────────────────────────────────────
    print("\n--- 1. Setup Product & Sales ---")
    p_res = client.post("/api/products", json={
        "sku": "CABLE-FC-01",
        "name": "Braided USB-C Fast Cable",
        "selling_price": 15.00,
        "cost_price": 5.00,
        "current_stock": 50.0,
        "reorder_level": 40.0,
        "safety_stock": 10.0,
        "lead_time_days": 4,
        "store_type": "a",
        "assortment": "a",
        "competition_distance": 500.0,
        "promo_active": True,
    })
    chk(p_res.status_code == 201, "Product created with 201")
    product_id = p_res.json()["id"]

    # Record a past sale of 45 units -> leaves current_stock = 5.0
    twenty_days_ago = str(date.today() - timedelta(days=20))
    s_res = client.post("/api/sales", json={
        "product_id": product_id,
        "quantity": 45.0,
        "unit_price": 15.0,
        "sale_date": twenty_days_ago,
    })
    chk(s_res.status_code == 201, "Sale recorded successfully")

    # ── 2. Run Decoupled Forecast (No Recommendation Created) ─────────────────
    print("\n--- 2. POST /api/products/{id}/forecast (Decoupled Forecast) ---")
    f_res = client.post(f"/api/products/{product_id}/forecast", json={"horizon_days": 7})
    chk(f_res.status_code == 201, "Forecast generated with 201")
    f_data = f_res.json()
    forecast_id_1 = f_data["id"]

    chk(f_data["horizon_days"] == 7, "Horizon is 7 days", str(f_data["horizon_days"]))
    chk(f_data["predicted_sales"] > 0, "Predicted sales is positive", str(f_data["predicted_sales"]))
    chk(f_data["model_used"] == "random_forest", "Model used is trained random_forest", f_data["model_used"])
    chk(f_data["current_stock"] == 5.0, "Current stock matches product", str(f_data["current_stock"]))
    chk(f_data["stock_gap_preview"] > 0, "Stock gap preview computed", str(f_data["stock_gap_preview"]))
    chk(f_data["status"] == "active", "Forecast status is 'active'", f_data["status"])

    # Verify no recommendations were automatically created
    with _Session() as session:
        from backend.app.models import Recommendation
        rec_count = session.query(Recommendation).count()
        chk(rec_count == 0, "No recommendations automatically created by forecasting alone (Decoupled)", f"count={rec_count}")

    # ── 3. Test Forecast History & Accuracy ───────────────────────────────────
    print("\n--- 3. GET /api/products/{id}/forecasts (History & Accuracy) ---")
    hist_res = client.get(f"/api/products/{product_id}/forecasts")
    chk(hist_res.status_code == 200, "Forecast history retrieved with 200")
    hist_items = hist_res.json()
    chk(len(hist_items) == 1, "History contains 1 item", f"len={len(hist_items)}")
    chk(hist_items[0]["id"] == forecast_id_1, "History item matches forecast id")
    chk("accuracy_note" in hist_items[0], "Accuracy note included in history", hist_items[0].get("accuracy_note"))

    # ── 4. Act on Forecast 1: "trigger_inventory_check" ───────────────────────
    print("\n--- 4. POST /api/forecasts/{id}/act -> 'trigger_inventory_check' ---")
    act_res = client.post(f"/api/forecasts/{forecast_id_1}/act", json={"action": "trigger_inventory_check"})
    chk(act_res.status_code == 200, "Act on forecast with 200")
    act_data = act_res.json()
    chk(act_data["status"] == "acted_on", "Forecast status updated to 'acted_on'", act_data["status"])
    chk(act_data["recommendation_id"] is not None, "Recommendation created from explicit action", str(act_data["recommendation_id"]))

    with _Session() as session:
        rec_count_after = session.query(Recommendation).count()
        chk(rec_count_after == 1, "1 Recommendation now exists in database", f"count={rec_count_after}")

    # ── 5. Run Forecast 2 and Act: "dismiss" ───────────────────────────────────
    print("\n--- 5. Run Forecast 2 & Dismiss ---")
    f_res_2 = client.post(f"/api/products/{product_id}/forecast", json={"horizon_days": 14})
    chk(f_res_2.status_code == 201, "Second forecast created with 201")
    forecast_id_2 = f_res_2.json()["id"]

    dismiss_res = client.post(f"/api/forecasts/{forecast_id_2}/act", json={"action": "dismiss"})
    chk(dismiss_res.status_code == 200, "Dismiss action succeeded with 200")
    chk(dismiss_res.json()["status"] == "dismissed", "Forecast status is 'dismissed'", dismiss_res.json()["status"])

    # Verify no new recommendation was created by dismissing
    with _Session() as session:
        rec_count_after_dismiss = session.query(Recommendation).count()
        chk(rec_count_after_dismiss == 1, "No extra recommendation created by dismiss action", f"count={rec_count_after_dismiss}")

    # ── 6. Run Forecast 3 and Act: "adjust_stock" ──────────────────────────────
    print("\n--- 6. Run Forecast 3 & Adjust Stock Manually ---")
    f_res_3 = client.post(f"/api/products/{product_id}/forecast", json={"horizon_days": 30})
    chk(f_res_3.status_code == 201, "Third forecast created with 201")
    forecast_id_3 = f_res_3.json()["id"]

    adj_res = client.post(f"/api/forecasts/{forecast_id_3}/act", json={
        "action": "adjust_stock",
        "stock_adjustment": 50.0,
    })
    chk(adj_res.status_code == 200, "Adjust stock action succeeded with 200")
    chk(adj_res.json()["status"] == "acted_on", "Forecast status is 'acted_on'")
    chk(adj_res.json()["current_stock"] == 50.0, "Product stock updated to 50.0", str(adj_res.json()["current_stock"]))

    # Check product stock directly
    p_check = client.get(f"/api/products/{product_id}").json()
    chk(p_check["current_stock"] == 50.0, "Product GET confirms stock is 50.0", str(p_check["current_stock"]))

    # Cleanup temp database
    _engine.dispose()
    if os.path.exists(_tmp_db):
        try:
            os.remove(_tmp_db)
        except Exception:
            pass

    print("\n" + "=" * 65)
    if all_passed:
        print("ALL SALES FORECASTING TESTS PASSED!")
    else:
        print("SOME TESTS FAILED -- see above")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
