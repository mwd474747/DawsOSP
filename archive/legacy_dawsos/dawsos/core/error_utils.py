"""
Error handling utilities for DawsOS.

Provides standard error handling patterns including:
- with_logging(): Decorator for automatic error logging
- safe_get(): Safe execution with default fallback
- retry_on_failure(): Retry logic with exponential backoff

See docs/ErrorHandlingGuide.md for usage patterns.
"""

import logging
import time
from typing import Any, Callable, Optional, TypeVar, Tuple, Type
from functools import wraps

T = TypeVar('T')

logger = logging.getLogger(__name__)


def with_logging(operation_name: str, logger_instance: logging.Logger):
    """
    Decorator for consistent error logging.

    Automatically logs any exceptions raised by the decorated function
    with the specified operation name and full stack trace.

    Args:
        operation_name: Name of the operation for logging context
        logger_instance: Logger instance to use for error messages

    Returns:
        Decorator function

    Example:
        >>> @with_logging("calculate_metrics", logger)
        >>> def calculate_metrics(data):
        >>>     return process(data)

    See: Pattern 2 in docs/ErrorHandlingGuide.md
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger_instance.error(
                    f"Error in {operation_name}: {e}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def safe_get(
    func: Callable[[], T],
    default: T = None,
    error_types: Tuple[Type[Exception], ...] = (Exception,),
    logger_instance: Optional[logging.Logger] = None
) -> T:
    """
    Safely execute function, return default on error.

    Executes the provided function and catches specified exception types.
    Returns the default value if any of the specified exceptions occur.

    Args:
        func: Function to execute (no arguments)
        default: Value to return on error (default: None)
        error_types: Tuple of exception types to catch (default: all exceptions)
        logger_instance: Optional logger for warning messages

    Returns:
        Function result on success, default value on error

    Example:
        >>> data = safe_get(
        >>>     lambda: fetch_data(symbol),
        >>>     default={},
        >>>     error_types=(ValueError, KeyError),
        >>>     logger_instance=logger
        >>> )

    See: Pattern 1 in docs/ErrorHandlingGuide.md
    """
    try:
        return func()
    except error_types as e:
        if logger_instance:
            logger_instance.warning(f"Safe get failed: {e}")
        return default


def require_graph(
    graph: Any,
    logger_instance: logging.Logger,
    return_value: Any = None,
    error_dict: bool = False
) -> Optional[Any]:
    """
    Validate graph availability, return default on failure.

    Consolidated pattern for graph validation across agents and actions.
    Replaces 31+ duplicate "if not self.graph:" checks.

    Args:
        graph: Graph instance to check
        logger_instance: Logger for warnings
        return_value: Value to return if graph unavailable (default: None)
        error_dict: If True, return error dict instead of return_value

    Returns:
        None if graph is available (continue execution),
        return_value or error dict if graph is unavailable

    Example:
        >>> # Before (3 lines):
        >>> if not self.graph:
        >>>     self.logger.warning("Graph not available")
        >>>     return []
        >>>
        >>> # After (2 lines):
        >>> if err := require_graph(self.graph, self.logger, return_value=[]):
        >>>     return err

    See: Safe refactoring Phase 2
    """
    if not graph:
        logger_instance.warning("Graph not available for operation")
        if error_dict:
            return {"error": "Graph not available", "success": False}
        return return_value
    return None  # Graph is available, continue execution


def retry_on_failure(
    func: Callable[[], T],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger_instance: Optional[logging.Logger] = None
) -> T:
    """
    Retry function with exponential backoff.

    Executes the provided function with automatic retry logic for transient
    failures. Uses exponential backoff between attempts.

    Args:
        func: Function to execute (no arguments)
        max_attempts: Maximum number of attempts (default: 3)
        delay: Initial delay in seconds (default: 1.0)
        backoff: Backoff multiplier (default: 2.0 for exponential)
        exceptions: Tuple of exception types to retry (default: all exceptions)
        logger_instance: Optional logger for retry messages

    Returns:
        Function result on success

    Raises:
        Last exception if all attempts fail

    Example:
        >>> result = retry_on_failure(
        >>>     lambda: api_call(endpoint),
        >>>     max_attempts=3,
        >>>     delay=1.0,
        >>>     exceptions=(TimeoutError, ConnectionError),
        >>>     logger_instance=logger
        >>> )

    Retry schedule with default parameters:
        - Attempt 1: immediate
        - Attempt 2: after 1.0s
        - Attempt 3: after 2.0s
        - Total time: ~3.0s

    See: Pattern 4 in docs/ErrorHandlingGuide.md
    """
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            if attempt == max_attempts - 1:
                # Final attempt failed
                if logger_instance:
                    logger_instance.error(
                        f"Failed after {max_attempts} attempts: {e}"
                    )
                raise

            # Calculate wait time with exponential backoff
            wait_time = delay * (backoff ** attempt)

            if logger_instance:
                logger_instance.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed, "
                    f"retrying in {wait_time:.1f}s: {e}"
                )

            time.sleep(wait_time)

    # Should never reach here, but satisfies type checker
    raise RuntimeError("Retry logic error: exhausted attempts without raising")


def safe_execute_with_cleanup(
    operation: Callable[[], T],
    cleanup: Callable[[], None],
    operation_name: str = "operation",
    logger_instance: Optional[logging.Logger] = None
) -> Optional[T]:
    """
    Execute operation with guaranteed cleanup, even on error.

    Ensures cleanup function is always called, regardless of whether
    the operation succeeds or fails.

    Args:
        operation: Function to execute
        cleanup: Function to call for cleanup (always executed)
        operation_name: Name for logging context
        logger_instance: Optional logger for error messages

    Returns:
        Operation result on success, None on error

    Example:
        >>> def acquire_resource():
        >>>     return open_connection()
        >>>
        >>> def use_resource(conn):
        >>>     return conn.execute(query)
        >>>
        >>> def release_resource(conn):
        >>>     conn.close()
        >>>
        >>> conn = acquire_resource()
        >>> result = safe_execute_with_cleanup(
        >>>     lambda: use_resource(conn),
        >>>     lambda: release_resource(conn),
        >>>     operation_name="database_query",
        >>>     logger_instance=logger
        >>> )

    See: Pattern 3 in docs/ErrorHandlingGuide.md
    """
    try:
        return operation()
    except Exception as e:
        if logger_instance:
            logger_instance.error(
                f"Error in {operation_name}: {e}",
                exc_info=True
            )
        return None
    finally:
        try:
            cleanup()
        except Exception as e:
            if logger_instance:
                logger_instance.error(
                    f"Error during cleanup of {operation_name}: {e}",
                    exc_info=True
                )


def with_context_errors(
    context_info: str,
    logger_instance: logging.Logger,
    return_error_dict: bool = True
):
    """
    Decorator for context-rich error messages.

    Wraps functions to provide detailed error information including
    the operation context. Useful for user-facing operations.

    Args:
        context_info: Context string (e.g., "processing {symbol}")
        logger_instance: Logger instance for error messages
        return_error_dict: If True, return error dict instead of raising

    Returns:
        Decorator function

    Example:
        >>> @with_context_errors("calculating DCF for {symbol}", logger)
        >>> def calculate_dcf(symbol, financials):
        >>>     return perform_calculation(financials)

    See: Pattern 5 in docs/ErrorHandlingGuide.md
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                # Expected validation errors
                error_msg = f"Validation failed: {context_info} - {e}"
                logger_instance.error(error_msg)
                if return_error_dict:
                    return {
                        "error": f"Validation failed",
                        "context": context_info,
                        "details": str(e)
                    }
                raise
            except Exception as e:
                # Unexpected errors
                error_msg = f"Unexpected error: {context_info} - {e}"
                logger_instance.error(error_msg, exc_info=True)
                if return_error_dict:
                    return {
                        "error": "Internal error",
                        "context": context_info,
                        "details": "Please contact support"
                    }
                raise
        return wrapper
    return decorator


# Convenience function for common use case
def log_and_return_none(
    func: Callable[[], T],
    context: str,
    logger_instance: logging.Logger
) -> Optional[T]:
    """
    Execute function, log errors, return None on failure.

    Convenience wrapper for the common pattern of trying an operation
    and returning None if it fails.

    Args:
        func: Function to execute
        context: Context string for error messages
        logger_instance: Logger instance

    Returns:
        Function result or None

    Example:
        >>> data = log_and_return_none(
        >>>     lambda: fetch_data(symbol),
        >>>     f"fetching data for {symbol}",
        >>>     logger
        >>> )
    """
    try:
        return func()
    except Exception as e:
        logger_instance.error(f"Error {context}: {e}", exc_info=True)
        return None
