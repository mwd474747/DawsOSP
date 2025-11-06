#!/usr/bin/env python3
"""
Master Seed Script - Seed All Data for DawsOS

This script orchestrates all seed scripts in the correct order:
1. Historical pricing packs (needs to exist first)
2. FX rates (references pricing packs)
3. Portfolio daily values (references pricing packs and FX rates)
4. Security sectors (independent)
5. Corporate actions (references pricing packs)
6. Economic indicators (references pricing packs)

Usage:
    python backend/scripts/seed_all_data.py
    python backend/scripts/seed_all_data.py --days 300 --use-stubs
"""

import asyncio
import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.seed_historical_pricing_packs import HistoricalPricingPackSeeder
from scripts.seed_missing_reference_data import ReferenceDataSeeder
from scripts.seed_portfolio_daily_values import PortfolioDailyValuesSeeder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_all_data(
    days: int = 300,
    start_date: date = None,
    use_stubs: bool = True,
    skip_pricing_packs: bool = False,
    skip_fx_rates: bool = False,
    skip_daily_values: bool = False,
    skip_reference_data: bool = False
):
    """
    Seed all data for DawsOS.
    
    Args:
        days: Number of days to generate (default: 300)
        start_date: Start date (default: today - days)
        use_stubs: Use stub data for prices (default: True)
        skip_pricing_packs: Skip pricing pack generation
        skip_fx_rates: Skip FX rate seeding
        skip_daily_values: Skip portfolio daily values
        skip_reference_data: Skip reference data (sectors, corporate actions)
    """
    if start_date is None:
        start_date = date.today() - timedelta(days=days)
    
    logger.info("=" * 80)
    logger.info("DAWSOS COMPREHENSIVE DATA SEEDING")
    logger.info("=" * 80)
    logger.info(f"Date range: {start_date} to {date.today()} ({days} days)")
    logger.info(f"Use stubs: {use_stubs}")
    logger.info("=" * 80)
    
    # Step 1: Historical Pricing Packs (CRITICAL)
    if not skip_pricing_packs:
        logger.info("\n📦 Step 1: Generating historical pricing packs...")
        try:
            pack_seeder = HistoricalPricingPackSeeder(use_stubs=use_stubs)
            await pack_seeder.run(days=days, start_date=start_date)
            logger.info("✅ Historical pricing packs generated")
        except Exception as e:
            logger.error(f"❌ Failed to generate pricing packs: {e}", exc_info=True)
            raise
    else:
        logger.info("⏭️  Skipping pricing pack generation")
    
    # Step 2: FX Rates (depends on pricing packs)
    if not skip_fx_rates:
        logger.info("\n💱 Step 2: Seeding FX rates...")
        try:
            fx_seeder = ReferenceDataSeeder()
            await fx_seeder.connect()
            await fx_seeder.seed_fx_rates()
            await fx_seeder.disconnect()
            logger.info("✅ FX rates seeded")
        except Exception as e:
            logger.error(f"❌ Failed to seed FX rates: {e}", exc_info=True)
            # Non-critical, continue
            logger.warning("Continuing with other steps...")
    else:
        logger.info("⏭️  Skipping FX rate seeding")
    
    # Step 3: Portfolio Daily Values (depends on pricing packs and FX rates)
    if not skip_daily_values:
        logger.info("\n📊 Step 3: Generating portfolio daily values...")
        try:
            daily_values_seeder = PortfolioDailyValuesSeeder()
            await daily_values_seeder.run(days=days, start_date=start_date)
            logger.info("✅ Portfolio daily values generated")
        except Exception as e:
            logger.error(f"❌ Failed to generate portfolio daily values: {e}", exc_info=True)
            # Non-critical, continue
            logger.warning("Continuing with other steps...")
    else:
        logger.info("⏭️  Skipping portfolio daily values generation")
    
    # Step 4: Reference Data (sectors, corporate actions)
    if not skip_reference_data:
        logger.info("\n📋 Step 4: Seeding reference data (sectors, corporate actions)...")
        try:
            ref_seeder = ReferenceDataSeeder()
            await ref_seeder.connect()
            await ref_seeder.seed_security_sectors()
            await ref_seeder.seed_corporate_actions()
            await ref_seeder.verify_seed_data()
            await ref_seeder.disconnect()
            logger.info("✅ Reference data seeded")
        except Exception as e:
            logger.error(f"❌ Failed to seed reference data: {e}", exc_info=True)
            # Non-critical, continue
            logger.warning("Continuing...")
    else:
        logger.info("⏭️  Skipping reference data seeding")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ DATA SEEDING COMPLETE")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("1. Verify currency attribution works (should return non-zero values)")
    logger.info("2. Verify risk metrics calculate correctly")
    logger.info("3. Verify factor analysis works")
    logger.info("4. Verify performance metrics (TWR, MWR, Sharpe) calculate correctly")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Seed all data for DawsOS")
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
        default=True,
        help="Use stub data for prices (default: True)"
    )
    parser.add_argument(
        "--skip-pricing-packs",
        action="store_true",
        help="Skip pricing pack generation"
    )
    parser.add_argument(
        "--skip-fx-rates",
        action="store_true",
        help="Skip FX rate seeding"
    )
    parser.add_argument(
        "--skip-daily-values",
        action="store_true",
        help="Skip portfolio daily values generation"
    )
    parser.add_argument(
        "--skip-reference-data",
        action="store_true",
        help="Skip reference data seeding"
    )
    args = parser.parse_args()
    
    start_date = None
    if args.start_date:
        start_date = date.fromisoformat(args.start_date)
    
    await seed_all_data(
        days=args.days,
        start_date=start_date,
        use_stubs=args.use_stubs,
        skip_pricing_packs=args.skip_pricing_packs,
        skip_fx_rates=args.skip_fx_rates,
        skip_daily_values=args.skip_daily_values,
        skip_reference_data=args.skip_reference_data
    )


if __name__ == "__main__":
    asyncio.run(main())

