"""
Executor API - Main Entry Point for Pattern Execution

Purpose: Execute patterns with freshness gate, context construction, error handling
Updated: 2025-10-22
Priority: P0 (Critical for Phase 2)

Endpoints:
    POST /v1/execute - Execute pattern with freshness gate

Critical Requirements:
    - BLOCKS execution when pack.is_fresh = false (returns 503)
    - Constructs RequestCtx with pricing_pack_id + ledger_commit_hash
    - All results traceable to pack + ledger for reproducibility
    - Proper error handling (4xx for client errors, 5xx for server errors)

Freshness Gate:
    - If require_fresh=true AND pack.is_fresh=false → 503 Service Unavailable
    - Returns estimated_ready time for client retry
    - Allows override with require_fresh=false for development

Architecture:
    UI → Executor API → Pattern Orchestrator → Agent Runtime → Agents → Services
"""

import logging
import uuid
from contextlib import nullcontext
from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.core.types import (
    RequestCtx,
    ExecReq,
    ExecResp,
    ExecError,
    ErrorCode,
    PackStatus,
)
from backend.app.db.pricing_pack_queries import get_pricing_pack_queries
from backend.app.core.pattern_orchestrator import PatternOrchestrator
from backend.app.core.agent_runtime import AgentRuntime
from backend.app.agents.financial_analyst import FinancialAnalyst
from backend.observability import setup_observability
from backend.observability.tracing import trace_context, add_context_attributes, add_pattern_attributes
from backend.observability.metrics import setup_metrics, get_metrics
from backend.observability.errors import capture_exception

logger = logging.getLogger("DawsOS.Executor")

# ============================================================================
# Runtime Initialization (Singleton)
# ============================================================================

_agent_runtime = None
_pattern_orchestrator = None


def get_agent_runtime() -> AgentRuntime:
    """Get or create singleton agent runtime."""
    global _agent_runtime
    if _agent_runtime is None:
        # Initialize services dict (stub for now)
        services = {
            "db": None,  # TODO: Wire real DB
            "redis": None,  # TODO: Wire real Redis
        }

        # Create runtime
        _agent_runtime = AgentRuntime(services)

        # Register agents
        financial_analyst = FinancialAnalyst("financial_analyst", services)
        _agent_runtime.register_agent(financial_analyst)

        logger.info("Agent runtime initialized with financial_analyst")

    return _agent_runtime


def get_pattern_orchestrator() -> PatternOrchestrator:
    """Get or create singleton pattern orchestrator."""
    global _pattern_orchestrator
    if _pattern_orchestrator is None:
        runtime = get_agent_runtime()
        _pattern_orchestrator = PatternOrchestrator(
            agent_runtime=runtime,
            db=None,  # TODO: Wire real DB
            redis=None,  # TODO: Wire real Redis
        )
        logger.info("Pattern orchestrator initialized")

    return _pattern_orchestrator


logger = logging.getLogger("DawsOS.Executor")

# Initialize FastAPI app
app = FastAPI(
    title="DawsOS Executor API",
    version="1.0.0",
    description="Pattern execution API with freshness gate",
)

# ============================================================================
# Observability Setup
# ============================================================================

# Initialize metrics (always enabled)
setup_metrics(service_name="dawsos_executor")

# Setup observability (tracing/errors optional, based on config)
# TODO: Load from environment variables
# setup_observability(
#     service_name="dawsos-executor",
#     environment="development",
#     jaeger_endpoint=os.getenv("JAEGER_ENDPOINT"),
#     sentry_dsn=os.getenv("SENTRY_DSN"),
# )


# ============================================================================
# Pydantic Models (for FastAPI request/response validation)
# ============================================================================


class ExecuteRequest(BaseModel):
    """Request model for /v1/execute endpoint."""

    pattern_id: str = Field(..., description="Pattern ID to execute")
    inputs: dict = Field(default_factory=dict, description="Pattern inputs")
    require_fresh: bool = Field(
        default=True,
        description="Block execution if pack not fresh (default: true)",
    )
    asof_date: Optional[str] = Field(
        default=None,
        description="As-of date override (ISO format: YYYY-MM-DD)",
    )
    portfolio_id: Optional[str] = Field(default=None, description="Portfolio filter")
    security_id: Optional[str] = Field(default=None, description="Security filter")


class ExecuteResponse(BaseModel):
    """Response model for /v1/execute endpoint."""

    result: dict
    metadata: dict
    warnings: list[str] = Field(default_factory=list)
    trace_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str
    details: dict = Field(default_factory=dict)
    request_id: Optional[str] = None
    timestamp: str


# ============================================================================
# Dependencies
# ============================================================================


