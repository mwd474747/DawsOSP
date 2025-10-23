#!/usr/bin/env python3
"""
Check Metrics Schema Structure (No Dependencies)

Purpose: Verify file structure and basic syntax without external dependencies
Updated: 2025-10-22
Priority: P0

Usage:
    python3 backend/tests/check_metrics_structure.py
"""

import ast
import sys
from pathlib import Path

# File paths
SCHEMA_FILE = Path("backend/db/schema/portfolio_metrics.sql")
QUERIES_FILE = Path("backend/app/db/metrics_queries.py")
INIT_FILE = Path("backend/app/db/__init__.py")


def check_file_exists(path: Path) -> bool:
    """Check if file exists."""
    if not path.exists():
        print(f"  ❌ File not found: {path}")
        return False
    print(f"  ✓ File exists: {path}")
    return True


def check_sql_schema(path: Path) -> bool:
    """Check SQL schema file structure."""
    print(f"\nChecking SQL schema: {path}")

    if not path.exists():
        print(f"  ❌ File not found")
        return False

    content = path.read_text()

    # Check for required tables
    required_tables = [
        "portfolio_metrics",
        "currency_attribution",
        "factor_exposures",
    ]

    print("  Checking tables...")
    for table in required_tables:
        if f"CREATE TABLE {table}" in content:
            print(f"    ✓ Table: {table}")
        else:
            print(f"    ❌ Missing table: {table}")
            return False

    # Check for hypertables
    print("  Checking hypertables...")
    if "create_hypertable" in content:
        count = content.count("create_hypertable")
        print(f"    ✓ Found {count} hypertable definitions")
    else:
        print(f"    ❌ No hypertable definitions found")
        return False

    # Check for continuous aggregates
    print("  Checking continuous aggregates...")
    required_views = [
        "portfolio_metrics_30d_rolling",
        "portfolio_metrics_60d_rolling",
        "portfolio_metrics_90d_sharpe",
        "portfolio_metrics_1y_beta",
    ]

    for view in required_views:
        if f"CREATE MATERIALIZED VIEW {view}" in content:
            print(f"    ✓ View: {view}")
        else:
            print(f"    ❌ Missing view: {view}")
            return False

    # Check for compression policy
    if "add_compression_policy" in content:
        print(f"    ✓ Compression policy configured")
    else:
        print(f"    ⚠️  No compression policy (optional)")

    print("  ✓ SQL schema structure valid")
    return True


def check_python_file(path: Path) -> bool:
    """Check Python file can be parsed."""
    print(f"\nChecking Python file: {path}")

    if not path.exists():
        print(f"  ❌ File not found")
        return False

    try:
        content = path.read_text()
        ast.parse(content)
        print(f"  ✓ Python syntax valid")

        # Count lines
        lines = len(content.splitlines())
        print(f"  ✓ File size: {lines} lines")

        return True

    except SyntaxError as e:
        print(f"  ❌ Syntax error: {e}")
        return False


def check_metrics_queries_methods(path: Path) -> bool:
    """Check metrics_queries.py has required methods."""
    print(f"\nChecking MetricsQueries methods: {path}")

    if not path.exists():
        return False

    content = path.read_text()

    required_methods = [
        # Portfolio metrics
        "insert_metrics",
        "get_latest_metrics",
        "get_metrics_history",
        # Currency attribution
        "insert_currency_attribution",
        "get_currency_attribution",
        # Factor exposures
        "insert_factor_exposures",
        "get_factor_exposures",
        # Rolling metrics
        "get_rolling_metrics_30d",
        "get_rolling_metrics_60d",
        "get_sharpe_90d",
        "get_beta_1y",
    ]

    print("  Checking methods...")
    for method in required_methods:
        if f"async def {method}" in content:
            print(f"    ✓ {method}()")
        else:
            print(f"    ❌ Missing method: {method}()")
            return False

    # Check for singleton pattern
    if "get_metrics_queries" in content and "init_metrics_queries" in content:
        print(f"  ✓ Singleton pattern implemented")
    else:
        print(f"  ❌ Singleton pattern missing")
        return False

    # Check for stub mode support
    if "use_db: bool = True" in content:
        print(f"  ✓ Stub mode support (use_db parameter)")
    else:
        print(f"  ⚠️  No stub mode parameter")

    print("  ✓ MetricsQueries structure valid")
    return True


def check_init_exports(path: Path) -> bool:
    """Check __init__.py exports metrics queries."""
    print(f"\nChecking module exports: {path}")

    if not path.exists():
        return False

    content = path.read_text()

    required_exports = [
        "MetricsQueries",
        "get_metrics_queries",
        "init_metrics_queries",
    ]

    print("  Checking exports...")
    for export in required_exports:
        if f'"{export}"' in content or f"'{export}'" in content:
            print(f"    ✓ {export}")
        else:
            print(f"    ❌ Missing export: {export}")
            return False

    print("  ✓ Module exports valid")
    return True


def main():
    """Run all structure checks."""
    print("=" * 80)
    print("PHASE 3 TASK 1: METRICS SCHEMA STRUCTURE VERIFICATION")
    print("=" * 80)

    all_passed = True

    # Check 1: SQL schema file
    print("\n[1/4] SQL Schema File")
    if not check_sql_schema(SCHEMA_FILE):
        all_passed = False

    # Check 2: Python queries file
    print("\n[2/4] Python Queries File")
    if not check_python_file(QUERIES_FILE):
        all_passed = False

    # Check 3: Queries methods
    print("\n[3/4] MetricsQueries Methods")
    if not check_metrics_queries_methods(QUERIES_FILE):
        all_passed = False

    # Check 4: Module exports
    print("\n[4/4] Module Exports")
    if not check_init_exports(INIT_FILE):
        all_passed = False

    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL STRUCTURE CHECKS PASSED")
        print("=" * 80)
        print("\nDeliverables Complete:")
        print(f"  • {SCHEMA_FILE} (SQL schema with hypertables)")
        print(f"  • {QUERIES_FILE} (AsyncPG query methods)")
        print(f"  • {INIT_FILE} (Module exports)")
        print("\nNext Steps:")
        print("  1. Run: psql -f backend/db/schema/portfolio_metrics.sql")
        print("  2. Set DATABASE_URL environment variable")
        print("  3. Test with real database")
        print("\nReady for Phase 3 Task 2: Currency Attribution Implementation")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
