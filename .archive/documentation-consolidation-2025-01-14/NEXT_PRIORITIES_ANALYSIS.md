# Next Priorities Analysis

**Date:** January 14, 2025  
**Status:** 📋 **PRIORITIZED**  
**Purpose:** Determine next high-priority issues to address from the critical issues and anti-patterns list

---

## Executive Summary

**Completed Issues:** 6/47  
**Remaining Critical/High Priority:** 6 issues  
**Next Recommended Actions:** 3 high-impact tasks

---

## ✅ Completed Issues

1. ✅ **Missing Tax Capabilities** - Tax patterns archived
2. ✅ **Missing `metrics.compute`** - Removed from capabilities list
3. ✅ **Missing Capability Decorations** - Added `@capability` decorators to 4 methods
4. ✅ **Silent Stub Data** - `risk.compute_factor_exposures` already has `_provenance` field
5. ✅ **UI Data Structure Mismatches** - Chart components improved to handle nested structures
6. ✅ **Pattern Output Format Chaos** - Orchestrator handles all formats, standards documented

---

## 🔴 Remaining Critical/High Priority Issues

### Issue 9: Direct Service Imports in Agents (ANTI-PATTERN) ⚠️

**Status:** 🔴 **ACTIVE** - Still using singleton getters

**Current State:**
- `financial_analyst.py` imports and uses:
  - `get_pricing_service()` - 1 usage
  - `get_optimizer_service()` - 4 usages
  - `get_ratings_service()` - 5 usages
- `macro_hound.py` imports and uses:
  - `get_macro_service()` - 3 usages
  - `get_scenario_service()` - 2 usages

**Impact:**
- Creates duplicate service instances (memory waste)
- Bypasses dependency injection
- Makes testing harder
- Creates circular dependencies

**Fix:** Update agents to use dependency injection instead of singleton getters.

**Files:**
- `backend/app/agents/financial_analyst.py`
- `backend/app/agents/macro_hound.py`

**Estimated Time:** 2-3 hours

---

### Issue 10: Multiple Database Connection Patterns (INCONSISTENCY) 🔄

**Status:** 🔴 **ACTIVE** - 5 different patterns in use

**Patterns Found:**
1. **Get Pool:** `get_db_pool()` → `pool.acquire()`
2. **Get Connection:** `get_db()` → `async with get_db()`
3. **Direct asyncpg:** `asyncpg.connect()` → `conn.fetch()`
4. **Service-Level Pool:** Service creates own pool
5. **Agent-Level Connection:** `get_db_connection_with_rls(ctx.user_id)`

**Impact:**
- Connection pool exhaustion
- Transaction boundary confusion
- Row-Level Security (RLS) only in Pattern 5
- Testing different for each pattern

**Fix:** Standardize on Pattern 5 (RLS-aware) or document which pattern to use when.

**Files:** All `backend/app/services/*.py` and `backend/app/agents/*.py`

**Estimated Time:** 4-6 hours

---

### Issue 11: Duplicate Services (ANTI-PATTERN) ⚠️

**Status:** 🔴 **ACTIVE** - Services consolidated into agents but still exist

**Services to Delete:**
- `backend/app/services/optimizer.py` (OptimizerService) → Moved to FinancialAnalyst ✅
- `backend/app/services/ratings.py` (RatingsService) → Moved to FinancialAnalyst ✅
- `backend/app/services/charts.py` (ChartsService) → Moved to FinancialAnalyst ✅
- `backend/app/services/alerts.py` (AlertService) → Moved to MacroHound ✅
- `backend/app/services/reports.py` (ReportService) → Moved to DataHarvester ✅

**Impact:**
- Agents call service methods, service methods might call agent capabilities (circular!)
- Unclear which layer does what
- Business logic split between agents and services

**Fix:** Mark as deprecated, then delete after migration.

**Files:**
- `backend/app/services/optimizer.py`
- `backend/app/services/ratings.py`
- `backend/app/services/charts.py`
- `backend/app/services/alerts.py`
- `backend/app/services/reports.py`

**Estimated Time:** 2-3 hours

---

### Issue 12: Overlapping Services (INCONSISTENCY) 🔄

**Status:** 🔴 **ACTIVE** - Multiple services doing the same thing

**Duplicates Found:**
1. **Scenario Services (2 implementations):**
   - `ScenarioService` (backend/app/services/scenarios.py)
   - `MacroAwareScenarioService` (backend/app/services/macro_scenario.py)
   - **Which to use?** Patterns use `macro.run_scenario` capability

