"""
Trade API Endpoints

RESTful API for executing trades and viewing positions/lots.

Endpoints:
- POST /v1/trades - Execute buy/sell trade
- GET /v1/trades - List trades for a portfolio
- GET /v1/lots - View open lots for a portfolio
- GET /v1/positions - View current positions

Created: 2025-10-23
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
import logging

from app.db.connection import get_db_connection_with_rls
from app.services.trade_execution import (
    TradeExecutionService,
    TradeType,
    LotSelectionMethod,
    TradeExecutionError,
    InsufficientSharesError,
    InvalidTradeError
)
from app.middleware.auth_middleware import verify_token
from app.core.di_container import ensure_initialized

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/trades", tags=["trades"])


# ============================================================================
# Pydantic Models
# ============================================================================

class TradeRequest(BaseModel):
    """Request model for executing a trade."""

    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    symbol: str = Field(..., min_length=1, max_length=20, description="Security symbol (e.g., AAPL)")
    trade_type: Literal["buy", "sell"] = Field(..., description="Trade type (buy or sell)")
    qty: Decimal = Field(..., gt=0, description="Quantity (positive)")
    price: Decimal = Field(..., ge=0, description="Price per share")
    currency: str = Field(..., pattern="^[A-Z]{3}$", description="Trade currency (ISO 4217)")
    trade_date: date = Field(..., description="Trade execution date")
    settlement_date: Optional[date] = Field(None, description="Settlement date (defaults to T+2)")
    lot_selection: Optional[Literal["fifo", "lifo", "hifo", "specific"]] = Field(
        "fifo",
        description="Lot selection method for sells"
    )
    specific_lot_id: Optional[UUID] = Field(None, description="Specific lot ID (if lot_selection=specific)")
    base_currency: Optional[str] = Field(None, pattern="^[A-Z]{3}$", description="Portfolio base currency")
    fx_rate: Optional[Decimal] = Field(None, gt=0, description="FX rate (trade_currency -> base_currency)")
    fees: Decimal = Field(Decimal("0"), ge=0, description="Trade fees/commissions")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional trade notes")

    @validator("specific_lot_id")
    def validate_specific_lot(cls, v, values):
        """Validate specific_lot_id is provided when lot_selection=specific."""
        if values.get("lot_selection") == "specific" and not v:
            raise ValueError("specific_lot_id required when lot_selection=specific")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
                "symbol": "AAPL",
                "trade_type": "buy",
                "qty": 10,
                "price": 150.50,
                "currency": "USD",
                "trade_date": "2025-10-23",
                "fees": 1.00,
                "notes": "Initial AAPL position"
            }
        }


class LotInfo(BaseModel):
    """Lot information in trade response."""

    lot_id: UUID
    symbol: str
    qty_closed: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
    proceeds: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    acquisition_date: Optional[date] = None
    disposition_date: Optional[date] = None


class TradeResponse(BaseModel):
    """Response model for trade execution."""

    trade_id: UUID
    symbol: str
    trade_type: str
    qty: Decimal
    price: Decimal
    currency: str
    total_cost: Optional[Decimal] = None  # For buys
    net_proceeds: Optional[Decimal] = None  # For sells
    cost_basis_base: Optional[Decimal] = None  # For buys
    proceeds_base: Optional[Decimal] = None  # For sells
    fx_rate: Decimal
    trade_date: date
    settlement_date: date
    lot_id: Optional[UUID] = None  # For buys (single lot created)
    lots_closed: Optional[List[LotInfo]] = None  # For sells
    realized_pnl: Optional[Decimal] = None  # For sells
    fees: Decimal
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "trade_id": "123e4567-e89b-12d3-a456-426614174000",
                "symbol": "AAPL",
                "trade_type": "buy",
                "qty": 10,
                "price": 150.50,
                "currency": "USD",
                "total_cost": 1506.00,
                "cost_basis_base": 1506.00,
                "fx_rate": 1.0,
                "trade_date": "2025-10-23",
                "settlement_date": "2025-10-25",
                "lot_id": "456e7890-e89b-12d3-a456-426614174001",
                "fees": 1.00
            }
        }


class TransactionListItem(BaseModel):
    """Transaction list item."""

    id: UUID
    portfolio_id: UUID
    transaction_type: str
    symbol: Optional[str]
    quantity: Optional[Decimal]
    price: Optional[Decimal]
    currency: str
    transaction_date: date
    settlement_date: Optional[date]
    fee: Decimal
    amount: Decimal
    narration: Optional[str]
    created_at: datetime


class LotListItem(BaseModel):
    """Lot list item."""

    id: UUID
    portfolio_id: UUID
    symbol: str
    quantity_original: Decimal
    quantity_open: Decimal
    quantity: Decimal
    cost_basis: Decimal
    acquisition_date: date
    closed_date: Optional[date]
    is_open: bool
    currency: str
    created_at: datetime


class PositionItem(BaseModel):
    """Position item with current holdings."""

    symbol: str
    qty: Decimal
    cost_basis: Decimal
    avg_cost: Decimal
    currency: str
    # Note: market_value and unrealized_pnl require pricing data


# ============================================================================
# Dependencies
# ============================================================================

def get_user_id_from_claims(claims: dict) -> UUID:
    """
    Extract user_id from JWT claims and convert to UUID.

    Args:
        claims: JWT claims dict from verify_token dependency

    Returns:
        User UUID

    Raises:
        HTTPException: If user_id is invalid
    """
    user_id_str = claims.get("user_id")
    if not user_id_str:
        raise HTTPException(
            status_code=401,
            detail="JWT token missing user_id claim"
        )

    try:
        return UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id format in JWT token (must be UUID)"
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("", response_model=TradeResponse, status_code=201)
async def execute_trade(
    trade: TradeRequest,
    claims: dict = Depends(verify_token)
) -> TradeResponse:
    """
    Execute a buy or sell trade.

    **Buy Trade**:
    - Creates a new lot with cost basis
    - Records transaction

    **Sell Trade**:
    - Closes/reduces lots using specified selection method (default: FIFO)
    - Calculates realized P&L
    - Records transaction

    **Multi-Currency**:
    - If trade currency != base currency, provide fx_rate
    - Cost basis/proceeds converted to base currency

    **RLS**: Automatically filtered to user's portfolios

    **UAT Coverage**: UAT-003, UAT-004, UAT-005
    """
    user_id = get_user_id_from_claims(claims)
    user_role = claims.get("role", "USER")
    
    # RBAC: Check permission to write trades
    container = ensure_initialized()
    auth_service = container.resolve("auth")
    if not auth_service.check_permission(user_role, "write_trades"):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to execute trades"
        )
    
    logger.info(
        f"Trade request: user_id={user_id}, portfolio_id={trade.portfolio_id}, "
        f"type={trade.trade_type}, symbol={trade.symbol}, qty={trade.qty}, role={user_role}"
    )

    try:
        async with get_db_connection_with_rls(str(user_id)) as conn:
            # Verify portfolio exists and belongs to user (RLS enforced)
            portfolio = await conn.fetchrow(
                "SELECT id, base_currency FROM portfolios WHERE id = $1 AND is_active = true",
                trade.portfolio_id
            )

            if not portfolio:
                raise HTTPException(
                    status_code=404,
                    detail=f"Portfolio {trade.portfolio_id} not found or inactive"
                )

            # Use portfolio base currency if not provided
            base_currency = trade.base_currency or portfolio["base_currency"]

            # Initialize trade execution service
            service = TradeExecutionService(conn)

            # Execute trade
            if trade.trade_type == "buy":
                result = await service.execute_buy(
                    portfolio_id=trade.portfolio_id,
                    symbol=trade.symbol,
                    qty=trade.qty,
                    price=trade.price,
                    currency=trade.currency,
                    trade_date=trade.trade_date,
                    settlement_date=trade.settlement_date,
                    base_currency=base_currency,
                    fx_rate=trade.fx_rate,
                    fees=trade.fees,
                    notes=trade.notes
                )

                return TradeResponse(
                    trade_id=result["trade_id"],
                    symbol=result["symbol"],
                    trade_type="buy",
                    qty=result["qty"],
                    price=result["price"],
                    currency=result["currency"],
                    total_cost=result["total_cost"],
                    cost_basis_base=result["cost_basis_base"],
                    fx_rate=result["fx_rate"],
                    trade_date=result["trade_date"],
                    settlement_date=result["settlement_date"],
                    lot_id=result["lot_id"],
                    fees=trade.fees,
                    notes=trade.notes
                )

            else:  # sell
                result = await service.execute_sell(
                    portfolio_id=trade.portfolio_id,
                    symbol=trade.symbol,
                    qty=trade.qty,
                    price=trade.price,
                    currency=trade.currency,
                    trade_date=trade.trade_date,
                    settlement_date=trade.settlement_date,
                    lot_selection=LotSelectionMethod(trade.lot_selection),
                    specific_lot_id=trade.specific_lot_id,
                    base_currency=base_currency,
                    fx_rate=trade.fx_rate,
                    fees=trade.fees,
                    notes=trade.notes
                )

                lots_closed = [
                    LotInfo(
                        lot_id=lot["lot_id"],
                        symbol=lot["symbol"],
                        qty_closed=lot["qty_closed"],
                        cost_basis=lot["cost_basis"],
                        proceeds=lot["proceeds"],
                        realized_pnl=lot["realized_pnl"],
                        acquisition_date=lot["acquisition_date"],
                        disposition_date=lot["disposition_date"]
                    )
                    for lot in result["lots_closed"]
                ]

                return TradeResponse(
                    trade_id=result["trade_id"],
                    symbol=result["symbol"],
                    trade_type="sell",
                    qty=result["qty"],
                    price=result["price"],
                    currency=result["currency"],
                    net_proceeds=result["net_proceeds"],
                    proceeds_base=result["proceeds_base"],
                    fx_rate=result["fx_rate"],
                    trade_date=result["trade_date"],
                    settlement_date=result["settlement_date"],
                    lots_closed=lots_closed,
                    realized_pnl=result["realized_pnl"],
                    fees=trade.fees,
                    notes=trade.notes
                )

    except InsufficientSharesError as e:
        logger.warning(f"Insufficient shares: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except InvalidTradeError as e:
        logger.warning(f"Invalid trade: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except TradeExecutionError as e:
        logger.error(f"Trade execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {e}")

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        # Programming errors - should not happen, log and re-raise as HTTPException
        logger.error(f"Programming error executing trade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error (programming error): {str(e)}")
    except Exception as e:
        # Service/database errors - log and re-raise as HTTPException
        logger.error(f"Unexpected error executing trade: {e}", exc_info=True)
        # Don't raise DatabaseError here - convert to HTTPException is intentional
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=List[TransactionListItem])
async def list_trades(
    portfolio_id: UUID,
    claims: dict = Depends(verify_token),
    symbol: Optional[str] = None,
    trade_type: Optional[Literal["buy", "sell"]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000)
) -> List[TransactionListItem]:
    """
    List trades for a portfolio.

    **Filters**:
    - symbol: Filter by symbol
    - trade_type: Filter by buy/sell
    - start_date: Filter by trade_date >= start_date
    - end_date: Filter by trade_date <= end_date
    - limit: Max results (default 100, max 1000)

    **RLS**: Automatically filtered to user's portfolios

    **UAT Coverage**: UAT-006
    """
    user_id = get_user_id_from_claims(claims)
    logger.info(
        f"List trades: user_id={user_id}, portfolio_id={portfolio_id}, "
        f"symbol={symbol}, type={trade_type}"
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

            # Build query
            query = """
                SELECT id, portfolio_id, transaction_type, symbol, quantity, price, currency,
                       transaction_date, settlement_date, fee, amount, narration, created_at
                FROM transactions
                WHERE portfolio_id = $1
            """
            params = [portfolio_id]
            param_idx = 2

            if symbol:
                query += f" AND symbol = ${param_idx}"
                params.append(symbol)
                param_idx += 1

            if trade_type:
                query += f" AND transaction_type = ${param_idx}"
                params.append(trade_type.upper())  # DB uses uppercase
                param_idx += 1

            if start_date:
                query += f" AND transaction_date >= ${param_idx}"
                params.append(start_date)
                param_idx += 1

            if end_date:
                query += f" AND transaction_date <= ${param_idx}"
                params.append(end_date)
                param_idx += 1

            query += f" ORDER BY transaction_date DESC, created_at DESC LIMIT ${param_idx}"
            params.append(limit)

            rows = await conn.fetch(query, *params)

            return [TransactionListItem(**row) for row in rows]

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error listing trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/lots", response_model=List[LotListItem])
async def list_lots(
    portfolio_id: UUID,
    claims: dict = Depends(verify_token),
    symbol: Optional[str] = None,
    open_only: bool = Query(True, description="Show only open lots")
) -> List[LotListItem]:
    """
    List lots for a portfolio.

    **Filters**:
    - symbol: Filter by symbol
    - open_only: Show only open lots (default true)

    **RLS**: Automatically filtered to user's portfolios

    **UAT Coverage**: UAT-007
    """
    user_id = get_user_id_from_claims(claims)
    logger.info(
        f"List lots: user_id={user_id}, portfolio_id={portfolio_id}, "
        f"symbol={symbol}, open_only={open_only}"
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

            # Build query
            query = """
                SELECT id, portfolio_id, symbol, quantity_original, quantity_open, quantity,
                       cost_basis, acquisition_date, closed_date, is_open, currency, created_at
                FROM lots
                WHERE portfolio_id = $1
            """
            params = [portfolio_id]
            param_idx = 2

            if open_only:
                query += " AND quantity_open > 0"

            if symbol:
                query += f" AND symbol = ${param_idx}"
                params.append(symbol)
                param_idx += 1

            query += " ORDER BY acquisition_date ASC, created_at ASC"

            rows = await conn.fetch(query, *params)

            return [LotListItem(**row) for row in rows]

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error listing lots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/positions", response_model=List[PositionItem])
async def list_positions(
    portfolio_id: UUID,
    claims: dict = Depends(verify_token)
) -> List[PositionItem]:
    """
    List current positions for a portfolio (aggregated from open lots).

    **Position Calculation**:
    - qty: Sum of quantity_open across all open lots
    - cost_basis: Weighted average cost basis
    - avg_cost: cost_basis / qty

    **RLS**: Automatically filtered to user's portfolios

    **UAT Coverage**: UAT-008
    """
    user_id = get_user_id_from_claims(claims)
    logger.info(f"List positions: user_id={user_id}, portfolio_id={portfolio_id}")

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

            # Get positions from open lots
            service = TradeExecutionService(conn)
            positions = await service.get_portfolio_positions(portfolio_id)

            return [
                PositionItem(
                    symbol=pos["symbol"],
                    qty=pos["qty"],
                    cost_basis=pos["cost_basis"],
                    avg_cost=pos["cost_basis"] / pos["qty"] if pos["qty"] > 0 else Decimal("0"),
                    currency=pos["currency"]
                )
                for pos in positions
            ]

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error listing positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
