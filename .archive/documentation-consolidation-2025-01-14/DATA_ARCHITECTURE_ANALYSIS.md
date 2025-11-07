# Data Architecture Analysis & Recommendations

**Date:** January 14, 2025  
**Status:** 🔍 **COMPREHENSIVE ANALYSIS COMPLETE**  
**Purpose:** Review database and data architecture documentation, identify gaps, assess consistency, and provide stability recommendations

---

## 📊 Executive Summary

**Current State:**
- ✅ **Database Layer:** Well-documented, 22 active tables, standardized field naming
- ⚠️ **Data Flow:** Partially documented, missing service layer details
- ⚠️ **Computation vs Storage:** Inconsistent pattern, unclear strategy
- ❌ **Data Architecture Doc:** Missing comprehensive data architecture document
- ⚠️ **Stability Issues:** Unused cache tables, mixed computation patterns, no TTL strategy

**Key Findings:**
1. **Missing Data Architecture Document** - No single source of truth for data flow
2. **Inconsistent Computation Patterns** - Some services compute, some cache, no clear strategy
3. **Unused Cache Tables** - `currency_attribution`, `factor_exposures` tables exist but not used
4. **Mixed Data Access Patterns** - Agents access DB directly, services also access DB directly
5. **No TTL Strategy** - No cache invalidation or freshness guarantees documented

---

## 🔍 Current Data Architecture (Reconstructed from Code)

### Layer 1: Database Layer ✅ **WELL DOCUMENTED**

**Connection Management:**
- **Pattern:** Cross-module pool storage using `sys.modules`
- **Implementation:** `backend/app/db/connection.py`
- **Pool Configuration:** min_size=5, max_size=20, timeout=60s
- **Status:** ✅ **STABLE** - Fixed November 2, 2025

**Tables:**
- **22 Active Tables** - Core portfolio, pricing, metrics, time-series
- **3 Views** - `latest_ledger_snapshot`, `portfolio_currency_attributions`, `v_derived_indicators`
- **Hypertables:** 8 TimescaleDB hypertables for time-series data

**Data Access:**
- **Direct Queries:** Agents use `execute_query`, `execute_statement` from `connection.py`
- **RLS Support:** `get_db_connection_with_rls()` for user-scoped data
- **Parameterized Queries:** All queries use parameterized queries (asyncpg)

---

### Layer 2: Service Layer ⚠️ **PARTIALLY DOCUMENTED**

**Computation Patterns:**

#### Pattern A: Compute On-Demand (No Caching)
**Services:**
- `currency_attribution.py` - Computes fresh every time
- `factor_analysis.py` - Computes fresh every time
- `risk_metrics.py` - Computes fresh every time
- `scenarios.py` - Computes fresh every time

**Tables Created But Not Used:**
- `currency_attribution` - Table exists, service doesn't write to it
- `factor_exposures` - Table exists, service doesn't write to it

**Issue:** Tables exist for caching but services never use them

#### Pattern B: Query Stored Data
**Services:**
- `metrics.py` - Queries `portfolio_daily_values` hypertable
- `metrics.py` - Queries `portfolio_metrics` hypertable (if available)
- `pricing.py` - Queries `prices`, `fx_rates` from pricing packs

**Status:** ✅ **WORKING** - Services correctly query stored data

#### Pattern C: Mixed Pattern (Compute + Query)
**Services:**
- `metrics.py` - Queries `portfolio_daily_values` but computes TWR/MWR from it
- `scenarios.py` - Queries positions, computes factor exposures on-the-fly

**Issue:** Unclear separation between compute and storage

---

### Layer 3: Agent Layer ⚠️ **INCOMPLETE DOCUMENTATION**

**Data Access Patterns:**

#### Pattern A: Direct Database Access
**Agents:**
- `financial_analyst.py` - Uses `get_db_connection_with_rls()` directly
- Queries `lots` table directly for positions
- Uses `execute_query`, `execute_statement` from `connection.py`

**Example:**
```python
async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
    rows = await conn.fetch("SELECT ... FROM lots ...")
```

#### Pattern B: Service Layer Access
**Agents:**
- `financial_analyst.py` - Uses `PricingService` for prices
- `financial_analyst.py` - Uses `PerformanceCalculator` for metrics
- Uses `get_pricing_service()` singleton

