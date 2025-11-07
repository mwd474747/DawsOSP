# Database Connection Standardization - Step-by-Step Execution Guide

**Date:** January 14, 2025  
**Status:** 📋 **EXECUTION GUIDE**  
**Purpose:** Detailed step-by-step instructions for standardizing database connection patterns

---

## Quick Reference: Standard Patterns

### Pattern A: User-Scoped Data (RLS Required) ⭐
**Use:** Agents, API routes accessing user data  
**Code:**
```python
from app.db.connection import get_db_connection_with_rls

async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
    rows = await conn.fetch(query, *args)
```

### Pattern B: System-Level Operations (No RLS)
**Use:** Services, background jobs, system operations  
**Code:**
```python
from app.db.connection import execute_query, execute_query_one, execute_statement

rows = await execute_query(query, *args)
row = await execute_query_one(query, *args)
await execute_statement(query, *args)
```

---

## Phase 1: Services (2-3 hours)

### Step 1.1: Update `backend/app/services/ratings.py`

**File:** `backend/app/services/ratings.py`  
**Current Pattern:** Pattern 1 (pool.acquire) + Pattern 4 (service-level pool caching)  
**Target Pattern:** Pattern B (helper functions)

**Changes Required:**

1. **Remove pool caching from `__init__`:**
   ```python
   # BEFORE:
   def __init__(self, use_db: bool = True, db_pool=None):
       self.use_db = use_db
       self.db_pool = db_pool
       # ...
   
   # AFTER:
   def __init__(self, use_db: bool = True, db_pool=None):
       self.use_db = use_db
       # Remove self.db_pool - not needed
       # ...
   ```

2. **Update `_load_rubrics` method (line ~68):**
   ```python
   # BEFORE:
   async def _load_rubrics(self) -> Dict[str, Dict]:
       if not self.db_pool:
           from app.db.connection import get_db_pool
           self.db_pool = get_db_pool()
       
       query = "..."
       async with self.db_pool.acquire() as conn:
           rows = await conn.fetch(query)
   
   # AFTER:
   async def _load_rubrics(self) -> Dict[str, Dict]:
       from app.db.connection import execute_query
       
       query = "..."
       rows = await execute_query(query)
   ```

**Validation:**
- [ ] Remove `self.db_pool` from `__init__`
- [ ] Replace `pool.acquire()` with `execute_query()`
- [ ] Remove pool initialization logic
- [ ] Test `_load_rubrics()` method

---

### Step 1.2: Update `backend/app/services/audit.py`

**File:** `backend/app/services/audit.py`  
**Current Pattern:** Pattern 1 (pool.acquire) + Pattern 4 (service-level pool caching)  
**Target Pattern:** Pattern B (helper functions)

**Changes Required:**

1. **Remove `_get_db_pool` method (line ~82):**
   ```python
   # DELETE THIS METHOD:
   def _get_db_pool(self) -> asyncpg.Pool:
       if self.db_pool is None:
           from app.db.connection import get_db_pool
           self.db_pool = get_db_pool()
       return self.db_pool
   ```

2. **Update `log_event` method (line ~132):**
   ```python
   # BEFORE:
   async def log_event(self, ...):
       pool = self._get_db_pool()
       async with pool.acquire() as conn:
           await conn.execute(query, ...)
   
   # AFTER:
   async def log_event(self, ...):
       from app.db.connection import execute_statement
       
       await execute_statement(query, ...)
   ```

3. **Update all other methods using `_get_db_pool()`:**
   - Line ~195: `log_user_action`
   - Line ~251: `log_api_request`
   - Line ~310: `log_error`

**Validation:**
- [ ] Remove `_get_db_pool()` method
- [ ] Remove `self.db_pool` caching
- [ ] Replace all `pool.acquire()` with `execute_statement()`
- [ ] Test all audit logging methods

---

## Phase 2: Agents (1-2 hours)

### Step 2.1: Update `backend/app/agents/financial_analyst.py`

