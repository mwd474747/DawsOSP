# Ratings & Optimizer Implementation Specification

**Extracted From**: IMPLEMENTATION_ROADMAP_V2.md (Sprint 4)
**Date**: October 24, 2025
**Status**: Specification Ready for Implementation
**Priority**: P1 (Critical missing features)

This document captures the detailed implementation specifications for the Ratings and Optimizer services from the original roadmap, ensuring no valuable design work is lost.

---

## 1. Ratings Service (`backend/app/services/ratings.py`)

### Overview

Implements **Buffett Quality Framework** with three rating dimensions:
1. **Dividend Safety** (0-10) - Sustainability of dividend payments
2. **Moat Strength** (0-10) - Competitive advantage durability
3. **Resilience** (0-10) - Financial fortress strength

### 1.1 Dividend Safety Rating

**Purpose**: Assess dividend payment sustainability

**Components** (weighted):
- Payout Ratio (30%) - Lower is better, < 50% ideal
- FCF Coverage (35%) - Higher is better, > 2x ideal
- Growth Streak (20%) - Years of consecutive dividend growth
- Net Cash (15%) - Positive balance sheet strength

**Implementation**:

```python
# backend/app/services/ratings.py

from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class RatingsService:
    """Buffett quality ratings service."""

    def __init__(self, db_pool, providers):
        self.db_pool = db_pool
        self.providers = providers

    async def compute_dividend_safety(
        self,
        symbol: str,
        pack_id: UUID
    ) -> Dict[str, Any]:
        """
        Compute Dividend Safety score (0-10 scale).

        Args:
            symbol: Stock ticker symbol
            pack_id: Pricing pack ID for fundamental data

        Returns:
            Dict with:
                - score: float (0-10)
                - components: dict of sub-scores
                - inputs: dict of raw inputs
                - method_version: "div_safety_v1"
        """
        # Fetch fundamentals from FMP
        fundamentals = await self._fetch_fundamentals(symbol, pack_id)

        # 1. Payout ratio score (30% weight)
        payout_ratio = self._safe_divide(
            fundamentals.get("dividendsPaid", 0),
            fundamentals.get("netIncome", 1)
        )

        if payout_ratio < 0.3:
            payout_score = 10.0
        elif payout_ratio < 0.5:
            # Linear scale: 0.3-0.5 → 10-7
            payout_score = 10.0 - ((payout_ratio - 0.3) * 15)
        elif payout_ratio < 0.8:
            # Linear scale: 0.5-0.8 → 7-3
            payout_score = 7.0 - ((payout_ratio - 0.5) * 13.3)
        else:
            # > 0.8 is concerning
            payout_score = max(0, 3.0 - ((payout_ratio - 0.8) * 5))

        # 2. FCF coverage score (35% weight)
        fcf_coverage = self._safe_divide(
            fundamentals.get("freeCashFlow", 0),
            fundamentals.get("dividendsPaid", 1)
        )

        if fcf_coverage >= 2.0:
            fcf_score = 10.0
        elif fcf_coverage >= 1.0:
            # 1x-2x → 5-10
            fcf_score = 5.0 + ((fcf_coverage - 1.0) * 5)
        else:
            # < 1x is red flag
            fcf_score = max(0, fcf_coverage * 5)

        # 3. Growth streak score (20% weight)
        growth_streak_years = await self._compute_growth_streak(symbol)
        streak_score = min(10.0, growth_streak_years)  # 10+ years = max score

        # 4. Net cash score (15% weight)
        net_cash = (
            fundamentals.get("cashAndEquivalents", 0) -
            fundamentals.get("totalDebt", 0)
        )

        if net_cash > 0:
            # Positive net cash is good
            cash_score = 10.0
        elif net_cash > -fundamentals.get("totalEquity", 1) * 0.3:
            # Manageable debt (< 30% of equity)
            cash_score = 7.0
        else:
            # High debt load
            cash_score = max(0, 5.0 + (net_cash / fundamentals.get("totalEquity", 1)) * 10)

        # Weighted average
        div_safety = (
            0.30 * payout_score +
            0.35 * fcf_score +
            0.20 * streak_score +
            0.15 * cash_score
        )

        return {
            "score": round(div_safety, 1),
            "components": {
                "payout_score": round(payout_score, 1),
                "fcf_score": round(fcf_score, 1),
                "streak_score": round(streak_score, 1),
                "cash_score": round(cash_score, 1),
            },
            "inputs": {
                "payout_ratio": round(payout_ratio, 3),
                "fcf_coverage": round(fcf_coverage, 2),
                "growth_streak_years": growth_streak_years,
                "net_cash": float(net_cash),
            },
            "method_version": "div_safety_v1",
            "symbol": symbol,
            "pack_id": str(pack_id),
            "computed_at": datetime.utcnow().isoformat(),
        }

    async def compute_moat_strength(
        self,
        symbol: str,
        pack_id: UUID
    ) -> Dict[str, Any]:
        """
        Compute Economic Moat score (0-10 scale).

        Components:
            - ROE consistency (25%) - Stable high returns
            - Gross margin (25%) - Pricing power
            - Intangibles ratio (25%) - Brand/IP value
            - Switching costs (25%) - Customer lock-in proxy

        Returns:
            Dict with score, components, inputs, method_version
        """
        fundamentals = await self._fetch_fundamentals(symbol, pack_id)
        historical = await self._fetch_historical_ratios(symbol, years=5)

        # 1. ROE consistency (25% weight)
        roe_values = [h.get("returnOnEquity", 0) for h in historical]
        avg_roe = sum(roe_values) / len(roe_values) if roe_values else 0
        roe_std = self._std_dev(roe_values)

        # High ROE + low volatility = strong moat
        if avg_roe > 0.20 and roe_std < 0.05:
            roe_score = 10.0
        elif avg_roe > 0.15:
            roe_score = 7.0 - (roe_std * 50)  # Penalize volatility
        else:
            roe_score = max(0, avg_roe * 35)

        # 2. Gross margin (25% weight)
        gross_margin = self._safe_divide(
            fundamentals.get("grossProfit", 0),
            fundamentals.get("revenue", 1)
        )

        if gross_margin > 0.60:
            margin_score = 10.0
        elif gross_margin > 0.40:
            margin_score = 5.0 + ((gross_margin - 0.40) * 25)
        else:
            margin_score = max(0, gross_margin * 12.5)

        # 3. Intangibles ratio (25% weight)
        intangibles_ratio = self._safe_divide(
            fundamentals.get("intangibleAssets", 0) +
            fundamentals.get("goodwill", 0),
            fundamentals.get("totalAssets", 1)
        )

        # 10-40% is ideal (meaningful but not excessive goodwill)
        if 0.10 <= intangibles_ratio <= 0.40:
            intangibles_score = 10.0
        elif intangibles_ratio < 0.10:
            intangibles_score = intangibles_ratio * 100
        else:
            # > 40% could indicate overpayment for acquisitions
            intangibles_score = max(0, 10.0 - ((intangibles_ratio - 0.40) * 20))

        # 4. Switching costs proxy (25% weight)
        # Use R&D intensity + customer concentration as proxy
        rd_intensity = self._safe_divide(
            fundamentals.get("researchAndDevelopmentExpenses", 0),
            fundamentals.get("revenue", 1)
        )

        # Higher R&D = more proprietary tech = higher switching costs
        if rd_intensity > 0.15:
            switching_score = 10.0
        elif rd_intensity > 0.05:
            switching_score = 5.0 + ((rd_intensity - 0.05) * 50)
        else:
            switching_score = max(0, rd_intensity * 100)

        # Weighted average
        moat_strength = (
            0.25 * roe_score +
            0.25 * margin_score +
            0.25 * intangibles_score +
            0.25 * switching_score
        )

        return {
            "score": round(moat_strength, 1),
            "components": {
                "roe_score": round(roe_score, 1),
                "margin_score": round(margin_score, 1),
                "intangibles_score": round(intangibles_score, 1),
                "switching_score": round(switching_score, 1),
            },
            "inputs": {
                "avg_roe": round(avg_roe, 3),
                "roe_std": round(roe_std, 3),
                "gross_margin": round(gross_margin, 3),
                "intangibles_ratio": round(intangibles_ratio, 3),
                "rd_intensity": round(rd_intensity, 3),
            },
            "method_version": "moat_strength_v1",
            "symbol": symbol,
            "pack_id": str(pack_id),
            "computed_at": datetime.utcnow().isoformat(),
        }

    async def compute_resilience(
        self,
        symbol: str,
        pack_id: UUID
    ) -> Dict[str, Any]:
        """
        Compute Financial Resilience score (0-10 scale).

        Components:
            - Debt-to-Equity (30%) - Balance sheet strength
            - Interest Coverage (30%) - Debt serviceability
            - Current Ratio (20%) - Short-term liquidity
            - Margin Stability (20%) - Earnings consistency

        Returns:
            Dict with score, components, inputs, method_version
        """
        fundamentals = await self._fetch_fundamentals(symbol, pack_id)
        historical = await self._fetch_historical_ratios(symbol, years=5)

        # 1. Debt-to-Equity (30% weight)
        debt_to_equity = self._safe_divide(
            fundamentals.get("totalDebt", 0),
            fundamentals.get("totalEquity", 1)
        )

        if debt_to_equity < 0.3:
            de_score = 10.0
        elif debt_to_equity < 0.6:
            de_score = 10.0 - ((debt_to_equity - 0.3) * 20)
        elif debt_to_equity < 1.0:
            de_score = 4.0 - ((debt_to_equity - 0.6) * 7.5)
        else:
            de_score = max(0, 1.0 - ((debt_to_equity - 1.0) * 2))

        # 2. Interest Coverage (30% weight)
        interest_coverage = self._safe_divide(
            fundamentals.get("ebit", 0),
            fundamentals.get("interestExpense", 1)
        )

        if interest_coverage >= 10:
            coverage_score = 10.0
        elif interest_coverage >= 5:
            coverage_score = 7.0 + ((interest_coverage - 5) * 0.6)
        elif interest_coverage >= 2:
            coverage_score = 4.0 + ((interest_coverage - 2) * 1.0)
        else:
            coverage_score = max(0, interest_coverage * 2)

        # 3. Current Ratio (20% weight)
        current_ratio = self._safe_divide(
            fundamentals.get("totalCurrentAssets", 0),
            fundamentals.get("totalCurrentLiabilities", 1)
        )

        if current_ratio >= 2.0:
            liquidity_score = 10.0
        elif current_ratio >= 1.5:
            liquidity_score = 7.0 + ((current_ratio - 1.5) * 6)
        elif current_ratio >= 1.0:
            liquidity_score = 3.0 + ((current_ratio - 1.0) * 8)
        else:
            liquidity_score = max(0, current_ratio * 3)

        # 4. Margin Stability (20% weight)
        operating_margins = [
            self._safe_divide(h.get("operatingIncome", 0), h.get("revenue", 1))
            for h in historical
        ]
        avg_margin = sum(operating_margins) / len(operating_margins) if operating_margins else 0
        margin_std = self._std_dev(operating_margins)

        # High stable margins = resilience
        if avg_margin > 0.20 and margin_std < 0.03:
            stability_score = 10.0
        elif avg_margin > 0.10:
            stability_score = 5.0 + ((avg_margin - 0.10) * 30) - (margin_std * 50)
        else:
            stability_score = max(0, avg_margin * 50)

        # Weighted average
        resilience = (
            0.30 * de_score +
            0.30 * coverage_score +
            0.20 * liquidity_score +
            0.20 * stability_score
        )

        return {
            "score": round(resilience, 1),
            "components": {
                "de_score": round(de_score, 1),
                "coverage_score": round(coverage_score, 1),
                "liquidity_score": round(liquidity_score, 1),
                "stability_score": round(stability_score, 1),
            },
            "inputs": {
                "debt_to_equity": round(debt_to_equity, 2),
                "interest_coverage": round(interest_coverage, 2),
                "current_ratio": round(current_ratio, 2),
                "avg_margin": round(avg_margin, 3),
                "margin_std": round(margin_std, 3),
            },
            "method_version": "resilience_v1",
            "symbol": symbol,
            "pack_id": str(pack_id),
            "computed_at": datetime.utcnow().isoformat(),
        }

    async def compute_aggregate_rating(
        self,
        symbol: str,
        pack_id: UUID
    ) -> Dict[str, Any]:
        """
        Compute aggregate Buffett Quality Score (0-10).

        Equal weighting of three dimensions:
            - Dividend Safety (33%)
            - Moat Strength (33%)
            - Resilience (33%)

        Returns:
            Dict with aggregate score and all component ratings
        """
        # Compute all three dimensions
        div_safety = await self.compute_dividend_safety(symbol, pack_id)
        moat = await self.compute_moat_strength(symbol, pack_id)
        resilience = await self.compute_resilience(symbol, pack_id)

        # Equal weighting
        aggregate_score = (
            div_safety["score"] * 0.33 +
            moat["score"] * 0.33 +
            resilience["score"] * 0.34
        )

        return {
            "score": round(aggregate_score, 1),
            "dividend_safety": div_safety,
            "moat_strength": moat,
            "resilience": resilience,
            "symbol": symbol,
            "pack_id": str(pack_id),
            "method_version": "buffett_aggregate_v1",
            "computed_at": datetime.utcnow().isoformat(),
        }

    # Helper methods

    def _safe_divide(self, numerator: float, denominator: float) -> float:
        """Safe division with zero handling."""
        return numerator / denominator if denominator != 0 else 0.0

    def _std_dev(self, values: list) -> float:
        """Calculate standard deviation."""
        if not values or len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    async def _fetch_fundamentals(self, symbol: str, pack_id: UUID) -> Dict[str, Any]:
        """Fetch fundamental data from FMP provider."""
        # Implementation delegates to FMP provider
        from backend.app.providers.fmp import get_fmp_client
        client = get_fmp_client()
        return await client.get_fundamentals(symbol)

    async def _fetch_historical_ratios(self, symbol: str, years: int = 5) -> list:
        """Fetch historical financial ratios."""
        from backend.app.providers.fmp import get_fmp_client
        client = get_fmp_client()
        return await client.get_historical_ratios(symbol, years=years)

    async def _compute_growth_streak(self, symbol: str) -> int:
        """Compute consecutive years of dividend growth."""
        from backend.app.providers.fmp import get_fmp_client
        client = get_fmp_client()
        dividends = await client.get_dividend_history(symbol, years=20)

        streak = 0
        for i in range(1, len(dividends)):
            if dividends[i]["amount"] > dividends[i-1]["amount"]:
                streak += 1
            else:
                break

        return streak


# Singleton pattern
_ratings_service = None

def get_ratings_service():
    """Get or create ratings service singleton."""
    global _ratings_service
    if _ratings_service is None:
        from backend.app.db.connection import get_db_pool
        _ratings_service = RatingsService(
            db_pool=get_db_pool(),
            providers={}  # Providers injected as needed
        )
    return _ratings_service
```

