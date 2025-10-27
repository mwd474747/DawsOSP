# Optimizer Agent Specification

**Role**: Portfolio optimization and policy-based rebalancing
**Context**: [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md) | [ORCHESTRATOR.md](./ORCHESTRATOR.md)
**Status**: ⚠️ Partial Implementation (Service Ready, Agent Implemented)
**Priority**: P1
**Last Updated**: October 27, 2025

---

## Mission

Provide portfolio optimization capabilities using Riskfolio-Lib for mean-variance optimization with policy constraints, quality ratings, tracking error limits, and trade proposals.

---

## Current Capabilities

### ⚠️ Implemented but Not Fully Integrated

1. **Trade Proposals**
   - `optimizer.propose_trades` - Generate trade proposals for rebalancing
   - `optimizer.analyze_impact` - Analyze impact of proposed trades

2. **Hedge Suggestions**
   - `optimizer.suggest_hedges` - Suggest hedging strategies
   - `optimizer.suggest_deleveraging_hedges` - Suggest deleveraging hedges

### ⚠️ Service Integration Status
- **Service Class**: `OptimizerService` in `backend/app/services/optimizer.py` ✅ Implemented
- **Agent Class**: `OptimizerAgent` in `backend/app/agents/optimizer_agent.py` ✅ Implemented
- **Pattern Integration**: `policy_rebalance.json` exists but not fully wired
- **Riskfolio-Lib**: Integration implemented but needs testing

---

## Implementation Status

### ✅ Service Layer Complete
- Riskfolio-Lib integration implemented
- Policy constraint logic implemented
- Trade proposal generation implemented
- Cost estimation implemented

### ⚠️ Agent Layer Partial
- Agent class implemented
- Capabilities declared
- Method stubs implemented
- Service integration needs completion

### ❌ Pattern Integration Pending
- `policy_rebalance` pattern exists but not fully functional
- UI integration pending
- End-to-end testing pending

---

## Code Examples

### Agent Method Implementation
```python
async def optimizer_propose_trades(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    policy_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Generate trade proposals for portfolio rebalancing."""
    portfolio_id = portfolio_id or (str(ctx.portfolio_id) if ctx.portfolio_id else None)
    
    if not portfolio_id:
        raise ValueError("portfolio_id required for optimizer.propose_trades")
    
    logger.info(f"optimizer.propose_trades: portfolio_id={portfolio_id}")
    
    try:
        # Get optimizer service
        optimizer_service = get_optimizer_service()
        
        # Generate trade proposals
        proposals = await optimizer_service.propose_trades(
            portfolio_id=UUID(portfolio_id),
            policy_id=policy_id or "default",
            asof_date=ctx.asof_date
        )
        
        # Attach metadata
        metadata = self._create_metadata(
            source=f"optimizer_service:{ctx.pricing_pack_id}",
            asof=ctx.asof_date,
            ttl=1800
        )
        
        return self._attach_metadata(proposals, metadata)
        
    except Exception as e:
        logger.error(f"Optimizer service error: {e}")
        return self._attach_metadata({
            "error": "Trade proposal generation failed",
            "proposals": None
        }, metadata)
```

### Service Integration Example
```python
async def propose_trades(
    self,
    portfolio_id: UUID,
    policy_id: str = "default",
    asof_date: date = None
) -> Dict[str, Any]:
    """Generate trade proposals using Riskfolio-Lib."""
    
    # Load portfolio positions
    positions = await self._load_positions(portfolio_id, asof_date)
    
    # Load policy constraints
    policy = await self._load_policy(policy_id)
    
    # Run optimization
    optimization_result = await self._run_optimization(positions, policy)
    
    # Generate trade proposals
    proposals = await self._generate_proposals(optimization_result, positions)
    
    return {
        "proposals": proposals,
        "optimization_result": optimization_result,
        "policy_applied": policy
    }
```

---

## Integration Points

### Services Used
- **OptimizerService**: Core optimization logic
- **RatingsService**: Quality constraints
- **PricingService**: Position valuation
- **LedgerService**: Position data

### Patterns Using This Agent
- `policy_rebalance` - Policy-based rebalancing (pending integration)

### Database Tables
- `portfolios` - Portfolio data
- `lots` - Position data
- `ratings` - Quality ratings
- `pricing_packs` - Valuation data

