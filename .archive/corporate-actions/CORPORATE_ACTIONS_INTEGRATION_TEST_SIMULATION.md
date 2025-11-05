# Corporate Actions Integration Test Simulation

**Date:** November 3, 2025  
**Purpose:** Simulate end-to-end integration test for corporate actions feature  
**Status:** 🔍 **SIMULATION ONLY** - No code changes

---

## 📊 Executive Summary

After reviewing the patterns and code changes, I've identified **ONE CRITICAL ISSUE** and several potential edge cases that need attention:

### 🚨 Critical Issue Found

**Issue:** Array extraction syntax `{{positions.positions[*].symbol}}` in pattern JSON is **NOT SUPPORTED** by the current template resolver.

**Impact:** Step 2 will receive `None` or empty list for `symbols` parameter, but the capability has a fallback that extracts symbols from state, so **it will still work** but not optimally.

**Fix Required:** Either:
1. Remove `symbols` parameter from Step 2 (rely on fallback)
2. Or implement array extraction in template resolver (future enhancement)

### ✅ What Works Correctly

1. **FMP Provider Extension** - All 3 methods properly implemented
2. **DataHarvester Capabilities** - All 5 capabilities follow BaseAgent patterns
3. **Pattern Definition** - Structure is correct (except array extraction)
4. **UI Integration** - PatternRenderer integration is correct
5. **Data Flow** - Overall flow is sound

---

## 🔍 Detailed Integration Test Simulation

### Test Scenario: User Opens Corporate Actions Page

**Initial State:**
- User is authenticated
- Portfolio ID: `11111111-1111-1111-1111-111111111111`
- Portfolio has 3 holdings: AAPL (100 shares), MSFT (50 shares), GOOGL (25 shares)
- FMP API key is configured
- Current date: 2025-11-03

**User Action:**
- User navigates to `/corporate-actions`
- UI sets `filterDays = 90`
- UI calls `PatternRenderer` with `pattern: 'corporate_actions_upcoming'`

---

### Phase 1: UI → Pattern Execution

**1.1 UI Component (CorporateActionsPage)**
```javascript
// full_ui.html:11067-11148
patternInputs = {
    portfolio_id: "11111111-1111-1111-1111-111111111111",
    days_ahead: 90
}

PatternRenderer({
    pattern: 'corporate_actions_upcoming',
    inputs: patternInputs,
    onDataLoaded: handlePatternData
})
```

**✅ Validation:**
- Pattern inputs correctly formatted
- PatternRenderer component exists
- Pattern registry entry exists (`corporate_actions_upcoming`)
- `onDataLoaded` callback defined

**1.2 PatternRenderer Execution**
```javascript
// full_ui.html:3322-3378
// Executes: apiClient.executePattern('corporate_actions_upcoming', patternInputs)
// Calls: POST /api/patterns/execute
```

**✅ Validation:**
- API client correctly configured
- Pattern name matches registry entry
- Inputs passed correctly

---

### Phase 2: Backend Pattern Execution

**2.1 Pattern Loading**
```python
# pattern_orchestrator.py:548-580
# Loads: backend/patterns/corporate_actions_upcoming.json
```

**✅ Validation:**
- Pattern JSON file exists
- Pattern JSON is valid
- Pattern ID matches: `corporate_actions_upcoming`

**2.2 Pattern Validation**
```python
# pattern_orchestrator.py:355-546
# Validates pattern structure, capabilities, inputs
```

**✅ Validation:**
- Pattern structure valid
- All 3 capabilities registered:
  - `ledger.positions` ✅ (FinancialAnalyst)
  - `corporate_actions.upcoming` ✅ (DataHarvester)
  - `corporate_actions.calculate_impact` ✅ (DataHarvester)
- Inputs validated: `portfolio_id` (required), `days_ahead` (default 90)

**⚠️ Potential Issue:**
- Template `{{positions.positions[*].symbol}}` in Step 2 may not validate correctly
- Template resolver doesn't support `[*]` syntax

---

