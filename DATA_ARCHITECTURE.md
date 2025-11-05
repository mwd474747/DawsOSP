# Data Architecture

**Version:** 1.0  
**Last Updated:** January 14, 2025  
**Status:** ✅ **COMPREHENSIVE DOCUMENTATION**

---

## 📊 Overview

This document describes the complete data architecture of DawsOS, including data flow, storage patterns, computation strategies, and access patterns. It serves as the single source of truth for understanding how data moves through the system.

---

## 🔄 Complete Data Flow

### End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE DATA FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CLIENT REQUEST                                              │
│     POST /api/patterns/execute                                 │
│     {pattern: "portfolio_overview", inputs: {portfolio_id}}    │
│     ↓                                                           │
│  2. API LAYER (combined_server.py)                             │
│     - Validates request                                        │
│     - Extracts JWT token (user_id)                             │
│     - Creates RequestCtx with pricing_pack_id                 │
│     - Calls PatternOrchestrator                                │
│     ↓                                                           │
│  3. PATTERN ORCHESTRATOR                                       │
│     - Loads pattern JSON from backend/patterns/               │
│     - Resolves templates: {{inputs.x}}, {{ctx.y}}              │
│     - Executes steps sequentially                              │
│     - Stores step results in state dict                        │
│     ↓                                                           │
│  4. AGENT RUNTIME                                               │
│     - Routes capability to appropriate agent                   │
│     - Example: "ledger.positions" → FinancialAnalyst          │
│     ↓                                                           │
│  5. AGENT EXECUTION                                             │
│     Pattern A: Direct Database Access                         │
│       → Uses get_db_connection_with_rls()                      │
│       → Queries lots table directly                             │
│       → Returns positions with quantity field                  │
│                                                                 │
│     Pattern B: Service Layer Access                            │
│       → Uses PricingService.get_price()                        │
│       → Service queries prices table                           │
│       → Returns price data                                     │
│     ↓                                                           │
│  6. SERVICE LAYER (if used)                                    │
│     Pattern A: Compute On-Demand                              │
│       → CurrencyAttributionService.compute_attribution()       │
│       → Queries lots, prices, fx_rates directly                │
│       → Computes attribution fresh                             │
│       → Returns result (does NOT write to cache table)     │
│                                                                 │
│     Pattern B: Query Stored Data                              │
│       → PerformanceCalculator.compute_twr()                    │
│       → Queries portfolio_daily_values hypertable           │
│       → Computes TWR from stored NAV data                      │
│       → Returns result                                         │
│     ↓                                                           │
│  7. DATABASE LAYER                                             │
│     Connection Pool (asyncpg)                                  │
│     → Cross-module storage (sys.modules)                       │
│     → RLS support for user-scoped queries                       │
│     → Parameterized queries (SQL injection safe)               │
│     ↓                                                           │
│  8. POSTGRESQL + TIMESCALEDB                                   │
│     → 22 active tables                                          │
│     → 8 hypertables for time-series                            │
│     → Pricing packs for reproducibility                        │
│     ↓                                                           │
│  9. RESULT AGGREGATION                                         │
│     Pattern orchestrator collects step results                 │
│     Stores in state dict                                        │
│     Next step can reference previous results                   │
│     ↓                                                           │
│  10. API RESPONSE                                               │
│      Returns aggregated results                                │
│      Includes trace_id for debugging                            │
│      ↓                                                          │
│  11. FRONTEND                                                    │
│       React components render data                              │
│       PatternRenderer handles pattern-specific rendering        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Layer

### Connection Management

**Pattern:** Cross-module pool storage using `sys.modules`

**Implementation:** `backend/app/db/connection.py`

**Key Features:**
- Single pool instance shared across all modules
- RLS support via `get_db_connection_with_rls(user_id)`
- Parameterized queries (SQL injection safe)
- Connection pooling: min_size=5, max_size=20

**Usage:**
```python
# Register pool (in combined_server.py)
from app.db.connection import register_external_pool
register_external_pool(pool)

# Access pool (in any module)
from app.db.connection import get_db_pool
pool = get_db_pool()
```

