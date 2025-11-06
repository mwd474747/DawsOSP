# Field Name Standardization Refactor Plan

**Date:** January 14, 2025  
**Status:** 📋 **PLANNING**  
**Purpose:** Comprehensive field name standardization across database schema and application code

---

## Executive Summary

**Current State:**
- Database schema uses abbreviated field names (`qty_open`, `qty_original`) from Migration 007
- Application code inconsistently uses both abbreviated (`qty_open`) and full names (`quantity_open`)
- Date fields use different conventions across tables (`valuation_date` vs `asof_date` vs `date`)
- Value fields use different conventions (`total_value` vs `nav` vs `market_value`)

**Target State:**
- Consistent field naming across all database tables
- Application code uses database field names directly (no aliasing except for API responses)
- Clear separation between database layer (source of truth) and API layer (transformation)

**Impact:**
- **Database Layer:** 1 table needs field rename (`portfolio_daily_values.valuation_date` → `asof_date`)
- **Application Layer:** ~20 files need updates (SQL queries, Python code)
- **API Layer:** No changes (already uses aliases for API responses)

---

## 1. Field Name Inventory

### 1.1 Quantity Fields

**Database Schema (Source of Truth):**
- `lots.qty_open` (NUMERIC) - Remaining open quantity
- `lots.qty_original` (NUMERIC) - Original purchase quantity
- `lots.quantity` (NUMERIC) - **DEPRECATED** (kept for backwards compatibility)

**Application Code Usage:**
- ✅ **CORRECT:** `qty_open` in SQL queries (18 files)
- ✅ **CORRECT:** `qty_original` in SQL queries (5 files)
- ⚠️ **ALIASED:** `qty_open as quantity_open` in SELECT statements (for Python code compatibility)
- ⚠️ **ALIASED:** `qty_original as quantity_original` in SELECT statements (for Python code compatibility)

**Current Status:**
- ✅ **FIXED:** All SQL queries now use `qty_open` and `qty_original` (matches database)
- ✅ **FIXED:** Python code uses aliases (`qty_open as quantity_open`) for compatibility
- ✅ **CORRECT:** API layer returns `quantity` (transformed from `quantity_open`)

**Recommendation:**
- ✅ **KEEP AS IS:** Database uses `qty_open`/`qty_original` (abbreviated)
- ✅ **KEEP AS IS:** Application code uses aliases for Python compatibility
- ✅ **KEEP AS IS:** API layer transforms to `quantity` for external consumers

---

### 1.2 Date Fields

**Database Schema (Source of Truth):**

**Time-Series Fact Tables (Should use `asof_date`):**
- ✅ `portfolio_metrics.asof_date` (DATE)
- ✅ `currency_attribution.asof_date` (DATE)
- ✅ `factor_exposures.asof_date` (DATE)
- ✅ `prices.asof_date` (DATE)
- ✅ `economic_indicators.asof_date` (DATE)
- 🔴 `portfolio_daily_values.valuation_date` (DATE) - **INCONSISTENT**

**Reference Tables (Use specialized names):**
- ✅ `pricing_packs.date` (DATE) - Pack date
- ✅ `lots.acquisition_date` (DATE) - Purchase date
- ✅ `lots.closed_date` (DATE) - Close date
- ✅ `transactions.transaction_date` (DATE) - Transaction date
- ✅ `transactions.settlement_date` (DATE) - Settlement date
- ✅ `corporate_actions.payment_date` (DATE) - Payment date
- ✅ `corporate_actions.ex_date` (DATE) - Ex-dividend date
- ✅ `corporate_actions.record_date` (DATE) - Record date

**Application Code Usage:**
- ✅ **CORRECT:** `asof_date` in queries for `portfolio_metrics`, `currency_attribution`, `factor_exposures`
- ✅ **CORRECT:** `valuation_date as asof_date` alias in queries for `portfolio_daily_values` (2 files)
- ⚠️ **INCONSISTENT:** Some code uses `asof_date` directly when querying `portfolio_daily_values` (should use alias)

