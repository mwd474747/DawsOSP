# Domain-Driven Constants Extraction Plan
## Aligned with DawsOS Data Architecture & Broader Refactoring Strategy

**Date**: November 7, 2025
**Status**: 🎯 READY FOR IMPLEMENTATION
**Alignment**: Phase 7 of TECHNICAL_DEBT_REMOVAL_PLAN_V3.md
**Domain Expert**: Data Integration & Architecture Focus

---

## Executive Summary

This plan extracts magic numbers into domain-driven constants that reflect **DawsOS's actual business logic** and **data architecture**. Unlike a generic constants file, this approach:

✅ **Aligns with domain model**: Financial, Macro, Risk, Attribution domains
✅ **Matches data architecture**: Time-series, valuation, factor analysis
✅ **Supports broader refactoring**: Phase 2 (DI), Phase 1 (Exception Handling)
✅ **Enables data validation**: Constants become contract specifications
✅ **Improves maintainability**: Domain experts can update values

---

## Domain Analysis: DawsOS Core Domains

Based on codebase analysis and [DATABASE.md](DATABASE.md):

### 1. **Portfolio Valuation Domain**
- Services: `PricingService`, `MetricsService`
- Tables: `portfolio_daily_values`, `lots`, `pricing_packs`
- Key Constants: Trading days, annualization factors, lookback periods

### 2. **Risk Analytics Domain**
- Services: `RiskMetricsService`, `FactorAnalysisService`, `CurrencyAttributionService`
- Tables: `factor_exposures`, `currency_attribution`
- Key Constants: Confidence levels, VaR/CVaR thresholds, factor loadings

### 3. **Macro Regime Domain**
- Services: `MacroService`, `CyclesService`, `MacroAwareScenariosService`
- Tables: `economic_indicators`, `macro_regime_detections`, `indicator_configurations`
- Key Constants: Z-score thresholds, regime change triggers, indicator weights

### 4. **Scenario Analysis Domain**
- Services: `ScenariosService`, `OptimizerService`
- Tables: `scenarios`, `scenario_results`
- Key Constants: Monte Carlo iterations, optimization tolerances, constraint bounds

### 5. **Data Integration Domain**
- Services: `FREDProvider`, `FMPProvider`, `PolygonProvider`
- Key Constants: API timeouts, rate limits, retry policies, data freshness thresholds

---

## Constants Architecture (Domain-Driven)

### File Structure

```
backend/app/core/constants/
├── __init__.py                    # Public API
├── financial.py                   # Portfolio valuation constants
├── risk.py                        # Risk analytics constants
├── macro.py                       # Macro regime constants
├── scenarios.py                   # Scenario analysis constants
├── integration.py                 # External API constants
├── validation.py                  # Data quality thresholds
└── time_periods.py                # Reusable time period constants
```

**Rationale**: Domain-specific files make it clear which constants apply to which business logic.

---

## Detailed Constants Specification

### 1. Financial Domain Constants (`financial.py`)

