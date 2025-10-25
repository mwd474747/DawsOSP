"""
Database Seed Loader

Purpose: Load seed data into DawsOS database
Updated: 2025-10-22
Priority: P0 (Foundation)

Features:
    - Idempotent UPSERT operations
    - CSV/JSON seed file support
    - Natural key conflict resolution
    - Transaction safety

Usage:
    python scripts/seed_loader.py --domain macro
    python scripts/seed_loader.py --domain portfolios
    python scripts/seed_loader.py --all
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.db.connection import init_db_pool, get_db_pool, execute_statement, execute_query

logger = logging.getLogger("DawsOS.SeedLoader")
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)

# Seed data directory
SEED_DIR = Path(__file__).parent.parent / "data" / "seeds"


# ============================================================================
# Utility Functions
# ============================================================================


def parse_value(value: str, field_type: str) -> Any:
    """Parse CSV value to appropriate Python type."""
    if value == "" or value.lower() == "null":
        if field_type == "json":
            return {}  # Return empty dict for empty JSON fields
        return None

    if field_type == "int":
        return int(value)
    elif field_type == "float":
        return float(value)
    elif field_type == "decimal":
        return Decimal(value)
    elif field_type == "bool":
        return value.lower() in ("true", "t", "1", "yes")
    elif field_type == "date":
        return datetime.strptime(value, "%Y-%m-%d").date()
    elif field_type == "datetime":
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    elif field_type == "json":
        return json.loads(value)
    else:
        return value  # String


def parse_decimal_optional(value: Optional[str]) -> Optional[Decimal]:
    if value in (None, "", "null"):
        return None
    return Decimal(str(value))


def parse_int_optional(value: Optional[str]) -> Optional[int]:
    if value in (None, "", "null"):
        return None
    try:
        return int(value)
    except ValueError:
        return None


# ============================================================================
# Seed Loaders
# ============================================================================


class MacroSeedLoader:
    """Load macro indicator seed data."""

    async def load(self):
        """Load macro indicators from seed files."""
        logger.info("Loading macro indicator seeds...")

        # Load FRED series catalog
        catalog_path = SEED_DIR / "macro" / "fred_series_catalog.json"
        if catalog_path.exists():
            with open(catalog_path) as f:
                catalog = json.load(f)
                await self._load_fred_catalog(catalog)

        # Load macro indicator values
        indicators_path = SEED_DIR / "macro" / "macro_indicators.csv"
        if indicators_path.exists():
            await self._load_macro_indicators(indicators_path)

        logger.info("Macro indicator seeds loaded successfully")

    async def _load_fred_catalog(self, catalog: Dict):
        """Store FRED series catalog metadata."""
        # This could be stored in a metadata table if needed
        logger.info(f"Loaded {len(catalog.get('series', {}))} FRED series definitions")

    async def _load_macro_indicators(self, path: Path):
        """Load macro indicator values from CSV."""
        query = """
            INSERT INTO macro_indicators (
                indicator_id,
                indicator_name,
                date,
                value,
                units,
                frequency,
                source
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (indicator_id, date)
            DO UPDATE SET
                value = EXCLUDED.value,
                indicator_name = EXCLUDED.indicator_name,
                units = EXCLUDED.units,
                frequency = EXCLUDED.frequency
        """

        count = 0
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                await execute_statement(
                    query,
                    row["indicator_id"],
                    row["indicator_name"],
                    parse_value(row["date"], "date"),
                    parse_value(row["value"], "decimal"),
                    row.get("units"),
                    row.get("frequency"),
                    row.get("source", "FRED"),
                )
                count += 1

        logger.info(f"Loaded {count} macro indicator data points")


class CycleSeedLoader:
    """Load macro cycle seed data."""

    async def load(self):
        """Load cycle definitions and snapshots."""
        logger.info("Loading macro cycle seeds...")

        # Load cycle definitions
        defs_path = SEED_DIR / "macro_cycles" / "macro_cycle_definitions.json"
        if defs_path.exists():
            with open(defs_path) as f:
                defs = json.load(f)
                await self._load_cycle_definitions(defs)

        # Load cycle phase snapshots
        snapshots_path = SEED_DIR / "macro_cycles" / "cycle_phase_snapshots.csv"
        if snapshots_path.exists():
            await self._load_cycle_snapshots(snapshots_path)

        logger.info("Macro cycle seeds loaded successfully")

    async def _load_cycle_definitions(self, defs: Dict):
        """Store cycle definitions metadata."""
        # Store as JSON for now (could be normalized into tables)
        logger.info(f"Loaded {len(defs.get('cycles', []))} cycle definitions")

    async def _load_cycle_snapshots(self, path: Path):
        """Load cycle phase snapshots from CSV."""
        query = """
            INSERT INTO cycle_phases (
                cycle_type,
                date,
                phase,
                phase_number,
                composite_score,
                indicators_json
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (cycle_type, date)
            DO UPDATE SET
                phase = EXCLUDED.phase,
                phase_number = EXCLUDED.phase_number,
                composite_score = EXCLUDED.composite_score,
                indicators_json = EXCLUDED.indicators_json
        """

        count = 0
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map cycle_id to cycle_type
                cycle_id = row["cycle_id"]
                if cycle_id == "short_term_debt":
                    cycle_type = "STDC"
                elif cycle_id == "long_term_debt":
                    cycle_type = "LTDC"
                elif cycle_id == "empire":
                    cycle_type = "EMPIRE"
                else:
                    continue

                # Parse phase_label to get phase_number
                phase_label = row["phase_label"]
                phase_number = 1  # Default, would map from definitions

                # Parse JSON to validate, then convert back to string for JSONB column
                drivers_dict = parse_value(row.get("drivers_json", "{}"), "json")
                drivers_json_str = json.dumps(drivers_dict) if drivers_dict else "{}"

                await execute_statement(
                    query,
                    cycle_type,
                    parse_value(row["asof_date"], "date"),
                    phase_label,
                    phase_number,
                    parse_value(row["phase_score"], "decimal"),
                    drivers_json_str,
                )
                count += 1

        logger.info(f"Loaded {count} cycle phase snapshots")


class PortfolioSeedLoader:
    """Load portfolio seed data."""

    def __init__(self):
        # Cache portfolio_id → user_id mapping for RLS
        self.portfolio_user_map = {}

    async def load(self):
        """Load portfolios, lots, and transactions."""
        logger.info("Loading portfolio seeds...")

        # Load portfolios (and build user_id cache)
        portfolios_path = SEED_DIR / "portfolios" / "portfolios.csv"
        if portfolios_path.exists():
            await self._load_portfolios(portfolios_path)

        # Load lots
        lots_path = SEED_DIR / "portfolios" / "lots.csv"
        if lots_path.exists():
            await self._load_lots(lots_path)

        # Load transactions
        txns_path = SEED_DIR / "portfolios" / "transactions.csv"
        if txns_path.exists():
            await self._load_transactions(txns_path)

        logger.info("Portfolio seeds loaded successfully")

    async def _load_portfolios(self, path: Path):
        """Load portfolios from CSV."""
        from backend.app.db.connection import get_db_connection

        query = """
            INSERT INTO portfolios (
                id,
                user_id,
                name,
                description,
                base_currency,
                benchmark_id
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id)
            DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                base_currency = EXCLUDED.base_currency,
                benchmark_id = EXCLUDED.benchmark_id
        """

        count = 0
        with open(path) as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                logger.info(f"Processing portfolio row {row_num}: id={row.get('id')}, user_id={row.get('user_id')}")

                # Validate required fields
                if not row.get("id") or not row.get("user_id"):
                    logger.warning(f"Skipping row {row_num} with missing id or user_id: {row}")
                    continue

                # Use single connection + transaction for SET + INSERT (RLS requirement)
                async with get_db_connection() as conn:
                    async with conn.transaction():
                        # Set RLS context for this user
                        user_id = row["user_id"]
                        logger.info(f"Setting RLS context: SET app.user_id = '{user_id}'")
                        await conn.execute(f"SET LOCAL app.user_id = '{user_id}'")

                        # Verify setting worked
                        test_val = await conn.fetchval("SELECT current_setting('app.user_id', true)")
                        logger.info(f"RLS context verified: {test_val}")

                        # Insert with RLS context active
                        await conn.execute(
                            query,
                            row["id"],
                            user_id,
                            row["name"],
                            row.get("description") or None,
                            row.get("base_ccy", "USD"),
                            row.get("benchmark_id") or None,
                        )
                        # Cache mapping for RLS in lots/transactions
                        self.portfolio_user_map[row["id"]] = user_id
                        count += 1

        logger.info(f"Loaded {count} portfolios")

    async def _load_lots(self, path: Path):
        """Load lots from CSV."""
        from backend.app.db.connection import get_db_connection

        query = """
            INSERT INTO lots (
                id,
                portfolio_id,
                security_id,
                symbol,
                acquisition_date,
                quantity,
                cost_basis,
                cost_basis_per_share,
                currency,
                qty_original,
                qty_open
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (id)
            DO UPDATE SET
                quantity = EXCLUDED.quantity,
                cost_basis = EXCLUDED.cost_basis,
                qty_open = EXCLUDED.qty_open,
                is_open = true
        """

        count = 0
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                qty = parse_value(row.get("qty_open", row.get("quantity")), "decimal")
                cost_per_share = parse_value(
                    row.get("cost_per_unit_ccy", row.get("cost_basis_per_share")), "decimal"
                )
                cost_basis = qty * cost_per_share if qty and cost_per_share else Decimal("0")

                # RLS: Get user_id from cache and use single connection
                portfolio_id = row["portfolio_id"]
                user_id = self.portfolio_user_map.get(portfolio_id)
                if not user_id:
                    logger.warning(f"Portfolio {portfolio_id} not found in cache, skipping lot")
                    continue

                async with get_db_connection() as conn:
                    async with conn.transaction():
                        # Set RLS context
                        await conn.execute(f"SET LOCAL app.user_id = '{user_id}'")

                        # Insert lot with RLS context active
                        await conn.execute(
                            query,
                            row["id"],
                            portfolio_id,
                            row["security_id"],
                            row.get("symbol", "UNKNOWN"),
                            parse_value(row.get("trade_date", row.get("acquisition_date")), "date"),
                            qty,  # quantity
                            cost_basis,
                            cost_per_share,
                            row.get("cost_ccy", row.get("currency", "USD")),
                            qty,  # qty_original (same as quantity for new lots)
                            qty,  # qty_open (same as quantity for open lots)
                        )
                        count += 1

        logger.info(f"Loaded {count} lots")

    async def _load_transactions(self, path: Path):
        """Load transactions from CSV."""
        from backend.app.db.connection import get_db_connection

        query = """
            INSERT INTO transactions (
                id,
                portfolio_id,
                transaction_type,
                security_id,
                symbol,
                transaction_date,
                quantity,
                price,
                amount,
                currency,
                source
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (id)
            DO NOTHING
        """

        count = 0
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                txn_type = row.get("type", row.get("transaction_type", "BUY")).upper()

                # Parse amount - ensure we use "amount" field value if present
                amount_str = row.get("amount", row.get("net_base", "0"))
                if not amount_str or amount_str == "":
                    amount_str = "0"

                # RLS: Get user_id from cache and use single connection
                portfolio_id = row["portfolio_id"]
                user_id = self.portfolio_user_map.get(portfolio_id)
                if not user_id:
                    logger.warning(f"Portfolio {portfolio_id} not found in cache, skipping transaction")
                    continue

                async with get_db_connection() as conn:
                    async with conn.transaction():
                        # Set RLS context
                        await conn.execute(f"SET LOCAL app.user_id = '{user_id}'")

                        # Insert transaction with RLS context active
                        await conn.execute(
                            query,
                            row["id"],
                            portfolio_id,
                            txn_type,
                            row.get("security_id"),
                            row.get("symbol"),
                            parse_value(
                                row.get("txn_ts", row.get("transaction_date", "2024-01-01"))[:10], "date"
                            ),
                            parse_value(row.get("qty", row.get("quantity", "0")), "decimal"),
                            parse_value(row.get("price_base", row.get("price", "0")), "decimal"),
                            parse_value(amount_str, "decimal"),
                            row.get("trade_ccy", row.get("currency", "USD")),
                            "import",  # Must be 'ledger', 'manual', or 'import'
                        )
                        count += 1

        logger.info(f"Loaded {count} transactions")


class SymbolSeedLoader:
    """Load symbol/security seed data."""

    async def load(self):
        """Load securities from CSV."""
        logger.info("Loading symbol seeds...")

        securities_path = SEED_DIR / "symbols" / "securities.csv"
        if not securities_path.exists():
            logger.warning(f"Securities seed file not found: {securities_path}")
            return

        await self._load_securities(securities_path)
        logger.info("Symbol seeds loaded successfully")

    async def _load_securities(self, path: Path):
        """Load securities from CSV."""
        query = """
            INSERT INTO securities (
                id,
                symbol,
                exchange,
                name,
                trading_currency,
                dividend_currency,
                domicile_country,
                security_type,
                active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (symbol) DO UPDATE SET
                exchange = EXCLUDED.exchange,
                name = EXCLUDED.name,
                trading_currency = EXCLUDED.trading_currency,
                dividend_currency = EXCLUDED.dividend_currency,
                domicile_country = EXCLUDED.domicile_country,
                security_type = EXCLUDED.security_type,
                active = EXCLUDED.active
        """

        count = 0
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                security_id = row.get("id")
                symbol = row.get("symbol")

                if not security_id or not symbol:
                    logger.warning(f"Skipping incomplete security row: {row}")
                    continue

                try:
                    # Convert string UUID to UUID object
                    from uuid import UUID
                    sec_uuid = UUID(security_id)
                except ValueError as e:
                    logger.error(f"Invalid UUID for {symbol}: {security_id} - {e}")
                    continue

                try:
                    await execute_statement(
                        query,
                        sec_uuid,
                        symbol,
                        row.get("exchange", ""),
                        row.get("name", ""),
                        row.get("trading_currency", "USD"),
                        row.get("dividend_currency", row.get("trading_currency", "USD")),
                        row.get("domicile_country", "US"),
                        row.get("type", "equity"),  # CSV uses 'type', DB uses 'security_type'
                        True  # active = true by default
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to insert security {symbol} ({security_id}): {e}")
                    continue

        logger.info(f"Loaded {count} securities")


# ============================================================================
# Main Loader
# ============================================================================

class PricingSeedLoader:
    """Load pricing pack and price seed data."""

    async def load(self):
        prices_dir = SEED_DIR / "prices"

        if not prices_dir.exists():
            logger.info("No prices seed directory found; skipping price seeds")
            return

        logger.info("Loading pricing seeds from %s", prices_dir)
        total_rows = 0

        for csv_file in sorted(prices_dir.glob("*.csv")):
            date_str = csv_file.stem
            try:
                pack_date = date.fromisoformat(date_str)
            except ValueError:
                logger.warning("Skipping prices seed with invalid date name: %s", csv_file.name)
                continue

            pack_id = f"PP_{date_str}"

            try:
                await execute_statement(
                    """
                    INSERT INTO pricing_packs (id, date, policy, hash, status, is_fresh, prewarm_done, reconciliation_passed, sources_json)
                    VALUES ($1, $2, $3, $4, 'fresh', true, true, true, $5::jsonb)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    pack_id,
                    pack_date,
                    "WM4PM_CAD",
                    f"sha256:seed:{date_str}",
                    json.dumps({"seed": True}),  # Convert dict to JSON string
                )
            except Exception as exc:
                logger.error("Failed to insert pricing pack %s: %s", pack_id, exc, exc_info=True)
                continue

            with open(csv_file, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    security_id = row.get("security_id")
                    close = row.get("close")

                    if not security_id or close in (None, "", "null"):
                        logger.warning("Skipping incomplete price row in %s: %s", csv_file.name, row)
                        continue

                    try:
                        security_uuid = UUID(str(security_id))
                    except ValueError:
                        logger.warning("Invalid security_id %s in %s", security_id, csv_file.name)
                        continue

                    try:
                        await execute_statement(
                            """
                            INSERT INTO prices (id, security_id, pricing_pack_id, asof_date, close, open, high, low, volume, currency, source)
                            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                            ON CONFLICT (security_id, pricing_pack_id) DO UPDATE
                            SET close = EXCLUDED.close,
                                open = EXCLUDED.open,
                                high = EXCLUDED.high,
                                low = EXCLUDED.low,
                                volume = EXCLUDED.volume,
                                currency = EXCLUDED.currency,
                                source = EXCLUDED.source
                            """,
                            security_uuid,
                            pack_id,
                            pack_date,
                            Decimal(str(close)),
                            parse_decimal_optional(row.get("open")),
                            parse_decimal_optional(row.get("high")),
                            parse_decimal_optional(row.get("low")),
                            parse_int_optional(row.get("volume")),
                            row.get("currency", "USD"),
                            row.get("source", "seed"),
                        )
                        total_rows += 1
                    except Exception as exc:
                        logger.error(
                            "Failed to upsert price for %s in pack %s: %s",
                            security_uuid,
                            pack_id,
                            exc,
                            exc_info=True,
                        )

        logger.info("Loaded %s price rows from seed files", total_rows)




class SeedLoader:
    """Main seed loader orchestrator."""

    def __init__(self):
        self.loaders = {
            "macro": MacroSeedLoader(),
            "cycles": CycleSeedLoader(),
            "portfolios": PortfolioSeedLoader(),
            "symbols": SymbolSeedLoader(),
            "prices": PricingSeedLoader(),
        }

    async def load_domain(self, domain: str):
        """Load seeds for a specific domain."""
        if domain not in self.loaders:
            raise ValueError(f"Unknown domain: {domain}")

        loader = self.loaders[domain]
        await loader.load()

    async def load_all(self):
        """Load all seed domains in order."""
        logger.info("Loading all seed domains...")

        # Order matters: symbols → portfolios → prices → macro → cycles
        for domain in ["symbols", "portfolios", "prices", "macro", "cycles"]:
            await self.load_domain(domain)

        logger.info("All seed domains loaded successfully")


# ============================================================================
# CLI
# ============================================================================


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DawsOS Database Seed Loader")
    parser.add_argument(
        "--domain",
        choices=["macro", "cycles", "portfolios", "symbols"],
        help="Specific domain to load",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Load all domains",
    )

    args = parser.parse_args()

    if not args.domain and not args.all:
        parser.error("Must specify --domain or --all")

    # Initialize database pool
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos"
    )

    logger.info(f"Initializing database pool: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    try:
        await init_db_pool(database_url)
        logger.info("✅ Database pool initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database pool: {e}")
        sys.exit(1)

    loader = SeedLoader()

    try:
        if args.all:
            await loader.load_all()
        else:
            await loader.load_domain(args.domain)

        logger.info("✅ Seed loading complete")
    except Exception as e:
        logger.error(f"❌ Seed loading failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
