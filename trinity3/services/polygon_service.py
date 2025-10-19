"""Polygon.io API Service for real-time market data"""

import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd

class PolygonService:
    """Service for fetching real-time market data from Polygon.io"""
    
    def __init__(self):
        self.api_key = os.getenv('POLYGON_API_KEY', '')
        self.base_url = 'https://api.polygon.io'
        self.enabled = bool(self.api_key)
        
    def is_configured(self) -> bool:
        """Check if Polygon API is configured"""
        return self.enabled
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        if not self.enabled:
            return {
                'status': 'unavailable',
                'message': 'Polygon API key not configured'
            }
        
        try:
            url = f"{self.base_url}/v1/marketstatus/now?apiKey={self.api_key}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'open' if data.get('market') == 'open' else 'closed',
                    'afterHours': data.get('afterHours', 'closed'),
                    'exchanges': data.get('exchanges', {}),
                    'currencies': data.get('currencies', {})
                }
        except Exception as e:
            print(f"Polygon market status error: {e}")
        
        return {'status': 'unknown', 'message': 'Failed to fetch market status'}
    
    def get_ticker_snapshot(self, ticker: str) -> Dict[str, Any]:
        """Get snapshot data for a ticker"""
        if not self.enabled:
            return {}
        
        try:
            url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}?apiKey={self.api_key}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'ticker' in data:
                    ticker_data = data['ticker']
                    return {
                        'symbol': ticker_data.get('ticker'),
                        'price': ticker_data.get('day', {}).get('c'),
                        'open': ticker_data.get('day', {}).get('o'),
                        'high': ticker_data.get('day', {}).get('h'),
                        'low': ticker_data.get('day', {}).get('l'),
                        'volume': ticker_data.get('day', {}).get('v'),
                        'prevClose': ticker_data.get('prevDay', {}).get('c'),
                        'change': ticker_data.get('todaysChange'),
                        'changePercent': ticker_data.get('todaysChangePerc'),
                        'updated': ticker_data.get('updated')
                    }
        except Exception as e:
            print(f"Polygon ticker snapshot error for {ticker}: {e}")
        
        return {}
    
    def get_aggregates(self, ticker: str, multiplier: int = 1, timespan: str = 'day', from_date: str = None, to_date: str = None) -> pd.DataFrame:
        """Get aggregate bars for a ticker"""
        if not self.enabled:
            return pd.DataFrame()
        
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}?adjusted=true&sort=asc&limit=5000&apiKey={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data:
                    df = pd.DataFrame(data['results'])
                    df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
                    df.rename(columns={
                        'o': 'open',
                        'h': 'high',
                        'l': 'low',
                        'c': 'close',
                        'v': 'volume',
                        't': 'timestamp_ms',
                        'vw': 'vwap',
                        'n': 'transactions'
                    }, inplace=True)
                    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'vwap']]
        except Exception as e:
            print(f"Polygon aggregates error for {ticker}: {e}")
        
        return pd.DataFrame()
    
    def get_market_movers(self, direction: str = 'gainers') -> List[Dict[str, Any]]:
        """Get top gainers or losers"""
        if not self.enabled:
            return []
        
        try:
            # Get snapshots for all tickers
            url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers?apiKey={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tickers = data.get('tickers', [])
                
                # Calculate change percentages and sort
                movers = []
                for ticker in tickers:
                    change_pct = ticker.get('todaysChangePerc', 0)
                    if change_pct != 0:
                        movers.append({
                            'symbol': ticker.get('ticker'),
                            'price': ticker.get('day', {}).get('c'),
                            'change': ticker.get('todaysChange'),
                            'changePercent': change_pct,
                            'volume': ticker.get('day', {}).get('v')
                        })
                
                # Sort by change percentage
                if direction == 'gainers':
                    movers.sort(key=lambda x: x['changePercent'], reverse=True)
                else:
                    movers.sort(key=lambda x: x['changePercent'])
                
                return movers[:10]  # Return top 10
        except Exception as e:
            print(f"Polygon market movers error: {e}")
        
        return []
    
    def get_news(self, ticker: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest news articles"""
        if not self.enabled:
            return []
        
        try:
            if ticker:
                url = f"{self.base_url}/v2/reference/news?ticker={ticker}&limit={limit}&apiKey={self.api_key}"
            else:
                url = f"{self.base_url}/v2/reference/news?limit={limit}&apiKey={self.api_key}"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for article in data.get('results', []):
                    articles.append({
                        'title': article.get('title'),
                        'author': article.get('author'),
                        'published': article.get('published_utc'),
                        'url': article.get('article_url'),
                        'summary': article.get('description', '')[:200],
                        'tickers': article.get('tickers', [])
                    })
                return articles
        except Exception as e:
            print(f"Polygon news error: {e}")
        
        return []
    
    def get_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """Calculate technical indicators from price data"""
        df = self.get_aggregates(ticker)
        
        if df.empty:
            return {}
        
        try:
            # Calculate simple technical indicators
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            df['SMA_50'] = df['close'].rolling(window=50).mean()
            df['RSI'] = self._calculate_rsi(df['close'])
            
            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            return {
                'price': latest['close'],
                'sma20': latest['SMA_20'],
                'sma50': latest['SMA_50'],
                'rsi': latest['RSI'],
                'volume': latest['volume'],
                'trend': 'up' if latest['close'] > prev['close'] else 'down'
            }
        except Exception as e:
            print(f"Technical indicators error: {e}")
            return {}
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        deltas = prices.diff()
        gain = deltas.where(deltas > 0, 0)
        loss = -deltas.where(deltas < 0, 0)
        
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi