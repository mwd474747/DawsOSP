#!/usr/bin/env python3
"""
Financial Confidence Calculator - Extracted from FinancialAnalyst (Phase 2.1)

Calculates confidence scores for financial analyses based on data quality,
business predictability, and historical success rates.

Part of Phase 2 god object refactoring to reduce FinancialAnalyst complexity.

Phase 2.4: Uses FinancialConstants for all magic numbers.
"""

import logging
from typing import Dict, Any, Optional

# Phase 2.4: Import constants
from ...config.financial_constants import FinancialConstants

# Type aliases for clarity
FinancialData = Dict[str, Any]
ConfidenceFactors = Dict[str, Any]


class FinancialConfidenceCalculator:
    """
    Calculates confidence scores for financial analyses.

    Confidence Factors:
    - Data Quality: Completeness and consistency of financial data
    - Business Predictability: Stability indicated by ROIC, leverage
    - Historical Success Rate: Track record of analysis type (e.g., DCF)
    - Data Points: Number of available metrics

    Confidence Score Range: 0.0-1.0 (higher = more confident)
    """

    def __init__(self,
                 confidence_calculator_module: Any,
                 logger: logging.Logger = None):
        """
        Initialize confidence calculator.

        Args:
            confidence_calculator_module: Core confidence calculator module
            logger: Logger instance for diagnostic output
        """
        self.confidence_calc = confidence_calculator_module
        self.logger = logger or logging.getLogger(__name__)

    def calculate_confidence(self,
                            financial_data: FinancialData,
                            symbol: str,
                            confidence_factors: ConfidenceFactors = None,
                            data_quality: float = None) -> float:
        """
        Calculate comprehensive confidence score for financial analysis.

        Combines:
        1. Data quality (completeness, consistency)
        2. Business predictability (ROIC, leverage)
        3. Historical success rates (from knowledge base)
        4. Number of available data points

        Args:
            financial_data: Financial metrics dictionary
            symbol: Stock ticker symbol
            confidence_factors: Optional confidence factors from knowledge base
            data_quality: Optional pre-calculated data quality score

        Returns:
            Confidence score (0.0-1.0)
        """
        try:
            self.logger.debug(f"Calculating confidence for {symbol}")

            # Phase 2.4: Use FinancialConstants for data quality default
            if data_quality is None:
                # Will be calculated by assess_data_quality via data_fetcher
                data_quality = FinancialConstants.DEFAULT_DATA_QUALITY

            # Calculate business predictability
            business_predictability = self.assess_business_predictability(
                financial_data,
                symbol
            )

            # Phase 2.4: Get historical success rate from factors or FinancialConstants
            confidence_factors = confidence_factors or {}
            historical_success_rate = confidence_factors.get(
                'dcf_success_rate',
                FinancialConstants.DCF_HISTORICAL_SUCCESS_RATE
            )

            # Count available data points
            num_data_points = len([k for k, v in financial_data.items() if v is not None])

            # Use dynamic confidence calculator
            confidence_result = self.confidence_calc.calculate_confidence(
                data_quality=data_quality,
                model_accuracy=business_predictability,
                historical_success_rate=historical_success_rate,
                num_data_points=num_data_points,
                analysis_type='dcf'
            )

            confidence_score = confidence_result['confidence']

            self.logger.debug(
                f"Confidence for {symbol}: {confidence_score:.2f} "
                f"(data_quality: {data_quality:.2f}, "
                f"predictability: {business_predictability:.2f})"
            )

            return confidence_score

        except Exception as e:
            # Phase 2.4: Fallback using FinancialConstants
            self.logger.warning(
                f"Confidence calculation failed for {symbol}, using defaults: {e}"
            )
            return self.confidence_calc.calculate_confidence(
                data_quality=FinancialConstants.DEFAULT_DATA_QUALITY,
                analysis_type='dcf'
            )['confidence']

    def assess_business_predictability(self,
                                      financial_data: FinancialData,
                                      symbol: str) -> float:
        """
        Assess business predictability based on financial metrics.

        Predictability Indicators:
        - ROIC (Return on Invested Capital): Stable, high ROIC = predictable
        - Leverage (Debt/Equity): Low leverage = more predictable

        Args:
            financial_data: Financial metrics
            symbol: Stock ticker symbol

        Returns:
            Predictability score (0.3-1.0), higher = more predictable
        """
        # Phase 2.4: Use FinancialConstants for predictability calculation
        predictability = FinancialConstants.BASE_PREDICTABILITY

        # Higher predictability for stable metrics
        roic = self.calculate_roic_internal(financial_data)
        if roic and roic > FinancialConstants.STRONG_ROIC_THRESHOLD:
            predictability += FinancialConstants.STRONG_ROIC_PREDICTABILITY_BONUS
            self.logger.debug(f"{symbol} ROIC: {roic:.2%} (strong, +{FinancialConstants.STRONG_ROIC_PREDICTABILITY_BONUS} predictability)")
        elif roic and roic < FinancialConstants.WEAK_ROIC_THRESHOLD:
            predictability -= FinancialConstants.WEAK_ROIC_PREDICTABILITY_PENALTY
            self.logger.debug(f"{symbol} ROIC: {roic:.2%} (weak, -{FinancialConstants.WEAK_ROIC_PREDICTABILITY_PENALTY} predictability)")

        # Check debt levels (high debt = less predictable)
        debt_equity = financial_data.get('debt_to_equity', FinancialConstants.DEFAULT_DEBT_TO_EQUITY)
        if debt_equity > FinancialConstants.HIGH_LEVERAGE_THRESHOLD:
            predictability -= FinancialConstants.HIGH_LEVERAGE_PREDICTABILITY_PENALTY
            self.logger.debug(f"{symbol} D/E: {debt_equity:.2f} (high, -{FinancialConstants.HIGH_LEVERAGE_PREDICTABILITY_PENALTY} predictability)")
        elif debt_equity < FinancialConstants.LOW_LEVERAGE_THRESHOLD:
            predictability += FinancialConstants.LOW_LEVERAGE_PREDICTABILITY_BONUS
            self.logger.debug(f"{symbol} D/E: {debt_equity:.2f} (low, +{FinancialConstants.LOW_LEVERAGE_PREDICTABILITY_BONUS} predictability)")

        # Clamp to reasonable range using FinancialConstants
        predictability_score = min(
            FinancialConstants.MAX_PREDICTABILITY,
            max(FinancialConstants.MIN_PREDICTABILITY, predictability)
        )

        self.logger.debug(f"{symbol} predictability: {predictability_score:.2f}")

        return predictability_score

    def calculate_roic_internal(self, financial_data: FinancialData) -> Optional[float]:
        """
        Calculate ROIC (Return on Invested Capital) for predictability assessment.

        ROIC = NOPAT / Invested Capital
        where:
        - NOPAT = EBIT × (1 - Tax Rate)
        - Invested Capital = Working Capital + PP&E + Goodwill

        High ROIC (>15%) indicates competitive advantage and predictable returns.

        Args:
            financial_data: Financial metrics

        Returns:
            ROIC (decimal, e.g., 0.15 = 15%) or None if can't calculate
        """
        try:
            ebit = financial_data.get('ebit', 0)
            # Phase 2.4: Use FinancialConstants for tax rate default
            tax_rate = financial_data.get('tax_rate', FinancialConstants.CORPORATE_TAX_RATE)

            # Invested capital components
            working_capital = financial_data.get('working_capital', 0)
            ppe = financial_data.get('property_plant_equipment', 0)
            goodwill = financial_data.get('goodwill', 0)

            invested_capital = working_capital + ppe + goodwill

            if invested_capital > 0 and ebit:
                nopat = ebit * (1 - tax_rate)  # Net Operating Profit After Tax
                roic = nopat / invested_capital

                self.logger.debug(
                    f"ROIC calculation: NOPAT={nopat:,.0f}, "
                    f"Invested Capital={invested_capital:,.0f}, "
                    f"ROIC={roic:.2%}"
                )

                return roic

            self.logger.debug(
                "ROIC calculation skipped: "
                f"invested_capital={invested_capital}, ebit={ebit}"
            )
            return None

        except (KeyError, TypeError, ValueError) as e:
            self.logger.warning(f"Failed to calculate internal ROIC: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in ROIC calculation: {e}", exc_info=True)
            return None

    def calculate_debt_to_equity(self, financial_data: FinancialData) -> float:
        """
        Calculate Debt-to-Equity ratio for leverage assessment.

        D/E = Total Debt / Total Equity

        Interpretation:
        - D/E < 0.3: Conservative leverage (low risk)
        - D/E 0.3-1.0: Moderate leverage (balanced)
        - D/E > 1.0: High leverage (higher risk, less predictable)

        Args:
            financial_data: Financial metrics

        Returns:
            Debt-to-Equity ratio (0.0+), or default from FinancialConstants if can't calculate
        """
        try:
            total_debt = financial_data.get('total_debt', 0)
            total_equity = financial_data.get('total_equity', 0)

            if total_equity > 0:
                debt_equity = total_debt / total_equity
                self.logger.debug(
                    f"D/E: {debt_equity:.2f} "
                    f"(debt={total_debt:,.0f}, equity={total_equity:,.0f})"
                )
                return debt_equity

            # If no equity data, check if it's in financial_data directly
            if 'debt_to_equity' in financial_data:
                return financial_data['debt_to_equity']

            # Phase 2.4: Use FinancialConstants for default D/E
            self.logger.debug(
                f"D/E calculation failed, using default {FinancialConstants.DEFAULT_DEBT_TO_EQUITY}"
            )
            return FinancialConstants.DEFAULT_DEBT_TO_EQUITY

        except Exception as e:
            self.logger.warning(f"Failed to calculate D/E ratio: {e}")
            return FinancialConstants.DEFAULT_DEBT_TO_EQUITY