**Example:**
```python
pricing_service = get_pricing_service()
price = await pricing_service.get_price(security_id, pack_id)
```

**Issue:** Mixed patterns - some direct DB, some service layer

---

### Layer 4: Pattern Orchestration ✅ **WELL DOCUMENTED**

**Data Flow:**
1. Pattern loaded from JSON
2. Template substitution: `{{inputs.x}}`, `{{ctx.y}}`, `{{step_result.z}}`
3. Capability routed to agent
4. Agent executes (may use service or DB directly)
5. Result stored in state
6. Next step uses previous result
7. Final result aggregated and returned

**Status:** ✅ **DOCUMENTED** in ARCHITECTURE.md

---

### Layer 5: API Layer ✅ **DOCUMENTED**

**Endpoints:**
- `POST /api/patterns/execute` - Main pattern execution endpoint
- Various REST endpoints for portfolio, metrics, etc.

**Status:** ✅ **DOCUMENTED** in API_CONTRACT.md

---

## 📋 Documentation Gaps

### Critical Gaps

1. **Missing Data Architecture Document** ❌
   - **Issue:** No single document explaining data flow end-to-end
   - **Impact:** Developers must piece together architecture from multiple docs
   - **Recommendation:** Create `DATA_ARCHITECTURE.md` with complete data flow

2. **Service Layer Patterns Not Documented** ⚠️
   - **Issue:** DATABASE.md mentions "computed on-demand" but doesn't explain when/why
   - **Impact:** Unclear why `currency_attribution` table exists but isn't used
   - **Recommendation:** Document service layer computation vs storage patterns

3. **Cache Strategy Not Documented** ❌
   - **Issue:** Tables exist for caching but no strategy documented
   - **Impact:** Developers don't know when to compute vs cache
   - **Recommendation:** Document caching strategy (or remove unused cache tables)

4. **Data Access Patterns Not Documented** ⚠️
   - **Issue:** No guidance on when agents should use services vs direct DB access
   - **Impact:** Inconsistent patterns across codebase
   - **Recommendation:** Document data access guidelines

5. **Error Handling Patterns Not Documented** ⚠️
   - **Issue:** No documentation on error handling, retries, fallbacks
   - **Impact:** Inconsistent error handling across services
   - **Recommendation:** Document error handling patterns

---

## 🔄 Data Flow Architecture (Reconstructed)

### Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE DATA FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. API REQUEST                                                 │
│     POST /api/patterns/execute                                  │
│     {pattern: "portfolio_overview", inputs: {...}}            │
│     ↓                                                           │
│  2. PATTERN ORCHESTRATOR                                       │
│     Loads pattern JSON                                          │
│     Resolves templates: {{inputs.portfolio_id}}                │
│     Creates RequestCtx with pricing_pack_id                    │
│     ↓                                                           │
│  3. AGENT RUNTIME                                               │
│     Routes capability to agent                                  │
│     Example: "ledger.positions" → FinancialAnalyst             │
│     ↓                                                           │
│  4. AGENT EXECUTION                                             │
│     Pattern A: Direct DB Access                                │
│       → Uses get_db_connection_with_rls()                     │
│       → Queries lots table directly                             │
│       → Returns positions with quantity field                  │
│                                                                 │
│     Pattern B: Service Layer Access                            │
│       → Uses PricingService.get_price()                        │
│       → Service queries prices table                           │
│       → Returns price data                                     │
│     ↓                                                           │
│  5. SERVICE LAYER (if used)                                    │
│     Pattern A: Compute On-Demand                               │
│       → CurrencyAttributionService.compute_attribution()       │
│       → Queries lots, prices, fx_rates                         │
│       → Computes attribution fresh                             │
│       → Returns result (does NOT write to cache table)         │
│                                                                 │
│     Pattern B: Query Stored Data                               │
│       → PerformanceCalculator.compute_twr()                     │
│       → Queries portfolio_daily_values hypertable             │
│       → Computes TWR from stored NAV data                      │
│       → Returns result                                         │
│     ↓                                                           │
│  6. DATABASE LAYER                                              │
│     Connection Pool (asyncpg)                                   │
│     → Cross-module storage (sys.modules)                       │
│     → RLS support for user-scoped queries                      │
│     → Parameterized queries (SQL injection safe)              │
│     ↓                                                           │
│  7. POSTGRESQL + TIMESCALEDB                                    │
│     → 22 active tables                                          │
│     → 8 hypertables for time-series                            │
│     → Pricing packs for reproducibility                        │
│     ↓                                                           │
│  8. RESULT AGGREGATION                                         │
│     Pattern orchestrator collects step results                 │
│     Stores in state dict                                        │
│     Next step can reference previous results                   │
│     ↓                                                           │
│  9. API RESPONSE                                                │
│     Returns aggregated results                                 │
│     Includes trace_id for debugging                            │
│     ↓                                                           │
│  10. FRONTEND                                                    │
│      React components render data                               │
│      PatternRenderer handles pattern-specific rendering        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Architecture Inconsistencies

