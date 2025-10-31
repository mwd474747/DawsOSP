#!/usr/bin/env python3
"""
Simple metrics computation script that directly connects to database.
Computes TWR from portfolio_daily_values and stores in portfolio_metrics.
"""

import asyncio
import asyncpg
import os
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def compute_metrics_for_portfolio(conn, portfolio_id: str, pack_id: str, asof_date: date):
    """Compute metrics for a single portfolio."""
    
    # Get historical returns from portfolio_daily_values
    returns_query = """
        WITH nav_series AS (
            SELECT 
                valuation_date,
                total_value,
                LAG(total_value) OVER (ORDER BY valuation_date) as prev_value
            FROM portfolio_daily_values
            WHERE portfolio_id = $1::uuid
                AND valuation_date <= $2
                AND valuation_date >= $2 - INTERVAL '365 days'
            ORDER BY valuation_date
        ),
        daily_returns AS (
            SELECT 
                valuation_date,
                CASE 
                    WHEN prev_value > 0 THEN (total_value - prev_value) / prev_value
                    ELSE 0
                END as daily_return
            FROM nav_series
            WHERE prev_value IS NOT NULL
        )
        SELECT 
            COUNT(*) as days,
            AVG(daily_return) as avg_return,
            STDDEV(daily_return) as volatility
        FROM daily_returns
    """
    
    result = await conn.fetchrow(returns_query, UUID(portfolio_id), asof_date)
    
    if not result or result["days"] == 0:
        logger.warning(f"No historical data for portfolio {portfolio_id}")
        return None
    
    days = int(result["days"])
    avg_daily_return = float(result["avg_return"]) if result["avg_return"] else 0
    daily_volatility = float(result["volatility"]) if result["volatility"] else 0
    
    # Calculate period returns
    ytd_query = """
        WITH start_val AS (
            SELECT total_value FROM portfolio_daily_values 
            WHERE portfolio_id = $1::uuid 
                AND valuation_date = DATE_TRUNC('year', $2::date)
            LIMIT 1
        ),
        end_val AS (
            SELECT total_value FROM portfolio_daily_values
            WHERE portfolio_id = $1::uuid 
                AND valuation_date = $2::date
            LIMIT 1
        )
        SELECT 
            (e.total_value - s.total_value) / NULLIF(s.total_value, 0) as ytd_return
        FROM start_val s, end_val e
    """
    
    ytd_result = await conn.fetchrow(ytd_query, UUID(portfolio_id), asof_date)
    ytd_return = float(ytd_result["ytd_return"]) if ytd_result and ytd_result["ytd_return"] else 0
    
    # Simplified metrics
    annual_return = avg_daily_return * 252  # Annualized
    annual_vol = daily_volatility * (252 ** 0.5) if daily_volatility else 0
    sharpe_ratio = annual_return / annual_vol if annual_vol > 0 else 0
    
    # First check if metrics already exist for this date
    check_query = """
        SELECT portfolio_id FROM portfolio_metrics 
        WHERE portfolio_id = $1::uuid AND asof_date = $2
    """
    existing = await conn.fetchrow(check_query, UUID(portfolio_id), asof_date)
    
    if existing:
        # Update existing record
        update_query = """
            UPDATE portfolio_metrics SET
                pricing_pack_id = $3,
                twr_1d = $4,
                twr_ytd = $5,
                twr_1y = $6,
                volatility_1y = $7,
                sharpe_1y = $8,
                max_drawdown_1y = $9,
                portfolio_value_base = $10,
                base_currency = $11,
                created_at = NOW()
            WHERE portfolio_id = $1::uuid AND asof_date = $2
        """
        query = update_query
    else:
        # Insert new record
        insert_query = """
            INSERT INTO portfolio_metrics (
                portfolio_id,
                asof_date,
                pricing_pack_id,
                twr_1d,
                twr_ytd,
                twr_1y,
                volatility_1y,
                sharpe_1y,
                max_drawdown_1y,
                portfolio_value_base,
                base_currency,
                created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
        """
        query = insert_query
    
    # Get current portfolio value
    value_query = """
        SELECT total_value FROM portfolio_daily_values 
        WHERE portfolio_id = $1::uuid 
        ORDER BY valuation_date DESC 
        LIMIT 1
    """
    value_result = await conn.fetchrow(value_query, UUID(portfolio_id))
    current_value = value_result["total_value"] if value_result else Decimal("0")
    
    await conn.execute(
        query,
        UUID(portfolio_id),
        asof_date,
        pack_id,
        Decimal(str(avg_daily_return)),
        Decimal(str(ytd_return)),
        Decimal(str(annual_return)),
        Decimal(str(annual_vol)),
        Decimal(str(sharpe_ratio)),
        Decimal("0"),  # Placeholder for max_drawdown_1y
        current_value,  # portfolio_value_base
        "USD",  # base_currency
    )
    
    logger.info(f"Computed metrics for portfolio {portfolio_id}: "
              f"YTD={ytd_return:.2%}, Annual Vol={annual_vol:.2%}, Sharpe={sharpe_ratio:.2f}")
    
    return {
        "portfolio_id": portfolio_id,
        "ytd_return": ytd_return,
        "annual_return": annual_return,
        "annual_volatility": annual_vol,
        "sharpe_ratio": sharpe_ratio,
        "days_of_data": days
    }


async def main():
    """Main function to compute metrics for all portfolios."""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return
    
    conn = await asyncpg.connect(database_url)
    
    try:
        # Get all portfolios with data in portfolio_daily_values
        portfolios_query = """
            SELECT DISTINCT p.id, p.name, COUNT(pdv.valuation_date) as days
            FROM portfolios p
            INNER JOIN portfolio_daily_values pdv ON pdv.portfolio_id = p.id
            GROUP BY p.id, p.name
            HAVING COUNT(pdv.valuation_date) > 0
        """
        
        portfolios = await conn.fetch(portfolios_query)
        logger.info(f"Found {len(portfolios)} portfolios with daily values")
        
        # Compute metrics for each portfolio
        pack_id = "PP_2025-10-21"  # Use the latest pricing pack
        asof_date = date.today()
        
        for portfolio in portfolios:
            portfolio_id = str(portfolio["id"])
            portfolio_name = portfolio["name"]
            days = portfolio["days"]
            
            logger.info(f"Computing metrics for {portfolio_name} ({days} days of data)")
            
            result = await compute_metrics_for_portfolio(conn, portfolio_id, pack_id, asof_date)
            
            if result:
                logger.info(f"✅ Successfully computed metrics for {portfolio_name}")
            else:
                logger.warning(f"❌ Failed to compute metrics for {portfolio_name}")
        
        logger.info("Metrics computation completed")
        
    except Exception as e:
        logger.error(f"Error computing metrics: {e}", exc_info=True)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())