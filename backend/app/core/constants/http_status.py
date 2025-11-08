"""
HTTP Status Codes with Domain Context

Domain: API error handling, client-server communication
Sources: RFC 7231, HTTP specification
Identified by: Replit analysis (15+ HTTP status code instances)

This module provides named constants for HTTP status codes used throughout
the DawsOS API, improving code readability and reducing magic numbers.
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
# STATUS CODE CATEGORIES
# =============================================================================

SUCCESS_STATUS_CODES = [200, 201, 202, 204]
CLIENT_ERROR_STATUS_CODES = [400, 401, 403, 404, 422, 429]
SERVER_ERROR_STATUS_CODES = [500, 502, 503, 504]
RETRYABLE_STATUS_CODES = [429, 500, 502, 503, 504]

# =============================================================================
# HUMAN-READABLE DESCRIPTIONS
# =============================================================================

STATUS_CODE_DESCRIPTIONS = {
    200: "Success",
    201: "Resource created",
    202: "Accepted for processing",
    204: "Success with no content",
    400: "Invalid request",
    401: "Authentication required",
    403: "Permission denied",
    404: "Resource not found",
    422: "Validation error",
    429: "Rate limit exceeded",
    500: "Server error",
    502: "Bad gateway",
    503: "Service temporarily unavailable",
    504: "Gateway timeout",
}

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
    # Categories
    "SUCCESS_STATUS_CODES",
    "CLIENT_ERROR_STATUS_CODES",
    "SERVER_ERROR_STATUS_CODES",
    "RETRYABLE_STATUS_CODES",
    # Descriptions
    "STATUS_CODE_DESCRIPTIONS",
]
