"""
Alert Management API Routes

Purpose: CRUD operations for user-defined alerts
Updated: 2025-10-23
Priority: P1 (Sprint 3 Week 6)

Endpoints:
    POST   /v1/alerts              - Create new alert
    GET    /v1/alerts              - List alerts (RLS filtered)
    GET    /v1/alerts/{id}         - Get single alert
    PATCH  /v1/alerts/{id}         - Update alert
    DELETE /v1/alerts/{id}         - Delete alert (soft delete)
    POST   /v1/alerts/{id}/test    - Test alert condition (dry run)

Features:
    - Row-Level Security (RLS) for multi-tenant isolation
    - Condition validation
    - Cooldown enforcement
    - Deduplication (max 1 notification per user/alert/day)

Usage:
    # Create alert
    POST /v1/alerts
    X-User-ID: 11111111-1111-1111-1111-111111111111
    {
        "condition_json": {
            "type": "macro",
            "entity": "VIX",
            "metric": "level",
            "op": ">",
            "value": 30
        },
        "notify_email": true,
        "notify_inapp": true,
        "cooldown_hours": 24
    }
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Header, status, Query
from pydantic import BaseModel, Field

from backend.app.db.connection import get_db_connection_with_rls, execute_query_one
from backend.app.core.alert_validators import (
    validate_alert_condition,
    validate_cooldown_hours,
    validate_notification_channels,
)
from backend.app.services.alerts import AlertService

logger = logging.getLogger("DawsOS.API.Alerts")

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


# ============================================================================
# Request/Response Models
# ============================================================================


class AlertCreate(BaseModel):
    """Alert creation request."""

    condition_json: Dict[str, Any] = Field(
        ..., description="Alert condition JSON (see alert_validators for schema)"
    )
    notify_email: bool = Field(default=False, description="Send email notifications")
    notify_inapp: bool = Field(default=True, description="Send in-app notifications")
    cooldown_hours: int = Field(
        default=24,
        ge=0,
        le=8760,
        description="Cooldown period in hours (prevent spam)",
    )


class AlertUpdate(BaseModel):
    """Alert update request."""

    condition_json: Optional[Dict[str, Any]] = Field(None, description="Alert condition JSON")
    notify_email: Optional[bool] = None
    notify_inapp: Optional[bool] = None
    cooldown_hours: Optional[int] = Field(None, ge=0, le=8760)
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    """Alert response model."""

    id: UUID
    user_id: UUID
    condition_json: Dict[str, Any]
    notify_email: bool
    notify_inapp: bool
    cooldown_hours: int
    last_fired_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertTestResponse(BaseModel):
    """Alert test response (dry run)."""

    alert_id: UUID
    condition_met: bool
    current_value: Optional[Any]
    threshold_value: Any
    would_trigger: bool
    cooldown_remaining_hours: Optional[float]
    message: str


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


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert: AlertCreate, user_id: UUID = Depends(get_current_user_id)
) -> AlertResponse:
    """
    Create new alert.

    Steps:
        1. Validate condition JSON
        2. Validate cooldown hours
        3. Validate notification channels
        4. Insert into alerts table with RLS context

    Args:
        alert: Alert creation data
        user_id: Current user ID (from header/JWT)

    Returns:
        Created alert

    Raises:
        HTTPException: If validation or creation fails
    """
    alert_id = uuid4()

    logger.info(f"Creating alert for user {user_id}: {alert.condition_json}")

    # Validate condition JSON
    is_valid, errors = validate_alert_condition(alert.condition_json)
    if not is_valid:
        logger.warning(f"Invalid alert condition: {errors}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors, "message": "Invalid alert condition"},
        )

    # Validate cooldown
    is_valid, errors = validate_cooldown_hours(alert.cooldown_hours)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors, "message": "Invalid cooldown hours"},
        )

    # Validate notification channels
    is_valid, errors = validate_notification_channels(
        alert.notify_email, alert.notify_inapp
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors, "message": "Invalid notification channels"},
        )

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            query = """
                INSERT INTO alerts (
                    id,
                    user_id,
                    condition_json,
                    notify_email,
                    notify_inapp,
                    cooldown_hours,
                    is_active,
                    created_at,
                    updated_at
                ) VALUES (
                    $1::uuid,
                    $2::uuid,
                    $3::jsonb,
                    $4,
                    $5,
                    $6,
                    true,
                    NOW(),
                    NOW()
                )
                RETURNING
                    id,
                    user_id,
                    condition_json,
                    notify_email,
                    notify_inapp,
                    cooldown_hours,
                    last_fired_at,
                    is_active,
                    created_at,
                    updated_at
            """

            row = await conn.fetchrow(
                query,
                alert_id,
                user_id,
                alert.condition_json,
                alert.notify_email,
                alert.notify_inapp,
                alert.cooldown_hours,
            )

            logger.info(f"Alert created: {alert_id}")

            return AlertResponse(
                id=row["id"],
                user_id=row["user_id"],
                condition_json=row["condition_json"],
                notify_email=row["notify_email"],
                notify_inapp=row["notify_inapp"],
                cooldown_hours=row["cooldown_hours"],
                last_fired_at=row["last_fired_at"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    except Exception as e:
        logger.error(f"Failed to create alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert",
        )


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    user_id: UUID = Depends(get_current_user_id),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[AlertResponse]:
    """
    List user's alerts (RLS filtered).

    Args:
        user_id: Current user ID (from header/JWT)
        is_active: Filter by active status
        limit: Maximum results
        offset: Offset for pagination

    Returns:
        List of alerts
    """
    logger.debug(f"Listing alerts for user {user_id}")

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            # Build query with optional filter
            active_filter = ""
            params = [limit, offset]
            if is_active is not None:
                active_filter = "AND is_active = $3"
                params.append(is_active)

            query = f"""
                SELECT
                    id,
                    user_id,
                    condition_json,
                    notify_email,
                    notify_inapp,
                    cooldown_hours,
                    last_fired_at,
                    is_active,
                    created_at,
                    updated_at
                FROM alerts
                WHERE user_id = '{user_id}'
                {active_filter}
                ORDER BY created_at DESC
                LIMIT $1
                OFFSET $2
            """

            rows = await conn.fetch(query, *params)

            alerts = [
                AlertResponse(
                    id=row["id"],
                    user_id=row["user_id"],
                    condition_json=row["condition_json"],
                    notify_email=row["notify_email"],
                    notify_inapp=row["notify_inapp"],
                    cooldown_hours=row["cooldown_hours"],
                    last_fired_at=row["last_fired_at"],
                    is_active=row["is_active"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

            logger.debug(f"Found {len(alerts)} alerts for user {user_id}")
            return alerts

    except Exception as e:
        logger.error(f"Failed to list alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list alerts",
        )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID, user_id: UUID = Depends(get_current_user_id)
) -> AlertResponse:
    """
    Get alert by ID (RLS filtered).

    Args:
        alert_id: Alert UUID
        user_id: Current user ID (from header/JWT)

    Returns:
        Alert details

    Raises:
        HTTPException: If alert not found
    """
    logger.debug(f"Getting alert {alert_id} for user {user_id}")

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            query = """
                SELECT
                    id,
                    user_id,
                    condition_json,
                    notify_email,
                    notify_inapp,
                    cooldown_hours,
                    last_fired_at,
                    is_active,
                    created_at,
                    updated_at
                FROM alerts
                WHERE id = $1::uuid
                  AND user_id = '{user_id}'
            """

            row = await conn.fetchrow(query.format(user_id=user_id), alert_id)

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Alert {alert_id} not found",
                )

            return AlertResponse(
                id=row["id"],
                user_id=row["user_id"],
                condition_json=row["condition_json"],
                notify_email=row["notify_email"],
                notify_inapp=row["notify_inapp"],
                cooldown_hours=row["cooldown_hours"],
                last_fired_at=row["last_fired_at"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert",
        )


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    alert_update: AlertUpdate,
    user_id: UUID = Depends(get_current_user_id),
) -> AlertResponse:
    """
    Update alert (RLS filtered).

    Args:
        alert_id: Alert UUID
        alert_update: Alert update data
        user_id: Current user ID (from header/JWT)

    Returns:
        Updated alert

    Raises:
        HTTPException: If alert not found or update fails
    """
    logger.info(f"Updating alert {alert_id} for user {user_id}")

    # Validate condition if provided
    if alert_update.condition_json:
        is_valid, errors = validate_alert_condition(alert_update.condition_json)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": errors, "message": "Invalid alert condition"},
            )

    # Validate cooldown if provided
    if alert_update.cooldown_hours is not None:
        is_valid, errors = validate_cooldown_hours(alert_update.cooldown_hours)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": errors, "message": "Invalid cooldown hours"},
            )

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            # Build UPDATE query dynamically
            updates = []
            params = [alert_id]
            param_idx = 2

            if alert_update.condition_json is not None:
                updates.append(f"condition_json = ${param_idx}::jsonb")
                params.append(alert_update.condition_json)
                param_idx += 1

            if alert_update.notify_email is not None:
                updates.append(f"notify_email = ${param_idx}")
                params.append(alert_update.notify_email)
                param_idx += 1

            if alert_update.notify_inapp is not None:
                updates.append(f"notify_inapp = ${param_idx}")
                params.append(alert_update.notify_inapp)
                param_idx += 1

            if alert_update.cooldown_hours is not None:
                updates.append(f"cooldown_hours = ${param_idx}")
                params.append(alert_update.cooldown_hours)
                param_idx += 1

            if alert_update.is_active is not None:
                updates.append(f"is_active = ${param_idx}")
                params.append(alert_update.is_active)
                param_idx += 1

            if not updates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update",
                )

            # Add updated_at
            updates.append("updated_at = NOW()")

            query = f"""
                UPDATE alerts
                SET {', '.join(updates)}
                WHERE id = $1::uuid
                  AND user_id = '{user_id}'
                RETURNING
                    id,
                    user_id,
                    condition_json,
                    notify_email,
                    notify_inapp,
                    cooldown_hours,
                    last_fired_at,
                    is_active,
                    created_at,
                    updated_at
            """

            row = await conn.fetchrow(query.format(user_id=user_id), *params)

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Alert {alert_id} not found",
                )

            logger.info(f"Alert {alert_id} updated")

            return AlertResponse(
                id=row["id"],
                user_id=row["user_id"],
                condition_json=row["condition_json"],
                notify_email=row["notify_email"],
                notify_inapp=row["notify_inapp"],
                cooldown_hours=row["cooldown_hours"],
                last_fired_at=row["last_fired_at"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert",
        )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID, user_id: UUID = Depends(get_current_user_id)
):
    """
    Delete alert (soft delete - sets is_active=false).

    Args:
        alert_id: Alert UUID
        user_id: Current user ID (from header/JWT)

    Raises:
        HTTPException: If alert not found
    """
    logger.info(f"Deleting alert {alert_id} for user {user_id}")

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            query = """
                UPDATE alerts
                SET is_active = false, updated_at = NOW()
                WHERE id = $1::uuid
                  AND user_id = '{user_id}'
            """

            result = await conn.execute(query.format(user_id=user_id), alert_id)

            # Check if any row was updated
            if result == "UPDATE 0":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Alert {alert_id} not found",
                )

            logger.info(f"Alert {alert_id} deleted (soft delete)")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert",
        )


@router.post("/{alert_id}/test", response_model=AlertTestResponse)
async def test_alert(
    alert_id: UUID, user_id: UUID = Depends(get_current_user_id)
) -> AlertTestResponse:
    """
    Test alert condition (dry run).

    Evaluates condition against current data without sending notifications.

    Args:
        alert_id: Alert UUID
        user_id: Current user ID (from header/JWT)

    Returns:
        Test results (condition met, current value, would trigger)

    Raises:
        HTTPException: If alert not found
    """
    logger.info(f"Testing alert {alert_id} for user {user_id}")

    try:
        # Get alert
        alert_row = await execute_query_one(
            """
            SELECT
                id,
                user_id,
                condition_json,
                cooldown_hours,
                last_fired_at
            FROM alerts
            WHERE id = $1::uuid
              AND user_id = $2::uuid
            """,
            alert_id,
            user_id,
        )

        if not alert_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found",
            )

        alert_data = {
            "id": str(alert_row["id"]),
            "condition_json": alert_row["condition_json"],
            "cooldown_hours": alert_row["cooldown_hours"],
            "last_fired_at": alert_row["last_fired_at"],
        }

        # Evaluate condition
        alert_service = AlertService(use_db=True)

        from datetime import date

        ctx = {
            "asof_date": date.today(),
            "user_id": str(user_id),
            "portfolio_id": alert_data["condition_json"].get("portfolio_id"),
        }

        condition_met = await alert_service.evaluate_condition(
            alert_data["condition_json"], ctx
        )

        current_value = await alert_service.get_alert_value(
            alert_data["condition_json"], ctx
        )

        cooldown_passed = alert_service.check_cooldown(
            alert_id=str(alert_id),
            last_fired_at=alert_data["last_fired_at"],
            cooldown_hours=alert_data["cooldown_hours"],
        )

        would_trigger = condition_met and cooldown_passed

        # Calculate cooldown remaining
        cooldown_remaining_hours = None
        if alert_data["last_fired_at"] and not cooldown_passed:
            from datetime import datetime, timedelta

            cooldown_delta = timedelta(hours=alert_data["cooldown_hours"])
            time_since_fire = datetime.utcnow() - alert_data["last_fired_at"]
            remaining = cooldown_delta - time_since_fire
            cooldown_remaining_hours = remaining.total_seconds() / 3600

        # Build message
        if would_trigger:
            message = f"Alert would trigger! Condition met and cooldown passed."
        elif condition_met and not cooldown_passed:
            message = f"Condition met, but cooldown active ({cooldown_remaining_hours:.1f}h remaining)"
        else:
            message = "Condition not met"

        logger.info(f"Alert test complete: {message}")

        return AlertTestResponse(
            alert_id=alert_id,
            condition_met=condition_met,
            current_value=current_value,
            threshold_value=alert_data["condition_json"].get("value"),
            would_trigger=would_trigger,
            cooldown_remaining_hours=cooldown_remaining_hours,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test alert",
        )
