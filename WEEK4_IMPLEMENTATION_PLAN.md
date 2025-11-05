# Week 4 Implementation Plan: Pattern Updates & Testing

**Date:** November 5, 2025
**Planner:** Claude Code (Sonnet 4.5)
**Prerequisites:** Week 2 & 3 complete, validation fixes applied (commit 49ecc86)
**Status:** 📋 **READY TO EXECUTE**

---

## Executive Summary

Week 4 focuses on **completing the pattern optimization** started in Week 3 and **adding test coverage** for critical financial metrics fixes from Week 2.

### Goals

1. ✅ **Eliminate 50% of pattern duplication** by updating 8 patterns to use new abstraction
2. ✅ **Prevent regressions** by adding unit tests for TWR formula
3. ✅ **Verify MWR works** with integration test
4. ✅ **Ensure no performance degradation** with benchmarking

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Code Reduction** | -180 lines | Count steps before/after |
| **Test Coverage** | +15% | pytest --cov |
| **Performance** | No regression | p95 latency ±5% |
| **Pattern Success Rate** | 100% | All 8 patterns execute |

### Estimated Timeline

- **High Priority:** 5-8 hours (Tasks 1-3)
- **Medium Priority:** 6-9 hours (Tasks 4-5)
- **Low Priority:** 4-5 hours (Tasks 6-7)
- **Total:** 15-22 hours (~2-3 days)

---

## Task Breakdown

### HIGH PRIORITY (Must Complete)

---

### Task 1: Update 8 Patterns to Use `portfolio.get_valued_positions()`

**Priority:** P0 (Critical)
**Estimated Time:** 2-3 hours
**Complexity:** Low (simple find-replace)
**Dependencies:** None (abstraction already created)

#### Objective

Replace the 2-step "get positions + price them" sequence with single abstraction call in 8 patterns.

#### Patterns to Update

1. [portfolio_overview.json](backend/patterns/portfolio_overview.json)
2. [policy_rebalance.json](backend/patterns/policy_rebalance.json)
3. [portfolio_scenario_analysis.json](backend/patterns/portfolio_scenario_analysis.json)
4. [cycle_deleveraging_scenarios.json](backend/patterns/cycle_deleveraging_scenarios.json)
5. [news_impact_analysis.json](backend/patterns/news_impact_analysis.json)
6. [export_portfolio_report.json](backend/patterns/export_portfolio_report.json)
7. [portfolio_macro_overview.json](backend/patterns/portfolio_macro_overview.json)
8. [portfolio_cycle_risk.json](backend/patterns/portfolio_cycle_risk.json) *(if exists)*

#### Change Template

**BEFORE (2 steps, ~20 lines):**
```json
{
  "steps": [
    {
      "capability": "ledger.positions",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}"
      },
      "as": "positions"
    },
    {
      "capability": "pricing.apply_pack",
      "args": {
        "positions": "{{positions.positions}}",
        "pack_id": "{{ctx.pricing_pack_id}}"
      },
      "as": "valued"
    }
  ]
}
```

**AFTER (1 step, ~10 lines):**
```json
{
  "steps": [
    {
      "capability": "portfolio.get_valued_positions",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}"
      },
      "as": "valued"
    }
  ]
}
```

#### Implementation Steps

1. **Read each pattern file**
   ```bash
   cat backend/patterns/portfolio_overview.json
   ```

2. **Identify the sequence** (look for ledger.positions → pricing.apply_pack)

3. **Replace with abstraction** (use Edit tool)

4. **Verify JSON is valid**
   ```bash
   jq . backend/patterns/portfolio_overview.json > /dev/null
   echo $?  # Should be 0
   ```

5. **Test pattern execution** (if database available)
   ```bash
   curl -X POST http://localhost:8000/api/pattern/portfolio_overview \
     -H "Content-Type: application/json" \
     -d '{"portfolio_id": "test-uuid"}'
   ```

6. **Repeat for all 8 patterns**

#### Validation Criteria

- ✅ All 8 patterns updated
- ✅ JSON syntax valid (jq passes)
- ✅ Pattern execution succeeds (if DB available)
- ✅ Output matches previous behavior (same fields)
- ✅ Metadata preserved (`__metadata__` field present)

