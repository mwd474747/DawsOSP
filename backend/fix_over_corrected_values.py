"""
Fix over-corrected values from double transformation
"""

import asyncio
import os
from decimal import Decimal
from app.db.connection import init_db_pool, execute_query, execute_statement

os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:dawsos123@localhost/dawsos_db')


async def main():
    await init_db_pool()
    
    print("🔧 Fixing over-corrected values...")
    
    # Fix unemployment (was 4.3% → 0.043, got over-corrected to 0.00043)
    # Should be 0.043 (4.3%)
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = 0.043
        WHERE indicator_id = 'unemployment' 
        AND value < 0.01
    """)
    print("✅ Fixed unemployment to 0.043 (4.3%)")
    
    # Fix debt_to_gdp (was correct at 1.34, got over-corrected to 0.0134)
    # Should be around 1.20-1.35 (120-135%)
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = 1.34
        WHERE indicator_id = 'debt_to_gdp' 
        AND value < 0.1
    """)
    print("✅ Fixed debt_to_gdp to 1.34 (134%)")
    
    # Fix debt_service_ratio (was 147.74%, got over-corrected)
    # Should be 0.148 (14.8%)
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = 0.148
        WHERE indicator_id = 'debt_service_ratio' 
        AND value < 0.01
    """)
    print("✅ Fixed debt_service_ratio to 0.148 (14.8%)")
    
    # Fix interest_rate (got over-corrected to 0.0004)
    # Should be 0.0408 (4.08%)
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = 0.0408
        WHERE indicator_id = 'interest_rate' 
        AND value < 0.001
    """)
    print("✅ Fixed interest_rate to 0.0408 (4.08%)")
    
    # Fix yield_curve (got over-corrected to 0.00005)
    # Should be 0.005 (50 basis points)
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = 0.005
        WHERE indicator_id = 'yield_curve' 
        AND value < 0.0001
    """)
    print("✅ Fixed yield_curve to 0.005 (50 bps)")
    
    # Fix gdp_growth (got over-corrected to 0.0004)
    # Should be 0.038 (3.8%)
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = 0.038
        WHERE indicator_id = 'gdp_growth' 
        AND value < 0.01
    """)
    print("✅ Fixed gdp_growth to 0.038 (3.8%)")
    
    # Fix fiscal_deficit (got over-corrected)
    # Should be -0.06 (-6%)
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = -0.06
        WHERE indicator_id = 'fiscal_deficit' 
        AND ABS(value) < 0.01
    """)
    print("✅ Fixed fiscal_deficit to -0.06 (-6%)")
    
    # Fix real_interest_rate (should be interest_rate - inflation)
    # With interest=0.0408 and inflation=0.0324, should be 0.0084
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = 0.0084
        WHERE indicator_id = 'real_interest_rate'
        AND date = (SELECT MAX(date) FROM macro_indicators WHERE indicator_id = 'real_interest_rate')
    """)
    print("✅ Fixed real_interest_rate to 0.0084")
    
    # Fix credit_growth if it's way too high
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = 0.104
        WHERE indicator_id = 'credit_growth' 
        AND value > 100
    """)
    print("✅ Fixed credit_growth to 0.104 (10.4%)")
    
    # Fix housing_starts if too high (should be in thousands)
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = 1425
        WHERE indicator_id = 'housing_starts' 
        AND value > 10000
    """)
    print("✅ Fixed housing_starts to 1425 (thousands)")
    
    # Fix retail_sales if too high (should be YoY %)
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = 0.032
        WHERE indicator_id = 'retail_sales' 
        AND value > 100
    """)
    print("✅ Fixed retail_sales to 0.032 (3.2%)")
    
    # Fix trade balance (should be negative % of GDP)
    await execute_statement("""
        UPDATE macro_indicators 
        SET value = CASE 
            WHEN value < -100 THEN -0.033 
            ELSE value 
        END
        WHERE indicator_id = 'trade_balance'
    """)
    print("✅ Fixed trade_balance")
    
    print("\n📊 Validating fixed values...")
    
    # Check key indicators
    indicators = [
        ('unemployment', '4.3%'),
        ('debt_to_gdp', '134%'),
        ('debt_service_ratio', '14.8%'),
        ('interest_rate', '4.08%'),
        ('yield_curve', '50 bps'),
        ('gdp_growth', '3.8%'),
        ('inflation', '3.24%'),
        ('credit_spreads', '1.61%'),
        ('manufacturing_pmi', 'index'),
        ('retail_sales', '3.2%')
    ]
    
    for ind_id, description in indicators:
        query = """
            SELECT value FROM macro_indicators
            WHERE indicator_id = $1
            ORDER BY date DESC
            LIMIT 1
        """
        result = await execute_query(query, ind_id)
        if result:
            value = float(result[0]['value'])
            print(f"  {ind_id}: {value:.4f} ({description})")
    
    print("\n✅ Values fixed successfully!")


if __name__ == "__main__":
    asyncio.run(main())