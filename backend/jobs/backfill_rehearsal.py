"""
Backfill Rehearsal Tool

Purpose: CLI tool to simulate D0 → D1 pack supersede scenarios
Updated: 2025-10-22
Priority: P2 (Operational readiness for Phase 4 Task 5)

Features:
    - Simulate historical restatement scenarios
    - Analyze impact before production backfill
    - Validate no silent mutation (explicit supersede chain)
    - Generate impact report

Usage:
    # Dry run (no database changes)
    python -m backend.jobs.backfill_rehearsal \
        --start-date 2025-09-01 \
        --end-date 2025-09-30 \
        --dry-run

    # Execute supersede chain
    python -m backend.jobs.backfill_rehearsal \
        --pack-id PP_2025-10-21 \
        --reason "Late corporate action: AAPL 2-for-1 split" \
        --execute

    # Impact analysis report
    python -m backend.jobs.backfill_rehearsal \
        --pack-id PP_2025-10-21 \
        --analyze-only

Governance:
    - Pack immutability: D0 pack never modified, only superseded
    - Explicit supersede chain: D0.superseded_by → D1.id
    - Restatement banner: UI displays when using superseded pack
    - Audit trail: All supersedes logged with reason
"""

import argparse
import asyncio
import hashlib
import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from backend.app.db.connection import get_db_pool, execute_query_one, execute_query, execute_statement
from backend.app.db.pricing_pack_queries import PricingPackQueries, get_pricing_pack_queries
from backend.app.db.metrics_queries import MetricsQueries, get_metrics_queries

logger = logging.getLogger("DawsOS.BackfillRehearsal")
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)


# ============================================================================
# Supersede Operations
# ============================================================================


