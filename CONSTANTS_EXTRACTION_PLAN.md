# Constants Extraction Plan - Parallel Work

**Date**: November 7, 2025
**Status**: 🟢 READY TO START (Can work in parallel with Phase 2)
**Purpose**: Extract magic numbers to named constants for better maintainability

---

## Executive Summary

While the main IDE agent works on Phase 2 (Singleton Removal), I can work in parallel on extracting magic numbers to named constants. This is a low-risk, high-value task that:

✅ **Does NOT conflict** with Phase 2 DI work (different files/concerns)
✅ **Improves code clarity** immediately
✅ **Makes values easier to maintain** (change in one place)
✅ **Follows Phase 7** of TECHNICAL_DEBT_REMOVAL_PLAN_V3.md

---

## Scope

### Files with Magic Numbers (100+ files identified)

From grep search, high-concentration files include:
- Financial calculations (pricing, metrics, attribution)
- Time periods (252 trading days, 365 days, 12 months)
- Risk thresholds (0.95, 0.05 confidence intervals)
- Service configurations (timeouts, retries, limits)

### What to Extract

**Priority 1 - Financial Constants** (Most critical):
```python
# Trading days
TRADING_DAYS_PER_YEAR = 252
CALENDAR_DAYS_PER_YEAR = 365
MONTHS_PER_YEAR = 12
WEEKS_PER_YEAR = 52

# Statistical thresholds
CONFIDENCE_LEVEL_95 = 0.95
SIGNIFICANCE_LEVEL_5 = 0.05
STANDARD_DEVIATIONS_2 = 2.0

# Risk thresholds
DEFAULT_VAR_CONFIDENCE = 0.95
DEFAULT_CVAR_CONFIDENCE = 0.95
```

**Priority 2 - Service Configuration** (High value):
```python
# API timeouts
DEFAULT_API_TIMEOUT = 30
DEFAULT_HTTP_TIMEOUT = 30.0
DEFAULT_FRED_TIMEOUT = 30

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_BACKOFF_FACTOR = 2.0

# Rate limiting
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60
```

**Priority 3 - Data Processing** (Medium value):
```python
# Batch sizes
DEFAULT_BATCH_SIZE = 100
MAX_BATCH_SIZE = 1000

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Data freshness
DEFAULT_CACHE_TTL = 300  # 5 minutes
STALE_DATA_THRESHOLD = 86400  # 24 hours
```

---

## Implementation Approach

### Step 1: Create Constants Module

**File**: `backend/app/core/constants.py`

