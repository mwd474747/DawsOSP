# NoneType Multiplication Error Fix

**Date**: October 15, 2025
**Status**: ✅ Fixed
**Error**: `TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'`
**Root Cause**: Dictionary `.get()` returns None when key exists with None value, causing multiplication errors

---

## Problem

User encountered error when viewing Markets tab:
```
TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'
```

**Location**: Various display methods in `trinity_dashboard_tabs.py`

---

## Root Cause Analysis

### The Misconception

Many developers assume:
```python
value = dict.get('key', 0)  # Always returns 0 if key doesn't exist or is None
```

**This is WRONG!**

### The Reality

```python
# Case 1: Key doesn't exist
data = {'other_key': 123}
value = data.get('missing_key', 0)  # Returns 0 ✅

# Case 2: Key exists with None value
data = {'key': None}
value = data.get('key', 0)  # Returns None ❌ (NOT 0!)

# Case 3: Key exists with 0 value
data = {'key': 0}
value = data.get('key', 0)  # Returns 0 ✅
```

**Key Insight**: `.get(key, default)` returns the default ONLY if the key doesn't exist, NOT if the value is None.

### Why FMP API Returns None

FMP API returns JSON like:
```json
{
  "roe": null,
  "roa": 0.05,
  "debtToEquity": null,
  "revenueGrowth": null
}
```

When parsed:
- `metrics['roe']` = `None` (not missing, but explicitly null)
- `metrics.get('roe', 0)` returns `None` (because key exists!)
- `None * 100` → **TypeError**

---

## Problematic Code Patterns

### Pattern 1: Direct Multiplication
```python
# ❌ WRONG - Crashes if value is None
st.write(f"Dividend Yield: {fundamentals.get('dividendYield', 0)*100:.2f}%")

# When dividendYield is None:
# None * 100 → TypeError
```

### Pattern 2: Direct Division
```python
# ❌ WRONG - Crashes if value is None
st.write(f"Market Cap: ${fundamentals.get('mktCap', 0)/1e9:.2f}B")

# When mktCap is None:
# None / 1000000000 → TypeError
```

### Pattern 3: Formatting Operations
```python
# ❌ WRONG - Crashes if value is None
st.metric("ROE", f"{metrics.get('roe', 0)*100:.2f}%")

# When roe is None:
# None * 100 → TypeError
```

---

## The Fix

### Solution: Use `or` Operator

```python
# ✅ CORRECT - Handles both missing keys AND None values
value = dict.get('key', 0) or 0

# Behavior:
# - Key doesn't exist: .get() returns 0, 0 or 0 → 0
# - Key exists with None: .get() returns None, None or 0 → 0
# - Key exists with 0: .get() returns 0, 0 or 0 → 0
# - Key exists with value: .get() returns value, value or 0 → value
```

**Why This Works**:
- `None or 0` evaluates to `0` (None is falsy)
- `0 or 0` evaluates to `0` (first 0 is falsy, returns second)
- `5 or 0` evaluates to `5` (5 is truthy, returns first)

---

## Fixes Applied

### Fix 1: Fundamentals Display (lines 1176-1189)

**Before**:
```python
st.write(f"**Market Cap:** ${fundamentals.get('mktCap', 0)/1e9:.2f}B")
st.write(f"**P/E Ratio:** {fundamentals.get('pe', 0):.2f}")
st.write(f"**Revenue:** ${fundamentals.get('revenue', 0)/1e9:.2f}B")
st.write(f"**Dividend Yield:** {fundamentals.get('dividendYield', 0)*100:.2f}%")
```

**After**:
```python
mkt_cap = fundamentals.get('mktCap', 0) or 0
pe = fundamentals.get('pe', 0) or 0
revenue = fundamentals.get('revenue', 0) or 0
div_yield = fundamentals.get('dividendYield', 0) or 0

st.write(f"**Market Cap:** ${mkt_cap/1e9:.2f}B")
st.write(f"**P/E Ratio:** {pe:.2f}")
st.write(f"**Revenue:** ${revenue/1e9:.2f}B")
st.write(f"**Dividend Yield:** {div_yield*100:.2f}%")
```

---

### Fix 2: Key Metrics Display (lines 1239-1265)

**Before**:
```python
st.metric("ROE", f"{metrics.get('roe', 0)*100:.2f}%")
st.metric("ROA", f"{metrics.get('roa', 0)*100:.2f}%")
st.metric("Profit Margin", f"{metrics.get('netProfitMargin', 0)*100:.2f}%")
st.metric("Revenue Growth", f"{metrics.get('revenueGrowth', 0)*100:.2f}%")
```

**After**:
```python
roe = (metrics.get('roe') or 0) * 100
roa = (metrics.get('roa') or 0) * 100
profit_margin = (metrics.get('netProfitMargin') or 0) * 100
revenue_growth = (metrics.get('revenueGrowth') or 0) * 100

st.metric("ROE", f"{roe:.2f}%")
st.metric("ROA", f"{roa:.2f}%")
st.metric("Profit Margin", f"{profit_margin:.2f}%")
st.metric("Revenue Growth", f"{revenue_growth:.2f}%")
```

---

### Fix 3: Insider Trading Display (lines 1276-1286)

**Before**:
```python
'Shares': f"{txn.get('securitiesTransacted', 0):,}",
'Value': f"${txn.get('transactionValue', 0)/1000:.0f}K"
```

