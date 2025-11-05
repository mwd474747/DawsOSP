# Detailed Sprint Plan V2: Critical Fixes + Broader Refactor (Revised)

**Date:** November 4, 2025  
**Purpose:** Comprehensive sprint plan integrating all critical issues, broader refactor, and pattern system work  
**Status:** 📋 **REVISED WITH FEEDBACK** - Ready for Execution

---

## 🎯 Executive Summary

This **revised sprint plan** incorporates critical feedback and integrates **three major work streams**:
1. **Critical Issues (15 P0-P2 issues)** - Security, reliability, data integrity fixes
2. **Broader Refactor (Database + API + Validation)** - Field naming, database integrity, consolidation
3. **Pattern System Refactor** - Simplification, consolidation, elimination of duplication

**Key Revision:** **Database-first approach** - Field name standardization MUST come first before pattern system refactoring.

**Total Duration:** 4-5 weeks (23-27 working days)  
**Sprint Structure:** Week-based phases (not 2-week sprints)  
**Team Size:** 1-2 developers  
**Risk Level:** Medium-High (coordinated changes across multiple layers)

---

## 📊 Field Name Usage Analysis (685 Total Locations)

### Current State Analysis

**Database Schema:** 201 locations
- `qty_open`: 51 locations
- `quantity`: 105 locations
- `market_value`: 33 locations
- `value`: 12 locations

**Backend Agents:** 219 locations
- Mixed usage of `qty_open`, `qty`, `quantity`
- Field name transformations in queries
- Inconsistent naming across agents

**Backend Services:** 127 locations
- Services rename fields differently
- `qty_open` → `qty` → `quantity` transformations
- Inconsistent field naming

**Pattern JSON:** 25 locations
- Patterns expect `quantity`, `market_value`
- Field name mismatches cause failures

**UI (full_ui.html):** 113 locations
- 46 `dataPath` mappings depend on field names
- Pattern registry expects specific field names
- Field name mismatches cause blank panels

**Critical Finding:** Pattern system CANNOT be refactored without standardized field names first.

---

## 🚨 Critical Dependency: Field Names Block Pattern Refactoring

### Why Field Names Must Come First

**UI patternRegistry expects specific field names:**
```javascript
// full_ui.html:2832-3451
{
  dataPath: 'valued_positions.positions',
  columns: [
    { field: 'quantity', header: 'Qty' },  // Must match backend exactly
    { field: 'market_value', header: 'Value' }  // Must match backend exactly
  ]
}

// If backend returns "qty_open", UI lookup fails → blank panels
```

**Pattern JSON expects standardized names:**
```json
// portfolio_overview.json
{
  "outputs": {
    "valued_positions": {
      "positions": [
        {
          "quantity": ...,  // Must be "quantity", not "qty_open"
          "market_value": ...  // Must be "market_value", not "value"
        }
      ]
    }
  }
}
```

**Impact of Mismatch:**
- Pattern execution succeeds but UI panels are blank
- `getDataByPath()` fails to find data
- Users see empty charts/tables
- No clear error message (silent failure)

**Conclusion:** Field name standardization MUST be completed before pattern system refactoring can proceed.

---

## 📋 Revised Execution Plan

### WEEK 0: Foundation (3-5 days) ⚠️ **CRITICAL - BLOCKS ALL OTHER WORK**

**Goal:** Fix P0 database issues blocking all downstream work

**Priority:** P0 - MUST BE FIRST

---

#### Day 1-2: Database Field Name Standardization

**Story 0.1: Standardize Quantity Fields** (13 points)
- **Priority:** P0 - BLOCKS PATTERN REFACTORING
- **Effort:** 2 days
- **Risk:** HIGH (affects all layers)

**Migration 014: Standardize Quantity Fields**

**Database Changes:**
```sql
-- Migration 014: Standardize Quantity Fields
-- qty_open → quantity_open
-- qty_original → quantity_original
-- quantity → quantity (keep, but ensure consistency)

BEGIN;

-- Step 1: Add new columns
ALTER TABLE lots ADD COLUMN IF NOT EXISTS quantity_open NUMERIC(18, 8);
ALTER TABLE lots ADD COLUMN IF NOT EXISTS quantity_original NUMERIC(18, 8);

-- Step 2: Copy data from old columns
UPDATE lots SET quantity_open = qty_open WHERE qty_open IS NOT NULL;
UPDATE lots SET quantity_original = qty_original WHERE qty_original IS NOT NULL;

-- Step 3: Update indexes
CREATE INDEX IF NOT EXISTS idx_lots_quantity_open ON lots(quantity_open);
DROP INDEX IF EXISTS idx_lots_qty_open;

-- Step 4: Drop old columns (after verification)
-- ALTER TABLE lots DROP COLUMN qty_open;
-- ALTER TABLE lots DROP COLUMN qty_original;

-- Step 5: Update views
CREATE OR REPLACE VIEW current_positions AS
SELECT 
    l.id,
    l.security_id,
    l.portfolio_id,
    l.quantity_open,  -- Updated field name
    l.quantity_original,
    ...
FROM lots l
WHERE l.quantity_open > 0;

COMMIT;
```

