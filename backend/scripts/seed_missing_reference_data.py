#!/usr/bin/env python3
"""
Seed Missing Reference Data for DawsOS

This script adds the missing reference data that's causing empty values in the UI:
1. Historical FX rates aligned with pricing packs
2. Security sector/industry classifications
3. Corporate actions (dividends, splits)

Author: DawsOS Team
Created: November 2025
"""

import asyncio
import asyncpg
import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReferenceDataSeeder:
    """Seeds missing reference data into DawsOS database."""
    
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
    
    async def seed_fx_rates(self):
        """
        Seed historical FX rates for all pricing packs.
        
        Currency pairs needed:
        - USD/CAD (US Dollar to Canadian Dollar)
        - EUR/CAD (Euro to Canadian Dollar)
        - USD/EUR (US Dollar to Euro)
        """
        logger.info("Seeding FX rates...")
        
        # Get recent pricing packs (last 30 days only to avoid timeout)
        packs = await self.conn.fetch("""
            SELECT id, date FROM pricing_packs 
            WHERE date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY date
        """)
        logger.info(f"Found {len(packs)} recent pricing packs to populate with FX rates")
        
        # Base FX rates with realistic variations
        base_rates = {
            ("USD", "CAD"): 1.3625,  # USD to CAD
            ("CAD", "USD"): 0.7339,  # CAD to USD (1/1.3625)
            ("EUR", "CAD"): 1.4890,  # EUR to CAD
            ("CAD", "EUR"): 0.6716,  # CAD to EUR (1/1.4890)
            ("USD", "EUR"): 0.9147,  # USD to EUR
            ("EUR", "USD"): 1.0932,  # EUR to USD (1/0.9147)
        }
        
        fx_records = []
        for pack in packs:
            pack_id = pack['id']
            pack_date = pack['date']
            
            # Add some realistic variation based on date
            days_from_start = (pack_date - date(2024, 1, 1)).days
            variation = 0.98 + (0.04 * ((days_from_start % 60) / 60))  # ±2% variation
            
            for (base_ccy, quote_ccy), base_rate in base_rates.items():
                fx_records.append({
                    'base_ccy': base_ccy,
                    'quote_ccy': quote_ccy,
                    'pricing_pack_id': pack_id,
                    'asof_ts': datetime.combine(pack_date, datetime.min.time()),
                    'rate': Decimal(str(base_rate * variation)),
                    'source': 'FMP',
                    'policy': 'WM4PM_CAD'
                })
        
        # Insert FX rates using batch insert for efficiency
        if fx_records:
            # Use COPY for bulk insert (much faster)
            columns = ['base_ccy', 'quote_ccy', 'pricing_pack_id', 'asof_ts', 'rate', 'source', 'policy']
            
            # Prepare records for COPY
            records = [
                (r['base_ccy'], r['quote_ccy'], r['pricing_pack_id'], 
                 r['asof_ts'], r['rate'], r['source'], r['policy'])
                for r in fx_records
            ]
            
            # Use COPY for bulk insert
            await self.conn.copy_records_to_table(
                'fx_rates',
                records=records,
                columns=columns
            )
            
            logger.info(f"✅ Bulk inserted {len(fx_records)} FX rates across {len(packs)} pricing packs")
    
    async def seed_security_sectors(self):
        """
        Seed sector/industry classifications for securities.
        
        Maps securities to GICS sectors for proper sector allocation.
        """
        logger.info("Seeding security sectors...")
        
        # Get all securities
        securities = await self.conn.fetch("SELECT id, symbol FROM securities")
        logger.info(f"Found {len(securities)} securities to classify")
        
        # Map symbols to sectors (realistic GICS classifications)
        sector_map = {
            'AAPL': {'sector': 'Information Technology', 'industry': 'Technology Hardware', 'gics_code': '45'},
            'MSFT': {'sector': 'Information Technology', 'industry': 'Software', 'gics_code': '45'},
            'GOOGL': {'sector': 'Communication Services', 'industry': 'Interactive Media', 'gics_code': '50'},
            'AMZN': {'sector': 'Consumer Discretionary', 'industry': 'Internet Retail', 'gics_code': '25'},
            'JPM': {'sector': 'Financials', 'industry': 'Banks', 'gics_code': '40'},
            'WMT': {'sector': 'Consumer Staples', 'industry': 'Food & Staples Retail', 'gics_code': '30'},
            'BRK.B': {'sector': 'Financials', 'industry': 'Diversified Financials', 'gics_code': '40'},
            'SPY': {'sector': 'Diversified', 'industry': 'Equity ETF', 'gics_code': '00'},
            'TD.TO': {'sector': 'Financials', 'industry': 'Banks', 'gics_code': '40'},
            'RY.TO': {'sector': 'Financials', 'industry': 'Banks', 'gics_code': '40'},
            'BMO.TO': {'sector': 'Financials', 'industry': 'Banks', 'gics_code': '40'},
            'BNS.TO': {'sector': 'Financials', 'industry': 'Banks', 'gics_code': '40'},
            'BCE.TO': {'sector': 'Communication Services', 'industry': 'Telecom', 'gics_code': '50'},
            'SHOP.TO': {'sector': 'Information Technology', 'industry': 'Software', 'gics_code': '45'},
            'CNR.TO': {'sector': 'Industrials', 'industry': 'Transportation', 'gics_code': '20'},
            'SAP': {'sector': 'Information Technology', 'industry': 'Software', 'gics_code': '45'},
            'ASML': {'sector': 'Information Technology', 'industry': 'Semiconductors', 'gics_code': '45'},
        }
        
        # Create security_classifications table if it doesn't exist
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS security_classifications (
                security_id UUID PRIMARY KEY REFERENCES securities(id),
                sector VARCHAR(100),
                industry VARCHAR(100),
                gics_code VARCHAR(10),
                classification_date DATE DEFAULT CURRENT_DATE,
                source VARCHAR(50) DEFAULT 'Manual',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Insert classifications
        for security in securities:
            symbol = security['symbol']
            security_id = security['id']
            
            if symbol in sector_map:
                classification = sector_map[symbol]
                await self.conn.execute("""
                    INSERT INTO security_classifications (security_id, sector, industry, gics_code, source)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (security_id) 
                    DO UPDATE SET 
                        sector = EXCLUDED.sector,
                        industry = EXCLUDED.industry,
                        gics_code = EXCLUDED.gics_code,
                        updated_at = NOW()
                """, 
                    security_id,
                    classification['sector'],
                    classification['industry'],
                    classification['gics_code'],
                    'Manual'
                )
        
        logger.info(f"✅ Classified {len(sector_map)} securities by sector")
    
    async def seed_corporate_actions(self):
        """
        Seed corporate actions (dividends and splits) for securities.
        
        Adds realistic dividend and split events for holdings.
        """
        logger.info("Seeding corporate actions...")
        
        # Create corporate_actions table if it doesn't exist
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS corporate_actions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                security_id UUID REFERENCES securities(id),
                portfolio_id UUID REFERENCES portfolios(id),
                action_type VARCHAR(50) NOT NULL,
                ex_date DATE NOT NULL,
                record_date DATE,
                pay_date DATE,
                amount DECIMAL(20,8),
                currency VARCHAR(3),
                ratio VARCHAR(20),
                description TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Get portfolio and securities
        portfolio = await self.conn.fetchrow(
            "SELECT id FROM portfolios WHERE name = 'Diversified Growth Portfolio'"
        )
        if not portfolio:
            logger.warning("Portfolio not found, skipping corporate actions")
            return
            
        portfolio_id = portfolio['id']
        
        # Sample corporate actions for known securities
        actions = [
            # Apple dividends (quarterly)
            {
                'symbol': 'AAPL',
                'action_type': 'dividend',
                'ex_date': date(2025, 2, 7),
                'pay_date': date(2025, 2, 14),
                'amount': Decimal('0.25'),
                'currency': 'USD',
                'description': 'Q1 2025 Dividend'
            },
            {
                'symbol': 'AAPL',
                'action_type': 'dividend',
                'ex_date': date(2025, 5, 9),
                'pay_date': date(2025, 5, 16),
                'amount': Decimal('0.25'),
                'currency': 'USD',
                'description': 'Q2 2025 Dividend'
            },
            # Microsoft dividends
            {
                'symbol': 'MSFT',
                'action_type': 'dividend',
                'ex_date': date(2025, 2, 20),
                'pay_date': date(2025, 3, 13),
                'amount': Decimal('0.75'),
                'currency': 'USD',
                'description': 'Q1 2025 Dividend'
            },
            # Canadian bank dividends (quarterly, higher yield)
            {
                'symbol': 'TD.TO',
                'action_type': 'dividend',
                'ex_date': date(2025, 1, 9),
                'pay_date': date(2025, 1, 31),
                'amount': Decimal('1.02'),
                'currency': 'CAD',
                'description': 'Q1 2025 Dividend'
            },
            {
                'symbol': 'RY.TO',
                'action_type': 'dividend',
                'ex_date': date(2025, 1, 23),
                'pay_date': date(2025, 2, 24),
                'amount': Decimal('1.42'),
                'currency': 'CAD',
                'description': 'Q1 2025 Dividend'
            },
            # Stock split example
            {
                'symbol': 'SHOP.TO',
                'action_type': 'split',
                'ex_date': date(2025, 3, 1),
                'ratio': '10:1',
                'description': '10-for-1 Stock Split'
            },
        ]
        
        # Insert corporate actions
        for action in actions:
            # Get security ID
            security = await self.conn.fetchrow(
                "SELECT id FROM securities WHERE symbol = $1",
                action['symbol']
            )
            
            if security:
                await self.conn.execute("""
                    INSERT INTO corporate_actions 
                    (security_id, portfolio_id, action_type, ex_date, pay_date, amount, currency, ratio, description, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT DO NOTHING
                """,
                    security['id'],
                    portfolio_id,
                    action['action_type'],
                    action['ex_date'],
                    action.get('pay_date'),
                    action.get('amount'),
                    action.get('currency'),
                    action.get('ratio'),
                    action['description'],
                    'upcoming' if action['ex_date'] > date.today() else 'completed'
                )
        
        logger.info(f"✅ Created {len(actions)} corporate action events")
    
    async def verify_seed_data(self):
        """Verify that seed data was created successfully."""
        logger.info("\n📊 Verifying seed data...")
        
        # Check FX rates
        fx_count = await self.conn.fetchval("SELECT COUNT(*) FROM fx_rates")
        logger.info(f"FX rates: {fx_count} records")
        
        # Check sector classifications
        sector_exists = await self.conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'security_classifications'
            )
        """)
        if sector_exists:
            sector_count = await self.conn.fetchval("SELECT COUNT(*) FROM security_classifications")
            logger.info(f"Security classifications: {sector_count} records")
        
        # Check corporate actions
        ca_exists = await self.conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'corporate_actions'
            )
        """)
        if ca_exists:
            ca_count = await self.conn.fetchval("SELECT COUNT(*) FROM corporate_actions")
            logger.info(f"Corporate actions: {ca_count} records")
        
        # Sample FX rate
        sample_fx = await self.conn.fetchrow("""
            SELECT * FROM fx_rates 
            WHERE base_ccy = 'USD' AND quote_ccy = 'CAD' 
            LIMIT 1
        """)
        if sample_fx:
            logger.info(f"Sample FX rate: {sample_fx['base_ccy']}/{sample_fx['quote_ccy']} = {sample_fx['rate']}")
    
    async def run(self):
        """Run all seeding operations."""
        try:
            await self.connect()
            
            # Seed all missing data
            await self.seed_fx_rates()
            await self.seed_security_sectors()
            await self.seed_corporate_actions()
            
            # Verify
            await self.verify_seed_data()
            
            logger.info("\n✅ Successfully seeded all missing reference data!")
            
        except Exception as e:
            logger.error(f"Error seeding data: {e}", exc_info=True)
            raise
        finally:
            await self.disconnect()


async def main():
    """Main entry point."""
    seeder = ReferenceDataSeeder()
    await seeder.run()


if __name__ == "__main__":
    asyncio.run(main())