"""Quick Phase 1 API verification script."""
import requests

base = 'http://localhost:8000'

# Test 1: Root
r = requests.get(f'{base}/')
assert r.status_code == 200, f'Root failed: {r.status_code}'
print('1. Root OK:', r.json()['status'])

# Test 2: Products list (existing functionality)
r = requests.get(f'{base}/api/products')
assert r.status_code == 200, f'Products failed: {r.status_code}'
products = r.json()
print(f'2. Products OK: {len(products)} products returned')

# Test 3: Dashboard summary (existing functionality)
r = requests.get(f'{base}/api/dashboard/summary')
assert r.status_code == 200, f'Dashboard failed: {r.status_code}'
dashboard = r.json()
print(f'3. Dashboard OK: currency={dashboard["currency"]}')

# Test 4: Settings (now has new fields)
r = requests.get(f'{base}/api/settings')
assert r.status_code == 200, f'Settings failed: {r.status_code}'
settings = r.json()
print(f'4. Settings OK: autonomous_mode={settings.get("autonomous_mode")}, safety_stock_days={settings.get("safety_stock_days")}')

# Test 5: Recommendations list (now with new entity fields)
r = requests.get(f'{base}/api/recommendations')
assert r.status_code == 200, f'Recommendations failed: {r.status_code}'
recs = r.json()
print(f'5. Recommendations OK: {len(recs)} records')
if recs:
    rec = recs[0]
    print(f'   module={rec.get("module")}, entity_type={rec.get("entity_type")}')

# Test 6: Sales list (existing functionality)
r = requests.get(f'{base}/api/sales')
assert r.status_code == 200, f'Sales failed: {r.status_code}'
print(f'6. Sales OK: {len(r.json())} sales records')

# Test 7: Customers list
r = requests.get(f'{base}/api/customers')
assert r.status_code == 200
print(f'7. Customers OK: {len(r.json())} customers')

# Test 8: Expenses list
r = requests.get(f'{base}/api/expenses')
assert r.status_code == 200
print(f'8. Expenses OK: {len(r.json())} records')

# Test 9: Recommendations analytics
r = requests.get(f'{base}/api/recommendations/analytics')
assert r.status_code == 200
analytics = r.json()
print(f'9. Analytics OK: total={analytics["total_count"]}, pending={analytics["pending_count"]}')

# Test 10: Settings PATCH with new autonomous_mode field
r = requests.put(f'{base}/api/settings', json={'autonomous_mode': False})
assert r.status_code == 200
updated = r.json()
assert 'autonomous_mode' in updated
print(f'10. Settings Update OK: autonomous_mode field present={("autonomous_mode" in updated)}')

print()
print('ALL PHASE 1 VERIFICATION TESTS PASSED')
