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
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger("DawsOS.Database")


# ============================================================================
# Connection Pool
# ============================================================================

_pool: Optional[asyncpg.Pool] = None


async def init_db_pool(
    database_url: Optional[str] = None,
    min_size: int = 5,
    max_size: int = 20,
    command_timeout: float = 60.0,
    max_inactive_connection_lifetime: float = 300.0,
) -> asyncpg.Pool:
    """
    Initialize database connection pool.

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
    global _pool

    if _pool is not None:
        logger.warning("Database pool already initialized, returning existing pool")
        return _pool

    # Get database URL
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "Database URL not provided. Set DATABASE_URL environment variable "
            "or pass database_url parameter."
        )

    logger.info(f"Initializing database connection pool (min={min_size}, max={max_size})")

    try:
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=min_size,
            max_size=max_size,
            command_timeout=command_timeout,
            max_inactive_connection_lifetime=max_inactive_connection_lifetime,
        )

        logger.info("Database connection pool initialized successfully")

        # Test connection
        async with _pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            logger.info(f"Database connected: {version}")

        return _pool

    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}", exc_info=True)
        raise


def get_db_pool() -> asyncpg.Pool:
    """
    Get database connection pool.

    Returns:
        AsyncPG connection pool

    Raises:
        RuntimeError: If pool not initialized
    """
    if _pool is None:
        raise RuntimeError(
            "Database pool not initialized. Call init_db_pool() first."
        )
    return _pool


async def close_db_pool():
    """
    Close database connection pool.

    Gracefully closes all connections in the pool.
    """
    global _pool

    if _pool is None:
        logger.warning("Database pool not initialized, nothing to close")
        return

    logger.info("Closing database connection pool")

    try:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")

    except Exception as e:
        logger.error(f"Error closing database pool: {e}", exc_info=True)
        raise


@asynccontextmanager
async def get_db_connection():
    """
    Get database connection from pool (context manager).

    Usage:
        async with get_db_connection() as conn:
            result = await conn.fetchrow("SELECT * FROM pricing_packs LIMIT 1")

    Yields:
        AsyncPG connection
    """
    pool = get_db_pool()
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