**Current Status:**
- ✅ **FIXED:** `factor_analysis.py` uses `valuation_date as asof_date` alias
- ✅ **FIXED:** `metrics.py` uses `valuation_date as asof_date` alias
- ⚠️ **REMAINING:** `portfolio_daily_values` schema uses `valuation_date` (inconsistent with other time-series tables)

**Recommendation:**
- 🔴 **STANDARDIZE:** Rename `portfolio_daily_values.valuation_date` → `asof_date` (migration required)
- ✅ **KEEP:** Specialized date fields (`acquisition_date`, `transaction_date`, etc.) remain as-is

---

### 1.3 Value Fields

**Database Schema (Source of Truth):**

**Portfolio Value Fields:**
- ✅ `portfolio_daily_values.total_value` (NUMERIC) - Total portfolio NAV
- ✅ `portfolio_daily_values.positions_value` (NUMERIC) - Positions value
- ✅ `portfolio_daily_values.cash_balance` (NUMERIC) - Cash balance
- ✅ `portfolio_metrics.portfolio_value_base` (NUMERIC) - Portfolio value in base currency
- ✅ `portfolio_metrics.portfolio_value_local` (NUMERIC) - Portfolio value in local currency

**Position Value Fields:**
- ⚠️ **COMPUTED:** `market_value` (computed as `qty_open * price`) - Not stored in database
- ⚠️ **COMPUTED:** `value` (computed as `qty_open * price`) - Not stored in database

**Application Code Usage:**
- ✅ **CORRECT:** `total_value` in queries for `portfolio_daily_values`
- ✅ **CORRECT:** `portfolio_value_base` in queries for `portfolio_metrics`
- ⚠️ **INCONSISTENT:** Some code computes `market_value` vs `value` (both mean the same thing)

**Current Status:**
- ✅ **CORRECT:** Database uses `total_value` (not `nav`)
- ✅ **CORRECT:** Application code uses `total_value` from database
- ⚠️ **INCONSISTENT:** Python code uses both `market_value` and `value` for computed position values

**Recommendation:**
- ✅ **KEEP AS IS:** Database uses `total_value` (descriptive, clear)
- 🔴 **STANDARDIZE:** Application code should use `market_value` consistently (not `value`)

---

### 1.4 Other Field Name Inconsistencies

**Currency Fields:**
- ✅ `portfolios.base_currency` (TEXT)
- ✅ `securities.trading_currency` (TEXT)
- ✅ `securities.dividend_currency` (TEXT)
- ✅ `lots.currency` (TEXT)
- ✅ `fx_rates.base_ccy` (TEXT) - Abbreviated for FX pairs
- ✅ `fx_rates.quote_ccy` (TEXT) - Abbreviated for FX pairs

**Status:** ✅ **CONSISTENT** - Currency fields follow clear naming conventions

**Price Fields:**
- ✅ `prices.close` (NUMERIC) - Closing price
- ✅ `prices.open` (NUMERIC) - Opening price
- ✅ `prices.high` (NUMERIC) - High price
- ✅ `prices.low` (NUMERIC) - Low price

**Status:** ✅ **CONSISTENT** - Price fields follow standard OHLC naming

---

## 2. Standardization Rules

### 2.1 Database Schema Standards

**Rule 1: Time-Series Fact Tables**
- **Standard:** Use `asof_date` for all time-series fact tables
- **Rationale:** Consistent naming across `portfolio_metrics`, `currency_attribution`, `factor_exposures`, `prices`, `economic_indicators`
- **Exception:** Reference tables use specialized names (`acquisition_date`, `transaction_date`, etc.)

**Rule 2: Quantity Fields**
- **Standard:** Use abbreviated names (`qty_open`, `qty_original`)
- **Rationale:** Migration 007 established this convention, widely used in codebase
- **Exception:** Legacy `quantity` field kept for backwards compatibility (deprecated)

**Rule 3: Value Fields**
- **Standard:** Use descriptive names (`total_value`, `positions_value`, `cash_balance`)
- **Rationale:** Clear, unambiguous naming
- **Exception:** Computed fields in application code use `market_value` (not `value`)

**Rule 4: Currency Fields**
- **Standard:** Use full names (`base_currency`, `trading_currency`) except FX pairs (`base_ccy`, `quote_ccy`)
- **Rationale:** FX pairs use industry-standard abbreviations

