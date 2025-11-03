# Sprint 3: Complex Endpoints Migration Guide
**Date:** November 2, 2025
**Purpose:** Detailed planning and context for migrating complex endpoints
**For:** Auth refactor agent

---

## 📋 Overview

### Sprint 3 Scope
**Target:** 19 complex endpoints
**Types:**
- Path parameters (2 endpoints)
- Query parameters (16+ endpoints)
- Body parameters (1 endpoint)

**Complexity Factors:**
1. Multiple parameter types (Query, Path, Body)
2. Parameter order matters (`user` must be LAST)
3. Optional vs required parameters
4. Default values preservation
5. Type validation (Pydantic models)

---

## 🎯 Critical Rules for Sprint 3

### Rule 1: Parameter Order
**FastAPI dependency injection order matters!**

```python
# ✅ CORRECT ORDER:
async def endpoint(
    path_param: str,                          # 1. Path parameters first
    query_param: str = Query(...),            # 2. Query parameters second
    body: MyModel,                             # 3. Body parameters third
    user: dict = Depends(require_auth)         # 4. Auth dependency LAST
):
```

```python
# ❌ WRONG ORDER (will break):
async def endpoint(
    user: dict = Depends(require_auth),        # ❌ Auth first
    path_param: str,                           # ❌ Path after dependency
):
```

### Rule 2: Preserve All Existing Behavior
- Keep all Query defaults
- Keep all validation rules
- Keep all parameter descriptions
- Only add auth dependency

### Rule 3: Import Management
```python
from fastapi import Depends, Query, Path, Body
from app.auth.dependencies import require_auth
```

---

## 📊 Complete Endpoint Inventory

### Category 1: Path Parameters (2 endpoints)

#### 1.1 DELETE /api/alerts/{alert_id}
**Location:** Line 2801
**Status:** ❌ NOT MIGRATED (still uses old pattern)

**Current Signature:**
```python
@app.delete("/api/alerts/{alert_id}")
async def delete_alert(request: Request, alert_id: str):
    user = await get_current_user(request)  # OLD PATTERN
    if not user:
        raise HTTPException(status_code=401, ...)
```

**Target Signature:**
```python
@app.delete("/api/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,                           # Path parameter first
    user: dict = Depends(require_auth)       # Auth dependency last
):
    # AUTH_STATUS: MIGRATED - Sprint 3
    # Remove old auth code (lines 2806-2811)
```

**Complexity:** Low
- Only 1 path parameter
- No query or body parameters
- Straightforward migration

**Testing:**
```bash
# Should fail with 401
curl -X DELETE http://localhost:5000/api/alerts/123e4567-e89b-12d3-a456-426614174000

# Should work with auth
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/alerts/123e4567-e89b-12d3-a456-426614174000
```

---

#### 1.2 GET /api/quotes/{symbol}
**Location:** Line 3727
**Status:** ❌ NOT MIGRATED (still uses old pattern)

**Current Signature:**
```python
@app.get("/api/quotes/{symbol}")
async def get_quote(symbol: str, request: Request):
    user = await get_current_user(request)  # OLD PATTERN
    if not user:
        raise HTTPException(status_code=401, ...)
```

**Target Signature:**
```python
@app.get("/api/quotes/{symbol}")
async def get_quote(
    symbol: str,                             # Path parameter first
    user: dict = Depends(require_auth)       # Auth dependency last
):
    # AUTH_STATUS: MIGRATED - Sprint 3
    # Remove old auth code (lines 3731-3736)
```

**Complexity:** Low
- Only 1 path parameter
- No query or body parameters
- Straightforward migration

**Testing:**
```bash
# Should fail with 401
curl http://localhost:5000/api/quotes/AAPL

# Should work with auth
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/quotes/AAPL
```

---

### Category 2: Query Parameters (16+ endpoints)

#### 2.1 GET /api/metrics/{portfolio_id}
**Location:** Line 1566
**Status:** ❌ NOT MIGRATED

**Current Signature:**
```python
@app.get("/api/metrics/{portfolio_id}")
async def get_portfolio_metrics(portfolio_id: str):
    # No auth check! Public endpoint
```

**Action:** SKIP - No auth needed (metrics endpoint)

---