```python
"""
Portfolio Valuation & Performance Measurement Constants

Domain: Portfolio management, performance attribution
Sources: Industry standards (GIPS, CFA Institute)
"""

# =============================================================================
# TRADING CALENDAR CONSTANTS
# =============================================================================

# Industry Standard: 252 trading days per year (NYSE/NASDAQ calendar)
# Source: Excludes weekends + major holidays (~104 weekend days + 9 holidays)
TRADING_DAYS_PER_YEAR = 252

# Calendar days for annualization
CALENDAR_DAYS_PER_YEAR = 365

# Period conversions
MONTHS_PER_YEAR = 12
WEEKS_PER_YEAR = 52
BUSINESS_DAYS_PER_WEEK = 5

# Common lookback periods (in trading days)
LOOKBACK_1_MONTH = 21      # ~1 month of trading
LOOKBACK_3_MONTHS = 63     # ~3 months of trading
LOOKBACK_6_MONTHS = 126    # ~6 months of trading
LOOKBACK_1_YEAR = 252      # 1 year of trading
LOOKBACK_3_YEARS = 756     # 3 years of trading
LOOKBACK_5_YEARS = 1260    # 5 years of trading

# Volatility windows (used in metrics.py:460, 515)
VOLATILITY_WINDOWS_DEFAULT = [30, 90, 252]  # Short, medium, long-term vol

# =============================================================================
# RETURN CALCULATION CONSTANTS
# =============================================================================

# Annualization factors
# TWR: (1 + return)^(365/days) - 1
# MWR: Uses IRR with 365-day year (metrics.py:299)
ANNUALIZATION_DAYS = 365

# Minimum data points for reliable statistics
MIN_RETURNS_FOR_VOLATILITY = 2   # Need at least 2 returns for std dev
MIN_RETURNS_FOR_SHARPE = 30      # Industry best practice (1 month)
MIN_RETURNS_FOR_BETA = 252       # Need 1 year for reliable beta

# =============================================================================
# PERFORMANCE THRESHOLDS
# =============================================================================

# Sharpe Ratio bounds (for validation)
# Typical range: -3 to +10 (outside this suggests data error)
MIN_VALID_SHARPE_RATIO = -3.0
MAX_VALID_SHARPE_RATIO = 10.0

# Information Ratio bounds
MIN_VALID_INFORMATION_RATIO = -5.0
MAX_VALID_INFORMATION_RATIO = 5.0

# Volatility bounds (annualized)
MIN_VALID_VOLATILITY = 0.001   # 0.1% (too low suggests data issue)
MAX_VALID_VOLATILITY = 5.0     # 500% (too high suggests data issue)

# =============================================================================
# PRICING PACK CONFIGURATION
# =============================================================================

# Pricing pack freshness threshold (in days)
# After this many days without update, pack is considered stale
PRICING_PACK_STALE_DAYS = 7

# Maximum allowed price change in single day (for validation)
# 50% = stock halted or data error
MAX_DAILY_PRICE_CHANGE_PERCENT = 0.50

# Minimum price value (for validation)
MIN_VALID_PRICE = 0.01  # Penny stocks threshold
```

**Usage Example**:
```python
# Before (metrics.py:184)
vol = float(np.std(returns) * np.sqrt(252))

# After
from app.core.constants.financial import TRADING_DAYS_PER_YEAR

vol = float(np.std(returns) * np.sqrt(TRADING_DAYS_PER_YEAR))
```

---

### 2. Risk Analytics Constants (`risk.py`)

```python
"""
Risk Metrics & Factor Analysis Constants

Domain: VaR, CVaR, factor exposures, risk decomposition
Sources: Basel III, industry best practices
"""

# =============================================================================
# VAR/CVAR CONSTANTS
# =============================================================================

# Confidence levels (industry standard)
# 95% = 1 in 20 days expected to exceed VaR
# 99% = 1 in 100 days expected to exceed VaR
CONFIDENCE_LEVEL_95 = 0.95
CONFIDENCE_LEVEL_99 = 0.99

# Significance levels (inverse of confidence)
SIGNIFICANCE_LEVEL_5 = 0.05   # 5th percentile for VaR_95
SIGNIFICANCE_LEVEL_1 = 0.01   # 1st percentile for VaR_99

# Default confidence levels
DEFAULT_VAR_CONFIDENCE = 0.95
DEFAULT_CVAR_CONFIDENCE = 0.95

# Lookback period for VaR calculation
# Industry standard: 252 trading days (1 year)
VAR_LOOKBACK_DAYS = 252

# =============================================================================
# STATISTICAL THRESHOLDS
# =============================================================================

# Standard deviation multiples (for outlier detection)
# 2σ = 95% confidence interval
# 3σ = 99.7% confidence interval
STANDARD_DEVIATIONS_1 = 1.0
STANDARD_DEVIATIONS_2 = 2.0
STANDARD_DEVIATIONS_3 = 3.0

# Z-score thresholds for anomaly detection
Z_SCORE_THRESHOLD_MODERATE = 2.0   # ~95% confidence
Z_SCORE_THRESHOLD_SEVERE = 3.0     # ~99.7% confidence

# =============================================================================
# FACTOR ANALYSIS CONSTANTS
# =============================================================================

# Minimum factor loading to be considered significant
# Below this, factor exposure is negligible
MIN_SIGNIFICANT_FACTOR_LOADING = 0.05  # 5%

# Maximum factor concentration
# Prevents over-exposure to single factor
MAX_FACTOR_CONCENTRATION = 0.50  # 50%

# R-squared threshold for model quality
# Below this, factor model is unreliable
MIN_FACTOR_MODEL_R_SQUARED = 0.30  # 30%

# =============================================================================
# TRACKING ERROR CONSTANTS
# =============================================================================

# Tracking error calculation period (default 1 year)
DEFAULT_TRACKING_ERROR_PERIODS = 252

# Tracking error thresholds (for validation)
# Passive fund: <2%, Active fund: 2-6%, Aggressive: >6%
TRACKING_ERROR_PASSIVE_MAX = 0.02
TRACKING_ERROR_ACTIVE_MIN = 0.02
TRACKING_ERROR_ACTIVE_MAX = 0.06

# =============================================================================
# DOWNSIDE RISK CONSTANTS
# =============================================================================

# Minimum Acceptable Return (MAR) for downside deviation
# Default: 0% (any negative return is "downside")
DEFAULT_MAR = 0.0

# Sortino ratio calculation (uses downside deviation)
# Same lookback as Sharpe for consistency
SORTINO_LOOKBACK_DAYS = 252
```

