#!/usr/bin/env python3
"""
Populate economic_indicators table with test data for factor analysis
"""

import asyncio
import asyncpg
import os
from datetime import datetime, date, timedelta
import random
import sys
sys.path.append('backend')

from app.db.connection import init_db_pool, get_db_pool

async def populate_test_data():
    """Populate economic_indicators with test data"""
    print("=" * 60)
    print("POPULATING ECONOMIC INDICATORS TEST DATA")
    print("=" * 60)
    
    try:
        # Initialize database pool
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        await init_db_pool(database_url)
        print("✅ Database pool initialized")
        
        pool = await get_db_pool()
        
        async with pool.acquire() as db:
            print("✅ Database connection established")
            
            # Clear existing test data
            await db.execute("DELETE FROM economic_indicators")
            print("✅ Cleared existing data")
            
            # Generate 365 days of test data
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
            
            print(f"\n📊 Generating data from {start_date} to {end_date}...")
            
            # Base values for each indicator
            base_values = {
                'DFII10': 2.5,     # Real rate (10-year TIPS)
                'T10YIE': 2.3,     # Inflation expectations
                'BAMLC0A0CM': 1.2, # Credit spread
                'DTWEXBGS': 115.0, # USD index
                'SP500': 4500.0    # S&P 500
            }
            
            # Generate daily values
            current_date = start_date
            values_to_insert = []
            
            while current_date <= end_date:
                # Skip weekends
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    for series_id, base_value in base_values.items():
                        # Add random walk with mean reversion
                        change = random.gauss(0, 0.01)  # 1% daily volatility
                        value = base_value * (1 + change)
                        
                        # Add trend for SP500
                        if series_id == 'SP500':
                            days_elapsed = (current_date - start_date).days
                            value = value * (1 + 0.0003 * days_elapsed)  # 0.03% daily trend
                        
                        values_to_insert.append((
                            series_id,
                            current_date,
                            value,
                            'percent' if series_id in ['DFII10', 'T10YIE', 'BAMLC0A0CM'] else 'index',
                            'FRED'
                        ))
                
                current_date += timedelta(days=1)
            
            print(f"📝 Inserting {len(values_to_insert)} records...")
            
            # Batch insert
            await db.executemany("""
                INSERT INTO economic_indicators (series_id, asof_date, value, unit, source)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (series_id, asof_date) DO UPDATE 
                SET value = EXCLUDED.value, unit = EXCLUDED.unit
            """, values_to_insert)
            
            print("✅ Data inserted successfully")
            
            # Verify the data
            count = await db.fetchval("SELECT COUNT(*) FROM economic_indicators")
            series_count = await db.fetchval("SELECT COUNT(DISTINCT series_id) FROM economic_indicators")
            date_range = await db.fetchrow("""
                SELECT MIN(asof_date) as min_date, MAX(asof_date) as max_date
                FROM economic_indicators
            """)
            
            print(f"\n📊 Verification:")
            print(f"   Total records: {count}")
            print(f"   Unique series: {series_count}")
            print(f"   Date range: {date_range['min_date']} to {date_range['max_date']}")
            
            # Sample data
            sample = await db.fetch("""
                SELECT series_id, COUNT(*) as count
                FROM economic_indicators
                GROUP BY series_id
                ORDER BY series_id
            """)
            
            print("\n   Records per series:")
            for row in sample:
                print(f"      {row['series_id']:15s}: {row['count']} records")
    
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("POPULATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(populate_test_data())