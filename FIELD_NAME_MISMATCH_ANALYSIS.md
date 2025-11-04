# Field Name Mismatch Analysis: `qty` vs `qty_open`

**Date:** November 3, 2025  
**Purpose:** Understand why field name mismatch exists and impact on dependencies  
**Status:** 🔍 **ANALYSIS ONLY** - No code changes

---

## 📊 Executive Summary

**Root Cause:** Inconsistent field naming between database schema (`qty_open`) and agent capability return structures (`qty`).

**Source of Truth:** `ledger.positions` capability returns `qty` (not `qty_open`). This is the standard used throughout the system.

**Impact:** `corporate_actions` capabilities incorrectly expect `qty_open`, causing the mismatch. Fixing this will **NOT** break any dependencies.

**Recommendation:** Change `corporate_actions` to use `qty` to align with `ledger.positions` return structure.

---

## 🔍 Field Name Usage Across System

### 1. Database Schema (`lots` table)

**Field Name:** `qty_open`  
**Purpose:** Stores open quantity for each tax lot

**SQL Query Example:**
```sql
SELECT
    l.security_id,
    l.symbol,
    l.qty_open AS qty,  -- Database field is qty_open
    l.cost_basis,
    l.currency
FROM lots l
WHERE l.portfolio_id = $1
  AND l.is_open = true
  AND l.qty_open > 0
```

**Location:** `financial_analyst.py:168`

**Key Finding:** Database uses `qty_open`, but SQL aliases it as `qty` in the query result.

---

### 2. `ledger.positions` Capability (Source of Truth)

**Capability:** `financial_analyst.ledger_positions`  
**Return Structure:**
```python
{
    "portfolio_id": "...",
    "asof_date": "2025-11-03",
    "positions": [
        {
            "security_id": "...",
            "symbol": "AAPL",
            "qty": Decimal("100"),  # ← Returns "qty", not "qty_open"
            "cost_basis": Decimal("15000.00"),
            "currency": "USD",
            "base_currency": "USD"
        },
        ...
    ],
    "total_positions": 3,
    "base_currency": "USD"
}
```

**Implementation:**
```python
# financial_analyst.py:168-192
# SQL: l.qty_open AS qty
qty = Decimal(str(row["qty"]))  # Reads from aliased "qty" column
positions.append({
    "security_id": str(row["security_id"]),
    "symbol": row["symbol"] or "UNKNOWN",
    "qty": qty,  # ← Returns "qty"
    ...
})
```

**Key Finding:** `ledger.positions` is the **source of truth** for position field names. It returns `qty`, not `qty_open`.

---

### 3. `pricing.apply_pack` Capability (Downstream Consumer)

**Capability:** `financial_analyst.pricing_apply_pack`  
**Input:** Takes positions from `ledger.positions`  
**Field Access:**
```python
# financial_analyst.py:313
qty = pos.get("qty", Decimal("0"))  # ← Reads "qty"
```

**Return Structure:**
```python
# financial_analyst.py:358-366
valued_position = {
    **pos,  # ← Spreads all fields from input, including "qty"
    "price": price,
    "value_local": value_local,
    "value": value_base,
    "fx_rate": fx_rate,
    "base_currency": base_currency,
}
```

**Key Finding:** `pricing.apply_pack` correctly uses `qty` and passes it through via `**pos`.

---

### 4. Patterns Using `ledger.positions`

**All Patterns Access Positions Correctly:**

**portfolio_overview.json:**
```json
{
  "capability": "pricing.apply_pack",
  "args": {
    "positions": "{{positions.positions}}"  // Uses qty from ledger.positions
  }
}
```

**policy_rebalance.json:**
```json
{
  "capability": "pricing.apply_pack",
  "args": {
    "positions": "{{positions.positions}}"  // Uses qty from ledger.positions
  }
}
```

**news_impact_analysis.json:**
```json
{
  "capability": "news.compute_portfolio_impact",
  "args": {
    "positions": "{{positions.positions}}"  // Uses qty from ledger.positions
  }
}
```

**Key Finding:** All existing patterns correctly use positions from `ledger.positions`, which returns `qty`.

---

### 5. Other Capabilities Using Positions

**portfolio.sector_allocation:**
```python
# financial_analyst.py:763
position_list = positions["positions"]  # Gets positions from valued_positions
# Uses pos.get("qty") implicitly via position data structure
```

**Key Finding:** Uses `qty` correctly (via `pricing.apply_pack` output).

---

### 6. `get_position_details` Capability (Direct DB Access)

**Capability:** `financial_analyst.get_position_details`  
**Database Access:**
```python
# financial_analyst.py:1120-1165
# Directly queries lots table
lots = await conn.fetch("""
    SELECT l.*, s.symbol, s.currency
    FROM lots l
    WHERE l.qty_open > 0  # ← Uses qty_open from DB
""")

total_qty = sum(Decimal(str(lot["qty_open"])) for lot in lots)  # ← Uses qty_open
```

