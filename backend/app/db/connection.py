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
import threading
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger("DawsOS.Database")

# Module-level shared pool storage
_shared_pool: Optional[asyncpg.Pool] = None

# External pool registration (for combined_server.py to register its pool)
_external_pool: Optional[asyncpg.Pool] = None

def register_external_pool(pool: asyncpg.Pool) -> None:
    """
    Register an externally created database pool.
    
    This allows combined_server.py to explicitly register its pool,
    solving the module instance separation issue.
    
    Args:
        pool: AsyncPG connection pool to register
    """
    global _external_pool, _shared_pool
    _external_pool = pool
    # ALSO set _shared_pool to ensure availability across module boundaries
    _shared_pool = pool
    
    # Additionally, try to set the pool in PoolManager singleton
    try:
        pool_manager = PoolManager()
        pool_manager._pool = pool
        logger.info(f"✅ Pool registered in PoolManager singleton")
    except Exception as e:
        logger.warning(f"Could not register pool in PoolManager: {e}")
    
    # Also try to register with Redis coordinator if available
    try:
        if hasattr(coordinator, '_local_pool'):
            coordinator._local_pool = pool
            logger.info(f"✅ Pool registered in Redis coordinator")
    except Exception as e:
        logger.warning(f"Could not register pool in Redis coordinator: {e}")
    
    logger.info(f"✅ External database pool registered in ALL locations: {pool}")

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
# Optional import for redis coordinator (graceful degradation)
try:
    from app.db.redis_pool_coordinator import coordinator
except ImportError:
    logger.warning("Redis pool coordinator not available - using local pool only")
    coordinator = None


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
    Get database connection pool.

    Priority order:
    1. External pool (registered via register_external_pool)
    2. Direct import from combined_server (if available)
    3. Module-level shared pool
    4. PoolManager singleton
    5. Redis coordinator

    Returns:
        AsyncPG connection pool

    Raises:
        RuntimeError: If pool not initialized
    """
    global _shared_pool, _external_pool
    
    # Add detailed logging to debug the issue
    logger.info(f"get_db_pool() called - Starting pool search...")
    logger.info(f"  _external_pool is {'set' if _external_pool is not None else 'None'}")
    logger.info(f"  _shared_pool is {'set' if _shared_pool is not None else 'None'}")
    
    # PRIORITY 1: Check external registered pool (most reliable for combined_server)
    if _external_pool is not None:
        logger.info("✅ Using externally registered pool")
        return _external_pool
    else:
        logger.info("❌ External pool not registered")
    
    # PRIORITY 2: Try direct import from combined_server (fixes module boundary issue)
    try:
        import sys
        logger.info(f"Checking sys.modules for combined_server...")
        # Check if combined_server is already imported
        if 'combined_server' in sys.modules:
            logger.info("combined_server found in sys.modules")
            import combined_server
            if hasattr(combined_server, 'db_pool'):
                logger.info(f"combined_server.db_pool attribute exists: {combined_server.db_pool is not None}")
                if combined_server.db_pool is not None:
                    logger.info("✅ Using pool directly from combined_server module")
                    return combined_server.db_pool
            else:
                logger.info("❌ combined_server doesn't have db_pool attribute")
        else:
            logger.info("❌ combined_server not in sys.modules")
    except Exception as e:
        logger.info(f"❌ Could not access combined_server.db_pool: {e}")
    
    # PRIORITY 3: Check module-level shared pool
    if _shared_pool is not None:
        logger.info("✅ Using module-level shared pool")
        return _shared_pool
    else:
        logger.info("❌ Module-level shared pool not set")
    
    # PRIORITY 4: Check PoolManager singleton
    pool_manager = PoolManager()
    if hasattr(pool_manager, '_pool') and pool_manager._pool is not None:
        logger.info("✅ Using pool from PoolManager singleton")
        return pool_manager._pool
    else:
        logger.info("❌ PoolManager singleton pool not initialized")
    
    # PRIORITY 5: Fallback to Redis coordinator (for backward compatibility)
    if coordinator is not None:
        try:
            pool = coordinator.get_pool_sync()
            if pool is not None:
                logger.info("✅ Using pool from Redis coordinator")
                return pool
            else:
                logger.info("❌ Redis coordinator pool is None")
        except Exception as e:
            logger.info(f"❌ Redis coordinator failed: {e}")
    else:
        logger.info("❌ Redis coordinator not available (module not imported)")

    # Pool not initialized yet - this is an error
    logger.error("❌ CRITICAL: No pool available from any source!")
    logger.error("  Attempted sources:")
    logger.error("    1. External pool (register_external_pool) - NOT FOUND")
    logger.error("    2. Direct import from combined_server - NOT FOUND")
    logger.error("    3. Module-level shared pool - NOT FOUND")
    logger.error("    4. PoolManager singleton - NOT FOUND")
    logger.error("    5. Redis coordinator - NOT FOUND")
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
