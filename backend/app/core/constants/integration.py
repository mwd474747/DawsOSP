"""
External API Integration Constants

Domain: FRED, FMP, Polygon, News APIs
Sources: API documentation, rate limit specs
Identified by: Replit analysis (25+ instances)

This module contains constants used for:
- API timeout configuration
- Retry policies and backoff strategies
- Rate limiting per provider
- Cache TTL settings
- Batch processing limits
"""

# =============================================================================
# API TIMEOUT CONFIGURATION
# =============================================================================

# Default timeout for all HTTP requests (seconds)
DEFAULT_HTTP_TIMEOUT = 30.0

# Provider-specific timeouts
FRED_API_TIMEOUT = 30
FMP_API_TIMEOUT = 30
POLYGON_API_TIMEOUT = 30
NEWS_API_TIMEOUT = 15  # News APIs typically faster

# Connection timeout (seconds)
# Time to wait for initial connection
DEFAULT_CONNECTION_TIMEOUT = 10

# Read timeout (seconds)
# Time to wait for response after connection
DEFAULT_READ_TIMEOUT = 30

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================

# Maximum retry attempts for failed requests
DEFAULT_MAX_RETRIES = 3

# Initial retry delay (seconds)
DEFAULT_RETRY_DELAY = 1.0

# Backoff multiplier for exponential backoff
# Delay = initial_delay * (backoff_factor ^ attempt)
DEFAULT_BACKOFF_FACTOR = 2.0

# Maximum retry delay (seconds)
# Caps exponential backoff
MAX_RETRY_DELAY = 60.0

# Status codes to retry on
RETRYABLE_STATUS_CODES = [429, 500, 502, 503, 504]

# =============================================================================
# RATE LIMITING
# =============================================================================

# Generic rate limits (fallback)
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds

# FRED API rate limits
# Source: https://fred.stlouisfed.org/docs/api/rate_limits.html
FRED_RATE_LIMIT_REQUESTS = 120
FRED_RATE_LIMIT_WINDOW = 60

# FMP API rate limits (free tier)
# Source: https://site.financialmodelingprep.com/developer/docs/pricing
FMP_RATE_LIMIT_REQUESTS = 300
FMP_RATE_LIMIT_WINDOW = 60

# Polygon API rate limits (basic tier)
# Source: https://polygon.io/pricing
# Note: Actual implementation uses 100 requests per minute (conservative setting)
POLYGON_RATE_LIMIT_REQUESTS = 100  # Requests per minute (conservative)
POLYGON_RATE_LIMIT_WINDOW = 60  # Per minute

# NewsAPI rate limits (free tier)
NEWS_API_RATE_LIMIT_REQUESTS = 100
NEWS_API_RATE_LIMIT_WINDOW = 86400  # Per day

# =============================================================================
# DATA CACHING (UPDATED from Replit - 8 instances)
# =============================================================================

# Cache TTL (time-to-live) in seconds
# Different purposes require different cache durations
CACHE_TTL_REALTIME = 10      # 10 seconds (for live market data)
CACHE_TTL_SHORT = 60         # 1 minute (for volatile data)
CACHE_TTL_MEDIUM = 300       # 5 minutes (for market data)
CACHE_TTL_LONG = 600         # 10 minutes (for derived metrics)
CACHE_TTL_VERY_LONG = 3600   # 1 hour (for reference data)
CACHE_TTL_HISTORICAL = 86400 # 24 hours (for historical data)

# Stale data thresholds by purpose
STALE_DATA_THRESHOLD_MARKET = 300    # 5 minutes for market data
STALE_DATA_THRESHOLD_PRICING = 3600  # 1 hour for pricing
STALE_DATA_THRESHOLD_METRICS = 86400 # 24 hours for metrics

# Cache garbage collection interval
CACHE_GC_INTERVAL = 3600  # Run GC every hour

# =============================================================================
# BATCH PROCESSING
# =============================================================================

# Default batch size for bulk API requests
DEFAULT_BATCH_SIZE = 100
MAX_BATCH_SIZE = 1000
MIN_BATCH_SIZE = 10

# Delay between batch requests (to respect rate limits)
BATCH_REQUEST_DELAY = 0.1  # 100ms

# =============================================================================
# DATA QUALITY
# =============================================================================

# Minimum data points required for time series
MIN_TIME_SERIES_DATA_POINTS = 30

# Maximum allowed gap in time series (days)
# Larger gaps may indicate data quality issue
MAX_TIME_SERIES_GAP_DAYS = 7

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Timeouts
    "DEFAULT_HTTP_TIMEOUT",
    "FRED_API_TIMEOUT",
    "FMP_API_TIMEOUT",
    "POLYGON_API_TIMEOUT",
    "NEWS_API_TIMEOUT",
    "DEFAULT_CONNECTION_TIMEOUT",
    "DEFAULT_READ_TIMEOUT",
    # Retry configuration
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY",
    "DEFAULT_BACKOFF_FACTOR",
    "MAX_RETRY_DELAY",
    "RETRYABLE_STATUS_CODES",
    # Rate limiting
    "DEFAULT_RATE_LIMIT_REQUESTS",
    "DEFAULT_RATE_LIMIT_WINDOW",
    "FRED_RATE_LIMIT_REQUESTS",
    "FRED_RATE_LIMIT_WINDOW",
    "FMP_RATE_LIMIT_REQUESTS",
    "FMP_RATE_LIMIT_WINDOW",
    "POLYGON_RATE_LIMIT_REQUESTS",
    "POLYGON_RATE_LIMIT_WINDOW",
    "NEWS_API_RATE_LIMIT_REQUESTS",
    "NEWS_API_RATE_LIMIT_WINDOW",
    # Caching
    "CACHE_TTL_REALTIME",
    "CACHE_TTL_SHORT",
    "CACHE_TTL_MEDIUM",
    "CACHE_TTL_LONG",
    "CACHE_TTL_VERY_LONG",
    "CACHE_TTL_HISTORICAL",
    "STALE_DATA_THRESHOLD_MARKET",
    "STALE_DATA_THRESHOLD_PRICING",
    "STALE_DATA_THRESHOLD_METRICS",
    "CACHE_GC_INTERVAL",
    # Batch processing
    "DEFAULT_BATCH_SIZE",
    "MAX_BATCH_SIZE",
    "MIN_BATCH_SIZE",
    "BATCH_REQUEST_DELAY",
    # Data quality
    "MIN_TIME_SERIES_DATA_POINTS",
    "MAX_TIME_SERIES_GAP_DAYS",
]
