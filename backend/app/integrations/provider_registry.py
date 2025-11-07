
"""
Provider Registry - Centralized API Client Management

Purpose: Single source of truth for all external API providers
- Ensures single instance per provider (connection pooling)
- Shares rate limiter state across requests
- Shares circuit breaker state
- Validates API keys on startup

Usage:
    from app.integrations.provider_registry import get_provider_registry
    
    registry = get_provider_registry()
    fmp = registry.get_fmp_provider()
    fred = registry.get_fred_provider()
"""

import logging
import os
from typing import Optional

from app.integrations.fmp_provider import FMPProvider
from app.integrations.fred_provider import FREDProvider
from app.integrations.polygon_provider import PolygonProvider
from app.integrations.news_provider import NewsAPIProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Singleton registry for all external API providers.
    
    Ensures single instance per provider for:
    - Connection pooling
    - Rate limiter state sharing
    - Circuit breaker state sharing
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._fmp_provider: Optional[FMPProvider] = None
        self._fred_provider: Optional[FREDProvider] = None
        self._polygon_provider: Optional[PolygonProvider] = None
        self._news_provider: Optional[NewsAPIProvider] = None
        
        self._initialized = True
        logger.info("ProviderRegistry initialized")
    
    def get_fmp_provider(self) -> FMPProvider:
        """Get FMP provider instance (singleton)"""
        if self._fmp_provider is None:
            api_key = os.getenv("FMP_API_KEY")
            if not api_key:
                raise ValueError(
                    "FMP_API_KEY not found in environment. "
                    "Please add it to Replit Secrets."
                )
            self._fmp_provider = FMPProvider(api_key=api_key)
            logger.info("✅ FMP provider initialized")
        
        return self._fmp_provider
    
    def get_fred_provider(self) -> FREDProvider:
        """Get FRED provider instance (singleton)"""
        if self._fred_provider is None:
            api_key = os.getenv("FRED_API_KEY")
            if not api_key:
                raise ValueError(
                    "FRED_API_KEY not found in environment. "
                    "Please add it to Replit Secrets."
                )
            self._fred_provider = FREDProvider(api_key=api_key)
            logger.info("✅ FRED provider initialized")
        
        return self._fred_provider
    
    def get_polygon_provider(self) -> PolygonProvider:
        """Get Polygon provider instance (singleton)"""
        if self._polygon_provider is None:
            api_key = os.getenv("POLYGON_API_KEY")
            if not api_key:
                raise ValueError(
                    "POLYGON_API_KEY not found in environment. "
                    "Please add it to Replit Secrets."
                )
            self._polygon_provider = PolygonProvider(api_key=api_key)
            logger.info("✅ Polygon provider initialized")
        
        return self._polygon_provider
    
    def get_news_provider(self, tier: str = "dev") -> NewsAPIProvider:
        """Get NewsAPI provider instance (singleton)"""
        if self._news_provider is None:
            api_key = os.getenv("NEWSAPI_KEY")
            if not api_key:
                raise ValueError(
                    "NEWSAPI_KEY not found in environment. "
                    "Please add it to Replit Secrets."
                )
            self._news_provider = NewsAPIProvider(api_key=api_key, tier=tier)
            logger.info("✅ NewsAPI provider initialized")
        
        return self._news_provider
    
    def validate_all_keys(self) -> dict:
        """
        Validate all API keys are configured.
        
        Returns:
            Dict with validation results:
            {
                "FMP_API_KEY": True/False,
                "FRED_API_KEY": True/False,
                ...
            }
        """
        keys = {
            "FMP_API_KEY": os.getenv("FMP_API_KEY"),
            "FRED_API_KEY": os.getenv("FRED_API_KEY"),
            "POLYGON_API_KEY": os.getenv("POLYGON_API_KEY"),
            "NEWSAPI_KEY": os.getenv("NEWSAPI_KEY"),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        }
        
        results = {key: bool(value) for key, value in keys.items()}
        
        missing = [key for key, present in results.items() if not present]
        if missing:
            logger.warning(f"⚠️ Missing API keys: {', '.join(missing)}")
        else:
            logger.info("✅ All API keys configured")
        
        return results


# Singleton instance
_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Get provider registry singleton"""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