**See Also:** [DATABASE.md](DATABASE.md) - Database Connection Architecture section

---

### Table Categories

#### 1. Core Portfolio Tables ✅ **ACTIVE**
- `portfolios` - Portfolio metadata
- `lots` - Position holdings (source of truth)
- `transactions` - Trade history
- `securities` - Security master data

**Usage:** Direct queries by agents and services

#### 2. Pricing & Market Data ✅ **ACTIVE**
- `pricing_packs` - Immutable pricing snapshots
- `prices` - Security prices (tied to pricing packs)
- `fx_rates` - FX rates (tied to pricing packs)

**Usage:** Accessed via `PricingService` (service layer)

#### 3. Time-Series Tables (Hypertables) ✅ **ACTIVE**
- `portfolio_daily_values` - Daily NAV tracking
- `portfolio_metrics` - Performance metrics time-series
- `portfolio_cash_flows` - Cash flow tracking
- `macro_indicators` - Economic indicators

**Usage:** Queried by services for historical data

#### 4. Cache Tables ⚠️ **UNUSED**
- `currency_attribution` - Table exists, service computes fresh
- `factor_exposures` - Table exists, service computes fresh

**Status:** ⚠️ **TABLES EXIST BUT NOT USED** - See recommendations below

#### 5. Risk & Scenario Tables ✅ **ACTIVE**
- `regime_history` - Economic regime detection
- `scenario_shocks` - Shock scenario definitions
- `position_factor_betas` - Security-level factor exposures

**Usage:** Queried by services for risk analysis

---

## 🔧 Service Layer Patterns

### Pattern A: Compute On-Demand (No Caching)

**Services:**
- `CurrencyAttributor` - Computes currency attribution fresh
- `FactorAnalyzer` - Computes factor exposures fresh
- `RiskMetrics` - Computes VaR/CVaR fresh
- `ScenarioService` - Computes scenario results fresh

**Characteristics:**
- Always computes fresh (no caching)
- Queries database directly for source data
- Returns computed results
- **Does NOT write to cache tables**

**Example:**
```python
# CurrencyAttributor.compute_attribution()
# 1. Queries lots, prices, fx_rates directly
# 2. Computes attribution fresh
# 3. Returns result (does NOT write to currency_attribution table)
```

**Rationale:**
- Computations are fast enough (< 1 second)
- Data changes frequently (pricing packs update daily)
- Caching would add complexity without significant benefit

---

### Pattern B: Query Stored Data

**Services:**
- `PerformanceCalculator` - Queries `portfolio_daily_values` hypertable
- `PricingService` - Queries `prices`, `fx_rates` from pricing packs

**Characteristics:**
- Queries pre-computed data from hypertables
- Data written by nightly jobs (not by service)
- Fast retrieval (< 100ms)

**Example:**
```python
# PerformanceCalculator.compute_twr()
# 1. Queries portfolio_daily_values hypertable
# 2. Computes TWR from stored NAV data
# 3. Returns result
```

**Rationale:**
- Historical data expensive to compute
- Written once by nightly job
- Read many times by services

---

### Pattern C: Mixed Pattern (Compute + Query)

**Services:**
- `PerformanceCalculator` - Queries `portfolio_daily_values`, computes TWR
- `ScenarioService` - Queries positions, computes factor exposures on-the-fly

**Characteristics:**
- Queries source data from database
- Computes derived metrics on-the-fly
- Returns computed results

**Rationale:**
- Source data stored, derived metrics computed
- Balance between storage and computation

---

## 🔄 Data Access Patterns

### Pattern A: Direct Database Access

**When Used:**
- Simple queries without business logic
- Agent-level data access (e.g., `ledger.positions`)
- User-scoped queries (RLS required)

**Example:**
```python
# financial_analyst.py.ledger_positions()
async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
    rows = await conn.fetch(
        "SELECT * FROM lots WHERE portfolio_id = $1",
        portfolio_uuid
    )
```

**Guidelines:**
- ✅ Use for simple queries (SELECT only)
- ✅ Use when RLS is required
- ⚠️ Avoid for complex business logic
- ⚠️ Avoid for computations

---

