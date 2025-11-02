#!/usr/bin/env python
"""
Fix Macro Indicators Script

Purpose: Fix existing macro indicators in database by applying proper FRED transformations
Created: 2025-11-02

This script:
1. Fetches all raw macro indicators from the database
2. Applies proper transformations using FREDTransformationService  
3. Updates the database with corrected values
4. Validates the results
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from pathlib import Path
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.connection import execute_query, execute_statement, get_db_pool
from app.services.fred_transformation import FREDTransformationService
from app.integrations.fred_provider import FREDProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FixMacroIndicators")


async def get_all_indicators() -> List[Dict]:
    """Fetch all macro indicators from database."""
    query = """
        SELECT DISTINCT 
            indicator_id,
            indicator_name,
            date,
            value,
            units,
            source
        FROM macro_indicators
        ORDER BY indicator_id, date
    """
    rows = await execute_query(query)
    return rows


async def get_indicators_by_series(series_id: str) -> List[Dict]:
    """Fetch all values for a specific series."""
    query = """
        SELECT 
            indicator_id,
            date,
            value
        FROM macro_indicators
        WHERE indicator_id = $1
        ORDER BY date
    """
    rows = await execute_query(query, series_id)
    return rows


async def update_indicator_value(
    indicator_id: str,
    date: str,
    new_value: float
):
    """Update a single indicator value in the database."""
    query = """
        UPDATE macro_indicators 
        SET value = $1,
            last_updated = NOW()
        WHERE indicator_id = $2 
        AND date = $3
    """
    await execute_statement(
        query,
        Decimal(str(new_value)),
        indicator_id,
        date
    )


async def fix_indicators_for_series(series_id: str, transformation_service: FREDTransformationService):
    """Fix all indicators for a specific FRED series."""
    
    logger.info(f"Processing series: {series_id}")
    
    # Get all values for this series
    indicators = await get_indicators_by_series(series_id)
    
    if not indicators:
        logger.warning(f"No indicators found for series {series_id}")
        return
    
    # Build historical values list
    historical_values = []
    for ind in indicators:
        historical_values.append({
            'date': ind['date'].isoformat(),
            'value': float(ind['value'])
        })
    
    # Process each indicator with transformation
    updates_made = 0
    for i, ind in enumerate(indicators):
        raw_value = float(ind['value'])
        date_str = ind['date'].isoformat()
        
        # Use historical values up to (but not including) current for YoY calculations
        historical_for_transform = historical_values[:i] if i > 0 else None
        
        # Apply transformation
        transformed_value = transformation_service.transform_fred_value(
            series_id=series_id,
            value=raw_value,
            date_str=date_str,
            historical_values=historical_for_transform
        )
        
        # Update if transformation changed the value significantly
        if transformed_value is not None and abs(transformed_value - raw_value) > 0.001:
            await update_indicator_value(
                indicator_id=series_id,
                date=ind['date'],
                new_value=transformed_value
            )
            
            # Log significant transformations
            if updates_made < 5:  # Log first few for visibility
                indicator_name = transformation_service.get_indicator_name(series_id)
                logger.info(
                    f"  Updated {indicator_name} ({series_id}) on {date_str}: "
                    f"{raw_value:.2f} → {transformed_value:.6f}"
                )
            updates_made += 1
    
    if updates_made > 0:
        logger.info(f"  ✅ Fixed {updates_made} values for {series_id}")
    else:
        logger.info(f"  ⚪ No updates needed for {series_id}")


async def validate_results():
    """Validate that the fixed values are in expected ranges."""
    
    logger.info("\n📊 Validating fixed values...")
    
    # Expected ranges for key indicators (as decimals/percentages)
    expected_ranges = {
        'UNRATE': (0.02, 0.15),          # Unemployment: 2% - 15%
        'CPIAUCSL': (-0.02, 0.20),       # Inflation YoY: -2% - 20%
        'T10Y2Y': (-0.03, 0.03),         # Yield curve: -3% - 3%
        'DFF': (0.0, 0.20),              # Fed funds rate: 0% - 20%
        'BAA10Y': (0.001, 0.10),         # Credit spreads: 0.1% - 10%
        'GFDEGDQ188S': (0.3, 2.0),       # Debt to GDP: 30% - 200%
        'TDSP': (0.08, 0.15),            # Debt service ratio: 8% - 15%
        'NAPM': (30, 70),                # Manufacturing PMI: 30 - 70
        'UMCSENT': (50, 120),            # Consumer sentiment: 50 - 120
        'VIXCLS': (10, 80),              # VIX: 10 - 80
        'RSXFS': (-0.10, 0.30),          # Retail sales YoY: -10% - 30%
    }
    
    validation_issues = []
    
    for series_id, (min_val, max_val) in expected_ranges.items():
        # Get latest value
        query = """
            SELECT value, date
            FROM macro_indicators
            WHERE indicator_id = $1
            ORDER BY date DESC
            LIMIT 1
        """
        row = await execute_query(query, series_id)
        
        if row:
            value = float(row[0]['value'])
            date = row[0]['date']
            
            if value < min_val or value > max_val:
                validation_issues.append(
                    f"  ❌ {series_id}: {value:.6f} outside range [{min_val}, {max_val}] on {date}"
                )
            else:
                logger.info(f"  ✅ {series_id}: {value:.6f} within range [{min_val}, {max_val}]")
    
    if validation_issues:
        logger.warning("Validation issues found:")
        for issue in validation_issues:
            logger.warning(issue)
    else:
        logger.info("\n✅ All indicators within expected ranges!")
    
    return len(validation_issues) == 0


async def main():
    """Main function to fix all macro indicators."""
    
    logger.info("🔧 Starting macro indicators fix...")
    logger.info("=" * 60)
    
    # Initialize transformation service
    transformation_service = FREDTransformationService()
    
    # Get unique series IDs from database
    query = """
        SELECT DISTINCT indicator_id 
        FROM macro_indicators
        ORDER BY indicator_id
    """
    rows = await execute_query(query)
    
    if not rows:
        logger.error("No indicators found in database!")
        return
    
    series_ids = [row['indicator_id'] for row in rows]
    logger.info(f"Found {len(series_ids)} unique series to process")
    
    # Process each series
    for series_id in series_ids:
        try:
            await fix_indicators_for_series(series_id, transformation_service)
        except Exception as e:
            logger.error(f"Failed to process {series_id}: {e}", exc_info=True)
    
    # Validate results
    logger.info("\n" + "=" * 60)
    success = await validate_results()
    
    if success:
        logger.info("\n🎉 Successfully fixed all macro indicators!")
    else:
        logger.warning("\n⚠️ Some indicators may still need attention")
    
    logger.info("=" * 60)
    logger.info("Fix complete!")


if __name__ == "__main__":
    asyncio.run(main())