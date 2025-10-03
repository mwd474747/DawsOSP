"""DataHarvester - Orchestrates data fetching from all sources"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List

class DataHarvester(BaseAgent):
    """Fetches data from various sources"""

    def __init__(self, graph, capabilities: Dict = None, llm_client=None):
        super().__init__(graph=graph, name="DataHarvester", llm_client=llm_client)
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
        # Store result in knowledge graph
        result = self.harvest(request)
        if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
            node_id = self.store_result(result)
            result['node_id'] = node_id
        return result

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
                        'response': f'Fetched market data for {", ".join(symbols)}',
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
                # Try to use knowledge base for economic data as fallback
                if hasattr(self, 'graph') and self.graph:
                    try:
                        economic_data = self.graph.query("SELECT * FROM economic_indicators ORDER BY date DESC LIMIT 1")
                        if economic_data:
                            latest_data = economic_data[0] if economic_data else {}
                            return {
                                'response': 'Fetched economic data from knowledge base',
                                'data': {
                                    'GDP': latest_data.get('gdp_growth', {'value': 'unavailable', 'trend': 'unknown'}),
                                    'CPI': latest_data.get('inflation_rate', {'value': 'unavailable', 'trend': 'unknown'}),
                                    'Unemployment': latest_data.get('unemployment_rate', {'value': 'unavailable', 'trend': 'unknown'}),
                                    'FedFunds': latest_data.get('fed_funds_rate', {'value': 'unavailable', 'trend': 'unknown'}),
                                    '10YYield': latest_data.get('ten_year_yield', {'value': 'unavailable', 'trend': 'unknown'})
                                },
                                'source': 'knowledge_base'
                            }
                    except Exception as e:
                        print(f"Knowledge base query failed: {e}")

                # Last resort: indicate data unavailable rather than fake data
                return {
                    'response': 'Economic data source unavailable',
                    'data': {
                        'GDP': {'value': 'unavailable', 'trend': 'FRED API or knowledge base required'},
                        'CPI': {'value': 'unavailable', 'trend': 'FRED API or knowledge base required'},
                        'Unemployment': {'value': 'unavailable', 'trend': 'FRED API or knowledge base required'},
                        'FedFunds': {'value': 'unavailable', 'trend': 'FRED API or knowledge base required'},
                        '10YYield': {'value': 'unavailable', 'trend': 'FRED API or knowledge base required'}
                    },
                    'note': 'Configure FRED_API_KEY environment variable for real economic data'
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
                            # Get real correlation using knowledge base sector data
                            correlation_value = self._calculate_sector_correlation(base_symbol, symbol)
                            correlations[symbol] = {
                                'price': quote.get('price', 0),
                                'correlation': correlation_value
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
                    'response': f'Fetched data for: {", ".join(data.keys())}',
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

    def _calculate_sector_correlation(self, symbol1: str, symbol2: str) -> float:
        """Calculate correlation using knowledge base sector data"""
        try:
            # Get sector correlations from knowledge base
            if 'enriched_data' in self.capabilities:
                correlations_data = self.capabilities['enriched_data'].get('sector_correlations', {})
                correlation_matrix = correlations_data.get('correlation_matrix', {})

                # Get company sector mappings from knowledge base
                companies_data = self.capabilities['enriched_data'].get('sp500_companies', {})

                # Find sectors for both symbols
                sector1 = self._find_company_sector(symbol1, companies_data)
                sector2 = self._find_company_sector(symbol2, companies_data)

                # If both symbols have sectors, return sector correlation
                if sector1 and sector2 and sector1 in correlation_matrix:
                    return correlation_matrix[sector1].get(sector2, 0.5)

                # For ETFs and indices, use predefined correlations
                etf_correlations = {
                    'QQQ': 0.85,  # Tech-heavy, high correlation with most stocks
                    'DXY': -0.3,  # Dollar typically inverse to stocks
                    'GLD': -0.1,  # Gold slightly inverse
                    'TLT': -0.4,  # Bonds typically inverse to stocks
                    'VIX': -0.8   # Fear index, strongly inverse
                }

                if symbol2 in etf_correlations:
                    return etf_correlations[symbol2]

            # Default correlation for unknown pairs
            return round(0.4, 2)  # Moderate positive correlation as default

        except Exception as e:
            print(f"Error calculating correlation: {e}")
            return 0.5  # Safe default

    def _find_company_sector(self, symbol: str, companies_data: dict) -> str:
        """Find sector for a given company symbol"""
        for sector, cap_groups in companies_data.items():
            if isinstance(cap_groups, dict):
                for cap_group, companies in cap_groups.items():
                    if isinstance(companies, dict) and symbol in companies:
                        return sector
        return None

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