"""
Pack Health Endpoint

Purpose: Expose pricing pack health status for monitoring and UI
Updated: 2025-10-22
Priority: P0 (Critical for Phase 2)

Endpoints:
    GET /health/pack - Get pricing pack health status

Critical Requirements:
    - Returns real pack status from database
    - Status = "warming" when is_fresh = false
    - Status = "fresh" when is_fresh = true
    - Status = "error" when reconciliation failed
    - Includes estimated_ready time when warming

Usage:
    # Check if pack is fresh before calling executor
    response = requests.get("/health/pack")
    if response.json()["is_fresh"]:
        # Safe to call /v1/execute
        pass
    else:
        # Wait until estimated_ready time
        pass
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.core.types import PackHealth, PackStatus
from backend.app.db.pricing_pack_queries import get_pricing_pack_queries

logger = logging.getLogger("DawsOS.Health")

# Initialize FastAPI app
app = FastAPI(
    title="DawsOS Health API",
    version="1.0.0",
    description="Health check endpoints for monitoring",
)


# ============================================================================
# Pydantic Models
# ============================================================================


class PackHealthResponse(BaseModel):
    """Response model for /health/pack endpoint."""

    status: str = Field(..., description="Pack status (warming/fresh/error/stale)")
    pack_id: str = Field(..., description="Pricing pack ID")
    asof_date: str = Field(..., description="Pack as-of date (ISO format)")
    is_fresh: bool = Field(..., description="Whether pack is fresh (ready for use)")
    prewarm_done: bool = Field(..., description="Whether pre-warm completed")
    reconciliation_passed: bool = Field(..., description="Whether reconciliation passed")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")
    error_message: Optional[str] = Field(default=None, description="Error message if status=error")
    estimated_ready: Optional[str] = Field(
        default=None,
        description="Estimated time when pack will be fresh (ISO format)",
    )


# ============================================================================
# Health Endpoints
# ============================================================================


@app.get(
    "/health/pack",
    response_model=PackHealthResponse,
    responses={
        200: {"description": "Pack health status"},
        503: {"description": "No pack found or pack error"},
    },
)
async def pack_health() -> PackHealthResponse:
    """
    Get pricing pack health status.

    Returns pack status for monitoring and UI display.
    UI can use this to show "Data warming" banner when is_fresh=false.

    Returns:
        PackHealthResponse with status details

    Raises:
        HTTPException 503: No pack found or pack in error state
    """
    try:
        logger.info("Pack health check requested")

        # Get pack health from database
        pack_queries = get_pricing_pack_queries()
        health = await pack_queries.get_pack_health()

        if not health:
            logger.error("No pricing pack found")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "error",
                    "error": "no_pack_found",
                    "message": "No pricing pack found. Nightly job may not have run yet.",
                },
            )

        # Log status
        logger.info(
            f"Pack health: status={health.status.value}, pack_id={health.pack_id}, "
            f"is_fresh={health.is_fresh}, prewarm_done={health.prewarm_done}"
        )

        # Return health status
        return PackHealthResponse(
            status=health.status.value,
            pack_id=health.pack_id,
            asof_date=str(health.asof_date),
            is_fresh=health.is_fresh,
            prewarm_done=health.prewarm_done,
            reconciliation_passed=health.reconciliation_passed,
            updated_at=health.updated_at.isoformat(),
            error_message=health.error_message,
            estimated_ready=health.estimated_ready.isoformat() if health.estimated_ready else None,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.exception(f"Pack health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error": "internal_error",
                "message": "Failed to retrieve pack health status.",
            },
        )


@app.get("/health")
async def basic_health_check():
    """
    Basic health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "DawsOS API",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with pack status.

    Returns:
        Detailed health status including pack health
    """
    try:
        # Get pack health
        pack_queries = get_pricing_pack_queries()
        pack_health = await pack_queries.get_pack_health()

        return {
            "status": "healthy",
            "service": "DawsOS API",
            "timestamp": datetime.now().isoformat(),
            "pack_status": pack_health.to_dict() if pack_health else None,
        }

    except Exception as e:
        logger.exception(f"Detailed health check failed: {e}")
        return {
            "status": "degraded",
            "service": "DawsOS API",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