**Rollback Script:**
```sql
-- Rollback: Restore old columns
BEGIN;
ALTER TABLE lots ADD COLUMN IF NOT EXISTS qty_open NUMERIC(18, 8);
ALTER TABLE lots ADD COLUMN IF NOT EXISTS qty_original NUMERIC(18, 8);
UPDATE lots SET qty_open = quantity_open WHERE quantity_open IS NOT NULL;
UPDATE lots SET qty_original = quantity_original WHERE quantity_original IS NOT NULL;
COMMIT;
```

**Code Updates (51 files):**
1. **Backend Agents (219 locations):**
   - Update `financial_analyst.py` (line 168: `SELECT qty_open AS qty`)
   - Update all agent queries to use `quantity_open`
   - Remove field name transformations

2. **Backend Services (127 locations):**
   - Update `risk.py`, `optimizer.py`, `trade_execution.py`
   - Update all service queries to use standardized names
   - Remove field name transformations

3. **Pattern JSON (25 locations):**
   - Update all pattern outputs to use `quantity`, `quantity_open`
   - Update pattern templates to use standardized names

4. **UI (113 locations):**
   - Update `patternRegistry` dataPath mappings (46 locations)
   - Update UI components to use standardized names
   - Update chart components to use standardized names

**Validation Script:**
```python
# scripts/validate_field_names.py
async def validate_field_names():
    """Validate all field names are standardized."""
    errors = []
    
    # Check database
    result = await conn.fetch("SELECT COUNT(*) FROM lots WHERE qty_open IS NOT NULL")
    if result[0]['count'] > 0:
        errors.append("Database still has qty_open column")
    
    # Check backend queries
    for file in glob.glob("backend/**/*.py"):
        if "qty_open" in open(file).read():
            errors.append(f"Backend file still uses qty_open: {file}")
    
    # Check pattern JSON
    for pattern_file in glob.glob("backend/patterns/*.json"):
        pattern = json.load(open(pattern_file))
        if "qty_open" in json.dumps(pattern):
            errors.append(f"Pattern still uses qty_open: {pattern_file}")
    
    return errors
```

**Acceptance Criteria:**
- [ ] Database migration successful (no qty_open column)
- [ ] All 51 files updated to use quantity_open
- [ ] All 46 UI dataPath mappings updated
- [ ] Validation script passes (zero errors)
- [ ] All patterns execute successfully
- [ ] UI renders correctly with standardized names

**Files to Modify:**
- `backend/db/migrations/014_standardize_quantity_fields.sql` (NEW)
- `backend/app/agents/*.py` (51 files)
- `backend/app/services/*.py` (127 locations)
- `backend/patterns/*.json` (25 locations)
- `full_ui.html` (113 locations, 46 dataPath mappings)

---

#### Day 3: Standardize Date Fields

**Story 0.2: Standardize Date Fields** (5 points)
- **Priority:** P0 - DATA CONSISTENCY
- **Effort:** 1 day
- **Risk:** MEDIUM

**Migration 015: Standardize Date Fields**

**Database Changes:**
```sql
-- Migration 015: Standardize Date Fields
-- All date fields → asof_date (for consistency)

BEGIN;

-- Step 1: Add asof_date columns where missing
ALTER TABLE portfolio_metrics ADD COLUMN IF NOT EXISTS asof_date DATE;
ALTER TABLE portfolio_daily_values ADD COLUMN IF NOT EXISTS asof_date DATE;

-- Step 2: Copy data from existing date columns
UPDATE portfolio_metrics SET asof_date = date WHERE date IS NOT NULL;
UPDATE portfolio_daily_values SET asof_date = date WHERE date IS NOT NULL;

-- Step 3: Update indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_metrics_asof_date ON portfolio_metrics(asof_date);
CREATE INDEX IF NOT EXISTS idx_portfolio_daily_values_asof_date ON portfolio_daily_values(asof_date);

COMMIT;
```

**Code Updates:**
- Update all queries to use `asof_date` instead of `date`
- Update all agent methods to use `asof_date`
- Update pattern JSON to use `asof_date`

**Acceptance Criteria:**
- [ ] All date fields standardized to `asof_date`
- [ ] All queries updated
- [ ] All patterns use `asof_date`
- [ ] Validation script passes

---

#### Day 4: Database Integrity Fixes

**Story 0.3: Fix Database Integrity Violations** (8 points)
- **Priority:** P0 - DATA INTEGRITY
- **Effort:** 1 day
- **Risk:** MEDIUM

**Migration 016: Add Missing FK Constraints**

