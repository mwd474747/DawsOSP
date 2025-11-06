# Currency Attribution Test Execution Plan

**Date:** January 14, 2025  
**Purpose:** Execute comprehensive test of currency attribution with seeded data

---

## Test Execution Checklist

### Step 1: Verify Remote Sync

- [x] Sync with remote
- [x] Check for new seed scripts
- [x] Review Replit's comprehensive seed script

**Status:** ✅ **COMPLETE** - Found `seed_comprehensive_data.py`

---

### Step 2: Check Data Availability

**SQL Queries:**
```sql
-- Check pricing packs
SELECT COUNT(*) as pack_count, MIN(date) as earliest, MAX(date) as latest
FROM pricing_packs;

-- Check prices
SELECT COUNT(DISTINCT pricing_pack_id) as packs_with_prices,
       COUNT(DISTINCT security_id) as securities_with_prices
FROM prices;

-- Check FX rates
SELECT COUNT(DISTINCT pricing_pack_id) as packs_with_fx,
       COUNT(*) as total_fx_rates
FROM fx_rates;

-- Check portfolio daily values
SELECT portfolio_id, COUNT(*) as days
FROM portfolio_daily_values
GROUP BY portfolio_id;

-- Check holdings
SELECT portfolio_id, COUNT(*) as holdings
FROM lots
WHERE quantity_open > 0
GROUP BY portfolio_id;
```

---

### Step 3: Fix Critical Bug

**Bug:** Weight and contribution calculation missing

**Location:** `backend/app/services/currency_attribution.py:200-227`

**Fix Applied:**
- ✅ Calculate total portfolio value
- ✅ Calculate weights for each position
- ✅ Calculate weighted contributions

**Status:** ✅ **FIXED** - Weights and contributions now calculated

---

### Step 4: Run Test Script

**Command:**
```bash
cd backend
python3 scripts/test_currency_attribution.py
```

**Expected Output:**
- Data requirements check results
- Attribution execution results
- Finance formula validation results

---

### Step 5: Validate Results

**Code Perspective:**
- ✅ All data exists
- ✅ Attribution executes
- ✅ Returns are non-zero
- ✅ No errors

**Finance Perspective:**
- ✅ Currency identity holds (< 1bp error)
- ✅ Weights sum to ~1.0
- ✅ Returns are reasonable
- ✅ Contributions are weighted correctly

---

## Next Steps

1. **Run test script** to verify seeded data
2. **Fix any remaining issues**
3. **Validate currency attribution works**
4. **Document findings**

---

**Status:** 🔍 **READY FOR EXECUTION**

