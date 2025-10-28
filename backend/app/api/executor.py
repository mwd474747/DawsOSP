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
import asyncio
from contextlib import nullcontext, asynccontextmanager
from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.types import (
    RequestCtx,
    ExecReq,
    ExecResp,
    ExecError,
    ErrorCode,
    PackStatus,
)
from app.db.pricing_pack_queries import get_pricing_pack_queries
from app.core.pattern_orchestrator import PatternOrchestrator
from app.core.agent_runtime import AgentRuntime
from app.agents.financial_analyst import FinancialAnalyst
from app.middleware.auth_middleware import verify_token
from app.services.audit import get_audit_service
from observability import setup_observability
from observability.tracing import trace_context, add_context_attributes, add_pattern_attributes
from observability.metrics import setup_metrics, get_metrics
from observability.errors import capture_exception

logger = logging.getLogger("DawsOS.Executor")

# ============================================================================
# Runtime Initialization (Singleton)
# ============================================================================

_agent_runtime = None
_pattern_orchestrator = None


def get_agent_runtime(reinit_services: bool = False) -> AgentRuntime:
    """
    Get or create singleton agent runtime.

    Args:
        reinit_services: If True, reinitialize services dict with current pool (for startup)
    """
    global _agent_runtime

    # Get current database pool (may be None if not initialized yet)
    from app.db.connection import get_db_pool

    try:
        db_pool = get_db_pool()
        logger.debug("✅ Retrieved database pool for agent runtime")
    except RuntimeError:
        logger.debug("⚠️ Database pool not initialized yet")
        db_pool = None

    services = {
        "db": db_pool,
        "redis": None,  # TODO: Wire real Redis when needed
    }

    # If runtime exists and reinit_services=True, update the services dict
    if _agent_runtime is not None and reinit_services:
        logger.info("Updating agent runtime with initialized database pool")
        _agent_runtime.services = services
        # Also update services on each registered agent
        for agent_id, agent in _agent_runtime.agents.items():
            agent.services = services
        return _agent_runtime

    if _agent_runtime is None:
        # Create runtime
        _agent_runtime = AgentRuntime(services)

        # Register agents (6 total - all agents registered)
        # ✅ COMPLETE (2025-10-27): All agents registered (financial, macro, harvester, claude, ratings, optimizer)

        # 1. Financial Analyst - Portfolio analysis, metrics, pricing
        financial_analyst = FinancialAnalyst("financial_analyst", services)
        _agent_runtime.register_agent(financial_analyst)

        # 2. Macro Hound - Macro regime, cycles, scenarios, DaR
        from app.agents.macro_hound import MacroHound
        macro_hound = MacroHound("macro_hound", services)
        _agent_runtime.register_agent(macro_hound)

        # 3. Data Harvester - Provider integration (FMP, Polygon, FRED, NewsAPI)
        from app.agents.data_harvester import DataHarvester
        data_harvester = DataHarvester("data_harvester", services)
        _agent_runtime.register_agent(data_harvester)

        # 4. Claude Agent - AI explanations and analysis
        from app.agents.claude_agent import ClaudeAgent
        claude_agent = ClaudeAgent("claude", services)
        _agent_runtime.register_agent(claude_agent)

        # 5. Ratings Agent - Buffett-style quality ratings
        from app.agents.ratings_agent import RatingsAgent
        ratings_agent = RatingsAgent("ratings", services)
        _agent_runtime.register_agent(ratings_agent)

        # 6. Optimizer Agent - Portfolio optimization and rebalancing
        from app.agents.optimizer_agent import OptimizerAgent
        optimizer_agent = OptimizerAgent("optimizer", services)
        _agent_runtime.register_agent(optimizer_agent)

        # 7. Reports Agent - PDF/CSV export generation
        from app.agents.reports_agent import ReportsAgent
        reports_agent = ReportsAgent("reports", services)
        _agent_runtime.register_agent(reports_agent)

        # 8. Alerts Agent - Alert suggestions and threshold-based creation
        from app.agents.alerts_agent import AlertsAgent
        alerts_agent = AlertsAgent("alerts", services)
        _agent_runtime.register_agent(alerts_agent)

        # 9. Charts Agent - Chart formatting and visualization specs
        from app.agents.charts_agent import ChartsAgent
        charts_agent = ChartsAgent("charts", services)
        _agent_runtime.register_agent(charts_agent)

        logger.info(
            "Agent runtime initialized with 9 agents: "
            "financial_analyst, macro_hound, data_harvester, claude, ratings, optimizer, reports, alerts, charts"
        )

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
    description="Pattern execution API with JWT authentication and freshness gate",
)