#### Expected Impact

- **Code Reduction:** 16 steps → 8 steps (50% reduction)
- **Lines Saved:** ~180 lines (8 patterns × ~22 lines each → 8 patterns × ~11 lines each)
- **Maintainability:** Single source of truth for position valuation logic
- **Future-Proof:** Easy to add caching, batch optimization, etc.

#### Rollback Plan

If issues found:
```bash
git diff backend/patterns/
git checkout backend/patterns/*.json  # Revert all
```

---

### Task 2: Add Unit Tests for TWR Formula

**Priority:** P0 (Critical - prevents regression)
**Estimated Time:** 2-3 hours
**Complexity:** Medium (need to mock database)
**Dependencies:** pytest, pytest-asyncio

#### Objective

Add comprehensive unit tests for Time-Weighted Return calculation to prevent regression of critical fix from Week 2.

#### Test File

**Location:** `backend/tests/test_metrics_twr.py`

#### Test Cases

**Test 1: Baseline (No Cash Flows)**
```python
async def test_twr_no_cash_flows():
    """Test TWR with no deposits/withdrawals."""
    values = [
        {"total_value": 100000, "cash_flows": 0},
        {"total_value": 110000, "cash_flows": 0},  # +10%
        {"total_value": 121000, "cash_flows": 0},  # +10%
    ]
    result = await compute_twr(values, start_date, end_date)

    assert abs(result["twr"] - 0.21) < 0.001  # 21% total
    assert result["error"] is None
```

**Test 2: Single Deposit Mid-Period**
```python
async def test_twr_with_deposit():
    """Test TWR correctly excludes deposit from return calculation."""
    values = [
        {"total_value": 100000, "cash_flows": 0},
        {"total_value": 120000, "cash_flows": 0},      # +20%
        {"total_value": 220000, "cash_flows": 100000}, # Deposit
        {"total_value": 198000, "cash_flows": 0},      # -10%
    ]
    result = await compute_twr(values, start_date, end_date)

    # TWR = (1.2 × 0.9) - 1 = +8%
    assert abs(result["twr"] - 0.08) < 0.001
    # MWR would be negative (investor lost money due to bad timing)
```

**Test 3: Single Withdrawal Mid-Period**
```python
async def test_twr_with_withdrawal():
    """Test TWR correctly handles withdrawals."""
    values = [
        {"total_value": 100000, "cash_flows": 0},
        {"total_value": 120000, "cash_flows": 0},       # +20%
        {"total_value": 20000, "cash_flows": -100000},  # Withdrawal
        {"total_value": 22000, "cash_flows": 0},        # +10%
    ]
    result = await compute_twr(values, start_date, end_date)

    # TWR = (1.2 × 1.1) - 1 = +32%
    assert abs(result["twr"] - 0.32) < 0.001
```

**Test 4: Multiple Cash Flows**
```python
async def test_twr_multiple_cash_flows():
    """Test TWR with frequent deposits/withdrawals."""
    values = [
        {"total_value": 100000, "cash_flows": 0},
        {"total_value": 105000, "cash_flows": 0},      # +5%
        {"total_value": 205000, "cash_flows": 100000}, # Deposit
        {"total_value": 215000, "cash_flows": 0},      # +4.88%
        {"total_value": 115000, "cash_flows": -100000},# Withdrawal
        {"total_value": 120000, "cash_flows": 0},      # +4.35%
    ]
    result = await compute_twr(values, start_date, end_date)

    # TWR = (1.05 × 1.0488 × 1.0435) - 1 ≈ +14.7%
    assert abs(result["twr"] - 0.147) < 0.005
```

**Test 5: Negative Returns**
```python
async def test_twr_negative_returns():
    """Test TWR with losses."""
    values = [
        {"total_value": 100000, "cash_flows": 0},
        {"total_value": 90000, "cash_flows": 0},  # -10%
        {"total_value": 81000, "cash_flows": 0},  # -10%
    ]
    result = await compute_twr(values, start_date, end_date)

    assert abs(result["twr"] - (-0.19)) < 0.001  # -19%
```