### 1.2 Database Schema for Ratings

```sql
-- backend/db/schema/ratings.sql

CREATE TABLE IF NOT EXISTS ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(10) NOT NULL,
    pricing_pack_id UUID NOT NULL REFERENCES pricing_packs(id),
    rating_type VARCHAR(50) NOT NULL,  -- 'dividend_safety', 'moat_strength', 'resilience', 'aggregate'
    score NUMERIC(3,1) NOT NULL CHECK (score >= 0 AND score <= 10),
    method_version VARCHAR(50) NOT NULL,
    components_json JSON NOT NULL,  -- Sub-scores breakdown
    inputs_json JSON NOT NULL,  -- Raw input values
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(symbol, pricing_pack_id, rating_type, method_version)
);

CREATE INDEX idx_ratings_symbol_pack ON ratings(symbol, pricing_pack_id);
CREATE INDEX idx_ratings_type ON ratings(rating_type);
CREATE INDEX idx_ratings_score ON ratings(score);

-- Partition by rating_type for query performance
-- (Optional - implement if table grows large)
```

### 1.3 Nightly Pre-Warm Job

```python
# backend/jobs/prewarm_ratings.py

"""
Ratings Pre-Warm Job

Purpose: Pre-compute ratings for S&P 500 stocks nightly
Schedule: 00:08 local time (after pricing pack build at 00:00)
Duration: ~30 minutes for 500 symbols
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from backend.app.services.ratings import get_ratings_service
from backend.app.db.connection import execute_query

logger = logging.getLogger(__name__)


async def prewarm_ratings():
    """Pre-warm Buffett ratings for S&P 500."""

    start_time = datetime.utcnow()
    logger.info("Starting ratings pre-warm job")

    # Get latest pricing pack
    pack_id = await _get_latest_pack_id()
    if not pack_id:
        logger.error("No pricing pack found, skipping pre-warm")
        return

    # Get S&P 500 symbols
    symbols = await _get_sp500_symbols()
    logger.info(f"Pre-warming ratings for {len(symbols)} symbols with pack {pack_id}")

    # Get ratings service
    ratings_service = get_ratings_service()

    # Compute ratings (batch with concurrency limit)
    success_count = 0
    error_count = 0

    for i in range(0, len(symbols), 10):  # Process in batches of 10
        batch = symbols[i:i+10]
        tasks = [
            _compute_and_store_rating(ratings_service, symbol, pack_id)
            for symbol in batch
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                error_count += 1
                logger.error(f"Rating computation failed: {result}")
            else:
                success_count += 1

        # Log progress every 100 symbols
        if (i + 10) % 100 == 0:
            logger.info(f"Progress: {i+10}/{len(symbols)} symbols processed")

    duration = (datetime.utcnow() - start_time).total_seconds()

    logger.info(
        f"Ratings pre-warm complete: "
        f"{success_count} success, {error_count} errors, "
        f"duration={duration:.1f}s"
    )


async def _compute_and_store_rating(
    ratings_service,
    symbol: str,
    pack_id: UUID
) -> None:
    """Compute all ratings for a symbol and store in database."""

    try:
        # Compute aggregate (includes all three dimensions)
        result = await ratings_service.compute_aggregate_rating(symbol, pack_id)

        # Store dividend safety
        await _store_rating(
            symbol=symbol,
            pack_id=pack_id,
            rating_type="dividend_safety",
            score=result["dividend_safety"]["score"],
            method_version=result["dividend_safety"]["method_version"],
            components=result["dividend_safety"]["components"],
            inputs=result["dividend_safety"]["inputs"]
        )

        # Store moat strength
        await _store_rating(
            symbol=symbol,
            pack_id=pack_id,
            rating_type="moat_strength",
            score=result["moat_strength"]["score"],
            method_version=result["moat_strength"]["method_version"],
            components=result["moat_strength"]["components"],
            inputs=result["moat_strength"]["inputs"]
        )

        # Store resilience
        await _store_rating(
            symbol=symbol,
            pack_id=pack_id,
            rating_type="resilience",
            score=result["resilience"]["score"],
            method_version=result["resilience"]["method_version"],
            components=result["resilience"]["components"],
            inputs=result["resilience"]["inputs"]
        )

        # Store aggregate
        await _store_rating(
            symbol=symbol,
            pack_id=pack_id,
            rating_type="aggregate",
            score=result["score"],
            method_version=result["method_version"],
            components={
                "dividend_safety": result["dividend_safety"]["score"],
                "moat_strength": result["moat_strength"]["score"],
                "resilience": result["resilience"]["score"],
            },
            inputs={}
        )

    except Exception as e:
        logger.error(f"Failed to compute rating for {symbol}: {e}", exc_info=True)
        raise


async def _store_rating(
    symbol: str,
    pack_id: UUID,
    rating_type: str,
    score: float,
    method_version: str,
    components: dict,
    inputs: dict
) -> None:
    """Store rating in database (UPSERT)."""

    query = """
        INSERT INTO ratings (
            symbol, pricing_pack_id, rating_type, score,
            method_version, components_json, inputs_json
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (symbol, pricing_pack_id, rating_type, method_version)
        DO UPDATE SET
            score = EXCLUDED.score,
            components_json = EXCLUDED.components_json,
            inputs_json = EXCLUDED.inputs_json,
            computed_at = NOW()
    """

    await execute_statement(
        query,
        symbol, pack_id, rating_type, score,
        method_version, components, inputs
    )


async def _get_latest_pack_id() -> UUID:
    """Get most recent pricing pack ID."""
    query = """
        SELECT id FROM pricing_packs
        ORDER BY created_at DESC
        LIMIT 1
    """
    result = await execute_query(query)
    return result[0]["id"] if result else None


async def _get_sp500_symbols() -> list:
    """Get S&P 500 stock symbols."""
    # TODO: Replace with actual S&P 500 list from securities table or external source
    # For now, return common large-cap symbols
    return [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
        "V", "JNJ", "WMT", "JPM", "MA", "PG", "UNH", "HD", "DIS", "BAC",
        "ADBE", "NFLX", "CRM", "PFE", "CSCO", "KO", "NKE", "INTC", "ABBV",
        # ... (include all 500)
    ]


# Schedule with APScheduler
if __name__ == "__main__":
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()

    # Run daily at 00:08 (after pricing pack build)
    scheduler.add_job(
        prewarm_ratings,
        trigger="cron",
        hour=0,
        minute=8,
        id="prewarm_ratings",
        name="Pre-warm Buffett Ratings"
    )

    scheduler.start()
    asyncio.get_event_loop().run_forever()
```

