"""
Build Pricing Pack - Stub Implementation

Purpose: Build pricing pack with stub data (for testing before provider integration)
Updated: 2025-10-23
Priority: P0 (Critical for development/testing)

Usage:
    # Build pack for today with stub data
    python backend/jobs/build_pack_stub.py

    # Build pack for specific date
    python backend/jobs/build_pack_stub.py --date 2025-10-21

    # Build pack and mark as fresh immediately
    python backend/jobs/build_pack_stub.py --date 2025-10-21 --mark-fresh

Sacred Invariants:
    1. Stub data is HARDCODED and deterministic
    2. Pack ID format: PP_YYYY-MM-DD
    3. Pack hash is computed from stub data
    4. Status starts as 'warming', marked 'fresh' after pre-warm

Stub Data:
    - 10 securities (AAPL, RY.TO, XIU.TO, VFV.TO, MSFT, GOOGL, TD.TO, XIC.TO, AMZN, ENB.TO)
    - 10 prices (one per security)
    - 5 FX rates (USD/CAD, EUR/CAD, GBP/CAD, CAD/USD, JPY/CAD)
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict
import hashlib
import json

# Add repository root to path for imports
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.db.connection import get_db_pool, execute_statement, execute_query_one
from app.db.pricing_pack_queries import get_pricing_pack_queries

logger = logging.getLogger("DawsOS.BuildPackStub")


# ============================================================================
# Stub Data
# ============================================================================

# Securities (hardcoded UUIDs match schema sample data)
STUB_SECURITIES = [
    {"id": "11111111-1111-1111-1111-111111111111", "symbol": "AAPL", "currency": "USD"},
    {"id": "22222222-2222-2222-2222-222222222222", "symbol": "RY.TO", "currency": "CAD"},
    {"id": "33333333-3333-3333-3333-333333333333", "symbol": "XIU.TO", "currency": "CAD"},
    {"id": "44444444-4444-4444-4444-444444444444", "symbol": "VFV.TO", "currency": "CAD"},
    {"id": "55555555-5555-5555-5555-555555555555", "symbol": "MSFT", "currency": "USD"},
    {"id": "66666666-6666-6666-6666-666666666666", "symbol": "GOOGL", "currency": "USD"},
    {"id": "77777777-7777-7777-7777-777777777777", "symbol": "TD.TO", "currency": "CAD"},
    {"id": "88888888-8888-8888-8888-888888888888", "symbol": "XIC.TO", "currency": "CAD"},
    {"id": "99999999-9999-9999-9999-999999999999", "symbol": "AMZN", "currency": "USD"},
    {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "symbol": "ENB.TO", "currency": "CAD"},
]

# Stub prices (reasonable but hardcoded)
STUB_PRICES = {
    "AAPL": Decimal("185.23"),
    "RY.TO": Decimal("142.56"),
    "XIU.TO": Decimal("37.82"),
    "VFV.TO": Decimal("115.34"),
    "MSFT": Decimal("412.67"),
    "GOOGL": Decimal("168.92"),
    "TD.TO": Decimal("78.45"),
    "XIC.TO": Decimal("35.21"),
    "AMZN": Decimal("178.34"),
    "ENB.TO": Decimal("51.23"),
}

# Stub FX rates
STUB_FX_RATES = [
    {"base": "USD", "quote": "CAD", "rate": Decimal("1.3625")},
    {"base": "EUR", "quote": "CAD", "rate": Decimal("1.4823")},
    {"base": "GBP", "quote": "CAD", "rate": Decimal("1.7245")},
    {"base": "CAD", "quote": "USD", "rate": Decimal("0.7339")},
    {"base": "JPY", "quote": "CAD", "rate": Decimal("0.0091")},
]


# ============================================================================
# Pack Builder (Stub)
# ============================================================================


class StubPackBuilder:
    """Build pricing pack with stub data."""

    def __init__(self):
        """Initialize stub pack builder."""
        self.pack_queries = get_pricing_pack_queries(use_db=True)

    async def build_pack(
        self,
        asof_date: date,
        policy: str = "WM4PM_CAD",
        mark_fresh: bool = False,
    ) -> str:
        """
        Build pricing pack with stub data.

        Args:
            asof_date: As-of date for pack
            policy: Pricing policy (default: WM4PM_CAD)
            mark_fresh: If True, mark pack as fresh immediately

        Returns:
            Pricing pack ID
        """
        logger.info(f"Building stub pricing pack for {asof_date}, policy={policy}")

        # Generate pack ID
        pack_id = f"PP_{asof_date.isoformat()}"

        # Check if pack already exists
        existing = await self._get_existing_pack(pack_id)
        if existing:
            logger.warning(f"Pack {pack_id} already exists")
            return pack_id

        # Build price data
        prices_data = self._build_stub_prices(asof_date)
        logger.info(f"Built {len(prices_data)} stub prices")

        # Build FX data
        fx_data = self._build_stub_fx_rates(asof_date)
        logger.info(f"Built {len(fx_data)} stub FX rates")

        # Compute hash
        pack_hash = self._compute_hash(prices_data, fx_data)
        logger.info(f"Computed pack hash: {pack_hash[:16]}...")

        # Create pack record
        await self._create_pack_record(pack_id, asof_date, policy, pack_hash, mark_fresh)
        logger.info(f"Created pack record: {pack_id}")

        # Insert prices
        await self._insert_prices(pack_id, prices_data)
        logger.info(f"Inserted {len(prices_data)} prices")

        # Insert FX rates
        await self._insert_fx_rates(pack_id, fx_data)
        logger.info(f"Inserted {len(fx_data)} FX rates")

        # Mark as fresh if requested
        if mark_fresh:
            await self.pack_queries.mark_pack_fresh(pack_id)
            logger.info(f"Marked pack {pack_id} as fresh")

        logger.info(f"✅ Stub pack built successfully: {pack_id}")
        return pack_id

    def _build_stub_prices(self, asof_date: date) -> List[Dict]:
        """Build stub price data."""
        prices = []
        for sec in STUB_SECURITIES:
            price = STUB_PRICES.get(sec["symbol"])
            if price:
                prices.append({
                    "security_id": sec["id"],
                    "asof_date": asof_date,
                    "close": price,
                    "currency": sec["currency"],
                    "source": "stub",
                })
        return prices

    def _build_stub_fx_rates(self, asof_date: date) -> List[Dict]:
        """Build stub FX rate data."""
        fx_rates = []
        asof_ts = datetime.combine(asof_date, datetime.min.time().replace(hour=16))
        for fx in STUB_FX_RATES:
            fx_rates.append({
                "base_ccy": fx["base"],
                "quote_ccy": fx["quote"],
                "asof_ts": asof_ts,
                "rate": fx["rate"],
                "source": "stub",
                "policy": "WM4PM_CAD",
            })
        return fx_rates

    def _compute_hash(self, prices: List[Dict], fx_rates: List[Dict]) -> str:
        """Compute SHA256 hash of prices and FX rates."""
        # Sort for deterministic hash
        prices_sorted = sorted(prices, key=lambda p: p["security_id"])
        fx_sorted = sorted(fx_rates, key=lambda f: (f["base_ccy"], f["quote_ccy"]))

        # Serialize to JSON
        data = {
            "prices": [
                {
                    "security_id": p["security_id"],
                    "close": str(p["close"]),
                    "currency": p["currency"],
                }
                for p in prices_sorted
            ],
            "fx_rates": [
                {
                    "base_ccy": f["base_ccy"],
                    "quote_ccy": f["quote_ccy"],
                    "rate": str(f["rate"]),
                }
                for f in fx_sorted
            ],
        }

        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    async def _get_existing_pack(self, pack_id: str) -> bool:
        """Check if pack already exists."""
        query = "SELECT id FROM pricing_packs WHERE id = $1"
        row = await execute_query_one(query, pack_id)
        return row is not None

    async def _create_pack_record(
        self,
        pack_id: str,
        asof_date: date,
        policy: str,
        pack_hash: str,
        mark_fresh: bool,
    ):
        """Create pricing_packs table record."""
        sources_json = json.dumps({"stub": True})

        query = """
            INSERT INTO pricing_packs (
                id, date, policy, hash,
                sources_json,
                status, is_fresh, prewarm_done,
                reconciliation_passed,
                created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """

        status = "fresh" if mark_fresh else "warming"
        is_fresh = mark_fresh
        prewarm_done = mark_fresh

        await execute_statement(
            query,
            pack_id,
            asof_date,
            policy,
            pack_hash,
            sources_json,
            status,
            is_fresh,
            prewarm_done,
            False,  # reconciliation_passed (set by reconcile job)
        )

    async def _insert_prices(self, pack_id: str, prices: List[Dict]):
        """Insert prices into prices table."""
        if not prices:
            return

        query = """
            INSERT INTO prices (
                security_id, pricing_pack_id, asof_date, close, currency, source
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (security_id, pricing_pack_id) DO NOTHING
        """

        for price in prices:
            await execute_statement(
                query,
                price["security_id"],
                pack_id,
                price["asof_date"],
                price["close"],
                price["currency"],
                price["source"],
            )

    async def _insert_fx_rates(self, pack_id: str, fx_rates: List[Dict]):
        """Insert FX rates into fx_rates table."""
        if not fx_rates:
            return

        query = """
            INSERT INTO fx_rates (
                pricing_pack_id, base_ccy, quote_ccy, asof_ts, rate, source, policy
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (base_ccy, quote_ccy, pricing_pack_id) DO NOTHING
        """

        for fx in fx_rates:
            await execute_statement(
                query,
                pack_id,
                fx["base_ccy"],
                fx["quote_ccy"],
                fx["asof_ts"],
                fx["rate"],
                fx["source"],
                fx["policy"],
            )


# ============================================================================
# CLI
# ============================================================================


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build pricing pack with stub data")
    parser.add_argument(
        "--date",
        type=str,
        help="Pack date (YYYY-MM-DD, default: yesterday)",
    )
    parser.add_argument(
        "--policy",
        type=str,
        default="WM4PM_CAD",
        help="Pricing policy (default: WM4PM_CAD)",
    )
    parser.add_argument(
        "--mark-fresh",
        action="store_true",
        help="Mark pack as fresh immediately (skip pre-warm)",
    )
    args = parser.parse_args()

    # Parse date
    if args.date:
        asof_date = date.fromisoformat(args.date)
    else:
        asof_date = date.today() - timedelta(days=1)

    logger.info("=" * 80)
    logger.info("BUILD PRICING PACK (STUB)")
    logger.info("=" * 80)
    logger.info(f"Date: {asof_date}")
    logger.info(f"Policy: {args.policy}")
    logger.info(f"Mark Fresh: {args.mark_fresh}")
    logger.info("=" * 80)

    # Initialize database connection
    await get_db_pool()

    # Build pack
    builder = StubPackBuilder()
    pack_id = await builder.build_pack(
        asof_date=asof_date,
        policy=args.policy,
        mark_fresh=args.mark_fresh,
    )

    logger.info("=" * 80)
    logger.info(f"✅ SUCCESS: Pack built: {pack_id}")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
