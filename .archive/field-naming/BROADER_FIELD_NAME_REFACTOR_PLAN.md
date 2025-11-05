# Broader Field Name Refactor: Comprehensive Plan

**Date:** November 3, 2025  
**Status:** ✅ **VALIDATED - Ready for Execution**  
**Timeline:** 6-8 weeks (extended from 6 weeks to include database schema fixes)

---

## 📊 Executive Summary

**Validation Status:** ✅ **ALL FINDINGS CONFIRMED**

The database schema analysis has been **fully validated**. All critical issues are confirmed, and the 3-phase plan is accurate and well-structured. The extended timeline (6-8 weeks) is justified by the scope of database schema fixes required.

**Key Confirmed Issues:**
1. ✅ **Quantity Field Naming Chaos** - 3-way conflict (quantity, qty_open, qty_original)
2. ✅ **Date Field Inconsistency** - 11+ different date column names
3. ✅ **Duplicate Table Definitions** - position_factor_betas and scenario_shocks
4. ✅ **Missing Foreign Key Constraints** - lots.security_id, position_factor_betas.security_id
5. ✅ **No Materialized View for Current Positions** - Query duplicated 10+ times

**Impact Assessment:**
- **Database Layer:** Critical issues affecting all layers
- **API Layer:** Field name transformations create confusion
- **UI Layer:** Must handle multiple field name variants
- **Performance:** Missing materialized view causes repeated aggregations

---

## ✅ Validation Summary

### Issue 1: Quantity Field Naming Chaos - CONFIRMED ✅

**Evidence:**
- Base schema: `quantity` (full name)
- Migration 007: `qty_open`, `qty_original` (abbreviations)
- Code usage: 105 occurrences of `quantity`, 99 of `qty_open`, 80 of `qty`, 33 of `qty_original`

**Impact:** HIGH - Every holdings query must decide which field to use

**Validation Result:** ✅ **CONFIRMED**

---

### Issue 2: Date Field Inconsistency - CONFIRMED ✅

**Evidence:**
- 11+ different date column names:
  - `asof_date` (portfolio_metrics, currency_attribution, factor_exposures)
  - `valuation_date` (portfolio_daily_values)
  - `transaction_date` (transactions)
  - `acquisition_date` (lots)
  - `flow_date` (portfolio_cash_flows)
  - `date` (prices, macro_indicators, regime_history)
  - `payment_date`, `ex_date`, `record_date` (corporate_actions)
  - And more...

**Impact:** HIGH - Time-series joins require field name translation

**Validation Result:** ✅ **CONFIRMED**

---

### Issue 3: Duplicate Table Definitions - CONFIRMED ✅

**Evidence:**

**`position_factor_betas`:**
- **Schema** (`scenario_factor_tables.sql:12-51`):
  - PK: `(portfolio_id, security_id, factor_name)` (composite)
  - Structure: Normalized (factor_name, beta)
  - No FK constraints (commented out)
  - No date dimension

- **Migration** (`009_add_scenario_dar_tables.sql:70-97`):
  - PK: `id UUID` (single column)
  - Structure: Denormalized (individual beta columns)
  - Has FK constraint for `portfolio_id`
  - Has `asof_date` dimension
  - Different columns: `symbol` vs no symbol

**`scenario_shocks`:**
- **Schema** (`scenario_factor_tables.sql:74-124`):
  - PK: `scenario_id UUID`
  - Uses `scenario_name VARCHAR(100)`
  - JSONB structure: `shock_definition`

- **Migration** (`009_add_scenario_dar_tables.sql:28-66`):
  - PK: `id UUID`
  - Uses `shock_type TEXT` and `shock_name TEXT`
  - Individual columns: `real_rates_bps`, `inflation_bps`, etc.

**Impact:** CRITICAL - Which schema is correct?

**Validation Result:** ✅ **CONFIRMED**

---

### Issue 4: Missing Foreign Key Constraints - CONFIRMED ✅

**Evidence:**

**1. `lots.security_id`:**
```sql
-- backend/db/schema/001_portfolios_lots_transactions.sql:66
security_id UUID NOT NULL,  -- Reference to securities table (global)
-- ❌ No REFERENCES clause!
```

**2. `position_factor_betas.security_id`:**
```sql
-- backend/db/schema/scenario_factor_tables.sql:14
security_id UUID NOT NULL,
-- ❌ No REFERENCES clause! (commented out at line 28-29)
```

**3. `transactions.security_id`:**
```sql
-- Commented out in schema
security_id UUID,  -- Should reference securities(id)
-- ❌ No FK constraint!
```

**Impact:** HIGH - Referential integrity not enforced

**Validation Result:** ✅ **CONFIRMED**

---

### Issue 5: No Materialized View for Current Positions - CONFIRMED ✅

