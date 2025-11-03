# Code Patterns for OptimizerAgent → FinancialAnalyst Consolidation

## Quick Reference Guide for Implementation

---

## Pattern 1: Portfolio ID Resolution

**Used in:** All 4 methods

```python
# Resolve portfolio_id
if not portfolio_id:
    portfolio_id = str(ctx.portfolio_id) if ctx.portfolio_id else None
if not portfolio_id:
    raise ValueError("portfolio_id required for optimizer.METHOD_NAME")

portfolio_uuid = UUID(portfolio_id)
```

**Key Points:**
- Check parameter first, fall back to context
- String to UUID conversion for safety
- Raise ValueError with method name if missing

---

## Pattern 2: Pricing Pack Validation (SACRED)

**Used in:** All 4 methods

```python
# Get pricing_pack_id from context (SACRED for reproducibility)
pricing_pack_id = ctx.pricing_pack_id
if not pricing_pack_id:
    raise ValueError("pricing_pack_id required in context for optimizer.METHOD_NAME")
```

**Key Points:**
- SACRED invariant for reproducibility
- Always from context, not parameter
- Non-negotiable - raise ValueError if missing

---

## Pattern 3: Multi-Source Parameter Resolution

**Pattern A: Ratings (from state or parameter)**

```python
# Get ratings from state if not provided
if not ratings and state.get("ratings"):
    # Extract quality scores from ratings result
    ratings_result = state["ratings"]
    if isinstance(ratings_result, dict) and "positions" in ratings_result:
        # Portfolio ratings mode
        ratings = {
            pos["symbol"]: pos.get("rating", 0.0)
            for pos in ratings_result["positions"]
            if pos.get("rating") is not None
        }
    elif isinstance(ratings_result, dict) and "overall_rating" in ratings_result:
        # Single security ratings mode
        symbol = ratings_result.get("symbol")
        if symbol:
            ratings = {symbol: float(ratings_result["overall_rating"]) / 10.0}
```

**Pattern B: Proposed Trades (multi-location in state)**

```python
# Get proposed_trades from multiple possible locations
if not proposed_trades:
    # Check state for proposed_trades directly
    proposed_trades = state.get("proposed_trades")
if not proposed_trades:
    # Check state for rebalance_result.trades
    rebalance_result = state.get("rebalance_result")
    if rebalance_result and "trades" in rebalance_result:
        proposed_trades = rebalance_result["trades"]
if not proposed_trades:
    raise ValueError(
        "proposed_trades required for optimizer.analyze_impact. "
        "Run optimizer.propose_trades first."
    )
```

**Pattern C: Scenario ID (from scenario_result dict)**

```python
# Handle scenario_result from pattern or scenario_id parameter
if scenario_result:
    # Extract scenario_id from scenario_result object
    if isinstance(scenario_result, dict):
        scenario_id = scenario_result.get("scenario_id") or scenario_result.get("id")
        if not scenario_id:
            # Try to infer from scenario type or name
            scenario_id = scenario_result.get("scenario_type") or scenario_result.get("name") or "unknown"
elif not scenario_id:
    raise ValueError("Either scenario_id or scenario_result required for optimizer.suggest_hedges")
```

**Key Points:**
- Search multiple locations in state dict
- Multiple dict key variants (scenario_id, id, scenario_type, name)
- Fall back to direct parameter if state not available

---

## Pattern 4: Policy Parameter Consolidation

**Used in:** optimizer_propose_trades

