"""
Polygon Client - Polygon.io API integration

Purpose: Fetch prices and corporate actions from Polygon
Updated: 2025-10-23
Priority: P0 (Critical for pricing packs)

Provider: Polygon.io
Rate Limit: 100 requests per minute
Circuit Breaker: 3 failures → OPEN (60s timeout)

Endpoints:
    - Daily Prices: GET /v2/aggs/ticker/{symbol}/range/1/day/{from}/{to}
    - Ticker Details: GET /v3/reference/tickers/{symbol}
    - Stock Splits: GET /v3/reference/splits
    - Dividends: GET /v3/reference/dividends

Usage:
    from backend.app.providers.polygon_client import PolygonClient

    client = PolygonClient(api_key="your_key")

    # Get daily prices
    prices = await client.get_daily_prices("AAPL", "2025-01-01", "2025-10-23")

    # Get splits
    splits = await client.get_splits("AAPL")

Sacred Invariants:
    1. All API calls go through circuit breaker
    2. Rate limiter enforces 100 req/min
    3. Exponential backoff: base=1s, max=60s, jitter=±20%
    4. Data attribution required in reports

References:
    - PRODUCT_SPEC.md §5 (Provider Integration)
    - https://polygon.io/docs/stocks
"""

import os
import asyncio
import logging
import random
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import aiohttp

from backend.app.core.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError
from backend.app.core.rate_limiter import get_rate_limiter

logger = logging.getLogger("DawsOS.PolygonClient")


# ============================================================================
# Exceptions
# ============================================================================


class PolygonError(Exception):
    """Base exception for Polygon client errors."""
    pass


class PolygonRateLimitError(PolygonError):
    """Rate limit exceeded."""
    pass


class PolygonAuthError(PolygonError):
    """Authentication failed."""
    pass


class PolygonNotFoundError(PolygonError):
    """Resource not found."""
    pass


# ============================================================================
# Polygon Client
# ============================================================================


