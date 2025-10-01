"""Fundamentals capability - Company fundamental data"""
import urllib.request
import urllib.parse
import json
from typing import Dict, List
from datetime import datetime

class FundamentalsCapability:
    """Company fundamentals and financial data"""

    def __init__(self, api_key: str = None):
        # Using Alpha Vantage (free tier available)
        # Get key at: https://www.alphavantage.co/support/#api-key
        self.api_key = api_key or 'demo'  # Demo key for testing
        self.base_url = 'https://www.alphavantage.co/query'
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour for fundamentals

    def get_overview(self, symbol: str) -> Dict:
        """Get company overview and key metrics"""
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

        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())

                if 'Symbol' in data:
                    overview = {
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

                    # Cache results
                    self.cache[cache_key] = {
                        'data': overview,
                        'time': datetime.now().timestamp()
                    }

                    return overview

                return {'symbol': symbol, 'error': 'No data available'}

        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}