**Database Changes:**
```sql
-- Migration 016: Add Missing FK Constraints
-- Prevent orphaned records

BEGIN;

-- Step 1: Clean orphaned records
DELETE FROM lots 
WHERE security_id NOT IN (SELECT id FROM securities);

DELETE FROM transactions 
WHERE security_id NOT IN (SELECT id FROM securities);

-- Step 2: Add FK constraints
ALTER TABLE lots 
ADD CONSTRAINT fk_lots_security_id 
FOREIGN KEY (security_id) REFERENCES securities(id);

ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_security_id 
FOREIGN KEY (security_id) REFERENCES securities(id);

ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_portfolio_id 
FOREIGN KEY (portfolio_id) REFERENCES portfolios(id);

-- Step 3: Add indexes for FK lookups
CREATE INDEX IF NOT EXISTS idx_lots_security_id ON lots(security_id);
CREATE INDEX IF NOT EXISTS idx_transactions_security_id ON transactions(security_id);

COMMIT;
```

**Rollback Script:**
```sql
-- Rollback: Remove FK constraints
BEGIN;
ALTER TABLE lots DROP CONSTRAINT IF EXISTS fk_lots_security_id;
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS fk_transactions_security_id;
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS fk_transactions_portfolio_id;
COMMIT;
```

**Validation Script:**
```python
# scripts/validate_integrity.py
async def validate_integrity():
    """Validate database integrity."""
    errors = []
    
    # Check for orphaned records
    orphaned_lots = await conn.fetch("""
        SELECT COUNT(*) FROM lots l
        WHERE l.security_id NOT IN (SELECT id FROM securities)
    """)
    if orphaned_lots[0]['count'] > 0:
        errors.append(f"Found {orphaned_lots[0]['count']} orphaned lots")
    
    # Check FK constraints exist
    constraints = await conn.fetch("""
        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_name = 'lots' AND constraint_type = 'FOREIGN KEY'
    """)
    if not any(c['constraint_name'] == 'fk_lots_security_id' for c in constraints):
        errors.append("Missing FK constraint: fk_lots_security_id")
    
    return errors
```

**Acceptance Criteria:**
- [ ] All orphaned records cleaned
- [ ] FK constraints added and enforced
- [ ] Validation script passes (zero orphaned records)
- [ ] All patterns execute successfully

---

#### Day 5: Fix Duplicate Table Definitions

**Story 0.4: Fix Duplicate Table Definitions** (3 points)
- **Priority:** P0 - DATA CONSISTENCY
- **Effort:** 1 day
- **Risk:** LOW

**Migration 017: Fix Duplicate Table Definitions**

**Database Changes:**
```sql
-- Migration 017: Fix Duplicate Table Definitions
-- Remove duplicate views, consolidate schema

BEGIN;

-- Step 1: Identify duplicate views
-- (Check for multiple definitions of same view)

-- Step 2: Drop duplicate views
DROP VIEW IF EXISTS current_positions_duplicate;
DROP VIEW IF EXISTS portfolio_holdings_duplicate;

-- Step 3: Create single source of truth
CREATE OR REPLACE VIEW current_positions AS
SELECT 
    l.id,
    l.security_id,
    s.symbol,
    l.portfolio_id,
    l.quantity_open,
    l.quantity_original,
    ...
FROM lots l
JOIN securities s ON l.security_id = s.id
WHERE l.quantity_open > 0;

COMMIT;
```

**Acceptance Criteria:**
- [ ] Duplicate views removed
- [ ] Single source of truth for each view
- [ ] All queries updated to use consolidated views
- [ ] Validation script passes

---

### WEEK 1-2: Pattern System Refactoring (10 days)

**Dependencies:** ✅ Week 0 complete (field names standardized)

**Goal:** Simplify pattern system now that field names are standardized

---

#### Week 1: Pattern System Preparation

**Story 1.1: Update Pattern JSON Files** (8 points)
- **Priority:** P1 - PATTERN REFACTORING
- **Effort:** 2 days
- **Risk:** MEDIUM

**Tasks:**
1. **Update 13 pattern JSON files** (4 hours)
   - Update field names to use standardized names
   - Update pattern outputs to use `quantity`, `quantity_open`, `market_value`
   - Update pattern templates to use standardized names
   - Test pattern execution

2. **Create Pydantic schemas** (4 hours)
   - Create Pydantic schemas for pattern inputs
   - Validate pattern inputs against schemas
   - Return clear validation errors
   - Test validation

3. **Update pattern registry** (2 hours)
   - Update 46 UI dataPath mappings
   - Update pattern registry to match standardized names
   - Test UI rendering

4. **Testing & Validation** (2 hours)
   - Test all 13 patterns execute
   - Test UI rendering
   - Verify no regressions

