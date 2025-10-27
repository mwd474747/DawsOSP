"""
Provider Facades - Unified interface for all data providers

Purpose: Single entry point for accessing FMP, Polygon, and FRED data
Updated: 2025-10-23
Priority: P0 (Critical for data access)

This module provides:
    1. Unified interface wrapping all provider clients
    2. In-memory caching with TTL (Redis optional)
    3. Graceful fallback to stubs if providers unavailable
    4. Attribution tracking for reports

Architecture:
    - ProviderFacade: Main interface for accessing all providers
    - Route fundamentals → FMP
    - Route prices → Polygon
    - Route macro → FRED
    - Cache all responses with TTL
    - Fallback to stubs on circuit breaker open

Usage:
    from backend.app.services.providers import get_provider_facade

    facade = get_provider_facade()

    # Get fundamentals
    income = await facade.get_fundamentals("AAPL")

    # Get prices
    prices = await facade.get_prices("AAPL", "2025-01-01", "2025-10-23")

    # Get macro series
    yield_curve = await facade.get_macro_series("T10Y2Y", "2024-01-01", "2025-10-23")

Sacred Invariants:
    1. All provider calls go through facade
    2. Cache hits bypass provider calls
    3. Circuit breaker failures trigger stub fallback
    4. Attribution tracked for all responses

References:
    - PRODUCT_SPEC.md §5 (Provider Integration)
"""

import logging
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import json

from backend.app.providers.fmp_client import get_fmp_client, FMPError
from backend.app.providers.polygon_client import get_polygon_client, PolygonError
from backend.app.providers.fred_client import get_fred_client, FREDError
from backend.app.core.circuit_breaker import CircuitBreakerOpenError

logger = logging.getLogger("DawsOS.ProviderFacade")


# ============================================================================
# Cache
# ============================================================================


