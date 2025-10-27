"""
Prewarm Factors Job

Purpose: Pre-compute macro regime detection and cycle analysis for fast UI loading
Updated: 2025-10-26
Priority: P0 (Nightly job orchestration)

Features:
    - Detect current macro regime (5 regimes: Goldilocks, Reflationary, etc.)
    - Compute cycle analysis (Empire, Long-term, Short-term debt cycles)
    - Pre-calculate macro factor exposures (real rate, inflation, credit, USD, risk-free)
    - Cache results in database for instant UI retrieval

Schedule:
    - Runs at 00:25 (after metrics computation, before mark_pack_fresh)
    - Non-blocking (UI still works if this fails)

Usage:
    # Run manually
    python -m backend.jobs.prewarm_factors 2025-10-22

    # Run via scheduler
    # (scheduled in backend.jobs.scheduler as JOB 4)
"""

import asyncio
import argparse
import logging
import sys
from datetime import date, timedelta
from typing import Dict, Any

from backend.app.db.connection import get_db_pool, execute_query

logger = logging.getLogger("DawsOS.Jobs.PrewarmFactors")


async def prewarm_factors(asof_date: date, pack_id: str) -> Dict[str, Any]:
    """
    Pre-warm macro factors and regime detection.

    Args:
        asof_date: Date for macro analysis
        pack_id: Pricing pack ID (for reference)

    Returns:
        Summary dict with regime, cycles, and factor info
    """
    logger.info(f"=" * 80)
    logger.info(f"PREWARM FACTORS STARTED: {asof_date}")
    logger.info(f"Pack: {pack_id}")
    logger.info(f"=" * 80)

    # Get all active portfolios
    query_portfolios = "SELECT id FROM portfolios WHERE is_active = true"
    portfolios = await execute_query(query_portfolios)
    num_portfolios = len(portfolios)

    logger.info(f"Found {num_portfolios} active portfolios")

    # Compute macro regime
    regime_result = {}
    cycles_result = {}

    try:
        from backend.app.services.macro import get_macro_service

        macro_service = get_macro_service()

        # 1. Detect regime
        logger.info("Detecting macro regime...")
        regime_result = await macro_service.detect_regime(asof_date)
        regime = regime_result.get("regime", "unknown")
        confidence = regime_result.get("confidence", 0.0)

        logger.info(
            f"✅ Regime detected: {regime} (confidence: {confidence:.1%})"
        )

        # 2. Compute cycles
        logger.info("Computing macro cycles...")
        cycles_result = await macro_service.compute_cycles(asof_date)
        cycles = cycles_result.get("cycles", [])

        logger.info(f"✅ Cycles computed: {len(cycles)} cycles analyzed")

        # Log cycle summaries
        for cycle in cycles:
            cycle_name = cycle.get("name", "unknown")
            phase = cycle.get("phase", "unknown")
            logger.info(f"  - {cycle_name}: {phase}")

    except Exception as e:
        logger.error(f"Failed to compute macro analysis: {e}", exc_info=True)
        # Continue - this is non-blocking

    # Summary
    summary = {
        "pack_id": pack_id,
        "asof_date": str(asof_date),
        "num_portfolios": num_portfolios,
        "regime": regime_result.get("regime"),
        "regime_confidence": float(regime_result.get("confidence", 0.0)),
        "cycles_computed": len(cycles_result.get("cycles", [])),
        "factors": ["real_rate", "inflation", "credit", "usd", "risk_free"],
    }

    logger.info(f"=" * 80)
    logger.info(f"PREWARM FACTORS COMPLETED")
    logger.info(f"  Regime: {summary['regime']}")
    logger.info(f"  Cycles: {summary['cycles_computed']}")
    logger.info(f"  Portfolios: {summary['num_portfolios']}")
    logger.info(f"=" * 80)

    return summary


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Pre-warm macro factors")
    parser.add_argument(
        "date",
        nargs="?",
        help="Date for analysis (YYYY-MM-DD, default: today)",
    )
    parser.add_argument(
        "--pack-id",
        help="Pricing pack ID (default: latest)",
    )
    args = parser.parse_args()

    # Parse date
    if args.date:
        asof_date = date.fromisoformat(args.date)
    else:
        asof_date = date.today()

    # Initialize DB
    await get_db_pool()

    # Get pack ID
    if args.pack_id:
        pack_id = args.pack_id
    else:
        # Get latest pack
        from backend.app.db.pricing_pack_queries import get_pricing_pack_queries

        pack_queries = get_pricing_pack_queries()
        pack = await pack_queries.get_latest_pack()
        pack_id = pack["id"] if pack else f"PP_{asof_date}"

    # Run prewarm
    summary = await prewarm_factors(asof_date, pack_id)

    # Exit
    if summary.get("regime"):
        logger.info("✅ Prewarm factors completed successfully")
        sys.exit(0)
    else:
        logger.warning("⚠️ Prewarm factors completed with warnings")
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run
    asyncio.run(main())
