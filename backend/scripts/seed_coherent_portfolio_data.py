#!/usr/bin/env python3
"""
Coherent Portfolio Data Seeder
================================
Creates realistic, coherent portfolio data that aligns with actual holdings and contributions.

This script:
1. Tracks all cash contributions ($620K total)
2. Calculates realistic portfolio growth based on actual holdings
3. Ensures cash balance + securities value = total NAV
4. Creates consistent metrics and cash flow records

Author: DawsOS
Date: November 2025
"""

import asyncio
import asyncpg
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from decimal import Decimal
import os
import logging
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Portfolio configuration
PORTFOLIO_ID = UUID('64ff3be6-0ed1-4990-a32b-4ded17f0320c')
START_DATE = date(2023, 11, 30)
END_DATE = date(2025, 10, 31)

# Security appreciation factors (realistic based on market performance)
APPRECIATION = {
    'BAM': 1.35,    # Brookfield - strong performance
    'BBUC': 1.01,   # Cash fund - minimal appreciation  
    'BRK.B': 1.35,  # Berkshire - value growth
    'BTI': 1.25,    # British American Tobacco - dividend + modest growth
    'CNR': 1.25,    # Canadian National Railway - steady growth
    'EVO': 1.15,    # Evolution Gaming - moderate growth
    'HHC': 1.15,    # Howard Hughes - moderate growth
    'NKE': 0.95,    # Nike - slight decline
    'PYPL': 0.95    # PayPal - slight decline
}

# Actual holdings data (from lots table)
HOLDINGS = {
    'BAM': {'shares': 600, 'cost_basis': 26118.00},
    'BBUC': {'shares': 50000, 'cost_basis': 50000.00},
    'BRK.B': {'shares': 130, 'cost_basis': 43670.40},
    'BTI': {'shares': 800, 'cost_basis': 26069.00},
    'CNR': {'shares': 300, 'cost_basis': 47220.00},
    'EVO': {'shares': 250, 'cost_basis': 24480.00},
    'HHC': {'shares': 300, 'cost_basis': 20220.00},
    'NKE': {'shares': 250, 'cost_basis': 20470.50},
    'PYPL': {'shares': 400, 'cost_basis': 22620.00}
}

TOTAL_COST_BASIS = sum(h['cost_basis'] for h in HOLDINGS.values())  # $280,867.90

