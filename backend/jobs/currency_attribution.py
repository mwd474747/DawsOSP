"""
Currency Attribution Engine

Purpose: Decompose portfolio returns into local currency and FX components
Updated: 2025-10-22
Priority: P0 (Critical for Phase 3)

Mathematical Identity:
    r_base = (1 + r_local)(1 + r_fx) - 1

Decomposition:
    r_base = r_local + r_fx + (r_local × r_fx)

    Where:
    - r_local: Return in asset's local currency
    - r_fx: FX return (change in FX rate)
    - (r_local × r_fx): Interaction term (small, typically < 0.01%)
    - r_base: Return in portfolio's base currency

Validation:
    Must hold to ±0.1 basis point accuracy:
    |r_base_computed - r_base_actual| ≤ 0.000001 (0.1bp)

Usage:
    from backend.jobs.currency_attribution import CurrencyAttribution

    # Initialize
    attr = CurrencyAttribution(base_currency='CAD')

    # Compute attribution for single position
    result = attr.compute_position_attribution(
        position_return_local=0.0150,  # 1.50% in EUR
        fx_return=-0.0025,             # -0.25% EUR/CAD appreciation
    )
    # Returns: {
    #     'local_return': 0.0150,
    #     'fx_return': -0.0025,
    #     'interaction_return': -0.0000375,
    #     'total_return': 0.01246250,
    #     'error_bps': 0.0
    # }

    # Compute attribution for entire portfolio
    portfolio_attribution = attr.compute_portfolio_attribution(
        positions=positions,
        fx_rates=fx_rates,
        base_currency='CAD',
    )

Beancount Integration:
    Uses Beancount's "at_value" directive for FX rate locking:

    2025-10-21 * "Buy EUR position"
        Assets:Broker:EUR  1000.00 EUR {1.50 CAD}  @ 1.50 CAD
        Assets:Broker:CAD -1500.00 CAD
"""

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Validation threshold: ±0.1 basis point
VALIDATION_THRESHOLD_BP = Decimal("0.1")
VALIDATION_THRESHOLD = Decimal("0.000001")  # 0.1bp as decimal


@dataclass
class PositionAttribution:
    """Currency attribution for a single position."""

    position_id: str
    currency: str
    base_currency: str

    # Returns (all as decimals, e.g., 0.0150 = 1.50%)
    local_return: Decimal
    fx_return: Decimal
    interaction_return: Decimal
    total_return: Decimal

    # Validation
    base_return_actual: Optional[Decimal] = None
    error_bps: Optional[Decimal] = None

    # Position details
    position_value_local: Optional[Decimal] = None
    position_value_base: Optional[Decimal] = None
    weight: Optional[Decimal] = None  # Portfolio weight

    def validate(self) -> bool:
        """
        Validate currency attribution identity.

        Returns:
            True if identity holds to ±0.1bp

        Raises:
            ValueError if validation fails
        """
        if self.base_return_actual is None:
            logger.warning(
                f"Cannot validate {self.position_id}: base_return_actual not set"
            )
            return False

        # Compute error
        computed = self.total_return
        actual = self.base_return_actual
        error = abs(computed - actual)
        error_bps = error * Decimal("10000")  # Convert to basis points

        # Store error
        self.error_bps = error_bps

        # Check threshold
        if error > VALIDATION_THRESHOLD:
            raise ValueError(
                f"Currency attribution identity violated for {self.position_id}: "
                f"computed={computed:.10f}, actual={actual:.10f}, "
                f"error={error_bps:.4f}bp (threshold=0.1bp)"
            )

        logger.debug(
            f"Currency attribution validated for {self.position_id}: "
            f"error={error_bps:.4f}bp"
        )
        return True


