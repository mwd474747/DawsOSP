"""
Reusable Time Period Definitions

Domain: Canonical time unit conversions
Used by: Re-exported via constants/__init__.py for convenience
Identified by: Constants audit 2025-11-07

This module provides canonical time period constants.
Most financial-specific constants moved to financial.py.

Cleanup History:
- 2025-11-07: Removed 31 unused constants (86% waste)
  - Removed: All seconds/minutes/hours conversions (unused)
  - Removed: All PERIOD_* constants (unused)
  - Removed: Most trading calendar constants (duplicated in financial.py)
  - Kept: SECONDS_PER_DAY, DAYS_PER_YEAR (re-exported by __init__.py)
  - Note: MONTHS_PER_YEAR, WEEKS_PER_YEAR kept as canonical source
"""

# =============================================================================
# TIME UNIT CONVERSIONS (Canonical source)
# =============================================================================

# Seconds (minimal set - re-exported by __init__.py)
SECONDS_PER_DAY = 86400  # 24 * 60 * 60

# Days (canonical definitions)
DAYS_PER_YEAR = 365

# Weeks (canonical definition - used indirectly via financial.py)
WEEKS_PER_YEAR = 52

# Months (canonical definition - used indirectly via financial.py)
MONTHS_PER_YEAR = 12

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    "SECONDS_PER_DAY",
    "DAYS_PER_YEAR",
    "WEEKS_PER_YEAR",
    "MONTHS_PER_YEAR",
]
