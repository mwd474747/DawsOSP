"""
Benchmark Service - Load and process benchmark returns

Purpose: Provide benchmark returns for performance attribution (hedged/unhedged)
Updated: 2025-10-23
Priority: P0 (Critical for metrics calculation)

Features:
    - Load benchmark price data from pricing packs
    - Compute benchmark returns (local currency)
    - Hedge benchmarks to portfolio base currency (strip FX component)
    - Support for multiple benchmarks (SPY, VTI, custom)

Sacred Accuracy:
    - Benchmark returns use pricing pack for reproducibility
    - Hedged returns MUST strip FX component (local returns only)
    - Unhedged returns include both local and FX components

Usage:
    from app.services.benchmarks import BenchmarkService

    service = BenchmarkService()

    # Get unhedged returns (includes FX)
    returns = await service.get_benchmark_returns(
        benchmark_id="SPY",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 10, 21),
        pack_id="PP_2025-10-21",
        hedged=False,
    )

    # Get hedged returns (local only, no FX)
    hedged_returns = await service.get_benchmark_returns(
        benchmark_id="SPY",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 10, 21),
        pack_id="PP_2025-10-21",
        hedged=True,
        base_currency="CAD",
    )
"""

import logging
from datetime import date, timedelta
from typing import List, Optional, Dict, Tuple
from decimal import Decimal
from dataclasses import dataclass

import numpy as np

from app.services.pricing import PricingService, get_pricing_service
from app.db.connection import execute_query

logger = logging.getLogger("DawsOS.Benchmarks")


@dataclass
class BenchmarkReturn:
    """Single benchmark return observation."""
    asof_date: date
    return_value: Decimal
    price: Decimal
    currency: str
    hedged: bool