### Pattern B: Service Layer Access

**When Used:**
- Business logic (e.g., pricing, metrics)
- Computations (e.g., attribution, factors)
- Reusable functionality

**Example:**
```python
# financial_analyst.py.pricing_apply_pack()
pricing_service = get_pricing_service()
price = await pricing_service.get_price(security_id, pack_id)
```

**Guidelines:**
- ✅ Use for business logic
- ✅ Use for computations
- ✅ Use for reusable functionality
- ✅ Prefer service layer over direct DB access

---

## 📊 Computation vs Storage Strategy

### Current Implementation

| Pattern | Tables | Status | Usage |
|---------|--------|--------|-------|
| **Computed On-Demand** | `currency_attribution`, `factor_exposures` | ⚠️ Tables exist but not used | Services compute fresh |
| **Stored & Retrieved** | `portfolio_daily_values`, `portfolio_metrics` | ✅ Active | Services query stored data |
| **Hybrid** | `prices`, `fx_rates` | ✅ Active | Written by jobs, queried by services |

### Unused Cache Tables ⚠️ **ARCHITECTURAL DEBT**

**Tables:**
- `currency_attribution` - Table exists, service computes fresh
- `factor_exposures` - Table exists, service computes fresh

**Current Behavior:**
- Services compute fresh every time
- Never write to cache tables
- Tables exist but unused

**Impact:**
- Wasted database resources
- Confusing architecture
- No performance benefit

**Recommendation:**
- **Option A (Recommended):** Remove unused cache tables
- **Option B:** Implement caching with TTL (more complex)

**See Also:** [DATA_ARCHITECTURE_ANALYSIS.md](DATA_ARCHITECTURE_ANALYSIS.md) - Recommendations section

---

## 🔐 Data Consistency & Validation

### Pricing Pack Pattern ✅ **CONSISTENT**

**Purpose:** Ensure reproducibility of portfolio valuations

**Pattern:**
- All valuations reference `pricing_pack_id`
- Pricing packs are immutable snapshots
- Same pack_id → same results (byte-for-byte)

**Usage:**
- Request context includes `pricing_pack_id`
- Patterns reference `{{ctx.pricing_pack_id}}`
- Services use `pricing_pack_id` for all queries

**See Also:** [PRICING_PACK_ARCHITECTURE.md](PRICING_PACK_ARCHITECTURE.md)

---

### Field Naming Standards ✅ **STANDARDIZED**

**Database Layer:**
- Columns: `quantity_open`, `quantity_original`
- Legacy: `quantity` (deprecated)

**Agent Layer:**
- Return field: `quantity` (standardized)

**Service Layer:**
- Internal: `qty` (acceptable for service-to-service)

**See Also:** [ARCHITECTURE.md](ARCHITECTURE.md) - Field Naming Standards section

---

### Error Handling Patterns ⚠️ **INCONSISTENT**

**Current Patterns:**

1. **Return Empty Results:**
   - `CurrencyAttributor` - Returns empty dict with error message
   - `PerformanceCalculator` - Returns empty result if no data

2. **Raise Exceptions:**
   - `PricingService` - Raises `PricingPackNotFoundError`
   - `FinancialAnalyst` - Raises `ValueError` for invalid inputs

3. **Fallback to Stub Data:**
   - `FinancialAnalyst.ledger_positions()` - Falls back to stub data if DB fails

**Recommendation:**
- Standardize error handling patterns
- Document error handling guidelines
- Use custom exceptions for business logic errors

---

## 🎯 Stability Recommendations

### Priority 1: Resolve Unused Cache Tables ⚠️ **HIGH IMPACT**

**Issue:** `currency_attribution`, `factor_exposures` tables exist but not used

**Options:**

**Option A: Remove Tables (Recommended)**
- **Pros:** Simpler, less confusion, no wasted resources
- **Cons:** Lose potential caching benefit
- **Action:** Create migration to drop tables

**Option B: Implement Caching**
- **Pros:** Better performance, reduced computation
- **Cons:** More complex, need TTL strategy
- **Action:** 
  1. Add TTL columns to cache tables
  2. Implement `get_or_compute()` pattern
  3. Add cache invalidation on data changes

