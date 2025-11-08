# Phase 2: Circular Dependencies Analysis

**Date:** January 15, 2025  
**Status:** 🚧 IN PROGRESS  
**Priority:** P0 (Critical - Must be done FIRST per V3 plan)

---

## Executive Summary

**V3 Plan Requirement:** Fix circular dependencies FIRST, then fix initialization order, then migrate to DI container.

**Analysis:** No direct circular imports found. Indirect circular dependencies exist through singleton pattern.

---

## Dependency Analysis

### Direct Imports Analysis

**Services → Services:**
- ✅ No circular imports found
- Services import from `app.core` (types, exceptions, constants)
- Services don't import other services directly

**Services → Agents:**
- ✅ No imports found
- Services don't import agents

**Agents → Services:**
- ✅ Unidirectional
- Agents import services (correct direction)

**Result:** ✅ **No direct circular dependencies**

---

## Indirect Circular Dependencies (Through Singletons)

### Problem: Singleton Pattern Creates Implicit Dependencies

**Example:**
```python
# In scenarios.py
from app.services.pricing import get_pricing_service

class ScenarioService:
    def some_method(self):
        pricing_service = get_pricing_service()  # Implicit dependency
```

**Issue:**
- `get_pricing_service()` creates singleton on first call
- If `ScenarioService` is created before `PricingService`, initialization order matters
- Creates implicit dependency chain

**Current State:**
- ✅ DI container already handles this correctly
- ✅ Service initializer registers services in dependency order
- ⚠️ But singleton functions still exist and are used

---

## Singleton Functions Found

**Files with singleton functions:**
1. `backend/app/services/pricing.py` - `get_pricing_service()`
2. `backend/app/services/ratings.py` - `get_ratings_service()`
3. `backend/app/services/optimizer.py` - `get_optimizer_service()`
4. `backend/app/services/scenarios.py` - `get_scenario_service()`
5. `backend/app/services/macro.py` - `get_macro_service()`
6. `backend/app/services/reports.py` - `get_reports_service()`
7. `backend/app/services/risk.py` - `get_risk_service()`
8. `backend/app/services/benchmarks.py` - `get_benchmark_service()`
9. `backend/app/services/fred_transformation.py` - `get_transformation_service()`
10. `backend/app/services/auth.py` - `get_auth_service()` (likely)
11. `backend/app/services/alerts.py` - `get_alert_service()` (likely)
12. `backend/app/services/cycles.py` - `get_cycles_service()` (likely)
13. `backend/app/services/audit.py` - `get_audit_service()` (likely)
14. `backend/app/services/notifications.py` - `get_notification_service()` (likely)

**Total:** ~14-18 singleton functions

---

## Circular Dependency Through Singletons

### Example Chain:

```
ScenarioService.__init__()
  → calls get_pricing_service()
    → creates PricingService singleton
      → PricingService might call get_scenario_service() (if needed)
        → creates ScenarioService singleton
          → CIRCULAR DEPENDENCY!
```

**However:**
- This is only a problem if services call each other's singleton functions
- Need to verify if this actually happens

---

## Verification: Do Services Call Each Other's Singletons?

**Analysis Needed:**
- Check if `ScenarioService` calls `get_pricing_service()`
- Check if `PricingService` calls `get_scenario_service()`
- Check if any service calls another service's singleton function

**Action:** Search for singleton function calls within services

---

## Solution: Remove Singleton Pattern

**Approach:**
1. ✅ DI container already exists and works
2. ✅ Service initializer already uses DI container
3. ⚠️ Need to remove singleton functions
4. ⚠️ Need to update all call sites to use DI container

**This eliminates:**
- Implicit dependencies
- Initialization order issues
- Circular dependency risk

---

## Next Steps

1. **Verify actual circular dependencies** (check if services call each other's singletons)
2. **Fix initialization order** (ensure DI container initializes in correct order)
3. **Update executor.py** (use DI container instead of singleton)
4. **Remove singleton functions** (replace with DI container)

---

**Status:** 🚧 IN PROGRESS  
**Next Step:** Verify if services actually call each other's singleton functions

