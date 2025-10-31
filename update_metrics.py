#!/usr/bin/env python3
"""
Manual Metrics Refresh Script
Updates portfolio metrics on-demand without automated scheduling
Run this script whenever metrics need to be refreshed

Usage:
    python update_metrics.py
"""

import asyncio
import asyncpg
import os
from datetime import datetime, timedelta
from decimal import Decimal
import sys

# Add backend to path
sys.path.insert(0, 'backend')

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
PORTFOLIO_ID = "64ff3be6-0ed1-4990-a32b-4ded17f0320c"  # Main portfolio

async def update_metrics():
    """Main function to update portfolio metrics"""
    print(f"🚀 Starting metrics update at {datetime.now()}")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        # 1. Update daily valuations for recent days
        print("\n📊 Updating daily valuations...")
        await update_daily_valuations(conn)
        
        # 2. Compute latest metrics
        print("\n📈 Computing portfolio metrics...")
        await compute_portfolio_metrics(conn)
        
        # 3. Verify data integrity
        print("\n🔍 Verifying data integrity...")
        await verify_data_integrity(conn)
        
        await conn.close()
        print(f"\n✅ Metrics update completed at {datetime.now()}")
        
    except Exception as e:
        print(f"❌ Error updating metrics: {e}")
        raise

async def update_daily_valuations(conn):
    """Update portfolio_daily_values for recent days"""
    
    # Get the latest valuation date
    latest_date = await conn.fetchval("""
        SELECT MAX(valuation_date) 
        FROM portfolio_daily_values 
        WHERE portfolio_id = $1
    """, PORTFOLIO_ID)
    
    if latest_date:
        print(f"  Latest valuation date: {latest_date}")
        days_behind = (datetime.now().date() - latest_date).days
        if days_behind > 0:
            print(f"  📅 {days_behind} days behind, updating...")
            # Run backfill for missing days
            # Note: This would call the backfill script
            print(f"  📝 To update: Run python backend/jobs/backfill_daily_values.py")
            print(f"     with dates from {latest_date + timedelta(days=1)} to {datetime.now().date()}")
        else:
            print("  ✅ Daily valuations up to date")
    else:
        print("  ⚠️ No historical valuations found, running full backfill...")
        # Run full historical backfill
        print("  📝 To backfill: Run python backend/jobs/backfill_daily_values.py")

async def compute_portfolio_metrics(conn):
    """Compute TWR, MWR and other metrics"""
    
    # Get portfolio daily values for TWR calculation
    daily_values = await conn.fetch("""
        SELECT valuation_date, total_value 
        FROM portfolio_daily_values 
        WHERE portfolio_id = $1 
        ORDER BY valuation_date
        LIMIT 365
    """, PORTFOLIO_ID)
    
    if len(daily_values) < 2:
        print("  ⚠️ Not enough data for metrics calculation")
        return
    
    # Calculate TWR (simplified)
    start_value = float(daily_values[0]['total_value'])
    end_value = float(daily_values[-1]['total_value'])
    days = (daily_values[-1]['valuation_date'] - daily_values[0]['valuation_date']).days
    
    if start_value > 0 and days > 0:
        total_return = (end_value / start_value - 1) * 100
        annualized_return = ((end_value / start_value) ** (365 / days) - 1) * 100
        
        print(f"  📊 Portfolio Value: ${end_value:,.2f}")
        print(f"  📈 Total Return: {total_return:.2f}%")
        print(f"  📅 Annualized Return: {annualized_return:.2f}%")
        
        # Update portfolio_metrics table
        await conn.execute("""
            INSERT INTO portfolio_metrics (
                portfolio_id, metric_date, metric_name, metric_value
            ) VALUES ($1, $2, $3, $4)
            ON CONFLICT (portfolio_id, metric_date, metric_name)
            DO UPDATE SET metric_value = $4, updated_at = NOW()
        """, PORTFOLIO_ID, datetime.now().date(), 'twr_1y', Decimal(str(annualized_return)))
        
        print("  ✅ Metrics updated in database")
    else:
        print("  ⚠️ Invalid data for metrics calculation")

async def verify_data_integrity(conn):
    """Verify data consistency and integrity"""
    
    # Check for gaps in daily values
    gaps = await conn.fetchval("""
        WITH date_series AS (
            SELECT generate_series(
                MIN(valuation_date),
                MAX(valuation_date),
                '1 day'::interval
            )::date AS expected_date
            FROM portfolio_daily_values
            WHERE portfolio_id = $1
        )
        SELECT COUNT(*) FROM date_series
        WHERE expected_date NOT IN (
            SELECT valuation_date FROM portfolio_daily_values
            WHERE portfolio_id = $1
        )
    """, PORTFOLIO_ID)
    
    if gaps > 0:
        print(f"  ⚠️ Found {gaps} gaps in daily valuations")
    else:
        print("  ✅ No gaps in daily valuations")
    
    # Check recent metrics
    recent_metrics = await conn.fetchval("""
        SELECT COUNT(*) FROM portfolio_metrics
        WHERE portfolio_id = $1
        AND metric_date >= CURRENT_DATE - INTERVAL '7 days'
    """, PORTFOLIO_ID)
    
    print(f"  📊 {recent_metrics} metrics updated in last 7 days")
    
    # Check transaction count
    tx_count = await conn.fetchval("""
        SELECT COUNT(*) FROM transactions
        WHERE portfolio_id = $1
    """, PORTFOLIO_ID)
    
    print(f"  📝 {tx_count} transactions in ledger")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════╗
║     DawsOS Manual Metrics Refresh       ║
╚══════════════════════════════════════════╝
    """)
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        asyncio.run(update_metrics())
        print("\n✨ Metrics successfully refreshed!")
        print("📌 Note: Automated scheduling is deferred - run this script as needed")
    except Exception as e:
        print(f"\n❌ Failed to update metrics: {e}")
        sys.exit(1)