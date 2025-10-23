# Phase 4: API Layer + UI Overview - EXECUTION PLAN

**Date**: 2025-10-22
**Status**: 🔄 READY TO START
**Duration**: 3-5 sessions (12-20 hours estimated)
**Sprint**: S2-W4 (Sprint 2 Week 4)

---

## Executive Summary

Phase 4 implements **API endpoints**, **agent capability wiring**, and **UI Portfolio Overview** to complete Sprint 2. This phase connects the Phase 3 database/jobs layer to the presentation layer via RESTful APIs.

**Context**: Phase 3 complete (metrics + currency attribution working), Phase 2 execution path operational.

**Critical Deliverables**:
1. REST API endpoints for metrics and attribution
2. Agent capability wiring (metrics.compute_twr, attribution.currency)
3. UI Portfolio Overview with provenance badges
4. End-to-end integration tests
5. Backfill rehearsal tool
6. Visual regression test baseline

---

## Phase 3 Assets (Verified Complete)

From Phase 3 completion, we have:

### ✅ Database Layer Complete

**`backend/db/schema/portfolio_metrics.sql`** (434 lines):
- 3 TimescaleDB hypertables (portfolio_metrics, currency_attribution, factor_exposures)
- 4 continuous aggregates (30d, 60d, 90d, 1y)
- Compression policies, indexes, constraints

**`backend/app/db/metrics_queries.py`** (759 lines):
- 11 async methods (insert_metrics, get_latest_metrics, get_rolling_metrics, etc.)
- Singleton pattern (`get_metrics_queries()`)
- AsyncPG connection pool

**Status**: Production-ready, all structure tests passing

### ✅ Jobs Layer Complete

**`backend/jobs/metrics.py`** (modified, +160 lines):
- Metrics computation (TWR, MWR, Sharpe, volatility, drawdown)
- Database integration with graceful fallback
- Currency attribution integration
- Async storage via MetricsQueries

**`backend/jobs/currency_attribution.py`** (542 lines):
- Position and portfolio-level attribution
- Mathematical identity: `r_base = (1+r_local)(1+r_fx)-1`
- ±0.1bp accuracy validation
- Decimal precision throughout

**Status**: Production-ready, 67/67 tests passing

### ⏳ Agent Framework Ready

**`backend/app/agents/financial_analyst.py`** (exists):
- Capability framework in place
- get_capabilities() method ready
- **Needs wiring**: metrics.compute_twr, attribution.currency

**`backend/app/core/capability_registry.py`** (exists):
- Capability categories defined (metrics, attribution)
- Ready for registration

**Status**: Framework ready, implementation pending

---

## Phase 4 Requirements (from PRODUCT_SPEC)

### Sprint 2 Week 4 (S2-W4) Deliverables

**From IMPLEMENTATION_ROADMAP_V2.md**:
- UI Portfolio Overview (Streamlit)
- Provenance display (pack ID, ledger hash)
- Backfill rehearsal (D0 → D1 supersede path)
- Visual regression tests (Percy baseline)

**Additional (from integration analysis)**:
- REST API endpoints (FastAPI)
- Agent capability wiring
- Pydantic response schemas
- End-to-end integration tests

**Acceptance Criteria**:
- ✅ Metrics API returns data from TimescaleDB
- ✅ Attribution API computes on-demand
- ✅ UI renders with provenance badges
- ✅ Backfill creates superseded chain
- ✅ Visual snapshots baseline stored

---

## Task Breakdown (6 Tasks)

### Task 1: REST API Endpoints (FastAPI)
**Priority**: P0 (Foundation)
**Duration**: 4-6 hours
**Dependencies**: Phase 3 (database layer)

**Deliverables**:
1. `backend/app/api/routes/metrics.py` (200 lines)
   - GET /api/v1/portfolios/{id}/metrics
   - GET /api/v1/portfolios/{id}/metrics/history
   - Query params: asof_date, start_date, end_date
   - Pydantic response models

2. `backend/app/api/routes/attribution.py` (150 lines)
   - GET /api/v1/portfolios/{id}/attribution/currency
   - Query params: asof_date
   - On-demand computation or database retrieval

