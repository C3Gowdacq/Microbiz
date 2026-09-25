"""
Phase 2 live API integration test.
Verifies that recording a sale via the API creates an InventoryEvent.
"""
import requests
import sqlite3
import os

base = 'http://localhost:8000'
db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'microbizai.db')
db_path = os.path.abspath(db_path)

# Get a product to test with
r = requests.get(f'{base}/api/products')
products = r.json()
assert len(products) > 0, "No products in DB"

# Find a product with stock > 1
product = next((p for p in products if p['current_stock'] >= 1), None)
assert product is not None, "No product with stock >= 1"

product_id = product['id']
stock_before = product['current_stock']
print(f"Testing with: {product['name']} (stock={stock_before})")

# Count inventory events BEFORE the sale
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM inventory_events WHERE product_id=?", (product_id,))
events_before = c.fetchone()[0]

# Record a sale of 1 unit
r = requests.post(f'{base}/api/sales', json={
    'product_id': product_id,
    'quantity': 1.0,
    'unit_price': product['selling_price'],
})
assert r.status_code == 201, f"Sale failed: {r.status_code} - {r.text}"
sale = r.json()
print(f"Sale recorded: id={sale['id']}, total={sale['total_amount']}")

# Verify stock decreased
r2 = requests.get(f'{base}/api/products/{product_id}')
updated_product = r2.json()
expected_stock = round(stock_before - 1.0, 4)
assert abs(updated_product['current_stock'] - expected_stock) < 0.01, (
    f"Stock not decremented: before={stock_before}, after={updated_product['current_stock']}"
)
print(f"Stock decremented: {stock_before} -> {updated_product['current_stock']}")

# Verify InventoryEvent was created
c.execute("SELECT COUNT(*) FROM inventory_events WHERE product_id=?", (product_id,))
events_after = c.fetchone()[0]
assert events_after == events_before + 1, (
    f"InventoryEvent not created: before={events_before}, after={events_after}"
)

# Get the new event
c.execute(
    "SELECT event_type, quantity_before, quantity_change, quantity_after FROM inventory_events "
    "WHERE product_id=? ORDER BY id DESC LIMIT 1",
    (product_id,)
)
event = c.fetchone()
print(f"InventoryEvent: type={event[0]}, before={event[1]}, change={event[2]}, after={event[3]}")

assert event[0] == "SALE"
assert event[1] == stock_before
assert event[2] == -1.0
assert abs(event[3] - expected_stock) < 0.01

# Verify AuditLog was created
c.execute(
    "SELECT action, actor_type FROM audit_logs WHERE entity_id=? ORDER BY id DESC LIMIT 1",
    (product_id,)
)
log = c.fetchone()
assert log is not None, "AuditLog not created"
assert log[0] == "STOCK_DECREASED"
assert log[1] == "SYSTEM"
print(f"AuditLog: action={log[0]}, actor={log[1]}")

conn.close()

print()
print("PHASE 2 LIVE API INTEGRATION TEST PASSED")
print("- Sale creates InventoryEvent atomically")
print("- InventoryEvent records correct before/change/after values")
print("- AuditLog entry created with correct actor and action")
