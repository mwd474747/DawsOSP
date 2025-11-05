"""
DawsOS Macro Hound Agent

Purpose: Macro analysis, regime detection, cycles, scenarios, DaR
Updated: 2025-11-02

Capabilities:
    - macro.detect_regime: Detect current macro regime (5 regimes)
    - macro.compute_cycles: Compute STDC/LTDC/Empire/Civil cycle phases
    - macro.get_indicators: Get current macro indicators with z-score
    - macro.run_scenario: Run stress test scenario
    - macro.compute_dar: Compute Drawdown at Risk (DaR)
    - scenarios.*: Deleveraging scenarios (austerity, default, money printing)

Architecture:
    Pattern → Agent Runtime → MacroHound → MacroService/CyclesService → Database

Usage:
    agent = MacroHound("macro_hound", services)
    runtime.register_agent(agent)
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

# Import capability contract decorator (optional - graceful degradation)
try:
    from app.core.capability_contract import capability
    CAPABILITY_CONTRACT_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Capability contract module not available - contracts disabled")
    # Fallback: no-op decorator
    def capability(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    CAPABILITY_CONTRACT_AVAILABLE = False

from app.agents.base_agent import BaseAgent
from app.core.types import RequestCtx
from app.core.provenance import ProvenanceWrapper, DataProvenance
from app.services.macro import MacroService
from app.services.cycles import CyclesService
from app.services.macro_aware_scenarios import MacroAwareScenarioService
from app.services.alerts import AlertService
from app.services.playbooks import PlaybookGenerator

logger = logging.getLogger("DawsOS.MacroHound")


class MacroHound(BaseAgent):
    """
    Macro Analysis Agent.

    Provides capabilities for:
        - Macro regime detection (5 regimes: Early/Mid/Late Expansion, Early/Deep Contraction)
        - Cycle phase detection (STDC/LTDC/Empire cycles)
        - Macro indicators with z-score normalization
        - Scenario analysis (stress testing)
        - DaR (Drawdown at Risk) computation

    Integrates with:
        - MacroService (regime detection)
        - CyclesService (STDC/LTDC/Empire phases)
        - RiskService (DaR scenarios)
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "macro.detect_regime",
            "macro.compute_cycles",
            "macro.get_indicators",
            "macro.run_scenario",
            "macro.compute_dar",
            "macro.get_regime_history",
            "macro.detect_trend_shifts",
            "cycles.compute_short_term",
            "cycles.compute_long_term",
            "cycles.compute_empire",
            "cycles.compute_civil",  # NEW: Civil/Internal Order Cycle
            "cycles.aggregate_overview",
            "scenarios.deleveraging_austerity",
            "scenarios.deleveraging_default",
            "scenarios.deleveraging_money_printing",
            "scenarios.macro_aware_apply",  # NEW: Macro-aware scenario application
            "scenarios.macro_aware_rank",  # NEW: Regime-weighted scenario ranking
            "macro_hound.suggest_alert_presets",  # NEW: AlertsAgent consolidation
            "macro_hound.create_alert_if_threshold",  # NEW: AlertsAgent consolidation
        ]

    async def macro_detect_regime(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Detect current macro regime.

        Classifies the macro environment into one of 5 regimes based on
        key indicators (yield curve, unemployment, GDP growth, inflation).

        Args:
            ctx: Request context
            state: Execution state
            asof_date: Override as-of date (optional, uses ctx.asof_date if not provided)

        Returns:
            Dict with regime classification and indicators

        Example:
            {
                "regime_name": "MID_EXPANSION",
                "confidence": 0.78,
                "date": "2025-10-22",
                "indicators": {
                    "T10Y2Y": 0.52,      # 10Y-2Y yield spread
                    "UNRATE": 3.7,       # Unemployment rate
                    "GDP": 2.8,          # GDP growth rate
                    "CPIAUCSL": 2.4      # CPI inflation
                },
                "zscores": {
                    "T10Y2Y": 0.8,       # Z-score normalized
                    "UNRATE": -0.5,
                    "GDP": 0.3,
                    "CPIAUCSL": -0.2
                },
                "regime_scores": {
                    "EARLY_EXPANSION": 0.15,
                    "MID_EXPANSION": 0.78,
                    "LATE_EXPANSION": 0.45,
                    "EARLY_CONTRACTION": 0.12,
                    "DEEP_CONTRACTION": 0.05
                },
                "__metadata__": {
                    "source": "macro_service:regime_detector",
                    "asof": "2025-10-22",
                    "ttl": 3600
                }
            }
        """
        asof = asof_date or ctx.asof_date

        logger.info(f"macro.detect_regime: asof_date={asof}")

        # Get macro service (singleton pattern for now, TODO: DI)
        from app.services.macro import get_macro_service
        macro_service = get_macro_service()

        provenance = DataProvenance.UNKNOWN
        warnings = []

        try:
            # Detect current regime
            classification = await macro_service.detect_current_regime()

            result = {
                "regime_name": classification.regime.value,
                "confidence": float(classification.confidence),
                "date": str(classification.date),
                "indicators": {k: float(v) for k, v in classification.indicators.items()},
                "zscores": {k: float(v) for k, v in classification.zscores.items()},
                "regime_scores": {k.value: float(v) for k, v in classification.regime_scores.items()},
            }

            # Data comes from computed indicators
            provenance = DataProvenance.COMPUTED

        except Exception as e:
            logger.error(f"Error detecting regime: {e}", exc_info=True)
            result = {
                "regime_name": "UNKNOWN",
                "confidence": 0.0,
                "date": str(asof) if asof else None,
                "error": f"Regime detection error: {str(e)}",
            }
            provenance = DataProvenance.STUB
            warnings.append("Using fallback regime detection due to error")

        # Attach metadata
        metadata = self._create_metadata(
            source="macro_service:regime_detector",
            asof=asof,
            ttl=self.CACHE_TTL_HOUR,  # Cache for 1 hour
        )
        result = self._attach_metadata(result, metadata)

        # Add provenance information
        result["_provenance"] = {
            "type": provenance.value,
            "source": "macro_service:regime_detector" if provenance == DataProvenance.COMPUTED else "stub:error_fallback",
            "warnings": warnings,
            "confidence": result.get("confidence", 0.0)
        }

        return result

    async def macro_compute_cycles(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Compute macro cycle phases (STDC, LTDC, Empire).

        Analyzes long-term macro cycles based on Dalio framework:
        - STDC (Short-Term Debt Cycle): 5-10 year business cycles
        - LTDC (Long-Term Debt Cycle): 50-75 year debt super cycles
        - Empire Cycle: Rise and decline of global powers (200-300 years)

        Args:
            ctx: Request context
            state: Execution state
            asof_date: Override as-of date (optional)

        Returns:
            Dict with cycle phases for STDC, LTDC, Empire

        Example:
            {
                "stdc": {
                    "cycle_type": "STDC",
                    "phase": "Early Recovery",
                    "phase_number": 1,
                    "composite_score": 0.24,
                    "description": "Post-recession recovery phase"
                },
                "ltdc": {
                    "cycle_type": "LTDC",
                    "phase": "Expansion",
                    "phase_number": 3,
                    "composite_score": 0.65,
                    "description": "Long-term debt expansion phase"
                },
                "empire": {
                    "cycle_type": "EMPIRE",
                    "phase": "Peak",
                    "phase_number": 2,
                    "composite_score": 0.85,
                    "description": "Empire at peak power"
                },
                "date": "2025-10-22",
                "__metadata__": {...}
            }
        """
        asof = asof_date or ctx.asof_date

        logger.info(f"macro.compute_cycles: asof_date={asof}")

        # Get cycles service (singleton pattern for now, TODO: DI)
        from app.services.cycles import get_cycles_service
        cycles_service = get_cycles_service()

        try:
            # Detect all cycle phases
            stdc_phase = await cycles_service.detect_stdc_phase(as_of_date=asof)
            ltdc_phase = await cycles_service.detect_ltdc_phase(as_of_date=asof)
            empire_phase = await cycles_service.detect_empire_phase(as_of_date=asof)

            result = {
                "stdc": {
                    "cycle_type": stdc_phase.cycle_type.value,
                    "phase": stdc_phase.phase,
                    "phase_number": stdc_phase.phase_number,
                    "composite_score": float(stdc_phase.composite_score),
                    "description": stdc_phase.description if hasattr(stdc_phase, "description") else None,
                },
                "ltdc": {
                    "cycle_type": ltdc_phase.cycle_type.value,
                    "phase": ltdc_phase.phase,
                    "phase_number": ltdc_phase.phase_number,
                    "composite_score": float(ltdc_phase.composite_score),
                    "description": ltdc_phase.description if hasattr(ltdc_phase, "description") else None,
                },
                "empire": {
                    "cycle_type": empire_phase.cycle_type.value,
                    "phase": empire_phase.phase,
                    "phase_number": empire_phase.phase_number,
                    "composite_score": float(empire_phase.composite_score),
                    "description": empire_phase.description if hasattr(empire_phase, "description") else None,
                },
                "date": str(asof) if asof else None,
            }

        except Exception as e:
            logger.error(f"Error computing cycles: {e}", exc_info=True)
            result = {
                "stdc": None,
                "ltdc": None,
                "empire": None,
                "date": str(asof) if asof else None,
                "error": f"Cycle computation error: {str(e)}",
            }

        # Attach metadata
        metadata = self._create_metadata(
            source="cycles_service:phase_detector",
            asof=asof,
            ttl=self.CACHE_TTL_HOUR,  # Cache for 1 hour
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def macro_get_indicators(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get current macro indicators with z-scores.

        Retrieves key macro indicators and their z-score normalized values
        for regime detection and analysis.

        Args:
            ctx: Request context
            state: Execution state
            asof_date: Override as-of date (optional)

        Returns:
            Dict with indicator values and z-scores

        Example:
            {
                "indicators": {
                    "T10Y2Y": 0.52,
                    "UNRATE": 3.7,
                    "GDP": 2.8,
                    "CPIAUCSL": 2.4,
                    "M2": 4.5,
                    "FEDFUNDS": 5.25
                },
                "zscores": {
                    "T10Y2Y": 0.8,
                    "UNRATE": -0.5,
                    "GDP": 0.3,
                    "CPIAUCSL": -0.2,
                    "M2": 0.1,
                    "FEDFUNDS": 1.2
                },
                "date": "2025-10-22",
                "__metadata__": {...}
            }
        """
        asof = asof_date or ctx.asof_date

        logger.info(f"macro.get_indicators: asof_date={asof}")

        # Get macro service
        from app.services.macro import get_macro_service
        macro_service = get_macro_service()

        try:
            # Get indicators with z-scores
            indicators = await macro_service.get_indicators(asof_date=asof)
            zscores = await macro_service.compute_zscores(indicators, window_days=252)

            result = {
                "indicators": {k: float(v) for k, v in indicators.items()},
                "zscores": {k: float(v) for k, v in zscores.items()},
                "date": str(asof) if asof else None,
            }

        except Exception as e:
            logger.error(f"Error getting indicators: {e}", exc_info=True)
            result = {
                "indicators": {},
                "zscores": {},
                "date": str(asof) if asof else None,
                "error": f"Indicator fetch error: {str(e)}",
            }

        # Attach metadata
        metadata = self._create_metadata(
            source="macro_service:indicators",
            asof=asof,
            ttl=self.CACHE_TTL_HOUR,
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def macro_run_scenario(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        scenario_params: Optional[Dict[str, Any]] = None,
        pack_id: Optional[str] = None,
        custom_shocks: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run stress test scenario.

        Applies a stress test scenario to the portfolio and computes the
        expected change in portfolio value using factor-based shock analysis.

        Args:
            ctx: Request context
            state: Execution state
            portfolio_id: Portfolio ID (optional, uses ctx.portfolio_id if not provided)
            scenario_id: Scenario ID (e.g., "rates_up", "equity_selloff", "2008_financial_crisis")
            scenario_params: Custom scenario parameters (shocks to apply)
            pack_id: Pricing pack ID (optional, uses ctx.pricing_pack_id if not provided)
            custom_shocks: Custom shocks to apply (rates_bps, usd_vs_cad_pct, cpi_surprise_pct)

        Returns:
            Dict with scenario results

        Example:
            {
                "scenario_id": "rates_up",
                "scenario_name": "Rates Up +100bp",
                "portfolio_id": "11111111-1111-1111-1111-111111111111",
                "pre_shock_nav": 140000.0,
                "post_shock_nav": 133000.0,
                "total_delta_pl": -7000.0,
                "total_delta_pl_pct": -0.05,
                "factor_contributions": {
                    "real_rates": -8000.0,
                    "inflation": 0.0,
                    "credit": 0.0,
                    "usd": 500.0,
                    "equity": 500.0
                },
                "winners": [
                    {
                        "symbol": "TLT",
                        "delta_pl": 500.0,
                        "delta_pl_pct": 0.05
                    }
                ],
                "losers": [
                    {
                        "symbol": "AAPL",
                        "delta_pl": -2500.0,
                        "delta_pl_pct": -0.05
                    }
                ],
                "positions": [...],
                "__metadata__": {...}
            }
        """
        portfolio_id_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "macro.run_scenario")
        pack_id_str = self._resolve_pricing_pack_id(pack_id, ctx)

        logger.info(
            f"macro.run_scenario: portfolio_id={portfolio_id_uuid}, "
            f"scenario_id={scenario_id}, pack_id={pack_id_str}"
        )

        # Get scenario service
        from app.services.scenarios import get_scenario_service, ShockType

        scenario_service = get_scenario_service()

        try:
            # Determine shock type
            if scenario_id:
                # Map scenario_id to ShockType enum
                shock_type_map = {
                    "rates_up": ShockType.RATES_UP,
                    "rates_down": ShockType.RATES_DOWN,
                    "usd_up": ShockType.USD_UP,
                    "usd_down": ShockType.USD_DOWN,
                    "cpi_surprise": ShockType.CPI_SURPRISE,
                    "credit_spread_widening": ShockType.CREDIT_SPREAD_WIDENING,
                    "credit_spread_tightening": ShockType.CREDIT_SPREAD_TIGHTENING,
                    "equity_selloff": ShockType.EQUITY_SELLOFF,
                    "equity_rally": ShockType.EQUITY_RALLY,
                    # Historical analogs (use equity_selloff as base)
                    "2008_financial_crisis": ShockType.EQUITY_SELLOFF,
                    "covid_2020": ShockType.EQUITY_SELLOFF,
                    "dot_com_bubble": ShockType.EQUITY_SELLOFF,
                }
                shock_type = shock_type_map.get(scenario_id, ShockType.RATES_UP)
            else:
                # Default to rates_up if no scenario specified
                shock_type = ShockType.RATES_UP

            # Run scenario stress test
            scenario_result = await scenario_service.apply_scenario(
                portfolio_id=str(portfolio_id_uuid),
                shock_type=shock_type,
                pack_id=pack_id_str,
                as_of_date=ctx.asof_date,
            )

            # Convert ScenarioResult to dict for agent response
            result = {
                "scenario_id": scenario_id or shock_type.value,
                "scenario_name": scenario_result.shock_name,
                "portfolio_id": str(portfolio_id_uuid),
                "pre_shock_nav": float(scenario_result.pre_shock_nav),
                "post_shock_nav": float(scenario_result.post_shock_nav),
                "total_delta_pl": float(scenario_result.total_delta_pl),
                "total_delta_pl_pct": scenario_result.total_delta_pl_pct,
                "factor_contributions": {
                    k: float(v) for k, v in scenario_result.factor_contributions.items()
                },
                "winners": [
                    {
                        "symbol": pos.symbol,
                        "quantity": pos.quantity,
                        "pre_shock_value": float(pos.pre_shock_value),
                        "post_shock_value": float(pos.post_shock_value),
                        "delta_pl": float(pos.delta_pl),
                        "delta_pl_pct": pos.delta_pl_pct,
                    }
                    for pos in scenario_result.winners
                ],
                "losers": [
                    {
                        "symbol": pos.symbol,
                        "quantity": pos.quantity,
                        "pre_shock_value": float(pos.pre_shock_value),
                        "post_shock_value": float(pos.post_shock_value),
                        "delta_pl": float(pos.delta_pl),
                        "delta_pl_pct": pos.delta_pl_pct,
                    }
                    for pos in scenario_result.losers
                ],
                "positions": [
                    {
                        "symbol": pos.symbol,
                        "quantity": pos.quantity,
                        "pre_shock_value": float(pos.pre_shock_value),
                        "post_shock_value": float(pos.post_shock_value),
                        "delta_pl": float(pos.delta_pl),
                        "delta_pl_pct": pos.delta_pl_pct,
                        "factor_contributions": {
                            k: float(v) for k, v in pos.factor_contributions.items()
                        },
                    }
                    for pos in scenario_result.positions
                ],
                "as_of_date": str(scenario_result.as_of_date),
            }

        except Exception as e:
            logger.error(f"Error running scenario {scenario_id}: {e}", exc_info=True)
            result = {
                "scenario_id": scenario_id or "unknown",
                "scenario_name": scenario_id.replace("_", " ").title() if scenario_id else "Unknown Scenario",
                "portfolio_id": str(portfolio_id_uuid),
                "pre_shock_nav": None,
                "post_shock_nav": None,
                "total_delta_pl": None,
                "total_delta_pl_pct": None,
                "factor_contributions": {},
                "winners": [],
                "losers": [],
                "positions": [],
                "error": f"Scenario execution error: {str(e)}",
                "_is_stub": True,
            }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"scenario_service:{pack_id_str}",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_NONE,  # Don't cache scenario results (they're point-in-time stress tests)
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def scenarios_deleveraging_money_printing(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        pack_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run money printing deleveraging scenario.

        Simulates central bank monetization: inflation rises, currency weakens,
        commodities rally, real rates negative.
        """
        from app.services.scenarios import ShockType

        portfolio_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "scenarios.deleveraging_money_printing")
        pack_id = self._resolve_pricing_pack_id(pack_id, ctx)

        # Use macro.run_scenario with money printing shock
        return await self.macro_run_scenario(
            ctx=ctx,
            state=state,
            portfolio_id=str(portfolio_uuid),
            scenario_id="dalio_money_printing_deleveraging",
            pack_id=pack_id,
        )

    async def scenarios_deleveraging_austerity(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        pack_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run austerity deleveraging scenario.

        Simulates fiscal cuts: deflation risk, growth weak, spreads widen.
        """
        portfolio_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "scenarios.deleveraging_austerity")
        pack_id = self._resolve_pricing_pack_id(pack_id, ctx)

        return await self.macro_run_scenario(
            ctx=ctx,
            state=state,
            portfolio_id=str(portfolio_uuid),
            scenario_id="dalio_austerity_deleveraging",
            pack_id=pack_id,
        )

    async def scenarios_deleveraging_default(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        pack_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run default/restructuring deleveraging scenario.

        Simulates debt defaults: severe deflation, credit crisis, massive spreads.
        """
        portfolio_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "scenarios.deleveraging_default")
        pack_id = self._resolve_pricing_pack_id(pack_id, ctx)

        return await self.macro_run_scenario(
            ctx=ctx,
            state=state,
            portfolio_id=str(portfolio_uuid),
            scenario_id="dalio_default_deleveraging",
            pack_id=pack_id,
        )

    @capability(
        name="macro.compute_dar",
        inputs={
            "portfolio_id": str,
            "pack_id": str,
            "confidence": float,
            "horizon_days": int,
            "cycle_adjusted": bool,
        },
        outputs={
            "dar_value": float,
            "dar_amount": float,
            "confidence": float,
            "portfolio_id": str,
            "regime": str,
            "horizon_days": int,
            "scenarios_run": int,
            "worst_scenario": str,
            "worst_scenario_drawdown": float,
            "_provenance": dict,  # Added when computation fails (stub)
        },
        fetches_positions=False,
        implementation_status="partial",  # Real implementation, but falls back to stub on errors
        description="Compute Drawdown at Risk (DaR) using scenario analysis. Falls back to stub data on errors.",
        dependencies=["scenarios.compute_dar", "macro.detect_regime"],
    )
    async def macro_compute_dar(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        pack_id: Optional[str] = None,
        cycle_adjusted: bool = False,
        confidence: float = 0.95,
        horizon_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Compute Drawdown at Risk (DaR).

        Computes the expected maximum drawdown at a given confidence level
        by running all macro scenarios and taking the specified percentile.

        DaR Methodology (Dalio Framework):
        - DaR = Percentile of scenario drawdowns (e.g., 95th percentile)
        - Runs 9 pre-defined scenarios (rates, USD, CPI, credit, equity)
        - Conditions on current macro regime
        - Persists to dar_history table for trend analysis

        Args:
            ctx: Request context
            state: Execution state
            portfolio_id: Portfolio ID (optional)
            confidence: Confidence level (default 0.95 = 95%)
            horizon_days: Forecast horizon (default 30 days)

        Returns:
            Dict with DaR computation

        Example:
            {
                "dar_value": -0.185,  # 18.5% drawdown at 95% confidence
                "dar_amount": -25900.00,  # Dollar drawdown
                "confidence": 0.95,
                "portfolio_id": "11111111-1111-1111-1111-111111111111",
                "regime": "LATE_EXPANSION",
                "horizon_days": 30,
                "scenarios_run": 9,
                "worst_scenario": "equity_selloff",
                "worst_scenario_name": "Equity Selloff -20%",
                "worst_scenario_drawdown": -0.35,
                "mean_drawdown": -0.12,
                "median_drawdown": -0.08,
                "max_drawdown": -0.35,
                "current_nav": 140000.00,
                "scenario_distribution": [
                    {"scenario": "equity_selloff", "scenario_name": "Equity Selloff -20%", "drawdown_pct": -0.35, "delta_pl": -49000.00},
                    {"scenario": "credit_spread_widening", "scenario_name": "Credit Spreads +200bp", "drawdown_pct": -0.18, "delta_pl": -25200.00},
                    ...
                ],
                "as_of_date": "2025-10-24",
                "__metadata__": {...}
            }
        """
        portfolio_id_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "macro.compute_dar")

        # Use provided pack_id or fall back to context pack_id
        pack_id_str = self._resolve_pricing_pack_id(pack_id, ctx)

        logger.info(
            f"macro.compute_dar: portfolio_id={portfolio_id_uuid}, "
            f"confidence={confidence}, horizon={horizon_days}d, "
            f"pack_id={pack_id_str}, cycle_adjusted={cycle_adjusted}"
        )

        # TODO: Implement cycle-adjusted DaR if cycle_adjusted=True
        if cycle_adjusted:
            logger.info("Cycle-adjusted DaR requested (not yet fully implemented)")

        # Get scenario service
        from app.services.scenarios import get_scenario_service
        scenario_service = get_scenario_service()

        # Get macro service to detect current regime
        from app.services.macro import get_macro_service
        macro_service = get_macro_service()

        try:
            # Detect current regime for conditioning
            try:
                regime_classification = await macro_service.detect_current_regime()
                regime = regime_classification.regime.value
            except Exception as e:
                logger.warning(f"Could not detect regime for DaR conditioning: {e}")
                regime = "MID_EXPANSION"  # Default fallback

            logger.info(f"Computing DaR conditioned on regime: {regime}")

            # Compute DaR using scenario service
            dar_result = await scenario_service.compute_dar(
                portfolio_id=str(portfolio_id_uuid),
                regime=regime,
                confidence=confidence,
                horizon_days=horizon_days,
                pack_id=pack_id_str,
                as_of_date=ctx.asof_date,
            )

            # Check for errors
            if "error" in dar_result:
                logger.error(f"DaR computation failed: {dar_result['error']}")
                result = {
                    "dar_value": None,
                    "dar_amount": None,
                    "confidence": confidence,
                    "portfolio_id": str(portfolio_id_uuid),
                    "regime": regime,
                    "horizon_days": horizon_days,
                    "scenarios_run": 0,
                    "worst_scenario": None,
                    "worst_scenario_drawdown": None,
                    "error": dar_result["error"],
                    "_is_stub": True,
                    # PHASE 1 FIX: Add provenance warning to prevent user trust issues
                    "_provenance": {
                        "type": "stub",
                        "warnings": [
                            "DaR computation failed - using fallback data",
                            "Values may not be accurate for investment decisions"
                        ],
                        "confidence": 0.0,
                        "implementation_status": "stub",
                        "recommendation": "Do not use for investment decisions",
                        "source": "error_fallback_stub_data"
                    }
                }
            else:
                # Success - return DaR result
                result = dar_result

        except Exception as e:
            logger.error(f"Error computing DaR: {e}", exc_info=True)
            result = {
                "dar_value": None,
                "dar_amount": None,
                "confidence": confidence,
                "portfolio_id": str(portfolio_id_uuid),
                "regime": None,
                "horizon_days": horizon_days,
                "scenarios_run": 0,
                "worst_scenario": None,
                "worst_scenario_drawdown": None,
                "error": f"DaR computation error: {str(e)}",
                "_is_stub": True,
                # PHASE 1 FIX: Add provenance warning to prevent user trust issues
                "_provenance": {
                    "type": "stub",
                    "warnings": [
                        "DaR computation error - using fallback data",
                        "Values may not be accurate for investment decisions"
                    ],
                    "confidence": 0.0,
                    "implementation_status": "stub",
                    "recommendation": "Do not use for investment decisions",
                    "source": "exception_fallback_stub_data"
                }
            }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"scenario_service:dar:{pack_id_str}",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_HOUR,  # Cache for 1 hour (DaR is computationally expensive)
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def macro_get_regime_history(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        lookback_days: int = 365,
        lookback_weeks: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get historical regime classifications.

        Capability: macro.get_regime_history
        """
        # If lookback_weeks is provided, convert to days
        if lookback_weeks is not None:
            lookback_days = lookback_weeks * 7
            logger.info(f"macro.get_regime_history: lookback={lookback_weeks} weeks ({lookback_days} days)")
        else:
            logger.info(f"macro.get_regime_history: lookback={lookback_days} days")

        macro_service = MacroService()
        history = await macro_service.get_regime_history(lookback_days)

        metadata = self._create_metadata(
            source=f"macro_service:regime_history",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_HOUR
        )

        return self._attach_metadata({"history": history}, metadata)

    async def macro_detect_trend_shifts(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        regime_history: Optional[Dict[str, Any]] = None,
        factor_history: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Detect recent regime transitions/trend shifts.

        Capability: macro.detect_trend_shifts
        
        If regime_history and factor_history are provided (from pattern steps),
        uses those. Otherwise, fetches from MacroService.
        """
        logger.info("macro.detect_trend_shifts")

        # Use provided data if available, otherwise fetch from service
        if regime_history and factor_history:
            # Use data from pattern steps (preferred)
            logger.debug("Using regime_history and factor_history from pattern steps")
            
            # Analyze for shifts using provided data
            shifts = []
            if regime_history:
                # Extract history from provided data structure
                history_data = regime_history.get("history", regime_history) if isinstance(regime_history, dict) else []
                
                prev_regime = None
                if isinstance(history_data, list):
                    for entry in history_data:
                        if isinstance(entry, dict) and "regime" in entry:
                            current_regime = entry["regime"]
                            if prev_regime and current_regime != prev_regime:
                                shifts.append({
                                    "date": entry.get("date", ""),
                                    "from_regime": prev_regime,
                                    "to_regime": current_regime,
                                    "confidence": entry.get("confidence", 0.0)
                                })
                            prev_regime = current_regime
        else:
            # Fetch from MacroService (fallback)
            logger.debug("Fetching regime history from MacroService")
            macro_service = MacroService()
            history = await macro_service.get_regime_history(90)  # Last 90 days

            # Find regime changes
            shifts = []
            prev_regime = None
            for entry in history:
                if prev_regime and entry["regime"] != prev_regime:
                    shifts.append({
                        "date": entry["date"],
                        "from_regime": prev_regime,
                        "to_regime": entry["regime"],
                        "confidence": entry.get("confidence", 0.0)
                    })
                prev_regime = entry["regime"]

        metadata = self._create_metadata(
            source=f"macro_service:trend_shifts",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_HOUR
        )

        return self._attach_metadata({"shifts": shifts}, metadata)

    async def cycles_compute_short_term(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Compute Short-Term Debt Cycle (STDC) phase.

        Capability: cycles.compute_short_term
        """
        asof = asof_date or ctx.asof_date
        logger.info(f"cycles.compute_short_term: asof={asof}")

        cycles_service = CyclesService()
        phase = await cycles_service.detect_stdc_phase(as_of_date=asof)

        result = {
            "cycle_type": "short_term_debt",
            "phase_label": phase.phase,
            "phase_number": phase.phase_number,
            "composite_score": float(phase.composite_score),
            "date": phase.date.isoformat(),
            "indicators": phase.indicators,
        }

        metadata = self._create_metadata(
            source=f"cycles_service:stdc:{ctx.pricing_pack_id}",
            asof=phase.date,
            ttl=self.CACHE_TTL_DAY
        )

        return self._attach_metadata(result, metadata)

    async def cycles_compute_long_term(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Compute Long-Term Debt Cycle (LTDC) phase.

        Capability: cycles.compute_long_term
        """
        asof = asof_date or ctx.asof_date
        logger.info(f"cycles.compute_long_term: asof={asof}")

        cycles_service = CyclesService()
        phase = await cycles_service.detect_ltdc_phase(as_of_date=asof)

        result = {
            "cycle_type": "long_term_debt",
            "phase_label": phase.phase,
            "phase_number": phase.phase_number,
            "composite_score": float(phase.composite_score),
            "date": phase.date.isoformat(),
            "indicators": phase.indicators,
        }

        metadata = self._create_metadata(
            source=f"cycles_service:ltdc:{ctx.pricing_pack_id}",
            asof=phase.date,
            ttl=self.CACHE_TTL_DAY
        )

        return self._attach_metadata(result, metadata)

    async def cycles_compute_empire(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Compute Empire Cycle phase.

        Capability: cycles.compute_empire
        """
        asof = asof_date or ctx.asof_date
        logger.info(f"cycles.compute_empire: asof={asof}")

        cycles_service = CyclesService()
        phase = await cycles_service.detect_empire_phase(as_of_date=asof)

        result = {
            "cycle_type": "empire",
            "phase_label": phase.phase,
            "phase_number": phase.phase_number,
            "composite_score": float(phase.composite_score),
            "date": phase.date.isoformat(),
            "indicators": phase.indicators,
        }

        metadata = self._create_metadata(
            source=f"cycles_service:empire:{ctx.pricing_pack_id}",
            asof=phase.date,
            ttl=self.CACHE_TTL_DAY
        )

        return self._attach_metadata(result, metadata)

    async def cycles_compute_civil(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Compute Civil/Internal Order Cycle phase.

        Analyzes social cohesion and internal order based on:
        - Wealth inequality (Gini coefficient, top 1% wealth share)
        - Social polarization (political polarization index)
        - Institutional trust (government/media trust scores)
        - Social mobility metrics

        Based on Dalio's framework for internal conflict cycles.

        Capability: cycles.compute_civil
        """
        asof = asof_date or ctx.asof_date
        logger.info(f"cycles.compute_civil: asof={asof}")

        try:
            # Use the real CyclesService to detect civil phase
            cycles_service = CyclesService()
            phase = await cycles_service.detect_civil_phase(as_of_date=asof)

            # Generate description based on phase
            descriptions = {
                "Harmony": "Strong social cohesion, low inequality, high trust",
                "Rising Tensions": "Rising inequality, declining trust in institutions",
                "Polarization": "Deep political divisions, social unrest emerging",
                "Crisis": "Institutional breakdown, high conflict risk",
                "Conflict/Revolution": "Active internal conflict, potential for revolution or civil war",
                "Reconstruction": "Rebuilding institutions and social trust after conflict"
            }

            description = descriptions.get(phase.phase, "Unknown phase state")

            # Determine risk factors based on indicators
            gini = phase.indicators.get("gini_coefficient", 0.418)
            polarization = phase.indicators.get("polarization_index", 0.78)
            trust = phase.indicators.get("institutional_trust", 0.38)

            # Build result
            result = {
                "cycle_type": "civil",
                "phase_label": phase.phase,
                "phase_number": phase.phase_number,
                "composite_score": float(phase.composite_score),
                "confidence": float(phase.composite_score),  # Use composite score as confidence
                "description": description,
                "date": phase.date.isoformat() if phase.date else None,
                "indicators": phase.indicators,
                "risk_factors": {
                    "wealth_inequality": "HIGH" if gini > 0.40 else "MEDIUM" if gini > 0.35 else "LOW",
                    "political_polarization": "HIGH" if polarization > 0.70 else "MEDIUM" if polarization > 0.50 else "LOW",
                    "trust_deficit": "HIGH" if trust < 0.40 else "MEDIUM" if trust < 0.60 else "LOW",
                },
            }

        except Exception as e:
            logger.error(f"Error computing civil cycle: {e}", exc_info=True)
            # Return fallback values on error
            result = {
                "cycle_type": "civil",
                "phase_label": "Crisis",
                "phase_number": 4,
                "composite_score": 0.42,
                "confidence": 0.50,
                "description": "Institutional breakdown, high conflict risk",
                "date": asof.isoformat() if asof else None,
                "indicators": {
                    "gini_coefficient": 0.418,
                    "institutional_trust": 0.38,
                    "polarization_index": 0.78,
                    "social_unrest_score": 0.30,
                    "fiscal_deficit_gdp": -6.20,
                },
                "risk_factors": {
                    "wealth_inequality": "HIGH",
                    "political_polarization": "HIGH",
                    "trust_deficit": "HIGH",
                },
                "error": f"Civil cycle computation error: {str(e)}",
            }

        metadata = self._create_metadata(
            source=f"cycles_service:civil:{ctx.pricing_pack_id}",
            asof=asof,
            ttl=self.CACHE_TTL_DAY  # Cache for 24 hours (civil cycle changes slowly)
        )

        return self._attach_metadata(result, metadata)

    async def cycles_aggregate_overview(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Compute all four cycles in one call.

        Capability: cycles.aggregate_overview
        """
        asof = asof_date or ctx.asof_date
        logger.info(f"cycles.aggregate_overview: asof={asof}")

        cycles_service = CyclesService()

        # Compute all three cycles from service
        stdc_phase = await cycles_service.detect_stdc_phase(as_of_date=asof)
        ltdc_phase = await cycles_service.detect_ltdc_phase(as_of_date=asof)
        empire_phase = await cycles_service.detect_empire_phase(as_of_date=asof)

        # Compute civil cycle using our implementation
        civil_data = await self.cycles_compute_civil(ctx, state, asof_date=asof)

        result = {
            "short_term": {
                "phase_label": stdc_phase.phase,
                "phase_number": stdc_phase.phase_number,
                "composite_score": float(stdc_phase.composite_score),
            },
            "long_term": {
                "phase_label": ltdc_phase.phase,
                "phase_number": ltdc_phase.phase_number,
                "composite_score": float(ltdc_phase.composite_score),
            },
            "empire": {
                "phase_label": empire_phase.phase,
                "phase_number": empire_phase.phase_number,
                "composite_score": float(empire_phase.composite_score),
            },
            "civil": {
                "phase_label": civil_data.get("phase_label", "Rising Tension"),
                "phase_number": civil_data.get("phase_number", 3),
                "composite_score": civil_data.get("composite_score", 0.42),
                "description": civil_data.get("description", "Increasing wealth inequality, declining social cohesion"),
                "indicators": civil_data.get("indicators", {}),
            },
            "date": asof.isoformat(),
        }

        metadata = self._create_metadata(
            source=f"cycles_service:aggregate:{ctx.pricing_pack_id}",
            asof=asof,
            ttl=self.CACHE_TTL_DAY
        )

        return self._attach_metadata(result, metadata)

    async def scenarios_deleveraging_austerity(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        pack_id: Optional[str] = None,
        ltdc_phase: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Apply austerity deleveraging scenario (government spending cuts, tax increases).

        Capability: scenarios.deleveraging_austerity
        """
        logger.info(f"scenarios.deleveraging_austerity: portfolio={portfolio_id}, ltdc_phase={ltdc_phase}")

        from app.services.scenarios import ScenariosService
        scenarios_service = ScenariosService()

        # Define austerity scenario shocks
        scenario_spec = {
            "government_bonds": Decimal("0.15"),  # +15% (flight to safety)
            "equities": Decimal("-0.20"),          # -20% (economic slowdown)
            "commodities": Decimal("-0.15"),       # -15% (demand destruction)
            "currencies_usd": Decimal("0.10"),     # +10% USD strength (deflation)
        }

        result = await scenarios_service.apply_scenario(
            portfolio_id=self._to_uuid(portfolio_id, "portfolio_id"),
            scenario_spec=scenario_spec,
            pack_id=pack_id
        )

        metadata = self._create_metadata(
            source=f"scenarios_service:austerity:{pack_id}",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_NONE  # No caching for scenarios
        )

        return self._attach_metadata(result, metadata)

    async def scenarios_deleveraging_default(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        pack_id: Optional[str] = None,
        ltdc_phase: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Apply default deleveraging scenario (debt defaults, bankruptcies).

        Capability: scenarios.deleveraging_default
        """
        logger.info(f"scenarios.deleveraging_default: portfolio={portfolio_id}, ltdc_phase={ltdc_phase}")

        from app.services.scenarios import ScenariosService
        scenarios_service = ScenariosService()

        # Define default scenario shocks (severe deflation)
        scenario_spec = {
            "government_bonds": Decimal("-0.30"),  # -30% (default risk)
            "equities": Decimal("-0.50"),           # -50% (crisis)
            "commodities": Decimal("-0.40"),        # -40% (collapse in demand)
            "currencies_usd": Decimal("0.20"),      # +20% USD (deflation, flight to safety)
        }

        result = await scenarios_service.apply_scenario(
            portfolio_id=self._to_uuid(portfolio_id, "portfolio_id"),
            scenario_spec=scenario_spec,
            pack_id=pack_id
        )

        metadata = self._create_metadata(
            source=f"scenarios_service:default:{pack_id}",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_NONE
        )

        return self._attach_metadata(result, metadata)

    async def scenarios_deleveraging_money_printing(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        pack_id: Optional[str] = None,
        ltdc_phase: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Apply money printing deleveraging scenario (inflation, currency debasement).

        Capability: scenarios.deleveraging_money_printing
        """
        logger.info(f"scenarios.deleveraging_money_printing: portfolio={portfolio_id}, ltdc_phase={ltdc_phase}")

        from app.services.scenarios import ScenariosService
        scenarios_service = ScenariosService()

        # Define money printing scenario shocks (inflation)
        scenario_spec = {
            "government_bonds": Decimal("-0.25"),   # -25% (inflation erodes value)
            "equities": Decimal("0.10"),             # +10% (nominal gains)
            "commodities": Decimal("0.30"),          # +30% (inflation hedge)
            "currencies_usd": Decimal("-0.15"),      # -15% USD (currency debasement)
        }

        result = await scenarios_service.apply_scenario(
            portfolio_id=self._to_uuid(portfolio_id, "portfolio_id"),
            scenario_spec=scenario_spec,
            pack_id=pack_id
        )

        metadata = self._create_metadata(
            source=f"scenarios_service:money_printing:{pack_id}",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_NONE
        )

        return self._attach_metadata(result, metadata)

    async def scenarios_macro_aware_apply(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        scenario_name: str,
        pack_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Apply a scenario with macro-aware adjustments based on current regime and cycles.

        Capability: scenarios.macro_aware_apply
        """
        logger.info(f"scenarios.macro_aware_apply: portfolio={portfolio_id}, scenario={scenario_name}")

        # Initialize the macro-aware scenario service
        macro_aware_service = MacroAwareScenarioService()

        # Apply the scenario with macro adjustments
        result = await macro_aware_service.apply_macro_aware_scenario(
            portfolio_id=self._to_uuid(portfolio_id, "portfolio_id"),
            scenario_name=scenario_name,
            pack_id=pack_id
        )

        metadata = self._create_metadata(
            source=f"macro_aware_scenarios:{scenario_name}:{pack_id}",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_HOUR  # Cache for 1 hour
        )

        return self._attach_metadata(result, metadata)

    async def scenarios_macro_aware_rank(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        pack_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all scenarios ranked by regime-adjusted probability.

        Capability: scenarios.macro_aware_rank
        """
        logger.info(f"scenarios.macro_aware_rank: portfolio={portfolio_id}")

        # Initialize the macro-aware scenario service
        macro_aware_service = MacroAwareScenarioService()

        # Get regime-weighted scenarios
        ranked_scenarios = await macro_aware_service.get_regime_weighted_scenarios(
            portfolio_id=self._to_uuid(portfolio_id, "portfolio_id"),
            pack_id=pack_id
        )

        # Format results for UI consumption
        result = {
            "portfolio_id": portfolio_id,
            "pack_id": pack_id,
            "macro_state": ranked_scenarios.get("macro_state", {}),
            "scenarios": ranked_scenarios.get("scenarios", []),
            "most_probable": ranked_scenarios.get("scenarios", [])[:3] if ranked_scenarios.get("scenarios") else [],
            "hedging_priorities": [
                s["name"] for s in ranked_scenarios.get("scenarios", [])[:5]
            ],
        }

        metadata = self._create_metadata(
            source=f"macro_aware_scenarios:ranking:{pack_id}",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_HOUR  # Cache for 1 hour
        )

        return self._attach_metadata(result, metadata)

    async def macro_hound_suggest_alert_presets(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        portfolio_id: str,
    ) -> Dict[str, Any]:
        """
        Suggest alert presets based on trend analysis.

        Capability: macro_hound.suggest_alert_presets
        Pattern: macro_trend_monitor.json

        Args:
            ctx: Request context
            state: Pattern state
            trend_analysis: Trend analysis results (from macro.detect_trend_shifts)
            portfolio_id: Portfolio UUID

        Returns:
            {
                "suggestions": [
                    {
                        "type": "regime_shift",
                        "priority": "high",
                        "condition": {...},
                        "playbook": {...}
                    },
                    ...
                ],
                "count": int
            }
        """
        logger.info(f"macro_hound.suggest_alert_presets: portfolio_id={portfolio_id}")

        playbook_gen = PlaybookGenerator()
        suggestions = []

        # Check for regime shift
        if trend_analysis.get("regime_shift_detected"):
            old_regime = trend_analysis.get("old_regime", "Unknown")
            new_regime = trend_analysis.get("new_regime", "Unknown")
            confidence = trend_analysis.get("confidence", 0.0)

            playbook = playbook_gen.generate_regime_shift_playbook(
                old_regime=old_regime,
                new_regime=new_regime,
                confidence=float(confidence)
            )

            suggestions.append({
                "type": "regime_shift",
                "priority": "high",
                "title": f"Regime Shift: {old_regime} → {new_regime}",
                "condition": {
                    "type": "macro",
                    "entity": "regime",
                    "metric": "classification",
                    "op": "!=",
                    "value": old_regime,
                    "window": "weekly"
                },
                "playbook": playbook,
                "confidence": confidence
            })

        # Check for DaR increase
        if trend_analysis.get("dar_increasing"):
            dar_change = trend_analysis.get("dar_change_pct", 0.0)
            current_dar = trend_analysis.get("current_dar", 0.0)

            playbook = playbook_gen.generate_dar_breach_playbook(
                threshold=float(current_dar),
                portfolio_id=portfolio_id,
                severity="warning"
            )

            suggestions.append({
                "type": "dar_increase",
                "priority": "medium",
                "title": f"DaR Increased by {dar_change:.1%}",
                "condition": {
                    "type": "metric",
                    "entity": portfolio_id,
                    "metric": "dar",
                    "op": ">",
                    "value": current_dar * 1.1,  # Alert if 10% higher
                    "window": "weekly"
                },
                "playbook": playbook,
                "dar_change": dar_change
            })

        # Check for factor exposure spikes
        if trend_analysis.get("factor_spike_detected"):
            factor_name = trend_analysis.get("spike_factor", "Unknown")
            spike_magnitude = trend_analysis.get("spike_magnitude", 0.0)

            suggestions.append({
                "type": "factor_spike",
                "priority": "low",
                "title": f"Factor Exposure Spike: {factor_name}",
                "condition": {
                    "type": "metric",
                    "entity": portfolio_id,
                    "metric": f"factor_{factor_name.lower()}_exposure",
                    "op": ">",
                    "value": spike_magnitude * 0.8,
                    "window": "weekly"
                },
                "playbook": {
                    "title": "Factor Exposure Monitoring",
                    "description": f"Monitor {factor_name} exposure for rebalancing opportunities",
                    "actions": [
                        f"Review positions contributing to {factor_name} exposure",
                        "Consider rebalancing to reduce concentration",
                        "Monitor correlation with other factors"
                    ]
                },
                "spike_magnitude": spike_magnitude
            })

        result = {
            "suggestions": suggestions,
            "count": len(suggestions),
            "portfolio_id": portfolio_id,
            "analysis_date": str(ctx.asof_date)
        }

        metadata = self._create_metadata(
            source="alerts_service:suggest_presets",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_HOUR
        )

        return self._attach_metadata(result, metadata)

    async def macro_hound_create_alert_if_threshold(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        news_impact: Dict[str, Any],
        threshold: Optional[float] = 0.05,
    ) -> Dict[str, Any]:
        """
        Create alert if news impact exceeds threshold.

        Capability: macro_hound.create_alert_if_threshold
        Pattern: news_impact_analysis.json

        Args:
            ctx: Request context
            state: Pattern state
            portfolio_id: Portfolio UUID
            news_impact: News impact analysis results
            threshold: Impact threshold (default 5%)

        Returns:
            {
                "alert_created": bool,
                "alert": {...} or None,
                "reason": str (if not created)
            }
        """
        logger.info(f"macro_hound.create_alert_if_threshold: portfolio_id={portfolio_id}, threshold={threshold}")

        alert_service = AlertService(use_db=self.services is not None)

        # Extract total impact
        total_impact = abs(float(news_impact.get("total_impact", 0.0)))
        threshold_value = threshold or 0.05

        if total_impact > threshold_value:
            # Create alert condition
            condition = {
                "type": "news_sentiment",
                "entity": portfolio_id,
                "metric": "total_impact",
                "op": ">",
                "value": threshold_value,
                "window": "intraday"
            }

            # Evaluate condition
            try:
                eval_result = await alert_service.evaluate_condition(
                    condition=condition,
                    ctx={"asof_date": ctx.asof_date}
                )

                alert_data = {
                    "type": "news_impact",
                    "portfolio_id": portfolio_id,
                    "condition": condition,
                    "triggered_at": str(ctx.asof_date),
                    "impact_magnitude": total_impact,
                    "threshold": threshold_value,
                    "evaluation": eval_result,
                    "news_summary": news_impact.get("summary", "Significant news impact detected"),
                    "affected_positions": news_impact.get("affected_positions", [])
                }

                result = {
                    "alert_created": True,
                    "alert": alert_data,
                    "reason": f"News impact ({total_impact:.2%}) exceeded threshold ({threshold_value:.2%})"
                }

                logger.info(f"Alert created for portfolio {portfolio_id}: impact={total_impact:.2%}")

            except Exception as e:
                logger.error(f"Failed to create alert: {e}")
                result = {
                    "alert_created": False,
                    "alert": None,
                    "reason": f"Alert creation failed: {str(e)}"
                }

        else:
            result = {
                "alert_created": False,
                "alert": None,
                "reason": f"Impact ({total_impact:.2%}) below threshold ({threshold_value:.2%})"
            }

            logger.debug(f"No alert created: impact below threshold")

        metadata = self._create_metadata(
            source="alerts_service:create_if_threshold",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_5MIN  # 5 minutes
        )

        return self._attach_metadata(result, metadata)


# ============================================================================
# Singleton Pattern
# ============================================================================

_macro_hound_instance = None


def get_macro_hound(services: Optional[Dict[str, Any]] = None) -> MacroHound:
    """
    Get or create singleton MacroHound agent.

    Args:
        services: Services dict (optional)

    Returns:
        MacroHound instance
    """
    global _macro_hound_instance
    if _macro_hound_instance is None:
        _macro_hound_instance = MacroHound("macro_hound", services or {})
        logger.info("MacroHound agent initialized")
    return _macro_hound_instance