3. `backend/app/api/schemas/metrics.py` (150 lines)
   - MetricsResponse (Pydantic model)
   - AttributionResponse (Pydantic model)
   - JSON encoders for Decimal, date

4. `backend/app/api/__init__.py` (50 lines)
   - Router registration
   - Dependency injection setup

**API Design** (RESTful):
```python
# backend/app/api/routes/metrics.py
from fastapi import APIRouter, Depends, Query
from uuid import UUID
from datetime import date

router = APIRouter(prefix="/api/v1/portfolios", tags=["metrics"])

@router.get("/{portfolio_id}/metrics")
async def get_portfolio_metrics(
    portfolio_id: UUID,
    asof_date: date = Query(default_factory=date.today),
):
    """Get latest metrics for portfolio."""
    queries = get_metrics_queries()
    metrics = await queries.get_latest_metrics(portfolio_id, asof_date)

    if not metrics:
        raise HTTPException(404, "Metrics not found")

    return MetricsResponse.from_orm(metrics)

@router.get("/{portfolio_id}/metrics/history")
async def get_metrics_history(
    portfolio_id: UUID,
    start_date: date,
    end_date: date,
):
    """Get historical metrics for date range."""
    queries = get_metrics_queries()
    history = await queries.get_metrics_history(
        portfolio_id, start_date, end_date
    )
    return [MetricsResponse.from_orm(m) for m in history]
```

**Schema Design**:
```python
# backend/app/api/schemas/metrics.py
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date
from typing import Optional
from uuid import UUID

class MetricsResponse(BaseModel):
    portfolio_id: UUID
    asof_date: date
    pricing_pack_id: str

    # Returns
    twr_1d: Optional[Decimal] = Field(None, description="1-day TWR")
    twr_mtd: Optional[Decimal] = Field(None, description="Month-to-date TWR")
    twr_ytd: Optional[Decimal] = Field(None, description="Year-to-date TWR")

    # Risk
    volatility_30d: Optional[Decimal] = Field(None, description="30-day annualized volatility")
    sharpe_30d: Optional[Decimal] = Field(None, description="30-day Sharpe ratio")
    max_drawdown_1y: Optional[Decimal] = Field(None, description="1-year max drawdown")

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }

class AttributionResponse(BaseModel):
    portfolio_id: UUID
    asof_date: date
    pricing_pack_id: str

    local_return: Decimal
    fx_return: Decimal
    interaction_return: Decimal
    total_return: Decimal

    error_bps: Optional[Decimal] = Field(None, description="Validation error in basis points")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }
```

**Acceptance**:
- ✅ Endpoints return 200 with valid data
- ✅ Pydantic validation enforces types
- ✅ OpenAPI docs auto-generated
- ✅ Error handling (404, 500)

---

### Task 2: Agent Capability Wiring
**Priority**: P0 (Critical Path)
**Duration**: 2-3 hours
**Dependencies**: Task 1 (API endpoints)

**Deliverables**:
1. Update `backend/app/agents/financial_analyst.py` (+100 lines)
   - Add `metrics.compute_twr` capability
   - Add `metrics.compute_sharpe` capability
   - Add `attribution.currency` capability
   - Wire to MetricsQueries and CurrencyAttribution

2. Update `backend/app/core/capability_registry.py` (+20 lines)
   - Register new capabilities in CAPABILITY_CATEGORIES

