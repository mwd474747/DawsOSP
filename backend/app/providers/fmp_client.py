"""
FMP Client - Financial Modeling Prep API integration

Purpose: Fetch fundamentals from FMP (income statements, balance sheets, ratios)
Updated: 2025-10-23
Priority: P0 (Critical for fundamental analysis)

Provider: Financial Modeling Prep (FMP Premium)
Rate Limit: 120 requests per minute
Circuit Breaker: 3 failures → OPEN (60s timeout)

Endpoints:
    - Income Statement: GET /income-statement/{symbol}
    - Balance Sheet: GET /balance-sheet-statement/{symbol}
    - Cash Flow: GET /cash-flow-statement/{symbol}
    - Financial Ratios: GET /ratios/{symbol}
    - Company Profile: GET /profile/{symbol}

Usage:
    from backend.app.providers.fmp_client import FMPClient

    client = FMPClient(api_key="your_key")

    # Get income statement
    income = await client.get_income_statement("AAPL")

    # Get financial ratios
    ratios = await client.get_ratios("AAPL", limit=5)

Sacred Invariants:
    1. All API calls go through circuit breaker
    2. Rate limiter enforces 120 req/min
    3. Exponential backoff: base=1s, max=60s, jitter=±20%
    4. Data attribution required in reports

References:
    - PRODUCT_SPEC.md §5 (Provider Integration)
    - https://site.financialmodelingprep.com/developer/docs
"""

import os
import asyncio
import logging
import random
from typing import Optional, List, Dict, Any
from datetime import datetime
import aiohttp

from backend.app.core.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError
from backend.app.core.rate_limiter import get_rate_limiter

logger = logging.getLogger("DawsOS.FMPClient")


# ============================================================================
# Exceptions
# ============================================================================


class FMPError(Exception):
    """Base exception for FMP client errors."""
    pass


class FMPRateLimitError(FMPError):
    """Rate limit exceeded."""
    pass


class FMPAuthError(FMPError):
    """Authentication failed."""
    pass


class FMPNotFoundError(FMPError):
    """Resource not found."""
    pass


# ============================================================================
# FMP Client
# ============================================================================


