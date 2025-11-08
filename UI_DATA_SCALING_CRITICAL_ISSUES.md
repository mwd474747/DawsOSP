# UI Data Scaling - Critical Inconsistencies Found

**Date:** 2025-11-08
**Status:** 🚨 CRITICAL - Multiple double conversion bugs detected
**Impact:** HIGH - Incorrect percentage displays across multiple pages
**Related:** DATA_SCALING_AUDIT_CRITICAL_BUGS.md (backend fixes completed)

---

## Executive Summary

Comprehensive review of frontend data handling revealed **CRITICAL INCONSISTENCIES** between backend data formats and frontend transformations. The frontend contains multiple instances of **incorrect ÷100 conversions** that don't match the backend's decimal format.

### Key Findings

🚨 **CRITICAL**: Frontend assumes backend returns **whole number percentages** (e.g., 14.5 for 14.5%)
✅ **REALITY**: Backend returns **decimal percentages** (e.g., 0.145 for 14.5%)
❌ **BUG**: Frontend divides by 100 again → values displayed are **100x too small**

**Affected Areas:**
- Portfolio overview metrics (change_pct, ytd_return)
- Holdings table (weight, return_pct)
- Transactions page (PnL percentages)
- Scenarios page (impact percentages)
- Optimizer page (turnover, tracking error)
- **Macro Cycles page**: Mixed correct and incorrect handling

**Severity**: Production-breaking for user decision-making

---

## Part 1: Backend Data Format (Ground Truth)

### Confirmed Backend Format