---

## 2. Optimizer Service (`backend/app/services/optimizer.py`)

### Overview

Mean-variance portfolio optimization using **Riskfolio-Lib** with policy constraints:
- Sector limits (e.g., Tech ≤ 30%)
- Single-name caps (e.g., any stock ≤ 10%)
- Quality floors (e.g., Moat ≥ 6)
- Tracking error limits (e.g., TE ≤ 2%)

### 2.1 Implementation

```python
# backend/app/services/optimizer.py

"""
Portfolio Optimizer Service

Uses Riskfolio-Lib for mean-variance optimization with constraints.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass

try:
    import riskfolio as rp
except ImportError:
    # Graceful degradation if Riskfolio not installed
    rp = None
    logging.warning("Riskfolio-Lib not installed - optimizer will return stubs")

from backend.app.db.connection import execute_query

logger = logging.getLogger(__name__)


@dataclass
class OptimizerResult:
    """Result of portfolio optimization."""
    weights: Dict[str, float]  # Symbol → target weight
    expected_return: float
    expected_vol: float
    sharpe: float
    tracking_error: float
    trades: List[Dict[str, Any]]  # Trade instructions


class OptimizerService:
    """Portfolio optimization service."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def optimize_portfolio(
        self,
        portfolio_id: UUID,
        constraints: Dict[str, Any],
        pack_id: Optional[UUID] = None
    ) -> OptimizerResult:
        """
        Optimize portfolio using mean-variance optimization.

        Args:
            portfolio_id: Portfolio to optimize
            constraints: Dict with:
                - sector_limits: {sector: max_weight}
                - single_name_cap: float (e.g., 0.10 = 10%)
                - quality_floors: {metric: min_value}
                - te_limit: float (e.g., 0.02 = 2%)
            pack_id: Pricing pack for valuation

        Returns:
            OptimizerResult with optimal weights and trade instructions
        """
        if rp is None:
            return self._stub_result(portfolio_id)

        # Get current holdings
        current_holdings = await self._get_holdings(portfolio_id)

        # Get eligible universe (apply quality filters)
        eligible_symbols = await self._get_eligible_symbols(
            constraints.get("quality_floors", {})
        )

        # Filter holdings to eligible only
        filtered_holdings = [
            h for h in current_holdings
            if h["symbol"] in eligible_symbols
        ]

        # Get historical returns (252 trading days = 1 year)
        returns_df = await self._get_historical_returns(
            [h["symbol"] for h in filtered_holdings],
            days=252
        )

        # Build portfolio object
        port = rp.Portfolio(returns=returns_df)

        # Calculate expected returns and covariance
        port.assets_stats(
            method_mu="hist",  # Historical mean
            method_cov="hist",  # Historical covariance
            d=0.94  # Decay factor for exponential weighting
        )

        # Apply constraints

        # 1. Single-name caps
        single_name_cap = constraints.get("single_name_cap", 0.10)
        port.upperlng = single_name_cap

        # 2. Sector limits (using linear inequality constraints)
        sector_limits = constraints.get("sector_limits", {})
        for sector, limit in sector_limits.items():
            sector_symbols = await self._get_sector_symbols(sector)
            # Filter to symbols in our universe
            sector_symbols = [s for s in sector_symbols if s in eligible_symbols]

            if sector_symbols:
                # Create constraint: sum of sector weights <= limit
                constraint_row = np.zeros(len(returns_df.columns))
                for i, symbol in enumerate(returns_df.columns):
                    if symbol in sector_symbols:
                        constraint_row[i] = 1.0

                # Add to inequality constraints (Aw <= b)
                if not hasattr(port, "ainequality") or port.ainequality is None:
                    port.ainequality = constraint_row.reshape(1, -1)
                    port.binequality = np.array([limit])
                else:
                    port.ainequality = np.vstack([port.ainequality, constraint_row])
                    port.binequality = np.append(port.binequality, limit)

        # 3. Tracking error limit (implemented as constraint on variance)
        te_limit = constraints.get("te_limit")
        if te_limit:
            # Current portfolio as benchmark
            current_weights = self._get_current_weights(
                current_holdings,
                returns_df.columns
            )
            port.benchweights = current_weights
            port.upperte = te_limit

        # Optimize for maximum Sharpe ratio
        optimal_weights = port.optimization(
            model="Classic",  # Classic mean-variance
            rm="MV",  # Mean-variance risk measure
            obj="Sharpe",  # Maximize Sharpe ratio
            rf=0.04,  # Risk-free rate (4%)
            l=0  # No regularization
        )

        # Extract results
        weights_dict = {
            symbol: float(optimal_weights.loc[symbol, "weights"])
            for symbol in optimal_weights.index
        }

        # Calculate expected return and volatility
        expected_return = float(port.mu.T @ optimal_weights)
        expected_vol = float(np.sqrt(optimal_weights.T @ port.cov @ optimal_weights))
        sharpe = (expected_return - 0.04) / expected_vol if expected_vol > 0 else 0

        # Calculate tracking error vs current portfolio
        current_weights_aligned = self._get_current_weights(
            current_holdings,
            returns_df.columns
        )
        weight_diff = optimal_weights.values.flatten() - current_weights_aligned
        tracking_error = float(np.sqrt(weight_diff.T @ port.cov @ weight_diff))

        # Generate trade instructions
        trades = self._generate_trades(
            current_holdings,
            weights_dict,
            portfolio_id,
            pack_id
        )

        return OptimizerResult(
            weights=weights_dict,
            expected_return=expected_return,
            expected_vol=expected_vol,
            sharpe=sharpe,
            tracking_error=tracking_error,
            trades=trades
        )

    def _generate_trades(
        self,
        current_holdings: List[Dict],
        target_weights: Dict[str, float],
        portfolio_id: UUID,
        pack_id: UUID
    ) -> List[Dict[str, Any]]:
        """Generate trade instructions to move from current to target."""

        # Calculate current total value
        total_value = sum(h["market_value"] for h in current_holdings)

        trades = []

        # Get current weights
        current_weight_map = {
            h["symbol"]: h["market_value"] / total_value
            for h in current_holdings
        }

        # For each target position
        for symbol, target_weight in target_weights.items():
            current_weight = current_weight_map.get(symbol, 0.0)
            weight_diff = target_weight - current_weight

            # Skip if change is < 0.5% (avoid tiny trades)
            if abs(weight_diff) < 0.005:
                continue

            # Calculate trade value
            trade_value = weight_diff * total_value

            # Get current price (simplified - should use pack_id)
            price = next(
                (h["price"] for h in current_holdings if h["symbol"] == symbol),
                100.0  # Fallback price if not in current holdings
            )

            # Calculate shares to trade
            shares = int(trade_value / price)

            if shares == 0:
                continue

            trades.append({
                "symbol": symbol,
                "action": "BUY" if shares > 0 else "SELL",
                "shares": abs(shares),
                "estimated_price": price,
                "estimated_value": abs(trade_value),
                "current_weight": current_weight,
                "target_weight": target_weight,
                "weight_change": weight_diff,
            })

        # Sort by absolute weight change (largest first)
        trades.sort(key=lambda t: abs(t["weight_change"]), reverse=True)

        return trades

    async def _get_holdings(self, portfolio_id: UUID) -> List[Dict]:
        """Get current portfolio holdings."""
        query = """
            SELECT
                l.symbol,
                l.qty_open as shares,
                l.cost_base as cost_basis,
                s.current_price as price,
                l.qty_open * s.current_price as market_value
            FROM lots l
            LEFT JOIN (
                SELECT DISTINCT ON (security_id)
                    security_id,
                    price as current_price
                FROM prices
                ORDER BY security_id, date DESC
            ) s ON l.security_id = s.security_id
            WHERE l.portfolio_id = $1
              AND l.qty_open > 0
        """

        results = await execute_query(query, portfolio_id)
        return [dict(r) for r in results]

    async def _get_eligible_symbols(
        self,
        quality_floors: Dict[str, float]
    ) -> List[str]:
        """Get symbols that meet quality thresholds."""

        if not quality_floors:
            # No filters, return all symbols (or S&P 500)
            return await self._get_sp500_symbols()

        # Build WHERE clause for quality filters
        where_clauses = []
        params = []
        param_idx = 1

        for metric, min_value in quality_floors.items():
            where_clauses.append(
                f"(rating_type = ${param_idx} AND score >= ${param_idx+1})"
            )
            params.extend([metric, min_value])
            param_idx += 2

        where_sql = " OR ".join(where_clauses)

        query = f"""
            SELECT DISTINCT symbol
            FROM ratings
            WHERE {where_sql}
        """

        results = await execute_query(query, *params)
        return [r["symbol"] for r in results]

    async def _get_historical_returns(
        self,
        symbols: List[str],
        days: int = 252
    ) -> pd.DataFrame:
        """Get historical returns for symbols."""

        # Query daily prices
        query = """
            WITH daily_prices AS (
                SELECT
                    symbol,
                    date,
                    close_price,
                    LAG(close_price) OVER (PARTITION BY symbol ORDER BY date) as prev_price
                FROM prices
                WHERE symbol = ANY($1)
                  AND date >= CURRENT_DATE - INTERVAL '${days} days'
                ORDER BY symbol, date
            )
            SELECT
                symbol,
                date,
                (close_price - prev_price) / prev_price as return
            FROM daily_prices
            WHERE prev_price IS NOT NULL
            ORDER BY date, symbol
        """

        results = await execute_query(query, symbols, days=days)

        # Convert to DataFrame (symbols as columns, dates as rows)
        df = pd.DataFrame(results)

        if df.empty:
            # Return stub data if no price history
            logger.warning("No price history found, returning random returns")
            dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq="D")
            df = pd.DataFrame(
                np.random.randn(days, len(symbols)) * 0.01,
                index=dates,
                columns=symbols
            )
        else:
            df = df.pivot(index="date", columns="symbol", values="return")

        return df

    async def _get_sector_symbols(self, sector: str) -> List[str]:
        """Get symbols in a given sector."""
        query = """
            SELECT symbol
            FROM securities
            WHERE sector = $1
        """
        results = await execute_query(query, sector)
        return [r["symbol"] for r in results]

    def _get_current_weights(
        self,
        holdings: List[Dict],
        universe: List[str]
    ) -> np.ndarray:
        """Get current portfolio weights aligned to optimization universe."""

        total_value = sum(h["market_value"] for h in holdings)

        weights = np.zeros(len(universe))

        for i, symbol in enumerate(universe):
            holding = next((h for h in holdings if h["symbol"] == symbol), None)
            if holding:
                weights[i] = holding["market_value"] / total_value

        return weights

    def _stub_result(self, portfolio_id: UUID) -> OptimizerResult:
        """Return stub result if Riskfolio not available."""
        logger.warning("Returning stub optimizer result (Riskfolio not installed)")

        return OptimizerResult(
            weights={"AAPL": 0.30, "MSFT": 0.30, "GOOGL": 0.20, "AMZN": 0.20},
            expected_return=0.12,
            expected_vol=0.18,
            sharpe=0.67,
            tracking_error=0.05,
            trades=[
                {
                    "symbol": "AAPL",
                    "action": "BUY",
                    "shares": 100,
                    "estimated_price": 150.0,
                    "estimated_value": 15000.0,
                    "current_weight": 0.25,
                    "target_weight": 0.30,
                    "weight_change": 0.05,
                }
            ]
        )

    async def _get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbols."""
        # TODO: Query from securities table or external source
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]  # Stub


# Singleton
_optimizer_service = None

def get_optimizer_service():
    """Get or create optimizer service singleton."""
    global _optimizer_service
    if _optimizer_service is None:
        from backend.app.db.connection import get_db_pool
        _optimizer_service = OptimizerService(db_pool=get_db_pool())
    return _optimizer_service
```

