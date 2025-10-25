"""
Scenario Stress Testing Service

Purpose: Apply macro shocks to portfolio and suggest hedges
Updated: 2025-10-23
Priority: P0 (Critical for risk management)

Features:
    - Apply scenario shocks to portfolio positions
    - Compute delta P&L from factor exposures
    - Rank winners and losers by impact
    - Suggest hedge ideas based on scenario type
    - Pre-defined scenario library (rates, USD, CPI, etc.)

Shock Types (PRODUCT_SPEC.md §7):
    - rates_up: +100bp rate shock
    - rates_down: -100bp rate shock
    - usd_up: +5% USD appreciation
    - usd_down: -5% USD depreciation
    - cpi_surprise: +1% inflation shock

Architecture:
    Portfolio → Factor Betas → Scenario Shock → Delta P&L → Hedge Suggestions

Usage:
    from backend.app.services.scenarios import get_scenario_service

    service = get_scenario_service()
    result = await service.apply_scenario(
        portfolio_id="...",
        shock_type="rates_up",
        pack_id="...",
    )
    hedges = await service.suggest_hedges(result.losers, "rates_up")
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import json

from backend.app.db.connection import execute_query, execute_statement, execute_query_one

logger = logging.getLogger("DawsOS.ScenarioService")


# ============================================================================
# Enums and Data Models
# ============================================================================


class ShockType(str, Enum):
    """Scenario shock types."""

    RATES_UP = "rates_up"
    RATES_DOWN = "rates_down"
    USD_UP = "usd_up"
    USD_DOWN = "usd_down"
    CPI_SURPRISE = "cpi_surprise"
    CREDIT_SPREAD_WIDENING = "credit_spread_widening"
    CREDIT_SPREAD_TIGHTENING = "credit_spread_tightening"
    EQUITY_SELLOFF = "equity_selloff"
    EQUITY_RALLY = "equity_rally"


@dataclass
class Shock:
    """Scenario shock definition."""

    shock_type: ShockType
    name: str
    description: str

    # Factor shocks (in decimal, e.g., 0.01 = 1% or 100bp)
    real_rates_bps: float = 0.0  # Basis points (100 = 1%)
    inflation_bps: float = 0.0  # Basis points
    credit_spread_bps: float = 0.0  # Basis points
    usd_pct: float = 0.0  # Percent (0.05 = 5%)
    equity_pct: float = 0.0  # Percent

    # Metadata
    probability: float = 0.0  # 0-1
    severity: str = "moderate"  # low, moderate, high, extreme


@dataclass
class PositionShockResult:
    """Shock result for a single position."""

    symbol: str
    quantity: float
    pre_shock_value: Decimal
    post_shock_value: Decimal
    delta_pl: Decimal  # P&L change
    delta_pl_pct: float  # Percent change

    # Attribution
    factor_contributions: Dict[str, Decimal] = field(default_factory=dict)


@dataclass
class ScenarioResult:
    """Scenario stress test result."""

    portfolio_id: str
    shock_type: ShockType
    shock_name: str
    as_of_date: date

    # Portfolio-level
    pre_shock_nav: Decimal
    post_shock_nav: Decimal
    total_delta_pl: Decimal
    total_delta_pl_pct: float

    # Position-level
    positions: List[PositionShockResult]
    winners: List[PositionShockResult]  # Top 10 gainers
    losers: List[PositionShockResult]  # Top 10 losers

    # Attribution
    factor_contributions: Dict[str, Decimal]


@dataclass
class HedgeRecommendation:
    """Hedge recommendation."""

    hedge_type: str  # e.g., "TLT puts", "USD/CAD forward", "VIX calls"
    rationale: str  # Why this hedge works
    notional: Optional[Decimal] = None  # Suggested notional
    instruments: List[str] = field(default_factory=list)  # Specific tickers


# ============================================================================
# Scenario Library
# ============================================================================

SCENARIO_LIBRARY = {
    ShockType.RATES_UP: Shock(
        shock_type=ShockType.RATES_UP,
        name="Rates Up +100bp",
        description="10Y Treasury yield rises 100bp (1%), bond prices fall, equity multiple compression",
        real_rates_bps=100.0,
        usd_pct=0.02,  # USD strengthens 2%
        equity_pct=-0.05,  # Equity down 5% (P/E compression)
        probability=0.10,
        severity="moderate",
    ),
    ShockType.RATES_DOWN: Shock(
        shock_type=ShockType.RATES_DOWN,
        name="Rates Down -100bp",
        description="10Y Treasury yield falls 100bp, flight to quality, equity rally",
        real_rates_bps=-100.0,
        usd_pct=-0.02,  # USD weakens 2%
        equity_pct=0.08,  # Equity up 8% (P/E expansion)
        probability=0.08,
        severity="moderate",
    ),
    ShockType.USD_UP: Shock(
        shock_type=ShockType.USD_UP,
        name="USD Up +5%",
        description="USD appreciates 5%, negative for USD-denominated foreign assets",
        usd_pct=0.05,
        equity_pct=-0.02,  # Slight equity drag (multinational earnings)
        probability=0.12,
        severity="moderate",
    ),
    ShockType.USD_DOWN: Shock(
        shock_type=ShockType.USD_DOWN,
        name="USD Down -5%",
        description="USD depreciates 5%, positive for USD-denominated foreign assets",
        usd_pct=-0.05,
        equity_pct=0.02,  # Slight equity boost
        probability=0.12,
        severity="moderate",
    ),
    ShockType.CPI_SURPRISE: Shock(
        shock_type=ShockType.CPI_SURPRISE,
        name="CPI Surprise +1%",
        description="Inflation surprise +1%, rates rise, equity sells off",
        inflation_bps=100.0,
        real_rates_bps=50.0,  # Fed hikes
        equity_pct=-0.08,  # Risk-off
        credit_spread_bps=25.0,  # Spreads widen
        probability=0.05,
        severity="high",
    ),
    ShockType.CREDIT_SPREAD_WIDENING: Shock(
        shock_type=ShockType.CREDIT_SPREAD_WIDENING,
        name="Credit Spreads +200bp",
        description="Credit spreads widen 200bp, risk-off, recession fears",
        credit_spread_bps=200.0,
        equity_pct=-0.15,  # Equity selloff
        real_rates_bps=-50.0,  # Flight to quality
        probability=0.03,
        severity="high",
    ),
    ShockType.CREDIT_SPREAD_TIGHTENING: Shock(
        shock_type=ShockType.CREDIT_SPREAD_TIGHTENING,
        name="Credit Spreads -50bp",
        description="Credit spreads tighten 50bp, risk-on, growth optimism",
        credit_spread_bps=-50.0,
        equity_pct=0.05,  # Equity rally
        probability=0.08,
        severity="low",
    ),
    ShockType.EQUITY_SELLOFF: Shock(
        shock_type=ShockType.EQUITY_SELLOFF,
        name="Equity Selloff -20%",
        description="Broad equity selloff -20%, risk-off, VIX spike",
        equity_pct=-0.20,
        real_rates_bps=-75.0,  # Flight to quality
        credit_spread_bps=100.0,  # Spreads widen
        usd_pct=0.03,  # USD safe haven
        probability=0.02,
        severity="extreme",
    ),
    ShockType.EQUITY_RALLY: Shock(
        shock_type=ShockType.EQUITY_RALLY,
        name="Equity Rally +15%",
        description="Broad equity rally +15%, risk-on, growth optimism",
        equity_pct=0.15,
        real_rates_bps=25.0,  # Rates rise on growth
        credit_spread_bps=-25.0,  # Spreads tighten
        probability=0.05,
        severity="low",
    ),
}


# ============================================================================
# Scenario Service
# ============================================================================


class ScenarioService:
    """
    Scenario stress testing service.

    Applies macro shocks to portfolio and suggests hedges.
    """

    def __init__(self):
        self.scenarios = SCENARIO_LIBRARY

    async def get_position_betas(
        self,
        portfolio_id: str,
        pack_id: str,
    ) -> List[Dict]:
        """
        Get factor betas for all positions in portfolio.

        Args:
            portfolio_id: Portfolio UUID
            pack_id: Pricing pack UUID

        Returns:
            List of position records with factor betas
        """
        # TODO: Query position_factor_betas table (to be created)
        # For now, use placeholder betas
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
        positions = await execute_query(query, portfolio_id)

        # Add placeholder betas (TODO: compute from factor model)
        for pos in positions:
            # Placeholder: assume equity positions have typical betas
            pos["beta_real_rates"] = -5.0  # Duration = 5 years
            pos["beta_inflation"] = -3.0  # Negative inflation beta
            pos["beta_credit"] = 0.5  # Slight credit exposure
            pos["beta_usd"] = -0.5 if pos["currency"] != "USD" else 0.0
            pos["beta_equity"] = 1.0  # Market beta

        return positions

    async def apply_scenario(
        self,
        portfolio_id: str,
        shock_type: ShockType,
        pack_id: str,
        as_of_date: Optional[date] = None,
    ) -> ScenarioResult:
        """
        Apply scenario shock to portfolio.

        Args:
            portfolio_id: Portfolio UUID
            shock_type: Type of shock to apply
            pack_id: Pricing pack UUID
            as_of_date: Date for scenario (default: today)

        Returns:
            ScenarioResult with delta P&L and attribution
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get shock definition
        shock = self.scenarios[shock_type]

        # Get positions with factor betas
        positions = await self.get_position_betas(portfolio_id, pack_id)

        if not positions:
            logger.warning(f"No positions found for portfolio {portfolio_id}")
            return ScenarioResult(
                portfolio_id=portfolio_id,
                shock_type=shock_type,
                shock_name=shock.name,
                as_of_date=as_of_date,
                pre_shock_nav=Decimal("0"),
                post_shock_nav=Decimal("0"),
                total_delta_pl=Decimal("0"),
                total_delta_pl_pct=0.0,
                positions=[],
                winners=[],
                losers=[],
                factor_contributions={},
            )

        # Compute pre-shock NAV
        pre_shock_nav = sum(Decimal(str(p["market_value"])) for p in positions)

        # Apply shocks to each position
        position_results = []
        total_delta_pl = Decimal("0")

        for pos in positions:
            result = self._compute_position_delta(pos, shock)
            position_results.append(result)
            total_delta_pl += result.delta_pl

        # Compute post-shock NAV
        post_shock_nav = pre_shock_nav + total_delta_pl
        total_delta_pl_pct = float(total_delta_pl / pre_shock_nav) if pre_shock_nav > 0 else 0.0

        # Rank winners and losers
        sorted_positions = sorted(position_results, key=lambda p: p.delta_pl, reverse=True)
        winners = sorted_positions[:10]  # Top 10 gainers
        losers = sorted_positions[-10:]  # Top 10 losers (most negative)
        losers.reverse()  # Most negative first

        # Compute factor contributions (aggregate across portfolio)
        factor_contributions = {
            "real_rates": Decimal("0"),
            "inflation": Decimal("0"),
            "credit": Decimal("0"),
            "usd": Decimal("0"),
            "equity": Decimal("0"),
        }

        for pos_result in position_results:
            for factor, contrib in pos_result.factor_contributions.items():
                factor_contributions[factor] += contrib

        logger.info(
            f"Scenario {shock.name}: {total_delta_pl_pct*100:.2f}% impact "
            f"(NAV: {pre_shock_nav:.2f} → {post_shock_nav:.2f})"
        )

        return ScenarioResult(
            portfolio_id=portfolio_id,
            shock_type=shock_type,
            shock_name=shock.name,
            as_of_date=as_of_date,
            pre_shock_nav=pre_shock_nav,
            post_shock_nav=post_shock_nav,
            total_delta_pl=total_delta_pl,
            total_delta_pl_pct=total_delta_pl_pct,
            positions=position_results,
            winners=winners,
            losers=losers,
            factor_contributions=factor_contributions,
        )

    def _compute_position_delta(
        self,
        position: Dict,
        shock: Shock,
    ) -> PositionShockResult:
        """
        Compute delta P&L for a single position.

        Args:
            position: Position record with betas
            shock: Shock definition

        Returns:
            PositionShockResult
        """
        pre_shock_value = Decimal(str(position["market_value"]))

        # Compute delta from each factor
        # Delta = Beta * Shock * Market_Value
        # E.g., if beta_rates = -5, shock = +100bp = 0.01, MV = 100k
        # Delta = -5 * 0.01 * 100k = -5k (5% loss)

        delta_real_rates = Decimal("0")
        if shock.real_rates_bps != 0:
            # Convert bp to decimal (100bp = 0.01)
            shock_decimal = Decimal(str(shock.real_rates_bps / 10000))
            beta = Decimal(str(position["beta_real_rates"]))
            delta_real_rates = beta * shock_decimal * pre_shock_value

        delta_inflation = Decimal("0")
        if shock.inflation_bps != 0:
            shock_decimal = Decimal(str(shock.inflation_bps / 10000))
            beta = Decimal(str(position["beta_inflation"]))
            delta_inflation = beta * shock_decimal * pre_shock_value

        delta_credit = Decimal("0")
        if shock.credit_spread_bps != 0:
            shock_decimal = Decimal(str(shock.credit_spread_bps / 10000))
            beta = Decimal(str(position["beta_credit"]))
            delta_credit = beta * shock_decimal * pre_shock_value

        delta_usd = Decimal("0")
        if shock.usd_pct != 0:
            shock_decimal = Decimal(str(shock.usd_pct))
            beta = Decimal(str(position["beta_usd"]))
            delta_usd = beta * shock_decimal * pre_shock_value

        delta_equity = Decimal("0")
        if shock.equity_pct != 0:
            shock_decimal = Decimal(str(shock.equity_pct))
            beta = Decimal(str(position["beta_equity"]))
            delta_equity = beta * shock_decimal * pre_shock_value

        # Total delta
        total_delta = delta_real_rates + delta_inflation + delta_credit + delta_usd + delta_equity
        post_shock_value = pre_shock_value + total_delta
        delta_pct = float(total_delta / pre_shock_value) if pre_shock_value > 0 else 0.0

        return PositionShockResult(
            symbol=position["symbol"],
            quantity=position["quantity"],
            pre_shock_value=pre_shock_value,
            post_shock_value=post_shock_value,
            delta_pl=total_delta,
            delta_pl_pct=delta_pct,
            factor_contributions={
                "real_rates": delta_real_rates,
                "inflation": delta_inflation,
                "credit": delta_credit,
                "usd": delta_usd,
                "equity": delta_equity,
            },
        )

    async def suggest_hedges(
        self,
        losers: List[PositionShockResult],
        shock_type: ShockType,
    ) -> List[HedgeRecommendation]:
        """
        Suggest hedge ideas based on scenario losers.

        Args:
            losers: List of positions with negative delta P&L
            shock_type: Type of shock that caused losses

        Returns:
            List of HedgeRecommendation
        """
        hedges = []

        # Compute total loss
        total_loss = sum(pos.delta_pl for pos in losers)

        # Hedge suggestions by shock type
        if shock_type == ShockType.RATES_UP:
            hedges.append(
                HedgeRecommendation(
                    hedge_type="Treasury Puts",
                    rationale="TLT puts protect against rising rates (falling bond prices)",
                    notional=abs(total_loss) * Decimal("0.5"),  # Hedge 50% of loss
                    instruments=["TLT", "IEF", "TBT"],
                )
            )
            hedges.append(
                HedgeRecommendation(
                    hedge_type="Steepener Trade",
                    rationale="Short 2Y, long 10Y to benefit from curve steepening",
                    instruments=["SHY", "TLT"],
                )
            )

        elif shock_type == ShockType.RATES_DOWN:
            hedges.append(
                HedgeRecommendation(
                    hedge_type="Treasury Calls",
                    rationale="TLT calls benefit from falling rates (rising bond prices)",
                    notional=abs(total_loss) * Decimal("0.5"),
                    instruments=["TLT", "IEF"],
                )
            )

        elif shock_type == ShockType.USD_UP:
            hedges.append(
                HedgeRecommendation(
                    hedge_type="USD/CAD Forward",
                    rationale="Buy USD/CAD forwards to hedge USD strength",
                    notional=abs(total_loss),
                    instruments=["FXC", "USD/CAD futures"],
                )
            )
            hedges.append(
                HedgeRecommendation(
                    hedge_type="DXY Calls",
                    rationale="USD index calls benefit from USD appreciation",
                    instruments=["UUP", "DXY futures"],
                )
            )

        elif shock_type == ShockType.USD_DOWN:
            hedges.append(
                HedgeRecommendation(
                    hedge_type="USD/CAD Put",
                    rationale="Sell USD/CAD forwards to hedge USD weakness",
                    instruments=["FXC puts", "USD/CAD futures"],
                )
            )

        elif shock_type == ShockType.CPI_SURPRISE:
            hedges.append(
                HedgeRecommendation(
                    hedge_type="TIPS",
                    rationale="Treasury Inflation-Protected Securities hedge inflation risk",
                    notional=abs(total_loss) * Decimal("0.75"),
                    instruments=["TIP", "SCHP"],
                )
            )
            hedges.append(
                HedgeRecommendation(
                    hedge_type="Commodity Basket",
                    rationale="Commodities typically benefit from inflation",
                    instruments=["DBC", "PDBC", "GLD"],
                )
            )

        elif shock_type == ShockType.CREDIT_SPREAD_WIDENING:
            hedges.append(
                HedgeRecommendation(
                    hedge_type="HYG Puts",
                    rationale="High-yield bond puts protect against credit spread widening",
                    notional=abs(total_loss) * Decimal("0.6"),
                    instruments=["HYG", "JNK"],
                )
            )
            hedges.append(
                HedgeRecommendation(
                    hedge_type="CDX Spreads",
                    rationale="Buy protection on CDX investment grade index",
                    instruments=["CDX.IG", "LQD puts"],
                )
            )

        elif shock_type == ShockType.EQUITY_SELLOFF:
            hedges.append(
                HedgeRecommendation(
                    hedge_type="SPY Puts",
                    rationale="S&P 500 puts protect against equity drawdown",
                    notional=abs(total_loss) * Decimal("0.8"),
                    instruments=["SPY", "IVV", "VOO"],
                )
            )
            hedges.append(
                HedgeRecommendation(
                    hedge_type="VIX Calls",
                    rationale="VIX calls profit from volatility spike during selloffs",
                    instruments=["VXX", "UVXY"],
                )
            )

        logger.info(f"Generated {len(hedges)} hedge recommendations for {shock_type.value}")
        return hedges

    async def rank_winners_losers(
        self,
        deltas: List[PositionShockResult],
    ) -> Tuple[List[PositionShockResult], List[PositionShockResult]]:
        """
        Rank positions by delta P&L.

        Args:
            deltas: List of PositionShockResult

        Returns:
            Tuple of (winners, losers)
        """
        sorted_deltas = sorted(deltas, key=lambda p: p.delta_pl, reverse=True)
        winners = sorted_deltas[:10]  # Top 10 gainers
        losers = sorted_deltas[-10:]  # Top 10 losers
        losers.reverse()  # Most negative first

        return winners, losers


# ============================================================================
# Singleton
# ============================================================================


_scenario_service: Optional[ScenarioService] = None


def get_scenario_service() -> ScenarioService:
    """
    Get scenario service singleton.

    Returns:
        ScenarioService singleton
    """
    global _scenario_service
    if _scenario_service is None:
        _scenario_service = ScenarioService()
    return _scenario_service