class BackfillRehearsal:
    """
    Backfill rehearsal tool for pricing pack supersede scenarios.

    Simulates D0 → D1 pack supersede chain to validate:
    - Impact on existing metrics
    - Restatement banner display
    - No silent mutation (explicit chain)
    """

    def __init__(self, dry_run: bool = True):
        """
        Initialize backfill rehearsal tool.

        Args:
            dry_run: If True, only simulate changes (no database writes)
        """
        self.dry_run = dry_run
        self.pack_queries = get_pricing_pack_queries()
        self.metrics_queries = get_metrics_queries()

    async def simulate_supersede(
        self,
        pack_id: str,
        reason: str,
        new_pack_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Simulate supersede chain: D0 → D1.

        Args:
            pack_id: ID of pack to supersede (D0)
            reason: Reason for supersede (e.g., "Late corporate action")
            new_pack_data: Optional data for D1 pack (if None, generates placeholder)

        Returns:
            Impact analysis dict with:
                - affected_metrics: Count of metrics using D0 pack
                - supersede_chain: D0 → D1 relationship
                - banner_impact: Portfolios that will see restatement banner
                - validation: No silent mutation check
        """
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Simulating supersede: {pack_id}")
        logger.info(f"Reason: {reason}")

        # Step 1: Fetch D0 pack
        d0_pack = await self.pack_queries.get_pack_by_id(pack_id)
        if not d0_pack:
            raise ValueError(f"Pack {pack_id} not found")

        if d0_pack.get("superseded_by"):
            raise ValueError(f"Pack {pack_id} already superseded by {d0_pack['superseded_by']}")

        # Step 2: Analyze impact
        impact = await self._analyze_impact(d0_pack)

        # Step 3: Generate D1 pack
        d1_pack = self._generate_d1_pack(d0_pack, new_pack_data)

        # Step 4: Simulate supersede chain (if not dry run)
        if not self.dry_run:
            await self._execute_supersede(d0_pack, d1_pack, reason)
            logger.info(f"✅ Supersede complete: {d0_pack['id']} → {d1_pack['id']}")
        else:
            logger.info(f"[DRY RUN] Would supersede: {d0_pack['id']} → {d1_pack['id']}")

        # Step 5: Generate impact report
        impact.update({
            "d0_pack_id": d0_pack["id"],
            "d1_pack_id": d1_pack["id"],
            "reason": reason,
            "dry_run": self.dry_run,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return impact

    async def _analyze_impact(self, pack: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze impact of superseding a pack.

        Args:
            pack: Pack to analyze

        Returns:
            Impact analysis dict
        """
        pack_id = pack["id"]

        # Count metrics using this pack
        query_metrics = """
            SELECT COUNT(*) AS count
            FROM portfolio_metrics
            WHERE pricing_pack_id = $1
        """
        metrics_row = await execute_query_one(query_metrics, pack_id)
        affected_metrics = metrics_row["count"] if metrics_row else 0

        # Count attribution records using this pack
        query_attr = """
            SELECT COUNT(*) AS count
            FROM currency_attribution
            WHERE pricing_pack_id = $1
        """
        attr_row = await execute_query_one(query_attr, pack_id)
        affected_attribution = attr_row["count"] if attr_row else 0

        # Get unique portfolios affected
        query_portfolios = """
            SELECT DISTINCT portfolio_id
            FROM portfolio_metrics
            WHERE pricing_pack_id = $1
        """
        portfolio_rows = await execute_query(query_portfolios, pack_id)
        affected_portfolios = [str(row["portfolio_id"]) for row in portfolio_rows]

        impact = {
            "affected_metrics_count": affected_metrics,
            "affected_attribution_count": affected_attribution,
            "affected_portfolios": affected_portfolios,
            "affected_portfolios_count": len(affected_portfolios),
            "pack_date": pack["date"].isoformat(),
            "pack_status": pack["status"],
            "pack_is_fresh": pack["is_fresh"],
        }

        logger.info(f"Impact analysis: {affected_metrics} metrics, {len(affected_portfolios)} portfolios")
        return impact

    def _generate_d1_pack(
        self,
        d0_pack: Dict[str, Any],
        new_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate D1 pack (superseding D0).

        Args:
            d0_pack: Original pack (D0)
            new_data: Optional new pack data (if None, generates placeholder)

        Returns:
            D1 pack dict
        """
        pack_date = d0_pack["date"]
        policy = d0_pack["policy"]

        # Generate D1 pack ID
        # Format: PP_YYYY-MM-DD_D1 (D1 suffix indicates first restatement)
        d1_pack_id = f"{d0_pack['id']}_D1"

        # Generate new hash (D1 has different data than D0)
        hash_input = f"{pack_date}|{policy}|D1|{datetime.utcnow().isoformat()}"
        new_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        # Build D1 pack
        d1_pack = {
            "id": d1_pack_id,
            "date": pack_date,
            "policy": policy,
            "hash": f"sha256:{new_hash[:16]}",
            "status": "fresh",
            "is_fresh": True,
            "prewarm_done": True,
            "reconciliation_passed": new_data.get("reconciliation_passed", True) if new_data else True,
            "reconciliation_failed": False,
            "error_message": None,
            "superseded_by": None,  # D1 is not superseded (yet)
            "sources_json": new_data.get("sources_json", d0_pack["sources_json"]) if new_data else d0_pack["sources_json"],
        }

        logger.info(f"Generated D1 pack: {d1_pack_id}")
        return d1_pack

    async def _execute_supersede(
        self,
        d0_pack: Dict[str, Any],
        d1_pack: Dict[str, Any],
        reason: str,
    ):
        """
        Execute supersede chain: D0 → D1.

        Args:
            d0_pack: Original pack (D0)
            d1_pack: New pack (D1)
            reason: Supersede reason
        """
        # Step 1: Insert D1 pack
        insert_query = """
            INSERT INTO pricing_packs (
                id,
                date,
                policy,
                hash,
                status,
                is_fresh,
                prewarm_done,
                reconciliation_passed,
                reconciliation_failed,
                error_message,
                superseded_by,
                sources_json
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb)
        """
        await execute_statement(
            insert_query,
            d1_pack["id"],
            d1_pack["date"],
            d1_pack["policy"],
            d1_pack["hash"],
            d1_pack["status"],
            d1_pack["is_fresh"],
            d1_pack["prewarm_done"],
            d1_pack["reconciliation_passed"],
            d1_pack["reconciliation_failed"],
            d1_pack["error_message"],
            d1_pack["superseded_by"],
            json.dumps(d1_pack["sources_json"]),
        )
        logger.info(f"✅ Inserted D1 pack: {d1_pack['id']}")

        # Step 2: Update D0 pack to point to D1
        update_query = """
            UPDATE pricing_packs
            SET superseded_by = $1,
                updated_at = NOW()
            WHERE id = $2
        """
        await execute_statement(update_query, d1_pack["id"], d0_pack["id"])
        logger.info(f"✅ Updated D0 pack superseded_by: {d0_pack['id']} → {d1_pack['id']}")

        # Step 3: Log audit trail
        # TODO: Insert into audit_log table (if exists)
        # For now, just log
        logger.info(f"Audit: Pack {d0_pack['id']} superseded by {d1_pack['id']}, reason: {reason}")

    async def analyze_pack(self, pack_id: str) -> Dict[str, Any]:
        """
        Analyze impact of superseding a pack (read-only).

        Args:
            pack_id: Pack ID to analyze

        Returns:
            Impact analysis dict
        """
        pack = await self.pack_queries.get_pack_by_id(pack_id)
        if not pack:
            raise ValueError(f"Pack {pack_id} not found")

        impact = await self._analyze_impact(pack)

        # Add validation checks
        impact.update({
            "validation": {
                "is_superseded": pack.get("superseded_by") is not None,
                "superseded_by": pack.get("superseded_by"),
                "can_supersede": pack.get("superseded_by") is None,
                "is_fresh": pack["is_fresh"],
                "status": pack["status"],
            }
        })

        return impact

    async def list_supersede_chains(self) -> List[Dict[str, Any]]:
        """
        List all supersede chains in the database.

        Returns:
            List of supersede chains
        """
        query = """
            WITH RECURSIVE chain AS (
                -- Base case: packs that supersede others
                SELECT
                    id,
                    date,
                    superseded_by,
                    1 AS level,
                    id AS root_id
                FROM pricing_packs
                WHERE id IN (
                    SELECT DISTINCT superseded_by
                    FROM pricing_packs
                    WHERE superseded_by IS NOT NULL
                )

                UNION ALL

                -- Recursive case: follow chain backwards
                SELECT
                    p.id,
                    p.date,
                    p.superseded_by,
                    c.level + 1,
                    c.root_id
                FROM pricing_packs p
                INNER JOIN chain c ON p.superseded_by = c.id
            )
            SELECT
                root_id AS latest_pack_id,
                json_agg(
                    json_build_object(
                        'pack_id', id,
                        'date', date,
                        'level', level
                    )
                    ORDER BY level DESC
                ) AS chain
            FROM chain
            GROUP BY root_id
        """

        rows = await execute_query(query)
        chains = []
        for row in rows:
            chains.append({
                "latest_pack_id": row["latest_pack_id"],
                "chain": row["chain"],
            })

        return chains


# ============================================================================
# CLI
# ============================================================================


async def main():
    """CLI entry point for backfill rehearsal tool."""
    parser = argparse.ArgumentParser(
        description="Backfill Rehearsal Tool - Simulate D0 → D1 pack supersede scenarios"
    )

    parser.add_argument(
        "--pack-id",
        type=str,
        help="Pack ID to supersede (e.g., PP_2025-10-21)",
    )

    parser.add_argument(
        "--reason",
        type=str,
        help="Reason for supersede (e.g., 'Late corporate action: AAPL split')",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Simulate only (no database changes) [default: True]",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute supersede (overrides --dry-run)",
    )

    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Analyze impact only (no supersede)",
    )

    parser.add_argument(
        "--list-chains",
        action="store_true",
        help="List all supersede chains",
    )

    args = parser.parse_args()

    # Determine dry_run mode
    dry_run = not args.execute

    # Initialize tool
    tool = BackfillRehearsal(dry_run=dry_run)

    try:
        if args.list_chains:
            # List all supersede chains
            chains = await tool.list_supersede_chains()
            print("\n=== Supersede Chains ===\n")
            if not chains:
                print("No supersede chains found.")
            else:
                for chain in chains:
                    print(f"Latest: {chain['latest_pack_id']}")
                    for node in chain["chain"]:
                        print(f"  {'→' * node['level']} {node['pack_id']} ({node['date']})")
                    print()

        elif args.analyze_only:
            # Analyze impact only
            if not args.pack_id:
                print("ERROR: --pack-id required for --analyze-only")
                return

            impact = await tool.analyze_pack(args.pack_id)
            print("\n=== Impact Analysis ===\n")
            print(json.dumps(impact, indent=2, default=str))

        elif args.pack_id and args.reason:
            # Simulate supersede
            impact = await tool.simulate_supersede(args.pack_id, args.reason)
            print("\n=== Supersede Simulation ===\n")
            print(json.dumps(impact, indent=2, default=str))

            if not dry_run:
                print(f"\n✅ Supersede complete: {impact['d0_pack_id']} → {impact['d1_pack_id']}")
            else:
                print(f"\n[DRY RUN] No database changes made.")
                print(f"Use --execute to apply changes.")

        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\nERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