2. **Alert Services (2 implementations):**
   - `AlertService` (backend/app/services/alerts.py)
   - `AlertDeliveryService` (backend/app/services/alert_delivery.py)
   - **Which to use?** Both imported in different places

**Impact:**
- Code duplication
- Business logic split between services
- Hard to find "source of truth"
- Testing nightmare (which service to mock?)

**Fix:** Consolidate or document which to use.

**Files:**
- `backend/app/services/scenarios.py`
- `backend/app/services/macro_scenario.py`
- `backend/app/services/alerts.py`
- `backend/app/services/alert_delivery.py`

**Estimated Time:** 3-4 hours

---

### Issue 14: Import Spaghetti (ANTI-PATTERN) 🍝

**Status:** 🔴 **ACTIVE** - Circular dependencies and excessive imports

**Location:** `backend/app/agents/financial_analyst.py` (60+ imports)

**Problem:**
```
financial_analyst.py
  → imports OptimizerService
    → imports PortfolioService
      → imports PerformanceCalculator
        → imports financial_analyst capabilities (circular!)
```

**Impact:**
- Import order matters (fragile)
- Circular import errors possible
- Hard to understand dependencies
- Can't extract modules independently

**Fix:** Refactor to break circular dependencies.

**File:** `backend/app/agents/financial_analyst.py`

**Estimated Time:** 4-6 hours

---

### Issue 18: Inconsistent Error Handling (MEDIUM) ⚠️

**Status:** 🔴 **ACTIVE** - Different error handling patterns across codebase

**Patterns Found:**
- Some use `try/except Exception` (too broad)
- Some use specific exceptions (`ValueError`, `KeyError`)
- Some return error responses, some raise exceptions
- Some log errors, some don't

**Impact:**
- Inconsistent UX
- Hard to debug
- Some errors silently fail

**Fix:** Standardize error handling patterns.

**Files:** All `backend/app/**/*.py`

**Estimated Time:** 4-6 hours

---

## 🎯 Recommended Next Steps (Priority Order)

### Priority 1: Issue 9 - Direct Service Imports in Agents (2-3 hours)

**Why First:**
- High impact, low risk
- Improves testability and maintainability
- Reduces memory waste from duplicate instances
- Aligns with dependency injection pattern

**Action:**
- Update `financial_analyst.py` to use dependency injection for services
- Update `macro_hound.py` to use dependency injection for services
- Remove singleton getter imports

---

### Priority 2: Issue 11 - Duplicate Services (2-3 hours)

**Why Second:**
- Removes confusion about which layer does what
- Prevents circular dependencies
- Cleaner architecture
- Low risk (services already consolidated into agents)

**Action:**
- Add deprecation warnings to duplicate services
- Verify no external dependencies
- Mark for deletion in next release

---

### Priority 3: Issue 12 - Overlapping Services (3-4 hours)

**Why Third:**
- Consolidates duplicate functionality
- Clarifies "source of truth"
- Improves maintainability
- Medium risk (need to verify which service is actually used)

**Action:**
- Analyze which service is actually used
- Document or consolidate
- Update all references

---

## 📊 Summary

**High Priority Remaining:**
- Issue 9: Direct Service Imports (2-3 hours) ⭐ **RECOMMENDED NEXT**
- Issue 11: Duplicate Services (2-3 hours) ⭐ **RECOMMENDED NEXT**
- Issue 12: Overlapping Services (3-4 hours) ⭐ **RECOMMENDED NEXT**
- Issue 10: Multiple DB Connection Patterns (4-6 hours)
- Issue 14: Import Spaghetti (4-6 hours)
- Issue 18: Inconsistent Error Handling (4-6 hours)

**Total Estimated Time:** 19-28 hours for all high-priority issues

---

## 🚀 Immediate Next Action

**Recommended:** Start with **Issue 9 - Direct Service Imports in Agents**

**Reasoning:**
1. ✅ High impact, low risk
2. ✅ Quick win (2-3 hours)
3. ✅ Improves code quality immediately
4. ✅ Sets foundation for other fixes
5. ✅ No breaking changes

**Files to Update:**
- `backend/app/agents/financial_analyst.py` - Replace singleton getters with dependency injection
- `backend/app/agents/macro_hound.py` - Replace singleton getters with dependency injection