**Acceptance Criteria:**
- [ ] All 13 pattern JSON files updated
- [ ] Pydantic schemas created for all patterns
- [ ] All 46 UI dataPath mappings updated
- [ ] All patterns execute successfully
- [ ] UI renders correctly

**Files to Modify:**
- `backend/patterns/*.json` (13 files)
- `backend/app/core/pattern_orchestrator.py` (add Pydantic validation)
- `full_ui.html` (46 dataPath mappings)

---

**Story 1.2: Eliminate Pattern Registry Duplication** (13 points)
- **Priority:** P1 - SIMPLIFICATION
- **Effort:** 3 days
- **Risk:** MEDIUM

**Tasks:**
1. **Move panel definitions to backend JSON** (8 hours)
   - Add `display.panels[]` to pattern JSON files
   - Include `dataPath` mappings in JSON
   - Remove `patternRegistry` from frontend
   - Update PatternRenderer to read from JSON

2. **Update PatternRenderer** (4 hours)
   - Read panel definitions from pattern response
   - Extract panels from pattern JSON
   - Update `getDataByPath()` to use JSON paths
   - Maintain backward compatibility

3. **Testing & Validation** (4 hours)
   - Test all patterns render correctly
   - Test panel rendering
   - Test dataPath extraction
   - Verify no UI regressions

**Acceptance Criteria:**
- [ ] Panel definitions in backend JSON only
- [ ] Frontend `patternRegistry` removed
- [ ] PatternRenderer reads from JSON
- [ ] All patterns render correctly
- [ ] No UI regressions

**Files to Modify:**
- `backend/patterns/*.json` (add display.panels)
- `full_ui.html` (remove patternRegistry, update PatternRenderer)

---

#### Week 2: Pattern Consolidation & Simplification

**Story 1.3: Consolidate Overlapping Patterns** (8 points)
- **Priority:** P1 - SIMPLIFICATION
- **Effort:** 2 days
- **Risk:** MEDIUM

**Tasks:**
1. **Identify pattern overlap** (2 hours)
   - Compare `portfolio_macro_overview` vs `portfolio_cycle_risk`
   - Identify similar functionality
   - Document consolidation opportunities
   - Create consolidation plan

2. **Consolidate overlapping patterns** (6 hours)
   - Merge `portfolio_macro_overview` into `portfolio_cycle_risk`
   - Update pattern references
   - Update UI references
   - Test consolidated patterns

3. **Remove unused patterns** (2 hours)
   - Identify unused patterns
   - Remove `cycle_deleveraging_scenarios` if unused
   - Remove `holding_deep_dive` if unused
   - Update documentation

4. **Testing & Validation** (2 hours)
   - Test consolidated patterns
   - Test pattern references
   - Test UI references
   - Verify no regressions

**Acceptance Criteria:**
- [ ] Overlapping patterns consolidated
- [ ] Unused patterns removed
- [ ] Pattern references updated
- [ ] UI references updated
- [ ] No regressions

**Files to Modify:**
- `backend/patterns/*.json` (consolidate patterns)
- `full_ui.html` (update pattern references)

---

**Story 1.4: Simplify Panel System** (5 points)
- **Priority:** P1 - SIMPLIFICATION
- **Effort:** 1 day
- **Risk:** MEDIUM

**Tasks:**
1. **Consolidate similar panel types** (4 hours)
   - Merge `pie_chart` and `donut_chart` into single type
   - Merge similar panel types
   - Update panel renderers
   - Test panel rendering

2. **Reduce panel system indirection** (2 hours)
   - Simplify PatternRenderer → PanelRenderer → Individual Panels
   - Reduce layers of indirection
   - Simplify panel rendering logic
   - Test panel rendering

3. **Testing & Validation** (2 hours)
   - Test all panel types render correctly
   - Test panel rendering performance
   - Verify no UI regressions
   - Test panel customization

**Acceptance Criteria:**
- [ ] Similar panel types consolidated
- [ ] Panel system indirection reduced
- [ ] All panels render correctly
- [ ] Performance improved
- [ ] No UI regressions

**Files to Modify:**
- `full_ui.html` (simplify panel system)
- `backend/patterns/*.json` (update panel types)

---

### WEEK 3: Complete System Fixes + Critical Issues (5 days)

**Dependencies:** ✅ Week 0-2 complete

**Goal:** Complete system fixes and address remaining critical issues

---

#### Day 1: Security Fixes (P0)

**Story 3.1: Fix Unsafe eval() Vulnerability** (8 points)
- **Priority:** P0 - SECURITY CRITICAL
- **Effort:** 1 day
- **Risk:** HIGH

**Tasks:**
1. **Replace eval() with safe evaluator** (4 hours)
   - Install `simpleeval` library or implement AST-based evaluator
   - Replace `eval()` in `pattern_orchestrator.py:845`
   - Create whitelist of allowed operations
   - Add input sanitization

