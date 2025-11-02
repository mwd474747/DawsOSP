import httpx
import json

print("Testing critical fixes after architect review...")
print("=" * 50)

base_url = "http://localhost:5000/api"
token = None

# 1. Login
print("1. Testing authentication...")
login_response = httpx.post(f"{base_url}/auth/login", json={
    "email": "michael@dawsos.com",
    "password": "admin123"
})
if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print("   ✅ Authentication successful")
else:
    print(f"   ❌ Auth failed: {login_response.status_code}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# 2. Test patterns/execute (was failing with 422)
print("\n2. Testing /patterns/execute (previously 422)...")
pattern_response = httpx.post(
    f"{base_url}/patterns/execute",
    json={"pattern": "portfolio_overview", "inputs": {"portfolio_id": "test"}},
    headers=headers
)
print(f"   Status: {pattern_response.status_code}")
if pattern_response.status_code == 200:
    print("   ✅ Pattern execution fixed!")
else:
    print(f"   ❌ Still failing: {pattern_response.text[:200]}")

# 3. Test market/quotes without symbols (was 422)
print("\n3. Testing /market/quotes without symbols (previously 422)...")
quotes_response = httpx.get(f"{base_url}/market/quotes", headers=headers)
print(f"   Status: {quotes_response.status_code}")
if quotes_response.status_code == 200:
    data = quotes_response.json()
    if data.get("data", {}).get("quotes"):
        print(f"   ✅ Market quotes fixed! Returned {len(data['data']['quotes'])} default quotes")
    else:
        print("   ⚠️ Endpoint works but no quotes data")
else:
    print(f"   ❌ Still failing: {quotes_response.text[:200]}")

# 4. Test market/quotes with symbols (should still work)
print("\n4. Testing /market/quotes with symbols...")
quotes_response = httpx.get(
    f"{base_url}/market/quotes?symbols=AAPL,GOOGL",
    headers=headers
)
print(f"   Status: {quotes_response.status_code}")
if quotes_response.status_code == 200:
    print("   ✅ Market quotes with symbols works")
else:
    print(f"   ❌ Failed: {quotes_response.text[:200]}")

print("\n" + "=" * 50)
print("Critical fixes validation complete!")
