"""Fundamentals capability - Company fundamental data.

Phase 3.1: Comprehensive type hints added for improved type safety.
"""
import urllib.request
import urllib.parse
import json
from typing import Dict, Any, Optional
from core.typing_compat import TypeAlias
from datetime import datetime
from core.api_helper import APIHelper

# Type aliases for clarity
CompanyOverview: TypeAlias = Dict[str, Any]
SymbolStr: TypeAlias = str

class FundamentalsCapability(APIHelper):
    """Company fundamentals and financial data with retry and fallback tracking"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Fundamentals Capability with Alpha Vantage API.

        Args:
            api_key: Optional Alpha Vantage API key (defaults to 'demo')
        """
        # Initialize APIHelper mixin
        super().__init__()

        # Using Alpha Vantage (free tier available)
        # Get key at: https://www.alphavantage.co/support/#api-key
        self.api_key: str = api_key or 'demo'  # Demo key for testing
        self.base_url: str = 'https://www.alphavantage.co/query'
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl: int = 3600  # 1 hour for fundamentals

    def _fetch_overview(self, symbol: SymbolStr, url: str) -> CompanyOverview:
        """Internal method to fetch overview (wrapped by api_call for retry/fallback).

        Args:
            symbol: Stock symbol
            url: Full API URL to fetch

        Returns:
            Dictionary with company overview data

        Raises:
            ValueError: If no data is available in response
        """
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())

            if 'Symbol' in data:
                return {
                    'symbol': data.get('Symbol'),
                    'name': data.get('Name'),
                    'sector': data.get('Sector'),
                    'industry': data.get('Industry'),
                    'market_cap': float(data.get('MarketCapitalization', 0) or 0),
                    'pe_ratio': float(data.get('PERatio', 0) or 0),
                    'dividend_yield': float(data.get('DividendYield', 0) or 0),
                    'eps': float(data.get('EPS', 0) or 0),
                    'beta': float(data.get('Beta', 0) or 0)
                }
            else:
                raise ValueError("No data available in response")

    def get_overview(self, symbol: SymbolStr) -> CompanyOverview:
        """Get company overview and key metrics with retry and fallback.

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Dictionary with company overview and fundamental metrics
        """
        cache_key = f"overview_{symbol}"

        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now().timestamp() - cached['time'] < self.cache_ttl:
                return cached['data']

        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.api_key
        }

        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"

        # Use APIHelper for retry and fallback tracking
        overview = self.api_call(
            self._fetch_overview,
            symbol,
            url,
            max_retries=3,
            backoff=1.0,
            fallback={'symbol': symbol, 'error': 'API unavailable - using cached data'},
            component_name='alpha_vantage'
        )

        # Cache successful results
        if overview and 'error' not in overview:
            self.cache[cache_key] = {
                'data': overview,
                'time': datetime.now().timestamp()
            }

        return overview