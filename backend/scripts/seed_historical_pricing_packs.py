#!/usr/bin/env python3
"""
Seed Historical Pricing Packs for DawsOS

This script generates 300 days of historical pricing packs to enable:
- Currency attribution (requires 252 days)
- Risk metrics (requires 252 days)
- Factor analysis (requires 252 days)
- Performance metrics (requires 252 days)

Usage:
    python backend/scripts/seed_historical_pricing_packs.py
    python backend/scripts/seed_historical_pricing_packs.py --days 300
    python backend/scripts/seed_historical_pricing_packs.py --start-date 2024-01-01
"""

import asyncio
import asyncpg
import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import logging
import random
from pathlib import Path

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Import pack builder
from jobs.build_pricing_pack import PricingPackBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoricalPricingPackSeeder:
    """Seeds historical pricing packs for system functionality."""
    
    def __init__(self, use_stubs: bool = True):
        """
        Initialize seeder.
        
        Args:
            use_stubs: Use stub data for prices (default: True for seeding)
        """
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.conn = None
        self.use_stubs = use_stubs
        self.builder = PricingPackBuilder(use_stubs=use_stubs)
        
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
        # Monday = 0, Sunday = 6
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
    
    async def check_existing_packs(self, start_date: date, end_date: date) -> Dict[date, bool]:
        """Check which packs already exist."""
        packs = await self.conn.fetch(
            """
            SELECT date FROM pricing_packs
            WHERE date BETWEEN $1 AND $2
            ORDER BY date
            """,
            start_date,
            end_date
        )
        existing_dates = {row['date'] for row in packs}
        
        trading_days = self._get_trading_days(start_date, end_date)
        result = {}
        for day in trading_days:
            result[day] = day in existing_dates
        return result
    
    async def seed_historical_packs(
        self,
        days: int = 300,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip_existing: bool = True
    ):
        """
        Generate historical pricing packs.
        
        Args:
            days: Number of days to generate (default: 300)
            start_date: Start date (default: today - days)
            end_date: End date (default: today)
            skip_existing: Skip packs that already exist (default: True)
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        logger.info(f"Seeding historical pricing packs from {start_date} to {end_date}")
        
        # Check existing packs
        existing_packs = await self.check_existing_packs(start_date, end_date)
        trading_days = self._get_trading_days(start_date, end_date)
        
        existing_count = sum(1 for day in trading_days if existing_packs.get(day, False))
        logger.info(f"Found {existing_count} existing packs out of {len(trading_days)} trading days")
        
        # Filter to only missing packs if skip_existing
        if skip_existing:
            days_to_generate = [day for day in trading_days if not existing_packs.get(day, False)]
        else:
            days_to_generate = trading_days
        
        logger.info(f"Generating {len(days_to_generate)} pricing packs...")
        
        # Generate packs (oldest first for better price coherence)
        generated = 0
        failed = 0
        
        for i, pack_date in enumerate(days_to_generate, 1):
            try:
                logger.info(f"[{i}/{len(days_to_generate)}] Building pack for {pack_date}...")
                
                pack_id = await self.builder.build_pack(
                    asof_date=pack_date,
                    policy="WM4PM_CAD",
                    mark_fresh=True  # Mark as fresh for historical packs
                )
                
                generated += 1
                
                if i % 50 == 0:
                    logger.info(f"  Progress: {i}/{len(days_to_generate)} packs generated")
                    
            except Exception as e:
                logger.error(f"Failed to build pack for {pack_date}: {e}", exc_info=True)
                failed += 1
                # Continue with next pack
                continue
        
        logger.info(f"✅ Generated {generated} pricing packs ({failed} failed)")
        
        # Verify
        await self.verify_packs(start_date, end_date)
    
    async def verify_packs(self, start_date: date, end_date: date):
        """Verify that packs were created successfully."""
        logger.info("\n📊 Verifying pricing packs...")
        
        packs = await self.conn.fetch(
            """
            SELECT date, status, is_fresh, COUNT(DISTINCT p.security_id) as price_count
            FROM pricing_packs pp
            LEFT JOIN prices p ON pp.id = p.pricing_pack_id
            WHERE pp.date BETWEEN $1 AND $2
            GROUP BY pp.date, pp.status, pp.is_fresh
            ORDER BY pp.date
            """,
            start_date,
            end_date
        )
        
        logger.info(f"Found {len(packs)} pricing packs")
        
        # Check for gaps
        trading_days = self._get_trading_days(start_date, end_date)
        pack_dates = {row['date'] for row in packs}
        missing_dates = [day for day in trading_days if day not in pack_dates]
        
        if missing_dates:
            logger.warning(f"⚠️  Missing packs for {len(missing_dates)} dates (first 10: {missing_dates[:10]})")
        else:
            logger.info("✅ All trading days have pricing packs")
        
        # Check prices
        packs_with_prices = [p for p in packs if p['price_count'] > 0]
        if packs_with_prices:
            avg_prices = sum(p['price_count'] for p in packs_with_prices) / len(packs_with_prices)
            logger.info(f"Average prices per pack: {avg_prices:.1f}")
        else:
            logger.warning("⚠️  No prices found in packs")
        
        # Sample pack
        if packs:
            sample = packs[0]
            logger.info(f"Sample pack: {sample['date']}, status={sample['status']}, prices={sample['price_count']}")
    
    async def run(self, days: int = 300, start_date: Optional[date] = None):
        """Run seeding operation."""
        try:
            await self.connect()
            
            await self.seed_historical_packs(days=days, start_date=start_date)
            
            logger.info("\n✅ Successfully seeded historical pricing packs!")
            
        except Exception as e:
            logger.error(f"Error seeding pricing packs: {e}", exc_info=True)
            raise
        finally:
            await self.disconnect()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed historical pricing packs")
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
        "--use-stubs",
        action="store_true",
        help="Use stub data instead of real providers"
    )
    args = parser.parse_args()
    
    start_date = None
    if args.start_date:
        start_date = date.fromisoformat(args.start_date)
    
    seeder = HistoricalPricingPackSeeder(use_stubs=args.use_stubs)
    await seeder.run(days=args.days, start_date=start_date)


if __name__ == "__main__":
    asyncio.run(main())

