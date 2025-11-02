"""
Database Connection Management

Purpose: Async PostgreSQL/TimescaleDB connection pooling
Updated: 2025-11-02
Priority: P0 (Critical)

Features:
    - AsyncPG connection pool with cross-module persistence
    - Connection lifecycle management
    - Health checks
    - Graceful shutdown

Usage:
    from app.db.connection import get_db_pool, init_db_pool

    # Initialize at startup
    await init_db_pool(database_url)

    # Use in queries
    async with get_db_pool().acquire() as conn:
        result = await conn.fetchrow("SELECT * FROM pricing_packs LIMIT 1")
"""

import asyncpg
import logging
import os
import sys
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger("DawsOS.Database")

# ============================================================================
# Cross-Module Pool Storage using sys.modules
# ============================================================================
# This ensures ALL imports of connection.py see the SAME pool instance,
# solving the module boundary issue where agents get different instances.

POOL_STORAGE_KEY = '__dawsos_db_pool_storage__'

def _get_pool_storage():
    """
    Get or create cross-module pool storage using sys.modules.
    
    This storage survives module reloads and different import contexts,
    ensuring all parts of the application see the same pool instance.
    """
    if POOL_STORAGE_KEY not in sys.modules:
        # Create a simple namespace to hold our pool
        import types
        storage = types.ModuleType(POOL_STORAGE_KEY)
        storage.pool = None
        sys.modules[POOL_STORAGE_KEY] = storage
        logger.info(f"Created cross-module pool storage: {POOL_STORAGE_KEY}")
    return sys.modules[POOL_STORAGE_KEY]

def register_external_pool(pool: asyncpg.Pool) -> None:
    """
    Register an externally created database pool.
    
    This stores the pool in sys.modules which survives module boundary issues,
    ensuring all agents can access the same pool instance.
    
    Args:
        pool: AsyncPG connection pool to register
    """
    storage = _get_pool_storage()
    storage.pool = pool
    logger.info(f"✅ Database pool registered in cross-module storage: {pool}")

# ============================================================================
# Pool Initialization
# ============================================================================

async def init_db_pool(
    database_url: Optional[str] = None,
    min_size: int = 5,
    max_size: int = 20,
    command_timeout: float = 60.0,
    max_inactive_connection_lifetime: float = 300.0,
) -> asyncpg.Pool:
    """
    Initialize database connection pool.

    Creates a pool and stores it in cross-module storage for access
    by all parts of the application.

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
    storage = _get_pool_storage()
    
    # Return existing pool if already initialized
    if storage.pool is not None:
        logger.warning("Database pool already initialized, returning existing pool")
        return storage.pool
    
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
        pool = await asyncpg.create_pool(
            database_url,
            min_size=min_size,
            max_size=max_size,
            command_timeout=command_timeout,
            max_inactive_connection_lifetime=max_inactive_connection_lifetime,
        )

        logger.info("Database connection pool created successfully")

        # Test connection
        async with pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            logger.info(f"Database connected: {version}")

        # Store in cross-module storage
        storage.pool = pool
        logger.info("✅ Database pool stored in cross-module storage")
        
        return pool

    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}", exc_info=True)
        raise

# ============================================================================
# Pool Access (Simplified to 2 sources)
# ============================================================================

def get_db_pool() -> asyncpg.Pool:
    """
    Get database connection pool.

    Simplified to just 2 sources:
    1. Cross-module storage (primary - works across module boundaries)
    2. Direct import from combined_server (fallback for legacy compatibility)

    Returns:
        AsyncPG connection pool

    Raises:
        RuntimeError: If pool not initialized
    """
    # SOURCE 1: Check cross-module storage (primary method)
    storage = _get_pool_storage()
    if storage.pool is not None:
        return storage.pool
    
    # SOURCE 2: Try direct import from combined_server (fallback)
    try:
        if 'combined_server' in sys.modules:
            import combined_server
            if hasattr(combined_server, 'db_pool') and combined_server.db_pool is not None:
                logger.info("Using pool directly from combined_server module (fallback)")
                # Also register it for future use
                register_external_pool(combined_server.db_pool)
                return combined_server.db_pool
    except Exception as e:
        logger.debug(f"Could not access combined_server.db_pool: {e}")

    # Pool not initialized - this is an error
    logger.error("❌ Database pool not initialized!")
    logger.error("  Attempted sources:")
    logger.error("    1. Cross-module storage - NOT FOUND")
    logger.error("    2. Direct import from combined_server - NOT FOUND")
    raise RuntimeError(
        "Database pool not initialized. Call init_db_pool() or register_external_pool() first."
    )

async def close_db_pool():
    """
    Close database connection pool.

    Gracefully closes the pool and clears it from cross-module storage.
    """
    storage = _get_pool_storage()
    
    if storage.pool is None:
        logger.warning("Database pool not initialized, nothing to close")
        return

    logger.info("Closing database connection pool")
    try:
        await storage.pool.close()
        storage.pool = None
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database pool: {e}", exc_info=True)

# ============================================================================
# Connection Context Managers
# ============================================================================

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

# ============================================================================
# Health Check
# ============================================================================

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