**Usage Example**:
```python
# Before (scattered across risk files)
var_95 = np.percentile(returns, 5)
z_threshold = 2.0

# After
from app.core.constants.risk import (
    SIGNIFICANCE_LEVEL_5,
    Z_SCORE_THRESHOLD_MODERATE,
)

var_95 = np.percentile(returns, SIGNIFICANCE_LEVEL_5 * 100)
z_threshold = Z_SCORE_THRESHOLD_MODERATE
```

---

### 3. Macro Regime Constants (`macro.py`)

```python
"""
Macro Economic Regime Detection Constants

Domain: Macro indicators, regime changes, cycle detection
Sources: Economic research, DawsOS proprietary models
"""

# =============================================================================
# REGIME DETECTION THRESHOLDS
# =============================================================================

# Z-score thresholds for regime change detection
# Used in cycles.py for composite indicator z-scores
REGIME_CHANGE_Z_SCORE_THRESHOLD = 1.5

# Minimum duration for regime to be considered stable
# Prevents false positives from short-term noise
MIN_REGIME_DURATION_DAYS = 90  # ~3 months

# Lookback period for regime detection
# How much history to use for calculating indicator statistics
REGIME_DETECTION_LOOKBACK_DAYS = 1260  # 5 years of trading data

# =============================================================================
# INDICATOR WEIGHTING
# =============================================================================

# Default weights for composite indicators (must sum to 1.0)
# Can be overridden per indicator in indicator_configurations table
DEFAULT_INDICATOR_WEIGHT = 1.0 / 7  # Equal weight for 7 indicators

# Weight bounds (for validation)
MIN_INDICATOR_WEIGHT = 0.0
MAX_INDICATOR_WEIGHT = 1.0

# =============================================================================
# DATA FRESHNESS REQUIREMENTS
# =============================================================================

# Maximum age for economic indicator data (in days)
# After this, data is considered stale
MAX_INDICATOR_AGE_DAYS = 90  # 3 months (some indicators are quarterly)

# Minimum data points required for regime detection
# Need sufficient history for statistical reliability
MIN_INDICATOR_DATA_POINTS = 60  # ~5 years of monthly data

# =============================================================================
# CYCLE IDENTIFICATION CONSTANTS
# =============================================================================

# Typical cycle durations (for validation)
# Economic cycles generally range from 2-10 years
MIN_CYCLE_DURATION_MONTHS = 24   # 2 years
MAX_CYCLE_DURATION_MONTHS = 120  # 10 years

# Peak/trough detection sensitivity
# How much change required to identify turning point
MIN_CYCLE_AMPLITUDE_PERCENT = 0.10  # 10% change

# =============================================================================
# FRED DATA INTEGRATION
# =============================================================================

# FRED API update frequency (days)
# How often to check for new data
FRED_UPDATE_CHECK_FREQUENCY_DAYS = 1  # Daily

# FRED series categories (for organization)
# Used in fred_transformation.py
FRED_CATEGORY_LEADING = "leading"
FRED_CATEGORY_COINCIDENT = "coincident"
FRED_CATEGORY_LAGGING = "lagging"
```

**Usage Example**:
```python
# Before (cycles.py)
z_threshold = 1.5
min_duration = 90

# After
from app.core.constants.macro import (
    REGIME_CHANGE_Z_SCORE_THRESHOLD,
    MIN_REGIME_DURATION_DAYS,
)

z_threshold = REGIME_CHANGE_Z_SCORE_THRESHOLD
min_duration = MIN_REGIME_DURATION_DAYS
```

---

### 4. Scenario Analysis Constants (`scenarios.py`)

