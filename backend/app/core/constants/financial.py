"""
Portfolio Valuation & Performance Measurement Constants

Domain: Portfolio management, trading calendar
Sources: Industry standards (NYSE trading calendar, GIPS)
Identified by: Replit analysis + Constants audit 2025-11-07

This module contains financial domain-specific constants used for:
- Trading calendar calculations (252 trading days per year)
- Period conversions

Cleanup History:
- 2025-11-07: Removed 22 unused constants (88% waste)
  - Removed: CALENDAR_DAYS_PER_YEAR, BUSINESS_DAYS_PER_WEEK (unused)
  - Removed: All LOOKBACK_* periods (unused)
  - Removed: VOLATILITY_WINDOWS_DEFAULT (unused)
  - Removed: ANNUALIZATION_DAYS (unused)
  - Removed: All MIN_RETURNS_* thresholds (unused)
  - Removed: All performance validation thresholds (unused)
  - Removed: All pricing thresholds (unused)
  - Note: MONTHS_PER_YEAR, WEEKS_PER_YEAR are duplicates from time_periods.py
    but kept here for domain-specific financial context
"""

# =============================================================================
# TRADING CALENDAR CONSTANTS
# =============================================================================

# Industry Standard: 252 trading days per year (NYSE/NASDAQ calendar)
# Source: Excludes weekends + major holidays (~104 weekend days + 9 holidays)
# Used in: Volatility annualization, Sharpe ratio, return calculations
TRADING_DAYS_PER_YEAR = 252

# Period conversions (financial domain context)
# Note: Also defined in time_periods.py as canonical source
MONTHS_PER_YEAR = 12
WEEKS_PER_YEAR = 52

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
    "MONTHS_PER_YEAR",
    "WEEKS_PER_YEAR",
]