**Recommendation:** **Option A** - Current performance is acceptable, simpler is better

---

### Priority 2: Document Data Access Guidelines ⚠️ **MEDIUM IMPACT**

**Issue:** No clear guidelines on when to use direct DB vs service layer

**Recommendation:**
1. Document guidelines in DEVELOPMENT_GUIDE.md
2. Prefer service layer for business logic
3. Direct DB acceptable for simple queries

**Guidelines:**
- ✅ **Direct DB:** Simple queries (SELECT only), RLS required
- ✅ **Service Layer:** Business logic, computations, reusable functionality

---

### Priority 3: Standardize Error Handling ⚠️ **MEDIUM IMPACT**

**Issue:** Inconsistent error handling across services

**Recommendation:**
1. Document error handling patterns
2. Use custom exceptions for business logic errors
3. Standardize error response format

**Patterns:**
- **Business Logic Errors:** Use custom exceptions (`PricingPackNotFoundError`)
- **Data Validation:** Return empty results with error message
- **System Errors:** Raise exceptions, log errors

---

### Priority 4: Add TTL Strategy (If Caching) ⚠️ **LOW PRIORITY**

**Issue:** No cache invalidation or freshness guarantees

**Recommendation:**
- Add `expires_at` column to cache tables
- Implement cache invalidation on data changes
- Add freshness checks in services

**Impact:**
- Better data freshness guarantees
- Automatic cache invalidation
- Prevents stale data issues

**Priority:** **Defer** - Only needed if implementing caching

---

## 📋 Data Flow Examples

### Example 1: Portfolio Overview Pattern

```
1. Pattern: portfolio_overview.json
   ↓
2. Step 1: ledger.positions
   → FinancialAnalyst.ledger_positions()
   → Direct DB: SELECT * FROM lots WHERE portfolio_id = $1
   → Returns: positions with quantity field
   ↓
3. Step 2: pricing.apply_pack
   → FinancialAnalyst.pricing_apply_pack()
   → Service Layer: PricingService.get_price()
   → Service queries: SELECT * FROM prices WHERE pricing_pack_id = $1
   → Returns: valued_positions with prices
   ↓
4. Step 3: metrics.compute_twr
   → FinancialAnalyst.metrics_compute_twr()
   → Service Layer: PerformanceCalculator.compute_twr()
   → Service queries: SELECT * FROM portfolio_daily_values WHERE portfolio_id = $1
   → Returns: perf_metrics
   ↓
5. Result: Aggregated results returned to frontend
```

---

### Example 2: Corporate Actions Pattern

```
1. Pattern: corporate_actions_upcoming.json
   ↓
2. Step 1: ledger.positions
   → FinancialAnalyst.ledger_positions()
   → Direct DB: SELECT * FROM lots WHERE portfolio_id = $1
   → Returns: positions with quantity field
   ↓
3. Step 2: corporate_actions.upcoming
   → DataHarvester.corporate_actions_upcoming()
   → Extracts symbols from positions (uses quantity field)
   → Fetches from FMP API (dividends, splits, earnings)
   → Filters by portfolio holdings
   → Returns: actions list
   ↓
4. Step 3: corporate_actions.calculate_impact
   → DataHarvester.corporate_actions_calculate_impact()
   → Uses positions with quantity field
   → Calculates portfolio impact
   → Returns: actions_with_impact
   ↓
5. Result: Corporate actions with portfolio impact
```

---

## 🔍 Data Consistency Guarantees

### Pricing Pack Reproducibility ✅

**Guarantee:** Same `pricing_pack_id` → same results

**Implementation:**
- Pricing packs are immutable snapshots
- All prices and FX rates tied to `pricing_pack_id`
- Services use `pricing_pack_id` for all queries

**Validation:**
- SHA-256 hash of all prices + FX rates
- Reconciliation checks (±1bp tolerance)

---

### Field Naming Consistency ✅

**Guarantee:** Consistent field names across layers

**Implementation:**
- Database: `quantity_open`, `quantity_original`
- Agent: `quantity` (standardized)
- Service: `qty` (internal, acceptable)

