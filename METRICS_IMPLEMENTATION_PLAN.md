
# Metrics Implementation & Technical Debt Elimination Plan

## Executive Summary

This plan addresses the missing portfolio metrics infrastructure (TWR/MWR/Historical NAV) by implementing the proper data pipeline while eliminating technical debt and anti-patterns.

## Current State Analysis

### ✅ What EXISTS:
1. **`transactions` table** - Has trade history from Beancount ledger
2. **`portfolio_metrics` table** - Schema exists but **EMPTY** (no data)
3. **Metrics computation code** - Exists in `backend/jobs/metrics.py`
4. **Currency attribution** - Exists in `backend/app/services/currency_attribution.py`

### ❌ What's MISSING:
1. **`portfolio_daily_values` table** - Referenced but never created
2. **`portfolio_cash_flows` table** - Referenced in MWR calculation but doesn't exist
3. **Daily job to populate metrics** - No scheduled process running metrics computation
4. **Transaction-to-metrics pipeline** - Code expects pre-computed values, not raw transactions

## Root Cause

The architecture has **TWO APPROACHES** conflicting:

### Approach A (Designed but not implemented):
```
Transactions → Daily Job → portfolio_daily_values → Metrics Computation → portfolio_metrics
```

### Approach B (Currently attempted):
```
Transactions → ??? → portfolio_metrics (directly)
```

**The missing link**: No process converts transactions into daily portfolio values.

## Implementation Plan (Proper Fix)

### Phase 0: UI Transaction Integration (Week 0)
**Priority: P0 - Critical UI Bug**

#### Problem Identified
The diagnosis revealed that:
- UI calls `/api/transactions` which returns **mock/stub data**
- Real transactions exist in database via `/v1/trades` endpoint
- **Gap**: UI is not connected to the real transaction API

#### 0.1 Fix Transaction Endpoint
- **File**: `combined_server.py`
- **Current Issue**: `/api/transactions` endpoint returns hardcoded mock data (Line ~1772)
- **Action**: Redirect to real trades endpoint or integrate with `/v1/trades`

**Option 1: Update `/api/transactions` to call real data**
```python
@app.get("/api/transactions")
async def get_transactions(
    portfolio_id: str = Query(...),
    claims: dict = Depends(verify_token)
):
    """Get transaction history from database"""
    from backend.app.api.routes.trades import list_trades
    from uuid import UUID
    
    return await list_trades(
        portfolio_id=UUID(portfolio_id),
        claims=claims
    )
```

**Option 2: Update UI to call `/v1/trades` directly**
- **File**: `full_ui.html`
- **Line**: ~2500 (transaction fetch logic)
- **Change**: Update fetch URL from `/api/transactions` to `/v1/trades?portfolio_id=${portfolioId}`
- **Format**: Ensure response format matches UI expectations

#### 0.2 Verify Transaction Display
- [ ] Test UI displays real transactions from seed data
- [ ] Verify transaction types (BUY, SELL, DIVIDEND) render correctly
- [ ] Confirm dates, quantities, prices display accurately
- [ ] Validate transaction history matches database `transactions` table
- [ ] Remove any mock data fallbacks

#### 0.3 Update Transaction Schema Mapping
- **Issue**: UI expects specific transaction object structure
- **Required Fields**: date, type, symbol, quantity, price, amount, realized_gain
- **Action**: Ensure `/v1/trades` response matches UI expectations or add transformation layer

#### Success Criteria
- [ ] UI Transaction tab shows real database transactions
- [ ] No mock/stub data returned by `/api/transactions`
- [ ] Transaction list matches seed data from `seed_portfolio_data.sql`
- [ ] All transaction types display correctly

---

### Phase 1: Database Schema Creation
**Priority: P0 - Blocking all metrics**

#### 1.1 Create `portfolio_daily_values` Hypertable
- **File**: `backend/db/schema/portfolio_daily_values.sql` (NEW)
- **Purpose**: Store daily NAV, cash flows, position values
- **Columns**:
  - `portfolio_id UUID`
  - `valuation_date DATE` (hypertable partition key)
  - `total_value NUMERIC(20,2)`
  - `cash_balance NUMERIC(20,2)`
  - `positions_value NUMERIC(20,2)`
  - `cash_flows NUMERIC(20,2)` (dividends, deposits, withdrawals)
  - `currency VARCHAR(3)`
  - `computed_at TIMESTAMPTZ`
