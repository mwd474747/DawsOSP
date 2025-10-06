#!/usr/bin/env python3
"""
Fetch Financials Action - Fetch financial data via data harvester

Fetches financial statements and data using the data_harvester agent.
Provides structured financial data for analysis patterns.

Priority: 📊 Business Logic - Critical for financial analysis
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class FetchFinancialsAction(ActionHandler):
    """
    Fetch financial data using data harvester.

    Requests financial data from data_harvester agent, including:
    - Financial statements (income, balance, cash flow)
    - Quarterly/annual periods
    - Symbol-specific data

    Pattern Example:
        {
            "action": "fetch_financials",
            "symbol": "{SYMBOL}",
            "data_type": "financial_statements",
            "period": "quarter"
        }
    """

    @property
    def action_name(self) -> str:
        return "fetch_financials"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Fetch financial data via data harvester.

        Args:
            params: Must contain 'symbol', optional 'data_type', 'period'
            context: Current execution context (may contain 'symbol')
            outputs: Previous step outputs

        Returns:
            Financial data with symbol, data_type, period, and source
        """
        # Extract and resolve parameters
        symbol = self._resolve_param(
            params.get('symbol') or context.get('symbol', 'AAPL'),
            context,
            outputs
        )
        data_type = params.get('data_type', 'financial_statements')
        period = params.get('period', 'quarter')

        # Try to use data harvester agent
        data_harvester = self._get_agent('data_harvester')
        if data_harvester and hasattr(data_harvester, 'harvest'):
            try:
                # Request financial data
                request = f"{data_type} for {symbol} {period}"
                result = data_harvester.harvest(request)

                if result and 'data' in result:
                    self.logger.info(
                        f"Fetched financials for {symbol} via data_harvester "
                        f"(type={data_type}, period={period})"
                    )
                    return {
                        'financials': result['data'],
                        'symbol': symbol,
                        'data_type': data_type,
                        'period': period,
                        'source': 'data_harvester'
                    }
                else:
                    self.logger.warning(
                        f"Data harvester returned no data for {symbol}, using fallback"
                    )
            except Exception as e:
                self.logger.warning(
                    f"Data harvester failed for {symbol}: {e}, using fallback"
                )

        # Fallback: structured placeholder
        self.logger.debug(
            f"Using placeholder financials for {symbol} "
            f"(data_harvester not available or failed)"
        )

        return {
            'financials': {
                'revenue': f"{symbol} revenue data needed",
                'net_income': f"{symbol} earnings data needed",
                'cash_flow': f"{symbol} cash flow data needed",
                'note': 'Placeholder data - data_harvester not available'
            },
            'symbol': symbol,
            'data_type': data_type,
            'period': period,
            'source': 'placeholder'
        }

    def _get_agent(self, agent_name: str):
        """Get agent from runtime if available."""
        if self.runtime and hasattr(self.runtime, 'agents'):
            return self.runtime.agents.get(agent_name)
        return None
