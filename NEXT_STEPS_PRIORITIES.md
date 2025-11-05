# Next Steps & Priorities

**Date:** November 5, 2025  
**Status:** ✅ **Priority 1 Complete - Ready for Next Phase**

---

## ✅ Completed Work

### Priority 1: API Layer Integration (COMPLETE)

**Status:** ✅ **ALL FIXES IMPLEMENTED AND VALIDATED**

**Completed:**
1. ✅ Updated `executor.py` imports to include PricingService and custom exceptions
2. ✅ Replaced `pack_queries.get_latest_pack()` with `PricingService.get_latest_pack()`
3. ✅ Added custom exception handling before generic Exception catch
4. ✅ Updated `health_pack` endpoint to use PricingService
5. ✅ Fixed HTTP status codes (400 for validation, 503 for not found/stale)
6. ✅ Added rich error context (pack_id, status, is_fresh, estimated_ready)
7. ✅ Validated all changes (syntax, linting, logic)

**Impact:**
- ✅ Consistent error handling across API and service layers
- ✅ Correct HTTP status codes for better client retry logic
- ✅ Rich error messages for better debugging
- ✅ Consistent patterns across all endpoints

---

## 🎯 Next Priorities

### Priority 2: Service Layer Consistency (MEDIUM)

**Goal:** Update remaining services to use custom exceptions instead of ValueError

**Services to Update:**
1. `backend/app/services/metrics.py:506` - Raises `ValueError` for "Pricing pack not found"
2. `backend/app/services/currency_attribution.py:115` - Raises `ValueError` for pack_id validation
3. `backend/app/services/currency_attribution.py:407` - Raises `ValueError` for "Pricing pack not found"
4. `backend/app/services/risk_metrics.py:506` - Raises `ValueError` for "Pricing pack not found"
5. `backend/app/services/factor_analysis.py:433` - Raises `ValueError` for "Pricing pack not found"

**Tasks:**
1. Update `metrics.py` to use `PricingPackNotFoundError`
2. Update `currency_attribution.py` to use `PricingPackValidationError` and `PricingPackNotFoundError`
3. Update `risk_metrics.py` to use `PricingPackNotFoundError`
4. Update `factor_analysis.py` to use `PricingPackNotFoundError`
5. Test all changes to ensure no regressions

**Impact:**
- Medium - Improves consistency and error categorization
- Makes error handling at API layer simpler (no need to catch both ValueError and custom exceptions)

**Estimated Effort:** 2-3 hours

---

### Priority 3: Code Cleanup (LOW)

**Goal:** Remove dead code and improve code quality

**Tasks:**
1. Remove redundant check in `financial_analyst.py:337-338` (dead code - never reached)
2. Review other potential dead code or redundant checks

**Impact:**
- Low - Code cleanup, no functional change

**Estimated Effort:** 30 minutes

---

### Priority 4: Documentation Updates (LOW)

**Goal:** Update API documentation to reflect custom exceptions

**Tasks:**
1. Update `executor.py` docstring to document custom exceptions
2. Update OpenAPI schema to include new error responses
3. Add examples of error responses for each exception type
4. Update `pricing.py` top-level docstring to mention exception handling

**Impact:**
- Low - Documentation improvement

**Estimated Effort:** 1 hour

---

### Priority 5: Integration Tests (MEDIUM)

**Goal:** Add tests to validate exception handling

**Tasks:**
1. Create integration tests for exception handling
2. Test `PricingPackNotFoundError` → 503 Service Unavailable
3. Test `PricingPackStaleError` → 503 Service Unavailable
4. Test `PricingPackValidationError` → 400 Bad Request
5. Verify error response structure includes pack_id, status, reason

**Impact:**
- Medium - Regression tests prevent future issues
- Confidence in error handling correctness

**Estimated Effort:** 2-3 hours

---

## 📋 Recommended Sequence

### Immediate Next Steps (This Week)

1. **Priority 2: Service Layer Consistency** (2-3 hours)
   - Update remaining services to use custom exceptions
   - Ensures consistency across entire codebase
   - Prevents confusion between ValueError and custom exceptions

2. **Priority 3: Code Cleanup** (30 minutes)
   - Quick cleanup while working on Priority 2
   - Remove dead code in financial_analyst.py

### Short-Term (Next Week)

3. **Priority 5: Integration Tests** (2-3 hours)
   - Validate exception handling works correctly
   - Prevent regressions

4. **Priority 4: Documentation Updates** (1 hour)
   - Update API documentation
   - Improve developer experience

---

## 🎯 Summary

**Current Status:**
- ✅ Priority 1: API Layer Integration - **COMPLETE**
- ⏳ Priority 2: Service Layer Consistency - **NEXT**
- ⏳ Priority 3: Code Cleanup - **PENDING**
- ⏳ Priority 4: Documentation Updates - **PENDING**
- ⏳ Priority 5: Integration Tests - **PENDING**

**Recommended Next Action:**
**Start Priority 2: Service Layer Consistency**

This will:
- Complete the exception handling refactoring
- Ensure consistency across all services
- Make error handling simpler and more maintainable

---

## 📝 Notes

**Why Priority 2 First?**
- Completes the exception handling refactoring started in Phase 2
- Ensures consistency across entire codebase
- Prevents confusion between ValueError and custom exceptions
- Makes future work easier (documentation, tests)

**Why Priority 3 with Priority 2?**
- Quick cleanup that can be done alongside Priority 2
- Removes dead code that's already identified
- Low risk, high value

**Why Priority 5 Before Priority 4?**
- Tests validate that the implementation works correctly
- Documentation can be updated after validation
- Reduces risk of documenting incorrect behavior

---

## ✅ Validation Checklist for Next Work

Before starting Priority 2, ensure:
- ✅ All Priority 1 fixes are committed and pushed
- ✅ Validation report confirms all fixes work correctly
- ✅ No syntax or linting errors
- ✅ API endpoints tested manually (if possible)

After completing Priority 2, validate:
- ✅ All services use custom exceptions consistently
- ✅ No ValueError raised for pricing pack errors
- ✅ All imports updated correctly
- ✅ No regressions in existing functionality