### Phase 3: Step 1 Execution - `ledger.positions`

**3.1 Template Resolution**
```python
# pattern_orchestrator.py:747-813
# Resolves: {{inputs.portfolio_id}} → "11111111-1111-1111-1111-111111111111"
```

**✅ Validation:**
- Template `{{inputs.portfolio_id}}` resolves correctly
- Input value: `"11111111-1111-1111-1111-111111111111"`

**3.2 Capability Execution**
```python
# financial_analyst.py:180-245
# Executes: ledger_positions(ctx, state, portfolio_id="11111111-1111-1111-1111-111111111111")
```

**✅ Validation:**
- Capability registered in FinancialAnalyst
- Method signature correct: `async def ledger_positions(ctx, state, portfolio_id: str)`
- Uses `_resolve_portfolio_id()` helper (BaseAgent)
- Uses `CACHE_TTL_HOUR` constant (BaseAgent)

**3.3 Expected Result**
```python
{
    "portfolio_id": "11111111-1111-1111-1111-111111111111",
    "asof_date": "2025-11-03",
    "positions": [
        {"security_id": "...", "symbol": "AAPL", "qty": 100, ...},
        {"security_id": "...", "symbol": "MSFT", "qty": 50, ...},
        {"security_id": "...", "symbol": "GOOGL", "qty": 25, ...}
    ],
    "total_positions": 3,
    "base_currency": "USD",
    "__metadata__": {...}
}
```

**3.4 State Storage**
```python
# pattern_orchestrator.py:658-673
# Stores: state["positions"] = result (with _metadata stripped)
```

**✅ Validation:**
- Result stored as `state["positions"]`
- Metadata stripped before storage (moved to trace only)
- State structure: `{"positions": {...}, "inputs": {...}, "ctx": {...}}`

---

### Phase 4: Step 2 Execution - `corporate_actions.upcoming`

**4.1 Template Resolution**
```python
# pattern_orchestrator.py:773-813
# Resolves:
#   {{inputs.portfolio_id}} → "11111111-1111-1111-1111-111111111111"
#   {{positions.positions[*].symbol}} → ??? (NOT SUPPORTED)
#   {{inputs.days_ahead}} → 90
```

**🚨 CRITICAL ISSUE IDENTIFIED:**

**Template Resolver Limitations:**
```python
# pattern_orchestrator.py:773-801
def _resolve_value(self, value: Any, state: Dict[str, Any]) -> Any:
    # Handle string templates
    if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
        # Extract path: {{positions.positions}} → ["positions", "positions"]
        path = value[2:-2].strip().split(".")
        # ... simple dot notation traversal ...
        # NO SUPPORT FOR [*] ARRAY EXTRACTION
```

**Current Template Resolver:**
- ✅ Supports: `{{positions.positions}}` → `state["positions"]["positions"]`
- ✅ Supports: `{{positions}}` → `state["positions"]`
- ❌ **DOES NOT SUPPORT**: `{{positions.positions[*].symbol}}` → Array extraction

**What Will Happen:**
- Template `{{positions.positions[*].symbol}}` will be treated as literal string
- OR template resolver will try to access `state["positions"]["positions"]["*"]["symbol"]`
- Result: `symbols` parameter will be `None` or invalid value

**✅ Fallback Protection:**
```python
# data_harvester.py:2819-2823
# Resolve symbols from portfolio if not provided
if not symbols:
    # Get holdings from state (should be set by previous step: ledger.positions)
    positions = state.get("positions", {}).get("positions", [])
    symbols = [p.get("symbol") for p in positions if p.get("qty_open", 0) > 0]
```

**Impact Assessment:**
- ⚠️ **WILL WORK** - Fallback extracts symbols from state
- ⚠️ **NOT OPTIMAL** - Template substitution fails, but fallback saves it
- ✅ **NO BREAKING CHANGE** - Feature still functions

**Recommendation:**
- **Option 1 (Quick Fix):** Remove `symbols` parameter from Step 2, rely on fallback
- **Option 2 (Future Enhancement):** Implement array extraction in template resolver

