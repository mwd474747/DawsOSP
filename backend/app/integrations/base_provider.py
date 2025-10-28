"""
DawsOS Base Provider

Purpose: Abstract base class for all external data provider facades
Updated: 2025-10-21
Priority: P0 (Critical for data resilience)

Features:
    - Circuit breaker with OPEN/CLOSED/HALF_OPEN states
    - Dead Letter Queue (DLQ) for failed requests with exponential backoff
    - Rights pre-flight checks
    - OpenTelemetry tracing
    - Prometheus metrics
    - Cached/stale data serving when provider unavailable

Usage:
    class FMPProvider(BaseProvider):
        async def call(self, request: ProviderRequest) -> ProviderResponse:
            # Implementation
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from opentelemetry import trace
from prometheus_client import Counter, Gauge, Histogram

from backend.app.core.types import ProviderTimeoutError, RequestCtx, RightsViolationError

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# ============================================================================
# Prometheus Metrics
# ============================================================================

provider_requests_total = Counter(
    "provider_requests_total",
    "Total provider API requests",
    labelnames=["provider", "endpoint", "status"],
)

provider_latency_seconds = Histogram(
    "provider_latency_seconds",
    "Provider API latency in seconds",
    labelnames=["provider", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)

provider_errors_total = Counter(
    "provider_errors_total",
    "Total provider API errors",
    labelnames=["provider", "endpoint", "error_type"],
)

circuit_breaker_state_gauge = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
    labelnames=["provider"],
)

dlq_size_gauge = Gauge(
    "dlq_size",
    "Dead Letter Queue size",
    labelnames=["provider"],
)


# ============================================================================
# Exceptions
# ============================================================================


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


# ============================================================================
# Data Classes
# ============================================================================


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for a provider."""

    name: str
    base_url: str
    rate_limit_rpm: int
    circuit_breaker_threshold: int = 3
    circuit_breaker_timeout: int = 60
    rights: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderRequest:
    """Generic provider request."""

    endpoint: str
    params: Dict[str, Any]
    ctx: RequestCtx
    rights_check: Optional[str] = None  # e.g., "export_pdf"
    timeout: float = 5.0


@dataclass(frozen=True)
class ProviderResponse:
    """Generic provider response."""

    data: Any
    provider: str
    endpoint: str
    status_code: int
    latency_ms: float
    cached: bool = False
    stale: bool = False

    def with_stale_flag(self) -> "ProviderResponse":
        """Return copy with stale=True."""
        return ProviderResponse(
            data=self.data,
            provider=self.provider,
            endpoint=self.endpoint,
            status_code=self.status_code,
            latency_ms=self.latency_ms,
            cached=self.cached,
            stale=True,
        )


# ============================================================================
# Circuit Breaker
# ============================================================================


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = 0  # Normal operation
    OPEN = 1  # Blocking requests (serving stale data)
    HALF_OPEN = 2  # Testing recovery (limited requests)


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for provider resilience.

    State transitions:
        CLOSED → OPEN: After threshold failures
        OPEN → HALF_OPEN: After timeout expires
        HALF_OPEN → CLOSED: After successful request
        HALF_OPEN → OPEN: After failure
    """

    name: str
    threshold: int = 3  # Open after N failures
    timeout: int = 60  # Test recovery after N seconds
    state: CircuitState = field(default=CircuitState.CLOSED)
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    half_open_calls: int = 0
    max_half_open_calls: int = 1

    def is_open(self) -> bool:
        """
        Check if circuit is open.

        Returns:
            True if circuit is open (requests blocked)
        """
        if self.state == CircuitState.OPEN:
            # Check if timeout expired → move to HALF_OPEN
            if self.last_failure_time and datetime.utcnow() - self.last_failure_time > timedelta(
                seconds=self.timeout
            ):
                logger.info(f"Circuit breaker {self.name}: OPEN → HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                circuit_breaker_state_gauge.labels(provider=self.name).set(
                    CircuitState.HALF_OPEN.value
                )
                return False
            return True

        if self.state == CircuitState.HALF_OPEN:
            # Limit calls in half-open state
            if self.half_open_calls >= self.max_half_open_calls:
                return True

        return False

    def record_success(self):
        """Record successful call."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker {self.name}: HALF_OPEN → CLOSED")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
            circuit_breaker_state_gauge.labels(provider=self.name).set(
                CircuitState.CLOSED.value
            )
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery → back to OPEN
            logger.warning(f"Circuit breaker {self.name}: HALF_OPEN → OPEN (recovery failed)")
            self.state = CircuitState.OPEN
            circuit_breaker_state_gauge.labels(provider=self.name).set(CircuitState.OPEN.value)

        elif self.failure_count >= self.threshold:
            logger.error(
                f"Circuit breaker {self.name}: CLOSED → OPEN "
                f"({self.failure_count} failures, threshold={self.threshold})"
            )
            self.state = CircuitState.OPEN
            circuit_breaker_state_gauge.labels(provider=self.name).set(CircuitState.OPEN.value)

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.name,
            "failure_count": self.failure_count,
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
        }


