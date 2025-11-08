"""
Polygon.io Provider Facade

Purpose: Fetch prices, splits, dividends for corporate actions
Updated: 2025-10-21
Priority: P0 (Critical for pricing pack builder)

Features:
    - Historical OHLCV prices (daily aggregates)
    - Stock splits with ex-date
    - Dividends with ex-date and pay-date (CRITICAL for ADR accuracy)
    - Rate limiting: 100 req/min (token bucket)
    - Smart retry logic with exponential backoff (1s, 2s, 4s)
    - Dead Letter Queue for failed requests
    - Rights: Restricted export, requires attribution

Endpoints:
    - /v2/aggs/ticker/{symbol}/range/1/day/{from}/{to}
    - /v3/reference/splits
    - /v3/reference/dividends

Usage:
    provider = PolygonProvider(api_key=settings.POLYGON_API_KEY)
    prices = await provider.get_daily_prices("AAPL", start_date, end_date)
    dividends = await provider.get_dividends("AAPL")
"""

import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from .base_provider import BaseProvider, ProviderConfig, ProviderError
from .rate_limiter import rate_limit
from app.core.constants.integration import (
    POLYGON_RATE_LIMIT_REQUESTS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY,
)

logger = logging.getLogger(__name__)


class PolygonProvider(BaseProvider):
    """
    Polygon.io provider facade with rate limiting and circuit breaker.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.polygon.io"):
        """
        Initialize Polygon provider.

        Args:
            api_key: Polygon API key
            base_url: Polygon base URL (default: https://api.polygon.io)
        """
        config = ProviderConfig(
            name="Polygon",
            base_url=base_url,
            rate_limit_rpm=POLYGON_RATE_LIMIT_REQUESTS,  # From Polygon API documentation
            max_retries=DEFAULT_MAX_RETRIES,
            retry_base_delay=DEFAULT_RETRY_DELAY,
            rights={
                "export_pdf": False,  # Restricted
                "export_csv": False,  # Restricted
                "redistribution": False,
                "requires_attribution": True,
                "attribution_text": "Market data © Polygon.io",
            },
        )

        super().__init__(config)
        self.api_key = api_key
        
    async def call(self, request) -> Any:
        """
        Generic call method required by BaseProvider.
        
        Routes to appropriate Polygon endpoint based on request.
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

    @rate_limit(requests_per_minute=100)
    async def get_daily_prices(
        self, symbol: str, start_date: date, end_date: date, adjusted: bool = True
    ) -> List[Dict]:
        """
        Get daily OHLCV prices.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            start_date: Start date
            end_date: End date
            adjusted: If True, adjust for splits (not dividends)

        Returns:
            [
                {
                    "date": "2024-01-02",
                    "open": 187.15,
                    "high": 188.44,
                    "low": 183.89,
                    "close": 185.64,
                    "volume": 82488600,
                    "vwap": 185.92,
                    "transactions": 748523
                },
                ...
            ]

        Raises:
            ProviderError: If API call fails

        Note:
            - Polygon adjusts for splits but NOT dividends (split-adjusted only)
            - For total return, must compute dividend adjustments separately
        """
        url = f"{self.config.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
        params = {
            "apiKey": self.api_key,
            "adjusted": "true" if adjusted else "false",
            "sort": "asc",
            "limit": 50000,
        }

        response = await self._request("GET", url, params=params)

        # Parse response
        if response.get("status") != "OK":
            raise ProviderError(f"Polygon API error: {response.get('error', 'Unknown error')}")

        results = response.get("results", [])

        # Convert timestamp to date
        prices = []
        for bar in results:
            prices.append({
                "date": datetime.fromtimestamp(bar["t"] / 1000).date().isoformat(),
                "open": bar["o"],
                "high": bar["h"],
                "low": bar["l"],
                "close": bar["c"],
                "volume": bar["v"],
                "vwap": bar.get("vw"),
                "transactions": bar.get("n"),
            })

        return prices

    # NOTE: Corporate actions methods (get_splits, get_dividends) were removed
    # in favor of FMP Premium as the primary source. FMP provides:
    # - Dividends, splits, AND earnings (Polygon lacks earnings)
    # - Already implemented and tested in DataHarvester agent
    # - No quality issues reported
    # If you need corporate actions data, use FMP via DataHarvester:
    #   - corporate_actions.dividends
    #   - corporate_actions.splits
    #   - corporate_actions.earnings
    # See: PROVIDER_API_AUDIT.md for full analysis

    @rate_limit(requests_per_minute=100)
    async def get_last_quote(self, symbol: str) -> Dict:
        """
        Get most recent quote for symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            {
                "ticker": "AAPL",
                "bid": 175.40,
                "bid_size": 100,
                "ask": 175.43,
                "ask_size": 200,
                "last_trade_price": 175.42,
                "last_trade_size": 50,
                "last_trade_time": "2024-01-15T20:59:59.999Z",
                "exchange": "NASDAQ"
            }
        """
        url = f"{self.config.base_url}/v2/last/nbbo/{symbol}"
        params = {"apiKey": self.api_key}

        response = await self._request("GET", url, params=params)

        if response.get("status") != "OK":
            raise ProviderError(f"Polygon quote error: {response.get('error', 'Unknown error')}")

        result = response.get("results", {})

        return {
            "ticker": symbol,
            "bid": result.get("P"),  # Bid price
            "bid_size": result.get("S"),  # Bid size
            "ask": result.get("p"),  # Ask price
            "ask_size": result.get("s"),  # Ask size
            "last_trade_price": result.get("p"),  # Last trade price
            "last_trade_size": result.get("s"),  # Last trade size
            "last_trade_time": result.get("t"),  # Last trade timestamp
            "exchange": result.get("x"),  # Exchange
        }

    async def get_snapshot(self, symbols: List[str]) -> List[Dict]:
        """
        Get snapshot for multiple symbols (bulk endpoint).

        Args:
            symbols: List of stock ticker symbols

        Returns:
            [
                {
                    "ticker": "AAPL",
                    "day": {
                        "open": 174.20,
                        "high": 176.20,
                        "low": 173.50,
                        "close": 175.43,
                        "volume": 52000000,
                        "vwap": 174.85
                    },
                    "prev_day": {
                        "close": 173.26,
                        "volume": 48000000
                    },
                    "min": {  # Latest minute bar
                        "close": 175.43,
                        "volume": 12000
                    },
                    "updated": 1698345600000
                },
                ...
            ]
        """
        # Polygon supports bulk snapshots via /v2/snapshot/locale/us/markets/stocks/tickers
        url = f"{self.config.base_url}/v2/snapshot/locale/us/markets/stocks/tickers"
        params = {"apiKey": self.api_key, "tickers": ",".join(symbols)}

        response = await self._request("GET", url, params=params)

        if response.get("status") != "OK":
            raise ProviderError(f"Polygon snapshot error: {response.get('error', 'Unknown error')}")

        return response.get("tickers", [])

    # _request() method inherited from BaseProvider
