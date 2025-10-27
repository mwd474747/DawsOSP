"""
DLQ Replay Job

Purpose: Hourly retry of failed alert notifications from Dead Letter Queue
Updated: 2025-10-23
Priority: P1 (Sprint 3 Week 6)

Features:
    - Pop failed jobs from DLQ (max 100 per run)
    - Retry notification delivery
    - Ack successful retries
    - Nack failed retries (increment retry count)
    - Stop retrying after max attempts (3)

Retry Strategy:
    - Attempt 1: 1 minute after initial failure
    - Attempt 2: 5 minutes after 2nd failure
    - Attempt 3: 30 minutes after 3rd failure
    - After 3 attempts: Mark as permanently failed

Schedule:
    - Runs hourly at :05 (00:05, 01:05, 02:05, ...)
    - Takes 1-2 minutes for ~100 jobs

Usage:
    # Run manually
    python -m backend.jobs.replay_dlq

    # Run via scheduler
    # (scheduled in backend.jobs.scheduler every hour at :05)
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List

from backend.app.services.notifications import NotificationService
from backend.app.services.dlq import DLQService

logger = logging.getLogger("DawsOS.Jobs.ReplayDLQ")


class DLQReplayer:
    """
    DLQ replay job.

    Retries failed notification deliveries from Dead Letter Queue.
    """

    def __init__(self, use_db: bool = True):
        """
        Initialize DLQ replayer.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
        """
        self.use_db = use_db

        # Initialize services
        self.notification_service = NotificationService(use_db=use_db)
        self.dlq_service = DLQService(use_db=use_db)

        logger.info(f"DLQReplayer initialized (use_db={use_db})")

    async def replay_dlq_jobs(
        self,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Replay failed jobs from DLQ.

        Workflow:
        1. Pop batch of jobs from DLQ (max batch_size)
        2. For each job:
            a. Retry notification delivery
            b. If success: ack job
            c. If failure: nack job (increment retry count)
            d. If max attempts reached: mark as permanently failed
        3. Return summary statistics

        Args:
            batch_size: Maximum number of jobs to process

        Returns:
            Summary dict with counts and timing
        """
        logger.info(f"=" * 80)
        logger.info(f"DLQ REPLAY STARTED")
        logger.info(f"=" * 80)

        started_at = datetime.now()

        # Get DLQ stats before processing
        stats_before = await self.dlq_service.get_dlq_stats()
        logger.info(
            f"DLQ stats before: "
            f"pending={stats_before.get('pending', 0)}, "
            f"delivered={stats_before.get('delivered', 0)}, "
            f"failed={stats_before.get('failed', 0)}"
        )

        # Pop jobs from DLQ
        jobs = await self.dlq_service.pop_from_dlq(limit=batch_size)
        logger.info(f"Popped {len(jobs)} jobs from DLQ for retry")

        # Counters
        success_count = 0
        failed_count = 0
        permanent_fail_count = 0

        # Retry each job
        for job in jobs:
            job_id = job["id"]
            alert_id = job["alert_id"]
            user_id = job["user_id"]
            payload = job["payload"]
            retry_count = job["retry_count"]

            logger.info(
                f"Retrying job {job_id} (alert={alert_id}, user={user_id}, "
                f"attempt={retry_count + 1}/3)"
            )

            try:
                # Retry notification delivery
                delivered = await self.notification_service.send_notification(
                    user_id=user_id,
                    alert_id=alert_id,
                    message=payload.get("message", "Alert triggered"),
                    channels=payload.get("channels", {"inapp": True}),
                    alert_name=payload.get("alert_name"),
                )

                if delivered:
                    # Success - ack job
                    await self.dlq_service.ack_dlq_job(job_id)
                    success_count += 1
                    logger.info(f"Job {job_id} delivered successfully on retry")
                else:
                    # Deduplication prevented delivery - ack anyway
                    await self.dlq_service.ack_dlq_job(job_id)
                    success_count += 1
                    logger.info(f"Job {job_id} skipped (deduplication)")

            except Exception as e:
                # Failure - nack job
                logger.error(f"Job {job_id} failed on retry: {e}")

                # Nack (increments retry count)
                await self.dlq_service.nack_dlq_job(job_id, str(e))

                # Check if max retries reached
                if retry_count + 1 >= self.dlq_service.MAX_RETRIES:
                    permanent_fail_count += 1
                    logger.error(
                        f"Job {job_id} permanently failed after "
                        f"{retry_count + 1} attempts"
                    )
                else:
                    failed_count += 1

        # Get DLQ stats after processing
        stats_after = await self.dlq_service.get_dlq_stats()
        logger.info(
            f"DLQ stats after: "
            f"pending={stats_after.get('pending', 0)}, "
            f"delivered={stats_after.get('delivered', 0)}, "
            f"failed={stats_after.get('failed', 0)}"
        )

        # Compute timing
        completed_at = datetime.now()
        duration_seconds = (completed_at - started_at).total_seconds()

        # Build summary
        summary = {
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": duration_seconds,
            "jobs_processed": len(jobs),
            "jobs_succeeded": success_count,
            "jobs_failed": failed_count,
            "jobs_permanent_fail": permanent_fail_count,
            "dlq_pending_before": stats_before.get("pending", 0),
            "dlq_pending_after": stats_after.get("pending", 0),
            "dlq_delivered_before": stats_before.get("delivered", 0),
            "dlq_delivered_after": stats_after.get("delivered", 0),
            "dlq_failed_before": stats_before.get("failed", 0),
            "dlq_failed_after": stats_after.get("failed", 0),
        }

        logger.info(f"=" * 80)
        logger.info(f"DLQ REPLAY COMPLETED")
        logger.info(f"  Duration: {duration_seconds:.2f}s")
        logger.info(f"  Jobs processed: {len(jobs)}")
        logger.info(f"  Jobs succeeded: {success_count}")
        logger.info(f"  Jobs failed (will retry): {failed_count}")
        logger.info(f"  Jobs permanently failed: {permanent_fail_count}")
        logger.info(f"=" * 80)

        return summary


# ===========================
# STANDALONE EXECUTION
# ===========================

async def main():
    """Run DLQ replay job immediately (for testing)."""
    # Get batch size from command line or use default
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    # Initialize replayer
    replayer = DLQReplayer(use_db=True)

    # Run replay
    summary = await replayer.replay_dlq_jobs(batch_size=batch_size)

    # Exit with appropriate code
    if summary["jobs_permanent_fail"] > 0:
        logger.warning(
            f"DLQ replay completed with {summary['jobs_permanent_fail']} permanent failures"
        )
        sys.exit(1)
    else:
        logger.info("DLQ replay completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run
    asyncio.run(main())
