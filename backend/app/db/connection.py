"""
Database Connection Management - Simplified

Purpose: Simple AsyncPG connection pooling
Updated: 2025-10-28
Priority: P0 (Critical for system functionality)

Features:
    - Simple AsyncPG connection pool
    - No complex singleton patterns
    - Direct initialization and usage

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

logger = logging.getLogger("DawsOS.Database")

# Global pool instance
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
    global _pool
    
    if _pool is None:
        raise RuntimeError(
            "Database pool not initialized. Call init_db_pool() in startup event."
        )
    
    return _pool


async def close_db_pool():
    """
    Close database connection pool.

    Gracefully closes the pool.
    """
    global _pool
    
    if _pool is not None:
        logger.info("Closing database connection pool")
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")


# ============================================================================
# Connection Context Managers
# ============================================================================

from contextlib import asynccontextmanager
from typing import AsyncGenerator

@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Get a database connection from the pool.
    
    Returns:
        AsyncPG connection
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_db_connection_with_rls(user_id: str) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Get a database connection with Row Level Security (RLS) enabled.
    
    Args:
        user_id: User ID for RLS context
        
    Returns:
        AsyncPG connection with RLS enabled
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        # Set RLS context
        await conn.execute("SELECT set_config('app.current_user_id', $1, true)", user_id)
        yield conn


# ============================================================================
# Health Check and Query Execution
# ============================================================================

async def check_db_health() -> bool:
    """
    Check if database is healthy.
    
    Returns:
        True if healthy, False otherwise
    """
    try:
        pool = get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def execute_query(query: str, *args) -> list:
    """
    Execute a query and return all results.
    
    Args:
        query: SQL query
        *args: Query parameters
        
    Returns:
        List of results
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def execute_query_one(query: str, *args) -> dict:
    """
    Execute a query and return one result.
    
    Args:
        query: SQL query
        *args: Query parameters
        
    Returns:
        Single result row
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def execute_query_value(query: str, *args) -> any:
    """
    Execute a query and return a single value.
    
    Args:
        query: SQL query
        *args: Query parameters
        
    Returns:
        Single value
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)


async def execute_statement(query: str, *args) -> str:
    """
    Execute a statement (INSERT, UPDATE, DELETE).
    
    Args:
        query: SQL statement
        *args: Statement parameters
        
    Returns:
        Status message
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(query, *args)
        return "Statement executed successfully"