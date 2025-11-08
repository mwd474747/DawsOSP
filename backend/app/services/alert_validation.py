"""
Alert Service Input Validation

Purpose: Validate inputs for alert service to prevent SQL injection and other security issues
Updated: 2025-01-15
Priority: P0 (Critical - Security)

Features:
    - Whitelist validation for SQL column names
    - UUID validation
    - Symbol validation
    - Metric name validation
"""

from typing import Set, Optional
import re
from uuid import UUID

from app.core.exceptions import (
    ValidationError,
    InvalidUUIDError,
    InvalidValueError,
)


# Whitelist of valid column names for portfolio_metrics table
VALID_PORTFOLIO_METRIC_COLUMNS: Set[str] = {
    # Performance metrics
    "twr_1d", "twr_mtd", "twr_ytd", "twr_1y", "twr_3y", "twr_5y",
    "mwr_1y", "mwr_3y", "mwr_5y",
    # Risk metrics
    "max_drawdown_1y", "max_drawdown_3y", "max_drawdown_5y",
    "volatility_1y", "volatility_3y", "volatility_5y",
    "sharpe_1y", "sharpe_3y", "sharpe_5y",
    "sortino_1y", "sortino_3y", "sortino_5y",
    "beta_1y", "beta_3y", "beta_5y",
    "tracking_error_1y", "tracking_error_3y", "tracking_error_5y",
    # Attribution metrics
    "attribution_1y", "attribution_3y", "attribution_5y",
    # Other metrics
    "asof_date", "portfolio_id",
}

# Whitelist of valid column names for security_ratings table
VALID_RATING_COLUMNS: Set[str] = {
    "dividend_safety",
    "quality_score",
    "moat_score",
    "value_score",
    "growth_score",
    "momentum_score",
    "symbol",
    "asof_date",
}

# Whitelist of valid column names for security_prices table
VALID_PRICE_COLUMNS: Set[str] = {
    "close",
    "open",
    "high",
    "low",
    "volume",
    "change_pct",
    "symbol",
    "asof_date",
}


def validate_portfolio_metric_name(metric_name: str, raise_on_error: bool = False) -> bool:
    """
    Validate portfolio metric name against whitelist.
    
    Args:
        metric_name: Metric name to validate
        raise_on_error: If True, raise InvalidValueError instead of returning False
        
    Returns:
        True if valid, False otherwise (unless raise_on_error=True)
        
    Raises:
        InvalidValueError: If raise_on_error=True and metric name is invalid
    """
    if not metric_name or not isinstance(metric_name, str):
        if raise_on_error:
            raise InvalidValueError(metric_name, "metric_name", "Metric name must be a non-empty string")
        return False
    if metric_name not in VALID_PORTFOLIO_METRIC_COLUMNS:
        if raise_on_error:
            raise InvalidValueError(
                metric_name,
                "metric_name",
                f"Invalid portfolio metric name. Must be one of: {', '.join(sorted(VALID_PORTFOLIO_METRIC_COLUMNS))}"
            )
        return False
    return True


def validate_rating_metric_name(metric_name: str) -> bool:
    """
    Validate rating metric name against whitelist.
    
    Args:
        metric_name: Metric name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not metric_name or not isinstance(metric_name, str):
        return False
    return metric_name in VALID_RATING_COLUMNS


def validate_price_metric_name(metric_name: str) -> bool:
    """
    Validate price metric name against whitelist.
    
    Args:
        metric_name: Metric name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not metric_name or not isinstance(metric_name, str):
        return False
    return metric_name in VALID_PRICE_COLUMNS


def validate_uuid(uuid_string: Optional[str], raise_on_error: bool = False) -> bool:
    """
    Validate UUID string format.
    
    Args:
        uuid_string: UUID string to validate
        raise_on_error: If True, raise InvalidUUIDError instead of returning False
        
    Returns:
        True if valid UUID format, False otherwise (unless raise_on_error=True)
        
    Raises:
        InvalidUUIDError: If raise_on_error=True and UUID is invalid
    """
    if not uuid_string:
        if raise_on_error:
            raise InvalidUUIDError("", "uuid")
        return False
    try:
        UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        if raise_on_error:
            raise InvalidUUIDError(uuid_string, "uuid")
        return False


def validate_symbol(symbol: Optional[str]) -> bool:
    """
    Validate security symbol format.
    
    Args:
        symbol: Symbol to validate
        
    Returns:
        True if valid symbol format, False otherwise
    """
    if not symbol or not isinstance(symbol, str):
        return False
    # Symbols should be uppercase alphanumeric, 1-10 characters
    # Allow dots for some symbols (e.g., "BRK.B")
    pattern = re.compile(r'^[A-Z0-9.]{1,10}$')
    return bool(pattern.match(symbol.upper()))


def sanitize_column_name(column_name: str) -> str:
    """
    Sanitize column name to prevent SQL injection.
    
    This function ensures column names only contain safe characters.
    However, it should NOT be used as a substitute for whitelist validation.
    
    Args:
        column_name: Column name to sanitize
        
    Returns:
        Sanitized column name (only alphanumeric and underscores)
    """
    if not column_name or not isinstance(column_name, str):
        raise ValueError("Column name must be a non-empty string")
    
    # Remove any characters that aren't alphanumeric or underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', column_name)
    
    if not sanitized:
        raise ValueError("Column name contains no valid characters")
    
    return sanitized

