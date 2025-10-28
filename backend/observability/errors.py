"""
DawsOS Sentry Error Tracking

Purpose: Centralized error capture and reporting with Sentry
Updated: 2025-10-22
Priority: P1 (Sprint 1 Week 2 Gate)

Features:
    - Automatic exception capture
    - Context enrichment (user, request, custom tags)
    - Breadcrumb tracking
    - PII filtering (no sensitive data in errors)
    - Sampling rules (don't overwhelm Sentry)

Critical: Never send PII to Sentry
    - Filter user IDs
    - Filter portfolio IDs
    - Filter financial data
    - Filter API keys

Usage:
    from observability.errors import setup_error_tracking, capture_exception

    # Setup once at app startup
    setup_error_tracking(
        dsn="https://...@sentry.io/...",
        environment="production",
    )

    # Capture exceptions with context
    try:
        result = await orchestrator.run(...)
    except Exception as e:
        capture_exception(
            e,
            context={
                "pattern_id": pattern_id,
                "pricing_pack_id": ctx.pricing_pack_id,
            }
        )
        raise
"""

import logging
from typing import Any, Dict, Optional

# Sentry imports (will be optional - gracefully degrade if not installed)
try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.fastapi import FastAPIIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logger = logging.getLogger("DawsOS.Errors")

# Global Sentry initialization state
_sentry_initialized = False


def setup_error_tracking(
    dsn: Optional[str] = None,
    environment: str = "development",
    service_name: str = "dawsos-executor",
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
    enable_logging: bool = True,
) -> None:
    """
    Setup Sentry error tracking.

    Args:
        dsn: Sentry DSN (if None, error tracking disabled)
        environment: Environment name (dev/staging/production)
        service_name: Service name for error grouping
        traces_sample_rate: Percentage of transactions to trace (0.0-1.0)
        profiles_sample_rate: Percentage of transactions to profile (0.0-1.0)
        enable_logging: Enable logging integration (captures ERROR+ logs)
    """
    global _sentry_initialized

    if not SENTRY_AVAILABLE:
        logger.warning(
            "Sentry SDK not installed. Error tracking disabled. "
            "Install with: pip install sentry-sdk[fastapi]"
        )
        return

    if not dsn:
        logger.info("No Sentry DSN provided. Error tracking disabled.")
        return

    if _sentry_initialized:
        logger.warning("Sentry already initialized")
        return

    try:
        # Setup logging integration (if enabled)
        integrations = []

        if enable_logging:
            logging_integration = LoggingIntegration(
                level=logging.INFO,  # Capture INFO and above as breadcrumbs
                event_level=logging.ERROR,  # Send ERROR and above as events
            )
            integrations.append(logging_integration)

        # Add FastAPI integration
        integrations.append(FastAPIIntegration())

        # Initialize Sentry
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=integrations,
            before_send=_before_send,  # Filter PII
            before_breadcrumb=_before_breadcrumb,  # Filter breadcrumb PII
            release=f"{service_name}@1.0.0",
        )

        _sentry_initialized = True

        logger.info(
            f"Sentry error tracking initialized: environment={environment}, "
            f"traces_sample_rate={traces_sample_rate}"
        )

    except Exception as e:
        logger.error(f"Failed to setup Sentry: {e}", exc_info=True)


