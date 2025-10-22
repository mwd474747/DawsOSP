"""
Mock Data Service - Provides realistic mock data matching OpenBB response format

This service provides stub data for testing Trinity 3.0 patterns without requiring
OpenBB Platform installation or API keys. All mock data matches OpenBB response format
exactly to ensure compatibility when switching to real data.

Usage:
    service = MockDataService()
    quote = service.get_equity_quote('AAPL')
    econ = service.get_economic_indicators(['GDP', 'CPIAUCSL'])
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random


class MockDataService:
    """Provides realistic mock data matching OpenBB response format"""

    def __init__(self):
        """Initialize mock data service with realistic datasets"""
        self.cache = {}
        self._load_mock_datasets()

    def _load_mock_datasets(self):
        """Load realistic mock data for common symbols/indicators"""

        # Top 10 stock quotes (realistic data as of Oct 2025)
        self.mock_quotes = {
            'AAPL': {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'price': 178.25,
                'change': 2.15,
                'percent_change': 1.22,
                'volume': 52_000_000,
                'market_cap': 2_800_000_000_000,
                'pe_ratio': 29.5,
                'day_high': 179.50,
                'day_low': 176.80,
                '52_week_high': 199.62,
                '52_week_low': 164.08,
                'timestamp': '2025-10-20T16:00:00Z',
                'source': 'mock_data',
                'exchange': 'NASDAQ'
            },
            'MSFT': {
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'price': 412.85,
                'change': -1.25,
                'percent_change': -0.30,
                'volume': 24_500_000,
                'market_cap': 3_100_000_000_000,
                'pe_ratio': 35.2,
                'day_high': 415.20,
                'day_low': 410.50,
                '52_week_high': 430.82,
                '52_week_low': 309.45,
                'timestamp': '2025-10-20T16:00:00Z',
                'source': 'mock_data',
                'exchange': 'NASDAQ'
            },
            'GOOGL': {
                'symbol': 'GOOGL',
                'name': 'Alphabet Inc.',
                'price': 142.68,
                'change': 0.85,
                'percent_change': 0.60,
                'volume': 18_200_000,
                'market_cap': 1_800_000_000_000,
                'pe_ratio': 24.3,
                'day_high': 143.50,
                'day_low': 141.90,
                '52_week_high': 155.27,
                '52_week_low': 121.46,
                'timestamp': '2025-10-20T16:00:00Z',
                'source': 'mock_data',
                'exchange': 'NASDAQ'
            },
            'AMZN': {
                'symbol': 'AMZN',
                'name': 'Amazon.com Inc.',
                'price': 178.35,
                'change': 3.20,
                'percent_change': 1.83,
                'volume': 42_000_000,
                'market_cap': 1_850_000_000_000,
                'pe_ratio': 52.1,
                'day_high': 180.25,
                'day_low': 176.50,
                '52_week_high': 191.70,
                '52_week_low': 139.52,
                'timestamp': '2025-10-20T16:00:00Z',
                'source': 'mock_data',
                'exchange': 'NASDAQ'
            },
            'NVDA': {
                'symbol': 'NVDA',
                'name': 'NVIDIA Corporation',
                'price': 875.40,
                'change': 12.50,
                'percent_change': 1.45,
                'volume': 38_500_000,
                'market_cap': 2_150_000_000_000,
                'pe_ratio': 68.9,
                'day_high': 882.50,
                'day_low': 868.30,
                '52_week_high': 974.00,
                '52_week_low': 455.82,
                'timestamp': '2025-10-20T16:00:00Z',
                'source': 'mock_data',
                'exchange': 'NASDAQ'
            },
            'TSLA': {
                'symbol': 'TSLA',
                'name': 'Tesla, Inc.',
                'price': 242.68,
                'change': -4.20,
                'percent_change': -1.70,
                'volume': 95_000_000,
                'market_cap': 770_000_000_000,
                'pe_ratio': 72.5,
                'day_high': 248.50,
                'day_low': 240.10,
                '52_week_high': 299.29,
                '52_week_low': 152.37,
                'timestamp': '2025-10-20T16:00:00Z',
                'source': 'mock_data',
                'exchange': 'NASDAQ'
            },
            'META': {
                'symbol': 'META',
                'name': 'Meta Platforms Inc.',
                'price': 498.25,
                'change': 5.80,
                'percent_change': 1.18,
                'volume': 16_800_000,
                'market_cap': 1_280_000_000_000,
                'pe_ratio': 28.4,
                'day_high': 502.30,
                'day_low': 495.10,
                '52_week_high': 531.49,
                '52_week_low': 279.44,
                'timestamp': '2025-10-20T16:00:00Z',
                'source': 'mock_data',
                'exchange': 'NASDAQ'
            },
            'JPM': {
                'symbol': 'JPM',
                'name': 'JPMorgan Chase & Co.',
                'price': 198.45,
                'change': 1.35,
                'percent_change': 0.69,
                'volume': 8_900_000,
                'market_cap': 575_000_000_000,
                'pe_ratio': 11.2,
                'day_high': 199.80,
                'day_low': 196.90,
                '52_week_high': 207.98,
                '52_week_low': 135.19,
                'timestamp': '2025-10-20T16:00:00Z',
                'source': 'mock_data',
                'exchange': 'NYSE'
            },
            'V': {
                'symbol': 'V',
                'name': 'Visa Inc.',
                'price': 285.62,
                'change': 2.10,
                'percent_change': 0.74,
                'volume': 6_200_000,
                'market_cap': 590_000_000_000,
                'pe_ratio': 31.8,
                'day_high': 287.50,
                'day_low': 283.40,
                '52_week_high': 293.07,
                '52_week_low': 227.81,
                'timestamp': '2025-10-20T16:00:00Z',
                'source': 'mock_data',
                'exchange': 'NYSE'
            },
            'WMT': {
                'symbol': 'WMT',
                'name': 'Walmart Inc.',
                'price': 168.35,
                'change': 0.95,
                'percent_change': 0.57,
                'volume': 7_500_000,
                'market_cap': 455_000_000_000,
                'pe_ratio': 27.6,
                'day_high': 169.20,
                'day_low': 167.10,
                '52_week_high': 172.58,
                '52_week_low': 142.53,
                'timestamp': '2025-10-20T16:00:00Z',
                'source': 'mock_data',
                'exchange': 'NYSE'
            }
        }

        # Economic indicators (realistic Q3 2025 data)
        self.mock_economic = {
            'GDP': {
                'series_id': 'GDP',
                'name': 'Gross Domestic Product',
                'value': 27850.0,
                'units': 'Billions of Dollars',
                'frequency': 'Quarterly',
                'timestamp': '2025-Q3',
                'source': 'mock_data',
                'change': 2.8,
                'change_percent': 0.10
            },
            'CPIAUCSL': {
                'series_id': 'CPIAUCSL',
                'name': 'Consumer Price Index for All Urban Consumers',
                'value': 315.2,
                'units': 'Index 1982-1984=100',
                'frequency': 'Monthly',
                'timestamp': '2025-09',
                'source': 'mock_data',
                'change': 0.3,
                'change_percent': 0.10,
                'yoy_change': 2.4
            },
            'UNRATE': {
                'series_id': 'UNRATE',
                'name': 'Unemployment Rate',
                'value': 3.8,
                'units': 'Percent',
                'frequency': 'Monthly',
                'timestamp': '2025-09',
                'source': 'mock_data',
                'change': -0.1,
                'change_percent': -2.56
            },
            'FEDFUNDS': {
                'series_id': 'FEDFUNDS',
                'name': 'Federal Funds Effective Rate',
                'value': 5.33,
                'units': 'Percent',
                'frequency': 'Monthly',
                'timestamp': '2025-09',
                'source': 'mock_data',
                'change': 0.0,
                'change_percent': 0.0
            },
            'DGS10': {
                'series_id': 'DGS10',
                'name': '10-Year Treasury Constant Maturity Rate',
                'value': 4.68,
                'units': 'Percent',
                'frequency': 'Daily',
                'timestamp': '2025-10-20',
                'source': 'mock_data',
                'change': 0.05,
                'change_percent': 1.08
            },
            'DGS2': {
                'series_id': 'DGS2',
                'name': '2-Year Treasury Constant Maturity Rate',
                'value': 4.95,
                'units': 'Percent',
                'frequency': 'Daily',
                'timestamp': '2025-10-20',
                'source': 'mock_data',
                'change': 0.02,
                'change_percent': 0.41
            }
        }

        # Fundamentals (PE, PB, ROE, etc.)
        self.mock_fundamentals = {
            'AAPL': {
                'symbol': 'AAPL',
                'pe_ratio': 29.5,
                'pb_ratio': 43.2,
                'ps_ratio': 7.8,
                'dividend_yield': 0.52,
                'roe': 147.3,
                'roa': 27.8,
                'gross_margin': 44.1,
                'operating_margin': 30.2,
                'net_margin': 25.3,
                'debt_to_equity': 1.72,
                'current_ratio': 0.98,
                'quick_ratio': 0.85,
                'timestamp': '2025-Q3',
                'source': 'mock_data'
            },
            'MSFT': {
                'symbol': 'MSFT',
                'pe_ratio': 35.2,
                'pb_ratio': 11.8,
                'ps_ratio': 12.5,
                'dividend_yield': 0.75,
                'roe': 42.5,
                'roa': 18.3,
                'gross_margin': 69.8,
                'operating_margin': 44.2,
                'net_margin': 36.7,
                'debt_to_equity': 0.45,
                'current_ratio': 1.78,
                'quick_ratio': 1.65,
                'timestamp': '2025-Q3',
                'source': 'mock_data'
            }
            # Add more as needed
        }

        # News headlines
        self.mock_news = {
            'AAPL': [
                {
                    'title': 'Apple Reports Strong iPhone 15 Sales in Q3',
                    'summary': 'Apple exceeded analyst expectations with robust iPhone sales...',
                    'source': 'Bloomberg',
                    'timestamp': '2025-10-19T14:30:00Z',
                    'sentiment': 'positive',
                    'url': 'https://example.com/news/1'
                },
                {
                    'title': 'Apple Announces New AI Features for iOS 19',
                    'summary': 'Cupertino unveils major AI integration across its product line...',
                    'source': 'Reuters',
                    'timestamp': '2025-10-18T10:15:00Z',
                    'sentiment': 'positive',
                    'url': 'https://example.com/news/2'
                },
                {
                    'title': 'Supply Chain Concerns Emerge for Apple Suppliers',
                    'summary': 'Manufacturing delays reported in Asia affecting production...',
                    'source': 'Wall Street Journal',
                    'timestamp': '2025-10-17T09:45:00Z',
                    'sentiment': 'negative',
                    'url': 'https://example.com/news/3'
                }
            ],
            'MSFT': [
                {
                    'title': 'Microsoft Cloud Revenue Surges 25% Year-Over-Year',
                    'summary': 'Azure continues to gain market share against competitors...',
                    'source': 'CNBC',
                    'timestamp': '2025-10-19T16:00:00Z',
                    'sentiment': 'positive',
                    'url': 'https://example.com/news/4'
                },
                {
                    'title': 'Microsoft Expands AI Partnership with OpenAI',
                    'summary': 'New $10B investment strengthens AI infrastructure...',
                    'source': 'TechCrunch',
                    'timestamp': '2025-10-18T13:20:00Z',
                    'sentiment': 'positive',
                    'url': 'https://example.com/news/5'
                }
            ]
        }

    def get_equity_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch stock quote via mock data

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Dict with 'data' and 'error' keys matching OpenBB format
        """
        if symbol in self.mock_quotes:
            return {
                'data': self.mock_quotes[symbol],
                'error': None
            }
        else:
            return {
                'data': None,
                'error': f'Mock data not available for symbol: {symbol}'
            }

    def get_equity_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch company fundamentals via mock data

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Dict with 'data' and 'error' keys matching OpenBB format
        """
        if symbol in self.mock_fundamentals:
            return {
                'data': self.mock_fundamentals[symbol],
                'error': None
            }
        else:
            # Return partial fundamentals if quote exists
            if symbol in self.mock_quotes:
                return {
                    'data': {
                        'symbol': symbol,
                        'pe_ratio': self.mock_quotes[symbol].get('pe_ratio', 20.0),
                        'market_cap': self.mock_quotes[symbol].get('market_cap', 0),
                        'timestamp': '2025-Q3',
                        'source': 'mock_data',
                        'note': 'Partial fundamentals from quote data'
                    },
                    'error': None
                }
            else:
                return {
                    'data': None,
                    'error': f'Mock fundamentals not available for symbol: {symbol}'
                }

    def get_economic_indicators(self, indicators: List[str],
                               start: Optional[str] = None,
                               end: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch economic indicators via mock data

        Args:
            indicators: List of FRED series IDs (e.g., ['GDP', 'CPIAUCSL'])
            start: Start date (ignored for mock data)
            end: End date (ignored for mock data)

        Returns:
            Dict with 'data' and 'error' keys matching OpenBB format
        """
        results = {}
        missing = []

        for indicator in indicators:
            if indicator in self.mock_economic:
                results[indicator] = self.mock_economic[indicator]
            else:
                missing.append(indicator)

        if results:
            return {
                'data': results,
                'error': f'Missing indicators: {missing}' if missing else None
            }
        else:
            return {
                'data': None,
                'error': f'No mock data available for indicators: {indicators}'
            }

    def get_news(self, symbol: Optional[str] = None,
                category: Optional[str] = None,
                limit: int = 5) -> Dict[str, Any]:
        """
        Fetch financial news via mock data

        Args:
            symbol: Stock ticker symbol (optional)
            category: News category (optional, ignored for mock)
            limit: Max number of news items

        Returns:
            Dict with 'data' and 'error' keys matching OpenBB format
        """
        if symbol and symbol in self.mock_news:
            news_items = self.mock_news[symbol][:limit]
            return {
                'data': news_items,
                'error': None
            }
        elif symbol:
            return {
                'data': [],
                'error': f'No mock news available for symbol: {symbol}'
            }
        else:
            # Return general market news (combine all)
            all_news = []
            for items in self.mock_news.values():
                all_news.extend(items)
            return {
                'data': all_news[:limit],
                'error': None
            }

    def get_market_news(self, limit: int = 10) -> Dict[str, Any]:
        """
        Fetch general market news via mock data

        Args:
            limit: Max number of news items

        Returns:
            Dict with 'data' and 'error' keys matching OpenBB format
        """
        return self.get_news(symbol=None, limit=limit)

    def get_historical_prices(self, symbol: str,
                            start: Optional[str] = None,
                            end: Optional[str] = None,
                            interval: str = '1d') -> Dict[str, Any]:
        """
        Fetch historical prices via mock data

        Args:
            symbol: Stock ticker symbol
            start: Start date
            end: End date
            interval: Time interval (1d, 1h, etc.)

        Returns:
            Dict with 'data' and 'error' keys matching OpenBB format
        """
        if symbol not in self.mock_quotes:
            return {
                'data': None,
                'error': f'Mock historical data not available for symbol: {symbol}'
            }

        # Generate simple mock OHLCV data (last 30 days)
        current_price = self.mock_quotes[symbol]['price']
        historical_data = []

        for i in range(30, 0, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            # Simulate price variation (+/- 2% random walk)
            variation = random.uniform(-0.02, 0.02)
            price = current_price * (1 + variation * i / 30)

            historical_data.append({
                'date': date,
                'open': price * 0.995,
                'high': price * 1.01,
                'low': price * 0.99,
                'close': price,
                'volume': int(self.mock_quotes[symbol]['volume'] * random.uniform(0.8, 1.2)),
                'source': 'mock_data'
            })

        return {
            'data': historical_data,
            'error': None
        }

    def get_options_chain(self, symbol: str,
                         expiration: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch options chain via mock data (placeholder)

        Args:
            symbol: Stock ticker symbol
            expiration: Expiration date

        Returns:
            Dict with 'data' and 'error' keys
        """
        return {
            'data': None,
            'error': 'Options data not available in mock service (requires premium API)'
        }

    def get_market_breadth(self, index: str = 'SPX') -> Dict[str, Any]:
        """
        Fetch market breadth indicators via mock data (placeholder)

        Args:
            index: Market index

        Returns:
            Dict with 'data' and 'error' keys
        """
        return {
            'data': {
                'index': index,
                'advance_decline_ratio': 1.35,
                'new_highs': 125,
                'new_lows': 42,
                'timestamp': '2025-10-20',
                'source': 'mock_data'
            },
            'error': None
        }

    def get_sector_performance(self) -> Dict[str, Any]:
        """
        Fetch sector performance via mock data

        Returns:
            Dict with 'data' and 'error' keys matching OpenBB format
        """
        sectors = {
            'Technology': {'return_1d': 1.25, 'return_1w': 2.80, 'return_1m': 5.60},
            'Healthcare': {'return_1d': 0.45, 'return_1w': 1.20, 'return_1m': 3.10},
            'Financials': {'return_1d': 0.75, 'return_1w': 1.95, 'return_1m': 4.20},
            'Consumer Discretionary': {'return_1d': -0.35, 'return_1w': 0.80, 'return_1m': 2.40},
            'Energy': {'return_1d': -1.10, 'return_1w': -2.30, 'return_1m': -0.50},
            'Industrials': {'return_1d': 0.55, 'return_1w': 1.45, 'return_1m': 3.80},
            'Materials': {'return_1d': -0.20, 'return_1w': 0.60, 'return_1m': 1.90},
            'Real Estate': {'return_1d': 0.30, 'return_1w': 0.90, 'return_1m': 2.20},
            'Utilities': {'return_1d': 0.15, 'return_1w': 0.50, 'return_1m': 1.50},
            'Communication Services': {'return_1d': 0.85, 'return_1w': 2.10, 'return_1m': 4.50}
        }

        return {
            'data': {
                'sectors': sectors,
                'timestamp': '2025-10-20',
                'source': 'mock_data'
            },
            'error': None
        }

    def get_insider_trading(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """
        Fetch insider trading data via mock data (placeholder)

        Args:
            symbol: Stock ticker symbol
            limit: Max number of transactions

        Returns:
            Dict with 'data' and 'error' keys
        """
        return {
            'data': None,
            'error': 'Insider trading data not available in mock service'
        }

    def get_analyst_estimates(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch analyst estimates via mock data (placeholder)

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dict with 'data' and 'error' keys
        """
        return {
            'data': None,
            'error': 'Analyst estimates not available in mock service'
        }
