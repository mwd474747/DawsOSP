# Patterns and Metrics Functions Gaps Analysis

**Date:** November 3, 2025  
**Purpose:** Analyze missing patterns and functions required for application functionality  
**Status:** 📋 PLANNING ONLY (No Code Changes)

---

## 📊 Executive Summary

After comprehensive analysis of patterns, metrics functions, UI expectations, and codebase history, I've identified **critical gaps** between what's implemented, what's required, and what the UI expects. The system has **multiple implementations** of metrics computation, but there are **disconnects** between:

1. **Pattern JSON references** vs **capability return structures**
2. **UI expectations** vs **actual pattern outputs**
3. **Multiple competing implementations** of the same functionality
4. **Missing agent capabilities** for metrics computation

**Key Finding:** The `portfolio_overview` pattern references metrics that don't match the capability return structure, creating a **critical functional gap**.

---

## 🔍 Pattern Analysis

### 1. Existing Patterns (12 Total)

**Pattern Files:**
1. ✅ `portfolio_overview.json` - Portfolio dashboard
2. ✅ `portfolio_scenario_analysis.json` - Stress testing
3. ✅ `portfolio_cycle_risk.json` - Cycle risk analysis
4. ✅ `portfolio_macro_overview.json` - Macro overview
5. ✅ `macro_trend_monitor.json` - Macro trends
6. ✅ `macro_cycles_overview.json` - Cycle overview
7. ✅ `news_impact_analysis.json` - News impact
8. ✅ `cycle_deleveraging_scenarios.json` - Deleveraging scenarios
9. ✅ `buffett_checklist.json` - Quality ratings
10. ✅ `holding_deep_dive.json` - Position analysis
11. ✅ `policy_rebalance.json` - Rebalancing
12. ✅ `export_portfolio_report.json` - Report export

**Status:** ✅ All 12 patterns exist

---

## ⚠️ Critical Gap: portfolio_overview Pattern

### Pattern JSON References (What Pattern Expects)

**From `portfolio_overview.json` lines 113-143:**
```json
"presentation": {
  "performance_strip": {
    "metrics": [
      {
        "label": "TWR (1Y)",
        "value": "{{twr.total_return}}",  ← References "twr"
        "format": "percentage"
      },
      {
        "label": "Volatility",
        "value": "{{twr.volatility}}",  ← References "twr.volatility"
        "format": "percentage"
      },
      {
        "label": "Sharpe Ratio",
        "value": "{{twr.sharpe}}",  ← References "twr.sharpe"
        "format": "decimal_2"
      },
      {
        "label": "Max Drawdown",
        "value": "{{twr.max_drawdown}}",  ← References "twr.max_drawdown"
        "format": "percentage"
      }
    ]
  }
}
```

**Problem:** Pattern references `{{twr.total_return}}`, `{{twr.volatility}}`, `{{twr.sharpe}}`, `{{twr.max_drawdown}}`

---

### Pattern Steps (What Pattern Executes)

**From `portfolio_overview.json` lines 63-111:**
```json
"steps": [
  {
    "capability": "ledger.positions",
    "as": "positions"
  },
  {
    "capability": "pricing.apply_pack",
    "as": "valued_positions"
  },
  {
    "capability": "metrics.compute_twr",  ← Executes this capability
    "as": "perf_metrics"  ← Stores result as "perf_metrics"
  },
  {
    "capability": "attribution.currency",
    "as": "currency_attr"
  },
  {
    "capability": "portfolio.sector_allocation",
    "as": "sector_allocation"
  },
  {
    "capability": "portfolio.historical_nav",
    "as": "historical_nav"
  }
]
```

**Problem:** Capability result is stored as `perf_metrics`, but pattern presentation references `{{twr.*}}`

**Gap:** Pattern references `twr` but capability result is stored as `perf_metrics`

---

### UI Expectations (What Frontend Expects)

**From `full_ui.html` lines 2844-2851:**
```javascript
dataPath: 'perf_metrics',  ← UI expects "perf_metrics"
config: {
  columns: 4,
  metrics: [
    { key: 'twr_ytd', label: 'YTD Return', format: 'percentage' },
    { key: 'volatility', label: 'Volatility', format: 'percentage' },
    { key: 'sharpe', label: 'Sharpe Ratio', format: 'number' },
    { key: 'max_drawdown', label: 'Max Drawdown', format: 'percentage' }
  ]
}
```

**Expectation:** UI expects `perf_metrics.twr_ytd`, `perf_metrics.volatility`, `perf_metrics.sharpe`, `perf_metrics.max_drawdown`

---

### Capability Implementation (What It Actually Returns)

**From `backend/app/services/metrics.py` lines 173-181:**
```python
async def compute_twr(...) -> Dict:
    return {
        "twr": round(twr, 6),           ← Returns "twr" (not "twr_ytd")
        "ann_twr": round(ann_twr, 6),   ← Returns "ann_twr"
        "vol": round(vol, 6),          ← Returns "vol" (not "volatility")
        "sharpe": round(sharpe, 4),    ← Returns "sharpe" ✅
        "sortino": round(sortino, 4),  ← Returns "sortino"
        "days": days,
        "data_points": len(values),
    }
```

**Reality:** Capability returns `{"twr": ..., "vol": ..., "sharpe": ...}` but:
- UI expects `twr_ytd` (not `twr`)
- UI expects `volatility` (not `vol`)
- Pattern JSON references `{{twr.total_return}}` (not `{{perf_metrics.twr}}`)
- Pattern JSON references `{{twr.volatility}}` (not `{{perf_metrics.vol}}`)

**Gap:** Mismatch between capability return structure, pattern references, and UI expectations

---

## 🔴 Critical Gaps Identified

### Gap 1: Pattern Reference Mismatch (CRITICAL)

**Issue:** Pattern JSON references `{{twr.total_return}}` but:
1. Capability result stored as `perf_metrics` (not `twr`)
2. Capability returns `{"twr": ...}` (not `{"total_return": ...}`)

**Impact:** Pattern presentation will fail to resolve template variables

**Fix Required:**
- Option A: Change pattern JSON to reference `{{perf_metrics.twr}}` (not `{{twr.total_return}}`)
- Option B: Change capability to return `{"total_return": ..., "volatility": ...}` and store as `twr`

---

### Gap 2: Capability Return Structure Mismatch (HIGH)

**Issue:** Capability returns `{"twr": ..., "vol": ...}` but UI expects `{"twr_ytd": ..., "volatility": ...}`

**Impact:** UI metrics grid will fail to display values

**Fix Required:**
- Option A: Change capability to return `{"twr_ytd": ..., "volatility": ..., "sharpe": ..., "max_drawdown": ...}`
- Option B: Change UI to expect `{"twr": ..., "vol": ...}` and map fields

---

### Gap 3: Missing Max Drawdown in Capability Return (MEDIUM)

**Issue:** Capability returns `{"twr": ..., "vol": ..., "sharpe": ...}` but **doesn't return `max_drawdown`**

**Code Evidence:**
- `PerformanceCalculator.compute_twr()` returns: `twr`, `ann_twr`, `vol`, `sharpe`, `sortino`, `days`, `data_points`
- **Missing:** `max_drawdown`

**Impact:** UI expects `max_drawdown` but capability doesn't provide it

**Fix Required:** Add `max_drawdown` calculation to `compute_twr()` capability

---

### Gap 4: Multiple Competing Implementations (MEDIUM)

**Issue:** Multiple services compute metrics:
1. `backend/app/services/metrics.py` - `PerformanceCalculator.compute_twr()` (used by pattern)
2. `backend/jobs/metrics.py` - `MetricsComputer.compute_portfolio_metrics()` (comprehensive, stores in DB)
3. `backend/scripts/seed_portfolio_performance_data.py` - `PerformanceSeeder.calculate_metrics()` (for seeding)
4. `populate_portfolio_metrics_simple.py` - `populate_metrics()` (simple script)

**Problem:** Inconsistency between implementations

**Impact:** Different implementations may return different structures/values

**Fix Required:** Consolidate implementations or document which is authoritative

---

### Gap 5: Missing Agent Capability Registration (MEDIUM)

**Issue:** Pattern references `metrics.compute_twr` capability, but need to verify it's registered

**Code Evidence:**
- Pattern references: `"capability": "metrics.compute_twr"`
- Need to verify: Which agent registers this capability?

**Search Results:**
- `pattern_orchestrator.py:865` references `"capability": "metrics.compute_twr"`
- Need to find: Agent registration code

**Impact:** If capability not registered, pattern execution will fail

---

## 🔍 Metrics Computation History & Intention

### Intended Design