---

## Policy Framework

### Policy Types
1. **Quality-Based Policy**
   - Minimum quality score threshold
   - Maximum single position weight
   - Sector concentration limits

2. **Tracking Error Policy**
   - Maximum tracking error vs benchmark
   - Factor exposure limits
   - Volatility constraints

3. **Turnover Policy**
   - Maximum turnover per rebalance
   - Transaction cost limits
   - Tax efficiency constraints

### Policy Configuration
```json
{
  "policy_id": "conservative_quality",
  "constraints": {
    "min_quality_score": 6.0,
    "max_position_weight": 0.10,
    "max_tracking_error": 0.02,
    "max_turnover": 0.20
  }
}
```

---

## Riskfolio-Lib Integration

### Optimization Methods
- Mean-variance optimization
- Black-Litterman model
- Risk parity optimization
- Factor-based optimization

### Constraints Supported
- Weight constraints (min/max)
- Sector constraints
- Quality constraints
- Turnover constraints
- Transaction costs

### Example Usage
```python
import riskfolio as rp

# Create portfolio object
port = rp.Portfolio(returns=returns)

# Set optimization parameters
port.assets_stats(method_mu='hist', method_cov='hist')

# Add constraints
port.add_constraint(kind='box', up=0.10)  # Max 10% per position
port.add_constraint(kind='box', low=0.01)  # Min 1% per position

# Optimize
w = port.optimization(model='Classic', rm='MV', obj='Sharpe')
```

---

## Performance Characteristics

### Response Times
- `optimizer.propose_trades`: ~5-15 seconds (optimization dependent)
- `optimizer.analyze_impact`: ~2-5 seconds
- `optimizer.suggest_hedges`: ~3-8 seconds

### Optimization Complexity
- Small portfolios (< 50 positions): ~5 seconds
- Medium portfolios (50-200 positions): ~10 seconds
- Large portfolios (> 200 positions): ~15+ seconds

### Caching Strategy
- Optimization results: 1 hour TTL
- Trade proposals: 30 minutes TTL
- Policy configurations: 24 hours TTL

---

## Error Handling

### Optimization Failures
```python
try:
    result = await self._run_optimization(positions, policy)
except OptimizationError as e:
    logger.error(f"Optimization failed: {e}")
    return {
        "error": "Optimization failed",
        "fallback": "Use current allocation"
    }
except ConstraintError as e:
    logger.error(f"Constraint violation: {e}")
    return {
        "error": "Policy constraints cannot be satisfied",
        "suggestion": "Relax constraints or reduce positions"
    }
```

### Common Error Scenarios
- Infeasible constraints
- Insufficient data
- Optimization timeout
- Service unavailability

---

## Future Enhancements

### Planned Capabilities
- Multi-period optimization
- Tax-loss harvesting
- ESG constraint integration
- Real-time optimization

### Performance Improvements
- Parallel optimization
- Advanced caching
- Incremental optimization
- GPU acceleration

---

## Testing

### Test Coverage Needed
- Unit tests for optimization logic
- Integration tests with Riskfolio-Lib
- Policy constraint tests
- Performance tests

### Test Files to Create
- `backend/tests/unit/test_optimizer_agent.py`
- `backend/tests/integration/test_optimization.py`
- `backend/tests/golden/test_trade_proposals.py`

---

## Configuration

### Environment Variables
- `RISKFOLIO_CACHE_SIZE` - Optimization cache size
- `OPTIMIZATION_TIMEOUT` - Maximum optimization time
- `DEFAULT_POLICY_ID` - Default policy configuration

### Riskfolio-Lib Configuration
```python
RISKFOLIO_CONFIG = {
    "method_mu": "hist",
    "method_cov": "hist",
    "model": "Classic",
    "rm": "MV",
    "obj": "Sharpe"
}
```

---

## Monitoring and Observability

### Key Metrics
- Optimization success rate
- Average optimization time
- Constraint satisfaction rate
- Trade proposal acceptance rate

### Logging
- Optimization execution logs
- Constraint violation logs
- Performance timing logs
- Error logs with context

### Health Checks
- Riskfolio-Lib availability
- Optimization performance
- Constraint satisfaction
- Service response times
