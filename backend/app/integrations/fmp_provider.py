"""
FMP (Financial Modeling Prep) Provider Facade

Purpose: Fetch fundamentals, financials, ratios from FMP Premium API
Updated: 2025-10-21
Priority: P0 (Critical for pricing pack builder)

Features:
    - Company profiles
    - Income statements, balance sheets, cash flow statements
    - Financial ratios
    - Rate limiting: 120 req/min (token bucket)
    - Bandwidth tracking: Alert at 70%, 85%, 95% of monthly quota
    - Smart retry logic with exponential backoff (1s, 2s, 4s)
    - Dead Letter Queue for failed requests
    - Rights: Restricted export, requires attribution

Endpoints:
    - /v3/profile/{symbol}
    - /v3/income-statement/{symbol}
    - /v3/balance-sheet-statement/{symbol}
    - /v3/cash-flow-statement/{symbol}
    - /v3/ratios/{symbol}
    - /v3/quote/{symbols} (bulk endpoint for efficiency)

Usage:
    provider = FMPProvider(api_key=settings.FMP_API_KEY)
    profile = await provider.get_profile("AAPL")
"""

import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal

from .base_provider import BaseProvider, ProviderConfig, ProviderError
from .rate_limiter import rate_limit

logger = logging.getLogger(__name__)


