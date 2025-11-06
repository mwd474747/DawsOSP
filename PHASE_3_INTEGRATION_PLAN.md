# Phase 3 Integration Plan - After Replit Fixes

**Date:** January 14, 2025  
**Status:** ✅ **READY FOR EXECUTION** (after Replit completes backend fixes)  
**Purpose:** Integration steps after critical bugs are fixed

---

## Prerequisites

**Replit Agent Tasks (must complete first):**
1. ✅ Fix FactorAnalyzer field name bug (`valuation_date` vs `asof_date`)
2. ✅ Fix import/class name bug (`FactorAnalysisService` → `FactorAnalyzer`)
3. ✅ Create `economic_indicators` table (schema + migration)

**Status:** ⏳ **WAITING FOR REPLIT**

---

## Integration Steps

### Step 1: Verify Replit Fixes (30 minutes)

**Tasks:**
1. Verify `FactorAnalyzer` field name fix works
   - Test query: `SELECT valuation_date as asof_date FROM portfolio_daily_values`
   - Verify no SQL errors
2. Verify import fix works
   - Test: `from app.services.factor_analysis import FactorAnalyzer`
   - Verify no ImportError
3. Verify `economic_indicators` table exists
   - Test: `SELECT * FROM economic_indicators LIMIT 1;`
   - Verify table structure matches FactorAnalyzer usage

**Acceptance Criteria:**
- ✅ No SQL errors when running FactorAnalyzer
- ✅ No ImportError when importing FactorAnalyzer
- ✅ Table exists and is accessible

---

### Step 2: Integrate FactorAnalyzer into risk_compute_factor_exposures (4-5 hours)

**File:** `backend/app/agents/financial_analyst.py`

**Current State (Line 1172-1173):**
```python
# Use fallback data for factor exposures since FactorAnalysisService is not fully implemented
logger.warning("Using fallback factor exposures - FactorAnalysisService not available")
```

**Target State:**
```python
from app.services.factor_analysis import FactorAnalyzer
from app.db import get_db_connection_with_rls

async with get_db_connection_with_rls(ctx) as db:
    factor_service = FactorAnalyzer(db)
    result = await factor_service.compute_factor_exposure(
        portfolio_id=portfolio_id_uuid,
        pack_id=ctx.pricing_pack_id,
        lookback_days=252  # Default 1 year
    )
    
    # Transform result to match expected format
    return {
        "beta_real_rate": result.get("beta_real_rate", 0.0),
        "beta_inflation": result.get("beta_inflation", 0.0),
        "beta_credit": result.get("beta_credit", 0.0),
        "beta_fx": result.get("beta_fx", 0.0),
        "beta_market": result.get("beta_market", 0.0),
        "r_squared": result.get("r_squared", 0.0),
        "var_factor": result.get("var_factor", 0.0),
        "var_idiosyncratic": result.get("var_idiosyncratic", 0.0),
        "_provenance": "real"  # No longer stub!
    }
```

**Tasks:**
1. Remove stub data fallback
2. Add FactorAnalyzer import and instantiation
3. Call `compute_factor_exposure()` with correct parameters
4. Transform result to match expected API format
5. Update `_provenance` to "real" (not "stub")
6. Add error handling for insufficient data
7. Test with real portfolios

**Files to Update:**
- `backend/app/agents/financial_analyst.py` (line ~1172)

---

### Step 3: Verify risk_get_factor_exposure_history (1 hour)

**File:** `backend/app/agents/financial_analyst.py`

**Current State (Line 1235):**
- Uses `FactorAnalysisService` (wrong import - Replit will fix)
- Uses `FactorAnalyzer` correctly after fix

**Tasks:**
1. Verify Replit fix works (import and instantiation)
2. Verify historical query works correctly
3. Test with real portfolios
4. Verify output format matches expected API

**Note:** This method already uses FactorAnalyzer (after Replit fix), just needs verification.

---

### Step 4: End-to-End Testing (2-3 hours)

**Test Scenarios:**
1. **Factor Analysis with Real Data:**
   - Test `risk.compute_factor_exposures` with real portfolio
   - Verify no stub data
   - Verify factors are calculated correctly
   - Verify `_provenance` is "real"

2. **Factor Analysis with Insufficient Data:**
   - Test with portfolio that has < 30 days of history
   - Verify error handling works correctly
   - Verify no stub fallback (should return error, not stub)

3. **Historical Factor Analysis:**
   - Test `risk.get_factor_exposure_history`
   - Verify historical lookback works
   - Verify output format is correct

4. **Integration with Patterns:**
   - Test pattern that uses `risk.compute_factor_exposures`
   - Verify pattern output is correct
   - Verify no stub data warnings in UI

**Acceptance Criteria:**
- ✅ No stub data in factor analysis
- ✅ No SQL errors
- ✅ No ImportError
- ✅ Factors calculated correctly
- ✅ `_provenance` is "real" (not "stub")
- ✅ Error handling works correctly

---

## Files Summary

**Created (This Session):**
- ✅ `backend/db/schema/economic_indicators.sql` - Schema file
- ✅ `backend/db/migrations/015_add_economic_indicators.sql` - Migration file

**To Be Modified (After Replit):**
- ⏳ `backend/app/services/factor_analysis.py` - Field name fix (Replit)
- ⏳ `backend/app/agents/financial_analyst.py` - Import fix + integration (Replit + This)

---

## Timeline

**After Replit Completes (4-6 hours):**
1. **Step 1:** Verify fixes (30 min)
2. **Step 2:** Integrate FactorAnalyzer (4-5 hours)
3. **Step 3:** Verify history method (1 hour)
4. **Step 4:** End-to-end testing (2-3 hours)

**Total:** 8-10 hours (after Replit completes)

---

## Success Criteria

**Phase 3 Task 3.1 Complete When:**
- ✅ `risk.compute_factor_exposures` uses real FactorAnalyzer
- ✅ No stub data in factor analysis
- ✅ `_provenance` is "real" (not "stub")
- ✅ All tests pass
- ✅ Error handling works correctly
- ✅ No SQL errors
- ✅ No ImportError

---

**Status:** ✅ **READY FOR EXECUTION** (after Replit completes)