---

### 2.2 Application Code Standards

**Rule 1: SQL Queries**
- **Standard:** Use database field names directly in SQL queries
- **Rationale:** Database schema is source of truth
- **Exception:** Use aliases (`qty_open as quantity_open`) only when Python code expects different names

**Rule 2: Python Code**
- **Standard:** Use aliased names from SQL queries (`quantity_open`, `asof_date`)
- **Rationale:** Python code should use full, descriptive names
- **Exception:** When querying directly, use database field names

**Rule 3: API Responses**
- **Standard:** Transform to API-friendly names (`quantity`, `date`, `value`)
- **Rationale:** API layer should abstract database implementation details
- **Exception:** Keep database field names if they're already API-friendly

---

## 3. Refactoring Plan

### Phase 1: Database Schema Standardization (3-4 hours) 🔴 **HIGH PRIORITY**

**Note:** Reduced time estimate since no backward compatibility needed (app not active)

**Task 1.1: Rename `portfolio_daily_values.valuation_date` → `asof_date` (1-2 hours)**

**Migration:** `backend/db/migrations/016_standardize_date_fields.sql`

```sql
BEGIN;

-- Step 1: Rename column
ALTER TABLE portfolio_daily_values
    RENAME COLUMN valuation_date TO asof_date;

-- Step 2: Update indexes
DROP INDEX IF EXISTS idx_portfolio_daily_values_date;
CREATE INDEX idx_portfolio_daily_values_date 
    ON portfolio_daily_values(asof_date DESC);

DROP INDEX IF EXISTS idx_portfolio_daily_values_portfolio;
CREATE INDEX idx_portfolio_daily_values_portfolio 
    ON portfolio_daily_values(portfolio_id, asof_date DESC);

-- Step 3: Update hypertable (if needed)
-- Note: TimescaleDB hypertable will automatically use new column name

-- Step 4: Update comments
COMMENT ON COLUMN portfolio_daily_values.asof_date IS 
    'As-of date for portfolio valuation (standardized with other time-series tables)';

COMMIT;
```

**Affected Files:**
- `backend/db/schema/portfolio_daily_values.sql` - Update schema definition
- `backend/app/services/factor_analysis.py` - Remove alias (use `asof_date` directly)
- `backend/app/services/metrics.py` - Remove alias (use `asof_date` directly)
- `backend/app/services/currency_attribution.py` - Update if uses `valuation_date`
- `backend/scripts/seed_portfolio_daily_values.py` - Update if uses `valuation_date`

**Verification:**
- ✅ All queries use `asof_date` (no aliases needed)
- ✅ All indexes updated
- ✅ Hypertable still works correctly

---

**Task 1.2: Remove Deprecated `lots.quantity` Column (30 minutes)**

**Migration:** `backend/db/migrations/017_remove_deprecated_quantity.sql`

```sql
BEGIN;

-- Step 1: Verify no code uses quantity column
-- (Should already be verified, but check anyway)

-- Step 2: Drop deprecated column
ALTER TABLE lots
    DROP COLUMN IF EXISTS quantity;

-- Step 3: Verify column removed
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'lots'
  AND column_name = 'quantity';
-- Should return 0 rows

COMMIT;
```

**Affected Files:**
- None (column already not used)

**Verification:**
- ✅ Column removed
- ✅ No code references `quantity` column
- ✅ All code uses `qty_open` instead

---

**Task 1.3: Verify All Time-Series Tables Use `asof_date` (30 minutes)**

**Tables to Verify:**
- ✅ `portfolio_metrics.asof_date` - Already correct
- ✅ `currency_attribution.asof_date` - Already correct
- ✅ `factor_exposures.asof_date` - Already correct
- ✅ `prices.asof_date` - Already correct
- ✅ `economic_indicators.asof_date` - Already correct
- 🔴 `portfolio_daily_values.valuation_date` - **NEEDS RENAME** (Task 1.1)

**Action:** After Task 1.1, all time-series tables will use `asof_date` consistently.

---

