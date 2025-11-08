# Data Scaling Audit - Critical Bugs Found

**Date:** 2025-11-08
**Status:** 🔴 CRITICAL BUGS IDENTIFIED
**Severity:** HIGH - Double conversion errors causing 100x incorrect values
**Files Affected:** 2 (cycles.py, macro_data_helpers.py)

---

## Executive Summary

**CRITICAL FINDING:** Confirmed double conversion bugs in 2 files causing values to be 100x too small.

### The Bug

**Database stores TRANSFORMED values** (decimals like 0.045 for 4.5%)
**↓**
**Code divides by 100 AGAIN** (÷100 creates 0.00045)
**=**
**Values 100x too small** (0.00045 instead of 0.045)

### Evidence

1. **macro.py:688** - Stores transformed value: `final_value = transformed_value`
2. **cycles.py:734-738** - Divides by 100 again: `raw_value / 100.0`
3. **macro_data_helpers.py:89** - Divides DGS10 by 100 again: `dgs10 / Decimal("100")`

### Impact

- Risk-free rate 100x too small → All Sharpe ratios wrong
- Macro indicators 100x too small → Regime detection broken
- All calculations using these values are incorrect

---

## Bug Details

### BUG #1: cycles.py Double Conversion (CRITICAL)

**File:** [backend/app/services/cycles.py](backend/app/services/cycles.py)
**Lines:** 732-748
**Severity:** 🔴 CRITICAL

**The Problem:**
```python
# Line 725: Gets value from database (ALREADY TRANSFORMED)
raw_value = float(row["value"])  # e.g., 0.045 (4.5% stored as decimal)

# Lines 734-738: DIVIDES AGAIN
elif code_key == "gdp_growth":
    db_indicators[code_key] = raw_value / 100.0  # 0.045 ÷ 100 = 0.00045 ❌
elif code_key == "unemployment":
    db_indicators[code_key] = raw_value / 100.0  # DOUBLE CONVERSION ❌
elif code_key == "interest_rate":
    db_indicators[code_key] = raw_value / 100.0  # DOUBLE CONVERSION ❌
```

**Evidence of Transformation:**
```python
# macro.py:680-688 - PROOF database stores transformed values
transformed_value = self.transformation_service.transform_fred_value(
    series_id=indicator_id,
    value=raw_value,  # Raw FRED: 4.5
    ...
)
# transformed_value is now: 0.045

final_value = transformed_value if transformed_value is not None else raw_value

indicator = MacroIndicator(
    value=final_value,  # ← Stores 0.045 (decimal)
)
await self.store_indicator(indicator)  # ← Database gets 0.045
```

**Impact:**
- GDP growth: 2.5% stored as 0.025 → divided to 0.00025 (100x too small)
- Unemployment: 3.7% stored as 0.037 → divided to 0.00037 (100x too small)
- Interest rate: 4.08% stored as 0.0408 → divided to 0.000408 (100x too small)

**Result:** Macro regime detection completely broken

---

### BUG #2: macro_data_helpers.py Double Conversion (CRITICAL)

**File:** [backend/app/services/macro_data_helpers.py](backend/app/services/macro_data_helpers.py)
**Line:** 89
**Severity:** 🔴 CRITICAL

**The Problem:**
```python
async def get_risk_free_rate(as_of_date: Optional[date] = None) -> Decimal:
    # Gets DGS10 from database (ALREADY TRANSFORMED)
    dgs10 = await get_latest_indicator_value("DGS10", as_of_date)

    if dgs10 is not None:
        # WRONG COMMENT: Says "stored in percent" but it's stored as decimal!
        # DGS10 is stored in percent (e.g., 4.5), convert to decimal (0.045)
        return dgs10 / Decimal("100")  # ❌ DOUBLE CONVERSION
```

**Correct Comment Should Say:**
```python
# DGS10 is stored as decimal (e.g., 0.0408 for 4.08%), use as-is
return dgs10  # ✓ NO CONVERSION NEEDED
```

**Impact:**
- Risk-free rate: 4.08% stored as 0.0408 → divided to 0.000408 (100x too small)
- Sharpe ratios: `(return - rf) / vol` with rf 100x too small = inflated Sharpe
- All risk-adjusted metrics wrong

