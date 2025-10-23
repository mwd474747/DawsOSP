"""
TimescaleDB Continuous Aggregate Manager

Purpose: Monitor and manage TimescaleDB continuous aggregates
Updated: 2025-10-22
Priority: P0 (Phase 3 Task 4)

Features:
    - Monitor continuous aggregate freshness
    - Check refresh policy status
    - Manual refresh triggers
    - Performance monitoring
    - Health checks

Usage:
    from backend.app.db import get_continuous_aggregate_manager

    manager = get_continuous_aggregate_manager()

    # Check freshness
    status = await manager.get_aggregate_status()

    # Manual refresh
    await manager.refresh_aggregate('portfolio_metrics_30d_rolling')

    # Performance metrics
    stats = await manager.get_performance_stats()
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .connection import execute_query, execute_query_one, execute_statement

logger = logging.getLogger(__name__)


@dataclass
class AggregateStatus:
    """Status of a continuous aggregate."""

    view_name: str
    materialization_hypertable: str
    refresh_lag: Optional[timedelta]
    last_refresh: Optional[datetime]
    refresh_policy_enabled: bool
    schedule_interval: Optional[timedelta]
    total_rows: Optional[int]
    size_bytes: Optional[int]


@dataclass
class RefreshPolicy:
    """Continuous aggregate refresh policy configuration."""

    view_name: str
    schedule_interval: timedelta
    start_offset: timedelta
    end_offset: timedelta
    enabled: bool


class ContinuousAggregateManager:
    """
    Manager for TimescaleDB continuous aggregates.

    Provides monitoring, refresh, and performance tracking.
    """

    def __init__(self):
        """Initialize continuous aggregate manager."""
        logger.info("ContinuousAggregateManager initialized")

    async def get_all_aggregates(self) -> List[str]:
        """
        Get list of all continuous aggregates.

        Returns:
            List of continuous aggregate view names
        """
        query = """
            SELECT view_name
            FROM timescaledb_information.continuous_aggregates
            ORDER BY view_name
        """

        rows = await execute_query(query)
        return [row["view_name"] for row in rows]

    async def get_aggregate_status(
        self, view_name: Optional[str] = None
    ) -> Dict[str, AggregateStatus]:
        """
        Get status of continuous aggregates.

        Args:
            view_name: Optional specific aggregate name. If None, returns all.

        Returns:
            Dictionary mapping view name to AggregateStatus
        """
        if view_name:
            query = """
                SELECT
                    view_name,
                    materialization_hypertable_name,
                    completed_threshold,
                    invalidation_threshold
                FROM timescaledb_information.continuous_aggregates
                WHERE view_name = $1
            """
            rows = await execute_query(query, view_name)
        else:
            query = """
                SELECT
                    view_name,
                    materialization_hypertable_name,
                    completed_threshold,
                    invalidation_threshold
                FROM timescaledb_information.continuous_aggregates
            """
            rows = await execute_query(query)

        statuses = {}

        for row in rows:
            vname = row["view_name"]

            # Get refresh policy
            policy = await self._get_refresh_policy(vname)

            # Calculate refresh lag
            refresh_lag = None
            if row["completed_threshold"]:
                refresh_lag = datetime.now() - row["completed_threshold"]

            # Get size stats
            size_info = await self._get_aggregate_size(vname)

            statuses[vname] = AggregateStatus(
                view_name=vname,
                materialization_hypertable=row["materialization_hypertable_name"],
                refresh_lag=refresh_lag,
                last_refresh=row["completed_threshold"],
                refresh_policy_enabled=policy.enabled if policy else False,
                schedule_interval=policy.schedule_interval if policy else None,
                total_rows=size_info.get("row_count"),
                size_bytes=size_info.get("total_bytes"),
            )

        return statuses

    async def _get_refresh_policy(self, view_name: str) -> Optional[RefreshPolicy]:
        """Get refresh policy for a continuous aggregate."""
        query = """
            SELECT
                schedule_interval,
                config->>'start_offset' as start_offset,
                config->>'end_offset' as end_offset
            FROM timescaledb_information.jobs j
            JOIN timescaledb_information.continuous_aggregates ca
                ON ca.materialization_hypertable_name =
                   (j.hypertable_name::text)
            WHERE ca.view_name = $1
                AND j.proc_name = 'policy_refresh_continuous_aggregate'
        """

        row = await execute_query_one(query, view_name)

        if not row:
            return None

        return RefreshPolicy(
            view_name=view_name,
            schedule_interval=row["schedule_interval"],
            start_offset=self._parse_interval(row["start_offset"]),
            end_offset=self._parse_interval(row["end_offset"]),
            enabled=True,  # TODO: Check if job is enabled
        )

    async def _get_aggregate_size(self, view_name: str) -> Dict[str, Any]:
        """Get size statistics for a continuous aggregate."""
        query = """
            SELECT
                COUNT(*) as row_count,
                pg_total_relation_size(view_name::regclass) as total_bytes
            FROM (SELECT $1::text as view_name) v
        """

        try:
            row = await execute_query_one(query, view_name)
            return {
                "row_count": row["row_count"] if row else 0,
                "total_bytes": row["total_bytes"] if row else 0,
            }
        except Exception as e:
            logger.warning(f"Failed to get size for {view_name}: {e}")
            return {"row_count": None, "total_bytes": None}

    def _parse_interval(self, interval_str: str) -> timedelta:
        """Parse PostgreSQL interval string to timedelta."""
        # Simple parser for common intervals
        # TODO: Implement full PostgreSQL interval parsing
        if "hour" in interval_str:
            hours = int(interval_str.split()[0])
            return timedelta(hours=hours)
        elif "day" in interval_str:
            days = int(interval_str.split()[0])
            return timedelta(days=days)
        elif "month" in interval_str:
            # Approximate 1 month as 30 days
            months = int(interval_str.split()[0])
            return timedelta(days=months * 30)
        else:
            return timedelta(0)

    async def refresh_aggregate(
        self, view_name: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> bool:
        """
        Manually refresh a continuous aggregate.

        Args:
            view_name: Name of the continuous aggregate
            start_time: Optional start of refresh window
            end_time: Optional end of refresh window

        Returns:
            True if successful
        """
        try:
            if start_time and end_time:
                query = f"""
                    CALL refresh_continuous_aggregate(
                        '{view_name}',
                        $1,
                        $2
                    )
                """
                await execute_statement(query, start_time, end_time)
                logger.info(
                    f"Refreshed {view_name} from {start_time} to {end_time}"
                )
            else:
                # Refresh entire aggregate
                query = f"""
                    CALL refresh_continuous_aggregate(
                        '{view_name}',
                        NULL,
                        NULL
                    )
                """
                await execute_statement(query)
                logger.info(f"Refreshed entire {view_name}")

            return True

        except Exception as e:
            logger.error(f"Failed to refresh {view_name}: {e}", exc_info=True)
            return False

    async def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance statistics for continuous aggregates.

        Returns:
            Dictionary mapping view name to performance metrics
        """
        aggregates = await self.get_all_aggregates()
        stats = {}

        for view_name in aggregates:
            # Get query performance
            query_stats = await self._get_query_stats(view_name)

            # Get refresh job stats
            job_stats = await self._get_job_stats(view_name)

            stats[view_name] = {
                "query_stats": query_stats,
                "job_stats": job_stats,
            }

        return stats

    async def _get_query_stats(self, view_name: str) -> Dict[str, Any]:
        """Get query performance stats for an aggregate."""
        # Query pg_stat_user_tables for the materialized view
        query = """
            SELECT
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                n_tup_ins,
                n_tup_upd,
                n_tup_del,
                n_live_tup,
                n_dead_tup,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            WHERE relname = $1
        """

        row = await execute_query_one(query, view_name)

        if not row:
            return {}

        return dict(row)

    async def _get_job_stats(self, view_name: str) -> Dict[str, Any]:
        """Get refresh job statistics for an aggregate."""
        query = """
            SELECT
                j.job_id,
                j.last_run_started_at,
                j.last_successful_finish,
                j.last_run_status,
                j.total_runs,
                j.total_successes,
                j.total_failures
            FROM timescaledb_information.jobs j
            JOIN timescaledb_information.continuous_aggregates ca
                ON ca.materialization_hypertable_name = (j.hypertable_name::text)
            WHERE ca.view_name = $1
                AND j.proc_name = 'policy_refresh_continuous_aggregate'
        """

        row = await execute_query_one(query, view_name)

        if not row:
            return {}

        return dict(row)

    async def check_health(self) -> Dict[str, Any]:
        """
        Perform health check on continuous aggregates.

        Returns:
            Health status dictionary
        """
        health = {
            "status": "healthy",
            "issues": [],
            "warnings": [],
            "aggregates": {},
        }

        statuses = await self.get_aggregate_status()

        for view_name, status in statuses.items():
            aggregate_health = {
                "status": "healthy",
                "issues": [],
            }

            # Check if refresh policy is enabled
            if not status.refresh_policy_enabled:
                aggregate_health["issues"].append("Refresh policy not enabled")
                aggregate_health["status"] = "degraded"

            # Check refresh lag
            if status.refresh_lag:
                if status.refresh_lag > timedelta(days=1):
                    aggregate_health["issues"].append(
                        f"High refresh lag: {status.refresh_lag}"
                    )
                    aggregate_health["status"] = "degraded"
                elif status.refresh_lag > timedelta(hours=6):
                    aggregate_health["issues"].append(
                        f"Moderate refresh lag: {status.refresh_lag}"
                    )
                    if aggregate_health["status"] == "healthy":
                        aggregate_health["status"] = "warning"

            # Check size
            if status.total_rows == 0:
                aggregate_health["issues"].append("No data in aggregate")
                aggregate_health["status"] = "degraded"

            health["aggregates"][view_name] = aggregate_health

            # Update overall health
            if aggregate_health["status"] == "degraded":
                health["status"] = "degraded"
                health["issues"].extend(
                    [f"{view_name}: {issue}" for issue in aggregate_health["issues"]]
                )
            elif (
                aggregate_health["status"] == "warning"
                and health["status"] == "healthy"
            ):
                health["status"] = "warning"
                health["warnings"].extend(
                    [f"{view_name}: {issue}" for issue in aggregate_health["issues"]]
                )

        return health

    async def get_freshness_report(self) -> str:
        """
        Generate human-readable freshness report.

        Returns:
            Formatted report string
        """
        statuses = await self.get_aggregate_status()

        lines = ["=" * 80, "CONTINUOUS AGGREGATE FRESHNESS REPORT", "=" * 80, ""]

        for view_name, status in statuses.items():
            lines.append(f"Aggregate: {view_name}")
            lines.append(f"  Last Refresh: {status.last_refresh or 'Never'}")
            lines.append(
                f"  Refresh Lag: {status.refresh_lag or 'N/A'}"
            )
            lines.append(
                f"  Schedule: {status.schedule_interval or 'No policy'}"
            )
            lines.append(f"  Rows: {status.total_rows or 'Unknown':,}")
            lines.append(
                f"  Size: {self._format_bytes(status.size_bytes) if status.size_bytes else 'Unknown'}"
            )
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.2f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.2f} PB"


# ============================================================================
# Singleton Instance
# ============================================================================

_continuous_aggregate_manager: Optional[ContinuousAggregateManager] = None


def get_continuous_aggregate_manager() -> ContinuousAggregateManager:
    """Get singleton ContinuousAggregateManager instance."""
    global _continuous_aggregate_manager
    if _continuous_aggregate_manager is None:
        _continuous_aggregate_manager = ContinuousAggregateManager()
    return _continuous_aggregate_manager
