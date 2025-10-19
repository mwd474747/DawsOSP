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
        
    def _setup_credentials(self):
        """Configure OpenBB with available API keys from environment"""
        credentials_map = {
            'FMP_API_KEY': 'fmp_api_key',
            'FRED_API_KEY': 'fred_api_key',
            'NEWSAPI_KEY': 'newsapi_api_key',
            'ANTHROPIC_API_KEY': 'anthropic_api_key'
        }
        
        for env_key, obb_key in credentials_map.items():
            if os.getenv(env_key):
                setattr(self.obb.user.credentials, obb_key, os.getenv(env_key))
                
        # Additional providers can be configured here
        # Example: self.obb.user.credentials.polygon_api_key = os.getenv('POLYGON_API_KEY')
    
    def _setup_provider_hierarchy(self):
        """Define provider preferences for different data types"""
        self.provider_hierarchy = {
            'realtime_quotes': ['polygon', 'fmp', 'yfinance'],
            'fundamentals': ['fmp', 'polygon', 'yfinance'],
            'economic': ['fred', 'oecd', 'econdb'],
            'options': ['cboe', 'polygon', 'yfinance'],
            'news': ['newsapi', 'benzinga', 'fmp'],
            'default': ['fmp', 'yfinance']  # Always try these
        }
        
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
        
        data = self._get_with_fallback('equity.price.quote', symbol=symbol)
        
        if data:
            self.cache[cache_key] = (data, time.time())
            
        return data or {}
    
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
        
        # FRED series data
        for indicator in indicators:
            data = self._get_with_fallback(
                'economy.fred',
                series_id=indicator,
                start_date=start_date
            )
            if data:
                economic_data[indicator] = data
        
        # Country-specific data if requested
        if countries:
            gdp_data = self._get_with_fallback('economy.gdp', countries=countries)
            if gdp_data:
                economic_data['gdp_by_country'] = gdp_data
                
            inflation_data = self._get_with_fallback('economy.inflation', countries=countries)
            if inflation_data:
                economic_data['inflation_by_country'] = inflation_data
        
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
        """Get market breadth indicators"""
        breadth_data = {
            'gainers': self._get_with_fallback('equity.discovery.gainers'),
            'losers': self._get_with_fallback('equity.discovery.losers'),
            'active': self._get_with_fallback('equity.discovery.active'),
            'advancing_declining': self._get_with_fallback('index.market.breadth')
        }
        
        return {k: v for k, v in breadth_data.items() if v}
    
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