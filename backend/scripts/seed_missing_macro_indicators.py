#!/usr/bin/env python3
"""
Seed Missing Macro Indicators Script

Purpose: Seed database with missing macro indicators using default values from JSON configuration
Created: 2025-11-02
"""

import json
import asyncio
import logging
from datetime import date, datetime
from pathlib import Path
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.connection import execute_query, execute_statement, init_db_pool, close_db_pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_existing_indicators():
    """Get list of all unique indicator IDs currently in the database."""
    query = """
        SELECT DISTINCT indicator_id
        FROM macro_indicators
        ORDER BY indicator_id
    """
    rows = await execute_query(query)
    return {row['indicator_id'] for row in rows}


async def load_config_indicators():
    """Load all indicators from the macro_indicators_defaults.json config."""
    config_path = Path(__file__).parent.parent / "config" / "macro_indicators_defaults.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Extract all indicators from all categories
    indicators = {}
    for category_key, category_data in config['categories'].items():
        for indicator_id, indicator_data in category_data['indicators'].items():
            # Store with both the main ID and any aliases
            indicators[indicator_id] = {
                'category': category_key,
                'name': indicator_id.replace('_', ' ').title(),
                'data': indicator_data
            }
            
            # Also include aliases as separate entries pointing to the same data
            if 'aliases' in indicator_data:
                for alias in indicator_data['aliases']:
                    if alias not in indicators:  # Don't override if already exists
                        indicators[alias] = {
                            'category': category_key,
                            'name': indicator_data.get('notes', alias),
                            'data': indicator_data,
                            'is_alias': True,
                            'primary_id': indicator_id
                        }
    
    return indicators, config


async def seed_missing_indicators(dry_run=False):
    """Seed missing indicators with default values."""
    
    # Get existing indicators
    existing_ids = await get_existing_indicators()
    logger.info(f"Found {len(existing_ids)} unique indicator IDs in database")
    
    # Load configuration
    all_indicators, config = await load_config_indicators()
    logger.info(f"Found {len(all_indicators)} indicators (including aliases) in configuration")
    
    # Find missing indicators
    missing_indicators = {}
    for indicator_id, indicator_info in all_indicators.items():
        if indicator_id not in existing_ids:
            # Skip aliases if the primary indicator exists
            if indicator_info.get('is_alias'):
                primary_id = indicator_info.get('primary_id')
                if primary_id in existing_ids:
                    logger.debug(f"Skipping alias {indicator_id} as primary {primary_id} exists")
                    continue
            missing_indicators[indicator_id] = indicator_info
    
    logger.info(f"Found {len(missing_indicators)} missing indicators to seed")
    
    if not missing_indicators:
        logger.info("All indicators already present in database!")
        return 0
    
    # Display missing indicators
    logger.info("\nMissing indicators by category:")
    categories = {}
    for ind_id, ind_info in missing_indicators.items():
        cat = ind_info['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ind_id)
    
    for cat, indicators in sorted(categories.items()):
        logger.info(f"  {cat}: {', '.join(sorted(indicators))}")
    
    if dry_run:
        logger.info("\nDRY RUN - No data will be inserted")
        return len(missing_indicators)
    
    # Insert missing indicators
    insert_query = """
        INSERT INTO macro_indicators (
            indicator_id,
            indicator_name, 
            date,
            value,
            units,
            frequency,
            source,
            last_updated
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (indicator_id, date) DO UPDATE
        SET value = EXCLUDED.value,
            source = EXCLUDED.source,
            last_updated = EXCLUDED.last_updated
    """
    
    inserted_count = 0
    asof_date = date.today()
    
    for indicator_id, indicator_info in missing_indicators.items():
        data = indicator_info['data']
        
        # Extract values
        value = data.get('value', 0.0)
        units = data.get('unit', 'decimal')
        
        # Map display units to standard units
        if data.get('display_unit') == 'percentage':
            units = 'Percent'
        elif data.get('display_unit') == 'index':
            units = 'Index'
        elif data.get('display_unit') == 'basis_points':
            units = 'Basis Points'
        elif data.get('display_unit') == 'percentage_of_gdp':
            units = 'Percent of GDP'
        
        # Determine frequency - most macro indicators are monthly or quarterly
        frequency = 'Monthly'  # Default
        if 'daily' in data.get('notes', '').lower():
            frequency = 'Daily'
        elif 'quarterly' in data.get('notes', '').lower():
            frequency = 'Quarterly'
        elif 'annual' in data.get('notes', '').lower():
            frequency = 'Annual'
        
        # Use notes or indicator name for description
        indicator_name = data.get('notes', indicator_info['name'])
        
        # Mark source as 'default' to indicate these are placeholder values
        source = 'default'
        
        try:
            await execute_statement(
                insert_query,
                indicator_id,
                indicator_name,
                asof_date,
                value,
                units,
                frequency,
                source,
                datetime.now()
            )
            inserted_count += 1
            logger.info(f"  Inserted: {indicator_id} = {value} ({units}) [{data.get('confidence', 'default')} confidence]")
        except Exception as e:
            logger.error(f"  Failed to insert {indicator_id}: {e}")
    
    logger.info(f"\nSuccessfully seeded {inserted_count} missing indicators")
    
    # Verify total count
    query = "SELECT COUNT(DISTINCT indicator_id) as count FROM macro_indicators"
    result = await execute_query(query)
    total_count = result[0]['count'] if result else 0
    logger.info(f"Total unique indicators in database: {total_count}")
    
    # Check if we have values for critical indicators
    critical_indicators = ['gdp_growth', 'inflation', 'unemployment', 'interest_rate', 
                          'yield_curve', 'credit_growth', 'debt_to_gdp']
    
    logger.info("\nVerifying critical indicators:")
    for ind_id in critical_indicators:
        query = "SELECT COUNT(*) as count FROM macro_indicators WHERE indicator_id = $1"
        result = await execute_query(query, ind_id)
        count = result[0]['count'] if result else 0
        status = "✓" if count > 0 else "✗"
        logger.info(f"  {status} {ind_id}: {count} data points")
    
    return inserted_count


async def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed missing macro indicators with default values')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be inserted without making changes')
    args = parser.parse_args()
    
    try:
        # Initialize database pool
        await init_db_pool()
        
        logger.info("Starting macro indicators seeding process...")
        logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
        
        count = await seed_missing_indicators(dry_run=args.dry_run)
        
        if count > 0:
            logger.info(f"\n{'Would seed' if args.dry_run else 'Seeded'} {count} missing indicators")
            if args.dry_run:
                logger.info("Run without --dry-run to actually insert the data")
        else:
            logger.info("\nAll indicators already present - no seeding needed!")
            
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        raise
    finally:
        # Close database pool
        await close_db_pool()


if __name__ == "__main__":
    asyncio.run(main())