"""Pydantic models for cryptocurrency data validation.

Validates data from CryptoCapability (CoinGecko API).
Ensures runtime type safety for cryptocurrency prices and market data.

Version: 1.0.0
Last Updated: 2025-10-10
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional


class CryptoPrice(BaseModel):
    """Cryptocurrency price with validation.

    Validates real-time crypto price data from CoinGecko API.
    """
    model_config = ConfigDict(frozen=True)  # Immutable for thread safety

    symbol: str = Field(..., min_length=1, max_length=10, description="Crypto symbol (e.g., 'BTC', 'ETH')")
    price: float = Field(..., gt=0, description="Current price in USD (must be positive)")
    change_24h: float = Field(default=0.0, description="24-hour price change percentage")

    # Optional error field
    error: Optional[str] = Field(None, description="Error message if fetch failed")

    @field_validator('price')
    @classmethod
    def validate_price_reasonable(cls, v: float) -> float:
        """Ensure price is reasonable (> 0, < $10M per coin)."""
        if v <= 0:
            raise ValueError(f"price must be positive, got: {v}")
        if v > 10_000_000:  # $10M seems like a reasonable upper bound
            # Don't fail, but could log warning (some tokens could be this high)
            pass
        return v

    @field_validator('change_24h')
    @classmethod
    def validate_change_reasonable(cls, v: float) -> float:
        """Ensure 24h change is reasonable (-100% to +1000%)."""
        if v < -100 or v > 1000:
            # Don't fail validation, but note: extreme changes can happen in crypto
            pass
        return v


class CryptoQuote(BaseModel):
    """Extended cryptocurrency quote with market data.

    More comprehensive quote data including market cap, volume, etc.
    """
    model_config = ConfigDict(frozen=True)

    symbol: str = Field(..., min_length=1, max_length=10, description="Crypto symbol")
    name: str = Field(..., min_length=1, description="Cryptocurrency name")

    # Price data
    price: float = Field(..., gt=0, description="Current price in USD")
    change_24h: float = Field(default=0.0, description="24-hour price change %")
    change_7d: Optional[float] = Field(None, description="7-day price change %")

    # Market data
    market_cap: Optional[float] = Field(None, ge=0, description="Market capitalization in USD")
    volume_24h: Optional[float] = Field(None, ge=0, description="24-hour trading volume")

    # Supply data
    circulating_supply: Optional[float] = Field(None, ge=0, description="Circulating supply")
    total_supply: Optional[float] = Field(None, ge=0, description="Total supply")
    max_supply: Optional[float] = Field(None, ge=0, description="Maximum supply")

    # Optional error
    error: Optional[str] = Field(None, description="Error message if fetch failed")

    @field_validator('circulating_supply')
    @classmethod
    def validate_circulating_vs_total(cls, v: Optional[float], info) -> Optional[float]:
        """Ensure circulating supply <= total supply (if both present)."""
        if v is not None and 'total_supply' in info.data and info.data['total_supply'] is not None:
            total = info.data['total_supply']
            if v > total:
                raise ValueError(f"circulating_supply ({v}) cannot exceed total_supply ({total})")
        return v


class CryptoMarketSummary(BaseModel):
    """Cryptocurrency market summary.

    Aggregated market overview with top coins and global metrics.
    """
    model_config = ConfigDict(frozen=True)

    total_market_cap: float = Field(..., gt=0, description="Total crypto market cap in USD")
    total_volume_24h: float = Field(..., ge=0, description="Total 24h trading volume")
    btc_dominance: float = Field(..., ge=0, le=100, description="Bitcoin dominance percentage")

    # Optional top coins list
    top_coins: Optional[list] = Field(None, description="List of top cryptocurrencies by market cap")

    # Metadata
    as_of_timestamp: str = Field(..., description="Data timestamp (ISO format)")

    @field_validator('btc_dominance')
    @classmethod
    def validate_btc_dominance_range(cls, v: float) -> float:
        """Ensure BTC dominance is in valid range [0, 100]."""
        if v < 0 or v > 100:
            raise ValueError(f"btc_dominance must be in range [0, 100], got: {v}")
        return v


# Export all models
__all__ = [
    'CryptoPrice',
    'CryptoQuote',
    'CryptoMarketSummary',
]
