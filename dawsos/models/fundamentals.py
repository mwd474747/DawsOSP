"""Pydantic models for company fundamentals validation.

Validates data from FundamentalsCapability (Alpha Vantage API).
Ensures runtime type safety for company overview and financial metrics.

Version: 1.0.0
Last Updated: 2025-10-10
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class CompanyOverview(BaseModel):
    """Company overview with fundamental metrics validation.

    Validates data from Alpha Vantage OVERVIEW endpoint.
    Ensures all financial metrics are valid positive numbers where applicable.
    """
    model_config = ConfigDict(frozen=True)  # Immutable for thread safety

    # Core identifiers
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., 'AAPL')")
    name: Optional[str] = Field(None, description="Company name")

    # Classification
    sector: Optional[str] = Field(None, description="Business sector")
    industry: Optional[str] = Field(None, description="Industry classification")

    # Financial metrics
    market_cap: float = Field(default=0.0, ge=0, description="Market capitalization in USD")
    pe_ratio: float = Field(default=0.0, description="Price-to-Earnings ratio (can be negative)")
    dividend_yield: float = Field(default=0.0, ge=0, le=1.0, description="Dividend yield (0-1 range)")
    eps: float = Field(default=0.0, description="Earnings per share (can be negative)")
    beta: float = Field(default=0.0, description="Stock beta (volatility measure)")

    # Optional error field
    error: Optional[str] = Field(None, description="Error message if API failed")

    @field_validator('dividend_yield')
    @classmethod
    def validate_dividend_yield_range(cls, v: float) -> float:
        """Ensure dividend yield is in valid range [0, 1]."""
        if v < 0 or v > 1:
            raise ValueError(f"dividend_yield must be in range [0, 1], got: {v}")
        return v

    @field_validator('market_cap')
    @classmethod
    def validate_market_cap_positive(cls, v: float) -> float:
        """Ensure market cap is non-negative."""
        if v < 0:
            raise ValueError(f"market_cap cannot be negative, got: {v}")
        return v


class FinancialRatios(BaseModel):
    """Financial ratios and valuation metrics.

    Common ratios used for fundamental analysis with validation.
    """
    model_config = ConfigDict(frozen=True)

    symbol: str = Field(..., min_length=1, max_length=10)

    # Valuation ratios
    pe_ratio: Optional[float] = Field(None, description="Price-to-Earnings")
    pb_ratio: Optional[float] = Field(None, ge=0, description="Price-to-Book (must be positive)")
    ps_ratio: Optional[float] = Field(None, ge=0, description="Price-to-Sales (must be positive)")
    peg_ratio: Optional[float] = Field(None, description="PEG ratio (PE/Growth)")

    # Profitability ratios
    roe: Optional[float] = Field(None, description="Return on Equity")
    roa: Optional[float] = Field(None, description="Return on Assets")
    roic: Optional[float] = Field(None, description="Return on Invested Capital")

    # Efficiency ratios
    asset_turnover: Optional[float] = Field(None, ge=0, description="Asset turnover ratio")
    inventory_turnover: Optional[float] = Field(None, ge=0, description="Inventory turnover ratio")

    # Liquidity ratios
    current_ratio: Optional[float] = Field(None, ge=0, description="Current ratio")
    quick_ratio: Optional[float] = Field(None, ge=0, description="Quick ratio")

    # Leverage ratios
    debt_to_equity: Optional[float] = Field(None, ge=0, description="Debt-to-Equity ratio")
    debt_to_assets: Optional[float] = Field(None, ge=0, le=1, description="Debt-to-Assets ratio")

    @field_validator('debt_to_assets')
    @classmethod
    def validate_debt_to_assets_range(cls, v: Optional[float]) -> Optional[float]:
        """Ensure debt-to-assets is in valid range [0, 1]."""
        if v is not None and (v < 0 or v > 1):
            raise ValueError(f"debt_to_assets must be in range [0, 1], got: {v}")
        return v


class KeyMetrics(BaseModel):
    """Key financial metrics and performance indicators.

    Essential metrics for quick fundamental analysis.
    """
    model_config = ConfigDict(frozen=True)

    symbol: str = Field(..., min_length=1, max_length=10)

    # Growth metrics
    revenue_growth: Optional[float] = Field(None, description="YoY revenue growth rate")
    earnings_growth: Optional[float] = Field(None, description="YoY earnings growth rate")

    # Profitability metrics
    gross_margin: Optional[float] = Field(None, ge=0, le=1, description="Gross profit margin")
    operating_margin: Optional[float] = Field(None, description="Operating margin (can be negative)")
    net_margin: Optional[float] = Field(None, description="Net profit margin (can be negative)")

    # Per-share metrics
    eps: Optional[float] = Field(None, description="Earnings per share")
    book_value_per_share: Optional[float] = Field(None, description="Book value per share")
    free_cash_flow_per_share: Optional[float] = Field(None, description="FCF per share")

    # Other metrics
    shares_outstanding: Optional[float] = Field(None, gt=0, description="Total shares outstanding")
    dividend_per_share: Optional[float] = Field(None, ge=0, description="Annual dividend per share")

    @field_validator('gross_margin')
    @classmethod
    def validate_gross_margin_range(cls, v: Optional[float]) -> Optional[float]:
        """Ensure gross margin is in valid range [0, 1]."""
        if v is not None and (v < 0 or v > 1):
            raise ValueError(f"gross_margin must be in range [0, 1], got: {v}")
        return v

    @field_validator('shares_outstanding')
    @classmethod
    def validate_shares_positive(cls, v: Optional[float]) -> Optional[float]:
        """Ensure shares outstanding is positive."""
        if v is not None and v <= 0:
            raise ValueError(f"shares_outstanding must be positive, got: {v}")
        return v


class FinancialStatement(BaseModel):
    """Simplified financial statement data.

    Key line items from income statement, balance sheet, and cash flow.
    """
    model_config = ConfigDict(frozen=True)

    symbol: str = Field(..., min_length=1, max_length=10)
    fiscal_date: str = Field(..., description="Fiscal period end date (YYYY-MM-DD)")

    # Income statement
    revenue: Optional[float] = Field(None, ge=0, description="Total revenue")
    cost_of_revenue: Optional[float] = Field(None, ge=0, description="Cost of goods sold")
    gross_profit: Optional[float] = Field(None, description="Gross profit")
    operating_income: Optional[float] = Field(None, description="Operating income")
    net_income: Optional[float] = Field(None, description="Net income")

    # Balance sheet
    total_assets: Optional[float] = Field(None, ge=0, description="Total assets")
    total_liabilities: Optional[float] = Field(None, ge=0, description="Total liabilities")
    shareholders_equity: Optional[float] = Field(None, description="Shareholders equity")

    # Cash flow
    operating_cash_flow: Optional[float] = Field(None, description="Cash from operations")
    capital_expenditures: Optional[float] = Field(None, le=0, description="CapEx (usually negative)")
    free_cash_flow: Optional[float] = Field(None, description="Free cash flow")

    @field_validator('fiscal_date')
    @classmethod
    def validate_fiscal_date_format(cls, v: str) -> str:
        """Ensure fiscal date is in valid YYYY-MM-DD format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"fiscal_date must be in YYYY-MM-DD format, got: {v}")
        return v

    @field_validator('gross_profit')
    @classmethod
    def validate_gross_profit_vs_revenue(cls, v: Optional[float], info) -> Optional[float]:
        """Ensure gross profit <= revenue (if both present)."""
        if v is not None and 'revenue' in info.data and info.data['revenue'] is not None:
            revenue = info.data['revenue']
            if v > revenue:
                raise ValueError(f"gross_profit ({v}) cannot exceed revenue ({revenue})")
        return v


# Export all models
__all__ = [
    'CompanyOverview',
    'FinancialRatios',
    'KeyMetrics',
    'FinancialStatement',
]