@dataclass
class PortfolioAttribution:
    """Currency attribution for entire portfolio."""

    portfolio_id: str
    asof_date: date
    base_currency: str

    # Aggregated returns
    local_return: Decimal
    fx_return: Decimal
    interaction_return: Decimal
    total_return: Decimal

    # Validation
    base_return_actual: Optional[Decimal] = None
    error_bps: Optional[Decimal] = None

    # Position-level attribution
    positions: List[PositionAttribution] = None

    # Attribution by currency
    attribution_by_currency: Dict[str, Dict[str, Decimal]] = None

    def validate(self) -> bool:
        """Validate portfolio-level attribution identity."""
        if self.base_return_actual is None:
            logger.warning("Cannot validate: base_return_actual not set")
            return False

        # Compute error
        computed = self.total_return
        actual = self.base_return_actual
        error = abs(computed - actual)
        error_bps = error * Decimal("10000")

        # Store error
        self.error_bps = error_bps

        # Check threshold
        if error > VALIDATION_THRESHOLD:
            raise ValueError(
                f"Portfolio currency attribution identity violated: "
                f"computed={computed:.10f}, actual={actual:.10f}, "
                f"error={error_bps:.4f}bp (threshold=0.1bp)"
            )

        logger.info(
            f"Portfolio currency attribution validated: error={error_bps:.4f}bp"
        )
        return True