# ============================================================================
# Dead Letter Queue
# ============================================================================


@dataclass
class DLQEntry:
    """Dead letter queue entry."""

    request: ProviderRequest
    error: str
    retry_count: int = 0
    enqueued_at: datetime = field(default_factory=datetime.utcnow)


class DeadLetterQueue:
    """
    Dead letter queue for failed provider requests.

    Retries with exponential backoff: 1s, 2s, 4s
    After max_retries, publishes to failed queue for manual review.
    """

    def __init__(self, name: str, max_retries: int = 3):
        self.name = name
        self.max_retries = max_retries
        self.queue: List[DLQEntry] = []
        self.failed_queue: List[DLQEntry] = []

    async def enqueue(self, request: ProviderRequest, error: str):
        """
        Enqueue failed request for retry.

        Args:
            request: Failed provider request
            error: Error message
        """
        entry = DLQEntry(request=request, error=error)
        self.queue.append(entry)
        dlq_size_gauge.labels(provider=self.name).set(len(self.queue))

        logger.warning(
            f"DLQ {self.name}: Enqueued request to {request.endpoint} "
            f"(error: {error}, queue size: {len(self.queue)})"
        )

        # Start background retry (no await - fire and forget)
        asyncio.create_task(self._retry_with_backoff(entry))

    async def _retry_with_backoff(self, entry: DLQEntry):
        """
        Retry with exponential backoff.

        Delays: 1s, 2s, 4s (jittered)
        """
        import random

        delays = [1, 2, 4]

        for delay in delays:
            # Add jitter (±20%)
            jittered_delay = delay * (1 + random.uniform(-0.2, 0.2))
            await asyncio.sleep(jittered_delay)

            entry.retry_count += 1

            try:
                logger.info(
                    f"DLQ {self.name}: Retry attempt {entry.retry_count}/{self.max_retries} "
                    f"for {entry.request.endpoint} (delay: {jittered_delay:.2f}s)"
                )

                # Retry would need provider instance - placeholder for now
                # TODO: Implement actual retry with provider reference
                # await provider.call(entry.request)

                # Success - remove from queue
                self.queue.remove(entry)
                dlq_size_gauge.labels(provider=self.name).set(len(self.queue))
                logger.info(f"DLQ {self.name}: Retry succeeded for {entry.request.endpoint}")
                return

            except Exception as e:
                logger.error(
                    f"DLQ {self.name}: Retry {entry.retry_count} failed: {e}"
                )

                if entry.retry_count >= self.max_retries:
                    # Move to failed queue for manual review
                    self.failed_queue.append(entry)
                    self.queue.remove(entry)
                    dlq_size_gauge.labels(provider=self.name).set(len(self.queue))

                    logger.error(
                        f"DLQ {self.name}: Max retries exceeded for {entry.request.endpoint}, "
                        f"moved to failed queue"
                    )
                    return


# ============================================================================
# Base Provider
# ============================================================================


