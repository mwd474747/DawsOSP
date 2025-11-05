# Field Naming System Analysis & Cleanup Plan

**Date:** January 14, 2025  
**Status:** 🔍 **COMPREHENSIVE ANALYSIS COMPLETE**  
**Purpose:** Understand the quantity field naming system, identify inconsistencies, and create cleanup plan

---

## 📊 Executive Summary

A field naming refactor was completed that changed database column names from `qty_open`/`qty_original` to `quantity_open`/`quantity_original`. However, the **agent return structure** was standardized to use `quantity` (not `quantity_open` or `qty`). Some code was updated to support both field names during transition, but **corporate actions capabilities were missed**, causing the current bug.

**Key Findings:**
- ✅ **Database**: Uses `quantity_open` (refactored from `qty_open`)
- ✅ **ledger.positions**: Returns `quantity` (standardized)
- ✅ **pricing.apply_pack**: Supports both `quantity` and `qty` (transitional support)
- ❌ **corporate_actions.upcoming**: Uses `qty` (WRONG - should use `quantity`)
- ❌ **corporate_actions.calculate_impact**: Uses `qty` (WRONG - should use `quantity`)

---

## 🔍 Field Naming System Understanding

### Layer 1: Database Schema ✅ **STANDARDIZED**

**Database Column Names:**
- `lots.quantity_open` - Current open quantity (refactored from `qty_open`)
- `lots.quantity_original` - Original quantity when lot was created (refactored from `qty_original`)
- `lots.quantity` - Base quantity field (still exists for backwards compatibility)

**Evidence:**
```sql
-- Migration 001: Standardize field names
ALTER TABLE lots RENAME COLUMN qty_open TO quantity_open;
ALTER TABLE lots RENAME COLUMN quantity_original TO quantity_original;
```

**Status:** ✅ **COMPLETE** - Database uses full names

---

### Layer 2: Agent Return Structures ✅ **STANDARDIZED TO `quantity`**

**Standard Pattern:**
All agent capabilities that return positions use `quantity` as the field name (not `quantity_open` or `qty`).

#### 2.1 `ledger.positions` Capability ✅ **CORRECT**

**File:** `backend/app/agents/financial_analyst.py` lines 135-278

**Implementation:**
```python
# SQL Query (line 201)
SELECT
    l.security_id,
    l.symbol,
    l.quantity_open AS qty,  # ← Database column is quantity_open, aliased as qty in SQL
    l.cost_basis,
    l.currency,
    p.base_currency
FROM lots l
WHERE l.portfolio_id = $1
  AND l.is_open = true
  AND l.quantity_open > 0

# Return Structure (line 225)
positions.append({
    "security_id": str(row["security_id"]),
    "symbol": row["symbol"] or "UNKNOWN",
    "quantity": qty,  # ← Returns "quantity" (standardized name)
    "cost_basis": cost_basis,
    "currency": row["currency"] or portfolio_base_currency,
    "base_currency": portfolio_base_currency,
})
```

**Return Structure:**
```python
{
    "positions": [
        {
            "security_id": "uuid",
            "symbol": "AAPL",
            "quantity": Decimal("100"),  # ← Standardized to "quantity"
            "cost_basis": Decimal("15000.00"),
            "currency": "USD",
            "base_currency": "USD"
        }
    ],
    "total_positions": 1,
    "base_currency": "USD"
}
```

**Status:** ✅ **CORRECT** - Uses `quantity` field name

---

### Layer 3: Code That Consumes Agent Results ⚠️ **MIXED STATE**

#### 3.1 `pricing.apply_pack` ✅ **SUPPORTS BOTH (Transitional)**

**File:** `backend/app/agents/financial_analyst.py` line 392

**Implementation:**
```python
qty = pos.get("quantity", pos.get("qty", Decimal("0")))  # Support both field names
```

**Rationale:** Supports both `quantity` (new) and `qty` (old) during transition period.