2. **Add condition syntax validation** (2 hours)
   - Validate condition syntax before evaluation
   - Add clear error messages for invalid conditions
   - Test with malicious input patterns

3. **Testing & Validation** (2 hours)
   - Test with valid conditions (existing patterns)
   - Test with malicious conditions (security testing)
   - Verify no performance regression
   - Update documentation

**Acceptance Criteria:**
- [ ] No `eval()` usage in pattern orchestrator
- [ ] Safe evaluator handles all existing pattern conditions
- [ ] Security test passes (malicious conditions rejected)
- [ ] All existing patterns still work

**Files to Modify:**
- `backend/app/core/pattern_orchestrator.py` (lines 815-849)

---

**Story 3.2: Add Authorization Checking for Patterns** (3 points)
- **Priority:** P0 - SECURITY
- **Effort:** 1 day
- **Risk:** LOW

**Tasks:**
1. **Add rights checking in PatternOrchestrator** (2 hours)
   - Check `rights_required` field from pattern JSON
   - Validate user has required rights from JWT token
   - Return 403 Forbidden if rights insufficient
   - Add rights checking before pattern execution

2. **Add rights checking to executor API** (2 hours)
   - Add rights validation to executor endpoint
   - Check rights before calling orchestrator
   - Return clear error messages for denied access

3. **Testing & Validation** (2 hours)
   - Test with user having required rights (should pass)
   - Test with user missing required rights (should fail with 403)
   - Test with ADMIN user (should have all rights)
   - Verify error messages are clear

**Acceptance Criteria:**
- [ ] Patterns check `rights_required` before execution
- [ ] Users without required rights get 403 error
- [ ] ADMIN users can execute any pattern
- [ ] Error messages indicate missing rights
- [ ] All patterns have `rights_required` defined

**Files to Modify:**
- `backend/app/core/pattern_orchestrator.py` (add rights checking)
- `backend/app/api/executor.py` (add rights validation)

---

#### Day 2-3: Reliability Fixes (P0)

**Story 3.3: Add Pattern Execution Timeout** (5 points)
- **Priority:** P0 - RELIABILITY
- **Effort:** 2 days
- **Risk:** MEDIUM

**Tasks:**
1. **Add timeout wrapper** (4 hours)
   - Wrap `run_pattern()` with `asyncio.wait_for()`
   - Add configurable timeout per pattern type
   - Add timeout configuration in pattern JSON
   - Default timeout: 60 seconds (configurable)

2. **Add cancellation token support** (4 hours)
   - Implement cancellation token mechanism
   - Add cancellation endpoint for pattern execution
   - Clean up resources on timeout/cancellation
   - Return partial results if cancelled

3. **Testing & Validation** (2 hours)
   - Test with patterns that complete quickly
   - Test with patterns that exceed timeout
   - Test cancellation mechanism
   - Verify resource cleanup

**Acceptance Criteria:**
- [ ] Pattern execution times out after configured duration
- [ ] Cancellation endpoint works
- [ ] Resources cleaned up on timeout
- [ ] Partial results returned if cancelled
- [ ] All existing patterns have timeout configured

**Files to Modify:**
- `backend/app/core/pattern_orchestrator.py` (lines 548-745)
- `backend/app/api/executor.py` (add cancellation endpoint)
- `backend/patterns/*.json` (add timeout_seconds field)

---

**Story 3.4: Fix Template Substitution for Optional Variables** (5 points)
- **Priority:** P0 - RELIABILITY
- **Effort:** 2 days
- **Risk:** MEDIUM

**Tasks:**
1. **Add optional variable syntax** (4 hours)
   - Implement `{{?variable.name}}` syntax (returns None if missing)
   - Add default value syntax: `{{variable.name|default:value}}`
   - Update `_resolve_value()` to handle optional variables
   - Maintain backward compatibility

2. **Improve error messages** (2 hours)
   - Distinguish required vs optional variables
   - Add helpful error messages for missing variables
   - Include available state keys in error messages

3. **Testing & Validation** (2 hours)
   - Test with existing patterns (should still work)
   - Test with optional variables
   - Test with default values
   - Verify backward compatibility

**Acceptance Criteria:**
- [ ] Optional variables work: `{{?variable.name}}`
- [ ] Default values work: `{{variable.name|default:value}}`
- [ ] Required variables still raise errors
- [ ] Error messages are helpful
- [ ] All existing patterns still work

**Files to Modify:**
- `backend/app/core/pattern_orchestrator.py` (lines 773-801)

---

#### Day 4: Data Integrity Fixes (P0)

**Story 3.5: Make Pattern Input Validation Blocking** (3 points)
- **Priority:** P0 - DATA INTEGRITY
- **Effort:** 1 day
- **Risk:** LOW

**Tasks:**
1. **Make validation blocking for errors** (2 hours)
   - Change validation from non-blocking to blocking for critical errors
   - Distinguish between warnings (non-blocking) and errors (blocking)
   - Return clear validation errors to user
   - Update validation logic

