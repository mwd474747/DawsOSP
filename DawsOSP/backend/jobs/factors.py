"""
Factor Exposure Computation

Purpose: Compute portfolio factor exposures using Dalio framework
Updated: 2025-10-22
Priority: P0 (S1-W1 GATE - Truth Spine Foundation)

Factors (Dalio Framework):
    - Real Rate (DFII10)       - Real interest rate expectations
    - Inflation (T10YIE)       - Inflation expectations
    - Credit (BAMLC0A0CM)      - Credit spread / risk premium
    - USD (DTWEXBGS)           - USD strength
    - Risk-Free (DGS10)        - Nominal risk-free rate

Computed Metrics:
    - Factor loadings (regression coefficients)
    - Factor contribution to return (% attribution)
    - Rolling correlations (30/60/90 day)
    - Factor momentum (trend strength)

Critical Requirements:
    - Factor data from FRED provider
    - Portfolio returns from pricing packs
    - Multi-currency portfolios use base currency returns
    - Factor decomposition must match ±0.1bp

Sacred Accuracy:
    - Factor attribution must sum to total return ±0.1bp
    - Residual (alpha) = total_return - sum(factor_contributions)
"""

import asyncio
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
import numpy as np
from scipy import stats
from scipy.optimize import minimize

logger = logging.getLogger("DawsOS.Factors")


# Dalio Factor Definitions
DALIO_FACTORS = {
    "real_rate": {
        "name": "Real Rate",
        "fred_series": "DFII10",
        "description": "10-Year TIPS Constant Maturity Rate",
        "interpretation": "Real interest rate expectations",
    },
    "inflation": {
        "name": "Inflation",
        "fred_series": "T10YIE",
        "description": "10-Year Breakeven Inflation Rate",
        "interpretation": "Inflation expectations",
    },
    "credit": {
        "name": "Credit Spread",
        "fred_series": "BAMLC0A0CM",
        "description": "ICE BofA US Corporate Index Effective Yield",
        "interpretation": "Credit risk premium",
    },
    "usd": {
        "name": "USD",
        "fred_series": "DTWEXBGS",
        "description": "Trade Weighted U.S. Dollar Index: Broad, Goods and Services",
        "interpretation": "USD strength",
    },
    "risk_free": {
        "name": "Risk-Free Rate",
        "fred_series": "DGS10",
        "description": "10-Year Treasury Constant Maturity Rate",
        "interpretation": "Nominal risk-free rate",
    },
}


@dataclass
class FactorExposure:
    """Factor exposure for a single portfolio."""
    portfolio_id: str
    asof_date: date
    pricing_pack_id: str

    # Factor loadings (regression coefficients)
    loading_real_rate: Optional[Decimal] = None
    loading_inflation: Optional[Decimal] = None
    loading_credit: Optional[Decimal] = None
    loading_usd: Optional[Decimal] = None
    loading_risk_free: Optional[Decimal] = None

    # Factor contributions (% of return)
    contrib_real_rate: Optional[Decimal] = None
    contrib_inflation: Optional[Decimal] = None
    contrib_credit: Optional[Decimal] = None
    contrib_usd: Optional[Decimal] = None
    contrib_risk_free: Optional[Decimal] = None

    # Residual (alpha)
    alpha: Optional[Decimal] = None

    # Model fit quality
    r_squared: Optional[Decimal] = None
    adj_r_squared: Optional[Decimal] = None

    # Rolling correlations (30 day)
    corr_real_rate_30d: Optional[Decimal] = None
    corr_inflation_30d: Optional[Decimal] = None
    corr_credit_30d: Optional[Decimal] = None
    corr_usd_30d: Optional[Decimal] = None
    corr_risk_free_30d: Optional[Decimal] = None

    # Factor momentum
    momentum_real_rate: Optional[Decimal] = None
    momentum_inflation: Optional[Decimal] = None
    momentum_credit: Optional[Decimal] = None
    momentum_usd: Optional[Decimal] = None


