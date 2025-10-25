#!/usr/bin/env python3
"""
Check Database State and Add Metrics Seed Data

Purpose: Verify portfolio_metrics table state and add sample data if empty
Date: 2025-10-24
"""

import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import UUID

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.db.connection import init_db_pool, get_db_pool
from backend.app.db.metrics_queries import get_metrics_queries


async def check_database_state():
    """Check current state of database."""
    print("=" * 80)
    print("DATABASE STATE CHECK")
    print("=" * 80)

    # Initialize database pool
    database_url = "postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos"
    try:
        await init_db_pool(database_url)
        print("✅ Database pool initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database pool: {e}")
        return False

    pool = get_db_pool()

    # Check transactions table
    print("\n1. Checking transactions table...")
    async with pool.acquire() as conn:
        tx_count = await conn.fetchval(
            "SELECT COUNT(*) FROM transactions WHERE portfolio_id = $1",
            UUID("11111111-1111-1111-1111-111111111111")
        )
        print(f"   Transactions: {tx_count} records")

        if tx_count > 0:
            positions = await conn.fetch("""
                SELECT
                    COALESCE(s.symbol, t.symbol) as symbol,
                    SUM(CASE
                        WHEN t.transaction_type = 'BUY' THEN t.quantity
                        WHEN t.transaction_type = 'SELL' THEN -t.quantity
                        ELSE 0
                    END) as qty
                FROM transactions t
                LEFT JOIN securities s ON t.security_id = s.id
                WHERE t.portfolio_id = $1
                  AND t.transaction_type IN ('BUY', 'SELL')
                GROUP BY COALESCE(s.symbol, t.symbol)
                HAVING SUM(CASE
                    WHEN t.transaction_type = 'BUY' THEN t.quantity
                    WHEN t.transaction_type = 'SELL' THEN -t.quantity
                    ELSE 0
                END) > 0
            """, UUID("11111111-1111-1111-1111-111111111111"))

            print(f"   ✅ Positions computed from transactions:")
            for p in positions:
                print(f"      - {p['symbol']}: {p['qty']} shares")

    # Check portfolio_metrics table
    print("\n2. Checking portfolio_metrics table...")
    async with pool.acquire() as conn:
        metrics_count = await conn.fetchval(
            "SELECT COUNT(*) FROM portfolio_metrics WHERE portfolio_id = $1",
            UUID("11111111-1111-1111-1111-111111111111")
        )
        print(f"   Metrics records: {metrics_count}")

        if metrics_count > 0:
            latest = await conn.fetchrow("""
                SELECT asof_date, pricing_pack_id, twr_ytd, sharpe_1y
                FROM portfolio_metrics
                WHERE portfolio_id = $1
                ORDER BY asof_date DESC
                LIMIT 1
            """, UUID("11111111-1111-1111-1111-111111111111"))
            print(f"   ✅ Latest metrics: {latest['asof_date']}, TWR YTD: {latest['twr_ytd']}")
        else:
            print(f"   ❌ No metrics data found - NEED TO ADD SEED DATA")

    # Check pricing_packs table
    print("\n3. Checking pricing_packs table...")
    async with pool.acquire() as conn:
        pack_count = await conn.fetchval("SELECT COUNT(*) FROM pricing_packs")
        print(f"   Pricing packs: {pack_count} records")

        if pack_count > 0:
            latest_pack = await conn.fetchrow("""
                SELECT id, asof_date, is_fresh
                FROM pricing_packs
                ORDER BY asof_date DESC
                LIMIT 1
            """)
            print(f"   Latest pack: {latest_pack['id']}, Fresh: {latest_pack['is_fresh']}")

    print("\n" + "=" * 80)
    return metrics_count == 0  # Return True if need to seed


