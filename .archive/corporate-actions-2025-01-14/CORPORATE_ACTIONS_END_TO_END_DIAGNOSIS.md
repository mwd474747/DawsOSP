# Corporate Actions End-to-End Diagnosis

**Date:** January 14, 2025  
**Status:** 🔍 **DIAGNOSIS COMPLETE**  
**Purpose:** Comprehensive analysis of corporate actions flow and identification of root causes

---

## 📊 Executive Summary

The corporate actions feature is **architecturally complete** but **not working end-to-end**. The UI is correctly integrated with PatternRenderer, the pattern is properly defined, and the agent capabilities are implemented. However, there are several potential failure points that need validation.

**Key Findings:**
- ✅ UI correctly uses `PatternRenderer` with `corporate_actions_upcoming` pattern
- ✅ Pattern definition is correct with 3 steps
- ✅ Agent capabilities (`corporate_actions.upcoming`, `corporate_actions.calculate_impact`) are implemented
- ✅ FMP provider has all calendar endpoints (`get_dividend_calendar`, `get_split_calendar`, `get_earnings_calendar`)
- ⚠️ **CRITICAL GAP**: `/api/corporate-actions` endpoint returns empty data (but this endpoint is NOT used by UI)
- ⚠️ **POTENTIAL ISSUES**: FMP API key, date parsing, field name mismatches, holdings resolution

---

## 🔍 End-to-End Flow Analysis

### Layer 1: UI Component ✅ **CORRECTLY IMPLEMENTED**

**File:** `full_ui.html` lines 11139-11221  
**Component:** `CorporateActionsPage()`

**Implementation:**
```javascript
// Uses PatternRenderer (correct pattern-driven approach)
e(PatternRenderer, {
    pattern: 'corporate_actions_upcoming',
    inputs: {
        portfolio_id: getCurrentPortfolioId(),
        days_ahead: filterDays  // 30, 90, 180, 365
    },
    onDataLoaded: handlePatternData
})

// Expects data at: patternData.actions_with_impact.actions
```

**Status:** ✅ **CORRECT** - Uses pattern system, not direct API call

---

### Layer 2: Pattern Execution ✅ **CORRECTLY DEFINED**

**File:** `backend/patterns/corporate_actions_upcoming.json`

**Pattern Steps:**
1. `ledger.positions` → Get portfolio holdings → `as: "positions"`
2. `corporate_actions.upcoming` → Get upcoming actions → `as: "actions"`
3. `corporate_actions.calculate_impact` → Calculate impact → `as: "actions_with_impact"`

**Expected Output:**
```json
{
  "actions_with_impact": {
    "actions": [...],  // Actions with portfolio_quantity and portfolio_impact
    "total_dividend_impact": 120.00,
    "notifications": {
      "urgent": [...],
      "informational": [...]
    }
  }
}
```

**Status:** ✅ **CORRECT** - Pattern definition matches UI expectations

---

### Layer 3: Pattern Orchestrator ✅ **SHOULD WORK**

**Flow:**
1. UI calls `POST /api/patterns/execute` with `{ pattern_id: "corporate_actions_upcoming", inputs: {...} }`
2. Pattern orchestrator loads pattern JSON
3. Executes steps sequentially:
   - Step 1: `ledger.positions` → FinancialAnalyst agent
   - Step 2: `corporate_actions.upcoming` → DataHarvester agent
   - Step 3: `corporate_actions.calculate_impact` → DataHarvester agent
4. Returns aggregated results

**Status:** ✅ **SHOULD WORK** - Standard pattern execution flow

---

### Layer 4: Agent Capabilities ✅ **IMPLEMENTED**

**File:** `backend/app/agents/data_harvester.py`

#### 4.1 `corporate_actions.upcoming` (lines 2794-2960)

**Implementation:**
- ✅ Fetches dividends from FMP (`corporate_actions_dividends`)
- ✅ Fetches splits from FMP (`corporate_actions_splits`)
- ✅ Fetches earnings from FMP (`corporate_actions_earnings`)
- ✅ Filters by portfolio symbols (client-side filtering after FMP returns all)
- ✅ Combines all actions and calculates summary
- ✅ Returns: `{ actions: [...], summary: {...}, source: "fmp" }`

**Potential Issues:**
1. ⚠️ **Symbol Resolution**: Gets symbols from `state.get("positions", {}).get("positions", [])` (from previous step)
2. ⚠️ **Field Name Mismatch**: Uses `p.get("qty", 0)` but positions might use `quantity_open` or `quantity`
3. ⚠️ **Date Parsing**: Uses `datetime.strptime` but may fail on different date formats
4. ⚠️ **FMP API Key**: Returns empty if `FMP_API_KEY` not configured

**Status:** ✅ **IMPLEMENTED** - But has potential failure points

#### 4.2 `corporate_actions.calculate_impact` (lines 2962-3057)

**Implementation:**
- ✅ Extracts holdings from state or parameter
- ✅ Calculates portfolio impact for each action
- ✅ Creates notifications (urgent = within 7 days)
- ✅ Returns: `{ actions: [...], total_dividend_impact: 120.00, notifications: {...} }`