- **Indexes**: Composite on (portfolio_id, valuation_date)
- **Hypertable**: Partition by valuation_date (monthly chunks)

#### 1.2 Create `portfolio_cash_flows` Table
- **File**: `backend/db/schema/portfolio_cash_flows.sql` (NEW)
- **Purpose**: Track all portfolio cash movements for MWR
- **Columns**:
  - `id UUID PRIMARY KEY`
  - `portfolio_id UUID`
  - `flow_date DATE`
  - `flow_type VARCHAR(20)` (DEPOSIT, WITHDRAWAL, DIVIDEND, INTEREST)
  - `amount NUMERIC(20,2)`
  - `currency VARCHAR(3)`
  - `transaction_id UUID` (FK to transactions)
  - `created_at TIMESTAMPTZ`
- **Indexes**: (portfolio_id, flow_date)

#### 1.3 Create Continuous Aggregates (TimescaleDB)
- **File**: `backend/db/schema/continuous_aggregates.sql` (ENHANCE)
- **Aggregates**:
  - `portfolio_monthly_returns` (pre-compute monthly TWR)
  - `portfolio_rolling_volatility` (30/90/252 day windows)
  - `portfolio_drawdowns` (running max drawdown)

### Phase 2: Data Pipeline Implementation
**Priority: P0 - Required for metrics**

#### 2.1 Transaction Aggregator Job
- **File**: `backend/jobs/daily_valuation.py` (NEW)
- **Responsibility**: Aggregate transactions into daily values
- **Process**:
  1. Query all portfolios
  2. For each portfolio, for each day since inception:
     - Sum position values (from lots × prices)
     - Sum cash flows (dividends, deposits, withdrawals)
     - Calculate total NAV
     - Insert into `portfolio_daily_values`
  3. Extract cash flows → `portfolio_cash_flows`
- **Schedule**: Daily at 00:00 UTC (after pricing pack creation)
- **Backfill**: Initial run populates historical data

#### 2.2 Metrics Computation Job Enhancement
- **File**: `backend/jobs/metrics.py` (REFACTOR)
- **Current Issue**: Tries to read from empty `portfolio_metrics`
- **Fix**: 
  1. Read from `portfolio_daily_values` (not metrics table)
  2. Compute TWR using daily NAV series
  3. Compute MWR using cash flows + NAV
  4. Store results in `portfolio_metrics`
- **Dependencies**: Must run AFTER `daily_valuation.py`

#### 2.3 Historical NAV Service Fix
- **File**: `backend/app/agents/financial_analyst.py` (FIX)
- **Current Code** (Line ~1180):
  ```python
  SELECT valuation_date, total_value, cash_flows
  FROM portfolio_daily_values  # ← Table doesn't exist
  ```
- **Fix**: Keep query, create table (Phase 1.1)
- **Remove**: Simulated NAV fallback logic (Lines ~1184-1195)

### Phase 3: Technical Debt Elimination
**Priority: P1 - Cleanup alongside implementation**

#### 3.1 Remove Dead Code
**Files to Clean**:

1. **`backend/app/agents/financial_analyst.py`**
   - Remove: `_generate_simulated_nav()` (Lines ~1184-1195)
   - Remove: Fallback logic for missing metrics
   - Reason: Once tables exist, simulations are anti-pattern

2. **`backend/jobs/metrics.py`**
   - Remove: `MetricsComputer._stub_metrics()` method
   - Remove: Fallback to empty metrics
   - Reason: Should fail loudly if data missing

3. **`backend/app/services/metrics.py`**
   - Refactor: `PerformanceCalculator.compute_twr()`
   - Current: Expects `portfolio_daily_values` to exist
   - Change: Add error handling, not simulation
   - Reason: Silent failures hide broken pipelines

#### 3.2 Consolidate Metrics Queries
**Problem**: Metrics queries scattered across 3 files
- `backend/app/db/metrics_queries.py`
- `backend/app/services/metrics.py`
- `backend/jobs/metrics.py`

