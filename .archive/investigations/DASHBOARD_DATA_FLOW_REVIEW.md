# Dashboard Data Flow Review

**Date:** November 2, 2025  
**Purpose:** Comprehensive review of all functions that produce dashboard UI data, database queries, and UI wiring  
**Status:** 📋 ANALYSIS COMPLETE

---

## 📊 Executive Summary

This document provides a complete trace of the data flow from **database to dashboard UI**, reviewing:
1. **Dashboard UI Component** - How it requests data
2. **Pattern Execution** - How `portfolio_overview` pattern orchestrates data gathering
3. **Backend Capabilities** - All agent capabilities used by the dashboard
4. **Database Functions** - All database queries executed
5. **UI Data Mapping** - How UI `dataPath` properties map to backend outputs
6. **Connection Wiring** - Verification that database connections are properly wired

---

## 🔄 Complete Data Flow

### Flow Overview

```
DashboardPage (full_ui.html:8054)
  ↓
PatternRenderer (full_ui.html:3227)
  ↓
apiClient.executePattern('portfolio_overview', {portfolio_id, lookback_days: 252})
  ↓
POST /api/patterns/execute (combined_server.py)
  ↓
PatternOrchestrator.run_pattern() (pattern_orchestrator.py:533)
  ↓
Executes 6 steps sequentially:
  1. ledger.positions → FinancialAnalyst.ledger_positions()
  2. pricing.apply_pack → FinancialAnalyst.pricing_apply_pack()
  3. metrics.compute_twr → FinancialAnalyst.metrics_compute_twr()
  4. attribution.currency → FinancialAnalyst.attribution_currency()
  5. portfolio.sector_allocation → FinancialAnalyst.portfolio_sector_allocation()
  6. portfolio.historical_nav → FinancialAnalyst.portfolio_historical_nav()
  ↓
Aggregates all step outputs into final response
  ↓
Returns to UI: {data: {perf_metrics, currency_attr, valued_positions, sector_allocation, historical_nav}}
  ↓
PatternRenderer extracts data using getDataByPath() and renders panels
```

---

## 📋 Dashboard UI Component Analysis

### Component: DashboardPage

**Location:** `full_ui.html:8054-8063`

**Implementation:**
```javascript
function DashboardPage() {
    const { portfolioId } = useUserContext();
    
    return e('div', { className: 'dashboard-page' },
        e(PatternRenderer, {
            pattern: 'portfolio_overview',
            inputs: { portfolio_id: portfolioId, lookback_days: 252 }
        })
    );
}
```

**Status:** ✅ **CORRECT** - Uses `PatternRenderer` with proper inputs

---

### Component: PatternRenderer

**Location:** `full_ui.html:3227-3313`

**Key Functionality:**
1. Executes pattern via `apiClient.executePattern(pattern, finalInputs)`
2. Receives response: `{data: {...}}` or `{...}`
3. Extracts data using `getDataByPath(data, panel.dataPath)` for each panel
4. Renders panels using `PanelRenderer`

**Status:** ✅ **CORRECT** - Properly extracts data from pattern response

---

### UI Panel Configuration

**Location:** `full_ui.html:2833-2881`

**Panels Defined:**
1. **performance_strip** (metrics_grid)
   - `dataPath: 'perf_metrics'`
   - Maps to pattern output: `perf_metrics`

2. **nav_chart** (line_chart)
   - `dataPath: 'historical_nav'`
   - Maps to pattern output: `historical_nav`

3. **currency_attr** (donut_chart)
   - `dataPath: 'currency_attr'`
   - Maps to pattern output: `currency_attr`

4. **sector_alloc** (pie_chart)
   - `dataPath: 'sector_allocation'`
   - Maps to pattern output: `sector_allocation`

5. **holdings_table** (table)
   - `dataPath: 'valued_positions.positions'`
   - Maps to pattern output: `valued_positions.positions`

**Status:** ✅ **CORRECT** - All `dataPath` properties match pattern output structure

---

## 🎯 Pattern Definition Analysis

### Pattern: portfolio_overview

**Location:** `backend/patterns/portfolio_overview.json`

**Steps (6 total):**

#### Step 1: ledger.positions
- **Capability:** `ledger.positions`
- **Agent:** `FinancialAnalyst`
- **Function:** `ledger_positions()` (financial_analyst.py:79)
- **Returns:** `{positions: [...], ...}` → stored as `positions`

