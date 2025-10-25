"""
Database Connection Management

Purpose: Async PostgreSQL/TimescaleDB connection pooling
Updated: 2025-10-22
Priority: P0 (Critical for Task 6)

Features:
    - AsyncPG connection pool
    - Connection lifecycle management
    - Health checks
    - Graceful shutdown

Usage:
    from backend.app.db.connection import get_db_pool, init_db_pool

    # Initialize at startup
    await init_db_pool(database_url)

    # Use in queries
    async with get_db_pool().acquire() as conn:
        result = await conn.fetchrow("SELECT * FROM pricing_packs LIMIT 1")
"""

import asyncpg
import logging
import os
import threading
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger("DawsOS.Database")


# ============================================================================
# PoolManager Singleton
# ============================================================================
# Singleton pattern ensures ONE pool instance exists across ALL module imports,
# async contexts, and even uvicorn reloads. This solves the "pool not initialized"
# issue when agents/services import connection.py from different module instances.

class PoolManager:
    """
    Singleton database connection pool manager.

    Ensures a single pool instance exists across all module imports,
    async contexts, and even uvicorn worker reloads.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # Initialize instance attributes (NOT class attributes!)
                    cls._instance._pool = None
        return cls._instance

    async def initialize(
        self,
        database_url: str,
        min_size: int = 5,
        max_size: int = 20,
        command_timeout: float = 60.0,
        max_inactive_connection_lifetime: float = 300.0,
    ) -> asyncpg.Pool:
        """Initialize the connection pool (idempotent)."""
        if self._pool is not None:
            logger.warning("Database pool already initialized, returning existing pool")
            return self._pool

        logger.info(f"Initializing database connection pool (min={min_size}, max={max_size})")

        try:
            self._pool = await asyncpg.create_pool(
                database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=command_timeout,
                max_inactive_connection_lifetime=max_inactive_connection_lifetime,
            )

            logger.info("Database connection pool initialized successfully")

            # Test connection
            async with self._pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"Database connected: {version}")

            return self._pool

        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}", exc_info=True)
            raise

    def get_pool(self) -> asyncpg.Pool:
        """Get the connection pool (raises if not initialized)."""
        if not hasattr(self, '_pool') or self._pool is None:
            raise RuntimeError(
                "Database pool not initialized. Call PoolManager().initialize() first."
            )
        return self._pool

    async def close(self):
        """Close the connection pool."""
        if not hasattr(self, '_pool') or self._pool is None:
            logger.warning("Database pool not initialized, nothing to close")
            return

        logger.info("Closing database connection pool")
        try:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}", exc_info=True)


# Global singleton instance (deprecated - kept for backwards compatibility)
_pool_manager = PoolManager()

# ============================================================================
# Redis Coordinator (NEW - Fixes cross-module pool access)
# ============================================================================
from backend.app.db.redis_pool_coordinator import coordinator


async def init_db_pool(
    database_url: Optional[str] = None,
    min_size: int = 5,
    max_size: int = 20,
    command_timeout: float = 60.0,
    max_inactive_connection_lifetime: float = 300.0,
) -> asyncpg.Pool:
    """
    Initialize database connection pool via Redis coordinator.

    Uses Redis to coordinate pool configuration across module instances,
    fixing the "pool not initialized" issue in agents.

    Args:
        database_url: PostgreSQL connection URL (default: from DATABASE_URL env)
        min_size: Minimum pool size
        max_size: Maximum pool size
        command_timeout: Command timeout in seconds
        max_inactive_connection_lifetime: Max inactive connection lifetime

    Returns:
        AsyncPG connection pool

    Raises:
        ValueError: If database_url not provided and DATABASE_URL not set
        asyncpg.PostgresError: If connection fails
    """
    # Get database URL
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "Database URL not provided. Set DATABASE_URL environment variable "
            "or pass database_url parameter."
        )

    # Use Redis coordinator (fixes cross-module instance issue)
    return await coordinator.initialize(
        database_url=database_url,
        min_size=min_size,
        max_size=max_size,
        command_timeout=command_timeout,
        max_inactive_connection_lifetime=max_inactive_connection_lifetime,
    )


def get_db_pool() -> asyncpg.Pool:
    """
    Get database connection pool from Redis coordinator.

    Each module instance gets its own AsyncPG pool, but configuration is
    coordinated via Redis to ensure consistency.

    Returns:
        AsyncPG connection pool

    Raises:
        RuntimeError: If pool not initialized
    """
    # Try to get pool synchronously first (fast path)
    pool = coordinator.get_pool_sync()
    if pool is not None:
        return pool

    # Pool not initialized yet - this is an error
    # (Async creation must happen in async context via get_db_connection)
    raise RuntimeError(
        "Database pool not initialized. Call init_db_pool() in startup event."
    )


async def close_db_pool():
    """
    Close database connection pool via Redis coordinator.

    Gracefully closes the local pool and clears Redis configuration.
    """
    await coordinator.close()


@asynccontextmanager
async def get_db_connection():
    """
    Get database connection from pool (context manager).

    Automatically creates local pool from Redis config if needed.

    Usage:
        async with get_db_connection() as conn:
            result = await conn.fetchrow("SELECT * FROM pricing_packs LIMIT 1")

    Yields:
        AsyncPG connection
    """
    # Try to get pool, creating from Redis config if needed (async context)
    pool = await coordinator.get_pool()
    async with pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_db_connection_with_rls(user_id: str):
    """
    Get database connection with RLS context set (context manager).

    Sets app.user_id session variable for Row-Level Security policies.

    Args:
        user_id: User UUID (for RLS filtering)

    Usage:
        async with get_db_connection_with_rls(ctx.user_id) as conn:
            # All queries in this connection automatically filtered by user_id
            result = await conn.fetchrow("SELECT * FROM portfolios WHERE id = $1", portfolio_id)

    Yields:
        AsyncPG connection with RLS context set

    Note:
        RLS context is transaction-scoped using SET LOCAL, so it automatically
        resets when the transaction ends. This ensures no RLS bleed between requests.
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        # Start transaction
        async with conn.transaction():
            # Set RLS context (transaction-scoped)
            await conn.execute(f"SET LOCAL app.user_id = '{user_id}'")
            logger.debug(f"RLS context set: user_id={user_id}")

            yield conn

        # Transaction ends here, RLS context automatically reset


