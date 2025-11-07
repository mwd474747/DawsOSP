# Database Connection Pattern Standardization Plan

**Date:** January 14, 2025  
**Status:** 📋 **PLANNING**  
**Purpose:** Standardize database connection patterns across the codebase

---

## Executive Summary

**Current State:** 5 different database connection patterns in use  
**Target State:** 2 standardized patterns (RLS-aware for user data, helper functions for system operations)  
**Estimated Time:** 4-6 hours  
**Files Affected:** ~50 files

---

## Current Patterns Analysis

### Pattern 1: Get Pool → Acquire (Most Common)
**Usage:** Services, agents, jobs  
**Code:**
```python
from app.db.connection import get_db_pool

pool = get_db_pool()
async with pool.acquire() as conn:
    result = await conn.fetch(query, *args)
```

**Issues:**
- ❌ No RLS support
- ❌ Manual connection management
- ❌ Verbose (3 lines per query)

**Files Using:**
- `backend/app/services/ratings.py`
- `backend/app/agents/financial_analyst.py` (some methods)
- `backend/app/agents/data_harvester.py`
- `backend/jobs/daily_valuation.py`
- `backend/scripts/populate_fred_data.py`

---

### Pattern 2: Helper Functions (Most Common in Services)
**Usage:** Services (pricing, scenarios, macro, cycles, etc.)  
**Code:**
```python
from app.db.connection import execute_query, execute_query_one, execute_statement

rows = await execute_query(query, *args)
row = await execute_query_one(query, *args)
await execute_statement(query, *args)
```

**Issues:**
- ❌ No RLS support (uses shared pool without user context)
- ✅ Clean and concise
- ✅ Uses shared pool correctly

**Files Using:**
- `backend/app/services/pricing.py`
- `backend/app/services/scenarios.py`
- `backend/app/services/macro.py`
- `backend/app/services/cycles.py`
- `backend/app/services/risk.py`
- `backend/app/services/alerts.py`
- `backend/app/services/notifications.py`
- `backend/app/services/dlq.py`
- `backend/app/services/auth.py`
- `backend/app/services/benchmarks.py`

---

### Pattern 3: Direct asyncpg.connect() (Scripts Only)
**Usage:** Standalone scripts, migrations  
**Code:**
```python
import asyncpg

conn = await asyncpg.connect(DATABASE_URL)
result = await conn.fetch(query)
await conn.close()
```

**Issues:**
- ❌ Creates new connection (not pooled)
- ❌ No RLS support
- ❌ Must manually close
- ✅ Acceptable for scripts (one-time operations)

**Files Using:**
- `backend/scripts/seed_*.py` (multiple files)
- `backend/scripts/validate_database_schema.py`
- `backend/jobs/compute_metrics_simple.py`
- `backend/init_db.py`

**Recommendation:** ✅ **KEEP** for scripts (acceptable for one-time operations)

---

### Pattern 4: Service-Level Pool (Rare)
**Usage:** Services that cache pool  
**Code:**
```python
class MyService:
    def __init__(self):
        from app.db.connection import get_db_pool
        self.db_pool = get_db_pool()
    
    async def query(self):
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(query)
```

**Issues:**
- ❌ No RLS support
- ❌ Redundant (pool is already shared)
- ✅ Acceptable if service needs pool reference

**Files Using:**
- `backend/app/services/ratings.py` (caches pool)
- `backend/app/services/audit.py` (caches pool)

**Recommendation:** ⚠️ **REVIEW** - Can be replaced with helper functions

---

### Pattern 5: RLS-Aware Connection (Standard for User Data) ⭐
**Usage:** Agents, API routes (user-scoped data)  
**Code:**
```python
from app.db.connection import get_db_connection_with_rls

async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
    result = await conn.fetch(query, *args)
```

**Benefits:**
- ✅ RLS support (enforces row-level security)
- ✅ User context automatically set
- ✅ Proper transaction boundaries
- ✅ Required for user-scoped data

