"""
Reusable Time Period Definitions

Domain: Cross-cutting time calculations
Used by: All services requiring time conversions
Identified by: Replit analysis (10+ instances)

This module provides standard time unit conversions used across the application.
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

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Seconds
    "SECONDS_PER_MINUTE",
    "SECONDS_PER_HOUR",
    "SECONDS_PER_DAY",
    "SECONDS_PER_WEEK",
    "SECONDS_PER_MONTH_AVG",
    "SECONDS_PER_YEAR",
    # Minutes
    "MINUTES_PER_HOUR",
    "MINUTES_PER_DAY",
    "MINUTES_PER_WEEK",
    # Hours
    "HOURS_PER_DAY",
    "HOURS_PER_WEEK",
    # Days
    "DAYS_PER_WEEK",
    "DAYS_PER_MONTH_AVG",
    "DAYS_PER_YEAR",
    "DAYS_PER_LEAP_YEAR",
    # Weeks
    "WEEKS_PER_YEAR",
    "WEEKS_PER_MONTH_AVG",
    # Months
    "MONTHS_PER_YEAR",
    "MONTHS_PER_QUARTER",
    # Common periods
    "PERIOD_1_DAY",
    "PERIOD_1_WEEK",
    "PERIOD_2_WEEKS",
    "PERIOD_1_MONTH",
    "PERIOD_3_MONTHS",
    "PERIOD_6_MONTHS",
    "PERIOD_1_YEAR",
    "PERIOD_2_YEARS",
    "PERIOD_3_YEARS",
    "PERIOD_5_YEARS",
    "PERIOD_10_YEARS",
    # Trading calendar
    "TRADING_DAYS_PER_WEEK",
    "TRADING_DAYS_PER_MONTH",
    "TRADING_DAYS_PER_QUARTER",
    "TRADING_DAYS_PER_YEAR",
    "WEEKEND_DAYS_PER_YEAR",
    "HOLIDAY_DAYS_PER_YEAR",
]
