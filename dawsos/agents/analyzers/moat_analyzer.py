#!/usr/bin/env python3
"""
Moat Analyzer - Extracted from FinancialAnalyst (Phase 2.1)

Analyzes economic moats (competitive advantages) for companies.
Evaluates 5 moat factors: brand, network effects, cost advantages,
switching costs, and intangible assets.

Part of Phase 2 god object refactoring to reduce FinancialAnalyst complexity.

Phase 2.4: Uses FinancialConstants for all magic numbers.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Callable

# Phase 2.4: Import financial constants
from ...config.financial_constants import FinancialConstants

# Type aliases for clarity
FinancialData = Dict[str, Any]
MoatScores = Dict[str, float]
MoatAnalysis = Dict[str, Any]


class MoatAnalyzer:
    """
    Performs economic moat (competitive advantage) analysis.

    Moat Factors (0-10 each, max 50 total):
    - Brand Power: Pricing power indicated by gross margins
    - Network Effects: Growth acceleration in tech/comm services
    - Cost Advantages: Operational efficiency via operating margins
    - Switching Costs: Customer retention (recurring revenue proxy)
    - Intangible Assets: Patents, licenses, regulatory advantages

    Ratings (from FinancialConstants):
    - Wide Moat: Score > WIDE_MOAT_THRESHOLD (strong, durable advantage)
    - Narrow Moat: Score > NARROW_MOAT_THRESHOLD (moderate, temporary advantage)
    - No Moat: Score < NARROW_MOAT_THRESHOLD (commodity, competitive market)
    """

    def __init__(self, logger: logging.Logger):
        """
        Initialize moat analyzer.

        Args:
            logger: Logger instance for diagnostic output
        """
        self.logger = logger

    def analyze_moat(self,
                     symbol: str,
                     financial_data: FinancialData) -> MoatAnalysis:
        """
        Perform comprehensive moat analysis for a company.

        Args:
            symbol: Stock ticker symbol
            financial_data: Dictionary with financial metrics:
                - gross_margin: Gross profit / Revenue
                - operating_margin: Operating income / Revenue
                - sector: Industry classification
                - revenue_growth: YoY revenue growth rate
                - recurring_revenue_pct: Percent of recurring revenue

        Returns:
            Dict with moat_rating, overall_score, factor scores, and evidence
        """
        self.logger.info(f"Starting moat analysis for {symbol}")

        # Calculate individual moat factors
        moat_scores: MoatScores = {
            'brand': self.evaluate_brand_strength(financial_data),
            'network_effects': self.evaluate_network_effects(financial_data),
            'cost_advantages': self.evaluate_cost_advantages(financial_data),
            'switching_costs': self.evaluate_switching_costs(financial_data),
            'intangible_assets': self.evaluate_intangible_assets(financial_data)
        }

        # Calculate overall moat score and rating
        total_score = sum(moat_scores.values())
        moat_rating = self._calculate_moat_rating(total_score)

        self.logger.info(
            f"{symbol} moat analysis complete: {moat_rating} "
            f"(score: {total_score:.1f}/50)"
        )

        # Prepare detailed analysis
        analysis = {
            'symbol': symbol,
            'moat_rating': moat_rating,
            'overall_score': total_score,
            'factors': moat_scores,
            'financial_evidence': {
                'gross_margin': f"{financial_data.get('gross_margin', 0):.1%}",
                'operating_margin': f"{financial_data.get('operating_margin', 0):.1%}",
                'revenue_growth': f"{financial_data.get('revenue_growth', 0):.1%}",
                'sector': financial_data.get('sector', 'Unknown')
            },
            'timestamp': datetime.now().isoformat()
        }

        return analysis

    def evaluate_brand_strength(self, financial_data: FinancialData) -> float:
        """
        Evaluate brand moat based on pricing power (gross margins).

        Companies with strong brands can charge premium prices,
        leading to high gross margins (from FinancialConstants).

        Args:
            financial_data: Financial metrics

        Returns:
            Brand score (0-10)
        """
        gross_margin = financial_data.get('gross_margin', 0)

        if gross_margin <= FinancialConstants.BRAND_MOAT_GROSS_MARGIN_THRESHOLD:
            score = 0
        else:
            # Score = gross_margin * multiplier, capped at 10
            score = min(10, gross_margin * FinancialConstants.BRAND_MOAT_MULTIPLIER)

        self.logger.debug(
            f"Brand strength: {score:.1f}/10 "
            f"(gross margin: {gross_margin:.1%})"
        )

        return score

    def evaluate_network_effects(self, financial_data: FinancialData) -> float:
        """
        Evaluate network effects moat (primarily tech/comm services).

        Network effects occur when product value increases with more users
        (social networks, marketplaces, platforms). Indicated by high
        growth rates in tech sectors (from FinancialConstants).

        Args:
            financial_data: Financial metrics

        Returns:
            Network effects score (0-10)
        """
        sector = financial_data.get('sector', '')
        revenue_growth = financial_data.get('revenue_growth', 0)

        # Only applicable to tech and communication services
        if sector not in FinancialConstants.NETWORK_EFFECTS_SECTORS:
            self.logger.debug(f"Network effects: 0/10 (sector: {sector})")
            return 0

        if revenue_growth <= FinancialConstants.NETWORK_EFFECTS_GROWTH_THRESHOLD:
            score = 0
        else:
            # Score = revenue_growth * multiplier, capped at 10
            score = min(10, revenue_growth * FinancialConstants.NETWORK_EFFECTS_MULTIPLIER)

        self.logger.debug(
            f"Network effects: {score:.1f}/10 "
            f"(growth: {revenue_growth:.1%}, sector: {sector})"
        )

        return score

    def evaluate_cost_advantages(self, financial_data: FinancialData) -> float:
        """
        Evaluate cost advantage moat (operating efficiency).

        Companies with structural cost advantages (economies of scale,
        unique processes, proprietary technology) achieve high operating
        margins (from FinancialConstants).

        Args:
            financial_data: Financial metrics

        Returns:
            Cost advantages score (0-10)
        """
        operating_margin = financial_data.get('operating_margin', 0)

        if operating_margin <= FinancialConstants.COST_ADVANTAGES_MARGIN_THRESHOLD:
            score = 0
        else:
            # Score = operating_margin * multiplier, capped at 10
            score = min(10, operating_margin * FinancialConstants.COST_ADVANTAGES_MULTIPLIER)

        self.logger.debug(
            f"Cost advantages: {score:.1f}/10 "
            f"(operating margin: {operating_margin:.1%})"
        )

        return score

    def evaluate_switching_costs(self, financial_data: FinancialData) -> float:
        """
        Evaluate switching costs moat (customer retention).

        High switching costs (contractual, integration, learning curve)
        create customer stickiness. Approximated by recurring revenue
        percentage (from FinancialConstants).

        Args:
            financial_data: Financial metrics

        Returns:
            Switching costs score (0-10)
        """
        recurring_revenue_pct = financial_data.get('recurring_revenue_pct', 0)

        if recurring_revenue_pct <= FinancialConstants.SWITCHING_COSTS_RECURRING_THRESHOLD:
            score = 0
        else:
            # High recurring revenue = base score from constants
            score = FinancialConstants.SWITCHING_COSTS_BASE_SCORE

        self.logger.debug(
            f"Switching costs: {score:.1f}/10 "
            f"(recurring revenue: {recurring_revenue_pct:.1%})"
        )

        return score

    def evaluate_intangible_assets(self, financial_data: FinancialData) -> float:
        """
        Evaluate intangible assets moat (patents, licenses, regulations).

        Intangible assets (patents, regulatory approvals, licenses,
        trademarks) provide legal/regulatory barriers to competition.

        Currently placeholder - would need additional data sources:
        - Patent counts and quality
        - Regulatory filings
        - License exclusivity
        - Brand trademark value

        Args:
            financial_data: Financial metrics

        Returns:
            Intangible assets score (0-10)
        """
        # TODO: Implement when patent/regulatory data sources available
        # For now, return 0 (conservative approach)
        score = 0

        self.logger.debug("Intangible assets: 0/10 (data source pending)")

        return score

    def _calculate_moat_rating(self, total_score: float) -> str:
        """
        Convert numeric moat score to categorical rating.

        Uses thresholds from FinancialConstants.

        Args:
            total_score: Sum of all moat factor scores (0-50)

        Returns:
            'Wide', 'Narrow', or 'None'
        """
        if total_score > FinancialConstants.WIDE_MOAT_THRESHOLD:
            return 'Wide'
        elif total_score > FinancialConstants.NARROW_MOAT_THRESHOLD:
            return 'Narrow'
        else:
            return 'None'