async def get_current_user():
    """
    Get current user from authentication.

    TODO: Implement actual authentication (JWT, OAuth, etc.)

    Returns:
        User object with valid UUID

    Note:
        Stub returns fixed UUID for development. In production, this should
        return the authenticated user's UUID from JWT token or session.
    """
    # Stub: Return mock user with valid UUID
    return {
        "id": "00000000-0000-0000-0000-000000000001",  # Valid UUID format
        "email": "dev@example.com"
    }


# ============================================================================
# Metrics Endpoint
# ============================================================================


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.
    """
    from backend.observability.metrics import generate_metrics, METRICS_CONTENT_TYPE
    from fastapi import Response

    return Response(content=generate_metrics(), media_type=METRICS_CONTENT_TYPE)


# ============================================================================
# Executor API Endpoint
# ============================================================================


@app.post(
    "/v1/execute",
    response_model=ExecuteResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Pricing pack warming"},
        404: {"model": ErrorResponse, "description": "Pattern not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def execute(
    req: ExecuteRequest,
    user: dict = Depends(get_current_user),
) -> ExecuteResponse:
    """
    Execute pattern with freshness gate.

    Sacred Flow:
        1. Get latest pricing pack
        2. Check freshness gate (CRITICAL: block if warming)
        3. Construct RequestCtx (immutable context)
        4. Execute pattern via orchestrator
        5. Return result with metadata (pack ID, ledger hash, timing)

    Args:
        req: Execute request
        user: Current user (from authentication)

    Returns:
        ExecuteResponse with result and metadata

    Raises:
        HTTPException 503: Pricing pack warming (try again later)
        HTTPException 404: Pattern not found
        HTTPException 500: Internal server error
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now()

    # Get metrics registry
    metrics_registry = get_metrics()

    # Start tracing and metrics
    with trace_context(
        "execute_pattern",
        pattern_id=req.pattern_id,
        request_id=request_id,
    ) as span:
        try:
            with metrics_registry.time_request(req.pattern_id) if metrics_registry else nullcontext():
                logger.info(f"Execute request: pattern={req.pattern_id}, user={user['id']}, request_id={request_id}")

                # Add pattern attributes to span
                add_pattern_attributes(span, req.pattern_id, req.inputs)

                return await _execute_pattern_internal(req, user, request_id, started_at, span, metrics_registry)

        except HTTPException:
            # Re-raise HTTP exceptions (already formatted)
            raise

        except Exception as e:
            # Capture unexpected errors
            logger.exception(f"Unexpected error in execute: {e}")

            # Capture in Sentry with context
            capture_exception(
                e,
                context={
                    "pattern_id": req.pattern_id,
                    "request_id": request_id,
                },
                tags={
                    "component": "executor",
                    "pattern_id": req.pattern_id,
                },
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ExecError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=f"Internal server error: {str(e)}",
                    request_id=request_id,
                ).to_dict(),
            )