2. **Add Pydantic schema validation** (2 hours)
   - Create Pydantic schemas for pattern inputs
   - Validate inputs against schemas
   - Return detailed validation errors
   - Add schema validation to pattern JSON

3. **Testing & Validation** (2 hours)
   - Test with valid inputs (should pass)
   - Test with invalid inputs (should fail with clear errors)
   - Test with missing required inputs
   - Verify error messages are helpful

**Acceptance Criteria:**
- [ ] Validation blocks execution on critical errors
- [ ] Warnings are logged but don't block
- [ ] Pydantic schemas validate all pattern inputs
- [ ] Error messages are clear and actionable
- [ ] All existing patterns validate correctly

**Files to Modify:**
- `backend/app/core/pattern_orchestrator.py` (lines 355-546)
- `backend/patterns/*.json` (add input schemas)

---

**Story 3.6: Add Transaction Management for Multi-Step Patterns** (5 points)
- **Priority:** P0 - DATA INTEGRITY
- **Effort:** 2 days
- **Risk:** MEDIUM

**Tasks:**
1. **Wrap pattern execution in transaction** (4 hours)
   - Wrap `run_pattern()` in database transaction
   - Use asyncpg transaction context manager
   - Rollback on any step failure
   - Handle transaction boundaries for read-only vs write patterns

2. **Add transaction configuration** (2 hours)
   - Add `requires_transaction` field to pattern JSON
   - Support read-only patterns (no transaction needed)
   - Support write patterns (transaction required)
   - Default: read-only (no transaction)

3. **Testing & Validation** (2 hours)
   - Test with read-only patterns (should work without transaction)
   - Test with write patterns (should use transaction)
   - Test with pattern failure (should rollback)
   - Verify no partial state on failure

**Acceptance Criteria:**
- [ ] Write patterns use transactions
- [ ] Read-only patterns don't use transactions (performance)
- [ ] Pattern failures rollback database changes
- [ ] No partial state on pattern failure
- [ ] All patterns configured correctly

**Files to Modify:**
- `backend/app/core/pattern_orchestrator.py` (add transaction wrapper)
- `backend/patterns/*.json` (add requires_transaction field)

---

#### Day 5: Complete System Fixes

**Story 3.7: Verify suggest_hedges Capability** (2 points)
- **Priority:** P1 - VERIFICATION
- **Effort:** 0.5 day
- **Risk:** LOW

**Tasks:**
1. **Verify capability exists** (1 hour)
   - Verify `financial_analyst_suggest_hedges()` exists (line 2832)
   - Test capability execution
   - Test pattern execution with suggest_hedges
   - Verify no capability errors

2. **Test pattern execution** (1 hour)
   - Test `portfolio_scenario_analysis` pattern with suggest_hedges
   - Test `portfolio_cycle_risk` pattern with suggest_hedges
   - Verify hedge suggestions work correctly
   - Verify pattern completes successfully

**Acceptance Criteria:**
- [ ] `suggest_hedges` capability verified working
- [ ] Both patterns execute successfully
- [ ] Hedge suggestions returned correctly
- [ ] No capability errors

**Files to Review:**
- `backend/app/agents/financial_analyst.py` (line 2832)

---

**Story 3.8: Add Auth Token Refresh Interceptor** (3 points)
- **Priority:** P1 - USER EXPERIENCE
- **Effort:** 0.5 day
- **Risk:** LOW

**Tasks:**
1. **Add axios interceptor** (2 hours)
   - Add axios response interceptor in `full_ui.html`
   - Implement `refreshToken()` function
   - Retry original request with new token
   - Handle refresh errors

2. **Testing & Validation** (2 hours)
   - Test with expired token (should refresh)
   - Test with refresh failure (should redirect to login)
   - Test with long-running sessions
   - Verify no infinite loops

**Acceptance Criteria:**
- [ ] Token refresh interceptor works
- [ ] Expired tokens automatically refreshed
- [ ] Failed refresh redirects to login
- [ ] No infinite loops
- [ ] All API calls work with refreshed tokens

**Files to Modify:**
- `frontend/api-client.js` (add interceptor)
- `full_ui.html` (add refreshToken function)

---

**Story 3.9: Implement Structured Error Handling** (3 points)
- **Priority:** P1 - USER EXPERIENCE
- **Effort:** 0.5 day
- **Risk:** LOW

**Tasks:**
1. **Create error taxonomy** (2 hours)
   - Create `ErrorCode` enum
   - Define error categories
   - Map errors to user-friendly messages
   - Update error handling

2. **Update error responses** (2 hours)
   - Return structured error responses
   - Include error codes and messages
   - Include helpful suggestions
   - Update UI to display errors