**Return Structure:**
```python
# financial_analyst.py:1174-1186
result = {
    "symbol": symbol,
    "security_id": str(security_uuid),
    "qty_open": float(total_qty),  # ← Returns "qty_open"
    "avg_cost": float(avg_cost),
    "current_price": float(current_price),
    ...
}
```

**Key Finding:** `get_position_details` is a **different capability** that directly accesses the database. It returns `qty_open`, but this is **not used by patterns** - it's a standalone capability.

**Pattern Usage:**
- `holding_deep_dive.json:149` references `{{position.qty_open}}` - this is from `get_position_details`, not `ledger.positions`.

**Key Finding:** This is **NOT a dependency issue** - `get_position_details` is a separate capability with its own return structure.

---

### 7. UI Components

**Holdings API (`/api/holdings`):**
```python
# combined_server.py:1776
qty = float(pos.get("qty", 0))  # ← Uses "qty" from backend
holdings.append({
    "quantity": qty,  # ← Converts to "quantity" for UI
    ...
})
```

**Key Finding:** UI correctly uses `qty` from backend and converts it to `quantity` for display.

**UI Display:**
```javascript
// full_ui.html:11501, 11578
// UI checks both field names for backward compatibility
formatNumber(selectedSecurity.qty_open || selectedSecurity.quantity || 0)
formatNumber(position.qty_open || position.quantity || 0)
```

**Key Finding:** UI has fallback logic to handle both field names, but primary usage is `quantity` (from API conversion).

---

### 8. Corporate Actions Capabilities (THE MISMATCH)

**Location:** `data_harvester.py:2823, 2944`

**Current Implementation:**
```python
# corporate_actions_upcoming (line 2823)
symbols = [p.get("symbol") for p in positions if p.get("qty_open", 0) > 0]
# ❌ WRONG: Expects "qty_open"

# corporate_actions_calculate_impact (line 2944)
holdings = {p.get("symbol"): float(p.get("qty_open", 0)) for p in positions}
# ❌ WRONG: Expects "qty_open"
```

**Expected Input:**
- Positions from `ledger.positions` (Step 1 in pattern)
- `ledger.positions` returns `qty`, not `qty_open`

**Impact:**
- ❌ No symbols extracted (all positions filtered out)
- ❌ All holdings quantities = 0.0
- ❌ Dividend impact calculation broken

---

## 🔍 Dependency Analysis

### What Uses `ledger.positions` Output?

**Patterns:**
1. ✅ `portfolio_overview.json` - Uses `{{positions.positions}}` → `pricing.apply_pack` → Uses `qty` correctly
2. ✅ `policy_rebalance.json` - Uses `{{positions.positions}}` → `pricing.apply_pack` → Uses `qty` correctly
3. ✅ `news_impact_analysis.json` - Uses `{{positions.positions}}` → `news.compute_portfolio_impact` → Uses `qty` correctly
4. ✅ `portfolio_scenario_analysis.json` - Uses `{{positions.positions}}` → `pricing.apply_pack` → Uses `qty` correctly
5. ✅ `cycle_deleveraging_scenarios.json` - Uses `{{positions.positions}}` → `pricing.apply_pack` → Uses `qty` correctly
6. ❌ `corporate_actions_upcoming.json` - Uses `{{positions.positions}}` → **EXPECTS `qty_open`** (WRONG)

**Capabilities:**
1. ✅ `pricing.apply_pack` - Uses `qty` correctly
2. ✅ `portfolio.sector_allocation` - Uses `qty` correctly (via `pricing.apply_pack`)
3. ✅ `portfolio.historical_nav` - Doesn't use positions directly
4. ✅ `metrics.compute_twr` - Doesn't use positions directly
5. ❌ `corporate_actions.upcoming` - **EXPECTS `qty_open`** (WRONG)
6. ❌ `corporate_actions.calculate_impact` - **EXPECTS `qty_open`** (WRONG)

**Key Finding:** **ALL existing patterns and capabilities use `qty` correctly**. Only `corporate_actions` capabilities incorrectly expect `qty_open`.

---

### What Would Break If We Change `corporate_actions`?

**Answer: NOTHING** ✅

**Reasoning:**
1. `corporate_actions.upcoming` is only used by `corporate_actions_upcoming.json` pattern
2. `corporate_actions.calculate_impact` is only used by `corporate_actions_upcoming.json` pattern
3. No other patterns or capabilities depend on these capabilities
4. Changing `qty_open` → `qty` aligns with the standard used everywhere else

---

### What Would Break If We Change `ledger.positions` to Return `qty_open`?

**Answer: EVERYTHING** ❌

**Reasoning:**
1. `pricing.apply_pack` expects `qty` (line 313)
2. All patterns use positions from `ledger.positions` → `pricing.apply_pack`
3. UI expects `qty` from backend (line 1776)
4. Changing would break all existing patterns and capabilities

