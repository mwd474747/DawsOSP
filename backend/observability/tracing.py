"""
DawsOS OpenTelemetry Tracing

Purpose: Distributed tracing with OpenTelemetry and Jaeger
Updated: 2025-10-22
Priority: P1 (Sprint 1 Week 2 Gate)

Features:
    - Automatic trace context propagation
    - Span creation with rich attributes
    - Integration with FastAPI
    - Jaeger exporter for visualization

Critical Attributes:
    - pricing_pack_id: Immutable pricing snapshot
    - ledger_commit_hash: Exact ledger state
    - pattern_id: Pattern being executed
    - agent_name: Agent handling request
    - capability: Capability being invoked

Usage:
    from backend.observability.tracing import setup_tracing, trace_context

    # Setup once at app startup
    setup_tracing(
        service_name="dawsos-executor",
        jaeger_endpoint="http://localhost:14268/api/traces"
    )

    # Use context manager for automatic span creation
    with trace_context("execute_pattern", pattern_id=pattern_id) as span:
        span.set_attribute("pricing_pack_id", ctx.pricing_pack_id)
        result = await orchestrator.run(...)
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional

# OpenTelemetry imports (will be optional - gracefully degrade if not installed)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None

logger = logging.getLogger("DawsOS.Tracing")

# Global tracer instance
_tracer = None
_tracer_provider = None


def setup_tracing(
    service_name: str = "dawsos-executor",
    environment: str = "development",
    jaeger_endpoint: Optional[str] = None,
) -> None:
    """
    Setup OpenTelemetry tracing with Jaeger exporter.

    Args:
        service_name: Service name for traces
        environment: Environment (dev/staging/production)
        jaeger_endpoint: Jaeger collector endpoint (e.g., http://localhost:14268/api/traces)
                        If None, tracing will be disabled
    """
    global _tracer, _tracer_provider

    if not OTEL_AVAILABLE:
        logger.warning(
            "OpenTelemetry not installed. Tracing disabled. "
            "Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger"
        )
        return

    if not jaeger_endpoint:
        logger.info("No Jaeger endpoint provided. Tracing disabled.")
        return

    try:
        # Create resource with service name
        resource = Resource(attributes={
            SERVICE_NAME: service_name,
            "environment": environment,
            "service.version": "1.0.0",
        })

        # Create tracer provider
        _tracer_provider = TracerProvider(resource=resource)

        # Create Jaeger exporter
        jaeger_exporter = JaegerExporter(
            collector_endpoint=jaeger_endpoint,
        )

        # Add span processor with Jaeger exporter
        span_processor = BatchSpanProcessor(jaeger_exporter)
        _tracer_provider.add_span_processor(span_processor)

        # Set global tracer provider
        trace.set_tracer_provider(_tracer_provider)

        # Get tracer
        _tracer = trace.get_tracer(__name__)

        logger.info(
            f"OpenTelemetry tracing initialized: service={service_name}, "
            f"jaeger={jaeger_endpoint}"
        )

    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}", exc_info=True)
        _tracer = None


def get_tracer():
    """
    Get the global tracer instance.

    Returns:
        Tracer instance or None if tracing not setup
    """
    return _tracer


@contextmanager
def trace_context(
    span_name: str,
    attributes: Optional[Dict[str, Any]] = None,
    **kwargs,
):
    """
    Context manager for creating spans with automatic cleanup.

    Args:
        span_name: Name of the span (e.g., "execute_pattern", "agent_capability")
        attributes: Dict of attributes to set on span
        **kwargs: Additional attributes (convenience)

    Usage:
        with trace_context("execute_pattern", pattern_id=pattern_id) as span:
            span.set_attribute("pricing_pack_id", ctx.pricing_pack_id)
            result = await orchestrator.run(...)

    Yields:
        Span instance or NoOpSpan if tracing not available
    """
    if not _tracer:
        # No-op span for graceful degradation
        yield NoOpSpan()
        return

    # Merge attributes and kwargs
    all_attributes = attributes or {}
    all_attributes.update(kwargs)

    # Start span
    with _tracer.start_as_current_span(span_name) as span:
        # Set attributes
        for key, value in all_attributes.items():
            if value is not None:
                span.set_attribute(key, str(value))

        yield span


class NoOpSpan:
    """No-op span for when tracing is disabled."""

    def set_attribute(self, key: str, value: Any) -> None:
        """No-op set attribute."""
        pass

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """No-op add event."""
        pass

    def set_status(self, status: Any) -> None:
        """No-op set status."""
        pass


def instrument_fastapi(app):
    """
    Instrument FastAPI app with automatic tracing.

    Args:
        app: FastAPI application instance

    Usage:
        from fastapi import FastAPI
        from backend.observability.tracing import instrument_fastapi

        app = FastAPI()
        instrument_fastapi(app)
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available. Cannot instrument FastAPI.")
        return

    if not _tracer:
        logger.warning("Tracing not setup. Call setup_tracing() first.")
        return

    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}", exc_info=True)