**Fix**: Single source of truth
- **Keep**: `backend/app/db/metrics_queries.py` (DB access layer)
- **Refactor**: `backend/jobs/metrics.py` uses `metrics_queries.py`
- **Refactor**: `backend/app/services/metrics.py` uses `metrics_queries.py`
- **Delete**: Duplicate SQL in jobs/services

#### 3.3 Remove Simulation/Stub Patterns
**Anti-Pattern Locations**:

1. **Portfolio Overview Pattern**
   - File: `backend/patterns/portfolio_overview.json`
   - Current: Has `fallback` for missing metrics
   - Fix: Remove fallbacks, require real data
   - Migration: Show "Computing metrics..." UI state

2. **Historical NAV**
   - Current: Generates random walk simulation
   - Fix: Return error if `portfolio_daily_values` empty
   - UI: Show "No historical data" message

3. **Currency Attribution**
   - File: `backend/app/services/currency_attribution.py`
   - Current: Returns zeros if no pricing pack (Line ~32-35)
   - Fix: Raise error if required data missing
   - Reason: Silent zeros hide data gaps

### Phase 4: Job Scheduling & Orchestration
**Priority: P1 - Make it run automatically**

#### 4.1 Update Job Scheduler
- **File**: `backend/jobs/scheduler.py` (ENHANCE)
- **Add Jobs**:
  1. `daily_valuation.py` - 00:00 UTC daily
  2. `metrics.py` - 00:30 UTC daily (after valuation)
  3. `currency_attribution.py` - 01:00 UTC daily
- **Dependencies**: Valuation → Metrics → Attribution (sequential)

#### 4.2 Add Health Checks
- **File**: `backend/jobs/metrics.py` (ENHANCE)
- **Add**: Data quality checks
  - NAV ≈ Sum(positions) + cash (±1bp tolerance)
  - Cash flows sum to transaction history
  - No missing days in time series
- **Action**: Alert if reconciliation fails

### Phase 5: Data Backfill & Migration
**Priority: P1 - Populate historical data**

#### 5.1 Backfill Script
- **File**: `backend/jobs/backfill_daily_values.py` (NEW)
- **Process**:
  1. Find portfolio inception date (earliest transaction)
  2. For each day from inception → today:
     - Reconstruct NAV from transactions + prices
     - Calculate cash flows
     - Insert into `portfolio_daily_values`
  3. Validate: Final NAV matches current ledger
- **Run Once**: Before enabling daily jobs

#### 5.2 Metrics Recomputation
- **File**: `backend/jobs/metrics.py`
- **After Backfill**: Run `compute_all_metrics()`
- **Result**: `portfolio_metrics` table populated with real data
- **Validation**: Compare with Beancount ledger returns (±5bp)

## Testing Strategy

### Unit Tests (Add)
1. **`tests/unit/test_daily_valuation.py`** (NEW)
   - Test NAV calculation from transactions
   - Test cash flow extraction
   - Test missing price handling

2. **`tests/unit/test_metrics_computation.py`** (ENHANCE)
   - Test TWR calculation (known series)
   - Test MWR calculation (known cash flows)
   - Test edge cases (single day, no flows)

### Integration Tests (Add)
1. **`tests/integration/test_metrics_pipeline.py`** (NEW)
   - End-to-end: Transactions → Daily Values → Metrics
   - Validate against Beancount
   - Test reconciliation tolerance

### Golden Tests (Add)
1. **`tests/golden/metrics/`** (NEW)
   - Store known-good portfolio history
   - Regression test metrics computation
   - Alert if results drift >1bp

## Rollout Plan

### Week 0: UI Transaction Fix (NEW - CRITICAL)
- [ ] Day 1: Update `/api/transactions` endpoint or UI fetch calls (Phase 0.1)
- [ ] Day 2: Test transaction display with seed data (Phase 0.2)
- [ ] Day 3: Verify all transaction types render correctly (Phase 0.3)
- [ ] **Deliverable**: UI displays real transactions from database

### Week 1: Schema & Pipeline
- [ ] Day 1-2: Create database tables (Phase 1)
- [ ] Day 3-4: Implement `daily_valuation.py` (Phase 2.1)
- [ ] Day 5: Write unit tests

