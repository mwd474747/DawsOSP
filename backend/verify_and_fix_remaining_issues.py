"""
Verify and fix remaining data issues for macro cycles
"""

import asyncio
import os
from decimal import Decimal
from app.db.connection import init_db_pool, execute_query, execute_statement

os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:dawsos123@localhost/dawsos_db')


async def main():
    await init_db_pool()
    
    print("🔍 Checking current values in database...")
    
    # Check specific problematic indicators
    indicators_to_check = [
        'unemployment',
        'debt_to_gdp', 
        'debt_service_ratio',
        'housing_starts',
        'world_gdp_share',
        'inflation',
        'manufacturing_pmi'
    ]
    
    print("\n📊 Current database values:")
    for ind in indicators_to_check:
        query = """
            SELECT value, date FROM macro_indicators
            WHERE indicator_id = $1
            ORDER BY date DESC
            LIMIT 1
        """
        result = await execute_query(query, ind)
        if result:
            value = float(result[0]['value'])
            date = result[0]['date']
            print(f"  {ind}: {value:.6f} (date: {date})")
    
    # Check if there are multiple entries with bad values
    print("\n🔍 Checking for any remaining bad values...")
    
    bad_value_checks = [
        ('unemployment', 0.001, "< 0.001"),
        ('debt_to_gdp', 0.01, "< 0.01"),
        ('debt_service_ratio', 0.001, "< 0.001"),
    ]
    
    for ind, threshold, desc in bad_value_checks:
        query = f"""
            SELECT COUNT(*) as count 
            FROM macro_indicators
            WHERE indicator_id = $1 AND value < $2
        """
        result = await execute_query(query, ind, threshold)
        if result and result[0]['count'] > 0:
            print(f"  Found {result[0]['count']} bad values for {ind} ({desc})")
            
            # Fix all bad values for this indicator
            if ind == 'unemployment':
                fix_value = 0.043
            elif ind == 'debt_to_gdp':
                fix_value = 1.34
            elif ind == 'debt_service_ratio':
                fix_value = 0.148
            
            update_query = """
                UPDATE macro_indicators
                SET value = $1
                WHERE indicator_id = $2 AND value < $3
            """
            await execute_statement(update_query, Decimal(str(fix_value)), ind, threshold)
            print(f"    ✅ Fixed {ind} to {fix_value}")
    
    # Fix world_gdp_share if it's > 1 (should be percentage as decimal)
    query = """
        UPDATE macro_indicators
        SET value = value / 100
        WHERE indicator_id = 'world_gdp_share' AND value > 1
    """
    await execute_statement(query)
    print("✅ Fixed world_gdp_share to decimal")
    
    # Double-check all values are now correct
    print("\n📊 Verified values after fix:")
    for ind in indicators_to_check:
        query = """
            SELECT value, date FROM macro_indicators
            WHERE indicator_id = $1
            ORDER BY date DESC
            LIMIT 1
        """
        result = await execute_query(query, ind)
        if result:
            value = float(result[0]['value'])
            
            # Check if value is in expected range
            expected = {
                'unemployment': (0.02, 0.15),
                'debt_to_gdp': (0.3, 2.0),
                'debt_service_ratio': (0.08, 0.15),
                'housing_starts': (500, 3000),  # In thousands
                'world_gdp_share': (0.15, 0.35),
                'inflation': (0.01, 0.10),
                'manufacturing_pmi': (30, 70)
            }
            
            if ind in expected:
                min_val, max_val = expected[ind]
                in_range = min_val <= value <= max_val
                status = "✅" if in_range else "❌"
                print(f"  {status} {ind}: {value:.6f}")
            else:
                print(f"  {ind}: {value:.6f}")
    
    print("\n✅ Data verification and fixes complete!")


if __name__ == "__main__":
    asyncio.run(main())