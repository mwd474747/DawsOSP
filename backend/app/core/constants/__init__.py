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
- time_periods.py: Reusable time period conversions
- network.py: Port numbers, connection configuration
- http_status.py: HTTP status codes with descriptions
- versions.py: Version numbers, dependency compatibility

Note: validation.py was deleted in Phase 4.1 (2025-11-07) - all constants were unused (0% utilization)

Usage:
    from app.core.constants.financial import TRADING_DAYS_PER_YEAR
    from app.core.constants.risk import CONFIDENCE_LEVEL_95
    from app.core.constants.http_status import HTTP_400_BAD_REQUEST

Alignment: Phase 7 of TECHNICAL_DEBT_REMOVAL_PLAN_V3.md
"""

# Re-export commonly used constants for convenience
from app.core.constants.financial import (
    TRADING_DAYS_PER_YEAR,
    MONTHS_PER_YEAR,
)

from app.core.constants.risk import (
    CONFIDENCE_LEVEL_95,
)

from app.core.constants.time_periods import (
    SECONDS_PER_DAY,
    DAYS_PER_YEAR,
)

# NEW: Macro data helpers (dynamic data from database)
# These replace hardcoded constants with live data from FRED
# See: CONSTANTS_REFACTOR_PLAN_CONSERVATIVE.md
from app.services.macro_data_helpers import (
    get_risk_free_rate,  # Replaces DEFAULT_RISK_FREE_RATE (0.02 hardcoded)
    get_latest_indicator_value,
    get_indicator_percentile,
)

__all__ = [
    # Financial
    "TRADING_DAYS_PER_YEAR",
    "MONTHS_PER_YEAR",
    # Risk
    "CONFIDENCE_LEVEL_95",
    # Time periods
    "SECONDS_PER_DAY",
    "DAYS_PER_YEAR",
    # Macro data helpers (NEW - dynamic data)
    "get_risk_free_rate",
    "get_latest_indicator_value",
    "get_indicator_percentile",
]
