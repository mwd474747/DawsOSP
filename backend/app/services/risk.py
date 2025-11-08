"""
Risk Service (DaR - Drawdown at Risk)

Purpose: Regime-conditioned risk calculation using Monte Carlo simulation
Updated: 2025-10-23
Priority: P0 (Critical for risk management)

Features:
    - DaR (Drawdown at Risk) calculation at 95% confidence
    - Regime-conditioned covariance matrices
    - Monte Carlo simulation (10,000 scenarios)
    - Factor-based risk attribution
    - Historical and hypothetical scenarios

DaR Concept (PRODUCT_SPEC.md §7):
    Similar to VaR (Value at Risk), but measures potential drawdown instead of
    absolute loss. Answers: "What's the worst drawdown in the next 30 days at
    95% confidence given the current macro regime?"

Methodology:
    1. Determine current macro regime
    2. Load regime-specific covariance matrix
    3. Compute portfolio factor exposures (betas)
    4. Run Monte Carlo simulation (10k scenarios)
    5. Extract 95th percentile drawdown

Architecture:
    Portfolio → Factor Betas → Regime Covariance → Monte Carlo → DaR (95%)

Usage:
    from app.services.risk import get_risk_service
    from app.services.macro import MacroService

    # Detect current regime
    # Create macro service instance directly (should be passed via DI container)
    macro_service = MacroService(db_pool=db_pool) if db_pool else MacroService()
    regime = await macro_service.detect_current_regime()

    # Compute DaR
    risk_service = get_risk_service()
    dar = await service.compute_dar(
        portfolio_id="...",
        regime=regime.regime.value,
        confidence=0.95,
    )
"""

import logging
import random
import numpy as np
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import statistics

