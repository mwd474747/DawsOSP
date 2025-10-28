"""
Alert Delivery Tracking Service

Purpose: Track alert deliveries and manage DLQ for failed alerts
Updated: 2025-10-27
Priority: P0 (Phase 2 Task 2.2)

Features:
    - Delivery tracking (alert_deliveries table)
    - Content-based deduplication (MD5 hash)
    - DLQ insertion for failed deliveries
    - Retry scheduling

Usage:
    from backend.app.services.alert_delivery import AlertDeliveryService

    delivery_svc = AlertDeliveryService()

    # Track successful delivery
    await delivery_svc.track_delivery(
        alert_id="alert-123",
        alert_data={"condition": {...}, "message": "..."},
        delivery_methods=["inapp", "email"],
    )

    # Push to DLQ on failure
    await delivery_svc.push_to_dlq(
        alert_id="alert-123",
        alert_data={"condition": {...}},
        error_message="SMTP connection failed",
    )
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("DawsOS.AlertDelivery")


class AlertDeliveryService:
    """
    Alert delivery tracking service.

    Tracks successful deliveries and manages DLQ for failures.
    """

    def __init__(self, use_db: bool = True):
        """
        Initialize alert delivery service.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
        """
        self.use_db = use_db

        if use_db:
            try:
                from backend.app.db.connection import execute_query_one, execute_statement

                self.execute_query_one = execute_query_one
                self.execute_statement = execute_statement
                logger.info("AlertDeliveryService initialized with database integration")

            except Exception as e:
                logger.warning(
                    f"Failed to initialize database connections: {e}. "
                    "Falling back to stub mode."
                )
                self.use_db = False
        else:
            logger.info("AlertDeliveryService initialized in stub mode")

    def compute_content_hash(self, alert_data: Dict[str, Any]) -> str:
        """
        Compute MD5 hash of alert content for deduplication.

        Args:
            alert_data: Alert data dict

        Returns:
            MD5 hash (hex string)
        """
        # Sort keys for consistent hashing
        content_json = json.dumps(alert_data, sort_keys=True, default=str)
        return hashlib.md5(content_json.encode()).hexdigest()

    async def check_duplicate_delivery(
        self,
        alert_id: str,
        content_hash: str,
        lookback_hours: int = 24,
    ) -> bool:
        """
        Check if alert with same content was recently delivered.

        Args:
            alert_id: Alert ID
            content_hash: Content hash (MD5)
            lookback_hours: How far back to check (default: 24 hours)

        Returns:
            True if duplicate found, False otherwise
        """
        if not self.use_db:
            return False  # Stub: no duplicates

        query = """
            SELECT id
            FROM alert_deliveries
            WHERE alert_id = $1
              AND content_hash = $2
              AND delivered_at > NOW() - INTERVAL '%s hours'
            LIMIT 1
        """ % lookback_hours

        try:
            row = await self.execute_query_one(query, alert_id, content_hash)
            if row:
                logger.debug(
                    f"Duplicate delivery detected for alert {alert_id} "
                    f"(content_hash: {content_hash})"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to check duplicate delivery: {e}")
            # On error, allow delivery (fail open)
            return False

    async def track_delivery(
        self,
        alert_id: str,
        alert_data: Dict[str, Any],
        delivery_methods: List[str],
    ) -> str:
        """
        Track successful alert delivery.

        Args:
            alert_id: Alert ID
            alert_data: Alert data (condition, message, etc.)
            delivery_methods: List of delivery methods used (e.g., ["inapp", "email"])

        Returns:
            Delivery record ID
        """
        if not self.use_db:
            return "stub-delivery-id"

        # Compute content hash
        content_hash = self.compute_content_hash(alert_data)

        # Insert into alert_deliveries
        query = """
            INSERT INTO alert_deliveries (
                alert_id,
                content_hash,
                delivery_methods,
                delivered_at
            ) VALUES (
                $1,
                $2,
                $3::jsonb,
                NOW()
            )
            RETURNING id
        """

        try:
            row = await self.execute_query_one(
                query,
                alert_id,
                content_hash,
                json.dumps(delivery_methods),
            )

            delivery_id = str(row["id"])
            logger.info(
                f"Tracked delivery for alert {alert_id} "
                f"(delivery_id: {delivery_id}, methods: {delivery_methods})"
            )
            return delivery_id

        except Exception as e:
            logger.error(f"Failed to track delivery: {e}")
            raise

    async def push_to_dlq(
        self,
        alert_id: str,
        alert_data: Dict[str, Any],
        error_message: str,
    ) -> str:
        """
        Push failed alert to Dead Letter Queue.

        Args:
            alert_id: Alert ID
            alert_data: Alert data (condition, message, etc.)
            error_message: Error that caused failure

        Returns:
            DLQ record ID
        """
        if not self.use_db:
            logger.warning(f"DLQ (stub): alert {alert_id} failed: {error_message}")
            return "stub-dlq-id"

        # Insert into alert_dlq
        query = """
            INSERT INTO alert_dlq (
                alert_id,
                alert_data,
                error_message,
                retry_count,
                created_at
            ) VALUES (
                $1,
                $2::jsonb,
                $3,
                0,
                NOW()
            )
            RETURNING id
        """

        try:
            row = await self.execute_query_one(
                query,
                alert_id,
                json.dumps(alert_data),
                error_message,
            )

            dlq_id = str(row["id"])
            logger.warning(
                f"Alert {alert_id} pushed to DLQ "
                f"(dlq_id: {dlq_id}, error: {error_message})"
            )
            return dlq_id

        except Exception as e:
            logger.error(f"Failed to push to DLQ: {e}")
            raise

    async def get_failed_alerts(
        self,
        max_retry_count: int = 5,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get failed alerts from DLQ that need retry.

        Args:
            max_retry_count: Maximum retry attempts
            limit: Maximum alerts to return

        Returns:
            List of DLQ records
        """
        if not self.use_db:
            return []

        query = """
            SELECT
                id,
                alert_id,
                alert_data,
                error_message,
                retry_count,
                created_at,
                last_retry_at
            FROM alert_dlq
            WHERE retry_count < $1
            ORDER BY created_at ASC
            LIMIT $2
        """

        try:
            from backend.app.db.connection import execute_query

            rows = await execute_query(query, max_retry_count, limit)

            return [
                {
                    "id": str(row["id"]),
                    "alert_id": row["alert_id"],
                    "alert_data": row["alert_data"],
                    "error_message": row["error_message"],
                    "retry_count": row["retry_count"],
                    "created_at": row["created_at"],
                    "last_retry_at": row["last_retry_at"],
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get failed alerts: {e}")
            return []

    async def increment_retry_count(
        self,
        dlq_id: str,
    ) -> None:
        """
        Increment retry count for DLQ record.

        Args:
            dlq_id: DLQ record ID
        """
        if not self.use_db:
            return

        query = """
            UPDATE alert_dlq
            SET retry_count = retry_count + 1,
                last_retry_at = NOW()
            WHERE id = $1::uuid
        """

        try:
            await self.execute_statement(query, dlq_id)
            logger.debug(f"Incremented retry count for DLQ record {dlq_id}")

        except Exception as e:
            logger.error(f"Failed to increment retry count: {e}")

    async def remove_from_dlq(
        self,
        dlq_id: str,
    ) -> None:
        """
        Remove alert from DLQ after successful delivery.

        Args:
            dlq_id: DLQ record ID
        """
        if not self.use_db:
            return

        query = """
            DELETE FROM alert_dlq
            WHERE id = $1::uuid
        """

        try:
            await self.execute_statement(query, dlq_id)
            logger.info(f"Removed DLQ record {dlq_id} after successful retry")

        except Exception as e:
            logger.error(f"Failed to remove from DLQ: {e}")