**Test 6: Edge Case - Zero Starting Value**
```python
async def test_twr_zero_starting_value():
    """Test TWR gracefully handles zero starting value."""
    values = [
        {"total_value": 0, "cash_flows": 0},
        {"total_value": 100000, "cash_flows": 100000},  # Initial deposit
        {"total_value": 110000, "cash_flows": 0},        # +10%
    ]
    result = await compute_twr(values, start_date, end_date)

    # Should skip first period (zero denominator)
    assert result["twr"] is not None
    assert result["error"] is None
```

**Test 7: Edge Case - All Zero Values**
```python
async def test_twr_all_zeros():
    """Test TWR with no portfolio value."""
    values = [
        {"total_value": 0, "cash_flows": 0},
        {"total_value": 0, "cash_flows": 0},
    ]
    result = await compute_twr(values, start_date, end_date)

    assert result["twr"] == 0.0
    assert "No valid returns" in result.get("error", "")
```

**Test 8: Volatility Calculation**
```python
async def test_volatility_uses_corrected_twr():
    """Verify volatility calculation uses corrected TWR returns."""
    values = [
        {"total_value": 100000, "cash_flows": 0},
        {"total_value": 120000, "cash_flows": 0},      # +20%
        {"total_value": 220000, "cash_flows": 100000}, # Deposit
        {"total_value": 198000, "cash_flows": 0},      # -10%
    ]
    result = await compute_twr(values, start_date, end_date)

    # Volatility should be based on [+0.20, -0.10] returns
    # std([0.2, -0.1]) = 0.15, annualized = 0.15 × √252 ≈ 2.38
    assert abs(result["vol"] - 2.38) < 0.1
```

**Test 9: Sharpe Ratio with Custom RF Rate**
```python
async def test_sharpe_custom_rf_rate(monkeypatch):
    """Test Sharpe ratio uses configurable risk-free rate."""
    monkeypatch.setenv("RISK_FREE_RATE", "0.03")

    values = [
        {"total_value": 100000, "cash_flows": 0},
        {"total_value": 115000, "cash_flows": 0},  # +15% annualized
    ]
    result = await compute_twr(values, start_date, end_date)

    # Sharpe = (0.15 - 0.03) / vol = 0.12 / vol
    assert result["sharpe"] > 0
    assert abs((result["ann_twr"] - 0.03) / result["vol"] - result["sharpe"]) < 0.01
```

#### Test Utilities

**Mock Database:**
```python
@pytest.fixture
async def mock_db():
    """Mock database connection pool."""
    # Return mock or use in-memory SQLite
    pass
```

**Compute TWR Helper:**
```python
async def compute_twr(values, start_date, end_date):
    """Helper to call PerformanceCalculator.compute_twr()."""
    from app.services.metrics import PerformanceCalculator
    calc = PerformanceCalculator(db=mock_db)
    return await calc.compute_twr(
        portfolio_id="test-uuid",
        pack_id="test-pack",
        lookback_days=(end_date - start_date).days
    )
```

#### Running Tests

```bash
cd backend
pytest tests/test_metrics_twr.py -v
pytest tests/test_metrics_twr.py --cov=app.services.metrics
```

#### Success Criteria

- ✅ All 9 tests pass
- ✅ Code coverage >80% for metrics.py TWR function
- ✅ No flaky tests (run 10 times, all pass)

---

### Task 3: Integration Test for MWR Capability

**Priority:** P0 (Critical - verify new capability works)
**Estimated Time:** 1-2 hours
**Complexity:** Medium
**Dependencies:** pytest, test database

#### Objective

Verify `metrics.compute_mwr` capability works end-to-end through the agent runtime and pattern orchestrator.

#### Test File

**Location:** `backend/tests/test_metrics_mwr_integration.py`

#### Test Cases

**Test 1: Capability Registration**
```python
async def test_mwr_capability_registered():
    """Verify metrics.compute_mwr is discoverable."""
    from app.agents.financial_analyst import FinancialAnalyst

    agent = FinancialAnalyst("financial_analyst", services={})
    capabilities = agent.get_capabilities()

    assert "metrics.compute_mwr" in capabilities
```