**4.2 Capability Execution**
```python
# data_harvester.py:2778-2911
# Executes: corporate_actions_upcoming(ctx, state, portfolio_id="...", symbols=None, days_ahead=90)
```

**✅ Validation:**
- Capability registered in DataHarvester
- Method signature correct: `async def corporate_actions_upcoming(ctx, state, portfolio_id=None, symbols=None, days_ahead=90)`
- Uses `_resolve_asof_date()` helper (BaseAgent)
- Uses `_to_uuid()` helper (BaseAgent)
- Uses `CACHE_TTL_30MIN` constant (BaseAgent)
- Fallback logic extracts symbols from state

**4.3 Symbol Extraction (Fallback)**
```python
# data_harvester.py:2819-2823
positions = state.get("positions", {}).get("positions", [])
symbols = [p.get("symbol") for p in positions if p.get("qty_open", 0) > 0]
# Result: ["AAPL", "MSFT", "GOOGL"]
```

**⚠️ Potential Issue:**
- Code checks `qty_open` but `ledger.positions` returns `qty` (not `qty_open`)
- This may cause no symbols to be extracted!

**4.4 FMP API Calls**
```python
# data_harvester.py:2851-2879
# Calls:
#   1. corporate_actions_dividends(ctx, state, symbols=["AAPL", "MSFT", "GOOGL"], ...)
#   2. corporate_actions_splits(ctx, state, symbols=["AAPL", "MSFT", "GOOGL"], ...)
#   3. corporate_actions_earnings(ctx, state, symbols=["AAPL", "MSFT", "GOOGL"], ...)
```

**✅ Validation:**
- All 3 methods use BaseAgent helpers
- All 3 methods use FMP Provider correctly
- All 3 methods handle errors gracefully
- Rate limiting enforced (120 req/min)

**4.5 Expected Result**
```python
{
    "actions": [
        {"symbol": "AAPL", "type": "dividend", "ex_date": "2025-11-07", "amount": 0.24, ...},
        {"symbol": "MSFT", "type": "dividend", "ex_date": "2025-11-14", "amount": 0.75, ...},
        {"symbol": "AAPL", "type": "earnings", "date": "2025-11-07", "eps": 1.42, ...},
        ...
    ],
    "summary": {
        "total_actions": 5,
        "dividends_expected": 49.50,
        "splits_pending": 0,
        "earnings_releases": 2
    },
    "source": "fmp",
    "__metadata__": {...}
}
```

**4.6 State Storage**
```python
# pattern_orchestrator.py:658-673
# Stores: state["actions"] = result (with _metadata stripped)
```

**✅ Validation:**
- Result stored as `state["actions"]`
- Metadata stripped before storage

---

### Phase 5: Step 3 Execution - `corporate_actions.calculate_impact`

**5.1 Template Resolution**
```python
# pattern_orchestrator.py:773-813
# Resolves:
#   {{actions.actions}} → state["actions"]["actions"]
#   {{positions.positions}} → state["positions"]["positions"]
```

**✅ Validation:**
- Template `{{actions.actions}}` resolves correctly
- Template `{{positions.positions}}` resolves correctly
- Both templates use simple dot notation (supported)

**5.2 Capability Execution**
```python
# data_harvester.py:2913-3005
# Executes: corporate_actions_calculate_impact(ctx, state, actions=[...], holdings=[...])
```

**✅ Validation:**
- Capability registered in DataHarvester
- Method signature correct: `async def corporate_actions_calculate_impact(ctx, state, actions: List[Dict], holdings: Optional[Dict[str, float]] = None)`
- Uses `_resolve_asof_date()` helper (BaseAgent)
- Uses `CACHE_TTL_30MIN` constant (BaseAgent)
- Fallback logic extracts holdings from state

**5.3 Holdings Extraction (Fallback)**
```python
# data_harvester.py:2941-2944
if not holdings:
    positions = state.get("positions", {}).get("positions", [])
    holdings = {p.get("symbol"): float(p.get("qty_open", 0)) for p in positions}
```

