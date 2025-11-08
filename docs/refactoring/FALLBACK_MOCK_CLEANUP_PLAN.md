# Fallback and Mock Cleanup Plan

**Date:** January 15, 2025  
**Status:** 🚧 IN PROGRESS  
**Priority:** P1 (High - Technical Debt Clearance)

---

## Executive Summary

This plan addresses fallback patterns, mocks, and placeholder values that may be masking real issues instead of fixing them. The goal is to ensure that errors are properly surfaced and handled, not silently ignored or masked by fallbacks.

---

## Issues Identified

### 1. Placeholder Values in Docstrings (P2 - Medium)

**Location:** Multiple files  
**Issue:** "xxx" placeholder values in example code in docstrings may be confusing

**Files:**
- `backend/app/services/alerts.py:542,623,958,1061` - Example portfolio_id values
- `backend/app/services/notifications.py:24,38` - Example user_id/alert_id values
- `backend/app/services/dlq.py:34` - Example alert_id/user_id values
- `backend/app/core/alert_validators.py:228,283` - Example portfolio_id values

**Impact:** LOW - These are in docstring examples, not production code

**Fix:** Replace with clearer examples (e.g., `"portfolio-uuid-here"` or actual example UUIDs)

---

### 2. Stub Mode Fallback on Connection Errors (P1 - High)

**Location:** `backend/app/services/optimizer.py:293-296`

**Issue:** OptimizerService falls back to stub mode on database connection errors, which could mask real database issues.

**Current Code:**
```python
except Exception as e:
    # Connection/configuration errors - log and fall back to stub mode
    logger.warning(f"Failed to initialize database connections: {e}. Falling back to stub mode.")
    # Don't raise DatabaseError here - graceful degradation is intentional
    self.use_db = False
```

**Problem:** This masks database connection issues. In production, we should fail fast, not silently degrade to stub mode.

**Fix:** 
- Add production guard: Only allow stub mode fallback in development/testing
- In production, raise the exception instead of falling back
- Ensure proper error handling and logging

---

### 3. Stub Fundamentals on Missing API Key (P1 - High)

**Location:** `backend/app/agents/data_harvester.py:857+`

**Issue:** `_stub_fundamentals_for_symbol` is used when FMP_API_KEY is not configured, masking the real issue (missing API key).

**Current Behavior:** Returns stub data instead of error when API key is missing.

**Problem:** This masks configuration issues. Users should know when API keys are missing.

**Fix:**
- Check for API key at initialization
- Raise clear error if API key is missing in production
- Only use stub data in explicit test mode (guarded by environment)

---

### 4. Returning False on Missing Values (P2 - Medium)

**Location:** `backend/app/services/alerts.py:546-548,627-629`

**Issue:** When metric/rating values are None, the code returns False and logs a warning, but doesn't surface why the value is None.

**Current Code:**
```python
if value is None:
    logger.warning(f"Metric value not available: {condition}")
    return False
```

**Problem:** This masks the root cause (why is the value None? Database issue? Missing data? Calculation error?).

**Fix:**
- Log more context about why the value is None
- Include error details in the result
- Consider raising an exception for critical missing values

---

### 5. Default Metrics on Missing Data (P2 - Medium)

**Location:** `backend/app/services/fundamentals_transformer.py:219-247`

**Issue:** `_get_default_metrics` returns conservative default metrics when data is unavailable.

**Current Behavior:** Returns mid-range ratings (~5/10) when data is missing.

**Problem:** This might mask data quality issues. Users should know when data is missing.

**Fix:**
- Ensure proper logging when defaults are used
- Include provenance metadata indicating defaults were used
- Consider returning error result instead of defaults for critical metrics

---

### 6. Cached Data Fallback (P3 - Low)

**Location:** `backend/app/integrations/base_provider.py:248-254`

**Issue:** Falls back to cached data after all retries fail.

**Current Behavior:** Serves stale cached data with warning.

**Assessment:** This is actually **acceptable** - it's graceful degradation, not masking issues. The warning is logged, and the stale flag is set.

**Action:** Keep as-is, but ensure logging is clear.

---

## Fix Plan

### Phase 1: Critical Fixes (P1 - High Priority)

1. **Fix OptimizerService Stub Mode Fallback**
   - Add production guard
   - Raise exception in production instead of falling back
   - Keep stub mode only for explicit testing

2. **Fix Stub Fundamentals on Missing API Key**
   - Check API key at initialization
   - Raise clear error if missing in production
   - Only use stub in test mode

### Phase 2: Medium Priority Fixes (P2)

3. **Improve Missing Value Handling**
   - Add more context to None value warnings
   - Include error details in results
   - Consider exceptions for critical missing values

4. **Improve Default Metrics Logging**
   - Ensure clear logging when defaults are used
   - Include provenance metadata
   - Consider error results for critical metrics

5. **Replace Placeholder Values in Docstrings**
   - Replace "xxx" with clearer examples
   - Use example UUIDs or descriptive placeholders

---

## Implementation Order

1. **Fix OptimizerService stub mode fallback** (~1 hour)
2. **Fix stub fundamentals on missing API key** (~1 hour)
3. **Improve missing value handling** (~2 hours)
4. **Improve default metrics logging** (~1 hour)
5. **Replace placeholder values** (~30 minutes)

**Total Estimated Time:** ~5-6 hours

---

## Success Criteria

- ✅ No silent fallbacks to stub mode in production
- ✅ Clear errors when API keys are missing
- ✅ Proper logging when defaults are used
- ✅ No placeholder values in production code
- ✅ All fallbacks are intentional and logged

---

**Status:** 🚧 IN PROGRESS  
**Last Updated:** January 15, 2025

