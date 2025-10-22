"""
DawsOS Executor API

Purpose: FastAPI application with /execute endpoint, pattern orchestration, and observability
Updated: 2025-10-21
Priority: P0 (Critical for execution architecture)

Routes:
    POST /execute - Execute a pattern with full traceability
    GET /health - Health check
    GET /patterns - List available patterns
    GET /metrics - Prometheus metrics

Observability:
    - OpenTelemetry spans with pattern_id, pricing_pack_id, ledger_commit_hash
    - Prometheus histograms for pattern execution latency
    - Structured logging with trace_id correlation
"""

import json
import logging
import os
import subprocess
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

from app.core.types import RequestCtx

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "trace_id": "%(trace_id)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)

# ============================================================================
# OpenTelemetry Configuration
# ============================================================================

# Configure OTel resource
resource = Resource.create(
    {
        "service.name": "dawsos-executor-api",
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    }
)

# Configure trace provider
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

# Configure OTLP exporter (if endpoint configured)
otlp_endpoint = os.getenv("OTLP_ENDPOINT")
if otlp_endpoint:
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    logger.info(f"OpenTelemetry configured with OTLP endpoint: {otlp_endpoint}")
else:
    logger.warning("OTLP_ENDPOINT not configured - traces will not be exported")

# Get tracer
tracer = trace.get_tracer(__name__)

# ============================================================================
# Prometheus Metrics
# ============================================================================

# Pattern execution latency histogram
pattern_latency_histogram = Histogram(
    "pattern_latency_seconds",
    "Pattern execution latency in seconds",
    labelnames=["pattern_id", "status"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# Request counter
request_counter = Counter(
    "executor_requests_total",
    "Total number of executor requests",
    labelnames=["pattern_id", "status"],
)

# Freshness gate counter
freshness_gate_counter = Counter(
    "freshness_gate_blocks_total",
    "Total number of requests blocked by freshness gate",
    labelnames=["pack_id"],
)

# ============================================================================
# Request/Response Models
# ============================================================================


class ExecRequest(BaseModel):
    """Pattern execution request."""

    pattern_id: str = Field(..., description="Pattern ID to execute")
    portfolio_id: Optional[str] = Field(
        None, description="Portfolio UUID (if pattern is portfolio-scoped)"
    )
    inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Pattern input parameters"
    )
    asof: Optional[date] = Field(
        None, description="As-of date (defaults to today)"
    )


class ExecResponse(BaseModel):
    """Pattern execution response."""

    data: Dict[str, Any] = Field(..., description="Pattern output data")
    charts: list[Dict] = Field(default_factory=list, description="UI-ready chart configs")
    trace: Dict[str, Any] = Field(..., description="Execution trace with reproducibility metadata")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    version: str


class PatternInfo(BaseModel):
    """Pattern metadata."""

    id: str
    name: str
    description: str
    category: str


# ============================================================================
# Application Lifecycle
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting DawsOS Executor API")

    # Initialize database connection pool
    # db_pool = await create_db_pool()
    # app.state.db_pool = db_pool

    # Initialize Redis connection pool
    # redis_pool = await create_redis_pool()
    # app.state.redis_pool = redis_pool

    # Initialize services
    # services = {
    #     "db": db_pool,
    #     "redis": redis_pool,
    #     # Add API providers as they're configured
    # }
    # app.state.services = services

    # Initialize agent runtime (will be created in next file)
    # from app.core.agent_runtime import AgentRuntime
    # runtime = AgentRuntime(services)
    # Register agents here
    # app.state.runtime = runtime

    # Initialize pattern orchestrator (will be created in next file)
    # from app.core.pattern_orchestrator import PatternOrchestrator
    # orchestrator = PatternOrchestrator(runtime, db_pool, redis_pool)
    # app.state.orchestrator = orchestrator

    logger.info("DawsOS Executor API started successfully")

    yield

    logger.info("Shutting down DawsOS Executor API")
    # Close database pool
    # await db_pool.close()
    # Close Redis pool
    # await redis_pool.close()


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="DawsOS Executor API",
    version="1.0.0",
    description="Pattern-based portfolio intelligence executor with reproducibility guarantees",
    lifespan=lifespan,
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Pack-ID", "X-Rights-Version", "X-Trace-ID"],
        max_age=3600,
    )

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)


# ============================================================================
# Security Headers Middleware
# ============================================================================


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Add HSTS in production
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Add trace ID to response headers for debugging
    if hasattr(request.state, "trace_id"):
        response.headers["X-Trace-ID"] = request.state.trace_id

    return response


