# Authentication Refactoring Progress Tracker
## Quick Reference Checklist

### 📋 Pre-Flight Checklist
- [ ] Backup current code: `git commit -am "Pre-auth-refactor backup"`
- [ ] Verify all endpoints work currently
- [ ] Document current auth error count: 44 endpoints using old pattern

---

## SPRINT 1: Foundation (30 min) 🚀
- [ ] Fix `/api/patterns/execute` hardcoded user ID
- [ ] Create `backend/app/auth/dependencies.py`
- [ ] Move auth functions to new module
- [ ] Add AUTH_STATUS markers to endpoints
- [ ] Test: Server starts and patterns execute
- [ ] Commit: `git commit -m "Sprint 1: Auth foundation"`

## SPRINT 2: Simple Endpoints (45 min) 🎯
### Batch 1: Portfolio (10 endpoints)
- [ ] /api/portfolio
- [ ] /api/holdings  
- [ ] /api/transactions
- [ ] /api/portfolio/value-history
- [ ] /api/portfolio/cash-flows
- [ ] /api/optimize
- [ ] /api/allocation
- [ ] /api/risk/factors
- [ ] /api/risk/var
- [ ] /api/attribution

### Batch 2: Market & Reports (8 endpoints)
- [ ] /api/market/overview
- [ ] /api/market/cycles
- [ ] /api/macro
- [ ] /api/reports
- [ ] /api/reports/generate
- [ ] /api/currencies
- [ ] /api/assets
- [ ] /api/news

### Batch 3: Settings (8 endpoints)
- [ ] /api/settings
- [ ] /api/profile
- [ ] /api/preferences
- [ ] /api/notifications
- [ ] /api/audit-log
- [ ] /api/api-keys
- [ ] /api/data-sources
- [ ] /api/subscription

**Test & Commit:** `git commit -m "Sprint 2: Simple endpoints migrated"`

## SPRINT 3: Complex Endpoints (60 min) 🔧
### Path Parameters (2 endpoints)
- [ ] DELETE /api/alerts/{alert_id}
- [ ] GET /api/quotes/{symbol}

### Query Parameters (16 endpoints)
- [ ] /api/holdings (with params)
- [ ] /api/transactions (with params)
- [ ] /api/portfolio/value-history (with params)
- [ ] /api/optimize (with params)
- [ ] /api/risk/factors (with params)
- [ ] /api/risk/var (with params)
- [ ] /api/news (with params)
- [ ] /api/market/cycles (with params)
- [ ] /api/alerts GET (with params)
- [ ] /api/backtest
- [ ] /api/benchmark
- [ ] /api/correlations
- [ ] /api/efficient-frontier
- [ ] /api/rebalance
- [ ] /api/tax-loss-harvesting
- [ ] /api/scenario-analysis

### Body Parameters (1 endpoint)
- [ ] POST /api/alerts

**Test & Commit:** `git commit -m "Sprint 3: Complex endpoints migrated"`

## SPRINT 4: Cleanup (45 min) 🧹
- [ ] Remove all old `get_current_user()` calls
- [ ] Standardize error messages
- [ ] Remove unused imports
- [ ] Add endpoint docstrings
- [ ] Create auth middleware for metrics
- [ ] Verify 0 uses of old pattern remain
- [ ] Commit: `git commit -m "Sprint 4: Cleanup complete"`

## SPRINT 5: Testing & Docs (30 min) 📚
- [ ] Create `backend/tests/test_auth.py`
- [ ] Test 401 responses without token
- [ ] Test success with valid token
- [ ] Update API_DOCUMENTATION.md
- [ ] Create migration guide for future
- [ ] Final commit: `git commit -m "Sprint 5: Auth refactor complete"`

---

## 📊 Progress Metrics
- **Total Endpoints:** 45
- **Migrated:** 0 / 45
- **Lines Removed:** 0 / ~270
- **Sprints Complete:** 0 / 5

## 🎯 Migration Pattern Reference

### Simple Endpoint (Before):
```python
@app.get("/api/portfolio")
async def get_portfolio(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    # logic
```

### Simple Endpoint (After):
```python
@app.get("/api/portfolio")
async def get_portfolio(user: dict = Depends(require_auth)):
    # AUTH_STATUS: MIGRATED
    # logic
```

### Complex Endpoint (After):
```python
@app.get("/api/holdings")
async def get_holdings(
    portfolio_id: Optional[str] = Query(None),
    as_of_date: Optional[str] = Query(None),
    user: dict = Depends(require_auth)  # Always last
):
    # AUTH_STATUS: MIGRATED
    # logic
```

## ⚡ Quick Test Commands

```bash
# Test authenticated endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/portfolio

# Test should fail with 401
curl http://localhost:5000/api/portfolio

# Get token for testing
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"michael@dawsos.com","password":"test123"}' \
  | jq -r .access_token)
```