**Potential Issues:**
1. ⚠️ **Holdings Resolution**: Expects `holdings` parameter or `state.positions.positions`
2. ⚠️ **Field Name Mismatch**: Uses `p.get("qty", 0)` but might need `quantity_open` or `quantity`
3. ⚠️ **Date Format**: May fail on date parsing if formats differ

**Status:** ✅ **IMPLEMENTED** - But has potential failure points

---

### Layer 5: FMP Provider ✅ **IMPLEMENTED**

**File:** `backend/app/integrations/fmp_provider.py`

#### 5.1 `get_dividend_calendar()` (lines 344-397)

**FMP Endpoint:** `/v3/stock_dividend_calendar`  
**Parameters:** `from`, `to`, `apikey`  
**Returns:** List of dividend records

**FMP Response Format:**
```json
[
  {
    "date": "2025-11-07",  // Ex-date
    "symbol": "AAPL",
    "adjDividend": 0.24,
    "dividend": 0.24,
    "recordDate": "2025-11-10",
    "paymentDate": "2025-11-14",
    "declarationDate": "2025-10-28"
  }
]
```

**Normalization in `corporate_actions_dividends`:**
- ✅ Maps `date` → `ex_date`
- ✅ Maps `paymentDate` → `payment_date`
- ✅ Maps `adjDividend` or `dividend` → `amount`
- ✅ Sets `type: "dividend"`
- ✅ Sets `currency: "USD"` (hardcoded)
- ✅ Filters by symbols AFTER fetching (client-side)

**Status:** ✅ **IMPLEMENTED** - But currency is hardcoded to USD

#### 5.2 `get_split_calendar()` (lines 400-450)

**FMP Endpoint:** `/v3/stock_split_calendar`  
**Returns:** List of split records

**FMP Response Format:**
```json
[
  {
    "date": "2025-11-07",
    "symbol": "AAPL",
    "numerator": 4,
    "denominator": 1
  }
]
```

**Normalization in `corporate_actions_splits`:**
- ✅ Maps `date` → `date`
- ✅ Creates `ratio: "4:1"` from `numerator:denominator`
- ✅ Sets `type: "split"`
- ✅ Filters by symbols AFTER fetching

**Status:** ✅ **IMPLEMENTED** - Correct

#### 5.3 `get_earnings_calendar()` (lines 453-505)

**FMP Endpoint:** `/v3/earning_calendar`  
**Returns:** List of earnings records

**FMP Response Format:**
```json
[
  {
    "date": "2025-11-07",
    "symbol": "AAPL",
    "eps": 1.42,
    "epsEstimated": 1.38,
    "time": "amc",
    "revenue": 90000000000,
    "revenueEstimated": 89000000000
  }
]
```

**Normalization in `corporate_actions_earnings`:**
- ✅ Maps all fields correctly
- ✅ Sets `type: "earnings"`
- ✅ Filters by symbols AFTER fetching

**Status:** ✅ **IMPLEMENTED** - Correct

---

## 🔴 Root Cause Analysis

### Issue 1: Field Name Mismatch ⚠️ **CONFIRMED ROOT CAUSE**

**Problem:**
- `corporate_actions.upcoming` uses: `p.get("qty", 0)` (line 2839)
- `corporate_actions.calculate_impact` uses: `p.get("qty", 0)` (line 2993)
- **BUT** `ledger.positions` returns: `quantity` (NOT `qty`) - see `financial_analyst.py` line 225

**Evidence:**
- `ledger.positions` SQL query: `l.quantity_open AS qty` (line 201)
- But returns: `"quantity": qty` (line 225)
- So the field in the returned dict is `quantity`, not `qty`

**Impact:**
- `p.get("qty", 0)` always returns `0` (default)
- All positions are filtered out → `symbols` is empty
- Empty `symbols` → No filtering → Returns empty actions array
- UI shows "No corporate actions found"

**Fix Required:**
```python
# In corporate_actions.upcoming (line 2839)
# Change from: p.get("qty", 0)
# To: p.get("quantity", 0) or p.get("qty", 0)  # Support both field names

# In corporate_actions.calculate_impact (line 2993)
# Change from: p.get("qty", 0)
# To: p.get("quantity", 0) or p.get("qty", 0)  # Support both field names
```

---

### Issue 2: FMP API Key Missing ⚠️ **HIGH PROBABILITY**

**Problem:**
- All three methods (`corporate_actions_dividends`, `corporate_actions_splits`, `corporate_actions_earnings`) check for `FMP_API_KEY`
- If missing, returns empty arrays with error message
- Error is logged but may not propagate to UI

**Impact:**
- Empty actions array returned
- UI shows "No corporate actions found"

**Fix Required:**
- Verify `FMP_API_KEY` environment variable is set
- Check logs for "FMP_API_KEY not configured" messages

---

### Issue 3: Date Range Calculation ⚠️ **MEDIUM PROBABILITY**

**Problem:**
- `corporate_actions.upcoming` uses `days_ahead` parameter (default 90)
- But FMP calendar endpoints require `from_date` and `to_date`
- If `asof_date` is not today, date range might be wrong