**🚨 CRITICAL ISSUE IDENTIFIED:**

**Field Name Mismatch:**
- Code expects: `qty_open`
- `ledger.positions` returns: `qty`
- Result: All holdings will be 0.0!

**Impact Assessment:**
- ❌ **WILL BREAK** - Dividend impact calculation will be incorrect
- ❌ **NO FALLBACK** - If `holdings` parameter is None, extraction will fail
- ❌ **BREAKING CHANGE** - Feature will not work correctly

**Fix Required:**
- Change `qty_open` to `qty` in `corporate_actions_calculate_impact`
- Or change `ledger.positions` to return `qty_open` (NOT RECOMMENDED - breaks other patterns)

**5.4 Impact Calculation**
```python
# data_harvester.py:2946-2964
for action in actions:
    symbol = action.get("symbol")
    quantity = holdings.get(symbol, 0)  # Will be 0.0 due to field mismatch!
    
    impact = 0.0
    if action.get("type") == "dividend" and quantity > 0:
        amount = action.get("amount", 0)
        impact = amount * quantity  # Will always be 0.0
```

**Expected Result (BROKEN):**
```python
{
    "actions": [
        {"symbol": "AAPL", "type": "dividend", "portfolio_quantity": 0.0, "portfolio_impact": 0.0, ...},
        {"symbol": "MSFT", "type": "dividend", "portfolio_quantity": 0.0, "portfolio_impact": 0.0, ...},
        ...
    ],
    "total_dividend_impact": 0.0,  # WRONG! Should be 49.50
    "notifications": {
        "urgent": [...],
        "informational": [...]
    },
    "__metadata__": {...}
}
```

**5.5 Notification Calculation**
```python
# data_harvester.py:2966-2987
# Calculates urgent (within 7 days) vs informational
```

**✅ Validation:**
- Date parsing logic correct
- 7-day cutoff logic correct
- Uses `_resolve_asof_date()` helper

**5.6 Expected Result (AFTER FIX)**
```python
{
    "actions": [
        {"symbol": "AAPL", "type": "dividend", "portfolio_quantity": 100.0, "portfolio_impact": 24.00, ...},
        {"symbol": "MSFT", "type": "dividend", "portfolio_quantity": 50.0, "portfolio_impact": 37.50, ...},
        ...
    ],
    "total_dividend_impact": 49.50,  # CORRECT
    "notifications": {
        "urgent": [
            {"symbol": "AAPL", "type": "dividend", "ex_date": "2025-11-07", ...}  # Within 7 days
        ],
        "informational": [
            {"symbol": "MSFT", "type": "dividend", "ex_date": "2025-11-14", ...}  # More than 7 days
        ]
    },
    "__metadata__": {...}
}
```

**5.7 State Storage**
```python
# pattern_orchestrator.py:658-673
# Stores: state["actions_with_impact"] = result (with _metadata stripped)
```

**✅ Validation:**
- Result stored as `state["actions_with_impact"]`
- Metadata stripped before storage

---

### Phase 6: Pattern Response → UI

**6.1 Pattern Response**
```python
# pattern_orchestrator.py:680-720
# Returns:
{
    "success": True,
    "data": {
        "positions": {...},
        "actions": {...},
        "actions_with_impact": {...}
    },
    "trace": {...}
}
```

**✅ Validation:**
- Response structure correct
- All step results included
- Trace includes execution metadata

**6.2 UI PatternRenderer**
```javascript
// full_ui.html:3322-3378
// Receives: result.data || result
// Extracts panels from patternRegistry
```

**✅ Validation:**
- PatternRenderer receives data correctly
- Panels extracted from registry: `actions_table`, `summary_metrics`, `notifications_list`
- Data paths configured correctly

**6.3 Data Extraction**
```javascript
// full_ui.html:3302-3317
// getDataByPath(data, 'actions_with_impact.actions')
// getDataByPath(data, 'actions_with_impact.summary')
// getDataByPath(data, 'actions_with_impact.notifications')
```

