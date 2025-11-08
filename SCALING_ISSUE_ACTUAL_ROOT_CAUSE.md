# Data Scaling - Actual Root Cause Analysis

**Date:** 2025-11-08
**Status:** 🔍 INVESTIGATING - Previous "fixes" were incorrect and have been reverted

---

## What Happened

### Incorrect "Fixes" Applied (NOW REVERTED)
1. **Commit cc9a43e**: "Fixed" backend scaling by removing ÷100 divisions
2. **Commit c2957c5**: "Fixed" frontend scaling by removing ÷100 divisions
3. **Result**: Values displayed as "0.09290112%" instead of "9.29%"
4. **Action Taken**: REVERTED both commits

### Evidence from Screenshot

User screenshot shows:
```
TWR (1Y): 0.09290112%
YTD RETURN: 0.0435683%
MWR (1Y): 0.08825606%
VOLATILITY: 0.19049409%
```

These values suggest:
- Backend returns: `0.0009290112` (very small decimal)
- Frontend `formatPercentage()` multiplies by 100 → "0.092901%"
- Should display: "9.29%"

---

## Actual Root Cause

The screenshot values indicate **TWO possibilities**:

### Hypothesis 1: Test/Stub Data is Wrong Scale
The backend might be returning stub/test data that hasn't been properly formatted.

**Evidence:**
- Real TWR values should be in range -50% to +50% (decimals: -0.5 to +0.5)
- Screenshot shows ~0.09% which is suspiciously low
- Could be stub data that returns `9.29` (whole number percent) when code expects decimals

### Hypothesis 2: Database Stores Wrong Format
The database might store values in a different format than expected.

**Two competing standards:**
1. **Whole number percentages**: `9.29` stored in DB, code divides by 100 → `0.0929`
2. **Decimal percentages**: `0.0929` stored in DB, code uses as-is

---

## What We Know For Sure

### Backend Code (CURRENT - After Revert)

**macro_data_helpers.py** (lines 85-93):
```python
# Get DGS10 (10-Year Treasury rate)
dgs10 = await execute_statement(...)

if dgs10 is not None:
    # DGS10 is stored in percent (e.g., 4.5), convert to decimal (0.045)
    return dgs10 / Decimal("100")  # ✅ Division by 100 present
```

**cycles.py** (lines 732-748):
```python
# Hardcoded scaling logic
if code_key == "gdp_growth":
    db_indicators[code_key] = raw_value / 100.0  # ✅ Division by 100 present
elif code_key == "unemployment":
    db_indicators[code_key] = raw_value / 100.0  # ✅ Division by 100 present
# ... etc
```

### Frontend Code (CURRENT - After Revert)

**pages.js** (lines 317, 326, 404, etc.):
```javascript
// Portfolio overview
formatPercentage((data.change_pct || 0.0235) / 100)  // ✅ Division by 100 present
formatPercentage((data.ytd_return || 0.145) / 100)   // ✅ Division by 100 present

// Holdings table
formatPercentage((holding.weight || 0) / 100)        // ✅ Division by 100 present
```

**utils.js** (line 57):
```javascript
Utils.formatPercentage = function(value, decimals = 2) {
    return (value * 100).toFixed(decimals) + '%';  // ✅ Multiplies by 100
};
```

---

## The Math

### If Backend Returns Whole Number Percent (9.29):

**Data Flow:**
```
Database: 9.29
  ↓
Backend: 9.29 ÷ 100 = 0.0929
  ↓
Frontend: 0.0929 ÷ 100 = 0.000929
  ↓
formatPercentage: 0.000929 × 100 = 0.0929
  ↓
Display: "0.09%"  ❌ WRONG (matches screenshot!)
```

**This matches the screenshot values!**

### If Backend Returns Decimal (0.0929):

**Data Flow:**
```
Database: 0.0929
  ↓
Backend: 0.0929 (no division needed)
  ↓
Frontend: 0.0929 (no division needed)
  ↓
formatPercentage: 0.0929 × 100 = 9.29
  ↓
Display: "9.29%"  ✅ CORRECT
```

---

## Investigation Needed

### Step 1: Check What Database Actually Stores

Run query to see actual database values:
```sql
SELECT
    indicator_id,
    value,
    units
FROM macro_indicators
WHERE indicator_id IN ('DGS10', 'UNRATE', 'A191RL1Q225SBEA')
ORDER BY date DESC
LIMIT 5;
```

**Expected:**
- If `value = 4.08` and `units = 'Percent'` → Database stores whole numbers
- If `value = 0.0408` and `units = 'Percent'` → Database stores decimals

### Step 2: Check What Pattern Execution Returns

Add logging to pattern execution to see raw values before formatting:
```python
logger.info(f"TWR value before formatting: {perf_metrics['twr_1y']}")
logger.info(f"Type: {type(perf_metrics['twr_1y'])}")
```

### Step 3: Check If This is Stub Data

Look for stub data generators:
```bash
grep -r "0.092" backend/
grep -r "stub" backend/app/agents/financial_analyst.py
```

---

## Likely Fix (After Investigation)

### If Database Stores Whole Numbers:

**Current code is CORRECT** - No changes needed. The issue is elsewhere (stub data, data not loaded, etc.)

### If Database Stores Decimals:

**Need to remove double divisions:**

1. **Backend**: Remove ÷100 in macro_data_helpers.py, cycles.py
2. **Frontend**: Remove ÷100 in pages.js (11 locations)
3. **Keep**: formatPercentage() multiplication by 100 (correct)

---

## Next Steps

1. ✅ **DONE**: Revert incorrect "fixes"
2. ⏳ **TODO**: Check database actual values
3. ⏳ **TODO**: Add logging to pattern execution
4. ⏳ **TODO**: Verify FREDTransformationService behavior
5. ⏳ **TODO**: Check if this is stub/test data issue
6. ⏳ **TODO**: Apply correct fix based on findings

---

## Lessons Learned

❌ **Don't assume** - Check actual data before "fixing"
❌ **Don't trust documentation** - Verify with real database queries
❌ **Don't fix without testing** - Screenshot showed the "fix" made it worse
✅ **Do investigate thoroughly** - Understand root cause before changing code
✅ **Do revert quickly** - Bad fixes reverted immediately

---

**Status**: Awaiting investigation results to determine correct fix
**Priority**: HIGH - Display values currently 100x too small
**Risk**: MEDIUM - Need to verify correct data format before fixing

