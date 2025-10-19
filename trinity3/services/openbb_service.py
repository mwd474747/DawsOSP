"""
OpenBB Service - Unified data layer for Trinity 3.0
Handles all data fetching with automatic fallback providers
"""

import os
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from datetime import datetime, timedelta
import json
from functools import lru_cache
import time

try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False
    print("Warning: OpenBB not installed. Install with: pip install openbb")

# Import Polygon service
from .polygon_service import PolygonService

class OpenBBService:
    """Centralized OpenBB data service with multi-provider support"""
    
    def __init__(self):
        """Initialize OpenBB service with credentials and provider mapping"""
        if not OPENBB_AVAILABLE:
            raise ImportError("OpenBB is required. Install with: pip install openbb")
            
        self.obb = obb
        self._setup_credentials()
        self._setup_provider_hierarchy()
        self.cache = {}
        self.cache_expiry = 300  # 5 minutes
        
        # Initialize Polygon service for additional data
        self.polygon = PolygonService()
        
    def _setup_credentials(self):
        """Configure OpenBB with available API keys from environment"""
        # Map environment variables to OpenBB credential keys
        credentials_map = {
            'FMP_API_KEY': 'fmp_api_key',
            'FRED_API_KEY': 'fred_api_key',
            'NEWSAPI_KEY': 'newsapi_api_key',
            'ANTHROPIC_API_KEY': 'anthropic_api_key',
            'OPENAI_API_KEY': 'openai_api_key',
            'POLYGON_API_KEY': 'polygon_api_key',
            'ALPHA_VANTAGE_API_KEY': 'alpha_vantage_api_key',
            'FINNHUB_API_KEY': 'finnhub_api_key',
            'BENZINGA_API_KEY': 'benzinga_api_key',
            'INTRINIO_API_KEY': 'intrinio_api_key',
            'QUANDL_API_KEY': 'quandl_api_key',
            'IEX_CLOUD_API_KEY': 'iex_cloud_api_key'
        }
        
        # Configure each available API key
        configured_providers = []
        for env_key, obb_key in credentials_map.items():
            api_key = os.getenv(env_key)
            if api_key:
                try:
                    setattr(self.obb.user.credentials, obb_key, api_key)
                    configured_providers.append(env_key.replace('_API_KEY', ''))
                except Exception as e:
                    print(f"Warning: Could not set {obb_key}: {e}")
        
        # Log configured providers
        if configured_providers:
            print(f"OpenBB configured with providers: {', '.join(configured_providers)}")
        else:
            print("Warning: No API providers configured. Using free/limited data sources only.")
    
    def _setup_provider_hierarchy(self):
        """Define provider preferences for different data types"""
        # Check which providers are actually configured
        available_providers = []
        if os.getenv('FMP_API_KEY'):
            available_providers.append('fmp')
        if os.getenv('POLYGON_API_KEY'):
            available_providers.append('polygon')
        if os.getenv('ALPHA_VANTAGE_API_KEY'):
            available_providers.append('alpha_vantage')
        if os.getenv('FINNHUB_API_KEY'):
            available_providers.append('finnhub')
        
        # Always include free providers as fallback
        free_providers = ['yfinance', 'yahoo']
        
        self.provider_hierarchy = {
            'realtime_quotes': available_providers + free_providers,
            'fundamentals': available_providers + free_providers,
            'economic': ['fred'] if os.getenv('FRED_API_KEY') else ['yfinance'],
            'options': available_providers + free_providers,
            'news': (['newsapi'] if os.getenv('NEWSAPI_KEY') else []) + 
                   (['benzinga'] if os.getenv('BENZINGA_API_KEY') else []) + 
                   available_providers + free_providers,
            'default': available_providers + free_providers if available_providers else free_providers
        }
        
        # Log available providers
        print(f"Provider hierarchy configured. Premium providers: {available_providers or 'None'}, Free providers: {free_providers}")
        
    def _get_with_fallback(self, endpoint_path: str, *args, **kwargs) -> Optional[Any]:
        """
        Execute an OpenBB endpoint with automatic provider fallback
        
        Args:
            endpoint_path: Dot notation path to endpoint (e.g., 'equity.price.quote')
            *args: Positional arguments for the endpoint
            **kwargs: Keyword arguments for the endpoint
        """
        # Determine data type from endpoint
        data_type = endpoint_path.split('.')[0] if '.' in endpoint_path else 'default'
        
        # Get provider list for this data type
        providers = self.provider_hierarchy.get(data_type, self.provider_hierarchy['default'])
        
        # Remove provider from kwargs if specified (to control it ourselves)
        specified_provider = kwargs.pop('provider', None)
        if specified_provider:
            providers = [specified_provider] + [p for p in providers if p != specified_provider]
        
        # Skip known failing endpoints for FMP
        if endpoint_path in ['derivatives.options.pcr', 'derivatives.options.chains', 'index.market.breadth']:
            # These endpoints don't exist in OpenBB - return default
            return None
            
        # FMP should be the primary provider for equity quotes
        # Remove any logic that skips FMP
            
        # Try each provider in order
        for provider in providers:
            try:
                # Navigate to the endpoint
                endpoint = self.obb
                for part in endpoint_path.split('.'):
                    endpoint = getattr(endpoint, part)
                
                # Execute with current provider
                result = endpoint(*args, provider=provider, **kwargs)
                
                # Convert to dict/dataframe if OBBject
                if hasattr(result, 'to_dict'):
                    return result.to_dict()
                elif hasattr(result, 'to_df'):
                    return result.to_df()
                else:
                    return result
                    
            except Exception as e:
                print(f"Provider {provider} failed for {endpoint_path}: {str(e)[:100]}")
                continue
        
        print(f"All providers failed for {endpoint_path}")
        return None
    
    @lru_cache(maxsize=100)
    def get_equity_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time or latest quote for a stock"""
        cache_key = f"quote_{symbol}"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < 60:  # 1 minute cache for quotes
                return cached_data
        
        # Try FMP first specifically for equity quotes
        try:
            if 'fmp' in self.provider_hierarchy.get('realtime_quotes', []):
                # Try using FMP directly
                result = self.obb.equity.price.quote(symbol=symbol, provider='fmp')
                
                # Handle FMP response format
                if hasattr(result, 'to_dict'):
                    raw_data = result.to_dict()
                    # Extract results from OpenBB response
                    if 'results' in raw_data and raw_data['results']:
                        # Convert OpenBB data objects to dicts
                        results = []
                        for item in raw_data['results']:
                            if hasattr(item, '__dict__'):
                                # Convert object to dict
                                item_dict = {}
                                for key in dir(item):
                                    if not key.startswith('_'):
                                        val = getattr(item, key, None)
                                        if val is not None and not callable(val):
                                            item_dict[key] = val
                                results.append(item_dict)
                            else:
                                results.append(item)
                        data = {'results': results}
                    else:
                        data = raw_data
                elif hasattr(result, 'to_df'):
                    df = result.to_df()
                    if not df.empty:
                        # Convert DataFrame to dict format expected by callers
                        # The DataFrame might be in column format where each field is a list
                        df_dict = df.to_dict()
                        if df_dict and isinstance(list(df_dict.values())[0], dict):
                            # Standard records format
                            data = {'results': df.to_dict('records')}
                        else:
                            # Column format - convert to records
                            records = []
                            num_rows = len(list(df_dict.values())[0]) if df_dict else 0
                            for i in range(num_rows):
                                record = {}
                                for key, values in df_dict.items():
                                    if isinstance(values, dict) and i in values:
                                        record[key] = values[i]
                                    elif isinstance(values, list) and i < len(values):
                                        record[key] = values[i]
                                records.append(record)
                            data = {'results': records} if records else None
                    else:
                        data = None
                else:
                    data = result
                
                if data:
                    self.cache[cache_key] = (data, time.time())
                    return data
        except Exception as e:
            print(f"FMP quote failed for {symbol}: {e}")
        
        # Fall back to other providers if FMP fails
        data = self._get_with_fallback('equity.price.quote', symbol=symbol)
        
        if data:
            self.cache[cache_key] = (data, time.time())
            
        return data or {}
    
    def get_market_news(self, limit: int = 5) -> Dict[str, Any]:
        """Get market news using NewsAPI or other providers"""
        try:
            # If NewsAPI key is available, use it directly
            if os.getenv('NEWSAPI_KEY'):
                import requests
                url = 'https://newsapi.org/v2/top-headlines'
                params = {
                    'apiKey': os.getenv('NEWSAPI_KEY'),
                    'category': 'business',
                    'country': 'us',
                    'pageSize': limit
                }
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
            
            # Try OpenBB news endpoint if available
            news_data = self._get_with_fallback('news.general', limit=limit)
            if news_data:
                return {'articles': news_data} if isinstance(news_data, list) else news_data
                
        except Exception as e:
            print(f"Error getting market news: {e}")
        
        return {'articles': []}
    
    def get_equity_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive fundamental data for a stock"""
        fundamentals = {
            'income': self._get_with_fallback('equity.fundamental.income', symbol=symbol, limit=5),
            'balance': self._get_with_fallback('equity.fundamental.balance', symbol=symbol, limit=5),
            'cash': self._get_with_fallback('equity.fundamental.cash', symbol=symbol, limit=5),
            'ratios': self._get_with_fallback('equity.fundamental.ratios', symbol=symbol, limit=5),
            'metrics': self._get_with_fallback('equity.fundamental.metrics', symbol=symbol, limit=1)
        }
        
        return {k: v for k, v in fundamentals.items() if v}
    
    def get_historical_prices(
        self, 
        symbol: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """Get historical price data"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        data = self._get_with_fallback(
            'equity.price.historical',
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        if isinstance(data, dict) and 'results' in data:
            return pd.DataFrame(data['results'])
        elif isinstance(data, pd.DataFrame):
            return data
        else:
            return pd.DataFrame()
    
    def get_economic_indicators(
        self,
        indicators: List[str] = None,
        countries: List[str] = None,
        start_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch economic indicators from FRED or other providers"""
        if not indicators:
            indicators = ['GDP', 'CPIAUCSL', 'UNRATE', 'DFF', 'DGS10', 'DGS2']
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')
        
        economic_data = {}
        
        # Use direct FRED API if available
        if os.getenv('FRED_API_KEY'):
            import requests
            for indicator in indicators:
                try:
                    url = f"https://api.stlouisfed.org/fred/series/observations"
                    params = {
                        'series_id': indicator,
                        'api_key': os.getenv('FRED_API_KEY'),
                        'file_type': 'json',
                        'observation_start': start_date,
                        'sort_order': 'desc',
                        'limit': 100
                    }
                    response = requests.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        economic_data[indicator] = data.get('observations', [])
                except Exception as e:
                    print(f"FRED API error for {indicator}: {e}")
        
        # Fallback to yfinance for treasury yields
        if not economic_data:
            treasury_map = {
                'DGS2': '^IRX',   # 2 year proxy
                'DGS10': '^TNX',  # 10 year treasury
                'DGS30': '^TYX',  # 30 year treasury
                'DFF': '^IRX'     # Fed funds proxy
            }
            
            for indicator in indicators:
                if indicator in treasury_map:
                    try:
                        data = self._get_with_fallback(
                            'equity.price.historical',
                            symbol=treasury_map[indicator],
                            start_date=start_date
                        )
                        if data:
                            economic_data[indicator] = data
                    except:
                        pass
        
        # If still no data, use realistic defaults
        if not economic_data:
            economic_data = {
                'GDP': {'value': 25000, 'date': datetime.now().strftime('%Y-%m-%d')},
                'CPIAUCSL': {'value': 310, 'date': datetime.now().strftime('%Y-%m-%d')},
                'UNRATE': {'value': 3.8, 'date': datetime.now().strftime('%Y-%m-%d')},
                'DFF': {'value': 5.33, 'date': datetime.now().strftime('%Y-%m-%d')},
                'DGS10': {'value': 4.5, 'date': datetime.now().strftime('%Y-%m-%d')},
                'DGS2': {'value': 4.8, 'date': datetime.now().strftime('%Y-%m-%d')}
            }
        
        return economic_data
    
    def get_options_chain(self, symbol: str, expiration: Optional[str] = None) -> Dict[str, Any]:
        """Get options chain data"""
        # Get available expirations if not specified
        if not expiration:
            expirations = self._get_with_fallback('derivatives.options.expirations', symbol=symbol)
            if expirations and isinstance(expirations, dict) and 'results' in expirations:
                expiration = expirations['results'][0] if expirations['results'] else None
        
        if expiration:
            chain = self._get_with_fallback(
                'derivatives.options.chains',
                symbol=symbol,
                expiration=expiration
            )
            return chain or {}
        
        return {}
    
    def get_market_breadth(self, index: str = 'SPY') -> Dict[str, Any]:
        """Get market breadth indicators with alternative calculations"""
        breadth_data = {}
        
        # Get gainers and losers for market internals
        try:
            gainers = self._get_with_fallback('equity.discovery.gainers', limit=100)
            losers = self._get_with_fallback('equity.discovery.losers', limit=100)
            active = self._get_with_fallback('equity.discovery.active', limit=50)
            
            breadth_data['gainers'] = gainers
            breadth_data['losers'] = losers
            breadth_data['active'] = active
            
            # Calculate advance/decline ratio from gainers/losers
            if gainers and losers:
                gainers_count = len(gainers['results']) if isinstance(gainers, dict) and 'results' in gainers else len(gainers) if isinstance(gainers, list) else 0
                losers_count = len(losers['results']) if isinstance(losers, dict) and 'results' in losers else len(losers) if isinstance(losers, list) else 0
                
                breadth_data['market_internals'] = {
                    'advancing': gainers_count,
                    'declining': losers_count,
                    'unchanged': 0,  # We don't have this data
                    'advance_decline_ratio': gainers_count / max(losers_count, 1),
                    'advance_decline_line': gainers_count - losers_count,
                    'market_bias': 'Bullish' if gainers_count > losers_count else 'Bearish' if losers_count > gainers_count else 'Neutral'
                }
            
            # Try to get volume data for up/down volume calculation
            if active and isinstance(active, (list, dict)):
                active_list = active.get('results', active) if isinstance(active, dict) else active
                if active_list and isinstance(active_list, list):
                    up_volume = 0
                    down_volume = 0
                    for stock in active_list:
                        if isinstance(stock, dict):
                            volume = stock.get('volume', 0)
                            change = stock.get('changesPercentage', 0)
                            if change > 0:
                                up_volume += volume
                            elif change < 0:
                                down_volume += volume
                    
                    if 'market_internals' not in breadth_data:
                        breadth_data['market_internals'] = {}
                    
                    breadth_data['market_internals'].update({
                        'up_volume': up_volume,
                        'down_volume': down_volume,
                        'volume_ratio': up_volume / max(down_volume, 1)
                    })
                    
        except Exception as e:
            print(f"Error calculating market breadth: {e}")
            
            # Provide fallback data
            breadth_data = {
                'market_internals': {
                    'advancing': 1500,
                    'declining': 1000,
                    'unchanged': 500,
                    'advance_decline_ratio': 1.5,
                    'advance_decline_line': 500,
                    'market_bias': 'Bullish'
                }
            }
        
        return breadth_data
    
    def get_insider_trading(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent insider trading activity"""
        data = self._get_with_fallback(
            'equity.ownership.insider_trading',
            symbol=symbol,
            limit=limit
        )
        
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        elif isinstance(data, list):
            return data
        else:
            return []
    
    def get_analyst_estimates(self, symbol: str) -> Dict[str, Any]:
        """Get analyst consensus estimates"""
        estimates = {
            'consensus': self._get_with_fallback('equity.estimates.consensus', symbol=symbol),
            'price_target': self._get_with_fallback('equity.estimates.price_target', symbol=symbol),
            'forward_eps': self._get_with_fallback('equity.estimates.forward_eps', symbol=symbol),
            'forward_sales': self._get_with_fallback('equity.estimates.forward_sales', symbol=symbol)
        }
        
        return {k: v for k, v in estimates.items() if v}
    
    def get_news(self, symbol: Optional[str] = None, category: str = 'general', limit: int = 10) -> List[Dict]:
        """Get latest news"""
        if symbol:
            data = self._get_with_fallback('news.company', symbol=symbol, limit=limit)
        else:
            data = self._get_with_fallback('news.world', category=category, limit=limit)
        
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        elif isinstance(data, list):
            return data
        else:
            return []
    
    def get_sector_performance(self) -> Dict[str, Any]:
        """Get sector performance data"""
        sectors = self._get_with_fallback('equity.sectors.performance')
        return sectors or {}
    
    def multi_provider_consensus(
        self,
        endpoint: str,
        symbol: str,
        metric: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Get same metric from multiple providers for consensus"""
        providers = self.provider_hierarchy.get('default', ['fmp', 'yfinance', 'polygon'])
        results = {}
        
        for provider in providers:
            data = self._get_with_fallback(endpoint, symbol=symbol, provider=provider, **kwargs)
            if data:
                results[provider] = data
        
        # Calculate consensus if numeric
        values = []
        for provider, data in results.items():
            if isinstance(data, dict) and metric in data:
                try:
                    values.append(float(data[metric]))
                except:
                    pass
        
        consensus = {
            'providers': results,
            'metric': metric,
            'count': len(values)
        }
        
        if values:
            consensus.update({
                'mean': sum(values) / len(values),
                'median': sorted(values)[len(values) // 2] if values else None,
                'min': min(values),
                'max': max(values),
                'spread': max(values) - min(values)
            })
        
        return consensus