**After**:
```python
shares = txn.get('securitiesTransacted', 0) or 0
value = txn.get('transactionValue', 0) or 0

'Shares': f"{shares:,}",
'Value': f"${value/1000:.0f}K"
```

---

### Fix 4: Institutional Holdings Display (lines 1297-1307)

**Before**:
```python
'Shares': f"{holder.get('shares', 0):,}",
'Value': f"${holder.get('value', 0)/1e6:.1f}M",
'Change': f"{holder.get('change', 0):+.1f}%"
```

**After**:
```python
shares = holder.get('shares', 0) or 0
value = holder.get('value', 0) or 0
change = holder.get('change', 0) or 0

'Shares': f"{shares:,}",
'Value': f"${value/1e6:.1f}M",
'Change': f"{change:+.1f}%"
```

---

## Files Modified

| File | Lines Changed | Description |
|------|--------------|-------------|
| `dawsos/ui/trinity_dashboard_tabs.py` | 1176-1189 | Fundamentals display |
| `dawsos/ui/trinity_dashboard_tabs.py` | 1239-1265 | Key metrics display |
| `dawsos/ui/trinity_dashboard_tabs.py` | 1276-1286 | Insider trading display |
| `dawsos/ui/trinity_dashboard_tabs.py` | 1297-1307 | Institutional holdings display |

**Total Lines Modified**: ~40 lines across 4 methods

---

## Testing

### Test Case 1: None Values
```python
data = {
    'roe': None,
    'roa': None,
    'revenueGrowth': None
}

# Before: TypeError
# After: All display as 0.00%
```
✅ Passed

### Test Case 2: Zero Values
```python
data = {
    'roe': 0,
    'roa': 0,
    'revenueGrowth': 0
}

# Before: Worked (displayed 0.00%)
# After: Still works (displayed 0.00%)
```
✅ Passed

### Test Case 3: Normal Values
```python
data = {
    'roe': 0.15,
    'roa': 0.08,
    'revenueGrowth': 0.12
}

# Before: Worked (displayed 15.00%, 8.00%, 12.00%)
# After: Still works (displayed 15.00%, 8.00%, 12.00%)
```
✅ Passed

### Test Case 4: Missing Keys
```python
data = {
    'other_key': 123
}

# Before: Worked (displayed 0.00% for missing keys)
# After: Still works (displayed 0.00% for missing keys)
```
✅ Passed

---

## Prevention Guidelines

### Best Practice Pattern

**Always use the `or 0` pattern when performing arithmetic operations**:

```python
# ✅ SAFE PATTERN
value = data.get('key', 0) or 0
result = value * 100

# ✅ SAFE PATTERN (inline)
result = (data.get('key') or 0) * 100

# ❌ UNSAFE PATTERN
result = data.get('key', 0) * 100  # Crashes if key exists with None value
```

### When to Use This Pattern

Use `or 0` when:
1. ✅ Multiplying or dividing dictionary values
2. ✅ Formatting numeric values
3. ✅ Performing any math operations
4. ✅ API responses might contain null/None

Don't need `or 0` when:
1. ❌ Just displaying string values
2. ❌ Checking boolean existence (`if value:`)
3. ❌ Values are guaranteed non-None by validation

### Alternative: Explicit None Check

For complex logic, use explicit None checks:

```python
# Alternative approach
value = data.get('key')
if value is None:
    value = 0

result = value * 100
```

This is more verbose but clearer for complex cases.

---

## Impact

### Before Fix:
- ❌ Markets tab crashed when viewing stocks with incomplete data
- ❌ User experience: Red error screen
- ❌ No way to proceed without refreshing

### After Fix:
- ✅ Markets tab handles missing/None data gracefully
- ✅ Displays 0 or 0.00% for missing metrics
- ✅ User can continue browsing without errors

---

## Related Fixes

This fix is part of a series of Markets tab improvements:
1. [YTD_MTD_CALCULATION_FIX.md](YTD_MTD_CALCULATION_FIX.md) - Fixed 0% returns
2. [SECTOR_CORRELATIONS_AUTO_LOAD_FIX.md](SECTOR_CORRELATIONS_AUTO_LOAD_FIX.md) - Auto-load sectors
3. [MARKETS_TAB_FIXES_OCT_15.md](MARKETS_TAB_FIXES_OCT_15.md) - DataFrame boolean check
4. **NONE_TYPE_MULTIPLICATION_FIX.md** - This fix (NoneType errors)

---

## Lessons Learned

### Python Gotcha: `.get()` Default Value

The `.get(key, default)` method only returns the default if:
- ✅ The key doesn't exist

It does NOT return the default if:
- ❌ The key exists with a None value
- ❌ The key exists with an empty string
- ❌ The key exists with an empty list/dict

**Solution**: Always use `or` operator for arithmetic operations:
```python
value = data.get('key', 0) or 0  # Handles both cases
```

---

## Summary

✅ **Fixed NoneType multiplication errors** across 4 display methods
✅ **40 lines modified** to handle None values gracefully
✅ **All test cases passed** (None, 0, normal, missing)
✅ **Best practice pattern** documented for future development

**Status**: Production-ready. Markets tab now handles incomplete FMP API data without crashing.

---

**Deployment**: Changes applied. Restart Streamlit to see the fix.

```bash
pkill -f streamlit && sleep 3 && ./start.sh
```