#### 2.2 GET /api/holdings
**Location:** Line 1741
**Status:** ✅ MIGRATED (has AUTH_STATUS marker)

**Already Done - Verify Correctness:**
```python
async def get_holdings(
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user: dict = Depends(require_auth)
):
```

**Verification:**
- ✅ Query parameters first
- ✅ Auth dependency last
- ✅ All defaults preserved

---

#### 2.3 GET /api/transactions
**Location:** Line 1895
**Status:** ✅ MIGRATED (has AUTH_STATUS marker)

**Already Done - Verify Correctness:**
```python
async def get_transactions(
    portfolio_id: str = Query(..., description="Portfolio ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    user: dict = Depends(require_auth)
):
```

**Verification:**
- ✅ Query parameters first
- ✅ Auth dependency last
- ✅ All defaults and descriptions preserved

---

#### 2.4 GET /api/optimizer/proposals
**Location:** Line 4038
**Status:** ✅ MIGRATED

**Already Done:**
```python
async def get_optimizer_proposals(
    portfolio_id: Optional[str] = Query(None),
    user: dict = Depends(require_auth)
):
```

---

#### 2.5 GET /api/optimizer/analysis
**Location:** Line 4135
**Status:** ✅ MIGRATED

**Already Done:**
```python
async def get_optimizer_analysis(
    portfolio_id: Optional[str] = Query(None),
    user: dict = Depends(require_auth)
):
```

---

#### 2.6 GET /api/ratings/buffett
**Location:** Line 4252
**Status:** ✅ MIGRATED

**Already Done:**
```python
async def get_buffett_ratings(
    portfolio_id: Optional[str] = Query(None),
    user: dict = Depends(require_auth)
):
```

---

#### 2.7 GET /api/ai/insights
**Location:** Line 4450
**Status:** ✅ MIGRATED

**Already Done:**
```python
async def get_ai_insights(
    portfolio_id: Optional[str] = Query(None),
    insight_type: Optional[str] = Query("general"),
    user: dict = Depends(require_auth)
):
```

---

#### 2.8 GET /api/corporate-actions
**Location:** Line 4536
**Status:** ✅ MIGRATED

**Already Done:**
```python
async def get_corporate_actions(
    portfolio_id: Optional[str] = Query(None),
    days_ahead: int = Query(30, ge=1, le=365),
    user: dict = Depends(require_auth)
):
```

---

#### 2.9 GET /api/market/quotes
**Location:** Line 4874
**Status:** ✅ MIGRATED

**Already Done:**
```python
async def get_market_quotes(
    symbols: str = Query(default=None, description="Comma-separated list of symbols"),
    user: dict = Depends(require_auth)
):
```

---

#### 2.10 GET /api/scenarios
**Location:** Line 4689
**Status:** ❌ NOT MIGRATED

**Current Signature:**
```python
@app.get("/api/scenarios")
async def get_scenarios(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
):
    # No auth check - likely needs it
```

**Target Signature:**
```python
@app.get("/api/scenarios")
async def get_scenarios(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user: dict = Depends(require_auth)
):
    # AUTH_STATUS: MIGRATED - Sprint 3
```

---

### Category 3: Body Parameters (1+ endpoints)

#### 3.1 POST /api/alerts
**Location:** Line 1982
**Status:** ❌ NOT MIGRATED (still uses old pattern)

**Current Signature:**
```python
@app.post("/api/alerts")
async def create_alert(request: Request, alert_config: AlertConfig):
    user = await get_current_user(request)  # OLD PATTERN
    if not user:
        raise HTTPException(status_code=401, ...)
```

**Target Signature:**
```python
@app.post("/api/alerts")
async def create_alert(
    alert_config: AlertConfig,               # Body parameter first
    user: dict = Depends(require_auth)       # Auth dependency last
):
    # AUTH_STATUS: MIGRATED - Sprint 3
    # Remove old auth code (lines 1987-1992)
```

**Complexity:** Medium
- Pydantic model for body
- Need to preserve AlertConfig type
- Straightforward once you understand order

**Testing:**
```bash
# Should fail with 401
curl -X POST -H "Content-Type: application/json" \
  -d '{"type":"price","symbol":"AAPL","threshold":150}' \
  http://localhost:5000/api/alerts

# Should work with auth
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"type":"price","symbol":"AAPL","threshold":150}' \
  http://localhost:5000/api/alerts
```