#### Step 2: pricing.apply_pack
- **Capability:** `pricing.apply_pack`
- **Agent:** `FinancialAnalyst`
- **Function:** `pricing_apply_pack()` (financial_analyst.py:202)
- **Args:** Uses `{{positions.positions}}` from Step 1
- **Returns:** `{positions: [...], total_value: ..., ...}` → stored as `valued_positions`

#### Step 3: metrics.compute_twr
- **Capability:** `metrics.compute_twr`
- **Agent:** `FinancialAnalyst`
- **Function:** `metrics_compute_twr()` (financial_analyst.py:356)
- **Returns:** `{twr_1d, twr_mtd, twr_ytd, twr_1y, ...}` → stored as `perf_metrics`

#### Step 4: attribution.currency
- **Capability:** `attribution.currency`
- **Agent:** `FinancialAnalyst`
- **Function:** `attribution_currency()` (financial_analyst.py:559)
- **Returns:** `{local_return, fx_return, interaction_return, total_return, ...}` → stored as `currency_attr`

#### Step 5: portfolio.sector_allocation
- **Capability:** `portfolio.sector_allocation`
- **Agent:** `FinancialAnalyst`
- **Function:** `portfolio_sector_allocation()` (financial_analyst.py:1844)
- **Args:** Uses `{{valued_positions.positions}}` from Step 2
- **Returns:** `{sector_allocation: {...}, total_value: ...}` → stored as `sector_allocation`

#### Step 6: portfolio.historical_nav
- **Capability:** `portfolio.historical_nav`
- **Agent:** `FinancialAnalyst`
- **Function:** `portfolio_historical_nav()` (financial_analyst.py:1961)
- **Returns:** `{data_points: [{date, value}, ...], ...}` → stored as `historical_nav`

**Status:** ✅ **CORRECT** - All steps properly defined and wired

---

## 💾 Database Functions Review

### Capability 1: ledger.positions

**Function:** `FinancialAnalyst.ledger_positions()`  
**Location:** `backend/app/agents/financial_analyst.py:79-199`

**Database Query:**
```sql
SELECT
    l.security_id,
    l.symbol,
    l.qty_open AS qty,
    l.cost_basis,
    l.currency,
    p.base_currency
FROM lots l
JOIN portfolios p ON p.id = l.portfolio_id
WHERE l.portfolio_id = $1
  AND l.is_open = true
  AND l.qty_open > 0
```

**Database Connection:**
- Uses: `get_db_connection_with_rls(ctx.user_id)`
- Location: `financial_analyst.py:116`
- Status: ✅ **CORRECT** - Uses RLS connection manager

**Tables Accessed:**
- `lots` - Position holdings
- `portfolios` - Portfolio metadata

**Output Structure:**
```python
{
    "positions": [
        {
            "security_id": "uuid",
            "symbol": "AAPL",
            "qty": Decimal("100"),
            "cost_basis": Decimal("15000.00"),
            "currency": "USD",
            "base_currency": "CAD"
        },
        ...
    ],
    "portfolio_id": "uuid",
    "base_currency": "CAD",
    ...
}
```

---

### Capability 2: pricing.apply_pack

**Function:** `FinancialAnalyst.pricing_apply_pack()`  
**Location:** `backend/app/agents/financial_analyst.py:202-354`

**Service Used:** `PricingService` (backend/app/services/pricing.py)

**Database Queries (via PricingService):**

**Query 1: Get Prices (get_prices_as_decimals)**
```sql
SELECT security_id, close
FROM prices
WHERE security_id = ANY($1) AND pricing_pack_id = $2
```
- Location: `pricing.py:357-361`
- Tables: `prices`
- Status: ✅ **CORRECT** - Uses `execute_query()` helper

**Query 2: Get FX Rate (get_fx_rate)**
```sql
SELECT
    base_ccy,
    quote_ccy,
    pricing_pack_id,
    asof_ts,
    rate,
    source,
    policy
FROM fx_rates
WHERE base_ccy = $1 AND quote_ccy = $2 AND pricing_pack_id = $3
```
- Location: `pricing.py:470-481`
- Tables: `fx_rates`
- Status: ✅ **CORRECT** - Uses `execute_query_one()` helper

**Database Connection:**
- PricingService uses: `execute_query()` and `execute_query_one()` helpers
- These use: `get_db_connection()` (connection.py:217)
- Status: ✅ **CORRECT** - Uses connection pool correctly

