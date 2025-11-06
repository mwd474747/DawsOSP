"""
DawsOS Base Provider

Purpose: Abstract base class for all external data provider facades
Updated: 2025-11-02
Priority: P0 (Critical for data resilience)

Features:
    - Simple retry logic with exponential backoff
    - Respects API rate limits (429 status and retry-after headers)
    - Rights pre-flight checks
    - OpenTelemetry tracing
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

from app.core.types import ProviderTimeoutError, RequestCtx, RightsViolationError

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


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
# Base Provider
# ============================================================================


class BaseProvider(ABC):
    """
    Base provider facade with smart retry logic and cached fallback.

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
            ProviderError: If API call fails
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

                    await asyncio.sleep(delay)

        # All retries failed, log error and try cached data
        logger.error(
            f"{self.name}: All {self.max_retries + 1} attempts failed for {request.endpoint}: "
            f"{type(last_exception).__name__}: {str(last_exception)}"
        )

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

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_body: Optional[Dict] = None,
        timeout: float = 30.0
    ) -> Any:
        """
        Make HTTP request with error handling.

        Shared implementation for all providers to reduce code duplication.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            json_body: JSON request body
            timeout: Request timeout in seconds (default: 30.0)

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: If HTTP error occurs
        """
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_body
            )
            response.raise_for_status()
            return response.json()