async def add_seed_metrics():
    """Add sample metrics data for test portfolio."""
    print("\n" + "=" * 80)
    print("ADDING SEED METRICS DATA")
    print("=" * 80)

    portfolio_id = UUID("11111111-1111-1111-1111-111111111111")
    asof_date = date(2025, 10, 23)
    pricing_pack_id = "PP_2025-10-23"

    # Sample metrics data (realistic values)
    metrics = {
        # Time-Weighted Returns
        "twr_1d": Decimal("0.0012"),      # +0.12% daily
        "twr_wtd": Decimal("0.0065"),     # +0.65% week-to-date
        "twr_mtd": Decimal("0.0234"),     # +2.34% month-to-date
        "twr_qtd": Decimal("0.0567"),     # +5.67% quarter-to-date
        "twr_ytd": Decimal("0.0850"),     # +8.50% year-to-date
        "twr_1y": Decimal("0.1240"),      # +12.40% trailing 1 year
        "twr_3y": Decimal("0.2450"),      # +24.50% trailing 3 years (annualized)
        "twr_5y": Decimal("0.4120"),      # +41.20% trailing 5 years (annualized)
        "twr_itd": Decimal("0.5230"),     # +52.30% inception-to-date

        # Sharpe Ratios (risk-adjusted returns)
        "sharpe_30d": Decimal("1.45"),
        "sharpe_90d": Decimal("1.32"),
        "sharpe_1y": Decimal("1.28"),
        "sharpe_3y": Decimal("1.42"),
        "sharpe_5y": Decimal("1.38"),
        "sharpe_itd": Decimal("1.41"),

        # Volatility (annualized)
        "volatility_30d": Decimal("0.1520"),   # 15.20% 30-day vol
        "volatility_90d": Decimal("0.1680"),   # 16.80% 90-day vol
        "volatility_1y": Decimal("0.1750"),    # 17.50% 1-year vol

        # Drawdowns (peak-to-trough)
        "max_drawdown_ytd": Decimal("-0.0850"),   # -8.50% max drawdown YTD
        "max_drawdown_1y": Decimal("-0.1250"),    # -12.50% max drawdown 1Y
        "max_drawdown_3y": Decimal("-0.1850"),    # -18.50% max drawdown 3Y
        "max_drawdown_itd": Decimal("-0.2150"),   # -21.50% max drawdown ITD

        # Portfolio values
        "portfolio_value_base": Decimal("1000000.00"),  # $1M portfolio
        "base_currency": "CAD",

        # Win/loss stats
        "win_rate_1y": Decimal("0.5800"),     # 58% winning days
        "avg_win_1y": Decimal("0.0125"),      # 1.25% average win
        "avg_loss_1y": Decimal("-0.0098"),    # -0.98% average loss
    }

    queries = get_metrics_queries()

    try:
        success = await queries.insert_metrics(
            portfolio_id=portfolio_id,
            asof_date=asof_date,
            pricing_pack_id=pricing_pack_id,
            metrics=metrics
        )

        if success:
            print(f"✅ Successfully inserted metrics for portfolio {portfolio_id}")
            print(f"   As-of Date: {asof_date}")
            print(f"   Pricing Pack: {pricing_pack_id}")
            print(f"   TWR YTD: {metrics['twr_ytd']} (+{float(metrics['twr_ytd'])*100:.2f}%)")
            print(f"   Sharpe 1Y: {metrics['sharpe_1y']}")
            print(f"   Volatility 1Y: {metrics['volatility_1y']} ({float(metrics['volatility_1y'])*100:.2f}%)")
        else:
            print(f"❌ Failed to insert metrics")

    except Exception as e:
        print(f"❌ Error inserting metrics: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 80)


async def main():
    """Main execution."""
    needs_seed = await check_database_state()

    if needs_seed:
        print("\n⚠️  Metrics table is empty - adding seed data...")
        await add_seed_metrics()

        # Verify seed data was added
        print("\n🔍 Verifying seed data...")
        await check_database_state()
    else:
        print("\n✅ Metrics data already exists - no seed needed")


if __name__ == "__main__":
    asyncio.run(main())