**Key Finding:** **DO NOT** change `ledger.positions` - it's the source of truth and changing it would break everything.

---

## 🎯 Root Cause Analysis

### Why Does The Mismatch Exist?

**Theory 1: Copy-Paste Error**
- Developer saw `get_position_details` returns `qty_open`
- Assumed `ledger.positions` also returns `qty_open`
- Copied field name without checking actual return structure

**Theory 2: Database Schema Confusion**
- Developer saw database uses `qty_open`
- Assumed agent capabilities also use `qty_open`
- Didn't notice SQL aliases `qty_open AS qty`

**Theory 3: Incomplete Implementation**
- Corporate actions feature was implemented quickly
- Developer didn't check existing patterns for field name usage
- Used database field name instead of capability return structure

**Most Likely:** Theory 1 or 3 - developer didn't verify the actual return structure from `ledger.positions`.

---

## 📋 Field Name Standard

### Current Standard (Established)

**Source of Truth:** `ledger.positions` capability  
**Field Name:** `qty`  
**Usage:** All existing patterns and capabilities use `qty`

**Examples:**
- `pricing.apply_pack` → Uses `qty` ✅
- `portfolio.sector_allocation` → Uses `qty` ✅
- All patterns → Use `qty` ✅

---

### Exception (Not a Dependency Issue)

**`get_position_details` Capability:**
- Direct database access
- Returns `qty_open`
- Used by `holding_deep_dive.json` pattern
- **NOT used by other patterns or capabilities**
- **Separate capability, separate return structure**

**Key Finding:** This is **NOT a dependency issue** - it's a different capability with its own return structure.

---

## 🔧 Recommended Fix

### Fix 1: Update `corporate_actions_upcoming` (Line 2823)

**Current:**
```python
symbols = [p.get("symbol") for p in positions if p.get("qty_open", 0) > 0]
```

**Fixed:**
```python
symbols = [p.get("symbol") for p in positions if p.get("qty", 0) > 0]
```

**Rationale:**
- Aligns with `ledger.positions` return structure
- Matches all other capabilities
- No dependencies broken

---

### Fix 2: Update `corporate_actions_calculate_impact` (Line 2944)

**Current:**
```python
holdings = {p.get("symbol"): float(p.get("qty_open", 0)) for p in positions}
```

**Fixed:**
```python
holdings = {p.get("symbol"): float(p.get("qty", 0)) for p in positions}
```

**Rationale:**
- Aligns with `ledger.positions` return structure
- Matches all other capabilities
- No dependencies broken

---

## ✅ Validation Checklist

### Before Fix

- [ ] `corporate_actions.upcoming` extracts symbols from `ledger.positions` → **FAILS** (expects `qty_open`, gets `qty`)
- [ ] `corporate_actions.calculate_impact` extracts holdings from `ledger.positions` → **FAILS** (expects `qty_open`, gets `qty`)
- [ ] All existing patterns continue to work → **PASS** (they use `qty` correctly)

### After Fix

- [ ] `corporate_actions.upcoming` extracts symbols from `ledger.positions` → **PASS** (uses `qty`)
- [ ] `corporate_actions.calculate_impact` extracts holdings from `ledger.positions` → **PASS** (uses `qty`)
- [ ] All existing patterns continue to work → **PASS** (no changes to them)
- [ ] `get_position_details` continues to work → **PASS** (separate capability, unaffected)

---

## 📊 Impact Assessment

### Breaking Changes: **NONE** ✅

**Reasoning:**
1. `corporate_actions` capabilities are only used by `corporate_actions_upcoming.json` pattern
2. No other patterns or capabilities depend on `corporate_actions`
3. Changing `qty_open` → `qty` aligns with the standard
4. All existing patterns and capabilities continue to work

---

### Risk Level: **LOW** ✅

**Reasoning:**
1. Simple field name change (2 lines of code)
2. No architectural changes
3. No database changes
4. No pattern changes
5. Easy to test and verify

---

## 🎯 Summary

### Field Name Standard

**Source of Truth:** `ledger.positions` capability  
**Standard Field Name:** `qty`  
**Usage:** All existing patterns and capabilities use `qty` correctly

### The Mismatch

**Location:** `corporate_actions` capabilities  
**Issue:** Expects `qty_open` but receives `qty` from `ledger.positions`  
**Impact:** Feature doesn't work (no symbols extracted, all quantities = 0.0)

### The Fix

**Change:** `qty_open` → `qty` in `corporate_actions` capabilities  
**Impact:** **NO BREAKING CHANGES** - aligns with standard  
**Risk:** **LOW** - simple field name change

---

**Analysis Complete**  
**Status:** ✅ **SAFE TO FIX** - No dependencies will break  
**Recommendation:** Proceed with fixes immediately

