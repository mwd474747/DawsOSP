"""
Dead Letter Queue (DLQ) Service

Purpose: Handle failed alert notifications with retry logic
Updated: 2025-10-23
Priority: P1 (Sprint 3 Week 6)

Features:
    - Push failed jobs to DLQ
    - Pop jobs for retry
    - Exponential backoff (1m, 5m, 30m)
    - Max 3 retry attempts
    - Ack/Nack for success/failure
    - Automatic cleanup after max retries

Retry Strategy:
    - Attempt 0: Immediate (initial failure)
    - Attempt 1: 1 minute delay
    - Attempt 2: 5 minute delay
    - Attempt 3: 30 minute delay
    - After 3 attempts: Mark as failed, stop retrying

DLQ Status Flow:
    pending → retrying → delivered (success)
    pending → retrying → failed (max attempts reached)

Usage:
    from app.services.dlq import DLQService

    dlq_svc = DLQService()

    # Push failed job to DLQ
    await dlq_svc.push_to_dlq(
        alert_id="alert-uuid-here",
        user_id="user-uuid-here",
        payload={"message": "...", "channels": {"email": True}},
        error="SMTP connection timeout"
    )

    # Pop jobs for retry (in hourly job)
    jobs = await dlq_svc.pop_from_dlq(limit=100)
    for job in jobs:
        try:
            # Retry delivery
            await retry_notification(job)
            await dlq_svc.ack_dlq_job(job["id"])
        except Exception as e:
            await dlq_svc.nack_dlq_job(job["id"], str(e))
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID

logger = logging.getLogger("DawsOS.DLQ")


class DLQService:
    """
    Dead Letter Queue service for failed alert notifications.

    Implements retry logic with exponential backoff:
    - Attempt 1: 1 minute delay
    - Attempt 2: 5 minute delay
    - Attempt 3: 30 minute delay
    - After 3 attempts: Mark as failed, stop retrying
    """

    # Retry delays (in minutes) for each attempt
    RETRY_DELAYS = {
        0: 1,   # After 1st failure: 1 minute
        1: 5,   # After 2nd failure: 5 minutes
        2: 30,  # After 3rd failure: 30 minutes
    }

    MAX_RETRIES = 3

    def __init__(self, use_db: bool = True):
        """
        Initialize DLQ service.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
        """
        self.use_db = use_db

        if use_db:
            try:
                from app.db.connection import (
                    execute_query_one,
                    execute_query,
                    execute_statement,
                )

                self.execute_query_one = execute_query_one
                self.execute_query = execute_query
                self.execute_statement = execute_statement
                logger.info("DLQService initialized with database integration")

            except Exception as e:
                logger.warning(
                    f"Failed to initialize database connections: {e}. "
                    "Falling back to stub mode."
                )
                self.use_db = False
        else:
            logger.info("DLQService initialized in stub mode")

    async def push_to_dlq(
        self,
        alert_id: str,
        user_id: str,
        payload: Dict[str, Any],
        error: str,
    ) -> str:
        """
        Push failed notification job to DLQ.

        Args:
            alert_id: Alert UUID
            user_id: User UUID
            payload: Notification payload (message, channels, etc.)
            error: Error message from failure

        Returns:
            DLQ job ID

        Raises:
            Exception: If database insert fails
        """
        logger.warning(
            f"Pushing failed notification to DLQ: "
            f"alert={alert_id}, user={user_id}, error={error}"
        )

        if not self.use_db:
            # Stub: return fake job ID
            return "stub-dlq-job-id"

        # Insert into DLQ table
        query = """
            INSERT INTO dlq (
                alert_id,
                user_id,
                payload,
                error_message,
                retry_count,
                status,
                created_at
            ) VALUES (
                $1::uuid,
                $2::uuid,
                $3::jsonb,
                $4,
                0,
                'pending',
                NOW()
            )
            RETURNING id
        """

        try:
            row = await self.execute_query_one(
                query,
                alert_id,
                user_id,
                payload,
                error,
            )

            job_id = str(row["id"])
            logger.info(f"DLQ job created: {job_id}")
            return job_id

        except Exception as e:
            logger.error(f"Failed to push job to DLQ: {e}")
            raise

    async def pop_from_dlq(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Pop jobs from DLQ for retry.

        Only pops jobs that:
        - Are in 'pending' status
        - Have retry_count < MAX_RETRIES
        - Have waited long enough based on exponential backoff

        Args:
            limit: Maximum number of jobs to pop

        Returns:
            List of DLQ job dicts
        """
        if not self.use_db:
            # Stub: return empty list
            return []

        # Query DLQ table for jobs ready to retry
        # Calculate minimum wait time based on retry_count
        query = """
            WITH retry_delays AS (
                SELECT
                    id,
                    alert_id,
                    user_id,
                    payload,
                    error_message,
                    retry_count,
                    last_retry_at,
                    created_at,
                    CASE retry_count
                        WHEN 0 THEN 1    -- 1 minute after 1st failure
                        WHEN 1 THEN 5    -- 5 minutes after 2nd failure
                        WHEN 2 THEN 30   -- 30 minutes after 3rd failure
                        ELSE 60          -- 60 minutes for any other
                    END AS delay_minutes
                FROM dlq
                WHERE status = 'pending'
                  AND retry_count < $1
            )
            SELECT
                id,
                alert_id,
                user_id,
                payload,
                error_message,
                retry_count,
                last_retry_at,
                created_at
            FROM retry_delays
            WHERE (
                last_retry_at IS NULL
                OR last_retry_at + (delay_minutes || ' minutes')::interval < NOW()
            )
            ORDER BY created_at ASC
            LIMIT $2
        """

        try:
            rows = await self.execute_query(query, self.MAX_RETRIES, limit)

            jobs = [
                {
                    "id": str(row["id"]),
                    "alert_id": str(row["alert_id"]),
                    "user_id": str(row["user_id"]),
                    "payload": row["payload"],
                    "error_message": row["error_message"],
                    "retry_count": row["retry_count"],
                    "last_retry_at": row["last_retry_at"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

            logger.info(f"Popped {len(jobs)} jobs from DLQ for retry")
            return jobs

        except Exception as e:
            logger.error(f"Failed to pop jobs from DLQ: {e}")
            return []

    async def ack_dlq_job(
        self,
        job_id: str,
    ) -> bool:
        """
        Acknowledge successful retry of DLQ job.

        Marks job as 'delivered' and sets delivered_at timestamp.

        Args:
            job_id: DLQ job UUID

        Returns:
            True if acknowledged, False otherwise
        """
        logger.info(f"Acknowledging DLQ job: {job_id}")

        if not self.use_db:
            # Stub: always succeed
            return True

        # Update DLQ table
        query = """
            UPDATE dlq
            SET
                status = 'delivered',
                delivered_at = NOW()
            WHERE id = $1::uuid
              AND status != 'delivered'
        """

        try:
            result = await self.execute_statement(query, job_id)
            updated = int(result.split()[-1]) if result else 0

            if updated > 0:
                logger.info(f"DLQ job acknowledged: {job_id}")
                return True
            else:
                logger.warning(f"DLQ job not found or already acknowledged: {job_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to acknowledge DLQ job: {e}")
            return False

    async def nack_dlq_job(
        self,
        job_id: str,
        error: str,
    ) -> bool:
        """
        Negative acknowledge failed retry of DLQ job.

        Increments retry_count and updates error_message.
        If retry_count >= MAX_RETRIES, marks job as 'failed'.

        Args:
            job_id: DLQ job UUID
            error: Error message from retry failure

        Returns:
            True if nack'd, False otherwise
        """
        logger.warning(f"Nack'ing DLQ job: {job_id}, error: {error}")

        if not self.use_db:
            # Stub: always succeed
            return True

        # Update DLQ table
        # Increment retry_count and check if max retries reached
        query = """
            UPDATE dlq
            SET
                retry_count = retry_count + 1,
                last_retry_at = NOW(),
                error_message = $2,
                status = CASE
                    WHEN retry_count + 1 >= $3 THEN 'failed'
                    ELSE 'pending'
                END
            WHERE id = $1::uuid
              AND status != 'delivered'
            RETURNING retry_count, status
        """

        try:
            row = await self.execute_query_one(query, job_id, error, self.MAX_RETRIES)

            if row:
                retry_count = row["retry_count"]
                status = row["status"]

                if status == "failed":
                    logger.error(
                        f"DLQ job failed permanently after {retry_count} attempts: {job_id}"
                    )
                else:
                    logger.info(
                        f"DLQ job nack'd (attempt {retry_count}/{self.MAX_RETRIES}): {job_id}"
                    )

                return True
            else:
                logger.warning(f"DLQ job not found or already delivered: {job_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to nack DLQ job: {e}")
            return False

    async def get_dlq_stats(self) -> Dict[str, int]:
        """
        Get DLQ statistics.

        Returns:
            Dict with counts by status
        """
        if not self.use_db:
            # Stub: return zeros
            return {
                "pending": 0,
                "retrying": 0,
                "delivered": 0,
                "failed": 0,
                "total": 0,
            }

        # Query DLQ table for status counts
        query = """
            SELECT
                status,
                COUNT(*) AS count
            FROM dlq
            GROUP BY status
        """

        try:
            rows = await self.execute_query(query)

            stats = {row["status"]: row["count"] for row in rows}

            # Add total
            stats["total"] = sum(stats.values())

            return stats

        except Exception as e:
            logger.error(f"Failed to get DLQ stats: {e}")
            return {"pending": 0, "retrying": 0, "delivered": 0, "failed": 0, "total": 0}

    async def cleanup_old_jobs(
        self,
        days: int = 30,
    ) -> int:
        """
        Cleanup old DLQ jobs.

        Removes jobs older than specified days that are either:
        - Delivered (successfully retried)
        - Failed (max retries reached)

        Args:
            days: Number of days to keep jobs

        Returns:
            Number of jobs deleted
        """
        logger.info(f"Cleaning up DLQ jobs older than {days} days")

        if not self.use_db:
            # Stub: return 0
            return 0

        # Delete old jobs
        query = """
            DELETE FROM dlq
            WHERE status IN ('delivered', 'failed')
              AND created_at < NOW() - ($1 || ' days')::interval
        """

        try:
            result = await self.execute_statement(query, days)
            deleted = int(result.split()[-1]) if result else 0

            logger.info(f"Cleaned up {deleted} old DLQ jobs")
            return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup DLQ jobs: {e}")
            return 0

    def calculate_next_retry_time(
        self,
        retry_count: int,
        last_retry_at: Optional[datetime],
    ) -> datetime:
        """
        Calculate next retry time based on exponential backoff.

        Args:
            retry_count: Current retry count
            last_retry_at: Last retry timestamp

        Returns:
            Next retry timestamp
        """
        if last_retry_at is None:
            last_retry_at = datetime.utcnow()

        # Get delay for this retry count
        delay_minutes = self.RETRY_DELAYS.get(retry_count, 60)

        next_retry_time = last_retry_at + timedelta(minutes=delay_minutes)
        return next_retry_time