---

## ⚠️ Potential Pitfalls & How to Avoid

### Pitfall 1: Wrong Parameter Order
**Problem:** Auth dependency not last
**Impact:** FastAPI will raise validation errors
**Solution:** Always put `user: dict = Depends(require_auth)` as LAST parameter

**Example:**
```python
# ❌ WRONG - Auth not last
async def endpoint(
    user: dict = Depends(require_auth),
    query_param: str = Query(None)
):

# ✅ CORRECT - Auth last
async def endpoint(
    query_param: str = Query(None),
    user: dict = Depends(require_auth)
):
```

---

### Pitfall 2: Removing Request Parameter Prematurely
**Problem:** Removing `Request` before migrating all usages
**Impact:** Other code may still reference request object
**Solution:** Check for any uses of `request` variable in endpoint body

**Example:**
```python
# Before migration
async def endpoint(request: Request):
    user = await get_current_user(request)
    ip = request.client.host  # ⚠️ Still using request!

# After migration - keep request if needed
async def endpoint(
    request: Request,  # Keep if used elsewhere
    user: dict = Depends(require_auth)
):
    ip = request.client.host  # ✅ Still works
```

---

### Pitfall 3: Forgetting AUTH_STATUS Marker
**Problem:** No way to track migration progress
**Impact:** Can't tell what's done
**Solution:** Always add comment after migration

```python
async def endpoint(user: dict = Depends(require_auth)):
    # AUTH_STATUS: MIGRATED - Sprint 3
    # ^^ Add this comment!
```

---

### Pitfall 4: Not Testing Both Success and Failure
**Problem:** Only testing authenticated case
**Impact:** 401 errors may not work
**Solution:** Test both cases for every endpoint

```bash
# Test 1: Should fail with 401
curl http://localhost:5000/api/endpoint

# Test 2: Should succeed with 200
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/endpoint
```

---

### Pitfall 5: Breaking Default Parameter Values
**Problem:** Changing Query defaults during migration
**Impact:** API behavior changes
**Solution:** Copy defaults exactly

**Example:**
```python
# ❌ WRONG - Lost default value
async def endpoint(
    page: int = Query(1),      # Lost ge=1, le=1000
    user: dict = Depends(require_auth)
):

# ✅ CORRECT - Preserved all defaults
async def endpoint(
    page: int = Query(1, ge=1, le=1000),  # Kept all constraints
    user: dict = Depends(require_auth)
):
```

---

## 🔍 Endpoints Requiring Special Attention

### High Complexity Endpoints

#### 1. POST /api/scenario (Line 2849)
**Why Complex:**
- Has default parameter
- String parameter with default value
- May have additional query params

**Migration Pattern:**
```python
# Before
async def run_scenario_analysis(
    request: Request,
    scenario: str = "rates_up"
):

# After
async def run_scenario_analysis(
    scenario: str = "rates_up",
    user: dict = Depends(require_auth)
):
```

---

#### 2. Endpoints with Both Path and Query Parameters
**Pattern to use:**
```python
async def endpoint(
    path_param: str,                     # Path first
    query_param: str = Query(None),      # Query second
    user: dict = Depends(require_auth)   # Auth last
):
```

---

## 📝 Migration Checklist for Each Endpoint

### Before Starting
- [ ] Read current endpoint signature
- [ ] Identify all parameters (path, query, body)
- [ ] Note all default values and constraints
- [ ] Check for Request object usage elsewhere

### During Migration
- [ ] Remove `request: Request` parameter (if not used)
- [ ] Remove old auth code (lines with get_current_user)
- [ ] Add `user: dict = Depends(require_auth)` as LAST parameter
- [ ] Verify parameter order: path → query → body → auth
- [ ] Preserve all Query(...) defaults and constraints
- [ ] Add AUTH_STATUS: MIGRATED - Sprint 3 comment

### After Migration
- [ ] Verify syntax (no errors)
- [ ] Test 401 without token
- [ ] Test 200 with token
- [ ] Verify response data unchanged
- [ ] Check for any `request.` references that broke

---

## 🎯 Recommended Migration Order

