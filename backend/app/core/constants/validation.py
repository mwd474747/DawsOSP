"""
Data Validation & Alert Threshold Constants

Domain: Alert conditions, mock/stub data detection
Sources: Alert service requirements
Identified by: Analysis of alerts.py

This module contains constants used for:
- Alert cooldown periods
- Mock/stub data detection in deprecated services

Cleanup History:
- 2025-11-07: Removed 43 unused constants (91.5% waste)
  - Removed: VIX thresholds, unemployment thresholds, drawdown thresholds
  - Removed: Sharpe/volatility/quality/dividend/sentiment thresholds
  - Removed: Data quality thresholds, price change thresholds
  - Removed: Extended cooldown periods
  - Reason: Never used in codebase (planned but not implemented features)
"""

# =============================================================================
# ALERT COOLDOWN PERIODS (hours)
# =============================================================================

# Default cooldown to prevent alert spam
DEFAULT_ALERT_COOLDOWN_HOURS = 24  # 24 hours (1 day)

# Alert lookback for duplicate detection
DEFAULT_ALERT_LOOKBACK_HOURS = 24  # Check last 24 hours for duplicates

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
    # Mock data detection
    "MOCK_DATA_RANDOM_MIN",
    "MOCK_DATA_RANDOM_MAX",
]
