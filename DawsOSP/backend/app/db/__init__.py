"""
DawsOS Database Module

Purpose: Database connection, queries, and schema management
Updated: 2025-10-22
Priority: P0 (Critical for Phase 2 & Phase 3)

Components:
    - connection.py: AsyncPG connection pooling
    - pricing_pack_queries.py: Pricing pack database queries
    - metrics_queries.py: Portfolio metrics, currency attribution, factor exposures

Usage:
    from backend.app.db import init_db_pool, get_pricing_pack_queries, get_metrics_queries

    # Initialize at startup
    await init_db_pool(database_url)

    # Use pricing pack queries
    pack_queries = get_pricing_pack_queries()
    pack = await pack_queries.get_latest_pack()

    # Use metrics queries
    metrics_queries = get_metrics_queries()
    metrics = await metrics_queries.get_latest_metrics(portfolio_id)
"""

from .connection import (
    init_db_pool,
    get_db_pool,
    close_db_pool,
    get_db_connection,
    get_db_connection_with_rls,
    check_db_health,
    execute_query,
    execute_query_one,
    execute_query_value,
    execute_statement,
)

from .pricing_pack_queries import (
    PricingPackQueries,
    get_pricing_pack_queries,
    init_pricing_pack_queries,
)

from .metrics_queries import (
    MetricsQueries,
    get_metrics_queries,
    init_metrics_queries,
)

from .continuous_aggregate_manager import (
    ContinuousAggregateManager,
    get_continuous_aggregate_manager,
    AggregateStatus,
    RefreshPolicy,
)

__all__ = [
    # Connection
    "init_db_pool",
    "get_db_pool",
    "close_db_pool",
    "get_db_connection",
    "get_db_connection_with_rls",
    "check_db_health",
    "execute_query",
    "execute_query_one",
    "execute_query_value",
    "execute_statement",
    # Pricing Pack Queries
    "PricingPackQueries",
    "get_pricing_pack_queries",
    "init_pricing_pack_queries",
    # Metrics Queries
    "MetricsQueries",
    "get_metrics_queries",
    "init_metrics_queries",
    # Continuous Aggregate Manager
    "ContinuousAggregateManager",
    "get_continuous_aggregate_manager",
    "AggregateStatus",
    "RefreshPolicy",
]