class FMPClient:
    """
    Financial Modeling Prep API client.

    Provides access to:
    - Income statements
    - Balance sheets
    - Cash flow statements
    - Financial ratios
    - Company profiles
    """

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: int = 120,
        max_retries: int = 3,
    ):
        """
        Initialize FMP client.

        Args:
            api_key: FMP API key (default: from FMP_API_KEY env var)
            rate_limit: Requests per minute (default: 120)
            max_retries: Max retry attempts (default: 3)
        """
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        if not self.api_key:
            logger.warning("FMP_API_KEY not set, client will fail on API calls")

        self.max_retries = max_retries

        # Circuit breaker (3 failures → OPEN for 60s)
        self.circuit_breaker = get_circuit_breaker(
            name="FMP",
            threshold=int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "3")),
            timeout=float(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60")),
        )

        # Rate limiter (120 req/min)
        self.rate_limiter = get_rate_limiter(
            name="FMP",
            rate=rate_limit,
            per=60.0,
        )

        # HTTP session (created lazily)
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(
            f"FMP client initialized: rate_limit={rate_limit}/min, "
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
            endpoint: API endpoint (e.g., "/income-statement/AAPL")
            params: Query parameters (default: None)

        Returns:
            Response JSON

        Raises:
            FMPError: On API error
            CircuitBreakerOpenError: If circuit is open
        """
        # Ensure we have API key
        if not self.api_key:
            raise FMPAuthError("FMP_API_KEY not set")

        # Add API key to params
        params = params or {}
        params["apikey"] = self.api_key

        # Build URL
        url = f"{self.BASE_URL}{endpoint}"

        # Acquire rate limit token
        await self.rate_limiter.acquire()

        # Make request through circuit breaker with retries
        async def _make_request():
            session = await self._get_session()

            for attempt in range(self.max_retries):
                try:
                    logger.debug(f"FMP request: {endpoint} (attempt {attempt + 1}/{self.max_retries})")

                    async with session.get(url, params=params) as response:
                        # Check for errors
                        if response.status == 401:
                            raise FMPAuthError("Invalid API key")
                        elif response.status == 429:
                            raise FMPRateLimitError("Rate limit exceeded")
                        elif response.status == 404:
                            raise FMPNotFoundError(f"Not found: {endpoint}")
                        elif response.status >= 500:
                            # Server error, retry
                            if attempt < self.max_retries - 1:
                                wait_time = self._calculate_backoff(attempt)
                                logger.warning(
                                    f"FMP server error {response.status}, "
                                    f"retrying in {wait_time:.2f}s"
                                )
                                await asyncio.sleep(wait_time)
                                continue
                            raise FMPError(f"Server error: {response.status}")
                        elif response.status >= 400:
                            raise FMPError(f"Client error: {response.status}")

                        # Parse JSON
                        data = await response.json()
                        return data

                except aiohttp.ClientError as e:
                    # Network error, retry
                    if attempt < self.max_retries - 1:
                        wait_time = self._calculate_backoff(attempt)
                        logger.warning(f"FMP network error: {e}, retrying in {wait_time:.2f}s")
                        await asyncio.sleep(wait_time)
                        continue
                    raise FMPError(f"Network error: {e}")

            raise FMPError(f"Max retries ({self.max_retries}) exceeded")

        # Execute through circuit breaker
        try:
            return await self.circuit_breaker.call(_make_request)
        except CircuitBreakerOpenError:
            logger.error("FMP circuit breaker is OPEN")
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
    # Income Statement
    # ========================================================================

    async def get_income_statement(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get income statement for symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            period: "annual" or "quarter" (default: "annual")
            limit: Number of periods to return (default: 5)

        Returns:
            List of income statement records (newest first)

        Raises:
            FMPError: On API error
        """
        logger.info(f"Fetching income statement: {symbol} ({period}, limit={limit})")

        endpoint = f"/income-statement/{symbol}"
        params = {"period": period, "limit": limit}

        data = await self._request(endpoint, params)

        # FMP returns list of statements
        if not isinstance(data, list):
            raise FMPError(f"Unexpected response format: {type(data)}")

        logger.info(f"Fetched {len(data)} income statement periods for {symbol}")
        return data

    # ========================================================================
    # Balance Sheet
    # ========================================================================

    async def get_balance_sheet(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get balance sheet for symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            period: "annual" or "quarter" (default: "annual")
            limit: Number of periods to return (default: 5)

        Returns:
            List of balance sheet records (newest first)

        Raises:
            FMPError: On API error
        """
        logger.info(f"Fetching balance sheet: {symbol} ({period}, limit={limit})")

        endpoint = f"/balance-sheet-statement/{symbol}"
        params = {"period": period, "limit": limit}

        data = await self._request(endpoint, params)

        # FMP returns list of statements
        if not isinstance(data, list):
            raise FMPError(f"Unexpected response format: {type(data)}")

        logger.info(f"Fetched {len(data)} balance sheet periods for {symbol}")
        return data

    # ========================================================================
    # Cash Flow
    # ========================================================================

    async def get_cash_flow(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get cash flow statement for symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            period: "annual" or "quarter" (default: "annual")
            limit: Number of periods to return (default: 5)

        Returns:
            List of cash flow records (newest first)

        Raises:
            FMPError: On API error
        """
        logger.info(f"Fetching cash flow: {symbol} ({period}, limit={limit})")

        endpoint = f"/cash-flow-statement/{symbol}"
        params = {"period": period, "limit": limit}

        data = await self._request(endpoint, params)

        # FMP returns list of statements
        if not isinstance(data, list):
            raise FMPError(f"Unexpected response format: {type(data)}")

        logger.info(f"Fetched {len(data)} cash flow periods for {symbol}")
        return data

    # ========================================================================
    # Financial Ratios
    # ========================================================================

    async def get_ratios(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get financial ratios for symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            period: "annual" or "quarter" (default: "annual")
            limit: Number of periods to return (default: 5)

        Returns:
            List of ratio records (newest first)

        Raises:
            FMPError: On API error
        """
        logger.info(f"Fetching ratios: {symbol} ({period}, limit={limit})")

        endpoint = f"/ratios/{symbol}"
        params = {"period": period, "limit": limit}

        data = await self._request(endpoint, params)

        # FMP returns list of ratio sets
        if not isinstance(data, list):
            raise FMPError(f"Unexpected response format: {type(data)}")

        logger.info(f"Fetched {len(data)} ratio periods for {symbol}")
        return data

    # ========================================================================
    # Company Profile
    # ========================================================================

    async def get_profile(self, symbol: str) -> Dict[str, Any]:
        """
        Get company profile for symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")

        Returns:
            Company profile record

        Raises:
            FMPError: On API error
        """
        logger.info(f"Fetching profile: {symbol}")

        endpoint = f"/profile/{symbol}"

        data = await self._request(endpoint)

        # FMP returns list with single profile
        if not isinstance(data, list) or len(data) == 0:
            raise FMPNotFoundError(f"Profile not found: {symbol}")

        profile = data[0]
        logger.info(f"Fetched profile for {symbol}")
        return profile

    # ========================================================================
    # Batch Queries
    # ========================================================================

    async def get_batch_income_statements(
        self,
        symbols: List[str],
        period: str = "annual",
        limit: int = 5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get income statements for multiple symbols.

        Args:
            symbols: List of stock symbols
            period: "annual" or "quarter" (default: "annual")
            limit: Number of periods to return (default: 5)

        Returns:
            Dict mapping symbol to income statement records
        """
        logger.info(f"Fetching batch income statements: {len(symbols)} symbols")

        results = {}
        for symbol in symbols:
            try:
                data = await self.get_income_statement(symbol, period, limit)
                results[symbol] = data
            except FMPError as e:
                logger.warning(f"Failed to fetch income statement for {symbol}: {e}")
                results[symbol] = []

        return results

    async def get_batch_ratios(
        self,
        symbols: List[str],
        period: str = "annual",
        limit: int = 5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get financial ratios for multiple symbols.

        Args:
            symbols: List of stock symbols
            period: "annual" or "quarter" (default: "annual")
            limit: Number of periods to return (default: 5)

        Returns:
            Dict mapping symbol to ratio records
        """
        logger.info(f"Fetching batch ratios: {len(symbols)} symbols")

        results = {}
        for symbol in symbols:
            try:
                data = await self.get_ratios(symbol, period, limit)
                results[symbol] = data
            except FMPError as e:
                logger.warning(f"Failed to fetch ratios for {symbol}: {e}")
                results[symbol] = []

        return results


# ============================================================================
# Global Instance
# ============================================================================


_fmp_client: Optional[FMPClient] = None


def get_fmp_client(api_key: Optional[str] = None) -> FMPClient:
    """
    Get singleton FMP client instance.

    Args:
        api_key: FMP API key (default: from FMP_API_KEY env var)

    Returns:
        FMPClient instance
    """
    global _fmp_client
    if _fmp_client is None:
        _fmp_client = FMPClient(api_key=api_key)
    return _fmp_client
