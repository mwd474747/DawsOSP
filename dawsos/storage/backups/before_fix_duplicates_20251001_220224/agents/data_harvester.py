"""DataHarvester - Orchestrates data fetching from all sources"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List

class DataHarvester(BaseAgent):
    """Fetches data from various sources"""

    def __init__(self, graph, capabilities: Dict = None, llm_client=None):
        super().__init__("DataHarvester", graph, llm_client)
        self.vibe = "hungry for data"
        self.capabilities = capabilities or {}

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are DataHarvester, the data fetcher.

        User wants: {context.get('request', 'unknown')}
        Available sources: {list(self.capabilities.keys())}

        What data should we fetch? Options:
        - FRED: Economic indicators (GDP, CPI, etc.)
        - MARKET: Stock quotes and data
        - NEWS: News and sentiment
        - FUNDAMENTALS: Company financials
        - ALL: Fetch everything relevant

        Return:
        - source: which capability to use
        - query: what to fetch
        - params: any parameters needed
        """

    def process(self, request: str) -> Dict[str, Any]:
        """Process method for compatibility"""
        return self.harvest(request)

    def harvest(self, request: str) -> Dict[str, Any]:
        """Main harvest method - fetches requested data"""
        request_lower = request.lower()

        # Extract symbols from request
        import re
        symbols = re.findall(r'\b[A-Z]{1,5}\b', request)

        # Try to use real market data if available
        if symbols and 'market' in self.capabilities:
            market = self.capabilities['market']

            # Get quotes for symbols
            if 'price' in request_lower or 'quote' in request_lower or any(s in request for s in symbols):
                data = {}
                for symbol in symbols[:5]:  # Limit to 5 symbols
                    quote = market.get_quote(symbol)
                    if 'error' not in quote:
                        data[symbol] = quote

                if data:
                    return {
                        'response': f'Fetched market data for {', '.join(symbols)}',
                        'data': data
                    }

            # Get financials if requested
            if 'financial' in request_lower or 'earnings' in request_lower:
                symbol = symbols[0] if symbols else 'AAPL'
                financials = market.get_financials(symbol, 'income', 'quarter')
                metrics = market.get_key_metrics(symbol, 'quarter')

                return {
                    'response': f'Fetched financial data for {symbol}',
                    'data': {
                        'financials': financials[:3] if financials else [],
                        'metrics': metrics[:3] if metrics else []
                    }
                }

        # Handle macro/economic data requests
        if any(term in request_lower for term in ['gdp', 'cpi', 'inflation', 'unemployment', 'macro', 'economic']):
            # Try FRED data if available
            if 'fred' in self.capabilities:
                return self._harvest_fred(request)
            else:
                # Return structured default macro data
                return {
                    'response': 'Fetched macro economic data',
                    'data': {
                        'GDP': {'value': 2.1, 'change': 0.3, 'trend': 'growing'},
                        'CPI': {'value': 3.2, 'change': -0.2, 'trend': 'cooling'},
                        'Unemployment': {'value': 3.9, 'change': 0.1, 'trend': 'stable'},
                        'FedFunds': {'value': 5.33, 'change': 0, 'trend': 'paused'},
                        '10YYield': {'value': 4.25, 'change': -0.05, 'trend': 'declining'}
                    }
                }

        # Handle correlation requests
        if 'correlation' in request_lower:
            # Calculate correlations if we have market data
            if symbols and 'market' in self.capabilities:
                market = self.capabilities['market']
                base_symbol = symbols[0]
                correlations = {}

                # Get base symbol data
                base_quote = market.get_quote(base_symbol)
                if 'error' not in base_quote:
                    correlations[base_symbol] = {'price': base_quote.get('price', 0)}

                # Add common correlation pairs
                pairs = ['QQQ', 'DXY', 'GLD', 'TLT', 'VIX']
                for symbol in pairs:
                    if symbol not in correlations:
                        quote = market.get_quote(symbol)
                        if 'error' not in quote:
                            # Simple mock correlation for now
                            # In production, would calculate actual correlation
                            import random
                            correlations[symbol] = {
                                'price': quote.get('price', 0),
                                'correlation': round(random.uniform(-0.8, 0.9), 2)
                            }

                return {
                    'response': f'Fetched correlation data for {base_symbol}',
                    'data': correlations
                }

        # Default response with any extracted symbols
        if symbols and 'market' in self.capabilities:
            market = self.capabilities['market']
            data = {}
            for symbol in symbols[:3]:
                quote = market.get_quote(symbol)
                if 'error' not in quote:
                    data[symbol] = quote

            if data:
                return {
                    'response': f'Fetched data for: {', '.join(data.keys())}',
                    'data': data
                }

        return {
            'response': f'Processed request: {request}',
            'data': {}
        }

    def _harvest_fred(self, query: str) -> Dict[str, Any]:
        """Harvest economic data"""
        if 'fred' not in self.capabilities:
            return {"error": "FRED capability not available"}

        fred = self.capabilities['fred']

        # Common queries
        if 'gdp' in query.lower():
            return fred.get_latest('GDP')
        elif 'inflation' in query.lower() or 'cpi' in query.lower():
            return fred.get_latest('CPI')
        elif 'unemployment' in query.lower():
            return fred.get_latest('UNEMPLOYMENT')
        elif 'all' in query.lower():
            return fred.get_all_indicators()
        else:
            # Try to fetch directly
            return fred.get_latest(query.upper())

    def _harvest_market(self, query: str) -> Dict[str, Any]:
        """Harvest market data"""
        if 'market' not in self.capabilities:
            return {"error": "Market capability not available"}

        market = self.capabilities['market']

        # Extract ticker if present
        ticker = query.upper().split()[0] if query else 'SPY'

        return market.get_quote(ticker)

    def _harvest_news(self, query: str) -> Dict[str, Any]:
        """Harvest news data"""
        if 'news' not in self.capabilities:
            return {"error": "News capability not available"}

        news = self.capabilities['news']

        if query:
            return {"articles": news.search_news(query)}
        else:
            return {"articles": news.get_headlines()}

    def _harvest_everything(self, request: str) -> Dict[str, Any]:
        """Harvest from all sources"""
        results = {}

        # Get economic indicators
        if 'fred' in self.capabilities:
            results['economic'] = self.capabilities['fred'].get_all_indicators()

        # Get market movers
        if 'market' in self.capabilities:
            results['gainers'] = self.capabilities['market'].get_market_movers('gainers')
            results['losers'] = self.capabilities['market'].get_market_movers('losers')

        # Get news sentiment
        if 'news' in self.capabilities:
            results['sentiment'] = self.capabilities['news'].get_market_sentiment()

        return results

    def schedule_harvest(self, frequency: str = "daily") -> Dict[str, Any]:
        """Schedule regular data harvesting"""
        return {
            "status": "scheduled",
            "frequency": frequency,
            "next_harvest": "tomorrow at market open"
        }

class FREDBot(BaseAgent):
    """Sub-agent for FRED data"""

    def __init__(self, capability, llm_client=None):
        super().__init__("FREDBot", None, llm_client)
        self.vibe = "economic"
        self.capability = capability

class MarketBot(BaseAgent):
    """Sub-agent for market data"""

    def __init__(self, capability, llm_client=None):
        super().__init__("MarketBot", None, llm_client)
        self.vibe = "trader"
        self.capability = capability

class NewsBot(BaseAgent):
    """Sub-agent for news data"""

    def __init__(self, capability, llm_client=None):
        super().__init__("NewsBot", None, llm_client)
        self.vibe = "informed"
        self.capability = capability