**Validation:**
- Standardized in January 2025 (Phase 1)
- All agent capabilities return `quantity`

---

### Data Access Security ✅

**Guarantee:** User-scoped data access via RLS

**Implementation:**
- `get_db_connection_with_rls(user_id)` enforces RLS
- All user-scoped queries use RLS
- Pattern-level rights checks

**Validation:**
- RLS policies enforce user-scoped access
- JWT token provides `user_id`

---

## ⚠️ Known Issues & Gaps

### Critical Issues

1. **Silent Stub Data in Risk Analytics** ⚠️ **CRITICAL - USER TRUST ISSUE**
   - `risk.compute_factor_exposures` returns hardcoded fake data with NO warnings
   - **Location:** `backend/app/agents/financial_analyst.py` lines 1086-1110
   - **Impact:** Users see meaningless data, destroys credibility if discovered
   - **Recommendation:** Add `_provenance` field with warnings (Phase 1 - 4 hours)
   - **See Also:** [REFACTORING_MASTER_PLAN.md](REFACTORING_MASTER_PLAN.md) - Issue 1

2. **Unused Cache Tables** ⚠️
   - `currency_attribution`, `factor_exposures` tables exist but not used
   - **Impact:** Wasted resources, confusing architecture
   - **Recommendation:** Remove tables or implement caching

2. **No TTL Strategy** ⚠️
   - No cache invalidation or freshness guarantees
   - **Impact:** Potential for stale data (if caching implemented)
   - **Recommendation:** Add TTL columns if implementing caching

### Medium Issues

3. **Pattern Output Format Chaos** ⚠️
   - 3 incompatible response formats across patterns
   - Orchestrator extracts `{"data": {"panels": [...]}}` instead of actual step results
   - **Impact:** UI shows "No data" or crashes, silent failures
   - **Recommendation:** Fix pattern output extraction (Phase 1 - 4 hours)
   - **See Also:** [REFACTORING_MASTER_PLAN.md](REFACTORING_MASTER_PLAN.md) - Issue 2

4. **No Pattern Validation** ⚠️
   - Patterns can reference undefined steps
   - No capability contracts
   - No input validation
   - **Impact:** Runtime errors instead of compile-time validation
   - **Recommendation:** Add step dependency validation (Phase 2 - 8 hours)
   - **See Also:** [REFACTORING_MASTER_PLAN.md](REFACTORING_MASTER_PLAN.md) - Issue 3

5. **Mixed Data Access Patterns** ⚠️
   - No clear guidelines on direct DB vs service layer
   - **Impact:** Inconsistent patterns, harder to maintain
   - **Recommendation:** Document guidelines

6. **Inconsistent Error Handling** ⚠️
   - Different patterns across services
   - **Impact:** Inconsistent user experience
   - **Recommendation:** Standardize error handling

---

## 📚 Related Documentation

- **[DATABASE.md](DATABASE.md)** - Database schema, tables, migrations
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture, patterns
- **[PRICING_PACK_ARCHITECTURE.md](PRICING_PACK_ARCHITECTURE.md)** - Pricing pack system
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Development guidelines
- **[DATA_ARCHITECTURE_ANALYSIS.md](DATA_ARCHITECTURE_ANALYSIS.md)** - Detailed analysis

---

## ✅ Summary

**Current State:**
- ✅ Database layer well-designed and stable
- ✅ Pricing pack pattern ensures reproducibility
- ✅ Field naming standardized
- ⚠️ Service layer patterns inconsistent
- ⚠️ Unused cache tables create confusion

**Data Architecture:**
- **Consistent:** Connection pooling, pricing packs, field naming
- **Inconsistent:** Computation vs storage, data access patterns
- **Missing:** TTL strategy, comprehensive error handling

**Recommendations:**
1. **Remove unused cache tables** - Simplify architecture
2. **Document data access guidelines** - Standardize patterns
3. **Standardize error handling** - Consistent user experience

**Stability Assessment:**
- ✅ **System is stable** - Works correctly
- ⚠️ **Documentation gaps** - Make maintenance harder
- ✅ **No critical issues** - Production-ready

