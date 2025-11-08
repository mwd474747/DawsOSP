"""
Risk Metrics & Factor Analysis Constants

Domain: VaR calculations, tracking error
Sources: Basel III, industry best practices
Identified by: Replit analysis + Constants audit 2025-11-07

This module contains risk management constants used for:
- Value at Risk (VaR) confidence levels
- Tracking error calculations

Cleanup History:
- 2025-11-07: Removed 19 unused constants (86.4% waste)
  - Removed: CONFIDENCE_LEVEL_99, SIGNIFICANCE_LEVEL_5, SIGNIFICANCE_LEVEL_1 (unused)
  - Removed: DEFAULT_VAR_CONFIDENCE, DEFAULT_CVAR_CONFIDENCE (unused)
  - Removed: All STANDARD_DEVIATIONS_* constants (unused)
  - Removed: All Z_SCORE_THRESHOLD_* constants (unused)
  - Removed: All factor analysis constants (unused planned features)
  - Removed: All tracking error thresholds (unused)
  - Removed: All downside risk constants (DEFAULT_MAR, SORTINO_LOOKBACK_DAYS) (unused)
  - Kept: CONFIDENCE_LEVEL_95, VAR_LOOKBACK_DAYS, DEFAULT_TRACKING_ERROR_PERIODS (in use)
"""

# =============================================================================
# VAR/CVAR CONSTANTS
# =============================================================================

# Confidence levels (industry standard)
# 95% = 1 in 20 days expected to exceed VaR (common for internal risk management)
CONFIDENCE_LEVEL_95 = 0.95

# Lookback period for VaR calculation
# Industry standard: 252 trading days (1 year of historical data)
VAR_LOOKBACK_DAYS = 252

# =============================================================================
# TRACKING ERROR CONSTANTS
# =============================================================================

# Tracking error calculation period (default 1 year)
DEFAULT_TRACKING_ERROR_PERIODS = 252

# =============================================================================
# RISK-FREE RATE - REMOVED (Use Dynamic Data)
# =============================================================================

# REMOVED in v1.1.0 - Use get_risk_free_rate() from app.core.constants instead
#
# The hardcoded DEFAULT_RISK_FREE_RATE constant has been removed.
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
    # VaR/CVaR
    "CONFIDENCE_LEVEL_95",
    "VAR_LOOKBACK_DAYS",
    # Tracking error
    "DEFAULT_TRACKING_ERROR_PERIODS",
]
