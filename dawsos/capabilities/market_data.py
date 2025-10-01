import os
import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class MarketDataCapability:
    """Financial Modeling Prep API integration (Pro version)"""
    
    def __init__(self):
        # Get FMP API key from environment
        self.api_key = os.getenv('FMP_API_KEY')
        self.base_url = 'https://financialmodelingprep.com/api'
        self.cache = {}
        self.cache_ttl = 60  # 1 minute for real-time data
        
    def get_quote(self, symbol: str) -> Dict:
        """Get real-time stock quote"""
        # Check cache
        if symbol in self.cache:
            cached = self.cache[symbol]
            if datetime.now() - cached['time'] < timedelta(seconds=self.cache_ttl):
                return cached['data']
        
        url = f"{self.base_url}/v3/quote/{symbol}?apikey={self.api_key}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                if data:
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
                    self.cache[symbol] = {
                        'data': quote,
                        'time': datetime.now()
                    }
                    
                    return quote
                
                return {'symbol': symbol, 'error': 'No data available'}
                
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def get_historical(self, symbol: str, period: str = '1M', interval: str = '1d') -> List[Dict]:
        """Get historical price data
        period: 1D, 5D, 1M, 3M, 6M, 1Y, 3Y, 5Y, 10Y, max
        interval: 1min, 5min, 15min, 30min, 1hour, 4hour, 1d
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
    
    def get_company_profile(self, symbol: str) -> Dict:
        """Get comprehensive company profile"""
        url = f"{self.base_url}/v3/profile/{symbol}?apikey={self.api_key}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                if data:
                    profile = data[0]
                    return {
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
                
                return {'symbol': symbol, 'error': 'No profile data'}
                
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def get_financials(self, symbol: str, statement: str = 'income', period: str = 'annual') -> List[Dict]:
        """Get financial statements
        statement: income, balance, cash-flow
        period: annual, quarter
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
    
    def get_key_metrics(self, symbol: str, period: str = 'annual') -> List[Dict]:
        """Get key financial metrics (Pro feature)"""
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
    
    def get_analyst_estimates(self, symbol: str) -> List[Dict]:
        """Get analyst estimates (Pro feature)"""
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
    
    def get_insider_trading(self, symbol: str) -> List[Dict]:
        """Get insider trading data (Pro feature)"""
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
    
    def get_institutional_holders(self, symbol: str) -> List[Dict]:
        """Get institutional ownership (Pro feature)"""
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
    
    def screen_stocks(self, criteria: Dict) -> List[Dict]:
        """Advanced stock screener (Pro feature)"""
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
    
    def get_market_movers(self, type: str = 'gainers') -> List[Dict]:
        """Get market movers
        type: gainers, losers, actives
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