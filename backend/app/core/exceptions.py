"""
DawsOS Exception Hierarchy

This module defines the exception hierarchy for DawsOS.
All exceptions inherit from DawsOSException for easy catching.
"""

from typing import Optional, Dict, Any


# ============================================================================
# Base Exception
# ============================================================================

class DawsOSException(Exception):
    """Base exception for all DawsOS exceptions."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.retryable = retryable
    
    def __str__(self):
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "retryable": self.retryable,
        }


# ============================================================================
# Database Exceptions
# ============================================================================

class DatabaseError(DawsOSException):
    """Base exception for database errors."""
    pass


class ConnectionError(DatabaseError):
    """Database connection error."""
    
    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(message, retryable=True, **kwargs)


class QueryError(DatabaseError):
    """Database query error."""
    
    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if query:
            details["query"] = query
        super().__init__(message, details=details, **kwargs)


class TransactionError(DatabaseError):
    """Database transaction error."""
    
    def __init__(self, message: str = "Transaction failed", **kwargs):
        super().__init__(message, retryable=True, **kwargs)


class RLSViolationError(DatabaseError):
    """Row-level security policy violation."""
    
    def __init__(self, message: str = "Access denied by RLS policy", **kwargs):
        super().__init__(message, retryable=False, **kwargs)


class DataError(DatabaseError):
    """Database data error (constraint violation, etc.)."""
    
    def __init__(self, message: str, constraint: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if constraint:
            details["constraint"] = constraint
        super().__init__(message, details=details, **kwargs)


# ============================================================================
# Validation Exceptions
# ============================================================================

class ValidationError(DawsOSException):
    """Base exception for validation errors."""
    pass


class MissingFieldError(ValidationError):
    """Missing required field."""
    
    def __init__(self, field_name: str, **kwargs):
        message = f"Missing required field: {field_name}"
        details = kwargs.get("details", {})
        details["field"] = field_name
        super().__init__(message, details=details, **kwargs)


class InvalidUUIDError(ValidationError):
    """Invalid UUID format."""
    
    def __init__(self, value: str, field_name: str = "id", **kwargs):
        message = f"Invalid UUID format for {field_name}: {value}"
        details = kwargs.get("details", {})
        details["value"] = value
        details["field"] = field_name
        super().__init__(message, details=details, **kwargs)


class InvalidDateError(ValidationError):
    """Invalid date format."""
    
    def __init__(self, value: str, field_name: str = "date", **kwargs):
        message = f"Invalid date format for {field_name}: {value}"
        details = kwargs.get("details", {})
        details["value"] = value
        details["field"] = field_name
        super().__init__(message, details=details, **kwargs)


class InvalidTypeError(ValidationError):
    """Invalid type."""
    
    def __init__(self, value: Any, expected_type: type, field_name: str = "value", **kwargs):
        message = f"Invalid type for {field_name}: expected {expected_type.__name__}, got {type(value).__name__}"
        details = kwargs.get("details", {})
        details["value"] = str(value)
        details["expected_type"] = expected_type.__name__
        details["actual_type"] = type(value).__name__
        details["field"] = field_name
        super().__init__(message, details=details, **kwargs)


class InvalidValueError(ValidationError):
    """Invalid value (out of range, etc.)."""
    
    def __init__(self, value: Any, field_name: str, reason: str, **kwargs):
        message = f"Invalid value for {field_name}: {reason}"
        details = kwargs.get("details", {})
        details["value"] = str(value)
        details["field"] = field_name
        details["reason"] = reason
        super().__init__(message, details=details, **kwargs)


# ============================================================================
# API Exceptions
# ============================================================================

class APIError(DawsOSException):
    """Base exception for API errors."""
    pass


class ExternalAPIError(APIError):
    """External API error."""
    
    def __init__(self, message: str, api_name: str, status_code: Optional[int] = None, **kwargs):
        details = kwargs.get("details", {})
        details["api_name"] = api_name
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details=details, retryable=True, **kwargs)


class NetworkError(APIError):
    """Network error."""
    
    def __init__(self, message: str = "Network error occurred", **kwargs):
        super().__init__(message, retryable=True, **kwargs)


class TimeoutError(APIError):
    """Timeout error."""
    
    def __init__(self, message: str = "Request timed out", timeout: Optional[float] = None, **kwargs):
        details = kwargs.get("details", {})
        if timeout:
            details["timeout"] = timeout
        super().__init__(message, details=details, retryable=True, **kwargs)


class RateLimitError(APIError):
    """Rate limit error."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, **kwargs):
        details = kwargs.get("details", {})
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, details=details, retryable=True, **kwargs)


class AuthenticationError(APIError):
    """API authentication error."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, retryable=False, **kwargs)


# ============================================================================
# Business Logic Exceptions
# ============================================================================

class BusinessLogicError(DawsOSException):
    """Base exception for business logic errors."""
    pass


class PortfolioNotFoundError(BusinessLogicError):
    """Portfolio not found."""
    
    def __init__(self, portfolio_id: str, **kwargs):
        message = f"Portfolio not found: {portfolio_id}"
        details = kwargs.get("details", {})
        details["portfolio_id"] = portfolio_id
        super().__init__(message, details=details, **kwargs)


class SecurityNotFoundError(BusinessLogicError):
    """Security not found."""
    
    def __init__(self, security_id: str, **kwargs):
        message = f"Security not found: {security_id}"
        details = kwargs.get("details", {})
        details["security_id"] = security_id
        super().__init__(message, details=details, **kwargs)


class PricingPackNotFoundError(BusinessLogicError):
    """Pricing pack not found."""
    
    def __init__(self, pack_id: str, **kwargs):
        message = f"Pricing pack not found: {pack_id}"
        details = kwargs.get("details", {})
        details["pack_id"] = pack_id
        super().__init__(message, details=details, **kwargs)


class InsufficientDataError(BusinessLogicError):
    """Insufficient data for operation."""
    
    def __init__(self, message: str, required: Optional[Dict[str, Any]] = None, **kwargs):
        details = kwargs.get("details", {})
        if required:
            details["required"] = required
        super().__init__(message, details=details, **kwargs)


# ============================================================================
# Programming Errors (Should Not Be Caught)
# ============================================================================

# These should NOT be caught with broad exception handlers
# They indicate bugs that should be fixed, not handled

# AttributeError - Missing attribute (bug)
# KeyError - Missing dictionary key (bug)
# TypeError - Wrong type (bug)
# IndexError - Out of bounds (bug)
# NameError - Undefined variable (bug)

# These should be re-raised immediately to surface bugs


# ============================================================================
# Unexpected Errors
# ============================================================================

class UnexpectedError(DawsOSException):
    """Truly unexpected error that should be investigated."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None, **kwargs):
        details = kwargs.get("details", {})
        if original_error:
            details["original_error"] = str(original_error)
            details["original_error_type"] = type(original_error).__name__
        super().__init__(message, details=details, **kwargs)

