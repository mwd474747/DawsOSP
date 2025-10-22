"""
Capability Router - Routes capability calls to appropriate data services

This router provides an abstraction layer between Trinity capabilities and data services.
It supports both MockDataService (for testing) and OpenBBService (for real data) with
identical interfaces, enabling seamless switching via a single flag.

Usage:
    # Use mock data (default)
    router = CapabilityRouter(use_real_data=False)
    result = router.route('can_fetch_stock_quotes', {'symbol': 'AAPL'})

    # Use real data (when OpenBB available)
    router = CapabilityRouter(use_real_data=True)
    result = router.route('can_fetch_stock_quotes', {'symbol': 'AAPL'})
"""

from typing import Dict, Any, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mock_data_service import MockDataService


class CapabilityRouter:
    """Routes capability calls to appropriate data service (mock or real)"""

    def __init__(self, use_real_data: bool = False):
        """
        Initialize router with data service

        Args:
            use_real_data: If True, attempt to use OpenBBService; if False (default),
                          use MockDataService
        """
        self.use_real_data = use_real_data

        if use_real_data:
            try:
                from services.openbb_service import OpenBBService
                self.data_service = OpenBBService()
                print("✅ CapabilityRouter: Using OpenBB real data service")
            except ImportError as e:
                print(f"⚠️ CapabilityRouter: OpenBB not available ({e}), falling back to mock data")
                self.data_service = MockDataService()
                self.use_real_data = False  # Update flag to reflect actual state
        else:
            self.data_service = MockDataService()
            print("✅ CapabilityRouter: Using mock data service")

    def route(self, capability: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route capability to appropriate service method

        Args:
            capability: Capability name (e.g., 'can_fetch_stock_quotes')
            context: Context dict with parameters (e.g., {'symbol': 'AAPL'})

        Returns:
            Dict with 'data' and 'error' keys matching OpenBB format

        Example:
            router = CapabilityRouter()
            result = router.route('can_fetch_stock_quotes', {'symbol': 'AAPL'})
            if result['error']:
                print(f"Error: {result['error']}")
            else:
                print(f"Price: {result['data']['price']}")
        """
        # Capability to method mapping
        CAPABILITY_MAP = {
            'can_fetch_stock_quotes': self._fetch_quote,
            'can_fetch_economic_data': self._fetch_economic,
            'can_fetch_fundamentals': self._fetch_fundamentals,
            'can_fetch_news': self._fetch_news,
            'can_calculate_risk_metrics': self._calculate_risk,
            'can_fetch_crypto_data': self._fetch_crypto,
            'can_detect_patterns': self._detect_patterns,
        }

        handler = CAPABILITY_MAP.get(capability)
        if handler:
            try:
                return handler(context)
            except Exception as e:
                return {
                    'data': None,
                    'error': f'Error routing capability {capability}: {str(e)}'
                }
        else:
            return {
                'data': None,
                'error': f'Unknown capability: {capability}. Available: {list(CAPABILITY_MAP.keys())}'
            }

    def _fetch_quote(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch stock quote via data service

        Args:
            context: Must contain 'symbol' key

        Returns:
            Dict with 'data' and 'error' keys
        """
        symbol = context.get('symbol')
        if not symbol:
            return {
                'data': None,
                'error': 'Missing required parameter: symbol'
            }

        return self.data_service.get_equity_quote(symbol)

    def _fetch_economic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch economic data via data service

        Args:
            context: Must contain 'indicators' key (list of series IDs)

        Returns:
            Dict with 'data' and 'error' keys
        """
        indicators = context.get('indicators', [])
        if not indicators:
            # Default to common indicators if none specified
            indicators = ['GDP', 'CPIAUCSL', 'UNRATE']

        start = context.get('start')
        end = context.get('end')

        return self.data_service.get_economic_indicators(indicators, start, end)

    def _fetch_fundamentals(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch company fundamentals via data service

        Args:
            context: Must contain 'symbol' key

        Returns:
            Dict with 'data' and 'error' keys
        """
        symbol = context.get('symbol')
        if not symbol:
            return {
                'data': None,
                'error': 'Missing required parameter: symbol'
            }

        return self.data_service.get_equity_fundamentals(symbol)

    def _fetch_news(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch financial news via data service

        Args:
            context: May contain 'symbol', 'category', 'limit' keys

        Returns:
            Dict with 'data' and 'error' keys
        """
        symbol = context.get('symbol')
        category = context.get('category')
        limit = context.get('limit', 5)

        return self.data_service.get_news(symbol, category, limit)

    def _calculate_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate risk metrics using historical data

        This capability combines historical price data with risk calculations.

        Args:
            context: Must contain 'symbol' or 'holdings' key

        Returns:
            Dict with 'data' and 'error' keys
        """
        symbol = context.get('symbol')
        holdings = context.get('holdings', [])

        if not symbol and not holdings:
            return {
                'data': None,
                'error': 'Missing required parameter: symbol or holdings'
            }

        # For single symbol
        if symbol:
            historical = self.data_service.get_historical_prices(symbol)
            if historical['error']:
                return historical

            # Calculate simple metrics from historical data
            prices = [day['close'] for day in historical['data']]
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]

            volatility = self._calculate_volatility(returns)
            max_drawdown = self._calculate_max_drawdown(prices)

            return {
                'data': {
                    'symbol': symbol,
                    'volatility_30d': volatility,
                    'max_drawdown_30d': max_drawdown,
                    'current_price': prices[-1],
                    'price_change_30d': (prices[-1] - prices[0]) / prices[0],
                    'timestamp': '2025-10-20',
                    'source': 'mock_data' if not self.use_real_data else 'openbb'
                },
                'error': None
            }

        # For portfolio (multiple holdings)
        else:
            portfolio_metrics = []
            for holding in holdings:
                if isinstance(holding, dict):
                    sym = holding.get('symbol')
                else:
                    sym = holding

                metrics = self._calculate_risk({'symbol': sym})
                if not metrics['error']:
                    portfolio_metrics.append(metrics['data'])

            return {
                'data': {
                    'holdings': portfolio_metrics,
                    'portfolio_size': len(portfolio_metrics),
                    'timestamp': '2025-10-20',
                    'source': 'mock_data' if not self.use_real_data else 'openbb'
                },
                'error': None if portfolio_metrics else 'No valid holdings data'
            }

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate annualized volatility from returns"""
        if not returns:
            return 0.0

        # Simple standard deviation
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        volatility = (variance ** 0.5) * (252 ** 0.5)  # Annualized

        return round(volatility * 100, 2)  # Return as percentage

    def _calculate_max_drawdown(self, prices: List[float]) -> float:
        """Calculate maximum drawdown from price series"""
        if not prices:
            return 0.0

        max_price = prices[0]
        max_dd = 0.0

        for price in prices:
            if price > max_price:
                max_price = price
            dd = (price - max_price) / max_price
            if dd < max_dd:
                max_dd = dd

        return round(max_dd * 100, 2)  # Return as percentage

    def _fetch_crypto(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch cryptocurrency data via data service

        Args:
            context: Must contain 'symbol' key (e.g., 'BTC-USD')

        Returns:
            Dict with 'data' and 'error' keys
        """
        # Placeholder - crypto not in mock data yet
        return {
            'data': None,
            'error': 'Cryptocurrency data not available in mock service'
        }

    def _detect_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect chart patterns using historical data

        This is a placeholder - actual pattern detection would be done by
        the pattern_spotter agent using the historical price data.

        Args:
            context: Must contain 'symbol' key

        Returns:
            Dict with 'data' and 'error' keys
        """
        symbol = context.get('symbol')
        if not symbol:
            return {
                'data': None,
                'error': 'Missing required parameter: symbol'
            }

        # This capability should delegate to pattern_spotter agent
        # For now, return a placeholder indicating agent routing needed
        return {
            'data': None,
            'error': 'Pattern detection requires pattern_spotter agent (not data service)'
        }

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the current data service

        Returns:
            Dict with service type and status
        """
        service_type = 'OpenBB' if self.use_real_data else 'Mock'
        service_class = self.data_service.__class__.__name__

        return {
            'service_type': service_type,
            'service_class': service_class,
            'use_real_data': self.use_real_data,
            'available_capabilities': [
                'can_fetch_stock_quotes',
                'can_fetch_economic_data',
                'can_fetch_fundamentals',
                'can_fetch_news',
                'can_calculate_risk_metrics'
            ]
        }

    def list_capabilities(self) -> List[str]:
        """
        List all supported capabilities

        Returns:
            List of capability names
        """
        return [
            'can_fetch_stock_quotes',
            'can_fetch_economic_data',
            'can_fetch_fundamentals',
            'can_fetch_news',
            'can_calculate_risk_metrics',
            'can_fetch_crypto_data',
            'can_detect_patterns'
        ]

    def test_capability(self, capability: str) -> Dict[str, Any]:
        """
        Test a capability with default parameters

        Args:
            capability: Capability name to test

        Returns:
            Dict with test results
        """
        test_contexts = {
            'can_fetch_stock_quotes': {'symbol': 'AAPL'},
            'can_fetch_economic_data': {'indicators': ['GDP']},
            'can_fetch_fundamentals': {'symbol': 'AAPL'},
            'can_fetch_news': {'symbol': 'AAPL', 'limit': 3},
            'can_calculate_risk_metrics': {'symbol': 'AAPL'}
        }

        context = test_contexts.get(capability, {})
        result = self.route(capability, context)

        return {
            'capability': capability,
            'test_context': context,
            'success': result['error'] is None,
            'result': result
        }
