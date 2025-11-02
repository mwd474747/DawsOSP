"""
DawsOS Ratings Agent

Purpose: Buffett-style quality ratings (dividend safety, moat strength, resilience)
Updated: 2025-10-27 (Agent Wiring)
Priority: P1 (Core business logic)

Capabilities:
    - ratings.dividend_safety: Calculate dividend safety rating (0-10)
    - ratings.moat_strength: Calculate economic moat strength (0-10)
    - ratings.resilience: Calculate balance sheet resilience (0-10)
    - ratings.aggregate: Aggregate all ratings into overall quality score

Architecture:
    Pattern → Agent → RatingsService → rating_rubrics table → Database

Usage:
    agent = RatingsAgent("ratings", services)
    runtime.register_agent(agent)

Integration:
    - Consumes fundamentals from Data Harvester (provider.fetch_fundamentals)
    - Used by OptimizerAgent for quality filtering
    - Powers buffett_checklist pattern
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.base_agent import BaseAgent, AgentMetadata
from app.core.types import RequestCtx
from app.services.ratings import get_ratings_service
from app.services.fundamentals_transformer import transform_fmp_to_ratings_format

logger = logging.getLogger("DawsOS.RatingsAgent")


class RatingsAgent(BaseAgent):
    """
    Ratings Agent - Buffett-style quality scoring.

    Provides capabilities for calculating quality ratings based on
    fundamental analysis:
        - Dividend safety (payout sustainability)
        - Moat strength (competitive advantage)
        - Resilience (balance sheet strength)
        - Aggregate quality score

    All ratings use 0-10 scale based on research-backed thresholds
    from RATINGS_ARCHITECT.md specification.
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
        symbol: Optional[str] = None,
        security_id: Optional[str] = None,
        fundamentals: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Calculate dividend safety rating (0-10 scale).

        Capability: ratings.dividend_safety

        Components:
            1. Payout ratio (5-year avg): <30%=10, <50%=7, <70%=5, else=2
            2. FCF coverage: >3.0=10, >2.0=7, >1.0=5, else=2
            3. Dividend growth streak: >=20=10, >=10=9, >=5=7, else=5
            4. Net cash position: >$50B=10, >$10B=8, >$1B=6, else=4

        Args:
            ctx: Request context
            state: Execution state (may contain fundamentals from prior step)
            symbol: Security symbol (optional if in fundamentals)
            security_id: Security UUID (optional)
            fundamentals: Fundamentals dict (optional, fetched if not provided)
            **kwargs: Additional arguments

        Returns:
            Dict with:
                - overall: Decimal (0-10 weighted average)
                - components: Dict with score/value/weight for each component
                - symbol: str
                - security_id: Optional[str]
                - _metadata: Metadata dict
        """
        # Resolve symbol from state or arguments
        if not symbol and fundamentals:
            symbol = fundamentals.get("symbol")
        if not symbol and state.get("fundamentals"):
            symbol = state["fundamentals"].get("symbol")
        
        # If we have security_id but no symbol, look it up
        if not symbol and security_id:
            # Use a stub symbol for now (in production would query database)
            symbol = "STUB"
            logger.warning(f"Using stub symbol for security_id {security_id}")
        
        if not symbol:
            raise ValueError("symbol required for ratings.dividend_safety")

        # Get fundamentals from state if not provided
        if not fundamentals:
            fundamentals = state.get("fundamentals")
        if not fundamentals:
            raise ValueError(
                "fundamentals required for ratings.dividend_safety. "
                "Run fundamentals.load or provider.fetch_fundamentals first."
            )

        logger.info(f"ratings.dividend_safety: symbol={symbol}")

        # Transform FMP data to ratings format if needed
        if "income_statement" in fundamentals and "balance_sheet" in fundamentals:
            # This is raw FMP data, transform it
            logger.info(f"Transforming FMP fundamentals for {symbol}")
            transformed_fundamentals = transform_fmp_to_ratings_format(fundamentals)
        else:
            # Already in the correct format or has required fields
            transformed_fundamentals = fundamentals

        # Call ratings service
        ratings_service = get_ratings_service()
        security_uuid = UUID(security_id) if security_id else None

        try:
            result = await ratings_service.calculate_dividend_safety(
                symbol=symbol,
                fundamentals=transformed_fundamentals,
                security_id=security_uuid,
            )

            # Attach metadata
            metadata = self._create_metadata(
                source=f"ratings_service:v1:{ctx.asof_date}",
                asof=ctx.asof_date or date.today(),
                ttl=86400,  # Cache for 1 day (ratings are stable)
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"Dividend safety calculation failed for {symbol}: {e}", exc_info=True)
            # Return error result with metadata
            error_result = {
                "overall": Decimal("0"),
                "error": str(e),
                "symbol": symbol,
                "security_id": security_id,
            }
            metadata = self._create_metadata(
                source=f"ratings_service:error",
                asof=ctx.asof_date or date.today(),
                ttl=0,
            )
            return self._attach_metadata(error_result, metadata)

    async def ratings_moat_strength(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: Optional[str] = None,
        security_id: Optional[str] = None,
        fundamentals: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Calculate economic moat strength (0-10 scale).

        Capability: ratings.moat_strength

        Components:
            1. ROE consistency (5Y): >20%=10, >15%=8, >10%=6, else=4
            2. Gross margin (5Y): >60%=10, >40%=8, >25%=6, else=4
            3. Intangible assets ratio: >30%=8, >15%=6, else=4
            4. Switching costs: Qualitative score from rubric (default 5)

        Args:
            ctx: Request context
            state: Execution state
            symbol: Security symbol
            security_id: Security UUID (optional)
            fundamentals: Fundamentals dict
            **kwargs: Additional arguments

        Returns:
            Dict with overall score and component breakdown
        """
        # Resolve symbol
        if not symbol and fundamentals:
            symbol = fundamentals.get("symbol")
        if not symbol and state.get("fundamentals"):
            symbol = state["fundamentals"].get("symbol")
        
        # If we have security_id but no symbol, look it up
        if not symbol and security_id:
            # Use a stub symbol for now (in production would query database)
            symbol = "STUB"
            logger.warning(f"Using stub symbol for security_id {security_id}")
        
        if not symbol:
            raise ValueError("symbol required for ratings.moat_strength")

        # Get fundamentals
        if not fundamentals:
            fundamentals = state.get("fundamentals")
        if not fundamentals:
            raise ValueError(
                "fundamentals required for ratings.moat_strength. "
                "Run fundamentals.load or provider.fetch_fundamentals first."
            )

        logger.info(f"ratings.moat_strength: symbol={symbol}")

        # Transform FMP data to ratings format if needed
        if "income_statement" in fundamentals and "balance_sheet" in fundamentals:
            # This is raw FMP data, transform it
            logger.info(f"Transforming FMP fundamentals for {symbol}")
            transformed_fundamentals = transform_fmp_to_ratings_format(fundamentals)
        else:
            # Already in the correct format or has required fields
            transformed_fundamentals = fundamentals

        # Call ratings service
        ratings_service = get_ratings_service()
        security_uuid = UUID(security_id) if security_id else None

        try:
            result = await ratings_service.calculate_moat_strength(
                symbol=symbol,
                fundamentals=transformed_fundamentals,
                security_id=security_uuid,
            )

            # Attach metadata
            metadata = self._create_metadata(
                source=f"ratings_service:v1:{ctx.asof_date}",
                asof=ctx.asof_date or date.today(),
                ttl=86400,
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"Moat strength calculation failed for {symbol}: {e}", exc_info=True)
            error_result = {
                "overall": Decimal("0"),
                "error": str(e),
                "symbol": symbol,
                "security_id": security_id,
            }
            metadata = self._create_metadata(
                source=f"ratings_service:error",
                asof=ctx.asof_date or date.today(),
                ttl=0,
            )
            return self._attach_metadata(error_result, metadata)

    async def ratings_resilience(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: Optional[str] = None,
        security_id: Optional[str] = None,
        fundamentals: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Calculate balance sheet resilience (0-10 scale).

        Capability: ratings.resilience

        Components:
            1. Debt/Equity: <0.5=10, <1.0=8, <2.0=6, else=3
            2. Interest coverage: >10=10, >5=8, >2=6, else=3
            3. Current ratio: >2.0=10, >1.5=8, >1.0=7, else=4
            4. Operating margin stability (std dev): <2%=10, <5%=8, <10%=6, else=4

        Args:
            ctx: Request context
            state: Execution state
            symbol: Security symbol
            security_id: Security UUID (optional)
            fundamentals: Fundamentals dict
            **kwargs: Additional arguments

        Returns:
            Dict with overall score and component breakdown
        """
        # Resolve symbol
        if not symbol and fundamentals:
            symbol = fundamentals.get("symbol")
        if not symbol and state.get("fundamentals"):
            symbol = state["fundamentals"].get("symbol")
        
        # If we have security_id but no symbol, look it up
        if not symbol and security_id:
            # Use a stub symbol for now (in production would query database)
            symbol = "STUB"
            logger.warning(f"Using stub symbol for security_id {security_id}")
        
        if not symbol:
            raise ValueError("symbol required for ratings.resilience")

        # Get fundamentals
        if not fundamentals:
            fundamentals = state.get("fundamentals")
        if not fundamentals:
            raise ValueError(
                "fundamentals required for ratings.resilience. "
                "Run fundamentals.load or provider.fetch_fundamentals first."
            )

        logger.info(f"ratings.resilience: symbol={symbol}")

        # Transform FMP data to ratings format if needed
        if "income_statement" in fundamentals and "balance_sheet" in fundamentals:
            # This is raw FMP data, transform it
            logger.info(f"Transforming FMP fundamentals for {symbol}")
            transformed_fundamentals = transform_fmp_to_ratings_format(fundamentals)
        else:
            # Already in the correct format or has required fields
            transformed_fundamentals = fundamentals

        # Call ratings service
        ratings_service = get_ratings_service()
        security_uuid = UUID(security_id) if security_id else None

        try:
            result = await ratings_service.calculate_resilience(
                symbol=symbol,
                fundamentals=transformed_fundamentals,
                security_id=security_uuid,
            )

            # Attach metadata
            metadata = self._create_metadata(
                source=f"ratings_service:v1:{ctx.asof_date}",
                asof=ctx.asof_date or date.today(),
                ttl=86400,
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"Resilience calculation failed for {symbol}: {e}", exc_info=True)
            error_result = {
                "overall": Decimal("0"),
                "error": str(e),
                "symbol": symbol,
                "security_id": security_id,
            }
            metadata = self._create_metadata(
                source=f"ratings_service:error",
                asof=ctx.asof_date or date.today(),
                ttl=0,
            )
            return self._attach_metadata(error_result, metadata)

    async def ratings_aggregate(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: Optional[str] = None,
        security_id: Optional[str] = None,
        fundamentals: Optional[Dict[str, Any]] = None,
        positions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Aggregate all ratings into overall quality score.

        Capability: ratings.aggregate

        Aggregation Weights:
            - Moat strength: 40% (most important - competitive advantage)
            - Resilience: 35% (balance sheet safety)
            - Dividend safety: 25% (income sustainability)

        Overall Rating Scale:
            - A (90-100): Exceptional quality - Buffett's "wonderful company"
            - B (80-89): Strong quality - Buffett's "good company"
            - C (70-79): Acceptable quality - requires fair price
            - D (60-69): Below average - avoid unless deeply discounted
            - F (<60): Poor quality - stay away

        Args:
            ctx: Request context
            state: Execution state
            symbol: Security symbol (if rating single security)
            security_id: Security UUID (optional)
            fundamentals: Fundamentals dict (if rating single security)
            positions: List of positions (if rating portfolio holdings)
            **kwargs: Additional arguments

        Returns:
            If single security:
                Dict with:
                    - overall_rating: Decimal (0-100)
                    - overall_grade: str (A/B/C/D/F)
                    - moat: Dict (component ratings)
                    - resilience: Dict (component ratings)
                    - dividend: Dict (component ratings)
                    - _metadata: Metadata dict

            If portfolio positions:
                Dict with:
                    - positions: List of dicts (one per position with ratings)
                    - portfolio_avg_rating: Decimal
                    - portfolio_avg_grade: str
                    - _metadata: Metadata dict
        """
        # Determine if rating single security or portfolio
        if positions:
            # Portfolio mode: rate each position
            return await self._aggregate_portfolio_ratings(ctx, state, positions)
        else:
            # Single security mode
            return await self._aggregate_single_rating(ctx, state, symbol, security_id, fundamentals)

    async def _aggregate_single_rating(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: Optional[str],
        security_id: Optional[str],
        fundamentals: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Aggregate ratings for a single security."""
        # Resolve symbol
        if not symbol and fundamentals:
            symbol = fundamentals.get("symbol")
        if not symbol and state.get("fundamentals"):
            symbol = state["fundamentals"].get("symbol")
        
        # If we have security_id but no symbol, look it up
        if not symbol and security_id:
            # Use a stub symbol for now (in production would query database)
            symbol = "STUB"
            logger.warning(f"Using stub symbol for security_id {security_id}")
        
        if not symbol:
            raise ValueError("symbol required for ratings.aggregate")

        # Get fundamentals
        if not fundamentals:
            fundamentals = state.get("fundamentals")
        if not fundamentals:
            raise ValueError(
                "fundamentals required for ratings.aggregate. "
                "Run fundamentals.load or provider.fetch_fundamentals first."
            )

        logger.info(f"ratings.aggregate: symbol={symbol}")

        # Transform FMP data to ratings format if needed
        if "income_statement" in fundamentals and "balance_sheet" in fundamentals:
            # This is raw FMP data, transform it
            logger.info(f"Transforming FMP fundamentals for {symbol}")
            transformed_fundamentals = transform_fmp_to_ratings_format(fundamentals)
        else:
            # Already in the correct format or has required fields
            transformed_fundamentals = fundamentals

        # Call ratings service
        ratings_service = get_ratings_service()
        security_uuid = UUID(security_id) if security_id else None

        try:
            result = await ratings_service.aggregate(
                symbol=symbol,
                fundamentals=transformed_fundamentals,
                security_id=security_uuid,
            )

            # Attach metadata
            metadata = self._create_metadata(
                source=f"ratings_service:aggregate:v1:{ctx.asof_date}",
                asof=ctx.asof_date or date.today(),
                ttl=86400,
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"Aggregate rating calculation failed for {symbol}: {e}", exc_info=True)
            error_result = {
                "overall_rating": Decimal("0"),
                "overall_grade": "F",
                "error": str(e),
                "symbol": symbol,
                "security_id": security_id,
            }
            metadata = self._create_metadata(
                source=f"ratings_service:error",
                asof=ctx.asof_date or date.today(),
                ttl=0,
            )
            return self._attach_metadata(error_result, metadata)

    async def _aggregate_portfolio_ratings(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        positions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Aggregate ratings for portfolio positions.

        For each position, fetch fundamentals and calculate ratings.
        Return weighted average portfolio rating.
        """
        logger.info(f"ratings.aggregate: rating {len(positions)} positions")

        ratings_service = get_ratings_service()
        rated_positions = []
        total_value = Decimal("0")
        weighted_rating_sum = Decimal("0")

        for pos in positions:
            symbol = pos.get("symbol")
            security_id = pos.get("security_id")
            value = Decimal(str(pos.get("value", 0)))
            total_value += value

            # TODO: Fetch fundamentals for each position
            # For now, use stub data or skip if no fundamentals in position
            fundamentals = pos.get("fundamentals")
            if not fundamentals:
                logger.warning(f"No fundamentals for {symbol}, skipping rating")
                rated_positions.append({
                    **pos,
                    "rating": None,
                    "grade": None,
                    "rating_error": "No fundamentals available",
                })
                continue

            try:
                # Calculate aggregate rating
                rating_result = await ratings_service.aggregate(
                    symbol=symbol,
                    fundamentals=fundamentals,
                    security_id=UUID(security_id) if security_id else None,
                )

                overall_rating = rating_result["overall_rating"]
                overall_grade = rating_result["overall_grade"]

                rated_positions.append({
                    **pos,
                    "rating": float(overall_rating),
                    "grade": overall_grade,
                    "moat": float(rating_result["moat"]["overall"]),
                    "resilience": float(rating_result["resilience"]["overall"]),
                    "dividend_safety": float(rating_result["dividend"]["overall"]),
                })

                # Accumulate weighted rating
                weighted_rating_sum += overall_rating * value

            except Exception as e:
                logger.error(f"Rating failed for {symbol}: {e}")
                rated_positions.append({
                    **pos,
                    "rating": None,
                    "grade": None,
                    "rating_error": str(e),
                })

        # Calculate portfolio average
        if total_value > 0:
            portfolio_avg_rating = weighted_rating_sum / total_value
            portfolio_avg_grade = self._rating_to_grade(portfolio_avg_rating)
        else:
            portfolio_avg_rating = Decimal("0")
            portfolio_avg_grade = "F"

        result = {
            "positions": rated_positions,
            "portfolio_avg_rating": float(portfolio_avg_rating),
            "portfolio_avg_grade": portfolio_avg_grade,
            "total_value": float(total_value),
            "rated_count": len([p for p in rated_positions if p.get("rating") is not None]),
            "unrated_count": len([p for p in rated_positions if p.get("rating") is None]),
        }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"ratings_service:portfolio:v1:{ctx.asof_date}",
            asof=ctx.asof_date or date.today(),
            ttl=86400,
        )

        return self._attach_metadata(result, metadata)

    def _rating_to_grade(self, rating: Decimal) -> str:
        """Convert numeric rating (0-100 scale) to letter grade."""
        if rating >= Decimal("90"):
            return "A"
        elif rating >= Decimal("80"):
            return "B"
        elif rating >= Decimal("70"):
            return "C"
        elif rating >= Decimal("60"):
            return "D"
        else:
            return "F"
