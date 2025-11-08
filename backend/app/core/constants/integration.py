"""
External API Integration Constants

Domain: FRED, FMP API integration
Sources: API documentation, rate limit specs
Identified by: Replit analysis + Constants audit 2025-11-07

This module contains constants used for:
- API timeout configuration
- Retry policies
- Rate limiting per provider

Cleanup History:
- 2025-11-07: Removed 28 unused constants (70% waste)
  - Removed: Provider-specific timeouts (FRED/FMP/POLYGON/NEWS_API_TIMEOUT) (unused)
  - Removed: DEFAULT_CONNECTION_TIMEOUT (duplicate with network.py, removed from here)
  - Removed: DEFAULT_READ_TIMEOUT, DEFAULT_REQUEST_TIMEOUT (unused)
  - Removed: DEFAULT_BACKOFF_FACTOR, MAX_RETRY_DELAY (unused)
  - Removed: RETRYABLE_STATUS_CODES (duplicate with http_status.py, removed from here)
  - Removed: All generic rate limits (DEFAULT_RATE_LIMIT_*) (unused)
  - Removed: FMP/POLYGON/NEWS rate limit windows (unused)
  - Removed: All cache TTL constants (unused - no caching implemented)
  - Removed: All batch processing constants (unused)
  - Removed: All data quality constants (unused)
  - Note: Kept only actively used integration constants
"""

# =============================================================================
# API TIMEOUT CONFIGURATION
# =============================================================================

# Default timeout for all HTTP requests (seconds)
DEFAULT_HTTP_TIMEOUT = 30.0

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================

# Maximum retry attempts for failed requests
DEFAULT_MAX_RETRIES = 3

# Initial retry delay (seconds)
DEFAULT_RETRY_DELAY = 1.0

# =============================================================================
# RATE LIMITING
# =============================================================================

# FRED API rate limits
# Source: https://fred.stlouisfed.org/docs/api/rate_limits.html
FRED_RATE_LIMIT_REQUESTS = 120
FRED_RATE_LIMIT_WINDOW = 60

# FMP API rate limits (free tier)
# Source: https://site.financialmodelingprep.com/developer/docs/pricing
FMP_RATE_LIMIT_REQUESTS = 300

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Timeouts
    "DEFAULT_HTTP_TIMEOUT",
    # Retry configuration
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY",
    # Rate limiting
    "FRED_RATE_LIMIT_REQUESTS",
    "FRED_RATE_LIMIT_WINDOW",
    "FMP_RATE_LIMIT_REQUESTS",
]
