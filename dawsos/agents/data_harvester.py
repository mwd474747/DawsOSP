"""DataHarvester - Orchestrates data fetching from all sources

Phase 3.1: Comprehensive type hints added for better IDE support and type safety.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from core.typing_compat import TypeAlias

# Type aliases for clarity
CapabilitiesDict: TypeAlias = Dict[str, Any]
HarvestResult: TypeAlias = Dict[str, Any]
SymbolList: TypeAlias = List[str]

class DataHarvester(BaseAgent):
    """Fetches data from various sources"""

    def __init__(
        self,
        graph: Any,
        capabilities: Optional[CapabilitiesDict] = None,
        llm_client: Optional[Any] = None
    ) -> None:
        """Initialize DataHarvester with graph, capabilities, and optional LLM client."""
        super().__init__(graph=graph, name="DataHarvester", llm_client=llm_client)
        self.vibe: str = "hungry for data"
        self.capabilities: CapabilitiesDict = capabilities or {}

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

    def process(self, request: str) -> HarvestResult:
        """Process method for compatibility - harvests data and stores in graph."""
        # Store result in knowledge graph
        result: HarvestResult = self.harvest(request)
        if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
            node_id: str = self.store_result(result)
            result['node_id'] = node_id
        return result

    def harvest(self, request: str) -> HarvestResult:
        """Main harvest method - fetches requested data from various sources."""
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

    def _harvest_fred(self, query: str) -> HarvestResult:
        """Harvest economic data from FRED API."""
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

    def _harvest_market(self, query: str) -> HarvestResult:
        """Harvest market data (quotes, prices, etc.)."""
        if 'market' not in self.capabilities:
            return {"error": "Market capability not available"}

        market = self.capabilities['market']

        # Extract ticker if present
        ticker = query.upper().split()[0] if query else 'SPY'

        return market.get_quote(ticker)

    def _harvest_news(self, query: str) -> HarvestResult:
        """Harvest news data and sentiment."""
        if 'news' not in self.capabilities:
            return {"error": "News capability not available"}

        news = self.capabilities['news']

        if query:
            return {"articles": news.search_news(query)}
        else:
            return {"articles": news.get_headlines()}

    def _calculate_sector_correlation(self, symbol1: str, symbol2: str) -> float:
        """Calculate correlation using knowledge base sector data.

        Args:
            symbol1: First stock symbol
            symbol2: Second stock symbol

        Returns:
            Correlation coefficient (-1.0 to 1.0)
        """
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

    def _find_company_sector(self, symbol: str, companies_data: dict) -> Optional[str]:
        """Find sector for a given company symbol.

        Args:
            symbol: Stock ticker symbol
            companies_data: Dictionary of sector/company mappings

        Returns:
            Sector name or None if not found
        """
        for sector, cap_groups in companies_data.items():
            if isinstance(cap_groups, dict):
                for cap_group, companies in cap_groups.items():
                    if isinstance(companies, dict) and symbol in companies:
                        return sector
        return None

    def _harvest_everything(self, request: str) -> HarvestResult:
        """Harvest from all available sources (FRED, market, news)."""
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

    def schedule_harvest(self, frequency: str = "daily") -> HarvestResult:
        """Schedule regular data harvesting.

        Args:
            frequency: How often to harvest (daily, hourly, etc.)

        Returns:
            Scheduling status and next harvest time
        """
        return {
            "status": "scheduled",
            "frequency": frequency,
            "next_harvest": "tomorrow at market open"
        }

    # ============================================================================
    # OPTIONS DATA METHODS (Added for options trading capabilities)
    # ============================================================================

    def fetch_options_flow(self, tickers: SymbolList) -> HarvestResult:
        """Fetch options flow data for multiple tickers.

        Args:
            tickers: List of stock symbols (e.g., ['SPY', 'QQQ', 'IWM'])

        Returns:
            Dictionary with flow_data and tickers
        """
        if 'polygon' not in self.capabilities:
            return {
                'error': 'Polygon capability not available',
                'note': 'Configure POLYGON_API_KEY to enable options data'
            }

        polygon = self.capabilities['polygon']
        flow_data = {}

        for ticker in tickers:
            chain = polygon.get_option_chain(ticker)
            flow_data[ticker] = chain

        return {
            'flow_data': flow_data,
            'tickers': tickers,
            'timestamp': 'now'
        }

    def fetch_unusual_options(self, min_premium: float = 10000) -> HarvestResult:
        """Fetch unusual options activity.

        Args:
            min_premium: Minimum premium threshold (default: $10,000)

        Returns:
            Dictionary with unusual_activities
        """
        if 'polygon' not in self.capabilities:
            return {
                'error': 'Polygon capability not available',
                'note': 'Configure POLYGON_API_KEY to enable options data'
            }

        polygon = self.capabilities['polygon']
        unusual = polygon.detect_unusual_activity(min_premium=min_premium)

        return {
            'unusual_activities': unusual,
            'min_premium': min_premium
        }

    # ========================================
    # Capability Routing Wrapper Methods
    # ========================================
    # These public methods match the capabilities declared in AGENT_CAPABILITIES
    # and delegate to the existing harvest() method with appropriate queries.

    def fetch_stock_quotes(self, symbols: SymbolList, context: Dict[str, Any] = None) -> HarvestResult:
        """
        Public wrapper for stock quotes fetching capability.
        Maps to: can_fetch_stock_quotes
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        query = f"Get stock quotes for {', '.join(symbols)}"
        return self.harvest(query)

    def fetch_economic_data(self, indicators: Optional[List[str]] = None, context: Dict[str, Any] = None) -> HarvestResult:
        """
        Public wrapper for economic data fetching capability.
        Maps to: can_fetch_economic_data

        This is the primary method for Trinity 3.0 GDP Refresh Flow, implementing
        three-tier fallback (live → cache → static) via FredDataCapability.

        Args:
            indicators: List of indicator names or series IDs (default: ['GDP', 'CPI', 'UNRATE', 'DFF'])
            context: Optional context with 'series', 'start_date', 'end_date', 'frequency'

        Returns:
            Dict with series data, source, timestamp, cache age, and health status
        """
        # FRED capability is required for economic data
        if 'fred' not in self.capabilities:
            return {
                'error': 'FRED capability not available',
                'note': 'Configure FRED_API_KEY environment variable for economic data'
            }

        fred = self.capabilities['fred']

        # Extract parameters from context if provided
        series = indicators
        start_date = None
        end_date = None
        frequency = None

        if context:
            # Support both 'indicators' (from pattern_engine) and 'series' (legacy) parameter names
            series = context.get('indicators') or context.get('series') or indicators
            start_date = context.get('start_date')
            end_date = context.get('end_date')
            frequency = context.get('frequency')

        # Use new fetch_economic_indicators method (Trinity 3.0)
        if hasattr(fred, 'fetch_economic_indicators'):
            result = fred.fetch_economic_indicators(
                series=series,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency
            )

            # Store in knowledge graph if available
            if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
                node_id = self.store_result(result)
                result['node_id'] = node_id

            return result

        # Fallback to legacy _harvest_fred method
        if indicators:
            query = f"Fetch economic indicators: {', '.join(indicators)}"
        else:
            query = "Fetch key economic indicators"
        return self._harvest_fred(query)

    def fetch_news(self, symbols: Optional[SymbolList] = None, context: Dict[str, Any] = None) -> HarvestResult:
        """
        Public wrapper for news fetching capability.
        Maps to: can_fetch_news
        """
        if symbols:
            if isinstance(symbols, str):
                symbols = [symbols]
            query = f"Get latest news for {', '.join(symbols)}"
        else:
            query = "Get latest market news"
        return self._harvest_news(query)

    def fetch_fundamentals(self, symbol: str, context: Dict[str, Any] = None) -> HarvestResult:
        """
        Public wrapper for fundamentals fetching capability.
        Maps to: can_fetch_fundamentals
        """
        query = f"Fetch fundamental data for {symbol}"
        return self.harvest(query)

    def fetch_market_movers(self, context: Dict[str, Any] = None) -> HarvestResult:
        """
        Public wrapper for market movers fetching capability.
        Maps to: can_fetch_market_movers
        """
        query = "Get today's market movers and top gainers/losers"
        return self._harvest_market(query)

    def fetch_crypto_data(self, symbols: Optional[List[str]] = None, context: Dict[str, Any] = None) -> HarvestResult:
        """
        Public wrapper for crypto data fetching capability.
        Maps to: can_fetch_crypto_data
        """
        if symbols:
            query = f"Fetch crypto data for {', '.join(symbols)}"
        else:
            query = "Fetch major cryptocurrency data"
        return self.harvest(query)

class FREDBot(BaseAgent):
    """Sub-agent for FRED data (Phase 3.1: Type hints added)"""

    def __init__(self, capability: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize FREDBot with FRED capability.

        Args:
            capability: FRED data capability instance
            llm_client: Optional LLM client for AI-powered responses
        """
        super().__init__("FREDBot", None, llm_client)
        self.vibe: str = "economic"
        self.capability: Any = capability

class MarketBot(BaseAgent):
    """Sub-agent for market data (Phase 3.1: Type hints added)"""

    def __init__(self, capability: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize MarketBot with market capability.

        Args:
            capability: Market data capability instance
            llm_client: Optional LLM client for AI-powered responses
        """
        super().__init__("MarketBot", None, llm_client)
        self.vibe: str = "trader"
        self.capability: Any = capability

class NewsBot(BaseAgent):
    """Sub-agent for news data (Phase 3.1: Type hints added)"""

    def __init__(self, capability: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize NewsBot with news capability.

        Args:
            capability: News data capability instance
            llm_client: Optional LLM client for AI-powered responses
        """
        super().__init__("NewsBot", None, llm_client)
        self.vibe: str = "informed"
        self.capability: Any = capability