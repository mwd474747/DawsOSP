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
    ) -> Dict[str, Any]:
        """
        Run stress test scenario.

        Applies a stress test scenario to the portfolio and computes the
        expected change in portfolio value.

        Args:
            ctx: Request context
            state: Execution state
            portfolio_id: Portfolio ID (optional, uses ctx.portfolio_id if not provided)
            scenario_id: Scenario ID (e.g., "2008_financial_crisis")
            scenario_params: Custom scenario parameters (shocks to apply)

        Returns:
            Dict with scenario results

        Example:
            {
                "scenario_id": "2008_financial_crisis",
                "scenario_name": "2008 Financial Crisis",
                "portfolio_id": "11111111-1111-1111-1111-111111111111",
                "current_value": 140000.0,
                "shocked_value": 105000.0,
                "delta_pl": -35000.0,
                "delta_pl_pct": -0.25,
                "by_holding": [
                    {
                        "symbol": "AAPL",
                        "current_value": 52500.0,
                        "shocked_value": 39375.0,
                        "delta_pl": -13125.0,
                        "delta_pl_pct": -0.25
                    },
                    ...
                ],
                "__metadata__": {...}
            }
        """
        portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

        if not portfolio_id_uuid:
            raise ValueError("portfolio_id required for macro.run_scenario")

        logger.info(
            f"macro.run_scenario: portfolio_id={portfolio_id_uuid}, "
            f"scenario_id={scenario_id}"
        )

        # TODO: Implement scenario service
        # For now, return stub data
        result = {
            "scenario_id": scenario_id or "custom",
            "scenario_name": "Custom Scenario" if not scenario_id else scenario_id.replace("_", " ").title(),
            "portfolio_id": str(portfolio_id_uuid),
            "current_value": None,
            "shocked_value": None,
            "delta_pl": None,
            "delta_pl_pct": None,
            "by_holding": [],
            "error": "Scenario service not yet implemented",
        }

        # Attach metadata
        metadata = self._create_metadata(
            source="scenario_service:stress_test",
            asof=ctx.asof_date,
            ttl=0,  # Don't cache scenario results
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def macro_compute_dar(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        confidence: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Compute Drawdown at Risk (DaR).

        Computes the expected maximum drawdown at a given confidence level
        by running 13 macro scenarios and taking the specified percentile.

        Args:
            ctx: Request context
            state: Execution state
            portfolio_id: Portfolio ID (optional)
            confidence: Confidence level (default 0.95 = 95%)

        Returns:
            Dict with DaR computation

        Example:
            {
                "dar_value": -0.185,  # 18.5% drawdown at 95% confidence
                "confidence": 0.95,
                "portfolio_id": "11111111-1111-1111-1111-111111111111",
                "scenarios_run": 13,
                "worst_scenario": "2008_financial_crisis",
                "worst_scenario_drawdown": -0.35,
                "scenario_distribution": [
                    {"scenario": "2008_financial_crisis", "drawdown": -0.35},
                    {"scenario": "covid_2020", "drawdown": -0.28},
                    ...
                ],
                "__metadata__": {...}
            }
        """
        portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

        if not portfolio_id_uuid:
            raise ValueError("portfolio_id required for macro.compute_dar")

        logger.info(
            f"macro.compute_dar: portfolio_id={portfolio_id_uuid}, "
            f"confidence={confidence}"
        )

        # TODO: Implement DaR service
        # For now, return stub data
        result = {
            "dar_value": None,
            "confidence": confidence,
            "portfolio_id": str(portfolio_id_uuid),
            "scenarios_run": 0,
            "worst_scenario": None,
            "worst_scenario_drawdown": None,
            "scenario_distribution": [],
            "error": "DaR service not yet implemented",
        }

        # Attach metadata
        metadata = self._create_metadata(
            source="risk_service:dar_computation",
            asof=ctx.asof_date,
            ttl=3600,
        )
        result = self._attach_metadata(result, metadata)

        return result


# ============================================================================
# Factory Function (Singleton Pattern)
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