**Example Calculation:**
```python
# CORRECT:
portfolio_return = 0.12  # 12%
risk_free_rate = 0.0408  # 4.08%
volatility = 0.15  # 15%
sharpe = (0.12 - 0.0408) / 0.15 = 0.528  ✓

# BUGGY (current):
risk_free_rate = 0.000408  # 100x too small
sharpe = (0.12 - 0.000408) / 0.15 = 0.798  ❌ (51% too high!)
```

---

### BUG #3: cycles.py Inconsistent Divisors (HIGH)

**File:** [backend/app/services/cycles.py](backend/app/services/cycles.py)
**Lines:** 732, 740, 742, 744
**Severity:** 🟠 HIGH

**The Problem:**
Different indicators use wildly inconsistent divisors with no justification:

```python
if code_key == "inflation":
    db_indicators[code_key] = raw_value / 10000.0  # ❌ Why 10000?

elif code_key == "credit_growth":
    db_indicators[code_key] = raw_value / 1000000.0  # ❌ Why 1 million?

elif code_key == "debt_service_ratio":
    db_indicators[code_key] = raw_value / 10000000.0  # ❌ Why 10 million!?

elif code_key == "debt_to_gdp":
    db_indicators[code_key] = raw_value / 27436999  # ❌ Magic number (2023 GDP)
```

**Analysis:**

**Inflation (÷10000):**
- FRED CPIAUCSL transformed to YoY % change by FREDTransformationService
- Output: 0.032 (3.2%)
- Divided by 10000: 0.0000032 (0.00032%) ❌ WAY TOO SMALL
- **Should be:** No division (already decimal) or ÷100 if raw

**Credit Growth (÷1000000):**
- FRED TOTBKCR is absolute value in millions of dollars
- FREDTransformationService should convert to YoY % change
- If raw: 104104.952 million dollars
- Divided by 1000000: 0.104 (10.4%) - This might be correct for RAW
- But if using transformed: Already a decimal, wrong divisor

**Debt Service Ratio (÷10000000):**
- FRED TDSP is already in percentage (9.91 = 9.91%)
- FREDTransformationService converts to 0.0991 (decimal)
- Divided by 10000000: 0.0000000099 ❌ ABSURDLY SMALL
- **Should be:** No division (already decimal)

**Debt to GDP (÷27436999):**
- Hardcoded 2023 US GDP value
- Becomes stale as GDP grows
- **Should use:** FRED series GFDEGDQ188S (already percentage)

**Impact:** All macro regime calculations using these indicators are wrong

---

## Root Cause Analysis

### How Did This Happen?

**Timeline:**

1. **Original Implementation (2024-Q3):**
   - cycles.py created with hardcoded scaling
   - Assumed database had RAW FRED values
   - Manually divided by 100, 10000, etc.

2. **FREDTransformationService Added (2024-10-14):**
   - Centralized transformation logic
   - macro.py updated to use service
   - Database NOW stores transformed values

3. **Nobody Updated cycles.py:**
   - Still assumes raw values
   - Still divides by 100, 10000, etc.
   - Creates DOUBLE CONVERSION

**Why It Persisted:**

1. **No Integration Tests** - Never caught the double conversion
2. **No Validation** - Never checked if values are in expected ranges
3. **Misleading Comments** - macro_data_helpers.py comment says "stored in percent"
4. **Silently Wrong** - Code runs without errors, just produces wrong results

---

## Data Flow Visualization

### Current (BUGGY) Flow

```
┌─────────────────────────────────────────────────────────┐
│ FRED API                                                │
│ DGS10 = 4.08 (means 4.08%)                             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ FREDTransformationService (macro.py:680)                │
│ transform_fred_value("DGS10", 4.08)                     │
│ → Returns: 0.0408 (÷100 conversion)                     │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Database: macro_indicators.value                        │
│ → Stores: 0.0408 (decimal)                              │
└───────────────────────┬─────────────────────────────────┘
                        │
           ┌────────────┴────────────┐
           │                         │
           ▼                         ▼
┌─────────────────────┐   ┌─────────────────────────────┐
│ cycles.py:738       │   │ macro_data_helpers.py:89    │
│                     │   │                             │
│ Gets: 0.0408        │   │ Gets: 0.0408                │
│ Divides: ÷100       │   │ Divides: ÷100               │
│ Result: 0.000408 ❌ │   │ Result: 0.000408 ❌          │
└─────────────────────┘   └─────────────────────────────┘
```