### Week 2: Metrics & Backfill
- [ ] Day 1-2: Refactor `metrics.py` (Phase 2.2)
- [ ] Day 3: Fix `historical_nav` service (Phase 2.3)
- [ ] Day 4-5: Run backfill script (Phase 5.1)

### Week 3: Cleanup & Testing
- [ ] Day 1-2: Remove dead code (Phase 3.1-3.3)
- [ ] Day 3: Add job scheduling (Phase 4.1-4.2)
- [ ] Day 4-5: Integration tests (Phase 5.2)

### Week 4: Validation & Monitoring
- [ ] Day 1-2: Compare metrics vs Beancount ledger
- [ ] Day 3: Set up monitoring/alerts
- [ ] Day 4: Update documentation
- [ ] Day 5: Deploy to production

## Success Criteria

### Functional
- [ ] `portfolio_daily_values` table populated (no gaps)
- [ ] `portfolio_metrics` table has real TWR/MWR (not empty)
- [ ] Historical NAV chart shows real data (not simulation)
- [ ] Metrics reconcile with Beancount ledger (±5bp)

### Technical Debt
- [ ] Zero simulation/stub code in production paths
- [ ] All metrics queries use single DB access layer
- [ ] No silent failures (errors raised loudly)
- [ ] Continuous aggregates precompute rolling metrics

### Operational
- [ ] Daily jobs run automatically (scheduler)
- [ ] Health checks alert on reconciliation failures
- [ ] Monitoring dashboard shows pipeline status
- [ ] Documentation updated (developer + user)

## Risk Mitigation

### Risk 1: Backfill Takes Too Long
- **Mitigation**: Batch processing (1000 days at a time)
- **Fallback**: Backfill last 90 days first, rest async

### Risk 2: Metrics Don't Match Beancount
- **Mitigation**: Reconciliation job with detailed logging
- **Action**: Flag discrepancies >5bp for manual review

### Risk 3: Missing Pricing Data
- **Mitigation**: Interpolate missing prices (carry forward)
- **Alert**: Log warning for interpolated values

### Risk 4: Breaking Existing UI
- **Mitigation**: Feature flag new metrics, keep stubs temporarily
- **Rollback**: Revert to simulated data if pipeline fails

## Appendix: File Change Summary

### New Files (7)
1. `backend/db/schema/portfolio_daily_values.sql`
2. `backend/db/schema/portfolio_cash_flows.sql`
3. `backend/jobs/daily_valuation.py`
4. `backend/jobs/backfill_daily_values.py`
5. `tests/unit/test_daily_valuation.py`
6. `tests/integration/test_metrics_pipeline.py`
7. `tests/golden/metrics/portfolio_returns.json`

### Modified Files (9)
1. **`combined_server.py`** (Phase 0: Fix `/api/transactions` endpoint OR Phase 1: initialize new tables)
2. **`full_ui.html`** (Phase 0: Update transaction fetch URL if using Option 2)
3. `backend/jobs/metrics.py` (refactor to use daily_values)
4. `backend/jobs/scheduler.py` (add new jobs)
5. `backend/app/agents/financial_analyst.py` (remove simulation)
6. `backend/app/services/metrics.py` (use metrics_queries)
7. `backend/app/db/metrics_queries.py` (add daily_values queries)
8. `backend/patterns/portfolio_overview.json` (remove fallbacks)
9. `backend/db/schema/continuous_aggregates.sql` (add new aggregates)

### Deleted Code (~500 lines)
- All simulation/stub methods
- Duplicate SQL queries
- Fallback logic for missing data

## Notes

- **Phase 0 is Critical**: Must fix UI transaction display before building metrics pipeline
- **TimescaleDB Required**: Hypertables for efficient time-series storage
- **PostgreSQL Version**: Requires 12+ for generated columns
- **Python Version**: 3.9+ for asyncpg compatibility
- **Migration**: Zero downtime (tables created, jobs enabled after backfill)
- **Transaction Data**: Already exists in database from seed data and trade execution
- **UI-Backend Gap**: Transactions exist but UI shows mock data (Phase 0 fixes this)

---

**Plan Version**: 1.1  
**Created**: 2025-10-31  
**Updated**: 2025-10-31 (Added Phase 0 for UI Transaction Integration)  
**Status**: Ready for Implementation
