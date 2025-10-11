"""Base Pydantic models for DawsOS API validation.

This module provides generic response wrappers and common patterns for all API integrations.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Generic, TypeVar, Optional, Dict, Any, List

# Type variable for generic responses
T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """Generic validated API response wrapper.

    Used to wrap all external API responses with consistent metadata and validation.

    Example:
        >>> response = APIResponse[StockQuote](
        ...     data=quote,
        ...     source='live',
        ...     timestamp=datetime.now()
        ... )
    """
    model_config = ConfigDict(frozen=True)  # Immutable

    data: T = Field(..., description="The validated response data")
    source: str = Field(..., description="Data source: 'live', 'cache', or 'fallback'")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the data was fetched")
    cache_age_seconds: int = Field(default=0, ge=0, description="Age of cached data in seconds")
    error: Optional[str] = Field(default=None, description="Error message if request failed")


class DataQuality(BaseModel):
    """Data quality metadata for validation results.

    Provides transparency about data completeness and freshness.
    """
    model_config = ConfigDict(frozen=True)

    quality: str = Field(..., description="Quality level: 'high', 'medium', 'low', 'none'")
    completeness: float = Field(..., ge=0.0, le=1.0, description="Data completeness ratio (0-1)")
    freshness_hours: Optional[float] = Field(None, ge=0, description="Hours since last update")
    validation_errors: List[str] = Field(default_factory=list, description="Any validation warnings")

    @property
    def is_valid(self) -> bool:
        """Check if data quality is acceptable (high or medium)."""
        return self.quality in ['high', 'medium']


class ValidationError(BaseModel):
    """Structured validation error for clear error reporting.

    When Pydantic validation fails, this provides user-friendly error details.
    """
    model_config = ConfigDict(frozen=True)

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Human-readable error message")
    invalid_value: Optional[Any] = Field(None, description="The value that failed validation")
    expected_type: Optional[str] = Field(None, description="Expected data type or constraint")


class HealthStatus(BaseModel):
    """API health status for observability.

    Tracks API availability, rate limits, and degradation.
    """
    model_config = ConfigDict(frozen=True)

    api_name: str = Field(..., description="API name (e.g., 'FRED', 'FMP')")
    is_configured: bool = Field(..., description="Whether API key is configured")
    is_available: bool = Field(..., description="Whether API is currently reachable")
    rate_limit_remaining: Optional[int] = Field(None, ge=0, description="Remaining API calls")
    fallback_count: int = Field(default=0, ge=0, description="Number of fallback uses")
    warnings: List[str] = Field(default_factory=list, description="Any health warnings")
    last_check: datetime = Field(default_factory=datetime.now, description="Last health check time")


class CacheMetadata(BaseModel):
    """Cache metadata for transparent caching.

    Tracks cache hits, misses, and expiration.
    """
    model_config = ConfigDict(frozen=True)

    cache_key: str = Field(..., description="Unique cache key")
    is_cached: bool = Field(..., description="Whether data came from cache")
    is_stale: bool = Field(default=False, description="Whether cached data is expired")
    cache_time: Optional[datetime] = Field(None, description="When data was cached")
    ttl_seconds: int = Field(..., gt=0, description="Time-to-live in seconds")

    @property
    def age_seconds(self) -> Optional[int]:
        """Calculate cache age in seconds."""
        if self.cache_time:
            return int((datetime.now() - self.cache_time).total_seconds())
        return None

    @property
    def is_fresh(self) -> bool:
        """Check if cache is fresh (within TTL)."""
        age = self.age_seconds
        return age is not None and age < self.ttl_seconds


class Observation(BaseModel):
    """Single time-series observation (generic).

    Used for any time-series data (economic indicators, stock prices, etc.)
    """
    date: str = Field(..., description="Observation date in YYYY-MM-DD format")
    value: float = Field(..., description="Observed value")

    model_config = ConfigDict(frozen=True)


class TimeSeriesMetadata(BaseModel):
    """Metadata for time-series data.

    Provides context about the time series (units, frequency, etc.)
    """
    series_id: str = Field(..., description="Unique series identifier")
    name: str = Field(..., description="Human-readable series name")
    units: str = Field(..., description="Units of measurement")
    frequency: str = Field(..., description="Data frequency (Daily, Monthly, Quarterly, etc.)")
    start_date: str = Field(..., description="First available date")
    end_date: str = Field(..., description="Last available date")
    observations_count: int = Field(..., ge=0, description="Number of observations")

    model_config = ConfigDict(frozen=True)


# Package exports
__all__ = [
    'APIResponse',
    'DataQuality',
    'ValidationError',
    'HealthStatus',
    'CacheMetadata',
    'Observation',
    'TimeSeriesMetadata',
]