**Test 2: Direct Agent Call**
```python
async def test_mwr_direct_call():
    """Test calling metrics_compute_mwr() directly."""
    agent = FinancialAnalyst("financial_analyst", services)

    result = await agent.metrics_compute_mwr(
        ctx=mock_ctx,
        state={},
        portfolio_id="test-portfolio-id",
        pack_id="PP_2025-11-05"
    )

    assert "mwr" in result
    assert "ann_mwr" in result
    assert "__metadata__" in result
    assert result["__metadata__"]["capability"] == "metrics.compute_mwr"
```

**Test 3: Runtime Execution**
```python
async def test_mwr_via_runtime():
    """Test calling MWR through AgentRuntime."""
    from app.core.agent_runtime import AgentRuntime

    runtime = AgentRuntime(services)
    runtime.register_agent(FinancialAnalyst("financial_analyst", services))

    result = await runtime.execute_capability(
        "metrics.compute_mwr",
        ctx=mock_ctx,
        state={},
        portfolio_id="test-portfolio-id"
    )

    assert result is not None
    assert "mwr" in result
```

**Test 4: IRR Convergence**
```python
async def test_mwr_irr_converges():
    """Verify IRR solver converges for realistic scenarios."""
    # Test with portfolio that has:
    # - Initial investment: $100k
    # - Mid-year deposit: $50k
    # - Ending value: $160k

    result = await compute_mwr(portfolio_with_cash_flows)

    assert result["mwr"] is not None
    assert -1.0 < result["mwr"] < 1.0  # Reasonable IRR range
    assert "error" not in result
```

**Test 5: MWR vs TWR Divergence**
```python
async def test_mwr_twr_divergence():
    """Verify MWR and TWR differ when cash flow timing matters."""
    # Scenario: Deposit right before market drops
    # - Jan: $100k → $120k (+20%)
    # - Jul: Deposit $100k → $220k
    # - Dec: Market drops to $198k (-10%)

    twr_result = await compute_twr(portfolio)
    mwr_result = await compute_mwr(portfolio)

    # TWR = (1.2 × 0.9) - 1 = +8%
    assert abs(twr_result["twr"] - 0.08) < 0.01

    # MWR should be negative (bad timing)
    assert mwr_result["mwr"] < 0

    # They should diverge significantly
    assert abs(twr_result["twr"] - mwr_result["mwr"]) > 0.05
```

**Test 6: Error Handling**
```python
async def test_mwr_invalid_portfolio():
    """Test MWR gracefully handles invalid portfolio ID."""
    result = await agent.metrics_compute_mwr(
        ctx=mock_ctx,
        state={},
        portfolio_id="invalid-uuid"
    )

    assert "error" in result
    assert result["mwr"] == 0.0
```

#### Running Tests

```bash
pytest tests/test_metrics_mwr_integration.py -v
```

#### Success Criteria

- ✅ All 6 tests pass
- ✅ MWR calculation completes in <1 second
- ✅ Error cases handled gracefully

---

### MEDIUM PRIORITY (Should Complete)

---

### Task 4: Performance Benchmarking

**Priority:** P1 (Important - verify no regression)
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** pytest-benchmark or time module

#### Objective

Ensure the new `portfolio.get_valued_positions()` abstraction doesn't slow down pattern execution.

#### Benchmark Patterns

Focus on the 3 most commonly used patterns:
1. `portfolio_overview.json`
2. `policy_rebalance.json`
3. `portfolio_scenario_analysis.json`

#### Metrics to Track

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Pattern Execution Time** | ±5% | p95 latency |
| **Database Query Count** | No increase | SQL logging |
| **Memory Usage** | ±10% | tracemalloc |
| **Cache Hit Rate** | Same or better | Redis metrics |

#### Benchmark Script

**Location:** `backend/tests/benchmark_patterns.py`