class CurrencyAttribution:
    """
    Currency attribution engine.

    Decomposes portfolio returns into local currency and FX components.
    """

    def __init__(self, base_currency: str = "CAD"):
        """
        Initialize currency attribution engine.

        Args:
            base_currency: Portfolio's base currency (default: CAD)
        """
        self.base_currency = base_currency
        logger.info(f"CurrencyAttribution initialized (base_currency={base_currency})")

    def compute_position_attribution(
        self,
        position_id: str,
        currency: str,
        local_return: float,
        fx_return: float,
        base_return_actual: Optional[float] = None,
        position_value_local: Optional[float] = None,
        position_value_base: Optional[float] = None,
        weight: Optional[float] = None,
    ) -> PositionAttribution:
        """
        Compute currency attribution for a single position.

        Args:
            position_id: Position identifier
            currency: Position's local currency
            local_return: Return in local currency (e.g., 0.0150 = 1.50%)
            fx_return: FX return (e.g., -0.0025 = -0.25%)
            base_return_actual: Actual return in base currency (for validation)
            position_value_local: Position value in local currency
            position_value_base: Position value in base currency
            weight: Portfolio weight

        Returns:
            PositionAttribution with decomposed returns

        Example:
            >>> attr = CurrencyAttribution('CAD')
            >>> result = attr.compute_position_attribution(
            ...     position_id='AAPL',
            ...     currency='USD',
            ...     local_return=0.0150,
            ...     fx_return=-0.0025,
            ...     base_return_actual=0.012463,
            ... )
            >>> result.local_return
            Decimal('0.0150')
            >>> result.fx_return
            Decimal('-0.0025')
            >>> result.total_return
            Decimal('0.01246250')
            >>> result.error_bps < 0.1
            True
        """
        # Convert to Decimal for precision
        r_local = Decimal(str(local_return))
        r_fx = Decimal(str(fx_return))

        # Compute interaction term: r_local × r_fx
        r_interaction = r_local * r_fx

        # Compute total return: r_base = (1 + r_local)(1 + r_fx) - 1
        r_total = (Decimal("1") + r_local) * (Decimal("1") + r_fx) - Decimal("1")

        # Verification: r_total should equal r_local + r_fx + r_interaction
        r_total_check = r_local + r_fx + r_interaction
        assert abs(r_total - r_total_check) < Decimal(
            "1e-15"
        ), "Attribution identity failed"

        # Create attribution object
        attribution = PositionAttribution(
            position_id=position_id,
            currency=currency,
            base_currency=self.base_currency,
            local_return=r_local,
            fx_return=r_fx,
            interaction_return=r_interaction,
            total_return=r_total,
            base_return_actual=(
                Decimal(str(base_return_actual)) if base_return_actual else None
            ),
            position_value_local=(
                Decimal(str(position_value_local)) if position_value_local else None
            ),
            position_value_base=(
                Decimal(str(position_value_base)) if position_value_base else None
            ),
            weight=Decimal(str(weight)) if weight else None,
        )

        # Validate if actual return provided
        if base_return_actual is not None:
            attribution.validate()

        return attribution

    def compute_portfolio_attribution(
        self,
        portfolio_id: str,
        asof_date: date,
        position_attributions: List[PositionAttribution],
        base_return_actual: Optional[float] = None,
    ) -> PortfolioAttribution:
        """
        Compute currency attribution for entire portfolio.

        Aggregates position-level attributions using portfolio weights.

        Args:
            portfolio_id: Portfolio identifier
            asof_date: As-of date
            position_attributions: List of position attributions with weights
            base_return_actual: Actual portfolio return in base currency

        Returns:
            PortfolioAttribution with aggregated returns

        Formula:
            r_portfolio = Σ(w_i × r_i)

            Where:
            - w_i: Weight of position i
            - r_i: Return of position i

        Decomposition:
            r_local_portfolio = Σ(w_i × r_local_i)
            r_fx_portfolio = Σ(w_i × r_fx_i)
            r_interaction_portfolio = Σ(w_i × r_interaction_i)
        """
        # Validate all positions have weights
        for pos in position_attributions:
            if pos.weight is None:
                raise ValueError(
                    f"Position {pos.position_id} missing weight. "
                    "All positions must have weights for portfolio attribution."
                )

        # Aggregate weighted returns
        total_local = Decimal("0")
        total_fx = Decimal("0")
        total_interaction = Decimal("0")
        total_return = Decimal("0")

        for pos in position_attributions:
            total_local += pos.weight * pos.local_return
            total_fx += pos.weight * pos.fx_return
            total_interaction += pos.weight * pos.interaction_return
            total_return += pos.weight * pos.total_return

        # Group by currency for attribution breakdown
        attribution_by_currency: Dict[str, Dict[str, Decimal]] = {}

        for pos in position_attributions:
            if pos.currency not in attribution_by_currency:
                attribution_by_currency[pos.currency] = {
                    "local_return": Decimal("0"),
                    "fx_return": Decimal("0"),
                    "interaction_return": Decimal("0"),
                    "total_return": Decimal("0"),
                    "weight": Decimal("0"),
                }

            curr_attr = attribution_by_currency[pos.currency]
            curr_attr["local_return"] += pos.weight * pos.local_return
            curr_attr["fx_return"] += pos.weight * pos.fx_return
            curr_attr["interaction_return"] += pos.weight * pos.interaction_return
            curr_attr["total_return"] += pos.weight * pos.total_return
            curr_attr["weight"] += pos.weight

        # Create portfolio attribution
        portfolio_attribution = PortfolioAttribution(
            portfolio_id=portfolio_id,
            asof_date=asof_date,
            base_currency=self.base_currency,
            local_return=total_local,
            fx_return=total_fx,
            interaction_return=total_interaction,
            total_return=total_return,
            base_return_actual=(
                Decimal(str(base_return_actual)) if base_return_actual else None
            ),
            positions=position_attributions,
            attribution_by_currency=attribution_by_currency,
        )

        # Validate if actual return provided
        if base_return_actual is not None:
            portfolio_attribution.validate()

        return portfolio_attribution

    def compute_fx_return(
        self,
        fx_rate_start: float,
        fx_rate_end: float,
    ) -> Decimal:
        """
        Compute FX return from rate changes.

        Args:
            fx_rate_start: Starting FX rate (e.g., 1.50 EUR/CAD)
            fx_rate_end: Ending FX rate (e.g., 1.48 EUR/CAD)

        Returns:
            FX return as Decimal

        Formula:
            r_fx = (FX_end / FX_start) - 1

        Example:
            >>> attr = CurrencyAttribution('CAD')
            >>> # EUR/CAD appreciates from 1.50 to 1.48 (EUR stronger)
            >>> attr.compute_fx_return(1.50, 1.48)
            Decimal('-0.01333333...')  # -1.33% (negative = appreciation)
        """
        rate_start = Decimal(str(fx_rate_start))
        rate_end = Decimal(str(fx_rate_end))

        if rate_start == Decimal("0"):
            raise ValueError("FX rate start cannot be zero")

        fx_return = (rate_end / rate_start) - Decimal("1")

        return fx_return

    def compute_from_beancount(
        self,
        position_id: str,
        currency: str,
        position_value_start_local: float,
        position_value_end_local: float,
        fx_rate_start: float,
        fx_rate_end: float,
        flows_local: float = 0.0,
    ) -> PositionAttribution:
        """
        Compute attribution from Beancount data.

        Args:
            position_id: Position identifier
            currency: Position's local currency
            position_value_start_local: Starting value in local currency
            position_value_end_local: Ending value in local currency
            fx_rate_start: Starting FX rate
            fx_rate_end: Ending FX rate
            flows_local: Cash flows in local currency (default: 0)

        Returns:
            PositionAttribution

        Formula:
            r_local = (V_end - V_start - Flows) / V_start
            r_fx = (FX_end / FX_start) - 1
            r_base = (1 + r_local)(1 + r_fx) - 1
        """
        # Compute local return (time-weighted)
        v_start = Decimal(str(position_value_start_local))
        v_end = Decimal(str(position_value_end_local))
        flows = Decimal(str(flows_local))

        if v_start == Decimal("0"):
            raise ValueError("Starting position value cannot be zero")

        r_local = (v_end - v_start - flows) / v_start

        # Compute FX return
        r_fx = self.compute_fx_return(fx_rate_start, fx_rate_end)

        # Compute base return (actual)
        v_start_base = v_start * Decimal(str(fx_rate_start))
        v_end_base = v_end * Decimal(str(fx_rate_end))
        flows_base = flows * Decimal(str(fx_rate_end))  # Flow at end rate

        r_base_actual = (v_end_base - v_start_base - flows_base) / v_start_base

        # Compute attribution
        return self.compute_position_attribution(
            position_id=position_id,
            currency=currency,
            local_return=float(r_local),
            fx_return=float(r_fx),
            base_return_actual=float(r_base_actual),
            position_value_local=float(v_end),
            position_value_base=float(v_end_base),
        )


