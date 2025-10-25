"""
Trade Execution Service

Handles buy/sell trade execution with lot creation, FIFO lot selection,
and multi-currency support for the DawsOS portfolio system.

Core Responsibilities:
- Execute buy trades (create lots)
- Execute sell trades (FIFO lot selection, realized P&L)
- Multi-currency FX conversion
- Cost basis tracking
- Realized/unrealized P&L calculation

Created: 2025-10-23
"""

from uuid import UUID, uuid4
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import asyncpg
import logging

logger = logging.getLogger(__name__)


class TradeType(str, Enum):
    """Trade type enumeration."""
    BUY = "buy"
    SELL = "sell"


class LotSelectionMethod(str, Enum):
    """Lot selection method for sell trades."""
    FIFO = "fifo"  # First In First Out
    LIFO = "lifo"  # Last In First Out
    HIFO = "hifo"  # Highest In First Out
    SPECIFIC = "specific"  # Specific lot ID


class TradeExecutionError(Exception):
    """Base exception for trade execution errors."""
    pass


class InsufficientSharesError(TradeExecutionError):
    """Raised when attempting to sell more shares than available."""
    pass


class InvalidTradeError(TradeExecutionError):
    """Raised when trade parameters are invalid."""
    pass


class TradeExecutionService:
    """
    Service for executing portfolio trades with lot tracking.

    Handles:
    - Buy trades: Create new lots
    - Sell trades: Close/reduce lots via FIFO (or other methods)
    - Multi-currency trades: FX conversion at trade time
    - Realized P&L calculation
    - Cost basis tracking
    """

    def __init__(self, conn: asyncpg.Connection):
        """
        Initialize trade execution service.

        Args:
            conn: Database connection with RLS context set
        """
        self.conn = conn

    async def execute_buy(
        self,
        portfolio_id: UUID,
        symbol: str,
        qty: Decimal,
        price: Decimal,
        currency: str,
        trade_date: date,
        settlement_date: Optional[date] = None,
        base_currency: Optional[str] = None,
        fx_rate: Optional[Decimal] = None,
        fees: Decimal = Decimal("0"),
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a buy trade, creating a new lot.

        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol (e.g., "AAPL", "VOO")
            qty: Quantity purchased (positive)
            price: Price per share in trade currency
            currency: Trade currency (e.g., "USD", "EUR")
            trade_date: Trade execution date
            settlement_date: Settlement date (defaults to trade_date + 2)
            base_currency: Portfolio base currency (for conversion)
            fx_rate: FX rate from trade currency to base currency
            fees: Trade fees/commissions
            notes: Optional trade notes

        Returns:
            Dict with trade_id, lot_id, total_cost

        Raises:
            InvalidTradeError: If qty <= 0 or price < 0
        """
        # Validation
        if qty <= 0:
            raise InvalidTradeError(f"Buy quantity must be positive, got {qty}")
        if price < 0:
            raise InvalidTradeError(f"Price cannot be negative, got {price}")

        # Default settlement date (T+2)
        if settlement_date is None:
            settlement_date = trade_date

        # Calculate costs in trade currency
        gross_amount = qty * price
        total_cost = gross_amount + fees

        # Multi-currency: convert to base currency if needed
        cost_basis_base_currency = total_cost
        fx_rate_used = Decimal("1.0")

        if base_currency and base_currency != currency:
            if fx_rate is None:
                # TODO: Fetch FX rate from pricing pack or external service
                logger.warning(f"FX rate not provided for {currency}->{base_currency}, using 1.0")
                fx_rate_used = Decimal("1.0")
            else:
                fx_rate_used = fx_rate

            cost_basis_base_currency = total_cost * fx_rate_used

        logger.info(
            f"Executing BUY: {qty} {symbol} @ {price} {currency}, "
            f"total_cost={total_cost}, cost_basis_base={cost_basis_base_currency}"
        )

        # Create transaction record
        trade_id = uuid4()

        async with self.conn.transaction():
            await self.conn.execute(
                """
                INSERT INTO transactions (
                    id, portfolio_id, transaction_type, symbol, qty, price, currency,
                    trade_date, settlement_date, fees, total_amount, notes, created_at
                )
                VALUES ($1, $2, 'buy', $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
                """,
                trade_id, portfolio_id, symbol, qty, price, currency,
                trade_date, settlement_date, fees, total_cost, notes
            )

            # Create lot record
            lot_id = await self._create_lot(
                portfolio_id=portfolio_id,
                symbol=symbol,
                qty=qty,
                cost_basis=cost_basis_base_currency,
                acquisition_date=trade_date,
                currency=base_currency or currency,
                transaction_id=trade_id
            )

        logger.info(f"BUY complete: trade_id={trade_id}, lot_id={lot_id}")

        return {
            "trade_id": trade_id,
            "lot_id": lot_id,
            "symbol": symbol,
            "qty": qty,
            "price": price,
            "currency": currency,
            "total_cost": total_cost,
            "cost_basis_base": cost_basis_base_currency,
            "fx_rate": fx_rate_used,
            "trade_date": trade_date,
            "settlement_date": settlement_date
        }

    async def execute_sell(
        self,
        portfolio_id: UUID,
        symbol: str,
        qty: Decimal,
        price: Decimal,
        currency: str,
        trade_date: date,
        settlement_date: Optional[date] = None,
        lot_selection: LotSelectionMethod = LotSelectionMethod.FIFO,
        specific_lot_id: Optional[UUID] = None,
        base_currency: Optional[str] = None,
        fx_rate: Optional[Decimal] = None,
        fees: Decimal = Decimal("0"),
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a sell trade, closing/reducing lots and calculating realized P&L.

        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol
            qty: Quantity sold (positive)
            price: Sale price per share in trade currency
            currency: Trade currency
            trade_date: Trade execution date
            settlement_date: Settlement date (defaults to trade_date + 2)
            lot_selection: Method for selecting lots (FIFO, LIFO, HIFO, SPECIFIC)
            specific_lot_id: Specific lot ID (if lot_selection=SPECIFIC)
            base_currency: Portfolio base currency
            fx_rate: FX rate from trade currency to base currency
            fees: Trade fees/commissions
            notes: Optional trade notes

        Returns:
            Dict with trade_id, lots_closed, realized_pnl

        Raises:
            InsufficientSharesError: If not enough shares to sell
            InvalidTradeError: If qty <= 0 or price < 0
        """
        # Validation
        if qty <= 0:
            raise InvalidTradeError(f"Sell quantity must be positive, got {qty}")
        if price < 0:
            raise InvalidTradeError(f"Price cannot be negative, got {price}")

        # Default settlement date (T+2)
        if settlement_date is None:
            settlement_date = trade_date

        # Calculate proceeds in trade currency
        gross_proceeds = qty * price
        net_proceeds = gross_proceeds - fees

        # Multi-currency: convert to base currency if needed
        proceeds_base_currency = net_proceeds
        fx_rate_used = Decimal("1.0")

        if base_currency and base_currency != currency:
            if fx_rate is None:
                logger.warning(f"FX rate not provided for {currency}->{base_currency}, using 1.0")
                fx_rate_used = Decimal("1.0")
            else:
                fx_rate_used = fx_rate

            proceeds_base_currency = net_proceeds * fx_rate_used

        logger.info(
            f"Executing SELL: {qty} {symbol} @ {price} {currency}, "
            f"net_proceeds={net_proceeds}, proceeds_base={proceeds_base_currency}"
        )

        # Get open lots for this symbol
        open_lots = await self._get_open_lots(
            portfolio_id=portfolio_id,
            symbol=symbol,
            lot_selection=lot_selection,
            specific_lot_id=specific_lot_id
        )

        # Check sufficient shares
        total_available = sum(lot["qty_open"] for lot in open_lots)
        if total_available < qty:
            raise InsufficientSharesError(
                f"Insufficient shares to sell: need {qty}, have {total_available} {symbol}"
            )

        # Create transaction record
        trade_id = uuid4()

        async with self.conn.transaction():
            await self.conn.execute(
                """
                INSERT INTO transactions (
                    id, portfolio_id, transaction_type, symbol, qty, price, currency,
                    trade_date, settlement_date, fees, total_amount, notes, created_at
                )
                VALUES ($1, $2, 'sell', $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
                """,
                trade_id, portfolio_id, symbol, -qty, price, currency,
                trade_date, settlement_date, fees, net_proceeds, notes
            )

            # Close/reduce lots and calculate realized P&L
            lots_closed, realized_pnl = await self._close_lots(
                portfolio_id=portfolio_id,
                open_lots=open_lots,
                qty_to_sell=qty,
                proceeds_per_share=proceeds_base_currency / qty,
                trade_date=trade_date,
                transaction_id=trade_id
            )

        logger.info(
            f"SELL complete: trade_id={trade_id}, lots_closed={len(lots_closed)}, "
            f"realized_pnl={realized_pnl}"
        )

        return {
            "trade_id": trade_id,
            "symbol": symbol,
            "qty": qty,
            "price": price,
            "currency": currency,
            "net_proceeds": net_proceeds,
            "proceeds_base": proceeds_base_currency,
            "fx_rate": fx_rate_used,
            "lots_closed": lots_closed,
            "realized_pnl": realized_pnl,
            "trade_date": trade_date,
            "settlement_date": settlement_date
        }

    async def _create_lot(
        self,
        portfolio_id: UUID,
        symbol: str,
        qty: Decimal,
        cost_basis: Decimal,
        acquisition_date: date,
        currency: str,
        transaction_id: Optional[UUID] = None
    ) -> UUID:
        """
        Create a new lot record.

        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol
            qty: Lot quantity
            cost_basis: Total cost basis in base currency
            acquisition_date: Acquisition date
            currency: Base currency
            transaction_id: Related transaction ID

        Returns:
            Lot UUID
        """
        lot_id = uuid4()

        await self.conn.execute(
            """
            INSERT INTO lots (
                id, portfolio_id, symbol, qty_original, qty_open,
                cost_basis, acquisition_date, currency, transaction_id, created_at
            )
            VALUES ($1, $2, $3, $4, $4, $5, $6, $7, $8, NOW())
            """,
            lot_id, portfolio_id, symbol, qty, cost_basis,
            acquisition_date, currency, transaction_id
        )

        logger.debug(
            f"Created lot: lot_id={lot_id}, symbol={symbol}, qty={qty}, "
            f"cost_basis={cost_basis}"
        )

        return lot_id

    async def _get_open_lots(
        self,
        portfolio_id: UUID,
        symbol: str,
        lot_selection: LotSelectionMethod,
        specific_lot_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get open lots for a symbol, sorted by lot selection method.

        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol
            lot_selection: Lot selection method (FIFO, LIFO, HIFO, SPECIFIC)
            specific_lot_id: Specific lot ID (if SPECIFIC)

        Returns:
            List of lot records sorted by selection method

        Raises:
            InvalidTradeError: If SPECIFIC lot not found or closed
        """
        if lot_selection == LotSelectionMethod.SPECIFIC:
            if not specific_lot_id:
                raise InvalidTradeError("specific_lot_id required for SPECIFIC lot selection")

            # Get specific lot
            row = await self.conn.fetchrow(
                """
                SELECT id, symbol, qty_open, cost_basis, acquisition_date, currency
                FROM lots
                WHERE portfolio_id = $1 AND id = $2 AND qty_open > 0
                """,
                portfolio_id, specific_lot_id
            )

            if not row:
                raise InvalidTradeError(f"Lot {specific_lot_id} not found or already closed")

            return [dict(row)]

        # Determine sort order based on lot selection method
        if lot_selection == LotSelectionMethod.FIFO:
            order_by = "acquisition_date ASC, created_at ASC"
        elif lot_selection == LotSelectionMethod.LIFO:
            order_by = "acquisition_date DESC, created_at DESC"
        elif lot_selection == LotSelectionMethod.HIFO:
            # Highest cost basis per share first (maximize tax loss harvesting)
            order_by = "(cost_basis / qty_original) DESC, acquisition_date ASC"
        else:
            raise InvalidTradeError(f"Unsupported lot selection method: {lot_selection}")

        # Get open lots sorted by selection method
        rows = await self.conn.fetch(
            f"""
            SELECT id, symbol, qty_open, cost_basis, acquisition_date, currency
            FROM lots
            WHERE portfolio_id = $1 AND symbol = $2 AND qty_open > 0
            ORDER BY {order_by}
            """,
            portfolio_id, symbol
        )

        return [dict(row) for row in rows]

    async def _close_lots(
        self,
        portfolio_id: UUID,
        open_lots: List[Dict[str, Any]],
        qty_to_sell: Decimal,
        proceeds_per_share: Decimal,
        trade_date: date,
        transaction_id: UUID
    ) -> Tuple[List[Dict[str, Any]], Decimal]:
        """
        Close/reduce lots and calculate realized P&L.

        Args:
            portfolio_id: Portfolio UUID
            open_lots: List of open lots (sorted by selection method)
            qty_to_sell: Total quantity to sell
            proceeds_per_share: Proceeds per share (in base currency)
            trade_date: Trade date
            transaction_id: Related transaction ID

        Returns:
            Tuple of (lots_closed, total_realized_pnl)
        """
        lots_closed = []
        total_realized_pnl = Decimal("0")
        remaining_qty = qty_to_sell

        for lot in open_lots:
            if remaining_qty <= 0:
                break

            lot_id = lot["id"]
            qty_open = lot["qty_open"]
            cost_basis_total = lot["cost_basis"]

            # Determine how much to close from this lot
            qty_to_close = min(remaining_qty, qty_open)

            # Calculate proportional cost basis
            cost_basis_per_share = cost_basis_total / lot["qty_open"]
            cost_basis_closed = qty_to_close * cost_basis_per_share

            # Calculate realized P&L for this lot
            proceeds_closed = qty_to_close * proceeds_per_share
            realized_pnl = proceeds_closed - cost_basis_closed

            # Update lot qty_open
            new_qty_open = qty_open - qty_to_close

            await self.conn.execute(
                """
                UPDATE lots
                SET qty_open = $1,
                    closed_date = CASE WHEN $1 = 0 THEN $2 ELSE NULL END,
                    updated_at = NOW()
                WHERE id = $3
                """,
                new_qty_open, trade_date if new_qty_open == 0 else None, lot_id
            )

            logger.debug(
                f"Closed lot: lot_id={lot_id}, qty_closed={qty_to_close}, "
                f"cost_basis={cost_basis_closed}, proceeds={proceeds_closed}, "
                f"realized_pnl={realized_pnl}"
            )

            lots_closed.append({
                "lot_id": lot_id,
                "symbol": lot["symbol"],
                "qty_closed": qty_to_close,
                "cost_basis": cost_basis_closed,
                "proceeds": proceeds_closed,
                "realized_pnl": realized_pnl,
                "acquisition_date": lot["acquisition_date"],
                "disposition_date": trade_date
            })

            total_realized_pnl += realized_pnl
            remaining_qty -= qty_to_close

        return lots_closed, total_realized_pnl

    async def get_portfolio_positions(
        self,
        portfolio_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get current positions from open lots.

        Args:
            portfolio_id: Portfolio UUID

        Returns:
            List of positions with qty, cost_basis, unrealized P&L
        """
        rows = await self.conn.fetch(
            """
            SELECT
                symbol,
                SUM(qty_open) as qty,
                SUM(cost_basis * qty_open / qty_original) as cost_basis,
                currency
            FROM lots
            WHERE portfolio_id = $1 AND qty_open > 0
            GROUP BY symbol, currency
            ORDER BY symbol
            """,
            portfolio_id
        )

        positions = []
        for row in rows:
            positions.append({
                "symbol": row["symbol"],
                "qty": row["qty"],
                "cost_basis": row["cost_basis"],
                "currency": row["currency"],
                # Note: unrealized P&L requires current market price (not available here)
            })

        return positions

    async def get_realized_pnl(
        self,
        portfolio_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Decimal:
        """
        Get total realized P&L for a portfolio in a date range.

        Args:
            portfolio_id: Portfolio UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Total realized P&L
        """
        # TODO: Implement once we have realized_pnl tracking
        # For now, calculate from closed lots

        query = """
            SELECT
                l.id as lot_id,
                l.cost_basis,
                l.qty_original,
                l.qty_open,
                t.qty as sold_qty,
                t.total_amount as proceeds
            FROM lots l
            JOIN transactions t ON t.portfolio_id = l.portfolio_id
                AND t.symbol = l.symbol
                AND t.transaction_type = 'sell'
            WHERE l.portfolio_id = $1
                AND l.qty_open < l.qty_original
        """

        params = [portfolio_id]

        if start_date:
            query += " AND t.trade_date >= $2"
            params.append(start_date)

        if end_date:
            param_idx = 3 if start_date else 2
            query += f" AND t.trade_date <= ${param_idx}"
            params.append(end_date)

        # Note: This is a simplified calculation
        # Proper implementation should track realized P&L at transaction time

        logger.warning("get_realized_pnl is using simplified calculation")

        return Decimal("0")  # Placeholder