# ============================================================================
# Dependency Injection
# ============================================================================


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.

    TODO: Implement JWT validation with AUTH_SECURITY from infrastructure phase.
    For now, returns a demo user for development.
    """
    # TODO: Implement JWT authentication
    # from app.auth import validate_jwt_token
    # token = request.headers.get("Authorization", "").replace("Bearer ", "")
    # user = await validate_jwt_token(token)
    # return user

    # Development placeholder
    return {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "email": "demo@dawsos.com",
    }


async def get_db():
    """
    Get database connection from pool.

    TODO: Implement after infrastructure phase completes.
    """
    # TODO: Return connection from pool
    # async with app.state.db_pool.acquire() as conn:
    #     yield conn
    pass


# ============================================================================
# Helper Functions
# ============================================================================


async def build_request_context(
    req: ExecRequest, user: Dict[str, Any], trace_id: str
) -> RequestCtx:
    """
    Build immutable request context with reproducibility guarantees.

    Args:
        req: Execution request
        user: Authenticated user
        trace_id: OpenTelemetry trace ID

    Returns:
        RequestCtx with pricing_pack_id, ledger_commit_hash, and metadata

    Raises:
        HTTPException: If pricing pack not found or not fresh
    """
    asof = req.asof or date.today()

    # TODO: Query pricing pack from database
    # pack = await db.fetchrow("SELECT id, is_fresh FROM pricing_packs WHERE asof_date = $1", asof)
    # if not pack:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"No pricing pack found for {asof}"
    #     )
    # pricing_pack_id = str(pack["id"])
    # is_fresh = pack["is_fresh"]

    # Development placeholder
    pricing_pack_id = f"{asof.strftime('%Y%m%d')}_v1"
    is_fresh = True

    # Get ledger commit hash (requires ledger repo to be cloned)
    ledger_path = os.getenv("LEDGER_PATH", "/app/ledger")
    try:
        if os.path.exists(ledger_path):
            ledger_commit = subprocess.check_output(
                ["git", "-C", ledger_path, "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
        else:
            # Development placeholder
            ledger_commit = "dev_no_ledger"
            logger.warning(f"Ledger repo not found at {ledger_path}, using placeholder")
    except subprocess.CalledProcessError:
        ledger_commit = "dev_git_error"
        logger.warning("Failed to get ledger commit hash, using placeholder")

    # Get portfolio settings if portfolio_id provided
    base_currency = "CAD"  # Default
    if req.portfolio_id:
        # TODO: Query portfolio settings from database
        # portfolio = await db.fetchrow(
        #     "SELECT base_ccy FROM portfolios WHERE id = $1",
        #     UUID(req.portfolio_id)
        # )
        # if not portfolio:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail=f"Portfolio {req.portfolio_id} not found"
        #     )
        # base_currency = portfolio["base_ccy"]
        pass

    # Create immutable request context
    ctx = RequestCtx(
        pricing_pack_id=pricing_pack_id,
        ledger_commit_hash=ledger_commit,
        trace_id=trace_id,
        user_id=UUID(user["user_id"]),
        request_id=str(uuid4()),
        timestamp=datetime.utcnow(),
        portfolio_id=UUID(req.portfolio_id) if req.portfolio_id else None,
        base_currency=base_currency,
        rights_profile=os.getenv("RIGHTS_PROFILE", "staging"),
    )

    return ctx


async def is_pack_fresh(pricing_pack_id: str) -> bool:
    """
    Check if pricing pack is fresh (pre-warming completed).

    Args:
        pricing_pack_id: Pricing pack ID to check

    Returns:
        True if pack is fresh, False if still warming
    """
    # TODO: Query database for pack freshness
    # pack = await db.fetchrow("SELECT is_fresh FROM pricing_packs WHERE id = $1", pricing_pack_id)
    # return pack["is_fresh"] if pack else False

    # Development placeholder (always fresh)
    return True


async def run_pattern(
    pattern_id: str,
    ctx: RequestCtx,
    inputs: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute pattern through orchestrator.

    Args:
        pattern_id: Pattern to execute
        ctx: Request context with reproducibility metadata
        inputs: Pattern input parameters

    Returns:
        Dict with data, charts, and trace

    Raises:
        ValueError: If pattern not found
    """
    # TODO: Use pattern orchestrator
    # orchestrator = app.state.orchestrator
    # return await orchestrator.run_pattern(pattern_id, ctx, inputs)

    # Development placeholder
    logger.info(f"Running pattern {pattern_id} with context {ctx.to_dict()}")
    return {
        "data": {
            "message": f"Pattern {pattern_id} executed successfully",
            "inputs": inputs,
        },
        "charts": [],
        "trace": {
            "pattern_id": pattern_id,
            "pricing_pack_id": ctx.pricing_pack_id,
            "ledger_commit_hash": ctx.ledger_commit_hash,
            "agents_used": [],
            "capabilities_used": [],
            "sources": [],
            "per_panel_staleness": [],
            "steps": [],
        },
    }


