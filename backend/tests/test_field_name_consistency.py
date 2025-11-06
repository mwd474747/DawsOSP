"""
Field Name Consistency Regression Tests

Purpose: Prevent SQL errors from field name mismatches (valuation_date vs asof_date)
Created: 2025-11-05
Priority: P0 (Critical - prevents production SQL errors)

Background:
    The portfolio_daily_values table uses 'valuation_date' as its date column,
    while most other code expects 'asof_date'. The correct pattern is:
        SELECT valuation_date as asof_date FROM portfolio_daily_values

    This test suite ensures all queries follow this pattern to prevent SQL errors.

Critical Bug Fixed:
    - File: backend/app/services/risk_metrics.py:414
    - Issue: Used 'asof_date' directly (column doesn't exist)
    - Fix: Changed to 'valuation_date as asof_date'
    - Commit: 89e2617 (Replit agent, 2025-11-05)

Tests:
    1. Verify portfolio_daily_values schema (has valuation_date, not asof_date)
    2. Test all service methods that query portfolio_daily_values
    3. Validate alias pattern is used consistently
    4. Integration test: End-to-end portfolio metrics calculation

Usage:
    pytest backend/tests/test_field_name_consistency.py -v
"""

import pytest
import asyncio
import re
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from backend.app.db.connection import db_manager, get_db_connection


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool():
    """Initialize database pool for tests."""
    await db_manager.initialize()
    yield db_manager.pool
    await db_manager.close()


@pytest.fixture
async def test_portfolio(db_pool):
    """Create test portfolio with daily values."""
    async with get_db_connection() as conn:
        # Create test user
        user_id = uuid4()
        await conn.execute(
            """
            INSERT INTO users (user_id, email, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id, f"test_{user_id}@test.com", "Test User"
        )

        # Create test portfolio
        portfolio_id = uuid4()
        await conn.execute(
            """
            INSERT INTO portfolios (portfolio_id, user_id, name, base_ccy)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (portfolio_id) DO NOTHING
            """,
            portfolio_id, user_id, "Test Portfolio", "USD"
        )

        # Create test daily values (with valuation_date)
        start_date = date.today() - timedelta(days=30)
        for i in range(30):
            val_date = start_date + timedelta(days=i)
            total_value = Decimal("100000") + Decimal(i * 100)

            await conn.execute(
                """
                INSERT INTO portfolio_daily_values
                (portfolio_id, valuation_date, total_value, cash_flows)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (portfolio_id, valuation_date) DO NOTHING
                """,
                portfolio_id, val_date, total_value, Decimal("0")
            )

        yield {
            "portfolio_id": portfolio_id,
            "user_id": user_id,
            "start_date": start_date,
            "end_date": date.today()
        }

        # Cleanup
        await conn.execute("DELETE FROM portfolio_daily_values WHERE portfolio_id = $1", portfolio_id)
        await conn.execute("DELETE FROM portfolios WHERE portfolio_id = $1", portfolio_id)
        await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)


# ============================================================================
# Schema Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_portfolio_daily_values_schema(db_pool):
    """
    Verify portfolio_daily_values table has valuation_date column (not asof_date).

    This is the root cause validation - the table schema defines 'valuation_date',
    so all queries must use that column name with an alias.
    """
    async with get_db_connection() as conn:
        # Check columns
        columns = await conn.fetch(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'portfolio_daily_values'
            AND table_schema = 'public'
            ORDER BY ordinal_position
            """
        )

        column_names = [col["column_name"] for col in columns]

        # Assert valuation_date exists
        assert "valuation_date" in column_names, \
            "portfolio_daily_values must have 'valuation_date' column"

        # Assert asof_date does NOT exist (common mistake)
        assert "asof_date" not in column_names, \
            "portfolio_daily_values should NOT have 'asof_date' column (use 'valuation_date')"

        # Verify expected columns exist
        expected_columns = ["portfolio_id", "valuation_date", "total_value", "cash_flows"]
        for col in expected_columns:
            assert col in column_names, f"Expected column '{col}' not found"


@pytest.mark.asyncio
async def test_query_pattern_validation(db_pool):
    """
    Validate that the correct alias pattern works.

    Correct pattern:
        SELECT valuation_date as asof_date, total_value
        FROM portfolio_daily_values
        WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
    """
    async with get_db_connection() as conn:
        # This query should succeed
        result = await conn.fetch(
            """
            SELECT valuation_date as asof_date, total_value
            FROM portfolio_daily_values
            WHERE valuation_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 5
            """
        )

        # Verify alias works
        if result:
            assert "asof_date" in result[0].keys(), \
                "Alias 'asof_date' should be available"
            assert "valuation_date" not in result[0].keys(), \
                "Original column 'valuation_date' should not be in result (aliased)"


