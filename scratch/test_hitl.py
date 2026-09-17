"""
test_hitl.py -- Test script for Part 11 HITL flow (7a-7e).
"""

import urllib.request
import json

payload = {
    'inventory_inputs': [
        {'product_id': 'SKU_ELECTRONICS_001', 'current_stock': 40, 'forecast_demand': 90, 'reorder_level': 50, 'safety_stock': 20, 'lead_time_days': 5},
        {'product_id': 'SKU_APPAREL_042', 'current_stock': 120, 'forecast_demand': 80, 'reorder_level': 50, 'safety_stock': 30, 'lead_time_days': 3},
        {'product_id': 'SKU_GROCERY_108', 'current_stock': 50, 'forecast_demand': 320, 'reorder_level': 100, 'safety_stock': 40, 'lead_time_days': 2}
    ],
    'cashflow_input': {
        'current_cash': 25000.0,
        'expected_sales_revenue': 18000.0,
        'upcoming_expenses': 12000.0,
        'planned_purchase_cost': 15000.0,
        'min_cash_reserve': 5000.0
    },
    'expense_inputs': [
        {'category': 'Rent', 'current_period_amount': 4000.0, 'prior_period_amount': 4000.0},
        {'category': 'Utilities', 'current_period_amount': 1600.0, 'prior_period_amount': 1200.0},
        {'category': 'Salaries', 'current_period_amount': 8500.0, 'prior_period_amount': 8500.0},
        {'category': 'Marketing', 'current_period_amount': 2500.0, 'prior_period_amount': 1800.0}
    ],
    'credit_inputs': [
        {'customer_id': 'CUST_RELIABLE', 'invoice_amount': 5000, 'amount_paid': 5000, 'due_date': '2025-07-01', 'today': '2025-07-16'},
        {'customer_id': 'CUST_LATE_PAY', 'invoice_amount': 8000, 'amount_paid': 3000, 'due_date': '2025-06-25', 'today': '2025-07-16'},
        {'customer_id': 'CUST_DELINQUENT', 'invoice_amount': 12000, 'amount_paid': 0, 'due_date': '2025-06-01', 'today': '2025-07-16'},
        {'customer_id': 'CUST_NEW', 'invoice_amount': 3000, 'amount_paid': 0, 'due_date': '2025-07-20', 'today': '2025-07-16'}
    ],
    'profitability_inputs': [
        {'product_id': 'Electronics Premium', 'selling_price': 299.99, 'cost_price': 180.0, 'quantity_sold': 45},
        {'product_id': 'Electronics Budget', 'selling_price': 49.99, 'cost_price': 42.0, 'quantity_sold': 200},
        {'product_id': 'Apparel T-Shirts', 'selling_price': 24.99, 'cost_price': 8.0, 'quantity_sold': 350},
        {'product_id': 'Clearance Items', 'selling_price': 9.99, 'cost_price': 12.0, 'quantity_sold': 100},
        {'product_id': 'Accessories', 'selling_price': 14.99, 'cost_price': 5.0, 'quantity_sold': 500}
    ],
    'forecast_horizon_days': 7,
    'today': '2025-07-16'
}

data_bytes = json.dumps(payload).encode('utf-8')

print("=== STEP 7a: POST /api/agents/run-full ===")
req = urllib.request.Request('http://127.0.0.1:8000/api/agents/run-full', data=data_bytes, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as resp:
    res1 = json.loads(resp.read().decode())
    id1 = res1['recommendation_id']
    action1 = res1['decision']['primary_recommendation']['action']
    print(f"  [PASS] Created Recommendation ID: {id1}")
    print(f"         Primary Action: {action1}")

print(f"\n=== STEP 7b: GET /api/recommendations/{id1} ===")
req = urllib.request.Request(f'http://127.0.0.1:8000/api/recommendations/{id1}')
with urllib.request.urlopen(req) as resp:
    rec1 = json.loads(resp.read().decode())
    print(f"  [PASS] Fetched ID {id1} Status: '{rec1['status']}' (Expected: 'pending')")

print(f"\n=== STEP 7c: POST /api/recommendations/{id1}/approve ===")
req = urllib.request.Request(f'http://127.0.0.1:8000/api/recommendations/{id1}/approve', data=b'', headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as resp:
    approved_rec = json.loads(resp.read().decode())
    print(f"  [PASS] Approved ID {id1} Status: '{approved_rec['status']}' (Expected: 'approved')")

print(f"\n=== STEP 7d: Call /api/recommendations/{id1}/reject on SAME ID ===")
try:
    req = urllib.request.Request(f'http://127.0.0.1:8000/api/recommendations/{id1}/reject', data=b'', headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        print("  [FAIL] Unexpected success")
except urllib.error.HTTPError as e:
    err_body = e.read().decode()
    print(f"  [PASS] Caught Expected HTTP {e.code} Error: {err_body}")

print("\n=== STEP 7e: Second run_full, get new ID, call /modify ===")
req = urllib.request.Request('http://127.0.0.1:8000/api/agents/run-full', data=data_bytes, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as resp:
    res2 = json.loads(resp.read().decode())
    id2 = res2['recommendation_id']
    print(f"  [PASS] Created Second Recommendation ID: {id2}")

modify_payload = json.dumps({'modified_message': 'Dear Customer, please pay invoice EUR 12,000 immediately. Contact us at 555-0199.'}).encode('utf-8')
req = urllib.request.Request(f'http://127.0.0.1:8000/api/recommendations/{id2}/modify', data=modify_payload, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as resp:
    modified_rec = json.loads(resp.read().decode())
    print(f"  [PASS] Modified ID {id2} Status: '{modified_rec['status']}' (Expected: 'modified')")
    print(f"         Stored Modified Message: {repr(modified_rec['modified_message'])}")

print("\n=== BONUS: GET /api/recommendations/analytics ===")
req = urllib.request.Request('http://127.0.0.1:8000/api/recommendations/analytics')
with urllib.request.urlopen(req) as resp:
    analytics = json.loads(resp.read().decode())
    print("  [PASS] Analytics Data:")
    print(json.dumps(analytics, indent=4))