```python
"""
DawsOS Application Constants

This module contains all application-wide constants to avoid magic numbers
throughout the codebase. Constants are organized by domain.
"""

# =============================================================================
# FINANCIAL CONSTANTS
# =============================================================================

# Trading Calendar
TRADING_DAYS_PER_YEAR = 252
CALENDAR_DAYS_PER_YEAR = 365
MONTHS_PER_YEAR = 12
WEEKS_PER_YEAR = 52
BUSINESS_DAYS_PER_WEEK = 5

# Statistical Measures
CONFIDENCE_LEVEL_95 = 0.95
CONFIDENCE_LEVEL_99 = 0.99
SIGNIFICANCE_LEVEL_5 = 0.05
SIGNIFICANCE_LEVEL_1 = 0.01
STANDARD_DEVIATIONS_1 = 1.0
STANDARD_DEVIATIONS_2 = 2.0
STANDARD_DEVIATIONS_3 = 3.0

# Risk Metrics
DEFAULT_VAR_CONFIDENCE = 0.95
DEFAULT_CVAR_CONFIDENCE = 0.95
DEFAULT_TRACKING_ERROR_PERIODS = 252  # 1 year
DEFAULT_SHARPE_RISK_FREE_RATE = 0.0

# Performance Thresholds
MIN_SHARPE_RATIO = -3.0
MAX_SHARPE_RATIO = 10.0
MIN_INFORMATION_RATIO = -5.0
MAX_INFORMATION_RATIO = 5.0

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Timeouts (seconds)
DEFAULT_API_TIMEOUT = 30
DEFAULT_HTTP_TIMEOUT = 30.0
DEFAULT_FRED_TIMEOUT = 30
DEFAULT_FMP_TIMEOUT = 30
DEFAULT_POLYGON_TIMEOUT = 30
DEFAULT_NEWS_TIMEOUT = 30

# Retry Configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_BACKOFF_FACTOR = 2.0
MAX_RETRY_DELAY = 60.0

# Rate Limiting
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds
FMP_RATE_LIMIT_REQUESTS = 300
FMP_RATE_LIMIT_WINDOW = 60
FRED_RATE_LIMIT_REQUESTS = 120
FRED_RATE_LIMIT_WINDOW = 60

# =============================================================================
# DATA PROCESSING
# =============================================================================

# Batch Sizes
DEFAULT_BATCH_SIZE = 100
MAX_BATCH_SIZE = 1000
MIN_BATCH_SIZE = 10

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000
MIN_PAGE_SIZE = 1

# Cache Configuration
DEFAULT_CACHE_TTL = 300  # 5 minutes
SHORT_CACHE_TTL = 60     # 1 minute
LONG_CACHE_TTL = 3600    # 1 hour
STALE_DATA_THRESHOLD = 86400  # 24 hours

# Database Query Limits
DEFAULT_QUERY_LIMIT = 1000
MAX_QUERY_LIMIT = 10000

# =============================================================================
# TIME PERIODS
# =============================================================================

# Seconds
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800

# Minutes
MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 1440

# Days
DAYS_PER_WEEK = 7
DAYS_PER_MONTH_AVG = 30
DAYS_PER_YEAR = 365

# =============================================================================
# ALERTING
# =============================================================================

# Alert Thresholds
DEFAULT_ALERT_THRESHOLD = 0.05  # 5%
HIGH_ALERT_THRESHOLD = 0.10     # 10%
CRITICAL_ALERT_THRESHOLD = 0.20 # 20%

# Alert Delivery
MAX_ALERT_RETRY_ATTEMPTS = 3
ALERT_RETRY_DELAY = 300  # 5 minutes
ALERT_BATCH_SIZE = 100

# =============================================================================
# OPTIMIZATION
# =============================================================================

# Optimizer Constraints
DEFAULT_MIN_WEIGHT = 0.0
DEFAULT_MAX_WEIGHT = 0.30  # 30%
DEFAULT_TARGET_RETURN = 0.08  # 8%
DEFAULT_RISK_TOLERANCE = 0.15  # 15%

# Solver Configuration
DEFAULT_MAX_ITERATIONS = 1000
DEFAULT_SOLVER_TOLERANCE = 1e-6

# =============================================================================
# VALIDATION
# =============================================================================

# Data Quality
MIN_DATA_POINTS_REQUIRED = 30
MIN_PRICE_VALUE = 0.01
MAX_PRICE_CHANGE_PERCENT = 0.50  # 50% in one day (suspicious)

# Portfolio Constraints
MIN_PORTFOLIO_VALUE = 0
MAX_PORTFOLIO_POSITIONS = 10000
MIN_POSITION_SIZE = 0.0001  # $0.01 minimum

# =============================================================================
# FEATURE FLAGS
# =============================================================================

# Development flags (can be overridden by environment)
ENABLE_CACHING = True
ENABLE_RATE_LIMITING = True
ENABLE_ALERTS = True
ENABLE_BACKGROUND_TASKS = True
```

### Step 2: Migration Strategy

**Approach**: Gradual, file-by-file migration

1. Start with high-value files (metrics, pricing, scenarios)
2. Replace magic numbers with constants
3. Add imports: `from app.core.constants import *`
4. Run tests after each file
5. Create PR for review

**Example Migration**:

**Before**:
```python
# backend/app/services/metrics.py
sharpe_ratio = (returns.mean() * 252) / (returns.std() * math.sqrt(252))
var_95 = np.percentile(returns, 5)
```

**After**:
```python
# backend/app/services/metrics.py
from app.core.constants import (
    TRADING_DAYS_PER_YEAR,
    CONFIDENCE_LEVEL_95,
    SIGNIFICANCE_LEVEL_5,
)

sharpe_ratio = (returns.mean() * TRADING_DAYS_PER_YEAR) / (
    returns.std() * math.sqrt(TRADING_DAYS_PER_YEAR)
)
var_95 = np.percentile(returns, SIGNIFICANCE_LEVEL_5 * 100)
```

### Step 3: Testing Strategy

**For Each Migrated File**:
1. ✅ Run unit tests for that module
2. ✅ Run integration tests if applicable
3. ✅ Verify numeric outputs match exactly (no logic changes)
4. ✅ Check for unintended constant usage