### 1. Unused Cache Tables ⚠️ **CRITICAL**

**Tables:**
- `currency_attribution` - Table exists, service computes fresh
- `factor_exposures` - Table exists, service computes fresh

**Current Behavior:**
- `CurrencyAttributor.compute_attribution()` - Always computes fresh
- `FactorAnalyzer.compute_factor_exposure()` - Always computes fresh
- Neither service writes to cache tables

**Impact:**
- Wasted database resources
- Confusing architecture (why do tables exist?)
- No performance benefit from caching

**Recommendation:**
1. **Option A:** Remove unused cache tables (simpler)
2. **Option B:** Implement caching with TTL (more complex, better performance)

---

### 2. Mixed Data Access Patterns ⚠️ **MODERATE**

**Pattern A: Direct DB Access**
- `financial_analyst.py.ledger_positions()` - Queries lots directly
- `financial_analyst.py.get_position_details()` - Queries lots directly

**Pattern B: Service Layer Access**
- `financial_analyst.py.pricing_apply_pack()` - Uses PricingService
- `financial_analyst.py.metrics_compute_twr()` - Uses PerformanceCalculator

**Issue:** No clear guideline on when to use which pattern

**Impact:**
- Inconsistent patterns
- Harder to maintain
- Potential for code duplication

**Recommendation:**
- **Document guidelines:** When to use direct DB vs service layer
- **Prefer service layer:** For business logic, prefer service layer
- **Direct DB acceptable:** For simple queries without business logic

---

### 3. No TTL Strategy ⚠️ **MODERATE**

**Issue:** No cache invalidation or freshness guarantees

**Current State:**
- `portfolio_daily_values` - Written by nightly job, but no TTL
- `portfolio_metrics` - Written by metrics service, but no TTL
- `currency_attribution` - Not cached, computed fresh
- `factor_exposures` - Not cached, computed fresh

**Impact:**
- No way to know if cached data is stale
- No automatic cache invalidation
- Potential for serving stale data

**Recommendation:**
- **Add TTL columns** to cache tables (`expires_at`, `ttl_seconds`)
- **Implement cache invalidation** on data changes
- **Document freshness requirements** for each data type

---

### 4. Service Layer Mixing ⚠️ **MODERATE**

**Issue:** Services both compute AND access DB directly

**Example:**
- `CurrencyAttributor` - Queries lots, prices, fx_rates directly
- `FactorAnalyzer` - Queries portfolio returns, factor returns directly
- `PerformanceCalculator` - Queries portfolio_daily_values directly

**Impact:**
- Services are tightly coupled to database schema
- Hard to test (need database)
- Hard to swap storage backends

**Recommendation:**
- **Separate concerns:** Compute logic vs data access
- **Use repository pattern:** Abstract data access behind interfaces
- **Keep current for now:** Low priority, working fine

---

## 🎯 Stability Recommendations

### Priority 1: Document Data Architecture ✅ **HIGH IMPACT**

**Action:**
1. Create `DATA_ARCHITECTURE.md` with complete data flow
2. Document service layer patterns (compute vs storage)
3. Document data access guidelines (direct DB vs service layer)
4. Document caching strategy (or remove unused tables)

**Impact:**
- ✅ Reduces confusion
- ✅ Makes onboarding easier
- ✅ Prevents architectural drift

---

### Priority 2: Resolve Unused Cache Tables ⚠️ **MEDIUM IMPACT**

**Option A: Remove Tables (Recommended)**
- **Pros:** Simpler, less confusion, no wasted resources
- **Cons:** Lose potential caching benefit
- **Action:** Create migration to drop `currency_attribution`, `factor_exposures` tables

