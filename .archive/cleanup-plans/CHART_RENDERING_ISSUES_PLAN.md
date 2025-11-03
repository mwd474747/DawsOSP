# Chart Rendering Issues - Diagnostic Plan

**Date:** November 2, 2025  
**Purpose:** Identify potential issues preventing portfolio over time and sector allocation charts from rendering  
**Status:** 📋 DIAGNOSTIC PLAN ONLY (No Code Changes)

---

## 📊 Executive Summary

Charts not rendering despite everything being "wired correctly." This document identifies **potential data structure mismatches** and **formatting issues** that could prevent Chart.js from rendering.

---

## 🔍 Issue 1: Historical NAV Line Chart

### Expected Flow

**Backend Returns (`portfolio_historical_nav`):**
```python
{
    "historical_nav": [
        {"date": "2025-09-21", "value": 92000.00},
        {"date": "2025-09-22", "value": 92500.00},
        ...
    ],
    "data_points": 30,
    "lookback_days": 30,
    ...
}
```

**UI dataPath:** `'historical_nav'` (full_ui.html:2859)

**PatternRenderer Data Extraction:**
```javascript
data = getDataByPath(data, 'historical_nav')
// Returns: [{date: "2025-09-21", value: 92000.00}, ...]
```

**LineChartPanel Receives:**
```javascript
data = [{date: "2025-09-21", value: 92000.00}, ...]  // Array directly
```

**LineChartPanel Data Extraction (full_ui.html:3456-3459):**
```javascript
labels: data.labels || (data.data ? data.data.map(d => d.date || d.x) : []),
data: data.values || (data.data ? data.data.map(d => d.value || d.y) : []),
```

### 🔴 CRITICAL ISSUE IDENTIFIED

**Problem:** LineChartPanel expects data in one of these formats:
1. `{labels: [...], values: [...]}`
2. `{data: [{date, value}, ...]}`

**But receives:** `[{date, value}, ...]` (array directly)