**Source:** [backend/app/services/metrics.py](backend/app/services/metrics.py#L87-L94)

```python
async def compute_twr(...) -> Dict:
    """
    Returns:
        Dict containing:
        - twr: Total return over period (decimal, e.g., 0.15 = 15%)
        - ann_twr: Annualized return (decimal)
        - vol: Annualized volatility (decimal)
        - sharpe: Sharpe ratio
        - sortino: Sortino ratio
    """
    # Line 180: Geometric linking
    twr = float(np.prod([1 + r for r in returns]) - 1)

    # Line 185: Annualization
    ann_twr = (1 + twr) ** ann_factor - 1

    # Returns: twr=0.15 for 15% return
```

**Format Confirmation:**
- **TWR (Time-Weighted Return)**: Decimal format (0.145 = 14.5%)
- **Change Percentage**: Decimal format (0.0235 = 2.35%)
- **Volatility**: Decimal format (0.15 = 15%)
- **Macro Indicators**: Decimal format (0.0408 = 4.08% for interest rates)
- **Weights/Allocations**: Decimal format (0.25 = 25%)

**Evidence:** Backend scaling bugs ALREADY FIXED in previous commit
(See: DATA_SCALING_AUDIT_CRITICAL_BUGS.md)

---

## Part 2: Frontend Data Transformation Bugs

### Utils.formatPercentage() Function

**Location:** [frontend/utils.js:55-58](frontend/utils.js#L55-L58)

```javascript
Utils.formatPercentage = function(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) return '-';
    return (value * 100).toFixed(decimals) + '%';  // ✅ CORRECT: Expects decimal input
};
```

**Expected Input:** Decimal (0.145)
**Processing:** ×100 → "14.50%"
**Status:** ✅ **CORRECT** - Function expects decimal input

---

## Part 3: Critical Bugs - Incorrect Double Division

### Bug Category 1: Portfolio Overview Page

**Location:** [frontend/pages.js:317](frontend/pages.js#L317), [frontend/pages.js:326](frontend/pages.js#L326)

#### Bug UI-SCALE-001: change_pct Double Division

```javascript
// Line 317 - INCORRECT ❌
formatPercentage((data.change_pct || 0.0235) / 100)

// Backend returns: 0.0235 (2.35%)
// Frontend divides by 100: 0.0235 ÷ 100 = 0.000235
// formatPercentage multiplies by 100: 0.000235 × 100 = 0.0235
// Display: "0.02%" ❌ WRONG (should be "2.35%")
```

**Impact:** Portfolio daily change displayed as **100x too small**

**Fix:**
```javascript
// CORRECT ✅
formatPercentage(data.change_pct || 0.0235)
```

---

#### Bug UI-SCALE-002: ytd_return Double Division

```javascript
// Line 326 - INCORRECT ❌
formatPercentage((data.ytd_return || 0.145) / 100)

// Backend returns: 0.145 (14.5%)
// Frontend divides by 100: 0.145 ÷ 100 = 0.00145
// formatPercentage multiplies by 100: 0.00145 × 100 = 0.145
// Display: "0.14%" ❌ WRONG (should be "14.50%")
```

**Impact:** YTD return displayed as **100x too small**

**Fix:**
```javascript
// CORRECT ✅
formatPercentage(data.ytd_return || 0.145)
```

---

### Bug Category 2: Holdings Table

**Location:** [frontend/pages.js:404](frontend/pages.js#L404), [frontend/pages.js:406](frontend/pages.js#L406)

#### Bug UI-SCALE-003: Holding Weight Double Division

```javascript
// Line 404 - INCORRECT ❌
formatPercentage((holding.weight || 0) / 100)

// Backend returns: 0.25 (25% weight)
// Frontend divides by 100: 0.25 ÷ 100 = 0.0025
// Display: "0.25%" ❌ WRONG (should be "25.00%")
```

**Impact:** Portfolio weights displayed as **100x too small**

---

#### Bug UI-SCALE-004: Holding Return Double Division

```javascript
// Line 406 - INCORRECT ❌
formatPercentage((holding.return_pct || 0) / 100)

// Backend returns: 0.0850 (8.5% return)
// Display: "0.09%" ❌ WRONG (should be "8.50%")
```

**Impact:** Holding returns displayed as **100x too small**

---

### Bug Category 3: Transactions Page

**Location:** [frontend/pages.js:561](frontend/pages.js#L561)

#### Bug UI-SCALE-005: Total PnL Percentage

```javascript
// Line 561 - INCORRECT ❌
formatPercentage(summaryData.totalPnLPct / 100)
```

**Impact:** Transaction profit/loss percentages **100x too small**

---

### Bug Category 4: Scenarios Page

**Location:** [frontend/pages.js:594](frontend/pages.js#L594)

#### Bug UI-SCALE-006: Scenario Impact Percentage

```javascript
// Line 594 - INCORRECT ❌
formatPercentage(scenario.impactPct / 100)

// Backend returns: -0.15 (-15% impact)
// Display: "-0.15%" ❌ WRONG (should be "-15.00%")
```

**Impact:** Scenario impacts displayed as **100x too small**

---

### Bug Category 5: Optimizer Page

**Location:** [frontend/pages.js:1766-1779](frontend/pages.js#L1766-L1779)

#### Bug UI-SCALE-007: Multiple Optimizer Metrics

```javascript
// Lines 1766-1779 - ALL INCORRECT ❌
formatPercentage((optimizationData.summary.turnoverPct || 0) / 100)     // Turnover
formatPercentage((optimizationData.summary.teImpact || 0) / 100)        // Tracking error
formatPercentage(optimizationData.impact.currentConcentration / 100)    // Current concentration
formatPercentage(optimizationData.impact.postConcentration / 100)       // Post concentration
formatPercentage(optimizationData.impact.concentrationDelta / 100)      // Delta

// All displays are 100x too small
```

**Impact:** Optimizer results completely wrong, user cannot make rebalancing decisions

---

### Bug Category 6: Policy Configuration

**Location:** [frontend/pages.js:1665-1668](frontend/pages.js#L1665-L1668)

#### Bug UI-SCALE-008: Policy Allocation Division

```javascript
// Lines 1665-1668 - INCORRECT ❌
policies.push({ type: 'target_allocation', category: 'risk', value: policyConfig.risk / 100 });
policies.push({ type: 'target_allocation', category: 'growth', value: policyConfig.growth / 100 });
policies.push({ type: 'target_allocation', category: 'dividend', value: policyConfig.dividend / 100 });
policies.push({ type: 'target_allocation', category: 'defensive', value: policyConfig.defensive / 100 });

// If policyConfig.risk = 40 (user enters "40%" in UI)
// Sends to backend: 40 ÷ 100 = 0.40 ✅ CORRECT (depends on UI input format)
// BUT: If policyConfig.risk = 0.40 (already decimal), sends 0.0040 ❌ WRONG
```

**Status:** ⚠️ **AMBIGUOUS** - Depends on UI input format
**Requires Investigation:** Check if policy form inputs return whole numbers or decimals

---

## Part 4: Macro Cycles Page - Mixed Handling (Interesting Case)

### CORRECT Handling - Macro Indicators

**Location:** [frontend/pages.js:980-985](frontend/pages.js#L980-L985)

```javascript
// Lines 980-985 - CORRECT ✅
{ label: 'GDP Growth', value: formatPercentage(ind.gdp_growth || 3.8), ... }
{ label: 'Inflation Rate', value: formatPercentage(ind.inflation || 3.24), ... }
{ label: 'Unemployment', value: formatPercentage(ind.unemployment || 4.3), ... }
{ label: 'Interest Rate', value: formatPercentage(ind.interest_rate || 4.08), ... }

// ✅ NO division by 100
// Backend returns: 0.038 (3.8% unemployment)
// formatPercentage: 0.038 × 100 = "3.80%"
```

**Status:** ✅ **CORRECT** - These work properly

---

### SUSPICIOUS - Fallback Values

**Location:** [frontend/pages.js:980-985](frontend/pages.js#L980-L985)

```javascript
// Fallback values look like whole numbers, not decimals
{ label: 'GDP Growth', value: formatPercentage(ind.gdp_growth || 3.8), ... }
//                                                                  ^^^ 3.8 or 0.038?

// Issue: Fallback values appear to be WHOLE NUMBERS (3.8 = 3.8%, not 0.038)
// If backend returns null, fallback is used:
// formatPercentage(3.8) → 3.8 × 100 = "380%" ❌ WRONG

// Ambiguity: Are these hardcoded fallbacks or real API responses?
```

**Status:** ⚠️ **SUSPICIOUS** - Fallback values inconsistent with decimal format

**Example:**
```javascript
// Line 980
ind.gdp_growth || ind.GDP_growth || 3.8

// If backend returns decimal: ind.gdp_growth = 0.038 ✅
// If backend returns null: fallback = 3.8 ❌ (will display as "380%")
```

---

### CORRECT - Empire Cycle Indicators

**Location:** [frontend/pages.js:1026-1032](frontend/pages.js#L1026-L1032)

```javascript
// Lines 1026-1032 - CORRECT ✅
{ label: 'Innovation Score', value: formatNumber(empire.innovation_rate * 100 || 100, 0), ... }
//                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
// Backend returns: 0.76 (76%)
// Manual multiplication: 0.76 × 100 = 76
// formatNumber: "76" (no further transformation)

{ label: 'Global GDP Share', value: formatPercentage(empire.global_trade_share || 0.2393), ... }
//                                   ^^^^^^^^^^^^^^^^^
// Backend returns: 0.2393 (23.93%)
// formatPercentage: 0.2393 × 100 = "23.93%"
```

**Status:** ✅ **CORRECT** - Proper decimal handling

---

### CORRECT - Long-Term Debt Cycle

**Location:** [frontend/pages.js:997](frontend/pages.js#L997), [frontend/pages.js:1008](frontend/pages.js#L1008)

```javascript
// Line 997, 1008 - SPECIAL CASE ✅
{ label: 'Total Debt/GDP', value: formatPercentage(ltdc.debt_to_gdp || 1.188), ... }

// Backend returns: 1.188 (118.8% debt-to-GDP ratio)
// formatPercentage: 1.188 × 100 = "118.80%"
// ✅ CORRECT - Debt ratios can exceed 100%
```

**Status:** ✅ **CORRECT** - Ratio format properly handled

---

## Part 5: Impact Assessment

### User Impact by Bug

| Bug ID | Location | Field | Impact | Severity |
|--------|----------|-------|--------|----------|
| UI-SCALE-001 | Portfolio Overview | Daily Change % | Values 100x too small | 🚨 CRITICAL |
| UI-SCALE-002 | Portfolio Overview | YTD Return | Values 100x too small | 🚨 CRITICAL |
| UI-SCALE-003 | Holdings Table | Position Weight | Values 100x too small | 🚨 CRITICAL |
| UI-SCALE-004 | Holdings Table | Position Return | Values 100x too small | 🚨 CRITICAL |
| UI-SCALE-005 | Transactions | Total PnL % | Values 100x too small | 🚨 HIGH |
| UI-SCALE-006 | Scenarios | Impact % | Values 100x too small | 🚨 CRITICAL |
| UI-SCALE-007 | Optimizer | All Metrics | Values 100x too small | 🚨 CRITICAL |
| UI-SCALE-008 | Policy Config | Allocations | Ambiguous (needs testing) | ⚠️ MEDIUM |

### Production Risk Assessment

**Critical Path Affected:**
1. ✅ User views portfolio → Sees 0.14% YTD instead of 14% → **Makes wrong investment decision**
2. ✅ User checks holdings → Sees 0.25% weight instead of 25% → **Misunderstands allocation**
3. ✅ User runs scenario → Sees -0.15% impact instead of -15% → **Underestimates risk**
4. ✅ User optimizes portfolio → All metrics wrong → **Cannot rebalance properly**

**Impact on Business Logic:** None (backend correct)
**Impact on UI/UX:** 🚨 **SEVERE** - All percentage displays broken

---

## Part 6: Root Cause Analysis

### Why Did This Happen?

**Timeline:**
1. **Original Implementation**: Frontend assumed backend returns whole numbers (4.5 for 4.5%)
2. **Backend Refactor**: Backend standardized on decimal format (0.045 for 4.5%)
3. **Frontend NOT Updated**: Frontend still divides by 100 before calling formatPercentage
4. **Result**: Double conversion (backend ÷100, frontend ÷100 again)

**Similar to Backend Bug:**
- Backend had same issue with macro indicators (see DATA_SCALING_AUDIT_CRITICAL_BUGS.md)
- Root cause: Database format changed (FRED transformation), consumers not updated

---

## Part 7: Fix Strategy

### Principles

1. **Backend is Source of Truth**: Backend returns decimals (0.145 = 14.5%)
2. **formatPercentage Expects Decimals**: Function already correct (multiplies by 100)
3. **Remove All ÷100 Before formatPercentage**: Consumers should pass decimals directly

### Fix Pattern

**BEFORE (WRONG):**
```javascript
formatPercentage((data.change_pct || 0.0235) / 100)  // ❌ Double conversion
```

**AFTER (CORRECT):**
```javascript
formatPercentage(data.change_pct || 0.0235)  // ✅ Direct usage
```

---

## Part 8: Fix Implementation Plan

### Phase 1: Critical Fixes (Pages with User Decision Impact)

**Priority:** 🚨 P0 - Production-breaking

**Files to Fix:**
1. [frontend/pages.js](frontend/pages.js)

**Changes Required:**

#### 1. Portfolio Overview (Lines 317, 326)
```javascript
// BEFORE ❌
formatPercentage((data.change_pct || 0.0235) / 100)
formatPercentage((data.ytd_return || 0.145) / 100)

// AFTER ✅
formatPercentage(data.change_pct || 0.0235)
formatPercentage(data.ytd_return || 0.145)
```

#### 2. Holdings Table (Lines 404, 406)
```javascript
// BEFORE ❌
formatPercentage((holding.weight || 0) / 100)
formatPercentage((holding.return_pct || 0) / 100)

// AFTER ✅
formatPercentage(holding.weight || 0)
formatPercentage(holding.return_pct || 0)
```

#### 3. Scenarios Page (Line 594)
```javascript
// BEFORE ❌
formatPercentage(scenario.impactPct / 100)

// AFTER ✅
formatPercentage(scenario.impactPct)
```

#### 4. Optimizer Page (Lines 1766-1779)
```javascript
// BEFORE ❌
formatPercentage((optimizationData.summary.turnoverPct || 0) / 100)
formatPercentage((optimizationData.summary.teImpact || 0) / 100)
formatPercentage(optimizationData.impact.currentConcentration / 100)
formatPercentage(optimizationData.impact.postConcentration / 100)
formatPercentage(optimizationData.impact.concentrationDelta / 100)

// AFTER ✅
formatPercentage(optimizationData.summary.turnoverPct || 0)
formatPercentage(optimizationData.summary.teImpact || 0)
formatPercentage(optimizationData.impact.currentConcentration)
formatPercentage(optimizationData.impact.postConcentration)
formatPercentage(optimizationData.impact.concentrationDelta)
```

#### 5. Transactions Page (Line 561)
```javascript
// BEFORE ❌
formatPercentage(summaryData.totalPnLPct / 100)

// AFTER ✅
formatPercentage(summaryData.totalPnLPct)
```

**Total Changes:** 11 lines across 1 file

---

### Phase 2: Investigation Required

**Priority:** ⚠️ P1 - Ambiguous cases

#### 1. Policy Configuration (Lines 1665-1668)

**Investigation Needed:**
- Check policy form inputs: Do they return whole numbers (40) or decimals (0.40)?
- Check backend policy endpoint: Does it expect whole numbers or decimals?
- Test with live data

**Possible Fixes:**
```javascript
// If UI inputs are whole numbers (user enters "40"):
policies.push({ type: 'target_allocation', category: 'risk', value: policyConfig.risk / 100 });  // ✅ Keep as-is

// If UI inputs are already decimals (user enters "0.40" or slider returns 0.40):
policies.push({ type: 'target_allocation', category: 'risk', value: policyConfig.risk });  // ✅ Remove division
```

#### 2. Macro Cycles Fallback Values

**Investigation Needed:**
- Are fallback values (3.8, 4.3, etc.) whole numbers or decimals?
- Should fallbacks match backend format (0.038 instead of 3.8)?

**Possible Fix:**
```javascript
// BEFORE (ambiguous)
{ label: 'GDP Growth', value: formatPercentage(ind.gdp_growth || 3.8), ... }

// AFTER (consistent with decimal format)
{ label: 'GDP Growth', value: formatPercentage(ind.gdp_growth || 0.038), ... }
```

---

### Phase 3: Validation & Testing

**Test Cases:**

1. **Portfolio Overview**
   - Load portfolio with 14.5% YTD return
   - Verify display shows "14.50%" not "0.14%"

2. **Holdings Table**
   - Load portfolio with 25% weight position
   - Verify display shows "25.00%" not "0.25%"

3. **Scenarios**
   - Run recession scenario with -15% impact
   - Verify display shows "-15.00%" not "-0.15%"

4. **Optimizer**
   - Run optimizer with 5% turnover
   - Verify display shows "5.00%" not "0.05%"

5. **Policy Config**
   - Set 40% risk allocation
   - Verify backend receives 0.40 (decimal)

---

## Part 9: Documentation Updates

### Update DATA_SCALE_TYPE_DOCUMENTATION.md

Add section:

```markdown
## UI Data Flow

### Frontend Formatting Functions

**formatPercentage(value)** - [frontend/utils.js:55](frontend/utils.js#L55)
- **Input:** Decimal (0.145)
- **Processing:** value × 100
- **Output:** "14.50%"

**CRITICAL RULE:**
✅ **DO**: Pass decimals directly to formatPercentage
❌ **DON'T**: Divide by 100 before calling formatPercentage

**Example:**
```javascript
// Backend returns: 0.145 (14.5%)
formatPercentage(data.ytd_return)  // ✅ "14.50%"
formatPercentage(data.ytd_return / 100)  // ❌ "0.14%" (WRONG)
```
```

---

## Part 10: Summary

### Critical Bugs Found: 8

| Category | Count | Severity |
|----------|-------|----------|
| Double conversion (÷100 error) | 7 | 🚨 CRITICAL |
| Ambiguous (needs investigation) | 1 | ⚠️ MEDIUM |
| Suspicious fallback values | ~6 | ⚠️ LOW |

### Fix Complexity: LOW

- **Lines to change:** 11 (simple find-replace of `/ 100` removal)
- **Files affected:** 1 ([frontend/pages.js](frontend/pages.js))
- **Risk level:** LOW (removal of incorrect transformation)
- **Testing required:** Manual verification of 5 key pages

### Recommended Action

✅ **IMMEDIATE FIX** (Phase 1): Remove all `/ 100` before formatPercentage calls
⚠️ **FOLLOW-UP** (Phase 2): Investigate policy config and fallback values
📝 **DOCUMENTATION** (Phase 3): Update DATA_SCALE_TYPE_DOCUMENTATION.md

---

## Files Affected

**Frontend:**
- [frontend/pages.js](frontend/pages.js) (11 lines to fix)
- [frontend/utils.js](frontend/utils.js) (reference - no changes needed)

**Documentation:**
- [DATA_SCALE_TYPE_DOCUMENTATION.md](DATA_SCALE_TYPE_DOCUMENTATION.md) (add UI section)

---

**Analysis Completed:** 2025-11-08
**Next Step:** Execute Phase 1 fixes (11 line changes)
**Estimated Fix Time:** 30 minutes (changes) + 1 hour (testing)

