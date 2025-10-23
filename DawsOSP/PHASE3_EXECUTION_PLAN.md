# Phase 3: Metrics + Currency Attribution - EXECUTION PLAN

**Date**: 2025-10-22
**Status**: 🔄 READY TO START
**Duration**: 5 days (40 hours estimated)
**Sprint**: S2-W3 (Sprint 2 Week 3)

---

## Executive Summary

Phase 3 implements **portfolio metrics** (TWR, MWR, Sharpe) and **currency attribution** (local/FX/interaction) with ±1bp accuracy requirements and TimescaleDB continuous aggregates.

**Context**: Phase 2 complete (execution path working), Phase 1 has stub implementations that need DB wiring.

**Critical Deliverables**:
1. Wire metrics computation to database
2. Implement currency attribution (local/FX/interaction)
3. Setup TimescaleDB continuous aggregates
4. Property tests for currency identities
5. Integration with agent runtime

---

## Phase 1 Assets (Verified)

From Phase 1 verification, we have:

### ✅ Already Implemented (Jobs)

**`backend/jobs/metrics.py`** (513 lines):
- `PortfolioMetrics` dataclass (complete)
- `MetricsComputer` class with:
  - TWR/MWR calculations
  - Volatility (rolling 30/60/90 day)
  - Sharpe ratio
  - Alpha/Beta vs benchmark
  - Max drawdown
  - Win rate
- **Status**: Stub implementation (needs DB wiring)

**`backend/jobs/reconciliation.py`** (529 lines):
- Ledger vs DB reconciliation
- ±1bp accuracy validation
- **Status**: Working (Phase 1)

### ✅ Already Implemented (Services)

**`backend/app/services/metrics.py`** - Check if exists
**`backend/app/services/risk_metrics.py`** - Risk calculations

### ⚠️ Missing (Phase 3 Deliverables)

1. **Currency Attribution Logic** - Not implemented
2. **Database Tables** - `portfolio_metrics`, `currency_attribution`, `factor_exposures`
3. **TimescaleDB Setup** - Continuous aggregates
4. **Agent Integration** - metrics.* capabilities
5. **Property Tests** - Currency identity validation

---

## Phase 3 Requirements (from PRODUCT_SPEC)

### Sprint 2 Week 3: Metrics + Currency Attribution

**Deliverables**:
- TWR/MWR/Sharpe calculations
- Currency attribution (local/FX/interaction with ±0.1bp invariant)
- Continuous aggregates (30-day rolling vol, TimescaleDB)
- Property tests (currency identity, FX triangulation)

**Acceptance Criteria**:
- ✅ TWR matches Beancount ±1bp
- ✅ Currency attribution identity holds: `r_base ≈ (1+r_local)(1+r_fx)-1 ±0.1bp`
- ✅ Continuous aggregates update nightly

---

## Task Breakdown (5 Tasks)

### Task 1: Database Schema for Metrics
**Priority**: P0 (Foundation)
**Duration**: 3 hours
**Dependencies**: Phase 2 (database connection)

**Deliverables**:
1. `backend/db/schema/portfolio_metrics.sql` (150 lines)
   - portfolio_metrics hypertable (TimescaleDB)
   - currency_attribution table
   - factor_exposures table
   - Continuous aggregates (rolling vol, betas)

2. `backend/app/db/metrics_queries.py` (300 lines)
   - insert_metrics()
   - get_metrics_history()
   - get_latest_metrics()
   - get_rolling_metrics()

**Schema** (from PRODUCT_SPEC):
```sql
CREATE TABLE portfolio_metrics (
    portfolio_id UUID NOT NULL,
    asof_date DATE NOT NULL,
    pricing_pack_id TEXT NOT NULL,

    -- Returns
    twr_1d NUMERIC(12, 8),
    twr_mtd NUMERIC(12, 8),
    twr_ytd NUMERIC(12, 8),
    twr_1y NUMERIC(12, 8),

    -- Risk
    volatility_30d NUMERIC(12, 8),
    sharpe_30d NUMERIC(12, 8),
    max_drawdown_1y NUMERIC(12, 8),

    -- Benchmark relative
    alpha_1y NUMERIC(12, 8),
    beta_1y NUMERIC(12, 8),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (portfolio_id, asof_date, pricing_pack_id)
);

-- TimescaleDB hypertable
SELECT create_hypertable('portfolio_metrics', 'asof_date');

-- Continuous aggregate: 30-day rolling volatility
CREATE MATERIALIZED VIEW portfolio_metrics_30d_rolling
WITH (timescaledb.continuous) AS
SELECT
    portfolio_id,
    time_bucket('1 day', asof_date) AS day,
    stddev(twr_1d) * sqrt(252) AS volatility_30d_realized
FROM portfolio_metrics
WHERE asof_date >= NOW() - INTERVAL '30 days'
GROUP BY portfolio_id, day;
```

