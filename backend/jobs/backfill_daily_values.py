#!/usr/bin/env python3
"""
Backfill portfolio_daily_values table with historical data.
Phase 5 of Metrics Implementation Plan.

This script:
1. Queries historical transactions
2. Calculates daily portfolio values
3. Populates portfolio_daily_values table
4. Handles cash flows for MWR calculation
"""

import asyncio
import asyncpg
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID
import os
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyValueBackfill:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def backfill_portfolio(self, portfolio_id: str, start_date: date, end_date: date):
        """Backfill daily values for a specific portfolio."""
        logger.info(f"Backfilling portfolio {portfolio_id} from {start_date} to {end_date}")
        
        # Get all transactions for the portfolio
        transactions = await self.conn.fetch(
            """
            SELECT 
                transaction_date,
                transaction_type,
                security_id,
                quantity,
                price,
                amount,
                currency
            FROM transactions
            WHERE portfolio_id = $1
                AND transaction_date >= $2
                AND transaction_date <= $3
            ORDER BY transaction_date, created_at
            """,
            UUID(portfolio_id),
            start_date,
            end_date
        )
        
        # Get portfolio base currency
        portfolio = await self.conn.fetchrow(
            "SELECT base_currency FROM portfolios WHERE id = $1",
            UUID(portfolio_id)
        )
        base_currency = portfolio["base_currency"] if portfolio else "USD"
        
        # Process each day
        current_date = start_date
        holdings = {}  # Track security holdings
        cash_balance = Decimal("1000000")  # Start with 1M initial cash
        
        # Record initial cash flow
        await self.record_cash_flow(portfolio_id, start_date, cash_balance, "DEPOSIT")
        
        while current_date <= end_date:
            # Process transactions for this day
            day_transactions = [
                t for t in transactions 
                if t["transaction_date"] == current_date
            ]
            
            for txn in day_transactions:
                security_id = txn["security_id"]
                # Handle potential null values
                quantity = Decimal(str(txn["quantity"])) if txn["quantity"] is not None else Decimal("0")
                amount = Decimal(str(txn["amount"])) if txn["amount"] is not None else Decimal("0")
                txn_type = txn["transaction_type"]
                
                if txn_type == "BUY":
                    holdings[security_id] = holdings.get(security_id, Decimal("0")) + quantity
                    cash_balance -= amount
                elif txn_type == "SELL":
                    holdings[security_id] = holdings.get(security_id, Decimal("0")) - quantity
                    cash_balance += amount
                elif txn_type == "DEPOSIT":
                    cash_balance += amount
                    await self.record_cash_flow(portfolio_id, current_date, amount, "DEPOSIT")
                elif txn_type == "WITHDRAWAL":
                    cash_balance -= amount
                    await self.record_cash_flow(portfolio_id, current_date, -amount, "WITHDRAWAL")
            
            # Calculate portfolio value for the day
            holdings_value = Decimal("0")
            
            # Get latest prices for holdings
            if holdings:
                for security_id, quantity in holdings.items():
                    if quantity > 0:
                        # Get price from pricing_packs
                        price = await self.get_security_price(security_id, current_date)
                        holdings_value += quantity * price
            
            total_value = cash_balance + holdings_value
            
            # Insert daily value
            await self.conn.execute(
                """
                INSERT INTO portfolio_daily_values (
                    portfolio_id,
                    valuation_date,
                    total_value,
                    cash_balance,
                    positions_value,
                    cash_flows,
                    currency,
                    computed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                ON CONFLICT (portfolio_id, valuation_date) 
                DO UPDATE SET 
                    total_value = EXCLUDED.total_value,
                    cash_balance = EXCLUDED.cash_balance,
                    positions_value = EXCLUDED.positions_value,
                    computed_at = NOW()
                """,
                UUID(portfolio_id),
                current_date,
                total_value,
                cash_balance,
                holdings_value,
                Decimal("0"),  # cash_flows placeholder
                base_currency
            )
            
            logger.debug(f"Date: {current_date}, Total: {total_value}, Cash: {cash_balance}, Securities: {holdings_value}")
            
            # Move to next day
            current_date += timedelta(days=1)
        
        logger.info(f"Completed backfill for portfolio {portfolio_id}")
    
    async def get_security_price(self, security_id: str, price_date: date) -> Decimal:
        """Get security price from latest transaction price."""
        # Use transaction price
        row = await self.conn.fetchrow(
            """
            SELECT price
            FROM transactions
            WHERE security_id = $1
                AND transaction_date <= $2
                AND price > 0
            ORDER BY transaction_date DESC, created_at DESC
            LIMIT 1
            """,
            security_id,
            price_date
        )
        
        if row and row["price"]:
            return Decimal(str(row["price"]))
        
        # Default fallback - use 100 as baseline price
        return Decimal("100")
    
    async def record_cash_flow(self, portfolio_id: str, flow_date: date, amount: Decimal, flow_type: str):
        """Record a cash flow for MWR calculation."""
        # Check if cash flow already exists
        existing = await self.conn.fetchrow(
            """
            SELECT id FROM portfolio_cash_flows
            WHERE portfolio_id = $1 AND flow_date = $2 AND flow_type = $3
            """,
            UUID(portfolio_id),
            flow_date,
            flow_type
        )
        
        if existing:
            # Update existing cash flow
            await self.conn.execute(
                """
                UPDATE portfolio_cash_flows 
                SET amount = $4, created_at = NOW()
                WHERE portfolio_id = $1 AND flow_date = $2 AND flow_type = $3
                """,
                UUID(portfolio_id),
                flow_date,
                flow_type,
                amount
            )
        else:
            # Insert new cash flow
            await self.conn.execute(
                """
                INSERT INTO portfolio_cash_flows (
                    id,
                    portfolio_id,
                    flow_date,
                    flow_type,
                    amount,
                    currency,
                    created_at
                ) VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NOW())
                """,
                UUID(portfolio_id),
                flow_date,
                flow_type,
                amount,
                "USD"  # Default currency
            )
    
    async def get_portfolios_to_backfill(self) -> List[Dict]:
        """Get all portfolios that need backfilling."""
        return await self.conn.fetch(
            """
            SELECT 
                p.id,
                p.name,
                p.base_currency,
                MIN(t.transaction_date) as first_transaction,
                MAX(t.transaction_date) as last_transaction,
                COUNT(DISTINCT pdv.valuation_date) as existing_values
            FROM portfolios p
            LEFT JOIN transactions t ON t.portfolio_id = p.id
            LEFT JOIN portfolio_daily_values pdv ON pdv.portfolio_id = p.id
            GROUP BY p.id, p.name, p.base_currency
            HAVING COUNT(t.id) > 0
            """
        )


async def main():
    """Main backfill function."""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return
    
    # Connect to database
    conn = await asyncpg.connect(database_url)
    
    try:
        backfiller = DailyValueBackfill(conn)
        
        # Get portfolios to backfill
        portfolios = await backfiller.get_portfolios_to_backfill()
        logger.info(f"Found {len(portfolios)} portfolios to backfill")
        
        for portfolio in portfolios:
            portfolio_id = str(portfolio["id"])
            first_txn = portfolio["first_transaction"]
            last_txn = portfolio["last_transaction"]
            existing_values = portfolio["existing_values"]
            
            if not first_txn:
                logger.info(f"Portfolio {portfolio_id} has no transactions, skipping")
                continue
            
            # Calculate date range
            start_date = first_txn
            end_date = date.today()
            
            logger.info(f"Portfolio {portfolio_id} ({portfolio['name']}): "
                      f"{existing_values} existing values, "
                      f"backfilling from {start_date} to {end_date}")
            
            # Perform backfill
            await backfiller.backfill_portfolio(portfolio_id, start_date, end_date)
        
        logger.info("Backfill completed successfully")
        
    except Exception as e:
        logger.error(f"Backfill failed: {e}", exc_info=True)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())