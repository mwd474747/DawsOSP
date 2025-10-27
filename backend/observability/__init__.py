"""
DawsOS Observability Module

Purpose: Centralized observability setup for tracing, metrics, and error tracking
Updated: 2025-10-22
Priority: P1 (Sprint 1 Week 2 Gate)

Components:
    - tracing.py: OpenTelemetry distributed tracing
    - metrics.py: Prometheus metrics collection
    - errors.py: Sentry error capture

Usage:
    from backend.observability import setup_observability

    setup_observability(
        service_name="dawsos-executor",
        environment="production",
        jaeger_endpoint="http://localhost:14268/api/traces",
        sentry_dsn="https://...",
    )
"""

from .tracing import setup_tracing, get_tracer, trace_context
from .metrics import setup_metrics, metrics
from .errors import setup_error_tracking, capture_exception

__all__ = [
    "setup_tracing",
    "get_tracer",
    "trace_context",
    "setup_metrics",
    "metrics",
    "setup_error_tracking",
    "capture_exception",
]


def setup_observability(
    service_name: str = "dawsos-executor",
    environment: str = "development",
    jaeger_endpoint: str = None,
    sentry_dsn: str = None,
    enable_metrics: bool = True,
):
    """
    Setup all observability components.

    Args:
        service_name: Service identifier for traces/metrics
        environment: Environment name (dev/staging/production)
        jaeger_endpoint: Jaeger collector endpoint (optional)
        sentry_dsn: Sentry DSN for error tracking (optional)
        enable_metrics: Enable Prometheus metrics (default: True)
    """
    # Setup tracing
    if jaeger_endpoint:
        setup_tracing(
            service_name=service_name,
            environment=environment,
            jaeger_endpoint=jaeger_endpoint,
        )

    # Setup metrics
    if enable_metrics:
        setup_metrics(service_name=service_name)

    # Setup error tracking
    if sentry_dsn:
        setup_error_tracking(
            dsn=sentry_dsn,
            environment=environment,
            service_name=service_name,
        )
