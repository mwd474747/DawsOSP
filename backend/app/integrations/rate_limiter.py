"""
DawsOS Rate Limiter

Purpose: Token bucket rate limiting with jittered backoff
Updated: 2025-11-05
Priority: P0 (Critical for API compliance)

Features:
    - Token bucket algorithm
    - Per-provider rate limits
    - Jittered exponential backoff on 429 errors
    - Bandwidth budget tracking (for FMP)

Usage:
    @rate_limit(requests_per_minute=120)
    async def call_api(self, request):
        # API call
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Dict

logger = logging.getLogger(__name__)


# ============================================================================
# Token Bucket Rate Limiter
# ============================================================================


@dataclass
class TokenBucket:
    """
    Token bucket for rate limiting.

    Tokens are added at a constant rate (refill_rate).
    Each request consumes 1 token.
    If no tokens available, request is delayed.
    """

    capacity: int  # Maximum tokens
    refill_rate: float  # Tokens per second
    tokens: float = field(init=False)
    last_refill: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self.tokens = float(self.capacity)

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens (blocking if necessary).

        Args:
            tokens: Number of tokens to acquire

        Returns:
            Delay in seconds (0 if no delay)
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return 0.0

        # Not enough tokens - calculate delay
        tokens_needed = tokens - self.tokens
        delay = tokens_needed / self.refill_rate

        # Add jitter (±10%)
        jittered_delay = delay * (1 + random.uniform(-0.1, 0.1))

        logger.debug(
            f"Rate limit: waiting {jittered_delay:.2f}s for {tokens} tokens "
            f"(current: {self.tokens:.2f}/{self.capacity})"
        )

        await asyncio.sleep(jittered_delay)

        # Refill and consume
        self._refill()
        self.tokens -= tokens

        return jittered_delay


# ============================================================================
# Rate Limiter Manager
# ============================================================================


class RateLimiterManager:
    """
    Manage token buckets for multiple providers.

    Each provider gets its own token bucket based on rate limits.
    """

    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}

    def get_bucket(self, provider: str, requests_per_minute: int) -> TokenBucket:
        """
        Get token bucket for provider.

        Args:
            provider: Provider name
            requests_per_minute: Rate limit

        Returns:
            TokenBucket instance
        """
        if provider not in self.buckets:
            # Convert requests_per_minute to refill_rate (tokens per second)
            refill_rate = requests_per_minute / 60.0

            self.buckets[provider] = TokenBucket(
                capacity=requests_per_minute,
                refill_rate=refill_rate,
            )

            logger.info(
                f"Created rate limiter for {provider}: "
                f"{requests_per_minute} req/min ({refill_rate:.2f} tokens/sec)"
            )

        return self.buckets[provider]


# Global rate limiter manager
_rate_limiter_manager = RateLimiterManager()


# ============================================================================
# Rate Limit Decorator
# ============================================================================


def rate_limit(requests_per_minute: int):
    """
    Decorator to enforce rate limiting on provider calls.

    Uses token bucket algorithm with jittered delays.

    Args:
        requests_per_minute: Maximum requests per minute

    Usage:
        @rate_limit(requests_per_minute=120)
        async def call_api(self, request):
            # API call
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, request, *args, **kwargs):
            provider_name = self.name

            # Get token bucket
            bucket = _rate_limiter_manager.get_bucket(provider_name, requests_per_minute)

            # Acquire token (may block)
            delay = await bucket.acquire(tokens=1)

            if delay > 0:
                logger.debug(
                    f"Rate limit enforced for {provider_name}: delayed {delay:.2f}s"
                )

            # Execute call
            return await func(self, request, *args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Exponential Backoff for 429 Errors
# ============================================================================


async def backoff_on_429(
    func: Callable, provider_name: str, max_retries: int = 3
) -> any:
    """
    Retry with exponential backoff on 429 (rate limit) errors.

    Delays: 1s, 2s, 4s (jittered)

    Args:
        func: Async function to retry
        provider_name: Provider name (for metrics)
        max_retries: Maximum retry attempts

    Returns:
        Function result

    Raises:
        Exception: If max retries exceeded
    """
    delays = [1, 2, 4]

    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            # Check if 429 error
            if hasattr(e, "status_code") and e.status_code == 429:
                if attempt < max_retries - 1:
                    delay = delays[attempt]
                    # Add jitter (±20%)
                    jittered_delay = delay * (1 + random.uniform(-0.2, 0.2))

                    logger.warning(
                        f"Rate limit 429 from {provider_name}, "
                        f"retrying in {jittered_delay:.2f}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )

                    await asyncio.sleep(jittered_delay)
                else:
                    logger.error(
                        f"Max retries exceeded for {provider_name} after 429 errors"
                    )
                    raise
            else:
                # Not a 429 error - re-raise immediately
                raise

    # Should not reach here
    raise Exception(f"Max retries exceeded for {provider_name}")


# ============================================================================
# Bandwidth Budget Tracker (for FMP)
# ============================================================================


@dataclass
class BandwidthBudget:
    """
    Track bandwidth usage and budget.

    FMP has monthly bandwidth cap (e.g., 50 GB).
    Alert at 70%, 85%, 95% thresholds.
    """

    monthly_limit_gb: float
    current_usage_gb: float = 0.0
    month_start: datetime = field(default_factory=lambda: datetime.utcnow().replace(day=1))

    def add_usage(self, bytes_used: int):
        """
        Add bandwidth usage.

        Args:
            bytes_used: Bytes consumed in this request
        """
        gb_used = bytes_used / (1024**3)
        self.current_usage_gb += gb_used

        # Check if new month
        now = datetime.utcnow()
        if now.month != self.month_start.month:
            logger.info(
                f"Bandwidth reset for new month: "
                f"previous usage {self.current_usage_gb:.2f} GB"
            )
            self.current_usage_gb = 0.0
            self.month_start = now.replace(day=1)

        # Check thresholds
        usage_pct = self.current_usage_gb / self.monthly_limit_gb * 100

        if usage_pct >= 95:
            logger.error(
                f"CRITICAL: Bandwidth usage at {usage_pct:.1f}% "
                f"({self.current_usage_gb:.2f}/{self.monthly_limit_gb} GB)"
            )
        elif usage_pct >= 85:
            logger.warning(
                f"WARNING: Bandwidth usage at {usage_pct:.1f}% "
                f"({self.current_usage_gb:.2f}/{self.monthly_limit_gb} GB)"
            )
        elif usage_pct >= 70:
            logger.info(
                f"NOTICE: Bandwidth usage at {usage_pct:.1f}% "
                f"({self.current_usage_gb:.2f}/{self.monthly_limit_gb} GB)"
            )

    def get_status(self) -> Dict:
        """Get bandwidth budget status."""
        usage_pct = self.current_usage_gb / self.monthly_limit_gb * 100
        remaining_pct = 100 - usage_pct

        return {
            "monthly_limit_gb": self.monthly_limit_gb,
            "current_usage_gb": round(self.current_usage_gb, 2),
            "usage_pct": round(usage_pct, 1),
            "remaining_pct": round(remaining_pct, 1),
            "month_start": self.month_start.isoformat(),
        }
