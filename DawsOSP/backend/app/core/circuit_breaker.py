"""
Circuit Breaker - Failure detection and provider protection

Purpose: Implement circuit breaker pattern for external provider calls
Updated: 2025-10-23
Priority: P0 (Critical for provider resilience)

The circuit breaker prevents cascading failures by:
1. Tracking consecutive failures for each provider
2. Opening circuit after threshold failures (default: 3)
3. Rejecting requests for timeout period (default: 60s)
4. Testing recovery with half-open state

States:
    CLOSED: Normal operation, requests pass through
    OPEN: Provider down, reject requests immediately
    HALF_OPEN: Testing if provider recovered (allow 1 request)

Usage:
    from backend.app.core.circuit_breaker import CircuitBreaker

    # Create circuit breaker for provider
    breaker = CircuitBreaker(name="FMP", threshold=3, timeout=60)

    # Execute function with circuit breaker
    try:
        result = await breaker.call(my_async_func, arg1, arg2)
    except CircuitBreakerOpenError:
        # Circuit is open, provider is down
        logger.warning("FMP circuit breaker is open")

Sacred Invariants:
    1. Circuit opens after threshold consecutive failures
    2. Circuit stays open for timeout seconds
    3. Half-open state allows exactly 1 test request
    4. Successful request in half-open → CLOSED
    5. Failed request in half-open → OPEN (reset timeout)

References:
    - PRODUCT_SPEC.md §5 (Circuit Breaker)
    - PRODUCT_SPEC.md §13 (Circuit Breaker stub)
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Any, TypeVar, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("DawsOS.CircuitBreaker")

T = TypeVar('T')


# ============================================================================
# Circuit Breaker States
# ============================================================================


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"           # Normal operation
    OPEN = "open"              # Provider down, reject requests
    HALF_OPEN = "half_open"    # Testing recovery


# ============================================================================
# Exceptions
# ============================================================================


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and request is rejected."""
    pass


# ============================================================================
# Metrics
# ============================================================================


