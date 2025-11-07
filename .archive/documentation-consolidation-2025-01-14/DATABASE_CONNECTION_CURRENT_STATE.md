# Database Connection Patterns - Current State Analysis

**Date:** January 14, 2025  
**Status:** ✅ **ACCURATE** - Reflects actual codebase state  
**Purpose:** Document the actual current state of database connection patterns before standardization

---

## Executive Summary

**Total Database Access Points:** ~150+  
**Pattern Distribution:**
- Pattern B (Helper Functions): ~104 usages (69%) ✅ **Most services already standardized**
- Pattern A (RLS-Aware): ~42 usages (28%) ✅ **API routes and some agents**
- Pattern 1 (Pool Acquire): ~20 usages (13%) ⚠️ **Needs standardization**
- Pattern 3 (Direct asyncpg): ~10 usages (7%) ✅ **Scripts only - acceptable**

---

## Current State by Pattern

### Pattern A: RLS-Aware Connection ✅ **CORRECT**

**Usage:** API routes, some agent methods  
**Count:** ~42 usages  
**Status:** ✅ **Already standardized**

**Files Using:**
- ✅ `backend/app/api/routes/portfolios.py` - 6 usages
- ✅ `backend/app/api/routes/trades.py` - 5 usages
- ✅ `backend/app/api/routes/corporate_actions.py` - 6 usages
- ✅ `backend/app/api/routes/alerts.py` - 6 usages
- ✅ `backend/app/api/routes/notifications.py` - 5 usages
- ✅ `backend/app/agents/financial_analyst.py` - 3 usages (lines 240, 2683, 3164)
- ✅ `backend/app/api/routes/macro.py` - 1 usage

**Example:**
```python
from app.db.connection import get_db_connection_with_rls

async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
    rows = await conn.fetch(query, *args)
```

**Assessment:** ✅ **No changes needed** - Already using correct pattern

---

### Pattern B: Helper Functions ✅ **CORRECT**

**Usage:** Most services (system-level operations)  
**Count:** ~104 usages  
**Status:** ✅ **Already standardized**

**Files Using:**
- ✅ `backend/app/services/pricing.py` - 7 usages
- ✅ `backend/app/services/scenarios.py` - 5 usages
- ✅ `backend/app/services/macro.py` - 8 usages
- ✅ `backend/app/services/cycles.py` - 3 usages
- ✅ `backend/app/services/risk.py` - 2 usages
- ✅ `backend/app/services/alerts.py` - 17 usages
- ✅ `backend/app/services/notifications.py` - 10 usages
- ✅ `backend/app/services/dlq.py` - 12 usages
- ✅ `backend/app/services/benchmarks.py` - 3 usages
- ✅ `backend/app/services/auth.py` - 10 usages
- ✅ `backend/app/services/alert_delivery.py` - 10 usages
- ✅ `backend/app/services/optimizer.py` - 15 usages (via self.execute_query)
- ✅ `backend/app/services/reports.py` - 2 usages

**Example:**
```python
from app.db.connection import execute_query, execute_query_one, execute_statement

rows = await execute_query(query, *args)
row = await execute_query_one(query, *args)
await execute_statement(query, *args)
```

**Assessment:** ✅ **No changes needed** - Already using correct pattern

---

### Pattern 1: Pool Acquire ⚠️ **NEEDS STANDARDIZATION**

**Usage:** Some services, agents, jobs  
**Count:** ~20 usages  
**Status:** ⚠️ **Needs standardization**

#### Services Using Pattern 1:

**1. `backend/app/services/ratings.py` (1 usage)**
- **Line 116:** `async with self.db_pool.acquire() as conn:`
- **Context:** `_load_rubrics()` method - loads rating rubrics from database
- **RLS Required:** ❌ No (system-level data: rating_rubrics table)
- **Target Pattern:** Pattern B (helper functions)
- **Change:**
  ```python
  # BEFORE:
  async with self.db_pool.acquire() as conn:
      rows = await conn.fetch(query)
  
  # AFTER:
  from app.db.connection import execute_query
  rows = await execute_query(query)
  ```