**Acceptance**:
- ✅ Hypertable created
- ✅ Continuous aggregates configured
- ✅ Queries return results < 50ms

---

### Task 2: Currency Attribution Implementation
**Priority**: P0 (Critical Path)
**Duration**: 8 hours
**Dependencies**: Task 1 (schema)

**Deliverables**:
1. `backend/app/services/currency_attribution.py` (400 lines)
   - `CurrencyAttributionService` class
   - `compute_attribution(positions, pack_id) → (r_local, r_fx, r_interaction)`
   - Validation: `r_base ≈ (1+r_local)(1+r_fx)-1 ±0.1bp`

2. `backend/tests/test_currency_attribution.py` (300 lines)
   - Unit tests: attribution calculation
   - Property tests: identity `(1+r_local)(1+r_fx)-1`
   - Property tests: FX triangulation
   - Integration test: multi-currency portfolio

**Algorithm** (from PRODUCT_SPEC):
```python
def compute_attribution(positions, pack_id):
    """
    Compute currency attribution.

    Returns: (r_local, r_fx, r_interaction)

    Identity: r_base = (1+r_local)(1+r_fx) - 1
            = r_local + r_fx + r_local*r_fx

    Where:
    - r_local: Local currency return (price change in local ccy)
    - r_fx: FX return (currency movement)
    - r_interaction: Cross-term (r_local * r_fx)
    """
    local_returns = []
    fx_returns = []
    weights = []

    for pos in positions:
        # Local return
        p0 = get_price(pos.symbol, pack_id - 1day, pos.local_ccy)
        p1 = get_price(pos.symbol, pack_id, pos.local_ccy)
        r_local = (p1 - p0) / p0

        # FX return
        fx0 = get_fx_rate(pos.local_ccy, base_ccy, pack_id - 1day)
        fx1 = get_fx_rate(pos.local_ccy, base_ccy, pack_id)
        r_fx = (fx1 - fx0) / fx0

        # Weight
        w = pos.value_base(pack_id - 1day) / portfolio_value(pack_id - 1day)

        local_returns.append(r_local * w)
        fx_returns.append(r_fx * w)
        weights.append(w)

    r_local_portfolio = sum(local_returns)
    r_fx_portfolio = sum(fx_returns)
    r_interaction = r_local_portfolio * r_fx_portfolio

    # Validate identity
    r_base_computed = r_local_portfolio + r_fx_portfolio + r_interaction
    r_base_actual = portfolio_return_base(pack_id)

    error_bps = abs(r_base_computed - r_base_actual) * 10000
    assert error_bps <= 0.1, f"Attribution identity violated: {error_bps:.4f} bp"

    return {
        "local_return": r_local_portfolio,
        "fx_return": r_fx_portfolio,
        "interaction_return": r_interaction,
        "total_return": r_base_computed,
        "error_bps": error_bps,
    }
```

**Acceptance**:
- ✅ Attribution identity holds ±0.1bp
- ✅ Multi-currency portfolio attribution correct
- ✅ Property tests pass (100 random portfolios)

---

### Task 3: Wire Metrics to Database
**Priority**: P0 (Critical Path)
**Duration**: 6 hours
**Dependencies**: Task 1 (schema), existing metrics.py

**Deliverables**:
1. Update `backend/jobs/metrics.py` (+200 lines)
   - Replace stub with DB insert
   - Use `metrics_queries.insert_metrics()`
   - Store TWR/MWR/Sharpe in database

2. Update `backend/app/agents/financial_analyst.py` (+100 lines)
   - Add `metrics.compute_twr` capability (wire to DB)
   - Add `metrics.currency_attribution` capability

3. Integration test: End-to-end metrics flow
   - Nightly job → compute metrics → DB → agent → UI

**Flow**:
```
Nightly Job (00:07) → MetricsComputer.compute_all() → INSERT portfolio_metrics
                   ↓
Agent Runtime → metrics.compute_twr → SELECT from portfolio_metrics
             ↓
UI → Display TWR/MWR/Sharpe with provenance (pack_id, asof_date)
```

**Acceptance**:
- ✅ Metrics stored in database
- ✅ Agent capability returns metrics from DB
- ✅ TWR matches Beancount ±1bp

---

