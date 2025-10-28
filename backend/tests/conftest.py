"""
Alternative Test Infrastructure - Manual Cleanup Approach

This module provides test infrastructure that avoids async loop conflicts by using manual cleanup.
Created: 2025-10-27
Purpose: Resolve pytest-asyncio and asyncpg transaction conflicts
"""

import pytest
import pytest_asyncio
import asyncio
import os
from typing import AsyncGenerator, List
from uuid import uuid4

# Set test database URL
os.environ["DATABASE_URL"] = "postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos"

from app.db.connection import init_db_pool


@pytest_asyncio.fixture(scope="session")
async def db_pool():
    """Create a database connection pool for the test session."""
    pool = await init_db_pool()
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def db_connection(db_pool) -> AsyncGenerator:
    """Get a database connection without transaction management."""
    async with db_pool.acquire() as conn:
        yield conn


@pytest_asyncio.fixture
async def auth_service():
    """Get auth service instance."""
    from app.services.auth import get_auth_service
    return get_auth_service()


@pytest_asyncio.fixture
async def reports_service():
    """Get reports service instance."""
    from app.services.reports import get_reports_service
    return get_reports_service()


@pytest_asyncio.fixture
async def test_user_id(db_connection):
    """Create a test user and return the user ID."""
    user_id = uuid4()
    email = f"test-{user_id}@dawsos.com"
    
    # Create test user
    await db_connection.execute(
        """
        INSERT INTO users (id, email, role, permissions, is_active, password_hash, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """,
        user_id, email, "USER", [], True, "$2b$12$test_hash_placeholder"
    )
    
    yield str(user_id)
    
    # Manual cleanup
    try:
        await db_connection.execute("DELETE FROM audit_log WHERE user_id = $1", user_id)
        await db_connection.execute("DELETE FROM users WHERE id = $1", user_id)
    except Exception as e:
        print(f"Cleanup warning: {e}")


@pytest_asyncio.fixture
async def test_portfolio_id(db_connection):
    """Create a test portfolio and return the portfolio ID."""
    portfolio_id = uuid4()
    
    # Create test portfolio
    await db_connection.execute(
        """
        INSERT INTO portfolios (id, name, base_currency, created_at)
        VALUES ($1, $2, $3, NOW())
        """,
        portfolio_id, "Test Portfolio", "CAD"
    )
    
    yield str(portfolio_id)
    
    # Manual cleanup
    try:
        await db_connection.execute("DELETE FROM portfolios WHERE id = $1", portfolio_id)
    except Exception as e:
        print(f"Cleanup warning: {e}")


@pytest_asyncio.fixture
async def cleanup_tracker(db_connection):
    """Track created records for cleanup."""
    created_records = []
    
    yield created_records
    
    # Cleanup all tracked records
    for record_type, record_id in created_records:
        try:
            if record_type == "user":
                await db_connection.execute("DELETE FROM audit_log WHERE user_id = $1", record_id)
                await db_connection.execute("DELETE FROM users WHERE id = $1", record_id)
            elif record_type == "portfolio":
                await db_connection.execute("DELETE FROM portfolios WHERE id = $1", record_id)
        except Exception as e:
            print(f"Cleanup warning for {record_type} {record_id}: {e}")
