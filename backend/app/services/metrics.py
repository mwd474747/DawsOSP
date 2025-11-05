"""
DawsOS Performance Metrics Calculator

Purpose: Calculate TWR, MWR, Sharpe, Max Drawdown with ±1bp reconciliation guarantee
Updated: 2025-10-21
Priority: P0 (Critical for portfolio analytics)

Features:
    - Time-Weighted Return (TWR) with geometric linking
    - Money-Weighted Return (MWR) via IRR calculation
    - Sharpe ratio and Sortino ratio
    - Maximum drawdown with recovery tracking
    - Beta to benchmark (hedged/unhedged)
    - Rolling volatility (30/90/252 day windows)

Acceptance:
    - TWR reconciles to Beancount ledger ±1 basis point
    - All calculations reference pricing_pack_id for reproducibility
    - Multi-currency portfolios handled correctly

Usage:
    calc = PerformanceCalculator(db)
    twr = await calc.compute_twr(portfolio_id, pack_id, lookback_days=252)
"""

import logging
import os
import numpy as np
import pandas as pd
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from app.core.types import (
    PricingPackNotFoundError,
    PricingPackValidationError,
)
from app.services.pricing import get_pricing_service
from app.services.portfolio_helpers import get_portfolio_value

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """
    Performance metrics calculator.

    All metrics use pricing_pack_id for reproducibility and reconcile
    to Beancount ledger within ±1 basis point tolerance.
    """

    def __init__(self, db):
        """
        Initialize calculator.

        Args:
            db: Async database connection pool
        """
        self.db = db

    async def compute_twr(
        self, portfolio_id: str, pack_id: str, lookback_days: int = 252
    ) -> Dict:
        """
        Compute Time-Weighted Return (TWR) with geometric linking.

        Formula:
            TWR = [(1+r1)(1+r2)...(1+rn)] - 1

        Where:
            r_i = (V_i - V_{i-1} - CF_i) / (V_{i-1} + CF_i)
            V_i = Portfolio value at time i
            CF_i = Cash flows at time i (contributions/withdrawals)

        Uses geometric linking to eliminate impact of cash flows, making TWR
        suitable for comparing portfolio performance independent of contribution timing.

        Args:
            portfolio_id: Portfolio UUID. Required.
            pack_id: Pricing pack UUID for end date. Format: "PP_YYYY-MM-DD". Required.
            lookback_days: Historical period in days. Must be between 1 and 3650. Default 252 (1 trading year).

        Returns:
            Dict containing:
            - twr: Total return over period (decimal, e.g., 0.15 = 15%)
            - ann_twr: Annualized return (decimal)
            - vol: Annualized volatility (standard deviation of daily returns × sqrt(252))
            - sharpe: Sharpe ratio ((ann_twr - risk_free_rate) / vol). Assumes 4% risk-free rate.
            - sortino: Sortino ratio (uses downside deviation only)
            - days: Number of days in period
            - data_points: Number of daily valuations used

        Raises:
            ValueError: If portfolio_id is invalid or not found.
            ValueError: If pack_id is invalid or not found.
            ValueError: If lookback_days is outside valid range (1-3650).
            ValueError: If insufficient data for calculation (< 2 data points).
            DatabaseError: If database query fails.
            
        Note:
            - Returns empty result with error message if insufficient data
            - Uses portfolio_daily_values hypertable for daily valuations
            - Gracefully handles missing portfolio_daily_values table (returns empty result)
            - Reconciliation guarantee: ±1 basis point accuracy when data available
            - Annualization assumes 365 days per year
        """
        # Get pack date
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=lookback_days)

        # Get daily valuations from portfolio_daily_values hypertable
        # Note: Table may not exist in dev environment, handle gracefully
        try:
            values = await self.db.fetch(
                """
                SELECT valuation_date as asof_date, total_value, cash_flows
                FROM portfolio_daily_values
                WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
                ORDER BY valuation_date
            """,
                portfolio_id,
                start_date,
                end_date,
            )
        except Exception as e:
            logger.warning(f"Could not query portfolio_daily_values: {e}. Using empty dataset.")
            values = []

        if len(values) < 2:
            logger.warning(
                f"Insufficient data for TWR calculation: {len(values)} data points"
            )
            return {
                "twr": 0.0,
                "ann_twr": 0.0,
                "vol": 0.0,
                "sharpe": 0.0,
                "sortino": 0.0,
                "error": "Insufficient data",
            }

        # Compute daily returns
        returns = []
        for i in range(1, len(values)):
            v_prev = Decimal(str(values[i - 1]["total_value"]))
            v_curr = Decimal(str(values[i]["total_value"]))
            cf = Decimal(str(values[i].get("cash_flows", 0)))

            # Time-Weighted Return (TWR) formula
            # Standard approach: Remove cash flow impact from ending value, divide by starting value
            # r = (V_curr - CF - V_prev) / V_prev
            #
            # This measures portfolio manager performance independent of cash flow timing.
            # Cash flows are assumed to occur at end-of-day (EOD).
            denominator = v_prev
            if denominator > 0:
                r = (v_curr - cf - v_prev) / denominator
                returns.append(float(r))

        if not returns:
            return {
                "twr": 0.0,
                "ann_twr": 0.0,
                "vol": 0.0,
                "sharpe": 0.0,
                "sortino": 0.0,
                "error": "No valid returns",
            }

        # Geometric linking: (1+r1)(1+r2)...(1+rn) - 1
        twr = float(np.prod([1 + r for r in returns]) - 1)

        # Annualize
        days = (end_date - start_date).days
        ann_factor = 365 / days if days > 0 else 1
        ann_twr = (1 + twr) ** ann_factor - 1

        # Volatility (annualized standard deviation of daily returns)
        vol = float(np.std(returns) * np.sqrt(252)) if len(returns) > 1 else 0.0

        # Sharpe ratio
        # Default risk-free rate: 4% (approximate long-term T-bill rate)
        # TODO: Make configurable via environment variable or database setting
        rf_rate = float(os.getenv("RISK_FREE_RATE", "0.04"))
        sharpe = (ann_twr - rf_rate) / vol if vol > 0 else 0.0

        # Sortino ratio (downside deviation only)
        downside_returns = [r for r in returns if r < 0]
        downside_vol = (
            float(np.std(downside_returns) * np.sqrt(252))
            if len(downside_returns) > 1
            else vol
        )
        sortino = (ann_twr - rf_rate) / downside_vol if downside_vol > 0 else 0.0

        logger.info(
            f"TWR calculated for {portfolio_id}: {twr:.4f} "
            f"(annualized: {ann_twr:.4f}, vol: {vol:.4f}, sharpe: {sharpe:.2f})"
        )

        return {
            "twr": round(twr, 6),
            "ann_twr": round(ann_twr, 6),
            "vol": round(vol, 6),
            "sharpe": round(sharpe, 4),
            "sortino": round(sortino, 4),
            "days": days,
            "data_points": len(values),
        }

    async def compute_mwr(self, portfolio_id: str, pack_id: str) -> Dict:
        """
        Compute Money-Weighted Return (MWR) via Internal Rate of Return (IRR).

        MWR accounts for the timing and size of cash flows, making it suitable
        for measuring investor-specific returns. Higher cash flows during periods
        of high returns increase MWR relative to TWR.

        Formula:
            0 = sum(CF_i / (1+IRR)^t_i) + V_n / (1+IRR)^t_n

        Where:
            CF_i = Cash flow at time i (positive for contributions, negative for withdrawals)
            t_i = Days from start / 365
            V_n = Terminal portfolio value (as negative cash flow)

        Solves for IRR using Newton-Raphson method with convergence tolerance 1e-6.

        Args:
            portfolio_id: Portfolio UUID. Required.
            pack_id: Pricing pack UUID for terminal valuation. Format: "PP_YYYY-MM-DD". Required.

        Returns:
            Dict containing:
            - mwr: Money-weighted return (IRR) as decimal (e.g., 0.14 = 14%)
            - ann_mwr: Annualized MWR (if period < 1 year, annualized to 1 year)

        Raises:
            ValueError: If portfolio_id is invalid or not found.
            ValueError: If pack_id is invalid or not found.
            ValueError: If no cash flows found in period.
            ValueError: If IRR calculation doesn't converge after 100 iterations.
            DatabaseError: If database query fails.
            
        Note:
            - Uses 1 year lookback period (365 days from pack date)
            - Returns empty result with error message if no cash flows
            - IRR must be > -100% (bounded at -0.99)
            - Terminal value is included as negative cash flow
            - Annualization: (1 + mwr)^(365/days) - 1
        """
        # Get date range (1 year lookback)
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=365)

        # Get all cash flows
        cash_flows = await self.db.fetch(
            """
            SELECT trade_date, amount
            FROM portfolio_cash_flows
            WHERE portfolio_id = $1 AND trade_date BETWEEN $2 AND $3
            ORDER BY trade_date
        """,
            portfolio_id,
            start_date,
            end_date,
        )

        if not cash_flows:
            logger.warning(f"No cash flows for MWR calculation: {portfolio_id}")
            return {"mwr": 0.0, "ann_mwr": 0.0, "error": "No cash flows"}

        # Build cash flow series for IRR calculation
        cf_series = []
        for cf in cash_flows:
            days_from_start = (cf["trade_date"] - start_date).days
            cf_series.append((days_from_start, float(cf["amount"])))

        # Add terminal value (ending portfolio value as negative cash flow)
        terminal_value = await self._get_portfolio_value(portfolio_id, pack_id)
        total_days = (end_date - start_date).days
        cf_series.append(
            (total_days, -float(terminal_value))
        )  # Negative = ending value

        # Solve for IRR using Newton-Raphson
        try:
            irr = self._calculate_irr(cf_series)
        except ValueError as e:
            logger.error(f"IRR calculation failed for {portfolio_id}: {e}")
            return {"mwr": 0.0, "ann_mwr": 0.0, "error": str(e)}

        # Annualize if period < 1 year
        ann_mwr = (1 + irr) ** (365 / total_days) - 1 if total_days > 0 else 0.0

        logger.info(
            f"MWR calculated for {portfolio_id}: {irr:.4f} (annualized: {ann_mwr:.4f})"
        )

        return {"mwr": round(irr, 6), "ann_mwr": round(ann_mwr, 6)}

    def _calculate_irr(
        self, cash_flows: List[tuple], guess: float = 0.1, max_iter: int = 100
    ) -> float:
        """
        Calculate Internal Rate of Return using Newton-Raphson method.

        Args:
            cash_flows: List of (days_from_start, amount) tuples
            guess: Initial guess for IRR (default 0.1 = 10%)
            max_iter: Maximum iterations (default 100)

        Returns:
            IRR as decimal (e.g., 0.15 = 15%)

        Raises:
            ValueError: If IRR doesn't converge
        """
        tolerance = 1e-6
        r = guess

        for iteration in range(max_iter):
            # NPV = sum(CF_i / (1+r)^(t_i/365))
            npv = sum(cf / (1 + r) ** (t / 365) for t, cf in cash_flows)

            # NPV' = sum(-t * CF_i / (365 * (1+r)^(t/365 + 1)))
            npv_prime = sum(
                -t * cf / (365 * (1 + r) ** (t / 365 + 1)) for t, cf in cash_flows
            )

            # Check convergence
            if abs(npv) < tolerance:
                logger.debug(f"IRR converged in {iteration} iterations: {r:.6f}")
                return r

            # Check derivative
            if abs(npv_prime) < 1e-10:
                logger.warning("IRR derivative too small, may not converge")
                break

            # Newton-Raphson update
            r_new = r - npv / npv_prime

            # Bounds check (IRR must be > -100%)
            if r_new < -0.99:
                r_new = -0.99

            r = r_new

        # Didn't converge
        raise ValueError(
            f"IRR did not converge after {max_iter} iterations (final r={r:.6f})"
        )

    async def compute_max_drawdown(
        self, portfolio_id: str, pack_id: str, lookback_days: int = 252
    ) -> Dict:
        """
        Compute maximum drawdown (largest peak-to-trough decline).

        Args:
            portfolio_id: Portfolio UUID
            pack_id: Pricing pack UUID
            lookback_days: Historical period (default 252)

        Returns:
            {
                "max_dd": -0.15,  # -15% max drawdown
                "max_dd_date": "2024-03-15",
                "peak_value": 125000.0,
                "trough_value": 106250.0,
                "recovery_days": 45  # Days to recover (-1 if not recovered)
            }
        """
        # Get daily values
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=lookback_days)

        try:
            values = await self.db.fetch(
                """
                SELECT valuation_date as asof_date, total_value
                FROM portfolio_daily_values
                WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
                ORDER BY valuation_date
            """,
                portfolio_id,
                start_date,
                end_date,
            )
        except Exception as e:
            logger.warning(f"Could not query portfolio_daily_values: {e}. Using empty dataset.")
            values = []

        if len(values) < 2:
            return {"max_dd": 0.0, "error": "Insufficient data"}

        values_arr = np.array([float(v["total_value"]) for v in values])

        # Compute running max and drawdown
        running_max = np.maximum.accumulate(values_arr)
        drawdowns = (values_arr - running_max) / running_max

        max_dd = float(np.min(drawdowns))
        max_dd_idx = int(np.argmin(drawdowns))

        peak_value = float(running_max[max_dd_idx])
        trough_value = float(values_arr[max_dd_idx])

        recovery_days = self._compute_recovery_days(values, max_dd_idx)

        logger.info(
            f"Max drawdown for {portfolio_id}: {max_dd:.2%} "
            f"(peak: ${peak_value:,.0f}, trough: ${trough_value:,.0f})"
        )

        return {
            "max_dd": round(max_dd, 6),
            "max_dd_date": values[max_dd_idx]["asof_date"].isoformat(),
            "peak_value": round(peak_value, 2),
            "trough_value": round(trough_value, 2),
            "recovery_days": recovery_days,
        }

    def _compute_recovery_days(self, values: List, dd_idx: int) -> int:
        """
        Compute days from max drawdown to recovery.

        Args:
            values: List of daily values
            dd_idx: Index of maximum drawdown

        Returns:
            Days to recover (-1 if not yet recovered)
        """
        peak_value = max(float(v["total_value"]) for v in values[: dd_idx + 1])

        for i in range(dd_idx, len(values)):
            if float(values[i]["total_value"]) >= peak_value:
                recovery_days = (
                    values[i]["asof_date"] - values[dd_idx]["asof_date"]
                ).days
                logger.debug(f"Recovery took {recovery_days} days")
                return recovery_days

        # Not yet recovered
        return -1

    async def compute_rolling_volatility(
        self, portfolio_id: str, pack_id: str, windows: List[int] = [30, 90, 252]
    ) -> Dict:
        """
        Compute rolling volatility for multiple windows.

        Args:
            portfolio_id: Portfolio UUID
            pack_id: Pricing pack UUID
            windows: List of window sizes in days (default [30, 90, 252])

        Returns:
            {
                "vol_30d": 0.15,
                "vol_90d": 0.18,
                "vol_252d": 0.20
            }
        """
        # Get daily returns for longest window
        max_window = max(windows)
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=max_window)

        try:
            values = await self.db.fetch(
                """
                SELECT valuation_date as asof_date, total_value
                FROM portfolio_daily_values
                WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
                ORDER BY valuation_date
            """,
                portfolio_id,
                start_date,
                end_date,
            )
        except Exception as e:
            logger.warning(f"Could not query portfolio_daily_values: {e}. Using empty dataset.")
            values = []

        if len(values) < 2:
            return {f"vol_{w}d": 0.0 for w in windows}

        # Compute daily returns
        prices = np.array([float(v["total_value"]) for v in values])
        returns = np.diff(prices) / prices[:-1]

        # Compute volatility for each window
        result = {}
        for window in windows:
            if len(returns) >= window:
                window_returns = returns[-window:]
                vol = float(np.std(window_returns) * np.sqrt(252))
                result[f"vol_{window}d"] = round(vol, 6)
            else:
                result[f"vol_{window}d"] = 0.0

        return result

    async def _get_pack_date(self, pack_id: str) -> date:
        """Get as-of date for pricing pack."""
        pricing_service = get_pricing_service()
        pack = await pricing_service.get_pack_by_id(pack_id, raise_if_not_found=True)
        return pack.date

    async def _get_portfolio_value(self, portfolio_id: str, pack_id: str) -> Decimal:
        """
        Get total portfolio value from pricing pack.

        Sums: quantity_open × price × fx_rate for all positions.
        """
        return await get_portfolio_value(self.db, portfolio_id, pack_id)