```python
# Merge policies and constraints for pattern compatibility
if policies or constraints:
    # Handle both list and dict formats for policies
    if isinstance(policies, list):
        # Convert list of policies to a dict format for optimizer
        merged_policy = {}
        for policy in policies:
            if 'type' in policy:
                # Convert policy type to dict key
                if policy['type'] == 'min_quality_score':
                    merged_policy['min_quality_score'] = policy.get('value', 0.0)
                elif policy['type'] == 'max_single_position':
                    merged_policy['max_single_position_pct'] = policy.get('value', 20.0)
                elif policy['type'] == 'max_sector':
                    merged_policy['max_sector_pct'] = policy.get('value', 30.0)
                elif policy['type'] == 'target_allocation':
                    # Handle target allocations separately
                    category = policy.get('category', '')
                    value = policy.get('value', 0.0)
                    merged_policy[f'target_{category}'] = value
    else:
        # Use policies as base if it's a dict
        merged_policy = policies or {}
    
    # Merge constraints if provided
    if constraints and isinstance(constraints, dict):
        # Add constraints to the policy dict
        if 'max_turnover_pct' in constraints:
            merged_policy['max_turnover_pct'] = constraints['max_turnover_pct']
        if 'max_te_pct' in constraints:
            merged_policy['max_tracking_error_pct'] = constraints['max_te_pct']
        if 'min_lot_value' in constraints:
            merged_policy['min_lot_value'] = constraints['min_lot_value']
    
    policy_json = merged_policy

# Default policy if not provided
if not policy_json:
    policy_json = {
        "min_quality_score": 0.0,
        "max_single_position_pct": 20.0,
        "max_sector_pct": 30.0,
        "max_turnover_pct": 20.0,
        "max_tracking_error_pct": 3.0,
        "method": "mean_variance",
    }
```

**Key Points:**
- Handle list format (convert type→value to dict keys)
- Handle dict format (merge with constraints)
- Apply sensible defaults
- Support key name variations (max_te_pct → max_tracking_error_pct)

---

## Pattern 5: Regime Multi-Source Resolution

**Used in:** optimizer_suggest_deleveraging_hedges

```python
# Resolve regime from pattern parameters or state
if ltdc_phase:
    # Map LTDC phase to regime
    regime_mapping = {
        "Phase 1": "LATE_EXPANSION",
        "Phase 2": "DELEVERAGING", 
        "Phase 3": "DEPRESSION",
        "Phase 4": "EARLY_EXPANSION",
    }
    regime = regime_mapping.get(ltdc_phase, "LATE_EXPANSION")
elif scenarios:
    # Infer regime from scenario results
    # Look for the most severe scenario impact
    max_impact = 0.0
    regime = "LATE_EXPANSION"  # Default
    for scenario_name, scenario_result in scenarios.items():
        if isinstance(scenario_result, dict):
            impact = scenario_result.get("total_delta_pct", 0.0)
            if impact > max_impact:
                max_impact = impact
                # Map scenario to regime
                if "default" in scenario_name.lower():
                    regime = "DEPRESSION"
                elif "austerity" in scenario_name.lower():
                    regime = "DELEVERAGING"
                elif "money_printing" in scenario_name.lower():
                    regime = "LATE_EXPANSION"
elif not regime:
    # Get regime from state if not provided
    regime_result = state.get("regime")
    if regime_result and isinstance(regime_result, dict):
        regime = regime_result.get("regime")

if not regime:
    raise ValueError(
        "regime required for optimizer.suggest_deleveraging_hedges. "
        "Provide regime, ltdc_phase, scenarios, or run macro.detect_regime first."
    )
```

**Key Points:**
- Priority order: direct param → LTDC phase → scenario inference → state
- Scenario inference: find max impact and map scenario name to regime
- Always have a fallback (LATE_EXPANSION)
- Clear error message with resolution options

---

## Pattern 6: Service Call with Metadata

**Used in:** All 4 methods

```python
logger.info(
    f"optimizer.METHOD_NAME: portfolio_id={portfolio_id}, "
    f"pricing_pack_id={pricing_pack_id}, "
    f"other_param={value}"
)

# Call optimizer service
optimizer_service = get_optimizer_service()

try:
    result = await optimizer_service.METHOD_NAME(
        portfolio_id=portfolio_uuid,
        # ... other params ...
        pricing_pack_id=pricing_pack_id,
    )

    # Attach metadata
    metadata = self._create_metadata(
        source=f"optimizer_service:{ctx.pricing_pack_id}",
        asof=ctx.asof_date or date.today(),
        ttl=0,  # Or 3600 for cached methods
    )

    return self._attach_metadata(result, metadata)

except Exception as e:
    logger.error(f"METHOD_NAME failed: {e}", exc_info=True)
    error_result = {
        # ... empty/zero structure ...
        "error": str(e),
        "warnings": [f"Method failed: {str(e)}"],
    }
    metadata = self._create_metadata(
        source=f"optimizer_service:error",
        asof=ctx.asof_date or date.today(),
        ttl=0,
    )
    return self._attach_metadata(error_result, metadata)
```

