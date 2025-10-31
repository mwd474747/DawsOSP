"""
Daily Portfolio Valuation Job

Purpose: Aggregate transactions into daily portfolio values
Updated: 2025-10-31
Priority: P0 (Phase 2 Task 1 - Build Transaction-to-NAV Pipeline)

This job:
1. Reads transactions from the transactions table
2. Computes daily NAV for each portfolio
3. Populates portfolio_daily_values table
4. Extracts cash flows to portfolio_cash_flows table
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import asyncpg

logger = logging.getLogger("DawsOS.DailyValuation")


class DailyValuationJob:
    """Computes and stores daily portfolio valuations from transactions."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        
    async def run(self, backfill_days: int = 365) -> Dict[str, int]:
        """
        Run daily valuation job.
        
        Args:
            backfill_days: Number of days to backfill (default 365)
            
        Returns:
            Dict with counts of processed portfolios and days
        """
        logger.info(f"Starting daily valuation job (backfill_days={backfill_days})")
        
        try:
            # Get all portfolios
            portfolios = await self._get_portfolios()
            logger.info(f"Found {len(portfolios)} portfolios to process")
            
            total_records = 0
            total_cash_flows = 0
            
            for portfolio in portfolios:
                portfolio_id = portfolio['id']
                
                # Process this portfolio
                records, flows = await self._process_portfolio(
                    portfolio_id, 
                    backfill_days
                )
                
                total_records += records
                total_cash_flows += flows
                
                logger.info(f"Portfolio {portfolio_id}: {records} daily values, {flows} cash flows")
            
            logger.info(f"Daily valuation complete: {total_records} values, {total_cash_flows} flows")
            
            return {
                "portfolios": len(portfolios),
                "daily_values": total_records,
                "cash_flows": total_cash_flows
            }
            
        except Exception as e:
            logger.error(f"Daily valuation job failed: {e}")
            raise
    
    async def _get_portfolios(self) -> List[asyncpg.Record]:
        """Get all active portfolios."""
        query = """
            SELECT DISTINCT p.id, p.base_currency
            FROM portfolios p
            WHERE p.active = true
        """
        
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(query)
    
    async def _process_portfolio(
        self, 
        portfolio_id: UUID, 
        backfill_days: int
    ) -> Tuple[int, int]:
        """
        Process a single portfolio's daily valuations.
        
        Returns:
            Tuple of (daily_value_records_created, cash_flow_records_created)
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=backfill_days)
        
        # Get portfolio inception date (first transaction)
        inception_date = await self._get_inception_date(portfolio_id)
        if inception_date:
            start_date = max(start_date, inception_date)
        
        logger.info(f"Processing portfolio {portfolio_id} from {start_date} to {end_date}")
        
        # Get all transactions for this portfolio
        transactions = await self._get_transactions(portfolio_id, start_date, end_date)
        
        # Get all historical prices
        prices = await self._get_historical_prices(start_date, end_date)
        
        # Build daily NAV series
        daily_values = []
        cash_flows = []
        
        current_date = start_date
        positions = {}  # symbol -> quantity
        cash_balance = Decimal('0')
        
        while current_date <= end_date:
            # Process transactions for this day
            day_transactions = [
                t for t in transactions 
                if t['transaction_date'] == current_date
            ]
            
            for txn in day_transactions:
                # Update positions and cash
                if txn['transaction_type'] == 'BUY':
                    symbol = txn['symbol']
                    positions[symbol] = positions.get(symbol, Decimal('0')) + txn['quantity']
                    cash_balance -= txn['amount']
                    
                elif txn['transaction_type'] == 'SELL':
                    symbol = txn['symbol']
                    positions[symbol] = positions.get(symbol, Decimal('0')) - txn['quantity']
                    cash_balance += txn['amount']
                    
                elif txn['transaction_type'] == 'DIVIDEND':
                    cash_balance += txn['amount']
                    # Record as cash flow
                    cash_flows.append({
                        'portfolio_id': portfolio_id,
                        'flow_date': current_date,
                        'flow_type': 'DIVIDEND',
                        'amount': txn['amount'],
                        'transaction_id': txn['id']
                    })
                    
                elif txn['transaction_type'] == 'DEPOSIT':
                    cash_balance += txn['amount']
                    cash_flows.append({
                        'portfolio_id': portfolio_id,
                        'flow_date': current_date,
                        'flow_type': 'DEPOSIT',
                        'amount': txn['amount'],
                        'transaction_id': txn['id']
                    })
                    
                elif txn['transaction_type'] == 'WITHDRAWAL':
                    cash_balance -= txn['amount']
                    cash_flows.append({
                        'portfolio_id': portfolio_id,
                        'flow_date': current_date,
                        'flow_type': 'WITHDRAWAL',
                        'amount': -txn['amount'],
                        'transaction_id': txn['id']
                    })
            
            # Calculate positions value for this day
            positions_value = Decimal('0')
            for symbol, quantity in positions.items():
                if quantity > 0:
                    # Get price for this symbol on this date
                    price = self._get_price_on_date(prices, symbol, current_date)
                    if price:
                        positions_value += quantity * price
            
            # Total NAV = positions + cash
            total_value = positions_value + cash_balance
            
            # Only record if we have positions or cash
            if total_value != 0 or len(positions) > 0:
                daily_values.append({
                    'portfolio_id': portfolio_id,
                    'valuation_date': current_date,
                    'total_value': total_value,
                    'cash_balance': cash_balance,
                    'positions_value': positions_value,
                    'cash_flows': sum(cf['amount'] for cf in cash_flows if cf['flow_date'] == current_date)
                })
            
            current_date += timedelta(days=1)
        
        # Store daily values
        records_created = await self._store_daily_values(daily_values)
        
        # Store cash flows
        flows_created = await self._store_cash_flows(cash_flows)
        
        return records_created, flows_created
    
    async def _get_inception_date(self, portfolio_id: UUID) -> Optional[date]:
        """Get the earliest transaction date for a portfolio."""
        query = """
            SELECT MIN(transaction_date) as inception_date
            FROM transactions
            WHERE portfolio_id = $1
        """
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(query, portfolio_id)
            return result
    
    async def _get_transactions(
        self, 
        portfolio_id: UUID, 
        start_date: date, 
        end_date: date
    ) -> List[asyncpg.Record]:
        """Get all transactions for a portfolio in date range."""
        query = """
            SELECT 
                id,
                transaction_date,
                transaction_type,
                symbol,
                quantity,
                price,
                amount
            FROM transactions
            WHERE portfolio_id = $1
                AND transaction_date BETWEEN $2 AND $3
            ORDER BY transaction_date, created_at
        """
        
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(query, portfolio_id, start_date, end_date)
    
    async def _get_historical_prices(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[asyncpg.Record]:
        """Get all historical prices in date range."""
        query = """
            SELECT 
                s.symbol,
                p.asof_date as price_date,
                p.close as close_price
            FROM prices p
            JOIN securities s ON p.security_id = s.id
            WHERE p.asof_date BETWEEN $1 AND $2
            ORDER BY p.asof_date
        """
        
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(query, start_date, end_date)
    
    def _get_price_on_date(
        self, 
        prices: List[asyncpg.Record],
        symbol: str,
        target_date: date
    ) -> Optional[Decimal]:
        """Get price for a symbol on a specific date (or carry forward)."""
        last_price = None
        
        for price_rec in prices:
            if price_rec['symbol'] == symbol:
                if price_rec['price_date'] <= target_date:
                    last_price = Decimal(str(price_rec['close_price']))
                elif price_rec['price_date'] > target_date:
                    break
        
        return last_price
    
    async def _store_daily_values(self, daily_values: List[Dict]) -> int:
        """Store daily portfolio values."""
        if not daily_values:
            return 0
        
        query = """
            INSERT INTO portfolio_daily_values (
                portfolio_id, valuation_date, total_value,
                cash_balance, positions_value, cash_flows
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (portfolio_id, valuation_date) 
            DO UPDATE SET
                total_value = EXCLUDED.total_value,
                cash_balance = EXCLUDED.cash_balance,
                positions_value = EXCLUDED.positions_value,
                cash_flows = EXCLUDED.cash_flows,
                computed_at = CURRENT_TIMESTAMP
        """
        
        async with self.db_pool.acquire() as conn:
            count = 0
            for dv in daily_values:
                await conn.execute(
                    query,
                    dv['portfolio_id'],
                    dv['valuation_date'],
                    dv['total_value'],
                    dv['cash_balance'],
                    dv['positions_value'],
                    dv['cash_flows']
                )
                count += 1
            
            return count
    
    async def _store_cash_flows(self, cash_flows: List[Dict]) -> int:
        """Store portfolio cash flows."""
        if not cash_flows:
            return 0
        
        query = """
            INSERT INTO portfolio_cash_flows (
                portfolio_id, flow_date, flow_type,
                amount, transaction_id
            ) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT DO NOTHING
        """
        
        async with self.db_pool.acquire() as conn:
            count = 0
            for cf in cash_flows:
                result = await conn.execute(
                    query,
                    cf['portfolio_id'],
                    cf['flow_date'],
                    cf['flow_type'],
                    cf['amount'],
                    cf.get('transaction_id')
                )
                if result.split()[-1] != '0':
                    count += 1
            
            return count


async def run_daily_valuation(db_pool: asyncpg.Pool, backfill_days: int = 365):
    """Entry point for the daily valuation job."""
    job = DailyValuationJob(db_pool)
    return await job.run(backfill_days)


if __name__ == "__main__":
    # For testing
    import os
    from backend.app.db.connection import get_db_pool
    
    async def main():
        logging.basicConfig(level=logging.INFO)
        
        # Get database pool
        db_pool = await get_db_pool()
        
        try:
            # Run valuation job
            result = await run_daily_valuation(db_pool, backfill_days=30)
            print(f"Daily valuation complete: {result}")
        finally:
            await db_pool.close()
    
    asyncio.run(main())