### 2.2 Requirements

```txt
# Add to backend/requirements.txt

riskfolio-lib>=6.0.0
cvxpy>=1.4.0  # Required by Riskfolio
```

---

## 3. Agent Wiring

### 3.1 Ratings Agent

```python
# backend/app/agents/ratings_agent.py

"""
Ratings Agent - Buffett Quality Framework

Capabilities:
    - ratings.dividend_safety
    - ratings.moat_strength
    - ratings.resilience
    - ratings.aggregate
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from backend.app.agents.base_agent import BaseAgent
from backend.app.core.types import RequestCtx
from backend.app.services.ratings import get_ratings_service

logger = logging.getLogger(__name__)


class RatingsAgent(BaseAgent):
    """Agent for Buffett quality ratings."""

    def get_capabilities(self) -> List[str]:
        """Return list of ratings capabilities."""
        return [
            "ratings.dividend_safety",
            "ratings.moat_strength",
            "ratings.resilience",
            "ratings.aggregate",
        ]

    async def ratings_dividend_safety(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: str,
        pack_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compute dividend safety rating."""
        pack_uuid = UUID(pack_id) if pack_id else ctx.pricing_pack_id

        logger.info(f"ratings.dividend_safety: symbol={symbol}, pack={pack_uuid}")

        ratings_service = get_ratings_service()
        result = await ratings_service.compute_dividend_safety(symbol, pack_uuid)

        metadata = self._create_metadata(
            source=f"ratings_service:{pack_uuid}",
            asof=ctx.asof_date,
            ttl=86400  # Cache for 24 hours
        )

        return self._attach_metadata(result, metadata)

    async def ratings_moat_strength(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: str,
        pack_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compute economic moat rating."""
        pack_uuid = UUID(pack_id) if pack_id else ctx.pricing_pack_id

        logger.info(f"ratings.moat_strength: symbol={symbol}, pack={pack_uuid}")

        ratings_service = get_ratings_service()
        result = await ratings_service.compute_moat_strength(symbol, pack_uuid)

        metadata = self._create_metadata(
            source=f"ratings_service:{pack_uuid}",
            asof=ctx.asof_date,
            ttl=86400
        )

        return self._attach_metadata(result, metadata)

    async def ratings_resilience(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: str,
        pack_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compute financial resilience rating."""
        pack_uuid = UUID(pack_id) if pack_id else ctx.pricing_pack_id

        logger.info(f"ratings.resilience: symbol={symbol}, pack={pack_uuid}")

        ratings_service = get_ratings_service()
        result = await ratings_service.compute_resilience(symbol, pack_uuid)

        metadata = self._create_metadata(
            source=f"ratings_service:{pack_uuid}",
            asof=ctx.asof_date,
            ttl=86400
        )

        return self._attach_metadata(result, metadata)

    async def ratings_aggregate(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        symbol: str,
        pack_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compute aggregate Buffett quality score."""
        pack_uuid = UUID(pack_id) if pack_id else ctx.pricing_pack_id

        logger.info(f"ratings.aggregate: symbol={symbol}, pack={pack_uuid}")

        ratings_service = get_ratings_service()
        result = await ratings_service.compute_aggregate_rating(symbol, pack_uuid)

        metadata = self._create_metadata(
            source=f"ratings_service:{pack_uuid}",
            asof=ctx.asof_date,
            ttl=86400
        )

        return self._attach_metadata(result, metadata)
```

