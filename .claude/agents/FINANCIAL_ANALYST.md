# Financial Analyst Agent Specification

**Role**: Portfolio data, pricing, metrics computation, and risk analysis
**Context**: [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md) | [ORCHESTRATOR.md](./ORCHESTRATOR.md)
**Status**: ✅ Operational (Production)
**Priority**: P0
**Last Updated**: October 27, 2025

---

## Mission

Provide comprehensive portfolio analysis capabilities including position loading, pricing application, metrics computation, currency attribution, and risk factor analysis. This is the core agent for all portfolio-related operations.

---

## Current Capabilities

### ✅ Implemented and Operational

1. **Portfolio Data Management**
   - `ledger.positions` - Load portfolio positions from lots table
   - `pricing.apply_pack` - Apply pricing pack to positions for valuation

2. **Performance Metrics**
   - `metrics.compute` - Generic metrics computation wrapper
   - `metrics.compute_twr` - Time-weighted return calculation
   - `metrics.compute_sharpe` - Sharpe ratio calculation

3. **Attribution Analysis**
   - `attribution.currency` - Currency return decomposition

4. **Visualization**
   - `charts.overview` - Generate portfolio overview charts

5. **Risk Analysis**
   - `risk.compute_factor_exposures` - Factor exposure calculation
   - `risk.get_factor_exposure_history` - Historical factor exposure
   - `risk.overlay_cycle_phases` - Cycle-aware risk analysis

6. **Position Analysis**
   - `get_position_details` - Individual position details
   - `compute_position_return` - Position-level return calculation
   - `compute_portfolio_contribution` - Portfolio contribution analysis
   - `compute_position_currency_attribution` - Position-level FX attribution
   - `compute_position_risk` - Position-level risk metrics

7. **Transaction Analysis**
   - `get_transaction_history` - Transaction history retrieval
   - `get_security_fundamentals` - Security fundamental data
   - `get_comparable_positions` - Comparable position analysis

---

## Implementation Status

### ✅ Complete Implementation
- **Agent Class**: `FinancialAnalyst` in `backend/app/agents/financial_analyst.py`
- **Service Integration**: Integrated with LedgerService, PricingService, MetricsService
- **Database Integration**: Full TimescaleDB integration for metrics and attribution
- **Pattern Integration**: Used by `portfolio_overview`, `holding_deep_dive`, `portfolio_macro_overview`
- **Testing**: Comprehensive test coverage in `backend/tests/`

### ✅ Production Ready
- All capabilities implemented and tested
- Database integration complete
- Pattern execution working
- Error handling and graceful degradation
- Metadata attachment for traceability

---

## Code Examples

### Agent Method Implementation
```python
async def ledger_positions(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Get portfolio positions from Beancount ledger."""
    portfolio_id = portfolio_id or (str(ctx.portfolio_id) if ctx.portfolio_id else None)
    
    if not portfolio_id:
        raise ValueError("portfolio_id required for ledger.positions")
    
    logger.info(f"ledger.positions: portfolio_id={portfolio_id}, asof_date={ctx.asof_date}")
    
    # Get positions from ledger service
    ledger_service = get_ledger_service()
    positions = await ledger_service.get_positions(
        portfolio_id=UUID(portfolio_id),
        asof_date=ctx.asof_date
    )
    
    # Attach metadata
    metadata = self._create_metadata(
        source=f"ledger_service:{ctx.pricing_pack_id}",
        asof=ctx.asof_date,
        ttl=300
    )
    
    return self._attach_metadata({"positions": positions}, metadata)
```

### Service Integration Pattern
```python
async def metrics_compute_twr(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    lookback_days: int = 252,
) -> Dict[str, Any]:
    """Compute Time-Weighted Return."""
    portfolio_id = portfolio_id or (str(ctx.portfolio_id) if ctx.portfolio_id else None)
    
    # Get metrics service
    metrics_service = get_metrics_service()
    
    # Compute TWR
    twr_result = await metrics_service.compute_twr(
        portfolio_id=UUID(portfolio_id),
        asof_date=ctx.asof_date,
        lookback_days=lookback_days
    )
    
    # Attach metadata
    metadata = self._create_metadata(
        source=f"metrics_service:{ctx.pricing_pack_id}",
        asof=ctx.asof_date,
        ttl=3600
    )
    
    return self._attach_metadata(twr_result, metadata)
```

---

## Integration Points

### Services Used
- **LedgerService**: Position and transaction data
- **PricingService**: Position valuation and pricing packs
- **MetricsService**: Performance metrics calculation
- **CurrencyAttributor**: Multi-currency attribution analysis

### Patterns Using This Agent
- `portfolio_overview` - Core portfolio analysis
- `holding_deep_dive` - Individual position analysis
- `portfolio_macro_overview` - Macro-aware portfolio analysis
- `portfolio_cycle_risk` - Cycle-aware risk analysis

### Database Tables
- `lots` - Position data
- `transactions` - Transaction history
- `portfolio_metrics` - Computed metrics
- `currency_attribution` - FX attribution data
- `factor_exposures` - Risk factor data

---

## Performance Characteristics

### Response Times
- `ledger.positions`: ~50ms (cached)
- `pricing.apply_pack`: ~100ms (depends on position count)
- `metrics.compute_twr`: ~200ms (database query)
- `attribution.currency`: ~150ms (complex calculation)

### Caching Strategy
- Position data: 5 minutes TTL
- Metrics: 1 hour TTL
- Attribution: 30 minutes TTL
- Charts: 15 minutes TTL

---

## Error Handling

### Graceful Degradation
```python
try:
    result = await service.compute_metrics(portfolio_id)
except DatabaseError as e:
    logger.error(f"Database error in metrics computation: {e}")
    result = {"error": "Metrics computation unavailable", "metrics": None}
except Exception as e:
    logger.error(f"Unexpected error in metrics computation: {e}")
    result = {"error": "Metrics computation failed", "metrics": None}

return self._attach_metadata(result, metadata)
```

### Error Types Handled
- Database connection errors
- Missing portfolio data
- Invalid pricing pack references
- Calculation errors (division by zero, etc.)
- Service unavailability

---

## Future Enhancements

### Planned Capabilities
- Real-time position updates
- Advanced risk metrics (VaR, CVaR)
- Sector attribution analysis
- Benchmark comparison
- Tax-loss harvesting analysis

### Performance Improvements
- Parallel metric computation
- Advanced caching strategies
- Database query optimization
- Real-time data streaming

---

## Testing

### Test Coverage
- Unit tests for all capabilities
- Integration tests with database
- Pattern execution tests
- Error handling tests
- Performance tests

### Test Files
- `backend/tests/unit/test_financial_analyst.py`
- `backend/tests/integration/test_portfolio_analysis.py`
- `backend/tests/golden/test_metrics_calculation.py`

---

## Dependencies

### Required Services
- LedgerService (position data)
- PricingService (valuation)
- MetricsService (performance)
- CurrencyAttributor (FX analysis)

### Required Database Tables
- `lots`, `transactions`, `portfolio_metrics`, `currency_attribution`, `factor_exposures`

### Required Environment Variables
- `DATABASE_URL` - Database connection
- `PRICING_POLICY` - Pricing policy (default: WM4PM_CAD)

---

## Monitoring and Observability

### Key Metrics
- Request count per capability
- Response time percentiles
- Error rates by capability
- Cache hit rates
- Database query performance

### Logging
- Capability execution logs
- Performance timing logs
- Error logs with stack traces
- Database query logs

### Health Checks
- Database connectivity
- Service availability
- Cache health
- Performance thresholds