```python
"""
Monte Carlo Simulation & Portfolio Optimization Constants

Domain: Scenario generation, stress testing, portfolio construction
Sources: Quantitative finance literature
"""

# =============================================================================
# MONTE CARLO SIMULATION
# =============================================================================

# Default number of simulation paths
# More paths = more accurate but slower
MONTE_CARLO_PATHS_DEFAULT = 10000
MONTE_CARLO_PATHS_QUICK = 1000    # For quick estimates
MONTE_CARLO_PATHS_PRECISE = 100000  # For final analysis

# Simulation time horizon (years)
DEFAULT_SIMULATION_HORIZON_YEARS = 1
LONG_TERM_HORIZON_YEARS = 10

# Random seed for reproducibility (None = random)
DEFAULT_RANDOM_SEED = None

# =============================================================================
# PORTFOLIO OPTIMIZATION
# =============================================================================

# Weight constraints (min/max portfolio weight per security)
DEFAULT_MIN_WEIGHT = 0.0      # Allow zero position
DEFAULT_MAX_WEIGHT = 0.30     # 30% maximum (diversification)

# Position count constraints
MIN_PORTFOLIO_POSITIONS = 10   # Minimum for diversification
MAX_PORTFOLIO_POSITIONS = 100  # Maximum for manageability

# Target return (annualized)
DEFAULT_TARGET_RETURN = 0.08  # 8% per year

# Risk tolerance (annualized volatility)
DEFAULT_RISK_TOLERANCE = 0.15  # 15% volatility

# =============================================================================
# SOLVER CONFIGURATION
# =============================================================================

# Optimization solver settings
DEFAULT_SOLVER = "ECOS"  # Embedded Conic Solver
ALTERNATIVE_SOLVER = "SCS"  # Splitting Conic Solver

# Maximum iterations before solver stops
DEFAULT_MAX_ITERATIONS = 1000

# Convergence tolerance
DEFAULT_SOLVER_TOLERANCE = 1e-6

# Solver timeout (seconds)
DEFAULT_SOLVER_TIMEOUT = 60

# =============================================================================
# SCENARIO WEIGHTING
# =============================================================================

# Probability weights for different scenarios
# Used in macro_aware_scenarios.py
SCENARIO_WEIGHT_BASE = 0.50      # 50% probability for base case
SCENARIO_WEIGHT_EXPANSION = 0.25  # 25% for expansion
SCENARIO_WEIGHT_RECESSION = 0.25  # 25% for recession

# Stress test severity levels
STRESS_TEST_MILD = 1.0      # 1σ shock
STRESS_TEST_MODERATE = 2.0  # 2σ shock
STRESS_TEST_SEVERE = 3.0    # 3σ shock
STRESS_TEST_EXTREME = 4.0   # 4σ shock (tail risk)

# =============================================================================
# VALIDATION BOUNDS
# =============================================================================

# Maximum allowed leverage
MAX_LEVERAGE = 1.0  # 100% invested (no margin)

# Minimum cash allocation
MIN_CASH_PERCENT = 0.0

# Maximum turnover per rebalance
MAX_TURNOVER_PERCENT = 0.50  # 50% of portfolio
```

---

### 5. Data Integration Constants (`integration.py`)