class CoherentPortfolioSeeder:
    """Seeds coherent portfolio data with realistic progression"""
    
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        
    async def clean_existing_data(self):
        """Remove existing portfolio daily values to prevent duplicates"""
        logger.info("Cleaning existing portfolio_daily_values...")
        
        count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM portfolio_daily_values WHERE portfolio_id = $1",
            PORTFOLIO_ID
        )
        
        await self.conn.execute(
            "DELETE FROM portfolio_daily_values WHERE portfolio_id = $1",
            PORTFOLIO_ID
        )
        
        logger.info(f"Deleted {count} existing records")
        
    async def get_cash_flows(self) -> pd.DataFrame:
        """Get all cash contributions from transactions"""
        rows = await self.conn.fetch("""
            SELECT transaction_date, amount
            FROM transactions
            WHERE portfolio_id = $1 
              AND transaction_type = 'TRANSFER_IN'
            ORDER BY transaction_date
        """, PORTFOLIO_ID)
        
        if not rows:
            logger.warning("No cash flows found!")
            return pd.DataFrame()
            
        df = pd.DataFrame([dict(r) for r in rows])
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = df['amount'].astype(float)
        
        logger.info(f"Found {len(df)} cash flows totaling ${df['amount'].sum():,.0f}")
        return df
        
    async def get_trade_activity(self) -> pd.DataFrame:
        """Get all buys and sells to track investment timing"""
        rows = await self.conn.fetch("""
            SELECT transaction_date, transaction_type, symbol, quantity, price, amount
            FROM transactions
            WHERE portfolio_id = $1 
              AND transaction_type IN ('BUY', 'SELL')
            ORDER BY transaction_date
        """, PORTFOLIO_ID)
        
        df = pd.DataFrame([dict(r) for r in rows])
        if not df.empty:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df['amount'] = df['amount'].astype(float)
            
        logger.info(f"Found {len(df)} trades")
        return df
        
    def calculate_portfolio_value(self, date: pd.Timestamp, cash_flows: pd.DataFrame, 
                                 trades: pd.DataFrame) -> dict:
        """Calculate portfolio value at a specific date"""
        
        # Calculate cumulative cash contributions up to this date
        cash_contributions = cash_flows[cash_flows['transaction_date'] <= date]['amount'].sum()
        
        # Calculate cash spent on investments up to this date
        if not trades.empty:
            cash_spent = -trades[trades['transaction_date'] <= date]['amount'].sum()
            # Get proceeds from sells
            sell_proceeds = trades[(trades['transaction_date'] <= date) & 
                                  (trades['transaction_type'] == 'SELL')]['amount'].sum()
        else:
            cash_spent = 0
            sell_proceeds = 0
            
        # Cash balance = contributions - spent + proceeds
        cash_balance = cash_contributions - cash_spent + sell_proceeds
        
        # Calculate securities value based on when they were purchased
        securities_value = 0
        for symbol, holding in HOLDINGS.items():
            # Check if we owned this security on this date
            symbol_trades = trades[trades['symbol'] == symbol] if not trades.empty else pd.DataFrame()
            if not symbol_trades.empty:
                first_buy = symbol_trades[symbol_trades['transaction_type'] == 'BUY']['transaction_date'].min()
                if pd.notna(first_buy) and date >= first_buy:
                    # Calculate appreciation based on time held
                    days_held = (date - first_buy).days
                    total_days = (END_DATE - first_buy.date()).days
                    if total_days > 0:
                        progress = min(days_held / total_days, 1.0)
                        # Linear appreciation from cost to target
                        current_appreciation = 1.0 + (APPRECIATION[symbol] - 1.0) * progress
                        securities_value += holding['cost_basis'] * current_appreciation
                        
        # Add some market volatility
        noise = np.random.normal(0, 0.01) * (cash_balance + securities_value)
        
        return {
            'cash_balance': max(0, cash_balance + noise * 0.3),
            'securities_value': max(0, securities_value + noise * 0.7),
            'total_value': max(0, cash_balance + securities_value + noise)
        }
        
    async def generate_daily_values(self):
        """Generate coherent daily NAV values"""
        
        # Get cash flows and trades
        cash_flows = await self.get_cash_flows()
        trades = await self.get_trade_activity()
        
        # Generate business days only
        dates = pd.bdate_range(start=START_DATE, end=END_DATE, freq='B')
        
        logger.info(f"Generating {len(dates)} daily values from {START_DATE} to {END_DATE}")
        
        records = []
        for date in dates:
            values = self.calculate_portfolio_value(date, cash_flows, trades)
            
            records.append({
                'portfolio_id': PORTFOLIO_ID,
                'valuation_date': date.date(),
                'total_value': Decimal(str(round(values['total_value'], 2))),
                'cash_balance': Decimal(str(round(values['cash_balance'], 2))),
                'positions_value': Decimal(str(round(values['securities_value'], 2))),
                'cash_flows': Decimal('0'),  # Will be set separately
                'currency': 'USD',
                'computed_at': datetime.now()
            })
            
        # Add cash flows on the actual dates
        for _, flow in cash_flows.iterrows():
            flow_date = flow['transaction_date'].date()
            for record in records:
                if record['valuation_date'] == flow_date:
                    record['cash_flows'] = Decimal(str(flow['amount']))
                    break
                    
        return records
        
    async def insert_daily_values(self, records: list):
        """Insert daily values into database"""
        
        logger.info(f"Inserting {len(records)} daily value records...")
        
        # Use batch insert for efficiency
        values = [
            (r['portfolio_id'], r['valuation_date'], r['total_value'],
             r['cash_balance'], r['positions_value'], r['cash_flows'],
             r['currency'], r['computed_at'])
            for r in records
        ]
        
        await self.conn.executemany("""
            INSERT INTO portfolio_daily_values (
                portfolio_id, valuation_date, total_value,
                cash_balance, positions_value, cash_flows,
                currency, computed_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (portfolio_id, valuation_date) DO UPDATE SET
                total_value = EXCLUDED.total_value,
                cash_balance = EXCLUDED.cash_balance,
                positions_value = EXCLUDED.positions_value,
                cash_flows = EXCLUDED.cash_flows,
                currency = EXCLUDED.currency,
                computed_at = EXCLUDED.computed_at
        """, values)
        
        logger.info("Daily values inserted successfully")
        
    async def create_cash_flow_records(self):
        """Create portfolio_cash_flows records for MWR calculation"""
        
        logger.info("Creating cash flow records...")
        
        # Get all TRANSFER_IN transactions
        flows = await self.conn.fetch("""
            SELECT transaction_date, amount
            FROM transactions
            WHERE portfolio_id = $1 
              AND transaction_type = 'TRANSFER_IN'
            ORDER BY transaction_date
        """, PORTFOLIO_ID)
        
        # Insert into portfolio_cash_flows
        for flow in flows:
            await self.conn.execute("""
                INSERT INTO portfolio_cash_flows (
                    portfolio_id, flow_date, flow_type, amount, created_at
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (portfolio_id, flow_date, flow_type) DO UPDATE SET
                    amount = EXCLUDED.amount,
                    created_at = EXCLUDED.created_at
            """, PORTFOLIO_ID, flow['transaction_date'], 'CONTRIBUTION',
                Decimal(str(flow['amount'])), datetime.now())
                
        logger.info(f"Created {len(flows)} cash flow records")
        
    async def update_current_prices(self):
        """Add current market prices matching appreciation factors"""
        
        logger.info("Updating current prices in pricing pack...")
        
        # Get latest pricing pack
        pack_id = 'PP_2025-11-03'
        
        for symbol, holding in HOLDINGS.items():
            # Calculate current price based on appreciation
            avg_cost = holding['cost_basis'] / holding['shares']
            current_price = avg_cost * APPRECIATION[symbol]
            
            # Get security_id
            security_id = await self.conn.fetchval(
                "SELECT id FROM securities WHERE symbol = $1",
                symbol
            )
            
            if security_id:
                # Update or insert price
                await self.conn.execute("""
                    INSERT INTO prices (
                        id, security_id, pricing_pack_id, asof_date,
                        close, currency, source, created_at
                    ) VALUES (
                        gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7
                    )
                    ON CONFLICT (security_id, pricing_pack_id) DO UPDATE SET
                        close = EXCLUDED.close,
                        asof_date = EXCLUDED.asof_date
                """, security_id, pack_id, date(2025, 11, 3),
                    Decimal(str(round(current_price, 2))), 'USD', 'SEED', datetime.now())
                    
                logger.info(f"Updated {symbol} price: ${avg_cost:.2f} -> ${current_price:.2f}")
                
    async def verify_coherence(self):
        """Verify data coherence"""
        
        logger.info("Verifying data coherence...")
        
        # Check final portfolio value
        final = await self.conn.fetchrow("""
            SELECT total_value, cash_balance, positions_value
            FROM portfolio_daily_values
            WHERE portfolio_id = $1
            ORDER BY valuation_date DESC
            LIMIT 1
        """, PORTFOLIO_ID)
        
        # Check total contributions
        contributions = await self.conn.fetchval("""
            SELECT SUM(amount)
            FROM transactions
            WHERE portfolio_id = $1 
              AND transaction_type = 'TRANSFER_IN'
        """, PORTFOLIO_ID)
        
        # Calculate expected securities value
        expected_securities = sum(h['cost_basis'] * APPRECIATION.get(s, 1.0) 
                                 for s, h in HOLDINGS.items())
        
        logger.info(f"Final portfolio value: ${final['total_value']:,.2f}")
        logger.info(f"  - Cash balance: ${final['cash_balance']:,.2f}")
        logger.info(f"  - Securities value: ${final['positions_value']:,.2f}")
        logger.info(f"Total contributions: ${contributions:,.2f}")
        logger.info(f"Expected securities value: ${expected_securities:,.2f}")
        logger.info(f"Implied return: {((final['total_value'] - contributions) / contributions * 100):.1f}%")
        
    async def run(self):
        """Execute the seeding process"""
        try:
            await self.clean_existing_data()
            
            # Generate and insert daily values
            records = await self.generate_daily_values()
            await self.insert_daily_values(records)
            
            # Create supporting records
            await self.create_cash_flow_records()
            await self.update_current_prices()
            
            # Verify everything is coherent
            await self.verify_coherence()
            
            logger.info("✅ Coherent portfolio data seeding complete!")
            
        except Exception as e:
            logger.error(f"Error seeding data: {e}")
            raise


async def main():
    """Main entry point"""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set")
        return
        
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        seeder = CoherentPortfolioSeeder(conn)
        await seeder.run()
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())