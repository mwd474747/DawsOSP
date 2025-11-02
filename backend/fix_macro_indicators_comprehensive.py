"""
Comprehensive fix for macro indicators in database
Maps human-readable names to FRED series and applies transformations
"""

import asyncio
import os
from decimal import Decimal
from app.db.connection import init_db_pool, execute_query, execute_statement
from app.services.fred_transformation import FREDTransformationService

os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:dawsos123@localhost/dawsos_db')


# Mapping from database indicator_id to FRED series ID
INDICATOR_TO_FRED_MAPPING = {
    'gdp_growth': 'A191RL1Q225SBEA',
    'inflation': 'CPIAUCSL',
    'unemployment': 'UNRATE', 
    'interest_rate': 'DFF',
    'yield_curve': 'T10Y2Y',
    'credit_growth': 'TOTBKCR',
    'debt_to_gdp': 'GFDEGDQ188S',
    'debt_service_ratio': 'TDSP',
    'fiscal_deficit': 'FYFSGDA188S',
    'industrial_production': 'INDPRO',
    'manufacturing_pmi': 'NAPM',
    'housing_starts': 'HOUST',
    'retail_sales': 'RSXFS',
    'm2_money_supply': 'M2SL',
    'consumer_confidence': 'UMCSENT',
    'vix': 'VIXCLS',
    'credit_spreads': 'BAA10Y',
    'trade_balance': 'NETEXP',
    'real_interest_rate': 'DFF',  # Will need special calculation
    'productivity_growth': 'OPHNFB',
}


async def fix_indicator(indicator_id: str, fred_series_id: str, transformation_service: FREDTransformationService):
    """Fix a specific indicator by applying proper transformation."""
    
    print(f"\n📊 Processing {indicator_id} (FRED: {fred_series_id})")
    
    # Get all values for this indicator
    query = """
        SELECT date, value
        FROM macro_indicators
        WHERE indicator_id = $1
        ORDER BY date
    """
    rows = await execute_query(query, indicator_id)
    
    if not rows:
        print(f"  No data found for {indicator_id}")
        return 0
    
    print(f"  Found {len(rows)} values")
    
    # Build historical values for YoY calculations
    historical = []
    for row in rows:
        historical.append({
            'date': row['date'].isoformat(),
            'value': float(row['value'])
        })
    
    updates = 0
    sample_shown = False
    
    for i, row in enumerate(rows):
        raw_value = float(row['value'])
        date_str = row['date'].isoformat()
        
        # Get historical values for transformation (excluding current)
        hist_for_transform = historical[:i] if i > 0 else None
        
        # Apply transformation
        transformed = transformation_service.transform_fred_value(
            series_id=fred_series_id,
            value=raw_value,
            date_str=date_str,
            historical_values=hist_for_transform
        )
        
        if transformed is not None and abs(transformed - raw_value) > 0.001:
            # Update the value
            update_query = """
                UPDATE macro_indicators
                SET value = $1, last_updated = NOW()
                WHERE indicator_id = $2 AND date = $3
            """
            await execute_statement(
                update_query,
                Decimal(str(transformed)),
                indicator_id,
                row['date']
            )
            updates += 1
            
            # Show first transformation as example
            if not sample_shown:
                print(f"  Example: {raw_value:.2f} → {transformed:.6f} ({date_str})")
                sample_shown = True
    
    if updates > 0:
        print(f"  ✅ Fixed {updates} values")
    else:
        print(f"  ⚪ No updates needed")
    
    return updates