**Implementation**:
```python
# backend/app/agents/financial_analyst.py

async def metrics_compute_twr(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    asof_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Compute Time-Weighted Return using metrics database.

    Args:
        ctx: Request context (contains portfolio_id, asof_date)
        state: Execution state
        portfolio_id: Override portfolio ID (optional)
        asof_date: Override as-of date (optional)

    Returns:
        Dict with TWR metrics and provenance
    """
    portfolio_id = UUID(portfolio_id or str(ctx.portfolio_id))
    asof_date = asof_date or ctx.asof_date

    # Fetch from database
    queries = get_metrics_queries()
    metrics = await queries.get_latest_metrics(portfolio_id, asof_date)

    if not metrics:
        # Compute on-demand if not in database
        logger.info(f"Metrics not in DB, computing on-demand for {portfolio_id}")
        computer = MetricsComputer(use_db=False)
        metrics = await computer.compute_single(portfolio_id, asof_date)

    return {
        "twr_1d": float(metrics.twr_1d) if metrics.twr_1d else None,
        "twr_mtd": float(metrics.twr_mtd) if metrics.twr_mtd else None,
        "twr_ytd": float(metrics.twr_ytd) if metrics.twr_ytd else None,
        "pricing_pack_id": metrics.pricing_pack_id,
        "asof_date": str(metrics.asof_date),
        "__metadata__": {
            "source": "metrics_database",
            "capability": "metrics.compute_twr",
        }
    }

async def attribution_currency(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute currency attribution (local/FX/interaction).

    Args:
        ctx: Request context
        state: Execution state
        portfolio_id: Override portfolio ID (optional)

    Returns:
        Dict with attribution breakdown
    """
    portfolio_id = UUID(portfolio_id or str(ctx.portfolio_id))

    # Use CurrencyAttribution service
    from backend.jobs.currency_attribution import CurrencyAttribution

    attr = CurrencyAttribution(base_currency="CAD")
    result = attr.compute_portfolio_attribution(
        portfolio_id=str(portfolio_id),
        asof_date=ctx.asof_date,
    )

    return {
        "local_return": float(result.local_return),
        "fx_return": float(result.fx_return),
        "interaction_return": float(result.interaction_return),
        "total_return": float(result.total_return),
        "error_bps": float(result.error_bps) if result.error_bps else None,
        "pricing_pack_id": ctx.pricing_pack_id,
        "__metadata__": {
            "source": "currency_attribution",
            "capability": "attribution.currency",
        }
    }

def get_capabilities(self) -> List[str]:
    """Return list of capabilities."""
    return [
        "ledger.positions",
        "pricing.apply_pack",
        "metrics.compute_twr",       # NEW
        "metrics.compute_sharpe",    # NEW
        "attribution.currency",      # NEW
        "charts.overview",
    ]
```

**Acceptance**:
- ✅ Capabilities registered in registry
- ✅ Agent runtime routes to methods
- ✅ Metadata attached for attribution
- ✅ Database fallback works (on-demand computation)

---

### Task 3: UI Portfolio Overview (Streamlit)
**Priority**: P1 (User-Facing)
**Duration**: 3-4 hours
**Dependencies**: Task 2 (agent capabilities)

**Deliverables**:
1. `ui/screens/portfolio_overview.py` (300 lines)
   - Streamlit implementation per roadmap
   - Provenance badges (pack ID, ledger hash)
   - KPI ribbon (TWR, MWR, Vol, Sharpe, Drawdown)
   - Currency attribution breakdown

**Implementation** (from IMPLEMENTATION_ROADMAP_V2.md):
```python
# ui/screens/portfolio_overview.py
import streamlit as st
from ui.components.dawsos_theme import apply_dawsos_theme, metric_card

def render_portfolio_overview(portfolio_id: str):
    """Render portfolio overview with provenance."""
    apply_dawsos_theme()

    # Execute pattern via API
    result = client.execute("portfolio_overview", {"portfolio_id": portfolio_id})

    # Header with provenance
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title(result.data["portfolio_name"])
    with col2:
        st.markdown(f"""
        <div class="provenance-chip">
            Pack: {result.provenance["pricing_pack_id"][:8]} |
            Ledger: {result.provenance["ledger_commit_hash"][:7]}
        </div>
        """, unsafe_allow_html=True)

    # KPI Ribbon
    kpi_cols = st.columns(5)
    metrics = result.data["perf_strip"]

    with kpi_cols[0]:
        metric_card("TWR (YTD)", f"{metrics['twr_ytd']:.2%}")
    with kpi_cols[1]:
        metric_card("MWR", f"{metrics['mwr_ytd']:.2%}")
    with kpi_cols[2]:
        metric_card("Vol (Ann.)", f"{metrics['volatility_30d']:.2%}")
    with kpi_cols[3]:
        metric_card("Max DD", f"{metrics['max_drawdown_1y']:.2%}")
    with kpi_cols[4]:
        metric_card("Sharpe", f"{metrics['sharpe_30d']:.2f}")

    # Currency Attribution (if multi-currency)
    if result.data.get("attribution"):
        st.subheader("Currency Attribution")
        attr = result.data["attribution"]

        col1, col2, col3 = st.columns(3)
        with col1:
            metric_card("Local Return", f"{attr['local_return']:.2%}")
        with col2:
            metric_card("FX Return", f"{attr['fx_return']:.2%}")
        with col3:
            metric_card("Interaction", f"{attr['interaction_return']:.4%}")
```