**Test Example**:
```python
# tests/test_constants_migration.py
def test_sharpe_ratio_unchanged():
    """Verify Sharpe ratio calculation unchanged after constants migration"""
    # Before (magic numbers)
    old_sharpe = (returns.mean() * 252) / (returns.std() * math.sqrt(252))

    # After (constants)
    new_sharpe = calculate_sharpe_ratio(returns)

    assert abs(old_sharpe - new_sharpe) < 1e-10
```

---

## Priority Order (Can work in parallel with Phase 2)

### Week 1: High-Value Financial Files
1. ✅ Create `constants.py` module
2. ⏳ Migrate `services/metrics.py`
3. ⏳ Migrate `services/pricing.py`
4. ⏳ Migrate `services/scenarios.py`
5. ⏳ Migrate `services/risk_metrics.py`
6. ⏳ Migrate `services/currency_attribution.py`
7. ⏳ Migrate `services/factor_analysis.py`

**Estimated Time**: 4-6 hours

### Week 2: Service Configuration Files
8. ⏳ Migrate `integrations/rate_limiter.py`
9. ⏳ Migrate `integrations/base_provider.py`
10. ⏳ Migrate `integrations/fred_provider.py`
11. ⏳ Migrate `integrations/fmp_provider.py`
12. ⏳ Migrate `integrations/polygon_provider.py`
13. ⏳ Migrate `services/alerts.py`

**Estimated Time**: 3-4 hours

### Week 3: API Routes and Jobs
14. ⏳ Migrate API routes (`api/routes/*.py`)
15. ⏳ Migrate background jobs (`jobs/*.py`)
16. ⏳ Migrate remaining services

**Estimated Time**: 4-6 hours

**Total Estimated Time**: 11-16 hours (spread over 2-3 weeks)

---

## Why This Works in Parallel

### ✅ No Conflicts with Phase 2 (Singleton Removal)

**Phase 2 focuses on**:
- Dependency injection
- Service initialization order
- Singleton → DI migration
- `combined_server.py` changes

**Constants extraction focuses on**:
- Replacing magic numbers
- Creating constants module
- Updating imports
- No initialization changes

**Zero Overlap**: Different files, different concerns

### ✅ Low Risk

- No logic changes (just naming)
- Easy to verify (numeric outputs identical)
- Easy to rollback (git revert)
- Doesn't affect initialization order
- Doesn't affect dependency injection

### ✅ High Value

- Immediate code clarity improvement
- Makes future changes easier (change value once)
- Self-documenting (named constants explain purpose)
- Prevents copy-paste errors

---

## Coordination with Main IDE Agent

### Communication Protocol

**Before starting each file**:
1. Check if main agent is working on that file
2. If yes, skip and move to next file
3. If no, proceed with migration

**Git Workflow**:
1. Pull latest changes before each migration
2. Work on separate branch: `constants-extraction`
3. Small, focused commits per file or related group
4. Regular pushes to avoid merge conflicts

**Commit Message Format**:
```
refactor: extract magic numbers to constants in [module]

- Created/Updated constants.py with [DOMAIN] constants
- Replaced magic numbers in [file.py]
- No logic changes (verified by tests)

Part of Phase 7 (Constants Extraction)
```

---

## Success Criteria

### Quantitative
- ✅ Zero magic numbers in migrated files
- ✅ All constants documented
- ✅ All tests passing after migration
- ✅ Numeric outputs identical (within floating point precision)

### Qualitative
- ✅ Code more readable
- ✅ Constants logically organized
- ✅ Easy to find and update values
- ✅ Self-documenting code

---

## Risk Mitigation

### Risk: Breaking Calculations
**Mitigation**: Verify numeric outputs match exactly before/after

### Risk: Merge Conflicts with Phase 2
**Mitigation**: Work on different files, coordinate before commits

### Risk: Using Wrong Constant
**Mitigation**: Clear naming, code review, tests verify correctness

### Risk: Missing Some Magic Numbers
**Mitigation**: Grep search after migration, code review

---

## Ready to Start?

**Answer: YES ✅**

**Reasons**:
1. ✅ Plan is detailed and clear
2. ✅ No conflicts with Phase 2 work
3. ✅ Low risk, high value
4. ✅ Can start immediately on Week 1 files
5. ✅ Testing strategy in place

**First Steps**:
1. Create `backend/app/core/constants.py`
2. Start with `services/metrics.py` migration
3. Run tests to verify
4. Commit and push
5. Move to next file

---

**Status**: 🟢 READY TO START
**Can Work in Parallel**: YES ✅
**Estimated Duration**: 11-16 hours over 2-3 weeks
**Risk Level**: LOW
**Value**: HIGH

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