**Files Using:**
- `backend/app/agents/financial_analyst.py` (some methods)
- `backend/app/api/routes/portfolios.py`
- `backend/app/api/routes/trades.py`
- `backend/app/api/routes/corporate_actions.py`
- `backend/app/api/routes/alerts.py`
- `backend/app/api/routes/notifications.py`

**Recommendation:** ✅ **STANDARD** for all user-scoped data

---

## Standardization Strategy

### Principle: Use the Right Pattern for the Context

1. **User-Scoped Data (RLS Required):**
   - Use: `get_db_connection_with_rls(user_id)`
   - Context: Agent methods, API routes that access user data
   - Examples: Positions, transactions, portfolios, alerts

2. **System/Admin Operations (No RLS):**
   - Use: `execute_query`, `execute_query_one`, `execute_statement`
   - Context: Services, background jobs, system operations
   - Examples: Pricing packs, metrics, macro indicators, system config

3. **Scripts (One-Time Operations):**
   - Use: `asyncpg.connect()` (acceptable)
   - Context: Standalone scripts, migrations, one-time data loads
   - Examples: Seed scripts, validation scripts

---

## Step-by-Step Migration Plan

### Phase 1: Document Current State (30 minutes)

**Step 1.1:** Create inventory of all database connection usage
- [ ] Scan all files for database connection patterns
- [ ] Categorize by pattern type
- [ ] Identify RLS requirements for each usage
- [ ] Document in `DATABASE_CONNECTION_INVENTORY.md`

**Deliverable:** Complete inventory of all database connections

---

### Phase 2: Standardize Services (2-3 hours)

**Step 2.1:** Update services using Pattern 1 (pool.acquire)
- [ ] `backend/app/services/ratings.py` - Replace `pool.acquire()` with helper functions
- [ ] `backend/app/services/audit.py` - Replace `pool.acquire()` with helper functions
- [ ] Verify no RLS needed (services are system-level)

**Step 2.2:** Verify services using Pattern 2 (helper functions)
- [ ] Confirm all services using `execute_query*` are system-level (no RLS needed)
- [ ] Document which services are correctly using helper functions
- [ ] No changes needed if already correct

**Step 2.3:** Review services using Pattern 4 (service-level pool)
- [ ] `backend/app/services/ratings.py` - Remove pool caching, use helper functions
- [ ] `backend/app/services/audit.py` - Remove pool caching, use helper functions
- [ ] Simplify service initialization

**Files to Update:**
- `backend/app/services/ratings.py`
- `backend/app/services/audit.py`

---

### Phase 3: Standardize Agents (1-2 hours)

**Step 3.1:** Update agents using Pattern 1 (pool.acquire) to Pattern 5 (RLS-aware)
- [ ] `backend/app/agents/financial_analyst.py` - Replace `pool.acquire()` with `get_db_connection_with_rls()`
  - Line 1033-1034: `get_db_pool()` usage
  - Line 1251-1255: `pool.acquire()` usage
  - Line 1365-1369: `pool.acquire()` usage
  - Line 1670, 1781, 1995, 2106, 2259, 2326, 2473: `db_pool.acquire()` usage
- [ ] `backend/app/agents/data_harvester.py` - Replace `pool.acquire()` with `get_db_connection_with_rls()`
  - Line 674: `db_pool.acquire()` usage

**Step 3.2:** Verify agents already using Pattern 5 (RLS-aware)
- [ ] `backend/app/agents/financial_analyst.py` - Verify RLS usage is correct
  - Line 240: ✅ Already using `get_db_connection_with_rls()`
  - Line 2683: ✅ Already using `get_db_connection_with_rls()`
  - Line 3164: ✅ Already using `get_db_connection_with_rls()`

**Files to Update:**
- `backend/app/agents/financial_analyst.py`
- `backend/app/agents/data_harvester.py`

---

### Phase 4: Standardize Jobs (1 hour)

