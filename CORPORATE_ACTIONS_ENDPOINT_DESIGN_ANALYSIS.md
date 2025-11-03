# Corporate Actions Endpoint Design Analysis

**Date:** November 3, 2025  
**Purpose:** Examine endpoint usage across codebase, identify design issues, and assess breaking change risks  
**Status:** 📋 **PLANNING PHASE** - No code changes

---

## 📊 Executive Summary

After comprehensive analysis of `/api/corporate-actions` endpoint usage across the codebase:

**Findings:**
- ✅ **Isolated Usage** - Only used by UI component (`CorporateActionsPage`)
- ⚠️ **Design Inconsistency** - Doesn't follow pattern of other portfolio endpoints
- ⚠️ **Dual API Structure** - Two separate corporate actions APIs exist (confusing)
- ✅ **No Breaking Risks** - Implementation won't break existing functionality
- ⚠️ **Missing RLS** - Current endpoint doesn't use RLS-enabled connections

**Recommendation:** Implement fix with design improvements to align with existing patterns.

---

## 🔍 Endpoint Usage Analysis

### 1. Current Usage Locations

#### ✅ UI Component Only
**File:** `full_ui.html` lines 10880-10907  
**Component:** `CorporateActionsPage()`

**Usage Pattern:**
```javascript
const response = await axios.get('/api/corporate-actions', {
    params: {
        days_ahead: filterDays,
        portfolio_id: getCurrentPortfolioId()
    },
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

// Expects: response.data.data.actions = [...]
setCorporateActions(response.data.data.actions || []);
```

**Assessment:**
- ✅ **Single Consumer** - Only used by this one UI component
- ✅ **Simple Data Contract** - Expects `response.data.data.actions` array
- ✅ **Defensive Coding** - Uses `|| []` fallback for empty responses
- ✅ **Handles Empty State** - UI already handles empty arrays gracefully

**Impact of Fix:** ✅ **NO BREAKING CHANGES** - UI expects array, will receive array (just populated instead of empty).

---

### 2. No Other Dependencies Found

**Searched For:**
- ❌ No patterns reference corporate actions
- ❌ No agent capabilities reference corporate actions
- ❌ No other services call this endpoint
- ❌ No background jobs depend on it
- ❌ No tests reference it (in current codebase)
- ❌ No documentation that would need updating (beyond fixing the mock data note)

**Assessment:** ✅ **ISOLATED ENDPOINT** - Changes won't break other systems.

---

## ⚠️ Design Issues Identified

### Issue 1: API Route Duplication (Design Inconsistency)

**Problem:** Two separate corporate actions APIs exist:

**1. `/api/corporate-actions` (in `combined_server.py`)**
- **Purpose:** GET upcoming corporate actions for display
- **Method:** GET
- **Status:** Returns empty array (after commit 94cbb01)
- **Auth:** Uses `require_auth` dependency
- **Location:** `combined_server.py` line 4645

**2. `/v1/corporate-actions/*` (in `backend/app/api/routes/corporate_actions.py`)**
- **Purpose:** POST/GET for recording/querying past corporate actions
- **Methods:** POST `/v1/corporate-actions/dividends`, POST `/v1/corporate-actions/splits`, GET `/v1/corporate-actions/dividends`
- **Status:** Fully implemented for recording past events
- **Auth:** Uses `verify_token` dependency (JWT)
- **Location:** Router in `backend/app/api/routes/corporate_actions.py`
- **Registration:** Registered in `backend/app/api/__init__.py` line 66

**Analysis:**
```
/api/corporate-actions          → GET upcoming events (UI display)
/v1/corporate-actions/dividends → POST record past dividend
/v1/corporate-actions/splits    → POST record past split
/v1/corporate-actions/dividends → GET past dividend history
```

**Design Issue:**
- ⚠️ **Inconsistent Naming** - `/api/corporate-actions` vs `/v1/corporate-actions/*`
- ⚠️ **Different Auth Systems** - `require_auth` vs `verify_token` (though they may be equivalent)
- ⚠️ **Separate Locations** - One in `combined_server.py`, one in router module
- ⚠️ **No Clear Separation** - Upcoming vs Past events not clearly distinguished in URL structure