```python
import asyncio
import time
from statistics import mean, median

async def benchmark_pattern(pattern_name, iterations=100):
    """Benchmark pattern execution time."""
    times = []

    for i in range(iterations):
        start = time.perf_counter()

        result = await orchestrator.execute_pattern(
            pattern_name=pattern_name,
            inputs={"portfolio_id": test_portfolio_id},
            ctx=test_ctx
        )

        end = time.perf_counter()
        times.append(end - start)

    return {
        "pattern": pattern_name,
        "iterations": iterations,
        "mean": mean(times),
        "median": median(times),
        "p95": sorted(times)[int(0.95 * iterations)],
        "p99": sorted(times)[int(0.99 * iterations)],
    }

# Run benchmarks
results_before = await benchmark_pattern("portfolio_overview", 100)
# ... update pattern ...
results_after = await benchmark_pattern("portfolio_overview", 100)

# Compare
pct_change = (results_after["p95"] - results_before["p95"]) / results_before["p95"] * 100
print(f"P95 latency change: {pct_change:+.1f}%")
assert abs(pct_change) < 5, "Performance regression detected"
```

#### Database Query Profiling

```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Count queries before/after
queries_before = count_queries_during_pattern_execution("portfolio_overview")
# ... update pattern ...
queries_after = count_queries_during_pattern_execution("portfolio_overview")

assert queries_after <= queries_before, "More queries after optimization!"
```

#### Memory Profiling

```python
import tracemalloc

tracemalloc.start()
await execute_pattern("portfolio_overview")
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"Current memory: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")
```

#### Expected Results

**Hypothesis:** Performance should be **same or better**

**Reasoning:**
- Same number of database queries (2 before → 2 after, just called from abstraction)
- Slightly less orchestrator overhead (1 capability call instead of 2)
- Memory usage should be identical

**If Performance Degrades:**
1. Profile with `cProfile` to find bottleneck
2. Check if abstraction adds unnecessary data copying
3. Consider adding caching to abstraction

#### Running Benchmarks

```bash
cd backend
python tests/benchmark_patterns.py
```

#### Success Criteria

- ✅ P95 latency within ±5% for all 3 patterns
- ✅ Database query count same or less
- ✅ Memory usage within ±10%

---

### Task 5: Add MWR to Portfolio Overview UI

**Priority:** P1 (Important - expose new metric to users)
**Estimated Time:** 4-6 hours
**Complexity:** High (requires UI changes)
**Dependencies:** UI framework (React/Next.js)

#### Objective

Display both TWR and MWR side-by-side in portfolio overview, explaining the difference to users.

#### UI Changes

**Location:** `dawsos-ui/src/app/portfolio/overview.tsx` or `full_ui.html`

#### Design Mockup

```
╔════════════════════════════════════════════════════════╗
║ Portfolio Performance                                  ║
║                                                        ║
║ Time-Weighted Return (TWR):   +8.0%  ℹ️               ║
║ └─ Measures manager skill independent of cash flows   ║
║                                                        ║
║ Money-Weighted Return (MWR):  -1.0%  ℹ️               ║
║ └─ Your actual return including cash flow timing      ║
║                                                        ║
║ ⚠️ Why are they different?                            ║
║ You deposited $100k right before market dropped 10%.  ║
║ The manager performed well (+8%), but your timing     ║
║ resulted in a loss (-1%).                             ║
║                                                        ║
║ [Learn More About TWR vs MWR]                         ║
╚════════════════════════════════════════════════════════╝
```

#### Backend Changes

**File:** `backend/app/api/routes.py` (or wherever `/api/portfolio/overview` is defined)

```python
@router.get("/portfolio/{portfolio_id}/overview")
async def get_portfolio_overview(portfolio_id: str):
    # Existing TWR call
    twr_result = await runtime.execute_capability(
        "metrics.compute_twr",
        ctx=ctx,
        state={},
        portfolio_id=portfolio_id
    )

    # NEW: MWR call
    mwr_result = await runtime.execute_capability(
        "metrics.compute_mwr",
        ctx=ctx,
        state={},
        portfolio_id=portfolio_id
    )

    return {
        "twr": twr_result.get("twr"),
        "mwr": mwr_result.get("mwr"),  # NEW
        "twr_annualized": twr_result.get("ann_twr"),
        "mwr_annualized": mwr_result.get("ann_mwr"),  # NEW
        # ... other fields ...
    }
```

#### Frontend Changes

**File:** `dawsos-ui/src/components/PerformanceMetrics.tsx`

