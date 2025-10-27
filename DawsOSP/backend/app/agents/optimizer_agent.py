"""
DawsOS Optimizer Agent

Purpose: Portfolio optimization and rebalancing with Riskfolio-Lib
Updated: 2025-10-27 (Agent Wiring)
Priority: P1 (Core business logic)

Capabilities:
    - optimizer.propose_trades: Generate rebalance trades based on policy constraints
    - optimizer.analyze_impact: Analyze impact of proposed trades on portfolio metrics
    - optimizer.suggest_hedges: Recommend hedges for scenario stress tests
    - optimizer.suggest_deleveraging_hedges: Regime-specific deleveraging recommendations

Architecture:
    Pattern → Agent → OptimizerService → Riskfolio-Lib → Database

Usage:
    agent = OptimizerAgent("optimizer", services)
    runtime.register_agent(agent)

Integration:
    - Consumes positions from Financial Analyst (ledger.positions)
    - Consumes pricing from Financial Analyst (pricing.apply_pack)
    - Consumes ratings from Ratings Agent (ratings.aggregate) for quality filtering
    - Powers policy_rebalance pattern
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.base_agent import BaseAgent, AgentMetadata
from app.core.types import RequestCtx
from backend.app.services.optimizer import get_optimizer_service

logger = logging.getLogger("DawsOS.OptimizerAgent")


class OptimizerAgent(BaseAgent):
    """
    Optimizer Agent - Portfolio optimization and rebalancing.

    Provides capabilities for:
        - Trade proposal generation (policy-based rebalancing)
        - Impact analysis (before/after metrics)
        - Hedge recommendations (scenario stress testing)
        - Deleveraging recommendations (regime-based)

    Uses Riskfolio-Lib for optimization:
        - Mean-Variance (Markowitz)
        - Risk Parity
        - Maximum Sharpe Ratio
        - CVaR (Conditional Value at Risk)
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "optimizer.propose_trades",
            "optimizer.analyze_impact",
            "optimizer.suggest_hedges",
            "optimizer.suggest_deleveraging_hedges",
        ]

    async def optimizer_propose_trades(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        policy_json: Optional[Dict[str, Any]] = None,
        positions: Optional[List[Dict[str, Any]]] = None,
        ratings: Optional[Dict[str, float]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate rebalance trade proposals based on policy constraints.

        Capability: optimizer.propose_trades

        Policy Constraints (policy_json):
            - min_quality_score: Minimum aggregate quality rating (0-10)
            - max_single_position_pct: Maximum weight per position (%)
            - max_sector_pct: Maximum sector concentration (%)
            - max_turnover_pct: Maximum turnover percentage
            - max_tracking_error_pct: Maximum tracking error vs benchmark
            - method: Optimization method (mean_variance, risk_parity, max_sharpe, cvar)

        Args:
            ctx: Request context
            state: Execution state (may contain positions, ratings from prior steps)
            portfolio_id: Portfolio UUID (optional, uses ctx.portfolio_id if not provided)
            policy_json: Policy constraints dict (optional, uses defaults)
            positions: Valued positions (optional, fetched if not provided)
            ratings: Dict of {symbol: quality_score} (optional, from ratings agent)
            **kwargs: Additional arguments

        Returns:
            Dict with:
                - trades: List of trade proposals
                - trade_count: int
                - total_turnover: Decimal
                - turnover_pct: float
                - estimated_costs: Decimal
                - cost_bps: float
                - method: str (optimization method)
                - constraints_met: bool
                - warnings: List[str]
                - _metadata: Metadata dict
        """
        # Resolve portfolio_id
        if not portfolio_id:
            portfolio_id = str(ctx.portfolio_id) if ctx.portfolio_id else None
        if not portfolio_id:
            raise ValueError("portfolio_id required for optimizer.propose_trades")

        portfolio_uuid = UUID(portfolio_id)

        # Default policy if not provided
        if not policy_json:
            policy_json = {
                "min_quality_score": 0.0,
                "max_single_position_pct": 20.0,
                "max_sector_pct": 30.0,
                "max_turnover_pct": 20.0,
                "max_tracking_error_pct": 3.0,
                "method": "mean_variance",
            }

        # Get pricing_pack_id from context (SACRED for reproducibility)
        pricing_pack_id = ctx.pricing_pack_id
        if not pricing_pack_id:
            raise ValueError("pricing_pack_id required in context for optimizer.propose_trades")

        # Get ratings from state if not provided
        if not ratings and state.get("ratings"):
            # Extract quality scores from ratings result
            ratings_result = state["ratings"]
            if isinstance(ratings_result, dict) and "positions" in ratings_result:
                # Portfolio ratings mode
                ratings = {
                    pos["symbol"]: pos.get("rating", 0.0)
                    for pos in ratings_result["positions"]
                    if pos.get("rating") is not None
                }
            elif isinstance(ratings_result, dict) and "overall_rating" in ratings_result:
                # Single security ratings mode
                symbol = ratings_result.get("symbol")
                if symbol:
                    ratings = {symbol: float(ratings_result["overall_rating"]) / 10.0}

        logger.info(
            f"optimizer.propose_trades: portfolio_id={portfolio_id}, "
            f"pricing_pack_id={pricing_pack_id}, "
            f"policy={policy_json.get('method', 'mean_variance')}"
        )

        # Call optimizer service
        optimizer_service = get_optimizer_service()

        try:
            result = await optimizer_service.propose_trades(
                portfolio_id=portfolio_uuid,
                policy_json=policy_json,
                pricing_pack_id=pricing_pack_id,
                ratings=ratings,
            )

            # Attach metadata
            metadata = self._create_metadata(
                source=f"optimizer_service:{ctx.pricing_pack_id}",
                asof=ctx.asof_date or date.today(),
                ttl=0,  # No caching for trade proposals (always fresh)
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"Trade proposal generation failed: {e}", exc_info=True)
            error_result = {
                "trades": [],
                "trade_count": 0,
                "total_turnover": Decimal("0"),
                "turnover_pct": 0.0,
                "estimated_costs": Decimal("0"),
                "cost_bps": 0.0,
                "error": str(e),
                "constraints_met": False,
                "warnings": [f"Optimization failed: {str(e)}"],
            }
            metadata = self._create_metadata(
                source=f"optimizer_service:error",
                asof=ctx.asof_date or date.today(),
                ttl=0,
            )
            return self._attach_metadata(error_result, metadata)

    async def optimizer_analyze_impact(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        proposed_trades: Optional[List[Dict[str, Any]]] = None,
        current_positions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Analyze impact of proposed trades on portfolio metrics.

        Capability: optimizer.analyze_impact

        Analyzes before/after:
            - Portfolio value
            - Average dividend safety
            - Average moat strength
            - Concentration (top 10 holdings)
            - Tracking error
            - Sharpe ratio
            - Expected return

        Args:
            ctx: Request context
            state: Execution state (may contain trades, positions from prior steps)
            portfolio_id: Portfolio UUID
            proposed_trades: List of trade proposals (from propose_trades)
            current_positions: Current valued positions
            **kwargs: Additional arguments

        Returns:
            Dict with:
                - current_value: Decimal
                - post_rebalance_value: Decimal
                - value_delta: Decimal
                - current_div_safety: float
                - post_div_safety: float
                - div_safety_delta: float
                - current_moat: float
                - post_moat: float
                - moat_delta: float
                - current_concentration: float
                - post_concentration: float
                - concentration_delta: float
                - te_delta: float
                - _metadata: Metadata dict
        """
        # Resolve portfolio_id
        if not portfolio_id:
            portfolio_id = str(ctx.portfolio_id) if ctx.portfolio_id else None
        if not portfolio_id:
            raise ValueError("portfolio_id required for optimizer.analyze_impact")

        portfolio_uuid = UUID(portfolio_id)

        # Get proposed_trades from state if not provided
        if not proposed_trades:
            rebalance_result = state.get("rebalance_result")
            if rebalance_result and "trades" in rebalance_result:
                proposed_trades = rebalance_result["trades"]
        if not proposed_trades:
            raise ValueError(
                "proposed_trades required for optimizer.analyze_impact. "
                "Run optimizer.propose_trades first."
            )

        # Get pricing_pack_id from context
        pricing_pack_id = ctx.pricing_pack_id
        if not pricing_pack_id:
            raise ValueError("pricing_pack_id required in context for optimizer.analyze_impact")

        logger.info(
            f"optimizer.analyze_impact: portfolio_id={portfolio_id}, "
            f"trades={len(proposed_trades)}, "
            f"pricing_pack_id={pricing_pack_id}"
        )

        # Call optimizer service
        optimizer_service = get_optimizer_service()

        try:
            result = await optimizer_service.analyze_impact(
                portfolio_id=portfolio_uuid,
                proposed_trades=proposed_trades,
                pricing_pack_id=pricing_pack_id,
            )

            # Attach metadata
            metadata = self._create_metadata(
                source=f"optimizer_service:{ctx.pricing_pack_id}",
                asof=ctx.asof_date or date.today(),
                ttl=0,  # No caching for impact analysis
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"Impact analysis failed: {e}", exc_info=True)
            error_result = {
                "current_value": Decimal("0"),
                "post_rebalance_value": Decimal("0"),
                "value_delta": Decimal("0"),
                "error": str(e),
            }
            metadata = self._create_metadata(
                source=f"optimizer_service:error",
                asof=ctx.asof_date or date.today(),
                ttl=0,
            )
            return self._attach_metadata(error_result, metadata)

    async def optimizer_suggest_hedges(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Suggest hedge instruments for a scenario stress test.

        Capability: optimizer.suggest_hedges

        Scenario Types:
            - rates_up: Rate increase scenario
            - equity_selloff: Equity market crash
            - usd_up: USD appreciation
            - credit_spread_widening: Credit spread blowout

        Hedge Instruments:
            - SPY put options (equity hedges)
            - TLT put options (duration hedges)
            - UUP short (USD hedges)
            - LQD put options (credit hedges)

        Args:
            ctx: Request context
            state: Execution state
            portfolio_id: Portfolio UUID
            scenario_id: Scenario ID (e.g., "rates_up", "equity_selloff")
            **kwargs: Additional arguments

        Returns:
            Dict with:
                - hedges: List[HedgeRecommendation] as dicts
                - total_notional: Decimal
                - expected_offset_pct: float (expected portfolio loss offset)
                - scenario_id: str
                - _metadata: Metadata dict
        """
        # Resolve portfolio_id
        if not portfolio_id:
            portfolio_id = str(ctx.portfolio_id) if ctx.portfolio_id else None
        if not portfolio_id:
            raise ValueError("portfolio_id required for optimizer.suggest_hedges")

        portfolio_uuid = UUID(portfolio_id)

        # Require scenario_id
        if not scenario_id:
            raise ValueError("scenario_id required for optimizer.suggest_hedges")

        # Get pricing_pack_id from context
        pricing_pack_id = ctx.pricing_pack_id
        if not pricing_pack_id:
            raise ValueError("pricing_pack_id required in context for optimizer.suggest_hedges")

        logger.info(
            f"optimizer.suggest_hedges: portfolio_id={portfolio_id}, "
            f"scenario_id={scenario_id}, "
            f"pricing_pack_id={pricing_pack_id}"
        )

        # Call optimizer service
        optimizer_service = get_optimizer_service()

        try:
            result = await optimizer_service.suggest_hedges(
                portfolio_id=portfolio_uuid,
                scenario_id=scenario_id,
                pricing_pack_id=pricing_pack_id,
            )

            # Attach metadata
            metadata = self._create_metadata(
                source=f"optimizer_service:hedges:{scenario_id}",
                asof=ctx.asof_date or date.today(),
                ttl=3600,  # Cache for 1 hour
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"Hedge suggestion failed for scenario {scenario_id}: {e}", exc_info=True)
            error_result = {
                "hedges": [],
                "total_notional": Decimal("0"),
                "expected_offset_pct": 0.0,
                "scenario_id": scenario_id,
                "error": str(e),
            }
            metadata = self._create_metadata(
                source=f"optimizer_service:error",
                asof=ctx.asof_date or date.today(),
                ttl=0,
            )
            return self._attach_metadata(error_result, metadata)

    async def optimizer_suggest_deleveraging_hedges(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        regime: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Suggest deleveraging hedges based on macro regime.

        Capability: optimizer.suggest_deleveraging_hedges

        Dalio Deleveraging Playbook:
            - DELEVERAGING / DEPRESSION: Aggressive deleveraging
                - Reduce equity 40%
                - Increase safe havens (GLD, TLT, CASH) to 30%
                - Exit high-yield credit 100%

            - LATE_EXPANSION: Moderate deleveraging
                - Reduce equity 20%
                - Increase defensive sectors (XLU, XLP, VNQ) to 15%

            - REFLATION: Reduce duration, increase real assets
                - Reduce long-duration bonds (TLT, IEF) 50%
                - Increase inflation hedges (GLD, TIP, DBC) to 20%

        Args:
            ctx: Request context
            state: Execution state (may contain regime from macro.detect_regime)
            portfolio_id: Portfolio UUID
            regime: Macro regime (e.g., "LATE_EXPANSION", "DELEVERAGING")
            **kwargs: Additional arguments

        Returns:
            Dict with:
                - recommendations: List[Dict] with action/instruments/rationale
                - regime: str
                - total_reduction_pct: float
                - total_allocation_pct: float
                - _metadata: Metadata dict
        """
        # Resolve portfolio_id
        if not portfolio_id:
            portfolio_id = str(ctx.portfolio_id) if ctx.portfolio_id else None
        if not portfolio_id:
            raise ValueError("portfolio_id required for optimizer.suggest_deleveraging_hedges")

        portfolio_uuid = UUID(portfolio_id)

        # Get regime from state if not provided
        if not regime:
            regime_result = state.get("regime")
            if regime_result and isinstance(regime_result, dict):
                regime = regime_result.get("regime")
        if not regime:
            raise ValueError(
                "regime required for optimizer.suggest_deleveraging_hedges. "
                "Run macro.detect_regime first."
            )

        # Get pricing_pack_id from context
        pricing_pack_id = ctx.pricing_pack_id
        if not pricing_pack_id:
            raise ValueError("pricing_pack_id required in context for optimizer.suggest_deleveraging_hedges")

        logger.info(
            f"optimizer.suggest_deleveraging_hedges: portfolio_id={portfolio_id}, "
            f"regime={regime}, "
            f"pricing_pack_id={pricing_pack_id}"
        )

        # Call optimizer service
        optimizer_service = get_optimizer_service()

        try:
            result = await optimizer_service.suggest_deleveraging_hedges(
                portfolio_id=portfolio_uuid,
                regime=regime,
                pricing_pack_id=pricing_pack_id,
            )

            # Attach metadata
            metadata = self._create_metadata(
                source=f"optimizer_service:deleveraging:{regime}",
                asof=ctx.asof_date or date.today(),
                ttl=3600,  # Cache for 1 hour
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"Deleveraging hedge suggestion failed for regime {regime}: {e}", exc_info=True)
            error_result = {
                "recommendations": [],
                "regime": regime,
                "total_reduction_pct": 0.0,
                "total_allocation_pct": 0.0,
                "error": str(e),
            }
            metadata = self._create_metadata(
                source=f"optimizer_service:error",
                asof=ctx.asof_date or date.today(),
                ttl=0,
            )
            return self._attach_metadata(error_result, metadata)
