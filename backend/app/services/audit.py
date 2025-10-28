"""
Audit Logging Service

Purpose: Log all user actions for security, compliance, and debugging
Updated: 2025-10-27
Priority: P0 (Critical for compliance and security)

Architecture:
    - All user actions logged to audit_log table
    - Includes user_id, action, resource_type, resource_id, details, timestamp
    - Immutable audit trail (no updates/deletes)
    - Queryable for compliance reporting

Database Schema:
    CREATE TABLE audit_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL,
        action TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        details JSONB,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        ip_address TEXT,
        user_agent TEXT
    );

Usage:
    from app.services.audit import get_audit_service

    audit = get_audit_service()

    # Log pattern execution
    await audit.log(
        user_id="11111111-1111-1111-1111-111111111111",
        action="execute_pattern",
        resource_type="pattern",
        resource_id="portfolio_overview",
        details={"portfolio_id": "22222222-2222-2222-2222-222222222222"}
    )

    # Log export
    await audit.log(
        user_id=user_id,
        action="export_pdf",
        resource_type="report",
        resource_id=report_id,
        details={"format": "pdf", "size_bytes": 45000}
    )
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg

logger = logging.getLogger(__name__)


class AuditService:
    """
    Audit logging service.

    Logs all user actions to audit_log table for:
        - Security monitoring
        - Compliance reporting
        - Debugging and troubleshooting
        - User activity tracking
    """

    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        """
        Initialize audit service.

        Args:
            db_pool: AsyncPG connection pool (optional, can be lazy-loaded)
        """
        self.db_pool = db_pool
        logger.info("AuditService initialized")

    def _get_db_pool(self) -> asyncpg.Pool:
        """
        Get database pool (lazy load if needed).

        Returns:
            AsyncPG pool

        Raises:
            RuntimeError: If pool not available
        """
        if self.db_pool is not None:
            return self.db_pool

        # Try to get pool from connection module
        from app.db.connection import get_db_pool
        self.db_pool = get_db_pool()
        return self.db_pool

    async def log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log user action to audit trail.

        Args:
            user_id: UUID of user performing action
            action: Action name (e.g., "execute_pattern", "export_pdf", "write_trade")
            resource_type: Type of resource (e.g., "pattern", "portfolio", "report")
            resource_id: ID of resource (pattern_id, portfolio_id, etc.)
            details: Optional JSON details (inputs, outputs, metadata)
            ip_address: Optional client IP address
            user_agent: Optional client user agent string

        Example:
            >>> await audit.log(
            ...     user_id="11111111-1111-1111-1111-111111111111",
            ...     action="execute_pattern",
            ...     resource_type="pattern",
            ...     resource_id="portfolio_overview",
            ...     details={"portfolio_id": "22222222-2222-2222-2222-222222222222"}
            ... )
        """
        try:
            pool = self._get_db_pool()

            query = """
                INSERT INTO audit_log (
                    user_id,
                    action,
                    resource_type,
                    resource_id,
                    details,
                    timestamp,
                    ip_address,
                    user_agent
                )
                VALUES ($1, $2, $3, $4, $5, NOW(), $6, $7)
            """

            await pool.execute(
                query,
                UUID(user_id) if isinstance(user_id, str) else user_id,
                action,
                resource_type,
                resource_id,
                details or {},
                ip_address,
                user_agent
            )

            logger.debug(
                f"Audit log: user_id={user_id}, action={action}, "
                f"resource_type={resource_type}, resource_id={resource_id}"
            )

        except Exception as e:
            # CRITICAL: Never fail request due to audit log failure
            # Log error but don't raise exception
            logger.error(
                f"Failed to write audit log: {e} "
                f"(user_id={user_id}, action={action}, resource_type={resource_type})"
            )

    async def get_user_activity(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get recent activity for a user.

        Args:
            user_id: User UUID
            limit: Max number of records (default: 100)
            offset: Pagination offset (default: 0)

        Returns:
            List of audit log records

        Example:
            >>> activity = await audit.get_user_activity("11111111-1111-1111-1111-111111111111")
            >>> for record in activity:
            ...     print(f"{record['timestamp']}: {record['action']} on {record['resource_type']}")
        """
        try:
            pool = self._get_db_pool()

            query = """
                SELECT
                    id,
                    user_id,
                    action,
                    resource_type,
                    resource_id,
                    details,
                    timestamp,
                    ip_address,
                    user_agent
                FROM audit_log
                WHERE user_id = $1
                ORDER BY timestamp DESC
                LIMIT $2 OFFSET $3
            """

            rows = await pool.fetch(
                query,
                UUID(user_id) if isinstance(user_id, str) else user_id,
                limit,
                offset
            )

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to fetch user activity: {e}")
            return []

    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get audit history for a specific resource.

        Args:
            resource_type: Type of resource (e.g., "portfolio", "pattern")
            resource_id: Resource ID
            limit: Max number of records (default: 100)

        Returns:
            List of audit log records

        Example:
            >>> history = await audit.get_resource_history(
            ...     "portfolio",
            ...     "11111111-1111-1111-1111-111111111111"
            ... )
        """
        try:
            pool = self._get_db_pool()

            query = """
                SELECT
                    id,
                    user_id,
                    action,
                    resource_type,
                    resource_id,
                    details,
                    timestamp,
                    ip_address,
                    user_agent
                FROM audit_log
                WHERE resource_type = $1 AND resource_id = $2
                ORDER BY timestamp DESC
                LIMIT $3
            """

            rows = await pool.fetch(query, resource_type, resource_id, limit)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to fetch resource history: {e}")
            return []

    async def search_logs(
        self,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search audit logs with filters.

        Args:
            action: Filter by action (optional)
            resource_type: Filter by resource type (optional)
            user_id: Filter by user ID (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            limit: Max number of records (default: 100)

        Returns:
            List of matching audit log records

        Example:
            >>> # Find all exports in last 7 days
            >>> from datetime import datetime, timedelta
            >>> logs = await audit.search_logs(
            ...     action="export_pdf",
            ...     start_date=datetime.utcnow() - timedelta(days=7)
            ... )
        """
        try:
            pool = self._get_db_pool()

            # Build dynamic query based on filters
            conditions = []
            params = []
            param_idx = 1

            if action:
                conditions.append(f"action = ${param_idx}")
                params.append(action)
                param_idx += 1

            if resource_type:
                conditions.append(f"resource_type = ${param_idx}")
                params.append(resource_type)
                param_idx += 1

            if user_id:
                conditions.append(f"user_id = ${param_idx}")
                params.append(UUID(user_id) if isinstance(user_id, str) else user_id)
                param_idx += 1

            if start_date:
                conditions.append(f"timestamp >= ${param_idx}")
                params.append(start_date)
                param_idx += 1

            if end_date:
                conditions.append(f"timestamp <= ${param_idx}")
                params.append(end_date)
                param_idx += 1

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
                SELECT
                    id,
                    user_id,
                    action,
                    resource_type,
                    resource_id,
                    details,
                    timestamp,
                    ip_address,
                    user_agent
                FROM audit_log
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ${param_idx}
            """

            params.append(limit)

            rows = await pool.fetch(query, *params)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to search audit logs: {e}")
            return []


# ============================================================================
# Service Singleton
# ============================================================================

_audit_service = None


def get_audit_service(db_pool: Optional[asyncpg.Pool] = None) -> AuditService:
    """
    Get singleton audit service instance.

    Args:
        db_pool: Optional database pool (uses connection module if not provided)

    Returns:
        AuditService instance

    Example:
        >>> from app.services.audit import get_audit_service
        >>> audit = get_audit_service()
        >>> await audit.log(user_id, "execute_pattern", "pattern", pattern_id)
    """
    global _audit_service

    if _audit_service is None:
        _audit_service = AuditService(db_pool)

    return _audit_service