```typescript
interface PerformanceMetricsProps {
  twr: number;
  mwr: number;
  showExplanation?: boolean;
}

export function PerformanceMetrics({ twr, mwr, showExplanation = true }: PerformanceMetricsProps) {
  const divergence = Math.abs(twr - mwr);
  const showWarning = divergence > 0.05; // More than 5% difference

  return (
    <div className="performance-metrics">
      <MetricRow
        label="Time-Weighted Return (TWR)"
        value={formatPercent(twr)}
        tooltip="Measures portfolio manager performance independent of cash flow timing"
        icon="📊"
      />

      <MetricRow
        label="Money-Weighted Return (MWR)"
        value={formatPercent(mwr)}
        tooltip="Your actual return including the impact of deposit/withdrawal timing"
        icon="💰"
      />

      {showWarning && showExplanation && (
        <Alert variant="info">
          <p>Your TWR ({formatPercent(twr)}) differs from MWR ({formatPercent(mwr)}) by {formatPercent(divergence)}.</p>
          <p>This suggests the timing of your deposits/withdrawals significantly impacted your returns.</p>
          <Link href="/learn/twr-vs-mwr">Learn More</Link>
        </Alert>
      )}
    </div>
  );
}
```

#### Documentation Page

**File:** `docs/learn/twr-vs-mwr.md`

```markdown
# Understanding TWR vs MWR

## What's the Difference?

**Time-Weighted Return (TWR)** measures how well your portfolio *manager* performed, independent of when you added or withdrew money.

**Money-Weighted Return (MWR)** measures *your actual experience* as an investor, accounting for the timing and size of your cash flows.

## Example

Imagine this scenario:

| Date | Event | Portfolio Value |
|------|-------|-----------------|
| Jan 1 | Start with $100k | $100,000 |
| Jun 30 | Market up 20% | $120,000 |
| Jul 1 | You deposit $100k | $220,000 |
| Dec 31 | Market down 10% | $198,000 |

**TWR:** (1.2 × 0.9) - 1 = **+8.0%**
- Your manager did well! The portfolio beat the market.

**MWR:** **-1.0%** (IRR)
- You lost money because you deposited right before the drop.

## When to Use Each

- **TWR:** Comparing fund managers, evaluating strategy performance
- **MWR:** Understanding your actual returns, tax planning

## Why DawsOS Shows Both

Most platforms only show one metric. We show both because:
1. **Transparency:** You deserve to see both perspectives
2. **Learning:** Large divergence signals you should rethink deposit timing
3. **Accountability:** Separates manager skill from investor behavior

[Back to Portfolio Overview](/portfolio)
```

#### Testing

1. **Unit Test:** Verify API returns both TWR and MWR
2. **Integration Test:** End-to-end from DB → API → UI
3. **Visual Test:** Screenshot comparison before/after
4. **Accessibility Test:** Screen reader reads both metrics

#### Success Criteria

- ✅ Both TWR and MWR displayed in UI
- ✅ Tooltip explains each metric
- ✅ Warning shown when divergence >5%
- ✅ "Learn More" link works
- ✅ Passes accessibility audit (WCAG 2.1 AA)

---

### LOW PRIORITY (Nice to Have)

---

### Task 6: Make Risk-Free Rate Dynamic

**Priority:** P2 (Enhancement)
**Estimated Time:** 3-4 hours
**Complexity:** Medium
**Dependencies:** FRED API or equivalent

#### Objective

Replace hardcoded risk-free rate with dynamic query from Federal Reserve Economic Data (FRED).

#### Implementation

**File:** `backend/app/services/metrics.py`

**Current Code:**
```python
rf_rate = float(os.getenv("RISK_FREE_RATE", "0.04"))  # Static
```

**Target Code:**
```python
async def get_risk_free_rate(self, cache_ttl=86400):
    """
    Get current risk-free rate from FRED (3-month T-bill).

    Caches for 24 hours to avoid excessive API calls.
    Falls back to environment variable if FRED unavailable.
    """
    cache_key = "risk_free_rate:fred:3m_tbill"

    # Check cache
    cached = await self.redis.get(cache_key)
    if cached:
        return float(cached)

    try:
        # Query FRED for 3-month T-bill rate
        from app.integrations.fred_provider import FREDProvider
        fred = FREDProvider()

        rate = await fred.get_series_latest("DGS3MO")  # 3-Month Treasury
        rate_decimal = float(rate) / 100  # Convert from percent to decimal

        # Cache for 24 hours
        await self.redis.setex(cache_key, cache_ttl, str(rate_decimal))

        return rate_decimal

    except Exception as e:
        logger.warning(f"Failed to fetch risk-free rate from FRED: {e}")
        # Fall back to environment variable
        return float(os.getenv("RISK_FREE_RATE", "0.04"))
```