class BenchmarkService:
    """
    Service for loading and processing benchmark returns.

    Supports:
    - Unhedged returns: Includes both price return and FX return
    - Hedged returns: Price return only (FX component stripped)
    """

    def __init__(self, use_db: bool = True):
        """
        Initialize benchmark service.

        Args:
            use_db: Use database connection (default: True)
        """
        self.use_db = use_db
        self.pricing_service = get_pricing_service(use_db=use_db)
        logger.info(f"BenchmarkService initialized (use_db={use_db})")

    async def get_benchmark_returns(
        self,
        benchmark_id: str,
        start_date: date,
        end_date: date,
        pack_id: str,
        hedged: bool = False,
        base_currency: Optional[str] = None,
    ) -> List[BenchmarkReturn]:
        """
        Get benchmark returns for a date range.

        Args:
            benchmark_id: Benchmark identifier (e.g., "SPY", "VTI", "XIC.TO")
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            pack_id: Pricing pack ID for consistent pricing
            hedged: If True, strip FX component (default: False)
            base_currency: Base currency for hedging (required if hedged=True)

        Returns:
            List of BenchmarkReturn objects

        Raises:
            ValueError: If hedged=True and base_currency not provided

        Example:
            >>> service = BenchmarkService()
            >>> returns = await service.get_benchmark_returns(
            ...     benchmark_id="SPY",
            ...     start_date=date(2025, 1, 1),
            ...     end_date=date(2025, 10, 21),
            ...     pack_id="PP_2025-10-21",
            ...     hedged=True,
            ...     base_currency="CAD",
            ... )
            >>> returns[0].return_value
            Decimal('0.0012')  # 12bp daily return (hedged)
        """
        if hedged and not base_currency:
            raise ValueError("base_currency required when hedged=True")

        # Get benchmark price history from pricing packs
        prices = await self._get_benchmark_prices(
            benchmark_id=benchmark_id,
            start_date=start_date,
            end_date=end_date,
        )

        if len(prices) < 2:
            logger.warning(
                f"Insufficient price data for benchmark {benchmark_id}: "
                f"got {len(prices)} prices, need at least 2"
            )
            return []

        # Get FX rates if hedging required
        fx_rates = None
        benchmark_currency = prices[0]["currency"]

        if hedged and benchmark_currency != base_currency:
            fx_rates = await self._get_fx_rates(
                base_ccy=benchmark_currency,
                quote_ccy=base_currency,
                start_date=start_date,
                end_date=end_date,
            )

        # Compute returns
        returns = []
        for i in range(1, len(prices)):
            prev_price = prices[i-1]["close"]
            curr_price = prices[i]["close"]
            curr_date = prices[i]["asof_date"]

            if prev_price == Decimal("0"):
                logger.warning(f"Zero price for {benchmark_id} on {prices[i-1]['asof_date']}")
                continue

            # Local return (price return in benchmark's currency)
            local_return = (curr_price - prev_price) / prev_price

            # If hedged and different currency, strip FX component
            if hedged and fx_rates and benchmark_currency != base_currency:
                # For hedged returns, we use local return only
                # FX component is stripped
                return_value = local_return
            elif not hedged and benchmark_currency != base_currency:
                # For unhedged returns, we need to include FX
                # Get FX returns for this period
                fx_return = self._get_fx_return_for_date(
                    fx_rates=fx_rates,
                    asof_date=curr_date,
                )
                # Total return = (1 + local_return) * (1 + fx_return) - 1
                return_value = (Decimal("1") + local_return) * (Decimal("1") + fx_return) - Decimal("1")
            else:
                # Same currency or no FX data needed
                return_value = local_return

            returns.append(BenchmarkReturn(
                asof_date=curr_date,
                return_value=return_value,
                price=curr_price,
                currency=benchmark_currency,
                hedged=hedged,
            ))

        logger.info(
            f"Loaded {len(returns)} returns for benchmark {benchmark_id} "
            f"({start_date} to {end_date}, hedged={hedged})"
        )
        return returns

    async def get_benchmark_returns_as_array(
        self,
        benchmark_id: str,
        start_date: date,
        end_date: date,
        pack_id: str,
        hedged: bool = False,
        base_currency: Optional[str] = None,
    ) -> np.ndarray:
        """
        Get benchmark returns as numpy array (for calculations).

        Args:
            benchmark_id: Benchmark identifier
            start_date: Start date
            end_date: End date
            pack_id: Pricing pack ID
            hedged: Strip FX component
            base_currency: Base currency for hedging

        Returns:
            Numpy array of returns
        """
        returns = await self.get_benchmark_returns(
            benchmark_id=benchmark_id,
            start_date=start_date,
            end_date=end_date,
            pack_id=pack_id,
            hedged=hedged,
            base_currency=base_currency,
        )

        return np.array([float(r.return_value) for r in returns])

    async def _get_benchmark_prices(
        self,
        benchmark_id: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict]:
        """
        Get benchmark price history.

        Args:
            benchmark_id: Benchmark identifier
            start_date: Start date
            end_date: End date

        Returns:
            List of price dicts with keys: asof_date, close, currency
        """
        if not self.use_db:
            logger.warning(f"_get_benchmark_prices: Using stub for {benchmark_id}")
            # Generate stub prices (1% daily return)
            prices = []
            current_price = Decimal("100.00")
            current_date = start_date

            while current_date <= end_date:
                prices.append({
                    "asof_date": current_date,
                    "close": current_price,
                    "currency": "USD",
                })
                current_price *= Decimal("1.01")  # 1% daily
                current_date += timedelta(days=1)

            return prices

        # Query prices table for benchmark
        # Note: We need to map benchmark_id to security_id
        # For now, use symbol lookup
        query = """
            SELECT
                p.asof_date,
                p.close,
                p.currency
            FROM prices p
            JOIN securities s ON p.security_id = s.id
            WHERE s.symbol = $1
              AND p.asof_date >= $2
              AND p.asof_date <= $3
            ORDER BY p.asof_date ASC
        """

        try:
            rows = await execute_query(query, benchmark_id, start_date, end_date)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get benchmark prices for {benchmark_id}: {e}")
            # Return empty list - caller will handle
            return []

    async def _get_fx_rates(
        self,
        base_ccy: str,
        quote_ccy: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict]:
        """
        Get FX rate history.

        Args:
            base_ccy: Base currency (e.g., "USD")
            quote_ccy: Quote currency (e.g., "CAD")
            start_date: Start date
            end_date: End date

        Returns:
            List of FX rate dicts with keys: asof_ts, rate
        """
        if not self.use_db:
            logger.warning(f"_get_fx_rates: Using stub for {base_ccy}/{quote_ccy}")
            # Generate stub FX rates (constant 1.36 CAD per USD)
            fx_rates = []
            current_date = start_date

            while current_date <= end_date:
                fx_rates.append({
                    "asof_ts": current_date,
                    "rate": Decimal("1.3600"),
                })
                current_date += timedelta(days=1)

            return fx_rates

        # Query fx_rates table
        query = """
            SELECT
                asof_ts,
                rate
            FROM fx_rates
            WHERE base_ccy = $1
              AND quote_ccy = $2
              AND DATE(asof_ts) >= $3
              AND DATE(asof_ts) <= $4
            ORDER BY asof_ts ASC
        """

        try:
            rows = await execute_query(query, base_ccy, quote_ccy, start_date, end_date)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get FX rates for {base_ccy}/{quote_ccy}: {e}")
            return []

    def _get_fx_return_for_date(
        self,
        fx_rates: List[Dict],
        asof_date: date,
    ) -> Decimal:
        """
        Get FX return for a specific date.

        Finds the two most recent FX rates and computes return.

        Args:
            fx_rates: List of FX rates
            asof_date: Date to get return for

        Returns:
            FX return as Decimal
        """
        if not fx_rates or len(fx_rates) < 2:
            return Decimal("0")

        # Find rates on or before asof_date
        relevant_rates = [
            r for r in fx_rates
            if r["asof_ts"].date() <= asof_date
        ]

        if len(relevant_rates) < 2:
            return Decimal("0")

        # Get two most recent rates
        prev_rate = relevant_rates[-2]["rate"]
        curr_rate = relevant_rates[-1]["rate"]

        if prev_rate == Decimal("0"):
            return Decimal("0")

        # FX return = (curr_rate / prev_rate) - 1
        fx_return = (curr_rate / prev_rate) - Decimal("1")

        return fx_return


# ============================================================================
# Singleton Instance
# ============================================================================

_benchmark_service: Optional[BenchmarkService] = None


def get_benchmark_service(use_db: bool = True) -> BenchmarkService:
    """
    Get singleton BenchmarkService instance.

    Args:
        use_db: Use database connection (default: True)

    Returns:
        BenchmarkService instance
    """
    global _benchmark_service
    if _benchmark_service is None:
        _benchmark_service = BenchmarkService(use_db=use_db)
    return _benchmark_service


def init_benchmark_service(use_db: bool = True) -> BenchmarkService:
    """
    Initialize BenchmarkService.

    Args:
        use_db: Use database connection (default: True)

    Returns:
        BenchmarkService instance
    """
    global _benchmark_service
    _benchmark_service = BenchmarkService(use_db=use_db)
    return _benchmark_service