**Impact:** ⚠️ **CONFUSION** - Developers might not know which endpoint to use. However, **NOT A BREAKING ISSUE** - they serve different purposes.

---

### Issue 2: Missing RLS Pattern (Security Concern)

**Current Implementation:**
```python
@app.get("/api/corporate-actions", response_model=SuccessResponse)
async def get_corporate_actions(
    portfolio_id: Optional[str] = Query(None),
    days_ahead: int = Query(30, ge=1, le=365),
    user: dict = Depends(require_auth)  # ✅ Auth present
):
    try:
        # ⚠️ Doesn't use RLS-enabled connection
        response = {
            "portfolio_id": portfolio_id,
            "actions": [],  # Empty - no DB query
            ...
        }
        return SuccessResponse(data=response)
```

**Comparison with Other Endpoints:**
```python
# Example: /api/portfolio endpoint (line 1576)
@app.get("/api/portfolio")
async def get_portfolio(user: dict = Depends(require_auth)):
    # ✅ Uses pattern orchestrator (which handles RLS internally)
    pattern_result = await execute_pattern_orchestrator(...)

# Example: /api/holdings endpoint (line 1717)
@app.get("/api/holdings")
async def get_holdings(user: dict = Depends(require_auth)):
    # ✅ Uses pattern orchestrator (which handles RLS internally)
    pattern_result = await execute_pattern_orchestrator(...)

# Example: /v1/corporate-actions/dividends (from router)
@router.post("/dividends")
async def record_dividend(..., claims: dict = Depends(verify_token)):
    # ✅ Uses RLS-enabled connection
    async with get_db_connection_with_rls(str(user_id)) as conn:
        service = CorporateActionsService(conn)
        ...
```

**Design Issue:**
- ⚠️ **No RLS Enforcement** - Current endpoint doesn't query database, so RLS not needed yet
- ⚠️ **Will Need RLS** - When we implement real functionality, must use RLS
- ⚠️ **Inconsistent with Router** - `/v1/corporate-actions/*` endpoints properly use RLS

**Impact:** ⚠️ **FUTURE SECURITY RISK** - Must ensure RLS when implementing real functionality. Not breaking now, but critical for implementation.

---

### Issue 3: Portfolio ID Parameter Handling

**Current Implementation:**
```python
portfolio_id: Optional[str] = Query(None),  # ⚠️ Optional, but required for functionality
```

**Comparison with Other Endpoints:**
```python
# Similar endpoints with Optional portfolio_id:
@app.get("/api/optimizer/proposals")
async def get_optimizer_proposals(
    portfolio_id: Optional[str] = Query(None),  # Optional
    ...
):
    # ⚠️ Some endpoints handle None, some don't

@app.get("/api/ai/insights")
async def get_ai_insights(
    portfolio_id: Optional[str] = Query(None),  # Optional
    ...
):
    # ⚠️ Some endpoints handle None, some don't
```

**Design Issue:**
- ⚠️ **Optional but Required** - `portfolio_id` is Optional but actually required for portfolio-specific data
- ⚠️ **No Validation** - Current implementation doesn't validate portfolio_id is provided
- ⚠️ **Inconsistent** - Some endpoints require it, some make it optional

**Impact:** ⚠️ **CLARITY ISSUE** - Should be required parameter, not optional. Not breaking, but inconsistent.

---

### Issue 4: Response Structure Consistency

**Current Response:**
```python
{
    "portfolio_id": portfolio_id,
    "time_horizon_days": days_ahead,
    "actions": [],
    "summary": {...},
    "notifications": {...},
    "last_updated": datetime.utcnow().isoformat(),
    "metadata": {...}
}
```

**Comparison with Other Endpoints:**
```python
# Most endpoints return SuccessResponse with simple data:
return SuccessResponse(data={"alerts": []})  # Simple structure

# Some endpoints return pattern results:
return SuccessResponse(data=pattern_result["data"])  # Complex nested structure
```

**Design Issue:**
- ✅ **Good Metadata** - Includes summary, notifications, last_updated
- ⚠️ **Nested Structure** - Multiple levels of nesting (data.actions, data.summary, data.notifications)
- ✅ **Consistent with UI** - UI expects this structure (no breaking change)

**Impact:** ✅ **NO ISSUE** - Structure is appropriate for UI needs.

