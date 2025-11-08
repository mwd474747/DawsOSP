# Anti-Pattern Analysis - Replit Changes

**Date:** January 15, 2025  
**Status:** 🔴 CRITICAL - Anti-pattern introduced  
**Priority:** P1 (Must fix immediately)

---

## Executive Summary

Replit changes introduced a **singleton factory function anti-pattern** that contradicts our Phase 2 refactoring work. This needs to be fixed immediately to maintain architectural consistency.

---

## Issues Identified

### 1. ❌ Anti-Pattern: Singleton Factory Function Reintroduced

**Location:** `backend/app/services/scenarios.py:993-995`

**Problem:**
```python
def get_scenario_service():
    """Factory function to return ScenarioService instance."""
    return ScenarioService()
```

**Why This Is Wrong:**
- We just removed all singleton factory functions as part of Phase 2 refactoring
- This reintroduces the exact pattern we're trying to eliminate
- Contradicts our DI container architecture
- Creates inconsistency with other services

**Root Cause:**
- Import failure: `from app.services.scenarios import get_scenario_service` failed because function didn't exist
- Cascade effect: Entire import block failed, setting `RequestCtx = None`
- Runtime error: `RequestCtx()` called on `None` object

**Proper Fix:**
- Remove `get_scenario_service()` function
- Use DI container: `container.resolve("scenarios")`
- Or use direct instantiation: `ScenarioService(db_pool=db_pool)`

---

## Root Cause Analysis

### Import Failure Chain

1. **Initial Problem:** `get_scenario_service()` didn't exist
2. **Import Failure:** `from app.services.scenarios import get_scenario_service` failed
3. **Cascade Effect:** Entire import block failed (line 108-109 in combined_server.py)
4. **Fallback:** `RequestCtx = None` was set (line 114)
5. **Runtime Error:** `RequestCtx()` called on `None` object

### Why This Happened

- Replit added a quick fix without understanding the architecture
- No awareness of Phase 2 singleton removal refactoring
- Import error handling was too broad (caught all imports)

---

## Proper Resolution

### Step 1: Remove Factory Function

**File:** `backend/app/services/scenarios.py`

**Remove:**
```python
# ============================================================================
# Singleton
# ============================================================================

# Factory function for combined_server.py
def get_scenario_service():
    """Factory function to return ScenarioService instance."""
    return ScenarioService()
```

**Add Migration Comment:**
```python
# ============================================================================
# Singleton - REMOVED
# ============================================================================
#
# DEPRECATED: Singleton pattern removed as part of Phase 2 refactoring.
# Use ScenarioService(db_pool=...) directly instead.
#
# Migration:
#     OLD: service = get_scenario_service()
#     NEW: service = ScenarioService(db_pool=db_pool)
#     OR:  service = container.resolve("scenarios")
#
```

### Step 2: Update combined_server.py

**File:** `combined_server.py`

**Change Import (line 101):**
```python
# OLD:
from app.services.scenarios import get_scenario_service, ShockType

# NEW:
from app.services.scenarios import ScenarioService, ShockType
```

**Change Usage (line 3486):**
```python
# OLD:
service = get_scenario_service()

# NEW (Option 1 - DI Container):
from app.core.di_container import get_container
container = get_container()
if not container._initialized:
    from app.core.service_initializer import initialize_services
    initialize_services(container, db_pool=db_pool)
service = container.resolve("scenarios")

# NEW (Option 2 - Direct Instantiation):
service = ScenarioService(db_pool=db_pool)
```

**Recommendation:** Use Option 2 (direct instantiation) for this fallback code path since it's already in an error handler.

---

## Other Issues to Check

### 1. ✅ AlertService Recreated

**Status:** Looks good - no singleton factory function

**File:** `backend/app/services/alerts.py`

**Analysis:**
- Proper class structure
- No singleton factory function
- Uses DI container pattern (registered in service_initializer.py)

### 2. ⚠️ Import Error Handling

**Location:** `combined_server.py:108-119`

**Issue:** Too broad exception handling sets all imports to `None`

**Recommendation:** More granular error handling to identify which specific import failed

---

## Impact Assessment

### Immediate Impact
- ✅ System works (Replit fix resolved the immediate error)
- ❌ Architectural inconsistency introduced
- ❌ Technical debt increased

### Long-term Impact
- Confusion for future developers
- Inconsistent patterns across codebase
- Maintenance burden

---

## Resolution Plan

1. **Immediate (P1):** Remove `get_scenario_service()` function
2. **Immediate (P1):** Update `combined_server.py` to use DI container or direct instantiation
3. **Short-term (P2):** Improve import error handling to be more granular
4. **Short-term (P2):** Add architecture documentation to prevent future anti-patterns

---

## Prevention

### For Future Changes
1. Always check existing architecture patterns before adding new code
2. Review DI container registration before creating factory functions
3. Use direct instantiation or DI container, never singleton factory functions
4. Update documentation when making architectural changes

---

**Status:** 🔴 **CRITICAL** - Must fix before next deployment

