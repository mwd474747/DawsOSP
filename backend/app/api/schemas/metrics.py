"""
DawsOS Metrics API Schemas

Purpose: Pydantic models for metrics API responses
Updated: 2025-10-22
Priority: P0 (Phase 4 Task 1)

Models:
    - MetricsResponse: Single metrics response
    - MetricsHistoryResponse: List of historical metrics

Usage:
    from app.api.schemas.metrics import MetricsResponse

    metrics = await queries.get_latest_metrics(portfolio_id, asof_date)
    return MetricsResponse.from_orm(metrics)
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MetricsResponse(BaseModel):
    """
    Portfolio metrics response model.

    Contains all computed metrics for a portfolio as of a specific date.
    All Decimal fields are converted to float for JSON serialization.
    """

    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    asof_date: date = Field(..., description="As-of date for metrics")
    pricing_pack_id: str = Field(..., description="Pricing pack ID used for valuation")

    # Returns
    twr_1d: Optional[float] = Field(None, description="1-day time-weighted return")
    twr_mtd: Optional[float] = Field(None, description="Month-to-date TWR")
    twr_qtd: Optional[float] = Field(None, description="Quarter-to-date TWR")
    twr_ytd: Optional[float] = Field(None, description="Year-to-date TWR")
    twr_1y: Optional[float] = Field(None, description="1-year TWR")
    twr_3y_ann: Optional[float] = Field(None, description="3-year annualized TWR")
    twr_5y_ann: Optional[float] = Field(None, description="5-year annualized TWR")
    twr_inception_ann: Optional[float] = Field(None, description="Inception annualized TWR")

    mwr_ytd: Optional[float] = Field(None, description="Year-to-date money-weighted return")
    mwr_1y: Optional[float] = Field(None, description="1-year MWR")
    mwr_3y_ann: Optional[float] = Field(None, description="3-year annualized MWR")
    mwr_inception_ann: Optional[float] = Field(None, description="Inception annualized MWR")

    # Risk metrics
    volatility_30d: Optional[float] = Field(None, description="30-day annualized volatility")
    volatility_60d: Optional[float] = Field(None, description="60-day annualized volatility")
    volatility_90d: Optional[float] = Field(None, description="90-day annualized volatility")
    volatility_1y: Optional[float] = Field(None, description="1-year annualized volatility")

    sharpe_30d: Optional[float] = Field(None, description="30-day Sharpe ratio")
    sharpe_60d: Optional[float] = Field(None, description="60-day Sharpe ratio")
    sharpe_90d: Optional[float] = Field(None, description="90-day Sharpe ratio")
    sharpe_1y: Optional[float] = Field(None, description="1-year Sharpe ratio")

    max_drawdown_1y: Optional[float] = Field(None, description="1-year maximum drawdown")
    max_drawdown_3y: Optional[float] = Field(None, description="3-year maximum drawdown")

    # Benchmark relative
    alpha_1y: Optional[float] = Field(None, description="1-year alpha vs benchmark")
    alpha_3y_ann: Optional[float] = Field(None, description="3-year annualized alpha")
    beta_1y: Optional[float] = Field(None, description="1-year beta vs benchmark")
    beta_3y: Optional[float] = Field(None, description="3-year beta")

    tracking_error_1y: Optional[float] = Field(None, description="1-year tracking error")
    information_ratio_1y: Optional[float] = Field(None, description="1-year information ratio")

    # Trading stats
    win_rate_1y: Optional[float] = Field(None, description="1-year win rate")
    avg_win: Optional[float] = Field(None, description="Average win")
    avg_loss: Optional[float] = Field(None, description="Average loss")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None,
            UUID: str,
        }

    @classmethod
    def from_orm(cls, obj):
        """
        Create response from ORM object (PortfolioMetrics).

        Converts Decimal fields to float for JSON serialization.
        """
        if obj is None:
            return None

        # Convert Decimal fields to float
        data = {}
        for field_name, field in cls.__fields__.items():
            value = getattr(obj, field_name, None)
            if isinstance(value, Decimal):
                data[field_name] = float(value) if value is not None else None
            elif isinstance(value, UUID):
                data[field_name] = str(value)
            else:
                data[field_name] = value

        return cls(**data)


class MetricsHistoryResponse(BaseModel):
    """
    Historical metrics response model.

    Contains a list of metrics for a date range.
    """

    portfolio_id: UUID
    start_date: date
    end_date: date
    metrics: List[MetricsResponse] = Field(default_factory=list)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            UUID: str,
        }


__all__ = ["MetricsResponse", "MetricsHistoryResponse"]