**File:** `backend/app/agents/financial_analyst.py`  
**Current Pattern:** Pattern 1 (pool.acquire) in some methods  
**Target Pattern:** Pattern A (RLS-aware) for user data

**Changes Required:**

1. **Update `metrics.compute_twr` method (line ~1033):**
   ```python
   # BEFORE:
   from app.db.connection import get_db_pool
   db = get_db_pool()
   # ... uses db directly
   
   # AFTER:
   from app.db.connection import get_db_connection_with_rls
   
   async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
       # ... use conn instead of db
   ```

2. **Update `metrics.compute_mwr` method (line ~1251):**
   ```python
   # BEFORE:
   from app.db import get_db_pool
   pool = await get_db_pool()
   async with pool.acquire() as db:
       rows = await db.fetch(query, ...)
   
   # AFTER:
   from app.db.connection import get_db_connection_with_rls
   
   async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
       rows = await conn.fetch(query, ...)
   ```

3. **Update `metrics.compute_sharpe` method (line ~1365):**
   ```python
   # BEFORE:
   from app.db import get_db_pool
   pool = await get_db_pool()
   async with pool.acquire() as db:
       rows = await db.fetch(query, ...)
   
   # AFTER:
   from app.db.connection import get_db_connection_with_rls
   
   async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
       rows = await conn.fetch(query, ...)
   ```

4. **Update `attribution.currency` method (line ~1670):**
   ```python
   # BEFORE:
   async with db_pool.acquire() as conn:
       rows = await conn.fetch(query, ...)
   
   # AFTER:
   async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
       rows = await conn.fetch(query, ...)
   ```

5. **Update `charts.overview` method (line ~1781):**
   ```python
   # BEFORE:
   async with db_pool.acquire() as conn:
       rows = await conn.fetch(query, ...)
   
   # AFTER:
   async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
       rows = await conn.fetch(query, ...)
   ```

6. **Update `portfolio.sector_allocation` method (line ~1995):**
   ```python
   # BEFORE:
   async with db_pool.acquire() as conn:
       rows = await conn.fetch(query, ...)
   
   # AFTER:
   async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
       rows = await conn.fetch(query, ...)
   ```

7. **Update `portfolio.historical_nav` method (line ~2106):**
   ```python
   # BEFORE:
   async with db_pool.acquire() as conn:
       rows = await conn.fetch(query, ...)
   
   # AFTER:
   async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
       rows = await conn.fetch(query, ...)
   ```

8. **Update `risk.get_factor_exposure_history` method (line ~2259):**
   ```python
   # BEFORE:
   async with db_pool.acquire() as conn:
       rows = await conn.fetch(query, ...)
   
   # AFTER:
   async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
       rows = await conn.fetch(query, ...)
   ```

9. **Update `risk.compute_factor_exposures` method (line ~2326):**
   ```python
   # BEFORE:
   async with db_pool.acquire() as conn:
       rows = await conn.fetch(query, ...)
   
   # AFTER:
   async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
       rows = await conn.fetch(query, ...)
   ```

10. **Update `get_comparable_positions` method (line ~2473):**
    ```python
    # BEFORE:
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, ...)
    
    # AFTER:
    async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
        rows = await conn.fetch(query, ...)
    ```

**Note:** Methods already using `get_db_connection_with_rls()` (lines 240, 2683, 3164) are correct - **DO NOT CHANGE**.

**Validation:**
- [ ] All 10 methods updated to use `get_db_connection_with_rls()`
- [ ] All methods use `ctx.user_id` for RLS
- [ ] No remaining `pool.acquire()` calls
- [ ] Test all affected capabilities

---

### Step 2.2: Update `backend/app/agents/data_harvester.py`

**File:** `backend/app/agents/data_harvester.py`  
**Current Pattern:** Pattern 1 (pool.acquire)  
**Context:** Queries `securities` table (system-level data)  
**RLS Required:** ❌ No (system-level: securities table)  
**Target Pattern:** Pattern B (helper functions)

**Changes Required:**