**Key Points:**
- Always log entry with parameters
- Delegate to service method
- Attach metadata (source includes pricing_pack_id and method name)
- TTL=0 for proposals (always fresh), TTL=3600 for hedges (cacheable)
- Error handling returns empty/zero structure with error message
- Always attach metadata even on error

---

## Pattern 7: TTL (Time-To-Live) Strategy

**TTL=0 (No Caching):**
- `optimizer.propose_trades` - Trade proposals must be fresh (always recompute)
- `optimizer.analyze_impact` - Impact analysis depends on latest positions

**TTL=3600 (1-hour cache):**
- `optimizer.suggest_hedges` - Scenario hedges are relatively stable
- `optimizer.suggest_deleveraging_hedges` - Regime recommendations are stable

```python
# For fresh data:
metadata = self._create_metadata(
    source=f"optimizer_service:{ctx.pricing_pack_id}",
    asof=ctx.asof_date or date.today(),
    ttl=0,  # No caching
)

# For cacheable data:
metadata = self._create_metadata(
    source=f"optimizer_service:hedges:{scenario_id}",
    asof=ctx.asof_date or date.today(),
    ttl=3600,  # Cache for 1 hour
)
```

---

## Pattern 8: Return Structure Patterns

### Pattern A: Trade Proposals (propose_trades)
```python
{
    "trades": [
        {
            "symbol": str,
            "security_id": str,
            "action": "BUY"|"SELL"|"HOLD",
            "quantity": int,
            "current_shares": int,
            "target_shares": int,
            "current_weight_pct": float,
            "target_weight_pct": float,
            "current_price": float,
            "trade_value": float,
            "estimated_cost": float,
            "rationale": str,
        }
    ],
    "trade_count": int,
    "total_turnover": Decimal,
    "turnover_pct": float,
    "estimated_costs": Decimal,
    "cost_bps": float,
    "method": str,
    "constraints_met": bool,
    "warnings": List[str],
    "_metadata": Dict,
}
```

### Pattern B: Impact Analysis (analyze_impact)
```python
{
    "current_value": Decimal,
    "post_rebalance_value": Decimal,
    "value_delta": Decimal,
    "current_concentration": float,        # % in top 10
    "post_concentration": float,
    "concentration_delta": float,
    # Optional fields (TODO: not yet implemented):
    # "current_sharpe": float,
    # "post_sharpe": float,
    # "current_vol": float,
    # "post_vol": float,
    "_metadata": Dict,
}
```

### Pattern C: Hedge Recommendations (suggest_hedges)
```python
{
    "scenario_id": str,
    "hedges": [
        {
            "instrument": str,
            "instrument_type": str,  # "equity", "option", "futures", "etf"
            "action": "BUY"|"SELL",
            "notional": Decimal,
            "hedge_ratio": float,
            "rationale": str,
            "expected_offset_pct": float,
        }
    ],
    "total_notional": Decimal,
    "expected_offset_pct": float,
    "_metadata": Dict,
}
```

### Pattern D: Deleveraging Recommendations (suggest_deleveraging_hedges)
```python
{
    "regime": str,
    "recommendations": [
        {
            "action": str,  # "reduce_equity_exposure", "increase_safe_havens", etc.
            "instruments": List[str],
            "target_reduction_pct": float,  # Optional
            "target_allocation_pct": float,  # Optional
            "rationale": str,
        }
    ],
    "total_reduction_pct": float,
    "total_allocation_pct": float,
    "_metadata": Dict,
}
```

---

## Pattern 9: Dalio Deleveraging Regimes

**Reference for deleveraging recommendations:**

