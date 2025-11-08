# Constants Refactor Plan - Conservative & Non-Disruptive

**Date**: November 7, 2025
**Approach**: Leverage existing DawsOS patterns, validate all assumptions, zero disruption
**Status**: 🎯 **PRODUCTION-READY PLAN**

---

## 🎯 Core Principle

**DO NOT** create new architecture. **BORROW** from existing DawsOS patterns:
- ✅ `MacroService` already fetches macro indicators from FRED
- ✅ `macro_indicators` table already stores DGS10, UNRATE, etc.
- ✅ Helper functions like `execute_query()` already exist
- ✅ Caching patterns already in use

**Goal**: Make constants **query the existing data** instead of hardcoding values.

---

## ✅ Validated Assumptions (Evidence-Based)

### 1. FRED Data Already Fetched ✅ CONFIRMED
**Evidence**:
```python
# backend/app/services/macro.py:469
async def get_latest_indicator(self, indicator_id: str) -> Optional[MacroIndicator]:
    """Get latest value for an indicator from database."""
    query = """
        SELECT value
        FROM macro_indicators
        WHERE indicator_id = $1
        ORDER BY date DESC LIMIT 1
    """
```

**Available Indicators** (from macro.py:446-456):
```python
"DGS10": "10-Year Treasury Constant Maturity Rate",  # ← Risk-free rate source
"DGS2": "2-Year Treasury Constant Maturity Rate",
"T10Y2Y": "10Y-2Y Treasury Spread",
"UNRATE": "Unemployment Rate",
"CPIAUCSL": "Consumer Price Index",
"BAA10Y": "Baa Corporate Bond Yield Spread"
```

**Status**: ✅ DGS10 (10Y Treasury) is already available for risk-free rate

---

### 2. Database Schema Verified ✅ CONFIRMED
**Evidence**:
```sql
-- backend/db/schema/macro_indicators.sql:26-48
CREATE TABLE macro_indicators (
    id UUID PRIMARY KEY,
    indicator_id TEXT NOT NULL,  -- "DGS10", "UNRATE", etc.
    date DATE NOT NULL,
    value NUMERIC NOT NULL,
    units TEXT,  -- "Percent"
    frequency TEXT  -- "Daily", "Monthly"
);

CREATE INDEX idx_macro_indicators_indicator_date
    ON macro_indicators(indicator_id, date DESC);
```

**Status**: ✅ Table exists, has indexes, stores FRED data

---

### 3. Existing Helper Functions ✅ CONFIRMED
**Evidence**:
```python
# backend/app/db/connection.py (used throughout)
from app.db.connection import execute_query, execute_query_one, execute_statement

# Example usage in macro.py:216-225
rows = await execute_query(query, indicator_id, as_of_date, lookback_start)
```

**Status**: ✅ Database helper functions already exist and are used

---

### 4. No Redis/Caching Currently ⚠️ NOT FOUND
**Evidence**: Searched for Redis usage, found **none** in services layer.

**Decision**: ❌ **DO NOT** add Redis caching (new dependency). Use simple in-memory cache or database-only.

---

### 5. Service Pattern Exists ✅ CONFIRMED
**Evidence**:
```python
# All services follow this pattern:
class SomeService:
    def __init__(self, fred_client: Optional[FREDProvider] = None):
        self.fred_client = fred_client

    async def some_method(self):
        # Use execute_query() for database
        # Use self.fred_client for external API
```

**Status**: ✅ Follow existing service pattern

---

## 📋 Conservative Refactor Plan (3 Phases)

