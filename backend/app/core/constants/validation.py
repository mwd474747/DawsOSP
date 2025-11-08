"""
Data Validation & Alert Threshold Constants

Domain: Alert conditions, data quality, threshold monitoring
Sources: Risk management practices, financial industry standards
Identified by: Analysis of alerts.py and alert_validators.py

This module contains constants used for:
- Alert threshold values
- Cooldown periods
- Data quality bounds
- Metric thresholds for anomaly detection
"""

# =============================================================================
# ALERT COOLDOWN PERIODS (hours)
# =============================================================================

# Default cooldown to prevent alert spam
DEFAULT_ALERT_COOLDOWN_HOURS = 24  # 24 hours (1 day)

# Alert lookback for duplicate detection
DEFAULT_ALERT_LOOKBACK_HOURS = 24  # Check last 24 hours for duplicates

# Extended cooldown periods
ALERT_COOLDOWN_EXTENDED = 48  # 2 days
ALERT_COOLDOWN_WEEKLY = 168  # 7 days

# =============================================================================
# MACRO ALERT THRESHOLDS
# =============================================================================

# VIX (Volatility Index) thresholds
VIX_ELEVATED_THRESHOLD = 20.0  # Market anxiety
VIX_HIGH_THRESHOLD = 30.0  # High volatility / fear
VIX_EXTREME_THRESHOLD = 40.0  # Extreme fear / panic

# Unemployment rate thresholds (percent)
UNEMPLOYMENT_LOW_THRESHOLD = 4.0  # Very low unemployment (tight labor market)
UNEMPLOYMENT_NORMAL_THRESHOLD = 5.0  # Normal unemployment
UNEMPLOYMENT_HIGH_THRESHOLD = 7.0  # Elevated unemployment

# =============================================================================
# PORTFOLIO METRIC THRESHOLDS
# =============================================================================

# Maximum drawdown thresholds (decimal)
MAX_DRAWDOWN_WARNING = 0.10  # 10% drawdown (yellow flag)
MAX_DRAWDOWN_ALERT = 0.15  # 15% drawdown (red flag)
MAX_DRAWDOWN_CRITICAL = 0.20  # 20% drawdown (critical)

# Sharpe ratio thresholds
SHARPE_POOR = 0.5  # Poor risk-adjusted returns
SHARPE_ACCEPTABLE = 1.0  # Acceptable risk-adjusted returns
SHARPE_GOOD = 1.5  # Good risk-adjusted returns
SHARPE_EXCELLENT = 2.0  # Excellent risk-adjusted returns

# Volatility thresholds (annualized)
VOLATILITY_LOW = 0.10  # 10% annualized volatility
VOLATILITY_MODERATE = 0.15  # 15% annualized volatility
VOLATILITY_HIGH = 0.20  # 20% annualized volatility
VOLATILITY_EXTREME = 0.30  # 30% annualized volatility

# =============================================================================
# RATING THRESHOLDS (0-10 scale)
# =============================================================================

# Quality score thresholds
QUALITY_SCORE_POOR = 4.0  # Poor quality
QUALITY_SCORE_FAIR = 6.0  # Fair quality
QUALITY_SCORE_GOOD = 7.0  # Good quality
QUALITY_SCORE_EXCELLENT = 8.0  # Excellent quality

# Dividend safety thresholds
DIVIDEND_SAFETY_RISK = 5.0  # Dividend at risk
DIVIDEND_SAFETY_FAIR = 6.0  # Fair dividend safety
DIVIDEND_SAFETY_SAFE = 7.0  # Safe dividend

# =============================================================================
# PRICE CHANGE THRESHOLDS (decimal)
# =============================================================================

# Daily price change thresholds
PRICE_CHANGE_SMALL = 0.02  # 2% daily move
PRICE_CHANGE_MODERATE = 0.05  # 5% daily move (notable)
PRICE_CHANGE_LARGE = 0.10  # 10% daily move (significant)
PRICE_CHANGE_EXTREME = 0.15  # 15% daily move (extreme)

# =============================================================================
# NEWS SENTIMENT THRESHOLDS
# =============================================================================

