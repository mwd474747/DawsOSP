"""
Redis Pool Coordinator

Purpose: Coordinate database pool initialization across Python module instances
Updated: 2025-10-24
Priority: P0 (Critical - fixes pool access issue)

Problem:
    Python's import system creates separate module instances in different
    contexts (API startup vs agent code), causing separate PoolManager
    instances even with singleton pattern.

Solution:
    Use Redis as external coordination layer. Each module instance maintains
    its own AsyncPG pool, but Redis tracks pool initialization state and
    configuration to ensure consistency.

Architecture:
    - Redis stores pool configuration (database_url, min_size, max_size)
    - Each module instance creates its own AsyncPG pool with same config
    - Redis acts as "source of truth" for pool state
    - No serialization of pool objects (AsyncPG pools can't be pickled)

Usage:
    from app.db.redis_pool_coordinator import coordinator

    # Initialize (sets config in Redis + creates local pool)
    pool = await coordinator.initialize(database_url, min_size=5, max_size=20)

    # Get pool (creates local pool if needed, using config from Redis)
    pool = await coordinator.get_pool()
"""

import asyncpg
import redis
import logging
import os
import json
from typing import Optional, Dict, Any

logger = logging.getLogger("DawsOS.RedisPoolCoordinator")


class RedisPoolCoordinator:
    """
    Coordinates database pool initialization across module instances via Redis.

    Each Python module instance maintains its own AsyncPG pool, but Redis
    stores the configuration to ensure all instances use the same settings.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize coordinator with Redis connection.

        Args:
            redis_url: Redis connection URL (default: from REDIS_URL env or localhost)
        """
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            self._redis = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self._redis.ping()
            logger.info(f"Redis pool coordinator connected: {redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Pool coordination disabled.")
            self._redis = None

        self._config_key = "dawsos:db_pool:config"
        self._state_key = "dawsos:db_pool:state"
        self._local_pool: Optional[asyncpg.Pool] = None

    async def initialize(
        self,
        database_url: str,
        min_size: int = 5,
        max_size: int = 20,
        command_timeout: float = 60.0,
        max_inactive_connection_lifetime: float = 300.0,
    ) -> asyncpg.Pool:
        """
        Initialize database pool and store config in Redis.

        This creates a local AsyncPG pool and stores the configuration in Redis
        so other module instances can create their own pools with the same settings.

        Args:
            database_url: PostgreSQL connection URL
            min_size: Minimum pool size
            max_size: Maximum pool size
            command_timeout: Command timeout in seconds
            max_inactive_connection_lifetime: Max inactive connection lifetime

        Returns:
            AsyncPG connection pool

        Raises:
            asyncpg.PostgresError: If connection fails
        """
        # Check if local pool already exists
        if self._local_pool is not None:
            logger.info("Local pool already initialized, returning existing pool")
            return self._local_pool

        logger.info(f"Initializing database connection pool (min={min_size}, max={max_size})")

        # Create local pool
        try:
            self._local_pool = await asyncpg.create_pool(
                database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=command_timeout,
                max_inactive_connection_lifetime=max_inactive_connection_lifetime,
            )

            logger.info("Database connection pool initialized successfully")

            # Test connection
            async with self._local_pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"Database connected: {version}")

        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}", exc_info=True)
            raise

        # Store configuration in Redis (for other module instances)
        if self._redis is not None:
            config = {
                "database_url": database_url,
                "min_size": min_size,
                "max_size": max_size,
                "command_timeout": command_timeout,
                "max_inactive_connection_lifetime": max_inactive_connection_lifetime,
            }

            try:
                self._redis.set(self._config_key, json.dumps(config), ex=3600)
                self._redis.set(self._state_key, "initialized", ex=3600)
                logger.info("Pool configuration stored in Redis")
            except Exception as e:
                logger.warning(f"Failed to store config in Redis: {e}")

        return self._local_pool

    async def get_pool(self) -> asyncpg.Pool:
        """
        Get database pool, creating it if necessary using config from Redis.

        If local pool doesn't exist, retrieves configuration from Redis and
        creates a new pool with those settings.

        Returns:
            AsyncPG connection pool

        Raises:
            RuntimeError: If pool not initialized and no config in Redis
        """
        # Return local pool if it exists
        if self._local_pool is not None:
            return self._local_pool

        # Try to create pool from Redis config
        if self._redis is not None:
            try:
                config_json = self._redis.get(self._config_key)
                if config_json:
                    config = json.loads(config_json)
                    logger.info("Creating local pool from Redis configuration")

                    self._local_pool = await asyncpg.create_pool(
                        config["database_url"],
                        min_size=config["min_size"],
                        max_size=config["max_size"],
                        command_timeout=config["command_timeout"],
                        max_inactive_connection_lifetime=config[
                            "max_inactive_connection_lifetime"
                        ],
                    )

                    logger.info("Local pool created from Redis config")
                    return self._local_pool

            except Exception as e:
                logger.error(f"Failed to create pool from Redis config: {e}", exc_info=True)

        # No local pool and no Redis config
        raise RuntimeError(
            "Database pool not initialized. Call initialize() first or ensure "
            "pool is initialized in API startup."
        )

    def get_pool_sync(self) -> Optional[asyncpg.Pool]:
        """
        Get database pool synchronously (returns None if not initialized).

        This is a synchronous variant that doesn't attempt to create the pool.
        Use this only when you're sure the pool should already exist.

        Returns:
            AsyncPG connection pool or None
        """
        return self._local_pool

    async def close(self):
        """
        Close local database connection pool and clear Redis state.

        Gracefully closes the local pool connection and clears configuration
        from Redis.
        """
        if self._local_pool is None:
            logger.warning("Local pool not initialized, nothing to close")
            return

        logger.info("Closing local database connection pool")

        try:
            await self._local_pool.close()
            self._local_pool = None
            logger.info("Local database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing local pool: {e}", exc_info=True)

        # Clear Redis state
        if self._redis is not None:
            try:
                self._redis.delete(self._config_key, self._state_key)
                logger.info("Pool configuration cleared from Redis")
            except Exception as e:
                logger.warning(f"Failed to clear Redis config: {e}")


# Global coordinator instance
coordinator = RedisPoolCoordinator()
