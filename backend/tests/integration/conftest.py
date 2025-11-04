"""
Integration Test Infrastructure

Purpose: Shared fixtures for DawsOS integration tests
Created: 2025-10-23
Priority: P0 (Critical for UAT testing)

Fixtures:
    - Database setup/teardown (test database)
    - Test user creation (2+ users for RLS testing)
    - Test portfolio setup (with sample trades)
    - API client fixtures (authenticated requests)
    - Pricing pack fixtures (test pack with known prices)
    - Cleanup functions (rollback after each test)

Usage:
    pytest backend/tests/integration/ -v
"""

import asyncio
import asyncpg
import os
import pytest
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import AsyncGenerator, Dict, List, Optional
from uuid import UUID, uuid4
from httpx import AsyncClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DawsOS.IntegrationTests")


# ============================================================================
# Test Configuration
# ============================================================================

# Test database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos_test"
)

# Test user IDs (fixed UUIDs for predictable testing)
USER_A_ID = "00000000-0000-0000-0000-000000000001"
USER_B_ID = "00000000-0000-0000-0000-000000000002"

# Test portfolio IDs
PORTFOLIO_A1_ID = "11111111-1111-1111-1111-111111111111"
PORTFOLIO_A2_ID = "11111111-1111-1111-1111-111111111112"
PORTFOLIO_B1_ID = "22222222-2222-2222-2222-222222222221"

# Test security IDs
AAPL_SECURITY_ID = "33333333-3333-3333-3333-333333333301"
GOOGL_SECURITY_ID = "33333333-3333-3333-3333-333333333302"
MSFT_SECURITY_ID = "33333333-3333-3333-3333-333333333303"
SPY_SECURITY_ID = "33333333-3333-3333-3333-333333333304"


# ============================================================================
# Event Loop Fixture (Session-scoped)
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests (session-scoped).

    This allows sharing async resources across all tests in a session.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ============================================================================
# Database Pool Fixture (Session-scoped)
# ============================================================================

@pytest.fixture(scope="session")
async def db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """
    Create database connection pool for tests (session-scoped).

    Yields:
        AsyncPG connection pool
    """
    logger.info(f"Creating test database pool: {TEST_DATABASE_URL}")

    pool = await asyncpg.create_pool(
        TEST_DATABASE_URL,
        min_size=5,
        max_size=20,
        command_timeout=60.0
    )

    # Verify connection
    async with pool.acquire() as conn:
        version = await conn.fetchval("SELECT version()")
        logger.info(f"Connected to test database: {version}")

    yield pool

    # Cleanup
    logger.info("Closing test database pool")
    await pool.close()


# ============================================================================
# Database Schema Fixture (Session-scoped)
# ============================================================================

