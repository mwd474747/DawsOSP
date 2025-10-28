"""
Core Database Module for DawsOS

Purpose: Provides database connection dependencies for FastAPI and pattern orchestration
Updated: 2025-10-28
Priority: P0 (Critical for pattern execution)

Features:
    - FastAPI dependency injection
    - Database connection management
    - Pattern orchestration integration
    - Health checks and monitoring

Usage:
    from app.core.database import get_db_connection, init_database
    
    # Initialize at startup
    await init_database()
    
    # Use in FastAPI endpoints
    @app.get("/endpoint")
    async def endpoint(conn: asyncpg.Connection = Depends(get_db_connection)):
        result = await conn.fetchrow("SELECT * FROM table")
        return result
"""

import os
import logging
from typing import AsyncGenerator
import asyncpg
from fastapi import Depends
from app.db.connection import get_db_pool, init_db_pool

logger = logging.getLogger(__name__)

# Global database pool instance
_db_pool = None

async def init_database() -> None:
    """
    Initialize database connection pool.
    
    This should be called at application startup.
    """
    global _db_pool
    
    try:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.warning("DATABASE_URL not set, using default")
            database_url = "postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos"
        
        # Initialize the database pool
        await init_db_pool(database_url)
        _db_pool = get_db_pool()
        
        logger.info("Database connection pool initialized successfully")
        
        # Test the connection
        async with _db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            logger.info(f"Database health check passed: {result}")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    FastAPI dependency for database connections.
    
    Yields:
        asyncpg.Connection: Database connection from the pool
        
    Usage:
        @app.get("/endpoint")
        async def endpoint(conn: asyncpg.Connection = Depends(get_db_connection)):
            result = await conn.fetchrow("SELECT * FROM table")
            return result
    """
    if _db_pool is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with _db_pool.acquire() as conn:
        yield conn

async def get_db_pool_instance():
    """
    Get the database pool instance for pattern orchestration.
    
    Returns:
        asyncpg.Pool: Database connection pool
    """
    if _db_pool is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return _db_pool

async def health_check() -> dict:
    """
    Perform database health check.
    
    Returns:
        dict: Health check results
    """
    try:
        if _db_pool is None:
            return {"status": "error", "message": "Database not initialized"}
        
        async with _db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            
        return {
            "status": "healthy",
            "message": "Database connection successful",
            "test_query_result": result
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "message": f"Database health check failed: {str(e)}"
        }

# Convenience function for pattern orchestration
def get_db_for_patterns():
    """
    Get database connection for pattern orchestration.
    
    This is a synchronous wrapper for the async database pool.
    Pattern orchestration needs this for initialization.
    """
    return _db_pool
