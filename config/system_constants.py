#!/usr/bin/env python3
"""
System Constants - Phase 2.4

Centralized system configuration constants.
Eliminates magic numbers for caching, performance, and data quality settings.

All constants are well-documented with rationale.
"""


class SystemConstants:
    """System configuration constants for caching, performance, and quality"""

    # ==================== CACHING ====================

    # Knowledge loader cache TTL (time-to-live)
    KNOWLEDGE_CACHE_TTL_MINUTES = 30  # 30 minutes

    # Enriched data maximum age before refresh
    ENRICHED_DATA_MAX_AGE_HOURS = 24  # 24 hours (1 day)

    # Graph traversal cache size limit
    GRAPH_TRAVERSAL_CACHE_SIZE = 1000  # Max 1000 cached queries

    # ==================== PERFORMANCE ====================

    # Maximum depth for graph traversal
    MAX_GRAPH_TRAVERSAL_DEPTH = 5  # Prevent infinite loops

    # Maximum time for pattern execution
    MAX_PATTERN_EXECUTION_TIME_SECONDS = 30  # 30 seconds timeout

    # Maximum recursion depth for nested pattern execution
    MAX_PATTERN_RECURSION_DEPTH = 5  # Prevent infinite recursion

    # ==================== DATA QUALITY ====================

    # Minimum confidence score to proceed with analysis
    MINIMUM_CONFIDENCE_SCORE = 0.5  # 50%

    # High confidence threshold for reliable results
    HIGH_CONFIDENCE_THRESHOLD = 0.8  # 80%

    # Minimum required fields for financial data completeness
    REQUIRED_FINANCIAL_FIELDS = ['free_cash_flow', 'net_income', 'revenue', 'ebit']

    # ==================== PERSISTENCE ====================

    # Backup retention period
    BACKUP_RETENTION_DAYS = 30  # 30 days

    # Auto-rotation file size threshold
    AUTO_ROTATION_SIZE_MB = 10  # 10 MB

    # Checksum algorithm
    CHECKSUM_ALGORITHM = 'sha256'

    # ==================== LOGGING ====================

    # Default log level
    DEFAULT_LOG_LEVEL = 'INFO'

    # Maximum log file size before rotation
    MAX_LOG_FILE_SIZE_MB = 50  # 50 MB

    # Number of rotated log files to keep
    LOG_BACKUP_COUNT = 5

    # ==================== API RATE LIMITING ====================

    # Maximum API requests per minute (FMP API)
    MAX_API_REQUESTS_PER_MINUTE = 300  # FMP free tier limit

    # Retry attempts for failed API calls
    API_RETRY_ATTEMPTS = 3

    # Delay between retries (seconds)
    API_RETRY_DELAY_SECONDS = 1

    # ==================== UI CONFIGURATION ====================

    # Streamlit page refresh interval (seconds)
    UI_REFRESH_INTERVAL_SECONDS = 60  # 1 minute

    # Maximum items to display in lists
    MAX_DISPLAY_ITEMS = 100

    # Chart default height (pixels)
    DEFAULT_CHART_HEIGHT = 400

    # ==================== VALIDATION ====================

    # Stock symbol length constraints
    MIN_SYMBOL_LENGTH = 1
    MAX_SYMBOL_LENGTH = 5

    # Maximum number of stocks in portfolio analysis
    MAX_PORTFOLIO_STOCKS = 50

    # Maximum number of stocks for comparison
    MAX_COMPARISON_STOCKS = 10