**Output Structure:**
```python
{
    "pricing_pack_id": "PP_2025-10-21",
    "positions": [
        {
            "security_id": "uuid",
            "symbol": "AAPL",
            "qty": Decimal("100"),
            "price": Decimal("175.50"),
            "value_local": Decimal("17550.00"),
            "value": Decimal("23919.75"),  # value_local * fx_rate
            "fx_rate": Decimal("1.3635"),
            "weight": Decimal("0.25"),
            ...
        },
        ...
    ],
    "total_value": Decimal("95679.00"),
    "currency": "CAD",
    ...
}
```

---

### Capability 3: metrics.compute_twr

**Function:** `FinancialAnalyst.metrics_compute_twr()`  
**Location:** `backend/app/agents/financial_analyst.py:356-462`

**Database Queries (via MetricsQueries):**

**Query: Get Latest Metrics**
```sql
SELECT *
FROM portfolio_metrics
WHERE portfolio_id = $1 AND pricing_pack_id = $2
ORDER BY asof_date DESC
LIMIT 1
```
- Location: `metrics_queries.py:253-260`
- Tables: `portfolio_metrics`
- Status: ✅ **CORRECT** - Uses `execute_query_one()` helper

**Database Connection:**
- MetricsQueries uses: `execute_query_one()` helper
- Helper uses: `get_db_connection()` (connection.py:327)
- Status: ✅ **CORRECT** - Uses connection pool correctly

**Output Structure:**
```python
{
    "portfolio_id": "uuid",
    "asof_date": "2025-10-21",
    "pricing_pack_id": "PP_2025-10-21",
    "twr_1d": 0.0012,
    "twr_mtd": 0.0234,
    "twr_ytd": 0.0850,
    "twr_1y": 0.1240,
    "twr_3y": 0.2450,
    "twr_5y": 0.4120,
    "twr_itd": 0.5230,
    ...
}
```

---

### Capability 4: attribution.currency

**Function:** `FinancialAnalyst.attribution_currency()`  
**Location:** `backend/app/agents/financial_analyst.py:559-667`

**Service Used:** `CurrencyAttributor` (backend/app/services/currency_attribution.py)

**Database Queries (via CurrencyAttributor):**

**Query 1: Get Pack Dates**
```sql
SELECT id FROM pricing_packs
WHERE date = $1
ORDER BY created_at DESC
LIMIT 1
```
- Location: `currency_attribution.py:104-112`
- Tables: `pricing_packs`

**Query 2: Get Holdings with Prices and FX Rates**
```sql
SELECT
    l.security_id,
    s.symbol,
    l.currency as local_ccy,
    l.qty_open,
    p_start.close as price_start_local,
    p_end.close as price_end_local,
    fx_start.rate as fx_start,
    fx_end.rate as fx_end
FROM lots l
JOIN securities s ON l.security_id = s.id
JOIN prices p_start ON l.security_id = p_start.security_id
    AND p_start.pricing_pack_id = $3
JOIN prices p_end ON l.security_id = p_end.security_id
    AND p_end.pricing_pack_id = $2
LEFT JOIN fx_rates fx_start ON l.currency = fx_start.base_ccy
    AND fx_start.quote_ccy = $4
    AND fx_start.pricing_pack_id = $3
LEFT JOIN fx_rates fx_end ON l.currency = fx_end.base_ccy
    AND fx_end.quote_ccy = $4
    AND fx_end.pricing_pack_id = $2
WHERE l.portfolio_id = $1
  AND l.qty_open > 0
```
- Location: `currency_attribution.py:123-153`
- Tables: `lots`, `securities`, `prices`, `fx_rates`
- Status: ✅ **CORRECT** - Complex JOIN but properly structured

**Database Connection:**
- CurrencyAttributor uses: `self.db.fetch()` and `self.db.fetchrow()`
- Where `self.db` is the database pool passed to `__init__`
- Location: `financial_analyst.py:617-618` - Gets pool via `get_db_pool()`
- Status: ✅ **CORRECT** - Uses pool directly (service layer pattern)

**Output Structure:**
```python
{
    "portfolio_id": "uuid",
    "asof_date": "2025-10-21",
    "pricing_pack_id": "PP_2025-10-21",
    "base_currency": "CAD",
    "local_return": 0.0850,
    "fx_return": -0.0120,
    "interaction_return": -0.0010,
    "total_return": 0.0720,
    "by_currency": {
        "USD": {"local": 0.08, "fx": 0.0, "interaction": 0.0, "weight": 0.60},
        "EUR": {"local": 0.03, "fx": 0.015, "interaction": 0.0005, "weight": 0.25},
        ...
    },
    "error_bps": 0.05,
    ...
}
```

---

### Capability 5: portfolio.sector_allocation

