# Constants Refactor - Phase 3 Migration Plan

**Date**: November 7, 2025
**Status**: ⏳ READY TO EXECUTE (Phases 1-2 Complete)
**Risk Level**: MEDIUM (breaking changes, requires testing)

---

## Overview

Phase 3 migrates services from hardcoded risk-free rate constants to dynamic data helpers. This is the **first breaking change** in the refactor plan.

**Prerequisite**: Phases 1-2 must be complete ✅
- Phase 1: Dynamic data infrastructure created ✅
- Phase 2: Old constants marked deprecated ✅

---

## Phase 3 Strategy: Incremental Service Migration

### Approach: Batch Migration (High-Impact First)

We'll migrate services in 3 batches, testing after each batch:

1. **Batch 1** (HIGH IMPACT): optimizer.py - Portfolio optimization (3 instances)
2. **Batch 2** (MEDIUM IMPACT): Seed scripts - Test data generation (4 instances)
3. **Batch 3** (CLEANUP): Remove deprecated constants from modules

**Why This Order**:
- Optimizer.py is most critical (production code, high visibility)
- Seed scripts are low-risk (only run during development)
- Removing deprecated constants last ensures rollback is possible

---

## Batch 1: Migrate optimizer.py (HIGH IMPACT)

### Current Usage Analysis

Let me find where optimizer.py uses risk-free rate:

**File**: `backend/app/services/optimizer.py`
**Expected Instances**: 3 (from code review)

### Migration Steps

#### Step 1: Identify All Usages

```bash
# Search for risk-free rate usage in optimizer.py
grep -n "RISK_FREE_RATE" backend/app/services/optimizer.py
```

#### Step 2: Update Imports

**Before**:
```python
from app.core.constants.scenarios import DEFAULT_OPTIMIZATION_RISK_FREE_RATE
# or
from app.core.constants.risk import DEFAULT_RISK_FREE_RATE
```

**After**:
```python
from app.core.constants import get_risk_free_rate
```

#### Step 3: Update Function Signatures (if needed)

If the optimizer functions are not already async, they'll need to become async to call `await get_risk_free_rate()`.

**Potential Impact**: If optimizer.py functions are called synchronously, this is a breaking change.

**Before**:
```python
def optimize_portfolio(holdings, constraints):
    rf_rate = DEFAULT_OPTIMIZATION_RISK_FREE_RATE  # 0.02
    # ... optimization logic
```

**After**:
```python
async def optimize_portfolio(holdings, constraints):
    rf_rate = await get_risk_free_rate()  # Live from FRED
    # ... optimization logic
```

**Cascading Changes**: All callers of `optimize_portfolio()` must also use `await`.

#### Step 4: Testing Strategy

**Unit Tests**:
```python
# Test that optimizer uses live risk-free rate
@pytest.mark.asyncio
async def test_optimizer_uses_dynamic_risk_free_rate(db_connection):
    # Insert DGS10 = 5.0%
    await db_connection.execute("""
        INSERT INTO macro_indicators (indicator_id, date, value)
        VALUES ('DGS10', CURRENT_DATE, 5.0)
        ON CONFLICT (indicator_id, date) DO UPDATE SET value = 5.0
    """)

    # Run optimization
    result = await optimize_portfolio(...)

    # Verify it used 5.0% (not hardcoded 2%)
    assert result.risk_free_rate_used == 0.05
```

**Integration Tests**:
- Run full optimization with live data
- Compare results to baseline (should be different due to rate change)
- Verify no crashes or errors

**Regression Tests**:
- Run existing optimizer test suite
- All tests should pass (or fail only due to rate difference)

### Rollback Plan (Batch 1)

If optimizer migration fails:

```python
# Rollback: Revert to hardcoded constant
from app.core.constants.scenarios import DEFAULT_OPTIMIZATION_RISK_FREE_RATE

async def optimize_portfolio(holdings, constraints):
    # TEMPORARY ROLLBACK: Use hardcoded rate
    rf_rate = DEFAULT_OPTIMIZATION_RISK_FREE_RATE  # 0.02
    # NOTE: Revert to dynamic after fixing issue

    # ... optimization logic
```

**Rollback Time**: < 5 minutes (one-line change)

### Estimated Effort (Batch 1)

| Task | Effort | Risk |
|------|--------|------|
| Identify usages | 30 min | LOW |
| Update imports | 15 min | LOW |
| Make functions async (if needed) | 1-2 hours | MEDIUM |
| Update all callers (if needed) | 2-4 hours | MEDIUM |
| Write unit tests | 1-2 hours | LOW |
| Run integration tests | 1 hour | LOW |
| Fix issues | 1-2 hours | MEDIUM |
| **Total** | **6-12 hours** | **MEDIUM** |