**Impact:**
- `data.labels` = `undefined` ❌
- `data.data` = `undefined` ❌ (it's `data` itself, not `data.data`)
- `data.data.map(...)` = **CRASH** or empty array
- Result: **No labels, no data points → Chart doesn't render**

---

## 🔍 Issue 2: Sector Allocation Pie Chart

### Expected Flow

**Backend Returns (`portfolio_sector_allocation`):**
```python
{
    "sector_allocation": {
        "Technology": 35.5,
        "Healthcare": 22.3,
        "Financial Services": 18.7,
        ...
    },
    "total_sectors": 6,
    "total_value": 95679.00,
    ...
}
```

**UI dataPath:** `'sector_allocation'` (full_ui.html:2871)

**PatternRenderer Data Extraction:**
```javascript
data = getDataByPath(data, 'sector_allocation')
// Returns: {Technology: 35.5, Healthcare: 22.3, ...}
```

**PieChartPanel Receives:**
```javascript
data = {Technology: 35.5, Healthcare: 22.3, ...}  // Object directly
```

**PieChartPanel Data Extraction (full_ui.html:3724-3725):**
```javascript
const labels = Object.keys(data);
const values = Object.values(data);
```

### ✅ This Should Work

**Analysis:**
- PieChartPanel expects: Object with keys as labels, values as data
- Receives: `{Technology: 35.5, Healthcare: 22.3, ...}`
- `Object.keys(data)` = `["Technology", "Healthcare", ...]` ✅
- `Object.values(data)` = `[35.5, 22.3, ...]` ✅
- **BUT:** What if `data` is empty object `{}`?
- **OR:** What if `data` is `null` or `undefined`?

---

## 🔍 Potential Root Causes

### Root Cause 1: Data Structure Mismatch (Historical NAV)

**Location:** `full_ui.html:3456-3459` (LineChartPanel)

**Issue:**
```javascript
// LineChartPanel expects:
data.labels  // or
data.data    // array of {date, value} objects

// But receives:
[{date, value}, ...]  // array directly

// So:
data.labels = undefined  ❌
data.data = undefined    ❌ (data IS the array, not data.data)
```

**Fix Required:**
- LineChartPanel should handle case where `data` is an array directly
- OR: Backend should wrap array in object: `{data: [{date, value}, ...]}`

---

### Root Cause 2: Empty Data Arrays/Objects

**Scenario 1: Empty Historical NAV**
- Backend returns: `{historical_nav: [], data_points: 0}`
- `getDataByPath` returns: `[]`
- LineChartPanel receives: `[]`
- `data.data.map(...)` = `undefined.map(...)` → **CRASH**

**Scenario 2: Empty Sector Allocation**
- Backend returns: `{sector_allocation: {}, total_sectors: 0}`
- `getDataByPath` returns: `{}`
- PieChartPanel receives: `{}`
- `Object.keys({})` = `[]` → Chart renders with no data

---

### Root Cause 3: Null/Undefined Data

**Scenario: Historical NAV Missing from Response**
- Pattern doesn't return `historical_nav` key
- `getDataByPath(data, 'historical_nav')` returns: `null` or `undefined`
- LineChartPanel receives: `null`
- Line 3445: `if (!data || !chartRef.current) return;` → **Returns null, no chart rendered**

**Scenario: Sector Allocation Missing**
- Pattern doesn't return `sector_allocation` key
- `getDataByPath(data, 'sector_allocation')` returns: `null`
- PieChartPanel receives: `null`
- Line 3715: `if (!data || !chartRef.current) return;` → **Returns null, no chart rendered**

---

### Root Cause 4: Chart.js Initialization Timing

**Issue:** Chart.js may not initialize if:
- Canvas ref is not ready when `useEffect` runs
- Chart instance destroyed before render completes
- Multiple rapid re-renders causing chart destruction

**Location:** `full_ui.html:3444-3514` (LineChartPanel useEffect)

**Potential Problem:**
```javascript
useEffect(() => {
    if (!data || !chartRef.current) return;  // Early return if ref not ready
    
    // ... chart creation
}, [data]);  // Only depends on data, not chartRef
```

**Issue:** If `chartRef.current` is `null` when `data` updates, chart won't initialize.

---

### Root Cause 5: Pattern Response Structure

**Potential Issue:** Pattern orchestrator may wrap output in nested structure

**Expected:**
```json
{
  "data": {
    "historical_nav": [...],
    "sector_allocation": {...}
  }
}
```

**But PatternRenderer extracts:**
```javascript
setData(result.data || result);  // Line 3270
```

**If pattern returns:**
```json
{
  "historical_nav": {
    "data_points": [...],
    "lookback_days": 30
  }
}
```

**Then `getDataByPath(data, 'historical_nav')` returns:**
```json
{
  "data_points": [...],
  "lookback_days": 30
}
```

**Not:** `[...]` (array)

---

## 🔍 Detailed Analysis: Historical NAV Chart

### Backend Output Structure

**Function:** `portfolio_historical_nav()` (financial_analyst.py:2039-2046)
```python
result = {
    "historical_nav": historical_data,  # Array: [{date, value}, ...]
    "lookback_days": lookback_days,
    "start_date": ...,
    "end_date": ...,
    "total_return_pct": ...,
    "data_points": len(historical_data),
}
```

**Pattern Output:**
- Step stores as: `"as": "historical_nav"`
- PatternOrchestrator aggregates into final response
- Final response: `{historical_nav: {...}}` (the entire result object)

### UI Data Extraction

**PatternRenderer (full_ui.html:3270):**
```javascript
setData(result.data || result);
```

**PanelRenderer (full_ui.html:3308):**
```javascript
data: getDataByPath(data, panel.dataPath)
// For historical_nav: getDataByPath(data, 'historical_nav')
```

**getDataByPath (full_ui.html:3207-3222):**
```javascript
function getDataByPath(data, path) {
    if (!path || !data) return data;
    
    const parts = path.split('.');
    let current = data;
    
    for (const part of parts) {
        if (current && typeof current === 'object') {
            current = current[part];
        } else {
            return null;
        }
    }
    
    return current;
}
```

**Expected Flow:**
1. Pattern returns: `{data: {historical_nav: {historical_nav: [...], ...}}}`
2. PatternRenderer sets: `data = {historical_nav: {historical_nav: [...], ...}}`
3. `getDataByPath(data, 'historical_nav')` returns: `{historical_nav: [...], lookback_days: 30, ...}`
4. LineChartPanel receives: `{historical_nav: [...], ...}` (object, not array)

**LineChartPanel Extraction (full_ui.html:3456-3459):**
```javascript
labels: data.labels || (data.data ? data.data.map(d => d.date || d.x) : []),
data: data.values || (data.data ? data.data.map(d => d.value || d.y) : []),
```

**Problem:**
- `data.labels` = `undefined` ❌
- `data.data` = `undefined` ❌ (the array is at `data.historical_nav`, not `data.data`)
- **Result: Empty arrays → Chart doesn't render**

---

## 🔍 Detailed Analysis: Sector Allocation Chart

### Backend Output Structure

**Function:** `portfolio_sector_allocation()` (financial_analyst.py:1944-1949)
```python
result = {
    "sector_allocation": sector_allocation,  # Dict: {Technology: 35.5, ...}
    "total_sectors": len(sector_allocation),
    "total_value": float(total_value),
    "currency": ctx.base_currency or "USD",
}
```

### UI Data Extraction

**Expected Flow:**
1. Pattern returns: `{data: {sector_allocation: {sector_allocation: {...}, ...}}}`
2. PatternRenderer sets: `data = {sector_allocation: {sector_allocation: {...}, ...}}`
3. `getDataByPath(data, 'sector_allocation')` returns: `{sector_allocation: {...}, total_sectors: 6, ...}`
4. PieChartPanel receives: `{sector_allocation: {...}, ...}` (object)

**PieChartPanel Extraction (full_ui.html:3724-3725):**
```javascript
const labels = Object.keys(data);
const values = Object.values(data);
```

**Problem:**
- `Object.keys(data)` = `["sector_allocation", "total_sectors", "total_value", "currency"]` ❌
- `Object.values(data)` = `[{Technology: 35.5, ...}, 6, 95679.00, "USD"]` ❌
- **Result: Chart tries to render with wrong labels/values → Chart displays incorrectly or doesn't render**

---

## 🎯 Root Cause Summary

### Issue 1: Historical NAV Chart

**Root Cause:** **Data Structure Mismatch**
- Backend returns: `{historical_nav: [{date, value}, ...], ...}` (object with array property)
- UI extracts: `getDataByPath(data, 'historical_nav')` → Returns object, not array
- LineChartPanel expects: `{data: [...]}` or `{labels: [...], values: [...]}`
- But receives: `{historical_nav: [...], ...}` (wrong property name)

**Fix Required:**
1. LineChartPanel should check for `data.historical_nav` if `data.data` doesn't exist
2. OR: Backend should return `{data_points: [{date, value}, ...]}` instead of `{historical_nav: [...]}`
3. OR: UI dataPath should be `'historical_nav.historical_nav'` (if pattern wraps it)

---

### Issue 2: Sector Allocation Chart

**Root Cause:** **Wrong Property Extraction**
- Backend returns: `{sector_allocation: {...}, total_sectors: 6, ...}` (object with nested object)
- UI extracts: `getDataByPath(data, 'sector_allocation')` → Returns object with `sector_allocation` property
- PieChartPanel expects: Flat object `{Technology: 35.5, Healthcare: 22.3, ...}`
- But receives: `{sector_allocation: {...}, total_sectors: 6, ...}` (nested object)

**Fix Required:**
1. PieChartPanel should check for `data.sector_allocation` if `data` has nested structure
2. OR: UI dataPath should be `'sector_allocation.sector_allocation'` (if pattern wraps it)
3. OR: Backend should return just `{Technology: 35.5, ...}` as top-level (but pattern stores as `sector_allocation`)

---

## 📋 Diagnostic Checklist

### To Verify Historical NAV Issue:

1. **Check Browser Console:**
   - Look for JavaScript errors related to `.map()` or Chart.js
   - Check if `data.data.map` throws error

2. **Check Network Response:**
   - Inspect `/api/patterns/execute` response
   - Verify `historical_nav` structure in response

3. **Add Debug Logging:**
   ```javascript
   // In LineChartPanel, before chart creation:
   console.log('LineChartPanel received data:', data);
   console.log('data.labels:', data.labels);
   console.log('data.data:', data.data);
   console.log('data.historical_nav:', data.historical_nav);
   ```

4. **Check dataPath Resolution:**
   - Verify `getDataByPath(data, 'historical_nav')` returns what LineChartPanel expects

---

### To Verify Sector Allocation Issue:

1. **Check Browser Console:**
   - Look for Chart.js errors
   - Check if `Object.keys(data)` returns unexpected values

2. **Check Network Response:**
   - Inspect `/api/patterns/execute` response
   - Verify `sector_allocation` structure in response

3. **Add Debug Logging:**
   ```javascript
   // In PieChartPanel, before chart creation:
   console.log('PieChartPanel received data:', data);
   console.log('Object.keys(data):', Object.keys(data));
   console.log('Object.values(data):', Object.values(data));
   console.log('data.sector_allocation:', data.sector_allocation);
   ```

4. **Check dataPath Resolution:**
   - Verify `getDataByPath(data, 'sector_allocation')` returns what PieChartPanel expects

---

## 🔍 Most Likely Issues (Ranked)

### 🔴 Issue #1: Historical NAV Data Structure Mismatch (HIGH PROBABILITY)

**Problem:**
- Backend returns: `{historical_nav: [{date, value}, ...], data_points: 30, ...}`
- UI extracts: `getDataByPath(data, 'historical_nav')` → `{historical_nav: [...], ...}`
- LineChartPanel expects: `{data: [...]}` or `{labels: [...], values: [...]}`
- Receives: `{historical_nav: [...], ...}`

**Fix:**
- LineChartPanel should handle: `data.historical_nav` or `data.data_points`
- OR: Check if `data` is array directly: `Array.isArray(data) ? data : data.data`

---

### 🔴 Issue #2: Sector Allocation Nested Object (HIGH PROBABILITY)

**Problem:**
- Backend returns: `{sector_allocation: {...}, total_sectors: 6, ...}`
- UI extracts: `getDataByPath(data, 'sector_allocation')` → `{sector_allocation: {...}, ...}`
- PieChartPanel expects: `{Technology: 35.5, Healthcare: 22.3, ...}`
- Receives: `{sector_allocation: {...}, total_sectors: 6, ...}`

**Fix:**
- PieChartPanel should check: `data.sector_allocation` if `data.sector_allocation` exists
- OR: UI dataPath should be: `'sector_allocation.sector_allocation'`

---

### 🟡 Issue #3: Empty Data Arrays/Objects (MEDIUM PROBABILITY)

**Problem:**
- Backend returns empty arrays/objects if no data
- Charts receive: `[]` or `{}`
- Chart.js may not render or may crash

**Fix:**
- Add checks for empty data
- Show "No data available" message instead of chart

---

### 🟡 Issue #4: Chart.js Canvas Ref Timing (LOW PROBABILITY)

**Problem:**
- Canvas ref may not be ready when `useEffect` runs
- Chart initialization skipped

**Fix:**
- Add ref check or delay chart creation
- Use `useLayoutEffect` instead of `useEffect`

---

### 🟢 Issue #5: Missing Chart.js Library (LOW PROBABILITY)

**Problem:**
- Chart.js not loaded
- `new Chart()` throws error

**Fix:**
- Verify Chart.js script tag in HTML
- Check for Chart.js CDN or local file

---

## 📋 Verification Steps (No Code Changes)

### Step 1: Inspect Network Response

**Action:**
1. Open browser DevTools → Network tab
2. Filter for `/api/patterns/execute`
3. Click request → Response tab
4. Search for `historical_nav` and `sector_allocation`

**Expected Structure:**
```json
{
  "status": "success",
  "data": {
    "historical_nav": {
      "historical_nav": [{date, value}, ...],
      "data_points": 30,
      ...
    },
    "sector_allocation": {
      "sector_allocation": {Technology: 35.5, ...},
      "total_sectors": 6,
      ...
    }
  }
}
```

---

### Step 2: Check Browser Console

**Action:**
1. Open browser DevTools → Console tab
2. Look for errors related to:
   - `.map()` calls
   - Chart.js initialization
   - `undefined` property access

**Common Errors:**
- `Cannot read property 'map' of undefined`
- `Chart is not a constructor`
- `Cannot read property 'current' of null`

---

### Step 3: Verify DataPath Resolution

**Action:**
1. Add temporary console.log in `PatternRenderer`:
   ```javascript
   // After line 3308:
   console.log('Panel:', panel.id, 'dataPath:', panel.dataPath);
   console.log('Extracted data:', getDataByPath(data, panel.dataPath));
   ```

2. Check console output for:
   - `historical_nav` → What structure is returned?
   - `sector_allocation` → What structure is returned?

---

### Step 4: Verify Chart Component Receives Data

**Action:**
1. Add temporary console.log in `LineChartPanel`:
   ```javascript
   // Line 3445, before early return:
   console.log('LineChartPanel - data:', data);
   console.log('LineChartPanel - data.data:', data.data);
   console.log('LineChartPanel - data.historical_nav:', data.historical_nav);
   ```

2. Add temporary console.log in `PieChartPanel`:
   ```javascript
   // Line 3715, before early return:
   console.log('PieChartPanel - data:', data);
   console.log('PieChartPanel - data.sector_allocation:', data.sector_allocation);
   console.log('PieChartPanel - Object.keys(data):', Object.keys(data));
   ```

---

## 🎯 Most Likely Root Cause

**Based on analysis:**

### Issue #1: Historical NAV Chart
**Most Likely:** Data structure mismatch
- Backend returns object with `historical_nav` property containing array
- UI extracts object, but LineChartPanel expects array or object with `data` property
- **Fix:** LineChartPanel should check `data.historical_nav` if `data.data` doesn't exist

### Issue #2: Sector Allocation Chart
**Most Likely:** Nested object extraction
- Backend returns object with `sector_allocation` property containing object
- UI extracts outer object, but PieChartPanel expects inner object directly
- **Fix:** PieChartPanel should check `data.sector_allocation` if `data` has nested structure

---

## 📋 Recommended Diagnostic Actions

### Immediate Actions (No Code Changes):

1. **Check Network Tab:**
   - Inspect actual response structure from `/api/patterns/execute`
   - Verify `historical_nav` and `sector_allocation` structures

2. **Check Browser Console:**
   - Look for JavaScript errors
   - Check for Chart.js errors

3. **Add Temporary Debug Logging:**
   - Log data received by LineChartPanel
   - Log data received by PieChartPanel
   - Log dataPath resolution results

4. **Verify Chart.js Loaded:**
   - Check if `Chart` global variable exists
   - Check for Chart.js script tag errors

---

## 🔍 Alternative Potential Issues

### Issue A: Canvas Element Not Rendering

**Problem:**
- Chart container renders but canvas doesn't appear
- CSS `height: 400px` may not be applied
- Container may have `display: none` or `visibility: hidden`

**Check:**
- Inspect DOM for canvas element
- Check computed styles for chart-container

---

### Issue B: Chart.js Version Mismatch

**Problem:**
- Chart.js v4.x API may differ from what code expects
- `new Chart(ctx, {...})` may require different options structure

**Check:**
- Verify Chart.js version loaded
- Check Chart.js documentation for API changes

---

### Issue C: Empty Data Silently Failing

**Problem:**
- Backend returns empty arrays/objects
- Charts receive empty data but don't show error
- Just render nothing (no visual indication)

**Check:**
- Verify data contains actual values
- Check if arrays/objects are empty

---

## 📋 Summary

### Most Likely Issues (Ranked by Probability):

1. **🔴 Data Structure Mismatch - Historical NAV**
   - Backend returns `{historical_nav: [...]}`
   - LineChartPanel expects `{data: [...]}`
   - **Fix:** Check `data.historical_nav` in LineChartPanel

2. **🔴 Nested Object - Sector Allocation**
   - Backend returns `{sector_allocation: {...}, ...}`
   - PieChartPanel receives outer object instead of inner
   - **Fix:** Check `data.sector_allocation` in PieChartPanel

3. **🟡 Empty Data**
   - Arrays/objects empty → Chart doesn't render
   - **Fix:** Add empty data handling

4. **🟡 Canvas Ref Timing**
   - Ref not ready when useEffect runs
   - **Fix:** Add ref readiness check

5. **🟢 Chart.js Not Loaded**
   - Library missing → `Chart is not a constructor`
   - **Fix:** Verify Chart.js script tag

---

**Next Steps:** Use diagnostic checklist to verify which issue is causing the problem.

