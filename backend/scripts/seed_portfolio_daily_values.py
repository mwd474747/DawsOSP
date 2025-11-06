#!/usr/bin/env python3
"""
Seed Portfolio Daily Values for DawsOS

This script generates historical portfolio daily values to enable:
- Currency attribution (requires portfolio_daily_values)
- Risk metrics (requires portfolio_daily_values)
- Factor analysis (requires portfolio_daily_values)
- Performance metrics (TWR, MWR, Sharpe)

Usage:
    python backend/scripts/seed_portfolio_daily_values.py
    python backend/scripts/seed_portfolio_daily_values.py --days 300
    python backend/scripts/seed_portfolio_daily_values.py --portfolio-id <uuid>
"""

import asyncio
import asyncpg
import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from uuid import UUID
import logging
from pathlib import Path

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PortfolioDailyValuesSeeder:
    """Seeds portfolio daily values for system functionality."""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.conn = None
        
    async def connect(self):
        """Connect to database."""
        self.conn = await asyncpg.connect(self.db_url)
        logger.info("Connected to database")
        
    async def disconnect(self):
        """Disconnect from database."""
        if self.conn:
            await self.conn.close()
            logger.info("Disconnected from database")
    
    def _is_trading_day(self, check_date: date) -> bool:
        """Check if date is a trading day (exclude weekends)."""
        return check_date.weekday() < 5
    
    def _get_trading_days(self, start_date: date, end_date: date) -> List[date]:
        """Get list of trading days between start and end dates."""
        trading_days = []
        current = start_date
        while current <= end_date:
            if self._is_trading_day(current):
                trading_days.append(current)
            current += timedelta(days=1)
        return trading_days
    
    async def get_portfolio_holdings(self, portfolio_id: UUID, asof_date: date) -> Dict[str, Decimal]:
        """
        Get portfolio holdings (lots) for a specific date.
        
        Returns:
            Dict mapping security_id to quantity_open
        """
        holdings = await self.conn.fetch(
            """
            SELECT security_id, quantity_open
            FROM lots
            WHERE portfolio_id = $1
                AND opened_at <= $2
                AND (closed_at IS NULL OR closed_at > $2)
                AND quantity_open > 0
            """,
            portfolio_id,
            asof_date
        )
        
        return {str(row['security_id']): Decimal(str(row['quantity_open'])) for row in holdings}
    
    async def calculate_portfolio_value(
        self,
        portfolio_id: UUID,
        pack_date: date
    ) -> Dict[str, Decimal]:
        """
        Calculate portfolio value for a specific date.
        
        Returns:
            Dict with total_value, cash_balance, positions_value
        """
        # Get pricing pack for date
        pack = await self.conn.fetchrow(
            """
            SELECT id FROM pricing_packs
            WHERE date = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            pack_date
        )
        
        if not pack:
            logger.warning(f"No pricing pack found for {pack_date}")
            return {
                'total_value': Decimal('0'),
                'cash_balance': Decimal('0'),
                'positions_value': Decimal('0')
            }
        
        pack_id = pack['id']
        
        # Get portfolio base currency
        portfolio = await self.conn.fetchrow(
            "SELECT base_currency FROM portfolios WHERE id = $1",
            portfolio_id
        )
        if not portfolio:
            logger.warning(f"Portfolio {portfolio_id} not found")
            return {
                'total_value': Decimal('0'),
                'cash_balance': Decimal('0'),
                'positions_value': Decimal('0')
            }
        
        base_currency = portfolio['base_currency']
        
        # Get holdings
        holdings = await self.get_portfolio_holdings(portfolio_id, pack_date)
        
        if not holdings:
            logger.debug(f"No holdings for portfolio {portfolio_id} on {pack_date}")
            return {
                'total_value': Decimal('0'),
                'cash_balance': Decimal('0'),
                'positions_value': Decimal('0')
            }
        
        # Calculate positions value
        positions_value = Decimal('0')
        
        for security_id, quantity in holdings.items():
            # Get price for security
            price_row = await self.conn.fetchrow(
                """
                SELECT close, currency
                FROM prices
                WHERE security_id = $1 AND pricing_pack_id = $2
                """,
                UUID(security_id),
                pack_id
            )
            
            if not price_row:
                logger.debug(f"No price for security {security_id} in pack {pack_id}")
                continue
            
            price = Decimal(str(price_row['close']))
            security_currency = price_row['currency']
            
            # Get FX rate if needed
            if security_currency != base_currency:
                fx_rate_row = await self.conn.fetchrow(
                    """
                    SELECT rate
                    FROM fx_rates
                    WHERE base_ccy = $1 AND quote_ccy = $2 AND pricing_pack_id = $3
                    """,
                    security_currency,
                    base_currency,
                    pack_id
                )
                
                if fx_rate_row:
                    fx_rate = Decimal(str(fx_rate_row['rate']))
                else:
                    # Try inverse
                    fx_rate_row = await self.conn.fetchrow(
                        """
                        SELECT rate
                        FROM fx_rates
                        WHERE base_ccy = $1 AND quote_ccy = $2 AND pricing_pack_id = $3
                        """,
                        base_currency,
                        security_currency,
                        pack_id
                    )
                    
                    if fx_rate_row:
                        fx_rate = Decimal('1') / Decimal(str(fx_rate_row['rate']))
                    else:
                        logger.debug(f"No FX rate for {security_currency}/{base_currency} in pack {pack_id}")
                        fx_rate = Decimal('1')  # Default to 1:1
            else:
                fx_rate = Decimal('1')
            
            # Calculate value in base currency
            value = quantity * price * fx_rate
            positions_value += value
        
        # Get cash balance (simplified - assume starting cash)
        # In real implementation, would track cash from transactions
        cash_balance = Decimal('100000')  # Placeholder
        
        total_value = positions_value + cash_balance
        
        return {
            'total_value': total_value,
            'cash_balance': cash_balance,
            'positions_value': positions_value
        }
    
    async def seed_portfolio_daily_values(
        self,
        portfolio_id: Optional[UUID] = None,
        days: int = 300,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        """
        Generate portfolio daily values.
        
        Args:
            portfolio_id: Portfolio UUID (None = all portfolios)
            days: Number of days to generate (default: 300)
            start_date: Start date (default: today - days)
            end_date: End date (default: today)
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        # Get portfolios
        if portfolio_id:
            portfolios = await self.conn.fetch(
                "SELECT id, name, base_currency FROM portfolios WHERE id = $1",
                portfolio_id
            )
        else:
            portfolios = await self.conn.fetch(
                "SELECT id, name, base_currency FROM portfolios"
            )
        
        if not portfolios:
            logger.warning("No portfolios found")
            return
        
        logger.info(f"Seeding portfolio daily values for {len(portfolios)} portfolio(s)")
        
        trading_days = self._get_trading_days(start_date, end_date)
        logger.info(f"Generating values for {len(trading_days)} trading days")
        
        total_records = 0
        
        for portfolio in portfolios:
            portfolio_id = portfolio['id']
            portfolio_name = portfolio['name']
            base_currency = portfolio['base_currency']
            
            logger.info(f"Processing portfolio: {portfolio_name} ({portfolio_id})")
            
            records = []
            
            for i, pack_date in enumerate(trading_days, 1):
                try:
                    # Calculate portfolio value
                    values = await self.calculate_portfolio_value(portfolio_id, pack_date)
                    
                    records.append({
                        'portfolio_id': portfolio_id,
                        'valuation_date': pack_date,
                        'total_value': values['total_value'],
                        'cash_balance': values['cash_balance'],
                        'positions_value': values['positions_value'],
                        'cash_flows': Decimal('0'),  # Placeholder - would come from transactions
                        'currency': base_currency
                    })
                    
                    if i % 50 == 0:
                        logger.debug(f"  Progress: {i}/{len(trading_days)} days calculated")
                        
                except Exception as e:
                    logger.error(f"Failed to calculate value for {pack_date}: {e}", exc_info=True)
                    continue
            
            # Insert records in batch
            if records:
                await self.conn.executemany(
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
                    [(r['portfolio_id'], r['valuation_date'], r['total_value'],
                      r['cash_balance'], r['positions_value'], r['cash_flows'],
                      r['currency']) for r in records]
                )
                
                total_records += len(records)
                logger.info(f"✅ Inserted {len(records)} daily values for portfolio {portfolio_name}")
        
        logger.info(f"✅ Total: {total_records} portfolio daily values inserted")
    
    async def verify_daily_values(
        self,
        portfolio_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        """Verify that daily values were created successfully."""
        logger.info("\n📊 Verifying portfolio daily values...")
        
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=300)
        
        if portfolio_id:
            query = """
                SELECT portfolio_id, COUNT(*) as days
                FROM portfolio_daily_values
                WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
                GROUP BY portfolio_id
            """
            rows = await self.conn.fetch(query, portfolio_id, start_date, end_date)
        else:
            query = """
                SELECT portfolio_id, COUNT(*) as days
                FROM portfolio_daily_values
                WHERE valuation_date BETWEEN $1 AND $2
                GROUP BY portfolio_id
            """
            rows = await self.conn.fetch(query, start_date, end_date)
        
        logger.info(f"Found daily values for {len(rows)} portfolio(s)")
        
        for row in rows:
            logger.info(f"  Portfolio {row['portfolio_id']}: {row['days']} days")
    
    async def run(
        self,
        portfolio_id: Optional[UUID] = None,
        days: int = 300,
        start_date: Optional[date] = None
    ):
        """Run seeding operation."""
        try:
            await self.connect()
            
            await self.seed_portfolio_daily_values(
                portfolio_id=portfolio_id,
                days=days,
                start_date=start_date
            )
            
            await self.verify_daily_values(portfolio_id=portfolio_id, start_date=start_date)
            
            logger.info("\n✅ Successfully seeded portfolio daily values!")
            
        except Exception as e:
            logger.error(f"Error seeding portfolio daily values: {e}", exc_info=True)
            raise
        finally:
            await self.disconnect()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed portfolio daily values")
    parser.add_argument(
        "--days",
        type=int,
        default=300,
        help="Number of days to generate (default: 300)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD, default: today - days)"
    )
    parser.add_argument(
        "--portfolio-id",
        type=str,
        help="Portfolio UUID (default: all portfolios)"
    )
    args = parser.parse_args()
    
    start_date = None
    if args.start_date:
        start_date = date.fromisoformat(args.start_date)
    
    portfolio_id = None
    if args.portfolio_id:
        portfolio_id = UUID(args.portfolio_id)
    
    seeder = PortfolioDailyValuesSeeder()
    await seeder.run(portfolio_id=portfolio_id, days=args.days, start_date=start_date)


if __name__ == "__main__":
    asyncio.run(main())

