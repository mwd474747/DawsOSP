"""
Macro Economic Regime Constants

Domain: Economic cycle detection, regime classification, indicator weighting
Sources: Macro economic theory, business cycle research
Identified by: Analysis of cycles.py and macro.py

This module contains constants used for:
- Regime detection thresholds (z-scores)
- Phase indicator weights
- Regime probability normalization
- Lookback periods for macro indicators
"""

# =============================================================================
# REGIME DETECTION LOOKBACK PERIODS
# =============================================================================

# Standard lookback period for macro regime detection
# Uses 252 trading days (1 year) for z-score normalization
DEFAULT_MACRO_LOOKBACK_DAYS = 252

# =============================================================================
# Z-SCORE THRESHOLDS FOR REGIME CLASSIFICATION
# =============================================================================

# Z-score ranges for regime rules
# These define when an indicator is "high", "low", "normal"

# Threshold definitions:
# -2.0 = Very low (bottom 2.5%)
# -1.5 = Low
# -1.0 = Below average
# -0.5 = Slightly below average
#  0.0 = Average
#  0.5 = Slightly above average
#  1.0 = Above average
#  1.5 = High
#  2.0 = Very high (top 2.5%)
#  2.5 = Extreme

ZSCORE_VERY_LOW = -2.0
ZSCORE_LOW = -1.5
ZSCORE_BELOW_AVERAGE = -1.0
ZSCORE_SLIGHTLY_BELOW = -0.5
ZSCORE_AVERAGE = 0.0
ZSCORE_SLIGHTLY_ABOVE = 0.5
ZSCORE_ABOVE_AVERAGE = 1.0
ZSCORE_HIGH = 1.5
ZSCORE_VERY_HIGH = 2.0
ZSCORE_EXTREME = 2.5

# =============================================================================
# PHASE INDICATOR WEIGHTS (Economic Cycle Phases)
# =============================================================================

# Early Recovery phase weights
EARLY_RECOVERY_YIELD_CURVE_WEIGHT = 2.5  # Yield curve steepening (strong signal)
EARLY_RECOVERY_UNEMPLOYMENT_WEIGHT = 1.5  # Unemployment falling
EARLY_RECOVERY_INDPRO_WEIGHT = 1.0  # Industrial production rising
EARLY_RECOVERY_CREDIT_WEIGHT = 0.5  # Credit starting to grow

# Mid Expansion phase weights
MID_EXPANSION_GDP_WEIGHT = 2.0  # Strong GDP growth
MID_EXPANSION_PAYEMS_WEIGHT = 1.5  # Job growth strong
MID_EXPANSION_CREDIT_WEIGHT = 1.0  # Credit accelerating
MID_EXPANSION_YIELD_CURVE_WEIGHT = 1.0  # Yield curve positive

# Late Expansion / Boom phase weights
LATE_EXPANSION_INFLATION_WEIGHT = 2.0  # Inflation rising
LATE_EXPANSION_YIELD_CURVE_WEIGHT = -2.0  # Yield curve flattening/inverting (negative)
LATE_EXPANSION_CREDIT_WEIGHT = 1.5  # Credit growth peaking
LATE_EXPANSION_UNEMPLOYMENT_WEIGHT = -1.0  # Unemployment very low (negative = tight labor)

# Early Recession phase weights
EARLY_RECESSION_YIELD_CURVE_WEIGHT = -2.5  # Yield curve inverted (strong signal)
EARLY_RECESSION_GDP_WEIGHT = -1.5  # GDP growth slowing (negative)
EARLY_RECESSION_INDPRO_WEIGHT = -1.0  # Industrial production falling
EARLY_RECESSION_CREDIT_WEIGHT = -0.5  # Credit contracting

# Deep Recession phase weights
DEEP_RECESSION_UNEMPLOYMENT_WEIGHT = 2.5  # Unemployment rising sharply
DEEP_RECESSION_GDP_WEIGHT = -2.0  # GDP contracting (negative)
DEEP_RECESSION_CREDIT_WEIGHT = -2.0  # Credit contracting sharply
DEEP_RECESSION_PAYEMS_WEIGHT = -1.5  # Job losses

# =============================================================================
# REGIME PROBABILITY NORMALIZATION
# =============================================================================

# Minimum probability value (floor)
MIN_REGIME_PROBABILITY = 0.0

# Maximum probability value (ceiling)
MAX_REGIME_PROBABILITY = 1.0

# Default probability when no indicators match
DEFAULT_REGIME_PROBABILITY = 0.0

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Lookback periods
    "DEFAULT_MACRO_LOOKBACK_DAYS",
    # Z-score thresholds
    "ZSCORE_VERY_LOW",
    "ZSCORE_LOW",
    "ZSCORE_BELOW_AVERAGE",
    "ZSCORE_SLIGHTLY_BELOW",
    "ZSCORE_AVERAGE",
    "ZSCORE_SLIGHTLY_ABOVE",
    "ZSCORE_ABOVE_AVERAGE",
    "ZSCORE_HIGH",
    "ZSCORE_VERY_HIGH",
    "ZSCORE_EXTREME",
    # Early Recovery weights
    "EARLY_RECOVERY_YIELD_CURVE_WEIGHT",
    "EARLY_RECOVERY_UNEMPLOYMENT_WEIGHT",
    "EARLY_RECOVERY_INDPRO_WEIGHT",
    "EARLY_RECOVERY_CREDIT_WEIGHT",
    # Mid Expansion weights
    "MID_EXPANSION_GDP_WEIGHT",
    "MID_EXPANSION_PAYEMS_WEIGHT",
    "MID_EXPANSION_CREDIT_WEIGHT",
    "MID_EXPANSION_YIELD_CURVE_WEIGHT",
    # Late Expansion weights
    "LATE_EXPANSION_INFLATION_WEIGHT",
    "LATE_EXPANSION_YIELD_CURVE_WEIGHT",
    "LATE_EXPANSION_CREDIT_WEIGHT",
    "LATE_EXPANSION_UNEMPLOYMENT_WEIGHT",
    # Early Recession weights
    "EARLY_RECESSION_YIELD_CURVE_WEIGHT",
    "EARLY_RECESSION_GDP_WEIGHT",
    "EARLY_RECESSION_INDPRO_WEIGHT",
    "EARLY_RECESSION_CREDIT_WEIGHT",
    # Deep Recession weights
    "DEEP_RECESSION_UNEMPLOYMENT_WEIGHT",
    "DEEP_RECESSION_GDP_WEIGHT",
    "DEEP_RECESSION_CREDIT_WEIGHT",
    "DEEP_RECESSION_PAYEMS_WEIGHT",
    # Probability normalization
    "MIN_REGIME_PROBABILITY",
    "MAX_REGIME_PROBABILITY",
    "DEFAULT_REGIME_PROBABILITY",
]