async def _execute_pattern_internal(
    req: ExecuteRequest,
    user: dict,
    request_id: str,
    started_at: datetime,
    span,
    metrics_registry,
) -> ExecuteResponse:
    """Internal implementation of pattern execution (separated for instrumentation)."""
    try:

        # ========================================
        # STEP 1: Get Latest Pricing Pack
        # ========================================

        pack_queries = get_pricing_pack_queries()
        pack = await pack_queries.get_latest_pack()

        if not pack:
            logger.error("No pricing pack found")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ExecError(
                    code=ErrorCode.PACK_NOT_FOUND,
                    message="No pricing pack found. Nightly job may not have run yet.",
                    request_id=request_id,
                ).to_dict(),
            )

        # ========================================
        # STEP 2: Freshness Gate (CRITICAL)
        # ========================================

        if req.require_fresh and not pack["is_fresh"]:
            logger.warning(
                f"Freshness gate BLOCKED: pack={pack['id']}, is_fresh={pack['is_fresh']}, "
                f"prewarm_done={pack['prewarm_done']}"
            )

            # Calculate estimated ready time
            # Assume 15 minutes for full pre-warm
            from datetime import timedelta

            estimated_ready = pack["updated_at"] + timedelta(minutes=15)

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ExecError(
                    code=ErrorCode.PACK_WARMING,
                    message="Pricing pack warming in progress. Try again in a few minutes.",
                    details={
                        "pack_id": pack["id"],
                        "status": pack["status"],
                        "prewarm_done": pack["prewarm_done"],
                        "estimated_ready": estimated_ready.isoformat(),
                    },
                    request_id=request_id,
                ).to_dict(),
            )

        # Check for reconciliation failure
        if pack["reconciliation_failed"]:
            logger.error(f"Reconciliation failed for pack: {pack['id']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ExecError(
                    code=ErrorCode.PACK_ERROR,
                    message="Pricing pack reconciliation failed. Manual intervention required.",
                    details={
                        "pack_id": pack["id"],
                        "error": "Ledger reconciliation failed (±1bp threshold exceeded)",
                    },
                    request_id=request_id,
                ).to_dict(),
            )

        logger.info(f"Freshness gate PASSED: pack={pack['id']}, is_fresh={pack['is_fresh']}")

        # ========================================
        # STEP 3: Construct RequestCtx
        # ========================================

        # Get ledger commit hash
        ledger_commit_hash = await pack_queries.get_ledger_commit_hash()

        # Parse asof_date (if provided)
        asof_date = pack["date"]
        if req.asof_date:
            try:
                asof_date = date.fromisoformat(req.asof_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ExecError(
                        code=ErrorCode.PATTERN_INVALID,
                        message=f"Invalid asof_date format: {req.asof_date}. Use ISO format (YYYY-MM-DD).",
                        request_id=request_id,
                    ).to_dict(),
                )

        # Build context (immutable)
        from uuid import UUID
        ctx = RequestCtx(
            user_id=UUID(user["id"]) if isinstance(user["id"], str) else user["id"],
            pricing_pack_id=pack["id"],
            ledger_commit_hash=ledger_commit_hash,
            trace_id=request_id,  # Use request_id as trace_id
            request_id=request_id,
            timestamp=started_at,
            asof_date=asof_date,
            require_fresh=req.require_fresh,
            portfolio_id=UUID(req.portfolio_id) if req.portfolio_id else None,
        )

        logger.info(f"RequestCtx constructed: {ctx.to_dict()}")

        # Add context attributes to span
        add_context_attributes(span, ctx)

        # ========================================
        # STEP 3.5: Set RLS Context (Security)
        # ========================================

        # TODO: Set RLS context for database queries executed during pattern execution
        #
        # RLS (Row-Level Security) context must be set before executing any user-specific
        # database queries. This ensures multi-tenant data isolation.
        #
        # Implementation approach:
        #   - Patterns/agents that query user data should use get_db_connection_with_rls(ctx.user_id)
        #   - This automatically sets app.user_id for RLS policies
        #   - RLS context is transaction-scoped (auto-resets after transaction)
        #
        # Example in agent code:
        #   from backend.app.db import get_db_connection_with_rls
        #
        #   async with get_db_connection_with_rls(ctx.user_id) as conn:
        #       portfolios = await conn.fetch("SELECT * FROM portfolios WHERE id = $1", portfolio_id)
        #
        # Status: Infrastructure ready (get_db_connection_with_rls implemented)
        #         Agents need to migrate from get_db_connection() to get_db_connection_with_rls()
        #
        # See: backend/app/db/connection.py:164-196

        # Record pack freshness metric
        if metrics_registry:
            metrics_registry.record_pack_freshness(pack["id"], pack["status"])

        # ========================================
        # STEP 4: Execute Pattern via Orchestrator
        # ========================================

        try:
            # Get orchestrator (with agent runtime wired)
            orchestrator = get_pattern_orchestrator()

            # Execute pattern
            logger.info(f"Executing pattern via orchestrator: {req.pattern_id}")
            orchestration_result = await orchestrator.run_pattern(
                pattern_id=req.pattern_id,
                ctx=ctx,
                inputs=req.inputs,
            )

            # Extract data from orchestration result
            result = orchestration_result.get("data", {})
            trace = orchestration_result.get("trace", {})

            logger.info(f"Pattern executed successfully: {req.pattern_id}, trace={trace}")

        except FileNotFoundError:
            logger.error(f"Pattern not found: {req.pattern_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ExecError(
                    code=ErrorCode.PATTERN_NOT_FOUND,
                    message=f"Pattern not found: {req.pattern_id}",
                    request_id=request_id,
                ).to_dict(),
            )

        except ValueError as e:
            logger.exception(f"Pattern execution failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ExecError(
                    code=ErrorCode.PATTERN_EXECUTION_ERROR,
                    message=f"Pattern execution failed: {str(e)}",
                    request_id=request_id,
                ).to_dict(),
            )

        # ========================================
        # STEP 5: Build Response
        # ========================================

        completed_at = datetime.now()
        duration_ms = (completed_at - started_at).total_seconds() * 1000

        metadata = {
            "pricing_pack_id": pack["id"],
            "ledger_commit_hash": ledger_commit_hash,
            "pattern_id": req.pattern_id,
            "asof_date": str(asof_date),
            "duration_ms": round(duration_ms, 2),
            "timestamp": completed_at.isoformat(),
        }

        logger.info(
            f"Execute completed: pattern={req.pattern_id}, duration={duration_ms:.2f}ms, "
            f"request_id={request_id}"
        )

        return ExecuteResponse(
            result=result,
            metadata=metadata,
            warnings=[],
            trace_id=request_id,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (already formatted)
        raise

    except Exception as e:
        # Catch-all for unexpected errors
        logger.exception(f"Execute failed with unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ExecError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error during pattern execution.",
                details={"error": str(e)},
                request_id=request_id,
            ).to_dict(),
        )


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Custom error handler for HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


# ============================================================================
# Health Check
# ============================================================================


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