**From `backend/jobs/metrics.py` header (lines 1-35):**
```
Purpose: Compute daily portfolio metrics (TWR, MWR, vol, Sharpe, alpha, beta)
Updated: 2025-10-22
Priority: P0 (Phase 3 Task 3 - Wire Metrics to Database)

Metrics Computed:
    - TWR (Time-Weighted Return) - eliminates cash flow impact
    - MWR (Money-Weighted Return / IRR) - includes cash flow impact
    - Volatility (rolling 30/60/90 day)
    - Sharpe Ratio (vs risk-free rate)
    - Alpha (excess return vs benchmark)
    - Beta (systematic risk vs benchmark)
    - Max Drawdown
    - Win Rate
    - Currency Attribution (local + FX + interaction)
```

**Intention:** Comprehensive metrics computation with database storage

---

### Actual Implementation

**From `backend/app/services/metrics.py` header (lines 1-24):**
```
Purpose: Calculate TWR, MWR, Sharpe, Max Drawdown with ±1bp reconciliation guarantee
Updated: 2025-10-21
Priority: P0 (Critical for portfolio analytics)

Features:
    - Time-Weighted Return (TWR) with geometric linking
    - Money-Weighted Return (MWR) via IRR calculation
    - Sharpe ratio and Sortino ratio
    - Maximum drawdown with recovery tracking
    - Beta to benchmark (hedged/unhedged)
    - Rolling volatility (30/90/252 day windows)
```

**Reality:** Service exists but `compute_twr()` doesn't return `max_drawdown` despite header claiming it does

---

## 📊 Database Schema vs Capability Return

### Database Schema (What Can Be Stored)

**From `backend/db/schema/portfolio_metrics.sql` lines 15-57:**
```sql
CREATE TABLE portfolio_metrics (
    -- Returns
    twr_1d NUMERIC(12, 8),
    twr_mtd NUMERIC(12, 8),
    twr_qtd NUMERIC(12, 8),
    twr_ytd NUMERIC(12, 8),  ← Database has twr_ytd
    twr_1y NUMERIC(12, 8),
    
    -- Volatility
    volatility_30d NUMERIC(12, 8),  ← Database has volatility_30d
    volatility_60d NUMERIC(12, 8),
    volatility_90d NUMERIC(12, 8),
    volatility_1y NUMERIC(12, 8),
    
    -- Sharpe Ratio
    sharpe_30d NUMERIC(12, 8),  ← Database has sharpe_30d
    sharpe_60d NUMERIC(12, 8),
    sharpe_90d NUMERIC(12, 8),
    sharpe_1y NUMERIC(12, 8),
    
    -- Drawdown
    max_drawdown_1y NUMERIC(12, 8),  ← Database has max_drawdown_1y
    max_drawdown_3y NUMERIC(12, 8),
    current_drawdown NUMERIC(12, 8),
    
    ...
);
```

**Database Fields:** `twr_ytd`, `volatility_*`, `sharpe_*`, `max_drawdown_*`

