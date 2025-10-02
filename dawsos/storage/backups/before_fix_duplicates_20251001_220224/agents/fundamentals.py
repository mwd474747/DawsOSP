import urllib.request
import json
from typing import Dict, List, Optional

class FundamentalsCapability:
    """Company fundamentals and financial data"""
    
    def __init__(self, api_key: str = None):
        # Using Alpha Vantage (free tier available)
        # Get key at: https://www.alphavantage.co/support/#api-key
        self.api_key = api_key or 'your_alpha_vantage_key'
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
                
                overview = {
                    'symbol': data.get('Symbol'),
                    'name': data.get('Name'),
                    'sector': data.get('Sector'),
                    'industry': data.get('Industry'),
                    'market_cap': float(data.get('MarketCapitalization', 0)),
                    'pe_ratio': float(data.get('PERatio', 0) or 0),
                    'peg_ratio': float(data.get('PEGRatio', 0) or 0),
                    'book_value': float(data.get('BookValue', 0) or 0),
                    'dividend_yield': float(data.get('DividendYield', 0) or 0),
                    'eps': float(data.get('EPS', 0) or 0),
                    'revenue_ttm': float(data.get('RevenueTTM', 0) or 0),
                    'profit_margin': float(data.get('ProfitMargin', 0) or 0),
                    'beta': float(data.get('Beta', 0) or 0),
                    '52_week_high': float(data.get('52WeekHigh', 0) or 0),
                    '52_week_low': float(data.get('52WeekLow', 0) or 0)
                }
                
                # Cache results
                self.cache[cache_key] = {
                    'data': overview,
                    'time': datetime.now().timestamp()
                }
                
                return overview
                
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def get_income_statement(self, symbol: str) -> Dict:
        """Get income statement data"""
        params = {
            'function': 'INCOME_STATEMENT',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                # Get most recent annual report
                annual = data.get('annualReports', [{}])[0] if data.get('annualReports') else {}
                
                return {
                    'symbol': symbol,
                    'fiscal_year': annual.get('fiscalDateEnding'),
                    'revenue': float(annual.get('totalRevenue', 0) or 0),
                    'gross_profit': float(annual.get('grossProfit', 0) or 0),
                    'operating_income': float(annual.get('operatingIncome', 0) or 0),
                    'net_income': float(annual.get('netIncome', 0) or 0),
                    'ebitda': float(annual.get('ebitda', 0) or 0)
                }
                
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def get_balance_sheet(self, symbol: str) -> Dict:
        """Get balance sheet data"""
        params = {
            'function': 'BALANCE_SHEET',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                # Get most recent annual report
                annual = data.get('annualReports', [{}])[0] if data.get('annualReports') else {}
                
                return {
                    'symbol': symbol,
                    'fiscal_year': annual.get('fiscalDateEnding'),
                    'total_assets': float(annual.get('totalAssets', 0) or 0),
                    'total_liabilities': float(annual.get('totalLiabilities', 0) or 0),
                    'total_equity': float(annual.get('totalShareholderEquity', 0) or 0),
                    'cash': float(annual.get('cashAndCashEquivalentsAtCarryingValue', 0) or 0),
                    'debt': float(annual.get('longTermDebt', 0) or 0),
                    'current_ratio': self._calculate_current_ratio(annual)
                }
                
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def _calculate_current_ratio(self, data: Dict) -> float:
        """Calculate current ratio from balance sheet data"""
        current_assets = float(data.get('totalCurrentAssets', 0) or 0)
        current_liabilities = float(data.get('totalCurrentLiabilities', 1) or 1)
        return current_assets / current_liabilities if current_liabilities > 0 else 0
    
    def screen_value_stocks(self, max_pe: float = 20, min_dividend: float = 2) -> List[str]:
        """Screen for value stocks based on criteria"""
        # In production, would query a database or API
        # For demo, checking a few known value stocks
        candidates = ['KO', 'PG', 'JNJ', 'VZ', 'T', 'XOM', 'CVX', 'PFE']
        value_stocks = []
        
        for symbol in candidates:
            overview = self.get_overview(symbol)
            if 'error' not in overview:
                pe = overview.get('pe_ratio', 100)
                div_yield = overview.get('dividend_yield', 0)
                
                if pe < max_pe and div_yield > min_dividend:
                    value_stocks.append({
                        'symbol': symbol,
                        'pe_ratio': pe,
                        'dividend_yield': div_yield,
                        'name': overview.get('name')
                    })
        
        return value_stocks