**Task 1.4: Update Schema Documentation (30 minutes)**

**Files to Update:**
- `DATABASE.md` - Update `portfolio_daily_values` schema documentation
- `backend/db/schema/portfolio_daily_values.sql` - Update comments
- Any other documentation referencing `valuation_date`

---

### Phase 2: Application Code Standardization (4-6 hours) 🟡 **MEDIUM PRIORITY**

**Note:** Reduced time estimate since no backward compatibility needed (app not active)

**Task 2.1: Remove All Field Name Aliases (2-3 hours)**

**Files to Update:**
- `backend/app/services/factor_analysis.py` - Remove `valuation_date as asof_date` alias
- `backend/app/services/metrics.py` - Remove `valuation_date as asof_date` alias
- `backend/app/services/currency_attribution.py` - Remove `valuation_date as asof_date` alias (if used)
- `backend/app/agents/financial_analyst.py` - Remove `qty_open as quantity_open` aliases
- `backend/app/api/routes/trades.py` - Remove `qty_open as quantity_open` aliases
- `backend/app/services/trade_execution.py` - Remove `qty_open as quantity_open` aliases
- All other files using aliases

**Change:**
```sql
-- BEFORE (with aliases)
SELECT valuation_date as asof_date, total_value
FROM portfolio_daily_values
WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3

SELECT qty_open as quantity_open, qty_original as quantity_original
FROM lots
WHERE qty_open > 0

-- AFTER (no aliases)
SELECT asof_date, total_value
FROM portfolio_daily_values
WHERE portfolio_id = $1 AND asof_date BETWEEN $2 AND $3

SELECT qty_open, qty_original
FROM lots
WHERE qty_open > 0
```

**Python Code Changes:**
```python
# BEFORE (using aliased names)
row["asof_date"]  # From alias
row["quantity_open"]  # From alias

# AFTER (using database field names directly)
row["asof_date"]  # Direct from database
row["qty_open"]  # Direct from database (update Python code to use qty_open)
```

**Verification:**
- ✅ All queries use database field names directly (no aliases)
- ✅ Python code uses database field names directly
- ✅ No breaking changes to API responses (API layer transforms field names)

---

**Task 2.2: Standardize Computed Value Field Names (2-3 hours)**

**Files to Update:**
- `backend/app/agents/financial_analyst.py` - Use `market_value` consistently (not `value`)
- `backend/app/services/scenarios.py` - Use `market_value` consistently
- `backend/app/services/currency_attribution.py` - Use `market_value` consistently

**Change:**
```python
# BEFORE
position["value"] = float(qty * price)

# AFTER
position["market_value"] = float(qty * price)
```

**Note:** This is a Python code change, not a database change. Database doesn't store computed values.

**Verification:**
- ✅ All computed position values use `market_value`
- ✅ API responses still return `value` (transformed from `market_value`)

---

**Task 2.3: Verify All SQL Queries Use Database Field Names (2 hours)**

**Files to Verify:**
- All files in `backend/app/services/` that query `lots` table
- All files in `backend/app/services/` that query `portfolio_daily_values` table
- All files in `backend/app/agents/` that query database tables

**Checklist:**
- ✅ All queries use `qty_open` (not `quantity_open`)
- ✅ All queries use `qty_original` (not `quantity_original`)
- ✅ All queries use `asof_date` (not `valuation_date`)
- ✅ All queries use `total_value` (not `nav`)

---

### Phase 3: Testing & Validation (4-6 hours) 🟡 **HIGH PRIORITY**

**Task 3.1: Unit Tests (2-3 hours)**

**Test Files to Update:**
- `backend/tests/unit/test_factor_analysis.py` - Test `asof_date` queries
- `backend/tests/unit/test_metrics.py` - Test `asof_date` queries
- `backend/tests/unit/test_currency_attribution.py` - Test `asof_date` queries

**Test Cases:**
- ✅ Query `portfolio_daily_values` using `asof_date` (not `valuation_date`)
- ✅ Query `lots` using `qty_open` (not `quantity_open`)
- ✅ Computed values use `market_value` (not `value`)

---

**Task 3.2: Integration Tests (2-3 hours)**

