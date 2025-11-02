"""
Simple script to fix macro indicators by applying transformations
Run this within the existing server environment
"""

import asyncio
import logging
from decimal import Decimal
from app.db.connection import execute_query, execute_statement
from app.services.fred_transformation import FREDTransformationService

logger = logging.getLogger("FixMacroData")
logging.basicConfig(level=logging.INFO)


async def fix_macro_data():
    """Fix macro indicators by applying transformations."""
    
    transformation_service = FREDTransformationService()
    
    # Get all unique series
    query = """
        SELECT DISTINCT indicator_id 
        FROM macro_indicators
        ORDER BY indicator_id
    """
    series_rows = await execute_query(query)
    
    if not series_rows:
        logger.error("No indicators found!")
        return
    
    logger.info(f"Found {len(series_rows)} series to process")
    
    for series_row in series_rows:
        series_id = series_row['indicator_id']
        logger.info(f"Processing {series_id}...")
        
        # Get all values for this series
        query = """
            SELECT indicator_id, date, value
            FROM macro_indicators
            WHERE indicator_id = $1
            ORDER BY date
        """
        rows = await execute_query(query, series_id)
        
        # Build historical values
        historical = []
        for row in rows:
            historical.append({
                'date': row['date'].isoformat(),
                'value': float(row['value'])
            })
        
        # Apply transformations
        updates = 0
        for i, row in enumerate(rows):
            raw_value = float(row['value'])
            date_str = row['date'].isoformat()
            
            # Historical values up to but not including current
            hist_for_transform = historical[:i] if i > 0 else None
            
            transformed = transformation_service.transform_fred_value(
                series_id=series_id,
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
                    series_id,
                    row['date']
                )
                
                if updates < 3:  # Log first few
                    logger.info(f"  Updated {date_str}: {raw_value:.2f} → {transformed:.6f}")
                updates += 1
        
        if updates > 0:
            logger.info(f"  Fixed {updates} values for {series_id}")
    
    # Validate key indicators
    logger.info("\nValidating key indicators...")
    
    key_indicators = {
        'UNRATE': (0.02, 0.15, 'Unemployment'),
        'CPIAUCSL': (-0.02, 0.20, 'Inflation YoY'),
        'T10Y2Y': (-0.03, 0.03, 'Yield Curve'),
        'GFDEGDQ188S': (0.3, 2.0, 'Debt to GDP'),
        'NAPM': (30, 70, 'Manufacturing PMI')
    }
    
    for series_id, (min_val, max_val, name) in key_indicators.items():
        query = """
            SELECT value FROM macro_indicators
            WHERE indicator_id = $1
            ORDER BY date DESC LIMIT 1
        """
        row = await execute_query(query, series_id)
        
        if row:
            value = float(row[0]['value'])
            if min_val <= value <= max_val:
                logger.info(f"  ✅ {name} ({series_id}): {value:.4f} in range [{min_val}, {max_val}]")
            else:
                logger.warning(f"  ❌ {name} ({series_id}): {value:.4f} OUTSIDE [{min_val}, {max_val}]")
    
    logger.info("\nFix complete!")


if __name__ == "__main__":
    # This should be run from within the server environment
    asyncio.run(fix_macro_data())