class FactorComputer:
    """
    Compute portfolio factor exposures using Dalio framework.

    Dalio Factors:
    - Real rate (DFII10)
    - Inflation (T10YIE)
    - Credit spread (BAMLC0A0CM)
    - USD (DTWEXBGS)
    - Risk-free rate (DGS10)

    Factor Model:
    portfolio_return = alpha + β1*real_rate + β2*inflation + β3*credit + β4*usd + β5*risk_free + ε

    Where:
    - alpha = residual return (skill/idiosyncratic)
    - βi = factor loadings (sensitivities)
    - εi = error term
    """

    def __init__(self):
        """Initialize factor computer."""
        pass

    async def compute_all_factors(
        self,
        pack_id: str,
        asof_date: date,
    ) -> List[FactorExposure]:
        """
        Compute factor exposures for all portfolios.

        Args:
            pack_id: Pricing pack ID
            asof_date: As-of date

        Returns:
            List of FactorExposure for each portfolio
        """
        logger.info(f"Computing factor exposures for pack {pack_id}")

        # Get all portfolios
        portfolios = await self._get_active_portfolios()

        # Get factor data (FRED)
        factor_data = await self._get_factor_data(asof_date)

        exposures = []
        for portfolio_id in portfolios:
            try:
                exposure = await self.compute_portfolio_factors(
                    portfolio_id=portfolio_id,
                    pack_id=pack_id,
                    asof_date=asof_date,
                    factor_data=factor_data,
                )
                exposures.append(exposure)
            except Exception as e:
                logger.exception(f"Failed to compute factors for portfolio {portfolio_id}: {e}")

        logger.info(f"Computed factor exposures for {len(exposures)} portfolios")
        return exposures

    async def compute_portfolio_factors(
        self,
        portfolio_id: str,
        pack_id: str,
        asof_date: date,
        factor_data: Dict[str, np.ndarray],
    ) -> FactorExposure:
        """
        Compute factor exposure for a single portfolio.

        Args:
            portfolio_id: Portfolio ID
            pack_id: Pricing pack ID
            asof_date: As-of date
            factor_data: Factor time series (from FRED)

        Returns:
            FactorExposure object
        """
        logger.debug(f"Computing factor exposure for portfolio {portfolio_id}")

        # Get portfolio returns
        portfolio_returns = await self._get_portfolio_returns(portfolio_id, asof_date)

        # Align portfolio returns with factor data
        aligned_returns, aligned_factors = self._align_data(portfolio_returns, factor_data)

        # Compute factor loadings (regression)
        loadings, alpha, r_squared, adj_r_squared = self._compute_factor_loadings(
            aligned_returns, aligned_factors
        )

        # Compute factor contributions
        contributions = self._compute_factor_contributions(loadings, aligned_factors)

        # Compute rolling correlations
        correlations = self._compute_rolling_correlations(aligned_returns, aligned_factors)

        # Compute factor momentum
        momentum = self._compute_factor_momentum(aligned_factors)

        # Create exposure object
        exposure = FactorExposure(
            portfolio_id=portfolio_id,
            asof_date=asof_date,
            pricing_pack_id=pack_id,
            # Loadings
            loading_real_rate=Decimal(str(loadings.get("real_rate", 0.0))),
            loading_inflation=Decimal(str(loadings.get("inflation", 0.0))),
            loading_credit=Decimal(str(loadings.get("credit", 0.0))),
            loading_usd=Decimal(str(loadings.get("usd", 0.0))),
            loading_risk_free=Decimal(str(loadings.get("risk_free", 0.0))),
            # Contributions
            contrib_real_rate=Decimal(str(contributions.get("real_rate", 0.0))),
            contrib_inflation=Decimal(str(contributions.get("inflation", 0.0))),
            contrib_credit=Decimal(str(contributions.get("credit", 0.0))),
            contrib_usd=Decimal(str(contributions.get("usd", 0.0))),
            contrib_risk_free=Decimal(str(contributions.get("risk_free", 0.0))),
            # Alpha
            alpha=Decimal(str(alpha)),
            # Model fit
            r_squared=Decimal(str(r_squared)),
            adj_r_squared=Decimal(str(adj_r_squared)),
            # Correlations
            corr_real_rate_30d=Decimal(str(correlations.get("real_rate", 0.0))),
            corr_inflation_30d=Decimal(str(correlations.get("inflation", 0.0))),
            corr_credit_30d=Decimal(str(correlations.get("credit", 0.0))),
            corr_usd_30d=Decimal(str(correlations.get("usd", 0.0))),
            corr_risk_free_30d=Decimal(str(correlations.get("risk_free", 0.0))),
            # Momentum
            momentum_real_rate=Decimal(str(momentum.get("real_rate", 0.0))),
            momentum_inflation=Decimal(str(momentum.get("inflation", 0.0))),
            momentum_credit=Decimal(str(momentum.get("credit", 0.0))),
            momentum_usd=Decimal(str(momentum.get("usd", 0.0))),
        )

        # Store exposure in DB
        await self._store_exposure(exposure)

        return exposure

    async def _get_active_portfolios(self) -> List[str]:
        """Get list of active portfolio IDs."""
        # TODO: Query DB for active portfolios
        logger.debug("Getting active portfolios")
        return []

    async def _get_factor_data(
        self,
        asof_date: date,
        lookback_days: int = 1260,  # ~5 years
    ) -> Dict[str, np.ndarray]:
        """
        Get factor time series from FRED.

        Returns:
            Dict mapping factor name to time series array
        """
        # TODO: Query FRED data for each factor
        # Use FRED provider to fetch:
        # - DFII10 (real rate)
        # - T10YIE (inflation)
        # - BAMLC0A0CM (credit)
        # - DTWEXBGS (USD)
        # - DGS10 (risk-free)

        logger.debug(f"Getting factor data for {asof_date}")

        factor_data = {}
        for factor_id, factor_info in DALIO_FACTORS.items():
            # Placeholder: return empty array
            factor_data[factor_id] = np.array([])

        return factor_data

    async def _get_portfolio_returns(
        self,
        portfolio_id: str,
        asof_date: date,
        lookback_days: int = 1260,
    ) -> np.ndarray:
        """
        Get portfolio daily returns.

        Returns:
            Array of daily returns (most recent last)
        """
        # TODO: Query portfolio_valuations table for daily returns
        logger.debug(f"Getting returns for portfolio {portfolio_id}")
        return np.array([])

    def _align_data(
        self,
        portfolio_returns: np.ndarray,
        factor_data: Dict[str, np.ndarray],
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Align portfolio returns with factor data.

        Ensures all arrays have same length and dates match.
        """
        # TODO: Implement data alignment
        # 1. Find common date range
        # 2. Interpolate missing values (forward fill)
        # 3. Ensure all arrays have same length

        return portfolio_returns, factor_data

    def _compute_factor_loadings(
        self,
        returns: np.ndarray,
        factor_data: Dict[str, np.ndarray],
    ) -> Tuple[Dict[str, float], float, float, float]:
        """
        Compute factor loadings using regression.

        Model: portfolio_return = alpha + β1*f1 + β2*f2 + ... + βN*fN + ε

        Returns:
            (loadings, alpha, r_squared, adj_r_squared)
        """
        if len(returns) == 0:
            return {}, 0.0, 0.0, 0.0

        # TODO: Implement multiple regression
        # 1. Prepare design matrix X (factor values)
        # 2. Prepare response vector y (portfolio returns)
        # 3. Solve: β = (X'X)^-1 X'y
        # 4. Compute R² and adjusted R²

        # Placeholder
        loadings = {factor: 0.0 for factor in DALIO_FACTORS.keys()}
        alpha = 0.0
        r_squared = 0.0
        adj_r_squared = 0.0

        return loadings, alpha, r_squared, adj_r_squared

    def _compute_factor_contributions(
        self,
        loadings: Dict[str, float],
        factor_data: Dict[str, np.ndarray],
    ) -> Dict[str, float]:
        """
        Compute factor contributions to return.

        Contribution = loading * factor_return

        Sacred Accuracy:
        - Sum of contributions must equal total return ±0.1bp
        - Residual (alpha) = total_return - sum(contributions)
        """
        # TODO: Implement contribution calculation
        # 1. For each factor: contrib = loading * factor_return
        # 2. Validate: sum(contribs) + alpha ≈ total_return ±0.1bp

        contributions = {factor: 0.0 for factor in DALIO_FACTORS.keys()}
        return contributions

    def _compute_rolling_correlations(
        self,
        returns: np.ndarray,
        factor_data: Dict[str, np.ndarray],
        window: int = 30,
    ) -> Dict[str, float]:
        """
        Compute rolling correlations (30 day window).

        Correlation = Cov(returns, factor) / (StdDev(returns) * StdDev(factor))
        """
        if len(returns) < window:
            return {factor: 0.0 for factor in DALIO_FACTORS.keys()}

        # TODO: Implement rolling correlation
        # 1. For each factor, compute correlation over last 30 days
        # 2. Use pandas rolling or numpy sliding window

        correlations = {factor: 0.0 for factor in DALIO_FACTORS.keys()}
        return correlations

    def _compute_factor_momentum(
        self,
        factor_data: Dict[str, np.ndarray],
        window: int = 90,
    ) -> Dict[str, float]:
        """
        Compute factor momentum (trend strength).

        Momentum = (current_value - MA_90d) / StdDev_90d

        Interpretation:
        - > +1: Strong uptrend
        - < -1: Strong downtrend
        - Near 0: No trend
        """
        # TODO: Implement momentum calculation
        # 1. Compute 90-day moving average
        # 2. Compute 90-day standard deviation
        # 3. Momentum = (current - MA) / StdDev

        momentum = {}
        for factor_id in DALIO_FACTORS.keys():
            if factor_id != "risk_free":  # Skip risk-free (no momentum)
                momentum[factor_id] = 0.0

        return momentum

    async def _store_exposure(self, exposure: FactorExposure):
        """Store factor exposure in DB."""
        # TODO: Insert into portfolio_factor_exposures table
        logger.debug(f"Storing factor exposure for portfolio {exposure.portfolio_id}")


# ===========================
# REGIME DETECTION
# ===========================

@dataclass
class MacroRegime:
    """Macro regime classification."""
    regime_id: str
    regime_name: str
    asof_date: date
    probability: Decimal

    # Regime characteristics
    growth: str  # "expansion", "contraction"
    inflation: str  # "rising", "falling"
    policy: str  # "tightening", "easing", "neutral"

    # Factor signals
    real_rate_signal: str  # "bullish", "bearish", "neutral"
    inflation_signal: str
    credit_signal: str
    usd_signal: str


class RegimeDetector:
    """
    Detect macro regime using Dalio framework.

    Regimes (Dalio):
    1. Goldilocks (growth up, inflation down) - risk-on
    2. Reflation (growth up, inflation up) - commodities, real assets
    3. Stagflation (growth down, inflation up) - defensive, gold
    4. Deflation (growth down, inflation down) - bonds, quality

    Signals:
    - Real rate rising → growth expectations up
    - Inflation rising → inflation expectations up
    - Credit spread widening → risk aversion
    - USD strengthening → flight to quality
    """

    def __init__(self):
        """Initialize regime detector."""
        pass

    async def detect_regime(
        self,
        asof_date: date,
        factor_data: Dict[str, np.ndarray],
    ) -> MacroRegime:
        """
        Detect current macro regime.

        Args:
            asof_date: As-of date
            factor_data: Factor time series

        Returns:
            MacroRegime classification
        """
        # TODO: Implement regime detection
        # 1. Compute factor changes (30/60/90 day)
        # 2. Classify growth (real_rate + credit)
        # 3. Classify inflation (inflation expectations)
        # 4. Classify policy (risk_free rate changes)
        # 5. Map to regime (Goldilocks/Reflation/Stagflation/Deflation)

        logger.debug(f"Detecting regime for {asof_date}")

        return MacroRegime(
            regime_id="goldilocks",
            regime_name="Goldilocks",
            asof_date=asof_date,
            probability=Decimal("0.75"),
            growth="expansion",
            inflation="falling",
            policy="neutral",
            real_rate_signal="bullish",
            inflation_signal="neutral",
            credit_signal="bullish",
            usd_signal="neutral",
        )


# ===========================
# STANDALONE EXECUTION
# ===========================

async def main():
    """Run factor computation immediately (for testing)."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python factors.py <pack_id> [asof_date]")
        sys.exit(1)

    pack_id = sys.argv[1]
    asof_date = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today() - timedelta(days=1)

    # Initialize factor computer
    computer = FactorComputer()

    # Compute factors for all portfolios
    exposures = await computer.compute_all_factors(
        pack_id=pack_id,
        asof_date=asof_date,
    )

    # Print summary
    print(f"Computed factor exposures for {len(exposures)} portfolios")
    for exposure in exposures:
        print(f"  Portfolio: {exposure.portfolio_id}")
        print(f"    Real Rate Loading: {exposure.loading_real_rate}")
        print(f"    Inflation Loading: {exposure.loading_inflation}")
        print(f"    Alpha: {exposure.alpha}")
        print(f"    R²: {exposure.r_squared}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(main())
