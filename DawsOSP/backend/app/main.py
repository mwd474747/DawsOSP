"""
DawsOS Executor API

Purpose: FastAPI application with legacy endpoints (execution moved to /v1/execute)
Updated: 2025-10-22 (Governance remediation - legacy /execute removed)
Priority: P0 (Critical for execution architecture)

Routes:
    GET /health - Health check
    GET /patterns - List available patterns
    GET /metrics - Prometheus metrics

Note: Pattern execution has moved to POST /v1/execute (backend/app/api/executor.py)
      This file now contains only legacy support endpoints.

Observability:
    - OpenTelemetry spans with pattern_id, pricing_pack_id, ledger_commit_hash
    - Prometheus histograms for pattern execution latency
    - Structured logging with trace_id correlation
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, status
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
