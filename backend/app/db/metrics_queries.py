"""
Portfolio Metrics Database Queries

Purpose: AsyncPG-based queries for portfolio metrics, currency attribution, and factor exposures
Updated: 2025-10-22
Priority: P0 (Critical for Phase 3)

Usage:
    from app.db import get_metrics_queries

    queries = get_metrics_queries()

    # Insert daily metrics
    await queries.insert_metrics(portfolio_id, asof_date, metrics_data)

    # Get latest metrics
    latest = await queries.get_latest_metrics(portfolio_id)

    # Get historical metrics
    history = await queries.get_metrics_history(portfolio_id, start_date, end_date)

    # Get rolling metrics from continuous aggregates
    rolling = await queries.get_rolling_metrics_30d(portfolio_id, asof_date)

Testing:
    # Use stub mode for tests without database
    queries = MetricsQueries(use_db=False)
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from .connection import execute_query, execute_query_one, execute_statement

logger = logging.getLogger(__name__)


class MetricsQueries:
    """Database queries for portfolio metrics and attribution."""

    def __init__(self, use_db: bool = True):
        """
        Initialize metrics queries.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
        """
        self.use_db = use_db
        logger.info(f"MetricsQueries initialized (use_db={use_db})")

    # ========================================================================
    # Portfolio Metrics Operations
    # ========================================================================

    async def insert_metrics(
        self,
        portfolio_id: UUID,
        asof_date: date,
        pricing_pack_id: str,
        metrics: Dict[str, Any],
    ) -> bool:
        """
        Insert daily portfolio metrics.

        Args:
            portfolio_id: Portfolio UUID
            asof_date: As-of date for metrics
            pricing_pack_id: Pricing pack ID (e.g., 'PP_2025-10-21')
            metrics: Dictionary of metric values

        Returns:
            True if successful

        Example:
            await queries.insert_metrics(
                portfolio_id=UUID('...'),
                asof_date=date(2025, 10, 21),
                pricing_pack_id='PP_2025-10-21',
                metrics={
                    'twr_1d': 0.0012,
                    'twr_ytd': 0.0850,
                    'volatility_30d': 0.1520,
                    'sharpe_30d': 0.5592,
                    'portfolio_value_base': 1000000.00,
                    'base_currency': 'CAD',
                }
            )
        """
        if not self.use_db:
            logger.warning("insert_metrics: Using stub (no-op)")
            return True

        query = """
            INSERT INTO portfolio_metrics (
                portfolio_id, asof_date, pricing_pack_id,
                twr_1d, twr_1d_base,
                twr_mtd, twr_qtd, twr_ytd, twr_1y,
                twr_3y_ann, twr_5y_ann, twr_inception_ann,
                mwr_ytd, mwr_1y, mwr_3y_ann, mwr_inception_ann,
                volatility_30d, volatility_60d, volatility_90d, volatility_1y,
                sharpe_30d, sharpe_60d, sharpe_90d, sharpe_1y,
                max_drawdown_1y, max_drawdown_3y, current_drawdown,
                alpha_1y, alpha_3y_ann, beta_1y, beta_3y,
                tracking_error_1y, information_ratio_1y,
                win_rate_1y, avg_win, avg_loss,
                portfolio_value_base, portfolio_value_local, cash_balance,
                base_currency, benchmark_id, reconciliation_error_bps
            ) VALUES (
                $1, $2, $3,
                $4, $5, $6, $7, $8, $9, $10, $11, $12,
                $13, $14, $15, $16,
                $17, $18, $19, $20,
                $21, $22, $23, $24,
                $25, $26, $27,
                $28, $29, $30, $31,
                $32, $33,
                $34, $35, $36,
                $37, $38, $39,
                $40, $41, $42
            )
            ON CONFLICT (portfolio_id, asof_date, pricing_pack_id)
            DO UPDATE SET
                twr_1d = EXCLUDED.twr_1d,
                twr_1d_base = EXCLUDED.twr_1d_base,
                twr_mtd = EXCLUDED.twr_mtd,
                twr_qtd = EXCLUDED.twr_qtd,
                twr_ytd = EXCLUDED.twr_ytd,
                twr_1y = EXCLUDED.twr_1y,
                twr_3y_ann = EXCLUDED.twr_3y_ann,
                twr_5y_ann = EXCLUDED.twr_5y_ann,
                twr_inception_ann = EXCLUDED.twr_inception_ann,
                mwr_ytd = EXCLUDED.mwr_ytd,
                mwr_1y = EXCLUDED.mwr_1y,
                mwr_3y_ann = EXCLUDED.mwr_3y_ann,
                mwr_inception_ann = EXCLUDED.mwr_inception_ann,
                volatility_30d = EXCLUDED.volatility_30d,
                volatility_60d = EXCLUDED.volatility_60d,
                volatility_90d = EXCLUDED.volatility_90d,
                volatility_1y = EXCLUDED.volatility_1y,
                sharpe_30d = EXCLUDED.sharpe_30d,
                sharpe_60d = EXCLUDED.sharpe_60d,
                sharpe_90d = EXCLUDED.sharpe_90d,
                sharpe_1y = EXCLUDED.sharpe_1y,
                max_drawdown_1y = EXCLUDED.max_drawdown_1y,
                max_drawdown_3y = EXCLUDED.max_drawdown_3y,
                current_drawdown = EXCLUDED.current_drawdown,
                alpha_1y = EXCLUDED.alpha_1y,
                alpha_3y_ann = EXCLUDED.alpha_3y_ann,
                beta_1y = EXCLUDED.beta_1y,
                beta_3y = EXCLUDED.beta_3y,
                tracking_error_1y = EXCLUDED.tracking_error_1y,
                information_ratio_1y = EXCLUDED.information_ratio_1y,
                win_rate_1y = EXCLUDED.win_rate_1y,
                avg_win = EXCLUDED.avg_win,
                avg_loss = EXCLUDED.avg_loss,
                portfolio_value_base = EXCLUDED.portfolio_value_base,
                portfolio_value_local = EXCLUDED.portfolio_value_local,
                cash_balance = EXCLUDED.cash_balance,
                base_currency = EXCLUDED.base_currency,
                benchmark_id = EXCLUDED.benchmark_id,
                reconciliation_error_bps = EXCLUDED.reconciliation_error_bps
        """

        try:
            await execute_statement(
                query,
                portfolio_id,
                asof_date,
                pricing_pack_id,
                metrics.get("twr_1d"),
                metrics.get("twr_1d_base"),
                metrics.get("twr_mtd"),
                metrics.get("twr_qtd"),
                metrics.get("twr_ytd"),
                metrics.get("twr_1y"),
                metrics.get("twr_3y_ann"),
                metrics.get("twr_5y_ann"),
                metrics.get("twr_inception_ann"),
                metrics.get("mwr_ytd"),
                metrics.get("mwr_1y"),
                metrics.get("mwr_3y_ann"),
                metrics.get("mwr_inception_ann"),
                metrics.get("volatility_30d"),
                metrics.get("volatility_60d"),
                metrics.get("volatility_90d"),
                metrics.get("volatility_1y"),
                metrics.get("sharpe_30d"),
                metrics.get("sharpe_60d"),
                metrics.get("sharpe_90d"),
                metrics.get("sharpe_1y"),
                metrics.get("max_drawdown_1y"),
                metrics.get("max_drawdown_3y"),
                metrics.get("current_drawdown"),
                metrics.get("alpha_1y"),
                metrics.get("alpha_3y_ann"),
                metrics.get("beta_1y"),
                metrics.get("beta_3y"),
                metrics.get("tracking_error_1y"),
                metrics.get("information_ratio_1y"),
                metrics.get("win_rate_1y"),
                metrics.get("avg_win"),
                metrics.get("avg_loss"),
                metrics.get("portfolio_value_base"),
                metrics.get("portfolio_value_local"),
                metrics.get("cash_balance"),
                metrics.get("base_currency"),
                metrics.get("benchmark_id"),
                metrics.get("reconciliation_error_bps"),
            )
            logger.info(
                f"Inserted metrics for portfolio {portfolio_id} on {asof_date}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to insert metrics for portfolio {portfolio_id}: {e}",
                exc_info=True,
            )
            return False

    async def get_latest_metrics(
        self, portfolio_id: UUID, pricing_pack_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get latest metrics for a portfolio.

        Args:
            portfolio_id: Portfolio UUID
            pricing_pack_id: Optional specific pricing pack ID

        Returns:
            Dictionary of metrics or None if not found
        """
        if not self.use_db:
            logger.warning("get_latest_metrics: Using stub")
            return {
                "portfolio_id": str(portfolio_id),
                "asof_date": date(2025, 10, 21),
                "pricing_pack_id": "PP_2025-10-21",
                "twr_1d": Decimal("0.0012"),
                "twr_ytd": Decimal("0.0850"),
                "volatility_30d": Decimal("0.1520"),
                "sharpe_30d": Decimal("0.5592"),
                "portfolio_value_base": Decimal("1000000.00"),
                "base_currency": "CAD",
            }

        if pricing_pack_id:
            query = """
                SELECT *
                FROM portfolio_metrics
                WHERE portfolio_id = $1 AND pricing_pack_id = $2
                ORDER BY asof_date DESC
                LIMIT 1
            """
            row = await execute_query_one(query, portfolio_id, pricing_pack_id)
        else:
            query = """
                SELECT *
                FROM portfolio_metrics
                WHERE portfolio_id = $1
                ORDER BY asof_date DESC, created_at DESC
                LIMIT 1
            """
            row = await execute_query_one(query, portfolio_id)

        if not row:
            logger.warning(f"No metrics found for portfolio {portfolio_id}")
            return None

        return dict(row)

    async def get_metrics_history(
        self,
        portfolio_id: UUID,
        start_date: date,
        end_date: date,
        pricing_pack_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get historical metrics for a portfolio.

        Args:
            portfolio_id: Portfolio UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            pricing_pack_id: Optional specific pricing pack ID

        Returns:
            List of metrics dictionaries ordered by date ASC
        """
        if not self.use_db:
            logger.warning("get_metrics_history: Using stub")
            return [
                {
                    "portfolio_id": str(portfolio_id),
                    "asof_date": date(2025, 10, 21),
                    "twr_1d": Decimal("0.0012"),
                    "twr_ytd": Decimal("0.0850"),
                }
            ]

        if pricing_pack_id:
            query = """
                SELECT *
                FROM portfolio_metrics
                WHERE portfolio_id = $1
                  AND asof_date >= $2
                  AND asof_date <= $3
                  AND pricing_pack_id = $4
                ORDER BY asof_date ASC
            """
            rows = await execute_query(query, portfolio_id, start_date, end_date, pricing_pack_id)
        else:
            query = """
                SELECT *
                FROM portfolio_metrics
                WHERE portfolio_id = $1
                  AND asof_date >= $2
                  AND asof_date <= $3
                ORDER BY asof_date ASC
            """
            rows = await execute_query(query, portfolio_id, start_date, end_date)

        return [dict(row) for row in rows]

    # ========================================================================
    # Currency Attribution Operations
    # ========================================================================

    async def insert_currency_attribution(
        self,
        portfolio_id: UUID,
        asof_date: date,
        pricing_pack_id: str,
        attribution: Dict[str, Any],
    ) -> bool:
        """
        Insert currency attribution data.

        Args:
            portfolio_id: Portfolio UUID
            asof_date: As-of date
            pricing_pack_id: Pricing pack ID
            attribution: Attribution data

        Returns:
            True if successful

        Example:
            await queries.insert_currency_attribution(
                portfolio_id=UUID('...'),
                asof_date=date(2025, 10, 21),
                pricing_pack_id='PP_2025-10-21',
                attribution={
                    'local_return': 0.0015,
                    'fx_return': -0.0003,
                    'interaction_return': -0.0000045,
                    'total_return': 0.0011955,
                    'base_return_actual': 0.0012,
                    'error_bps': 0.045,
                    'base_currency': 'CAD',
                    'attribution_by_currency': {'USD': {...}, 'EUR': {...}}
                }
            )
        """
        if not self.use_db:
            logger.warning("insert_currency_attribution: Using stub (no-op)")
            return True

        query = """
            INSERT INTO currency_attribution (
                portfolio_id, asof_date, pricing_pack_id,
                local_return, fx_return, interaction_return,
                total_return, base_return_actual, error_bps,
                attribution_by_currency, base_currency
            ) VALUES (
                $1, $2, $3,
                $4, $5, $6,
                $7, $8, $9,
                $10, $11
            )
            ON CONFLICT (portfolio_id, asof_date, pricing_pack_id)
            DO UPDATE SET
                local_return = EXCLUDED.local_return,
                fx_return = EXCLUDED.fx_return,
                interaction_return = EXCLUDED.interaction_return,
                total_return = EXCLUDED.total_return,
                base_return_actual = EXCLUDED.base_return_actual,
                error_bps = EXCLUDED.error_bps,
                attribution_by_currency = EXCLUDED.attribution_by_currency,
                base_currency = EXCLUDED.base_currency
        """

        try:
            await execute_statement(
                query,
                portfolio_id,
                asof_date,
                pricing_pack_id,
                attribution.get("local_return"),
                attribution.get("fx_return"),
                attribution.get("interaction_return"),
                attribution.get("total_return"),
                attribution.get("base_return_actual"),
                attribution.get("error_bps"),
                attribution.get("attribution_by_currency"),
                attribution.get("base_currency"),
            )
            logger.info(
                f"Inserted currency attribution for portfolio {portfolio_id} on {asof_date}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to insert currency attribution for portfolio {portfolio_id}: {e}",
                exc_info=True,
            )
            return False

    async def get_currency_attribution(
        self, portfolio_id: UUID, asof_date: date, pricing_pack_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get currency attribution for a specific date.

        Args:
            portfolio_id: Portfolio UUID
            asof_date: As-of date
            pricing_pack_id: Optional specific pricing pack ID

        Returns:
            Attribution dictionary or None
        """
        if not self.use_db:
            logger.warning("get_currency_attribution: Using stub")
            return {
                "portfolio_id": str(portfolio_id),
                "asof_date": asof_date,
                "local_return": Decimal("0.0015"),
                "fx_return": Decimal("-0.0003"),
                "interaction_return": Decimal("-0.0000045"),
                "total_return": Decimal("0.0011955"),
                "base_return_actual": Decimal("0.0012"),
                "error_bps": Decimal("0.045"),
            }

        if pricing_pack_id:
            query = """
                SELECT *
                FROM currency_attribution
                WHERE portfolio_id = $1 AND asof_date = $2 AND pricing_pack_id = $3
            """
            row = await execute_query_one(query, portfolio_id, asof_date, pricing_pack_id)
        else:
            query = """
                SELECT *
                FROM currency_attribution
                WHERE portfolio_id = $1 AND asof_date = $2
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await execute_query_one(query, portfolio_id, asof_date)

        if not row:
            return None

        return dict(row)

    # ========================================================================
    # Factor Exposure Operations
    # ========================================================================

    async def insert_factor_exposures(
        self,
        portfolio_id: UUID,
        asof_date: date,
        pricing_pack_id: str,
        exposures: Dict[str, Any],
    ) -> bool:
        """
        Insert factor exposure data.

        Args:
            portfolio_id: Portfolio UUID
            asof_date: As-of date
            pricing_pack_id: Pricing pack ID
            exposures: Factor exposure data

        Returns:
            True if successful
        """
        if not self.use_db:
            logger.warning("insert_factor_exposures: Using stub (no-op)")
            return True

        query = """
            INSERT INTO factor_exposures (
                portfolio_id, asof_date, pricing_pack_id,
                beta_real_rate, beta_inflation, beta_credit, beta_fx,
                beta_market, beta_size, beta_value, beta_momentum,
                var_factor, var_idiosyncratic, r_squared,
                factor_contributions, estimation_window_days, benchmark_id
            ) VALUES (
                $1, $2, $3,
                $4, $5, $6, $7,
                $8, $9, $10, $11,
                $12, $13, $14,
                $15, $16, $17
            )
            ON CONFLICT (portfolio_id, asof_date, pricing_pack_id)
            DO UPDATE SET
                beta_real_rate = EXCLUDED.beta_real_rate,
                beta_inflation = EXCLUDED.beta_inflation,
                beta_credit = EXCLUDED.beta_credit,
                beta_fx = EXCLUDED.beta_fx,
                beta_market = EXCLUDED.beta_market,
                beta_size = EXCLUDED.beta_size,
                beta_value = EXCLUDED.beta_value,
                beta_momentum = EXCLUDED.beta_momentum,
                var_factor = EXCLUDED.var_factor,
                var_idiosyncratic = EXCLUDED.var_idiosyncratic,
                r_squared = EXCLUDED.r_squared,
                factor_contributions = EXCLUDED.factor_contributions,
                estimation_window_days = EXCLUDED.estimation_window_days,
                benchmark_id = EXCLUDED.benchmark_id
        """

        try:
            await execute_statement(
                query,
                portfolio_id,
                asof_date,
                pricing_pack_id,
                exposures.get("beta_real_rate"),
                exposures.get("beta_inflation"),
                exposures.get("beta_credit"),
                exposures.get("beta_fx"),
                exposures.get("beta_market"),
                exposures.get("beta_size"),
                exposures.get("beta_value"),
                exposures.get("beta_momentum"),
                exposures.get("var_factor"),
                exposures.get("var_idiosyncratic"),
                exposures.get("r_squared"),
                exposures.get("factor_contributions"),
                exposures.get("estimation_window_days"),
                exposures.get("benchmark_id"),
            )
            logger.info(
                f"Inserted factor exposures for portfolio {portfolio_id} on {asof_date}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to insert factor exposures for portfolio {portfolio_id}: {e}",
                exc_info=True,
            )
            return False

    async def get_factor_exposures(
        self, portfolio_id: UUID, asof_date: date, pricing_pack_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get factor exposures for a specific date.

        Args:
            portfolio_id: Portfolio UUID
            asof_date: As-of date
            pricing_pack_id: Optional specific pricing pack ID

        Returns:
            Exposures dictionary or None
        """
        if not self.use_db:
            logger.warning("get_factor_exposures: Using stub")
            return {
                "portfolio_id": str(portfolio_id),
                "asof_date": asof_date,
                "beta_real_rate": Decimal("0.35"),
                "beta_inflation": Decimal("-0.12"),
                "beta_market": Decimal("0.85"),
                "r_squared": Decimal("0.72"),
            }

        if pricing_pack_id:
            query = """
                SELECT *
                FROM factor_exposures
                WHERE portfolio_id = $1 AND asof_date = $2 AND pricing_pack_id = $3
            """
            row = await execute_query_one(query, portfolio_id, asof_date, pricing_pack_id)
        else:
            query = """
                SELECT *
                FROM factor_exposures
                WHERE portfolio_id = $1 AND asof_date = $2
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await execute_query_one(query, portfolio_id, asof_date)

        if not row:
            return None

        return dict(row)

    # ========================================================================
    # Continuous Aggregate Queries (Rolling Metrics)
    # ========================================================================

    async def get_rolling_metrics_30d(
        self, portfolio_id: UUID, asof_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Get 30-day rolling metrics from continuous aggregate.

        Args:
            portfolio_id: Portfolio UUID
            asof_date: As-of date

        Returns:
            Rolling metrics dictionary or None
        """
        if not self.use_db:
            logger.warning("get_rolling_metrics_30d: Using stub")
            return {
                "portfolio_id": str(portfolio_id),
                "day": asof_date,
                "avg_return_30d": Decimal("0.0010"),
                "volatility_30d_realized": Decimal("0.1520"),
                "drawdown_30d": Decimal("0.0200"),
            }

        query = """
            SELECT *
            FROM portfolio_metrics_30d_rolling
            WHERE portfolio_id = $1 AND day = $2
        """
        row = await execute_query_one(query, portfolio_id, asof_date)

        if not row:
            return None

        return dict(row)

    async def get_rolling_metrics_60d(
        self, portfolio_id: UUID, asof_date: date
    ) -> Optional[Dict[str, Any]]:
        """Get 60-day rolling metrics from continuous aggregate."""
        if not self.use_db:
            logger.warning("get_rolling_metrics_60d: Using stub")
            return {
                "portfolio_id": str(portfolio_id),
                "day": asof_date,
                "avg_return_60d": Decimal("0.0009"),
                "volatility_60d_realized": Decimal("0.1480"),
            }

        query = """
            SELECT *
            FROM portfolio_metrics_60d_rolling
            WHERE portfolio_id = $1 AND day = $2
        """
        row = await execute_query_one(query, portfolio_id, asof_date)

        if not row:
            return None

        return dict(row)

    async def get_sharpe_90d(
        self, portfolio_id: UUID, asof_date: date
    ) -> Optional[Dict[str, Any]]:
        """Get 90-day Sharpe ratio from continuous aggregate."""
        if not self.use_db:
            logger.warning("get_sharpe_90d: Using stub")
            return {
                "portfolio_id": str(portfolio_id),
                "day": asof_date,
                "avg_return_90d": Decimal("0.0008"),
                "sharpe_90d_realized": Decimal("0.5200"),
            }

        query = """
            SELECT *
            FROM portfolio_metrics_90d_sharpe
            WHERE portfolio_id = $1 AND day = $2
        """
        row = await execute_query_one(query, portfolio_id, asof_date)

        if not row:
            return None

        return dict(row)

    async def get_beta_1y(
        self, portfolio_id: UUID, asof_date: date
    ) -> Optional[Dict[str, Any]]:
        """Get 1-year beta/alpha from continuous aggregate."""
        if not self.use_db:
            logger.warning("get_beta_1y: Using stub")
            return {
                "portfolio_id": str(portfolio_id),
                "day": asof_date,
                "avg_beta_1y": Decimal("0.85"),
                "avg_alpha_1y": Decimal("0.0020"),
            }

        query = """
            SELECT *
            FROM portfolio_metrics_1y_beta
            WHERE portfolio_id = $1 AND day = $2
        """
        row = await execute_query_one(query, portfolio_id, asof_date)

        if not row:
            return None

        return dict(row)


# ============================================================================
# Singleton Instance
# ============================================================================

_metrics_queries: Optional[MetricsQueries] = None


def get_metrics_queries() -> MetricsQueries:
    """Get singleton MetricsQueries instance (lazy-initializes if needed)."""
    global _metrics_queries
    if _metrics_queries is None:
        logger.info("MetricsQueries not initialized, lazy-initializing with use_db=True")
        _metrics_queries = MetricsQueries(use_db=True)
    return _metrics_queries


def init_metrics_queries(use_db: bool = True) -> MetricsQueries:
    """
    Initialize singleton MetricsQueries instance.

    Args:
        use_db: If True, use real database. If False, use stubs for testing.

    Returns:
        MetricsQueries instance
    """
    global _metrics_queries
    _metrics_queries = MetricsQueries(use_db=use_db)
    logger.info("MetricsQueries singleton initialized")
    return _metrics_queries