**Acceptance Criteria:**
- [ ] Error taxonomy created
- [ ] All errors return structured responses
- [ ] UI displays user-friendly error messages
- [ ] Error messages include helpful suggestions
- [ ] Error handling consistent across all endpoints

**Files to Modify:**
- `backend/app/core/types.py` (add ErrorCode enum)
- `backend/app/api/executor.py` (update error handling)
- `full_ui.html` (update error display)

---

### WEEK 4: E2E Validation & Production (5 days)

**Dependencies:** ✅ Week 0-3 complete

**Goal:** Comprehensive testing and production deployment

---

#### Day 1-2: Comprehensive Testing

**Story 4.1: Pattern System Testing** (8 points)
- **Priority:** P0 - VALIDATION
- **Effort:** 2 days
- **Risk:** HIGH (could miss regressions)

**Test Suite:**
```python
# tests/pattern_system_test.py
async def test_all_patterns():
    """Test all 13 patterns execute correctly."""
    patterns = [
        'portfolio_overview',
        'portfolio_scenario_analysis',
        'portfolio_cycle_risk',
        'macro_cycles_overview',
        'macro_trend_monitor',
        'policy_rebalance',
        'buffett_checklist',
        'news_impact_analysis',
        'holding_deep_dive',
        'export_portfolio_report',
        'corporate_actions_upcoming',
        'portfolio_macro_overview',  # If not removed
        'cycle_deleveraging_scenarios',  # If not removed
    ]
    
    for pattern in patterns:
        result = await execute_pattern(pattern, test_inputs)
        assert result['success'], f"Pattern {pattern} failed"
        assert 'data' in result, f"Pattern {pattern} missing data"
        assert 'trace' in result, f"Pattern {pattern} missing trace"
        # Validate field names
        validate_field_names(result['data'])
        # Validate UI rendering
        validate_ui_rendering(pattern, result['data'])
```

**Acceptance Criteria:**
- [ ] All 13 patterns execute successfully
- [ ] All patterns return standardized field names
- [ ] All UI panels render correctly
- [ ] All dataPath mappings work
- [ ] No regressions found

---

#### Day 3: API Endpoint Testing

**Story 4.2: API Endpoint Testing** (5 points)
- **Priority:** P0 - VALIDATION
- **Effort:** 1 day
- **Risk:** MEDIUM

**Test All 53+ Endpoints:**
- [ ] Verify standardized field names
- [ ] Verify no capability errors
- [ ] Verify token refresh works
- [ ] Verify data integrity
- [ ] Verify error handling

---

#### Day 4: Performance Testing

**Story 4.3: Performance Testing** (3 points)
- **Priority:** P1 - PERFORMANCE
- **Effort:** 1 day
- **Risk:** LOW

**Performance Benchmarks:**
- [ ] Holdings query time: <50ms (target <100ms)
- [ ] Pattern execution time: <2s (p95)
- [ ] Portfolio load time: <1s (target <1.5s)
- [ ] API response time: <500ms (p95)

---

#### Day 5: Production Deployment

**Story 4.4: Staged Production Deployment** (5 points)
- **Priority:** P0 - DEPLOYMENT
- **Effort:** 1 day
- **Risk:** HIGH

**Deployment Steps:**
1. **Stage 1: Database Migration** (2 hours)
   - Run migration 014 (quantity fields)
   - Run migration 015 (date fields)
   - Run migration 016 (FK constraints)
   - Run migration 017 (duplicate tables)
   - Verify migrations successful

2. **Stage 2: Code Deployment** (2 hours)
   - Deploy backend code updates
   - Deploy frontend code updates
   - Verify deployment successful
   - Monitor for errors

3. **Stage 3: Validation** (2 hours)
   - Run validation scripts
   - Test critical user workflows
   - Monitor performance metrics
   - Verify no regressions

4. **Rollback Procedures** (1 hour)
   - Document rollback steps
   - Test rollback procedures
   - Prepare rollback scripts
   - Monitor for issues

**Acceptance Criteria:**
- [ ] All migrations successful
- [ ] Code deployed successfully
- [ ] Validation scripts pass
- [ ] No regressions found
- [ ] Performance metrics met
- [ ] Rollback procedures ready

---

## 📊 Success Metrics

### Technical Metrics

| Metric | Before | After (Target) | Improvement |
|--------|--------|----------------|-------------|
| **Field name consistency** | 30% | 95%+ | 65% improvement |
| **Holdings query time** | 150ms | <50ms | 67% faster |
| **Pattern success rate** | 95% | 99%+ | 4% improvement |
| **API error rate** | 3% | <1% | 67% reduction |
| **Pattern execution time** | 3s | <2s (p95) | 33% faster |

### User Experience Metrics

| Metric | Before | After (Target) | Improvement |
|--------|--------|----------------|-------------|
| **Portfolio load time** | 2s | <1s | 50% faster |
| **Token refresh success** | N/A | 99%+ | New feature |
| **Error message clarity** | 30% | 80%+ | 50% improvement |
| **UI panel rendering** | 95% | 99%+ | 4% improvement |