### Phase 1: Create Macro Data Helper (NON-BREAKING)
**Effort**: 4-6 hours
**Risk**: LOW (new helper, doesn't change existing code)

#### Step 1.1: Create macro_data_helpers.py (NEW FILE)
**Location**: `backend/app/services/macro_data_helpers.py`

**Purpose**: Centralized functions to query macro_indicators table

```python
"""
Macro Data Helpers

Purpose: Helper functions to query macro indicators from database
Pattern: Similar to execute_query() - simple, focused helpers
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from app.db.connection import execute_query_one, execute_query

logger = logging.getLogger("DawsOS.MacroDataHelpers")


async def get_latest_indicator_value(
    indicator_id: str,
    as_of_date: Optional[date] = None
) -> Optional[Decimal]:
    """
    Get latest value for a macro indicator from database.

    Args:
        indicator_id: FRED series ID (e.g., "DGS10", "UNRATE")
        as_of_date: Get value as of this date (default: latest available)

    Returns:
        Indicator value as Decimal, or None if not found

    Example:
        # Get latest 10Y Treasury rate
        dgs10 = await get_latest_indicator_value("DGS10")
        if dgs10:
            risk_free_rate = dgs10 / 100  # Convert percent to decimal
    """
    if as_of_date:
        query = """
            SELECT value
            FROM macro_indicators
            WHERE indicator_id = $1
                AND date <= $2
            ORDER BY date DESC
            LIMIT 1
        """
        row = await execute_query_one(query, indicator_id, as_of_date)
    else:
        query = """
            SELECT value
            FROM macro_indicators
            WHERE indicator_id = $1
            ORDER BY date DESC
            LIMIT 1
        """
        row = await execute_query_one(query, indicator_id)

    if row:
        return Decimal(str(row["value"]))
    return None


async def get_risk_free_rate(as_of_date: Optional[date] = None) -> Decimal:
    """
    Get risk-free rate from DGS10 (10Y Treasury).

    Args:
        as_of_date: Get rate as of this date (default: latest)

    Returns:
        Risk-free rate as decimal (e.g., 0.045 for 4.5%)
        Falls back to 0.03 (3%) if no data available

    Example:
        rf_rate = await get_risk_free_rate()
        sharpe = (portfolio_return - rf_rate) / portfolio_vol
    """
    dgs10 = await get_latest_indicator_value("DGS10", as_of_date)

    if dgs10 is not None:
        # DGS10 is in percent (e.g., 4.5), convert to decimal (0.045)
        return dgs10 / Decimal("100")

    # Fallback: Conservative 3% if no data
    logger.warning(
        f"DGS10 not available for {as_of_date or 'latest'}, using 3% fallback"
    )
    return Decimal("0.03")


async def get_indicator_percentile(
    indicator_id: str,
    percentile: int,
    lookback_days: int = 252
) -> Optional[Decimal]:
    """
    Calculate percentile value for an indicator over lookback window.

    Args:
        indicator_id: FRED series ID
        percentile: Percentile to calculate (0-100)
        lookback_days: Historical window (default: 252 trading days)

    Returns:
        Percentile value, or None if insufficient data

    Example:
        # Get 80th percentile VIX over last year
        vix_80th = await get_indicator_percentile("VIX", 80, 252)
    """
    lookback_start = date.today() - timedelta(days=lookback_days)

    query = """
        SELECT value
        FROM macro_indicators
        WHERE indicator_id = $1
            AND date >= $2
        ORDER BY date DESC
    """
    rows = await execute_query(query, indicator_id, lookback_start)

    if not rows or len(rows) < 30:  # Need minimum data points
        logger.warning(
            f"Insufficient data for percentile: {indicator_id} "
            f"(found {len(rows) if rows else 0} points, need 30+)"
        )
        return None

    values = [float(row["value"]) for row in rows]
    values.sort()

    # Calculate percentile index
    index = int((percentile / 100.0) * len(values))
    index = min(index, len(values) - 1)

    return Decimal(str(values[index]))
```

**Why This Approach**:
- ✅ Follows existing patterns (similar to `execute_query()`)
- ✅ No new dependencies (uses existing db connection)
- ✅ Simple functions, easy to test
- ✅ Non-breaking (new file, doesn't change existing code)

---

### Phase 2: Deprecate Constants, Add Migration Path (GRADUAL)
**Effort**: 6-8 hours
**Risk**: LOW (both old and new work side-by-side)

#### Step 2.1: Mark Constants as Deprecated
**Files to Update**:
- `backend/app/core/constants/financial.py`
- `backend/app/core/constants/risk.py`
- `backend/app/core/constants/scenarios.py`

**Changes**:
```python
# financial.py - ADD DEPRECATION WARNINGS

# DEPRECATED: Use macro_data_helpers.get_risk_free_rate() instead
# This constant is stale and does not reflect current market conditions.
# Will be removed in v2.0.0
DEFAULT_SHARPE_RISK_FREE_RATE = Decimal("0.0")  # DEPRECATED

# risk.py - ADD DEPRECATION WARNINGS

# DEPRECATED: Use macro_data_helpers.get_risk_free_rate() instead
DEFAULT_RISK_FREE_RATE = Decimal("0.0")  # DEPRECATED

# scenarios.py - ADD DEPRECATION WARNINGS

# DEPRECATED: Use macro_data_helpers.get_risk_free_rate() instead
DEFAULT_OPTIMIZATION_RISK_FREE_RATE = Decimal("0.02")  # DEPRECATED
```

**Why Deprecate Instead of Remove**:
- ✅ Non-breaking (old code still works)
- ✅ Clear migration path
- ✅ Can remove in future version
- ✅ Gives time to find/fix all usages

---

#### Step 2.2: Add Helper to Constants Module (BRIDGE)
**File**: `backend/app/core/constants/__init__.py`

**Add**:
```python
# Re-export macro data helpers for convenience
from app.services.macro_data_helpers import (
    get_risk_free_rate,
    get_latest_indicator_value,
    get_indicator_percentile,
)

__all__ = [
    # ... existing exports
    # Macro data helpers (NEW)
    "get_risk_free_rate",
    "get_latest_indicator_value",
    "get_indicator_percentile",
]
```

**Why**:
- ✅ Convenient imports (from app.core.constants import get_risk_free_rate)
- ✅ Discoverability (constants module is well-known)
- ✅ Non-breaking (adds new, doesn't remove old)

---

### Phase 3: Update Services (ONE AT A TIME)
**Effort**: 12-16 hours
**Risk**: MEDIUM (changes calculations, need testing)

#### Migration Pattern (SAFE)
**For each service file**:

1. **Import new helper**:
```python
# OLD
from app.core.constants.scenarios import DEFAULT_OPTIMIZATION_RISK_FREE_RATE

# NEW (add alongside old, don't remove yet)
from app.services.macro_data_helpers import get_risk_free_rate
```

2. **Update function signature** (make async if needed):
```python
# OLD
def compute_sharpe(portfolio_return: float, portfolio_vol: float) -> float:
    return (portfolio_return - DEFAULT_SHARPE_RISK_FREE_RATE) / portfolio_vol

# NEW (async)
async def compute_sharpe(portfolio_return: float, portfolio_vol: float) -> float:
    rf_rate = await get_risk_free_rate()
    return (portfolio_return - float(rf_rate)) / portfolio_vol
```

3. **Update callers** (propagate async):
```python
# OLD
sharpe = compute_sharpe(ret, vol)

# NEW
sharpe = await compute_sharpe(ret, vol)
```

4. **Test thoroughly**:
```python
# Test with mock data
async def test_compute_sharpe_uses_current_rate():
    # Ensure DGS10 exists in test database
    await execute_statement("""
        INSERT INTO macro_indicators (indicator_id, date, value, units)
        VALUES ('DGS10', CURRENT_DATE, 4.5, 'Percent')
    """)

    # Compute Sharpe
    sharpe = await compute_sharpe(0.10, 0.15)  # 10% return, 15% vol

    # Expected: (0.10 - 0.045) / 0.15 = 0.367
    assert abs(sharpe - 0.367) < 0.01
```

---

#### Priority Order for Service Updates

**BATCH 1: High-Impact, Low-Risk** (4-6 hours)
1. ✅ `backend/app/services/optimizer.py` (3 instances)
   - Lines 990, 1214, 1222, 1231, 1240
   - Impact: Portfolio optimizer will use current rates
   - Risk: LOW (optimizer has comprehensive tests)

**BATCH 2: Medium-Impact** (4-6 hours)
2. ✅ `backend/scripts/seed_portfolio_performance_clean.py` (2 instances)
   - Lines 42, 362
   - Impact: Test data generation
   - Risk: VERY LOW (dev script only)

3. ✅ `backend/scripts/seed_portfolio_performance_data.py` (2 instances)
   - Lines 43, 350
   - Impact: Test data generation
   - Risk: VERY LOW (dev script only)

**BATCH 3: Low-Impact** (4-6 hours)
4. ✅ Remove hardcoded 252, 0.95, 365 in services
   - Use constants instead (code review Issue C2-C4)
   - Impact: Consistency
   - Risk: LOW (pure refactor)

---

## 🚫 What NOT to Do (Anti-Patterns)

### ❌ DO NOT Add Redis
**Why**: No existing Redis usage in services layer. Adding new dependency is disruptive.

**Alternative**: Use database queries (fast with indexes) or simple in-memory cache.

---

### ❌ DO NOT Create New Service Classes
**Why**: MacroService already exists and fetches macro data.

**Alternative**: Use simple helper functions (like execute_query()).

---

### ❌ DO NOT Change Database Schema
**Why**: `macro_indicators` table is perfect as-is.

**Alternative**: Query existing table.

---

### ❌ DO NOT Add New API Calls
**Why**: FRED data is already fetched and stored by MacroService.

**Alternative**: Query database, not external API.

---

### ❌ DO NOT Remove Constants Immediately
**Why**: Breaking change, need migration period.

**Alternative**: Deprecate first, remove in v2.0.0.

---

## 📊 Validation Checklist

Before starting, verify these assumptions:

### Database Validation
```bash
# Check if macro_indicators table exists
SELECT COUNT(*) FROM macro_indicators WHERE indicator_id = 'DGS10';

# Expected: > 0 rows (data exists)
# If 0: Run populate_fred_data.py first
```

### Service Pattern Validation
```python
# Check if execute_query() works
from app.db.connection import execute_query
rows = await execute_query("SELECT 1 AS test")
assert rows[0]["test"] == 1
```

### FRED Data Freshness
```sql
-- Check latest DGS10 date
SELECT MAX(date) FROM macro_indicators WHERE indicator_id = 'DGS10';

-- Expected: Recent date (within last week)
-- If stale: Run MacroService.fetch_indicators()
```

---

## 🧪 Testing Strategy

### Unit Tests (NEW)
**File**: `backend/tests/services/test_macro_data_helpers.py`

```python
import pytest
from datetime import date
from decimal import Decimal
from app.services.macro_data_helpers import (
    get_risk_free_rate,
    get_latest_indicator_value,
    get_indicator_percentile,
)
from app.db.connection import execute_statement

@pytest.mark.asyncio
async def test_get_risk_free_rate():
    """Test risk-free rate fetching from DGS10"""
    # Setup: Insert test data
    await execute_statement("""
        INSERT INTO macro_indicators (indicator_id, date, value, units)
        VALUES ('DGS10', '2025-11-07', 4.5, 'Percent')
        ON CONFLICT DO NOTHING
    """)

    # Test
    rf_rate = await get_risk_free_rate()

    # Verify
    assert rf_rate == Decimal("0.045")  # 4.5% as decimal

@pytest.mark.asyncio
async def test_get_risk_free_rate_fallback():
    """Test fallback when DGS10 not available"""
    # Test with non-existent indicator
    rf_rate = await get_risk_free_rate(as_of_date=date(1900, 1, 1))

    # Verify fallback to 3%
    assert rf_rate == Decimal("0.03")
```

---

### Integration Tests (MODIFY EXISTING)
**File**: `backend/tests/services/test_optimizer.py`

```python
@pytest.mark.asyncio
async def test_optimizer_uses_current_risk_free_rate():
    """Verify optimizer uses dynamic risk-free rate"""
    # Setup: Ensure DGS10 data exists
    await execute_statement("""
        INSERT INTO macro_indicators (indicator_id, date, value)
        VALUES ('DGS10', CURRENT_DATE, 4.5)
        ON CONFLICT (indicator_id, date) DO UPDATE SET value = 4.5
    """)

    # Run optimizer
    optimizer = PortfolioOptimizer()
    result = await optimizer.compute_optimal_weights(
        portfolio_id=TEST_PORTFOLIO_ID,
        lookback_days=252
    )

    # Verify: Risk-free rate in result should be ~4.5%
    # (specific assertion depends on optimizer output structure)
    assert result.risk_free_rate >= 0.04
    assert result.risk_free_rate <= 0.05
```

---

### Regression Tests (CRITICAL)
**Purpose**: Ensure numeric outputs don't change unexpectedly

```python
@pytest.mark.asyncio
async def test_sharpe_ratio_regression():
    """Ensure Sharpe ratios are in expected range after refactor"""
    # Setup: Known portfolio with known return/vol
    portfolio_return = 0.10  # 10%
    portfolio_vol = 0.15     # 15%

    # Ensure DGS10 = 3% (for consistent test)
    await execute_statement("""
        INSERT INTO macro_indicators (indicator_id, date, value)
        VALUES ('DGS10', CURRENT_DATE, 3.0)
        ON CONFLICT (indicator_id, date) DO UPDATE SET value = 3.0
    """)

    # Calculate Sharpe
    sharpe = await compute_sharpe(portfolio_return, portfolio_vol)

    # Expected: (0.10 - 0.03) / 0.15 = 0.467
    expected = (0.10 - 0.03) / 0.15
    assert abs(sharpe - expected) < 0.01  # Within 1% tolerance
```

---

## 📅 Implementation Timeline

### Week 1: Setup & Validation (Non-Breaking)
**Days 1-2**: Validate assumptions
- [ ] Verify DGS10 data exists in macro_indicators
- [ ] Check FRED data freshness
- [ ] Confirm execute_query() pattern

**Days 3-5**: Create helpers
- [ ] Create `macro_data_helpers.py`
- [ ] Write unit tests
- [ ] Add to constants `__init__.py`

**Deliverable**: New helpers available, zero code changes

---

### Week 2: Deprecation & Documentation (Non-Breaking)
**Days 1-3**: Mark constants deprecated
- [ ] Add deprecation warnings to constants
- [ ] Update documentation
- [ ] Create migration guide

**Days 4-5**: Update tests
- [ ] Add regression tests
- [ ] Update integration tests
- [ ] Verify nothing breaks

**Deliverable**: Clear deprecation path, all tests pass

---

### Week 3: Service Migration (Breaking Changes Begin)
**Days 1-2**: Batch 1 (Optimizer)
- [ ] Update optimizer.py (3 instances)
- [ ] Run optimizer tests
- [ ] Verify outputs match expected

**Days 3-4**: Batch 2 (Scripts)
- [ ] Update seed scripts (4 instances)
- [ ] Regenerate test data
- [ ] Verify data quality

**Day 5**: Batch 3 (Magic Numbers)
- [ ] Replace hardcoded 252, 0.95, 365
- [ ] Run full test suite
- [ ] Fix any regressions

**Deliverable**: Services use dynamic data, tests pass

---

## 🎯 Success Criteria

### Functional
- [ ] `get_risk_free_rate()` returns current DGS10 value
- [ ] All services use dynamic risk-free rate
- [ ] No hardcoded 252, 0.95, 365 in services
- [ ] Sharpe ratios within 5% of expected values

### Non-Functional
- [ ] All existing tests pass
- [ ] No new dependencies added
- [ ] Query performance < 50ms (database has indexes)
- [ ] Code coverage >= 80% for new helpers

### Documentation
- [ ] Migration guide created
- [ ] Deprecation warnings added
- [ ] Inline documentation updated
- [ ] Code review comments addressed

---

## 🚨 Rollback Plan

If issues arise:

### Immediate Rollback (Same Day)
1. Revert service changes (git revert)
2. Keep deprecated constants (they still work)
3. Remove macro_data_helpers.py import

### Partial Rollback (Per Service)
1. Revert individual service files
2. Keep helpers available (for future use)
3. Update only low-risk services first

### Full Rollback (Emergency)
1. Git revert entire refactor branch
2. Document issues found
3. Plan improved approach

---

## 📝 Migration Guide for Developers

### Before (OLD)
```python
from app.core.constants.scenarios import DEFAULT_OPTIMIZATION_RISK_FREE_RATE

def compute_sharpe(portfolio_return, portfolio_vol):
    return (portfolio_return - DEFAULT_OPTIMIZATION_RISK_FREE_RATE) / portfolio_vol

# Usage
sharpe = compute_sharpe(0.10, 0.15)
```

### After (NEW)
```python
from app.services.macro_data_helpers import get_risk_free_rate

async def compute_sharpe(portfolio_return, portfolio_vol):
    rf_rate = await get_risk_free_rate()
    return (portfolio_return - float(rf_rate)) / portfolio_vol

# Usage (now async)
sharpe = await compute_sharpe(0.10, 0.15)
```

### Key Changes
1. **Import changed**: From constants to macro_data_helpers
2. **Function is async**: Must use `async def` and `await`
3. **Callers must await**: Propagate async up the call stack
4. **Type changed**: Decimal instead of float (convert with `float()`)

---

## 🎓 Lessons from Existing Code

### Pattern 1: MacroService Already Does This
**Evidence**: `macro.py:469-495`

MacroService.get_latest_indicator() already queries macro_indicators table. Our helpers just wrap this pattern for reuse.

**Lesson**: We're not inventing new patterns, just making existing patterns reusable.

---

### Pattern 2: execute_query() is the Standard
**Evidence**: Used in 20+ service files

All services use `execute_query()` / `execute_query_one()` for database access.

**Lesson**: Follow this pattern, don't create new database abstractions.

---

### Pattern 3: Simple Functions Over Classes
**Evidence**: `fred_transformation.py` has standalone functions

DawsOS prefers simple functions over heavyweight classes when possible.

**Lesson**: `get_risk_free_rate()` as function, not RiskFreeRateService class.

---

## 🏁 Conclusion

This plan is **conservative** and **non-disruptive** because:

✅ **Leverages existing infrastructure** (MacroService, macro_indicators table)
✅ **Follows existing patterns** (execute_query(), simple functions)
✅ **Non-breaking migration** (deprecate, don't remove)
✅ **Validates all assumptions** (check database before starting)
✅ **Testable in isolation** (new helpers can be tested independently)
✅ **Rollback-friendly** (each service updated independently)

**Risk Level**: **LOW-MEDIUM**
**Effort**: **22-30 hours** over 3 weeks
**ROI**: **VERY HIGH** (fixes critical calculation bug, enables accurate metrics)

---

**Status**: Ready for approval and execution
**Next Step**: Validate database has DGS10 data, then create macro_data_helpers.py

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
