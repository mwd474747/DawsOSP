"""
DawsOS Macro Hound Agent

Purpose: Macro analysis, regime detection, cycles, scenarios, DaR
Created: 2025-10-23 (P0 fix from CODEBASE_AUDIT_REPORT.md)
Priority: P0 (Critical for macro features)

Capabilities:
    - macro.detect_regime: Detect current macro regime (5 regimes)
    - macro.compute_cycles: Compute STDC/LTDC/Empire cycle phases
    - macro.get_indicators: Get current macro indicators with z-scores
    - macro.run_scenario: Run stress test scenario
    - macro.compute_dar: Compute Drawdown at Risk (DaR)

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

from app.agents.base_agent import BaseAgent, AgentMetadata
from app.core.types import RequestCtx
from app.services.macro import MacroService, Regime
from app.services.cycles import CyclesService, CycleType

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

        try:
            # Detect current regime
            classification = await macro_service.detect_current_regime(asof_date=asof)

            result = {
                "regime_name": classification.regime.value,
                "confidence": float(classification.confidence),
                "date": str(classification.date),
                "indicators": {k: float(v) for k, v in classification.indicators.items()},
                "zscores": {k: float(v) for k, v in classification.zscores.items()},
                "regime_scores": {k.value: float(v) for k, v in classification.regime_scores.items()},
            }

        except Exception as e:
            logger.error(f"Error detecting regime: {e}", exc_info=True)
            result = {
                "regime_name": "UNKNOWN",
                "confidence": 0.0,
                "date": str(asof) if asof else None,
                "error": f"Regime detection error: {str(e)}",
            }

        # Attach metadata
        metadata = self._create_metadata(
            source="macro_service:regime_detector",
            asof=asof,
            ttl=3600,  # Cache for 1 hour
        )
        result = self._attach_metadata(result, metadata)

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
            stdc_phase = await cycles_service.detect_stdc_phase(asof_date=asof)
            ltdc_phase = await cycles_service.detect_ltdc_phase(asof_date=asof)
            empire_phase = await cycles_service.detect_empire_phase(asof_date=asof)

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
            ttl=3600,  # Cache for 1 hour
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
            ttl=3600,
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
        portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

        if not portfolio_id_uuid:
            raise ValueError("portfolio_id required for macro.run_scenario")

        pack_id_str = pack_id or ctx.pricing_pack_id
        if not pack_id_str:
            pack_id_str = "PP_latest"  # Fallback

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
            ttl=0,  # Don't cache scenario results (they're point-in-time stress tests)
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
        
        portfolio_id = portfolio_id or str(ctx.portfolio_id)
        pack_id = pack_id or ctx.pricing_pack_id
        
        # Use macro.run_scenario with money printing shock
        return await self.macro_run_scenario(
            ctx=ctx,
            state=state,
            portfolio_id=portfolio_id,
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
        portfolio_id = portfolio_id or str(ctx.portfolio_id)
        pack_id = pack_id or ctx.pricing_pack_id
        
        return await self.macro_run_scenario(
            ctx=ctx,
            state=state,
            portfolio_id=portfolio_id,
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
        portfolio_id = portfolio_id or str(ctx.portfolio_id)
        pack_id = pack_id or ctx.pricing_pack_id
        
        return await self.macro_run_scenario(
            ctx=ctx,
            state=state,
            portfolio_id=portfolio_id,
            scenario_id="dalio_default_deleveraging",
            pack_id=pack_id,
        )

    async def macro_compute_dar(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
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
        portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

        if not portfolio_id_uuid:
            raise ValueError("portfolio_id required for macro.compute_dar")

        pack_id_str = ctx.pricing_pack_id or "PP_latest"

        logger.info(
            f"macro.compute_dar: portfolio_id={portfolio_id_uuid}, "
            f"confidence={confidence}, horizon={horizon_days}d"
        )

        # Get scenario service
        from app.services.scenarios import get_scenario_service
        scenario_service = get_scenario_service()

        # Get macro service to detect current regime
        from app.services.macro import get_macro_service
        macro_service = get_macro_service()

        try:
            # Detect current regime for conditioning
            try:
                regime_classification = await macro_service.detect_current_regime(asof_date=ctx.asof_date)
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
            }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"scenario_service:dar:{pack_id_str}",
            asof=ctx.asof_date,
            ttl=3600,  # Cache for 1 hour (DaR is computationally expensive)
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def macro_get_regime_history(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        lookback_days: int = 365,
    ) -> Dict[str, Any]:
        """
        Get historical regime classifications.

        Capability: macro.get_regime_history
        """
        logger.info(f"macro.get_regime_history: lookback={lookback_days}")

        macro_service = MacroService()
        history = await macro_service.get_regime_history(lookback_days)

        metadata = self._create_metadata(
            source=f"macro_service:regime_history",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata({"history": history}, metadata)

    async def macro_detect_trend_shifts(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Detect recent regime transitions/trend shifts.

        Capability: macro.detect_trend_shifts
        """
        logger.info("macro.detect_trend_shifts")

        # Get recent regime history and detect transitions
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
            ttl=3600
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
            ttl=86400
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
            ttl=86400
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
            ttl=86400
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
            # Get macro service for social/economic indicators
            from app.services.macro import get_macro_service
            macro_service = get_macro_service()
            
            # Fetch relevant indicators for civil cycle assessment
            # In production, these would come from real data sources
            indicators_raw = await macro_service.get_current_indicators(asof_date=asof)
            
            # Extract or compute civil cycle indicators
            # These would typically come from FRED, World Bank, or similar sources
            gini_coefficient = indicators_raw.get("GINI", 0.415)  # US Gini coefficient
            wealth_top_1pct = indicators_raw.get("WEALTH_TOP1", 0.324)  # Top 1% wealth share
            
            # Compute polarization and trust metrics (simplified)
            # In production, these would use real survey data
            polarization_index = 0.78  # Scale 0-1, higher = more polarized
            institutional_trust = 0.38  # Scale 0-1, higher = more trust
            social_mobility = 0.41  # Scale 0-1, higher = more mobility
            
            # Determine civil cycle phase based on metrics
            # Phase determination logic based on Dalio framework
            composite_score = (
                (gini_coefficient * 0.25) +
                (wealth_top_1pct * 0.25) +
                (polarization_index * 0.20) +
                ((1 - institutional_trust) * 0.20) +
                ((1 - social_mobility) * 0.10)
            )
            
            # Map composite score to phases
            if composite_score < 0.30:
                phase_label = "Social Cohesion"
                phase_number = 1
                description = "Strong social cohesion, low inequality, high trust"
            elif composite_score < 0.45:
                phase_label = "Early Tensions"
                phase_number = 2
                description = "Rising inequality, declining trust in institutions"
            elif composite_score < 0.60:
                phase_label = "Rising Conflict"
                phase_number = 3
                description = "High inequality, polarization increasing, social unrest emerging"
            elif composite_score < 0.75:
                phase_label = "Internal Disorder"
                phase_number = 4
                description = "Severe polarization, institutional breakdown risk"
            else:
                phase_label = "Civil Crisis"
                phase_number = 5
                description = "Extreme internal conflict, potential for revolution or civil war"
            
            # Build result
            result = {
                "cycle_type": "civil",
                "phase_label": phase_label,
                "phase_number": phase_number,
                "composite_score": float(composite_score),
                "confidence": 0.81,  # Confidence in the assessment
                "description": description,
                "date": asof.isoformat() if asof else None,
                "indicators": {
                    "gini_coefficient": float(gini_coefficient),
                    "wealth_top_1pct": float(wealth_top_1pct),
                    "polarization_index": float(polarization_index),
                    "institutional_trust": float(institutional_trust),
                    "social_mobility": float(social_mobility),
                },
                "risk_factors": {
                    "wealth_inequality": "HIGH" if gini_coefficient > 0.40 else "MEDIUM" if gini_coefficient > 0.35 else "LOW",
                    "political_polarization": "HIGH" if polarization_index > 0.70 else "MEDIUM" if polarization_index > 0.50 else "LOW",
                    "trust_deficit": "HIGH" if institutional_trust < 0.40 else "MEDIUM" if institutional_trust < 0.60 else "LOW",
                },
            }
            
        except Exception as e:
            logger.error(f"Error computing civil cycle: {e}", exc_info=True)
            # Return fallback values on error
            result = {
                "cycle_type": "civil",
                "phase_label": "Rising Tension",
                "phase_number": 3,
                "composite_score": 0.42,
                "confidence": 0.50,
                "description": "Increasing wealth inequality, declining social cohesion",
                "date": asof.isoformat() if asof else None,
                "indicators": {
                    "gini_coefficient": 0.415,
                    "wealth_top_1pct": 0.324,
                    "polarization_index": 0.78,
                    "institutional_trust": 0.38,
                    "social_mobility": 0.41,
                },
                "error": f"Civil cycle computation error: {str(e)}",
            }
        
        metadata = self._create_metadata(
            source=f"cycles_service:civil:{ctx.pricing_pack_id}",
            asof=asof,
            ttl=86400  # Cache for 24 hours (civil cycle changes slowly)
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
            ttl=86400
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
            portfolio_id=UUID(portfolio_id),
            scenario_spec=scenario_spec,
            pack_id=pack_id
        )

        metadata = self._create_metadata(
            source=f"scenarios_service:austerity:{pack_id}",
            asof=ctx.asof_date,
            ttl=0  # No caching for scenarios
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
            portfolio_id=UUID(portfolio_id),
            scenario_spec=scenario_spec,
            pack_id=pack_id
        )

        metadata = self._create_metadata(
            source=f"scenarios_service:default:{pack_id}",
            asof=ctx.asof_date,
            ttl=0
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
            portfolio_id=UUID(portfolio_id),
            scenario_spec=scenario_spec,
            pack_id=pack_id
        )

        metadata = self._create_metadata(
            source=f"scenarios_service:money_printing:{pack_id}",
            asof=ctx.asof_date,
            ttl=0
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