### Task 4: TimescaleDB Continuous Aggregates
**Priority**: P1 (Performance)
**Duration**: 4 hours
**Dependencies**: Task 1 (hypertable)

**Deliverables**:
1. `backend/db/schema/continuous_aggregates.sql` (200 lines)
   - 30-day rolling volatility
   - 60-day rolling volatility
   - 90-day rolling beta
   - 1-year Sharpe ratio

2. `backend/jobs/refresh_aggregates.py` (150 lines)
   - Refresh continuous aggregates (nightly)
   - Called after metrics computation

**Continuous Aggregate Example**:
```sql
-- 30-day rolling volatility
CREATE MATERIALIZED VIEW portfolio_metrics_30d_vol
WITH (timescaledb.continuous) AS
SELECT
    portfolio_id,
    time_bucket('1 day', asof_date) AS day,
    stddev(twr_1d) OVER (
        PARTITION BY portfolio_id
        ORDER BY asof_date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) * sqrt(252) AS volatility_30d
FROM portfolio_metrics
GROUP BY portfolio_id, asof_date, twr_1d;

-- Refresh policy: update every hour
SELECT add_continuous_aggregate_policy('portfolio_metrics_30d_vol',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

**Acceptance**:
- ✅ Continuous aggregates refresh nightly
- ✅ Query performance < 50ms (vs 500ms+ without)
- ✅ Rolling metrics accurate vs batch computation

---

### Task 5: Property Tests for Currency Identities
**Priority**: P1 (Quality Assurance)
**Duration**: 3 hours
**Dependencies**: Task 2 (currency attribution)

**Deliverables**:
1. `backend/tests/properties/test_currency_properties.py` (400 lines)
   - Property: `r_base = (1+r_local)(1+r_fx) - 1 ±0.1bp`
   - Property: FX triangulation (USD→CAD→EUR = USD→EUR)
   - Property: Identity currency (CAD→CAD = 0)
   - Property: Inverse rates (USD→CAD * CAD→USD = 1)

2. Use Hypothesis for property-based testing

**Property Tests**:
```python
from hypothesis import given, strategies as st
from decimal import Decimal

@given(
    r_local=st.decimals(min_value="-0.10", max_value="0.10", places=6),
    r_fx=st.decimals(min_value="-0.10", max_value="0.10", places=6),
)
def test_currency_attribution_identity(r_local, r_fx):
    """Property: r_base = (1+r_local)(1+r_fx) - 1"""
    r_base_identity = (1 + r_local) * (1 + r_fx) - 1
    r_base_decomposed = r_local + r_fx + r_local * r_fx

    error_bps = abs(r_base_identity - r_base_decomposed) * 10000
    assert error_bps < 0.1, f"Identity violated: {error_bps:.4f} bp"

@given(
    rate_usd_cad=st.decimals(min_value="1.0", max_value="2.0", places=4),
    rate_cad_eur=st.decimals(min_value="0.5", max_value="1.5", places=4),
)
def test_fx_triangulation(rate_usd_cad, rate_cad_eur):
    """Property: USD→CAD→EUR = USD→EUR (within tolerance)"""
    rate_usd_eur_direct = get_fx_rate("USD", "EUR")
    rate_usd_eur_via_cad = rate_usd_cad * rate_cad_eur

    error_bps = abs(rate_usd_eur_direct - rate_usd_eur_via_cad) / rate_usd_eur_direct * 10000
    assert error_bps < 1.0, f"Triangulation error: {error_bps:.4f} bp"
```

**Acceptance**:
- ✅ 1000+ property test cases pass
- ✅ No violations of currency identities
- ✅ FX triangulation holds ±1bp

---

## Parallel Execution Strategy

### Week 1 (Days 1-2): Foundation
**Day 1** (8 hours):
- Task 1: Database schema (3 hours)
- Task 2: Currency attribution (5 hours - start)

**Day 2** (8 hours):
- Task 2: Currency attribution (3 hours - finish)
- Task 3: Wire metrics to DB (5 hours - start)

### Week 2 (Days 3-4): Integration + Performance
**Day 3** (8 hours):
- Task 3: Wire metrics to DB (1 hour - finish)
- Task 4: TimescaleDB continuous aggregates (4 hours)
- Task 5: Property tests (3 hours)

**Day 4** (8 hours):
- Integration testing (4 hours)
- Performance tuning (2 hours)
- Documentation (2 hours)

**Day 5** (8 hours):
- Buffer for issues
- Acceptance gate validation
- Handoff documentation

**Total**: 40 hours over 5 days

---

## Critical Path Dependencies

```
Task 1 (Schema) ─┬─→ Task 2 (Currency Attribution)
                 │                    │
                 ├─→ Task 3 (Wire Metrics to DB)
                 │                    │
                 └─→ Task 4 (Continuous Aggregates)
                                      │
                                      ▼
                           Task 5 (Property Tests)
                                      │
                                      ▼
                            Integration Testing