1. **Update `fundamentals.load` method (line ~675):**
   ```python
   # BEFORE:
   db_pool = self.services.get("db")
   if db_pool:
       async with db_pool.acquire() as conn:
           row = await conn.fetchrow("SELECT symbol FROM securities WHERE id = $1", ...)
   
   # AFTER:
   from app.db.connection import execute_query_one
   
   row = await execute_query_one("SELECT symbol FROM securities WHERE id = $1", ...)
   ```

**Validation:**
- [ ] Replace `pool.acquire()` with `execute_query_one()`
- [ ] Remove `db_pool` check (helper functions handle errors)
- [ ] Test `fundamentals.load` capability

---

## Phase 3: Jobs (1 hour)

### Step 3.1: Update `backend/jobs/daily_valuation.py`

**File:** `backend/jobs/daily_valuation.py`  
**Current Pattern:** Pattern 1 (pool.acquire) - pool passed in `__init__`  
**Context:** Background job - system-level operations  
**RLS Required:** ❌ No (background job, system-level)  
**Target Pattern:** Pattern B (helper functions)

**Changes Required:**

1. **Update `__init__` method (line ~29):**
   ```python
   # BEFORE:
   def __init__(self, db_pool: asyncpg.Pool):
       self.db_pool = db_pool
   
   # AFTER:
   def __init__(self):
       # Remove db_pool parameter - not needed
       pass
   ```

2. **Update `_get_portfolios` method (line ~86):**
   ```python
   # BEFORE:
   async with self.db_pool.acquire() as conn:
       return await conn.fetch(query)
   
   # AFTER:
   from app.db.connection import execute_query
   
   return await execute_query(query)
   ```

3. **Update `_fetch_portfolio_positions` method (line ~215):**
   ```python
   # BEFORE:
   async with self.db_pool.acquire() as conn:
       rows = await conn.fetch(query, ...)
   
   # AFTER:
   from app.db.connection import execute_query
   
   rows = await execute_query(query, ...)
   ```

4. **Update `_fetch_pricing_pack` method (line ~241):**
   ```python
   # BEFORE:
   async with self.db_pool.acquire() as conn:
       row = await conn.fetchrow(query, ...)
   
   # AFTER:
   from app.db.connection import execute_query_one
   
   row = await execute_query_one(query, ...)
   ```

5. **Update `_calculate_position_values` method (line ~261):**
   ```python
   # BEFORE:
   async with self.db_pool.acquire() as conn:
       rows = await conn.fetch(query, ...)
   
   # AFTER:
   from app.db.connection import execute_query
   
   rows = await execute_query(query, ...)
   ```

6. **Update `_update_daily_values` method (line ~301):**
   ```python
   # BEFORE:
   async with self.db_pool.acquire() as conn:
       await conn.execute(query, ...)
   
   # AFTER:
   from app.db.connection import execute_statement
   
   await execute_statement(query, ...)
   ```

7. **Update `_update_portfolio_metrics` method (line ~330):**
   ```python
   # BEFORE:
   async with self.db_pool.acquire() as conn:
       await conn.execute(query, ...)
   
   # AFTER:
   from app.db.connection import execute_statement
   
   await execute_statement(query, ...)
   ```

8. **Update `run` method (line ~362):**
   ```python
   # BEFORE:
   from backend.app.db.connection import get_db_pool
   db_pool = await get_db_pool()
   # ... uses db_pool
   
   # AFTER:
   # Remove - no longer needed
   ```

**Validation:**
- [ ] Remove `db_pool` parameter from `__init__`
- [ ] Replace all 6 `pool.acquire()` calls with helper functions
- [ ] Update job invocation to not pass `db_pool`
- [ ] Test daily valuation job

---

## Phase 4: API Routes (30 minutes)

### Step 4.1: Review API Routes

