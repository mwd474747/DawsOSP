"""
DawsOS Attribution API Schemas

Purpose: Pydantic models for currency attribution API responses
Updated: 2025-10-22
Priority: P0 (Phase 4 Task 1)

Models:
    - AttributionResponse: Currency attribution breakdown

Usage:
    from backend.app.api.schemas.attribution import AttributionResponse

    attribution = currency_attr.compute_portfolio_attribution(portfolio_id, asof_date)
    return AttributionResponse.from_attribution(attribution)
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AttributionResponse(BaseModel):
    """
    Currency attribution response model.

    Decomposes portfolio return into local currency return, FX return, and interaction.
    Mathematical identity: r_base = (1 + r_local)(1 + r_fx) - 1
    """

    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    asof_date: date = Field(..., description="As-of date for attribution")
    pricing_pack_id: str = Field(..., description="Pricing pack ID used")

    local_return: float = Field(..., description="Local currency return component")
    fx_return: float = Field(..., description="FX return component")
    interaction_return: float = Field(..., description="Interaction term (r_local × r_fx)")
    total_return: float = Field(..., description="Total return in base currency")

    error_bps: Optional[float] = Field(
        None,
        description="Validation error in basis points (should be < 0.1bp)"
    )

    base_currency: str = Field(default="CAD", description="Base currency for attribution")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None,
            UUID: str,
        }

    @classmethod
    def from_attribution(cls, attribution_obj, portfolio_id: UUID, asof_date: date, pricing_pack_id: str):
        """
        Create response from PortfolioAttribution object.

        Args:
            attribution_obj: PortfolioAttribution from currency_attribution.py
            portfolio_id: Portfolio UUID
            asof_date: As-of date
            pricing_pack_id: Pricing pack ID

        Returns:
            AttributionResponse with converted Decimal fields
        """
        return cls(
            portfolio_id=portfolio_id,
            asof_date=asof_date,
            pricing_pack_id=pricing_pack_id,
            local_return=float(attribution_obj.local_return),
            fx_return=float(attribution_obj.fx_return),
            interaction_return=float(attribution_obj.interaction_return),
            total_return=float(attribution_obj.total_return),
            error_bps=float(attribution_obj.error_bps) if attribution_obj.error_bps is not None else None,
            base_currency=attribution_obj.base_currency,
        )


class PositionAttributionResponse(BaseModel):
    """
    Position-level currency attribution response.

    Attribution for a single position.
    """

    position_id: str = Field(..., description="Position identifier")
    currency: str = Field(..., description="Position currency")
    base_currency: str = Field(..., description="Base currency")

    local_return: float = Field(..., description="Local currency return")
    fx_return: float = Field(..., description="FX return")
    interaction_return: float = Field(..., description="Interaction term")
    total_return: float = Field(..., description="Total return in base currency")

    error_bps: Optional[float] = Field(None, description="Validation error in bp")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None,
        }


__all__ = ["AttributionResponse", "PositionAttributionResponse"]