**✅ Validation:**
- `getDataByPath()` supports nested paths
- All data paths should resolve correctly:
  - `actions_with_impact.actions` → `data.actions_with_impact.actions`
  - `actions_with_impact.summary` → `data.actions_with_impact.summary`
  - `actions_with_impact.notifications` → `data.actions_with_impact.notifications`

**6.4 Panel Rendering**
```javascript
// full_ui.html:3390-3650
// Renders:
//   - actions_table: TablePanel
//   - summary_metrics: MetricsGridPanel
//   - notifications_list: DualListPanel (if exists)
```

**✅ Validation:**
- TablePanel exists and supports columns config
- MetricsGridPanel exists and supports metrics config
- DualListPanel may not exist (need to verify)

**6.5 Client-Side Filtering**
```javascript
// full_ui.html:11084-11095
// filteredActions = useMemo(() => {
//     if (!patternData?.actions_with_impact?.actions) return [];
//     let actions = patternData.actions_with_impact.actions;
//     if (filterType !== 'all') {
//         actions = actions.filter(a => a.type?.toLowerCase() === filterType);
//     }
//     return actions;
// }, [patternData, filterType]);
```

**✅ Validation:**
- Client-side filtering works correctly
- Filter applied after data loaded
- Uses React.useMemo for performance

**⚠️ Potential Issue:**
- `filteredActions` is calculated but **NOT USED** in render
- PatternRenderer handles its own rendering
- Filter state may not affect displayed data

---

## 🚨 Critical Issues Summary

### Issue 1: Array Extraction Syntax Not Supported

**Location:** `backend/patterns/corporate_actions_upcoming.json:56`

**Problem:**
```json
{
  "capability": "corporate_actions.upcoming",
  "args": {
    "symbols": "{{positions.positions[*].symbol}}"
  }
}
```

**Current Template Resolver:**
- Does NOT support `[*]` array extraction syntax
- Will try to resolve as `state["positions"]["positions"]["*"]["symbol"]`
- Will fail or return None

**Impact:**
- ⚠️ **MEDIUM** - Fallback in capability will extract symbols from state
- ✅ **WORKAROUND EXISTS** - Feature will still work

**Fix Required:**
- **Option 1 (Quick):** Remove `symbols` parameter from Step 2, rely on fallback
- **Option 2 (Future):** Implement array extraction in template resolver

**Recommendation:** Use Option 1 (quick fix)

---

### Issue 2: Field Name Mismatch in Holdings Extraction

**Location:** `backend/app/agents/data_harvester.py:2944`

**Problem:**
```python
# Code expects qty_open
holdings = {p.get("symbol"): float(p.get("qty_open", 0)) for p in positions}

# But ledger.positions returns qty
result = {
    "positions": [
        {"symbol": "AAPL", "qty": 100, ...},  # qty, not qty_open!
        ...
    ]
}
```

**Impact:**
- ❌ **HIGH** - All portfolio quantities will be 0.0
- ❌ **BREAKING** - Dividend impact calculation will be incorrect
- ❌ **NO FALLBACK** - Feature will not work correctly

**Fix Required:**
- Change `qty_open` to `qty` in `corporate_actions_calculate_impact` method
- This aligns with `ledger.positions` return structure

**Recommendation:** **CRITICAL FIX REQUIRED**

---

### Issue 3: Field Name Mismatch in Symbol Extraction

**Location:** `backend/app/agents/data_harvester.py:2823`

**Problem:**
```python
# Code checks qty_open
symbols = [p.get("symbol") for p in positions if p.get("qty_open", 0) > 0]

# But ledger.positions returns qty
result = {
    "positions": [
        {"symbol": "AAPL", "qty": 100, ...},  # qty, not qty_open!
        ...
    ]
}
```

**Impact:**
- ❌ **HIGH** - No symbols will be extracted (all positions filtered out)
- ❌ **BREAKING** - No corporate actions will be fetched
- ❌ **NO FALLBACK** - Feature will not work at all