**Status:** ✅ **CORRECT** - Supports both, but should be updated to only use `quantity` after cleanup

---

#### 3.2 `corporate_actions.upcoming` ❌ **USES WRONG FIELD**

**File:** `backend/app/agents/data_harvester.py` line 2839

**Current Implementation:**
```python
positions = state.get("positions", {}).get("positions", [])
symbols = [p.get("symbol") for p in positions if p.get("qty", 0) > 0]  # ← WRONG: uses "qty"
```

**Problem:**
- `ledger.positions` returns `quantity` (not `qty`)
- `p.get("qty", 0)` always returns `0` (default)
- All positions filtered out → Empty symbols array

**Fix Required:**
```python
symbols = [p.get("symbol") for p in positions if p.get("quantity", 0) > 0]  # ← Use "quantity"
```

**Status:** ❌ **NEEDS FIX**

---

#### 3.3 `corporate_actions.calculate_impact` ❌ **USES WRONG FIELD**

**File:** `backend/app/agents/data_harvester.py` lines 2993, 2996

**Current Implementation:**
```python
positions = state.get("positions", {}).get("positions", [])
holdings = {p.get("symbol"): float(p.get("qty", 0)) for p in positions}  # ← WRONG: uses "qty"
```

**Also in list conversion:**
```python
holdings = {p.get("symbol"): float(p.get("qty", 0)) for p in holdings}  # ← WRONG: uses "qty"
```

**Problem:**
- Same issue as `corporate_actions.upcoming`
- `p.get("qty", 0)` always returns `0`
- All holdings are zero → No impact calculations

**Fix Required:**
```python
holdings = {p.get("symbol"): float(p.get("quantity", 0)) for p in positions}  # ← Use "quantity"
holdings = {p.get("symbol"): float(p.get("quantity", 0)) for p in holdings}  # ← Use "quantity"
```

**Status:** ❌ **NEEDS FIX**

---

## 🔍 Complete Field Name Usage Analysis

### Database Layer

| Location | Field Name | Usage | Status |
|----------|-----------|-------|--------|
| `lots` table | `quantity_open` | Current open quantity | ✅ Correct |
| `lots` table | `quantity_original` | Original quantity | ✅ Correct |
| `lots` table | `quantity` | Base quantity (legacy) | ⚠️ Deprecated but still exists |

### Agent Return Layer

| Capability | Returns Field | Status |
|------------|--------------|--------|
| `ledger.positions` | `quantity` | ✅ Correct |
| `pricing.apply_pack` | `quantity` | ✅ Correct |
| `macro.run_scenario` | `quantity` | ✅ Correct |

### Code Consumption Layer

| Location | Field Used | Expected | Status |
|----------|-----------|----------|--------|
| `pricing.apply_pack` | `quantity` or `qty` | `quantity` | ✅ Supports both (transitional) |
| `corporate_actions.upcoming` | `qty` | `quantity` | ❌ **WRONG** |
| `corporate_actions.calculate_impact` | `qty` | `quantity` | ❌ **WRONG** |

---

## 🔧 Cleanup Plan

### Priority 1: Fix Corporate Actions (IMMEDIATE)

**Files to Update:**
1. `backend/app/agents/data_harvester.py` line 2839
2. `backend/app/agents/data_harvester.py` line 2993
3. `backend/app/agents/data_harvester.py` line 2996

**Changes:**
```python
# Line 2839: Change from qty to quantity
symbols = [p.get("symbol") for p in positions if p.get("quantity", 0) > 0]

# Line 2993: Change from qty to quantity
holdings = {p.get("symbol"): float(p.get("quantity", 0)) for p in positions}

# Line 2996: Change from qty to quantity
holdings = {p.get("symbol"): float(p.get("quantity", 0)) for p in holdings}
```

**Impact:** Fixes corporate actions feature immediately

---

### Priority 2: Remove Transitional Support (CLEANUP)

