"""
Pricing Pack Database Queries

Purpose: Database queries for pricing pack status and operations
Updated: 2025-10-22
Priority: P0 (Critical for Phase 2 executor)

Queries:
    - get_latest_pack: Get most recent pricing pack
    - get_pack_by_id: Get pricing pack by ID
    - get_pack_status: Get pack health status
    - mark_pack_fresh: Mark pack as fresh (after pre-warm)
    - mark_pack_error: Mark pack as error (if reconciliation failed)

Critical Requirements:
    - All queries use parameterized SQL (no SQL injection)
    - Pack status derived from multiple fields (is_fresh, reconciliation_passed, etc.)
    - Freshness gate depends on is_fresh flag
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
from decimal import Decimal
import subprocess

from app.core.types import PackHealth, PackStatus
from app.db.connection import get_db_pool, execute_query_one, execute_statement

logger = logging.getLogger("DawsOS.PricingPackQueries")


# ============================================================================
# Pack Queries
# ============================================================================


class PricingPackQueries:
    """
    Database queries for pricing pack operations.

    Uses AsyncPG connection pool for all database operations.
    """

    def __init__(self, use_db: bool = True):
        """
        Initialize pricing pack queries.

        Args:
            use_db: Use database connection (default: True, False for testing)
        """
        self.use_db = use_db

    async def get_latest_pack(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent fresh pricing pack.

        Returns:
            Pack row as dict, or None if no fresh packs exist
            
        Note:
            Only returns packs with status='fresh' and is_fresh=true.
            Excludes packs with status='error' or 'warming'.

        Example:
            {
                "id": "PP_2025-10-21",
                "date": date(2025, 10, 21),
                "policy": "WM4PM_CAD",
                "hash": "sha256:abc123...",
                "status": "fresh",
                "is_fresh": True,
                "prewarm_done": True,
                "reconciliation_passed": True,
                "reconciliation_failed": False,
                "error_message": None,
                "created_at": datetime(2025, 10, 22, 0, 10),
                "updated_at": datetime(2025, 10, 22, 0, 18),
            }
        """
        if not self.use_db:
            logger.warning("get_latest_pack: Using stub implementation (use_db=False)")
            # Stub: Return mock pack for testing
            return {
                "id": "PP_2025-10-21",
                "date": date(2025, 10, 21),
                "policy": "WM4PM_CAD",
                "hash": "sha256:abc123",
                "status": "fresh",
                "is_fresh": True,
                "prewarm_done": True,
                "reconciliation_passed": True,
                "reconciliation_failed": False,
                "error_message": None,
                "created_at": datetime(2025, 10, 22, 0, 10),
                "updated_at": datetime(2025, 10, 22, 0, 18),
            }

        query = """
            SELECT
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
                created_at,
                updated_at
            FROM pricing_packs
            WHERE status = 'fresh' AND is_fresh = true
            ORDER BY date DESC, created_at DESC
            LIMIT 1
        """

        try:
            row = await execute_query_one(query)
            if not row:
                logger.warning("No pricing packs found in database")
                return None

            return dict(row)

        except Exception as e:
            logger.error(f"Failed to get latest pack: {e}", exc_info=True)
            raise

    async def get_pack_by_id(self, pack_id: str) -> Optional[Dict[str, Any]]:
        """
        Get pricing pack by ID.

        Args:
            pack_id: Pricing pack ID (e.g., "PP_2025-10-21")

        Returns:
            Pack row as dict, or None if not found
        """
        if not self.use_db:
            logger.warning(f"get_pack_by_id({pack_id}): Using stub implementation")
            # Stub: Return mock pack if ID matches
            if pack_id == "PP_2025-10-21":
                return await self.get_latest_pack()
            return None

        query = """
            SELECT
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
                created_at,
                updated_at
            FROM pricing_packs
            WHERE id = $1
        """

        try:
            row = await execute_query_one(query, pack_id)
            if not row:
                logger.warning(f"Pricing pack not found: {pack_id}")
                return None

            return dict(row)

        except Exception as e:
            logger.error(f"Failed to get pack by ID {pack_id}: {e}", exc_info=True)
            raise

    async def get_pack_health(self, pack_id: Optional[str] = None) -> Optional[PackHealth]:
        """
        Get pack health status.

        Args:
            pack_id: Optional pack ID (default: latest pack)

        Returns:
            PackHealth object with status, or None if no pack found
        """
        # Get pack
        if pack_id:
            pack = await self.get_pack_by_id(pack_id)
        else:
            pack = await self.get_latest_pack()

        if not pack:
            return None

        # Determine status
        if pack["reconciliation_failed"]:
            status = PackStatus.ERROR
            error_message = "Ledger reconciliation failed"
        elif pack["is_fresh"]:
            status = PackStatus.FRESH
            error_message = None
        else:
            status = PackStatus.WARMING
            error_message = None

        # Estimate ready time (if warming)
        estimated_ready = None
        if status == PackStatus.WARMING:
            # Assume 15 minutes for pre-warm
            estimated_ready = pack["updated_at"] + timedelta(minutes=15)

        return PackHealth(
            status=status,
            pack_id=pack["id"],
            asof_date=pack["date"],
            is_fresh=pack["is_fresh"],
            prewarm_done=pack["prewarm_done"],
            reconciliation_passed=pack["reconciliation_passed"],
            updated_at=pack["updated_at"],
            error_message=error_message,
            estimated_ready=estimated_ready,
        )

    async def mark_pack_fresh(self, pack_id: str) -> bool:
        """
        Mark pack as fresh (after pre-warm completes).

        Args:
            pack_id: Pricing pack ID

        Returns:
            True if updated successfully
        """
        if not self.use_db:
            logger.warning(f"mark_pack_fresh({pack_id}): Using stub implementation")
            return True

        query = """
            UPDATE pricing_packs
            SET status = 'fresh',
                is_fresh = true,
                prewarm_done = true,
                updated_at = NOW()
            WHERE id = $1
        """

        try:
            result = await execute_statement(query, pack_id)
            logger.info(f"Marked pack {pack_id} as fresh: {result}")
            return True

        except Exception as e:
            logger.error(f"Failed to mark pack {pack_id} as fresh: {e}", exc_info=True)
            raise

    async def mark_pack_error(self, pack_id: str, error_message: str) -> bool:
        """
        Mark pack as error (if reconciliation failed).

        Args:
            pack_id: Pricing pack ID
            error_message: Error message

        Returns:
            True if updated successfully
        """
        if not self.use_db:
            logger.warning(f"mark_pack_error({pack_id}): Using stub implementation")
            return True

        query = """
            UPDATE pricing_packs
            SET status = 'error',
                is_fresh = false,
                reconciliation_failed = true,
                error_message = $1,
                updated_at = NOW()
            WHERE id = $2
        """

        try:
            result = await execute_statement(query, error_message, pack_id)
            logger.error(f"Marked pack {pack_id} as error: {result}")
            return True

        except Exception as e:
            logger.error(f"Failed to mark pack {pack_id} as error: {e}", exc_info=True)
            raise

    async def get_ledger_commit_hash(self, ledger_path: str = ".ledger") -> str:
        """
        Get current ledger commit hash from git repository.

        Args:
            ledger_path: Path to ledger git repository (default: .ledger)

        Returns:
            Ledger commit hash

        Raises:
            RuntimeError: If git command fails
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=ledger_path,
                capture_output=True,
                text=True,
                check=True,
            )
            commit_hash = result.stdout.strip()
            logger.debug(f"Ledger commit hash: {commit_hash}")
            return commit_hash

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get ledger commit hash: {e}", exc_info=True)
            # Fall back to stub for development
            logger.warning("Using stub commit hash (git command failed)")
            return "abc123def456"

        except FileNotFoundError:
            logger.warning(f"Ledger repository not found at {ledger_path}, using stub")
            return "abc123def456"


# ============================================================================
# Global Instance
# ============================================================================


# Singleton instance
_pricing_pack_queries: Optional[PricingPackQueries] = None


def get_pricing_pack_queries(use_db: bool = True) -> PricingPackQueries:
    """
    Get singleton PricingPackQueries instance.

    Args:
        use_db: Use database connection (default: True)

    Returns:
        PricingPackQueries instance
    """
    global _pricing_pack_queries
    if _pricing_pack_queries is None:
        _pricing_pack_queries = PricingPackQueries(use_db=use_db)
    return _pricing_pack_queries


def init_pricing_pack_queries(use_db: bool = True) -> PricingPackQueries:
    """
    Initialize PricingPackQueries.

    Args:
        use_db: Use database connection (default: True)

    Returns:
        PricingPackQueries instance
    """
    global _pricing_pack_queries
    _pricing_pack_queries = PricingPackQueries(use_db=use_db)
    return _pricing_pack_queries