**Capability Returns:** `twr`, `vol`, `sharpe` (missing `max_drawdown`, field names don't match)

**Gap:** Database schema and capability return structure don't align

---

## 🎯 UI Expectations vs Pattern Outputs

### UI Expected Structure

**From `full_ui.html` lines 2844-2851:**
```javascript
dataPath: 'perf_metrics',  ← UI expects "perf_metrics"
metrics: [
  { key: 'twr_ytd', ... },      ← UI expects twr_ytd
  { key: 'volatility', ... },   ← UI expects volatility
  { key: 'sharpe', ... },       ← UI expects sharpe ✅
  { key: 'max_drawdown', ... }  ← UI expects max_drawdown
]
```

**Expected:** `perf_metrics.twr_ytd`, `perf_metrics.volatility`, `perf_metrics.sharpe`, `perf_metrics.max_drawdown`

---

### Pattern Output Structure (Actual)

**Pattern stores capability result as `perf_metrics`:**
```json
{
  "perf_metrics": {
    "twr": 0.123,        ← Actual: "twr" (not "twr_ytd")
    "ann_twr": 0.156,
    "vol": 0.182,       ← Actual: "vol" (not "volatility")
    "sharpe": 1.23,     ← Actual: "sharpe" ✅
    "sortino": 1.45,
    "days": 252,
    "data_points": 252
    // Missing: max_drawdown
  }
}
```

**Gap:** Field names don't match, missing `max_drawdown`

---

## ✅ Functions That Exist (Implemented)

### 1. PerformanceCalculator.compute_twr() ✅

**Location:** `backend/app/services/metrics.py:53-181`

**Returns:**
```python
{
    "twr": float,           # Total return
    "ann_twr": float,       # Annualized return
    "vol": float,           # Volatility
    "sharpe": float,        # Sharpe ratio
    "sortino": float,       # Sortino ratio
    "days": int,            # Days in period
    "data_points": int      # Number of data points
}
```

**Used By:** Pattern `portfolio_overview.json` via `metrics.compute_twr` capability

**Status:** ✅ Implemented but field names don't match UI expectations

---

### 2. MetricsComputer.compute_portfolio_metrics() ✅

**Location:** `backend/jobs/metrics.py:185-249`

**Returns:** `PortfolioMetrics` dataclass with comprehensive metrics

**Used By:** Background job for database storage

**Status:** ✅ Implemented but not used by patterns

---

### 3. PerformanceSeeder.calculate_metrics() ✅

**Location:** `backend/scripts/seed_portfolio_performance_data.py:158-243`

**Returns:** DataFrame with metrics for seeding

**Used By:** Data seeding scripts

**Status:** ✅ Implemented for seeding only

---

## ❌ Functions That Are Missing or Incomplete

### 1. Max Drawdown in compute_twr() ❌

**Issue:** `PerformanceCalculator.compute_twr()` claims to calculate `max_drawdown` in header but doesn't return it

**Code Evidence:**
- Header says: "Maximum drawdown with recovery tracking"
- Return structure: `{"twr": ..., "vol": ..., "sharpe": ...}` (no `max_drawdown`)

**Fix Required:** Add `max_drawdown` calculation and return it

---

### 2. Field Name Mapping Function ❌

**Issue:** No function to map capability return structure to UI expected structure

**Gap:**
- Capability returns: `{"twr": ..., "vol": ...}`
- UI expects: `{"twr_ytd": ..., "volatility": ...}`

**Fix Required:** Add mapping function or change capability return structure

---

### 3. Agent Capability Registration ❌

**Issue:** Need to verify `metrics.compute_twr` capability is registered

**Search Results:**
- Pattern references: `"capability": "metrics.compute_twr"`
- Need to find: Where this capability is registered

**Fix Required:** Verify registration, register if missing

---

## 🔄 Pattern Template Reference Issues

### Issue: Pattern References vs Storage Keys

**Pattern JSON references:**
```json
"value": "{{twr.total_return}}"  ← References "twr" namespace
"value": "{{twr.volatility}}"    ← References "twr" namespace
```

**Pattern storage:**
```json
{
  "capability": "metrics.compute_twr",
  "as": "perf_metrics"  ← Stored as "perf_metrics" (not "twr")
}
```

**Gap:** Pattern references `{{twr.*}}` but result stored as `perf_metrics`

**Impact:** Template resolution will fail

---

## 📋 Summary of Gaps

### Critical Gaps (Must Fix)

1. ❌ **Pattern Reference Mismatch** - Pattern references `{{twr.*}}` but result stored as `perf_metrics`
2. ❌ **Field Name Mismatch** - Capability returns `twr`, `vol` but UI expects `twr_ytd`, `volatility`
3. ❌ **Missing Max Drawdown** - UI expects `max_drawdown` but capability doesn't return it

### High Priority Gaps

4. ⚠️ **Multiple Implementations** - 4 different implementations of metrics computation
5. ⚠️ **Capability Registration** - Need to verify `metrics.compute_twr` is registered

### Medium Priority Gaps

6. ⚠️ **Database Schema Alignment** - Database has `twr_ytd`, `volatility_*` but capability returns `twr`, `vol`
7. ⚠️ **Comprehensive Metrics** - `MetricsComputer` has comprehensive metrics but not used by patterns

---

## 🎯 Recommendations

### Priority 1: Fix Pattern References

**Action:** Update `portfolio_overview.json` to reference `{{perf_metrics.*}}` instead of `{{twr.*}}`

**Change:**
```json
"value": "{{perf_metrics.twr}}"  ← Instead of "{{twr.total_return}}"
"value": "{{perf_metrics.vol}}"  ← Instead of "{{twr.volatility}}"
```

---

### Priority 2: Align Capability Return Structure

**Action:** Update `PerformanceCalculator.compute_twr()` to return structure matching UI expectations

**Change:**
```python
return {
    "twr_ytd": round(twr, 6),           ← Instead of "twr"
    "volatility": round(vol, 6),        ← Instead of "vol"
    "sharpe": round(sharpe, 4),         ← Keep "sharpe" ✅
    "max_drawdown": round(max_dd, 6),   ← Add missing field
    ...
}
```

---

### Priority 3: Add Max Drawdown Calculation

**Action:** Implement `max_drawdown` calculation in `compute_twr()` capability

**Implementation:**
```python
# Calculate max drawdown
running_max = np.maximum.accumulate(nav_values)
drawdowns = (nav_values - running_max) / running_max
max_drawdown = float(np.min(drawdowns))
```

---

### Priority 4: Consolidate Implementations

**Action:** Choose one authoritative implementation or document which to use

**Recommendation:**
- Use `PerformanceCalculator.compute_twr()` for pattern execution (real-time)
- Use `MetricsComputer.compute_portfolio_metrics()` for database storage (batch)

---

## 📊 Pattern vs Function Alignment Matrix

| Component | Pattern Expects | Capability Returns | UI Expects | Database Schema | Status |
|-----------|----------------|-------------------|------------|----------------|--------|
| Namespace | `twr` | `perf_metrics` | `perf_metrics` ✅ | N/A | ❌ Mismatch |
| Total Return | `twr.total_return` | `twr` | `twr_ytd` | `twr_ytd` ✅ | ❌ Mismatch |
| Volatility | `twr.volatility` | `vol` | `volatility` | `volatility_*` ✅ | ❌ Mismatch |
| Sharpe | `twr.sharpe` | `sharpe` ✅ | `sharpe` ✅ | `sharpe_*` ✅ | ✅ Match |
| Max Drawdown | `twr.max_drawdown` | Missing ❌ | `max_drawdown` | `max_drawdown_*` ✅ | ❌ Missing |

**Overall Alignment:** 20% (1 of 5 components match)

---

## 🔍 Additional Findings

### Patterns Using Metrics

**Patterns that compute metrics:**
1. ✅ `portfolio_overview.json` - Uses `metrics.compute_twr`
2. ⚠️ Other patterns - Need to check if they use metrics

**Need to verify:** Do other patterns need metrics but don't have them?

---

### Metrics Required by UI

**UI components expecting metrics:**
1. ✅ `performance_strip` - Expects `perf_metrics` with `twr_ytd`, `volatility`, `sharpe`, `max_drawdown`
2. ⚠️ Other UI components - Need to check if they expect metrics

---

---

## 🔍 CRITICAL FINDING: Agent Implementation

### Actual Agent Return Structure

**From `backend/app/agents/financial_analyst.py:356-462`:**

The `metrics_compute_twr()` agent capability:
1. ✅ **Queries database** (`portfolio_metrics` table)
2. ✅ **Returns TWR fields**: `twr_1d`, `twr_mtd`, `twr_ytd`, `twr_1y`, `twr_3y`, `twr_5y`, `twr_itd`
3. ❌ **DOES NOT return**: `volatility`, `sharpe`, `max_drawdown`

**Actual Return:**
```python
{
    "twr_1d": float,
    "twr_mtd": float,
    "twr_ytd": float,      ← ✅ Matches UI expectation
    "twr_1y": float,
    "twr_3y": float,
    "twr_5y": float,
    "twr_itd": float,
    "portfolio_id": str,
    "asof_date": str,
    "pricing_pack_id": str,
    # Missing: volatility, sharpe, max_drawdown
}
```

**Database Has:**
```sql
-- portfolio_metrics table has:
- twr_ytd ✅
- volatility_30d, volatility_60d, volatility_90d, volatility_1y ✅
- sharpe_30d, sharpe_60d, sharpe_90d, sharpe_1y ✅
- max_drawdown_1y, max_drawdown_3y ✅
```

**Gap:** Agent queries database but **doesn't extract or return** volatility, sharpe, max_drawdown fields

**Fix Required:** Update `metrics_compute_twr()` to also return:
- `volatility` (from `volatility_1y`)
- `sharpe` (from `sharpe_1y`)
- `max_drawdown` (from `max_drawdown_1y`)

---

## 🔴 CRITICAL GAP: Pattern Reference vs Agent Return

### Pattern References (Lines 117-134):
```json
"value": "{{twr.total_return}}"      ← Pattern expects "twr" namespace
"value": "{{twr.volatility}}"       ← Pattern expects "twr.volatility"
"value": "{{twr.sharpe}}"            ← Pattern expects "twr.sharpe"
"value": "{{twr.max_drawdown}}"      ← Pattern expects "twr.max_drawdown"
```

### Pattern Storage (Line 86):
```json
{
  "capability": "metrics.compute_twr",
  "as": "perf_metrics"  ← Stored as "perf_metrics" (not "twr")
}
```

### Agent Returns:
```python
{
    "twr_ytd": float,     ← ✅ Has return (but as "twr_ytd", not "total_return")
    # Missing: volatility
    # Missing: sharpe
    # Missing: max_drawdown
}
```

**Triple Mismatch:**
1. ❌ Pattern references `{{twr.*}}` but stored as `perf_metrics`
2. ❌ Pattern references `{{twr.total_return}}` but agent returns `twr_ytd`
3. ❌ Pattern expects `volatility`, `sharpe`, `max_drawdown` but agent doesn't return them

---

## 📋 Updated Summary of Gaps

### Critical Gaps (Must Fix Immediately)

1. ❌ **Agent Missing Fields** - `metrics_compute_twr()` doesn't return `volatility`, `sharpe`, `max_drawdown` from database
2. ❌ **Pattern Reference Mismatch** - Pattern references `{{twr.*}}` but result stored as `perf_metrics`
3. ❌ **Field Name Mismatch** - Pattern references `{{twr.total_return}}` but agent returns `twr_ytd`

### High Priority Gaps

4. ⚠️ **Multiple Implementations** - 4 different implementations of metrics computation
5. ⚠️ **Service Not Used** - `PerformanceCalculator.compute_twr()` exists but agent uses database query instead

### Medium Priority Gaps

6. ⚠️ **Database Schema Alignment** - Database has all fields, but agent doesn't extract them all
7. ⚠️ **Comprehensive Metrics** - `MetricsComputer` has comprehensive metrics but not used by patterns

---

## ✅ Updated Recommendations

### Priority 1: Fix Agent Return Structure (CRITICAL)

**Action:** Update `FinancialAnalyst.metrics_compute_twr()` to return all required fields

**Change in `backend/app/agents/financial_analyst.py:428-440`:**
```python
result = {
    "portfolio_id": str(metrics["portfolio_id"]),
    "asof_date": str(metrics["asof_date"]),
    "pricing_pack_id": metrics["pricing_pack_id"],
    # TWR metrics
    "twr_ytd": float(metrics["twr_ytd"]) if metrics.get("twr_ytd") else None,
    "twr_1y": float(metrics["twr_1y"]) if metrics.get("twr_1y") else None,
    # ADD MISSING FIELDS:
    "volatility": float(metrics["volatility_1y"]) if metrics.get("volatility_1y") else None,
    "sharpe": float(metrics["sharpe_1y"]) if metrics.get("sharpe_1y") else None,
    "max_drawdown": float(metrics["max_drawdown_1y"]) if metrics.get("max_drawdown_1y") else None,
}
```

---

### Priority 2: Fix Pattern References (CRITICAL)

**Action:** Update `portfolio_overview.json` to reference correct structure

**Option A:** Change pattern to reference `{{perf_metrics.*}}`
```json
"value": "{{perf_metrics.twr_ytd}}"        ← Instead of "{{twr.total_return}}"
"value": "{{perf_metrics.volatility}}"    ← Instead of "{{twr.volatility}}"
"value": "{{perf_metrics.sharpe}}"         ← Instead of "{{twr.sharpe}}"
"value": "{{perf_metrics.max_drawdown}}"   ← Instead of "{{twr.max_drawdown}}"
```

**Option B:** Change pattern storage key to `twr` and return structure
```json
{
  "capability": "metrics.compute_twr",
  "as": "twr"  ← Store as "twr" instead of "perf_metrics"
}
```

And update agent to return:
```python
{
    "total_return": twr_ytd,  ← Instead of "twr_ytd"
    "volatility": ...,
    "sharpe": ...,
    "max_drawdown": ...
}
```

**Recommendation:** Option A (change pattern references) is safer and less disruptive

---

### Priority 3: Add Missing Fields to Agent (CRITICAL)

**Action:** Update agent to extract and return `volatility`, `sharpe`, `max_drawdown` from database

**Implementation:** Already shown in Priority 1

---

**Status:** Analysis complete. Critical gaps identified requiring fixes before application functionality works correctly.

