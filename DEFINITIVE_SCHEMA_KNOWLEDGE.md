# Definitive DawsOS Schema Knowledge

**Date:** January 14, 2025
**Purpose:** Single source of truth for database schema and naming conventions
**Environment:** Replit deployment (production database)

---

## 🎯 Critical Understanding

### Database Deployment Location
**Backend:** Hosted on **Replit** (NOT local)
**Access:** Via `DATABASE_URL` environment variable on Replit
**Cannot verify locally:** Must trust Replit's database inspection results

---

## 📊 Field Naming: The Definitive Answer

### According to DATABASE.md (Updated November 6, 2025)

**Migration Timeline:**
1. **Migration 007 (October 2025):** Created `qty_open`, `qty_original` (abbreviated names)
2. **Migration 001 (November 4, 2025):** Renamed to `quantity_open`, `quantity_original` (full names)

**Current Database State (per Replit inspection):**
```sql
lots table columns:
- quantity (deprecated)
- quantity_open (active) ← Full name
- quantity_original (active) ← Full name
```

**Evidence (from DATABASE.md line 14-15):**
> Migration 001 **WAS EXECUTED**. The database uses `quantity_open` and `quantity_original` (full names), NOT the abbreviated forms.

**Code Pattern (current):**
```python
# backend/app/services/currency_attribution.py line 162
SELECT l.quantity_open  # Direct field reference, NO alias needed
FROM lots l
WHERE l.quantity_open > 0
```

### Reconciliation with System Reminders

**System Reminder Shows:**
```python
# Line 162:
l.qty_open AS quantity_open  # Uses alias
```

**Actual File Shows:**
```python
# Line 162:
l.quantity_open  # Direct reference
```

**Conclusion:** The system reminder is **outdated**. Either:
1. Replit reverted changes after I made them, OR
2. My changes were never committed, OR
3. The database schema was corrected independently

**What This Means:**
- ✅ Database has `quantity_open` (Replit is correct)
- ✅ Code queries `quantity_open` directly (no alias)
- ✅ My earlier fixes with SQL aliases were unnecessary
- ✅ Replit's CRITICAL_FIXES_RECONCILIATION_REPORT.md is accurate

---

## 🗄️ Complete Schema Standards (from DATABASE.md)

### Naming Conventions

**Field Names:**
- Full words preferred over abbreviations
- Snake_case for all column names
- Prefix/suffix patterns:
  - `*_id`: Foreign keys (UUID type)
  - `*_date`: Date columns
  - `*_at`: Timestamp columns
  - `*_type`: Enum/classification columns

**Table Names:**
- Snake_case, plural form
- Time-series tables marked with 🕐 in docs
- No prefixes (e.g., `tbl_`, `dim_`, etc.)

**Examples:**
- ✅ `quantity_open` (full name)
- ✅ `quantity_original` (full name)
- ✅ `transaction_type` (full name)
- ✅ `security_id` (standard FK pattern)
- ❌ `qty_open` (abbreviated - old schema)
- ❌ `qty_original` (abbreviated - old schema)

---

## 📋 Critical Tables Reference

### 1. lots (Tax Lot Tracking)
**Primary Key:** `id` (UUID)

**Core Fields:**
- `id` → UUID
- `portfolio_id` → UUID (FK to portfolios)
- `security_id` → UUID (FK to securities)
- `symbol` → TEXT
- `quantity` → NUMERIC(20,8) **DEPRECATED**
- `quantity_open` → NUMERIC(20,8) **ACTIVE** ← Use this
- `quantity_original` → NUMERIC(20,8) **ACTIVE** ← Use this
- `cost_basis` → NUMERIC(20,2)
- `cost_basis_per_share` → NUMERIC(20,2)
- `acquisition_date` → DATE
- `closed_date` → DATE (NULL if open)
- `currency` → TEXT
- `is_open` → BOOLEAN
- `created_at` → TIMESTAMP WITH TIME ZONE
- `updated_at` → TIMESTAMP WITH TIME ZONE

**Migration History:**
- Migration 007: Added `qty_open`, `qty_original`
- Migration 001: Renamed to `quantity_open`, `quantity_original`
- Migration 014: Deprecated `quantity` field

**Code Pattern:**
```python
# Correct (current):
SELECT quantity_open, quantity_original FROM lots

# Incorrect (old):
SELECT qty_open AS quantity_open FROM lots
```

---

### 2. transactions (Trade History)
**Primary Key:** `id` (UUID)