### Batch 1: Simple Path Parameters (Easy - 30 min)
1. DELETE /api/alerts/{alert_id} (Line 2801)
2. GET /api/quotes/{symbol} (Line 3727)

**Reason:** Only 1 path param each, no query/body complexity

---

### Batch 2: Already Migrated - Verify Only (15 min)
Verify these 8 endpoints are correct:
1. GET /api/holdings (Line 1741)
2. GET /api/transactions (Line 1895)
3. GET /api/optimizer/proposals (Line 4038)
4. GET /api/optimizer/analysis (Line 4135)
5. GET /api/ratings/buffett (Line 4252)
6. GET /api/ai/insights (Line 4450)
7. GET /api/corporate-actions (Line 4536)
8. GET /api/market/quotes (Line 4874)

**Action:** Just review, ensure parameter order is correct

---

### Batch 3: Body Parameters (Medium - 15 min)
1. POST /api/alerts (Line 1982)
2. POST /api/scenario (Line 2849)

**Reason:** Body params need careful handling

---

### Batch 4: Remaining Query Parameter Endpoints (30 min)
Find and migrate any remaining endpoints with Query parameters
- Use grep to find: `Query\(` that don't have AUTH_STATUS
- Migrate in small groups of 3-5

---

## 📊 Current Status Summary

### Confirmed Migrated (8 endpoints)
✅ GET /api/holdings
✅ GET /api/transactions
✅ GET /api/optimizer/proposals
✅ GET /api/optimizer/analysis
✅ GET /api/ratings/buffett
✅ GET /api/ai/insights
✅ GET /api/corporate-actions
✅ GET /api/market/quotes

### Confirmed Not Migrated (4 endpoints)
❌ DELETE /api/alerts/{alert_id}
❌ GET /api/quotes/{symbol}
❌ POST /api/alerts
❌ GET /api/scenarios

### Unknown Status (~7-10 endpoints)
Need to audit remaining query parameter endpoints

---

## 🚨 Critical Reminders

### DO:
✅ Keep parameter order: path → query → body → auth
✅ Preserve all Query defaults and constraints
✅ Add AUTH_STATUS marker
✅ Test both 401 and 200 cases
✅ Remove old auth code

### DON'T:
❌ Put auth dependency before other parameters
❌ Change default values or constraints
❌ Forget to test
❌ Remove Request if used elsewhere
❌ Skip AUTH_STATUS marker

---

## 🔧 Code Templates

### Template 1: Path Parameter Only
```python
@app.delete("/api/resource/{resource_id}")
async def delete_resource(
    resource_id: str,
    user: dict = Depends(require_auth)
):
    # AUTH_STATUS: MIGRATED - Sprint 3
    # ... endpoint logic using resource_id and user
```

### Template 2: Query Parameters
```python
@app.get("/api/resource")
async def get_resource(
    query_param: str = Query(None, description="..."),
    page: int = Query(1, ge=1, le=1000),
    user: dict = Depends(require_auth)
):
    # AUTH_STATUS: MIGRATED - Sprint 3
    # ... endpoint logic
```

### Template 3: Body Parameter
```python
@app.post("/api/resource")
async def create_resource(
    resource_data: ResourceModel,
    user: dict = Depends(require_auth)
):
    # AUTH_STATUS: MIGRATED - Sprint 3
    # ... endpoint logic using resource_data and user
```

### Template 4: Mixed Parameters
```python
@app.post("/api/resource/{resource_id}")
async def update_resource(
    resource_id: str,                     # Path first
    query_param: str = Query(None),       # Query second
    resource_data: ResourceModel,         # Body third
    user: dict = Depends(require_auth)    # Auth LAST
):
    # AUTH_STATUS: MIGRATED - Sprint 3
    # ... endpoint logic
```

---

## 📚 Additional Resources

### FastAPI Dependency Injection Docs
https://fastapi.tiangolo.com/tutorial/dependencies/

### Parameter Order Rules
Path params → Query params → Body params → Dependencies

### Testing Auth
See: AUTH_REFACTOR_CHECKLIST.md lines 139-153

---

**Last Updated:** November 2, 2025
**Status:** Ready for Sprint 3 execution
**Estimated Time:** 1-1.5 hours for complete Sprint 3
