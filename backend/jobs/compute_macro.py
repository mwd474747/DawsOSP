"""
Macro Regime Detection Job

Purpose: Nightly job to fetch indicators from FRED and detect macro regime
Updated: 2025-10-23
Priority: P0 (Critical for risk management)

Schedule: Daily at 00:20 UTC (after market close, before metrics)

Tasks:
    1. Fetch latest macro indicators from FRED API
    2. Compute z-scores with 252-day rolling window
    3. Classify current macro regime (probabilistic)
    4. Store regime snapshot in database
    5. Alert if regime change detected
    6. Backfill historical data if needed

Usage:
    # CLI (manual run)
    python -m backend.jobs.compute_macro --asof-date 2025-10-23

    # Scheduler
    scheduler.add_job(
        compute_macro_regime,
        trigger="cron",
        hour=0,
        minute=20,
    )

Sacred Invariants:
    1. Always fetch from FRED (source of truth)
    2. Store ALL fetched data (audit trail)
    3. Never override historical regime snapshots
    4. Alert on regime transitions (>20pp probability swing)
"""

import asyncio
import logging
import argparse
from datetime import date, datetime, timedelta
from typing import Optional

from app.integrations.fred_provider import FREDProvider
from app.services.macro import get_macro_service, Regime
from app.db.connection import get_db_pool

logger = logging.getLogger("DawsOS.MacroJob")


# ============================================================================
# Job Functions
# ============================================================================


async def fetch_indicators_job(
    asof_date: Optional[date] = None,
    lookback_days: int = 365,
):
    """
    Fetch macro indicators from FRED.

    Args:
        asof_date: Fetch indicators as of this date (default: today)
        lookback_days: Fetch last N days of data (default: 365)
    """
    if asof_date is None:
        asof_date = date.today()

    logger.info(f"Fetching indicators for {asof_date}")

    # Get services
    import os
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        logger.error("FRED_API_KEY not configured")
        return
        
    fred_provider = FREDProvider(api_key=api_key)
    macro_service = get_macro_service(fred_client=fred_provider)

    # Fetch indicators
    try:
        results = await macro_service.fetch_indicators(
            asof_date=asof_date,
            lookback_days=lookback_days,
        )

        total_fetched = sum(len(obs) for obs in results.values())
        logger.info(f"Fetched {total_fetched} total observations across all indicators")

        return results

    except Exception as e:
        logger.error(f"Failed to fetch indicators: {e}", exc_info=True)
        raise


