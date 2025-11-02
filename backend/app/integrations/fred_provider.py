"""
FRED (Federal Reserve Economic Data) Provider Facade

Purpose: Fetch macro economic indicators from Federal Reserve Bank of St. Louis
Updated: 2025-10-21
Priority: P0 (Critical for macro regime detection and factor analysis)

Features:
    - Economic time series data (GDP, CPI, unemployment, yields, spreads)
    - Rate limiting: 60 req/min (token bucket)
    - Smart retry logic with exponential backoff (1s, 2s, 4s)
    - Dead Letter Queue for failed requests
    - Rights: Allowed export, free attribution

Series IDs (for factor analysis and regime detection):
    - T10Y2Y: 10Y-2Y Treasury yield spread (curve steepness)
    - CPIAUCSL: Consumer Price Index (inflation)
    - UNRATE: Unemployment rate
    - BAA10Y: BAA corporate - 10Y Treasury spread (credit risk)
    - DFII10: 10Y TIPS yield (real rate)
    - T10YIE: 10Y breakeven inflation
    - BAMLC0A0CM: ICE BofA AAA Corporate spread
    - DTWEXBGS: Trade-weighted USD index (DXY)

Endpoints:
    - /series/observations

Usage:
    provider = FREDProvider(api_key=settings.FRED_API_KEY)
    cpi = await provider.get_series("CPIAUCSL", start_date, end_date)
"""

import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from .base_provider import BaseProvider, ProviderConfig, ProviderError
from .rate_limiter import rate_limit

logger = logging.getLogger(__name__)


