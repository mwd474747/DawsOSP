"""
Portfolio Metrics Computation

Purpose: Compute daily portfolio metrics (TWR, MWR, vol, Sharpe, alpha, beta)
Updated: 2025-10-22
Priority: P0 (Phase 3 Task 3 - Wire Metrics to Database)

Metrics Computed:
    - TWR (Time-Weighted Return) - eliminates cash flow impact
    - MWR (Money-Weighted Return / IRR) - includes cash flow impact
    - Volatility (rolling 30/60/90 day)
    - Sharpe Ratio (vs risk-free rate)
    - Alpha (excess return vs benchmark)
    - Beta (systematic risk vs benchmark)
    - Max Drawdown
    - Win Rate
    - Currency Attribution (local + FX + interaction)

Critical Requirements:
    - All metrics use pricing pack for reproducibility
    - Multi-currency portfolios use base currency returns
    - Currency attribution computed for multi-currency portfolios
    - Benchmark returns are hedged to base currency
    - Metrics stored with pricing_pack_id for auditability

Sacred Accuracy:
    - Return calculations must match ±1bp vs ledger
    - Currency attribution must match ±0.1bp
    - Factor decomposition must match ±0.1bp

Database Integration:
    - Uses backend.app.db.metrics_queries for storage/retrieval
    - Uses backend.jobs.currency_attribution for FX decomposition
    - All metrics stored in portfolio_metrics hypertable
"""

import asyncio
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
from uuid import UUID

try:
    import numpy as np
except ImportError:
    np = None  # Optional dependency

logger = logging.getLogger("DawsOS.Metrics")


@dataclass
class PortfolioMetrics:
    """Portfolio metrics for a single date."""
    portfolio_id: str
    asof_date: date
    pricing_pack_id: str

    # Returns
    twr_1d: Optional[Decimal] = None
    twr_mtd: Optional[Decimal] = None
    twr_qtd: Optional[Decimal] = None
    twr_ytd: Optional[Decimal] = None
    twr_1y: Optional[Decimal] = None
    twr_3y_ann: Optional[Decimal] = None
    twr_5y_ann: Optional[Decimal] = None
    twr_inception_ann: Optional[Decimal] = None

    mwr_ytd: Optional[Decimal] = None
    mwr_1y: Optional[Decimal] = None
    mwr_3y_ann: Optional[Decimal] = None
    mwr_inception_ann: Optional[Decimal] = None

    # Risk
    volatility_30d: Optional[Decimal] = None
    volatility_60d: Optional[Decimal] = None
    volatility_90d: Optional[Decimal] = None
    volatility_1y: Optional[Decimal] = None

    sharpe_30d: Optional[Decimal] = None
    sharpe_60d: Optional[Decimal] = None
    sharpe_90d: Optional[Decimal] = None
    sharpe_1y: Optional[Decimal] = None

    max_drawdown_1y: Optional[Decimal] = None
    max_drawdown_3y: Optional[Decimal] = None

    # Benchmark relative
    alpha_1y: Optional[Decimal] = None
    alpha_3y_ann: Optional[Decimal] = None
    beta_1y: Optional[Decimal] = None
    beta_3y: Optional[Decimal] = None

    tracking_error_1y: Optional[Decimal] = None
    information_ratio_1y: Optional[Decimal] = None

    # Trading stats
    win_rate_1y: Optional[Decimal] = None
    avg_win: Optional[Decimal] = None
    avg_loss: Optional[Decimal] = None


