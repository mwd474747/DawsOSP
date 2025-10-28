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
from decimal import Decimal
from typing import Dict, Any, Optional, List
from uuid import UUID

from app.services.alerts import AlertService
from app.services.notifications import NotificationService
from app.services.dlq import DLQService

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
                from app.db.connection import (
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

                # Generate playbook if this is a DaR/drawdown/regime shift alert
                playbook = await self._generate_playbook(condition, ctx)

                # Build notification message
                message = self._build_notification_message(
                    condition=condition,
                    current_value=current_value,
                    playbook=playbook,
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

    async def _generate_playbook(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Generate actionable playbook for triggered alert.

        Args:
            condition: Alert condition JSON
            ctx: Evaluation context (contains DaR result, drawdown, etc.)

        Returns:
            Playbook dict or None if not applicable
        """
        condition_type = condition.get("type")

        try:
            from app.services.playbooks import PlaybookGenerator

            if condition_type == "dar_breach":
                # DaR breach playbook
                dar_result = ctx.get("dar_result", {})
                dar_actual = ctx.get("dar_actual")
                portfolio_id = condition.get("portfolio_id")
                threshold = Decimal(str(condition.get("threshold", 0.15)))

                if dar_actual and dar_result:
                    playbook = PlaybookGenerator.generate_dar_breach_playbook(
                        portfolio_id=UUID(portfolio_id),
                        dar_actual=dar_actual,
                        dar_threshold=threshold,
                        worst_scenario=dar_result.get("worst_scenario", "unknown"),
                        current_nav=Decimal(str(dar_result.get("current_nav", 1000000))),
                    )
                    return playbook

            elif condition_type == "drawdown_limit":
                # Drawdown limit playbook
                current_drawdown = ctx.get("current_drawdown")
                portfolio_id = condition.get("portfolio_id")
                limit = Decimal(str(condition.get("limit", 0.20)))

                if current_drawdown:
                    # Get current NAV from database
                    current_nav = Decimal("1000000")  # Default
                    if self.use_db:
                        nav_query = """
                            SELECT SUM(quantity * cost_basis_per_share) AS nav
                            FROM lots
                            WHERE portfolio_id = $1::uuid AND is_open = true
                        """
                        nav_row = await self.execute_query_one(nav_query, portfolio_id)
                        if nav_row and nav_row["nav"]:
                            current_nav = Decimal(str(nav_row["nav"]))

                    playbook = PlaybookGenerator.generate_drawdown_limit_playbook(
                        portfolio_id=UUID(portfolio_id),
                        current_drawdown=current_drawdown,
                        drawdown_limit=limit,
                        current_nav=current_nav,
                    )
                    return playbook

            elif condition_type == "regime_shift":
                # Regime shift playbook
                old_regime = ctx.get("old_regime")
                new_regime = ctx.get("new_regime")
                confidence = ctx.get("regime_confidence", Decimal("0.90"))

                if old_regime and new_regime:
                    playbook = PlaybookGenerator.generate_regime_shift_playbook(
                        portfolio_id=UUID(condition.get("portfolio_id", "00000000-0000-0000-0000-000000000000")),
                        old_regime=old_regime,
                        new_regime=new_regime,
                        confidence=confidence,
                    )
                    return playbook

        except Exception as e:
            logger.error(f"Failed to generate playbook: {e}", exc_info=True)

        return None

    def _build_notification_message(
        self,
        condition: Dict[str, Any],
        current_value: Optional[Any],
        playbook: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build human-readable notification message.

        Args:
            condition: Alert condition JSON
            current_value: Current value that triggered alert
            playbook: Optional playbook with actionable recommendations

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

        # Build base message based on condition type
        if condition_type == "dar_breach":
            dar_actual = threshold if isinstance(threshold, Decimal) else Decimal(str(threshold))
            base_msg = (
                f"⚠️ RISK ALERT: Drawdown at Risk (DaR) breach detected!\n\n"
                f"Portfolio DaR: {current_value:.1%} (threshold: {threshold:.1%})\n"
            )

        elif condition_type == "drawdown_limit":
            base_msg = (
                f"🚨 CRITICAL: Drawdown limit breached!\n\n"
                f"Current drawdown: {current_value:.1%} (limit: {threshold:.1%})\n"
            )

        elif condition_type == "regime_shift":
            base_msg = (
                f"📊 MACRO SHIFT: Regime change detected!\n\n"
                f"New regime: {current_value}\n"
            )

        elif condition_type == "macro":
            entity = condition.get("entity", "indicator")
            metric = condition.get("metric", "level")
            base_msg = (
                f"{entity} {op_text} {threshold} "
                f"(current {metric}: {current_value})"
            )

        elif condition_type == "metric":
            portfolio_id = condition.get("portfolio_id", "unknown")
            metric_name = condition.get("metric", "metric")
            base_msg = (
                f"Portfolio metric '{metric_name}' {op_text} {threshold} "
                f"(current: {current_value})"
            )

        elif condition_type == "rating":
            symbol = condition.get("symbol", "security")
            metric_name = condition.get("metric", "rating")
            base_msg = (
                f"{symbol} {metric_name} {op_text} {threshold} "
                f"(current: {current_value})"
            )

        elif condition_type == "price":
            symbol = condition.get("symbol", "security")
            metric_name = condition.get("metric", "price")
            base_msg = (
                f"{symbol} {metric_name} {op_text} {threshold} "
                f"(current: {current_value})"
            )

        elif condition_type == "news_sentiment":
            symbol = condition.get("symbol", "security")
            base_msg = (
                f"{symbol} news sentiment {op_text} {threshold} "
                f"(current: {current_value})"
            )

        else:
            base_msg = f"Alert condition triggered: {condition_type}"

        # Append playbook if available
        if playbook:
            playbook_msg = "\n\n📋 RECOMMENDED ACTION:\n"
            playbook_msg += f"Action: {playbook.get('action', 'N/A')}\n"
            playbook_msg += f"Rationale: {playbook.get('rationale', 'N/A')}\n"

            instruments = playbook.get('instruments', [])
            if instruments:
                playbook_msg += f"\nInstruments:\n"
                for inst in instruments[:3]:  # Show first 3 instruments
                    symbol = inst.get('symbol', inst.get('type', 'N/A'))
                    inst_type = inst.get('type', 'N/A')
                    playbook_msg += f"  • {symbol} ({inst_type})\n"

            notional = playbook.get('notional_usd', 0)
            if notional > 0:
                playbook_msg += f"\nSuggested allocation: ${notional:,.0f}\n"

            alternatives = playbook.get('alternatives', [])
            if alternatives:
                playbook_msg += f"\nAlternatives:\n"
                for alt in alternatives[:2]:  # Show first 2 alternatives
                    playbook_msg += f"  • {alt}\n"

            base_msg += playbook_msg

        return base_msg

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