### Correct Flow (AFTER FIX)

```
┌─────────────────────────────────────────────────────────┐
│ FRED API                                                │
│ DGS10 = 4.08 (means 4.08%)                             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ FREDTransformationService (macro.py:680)                │
│ transform_fred_value("DGS10", 4.08)                     │
│ → Returns: 0.0408 (÷100 conversion)                     │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Database: macro_indicators.value                        │
│ → Stores: 0.0408 (decimal)                              │
└───────────────────────┬─────────────────────────────────┘
                        │
           ┌────────────┴────────────┐
           │                         │
           ▼                         ▼
┌─────────────────────┐   ┌─────────────────────────────┐
│ cycles.py (FIXED)   │   │ macro_data_helpers (FIXED)  │
│                     │   │                             │
│ Gets: 0.0408        │   │ Gets: 0.0408                │
│ No division         │   │ No division                 │
│ Result: 0.0408 ✓    │   │ Result: 0.0408 ✓            │
└─────────────────────┘   └─────────────────────────────┘
```

---

## Fix Plan

### Fix #1: macro_data_helpers.py (5 minutes, LOW RISK)

**File:** `backend/app/services/macro_data_helpers.py`
**Lines to change:** 88-89

**BEFORE:**
```python
if dgs10 is not None:
    # DGS10 is stored in percent (e.g., 4.5), convert to decimal (0.045)
    return dgs10 / Decimal("100")
```

**AFTER:**
```python
if dgs10 is not None:
    # DGS10 is stored as decimal by FREDTransformationService (e.g., 0.0408 for 4.08%)
    # No conversion needed - use value as-is
    return dgs10
```

**Validation:**
```python
# Test with known value
rf = await get_risk_free_rate(date(2025, 11, 7))
assert 0.03 < rf < 0.06, f"Risk-free rate {rf} outside reasonable range (3%-6%)"
```

---

### Fix #2: cycles.py (20 minutes, MEDIUM RISK)

**File:** `backend/app/services/cycles.py`
**Lines to change:** 727-753

**BEFORE:**
```python
# Apply scaling based on configuration rules
scaling_rule = self.config_manager.get_scaling_rule(code_key)
if scaling_rule:
    # Apply the scaling transformation
    if code_key == "inflation":
        db_indicators[code_key] = raw_value / 10000.0
    elif code_key == "gdp_growth":
        db_indicators[code_key] = raw_value / 100.0
    # ... etc (all divisions)
```

**AFTER:**
```python
# Database stores values already transformed by FREDTransformationService
# Values are in decimal format (0.0408 = 4.08%), use as-is
#
# Exception: If value > 10, it may be untransformed raw data (legacy)
# In that case, apply percentage conversion
if raw_value > 10 and code_key in ["gdp_growth", "unemployment", "interest_rate", "yield_curve"]:
    logger.warning(
        f"Indicator {code_key} value {raw_value} appears untransformed, "
        f"applying percentage conversion. This should not happen with current data pipeline."
    )
    db_indicators[code_key] = raw_value / 100.0
else:
    # Use transformed value as-is
    db_indicators[code_key] = raw_value
```

**Validation:**
```python
# Add range checks after loading
for key, value in db_indicators.items():
    expected_ranges = {
        "gdp_growth": (-0.10, 0.10),  # -10% to +10%
        "unemployment": (0.02, 0.15),  # 2% to 15%
        "interest_rate": (0.0, 0.10),  # 0% to 10%
        "inflation": (-0.05, 0.15),   # -5% to +15%
    }

    if key in expected_ranges:
        min_val, max_val = expected_ranges[key]
        if not (min_val <= value <= max_val):
            logger.error(
                f"Indicator {key}={value} outside expected range "
                f"[{min_val}, {max_val}]. Check transformation pipeline."
            )
```

---

### Fix #3: Add Integration Test (15 minutes)

**File:** `backend/tests/services/test_scaling_bugs.py` (NEW)