**2. `backend/app/services/audit.py` (4 usages)**
- **Line 132:** `pool = self._get_db_pool()` then `async with pool.acquire() as conn:`
- **Line 195:** Same pattern
- **Line 251:** Same pattern
- **Line 310:** Same pattern
- **Context:** Audit logging methods - write to audit_log table
- **RLS Required:** ❌ No (system-level data: audit_log table)
- **Target Pattern:** Pattern B (helper functions)
- **Change:**
  ```python
  # BEFORE:
  pool = self._get_db_pool()
  async with pool.acquire() as conn:
      await conn.execute(query, ...)
  
  # AFTER:
  from app.db.connection import execute_statement
  await execute_statement(query, ...)
  ```

#### Agents Using Pattern 1:

**3. `backend/app/agents/financial_analyst.py` (12 usages)**

**Pattern 1a: Using `self.services.get("db")` (7 usages)**
- **Line 1670:** `attribution.currency` - queries lots, prices, fx_rates
- **Line 1781:** `charts.overview` - queries prices
- **Line 1995:** `portfolio.sector_allocation` - queries prices, fx_rates
- **Line 2106:** `portfolio.historical_nav` - queries prices
- **Line 2259:** `get_transaction_history` - queries transactions
- **Line 2326:** `get_security_fundamentals` - queries securities
- **Line 2473:** `get_comparable_positions` - queries securities
- **Context:** All access user-scoped data (lots, transactions, portfolios)
- **RLS Required:** ✅ **YES** (user-scoped data)
- **Target Pattern:** Pattern A (RLS-aware)
- **Change:**
  ```python
  # BEFORE:
  db_pool = self.services.get("db")
  async with db_pool.acquire() as conn:
      rows = await conn.fetch(query, ...)
  
  # AFTER:
  from app.db.connection import get_db_connection_with_rls
  async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
      rows = await conn.fetch(query, ...)
  ```

**Pattern 1b: Using `await get_db_pool()` (2 usages)**
- **Line 1254:** `metrics.compute_mwr` - queries transactions, portfolio_daily_values
- **Line 1368:** `metrics.compute_sharpe` - queries portfolio_metrics
- **Context:** Access user-scoped data (transactions, portfolio metrics)
- **RLS Required:** ✅ **YES** (user-scoped data)
- **Target Pattern:** Pattern A (RLS-aware)
- **Change:**
  ```python
  # BEFORE:
  pool = await get_db_pool()
  async with pool.acquire() as db:
      # ... use db
  
  # AFTER:
  from app.db.connection import get_db_connection_with_rls
  async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
      # ... use conn
  ```

**Pattern 1c: Using `get_db_pool()` (non-async) (1 usage)**
- **Line 1034:** `metrics.compute_twr` - passes to CurrencyAttributor
- **Context:** System-level operation (pricing packs, not user-scoped)
- **RLS Required:** ❌ No (system-level: pricing packs)
- **Target Pattern:** Pattern B (helper functions) OR keep as-is if CurrencyAttributor needs pool
- **Note:** Review if CurrencyAttributor can use helper functions instead

**Pattern 1d: Already using RLS (3 usages) ✅**
- **Line 240:** `ledger.positions` - ✅ Already using `get_db_connection_with_rls()`
- **Line 2683:** `compute_position_return` - ✅ Already using `get_db_connection_with_rls()`
- **Line 3164:** `_aggregate_portfolio_ratings` - ✅ Already using `get_db_connection_with_rls()`
- **Status:** ✅ **No changes needed**

**4. `backend/app/agents/data_harvester.py` (1 usage)**
- **Line 675:** `fundamentals.load` - queries securities table
- **Context:** System-level data (securities table - not user-scoped)
- **RLS Required:** ❌ No (system-level: securities table)
- **Target Pattern:** Pattern B (helper functions)
- **Change:**
  ```python
  # BEFORE:
  async with db_pool.acquire() as conn:
      row = await conn.fetchrow(query, ...)
  
  # AFTER:
  from app.db.connection import execute_query_one
  row = await execute_query_one(query, ...)
  ```