**Function:** `FinancialAnalyst.portfolio_sector_allocation()`  
**Location:** `backend/app/agents/financial_analyst.py:1844-1959`

**Database Queries:**
- **NONE** - This capability computes sector allocation from `valued_positions` data (already in memory from Step 2)
- Uses hardcoded sector mapping based on symbol (lines 1892-1933)
- No database access required

**Status:** ✅ **CORRECT** - Pure computation, no database queries needed

**Output Structure:**
```python
{
    "sector_allocation": {
        "Technology": 35.5,
        "Healthcare": 22.3,
        "Financial Services": 18.7,
        "Consumer Cyclical": 12.1,
        "Energy": 8.2,
        "Other": 3.2
    },
    "total_sectors": 6,
    "total_value": 95679.00,
    "currency": "CAD",
    ...
}
```

---

### Capability 6: portfolio.historical_nav

**Function:** `FinancialAnalyst.portfolio_historical_nav()`  
**Location:** `backend/app/agents/financial_analyst.py:1961-2055`

**Database Query:**
```sql
SELECT 
    valuation_date as asof_date,
    total_value as total_value_base
FROM portfolio_daily_values
WHERE portfolio_id = $1
  AND valuation_date >= CURRENT_DATE - INTERVAL '%s days'
ORDER BY valuation_date ASC
```
- Location: `financial_analyst.py:2001-2012`
- Tables: `portfolio_daily_values`
- Status: ✅ **CORRECT** - Uses RLS connection manager

**Database Connection:**
- Uses: `get_db_connection_with_rls(ctx.user_id)`
- Location: `financial_analyst.py:1999`
- Status: ✅ **CORRECT** - Uses RLS connection manager

**Output Structure:**
```python
{
    "data_points": [
        {"date": "2025-09-21", "value": 92000.00},
        {"date": "2025-09-22", "value": 92500.00},
        ...
    ],
    "total_points": 30,
    "portfolio_id": "uuid",
    "lookback_days": 30,
    ...
}
```

---

## 🔌 Database Connection Wiring Verification

### Connection Pool Architecture

**Primary Pool Storage:** `sys.modules['__dawsos_db_pool_storage__']`  
**Location:** `backend/app/db/connection.py:40-56`

**Pool Initialization:**
- Function: `init_db_pool()` (connection.py:76)
- Called from: `combined_server.py` at startup
- Storage: Cross-module storage via `sys.modules`
- Status: ✅ **CORRECT** - Ensures single pool instance across all modules

**Pool Access:**
- Function: `get_db_pool()` (connection.py:152)
- Sources:
  1. Cross-module storage (primary)
  2. Direct import from `combined_server` (fallback)
- Status: ✅ **CORRECT** - Two-source fallback ensures reliability

### Connection Usage Patterns

**Pattern 1: RLS Connections (Most Common)**
```python
async with get_db_connection_with_rls(user_id) as conn:
    rows = await conn.fetch(query, ...)
```
- Used by: `ledger_positions`, `portfolio_historical_nav`
- Status: ✅ **CORRECT** - Proper RLS context setting

**Pattern 2: Direct Pool Access**
```python
db = get_db_pool()
rows = await db.fetch(query, ...)
```
- Used by: `CurrencyAttributor`, `PricingService` (via helpers)
- Status: ✅ **CORRECT** - Service layer pattern

**Pattern 3: Helper Functions**
```python
rows = await execute_query(query, ...)
row = await execute_query_one(query, ...)
```
- Used by: `MetricsQueries`, `PricingService`
- Helpers use: `get_db_connection()` internally
- Status: ✅ **CORRECT** - Abstracted connection management

**Pattern 4: Service Layer with Pool Injection**
```python
attr_service = CurrencyAttributor(db)  # db is pool
attribution = await attr_service.compute_attribution(...)
```
- Used by: `attribution_currency`
- Status: ✅ **CORRECT** - Service receives pool, uses it directly

---

## ✅ Data Structure Verification

### Pattern Output Structure

**Expected Structure (from pattern):**
```json
{
  "data": {
    "positions": {...},
    "valued_positions": {
      "positions": [...],
      "total_value": ...,
      "currency": "..."
    },
    "perf_metrics": {
      "twr_ytd": ...,
      "volatility": ...,
      "sharpe": ...,
      ...
    },
    "currency_attr": {
      "local_return": ...,
      "fx_return": ...,
      "interaction_return": ...,
      "total_return": ...,
      ...
    },
    "sector_allocation": {
      "sector_allocation": {...},
      "total_value": ...,
      ...
    },
    "historical_nav": {
      "data_points": [...],
      "total_points": ...,
      ...
    }
  }
}
```