```

---

## Acceptance Criteria (S2-W3 Gates)

From PRODUCT_SPEC Section 10:

| Criteria | Test | Target |
|----------|------|--------|
| TWR matches Beancount ±1bp | Reconciliation test | 100% portfolios |
| Currency attribution identity | Property test | ±0.1bp error |
| Continuous aggregates update | Integration test | Nightly refresh |

**Additional Validation**:
- ✅ Metrics stored with pricing_pack_id
- ✅ Multi-currency portfolios correct
- ✅ Query performance < 50ms (p95)

---

## Risk Mitigation

### Risk 1: Currency Attribution Complexity
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Start with 2-currency portfolio (USD/CAD)
- Add property tests early
- Validate against known examples

### Risk 2: TimescaleDB Setup
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- Use TimescaleDB Docker image for development
- Test continuous aggregates in isolation
- Have manual refresh as backup

### Risk 3: ±0.1bp Accuracy Requirement
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Use Decimal for all calculations (not float)
- Property tests with random inputs
- Validate rounding at each step

---

## Dependencies

### External Services
- PostgreSQL with TimescaleDB extension
- Pricing packs (from Phase 2)
- Ledger data (from Phase 1)

### Python Packages
```bash
# Already installed
asyncpg>=0.29.0
numpy>=1.24.0
scipy>=1.11.0

# New for Phase 3
hypothesis>=6.90.0  # Property-based testing
```

### Database Extensions
```sql
-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Verify
SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';
```

---

## Testing Strategy

### Unit Tests (Task-specific)
- Currency attribution calculations
- Metrics computation (TWR, MWR, Sharpe)
- Database queries (insert, select)

### Property Tests (Task 5)
- Currency identity: `(1+r_local)(1+r_fx)-1`
- FX triangulation
- Identity currency
- Inverse rates

### Integration Tests
- End-to-end: Nightly job → DB → Agent → UI
- Multi-currency portfolio flow
- Continuous aggregate refresh

### Performance Tests
- Metrics computation: < 1s per portfolio
- Query performance: < 50ms (p95)
- Continuous aggregate: < 5s refresh

---

## Monitoring

### Metrics to Track

**From backend/observability/metrics.py** (add):
```python
# Metrics computation
self.metrics_computation_duration = Histogram(
    f"{service_name}_metrics_computation_seconds",
    "Metrics computation duration",
    ["portfolio_id"],
)

self.attribution_error_bps = Histogram(
    f"{service_name}_attribution_error_bps",
    "Currency attribution error in basis points",
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

self.continuous_aggregate_refresh_duration = Histogram(
    f"{service_name}_continuous_aggregate_refresh_seconds",
    "Continuous aggregate refresh duration",
    ["aggregate_name"],
)
```

### Alerts
- Attribution error > 0.1bp (P1 alert)
- Metrics computation failure (P0 alert)
- Continuous aggregate refresh failure (P1 alert)

---

## Documentation Deliverables

1. **PHASE3_COMPLETE.md** - Summary of all tasks
2. **CURRENCY_ATTRIBUTION_GUIDE.md** - Deep dive on currency math
3. **TIMESCALEDB_SETUP.md** - Continuous aggregates guide
4. **PROPERTY_TESTING_GUIDE.md** - How to write property tests

---

## Success Criteria

**Velocity**: Complete in ≤40 hours (on-budget)

**Quality**:
- ✅ All acceptance criteria met
- ✅ TWR matches Beancount ±1bp
- ✅ Currency attribution ±0.1bp
- ✅ 1000+ property tests passing
- ✅ Continuous aggregates working

**Architecture**:
- ✅ Metrics stored with pricing_pack_id
- ✅ Multi-currency support complete
- ✅ Query performance < 50ms

---

## Next Actions

1. **Immediate**: Start Task 1 (Database schema)
2. **Day 1**: Complete schema + start currency attribution
3. **Day 2-3**: Finish currency attribution + wire metrics
4. **Day 4**: Continuous aggregates + property tests
5. **Day 5**: Integration testing + validation

---

**Status**: Ready to start Phase 3 implementation
**Estimated Start**: 2025-10-22 16:00 UTC
**Estimated Complete**: 2025-10-27 16:00 UTC (5 days)
