# OPTIMIZER_ARCHITECT — Policy-Based Rebalancing Specialist

**Agent Type**: Business Logic
**Phase**: Future Enhancement
**Priority**: P2 (Future - Value-add feature when implemented)
**Status**: ⚠️ Service scaffold exists (`backend/app/services/optimizer.py`); no agent/UI wiring yet
**Created**: 2025-10-21
**Last Updated**: 2025-10-24

---

## Current Status

### ⚠️ Partial implementation
- `backend/app/services/optimizer.py` implements Riskfolio-based policy constraint logic and can be imported, but no `OptimizerAgent` exists yet.
- `policy_rebalance.json` is defined, however the UI and orchestrator do not expose it because optimizer outputs are experimental.
- Until an agent + UI integration land, use the service directly in notebooks/tests for research and keep policy decisions out of the user-facing app.

---

## Mission (When Implemented)

Implement **policy-based portfolio rebalancing** with quality ratings constraints, tracking error limits, turnover costs, and trade proposals using Riskfolio-Lib for mean-variance optimization.

---

## Scope & Responsibilities

### In Scope

1. **Policy Templates** (seeded from `data/SEEDS/optimizer/`)
   - Quality-based: Min quality score = 6.0, max single position = 10%
   - Tracking error (TE) constraint: ≤ 2% vs benchmark
   - Turnover limit: ≤ 20% per rebalance

2. **Optimization Engine**
   - Mean-variance optimization (Markowitz)
   - Riskfolio-Lib integration for covariance estimation
   - Constraints: min/max weights, sector limits, ratings thresholds

3. **Trade Proposals**
   - Δ shares to buy/sell
   - Estimated costs (commissions + market impact)
   - Expected TE change
   - Before/after portfolio metrics

4. **Rights-Aware Execution**
   - No optimization runs without valid pricing pack
   - Trade proposals include pricing_pack_id for reproducibility

### Out of Scope

- ❌ Live trade execution (proposal-only)
- ❌ Multi-period optimization (single-period only)
- ❌ Tax-loss harvesting (future enhancement)

---

## Acceptance Criteria

### AC-1: Quality-Based Policy (Golden Test)
**Given**: Portfolio with AAPL (quality 9.2), XOM (quality 4.5), JNJ (quality 9.0)
**When**: Apply policy "min_quality = 6.0"
**Then**:
- XOM weight → 0% (below threshold)
- AAPL, JNJ rebalanced to maintain target allocation
- Trade proposal: Sell 100 XOM, Buy 50 AAPL + 30 JNJ

**Golden Test**: `tests/golden/optimizer/quality_policy_rebalance.json`

---

### AC-2: Tracking Error Constraint
**Given**: Portfolio with TE = 3.5% vs benchmark (S&P 500)
**When**: Apply policy "max_te = 2.0%"
**Then**:
- Optimizer proposes trades to reduce TE to ≤ 2%
- Sector weights adjusted toward benchmark
- Expected TE after rebalance: 1.8%

**Golden Test**: `tests/golden/optimizer/te_constraint_rebalance.json`

---

### AC-3: Turnover Limit
**Given**: Rebalance proposal with 35% turnover
**When**: Apply policy "max_turnover = 20%"
**Then**:
- Optimizer scales down proposed trades
- Actual turnover: 19.5% (within limit)
- Trade-off: Higher residual TE (2.1% vs ideal 1.8%)

**Golden Test**: `tests/golden/optimizer/turnover_limit_rebalance.json`

---

### AC-4: Cost Estimation
**Given**: Trade proposal to sell 100 AAPL @ $232.50
**When**: Calculate estimated costs
**Then**:
- Commission: $5.00 (flat fee)
- Market impact: 0.15% × $23,250 = $34.88
- Total cost: $39.88
- Cost as % of trade: 0.17%

**Unit Test**: `tests/unit/optimizer/test_cost_estimation.py`

---