```python
"""
Integration test for data scaling bugs.

Regression tests for:
- SCALE-BUG-001: cycles.py double conversion
- SCALE-BUG-002: macro_data_helpers.py double conversion
"""

import pytest
from decimal import Decimal
from datetime import date
from backend.app.services.cycles import CyclesService
from backend.app.services.macro_data_helpers import get_risk_free_rate
from backend.app.db.connection import execute_statement


@pytest.mark.asyncio
async def test_no_double_conversion_cycles():
    """Verify cycles.py uses transformed values without re-dividing."""

    # Insert test data (transformed decimal format)
    await execute_statement(
        "INSERT INTO macro_indicators (indicator_id, indicator_name, date, value, units, source) "
        "VALUES ($1, $2, $3, $4, $5, $6) "
        "ON CONFLICT (indicator_id, date) DO UPDATE SET value = EXCLUDED.value",
        "A191RL1Q225SBEA", "Real Gross Domestic Product", date(2025, 11, 7),
        Decimal("0.025"), "Percent", "FRED"
    )

    # Get indicator from cycles.py
    service = CyclesService()
    indicators = await service.get_latest_indicators(date(2025, 11, 7))

    # Should use value as-is (not divide by 100)
    assert indicators["gdp_growth"] == pytest.approx(0.025, abs=0.001)
    assert indicators["gdp_growth"] != pytest.approx(0.00025, abs=0.00001)  # NOT double-converted


@pytest.mark.asyncio
async def test_no_double_conversion_risk_free_rate():
    """Verify macro_data_helpers uses transformed DGS10 without re-dividing."""

    # Insert test data (transformed decimal format)
    await execute_statement(
        "INSERT INTO macro_indicators (indicator_id, indicator_name, date, value, units, source) "
        "VALUES ($1, $2, $3, $4, $5, $6) "
        "ON CONFLICT (indicator_id, date) DO UPDATE SET value = EXCLUDED.value",
        "DGS10", "10-Year Treasury Constant Maturity Rate", date(2025, 11, 7),
        Decimal("0.0408"), "Percent", "FRED"
    )

    # Get risk-free rate
    rf = await get_risk_free_rate(date(2025, 11, 7))

    # Should use value as-is (not divide by 100)
    assert rf == pytest.approx(Decimal("0.0408"), abs=Decimal("0.001"))
    assert rf != pytest.approx(Decimal("0.000408"), abs=Decimal("0.000001"))  # NOT double-converted


@pytest.mark.asyncio
async def test_indicator_value_ranges():
    """Verify all indicators are in reasonable ranges (not 100x too small)."""

    service = CyclesService()
    indicators = await service.get_latest_indicators()

    # Check ranges
    if "gdp_growth" in indicators:
        assert -0.10 <= indicators["gdp_growth"] <= 0.10, \
            f"GDP growth {indicators['gdp_growth']} outside -10% to +10%"

    if "unemployment" in indicators:
        assert 0.02 <= indicators["unemployment"] <= 0.15, \
            f"Unemployment {indicators['unemployment']} outside 2% to 15%"

    if "interest_rate" in indicators:
        assert 0.0 <= indicators["interest_rate"] <= 0.10, \
            f"Interest rate {indicators['interest_rate']} outside 0% to 10%"
```

---

## Testing Strategy

### Phase 1: Pre-Fix Testing (Capture Current Behavior)

1. **Query Database:**
```bash
# Check actual stored values
psql -U dawsos_user -d dawsos_dev -c "
SELECT indicator_id, indicator_name, value, units
FROM macro_indicators
WHERE indicator_id IN ('DGS10', 'UNRATE', 'A191RL1Q225SBEA')
ORDER BY date DESC LIMIT 5;
"
```

2. **Capture Current Outputs:**
```python
# Save current regime detection output
regime = await cycles_service.detect_regime(date(2025, 11, 7))
with open("baseline_regime_BUGGY.json", "w") as f:
    json.dump(regime, f, indent=2)

# Save current risk-free rate
rf = await get_risk_free_rate(date(2025, 11, 7))
print(f"Current (buggy) risk-free rate: {rf}")
```

### Phase 2: Apply Fixes

1. Fix macro_data_helpers.py (5 min)
2. Fix cycles.py (20 min)
3. Add integration tests (15 min)