class InMemoryCache:
    """
    Simple in-memory cache with TTL.

    Note: This is a simple implementation. For production, use Redis.
    """

    def __init__(self):
        """Initialize cache."""
        self._cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_time)
        logger.info("In-memory cache initialized")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]

        # Check if expired
        if time.time() > expiry:
            del self._cache[key]
            return None

        logger.debug(f"Cache hit: {key}")
        return value

    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 3600 = 1 hour)
        """
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
        logger.debug(f"Cache set: {key} (ttl={ttl}s)")

    def delete(self, key: str):
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache delete: {key}")

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        # Count non-expired entries
        now = time.time()
        valid_entries = sum(1 for _, expiry in self._cache.values() if expiry > now)

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._cache) - valid_entries,
        }


# ============================================================================
# Provider Facade
# ============================================================================


class ProviderFacade:
    """
    Unified facade for all data providers.

    Routes requests to appropriate provider:
    - Fundamentals → FMP
    - Prices → Polygon
    - Macro → FRED

    Includes caching and stub fallback.
    """

    def __init__(
        self,
        use_cache: bool = True,
        stub_fallback: bool = True,
    ):
        """
        Initialize provider facade.

        Args:
            use_cache: Enable caching (default: True)
            stub_fallback: Fall back to stubs on provider failures (default: True)
        """
        self.use_cache = use_cache
        self.stub_fallback = stub_fallback

        # Initialize clients
        self.fmp_client = get_fmp_client()
        self.polygon_client = get_polygon_client()
        self.fred_client = get_fred_client()

        # Initialize cache
        self.cache = InMemoryCache() if use_cache else None

        logger.info(
            f"Provider facade initialized: "
            f"use_cache={use_cache}, stub_fallback={stub_fallback}"
        )

    # ========================================================================
    # Fundamentals (FMP)
    # ========================================================================

    async def get_fundamentals(
        self,
        symbol: str,
        include_income: bool = True,
        include_balance: bool = True,
        include_cash_flow: bool = True,
        include_ratios: bool = True,
        period: str = "annual",
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Get fundamentals for symbol (income, balance sheet, cash flow, ratios).

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            include_income: Include income statement (default: True)
            include_balance: Include balance sheet (default: True)
            include_cash_flow: Include cash flow statement (default: True)
            include_ratios: Include financial ratios (default: True)
            period: "annual" or "quarter" (default: "annual")
            limit: Number of periods (default: 5)

        Returns:
            Dict with keys: symbol, income, balance, cash_flow, ratios, attribution
        """
        # Check cache
        cache_key = f"fundamentals:{symbol}:{period}:{limit}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        result = {
            "symbol": symbol,
            "income": [],
            "balance": [],
            "cash_flow": [],
            "ratios": [],
            "attribution": "Financial Modeling Prep",
        }

        try:
            # Fetch income statement
            if include_income:
                result["income"] = await self.fmp_client.get_income_statement(
                    symbol, period, limit
                )

            # Fetch balance sheet
            if include_balance:
                result["balance"] = await self.fmp_client.get_balance_sheet(
                    symbol, period, limit
                )

            # Fetch cash flow
            if include_cash_flow:
                result["cash_flow"] = await self.fmp_client.get_cash_flow(
                    symbol, period, limit
                )

            # Fetch ratios
            if include_ratios:
                result["ratios"] = await self.fmp_client.get_ratios(
                    symbol, period, limit
                )

            # Cache result (TTL: 1 hour)
            if self.cache:
                self.cache.set(cache_key, result, ttl=3600)

            return result

        except (FMPError, CircuitBreakerOpenError) as e:
            logger.warning(f"FMP error for {symbol}: {e}")

            # Fallback to stub if enabled
            if self.stub_fallback:
                logger.info(f"Falling back to stub fundamentals for {symbol}")
                return self._stub_fundamentals(symbol)

            raise

    def _stub_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Return stub fundamentals data."""
        return {
            "symbol": symbol,
            "income": [],
            "balance": [],
            "cash_flow": [],
            "ratios": [],
            "attribution": "Stub data (provider unavailable)",
        }

    # ========================================================================
    # Prices (Polygon)
    # ========================================================================

    async def get_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjusted: bool = True,
    ) -> Dict[str, Any]:
        """
        Get daily prices for symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            adjusted: Use adjusted prices (default: True)

        Returns:
            Dict with keys: symbol, prices, attribution
        """
        # Check cache
        cache_key = f"prices:{symbol}:{start_date}:{end_date}:{adjusted}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            prices = await self.polygon_client.get_daily_prices(
                symbol, start_date, end_date, adjusted
            )

            result = {
                "symbol": symbol,
                "prices": prices,
                "attribution": "Polygon.io",
            }

            # Cache result (TTL: 1 hour)
            if self.cache:
                self.cache.set(cache_key, result, ttl=3600)

            return result

        except (PolygonError, CircuitBreakerOpenError) as e:
            logger.warning(f"Polygon error for {symbol}: {e}")

            # Fallback to stub if enabled
            if self.stub_fallback:
                logger.info(f"Falling back to stub prices for {symbol}")
                return self._stub_prices(symbol, start_date, end_date)

            raise

    def _stub_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Return stub prices data."""
        return {
            "symbol": symbol,
            "prices": [],
            "attribution": "Stub data (provider unavailable)",
        }

    # ========================================================================
    # Corporate Actions (Polygon)
    # ========================================================================

    async def get_splits(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get stock splits for symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            start_date: Start date (YYYY-MM-DD, default: None)
            end_date: End date (YYYY-MM-DD, default: None)

        Returns:
            Dict with keys: symbol, splits, attribution
        """
        # Check cache
        cache_key = f"splits:{symbol}:{start_date}:{end_date}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            splits = await self.polygon_client.get_splits(
                symbol=symbol,
                execution_date_gte=start_date,
                execution_date_lte=end_date,
            )

            result = {
                "symbol": symbol,
                "splits": splits,
                "attribution": "Polygon.io",
            }

            # Cache result (TTL: 24 hours, splits don't change often)
            if self.cache:
                self.cache.set(cache_key, result, ttl=86400)

            return result

        except (PolygonError, CircuitBreakerOpenError) as e:
            logger.warning(f"Polygon error for {symbol} splits: {e}")

            # Fallback to stub if enabled
            if self.stub_fallback:
                logger.info(f"Falling back to stub splits for {symbol}")
                return {"symbol": symbol, "splits": [], "attribution": "Stub data"}

            raise

    async def get_dividends(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get dividends for symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            start_date: Start date (YYYY-MM-DD, default: None)
            end_date: End date (YYYY-MM-DD, default: None)

        Returns:
            Dict with keys: symbol, dividends, attribution
        """
        # Check cache
        cache_key = f"dividends:{symbol}:{start_date}:{end_date}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            dividends = await self.polygon_client.get_dividends(
                symbol=symbol,
                ex_dividend_date_gte=start_date,
                ex_dividend_date_lte=end_date,
            )

            result = {
                "symbol": symbol,
                "dividends": dividends,
                "attribution": "Polygon.io",
            }

            # Cache result (TTL: 24 hours)
            if self.cache:
                self.cache.set(cache_key, result, ttl=86400)

            return result

        except (PolygonError, CircuitBreakerOpenError) as e:
            logger.warning(f"Polygon error for {symbol} dividends: {e}")

            # Fallback to stub if enabled
            if self.stub_fallback:
                logger.info(f"Falling back to stub dividends for {symbol}")
                return {"symbol": symbol, "dividends": [], "attribution": "Stub data"}

            raise

    # ========================================================================
    # Macro (FRED)
    # ========================================================================

    async def get_macro_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get macro series from FRED.

        Args:
            series_id: FRED series ID (e.g., "T10Y2Y", "UNRATE")
            start_date: Start date (YYYY-MM-DD, default: None)
            end_date: End date (YYYY-MM-DD, default: None)

        Returns:
            Dict with keys: series_id, observations, attribution
        """
        # Check cache
        cache_key = f"macro:{series_id}:{start_date}:{end_date}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            observations = await self.fred_client.get_series_observations(
                series_id, start_date, end_date
            )

            result = {
                "series_id": series_id,
                "observations": observations,
                "attribution": "Federal Reserve Economic Data (FRED)",
            }

            # Cache result (TTL: 1 hour)
            if self.cache:
                self.cache.set(cache_key, result, ttl=3600)

            return result

        except (FREDError, CircuitBreakerOpenError) as e:
            logger.warning(f"FRED error for {series_id}: {e}")

            # Fallback to stub if enabled
            if self.stub_fallback:
                logger.info(f"Falling back to stub macro for {series_id}")
                return self._stub_macro(series_id)

            raise

    def _stub_macro(self, series_id: str) -> Dict[str, Any]:
        """Return stub macro data."""
        return {
            "series_id": series_id,
            "observations": [],
            "attribution": "Stub data (provider unavailable)",
        }

    # ========================================================================
    # Cache Management
    # ========================================================================

    def clear_cache(self):
        """Clear all cache entries."""
        if self.cache:
            self.cache.clear()
            logger.info("Provider cache cleared")

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics."""
        if self.cache:
            return self.cache.get_stats()
        return None


# ============================================================================
# Global Instance
# ============================================================================


_provider_facade: Optional[ProviderFacade] = None


def get_provider_facade(
    use_cache: bool = True,
    stub_fallback: bool = True,
) -> ProviderFacade:
    """
    Get singleton ProviderFacade instance.

    Args:
        use_cache: Enable caching (default: True)
        stub_fallback: Fall back to stubs on provider failures (default: True)

    Returns:
        ProviderFacade instance
    """
    global _provider_facade
    if _provider_facade is None:
        _provider_facade = ProviderFacade(
            use_cache=use_cache,
            stub_fallback=stub_fallback,
        )
    return _provider_facade
