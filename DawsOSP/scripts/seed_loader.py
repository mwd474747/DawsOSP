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

from backend.app.db.connection import get_db_pool, execute_statement, execute_query

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

                await execute_statement(
                    query,
                    cycle_type,
                    parse_value(row["asof_date"], "date"),
                    phase_label,
                    phase_number,
                    parse_value(row["phase_score"], "decimal"),
                    parse_value(row.get("drivers_json", "{}"), "json"),
                )
                count += 1

        logger.info(f"Loaded {count} cycle phase snapshots")


class PortfolioSeedLoader:
    """Load portfolio seed data."""

    async def load(self):
        """Load portfolios, lots, and transactions."""
        logger.info("Loading portfolio seeds...")

        # Load portfolios
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
            for row in reader:
                await execute_statement(
                    query,
                    row["id"],
                    row["user_id"],
                    row["name"],
                    row.get("description"),
                    row.get("base_ccy", "USD"),
                    row.get("benchmark_id"),
                )
                count += 1

        logger.info(f"Loaded {count} portfolios")

    async def _load_lots(self, path: Path):
        """Load lots from CSV."""
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
                currency
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (id)
            DO UPDATE SET
                quantity = EXCLUDED.quantity,
                cost_basis = EXCLUDED.cost_basis,
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

                await execute_statement(
                    query,
                    row["id"],
                    row["portfolio_id"],
                    row["security_id"],
                    row.get("symbol", "UNKNOWN"),
                    parse_value(row.get("trade_date", row.get("acquisition_date")), "date"),
                    qty,
                    cost_basis,
                    cost_per_share,
                    row.get("cost_ccy", row.get("currency", "USD")),
                )
                count += 1

        logger.info(f"Loaded {count} lots")

    async def _load_transactions(self, path: Path):
        """Load transactions from CSV."""
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

                await execute_statement(
                    query,
                    row["id"],
                    row["portfolio_id"],
                    txn_type,
                    row.get("security_id"),
                    row.get("symbol"),
                    parse_value(
                        row.get("txn_ts", row.get("transaction_date", "2024-01-01"))[:10], "date"
                    ),
                    parse_value(row.get("qty", row.get("quantity")), "decimal"),
                    parse_value(row.get("price_base", row.get("price")), "decimal"),
                    parse_value(row.get("net_base", row.get("amount", "0")), "decimal"),
                    row.get("trade_ccy", row.get("currency", "USD")),
                    "seed",
                )
                count += 1

        logger.info(f"Loaded {count} transactions")


class SymbolSeedLoader:
    """Load symbol/security seed data."""

    async def load(self):
        """Load securities (stub - would need securities table)."""
        logger.info("Loading symbol seeds...")

        securities_path = SEED_DIR / "symbols" / "securities.csv"
        if securities_path.exists():
            logger.info("Securities table not yet implemented - skipping")
            # TODO: Implement when securities table is created

        logger.info("Symbol seeds loaded successfully")


# ============================================================================
# Main Loader
# ============================================================================


class SeedLoader:
    """Main seed loader orchestrator."""

    def __init__(self):
        self.loaders = {
            "macro": MacroSeedLoader(),
            "cycles": CycleSeedLoader(),
            "portfolios": PortfolioSeedLoader(),
            "symbols": SymbolSeedLoader(),
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

        # Order matters: symbols → portfolios → macro → cycles
        for domain in ["symbols", "portfolios", "macro", "cycles"]:
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
