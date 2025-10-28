"""
Mark Pack Fresh Job

Purpose: Mark pricing pack as fresh to enable executor API
Updated: 2025-10-26
Priority: P0 (Nightly job orchestration)

Features:
    - Updates pricing_packs.is_fresh = true
    - Updates pricing_packs.prewarm_done = true
    - Changes status from 'warming' to 'fresh'
    - Enables executor API freshness gate

Schedule:
    - Runs at 00:30 (after all prewarm jobs complete)
    - CRITICAL: Executor blocks requests until this completes

Usage:
    # Run manually
    python -m backend.jobs.mark_pack_fresh PP_2025-10-22

    # Run via scheduler
    # (scheduled in backend.jobs.scheduler as JOB 6)
"""

import asyncio
import argparse
import logging
import sys
from typing import Dict, Any

from app.db.connection import get_db_pool, execute_query_one

logger = logging.getLogger("DawsOS.Jobs.MarkPackFresh")


async def mark_pack_fresh(pack_id: str) -> Dict[str, Any]:
    """
    Mark pricing pack as fresh.

    Args:
        pack_id: Pricing pack ID to mark fresh

    Returns:
        Pack status dict with is_fresh, prewarm_done, status
    """
    logger.info(f"=" * 80)
    logger.info(f"MARK PACK FRESH: {pack_id}")
    logger.info(f"=" * 80)

    # Update pricing pack
    update_query = """
        UPDATE pricing_packs
        SET status = 'fresh',
            is_fresh = true,
            prewarm_done = true,
            updated_at = NOW()
        WHERE id = $1
        RETURNING id, status, is_fresh, prewarm_done, updated_at
    """

    result = await execute_query_one(update_query, pack_id)

    if not result:
        logger.error(f"❌ Pack {pack_id} not found")
        raise ValueError(f"Pack {pack_id} not found")

    logger.info(f"✅ Pack {pack_id} marked as fresh")
    logger.info(f"  Status: {result['status']}")
    logger.info(f"  is_fresh: {result['is_fresh']}")
    logger.info(f"  prewarm_done: {result['prewarm_done']}")
    logger.info(f"  Updated: {result['updated_at']}")
    logger.info(f"=" * 80)

    return {
        "pack_id": pack_id,
        "status": result["status"],
        "is_fresh": result["is_fresh"],
        "prewarm_done": result["prewarm_done"],
        "updated_at": result["updated_at"].isoformat(),
    }


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Mark pricing pack as fresh")
    parser.add_argument(
        "pack_id",
        help="Pricing pack ID to mark fresh (e.g., PP_2025-10-22)",
    )
    args = parser.parse_args()

    # Initialize DB
    await get_db_pool()

    # Mark pack fresh
    try:
        result = await mark_pack_fresh(args.pack_id)
        logger.info("✅ Success")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run
    asyncio.run(main())