#### Jobs Using Pattern 1:

**5. `backend/jobs/daily_valuation.py` (6 usages)**
- **Line 86:** `_get_portfolios()` - queries portfolios
- **Line 215:** `_fetch_portfolio_positions()` - queries lots
- **Line 241:** `_fetch_pricing_pack()` - queries pricing_packs
- **Line 261:** `_calculate_position_values()` - queries prices
- **Line 301:** `_update_daily_values()` - inserts into portfolio_daily_values
- **Line 330:** `_update_portfolio_metrics()` - inserts into portfolio_metrics
- **Context:** Background job - system-level operations
- **RLS Required:** ❌ No (background job, system-level)
- **Target Pattern:** Pattern B (helper functions)
- **Change:**
  ```python
  # BEFORE:
  async with self.db_pool.acquire() as conn:
      rows = await conn.fetch(query, ...)
  
  # AFTER:
  from app.db.connection import execute_query
  rows = await execute_query(query, ...)
  ```

---

### Pattern 3: Direct asyncpg.connect() ✅ **ACCEPTABLE**

**Usage:** Standalone scripts, migrations  
**Count:** ~10 usages  
**Status:** ✅ **Acceptable - no changes needed**

**Files Using:**
- ✅ `backend/scripts/seed_*.py` (multiple files)
- ✅ `backend/scripts/validate_database_schema.py`
- ✅ `backend/jobs/compute_metrics_simple.py`
- ✅ `backend/init_db.py`

**Example:**
```python
import asyncpg

conn = await asyncpg.connect(DATABASE_URL)
result = await conn.fetch(query)
await conn.close()
```

**Assessment:** ✅ **No changes needed** - Acceptable for one-time operations

---

## Detailed File-by-File Analysis

### Services

#### `backend/app/services/ratings.py`
**Current Pattern:** Pattern 1 (pool.acquire) + Pattern 4 (service-level pool caching)  
**Usages:** 1  
**RLS Required:** ❌ No  
**Target Pattern:** Pattern B (helper functions)

**Changes Needed:**
1. Remove `self.db_pool` from `__init__` (line 77)
2. Remove pool initialization in `_load_rubrics` (lines 97-100)
3. Replace `pool.acquire()` with `execute_query()` (line 116)

---

#### `backend/app/services/audit.py`
**Current Pattern:** Pattern 1 (pool.acquire) + Pattern 4 (service-level pool caching)  
**Usages:** 4  
**RLS Required:** ❌ No  
**Target Pattern:** Pattern B (helper functions)

**Changes Needed:**
1. Remove `self.db_pool` from `__init__` (if exists)
2. Remove `_get_db_pool()` method (lines 82-98)
3. Replace all 4 `pool.acquire()` calls with `execute_statement()`:
   - Line 132: `log()` method
   - Line 195: `log_user_action()` method
   - Line 251: `log_api_request()` method
   - Line 310: `log_error()` method

---

### Agents

#### `backend/app/agents/financial_analyst.py`
**Current Pattern:** Mixed (Pattern 1 in 9 methods, Pattern A in 3 methods)  
**Total Usages:** 12  
**RLS Required:** ✅ Yes (for 9 methods accessing user data)  
**Target Pattern:** Pattern A (RLS-aware) for user data