### UI dataPath Mappings

**Panel 1: performance_strip**
- `dataPath: 'perf_metrics'`
- Maps to: `data.perf_metrics` ✅ **CORRECT**

**Panel 2: nav_chart**
- `dataPath: 'historical_nav'`
- Maps to: `data.historical_nav` ✅ **CORRECT**

**Panel 3: currency_attr**
- `dataPath: 'currency_attr'`
- Maps to: `data.currency_attr` ✅ **CORRECT**

**Panel 4: sector_alloc**
- `dataPath: 'sector_allocation'`
- Maps to: `data.sector_allocation` ✅ **CORRECT**

**Panel 5: holdings_table**
- `dataPath: 'valued_positions.positions'`
- Maps to: `data.valued_positions.positions` ✅ **CORRECT**

**Status:** ✅ **ALL MAPPINGS CORRECT** - All UI dataPath properties correctly map to backend output structure

---

## 🔍 Issues Identified

### Issue 1: Sector Allocation Uses Hardcoded Mapping

**Location:** `financial_analyst.py:1892-1933`

**Problem:**
- Uses hardcoded symbol-to-sector mapping
- Should query `securities` table for actual sector data

**Impact:**
- ⚠️ **LOW** - Works but not scalable
- New securities not in mapping default to "Other"

**Recommendation:**
- Query `securities.sector` column if available
- Fall back to hardcoded mapping if not available

---

### Issue 2: Currency Attribution Query Complexity

**Location:** `currency_attribution.py:123-153`

**Problem:**
- Complex 5-table JOIN query
- Could be optimized with materialized views or denormalization

**Impact:**
- ⚠️ **LOW** - Works correctly but may be slow on large portfolios

**Recommendation:**
- Monitor query performance
- Consider materialized view if performance becomes issue

---

## ✅ Summary

### Database Functions Status

| Capability | Function | Database Queries | Connection Pattern | Status |
|------------|----------|------------------|-------------------|--------|
| ledger.positions | `ledger_positions()` | 1 query (lots, portfolios) | RLS connection | ✅ CORRECT |
| pricing.apply_pack | `pricing_apply_pack()` | 2 queries (prices, fx_rates) | Service helpers | ✅ CORRECT |
| metrics.compute_twr | `metrics_compute_twr()` | 1 query (portfolio_metrics) | Helper functions | ✅ CORRECT |
| attribution.currency | `attribution_currency()` | 2 queries (pricing_packs, lots+securities+prices+fx_rates) | Service pool access | ✅ CORRECT |
| portfolio.sector_allocation | `portfolio_sector_allocation()` | 0 queries (computed) | N/A | ✅ CORRECT |
| portfolio.historical_nav | `portfolio_historical_nav()` | 1 query (portfolio_daily_values) | RLS connection | ✅ CORRECT |

### UI Wiring Status

| Component | Pattern | dataPath Mapping | Status |
|-----------|---------|------------------|--------|
| DashboardPage | Uses PatternRenderer | N/A | ✅ CORRECT |
| PatternRenderer | Executes pattern | Extracts data correctly | ✅ CORRECT |
| performance_strip | perf_metrics | `perf_metrics` | ✅ CORRECT |
| nav_chart | historical_nav | `historical_nav` | ✅ CORRECT |
| currency_attr | currency_attr | `currency_attr` | ✅ CORRECT |
| sector_alloc | sector_allocation | `sector_allocation` | ✅ CORRECT |
| holdings_table | valued_positions | `valued_positions.positions` | ✅ CORRECT |

### Overall Status

**✅ ALL SYSTEMS CORRECTLY WIRED**

- All database functions properly connected to UI
- All dataPath mappings correct
- All database queries use proper connection patterns
- All connection pool access is correct
- No critical issues identified

**Minor Improvements:**
1. Sector allocation could query database instead of hardcoded mapping
2. Currency attribution query could be optimized (but works correctly)

---

## 📝 Recommendations

### Immediate Actions
- **NONE** - All systems correctly wired

### Future Improvements
1. **Sector Allocation Enhancement**
   - Query `securities.sector` column if available
   - Fall back to hardcoded mapping

2. **Performance Monitoring**
   - Monitor currency attribution query performance
   - Consider materialized views if needed

3. **Error Handling**
   - Add better error messages for missing data
   - Provide fallback UI states for empty data

---

**Review Complete** ✅

