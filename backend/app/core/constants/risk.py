"""
Risk Metrics & Factor Analysis Constants

Domain: VaR, CVaR, factor exposures, risk decomposition, tracking error
Sources: Basel III, industry best practices
Identified by: Replit analysis (35+ instances)

This module contains constants used for:
- Value at Risk (VaR) and Conditional VaR calculations
- Factor analysis and exposure limits
- Statistical thresholds for outlier detection
- Tracking error and downside risk metrics
"""

# =============================================================================
# VAR/CVAR CONSTANTS
# =============================================================================

# Confidence levels (industry standard)
# 95% = 1 in 20 days expected to exceed VaR (common for internal risk management)
# 99% = 1 in 100 days expected to exceed VaR (regulatory requirement, Basel)
CONFIDENCE_LEVEL_95 = 0.95
CONFIDENCE_LEVEL_99 = 0.99

# Significance levels (inverse of confidence)
# Used for percentile calculations: np.percentile(returns, SIGNIFICANCE_LEVEL_5 * 100)
SIGNIFICANCE_LEVEL_5 = 0.05   # 5th percentile for VaR_95
SIGNIFICANCE_LEVEL_1 = 0.01   # 1st percentile for VaR_99

# Default confidence levels
DEFAULT_VAR_CONFIDENCE = 0.95
DEFAULT_CVAR_CONFIDENCE = 0.95

# Lookback period for VaR calculation
# Industry standard: 252 trading days (1 year of historical data)
VAR_LOOKBACK_DAYS = 252

# =============================================================================
# STATISTICAL THRESHOLDS
# =============================================================================

# Standard deviation multiples (for outlier detection)
# 1σ = 68% confidence interval
# 2σ = 95% confidence interval
# 3σ = 99.7% confidence interval
STANDARD_DEVIATIONS_1 = 1.0
STANDARD_DEVIATIONS_2 = 2.0
STANDARD_DEVIATIONS_3 = 3.0

# Z-score thresholds for anomaly detection
# Used in regime detection, outlier identification
Z_SCORE_THRESHOLD_MODERATE = 2.0   # ~95% confidence
Z_SCORE_THRESHOLD_SEVERE = 3.0     # ~99.7% confidence

# =============================================================================
# FACTOR ANALYSIS CONSTANTS
# =============================================================================

# Minimum factor loading to be considered significant
# Below this, factor exposure is negligible (common industry practice: 5%)
MIN_SIGNIFICANT_FACTOR_LOADING = 0.05  # 5%

# Maximum factor concentration
# Prevents over-exposure to single factor (diversification requirement)
MAX_FACTOR_CONCENTRATION = 0.50  # 50%

# R-squared threshold for model quality
# Below this, factor model is unreliable (minimum explanatory power)
MIN_FACTOR_MODEL_R_SQUARED = 0.30  # 30%

# =============================================================================
# TRACKING ERROR CONSTANTS
# =============================================================================

# Tracking error calculation period (default 1 year)
DEFAULT_TRACKING_ERROR_PERIODS = 252

# Tracking error thresholds (for validation and fund classification)
# Source: Industry norms for different fund types
TRACKING_ERROR_PASSIVE_MAX = 0.02    # Passive fund: <2%
TRACKING_ERROR_ACTIVE_MIN = 0.02     # Active fund: 2-6%
TRACKING_ERROR_ACTIVE_MAX = 0.06
TRACKING_ERROR_AGGRESSIVE_MIN = 0.06 # Aggressive: >6%

# =============================================================================
# DOWNSIDE RISK CONSTANTS
# =============================================================================

# Minimum Acceptable Return (MAR) for downside deviation
# Default: 0% (any negative return is "downside")
# Can be set to risk-free rate or other benchmark
DEFAULT_MAR = 0.0

# Sortino ratio calculation (uses downside deviation instead of total volatility)
# Same lookback as Sharpe for consistency
SORTINO_LOOKBACK_DAYS = 252

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
    "CONFIDENCE_LEVEL_99",
    "SIGNIFICANCE_LEVEL_5",
    "SIGNIFICANCE_LEVEL_1",
    "DEFAULT_VAR_CONFIDENCE",
    "DEFAULT_CVAR_CONFIDENCE",
    "VAR_LOOKBACK_DAYS",
    # Statistical thresholds
    "STANDARD_DEVIATIONS_1",
    "STANDARD_DEVIATIONS_2",
    "STANDARD_DEVIATIONS_3",
    "Z_SCORE_THRESHOLD_MODERATE",
    "Z_SCORE_THRESHOLD_SEVERE",
    # Factor analysis
    "MIN_SIGNIFICANT_FACTOR_LOADING",
    "MAX_FACTOR_CONCENTRATION",
    "MIN_FACTOR_MODEL_R_SQUARED",
    # Tracking error
    "DEFAULT_TRACKING_ERROR_PERIODS",
    "TRACKING_ERROR_PASSIVE_MAX",
    "TRACKING_ERROR_ACTIVE_MIN",
    "TRACKING_ERROR_ACTIVE_MAX",
    "TRACKING_ERROR_AGGRESSIVE_MIN",
    # Downside risk
    "DEFAULT_MAR",
    "SORTINO_LOOKBACK_DAYS",
    # Note: DEFAULT_RISK_FREE_RATE removed - use get_risk_free_rate() from app.core.constants
]