**Evidence:**
- Query duplicated in 10+ files:
  - `backend/app/services/risk.py:325`
  - `backend/app/services/optimizer.py:882`
  - `backend/app/services/metrics.py:478`
  - `backend/app/services/currency_attribution.py:134,345,413`
  - `backend/app/services/scenarios.py:362,762`
  - `backend/app/services/trade_execution.py:427,453,567`
  - `backend/app/agents/financial_analyst.py:168`
  - And more...

**Common Pattern:**
```sql
SELECT 
    l.symbol,
    SUM(l.qty_open) as quantity,
    SUM(l.cost_basis) as cost_basis,
    p.close * SUM(l.qty_open) as market_value
FROM lots l
JOIN prices p ON p.security_id = l.security_id
WHERE l.portfolio_id = $1
  AND l.qty_open > 0
  AND p.pricing_pack_id = $2
GROUP BY l.symbol, p.close;
```

**Impact:** HIGH - Performance overhead, consistency risk

**Validation Result:** ✅ **CONFIRMED**

---

## 📋 3-Phase Plan: Detailed Breakdown

### Phase 1 (Week 1-2): Critical Fixes

**Objective:** Fix critical schema issues that affect all layers

**Tasks:**

1. **Standardize Field Names** (2-3 days)
   - `qty_open` → `quantity_open`
   - `qty_original` → `quantity_original`
   - Keep `quantity` for backwards compatibility (deprecate)
   - Update all code references (317 occurrences)

2. **Standardize Date Fields** (2-3 days)
   - All time-series fact tables → `asof_date`
   - Keep specialized names for event tables (`transaction_date`, `payment_date`)
   - Update all code references (891+ occurrences)

3. **Remove Duplicate Table Definitions** (1 day)
   - Delete migration version of `position_factor_betas`
   - Delete migration version of `scenario_shocks`
   - Keep schema versions as source of truth
   - Add migration to add indexes/constraints only

4. **Add Missing FK Constraints** (2 hours)
   - `lots.security_id` → `securities(id)`
   - `position_factor_betas.security_id` → `securities(id)`
   - `transactions.security_id` → `securities(id)` (allow NULL)

5. **Fix Migration Numbering Conflicts** (1 day)
   - Review all migration files
   - Ensure consistent numbering
   - Document migration dependencies

**Total Effort:** 6-8 days (1.5-2 weeks) ✅ **ACCURATE**

**Risk Level:** HIGH - Affects all layers, requires careful migration

---

### Phase 2 (Week 3-4): Performance & Architecture

**Objective:** Improve performance and architecture quality

**Tasks:**

1. **Create Materialized View for Current Positions** (2-3 days)
   - Create `current_positions` materialized view
   - Add refresh trigger on `lots` table changes
   - Update all 10+ service files to use view
   - Add indexes for performance

2. **Add Composite Indexes for Time-Series Queries** (1 day)
   - `portfolio_metrics(portfolio_id, pricing_pack_id, asof_date DESC)`
   - `currency_attribution(portfolio_id, asof_date DESC)`
   - `factor_exposures(portfolio_id, asof_date DESC)`
   - Covering indexes for common queries

3. **Add GIN Indexes for JSONB Columns** (1 day)
   - `scenario_shocks.shock_definition`
   - `scenario_results.winners_json`, `losers_json`
   - Other JSONB columns as needed

4. **Create Helper Functions** (1 day)
   - `get_latest_pricing_pack(portfolio_id)`
   - `get_current_positions(portfolio_id, asof_date)`
   - Standardize common queries

**Total Effort:** 5-6 days (1-1.5 weeks) ✅ **ACCURATE**

**Risk Level:** MEDIUM - Performance improvements, lower risk than Phase 1

---

### Phase 3 (Week 5-6): Data Quality & Cleanup

**Objective:** Improve data quality and schema consistency

**Tasks:**

1. **JSONB Schema Validation** (2-3 days)
   - Add CHECK constraints for JSONB structure
   - Validate `shock_definition` structure
   - Validate `winners_json`, `losers_json` structure

2. **Consistency Triggers for Denormalized Fields** (2-3 days)
   - Ensure `lots.symbol` matches `securities.symbol`
   - Ensure `transactions.symbol` matches `securities.symbol`
   - Add triggers or constraints

3. **Constraint Naming Standardization** (1 day)
   - Standardize constraint names: `fk_<table>_<column>`
   - Standardize check constraint names: `chk_<table>_<column>`
   - Document naming conventions

4. **Deprecated Tables Cleanup** (1 day)
   - Identify unused tables
   - Archive or remove deprecated tables
   - Update documentation

**Total Effort:** 6-8 days (1.5-2 weeks) ✅ **ACCURATE**

**Risk Level:** LOW-MEDIUM - Data quality improvements, minimal breaking changes

---

## 🎯 Timeline Assessment

### Original Estimate: 6 weeks

**Assessment:** ❌ **INSUFFICIENT** - Database schema fixes not included