async def check_db_health() -> dict:
    """
    Check database health.

    Returns:
        Health status dict

    Raises:
        Exception: If health check fails
    """
    try:
        pool = get_db_pool()

        # Get pool stats
        pool_size = pool.get_size()
        pool_free = pool.get_idle_size()

        # Test query
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        return {
            "status": "healthy",
            "pool_size": pool_size,
            "pool_free": pool_free,
            "pool_in_use": pool_size - pool_free,
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
        }


# ============================================================================
# Database Utilities
# ============================================================================


async def execute_query(query: str, *args, timeout: Optional[float] = None) -> list:
    """
    Execute query and return all rows.

    Args:
        query: SQL query
        *args: Query parameters
        timeout: Query timeout (default: use pool default)

    Returns:
        List of Record objects
    """
    async with get_db_connection() as conn:
        if timeout:
            return await conn.fetch(query, *args, timeout=timeout)
        else:
            return await conn.fetch(query, *args)


async def execute_query_one(
    query: str, *args, timeout: Optional[float] = None
) -> Optional[asyncpg.Record]:
    """
    Execute query and return first row.

    Args:
        query: SQL query
        *args: Query parameters
        timeout: Query timeout (default: use pool default)

    Returns:
        Record object or None if no results
    """
    async with get_db_connection() as conn:
        if timeout:
            return await conn.fetchrow(query, *args, timeout=timeout)
        else:
            return await conn.fetchrow(query, *args)


async def execute_query_value(
    query: str, *args, timeout: Optional[float] = None
) -> Optional[any]:
    """
    Execute query and return single value.

    Args:
        query: SQL query
        *args: Query parameters
        timeout: Query timeout (default: use pool default)

    Returns:
        Single value or None if no results
    """
    async with get_db_connection() as conn:
        if timeout:
            return await conn.fetchval(query, *args, timeout=timeout)
        else:
            return await conn.fetchval(query, *args)


async def execute_statement(query: str, *args, timeout: Optional[float] = None) -> str:
    """
    Execute statement (INSERT/UPDATE/DELETE).

    Args:
        query: SQL statement
        *args: Query parameters
        timeout: Query timeout (default: use pool default)

    Returns:
        Status string (e.g., "UPDATE 1")
    """
    async with get_db_connection() as conn:
        if timeout:
            return await conn.execute(query, *args, timeout=timeout)
        else:
            return await conn.execute(query, *args)