# Include auth routes
from app.api.routes.auth import router as auth_router
app.include_router(auth_router)
logger.info("✅ Auth routes registered at /auth")

print("=" * 80)
print("FASTAPI APP CREATED - Setting up DB middleware")
print("=" * 80)


# ============================================================================
# Database Initialization Middleware
# ============================================================================

_db_initialized = False
_init_lock = asyncio.Lock()


class DBInitMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure DB pool is initialized before handling requests."""

    async def dispatch(self, request, call_next):
        global _db_initialized

        if not _db_initialized:
            async with _init_lock:
                if not _db_initialized:
                    from app.db.connection import init_db_pool
                    import os

                    logger.info("🔄 Initializing database pool (first request)...")
                    print("=" * 80)
                    print("🔄 INITIALIZING DATABASE POOL ON FIRST REQUEST")
                    print("=" * 80)

                    database_url = os.getenv("DATABASE_URL")

                    try:
                        await init_db_pool(database_url)
                        logger.info("✅ Database pool initialized successfully")
                        print("=" * 80)
                        print("✅ DATABASE POOL INITIALIZED")
                        print("=" * 80)

                        # Update agent runtime with initialized pool
                        get_agent_runtime(reinit_services=True)
                        logger.info("✅ Agent runtime updated with database pool")

                        _db_initialized = True
                    except Exception as e:
                        logger.error(f"❌ Failed to initialize database pool: {e}")
                        print(f"❌ DATABASE POOL INITIALIZATION FAILED: {e}")
                        raise

        response = await call_next(request)
        return response


# Add middleware to app
app.add_middleware(DBInitMiddleware)

print("✅ DB Init Middleware registered")


# ============================================================================
# Startup/Shutdown Events (keeping for compatibility)
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database pool and other resources on startup."""
    from app.db.connection import init_db_pool
    import os

    print("=" * 80)
    print("STARTUP EVENT - Initializing database pool")
    print("=" * 80)

    database_url = os.getenv("DATABASE_URL")
    logger.info(f"Initializing database connection pool... URL={database_url}")

    try:
        await init_db_pool(database_url)
        logger.info("✅ Database connection pool initialized successfully")
        print("✅ DATABASE POOL INITIALIZED")

        # Update agent runtime with initialized pool
        get_agent_runtime(reinit_services=True)
        logger.info("✅ Agent runtime updated with database pool")

        # GOVERNANCE FIX #1: Force pricing service to use database for freshness gate
        from app.services.pricing import init_pricing_service
        init_pricing_service(use_db=True, force=True)
        logger.info("✅ Pricing service initialized with database (freshness gate enabled)")

    except Exception as e:
        logger.error(f"❌ Failed to initialize database pool: {e}", exc_info=True)
        print(f"❌ DATABASE POOL INITIALIZATION FAILED: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close database pool and other resources on shutdown."""
    from app.db.connection import close_db_pool

    logger.info("Closing database connection pool...")
    print("SHUTDOWN EVENT - Closing database pool")

    try:
        await close_db_pool()
        logger.info("Database connection pool closed successfully")
    except Exception as e:
        logger.error(f"Error closing database pool: {e}", exc_info=True)


# ============================================================================
# Observability Setup
# ============================================================================

# Initialize metrics (always enabled)
setup_metrics(service_name="dawsos_executor")

# Setup observability (tracing/errors optional, based on config)
# ✅ ENABLED (2025-10-23): Load from environment variables
import os

# Only enable if explicitly configured (opt-in for production)
if os.getenv("ENABLE_OBSERVABILITY", "false").lower() == "true":
    setup_observability(
        service_name="dawsos-executor",
        environment=os.getenv("ENVIRONMENT", "development"),
        jaeger_endpoint=os.getenv("JAEGER_ENDPOINT"),
        sentry_dsn=os.getenv("SENTRY_DSN"),
    )
    logger.info("Observability enabled: Jaeger tracing and Sentry error tracking")
else:
    logger.info("Observability disabled (set ENABLE_OBSERVABILITY=true to enable)")


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
# Metrics Endpoint
# ============================================================================


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.
    """
    from observability.metrics import generate_metrics, METRICS_CONTENT_TYPE
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
    claims: dict = Depends(verify_token),  # JWT authentication (production)
) -> ExecuteResponse:
    """
    Execute pattern with freshness gate and JWT authentication.

    Sacred Flow:
        1. Verify JWT token (via verify_token dependency)
        2. Get latest pricing pack
        3. Check freshness gate (CRITICAL: block if warming)
        4. Check portfolio access (RLS enforcement)
        5. Construct RequestCtx (immutable context with user_id + user_role)
        6. Execute pattern via orchestrator
        7. Audit log execution
        8. Return result with metadata (pack ID, ledger hash, timing)

    Authentication:
        - Requires valid JWT token in Authorization header
        - Format: "Authorization: Bearer <token>"
        - Token must contain user_id, email, role claims

    Authorization:
        - Portfolio access checked via RLS policies
        - Users can only access their own portfolios (unless ADMIN)

    Args:
        req: Execute request (pattern_id, inputs, require_fresh, asof_date)
        claims: JWT claims (user_id, email, role) from verify_token dependency

    Returns:
        ExecuteResponse with result and metadata

    Raises:
        HTTPException 401: Missing or invalid JWT token
        HTTPException 403: Portfolio access denied
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
                logger.info(f"Execute request: pattern={req.pattern_id}, user={claims['user_id']}, request_id={request_id}")

                # Add pattern attributes to span
                add_pattern_attributes(span, req.pattern_id, req.inputs)

                return await _execute_pattern_internal(req, claims, request_id, started_at, span, metrics_registry)

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
    claims: dict,
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

        # Extract user info from JWT claims
        user_id = claims["user_id"]
        user_role = claims.get("role", "USER")

        # Build context (immutable)
        from uuid import UUID
        ctx = RequestCtx(
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            pricing_pack_id=pack["id"],
            ledger_commit_hash=ledger_commit_hash,
            trace_id=request_id,  # Use request_id as trace_id
            request_id=request_id,
            timestamp=started_at,
            asof_date=asof_date,
            require_fresh=req.require_fresh,
            portfolio_id=UUID(req.portfolio_id) if req.portfolio_id else None,
        )

        logger.info(f"RequestCtx constructed: user_id={user_id}, role={user_role}, {ctx.to_dict()}")

        # Add context attributes to span
        add_context_attributes(span, ctx)

        # ========================================
        # STEP 3.5: Portfolio Access Check (Authorization)
        # ========================================

        # Check if user has access to the requested portfolio (if portfolio_id provided)
        if ctx.portfolio_id and user_role != "ADMIN":
            try:
                pool = get_db_pool()
                access_query = """
                    SELECT COUNT(*) as count
                    FROM portfolios
                    WHERE id = $1 AND user_id = $2
                """
                access_result = await pool.fetchrow(access_query, ctx.portfolio_id, ctx.user_id)

                if not access_result or access_result["count"] == 0:
                    logger.warning(
                        f"Portfolio access denied: user_id={ctx.user_id}, portfolio_id={ctx.portfolio_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=ExecError(
                            code=ErrorCode.PATTERN_INVALID,
                            message=f"Access denied to portfolio {ctx.portfolio_id}",
                            request_id=request_id,
                        ).to_dict(),
                    )

                logger.debug(f"Portfolio access granted: user_id={ctx.user_id}, portfolio_id={ctx.portfolio_id}")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Portfolio access check failed: {e}")
                # Fail closed - deny access on error
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ExecError(
                        code=ErrorCode.PATTERN_INVALID,
                        message="Portfolio access check failed",
                        request_id=request_id,
                    ).to_dict(),
                )

        # ========================================
        # STEP 3.6: RLS Context Enforcement (Security)
        # ========================================

        # RLS (Row-Level Security) REQUIREMENT:
        # All database queries MUST use get_db_connection_with_rls(ctx.user_id) to enforce
        # multi-tenant data isolation. This sets app.user_id for RLS policies.
        #
        # ✅ RLS Infrastructure Status:
        #    - get_db_connection_with_rls() implemented: backend/app/db/connection.py:165
        #    - RLS policies defined: backend/db/migrations/005_create_rls_policies.sql
        #    - RequestCtx includes user_id: backend/app/core/types.py:98
        #
        # Security Enforcement:
        #   - RequestCtx now carries the caller UUID (from JWT claims)
        #   - Agents must call get_db_connection_with_rls(ctx.user_id)
        #   - RLS context is transaction-scoped (auto-resets after transaction)

        if not ctx.user_id:
            logger.warning(
                "RLS WARNING: Missing user_id on RequestCtx; falling back to stub behaviour"
            )

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

            # ========================================
            # STEP 4.5: Audit Log Execution
            # ========================================

            # Log pattern execution for compliance and debugging
            try:
                audit_service = get_audit_service()
                await audit_service.log(
                    user_id=str(ctx.user_id),
                    action="execute_pattern",
                    resource_type="pattern",
                    resource_id=req.pattern_id,
                    details={
                        "portfolio_id": str(ctx.portfolio_id) if ctx.portfolio_id else None,
                        "pricing_pack_id": pack["id"],
                        "ledger_commit_hash": ledger_commit_hash,
                        "asof_date": str(asof_date),
                        "require_fresh": req.require_fresh,
                        "inputs": req.inputs,
                        "execution_time_ms": (datetime.now() - started_at).total_seconds() * 1000,
                    }
                )
                logger.debug("Audit log recorded for pattern execution")
            except Exception as audit_error:
                # Never fail request due to audit logging failure
                logger.error(f"Failed to write audit log: {audit_error}")

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