### Revised Estimate: 6-8 weeks

**Assessment:** ✅ **APPROPRIATE** - Includes database schema fixes

**Breakdown:**
- **Phase 1:** 1.5-2 weeks (Critical fixes)
- **Phase 2:** 1-1.5 weeks (Performance & Architecture)
- **Phase 3:** 1.5-2 weeks (Data Quality & Cleanup)
- **Buffer:** 1-2 weeks (for unexpected issues)
- **Total:** 6-8 weeks ✅

**Justification:**
- Database schema fixes require careful migration planning
- Field name changes affect 317+ code references
- Date field changes affect 891+ code references
- Materialized view requires updating 10+ service files
- Testing and validation required at each phase

---

## 🚨 Risk Assessment

### Phase 1: HIGH RISK ⚠️

**Risks:**
- Breaking changes to database schema
- Code updates required across all layers
- Migration must be carefully planned
- Rollback strategy needed

**Mitigation:**
- Use feature flags for gradual rollout
- Create backward-compatible aliases during transition
- Comprehensive testing before migration
- Rollback plan prepared

---

### Phase 2: MEDIUM RISK ⚠️

**Risks:**
- Materialized view refresh may impact performance
- Index creation may lock tables
- Service updates may introduce bugs

**Mitigation:**
- Use `CONCURRENTLY` for index creation
- Test materialized view refresh performance
- Gradual service updates with monitoring

---

### Phase 3: LOW-MEDIUM RISK ✅

**Risks:**
- JSONB validation may reject existing data
- Triggers may impact insert performance
- Constraint naming changes are cosmetic

**Mitigation:**
- Validate existing data before adding constraints
- Test trigger performance
- Constraint naming is non-breaking

---

## 📊 Impact Assessment

### Current State

**Database Layer:**
- 3 quantity field names (quantity, qty_open, qty_original)
- 11+ date column names
- Duplicate table definitions
- Missing FK constraints
- No materialized view for positions

**Code Layer:**
- 317+ references to quantity fields
- 891+ references to date fields
- 10+ duplicate holdings queries
- Field name transformations at API layer

**UI Layer:**
- Must handle multiple field name variants
- Defensive programming for field name mismatches

---

### Target State

**Database Layer:**
- Standardized quantity fields (`quantity_open`, `quantity_original`)
- Standardized date fields (`asof_date` for time-series)
- Single source of truth for tables
- All FK constraints enforced
- Materialized view for current positions

**Code Layer:**
- Standardized field names throughout
- Single repository for holdings queries
- No field name transformations

**UI Layer:**
- Consistent field names from API
- No defensive programming needed

---

## 🎯 Recommendations

### Immediate (Before Starting Refactor)

1. **Complete Phase 3 Consolidation** ✅ **DONE**
   - All agent consolidations complete
   - Legacy agents removed
   - Feature flags validated

2. **Complete Corporate Actions** ✅ **DONE**
   - All fixes applied
   - Field name mismatches fixed
   - Ready for testing

3. **Validate Current System** ⏳ **PENDING**
   - Test all patterns execute correctly
   - Test all API endpoints work
   - Document current working state

---

### Short-Term (Phase 1 Preparation)

1. **Create Migration Plan** (1 day)
   - Document all schema changes
   - Create rollback scripts
   - Plan migration sequence

2. **Create Feature Flags** (1 day)
   - Flag for field name changes
   - Flag for date field changes
   - Flag for materialized view usage

3. **Create Test Suite** (2 days)
   - Test all schema changes
   - Test all code updates
   - Test backward compatibility

---

### Execution (Phase 1-3)

1. **Execute Phase 1** (Week 1-2)
   - Critical fixes first
   - Validate each change
   - Monitor for issues

2. **Execute Phase 2** (Week 3-4)
   - Performance improvements
   - Architecture cleanup
   - Monitor performance

3. **Execute Phase 3** (Week 5-6)
   - Data quality improvements
   - Schema consistency
   - Final cleanup

---

## ✅ Validation Conclusion

**Analysis Quality:** ✅ **EXCELLENT** - All findings confirmed

**3-Phase Plan:** ✅ **VALIDATED** - Accurate timeline, correct priorities, well-structured

**Timeline:** ✅ **6-8 weeks** - Appropriate for scope

**Recommendation:** ✅ **PROCEED WITH REFACTOR** - After Phase 3 consolidation complete and corporate actions tested

---

**Status:** ✅ **VALIDATED - READY FOR EXECUTION**

**Next Steps:**
1. Complete current work (Phase 3 consolidation ✅, Corporate actions testing ⏳)
2. Prepare migration plan for Phase 1
3. Execute Phase 1-3 refactor (6-8 weeks)

---

**Validation Completed:** November 3, 2025  
**Plan Status:** ✅ **VALIDATED - Ready for Execution After Current Work Complete**