**High Variance**: Depends on whether optimizer functions are already async.

---

## Batch 2: Migrate Seed Scripts (MEDIUM IMPACT)

### Current Usage Analysis

**Files**: Seed scripts (test data generation)
**Expected Instances**: 4 (from code review)

### Migration Steps

Seed scripts are typically:
- `backend/db/seed_portfolios.py`
- `backend/db/seed_macro_data.py`
- Similar development tools

**Before**:
```python
from app.core.constants.scenarios import DEFAULT_OPTIMIZATION_RISK_FREE_RATE

async def seed_portfolio_scenarios():
    rf_rate = DEFAULT_OPTIMIZATION_RISK_FREE_RATE  # 0.02
    # ... create test scenarios
```

**After**:
```python
from app.core.constants import get_risk_free_rate

async def seed_portfolio_scenarios():
    rf_rate = await get_risk_free_rate()  # Live from FRED
    # ... create test scenarios
```

### Testing Strategy (Batch 2)

**Manual Testing**:
```bash
# Run seed script
python backend/db/seed_portfolios.py

# Verify data created correctly
# Check that risk-free rate matches current DGS10
```

**Low Risk**: Seed scripts only run during development, not production.

### Rollback Plan (Batch 2)

If seed script migration fails:
- Rollback is simple (one-line change per script)
- No production impact

### Estimated Effort (Batch 2)

| Task | Effort | Risk |
|------|--------|------|
| Find all seed scripts | 30 min | LOW |
| Update imports | 30 min | LOW |
| Test seed scripts | 1 hour | LOW |
| Fix issues | 1 hour | LOW |
| **Total** | **3 hours** | **LOW** |

---

## Batch 3: Remove Deprecated Constants (CLEANUP)

### When to Execute Batch 3

**ONLY after**:
1. ✅ Batch 1 complete and tested (optimizer migrated)
2. ✅ Batch 2 complete and tested (seed scripts migrated)
3. ✅ All services confirmed using new helpers
4. ✅ 1 week of production monitoring (no issues)

### Files to Modify

Remove deprecated constants from:

1. **backend/app/core/constants/risk.py**:
   ```python
   # DELETE THIS:
   DEFAULT_RISK_FREE_RATE = 0.0  # DEPRECATED - Use get_risk_free_rate() instead
   ```

2. **backend/app/core/constants/financial.py**:
   ```python
   # DELETE THIS:
   DEFAULT_SHARPE_RISK_FREE_RATE = 0.0  # DEPRECATED - Use get_risk_free_rate() instead
   ```

3. **backend/app/core/constants/scenarios.py**:
   ```python
   # DELETE THIS:
   DEFAULT_OPTIMIZATION_RISK_FREE_RATE = 0.02  # DEPRECATED - Use get_risk_free_rate() instead
   ```

### Validation Before Deletion

**CRITICAL**: Before deleting, verify NO services are using old constants:

```bash
# Search entire codebase for old constant usage
grep -r "DEFAULT_RISK_FREE_RATE" backend/app/services/
grep -r "DEFAULT_SHARPE_RISK_FREE_RATE" backend/app/services/
grep -r "DEFAULT_OPTIMIZATION_RISK_FREE_RATE" backend/app/services/

# Should return ZERO results (except in constants files)
```

If any usages found → DO NOT DELETE (migrate those services first).

### Testing Strategy (Batch 3)

**After deletion**:
```bash
# Run full test suite
pytest backend/tests/ -v

# All tests should pass
# Any failures indicate missed migration
```

### Rollback Plan (Batch 3)

If deletion breaks something:

```bash
# Restore deleted constants from git
git checkout backend/app/core/constants/risk.py
git checkout backend/app/core/constants/financial.py
git checkout backend/app/core/constants/scenarios.py

# Redeploy
```

**Rollback Time**: < 10 minutes

### Estimated Effort (Batch 3)

| Task | Effort | Risk |
|------|--------|------|
| Verify no usages | 30 min | LOW |
| Delete constants | 15 min | LOW |
| Update __all__ exports | 15 min | LOW |
| Run full test suite | 1 hour | LOW |
| Fix any issues | 1-2 hours | MEDIUM |
| **Total** | **3-4 hours** | **LOW** |

---

## Phase 3 Timeline

### Week 1: Batch 1 (Optimizer Migration)

**Monday-Tuesday** (6-12 hours):
- Identify all optimizer.py usages
- Make functions async (if needed)
- Update all callers
- Write unit tests
- Test integration

**Wednesday**:
- Deploy to staging
- Monitor for issues
- Fix any bugs

**Thursday**:
- Deploy to production
- Monitor closely

**Friday**:
- Continue monitoring
- Document any issues

### Week 2: Batch 2 (Seed Scripts)