def capture_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    level: str = "error",
) -> None:
    """
    Capture exception with context and tags.

    Args:
        error: Exception to capture
        context: Additional context dict (filtered for PII)
        tags: Tags for grouping/filtering in Sentry
        level: Error level (error/warning/info)

    Usage:
        try:
            result = await orchestrator.run(...)
        except Exception as e:
            capture_exception(
                e,
                context={
                    "pattern_id": pattern_id,
                    "pricing_pack_id": ctx.pricing_pack_id,
                },
                tags={
                    "component": "orchestrator",
                    "pattern_id": pattern_id,
                }
            )
            raise
    """
    if not _sentry_initialized:
        return

    with sentry_sdk.push_scope() as scope:
        # Set level
        scope.level = level

        # Add tags (for filtering in Sentry UI)
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, str(value))

        # Add context (extra data)
        if context:
            filtered_context = _filter_pii(context)
            for key, value in filtered_context.items():
                scope.set_context(key, value)

        # Capture exception
        sentry_sdk.capture_exception(error)


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Add breadcrumb for debugging context.

    Breadcrumbs are small events that lead up to an error,
    helping understand what happened before the exception.

    Args:
        message: Breadcrumb message
        category: Category for grouping (e.g., "http", "db", "auth")
        level: Level (info/debug/warning/error)
        data: Additional data (filtered for PII)

    Usage:
        add_breadcrumb(
            "Starting pattern execution",
            category="pattern",
            data={"pattern_id": "portfolio_overview"}
        )
    """
    if not _sentry_initialized:
        return

    filtered_data = _filter_pii(data) if data else None

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=filtered_data,
    )


def set_user_context(user_id: str, email: Optional[str] = None) -> None:
    """
    Set user context for error tracking.

    NOTE: Be careful with PII. Only set if user has consented
    and it's necessary for debugging.

    Args:
        user_id: User identifier (hashed, not raw)
        email: User email (optional, only if consented)
    """
    if not _sentry_initialized:
        return

    sentry_sdk.set_user({
        "id": _hash_pii(user_id),  # Hash user ID
        "email": email if email else None,
    })


def set_tags(**tags: str) -> None:
    """
    Set tags for all subsequent errors.

    Tags are used for filtering and grouping in Sentry UI.

    Args:
        **tags: Tag key-value pairs

    Usage:
        set_tags(
            environment="production",
            service="executor",
            version="1.0.0"
        )
    """
    if not _sentry_initialized:
        return

    for key, value in tags.items():
        sentry_sdk.set_tag(key, str(value))


# ============================================================================
# PII Filtering
# ============================================================================


def _filter_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter PII from data before sending to Sentry.

    Removes:
        - User IDs (replaced with hash)
        - Portfolio IDs (replaced with hash)
        - Security IDs
        - Financial amounts
        - API keys
        - Passwords

    Args:
        data: Dict to filter

    Returns:
        Filtered dict
    """
    if not data:
        return {}

    filtered = {}
    pii_keys = {
        "user_id",
        "portfolio_id",
        "security_id",
        "amount",
        "value",
        "cost_basis",
        "api_key",
        "password",
        "token",
        "secret",
    }

    for key, value in data.items():
        # Check if key contains PII
        if any(pii in key.lower() for pii in pii_keys):
            # Hash or redact
            if "id" in key.lower():
                filtered[key] = _hash_pii(str(value))
            else:
                filtered[key] = "[REDACTED]"
        else:
            # Keep non-PII data
            filtered[key] = value

    return filtered


def _hash_pii(value: str) -> str:
    """
    Hash PII value for Sentry.

    Args:
        value: Value to hash

    Returns:
        Hashed value (first 8 chars of hash)
    """
    import hashlib

    return hashlib.sha256(value.encode()).hexdigest()[:8]


def _before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter event before sending to Sentry.

    This is called for every error event before it's sent.
    Use this to filter out sensitive data or ignore certain errors.

    Args:
        event: Sentry event dict
        hint: Additional context

    Returns:
        Filtered event or None to drop event
    """
    # Filter PII from extra context
    if "extra" in event:
        event["extra"] = _filter_pii(event["extra"])

    # Filter PII from request data
    if "request" in event and "data" in event["request"]:
        event["request"]["data"] = _filter_pii(event["request"]["data"])

    # Drop errors from health checks (too noisy)
    if "request" in event and "url" in event["request"]:
        url = event["request"]["url"]
        if "/health" in url or "/metrics" in url:
            return None  # Drop event

    return event


def _before_breadcrumb(crumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter breadcrumb before adding to Sentry.

    Args:
        crumb: Breadcrumb dict
        hint: Additional context

    Returns:
        Filtered breadcrumb or None to drop
    """
    # Filter PII from breadcrumb data
    if "data" in crumb:
        crumb["data"] = _filter_pii(crumb["data"])

    # Drop breadcrumbs from health checks
    if crumb.get("category") == "http" and crumb.get("data", {}).get("url"):
        url = crumb["data"]["url"]
        if "/health" in url or "/metrics" in url:
            return None  # Drop breadcrumb

    return crumb


# ============================================================================
# Integration Helpers
# ============================================================================


def configure_fastapi_integration(app):
    """
    Configure FastAPI with Sentry integration.

    Args:
        app: FastAPI application

    Usage:
        from fastapi import FastAPI
        from observability.errors import configure_fastapi_integration

        app = FastAPI()
        configure_fastapi_integration(app)
    """
    if not _sentry_initialized:
        logger.warning("Sentry not initialized. Cannot configure FastAPI.")
        return

    # FastAPI integration is already setup in init
    # This is just a no-op for consistency
    logger.info("FastAPI configured with Sentry integration")


# ============================================================================
# Example Usage (for documentation)
# ============================================================================

if __name__ == "__main__":
    # Setup error tracking
    setup_error_tracking(
        dsn="https://example@sentry.io/123456",  # Replace with real DSN
        environment="development",
    )

    # Example: Capture exception with context
    try:
        raise ValueError("Test error")
    except Exception as e:
        capture_exception(
            e,
            context={
                "pattern_id": "test_pattern",
                "user_id": "user_123",  # Will be hashed
            },
            tags={
                "component": "test",
            },
        )
        print("Exception captured")

    # Example: Add breadcrumb
    add_breadcrumb(
        "Test breadcrumb",
        category="test",
        data={"test_key": "test_value"},
    )
    print("Breadcrumb added")

    print("Error tracking configured")
