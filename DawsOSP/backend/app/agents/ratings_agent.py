"""
DawsOS Ratings Agent

Purpose: Format ratings service results for pattern execution
Created: 2025-10-24 (Phase 1 MVP - governance remediation)
Priority: P1 (Critical for buffett_checklist pattern)

Capabilities:
    - ratings.dividend_safety: Calculate dividend sustainability (0-10 scale)
    - ratings.moat_strength: Calculate competitive moat strength (0-10 scale)
    - ratings.resilience: Calculate balance sheet strength (0-10 scale)

Architecture:
    Pattern → Agent Runtime → RatingsAgent → RatingsService

CRITICAL: Agent does NOT duplicate business logic from service.
          Agent only:
          1. Looks up symbol from security_id
          2. Calls service
          3. Formats service response for pattern compatibility

Governance: .ops/RATINGS_IMPLEMENTATION_GOVERNANCE.md
Specification: .claude/agents/business/RATINGS_ARCHITECT.md
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.base_agent import BaseAgent, AgentMetadata
from app.core.types import RequestCtx
from app.services.ratings import get_ratings_service

logger = logging.getLogger("DawsOS.RatingsAgent")


class RatingsAgent(BaseAgent):
    """
    Ratings Agent - Wraps ratings service for pattern execution.

    This agent does NOT contain business logic - it only:
        1. Looks up symbol from security_id (database query)
        2. Gets fundamentals from state or stubs (Phase 1)
        3. Calls RatingsService
        4. Formats response for pattern compatibility
        5. Attaches metadata for traceability

    All scoring logic is in RatingsService to prevent duplication.
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "ratings.dividend_safety",
            "ratings.moat_strength",
            "ratings.resilience",
            "ratings.aggregate",
        ]

    async def ratings_dividend_safety(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        security_id: Optional[str] = None,
        fundamentals: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate dividend safety rating (0-10 scale).

        Pattern Interface:
            Expects: security_id (UUID), optionally fundamentals dict
            Returns: Dict with rating, components, metadata

        Agent Responsibilities:
            1. Lookup symbol from security_id (database)
            2. Get/validate fundamentals
            3. Call service
            4. Format response
            5. Attach metadata

        Service Responsibilities (NO duplication here):
            - Apply thresholds
            - Calculate component scores
            - Apply weights
            - Return component breakdown

        Args:
            ctx: Request context (provides pricing_pack_id, asof_date)
            state: Execution state (may contain fundamentals from prior step)
            security_id: Security UUID (required)
            fundamentals: Fundamental data dict (optional, Phase 1 uses stubs)

        Returns:
            Dict formatted for buffett_checklist pattern presentation layer

        Raises:
            ValueError: If security_id not provided or security not found
        """
        if not security_id:
            raise ValueError("security_id is required for ratings.dividend_safety")

        logger.info(f"ratings.dividend_safety: security_id={security_id}")

        # Phase 1: Lookup symbol from security_id
        # TODO Phase 2: Query database instead of stub
        symbol = await self._get_symbol_from_security_id(security_id)

        # Get fundamentals from state or use stubs (Phase 1)
        if fundamentals is None:
            fundamentals = state.get("fundamentals")
            if fundamentals is None:
                logger.warning(
                    f"No fundamentals in state for {security_id}, using stubs"
                )
                fundamentals = self._stub_fundamentals_for_testing()

        # Call service (service contains ALL business logic)
        ratings_service = get_ratings_service()
        service_result = await ratings_service.calculate_dividend_safety(
            symbol, fundamentals
        )

        # Format for pattern (map service components to pattern expectations)
        result = {
            "overall_score": float(service_result["overall"]),
            "rating": float(service_result["overall"]),
            # Extract component scores from service result (no recalculation)
            "payout_score": float(service_result["components"]["payout_ratio"]["score"]),
            "coverage_score": float(service_result["components"]["fcf_coverage"]["score"]),
            "streak_score": float(service_result["components"]["growth_streak"]["score"]),
            "cash_score": float(service_result["components"]["net_cash"]["score"]),
            # Additional fields for pattern
            "fcf_coverage": float(fundamentals.get("fcf_dividend_coverage", 0)),
            "risk_flag": self._check_risk_flag(service_result["overall"]),
            # Include full component breakdown for debugging
            "components": service_result["components"],
        }

        # Attach metadata for traceability
        metadata = self._create_metadata(
            source=f"ratings_service:{ctx.pricing_pack_id}",
            asof=ctx.asof_date,
            ttl=86400,  # Cache for 24 hours
        )

        return self._attach_metadata(result, metadata)

    async def ratings_moat_strength(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        security_id: Optional[str] = None,
        fundamentals: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate economic moat strength rating (0-10 scale).

        Agent wraps service - NO business logic duplication.

        Args:
            ctx: Request context
            state: Execution state
            security_id: Security UUID (required)
            fundamentals: Fundamental data dict (optional)

        Returns:
            Dict formatted for pattern presentation

        Raises:
            ValueError: If security_id not provided
        """
        if not security_id:
            raise ValueError("security_id is required for ratings.moat_strength")

        logger.info(f"ratings.moat_strength: security_id={security_id}")

        symbol = await self._get_symbol_from_security_id(security_id)

        if fundamentals is None:
            fundamentals = state.get("fundamentals")
            if fundamentals is None:
                logger.warning(
                    f"No fundamentals in state for {security_id}, using stubs"
                )
                fundamentals = self._stub_fundamentals_for_testing()

        # Call service (service contains ALL scoring logic)
        ratings_service = get_ratings_service()
        service_result = await ratings_service.calculate_moat_strength(
            symbol, fundamentals
        )

        # Format for pattern (extract from service, don't recalculate)
        result = {
            "overall_score": float(service_result["overall"]),
            "moat_score": float(service_result["overall"]),
            # Extract component scores from service
            "roe_score": float(service_result["components"]["roe_consistency"]["score"]),
            "margin_score": float(service_result["components"]["gross_margin"]["score"]),
            "intangibles_score": float(service_result["components"]["intangibles"]["score"]),
            "switching_score": float(service_result["components"]["switching_costs"]["score"]),
            # Pattern compatibility fields (stub values for Phase 1)
            "fcf_score": 0,  # TODO Phase 2: Add to service
            "growth_stability_score": 0,  # TODO Phase 2: Add to service
            "brand_score": 0,  # Qualitative (Phase 2)
            "network_score": 0,
            "cost_score": 0,
            "primary_moat_type": self._infer_moat_type(service_result["components"]),
            "brand_evidence": "",
            "network_evidence": "",
            "cost_evidence": "",
            "switching_evidence": "",
            # Include full breakdown
            "components": service_result["components"],
        }

        metadata = self._create_metadata(
            source=f"ratings_service:{ctx.pricing_pack_id}",
            asof=ctx.asof_date,
            ttl=86400,
        )

        return self._attach_metadata(result, metadata)

    async def ratings_resilience(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        security_id: Optional[str] = None,
        fundamentals: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate financial resilience rating (0-10 scale).

        Agent wraps service - NO business logic duplication.

        Args:
            ctx: Request context
            state: Execution state
            security_id: Security UUID (required)
            fundamentals: Fundamental data dict (optional)

        Returns:
            Dict formatted for pattern presentation

        Raises:
            ValueError: If security_id not provided
        """
        if not security_id:
            raise ValueError("security_id is required for ratings.resilience")

        logger.info(f"ratings.resilience: security_id={security_id}")

        symbol = await self._get_symbol_from_security_id(security_id)

        if fundamentals is None:
            fundamentals = state.get("fundamentals")
            if fundamentals is None:
                logger.warning(
                    f"No fundamentals in state for {security_id}, using stubs"
                )
                fundamentals = self._stub_fundamentals_for_testing()

        # Call service (service contains ALL scoring logic)
        ratings_service = get_ratings_service()
        service_result = await ratings_service.calculate_resilience(symbol, fundamentals)

        # Format for pattern (extract from service, don't recalculate)
        result = {
            "overall_score": float(service_result["overall"]),
            "rating": float(service_result["overall"]),
            # Extract component scores from service
            "debt_equity_score": float(service_result["components"]["debt_equity"]["score"]),
            "coverage_score": float(service_result["components"]["interest_coverage"]["score"]),
            "liquidity_score": float(service_result["components"]["current_ratio"]["score"]),
            "stability_score": float(service_result["components"]["margin_stability"]["score"]),
            # Include full breakdown
            "components": service_result["components"],
        }

        metadata = self._create_metadata(
            source=f"ratings_service:{ctx.pricing_pack_id}",
            asof=ctx.asof_date,
            ttl=86400,
        )

        return self._attach_metadata(result, metadata)

    # ========================================================================
    # Helper Methods (NO business logic - only data access and formatting)
    # ========================================================================

    async def _get_symbol_from_security_id(self, security_id: str) -> str:
        """
        Lookup symbol from security_id UUID.

        Queries database securities table for symbol.

        Args:
            security_id: UUID string

        Returns:
            Symbol (str)

        Raises:
            ValueError: If security not found in database
        """
        db_pool = self.services.get("db")
        if not db_pool:
            raise RuntimeError("Database pool not available in agent services")

        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT symbol FROM securities WHERE id = $1", UUID(security_id)
            )
            if not result:
                raise ValueError(f"Security not found: {security_id}")

            symbol = result["symbol"]
            logger.debug(f"Database lookup: {security_id} → {symbol}")
            return symbol

    def _stub_fundamentals_for_testing(self) -> Dict[str, Any]:
        """
        Stub fundamentals for Phase 1 testing.

        TODO Phase 2: Remove when fundamentals.load capability implemented.

        Returns:
            Dict with stub fundamental data
        """
        return {
            "payout_ratio_5y_avg": Decimal("0.20"),
            "fcf_dividend_coverage": Decimal("2.5"),
            "dividend_growth_streak_years": 8,
            "net_cash_position": Decimal("5000000000"),  # $5B
            "roe_5y_avg": Decimal("0.18"),
            "gross_margin_5y_avg": Decimal("0.45"),
            "intangible_assets_ratio": Decimal("0.25"),
            "switching_cost_score": Decimal("7"),
            "debt_equity_ratio": Decimal("0.80"),
            "interest_coverage": Decimal("8.0"),
            "current_ratio": Decimal("1.8"),
            "operating_margin_std_dev": Decimal("0.03"),
        }

    async def ratings_aggregate(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        security_id: Optional[str] = None,
        fundamentals: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate aggregate quality score from all three ratings.

        Capability: ratings.aggregate

        Combines dividend safety, moat strength, and resilience into overall score.
        """
        logger.info(f"ratings.aggregate: security_id={security_id}")

        # Call all three rating methods
        dividend = await self.ratings_dividend_safety(ctx, state, security_id, fundamentals)
        moat = await self.ratings_moat_strength(ctx, state, security_id, fundamentals)
        resilience_rating = await self.ratings_resilience(ctx, state, security_id, fundamentals)

        # Aggregate with equal weights (Phase 1)
        # TODO Phase 2: Load weights from rating_rubrics table
        aggregate_score = (
            dividend["overall_score"] * 0.33 +
            moat["overall_score"] * 0.33 +
            resilience_rating["overall_score"] * 0.34
        )

        result = {
            "aggregate_score": aggregate_score,
            "dividend_safety": dividend["overall_score"],
            "moat_strength": moat["overall_score"],
            "resilience": resilience_rating["overall_score"],
            "rating_breakdown": {
                "dividend": dividend,
                "moat": moat,
                "resilience": resilience_rating,
            },
            "note": "Aggregate uses equal weights (Phase 1) - Phase 2 will load from rubric"
        }

        metadata = self._create_metadata(
            source=f"ratings_aggregate:{security_id}",
            asof=ctx.asof_date,
            ttl=86400
        )

        return self._attach_metadata(result, metadata)