**Acceptance**:
- ✅ UI renders with provenance badges
- ✅ KPI ribbon displays metrics
- ✅ Currency attribution visible (if applicable)
- ✅ Theme consistent with DawsOS branding

---

### Task 4: End-to-End Integration Tests
**Priority**: P1 (Quality Assurance)
**Duration**: 2-3 hours
**Dependencies**: Task 3 (UI complete)

**Deliverables**:
1. `backend/tests/test_e2e_metrics_api.py` (250 lines)
   - Full flow: API → Agent → Jobs → Database
   - Error handling scenarios
   - Performance validation (< 1.2s p95)

**Test Cases**:
```python
# backend/tests/test_e2e_metrics_api.py

async def test_metrics_api_full_flow():
    """Test full flow: API → Agent → Jobs → Database."""
    # 1. Setup: Insert test metrics in database
    queries = get_metrics_queries()
    await queries.insert_metrics(
        portfolio_id=UUID("test-portfolio-123"),
        asof_date=date(2025, 10, 22),
        pricing_pack_id="PP_2025-10-22",
        metrics={
            "twr_1d": 0.0125,  # 1.25%
            "twr_ytd": 0.0850,  # 8.50%
            "volatility_30d": 0.1520,  # 15.20%
        }
    )

    # 2. Call API endpoint
    response = client.get(
        f"/api/v1/portfolios/test-portfolio-123/metrics",
        params={"asof_date": "2025-10-22"}
    )

    # 3. Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["twr_1d"] == 0.0125
    assert data["twr_ytd"] == 0.0850
    assert data["pricing_pack_id"] == "PP_2025-10-22"

async def test_attribution_on_demand_computation():
    """Test on-demand currency attribution computation."""
    response = client.get(
        f"/api/v1/portfolios/test-portfolio-123/attribution/currency",
        params={"asof_date": "2025-10-22"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify identity: r_base ≈ (1+r_local)(1+r_fx)-1
    assert data["error_bps"] is None or data["error_bps"] < 0.1

async def test_api_performance_under_load():
    """Verify API p95 latency ≤ 1.2s."""
    import asyncio

    start = time.time()
    tasks = [
        client.get(f"/api/v1/portfolios/{i}/metrics")
        for i in range(100)
    ]
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    # p95 latency
    p95 = duration / 100 * 1.95  # Rough approximation
    assert p95 <= 1.2, f"p95 latency {p95}s exceeds 1.2s SLO"
```

**Acceptance**:
- ✅ All E2E tests pass
- ✅ Error handling verified
- ✅ Performance SLO met (< 1.2s p95)

---

### Task 5: Backfill Rehearsal Tool
**Priority**: P2 (Operational)
**Duration**: 2-3 hours
**Dependencies**: Phase 3 (pack schema)

**Deliverables**:
1. `backend/jobs/backfill_packs.py` (200 lines)
   - Backfill historical pricing packs
   - Supersede chain (D0 → D1)
   - Restatement banner trigger

