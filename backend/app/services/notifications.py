"""
Notification Delivery Service

Purpose: Send alert notifications via email and in-app channels
Updated: 2025-10-23
Priority: P1 (Sprint 3 Week 6)

Features:
    - In-app notifications (stored in notifications table)
    - Email notifications (via SMTP or AWS SES)
    - Deduplication (prevents duplicate deliveries)
    - Idempotency keys (user_id:alert_id:date)
    - Channel selection (email, in-app, or both)

Deduplication:
    - Database unique constraint: UNIQUE (user_id, alert_id, date_trunc('day', delivered_at))
    - Idempotency key: f"{user_id}:{alert_id}:{date}"
    - Prevents max 1 notification per user/alert/day

Email Configuration:
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=alerts@dawsos.com
    SMTP_PASSWORD=xxx
    SMTP_FROM=DawsOS Alerts <alerts@dawsos.com>

    Or use AWS SES:
    AWS_REGION=us-east-1
    AWS_SES_FROM=alerts@dawsos.com

Usage:
    from app.services.notifications import NotificationService

    notif_svc = NotificationService()

    # Send notification
    await notif_svc.send_notification(
        user_id="xxx",
        alert_id="yyy",
        message="VIX exceeded 30 (current: 32.5)",
        channels={"email": True, "inapp": True}
    )
"""

import logging
import os
import smtplib
from datetime import date, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from uuid import UUID

from app.db.connection import execute_query, execute_statement, execute_query_one
from app.core.exceptions import DatabaseError, ExternalAPIError

logger = logging.getLogger("DawsOS.Notifications")