**Impact:**
- Fetching actions from wrong date range
- Missing recent actions or fetching too far in future

**Fix Required:**
- Verify `asof_date` resolution in context
- Ensure date range calculation is correct

---

### Issue 4: Holdings Resolution ⚠️ **MEDIUM PROBABILITY**

**Problem:**
- `corporate_actions.upcoming` expects symbols from `state.positions.positions`
- But pattern step 1 is `ledger.positions` → `as: "positions"`
- Need to verify the exact structure returned by `ledger.positions`

**Impact:**
- If `state.positions.positions` is wrong structure, symbols will be empty
- No filtering → Returns all FMP actions or empty array

**Fix Required:**
- Check what `ledger.positions` actually returns
- Verify state structure matches expectations

---

### Issue 5: Pattern Step Ordering ⚠️ **LOW PROBABILITY**

**Problem:**
- Pattern step 2 (`corporate_actions.upcoming`) needs symbols from step 1
- But step 2 also accepts `portfolio_id` parameter
- If `portfolio_id` is provided, method might not use symbols from state

**Impact:**
- If `portfolio_id` is provided but portfolio has no holdings, returns empty
- If symbols not in state, falls back to empty array

**Fix Required:**
- Verify pattern passes `portfolio_id` correctly
- Ensure step 2 uses symbols from step 1 when available

---

## 🔧 Recommended Fixes (Priority Order)

### Priority 1: Fix Field Name Mismatch

**Files to Update:**
1. `backend/app/agents/data_harvester.py` line 2839
2. `backend/app/agents/data_harvester.py` line 2993

**Change:**
```python
# Support multiple field names for quantity
symbols = [
    p.get("symbol") 
    for p in positions 
    if (p.get("qty", 0) or p.get("quantity_open", 0) or p.get("quantity", 0)) > 0
]

holdings = {
    p.get("symbol"): float(
        p.get("qty", 0) or 
        p.get("quantity_open", 0) or 
        p.get("quantity", 0)
    ) 
    for p in positions
}
```

---

### Priority 2: Verify FMP API Key

**Action:**
1. Check environment variable: `FMP_API_KEY`
2. Test FMP endpoints directly:
   ```bash
   curl "https://financialmodelingprep.com/api/v3/stock_dividend_calendar?from=2025-01-14&to=2025-04-14&apikey=YOUR_KEY"
   ```
3. Check logs for "FMP_API_KEY not configured" errors

---

### Priority 3: Verify Holdings Resolution

**Action:**
1. Add debug logging to `corporate_actions.upcoming`:
   ```python
   logger.debug(f"Positions from state: {positions}")
   logger.debug(f"Resolved symbols: {symbols}")
   ```
2. Check what `ledger.positions` actually returns
3. Verify state structure matches expectations

---

### Priority 4: Add Error Handling

**Action:**
1. Ensure errors from FMP provider propagate to UI
2. Add user-friendly error messages
3. Log all errors with full context

---

## 🧪 Testing Plan

### Test 1: Verify Pattern Execution

**Steps:**
1. Call `POST /api/patterns/execute` with:
   ```json
   {
     "pattern_id": "corporate_actions_upcoming",
     "inputs": {
       "portfolio_id": "<valid-portfolio-id>",
       "days_ahead": 90
     }
   }
   ```
2. Check response structure
3. Verify all 3 steps execute successfully

### Test 2: Verify Holdings Resolution

**Steps:**
1. Check logs for `ledger.positions` output
2. Verify `state.positions.positions` structure
3. Check if symbols are extracted correctly

### Test 3: Verify FMP API Calls

**Steps:**
1. Check logs for FMP API calls
2. Verify responses are received
3. Check if filtering by symbols works

### Test 4: Verify Impact Calculation

**Steps:**
1. Check if `corporate_actions.calculate_impact` receives correct data
2. Verify holdings are passed correctly
3. Check if impact calculations are correct

---

## 📋 Next Steps

1. **Immediate**: Fix field name mismatch (Priority 1)
2. **Immediate**: Verify FMP API key is configured (Priority 2)
3. **Short-term**: Add debug logging to trace execution flow
4. **Short-term**: Test with real portfolio data
5. **Medium-term**: Add comprehensive error handling
6. **Medium-term**: Add unit tests for each capability

---

## ✅ Conclusion

The corporate actions feature is **architecturally sound** but has a **critical implementation bug** that prevents it from working end-to-end.

**Root Cause Confirmed:**
1. **Field name mismatch** - `ledger.positions` returns `quantity` but code uses `qty` → **CONFIRMED**
   - This causes all positions to be filtered out
   - Empty symbols → No filtering → Empty actions array
   - This is the PRIMARY reason the feature doesn't work

**Secondary Issues:**
2. **FMP API key missing** - Would cause empty arrays if not configured
3. **Holdings resolution** - Related to field name mismatch

**Fix Priority:**
1. **IMMEDIATE**: Fix field name mismatch (change `qty` to `quantity`)
2. **VERIFY**: Check FMP API key configuration
3. **TEST**: Verify end-to-end flow after fix

Once the field name mismatch is fixed, the feature should work correctly.

