"""
Notification Management API Routes

Purpose: CRUD operations for in-app notifications
Updated: 2025-10-23
Priority: P1 (Sprint 3 Week 6)

Endpoints:
    GET    /v1/notifications              - List notifications (RLS filtered)
    PATCH  /v1/notifications/{id}/read    - Mark notification as read
    DELETE /v1/notifications/{id}          - Delete notification

Features:
    - Row-Level Security (RLS) for multi-tenant isolation
    - Pagination support (50 per page)
    - Unread filter
    - Mark as read endpoint
    - Delete endpoint

Usage:
    # Get unread notifications
    GET /v1/notifications?unread_only=true
    X-User-ID: 11111111-1111-1111-1111-111111111111

    # Mark as read
    PATCH /v1/notifications/{notification_id}/read
    X-User-ID: 11111111-1111-1111-1111-111111111111
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, status, Query
from pydantic import BaseModel, Field

from backend.app.db.connection import get_db_connection_with_rls
from backend.app.services.notifications import NotificationService

logger = logging.getLogger("DawsOS.API.Notifications")

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


# ============================================================================
# Response Models
# ============================================================================


class NotificationResponse(BaseModel):
    """Notification response model."""

    id: UUID
    alert_id: UUID
    message: str
    delivered_at: datetime
    read_at: Optional[datetime]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notification list response."""

    notifications: List[NotificationResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


# ============================================================================
# Dependency: Get User ID from Header
# ============================================================================


async def get_current_user_id(
    x_user_id: Optional[str] = Header(None, description="User ID for RLS context")
) -> UUID:
    """
    Extract user_id from request header.

    In production, this would come from JWT token validation.
    For development, we use X-User-ID header.

    Args:
        x_user_id: User ID from header

    Returns:
        User UUID

    Raises:
        HTTPException: If user_id not provided
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-ID header required (or JWT token in production)",
        )

    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format (must be UUID)",
        )


# ============================================================================
# Endpoints
# ============================================================================


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    user_id: UUID = Depends(get_current_user_id),
    unread_only: bool = Query(False, description="Filter to unread notifications only"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> NotificationListResponse:
    """
    List user's notifications (RLS filtered).

    Args:
        user_id: Current user ID (from header/JWT)
        unread_only: Filter to unread notifications only
        limit: Maximum results (default: 50, max: 100)
        offset: Offset for pagination

    Returns:
        Paginated list of notifications
    """
    logger.debug(
        f"Listing notifications for user {user_id} "
        f"(unread_only={unread_only}, limit={limit}, offset={offset})"
    )

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            # Build query with optional unread filter
            unread_filter = "AND read_at IS NULL" if unread_only else ""

            # Get total count
            count_query = f"""
                SELECT COUNT(*) AS total
                FROM notifications
                WHERE user_id = '{user_id}'
                {unread_filter}
            """

            count_row = await conn.fetchrow(count_query.format(user_id=user_id))
            total = count_row["total"] if count_row else 0

            # Get notifications
            query = f"""
                SELECT
                    id,
                    alert_id,
                    message,
                    delivered_at,
                    read_at,
                    created_at,
                    (read_at IS NOT NULL) AS is_read
                FROM notifications
                WHERE user_id = '{user_id}'
                {unread_filter}
                ORDER BY delivered_at DESC
                LIMIT $1
                OFFSET $2
            """

            rows = await conn.fetch(query.format(user_id=user_id), limit, offset)

            notifications = [
                NotificationResponse(
                    id=row["id"],
                    alert_id=row["alert_id"],
                    message=row["message"],
                    delivered_at=row["delivered_at"],
                    read_at=row["read_at"],
                    is_read=row["is_read"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

            has_more = (offset + len(notifications)) < total

            logger.debug(
                f"Found {len(notifications)} notifications for user {user_id} "
                f"(total: {total}, has_more: {has_more})"
            )

            return NotificationListResponse(
                notifications=notifications,
                total=total,
                limit=limit,
                offset=offset,
                has_more=has_more,
            )

    except Exception as e:
        logger.error(f"Failed to list notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list notifications",
        )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID, user_id: UUID = Depends(get_current_user_id)
) -> NotificationResponse:
    """
    Mark notification as read.

    Args:
        notification_id: Notification UUID
        user_id: Current user ID (from header/JWT)

    Returns:
        Updated notification

    Raises:
        HTTPException: If notification not found
    """
    logger.info(f"Marking notification {notification_id} as read for user {user_id}")

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            query = """
                UPDATE notifications
                SET read_at = NOW()
                WHERE id = $1::uuid
                  AND user_id = '{user_id}'
                  AND read_at IS NULL
                RETURNING
                    id,
                    alert_id,
                    message,
                    delivered_at,
                    read_at,
                    created_at,
                    (read_at IS NOT NULL) AS is_read
            """

            row = await conn.fetchrow(query.format(user_id=user_id), notification_id)

            if not row:
                # Check if notification exists but already read
                check_query = """
                    SELECT id
                    FROM notifications
                    WHERE id = $1::uuid
                      AND user_id = '{user_id}'
                """
                check_row = await conn.fetchrow(
                    check_query.format(user_id=user_id), notification_id
                )

                if check_row:
                    # Notification exists but already read
                    # Fetch current state and return
                    get_query = """
                        SELECT
                            id,
                            alert_id,
                            message,
                            delivered_at,
                            read_at,
                            created_at,
                            (read_at IS NOT NULL) AS is_read
                        FROM notifications
                        WHERE id = $1::uuid
                          AND user_id = '{user_id}'
                    """
                    row = await conn.fetchrow(
                        get_query.format(user_id=user_id), notification_id
                    )
                else:
                    # Notification not found
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Notification {notification_id} not found",
                    )

            logger.info(f"Notification {notification_id} marked as read")

            return NotificationResponse(
                id=row["id"],
                alert_id=row["alert_id"],
                message=row["message"],
                delivered_at=row["delivered_at"],
                read_at=row["read_at"],
                is_read=row["is_read"],
                created_at=row["created_at"],
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read",
        )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID, user_id: UUID = Depends(get_current_user_id)
):
    """
    Delete notification.

    Args:
        notification_id: Notification UUID
        user_id: Current user ID (from header/JWT)

    Raises:
        HTTPException: If notification not found
    """
    logger.info(f"Deleting notification {notification_id} for user {user_id}")

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            query = """
                DELETE FROM notifications
                WHERE id = $1::uuid
                  AND user_id = '{user_id}'
            """

            result = await conn.execute(query.format(user_id=user_id), notification_id)

            # Check if any row was deleted
            if result == "DELETE 0":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Notification {notification_id} not found",
                )

            logger.info(f"Notification {notification_id} deleted")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification",
        )


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(user_id: UUID = Depends(get_current_user_id)):
    """
    Mark all unread notifications as read.

    Args:
        user_id: Current user ID (from header/JWT)
    """
    logger.info(f"Marking all notifications as read for user {user_id}")

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            query = """
                UPDATE notifications
                SET read_at = NOW()
                WHERE user_id = '{user_id}'
                  AND read_at IS NULL
            """

            result = await conn.execute(query.format(user_id=user_id))

            # Extract count from result (e.g., "UPDATE 5")
            count = int(result.split()[-1]) if result else 0
            logger.info(f"Marked {count} notifications as read for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read",
        )