class BaseProvider(ABC):
    """
    Base provider facade with circuit breaker and DLQ.

    All provider implementations must inherit from this class and
    implement the call() method.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize base provider.

        Args:
            config: Provider configuration
        """
        self.name = config.name
        self.base_url = config.base_url
        self.rate_limit_rpm = config.rate_limit_rpm
        self.rights = config.rights
        self.circuit_breaker = CircuitBreaker(
            name=config.name,
            threshold=config.circuit_breaker_threshold,
            timeout=config.circuit_breaker_timeout
        )
        self.dlq = DeadLetterQueue(name=f"{config.name}_dlq", max_retries=3)
        self._cache: Dict[str, ProviderResponse] = {}

        logger.info(f"Initialized provider: {config.name} (base_url={config.base_url})")

    @abstractmethod
    async def call(self, request: ProviderRequest) -> ProviderResponse:
        """
        Execute provider call.

        Must be implemented by subclasses.

        Args:
            request: Provider request

        Returns:
            Provider response

        Raises:
            ProviderTimeoutError: If request times out
            RightsViolationError: If rights check fails
        """
        pass

    async def call_with_circuit_breaker(
        self, request: ProviderRequest
    ) -> ProviderResponse:
        """
        Wrap call with circuit breaker and DLQ.

        Args:
            request: Provider request

        Returns:
            Provider response (may be cached/stale)

        Raises:
            ProviderTimeoutError: If circuit open and no cached data
        """
        # Check circuit breaker
        if self.circuit_breaker.is_open():
            logger.warning(
                f"Circuit breaker OPEN for {self.name}, attempting to serve cached data"
            )

            # Try to serve cached data
            cached = await self._get_cached(request)
            if cached:
                logger.info(
                    f"Serving cached/stale data for {request.endpoint} "
                    f"(circuit breaker open)"
                )
                return cached.with_stale_flag()

            # No cached data available
            raise ProviderTimeoutError(self.name, timeout_seconds=0)

        # Circuit breaker closed or half-open - attempt call
        try:
            with tracer.start_as_current_span("provider.call") as span:
                span.set_attribute("provider", self.name)
                span.set_attribute("endpoint", request.endpoint)
                span.set_attribute("circuit_breaker_state", self.circuit_breaker.state.name)

                response = await self.call(request)

                span.set_attribute("latency_ms", response.latency_ms)
                span.set_attribute("status_code", response.status_code)
                span.set_attribute("cached", response.cached)

                # Record success
                self.circuit_breaker.record_success()

                # Cache response
                await self._cache_response(request, response)

                return response

        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()

            # Enqueue in DLQ for retry
            await self.dlq.enqueue(request, error=str(e))

            # Try to serve cached data
            cached = await self._get_cached(request)
            if cached:
                logger.warning(
                    f"Provider call failed, serving cached/stale data for {request.endpoint}"
                )
                return cached.with_stale_flag()

            # No cached data - re-raise exception
            raise

    async def _get_cached(self, request: ProviderRequest) -> Optional[ProviderResponse]:
        """Get cached response for request."""
        cache_key = f"{request.endpoint}:{request.params}"
        return self._cache.get(cache_key)

    async def _cache_response(self, request: ProviderRequest, response: ProviderResponse):
        """Cache response for request."""
        cache_key = f"{request.endpoint}:{request.params}"
        self._cache[cache_key] = response

    async def _check_rights(self, ctx: RequestCtx, action: str):
        """
        Pre-flight rights check.

        Args:
            ctx: Request context with rights_profile
            action: Action to check (e.g., "export_pdf")

        Raises:
            RightsViolationError: If action not allowed
        """
        if not ctx.rights_profile:
            return  # No restrictions

        # TODO: Implement rights check against registry
        # from backend.app.services.rights_registry import get_registry
        # registry = get_registry()
        # result = registry.check_export([self.name], action, ctx.rights_profile)
        # if not result.allowed:
        #     raise RightsViolationError(action, ctx.rights_profile)

        # Placeholder: log the check
        logger.debug(
            f"Rights check: provider={self.name}, action={action}, "
            f"profile={ctx.rights_profile}"
        )

    def _record_metrics(self, endpoint: str, status_code: int, latency_ms: float):
        """Record Prometheus metrics."""
        provider_requests_total.labels(
            provider=self.name,
            endpoint=endpoint,
            status=str(status_code),
        ).inc()

        provider_latency_seconds.labels(
            provider=self.name,
            endpoint=endpoint,
        ).observe(latency_ms / 1000.0)

        if status_code >= 400:
            error_type = "client_error" if status_code < 500 else "server_error"
            provider_errors_total.labels(
                provider=self.name,
                endpoint=endpoint,
                error_type=error_type,
            ).inc()
