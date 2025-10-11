"""Fundamentals capability - Company fundamental data using FMP API.

Migrated from Alpha Vantage to Financial Modeling Prep (FMP) for better data quality
and consistency with other capabilities.

Phase 3.1: Comprehensive type hints added for improved type safety.
Phase 3.5: Migrated to FMP API, added Pydantic validation.
"""
import urllib.request
import urllib.parse
import json
import logging
from typing import Dict, Any, Optional
from core.typing_compat import TypeAlias
from datetime import datetime
from core.api_helper import APIHelper
from core.credentials import get_credential_manager

# Setup logger
logger = logging.getLogger(__name__)

# Type aliases for clarity
CompanyOverview: TypeAlias = Dict[str, Any]
SymbolStr: TypeAlias = str

class FundamentalsCapability(APIHelper):
    """Company fundamentals and financial data with retry and fallback tracking.

    Uses Financial Modeling Prep (FMP) API for company overview and financial metrics.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Fundamentals Capability with FMP API.

        Args:
            api_key: Optional FMP API key (loads from credentials if not provided)
        """
        # Initialize APIHelper mixin
        super().__init__()

        # Get FMP API key from credential manager
        if api_key is None:
            credentials = get_credential_manager()
            api_key = credentials.get('FMP_API_KEY', required=False)

        self.api_key: Optional[str] = api_key
        self.base_url: str = 'https://financialmodelingprep.com/api'
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl: int = 3600  # 1 hour for fundamentals

    def _fetch_profile(self, symbol: SymbolStr, url: str) -> CompanyOverview:
        """Internal method to fetch company profile from FMP (wrapped by api_call for retry/fallback).

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

            # FMP returns array of profiles, take first one
            if isinstance(data, list) and len(data) > 0:
                profile = data[0]
                return {
                    'symbol': profile.get('symbol'),
                    'name': profile.get('companyName'),
                    'sector': profile.get('sector'),
                    'industry': profile.get('industry'),
                    'market_cap': float(profile.get('mktCap', 0) or 0),
                    'pe_ratio': float(profile.get('peRatio', 0) or 0),
                    'dividend_yield': float(profile.get('lastDiv', 0) or 0) / float(profile.get('price', 1) or 1) if profile.get('lastDiv') and profile.get('price') else 0.0,
                    'eps': float(profile.get('eps', 0) or 0),
                    'beta': float(profile.get('beta', 0) or 0)
                }
            else:
                raise ValueError(f"No profile data available for {symbol}")

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
                logger.debug(f"Returning cached overview for {symbol}")
                return cached['data']

        # Build FMP profile URL
        if not self.api_key:
            logger.warning("No FMP_API_KEY available, returning fallback")
            return {
                'symbol': symbol,
                'error': 'FMP API key not configured',
                'name': None,
                'sector': None,
                'industry': None,
                'market_cap': 0.0,
                'pe_ratio': 0.0,
                'dividend_yield': 0.0,
                'eps': 0.0,
                'beta': 0.0
            }

        # FMP v3 profile endpoint
        url = f"{self.base_url}/v3/profile/{symbol}?apikey={self.api_key}"

        # Use APIHelper for retry and fallback tracking
        overview = self.api_call(
            self._fetch_profile,
            symbol,
            url,
            max_retries=3,
            backoff=1.0,
            fallback={
                'symbol': symbol,
                'error': 'API unavailable - using cached data',
                'name': None,
                'sector': None,
                'industry': None,
                'market_cap': 0.0,
                'pe_ratio': 0.0,
                'dividend_yield': 0.0,
                'eps': 0.0,
                'beta': 0.0
            },
            component_name='fmp_fundamentals'
        )

        # VALIDATE response with Pydantic before returning
        overview = self._validate_overview(overview, symbol)

        # Cache successful results
        if overview and 'error' not in overview:
            self.cache[cache_key] = {
                'data': overview,
                'time': datetime.now().timestamp()
            }
            logger.info(f"Cached overview for {symbol}")

        return overview

    def _validate_overview(self, overview_data: dict, symbol: str) -> dict:
        """Validate company overview data with Pydantic before returning.

        Args:
            overview_data: Raw overview data from API
            symbol: Stock symbol for context

        Returns:
            Validated overview dict or error dict with validation details
        """
        try:
            from models.fundamentals import CompanyOverview
            from pydantic import ValidationError as PydanticValidationError

            try:
                validated = CompanyOverview(**overview_data)
                logger.info(f"✓ Validated company overview for {symbol}")
                return validated.model_dump()
            except PydanticValidationError as e:
                logger.error(f"❌ Company overview validation failed for {symbol}: {e}")
                return {
                    'symbol': symbol,
                    'error': 'Data validation failed',
                    'validation_errors': [
                        {'field': '.'.join(str(loc) for loc in err['loc']), 'message': err['msg']}
                        for err in e.errors()
                    ]
                }
        except ImportError as e:
            logger.warning(f"Pydantic models not available, skipping validation: {e}")
            return overview_data

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of FMP fundamentals API.

        Returns:
            Dictionary with API health metrics
        """
        return {
            'api_name': 'FMP Fundamentals',
            'base_url': self.base_url,
            'has_api_key': bool(self.api_key),
            'cache_size': len(self.cache),
            'cache_ttl_seconds': self.cache_ttl,
            'status': 'configured' if self.api_key else 'missing_key'
        }
