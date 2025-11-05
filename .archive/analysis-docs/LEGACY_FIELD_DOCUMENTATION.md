# Legacy Field Documentation: `lots.quantity`

**Date:** January 14, 2025  
**Status:** ✅ **DOCUMENTATION COMPLETE**  
**Purpose:** Document the purpose, history, and deprecation plan for the legacy `quantity` field

---

## 📊 Executive Summary

The `lots` table contains a legacy `quantity` field that is **deprecated** but maintained for backwards compatibility. This document explains its history, purpose, and migration plan.

**Current Status:**
- ✅ **DEPRECATED** - Should not be used in new code
- ✅ **MAINTAINED** - Still exists in database for backwards compatibility
- ⚠️ **BUGS** - Some code still uses this field (scenarios.py)

**Recommendation:** Update all queries to use `quantity_open` instead of `quantity`. Do not drop the field yet.

---

## 📜 History

### Migration Timeline

**Original State (Pre-Migration 007):**
- `lots` table had `quantity` and `is_open` fields
- `quantity` represented total quantity in lot
- `is_open` boolean indicated if lot was open

**Migration 007 (2025-10-23):**
- Added `qty_open` and `qty_original` for partial lot tracking
- `qty_original`: Original quantity when lot was created
- `qty_open`: Remaining open quantity (decreases on sells)
- `quantity` field kept for backwards compatibility

**Migration 001 (2025-11-04):**
- Renamed `qty_open` → `quantity_open`
- Renamed `qty_original` → `quantity_original`
- `quantity` field still kept for backwards compatibility

**Current State:**
- `quantity_open`: Current open quantity (✅ USE THIS)
- `quantity_original`: Original quantity (✅ USE THIS)
- `quantity`: Legacy field (⚠️ DEPRECATED)

---

## 🎯 Purpose

### Original Purpose

The `quantity` field originally represented:
- **Total quantity** in a lot
- Used alongside `is_open` boolean to track lot status

**Limitation:** Could not handle partial lot reductions (e.g., sell 60 of 100 shares)

---

### Why It Was Replaced

**Problem:** Tax lot accounting requires partial lot tracking

**Example:**
1. Buy 100 shares of AAPL (create lot with `quantity=100`, `is_open=true`)
2. Sell 60 shares (need to track: `quantity_open=40`, `quantity_original=100`)
3. Sell 40 shares (close lot: `quantity_open=0`, `is_open=false`)

**Solution:** Migration 007 added `qty_open` and `qty_original` to support partial lot tracking

---

### Why It Was Kept

**Reason:** Backwards compatibility

**Migration 007 Notes:**
> "The old 'quantity' and 'is_open' fields are kept for backwards compatibility but should be considered deprecated."

**Status:** Still maintained in database, but deprecated in code

---

## 🔍 Current Usage

### Database Schema

**Table:** `lots`

**Columns:**
```sql
quantity NUMERIC(20,8)  -- ⚠️ DEPRECATED: Use quantity_open instead
quantity_open NUMERIC(20,8)  -- ✅ USE THIS: Current open quantity
quantity_original NUMERIC(20,8)  -- ✅ USE THIS: Original quantity
```

**Status:** All three fields exist in database

---

### Code Usage (Bugs Found)

**File:** `backend/app/services/scenarios.py`

**Line 318:**
```sql
SELECT l.quantity, ...  -- ❌ BUG: Should be l.quantity_open
```

**Line 396:**
```sql
WHERE l.quantity > 0  -- ❌ BUG: Should be l.quantity_open > 0
```

**Line 773:**
```sql
SELECT SUM(quantity * cost_basis_per_share) AS nav  -- ❌ BUG: Should be quantity_open
```

**Line 777:**
```sql
WHERE quantity > 0  -- ❌ BUG: Should be quantity_open > 0
```

**Status:** ❌ **BUGS** - Code uses deprecated field instead of `quantity_open`