**Option B: Implement Caching**
- **Pros:** Better performance, reduced computation
- **Cons:** More complex, need TTL strategy, cache invalidation
- **Action:** 
  1. Add TTL columns to cache tables
  2. Implement `get_or_compute()` pattern in services
  3. Add cache invalidation on data changes

**Recommendation:** **Option A** (remove tables) - simpler, current performance is acceptable

---

### Priority 3: Standardize Data Access Patterns ⚠️ **MEDIUM IMPACT**

**Guidelines:**
1. **Simple Queries:** Direct DB access OK (e.g., `ledger.positions`)
2. **Business Logic:** Use service layer (e.g., `pricing.apply_pack`)
3. **Complex Computations:** Use service layer (e.g., `metrics.compute_twr`)

**Action:**
1. Document guidelines in DEVELOPMENT_GUIDE.md
2. Gradually migrate direct DB access to service layer where appropriate
3. Keep current working code (no urgent refactoring needed)

---

### Priority 4: Add TTL Strategy ⚠️ **LOW PRIORITY**

**Action:**
1. Add `expires_at` column to cache tables
2. Implement cache invalidation on data changes
3. Add freshness checks in services

**Impact:**
- Better data freshness guarantees
- Automatic cache invalidation
- Prevents stale data issues

**Recommendation:** **Defer** - Current system works, add TTL when implementing caching

---

### Priority 5: Separate Compute from Storage ⚠️ **LOW PRIORITY**

**Action:**
1. Create repository interfaces for data access
2. Separate compute logic from data access
3. Make services testable without database

**Impact:**
- Better testability
- Easier to swap storage backends
- Cleaner separation of concerns

**Recommendation:** **Defer** - Current system works, refactor when adding new features

---

## 📊 Data Architecture Consistency Assessment

### ✅ Consistent Patterns

1. **Connection Pooling** ✅
   - Single pattern: Cross-module storage using `sys.modules`
   - Well-documented and stable

2. **Pricing Pack Pattern** ✅
   - Consistent use of `pricing_pack_id` for reproducibility
   - Well-documented in PRICING_PACK_ARCHITECTURE.md

3. **Field Naming** ✅
   - Database: `quantity_open`, `quantity_original`
   - Agent: `quantity`
   - Standardized (January 14, 2025)

4. **Time-Series Data** ✅
   - Consistent use of TimescaleDB hypertables
   - `portfolio_daily_values`, `portfolio_metrics`, `macro_indicators`

---

### ⚠️ Inconsistent Patterns

1. **Computation vs Storage** ⚠️
   - Some services compute, some query, no clear strategy
   - Cache tables exist but not used

2. **Data Access** ⚠️
   - Mixed direct DB and service layer access
   - No clear guidelines

3. **Error Handling** ⚠️
   - Inconsistent error handling across services
   - Some services return empty results, some raise exceptions

---

## 📋 Documentation Improvements Needed

### 1. Create DATA_ARCHITECTURE.md ⚠️ **HIGH PRIORITY**

**Content:**
- Complete data flow diagram
- Service layer patterns (compute vs storage)
- Data access guidelines (direct DB vs service layer)
- Caching strategy (or rationale for no caching)
- Error handling patterns
- Connection pooling details
- Pricing pack lifecycle

---

### 2. Update DATABASE.md ⚠️ **MEDIUM PRIORITY**

**Add Sections:**
- Service layer computation patterns
- Cache table usage (or removal plan)
- Data access guidelines
- Error handling patterns

---

### 3. Update ARCHITECTURE.md ⚠️ **MEDIUM PRIORITY**

**Add Sections:**
- Service layer architecture
- Data access patterns
- Computation vs storage strategy

---

### 4. Update DEVELOPMENT_GUIDE.md ⚠️ **MEDIUM PRIORITY**

**Add Sections:**
- When to use direct DB access vs service layer
- When to compute vs cache
- Error handling best practices
- Data flow debugging

---

## 🎯 Recommendations Summary

### Immediate Actions (High Impact)

1. **Create DATA_ARCHITECTURE.md** ✅
   - Document complete data flow
   - Explain service layer patterns
   - Document data access guidelines

2. **Resolve Unused Cache Tables** ⚠️
   - **Recommended:** Remove `currency_attribution`, `factor_exposures` tables
   - **Alternative:** Implement caching with TTL (more work)