**Monday** (3 hours):
- Migrate seed scripts
- Test manually
- Commit changes

**Tuesday-Wednesday**:
- Buffer for Batch 1 issues (if any)

### Week 3: Batch 3 (Cleanup)

**Monday** (3-4 hours):
- Verify no usages
- Delete deprecated constants
- Run full test suite

**Tuesday**:
- Deploy to production
- Monitor

**Total Timeline**: 2-3 weeks (12-19 hours work)

---

## Risk Assessment

### Risk Matrix

| Batch | Risk Level | Impact | Rollback Time |
|-------|-----------|---------|---------------|
| Batch 1 (optimizer.py) | MEDIUM | HIGH | < 5 min |
| Batch 2 (seed scripts) | LOW | LOW | < 5 min |
| Batch 3 (cleanup) | LOW | LOW | < 10 min |

### Highest Risks

1. **Optimizer.py async conversion** (HIGH RISK)
   - If optimizer functions not already async, cascading changes required
   - All callers must be updated
   - Potential for breaking API contracts

   **Mitigation**:
   - Check if optimizer.py already async (likely it is)
   - Test thoroughly before deploying
   - Have rollback ready

2. **Missing DGS10 data** (MEDIUM RISK)
   - If FRED data stale or missing, fallback to 3% kicks in
   - Optimization results change unexpectedly

   **Mitigation**:
   - Verify DGS10 data fresh before migration
   - Add monitoring for data staleness
   - Fallback to 3% is reasonable default

3. **Missed service migration** (LOW RISK)
   - Service still uses old constant after deletion
   - Code breaks in production

   **Mitigation**:
   - Comprehensive search before deletion (Batch 3)
   - Keep deprecated constants for 1 week
   - Full test suite run after deletion

### Overall Risk: MEDIUM

**Why Medium**:
- Batch 1 (optimizer) is high-impact, production code
- Async conversion may cascade to callers
- But: Easy rollback, good testing strategy, incremental approach

---

## Success Criteria

### Batch 1 Success:
- ✅ optimizer.py uses `get_risk_free_rate()`
- ✅ All unit tests pass
- ✅ Integration tests pass
- ✅ Production monitoring shows no errors
- ✅ Optimization results reasonable (not wildly different)

### Batch 2 Success:
- ✅ Seed scripts use `get_risk_free_rate()`
- ✅ Manual testing successful
- ✅ Test data generation works correctly

### Batch 3 Success:
- ✅ Deprecated constants removed
- ✅ Full test suite passes
- ✅ No services break
- ✅ Production stable for 1 week

### Overall Phase 3 Success:
- ✅ All services use dynamic risk-free rate
- ✅ No hardcoded 0.02 or 0.0 values remaining
- ✅ DGS10 data updates daily from FRED
- ✅ Optimization uses live Treasury rates
- ✅ All tests pass
- ✅ Production stable

---

## Pre-Flight Checklist

Before starting Phase 3, verify:

- [ ] Database is running and accessible
- [ ] Unit tests pass (Phases 1-2 tests)
- [ ] DGS10 data is fresh (< 7 days old)
- [ ] FRED data pipeline is working
- [ ] Database indexes exist (idx_macro_indicators_indicator_date)
- [ ] Staging environment available for testing
- [ ] Rollback plan documented and ready
- [ ] Monitoring in place (error rates, performance)

---

## Monitoring During Phase 3

### Metrics to Track

1. **Error Rates**:
   - Watch for increase in 500 errors
   - Monitor database connection errors
   - Track fallback to 3% usage (should be rare)

2. **Performance**:
   - Query time for `get_risk_free_rate()` (should be < 50ms)
   - Overall optimization time (should not increase significantly)

3. **Data Quality**:
   - DGS10 data freshness
   - Indicator query success rate

4. **Business Metrics**:
   - Optimization results (sanity check values)
   - Portfolio rebalancing recommendations

### Alert Thresholds

- 🔴 **Critical**: Error rate > 1%, optimization fails
- 🟠 **Warning**: Query time > 100ms, DGS10 data > 7 days old
- 🟡 **Info**: Fallback to 3% used (log for investigation)

---

## Alternative Approaches (Considered and Rejected)

### Approach 1: Big Bang Migration
Migrate all services at once.

**Rejected Because**:
- ❌ High risk (all or nothing)
- ❌ Difficult to isolate issues
- ❌ Harder to rollback

### Approach 2: Feature Flag
Use feature flag to toggle between old and new.

**Rejected Because**:
- ❌ Adds complexity (flag management)
- ❌ Temporary code that must be cleaned up later
- ❌ Not needed (rollback is simple with batch approach)

### Approach 3: Gradual Percentage Rollout
Deploy to 10% of users, then 50%, then 100%.

