# Authentication Refactoring Sprint Plan
## Minimize Risk Through Incremental Migration

### Overview
Total Effort: 4-5 sprints (2-3 hours each)
Risk Level: LOW (parallel patterns, no breaking changes)
Strategy: Run old and new auth patterns in parallel, migrate gradually, remove old pattern last

---

## 🏃 SPRINT 1: Foundation & Critical Fix
**Duration:** 30 minutes  
**Risk:** ✅ ZERO (additive only)

### Tasks:
1. **Fix Critical Security Issue** (5 min)
   ```python
   # Fix /api/patterns/execute endpoint (line 1155)
   - user = "user-001"
   + user = await get_current_user(request)
   + if not user:
   +     raise HTTPException(status_code=401, detail="Authentication required")
   + user_id = user["id"]
   ```

2. **Add Auth Utilities Module** (15 min)
   - Create `backend/app/auth/dependencies.py`
   - Move authentication functions from combined_server.py:
     - `get_current_user()` 
     - `require_auth()`
     - `create_jwt_token()`
     - `verify_password()`
   - Update imports in combined_server.py

3. **Create Migration Tracking** (10 min)
   - Add comment markers for endpoints:
     ```python
     # AUTH_STATUS: MIGRATED
     # AUTH_STATUS: PENDING
     ```

### Validation:
- Server starts ✓
- All existing endpoints work ✓
- Pattern execution now uses real user ID ✓

---

## 🏃 SPRINT 2: Simple Endpoints Migration (26 endpoints)
**Duration:** 45 minutes  
**Risk:** ✅ LOW (simple signatures only)

### Migrate Request-Only Endpoints:
These have signature: `async def endpoint(request: Request)`

**Batch 1 - Portfolio Endpoints (10 endpoints):**
- `/api/portfolio` 
- `/api/holdings`
- `/api/transactions`
- `/api/portfolio/value-history`
- `/api/portfolio/cash-flows`
- `/api/optimize`
- `/api/allocation`
- `/api/risk/factors`
- `/api/risk/var`
- `/api/attribution`

**Batch 2 - Market & Reports (8 endpoints):**
- `/api/market/overview`
- `/api/market/cycles`
- `/api/macro`
- `/api/reports`
- `/api/reports/generate`
- `/api/currencies`
- `/api/assets`
- `/api/news`

**Batch 3 - Settings & Misc (8 endpoints):**
- `/api/settings`
- `/api/profile`
- `/api/preferences`
- `/api/notifications`
- `/api/audit-log`
- `/api/api-keys`
- `/api/data-sources`
- `/api/subscription`

### Migration Pattern:
```python
# OLD PATTERN:
@app.get("/api/portfolio")
async def get_portfolio(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    # ... rest of logic

# NEW PATTERN:
@app.get("/api/portfolio")
async def get_portfolio(user: dict = Depends(require_auth)):
    # AUTH_STATUS: MIGRATED
    # ... rest of logic (unchanged)
```

### Validation After Each Batch:
- Run server, test 2-3 endpoints from batch
- Check frontend still works
- No regression in functionality

---

## 🏃 SPRINT 3: Complex Endpoints Migration (19 endpoints)
**Duration:** 60 minutes  
**Risk:** ⚠️ MEDIUM (parameter ordering matters)

### Endpoints with Path Parameters (2 endpoints):
```python
# Pattern: Path params come BEFORE Depends
@app.delete("/api/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,  # Path param first
    user: dict = Depends(require_auth)  # Auth dependency last
):
    # AUTH_STATUS: MIGRATED
```
- `/api/alerts/{alert_id}` (DELETE)
- `/api/quotes/{symbol}` (GET)

### Endpoints with Query Parameters (16 endpoints):
```python
# Pattern: Query params can go before OR after Depends
@app.get("/api/holdings")
async def get_holdings(
    portfolio_id: Optional[str] = Query(None),
    as_of_date: Optional[str] = Query(None),
    user: dict = Depends(require_auth)  # Auth dependency last
):
    # AUTH_STATUS: MIGRATED
```

