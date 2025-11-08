# Technical Debt: cycles.py Hardcoded Scaling Conflict

**Issue ID**: TD-CYCLES-001
**Severity**: HIGH (Data Integrity Risk)
**Date Identified**: 2025-11-07
**Estimated Fix Time**: 30 minutes
**Risk**: Double-conversion or inconsistent scaling leading to incorrect macro regime detection

---

## Problem Description

`backend/app/services/cycles.py` (lines 729-745) contains hardcoded scaling logic that duplicates and conflicts with the centralized `FREDTransformationService`.

### Current Code (PROBLEMATIC)

```python
# File: backend/app/services/cycles.py, lines 729-745
if code_key == "inflation":
    db_indicators[code_key] = raw_value / 10000.0      # ❌ Why 10000? Should be 100
elif code_key == "gdp_growth":
    db_indicators[code_key] = raw_value / 100.0        # ⚠️ Duplicate logic
elif code_key == "unemployment":
    db_indicators[code_key] = raw_value / 100.0
elif code_key == "interest_rate":
    db_indicators[code_key] = raw_value / 100.0
elif code_key == "credit_growth":
    db_indicators[code_key] = raw_value / 1000000.0    # ❌ Suspiciously large divisor
elif code_key == "debt_service_ratio":
    db_indicators[code_key] = raw_value / 10000000.0   # ❌ Extremely large divisor
```

### Issues

1. **Inconsistent Divisors**:
   - Inflation uses ÷10000 (why not ÷100 like others?)
   - Credit growth uses ÷1000000 (suspicious)
   - Debt service ratio uses ÷10000000 (extremely suspicious)

2. **Duplicate Logic**:
   - `fred_transformation.py` already handles FRED percentage conversion
   - Having two scaling systems creates risk of:
     - Double conversion (value ÷ 100 then ÷ 100 again = 10000x error)
     - Inconsistent scaling across services

3. **No Documentation**:
   - No comments explaining why each divisor is different
   - No reference to FRED API documentation
   - Unclear if these are correct or legacy bugs

4. **Risk of Data Corruption**:
   - If FRED data already transformed by `FREDTransformationService`, cycles.py will divide again
   - Could corrupt macro regime detection calculations

---

## Impact Analysis

### Affected Functionality

- **Macro Regime Detection**: Primary use case for cycles.py
- **Economic Indicators Dashboard**: May display incorrect values
- **Scenario Analysis**: If using macro regime as input

### Data Integrity Risk

**Scenario 1: Double Conversion**
```
FRED API: DGS10 = 4.5 (means 4.5%)
→ FREDTransformationService: 4.5 ÷ 100 = 0.045 (correct)
→ cycles.py: 0.045 ÷ 100 = 0.00045 (WRONG! 100x too small)
```

**Scenario 2: Inconsistent Scaling**
```
Inflation from FRED: 3.2 (means 3.2%)
→ cycles.py: 3.2 ÷ 10000 = 0.00032 (WRONG! Should be 0.032)
→ Expected: 3.2 ÷ 100 = 0.032 (correct)
```

### Business Impact

- **LOW if transformation service is used exclusively**
- **HIGH if cycles.py receives raw FRED data**
- **CRITICAL if both are used inconsistently**

---

## Root Cause Analysis

### Why This Exists

1. **Legacy Code**: Likely pre-dates `FREDTransformationService` (created 2024-10-14)
2. **Feature Isolation**: cycles.py may have been developed independently
3. **Lack of Centralization**: No single source of truth for FRED conversions

### Why It Persists

1. **No Integration Tests**: No tests comparing cycles.py vs fred_transformation.py output
2. **No Documentation**: Scaling rationale never documented
3. **Works "Good Enough"**: May be using pre-transformed data by accident

---

## Recommended Solution

### Short-term Fix (30 minutes)

**Step 1**: Delete hardcoded scaling logic

```python
# DELETE lines 729-745 from cycles.py
```

**Step 2**: Use centralized transformation service

```python
# ADD after line 728
from app.services.fred_transformation import get_transformation_service

transformation_service = get_transformation_service()

# In the row processing loop:
for row in rows:
    db_name = row["indicator_id"]
    if db_name in name_mapping:
        code_key = name_mapping[db_name]
        raw_value = float(row["value"])

        # Use centralized transformation (handles all FRED series correctly)
        transformed_value = transformation_service.transform_fred_value(
            series_id=db_name,
            value=raw_value,
            date_str=str(row["date"]),
            historical_values=historical_data.get(db_name, [])
        )

        # Use transformed value if available, otherwise raw
        db_indicators[code_key] = transformed_value if transformed_value is not None else raw_value
```

**Step 3**: Add integration test

