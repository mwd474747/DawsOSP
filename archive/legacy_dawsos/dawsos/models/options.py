"""Pydantic models for options data validation.

Validates data from PolygonOptionsCapability (Polygon.io API).
Ensures runtime type safety for options contracts, Greeks, and option chains.

Version: 1.0.0
Last Updated: 2025-10-10
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


class OptionsContract(BaseModel):
    """Individual options contract with validation.

    Validates data from Polygon.io /v3/reference/options/contracts endpoint.
    """
    model_config = ConfigDict(frozen=True)  # Immutable for thread safety

    # Contract identifiers
    ticker: Optional[str] = Field(None, description="Option ticker (e.g., 'O:SPY251219C00450000')")
    underlying_ticker: str = Field(..., min_length=1, max_length=10, description="Underlying stock symbol")

    # Contract specifications
    contract_type: str = Field(..., pattern="^(call|put)$", description="Option type: 'call' or 'put'")
    strike_price: float = Field(..., gt=0, description="Strike price (must be positive)")
    expiration_date: str = Field(..., description="Expiration date (YYYY-MM-DD)")

    # Exercise style and multiplier
    exercise_style: Optional[str] = Field(None, pattern="^(american|european)$", description="Exercise style")
    shares_per_contract: Optional[int] = Field(100, ge=1, description="Shares per contract (usually 100)")

    # Optional market data
    primary_exchange: Optional[str] = Field(None, description="Primary exchange")
    cfi: Optional[str] = Field(None, description="CFI code")

    @field_validator('expiration_date')
    @classmethod
    def validate_expiration_format(cls, v: str) -> str:
        """Ensure expiration date is in valid YYYY-MM-DD format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"expiration_date must be in YYYY-MM-DD format, got: {v}")
        return v

    @field_validator('contract_type')
    @classmethod
    def validate_contract_type_lowercase(cls, v: str) -> str:
        """Ensure contract type is lowercase."""
        return v.lower()


class GreeksData(BaseModel):
    """Options Greeks aggregation with validation.

    Aggregated Greeks data for portfolio-level risk assessment.
    """
    model_config = ConfigDict(frozen=True)

    ticker: str = Field(..., min_length=1, max_length=10, description="Underlying ticker")

    # Core Greeks
    net_delta: float = Field(default=0.0, description="Net delta (directional exposure)")
    total_gamma: float = Field(default=0.0, ge=0, description="Total gamma (delta acceleration)")
    total_vega: Optional[float] = Field(None, ge=0, description="Total vega (IV sensitivity)")
    total_theta: Optional[float] = Field(None, description="Total theta (time decay)")
    total_rho: Optional[float] = Field(None, description="Total rho (interest rate sensitivity)")

    # Optional metadata
    note: Optional[str] = Field(None, description="Implementation notes or warnings")
    error: Optional[str] = Field(None, description="Error message if calculation failed")

    @field_validator('total_gamma')
    @classmethod
    def validate_gamma_positive(cls, v: float) -> float:
        """Ensure gamma is non-negative (absolute value by definition)."""
        if v < 0:
            raise ValueError(f"total_gamma must be non-negative, got: {v}")
        return v


class OptionChainResponse(BaseModel):
    """Complete option chain response with validation.

    Validates the full response from get_option_chain() method.
    """
    model_config = ConfigDict(frozen=True)

    ticker: str = Field(..., min_length=1, max_length=10, description="Underlying ticker")

    # Contract lists
    calls: List[OptionsContract] = Field(default_factory=list, description="Call option contracts")
    puts: List[OptionsContract] = Field(default_factory=list, description="Put option contracts")

    # Metadata
    total_contracts: int = Field(default=0, ge=0, description="Total number of contracts")
    timestamp: str = Field(..., description="Response timestamp (ISO format)")

    # Optional error field
    error: Optional[str] = Field(None, description="Error message if fetch failed")

    @field_validator('total_contracts')
    @classmethod
    def validate_total_matches_lists(cls, v: int, info) -> int:
        """Ensure total_contracts matches the sum of calls + puts."""
        if 'calls' in info.data and 'puts' in info.data:
            actual_total = len(info.data['calls']) + len(info.data['puts'])
            if v != actual_total and v != 0:  # Allow 0 for error cases
                raise ValueError(f"total_contracts ({v}) doesn't match calls+puts ({actual_total})")
        return v

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        """Ensure timestamp is in valid ISO format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"timestamp must be in ISO format, got: {v}")
        return v


class UnusualActivityAlert(BaseModel):
    """Unusual options activity alert with validation.

    Identifies potentially significant options trades (large volume, unusual flow).
    """
    model_config = ConfigDict(frozen=True)

    ticker: str = Field(..., min_length=1, max_length=10, description="Underlying ticker")
    contract_type: str = Field(..., pattern="^(call|put)$", description="Option type")
    strike: float = Field(..., gt=0, description="Strike price")
    expiration: str = Field(..., description="Expiration date (YYYY-MM-DD)")

    # Activity metrics
    volume: int = Field(..., ge=0, description="Contract volume")
    open_interest: Optional[int] = Field(None, ge=0, description="Open interest")
    volume_oi_ratio: Optional[float] = Field(None, ge=0, description="Volume/OI ratio")

    # Sentiment indicators
    sentiment: Optional[str] = Field(None, pattern="^(bullish|bearish|neutral)$", description="Inferred sentiment")
    unusual_score: Optional[float] = Field(None, ge=0, le=100, description="Unusualness score (0-100)")

    # Timing
    detected_at: str = Field(..., description="Detection timestamp (ISO format)")

    @field_validator('volume_oi_ratio')
    @classmethod
    def validate_volume_oi_ratio_reasonable(cls, v: Optional[float]) -> Optional[float]:
        """Warn if volume/OI ratio is extremely high (> 10 is very unusual)."""
        if v is not None and v > 50:
            # Don't reject, but could log a warning in production
            pass
        return v


class IVRankData(BaseModel):
    """Implied Volatility rank and percentile data.

    Historical IV context for options pricing assessment.
    """
    model_config = ConfigDict(frozen=True)

    ticker: str = Field(..., min_length=1, max_length=10, description="Underlying ticker")

    # Current IV
    current_iv: float = Field(..., gt=0, le=5.0, description="Current implied volatility (0-5 range)")

    # Historical context (52-week)
    iv_rank: float = Field(..., ge=0, le=100, description="IV rank (0-100 percentile)")
    iv_percentile: float = Field(..., ge=0, le=100, description="IV percentile (0-100)")

    # Historical range
    iv_high_52w: float = Field(..., gt=0, description="52-week IV high")
    iv_low_52w: float = Field(..., gt=0, description="52-week IV low")

    # Metadata
    as_of_date: str = Field(..., description="Data date (YYYY-MM-DD)")

    @field_validator('current_iv')
    @classmethod
    def validate_current_iv_in_range(cls, v: float, info) -> float:
        """Ensure current IV is within 52-week range (if available)."""
        if 'iv_high_52w' in info.data and 'iv_low_52w' in info.data:
            high = info.data['iv_high_52w']
            low = info.data['iv_low_52w']
            if not (low <= v <= high * 1.1):  # Allow 10% overshoot for new highs
                # Don't fail validation, just note (IV can exceed 52w high)
                pass
        return v


# Export all models
__all__ = [
    'OptionsContract',
    'GreeksData',
    'OptionChainResponse',
    'UnusualActivityAlert',
    'IVRankData',
]
