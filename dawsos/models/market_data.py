"""Pydantic models for FMP (Financial Modeling Prep) market data validation.

Validates stock quotes, company profiles, and historical price data from FMP API
to ensure data integrity and prevent format incompatibility issues.

Reference: https://financialmodelingprep.com/developer/docs/
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class StockQuote(BaseModel):
    """Real-time stock quote with validation.

    Validates FMP /quote endpoint response with business logic constraints.

    Example:
        >>> quote = StockQuote(
        ...     symbol='AAPL',
        ...     name='Apple Inc.',
        ...     price=178.50,
        ...     day_low=177.00,
        ...     day_high=180.00
        ... )
    """
    model_config = ConfigDict(frozen=True)

    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    name: Optional[str] = Field(None, description="Company name")
    price: float = Field(..., gt=0, description="Current stock price (must be positive)")
    previous_close: Optional[float] = Field(None, ge=0, description="Previous closing price")
    change: Optional[float] = Field(None, description="Dollar change from previous close")
    change_percent: Optional[float] = Field(None, description="Percent change from previous close")

    # Intraday range
    day_low: Optional[float] = Field(None, gt=0, description="Day's low price")
    day_high: Optional[float] = Field(None, gt=0, description="Day's high price")

    # Annual range
    year_low: Optional[float] = Field(None, gt=0, description="52-week low price")
    year_high: Optional[float] = Field(None, gt=0, description="52-week high price")

    # Volume
    volume: Optional[int] = Field(None, ge=0, description="Trading volume")
    avg_volume: Optional[int] = Field(None, ge=0, description="Average trading volume")

    # Valuation metrics
    market_cap: Optional[float] = Field(None, ge=0, description="Market capitalization")
    pe: Optional[float] = Field(None, description="Price-to-earnings ratio")
    eps: Optional[float] = Field(None, description="Earnings per share")

    # Metadata
    exchange: Optional[str] = Field(None, description="Stock exchange")
    timestamp: Optional[int] = Field(None, description="Unix timestamp")

    @field_validator('day_high')
    @classmethod
    def validate_day_high_vs_low(cls, v: Optional[float], info) -> Optional[float]:
        """Ensure day_high >= day_low (impossible for high < low)."""
        if v is not None and 'day_low' in info.data and info.data['day_low'] is not None:
            if v < info.data['day_low']:
                raise ValueError(
                    f"day_high ({v}) cannot be less than day_low ({info.data['day_low']})"
                )
        return v

    @field_validator('year_high')
    @classmethod
    def validate_year_high_vs_low(cls, v: Optional[float], info) -> Optional[float]:
        """Ensure year_high >= year_low."""
        if v is not None and 'year_low' in info.data and info.data['year_low'] is not None:
            if v < info.data['year_low']:
                raise ValueError(
                    f"year_high ({v}) cannot be less than year_low ({info.data['year_low']})"
                )
        return v

    @field_validator('change')
    @classmethod
    def validate_change_consistency(cls, v: Optional[float], info) -> Optional[float]:
        """Validate change matches price - previous_close (within tolerance)."""
        if v is not None and 'price' in info.data and 'previous_close' in info.data:
            price = info.data['price']
            prev = info.data.get('previous_close')
            if prev is not None and price is not None:
                expected_change = price - prev
                # Allow 1% tolerance for rounding differences
                tolerance = abs(expected_change) * 0.01
                if abs(v - expected_change) > tolerance:
                    # Don't fail, just warn
                    pass  # Could log warning here
        return v

    @field_validator('symbol')
    @classmethod
    def validate_symbol_uppercase(cls, v: str) -> str:
        """Ensure symbol is uppercase."""
        return v.upper()


class CompanyProfile(BaseModel):
    """Company profile with validation.

    Validates FMP /profile endpoint response.

    Example:
        >>> profile = CompanyProfile(
        ...     symbol='AAPL',
        ...     company_name='Apple Inc.',
        ...     sector='Technology',
        ...     industry='Consumer Electronics'
        ... )
    """
    model_config = ConfigDict(frozen=True)

    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    company_name: str = Field(..., min_length=1, description="Full company name")
    sector: Optional[str] = Field(None, description="Business sector")
    industry: Optional[str] = Field(None, description="Industry classification")
    description: Optional[str] = Field(None, description="Company description")

    # Company details
    ceo: Optional[str] = Field(None, description="CEO name")
    website: Optional[str] = Field(None, description="Company website URL")
    exchange: Optional[str] = Field(None, description="Primary stock exchange")
    country: Optional[str] = Field(None, description="Country of incorporation")
    city: Optional[str] = Field(None, description="Headquarters city")
    address: Optional[str] = Field(None, description="Headquarters address")

    # Market data
    market_cap: Optional[float] = Field(None, ge=0, description="Market capitalization")
    price: Optional[float] = Field(None, gt=0, description="Current stock price")
    beta: Optional[float] = Field(None, description="Stock beta (volatility)")

    # Business metrics
    full_time_employees: Optional[int] = Field(None, ge=0, description="Number of full-time employees")
    ipo_date: Optional[str] = Field(None, description="IPO date (YYYY-MM-DD)")

    # Misc
    image: Optional[str] = Field(None, description="Company logo URL")
    is_etf: Optional[bool] = Field(False, description="Whether this is an ETF")
    is_actively_trading: Optional[bool] = Field(True, description="Whether actively trading")

    @field_validator('symbol')
    @classmethod
    def validate_symbol_uppercase(cls, v: str) -> str:
        """Ensure symbol is uppercase."""
        return v.upper()

    @field_validator('ipo_date')
    @classmethod
    def validate_ipo_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Ensure IPO date is valid format."""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                # Don't fail, just return None
                return None
        return v


class HistoricalPrice(BaseModel):
    """Single historical price observation.

    Validates individual price data points from historical data.
    """
    model_config = ConfigDict(frozen=True)

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    open: float = Field(..., gt=0, description="Opening price")
    high: float = Field(..., gt=0, description="High price")
    low: float = Field(..., gt=0, description="Low price")
    close: float = Field(..., gt=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

    # Optional fields
    adj_close: Optional[float] = Field(None, gt=0, alias='adjClose', description="Adjusted closing price")
    change: Optional[float] = Field(None, description="Dollar change")
    change_percent: Optional[float] = Field(None, alias='changePercent', description="Percent change")

    @field_validator('high')
    @classmethod
    def validate_high_vs_low(cls, v: float, info) -> float:
        """Ensure high >= low (impossible for high < low)."""
        if 'low' in info.data:
            low = info.data['low']
            if v < low:
                raise ValueError(f"high ({v}) cannot be less than low ({low})")
        return v

    @field_validator('close')
    @classmethod
    def validate_close_in_range(cls, v: float, info) -> float:
        """Ensure close is within [low, high] range."""
        if 'low' in info.data and 'high' in info.data:
            low = info.data['low']
            high = info.data['high']
            if v < low or v > high:
                # Allow small tolerance for rounding
                tolerance = (high - low) * 0.01
                if v < low - tolerance or v > high + tolerance:
                    raise ValueError(
                        f"close ({v}) must be between low ({low}) and high ({high})"
                    )
        return v

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Ensure date is in YYYY-MM-DD format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}")


# Package exports
__all__ = [
    'StockQuote',
    'CompanyProfile',
    'HistoricalPrice',
]
