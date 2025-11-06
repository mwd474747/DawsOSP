# Critical Fixes - Dependency & Pattern Validation

**Date:** January 14, 2025  
**Status:** 🔍 **VALIDATING BEFORE FIXES**  
**Purpose:** Validate dependencies and code pattern intentions before fixing critical issues

---

## Executive Summary

**Validating 4 Critical Issues:**

1. **Issue #14:** `base_agent.py:342` - PP_latest fallback
2. **Issue #3:** `build_pricing_pack.py:189-196` - Stub fallback
3. **Issue #11:** `pricing.py` - Stub mode enabled
4. **Issue #27:** `pattern_orchestrator.py:787-811` - Template validation

**Status:** ⏳ **VALIDATING** - Checking current state and dependencies

---

## Issue #14: PP_latest Fallback - Validation

**File:** `backend/app/agents/base_agent.py:325-360`

**Current Code:**
```python
def _resolve_pricing_pack_id(
    self,
    pack_id: Optional[str],
    ctx: RequestCtx,
    default: Optional[str] = None
) -> str:
    """Resolve pricing_pack_id with fallback chain."""
    from app.services.pricing import validate_pack_id
    
    # Resolve from multiple sources (no fallback to "PP_latest")
    resolved = pack_id or ctx.pricing_pack_id or default
    
    if not resolved:
        raise PricingPackValidationError(
            pricing_pack_id="",
            reason="pricing_pack_id is required but not provided. "
                   "Must be set in request context (ctx.pricing_pack_id) or provided as parameter. "
                   "Use get_pricing_service().get_latest_pack() to fetch current pack."
        )
    
    # Validate format
    validate_pack_id(resolved)
    
    return resolved
```

**Current State:** ✅ **ALREADY FIXED**
- No "PP_latest" fallback found
- Raises PricingPackValidationError if not resolved
- Validates format using `validate_pack_id()`

**Dependencies:**
- Uses `validate_pack_id()` from `app.services.pricing`
- Uses `PricingPackValidationError` from `app.core.types`
- Used by 11 capabilities in `financial_analyst.py` and `macro_hound.py`

**Pattern Intent:**
- Fallback chain: `pack_id` → `ctx.pricing_pack_id` → `default`
- No fallback to literal string (correct behavior)
- Raises error if not resolved (correct behavior)

**Action:** ✅ **NO FIX NEEDED** - Already correct

---

## Issue #3: Stub Fallback in Production - Validation

**File:** `backend/jobs/build_pricing_pack.py:189-213`

**Current Code:**
```python
# Validate data completeness
if not self._validate_data_completeness(securities, prices_data, fx_data):
    logger.error("Data validation failed, pack incomplete")
    
    # Production guard: never fall back to stubs in production
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError(
            f"Data validation failed for pricing pack asof {asof_date}. "
            f"Cannot build pack in production with incomplete data. "
            f"Stub fallback is only available in development/testing."
        )
    
    # Development mode: allow stub fallback with warning
    if self.use_stubs:
        logger.warning("⚠️ DEVELOPMENT MODE: Falling back to stub data")
        prices_data = self._build_stub_prices(asof_date, securities)
        fx_data = self._build_stub_fx_rates(asof_date)
        source = "stub_fallback"
        status = "warming"
    else:
        raise ValueError(
            f"Data validation failed for pricing pack asof {asof_date}. "
            f"Cannot build pack with incomplete data. "
            f"Set use_stubs=True for development/testing stub fallback."
        )
```

**Current State:** ✅ **ALREADY FIXED**
- Production guard checks `ENVIRONMENT == "production"`
- Raises ValueError in production (no stub fallback)
- Only allows stub fallback in development with `use_stubs=True`
- Logs warning when using stub data

**Dependencies:**
- Uses `os.getenv("ENVIRONMENT")` for production check
- Requires `use_stubs=True` to enable stub fallback
- Used by pricing pack builder job

**Pattern Intent:**
- Production: Never fall back to stubs (raises error)
- Development: Allow stub fallback with explicit `use_stubs=True`
- Clear logging when stub data is used

**Action:** ✅ **NO FIX NEEDED** - Already correct

---

## Issue #11: Stub Mode in Pricing Service - Validation

**File:** `backend/app/services/pricing.py:141-164`

