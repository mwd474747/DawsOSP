#!/usr/bin/env python3
"""
Financial Data Fetcher - Extracted from FinancialAnalyst (Phase 2.1)

Handles fetching and aggregating financial data from various sources
(FMP API, enriched datasets, knowledge graph).

Part of Phase 2 god object refactoring to reduce FinancialAnalyst complexity.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Type aliases for clarity
FinancialData = Dict[str, Any]
MarketCapability = Any
EnrichedDataCapability = Any


class FinancialDataFetcher:
    """
    Fetches and aggregates financial data from multiple sources.

    Data Sources:
    - FMP API (via market capability): Income statements, balance sheets, cash flows
    - Enriched datasets (via enriched_data capability): Financial calculations knowledge
    - Request parsing: Symbol extraction from natural language

    Provides unified interface for financial data retrieval across all analyzers.
    """

    def __init__(self,
                 market_capability: Optional[MarketCapability] = None,
                 enriched_data_capability: Optional[EnrichedDataCapability] = None,
                 logger: logging.Logger = None):
        """
        Initialize financial data fetcher.

        Args:
            market_capability: Market data API capability (FMP)
            enriched_data_capability: Enriched knowledge datasets
            logger: Logger instance for diagnostic output
        """
        self.market = market_capability
        self.enriched_data = enriched_data_capability
        self.logger = logger or logging.getLogger(__name__)

    def get_company_financials(self, symbol: str) -> FinancialData:
        """
        Get comprehensive company financial data from FMP API.

        Fetches:
        - Income statements (annual)
        - Balance sheets (annual)
        - Cash flow statements (annual)
        - Company profile (beta, market cap, sector)

        Calculates derived metrics:
        - Free cash flow (OCF - CapEx)
        - Total capital (debt + equity)
        - Working capital
        - EBITDA decomposition

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Dict with financial data or {"error": "..."} if fetch fails
        """
        if not self.market:
            return {"error": "Market capability not available"}

        try:
            self.logger.info(f"Fetching financial data for {symbol}")

            # Get latest financial statements from FMP API
            income_statements = self.market.get_financials(symbol, statement='income', period='annual')
            balance_sheets = self.market.get_financials(symbol, statement='balance', period='annual')
            cash_flow_statements = self.market.get_financials(symbol, statement='cash-flow', period='annual')
            company_profile = self.market.get_company_profile(symbol)

            # Validate responses
            if not income_statements or 'error' in income_statements[0]:
                return {"error": f"Failed to fetch income statement for {symbol}"}
            if not balance_sheets or 'error' in balance_sheets[0]:
                return {"error": f"Failed to fetch balance sheet for {symbol}"}
            if not cash_flow_statements or 'error' in cash_flow_statements[0]:
                return {"error": f"Failed to fetch cash flow statement for {symbol}"}

            # Get most recent period (index 0)
            income = income_statements[0]
            balance = balance_sheets[0]
            cash_flow = cash_flow_statements[0]

            # Calculate derived metrics
            total_debt = balance.get('debt', 0) or 0
            total_equity = balance.get('total_equity', 0) or 0
            total_capital = total_debt + total_equity

            # Get or calculate free cash flow
            free_cash_flow = cash_flow.get('free_cash_flow')
            if not free_cash_flow:
                # Calculate: Operating Cash Flow - Capital Expenditures
                operating_cf = cash_flow.get('operating_cash_flow', 0) or 0
                capex = abs(cash_flow.get('capex', 0) or 0)  # CapEx is usually negative
                free_cash_flow = operating_cf - capex

            # Calculate depreciation & amortization from EBITDA decomposition
            ebitda = income.get('ebitda', 0) or 0
            operating_income = income.get('operating_income', 0) or 0
            depreciation_amortization = (ebitda - operating_income) if ebitda and operating_income else 0

            # Extract profile data safely
            beta = 1.0
            market_cap = 0
            sector = 'Unknown'
            company_name = symbol

            if company_profile and 'error' not in company_profile:
                beta = company_profile.get('beta', 1.0)
                market_cap = company_profile.get('mktCap', 0)
                sector = company_profile.get('sector', 'Unknown')
                company_name = company_profile.get('companyName', symbol)

            # Build comprehensive financial data structure
            financial_data = {
                "symbol": symbol,
                "company_name": company_name,
                "sector": sector,

                # Core metrics for DCF
                "free_cash_flow": free_cash_flow or 0,
                "net_income": income.get('net_income', 0) or 0,
                "ebit": operating_income,  # Operating income = EBIT
                "ebitda": ebitda,
                "revenue": income.get('revenue', 0) or 0,

                # Cash flow components
                "operating_cash_flow": cash_flow.get('operating_cash_flow', 0) or 0,
                "capital_expenditures": abs(cash_flow.get('capex', 0) or 0),
                "depreciation_amortization": depreciation_amortization,

                # Balance sheet items
                "total_debt": total_debt,
                "total_equity": total_equity,
                "cash": balance.get('cash', 0) or 0,
                "total_assets": balance.get('total_assets', 0) or 0,
                "total_liabilities": balance.get('total_liabilities', 0) or 0,
                "working_capital": (balance.get('total_assets', 0) or 0) - (balance.get('total_liabilities', 0) or 0),
                "working_capital_change": 0,  # Would need historical data

                # Market metrics
                "beta": beta,
                "market_cap": market_cap,
                "tax_rate": 0.21,  # Default US corporate tax rate

                # Moat metrics (calculated from financials)
                "gross_margin": (income.get('gross_profit', 0) / income.get('revenue', 1)) if income.get('revenue') else 0,
                "operating_margin": (operating_income / income.get('revenue', 1)) if income.get('revenue') else 0,
                "revenue_growth": 0,  # Would need historical data
                "recurring_revenue_pct": 0,  # Would need business model data

                # Metadata
                "period": income.get('date', 'Unknown'),
                "data_source": "FMP API",
                "fetched_at": datetime.now().isoformat()
            }

            self.logger.info(
                f"Successfully fetched financial data for {symbol} "
                f"(period: {financial_data['period']})"
            )

            return financial_data

        except Exception as e:
            self.logger.error(
                f"Failed to get financial data for {symbol}: {e}",
                exc_info=True
            )
            return {"error": f"Failed to get financial data: {str(e)}"}

    def get_calculation_knowledge(self) -> Dict[str, Any]:
        """
        Get financial calculation knowledge from enriched datasets.

        Returns formulas, methodologies, and reference data for:
        - DCF valuation
        - Confidence factors
        - Risk assessments
        - Financial ratios

        Returns:
            Dict with financial calculation knowledge or empty dict if unavailable
        """
        if not self.enriched_data:
            self.logger.debug("Enriched data capability not available")
            return {}

        try:
            knowledge = self.enriched_data.get('financial_calculations', {})
            self.logger.debug(
                f"Retrieved calculation knowledge: "
                f"{len(knowledge)} categories"
            )
            return knowledge
        except Exception as e:
            self.logger.warning(f"Failed to get calculation knowledge: {e}")
            return {}

    def extract_symbol(self, request: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Extract stock symbol from request text or context.

        Checks context first, then parses request for ticker patterns.
        Looks for 1-5 letter uppercase alpha words (AAPL, MSFT, etc.)

        Args:
            request: Natural language request text
            context: Request context (may contain 'symbol' key)

        Returns:
            Stock symbol (uppercase) or None if not found
        """
        # Check context first
        if context and 'symbol' in context:
            symbol = context['symbol']
            self.logger.debug(f"Symbol from context: {symbol}")
            return symbol

        # Extract from request text
        words = request.upper().split()

        # Look for common stock symbol patterns (1-5 letters, all alpha)
        for word in words:
            if len(word) >= 1 and len(word) <= 5 and word.isalpha():
                self.logger.debug(f"Symbol from request: {word}")
                return word

        self.logger.warning(f"No symbol found in request: {request}")
        return None

    def assess_data_quality(self, financial_data: FinancialData) -> float:
        """
        Assess quality of financial data for confidence scoring.

        Quality factors:
        - Completeness: Presence of key fields (FCF, net income, revenue, EBIT)
        - Consistency: Reasonable ratios (FCF/NI should be < 3)

        Args:
            financial_data: Financial data dictionary

        Returns:
            Quality score (0.0-1.0), higher = better quality
        """
        if not financial_data or 'error' in financial_data:
            self.logger.debug("Low data quality: Missing or error data")
            return 0.3

        # Check for key financial metrics
        required_fields = ['free_cash_flow', 'net_income', 'revenue', 'ebit']
        present_fields = sum(1 for field in required_fields if financial_data.get(field) is not None)
        completeness_score = present_fields / len(required_fields)

        # Check for data consistency
        consistency_score = 0.8  # Default good consistency
        fcf = financial_data.get('free_cash_flow', 0)
        net_income = financial_data.get('net_income', 0)

        if fcf and net_income:
            fcf_ratio = abs(fcf / net_income) if net_income != 0 else 0
            if fcf_ratio > 3:  # Unusual FCF/NI ratio
                consistency_score -= 0.2
                self.logger.debug(
                    f"Consistency penalty: FCF/NI ratio = {fcf_ratio:.2f}"
                )

        # Calculate overall data quality
        data_quality = (completeness_score * 0.6 + consistency_score * 0.4)
        quality_score = min(1.0, max(0.0, data_quality))

        self.logger.debug(
            f"Data quality: {quality_score:.2f} "
            f"(completeness: {completeness_score:.2f}, "
            f"consistency: {consistency_score:.2f})"
        )

        return quality_score
