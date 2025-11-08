"""
DawsOS Application Constants

This package contains domain-driven constants organized by business domain.
Replaces magic numbers throughout the codebase with named, documented constants.

Architecture:
- financial.py: Portfolio valuation, trading calendar, performance metrics
- risk.py: VaR/CVaR, factor analysis, statistical thresholds
- macro.py: Macro regime detection, economic indicators
- scenarios.py: Monte Carlo simulation, portfolio optimization
- integration.py: External API configuration (timeouts, rate limits, retries)
- validation.py: Data quality thresholds, bounds checking
- time_periods.py: Reusable time period conversions
- network.py: Port numbers, connection configuration
- http_status.py: HTTP status codes with descriptions
- versions.py: Version numbers, dependency compatibility

Usage:
    from app.core.constants.financial import TRADING_DAYS_PER_YEAR
    from app.core.constants.risk import CONFIDENCE_LEVEL_95
    from app.core.constants.http_status import HTTP_400_BAD_REQUEST

Alignment: Phase 7 of TECHNICAL_DEBT_REMOVAL_PLAN_V3.md
"""

# Re-export commonly used constants for convenience
from app.core.constants.financial import (
    TRADING_DAYS_PER_YEAR,
    CALENDAR_DAYS_PER_YEAR,
    MONTHS_PER_YEAR,
    ANNUALIZATION_DAYS,
)

from app.core.constants.risk import (
    CONFIDENCE_LEVEL_95,
    CONFIDENCE_LEVEL_99,
    SIGNIFICANCE_LEVEL_5,
    DEFAULT_VAR_CONFIDENCE,
)

from app.core.constants.time_periods import (
    SECONDS_PER_DAY,
    DAYS_PER_YEAR,
)

__all__ = [
    # Financial
    "TRADING_DAYS_PER_YEAR",
    "CALENDAR_DAYS_PER_YEAR",
    "MONTHS_PER_YEAR",
    "ANNUALIZATION_DAYS",
    # Risk
    "CONFIDENCE_LEVEL_95",
    "CONFIDENCE_LEVEL_99",
    "SIGNIFICANCE_LEVEL_5",
    "DEFAULT_VAR_CONFIDENCE",
    # Time periods
    "SECONDS_PER_DAY",
    "DAYS_PER_YEAR",
]