**Test Scenarios:**
- ✅ Factor analysis with `asof_date` queries
- ✅ Metrics calculation with `asof_date` queries
- ✅ Currency attribution with `asof_date` queries
- ✅ Portfolio holdings with `qty_open` queries

**Verification:**
- ✅ All tests pass with new field names
- ✅ No breaking changes to API responses
- ✅ Database queries execute correctly

---

## 4. Migration Strategy

### 4.1 Backwards Compatibility

**Status:** ✅ **NO BACKWARD COMPATIBILITY REQUIRED**

**Reasoning:**
- App is **NOT in production** (no active users)
- No external API consumers
- Frontend already uses snake_case
- No database views/functions depend on field names
- No data migration needed

**Approach:**
- ✅ **Aggressive Refactoring:** Refactor directly without compatibility layer
- ✅ **Database Migration:** Rename column atomically (no data loss)
- ✅ **Application Code:** Update all queries to use standardized field names directly
- ✅ **Remove Aliases:** Remove all `qty_open as quantity_open` and `valuation_date as asof_date` aliases
- ✅ **Remove Deprecated Fields:** Drop `lots.quantity` column immediately

**Rollback Plan:**
- If migration fails, rollback by renaming column back to `valuation_date`
- Application code can use aliases as fallback (already implemented)
- **Note:** Rollback shouldn't be necessary (app not active)

---

### 4.2 Deployment Order

**Step 1: Update Application Code (No Migration)**
- Update all queries to use `asof_date` (with alias `valuation_date as asof_date`)
- Deploy application code
- Verify queries work with current database schema

**Step 2: Deploy Database Migration**
- Run migration to rename `valuation_date` → `asof_date`
- Remove aliases from queries (now use `asof_date` directly)
- Deploy updated application code

**Step 3: Verification**
- Run integration tests
- Verify all queries work correctly
- Check API responses unchanged

---

## 5. Risk Assessment

### 5.1 High Risk Areas

**Risk 1: Breaking Existing Queries**
- **Impact:** HIGH - Queries using `valuation_date` will fail after migration
- **Mitigation:** Update all queries before deploying migration
- **Verification:** Grep for `valuation_date` in codebase before migration

**Risk 2: Hypertable Compatibility**
- **Impact:** MEDIUM - TimescaleDB hypertable may need reconfiguration
- **Mitigation:** Test migration on development database first
- **Verification:** Verify hypertable still works after column rename

**Risk 3: Index Rebuild**
- **Impact:** LOW - Indexes need to be recreated
- **Mitigation:** Migration includes index recreation
- **Verification:** Verify indexes exist after migration

---

### 5.2 Low Risk Areas

**Risk 4: API Response Changes**
- **Impact:** LOW - API layer already uses transformations
- **Mitigation:** No changes needed to API layer
- **Verification:** API tests should pass unchanged

**Risk 5: Python Code Changes**
- **Impact:** LOW - Python code uses aliased names from queries
- **Mitigation:** Update Python code to use `asof_date` directly
- **Verification:** Unit tests should pass

---

## 6. Success Criteria

### 6.1 Database Layer

- ✅ All time-series fact tables use `asof_date` consistently
- ✅ All quantity fields use `qty_open`/`qty_original` consistently
- ✅ All value fields use `total_value`/`market_value` consistently
- ✅ All indexes updated and working
- ✅ Hypertables still functional

---

### 6.2 Application Layer

- ✅ All SQL queries use database field names directly (no aliases except for Python compatibility)
- ✅ All Python code uses consistent field names
- ✅ All computed values use `market_value` (not `value`)
- ✅ All unit tests pass
- ✅ All integration tests pass

---

### 6.3 API Layer

- ✅ API responses unchanged (field name transformations work correctly)
- ✅ API tests pass
- ✅ No breaking changes to external consumers

---

## 7. Timeline Estimate

**Phase 1: Database Schema Standardization**
- Task 1.1: Rename `valuation_date` → `asof_date` (2-3 hours)
- Task 1.2: Verify all time-series tables (1 hour)
- Task 1.3: Update documentation (1 hour)
- **Total:** 4-5 hours