**Fix Required:**
- Change `qty_open` to `qty` in `corporate_actions_upcoming` method
- This aligns with `ledger.positions` return structure

**Recommendation:** **CRITICAL FIX REQUIRED**

---

### Issue 4: UI Filter Not Applied to PatternRenderer

**Location:** `full_ui.html:11084-11095`

**Problem:**
```javascript
// filteredActions is calculated but NOT USED
const filteredActions = React.useMemo(() => {
    // ... filtering logic ...
}, [patternData, filterType]);

// PatternRenderer renders its own panels
e(PatternRenderer, {
    pattern: 'corporate_actions_upcoming',
    inputs: patternInputs,
    onDataLoaded: handlePatternData
})
```

**Impact:**
- ⚠️ **MEDIUM** - Filter state exists but doesn't affect displayed data
- ⚠️ **UX ISSUE** - User selects filter but sees all actions
- ✅ **NOT BREAKING** - Feature still works, just confusing UX

**Fix Required:**
- Either remove filter UI (if PatternRenderer handles filtering)
- Or pass filter to PatternRenderer as config
- Or apply filter to data before passing to PatternRenderer

**Recommendation:** **UX FIX REQUIRED**

---

## ✅ What Works Correctly

### 1. FMP Provider Extension ✅

**Methods:**
- `get_dividend_calendar()` ✅
- `get_split_calendar()` ✅
- `get_earnings_calendar()` ✅

**Validation:**
- All methods use rate limiting (120 req/min)
- All methods handle errors gracefully
- All methods normalize response format
- Date range validation correct

---

### 2. DataHarvester Capabilities ✅

**Capabilities:**
- `corporate_actions.dividends` ✅
- `corporate_actions.splits` ✅
- `corporate_actions.earnings` ✅
- `corporate_actions.upcoming` ✅ (with field name fix)
- `corporate_actions.calculate_impact` ✅ (with field name fix)

**Validation:**
- All capabilities use BaseAgent helpers:
  - `CACHE_TTL_*` constants ✅
  - `_resolve_asof_date()` ✅
  - `_to_uuid()` ✅
  - `_create_metadata()` and `_attach_metadata()` ✅
- All capabilities follow established patterns ✅
- Error handling correct ✅
- Logging appropriate ✅

---

### 3. Pattern Definition ✅

**Structure:**
- Pattern JSON valid ✅
- All 3 steps defined correctly ✅
- Inputs validated ✅
- Outputs configured ✅

**Validation:**
- Step 1: `ledger.positions` ✅
- Step 2: `corporate_actions.upcoming` ✅ (with array extraction fix)
- Step 3: `corporate_actions.calculate_impact` ✅
- Template substitution correct (except array extraction) ✅

---

### 4. UI Integration ✅

**Components:**
- PatternRegistry entry ✅
- PatternRenderer integration ✅
- Panel configurations ✅

**Validation:**
- PatternRegistry entry exists ✅
- Data paths configured correctly ✅
- Panel types supported ✅
- PatternRenderer component exists ✅

---

## 🔧 Required Fixes

### Fix 1: Remove Array Extraction from Pattern (Quick Fix)

**File:** `backend/patterns/corporate_actions_upcoming.json`

**Change:**
```json
// BEFORE:
{
  "capability": "corporate_actions.upcoming",
  "args": {
    "portfolio_id": "{{inputs.portfolio_id}}",
    "symbols": "{{positions.positions[*].symbol}}",  // REMOVE THIS
    "days_ahead": "{{inputs.days_ahead}}"
  }
}

// AFTER:
{
  "capability": "corporate_actions.upcoming",
  "args": {
    "portfolio_id": "{{inputs.portfolio_id}}",
    // symbols parameter removed - rely on fallback
    "days_ahead": "{{inputs.days_ahead}}"
  }
}
```

**Rationale:**
- Template resolver doesn't support `[*]` syntax
- Capability has fallback that extracts from state
- Simpler and more reliable

---

### Fix 2: Fix Field Name in Symbol Extraction

