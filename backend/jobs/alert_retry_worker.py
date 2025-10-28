"""
Alert Retry Worker

Purpose: Retry failed alert deliveries from DLQ with exponential backoff
Updated: 2025-10-27
Priority: P0 (Phase 2 Task 2.4)

Features:
    - Exponential backoff: 5min, 30min, 2hr, 12hr, 24hr
    - Max 5 retry attempts
    - Remove from DLQ after successful delivery
    - Metrics for retry attempts

Usage:
    # Run as scheduled job (cron/systemd)
    python backend/jobs/alert_retry_worker.py

    # Or import and run programmatically
    from backend.jobs.alert_retry_worker import retry_failed_alerts
    await retry_failed_alerts()
"""

import asyncio
import logging
from datetime import datetime, timedelta

from backend.app.services.alert_delivery import AlertDeliveryService
from backend.app.services.notifications import NotificationService
from backend.observability.metrics import get_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("DawsOS.AlertRetryWorker")

# Retry schedule (exponential backoff)
RETRY_SCHEDULE = [
    timedelta(minutes=5),    # Retry 1: 5 minutes
    timedelta(minutes=30),   # Retry 2: 30 minutes
    timedelta(hours=2),      # Retry 3: 2 hours
    timedelta(hours=12),     # Retry 4: 12 hours
    timedelta(hours=24),     # Retry 5: 24 hours
]

MAX_RETRIES = len(RETRY_SCHEDULE)


async def retry_failed_alerts():
    """
    Retry failed alert deliveries from DLQ.

    Fetches failed alerts from DLQ and retries delivery with exponential backoff.
    """
    logger.info("Starting alert retry worker")

    # Initialize services
    delivery_service = AlertDeliveryService(use_db=True)
    notification_service = NotificationService(use_db=True)
    metrics = get_metrics()

    # Get failed alerts
    failed_alerts = await delivery_service.get_failed_alerts(
        max_retry_count=MAX_RETRIES,
        limit=100,
    )

    if not failed_alerts:
        logger.info("No failed alerts to retry")
        return

    logger.info(f"Found {len(failed_alerts)} failed alerts to retry")

    # Retry each alert
    retried_count = 0
    success_count = 0
    skipped_count = 0

    for dlq_record in failed_alerts:
        dlq_id = dlq_record["id"]
        alert_id = dlq_record["alert_id"]
        alert_data = dlq_record["alert_data"]
        retry_count = dlq_record["retry_count"]
        last_retry_at = dlq_record["last_retry_at"]

        # Check if enough time has passed since last retry
        if last_retry_at:
            now = datetime.utcnow()
            time_since_retry = now - last_retry_at.replace(tzinfo=None)
            required_wait = RETRY_SCHEDULE[min(retry_count, len(RETRY_SCHEDULE) - 1)]

            if time_since_retry < required_wait:
                logger.debug(
                    f"Skipping alert {alert_id} (retry {retry_count + 1}): "
                    f"waiting {required_wait - time_since_retry} more"
                )
                skipped_count += 1
                continue

        # Retry delivery
        logger.info(
            f"Retrying alert {alert_id} (attempt {retry_count + 1}/{MAX_RETRIES})"
        )

        try:
            # Extract delivery info
            user_id = alert_data.get("user_id")
            message = alert_data.get("message")
            channels = alert_data.get("channels", {"inapp": True, "email": False})
            alert_name = alert_data.get("name", "Alert")

            # Attempt delivery
            success = await notification_service.send_notification(
                user_id=user_id,
                alert_id=alert_id,
                message=message,
                channels=channels,
                alert_name=alert_name,
            )

            if success:
                # Track successful delivery
                await delivery_service.track_delivery(
                    alert_id=alert_id,
                    alert_data=alert_data,
                    delivery_methods=[k for k, v in channels.items() if v],
                )

                # Remove from DLQ
                await delivery_service.remove_from_dlq(dlq_id)

                logger.info(f"Alert {alert_id} delivered successfully on retry")
                success_count += 1

                # Record metrics
                if metrics:
                    metrics.agent_invocations.labels(
                        agent_name="alert_retry_worker",
                        capability="retry_delivery",
                        status="success",
                    ).inc()

            else:
                # Delivery failed (likely deduplication)
                logger.warning(f"Alert {alert_id} not delivered on retry")

                # Increment retry count
                await delivery_service.increment_retry_count(dlq_id)
                retried_count += 1

        except Exception as e:
            logger.error(f"Failed to retry alert {alert_id}: {e}", exc_info=True)

            # Increment retry count
            await delivery_service.increment_retry_count(dlq_id)
            retried_count += 1

            # Record metrics
            if metrics:
                metrics.agent_invocations.labels(
                    agent_name="alert_retry_worker",
                    capability="retry_delivery",
                    status="error",
                ).inc()

    logger.info(
        f"Alert retry worker finished: "
        f"{success_count} succeeded, {retried_count} retried, {skipped_count} skipped"
    )


if __name__ == "__main__":
    asyncio.run(retry_failed_alerts())
