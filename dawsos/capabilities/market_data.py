"""Market Data Capability - Financial Modeling Prep API integration.

Phase 3.1: Comprehensive type hints added for improved type safety.
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
QuoteData: TypeAlias = Dict[str, Any]
ProfileData: TypeAlias = Dict[str, Any]
HistoricalData: TypeAlias = List[Dict[str, Any]]
FinancialData: TypeAlias = List[Dict[str, Any]]
ScreenerResults: TypeAlias = List[Dict[str, Any]]
CacheStats: TypeAlias = Dict[str, Any]

# Set up logging
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for FMP API calls with exponential backoff"""

    def __init__(self, max_requests_per_minute: int = 750):
        """
        Initialize rate limiter

        Args:
            max_requests_per_minute: Maximum API requests per minute (FMP Pro = 750)
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


class MarketDataCapability:
    """Financial Modeling Prep API integration (Pro version)"""

    def __init__(self) -> None:
        """Initialize Market Data Capability with FMP API key and cache configuration."""
        # Get FMP API key from credential manager
        credentials = get_credential_manager()
        self.api_key: Optional[str] = credentials.get('FMP_API_KEY', required=False)
        self.base_url: str = 'https://financialmodelingprep.com/api'
        self.cache: Dict[str, Dict[str, Any]] = {}

        # Configurable TTL by data type (in seconds)
        self.cache_ttl: Dict[str, int] = {
            'quotes': 60,           # 1 minute - real-time data
            'fundamentals': 86400,  # 24 hours - daily updates
            'news': 21600,          # 6 hours
            'historical': 3600,     # 1 hour
            'profile': 86400        # 24 hours
        }

        # Rate limiter (FMP Pro = 750 req/min)
        self.rate_limiter: RateLimiter = RateLimiter(max_requests_per_minute=750)

        # Cache statistics
        self.cache_stats: Dict[str, int] = {
            'hits': 0,
            'misses': 0,
            'expired_fallbacks': 0
        }

    def _get_from_cache(self, cache_key: str, data_type: str) -> Optional[Tuple[Dict, bool]]:
        """
        Get data from cache

        Args:
            cache_key: Cache key to lookup
            data_type: Type of data for TTL lookup ('quotes', 'fundamentals', etc.)

        Returns:
            Tuple of (data, is_fresh) or None if not in cache
        """
        if cache_key not in self.cache:
            self.cache_stats['misses'] += 1
            return None

        cached = self.cache[cache_key]
        age = (datetime.now() - cached['time']).total_seconds()
        ttl = self.cache_ttl.get(data_type, 60)

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
        """
        Make API call with retry logic and error handling

        Args:
            url: Full API URL
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed JSON response or None on failure
        """
        # Check if API key is available
        if not self.api_key:
            logger.error("FMP API key not configured. Please set FMP_API_KEY in credentials.")
            return None

        for retry in range(max_retries):
            try:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed()

                # Make request
                with urllib.request.urlopen(url, timeout=10) as response:
                    data = json.loads(response.read())
                    logger.debug(f"API call successful: {url[:100]}...")
                    return data

            except urllib.error.HTTPError as e:
                if e.code == 429:
                    # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded (429), retry {retry + 1}/{max_retries}")
                    self.rate_limiter.set_backoff(retry + 1)
                    if retry < max_retries - 1:
                        continue
                    else:
                        logger.error("Max retries exceeded for rate limit")
                        return None

                elif e.code == 401:
                    # Authentication error
                    logger.error("Invalid FMP API key (401). Please check your credentials.")
                    return None

                elif e.code == 404:
                    # Not found - symbol may be invalid
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
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'cache_hit_rate': f"{hit_rate:.1f}%",
            'expired_fallbacks': self.cache_stats['expired_fallbacks'],
            'cached_items': len(self.cache)
        }

    def get_quote(self, symbol: str) -> QuoteData:
        """
        Get real-time stock quote

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')

        Returns:
            Dict with quote data or error information
        """
        cache_key = f"quote_{symbol}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'quotes')
        if cached and cached[1]:  # If data is fresh
            return cached[0]

        # Make API call
        url = f"{self.base_url}/v3/quote/{symbol}?apikey={self.api_key}"
        data = self._make_api_call(url)

        if data and len(data) > 0:
            quote_data = data[0]
            quote = {
                'symbol': quote_data.get('symbol'),
                'name': quote_data.get('name'),
                'price': quote_data.get('price'),
                'previous_close': quote_data.get('previousClose'),
                'change': quote_data.get('change'),
                'change_percent': quote_data.get('changesPercentage'),
                'volume': quote_data.get('volume'),
                'market_cap': quote_data.get('marketCap'),
                'exchange': quote_data.get('exchange'),
                'day_low': quote_data.get('dayLow'),
                'day_high': quote_data.get('dayHigh'),
                'year_low': quote_data.get('yearLow'),
                'year_high': quote_data.get('yearHigh'),
                'pe': quote_data.get('pe'),
                'eps': quote_data.get('eps'),
                'avg_volume': quote_data.get('avgVolume'),
                'timestamp': quote_data.get('timestamp')
            }

            # Update cache
            self._update_cache(cache_key, quote)
            return quote

        # API call failed - try to return expired cache data
        if cached:
            logger.warning(f"API call failed, returning expired cache data for {symbol}")
            self.cache_stats['expired_fallbacks'] += 1
            result = cached[0].copy()
            result['_cached'] = True
            result['_warning'] = 'Using expired cached data due to API failure'
            return result

        return {'symbol': symbol, 'error': 'No data available'}
    
    def get_historical(self, symbol: str, period: str = '1M', interval: str = '1d') -> HistoricalData:
        """Get historical price data.

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')
            period: Time period (1D, 5D, 1M, 3M, 6M, 1Y, 3Y, 5Y, 10Y, max)
            interval: Data interval (1min, 5min, 15min, 30min, 1hour, 4hour, 1d)

        Returns:
            List of historical price data dictionaries
        """
        # Map period to FMP format
        period_map = {
            '1D': 1, '5D': 5, '1M': 30, '3M': 90,
            '6M': 180, '1Y': 365, '3Y': 1095, '5Y': 1825,
            '10Y': 3650, 'max': 7300
        }
        days = period_map.get(period, 30)
        
        # Use appropriate endpoint based on interval
        if interval in ['1min', '5min', '15min', '30min', '1hour', '4hour']:
            # Intraday data (Pro feature)
            url = f"{self.base_url}/v3/historical-chart/{interval}/{symbol}?apikey={self.api_key}"
        else:
            # Daily data
            from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            url = f"{self.base_url}/v3/historical-price-full/{symbol}?from={from_date}&to={to_date}&apikey={self.api_key}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                historical = []
                
                if 'historical' in data:
                    # Daily data format
                    for item in data['historical']:
                        historical.append({
                            'date': item.get('date'),
                            'open': item.get('open'),
                            'high': item.get('high'),
                            'low': item.get('low'),
                            'close': item.get('close'),
                            'volume': item.get('volume'),
                            'vwap': item.get('vwap'),
                            'change': item.get('change'),
                            'change_percent': item.get('changePercent')
                        })
                else:
                    # Intraday format
                    for item in data:
                        historical.append({
                            'date': item.get('date'),
                            'open': item.get('open'),
                            'high': item.get('high'),
                            'low': item.get('low'),
                            'close': item.get('close'),
                            'volume': item.get('volume')
                        })
                
                return historical
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_company_profile(self, symbol: str) -> ProfileData:
        """
        Get comprehensive company profile

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')

        Returns:
            Dict with company profile data or error information
        """
        cache_key = f"profile_{symbol}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'profile')
        if cached and cached[1]:  # If data is fresh
            return cached[0]

        # Make API call
        url = f"{self.base_url}/v3/profile/{symbol}?apikey={self.api_key}"
        data = self._make_api_call(url)

        if data and len(data) > 0:
            profile = data[0]
            result = {
                'symbol': profile.get('symbol'),
                'company_name': profile.get('companyName'),
                'sector': profile.get('sector'),
                'industry': profile.get('industry'),
                'ceo': profile.get('ceo'),
                'employees': profile.get('fullTimeEmployees'),
                'headquarters': f"{profile.get('city')}, {profile.get('state')}, {profile.get('country')}",
                'description': profile.get('description'),
                'website': profile.get('website'),
                'ipo_date': profile.get('ipoDate'),
                'market_cap': profile.get('mktCap'),
                'beta': profile.get('beta'),
                'dcf': profile.get('dcf'),  # Discounted Cash Flow value
                'rating': {
                    'score': profile.get('rating'),
                    'recommendation': profile.get('ratingRecommendation')
                }
            }

            # Update cache
            self._update_cache(cache_key, result)
            return result

        # API call failed - try to return expired cache data
        if cached:
            logger.warning(f"API call failed, returning expired cache data for {symbol} profile")
            self.cache_stats['expired_fallbacks'] += 1
            result = cached[0].copy()
            result['_cached'] = True
            result['_warning'] = 'Using expired cached data due to API failure'
            return result

        return {'symbol': symbol, 'error': 'No profile data available'}
    
    def get_financials(self, symbol: str, statement: str = 'income', period: str = 'annual') -> FinancialData:
        """Get financial statements.

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')
            statement: Financial statement type (income, balance, cash-flow)
            period: Reporting period (annual, quarter)

        Returns:
            List of financial statement data dictionaries
        """
        endpoint_map = {
            'income': 'income-statement',
            'balance': 'balance-sheet-statement',
            'cash-flow': 'cash-flow-statement'
        }
        
        endpoint = endpoint_map.get(statement, 'income-statement')
        url = f"{self.base_url}/v3/{endpoint}/{symbol}?period={period}&apikey={self.api_key}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                financials = []
                for item in data[:5]:  # Last 5 periods
                    if statement == 'income':
                        financials.append({
                            'date': item.get('date'),
                            'period': item.get('period'),
                            'revenue': item.get('revenue'),
                            'gross_profit': item.get('grossProfit'),
                            'operating_income': item.get('operatingIncome'),
                            'net_income': item.get('netIncome'),
                            'ebitda': item.get('ebitda'),
                            'eps': item.get('eps'),
                            'eps_diluted': item.get('epsdiluted')
                        })
                    elif statement == 'balance':
                        financials.append({
                            'date': item.get('date'),
                            'period': item.get('period'),
                            'total_assets': item.get('totalAssets'),
                            'total_liabilities': item.get('totalLiabilities'),
                            'total_equity': item.get('totalStockholdersEquity'),
                            'cash': item.get('cashAndCashEquivalents'),
                            'debt': item.get('totalDebt'),
                            'net_debt': item.get('netDebt')
                        })
                    else:  # cash-flow
                        financials.append({
                            'date': item.get('date'),
                            'period': item.get('period'),
                            'operating_cash_flow': item.get('operatingCashFlow'),
                            'investing_cash_flow': item.get('netCashUsedForInvestingActivites'),
                            'financing_cash_flow': item.get('netCashUsedProvidedByFinancingActivities'),
                            'free_cash_flow': item.get('freeCashFlow'),
                            'capex': item.get('capitalExpenditure')
                        })
                
                return financials
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_key_metrics(self, symbol: str, period: str = 'annual') -> FinancialData:
        """Get key financial metrics (Pro feature).

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')
            period: Reporting period (annual, quarter)

        Returns:
            List of key metrics dictionaries
        """
        url = f"{self.base_url}/v3/key-metrics/{symbol}?period={period}&apikey={self.api_key}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                metrics = []
                for item in data[:5]:
                    metrics.append({
                        'date': item.get('date'),
                        'period': item.get('period'),
                        'revenue_per_share': item.get('revenuePerShare'),
                        'pe_ratio': item.get('peRatio'),
                        'price_to_sales': item.get('priceToSalesRatio'),
                        'price_to_book': item.get('priceToBookRatio'),
                        'price_to_fcf': item.get('priceToFreeCashFlowsRatio'),
                        'roe': item.get('roe'),
                        'roa': item.get('roa'),
                        'debt_to_equity': item.get('debtToEquity'),
                        'current_ratio': item.get('currentRatio'),
                        'dividend_yield': item.get('dividendYield')
                    })
                
                return metrics
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_analyst_estimates(self, symbol: str) -> FinancialData:
        """Get analyst estimates (Pro feature).

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')

        Returns:
            List of analyst estimate dictionaries
        """
        url = f"{self.base_url}/v3/analyst-estimates/{symbol}?apikey={self.api_key}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                estimates = []
                for item in data[:4]:  # Next 4 quarters/years
                    estimates.append({
                        'date': item.get('date'),
                        'estimated_revenue_avg': item.get('estimatedRevenueAvg'),
                        'estimated_revenue_high': item.get('estimatedRevenueHigh'),
                        'estimated_revenue_low': item.get('estimatedRevenueLow'),
                        'estimated_eps_avg': item.get('estimatedEpsAvg'),
                        'estimated_eps_high': item.get('estimatedEpsHigh'),
                        'estimated_eps_low': item.get('estimatedEpsLow'),
                        'number_analyst_revenue': item.get('numberAnalystEstimatedRevenue'),
                        'number_analyst_eps': item.get('numberAnalystsEstimatedEps')
                    })
                
                return estimates
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_insider_trading(self, symbol: str) -> FinancialData:
        """Get insider trading data (Pro feature).

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')

        Returns:
            List of insider trading transaction dictionaries
        """
        url = f"{self.base_url}/v4/insider-trading?symbol={symbol}&apikey={self.api_key}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                trades = []
                for item in data[:20]:  # Last 20 trades
                    trades.append({
                        'filing_date': item.get('filingDate'),
                        'transaction_date': item.get('transactionDate'),
                        'reporter_name': item.get('reporterName'),
                        'transaction_type': item.get('transactionType'),
                        'securities_owned': item.get('securitiesOwned'),
                        'securities_transacted': item.get('securitiesTransacted'),
                        'price': item.get('price'),
                        'value': item.get('value')
                    })
                
                return trades
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_institutional_holders(self, symbol: str) -> FinancialData:
        """Get institutional ownership (Pro feature).

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')

        Returns:
            List of institutional holder dictionaries
        """
        url = f"{self.base_url}/v3/institutional-holder/{symbol}?apikey={self.api_key}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                holders = []
                for item in data[:20]:  # Top 20 holders
                    holders.append({
                        'holder': item.get('holder'),
                        'shares': item.get('shares'),
                        'date_reported': item.get('dateReported'),
                        'change': item.get('change'),
                        'percentage_held': item.get('percentageHeld')
                    })
                
                return holders
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def screen_stocks(self, criteria: Dict[str, Any]) -> ScreenerResults:
        """Advanced stock screener (Pro feature).

        Args:
            criteria: Screening criteria dictionary with filters

        Returns:
            List of stocks matching criteria
        """
        # Build query parameters
        params = {
            'apikey': self.api_key,
            'marketCapMoreThan': criteria.get('min_market_cap', 0),
            'marketCapLowerThan': criteria.get('max_market_cap', 10000000000000),
            'priceMoreThan': criteria.get('min_price', 0),
            'priceLowerThan': criteria.get('max_price', 100000),
            'betaMoreThan': criteria.get('min_beta', 0),
            'betaLowerThan': criteria.get('max_beta', 5),
            'volumeMoreThan': criteria.get('min_volume', 0),
            'dividendMoreThan': criteria.get('min_dividend', 0),
            'sector': criteria.get('sector', ''),
            'industry': criteria.get('industry', ''),
            'country': criteria.get('country', 'US'),
            'exchange': criteria.get('exchange', 'NASDAQ,NYSE'),
            'limit': criteria.get('limit', 100)
        }
        
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}
        
        url = f"{self.base_url}/v3/stock-screener?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                results = []
                for item in data:
                    results.append({
                        'symbol': item.get('symbol'),
                        'name': item.get('companyName'),
                        'sector': item.get('sector'),
                        'industry': item.get('industry'),
                        'market_cap': item.get('marketCap'),
                        'price': item.get('price'),
                        'beta': item.get('beta'),
                        'volume': item.get('volume'),
                        'dividend': item.get('lastAnnualDividend'),
                        'exchange': item.get('exchangeShortName')
                    })
                
                return results
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_market_movers(self, type: str = 'gainers') -> ScreenerResults:
        """Get market movers.

        Args:
            type: Mover type (gainers, losers, actives)

        Returns:
            List of market mover dictionaries
        """
        url = f"{self.base_url}/v3/{type}?apikey={self.api_key}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                movers = []
                for item in data[:20]:
                    movers.append({
                        'symbol': item.get('symbol'),
                        'name': item.get('name'),
                        'price': item.get('price'),
                        'change': item.get('change'),
                        'change_percent': item.get('changesPercentage'),
                        'volume': item.get('volume')
                    })
                
                return movers
                
        except Exception as e:
            return [{'error': str(e)}]
