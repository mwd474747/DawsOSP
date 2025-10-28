"""
Rate Limiter - Token bucket algorithm for API rate limiting

Purpose: Implement rate limiting for external provider API calls
Updated: 2025-10-23
Priority: P0 (Critical for provider compliance)

The rate limiter prevents exceeding provider API limits by:
1. Using token bucket algorithm for smooth rate limiting
2. Configurable rate limits per provider
3. Blocking and non-blocking token acquisition
4. Per-provider rate limiter instances

Token Bucket Algorithm:
    - Tokens are added to bucket at fixed rate (e.g., 120/min)
    - Each request consumes 1 token
    - If bucket empty, request waits or fails
    - Bucket has maximum capacity (burst allowance)

Usage:
    from app.core.rate_limiter import TokenBucket

    # Create rate limiter (120 requests per minute)
    limiter = TokenBucket(rate=120, per=60.0)

    # Blocking acquisition (wait for token)
    await limiter.acquire()
    result = await api_call()

    # Non-blocking acquisition (fail fast)
    if limiter.try_acquire():
        result = await api_call()
    else:
        logger.warning("Rate limit exceeded")

Sacred Invariants:
    1. Tokens refill at constant rate
    2. Bucket capacity = rate (allows short bursts)
    3. acquire() blocks until token available
    4. try_acquire() returns immediately (True/False)

References:
    - PRODUCT_SPEC.md §5 (Rate Limiting)
"""

import asyncio
import logging
import time
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("DawsOS.RateLimiter")


# ============================================================================
# Metrics
# ============================================================================


@dataclass
class RateLimiterMetrics:
    """Rate limiter metrics for observability."""
    name: str
    rate: float
    per: float
    tokens: float
    capacity: float
    total_requests: int
    total_throttled: int
    last_acquire: Optional[float]

    def to_dict(self) -> dict:
        """Convert metrics to dictionary."""
        return {
            "name": self.name,
            "rate": self.rate,
            "per": self.per,
            "tokens": self.tokens,
            "capacity": self.capacity,
            "total_requests": self.total_requests,
            "total_throttled": self.total_throttled,
            "last_acquire": self.last_acquire,
        }


# ============================================================================
# Token Bucket
# ============================================================================


class TokenBucket:
    """
    Token bucket rate limiter.

    Implements the token bucket algorithm:
    - Tokens are added at fixed rate (e.g., 120/min = 2/sec)
    - Each request consumes 1 token
    - If bucket empty, request waits (acquire) or fails (try_acquire)
    - Bucket has max capacity for burst traffic
    """

    def __init__(
        self,
        name: str = "default",
        rate: float = 60,
        per: float = 60.0,
        capacity: Optional[float] = None,
    ):
        """
        Initialize token bucket.

        Args:
            name: Rate limiter name (e.g., "FMP", "Polygon")
            rate: Number of tokens per time period (e.g., 120)
            per: Time period in seconds (e.g., 60 for per-minute)
            capacity: Max tokens in bucket (default: rate, allows burst)
        """
        self.name = name
        self.rate = rate
        self.per = per
        self.capacity = capacity or rate

        # Calculate tokens per second
        self._tokens_per_second = rate / per

        # State
        self._tokens = self.capacity
        self._last_refill = time.time()

        # Metrics
        self._total_requests = 0
        self._total_throttled = 0
        self._last_acquire: Optional[float] = None

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Rate limiter '{name}' initialized: "
            f"{rate} requests per {per}s ({self._tokens_per_second:.2f}/sec), "
            f"capacity={self.capacity}"
        )

    def get_metrics(self) -> RateLimiterMetrics:
        """
        Get rate limiter metrics.

        Returns:
            RateLimiterMetrics object
        """
        return RateLimiterMetrics(
            name=self.name,
            rate=self.rate,
            per=self.per,
            tokens=self._tokens,
            capacity=self.capacity,
            total_requests=self._total_requests,
            total_throttled=self._total_throttled,
            last_acquire=self._last_acquire,
        )

    async def acquire(self, tokens: int = 1):
        """
        Acquire tokens from bucket (blocking).

        Waits until enough tokens are available.

        Args:
            tokens: Number of tokens to acquire (default: 1)
        """
        async with self._lock:
            self._total_requests += 1

            while True:
                # Refill tokens based on elapsed time
                self._refill()

                # Check if enough tokens available
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    self._last_acquire = time.time()
                    return

                # Not enough tokens, calculate wait time
                tokens_needed = tokens - self._tokens
                wait_time = tokens_needed / self._tokens_per_second

                self._total_throttled += 1
                logger.debug(
                    f"Rate limiter '{self.name}' throttling: "
                    f"need {tokens_needed:.2f} tokens, waiting {wait_time:.2f}s"
                )

        # Wait outside lock to allow other tasks to run
        await asyncio.sleep(wait_time)

        # Retry acquisition
        async with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                self._last_acquire = time.time()
                return

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from bucket (non-blocking).

        Returns immediately with success/failure.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if tokens acquired, False if insufficient tokens
        """
        self._total_requests += 1

        # Refill tokens based on elapsed time
        self._refill()

        # Check if enough tokens available
        if self._tokens >= tokens:
            self._tokens -= tokens
            self._last_acquire = time.time()
            return True

        # Not enough tokens
        self._total_throttled += 1
        logger.debug(
            f"Rate limiter '{self.name}' denied: "
            f"need {tokens} tokens, have {self._tokens:.2f}"
        )
        return False

    async def try_acquire_async(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from bucket (non-blocking, async).

        Returns immediately with success/failure.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if tokens acquired, False if insufficient tokens
        """
        async with self._lock:
            return self.try_acquire(tokens)

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill

        # Calculate tokens to add
        tokens_to_add = elapsed * self._tokens_per_second

        # Add tokens (up to capacity)
        self._tokens = min(self._tokens + tokens_to_add, self.capacity)
        self._last_refill = now

    def reset(self):
        """Reset bucket to full capacity."""
        logger.info(f"Rate limiter '{self.name}' reset to full capacity")
        self._tokens = self.capacity
        self._last_refill = time.time()


