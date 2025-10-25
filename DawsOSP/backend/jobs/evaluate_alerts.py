"""
Alert Evaluation Job

Purpose: Nightly evaluation of user-defined alert conditions
Updated: 2025-10-23
Priority: P1 (Sprint 3 Week 6)

Features:
    - Load all active alerts from database
    - Evaluate conditions against current metrics
    - Check cooldown periods
    - Send notifications (with deduplication)
    - Push failed deliveries to DLQ
    - Update last_fired_at timestamps

Schedule:
    - Runs at 00:35 (after metrics computation at 00:30)
    - Takes 5-10 minutes for ~1000 alerts

Sacred Order Integration:
    - Runs AFTER compute_daily_metrics (00:30)
    - Uses fresh pricing pack and metrics
    - Deduplication prevents spam (max 1 per user/alert/day)

Usage:
    # Run manually
    python -m backend.jobs.evaluate_alerts 2025-10-22

    # Run via scheduler
    # (scheduled in backend.jobs.scheduler at 00:35)
"""

import asyncio
import logging
import sys
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID

from backend.app.services.alerts import AlertService
from backend.app.services.notifications import NotificationService
from backend.app.services.dlq import DLQService

logger = logging.getLogger("DawsOS.Jobs.EvaluateAlerts")


class AlertEvaluator:
    """
    Alert evaluation job.

    Evaluates all active alerts and sends notifications.
    """

    def __init__(self, use_db: bool = True):
        """
        Initialize alert evaluator.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
        """
        self.use_db = use_db

        # Initialize services
        self.alert_service = AlertService(use_db=use_db)
        self.notification_service = NotificationService(use_db=use_db)
        self.dlq_service = DLQService(use_db=use_db)

        if use_db:
            try:
                from backend.app.db.connection import (
                    execute_query,
                    execute_statement,
                )

                self.execute_query = execute_query
                self.execute_statement = execute_statement
                logger.info("AlertEvaluator initialized with database integration")

            except Exception as e:
                logger.warning(
                    f"Failed to initialize database connections: {e}. "
                    "Falling back to stub mode."
                )
                self.use_db = False
        else:
            logger.info("AlertEvaluator initialized in stub mode")

    async def evaluate_all_alerts(
        self,
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate all active alerts.

        Workflow:
        1. Load all active alerts from database
        2. For each alert:
            a. Build evaluation context (asof_date, portfolio_id, etc.)
            b. Evaluate condition
            c. Check cooldown
            d. If triggered: send notification (with deduplication)
            e. If failed: push to DLQ
            f. Update last_fired_at timestamp
        3. Return summary statistics

        Args:
            asof_date: Date for evaluation (default: today)

        Returns:
            Summary dict with counts and timing
        """
        if asof_date is None:
            asof_date = date.today()

        logger.info(f"=" * 80)
        logger.info(f"ALERT EVALUATION STARTED: {asof_date}")
        logger.info(f"=" * 80)

        started_at = datetime.now()

        # Load all active alerts
        alerts = await self._load_active_alerts()
        logger.info(f"Loaded {len(alerts)} active alerts")

        # Counters
        evaluated_count = 0
        triggered_count = 0
        delivered_count = 0
        failed_count = 0
        skipped_count = 0

        # Evaluate each alert
        for alert in alerts:
            try:
                alert_id = str(alert["id"])
                user_id = str(alert["user_id"])
                condition = alert["condition_json"]

                logger.debug(f"Evaluating alert {alert_id} for user {user_id}")

                # Build evaluation context
                ctx = {
                    "asof_date": asof_date,
                    "user_id": user_id,
                    "portfolio_id": condition.get("portfolio_id"),
                }

                # Check if alert should trigger
                should_trigger = await self.alert_service.should_trigger(alert, ctx)

                evaluated_count += 1

                if not should_trigger:
                    logger.debug(f"Alert {alert_id} did not trigger")
                    skipped_count += 1
                    continue

                triggered_count += 1
                logger.info(f"Alert {alert_id} triggered for user {user_id}")

                # Get current value for notification message
                current_value = await self.alert_service.get_alert_value(condition, ctx)

                # Build notification message
                message = self._build_notification_message(
                    condition=condition,
                    current_value=current_value,
                )

                # Determine notification channels
                channels = {
                    "email": alert.get("notify_email", False),
                    "inapp": alert.get("notify_inapp", True),
                }

                # Send notification (with deduplication)
                try:
                    delivered = await self.notification_service.send_notification(
                        user_id=user_id,
                        alert_id=alert_id,
                        message=message,
                        channels=channels,
                        alert_name=self._get_alert_name(condition),
                    )

                    if delivered:
                        delivered_count += 1

                        # Update last_fired_at timestamp
                        await self._update_last_fired_at(alert_id)

                        logger.info(
                            f"Notification delivered for alert {alert_id} "
                            f"(channels: {channels})"
                        )
                    else:
                        # Deduplication prevented delivery
                        logger.debug(
                            f"Notification skipped (deduplication) for alert {alert_id}"
                        )
                        skipped_count += 1

                except Exception as e:
                    # Notification failed - push to DLQ
                    logger.error(f"Notification failed for alert {alert_id}: {e}")
                    failed_count += 1

                    # Push to DLQ for retry
                    await self.dlq_service.push_to_dlq(
                        alert_id=alert_id,
                        user_id=user_id,
                        payload={
                            "message": message,
                            "channels": channels,
                            "alert_name": self._get_alert_name(condition),
                        },
                        error=str(e),
                    )

            except Exception as e:
                logger.exception(f"Failed to evaluate alert {alert.get('id')}: {e}")
                failed_count += 1

        # Compute timing
        completed_at = datetime.now()
        duration_seconds = (completed_at - started_at).total_seconds()

        # Build summary
        summary = {
            "asof_date": str(asof_date),
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": duration_seconds,
            "alerts_loaded": len(alerts),
            "alerts_evaluated": evaluated_count,
            "alerts_triggered": triggered_count,
            "notifications_delivered": delivered_count,
            "notifications_failed": failed_count,
            "alerts_skipped": skipped_count,
        }

        logger.info(f"=" * 80)
        logger.info(f"ALERT EVALUATION COMPLETED")
        logger.info(f"  Duration: {duration_seconds:.2f}s")
        logger.info(f"  Alerts loaded: {len(alerts)}")
        logger.info(f"  Alerts evaluated: {evaluated_count}")
        logger.info(f"  Alerts triggered: {triggered_count}")
        logger.info(f"  Notifications delivered: {delivered_count}")
        logger.info(f"  Notifications failed: {failed_count}")
        logger.info(f"  Alerts skipped: {skipped_count}")
        logger.info(f"=" * 80)

        return summary

    async def _load_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Load all active alerts from database.

        Returns:
            List of alert dicts
        """
        if not self.use_db:
            # Stub: return empty list
            logger.debug("Loading active alerts (stub mode)")
            return []

        # Query alerts table
        query = """
            SELECT
                id,
                user_id,
                condition_json,
                notify_email,
                notify_inapp,
                cooldown_hours,
                last_fired_at,
                created_at,
                updated_at
            FROM alerts
            WHERE is_active = true
            ORDER BY created_at ASC
        """

        try:
            rows = await self.execute_query(query)

            alerts = [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "condition_json": row["condition_json"],
                    "notify_email": row["notify_email"],
                    "notify_inapp": row["notify_inapp"],
                    "cooldown_hours": row["cooldown_hours"],
                    "last_fired_at": row["last_fired_at"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in rows
            ]

            logger.debug(f"Loaded {len(alerts)} active alerts")
            return alerts

        except Exception as e:
            logger.error(f"Failed to load active alerts: {e}")
            return []

    async def _update_last_fired_at(self, alert_id: str):
        """
        Update alert's last_fired_at timestamp.

        Args:
            alert_id: Alert UUID
        """
        if not self.use_db:
            # Stub: no-op
            return

        query = """
            UPDATE alerts
            SET last_fired_at = NOW()
            WHERE id = $1::uuid
        """

        try:
            await self.execute_statement(query, alert_id)
            logger.debug(f"Updated last_fired_at for alert {alert_id}")
        except Exception as e:
            logger.error(f"Failed to update last_fired_at for alert {alert_id}: {e}")

    def _build_notification_message(
        self,
        condition: Dict[str, Any],
        current_value: Optional[Any],
    ) -> str:
        """
        Build human-readable notification message.

        Args:
            condition: Alert condition JSON
            current_value: Current value that triggered alert

        Returns:
            Notification message
        """
        condition_type = condition.get("type")
        operator = condition.get("op", ">")
        threshold = condition.get("value", 0)

        # Operator symbols
        op_symbols = {
            ">": "exceeded",
            "<": "fell below",
            ">=": "reached or exceeded",
            "<=": "fell to or below",
            "==": "equals",
            "!=": "no longer equals",
        }

        op_text = op_symbols.get(operator, operator)

        if condition_type == "macro":
            entity = condition.get("entity", "indicator")
            metric = condition.get("metric", "level")
            return (
                f"{entity} {op_text} {threshold} "
                f"(current {metric}: {current_value})"
            )

        elif condition_type == "metric":
            portfolio_id = condition.get("portfolio_id", "unknown")
            metric_name = condition.get("metric", "metric")
            return (
                f"Portfolio metric '{metric_name}' {op_text} {threshold} "
                f"(current: {current_value})"
            )

        elif condition_type == "rating":
            symbol = condition.get("symbol", "security")
            metric_name = condition.get("metric", "rating")
            return (
                f"{symbol} {metric_name} {op_text} {threshold} "
                f"(current: {current_value})"
            )

        elif condition_type == "price":
            symbol = condition.get("symbol", "security")
            metric_name = condition.get("metric", "price")
            return (
                f"{symbol} {metric_name} {op_text} {threshold} "
                f"(current: {current_value})"
            )

        elif condition_type == "news_sentiment":
            symbol = condition.get("symbol", "security")
            return (
                f"{symbol} news sentiment {op_text} {threshold} "
                f"(current: {current_value})"
            )

        else:
            return f"Alert condition triggered: {condition_type}"

    def _get_alert_name(self, condition: Dict[str, Any]) -> str:
        """
        Get human-readable alert name.

        Args:
            condition: Alert condition JSON

        Returns:
            Alert name
        """
        condition_type = condition.get("type")

        if condition_type == "macro":
            entity = condition.get("entity", "indicator")
            return f"Macro Alert: {entity}"

        elif condition_type == "metric":
            metric_name = condition.get("metric", "metric")
            return f"Metric Alert: {metric_name}"

        elif condition_type == "rating":
            symbol = condition.get("symbol", "security")
            metric_name = condition.get("metric", "rating")
            return f"Rating Alert: {symbol} {metric_name}"

        elif condition_type == "price":
            symbol = condition.get("symbol", "security")
            return f"Price Alert: {symbol}"

        elif condition_type == "news_sentiment":
            symbol = condition.get("symbol", "security")
            return f"Sentiment Alert: {symbol}"

        else:
            return "Alert"


# ===========================
# STANDALONE EXECUTION
# ===========================

async def main():
    """Run alert evaluation job immediately (for testing)."""
    # Get date from command line or use today
    if len(sys.argv) > 1:
        asof_date = date.fromisoformat(sys.argv[1])
    else:
        asof_date = date.today()

    # Initialize evaluator
    evaluator = AlertEvaluator(use_db=True)

    # Run evaluation
    summary = await evaluator.evaluate_all_alerts(asof_date=asof_date)

    # Exit with appropriate code
    if summary["notifications_failed"] > 0:
        logger.warning(
            f"Alert evaluation completed with {summary['notifications_failed']} failures"
        )
        sys.exit(1)
    else:
        logger.info("Alert evaluation completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run
    asyncio.run(main())
