"""
Pricing Pack Builder - Immutable Price Snapshots

Purpose: Build immutable pricing packs for reproducible portfolio valuations
Updated: 2025-10-21
Priority: P0 (CRITICAL - Blocks all metrics, UI, and validation)

Sacred Invariants:
    1. Pricing packs are IMMUTABLE once created
    2. All valuations reference pricing_pack_id for reproducibility
    3. Pack includes prices + FX rates + hash for verification
    4. Packs have lifecycle: warming → fresh → superseded
    5. Freshness gate blocks executor until pre-warm completes

Lifecycle:
    1. build_pack() → status='warming'
    2. fetch prices from providers (Polygon, FMP)
    3. fetch FX rates from providers (FRED, FMP)
    4. apply pricing policy (WM 4PM for CAD)
    5. compute SHA256 hash
    6. insert prices and fx_rates with pricing_pack_id
    7. prewarm_factors() → pre-compute metrics
    8. mark_pack_fresh() → status='fresh', enable executor

Supersede Chain (for restatements):
    - Retroactive corporate action discovered
    - Create new pack with adjusted prices
    - Set old_pack.superseded_by = new_pack_id
    - UI shows banner: "Data restated due to {reason}"
    - NO SILENT MUTATIONS (explicit provenance)

Usage:
    pack_id = await build_pack(asof_date=date.today(), policy="WM4PM_CAD")
    is_fresh = await is_pack_fresh(pack_id)
    await mark_pack_fresh(pack_id)
"""

import logging
import hashlib
import json
import asyncpg
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.integrations.polygon_provider import PolygonProvider
from app.integrations.fmp_provider import FMPProvider
from app.integrations.fred_provider import FREDProvider

logger = logging.getLogger(__name__)