**Usage in Sharpe Calculation:**
```python
# Sharpe ratio
rf_rate = await self.get_risk_free_rate()
sharpe = (ann_twr - rf_rate) / vol if vol > 0 else 0.0
```

#### FRED Provider Setup

**File:** `backend/app/integrations/fred_provider.py`

```python
import httpx
from typing import Optional

class FREDProvider:
    """Provider for Federal Reserve Economic Data (FRED)."""

    def __init__(self):
        self.api_key = os.getenv("FRED_API_KEY")
        self.base_url = "https://api.stlouisfed.org/fred"

    async def get_series_latest(self, series_id: str) -> Optional[float]:
        """
        Get latest value for a FRED series.

        Args:
            series_id: FRED series ID (e.g., "DGS3MO" for 3-month T-bill)

        Returns:
            Latest value as float, or None if unavailable
        """
        if not self.api_key:
            raise ValueError("FRED_API_KEY not set in environment")

        url = f"{self.base_url}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data["observations"]:
                return float(data["observations"][0]["value"])
            else:
                return None
```

#### Configuration

**File:** `.env`

```bash
# FRED API Key (get from https://fred.stlouisfed.org/docs/api/api_key.html)
FRED_API_KEY=your_api_key_here

# Fallback risk-free rate (used if FRED unavailable)
RISK_FREE_RATE=0.04
```

#### Testing

```python
async def test_dynamic_risk_free_rate():
    """Test risk-free rate fetched from FRED."""
    calc = PerformanceCalculator(db=mock_db)

    rate = await calc.get_risk_free_rate()

    assert rate is not None
    assert 0.0 <= rate <= 0.10  # Reasonable range (0-10%)

    # Test caching
    rate2 = await calc.get_risk_free_rate()
    assert rate == rate2  # Should be cached
```

#### Success Criteria

- ✅ Risk-free rate queried from FRED daily
- ✅ Cached for 24 hours to avoid API rate limits
- ✅ Falls back to environment variable if FRED unavailable
- ✅ Sharpe ratio uses current risk-free rate

---

### Task 7: Archive Orphaned Patterns

**Priority:** P2 (Cleanup)
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** None

#### Objective

Identify and archive patterns that are no longer used to reduce codebase clutter.

#### Suspected Orphans

From [PATTERN_SYSTEM_ANALYSIS.md](PATTERN_SYSTEM_ANALYSIS.md):

1. `corporate_actions_upcoming.json` - No caller found
2. `news_impact_analysis.json` - Prototype, not production-ready
3. `cycle_deleveraging_scenarios.json` - Potentially duplicate of `portfolio_scenario_analysis.json`

#### Validation Process

**Step 1: Grep for Usage**
```bash
cd /Users/mdawson/Documents/GitHub/DawsOSP

# Check if pattern is called anywhere
grep -r "corporate_actions_upcoming" backend/
grep -r "news_impact_analysis" backend/
grep -r "cycle_deleveraging_scenarios" backend/

# Check API routes
grep -r "/api/pattern/" backend/app/api/
```

**Step 2: Check API Endpoints**
```bash
# List all pattern routes
grep -E "@router\.(get|post).*pattern" backend/app/api/routes.py
```

**Step 3: Check UI References**
```bash
# Check if UI calls these patterns
grep -r "corporate_actions" dawsos-ui/
grep -r "news_impact" dawsos-ui/
```

#### Archiving Process

**If no references found:**