```python
"""
External API Integration Constants

Domain: FRED, FMP, Polygon, News APIs
Sources: API documentation, rate limit specs
"""

# =============================================================================
# API TIMEOUT CONFIGURATION
# =============================================================================

# Default timeout for all HTTP requests (seconds)
DEFAULT_HTTP_TIMEOUT = 30.0

# Provider-specific timeouts
FRED_API_TIMEOUT = 30
FMP_API_TIMEOUT = 30
POLYGON_API_TIMEOUT = 30
NEWS_API_TIMEOUT = 15  # News APIs typically faster

# Connection timeout (seconds)
# Time to wait for initial connection
DEFAULT_CONNECTION_TIMEOUT = 10

# Read timeout (seconds)
# Time to wait for response after connection
DEFAULT_READ_TIMEOUT = 30

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================

# Maximum retry attempts for failed requests
DEFAULT_MAX_RETRIES = 3

# Initial retry delay (seconds)
DEFAULT_RETRY_DELAY = 1.0

# Backoff multiplier for exponential backoff
# Delay = initial_delay * (backoff_factor ^ attempt)
DEFAULT_BACKOFF_FACTOR = 2.0

# Maximum retry delay (seconds)
# Caps exponential backoff
MAX_RETRY_DELAY = 60.0

# Status codes to retry on
RETRYABLE_STATUS_CODES = [429, 500, 502, 503, 504]

# =============================================================================
# RATE LIMITING
# =============================================================================

# Generic rate limits
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds

# FRED API rate limits
# Source: https://fred.stlouisfed.org/docs/api/rate_limits.html
FRED_RATE_LIMIT_REQUESTS = 120
FRED_RATE_LIMIT_WINDOW = 60

# FMP API rate limits (free tier)
# Source: https://site.financialmodelingprep.com/developer/docs/pricing
FMP_RATE_LIMIT_REQUESTS = 300
FMP_RATE_LIMIT_WINDOW = 60

# Polygon API rate limits (basic tier)
# Source: https://polygon.io/pricing
POLYGON_RATE_LIMIT_REQUESTS = 5
POLYGON_RATE_LIMIT_WINDOW = 1  # Per second

# NewsAPI rate limits (free tier)
NEWS_API_RATE_LIMIT_REQUESTS = 100
NEWS_API_RATE_LIMIT_WINDOW = 86400  # Per day

# =============================================================================
# DATA CACHING
# =============================================================================

# Cache TTL (time-to-live) in seconds
CACHE_TTL_SHORT = 60        # 1 minute (for volatile data)
CACHE_TTL_MEDIUM = 300      # 5 minutes (for market data)
CACHE_TTL_LONG = 3600       # 1 hour (for reference data)
CACHE_TTL_VERY_LONG = 86400  # 24 hours (for historical data)

# Stale data threshold (seconds)
# After this, cached data is considered stale
STALE_DATA_THRESHOLD = 86400  # 24 hours

# =============================================================================
# BATCH PROCESSING
# =============================================================================

# Default batch size for bulk API requests
DEFAULT_BATCH_SIZE = 100
MAX_BATCH_SIZE = 1000
MIN_BATCH_SIZE = 10

# Delay between batch requests (to respect rate limits)
BATCH_REQUEST_DELAY = 0.1  # 100ms

# =============================================================================
# DATA QUALITY
# =============================================================================

# Minimum data points required for time series
MIN_TIME_SERIES_DATA_POINTS = 30

# Maximum allowed gap in time series (days)
# Larger gaps may indicate data quality issue
MAX_TIME_SERIES_GAP_DAYS = 7
```

**Integration with Rate Limiter**:
```python
# Before (rate_limiter.py)
max_calls = 100
window = 60

# After
from app.core.constants.integration import (
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_RATE_LIMIT_WINDOW,
)

max_calls = DEFAULT_RATE_LIMIT_REQUESTS
window = DEFAULT_RATE_LIMIT_WINDOW
```

---

### 6. Data Validation Constants (`validation.py`)

```python
"""
Data Quality & Validation Thresholds

Domain: Data contracts, quality checks, validation rules
Supports: Phase 2 data quality improvements
"""

# =============================================================================
# PORTFOLIO VALIDATION
# =============================================================================

# Portfolio value bounds (for validation)
MIN_PORTFOLIO_VALUE = 0
MAX_PORTFOLIO_VALUE = 1e12  # $1 trillion (sanity check)

# Position size bounds
MIN_POSITION_SIZE = 0.0001  # $0.01 minimum
MAX_POSITION_SIZE_PERCENT = 0.99  # 99% of portfolio (sanity check)

# Quantity bounds
MIN_QUANTITY = 0.0001  # Fractional shares allowed
MAX_QUANTITY = 1e9  # 1 billion shares (sanity check)

# =============================================================================
# PRICING VALIDATION
# =============================================================================

# Price bounds (for validation)
MIN_VALID_PRICE = 0.01  # Penny stocks
MAX_VALID_PRICE = 1e6  # $1 million per share (Berkshire Hathaway-level)

# Price change validation
# Exceeding this suggests data error or circuit breaker
MAX_DAILY_PRICE_CHANGE_PERCENT = 0.50  # 50%

# Bid-ask spread validation
# Exceeding this suggests illiquid market or data error
MAX_BID_ASK_SPREAD_PERCENT = 0.10  # 10%

# =============================================================================
# RETURNS VALIDATION
# =============================================================================

# Return bounds (for validation)
# Exceeding these suggests data error
MIN_VALID_RETURN = -0.99  # -99% (total loss)
MAX_VALID_RETURN = 10.0   # 1000% (exceptional gain)

# Volatility bounds (annualized)
MIN_VALID_VOLATILITY = 0.001  # 0.1% (very stable)
MAX_VALID_VOLATILITY = 5.0    # 500% (very volatile)

# =============================================================================
# DATA COMPLETENESS
# =============================================================================

# Minimum data points for statistical calculations
MIN_DATA_POINTS_VOLATILITY = 30   # 1 month
MIN_DATA_POINTS_CORRELATION = 60  # 2 months
MIN_DATA_POINTS_REGRESSION = 252  # 1 year

# Missing data tolerance (percentage)
# Above this, dataset is considered incomplete
MAX_MISSING_DATA_PERCENT = 0.10  # 10%

# =============================================================================
# TIME-SERIES VALIDATION
# =============================================================================

# Maximum allowed gap in time series (trading days)
MAX_TIME_SERIES_GAP_DAYS = 7

# Minimum frequency for time series (days)
MIN_TIME_SERIES_FREQUENCY_DAYS = 1  # Daily

# =============================================================================
# FIELD NAME VALIDATION
# =============================================================================

# Critical field names (must match database exactly)
# Prevents bugs like the valuation_date vs asof_date issue
REQUIRED_DATE_FIELD_PORTFOLIO = "valuation_date"  # portfolio_daily_values
REQUIRED_DATE_FIELD_FACTORS = "asof_date"         # factor_exposures
REQUIRED_DATE_FIELD_ATTRIBUTION = "asof_date"     # currency_attribution

# Quantity field names (standardized in migration 001)
QUANTITY_FIELD_OPEN = "quantity_open"
QUANTITY_FIELD_ORIGINAL = "quantity_original"
```