# Sentiment score thresholds (-1.0 to +1.0)
SENTIMENT_VERY_NEGATIVE = -0.5  # Very negative sentiment
SENTIMENT_NEGATIVE = -0.3  # Negative sentiment
SENTIMENT_NEUTRAL = 0.0  # Neutral sentiment
SENTIMENT_POSITIVE = 0.3  # Positive sentiment
SENTIMENT_VERY_POSITIVE = 0.5  # Very positive sentiment

# =============================================================================
# DATA QUALITY THRESHOLDS
# =============================================================================

# Minimum data points for statistical validity
MIN_DATA_POINTS_CORRELATION = 30  # Minimum for correlation analysis
MIN_DATA_POINTS_VOLATILITY = 20  # Minimum for volatility calculation
MIN_DATA_POINTS_REGRESSION = 50  # Minimum for regression analysis

# Maximum staleness (hours)
MAX_STALENESS_REALTIME = 1  # 1 hour for real-time data
MAX_STALENESS_DAILY = 24  # 24 hours for daily data
MAX_STALENESS_WEEKLY = 168  # 1 week for weekly data

# Price bounds (as multiplier of previous value)
PRICE_CHANGE_MAX_MULTIPLIER = 2.0  # 100% increase max (sanity check)
PRICE_CHANGE_MIN_MULTIPLIER = 0.5  # 50% decrease max (sanity check)

# =============================================================================
# MOCK/STUB DATA DETECTION
# =============================================================================

# Value used to detect mock data in deprecated services
MOCK_DATA_RANDOM_MIN = 0.0
MOCK_DATA_RANDOM_MAX = 0.3  # Random value between 0.0 and 0.3 indicates stub

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Alert cooldown
    "DEFAULT_ALERT_COOLDOWN_HOURS",
    "DEFAULT_ALERT_LOOKBACK_HOURS",
    "ALERT_COOLDOWN_EXTENDED",
    "ALERT_COOLDOWN_WEEKLY",
    # VIX thresholds
    "VIX_ELEVATED_THRESHOLD",
    "VIX_HIGH_THRESHOLD",
    "VIX_EXTREME_THRESHOLD",
    # Unemployment thresholds
    "UNEMPLOYMENT_LOW_THRESHOLD",
    "UNEMPLOYMENT_NORMAL_THRESHOLD",
    "UNEMPLOYMENT_HIGH_THRESHOLD",
    # Drawdown thresholds
    "MAX_DRAWDOWN_WARNING",
    "MAX_DRAWDOWN_ALERT",
    "MAX_DRAWDOWN_CRITICAL",
    # Sharpe ratio thresholds
    "SHARPE_POOR",
    "SHARPE_ACCEPTABLE",
    "SHARPE_GOOD",
    "SHARPE_EXCELLENT",
    # Volatility thresholds
    "VOLATILITY_LOW",
    "VOLATILITY_MODERATE",
    "VOLATILITY_HIGH",
    "VOLATILITY_EXTREME",
    # Quality scores
    "QUALITY_SCORE_POOR",
    "QUALITY_SCORE_FAIR",
    "QUALITY_SCORE_GOOD",
    "QUALITY_SCORE_EXCELLENT",
    # Dividend safety
    "DIVIDEND_SAFETY_RISK",
    "DIVIDEND_SAFETY_FAIR",
    "DIVIDEND_SAFETY_SAFE",
    # Price change thresholds
    "PRICE_CHANGE_SMALL",
    "PRICE_CHANGE_MODERATE",
    "PRICE_CHANGE_LARGE",
    "PRICE_CHANGE_EXTREME",
    # Sentiment thresholds
    "SENTIMENT_VERY_NEGATIVE",
    "SENTIMENT_NEGATIVE",
    "SENTIMENT_NEUTRAL",
    "SENTIMENT_POSITIVE",
    "SENTIMENT_VERY_POSITIVE",
    # Data quality
    "MIN_DATA_POINTS_CORRELATION",
    "MIN_DATA_POINTS_VOLATILITY",
    "MIN_DATA_POINTS_REGRESSION",
    "MAX_STALENESS_REALTIME",
    "MAX_STALENESS_DAILY",
    "MAX_STALENESS_WEEKLY",
    "PRICE_CHANGE_MAX_MULTIPLIER",
    "PRICE_CHANGE_MIN_MULTIPLIER",
    # Mock data detection
    "MOCK_DATA_RANDOM_MIN",
    "MOCK_DATA_RANDOM_MAX",
]