### AC-5: Seed Integration (Policy Templates)
**Given**: Policy templates in `data/SEEDS/optimizer/policy_templates.json`
**When**: Load policies via seeding script
**Then**:
- Policies stored in `optimizer_policies` table
- Constraints parsed and validated
- Version tracked (`method_version = "v1"`)

**Integration Test**: `tests/integration/test_optimizer_seed_integration.py`

---

## Implementation Specifications

### Optimizer Core

```python
# backend/app/analytics/optimizer.py

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List
import riskfolio as rp
import pandas as pd
import numpy as np

@dataclass(frozen=True)
class OptimizationPolicy:
    """Portfolio rebalancing policy."""
    policy_id: str
    min_quality_score: Decimal
    max_single_position_pct: Decimal
    max_sector_pct: Decimal
    max_tracking_error_pct: Decimal
    max_turnover_pct: Decimal
    method_version: str

@dataclass(frozen=True)
class TradeProposal:
    """Proposed trade for rebalancing."""
    security_id: str
    symbol: str
    current_shares: Decimal
    target_shares: Decimal
    delta_shares: Decimal  # target - current
    current_weight_pct: Decimal
    target_weight_pct: Decimal
    estimated_cost: Decimal

@dataclass(frozen=True)
class RebalanceResult:
    """Complete rebalance proposal."""
    portfolio_id: str
    policy_id: str
    trades: List[TradeProposal]
    total_turnover_pct: Decimal
    estimated_total_cost: Decimal
    te_before: Decimal
    te_after: Decimal
    ctx: RequestCtx

class PortfolioOptimizer:
    """Policy-based portfolio optimizer."""

    def __init__(self):
        self.policies = self._load_policies()

    async def propose_rebalance(
        self,
        ctx: RequestCtx,
        portfolio_id: str,
        policy_id: str,
    ) -> RebalanceResult:
        """Generate rebalance trade proposals."""
        policy = self.policies[policy_id]

        # Load current holdings
        holdings = await self._load_holdings(ctx, portfolio_id)

        # Load benchmark weights
        benchmark_weights = await self._load_benchmark(ctx, portfolio_id)

        # Filter holdings by quality rating
        eligible_holdings = [
            h for h in holdings
            if h.quality_score >= policy.min_quality_score
        ]

        # Build optimization problem
        returns, cov_matrix = await self._estimate_returns_covariance(ctx, eligible_holdings)

        # Run optimization
        target_weights = self._optimize(
            returns=returns,
            cov_matrix=cov_matrix,
            benchmark_weights=benchmark_weights,
            policy=policy,
        )

        # Generate trade proposals
        trades = self._generate_trades(holdings, target_weights, ctx)

        # Calculate metrics
        turnover = self._calculate_turnover(trades)
        total_cost = self._estimate_total_cost(trades)
        te_before = self._calculate_tracking_error(holdings, benchmark_weights, cov_matrix)
        te_after = self._calculate_tracking_error_proposed(target_weights, benchmark_weights, cov_matrix)

        return RebalanceResult(
            portfolio_id=portfolio_id,
            policy_id=policy_id,
            trades=trades,
            total_turnover_pct=turnover,
            estimated_total_cost=total_cost,
            te_before=te_before,
            te_after=te_after,
            ctx=ctx,
        )

    def _optimize(
        self,
        returns: pd.Series,
        cov_matrix: pd.DataFrame,
        benchmark_weights: pd.Series,
        policy: OptimizationPolicy,
    ) -> pd.Series:
        """Run mean-variance optimization with constraints."""
        # Create Riskfolio-Lib portfolio object
        port = rp.Portfolio(returns=returns.to_frame())

        # Set covariance matrix
        port.cov = cov_matrix

        # Set constraints
        port.upperlong = float(policy.max_single_position_pct)  # Max 10% per position
        port.budget = 1.0  # Fully invested

        # Add tracking error constraint
        port.benchweights = benchmark_weights
        port.allowTE = True
        port.TE = float(policy.max_tracking_error_pct)  # Max 2% TE

        # Optimize (mean-variance)
        w = port.optimization(
            model="Classic",  # Markowitz
            rm="MV",  # Mean-variance
            obj="Sharpe",  # Maximize Sharpe ratio
            rf=0.02,  # Risk-free rate (2%)
            l=0,  # No regularization
            hist=True,  # Use historical data
        )

        # Apply turnover constraint
        current_weights = port.benchweights  # Use benchmark as starting point
        proposed_turnover = np.abs(w - current_weights).sum()

        if proposed_turnover > float(policy.max_turnover_pct):
            # Scale down trades to meet turnover limit
            scale_factor = float(policy.max_turnover_pct) / proposed_turnover
            w = current_weights + scale_factor * (w - current_weights)

        return pd.Series(w.flatten(), index=returns.index)

    def _generate_trades(
        self,
        holdings: List[Holding],
        target_weights: pd.Series,
        ctx: RequestCtx,
    ) -> List[TradeProposal]:
        """Generate trade proposals from target weights."""
        total_value = sum(h.value for h in holdings)

        trades = []
        for holding in holdings:
            current_weight = holding.value / total_value
            target_weight = target_weights.get(holding.symbol, Decimal("0"))

            target_value = target_weight * total_value
            target_shares = target_value / holding.price

            delta_shares = target_shares - holding.shares

            if abs(delta_shares) > Decimal("0.01"):  # Min trade threshold
                estimated_cost = self._estimate_trade_cost(holding, delta_shares)

                trades.append(TradeProposal(
                    security_id=holding.security_id,
                    symbol=holding.symbol,
                    current_shares=holding.shares,
                    target_shares=target_shares,
                    delta_shares=delta_shares,
                    current_weight_pct=current_weight * 100,
                    target_weight_pct=target_weight * 100,
                    estimated_cost=estimated_cost,
                ))

        return trades

    def _estimate_trade_cost(self, holding: Holding, delta_shares: Decimal) -> Decimal:
        """Estimate trade cost (commission + market impact)."""
        trade_value = abs(delta_shares * holding.price)

        # Commission (flat $5 per trade)
        commission = Decimal("5.00")

        # Market impact (0.15% for liquid stocks)
        market_impact = trade_value * Decimal("0.0015")

        return commission + market_impact

    def _calculate_turnover(self, trades: List[TradeProposal]) -> Decimal:
        """Calculate total turnover as % of portfolio value."""
        total_trade_value = sum(abs(t.delta_shares * t.current_price) for t in trades)
        total_portfolio_value = sum(t.current_shares * t.current_price for t in trades)

        return (total_trade_value / total_portfolio_value) * 100

    def _calculate_tracking_error(
        self,
        holdings: List[Holding],
        benchmark_weights: pd.Series,
        cov_matrix: pd.DataFrame,
    ) -> Decimal:
        """Calculate tracking error (annualized)."""
        # Portfolio weights
        total_value = sum(h.value for h in holdings)
        port_weights = pd.Series({h.symbol: h.value / total_value for h in holdings})

        # Active weights (portfolio - benchmark)
        active_weights = port_weights - benchmark_weights

        # TE = sqrt(active_weights' * cov_matrix * active_weights) * sqrt(252)
        variance = active_weights.T @ cov_matrix @ active_weights
        te_daily = np.sqrt(variance)
        te_annual = te_daily * np.sqrt(252)

        return Decimal(str(te_annual))

    async def _estimate_returns_covariance(
        self,
        ctx: RequestCtx,
        holdings: List[Holding],
    ) -> tuple[pd.Series, pd.DataFrame]:
        """Estimate expected returns and covariance matrix."""
        # Fetch historical prices (1 year) from pricing packs
        prices = await self._fetch_historical_prices(ctx, holdings)

        # Calculate returns
        returns = prices.pct_change().dropna()

        # Expected returns (CAPM or historical mean)
        expected_returns = returns.mean() * 252  # Annualize

        # Covariance matrix
        cov_matrix = returns.cov() * 252  # Annualize

        return expected_returns, cov_matrix
```

