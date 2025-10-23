"""
Risk Service (DaR - Drawdown at Risk)

Purpose: Scenario-based risk calculation (Sprint 3 Week 5)
Updated: 2025-10-22
Priority: P1 (Sprint 3)

Features:
    - DaR (Drawdown at Risk) calculation at 95% confidence
    - Scenario stress testing
    - Historical scenario library
    - Portfolio-specific risk metrics

DaR Concept:
    Similar to VaR (Value at Risk), but measures potential drawdown instead of
    absolute loss. Answers: "What's the worst drawdown in the next 30 days at
    95% confidence?"

Scenarios:
    - Historical: 2008 Financial Crisis, 2020 COVID crash, etc.
    - Hypothetical: Yield curve +200bp, Oil shock, etc.
    - Regime-based: Transition to recession, etc.

Architecture:
    Portfolio → Scenarios → Stress Test → DaR Distribution → 95th Percentile

Usage:
    service = RiskService()
    dar = await service.compute_dar(portfolio_id, confidence=0.95)
    scenarios = await service.get_dar_scenarios(portfolio_id)
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import statistics

from backend.app.db.connection import execute_query, execute_statement, execute_query_one

logger = logging.getLogger("DawsOS.RiskService")


# ============================================================================
# Enums and Data Models
# ============================================================================


class ScenarioType(str, Enum):
    """Scenario types."""

    HISTORICAL = "HISTORICAL"  # Historical crisis
    HYPOTHETICAL = "HYPOTHETICAL"  # Hypothetical shock
    REGIME_TRANSITION = "REGIME_TRANSITION"  # Regime change


@dataclass
class Scenario:
    """Stress test scenario."""

    scenario_id: str
    name: str
    scenario_type: ScenarioType
    description: str

    # Asset class shocks (returns in decimal, e.g., -0.20 = -20%)
    equity_shock: float
    bond_shock: float
    commodity_shock: float
    fx_shock: Dict[str, float]  # {"USD": 0.0, "CAD": -0.05, ...}

    # Probability (for DaR calculation)
    probability: float  # 0-1


@dataclass
class DaRResult:
    """Drawdown at Risk result."""

    portfolio_id: str
    confidence: float  # 0-1
    dar: float  # DaR in percent (e.g., -0.15 = -15% drawdown)
    horizon_days: int  # Forecast horizon

    # Scenario breakdown
    worst_scenario: str
    worst_drawdown: float
    scenarios_tested: int

    # Date
    as_of_date: date


@dataclass
class StressTestResult:
    """Stress test result for a scenario."""

    scenario_id: str
    scenario_name: str
    portfolio_id: str

    # Pre-stress values
    pre_stress_nav: Decimal

    # Post-stress values
    post_stress_nav: Decimal
    drawdown: float  # Percent drawdown (negative)

    # Asset class breakdown
    asset_class_breakdown: Dict[str, float]

    # Date
    as_of_date: date


# ============================================================================
# Scenario Library
# ============================================================================

# Historical scenarios
HISTORICAL_SCENARIOS = [
    Scenario(
        scenario_id="CRISIS_2008",
        name="2008 Financial Crisis",
        scenario_type=ScenarioType.HISTORICAL,
        description="Oct 2007 - Mar 2009: Global financial crisis, equity -57%, credit spreads +600bp",
        equity_shock=-0.57,  # S&P 500 peak-to-trough
        bond_shock=-0.05,  # Government bonds rallied (flight to quality)
        commodity_shock=-0.30,  # Oil crashed
        fx_shock={"USD": 0.10, "CAD": -0.15, "EUR": -0.05},  # USD strengthened
        probability=0.01,  # 1% probability in any given 30-day period
    ),
    Scenario(
        scenario_id="COVID_2020",
        name="2020 COVID Crash",
        scenario_type=ScenarioType.HISTORICAL,
        description="Feb - Mar 2020: COVID pandemic, equity -34% in 23 days",
        equity_shock=-0.34,  # S&P 500 Feb 19 - Mar 23
        bond_shock=-0.02,  # Government bonds rallied
        commodity_shock=-0.50,  # Oil crashed to negative
        fx_shock={"USD": 0.05, "CAD": -0.10, "EUR": -0.03},
        probability=0.02,  # 2% probability (black swan)
    ),
    Scenario(
        scenario_id="TECH_BUST_2000",
        name="2000 Tech Bust",
        scenario_type=ScenarioType.HISTORICAL,
        description="Mar 2000 - Oct 2002: Dot-com bust, NASDAQ -78%",
        equity_shock=-0.45,  # S&P 500 peak-to-trough (broader market)
        bond_shock=0.05,  # Bonds rallied
        commodity_shock=-0.10,
        fx_shock={"USD": -0.05, "CAD": 0.0, "EUR": 0.05},
        probability=0.01,
    ),
]

# Hypothetical scenarios
HYPOTHETICAL_SCENARIOS = [
    Scenario(
        scenario_id="YIELD_SURGE",
        name="Yield Surge +200bp",
        scenario_type=ScenarioType.HYPOTHETICAL,
        description="10Y yield rises 200bp, bond prices fall, equity multiple compression",
        equity_shock=-0.15,  # P/E compression
        bond_shock=-0.10,  # Duration ~7, 200bp * 7 = -14% (using -10% conservative)
        commodity_shock=0.0,
        fx_shock={"USD": 0.05, "CAD": -0.03, "EUR": -0.02},  # USD strengthens
        probability=0.05,  # 5% probability
    ),
    Scenario(
        scenario_id="OIL_SHOCK",
        name="Oil Shock +$50/bbl",
        scenario_type=ScenarioType.HYPOTHETICAL,
        description="Oil price spikes $50/bbl, inflation shock",
        equity_shock=-0.10,  # Stagflation concerns
        bond_shock=-0.05,  # Inflation expectations rise
        commodity_shock=0.30,  # Energy stocks benefit
        fx_shock={"USD": 0.02, "CAD": 0.08, "EUR": -0.02},  # CAD strengthens (oil exporter)
        probability=0.03,
    ),
    Scenario(
        scenario_id="RECESSION_MILD",
        name="Mild Recession",
        scenario_type=ScenarioType.HYPOTHETICAL,
        description="Mild recession, GDP -2%, unemployment +2%",
        equity_shock=-0.20,
        bond_shock=0.03,  # Flight to quality
        commodity_shock=-0.15,
        fx_shock={"USD": 0.03, "CAD": -0.05, "EUR": -0.02},
        probability=0.10,  # 10% probability (most likely severe scenario)
    ),
]

# Regime transition scenarios
REGIME_SCENARIOS = [
    Scenario(
        scenario_id="EXPANSION_TO_CONTRACTION",
        name="Expansion → Contraction",
        scenario_type=ScenarioType.REGIME_TRANSITION,
        description="Transition from late expansion to early contraction",
        equity_shock=-0.12,
        bond_shock=0.02,
        commodity_shock=-0.08,
        fx_shock={"USD": 0.02, "CAD": -0.03, "EUR": -0.01},
        probability=0.15,  # 15% probability (common transition)
    ),
]

# Combined scenario library
ALL_SCENARIOS = HISTORICAL_SCENARIOS + HYPOTHETICAL_SCENARIOS + REGIME_SCENARIOS


# ============================================================================
# Risk Service
# ============================================================================


class RiskService:
    """
    Risk service for DaR calculation.

    Computes Drawdown at Risk (DaR) using scenario stress testing.
    """

    def __init__(self):
        self.scenarios = ALL_SCENARIOS

    async def get_portfolio_holdings(self, portfolio_id: str) -> List[Dict]:
        """
        Get portfolio holdings for stress testing.

        Args:
            portfolio_id: Portfolio UUID

        Returns:
            List of holdings with asset class mapping
        """
        query = """
            SELECT
                l.symbol,
                l.quantity,
                l.cost_basis_per_share,
                l.currency,
                l.quantity * l.cost_basis_per_share AS market_value
            FROM lots l
            WHERE l.portfolio_id = $1
              AND l.is_open = true
              AND l.quantity > 0
        """
        holdings = await execute_query(query, portfolio_id)

        # TODO: Add asset class classification
        # For now, assume all equity (will be enhanced later)
        for holding in holdings:
            holding["asset_class"] = "EQUITY"

        return holdings

    async def apply_scenario(
        self,
        portfolio_id: str,
        scenario: Scenario,
        as_of_date: date,
    ) -> StressTestResult:
        """
        Apply stress scenario to portfolio.

        Args:
            portfolio_id: Portfolio UUID
            scenario: Scenario to apply
            as_of_date: Date for stress test

        Returns:
            StressTestResult
        """
        # Get holdings
        holdings = await self.get_portfolio_holdings(portfolio_id)

        if not holdings:
            logger.warning(f"No holdings found for portfolio {portfolio_id}")
            return StressTestResult(
                scenario_id=scenario.scenario_id,
                scenario_name=scenario.name,
                portfolio_id=portfolio_id,
                pre_stress_nav=Decimal("0"),
                post_stress_nav=Decimal("0"),
                drawdown=0.0,
                asset_class_breakdown={},
                as_of_date=as_of_date,
            )

        # Compute pre-stress NAV
        pre_stress_nav = sum(Decimal(str(h["market_value"])) for h in holdings)

        # Apply shocks by asset class
        post_stress_nav = Decimal("0")
        asset_class_breakdown = {}

        for holding in holdings:
            asset_class = holding["asset_class"]
            pre_value = Decimal(str(holding["market_value"]))

            # Determine shock
            if asset_class == "EQUITY":
                shock = scenario.equity_shock
            elif asset_class == "BOND":
                shock = scenario.bond_shock
            elif asset_class == "COMMODITY":
                shock = scenario.commodity_shock
            else:
                shock = 0.0  # Unknown asset class

            # Apply shock
            post_value = pre_value * Decimal(str(1 + shock))
            post_stress_nav += post_value

            # Track by asset class
            if asset_class not in asset_class_breakdown:
                asset_class_breakdown[asset_class] = 0.0
            asset_class_breakdown[asset_class] += float(post_value - pre_value)

        # Compute drawdown
        drawdown = float((post_stress_nav - pre_stress_nav) / pre_stress_nav)

        logger.info(
            f"Scenario {scenario.scenario_id}: {drawdown*100:.2f}% drawdown "
            f"(NAV: {pre_stress_nav:.2f} → {post_stress_nav:.2f})"
        )

        return StressTestResult(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            portfolio_id=portfolio_id,
            pre_stress_nav=pre_stress_nav,
            post_stress_nav=post_stress_nav,
            drawdown=drawdown,
            asset_class_breakdown=asset_class_breakdown,
            as_of_date=as_of_date,
        )

    async def compute_dar(
        self,
        portfolio_id: str,
        confidence: float = 0.95,
        horizon_days: int = 30,
        as_of_date: Optional[date] = None,
    ) -> DaRResult:
        """
        Compute Drawdown at Risk (DaR).

        Args:
            portfolio_id: Portfolio UUID
            confidence: Confidence level (default: 0.95 = 95%)
            horizon_days: Forecast horizon in days (default: 30)
            as_of_date: Date for calculation (default: today)

        Returns:
            DaRResult
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Run stress tests for all scenarios
        results = []
        for scenario in self.scenarios:
            result = await self.apply_scenario(portfolio_id, scenario, as_of_date)
            results.append(result)

        if not results:
            raise ValueError("No stress test results")

        # Sort by drawdown (worst first)
        results.sort(key=lambda r: r.drawdown)

        # Compute DaR at confidence level
        # For 95% confidence, we take the 5th percentile (worst 5% of outcomes)
        percentile = 1 - confidence  # 95% confidence = 5th percentile
        index = int(len(results) * percentile)
        dar_scenario = results[index]

        dar = dar_scenario.drawdown

        # Find absolute worst case
        worst_scenario = results[0]

        logger.info(
            f"DaR ({confidence*100:.0f}% confidence, {horizon_days}d): {dar*100:.2f}% "
            f"(worst case: {worst_scenario.drawdown*100:.2f}% in {worst_scenario.scenario_name})"
        )

        return DaRResult(
            portfolio_id=portfolio_id,
            confidence=confidence,
            dar=dar,
            horizon_days=horizon_days,
            worst_scenario=worst_scenario.scenario_name,
            worst_drawdown=worst_scenario.drawdown,
            scenarios_tested=len(results),
            as_of_date=as_of_date,
        )

    async def get_dar_scenarios(self, portfolio_id: str) -> List[StressTestResult]:
        """
        Get all stress test scenarios for a portfolio.

        Args:
            portfolio_id: Portfolio UUID

        Returns:
            List of StressTestResult
        """
        as_of_date = date.today()
        results = []

        for scenario in self.scenarios:
            result = await self.apply_scenario(portfolio_id, scenario, as_of_date)
            results.append(result)

        # Sort by drawdown (worst first)
        results.sort(key=lambda r: r.drawdown)

        return results


# ============================================================================
# Singleton
# ============================================================================


_risk_service: Optional[RiskService] = None


def get_risk_service() -> RiskService:
    """
    Get risk service singleton.

    Returns:
        RiskService singleton
    """
    global _risk_service
    if _risk_service is None:
        _risk_service = RiskService()
    return _risk_service
