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
        # For now, return mock data to test the pattern
        # In production, this would actually fetch data
        if 'SPY' in request or 'correlations' in request:
            return {
                'response': 'Fetched correlation data for SPY',
                'data': {
                    'SPY': {'price': 450.0},
                    'QQQ': {'price': 380.0, 'correlation': 0.85},
                    'DXY': {'price': 105.0, 'correlation': -0.45},
                    'GLD': {'price': 185.0, 'correlation': -0.35}
                }
            }
        elif 'GDP' in request or 'CPI' in request or 'macro' in request.lower():
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

        return {
            'response': f'Fetched data for: {request}',
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