@app.get("/health/pack")
async def health_pack():
    """
    Pricing pack health check endpoint.

    Returns pack freshness status for monitoring.

    Response:
        - status: 'warming' | 'fresh' | 'error'
        - pack_id: Current pack ID
        - is_fresh: Boolean freshness flag
        - prewarm_done: Boolean prewarm completion flag
        - updated_at: Last update timestamp
        - estimated_ready: Estimated ready time (if warming)

    Status Codes:
        - 200: Pack is fresh and ready
        - 503: Pack is warming (not ready yet)
        - 500: Pack error or not found
    """
    try:
        from app.db.pricing_pack_queries import get_pricing_pack_queries

        pack_queries = get_pricing_pack_queries()

        # Get latest pack
        pack = await pack_queries.get_latest_pack()

        if not pack:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "No pricing packs found",
                    "pack_id": None,
                    "is_fresh": False,
                    "prewarm_done": False,
                }
            )

        pack_id = pack["id"]
        status = pack.get("status", "unknown")
        is_fresh = pack.get("is_fresh", False)
        prewarm_done = pack.get("prewarm_done", False)
        updated_at = pack.get("updated_at")
        error_message = pack.get("error_message")

        # Determine HTTP status code
        if status == "fresh" and is_fresh:
            http_status = 200
        elif status == "warming":
            http_status = 503
        else:
            http_status = 500

        # Estimate ready time (if warming)
        estimated_ready = None
        if status == "warming" and updated_at:
            # Assume 30 minutes from pack creation
            from datetime import timedelta
            estimated_ready = (updated_at + timedelta(minutes=30)).isoformat()

        response = {
            "status": status,
            "pack_id": pack_id,
            "is_fresh": is_fresh,
            "prewarm_done": prewarm_done,
            "updated_at": updated_at.isoformat() if updated_at else None,
            "estimated_ready": estimated_ready,
        }

        if error_message:
            response["error_message"] = error_message

        return JSONResponse(
            status_code=http_status,
            content=response
        )

    except Exception as e:
        logger.exception(f"Health pack check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "pack_id": None,
                "is_fresh": False,
            }
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