**Implementation** (from IMPLEMENTATION_ROADMAP_V2.md):
```python
# backend/jobs/backfill_packs.py

def backfill_packs(start_date: date, end_date: date):
    """
    Backfill pricing packs for historical dates.
    Marks D0 pack as superseded, creates D1 pack.
    """
    for d in date_range(start_date, end_date):
        if pack_exists(d):
            logger.info(f"Pack for {d} already exists, skipping")
            continue

        # Fetch historical prices
        prices = fetch_historical_prices(d)
        fx_rates = fetch_historical_fx(d)

        # Create pack
        pack_id = create_pack(d, prices, fx_rates)
        logger.info(f"Created backfill pack {pack_id} for {d}")

def test_backfill_creates_superseded_chain():
    """Verify late CA triggers D0 → D1 supersede path."""
    # Day 0: Create initial pack
    pack_d0 = create_pack(date(2024, 10, 1), prices_d0, fx_d0)

    # Day 1: Late split announcement (2-for-1)
    apply_split("AAPL", ratio=2.0, effective_date=date(2024, 10, 1))

    # Backfill creates D1 pack
    pack_d1 = create_pack(date(2024, 10, 1), prices_d1_adjusted, fx_d0)

    # D0 should be superseded
    pack_d0_reloaded = get_pack(pack_d0.id)
    assert pack_d0_reloaded.superseded_by == pack_d1.id

    # UI should show banner
    response = client.get(f"/v1/portfolios/123/valuation?pack_id={pack_d0.id}")
    assert "restatement" in response.json()["banner"].lower()
```

**Acceptance**:
- ✅ Backfill creates packs for date range
- ✅ Supersede chain works (D0 → D1)
- ✅ Restatement banner displayed

---

### Task 6: Visual Regression Tests (Percy)
**Priority**: P2 (Quality Assurance)
**Duration**: 2-3 hours
**Dependencies**: Task 3 (UI complete)

**Deliverables**:
1. `tests/visual/test_overview_screenshots.py` (150 lines)
   - Playwright + Percy integration
   - Baseline snapshots for Portfolio Overview

**Implementation** (from IMPLEMENTATION_ROADMAP_V2.md):
```python
# tests/visual/test_overview_screenshots.py
from playwright.sync_api import sync_playwright
from percy import percy_snapshot

def test_portfolio_overview_visual():
    """Capture visual baseline for Portfolio Overview."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://staging.dawsos.internal/portfolio/123")

        # Wait for metrics to load
        page.wait_for_selector(".metric-card")

        # Take snapshot
        percy_snapshot(browser, page, "Portfolio Overview")

        browser.close()

def test_portfolio_overview_dark_mode():
    """Capture dark mode variant."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://staging.dawsos.internal/portfolio/123?theme=dark")

        page.wait_for_selector(".metric-card")
        percy_snapshot(browser, page, "Portfolio Overview - Dark Mode")

        browser.close()
```

**Acceptance**:
- ✅ Baseline snapshots captured
- ✅ Percy integration working
- ✅ Dark mode variant included

---

## Parallel Execution Strategy

### Session 1 (4-6 hours): Foundation
- Task 1: REST API Endpoints (complete)
- Task 2: Agent Capability Wiring (start)

### Session 2 (4-6 hours): Integration
- Task 2: Agent Capability Wiring (finish)
- Task 3: UI Portfolio Overview (complete)
- Task 4: E2E Integration Tests (start)

### Session 3 (4-6 hours): Quality & Operations
- Task 4: E2E Integration Tests (finish)
- Task 5: Backfill Rehearsal Tool (complete)
- Task 6: Visual Regression Tests (complete)

**Total**: 12-18 hours over 3 sessions

---

## Acceptance Criteria (S2-W4 Gates)

From IMPLEMENTATION_ROADMAP_V2.md Section "Sprint 2":

| Criteria | Test | Target |
|----------|------|--------|
| Metrics API returns data | Integration test | 200 OK from database |
| Attribution API computes | Integration test | ±0.1bp accuracy |
| UI renders with provenance | Visual test | Badges visible |
| Backfill supersede chain | Integration test | D0 → D1 works |
| Visual regression baseline | Percy | Snapshots stored |

**Additional Validation**:
- ✅ Agent capabilities registered
- ✅ E2E tests pass (API → Agent → Jobs → DB)
- ✅ Performance SLO met (< 1.2s p95)
- ✅ OpenAPI documentation generated