---

## Seed Data Integration

**`data/SEEDS/optimizer/policy_templates.json`**
```json
{
  "schema_version": "1.0",
  "policies": [
    {
      "id": "quality_focused",
      "name": "Quality-Focused Balanced",
      "min_quality_score": 6.0,
      "max_single_position_pct": 0.10,
      "max_sector_pct": 0.25,
      "max_tracking_error_pct": 0.02,
      "max_turnover_pct": 0.20,
      "method_version": "v1"
    },
    {
      "id": "aggressive_growth",
      "name": "Aggressive Growth",
      "min_quality_score": 4.0,
      "max_single_position_pct": 0.15,
      "max_sector_pct": 0.40,
      "max_tracking_error_pct": 0.05,
      "max_turnover_pct": 0.30,
      "method_version": "v1"
    },
    {
      "id": "conservative_income",
      "name": "Conservative Income",
      "min_quality_score": 8.0,
      "max_single_position_pct": 0.08,
      "max_sector_pct": 0.20,
      "max_tracking_error_pct": 0.015,
      "max_turnover_pct": 0.15,
      "method_version": "v1"
    }
  ]
}
```

**`data/SEEDS/optimizer/constraint_defaults.json`**
```json
{
  "commission_per_trade": 5.00,
  "market_impact_bps": 15,
  "min_trade_value": 100.00,
  "risk_free_rate": 0.02,
  "annualization_factor": 252
}
```