from app.db.connection import execute_query, execute_statement, execute_query_one

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
    """Drawdown at Risk result (regime-conditioned)."""

    portfolio_id: str
    regime: str  # Macro regime (e.g., "MID_EXPANSION")
    confidence: float  # 0-1
    dar: float  # DaR in percent (e.g., -0.15 = -15% drawdown)
    horizon_days: int  # Forecast horizon

    # Monte Carlo simulation
    simulations: int  # Number of simulations run
    worst_drawdown: float  # Absolute worst case
    median_drawdown: float  # 50th percentile
    best_case: float  # Best case (could be positive)

    # Date (must come before fields with defaults)
    as_of_date: date

    # Factor attribution
    factor_contributions: Dict[str, float] = field(default_factory=dict)

    # Metadata
    nav: Decimal = Decimal("0")  # Current NAV


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

    Computes Drawdown at Risk (DaR) using regime-conditioned Monte Carlo simulation.
    """

    # Regime-conditioned covariance matrices (factor returns)
    # Covariance of: [real_rates, inflation, credit_spread, usd, equity]
    # Units: monthly returns (e.g., 0.01 = 1% monthly return)
    REGIME_COVARIANCES = {
        "EARLY_EXPANSION": np.array([
            # real_rates, inflation, credit, usd, equity
            [0.0004, -0.0001, -0.0002, 0.0001, -0.0003],  # real_rates
            [-0.0001, 0.0002, 0.0000, 0.0000, 0.0001],   # inflation
            [-0.0002, 0.0000, 0.0003, -0.0001, -0.0004],  # credit
            [0.0001, 0.0000, -0.0001, 0.0015, 0.0002],   # usd
            [-0.0003, 0.0001, -0.0004, 0.0002, 0.0025],  # equity
        ]),
        "MID_EXPANSION": np.array([
            [0.0003, -0.0001, -0.0001, 0.0000, -0.0002],
            [-0.0001, 0.0001, 0.0000, 0.0000, 0.0000],
            [-0.0001, 0.0000, 0.0002, 0.0000, -0.0002],
            [0.0000, 0.0000, 0.0000, 0.0010, 0.0001],
            [-0.0002, 0.0000, -0.0002, 0.0001, 0.0016],
        ]),
        "LATE_EXPANSION": np.array([
            [0.0006, 0.0002, 0.0003, -0.0001, -0.0001],
            [0.0002, 0.0004, 0.0001, -0.0001, 0.0000],
            [0.0003, 0.0001, 0.0008, -0.0002, -0.0006],
            [-0.0001, -0.0001, -0.0002, 0.0020, 0.0003],
            [-0.0001, 0.0000, -0.0006, 0.0003, 0.0030],
        ]),
        "EARLY_CONTRACTION": np.array([
            [0.0008, 0.0001, 0.0006, 0.0002, 0.0002],
            [0.0001, 0.0003, 0.0001, 0.0000, 0.0001],
            [0.0006, 0.0001, 0.0020, 0.0003, 0.0010],
            [0.0002, 0.0000, 0.0003, 0.0025, -0.0005],
            [0.0002, 0.0001, 0.0010, -0.0005, 0.0040],
        ]),
        "DEEP_CONTRACTION": np.array([
            [0.0010, -0.0002, 0.0008, 0.0005, 0.0008],
            [-0.0002, 0.0002, -0.0001, 0.0001, 0.0000],
            [0.0008, -0.0001, 0.0050, 0.0008, 0.0025],
            [0.0005, 0.0001, 0.0008, 0.0035, -0.0010],
            [0.0008, 0.0000, 0.0025, -0.0010, 0.0080],
        ]),
    }

    # Factor names (for indexing)
    FACTORS = ["real_rates", "inflation", "credit_spread", "usd", "equity"]

    def __init__(self, random_seed: Optional[int] = None):
        """
        Initialize risk service.

        Args:
            random_seed: Random seed for reproducibility (default: None)
        """
        self.scenarios = ALL_SCENARIOS
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

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

    def get_regime_covariance(self, regime: str) -> np.ndarray:
        """
        Get regime-specific covariance matrix.

        Args:
            regime: Macro regime (e.g., "MID_EXPANSION")

        Returns:
            Covariance matrix (5x5 numpy array)
        """
        if regime not in self.REGIME_COVARIANCES:
            logger.warning(f"Unknown regime {regime}, using MID_EXPANSION default")
            regime = "MID_EXPANSION"

        return self.REGIME_COVARIANCES[regime]

    async def get_portfolio_factor_betas(
        self,
        portfolio_id: str,
        pack_id: str,
    ) -> np.ndarray:
        """
        Get portfolio-level factor betas.

        Args:
            portfolio_id: Portfolio UUID
            pack_id: Pricing pack UUID

        Returns:
            Factor beta vector [real_rates, inflation, credit, usd, equity]
        """
        # Get position-level betas
        positions = await self.get_portfolio_holdings(portfolio_id)

        if not positions:
            return np.zeros(5)

        # Compute portfolio NAV
        total_nav = sum(Decimal(str(p["market_value"])) for p in positions)

        # Weight-average betas across positions
        portfolio_betas = np.zeros(5)
        for pos in positions:
            weight = float(Decimal(str(pos["market_value"])) / total_nav)
            pos_betas = np.array([
                pos.get("beta_real_rates", 0.0),
                pos.get("beta_inflation", 0.0),
                pos.get("beta_credit", 0.0),
                pos.get("beta_usd", 0.0),
                pos.get("beta_equity", 0.0),
            ])
            portfolio_betas += weight * pos_betas

        logger.debug(f"Portfolio betas: {portfolio_betas}")
        return portfolio_betas

    async def simulate_scenarios(
        self,
        betas: np.ndarray,
        covariance: np.ndarray,
        n_simulations: int = 10000,
    ) -> np.ndarray:
        """
        Run Monte Carlo simulation of portfolio returns.

        Args:
            betas: Portfolio factor betas (5-element vector)
            covariance: Factor covariance matrix (5x5)
            n_simulations: Number of simulations (default: 10,000)

        Returns:
            Array of simulated returns (length n_simulations)
        """
        logger.info(f"Running {n_simulations} Monte Carlo simulations")

        # Generate random factor returns from multivariate normal
        # Returns are monthly, so we use mean=0 (no drift)
        mean = np.zeros(5)
        factor_returns = np.random.multivariate_normal(
            mean,
            covariance,
            size=n_simulations,
        )

        # Compute portfolio returns: r_p = beta' * r_f
        portfolio_returns = factor_returns @ betas

        logger.debug(
            f"Simulated returns: mean={portfolio_returns.mean():.4f}, "
            f"std={portfolio_returns.std():.4f}, "
            f"min={portfolio_returns.min():.4f}, "
            f"max={portfolio_returns.max():.4f}"
        )

        return portfolio_returns

    async def compute_dar(
        self,
        portfolio_id: str,
        regime: str,
        pack_id: str,
        confidence: float = 0.95,
        horizon_days: int = 30,
        n_simulations: int = 10000,
        as_of_date: Optional[date] = None,
    ) -> DaRResult:
        """
        Compute Drawdown at Risk (DaR) using regime-conditioned Monte Carlo.

        Args:
            portfolio_id: Portfolio UUID
            regime: Current macro regime
            pack_id: Pricing pack UUID
            confidence: Confidence level (default: 0.95 = 95%)
            horizon_days: Forecast horizon in days (default: 30)
            n_simulations: Number of Monte Carlo simulations (default: 10,000)
            as_of_date: Date for calculation (default: today)

        Returns:
            DaRResult with regime-conditioned risk metrics
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get portfolio factor betas
        betas = await self.get_portfolio_factor_betas(portfolio_id, pack_id)

        # Get regime-specific covariance
        covariance = self.get_regime_covariance(regime)

        # Run Monte Carlo simulation
        returns = await self.simulate_scenarios(betas, covariance, n_simulations)

        # Compute percentiles
        percentile_idx = int((1 - confidence) * n_simulations)
        sorted_returns = np.sort(returns)

        dar = float(sorted_returns[percentile_idx])  # 5th percentile for 95% confidence
        worst_drawdown = float(sorted_returns[0])  # Absolute worst
        median_drawdown = float(np.median(returns))  # 50th percentile
        best_case = float(sorted_returns[-1])  # Best case

        # Compute factor contributions to DaR
        # Approximate using beta * marginal covariance
        factor_contributions = {}
        for i, factor in enumerate(self.FACTORS):
            # Marginal contribution = beta_i * sqrt(variance_i)
            variance = covariance[i, i]
            contribution = betas[i] * np.sqrt(variance)
            factor_contributions[factor] = float(contribution)

        # Get current NAV
        positions = await self.get_portfolio_holdings(portfolio_id)
        nav = sum(Decimal(str(p["market_value"])) for p in positions)

        logger.info(
            f"DaR ({confidence*100:.0f}% confidence, {horizon_days}d, {regime}): {dar*100:.2f}% "
            f"(worst: {worst_drawdown*100:.2f}%, median: {median_drawdown*100:.2f}%)"
        )

        return DaRResult(
            portfolio_id=portfolio_id,
            regime=regime,
            confidence=confidence,
            dar=dar,
            horizon_days=horizon_days,
            simulations=n_simulations,
            worst_drawdown=worst_drawdown,
            median_drawdown=median_drawdown,
            best_case=best_case,
            factor_contributions=factor_contributions,
            as_of_date=as_of_date,
            nav=nav,
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