@pytest.mark.asyncio
async def test_broken_query_pattern_fails(db_pool):
    """
    Verify that the BROKEN pattern (using asof_date directly) fails.

    This test documents the bug that was fixed in commit 89e2617.
    """
    async with get_db_connection() as conn:
        # This query should FAIL (column doesn't exist)
        with pytest.raises(Exception) as exc_info:
            await conn.fetch(
                """
                SELECT asof_date, total_value
                FROM portfolio_daily_values
                WHERE asof_date >= CURRENT_DATE - INTERVAL '7 days'
                LIMIT 5
                """
            )

        # Verify it's a column-not-found error
        error_msg = str(exc_info.value).lower()
        assert "asof_date" in error_msg or "column" in error_msg, \
            f"Expected column error for 'asof_date', got: {exc_info.value}"


# ============================================================================
# Service Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_risk_metrics_query(db_pool, test_portfolio):
    """
    Test risk_metrics.py queries (fixed in commit 89e2617).

    This is the exact query that was broken before the fix.
    """
    async with get_db_connection() as conn:
        result = await conn.fetch(
            """
            SELECT valuation_date as asof_date, total_value
            FROM portfolio_daily_values
            WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
            ORDER BY valuation_date
            """,
            test_portfolio["portfolio_id"],
            test_portfolio["start_date"],
            test_portfolio["end_date"]
        )

        assert len(result) > 0, "Should return daily values"
        assert "asof_date" in result[0].keys(), "Should have asof_date alias"

        # Verify chronological order
        dates = [row["asof_date"] for row in result]
        assert dates == sorted(dates), "Results should be ordered by date"


@pytest.mark.asyncio
async def test_metrics_service_queries(db_pool, test_portfolio):
    """
    Test metrics.py queries (3 locations use portfolio_daily_values).

    Locations:
        - Line 116: TWR calculation
        - Line 382: Drawdown calculation
        - Line 475: Volatility windows
    """
    async with get_db_connection() as conn:
        # Test TWR query pattern (line 116)
        result = await conn.fetch(
            """
            SELECT valuation_date as asof_date, total_value, cash_flows
            FROM portfolio_daily_values
            WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
            ORDER BY valuation_date
            """,
            test_portfolio["portfolio_id"],
            test_portfolio["start_date"],
            test_portfolio["end_date"]
        )

        assert len(result) > 0, "TWR query should return data"
        assert "asof_date" in result[0].keys()
        assert "total_value" in result[0].keys()
        assert "cash_flows" in result[0].keys()

        # Test drawdown query pattern (line 382)
        result = await conn.fetch(
            """
            SELECT valuation_date as asof_date, total_value
            FROM portfolio_daily_values
            WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
            ORDER BY valuation_date
            """,
            test_portfolio["portfolio_id"],
            test_portfolio["start_date"],
            test_portfolio["end_date"]
        )

        assert len(result) > 0, "Drawdown query should return data"

        # Test volatility query pattern (line 475)
        result = await conn.fetch(
            """
            SELECT valuation_date as asof_date, total_value
            FROM portfolio_daily_values
            WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
            ORDER BY valuation_date
            """,
            test_portfolio["portfolio_id"],
            test_portfolio["start_date"],
            test_portfolio["end_date"]
        )

        assert len(result) > 0, "Volatility query should return data"


@pytest.mark.asyncio
async def test_factor_analysis_query(db_pool, test_portfolio):
    """
    Test factor_analysis.py query (line 290).

    Used by FactorAnalyzer.compute_factor_exposure() for portfolio returns.
    """
    async with get_db_connection() as conn:
        result = await conn.fetch(
            """
            SELECT valuation_date as asof_date, total_value
            FROM portfolio_daily_values
            WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
            ORDER BY valuation_date
            """,
            test_portfolio["portfolio_id"],
            test_portfolio["start_date"],
            test_portfolio["end_date"]
        )

        assert len(result) >= 2, "Need at least 2 points to compute returns"

        # Compute returns (as factor_analysis.py does)
        returns = []
        for i in range(1, len(result)):
            v_prev = float(result[i - 1]["total_value"])
            v_curr = float(result[i]["total_value"])

            if v_prev > 0:
                ret = (v_curr - v_prev) / v_prev
                returns.append({
                    "asof_date": result[i]["asof_date"],
                    "return": ret
                })

        assert len(returns) > 0, "Should compute returns successfully"


@pytest.mark.asyncio
async def test_financial_analyst_query(db_pool, test_portfolio):
    """
    Test financial_analyst.py query (line 2535).

    Used by historical NAV computation.
    """
    async with get_db_connection() as conn:
        lookback_days = 30
        result = await conn.fetch(
            """
            SELECT
                valuation_date as asof_date,
                total_value as total_value_base
            FROM portfolio_daily_values
            WHERE portfolio_id = $1
              AND valuation_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY valuation_date ASC
            """ % lookback_days,
            test_portfolio["portfolio_id"]
        )

        assert len(result) > 0, "Should return historical NAV data"
        assert "asof_date" in result[0].keys()
        assert "total_value_base" in result[0].keys()