**Step 4.1:** Update jobs using Pattern 1 (pool.acquire) to helper functions
- [ ] `backend/jobs/daily_valuation.py` - Replace `pool.acquire()` with helper functions
  - Lines 86, 215, 241, 261, 301, 330: `self.db_pool.acquire()` usage
- [ ] Verify no RLS needed (jobs are system-level)

**Step 4.2:** Review jobs using Pattern 3 (direct asyncpg)
- [ ] `backend/jobs/compute_metrics_simple.py` - Review if should use pool
- [ ] Document which jobs can use direct connections (one-time operations)

**Files to Update:**
- `backend/jobs/daily_valuation.py`

---

### Phase 5: Standardize API Routes (30 minutes)

**Step 5.1:** Verify API routes using Pattern 5 (RLS-aware)
- [ ] `backend/app/api/routes/portfolios.py` - ✅ Already using `get_db_connection_with_rls()`
- [ ] `backend/app/api/routes/trades.py` - ✅ Already using `get_db_connection_with_rls()`
- [ ] `backend/app/api/routes/corporate_actions.py` - ✅ Already using `get_db_connection_with_rls()`
- [ ] `backend/app/api/routes/alerts.py` - ✅ Already using `get_db_connection_with_rls()`
- [ ] `backend/app/api/routes/notifications.py` - ✅ Already using `get_db_connection_with_rls()`

**Step 5.2:** Review API routes using other patterns
- [ ] `backend/app/api/routes/auth.py` - Review if needs RLS
- [ ] `backend/app/api/routes/macro.py` - Review if needs RLS

**Files to Review:**
- `backend/app/api/routes/auth.py`
- `backend/app/api/routes/macro.py`

---

### Phase 6: Scripts (No Changes Needed)

**Step 6.1:** Document scripts using Pattern 3 (direct asyncpg)
- [ ] Scripts are acceptable to use `asyncpg.connect()` (one-time operations)
- [ ] No changes needed
- [ ] Document in standards guide

**Files:**
- `backend/scripts/seed_*.py` (multiple files)
- `backend/scripts/validate_database_schema.py`
- `backend/init_db.py`

**Recommendation:** ✅ **NO CHANGES** - Scripts can use direct connections

---

## Detailed Migration Steps

### Step 1: Update `backend/app/services/ratings.py`

**Current:**
```python
async def _load_rubrics(self) -> Dict[str, Dict]:
    if not self.db_pool:
        from app.db.connection import get_db_pool
        self.db_pool = get_db_pool()
    
    query = "..."
    async with self.db_pool.acquire() as conn:
        rows = await conn.fetch(query)
```

**Target:**
```python
async def _load_rubrics(self) -> Dict[str, Dict]:
    from app.db.connection import execute_query
    
    query = "..."
    rows = await execute_query(query)
```

**Changes:**
- Remove `self.db_pool` caching
- Replace `pool.acquire()` with `execute_query()`
- Remove pool initialization logic

---

### Step 2: Update `backend/app/services/audit.py`

**Current:**
```python
def _get_db_pool(self) -> asyncpg.Pool:
    if self.db_pool is None:
        from app.db.connection import get_db_pool
        self.db_pool = get_db_pool()
    return self.db_pool

async def log_event(self, ...):
    pool = self._get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(query, ...)
```

**Target:**
```python
async def log_event(self, ...):
    from app.db.connection import execute_statement
    
    await execute_statement(query, ...)
```

**Changes:**
- Remove `_get_db_pool()` method
- Remove `self.db_pool` caching
- Replace `pool.acquire()` with `execute_statement()`

---

### Step 3: Update `backend/app/agents/financial_analyst.py`

**Current (Pattern 1 - pool.acquire):**
```python
from app.db import get_db_pool

pool = await get_db_pool()
async with pool.acquire() as db:
    rows = await db.fetch(query, *args)
```

**Target (Pattern 5 - RLS-aware):**
```python
from app.db.connection import get_db_connection_with_rls

async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
    rows = await conn.fetch(query, *args)
```

