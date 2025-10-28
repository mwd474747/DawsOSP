#!/usr/bin/env python3
"""
Verify Metrics Schema and Queries (Simple Test Script)

Purpose: Quick verification without pytest
Updated: 2025-10-22
Priority: P0

Usage:
    python3 backend/tests/verify_metrics_schema.py
"""

import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import UUID

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.metrics_queries import MetricsQueries

# Test constants
TEST_PORTFOLIO_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_PACK_ID = "PP_2025-10-21"
TEST_DATE = date(2025, 10, 21)


async def test_stub_mode():
    """Test all queries in stub mode (no database required)."""
    print("=" * 80)
    print("Testing MetricsQueries in STUB MODE (no database)")
    print("=" * 80)

    queries = MetricsQueries(use_db=False)

    # Test 1: Insert metrics
    print("\n[1/12] Testing insert_metrics...")
    metrics = {
        "twr_1d": 0.0012,
        "twr_ytd": 0.0850,
        "volatility_30d": 0.1520,
        "sharpe_30d": 0.5592,
        "portfolio_value_base": 1000000.00,
        "base_currency": "CAD",
    }
    result = await queries.insert_metrics(
        portfolio_id=TEST_PORTFOLIO_ID,
        asof_date=TEST_DATE,
        pricing_pack_id=TEST_PACK_ID,
        metrics=metrics,
    )
    assert result is True, "insert_metrics should return True"
    print("  ✓ insert_metrics returns True")

    # Test 2: Get latest metrics
    print("\n[2/12] Testing get_latest_metrics...")
    latest = await queries.get_latest_metrics(TEST_PORTFOLIO_ID)
    assert latest is not None, "get_latest_metrics should return data"
    assert latest["portfolio_id"] == str(TEST_PORTFOLIO_ID)
    assert latest["asof_date"] == date(2025, 10, 21)
    assert latest["twr_1d"] == Decimal("0.0012")
    assert latest["base_currency"] == "CAD"
    print(f"  ✓ Latest metrics: TWR_1D={latest['twr_1d']}, TWR_YTD={latest['twr_ytd']}")

    # Test 3: Get metrics history
    print("\n[3/12] Testing get_metrics_history...")
    start_date = date(2025, 10, 1)
    end_date = date(2025, 10, 31)
    history = await queries.get_metrics_history(
        TEST_PORTFOLIO_ID, start_date, end_date
    )
    assert isinstance(history, list), "get_metrics_history should return list"
    assert len(history) >= 1, "Should have at least 1 entry"
    print(f"  ✓ History: {len(history)} entries from {start_date} to {end_date}")

    # Test 4: Insert currency attribution
    print("\n[4/12] Testing insert_currency_attribution...")
    attribution = {
        "local_return": 0.0015,
        "fx_return": -0.0003,
        "interaction_return": -0.0000045,
        "total_return": 0.0011955,
        "base_return_actual": 0.0012,
        "error_bps": 0.045,
        "base_currency": "CAD",
    }
    result = await queries.insert_currency_attribution(
        portfolio_id=TEST_PORTFOLIO_ID,
        asof_date=TEST_DATE,
        pricing_pack_id=TEST_PACK_ID,
        attribution=attribution,
    )
    assert result is True, "insert_currency_attribution should return True"
    print("  ✓ insert_currency_attribution returns True")

    # Test 5: Get currency attribution
    print("\n[5/12] Testing get_currency_attribution...")
    attr = await queries.get_currency_attribution(TEST_PORTFOLIO_ID, TEST_DATE)
    assert attr is not None, "get_currency_attribution should return data"
    assert attr["local_return"] == Decimal("0.0015")
    assert attr["fx_return"] == Decimal("-0.0003")
    assert attr["error_bps"] == Decimal("0.045")
    print(f"  ✓ Attribution: local={attr['local_return']}, fx={attr['fx_return']}, error={attr['error_bps']}bp")

    # Test 6: Insert factor exposures
    print("\n[6/12] Testing insert_factor_exposures...")
    exposures = {
        "beta_real_rate": 0.35,
        "beta_inflation": -0.12,
        "beta_credit": 0.08,
        "beta_market": 0.85,
        "r_squared": 0.72,
        "estimation_window_days": 252,
    }
    result = await queries.insert_factor_exposures(
        portfolio_id=TEST_PORTFOLIO_ID,
        asof_date=TEST_DATE,
        pricing_pack_id=TEST_PACK_ID,
        exposures=exposures,
    )
    assert result is True, "insert_factor_exposures should return True"
    print("  ✓ insert_factor_exposures returns True")

    # Test 7: Get factor exposures
    print("\n[7/12] Testing get_factor_exposures...")
    exp = await queries.get_factor_exposures(TEST_PORTFOLIO_ID, TEST_DATE)
    assert exp is not None, "get_factor_exposures should return data"
    assert exp["beta_real_rate"] == Decimal("0.35")
    assert exp["beta_market"] == Decimal("0.85")
    assert exp["r_squared"] == Decimal("0.72")
    print(f"  ✓ Exposures: beta_market={exp['beta_market']}, R²={exp['r_squared']}")

    # Test 8: Get 30-day rolling metrics
    print("\n[8/12] Testing get_rolling_metrics_30d...")
    rolling_30d = await queries.get_rolling_metrics_30d(TEST_PORTFOLIO_ID, TEST_DATE)
    assert rolling_30d is not None, "get_rolling_metrics_30d should return data"
    assert rolling_30d["avg_return_30d"] == Decimal("0.0010")
    assert rolling_30d["volatility_30d_realized"] == Decimal("0.1520")
    print(f"  ✓ 30d rolling: avg_return={rolling_30d['avg_return_30d']}, vol={rolling_30d['volatility_30d_realized']}")

    # Test 9: Get 60-day rolling metrics
    print("\n[9/12] Testing get_rolling_metrics_60d...")
    rolling_60d = await queries.get_rolling_metrics_60d(TEST_PORTFOLIO_ID, TEST_DATE)
    assert rolling_60d is not None, "get_rolling_metrics_60d should return data"
    assert rolling_60d["avg_return_60d"] == Decimal("0.0009")
    print(f"  ✓ 60d rolling: avg_return={rolling_60d['avg_return_60d']}, vol={rolling_60d['volatility_60d_realized']}")

    # Test 10: Get 90-day Sharpe
    print("\n[10/12] Testing get_sharpe_90d...")
    sharpe_90d = await queries.get_sharpe_90d(TEST_PORTFOLIO_ID, TEST_DATE)
    assert sharpe_90d is not None, "get_sharpe_90d should return data"
    assert sharpe_90d["sharpe_90d_realized"] == Decimal("0.5200")
    print(f"  ✓ 90d Sharpe: {sharpe_90d['sharpe_90d_realized']}")

    # Test 11: Get 1-year beta
    print("\n[11/12] Testing get_beta_1y...")
    beta_1y = await queries.get_beta_1y(TEST_PORTFOLIO_ID, TEST_DATE)
    assert beta_1y is not None, "get_beta_1y should return data"
    assert beta_1y["avg_beta_1y"] == Decimal("0.85")
    assert beta_1y["avg_alpha_1y"] == Decimal("0.0020")
    print(f"  ✓ 1y beta: beta={beta_1y['avg_beta_1y']}, alpha={beta_1y['avg_alpha_1y']}")

    # Test 12: Test with specific pricing pack ID
    print("\n[12/12] Testing with specific pricing_pack_id...")
    latest_with_pack = await queries.get_latest_metrics(
        TEST_PORTFOLIO_ID, pricing_pack_id=TEST_PACK_ID
    )
    assert latest_with_pack is not None, "Should return metrics for specific pack"
    print(f"  ✓ Metrics for pack {TEST_PACK_ID}: {latest_with_pack['asof_date']}")

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✅")
    print("=" * 80)
    print("\nSummary:")
    print("  • insert_metrics: ✓")
    print("  • get_latest_metrics: ✓")
    print("  • get_metrics_history: ✓")
    print("  • insert_currency_attribution: ✓")
    print("  • get_currency_attribution: ✓")
    print("  • insert_factor_exposures: ✓")
    print("  • get_factor_exposures: ✓")
    print("  • get_rolling_metrics_30d: ✓")
    print("  • get_rolling_metrics_60d: ✓")
    print("  • get_sharpe_90d: ✓")
    print("  • get_beta_1y: ✓")
    print("  • Pricing pack ID filtering: ✓")
    print("\nReady for Phase 3 Task 2: Currency Attribution Implementation")


if __name__ == "__main__":
    try:
        asyncio.run(test_stub_mode())
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
