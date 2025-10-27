"""
Unit Test Fixtures

Purpose: Shared fixtures for DawsOS unit tests
Created: 2025-10-27
Priority: P0 (Critical for comprehensive testing)

Fixtures:
    - Mock database connections
    - Mock service dependencies
    - Sample data generators
    - Decimal comparison utilities
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Dict, List, Any
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================================
# Mock Database Fixtures
# ============================================================================

@pytest.fixture
def mock_db_pool():
    """Mock AsyncPG pool for unit tests."""
    pool = AsyncMock()

    # Mock acquire context manager
    connection = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = connection
    pool.acquire.return_value.__aexit__.return_value = None

    return pool


@pytest.fixture
def mock_db_connection():
    """Mock AsyncPG connection for unit tests."""
    conn = AsyncMock()

    # Common query mocks
    conn.fetchval = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    conn.execute = AsyncMock()

    return conn


# ============================================================================
# Sample Data Generators
# ============================================================================

@pytest.fixture
def sample_portfolio_id() -> UUID:
    """Return fixed portfolio ID for testing."""
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def sample_user_id() -> UUID:
    """Return fixed user ID for testing."""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_fundamentals() -> Dict[str, Any]:
    """Return sample fundamental data for testing."""
    return {
        "payout_ratio_5y_avg": Decimal("0.35"),
        "fcf_dividend_coverage": Decimal("2.5"),
        "dividend_growth_streak_years": 10,
        "net_cash_position": Decimal("20000000000"),
        "roic_5y_avg": Decimal("0.18"),
        "moat_score": Decimal("8.5"),
        "debt_to_equity": Decimal("0.45"),
        "interest_coverage": Decimal("12.0"),
        "current_ratio": Decimal("1.8"),
        "ebit_margin": Decimal("0.22")
    }


@pytest.fixture
def sample_positions() -> List[Dict[str, Any]]:
    """Return sample portfolio positions for testing."""
    return [
        {
            "symbol": "AAPL",
            "quantity": Decimal("100"),
            "cost_basis": Decimal("15000.00"),
            "cost_basis_per_share": Decimal("150.00"),
            "currency": "USD"
        },
        {
            "symbol": "GOOGL",
            "quantity": Decimal("50"),
            "cost_basis": Decimal("7000.00"),
            "cost_basis_per_share": Decimal("140.00"),
            "currency": "USD"
        },
        {
            "symbol": "MSFT",
            "quantity": Decimal("75"),
            "cost_basis": Decimal("22500.00"),
            "cost_basis_per_share": Decimal("300.00"),
            "currency": "USD"
        }
    ]


@pytest.fixture
def sample_pricing_pack() -> Dict[str, Any]:
    """Return sample pricing pack for testing."""
    return {
        "id": "PP_2025-10-27_TEST",
        "date": date.today(),
        "prices": {
            "AAPL": {"price": Decimal("175.50"), "currency": "USD"},
            "GOOGL": {"price": Decimal("145.00"), "currency": "USD"},
            "MSFT": {"price": Decimal("380.25"), "currency": "USD"},
            "SPY": {"price": Decimal("450.00"), "currency": "USD"}
        },
        "fx_rates": {
            ("USD", "USD"): Decimal("1.0000"),
            ("USD", "CAD"): Decimal("1.3500"),
            ("CAD", "USD"): Decimal("0.7407")
        }
    }


@pytest.fixture
def sample_macro_indicators() -> Dict[str, Any]:
    """Return sample macro indicators for testing."""
    return {
        "gdp_growth": Decimal("2.5"),
        "inflation_rate": Decimal("3.2"),
        "unemployment_rate": Decimal("4.1"),
        "fed_funds_rate": Decimal("5.25"),
        "treasury_10y": Decimal("4.50"),
        "treasury_2y": Decimal("4.80"),
        "vix": Decimal("18.5"),
        "credit_spread": Decimal("1.20")
    }


@pytest.fixture
def sample_scenario() -> Dict[str, Any]:
    """Return sample scenario for testing."""
    return {
        "id": "deleveraging_mild",
        "name": "Mild Deleveraging",
        "shocks": {
            "equity": Decimal("-0.15"),
            "bond": Decimal("0.05"),
            "commodity": Decimal("-0.10"),
            "fx_usd": Decimal("0.08")
        },
        "regime": "deleveraging",
        "severity": "mild"
    }


# ============================================================================
# Assertion Utilities
# ============================================================================

def assert_decimal_equal(
    actual: Decimal,
    expected: Decimal,
    tolerance: Decimal = Decimal("0.01")
):
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


def assert_decimal_in_range(
    actual: Decimal,
    min_val: Decimal,
    max_val: Decimal
):
    """
    Assert decimal is within range [min_val, max_val].

    Args:
        actual: Actual value
        min_val: Minimum expected value
        max_val: Maximum expected value

    Raises:
        AssertionError: If value is outside range
    """
    if not (min_val <= actual <= max_val):
        raise AssertionError(
            f"Value {actual} not in range [{min_val}, {max_val}]"
        )


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_ratings_service():
    """Mock RatingsService for testing."""
    service = MagicMock()
    service.calculate_dividend_safety = AsyncMock()
    service.calculate_moat_strength = AsyncMock()
    service.calculate_resilience = AsyncMock()
    service.aggregate_ratings = AsyncMock()
    return service


@pytest.fixture
def mock_optimizer_service():
    """Mock OptimizerService for testing."""
    service = MagicMock()
    service.propose_trades = AsyncMock()
    service.analyze_impact = AsyncMock()
    service.suggest_hedges = AsyncMock()
    service.suggest_deleveraging_hedges = AsyncMock()
    return service


@pytest.fixture
def mock_macro_service():
    """Mock MacroService for testing."""
    service = MagicMock()
    service.detect_regime = AsyncMock()
    service.get_indicators = AsyncMock()
    service.compute_cycles = AsyncMock()
    return service


@pytest.fixture
def mock_pricing_service():
    """Mock PricingService for testing."""
    service = MagicMock()
    service.build_pack = AsyncMock()
    service.get_pack = AsyncMock()
    service.apply_pack = AsyncMock()
    return service


@pytest.fixture
def mock_ledger_service():
    """Mock LedgerService for testing."""
    service = MagicMock()
    service.get_positions = AsyncMock()
    service.reconcile = AsyncMock()
    service.compute_nav = AsyncMock()
    return service


@pytest.fixture
def mock_scenarios_service():
    """Mock ScenariosService for testing."""
    service = MagicMock()
    service.apply_scenario = AsyncMock()
    service.compute_dar = AsyncMock()
    service.get_dar_history = AsyncMock()
    return service


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest for unit tests."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (no database required)"
    )
    config.addinivalue_line(
        "markers", "fast: Fast tests (< 100ms)"
    )
