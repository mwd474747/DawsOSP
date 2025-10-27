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
    - Circuit breaker: 3 failures → OPEN for 60s
    - Dead Letter Queue with exponential backoff
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
            rate_limit_rpm=100,  # 100 requests per minute
            circuit_breaker_threshold=3,
            circuit_breaker_timeout=60,
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

    @rate_limit(requests_per_minute=100)
    async def get_splits(
        self, symbol: Optional[str] = None, execution_date: Optional[date] = None, limit: int = 1000
    ) -> List[Dict]:
        """
        Get stock splits.

        Args:
            symbol: Stock ticker symbol (optional, returns all if None)
            execution_date: Filter by execution date (optional)
            limit: Max results (default 1000)

        Returns:
            [
                {
                    "ticker": "AAPL",
                    "execution_date": "2020-08-31",
                    "split_from": 1,
                    "split_to": 4,
                    "split_ratio": 0.25
                },
                ...
            ]

        Note:
            - execution_date is when split takes effect (same as ex-date)
            - split_ratio = split_from / split_to (e.g., 4:1 split = 0.25)
            - Adjust share quantities: new_qty = old_qty / split_ratio
            - Adjust prices: new_price = old_price * split_ratio
        """
        url = f"{self.config.base_url}/v3/reference/splits"
        params = {"apiKey": self.api_key, "limit": limit}

        if symbol:
            params["ticker"] = symbol
        if execution_date:
            params["execution_date"] = execution_date.isoformat()

        response = await self._request("GET", url, params=params)

        if response.get("status") != "OK":
            raise ProviderError(f"Polygon splits error: {response.get('error', 'Unknown error')}")

        results = response.get("results", [])

        # Normalize response
        splits = []
        for split in results:
            splits.append({
                "ticker": split["ticker"],
                "execution_date": split["execution_date"],
                "split_from": split["split_from"],
                "split_to": split["split_to"],
                "split_ratio": split["split_from"] / split["split_to"],
            })

        return splits

    @rate_limit(requests_per_minute=100)
    async def get_dividends(
        self,
        symbol: Optional[str] = None,
        ex_dividend_date: Optional[date] = None,
        declaration_date: Optional[date] = None,
        limit: int = 1000,
    ) -> List[Dict]:
        """
        Get dividends with ex-date and pay-date (CRITICAL for ADR accuracy).

        Args:
            symbol: Stock ticker symbol (optional, returns all if None)
            ex_dividend_date: Filter by ex-dividend date (optional)
            declaration_date: Filter by declaration date (optional)
            limit: Max results (default 1000)

        Returns:
            [
                {
                    "ticker": "AAPL",
                    "ex_dividend_date": "2024-08-09",
                    "pay_date": "2024-08-15",  # CRITICAL: Use this for FX conversion
                    "declaration_date": "2024-08-01",
                    "record_date": "2024-08-12",
                    "cash_amount": 0.24,
                    "currency": "USD",
                    "dividend_type": "CD",  # Cash Dividend
                    "frequency": 4  # Quarterly
                },
                ...
            ]

        Note:
            - CRITICAL: For ADR dividends, use pay_date FX rate, not ex_date FX
            - This prevents 42¢ per transaction accuracy errors
            - ex_dividend_date: Stock trades without dividend after this date
            - pay_date: When dividend is actually paid (use this FX rate)
            - record_date: Shareholder must own shares by this date
        """
        url = f"{self.config.base_url}/v3/reference/dividends"
        params = {"apiKey": self.api_key, "limit": limit}

        if symbol:
            params["ticker"] = symbol
        if ex_dividend_date:
            params["ex_dividend_date"] = ex_dividend_date.isoformat()
        if declaration_date:
            params["declaration_date"] = declaration_date.isoformat()

        response = await self._request("GET", url, params=params)

        if response.get("status") != "OK":
            raise ProviderError(f"Polygon dividends error: {response.get('error', 'Unknown error')}")

        results = response.get("results", [])

        # Normalize response
        dividends = []
        for div in results:
            dividends.append({
                "ticker": div["ticker"],
                "ex_dividend_date": div["ex_dividend_date"],
                "pay_date": div["pay_date"],  # CRITICAL for ADR FX accuracy
                "declaration_date": div.get("declaration_date"),
                "record_date": div.get("record_date"),
                "cash_amount": div["cash_amount"],
                "currency": div.get("currency", "USD"),
                "dividend_type": div.get("dividend_type", "CD"),
                "frequency": div.get("frequency", 4),
            })

        return dividends

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
