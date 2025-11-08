"""
HTTP Status Codes with Domain Context

Domain: API error handling, client-server communication
Sources: RFC 7231, HTTP specification
Identified by: Replit analysis (15+ HTTP status code instances) + Constants audit 2025-11-07

This module provides named constants for HTTP status codes used throughout
the DawsOS API, improving code readability and reducing magic numbers.

Cleanup History:
- 2025-11-07: Removed 4 unused aggregate lists
  - Removed: SUCCESS_STATUS_CODES (unused)
  - Removed: CLIENT_ERROR_STATUS_CODES (unused)
  - Removed: SERVER_ERROR_STATUS_CODES (unused)
  - Removed: STATUS_CODE_DESCRIPTIONS (unused)
  - Kept: All individual status codes (47% utilization, but future-proof)
  - Kept: RETRYABLE_STATUS_CODES (canonical source, used in retry logic)
"""

# =============================================================================
# SUCCESS RESPONSES (2xx)
# =============================================================================

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_202_ACCEPTED = 202
HTTP_204_NO_CONTENT = 204

# =============================================================================
# CLIENT ERRORS (4xx)
# =============================================================================

HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429

# =============================================================================
# SERVER ERRORS (5xx)
# =============================================================================

HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_502_BAD_GATEWAY = 502
HTTP_503_SERVICE_UNAVAILABLE = 503
HTTP_504_GATEWAY_TIMEOUT = 504

# =============================================================================
# RETRY LOGIC (canonical source)
# =============================================================================

# Status codes that warrant automatic retry
# Note: This is the canonical definition (was duplicate in integration.py)
RETRYABLE_STATUS_CODES = [429, 500, 502, 503, 504]

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Success codes
    "HTTP_200_OK",
    "HTTP_201_CREATED",
    "HTTP_202_ACCEPTED",
    "HTTP_204_NO_CONTENT",
    # Client error codes
    "HTTP_400_BAD_REQUEST",
    "HTTP_401_UNAUTHORIZED",
    "HTTP_403_FORBIDDEN",
    "HTTP_404_NOT_FOUND",
    "HTTP_422_UNPROCESSABLE_ENTITY",
    "HTTP_429_TOO_MANY_REQUESTS",
    # Server error codes
    "HTTP_500_INTERNAL_SERVER_ERROR",
    "HTTP_502_BAD_GATEWAY",
    "HTTP_503_SERVICE_UNAVAILABLE",
    "HTTP_504_GATEWAY_TIMEOUT",
    # Retry logic
    "RETRYABLE_STATUS_CODES",
]