@dataclass
class CircuitBreakerMetrics:
    """Circuit breaker metrics for observability."""
    name: str
    state: CircuitState
    failure_count: int
    success_count: int
    total_requests: int
    last_failure_time: Optional[float]
    last_state_change: Optional[float]
    opened_at: Optional[float]

    def to_dict(self) -> dict:
        """Convert metrics to dictionary."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "opened_at": self.opened_at,
        }


# ============================================================================
# Circuit Breaker
# ============================================================================


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    Implements the circuit breaker pattern:
    - CLOSED: Normal operation, requests pass through
    - OPEN: After threshold failures, reject requests for timeout period
    - HALF_OPEN: After timeout, allow 1 test request to check recovery
    """

    def __init__(
        self,
        name: str,
        threshold: int = 3,
        timeout: float = 60.0,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name (e.g., "FMP", "Polygon")
            threshold: Number of consecutive failures before opening (default: 3)
            timeout: Seconds to wait before testing recovery (default: 60)
        """
        self.name = name
        self.threshold = threshold
        self.timeout = timeout

        # State
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._total_requests = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change: Optional[float] = None
        self._opened_at: Optional[float] = None

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"threshold={threshold}, timeout={timeout}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self._state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self._state == CircuitState.CLOSED

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self._state == CircuitState.HALF_OPEN

    def get_metrics(self) -> CircuitBreakerMetrics:
        """
        Get circuit breaker metrics.

        Returns:
            CircuitBreakerMetrics object
        """
        return CircuitBreakerMetrics(
            name=self.name,
            state=self._state,
            failure_count=self._failure_count,
            success_count=self._success_count,
            total_requests=self._total_requests,
            last_failure_time=self._last_failure_time,
            last_state_change=self._last_state_change,
            opened_at=self._opened_at,
        )

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Result from func

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception raised by func
        """
        async with self._lock:
            self._total_requests += 1

            # Check if circuit should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(
                        f"Circuit breaker '{self.name}' transitioning to HALF_OPEN "
                        f"(timeout expired after {self.timeout}s)"
                    )
                    self._transition_to_half_open()
                else:
                    # Circuit is still open, reject request
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN "
                        f"(opened {time.time() - self._opened_at:.1f}s ago, "
                        f"timeout={self.timeout}s)"
                    )

        # Execute function (outside lock to allow concurrent requests in CLOSED state)
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result

        except Exception as e:
            await self._on_failure(e)
            raise

    def call_sync(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute synchronous function with circuit breaker protection.

        Args:
            func: Synchronous function to execute
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Result from func

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception raised by func
        """
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(
                    f"Circuit breaker '{self.name}' transitioning to HALF_OPEN "
                    f"(timeout expired after {self.timeout}s)"
                )
                self._transition_to_half_open()
            else:
                # Circuit is still open, reject request
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN "
                    f"(opened {time.time() - self._opened_at:.1f}s ago, "
                    f"timeout={self.timeout}s)"
                )

        self._total_requests += 1

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success_sync()
            return result

        except Exception as e:
            self._on_failure_sync(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if timeout has expired and circuit should attempt reset."""
        if self._state != CircuitState.OPEN:
            return False

        if self._opened_at is None:
            return False

        elapsed = time.time() - self._opened_at
        return elapsed >= self.timeout

    async def _on_success(self):
        """Handle successful request."""
        async with self._lock:
            self._on_success_sync()

    def _on_success_sync(self):
        """Handle successful request (synchronous)."""
        self._success_count += 1

        if self._state == CircuitState.HALF_OPEN:
            # Success in half-open → transition to closed
            logger.info(
                f"Circuit breaker '{self.name}' transitioning to CLOSED "
                f"(test request succeeded)"
            )
            self._transition_to_closed()
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0

    async def _on_failure(self, error: Exception):
        """Handle failed request."""
        async with self._lock:
            self._on_failure_sync(error)

    def _on_failure_sync(self, error: Exception):
        """Handle failed request (synchronous)."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        logger.warning(
            f"Circuit breaker '{self.name}' recorded failure "
            f"({self._failure_count}/{self.threshold}): {error}"
        )

        if self._state == CircuitState.HALF_OPEN:
            # Failure in half-open → transition back to open
            logger.warning(
                f"Circuit breaker '{self.name}' transitioning to OPEN "
                f"(test request failed)"
            )
            self._transition_to_open()

        elif self._state == CircuitState.CLOSED:
            # Check if threshold exceeded
            if self._failure_count >= self.threshold:
                logger.error(
                    f"Circuit breaker '{self.name}' transitioning to OPEN "
                    f"(threshold {self.threshold} failures exceeded)"
                )
                self._transition_to_open()

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = None
        self._last_state_change = time.time()

    def _transition_to_open(self):
        """Transition to OPEN state."""
        self._state = CircuitState.OPEN
        self._opened_at = time.time()
        self._last_state_change = time.time()

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        self._state = CircuitState.HALF_OPEN
        self._failure_count = 0
        self._last_state_change = time.time()

    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = None
        self._last_state_change = time.time()


# ============================================================================
# Global Registry
# ============================================================================


# Global registry of circuit breakers (keyed by name)
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    threshold: int = 3,
    timeout: float = 60.0,
) -> CircuitBreaker:
    """
    Get or create circuit breaker for a provider.

    Args:
        name: Provider name (e.g., "FMP", "Polygon", "FRED")
        threshold: Number of consecutive failures before opening (default: 3)
        timeout: Seconds to wait before testing recovery (default: 60)

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            threshold=threshold,
            timeout=timeout,
        )

    return _circuit_breakers[name]


def get_all_circuit_breakers() -> dict[str, CircuitBreaker]:
    """
    Get all registered circuit breakers.

    Returns:
        Dict mapping name to CircuitBreaker
    """
    return _circuit_breakers.copy()


def reset_all_circuit_breakers():
    """Reset all circuit breakers to CLOSED state."""
    for breaker in _circuit_breakers.values():
        breaker.reset()