@pytest.fixture(scope="session")
async def db_schema(db_pool: asyncpg.Pool):
    """
    Apply database schema to test database (session-scoped).

    This ensures all tables, indexes, and functions are created before tests run.
    """
    logger.info("Verifying database schema")

    async with db_pool.acquire() as conn:
        # Check required tables exist
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN (
                'portfolios', 'lots', 'transactions',
                'portfolio_metrics', 'currency_attribution',
                'pricing_packs', 'pricing_pack_prices',
                'ledger_reconciliations'
              )
            ORDER BY table_name
        """)

        table_names = [row['table_name'] for row in tables]
        logger.info(f"Found tables: {table_names}")

        required_tables = {
            'portfolios', 'lots', 'transactions',
            'portfolio_metrics', 'pricing_packs'
        }

        missing_tables = required_tables - set(table_names)
        if missing_tables:
            raise RuntimeError(
                f"Missing required tables: {missing_tables}. "
                "Run migrations before running integration tests."
            )

    logger.info("Database schema verified")
    yield


# ============================================================================
# Transaction Fixture (Function-scoped - Rollback after each test)
# ============================================================================

@pytest.fixture
async def db_transaction(db_pool: asyncpg.Pool, db_schema):
    """
    Create transaction for each test (function-scoped).

    All database changes are rolled back after each test, ensuring test isolation.

    Yields:
        AsyncPG connection with active transaction
    """
    async with db_pool.acquire() as conn:
        # Start transaction
        transaction = conn.transaction()
        await transaction.start()

        logger.debug("Test transaction started")

        try:
            yield conn
        finally:
            # Rollback transaction (cleanup)
            await transaction.rollback()
            logger.debug("Test transaction rolled back")


# ============================================================================
# Test Users Fixture
# ============================================================================

@pytest.fixture
async def test_users(db_transaction: asyncpg.Connection) -> Dict[str, UUID]:
    """
    Create test users (function-scoped).

    Creates two users for RLS isolation testing:
    - User A: Primary test user
    - User B: Secondary user (for isolation tests)

    Returns:
        Dict with user_a and user_b UUIDs
    """
    # Note: In a real system, users would be in a separate 'users' table
    # For integration tests, we just use the user_id directly

    users = {
        "user_a": UUID(USER_A_ID),
        "user_b": UUID(USER_B_ID)
    }

    logger.info(f"Test users: user_a={users['user_a']}, user_b={users['user_b']}")

    return users


# ============================================================================
# Test Portfolios Fixture
# ============================================================================

@pytest.fixture
async def test_portfolios(
    db_transaction: asyncpg.Connection,
    test_users: Dict[str, UUID]
) -> Dict[str, UUID]:
    """
    Create test portfolios (function-scoped).

    Creates:
    - User A: 2 portfolios (multi-portfolio testing)
    - User B: 1 portfolio (RLS isolation testing)

    Returns:
        Dict with portfolio IDs
    """
    portfolios = {}

    # User A - Portfolio 1 (USD)
    await db_transaction.execute("""
        INSERT INTO portfolios (id, user_id, name, description, base_currency, benchmark_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, UUID(PORTFOLIO_A1_ID), test_users["user_a"], "User A Portfolio 1",
        "Primary USD portfolio", "USD", "SPY", True)
    portfolios["a1"] = UUID(PORTFOLIO_A1_ID)

    # User A - Portfolio 2 (CAD)
    await db_transaction.execute("""
        INSERT INTO portfolios (id, user_id, name, description, base_currency, benchmark_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, UUID(PORTFOLIO_A2_ID), test_users["user_a"], "User A Portfolio 2",
        "Secondary CAD portfolio", "CAD", "SPY", True)
    portfolios["a2"] = UUID(PORTFOLIO_A2_ID)

    # User B - Portfolio 1 (USD)
    await db_transaction.execute("""
        INSERT INTO portfolios (id, user_id, name, description, base_currency, benchmark_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, UUID(PORTFOLIO_B1_ID), test_users["user_b"], "User B Portfolio 1",
        "User B primary portfolio", "USD", "SPY", True)
    portfolios["b1"] = UUID(PORTFOLIO_B1_ID)

    logger.info(f"Created {len(portfolios)} test portfolios")

    return portfolios


# ============================================================================
# Test Trades Fixture (with lots)
# ============================================================================

@pytest.fixture
async def test_trades(
    db_transaction: asyncpg.Connection,
    test_portfolios: Dict[str, UUID]
) -> Dict[str, List[Dict]]:
    """
    Create test trades and lots (function-scoped).

    Creates sample trades for User A Portfolio 1:
    - Buy 100 AAPL @ $150 (2024-01-15)
    - Buy 50 GOOGL @ $140 (2024-02-01)
    - Sell 30 AAPL @ $160 (2024-03-01) - FIFO from first lot
    - Dividend AAPL $50 (2024-03-15)

    Returns:
        Dict with trade and lot data
    """
    portfolio_id = test_portfolios["a1"]
    trades = []
    lots = []

    # Trade 1: Buy 100 AAPL @ $150
    trade1_id = uuid4()
    lot1_id = uuid4()

    await db_transaction.execute("""
        INSERT INTO transactions (
            id, portfolio_id, transaction_type, security_id, symbol,
            transaction_date, settlement_date, quantity, price, amount,
            currency, fee, commission, source
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    """, trade1_id, portfolio_id, "BUY", UUID(AAPL_SECURITY_ID), "AAPL",
        date(2024, 1, 15), date(2024, 1, 17), Decimal("100"), Decimal("150.00"),
        Decimal("-15000.00"), "USD", Decimal("0"), Decimal("0"), "manual")

    await db_transaction.execute("""
        INSERT INTO lots (
            id, portfolio_id, security_id, symbol, acquisition_date,
            quantity, quantity_original, quantity_open, cost_basis, cost_basis_per_share,
            currency, is_open
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """, lot1_id, portfolio_id, UUID(AAPL_SECURITY_ID), "AAPL", date(2024, 1, 15),
        Decimal("100"), Decimal("100"), Decimal("100"), Decimal("15000.00"),
        Decimal("150.00"), "USD", True)

    trades.append({
        "id": trade1_id, "type": "BUY", "symbol": "AAPL",
        "qty": Decimal("100"), "price": Decimal("150.00"),
        "lot_id": lot1_id
    })

    lots.append({
        "id": lot1_id, "symbol": "AAPL", "quantity_open": Decimal("100"),
        "cost_basis": Decimal("15000.00")
    })

    # Trade 2: Buy 50 GOOGL @ $140
    trade2_id = uuid4()
    lot2_id = uuid4()

    await db_transaction.execute("""
        INSERT INTO transactions (
            id, portfolio_id, transaction_type, security_id, symbol,
            transaction_date, settlement_date, quantity, price, amount,
            currency, fee, commission, source
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    """, trade2_id, portfolio_id, "BUY", UUID(GOOGL_SECURITY_ID), "GOOGL",
        date(2024, 2, 1), date(2024, 2, 3), Decimal("50"), Decimal("140.00"),
        Decimal("-7000.00"), "USD", Decimal("0"), Decimal("0"), "manual")

    await db_transaction.execute("""
        INSERT INTO lots (
            id, portfolio_id, security_id, symbol, acquisition_date,
            quantity, quantity_original, quantity_open, cost_basis, cost_basis_per_share,
            currency, is_open
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """, lot2_id, portfolio_id, UUID(GOOGL_SECURITY_ID), "GOOGL", date(2024, 2, 1),
        Decimal("50"), Decimal("50"), Decimal("50"), Decimal("7000.00"),
        Decimal("140.00"), "USD", True)

    trades.append({
        "id": trade2_id, "type": "BUY", "symbol": "GOOGL",
        "qty": Decimal("50"), "price": Decimal("140.00"),
        "lot_id": lot2_id
    })

    lots.append({
        "id": lot2_id, "symbol": "GOOGL", "quantity_open": Decimal("50"),
        "cost_basis": Decimal("7000.00")
    })

    # Trade 3: Sell 30 AAPL @ $160 (reduce lot1)
    trade3_id = uuid4()

    await db_transaction.execute("""
        INSERT INTO transactions (
            id, portfolio_id, transaction_type, security_id, symbol,
            transaction_date, settlement_date, quantity, price, amount,
            currency, fee, commission, lot_id, source
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
    """, trade3_id, portfolio_id, "SELL", UUID(AAPL_SECURITY_ID), "AAPL",
        date(2024, 3, 1), date(2024, 3, 3), Decimal("-30"), Decimal("160.00"),
        Decimal("4800.00"), "USD", Decimal("0"), Decimal("0"), lot1_id, "manual")

    # Update lot1 quantity_open (100 - 30 = 70)
    await db_transaction.execute("""
        UPDATE lots
        SET quantity_open = $1, quantity = $2, updated_at = NOW()
        WHERE id = $3
    """, Decimal("70"), Decimal("70"), lot1_id)

    trades.append({
        "id": trade3_id, "type": "SELL", "symbol": "AAPL",
        "qty": Decimal("30"), "price": Decimal("160.00"),
        "lot_id": lot1_id
    })

    # Update lots data
    lots[0]["quantity_open"] = Decimal("70")

    # Trade 4: Dividend AAPL $50
    trade4_id = uuid4()

    await db_transaction.execute("""
        INSERT INTO transactions (
            id, portfolio_id, transaction_type, security_id, symbol,
            transaction_date, amount, currency, source, narration
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """, trade4_id, portfolio_id, "DIVIDEND", UUID(AAPL_SECURITY_ID), "AAPL",
        date(2024, 3, 15), Decimal("50.00"), "USD", "manual", "Quarterly dividend")

    trades.append({
        "id": trade4_id, "type": "DIVIDEND", "symbol": "AAPL",
        "amount": Decimal("50.00")
    })

    logger.info(f"Created {len(trades)} test trades and {len(lots)} lots")

    return {
        "trades": trades,
        "lots": lots
    }


# ============================================================================
# Test Pricing Pack Fixture
# ============================================================================

@pytest.fixture
async def test_pricing_pack(
    db_transaction: asyncpg.Connection
) -> Dict:
    """
    Create test pricing pack with known prices (function-scoped).

    Returns:
        Dict with pricing pack data
    """
    pack_id = "PP_2025-10-23_TEST"
    pack_date = date.today()

    # Create pricing pack
    await db_transaction.execute("""
        INSERT INTO pricing_packs (id, date, is_fresh, created_at)
        VALUES ($1, $2, $3, NOW())
    """, pack_id, pack_date, True)

    # Add prices for test securities
    prices = [
        {"symbol": "AAPL", "price": Decimal("175.50"), "currency": "USD"},
        {"symbol": "GOOGL", "price": Decimal("145.00"), "currency": "USD"},
        {"symbol": "MSFT", "price": Decimal("380.25"), "currency": "USD"},
        {"symbol": "SPY", "price": Decimal("450.00"), "currency": "USD"},
    ]

    for p in prices:
        await db_transaction.execute("""
            INSERT INTO pricing_pack_prices (
                pricing_pack_id, symbol, price, currency, source, created_at
            )
            VALUES ($1, $2, $3, $4, $5, NOW())
        """, pack_id, p["symbol"], p["price"], p["currency"], "test")

    # Add FX rates
    fx_rates = [
        {"from_ccy": "USD", "to_ccy": "USD", "rate": Decimal("1.0000")},
        {"from_ccy": "USD", "to_ccy": "CAD", "rate": Decimal("1.3500")},
        {"from_ccy": "CAD", "to_ccy": "USD", "rate": Decimal("0.7407")},
    ]

    for fx in fx_rates:
        await db_transaction.execute("""
            INSERT INTO pricing_pack_fx_rates (
                pricing_pack_id, from_currency, to_currency, rate, source, created_at
            )
            VALUES ($1, $2, $3, $4, $5, NOW())
        """, pack_id, fx["from_ccy"], fx["to_ccy"], fx["rate"], "test")

    logger.info(f"Created pricing pack: {pack_id} with {len(prices)} prices and {len(fx_rates)} FX rates")

    return {
        "id": pack_id,
        "date": pack_date,
        "prices": prices,
        "fx_rates": fx_rates
    }


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create HTTP client for API testing (function-scoped).

    Yields:
        HTTPX async client
    """
    from app.api.executor import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def user_a_headers(test_users: Dict[str, UUID]) -> Dict[str, str]:
    """
    Get HTTP headers for User A (for authenticated requests).

    Returns:
        Dict with X-User-ID header
    """
    return {"X-User-ID": str(test_users["user_a"])}


@pytest.fixture
def user_b_headers(test_users: Dict[str, UUID]) -> Dict[str, str]:
    """
    Get HTTP headers for User B (for authenticated requests).

    Returns:
        Dict with X-User-ID header
    """
    return {"X-User-ID": str(test_users["user_b"])}


# ============================================================================
# RLS Connection Fixtures
# ============================================================================

@pytest.fixture
async def user_a_conn(
    db_transaction: asyncpg.Connection,
    test_users: Dict[str, UUID]
) -> asyncpg.Connection:
    """
    Get database connection with RLS context for User A.

    Returns:
        Connection with app.user_id set to User A
    """
    await db_transaction.execute(
        f"SET LOCAL app.user_id = '{test_users['user_a']}'"
    )
    return db_transaction


@pytest.fixture
async def user_b_conn(
    db_transaction: asyncpg.Connection,
    test_users: Dict[str, UUID]
) -> asyncpg.Connection:
    """
    Get database connection with RLS context for User B.

    Returns:
        Connection with app.user_id set to User B
    """
    await db_transaction.execute(
        f"SET LOCAL app.user_id = '{test_users['user_b']}'"
    )
    return db_transaction


# ============================================================================
# Helper Functions
# ============================================================================

async def verify_rls_isolation(
    conn: asyncpg.Connection,
    user_id: UUID,
    table: str,
    expected_count: int
) -> bool:
    """
    Verify RLS policy filters data correctly.

    Args:
        conn: Database connection with RLS context set
        user_id: Expected user_id for RLS filtering
        table: Table name to check
        expected_count: Expected row count for this user

    Returns:
        True if RLS is working correctly
    """
    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")

    if count != expected_count:
        logger.error(
            f"RLS isolation failed for {table}: "
            f"expected {expected_count} rows, got {count}"
        )
        return False

    return True


def assert_decimal_equal(actual: Decimal, expected: Decimal, tolerance: Decimal = Decimal("0.01")):
    """
    Assert two decimals are equal within tolerance.

    Args:
        actual: Actual value
        expected: Expected value
        tolerance: Tolerance (default: 0.01)

    Raises:
        AssertionError: If values differ by more than tolerance
    """
    diff = abs(actual - expected)
    if diff > tolerance:
        raise AssertionError(
            f"Decimals not equal: {actual} != {expected} "
            f"(diff: {diff}, tolerance: {tolerance})"
        )


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest for integration tests.
    """
    config.addinivalue_line(
        "markers", "integration: Integration tests (require test database)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "rls: RLS security tests"
    )
    config.addinivalue_line(
        "markers", "uat: User Acceptance Tests (P0)"
    )
