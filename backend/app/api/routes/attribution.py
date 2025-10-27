"""
DawsOS Attribution API Routes

Purpose: REST API endpoints for currency attribution
Updated: 2025-10-22
Priority: P0 (Phase 4 Task 1)

Endpoints:
    GET /api/v1/portfolios/{portfolio_id}/attribution/currency

Usage:
    curl "http://localhost:8000/api/v1/portfolios/123.../attribution/currency?asof_date=2025-10-22"
"""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Path

from backend.app.api.schemas.attribution import AttributionResponse
from backend.jobs.currency_attribution import CurrencyAttribution

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/portfolios",
    tags=["attribution"],
)


@router.get(
    "/{portfolio_id}/attribution/currency",
    response_model=AttributionResponse,
    summary="Get currency attribution",
    description="Compute currency attribution (local/FX/interaction) for a portfolio",
)
async def get_currency_attribution(
    portfolio_id: UUID = Path(..., description="Portfolio UUID"),
    asof_date: Optional[date] = Query(
        default_factory=date.today,
        description="As-of date for attribution (defaults to today)"
    ),
    base_currency: str = Query(
        default="CAD",
        description="Base currency for attribution"
    ),
) -> AttributionResponse:
    """
    Get currency attribution for portfolio.

    Computes currency attribution breakdown:
    - local_return: Return in local currency
    - fx_return: FX contribution
    - interaction_return: Cross-term (r_local × r_fx)
    - total_return: Total in base currency

    Mathematical identity: r_base = (1 + r_local)(1 + r_fx) - 1

    Args:
        portfolio_id: Portfolio UUID
        asof_date: As-of date for attribution
        base_currency: Base currency (default: CAD)

    Returns:
        AttributionResponse with decomposition

    Raises:
        HTTPException 400: Invalid input
        HTTPException 404: Portfolio not found
        HTTPException 500: Computation error
    """
    try:
        # Create currency attribution service
        attr_service = CurrencyAttribution(base_currency=base_currency)

        # Compute attribution
        # Note: This requires pricing pack ID - we'll need to fetch latest pack
        from backend.app.db.pricing_pack_queries import get_pricing_pack_queries

        pack_queries = get_pricing_pack_queries()
        latest_pack = await pack_queries.get_latest_pack()

        if not latest_pack:
            raise HTTPException(
                status_code=500,
                detail="No pricing pack available"
            )

        # Compute portfolio attribution
        # Note: This is a synchronous method, but we're in async context
        # For now, we'll call it directly. In production, consider using
        # run_in_executor for truly async execution.
        attribution = attr_service.compute_portfolio_attribution(
            portfolio_id=str(portfolio_id),
            asof_date=asof_date,
        )

        # Convert to response model
        return AttributionResponse.from_attribution(
            attribution,
            portfolio_id=portfolio_id,
            asof_date=asof_date,
            pricing_pack_id=latest_pack.id,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in currency attribution: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Error computing currency attribution for {portfolio_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error computing attribution"
        )


__all__ = ["router"]