**Files Already Correct (No Changes):**
- ✅ `backend/app/api/routes/portfolios.py` - 6 usages of `get_db_connection_with_rls()`
- ✅ `backend/app/api/routes/trades.py` - 5 usages of `get_db_connection_with_rls()`
- ✅ `backend/app/api/routes/corporate_actions.py` - 6 usages of `get_db_connection_with_rls()`
- ✅ `backend/app/api/routes/alerts.py` - 6 usages of `get_db_connection_with_rls()`
- ✅ `backend/app/api/routes/notifications.py` - 5 usages of `get_db_connection_with_rls()`
- ✅ `backend/app/api/routes/macro.py` - 1 usage of `get_db_connection_with_rls()`

**Files to Review:**

1. **Review `backend/app/api/routes/auth.py`:**
   - Check current database access pattern
   - Determine if RLS needed (user data) or system-level
   - Update if needed

**Validation:**
- [ ] Review auth routes for RLS requirements
- [ ] Update if needed
- [ ] Test affected endpoints

---

## Phase 5: Scripts (No Changes)

### Step 5.1: Document Script Pattern

**Files:** All `backend/scripts/*.py`  
**Current Pattern:** Pattern 3 (direct asyncpg.connect)  
**Recommendation:** ✅ **NO CHANGES** - Acceptable for one-time operations

**Documentation:**
- Scripts can use `asyncpg.connect()` directly
- No pooling needed for one-time operations
- No RLS needed for scripts (run as admin)

---

## Validation Checklist

After completing all phases:

### Code Review
- [ ] No `pool.acquire()` calls in services (except scripts)
- [ ] No `pool.acquire()` calls in agents (except scripts)
- [ ] All user-scoped data uses `get_db_connection_with_rls(user_id)`
- [ ] All system-level operations use `execute_query*` helper functions
- [ ] No service-level pool caching (except where necessary)
- [ ] All imports updated correctly

### Testing
- [ ] Unit tests pass for all services
- [ ] Unit tests pass for all agents
- [ ] Integration tests pass
- [ ] RLS policies enforced correctly
- [ ] Connection pool sharing verified
- [ ] No connection pool exhaustion

### Documentation
- [ ] `DATABASE.md` updated with standardized patterns
- [ ] Code examples added to documentation
- [ ] Migration guide documented

---

## Rollback Instructions

If issues arise during migration:

1. **Revert one file at a time:**
   ```bash
   git checkout HEAD -- backend/app/services/ratings.py
   ```

2. **Test after each revert:**
   - Run unit tests
   - Run integration tests
   - Verify functionality

3. **Document issues:**
   - Note which pattern caused problems
   - Update standardization plan
   - Adjust approach if needed

---

## Estimated Time Breakdown

| Phase | Files | Time | Priority |
|-------|-------|------|----------|
| Phase 1: Services | 2 files | 1-2 hours | High |
| Phase 2: Agents | 2 files | 1-2 hours | High |
| Phase 3: Jobs | 1 file | 30 min - 1 hour | Medium |
| Phase 4: API Routes | 2 files | 30 minutes | Low |
| Phase 5: Scripts | 0 files | 0 (documentation only) | N/A |
| **Total** | **7 files** | **3-5 hours** | |

---

## Execution Order

1. ✅ **Phase 1: Services** (highest impact, lowest risk)
2. ✅ **Phase 2: Agents** (high impact, medium risk)
3. ✅ **Phase 3: Jobs** (medium impact, low risk)
4. ✅ **Phase 4: API Routes** (low impact, low risk)
5. ✅ **Phase 5: Scripts** (documentation only)

---

## Success Criteria

✅ **Standardization Complete When:**
- All services use `execute_query*` helper functions
- All agents use `get_db_connection_with_rls(user_id)` for user data
- All API routes use `get_db_connection_with_rls(user_id)` for user data
- No `pool.acquire()` calls in services or agents (except scripts)
- No service-level pool caching
- All tests pass
- RLS policies enforced correctly

---

## Next Steps

1. Start with **Phase 1: Services** (lowest risk)
2. Test after each file update
3. Proceed to **Phase 2: Agents** after services complete
4. Continue through remaining phases
5. Validate with full test suite
6. Update documentation