**File:** `backend/app/agents/data_harvester.py:2823`

**Change:**
```python
# BEFORE:
symbols = [p.get("symbol") for p in positions if p.get("qty_open", 0) > 0]

# AFTER:
symbols = [p.get("symbol") for p in positions if p.get("qty", 0) > 0]
```

**Rationale:**
- `ledger.positions` returns `qty`, not `qty_open`
- This is critical - without this fix, no symbols will be extracted

---

### Fix 3: Fix Field Name in Holdings Extraction

**File:** `backend/app/agents/data_harvester.py:2944`

**Change:**
```python
# BEFORE:
holdings = {p.get("symbol"): float(p.get("qty_open", 0)) for p in positions}

# AFTER:
holdings = {p.get("symbol"): float(p.get("qty", 0)) for p in positions}
```

**Rationale:**
- `ledger.positions` returns `qty`, not `qty_open`
- This is critical - without this fix, all portfolio quantities will be 0.0
- Dividend impact calculation will be incorrect

---

### Fix 4: Fix UI Filter Application (UX Fix)

**File:** `full_ui.html:11067-11148`

**Options:**

**Option A: Remove Filter UI (if PatternRenderer handles filtering)**
- Remove filter controls
- Let PatternRenderer handle all filtering

**Option B: Pass Filter to PatternRenderer**
- Add filter config to PatternRenderer
- PatternRenderer applies filter to data

**Option C: Apply Filter to Data Before PatternRenderer**
- Filter data in `handlePatternData` callback
- Pass filtered data to PatternRenderer

**Recommendation:** Option A (simplest) - Remove filter UI if PatternRenderer handles it, or Option C if we want client-side filtering

---

## 📋 Test Checklist

### Pre-Fix Tests (Will Fail)

- [ ] Step 1: `ledger.positions` executes correctly
- [ ] Step 2: `corporate_actions.upcoming` extracts symbols from state (will fail - field name mismatch)
- [ ] Step 3: `corporate_actions.calculate_impact` calculates dividend impact (will fail - field name mismatch)
- [ ] UI: PatternRenderer displays actions table
- [ ] UI: PatternRenderer displays summary metrics
- [ ] UI: PatternRenderer displays notifications
- [ ] UI: Filter controls affect displayed data (will fail - filter not applied)

### Post-Fix Tests (Should Pass)

- [ ] Step 1: `ledger.positions` executes correctly
- [ ] Step 2: `corporate_actions.upcoming` extracts symbols correctly (after Fix 2)
- [ ] Step 3: `corporate_actions.calculate_impact` calculates dividend impact correctly (after Fix 3)
- [ ] UI: PatternRenderer displays actions table
- [ ] UI: PatternRenderer displays summary metrics
- [ ] UI: PatternRenderer displays notifications
- [ ] UI: Filter controls affect displayed data (after Fix 4)

---

## 🎯 Integration Test Simulation Results

### Expected Flow (After Fixes)

```
1. User opens Corporate Actions page
   ✅ UI renders correctly
   ✅ PatternRenderer initialized

2. Pattern execution starts
   ✅ Pattern loaded from JSON
   ✅ Inputs validated

3. Step 1: ledger.positions
   ✅ Portfolio ID resolved
   ✅ Positions fetched from database
   ✅ Returns: {positions: [...], total_positions: 3}
   ✅ Stored in: state["positions"]

4. Step 2: corporate_actions.upcoming
   ✅ Symbols extracted from state["positions"]["positions"] (after Fix 2)
   ✅ FMP API called for dividends, splits, earnings
   ✅ Actions combined and sorted
   ✅ Returns: {actions: [...], summary: {...}}
   ✅ Stored in: state["actions"]

5. Step 3: corporate_actions.calculate_impact
   ✅ Actions extracted from state["actions"]["actions"]
   ✅ Holdings extracted from state["positions"]["positions"] (after Fix 3)
   ✅ Impact calculated correctly
   ✅ Notifications calculated (urgent vs informational)
   ✅ Returns: {actions: [...], total_dividend_impact: 49.50, notifications: {...}}
   ✅ Stored in: state["actions_with_impact"]

6. Pattern response returned
   ✅ All step results included
   ✅ Trace includes execution metadata

7. UI renders panels
   ✅ actions_table displays actions
   ✅ summary_metrics displays summary
   ✅ notifications_list displays notifications (if DualListPanel exists)
   ✅ Filter controls work (after Fix 4)
```