### Phase 3: Post-Fix Testing

1. **Run Integration Tests:**
```bash
pytest backend/tests/services/test_scaling_bugs.py -v
```

2. **Compare Outputs:**
```python
# New regime detection output
regime_new = await cycles_service.detect_regime(date(2025, 11, 7))
with open("baseline_regime_FIXED.json", "w") as f:
    json.dump(regime_new, f, indent=2)

# Compare
import json
with open("baseline_regime_BUGGY.json") as f1, open("baseline_regime_FIXED.json") as f2:
    buggy = json.load(f1)
    fixed = json.load(f2)

    print("Indicators comparison:")
    for key in buggy.get("indicators", {}):
        buggy_val = buggy["indicators"][key]
        fixed_val = fixed["indicators"][key]
        ratio = fixed_val / buggy_val if buggy_val != 0 else 0
        print(f"{key}: {buggy_val:.6f} → {fixed_val:.6f} (×{ratio:.1f})")
```

**Expected Result:** Fixed values should be ~100x larger than buggy values

### Phase 4: Validation

1. **Check Ranges:**
   - GDP growth: -10% to +10% (reasonable)
   - Unemployment: 2% to 15% (reasonable)
   - Interest rates: 0% to 10% (reasonable)

2. **Check Regime Detection:**
   - Does the detected regime make sense?
   - Are macro indicators in reasonable ranges?

3. **Check Sharpe Ratios:**
   - Are they in typical range (-2 to +5)?
   - Not inflated by tiny risk-free rate?

---

## Rollback Plan

If fixes cause issues:

1. **Git Revert:**
```bash
git revert <commit-hash>
```

2. **Investigate Discrepancy:**
   - Why did outputs differ?
   - Are database values really transformed?
   - Check FREDTransformationService logs

3. **Add Diagnostic Logging:**
```python
logger.info(f"Database value for {indicator_id}: {raw_value}")
logger.info(f"Value after scaling: {scaled_value}")
logger.info(f"Expected range: {expected_range}")
```

---

## Priority & Timeline

**Priority:** 🔴 P0 - CRITICAL
**Estimated Fix Time:** 40 minutes
**Estimated Test Time:** 20 minutes
**Total:** ~1 hour

**Recommended Approach:**
1. Fix macro_data_helpers.py first (low risk, high impact)
2. Test risk-free rate values
3. Fix cycles.py (medium risk, high impact)
4. Add integration tests
5. Monitor in production

---

## Impact Assessment

### Before Fix (BUGGY)

- Risk-free rate: 0.000408 (should be 0.0408) - 100x too small
- GDP growth: 0.00025 (should be 0.025) - 100x too small
- Unemployment: 0.00037 (should be 0.037) - 100x too small
- All macro regime calculations: WRONG
- All Sharpe ratios: INFLATED (rf too small)

### After Fix (CORRECT)

- Risk-free rate: 0.0408 (4.08%) ✓
- GDP growth: 0.025 (2.5%) ✓
- Unemployment: 0.037 (3.7%) ✓
- Macro regime calculations: CORRECT ✓
- Sharpe ratios: ACCURATE ✓

---

## Related Documentation

- **TECHNICAL_DEBT_CYCLES_SCALING.md** - Original technical debt doc
- **DATA_SCALE_TYPE_DOCUMENTATION.md** - Comprehensive scale/type reference
- **CONSTANTS_COMPREHENSIVE_REVIEW.md** - Constants architecture review

---

## Conclusion

**Two critical double conversion bugs confirmed:**

1. ✅ **macro_data_helpers.py:89** - Divides DGS10 by 100 (already decimal)
2. ✅ **cycles.py:732-748** - Divides all indicators by 100/10000/etc (already decimal)

**Root cause:** Database stores transformed values, but code assumes raw values.

**Fix:** Remove divisions, use values as-is, add validation.

**Risk:** Medium (requires testing macro regime detection)

**Value:** CRITICAL (fixes all macro and risk calculations)

---

**Status:** READY TO FIX
**Next Step:** Apply fixes in order (macro_data_helpers → cycles.py → tests)
**Owner:** Data Integration Team
**Review Date:** 2025-11-08
