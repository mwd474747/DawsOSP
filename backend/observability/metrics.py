"""
DawsOS Prometheus Metrics

Purpose: Collect and expose metrics for Prometheus scraping
Updated: 2025-10-22
Priority: P1 (Sprint 1 Week 2 Gate)

Metrics:
    - API latency: Histogram of request duration by pattern
    - Request count: Counter of requests by pattern/status
    - Pack freshness: Gauge of pack status (0=warming, 1=fresh, 2=error)
    - Agent invocations: Counter of agent calls by agent/capability
    - Circuit breaker state: Gauge of circuit breaker status

Usage:
    from observability.metrics import setup_metrics, metrics

    # Setup once at app startup
    setup_metrics(service_name="dawsos-executor")

    # Record metrics
    with metrics.api_latency.labels(pattern_id="portfolio_overview").time():
        result = await orchestrator.run(...)

    metrics.request_count.labels(pattern_id="portfolio_overview", status="success").inc()
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional

# Prometheus imports (will be optional - gracefully degrade if not installed)
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Info,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger("DawsOS.Metrics")


# ============================================================================
# Metrics Registry
# ============================================================================


class MetricsRegistry:
    """
    Central registry for all Prometheus metrics.

    Provides easy access to metrics throughout the application.
    """

    def __init__(self, service_name: str = "dawsos"):
        """
        Initialize metrics registry.

        Args:
            service_name: Service name prefix for metrics
        """
        self.service_name = service_name
        self.enabled = PROMETHEUS_AVAILABLE

        if not self.enabled:
            logger.warning(
                "Prometheus client not installed. Metrics disabled. "
                "Install with: pip install prometheus-client"
            )
            return

        # API Metrics
        self.api_latency = Histogram(
            f"{service_name}_api_request_duration_seconds",
            "API request duration in seconds",
            ["pattern_id", "status"],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )

        self.request_count = Counter(
            f"{service_name}_requests_total",
            "Total number of API requests",
            ["pattern_id", "status"],
        )

        self.request_errors = Counter(
            f"{service_name}_request_errors_total",
            "Total number of request errors",
            ["pattern_id", "error_type"],
        )

        # Pack Metrics
        self.pack_freshness = Gauge(
            f"{service_name}_pack_freshness",
            "Pricing pack freshness status (0=warming, 1=fresh, 2=error, 3=stale)",
            ["pack_id"],
        )

        self.pack_build_duration = Histogram(
            f"{service_name}_pack_build_duration_seconds",
            "Pricing pack build duration in seconds",
            ["pack_id"],
            buckets=(60, 300, 600, 1200, 1800, 3600),  # 1min to 1hour
        )

        # Agent Metrics
        self.agent_invocations = Counter(
            f"{service_name}_agent_invocations_total",
            "Total number of agent capability invocations",
            ["agent_name", "capability", "status"],
        )

        self.agent_latency = Histogram(
            f"{service_name}_agent_latency_seconds",
            "Agent capability execution duration",
            ["agent_name", "capability"],
            buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
        )

        # Circuit Breaker Metrics
        self.circuit_breaker_state = Gauge(
            f"{service_name}_circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=open, 2=half_open)",
            ["agent_name"],
        )

        self.circuit_breaker_failures = Counter(
            f"{service_name}_circuit_breaker_failures_total",
            "Total circuit breaker failures",
            ["agent_name"],
        )

        # Pattern Metrics
        self.pattern_executions = Counter(
            f"{service_name}_pattern_executions_total",
            "Total pattern executions",
            ["pattern_id", "status"],
        )

        self.pattern_step_duration = Histogram(
            f"{service_name}_pattern_step_duration_seconds",
            "Pattern step execution duration",
            ["pattern_id", "step_index", "capability"],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
        )

        # System Info
        self.build_info = Info(
            f"{service_name}_build",
            "Build information",
        )
        self.build_info.info({
            "version": "1.0.0",
            "service": service_name,
        })

        logger.info(f"Prometheus metrics initialized: service={service_name}")

    @contextmanager
    def time_request(self, pattern_id: str):
        """
        Context manager to time API requests.

        Args:
            pattern_id: Pattern being executed

        Usage:
            with metrics.time_request("portfolio_overview"):
                result = await orchestrator.run(...)
        """
        if not self.enabled:
            yield
            return

        start_time = time.time()
        status = "success"

        try:
            yield
        except Exception as e:
            status = "error"
            self.request_errors.labels(
                pattern_id=pattern_id,
                error_type=type(e).__name__,
            ).inc()
            raise
        finally:
            duration = time.time() - start_time
            self.api_latency.labels(
                pattern_id=pattern_id,
                status=status,
            ).observe(duration)
            self.request_count.labels(
                pattern_id=pattern_id,
                status=status,
            ).inc()

    @contextmanager
    def time_agent(self, agent_name: str, capability: str):
        """
        Context manager to time agent invocations.

        Args:
            agent_name: Agent handling request
            capability: Capability being invoked

        Usage:
            with metrics.time_agent("financial_analyst", "ledger.positions"):
                result = await agent.execute(...)
        """
        if not self.enabled:
            yield
            return

        start_time = time.time()
        status = "success"

        try:
            yield
        except Exception:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            self.agent_latency.labels(
                agent_name=agent_name,
                capability=capability,
            ).observe(duration)
            self.agent_invocations.labels(
                agent_name=agent_name,
                capability=capability,
                status=status,
            ).inc()

    def record_pack_freshness(self, pack_id: str, status: str) -> None:
        """
        Record pricing pack freshness status.

        Args:
            pack_id: Pricing pack ID
            status: Pack status (warming/fresh/error/stale)
        """
        if not self.enabled:
            return

        status_map = {
            "warming": 0,
            "fresh": 1,
            "error": 2,
            "stale": 3,
        }

        value = status_map.get(status, 0)
        self.pack_freshness.labels(pack_id=pack_id).set(value)

    def record_circuit_breaker_state(self, agent_name: str, state: str) -> None:
        """
        Record circuit breaker state.

        Args:
            agent_name: Agent name
            state: Circuit breaker state (CLOSED/OPEN/HALF_OPEN)
        """
        if not self.enabled:
            return

        state_map = {
            "CLOSED": 0,
            "OPEN": 1,
            "HALF_OPEN": 2,
        }

        value = state_map.get(state, 0)
        self.circuit_breaker_state.labels(agent_name=agent_name).set(value)

    def record_pattern_execution(self, pattern_id: str, status: str) -> None:
        """
        Record pattern execution.

        Args:
            pattern_id: Pattern ID
            status: Execution status (success/error)
        """
        if not self.enabled:
            return

        self.pattern_executions.labels(
            pattern_id=pattern_id,
            status=status,
        ).inc()


# ============================================================================
# Global Metrics Instance
# ============================================================================

# Global metrics registry
metrics: Optional[MetricsRegistry] = None


def setup_metrics(service_name: str = "dawsos") -> MetricsRegistry:
    """
    Setup Prometheus metrics.

    Args:
        service_name: Service name for metrics

    Returns:
        MetricsRegistry instance
    """
    global metrics

    if metrics is None:
        metrics = MetricsRegistry(service_name=service_name)

    return metrics


def get_metrics() -> Optional[MetricsRegistry]:
    """
    Get global metrics registry.

    Returns:
        MetricsRegistry instance or None if not setup
    """
    return metrics


def generate_metrics() -> bytes:
    """
    Generate Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format

    Usage:
        from fastapi import Response
        from observability.metrics import generate_metrics, CONTENT_TYPE_LATEST

        @app.get("/metrics")
        async def metrics_endpoint():
            return Response(content=generate_metrics(), media_type=CONTENT_TYPE_LATEST)
    """
    if not PROMETHEUS_AVAILABLE:
        return b"# Prometheus client not installed\n"

    return generate_latest()


# Export content type for FastAPI
if PROMETHEUS_AVAILABLE:
    METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST
else:
    METRICS_CONTENT_TYPE = "text/plain"


# ============================================================================
# No-Op Metrics for Graceful Degradation
# ============================================================================


class NoOpMetric:
    """No-op metric for when Prometheus is disabled."""

    def labels(self, **kwargs):
        """No-op labels."""
        return self

    def inc(self, amount=1):
        """No-op increment."""
        pass

    def dec(self, amount=1):
        """No-op decrement."""
        pass

    def set(self, value):
        """No-op set."""
        pass

    def observe(self, amount):
        """No-op observe."""
        pass

    @contextmanager
    def time(self):
        """No-op time context manager."""
        yield


# ============================================================================
# Example Usage (for documentation)
# ============================================================================

if __name__ == "__main__":
    # Setup metrics
    setup_metrics(service_name="dawsos")

    # Example: Record API request
    with metrics.time_request("portfolio_overview"):
        time.sleep(0.1)  # Simulate work
        print("Request timed")

    # Example: Record agent invocation
    with metrics.time_agent("financial_analyst", "ledger.positions"):
        time.sleep(0.05)  # Simulate work
        print("Agent invocation timed")

    # Example: Record pack freshness
    metrics.record_pack_freshness("PP_2025-10-22", "fresh")

    # Example: Record circuit breaker state
    metrics.record_circuit_breaker_state("financial_analyst", "CLOSED")

    # Generate metrics
    print("\nGenerated metrics:")
    print(generate_metrics().decode())