**Rejected Because**:
- ❌ Adds deployment complexity
- ❌ Risk is already low (batch + rollback plan)
- ❌ Not worth the overhead

**Why Batch Migration is Best**:
- ✅ Incremental (test each step)
- ✅ Easy rollback (per-batch)
- ✅ High-impact first (optimizer)
- ✅ Simple (no feature flags or complex deployment)

---

## Post-Phase 3 Validation

After Phase 3 complete, verify:

1. **Code Quality**:
   ```bash
   # No hardcoded risk-free rates
   grep -r "0.02" backend/app/services/ | grep -i "risk"
   grep -r "= 0.0" backend/app/services/ | grep -i "risk"

   # Should return ZERO results
   ```

2. **Test Coverage**:
   ```bash
   # All tests pass
   pytest backend/tests/ -v --cov=app/services

   # Coverage should be > 80%
   ```

3. **Production Monitoring** (1 week):
   - No increase in errors
   - Performance stable
   - Optimization results reasonable

4. **Data Quality**:
   ```sql
   -- Verify DGS10 updated recently
   SELECT indicator_id, date, value
   FROM macro_indicators
   WHERE indicator_id = 'DGS10'
   ORDER BY date DESC LIMIT 1;

   -- Should be within last 7 days
   ```

---

## Documentation Updates (Post-Phase 3)

After Phase 3, update:

1. **README.md**:
   - Document dynamic risk-free rate feature
   - Explain FRED data dependency

2. **Developer Guide**:
   - Update examples to use `get_risk_free_rate()`
   - Remove references to old constants

3. **API Documentation**:
   - Document optimizer.py changes (if API changed)

4. **Deployment Guide**:
   - Document FRED data pipeline requirement
   - Add troubleshooting for stale data

---

## Recommended Execution Order

### Option 1: Full Phase 3 (12-19 hours over 2-3 weeks)

Execute all batches:
1. Week 1: Batch 1 (optimizer.py) - 6-12 hours
2. Week 2: Batch 2 (seed scripts) - 3 hours
3. Week 3: Batch 3 (cleanup) - 3-4 hours

**Total**: 12-19 hours, 2-3 weeks calendar time

**Pros**: Complete migration, no deprecated code
**Cons**: Requires testing, monitoring, potential async conversion

### Option 2: Batch 1 Only (6-12 hours)

Execute only Batch 1 (optimizer.py):
- Migrate production optimizer
- Leave seed scripts for later
- Keep deprecated constants (no harm)

**Total**: 6-12 hours, 1 week

**Pros**: High-impact migration complete, lower risk
**Cons**: Incomplete (still have deprecated constants)

### Option 3: Defer Phase 3

Don't execute Phase 3 yet:
- Phases 1-2 provide infrastructure
- Services can migrate on their own timeline
- Deprecated constants remain (no harm)

**Total**: 0 hours

**Pros**: Zero risk, zero effort
**Cons**: Incomplete refactor, deprecated code remains

---

## Recommendation

**Recommended**: **Option 2 (Batch 1 Only)**

**Why**:
1. ✅ Highest impact (optimizer uses live data)
2. ✅ Lower risk than full Phase 3
3. ✅ Can defer Batches 2-3 (low priority)
4. ✅ Proves out the migration pattern
5. ✅ Real production value delivered

**Next Steps After Batch 1**:
- Monitor production for 1-2 weeks
- Assess if Batches 2-3 worth the effort
- Consider removing deprecated constants in v2.0.0

---

## Phase 3 Effort Summary

| Batch | Effort | Risk | Priority |
|-------|--------|------|----------|
| Batch 1: optimizer.py | 6-12 hours | MEDIUM | HIGH |
| Batch 2: seed scripts | 3 hours | LOW | MEDIUM |
| Batch 3: cleanup | 3-4 hours | LOW | LOW |
| **Total** | **12-19 hours** | **MEDIUM** | - |

**Calendar Time**: 2-3 weeks (with monitoring/buffer)

---

## Conclusion

Phase 3 is **optional but recommended** (at least Batch 1).

**Benefits of Phase 3**:
- ✅ Optimizer uses live 10Y Treasury rates (not hardcoded 2%)
- ✅ More accurate portfolio optimization
- ✅ No more deprecated constants cluttering codebase
- ✅ Proves out dynamic data strategy

**Risks of Phase 3**:
- ⚠️ Potential async conversion (if optimizer not already async)
- ⚠️ Requires testing and monitoring
- ⚠️ 12-19 hours effort

**When to Execute**:
- **Now**: If optimizer accuracy is critical
- **v2.0.0**: If can defer (remove deprecated constants in major version)
- **Never**: If hardcoded 2% is acceptable (but why?)

**Decision Point**: User approval required before proceeding with Phase 3.

---

🚀 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
