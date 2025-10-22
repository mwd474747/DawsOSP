"""Pydantic models for FRED economic data validation.

Validates Federal Reserve Economic Data (FRED) API responses to ensure data integrity
and prevent format incompatibility issues.

Reference: https://api.stlouisfed.org/docs/fred/
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Optional, Any
from datetime import datetime

from models.base import Observation, TimeSeriesMetadata, HealthStatus


class FREDObservation(Observation):
    """FRED-specific observation with validation.

    Extends base Observation with FRED-specific constraints.

    Example:
        >>> obs = FREDObservation(date='2025-01-01', value=27500.0)
        >>> print(obs.value)
        27500.0
    """
    model_config = ConfigDict(frozen=True)

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Ensure date is in YYYY-MM-DD format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}")

    @field_validator('value')
    @classmethod
    def validate_value_finite(cls, v: float) -> float:
        """Ensure value is a finite number (not NaN or Inf)."""
        if not isinstance(v, (int, float)):
            raise ValueError(f"Value must be numeric, got: {type(v)}")
        if v != v:  # NaN check
            raise ValueError("Value cannot be NaN")
        if abs(v) == float('inf'):
            raise ValueError("Value cannot be infinite")
        return float(v)


class SeriesData(BaseModel):
    """Individual FRED series data with full metadata.

    Represents a single economic indicator (GDP, CPI, etc.) with all observations
    and metadata from FredDataCapability.

    Example:
        >>> series = SeriesData(
        ...     series_id='GDP',
        ...     name='Gross Domestic Product',
        ...     units='Billions of Dollars',
        ...     frequency='Quarterly',
        ...     observations=[...],
        ...     latest_value=27500.0,
        ...     latest_date='2025-01-01'
        ... )
    """

    series_id: str = Field(..., description="FRED series ID (e.g., 'GDP', 'CPIAUCSL')")
    name: str = Field(..., description="Human-readable series name")
    units: str = Field(..., description="Units of measurement")
    frequency: str = Field(..., description="Data frequency (Daily, Monthly, Quarterly, Annual)")
    observations: List[FREDObservation] = Field(..., min_length=1, description="Time series observations")
    latest_value: float = Field(..., description="Most recent observation value")
    latest_date: str = Field(..., description="Date of most recent observation")

    # Optional metadata
    seasonal_adjustment: Optional[str] = Field(None, description="Seasonal adjustment type")
    notes: Optional[str] = Field(None, description="Series notes/description")

    # Cache metadata (use aliases to accept underscore-prefixed fields from capability)
    cached: Optional[bool] = Field(None, alias='_cached', description="Whether data came from cache")
    stale: Optional[bool] = Field(None, alias='_stale', description="Whether cached data is expired")
    cache_age_days: Optional[float] = Field(None, alias='_cache_age_days', ge=0, description="Age of cache in days")

    model_config = ConfigDict(frozen=True, populate_by_name=True)  # Allow both name and alias

    @field_validator('observations')
    @classmethod
    def validate_observations_non_empty(cls, v: List[FREDObservation]) -> List[FREDObservation]:
        """Ensure at least one observation exists."""
        if not v or len(v) == 0:
            raise ValueError("Series must have at least one observation")
        return v

    @field_validator('latest_value')
    @classmethod
    def validate_latest_matches_observations(cls, v: float, info) -> float:
        """Ensure latest_value matches the last observation."""
        if 'observations' in info.data and info.data['observations']:
            last_obs = info.data['observations'][-1]
            if abs(v - last_obs.value) > 0.01:  # Allow small floating point differences
                raise ValueError(
                    f"latest_value ({v}) doesn't match last observation ({last_obs.value})"
                )
        return v

    @field_validator('frequency')
    @classmethod
    def validate_frequency_known(cls, v: str) -> str:
        """Ensure frequency is a known FRED type."""
        valid_frequencies = [
            'Daily', 'Weekly', 'Biweekly', 'Monthly', 'Quarterly',
            'Semiannual', 'Annual', 'Unknown'
        ]
        if v not in valid_frequencies:
            # Don't fail, but warn
            return 'Unknown'
        return v


class EconomicDataResponse(BaseModel):
    """Complete FRED economic data response from FredDataCapability.

    This is the main response structure from fetch_economic_indicators() and should
    validate against the actual capability output format.

    Example:
        >>> response = EconomicDataResponse(
        ...     series={'GDP': series_data},
        ...     source='live',
        ...     timestamp='2025-01-01T00:00:00',
        ...     cache_age_seconds=0,
        ...     health={...}
        ... )
        >>> print(response.source)
        'live'
    """
    series: Dict[str, SeriesData] = Field(..., description="Dictionary of series data keyed by series_id")
    source: str = Field(..., description="Data source: 'live', 'cache', or 'fallback'")
    timestamp: str = Field(..., description="ISO timestamp when data was fetched")
    cache_age_seconds: int = Field(..., ge=0, description="Age of cached data in seconds")
    health: Dict[str, Any] = Field(..., description="API health status")

    # Optional metadata (use aliases to accept underscore-prefixed fields from capability)
    metadata: Optional[Dict[str, Any]] = Field(None, alias='_metadata', description="Additional fetch context")
    warning: Optional[str] = Field(None, alias='_warning', description="Warning message if using degraded data")

    model_config = ConfigDict(frozen=True, populate_by_name=True)  # Allow both name and alias

    @field_validator('series')
    @classmethod
    def validate_series_non_empty(cls, v: Dict[str, SeriesData]) -> Dict[str, SeriesData]:
        """Ensure at least one series exists."""
        if not v or len(v) == 0:
            raise ValueError("Response must contain at least one series")
        return v

    @field_validator('source')
    @classmethod
    def validate_source_known(cls, v: str) -> str:
        """Ensure source is one of the expected values."""
        valid_sources = ['live', 'cache', 'fallback', 'error']
        if v not in valid_sources:
            raise ValueError(f"Source must be one of {valid_sources}, got: {v}")
        return v

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp_iso(cls, v: str) -> str:
        """Ensure timestamp is valid ISO format."""
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Timestamp must be ISO format, got: {v}")

    @property
    def total_observations(self) -> int:
        """Total number of observations across all series."""
        return sum(len(s.observations) for s in self.series.values())

    @property
    def data_quality(self) -> str:
        """Determine overall data quality based on source and errors."""
        if self.source == 'live':
            return 'high'
        elif self.source == 'cache':
            return 'medium'
        elif self.source == 'fallback':
            return 'low'
        else:
            return 'none'


class FREDHealthStatus(HealthStatus):
    """FRED-specific API health status.

    Extends base HealthStatus with FRED-specific metrics.
    """
    model_config = ConfigDict(frozen=True)

    cache_hits: int = Field(default=0, ge=0, description="Number of cache hits")
    cache_misses: int = Field(default=0, ge=0, description="Number of cache misses")
    cached_items: int = Field(default=0, ge=0, description="Number of cached items")

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return round((self.cache_hits / total) * 100, 1)


class EconomicIndicator(BaseModel):
    """Normalized economic indicator for PatternEngine consumption.

    This is the format that PatternEngine expects after processing SeriesData.

    Example:
        >>> indicator = EconomicIndicator(
        ...     indicator='GDP',
        ...     value=27500.0,
        ...     date='2025-01-01',
        ...     change_percent=2.5,
        ...     unit='Billions of Dollars',
        ...     frequency='Quarterly',
        ...     observations_count=100,
        ...     source='live',
        ...     data_quality='high'
        ... )
    """
    model_config = ConfigDict(frozen=True)

    indicator: str = Field(..., description="Indicator name (GDP, CPI, UNRATE, etc.)")
    value: float = Field(..., description="Latest value")
    date: str = Field(..., description="Date of latest value (YYYY-MM-DD)")
    change_percent: Optional[float] = Field(None, description="Percent change from previous period")
    unit: str = Field(..., description="Units of measurement")
    frequency: str = Field(..., description="Data frequency")
    observations_count: int = Field(..., ge=1, description="Number of observations")
    source: str = Field(..., description="Data source: 'live', 'cache', or 'fallback'")
    data_quality: str = Field(..., description="Quality level: 'high', 'medium', 'low', 'none'")

    @field_validator('data_quality')
    @classmethod
    def validate_quality_level(cls, v: str) -> str:
        """Ensure data quality is a known level."""
        valid_levels = ['high', 'medium', 'low', 'none']
        if v not in valid_levels:
            raise ValueError(f"data_quality must be one of {valid_levels}, got: {v}")
        return v


# Package exports
__all__ = [
    'FREDObservation',
    'SeriesData',
    'EconomicDataResponse',
    'FREDHealthStatus',
    'EconomicIndicator',
]