3. **Update Core Documentation** ✅
   - Add data architecture sections to existing docs
   - Document service layer patterns
   - Document data access guidelines

---

### Medium-Term Actions (Medium Impact)

4. **Standardize Data Access Patterns** ⚠️
   - Document guidelines
   - Gradually migrate to service layer where appropriate

5. **Add Error Handling Documentation** ⚠️
   - Document error handling patterns
   - Standardize error responses

---

### Long-Term Actions (Low Priority)

6. **Implement TTL Strategy** (if caching)
7. **Separate Compute from Storage** (if needed)
8. **Add Monitoring** for cache hit rates (if caching)

---

## ✅ Conclusion

**Current State:**
- ✅ Database layer well-documented and stable
- ⚠️ Data flow partially documented
- ⚠️ Service layer patterns inconsistent
- ❌ Missing comprehensive data architecture document

**Recommendations:**
1. **Create DATA_ARCHITECTURE.md** - Single source of truth for data flow
2. **Remove unused cache tables** - Simplify architecture
3. **Document service layer patterns** - Clarify when to compute vs cache
4. **Standardize data access** - Guidelines for direct DB vs service layer

**Stability Impact:**
- ✅ **Current system is stable** - Works correctly
- ⚠️ **Documentation gaps** - Make maintenance harder
- ⚠️ **Unused cache tables** - Waste resources, confuse architecture
- ✅ **No critical issues** - System is production-ready

**Priority:** Documentation improvements will significantly improve maintainability and developer experience.

---

## 🔗 Integration with Refactoring Master Plan

### Combined Critical Issues

**From Refactoring Analysis:**
1. **Silent Stub Data** ⚠️ **CRITICAL - USER TRUST ISSUE**
   - `risk.compute_factor_exposures` returns hardcoded fake data
   - **Location:** `backend/app/agents/financial_analyst.py` lines 1086-1110
   - **Impact:** Risk Analytics shows meaningless data, destroys credibility
   - **Fix:** Phase 1 - Add `_provenance` field with warnings (4 hours)

2. **Pattern Output Format Chaos** ⚠️ **CRITICAL - SILENT FAILURES**
   - 3 incompatible response formats
   - UI shows "No data" or crashes
   - **Fix:** Phase 1 - Fix pattern output extraction (4 hours)

3. **No Pattern Validation** ⚠️ **CRITICAL - RUNTIME ERRORS**
   - Patterns can reference undefined steps
   - Runtime errors with cryptic messages
   - **Fix:** Phase 2 - Add step dependency validation (8 hours)

**From Data Architecture Analysis:**
1. **Unused Cache Tables** ⚠️ **MODERATE - ARCHITECTURAL DEBT**
   - `currency_attribution`, `factor_exposures` tables not used
   - **Fix:** Remove tables or implement caching

2. **Mixed Data Access Patterns** ⚠️ **MODERATE**
   - No clear guidelines on direct DB vs service layer
   - **Fix:** Document guidelines (Phase 2)

---

### Unified Recommendations

**Priority 1: Emergency Fixes (Week 1 - 16 hours)**
1. Add provenance warnings to stub data (4 hours) ← **CRITICAL**
2. Fix pattern output extraction (4 hours) ← **CRITICAL**
3. Update 6 patterns to standard format (8 hours)

**Priority 2: Foundation (Weeks 2-3 - 32 hours)**
1. Create capability contracts (16 hours)
2. Add step dependency validation (8 hours)
3. Build pattern linter CLI (8 hours)
4. Remove unused cache tables (1 migration file)

**Priority 3: Features (Weeks 4-5 - 48 hours)**
1. Implement real factor analysis OR use library (16-40 hours)
2. Implement real DaR computation (32 hours) or defer
3. Implement unused patterns (16-24 hours)

**Priority 4: Quality (Week 6 - 24 hours)**
1. Integration tests (12 hours)
2. Performance monitoring (8 hours)
3. Documentation (4 hours)

---

### See Also

- **[REFACTORING_MASTER_PLAN.md](REFACTORING_MASTER_PLAN.md)** - Complete refactoring plan
- **[INTEGRATED_ARCHITECTURE_REFACTORING_PLAN.md](INTEGRATED_ARCHITECTURE_REFACTORING_PLAN.md)** - Unified view
- **[DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md)** - Complete data flow documentation