**Usage for Data Contracts**:
```python
# Example data contract validation
from app.core.constants.validation import (
    MIN_PORTFOLIO_VALUE,
    MAX_PORTFOLIO_VALUE,
    MIN_VALID_PRICE,
    MAX_DAILY_PRICE_CHANGE_PERCENT,
)

def validate_portfolio_value(value: float) -> bool:
    """Validate portfolio value is within reasonable bounds"""
    return MIN_PORTFOLIO_VALUE <= value <= MAX_PORTFOLIO_VALUE

def validate_price(price: float) -> bool:
    """Validate security price is reasonable"""
    return MIN_VALID_PRICE <= price <= MAX_VALID_PRICE
```

---

### 7. Time Periods Constants (`time_periods.py`)

```python
"""
Reusable Time Period Definitions

Domain: Cross-cutting time calculations
Used by: All services requiring time conversions
"""

# =============================================================================
# TIME UNIT CONVERSIONS
# =============================================================================

# Seconds
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800
SECONDS_PER_MONTH_AVG = 2592000  # 30 days
SECONDS_PER_YEAR = 31536000  # 365 days

# Minutes
MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 1440
MINUTES_PER_WEEK = 10080

# Hours
HOURS_PER_DAY = 24
HOURS_PER_WEEK = 168

# Days
DAYS_PER_WEEK = 7
DAYS_PER_MONTH_AVG = 30
DAYS_PER_YEAR = 365
DAYS_PER_LEAP_YEAR = 366

# Weeks
WEEKS_PER_YEAR = 52
WEEKS_PER_MONTH_AVG = 4.33

# Months
MONTHS_PER_YEAR = 12
MONTHS_PER_QUARTER = 3

# =============================================================================
# COMMON TIME PERIODS (in days)
# =============================================================================

# Short-term periods
PERIOD_1_DAY = 1
PERIOD_1_WEEK = 7
PERIOD_2_WEEKS = 14
PERIOD_1_MONTH = 30
PERIOD_3_MONTHS = 90
PERIOD_6_MONTHS = 180

# Long-term periods
PERIOD_1_YEAR = 365
PERIOD_2_YEARS = 730
PERIOD_3_YEARS = 1095
PERIOD_5_YEARS = 1825
PERIOD_10_YEARS = 3650

# =============================================================================
# TRADING CALENDAR SPECIFIC
# =============================================================================

# Trading days per period
TRADING_DAYS_PER_WEEK = 5
TRADING_DAYS_PER_MONTH = 21   # ~21 trading days per month
TRADING_DAYS_PER_QUARTER = 63  # ~63 trading days per quarter
TRADING_DAYS_PER_YEAR = 252    # Standard Wall Street assumption

# Non-trading days per year
WEEKEND_DAYS_PER_YEAR = 104    # ~52 weeks * 2 days
HOLIDAY_DAYS_PER_YEAR = 9      # NYSE holidays (approximate)
```

---

## Implementation Strategy

### Phase 1: Infrastructure (Week 1)

**Tasks**:
1. ✅ Create `backend/app/core/constants/` directory
2. ✅ Create `__init__.py` with public API
3. ✅ Create all 7 domain-specific modules
4. ✅ Add docstrings with domain context and sources
5. ✅ Run syntax validation (`python -m py_compile`)

