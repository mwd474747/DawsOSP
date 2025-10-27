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
from datetime import date
from typing import Any, Dict, List, Optional
from decimal import Decimal

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
                    quote = await provider_client.get_quote(symbol)
                    result = {
                        "symbol": symbol,
                        "price": float(quote.get("price", 0)),
                        "change": float(quote.get("change", 0)),
                        "change_pct": float(quote.get("changesPercentage", 0)) / 100,
                        "volume": int(quote.get("volume", 0)),
                        "market_cap": float(quote.get("marketCap", 0)),
                        "timestamp": quote.get("timestamp"),
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
            # TODO: Implement Polygon provider
            result = {
                "symbol": symbol,
                "error": "Polygon provider not yet implemented",
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
        api_key = os.getenv("NEWSAPI_KEY")

        if not api_key:
            result = {
                "symbol": symbol,
                "articles": [],
                "error": "NEWSAPI_KEY not configured",
            }
        else:
            try:
                provider_client = NewsAPIProvider(api_key=api_key)

                # Fetch news articles
                if symbol:
                    # Search for symbol in news
                    articles = await provider_client.search_news(
                        query=symbol, limit=limit
                    )
                elif query:
                    articles = await provider_client.search_news(
                        query=query, limit=limit
                    )
                else:
                    # Get top headlines
                    articles = await provider_client.get_top_headlines(limit=limit)

                result = {
                    "symbol": symbol,
                    "query": query,
                    "articles": articles,
                    "provider": "newsapi",
                    "rights_warning": "NewsAPI Developer tier: PDF export not allowed",
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

                # Fetch series data
                series_info = await provider_client.get_series_info(series_id)
                observations = await provider_client.get_series_observations(
                    series_id, limit=limit
                )

                result = {
                    "series_id": series_id,
                    "series_name": series_info.get("title"),
                    "observations": observations,
                    "units": series_info.get("units"),
                    "frequency": series_info.get("frequency"),
                    "provider": "fred",
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
