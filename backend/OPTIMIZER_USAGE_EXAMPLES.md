# Portfolio Optimizer - Usage Examples

**Date**: October 26, 2025
**Service**: backend/app/services/optimizer.py
**Status**: Production-ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Method 1: Propose Trades](#method-1-propose-trades)
3. [Method 2: Analyze Impact](#method-2-analyze-impact)
4. [Method 3: Suggest Hedges](#method-3-suggest-hedges)
5. [Method 4: Suggest Deleveraging Hedges](#method-4-suggest-deleveraging-hedges)
6. [Integration Examples](#integration-examples)
7. [Error Handling](#error-handling)

---

## Quick Start

### Installation

```bash
cd backend
pip install riskfolio-lib scikit-learn
```

### Import

```python
from app.services.optimizer import get_optimizer_service
from uuid import UUID

service = get_optimizer_service()
```

---

## Method 1: Propose Trades

### Basic Example

```python
import asyncio
from uuid import UUID

async def rebalance_portfolio():
    service = get_optimizer_service()

    # Define policy constraints
    policy_json = {
        "min_quality_score": 6.0,           # Exclude holdings below quality 6.0
        "max_single_position_pct": 15.0,    # Max 15% per position
        "max_turnover_pct": 20.0,           # Max 20% turnover
        "method": "mean_variance",          # Optimization method
        "lookback_days": 252,               # 1 year of price history
        "risk_free_rate": 0.02,             # 2% risk-free rate
        "commission_per_trade": 5.00,       # $5 commission
        "market_impact_bps": 15.0,          # 15 bps market impact
    }

    # Generate rebalance trades
    result = await service.propose_trades(
        portfolio_id=UUID("11111111-1111-1111-1111-111111111111"),
        policy_json=policy_json,
        pricing_pack_id="PP_2025-10-26",
        ratings={  # Optional: quality scores from ratings service
            "AAPL": 9.2,
            "RY": 8.5,
            "XIU": 7.0,
        }
    )

    # Print results
    print(f"Trade Count: {result['trade_count']}")
    print(f"Turnover: {result['turnover_pct']:.2f}%")
    print(f"Costs: {result['cost_bps']:.2f} bps")

    for trade in result['trades']:
        print(f"\n{trade['action']} {trade['quantity']} {trade['symbol']}")
        print(f"  Current: {trade['current_shares']} shares ({trade['current_weight_pct']:.1f}%)")
        print(f"  Target: {trade['target_shares']} shares ({trade['target_weight_pct']:.1f}%)")
        print(f"  Value: ${trade['trade_value']:.2f}")
        print(f"  Cost: ${trade['estimated_cost']:.2f}")
        print(f"  Rationale: {trade['rationale']}")

    return result

# Run
result = asyncio.run(rebalance_portfolio())
```

### Expected Output

```
Trade Count: 3
Turnover: 18.50%
Costs: 11.70 bps

BUY 50 AAPL
  Current: 100 shares (15.0%)
  Target: 150 shares (18.5%)
  Value: $11625.00
  Cost: $22.44
  Rationale: Increase weight from 15.0% to 18.5%

SELL 100 RY
  Current: 400 shares (25.0%)
  Target: 300 shares (18.5%)
  Value: $11000.00
  Cost: $21.50
  Rationale: Decrease weight from 25.0% to 18.5%

HOLD XIU
  Current: 1000 shares (10.0%)
  Target: 1000 shares (10.0%)
  Value: $0.00
  Cost: $0.00
  Rationale: No change (already at target weight)
```

### Advanced: Risk Parity Optimization

```python
policy_json = {
    "method": "risk_parity",  # Equal risk contribution
    "max_turnover_pct": 25.0,
    "lookback_days": 252,
}

result = await service.propose_trades(
    portfolio_id=portfolio_id,
    policy_json=policy_json,
    pricing_pack_id=pricing_pack_id,
)

# Risk parity will allocate more to low-volatility assets
# and less to high-volatility assets
```

### Advanced: Maximum Sharpe Ratio

```python
policy_json = {
    "method": "max_sharpe",  # Maximize risk-adjusted return
    "risk_free_rate": 0.025,  # 2.5% risk-free rate
    "max_single_position_pct": 20.0,
    "max_turnover_pct": 30.0,
}

result = await service.propose_trades(
    portfolio_id=portfolio_id,
    policy_json=policy_json,
    pricing_pack_id=pricing_pack_id,
)

# Max Sharpe will concentrate in high Sharpe ratio securities
```

### Advanced: CVaR Optimization (Tail Risk)

```python
policy_json = {
    "method": "cvar",  # Minimize tail risk
    "max_turnover_pct": 20.0,
    "lookback_days": 252,
}

result = await service.propose_trades(
    portfolio_id=portfolio_id,
    policy_json=policy_json,
    pricing_pack_id=pricing_pack_id,
)

# CVaR will minimize worst-case losses (downside protection)
```

---

## Method 2: Analyze Impact

### Basic Example

```python
async def analyze_rebalance_impact():
    service = get_optimizer_service()

    # First, get proposed trades
    policy_json = {"max_turnover_pct": 20.0}
    rebalance_result = await service.propose_trades(
        portfolio_id=UUID("11111111-1111-1111-1111-111111111111"),
        policy_json=policy_json,
        pricing_pack_id="PP_2025-10-26",
    )

    # Analyze impact of proposed trades
    impact = await service.analyze_impact(
        portfolio_id=UUID("11111111-1111-1111-1111-111111111111"),
        proposed_trades=rebalance_result['trades'],
        pricing_pack_id="PP_2025-10-26",
    )

    # Print impact analysis
    print(f"Current Value: ${impact['current_value']:.2f}")
    print(f"Post-Rebalance Value: ${impact['post_rebalance_value']:.2f}")
    print(f"Change: ${impact['value_delta']:.2f}")
    print(f"\nConcentration (Top 10):")
    print(f"  Current: {impact['current_concentration_top10']:.1f}%")
    print(f"  Post: {impact['post_concentration_top10']:.1f}%")
    print(f"  Change: {impact['delta_concentration']:.1f}%")

    return impact

impact = asyncio.run(analyze_rebalance_impact())
```

### Expected Output

```
Current Value: $243500.00
Post-Rebalance Value: $243215.00
Change: -$285.00

Concentration (Top 10):
  Current: 65.5%
  Post: 58.2%
  Change: -7.3%
```

### Advanced: With Risk Metrics (Future)

```python
# TODO: Once risk metrics are implemented
impact = await service.analyze_impact(
    portfolio_id=portfolio_id,
    proposed_trades=trades,
    pricing_pack_id=pricing_pack_id,
)

print(f"Expected Return: {impact['current_expected_return']:.2%} → {impact['post_expected_return']:.2%}")
print(f"Volatility: {impact['current_vol']:.2%} → {impact['post_vol']:.2%}")
print(f"Sharpe Ratio: {impact['current_sharpe']:.2f} → {impact['post_sharpe']:.2f}")
print(f"Max Drawdown: {impact['current_max_dd']:.2%} → {impact['post_max_dd']:.2%}")
```

---

## Method 3: Suggest Hedges

### Example: Equity Selloff Scenario

```python
async def hedge_equity_selloff():
    service = get_optimizer_service()

    hedges = await service.suggest_hedges(
        portfolio_id=UUID("11111111-1111-1111-1111-111111111111"),
        scenario_id="equity_selloff",
        pricing_pack_id="PP_2025-10-26",
    )

    print(f"Scenario: {hedges['scenario_id']}")
    print(f"Hedges: {len(hedges['hedges'])}\n")

    for hedge in hedges['hedges']:
        print(f"{hedge['action']} {hedge['instrument']} ({hedge['instrument_type']})")
        print(f"  Notional: ${hedge['notional']:.2f}")
        print(f"  Hedge Ratio: {hedge['hedge_ratio']:.0%}")
        print(f"  Expected Offset: {hedge['expected_offset_pct']:.0f}%")
        print(f"  Rationale: {hedge['rationale']}\n")

    return hedges

hedges = asyncio.run(hedge_equity_selloff())
```

### Expected Output

```
Scenario: equity_selloff
Hedges: 2

BUY VIX (option)
  Notional: $12175.00
  Hedge Ratio: 40%
  Expected Offset: 50%
  Rationale: VIX call options hedge equity market volatility

SELL SPY (option)
  Notional: $12175.00
  Hedge Ratio: 30%
  Expected Offset: 40%
  Rationale: SPY put options hedge broad equity exposure
```

### Example: Rate Increase Scenario

```python
hedges = await service.suggest_hedges(
    portfolio_id=portfolio_id,
    scenario_id="rates_up",
    pricing_pack_id=pricing_pack_id,
)

# Expected: Long TLT recommendation
# Rationale: Long-duration treasuries benefit from rate increases
```

### Example: USD Appreciation Scenario

```python
hedges = await service.suggest_hedges(
    portfolio_id=portfolio_id,
    scenario_id="usd_up",
    pricing_pack_id=pricing_pack_id,
)

# Expected: Short UUP (USD ETF)
# Rationale: Hedges currency appreciation risk for non-USD holdings
```

### Example: Credit Spread Widening

```python
hedges = await service.suggest_hedges(
    portfolio_id=portfolio_id,
    scenario_id="credit_spread_widening",
    pricing_pack_id=pricing_pack_id,
)

# Expected: LQD put options
# Rationale: Hedges investment-grade credit spread widening
```

---

## Method 4: Suggest Deleveraging Hedges

### Example: Deleveraging Regime

```python
async def deleverage_portfolio():
    service = get_optimizer_service()

    recommendations = await service.suggest_deleveraging_hedges(
        portfolio_id=UUID("11111111-1111-1111-1111-111111111111"),
        regime="DELEVERAGING",
        pricing_pack_id="PP_2025-10-26",
    )

    print(f"Regime: {recommendations['regime']}")
    print(f"Recommendations: {len(recommendations['recommendations'])}\n")

    for rec in recommendations['recommendations']:
        print(f"Action: {rec['action']}")
        if rec['instruments']:
            print(f"  Instruments: {', '.join(rec['instruments'])}")
        if 'target_reduction_pct' in rec:
            print(f"  Target Reduction: {rec['target_reduction_pct']:.0f}%")
        if 'target_allocation_pct' in rec:
            print(f"  Target Allocation: {rec['target_allocation_pct']:.0f}%")
        print(f"  Rationale: {rec['rationale']}\n")

    return recommendations

recs = asyncio.run(deleverage_portfolio())
```

### Expected Output

```
Regime: DELEVERAGING
Recommendations: 3

Action: reduce_equity_exposure
  Instruments: SPY, QQQ, VTI
  Target Reduction: 40%
  Rationale: Reduce equity beta aggressively in deleveraging regime to preserve capital

Action: increase_safe_havens
  Instruments: GLD, TLT, CASH
  Target Allocation: 30%
  Rationale: Increase gold, long-duration bonds, and cash as deflation hedges

Action: avoid_credit
  Instruments: HYG, JNK
  Target Reduction: 100%
  Rationale: Exit high-yield credit to avoid default risk in deleveraging
```

### Example: Late Expansion Regime

```python
recommendations = await service.suggest_deleveraging_hedges(
    portfolio_id=portfolio_id,
    regime="LATE_EXPANSION",
    pricing_pack_id=pricing_pack_id,
)

# Expected:
# - Reduce equity 20%
# - Rotate to defensive (utilities, staples, REITs) 15%
```

### Example: Reflation Regime

```python
recommendations = await service.suggest_deleveraging_hedges(
    portfolio_id=portfolio_id,
    regime="REFLATION",
    pricing_pack_id=pricing_pack_id,
)

# Expected:
# - Reduce duration (TLT, IEF) 50%
# - Increase inflation hedges (GLD, TIP, DBC) 20%
```

---

## Integration Examples

### Pattern Execution (Via Executor API)

```bash
curl -X POST "http://localhost:8000/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "policy_rebalance",
    "inputs": {
      "portfolio_id": "11111111-1111-1111-1111-111111111111",
      "policies": [],
      "constraints": {
        "max_te_pct": 2.0,
        "max_turnover_pct": 10.0,
        "min_lot_value": 500
      }
    }
  }'
```

### Agent Method (Financial Analyst)

```python
# backend/app/agents/financial_analyst.py

async def optimizer_propose_trades(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    policies: Optional[List] = None,
    constraints: Optional[Dict] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate rebalance trade proposals.

    Capability: optimizer.propose_trades
    """
    from app.services.optimizer import get_optimizer_service

    portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

    # Build policy JSON from constraints
    policy_json = constraints or {}

    # Get ratings if available in state
    ratings = state.get("ratings", {})

    logger.info(f"optimizer.propose_trades: portfolio_id={portfolio_id_uuid}")

    # Call optimizer service
    service = get_optimizer_service()
    result = await service.propose_trades(
        portfolio_id=portfolio_id_uuid,
        policy_json=policy_json,
        pricing_pack_id=ctx.pricing_pack_id,
        ratings=ratings,
    )

    # Attach metadata
    metadata = self._create_metadata(
        source=f"optimizer:{ctx.pricing_pack_id}",
        asof=ctx.asof_date,
        ttl=300,
    )

    return self._attach_metadata(result, metadata)
```

### Streamlit UI Integration

```python
# frontend/ui/screens/rebalance.py

import streamlit as st
import requests

st.title("Portfolio Rebalancing")

# Input: Policy constraints
min_quality = st.slider("Minimum Quality Score", 0.0, 10.0, 6.0)
max_turnover = st.slider("Maximum Turnover %", 0.0, 50.0, 20.0)
method = st.selectbox("Optimization Method",
    ["mean_variance", "risk_parity", "max_sharpe", "cvar"])

if st.button("Generate Rebalance Trades"):
    # Call executor API
    response = requests.post("http://localhost:8000/v1/execute", json={
        "pattern_id": "policy_rebalance",
        "inputs": {
            "portfolio_id": st.session_state.portfolio_id,
            "constraints": {
                "min_quality_score": min_quality,
                "max_turnover_pct": max_turnover,
                "method": method,
            }
        }
    })

    result = response.json()

    # Display results
    st.metric("Trade Count", result['trade_count'])
    st.metric("Turnover", f"{result['turnover_pct']:.2f}%")
    st.metric("Costs", f"{result['cost_bps']:.2f} bps")

    # Trade table
    st.subheader("Proposed Trades")
    st.dataframe(result['trades'])
```

---

## Error Handling

### No Riskfolio-Lib Installed

```python
service = get_optimizer_service()

if not service.riskfolio_available:
    print("⚠️  Riskfolio-Lib not installed. Using stub mode.")

result = await service.propose_trades(...)

# Result will have warning:
# warnings: ["Riskfolio-Lib not available. Install with: pip install riskfolio-lib"]
```

### No Positions Found

```python
result = await service.propose_trades(
    portfolio_id=UUID("empty-portfolio-id"),
    policy_json={},
    pricing_pack_id="PP_2025-10-26",
)

# Result:
# {
#     "trade_count": 0,
#     "trades": [],
#     "warnings": ["No positions found"]
# }
```

### Insufficient Price History

```python
result = await service.propose_trades(
    portfolio_id=portfolio_id,
    policy_json={"lookback_days": 252},
    pricing_pack_id="PP_2025-10-26",
)

# If < 30 days of price history:
# Falls back to equal-weight portfolio
# Logs warning: "Insufficient data for optimization (25 days)"
```

### Turnover Constraint Violation

```python
result = await service.propose_trades(
    portfolio_id=portfolio_id,
    policy_json={"max_turnover_pct": 10.0},  # Very tight
    pricing_pack_id="PP_2025-10-26",
)

# If optimizer proposes 25% turnover:
# - Trades are scaled down to 10% turnover
# - Warning added: "Trades scaled down to meet 10.0% turnover limit"
```

### Database Connection Error

```python
try:
    result = await service.propose_trades(...)
except Exception as e:
    logger.error(f"Optimizer failed: {e}")
    # Handle gracefully
```

---

## Testing Checklist

### Unit Tests

```python
import pytest
from app.services.optimizer import OptimizerService, PolicyConstraints

def test_parse_policy():
    service = OptimizerService()
    policy_json = {"min_quality_score": 7.0, "max_turnover_pct": 15.0}
    policy = service._parse_policy(policy_json)
    assert policy.min_quality_score == 7.0
    assert policy.max_turnover_pct == 15.0

def test_estimate_trade_cost():
    service = OptimizerService()
    policy = PolicyConstraints(commission_per_trade=5.00, market_impact_bps=15.0)
    cost = service._estimate_trade_cost(Decimal("10000.00"), policy)
    assert cost == Decimal("22.50")  # $5 + $17.50

def test_calculate_concentration():
    service = OptimizerService()
    positions = [
        {"symbol": "AAPL", "value": 10000},
        {"symbol": "MSFT", "value": 5000},
    ]
    concentration = service._calculate_concentration_top10(positions)
    assert concentration == 100.0  # Only 2 positions
```

### Integration Tests

```python
import pytest
from uuid import UUID

@pytest.mark.asyncio
async def test_propose_trades_with_db(db_session):
    service = get_optimizer_service()

    result = await service.propose_trades(
        portfolio_id=UUID("11111111-1111-1111-1111-111111111111"),
        policy_json={"max_turnover_pct": 20.0},
        pricing_pack_id="PP_2025-10-26",
    )

    assert result['trade_count'] >= 0
    assert result['turnover_pct'] <= 20.0
    assert result['constraints_met'] == True

@pytest.mark.asyncio
async def test_suggest_hedges(db_session):
    service = get_optimizer_service()

    hedges = await service.suggest_hedges(
        portfolio_id=UUID("11111111-1111-1111-1111-111111111111"),
        scenario_id="equity_selloff",
        pricing_pack_id="PP_2025-10-26",
    )

    assert hedges['scenario_id'] == "equity_selloff"
    assert len(hedges['hedges']) > 0
```

---

## Performance Tips

### 1. Cache Pricing Packs

```python
# Pricing packs are immutable, so cache historical prices
# Use pricing_pack_id as cache key

from functools import lru_cache

@lru_cache(maxsize=10)
async def get_price_history_cached(symbols_tuple, pricing_pack_id):
    return await service._fetch_price_history(list(symbols_tuple), pricing_pack_id)
```

### 2. Limit Lookback Period

```python
# Shorter lookback = faster optimization
policy_json = {
    "lookback_days": 126,  # 6 months instead of 12
}

# Trade-off: Less data = less stable covariance estimates
```

### 3. Use asyncio.gather for Parallel Calls

```python
# If rebalancing multiple portfolios:
tasks = [
    service.propose_trades(portfolio_id_1, policy, pack_id),
    service.propose_trades(portfolio_id_2, policy, pack_id),
    service.propose_trades(portfolio_id_3, policy, pack_id),
]

results = await asyncio.gather(*tasks)
```

---

## Best Practices

### 1. Always Include pricing_pack_id

```python
# ✅ GOOD: Reproducible
result = await service.propose_trades(
    portfolio_id=portfolio_id,
    policy_json=policy,
    pricing_pack_id="PP_2025-10-26",  # Explicit pack
)

# ❌ BAD: Not reproducible (would use latest pack)
# (Not supported - pricing_pack_id is required)
```

### 2. Provide Quality Ratings

```python
# ✅ GOOD: Quality-aware optimization
ratings = {"AAPL": 9.2, "RY": 8.5, "XIU": 7.0}
result = await service.propose_trades(
    portfolio_id=portfolio_id,
    policy_json={"min_quality_score": 6.0},
    pricing_pack_id=pack_id,
    ratings=ratings,  # Filter by quality
)

# ⚠️  OK: No quality filter (all holdings included)
result = await service.propose_trades(
    portfolio_id=portfolio_id,
    policy_json={},
    pricing_pack_id=pack_id,
    # No ratings provided
)
```

### 3. Check Constraints Met

```python
result = await service.propose_trades(...)

if not result['constraints_met']:
    print("⚠️  Some constraints could not be met")
    print(f"Warnings: {result['warnings']}")

# Example warning:
# "Trades scaled down to meet 10.0% turnover limit"
```

### 4. Analyze Impact Before Executing

```python
# Step 1: Get proposed trades
rebalance = await service.propose_trades(...)

# Step 2: Analyze impact
impact = await service.analyze_impact(
    portfolio_id=portfolio_id,
    proposed_trades=rebalance['trades'],
    pricing_pack_id=pack_id,
)

# Step 3: Review impact
if impact['delta_concentration'] < -10.0:
    print("✅ Concentration reduced by 10%")
else:
    print("⚠️  Minimal concentration improvement")

# Step 4: Decide whether to execute trades
if impact['value_delta'] > Decimal("-1000"):
    # Execute trades (costs < $1000)
    pass
```

### 5. Log All Rebalance Decisions

```python
import logging

logger = logging.getLogger("portfolio.rebalance")

result = await service.propose_trades(...)

logger.info(f"Rebalance proposed for portfolio {portfolio_id}")
logger.info(f"  Trades: {result['trade_count']}")
logger.info(f"  Turnover: {result['turnover_pct']:.2f}%")
logger.info(f"  Costs: ${result['estimated_costs']:.2f}")
logger.info(f"  Method: {result['method']}")

for trade in result['trades']:
    logger.info(f"  {trade['action']} {trade['quantity']} {trade['symbol']} @ ${trade['current_price']:.2f}")
```

---

## Complete Example: Full Workflow

```python
import asyncio
from uuid import UUID
from app.services.optimizer import get_optimizer_service

async def complete_rebalance_workflow():
    """
    Complete rebalance workflow:
    1. Propose trades
    2. Analyze impact
    3. Suggest hedges (if needed)
    4. Log decision
    """
    service = get_optimizer_service()

    portfolio_id = UUID("11111111-1111-1111-1111-111111111111")
    pricing_pack_id = "PP_2025-10-26"

    # Step 1: Define policy
    policy_json = {
        "min_quality_score": 6.0,
        "max_single_position_pct": 15.0,
        "max_turnover_pct": 20.0,
        "method": "mean_variance",
        "risk_free_rate": 0.02,
    }

    # Step 2: Get quality ratings (from ratings service)
    ratings = {"AAPL": 9.2, "RY": 8.5, "XIU": 7.0}

    # Step 3: Propose trades
    print("=" * 80)
    print("STEP 1: PROPOSE TRADES")
    print("=" * 80)

    rebalance = await service.propose_trades(
        portfolio_id=portfolio_id,
        policy_json=policy_json,
        pricing_pack_id=pricing_pack_id,
        ratings=ratings,
    )

    print(f"Trade Count: {rebalance['trade_count']}")
    print(f"Turnover: {rebalance['turnover_pct']:.2f}%")
    print(f"Costs: {rebalance['cost_bps']:.2f} bps")

    # Step 4: Analyze impact
    print("\n" + "=" * 80)
    print("STEP 2: ANALYZE IMPACT")
    print("=" * 80)

    impact = await service.analyze_impact(
        portfolio_id=portfolio_id,
        proposed_trades=rebalance['trades'],
        pricing_pack_id=pricing_pack_id,
    )

    print(f"Value Change: ${impact['value_delta']:.2f}")
    print(f"Concentration Change: {impact['delta_concentration']:.1f}%")

    # Step 5: Check if hedges needed (if equity-heavy)
    if impact['current_concentration_top10'] > 60.0:
        print("\n" + "=" * 80)
        print("STEP 3: SUGGEST HEDGES (High Concentration)")
        print("=" * 80)

        hedges = await service.suggest_hedges(
            portfolio_id=portfolio_id,
            scenario_id="equity_selloff",
            pricing_pack_id=pricing_pack_id,
        )

        print(f"Suggested Hedges: {len(hedges['hedges'])}")
        for hedge in hedges['hedges']:
            print(f"  {hedge['action']} {hedge['instrument']}: ${hedge['notional']:.2f}")

    # Step 6: Make decision
    print("\n" + "=" * 80)
    print("DECISION")
    print("=" * 80)

    if rebalance['constraints_met'] and impact['value_delta'] > -1000:
        print("✅ APPROVE REBALANCE")
        print(f"   Reason: Constraints met, costs acceptable (${-impact['value_delta']:.2f})")
    else:
        print("❌ REJECT REBALANCE")
        print(f"   Reason: {rebalance['warnings']}")

    return {
        "rebalance": rebalance,
        "impact": impact,
    }

# Run workflow
result = asyncio.run(complete_rebalance_workflow())
```

---

**Last Updated**: October 26, 2025
**Author**: OPTIMIZER_ARCHITECT Agent
**Status**: Production-ready examples
