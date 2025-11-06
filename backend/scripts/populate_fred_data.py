#!/usr/bin/env python3
"""
FRED Data Ingestion Script
Populates the economic_indicators table with latest FRED economic data.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
import logging
import httpx
import asyncpg
from typing import Dict, List, Optional

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FRED API Configuration
FRED_API_KEY = os.environ.get("FRED_API_KEY")
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL")

# FRED series to fetch
FRED_SERIES_MAPPING = {
    # Growth indicators
    "GDP": "GDP",  # Gross Domestic Product
    "GDPC1": "real_gdp",  # Real GDP
    
    # Inflation
    "CPIAUCSL": "cpi",  # Consumer Price Index
    "CPILFESL": "core_cpi",  # Core CPI
    
    # Employment
    "UNRATE": "unemployment_rate",  # Unemployment Rate
    "PAYEMS": "nonfarm_payrolls",  # Nonfarm Payrolls
    
    # Interest rates
    "DFF": "fed_funds_rate",  # Fed Funds Rate
    "DGS10": "treasury_10y",  # 10-Year Treasury
    "DGS2": "treasury_2y",  # 2-Year Treasury
    "T10Y2Y": "yield_curve_spread",  # 10Y-2Y Spread
    
    # Credit and money
    "TOTBKCR": "bank_credit",  # Bank Credit
    "M2SL": "m2_money_supply",  # M2 Money Supply
    
    # Manufacturing and production
    "INDPRO": "industrial_production",  # Industrial Production
    "MANEMP": "manufacturing_employment",  # Manufacturing Employment
    
    # Consumer indicators
    "RSXFS": "retail_sales",  # Retail Sales
    "UMCSENT": "consumer_sentiment",  # Consumer Sentiment
    "DSPIC96": "disposable_income",  # Real Disposable Personal Income
    
    # Housing
    "HOUST": "housing_starts",  # Housing Starts
    "MORTGAGE30US": "mortgage_rate_30y",  # 30-Year Mortgage Rate
    
    # Business indicators
    "CP": "corporate_profits",  # Corporate Profits
    "BOPGSTB": "trade_balance",  # Trade Balance
    
    # Volatility
    "VIXCLS": "vix",  # VIX Index
    
    # Dollar strength
    "DTWEXBGS": "dollar_index",  # Dollar Index
    
    # Commodity prices
    "DCOILWTICO": "wti_oil",  # WTI Oil Price
    "GOLDAMGBD228NLBM": "gold_price",  # Gold Price
}

class FREDDataIngester:
    """Handles FRED data fetching and database population."""
    
    def __init__(self, api_key: str, database_url: str):
        self.api_key = api_key
        self.database_url = database_url
        self.db_pool = None
        
    async def connect_db(self):
        """Create database connection pool."""
        self.db_pool = await asyncpg.create_pool(self.database_url)
        logger.info("Connected to database")
        
    async def disconnect_db(self):
        """Close database connection pool."""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Disconnected from database")
    
    async def fetch_fred_series(self, series_id: str, start_date: date) -> List[Dict]:
        """Fetch data for a specific FRED series."""
        async with httpx.AsyncClient() as client:
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "observation_start": start_date.isoformat(),
                "observation_end": date.today().isoformat(),
                "sort_order": "desc",
                "limit": 1000
            }
            
            try:
                response = await client.get(
                    f"{FRED_BASE_URL}/series/observations",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                observations = data.get("observations", [])
                logger.info(f"Fetched {len(observations)} observations for {series_id}")
                return observations
                
            except Exception as e:
                logger.error(f"Error fetching {series_id}: {e}")
                return []
    
    async def store_indicators(self, indicators: List[Dict]):
        """Store indicators in the database."""
        async with self.db_pool.acquire() as conn:
            # Prepare insert query - matching actual table structure
            insert_query = """
                INSERT INTO economic_indicators 
                    (series_id, asof_date, value, unit, source, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (series_id, asof_date) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    unit = EXCLUDED.unit,
                    source = EXCLUDED.source
            """
            
            # Batch insert
            rows_to_insert = []
            for indicator in indicators:
                rows_to_insert.append((
                    indicator["series_id"],  # Using series_id instead of indicator_type
                    indicator["asof_date"],
                    indicator["value"],
                    indicator.get("unit", "index"),
                    indicator.get("source", "FRED"),
                    datetime.utcnow()
                ))
            
            # Execute batch insert
            result = await conn.executemany(insert_query, rows_to_insert)
            logger.info(f"Inserted/updated {len(rows_to_insert)} indicators")
            
            return len(rows_to_insert)
    
    async def process_series(self, series_id: str, indicator_name: str, start_date: date) -> int:
        """Process a single FRED series and store in database."""
        logger.info(f"Processing {series_id} -> {indicator_name}")
        
        # Fetch data from FRED
        observations = await self.fetch_fred_series(series_id, start_date)
        
        if not observations:
            logger.warning(f"No observations found for {series_id}")
            return 0
        
        # Transform to indicator format
        indicators = []
        for obs in observations:
            # Skip missing values
            if obs["value"] == "." or obs["value"] == "":
                continue
                
            try:
                value = float(obs["value"])
                asof_date = datetime.strptime(obs["date"], "%Y-%m-%d").date()
                
                indicators.append({
                    "asof_date": asof_date,
                    "series_id": series_id,  # Using the original FRED series_id which fits in varchar(20)
                    "value": value,
                    "unit": "index",
                    "source": "FRED"
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Error processing observation: {e}")
                continue
        
        # Store in database
        if indicators:
            count = await self.store_indicators(indicators)
            return count
        
        return 0
    
    async def run_ingestion(self, lookback_days: int = 365):
        """Run the full ingestion process."""
        await self.connect_db()
        
        try:
            start_date = date.today() - timedelta(days=lookback_days)
            total_count = 0
            
            logger.info(f"Starting FRED data ingestion from {start_date}")
            logger.info(f"Processing {len(FRED_SERIES_MAPPING)} series")
            
            # Process each series
            for series_id, indicator_name in FRED_SERIES_MAPPING.items():
                count = await self.process_series(series_id, indicator_name, start_date)
                total_count += count
                
                # Rate limiting - be nice to FRED API
                await asyncio.sleep(0.5)
            
            logger.info(f"✅ Ingestion complete! Total indicators stored: {total_count}")
            
            # Verify data in database
            await self.verify_data()
            
        finally:
            await self.disconnect_db()
    
    async def verify_data(self):
        """Verify that data was properly stored."""
        async with self.db_pool.acquire() as conn:
            # Count indicators by series
            query = """
                SELECT 
                    series_id,
                    COUNT(*) as count,
                    MIN(asof_date) as earliest,
                    MAX(asof_date) as latest,
                    AVG(value) as avg_value
                FROM economic_indicators
                GROUP BY series_id
                ORDER BY series_id
            """
            
            rows = await conn.fetch(query)
            
            logger.info("\n📊 Economic Indicators Summary:")
            logger.info("-" * 60)
            for row in rows:
                logger.info(
                    f"{row['series_id']:25s} | "
                    f"Count: {row['count']:5d} | "
                    f"Range: {row['earliest']} to {row['latest']}"
                )
            logger.info("-" * 60)
            
            # Total count
            total_query = "SELECT COUNT(*) FROM economic_indicators"
            total = await conn.fetchval(total_query)
            logger.info(f"Total indicators in database: {total}")

async def main():
    """Main entry point."""
    if not FRED_API_KEY:
        logger.error("❌ FRED_API_KEY not found in environment variables")
        return
    
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL not found in environment variables")
        return
    
    logger.info("🚀 Starting FRED data ingestion...")
    
    ingester = FREDDataIngester(FRED_API_KEY, DATABASE_URL)
    await ingester.run_ingestion(lookback_days=365)  # Get 1 year of data
    
    logger.info("✨ FRED data ingestion complete!")

if __name__ == "__main__":
    asyncio.run(main())