"""
FRED Client - Federal Reserve Economic Data API integration

Purpose: Fetch macro indicators from FRED (yield curve, CPI, unemployment)
Updated: 2025-10-23
Priority: P0 (Critical for macro analysis)

Provider: FRED (Federal Reserve Bank of St. Louis)
Rate Limit: 60 requests per minute
Circuit Breaker: 3 failures → OPEN (60s timeout)

Common Series:
    - T10Y2Y: 10-Year minus 2-Year Treasury spread
    - UNRATE: Unemployment rate
    - CPIAUCSL: Consumer Price Index
    - BAA10Y: Moody's Baa Corporate Bond minus 10-Year Treasury
    - DGS10: 10-Year Treasury Constant Maturity Rate
    - DGS2: 2-Year Treasury Constant Maturity Rate

Endpoints:
    - Series Observations: GET /series/observations?series_id={id}
    - Series Info: GET /series?series_id={id}

Usage:
    from backend.app.providers.fred_client import FREDClient

    client = FREDClient(api_key="your_key")

    # Get series observations
    data = await client.get_series_observations(
        "T10Y2Y",
        start_date="2024-01-01",
        end_date="2025-10-23"
    )

Sacred Invariants:
    1. All API calls go through circuit breaker
    2. Rate limiter enforces 60 req/min
    3. Exponential backoff: base=1s, max=60s, jitter=±20%
    4. Data attribution required in reports

References:
    - PRODUCT_SPEC.md §5 (Provider Integration)
    - https://fred.stlouisfed.org/docs/api/fred/
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

logger = logging.getLogger("DawsOS.FREDClient")


# ============================================================================
# Common Series IDs
# ============================================================================

COMMON_SERIES = {
    # Yield Curve
    "T10Y2Y": "10-Year Treasury minus 2-Year Treasury",
    "T10Y3M": "10-Year Treasury minus 3-Month Treasury",
    "DGS10": "10-Year Treasury Constant Maturity Rate",
    "DGS2": "2-Year Treasury Constant Maturity Rate",
    "DGS5": "5-Year Treasury Constant Maturity Rate",
    "DGS30": "30-Year Treasury Constant Maturity Rate",
    "DGS3MO": "3-Month Treasury Bill",

    # Credit Spreads
    "BAA10Y": "Moody's Baa Corporate Bond minus 10-Year Treasury",
    "AAA10Y": "Moody's Aaa Corporate Bond minus 10-Year Treasury",

    # Inflation
    "CPIAUCSL": "Consumer Price Index for All Urban Consumers",
    "CPILFESL": "Consumer Price Index for All Urban Consumers: All Items Less Food and Energy",
    "PCEPI": "Personal Consumption Expenditures: Chain-type Price Index",

    # Labor Market
    "UNRATE": "Unemployment Rate",
    "PAYEMS": "All Employees, Total Nonfarm",
    "CIVPART": "Labor Force Participation Rate",

    # GDP
    "GDP": "Gross Domestic Product",
    "GDPC1": "Real Gross Domestic Product",
}


# ============================================================================
# Exceptions
# ============================================================================


class FREDError(Exception):
    """Base exception for FRED client errors."""
    pass


class FREDRateLimitError(FREDError):
    """Rate limit exceeded."""
    pass


class FREDAuthError(FREDError):
    """Authentication failed."""
    pass


class FREDNotFoundError(FREDError):
    """Resource not found."""
    pass


# ============================================================================
# FRED Client
# ============================================================================


class FREDClient:
    """
    FRED (Federal Reserve Economic Data) API client.

    Provides access to:
    - Macroeconomic time series
    - Series metadata
    - Batch queries
    """

    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize FRED client.

        Args:
            api_key: FRED API key (default: from FRED_API_KEY env var)
            rate_limit: Requests per minute (default: 60)
            max_retries: Max retry attempts (default: 3)
        """
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        if not self.api_key:
            logger.warning("FRED_API_KEY not set, client will fail on API calls")

        self.max_retries = max_retries

        # Circuit breaker (3 failures → OPEN for 60s)
        self.circuit_breaker = get_circuit_breaker(
            name="FRED",
            threshold=int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "3")),
            timeout=float(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60")),
        )

        # Rate limiter (60 req/min)
        self.rate_limiter = get_rate_limiter(
            name="FRED",
            rate=rate_limit,
            per=60.0,
        )

        # HTTP session (created lazily)
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(
            f"FRED client initialized: rate_limit={rate_limit}/min, "
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
            endpoint: API endpoint (e.g., "/series/observations")
            params: Query parameters (default: None)

        Returns:
            Response JSON

        Raises:
            FREDError: On API error
            CircuitBreakerOpenError: If circuit is open
        """
        # Ensure we have API key
        if not self.api_key:
            raise FREDAuthError("FRED_API_KEY not set")

        # Add API key and format to params
        params = params or {}
        params["api_key"] = self.api_key
        params["file_type"] = "json"

        # Build URL
        url = f"{self.BASE_URL}{endpoint}"

        # Acquire rate limit token
        await self.rate_limiter.acquire()

        # Make request through circuit breaker with retries
        async def _make_request():
            session = await self._get_session()

            for attempt in range(self.max_retries):
                try:
                    logger.debug(f"FRED request: {endpoint} (attempt {attempt + 1}/{self.max_retries})")

                    async with session.get(url, params=params) as response:
                        # Parse JSON first to check for FRED API errors
                        data = await response.json()

                        # FRED returns error messages in JSON
                        if "error_code" in data:
                            error_code = data["error_code"]
                            error_message = data.get("error_message", "Unknown error")

                            if error_code == 400:
                                raise FREDAuthError(f"Invalid API key: {error_message}")
                            elif error_code == 404:
                                raise FREDNotFoundError(f"Not found: {error_message}")
                            elif error_code == 429:
                                raise FREDRateLimitError(f"Rate limit exceeded: {error_message}")
                            else:
                                raise FREDError(f"API error {error_code}: {error_message}")

                        # Check HTTP status
                        if response.status == 401 or response.status == 403:
                            raise FREDAuthError("Invalid API key")
                        elif response.status == 429:
                            raise FREDRateLimitError("Rate limit exceeded")
                        elif response.status == 404:
                            raise FREDNotFoundError(f"Not found: {endpoint}")
                        elif response.status >= 500:
                            # Server error, retry
                            if attempt < self.max_retries - 1:
                                wait_time = self._calculate_backoff(attempt)
                                logger.warning(
                                    f"FRED server error {response.status}, "
                                    f"retrying in {wait_time:.2f}s"
                                )
                                await asyncio.sleep(wait_time)
                                continue
                            raise FREDError(f"Server error: {response.status}")
                        elif response.status >= 400:
                            raise FREDError(f"Client error: {response.status}")

                        return data

                except aiohttp.ClientError as e:
                    # Network error, retry
                    if attempt < self.max_retries - 1:
                        wait_time = self._calculate_backoff(attempt)
                        logger.warning(f"FRED network error: {e}, retrying in {wait_time:.2f}s")
                        await asyncio.sleep(wait_time)
                        continue
                    raise FREDError(f"Network error: {e}")

            raise FREDError(f"Max retries ({self.max_retries}) exceeded")

        # Execute through circuit breaker
        try:
            return await self.circuit_breaker.call(_make_request)
        except CircuitBreakerOpenError:
            logger.error("FRED circuit breaker is OPEN")
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
    # Series Observations
    # ========================================================================

    async def get_series_observations(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get observations for a series.

        Args:
            series_id: FRED series ID (e.g., "T10Y2Y", "UNRATE")
            start_date: Start date (YYYY-MM-DD, default: None)
            end_date: End date (YYYY-MM-DD, default: None)
            limit: Max observations (default: None for all)

        Returns:
            List of observation records (dict with keys: date, value, realtime_start, realtime_end)

        Raises:
            FREDError: On API error
        """
        logger.info(
            f"Fetching series observations: {series_id} "
            f"({start_date or 'earliest'} to {end_date or 'latest'})"
        )

        endpoint = "/series/observations"
        params = {"series_id": series_id}

        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date
        if limit:
            params["limit"] = limit

        data = await self._request(endpoint, params)

        # Extract observations
        observations = data.get("observations", [])
        logger.info(f"Fetched {len(observations)} observations for {series_id}")

        return observations

    async def get_latest_observation(
        self,
        series_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get latest observation for a series.

        Args:
            series_id: FRED series ID (e.g., "T10Y2Y", "UNRATE")

        Returns:
            Latest observation or None if not found

        Raises:
            FREDError: On API error
        """
        logger.info(f"Fetching latest observation: {series_id}")

        # Get last observation
        observations = await self.get_series_observations(
            series_id,
            limit=1,
        )

        if not observations:
            logger.warning(f"No observations found for {series_id}")
            return None

        # FRED returns observations sorted by date (newest first with limit=1)
        return observations[-1]

    # ========================================================================
    # Series Info
    # ========================================================================

    async def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """
        Get metadata for a series.

        Args:
            series_id: FRED series ID (e.g., "T10Y2Y", "UNRATE")

        Returns:
            Series metadata (dict with keys: id, title, frequency, units, etc.)

        Raises:
            FREDError: On API error
        """
        logger.info(f"Fetching series info: {series_id}")

        endpoint = "/series"
        params = {"series_id": series_id}

        data = await self._request(endpoint, params)

        # Extract series info
        series_list = data.get("seriess", [])
        if not series_list:
            raise FREDNotFoundError(f"Series not found: {series_id}")

        series_info = series_list[0]
        logger.info(f"Fetched series info for {series_id}: {series_info.get('title')}")

        return series_info

    # ========================================================================
    # Batch Queries
    # ========================================================================

    async def get_batch_series_observations(
        self,
        series_ids: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get observations for multiple series.

        Args:
            series_ids: List of FRED series IDs
            start_date: Start date (YYYY-MM-DD, default: None)
            end_date: End date (YYYY-MM-DD, default: None)

        Returns:
            Dict mapping series_id to list of observations
        """
        logger.info(
            f"Fetching batch series observations: {len(series_ids)} series "
            f"({start_date or 'earliest'} to {end_date or 'latest'})"
        )

        results = {}
        for series_id in series_ids:
            try:
                observations = await self.get_series_observations(
                    series_id,
                    start_date,
                    end_date,
                )
                results[series_id] = observations
            except FREDError as e:
                logger.warning(f"Failed to fetch observations for {series_id}: {e}")
                results[series_id] = []

        return results

    async def get_batch_latest_observations(
        self,
        series_ids: List[str],
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get latest observations for multiple series.

        Args:
            series_ids: List of FRED series IDs

        Returns:
            Dict mapping series_id to latest observation (or None if not found)
        """
        logger.info(f"Fetching batch latest observations: {len(series_ids)} series")

        results = {}
        for series_id in series_ids:
            try:
                observation = await self.get_latest_observation(series_id)
                results[series_id] = observation
            except FREDError as e:
                logger.warning(f"Failed to fetch latest observation for {series_id}: {e}")
                results[series_id] = None

        return results


# ============================================================================
# Global Instance
# ============================================================================


_fred_client: Optional[FREDClient] = None


def get_fred_client(api_key: Optional[str] = None) -> FREDClient:
    """
    Get singleton FRED client instance.

    Args:
        api_key: FRED API key (default: from FRED_API_KEY env var)

    Returns:
        FREDClient instance
    """
    global _fred_client
    if _fred_client is None:
        _fred_client = FREDClient(api_key=api_key)
    return _fred_client