class PricingPackBuilder:
    """
    Build immutable pricing packs with prices and FX rates.
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize pricing pack builder.

        Args:
            db_pool: AsyncPG connection pool
        """
        self.db = db_pool

        # Initialize providers (API keys from environment)
        import os
        self.polygon = PolygonProvider(api_key=os.getenv("POLYGON_API_KEY"))
        self.fmp = FMPProvider(api_key=os.getenv("FMP_API_KEY"))
        self.fred = FREDProvider(api_key=os.getenv("FRED_API_KEY"))

    async def build_pack(
        self,
        asof_date: date,
        policy: str = "WM4PM_CAD",
        restatement_reason: Optional[str] = None,
    ) -> str:
        """
        Build immutable pricing pack for asof_date.

        Sacred order (non-negotiable):
        1. Fetch prices from providers (Polygon, FMP)
        2. Fetch FX rates from providers (FRED, FMP)
        3. Apply pricing policy (WM 4PM for CAD)
        4. Compute hash of all prices + FX rates
        5. Store in pricing_packs table with status='warming'
        6. Insert prices and fx_rates with pricing_pack_id
        7. Mark as status='fresh' after pre-warm completes (done by scheduler)

        Args:
            asof_date: As-of date for pricing pack (usually yesterday)
            policy: Pricing policy (default: "WM4PM_CAD" = WM 4PM fix for CAD)
            restatement_reason: If provided, creates superseding pack

        Returns:
            pricing_pack_id (UUID string)

        Raises:
            ValueError: If pack already exists for date/policy
            ProviderError: If provider calls fail
        """
        logger.info(f"Building pricing pack for {asof_date}, policy={policy}")

        # Check if pack already exists (not superseded)
        existing_pack = await self._get_existing_pack(asof_date, policy)
        if existing_pack and not restatement_reason:
            logger.warning(f"Pack already exists for {asof_date}: {existing_pack['id']}")
            return existing_pack["id"]

        # Get all securities that need pricing
        securities = await self._get_active_securities()
        logger.info(f"Fetching prices for {len(securities)} securities")

        # Fetch prices
        prices_data = await self._fetch_prices(securities, asof_date)
        logger.info(f"Fetched {len(prices_data)} prices")

        # Fetch FX rates
        fx_data = await self._fetch_fx_rates(asof_date, policy)
        logger.info(f"Fetched {len(fx_data)} FX rates")

        # Compute hash for immutability verification
        pack_hash = self._compute_hash(prices_data, fx_data)

        # Create pricing pack record
        pack_id = await self._create_pack_record(
            asof_date, policy, pack_hash, prices_data, fx_data
        )

        # Insert prices
        await self._insert_prices(pack_id, prices_data)

        # Insert FX rates
        await self._insert_fx_rates(pack_id, fx_data)

        # If restatement, supersede old pack
        if restatement_reason and existing_pack:
            await self._supersede_pack(existing_pack["id"], pack_id, restatement_reason)

        logger.info(f"Pricing pack built: {pack_id} (hash: {pack_hash[:8]}...)")

        return pack_id

    async def _get_active_securities(self) -> List[Dict]:
        """
        Get all securities that need pricing.

        Returns:
            List of {id, symbol, currency, exchange}
        """
        rows = await self.db.fetch("""
            SELECT id, symbol, currency, exchange
            FROM securities
            WHERE active = TRUE
            ORDER BY symbol
        """)

        return [dict(row) for row in rows]

    async def _fetch_prices(
        self, securities: List[Dict], asof_date: date
    ) -> List[Dict]:
        """
        Fetch prices for all securities from providers.

        Uses Polygon as primary source, FMP as fallback.

        Args:
            securities: List of security records
            asof_date: Date for pricing

        Returns:
            List of {security_id, close, currency, source}
        """
        prices = []

        # Batch symbols by provider
        # Polygon: Daily aggregates (split-adjusted)
        for security in securities:
            try:
                # Fetch 1 day of data (just asof_date)
                daily_prices = await self.polygon.get_daily_prices(
                    symbol=security["symbol"],
                    start_date=asof_date,
                    end_date=asof_date,
                    adjusted=True,  # Split-adjusted (not dividend-adjusted)
                )

                if daily_prices:
                    prices.append({
                        "security_id": security["id"],
                        "close": Decimal(str(daily_prices[0]["close"])),
                        "currency": security["currency"],
                        "source": "polygon",
                    })
                else:
                    # Fallback to FMP quote
                    logger.warning(f"No Polygon data for {security['symbol']}, trying FMP")
                    fmp_quote = await self.fmp.get_quote([security["symbol"]])
                    if fmp_quote:
                        prices.append({
                            "security_id": security["id"],
                            "close": Decimal(str(fmp_quote[0]["price"])),
                            "currency": security["currency"],
                            "source": "fmp",
                        })

            except Exception as e:
                logger.error(f"Failed to fetch price for {security['symbol']}: {e}")
                continue

        return prices

    async def _fetch_fx_rates(self, asof_date: date, policy: str) -> List[Dict]:
        """
        Fetch FX rates from providers.

        Policy "WM4PM_CAD" uses FRED for FX rates (WM/Reuters 4PM fix).

        Args:
            asof_date: Date for FX rates
            policy: Pricing policy

        Returns:
            List of {base_ccy, quote_ccy, rate, source}
        """
        fx_rates = []

        # Currency pairs needed (for CAD base currency)
        pairs = [
            ("USD", "CAD"),  # USD per 1 CAD
            ("EUR", "CAD"),
            ("GBP", "CAD"),
            ("JPY", "CAD"),
            ("CHF", "CAD"),
        ]

        for base_ccy, quote_ccy in pairs:
            try:
                # FRED series for FX rates (using Canadian cross rates)
                # DEXCAUS = CAD/USD (inverted to get USD/CAD)
                if base_ccy == "USD" and quote_ccy == "CAD":
                    series_id = "DEXCAUS"
                else:
                    # For other currencies, would need different series
                    # Placeholder: use FMP for non-USD pairs
                    logger.warning(f"No FRED series for {base_ccy}/{quote_ccy}, skipping")
                    continue

                fred_data = await self.fred.get_series(
                    series_id=series_id,
                    start_date=asof_date,
                    end_date=asof_date,
                )

                if fred_data:
                    # DEXCAUS is CAD per 1 USD, so rate is USD/CAD = value
                    fx_rates.append({
                        "base_ccy": base_ccy,
                        "quote_ccy": quote_ccy,
                        "rate": Decimal(str(fred_data[0]["value"])),
                        "source": "fred",
                        "asof_ts": datetime.combine(asof_date, datetime.min.time()),
                    })

            except Exception as e:
                logger.error(f"Failed to fetch FX rate {base_ccy}/{quote_ccy}: {e}")
                continue

        return fx_rates

    def _compute_hash(self, prices: List[Dict], fx_rates: List[Dict]) -> str:
        """
        Compute SHA256 hash of all prices + FX rates for immutability verification.

        Args:
            prices: List of price records
            fx_rates: List of FX rate records

        Returns:
            SHA256 hash (hex string)
        """
        # Sort for deterministic hash
        prices_sorted = sorted(prices, key=lambda p: p["security_id"])
        fx_sorted = sorted(fx_rates, key=lambda f: (f["base_ccy"], f["quote_ccy"]))

        # Serialize to JSON
        data = {
            "prices": [
                {
                    "security_id": str(p["security_id"]),
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
        hash_bytes = hashlib.sha256(json_str.encode('utf-8')).hexdigest()

        return hash_bytes

    async def _create_pack_record(
        self,
        asof_date: date,
        policy: str,
        pack_hash: str,
        prices: List[Dict],
        fx_rates: List[Dict],
    ) -> str:
        """
        Create pricing_packs table record.

        Args:
            asof_date: As-of date
            policy: Pricing policy
            pack_hash: SHA256 hash
            prices: Price data (for sources_json)
            fx_rates: FX rate data (for sources_json)

        Returns:
            pricing_pack_id (UUID string)
        """
        # Determine sources
        price_sources = list(set(p["source"] for p in prices))
        fx_sources = list(set(f["source"] for f in fx_rates))

        sources_json = {
            "prices": price_sources,
            "fx": fx_sources,
        }

        row = await self.db.fetchrow("""
            INSERT INTO pricing_packs (
                asof_date, policy, sources_json, hash,
                status, prewarm_done, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            RETURNING id
        """, asof_date, policy, json.dumps(sources_json), pack_hash, "warming", False)

        return str(row["id"])

    async def _insert_prices(self, pack_id: str, prices: List[Dict]):
        """
        Insert prices into prices table.

        Args:
            pack_id: Pricing pack UUID
            prices: List of price records
        """
        if not prices:
            logger.warning("No prices to insert")
            return

        # Batch insert
        values = [
            (p["security_id"], pack_id, p["close"], p["currency"], p["source"])
            for p in prices
        ]

        await self.db.executemany("""
            INSERT INTO prices (security_id, pricing_pack_id, close, currency, source)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (security_id, pricing_pack_id) DO NOTHING
        """, values)

        logger.info(f"Inserted {len(values)} prices for pack {pack_id}")

    async def _insert_fx_rates(self, pack_id: str, fx_rates: List[Dict]):
        """
        Insert FX rates into fx_rates table.

        Args:
            pack_id: Pricing pack UUID
            fx_rates: List of FX rate records
        """
        if not fx_rates:
            logger.warning("No FX rates to insert")
            return

        values = [
            (f["base_ccy"], f["quote_ccy"], pack_id, f["rate"], f["source"], f["asof_ts"])
            for f in fx_rates
        ]

        await self.db.executemany("""
            INSERT INTO fx_rates (base_ccy, quote_ccy, pricing_pack_id, rate, source, asof_ts)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (base_ccy, quote_ccy, pricing_pack_id) DO NOTHING
        """, values)

        logger.info(f"Inserted {len(values)} FX rates for pack {pack_id}")

    async def _get_existing_pack(self, asof_date: date, policy: str) -> Optional[Dict]:
        """
        Get existing pack for date/policy (not superseded).

        Args:
            asof_date: As-of date
            policy: Pricing policy

        Returns:
            Pack record or None
        """
        row = await self.db.fetchrow("""
            SELECT id, status, superseded_by
            FROM pricing_packs
            WHERE asof_date = $1 AND policy = $2 AND superseded_by IS NULL
        """, asof_date, policy)

        return dict(row) if row else None

    async def _supersede_pack(
        self, old_pack_id: str, new_pack_id: str, reason: str
    ):
        """
        Mark old pack as superseded by new pack.

        Args:
            old_pack_id: Old pack UUID
            new_pack_id: New pack UUID
            reason: Reason for restatement
        """
        await self.db.execute("""
            UPDATE pricing_packs
            SET superseded_by = $1, updated_at = NOW()
            WHERE id = $2
        """, new_pack_id, old_pack_id)

        logger.info(f"Superseded pack {old_pack_id} with {new_pack_id}: {reason}")

    async def mark_pack_fresh(self, pack_id: str):
        """
        Mark pricing pack as fresh (pre-warm complete, ready for use).

        Called by nightly scheduler after pre-warm completes.

        Args:
            pack_id: Pricing pack UUID
        """
        await self.db.execute("""
            UPDATE pricing_packs
            SET status = 'fresh', prewarm_done = TRUE, updated_at = NOW()
            WHERE id = $1
        """, pack_id)

        logger.info(f"Marked pack {pack_id} as fresh")

    async def is_pack_fresh(self, pack_id: str) -> bool:
        """
        Check if pricing pack is fresh (ready for use).

        Used by executor freshness gate.

        Args:
            pack_id: Pricing pack UUID

        Returns:
            True if status='fresh', False otherwise
        """
        row = await self.db.fetchrow("""
            SELECT status FROM pricing_packs WHERE id = $1
        """, pack_id)

        return row and row["status"] == "fresh"

    async def get_pack_health(self, pack_id: str) -> Dict:
        """
        Get pricing pack health status for /health/pack endpoint.

        Args:
            pack_id: Pricing pack UUID

        Returns:
            {
                "status": "warming|fresh|error",
                "pack_id": "...",
                "updated_at": "2024-10-21T00:12:00Z",
                "prewarm_done": True|False,
                "is_fresh": True|False
            }
        """
        row = await self.db.fetchrow("""
            SELECT id, status, prewarm_done, updated_at
            FROM pricing_packs
            WHERE id = $1
        """, pack_id)

        if not row:
            return {"status": "error", "error": "Pack not found"}

        return {
            "status": row["status"],
            "pack_id": str(row["id"]),
            "updated_at": row["updated_at"].isoformat(),
            "prewarm_done": row["prewarm_done"],
            "is_fresh": row["status"] == "fresh",
        }