**Impact:** May cause incorrect portfolio calculations in scenario analysis

---

### Correct Usage

**Should Use:**
```sql
SELECT l.quantity_open, ...  -- ✅ CORRECT
WHERE l.quantity_open > 0  -- ✅ CORRECT
```

**Should NOT Use:**
```sql
SELECT l.quantity, ...  -- ❌ DEPRECATED
WHERE l.quantity > 0  -- ❌ DEPRECATED
```

---

## 📋 Deprecation Plan

### Phase 1: Add Deprecation Comment (IMMEDIATE)

**Migration:** `XXX_add_quantity_deprecation_comment.sql`

```sql
COMMENT ON COLUMN lots.quantity IS 
'⚠️ DEPRECATED: Use quantity_open for current positions. This field is kept for backwards compatibility (Migration 007) but will be removed in a future version. Do not use in new code.';
```

**Status:** ✅ **PLANNED** - Phase 1

---

### Phase 2: Update All Queries (IMMEDIATE)

**Tasks:**
1. Fix `scenarios.py` SQL queries (4 locations)
2. Audit all other services for `quantity` field usage
3. Update all queries to use `quantity_open`

**Status:** ✅ **PLANNED** - Phase 1

---

### Phase 3: Monitor Usage (ONGOING)

**Tasks:**
1. Monitor database queries for `quantity` field usage
2. Track any remaining references
3. Plan removal timeline

**Status:** ✅ **PLANNED** - Ongoing

---

### Phase 4: Remove Field (FUTURE)

**Prerequisites:**
- All queries updated to use `quantity_open`
- No remaining references to `quantity` field
- Migration window identified

**Timeline:** TBD - Future version

**Migration:**
```sql
-- Future migration to remove field
ALTER TABLE lots DROP COLUMN quantity;
```

**Status:** 🔮 **FUTURE** - Not yet planned

---

## ⚠️ Risks

### Risk 1: Incorrect Calculations

**Problem:** Code using `quantity` field may get incorrect values

**Impact:** High - Affects portfolio calculations

**Mitigation:** Fix all queries to use `quantity_open` (Phase 1)

---

### Risk 2: Data Inconsistency

**Problem:** `quantity` field may not be updated correctly

**Impact:** Medium - Data may be stale

**Mitigation:** All new code uses `quantity_open` (standardized)

---

### Risk 3: Breaking Changes

**Problem:** Dropping `quantity` field would break existing code

**Impact:** High - Breaking change

**Mitigation:** Keep field for backwards compatibility, plan gradual migration

---

## ✅ Recommendations

### Immediate (Phase 1)

1. ✅ Add deprecation comment to database
2. ✅ Fix all queries using `quantity` field (4 locations in scenarios.py)
3. ✅ Audit all services for `quantity` field usage
4. ✅ Update documentation

### Short-term (Phase 2-3)

1. ⚠️ Monitor usage of `quantity` field
2. ⚠️ Plan gradual migration
3. ⚠️ Update all test files

### Long-term (Phase 4)

1. 🔮 Plan removal timeline
2. 🔮 Create migration to remove field
3. 🔮 Execute removal migration

**Status:** Currently maintaining field for backwards compatibility

---

## 📝 Summary

**Field:** `lots.quantity`

**Status:** ⚠️ **DEPRECATED** - Use `quantity_open` instead

**History:**
- Original field in `lots` table
- Replaced by `quantity_open`/`quantity_original` in Migration 007
- Kept for backwards compatibility

**Current Issues:**
- ❌ 4 bugs in `scenarios.py` using deprecated field
- ⚠️ No deprecation comment in database

**Recommendation:**
1. ✅ Add deprecation comment (Phase 1)
2. ✅ Fix all queries (Phase 1)
3. ⚠️ Monitor usage (ongoing)
4. 🔮 Plan removal (future)

**DO NOT:** Drop field yet - maintain for backwards compatibility