---

## 🔗 Critical Dependencies

### Must Complete in Order

```
WEEK 0: Database Field Standardization (P0)
    ↓ BLOCKS
WEEK 1-2: Pattern System Refactoring
    ↓ REQUIRES
WEEK 3: Complete System Fixes
    ↓ REQUIRES
WEEK 4: E2E Validation & Production
```

### Why Field Names Must Come First

**Pattern System CANNOT be refactored without standardized field names because:**

1. **UI patternRegistry expects specific field names:**
   ```javascript
   // 46 dataPath mappings depend on exact field names
   { dataPath: 'valued_positions.positions', columns: [{ field: 'quantity' }] }
   // If backend returns "qty_open", UI lookup fails → blank panels
   ```

2. **Pattern JSON expects standardized names:**
   ```json
   // Patterns output data with specific field names
   { "quantity": ..., "market_value": ... }
   // Must match UI expectations exactly
   ```

3. **getDataByPath() depends on exact field names:**
   ```javascript
   // UI extracts data using dot notation
   getDataByPath(data, 'valued_positions.positions.quantity')
   // If field name is "qty_open", extraction fails
   ```

**Conclusion:** Field name standardization MUST be completed before pattern system refactoring.

---

## 🚨 Risk Mitigation

### High Risk Items

1. **Database Migration (Week 0)**
   - **Risk:** Breaking changes across all layers
   - **Mitigation:** 
     - Gradual migration (keep old fields for compatibility period)
     - Feature flag for new field names
     - Comprehensive testing before removal
     - Rollback scripts ready

2. **Pattern System Refactoring (Week 1-2)**
   - **Risk:** UI breaking changes
   - **Mitigation:**
     - Backend pre-extraction tested thoroughly
     - Frontend changes tested with backend changes
     - Rollback plan documented
     - Feature flag for gradual rollout

3. **Security Fixes (Week 3)**
   - **Risk:** Security vulnerability if not fixed
   - **Mitigation:**
     - Fix unsafe eval() immediately (Day 1)
     - Add authorization checking immediately (Day 1)
     - Security testing before production
     - Rollback procedures ready

---

## 📋 Rollback Strategy

### Week 0 Rollback

**Database Migration Rollback:**
```sql
-- Rollback Migration 014
BEGIN;
ALTER TABLE lots ADD COLUMN IF NOT EXISTS qty_open NUMERIC(18, 8);
UPDATE lots SET qty_open = quantity_open WHERE quantity_open IS NOT NULL;
COMMIT;
```

**Code Rollback:**
- Revert code changes to use old field names
- Update pattern JSON to use old field names
- Update UI to use old field names

### Week 1-2 Rollback

**Pattern System Rollback:**
- Re-enable `patternRegistry` in frontend
- Revert backend panel extraction changes
- Keep pattern JSON changes (field names)

### Week 3 Rollback

**Security Fixes Rollback:**
- Revert eval() changes (NOT RECOMMENDED)
- Disable authorization checks (NOT RECOMMENDED)
- Revert timeout changes

---

## ✅ Definition of Done

### For Each Story
- [ ] Code implemented and tested
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Acceptance criteria met
- [ ] Validation scripts pass

### For Each Week
- [ ] All stories completed
- [ ] Week goal achieved
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Validation scripts pass
- [ ] Ready for next week

---

## 🎯 Key Differences from Original Plan

### Revised Approach

1. **Database-First:** Field name standardization MUST come first (Week 0)
2. **Complete Migration Scripts:** Includes actual SQL, Python, JavaScript code
3. **Clear Dependencies:** Each week explicitly depends on previous week
4. **Realistic Timeline:** 4-5 weeks (23-27 days) instead of 6 weeks
5. **Validation Points:** Every task has validation criteria and test procedures

### Execution Order

**Original Plan:**
- Sprint 1: Security fixes first
- Sprint 2: Field naming after
- Sprint 3: Pattern refactoring last

**Revised Plan:**
- Week 0: Field naming FIRST (blocks everything)
- Week 1-2: Pattern refactoring (after field names)
- Week 3: Security fixes (can be done in parallel)
- Week 4: Validation & production

---

## 📊 Updated Timeline

**Total Duration:** 4-5 weeks (23-27 working days)

**Week 0:** Foundation (3-5 days) - Database field standardization
**Week 1-2:** Pattern System Refactoring (10 days) - After field names fixed
**Week 3:** Complete System Fixes (5 days) - Security, reliability, data integrity
**Week 4:** E2E Validation & Production (5 days) - Testing and deployment

---

**Status:** ✅ **REVISED PLAN COMPLETE** - Ready for Execution  
**Next Step:** Review plan and start Week 0 (Database Field Standardization)