**Core Fields:**
- `id` → UUID
- `portfolio_id` → UUID (FK)
- `transaction_type` → TEXT (BUY, SELL, DIVIDEND, etc.)
- `security_id` → UUID (FK)
- `symbol` → TEXT
- `transaction_date` → DATE
- `settlement_date` → DATE
- `quantity` → NUMERIC(20,8)
- `price` → NUMERIC(20,8)
- `amount` → NUMERIC(20,2)
- `currency` → TEXT
- `fee` → NUMERIC(20,2)
- `realized_pl` → NUMERIC(20,2) **NEW** (Migration 017)
- `narration` → TEXT
- `source` → TEXT
- `created_at` → TIMESTAMP WITH TIME ZONE

**New Fields (November 6, 2025):**
- `realized_pl` → For IRS Form 1099-B compliance

---

### 3. portfolios (Portfolio Master)
**Primary Key:** `id` (UUID)

**Core Fields:**
- `id` → UUID
- `name` → TEXT NOT NULL
- `base_currency` → TEXT NOT NULL
- `owner_id` → UUID (FK to users)
- `cost_basis_method` → VARCHAR(20) **NEW** (Migration 018)
- `cost_basis_method_changed_at` → TIMESTAMP **NEW**
- `created_at` → TIMESTAMP WITH TIME ZONE
- `updated_at` → TIMESTAMP WITH TIME ZONE

**New Fields (November 6, 2025):**
- `cost_basis_method` → FIFO/LIFO/HIFO/SPECIFIC_LOT/AVERAGE_COST
- Default: 'FIFO'
- Validated by trigger (prevents LIFO for stocks)

---

### 4. portfolio_daily_values (NAV History) 🕐
**Primary Key:** `(portfolio_id, valuation_date)`
**Type:** TimescaleDB Hypertable

**Core Fields:**
- `portfolio_id` → UUID
- `valuation_date` → DATE ⚠️ **INCONSISTENCY**
- `total_value` → NUMERIC(20,2)
- `cash_balance` → NUMERIC(20,2)
- `positions_value` → NUMERIC(20,2)
- `cash_flows` → NUMERIC(20,2)
- `currency` → VARCHAR(3)
- `computed_at` → TIMESTAMP WITH TIME ZONE

**⚠️ CRITICAL INCONSISTENCY:**
- This table uses `valuation_date`
- Other time-series tables use `asof_date`
- **DATABASE.md line 234-244 documents this**
- Code must handle both field names

---

### 5. currency_attribution (Cached Attribution) 🕐
**Primary Key:** `(portfolio_id, asof_date)`
**Type:** TimescaleDB Hypertable

**Core Fields:**
- `portfolio_id` → UUID
- `asof_date` → DATE ← Note: Uses asof_date (NOT valuation_date)
- `pricing_pack_id` → TEXT (FK)
- `local_return` → NUMERIC(12,8)
- `fx_return` → NUMERIC(12,8)
- `interaction_return` → NUMERIC(12,8)
- `total_return` → NUMERIC(12,8)
- `error_bps` → NUMERIC(12,8)
- `attribution_by_currency` → JSONB
- `base_currency` → TEXT
- `created_at` → TIMESTAMP WITH TIME ZONE

**Architecture Note:** Table exists for caching, but service computes from `lots` directly

---

### 6. factor_exposures (Risk Factors) 🕐
**Primary Key:** `(portfolio_id, asof_date)`
**Type:** TimescaleDB Hypertable

**Core Fields:**
- `portfolio_id` → UUID
- `asof_date` → DATE
- `pricing_pack_id` → TEXT (FK)
- `beta_real_rate` → NUMERIC(12,8)
- `beta_inflation` → NUMERIC(12,8)
- `beta_credit` → NUMERIC(12,8)
- `beta_fx` → NUMERIC(12,8)
- `beta_market` → NUMERIC(12,8)
- `beta_size` → NUMERIC(12,8)
- `beta_value` → NUMERIC(12,8)
- `beta_momentum` → NUMERIC(12,8)
- `var_factor` → NUMERIC(12,8)
- `var_idiosyncratic` → NUMERIC(12,8)
- `r_squared` → NUMERIC(12,8)
- `factor_contributions` → JSONB
- `created_at` → TIMESTAMP WITH TIME ZONE

**Architecture Note:** Table exists for caching, service computes on-demand

---

### 7. macro_indicators (Economic Data) 🕐
**Primary Key:** `(indicator_name, date)`
**Type:** TimescaleDB Hypertable

**Core Fields:**
- `indicator_name` → TEXT (e.g., 'GDP_GROWTH', 'INFLATION')
- `date` → DATE
- `value` → NUMERIC(20,8)
- `unit` → TEXT
- `source` → TEXT
- `created_at` → TIMESTAMP WITH TIME ZONE

**Status:** Contains 102 rows of active data (per DATABASE.md line 284)
**Populated by:** `backend/scripts/populate_fred_data.py`