---

## 🔍 Pattern Comparison Analysis

### How Other Portfolio Endpoints Work

**Pattern 1: Pattern Orchestrator (Most Common)**
```python
# /api/portfolio, /api/holdings, /api/transactions
@app.get("/api/portfolio")
async def get_portfolio(user: dict = Depends(require_auth)):
    # ✅ Uses pattern orchestrator
    pattern_result = await execute_pattern_orchestrator(
        "portfolio_overview",
        {"portfolio_id": portfolio_id},
        user_id=user.get("id")
    )
    # Pattern orchestrator handles RLS internally
    return SuccessResponse(data=pattern_result["data"])
```

**Pattern 2: Direct Service with RLS (Router Endpoints)**
```python
# /v1/corporate-actions/dividends, /v1/trades/*
@router.post("/dividends")
async def record_dividend(..., claims: dict = Depends(verify_token)):
    user_id = get_user_id_from_claims(claims)
    # ✅ Uses RLS-enabled connection
    async with get_db_connection_with_rls(str(user_id)) as conn:
        service = CorporateActionsService(conn)
        result = await service.record_dividend(...)
    return DividendResponse(**result)
```

**Pattern 3: Direct Query with RLS (Legacy)**
```python
# Some older endpoints
@app.get("/api/holdings")
async def get_holdings(user: dict = Depends(require_auth)):
    # ⚠️ Uses execute_query_safe (may not use RLS properly)
    result = await execute_query_safe(query, ...)
    return SuccessResponse(data=result)
```

**Current Corporate Actions Endpoint:**
```python
# /api/corporate-actions
@app.get("/api/corporate-actions")
async def get_corporate_actions(..., user: dict = Depends(require_auth)):
    # ⚠️ No database query, no RLS needed yet
    return SuccessResponse(data={"actions": []})
```

**Recommendation for Fix:**
- **Option A (Recommended):** Use Pattern Orchestrator
  - ✅ Consistent with other portfolio endpoints
  - ✅ Automatic RLS handling
  - ✅ Can add agent capabilities later
  - ⚠️ Requires creating corporate actions pattern first

- **Option B:** Use Direct Service with RLS (like router endpoints)
  - ✅ Consistent with `/v1/corporate-actions/*` router
  - ✅ Direct database access
  - ✅ Full control over query logic
  - ⚠️ Need to ensure RLS properly

- **Option C:** Hybrid - Direct Service but in `combined_server.py`
  - ✅ Quick implementation
  - ⚠️ Inconsistent with router pattern
  - ⚠️ Need to ensure RLS properly

---

## ⚠️ Breaking Change Risk Assessment

### Risk Analysis Matrix

| Change Type | Current State | Proposed State | Breaking Risk | Mitigation |
|------------|---------------|----------------|---------------|------------|
| **Response Structure** | Empty array `actions: []` | Populated array `actions: [...]` | ✅ **NONE** | UI already handles arrays, expects array |
| **Response Fields** | `summary: {...}` with zeros | `summary: {...}` with real counts | ✅ **NONE** | UI doesn't depend on zero values |
| **Metadata Field** | `metadata: {...}` present | `metadata: {...}` may be removed/updated | ⚠️ **LOW** | UI doesn't display metadata |
| **Error Handling** | Always returns 200 | May return 400/404/500 | ⚠️ **LOW** | UI has error handling, should handle gracefully |
| **Authentication** | `require_auth` | Keep `require_auth` | ✅ **NONE** | No change |
| **Parameters** | `portfolio_id: Optional` | May require `portfolio_id` | ⚠️ **MEDIUM** | UI always passes portfolio_id, but should validate |
| **Database Connection** | No DB query | DB query with RLS | ✅ **NONE** | No external dependency on current DB behavior |

**Overall Risk:** ✅ **LOW** - Changes are additive, not breaking.

---

### Specific Breaking Scenarios

#### Scenario 1: Response Structure Change
**Risk:** ⚠️ **NONE**

**Current Response:**
```python
{
    "actions": [],  # Empty array
    "summary": {"total_actions": 0, ...}
}
```

**Proposed Response:**
```python
{
    "actions": [...],  # Populated array
    "summary": {"total_actions": 5, ...}
}
```