```python
# File: backend/tests/services/test_cycles_transformation.py

async def test_cycles_transformation_matches_fred_service():
    """
    Ensure cycles.py uses same transformation logic as FREDTransformationService.

    Regression test for TD-CYCLES-001.
    """
    from app.services.cycles import CyclesService
    from app.services.fred_transformation import get_transformation_service

    cycles_svc = CyclesService()
    transform_svc = get_transformation_service()

    # Test data: FRED returns DGS10 = 4.5 (means 4.5%)
    test_date = date(2025, 11, 7)
    test_series = "DGS10"
    test_value = 4.5

    # Get transformation from service
    service_result = transform_svc.transform_fred_value(
        series_id=test_series,
        value=test_value,
        date_str=test_date.isoformat()
    )

    # Get value from cycles.py (after fix)
    # ... call cycles.py method that uses transformation ...

    # Should match (both should be 0.045)
    assert cycles_result == service_result, \
        f"Cycles transformation ({cycles_result}) doesn't match service ({service_result})"
```

### Long-term Solution (2 hours)

**Centralized Conversion Utilities**

Create `backend/app/core/utils/conversions.py` (see DATA_SCALE_TYPE_DOCUMENTATION.md):
- `percent_to_decimal()`
- `bps_to_decimal()`
- Type-safe conversion functions

**Benefits**:
- Single source of truth for all conversions
- Testable in isolation
- Self-documenting code

---

## Testing Strategy

### Before Fix

1. **Capture Current Behavior**:
   ```python
   # Run cycles.py with current code
   # Save output to baseline file
   regime = await cycles_svc.detect_regime(date(2025, 11, 7))
   with open("baseline_regime.json", "w") as f:
       json.dump(regime, f)
   ```

2. **Document Suspicious Values**:
   - Check if inflation values are ~100x too small
   - Check if credit_growth/debt_service_ratio are realistic

### After Fix

3. **Compare Outputs**:
   ```python
   # Run cycles.py with new code
   new_regime = await cycles_svc.detect_regime(date(2025, 11, 7))

   # Compare
   assert new_regime["regime"] == baseline["regime"], \
       "Regime classification changed after fix - investigate"
   ```

4. **Validate Against Known Data**:
   ```python
   # DGS10 on 2025-11-07 should be ~4.08%
   transformed = transform_svc.transform_fred_value("DGS10", 4.08, "2025-11-07")
   assert 0.04 <= transformed <= 0.05, "DGS10 transformation incorrect"
   ```

---

## Rollback Plan

If fix causes issues:

1. **Revert commit**: `git revert <commit-hash>`
2. **Restore hardcoded scaling**: Keep for now, add TODO comment
3. **Investigate discrepancy**: Why did outputs differ?

**Rollback triggers**:
- Regime detection tests fail
- Macro dashboard shows unrealistic values
- Integration tests reveal data corruption

---

## Implementation Checklist

- [ ] Review current cycles.py scaling logic (lines 729-745)
- [ ] Verify FREDTransformationService handles all series used by cycles.py
- [ ] Create baseline output file (before fix)
- [ ] Delete hardcoded scaling (lines 729-745)
- [ ] Add transformation service import
- [ ] Update row processing to use transformation service
- [ ] Run existing unit tests
- [ ] Create integration test comparing outputs
- [ ] Compare new output vs baseline
- [ ] Update DATA_SCALE_TYPE_DOCUMENTATION.md with resolution
- [ ] Commit with message: "fix(cycles): Remove hardcoded scaling, use FREDTransformationService"

---

## Related Issues

- **DATA_SCALE_TYPE_DOCUMENTATION.md**: Comprehensive scale/type reference
- **FRED_SCALING_DOCUMENTATION.md**: FRED-specific transformation rules
- **fred_transformation.py**: Centralized transformation service
- **Constants Phase 4.1**: Scale/type analysis that identified this issue

---

## Decision: Defer to Future Sprint

**Status**: IDENTIFIED BUT NOT FIXED
**Reason**: Requires careful testing to avoid breaking macro regime detection
**Priority**: HIGH but not blocking current work
**Target**: Next macro/cycles service refactoring sprint

**Action**: Document in backlog, add TODO comment to cycles.py

```python
# File: backend/app/services/cycles.py, line 729
# TODO (TD-CYCLES-001): Remove hardcoded scaling, use FREDTransformationService
# See: /Users/mdawson/Documents/GitHub/DawsOSP/TECHNICAL_DEBT_CYCLES_SCALING.md
# Risk: Duplicate/inconsistent scaling with fred_transformation.py
# Fix: DELETE lines 729-745, use transformation_service.transform_fred_value()
```

---

**Last Updated**: 2025-11-07
**Owner**: Data Integration Team
**Reviewer**: Macro Services Team
