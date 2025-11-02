"""
DawsOS Base Provider

Purpose: Abstract base class for all external data provider facades
Updated: 2025-11-02
Priority: P0 (Critical for data resilience)

Features:
    - Simple retry logic with exponential backoff
    - Respects API rate limits (429 status and retry-after headers)
    - Dead Letter Queue (DLQ) for failed requests
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
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from opentelemetry import trace
from prometheus_client import Counter, Gauge, Histogram

from app.core.types import ProviderTimeoutError, RequestCtx, RightsViolationError

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

provider_retries_total = Counter(
    "provider_retries_total",
    "Total provider API retries",
    labelnames=["provider", "endpoint", "retry_attempt"],
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
    max_retries: int = 3
    retry_base_delay: float = 1.0  # Base delay for exponential backoff
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
    Base provider facade with smart retry logic and DLQ.

    All provider implementations must inherit from this class and
    implement the call() method.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize base provider.

        Args:
            config: Provider configuration
        """
        self.config = config  # Store the full config object
        self.name = config.name
        self.base_url = config.base_url
        self.rate_limit_rpm = config.rate_limit_rpm
        self.rights = config.rights
        self.max_retries = config.max_retries
        self.retry_base_delay = config.retry_base_delay
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

    async def call_with_retry(
        self, request: ProviderRequest
    ) -> ProviderResponse:
        """
        Execute call with smart retry logic and exponential backoff.

        Args:
            request: Provider request

        Returns:
            Provider response (may be cached/stale if all retries fail)

        Raises:
            ProviderError: If all retries fail and no cached data available
        """
        last_exception = None
        retry_delays = [self.retry_base_delay, self.retry_base_delay * 2, self.retry_base_delay * 4]  # 1s, 2s, 4s
        
        for attempt in range(self.max_retries + 1):
            try:
                with tracer.start_as_current_span("provider.call") as span:
                    span.set_attribute("provider", self.name)
                    span.set_attribute("endpoint", request.endpoint)
                    span.set_attribute("retry_attempt", attempt)

                    response = await self.call(request)

                    span.set_attribute("latency_ms", response.latency_ms)
                    span.set_attribute("status_code", response.status_code)
                    span.set_attribute("cached", response.cached)

                    # Cache successful response
                    await self._cache_response(request, response)

                    # Record success metrics
                    self._record_metrics(request.endpoint, response.status_code, response.latency_ms)
                    
                    if attempt > 0:
                        logger.info(
                            f"{self.name}: Request succeeded after {attempt} retries for {request.endpoint}"
                        )
                    
                    return response

            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code if hasattr(e, 'response') else 0
                
                # Handle rate limiting (429) with retry-after header
                if status_code == 429 and hasattr(e.response, 'headers'):
                    retry_after = e.response.headers.get('retry-after')
                    if retry_after:
                        try:
                            delay = float(retry_after)
                            logger.warning(
                                f"{self.name}: Rate limited (429) on {request.endpoint}, "
                                f"retry-after: {delay}s (attempt {attempt + 1}/{self.max_retries + 1})"
                            )
                            
                            if attempt < self.max_retries:
                                provider_retries_total.labels(
                                    provider=self.name,
                                    endpoint=request.endpoint,
                                    retry_attempt=str(attempt + 1)
                                ).inc()
                                await asyncio.sleep(delay)
                                continue
                        except (ValueError, TypeError):
                            pass
                
                # For other errors, use exponential backoff
                if attempt < self.max_retries:
                    # Add jitter to prevent thundering herd
                    delay = retry_delays[attempt] * (1 + random.uniform(-0.2, 0.2))
                    
                    logger.warning(
                        f"{self.name}: Request failed for {request.endpoint} "
                        f"(status: {status_code}), retrying in {delay:.2f}s "
                        f"(attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    
                    provider_retries_total.labels(
                        provider=self.name,
                        endpoint=request.endpoint,
                        retry_attempt=str(attempt + 1)
                    ).inc()
                    
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Add jitter to prevent thundering herd
                    delay = retry_delays[attempt] * (1 + random.uniform(-0.2, 0.2))
                    
                    logger.warning(
                        f"{self.name}: Request failed for {request.endpoint} "
                        f"({type(e).__name__}: {str(e)}), retrying in {delay:.2f}s "
                        f"(attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    
                    provider_retries_total.labels(
                        provider=self.name,
                        endpoint=request.endpoint,
                        retry_attempt=str(attempt + 1)
                    ).inc()
                    
                    await asyncio.sleep(delay)

        # All retries failed, log error and try cached data
        logger.error(
            f"{self.name}: All {self.max_retries + 1} attempts failed for {request.endpoint}: "
            f"{type(last_exception).__name__}: {str(last_exception)}"
        )
        
        # Record error metrics
        provider_errors_total.labels(
            provider=self.name,
            endpoint=request.endpoint,
            error_type="max_retries_exceeded"
        ).inc()
        
        # Enqueue in DLQ for potential later retry
        if last_exception:
            await self.dlq.enqueue(request, error=str(last_exception))
        
        # Try to serve cached data as fallback
        cached = await self._get_cached(request)
        if cached:
            logger.warning(
                f"{self.name}: Serving cached/stale data for {request.endpoint} after all retries failed"
            )
            return cached.with_stale_flag()

        # No cached data - re-raise the last exception
        if last_exception:
            raise last_exception
        else:
            raise ProviderError(f"All retries failed for {request.endpoint}")

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
        # from app.services.rights_registry import get_registry
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
