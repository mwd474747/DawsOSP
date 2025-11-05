# Replit Agent Fix Prompts - Phase 1 Blocking Issues

**Date:** January 14, 2025  
**Status:** ⚠️ **BLOCKING ISSUES IDENTIFIED**  
**Priority:** CRITICAL - Fix before Phase 1 can be tested

---

## 🎯 Summary

The Replit agent found 4 critical issues preventing Phase 1 testing. After root cause analysis:

1. ✅ **Migration 009 not applied** - Easy fix (5 minutes)
2. ✅ **scenarios.py AttributeError** - Easy fix (5 minutes)
3. ❌ **Pattern execution returning wrong data** - Needs investigation (2-4 hours)
4. ⚠️ **Output extraction needs verification** - Needs testing (1-2 hours)

**Total Estimated Time:** 4-8 hours

---

## 📋 Fix Prompts for Replit Agent

### Fix Prompt 1: Apply Migration 009 (HIGH PRIORITY - 5 minutes)

```
Fix the missing position_factor_betas table issue.

1. Check if migration 009 has been applied:
   - Check database for position_factor_betas table
   - Run: SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'position_factor_betas');

2. If table doesn't exist, apply migration 009:
   - Run: python -m alembic upgrade head
   - OR manually apply: psql -d dawsos -f backend/db/migrations/009_add_scenario_dar_tables.sql

3. Verify table exists:
   - Check table structure
   - Verify indexes are created

4. Test scenario execution:
   - Run a scenario that uses position_factor_betas
   - Verify no "relation does not exist" errors

5. Report:
   - Migration status (applied or not)
   - Table verification results
   - Any errors encountered
```

---

### Fix Prompt 2: Fix scenarios.py AttributeError (HIGH PRIORITY - 5 minutes)

```
Fix the AttributeError in scenarios.py line 821.

1. Locate the error:
   - File: backend/app/services/scenarios.py
   - Line: 821
   - Error: 'str' object has no attribute 'value'

2. Understand the issue:
   - Line 800: for shock_type in self.scenarios.keys()
   - shock_type is a string (key from dict), not an Enum
   - Line 814: shock_type.value works (shock_type is Enum in this context)
   - Line 821: shock_type.value fails (shock_type is already a string)

3. Fix the issue:
   - Change line 821 to handle both Enum and string cases
   - Use: scenario_name = shock_type.value if hasattr(shock_type, 'value') else str(shock_type)
   - OR: Ensure shock_type is always an Enum before accessing .value

4. Test the fix:
   - Run DaR computation
   - Verify no AttributeError
   - Check logs for proper error messages

5. Report:
   - Fix applied
   - Test results
   - Any remaining errors
```

---

### Fix Prompt 3: Debug Pattern Execution Issue (CRITICAL PRIORITY - 2-4 hours)

```
Debug why all patterns return the same portfolio_overview data.

1. Check pattern loading:
   - Verify patterns are loaded correctly in PatternOrchestrator
   - Check if pattern_id is being passed correctly
   - Verify pattern spec is correct for each pattern

2. Check pattern execution:
   - Add logging to pattern execution
   - Verify correct pattern is being executed
   - Check if step execution is working
   - Verify step results are stored correctly in state

3. Check output extraction:
   - Verify output extraction logic works correctly
   - Test all 3 output formats
   - Check if Phase 1 changes broke output extraction

4. Debug steps:
   - Add logging to run_pattern() method
   - Log pattern_id being executed
   - Log step results being stored
   - Log output extraction process
   - Check if there's a fallback mechanism triggering

5. Potential issues to check:
   - Is pattern_id being passed correctly to run_pattern()?
   - Are patterns being loaded correctly?
   - Is output extraction logic working?
   - Is there a fallback to default pattern?

6. Test fixes:
   - Test all 6 updated patterns
   - Verify each returns correct data
   - Test existing patterns (portfolio_overview) to ensure no regression

7. Report:
   - Root cause identified
   - Fix applied
   - Test results for each pattern
   - Any remaining issues
```

---

### Fix Prompt 4: Verify Phase 1 Output Extraction (HIGH PRIORITY - 1-2 hours)

