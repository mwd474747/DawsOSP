"""FRED Data Capability - Federal Reserve Economic Data API integration.

Phase 3.1: Comprehensive type hints added for improved type safety.
"""
import urllib.request
import urllib.error
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from core.typing_compat import TypeAlias
from collections import deque
from core.credentials import get_credential_manager
from core.api_helper import APIHelper

# Type aliases for clarity
APIResponse: TypeAlias = Dict[str, Any]
SeriesData: TypeAlias = Dict[str, Any]
IndicatorData: TypeAlias = Dict[str, Any]
CacheStats: TypeAlias = Dict[str, Any]

# Set up logging
logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for FRED API calls with exponential backoff"""

    def __init__(self, max_requests_per_minute: int = 1000):
        """
        Initialize rate limiter

        Args:
            max_requests_per_minute: Maximum API requests per minute (FRED has no strict limit, but 1000 is safe)
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

class FredDataCapability(APIHelper):
    """Federal Reserve Economic Data (FRED) API integration with retry and fallback tracking"""

    def __init__(self) -> None:
        """Initialize FRED Data Capability with API key and cache configuration."""
        # Initialize APIHelper mixin
        super().__init__()

        # Get FRED API key from credential manager
        credentials = get_credential_manager()
        self.api_key: Optional[str] = credentials.get('FRED_API_KEY', required=False)
        self.base_url: str = 'https://api.stlouisfed.org/fred'
        self.cache: Dict[str, Dict[str, Any]] = {}

        # Configurable TTL by data type (in seconds)
        # Economic data changes daily at most, so 24 hours is safe
        self.cache_ttl: Dict[str, int] = {
            'series': 86400,      # 24 hours - economic data
            'metadata': 604800,   # 1 week - series metadata rarely changes
            'latest': 86400       # 24 hours - latest values
        }

        # Rate limiter (FRED has no strict limit, but 1000/min is safe)
        self.rate_limiter: RateLimiter = RateLimiter(max_requests_per_minute=1000)

        # Cache statistics
        self.cache_stats: Dict[str, int] = {
            'hits': 0,
            'misses': 0,
            'expired_fallbacks': 0
        }

        # Common economic indicators with T10Y2Y spread included
        self.indicators: Dict[str, str] = {
            'GDP': 'GDP',  # Gross Domestic Product
            'CPI': 'CPIAUCSL',  # Consumer Price Index
            'UNEMPLOYMENT': 'UNRATE',  # Unemployment Rate
            'FED_FUNDS': 'DFF',  # Federal Funds Rate
            'TREASURY_10Y': 'DGS10',  # 10-Year Treasury Rate
            'TREASURY_2Y': 'DGS2',  # 2-Year Treasury Rate
            'T10Y2Y': 'T10Y2Y',  # 10Y-2Y Treasury Spread (Recession Indicator)
            'SP500': 'SP500',  # S&P 500 Index
            'VIX': 'VIXCLS',  # CBOE Volatility Index
            'DOLLAR_INDEX': 'DTWEXBGS',  # Trade Weighted Dollar Index
            'RETAIL_SALES': 'RSXFS',  # Retail Sales
            'INDUSTRIAL_PRODUCTION': 'INDPRO',  # Industrial Production Index
            'HOUSING_STARTS': 'HOUST',  # Housing Starts
            'CONSUMER_SENTIMENT': 'UMCSENT',  # Consumer Sentiment
            'M2': 'M2SL',  # M2 Money Supply
            'INFLATION_EXPECTATIONS': 'T5YIE',  # 5-Year Inflation Expectations
            'CREDIT_SPREADS': 'BAMLH0A0HYM2',  # High Yield Credit Spreads
            'DEBT_TO_GDP': 'GFDEGDQ188S',  # Federal Debt to GDP
            'SAVINGS_RATE': 'PSAVERT',  # Personal Savings Rate
            'JOBLESS_CLAIMS': 'ICSA',  # Initial Jobless Claims
            'NFIB_OPTIMISM': 'NFIB',  # Small Business Optimism Index
            'PMI_MANUFACTURING': 'MANEMP',  # Manufacturing Employment
        }

    def _get_from_cache(self, cache_key: str, data_type: str) -> Optional[Tuple[Dict, bool]]:
        """
        Get data from cache

        Args:
            cache_key: Cache key to lookup
            data_type: Type of data for TTL lookup ('series', 'metadata', 'latest')

        Returns:
            Tuple of (data, is_fresh) or None if not in cache
        """
        if cache_key not in self.cache:
            self.cache_stats['misses'] += 1
            return None

        cached = self.cache[cache_key]
        age = (datetime.now() - cached['time']).total_seconds()
        ttl = self.cache_ttl.get(data_type, 86400)

        if age < ttl:
            self.cache_stats['hits'] += 1
            return (cached['data'], True)
        else:
            # Data exists but is expired
            return (cached['data'], False)

    def _update_cache(self, cache_key: str, data: SeriesData) -> None:
        """Update cache with new data.

        Args:
            cache_key: Key for cache storage
            data: Data to cache
        """
        self.cache[cache_key] = {
            'data': data,
            'time': datetime.now()
        }

    def _fetch_url(self, url: str) -> APIResponse:
        """
        Internal method to fetch URL (wrapped by api_call for retry/fallback)

        Args:
            url: Full API URL

        Returns:
            Parsed JSON response

        Raises:
            Exception: On any error (handled by APIHelper)
        """
        # Check if API key is available
        if not self.api_key:
            raise ValueError("FRED API key not configured")

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        # Make request
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            logger.debug(f"API call successful: {url[:100]}...")
            return data

    def _make_api_call(self, url: str, max_retries: int = 3) -> Optional[APIResponse]:
        """
        Make API call with retry logic and fallback tracking (uses APIHelper)

        Args:
            url: Full API URL
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed JSON response or None on failure
        """
        return self.api_call(
            self._fetch_url,
            url,
            max_retries=max_retries,
            backoff=1.0,
            fallback=None,
            component_name='fred_api'
        )

    def get_cache_stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            Dictionary with cache hit rate and usage metrics
        """
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'cache_hit_rate': f"{hit_rate:.1f}%",
            'expired_fallbacks': self.cache_stats['expired_fallbacks'],
            'cached_items': len(self.cache)
        }

    def get_health_status(self) -> CacheStats:
        """
        Get API health status for observability

        Returns:
            Dict with health metrics including:
            - api_configured: bool - Whether API key is set
            - fallback_count: int - Number of times expired cache was used
            - cache_health: str - 'healthy', 'degraded', or 'critical'
            - warnings: List[str] - Active warnings
        """
        warnings = []

        # Check API key configuration
        api_configured = bool(self.api_key)
        if not api_configured:
            warnings.append("FRED API key not configured - using cached data only")

        # Check fallback usage
        fallback_count = self.cache_stats['expired_fallbacks']
        if fallback_count > 0:
            warnings.append(f"Using expired cached data ({fallback_count} fallbacks)")

        # Determine cache health
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        if total_requests == 0:
            cache_health = 'unknown'
        elif fallback_count > total_requests * 0.5:
            cache_health = 'critical'  # More than 50% fallbacks
        elif fallback_count > 0:
            cache_health = 'degraded'  # Some fallbacks
        else:
            cache_health = 'healthy'

        return {
            'api_configured': api_configured,
            'fallback_count': fallback_count,
            'cache_health': cache_health,
            'warnings': warnings,
            'total_requests': total_requests,
            'cache_size': len(self.cache)
        }

    def get_series(self, series_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> SeriesData:
        """
        Get time series data for a specific indicator

        Args:
            series_id: FRED series ID (e.g., 'GDP', 'UNRATE')
            start_date: Start date in YYYY-MM-DD format (default: 5 years ago)
            end_date: End date in YYYY-MM-DD format (default: today)

        Returns:
            Dict with series data or error information
        """
        cache_key = f"series_{series_id}:{start_date}:{end_date}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'series')
        if cached and cached[1]:  # If data is fresh
            return cached[0]

        # Default date range
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')

        # Build URL
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date
        }

        url = f"{self.base_url}/series/observations?"
        url += '&'.join([f"{k}={v}" for k, v in params.items()])

        # Make API call
        data = self._make_api_call(url)

        if data:
            # Parse observations
            observations = []
            for obs in data.get('observations', []):
                try:
                    # Skip entries with "." which means no data
                    if obs.get('value') == '.':
                        continue
                    value = float(obs['value'])
                    observations.append({
                        'date': obs['date'],
                        'value': value
                    })
                except (ValueError, KeyError, TypeError):
                    continue

            result = {
                'series_id': series_id,
                'name': self._get_series_name(series_id),
                'units': data.get('units', 'Index'),
                'frequency': data.get('frequency', 'Monthly'),
                'observations': observations,
                'latest_value': observations[-1]['value'] if observations else None,
                'latest_date': observations[-1]['date'] if observations else None
            }

            # Update cache
            self._update_cache(cache_key, result)
            return result

        # API call failed - try to return expired cache data
        if cached:
            cache_age = (datetime.now() - self.cache[cache_key]['time']).days
            logger.warning(
                f"⚠️  FRED API FAILURE - Using expired cache for {series_id} "
                f"(age: {cache_age} days). Data may be stale!"
            )
            self.cache_stats['expired_fallbacks'] += 1
            result = cached[0].copy()
            result['_cached'] = True
            result['_stale'] = True
            result['_cache_age_days'] = cache_age
            result['_warning'] = f'Using expired cached data ({cache_age} days old) due to API failure'
            return result

        logger.error(f"❌ FRED API FAILURE - No cached data available for {series_id}")
        return {'error': 'No data available', 'series_id': series_id}

    def get_latest(self, indicator: str) -> IndicatorData:
        """Get latest value for an indicator.

        Args:
            indicator: Indicator name (e.g., 'GDP', 'CPI', 'UNEMPLOYMENT')

        Returns:
            Dictionary with latest indicator value and metadata
        """

        # Map indicator name to series ID
        series_id = self.indicators.get(indicator.upper(), indicator)

        # Get last 1 year of data (many indicators are monthly/quarterly)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        data = self.get_series(series_id, start_date, end_date)

        if 'error' in data:
            return data

        # Calculate change
        observations = data.get('observations', [])
        if len(observations) >= 2:
            latest = observations[-1]['value']
            previous = observations[-2]['value']
            change = latest - previous
            change_pct = ((latest - previous) / previous * 100) if previous != 0 else 0

            # Determine trend
            if len(observations) >= 5:
                recent_avg = sum(o['value'] for o in observations[-5:]) / 5
                older_avg = sum(o['value'] for o in observations[-10:-5]) / min(5, len(observations)-5) if len(observations) > 5 else recent_avg
                if recent_avg > older_avg * 1.01:
                    trend = 'rising'
                elif recent_avg < older_avg * 0.99:
                    trend = 'falling'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'

            return {
                'indicator': indicator,
                'series_id': series_id,
                'name': data.get('name'),
                'value': latest,
                'previous': previous,
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
                'trend': trend,
                'date': observations[-1]['date'],
                'units': data.get('units')
            }

        return {
            'indicator': indicator,
            'series_id': series_id,
            'value': data.get('latest_value'),
            'date': data.get('latest_date')
        }

    def get_all_indicators(self) -> Dict[str, IndicatorData]:
        """Get latest values for all common indicators.

        Returns:
            Dictionary mapping indicator names to their data
        """

        results = {}

        # Key indicators to fetch
        key_indicators = [
            'GDP', 'CPI', 'UNEMPLOYMENT', 'FED_FUNDS',
            'TREASURY_10Y', 'TREASURY_2Y', 'VIX', 'M2',
            'RETAIL_SALES', 'HOUSING_STARTS', 'JOBLESS_CLAIMS'
        ]

        for indicator in key_indicators:
            data = self.get_latest(indicator)
            if 'error' not in data:
                results[indicator] = data

        # Calculate yield curve (10Y - 2Y)
        if 'TREASURY_10Y' in results and 'TREASURY_2Y' in results:
            yield_curve = results['TREASURY_10Y']['value'] - results['TREASURY_2Y']['value']
            results['YIELD_CURVE'] = {
                'indicator': 'YIELD_CURVE',
                'name': '10Y-2Y Treasury Spread',
                'value': round(yield_curve, 2),
                'inverted': yield_curve < 0,
                'units': 'Percentage Points'
            }

        return results

    def get_recession_indicators(self) -> Dict[str, Any]:
        """Get recession probability indicators.

        Returns:
            Dictionary with recession risk metrics and signals
        """

        indicators = {}

        # Sahm Rule (unemployment rate)
        unemployment = self.get_latest('UNEMPLOYMENT')
        if 'error' not in unemployment:
            # Simplified Sahm rule calculation
            sahm_triggered = unemployment.get('change', 0) > 0.5
            indicators['sahm_rule'] = {
                'triggered': sahm_triggered,
                'unemployment_rate': unemployment.get('value'),
                'change': unemployment.get('change')
            }

        # Yield curve inversion
        treasury_10y = self.get_latest('TREASURY_10Y')
        treasury_2y = self.get_latest('TREASURY_2Y')
        if 'error' not in treasury_10y and 'error' not in treasury_2y:
            spread = treasury_10y['value'] - treasury_2y['value']
            indicators['yield_curve'] = {
                'spread': round(spread, 2),
                'inverted': spread < 0,
                '10y_rate': treasury_10y['value'],
                '2y_rate': treasury_2y['value']
            }

        # Credit spreads
        credit = self.get_latest('CREDIT_SPREADS')
        if 'error' not in credit:
            indicators['credit_spreads'] = {
                'value': credit.get('value'),
                'elevated': credit.get('value', 0) > 5,
                'trend': credit.get('trend')
            }

        # Leading indicators composite
        jobless = self.get_latest('JOBLESS_CLAIMS')
        housing = self.get_latest('HOUSING_STARTS')

        recession_score = 0
        if indicators.get('sahm_rule', {}).get('triggered'):
            recession_score += 30
        if indicators.get('yield_curve', {}).get('inverted'):
            recession_score += 25
        if indicators.get('credit_spreads', {}).get('elevated'):
            recession_score += 20
        if jobless and jobless.get('trend') == 'rising':
            recession_score += 15
        if housing and housing.get('trend') == 'falling':
            recession_score += 10

        indicators['recession_probability'] = {
            'score': recession_score,
            'risk_level': 'High' if recession_score > 60 else 'Medium' if recession_score > 30 else 'Low',
            'description': self._get_recession_description(recession_score)
        }

        return indicators

    def get_inflation_data(self) -> Dict[str, Any]:
        """Get comprehensive inflation metrics.

        Returns:
            Dictionary with CPI, inflation expectations, and regime analysis
        """

        metrics = {}

        # Core CPI
        cpi = self.get_latest('CPI')
        if 'error' not in cpi:
            metrics['cpi'] = {
                'value': cpi.get('value'),
                'yoy_change': cpi.get('change_percent'),
                'trend': cpi.get('trend'),
                'date': cpi.get('date')
            }

        # Inflation expectations
        expectations = self.get_latest('INFLATION_EXPECTATIONS')
        if 'error' not in expectations:
            metrics['expectations_5y'] = {
                'value': expectations.get('value'),
                'trend': expectations.get('trend')
            }

        # M2 money supply growth
        m2 = self.get_latest('M2')
        if 'error' not in m2:
            metrics['m2_growth'] = {
                'value': m2.get('change_percent'),
                'trend': m2.get('trend')
            }

        # Determine inflation regime
        cpi_value = cpi.get('value') if cpi else None
        if cpi_value is not None:
            if cpi_value > 4:
                regime = 'High Inflation'
            elif cpi_value > 2.5:
                regime = 'Above Target'
            elif cpi_value > 1.5:
                regime = 'On Target'
            else:
                regime = 'Below Target/Deflation Risk'

            metrics['regime'] = regime
            metrics['fed_action_likely'] = 'Hawkish' if cpi_value > 3 else 'Neutral' if cpi_value > 2 else 'Dovish'
        else:
            metrics['regime'] = 'Unknown'
            metrics['fed_action_likely'] = 'Unknown'

        return metrics

    def series_info(self, series_id: str) -> SeriesData:
        """
        Get metadata for a FRED series

        Args:
            series_id: FRED series ID (e.g., 'GDP', 'UNRATE')

        Returns:
            Dict with series metadata (title, units, frequency, last_updated, etc.)
        """
        cache_key = f"metadata_{series_id}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'metadata')
        if cached and cached[1]:  # If data is fresh
            return cached[0]

        # Build URL for series info
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json'
        }

        url = f"{self.base_url}/series?"
        url += '&'.join([f"{k}={v}" for k, v in params.items()])

        # Make API call
        data = self._make_api_call(url)

        if data and 'seriess' in data and len(data['seriess']) > 0:
            series_data = data['seriess'][0]
            result = {
                'series_id': series_data.get('id'),
                'title': series_data.get('title'),
                'units': series_data.get('units'),
                'units_short': series_data.get('units_short'),
                'frequency': series_data.get('frequency'),
                'frequency_short': series_data.get('frequency_short'),
                'seasonal_adjustment': series_data.get('seasonal_adjustment'),
                'seasonal_adjustment_short': series_data.get('seasonal_adjustment_short'),
                'last_updated': series_data.get('last_updated'),
                'observation_start': series_data.get('observation_start'),
                'observation_end': series_data.get('observation_end'),
                'popularity': series_data.get('popularity'),
                'notes': series_data.get('notes')
            }

            # Update cache
            self._update_cache(cache_key, result)
            return result

        # API call failed - try to return expired cache data
        if cached:
            cache_age = (datetime.now() - self.cache[cache_key]['time']).days
            logger.warning(
                f"⚠️  FRED API FAILURE - Using expired cache for {series_id} metadata "
                f"(age: {cache_age} days). Data may be stale!"
            )
            self.cache_stats['expired_fallbacks'] += 1
            result = cached[0].copy()
            result['_cached'] = True
            result['_stale'] = True
            result['_cache_age_days'] = cache_age
            result['_warning'] = f'Using expired cached metadata ({cache_age} days old) due to API failure'
            return result

        logger.error(f"❌ FRED API FAILURE - No cached metadata available for {series_id}")
        return {'error': 'No metadata available', 'series_id': series_id}

    def get_multiple_series(self, series_ids: List[str], start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, SeriesData]:
        """
        Fetch multiple series in one call

        Args:
            series_ids: List of FRED series IDs
            start_date: Start date in YYYY-MM-DD format (default: 5 years ago)
            end_date: End date in YYYY-MM-DD format (default: today)

        Returns:
            Dict with series_id as keys and series data as values
        """
        results = {}

        for series_id in series_ids:
            try:
                data = self.get_series(series_id, start_date, end_date)
                results[series_id] = data
            except Exception as e:
                logger.error(f"Error fetching series {series_id}: {e}")
                results[series_id] = {'error': str(e)}

        return results

    def get_latest_value(self, series_id: str) -> SeriesData:
        """
        Get just the most recent data point for a series

        Args:
            series_id: FRED series ID (e.g., 'GDP', 'UNRATE')

        Returns:
            Dict with latest value, date, and series info
        """
        # Get last 1 year of data (many indicators are monthly/quarterly)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        data = self.get_series(series_id, start_date, end_date)

        if 'error' in data:
            return data

        observations = data.get('observations', [])
        if observations:
            latest = observations[-1]
            return {
                'series_id': series_id,
                'name': data.get('name'),
                'value': latest['value'],
                'date': latest['date'],
                'units': data.get('units'),
                'frequency': data.get('frequency')
            }

        return {'error': 'No observations available', 'series_id': series_id}

    def get_series_with_dates(self, series_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> SeriesData:
        """
        Get series data with datetime objects instead of strings

        Args:
            series_id: FRED series ID (e.g., 'GDP', 'UNRATE')
            start_date: Start date in YYYY-MM-DD format (default: 5 years ago)
            end_date: End date in YYYY-MM-DD format (default: today)

        Returns:
            Dict with series data including datetime objects
        """
        data = self.get_series(series_id, start_date, end_date)

        if 'error' in data:
            return data

        # Convert date strings to datetime objects
        observations = data.get('observations', [])
        for obs in observations:
            try:
                obs['datetime'] = datetime.strptime(obs['date'], '%Y-%m-%d')
            except (ValueError, KeyError):
                obs['datetime'] = None

        # Also convert latest_date if present
        if data.get('latest_date'):
            try:
                data['latest_datetime'] = datetime.strptime(data['latest_date'], '%Y-%m-%d')
            except ValueError:
                data['latest_datetime'] = None

        return data

    def _get_series_name(self, series_id: str) -> str:
        """Get human-readable name for series.

        Args:
            series_id: FRED series ID

        Returns:
            Human-readable series name
        """

        # Reverse lookup in indicators dict
        for name, sid in self.indicators.items():
            if sid == series_id:
                return name.replace('_', ' ').title()

        return series_id

    def _get_recession_description(self, score: int) -> str:
        """Get description based on recession score.

        Args:
            score: Recession risk score (0-100)

        Returns:
            Human-readable recession risk description
        """

        if score >= 70:
            return "Very high recession risk. Multiple indicators flashing red."
        elif score >= 50:
            return "Elevated recession risk. Several concerning indicators."
        elif score >= 30:
            return "Moderate recession risk. Some warning signs present."
        elif score >= 15:
            return "Low recession risk. Few concerns at this time."
        else:
            return "Minimal recession risk. Economic indicators generally positive."