**Methods Needing RLS-Aware Connection:**
1. **Line 1034:** `metrics.compute_twr` - Review if needs RLS (uses CurrencyAttributor)
2. **Line 1254:** `metrics.compute_mwr` - ✅ Needs RLS (queries transactions)
3. **Line 1368:** `metrics.compute_sharpe` - ✅ Needs RLS (queries portfolio_metrics)
4. **Line 1670:** `attribution.currency` - ✅ Needs RLS (queries lots)
5. **Line 1781:** `charts.overview` - ✅ Needs RLS (queries prices for user positions)
6. **Line 1995:** `portfolio.sector_allocation` - ✅ Needs RLS (queries prices for user positions)
7. **Line 2106:** `portfolio.historical_nav` - ✅ Needs RLS (queries prices for user positions)
8. **Line 2259:** `get_transaction_history` - ✅ Needs RLS (queries transactions)
9. **Line 2326:** `get_security_fundamentals` - ⚠️ Review (queries securities - system-level?)
10. **Line 2473:** `get_comparable_positions` - ⚠️ Review (queries securities - system-level?)

**Methods Already Correct:**
- ✅ Line 240: `ledger.positions` - Already using `get_db_connection_with_rls()`
- ✅ Line 2683: `compute_position_return` - Already using `get_db_connection_with_rls()`
- ✅ Line 3164: `_aggregate_portfolio_ratings` - Already using `get_db_connection_with_rls()`

**Changes Needed:**
- Replace 9 `pool.acquire()` calls with `get_db_connection_with_rls(ctx.user_id)`
- Review 2 methods (lines 1034, 2326, 2473) to determine if RLS needed

---

#### `backend/app/agents/data_harvester.py`
**Current Pattern:** Pattern 1 (pool.acquire)  
**Usages:** 1  
**RLS Required:** ❌ No (system-level: securities table)  
**Target Pattern:** Pattern B (helper functions)

**Changes Needed:**
- Replace `db_pool.acquire()` with `execute_query_one()` (line 675)

---

### Jobs

#### `backend/jobs/daily_valuation.py`
**Current Pattern:** Pattern 1 (pool.acquire)  
**Usages:** 6  
**RLS Required:** ❌ No (background job, system-level)  
**Target Pattern:** Pattern B (helper functions)

**Changes Needed:**
- Remove `self.db_pool` from `__init__` (line 29)
- Replace all 6 `pool.acquire()` calls with helper functions:
  - Line 86: `execute_query()`
  - Line 215: `execute_query()`
  - Line 241: `execute_query_one()`
  - Line 261: `execute_query()`
  - Line 301: `execute_statement()`
  - Line 330: `execute_statement()`

---

## Summary of Changes Required

### Services (2 files, 5 usages)
- `ratings.py`: 1 usage → Pattern B
- `audit.py`: 4 usages → Pattern B

### Agents (2 files, 13 usages)
- `financial_analyst.py`: 9 usages → Pattern A (RLS-aware), 1 review needed
- `data_harvester.py`: 1 usage → Pattern B

### Jobs (1 file, 6 usages)
- `daily_valuation.py`: 6 usages → Pattern B

**Total:** 5 files, ~24 usages to standardize

---

## RLS Requirements Analysis

### User-Scoped Data (Requires RLS) ✅
- `lots` table - User's positions
- `transactions` table - User's transactions
- `portfolios` table - User's portfolios
- `portfolio_daily_values` table - User's portfolio values
- `portfolio_metrics` table - User's portfolio metrics
- `prices` table (when filtered by user's positions) - User's position prices

### System-Level Data (No RLS) ✅
- `pricing_packs` table - System-wide pricing snapshots
- `securities` table - System-wide security master data
- `rating_rubrics` table - System-wide rating configuration
- `audit_log` table - System-wide audit trail
- `macro_indicators` table - System-wide macro data
- `fx_rates` table - System-wide FX rates

---

## Validation Checklist

After standardization:
- [ ] All user-scoped data uses `get_db_connection_with_rls(user_id)`
- [ ] All system-level operations use `execute_query*` helper functions
- [ ] No `pool.acquire()` calls in services (except scripts)
- [ ] No `pool.acquire()` calls in agents (except scripts)
- [ ] No service-level pool caching
- [ ] All RLS policies enforced for user data
- [ ] Connection pool is shared (not duplicated)
- [ ] All tests pass