---

## Governance Compliance

### Codex Governance Alignment

**Allowed** (per DawsOS_Codex_Governance.md):
- ✅ Implement approved capabilities (metrics.compute_twr, attribution.currency)
- ✅ Write/expand tests (E2E, visual regression)
- ✅ Refactor for typing/observability
- ✅ Generate API schemas (Pydantic models)

**Disallowed** (enforced):
- ❌ No new dependencies (use existing FastAPI, Pydantic, Streamlit)
- ❌ No direct provider calls from UI (must go via agents)
- ❌ No DB schema changes without ADR (schema complete in Phase 3)
- ❌ No export paths without rights.ensure_allowed() (already enforced in Phase 2)

**Complexity Budget**:
- Diff budget: ≤ 300 LOC per task (all tasks comply)
- Cyclomatic complexity: ≤ 10 per function
- New files: ≤ 5 per PR (Task 1 creates 4, Task 3 creates 1)

---

## Dependencies

### External Services
- PostgreSQL with TimescaleDB (from Phase 3)
- AsyncPG connection pool (from Phase 3)
- FastAPI (already in requirements)
- Pydantic (already in requirements)
- Streamlit (already in requirements)

### Python Packages (existing)
```bash
# Already installed
fastapi>=0.104.0
pydantic>=2.5.0
streamlit>=1.28.0
asyncpg>=0.29.0

# New for Phase 4 (visual testing)
playwright>=1.40.0  # Visual regression
percy-playwright>=1.0.0  # Percy integration
```

### Database Schema
- portfolio_metrics (from Phase 3)
- currency_attribution (from Phase 3)
- pricing_packs (from Phase 2)

---

## Testing Strategy

### Unit Tests
- Pydantic model validation
- Agent capability methods
- API route handlers

### Integration Tests (E2E)
- Full flow: API → Agent → Jobs → Database
- Error handling (404, 500, validation errors)
- Performance validation (< 1.2s p95)

### Visual Tests
- Portfolio Overview baseline
- Dark mode variant
- Percy snapshot comparison

### Property Tests (reuse from Phase 3)
- Currency attribution identity
- TWR accuracy
- Metric calculations

---

## Monitoring

### Metrics to Track

**From backend/observability/metrics.py** (add):
```python
# API latency
self.api_latency = Histogram(
    f"{service_name}_api_request_duration_seconds",
    "API request latency",
    ["endpoint", "method", "status"],
)

# Agent capability execution
self.capability_execution_duration = Histogram(
    f"{service_name}_capability_execution_seconds",
    "Capability execution duration",
    ["capability_name"],
)

# UI page load
self.ui_page_load_duration = Histogram(
    f"{service_name}_ui_page_load_seconds",
    "UI page load duration",
    ["page_name"],
)
```

### Alerts
- API p95 latency > 1.2s (P1 alert)
- API error rate > 0.5% (P0 alert)
- UI page load > 3s (P2 alert)

---

## Documentation Deliverables

1. **PHASE4_COMPLETE.md** - Summary of all tasks
2. **API_DOCUMENTATION.md** - OpenAPI spec and usage guide
3. **UI_COMPONENT_GUIDE.md** - Streamlit components and theming

---

## Success Criteria

**Velocity**: Complete in ≤18 hours (on-budget)

**Quality**:
- ✅ All acceptance criteria met
- ✅ E2E tests pass
- ✅ Performance SLO met (< 1.2s p95)
- ✅ Visual regression baseline captured

**Architecture**:
- ✅ API layer follows RESTful conventions
- ✅ Agent capabilities properly wired
- ✅ UI displays provenance badges
- ✅ Governance compliance maintained

---

## Next Actions

1. **Immediate**: Start Task 1 (REST API Endpoints)
2. **Session 1**: Complete API + start agent wiring
3. **Session 2**: Complete agent wiring + UI
4. **Session 3**: E2E tests + backfill + visual tests

---

**Status**: Ready to start Phase 4 implementation
**Estimated Start**: 2025-10-22 (ready to start)
**Estimated Complete**: 2025-10-25 (3 days)