**Locations to Update:**
1. Line ~1033: `metrics.compute_twr` method
2. Line ~1251: `metrics.compute_mwr` method
3. Line ~1365: `metrics.compute_sharpe` method
4. Line ~1670: `attribution.currency` method
5. Line ~1781: `charts.overview` method
6. Line ~1995: `portfolio.sector_allocation` method
7. Line ~2106: `portfolio.historical_nav` method
8. Line ~2259: `risk.get_factor_exposure_history` method
9. Line ~2326: `risk.compute_factor_exposures` method
10. Line ~2473: `get_comparable_positions` method

**Note:** Methods that already use `get_db_connection_with_rls()` (lines 240, 2683, 3164) are correct and should remain unchanged.

---

### Step 4: Update `backend/app/agents/data_harvester.py`

**Current:**
```python
async with db_pool.acquire() as conn:
    rows = await conn.fetch(query, *args)
```

**Target:**
```python
# If user-scoped data:
async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
    rows = await conn.fetch(query, *args)

# If system-level data:
from app.db.connection import execute_query
rows = await execute_query(query, *args)
```

**Location to Update:**
- Line ~674: Review context to determine if RLS needed

---

### Step 5: Update `backend/jobs/daily_valuation.py`

**Current:**
```python
class DailyValuationJob:
    def __init__(self):
        self.db_pool = None
    
    async def _get_pool(self):
        if self.db_pool is None:
            from backend.app.db.connection import get_db_pool
            self.db_pool = await get_db_pool()
        return self.db_pool
    
    async def compute_valuation(self):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
```

**Target:**
```python
class DailyValuationJob:
    async def compute_valuation(self):
        from app.db.connection import execute_query
        
        rows = await execute_query(query, *args)
```

**Changes:**
- Remove `self.db_pool` caching
- Remove `_get_pool()` method
- Replace `pool.acquire()` with `execute_query()`
- Update all 6 usages (lines 86, 215, 241, 261, 301, 330)

---

## Validation Checklist

After migration, verify:

- [ ] All user-scoped data uses `get_db_connection_with_rls(user_id)`
- [ ] All system-level operations use `execute_query*` helper functions
- [ ] No direct `pool.acquire()` calls in services or agents (except scripts)
- [ ] No service-level pool caching (except where necessary)
- [ ] All RLS policies are enforced for user data
- [ ] Connection pool is shared (not duplicated)
- [ ] All tests pass
- [ ] No connection pool exhaustion warnings

---

## Testing Strategy

### Unit Tests
- [ ] Test each service with helper functions
- [ ] Test each agent with RLS-aware connections
- [ ] Verify RLS policies are enforced

### Integration Tests
- [ ] Test connection pool sharing
- [ ] Test concurrent requests
- [ ] Test connection pool limits

### Manual Testing
- [ ] Run all API endpoints
- [ ] Verify user data isolation (RLS)
- [ ] Check connection pool metrics

---

## Rollback Plan

If issues arise:
1. Revert changes to one file at a time
2. Test after each revert
3. Document which pattern caused issues
4. Adjust standardization plan accordingly

---

## Documentation Updates

After migration:
- [ ] Update `DATABASE.md` with standardized patterns
- [ ] Create `DATABASE_CONNECTION_GUIDE.md` with examples
- [ ] Update service/agent documentation
- [ ] Add code review checklist

---

## Summary

**Patterns to Standardize:**
1. ✅ **Services:** Use `execute_query*` helper functions (system-level, no RLS)
2. ✅ **Agents:** Use `get_db_connection_with_rls(user_id)` (user-scoped, RLS required)
3. ✅ **API Routes:** Use `get_db_connection_with_rls(user_id)` (user-scoped, RLS required)
4. ✅ **Jobs:** Use `execute_query*` helper functions (system-level, no RLS)
5. ✅ **Scripts:** Keep `asyncpg.connect()` (acceptable for one-time operations)

**Files to Update:** ~15 files
**Estimated Time:** 4-6 hours
**Risk Level:** Medium (requires careful testing of RLS enforcement)