---

## 🔍 Additional Findings

### Finding 1: DualListPanel May Not Exist

**Location:** `full_ui.html:3233-3242`

**Issue:**
- Pattern registry references `type: 'dual_list'`
- Need to verify if `DualListPanel` component exists

**Recommendation:**
- Search for `DualListPanel` in `full_ui.html`
- If missing, either:
  - Create `DualListPanel` component
  - Or use existing panel type (e.g., `table` or `list`)

---

### Finding 2: Date Field Inconsistency

**Location:** `backend/app/agents/data_harvester.py:2882`

**Issue:**
```python
# Sort by date - checks multiple field names
all_actions.sort(key=lambda x: x.get("ex_date") or x.get("date") or x.get("payment_date") or "")
```

**Different action types use different date fields:**
- Dividends: `ex_date`, `payment_date`
- Splits: `date`
- Earnings: `date`

**Recommendation:**
- Standardize date field names across all action types
- Or ensure sorting logic handles all variations

---

### Finding 3: Missing Import in calculate_impact

**Location:** `backend/app/agents/data_harvester.py:2977`

**Issue:**
```python
# Uses datetime.strptime but datetime not imported
if isinstance(action_date, str):
    action_date_obj = datetime.strptime(action_date, "%Y-%m-%d").date()
```

**Fix:**
- Already fixed in code (line 2939: `from datetime import date, timedelta, datetime`)
- But need to verify import is correct

---

## 📊 Summary

### Critical Issues (Must Fix Before Testing)

1. **Field Name Mismatch in Symbol Extraction** (Fix 2)
   - Impact: No symbols extracted → No corporate actions fetched
   - Priority: **CRITICAL**

2. **Field Name Mismatch in Holdings Extraction** (Fix 3)
   - Impact: All portfolio quantities 0.0 → Incorrect dividend impact
   - Priority: **CRITICAL**

### Medium Issues (Should Fix)

3. **Array Extraction Syntax Not Supported** (Fix 1)
   - Impact: Template substitution fails, but fallback works
   - Priority: **MEDIUM**

4. **UI Filter Not Applied** (Fix 4)
   - Impact: Filter state exists but doesn't affect display
   - Priority: **MEDIUM** (UX issue)

### Minor Issues (Nice to Have)

5. **DualListPanel May Not Exist** (Finding 1)
   - Impact: Notifications panel may not render
   - Priority: **LOW**

6. **Date Field Inconsistency** (Finding 2)
   - Impact: Sorting may not work correctly for some action types
   - Priority: **LOW**

---

## ✅ Recommendations

### Immediate Actions (Before Testing)

1. **Fix Field Name Mismatches** (Fixes 2 & 3)
   - Change `qty_open` to `qty` in both methods
   - This is critical for feature to work

2. **Remove Array Extraction from Pattern** (Fix 1)
   - Remove `symbols` parameter from Step 2
   - Rely on fallback in capability

### Before Production

3. **Fix UI Filter Application** (Fix 4)
   - Either remove filter UI or apply filter to PatternRenderer

4. **Verify DualListPanel Exists** (Finding 1)
   - Create component if missing
   - Or use alternative panel type

### Future Enhancements

5. **Implement Array Extraction in Template Resolver**
   - Support `{{positions.positions[*].symbol}}` syntax
   - This would enable more flexible patterns

6. **Standardize Date Field Names**
   - Use consistent field names across action types
   - Or document field name variations

---

**Test Simulation Complete**  
**Status:** 🚨 **2 CRITICAL FIXES REQUIRED** before testing  
**Estimated Fix Time:** 15 minutes (2 field name changes)