**List of Query Param Endpoints:**
- `/api/holdings` (portfolio_id, as_of_date)
- `/api/transactions` (portfolio_id, start_date, end_date)
- `/api/portfolio/value-history` (portfolio_id, period)
- `/api/optimize` (portfolio_id, strategy)
- `/api/risk/factors` (portfolio_id)
- `/api/risk/var` (portfolio_id, confidence_level)
- `/api/news` (portfolio_id, days)
- `/api/market/cycles` (cycle_type)
- `/api/alerts` (GET - status filter)
- `/api/backtest` (strategy, start_date, end_date)
- `/api/benchmark` (benchmark_id, period)
- `/api/correlations` (assets, period)
- `/api/efficient-frontier` (constraints)
- `/api/rebalance` (portfolio_id, target_allocation)
- `/api/tax-loss-harvesting` (portfolio_id, tax_rate)
- `/api/scenario-analysis` (scenario_type)

### Endpoint with Body Parameter (1 endpoint):
```python
@app.post("/api/alerts")
async def create_alert(
    alert_data: CreateAlertRequest,  # Body first
    user: dict = Depends(require_auth)  # Auth last
):
    # AUTH_STATUS: MIGRATED
```

### Validation:
- Test each complex endpoint individually
- Verify query parameters still work
- Check path parameters resolve correctly

---

## 🏃 SPRINT 4: Cleanup & Optimization
**Duration:** 45 minutes  
**Risk:** ✅ LOW (removal of dead code)

### Tasks:

1. **Remove Old Pattern Helper** (15 min)
   - Delete the old `get_current_user()` calls from migrated endpoints
   - Remove duplicate auth checking code
   - Clean up imports

2. **Consolidate Error Messages** (10 min)
   - Standardize all auth errors to: "Authentication required"
   - Remove variations like "User authentication required"

3. **Update Documentation** (10 min)
   ```python
   # Add docstrings to all migrated endpoints
   """
   Get user portfolio.
   
   Authentication: Required
   Returns: Portfolio data for authenticated user
   """
   ```

4. **Create Auth Middleware** (10 min)
   - Add request logging for auth failures
   - Add metrics collection hook
   ```python
   @app.middleware("http")
   async def auth_metrics_middleware(request: Request, call_next):
       # Track auth success/failure rates
   ```

### Validation:
- All 45 endpoints using new pattern
- 0 uses of old pattern
- Documentation updated

---

## 🏃 SPRINT 5: Testing & Documentation
**Duration:** 30 minutes  
**Risk:** ✅ ZERO (documentation only)

### Tasks:

1. **Create Test Suite** (15 min)
   - `backend/tests/test_auth.py`
   - Test authenticated endpoints return 401 without token
   - Test endpoints work with valid token
   - Test token refresh flow

2. **API Documentation Update** (10 min)
   - Update `API_DOCUMENTATION.md`
   - Mark all endpoints with auth requirements
   - Document token refresh strategy

3. **Migration Guide** (5 min)
   - Document the new pattern for future endpoints
   - Create template for new authenticated endpoints

### Final Metrics:
- Lines of code removed: ~270
- Endpoints migrated: 45
- Test coverage added: 100% of auth flow
- Documentation: Complete

---

## 🚀 Rollback Strategy

Each sprint is independently revertible:
1. Git commit after each sprint
2. Tag each sprint completion
3. If issues arise, revert single sprint only
4. Old pattern works in parallel until Sprint 4

## 📊 Success Metrics

- **Sprint 1:** Critical fix deployed, no regression
- **Sprint 2:** 26 simple endpoints migrated
- **Sprint 3:** All complex endpoints migrated
- **Sprint 4:** Old pattern completely removed
- **Sprint 5:** Full test coverage, documentation complete

## 🔄 Parallel Pattern Period

Sprints 1-3 run BOTH patterns:
- Old: `user = await get_current_user(request)`
- New: `user: dict = Depends(require_auth)`

This ensures zero downtime and gradual migration.

---

## Quick Start Commands

```bash
# After each sprint
git add . && git commit -m "Auth refactor: Sprint X complete"
git tag sprint-X-complete

# Test after each sprint
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/portfolio
curl http://localhost:5000/api/portfolio  # Should return 401

# Rollback if needed
git revert HEAD  # Revert last sprint only
```