### 3.2 Optimizer Agent

```python
# backend/app/agents/optimizer_agent.py

"""
Optimizer Agent - Portfolio Optimization

Capabilities:
    - optimizer.propose_trades
    - optimizer.analyze_impact
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from backend.app.agents.base_agent import BaseAgent
from backend.app.core.types import RequestCtx
from backend.app.services.optimizer import get_optimizer_service

logger = logging.getLogger(__name__)


class OptimizerAgent(BaseAgent):
    """Agent for portfolio optimization."""

    def get_capabilities(self) -> List[str]:
        """Return list of optimizer capabilities."""
        return [
            "optimizer.propose_trades",
            "optimizer.analyze_impact",
        ]

    async def optimizer_propose_trades(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        constraints: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Propose optimal trades for portfolio rebalancing.

        Args:
            portfolio_id: Portfolio to optimize
            constraints: Optimization constraints
                - sector_limits: {sector: max_weight}
                - single_name_cap: float
                - quality_floors: {metric: min_value}
                - te_limit: float
        """
        portfolio_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

        if not constraints:
            # Default constraints
            constraints = {
                "single_name_cap": 0.10,  # 10% max per stock
                "quality_floors": {
                    "moat_strength": 6.0  # Only stocks with moat >= 6
                },
                "te_limit": 0.05  # 5% tracking error limit
            }

        logger.info(
            f"optimizer.propose_trades: portfolio={portfolio_uuid}, "
            f"constraints={constraints}"
        )

        optimizer_service = get_optimizer_service()
        result = await optimizer_service.optimize_portfolio(
            portfolio_uuid,
            constraints,
            ctx.pricing_pack_id
        )

        # Convert to dict
        result_dict = {
            "target_weights": result.weights,
            "expected_return": result.expected_return,
            "expected_volatility": result.expected_vol,
            "sharpe_ratio": result.sharpe,
            "tracking_error": result.tracking_error,
            "trades": result.trades,
            "portfolio_id": str(portfolio_uuid),
            "pricing_pack_id": str(ctx.pricing_pack_id),
        }

        metadata = self._create_metadata(
            source=f"optimizer_service:{ctx.pricing_pack_id}",
            asof=ctx.asof_date,
            ttl=3600  # Cache for 1 hour
        )

        return self._attach_metadata(result_dict, metadata)

    async def optimizer_analyze_impact(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        proposed_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze impact of proposed portfolio changes.

        Args:
            portfolio_id: Portfolio ID
            proposed_weights: Proposed target weights {symbol: weight}

        Returns:
            Dict with impact analysis (return, risk, TE changes)
        """
        portfolio_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

        logger.info(f"optimizer.analyze_impact: portfolio={portfolio_uuid}")

        # TODO: Implement impact analysis
        # For now, return stub

        result = {
            "portfolio_id": str(portfolio_uuid),
            "return_change": 0.02,  # +2% expected return
            "risk_change": -0.01,  # -1% volatility
            "sharpe_change": 0.15,  # +0.15 Sharpe
            "tracking_error": 0.03,  # 3% TE vs current
            "status": "stub_implementation",
        }

        metadata = self._create_metadata(
            source="optimizer_service:stub",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)
```