**File:** `backend/app/agents/financial_analyst.py` line 392

**Current:**
```python
qty = pos.get("quantity", pos.get("qty", Decimal("0")))  # Support both field names
```

**Change To:**
```python
qty = pos.get("quantity", Decimal("0"))  # Only use quantity (standardized)
```

**Rationale:** 
- All agent capabilities now return `quantity`
- No code should be using `qty` anymore
- Removing transitional support simplifies code

**Impact:** Low risk - if any code still uses `qty`, it will fail explicitly (better than silent bug)

---

### Priority 3: Verify All Usages (VALIDATION)

**Search for remaining `qty` usage in agent return consumption:**

**Findings:**
1. ✅ `financial_analyst.py` line 219: `row["qty"]` - **CORRECT** (reading from SQL alias `AS qty`)
2. ✅ `trade_execution.py` line 564: `SUM(quantity_open) as qty` - **CORRECT** (SQL alias, then reads `row["qty"]`)
3. ✅ `trades.py` lines 307, 355, 586: Uses `qty` from service results - **OK** (service layer, not agent layer)
4. ❌ `data_harvester.py` lines 2839, 2993, 2996: Uses `qty` from agent results - **BUG** (should use `quantity`)

**Conclusion:**
- Only `corporate_actions` capabilities have bugs
- Other usages are correct (SQL aliases or service layer)
- Service layer can use its own field names (internal API)
- Agent layer should use standardized `quantity` field

---

## 📋 Field Naming Standard

### Standard Field Names

**Agent Return Structures:**
- ✅ `quantity` - Use this for all position quantities
- ❌ `qty` - Do not use (deprecated)
- ❌ `quantity_open` - Do not use (database column only)

**Database Column Names:**
- ✅ `quantity_open` - Current open quantity
- ✅ `quantity_original` - Original quantity
- ⚠️ `quantity` - Legacy field (deprecated but still exists)

**Rationale:**
- Agents return data structures, not database rows
- Agent return structures should use standardized field names
- Database column names are separate from agent return structures

---

## 🧪 Testing Plan

### Test 1: Verify Corporate Actions Works

**Steps:**
1. Fix field names in `corporate_actions.upcoming` and `corporate_actions.calculate_impact`
2. Execute pattern: `corporate_actions_upcoming`
3. Verify symbols are extracted correctly
4. Verify actions are filtered by portfolio holdings
5. Verify impact calculations include portfolio quantities

**Expected Result:**
- Symbols extracted from positions
- Actions filtered to portfolio holdings only
- Impact calculations show portfolio quantities and dollar impact

---

### Test 2: Verify No Regressions

**Steps:**
1. Remove transitional support from `pricing.apply_pack`
2. Run all patterns that use `pricing.apply_pack`
3. Verify no errors occur

**Expected Result:**
- All patterns work correctly
- No errors about missing `qty` field

---

## ✅ Summary

**Current State:**
- ✅ Database: Standardized to `quantity_open`/`quantity_original`
- ✅ Agents: Standardized to return `quantity`
- ⚠️ Code: Most code updated, but `corporate_actions` missed

**Required Fixes:**
1. **IMMEDIATE**: Fix `corporate_actions.upcoming` (line 2839)
2. **IMMEDIATE**: Fix `corporate_actions.calculate_impact` (lines 2993, 2996)
3. **CLEANUP**: Remove transitional support from `pricing.apply_pack` (line 392)

**Impact:**
- Fixes corporate actions feature
- Completes field naming standardization
- Removes technical debt from transitional code

---

## 📝 Notes

**Why This Happened:**
- Field naming refactor was done incrementally
- `pricing.apply_pack` was updated with transitional support
- `corporate_actions` capabilities were added later and not updated to use standardized field names

**Lesson Learned:**
- When refactoring field names, update all consumers immediately
- Don't leave transitional support code indefinitely
- Add tests to catch field name mismatches

