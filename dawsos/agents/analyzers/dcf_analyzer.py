#!/usr/bin/env python3
"""
DCF Analyzer - Handles all Discounted Cash Flow valuation calculations

Extracted from FinancialAnalyst as part of Phase 2.1 god object refactoring.
Focuses solely on DCF-related calculations with clean, testable methods.

Key Methods:
- calculate_intrinsic_value: Main entry point for DCF analysis
- project_cash_flows: Project future free cash flows
- calculate_wacc: Calculate weighted average cost of capital
- calculate_present_values: Discount cash flows to present value
- estimate_terminal_value: Calculate terminal value using perpetuity model

Phase 2.4: Uses FinancialConstants for all magic numbers.
"""

from typing import Dict, List, Any
from core.typing_compat import TypeAlias
from datetime import datetime
import logging

# Phase 2.4: Import financial constants
from config.financial_constants import FinancialConstants

# Type aliases
FinancialData: TypeAlias = Dict[str, Any]
CashFlows: TypeAlias = List[float]

class DCFAnalyzer:
    """
    Performs Discounted Cash Flow (DCF) valuation analysis.

    Uses standard DCF methodology:
    1. Project future cash flows (5-year projection)
    2. Calculate discount rate (WACC using CAPM)
    3. Discount cash flows to present value
    4. Calculate terminal value using perpetuity growth model
    5. Sum present values for intrinsic value

    Example:
        analyzer = DCFAnalyzer(market_data, logger)
        result = analyzer.calculate_intrinsic_value("AAPL", financial_data)
        print(f"Intrinsic value: ${result['intrinsic_value']}")
    """

    def __init__(self, market_capability, logger: logging.Logger):
        """
        Initialize DCF Analyzer.

        Args:
            market_capability: Market data provider (for beta, etc.)
            logger: Logger instance for tracking calculations
        """
        self.market = market_capability
        self.logger = logger

    def calculate_intrinsic_value(
        self,
        symbol: str,
        financial_data: FinancialData,
        growth_rates: List[float] = None,
        discount_rate: float = None
    ) -> Dict[str, Any]:
        """
        Calculate DCF intrinsic value for a stock.

        Args:
            symbol: Stock ticker symbol
            financial_data: Company financial data (FCF, debt, equity, etc.)
            growth_rates: Optional custom growth rates (default: declining 8%->3%)
            discount_rate: Optional custom discount rate (default: calculated WACC)

        Returns:
            Dictionary containing:
                - intrinsic_value: Calculated intrinsic value
                - projected_fcf: Projected free cash flows
                - discount_rate: Discount rate used
                - terminal_value: Terminal value (present value)
                - present_values: Present values of each projected CF
                - methodology: Description of methodology used
        """
        try:
            # Step 1: Project Cash Flows
            if growth_rates:
                projected_fcf = self._project_cash_flows_custom(
                    financial_data,
                    growth_rates
                )
            else:
                projected_fcf = self.project_cash_flows(financial_data, symbol)

            # Step 2: Calculate Discount Rate (WACC)
            if discount_rate is None:
                discount_rate = self.calculate_wacc(financial_data, symbol)

            # Step 3: Calculate Present Values
            present_values = self.calculate_present_values(projected_fcf, discount_rate)

            # Step 4: Estimate Terminal Value
            terminal_value = self.estimate_terminal_value(projected_fcf, discount_rate)

            # Step 5: Sum NPV
            intrinsic_value = sum(present_values) + terminal_value

            self.logger.info(
                f"DCF analysis for {symbol}: Intrinsic value ${intrinsic_value:,.2f} "
                f"(discount rate: {discount_rate:.2%})"
            )

            return {
                "symbol": symbol,
                "intrinsic_value": round(intrinsic_value, 2),
                "projected_fcf": projected_fcf,
                "discount_rate": discount_rate,
                "terminal_value": terminal_value,
                "present_values": present_values,
                "methodology": "Standard DCF with declining growth rates"
            }

        except Exception as e:
            self.logger.error(f"DCF analysis failed for {symbol}: {e}", exc_info=True)
            raise

    def project_cash_flows(
        self,
        financial_data: FinancialData,
        symbol: str,
        years: int = None
    ) -> CashFlows:
        """
        Project future cash flows based on historical data.

        Uses conservative declining growth rate assumptions from FinancialConstants.

        Args:
            financial_data: Company financial data
            symbol: Stock ticker (for logging)
            years: Number of years to project (default: from constants)

        Returns:
            List of projected free cash flows
        """
        if years is None:
            years = FinancialConstants.DCF_PROJECTION_YEARS

        try:
            # Get historical FCF
            current_fcf = financial_data.get('free_cash_flow', 0)

            if current_fcf <= 0:
                self.logger.warning(
                    f"{symbol} has zero or negative FCF ({current_fcf}), "
                    f"using conservative estimates"
                )
                # Fallback to conservative estimates
                return [100, 105, 110, 115, 120]

            # Use conservative declining growth assumption from constants
            growth_rates = FinancialConstants.DEFAULT_GROWTH_RATES[:years]

            projected_fcf = []
            fcf = current_fcf

            for i, growth_rate in enumerate(growth_rates, 1):
                fcf = fcf * (1 + growth_rate)
                projected_fcf.append(fcf)
                self.logger.debug(
                    f"{symbol} Year {i}: FCF ${fcf:,.0f} (growth: {growth_rate:.1%})"
                )

            return projected_fcf

        except Exception as e:
            self.logger.error(f"Cash flow projection failed for {symbol}: {e}")
            # Fallback to conservative estimates
            return [100, 105, 110, 115, 120]

    def _project_cash_flows_custom(
        self,
        financial_data: FinancialData,
        growth_rates: List[float]
    ) -> CashFlows:
        """Project cash flows with custom growth rates."""
        current_fcf = financial_data.get('free_cash_flow', 0)
        if current_fcf <= 0:
            return [100 * (1 + g) for g in growth_rates]

        projected_fcf = []
        fcf = current_fcf
        for growth_rate in growth_rates:
            fcf = fcf * (1 + growth_rate)
            projected_fcf.append(fcf)

        return projected_fcf

    def calculate_wacc(
        self,
        financial_data: FinancialData,
        symbol: str
    ) -> float:
        """
        Calculate Weighted Average Cost of Capital (WACC).

        Uses simplified CAPM (Capital Asset Pricing Model):
        Cost of Equity = Risk-Free Rate + Beta × Market Risk Premium

        Assumptions:
        - Risk-free rate: 4.5% (10-year Treasury)
        - Market risk premium: 6%
        - Beta: From financial data (default: 1.0)
        - Assumed mostly equity-financed for simplicity

        Args:
            financial_data: Company financial data (must contain 'beta')
            symbol: Stock ticker (for logging)

        Returns:
            WACC as decimal (e.g., 0.105 for 10.5%)
        """
        try:
            # CAPM components from FinancialConstants
            risk_free_rate = FinancialConstants.RISK_FREE_RATE
            market_risk_premium = FinancialConstants.MARKET_RISK_PREMIUM
            beta = financial_data.get('beta', FinancialConstants.DEFAULT_BETA)

            # Calculate cost of equity using CAPM
            cost_of_equity = risk_free_rate + (beta * market_risk_premium)

            # For simplicity, assume mostly equity financed
            # In full implementation, would calculate:
            # WACC = (E/V × Cost of Equity) + (D/V × Cost of Debt × (1 - Tax Rate))
            wacc = cost_of_equity

            self.logger.debug(
                f"{symbol} WACC calculation: "
                f"Risk-free={risk_free_rate:.2%}, Beta={beta:.2f}, "
                f"MRP={market_risk_premium:.2%}, WACC={wacc:.2%}"
            )

            return wacc

        except Exception as e:
            self.logger.warning(f"WACC calculation failed for {symbol}: {e}, using default")
            return FinancialConstants.DEFAULT_DISCOUNT_RATE

    def calculate_present_values(
        self,
        projected_fcf: CashFlows,
        discount_rate: float
    ) -> List[float]:
        """
        Calculate present values of projected cash flows.

        Discounts each future cash flow to present value using:
        PV = FCF / (1 + discount_rate) ^ year

        Args:
            projected_fcf: List of projected free cash flows
            discount_rate: Discount rate (WACC) as decimal

        Returns:
            List of present values corresponding to each projected CF
        """
        present_values = []

        for year, fcf in enumerate(projected_fcf, 1):
            pv = fcf / ((1 + discount_rate) ** year)
            present_values.append(pv)
            self.logger.debug(f"Year {year}: FCF ${fcf:,.0f} → PV ${pv:,.0f}")

        return present_values

    def estimate_terminal_value(
        self,
        projected_fcf: CashFlows,
        discount_rate: float,
        terminal_growth_rate: float = None
    ) -> float:
        """
        Estimate terminal value using perpetual growth model.

        Uses Gordon Growth Model (Perpetuity Formula):
        Terminal Value = (Final FCF × (1 + g)) / (r - g)

        Then discounts to present value:
        PV(Terminal Value) = Terminal Value / (1 + r) ^ years

        Args:
            projected_fcf: List of projected free cash flows
            discount_rate: Discount rate (WACC) as decimal
            terminal_growth_rate: Perpetual growth rate (default: from constants)

        Returns:
            Present value of terminal value
        """
        if terminal_growth_rate is None:
            terminal_growth_rate = FinancialConstants.TERMINAL_GROWTH_RATE
        if not projected_fcf:
            self.logger.warning("No projected cash flows, terminal value is 0")
            return 0

        # Get final year FCF
        final_fcf = projected_fcf[-1]

        # Calculate terminal value using perpetuity formula
        terminal_value = (final_fcf * (1 + terminal_growth_rate)) / (
            discount_rate - terminal_growth_rate
        )

        # Discount terminal value to present
        years = len(projected_fcf)
        present_terminal_value = terminal_value / ((1 + discount_rate) ** years)

        self.logger.debug(
            f"Terminal value: Final FCF ${final_fcf:,.0f}, "
            f"TV ${terminal_value:,.0f}, PV(TV) ${present_terminal_value:,.0f}"
        )

        return present_terminal_value