**Time**: 4 hours

### Phase 2: High-Value Migration (Week 1-2)

**Priority Order** (based on domain impact):

1. **Financial Domain** (8-10 hours)
   - `services/metrics.py` - Most magic numbers (252, 365, 0.95, etc.)
   - `services/pricing.py` - Pricing calculations
   - `db/metrics_queries.py` - SQL queries with hardcoded periods

2. **Risk Domain** (4-6 hours)
   - `services/risk_metrics.py` - VaR/CVaR calculations
   - `services/currency_attribution.py` - Attribution logic
   - `services/factor_analysis.py` - Factor loadings

3. **Integration Domain** (3-4 hours)
   - `integrations/rate_limiter.py` - Rate limits
   - `integrations/fred_provider.py` - FRED API
   - `integrations/fmp_provider.py` - FMP API
   - `integrations/polygon_provider.py` - Polygon API

**Time**: 15-20 hours total

### Phase 3: Complete Migration (Week 3)

4. **Macro Domain** (2-3 hours)
   - `services/cycles.py` - Regime detection
   - `services/macro.py` - Indicator weighting

5. **Scenarios Domain** (2-3 hours)
   - `services/scenarios.py` - Monte Carlo
   - `services/optimizer.py` - Portfolio optimization

6. **Validation Everywhere** (4-6 hours)
   - Add validation using constants from `validation.py`
   - Replace hardcoded bounds with named constants

**Time**: 8-12 hours

**Total Implementation Time**: 27-36 hours over 3 weeks

---

## Integration with Broader Refactoring

### Synergy with Phase 1 (Exception Handling)

**Constants enable better validation**:
```python
# Before
try:
    if volatility > 5.0:  # Magic number
        raise ValueError("Volatility too high")
except ValueError as e:
    logger.error(f"Programming error: {e}")
    raise

# After
from app.core.constants.validation import MAX_VALID_VOLATILITY

try:
    if volatility > MAX_VALID_VOLATILITY:
        raise ValueError(f"Volatility {volatility} exceeds max {MAX_VALID_VOLATILITY}")
except ValueError as e:
    logger.error(f"Programming error: {e}")
    raise
```

### Synergy with Phase 2 (Dependency Injection)

**Constants as configuration**:
```python
# In service initializer (Phase 2)
container.register_service(
    "pricing",
    PricingService,
    db_pool="db_pool",
    # Constants injected as config
    trading_days_per_year=TRADING_DAYS_PER_YEAR,
    annualization_days=ANNUALIZATION_DAYS,
)
```

### Synergy with Data Quality (Future)

**Constants define data contracts**:
```python
# In data contract definition
from app.core.constants.validation import (
    MIN_PORTFOLIO_VALUE,
    MAX_PORTFOLIO_VALUE,
    REQUIRED_DATE_FIELD_PORTFOLIO,
)

PORTFOLIO_VALUE_CONTRACT = {
    "min_value": MIN_PORTFOLIO_VALUE,
    "max_value": MAX_PORTFOLIO_VALUE,
    "required_fields": [REQUIRED_DATE_FIELD_PORTFOLIO],
}
```

---

## Testing Strategy

### Unit Tests for Constants

```python
# tests/test_constants.py
def test_trading_days_consistency():
    """Ensure trading day constants are mathematically consistent"""
    from app.core.constants.financial import (
        TRADING_DAYS_PER_YEAR,
        LOOKBACK_1_YEAR,
    )
    assert TRADING_DAYS_PER_YEAR == LOOKBACK_1_YEAR

def test_confidence_levels_sum():
    """Ensure confidence and significance levels are complementary"""
    from app.core.constants.risk import (
        CONFIDENCE_LEVEL_95,
        SIGNIFICANCE_LEVEL_5,
    )
    assert abs((CONFIDENCE_LEVEL_95 + SIGNIFICANCE_LEVEL_5) - 1.0) < 1e-10
```

### Migration Tests (Per Domain)

```python
# tests/test_metrics_migration.py
def test_sharpe_ratio_unchanged():
    """Verify Sharpe ratio matches old calculation after constants migration"""
    # Test data
    returns = np.array([0.01, -0.005, 0.02, ...])

    # Old calculation (magic numbers)
    old_sharpe = returns.mean() * 252 / (returns.std() * np.sqrt(252))

    # New calculation (constants)
    from app.core.constants.financial import TRADING_DAYS_PER_YEAR
    new_sharpe = returns.mean() * TRADING_DAYS_PER_YEAR / (
        returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    )

    # Should be identical (within floating point precision)
    assert abs(old_sharpe - new_sharpe) < 1e-10
```