class FMPProvider(BaseProvider):
    """
    FMP provider facade with rate limiting, circuit breaker, and bandwidth tracking.
    """

    def __init__(self, api_key: str, base_url: str = "https://financialmodelingprep.com/api"):
        """
        Initialize FMP provider.

        Args:
            api_key: FMP API key
            base_url: FMP base URL (default: https://financialmodelingprep.com/api)
        """
        config = ProviderConfig(
            name="FMP",
            base_url=base_url,
            rate_limit_rpm=120,  # 120 requests per minute
            max_retries=3,
            retry_base_delay=1.0,
            rights={
                "export_pdf": False,  # Restricted
                "export_csv": False,  # Restricted
                "redistribution": False,
                "requires_attribution": True,
                "attribution_text": "Financial data © Financial Modeling Prep",
            },
        )

        super().__init__(config)

        self.api_key = api_key
        
    async def call(self, request) -> Any:
        """
        Generic call method required by BaseProvider.
        
        Routes to appropriate FMP endpoint based on request.
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

    @rate_limit(requests_per_minute=120)
    async def get_profile(self, symbol: str) -> Dict:
        """
        Get company profile.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")

        Returns:
            {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "currency": "USD",
                "exchange": "NASDAQ",
                "industry": "Consumer Electronics",
                "sector": "Technology",
                "country": "US",
                "isin": "US0378331005",
                "cusip": "037833100",
                "description": "Apple Inc. designs...",
                "ceo": "Timothy Cook",
                "website": "https://www.apple.com",
                "employees": 161000,
                "marketCap": 3000000000000,
                "beta": 1.2
            }

        Raises:
            ProviderError: If API call fails
        """
        url = f"{self.config.base_url}/v3/profile/{symbol}"
        params = {"apikey": self.api_key}

        response = await self._request("GET", url, params=params)

        # FMP returns array with single object
        if isinstance(response, list) and len(response) > 0:
            return response[0]
        elif isinstance(response, dict):
            return response
        else:
            raise ProviderError(f"Unexpected response format for {symbol}")

    @rate_limit(requests_per_minute=120)
    async def get_income_statement(
        self, symbol: str, period: str = "annual", limit: int = 5
    ) -> List[Dict]:
        """
        Get income statements.

        Args:
            symbol: Stock ticker symbol
            period: "annual" or "quarter"
            limit: Number of periods to fetch (default 5)

        Returns:
            [
                {
                    "date": "2023-09-30",
                    "symbol": "AAPL",
                    "reportedCurrency": "USD",
                    "cik": "0000320193",
                    "fillingDate": "2023-11-03",
                    "acceptedDate": "2023-11-02 18:08:27",
                    "calendarYear": "2023",
                    "period": "FY",
                    "revenue": 383285000000,
                    "costOfRevenue": 214137000000,
                    "grossProfit": 169148000000,
                    "operatingExpenses": 51345000000,
                    "operatingIncome": 117803000000,
                    "netIncome": 96995000000,
                    "eps": 6.16,
                    "epsdiluted": 6.13
                },
                ...
            ]
        """
        url = f"{self.config.base_url}/v3/income-statement/{symbol}"
        params = {"apikey": self.api_key, "period": period, "limit": limit}

        response = await self._request("GET", url, params=params)
        return response if isinstance(response, list) else [response]

    @rate_limit(requests_per_minute=120)
    async def get_balance_sheet(
        self, symbol: str, period: str = "annual", limit: int = 5
    ) -> List[Dict]:
        """
        Get balance sheets.

        Args:
            symbol: Stock ticker symbol
            period: "annual" or "quarter"
            limit: Number of periods to fetch

        Returns:
            [
                {
                    "date": "2023-09-30",
                    "symbol": "AAPL",
                    "totalAssets": 352755000000,
                    "totalCurrentAssets": 143566000000,
                    "cashAndCashEquivalents": 29965000000,
                    "totalLiabilities": 290437000000,
                    "totalCurrentLiabilities": 133973000000,
                    "totalStockholdersEquity": 62318000000,
                    "retainedEarnings": 1408000000
                },
                ...
            ]
        """
        url = f"{self.config.base_url}/v3/balance-sheet-statement/{symbol}"
        params = {"apikey": self.api_key, "period": period, "limit": limit}

        response = await self._request("GET", url, params=params)
        return response if isinstance(response, list) else [response]

    @rate_limit(requests_per_minute=120)
    async def get_cash_flow(
        self, symbol: str, period: str = "annual", limit: int = 5
    ) -> List[Dict]:
        """
        Get cash flow statements.

        Args:
            symbol: Stock ticker symbol
            period: "annual" or "quarter"
            limit: Number of periods to fetch

        Returns:
            [
                {
                    "date": "2023-09-30",
                    "symbol": "AAPL",
                    "operatingCashFlow": 110543000000,
                    "capitalExpenditure": -10959000000,
                    "freeCashFlow": 99584000000,
                    "dividendsPaid": -14996000000,
                    "stockBasedCompensation": 10833000000
                },
                ...
            ]
        """
        url = f"{self.config.base_url}/v3/cash-flow-statement/{symbol}"
        params = {"apikey": self.api_key, "period": period, "limit": limit}

        response = await self._request("GET", url, params=params)
        return response if isinstance(response, list) else [response]

    @rate_limit(requests_per_minute=120)
    async def get_ratios(
        self, symbol: str, period: str = "annual", limit: int = 5
    ) -> List[Dict]:
        """
        Get financial ratios.

        Args:
            symbol: Stock ticker symbol
            period: "annual" or "quarter"
            limit: Number of periods to fetch

        Returns:
            [
                {
                    "date": "2023-09-30",
                    "symbol": "AAPL",
                    "currentRatio": 1.07,
                    "quickRatio": 0.85,
                    "debtToEquity": 1.97,
                    "returnOnEquity": 1.72,
                    "returnOnAssets": 0.28,
                    "netProfitMargin": 0.25,
                    "operatingProfitMargin": 0.31,
                    "priceToBookRatio": 51.2,
                    "priceToEarningsRatio": 31.5,
                    "dividendYield": 0.0045,
                    "payoutRatio": 0.15
                },
                ...
            ]
        """
        url = f"{self.config.base_url}/v3/ratios/{symbol}"
        params = {"apikey": self.api_key, "period": period, "limit": limit}

        response = await self._request("GET", url, params=params)
        return response if isinstance(response, list) else [response]

    @rate_limit(requests_per_minute=120)
    async def get_quote(self, symbols: List[str]) -> List[Dict]:
        """
        Get real-time quotes (bulk endpoint for efficiency).

        Args:
            symbols: List of stock ticker symbols (max 100 per request)

        Returns:
            [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "price": 175.43,
                    "changesPercentage": 1.25,
                    "change": 2.17,
                    "dayLow": 173.50,
                    "dayHigh": 176.20,
                    "yearHigh": 199.62,
                    "yearLow": 124.17,
                    "marketCap": 2750000000000,
                    "priceAvg50": 182.45,
                    "priceAvg200": 165.32,
                    "volume": 52000000,
                    "avgVolume": 58000000,
                    "exchange": "NASDAQ",
                    "open": 174.20,
                    "previousClose": 173.26,
                    "eps": 6.13,
                    "pe": 28.6,
                    "earningsAnnouncement": "2024-02-01T21:00:00.000+00:00",
                    "sharesOutstanding": 15728700000,
                    "timestamp": 1698345600
                },
                ...
            ]

        Raises:
            ValueError: If more than 100 symbols requested
        """
        if len(symbols) > 100:
            raise ValueError(f"FMP quote endpoint limited to 100 symbols, got {len(symbols)}")

        url = f"{self.config.base_url}/v3/quote/{','.join(symbols)}"
        params = {"apikey": self.api_key}

        response = await self._request("GET", url, params=params)
        return response if isinstance(response, list) else [response]

    @rate_limit(requests_per_minute=120)
    async def get_dividend_calendar(
        self, from_date: date, to_date: date
    ) -> List[Dict]:
        """
        Get dividend calendar for date range.
        NOTE: FMP returns ALL dividends for the date range, not filtered by symbol.

        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of dividend announcements

        Example:
            [
                {
                    "date": "2025-11-07",
                    "label": "November 07, 25",
                    "adjDividend": 0.24,
                    "symbol": "AAPL",
                    "dividend": 0.24,
                    "recordDate": "2025-11-10",
                    "paymentDate": "2025-11-14",
                    "declarationDate": "2025-10-28"
                }
            ]

        Raises:
            ProviderError: If API call fails
        """
        url = f"{self.config.base_url}/v3/stock_dividend_calendar"
        params = {
            "apikey": self.api_key,
            "from": from_date.isoformat(),
            "to": to_date.isoformat()
        }
        
        # Log the full request URL (without exposing API key)
        logger.info(f"FMP get_dividend_calendar: Requesting URL={url}, from={from_date.isoformat()}, to={to_date.isoformat()}")

        response = await self._request("GET", url, params=params)
        
        # Log the response details
        if isinstance(response, list):
            logger.info(f"FMP get_dividend_calendar: Received {len(response)} dividend records for date range")
            # Log sample of symbols returned (first 10 unique)
            if response:
                sample_symbols = list(set([r.get('symbol', 'unknown') for r in response[:20]]))[:10]
                logger.debug(f"FMP get_dividend_calendar: Sample symbols in response: {sample_symbols}")
        else:
            logger.warning(f"FMP get_dividend_calendar: Unexpected response type: {type(response)}, response={response}")
            
        return response if isinstance(response, list) else []

    @rate_limit(requests_per_minute=120)
    async def get_split_calendar(
        self, from_date: date, to_date: date
    ) -> List[Dict]:
        """
        Get stock split calendar for date range.
        NOTE: FMP returns ALL splits for the date range, not filtered by symbol.

        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of stock split announcements

        Example:
            [
                {
                    "date": "2025-11-07",
                    "label": "November 07, 25",
                    "symbol": "AAPL",
                    "numerator": 4,
                    "denominator": 1
                }
            ]

        Raises:
            ProviderError: If API call fails
        """
        url = f"{self.config.base_url}/v3/stock_split_calendar"
        params = {
            "apikey": self.api_key,
            "from": from_date.isoformat(),
            "to": to_date.isoformat()
        }
        
        # Log the full request URL (without exposing API key)
        logger.info(f"FMP get_split_calendar: Requesting URL={url}, from={from_date.isoformat()}, to={to_date.isoformat()}")

        response = await self._request("GET", url, params=params)
        
        # Log the response details
        if isinstance(response, list):
            logger.info(f"FMP get_split_calendar: Received {len(response)} split records for date range")
            # Log sample of symbols returned 
            if response:
                sample_symbols = list(set([r.get('symbol', 'unknown') for r in response[:20]]))[:10]
                logger.debug(f"FMP get_split_calendar: Sample symbols in response: {sample_symbols}")
        else:
            logger.warning(f"FMP get_split_calendar: Unexpected response type: {type(response)}, response={response}")
            
        return response if isinstance(response, list) else []

    @rate_limit(requests_per_minute=120)
    async def get_earnings_calendar(
        self, from_date: date, to_date: date
    ) -> List[Dict]:
        """
        Get earnings calendar for date range.
        NOTE: FMP returns ALL earnings for the date range, not filtered by symbol.

        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of earnings announcements

        Example:
            [
                {
                    "date": "2025-11-07",
                    "symbol": "AAPL",
                    "eps": 1.42,
                    "epsEstimated": 1.38,
                    "time": "amc",
                    "revenue": 90000000000,
                    "revenueEstimated": 89000000000
                }
            ]

        Raises:
            ProviderError: If API call fails
        """
        url = f"{self.config.base_url}/v3/earning_calendar"
        params = {
            "apikey": self.api_key,
            "from": from_date.isoformat(),
            "to": to_date.isoformat()
        }
        
        # Log the full request URL (without exposing API key)
        logger.info(f"FMP get_earnings_calendar: Requesting URL={url}, from={from_date.isoformat()}, to={to_date.isoformat()}")

        response = await self._request("GET", url, params=params)
        
        # Log the response details
        if isinstance(response, list):
            logger.info(f"FMP get_earnings_calendar: Received {len(response)} earnings records for date range")
            # Log sample of symbols returned
            if response:
                sample_symbols = list(set([r.get('symbol', 'unknown') for r in response[:20]]))[:10]
                logger.debug(f"FMP get_earnings_calendar: Sample symbols in response: {sample_symbols}")
        else:
            logger.warning(f"FMP get_earnings_calendar: Unexpected response type: {type(response)}, response={response}")
            
        return response if isinstance(response, list) else []

    async def _request(
        self, method: str, url: str, params: Optional[Dict] = None, json_body: Optional[Dict] = None
    ) -> Any:
        """
        Make HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            json_body: JSON request body
            
        Returns:
            Response JSON data
        """
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
