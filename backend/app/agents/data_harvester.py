"""
DawsOS Data Harvester Agent

Purpose: Data provider integration (FMP, Polygon, FRED, NewsAPI)
Created: 2025-10-23 (P0 fix from CODEBASE_AUDIT_REPORT.md)
Priority: P0 (Critical for holding deep-dive and news features)

Capabilities:
    - provider.fetch_quote: Fetch equity quote (FMP/Polygon)
    - provider.fetch_fundamentals: Fetch company fundamentals (FMP)
    - provider.fetch_news: Fetch news articles (NewsAPI)
    - provider.fetch_macro: Fetch macro indicators (FRED)
    - provider.fetch_ratios: Fetch financial ratios (FMP)

Architecture:
    Pattern → Agent Runtime → DataHarvester → Provider Facades → External APIs

Features:
    - Circuit breaker (3 failures → OPEN for 60s)
    - Rate limiting (provider-specific)
    - DLQ retry with exponential backoff
    - Rights enforcement (export restrictions)

Usage:
    agent = DataHarvester("data_harvester", services)
    runtime.register_agent(agent)
"""

import logging
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from decimal import Decimal
from uuid import UUID

from app.agents.base_agent import BaseAgent, AgentMetadata
from app.core.types import RequestCtx

logger = logging.getLogger("DawsOS.DataHarvester")