### Integration Tests

Run full test suite after each domain migration:
```bash
# After migrating financial domain
pytest tests/test_metrics.py -v
pytest tests/test_pricing.py -v

# After migrating risk domain
pytest tests/test_risk_metrics.py -v
pytest tests/test_factor_analysis.py -v
```

---

## Success Criteria

### Quantitative
- ✅ Zero hardcoded magic numbers in migrated files
- ✅ All constants have docstrings with domain context
- ✅ All tests pass after migration
- ✅ Numeric outputs identical to pre-migration (within 1e-10)
- ✅ 100% type hint coverage for constants

### Qualitative
- ✅ Domain experts can understand and modify constants
- ✅ Constants clearly map to business concepts
- ✅ Constants enable data validation
- ✅ Constants support data contract specifications
- ✅ Code reads like domain language

---

## Domain Validation Checklist

Before finalizing constants, verify with domain experts:

**Financial Domain**:
- [ ] Trading days (252) matches actual market calendar
- [ ] Annualization factors align with GIPS standards
- [ ] Performance thresholds reasonable for real portfolios

**Risk Domain**:
- [ ] VaR confidence levels match Basel III requirements
- [ ] Factor loading thresholds align with research
- [ ] Tracking error bounds match fund categories

**Macro Domain**:
- [ ] Regime change thresholds validated by economic research
- [ ] Indicator weights sum to 1.0
- [ ] Cycle duration bounds match historical data

**Scenarios Domain**:
- [ ] Monte Carlo path counts sufficient for accuracy
- [ ] Optimization constraints match real-world limits
- [ ] Stress test severity levels align with industry standards

**Integration Domain**:
- [ ] API rate limits match provider documentation
- [ ] Timeouts reasonable for network conditions
- [ ] Retry policies follow best practices

---

## Coordination with Main IDE Agent

### Work Allocation

**Main Agent (Phase 2 - DI Container)**:
- `combined_server.py`
- `core/di_container.py`
- `core/agent_runtime.py`
- Service initialization code

**Constants Extraction (This Agent)**:
- `services/*.py` (business logic)
- `integrations/*.py` (API clients)
- `db/queries.py` files
- Creating `core/constants/` modules

**Zero Overlap** ✅

### Git Workflow

```bash
# Create feature branch
git checkout -b constants-extraction

# Make changes file-by-file
git add backend/app/core/constants/financial.py
git commit -m "feat: add financial domain constants"

git add backend/app/services/metrics.py
git commit -m "refactor: use financial constants in metrics service"

# Sync with main frequently
git fetch origin main
git rebase origin/main

# Push when ready
git push origin constants-extraction
```

---

## Risk Mitigation

### Risk: Breaking Calculations
**Mitigation**: Test numeric output matches exactly (within 1e-10)
**Recovery**: Revert specific file, investigate discrepancy

### Risk: Merge Conflicts
**Mitigation**: Work on different files than Phase 2, sync frequently
**Recovery**: Resolve conflicts using constants branch changes

### Risk: Using Wrong Constant
**Mitigation**: Clear naming, domain-specific modules, code review
**Recovery**: Fix in subsequent commit, add test to prevent recurrence

### Risk: Missing Domain Knowledge
**Mitigation**: Document sources for each constant, verify with experts
**Recovery**: Update constants based on expert feedback

---

## Next Steps

### Immediate (Today)
1. ✅ Review this plan with user
2. ⏳ Get approval to proceed
3. ⏳ Create `backend/app/core/constants/` structure
4. ⏳ Implement `financial.py` module
5. ⏳ Migrate `services/metrics.py` as pilot

### This Week
6. ⏳ Complete Financial domain migration
7. ⏳ Complete Risk domain migration
8. ⏳ Complete Integration domain migration
9. ⏳ Run full test suite

### Next Week
10. ⏳ Complete remaining domains
11. ⏳ Add validation using constants
12. ⏳ Code review with domain experts
13. ⏳ Merge to main

---

**Status**: 🎯 READY FOR IMPLEMENTATION
**Estimated Duration**: 27-36 hours over 3 weeks
**Risk Level**: LOW (no logic changes)
**Value**: HIGH (domain clarity, validation support)
**Alignment**: Phase 7 of TECHNICAL_DEBT_REMOVAL_PLAN_V3.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
