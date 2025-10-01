import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class FREDCapability:
    """Federal Reserve Economic Data API integration"""
    
    def __init__(self, api_key: str = None):
        # You can get free key at: https://fred.stlouisfed.org/docs/api/api_key.html
        import os
        self.api_key = api_key or os.getenv('FRED_API_KEY') or 'abcdef123456789'  # Use env or default
        self.base_url = 'https://api.stlouisfed.org/fred'
        self.series_map = {
            'GDP': 'GDP',
            'CPI': 'CPIAUCSL',
            'UNEMPLOYMENT': 'UNRATE',
            'FED_RATE': 'FEDFUNDS',
            'M2': 'M2SL',
            'TREASURY_10Y': 'DGS10',
            'TREASURY_2Y': 'DGS2',
            'VIX': 'VIXCLS',
            'DOLLAR': 'DEXUSEU',
            'HOUSING': 'HOUST',
            'RETAIL_SALES': 'RSXFS',
            'INDUSTRIAL_PRODUCTION': 'INDPRO'
        }
        self.cache = {}
        self.cache_ttl = 900  # 15 minutes
    
    def get_series(self, series_id: str, limit: int = 10) -> List[Dict]:
        """Get time series data"""
        # Check cache
        cache_key = f"{series_id}_{limit}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached['time'] < timedelta(seconds=self.cache_ttl):
                return cached['data']
        
        # Map common names to FRED series IDs
        fred_id = self.series_map.get(series_id.upper(), series_id)
        
        # Build URL
        params = {
            'series_id': fred_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'limit': limit,
            'sort_order': 'desc'
        }
        url = f"{self.base_url}/series/observations?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                observations = data.get('observations', [])
                
                # Process data
                processed = []
                for obs in observations:
                    try:
                        value = float(obs['value'])
                        processed.append({
                            'date': obs['date'],
                            'value': value,
                            'series': fred_id
                        })
                    except (ValueError, KeyError):
                        continue
                
                # Update cache
                self.cache[cache_key] = {
                    'data': processed,
                    'time': datetime.now()
                }
                
                return processed
                
        except Exception as e:
            return [{'error': str(e), 'series': fred_id}]
    
    def get_latest(self, series_id: str) -> Optional[Dict]:
        """Get latest data point"""
        data = self.get_series(series_id, limit=1)
        return data[0] if data else None
    
    def get_all_indicators(self) -> Dict:
        """Get all major economic indicators"""
        indicators = {}
        
        for name, fred_id in self.series_map.items():
            latest = self.get_latest(fred_id)
            if latest and 'error' not in latest:
                indicators[name] = latest
        
        return indicators
    
    def compare_periods(self, series_id: str, periods_back: int = 12) -> Dict:
        """Compare current value to past periods"""
        data = self.get_series(series_id, limit=periods_back + 1)
        
        if not data or len(data) < 2:
            return {'error': 'Insufficient data'}
        
        current = data[0]['value']
        previous = data[1]['value'] if len(data) > 1 else current
        year_ago = data[-1]['value'] if len(data) > periods_back else current
        
        return {
            'series': series_id,
            'current': current,
            'previous': previous,
            'year_ago': year_ago,
            'change_1m': ((current - previous) / previous) * 100 if previous else 0,
            'change_1y': ((current - year_ago) / year_ago) * 100 if year_ago else 0
        }