# ============================================================================
# Convenience Functions
# ============================================================================


def validate_currency_attribution_identity(
    local_return: float,
    fx_return: float,
    base_return: float,
) -> bool:
    """
    Validate currency attribution identity holds.

    Args:
        local_return: Return in local currency
        fx_return: FX return
        base_return: Actual return in base currency

    Returns:
        True if identity holds to ±0.1bp

    Raises:
        ValueError if validation fails
    """
    r_local = Decimal(str(local_return))
    r_fx = Decimal(str(fx_return))
    r_base = Decimal(str(base_return))

    # Compute expected base return
    r_base_expected = (Decimal("1") + r_local) * (Decimal("1") + r_fx) - Decimal("1")

    # Compute error
    error = abs(r_base_expected - r_base)
    error_bps = error * Decimal("10000")

    if error > VALIDATION_THRESHOLD:
        raise ValueError(
            f"Currency attribution identity violated: "
            f"expected={r_base_expected:.10f}, actual={r_base:.10f}, "
            f"error={error_bps:.4f}bp (threshold=0.1bp)"
        )

    logger.debug(f"Currency attribution identity validated: error={error_bps:.4f}bp")
    return True


def compute_interaction_term(local_return: float, fx_return: float) -> Decimal:
    """
    Compute interaction term: r_local × r_fx

    Args:
        local_return: Return in local currency
        fx_return: FX return

    Returns:
        Interaction term as Decimal
    """
    r_local = Decimal(str(local_return))
    r_fx = Decimal(str(fx_return))
    return r_local * r_fx