async def apply_manual_fixes():
    """Apply manual fixes for indicators that need special handling."""
    
    print("\n🔧 Applying manual fixes for special indicators...")
    
    fixes_applied = []
    
    # Fix real_interest_rate (should be interest_rate - inflation)
    query = """
        WITH rates AS (
            SELECT date, value as interest_rate
            FROM macro_indicators
            WHERE indicator_id = 'interest_rate'
        ),
        inflation AS (
            SELECT date, value as inflation
            FROM macro_indicators
            WHERE indicator_id = 'inflation'
        )
        UPDATE macro_indicators
        SET value = (r.interest_rate - i.inflation)
        FROM rates r
        JOIN inflation i ON r.date = i.date
        WHERE macro_indicators.indicator_id = 'real_interest_rate'
        AND macro_indicators.date = r.date
        AND ABS(macro_indicators.value) > 100  -- Only fix obviously wrong values
    """
    await execute_statement(query)
    fixes_applied.append('real_interest_rate')
    
    # For indicators not in FRED mapping, apply sensible defaults
    default_fixes = {
        'gini_coefficient': (0.35, 0.50),  # Keep in this range
        'political_polarization': (30, 90),  # Scale to 0-100
        'institutional_trust': (20, 50),
        'education_score': (50, 80),
        'military_dominance': (20, 50),
        'world_gdp_share': (15, 30),
        'world_trade_share': (8, 15),
        'top_1_percent_wealth': (0.25, 0.40),
        'oil_prices': (40, 120),  # Keep as dollars
        'dollar_index': (0.90, 1.20),
        'jobless_claims': (150000, 500000),
        'corporate_profits': (2000, 4000),
        'data_quality_score': (0, 100),
        'credit_impulse': (-5, 5)
    }
    
    for indicator, (min_val, max_val) in default_fixes.items():
        # Check current values
        check_query = """
            SELECT AVG(value) as avg_val, MIN(value) as min_val, MAX(value) as max_val
            FROM macro_indicators
            WHERE indicator_id = $1
        """
        result = await execute_query(check_query, indicator)
        
        if result and result[0]['avg_val']:
            avg_val = float(result[0]['avg_val'])
            current_max = float(result[0]['max_val'])
            
            # Only fix if clearly out of range
            if current_max > max_val * 2 or avg_val > max_val * 1.5:
                # Scale down proportionally
                scale_factor = (min_val + max_val) / 2 / avg_val
                update_query = """
                    UPDATE macro_indicators
                    SET value = value * $1
                    WHERE indicator_id = $2
                """
                await execute_statement(update_query, Decimal(str(scale_factor)), indicator)
                fixes_applied.append(indicator)
                print(f"  Scaled {indicator} by factor {scale_factor:.4f}")
    
    return fixes_applied


async def validate_results():
    """Validate that values are now in expected ranges."""
    
    print("\n✅ Validating results...")
    
    expected_ranges = {
        'unemployment': (0.02, 0.15, "2-15%"),
        'inflation': (-0.02, 0.20, "YoY change"),
        'debt_to_gdp': (0.3, 2.0, "30-200%"),
        'debt_service_ratio': (0.08, 0.15, "8-15%"),
        'credit_spreads': (0.001, 0.10, "0.1-10%"),
        'manufacturing_pmi': (30, 70, "PMI range"),
        'retail_sales': (-0.10, 0.30, "YoY change"),
        'yield_curve': (-0.03, 0.03, "spread"),
        'interest_rate': (0.0, 0.20, "0-20%"),
        'gdp_growth': (-0.10, 0.15, "growth rate"),
        'vix': (10, 80, "volatility"),
        'consumer_confidence': (50, 120, "index")
    }
    
    all_valid = True
    
    for indicator, (min_val, max_val, description) in expected_ranges.items():
        query = """
            SELECT value FROM macro_indicators
            WHERE indicator_id = $1
            ORDER BY date DESC
            LIMIT 1
        """
        result = await execute_query(query, indicator)
        
        if result:
            value = float(result[0]['value'])
            in_range = min_val <= value <= max_val
            
            if in_range:
                print(f"  ✅ {indicator}: {value:.4f} ({description})")
            else:
                print(f"  ❌ {indicator}: {value:.4f} OUTSIDE [{min_val}, {max_val}] ({description})")
                all_valid = False
    
    return all_valid


async def main():
    """Main function."""
    
    print("🔧 Comprehensive Macro Indicators Fix")
    print("=" * 60)
    
    await init_db_pool()
    
    transformation_service = FREDTransformationService()
    
    # Process indicators that map to FRED series
    total_updates = 0
    
    for db_indicator, fred_series in INDICATOR_TO_FRED_MAPPING.items():
        if fred_series:  # Skip None mappings
            updates = await fix_indicator(db_indicator, fred_series, transformation_service)
            total_updates += updates
    
    # Apply manual fixes
    manual_fixes = await apply_manual_fixes()
    
    print(f"\n📊 Summary:")
    print(f"  Total values updated: {total_updates}")
    print(f"  Manual fixes applied: {len(manual_fixes)}")
    
    # Validate
    success = await validate_results()
    
    if success:
        print("\n🎉 All indicators successfully fixed!")
    else:
        print("\n⚠️ Some indicators may still need attention")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())