class FREDProvider(BaseProvider):
    """
    FRED provider facade with rate limiting and circuit breaker.
    """

    # Common economic series IDs
    SERIES_IDS = {
        # Yield curve
        "T10Y2Y": "10Y-2Y Treasury spread",
        "T10Y3M": "10Y-3M Treasury spread",
        "DGS10": "10Y Treasury constant maturity",
        "DGS2": "2Y Treasury constant maturity",

        # Inflation
        "CPIAUCSL": "Consumer Price Index",
        "PCEPI": "PCE Price Index",
        "T10YIE": "10Y breakeven inflation",
        "T5YIE": "5Y breakeven inflation",

        # Real rates
        "DFII10": "10Y TIPS yield",
        "DFII5": "5Y TIPS yield",

        # Labor
        "UNRATE": "Unemployment rate",
        "PAYEMS": "Nonfarm payrolls",
        "U6RATE": "U6 underemployment rate",

        # Credit spreads
        "BAA10Y": "BAA corporate - 10Y Treasury",
        "BAMLC0A0CM": "ICE BofA AAA Corporate OAS",
        "BAMLH0A0HYM2": "ICE BofA High Yield OAS",

        # Growth
        "GDP": "Gross Domestic Product",
        "GDPC1": "Real GDP",
        "GDPPOT": "Potential GDP",

        # Currency
        "DTWEXBGS": "Trade-weighted USD (broad)",
        "DEXCAUS": "CAD/USD exchange rate",

        # Housing
        "CSUSHPISA": "Case-Shiller Home Price Index",
        "MORTGAGE30US": "30Y mortgage rate",

        # Manufacturing
        "INDPRO": "Industrial Production Index",
        "ISM": "ISM Manufacturing PMI",
    }

    def __init__(self, api_key: str, base_url: str = "https://api.stlouisfed.org/fred"):
        """
        Initialize FRED provider.

        Args:
            api_key: FRED API key (free from https://fred.stlouisfed.org/docs/api/api_key.html)
            base_url: FRED base URL (default: https://api.stlouisfed.org/fred)
        """
        config = ProviderConfig(
            name="FRED",
            base_url=base_url,
            rate_limit_rpm=60,  # 60 requests per minute (conservative)
            max_retries=3,
            retry_base_delay=1.0,
            rights={
                "export_pdf": True,  # Allowed (public data)
                "export_csv": True,  # Allowed
                "redistribution": True,  # Allowed with attribution
                "requires_attribution": True,
                "attribution_text": "Source: Federal Reserve Economic Data (FRED®), Federal Reserve Bank of St. Louis",
            },
        )

        super().__init__(config)
        self.api_key = api_key

    async def call(self, request) -> Any:
        """
        Generic call method required by BaseProvider.
        
        Routes to appropriate FRED endpoint based on request.
        """
        import httpx
        import time
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=request.timeout if hasattr(request, 'timeout') else 10.0) as client:
            response = await client.get(
                request.endpoint,
                params=request.params if hasattr(request, 'params') else {}
            )
            response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            
            from app.integrations.base_provider import ProviderResponse
            return ProviderResponse(
                data=response.json(),
                provider=self.config.name,
                endpoint=request.endpoint,
                status_code=response.status_code,
                latency_ms=latency_ms,
                cached=False,
                stale=False
            )
    
    async def _request(self, method: str, url: str, params: dict = None) -> dict:
        """Internal helper for making HTTP requests."""
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method, url, params=params)
            response.raise_for_status()
            return response.json()

    @rate_limit(requests_per_minute=60)
    async def get_series(
        self,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        frequency: Optional[str] = None,
        aggregation_method: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get economic time series observations.

        Args:
            series_id: FRED series ID (e.g., "CPIAUCSL", "T10Y2Y")
            start_date: Start date (optional, defaults to series start)
            end_date: End date (optional, defaults to today)
            frequency: Frequency (optional: "d", "w", "bw", "m", "q", "sa", "a")
            aggregation_method: Aggregation (optional: "avg", "sum", "eop")

        Returns:
            [
                {
                    "date": "2024-01-01",
                    "value": 306.746,
                    "series_id": "CPIAUCSL"
                },
                ...
            ]

        Raises:
            ProviderError: If API call fails or series not found

        Note:
            - FRED returns observations in ascending date order
            - Some series have daily data, others monthly/quarterly
            - Missing values represented as "." in FRED response (filtered out)
        """
        url = f"{self.config.base_url}/series/observations"
        params = {
            "api_key": self.api_key,
            "file_type": "json",
            "series_id": series_id,
        }

        if start_date:
            params["observation_start"] = start_date.isoformat()
        if end_date:
            params["observation_end"] = end_date.isoformat()
        if frequency:
            params["frequency"] = frequency
        if aggregation_method:
            params["aggregation_method"] = aggregation_method

        response = await self._request("GET", url, params=params)

        # Check for errors
        if "error_code" in response:
            raise ProviderError(f"FRED API error: {response.get('error_message', 'Unknown error')}")

        observations = response.get("observations", [])

        # Normalize and filter out missing values
        series_data = []
        for obs in observations:
            # FRED uses "." for missing values
            if obs["value"] == ".":
                continue

            try:
                series_data.append({
                    "date": obs["date"],
                    "value": float(obs["value"]),
                    "series_id": series_id,
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid value for {series_id} on {obs['date']}: {obs['value']}")
                continue

        return series_data

    @rate_limit(requests_per_minute=60)
    async def get_series_info(self, series_id: str) -> Dict:
        """
        Get series metadata.

        Args:
            series_id: FRED series ID

        Returns:
            {
                "id": "CPIAUCSL",
                "title": "Consumer Price Index for All Urban Consumers: All Items in U.S. City Average",
                "observation_start": "1947-01-01",
                "observation_end": "2024-01-01",
                "frequency": "Monthly",
                "frequency_short": "M",
                "units": "Index 1982-1984=100",
                "seasonal_adjustment": "Seasonally Adjusted",
                "last_updated": "2024-02-13 07:44:03-06",
                "popularity": 95,
                "notes": "The Consumer Price Index for All Urban Consumers..."
            }
        """
        url = f"{self.config.base_url}/series"
        params = {
            "api_key": self.api_key,
            "file_type": "json",
            "series_id": series_id,
        }

        response = await self._request("GET", url, params=params)

        if "error_code" in response:
            raise ProviderError(f"FRED API error: {response.get('error_message', 'Unknown error')}")

        series_list = response.get("series", [])
        if not series_list:
            raise ProviderError(f"Series not found: {series_id}")

        return series_list[0]

    async def get_multiple_series(
        self,
        series_ids: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, List[Dict]]:
        """
        Get multiple series in parallel (efficient bulk fetch).

        Args:
            series_ids: List of FRED series IDs
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            {
                "CPIAUCSL": [{"date": "2024-01-01", "value": 306.746}, ...],
                "UNRATE": [{"date": "2024-01-01", "value": 3.7}, ...],
                ...
            }

        Note:
            - Fetches series sequentially to respect rate limit
            - For production, consider implementing request batching
        """
        results = {}

        for series_id in series_ids:
            try:
                series_data = await self.get_series(series_id, start_date, end_date)
                results[series_id] = series_data
            except ProviderError as e:
                logger.error(f"Failed to fetch {series_id}: {e}")
                results[series_id] = []

        return results

    async def get_factor_data(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get all factor series needed for factor analysis.

        Fetches:
            - Real rate (DFII10)
            - Inflation (T10YIE)
            - Credit spread (BAMLC0A0CM)
            - USD index (DTWEXBGS)
            - Risk-free rate (DGS10)

        Args:
            start_date: Start date (default: 1 year ago)
            end_date: End date (default: today)

        Returns:
            {
                "real_rate": [{"date": "2024-01-01", "value": 2.1}, ...],
                "inflation": [...],
                "credit": [...],
                "usd": [...],
                "risk_free": [...]
            }
        """
        if not start_date:
            start_date = date.today() - timedelta(days=365)
        if not end_date:
            end_date = date.today()

        factor_series = {
            "real_rate": "DFII10",
            "inflation": "T10YIE",
            "credit": "BAMLC0A0CM",
            "usd": "DTWEXBGS",
            "risk_free": "DGS10",
        }

        results = {}
        for factor_name, series_id in factor_series.items():
            try:
                series_data = await self.get_series(series_id, start_date, end_date)
                results[factor_name] = series_data
            except ProviderError as e:
                logger.error(f"Failed to fetch {factor_name} ({series_id}): {e}")
                results[factor_name] = []

        return results

    async def get_regime_indicators(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get all series needed for macro regime detection.

        Fetches:
            - Yield curve (T10Y2Y)
            - CPI (CPIAUCSL)
            - Unemployment (UNRATE)
            - Credit spread (BAA10Y)

        Args:
            start_date: Start date (default: 1 year ago)
            end_date: End date (default: today)

        Returns:
            {
                "curve": [{"date": "2024-01-01", "value": 0.45}, ...],
                "cpi": [...],
                "unemployment": [...],
                "credit_spread": [...]
            }
        """
        if not start_date:
            start_date = date.today() - timedelta(days=365)
        if not end_date:
            end_date = date.today()

        regime_series = {
            "curve": "T10Y2Y",
            "cpi": "CPIAUCSL",
            "unemployment": "UNRATE",
            "credit_spread": "BAA10Y",
        }

        results = {}
        for indicator_name, series_id in regime_series.items():
            try:
                series_data = await self.get_series(series_id, start_date, end_date)
                results[indicator_name] = series_data
            except ProviderError as e:
                logger.error(f"Failed to fetch {indicator_name} ({series_id}): {e}")
                results[indicator_name] = []

        return results
