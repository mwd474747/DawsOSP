#!/usr/bin/env python3
"""
API Helper - Shared instrumentation for capability modules

Provides unified retry logic, fallback tracking, and error handling for all
external API calls (FRED, FMP, News, etc.). Eliminates code duplication and
ensures consistent fallback behavior across the system.
"""

from typing import Callable, Any, Optional, Dict
from functools import wraps
import time
from core.logger import get_logger
from core.fallback_tracker import get_fallback_tracker

logger = get_logger('APIHelper')


class APIHelper:
    """
    Mixin for capability modules providing retry, logging, and fallback tracking

    Usage:
        class MyCapability(APIHelper):
            def __init__(self):
                super().__init__()

            def fetch_data(self, param):
                return self.api_call(
                    self._internal_fetch,
                    param,
                    max_retries=3,
                    fallback={'error': 'API unavailable'}
                )
    """

    def __init__(self):
        """Initialize API helper with statistics tracking"""
        self.api_stats = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'total_latency': 0.0,
            'fallbacks_used': 0
        }

    def api_call(
        self,
        func: Callable,
        *args,
        max_retries: int = 3,
        backoff: float = 1.0,
        fallback: Optional[Any] = None,
        component_name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute API call with retry, logging, and fallback tracking

        Args:
            func: API function to call
            *args: Positional arguments for func
            max_retries: Maximum retry attempts (default: 3)
            backoff: Initial backoff seconds for exponential backoff (default: 1.0)
            fallback: Value to return on total failure (default: None)
            component_name: Component name for fallback tracking (default: func.__name__)
            **kwargs: Keyword arguments for func

        Returns:
            API result or fallback value

        Raises:
            Exception: If fallback is None and all retries exhausted
        """
        self.api_stats['requests'] += 1
        component = component_name or func.__name__

        last_error = None

        for attempt in range(max_retries):
            try:
                start = time.time()
                result = func(*args, **kwargs)
                latency = time.time() - start

                self.api_stats['successes'] += 1
                self.api_stats['total_latency'] += latency

                logger.info(
                    f"API call succeeded: {component} ({latency:.2f}s, attempt {attempt + 1}/{max_retries})"
                )

                return result

            except Exception as e:
                last_error = e
                wait_time = backoff * (2 ** attempt)

                logger.warning(
                    f"API call failed (attempt {attempt + 1}/{max_retries}): "
                    f"{component} - {type(e).__name__}: {str(e)}"
                )

                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)

        # All retries exhausted
        self.api_stats['failures'] += 1

        logger.error(
            f"API call exhausted retries: {component} after {max_retries} attempts - {last_error}"
        )

        # Use fallback if provided
        if fallback is not None:
            self.api_stats['fallbacks_used'] += 1

            # Track fallback event
            tracker = get_fallback_tracker()
            fallback_reason = self._categorize_error(last_error)

            tracker.mark_fallback(
                component=component,
                reason=fallback_reason,
                data_type='cached' if isinstance(fallback, dict) else 'default'
            )

            logger.warning(f"Using fallback for {component}: {fallback_reason}")
            return fallback

        # No fallback - raise error
        raise last_error

    def _categorize_error(self, error: Exception) -> str:
        """
        Categorize error into fallback reason

        Args:
            error: Exception that occurred

        Returns:
            Fallback reason string
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()

        # Check for specific error patterns
        if 'timeout' in error_msg:
            return 'timeout'
        elif 'rate limit' in error_msg or '429' in error_msg:
            return 'rate_limit'
        elif 'quota' in error_msg:
            return 'quota_exceeded'
        elif 'connection' in error_msg or 'network' in error_msg:
            return 'connection_error'
        elif 'unauthorized' in error_msg or '401' in error_msg:
            return 'api_key_missing'
        elif 'forbidden' in error_msg or '403' in error_msg:
            return 'api_key_invalid'
        else:
            return 'api_error'

    def get_api_stats(self) -> Dict[str, Any]:
        """
        Get API statistics for monitoring

        Returns:
            Dict with:
            - requests: Total number of requests
            - successes: Successful requests
            - failures: Failed requests
            - avg_latency: Average latency in seconds
            - success_rate: Success rate (0-1)
            - fallbacks_used: Number of times fallback was used
        """
        avg_latency = (
            self.api_stats['total_latency'] / self.api_stats['successes']
            if self.api_stats['successes'] > 0
            else 0
        )

        success_rate = (
            self.api_stats['successes'] / self.api_stats['requests']
            if self.api_stats['requests'] > 0
            else 1.0
        )

        return {
            'requests': self.api_stats['requests'],
            'successes': self.api_stats['successes'],
            'failures': self.api_stats['failures'],
            'avg_latency': avg_latency,
            'success_rate': success_rate,
            'fallbacks_used': self.api_stats['fallbacks_used']
        }

    def reset_stats(self) -> None:
        """Reset API statistics"""
        self.api_stats = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'total_latency': 0.0,
            'fallbacks_used': 0
        }
        logger.info("API statistics reset")


def with_retry(
    max_retries: int = 3,
    backoff: float = 1.0,
    fallback: Optional[Any] = None
):
    """
    Decorator for adding retry logic to individual methods

    Usage:
        @with_retry(max_retries=3, fallback={'error': 'unavailable'})
        def fetch_data(self):
            # API call here
            pass

    Args:
        max_retries: Maximum retry attempts
        backoff: Initial backoff seconds
        fallback: Fallback value on failure

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if isinstance(self, APIHelper):
                return self.api_call(
                    func,
                    self,
                    *args,
                    max_retries=max_retries,
                    backoff=backoff,
                    fallback=fallback,
                    component_name=func.__name__,
                    **kwargs
                )
            else:
                # Fallback if not APIHelper - just call function
                return func(self, *args, **kwargs)
        return wrapper
    return decorator