```
Verify Phase 1 output extraction changes work correctly.

1. Test Format 1 (List):
   - Test pattern with outputs: ["perf_metrics", "currency_attr", ...]
   - Verify outputs are extracted correctly
   - Check if outputs match step results

2. Test Format 2 (Dict):
   - Test pattern with outputs: {"perf_metrics": {...}, ...}
   - Verify outputs are extracted correctly
   - Check if outputs match step results

3. Test Format 3 (Panels):
   - Test pattern with outputs: {"panels": [...]}
   - Verify panel IDs are extracted
   - Verify panel IDs are mapped to step results correctly

4. Test all 6 updated patterns:
   - portfolio_cycle_risk
   - portfolio_macro_overview
   - cycle_deleveraging_scenarios
   - macro_trend_monitor
   - holding_deep_dive
   - portfolio_scenario_analysis

5. Verify backward compatibility:
   - Test existing patterns (portfolio_overview, etc.)
   - Ensure no regressions
   - Verify outputs still work correctly

6. Report:
   - Test results for each format
   - Test results for each pattern
   - Any issues found
   - Recommendations
```

---

### Fix Prompt 5: Re-test Phase 1 Features (HIGH PRIORITY - 1-2 hours)

```
After fixes are applied, re-test Phase 1 features.

1. Test Risk Analytics Page:
   - Navigate to Risk Analytics page
   - Verify warning banner displays
   - Verify _provenance field in API response
   - Verify data displays correctly

2. Test Provenance Warnings:
   - Verify _provenance field in risk.compute_factor_exposures response
   - Verify warnings are displayed in UI
   - Verify warning banner shows correct messages

3. Test Pattern Output Extraction:
   - Test all 6 updated patterns
   - Verify outputs are extracted correctly
   - Verify no "No data" errors

4. Test Regression:
   - Test existing working patterns
   - Verify no regressions
   - Verify all pages work correctly

5. Report:
   - Test results for each feature
   - Any issues found
   - Phase 1 status (ready or not)
```

---

## 🔧 Quick Fixes (Do These First)

### Quick Fix 1: Apply Migration 009

```bash
# Apply pending migrations
python -m alembic upgrade head

# OR manually apply migration
psql -d dawsos -f backend/db/migrations/009_add_scenario_dar_tables.sql

# Verify table exists
psql -d dawsos -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'position_factor_betas');"
```

### Quick Fix 2: Fix scenarios.py Line 821

```python
# File: backend/app/services/scenarios.py
# Line: 821

# Before:
logger.warning(f"Scenario {shock_type.value} failed: {e}")

# After:
scenario_name = shock_type.value if hasattr(shock_type, 'value') else str(shock_type)
logger.warning(f"Scenario {scenario_name} failed: {e}")
```

---

## 📊 Priority Order

1. **Fix 1: Apply Migration 009** (5 minutes) - HIGH PRIORITY
2. **Fix 2: Fix scenarios.py AttributeError** (5 minutes) - HIGH PRIORITY
3. **Fix 3: Debug Pattern Execution** (2-4 hours) - CRITICAL PRIORITY
4. **Fix 4: Verify Phase 1 Output Extraction** (1-2 hours) - HIGH PRIORITY
5. **Fix 5: Re-test Phase 1 Features** (1-2 hours) - HIGH PRIORITY

---

## ✅ Success Criteria

Phase 1 is ready when:

- [ ] `position_factor_betas` table exists
- [ ] scenarios.py AttributeError fixed
- [ ] All patterns return correct data (not portfolio_overview)
- [ ] Output extraction works for all 3 formats
- [ ] Risk Analytics page shows warning banner
- [ ] `_provenance` field in API responses
- [ ] All 6 updated patterns execute correctly
- [ ] No regressions in existing patterns

---

## 📝 Reporting Template

For each fix, report:

1. **Fix Applied:** [What was fixed]
2. **Status:** ✅ PASS / ❌ FAIL
3. **Details:** [What was done and results]
4. **Errors:** [Any errors encountered]
5. **Next Steps:** [What needs to be done next]

---

**Ready for Replit Agent Fixes:** Yes  
**Estimated Total Time:** 4-8 hours  
**Priority:** CRITICAL - Blocking Phase 1 testing