```python
DELEVERAGING / DEPRESSION (Aggressive):
  - reduce_equity_exposure: SPY, QQQ, VTI → 40% reduction
  - increase_safe_havens: GLD, TLT, CASH → 30% allocation
  - avoid_credit: HYG, JNK → 100% exit

LATE_EXPANSION (Moderate):
  - reduce_equity_exposure: SPY, QQQ → 20% reduction
  - increase_defensive: XLU, XLP, VNQ → 15% allocation

REFLATION (Inflation Protection):
  - reduce_duration: TLT, IEF → 50% reduction
  - increase_inflation_hedges: GLD, TIP, DBC → 20% allocation
```

---

## Pattern 10: Scenario Type Mapping

**Reference for suggest_hedges scenario mapping:**

```python
scenario_mapping = {
    "rates_up": ShockType.RATES_UP,
    "rates_down": ShockType.RATES_DOWN,
    "usd_up": ShockType.USD_UP,
    "usd_down": ShockType.USD_DOWN,
    "inflation": ShockType.CPI_SURPRISE,
    "cpi_surprise": ShockType.CPI_SURPRISE,
    "credit_spread_widening": ShockType.CREDIT_SPREAD_WIDENING,
    "equity_selloff": ShockType.EQUITY_SELLOFF,
    "equity_rally": ShockType.EQUITY_RALLY,
    "late_cycle_rates_up": ShockType.RATES_UP,
    "recession_mild": ShockType.EQUITY_SELLOFF,
}

# Hedge recommendations:
rates_up → Long TLT (long-duration treasuries)
equity_selloff → VIX calls + SPY puts
usd_up → Short UUP (USD ETF)
credit_spread_widening → LQD puts (IG credit)
```

---

## Logging Best Practices

```python
# Entry point
logger.info(
    f"optimizer.METHOD_NAME: portfolio_id={portfolio_id}, "
    f"pricing_pack_id={pricing_pack_id}, "
    f"key_param={value}"
)

# Success with metrics
logger.info(
    f"Generated {len(trades)} trade proposals, "
    f"turnover={turnover_pct:.1f}%, "
    f"costs={cost_bps:.1f}bps"
)

# Data issues
logger.warning(f"No positions found for portfolio {portfolio_id}")
logger.warning(f"Riskfolio-Lib not available. Using stub mode.")
logger.warning(f"Constraint violated: turnover {turnover_pct:.1f}% exceeds {max_pct}%")

# Errors (always include traceback)
logger.error(f"Trade proposal generation failed: {e}", exc_info=True)
logger.error(f"Hedge suggestion failed for scenario {scenario_id}: {e}", exc_info=True)
```

---

## Key Service Dependencies

### OptimizerService Methods Called
```python
await optimizer_service.propose_trades(
    portfolio_id: UUID,
    policy_json: Dict[str, Any],
    pricing_pack_id: str,
    ratings: Optional[Dict[str, float]],
    positions: Optional[List[Dict[str, Any]]],
    use_db: bool,
)

await optimizer_service.analyze_impact(
    portfolio_id: UUID,
    proposed_trades: List[Dict[str, Any]],
    pricing_pack_id: str,
)

await optimizer_service.suggest_hedges(
    portfolio_id: UUID,
    scenario_id: str,
    pricing_pack_id: str,
)

await optimizer_service.suggest_deleveraging_hedges(
    portfolio_id: UUID,
    regime: str,
    pricing_pack_id: str,
)
```

### Service Acquisition
```python
from app.services.optimizer import get_optimizer_service

optimizer_service = get_optimizer_service()
```

---

## Implementation Checklist for Consolidation

- [ ] Copy method signatures to FinancialAnalyst
- [ ] Adjust method names (optimizer_* → financial_analyst_*)
- [ ] Update logging prefix from "DawsOS.OptimizerAgent" to "DawsOS.FinancialAnalyst"
- [ ] Update capability registration in get_capabilities()
- [ ] Ensure OptimizerService is injected as service dependency
- [ ] Test parameter resolution from multiple sources
- [ ] Test error handling and empty result generation
- [ ] Test metadata attachment (TTL values)
- [ ] Verify pattern compatibility (policies, constraints, scenario_result, ltdc_phase)
- [ ] Test with missing optional parameters
- [ ] Verify logging messages include correct agent name
- [ ] Test dual-registration for backward compatibility (if needed)
- [ ] Document new capabilities in docstring

