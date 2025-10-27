"""
Provider Clients - External data provider integrations

Purpose: Connect to FMP, Polygon, and FRED APIs with resilience
Updated: 2025-10-23
Priority: P0 (Critical for production data)

Providers:
    - FMP (Financial Modeling Prep): Fundamentals (income, balance sheet, ratios)
    - Polygon: Prices and corporate actions (splits, dividends)
    - FRED: Macro indicators (yield curve, CPI, unemployment)

Each client includes:
    - Circuit breaker for failure detection
    - Rate limiter for API compliance
    - Exponential backoff with jitter for retries
    - Comprehensive error handling
"""

from backend.app.providers.fmp_client import FMPClient
from backend.app.providers.polygon_client import PolygonClient
from backend.app.providers.fred_client import FREDClient

__all__ = [
    "FMPClient",
    "PolygonClient",
    "FREDClient",
]