**Analysis:**
- ✅ UI code: `response.data.data.actions || []` - Already handles empty arrays
- ✅ UI filters: `corporateActions.filter(...)` - Works with any array length
- ✅ UI display: Checks `filteredActions.length === 0` - Works regardless

**Conclusion:** ✅ **SAFE** - Array structure remains, just populated.

---

#### Scenario 2: Metadata Field Removal
**Risk:** ⚠️ **LOW**

**Current Response:**
```python
{
    "metadata": {
        "message": "Corporate actions tracking not implemented...",
        ...
    }
}
```

**Proposed Response:**
```python
{
    # metadata may be removed or changed
}
```

**Analysis:**
- ⚠️ UI doesn't read metadata field (not used in component)
- ⚠️ But some other system might check it (unlikely based on searches)
- ✅ Can keep metadata field with updated message

**Conclusion:** ⚠️ **LOW RISK** - Keep metadata field but update message to "implemented" or remove it.

---

#### Scenario 3: portfolio_id Validation
**Risk:** ⚠️ **LOW-MEDIUM**

**Current:**
```python
portfolio_id: Optional[str] = Query(None)  # Optional
# No validation
```

**Proposed:**
```python
portfolio_id: str = Query(..., description="Portfolio UUID")  # Required
# Or validate if provided
if not portfolio_id:
    raise HTTPException(status_code=400, detail="portfolio_id required")
```

**Analysis:**
- ✅ UI always passes `portfolio_id: getCurrentPortfolioId()` - Should be non-null
- ⚠️ But `getCurrentPortfolioId()` might return null if no portfolio selected
- ⚠️ API should validate and return 400, not 200 with empty data

**Conclusion:** ⚠️ **LOW-MEDIUM RISK** - Should validate, UI should handle 400 error gracefully.

---

#### Scenario 4: Database Connection with RLS
**Risk:** ✅ **NONE**

**Current:**
- No database query
- No RLS needed

**Proposed:**
- Database query with RLS
- Uses `get_db_connection_with_rls(user_id)`

**Analysis:**
- ✅ RLS ensures user can only see their own portfolio data
- ✅ This is a security improvement, not a breaking change
- ✅ If user doesn't have access, will return empty array (same as current behavior)

**Conclusion:** ✅ **SAFE** - RLS is an improvement, maintains security boundaries.

---

## 🎯 Design Recommendations

### Recommendation 1: Align with Existing Patterns

**Option A: Use Pattern Orchestrator (Recommended for Future)**
- ✅ Consistent with `/api/portfolio`, `/api/holdings`
- ✅ Automatic RLS handling
- ✅ Can add to `portfolio_overview` pattern or create new pattern
- ⚠️ Requires agent capabilities first

**Option B: Use Direct Service with RLS (Recommended for MVP)**
- ✅ Quick implementation
- ✅ Consistent with `/v1/corporate-actions/*` router pattern
- ✅ Direct control over query logic
- ⚠️ Must ensure RLS properly

**Recommendation:** **Option B for MVP** - Faster to implement, can refactor to Option A later if needed.

---

### Recommendation 2: Fix Parameter Validation

**Current:**
```python
portfolio_id: Optional[str] = Query(None),
```

**Recommended:**
```python
portfolio_id: str = Query(..., description="Portfolio UUID"),
# Or if keeping optional:
portfolio_id: Optional[str] = Query(None),
# Then validate:
if not portfolio_id:
    raise HTTPException(
        status_code=400,
        detail="portfolio_id parameter is required"
    )
```

**Rationale:**
- ✅ Clear API contract
- ✅ Better error messages
- ✅ Prevents confusion

---

### Recommendation 3: Ensure RLS Security

**Required Implementation:**
```python
@app.get("/api/corporate-actions", response_model=SuccessResponse)
async def get_corporate_actions(
    portfolio_id: str = Query(..., description="Portfolio UUID"),
    days_ahead: int = Query(30, ge=1, le=365),
    user: dict = Depends(require_auth)
):
    try:
        # ✅ Use RLS-enabled connection
        async with get_db_connection_with_rls(user['user_id']) as conn:
            # ✅ Verify portfolio belongs to user (RLS handles this, but explicit check is good)
            portfolio_check = await conn.fetchrow(
                "SELECT id FROM portfolios WHERE id = $1",
                UUID(portfolio_id)
            )
            if not portfolio_check:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            # ✅ Use service with RLS connection
            service = CorporateActionsService(conn)
            actions = await service.get_upcoming_actions(
                portfolio_id=UUID(portfolio_id),
                days_ahead=days_ahead
            )
            
            # Format response...
            return SuccessResponse(data=response)
```