class MetricsComputer:
    """
    Compute portfolio metrics using pricing packs.

    Metrics:
    - TWR (time-weighted return)
    - MWR (money-weighted return / IRR)
    - Volatility (rolling windows)
    - Sharpe ratio
    - Alpha / Beta vs benchmark
    - Tracking error / Information ratio
    - Max drawdown
    - Win rate
    - Currency attribution (for multi-currency portfolios)
    """

    def __init__(self, use_db: bool = True):
        """
        Initialize metrics computer.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
        """
        self.use_db = use_db

        if use_db:
            try:
                from app.db import get_metrics_queries
                from jobs.currency_attribution import CurrencyAttribution

                self.metrics_queries = get_metrics_queries()
                self.currency_attr = CurrencyAttribution(base_currency="CAD")
                logger.info("MetricsComputer initialized with database integration")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize database connections: {e}. "
                    "Falling back to stub mode."
                )
                self.use_db = False
                self.metrics_queries = None
                self.currency_attr = None
        else:
            self.metrics_queries = None
            self.currency_attr = None
            logger.info("MetricsComputer initialized in stub mode")

    async def compute_all_metrics(
        self,
        pack_id: str,
        asof_date: date,
    ) -> List[PortfolioMetrics]:
        """
        Compute metrics for all portfolios.

        Args:
            pack_id: Pricing pack ID
            asof_date: As-of date

        Returns:
            List of PortfolioMetrics for each portfolio
        """
        logger.info(f"Computing metrics for pack {pack_id}")

        # Get all portfolios
        portfolios = await self._get_active_portfolios()

        metrics_list = []
        for portfolio_id in portfolios:
            try:
                metrics = await self.compute_portfolio_metrics(
                    portfolio_id=portfolio_id,
                    pack_id=pack_id,
                    asof_date=asof_date,
                )
                metrics_list.append(metrics)
            except Exception as e:
                logger.exception(f"Failed to compute metrics for portfolio {portfolio_id}: {e}")

        logger.info(f"Computed metrics for {len(metrics_list)} portfolios")
        return metrics_list

    async def compute_portfolio_metrics(
        self,
        portfolio_id: str,
        pack_id: str,
        asof_date: date,
    ) -> PortfolioMetrics:
        """
        Compute metrics for a single portfolio.

        Args:
            portfolio_id: Portfolio ID
            pack_id: Pricing pack ID
            asof_date: As-of date

        Returns:
            PortfolioMetrics object
        """
        logger.debug(f"Computing metrics for portfolio {portfolio_id}")

        # Get portfolio returns history
        returns = await self._get_portfolio_returns(portfolio_id, asof_date)

        # Get benchmark returns (hedged to portfolio base currency)
        benchmark_returns = await self._get_benchmark_returns(portfolio_id, asof_date)

        # Get risk-free rate
        risk_free_rate = await self._get_risk_free_rate(asof_date)

        # Compute TWR (Time-Weighted Return)
        twr_metrics = self._compute_twr_metrics(returns, asof_date)

        # Compute MWR (Money-Weighted Return / IRR)
        mwr_metrics = await self._compute_mwr_metrics(portfolio_id, asof_date)

        # Compute volatility
        vol_metrics = self._compute_volatility_metrics(returns)

        # Compute Sharpe ratio
        sharpe_metrics = self._compute_sharpe_metrics(returns, risk_free_rate)

        # Compute alpha/beta
        alpha_beta_metrics = self._compute_alpha_beta_metrics(returns, benchmark_returns)

        # Compute drawdown
        drawdown_metrics = self._compute_drawdown_metrics(returns)

        # Compute trading stats
        trading_metrics = await self._compute_trading_metrics(portfolio_id, asof_date)

        # Combine all metrics
        metrics = PortfolioMetrics(
            portfolio_id=portfolio_id,
            asof_date=asof_date,
            pricing_pack_id=pack_id,
            **twr_metrics,
            **mwr_metrics,
            **vol_metrics,
            **sharpe_metrics,
            **alpha_beta_metrics,
            **drawdown_metrics,
            **trading_metrics,
        )

        # Store metrics in DB
        await self._store_metrics(metrics)

        # Compute and store currency attribution (if multi-currency portfolio)
        await self._compute_and_store_currency_attribution(
            portfolio_id=portfolio_id,
            pack_id=pack_id,
            asof_date=asof_date,
        )

        return metrics

    async def _compute_and_store_currency_attribution(
        self,
        portfolio_id: str,
        pack_id: str,
        asof_date: date,
    ):
        """
        Compute and store currency attribution for multi-currency portfolios.

        Args:
            portfolio_id: Portfolio ID
            pack_id: Pricing pack ID
            asof_date: As-of date
        """
        if not self.use_db or self.currency_attr is None:
            logger.debug(
                f"Skipping currency attribution for portfolio {portfolio_id} (stub mode)"
            )
            return

        try:
            # TODO: Get portfolio positions and FX rates from database
            # For now, skip if no positions available
            logger.debug(
                f"Currency attribution computation for portfolio {portfolio_id} "
                f"not yet implemented (waiting for position data)"
            )

            # FUTURE IMPLEMENTATION:
            # 1. Get all positions for portfolio on asof_date
            # 2. For each position, get local return and FX return
            # 3. Compute position-level attribution using currency_attr
            # 4. Aggregate to portfolio-level attribution
            # 5. Validate against actual portfolio return (±0.1bp)
            # 6. Store in currency_attribution table via metrics_queries

            # Example code (once position data available):
            # positions = await self._get_portfolio_positions(portfolio_id, asof_date)
            # position_attributions = []
            #
            # for pos in positions:
            #     attr = self.currency_attr.compute_position_attribution(
            #         position_id=pos.id,
            #         currency=pos.currency,
            #         local_return=pos.local_return,
            #         fx_return=pos.fx_return,
            #         weight=pos.weight,
            #     )
            #     position_attributions.append(attr)
            #
            # portfolio_attr = self.currency_attr.compute_portfolio_attribution(
            #     portfolio_id=portfolio_id,
            #     asof_date=asof_date,
            #     position_attributions=position_attributions,
            #     base_return_actual=actual_portfolio_return,
            # )
            #
            # await self.metrics_queries.insert_currency_attribution(
            #     portfolio_id=UUID(portfolio_id),
            #     asof_date=asof_date,
            #     pricing_pack_id=pack_id,
            #     attribution={
            #         'local_return': float(portfolio_attr.local_return),
            #         'fx_return': float(portfolio_attr.fx_return),
            #         'interaction_return': float(portfolio_attr.interaction_return),
            #         'total_return': float(portfolio_attr.total_return),
            #         'base_return_actual': float(portfolio_attr.base_return_actual),
            #         'error_bps': float(portfolio_attr.error_bps),
            #         'attribution_by_currency': portfolio_attr.attribution_by_currency,
            #         'base_currency': portfolio_attr.base_currency,
            #     }
            # )

        except Exception as e:
            logger.error(
                f"Failed to compute currency attribution for portfolio {portfolio_id}: {e}",
                exc_info=True,
            )

    async def _get_active_portfolios(self) -> List[str]:
        """Get list of active portfolio IDs."""
        if not self.use_db:
            logger.debug("Getting active portfolios (stub mode)")
            return []

        # Query DB for active portfolios
        query = """
            SELECT id::text
            FROM portfolios
            WHERE is_active = true
        """

        try:
            from app.db.connection import execute_query
            rows = await execute_query(query)
            portfolio_ids = [row["id"] for row in rows]
            logger.debug(f"Found {len(portfolio_ids)} active portfolios")
            return portfolio_ids
        except Exception as e:
            logger.error(f"Failed to get active portfolios: {e}", exc_info=True)
            return []

    async def _get_portfolio_returns(
        self,
        portfolio_id: str,
        asof_date: date,
        lookback_days: int = 1260,  # ~5 years
    ) -> List[float]:
        """
        Get portfolio daily returns.

        Returns:
            List of daily returns (most recent last)
        """
        if not self.use_db:
            logger.debug(f"Getting returns for portfolio {portfolio_id} (stub mode)")
            # Return stub data: random returns around 0.05% daily
            import random
            return [random.gauss(0.0005, 0.01) for _ in range(min(lookback_days, 252))]

        start_date = asof_date - timedelta(days=lookback_days)

        # Query portfolio_metrics table for historical returns
        query = """
            SELECT asof_date, twr_1d
            FROM portfolio_metrics
            WHERE portfolio_id = $1::uuid
              AND asof_date >= $2
              AND asof_date <= $3
              AND twr_1d IS NOT NULL
            ORDER BY asof_date ASC
        """

        try:
            from app.db.connection import execute_query
            rows = await execute_query(query, portfolio_id, start_date, asof_date)
            returns = [float(row["twr_1d"]) for row in rows]
            logger.debug(f"Loaded {len(returns)} returns for portfolio {portfolio_id}")
            return returns
        except Exception as e:
            logger.warning(f"Failed to load portfolio returns: {e}")
            # Fallback: compute from prices if available
            return []

    async def _get_benchmark_returns(
        self,
        portfolio_id: str,
        asof_date: date,
        lookback_days: int = 1260,
    ) -> List[float]:
        """
        Get benchmark returns hedged to portfolio base currency.

        CRITICAL: Benchmark returns must be hedged to remove FX impact.
        """
        if not self.use_db:
            logger.debug(f"Getting benchmark returns for portfolio {portfolio_id} (stub mode)")
            # Return stub data: market returns around 0.04% daily
            import random
            return [random.gauss(0.0004, 0.012) for _ in range(min(lookback_days, 252))]

        try:
            from app.db.connection import execute_query_one
            from app.services.benchmarks import get_benchmark_service

            # Get portfolio benchmark and base currency
            query = """
                SELECT benchmark_id, base_currency
                FROM portfolios
                WHERE id = $1::uuid
            """
            portfolio = await execute_query_one(query, portfolio_id)

            if not portfolio or not portfolio["benchmark_id"]:
                logger.warning(f"No benchmark configured for portfolio {portfolio_id}")
                return []

            benchmark_id = portfolio["benchmark_id"]
            base_currency = portfolio["base_currency"]

            # Get benchmark returns (hedged to base currency)
            benchmark_service = get_benchmark_service(use_db=self.use_db)
            start_date = asof_date - timedelta(days=lookback_days)

            # Get pack_id for this date
            pack_query = """
                SELECT id
                FROM pricing_packs
                WHERE date <= $1
                ORDER BY date DESC
                LIMIT 1
            """
            pack_row = await execute_query_one(pack_query, asof_date)
            pack_id = pack_row["id"] if pack_row else f"PP_{asof_date}"

            # Load hedged benchmark returns
            returns_array = await benchmark_service.get_benchmark_returns_as_array(
                benchmark_id=benchmark_id,
                start_date=start_date,
                end_date=asof_date,
                pack_id=pack_id,
                hedged=True,  # CRITICAL: Hedge to portfolio base currency
                base_currency=base_currency,
            )

            logger.debug(
                f"Loaded {len(returns_array)} hedged benchmark returns "
                f"for {benchmark_id} (base: {base_currency})"
            )
            return returns_array.tolist()

        except Exception as e:
            logger.error(f"Failed to load benchmark returns: {e}", exc_info=True)
            return []

    async def _get_risk_free_rate(self, asof_date: date) -> Decimal:
        """Get risk-free rate from FRED (DGS10 or DGS3MO)."""
        if not self.use_db:
            logger.debug(f"Getting risk-free rate for {asof_date} (stub mode)")
            return Decimal("0.05")  # Stub: 5%

        # Query FRED indicators table for DGS10 (10-year Treasury)
        query = """
            SELECT value
            FROM macro_indicators
            WHERE series_id = 'DGS10'
              AND asof_date <= $1
            ORDER BY asof_date DESC
            LIMIT 1
        """

        try:
            from app.db.connection import execute_query_one
            row = await execute_query_one(query, asof_date)

            if row and row["value"]:
                # Convert annual rate to daily rate
                annual_rate = Decimal(str(row["value"])) / Decimal("100")
                logger.debug(f"Risk-free rate: {annual_rate:.4%} (from DGS10)")
                return annual_rate

        except Exception as e:
            logger.warning(f"Failed to get risk-free rate from FRED: {e}")

        # Fallback to default rate
        return Decimal("0.05")

    def _compute_twr_metrics(
        self,
        returns: List[float],
        asof_date: date,
    ) -> Dict[str, Optional[Decimal]]:
        """
        Compute time-weighted returns.

        TWR eliminates cash flow impact by computing geometric return.
        Formula: TWR = (1+r1) * (1+r2) * ... * (1+rN) - 1
        """
        if len(returns) == 0:
            return {
                "twr_1d": None,
                "twr_mtd": None,
                "twr_qtd": None,
                "twr_ytd": None,
                "twr_1y": None,
                "twr_3y_ann": None,
                "twr_5y_ann": None,
                "twr_inception_ann": None,
            }

        # Get most recent return as 1-day TWR
        twr_1d = Decimal(str(returns[-1])) if returns else None

        # Helper to compute cumulative return
        def cumulative_return(ret_list):
            if not ret_list:
                return None
            # Geometric linking: (1+r1)*(1+r2)*...*(1+rN) - 1
            cum_ret = np.prod([1 + r for r in ret_list]) - 1
            return Decimal(str(cum_ret))

        # Helper to annualize return
        def annualize_return(cum_ret, num_days):
            if cum_ret is None or num_days <= 0:
                return None
            # Annualized = (1 + cum_ret)^(365/days) - 1
            ann_ret = (1 + float(cum_ret)) ** (365.0 / num_days) - 1
            return Decimal(str(ann_ret))

        # Compute period returns
        # MTD: Month-to-date
        month_start = date(asof_date.year, asof_date.month, 1)
        mtd_days = (asof_date - month_start).days + 1
        twr_mtd = cumulative_return(returns[-mtd_days:]) if len(returns) >= mtd_days else None

        # QTD: Quarter-to-date
        quarter = (asof_date.month - 1) // 3 + 1
        quarter_start = date(asof_date.year, (quarter - 1) * 3 + 1, 1)
        qtd_days = (asof_date - quarter_start).days + 1
        twr_qtd = cumulative_return(returns[-qtd_days:]) if len(returns) >= qtd_days else None

        # YTD: Year-to-date
        year_start = date(asof_date.year, 1, 1)
        ytd_days = (asof_date - year_start).days + 1
        twr_ytd = cumulative_return(returns[-ytd_days:]) if len(returns) >= ytd_days else None

        # 1 Year
        twr_1y = cumulative_return(returns[-252:]) if len(returns) >= 252 else None

        # 3 Year (annualized)
        twr_3y_cum = cumulative_return(returns[-756:]) if len(returns) >= 756 else None
        twr_3y_ann = annualize_return(twr_3y_cum, 756) if twr_3y_cum else None

        # 5 Year (annualized)
        twr_5y_cum = cumulative_return(returns[-1260:]) if len(returns) >= 1260 else None
        twr_5y_ann = annualize_return(twr_5y_cum, 1260) if twr_5y_cum else None

        # Inception (annualized)
        twr_inception_cum = cumulative_return(returns)
        twr_inception_ann = annualize_return(twr_inception_cum, len(returns)) if twr_inception_cum else None

        return {
            "twr_1d": twr_1d,
            "twr_mtd": twr_mtd,
            "twr_qtd": twr_qtd,
            "twr_ytd": twr_ytd,
            "twr_1y": twr_1y,
            "twr_3y_ann": twr_3y_ann,
            "twr_5y_ann": twr_5y_ann,
            "twr_inception_ann": twr_inception_ann,
        }

    async def _compute_mwr_metrics(
        self,
        portfolio_id: str,
        asof_date: date,
    ) -> Dict[str, Optional[Decimal]]:
        """
        Compute money-weighted returns (IRR).

        MWR includes cash flow impact by solving for IRR.
        Formula: 0 = CF0 + CF1/(1+IRR) + CF2/(1+IRR)^2 + ... + CFN/(1+IRR)^N
        """
        # TODO: Implement IRR calculation
        # 1. Get all cash flows (deposits, withdrawals, dividends)
        # 2. Get portfolio values at each date
        # 3. Solve for IRR using Newton-Raphson

        return {
            "mwr_ytd": Decimal("0.0"),
            "mwr_1y": Decimal("0.0"),
            "mwr_3y_ann": Decimal("0.0"),
            "mwr_inception_ann": Decimal("0.0"),
        }

    def _compute_volatility_metrics(
        self,
        returns: List[float],
    ) -> Dict[str, Optional[Decimal]]:
        """
        Compute volatility (standard deviation of returns).

        Volatility = stdev(daily_returns) * sqrt(252) for annualization
        """
        if len(returns) == 0:
            return {
                "volatility_30d": None,
                "volatility_60d": None,
                "volatility_90d": None,
                "volatility_1y": None,
            }

        # Helper to compute annualized volatility
        def annualized_vol(ret_list):
            if not ret_list or len(ret_list) < 2:
                return None
            # Stdev of daily returns * sqrt(252) for annualization
            daily_vol = np.std(ret_list, ddof=1)
            ann_vol = daily_vol * np.sqrt(252)
            return Decimal(str(ann_vol))

        # Compute rolling volatilities
        vol_30d = annualized_vol(returns[-30:]) if len(returns) >= 30 else None
        vol_60d = annualized_vol(returns[-60:]) if len(returns) >= 60 else None
        vol_90d = annualized_vol(returns[-90:]) if len(returns) >= 90 else None
        vol_1y = annualized_vol(returns[-252:]) if len(returns) >= 252 else None

        return {
            "volatility_30d": vol_30d,
            "volatility_60d": vol_60d,
            "volatility_90d": vol_90d,
            "volatility_1y": vol_1y,
        }

    def _compute_sharpe_metrics(
        self,
        returns: List[float],
        risk_free_rate: Decimal,
    ) -> Dict[str, Optional[Decimal]]:
        """
        Compute Sharpe ratio.

        Sharpe = (portfolio_return - risk_free_rate) / volatility
        """
        if len(returns) == 0:
            return {
                "sharpe_30d": None,
                "sharpe_60d": None,
                "sharpe_90d": None,
                "sharpe_1y": None,
            }

        rf = float(risk_free_rate)

        # Helper to compute Sharpe ratio
        def compute_sharpe(ret_list, num_days):
            if not ret_list or len(ret_list) < 2:
                return None

            # Annualized portfolio return
            cum_ret = np.prod([1 + r for r in ret_list]) - 1
            ann_ret = (1 + cum_ret) ** (365.0 / num_days) - 1

            # Annualized volatility
            daily_vol = np.std(ret_list, ddof=1)
            ann_vol = daily_vol * np.sqrt(252)

            if ann_vol == 0:
                return None

            # Sharpe = (return - rf) / volatility
            sharpe = (ann_ret - rf) / ann_vol
            return Decimal(str(sharpe))

        # Compute Sharpe for different windows
        sharpe_30d = compute_sharpe(returns[-30:], 30) if len(returns) >= 30 else None
        sharpe_60d = compute_sharpe(returns[-60:], 60) if len(returns) >= 60 else None
        sharpe_90d = compute_sharpe(returns[-90:], 90) if len(returns) >= 90 else None
        sharpe_1y = compute_sharpe(returns[-252:], 252) if len(returns) >= 252 else None

        return {
            "sharpe_30d": sharpe_30d,
            "sharpe_60d": sharpe_60d,
            "sharpe_90d": sharpe_90d,
            "sharpe_1y": sharpe_1y,
        }

    def _compute_alpha_beta_metrics(
        self,
        returns: List[float],
        benchmark_returns: List[float],
    ) -> Dict[str, Optional[Decimal]]:
        """
        Compute alpha and beta vs benchmark.

        Beta = Cov(portfolio, benchmark) / Var(benchmark)
        Alpha = portfolio_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate))

        CRITICAL: Benchmark returns must be hedged to portfolio base currency.
        """
        if len(returns) == 0 or len(benchmark_returns) == 0:
            return {
                "alpha_1y": None,
                "alpha_3y_ann": None,
                "beta_1y": None,
                "beta_3y": None,
                "tracking_error_1y": None,
                "information_ratio_1y": None,
            }

        # Helper to compute alpha/beta/tracking error
        def compute_alpha_beta(port_rets, bench_rets, num_days):
            # Align lengths
            min_len = min(len(port_rets), len(bench_rets))
            if min_len < 30:  # Need minimum data
                return None, None, None, None

            p_rets = np.array(port_rets[-min_len:])
            b_rets = np.array(bench_rets[-min_len:])

            # Beta = Cov(portfolio, benchmark) / Var(benchmark)
            covariance = np.cov(p_rets, b_rets)[0, 1]
            benchmark_var = np.var(b_rets, ddof=1)

            if benchmark_var == 0:
                beta = Decimal("1.0")
            else:
                beta = Decimal(str(covariance / benchmark_var))

            # Annualized returns
            p_cum_ret = np.prod([1 + r for r in p_rets]) - 1
            b_cum_ret = np.prod([1 + r for r in b_rets]) - 1

            p_ann_ret = (1 + p_cum_ret) ** (365.0 / num_days) - 1
            b_ann_ret = (1 + b_cum_ret) ** (365.0 / num_days) - 1

            # Alpha (assuming rf=0 for simplicity, should use actual rf)
            # Alpha = portfolio_return - beta * benchmark_return
            alpha = Decimal(str(p_ann_ret - float(beta) * b_ann_ret))

            # Tracking error = stdev(portfolio_returns - benchmark_returns) * sqrt(252)
            excess_rets = p_rets - b_rets
            te = Decimal(str(np.std(excess_rets, ddof=1) * np.sqrt(252)))

            # Information ratio = alpha / tracking_error
            if te > 0:
                ir = alpha / te
            else:
                ir = None

            return alpha, beta, te, ir

        # 1-year metrics
        alpha_1y, beta_1y, te_1y, ir_1y = compute_alpha_beta(
            returns[-252:],
            benchmark_returns[-252:],
            252
        ) if len(returns) >= 252 and len(benchmark_returns) >= 252 else (None, None, None, None)

        # 3-year metrics
        alpha_3y, beta_3y, _, _ = compute_alpha_beta(
            returns[-756:],
            benchmark_returns[-756:],
            756
        ) if len(returns) >= 756 and len(benchmark_returns) >= 756 else (None, None, None, None)

        return {
            "alpha_1y": alpha_1y,
            "alpha_3y_ann": alpha_3y,
            "beta_1y": beta_1y,
            "beta_3y": beta_3y,
            "tracking_error_1y": te_1y,
            "information_ratio_1y": ir_1y,
        }

    def _compute_drawdown_metrics(
        self,
        returns: List[float],
    ) -> Dict[str, Optional[Decimal]]:
        """
        Compute max drawdown.

        Drawdown = (peak_value - current_value) / peak_value
        Max Drawdown = max(drawdowns)
        """
        if len(returns) == 0:
            return {
                "max_drawdown_1y": None,
                "max_drawdown_3y": None,
            }

        def compute_max_drawdown(ret_list):
            if not ret_list or len(ret_list) < 2:
                return None

            # Compute cumulative wealth (starting at 1.0)
            cum_wealth = np.cumprod([1 + r for r in ret_list])

            # Track running maximum
            running_max = np.maximum.accumulate(cum_wealth)

            # Drawdown at each point = (running_max - current) / running_max
            drawdowns = (running_max - cum_wealth) / running_max

            # Max drawdown
            max_dd = np.max(drawdowns)

            return Decimal(str(max_dd))

        # Compute max drawdown for different periods
        max_dd_1y = compute_max_drawdown(returns[-252:]) if len(returns) >= 252 else None
        max_dd_3y = compute_max_drawdown(returns[-756:]) if len(returns) >= 756 else None

        return {
            "max_drawdown_1y": max_dd_1y,
            "max_drawdown_3y": max_dd_3y,
        }

    async def _compute_trading_metrics(
        self,
        portfolio_id: str,
        asof_date: date,
    ) -> Dict[str, Optional[Decimal]]:
        """
        Compute trading statistics.

        Metrics:
        - Win rate (% of trades with positive return)
        - Average win (avg return of winning trades)
        - Average loss (avg return of losing trades)
        """
        # TODO: Implement trading metrics
        # 1. Get all closed positions in last year
        # 2. Compute return for each position
        # 3. Calculate win rate, avg win, avg loss

        return {
            "win_rate_1y": Decimal("0.0"),
            "avg_win": Decimal("0.0"),
            "avg_loss": Decimal("0.0"),
        }

    async def _store_metrics(self, metrics: PortfolioMetrics):
        """
        Store metrics in database.

        Args:
            metrics: PortfolioMetrics object to store
        """
        if not self.use_db or self.metrics_queries is None:
            logger.debug(
                f"Skipping DB storage for portfolio {metrics.portfolio_id} (stub mode)"
            )
            return

        try:
            # Convert PortfolioMetrics to dict for database
            metrics_dict = {
                "twr_1d": float(metrics.twr_1d) if metrics.twr_1d else None,
                "twr_mtd": float(metrics.twr_mtd) if metrics.twr_mtd else None,
                "twr_qtd": float(metrics.twr_qtd) if metrics.twr_qtd else None,
                "twr_ytd": float(metrics.twr_ytd) if metrics.twr_ytd else None,
                "twr_1y": float(metrics.twr_1y) if metrics.twr_1y else None,
                "twr_3y_ann": float(metrics.twr_3y_ann) if metrics.twr_3y_ann else None,
                "twr_5y_ann": float(metrics.twr_5y_ann) if metrics.twr_5y_ann else None,
                "twr_inception_ann": (
                    float(metrics.twr_inception_ann) if metrics.twr_inception_ann else None
                ),
                "mwr_ytd": float(metrics.mwr_ytd) if metrics.mwr_ytd else None,
                "mwr_1y": float(metrics.mwr_1y) if metrics.mwr_1y else None,
                "mwr_3y_ann": float(metrics.mwr_3y_ann) if metrics.mwr_3y_ann else None,
                "mwr_inception_ann": (
                    float(metrics.mwr_inception_ann) if metrics.mwr_inception_ann else None
                ),
                "volatility_30d": (
                    float(metrics.volatility_30d) if metrics.volatility_30d else None
                ),
                "volatility_60d": (
                    float(metrics.volatility_60d) if metrics.volatility_60d else None
                ),
                "volatility_90d": (
                    float(metrics.volatility_90d) if metrics.volatility_90d else None
                ),
                "volatility_1y": (
                    float(metrics.volatility_1y) if metrics.volatility_1y else None
                ),
                "sharpe_30d": float(metrics.sharpe_30d) if metrics.sharpe_30d else None,
                "sharpe_60d": float(metrics.sharpe_60d) if metrics.sharpe_60d else None,
                "sharpe_90d": float(metrics.sharpe_90d) if metrics.sharpe_90d else None,
                "sharpe_1y": float(metrics.sharpe_1y) if metrics.sharpe_1y else None,
                "max_drawdown_1y": (
                    float(metrics.max_drawdown_1y) if metrics.max_drawdown_1y else None
                ),
                "max_drawdown_3y": (
                    float(metrics.max_drawdown_3y) if metrics.max_drawdown_3y else None
                ),
                "alpha_1y": float(metrics.alpha_1y) if metrics.alpha_1y else None,
                "alpha_3y_ann": (
                    float(metrics.alpha_3y_ann) if metrics.alpha_3y_ann else None
                ),
                "beta_1y": float(metrics.beta_1y) if metrics.beta_1y else None,
                "beta_3y": float(metrics.beta_3y) if metrics.beta_3y else None,
                "tracking_error_1y": (
                    float(metrics.tracking_error_1y) if metrics.tracking_error_1y else None
                ),
                "information_ratio_1y": (
                    float(metrics.information_ratio_1y)
                    if metrics.information_ratio_1y
                    else None
                ),
                "win_rate_1y": float(metrics.win_rate_1y) if metrics.win_rate_1y else None,
                "avg_win": float(metrics.avg_win) if metrics.avg_win else None,
                "avg_loss": float(metrics.avg_loss) if metrics.avg_loss else None,
                "base_currency": "CAD",  # TODO: Get from portfolio config
            }

            # Insert metrics into database
            await self.metrics_queries.insert_metrics(
                portfolio_id=UUID(metrics.portfolio_id),
                asof_date=metrics.asof_date,
                pricing_pack_id=metrics.pricing_pack_id,
                metrics=metrics_dict,
            )

            logger.info(
                f"Stored metrics for portfolio {metrics.portfolio_id} "
                f"on {metrics.asof_date}"
            )

        except Exception as e:
            logger.error(
                f"Failed to store metrics for portfolio {metrics.portfolio_id}: {e}",
                exc_info=True,
            )


# ===========================
# STANDALONE EXECUTION
# ===========================

async def main():
    """Run metrics computation immediately (for testing)."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python metrics.py <pack_id> [asof_date]")
        sys.exit(1)

    pack_id = sys.argv[1]
    asof_date = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today() - timedelta(days=1)

    # Initialize metrics computer
    computer = MetricsComputer()

    # Compute metrics for all portfolios
    metrics_list = await computer.compute_all_metrics(
        pack_id=pack_id,
        asof_date=asof_date,
    )

    # Print summary
    print(f"Computed metrics for {len(metrics_list)} portfolios")
    for metrics in metrics_list:
        print(f"  Portfolio: {metrics.portfolio_id}")
        print(f"    TWR 1Y: {metrics.twr_1y}")
        print(f"    Vol 1Y: {metrics.volatility_1y}")
        print(f"    Sharpe 1Y: {metrics.sharpe_1y}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(main())