### 3.3 Register Agents

```python
# backend/app/api/executor.py

# Add imports
from backend.app.agents.ratings_agent import RatingsAgent
from backend.app.agents.optimizer_agent import OptimizerAgent

# In get_agent_runtime():

# Register ratings agent
ratings_agent = RatingsAgent("ratings_agent", services)
_agent_runtime.register_agent(ratings_agent)

# Register optimizer agent
optimizer_agent = OptimizerAgent("optimizer_agent", services)
_agent_runtime.register_agent(optimizer_agent)

logger.info("Agent runtime initialized with 6 agents")
```

---

## 4. Testing

### 4.1 Ratings Service Tests

```python
# backend/tests/services/test_ratings.py

import pytest
from backend.app.services.ratings import get_ratings_service


@pytest.mark.asyncio
async def test_dividend_safety_high_quality():
    """Test dividend safety for high-quality dividend stock."""
    service = get_ratings_service()

    # Mock AAPL data (strong dividend profile)
    result = await service.compute_dividend_safety("AAPL", pack_id=test_pack_id)

    assert result["score"] >= 7.0  # Should score high
    assert result["method_version"] == "div_safety_v1"
    assert "payout_score" in result["components"]


@pytest.mark.asyncio
async def test_moat_strength_wide_moat():
    """Test moat strength for wide-moat company."""
    service = get_ratings_service()

    result = await service.compute_moat_strength("MSFT", pack_id=test_pack_id)

    assert result["score"] >= 8.0  # Microsoft has wide moat
    assert result["method_version"] == "moat_strength_v1"


@pytest.mark.asyncio
async def test_aggregate_rating():
    """Test aggregate Buffett quality score."""
    service = get_ratings_service()

    result = await service.compute_aggregate_rating("JNJ", pack_id=test_pack_id)

    assert 0 <= result["score"] <= 10
    assert "dividend_safety" in result
    assert "moat_strength" in result
    assert "resilience" in result
```

