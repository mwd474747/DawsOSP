"""Pydantic models for DawsOS API validation.

This package provides runtime type validation for all external API integrations,
ensuring data integrity and preventing format incompatibility issues.

Phase 2 of comprehensive remediation plan (Week 2-3).
"""

# Base models
from models.base import (
    APIResponse,
    DataQuality,
    ValidationError,
    HealthStatus,
    CacheMetadata,
    Observation,
    TimeSeriesMetadata,
)

# Economic data models (FRED)
from models.economic_data import (
    FREDObservation,
    SeriesData,
    EconomicDataResponse,
    FREDHealthStatus,
    EconomicIndicator,
)

# Market data models (FMP stocks)
from models.market_data import (
    StockQuote,
    CompanyProfile,
    HistoricalPrice,
)

# News data models (NewsAPI)
from models.news import (
    NewsArticle,
    NewsResponse,
    SentimentSummary,
)

# Fundamentals data models (FMP)
from models.fundamentals import (
    CompanyOverview,
    FinancialRatios,
    KeyMetrics,
    FinancialStatement,
)

# Options data models (Polygon.io)

# Crypto data models (CoinGecko)
from models.crypto import (
    CryptoPrice,
    CryptoQuote,
    CryptoMarketSummary,
)
from models.options import (
    OptionsContract,
    GreeksData,
    OptionChainResponse,
    UnusualActivityAlert,
    IVRankData,
    # Crypto data
    'CryptoPrice',
    'CryptoQuote',
    'CryptoMarketSummary',
)

__all__ = [
    # Base models
    'APIResponse',
    'DataQuality',
    'ValidationError',
    'HealthStatus',
    'CacheMetadata',
    'Observation',
    'TimeSeriesMetadata',
    # Economic data
    'FREDObservation',
    'SeriesData',
    'EconomicDataResponse',
    'FREDHealthStatus',
    'EconomicIndicator',
    # Market data
    'StockQuote',
    'CompanyProfile',
    'HistoricalPrice',
    # News data
    'NewsArticle',
    'NewsResponse',
    'SentimentSummary',
    # Fundamentals data
    'CompanyOverview',
    'FinancialRatios',
    'KeyMetrics',
    'FinancialStatement',
    # Options data
    'OptionsContract',
    'GreeksData',
    'OptionChainResponse',
    'UnusualActivityAlert',
    'IVRankData',
]

__version__ = '1.5.0'
