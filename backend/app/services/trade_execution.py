"""
Trade Execution Service v2

Schema-aligned version that matches the actual database schema.

Database Schema (as of 2025-10-23):
- lots: quantity_original, quantity_open, closed_date, quantity, is_open
- transactions: transaction_date, quantity, amount, fee, narration

Created: 2025-10-23
"""

from uuid import UUID, uuid4
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import asyncpg
import logging

logger = logging.getLogger(__name__)


class TradeType(str, Enum):
    """Trade type enumeration."""
    BUY = "BUY"  # Match DB constraint (uppercase)
    SELL = "SELL"


class LotSelectionMethod(str, Enum):
    """Lot selection method for sell trades."""
    FIFO = "fifo"
    LIFO = "lifo"
    HIFO = "hifo"
    SPECIFIC = "specific"


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
            settlement_date: Settlement date (defaults to trade_date)
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

        # Default settlement date
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
        
        # Lookup security from securities table
        security_row = await self.conn.fetchrow(
            "SELECT id FROM securities WHERE symbol = $1",
            symbol
        )
        
        if security_row:
            security_id = security_row['id']
            logger.info(f"Found existing security for {symbol}: {security_id}")
        else:
            # Create new security if it doesn't exist
            security_id = uuid4()
            await self.conn.execute(
                """
                INSERT INTO securities (id, symbol, name, security_type, currency, created_at)
                VALUES ($1, $2, $3, 'EQUITY', $4, NOW())
                ON CONFLICT (symbol) DO UPDATE SET updated_at = NOW()
                """,
                security_id, symbol, symbol, currency  # Use symbol as name if not provided
            )
            logger.info(f"Created new security for {symbol}: {security_id}")

        async with self.conn.transaction():
            await self.conn.execute(
                """
                INSERT INTO transactions (
                    id, portfolio_id, transaction_type, security_id, symbol,
                    transaction_date, settlement_date, quantity, price, amount,
                    currency, fee, narration, source, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'manual', NOW())
                """,
                trade_id, portfolio_id, "BUY", security_id, symbol,
                trade_date, settlement_date, qty, price, -total_cost,  # Negative = outflow
                currency, fees, notes
            )

            # Create lot record
            lot_id = await self._create_lot(
                portfolio_id=portfolio_id,
                security_id=security_id,
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
        lot_selection: Optional[LotSelectionMethod] = None,
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
            settlement_date: Settlement date (defaults to trade_date)
            lot_selection: Method for selecting lots (None=use portfolio default, FIFO, LIFO, HIFO, SPECIFIC)
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
        
        # Get portfolio's cost basis method if not specified
        if lot_selection is None:
            portfolio_row = await self.conn.fetchrow(
                "SELECT cost_basis_method FROM portfolios WHERE id = $1",
                portfolio_id
            )
            if portfolio_row:
                method_str = portfolio_row["cost_basis_method"]
                # Map database value to enum
                method_mapping = {
                    "FIFO": LotSelectionMethod.FIFO,
                    "LIFO": LotSelectionMethod.LIFO,
                    "HIFO": LotSelectionMethod.HIFO,
                    "SPECIFIC_LOT": LotSelectionMethod.SPECIFIC,
                    "AVERAGE_COST": LotSelectionMethod.FIFO  # Fallback to FIFO for average cost
                }
                lot_selection = method_mapping.get(method_str, LotSelectionMethod.FIFO)
                logger.info(f"Using portfolio cost_basis_method: {method_str} -> {lot_selection}")
            else:
                lot_selection = LotSelectionMethod.FIFO

        # Default settlement date
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
        total_available = sum(lot["quantity_open"] for lot in open_lots)
        if total_available < qty:
            raise InsufficientSharesError(
                f"Insufficient shares to sell: need {qty}, have {total_available} {symbol}"
            )

        # Create transaction record
        trade_id = uuid4()
        security_id = open_lots[0]["security_id"] if open_lots else uuid4()

        async with self.conn.transaction():
            await self.conn.execute(
                """
                INSERT INTO transactions (
                    id, portfolio_id, transaction_type, security_id, symbol,
                    transaction_date, settlement_date, quantity, price, amount,
                    currency, fee, narration, source, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'manual', NOW())
                """,
                trade_id, portfolio_id, "SELL", security_id, symbol,
                trade_date, settlement_date, qty, price, net_proceeds,  # Positive = inflow
                currency, fees, notes
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
            
            # Update transaction with realized P&L for tax reporting (IRS compliance)
            await self.conn.execute(
                """
                UPDATE transactions
                SET realized_pl = $1
                WHERE id = $2
                """,
                realized_pnl, trade_id
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
        security_id: UUID,
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
            security_id: Security UUID
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
        cost_basis_per_share = cost_basis / qty

        await self.conn.execute(
            """
            INSERT INTO lots (
                id, portfolio_id, security_id, symbol,
                acquisition_date, quantity_original, quantity_open, quantity,
                cost_basis, cost_basis_per_share, currency, is_open, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $6, $6, $7, $8, $9, true, NOW())
            """,
            lot_id, portfolio_id, security_id, symbol,
            acquisition_date, qty, cost_basis, cost_basis_per_share, currency
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
                SELECT id, security_id, symbol, qty_open AS quantity_open, cost_basis, acquisition_date, currency
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
            SELECT id, security_id, symbol, qty_open AS quantity_open, cost_basis, acquisition_date, currency, qty_original AS quantity_original
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
            quantity_open = lot["quantity_open"]
            cost_basis_total = lot["cost_basis"]
            quantity_original = lot["quantity_original"]

            # Determine how much to close from this lot
            qty_to_close = min(remaining_qty, quantity_open)

            # Calculate proportional cost basis
            cost_basis_per_share = cost_basis_total / quantity_original
            cost_basis_closed = qty_to_close * cost_basis_per_share

            # Calculate realized P&L for this lot
            proceeds_closed = qty_to_close * proceeds_per_share
            realized_pnl = proceeds_closed - cost_basis_closed

            # Update lot quantity_open
            new_quantity_open = quantity_open - qty_to_close

            await self.conn.execute(
                """
                UPDATE lots
                SET qty_open = $1,
                    quantity = $1,
                    closed_date = CASE WHEN $1 = 0 THEN $2 ELSE NULL END,
                    is_open = CASE WHEN $1 = 0 THEN false ELSE true END,
                    updated_at = NOW()
                WHERE id = $3
                """,
                new_quantity_open, trade_date if new_quantity_open == 0 else None, lot_id
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
