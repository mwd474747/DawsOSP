"""
Portfolio Valuation & Performance Measurement Constants

Domain: Portfolio management, performance attribution, financial calculations
Sources: Industry standards (GIPS, CFA Institute, NYSE trading calendar)
Identified by: Replit analysis (40+ instances)

This module contains constants used for:
- Trading calendar calculations (252 trading days per year)
- Return annualization (TWR, MWR, Sharpe ratio)
- Performance measurement lookback periods
- Volatility calculations
- Price validation thresholds
"""

# =============================================================================
# TRADING CALENDAR CONSTANTS
# =============================================================================

# Industry Standard: 252 trading days per year (NYSE/NASDAQ calendar)
# Source: Excludes weekends + major holidays (~104 weekend days + 9 holidays)
# Used in: Volatility annualization, Sharpe ratio, return calculations
TRADING_DAYS_PER_YEAR = 252

# Calendar days for annualization
# Used in: TWR/MWR calculations (IRR uses 365-day year)
CALENDAR_DAYS_PER_YEAR = 365

# Period conversions
MONTHS_PER_YEAR = 12
WEEKS_PER_YEAR = 52
BUSINESS_DAYS_PER_WEEK = 5

# Common lookback periods (in trading days)
# Used for: Performance metrics, volatility windows, correlation analysis
LOOKBACK_1_MONTH = 21      # ~1 month of trading
LOOKBACK_3_MONTHS = 63     # ~3 months of trading
LOOKBACK_6_MONTHS = 126    # ~6 months of trading
LOOKBACK_1_YEAR = 252      # 1 year of trading
LOOKBACK_3_YEARS = 756     # 3 years of trading
LOOKBACK_5_YEARS = 1260    # 5 years of trading

# Volatility windows (used in metrics.py:460, 515)
# Common industry practice: short, medium, long-term volatility
VOLATILITY_WINDOWS_DEFAULT = [30, 90, 252]  # 1 month, 3 months, 1 year

# =============================================================================
# RETURN CALCULATION CONSTANTS
# =============================================================================

# Annualization factors
# TWR: (1 + return)^(365/days) - 1
# MWR: Uses IRR with 365-day year (metrics.py:299)
ANNUALIZATION_DAYS = 365

# Minimum data points for reliable statistics
# Industry best practices for statistical significance
MIN_RETURNS_FOR_VOLATILITY = 2   # Need at least 2 returns for std dev
MIN_RETURNS_FOR_SHARPE = 30      # Industry best practice (1 month)
MIN_RETURNS_FOR_BETA = 252       # Need 1 year for reliable beta

# =============================================================================
# PERFORMANCE THRESHOLDS (for validation)
# =============================================================================

# Sharpe Ratio bounds
# Typical range: -3 to +10 (outside this suggests data error)
# Source: Historical market data (e.g., S&P 500 Sharpe ~0.5-1.0 long-term)
MIN_VALID_SHARPE_RATIO = -3.0
MAX_VALID_SHARPE_RATIO = 10.0

# Information Ratio bounds
# Typical range: -5 to +5 for active managers
MIN_VALID_INFORMATION_RATIO = -5.0
MAX_VALID_INFORMATION_RATIO = 5.0

# Volatility bounds (annualized)
# Used to detect data quality issues
MIN_VALID_VOLATILITY = 0.001   # 0.1% (too low suggests data issue)
MAX_VALID_VOLATILITY = 5.0     # 500% (too high suggests data issue)

# =============================================================================
# PRICING PACK CONFIGURATION
# =============================================================================

# Pricing pack freshness threshold (in days)
# After this many days without update, pack is considered stale
PRICING_PACK_STALE_DAYS = 7

# Maximum allowed price change in single day (for validation)
# 50% = likely stock halted, circuit breaker triggered, or data error
MAX_DAILY_PRICE_CHANGE_PERCENT = 0.50

# Minimum price value (for validation)
# Below this suggests penny stock or data error
MIN_VALID_PRICE = 0.01  # Penny stocks threshold

# =============================================================================
# RISK-FREE RATE - REMOVED (Use Dynamic Data)
# =============================================================================

# REMOVED in v1.1.0 - Use get_risk_free_rate() from app.core.constants instead
#
# The hardcoded DEFAULT_SHARPE_RISK_FREE_RATE constant has been removed.
# Use the dynamic helper function to fetch live 10-Year Treasury rates from FRED.
#
# Migration:
#   from app.core.constants import get_risk_free_rate
#   rf_rate = await get_risk_free_rate()  # Live from FRED (e.g., 0.045)
#
# See: CONSTANTS_REFACTOR_PHASES1-2_SUMMARY.md

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Trading calendar
    "TRADING_DAYS_PER_YEAR",
    "CALENDAR_DAYS_PER_YEAR",
    "MONTHS_PER_YEAR",
    "WEEKS_PER_YEAR",
    "BUSINESS_DAYS_PER_WEEK",
    # Lookback periods
    "LOOKBACK_1_MONTH",
    "LOOKBACK_3_MONTHS",
    "LOOKBACK_6_MONTHS",
    "LOOKBACK_1_YEAR",
    "LOOKBACK_3_YEARS",
    "LOOKBACK_5_YEARS",
    "VOLATILITY_WINDOWS_DEFAULT",
    # Return calculations
    "ANNUALIZATION_DAYS",
    "MIN_RETURNS_FOR_VOLATILITY",
    "MIN_RETURNS_FOR_SHARPE",
    "MIN_RETURNS_FOR_BETA",
    # Performance thresholds
    "MIN_VALID_SHARPE_RATIO",
    "MAX_VALID_SHARPE_RATIO",
    "MIN_VALID_INFORMATION_RATIO",
    "MAX_VALID_INFORMATION_RATIO",
    "MIN_VALID_VOLATILITY",
    "MAX_VALID_VOLATILITY",
    # Pricing
    "PRICING_PACK_STALE_DAYS",
    "MAX_DAILY_PRICE_CHANGE_PERCENT",
    "MIN_VALID_PRICE",
    # Note: DEFAULT_SHARPE_RISK_FREE_RATE removed - use get_risk_free_rate() from app.core.constants
]