class NotificationService:
    """
    Notification delivery service.

    Delivers notifications via:
    - In-app (stored in notifications table)
    - Email (SMTP or AWS SES)

    Implements deduplication to prevent spam.
    """

    def __init__(self, use_db: bool = True):
        """
        Initialize notification service.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
        """
        self.use_db = use_db

        # Email configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", "DawsOS Alerts <alerts@dawsos.com>")

        # AWS SES configuration (alternative to SMTP)
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.aws_ses_from = os.getenv("AWS_SES_FROM", "alerts@dawsos.com")
        self.use_ses = os.getenv("USE_AWS_SES", "false").lower() == "true"

        if use_db:
            try:
                from app.db.connection import execute_query_one, execute_statement

                self.execute_query_one = execute_query_one
                self.execute_statement = execute_statement
                logger.info("NotificationService initialized with database integration")

            except (ValueError, TypeError, KeyError, AttributeError) as e:
                # Programming errors - should not happen, log and re-raise
                logger.error(f"Programming error initializing database connections: {e}", exc_info=True)
                raise
            except Exception as e:
                # Connection/configuration errors - log and fall back to stub mode
                logger.warning(
                    f"Failed to initialize database connections: {e}. "
                    "Falling back to stub mode."
                )
                # Don't raise DatabaseError here - graceful degradation is intentional
                self.use_db = False
        else:
            logger.info("NotificationService initialized in stub mode")

    async def send_notification(
        self,
        user_id: str,
        alert_id: str,
        message: str,
        channels: Dict[str, bool],
        alert_name: Optional[str] = None,
    ) -> bool:
        """
        Send notification to user via specified channels.

        Args:
            user_id: User UUID
            alert_id: Alert UUID
            message: Notification message
            channels: Channel selection {"email": bool, "inapp": bool}
            alert_name: Optional alert name (for email subject)

        Returns:
            True if delivery succeeded, False otherwise

        Raises:
            Exception: If delivery fails (caller should push to DLQ)
        """
        logger.info(
            f"Sending notification to user {user_id} for alert {alert_id} "
            f"(channels: {channels})"
        )

        # Check deduplication
        if not await self.check_deduplication(user_id, alert_id, date.today()):
            logger.warning(
                f"Notification already delivered today for user {user_id}, alert {alert_id}"
            )
            return False

        success = True

        # Send in-app notification
        if channels.get("inapp", True):
            try:
                await self.send_inapp_notification(user_id, alert_id, message)
                logger.info(f"In-app notification sent to user {user_id}")
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                # Programming errors - re-raise to surface bugs immediately
                logger.error(f"Programming error sending in-app notification: {e}", exc_info=True)
                raise
            except Exception as e:
                # Database/service errors - re-raise as DatabaseError (critical operation)
                logger.error(f"Failed to send in-app notification: {e}")
                raise DatabaseError(f"Failed to send in-app notification: {e}", retryable=True) from e

        # Send email notification
        if channels.get("email", False):
            try:
                # Get user email from database
                email = await self._get_user_email(user_id)
                if email:
                    await self.send_email_notification(
                        email=email,
                        message=message,
                        subject=f"DawsOS Alert: {alert_name or 'Condition Triggered'}",
                    )
                    logger.info(f"Email notification sent to {email}")
                else:
                    logger.warning(f"No email found for user {user_id}")
            except Exception as e:
                # Email service errors - re-raise as ExternalAPIError (critical operation)
                logger.error(f"Failed to send email notification: {e}")
                raise ExternalAPIError(f"Failed to send email notification: {e}", api_name="email", retryable=True) from e

        return success

    async def send_inapp_notification(
        self,
        user_id: str,
        alert_id: str,
        message: str,
    ) -> str:
        """
        Send in-app notification (store in notifications table).

        Args:
            user_id: User UUID
            alert_id: Alert UUID
            message: Notification message

        Returns:
            Notification ID

        Raises:
            Exception: If database insert fails
        """
        if not self.use_db:
            # Stub: return fake notification ID
            logger.debug(f"In-app notification (stub): {message}")
            return "stub-notification-id"

        # Insert into notifications table
        # Deduplication enforced by UNIQUE constraint
        query = """
            INSERT INTO notifications (
                user_id,
                alert_id,
                message,
                delivered_at,
                created_at
            ) VALUES (
                $1::uuid,
                $2::uuid,
                $3,
                NOW(),
                NOW()
            )
            ON CONFLICT (user_id, alert_id, (delivered_at::date))
            DO NOTHING
            RETURNING id
        """

        try:
            row = await self.execute_query_one(query, user_id, alert_id, message)

            if row:
                notification_id = str(row["id"])
                logger.debug(f"In-app notification created: {notification_id}")
                return notification_id
            else:
                # Conflict: notification already exists for today
                logger.warning(
                    f"In-app notification already exists for user {user_id}, alert {alert_id}"
                )
                return ""

        except Exception as e:
            # Database errors - re-raise as DatabaseError (critical operation)
            logger.error(f"Failed to insert in-app notification: {e}")
            raise DatabaseError(f"Failed to insert in-app notification: {e}", retryable=True) from e

    async def send_email_notification(
        self,
        email: str,
        message: str,
        subject: str = "DawsOS Alert",
    ) -> bool:
        """
        Send email notification via SMTP or AWS SES.

        Args:
            email: Recipient email address
            message: Email body (plain text)
            subject: Email subject

        Returns:
            True if email sent successfully, False otherwise

        Raises:
            Exception: If email delivery fails
        """
        if self.use_ses:
            return await self._send_email_ses(email, message, subject)
        else:
            return await self._send_email_smtp(email, message, subject)

    async def _send_email_smtp(
        self,
        email: str,
        message: str,
        subject: str,
    ) -> bool:
        """Send email via SMTP."""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured, skipping email")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.smtp_from
            msg["To"] = email
            msg["Subject"] = subject

            # Plain text body
            text_part = MIMEText(message, "plain")
            msg.attach(text_part)

            # HTML body (optional)
            html_message = f"""
            <html>
              <body>
                <h2>DawsOS Alert</h2>
                <p>{message}</p>
                <hr>
                <p style="color: gray; font-size: 12px;">
                  This is an automated alert from DawsOS. To manage your alerts, visit the DawsOS dashboard.
                </p>
              </body>
            </html>
            """
            html_part = MIMEText(html_message, "html")
            msg.attach(html_part)

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent via SMTP to {email}")
            return True

        except Exception as e:
            # SMTP errors - re-raise as ExternalAPIError (critical operation)
            logger.error(f"Failed to send email via SMTP: {e}")
            raise ExternalAPIError(f"Failed to send email via SMTP: {e}", api_name="smtp", retryable=True) from e

    async def _send_email_ses(
        self,
        email: str,
        message: str,
        subject: str,
    ) -> bool:
        """Send email via AWS SES."""
        try:
            import boto3

            ses_client = boto3.client("ses", region_name=self.aws_region)

            # Send email
            response = ses_client.send_email(
                Source=self.aws_ses_from,
                Destination={"ToAddresses": [email]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {
                        "Text": {"Data": message},
                        "Html": {
                            "Data": f"""
                            <html>
                              <body>
                                <h2>DawsOS Alert</h2>
                                <p>{message}</p>
                                <hr>
                                <p style="color: gray; font-size: 12px;">
                                  This is an automated alert from DawsOS. To manage your alerts, visit the DawsOS dashboard.
                                </p>
                              </body>
                            </html>
                            """
                        },
                    },
                },
            )

            logger.info(f"Email sent via SES to {email}: {response['MessageId']}")
            return True

        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            # SES errors - re-raise as ExternalAPIError (critical operation)
            logger.error(f"Failed to send email via SES: {e}")
            raise ExternalAPIError(f"Failed to send email via SES: {e}", api_name="ses", retryable=True) from e

    async def check_deduplication(
        self,
        user_id: str,
        alert_id: str,
        notification_date: date,
    ) -> bool:
        """
        Check if notification already delivered today.

        Uses database unique constraint:
        UNIQUE (user_id, alert_id, date_trunc('day', delivered_at))

        Args:
            user_id: User UUID
            alert_id: Alert UUID
            notification_date: Date for deduplication check

        Returns:
            True if notification can be sent (no duplicate), False otherwise
        """
        if not self.use_db:
            # Stub: always allow
            return True

        # Query for existing notification
        query = """
            SELECT id
            FROM notifications
            WHERE user_id = $1::uuid
              AND alert_id = $2::uuid
              AND delivered_at::date = $3
            LIMIT 1
        """

        try:
            row = await self.execute_query_one(query, user_id, alert_id, notification_date)

            if row:
                # Duplicate exists
                logger.debug(
                    f"Notification already exists for user {user_id}, "
                    f"alert {alert_id} on {notification_date}"
                )
                return False
            else:
                # No duplicate
                return True

        except Exception as e:
            # Database errors - fail open (allow notification on error)
            logger.error(f"Failed to check deduplication: {e}")
            # Don't raise DatabaseError here - fail open is intentional
            return True

    def generate_idempotency_key(
        self,
        user_id: str,
        alert_id: str,
        notification_date: date,
    ) -> str:
        """
        Generate idempotency key for notification.

        Format: {user_id}:{alert_id}:{date}

        Args:
            user_id: User UUID
            alert_id: Alert UUID
            notification_date: Date for idempotency

        Returns:
            Idempotency key
        """
        return f"{user_id}:{alert_id}:{notification_date}"

    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """
        Get user email from database.

        Args:
            user_id: User UUID

        Returns:
            Email address or None if not found
        """
        if not self.use_db:
            # Stub: return fake email
            return f"user-{user_id}@example.com"

        # Query users table
        query = """
            SELECT email
            FROM users
            WHERE id = $1::uuid
        """

        try:
            row = await self.execute_query_one(query, user_id)
            if row and row["email"]:
                return row["email"]
            else:
                logger.warning(f"No email found for user {user_id}")
                return None
        except Exception as e:
            # Database errors - log and return None (graceful degradation)
            logger.error(f"Failed to get user email: {e}")
            # Don't raise DatabaseError here - graceful degradation is intentional
            return None

    async def mark_notification_read(
        self,
        notification_id: str,
        user_id: str,
    ) -> bool:
        """
        Mark notification as read.

        Args:
            notification_id: Notification UUID
            user_id: User UUID (for RLS)

        Returns:
            True if marked as read, False otherwise
        """
        if not self.use_db:
            # Stub: always succeed
            return True

        # Update notifications table
        query = """
            UPDATE notifications
            SET read_at = NOW()
            WHERE id = $1::uuid
              AND user_id = $2::uuid
              AND read_at IS NULL
        """

        try:
            result = await self.execute_statement(query, notification_id, user_id)
            # Result is like "UPDATE 1" or "UPDATE 0"
            updated = int(result.split()[-1]) if result else 0
            return updated > 0
        except Exception as e:
            # Database errors - log and return False (graceful degradation)
            logger.error(f"Failed to mark notification as read: {e}")
            # Don't raise DatabaseError here - graceful degradation is intentional
            return False

    async def delete_notification(
        self,
        notification_id: str,
        user_id: str,
    ) -> bool:
        """
        Delete notification.

        Args:
            notification_id: Notification UUID
            user_id: User UUID (for RLS)

        Returns:
            True if deleted, False otherwise
        """
        if not self.use_db:
            # Stub: always succeed
            return True

        # Delete from notifications table
        query = """
            DELETE FROM notifications
            WHERE id = $1::uuid
              AND user_id = $2::uuid
        """

        try:
            result = await self.execute_statement(query, notification_id, user_id)
            deleted = int(result.split()[-1]) if result else 0
            return deleted > 0
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error deleting notification: {e}", exc_info=True)
            raise
        except Exception as e:
            # Database errors - log and return False (graceful degradation)
            logger.error(f"Failed to delete notification: {e}")
            # Don't raise DatabaseError here - graceful degradation is intentional
            return False

    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get user's notifications.

        Args:
            user_id: User UUID
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            unread_only: If True, only return unread notifications

        Returns:
            List of notification dicts
        """
        if not self.use_db:
            # Stub: return empty list
            return []

        # Query notifications table
        unread_filter = "AND read_at IS NULL" if unread_only else ""

        query = f"""
            SELECT
                id,
                alert_id,
                message,
                delivered_at,
                read_at,
                created_at
            FROM notifications
            WHERE user_id = $1::uuid
            {unread_filter}
            ORDER BY delivered_at DESC
            LIMIT $2
            OFFSET $3
        """

        try:
            from app.db.connection import execute_query

            rows = await execute_query(query, user_id, limit, offset)

            return [
                {
                    "id": str(row["id"]),
                    "alert_id": str(row["alert_id"]),
                    "message": row["message"],
                    "delivered_at": row["delivered_at"].isoformat() if row["delivered_at"] else None,
                    "read_at": row["read_at"].isoformat() if row["read_at"] else None,
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "is_read": row["read_at"] is not None,
                }
                for row in rows
            ]

        except Exception as e:
            # Database errors - log and return empty list (graceful degradation)
            logger.error(f"Failed to get user notifications: {e}")
            # Don't raise DatabaseError here - graceful degradation is intentional
            return []