### 4.2 Optimizer Service Tests

```python
# backend/tests/services/test_optimizer.py

import pytest
from backend.app.services.optimizer import get_optimizer_service


@pytest.mark.asyncio
async def test_optimize_with_constraints():
    """Test portfolio optimization with constraints."""
    service = get_optimizer_service()

    constraints = {
        "single_name_cap": 0.10,
        "sector_limits": {"Technology": 0.30},
        "quality_floors": {"moat_strength": 6.0},
    }

    result = await service.optimize_portfolio(
        test_portfolio_id,
        constraints
    )

    assert result.sharpe > 0
    assert result.tracking_error >= 0
    assert len(result.weights) > 0
    assert all(0 <= w <= 0.10 for w in result.weights.values())


@pytest.mark.asyncio
async def test_trade_generation():
    """Test trade instruction generation."""
    service = get_optimizer_service()

    result = await service.optimize_portfolio(test_portfolio_id, {})

    assert isinstance(result.trades, list)
    for trade in result.trades:
        assert "symbol" in trade
        assert "action" in trade
        assert trade["action"] in ["BUY", "SELL"]
        assert "shares" in trade
        assert trade["shares"] > 0
```

---

## 5. Implementation Checklist

### Ratings Service
- [ ] Implement `RatingsService` class with 4 methods
- [ ] Add helper methods (_fetch_fundamentals, _compute_growth_streak, etc.)
- [ ] Create `ratings` database table
- [ ] Create ratings indexes
- [ ] Implement prewarm_ratings job
- [ ] Add ratings job to scheduler
- [ ] Create `RatingsAgent` class
- [ ] Register RatingsAgent in executor
- [ ] Write unit tests
- [ ] Test buffett_checklist pattern end-to-end

### Optimizer Service
- [ ] Implement `OptimizerService` class
- [ ] Add riskfolio-lib to requirements.txt
- [ ] Install and test Riskfolio
- [ ] Implement constraint handling
- [ ] Implement trade generation
- [ ] Create `OptimizerAgent` class
- [ ] Register OptimizerAgent in executor
- [ ] Write unit tests
- [ ] Test policy_rebalance pattern end-to-end

---

## 6. Estimated Effort

| Task | Effort | Priority |
|------|--------|----------|
| Ratings Service Implementation | 12 hours | P1 |
| Ratings Database Schema | 2 hours | P1 |
| Ratings Prewarm Job | 4 hours | P1 |
| Ratings Agent + Tests | 4 hours | P1 |
| Optimizer Service Implementation | 12 hours | P1 |
| Riskfolio Integration | 4 hours | P1 |
| Optimizer Agent + Tests | 4 hours | P1 |
| End-to-end Testing | 4 hours | P1 |
| **TOTAL** | **46 hours (5-6 days)** | |

---

**Last Updated**: October 24, 2025
**Source**: IMPLEMENTATION_ROADMAP_V2.md (Sprint 4, Weeks 7-8)
**Status**: Ready for implementation
