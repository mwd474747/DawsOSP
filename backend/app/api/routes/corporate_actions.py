"""
Corporate Actions API Endpoints

RESTful API for recording corporate actions (dividends, splits, withholding tax).

Endpoints:
- POST /v1/corporate-actions/dividends - Record dividend payment
- POST /v1/corporate-actions/splits - Record stock split
- POST /v1/corporate-actions/withholding-tax - Record ADR withholding tax
- GET /v1/corporate-actions/dividends - List dividend history

Created: 2025-10-23
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
import logging

from ...db.connection import get_db_connection_with_rls
from ...services.corporate_actions import (
    CorporateActionsService,
    CorporateActionError,
    InvalidCorporateActionError,
    InsufficientDataError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/corporate-actions", tags=["corporate-actions"])


# ============================================================================
# Pydantic Models
# ============================================================================

class DividendRequest(BaseModel):
    """Request model for recording a dividend."""

    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    symbol: str = Field(..., min_length=1, max_length=20, description="Security symbol (e.g., AAPL)")
    shares: Decimal = Field(..., gt=0, description="Number of shares held")
    dividend_per_share: Decimal = Field(..., gt=0, description="Dividend per share")
    currency: str = Field(..., pattern="^[A-Z]{3}$", description="Dividend currency (ISO 4217)")
    ex_date: date = Field(..., description="Ex-dividend date (for reference)")
    pay_date: date = Field(..., description="Payment date (CRITICAL: used for FX rate)")
    withholding_tax: Decimal = Field(Decimal("0"), ge=0, description="Tax withheld per share")
    base_currency: Optional[str] = Field(None, pattern="^[A-Z]{3}$", description="Portfolio base currency")
    pay_fx_rate: Optional[Decimal] = Field(None, gt=0, description="FX rate at pay date (required for ADR)")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes")

    @validator("pay_date")
    def validate_pay_date(cls, v, values):
        """Validate pay_date is after ex_date."""
        if "ex_date" in values and v < values["ex_date"]:
            raise ValueError("pay_date must be >= ex_date")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
                "symbol": "AAPL",
                "shares": 100,
                "dividend_per_share": 0.24,
                "currency": "USD",
                "ex_date": "2024-08-12",
                "pay_date": "2024-08-15",
                "withholding_tax": 0.036,
                "base_currency": "CAD",
                "pay_fx_rate": 1.36,
                "notes": "AAPL Q3 2024 dividend (ADR)"
            }
        }


class SplitRequest(BaseModel):
    """Request model for recording a stock split."""

    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    symbol: str = Field(..., min_length=1, max_length=20, description="Security symbol")
    split_ratio: Decimal = Field(..., gt=0, description="Split ratio (new/old, e.g., 2.0 for 2-for-1)")
    split_date: date = Field(..., description="Split effective date")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
                "symbol": "TSLA",
                "split_ratio": 3.0,
                "split_date": "2024-08-25",
                "notes": "3-for-1 stock split"
            }
        }


class WithholdingTaxRequest(BaseModel):
    """Request model for recording ADR withholding tax."""

    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    symbol: str = Field(..., min_length=1, max_length=20, description="Security symbol")
    tax_amount: Decimal = Field(..., gt=0, description="Tax amount (positive)")
    currency: str = Field(..., pattern="^[A-Z]{3}$", description="Tax currency (ISO 4217)")
    tax_date: date = Field(..., description="Tax payment date")
    base_currency: Optional[str] = Field(None, pattern="^[A-Z]{3}$", description="Portfolio base currency")
    fx_rate: Optional[Decimal] = Field(None, gt=0, description="FX rate at tax date")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
                "symbol": "AAPL",
                "tax_amount": 3.60,
                "currency": "USD",
                "tax_date": "2024-08-15",
                "base_currency": "CAD",
                "fx_rate": 1.36,
                "notes": "ADR withholding tax"
            }
        }


class DividendResponse(BaseModel):
    """Response model for dividend recording."""

    transaction_id: UUID
    symbol: str
    shares: Decimal
    dividend_per_share: Decimal
    currency: str
    gross_amount: Decimal
    withholding_amount: Decimal
    net_amount: Decimal
    ex_date: date
    pay_date: date
    pay_fx_rate: Decimal
    pay_fx_rate_id: Optional[UUID]
    net_amount_base: Decimal
    base_currency: str

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "123e4567-e89b-12d3-a456-426614174000",
                "symbol": "AAPL",
                "shares": 100,
                "dividend_per_share": 0.24,
                "currency": "USD",
                "gross_amount": 24.00,
                "withholding_amount": 3.60,
                "net_amount": 20.40,
                "ex_date": "2024-08-12",
                "pay_date": "2024-08-15",
                "pay_fx_rate": 1.36,
                "pay_fx_rate_id": "789e0123-e89b-12d3-a456-426614174003",
                "net_amount_base": 27.74,
                "base_currency": "CAD"
            }
        }


class SplitResponse(BaseModel):
    """Response model for stock split recording."""

    transaction_id: Optional[UUID]
    symbol: str
    split_ratio: Decimal
    split_date: date
    lots_adjusted: int
    lots: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "123e4567-e89b-12d3-a456-426614174000",
                "symbol": "TSLA",
                "split_ratio": 3.0,
                "split_date": "2024-08-25",
                "lots_adjusted": 2,
                "lots": [
                    {
                        "lot_id": "456e7890-e89b-12d3-a456-426614174001",
                        "old_qty_open": 100,
                        "new_qty_open": 300
                    }
                ]
            }
        }


class WithholdingTaxResponse(BaseModel):
    """Response model for withholding tax recording."""

    transaction_id: UUID
    symbol: str
    tax_amount: Decimal
    currency: str
    tax_date: date
    fx_rate: Decimal
    fx_rate_id: Optional[UUID]
    tax_amount_base: Decimal
    base_currency: str

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "123e4567-e89b-12d3-a456-426614174000",
                "symbol": "AAPL",
                "tax_amount": 3.60,
                "currency": "USD",
                "tax_date": "2024-08-15",
                "fx_rate": 1.36,
                "fx_rate_id": "789e0123-e89b-12d3-a456-426614174003",
                "tax_amount_base": 4.90,
                "base_currency": "CAD"
            }
        }


class DividendHistoryItem(BaseModel):
    """Dividend history list item."""

    id: UUID
    symbol: str
    pay_date: date
    ex_date: Optional[date]
    shares: Optional[Decimal]
    dividend_per_share: Optional[Decimal]
    net_amount: Decimal
    currency: str
    pay_fx_rate_id: Optional[UUID]
    narration: Optional[str]


# ============================================================================
# Dependencies
# ============================================================================

async def get_current_user_id(
    x_user_id: Optional[str] = Header(None)
) -> UUID:
    """
    Extract user_id from X-User-ID header.

    For UAT: Use header directly
    For Production: Extract from JWT token

    Args:
        x_user_id: X-User-ID header value

    Returns:
        User UUID

    Raises:
        HTTPException: If header missing or invalid
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail="X-User-ID header required (JWT auth in production)"
        )

    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid X-User-ID format (must be UUID)"
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/dividends", response_model=DividendResponse, status_code=201)
async def record_dividend(
    dividend: DividendRequest,
    user_id: UUID = Depends(get_current_user_id)
) -> DividendResponse:
    """
    Record a dividend payment.

    **CRITICAL**: For ADR dividends, this endpoint MUST use the pay-date FX rate
    (not ex-date FX). This is required for accurate cost basis tracking.

    **Example**: AAPL ADR dividend
    - Ex-date: 2024-08-12, FX = 1.34 USD/CAD
    - Pay-date: 2024-08-15, FX = 1.36 USD/CAD
    - Must use 1.36 (pay-date FX) for accuracy
    - Accuracy impact: ~42¢ per transaction

    **Gross/Net Calculation**:
    - Gross amount = shares * dividend_per_share
    - Withholding = shares * withholding_tax
    - Net amount = gross - withholding

    **Multi-Currency**:
    - If dividend currency != base currency, provide pay_fx_rate
    - Net amount converted to base currency using pay-date FX

    **RLS**: Automatically filtered to user's portfolios

    **UAT Coverage**: UAT-009, UAT-010 (ADR pay-date FX golden test)
    """
    logger.info(
        f"Dividend request: user_id={user_id}, portfolio_id={dividend.portfolio_id}, "
        f"symbol={dividend.symbol}, shares={dividend.shares}, pay_date={dividend.pay_date}"
    )

    try:
        async with get_db_connection_with_rls(str(user_id)) as conn:
            # Verify portfolio exists and belongs to user (RLS enforced)
            portfolio = await conn.fetchrow(
                "SELECT id, base_currency FROM portfolios WHERE id = $1 AND is_active = true",
                dividend.portfolio_id
            )

            if not portfolio:
                raise HTTPException(
                    status_code=404,
                    detail=f"Portfolio {dividend.portfolio_id} not found or inactive"
                )

            # Use portfolio base currency if not provided
            base_currency = dividend.base_currency or portfolio["base_currency"]

            # Initialize corporate actions service
            service = CorporateActionsService(conn)

            # Record dividend
            result = await service.record_dividend(
                portfolio_id=dividend.portfolio_id,
                symbol=dividend.symbol,
                shares=dividend.shares,
                dividend_per_share=dividend.dividend_per_share,
                currency=dividend.currency,
                ex_date=dividend.ex_date,
                pay_date=dividend.pay_date,
                withholding_tax=dividend.withholding_tax,
                base_currency=base_currency,
                pay_fx_rate=dividend.pay_fx_rate,
                notes=dividend.notes
            )

            return DividendResponse(**result)

    except InsufficientDataError as e:
        logger.warning(f"Insufficient data for dividend: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except InvalidCorporateActionError as e:
        logger.warning(f"Invalid dividend parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except CorporateActionError as e:
        logger.error(f"Corporate action error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dividend recording failed: {e}")

    except Exception as e:
        logger.error(f"Unexpected error recording dividend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/splits", response_model=SplitResponse, status_code=201)
async def record_split(
    split: SplitRequest,
    user_id: UUID = Depends(get_current_user_id)
) -> SplitResponse:
    """
    Record a stock split and adjust all open lots.

    **Split Examples**:
    - 2-for-1 split: split_ratio = 2.0 (each share becomes 2)
    - 3-for-1 split: split_ratio = 3.0 (each share becomes 3)
    - 1-for-2 reverse split: split_ratio = 0.5 (2 shares become 1)

    **Lot Adjustments**:
    - qty_original and qty_open are multiplied by split_ratio
    - cost_basis stays the same (total cost doesn't change)
    - cost_basis_per_share is adjusted (divided by split_ratio)

    **Example**: 100 shares @ $150/share (cost basis $15,000)
    - After 2-for-1 split: 200 shares @ $75/share (cost basis still $15,000)

    **RLS**: Automatically filtered to user's portfolios

    **UAT Coverage**: UAT-011
    """
    logger.info(
        f"Split request: user_id={user_id}, portfolio_id={split.portfolio_id}, "
        f"symbol={split.symbol}, split_ratio={split.split_ratio}"
    )

    try:
        async with get_db_connection_with_rls(str(user_id)) as conn:
            # Verify portfolio exists and belongs to user (RLS enforced)
            portfolio = await conn.fetchrow(
                "SELECT id FROM portfolios WHERE id = $1 AND is_active = true",
                split.portfolio_id
            )

            if not portfolio:
                raise HTTPException(
                    status_code=404,
                    detail=f"Portfolio {split.portfolio_id} not found or inactive"
                )

            # Initialize corporate actions service
            service = CorporateActionsService(conn)

            # Record split
            result = await service.record_split(
                portfolio_id=split.portfolio_id,
                symbol=split.symbol,
                split_ratio=split.split_ratio,
                split_date=split.split_date,
                notes=split.notes
            )

            return SplitResponse(**result)

    except InvalidCorporateActionError as e:
        logger.warning(f"Invalid split parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except CorporateActionError as e:
        logger.error(f"Corporate action error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Split recording failed: {e}")

    except Exception as e:
        logger.error(f"Unexpected error recording split: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/withholding-tax", response_model=WithholdingTaxResponse, status_code=201)
async def record_withholding_tax(
    tax: WithholdingTaxRequest,
    user_id: UUID = Depends(get_current_user_id)
) -> WithholdingTaxResponse:
    """
    Record ADR withholding tax.

    **Purpose**: Track tax withheld on ADR dividends for tax reporting.

    **Multi-Currency**:
    - If tax currency != base currency, provide fx_rate
    - Tax amount converted to base currency

    **RLS**: Automatically filtered to user's portfolios

    **UAT Coverage**: UAT-012
    """
    logger.info(
        f"Withholding tax request: user_id={user_id}, portfolio_id={tax.portfolio_id}, "
        f"symbol={tax.symbol}, tax_amount={tax.tax_amount}"
    )

    try:
        async with get_db_connection_with_rls(str(user_id)) as conn:
            # Verify portfolio exists and belongs to user (RLS enforced)
            portfolio = await conn.fetchrow(
                "SELECT id, base_currency FROM portfolios WHERE id = $1 AND is_active = true",
                tax.portfolio_id
            )

            if not portfolio:
                raise HTTPException(
                    status_code=404,
                    detail=f"Portfolio {tax.portfolio_id} not found or inactive"
                )

            # Use portfolio base currency if not provided
            base_currency = tax.base_currency or portfolio["base_currency"]

            # Initialize corporate actions service
            service = CorporateActionsService(conn)

            # Record withholding tax
            result = await service.record_withholding_tax(
                portfolio_id=tax.portfolio_id,
                symbol=tax.symbol,
                tax_amount=tax.tax_amount,
                currency=tax.currency,
                tax_date=tax.tax_date,
                base_currency=base_currency,
                fx_rate=tax.fx_rate,
                notes=tax.notes
            )

            return WithholdingTaxResponse(**result)

    except InsufficientDataError as e:
        logger.warning(f"Insufficient data for withholding tax: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except InvalidCorporateActionError as e:
        logger.warning(f"Invalid withholding tax parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except CorporateActionError as e:
        logger.error(f"Corporate action error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Withholding tax recording failed: {e}")

    except Exception as e:
        logger.error(f"Unexpected error recording withholding tax: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dividends", response_model=List[DividendHistoryItem])
async def list_dividends(
    portfolio_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    symbol: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[DividendHistoryItem]:
    """
    List dividend payment history for a portfolio.

    **Filters**:
    - symbol: Filter by symbol
    - start_date: Filter by pay_date >= start_date
    - end_date: Filter by pay_date <= end_date

    **RLS**: Automatically filtered to user's portfolios

    **UAT Coverage**: UAT-013
    """
    logger.info(
        f"List dividends: user_id={user_id}, portfolio_id={portfolio_id}, "
        f"symbol={symbol}"
    )

    try:
        async with get_db_connection_with_rls(str(user_id)) as conn:
            # Verify portfolio exists (RLS enforced)
            portfolio = await conn.fetchrow(
                "SELECT id FROM portfolios WHERE id = $1",
                portfolio_id
            )

            if not portfolio:
                raise HTTPException(
                    status_code=404,
                    detail=f"Portfolio {portfolio_id} not found"
                )

            # Get dividend history
            service = CorporateActionsService(conn)
            dividends = await service.get_dividend_history(
                portfolio_id=portfolio_id,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )

            return [DividendHistoryItem(**div) for div in dividends]

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error listing dividends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
