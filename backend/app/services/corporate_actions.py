"""
Corporate Actions Service

Handles portfolio corporate actions:
- Dividends (with gross/withholding/net tracking and ADR pay-date FX)
- Stock splits (adjust all open lots)
- ADR withholding tax

Critical Rule: ADR dividends MUST use pay-date FX rate (not ex-date FX).

Created: 2025-10-23
"""

from uuid import UUID, uuid4
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum
import asyncpg
import logging

logger = logging.getLogger(__name__)


class CorporateActionType(str, Enum):
    """Corporate action type enumeration."""
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"
    WITHHOLDING_TAX = "WITHHOLDING_TAX"


class CorporateActionError(Exception):
    """Base exception for corporate action errors."""
    pass


class InvalidCorporateActionError(CorporateActionError):
    """Raised when corporate action parameters are invalid."""
    pass


class InsufficientDataError(CorporateActionError):
    """Raised when required data is missing (e.g., FX rate not found)."""
    pass


class CorporateActionsService:
    """
    Service for recording portfolio corporate actions.

    Handles:
    - Dividend recording with gross/withholding/net tracking
    - ADR pay-date FX conversion (critical for accuracy)
    - Stock splits (adjust all open lots for symbol)
    - ADR withholding tax recording
    """

    def __init__(self, conn: asyncpg.Connection):
        """
        Initialize corporate actions service.

        Args:
            conn: Database connection with RLS context set
        """
        self.conn = conn

    async def _get_security_id(self, symbol: str) -> UUID:
        """
        Lookup security_id from symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")

        Returns:
            security_id UUID

        Raises:
            InvalidCorporateActionError: If security not found
        """
        row = await self.conn.fetchrow(
            "SELECT id FROM securities WHERE symbol = $1",
            symbol
        )
        if not row:
            raise InvalidCorporateActionError(
                f"Security not found: {symbol}. "
                f"Please add security to database before recording corporate action."
            )
        return row["id"]

    async def record_dividend(
        self,
        portfolio_id: UUID,
        symbol: str,
        shares: Decimal,
        dividend_per_share: Decimal,
        currency: str,
        ex_date: date,
        pay_date: date,
        withholding_tax: Decimal = Decimal("0"),
        base_currency: Optional[str] = None,
        pay_fx_rate: Optional[Decimal] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a dividend payment.

        **CRITICAL**: For ADR dividends, must use pay-date FX rate (not ex-date).

        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol (e.g., "AAPL")
            shares: Number of shares held
            dividend_per_share: Dividend per share in dividend currency
            currency: Dividend currency (e.g., "USD")
            ex_date: Ex-dividend date (for reference only)
            pay_date: Payment date (CRITICAL: used for FX rate lookup)
            withholding_tax: Tax withheld (in dividend currency)
            base_currency: Portfolio base currency (for conversion)
            pay_fx_rate: FX rate at pay date (base to quote)
            notes: Optional notes

        Returns:
            Dict with transaction_id, gross_amount, net_amount, etc.

        Raises:
            InvalidCorporateActionError: If parameters invalid
            InsufficientDataError: If FX rate required but not provided
        """
        # Validation
        if shares <= 0:
            raise InvalidCorporateActionError(f"Shares must be positive, got {shares}")
        if dividend_per_share <= 0:
            raise InvalidCorporateActionError(f"Dividend per share must be positive, got {dividend_per_share}")
        if withholding_tax < 0:
            raise InvalidCorporateActionError(f"Withholding tax cannot be negative, got {withholding_tax}")
        if pay_date < ex_date:
            raise InvalidCorporateActionError(f"Pay date {pay_date} cannot be before ex-date {ex_date}")

        # Calculate gross, withholding, net amounts
        gross_amount = shares * dividend_per_share
        withholding_amount = shares * withholding_tax
        net_amount = gross_amount - withholding_amount

        # Multi-currency: convert to base currency using PAY-DATE FX
        net_amount_base_currency = net_amount
        pay_fx_rate_id = None
        pay_fx_rate_used = Decimal("1.0")

        if base_currency and base_currency != currency:
            # CRITICAL: Must use pay-date FX rate for ADR dividends
            if pay_fx_rate is None:
                # Try to get FX rate from database
                logger.info(f"Looking up FX rate for {currency} to {base_currency} on {pay_date}")
                pay_fx_rate_id, pay_fx_rate_used = await self._get_or_create_fx_rate(
                    asof_date=pay_date,
                    base_currency=currency,
                    quote_currency=base_currency,
                    rate=None  # Will fetch from DB
                )
                if pay_fx_rate_id is None:
                    raise InsufficientDataError(
                        f"FX rate for {currency}->{base_currency} on pay date {pay_date} not found. "
                        f"Please provide pay_fx_rate parameter or insert FX rate into database."
                    )
            else:
                # Store provided FX rate
                pay_fx_rate_used = pay_fx_rate
                pay_fx_rate_id, _ = await self._get_or_create_fx_rate(
                    asof_date=pay_date,
                    base_currency=currency,
                    quote_currency=base_currency,
                    rate=pay_fx_rate_used
                )

            net_amount_base_currency = net_amount * pay_fx_rate_used

        logger.info(
            f"Recording DIVIDEND: {shares} {symbol} @ {dividend_per_share} {currency}, "
            f"gross={gross_amount}, withholding={withholding_amount}, net={net_amount}, "
            f"pay_date={pay_date}, pay_fx_rate={pay_fx_rate_used}, net_base={net_amount_base_currency}"
        )

        # Create transaction record
        transaction_id = uuid4()
        security_id = await self._get_security_id(symbol)

        async with self.conn.transaction():
            await self.conn.execute(
                """
                INSERT INTO transactions (
                    id, portfolio_id, transaction_type, security_id, symbol,
                    transaction_date, ex_date, pay_date, quantity, price, amount,
                    currency, fee, pay_fx_rate_id, narration, source, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, 'manual', NOW())
                """,
                transaction_id, portfolio_id, "DIVIDEND", security_id, symbol,
                pay_date, ex_date, pay_date, shares, dividend_per_share, net_amount_base_currency,
                currency, Decimal("0"), pay_fx_rate_id, notes
            )

        logger.info(f"DIVIDEND recorded: transaction_id={transaction_id}")

        return {
            "transaction_id": transaction_id,
            "symbol": symbol,
            "shares": shares,
            "dividend_per_share": dividend_per_share,
            "currency": currency,
            "gross_amount": gross_amount,
            "withholding_amount": withholding_amount,
            "net_amount": net_amount,
            "ex_date": ex_date,
            "pay_date": pay_date,
            "pay_fx_rate": pay_fx_rate_used,
            "pay_fx_rate_id": pay_fx_rate_id,
            "net_amount_base": net_amount_base_currency,
            "base_currency": base_currency or currency
        }

    async def record_split(
        self,
        portfolio_id: UUID,
        symbol: str,
        split_ratio: Decimal,
        split_date: date,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a stock split and adjust all open lots.

        Example: 2-for-1 split -> split_ratio = 2.0
        Example: 1-for-2 reverse split -> split_ratio = 0.5

        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol
            split_ratio: Split ratio (new shares / old shares)
            split_date: Split effective date
            notes: Optional notes

        Returns:
            Dict with transaction_id, lots_adjusted, etc.

        Raises:
            InvalidCorporateActionError: If parameters invalid
        """
        # Validation
        if split_ratio <= 0:
            raise InvalidCorporateActionError(f"Split ratio must be positive, got {split_ratio}")

        logger.info(
            f"Recording SPLIT: {symbol} {split_ratio}:1 on {split_date}"
        )

        # Get all open lots for this symbol
        open_lots = await self._get_open_lots(portfolio_id, symbol)

        if not open_lots:
            logger.warning(f"No open lots found for {symbol} in portfolio {portfolio_id}")
            return {
                "transaction_id": None,
                "symbol": symbol,
                "split_ratio": split_ratio,
                "split_date": split_date,
                "lots_adjusted": 0,
                "lots": []
            }

        # Create transaction record
        transaction_id = uuid4()
        security_id = open_lots[0]["security_id"] if open_lots else uuid4()

        lots_adjusted = []

        async with self.conn.transaction():
            # Record split transaction
            await self.conn.execute(
                """
                INSERT INTO transactions (
                    id, portfolio_id, transaction_type, security_id, symbol,
                    transaction_date, quantity, price, amount,
                    currency, fee, narration, source, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'manual', NOW())
                """,
                transaction_id, portfolio_id, "SPLIT", security_id, symbol,
                split_date, split_ratio, Decimal("0"), Decimal("0"),
                "USD", Decimal("0"), notes
            )

            # Adjust each lot
            for lot in open_lots:
                lot_id = lot["id"]
                old_quantity_original = lot["quantity_original"]
                old_quantity_open = lot["quantity_open"]
                old_cost_basis = lot["cost_basis"]

                # Calculate new quantities (multiply by split ratio)
                new_quantity_original = old_quantity_original * split_ratio
                new_quantity_open = old_quantity_open * split_ratio

                # Cost basis stays the same (total cost doesn't change)
                # But cost per share changes
                new_cost_basis_per_share = old_cost_basis / new_quantity_original

                await self.conn.execute(
                    """
                    UPDATE lots
                    SET qty_original = $1,
                        qty_open = $2,
                        quantity = $2,
                        cost_basis_per_share = $3,
                        updated_at = NOW()
                    WHERE id = $4
                    """,
                    new_quantity_original, new_quantity_open, new_cost_basis_per_share, lot_id
                )

                logger.debug(
                    f"Adjusted lot: lot_id={lot_id}, "
                    f"old_qty={old_quantity_open}, new_qty={new_quantity_open}, "
                    f"split_ratio={split_ratio}"
                )

                lots_adjusted.append({
                    "lot_id": lot_id,
                    "old_quantity_original": old_quantity_original,
                    "old_quantity_open": old_quantity_open,
                    "new_quantity_original": new_quantity_original,
                    "new_quantity_open": new_quantity_open,
                    "cost_basis": old_cost_basis
                })

        logger.info(f"SPLIT complete: transaction_id={transaction_id}, lots_adjusted={len(lots_adjusted)}")

        return {
            "transaction_id": transaction_id,
            "symbol": symbol,
            "split_ratio": split_ratio,
            "split_date": split_date,
            "lots_adjusted": len(lots_adjusted),
            "lots": lots_adjusted
        }

    async def record_withholding_tax(
        self,
        portfolio_id: UUID,
        symbol: str,
        tax_amount: Decimal,
        currency: str,
        tax_date: date,
        base_currency: Optional[str] = None,
        fx_rate: Optional[Decimal] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record ADR withholding tax.

        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol
            tax_amount: Tax amount (positive number, will be recorded as negative)
            currency: Tax currency
            tax_date: Tax payment date
            base_currency: Portfolio base currency
            fx_rate: FX rate at tax date
            notes: Optional notes

        Returns:
            Dict with transaction_id, tax_amount, etc.

        Raises:
            InvalidCorporateActionError: If parameters invalid
        """
        # Validation
        if tax_amount <= 0:
            raise InvalidCorporateActionError(f"Tax amount must be positive, got {tax_amount}")

        # Multi-currency: convert to base currency
        tax_amount_base_currency = tax_amount
        fx_rate_id = None
        fx_rate_used = Decimal("1.0")

        if base_currency and base_currency != currency:
            if fx_rate is None:
                # Try to get FX rate from database
                fx_rate_id, fx_rate_used = await self._get_or_create_fx_rate(
                    asof_date=tax_date,
                    base_currency=currency,
                    quote_currency=base_currency,
                    rate=None
                )
                if fx_rate_id is None:
                    raise InsufficientDataError(
                        f"FX rate for {currency}->{base_currency} on {tax_date} not found. "
                        f"Please provide fx_rate parameter."
                    )
            else:
                fx_rate_used = fx_rate
                fx_rate_id, _ = await self._get_or_create_fx_rate(
                    asof_date=tax_date,
                    base_currency=currency,
                    quote_currency=base_currency,
                    rate=fx_rate_used
                )

            tax_amount_base_currency = tax_amount * fx_rate_used

        logger.info(
            f"Recording WITHHOLDING_TAX: {symbol} {tax_amount} {currency} on {tax_date}, "
            f"fx_rate={fx_rate_used}, tax_base={tax_amount_base_currency}"
        )

        # Create transaction record (negative amount = outflow)
        transaction_id = uuid4()
        security_id = await self._get_security_id(symbol)

        async with self.conn.transaction():
            await self.conn.execute(
                """
                INSERT INTO transactions (
                    id, portfolio_id, transaction_type, security_id, symbol,
                    transaction_date, quantity, price, amount,
                    currency, fee, trade_fx_rate_id, narration, source, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'manual', NOW())
                """,
                transaction_id, portfolio_id, "FEE", security_id, symbol,
                tax_date, None, None, -tax_amount_base_currency,  # Negative = outflow
                currency, Decimal("0"), fx_rate_id, notes
            )

        logger.info(f"WITHHOLDING_TAX recorded: transaction_id={transaction_id}")

        return {
            "transaction_id": transaction_id,
            "symbol": symbol,
            "tax_amount": tax_amount,
            "currency": currency,
            "tax_date": tax_date,
            "fx_rate": fx_rate_used,
            "fx_rate_id": fx_rate_id,
            "tax_amount_base": tax_amount_base_currency,
            "base_currency": base_currency or currency
        }

    async def _get_open_lots(
        self,
        portfolio_id: UUID,
        symbol: str
    ) -> List[Dict[str, Any]]:
        """
        Get all open lots for a symbol in a portfolio.

        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol

        Returns:
            List of lot records
        """
        rows = await self.conn.fetch(
            """
            SELECT id, security_id, symbol, qty_original AS quantity_original, qty_open AS quantity_open, cost_basis, acquisition_date, currency
            FROM lots
            WHERE portfolio_id = $1 AND symbol = $2 AND qty_open > 0
            ORDER BY acquisition_date ASC, created_at ASC
            """,
            portfolio_id, symbol
        )

        return [dict(row) for row in rows]

    async def _get_or_create_fx_rate(
        self,
        asof_date: date,
        base_currency: str,
        quote_currency: str,
        rate: Optional[Decimal],
        policy: str = "WM4PM_CAD"
    ) -> tuple[Optional[UUID], Decimal]:
        """
        Get or create FX rate in database.

        Args:
            asof_date: FX rate date
            base_currency: Base currency (e.g., "USD")
            quote_currency: Quote currency (e.g., "CAD")
            rate: FX rate (if None, will fetch from database)
            policy: Pricing policy

        Returns:
            Tuple of (fx_rate_id, rate)
            Returns (None, 0) if rate not found and not provided
        """
        if base_currency == quote_currency:
            return None, Decimal("1.0")

        if rate is not None:
            # When a rate is provided, we still need to store it somewhere
            # Try to find an existing FX rate for this date or create one
            # But DON'T try to create pricing packs (those are system-managed)

            # First check if we already have a rate for this date
            row = await self.conn.fetchrow(
                """
                SELECT id, rate
                FROM fx_rates
                WHERE asof_ts::date = $1
                  AND base_ccy = $2
                  AND quote_ccy = $3
                ORDER BY asof_ts DESC
                LIMIT 1
                """,
                asof_date, base_currency, quote_currency
            )

            if row:
                # Use existing FX rate (even if rate differs slightly)
                # This is safer than trying to update system FX rates
                logger.info(f"Using existing FX rate for {base_currency}/{quote_currency} on {asof_date}: {row['rate']}")
                return row["id"], row["rate"]

            # If no FX rate exists, we can't proceed without a pricing pack
            # The FX rates should have been set up beforehand
            raise InsufficientDataError(
                f"FX rate for {base_currency}->{quote_currency} on {asof_date} not found in database. "
                f"FX rates must be created as part of pricing pack setup."
            )

        # Try to get from database (direct) - search across all packs for this date
        row = await self.conn.fetchrow(
            """
            SELECT id, rate
            FROM fx_rates
            WHERE asof_ts::date = $1
              AND base_ccy = $2
              AND quote_ccy = $3
            ORDER BY asof_ts DESC
            LIMIT 1
            """,
            asof_date, base_currency, quote_currency
        )

        if row:
            return row["id"], row["rate"]

        # Try reverse lookup (quote/base)
        row = await self.conn.fetchrow(
            """
            SELECT id, rate
            FROM fx_rates
            WHERE asof_ts::date = $1
              AND base_ccy = $2
              AND quote_ccy = $3
            ORDER BY asof_ts DESC
            LIMIT 1
            """,
            asof_date, quote_currency, base_currency
        )

        if row:
            # Return inverse rate
            inverse_rate = Decimal("1.0") / row["rate"]
            return row["id"], inverse_rate

        # Not found
        return None, Decimal("0")

    async def get_dividend_history(
        self,
        portfolio_id: UUID,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get dividend payment history for a portfolio.

        Args:
            portfolio_id: Portfolio UUID
            symbol: Filter by symbol (optional)
            start_date: Filter by pay_date >= start_date (optional)
            end_date: Filter by pay_date <= end_date (optional)

        Returns:
            List of dividend transactions
        """
        query = """
            SELECT
                id, symbol, transaction_date as pay_date, ex_date,
                quantity as shares, price as dividend_per_share,
                amount as net_amount, currency,
                pay_fx_rate_id, narration
            FROM transactions
            WHERE portfolio_id = $1
              AND transaction_type = 'DIVIDEND'
        """
        params = [portfolio_id]
        param_idx = 2

        if symbol:
            query += f" AND symbol = ${param_idx}"
            params.append(symbol)
            param_idx += 1

        if start_date:
            query += f" AND transaction_date >= ${param_idx}"
            params.append(start_date)
            param_idx += 1

        if end_date:
            query += f" AND transaction_date <= ${param_idx}"
            params.append(end_date)
            param_idx += 1

        query += " ORDER BY transaction_date DESC"

        rows = await self.conn.fetch(query, *params)

        return [dict(row) for row in rows]