class DataHarvester(BaseAgent):
    """
    Data Provider Integration Agent.

    Provides capabilities for:
        - Equity quotes (FMP, Polygon)
        - Company fundamentals (FMP)
        - Financial ratios (FMP)
        - News articles (NewsAPI)
        - Macro indicators (FRED)

    Integrates with:
        - FMPProvider (equity data, fundamentals)
        - PolygonProvider (equity data backup)
        - NewsAPIProvider (news)
        - FREDProvider (macro indicators)

    Features:
        - Circuit breaker protection
        - Rate limiting enforcement
        - DLQ retry logic
        - Rights registry checks
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "provider.fetch_quote",
            "provider.fetch_fundamentals",
            "provider.fetch_news",
            "provider.fetch_macro",
            "provider.fetch_ratios",
            "fundamentals.load",  # Alias for buffett_checklist pattern compatibility
            "news.search",  # Pattern compatibility for news_impact_analysis
            "news.compute_portfolio_impact",  # Pattern compatibility for news_impact_analysis
        ]

    async def provider_fetch_quote(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: str,
        provider: str = "fmp",
    ) -> Dict[str, Any]:
        """
        Fetch equity quote.

        Gets current price, volume, change for a security.

        Args:
            ctx: Request context
            state: Execution state
            symbol: Security symbol (e.g., "AAPL")
            provider: Provider to use ("fmp" or "polygon")

        Returns:
            Dict with quote data

        Example:
            {
                "symbol": "AAPL",
                "price": 175.43,
                "change": 2.15,
                "change_pct": 0.0124,
                "volume": 54238901,
                "market_cap": 2750000000000,
                "timestamp": "2025-10-22T16:00:00",
                "provider": "fmp",
                "__metadata__": {...}
            }
        """
        logger.info(f"provider.fetch_quote: symbol={symbol}, provider={provider}")

        # Get provider (lazy initialization)
        if provider == "fmp":
            from app.integrations.fmp_provider import FMPProvider
            api_key = os.getenv("FMP_API_KEY")
            if not api_key:
                result = {
                    "symbol": symbol,
                    "error": "FMP_API_KEY not configured",
                }
            else:
                try:
                    provider_client = FMPProvider(api_key=api_key)
                    # FMP get_quote expects a list of symbols
                    quotes = await provider_client.get_quote([symbol])
                    if quotes and len(quotes) > 0:
                        quote = quotes[0]  # Get first (and only) quote
                        result = {
                            "symbol": symbol,
                            "price": float(quote.get("price", 0)),
                            "change": float(quote.get("change", 0)),
                            "change_pct": float(quote.get("changesPercentage", 0)),
                            "volume": int(quote.get("volume", 0)),
                            "market_cap": float(quote.get("marketCap", 0)),
                            "timestamp": quote.get("timestamp"),
                            "provider": "fmp",
                            "_is_stub": False,
                        }
                    else:
                        result = {
                            "symbol": symbol,
                            "error": f"No quote data available for {symbol}",
                            "provider": "fmp",
                        }
                except Exception as e:
                    logger.error(f"Error fetching quote from FMP: {e}", exc_info=True)
                    result = {
                        "symbol": symbol,
                        "error": f"FMP error: {str(e)}",
                        "provider": "fmp",
                    }
        elif provider == "polygon":
            from app.integrations.polygon_provider import PolygonProvider
            api_key = os.getenv("POLYGON_API_KEY")
            if not api_key:
                result = {
                    "symbol": symbol,
                    "error": "POLYGON_API_KEY not configured",
                }
            else:
                try:
                    provider_client = PolygonProvider(api_key=api_key)
                    # Get latest quote using Polygon's last_quote method
                    quote = await provider_client.get_last_quote(symbol)
                    
                    if quote:
                        # Transform Polygon quote format to DawsOS format
                        result = {
                            "symbol": symbol,
                            "price": float(quote.get("last_trade_price", 0)),
                            "bid": float(quote.get("bid", 0)),
                            "ask": float(quote.get("ask", 0)),
                            "volume": int(quote.get("last_trade_size", 0)),
                            "timestamp": quote.get("last_trade_time"),
                            "provider": "polygon",
                            "_is_stub": False,
                        }
                    else:
                        result = {
                            "symbol": symbol,
                            "error": f"No quote data available for {symbol}",
                            "provider": "polygon",
                        }
                except Exception as e:
                    logger.error(f"Error fetching quote from Polygon: {e}", exc_info=True)
                    result = {
                        "symbol": symbol,
                        "error": f"Polygon error: {str(e)}",
                        "provider": "polygon",
                    }
        else:
            result = {
                "symbol": symbol,
                "error": f"Unknown provider: {provider}",
            }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"provider:{provider}:quote",
            asof=ctx.asof_date,
            ttl=300,  # Cache for 5 minutes
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def provider_fetch_fundamentals(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: str,
        period: str = "annual",
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Fetch company fundamentals (income statement, balance sheet, cash flow).

        Args:
            ctx: Request context
            state: Execution state
            symbol: Security symbol
            period: "annual" or "quarter"
            limit: Number of periods to fetch

        Returns:
            Dict with fundamental data

        Example:
            {
                "symbol": "AAPL",
                "period": "annual",
                "income_statement": [
                    {
                        "date": "2024-09-30",
                        "revenue": 391035000000,
                        "gross_profit": 170782000000,
                        "operating_income": 114301000000,
                        "net_income": 93736000000
                    },
                    ...
                ],
                "balance_sheet": [...],
                "cash_flow": [...],
                "provider": "fmp",
                "__metadata__": {...}
            }
        """
        logger.info(
            f"provider.fetch_fundamentals: symbol={symbol}, "
            f"period={period}, limit={limit}"
        )

        # Get FMP provider
        from app.integrations.fmp_provider import FMPProvider
        api_key = os.getenv("FMP_API_KEY")

        if not api_key:
            result = {
                "symbol": symbol,
                "error": "FMP_API_KEY not configured",
            }
        else:
            try:
                provider_client = FMPProvider(api_key=api_key)

                # Fetch income statement, balance sheet, cash flow
                income_stmt = await provider_client.get_income_statement(
                    symbol, period=period, limit=limit
                )
                balance_sheet = await provider_client.get_balance_sheet(
                    symbol, period=period, limit=limit
                )
                cash_flow = await provider_client.get_cash_flow(
                    symbol, period=period, limit=limit
                )

                result = {
                    "symbol": symbol,
                    "period": period,
                    "income_statement": income_stmt,
                    "balance_sheet": balance_sheet,
                    "cash_flow": cash_flow,
                    "provider": "fmp",
                }

            except Exception as e:
                logger.error(f"Error fetching fundamentals from FMP: {e}", exc_info=True)
                result = {
                    "symbol": symbol,
                    "error": f"FMP error: {str(e)}",
                    "provider": "fmp",
                }

        # Attach metadata
        metadata = self._create_metadata(
            source="provider:fmp:fundamentals",
            asof=ctx.asof_date,
            ttl=86400,  # Cache for 24 hours (fundamentals change slowly)
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def provider_fetch_news(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Fetch news articles.

        Args:
            ctx: Request context
            state: Execution state
            symbol: Security symbol (optional)
            query: Search query (optional)
            limit: Number of articles to fetch

        Returns:
            Dict with news articles

        Example:
            {
                "symbol": "AAPL",
                "articles": [
                    {
                        "title": "Apple announces new product",
                        "description": "Apple unveiled...",
                        "url": "https://...",
                        "published_at": "2025-10-22T10:00:00",
                        "source": "TechCrunch",
                        "sentiment": "positive"
                    },
                    ...
                ],
                "provider": "newsapi",
                "rights_warning": "NewsAPI Developer tier: PDF export not allowed",
                "__metadata__": {...}
            }
        """
        logger.info(
            f"provider.fetch_news: symbol={symbol}, query={query}, limit={limit}"
        )

        # Get NewsAPI provider
        from app.integrations.news_provider import NewsAPIProvider
        api_key = os.getenv("NEWS_API_KEY")

        if not api_key:
            result = {
                "symbol": symbol,
                "articles": [],
                "error": "NEWSAPI_KEY not configured",
            }
        else:
            try:
                # Determine tier from environment (default: dev)
                tier = os.getenv("NEWSAPI_TIER", "dev")
                provider_client = NewsAPIProvider(api_key=api_key, tier=tier)

                # Fetch news articles
                if symbol:
                    # Search for symbol in news
                    articles_raw = await provider_client.search(
                        query=symbol, page_size=limit
                    )
                elif query:
                    articles_raw = await provider_client.search(
                        query=query, page_size=limit
                    )
                else:
                    # Get top headlines
                    articles_raw = await provider_client.get_top_headlines(page_size=limit)

                # Transform NewsAPI format to DawsOS format
                articles_transformed = self._transform_newsapi_to_news_format(
                    articles_raw, symbol or query
                )

                result = {
                    "symbol": symbol,
                    "query": query,
                    "articles": articles_transformed,
                    "provider": "newsapi",
                    "rights_warning": "NewsAPI Developer tier: PDF export not allowed" if tier == "dev" else None,
                    "_is_stub": False,
                }

            except Exception as e:
                logger.error(f"Error fetching news from NewsAPI: {e}", exc_info=True)
                result = {
                    "symbol": symbol,
                    "articles": [],
                    "error": f"NewsAPI error: {str(e)}",
                    "provider": "newsapi",
                }

        # Attach metadata
        metadata = self._create_metadata(
            source="provider:newsapi:articles",
            asof=ctx.asof_date,
            ttl=1800,  # Cache for 30 minutes
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def provider_fetch_macro(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        series_id: str,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Fetch macro indicator data from FRED.

        Args:
            ctx: Request context
            state: Execution state
            series_id: FRED series ID (e.g., "T10Y2Y", "UNRATE")
            limit: Number of observations to fetch

        Returns:
            Dict with macro data

        Example:
            {
                "series_id": "T10Y2Y",
                "series_name": "10-Year Treasury Constant Maturity Minus 2-Year",
                "observations": [
                    {"date": "2025-10-22", "value": 0.52},
                    {"date": "2025-10-21", "value": 0.51},
                    ...
                ],
                "units": "Percent",
                "frequency": "Daily",
                "provider": "fred",
                "__metadata__": {...}
            }
        """
        logger.info(f"provider.fetch_macro: series_id={series_id}, limit={limit}")

        # Get FRED provider
        from app.integrations.fred_provider import FREDProvider
        api_key = os.getenv("FRED_API_KEY")

        if not api_key:
            result = {
                "series_id": series_id,
                "observations": [],
                "error": "FRED_API_KEY not configured",
            }
        else:
            try:
                provider_client = FREDProvider(api_key=api_key)

                # Fetch series info and data
                series_info = await provider_client.get_series_info(series_id)
                observations_raw = await provider_client.get_series(
                    series_id, limit=limit
                )

                # Transform FRED format to DawsOS format
                observations_transformed = self._transform_fred_to_macro_format(
                    observations_raw.get("observations", []), series_id
                )

                result = {
                    "series_id": series_id,
                    "series_name": series_info.get("title"),
                    "observations": observations_transformed,
                    "units": series_info.get("units"),
                    "frequency": series_info.get("frequency"),
                    "provider": "fred",
                    "_is_stub": False,
                }

            except Exception as e:
                logger.error(f"Error fetching macro from FRED: {e}", exc_info=True)
                result = {
                    "series_id": series_id,
                    "observations": [],
                    "error": f"FRED error: {str(e)}",
                    "provider": "fred",
                }

        # Attach metadata
        metadata = self._create_metadata(
            source="provider:fred:series",
            asof=ctx.asof_date,
            ttl=3600,  # Cache for 1 hour
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def provider_fetch_ratios(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: str,
        period: str = "annual",
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Fetch financial ratios.

        Args:
            ctx: Request context
            state: Execution state
            symbol: Security symbol
            period: "annual" or "quarter"
            limit: Number of periods to fetch

        Returns:
            Dict with financial ratios

        Example:
            {
                "symbol": "AAPL",
                "period": "annual",
                "ratios": [
                    {
                        "date": "2024-09-30",
                        "roe": 0.476,
                        "roa": 0.285,
                        "current_ratio": 1.08,
                        "debt_to_equity": 1.97,
                        "pe_ratio": 28.5
                    },
                    ...
                ],
                "provider": "fmp",
                "__metadata__": {...}
            }
        """
        logger.info(
            f"provider.fetch_ratios: symbol={symbol}, period={period}, limit={limit}"
        )

        # Get FMP provider
        from app.integrations.fmp_provider import FMPProvider
        api_key = os.getenv("FMP_API_KEY")

        if not api_key:
            result = {
                "symbol": symbol,
                "ratios": [],
                "error": "FMP_API_KEY not configured",
            }
        else:
            try:
                provider_client = FMPProvider(api_key=api_key)

                # Fetch ratios
                ratios = await provider_client.get_ratios(
                    symbol, period=period, limit=limit
                )

                result = {
                    "symbol": symbol,
                    "period": period,
                    "ratios": ratios,
                    "provider": "fmp",
                }

            except Exception as e:
                logger.error(f"Error fetching ratios from FMP: {e}", exc_info=True)
                result = {
                    "symbol": symbol,
                    "ratios": [],
                    "error": f"FMP error: {str(e)}",
                    "provider": "fmp",
                }

        # Attach metadata
        metadata = self._create_metadata(
            source="provider:fmp:ratios",
            asof=ctx.asof_date,
            ttl=86400,  # Cache for 24 hours
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def fundamentals_load(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        security_id: str,
        provider: str = "fmp",
    ) -> Dict[str, Any]:
        """
        Load fundamentals for buffett_checklist pattern compatibility.

        This method:
        1. Looks up symbol from security_id
        2. Fetches fundamentals from provider
        3. Transforms to ratings-service format

        Phase 1: Returns stub data for testing
        Phase 2: Fetch from FMP and transform

        Args:
            ctx: Request context
            state: Execution state
            security_id: Security UUID
            provider: Provider to use (default "fmp")

        Returns:
            Dict with fundamental metrics in ratings-service format

        Example:
            {
                "payout_ratio_5y_avg": 0.152,
                "fcf_dividend_coverage": 6.8,
                "dividend_growth_streak_years": 12,
                "net_cash_position": 51000000000,
                "roe_5y_avg": 0.24,
                "gross_margin_5y_avg": 0.66,
                "intangible_assets_ratio": 0.42,
                "switching_cost_score": 10,
                "debt_equity_ratio": 1.8,
                "interest_coverage": 12.5,
                "current_ratio": 1.1,
                "operating_margin_std_dev": 0.008
            }
        """
        logger.info(f"fundamentals.load: security_id={security_id}, provider={provider}")

        # Attempt real provider fetch with graceful fallback to stubs
        symbol = None
        source = "fundamentals:stub"

        try:
            # Step 1: Lookup symbol from security_id
            db_pool = self.services.get("db")
            if db_pool:
                async with db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT symbol FROM securities WHERE id = $1",
                        UUID(security_id)
                    )
                    if row:
                        symbol = row["symbol"]
                        logger.info(f"Looked up symbol: {security_id} → {symbol}")

            # Step 2: Attempt to fetch from provider if symbol found
            if symbol and provider == "fmp":
                logger.info(f"Attempting to fetch fundamentals for {symbol} from FMP")

                # Call provider.fetch_fundamentals (which may return stub if no API key)
                fundamentals_data = await self.provider_fetch_fundamentals(
                    ctx, state, symbol=symbol, provider=provider
                )

                # Call provider.fetch_ratios for additional metrics
                ratios_data = await self.provider_fetch_ratios(
                    ctx, state, symbol=symbol, provider=provider
                )

                # Check if we got real data (no error field means success)
                has_fundamentals = (
                    "error" not in fundamentals_data
                    and "income_statement" in fundamentals_data
                    and len(fundamentals_data.get("income_statement", [])) > 0
                )
                has_ratios = (
                    "error" not in ratios_data
                    and "ratios" in ratios_data
                    and len(ratios_data.get("ratios", [])) > 0
                )

                # If we got real data from both endpoints, transform it
                if has_fundamentals and has_ratios:
                    try:
                        result = self._transform_fmp_to_ratings_format(
                            fundamentals_data,
                            ratios_data,
                            symbol
                        )
                        source = f"fundamentals:fmp:{symbol}"
                        logger.info(f"Successfully transformed real fundamentals for {symbol}")
                    except ValueError as e:
                        logger.warning(f"FMP transformation failed for {symbol}: {e}, using stubs")
                        result = self._stub_fundamentals_for_symbol(symbol)
                        source = "fundamentals:stub"
                else:
                    # Provider returned error or empty data
                    error_msg = fundamentals_data.get("error") or ratios_data.get("error")
                    if error_msg:
                        logger.warning(f"Provider error for {symbol}: {error_msg}, using stubs")
                    else:
                        logger.warning(f"Provider returned empty data for {symbol}, using stubs")
                    result = self._stub_fundamentals_for_symbol(symbol)
                    source = "fundamentals:stub"
            else:
                if not symbol:
                    logger.warning(f"Could not lookup symbol for security_id={security_id}, using stubs")
                result = self._stub_fundamentals_for_symbol(None)

        except Exception as e:
            logger.warning(f"fundamentals.load failed, falling back to stubs: {e}")
            result = self._stub_fundamentals_for_symbol(symbol)

        metadata = self._create_metadata(
            source=source,
            asof=ctx.asof_date,
            ttl=86400,
        )

        return self._attach_metadata(result, metadata)

    def _stub_fundamentals_for_symbol(self, symbol: Optional[str]) -> Dict[str, Any]:
        """
        Generate stub fundamentals for testing.

        Returns consistent stub data with note indicating this is test data.
        """
        return {
            "payout_ratio_5y_avg": Decimal("0.20"),
            "fcf_dividend_coverage": Decimal("2.5"),
            "dividend_growth_streak_years": 8,
            "net_cash_position": Decimal("5000000000"),  # $5B
            "roe_5y_avg": Decimal("0.18"),
            "gross_margin_5y_avg": Decimal("0.45"),
            "intangible_assets_ratio": Decimal("0.25"),
            "switching_cost_score": Decimal("7"),
            "debt_equity_ratio": Decimal("0.80"),
            "interest_coverage": Decimal("8.0"),
            "current_ratio": Decimal("1.8"),
            "operating_margin_std_dev": Decimal("0.03"),
            "_is_stub": True,
            "_symbol": symbol or "UNKNOWN",
            "_note": "STUB DATA - Real provider integration not yet complete"
        }

    # ========================================================================
    # FMP Transformation Methods
    # ========================================================================

    def _transform_fmp_to_ratings_format(
        self,
        fmp_fundamentals: Dict[str, Any],
        fmp_ratios: Dict[str, Any],
        symbol: str
    ) -> Dict[str, Any]:
        """
        Transform FMP API responses to ratings service format.

        This method maps FMP field names to the format expected by the ratings service,
        calculating 5-year averages and other derived metrics.

        Args:
            fmp_fundamentals: Response from provider.fetch_fundamentals containing:
                - income_statement: List[Dict] (sorted newest first)
                - balance_sheet: List[Dict] (sorted newest first)
                - cash_flow: List[Dict] (sorted newest first)
            fmp_ratios: Response from provider.fetch_ratios containing:
                - ratios: List[Dict] (sorted newest first)
            symbol: Security symbol (for logging)

        Returns:
            Dict with all fields required by ratings service:
                - payout_ratio_5y_avg: Decimal
                - fcf_dividend_coverage: Decimal
                - dividend_growth_streak_years: int
                - net_cash_position: Decimal
                - roe_5y_avg: Decimal
                - gross_margin_5y_avg: Decimal
                - intangible_assets_ratio: Decimal
                - switching_cost_score: Decimal (default 5)
                - debt_equity_ratio: Decimal
                - interest_coverage: Decimal
                - current_ratio: Decimal
                - operating_margin_std_dev: Decimal
                - _symbol: str
                - _source: str ("fmp")
                - _is_stub: bool (False)

        Raises:
            ValueError: If required fields missing from FMP response

        FMP Field Mapping:
            Income Statement Fields:
                - revenue: Total revenue
                - costOfRevenue: Cost of goods sold
                - grossProfit: Gross profit (revenue - COGS)
                - operatingIncome: Operating income (EBIT)
                - netIncome: Net income
                - eps: Earnings per share
                - dividendsPaid: Cash dividends paid (negative number)

            Balance Sheet Fields:
                - totalAssets: Total assets
                - totalLiabilities: Total liabilities
                - totalEquity: Total shareholders' equity
                - cashAndCashEquivalents: Cash and equivalents
                - totalDebt: Total debt
                - intangibleAssets: Intangible assets (goodwill, patents, etc.)
                - totalCurrentAssets: Current assets
                - totalCurrentLiabilities: Current liabilities

            Ratios Fields:
                - returnOnEquity: ROE (net income / equity)
                - debtEquityRatio: Debt-to-equity ratio
                - currentRatio: Current ratio (current assets / current liabilities)
                - interestCoverage: Interest coverage (EBIT / interest expense)
                - grossProfitMargin: Gross margin (gross profit / revenue)
                - operatingProfitMargin: Operating margin (operating income / revenue)
                - payoutRatio: Dividend payout ratio (dividends / net income)
        """
        try:
            # Extract statement lists from FMP response
            income_statements = fmp_fundamentals.get("income_statement", [])
            balance_sheets = fmp_fundamentals.get("balance_sheet", [])
            cash_flows = fmp_fundamentals.get("cash_flow", [])
            ratios = fmp_ratios.get("ratios", [])

            # Validate we have data
            if not income_statements:
                raise ValueError("No income statement data in FMP response")
            if not balance_sheets:
                raise ValueError("No balance sheet data in FMP response")
            if not ratios:
                raise ValueError("No ratios data in FMP response")

            # Get most recent statements
            latest_income = income_statements[0]
            latest_balance = balance_sheets[0]
            latest_ratios = ratios[0]

            # ================================================================
            # Calculate 5-Year Averages
            # ================================================================

            # ROE consistency (5-year average)
            roe_5y_avg = self._calculate_5y_avg(ratios, "returnOnEquity")

            # Gross margin consistency (5-year average)
            gross_margin_5y_avg = self._calculate_5y_avg(ratios, "grossProfitMargin")

            # Payout ratio (5-year average)
            payout_ratio_5y_avg = self._calculate_5y_avg(ratios, "payoutRatio")

            # Operating margin stability (standard deviation over 5 years)
            operating_margin_std_dev = self._calculate_std_dev(ratios, "operatingProfitMargin")

            # ================================================================
            # Dividend Safety Components
            # ================================================================

            # FCF dividend coverage = Free Cash Flow / Dividends Paid
            # Note: FMP reports dividendsPaid as negative (cash outflow)
            fcf = Decimal(str(latest_income.get("freeCashFlow", 0)))
            dividends_paid_raw = latest_income.get("dividendsPaid", 0)
            dividends_paid = abs(Decimal(str(dividends_paid_raw)))  # Make positive

            if dividends_paid > 0:
                fcf_dividend_coverage = fcf / dividends_paid
            else:
                fcf_dividend_coverage = Decimal("0")

            # Dividend growth streak (consecutive years of dividend increases)
            dividend_growth_streak_years = self._calculate_dividend_streak(income_statements)

            # Net cash position = Cash - Total Debt
            cash = Decimal(str(latest_balance.get("cashAndCashEquivalents", 0)))
            total_debt = Decimal(str(latest_balance.get("totalDebt", 0)))
            net_cash_position = cash - total_debt

            # ================================================================
            # Moat Strength Components
            # ================================================================

            # Intangible assets ratio = Intangible Assets / Total Assets
            intangible_assets = Decimal(str(latest_balance.get("intangibleAssets", 0)))
            total_assets = Decimal(str(latest_balance.get("totalAssets", 1)))  # Avoid division by zero

            if total_assets > 0:
                intangible_assets_ratio = intangible_assets / total_assets
            else:
                intangible_assets_ratio = Decimal("0")

            # Switching costs (qualitative - default to 5)
            # TODO: Implement sector-based lookup for switching costs
            switching_cost_score = Decimal("5")

            # ================================================================
            # Resilience Components
            # ================================================================

            # Debt-to-equity ratio (from ratios)
            debt_equity_ratio = Decimal(str(latest_ratios.get("debtEquityRatio", 0)))

            # Interest coverage (from ratios)
            interest_coverage = Decimal(str(latest_ratios.get("interestCoverage", 0)))

            # Current ratio (from ratios)
            current_ratio = Decimal(str(latest_ratios.get("currentRatio", 0)))

            # ================================================================
            # Return Transformed Data
            # ================================================================

            logger.info(f"Successfully transformed FMP data for {symbol}")

            return {
                # Dividend safety
                "payout_ratio_5y_avg": payout_ratio_5y_avg,
                "fcf_dividend_coverage": fcf_dividend_coverage,
                "dividend_growth_streak_years": dividend_growth_streak_years,
                "net_cash_position": net_cash_position,

                # Moat strength
                "roe_5y_avg": roe_5y_avg,
                "gross_margin_5y_avg": gross_margin_5y_avg,
                "intangible_assets_ratio": intangible_assets_ratio,
                "switching_cost_score": switching_cost_score,

                # Resilience
                "debt_equity_ratio": debt_equity_ratio,
                "interest_coverage": interest_coverage,
                "current_ratio": current_ratio,
                "operating_margin_std_dev": operating_margin_std_dev,

                # Metadata
                "_symbol": symbol,
                "_source": "fmp",
                "_is_stub": False,
            }

        except (KeyError, IndexError, ValueError, ZeroDivisionError, TypeError) as e:
            logger.error(f"FMP transformation failed for {symbol}: {e}", exc_info=True)
            raise ValueError(f"Cannot transform FMP data for {symbol}: {e}")

    # ========================================================================
    # FMP Transformation Helper Methods
    # ========================================================================

    def _calculate_5y_avg(self, data_array: List[Dict], field: str) -> Decimal:
        """
        Calculate 5-year average of a field from FMP time series data.

        Args:
            data_array: List of FMP statements (sorted newest first)
            field: Field name to average (e.g., "returnOnEquity", "grossProfitMargin")

        Returns:
            Decimal: 5-year average, or Decimal("0") if no data

        Example:
            data_array = [
                {"date": "2023-12-31", "returnOnEquity": 0.45},
                {"date": "2022-12-31", "returnOnEquity": 0.42},
                ...
            ]
            avg = self._calculate_5y_avg(data_array, "returnOnEquity")
            # Returns Decimal("0.435")
        """
        if not data_array:
            return Decimal("0")

        # Take up to 5 years of data
        values = []
        for item in data_array[:5]:
            value = item.get(field, 0)
            if value is not None:
                try:
                    values.append(Decimal(str(value)))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {field}: {value}")
                    continue

        if not values:
            return Decimal("0")

        return sum(values) / Decimal(len(values))

    def _calculate_std_dev(self, data_array: List[Dict], field: str) -> Decimal:
        """
        Calculate standard deviation of a field from FMP time series data.

        Args:
            data_array: List of FMP statements (sorted newest first)
            field: Field name to analyze (e.g., "operatingIncomeRatio")

        Returns:
            Decimal: Standard deviation over 5 years, or Decimal("0") if no data

        Example:
            data_array = [
                {"date": "2023-12-31", "operatingIncomeRatio": 0.30},
                {"date": "2022-12-31", "operatingIncomeRatio": 0.28},
                ...
            ]
            std = self._calculate_std_dev(data_array, "operatingIncomeRatio")
            # Returns Decimal("0.015")
        """
        if not data_array:
            return Decimal("0")

        # Take up to 5 years of data
        values = []
        for item in data_array[:5]:
            value = item.get(field, 0)
            if value is not None:
                try:
                    values.append(Decimal(str(value)))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {field}: {value}")
                    continue

        if not values or len(values) < 2:
            return Decimal("0")

        # Calculate mean
        mean = sum(values) / Decimal(len(values))

        # Calculate variance
        variance = sum((v - mean) ** 2 for v in values) / Decimal(len(values))

        # Return square root (standard deviation)
        # Note: Decimal.sqrt() requires Python 3.9+, we'll use a workaround
        try:
            return variance.sqrt()
        except AttributeError:
            # Fallback for Python < 3.9
            import math
            return Decimal(str(math.sqrt(float(variance))))

    def _calculate_dividend_streak(self, data_array: List[Dict]) -> int:
        """
        Calculate consecutive years of dividend growth from FMP data.

        Args:
            data_array: List of FMP statements (sorted newest first)

        Returns:
            int: Number of consecutive years of dividend growth

        Example:
            data_array = [
                {"date": "2023-12-31", "dividendsPaid": -5000000000},  # Negative = paid out
                {"date": "2022-12-31", "dividendsPaid": -4500000000},
                {"date": "2021-12-31", "dividendsPaid": -4000000000},
                ...
            ]
            streak = self._calculate_dividend_streak(data_array)
            # Returns 2 (2023 > 2022 > 2021)

        Note:
            FMP reports dividendsPaid as negative numbers (cash outflow)
            We compare absolute values for growth streak
        """
        if not data_array or len(data_array) < 2:
            return 0

        streak = 0
        for i in range(len(data_array) - 1):
            current_div = data_array[i].get("dividendsPaid", 0)
            previous_div = data_array[i + 1].get("dividendsPaid", 0)

            # Convert to absolute values (FMP uses negative for outflows)
            try:
                current_abs = abs(Decimal(str(current_div)))
                previous_abs = abs(Decimal(str(previous_div)))
            except (ValueError, TypeError):
                logger.warning(f"Invalid dividend values: current={current_div}, previous={previous_div}")
                break

            # Check for growth (current year dividend > previous year dividend)
            if current_abs > previous_abs and previous_abs > 0:
                streak += 1
            else:
                break

        return streak

    # ========================================================================
    # Polygon Transformation Methods
    # ========================================================================

    def _transform_polygon_to_quote_format(
        self,
        polygon_price: Dict[str, Any],
        symbol: str
    ) -> Dict[str, Any]:
        """
        Transform Polygon API price response to DawsOS quote format.

        Args:
            polygon_price: Single price bar from Polygon API with keys:
                - o: open price (float)
                - h: high price (float)
                - l: low price (float)
                - c: close price (float)
                - v: volume (int)
                - t: timestamp in Unix milliseconds (int)
            symbol: Security symbol

        Returns:
            Dict with DawsOS quote format:
                - symbol: str
                - price: Decimal (close price)
                - change: Decimal (change from previous close)
                - change_pct: Decimal (percentage change)
                - volume: int
                - timestamp: str (ISO format)
                - provider: str ("polygon")
                - _is_stub: bool (False)

        Raises:
            ValueError: If required fields missing

        Example:
            Input (Polygon):
                {
                    "o": 175.10,
                    "h": 177.50,
                    "l": 174.80,
                    "c": 176.45,
                    "v": 54238901,
                    "t": 1698796800000
                }

            Output (DawsOS):
                {
                    "symbol": "AAPL",
                    "price": Decimal("176.45"),
                    "open": Decimal("175.10"),
                    "high": Decimal("177.50"),
                    "low": Decimal("174.80"),
                    "volume": 54238901,
                    "change": Decimal("1.35"),
                    "change_pct": Decimal("0.0077"),
                    "timestamp": "2023-11-01T00:00:00Z",
                    "provider": "polygon",
                    "_is_stub": False
                }
        """
        try:
            # Validate required fields
            required_fields = ["c", "o", "h", "l", "v", "t"]
            for field in required_fields:
                if field not in polygon_price:
                    raise ValueError(f"Missing required field: {field}")

            # Extract values
            close = Decimal(str(polygon_price["c"]))
            open_price = Decimal(str(polygon_price["o"]))
            high = Decimal(str(polygon_price["h"]))
            low = Decimal(str(polygon_price["l"]))
            volume = int(polygon_price["v"])
            timestamp_ms = int(polygon_price["t"])

            # Convert timestamp from Unix milliseconds to ISO format
            from datetime import datetime, timezone
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            timestamp_str = timestamp.isoformat()

            # Calculate change (assuming open as previous close for single-day quote)
            # Note: For accurate change, would need previous day's close
            change = close - open_price
            if open_price > 0:
                change_pct = change / open_price
            else:
                change_pct = Decimal("0")

            return {
                "symbol": symbol,
                "price": close,
                "open": open_price,
                "high": high,
                "low": low,
                "volume": volume,
                "change": change,
                "change_pct": change_pct,
                "timestamp": timestamp_str,
                "provider": "polygon",
                "_is_stub": False,
            }

        except (KeyError, ValueError, TypeError, ZeroDivisionError) as e:
            logger.error(f"Polygon transformation failed for {symbol}: {e}", exc_info=True)
            raise ValueError(f"Cannot transform Polygon price for {symbol}: {e}")

    # ========================================================================
    # FRED Transformation Methods
    # ========================================================================

    def _transform_fred_to_macro_format(
        self,
        fred_observations: List[Dict[str, Any]],
        series_id: str
    ) -> List[Dict[str, Any]]:
        """
        Transform FRED API observations to DawsOS macro indicator format.

        Args:
            fred_observations: List of FRED observations with keys:
                - date: observation date (str, "YYYY-MM-DD")
                - value: observation value (str, may be "." for missing)
                - realtime_start: realtime start date (str)
                - realtime_end: realtime end date (str)
            series_id: FRED series ID

        Returns:
            List of transformed observations with DawsOS format:
                - date: str (YYYY-MM-DD)
                - value: Decimal (converted from str, None if missing)
                - indicator_code: str (series_id)
                - _source: str ("fred")
                - _is_stub: bool (False)

        Example:
            Input (FRED):
                [
                    {
                        "date": "2025-10-22",
                        "value": "0.52",
                        "realtime_start": "2025-10-23",
                        "realtime_end": "2025-10-23"
                    },
                    {
                        "date": "2025-10-21",
                        "value": ".",
                        "realtime_start": "2025-10-23",
                        "realtime_end": "2025-10-23"
                    }
                ]

            Output (DawsOS):
                [
                    {
                        "date": "2025-10-22",
                        "value": Decimal("0.52"),
                        "indicator_code": "T10Y2Y",
                        "_source": "fred",
                        "_is_stub": False
                    },
                    {
                        "date": "2025-10-21",
                        "value": None,
                        "indicator_code": "T10Y2Y",
                        "_source": "fred",
                        "_is_stub": False
                    }
                ]
        """
        transformed = []

        for obs in fred_observations:
            try:
                date_str = obs.get("date")
                value_str = obs.get("value")

                if not date_str:
                    logger.warning(f"FRED observation missing date field: {obs}")
                    continue

                # Handle missing values (FRED uses "." for missing)
                if value_str == "." or value_str is None or value_str == "":
                    value = None
                else:
                    try:
                        value = Decimal(str(value_str))
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid FRED value for {series_id} on {date_str}: {value_str}")
                        value = None

                transformed.append({
                    "date": date_str,
                    "value": value,
                    "indicator_code": series_id,
                    "_source": "fred",
                    "_is_stub": False,
                })

            except Exception as e:
                logger.warning(f"Failed to transform FRED observation: {e}")
                continue

        logger.info(f"Transformed {len(transformed)} FRED observations for {series_id}")
        return transformed

    # ========================================================================
    # NewsAPI Transformation Methods
    # ========================================================================

    def _transform_newsapi_to_news_format(
        self,
        newsapi_articles: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Transform NewsAPI article responses to DawsOS news format.

        Args:
            newsapi_articles: List of NewsAPI articles with keys:
                - source: dict with "id" and "name"
                - author: str (may be None)
                - title: str
                - description: str
                - url: str
                - urlToImage: str (may be None)
                - publishedAt: str (ISO format)
                - content: str (only if business tier)
                - metadata_only: bool (True if dev tier)
            query: Search query or symbol

        Returns:
            List of transformed articles with DawsOS format:
                - title: str
                - summary: str (from description)
                - url: str
                - published_at: str (ISO format)
                - source: str (source name)
                - relevance: Decimal (calculated from keyword matching)
                - author: str (optional)
                - image_url: str (optional)
                - _source: str ("newsapi")
                - _is_stub: bool (False)
                - _metadata_only: bool (True if dev tier)

        Example:
            Input (NewsAPI):
                [
                    {
                        "source": {"id": "reuters", "name": "Reuters"},
                        "author": "John Doe",
                        "title": "Apple Reports Record Quarter",
                        "description": "Apple Inc. reported record quarterly earnings...",
                        "url": "https://reuters.com/article/123",
                        "urlToImage": "https://reuters.com/image.jpg",
                        "publishedAt": "2025-10-22T10:00:00Z",
                        "metadata_only": True
                    }
                ]

            Output (DawsOS):
                [
                    {
                        "title": "Apple Reports Record Quarter",
                        "summary": "Apple Inc. reported record quarterly earnings...",
                        "url": "https://reuters.com/article/123",
                        "published_at": "2025-10-22T10:00:00Z",
                        "source": "Reuters",
                        "relevance": Decimal("0.85"),
                        "author": "John Doe",
                        "image_url": "https://reuters.com/image.jpg",
                        "_source": "newsapi",
                        "_is_stub": False,
                        "_metadata_only": True
                    }
                ]
        """
        transformed = []

        for article in newsapi_articles:
            try:
                # Extract source name
                source_obj = article.get("source", {})
                source_name = source_obj.get("name", "Unknown")

                # Required fields
                title = article.get("title", "")
                description = article.get("description", "")
                url = article.get("url", "")
                published_at = article.get("publishedAt", "")

                if not title or not url:
                    logger.warning(f"NewsAPI article missing required fields: {article}")
                    continue

                # Optional fields
                author = article.get("author")
                image_url = article.get("urlToImage")
                metadata_only = article.get("metadata_only", False)

                # Calculate relevance score (simple keyword matching)
                relevance = self._calculate_news_relevance(title, description, query)

                transformed.append({
                    "headline": title,  # Changed from "title" to "headline" for compatibility
                    "summary": description,
                    "url": url,
                    "published_at": published_at,
                    "source": source_name,
                    "relevance": relevance,
                    "author": author,
                    "image_url": image_url,
                    "_source": "newsapi",
                    "_is_stub": False,
                    "_metadata_only": metadata_only,
                })

            except Exception as e:
                logger.warning(f"Failed to transform NewsAPI article: {e}")
                continue

        logger.info(f"Transformed {len(transformed)} NewsAPI articles for query '{query}'")
        return transformed

    def _calculate_news_relevance(
        self,
        title: str,
        description: str,
        query: str
    ) -> Decimal:
        """
        Calculate relevance score for news article based on keyword matching.

        Args:
            title: Article title
            description: Article description/summary
            query: Search query (symbol or keyword)

        Returns:
            Relevance score between 0.0 and 1.0

        Algorithm:
            - Exact match in title: 1.0
            - Match in title (case-insensitive): 0.85
            - Match in description: 0.70
            - Multiple matches: average of scores
            - No match: 0.50 (default relevance)
        """
        if not query or not title:
            return Decimal("0.50")

        query_lower = query.lower()
        title_lower = title.lower()
        description_lower = (description or "").lower()

        # Check for exact match in title
        if query == title:
            return Decimal("1.00")

        # Check for case-insensitive match in title
        if query_lower in title_lower:
            return Decimal("0.85")

        # Check for match in description
        if query_lower in description_lower:
            return Decimal("0.70")

        # No match found - default relevance
        return Decimal("0.50")

    async def news_search(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        entities: Optional[List] = None,
        lookback_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Search for news articles related to specified entities.

        Capability: news.search
        Pattern compatibility for news_impact_analysis.json

        Args:
            entities: List of symbols/entities to search for, or list of positions with 'symbol' field
            lookback_hours: Hours to look back for news (default: 24)

        Returns:
            Dict with news items and metadata
        """
        # Handle different input formats
        if not entities:
            # Check if valued positions are in state
            valued = state.get("valued", {})
            if valued and "positions" in valued:
                entities = valued["positions"]
            else:
                entities = []
        
        # Extract symbols if entities contains position objects
        symbols = []
        for entity in entities:
            if isinstance(entity, dict):
                # This is a position object, extract symbol
                symbol = entity.get("symbol")
                if symbol:
                    # Normalize symbol (e.g., BRK.B -> BRK-B for better search)
                    normalized_symbol = symbol.replace(".", "-")
                    symbols.append(normalized_symbol)
            elif isinstance(entity, str):
                # This is already a symbol string
                normalized_symbol = entity.replace(".", "-")
                symbols.append(normalized_symbol)
        
        logger.info(f"news.search: symbols={symbols}, lookback_hours={lookback_hours}")

        try:
            # Use existing provider.fetch_news capability
            all_news_items = []
            unique_articles = set()  # Track unique URLs to avoid duplicates
            
            for symbol in symbols:
                try:
                    news_result = await self.provider_fetch_news(
                        ctx, state, symbol=symbol, limit=20  # Pass limit to provider_fetch_news
                    )
                    
                    # Fix: Check for "articles" key instead of "news"
                    if news_result.get("articles"):
                        for article in news_result["articles"]:
                            # Skip duplicates based on URL
                            url = article.get("url", "")
                            if url and url not in unique_articles:
                                unique_articles.add(url)
                                # Add symbol reference to track which symbol matched
                                article["matched_symbol"] = symbol
                                all_news_items.append(article)
                    
                    # Log if no articles found for a symbol
                    if not news_result.get("articles"):
                        logger.info(f"No news articles found for symbol: {symbol}")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch news for symbol {symbol}: {e}")
                    continue

            # Filter by lookback time
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
            
            filtered_news = []
            for item in all_news_items:
                if item.get("published_at"):
                    try:
                        # Handle different date formats
                        pub_date_str = item["published_at"]
                        if pub_date_str.endswith("Z"):
                            pub_time = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                        else:
                            pub_time = datetime.fromisoformat(pub_date_str)
                        
                        if pub_time >= cutoff_time:
                            filtered_news.append(item)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not parse date {item.get('published_at')}: {e}")
                        # Include if we can't parse the date (better to show than miss)
                        filtered_news.append(item)
                else:
                    # Include articles without dates (shouldn't happen but be safe)
                    filtered_news.append(item)

            # Sort by relevance and date
            filtered_news.sort(
                key=lambda x: (
                    float(x.get("relevance", 0.5)),
                    x.get("published_at", "")
                ),
                reverse=True
            )

            # Log summary
            logger.info(f"news.search found {len(filtered_news)} articles for {len(symbols)} symbols")

            return {
                "news_items": filtered_news,
                "total_count": len(filtered_news),
                "entities_searched": symbols,
                "lookback_hours": lookback_hours,
                "_source": "newsapi",
            }

        except Exception as e:
            logger.error(f"news.search failed: {e}", exc_info=True)
            return {
                "news_items": [],
                "total_count": 0,
                "entities_searched": symbols,
                "lookback_hours": lookback_hours,
                "error": str(e),
            }

    async def news_compute_portfolio_impact(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        news_items: Any,  # Can be Dict or List
        positions: Any,  # Can be Dict or List
        min_threshold: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Compute portfolio impact of news items.

        Capability: news.compute_portfolio_impact
        Pattern compatibility for news_impact_analysis.json

        Args:
            news_items: Dict from news.search or List of news items
            positions: Dict from pricing.apply_pack or List of portfolio positions
            min_threshold: Minimum impact threshold (default: 0.1)

        Returns:
            Dict with impact analysis results
        """
        # Extract the actual lists from the input objects
        if isinstance(news_items, dict):
            actual_news_items = news_items.get("news_items", [])
        else:
            actual_news_items = news_items if isinstance(news_items, list) else []
        
        if isinstance(positions, dict):
            actual_positions = positions.get("positions", [])
        else:
            actual_positions = positions if isinstance(positions, list) else []
        
        logger.info(
            f"news.compute_portfolio_impact: {len(actual_news_items)} news items, "
            f"{len(actual_positions)} positions, threshold={min_threshold}"
        )

        try:
            # Create position lookup by symbol
            position_lookup = {}
            for pos in actual_positions:
                if isinstance(pos, dict):
                    symbol = pos.get("symbol")
                    if symbol:
                        position_lookup[symbol] = pos
            
            # Analyze each news item for portfolio impact
            impact_analysis = []
            total_impact_score = 0.0
            entity_mention_counts = {}
            
            for news_item in actual_news_items:
                if not isinstance(news_item, dict):
                    continue
                    
                # Extract news fields - handle None values
                title = (news_item.get("title") or news_item.get("headline") or "").lower()
                summary = (news_item.get("summary") or "").lower()
                content = (news_item.get("content") or summary or "").lower()
                
                # Enhanced sentiment analysis with more keywords  
                positive_keywords = ["up", "rise", "gain", "profit", "beat", "exceed", "strong", "growth", 
                                   "surge", "rally", "boost", "upgrade", "bullish", "record", "breakthrough"]
                negative_keywords = ["down", "fall", "drop", "loss", "miss", "weak", "decline", "crash",
                                   "plunge", "slump", "cut", "downgrade", "bearish", "warning", "concern"]
                
                # Calculate sentiment score based on keyword presence
                sentiment_score = 0.0
                for keyword in positive_keywords:
                    if keyword in title:
                        sentiment_score += 0.15  # Title mentions are weighted higher
                    if keyword in content:
                        sentiment_score += 0.05
                        
                for keyword in negative_keywords:
                    if keyword in title:
                        sentiment_score -= 0.15
                    if keyword in content:
                        sentiment_score -= 0.05
                
                # Clamp sentiment score to [-1, 1]
                sentiment_score = max(-1.0, min(1.0, sentiment_score))
                
                # Check which portfolio holdings are mentioned
                mentioned_symbols = []
                for symbol, position in position_lookup.items():
                    # Check both the symbol and possible variations
                    symbol_lower = symbol.lower()
                    symbol_normalized = symbol.replace(".", "").replace("-", "").lower()
                    
                    # Check if symbol or variations appear in title/content
                    if (symbol_lower in title or symbol_lower in content or
                        symbol_normalized in title or symbol_normalized in content):
                        mentioned_symbols.append(symbol)
                        # Track entity mentions for visualization
                        entity_mention_counts[symbol] = entity_mention_counts.get(symbol, 0) + 1
                
                # Also check if news mentions matched_symbol from search
                matched_symbol = news_item.get("matched_symbol", "")
                if matched_symbol:
                    # Convert back from normalized form (BRK-B -> BRK.B)
                    original_symbol = matched_symbol.replace("-", ".")
                    if original_symbol in position_lookup and original_symbol not in mentioned_symbols:
                        mentioned_symbols.append(original_symbol)
                        entity_mention_counts[original_symbol] = entity_mention_counts.get(original_symbol, 0) + 1
                
                # Calculate impact for each mentioned position
                position_impacts = []
                for symbol in mentioned_symbols:
                    position = position_lookup.get(symbol, {})
                    weight = float(position.get("weight", 0.0))  # Portfolio weight as percentage
                    
                    # Impact score combines relevance, sentiment, and portfolio weight
                    relevance = float(news_item.get("relevance", 0.5))
                    impact_score = abs(sentiment_score) * relevance * weight / 100.0
                    
                    if impact_score >= min_threshold:
                        position_impacts.append({
                            "symbol": symbol,
                            "weight": weight,
                            "impact_score": round(impact_score, 4),
                            "sentiment": "positive" if sentiment_score > 0 else "negative" if sentiment_score < 0 else "neutral",
                            "sentiment_score": round(sentiment_score, 3),
                        })
                        total_impact_score += impact_score
                
                # Include news item if it has portfolio impact
                if position_impacts:
                    impact_analysis.append({
                        "headline": news_item.get("title", ""),
                        "summary": news_item.get("summary", ""),
                        "source": news_item.get("source", ""),
                        "published_at": news_item.get("published_at", ""),
                        "url": news_item.get("url", ""),
                        "sentiment": "positive" if sentiment_score > 0 else "negative" if sentiment_score < 0 else "neutral",
                        "sentiment_score": round(sentiment_score, 3),
                        "impact_score": round(max(imp["impact_score"] for imp in position_impacts), 4),
                        "entities": mentioned_symbols,
                        "weight_affected": round(sum(imp["weight"] for imp in position_impacts), 2),
                        "mentioned_symbols": mentioned_symbols,
                        "position_impacts": position_impacts,
                    })
            
            # Sort by impact score (highest impact first)
            impact_analysis.sort(key=lambda x: x["impact_score"], reverse=True)
            
            # Prepare entity mentions for bar chart (top 10)
            entity_mentions_list = sorted(
                [{"entity": k, "mention_count": v} for k, v in entity_mention_counts.items()],
                key=lambda x: x["mention_count"],
                reverse=True
            )[:10]
            
            # Calculate portfolio exposure percentage
            exposed_positions = len(set(sum([item["entities"] for item in impact_analysis], [])))
            exposed_portfolio_pct = (exposed_positions / len(actual_positions) * 100) if actual_positions else 0
            
            # Calculate overall sentiment
            if impact_analysis:
                avg_sentiment = sum(item["sentiment_score"] for item in impact_analysis) / len(impact_analysis)
                overall_sentiment = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
            else:
                overall_sentiment = "neutral"
            
            # Calculate weighted impact score (0-1 scale)
            total_weight = sum(float(pos.get("weight", 0)) for pos in actual_positions)
            weighted_impact = (total_impact_score / total_weight * 100) if total_weight > 0 else 0
            
            return {
                # Core analysis results
                "news_with_impact": impact_analysis,  # For news_items panel
                "impact_analysis": impact_analysis,   # Backwards compatibility
                
                # Summary metrics for impact_summary panel
                "total_items": len(actual_news_items),
                "high_impact_count": len([item for item in impact_analysis if item["impact_score"] >= min_threshold]),
                "weighted_impact": round(weighted_impact, 4),
                "exposed_portfolio_pct": round(exposed_portfolio_pct, 2),
                "overall_sentiment": overall_sentiment,
                
                # Entity mentions for bar chart
                "entity_mentions": entity_mentions_list,
                
                # Additional metadata
                "total_impact_score": round(total_impact_score, 4),
                "min_threshold": min_threshold,
                "positions_analyzed": len(actual_positions),
                "news_items_analyzed": len(actual_news_items),
                "_source": "newsapi" if actual_news_items else "empty",
            }

        except Exception as e:
            logger.error(f"news.compute_portfolio_impact failed: {e}", exc_info=True)
            return {
                # Core analysis results (empty)
                "news_with_impact": [],
                "impact_analysis": [],
                
                # Summary metrics (defaults)
                "total_items": 0,
                "high_impact_count": 0,
                "weighted_impact": 0.0,
                "exposed_portfolio_pct": 0.0,
                "overall_sentiment": "neutral",
                
                # Entity mentions (empty)
                "entity_mentions": [],
                
                # Additional metadata
                "total_impact_score": 0.0,
                "min_threshold": min_threshold,
                "positions_analyzed": len(actual_positions),
                "news_items_analyzed": len(actual_news_items),
                "_source": "error",
                "error": str(e),
            }


# ============================================================================
# Factory Function (Singleton Pattern)
# ============================================================================

_data_harvester_instance = None


def get_data_harvester(services: Optional[Dict[str, Any]] = None) -> DataHarvester:
    """
    Get or create singleton DataHarvester agent.

    Args:
        services: Services dict (optional)

    Returns:
        DataHarvester instance
    """
    global _data_harvester_instance
    if _data_harvester_instance is None:
        _data_harvester_instance = DataHarvester("data_harvester", services or {})
        logger.info("DataHarvester agent initialized")
    return _data_harvester_instance
