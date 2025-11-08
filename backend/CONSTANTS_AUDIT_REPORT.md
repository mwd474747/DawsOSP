# Constants Usage Audit Report

**Generated:** 2025-11-07
**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/app/core/constants/`
**Scope:** All constants modules in backend codebase

---

## Executive Summary

This audit analyzed **274 constants** across **9 modules** to identify actually unused constants that can be safely removed from the codebase.

### Key Findings

- **Total Constants:** 274
- **Used Constants:** 104 (38.0%)
- **Unused Constants:** 170 (62.0%)
- **Duplicate Constants:** 5 (across different modules)

### Utilization by Module

| Module | Total | Used | Unused | Utilization |
|--------|-------|------|--------|-------------|
| **macro.py** | 34 | 33 | 1 | 97.1% ✅ |
| **scenarios.py** | 39 | 33 | 6 | 84.6% ✅ |
| **http_status.py** | 19 | 9 | 10 | 47.4% ⚠️ |
| **network.py** | 12 | 4 | 8 | 33.3% ⚠️ |
| **integration.py** | 40 | 12 | 28 | 30.0% ❌ |
| **risk.py** | 22 | 3 | 19 | 13.6% ❌ |
| **financial.py** | 25 | 3 | 22 | 12.0% ❌ |
| **validation.py** | 47 | 4 | 43 | 8.5% ❌ |
| **time_periods.py** | 36 | 3 | 33 | 8.3% ❌ |

---

## Summary Table

```
Module                    Total    Used     Unused   Utilization
--------------------------------------------------------------------------------
financial.py              25       3        22       12.0%
risk.py                   22       3        19       13.6%
macro.py                  34       33       1        97.1%
scenarios.py              39       33       6        84.6%
integration.py            40       12       28       30.0%
validation.py             47       4        43       8.5%
time_periods.py           36       3        33       8.3%
network.py                12       4        8        33.3%
http_status.py            19       9        10       47.4%
--------------------------------------------------------------------------------
TOTAL                     274      104      170      38.0%
```

---

## Detailed Findings by Module

### 1. financial.py (12.0% utilization) ❌

**Status:** CRITICAL - Most constants unused

**Used Constants (3):**
- `TRADING_DAYS_PER_YEAR` - 10 usages ⭐
- `MONTHS_PER_YEAR` - 2 usages (⚠️ DUPLICATE with time_periods.py)
- `WEEKS_PER_YEAR` - 2 usages (⚠️ DUPLICATE with time_periods.py)

**Unused Constants (22):**
```
CALENDAR_DAYS_PER_YEAR
BUSINESS_DAYS_PER_WEEK
LOOKBACK_1_MONTH
LOOKBACK_3_MONTHS
LOOKBACK_6_MONTHS
LOOKBACK_1_YEAR
LOOKBACK_3_YEARS
LOOKBACK_5_YEARS
VOLATILITY_WINDOWS_DEFAULT
ANNUALIZATION_DAYS
MIN_RETURNS_FOR_VOLATILITY
MIN_RETURNS_FOR_SHARPE
MIN_RETURNS_FOR_BETA
MIN_VALID_SHARPE_RATIO
MAX_VALID_SHARPE_RATIO
MIN_VALID_INFORMATION_RATIO
MAX_VALID_INFORMATION_RATIO
MIN_VALID_VOLATILITY
MAX_VALID_VOLATILITY
PRICING_PACK_STALE_DAYS
MAX_DAILY_PRICE_CHANGE_PERCENT
MIN_VALID_PRICE
```

**Recommendation:** Remove all unused constants. Consider if the module should be deprecated entirely (88% unused).

---

### 2. risk.py (13.6% utilization) ❌

**Status:** CRITICAL - Most constants unused

**Used Constants (3):**
- `CONFIDENCE_LEVEL_95` - 5 usages
- `VAR_LOOKBACK_DAYS` - 5 usages
- `DEFAULT_TRACKING_ERROR_PERIODS` - 3 usages

**Unused Constants (19):**
```
CONFIDENCE_LEVEL_99
SIGNIFICANCE_LEVEL_5
SIGNIFICANCE_LEVEL_1
DEFAULT_VAR_CONFIDENCE
DEFAULT_CVAR_CONFIDENCE
STANDARD_DEVIATIONS_1
STANDARD_DEVIATIONS_2
STANDARD_DEVIATIONS_3
Z_SCORE_THRESHOLD_MODERATE
Z_SCORE_THRESHOLD_SEVERE
MIN_SIGNIFICANT_FACTOR_LOADING
MAX_FACTOR_CONCENTRATION
MIN_FACTOR_MODEL_R_SQUARED
TRACKING_ERROR_PASSIVE_MAX
TRACKING_ERROR_ACTIVE_MIN
TRACKING_ERROR_ACTIVE_MAX
TRACKING_ERROR_AGGRESSIVE_MIN
DEFAULT_MAR
SORTINO_LOOKBACK_DAYS
```

**Recommendation:** Remove all unused constants. Many appear to be planned features never implemented.

---

### 3. macro.py (97.1% utilization) ✅

**Status:** EXCELLENT - Nearly all constants used

**Used Constants (33):** Top usages:
- `ZSCORE_AVERAGE` - 8 usages
- `ZSCORE_SLIGHTLY_ABOVE` - 8 usages
- `MIN_REGIME_PROBABILITY` - 8 usages
- `ZSCORE_SLIGHTLY_BELOW` - 6 usages
- And 29 more...

**Unused Constants (1):**
```
DEFAULT_REGIME_PROBABILITY
```

**Recommendation:** Remove `DEFAULT_REGIME_PROBABILITY`. Module is well-maintained.

---

### 4. scenarios.py (84.6% utilization) ✅

**Status:** GOOD - Most constants actively used

**Used Constants (33):** Top usages:
- `DEFAULT_SHOCK_BPS` - 4 usages
- `SEVERITY_MODERATE` - 4 usages
- `DEFAULT_SHOCK_PCT` - 3 usages
- And 30 more deleveraging scenario constants...

**Unused Constants (6):**
```
MAX_SCENARIO_PROBABILITY
MAX_QUALITY_SCORE
SEVERITY_LOW
METHOD_RISK_PARITY
METHOD_MAX_SHARPE
METHOD_CVAR
```

**Recommendation:** Remove unused optimization methods (may be planned features). Keep severity levels if planning alerts.

---

### 5. integration.py (30.0% utilization) ⚠️

**Status:** NEEDS CLEANUP - Many unused API constants

**Used Constants (12):** Top usages:
- `DEFAULT_MAX_RETRIES` - 10 usages
- `DEFAULT_RETRY_DELAY` - 10 usages
- `FRED_RATE_LIMIT_REQUESTS` - 5 usages
- `DEFAULT_HTTP_TIMEOUT` - 3 usages
- `FMP_RATE_LIMIT_REQUESTS` - 3 usages
- And 7 more...

**Unused Constants (28):**
```
FRED_API_TIMEOUT
FMP_API_TIMEOUT
POLYGON_API_TIMEOUT
NEWS_API_TIMEOUT
DEFAULT_READ_TIMEOUT
DEFAULT_BACKOFF_FACTOR
MAX_RETRY_DELAY
DEFAULT_RATE_LIMIT_REQUESTS
DEFAULT_RATE_LIMIT_WINDOW
FMP_RATE_LIMIT_WINDOW
POLYGON_RATE_LIMIT_WINDOW
NEWS_API_RATE_LIMIT_WINDOW
CACHE_TTL_REALTIME
CACHE_TTL_SHORT
CACHE_TTL_MEDIUM
CACHE_TTL_LONG
CACHE_TTL_VERY_LONG
CACHE_TTL_HISTORICAL
STALE_DATA_THRESHOLD_MARKET
STALE_DATA_THRESHOLD_PRICING
STALE_DATA_THRESHOLD_METRICS
CACHE_GC_INTERVAL
DEFAULT_BATCH_SIZE
MAX_BATCH_SIZE
MIN_BATCH_SIZE
BATCH_REQUEST_DELAY
MIN_TIME_SERIES_DATA_POINTS
MAX_TIME_SERIES_GAP_DAYS
```

**Recommendation:** Remove all unused caching and batch processing constants. Consider if planned cache layer was abandoned.

---

### 6. validation.py (8.5% utilization) ❌

**Status:** CRITICAL - Almost entirely unused

**Used Constants (4):**
- `DEFAULT_ALERT_COOLDOWN_HOURS` - 3 usages
- `DEFAULT_ALERT_LOOKBACK_HOURS` - 2 usages
- `MOCK_DATA_RANDOM_MIN` - 2 usages
- `MOCK_DATA_RANDOM_MAX` - 2 usages

**Unused Constants (43):**
```
ALERT_COOLDOWN_EXTENDED
ALERT_COOLDOWN_WEEKLY
VIX_ELEVATED_THRESHOLD
VIX_HIGH_THRESHOLD
VIX_EXTREME_THRESHOLD
UNEMPLOYMENT_LOW_THRESHOLD
UNEMPLOYMENT_NORMAL_THRESHOLD
UNEMPLOYMENT_HIGH_THRESHOLD
MAX_DRAWDOWN_WARNING
MAX_DRAWDOWN_ALERT
MAX_DRAWDOWN_CRITICAL
SHARPE_POOR
SHARPE_ACCEPTABLE
SHARPE_GOOD
SHARPE_EXCELLENT
VOLATILITY_LOW
VOLATILITY_MODERATE
VOLATILITY_HIGH
VOLATILITY_EXTREME
QUALITY_SCORE_POOR
QUALITY_SCORE_FAIR
QUALITY_SCORE_GOOD
QUALITY_SCORE_EXCELLENT
DIVIDEND_SAFETY_RISK
DIVIDEND_SAFETY_FAIR
DIVIDEND_SAFETY_SAFE
PRICE_CHANGE_SMALL
PRICE_CHANGE_MODERATE
PRICE_CHANGE_LARGE
PRICE_CHANGE_EXTREME
SENTIMENT_VERY_NEGATIVE
SENTIMENT_NEGATIVE
SENTIMENT_NEUTRAL
SENTIMENT_POSITIVE
SENTIMENT_VERY_POSITIVE
MIN_DATA_POINTS_CORRELATION
MIN_DATA_POINTS_VOLATILITY
MIN_DATA_POINTS_REGRESSION
MAX_STALENESS_REALTIME
MAX_STALENESS_DAILY
MAX_STALENESS_WEEKLY
PRICE_CHANGE_MAX_MULTIPLIER
PRICE_CHANGE_MIN_MULTIPLIER
```

**Recommendation:** Remove all unused thresholds. Many appear to be for planned alerting/validation features never implemented.

---

### 7. time_periods.py (8.3% utilization) ❌

**Status:** CRITICAL - Almost entirely unused

**Used Constants (3):**
- `TRADING_DAYS_PER_YEAR` - 10 usages (⚠️ DUPLICATE with financial.py)
- `WEEKS_PER_YEAR` - 2 usages (⚠️ DUPLICATE with financial.py)
- `MONTHS_PER_YEAR` - 2 usages (⚠️ DUPLICATE with financial.py)

**Unused Constants (33):**
```
SECONDS_PER_MINUTE
SECONDS_PER_HOUR
SECONDS_PER_DAY
SECONDS_PER_WEEK
SECONDS_PER_MONTH_AVG
SECONDS_PER_YEAR
MINUTES_PER_HOUR
MINUTES_PER_DAY
MINUTES_PER_WEEK
HOURS_PER_DAY
HOURS_PER_WEEK
DAYS_PER_WEEK
DAYS_PER_MONTH_AVG
DAYS_PER_YEAR
DAYS_PER_LEAP_YEAR
WEEKS_PER_MONTH_AVG
MONTHS_PER_QUARTER
PERIOD_1_DAY
PERIOD_1_WEEK
PERIOD_2_WEEKS
PERIOD_1_MONTH
PERIOD_3_MONTHS
PERIOD_6_MONTHS
PERIOD_1_YEAR
PERIOD_2_YEARS
PERIOD_3_YEARS
PERIOD_5_YEARS
PERIOD_10_YEARS
TRADING_DAYS_PER_WEEK
TRADING_DAYS_PER_MONTH
TRADING_DAYS_PER_QUARTER
WEEKEND_DAYS_PER_YEAR
HOLIDAY_DAYS_PER_YEAR
```

**Recommendation:** Remove all unused constants. Module has 92% waste. Consider deprecating entire module.

---

### 8. network.py (33.3% utilization) ⚠️

**Status:** NEEDS CLEANUP - Many unused network configs

**Used Constants (4):**
- `DEFAULT_API_PORT` - 2 usages
- `DEFAULT_COMBINED_SERVER_PORT` - 2 usages
- `DEFAULT_CONNECTION_TIMEOUT` - 2 usages (⚠️ DUPLICATE with integration.py)
- `ALL_INTERFACES` - 2 usages

**Unused Constants (8):**
```
POSTGRES_DEFAULT_PORT
REDIS_DEFAULT_PORT
DEFAULT_DB_POOL_MIN_SIZE
DEFAULT_DB_POOL_MAX_SIZE
DEFAULT_DB_POOL_TIMEOUT
DEFAULT_DB_QUERY_TIMEOUT
LONG_RUNNING_QUERY_TIMEOUT
LOCALHOST
```

**Recommendation:** Remove all unused database pool and timeout constants.

---

### 9. http_status.py (47.4% utilization) ⚠️

**Status:** ACCEPTABLE - About half used

**Used Constants (9):** Top usages:
- `HTTP_500_INTERNAL_SERVER_ERROR` - 57 usages ⭐⭐⭐
- `HTTP_400_BAD_REQUEST` - 17 usages ⭐
- `HTTP_403_FORBIDDEN` - 14 usages ⭐
- `HTTP_401_UNAUTHORIZED` - 12 usages
- `HTTP_404_NOT_FOUND` - 10 usages
- `HTTP_503_SERVICE_UNAVAILABLE` - 10 usages
- `HTTP_204_NO_CONTENT` - 4 usages
- `HTTP_201_CREATED` - 2 usages
- `RETRYABLE_STATUS_CODES` - 2 usages (⚠️ DUPLICATE with integration.py)

**Unused Constants (10):**
```
HTTP_200_OK
HTTP_202_ACCEPTED
HTTP_422_UNPROCESSABLE_ENTITY
HTTP_429_TOO_MANY_REQUESTS
HTTP_502_BAD_GATEWAY
HTTP_504_GATEWAY_TIMEOUT
SUCCESS_STATUS_CODES
CLIENT_ERROR_STATUS_CODES
SERVER_ERROR_STATUS_CODES
STATUS_CODE_DESCRIPTIONS
```

**Recommendation:** Keep unused HTTP codes (may be used in future). Remove unused aggregate lists.

---

## Duplicate Constants Across Modules

The following constants are defined in multiple modules, creating potential inconsistencies:

### 1. DEFAULT_CONNECTION_TIMEOUT
- **Modules:** `integration.py`, `network.py`
- **Recommendation:** Keep in `network.py` (networking concerns), remove from `integration.py`

### 2. MONTHS_PER_YEAR
- **Modules:** `financial.py`, `time_periods.py`
- **Recommendation:** Keep in `time_periods.py` (canonical location), remove from `financial.py`

### 3. RETRYABLE_STATUS_CODES
- **Modules:** `integration.py`, `http_status.py`
- **Recommendation:** Keep in `http_status.py` (HTTP concerns), remove from `integration.py`

### 4. TRADING_DAYS_PER_YEAR
- **Modules:** `financial.py`, `time_periods.py`
- **Recommendation:** Keep in `financial.py` (domain-specific, more widely used), remove from `time_periods.py`

### 5. WEEKS_PER_YEAR
- **Modules:** `financial.py`, `time_periods.py`
- **Recommendation:** Keep in `time_periods.py` (canonical location), remove from `financial.py`

---

## Complete List: All Unused Constants (170)

### financial.py (22 unused)
```python
CALENDAR_DAYS_PER_YEAR
BUSINESS_DAYS_PER_WEEK
LOOKBACK_1_MONTH
LOOKBACK_3_MONTHS
LOOKBACK_6_MONTHS
LOOKBACK_1_YEAR
LOOKBACK_3_YEARS
LOOKBACK_5_YEARS
VOLATILITY_WINDOWS_DEFAULT
ANNUALIZATION_DAYS
MIN_RETURNS_FOR_VOLATILITY
MIN_RETURNS_FOR_SHARPE
MIN_RETURNS_FOR_BETA
MIN_VALID_SHARPE_RATIO
MAX_VALID_SHARPE_RATIO
MIN_VALID_INFORMATION_RATIO
MAX_VALID_INFORMATION_RATIO
MIN_VALID_VOLATILITY
MAX_VALID_VOLATILITY
PRICING_PACK_STALE_DAYS
MAX_DAILY_PRICE_CHANGE_PERCENT
MIN_VALID_PRICE
```

### risk.py (19 unused)
```python
CONFIDENCE_LEVEL_99
SIGNIFICANCE_LEVEL_5
SIGNIFICANCE_LEVEL_1
DEFAULT_VAR_CONFIDENCE
DEFAULT_CVAR_CONFIDENCE
STANDARD_DEVIATIONS_1
STANDARD_DEVIATIONS_2
STANDARD_DEVIATIONS_3
Z_SCORE_THRESHOLD_MODERATE
Z_SCORE_THRESHOLD_SEVERE
MIN_SIGNIFICANT_FACTOR_LOADING
MAX_FACTOR_CONCENTRATION
MIN_FACTOR_MODEL_R_SQUARED
TRACKING_ERROR_PASSIVE_MAX
TRACKING_ERROR_ACTIVE_MIN
TRACKING_ERROR_ACTIVE_MAX
TRACKING_ERROR_AGGRESSIVE_MIN
DEFAULT_MAR
SORTINO_LOOKBACK_DAYS
```

### macro.py (1 unused)
```python
DEFAULT_REGIME_PROBABILITY
```

### scenarios.py (6 unused)
```python
MAX_SCENARIO_PROBABILITY
MAX_QUALITY_SCORE
SEVERITY_LOW
METHOD_RISK_PARITY
METHOD_MAX_SHARPE
METHOD_CVAR
```

### integration.py (28 unused)
```python
FRED_API_TIMEOUT
FMP_API_TIMEOUT
POLYGON_API_TIMEOUT
NEWS_API_TIMEOUT
DEFAULT_READ_TIMEOUT
DEFAULT_BACKOFF_FACTOR
MAX_RETRY_DELAY
DEFAULT_RATE_LIMIT_REQUESTS
DEFAULT_RATE_LIMIT_WINDOW
FMP_RATE_LIMIT_WINDOW
POLYGON_RATE_LIMIT_WINDOW
NEWS_API_RATE_LIMIT_WINDOW
CACHE_TTL_REALTIME
CACHE_TTL_SHORT
CACHE_TTL_MEDIUM
CACHE_TTL_LONG
CACHE_TTL_VERY_LONG
CACHE_TTL_HISTORICAL
STALE_DATA_THRESHOLD_MARKET
STALE_DATA_THRESHOLD_PRICING
STALE_DATA_THRESHOLD_METRICS
CACHE_GC_INTERVAL
DEFAULT_BATCH_SIZE
MAX_BATCH_SIZE
MIN_BATCH_SIZE
BATCH_REQUEST_DELAY
MIN_TIME_SERIES_DATA_POINTS
MAX_TIME_SERIES_GAP_DAYS
```

### validation.py (43 unused)
```python
ALERT_COOLDOWN_EXTENDED
ALERT_COOLDOWN_WEEKLY
VIX_ELEVATED_THRESHOLD
VIX_HIGH_THRESHOLD
VIX_EXTREME_THRESHOLD
UNEMPLOYMENT_LOW_THRESHOLD
UNEMPLOYMENT_NORMAL_THRESHOLD
UNEMPLOYMENT_HIGH_THRESHOLD
MAX_DRAWDOWN_WARNING
MAX_DRAWDOWN_ALERT
MAX_DRAWDOWN_CRITICAL
SHARPE_POOR
SHARPE_ACCEPTABLE
SHARPE_GOOD
SHARPE_EXCELLENT
VOLATILITY_LOW
VOLATILITY_MODERATE
VOLATILITY_HIGH
VOLATILITY_EXTREME
QUALITY_SCORE_POOR
QUALITY_SCORE_FAIR
QUALITY_SCORE_GOOD
QUALITY_SCORE_EXCELLENT
DIVIDEND_SAFETY_RISK
DIVIDEND_SAFETY_FAIR
DIVIDEND_SAFETY_SAFE
PRICE_CHANGE_SMALL
PRICE_CHANGE_MODERATE
PRICE_CHANGE_LARGE
PRICE_CHANGE_EXTREME
SENTIMENT_VERY_NEGATIVE
SENTIMENT_NEGATIVE
SENTIMENT_NEUTRAL
SENTIMENT_POSITIVE
SENTIMENT_VERY_POSITIVE
MIN_DATA_POINTS_CORRELATION
MIN_DATA_POINTS_VOLATILITY
MIN_DATA_POINTS_REGRESSION
MAX_STALENESS_REALTIME
MAX_STALENESS_DAILY
MAX_STALENESS_WEEKLY
PRICE_CHANGE_MAX_MULTIPLIER
PRICE_CHANGE_MIN_MULTIPLIER
```

### time_periods.py (33 unused)
```python
SECONDS_PER_MINUTE
SECONDS_PER_HOUR
SECONDS_PER_DAY
SECONDS_PER_WEEK
SECONDS_PER_MONTH_AVG
SECONDS_PER_YEAR
MINUTES_PER_HOUR
MINUTES_PER_DAY
MINUTES_PER_WEEK
HOURS_PER_DAY
HOURS_PER_WEEK
DAYS_PER_WEEK
DAYS_PER_MONTH_AVG
DAYS_PER_YEAR
DAYS_PER_LEAP_YEAR
WEEKS_PER_MONTH_AVG
MONTHS_PER_QUARTER
PERIOD_1_DAY
PERIOD_1_WEEK
PERIOD_2_WEEKS
PERIOD_1_MONTH
PERIOD_3_MONTHS
PERIOD_6_MONTHS
PERIOD_1_YEAR
PERIOD_2_YEARS
PERIOD_3_YEARS
PERIOD_5_YEARS
PERIOD_10_YEARS
TRADING_DAYS_PER_WEEK
TRADING_DAYS_PER_MONTH
TRADING_DAYS_PER_QUARTER
WEEKEND_DAYS_PER_YEAR
HOLIDAY_DAYS_PER_YEAR
```

### network.py (8 unused)
```python
POSTGRES_DEFAULT_PORT
REDIS_DEFAULT_PORT
DEFAULT_DB_POOL_MIN_SIZE
DEFAULT_DB_POOL_MAX_SIZE
DEFAULT_DB_POOL_TIMEOUT
DEFAULT_DB_QUERY_TIMEOUT
LONG_RUNNING_QUERY_TIMEOUT
LOCALHOST
```

### http_status.py (10 unused)
```python
HTTP_200_OK
HTTP_202_ACCEPTED
HTTP_422_UNPROCESSABLE_ENTITY
HTTP_429_TOO_MANY_REQUESTS
HTTP_502_BAD_GATEWAY
HTTP_504_GATEWAY_TIMEOUT
SUCCESS_STATUS_CODES
CLIENT_ERROR_STATUS_CODES
SERVER_ERROR_STATUS_CODES
STATUS_CODE_DESCRIPTIONS
```

---

## Recommendations

### Immediate Actions (High Priority)

1. **Remove validation.py unused constants (43 constants)** - 91.5% waste
2. **Remove time_periods.py unused constants (33 constants)** - 91.7% waste
3. **Remove integration.py cache/batch constants (28 constants)** - Abandoned features
4. **Remove financial.py unused constants (22 constants)** - 88% waste
5. **Remove risk.py unused constants (19 constants)** - 86.4% waste

### Medium Priority

6. **Resolve duplicates:**
   - Move `TRADING_DAYS_PER_YEAR` to `financial.py` only
   - Move `MONTHS_PER_YEAR` and `WEEKS_PER_YEAR` to `time_periods.py` only
   - Move `DEFAULT_CONNECTION_TIMEOUT` to `network.py` only
   - Move `RETRYABLE_STATUS_CODES` to `http_status.py` only

7. **Clean up network.py** - Remove 8 unused DB pool constants

### Low Priority

8. **Consider removing unused http_status.py aggregates** (keep individual codes)
9. **Remove scenarios.py unused optimization methods** (6 constants)
10. **Remove macro.py single unused constant**

### Potential Impact

- **Lines of code reduced:** ~500+ (constants + comments)
- **Maintenance burden reduced:** 62% fewer constants to track
- **Code clarity improved:** Only used constants remain
- **Duplicates eliminated:** 5 duplicate definitions resolved

---

## Methodology

This audit used automated grep-based searches to find actual usage of each constant across the entire `/Users/mdawson/Documents/GitHub/DawsOSP/backend` directory.

**Search criteria:**
- Whole-word matching (`grep -w`)
- Excluded definition files themselves
- Excluded `__init__.py` re-exports
- Counted actual usage in service files, routes, scripts, etc.

**Files searched:** All `.py` files in backend directory

**Validation:** Each constant was searched independently to ensure accurate counts.

---

## Next Steps

1. Review this report with the team
2. Verify critical constants before removal (some may be in frontend/tests)
3. Create removal branches for each module
4. Remove unused constants in phases
5. Update `__init__.py` to remove exports
6. Run full test suite after each removal
7. Update documentation to reflect streamlined constants

---

**End of Report**