---

### 8. pricing_packs (Price Snapshots)
**Primary Key:** `id` (TEXT, format: 'PP_YYYY-MM-DD')

**Core Fields:**
- `id` → TEXT (e.g., 'PP_2025-11-03')
- `date` → DATE
- `status` → TEXT (PENDING, COMPLETE, FAILED)
- `securities_count` → INTEGER
- `fx_pairs_count` → INTEGER
- `created_at` → TIMESTAMP WITH TIME ZONE

**Architecture Note:** Immutable snapshots for reproducible valuations

---

### 9. economic_indicators (FRED Data) 🕐
**Status:** Mentioned in Migration 015 but not detailed in table inventory

**Purpose:** Store FRED economic indicator data
**Populated by:** `backend/scripts/populate_fred_data.py`
**Indicators:** 24 series (GDP, CPI, rates, employment, etc.)

**Expected Schema (based on script):**
- `series_id` → TEXT (FRED series ID)
- `date` → DATE
- `value` → NUMERIC
- `created_at` → TIMESTAMP WITH TIME ZONE

---

## 🔍 Date Field Inconsistency Summary

**Problem:** Time-series tables use different field names

**Tables using `asof_date`:**
- `currency_attribution`
- `factor_exposures`
- (others not fully enumerated)

**Tables using `valuation_date`:**
- `portfolio_daily_values` ⚠️

**Tables using `date`:**
- `portfolio_metrics`
- `portfolio_cash_flows`
- `macro_indicators`
- `pricing_packs`

**Impact:** Code must handle multiple date field conventions

**Recommendation:** Standardize to `asof_date` for all point-in-time tables

---

## 🎯 Code Patterns to Follow

### Pattern 1: Direct Field Reference (Correct)
```python
# When database has full field names
SELECT quantity_open, quantity_original
FROM lots
WHERE quantity_open > 0
```

### Pattern 2: Alias for Backward Compatibility (Old)
```python
# When database has abbreviated names (NO LONGER NEEDED)
SELECT qty_open AS quantity_open, qty_original AS quantity_original
FROM lots
WHERE qty_open > 0
```

### Pattern 3: Handle Date Field Variance
```python
# For portfolio_daily_values
SELECT portfolio_id, valuation_date, total_value
FROM portfolio_daily_values

# For currency_attribution
SELECT portfolio_id, asof_date, total_return
FROM currency_attribution

# NOT mixing them:
# ❌ SELECT asof_date FROM portfolio_daily_values  # Wrong!
```

---

## 📊 Migration Execution Order

**Executed Migrations (per DATABASE.md line 95):**
```
002, 002b, 002c, 002d, 003, 005, 007, 008, 009, 010, 011, 012, 013, 014, 015, 016, 017, 018
```

**Key Migrations:**
- **007:** Created `qty_open`, `qty_original`
- **001:** Renamed to `quantity_open`, `quantity_original` (executed Nov 4, 2025)
- **014:** Deprecated `quantity` field
- **015:** Added `economic_indicators` table
- **016:** Standardized `asof_date` (renamed from `valuation_date` in some tables)
- **017:** Added `realized_pl` to transactions
- **018:** Added `cost_basis_method` to portfolios

**Pending:** None (all migrations complete as of November 6, 2025)

---

## ✅ Verification Checklist

When working with DawsOS database:

- [ ] Remember backend is on **Replit** (not local)
- [ ] Trust DATABASE.md as source of truth (updated November 6)
- [ ] Use `quantity_open`, `quantity_original` (full names)
- [ ] Handle `valuation_date` vs `asof_date` inconsistency
- [ ] Check Migration 001 was executed (it was)
- [ ] Don't add unnecessary SQL aliases
- [ ] Verify fields exist before querying (Replit has real schema)

---

## 🎓 Lessons Learned

1. **Always verify against live database** - Migration files don't tell execution order
2. **Trust production inspection** - Replit's database queries are authoritative
3. **DATABASE.md is updated** - Reflects actual Replit deployment state
4. **System reminders can be stale** - Code changes may have been reverted
5. **Field name inconsistencies exist** - Handle `valuation_date` vs `asof_date`

---

## 📚 Authoritative Sources

**Primary:** DATABASE.md (updated November 6, 2025)
**Secondary:** Replit database inspection results
**Tertiary:** CRITICAL_FIXES_RECONCILIATION_REPORT.md
**DO NOT TRUST:** Local migration files alone (execution order matters)

---

**Status:** ✅ **Knowledge Base Updated**
**Confidence:** High (based on Replit production database inspection)
**Last Verified:** November 6, 2025 (by Replit)
**Next Verification:** When schema changes are made