```bash
# Create archive directory
mkdir -p .archive/patterns-orphaned-20251105/

# Move pattern files
git mv backend/patterns/corporate_actions_upcoming.json \
  .archive/patterns-orphaned-20251105/

# Create README explaining why archived
cat > .archive/patterns-orphaned-20251105/README.md <<EOF
# Archived Patterns (November 5, 2025)

These patterns were archived because no active code references them.

## corporate_actions_upcoming.json
- **Reason:** No API routes or UI components reference this pattern
- **Last Modified:** October 28, 2025
- **Can Restore If:** Corporate actions feature is added in future

## news_impact_analysis.json
- **Reason:** Prototype that was never integrated into production
- **Last Modified:** October 25, 2025
- **Can Restore If:** News analysis feature is prioritized

## cycle_deleveraging_scenarios.json
- **Reason:** Duplicate of portfolio_scenario_analysis.json
- **Last Modified:** October 29, 2025
- **Can Restore If:** Need separate deleveraging-specific workflow
EOF

# Commit
git add .archive/patterns-orphaned-20251105/
git commit -m "Archive orphaned patterns (no active references found)"
```

#### Success Criteria

- ✅ All orphaned patterns identified
- ✅ No breaking changes (no code references them)
- ✅ Patterns moved to `.archive/` with documentation
- ✅ Git history preserved (use `git mv`, not `rm`)

---

## Execution Order

### Day 1 (High Priority)
1. ☐ Task 1: Update 8 patterns (2-3 hours)
2. ☐ Task 2: Add TWR unit tests (2-3 hours)

### Day 2 (High + Medium Priority)
3. ☐ Task 3: MWR integration test (1-2 hours)
4. ☐ Task 4: Performance benchmarking (2-3 hours)

### Day 3 (Medium + Low Priority)
5. ☐ Task 5: Add MWR to UI (4-6 hours)
6. ☐ Task 6: Dynamic risk-free rate (3-4 hours) *optional*
7. ☐ Task 7: Archive orphaned patterns (1 hour)

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Pattern update breaks functionality** | Medium | High | Test each pattern after update, rollback plan |
| **Performance regression** | Low | Medium | Benchmark before/after, profile if needed |
| **MWR IRR doesn't converge** | Low | Low | Add timeout, fall back to error state |
| **UI changes break layout** | Low | Medium | Visual regression tests, responsive testing |
| **FRED API rate limits** | Low | Low | Cache for 24 hours, fall back to env var |

---

## Success Metrics

### Code Quality
- ✅ **-180 lines** of duplicate code (50% reduction in pattern steps)
- ✅ **+15% test coverage** for metrics module
- ✅ **0 compilation errors**
- ✅ **0 breaking changes**

### Performance
- ✅ **P95 latency** within ±5% for all patterns
- ✅ **Database queries** same or fewer
- ✅ **Memory usage** within ±10%

### Features
- ✅ **MWR exposed** in API and UI
- ✅ **TWR formula** has comprehensive unit tests
- ✅ **8 patterns** using new abstraction

### Documentation
- ✅ **Validation report** created
- ✅ **Implementation plan** created (this document)
- ✅ **User docs** for TWR vs MWR

---

## Completion Criteria

**Week 4 is COMPLETE when:**
1. ✅ All 8 patterns updated and tested
2. ✅ TWR unit tests added (9 test cases)
3. ✅ MWR integration test passes
4. ✅ Performance benchmarks show no regression
5. ✅ All tests passing (`pytest --cov`)
6. ✅ Code committed and documented

**Optional (for full credit):**
7. ⚠️ MWR visible in UI
8. ⚠️ Dynamic risk-free rate implemented
9. ⚠️ Orphaned patterns archived

---

## Related Documentation

- [IMPLEMENTATION_SUMMARY_WEEK2_WEEK3.md](IMPLEMENTATION_SUMMARY_WEEK2_WEEK3.md) - Week 2 & 3 summary
- [WEEK2_WEEK3_VALIDATION_REPORT.md](WEEK2_WEEK3_VALIDATION_REPORT.md) - Validation findings
- [PATTERN_SYSTEM_ANALYSIS.md](PATTERN_SYSTEM_ANALYSIS.md) - Pattern architecture review
- [METRICS_VALIDATION_REPORT.md](METRICS_VALIDATION_REPORT.md) - Financial metrics analysis

---

**Created:** November 5, 2025
**Status:** 📋 **READY TO EXECUTE**
**Next Action:** Begin Task 1 (Update 8 patterns)
