"""
DawsOS Metrics API Routes

Purpose: REST API endpoints for portfolio metrics retrieval
Updated: 2025-10-22
Priority: P0 (Phase 4 Task 1)

Endpoints:
    GET /api/v1/portfolios/{portfolio_id}/metrics
    GET /api/v1/portfolios/{portfolio_id}/metrics/history

Usage:
    curl http://localhost:8000/api/v1/portfolios/123e4567-e89b-12d3-a456-426614174000/metrics
    curl "http://localhost:8000/api/v1/portfolios/123.../metrics/history?start_date=2025-01-01&end_date=2025-10-22"
"""

import logging
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import ValidationError

from app.api.schemas.metrics import MetricsResponse, MetricsHistoryResponse
from app.db.metrics_queries import get_metrics_queries

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/portfolios",
    tags=["metrics"],
)


@router.get(
    "/{portfolio_id}/metrics",
    response_model=MetricsResponse,
    summary="Get latest portfolio metrics",
    description="Retrieve the most recent metrics for a portfolio as of a specific date",
)
async def get_portfolio_metrics(
    portfolio_id: UUID = Path(..., description="Portfolio UUID"),
    asof_date: Optional[date] = Query(
        default=None,
        description="As-of date for metrics (defaults to latest available)"
    ),
) -> MetricsResponse:
    """
    Get latest portfolio metrics.

    Returns metrics from the portfolio_metrics table. If asof_date is not provided,
    returns the most recent metrics available.

    Args:
        portfolio_id: Portfolio UUID
        asof_date: Optional as-of date (defaults to latest)

    Returns:
        MetricsResponse with all computed metrics

    Raises:
        HTTPException 404: Metrics not found for portfolio
        HTTPException 500: Database error
    """
    try:
        # Get queries singleton
        queries = get_metrics_queries()

        # Fetch metrics from database
        if asof_date:
            metrics = await queries.get_latest_metrics(portfolio_id, asof_date)
        else:
            # Get absolute latest
            metrics = await queries.get_latest_metrics_any_date(portfolio_id)

        if not metrics:
            raise HTTPException(
                status_code=404,
                detail=f"Metrics not found for portfolio {portfolio_id}"
                + (f" on {asof_date}" if asof_date else "")
            )

        # Convert to response model
        return MetricsResponse.from_orm(metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metrics for {portfolio_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error fetching metrics"
        )


@router.get(
    "/{portfolio_id}/metrics/history",
    response_model=MetricsHistoryResponse,
    summary="Get historical metrics",
    description="Retrieve metrics history for a portfolio over a date range",
)
async def get_metrics_history(
    portfolio_id: UUID = Path(..., description="Portfolio UUID"),
    start_date: date = Query(..., description="Start date (inclusive)"),
    end_date: date = Query(..., description="End date (inclusive)"),
) -> MetricsHistoryResponse:
    """
    Get historical portfolio metrics.

    Returns all metrics for a portfolio within the specified date range.

    Args:
        portfolio_id: Portfolio UUID
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        MetricsHistoryResponse with list of metrics

    Raises:
        HTTPException 400: Invalid date range
        HTTPException 500: Database error
    """
    try:
        # Validate date range
        if end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail=f"end_date ({end_date}) must be >= start_date ({start_date})"
            )

        # Get queries singleton
        queries = get_metrics_queries()

        # Fetch metrics history
        metrics_list = await queries.get_metrics_history(
            portfolio_id, start_date, end_date
        )

        # Convert to response models
        metrics_responses = [MetricsResponse.from_orm(m) for m in metrics_list]

        return MetricsHistoryResponse(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics_responses,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching metrics history for {portfolio_id} "
            f"({start_date} to {end_date}): {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error fetching metrics history"
        )


__all__ = ["router"]
