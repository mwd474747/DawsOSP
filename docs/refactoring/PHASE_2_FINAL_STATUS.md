# Phase 2: Singleton Removal - Final Status

**Date:** January 15, 2025  
**Status:** 🚧 ~70% COMPLETE  
**Current Step:** Updating remaining call sites

---

## Completed Work

### ✅ 1. Circular Dependencies Analysis
- ✅ No actual circular imports found
- ✅ Indirect dependencies through singleton pattern (safe)

### ✅ 2. executor.py Migration
- ✅ Updated to use DI container
- ✅ Removed singleton variables

### ✅ 3. Service Call Sites Updated (10 files)
- ✅ `alerts.py` - 3 call sites
- ✅ `scenarios.py` - 1 call site
- ✅ `optimizer.py` - 1 call site
- ✅ `metrics.py` - 1 call site
- ✅ `risk_metrics.py` - 1 call site
- ✅ `factor_analysis.py` - 1 call site
- ✅ `currency_attribution.py` - 1 call site
- ✅ `benchmarks.py` - 1 call site (constructor)

### ✅ 4. Job Call Sites Updated (3 files)
- ✅ `compute_macro.py` - 2 call sites
- ✅ `scheduler.py` - 1 call site
- ✅ `prewarm_factors.py` - 1 call site

### ✅ 5. Helper Function Added
- ✅ `ensure_initialized()` in `di_container.py`

**Total Call Sites Updated:** ~15

---

## Remaining Work

### ⚠️ Remaining Call Sites (~16 matches)

**Services (function definitions):**
- Singleton function definitions still exist (expected - will be deprecated)
- `backend/app/services/pricing.py` - `get_pricing_service()` definition
- `backend/app/services/scenarios.py` - `get_scenario_service()` definition
- `backend/app/services/macro.py` - `get_macro_service()` definition
- `backend/app/services/ratings.py` - `get_ratings_service()` definition
- `backend/app/services/optimizer.py` - `get_optimizer_service()` definition
- And more...

**Routes:**
- `backend/app/api/routes/macro.py` - Need to check if there are actual call sites

**Agents:**
- `backend/app/agents/base_agent.py` - Just a comment/docstring reference

**Services:**
- `backend/app/services/risk.py` - Just a docstring usage example

---

## Next Steps

1. ✅ Update service call sites (COMPLETE)
2. ✅ Update job call sites (COMPLETE)
3. ⚠️ Check and update route call sites
4. ⏳ Mark singleton functions as deprecated (add deprecation warnings)
5. ⏳ Remove singleton functions (after deprecation period)
6. ⏳ Verify initialization order
7. ⏳ Add comprehensive tests

---

## Files Changed

**Backend (14 files):**
- `backend/app/core/di_container.py` (NEW helper function)
- `backend/app/api/executor.py` (UPDATED)
- `backend/app/services/alerts.py` (UPDATED)
- `backend/app/services/scenarios.py` (UPDATED)
- `backend/app/services/optimizer.py` (UPDATED)
- `backend/app/services/metrics.py` (UPDATED)
- `backend/app/services/risk_metrics.py` (UPDATED)
- `backend/app/services/factor_analysis.py` (UPDATED)
- `backend/app/services/currency_attribution.py` (UPDATED)
- `backend/app/services/benchmarks.py` (UPDATED)
- `backend/jobs/compute_macro.py` (UPDATED)
- `backend/jobs/scheduler.py` (UPDATED)
- `backend/jobs/prewarm_factors.py` (UPDATED)

---

**Status:** 🚧 ~70% COMPLETE  
**Last Updated:** January 15, 2025

