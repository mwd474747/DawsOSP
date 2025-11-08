"""
Scenario Analysis & Portfolio Optimization Constants

Domain: Monte Carlo simulation, stress testing, portfolio optimization
Sources: Risk management best practices, optimization theory
Identified by: Analysis of scenarios.py and optimizer.py

This module contains constants used for:
- Scenario shock magnitudes (basis points, percentages)
- Scenario probabilities and severity levels
- Portfolio optimization constraints
- Position sizing limits
- Sector concentration limits
"""

# =============================================================================
# SCENARIO SHOCK MAGNITUDES
# =============================================================================

# Default shock values (no shock)
DEFAULT_SHOCK_BPS = 0.0  # Basis points
DEFAULT_SHOCK_PCT = 0.0  # Percentage

# Probability ranges
MIN_SCENARIO_PROBABILITY = 0.0
MAX_SCENARIO_PROBABILITY = 1.0

# =============================================================================
# DELEVERAGING SCENARIOS (Money Printing)
# =============================================================================

# Money Printing Deleveraging (Inflationary)
MONEY_PRINTING_REAL_RATES_BPS = 25.0  # Real rates rise 25bp
MONEY_PRINTING_INFLATION_BPS = 150.0  # Inflation rises 150bp (1.5%)
MONEY_PRINTING_CREDIT_SPREAD_BPS = -50.0  # Credit spreads tighten 50bp
MONEY_PRINTING_USD_PCT = -0.12  # USD depreciates 12%
MONEY_PRINTING_EQUITY_PCT = 0.05  # Equities rise 5%
MONEY_PRINTING_PROBABILITY = 0.25  # 25% probability

# Austerity Deleveraging (Deflationary)
AUSTERITY_REAL_RATES_BPS = -75.0  # Real rates fall 75bp
AUSTERITY_INFLATION_BPS = -50.0  # Deflation 50bp
AUSTERITY_CREDIT_SPREAD_BPS = 100.0  # Credit spreads widen 100bp
AUSTERITY_USD_PCT = 0.08  # USD appreciates 8%
AUSTERITY_EQUITY_PCT = -0.20  # Equities fall 20%
AUSTERITY_PROBABILITY = 0.15  # 15% probability

# Default/Restructuring Deleveraging (Deep Deflation)
DEFAULT_REAL_RATES_BPS = -150.0  # Real rates fall 150bp
DEFAULT_INFLATION_BPS = -100.0  # Deflation 100bp
DEFAULT_CREDIT_SPREAD_BPS = 300.0  # Credit spreads widen 300bp
DEFAULT_USD_PCT = 0.15  # USD appreciates 15%
DEFAULT_EQUITY_PCT = -0.40  # Equities fall 40%
DEFAULT_PROBABILITY = 0.05  # 5% probability

# =============================================================================
# RATE SHOCK SCENARIOS
# =============================================================================

# Rates Up scenario
RATES_UP_100BP = 100.0  # 10Y Treasury yield rises 100bp

# =============================================================================
# PORTFOLIO OPTIMIZATION CONSTRAINTS
# =============================================================================

# Quality filters
MIN_QUALITY_SCORE = 0.0  # Minimum aggregate quality rating (0-10 scale)
MAX_QUALITY_SCORE = 10.0  # Maximum quality rating

# Position limits (percentages)
DEFAULT_MAX_SINGLE_POSITION_PCT = 20.0  # Maximum 20% in any single position
DEFAULT_MIN_POSITION_PCT = 0.5  # Minimum 0.5% to avoid dust positions

# Sector concentration limits (percentages)
DEFAULT_MAX_SECTOR_PCT = 30.0  # Maximum 30% in any single sector

# Tracking error limits (percentages)
DEFAULT_MAX_TRACKING_ERROR_PCT = 5.0  # Maximum 5% tracking error vs benchmark

# Turnover constraints (percentages)
DEFAULT_MAX_TURNOVER_PCT = 100.0  # Maximum 100% turnover

# Risk-free rate
DEFAULT_OPTIMIZATION_RISK_FREE_RATE = 0.02  # 2% annual risk-free rate

# Historical lookback for covariance estimation
DEFAULT_OPTIMIZATION_LOOKBACK_DAYS = 252  # 1 year of trading days

# =============================================================================
# SEVERITY LEVELS
# =============================================================================

SEVERITY_LOW = "low"
SEVERITY_MODERATE = "moderate"
SEVERITY_HIGH = "high"
SEVERITY_EXTREME = "extreme"

# =============================================================================
# OPTIMIZATION METHODS
# =============================================================================

METHOD_MEAN_VARIANCE = "mean_variance"
METHOD_RISK_PARITY = "risk_parity"
METHOD_MAX_SHARPE = "max_sharpe"
METHOD_CVAR = "cvar"

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Default shocks
    "DEFAULT_SHOCK_BPS",
    "DEFAULT_SHOCK_PCT",
    # Probability ranges
    "MIN_SCENARIO_PROBABILITY",
    "MAX_SCENARIO_PROBABILITY",
    # Money Printing Deleveraging
    "MONEY_PRINTING_REAL_RATES_BPS",
    "MONEY_PRINTING_INFLATION_BPS",
    "MONEY_PRINTING_CREDIT_SPREAD_BPS",
    "MONEY_PRINTING_USD_PCT",
    "MONEY_PRINTING_EQUITY_PCT",
    "MONEY_PRINTING_PROBABILITY",
    # Austerity Deleveraging
    "AUSTERITY_REAL_RATES_BPS",
    "AUSTERITY_INFLATION_BPS",
    "AUSTERITY_CREDIT_SPREAD_BPS",
    "AUSTERITY_USD_PCT",
    "AUSTERITY_EQUITY_PCT",
    "AUSTERITY_PROBABILITY",
    # Default/Restructuring Deleveraging
    "DEFAULT_REAL_RATES_BPS",
    "DEFAULT_INFLATION_BPS",
    "DEFAULT_CREDIT_SPREAD_BPS",
    "DEFAULT_USD_PCT",
    "DEFAULT_EQUITY_PCT",
    "DEFAULT_PROBABILITY",
    # Rate shocks
    "RATES_UP_100BP",
    # Optimization constraints
    "MIN_QUALITY_SCORE",
    "MAX_QUALITY_SCORE",
    "DEFAULT_MAX_SINGLE_POSITION_PCT",
    "DEFAULT_MIN_POSITION_PCT",
    "DEFAULT_MAX_SECTOR_PCT",
    "DEFAULT_MAX_TRACKING_ERROR_PCT",
    "DEFAULT_MAX_TURNOVER_PCT",
    "DEFAULT_OPTIMIZATION_RISK_FREE_RATE",
    "DEFAULT_OPTIMIZATION_LOOKBACK_DAYS",
    # Severity levels
    "SEVERITY_LOW",
    "SEVERITY_MODERATE",
    "SEVERITY_HIGH",
    "SEVERITY_EXTREME",
    # Optimization methods
    "METHOD_MEAN_VARIANCE",
    "METHOD_RISK_PARITY",
    "METHOD_MAX_SHARPE",
    "METHOD_CVAR",
]