# ============================================================================
# Helper Functions for Common Attributes
# ============================================================================


def add_context_attributes(span, ctx) -> None:
    """
    Add RequestCtx attributes to span.

    Args:
        span: OpenTelemetry span
        ctx: RequestCtx instance
    """
    if not span:
        return

    span.set_attribute("pricing_pack_id", ctx.pricing_pack_id)
    span.set_attribute("ledger_commit_hash", ctx.ledger_commit_hash)
    span.set_attribute("user_id", str(ctx.user_id))
    span.set_attribute("request_id", ctx.request_id)
    span.set_attribute("trace_id", ctx.trace_id)

    if ctx.asof_date:
        span.set_attribute("asof_date", str(ctx.asof_date))

    if ctx.portfolio_id:
        span.set_attribute("portfolio_id", str(ctx.portfolio_id))

    span.set_attribute("require_fresh", ctx.require_fresh)


def add_pattern_attributes(span, pattern_id: str, inputs: Dict[str, Any]) -> None:
    """
    Add pattern attributes to span.

    Args:
        span: OpenTelemetry span
        pattern_id: Pattern ID being executed
        inputs: Pattern inputs
    """
    if not span:
        return

    span.set_attribute("pattern_id", pattern_id)
    span.set_attribute("pattern_inputs_count", len(inputs))

    # Add input keys (not values, to avoid PII)
    if inputs:
        span.set_attribute("pattern_input_keys", ",".join(inputs.keys()))


def add_agent_attributes(span, agent_name: str, capability: str) -> None:
    """
    Add agent attributes to span.

    Args:
        span: OpenTelemetry span
        agent_name: Agent handling request
        capability: Capability being invoked
    """
    if not span:
        return

    span.set_attribute("agent_name", agent_name)
    span.set_attribute("capability", capability)


def add_error_attributes(span, error: Exception) -> None:
    """
    Add error attributes to span.

    Args:
        span: OpenTelemetry span
        error: Exception that occurred
    """
    if not span:
        return

    span.set_attribute("error", True)
    span.set_attribute("error.type", type(error).__name__)
    span.set_attribute("error.message", str(error))

    # Set span status to error
    if OTEL_AVAILABLE:
        from opentelemetry.trace import Status, StatusCode
        span.set_status(Status(StatusCode.ERROR, str(error)))


# ============================================================================
# Example Usage (for documentation)
# ============================================================================

if __name__ == "__main__":
    # Setup tracing
    setup_tracing(
        service_name="dawsos-executor",
        jaeger_endpoint="http://localhost:14268/api/traces",
    )

    # Example: Create span with attributes
    with trace_context("test_span", operation="test") as span:
        span.set_attribute("test_attribute", "test_value")
        print("Span created and attributes set")

    print("Tracing setup complete")