---

## Golden Tests

**`tests/golden/optimizer/quality_policy_rebalance.json`**
```json
{
  "portfolio_id": "P1",
  "policy_id": "quality_focused",
  "holdings": [
    {"symbol": "AAPL", "shares": 100, "price": 232.50, "quality_score": 9.2},
    {"symbol": "XOM", "shares": 200, "price": 112.30, "quality_score": 4.5},
    {"symbol": "JNJ", "shares": 150, "price": 165.80, "quality_score": 9.0}
  ],
  "expected_trades": [
    {"symbol": "XOM", "delta_shares": -200, "reason": "Below min quality (4.5 < 6.0)"},
    {"symbol": "AAPL", "delta_shares": 50},
    {"symbol": "JNJ", "delta_shares": 30}
  ],
  "expected_turnover_pct": 18.5,
  "expected_te_after": 1.8
}
```

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/unit/optimizer/ -k "cost or turnover or tracking_error"
```

**Coverage**:
- Trade cost estimation
- Turnover calculation
- Tracking error calculation
- Constraint enforcement

---

### Golden Tests
```bash
pytest tests/golden/optimizer/ --golden-update=never
```

**Scenarios**:
- Quality-based filtering (XOM excluded)
- TE constraint (portfolio converges to benchmark)
- Turnover limit (trades scaled down)

---

### Integration Tests
```bash
pytest tests/integration/test_optimizer_integration.py
```

**Flows**:
1. Seed policies → load into database
2. Fetch holdings + ratings → run optimizer
3. Generate trade proposals → verify reproducibility

---

## Related Documents

- **[PRODUCT_SPEC.md](../../PRODUCT_SPEC.md)** — Section 4: Policy Rebalancing
- **[DawsOS_Seeding_Plan](../../DawsOS_Seeding_Plan)** — Section 3.6: Optimizer
- **[RATINGS_ARCHITECT.md](./RATINGS_ARCHITECT.md)** — Quality scores input
- **[types.py](../../../backend/app/core/types.py)** — RebalanceRequest/Response

---

**Last Updated**: 2025-10-21
**Agent Owner**: Business Logic Team
**Review Cycle**: After policy changes or risk model updates