**Rationale:**
- ✅ Security: RLS ensures user can only access their own portfolios
- ✅ Consistency: Matches pattern from `/v1/corporate-actions/*` router
- ✅ Defense in depth: Explicit portfolio check + RLS

---

### Recommendation 4: Keep Response Structure Consistent

**Current Structure (Good):**
```python
{
    "portfolio_id": str,
    "time_horizon_days": int,
    "actions": List[Dict],
    "summary": {
        "total_actions": int,
        "dividends_expected": float,
        "splits_pending": int,
        "earnings_releases": int,
        "mergers_acquisitions": int
    },
    "notifications": {
        "urgent": List[Dict],
        "informational": List[Dict]
    },
    "last_updated": str (ISO datetime),
    "metadata": {  # Optional - can keep or remove
        "message": str,
        "version": str,
        "note": str
    }
}
```

**Recommendation:**
- ✅ Keep structure (works well)
- ⚠️ Update or remove metadata field:
  - Option 1: Remove `metadata` entirely
  - Option 2: Update message: "Corporate actions tracking implemented"
  - Option 3: Keep for debugging/version info

**Recommendation:** **Option 2** - Update metadata to indicate implementation status.

---

## ✅ Final Assessment

### Will Implementation Break Something?

**Answer:** ✅ **NO** - Implementation is safe with low risk.

**Reasons:**
1. ✅ **Isolated Usage** - Only used by one UI component
2. ✅ **Defensive UI Code** - UI handles empty arrays gracefully
3. ✅ **Additive Changes** - Adding data, not removing structure
4. ✅ **Same Response Shape** - Array structure remains the same
5. ✅ **RLS is Improvement** - Adds security, doesn't break functionality

**Minor Risks:**
1. ⚠️ **Parameter Validation** - Should validate `portfolio_id` is provided
2. ⚠️ **Metadata Field** - Update or remove to avoid confusion
3. ⚠️ **Error Handling** - Ensure UI handles 400/404 errors gracefully

**Mitigation:**
1. ✅ Validate `portfolio_id` parameter
2. ✅ Update metadata message or remove field
3. ✅ Test error scenarios in UI (already has error handling)

---

### Design Issues Summary

| Issue | Severity | Impact | Fix Required |
|-------|----------|--------|--------------|
| API Route Duplication | ⚠️ **Medium** | Confusion, inconsistency | Document clearly, consider consolidation later |
| Missing RLS Pattern | 🔴 **High** | Security risk when implemented | Must use RLS in implementation |
| Portfolio ID Validation | ⚠️ **Medium** | Clarity, error handling | Validate parameter |
| Response Structure | ✅ **None** | Already good | Keep current structure |

---

## 📋 Implementation Plan Recommendations

### Phase 1: MVP Implementation (Safe)

1. **Keep Endpoint Location** - Stay in `combined_server.py` for now (can refactor later)
2. **Use RLS Connection** - `get_db_connection_with_rls(user['user_id'])`
3. **Validate Parameters** - Require `portfolio_id`, validate format
4. **Use Direct Service** - `CorporateActionsService.get_upcoming_actions()`
5. **Keep Response Structure** - Maintain current structure, update metadata
6. **Error Handling** - Return appropriate HTTP status codes (400, 404, 500)

### Phase 2: Refactoring (Future)

1. **Consider Pattern Integration** - Add to `portfolio_overview` pattern or create new pattern
2. **Consider Router Migration** - Move to `/v1/corporate-actions/upcoming` route
3. **Consider Agent Capabilities** - Add `corporate_actions.upcoming` capability

**Recommendation:** Start with Phase 1 (MVP), refactor to Phase 2 later if needed.

---

**Status:** Analysis complete. Implementation is safe with low breaking change risk. Design improvements recommended but not blocking.