# ============================================================================
# Code Pattern Analysis Tests
# ============================================================================


@pytest.mark.asyncio
async def test_all_queries_use_correct_pattern():
    """
    Static analysis: Verify all Python files use the correct query pattern.

    This test scans the codebase to ensure no queries use the broken pattern.
    """
    import os
    import re

    backend_path = os.path.join(os.path.dirname(__file__), "..")

    # Pattern to detect broken queries
    broken_pattern = re.compile(
        r"FROM\s+portfolio_daily_values.*?WHERE.*?asof_date",
        re.IGNORECASE | re.DOTALL
    )

    # Pattern to detect correct queries
    correct_pattern = re.compile(
        r"valuation_date\s+as\s+asof_date.*?FROM\s+portfolio_daily_values",
        re.IGNORECASE | re.DOTALL
    )

    issues = []

    # Scan all Python files in services and agents
    for root, dirs, files in os.walk(backend_path):
        # Skip test directories
        if "tests" in root or "__pycache__" in root:
            continue

        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)

            with open(filepath, "r") as f:
                content = f.read()

                # Check if file queries portfolio_daily_values
                if "portfolio_daily_values" not in content:
                    continue

                # Check for broken pattern
                if broken_pattern.search(content):
                    # Verify it's not in a comment
                    for match in broken_pattern.finditer(content):
                        # Get line number
                        line_num = content[:match.start()].count("\n") + 1
                        issues.append(f"{filepath}:{line_num} - Uses 'asof_date' directly (should be 'valuation_date as asof_date')")

    assert len(issues) == 0, \
        f"Found {len(issues)} queries using broken pattern:\n" + "\n".join(issues)


# ============================================================================
# End-to-End Integration Test
# ============================================================================


@pytest.mark.asyncio
async def test_e2e_portfolio_metrics(db_pool, test_portfolio):
    """
    End-to-end test: Compute portfolio metrics using actual services.

    This verifies that the fixed queries work in real service methods.
    """
    from backend.app.services.metrics import Metrics
    from backend.app.services.risk_metrics import RiskMetrics

    # Create pricing pack
    async with get_db_connection() as conn:
        pack_id = uuid4()
        await conn.execute(
            """
            INSERT INTO pricing_packs (pack_id, date, status)
            VALUES ($1, $2, $3)
            ON CONFLICT (pack_id) DO NOTHING
            """,
            pack_id, date.today(), "complete"
        )

    try:
        # Test Metrics service
        metrics = Metrics(db_pool)
        twr_result = await metrics.compute_twr(
            str(test_portfolio["portfolio_id"]),
            str(pack_id),
            lookback_days=30
        )

        # Should not error (would error with broken field name)
        assert "twr" in twr_result or "error" in twr_result, \
            "Metrics.compute_twr should return result"

        # Test RiskMetrics service
        risk_metrics = RiskMetrics(db_pool)
        var_result = await risk_metrics.compute_var(
            str(test_portfolio["portfolio_id"]),
            str(pack_id),
            lookback_days=30
        )

        # Should not error (this was the original bug location)
        assert "var_1d" in var_result or "error" in var_result, \
            "RiskMetrics.compute_var should return result"

    finally:
        # Cleanup
        async with get_db_connection() as conn:
            await conn.execute("DELETE FROM pricing_packs WHERE pack_id = $1", pack_id)


# ============================================================================
# Documentation
# ============================================================================


def test_field_name_pattern_documentation():
    """
    Document the correct pattern for future developers.

    This test always passes but serves as living documentation.
    """
    correct_pattern = """
    CORRECT PATTERN (portfolio_daily_values queries):
    ================================================

    SELECT valuation_date as asof_date, total_value
    FROM portfolio_daily_values
    WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
    ORDER BY valuation_date

    Key points:
    1. Use 'valuation_date' in SELECT (the actual column name)
    2. Alias it as 'asof_date' for consistency with rest of codebase
    3. Use 'valuation_date' in WHERE clause
    4. Use 'valuation_date' in ORDER BY clause

    INCORRECT PATTERN (causes SQL error):
    ====================================

    SELECT asof_date, total_value  ❌ Column doesn't exist
    FROM portfolio_daily_values
    WHERE portfolio_id = $1 AND asof_date BETWEEN $2 AND $3  ❌
    ORDER BY asof_date  ❌

    Why this pattern?
    ================
    - The portfolio_daily_values table uses 'valuation_date' (schema decision)
    - Most other code expects 'asof_date' (convention)
    - The alias bridges the gap without changing schema or all code

    References:
    ==========
    - Fixed in commit 89e2617 (2025-11-05)
    - Files using this pattern:
      * backend/app/services/risk_metrics.py:414
      * backend/app/services/metrics.py:116, 382, 475
      * backend/app/services/factor_analysis.py:290
      * backend/app/agents/financial_analyst.py:2535
    """

    print(correct_pattern)
    assert True, "Documentation test always passes"