**Phase 2: Application Code Standardization**
- Task 2.1: Remove aliases (2-3 hours)
- Task 2.2: Standardize computed values (2-3 hours)
- Task 2.3: Verify all queries (2 hours)
- **Total:** 6-8 hours

**Phase 3: Testing & Validation**
- Task 3.1: Unit tests (2-3 hours)
- Task 3.2: Integration tests (2-3 hours)
- **Total:** 4-6 hours

**Grand Total:** 10-14 hours (1.5-2 days)

**Note:** Reduced from 14-19 hours since no backward compatibility needed (app not active)

---

## 8. Dependencies

**Prerequisites:**
- ✅ All current field name fixes completed (qty_open vs quantity_open)
- ✅ Database migration system working
- ✅ Test environment available

**Blocking Issues:**
- None identified

**Related Work:**
- Field name fixes completed in previous session
- Database schema review completed
- Factor analysis integration completed

---

## 9. Files to Modify

### 9.1 Database Schema Files

- `backend/db/schema/portfolio_daily_values.sql` - Update column name and comments
- `backend/db/migrations/016_standardize_date_fields.sql` - **NEW** - Migration script

---

### 9.2 Application Code Files

**Services:**
- `backend/app/services/factor_analysis.py` - Remove alias, use `asof_date` directly
- `backend/app/services/metrics.py` - Remove alias, use `asof_date` directly
- `backend/app/services/currency_attribution.py` - Update if uses `valuation_date`
- `backend/app/services/risk_metrics.py` - Verify uses `asof_date` correctly

**Agents:**
- `backend/app/agents/financial_analyst.py` - Standardize `market_value` usage

**Scripts:**
- `backend/scripts/seed_portfolio_daily_values.py` - Update if uses `valuation_date`

---

### 9.3 Documentation Files

- `DATABASE.md` - Update `portfolio_daily_values` schema documentation
- `FIELD_NAME_ANALYSIS_COMPREHENSIVE.md` - Mark as complete
- Any other documentation referencing `valuation_date`

---

## 10. Next Steps

1. **Review Plan:** Review this plan for completeness and accuracy
2. **Create Migration:** Create `016_standardize_date_fields.sql` migration
3. **Update Application Code:** Update all queries to use `asof_date` (with alias first)
4. **Test Migration:** Test migration on development database
5. **Deploy:** Deploy migration and updated application code
6. **Verify:** Run integration tests and verify all queries work

---

## Appendix A: Field Name Mapping

### A.1 Database → Application Code

| Database Field | Application Code | API Response | Notes |
|---------------|------------------|--------------|-------|
| `qty_open` | `quantity_open` (aliased) | `quantity` | Alias for Python compatibility |
| `qty_original` | `quantity_original` (aliased) | `quantity_original` | Alias for Python compatibility |
| `asof_date` | `asof_date` | `date` | Direct usage after migration |
| `valuation_date` | `asof_date` (aliased) | `date` | **TO BE RENAMED** → `asof_date` |
| `total_value` | `total_value` | `nav` | API transforms to `nav` |
| `market_value` | `market_value` (computed) | `value` | Computed, not stored |

---

### A.2 Standardization Rules Summary

1. **Time-Series Tables:** Use `asof_date` (not `valuation_date`, `date`)
2. **Quantity Fields:** Use `qty_open`/`qty_original` (abbreviated, matches database)
3. **Value Fields:** Use `total_value` (database) and `market_value` (computed)
4. **API Layer:** Transform to API-friendly names (`quantity`, `date`, `nav`)

---

## Appendix B: Verification Checklist

### B.1 Pre-Migration

- [ ] All queries using `valuation_date` identified
- [ ] All queries updated to use `asof_date` (with alias)
- [ ] Application code tested with current database schema
- [ ] Migration script created and tested on development database

### B.2 Post-Migration

- [ ] Database migration executed successfully
- [ ] All indexes recreated
- [ ] Hypertable still functional
- [ ] All queries use `asof_date` directly (no aliases)
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] API responses unchanged
- [ ] Documentation updated

---

**Status:** ✅ **PLAN COMPLETE** - Ready for execution