**Current Code:**
```python
def __init__(self, use_db: bool = True):
    """
    Initialize pricing service.
    
    Args:
        use_db: Use database connection (default: True, False for testing)
    
    Raises:
        ValueError: If use_db=False in production environment
    """
    import os
    
    # Production guard: prevent stub mode in production
    if not use_db and os.getenv("ENVIRONMENT") == "production":
        raise ValueError(
            "Cannot use stub mode (use_db=False) in production environment. "
            "Stub mode is only available for development and testing."
        )
    
    self.use_db = use_db
    self.pack_queries = get_pricing_pack_queries(use_db=use_db)
    
    if not use_db:
        logger.warning("⚠️ STUB MODE ACTIVE - Using fake pricing data (development/testing only)")
```

**Current State:** ✅ **ALREADY FIXED**
- Production guard checks `ENVIRONMENT == "production"`
- Raises ValueError if `use_db=False` in production
- Logs warning when stub mode is active

**Dependencies:**
- Uses `os.getenv("ENVIRONMENT")` for production check
- Used by all pricing service methods
- Need to check `get_pricing_service()` function

**Pattern Intent:**
- Production: Prevent stub mode (raises error)
- Development: Allow stub mode with explicit `use_db=False`
- Clear logging when stub mode is active

**Action:** ⚠️ **NEED TO VERIFY** - Check `get_pricing_service()` function

---

## Issue #27: Template Variable Validation - Validation

**File:** `backend/app/core/pattern_orchestrator.py:895-935`

**Current Code:**
```python
def _resolve_value(self, value: Any, state: Dict[str, Any]) -> Any:
    """
    Recursively resolve a single value (supports nested dicts/lists).
    
    Args:
        value: Value to resolve (supports template variables {{...}})
        state: Current execution state
    
    Returns:
        Resolved value
    """
    # Handle string templates
    if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
        # Extract path: {{positions}} → ["positions"] or {{positions.positions}} → ["positions", "positions"]
        path = value[2:-2].strip().split(".")
        result = state
        for part in path:
            if isinstance(result, dict):
                result = result.get(part)
            elif hasattr(result, part):
                result = getattr(result, part)
            else:
                raise ValueError(
                    f"Cannot resolve template path {value}: {part} not found"
                )
            # Allow None for optional parameters
            # Don't raise ValueError if result is None - just return None
            # This allows optional fields like custom_shocks to be None
        return result
    
    # Handle nested dicts
    elif isinstance(value, dict):
        return {k: self._resolve_value(v, state) for k, v in value.items()}
    
    # Handle lists
    elif isinstance(value, list):
        return [self._resolve_value(item, state) for item in value]
    
    # Return primitive values as-is
    else:
        return value
```

**Current State:** ⚠️ **PARTIAL** - Needs validation for required parameters

**Issue:**
- Raises ValueError if path not found (line 917-919)
- But allows None to be returned if path exists but value is None (line 920-923)
- No distinction between required and optional template variables
- No validation that required variables are not None

**Dependencies:**
- Used by `_resolve_args()` to resolve step arguments
- Used throughout pattern execution
- Need to identify which template variables are required

**Pattern Intent:**
- Optional parameters can be None (correct - e.g., `custom_shocks`)
- Required parameters should raise error if None (missing - e.g., `{{ctx.pricing_pack_id}}`)
- Need to distinguish required vs optional

**Action:** ⚠️ **NEEDS FIX** - Add validation for required parameters

---

## Validation Summary

### ✅ Already Fixed (No Action Needed)

1. **Issue #14:** PP_latest fallback - ✅ **ALREADY FIXED**
   - No "PP_latest" fallback in code
   - Raises PricingPackValidationError if not resolved
   - Validates format

2. **Issue #3:** Stub fallback in production - ✅ **ALREADY FIXED**
   - Production guard checks `ENVIRONMENT == "production"`
   - Raises ValueError in production
   - Only allows stub fallback in development

3. **Issue #11:** Stub mode in pricing - ✅ **ALREADY FIXED** (needs verification)
   - Production guard in `__init__`
   - Need to verify `get_pricing_service()` function

### ⚠️ Needs Fix

4. **Issue #27:** Template variable validation - ⚠️ **NEEDS FIX**
   - Allows None for optional parameters (correct)
   - No validation for required parameters (missing)
   - Need to add validation for required template variables

---

## Next Steps

1. ✅ **Verify `get_pricing_service()` function** - Check if it can bypass production guard
2. ⚠️ **Fix template variable validation** - Add validation for required parameters
3. ✅ **Test all fixes** - Verify no breaking changes

---

**Status:** 🔍 **VALIDATION IN PROGRESS**