async def detect_regime_job(
    asof_date: Optional[date] = None,
) -> Optional[str]:
    """
    Detect macro regime for a specific date.

    Args:
        asof_date: Detect regime as of this date (default: today)

    Returns:
        Regime name or None if failed
    """
    if asof_date is None:
        asof_date = date.today()

    logger.info(f"Detecting regime for {asof_date}")

    # Get service
    macro_service = get_macro_service()

    try:
        # Detect regime
        classification = await macro_service.detect_regime(asof_date=asof_date)

        logger.info(
            f"Regime detected: {classification.regime_name} "
            f"(confidence: {classification.confidence:.2%})"
        )

        # Log probabilities
        logger.info(f"Regime probabilities:")
        for regime_name, prob in sorted(
            classification.regime_probabilities.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            logger.info(f"  {regime_name}: {prob:.2%}")

        # Log drivers
        logger.info(f"Key drivers:")
        for driver, value in classification.drivers.items():
            logger.info(f"  {driver}: {value}")

        return classification.regime.value

    except Exception as e:
        logger.error(f"Failed to detect regime: {e}", exc_info=True)
        return None


async def check_regime_transition(
    asof_date: date,
    threshold: float = 0.20,
) -> bool:
    """
    Check if regime has transitioned significantly.

    Args:
        asof_date: Current date
        threshold: Probability swing threshold (default: 20%)

    Returns:
        True if regime transition detected
    """
    logger.info(f"Checking for regime transition on {asof_date}")

    macro_service = get_macro_service()

    try:
        # Get current regime
        current = await macro_service.detect_regime(asof_date=asof_date)

        # Get previous regime (1 day ago)
        prev_date = asof_date - timedelta(days=1)
        history = await macro_service.get_regime_history(
            start_date=prev_date,
            end_date=prev_date,
        )

        if not history:
            logger.info("No previous regime data, cannot check transition")
            return False

        previous = history[0]

        # Check if regime changed
        if current.regime != previous.regime:
            logger.warning(
                f"REGIME TRANSITION: {previous.regime.value} → {current.regime.value} "
                f"(confidence: {previous.confidence:.2%} → {current.confidence:.2%})"
            )
            return True

        # Check if probability swung significantly (even if same regime)
        current_prob = current.regime_probabilities.get(current.regime.value, 0.0)
        prev_prob = previous.regime_probabilities.get(current.regime.value, 0.0)
        swing = abs(current_prob - prev_prob)

        if swing > threshold:
            logger.warning(
                f"REGIME PROBABILITY SWING: {current.regime.value} "
                f"({prev_prob:.2%} → {current_prob:.2%}, swing: {swing:.2%})"
            )
            return True

        logger.info("No significant regime transition detected")
        return False

    except Exception as e:
        logger.error(f"Failed to check regime transition: {e}", exc_info=True)
        return False


async def backfill_historical_data(
    start_date: date,
    end_date: date,
):
    """
    Backfill historical indicator data and regime classifications.

    Args:
        start_date: Start date for backfill
        end_date: End date for backfill
    """
    logger.info(f"Backfilling historical data: {start_date} to {end_date}")

    import os
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        logger.error("FRED_API_KEY not configured")
        return
        
    fred_provider = FREDProvider(api_key=api_key)
    macro_service = get_macro_service(fred_client=fred_provider)

    # Fetch historical indicators
    logger.info("Step 1: Fetching historical indicators")
    lookback_days = (end_date - start_date).days + 365  # Extra year for z-scores
    await macro_service.fetch_indicators(
        asof_date=end_date,
        lookback_days=lookback_days,
    )

    # Detect regimes for each day
    logger.info("Step 2: Detecting regimes for each day")
    current_date = start_date
    count = 0

    while current_date <= end_date:
        try:
            await macro_service.detect_regime(asof_date=current_date)
            count += 1

            if count % 10 == 0:
                logger.info(f"Processed {count} days...")

        except Exception as e:
            logger.warning(f"Failed to detect regime for {current_date}: {e}")

        current_date += timedelta(days=1)

    logger.info(f"Backfill complete: processed {count} days")


# ============================================================================
# Main Job
# ============================================================================


async def compute_macro_regime(
    asof_date: Optional[date] = None,
    skip_fetch: bool = False,
):
    """
    Main macro regime detection job.

    Args:
        asof_date: Run job for this date (default: today)
        skip_fetch: Skip FRED fetch (use existing DB data)
    """
    if asof_date is None:
        asof_date = date.today()

    logger.info(f"Starting macro regime job for {asof_date}")

    try:
        # Step 1: Fetch indicators from FRED
        if not skip_fetch:
            logger.info("Step 1: Fetching indicators from FRED")
            await fetch_indicators_job(asof_date=asof_date)
        else:
            logger.info("Step 1: Skipping FRED fetch (using DB data)")

        # Step 2: Detect regime
        logger.info("Step 2: Detecting regime")
        regime = await detect_regime_job(asof_date=asof_date)

        if regime is None:
            logger.error("Regime detection failed")
            return False

        # Step 3: Check for regime transition
        logger.info("Step 3: Checking for regime transition")
        transition_detected = await check_regime_transition(asof_date)

        if transition_detected:
            logger.warning("ALERT: Regime transition detected!")
            # TODO: Send alert notification

        logger.info("Macro regime job completed successfully")
        return True

    except Exception as e:
        logger.error(f"Macro regime job failed: {e}", exc_info=True)
        return False


# ============================================================================
# CLI
# ============================================================================


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Macro Regime Detection Job")
    parser.add_argument(
        "--asof-date",
        type=str,
        help="Run job for this date (YYYY-MM-DD, default: today)",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip FRED fetch (use existing DB data)",
    )
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Backfill historical data",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for backfill (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for backfill (YYYY-MM-DD, default: today)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize DB connection pool
    await get_connection_pool()

    try:
        if args.backfill:
            # Backfill mode
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
            end_date = (
                datetime.strptime(args.end_date, "%Y-%m-%d").date()
                if args.end_date
                else date.today()
            )
            await backfill_historical_data(start_date, end_date)

        else:
            # Regular mode
            asof_date = (
                datetime.strptime(args.asof_date, "%Y-%m-%d").date()
                if args.asof_date
                else None
            )
            success = await compute_macro_regime(
                asof_date=asof_date,
                skip_fetch=args.skip_fetch,
            )
            exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
