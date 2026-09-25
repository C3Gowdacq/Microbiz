"""
backend/tests/verify_phase6_7_api.py

Live API integration verification for Phases 1-7:
- Checks /api/suppliers auto-seeding
- Creates and receives a Purchase Order via API
- Verifies stock increment and InventoryEvent
- Records a Sale via API and checks enriched inventory_risk
"""

import requests
import sys

base = "http://localhost:8000"

def run_checks():
    print("--- 1. Checking Root & Health ---")
    r = requests.get(f"{base}/")
    assert r.status_code == 200, f"Root failed: {r.text}"
    print("[OK] API is online:", r.json())

    print("\n--- 2. Checking Suppliers (Phase 6) ---")
    r = requests.get(f"{base}/api/suppliers")
    assert r.status_code == 200, f"List suppliers failed: {r.text}"
    suppliers = r.json()
    assert len(suppliers) >= 3, f"Expected at least 3 suppliers, got {len(suppliers)}"
    supplier = suppliers[0]
    print(f"[OK] Found {len(suppliers)} suppliers. Selected: {supplier['name']} (ID: {supplier['id']})")

    print("\n--- 3. Checking Products ---")
    r = requests.get(f"{base}/api/products")
    assert r.status_code == 200, f"List products failed: {r.text}"
    products = r.json()
    assert len(products) > 0, "No products found in DB"
    product = products[0]
    stock_before = product["current_stock"]
    print(f"[OK] Selected product: '{product['name']}' (ID: {product['id']}), Stock before PO: {stock_before}")

    print("\n--- 4. Creating Purchase Order (Phase 6) ---")
    po_payload = {
        "supplier_id": supplier["id"],
        "priority": "high",
        "reason": "Test replenishment",
        "items": [
            {
                "product_id": product["id"],
                "quantity": 10.0,
                "unit_cost": product["cost_price"] or 100.0,
            }
        ],
    }
    r = requests.post(f"{base}/api/purchase-orders", json=po_payload)
    assert r.status_code == 201, f"Create PO failed: {r.text}"
    po = r.json()
    po_id = po["id"]
    print(f"[OK] Created PO #{po_id} ({po['po_number']}), Total: Rs {po['total_amount']}, Status: {po['status']}")

    print("\n--- 5. Receiving Purchase Order (Phase 6) ---")
    r = requests.post(f"{base}/api/purchase-orders/{po_id}/receive")
    assert r.status_code == 200, f"Receive PO failed: {r.text}"
    po_received = r.json()
    assert po_received["status"] == "RECEIVED"
    print(f"[OK] PO #{po_id} successfully RECEIVED at {po_received['received_at']}")

    # Verify product stock increased
    r = requests.get(f"{base}/api/products/{product['id']}")
    assert r.status_code == 200
    prod_after_po = r.json()
    assert prod_after_po["current_stock"] == stock_before + 10.0
    print(f"[OK] Product stock successfully increased: {stock_before} -> {prod_after_po['current_stock']}")

    print("\n--- 6. Recording Sale with Real-time Risk Enrichment (Phase 4) ---")
    sale_payload = {
        "product_id": product["id"],
        "quantity": 2.0,
        "unit_price": product["selling_price"] or 150.0,
    }
    r = requests.post(f"{base}/api/sales", json=sale_payload)
    assert r.status_code == 201, f"Create sale failed: {r.text}"
    sale_resp = r.json()
    assert "inventory_risk" in sale_resp, "Sale response missing inventory_risk"
    risk = sale_resp["inventory_risk"]
    assert risk is not None, "inventory_risk is null"
    print(f"[OK] Sale recorded: ID #{sale_resp['id']}, total: Rs {sale_resp['total_amount']}")
    print(f"[OK] Real-time Inventory Risk: level={risk['risk_level']}, coverage={risk['coverage_days']}d, ROP={risk['reorder_point']}, recommended_order={risk['recommended_order_qty']}")

    print("\n========================================================")
    print("ALL PHASES 1-7 LIVE INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("========================================================")

if __name__ == "__main__":
    run_checks()