class PolygonClient:
    """
    Polygon.io API client.

    Provides access to:
    - Daily OHLCV prices
    - Stock splits
    - Dividends
    - Ticker details
    """

    BASE_URL = "https://api.polygon.io"

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: int = 100,
        max_retries: int = 3,
    ):
        """
        Initialize Polygon client.

        Args:
            api_key: Polygon API key (default: from POLYGON_API_KEY env var)
            rate_limit: Requests per minute (default: 100)
            max_retries: Max retry attempts (default: 3)
        """
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            logger.warning("POLYGON_API_KEY not set, client will fail on API calls")

        self.max_retries = max_retries

        # Circuit breaker (3 failures → OPEN for 60s)
        self.circuit_breaker = get_circuit_breaker(
            name="Polygon",
            threshold=int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "3")),
            timeout=float(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60")),
        )

        # Rate limiter (100 req/min)
        self.rate_limiter = get_rate_limiter(
            name="Polygon",
            rate=rate_limit,
            per=60.0,
        )

        # HTTP session (created lazily)
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(
            f"Polygon client initialized: rate_limit={rate_limit}/min, "
            f"max_retries={max_retries}"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    # ========================================================================
    # HTTP Methods
    # ========================================================================

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make API request with circuit breaker and rate limiting.

        Args:
            endpoint: API endpoint (e.g., "/v2/aggs/ticker/AAPL/range/1/day/...")
            params: Query parameters (default: None)

        Returns:
            Response JSON

        Raises:
            PolygonError: On API error
            CircuitBreakerOpenError: If circuit is open
        """
        # Ensure we have API key
        if not self.api_key:
            raise PolygonAuthError("POLYGON_API_KEY not set")

        # Add API key to params
        params = params or {}
        params["apiKey"] = self.api_key

        # Build URL
        url = f"{self.BASE_URL}{endpoint}"

        # Acquire rate limit token
        await self.rate_limiter.acquire()

        # Make request through circuit breaker with retries
        async def _make_request():
            session = await self._get_session()

            for attempt in range(self.max_retries):
                try:
                    logger.debug(f"Polygon request: {endpoint} (attempt {attempt + 1}/{self.max_retries})")

                    async with session.get(url, params=params) as response:
                        # Check for errors
                        if response.status == 401 or response.status == 403:
                            raise PolygonAuthError("Invalid API key")
                        elif response.status == 429:
                            raise PolygonRateLimitError("Rate limit exceeded")
                        elif response.status == 404:
                            raise PolygonNotFoundError(f"Not found: {endpoint}")
                        elif response.status >= 500:
                            # Server error, retry
                            if attempt < self.max_retries - 1:
                                wait_time = self._calculate_backoff(attempt)
                                logger.warning(
                                    f"Polygon server error {response.status}, "
                                    f"retrying in {wait_time:.2f}s"
                                )
                                await asyncio.sleep(wait_time)
                                continue
                            raise PolygonError(f"Server error: {response.status}")
                        elif response.status >= 400:
                            raise PolygonError(f"Client error: {response.status}")

                        # Parse JSON
                        data = await response.json()
                        return data

                except aiohttp.ClientError as e:
                    # Network error, retry
                    if attempt < self.max_retries - 1:
                        wait_time = self._calculate_backoff(attempt)
                        logger.warning(f"Polygon network error: {e}, retrying in {wait_time:.2f}s")
                        await asyncio.sleep(wait_time)
                        continue
                    raise PolygonError(f"Network error: {e}")

            raise PolygonError(f"Max retries ({self.max_retries}) exceeded")

        # Execute through circuit breaker
        try:
            return await self.circuit_breaker.call(_make_request)
        except CircuitBreakerOpenError:
            logger.error("Polygon circuit breaker is OPEN")
            raise

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff with jitter.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Wait time in seconds
        """
        # Exponential backoff: base=1s, max=60s
        base = 1.0
        max_wait = 60.0
        wait_time = min(base * (2 ** attempt), max_wait)

        # Add jitter (±20%)
        jitter = wait_time * 0.2
        wait_time = wait_time + random.uniform(-jitter, jitter)

        return max(0, wait_time)

    # ========================================================================
    # Daily Prices
    # ========================================================================

    async def get_daily_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjusted: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get daily OHLCV prices for symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            adjusted: Use adjusted prices (default: True)

        Returns:
            List of price records (dict with keys: o, h, l, c, v, t)
                o: open price
                h: high price
                l: low price
                c: close price
                v: volume
                t: timestamp (Unix milliseconds)

        Raises:
            PolygonError: On API error
        """
        logger.info(f"Fetching daily prices: {symbol} ({start_date} to {end_date})")

        endpoint = f"/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
        params = {
            "adjusted": "true" if adjusted else "false",
            "sort": "asc",
        }

        data = await self._request(endpoint, params)

        # Check response status (Polygon returns "OK" or "DELAYED" for successful requests)
        status = data.get("status")
        if status not in ["OK", "DELAYED"]:
            error = data.get("error", "Unknown error")
            raise PolygonError(f"API error: {error}")

        # Extract results
        results = data.get("results", [])
        logger.info(f"Fetched {len(results)} price records for {symbol}")

        return results

    async def get_daily_price(
        self,
        symbol: str,
        date_str: str,
        adjusted: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Get daily price for symbol on specific date.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            date_str: Date (YYYY-MM-DD)
            adjusted: Use adjusted prices (default: True)

        Returns:
            Price record or None if not found

        Raises:
            PolygonError: On API error
        """
        logger.info(f"Fetching daily price: {symbol} ({date_str})")

        # Query for single day
        results = await self.get_daily_prices(symbol, date_str, date_str, adjusted)

        if not results:
            logger.warning(f"No price found for {symbol} on {date_str}")
            return None

        return results[0]

    # ========================================================================
    # Stock Splits
    # ========================================================================

    async def get_splits(
        self,
        symbol: Optional[str] = None,
        execution_date_gte: Optional[str] = None,
        execution_date_lte: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get stock splits.

        Args:
            symbol: Stock symbol (default: None for all)
            execution_date_gte: Min execution date (YYYY-MM-DD)
            execution_date_lte: Max execution date (YYYY-MM-DD)
            limit: Max results (default: 100)

        Returns:
            List of split records

        Raises:
            PolygonError: On API error
        """
        logger.info(f"Fetching splits: symbol={symbol}, limit={limit}")

        endpoint = "/v3/reference/splits"
        params = {"limit": limit}

        if symbol:
            params["ticker"] = symbol
        if execution_date_gte:
            params["execution_date.gte"] = execution_date_gte
        if execution_date_lte:
            params["execution_date.lte"] = execution_date_lte

        data = await self._request(endpoint, params)

        # Check response status (Polygon returns "OK" or "DELAYED" for successful requests)
        status = data.get("status")
        if status not in ["OK", "DELAYED"]:
            error = data.get("error", "Unknown error")
            raise PolygonError(f"API error: {error}")

        # Extract results
        results = data.get("results", [])
        logger.info(f"Fetched {len(results)} split records")

        return results

    # ========================================================================
    # Dividends
    # ========================================================================

    async def get_dividends(
        self,
        symbol: Optional[str] = None,
        ex_dividend_date_gte: Optional[str] = None,
        ex_dividend_date_lte: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get dividends.

        Args:
            symbol: Stock symbol (default: None for all)
            ex_dividend_date_gte: Min ex-dividend date (YYYY-MM-DD)
            ex_dividend_date_lte: Max ex-dividend date (YYYY-MM-DD)
            limit: Max results (default: 100)

        Returns:
            List of dividend records

        Raises:
            PolygonError: On API error
        """
        logger.info(f"Fetching dividends: symbol={symbol}, limit={limit}")

        endpoint = "/v3/reference/dividends"
        params = {"limit": limit}

        if symbol:
            params["ticker"] = symbol
        if ex_dividend_date_gte:
            params["ex_dividend_date.gte"] = ex_dividend_date_gte
        if ex_dividend_date_lte:
            params["ex_dividend_date.lte"] = ex_dividend_date_lte

        data = await self._request(endpoint, params)

        # Check response status (Polygon returns "OK" or "DELAYED" for successful requests)
        status = data.get("status")
        if status not in ["OK", "DELAYED"]:
            error = data.get("error", "Unknown error")
            raise PolygonError(f"API error: {error}")

        # Extract results
        results = data.get("results", [])
        logger.info(f"Fetched {len(results)} dividend records")

        return results

    # ========================================================================
    # Ticker Details
    # ========================================================================

    async def get_ticker_details(self, symbol: str) -> Dict[str, Any]:
        """
        Get ticker details.

        Args:
            symbol: Stock symbol (e.g., "AAPL")

        Returns:
            Ticker details record

        Raises:
            PolygonError: On API error
        """
        logger.info(f"Fetching ticker details: {symbol}")

        endpoint = f"/v3/reference/tickers/{symbol}"

        data = await self._request(endpoint)

        # Check response status (Polygon returns "OK" or "DELAYED" for successful requests)
        status = data.get("status")
        if status not in ["OK", "DELAYED"]:
            error = data.get("error", "Unknown error")
            raise PolygonError(f"API error: {error}")

        # Extract results
        results = data.get("results", {})
        logger.info(f"Fetched ticker details for {symbol}")

        return results

    # ========================================================================
    # Batch Queries
    # ========================================================================

    async def get_batch_daily_prices(
        self,
        symbols: List[str],
        date_str: str,
        adjusted: bool = True,
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get daily prices for multiple symbols on specific date.

        Args:
            symbols: List of stock symbols
            date_str: Date (YYYY-MM-DD)
            adjusted: Use adjusted prices (default: True)

        Returns:
            Dict mapping symbol to price record (or None if not found)
        """
        logger.info(f"Fetching batch daily prices: {len(symbols)} symbols ({date_str})")

        results = {}
        for symbol in symbols:
            try:
                price = await self.get_daily_price(symbol, date_str, adjusted)
                results[symbol] = price
            except PolygonError as e:
                logger.warning(f"Failed to fetch price for {symbol}: {e}")
                results[symbol] = None

        return results


# ============================================================================
# Global Instance
# ============================================================================


_polygon_client: Optional[PolygonClient] = None


def get_polygon_client(api_key: Optional[str] = None) -> PolygonClient:
    """
    Get singleton Polygon client instance.

    Args:
        api_key: Polygon API key (default: from POLYGON_API_KEY env var)

    Returns:
        PolygonClient instance
    """
    global _polygon_client
    if _polygon_client is None:
        _polygon_client = PolygonClient(api_key=api_key)
    return _polygon_client