# ============================================================================
# Sliding Window Rate Limiter
# ============================================================================


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter (more precise than token bucket).

    Tracks exact timestamps of requests in a sliding window.
    More memory intensive but more accurate for strict limits.
    """

    def __init__(
        self,
        name: str = "default",
        max_requests: int = 60,
        window: float = 60.0,
    ):
        """
        Initialize sliding window rate limiter.

        Args:
            name: Rate limiter name (e.g., "FMP", "Polygon")
            max_requests: Max requests in window (e.g., 120)
            window: Window size in seconds (e.g., 60 for per-minute)
        """
        self.name = name
        self.max_requests = max_requests
        self.window = window

        # State: list of request timestamps
        self._requests: list[float] = []

        # Metrics
        self._total_requests = 0
        self._total_throttled = 0

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Sliding window rate limiter '{name}' initialized: "
            f"{max_requests} requests per {window}s"
        )

    async def acquire(self):
        """
        Acquire slot in window (blocking).

        Waits until request can be made within window.
        """
        async with self._lock:
            self._total_requests += 1

            while True:
                # Remove expired requests
                self._cleanup()

                # Check if we can make request
                if len(self._requests) < self.max_requests:
                    self._requests.append(time.time())
                    return

                # Window full, calculate wait time
                oldest_request = self._requests[0]
                wait_time = oldest_request + self.window - time.time()

                self._total_throttled += 1
                logger.debug(
                    f"Sliding window '{self.name}' throttling: "
                    f"window full ({len(self._requests)}/{self.max_requests}), "
                    f"waiting {wait_time:.2f}s"
                )

        # Wait outside lock
        await asyncio.sleep(max(0, wait_time))

        # Retry acquisition
        async with self._lock:
            self._cleanup()
            if len(self._requests) < self.max_requests:
                self._requests.append(time.time())
                return

    def try_acquire(self) -> bool:
        """
        Try to acquire slot in window (non-blocking).

        Returns:
            True if slot acquired, False if window full
        """
        self._total_requests += 1

        # Remove expired requests
        self._cleanup()

        # Check if we can make request
        if len(self._requests) < self.max_requests:
            self._requests.append(time.time())
            return True

        # Window full
        self._total_throttled += 1
        logger.debug(
            f"Sliding window '{self.name}' denied: "
            f"window full ({len(self._requests)}/{self.max_requests})"
        )
        return False

    def _cleanup(self):
        """Remove requests outside the window."""
        now = time.time()
        cutoff = now - self.window
        self._requests = [ts for ts in self._requests if ts > cutoff]

    def reset(self):
        """Clear all requests from window."""
        logger.info(f"Sliding window '{self.name}' reset")
        self._requests.clear()


# ============================================================================
# Global Registry
# ============================================================================


# Global registry of rate limiters (keyed by name)
_rate_limiters: dict[str, TokenBucket] = {}


def get_rate_limiter(
    name: str,
    rate: float = 60,
    per: float = 60.0,
    capacity: Optional[float] = None,
) -> TokenBucket:
    """
    Get or create rate limiter for a provider.

    Args:
        name: Provider name (e.g., "FMP", "Polygon", "FRED")
        rate: Number of tokens per time period (e.g., 120)
        per: Time period in seconds (e.g., 60 for per-minute)
        capacity: Max tokens in bucket (default: rate)

    Returns:
        TokenBucket instance
    """
    if name not in _rate_limiters:
        _rate_limiters[name] = TokenBucket(
            name=name,
            rate=rate,
            per=per,
            capacity=capacity,
        )

    return _rate_limiters[name]


def get_all_rate_limiters() -> dict[str, TokenBucket]:
    """
    Get all registered rate limiters.

    Returns:
        Dict mapping name to TokenBucket
    """
    return _rate_limiters.copy()


def reset_all_rate_limiters():
    """Reset all rate limiters to full capacity."""
    for limiter in _rate_limiters.values():
        limiter.reset()
