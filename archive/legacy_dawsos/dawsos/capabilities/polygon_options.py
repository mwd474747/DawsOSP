"""Polygon Options Capability - Polygon.io API integration for options data.

Provides options chain data, Greeks, unusual activity detection, and IV analysis.
Follows MarketDataCapability pattern for consistency.
"""
import urllib.request
import urllib.parse
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from core.typing_compat import TypeAlias
from collections import deque
from core.credentials import get_credential_manager

# Type aliases for clarity
OptionChainData: TypeAlias = Dict[str, Any]
UnusualActivity: TypeAlias = List[Dict[str, Any]]
GreeksData: TypeAlias = Dict[str, float]
IVRankData: TypeAlias = Dict[str, Any]
CacheStats: TypeAlias = Dict[str, Any]

# Set up logging
logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for Polygon API calls with exponential backoff

    Polygon Starter plan: 5 req/sec = 300 req/min (conservative limit)
    """

    def __init__(self, max_requests_per_minute: int = 300):
        """Initialize rate limiter

        Args:
            max_requests_per_minute: Maximum API requests per minute (default: 300 for Starter)
        """
        self.max_requests = max_requests_per_minute
        self.requests = deque()
        self.backoff_until = None

    def wait_if_needed(self) -> None:
        """Wait if approaching rate limit or in backoff period."""
        now = time.time()

        # Check if we're in backoff period
        if self.backoff_until and now < self.backoff_until:
            wait_time = self.backoff_until - now
            logger.warning(f"Rate limit backoff: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            self.backoff_until = None
            return

        # Remove requests older than 1 minute
        minute_ago = now - 60
        while self.requests and self.requests[0] < minute_ago:
            self.requests.popleft()

        # If approaching limit, wait
        if len(self.requests) >= self.max_requests * 0.95:  # 95% threshold
            wait_time = 60 - (now - self.requests[0])
            if wait_time > 0:
                logger.warning(f"Approaching rate limit: waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
                self.requests.clear()

        # Record this request
        self.requests.append(now)

    def set_backoff(self, retry_count: int = 1) -> None:
        """Set exponential backoff period.

        Args:
            retry_count: Number of retry attempts (default: 1)
        """
        backoff_seconds = min(2 ** retry_count, 60)  # Max 60 seconds
        self.backoff_until = time.time() + backoff_seconds
        logger.warning(f"Setting backoff for {backoff_seconds} seconds (retry {retry_count})")


class PolygonOptionsCapability:
    """Polygon.io options data integration with retry and caching"""

    def __init__(self) -> None:
        """Initialize Polygon Options Capability with API key and cache configuration."""
        # Get Polygon API key from credential manager
        credentials = get_credential_manager()
        self.api_key: Optional[str] = credentials.get('POLYGON_API_KEY', required=False)
        self.base_url: str = 'https://api.polygon.io'
        self.cache: Dict[str, Dict[str, Any]] = {}

        # Configurable TTL by data type (in seconds)
        self.cache_ttl: Dict[str, int] = {
            'option_chain': 900,     # 15 minutes (matches data delay)
            'unusual': 300,          # 5 minutes (more frequent for signals)
            'greeks': 900,           # 15 minutes
            'iv_rank': 3600,         # 1 hour (slower changing)
            'historical': 86400      # 24 hours
        }

        # Rate limiter (Polygon Starter = 5 req/sec = 300 req/min)
        self.rate_limiter: RateLimiter = RateLimiter(max_requests_per_minute=300)

        # Cache statistics
        self.cache_stats: Dict[str, int] = {
            'hits': 0,
            'misses': 0,
            'expired_fallbacks': 0
        }

    def _get_from_cache(self, cache_key: str, data_type: str) -> Optional[Tuple[Dict, bool]]:
        """Get data from cache

        Args:
            cache_key: Cache key to lookup
            data_type: Type of data for TTL lookup

        Returns:
            Tuple of (data, is_fresh) or None if not in cache
        """
        if cache_key not in self.cache:
            self.cache_stats['misses'] += 1
            return None

        cached = self.cache[cache_key]
        age = (datetime.now() - cached['time']).total_seconds()
        ttl = self.cache_ttl.get(data_type, 900)

        if age < ttl:
            self.cache_stats['hits'] += 1
            return (cached['data'], True)
        else:
            # Data exists but is expired
            return (cached['data'], False)

    def _update_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Update cache with new data.

        Args:
            cache_key: Key for cache storage
            data: Data to cache
        """
        self.cache[cache_key] = {
            'data': data,
            'time': datetime.now()
        }

    def _make_api_call(self, url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """Make API call with retry logic and error handling

        Args:
            url: Full API URL
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed JSON response or None on failure
        """
        # Check if API key is available
        if not self.api_key:
            logger.error("Polygon API key not configured. Please set POLYGON_API_KEY in credentials.")
            return None

        for retry in range(max_retries):
            try:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed()

                # Make request
                with urllib.request.urlopen(url, timeout=10) as response:
                    data = json.loads(response.read())
                    logger.debug(f"Polygon API call successful: {url[:100]}...")
                    return data

            except urllib.error.HTTPError as e:
                if e.code == 429:
                    # Rate limit exceeded
                    logger.warning(f"Polygon rate limit exceeded (429), retry {retry + 1}/{max_retries}")
                    self.rate_limiter.set_backoff(retry + 1)
                    if retry < max_retries - 1:
                        continue
                    else:
                        logger.error("Max retries exceeded for rate limit")
                        return None

                elif e.code == 401:
                    # Authentication error
                    logger.error("Invalid Polygon API key (401). Please check your credentials.")
                    return None

                elif e.code == 404:
                    # Not found
                    logger.warning(f"Resource not found (404): {url[:100]}...")
                    return None

                else:
                    logger.error(f"HTTP error {e.code}: {e.reason}")
                    if retry < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None

            except urllib.error.URLError as e:
                # Network error
                logger.error(f"Network error: {e.reason}, retry {retry + 1}/{max_retries}")
                if retry < max_retries - 1:
                    time.sleep(2 ** retry)  # Exponential backoff
                    continue
                return None

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {e}")
                return None

            except Exception as e:
                logger.error(f"Unexpected error: {type(e).__name__}: {e}")
                return None

        return None

    def get_cache_stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            Dictionary with cache hit rate and usage metrics
        """
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'total_requests': total_requests,
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'expired_fallbacks': self.cache_stats['expired_fallbacks']
        }

    def get_option_chain(
        self,
        ticker: str,
        expiration: Optional[str] = None,
        strike_gte: Optional[float] = None,
        strike_lte: Optional[float] = None,
        limit: int = 250
    ) -> OptionChainData:
        """Fetch option chain for a ticker

        Args:
            ticker: Stock symbol (e.g., 'SPY')
            expiration: Expiration date filter (YYYY-MM-DD)
            strike_gte: Minimum strike price
            strike_lte: Maximum strike price
            limit: Maximum contracts to return (default: 250, max per call)

        Returns:
            Dictionary with calls, puts, and metadata
        """
        # Build cache key
        cache_key = f"option_chain:{ticker}:{expiration}:{strike_gte}:{strike_lte}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'option_chain')
        if cached:
            data, is_fresh = cached
            if is_fresh:
                logger.info(f"Cache hit: option_chain for {ticker}")
                return data

        # Build API URL
        params = {
            'underlying_ticker': ticker,
            'apiKey': self.api_key,
            'limit': limit
        }
        if expiration:
            params['expiration_date'] = expiration
        if strike_gte:
            params['strike_price.gte'] = strike_gte
        if strike_lte:
            params['strike_price.lte'] = strike_lte

        url = f"{self.base_url}/v3/reference/options/contracts?{urllib.parse.urlencode(params)}"

        # Make API call
        response = self._make_api_call(url)
        if not response or 'results' not in response:
            # Use cached data as fallback if available
            if cached:
                logger.warning(f"Using expired cache for {ticker} option chain")
                self.cache_stats['expired_fallbacks'] += 1
                return cached[0]

            return {
                'error': 'Failed to fetch option chain',
                'ticker': ticker,
                'calls': [],
                'puts': []
            }

        # Process response
        contracts = response.get('results', [])
        calls = [c for c in contracts if c.get('contract_type') == 'call']
        puts = [c for c in contracts if c.get('contract_type') == 'put']

        result = {
            'ticker': ticker,
            'calls': calls,
            'puts': puts,
            'total_contracts': len(contracts),
            'timestamp': datetime.now().isoformat()
        }

        # VALIDATE response with Pydantic before caching
        result = self._validate_option_chain(result)

        # Update cache
        self._update_cache(cache_key, result)

        return result

    def detect_unusual_activity(
        self,
        min_premium: float = 10000,
        volume_oi_ratio: float = 3.0,
        lookback_hours: int = 24
    ) -> UnusualActivity:
        """Scan for unusual options activity (smart money signals)

        Args:
            min_premium: Minimum premium threshold in dollars
            volume_oi_ratio: Minimum volume/OI ratio for signal
            lookback_hours: Hours to look back

        Returns:
            List of unusual activity signals
        """
        cache_key = f"unusual:{min_premium}:{volume_oi_ratio}:{lookback_hours}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'unusual')
        if cached:
            data, is_fresh = cached
            if is_fresh:
                logger.info("Cache hit: unusual activity")
                return data

        # For MVP, return placeholder - full implementation requires:
        # 1. Snapshot API access (higher tier)
        # 2. Aggregates API for volume/OI data
        # 3. Real-time processing

        logger.info(f"Unusual activity scan: min_premium=${min_premium}, vol/OI>{volume_oi_ratio}")

        result = []  # Placeholder for now

        # Update cache
        self._update_cache(cache_key, result)

        return result

    def calculate_iv_rank(
        self,
        ticker: str,
        lookback_days: int = 252
    ) -> IVRankData:
        """Calculate IV rank and percentile

        Args:
            ticker: Stock symbol
            lookback_days: Days to look back for IV history (default: 252 = 1 year)

        Returns:
            Dictionary with IV rank, percentile, and strategy suggestions
        """
        cache_key = f"iv_rank:{ticker}:{lookback_days}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'iv_rank')
        if cached:
            data, is_fresh = cached
            if is_fresh:
                logger.info(f"Cache hit: IV rank for {ticker}")
                return data

        # Placeholder for MVP - full implementation requires historical IV data
        logger.info(f"IV rank calculation for {ticker} (lookback: {lookback_days} days)")

        result = {
            'ticker': ticker,
            'current_iv': 0.0,
            'iv_rank': 0.0,
            'iv_percentile': 0.0,
            'high_52w': 0.0,
            'low_52w': 0.0,
            'suggested_strategies': [],
            'note': 'Placeholder - requires historical IV data'
        }

        # Update cache
        self._update_cache(cache_key, result)

        return result

    def get_greeks(
        self,
        ticker: str,
        expiration: Optional[str] = None
    ) -> GreeksData:
        """Get aggregated Greeks for ticker

        Args:
            ticker: Stock symbol
            expiration: Optional expiration date filter

        Returns:
            Dictionary with aggregated Greeks
        """
        # Fetch option chain
        chain = self.get_option_chain(ticker, expiration=expiration)

        if 'error' in chain:
            return {
                'error': chain['error'],
                'net_delta': 0.0,
                'total_gamma': 0.0
            }

        # Aggregate Greeks from calls and puts
        # Note: Polygon provides Greeks in contract details
        net_delta = 0.0
        total_gamma = 0.0

        for call in chain.get('calls', []):
            # Greeks would be in contract details (requires additional API call per contract)
            # For MVP, placeholder
            pass

        for put in chain.get('puts', []):
            # Greeks would be in contract details
            pass

        result = {
            'ticker': ticker,
            'net_delta': net_delta,
            'total_gamma': total_gamma,
            'note': 'Placeholder - requires detailed contract data'
        }

        # VALIDATE response with Pydantic
        result = self._validate_greeks(result)

        return result

    def _validate_option_chain(self, chain_data: dict) -> dict:
        """Validate option chain data with Pydantic before returning.

        Args:
            chain_data: Raw option chain data

        Returns:
            Validated chain dict or error dict with validation details
        """
        try:
            from models.options import OptionChainResponse, OptionsContract
            from pydantic import ValidationError as PydanticValidationError

            try:
                # Validate individual contracts first (with intelligent filtering)
                validated_calls = []
                validated_puts = []
                contract_errors = []

                for i, call_data in enumerate(chain_data.get('calls', [])):
                    try:
                        validated = OptionsContract(**call_data)
                        validated_calls.append(validated.model_dump())
                    except PydanticValidationError as e:
                        logger.warning(f"Call contract {i} validation failed: {e}")
                        contract_errors.append({'index': i, 'type': 'call', 'errors': e.errors()})

                for i, put_data in enumerate(chain_data.get('puts', [])):
                    try:
                        validated = OptionsContract(**put_data)
                        validated_puts.append(validated.model_dump())
                    except PydanticValidationError as e:
                        logger.warning(f"Put contract {i} validation failed: {e}")
                        contract_errors.append({'index': i, 'type': 'put', 'errors': e.errors()})

                # Update chain_data with validated contracts
                validated_chain_data = {
                    **chain_data,
                    'calls': validated_calls,
                    'puts': validated_puts,
                    'total_contracts': len(validated_calls) + len(validated_puts)
                }

                # Validate the full chain response
                validated_chain = OptionChainResponse(**validated_chain_data)
                logger.info(f"✓ Validated option chain: {len(validated_calls)} calls, {len(validated_puts)} puts")

                if contract_errors:
                    logger.warning(f"⚠ {len(contract_errors)} contracts failed validation and were filtered")

                return validated_chain.model_dump()

            except PydanticValidationError as e:
                logger.error(f"❌ Option chain validation failed: {e}")
                return {
                    'ticker': chain_data.get('ticker', 'UNKNOWN'),
                    'error': 'Option chain validation failed',
                    'validation_errors': [
                        {'field': '.'.join(str(loc) for loc in err['loc']), 'message': err['msg']}
                        for err in e.errors()
                    ],
                    'calls': [],
                    'puts': [],
                    'total_contracts': 0,
                    'timestamp': datetime.now().isoformat()
                }
        except ImportError as e:
            logger.warning(f"Pydantic models not available, skipping validation: {e}")
            return chain_data

    def _validate_greeks(self, greeks_data: dict) -> dict:
        """Validate Greeks data with Pydantic before returning.

        Args:
            greeks_data: Raw Greeks data

        Returns:
            Validated Greeks dict or error dict with validation details
        """
        try:
            from models.options import GreeksData
            from pydantic import ValidationError as PydanticValidationError

            try:
                validated = GreeksData(**greeks_data)
                logger.info(f"✓ Validated Greeks for {greeks_data.get('ticker', 'UNKNOWN')}")
                return validated.model_dump()
            except PydanticValidationError as e:
                logger.error(f"❌ Greeks validation failed: {e}")
                return {
                    'ticker': greeks_data.get('ticker', 'UNKNOWN'),
                    'error': 'Greeks validation failed',
                    'validation_errors': [
                        {'field': '.'.join(str(loc) for loc in err['loc']), 'message': err['msg']}
                        for err in e.errors()
                    ],
                    'net_delta': 0.0,
                    'total_gamma': 0.0
                }
        except ImportError as e:
            logger.warning(f"Pydantic models not available, skipping validation: {e}")
            return greeks_data