# ============================================================================
# API Routes
# ============================================================================


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        version="1.0.0",
    )


@app.get("/patterns", response_model=list[PatternInfo])
async def list_patterns():
    """
    List all available patterns.

    Returns:
        List of pattern metadata (id, name, description, category)
    """
    patterns = []
    patterns_dir = Path("patterns")

    if not patterns_dir.exists():
        logger.warning(f"Patterns directory not found: {patterns_dir}")
        return patterns

    for pattern_file in patterns_dir.rglob("*.json"):
        try:
            spec = json.loads(pattern_file.read_text())
            patterns.append(
                PatternInfo(
                    id=spec["id"],
                    name=spec["name"],
                    description=spec.get("description", ""),
                    category=spec.get("category", "unknown"),
                )
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load pattern {pattern_file}: {e}")

    return patterns


@app.post("/execute", response_model=ExecResponse)
async def execute(
    req: ExecRequest,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Execute a pattern with full traceability.

    Args:
        req: Pattern execution request
        request: FastAPI request object
        user: Authenticated user from JWT

    Returns:
        ExecResponse with data, charts, and trace

    Raises:
        HTTPException 404: Pattern or pricing pack not found
        HTTPException 503: Pricing pack is warming (not fresh)
    """
    # Get current trace context
    span = trace.get_current_span()
    trace_context = span.get_span_context()
    trace_id = f"{trace_context.trace_id:032x}" if trace_context.is_valid else str(uuid4())
    request.state.trace_id = trace_id

    # Start pattern execution span
    with tracer.start_as_current_span(
        "pattern_execution",
        attributes={
            "pattern.id": req.pattern_id,
            "portfolio.id": req.portfolio_id or "none",
        },
    ) as execution_span:
        start_time = datetime.utcnow()

        try:
            # Build request context
            ctx = await build_request_context(req, user, trace_id)

            # Add context to span attributes
            execution_span.set_attribute("pricing.pack_id", ctx.pricing_pack_id)
            execution_span.set_attribute("ledger.commit_hash", ctx.ledger_commit_hash)
            execution_span.set_attribute("request.id", ctx.request_id)

            # Freshness gate: Block if pricing pack is warming
            if not await is_pack_fresh(ctx.pricing_pack_id):
                freshness_gate_counter.labels(pack_id=ctx.pricing_pack_id).inc()
                execution_span.set_attribute("freshness.blocked", True)
                request_counter.labels(pattern_id=req.pattern_id, status="blocked").inc()

                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "PACK_WARMING",
                        "message": "Pricing pack is warming up. Please retry in a few minutes.",
                        "pack_id": ctx.pricing_pack_id,
                        "trace_id": trace_id,
                    },
                )

            execution_span.set_attribute("freshness.blocked", False)

            # TODO: Set RLS context for database queries
            # await db.execute(f"SET LOCAL app.user_id = '{user['user_id']}'")

            # Execute pattern through orchestrator
            result = await run_pattern(req.pattern_id, ctx, req.inputs)

            # Record success metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            pattern_latency_histogram.labels(
                pattern_id=req.pattern_id, status="success"
            ).observe(duration)
            request_counter.labels(pattern_id=req.pattern_id, status="success").inc()

            execution_span.set_attribute("execution.duration_seconds", duration)
            execution_span.set_attribute("execution.status", "success")

            logger.info(
                f"Pattern {req.pattern_id} executed successfully in {duration:.3f}s",
                extra={"trace_id": trace_id},
            )

            return ExecResponse(
                data=result["data"],
                charts=result.get("charts", []),
                trace=result["trace"],
            )

        except HTTPException:
            # Re-raise HTTP exceptions (already have proper status codes)
            raise

        except Exception as e:
            # Record failure metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            pattern_latency_histogram.labels(
                pattern_id=req.pattern_id, status="error"
            ).observe(duration)
            request_counter.labels(pattern_id=req.pattern_id, status="error").inc()

            execution_span.set_attribute("execution.status", "error")
            execution_span.set_attribute("error.message", str(e))
            execution_span.record_exception(e)

            logger.error(
                f"Pattern {req.pattern_id} execution failed: {e}",
                extra={"trace_id": trace_id},
                exc_info=True,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "EXECUTION_FAILED",
                    "message": str(e),
                    "pattern_id": req.pattern_id,
                    "trace_id": trace_id,
                },
            )


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns:
        Metrics in Prometheus text format
    """
    return generate_latest().decode("utf-8")


# ============================================================================
# Development Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
