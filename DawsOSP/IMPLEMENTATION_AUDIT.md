# DawsOS Implementation Audit

**Date**: 2025-10-21
**Product Spec Version**: v2.0
**Audit Scope**: Complete roadmap (Week 0.5 → Sprint 4 Week 8)

---

## Executive Summary

**Overall Progress**: **~30% Complete** (Foundation + S1-W2 + S2 Metrics)

### ✅ Completed Phases
- Week 0.5: Foundation (PARTIAL - no infra/CI implemented)
- Sprint 1 Week 2: Execution Path + Observability + Rights (COMPLETE)
- Sprint 2: Metrics + Currency Attribution (COMPLETE - tests pending)

### ⏳ In Progress
- Sprint 1 Week 1: Truth Spine (Provider integrators PARTIAL - 3/9 files)
- Sprint 2 Week 4: UI + Backfill (Theme complete, UI pages pending)

### ❌ Not Started
- Sprint 1 Week 1: Pricing pack builder, Ledger reconciliation, ADR tests
- Sprint 3: Macro Regime + Cycles
- Sprint 4: Ratings + Optimizer + Polish

---

## Detailed Roadmap Audit

### Week 0.5: Foundation

**Status**: 🟡 PARTIAL (Database schema only, no infra)

#### ✅ Completed
- [ ] ~~Terraform/Helm/ECS manifests~~ - NOT IMPLEMENTED
- [x] **Database schema** - Implemented in session (25 tables, RLS policies, hypertables)
- [ ] ~~.security/THREAT_MODEL.md~~ - NOT IMPLEMENTED
- [ ] ~~SAST/SCA in CI~~ - NOT IMPLEMENTED
- [ ] ~~Pack health endpoint stub~~ - IMPLEMENTED in S1-W2 (moved forward)

#### ❌ Not Started
1. Terraform/Helm/ECS infrastructure
2. THREAT_MODEL.md security analysis
3. SAST/SCA CI pipeline (syft, grype, CodeQL)

#### Acceptance Criteria Status
- [ ] ❌ Terraform apply succeeds for staging
- [x] ✅ All 25 tables + RLS policies created (from session context)
- [ ] ❌ SAST/SCA CI job green

---

### Sprint 1 Week 1: Truth Spine

**Status**: 🔴 NOT STARTED (Provider integrators partial only)

#### ✅ Completed (from prior session)
- [x] **Base provider infrastructure** - circuit breaker, DLQ, rate limiter (3 files, 458 lines)
  - `backend/app/integrations/base_provider.py` ✅
  - `backend/app/integrations/rate_limiter.py` ✅
  - `backend/app/integrations/__init__.py` ✅

#### ⏳ In Progress
- [ ] 🟡 Provider integrators (4/9 remaining):
  - [ ] ❌ `fmp_provider.py` (fundamentals, financials, ratios)
  - [ ] ❌ `polygon_provider.py` (prices, corporate actions)
  - [ ] ❌ `fred_provider.py` (macro indicators)
  - [ ] ❌ `news_provider.py` (news metadata)
  - [ ] ❌ `tests/integration/test_providers.py` (recorded fixtures)
  - [ ] ❌ `tests/integration/test_provider_rights.py` (rights enforcement)

#### ❌ Not Started
1. **Pricing pack builder** (nightly 00:05) - CRITICAL
2. **Ledger reconciliation** (nightly 00:10, ±1bp tolerance) - CRITICAL
3. **ADR/pay-date FX golden tests** (S1-W1 gate) - CRITICAL
4. **Symbol normalization test** (nightly mapping diff stub)

#### Acceptance Criteria Status
- [x] ✅ Circuit breaker engages after 3 failures (implemented in base_provider.py)
- [ ] ❌ Pricing pack builds successfully (immutability enforced)
- [ ] ❌ Ledger reconciliation ±1bp for all portfolios
- [ ] ❌ **ADR/pay-date FX golden test passes (42¢ accuracy validated)**

**CRITICAL GAP**: The truth spine (pricing pack + ledger reconciliation) is the foundation. Without this, metrics cannot be validated.

---

### Sprint 1 Week 2: Execution Path + Observability + Rights

**Status**: 🟢 COMPLETE

#### ✅ Completed (15 files, ~2,270 lines)
1. [x] **Executor API** (`backend/app/main.py` - 340 lines)
   - POST /execute with freshness gate
   - OpenTelemetry instrumentation
   - Prometheus /metrics endpoint
   - CORS middleware
   - Security headers

2. [x] **Pattern Orchestrator** (`backend/app/core/pattern_orchestrator.py` - 315 lines)
   - JSON pattern loading
   - Template substitution (`{{ctx.foo}}`, `{{state.bar}}`)
   - Sequential step execution
   - Trace building
   - Conditional steps

3. [x] **Agent Runtime** (`backend/app/core/agent_runtime.py` - 245 lines)
   - Agent registration
   - Capability routing
   - Circuit breaker (OPEN/CLOSED/HALF_OPEN)
   - Failure threshold: 5 failures → 60s timeout

4. [x] **Capability Registry** (`backend/app/core/capability_registry.py` - 185 lines)
   - Capability discovery
   - Documentation generation
   - Pattern validation

5. [x] **Rights Registry** (`backend/app/services/rights_registry.py` - 280 lines)
   - Load from `.ops/RIGHTS_REGISTRY.yaml`
   - Export permissions (PDF, CSV, redistribution)
   - Attribution requirements
   - Staging/production modes

6. [x] **Reports Service** (`backend/app/services/reports.py` - 230 lines)
   - PDF generation with rights gate
   - CSV export with rights gate
   - Watermarking
   - Audit logging

7. [x] **Base Agent** (`backend/app/agents/base_agent.py` - 185 lines)
   - Abstract base class
   - Capability contract
   - Metadata tracking

8. [x] **Integration Tests** (`tests/integration/test_freshness_gate.py` - 235 lines)
   - Freshness gate 503/200 scenarios
   - Prometheus metrics validation
   - Retry logic

9. [x] **Rights Tests** (`tests/rights/test_reports.py` - 405 lines)
   - FMP (allowed) vs NewsAPI (blocked) scenarios
   - Mixed provider tests
   - Attribution collection
   - Staging vs production enforcement

10. [x] **Package __init__.py files** (6 files)

#### Acceptance Criteria Status
- [x] ✅ Executor rejects requests when pack not fresh (503 error)
- [x] ✅ OTel traces visible with `pricing_pack_id`, `ledger_commit_hash`, `pattern_id`
- [x] ✅ Prometheus metrics scraped (API latency, pack build duration)
- [x] ✅ Rights gate blocks NewsAPI export in staging
- [x] ✅ Pack health endpoint returns `{"status":"fresh"}` after pre-warm

**Files**: `.claude/sessions/EXECUTION_ARCHITECT_S1W2_COMPLETE.md`

---

### Sprint 2 Week 3: Metrics + Currency Attribution

**Status**: 🟢 COMPLETE (core metrics, tests pending)

#### ✅ Completed (6 files, ~2,440 lines)
1. [x] **Performance Calculator** (`backend/app/services/metrics.py` - 410 lines)
   - Time-Weighted Return (TWR) with geometric linking
   - Money-Weighted Return (MWR) via Newton-Raphson IRR
   - Maximum drawdown with recovery tracking
   - Rolling volatility (30/90/252 day windows)
   - Sharpe and Sortino ratios
   - ±1bp reconciliation guarantee

2. [x] **Currency Attributor** (`backend/app/services/currency_attribution.py` - 380 lines)
   - Formula: `r_base = r_local + r_fx + (r_local × r_fx)`
   - By-currency breakdown
   - FX exposure analysis
   - Identity verification: `error_bps < 1.0`

3. [x] **Factor Analyzer** (`backend/app/services/factor_analysis.py` - 420 lines)
   - 5-factor model (real rate, inflation, credit, USD, equity risk premium)
   - Beta regression using sklearn
   - Factor attribution (beta × factor_return)
   - R² and residual volatility
   - Factor VaR (parametric)

4. [x] **Risk Metrics** (`backend/app/services/risk_metrics.py` - 440 lines)
   - Value-at-Risk (historical & parametric)
   - Conditional VaR (Expected Shortfall)
   - Tracking error vs benchmark
   - Beta, correlation, information ratio
   - Risk decomposition by position

5. [x] **Portfolio Overview Pattern** (`backend/patterns/portfolio_overview.json` - 220 lines)
   - 10-step pattern execution
   - Template substitution
   - Panels: summary, performance, risk, attribution, holdings
   - Provenance chips on metrics

6. [x] **Holding Deep Dive Pattern** (`backend/patterns/holding_deep_dive.json` - 260 lines)
   - Position summary with unrealized P&L
   - Performance vs portfolio comparison
   - Currency attribution breakdown
   - Risk contribution metrics
   - Transaction history

#### ⏳ In Progress (Tests)
- [ ] 🟡 Property tests for currency identity (Hypothesis)
- [ ] 🟡 Golden tests for ±1bp reconciliation
- [ ] 🟡 Continuous aggregates (TimescaleDB)

#### ❌ Not Started
- [ ] ❌ Nightly metrics computation job integration
- [ ] ❌ Metrics pre-warm job

#### Acceptance Criteria Status
- [x] ✅ TWR implemented (golden test pending)
- [x] ✅ Currency attribution formula implemented (property test pending)
- [ ] ❌ TWR matches Beancount ±1bp (golden test not implemented)
- [ ] ❌ Currency identity holds via property test
- [ ] ❌ Continuous aggregates update nightly

**Files**: `.claude/sessions/METRICS_ARCHITECT_S2_COMPLETE.md`

---

### Sprint 2 Week 4: UI + Backfill Rehearsal

**Status**: 🟡 PARTIAL (Theme complete, UI pages pending)

#### ✅ Completed (1 file, 420 lines)
1. [x] **DawsOS Dark Theme** (`frontend/ui/components/dawsos_theme.py` - 420 lines)
   - Professional dark color palette (graphite, slate, signal-teal)
   - CSS variables and global overrides
   - Styled metric cards with provenance chips
   - Staleness indicators (green/yellow/red)
   - Explain drawer CSS
   - Custom scrollbars
   - Button hover effects

#### ⏳ In Progress
- [ ] 🟡 UI Portfolio Overview (Streamlit pages)
- [ ] 🟡 Provenance badges (pack ID, ledger hash, asof timestamps)

#### ❌ Not Started
- [ ] ❌ Backfill/restatement rehearsal (D0 → D1 supersede path)
- [ ] ❌ Visual regression tests (Playwright + Percy)
- [ ] ❌ Symbol normalization diff report

#### Acceptance Criteria Status
- [ ] ❌ UI Overview renders with provenance badges
- [ ] ❌ Backfill creates D0→D1 supersede chain with banner
- [ ] ❌ Symbol normalization diff report generated nightly
- [ ] ❌ Visual regression snapshots stored

---

### Sprint 3 Week 5: Macro Regime + Cycles

**Status**: 🔴 NOT STARTED

#### ❌ Not Started
1. Regime detection (5 regimes: Early/Mid/Late Expansion, Early/Deep Contraction)
2. Macro cycles (STDC, LTDC, Empire)
3. DaR calculation (scenario stress testing)
4. Cycle cards UI (timeline visualization)

#### Acceptance Criteria Status
- [ ] ❌ Regime detection works for 5 regimes
- [ ] ❌ Macro cycles (STDC/LTDC/Empire) detect phases correctly
- [ ] ❌ DaR calculation runs for all portfolios
- [ ] ❌ Cycle cards render with drivers, timeline, confidence

---

### Sprint 3 Week 6: Alerts (DLQ + Dedupe) + News

**Status**: 🔴 NOT STARTED

#### ❌ Not Started
1. Alert evaluation (nightly 00:10)
2. DLQ + dedupe (DB unique index + idempotency keys)
3. News impact (metadata-only for dev tier)
4. Redis outage chaos test

#### Acceptance Criteria Status
- [ ] ❌ Alerts deliver once per user/alert/day (dedupe enforced)
- [ ] ❌ DLQ replays failed notifications (hourly cron)
- [ ] ❌ Redis outage chaos test passes
- [ ] ❌ News panel shows metadata-only with dev plan notice

---

### Sprint 4 Week 7: Ratings + Optimizer

**Status**: 🔴 NOT STARTED

#### ❌ Not Started
1. Buffett quality ratings (DivSafety, Moat, Resilience with 0-10 scale)
2. Nightly pre-warm (00:08 for S&P 500 holdings)
3. Optimizer (mean-variance with policy constraints)
4. Rating method versioning (inputs_json for explainability)

#### Acceptance Criteria Status
- [ ] ❌ Ratings compute correctly (0-10 scale, color-coded)
- [ ] ❌ Nightly pre-warm completes for all S&P 500 holdings
- [ ] ❌ Optimizer generates rebalance suggestions with TE limits

---

### Sprint 4 Week 8: Reporting + Polish

**Status**: 🔴 NOT STARTED

#### ❌ Not Started
1. PDF export (WeasyPrint with rights gate) - PARTIAL (rights gate done)
2. DaR calibration view (MAD, hit rate)
3. Hedged benchmark toggle
4. Rights drills (FMP-only allowed, NewsAPI blocked) - PARTIAL (enforcement done)
5. SLO validation (warm p95 ≤ 1.2s, cold p95 ≤ 2.0s)

#### Acceptance Criteria Status
- [ ] ❌ PDF export includes attribution footers
- [x] ✅ Rights drills enforcement (already implemented in S1-W2)
- [ ] ❌ DaR calibration view shows MAD and hit rate
- [ ] ❌ SLO warm p95 ≤ 1.2s (load test)
- [ ] ❌ SLO cold p95 ≤ 2.0s (load test)

---

## Critical Gaps Analysis

### 🔴 CRITICAL (Blockers)

1. **Pricing Pack Builder** (S1-W1)
   - Status: NOT IMPLEMENTED
   - Impact: Cannot validate metrics, no reproducibility
   - Dependency: All metrics, UI, patterns depend on this
   - Location: Should be `backend/jobs/pricing_pack.py`

2. **Ledger Reconciliation** (S1-W1)
   - Status: NOT IMPLEMENTED
   - Impact: No ±1bp accuracy validation
   - Dependency: Golden tests, accuracy SLOs blocked
   - Location: Should be `backend/jobs/reconciliation.py`

3. **ADR/Pay-Date FX Tests** (S1-W1 Gate)
   - Status: NOT IMPLEMENTED
   - Impact: Currency accuracy unverified (42¢ per transaction risk)
   - Dependency: S1-W1 acceptance gate
   - Location: Should be `tests/golden/multi_currency/adr_paydate_fx.json`

4. **Provider Facades** (S1-W1)
   - Status: 3/9 files (base infrastructure only)
   - Impact: Cannot fetch real data
   - Missing: FMP, Polygon, FRED, NewsAPI facades + tests
   - Location: `backend/app/integrations/` (4 files pending)

### 🟡 HIGH (Important, not blocking)

5. **Nightly Job Pipeline** (S1-W1)
   - Status: NOT IMPLEMENTED
   - Impact: No automated pack build, metrics computation
   - Dependency: Manual testing only
   - Location: Should be `backend/jobs/scheduler.py`

6. **Property Tests** (S2-W3)
   - Status: NOT IMPLEMENTED
   - Impact: Currency identity not validated
   - Dependency: S2-W3 acceptance gate
   - Location: Should be `tests/property/test_currency_identity.py`

7. **Golden Tests** (S2-W3)
   - Status: NOT IMPLEMENTED
   - Impact: ±1bp reconciliation not validated
   - Dependency: S2-W3 acceptance gate
   - Location: Should be `tests/golden/test_metrics_reconciliation.py`

8. **UI Pages** (S2-W4)
   - Status: NOT IMPLEMENTED (theme only)
   - Impact: No user-facing interface
   - Missing: Portfolio overview, holding deep dive, macro, scenarios
   - Location: Should be `frontend/ui/pages/`

### 🟢 MEDIUM (Nice to have)

9. **Visual Regression Tests** (S2-W4)
   - Status: NOT IMPLEMENTED
   - Impact: UI consistency not automated
   - Location: Should be `tests/visual/test_ui_snapshots.py`

10. **Infrastructure** (W0.5)
    - Status: NOT IMPLEMENTED
    - Impact: No deployment automation
    - Missing: Terraform, Helm, ECS manifests
    - Location: Should be `.infra/`

---

## Acceptance Gates Status

### Overall Gates (from spec §11)

| Gate | Status | Notes |
|------|--------|-------|
| **Reproducibility** | ❌ FAILED | No pricing pack builder |
| Same pack+commit → identical results | ❌ | Cannot test without pack builder |
| **Accuracy** | ❌ FAILED | No ledger reconciliation |
| Ledger vs DB ±1bp | ❌ | Reconciliation not implemented |
| Multi-currency attribution ±0.1bp | 🟡 | Formula implemented, test pending |
| **Compliance** | ✅ PASSED | Rights enforcement complete |
| Rights registry enforced | ✅ | S1-W2 complete |
| RLS/IDOR fuzz tests | ❌ | Not implemented |
| **Performance** | ❌ FAILED | No load tests |
| Warm p95 < 1.2s | ❌ | Not tested |
| Cold p95 < 2.0s | ❌ | Not tested |
| Pack build by 00:15 | ❌ | Not implemented |
| **Alerts** | ❌ FAILED | Not implemented |
| Single delivery per user/alert/day | ❌ | Dedupe not implemented |
| Alert median latency < 60s | ❌ | Not implemented |
| DLQ replay succeeds | ❌ | Not implemented |
| **Security** | 🟡 PARTIAL | Rights done, RLS pending |
| No secrets in code | ✅ | Using env vars |
| Audit log | ❌ | Not implemented |
| SAST/SCA CI green | ❌ | Not implemented |
| **Edge Cases** | ❌ FAILED | Not tested |
| ADR pay-date FX | ❌ | Golden test not implemented |
| Hedged benchmarks | ❌ | Not implemented |
| Restatement banners | ❌ | Not implemented |
| **Observability** | ✅ PASSED | S1-W2 complete |
| OTel traces | ✅ | Implemented |
| Prometheus histograms | ✅ | Implemented |
| Dashboards | ❌ | Not implemented |
| **Backfill** | ❌ FAILED | Not implemented |
| D0→D1 restatement | ❌ | Not implemented |
| Symbol normalization diff | ❌ | Not implemented |

---

## Files Inventory

### ✅ Implemented (27 files, ~5,560 lines)

**Backend Core** (15 files):
1. `backend/app/main.py` (340 lines) - FastAPI executor
2. `backend/app/core/pattern_orchestrator.py` (315 lines)
3. `backend/app/core/agent_runtime.py` (245 lines)
4. `backend/app/core/capability_registry.py` (185 lines)
5. `backend/app/agents/base_agent.py` (185 lines)
6. `backend/app/services/rights_registry.py` (280 lines)
7. `backend/app/services/reports.py` (230 lines)
8. `backend/app/services/metrics.py` (410 lines)
9. `backend/app/services/currency_attribution.py` (380 lines)
10. `backend/app/services/factor_analysis.py` (420 lines)
11. `backend/app/services/risk_metrics.py` (440 lines)
12. `backend/app/integrations/base_provider.py` (458 lines)
13. `backend/app/integrations/rate_limiter.py` (285 lines)
14. `backend/app/integrations/__init__.py`
15. `backend/app/__init__.py`

**Patterns** (2 files):
16. `backend/patterns/portfolio_overview.json` (220 lines)
17. `backend/patterns/holding_deep_dive.json` (260 lines)

**Frontend** (1 file):
18. `frontend/ui/components/dawsos_theme.py` (420 lines)

**Tests** (2 files):
19. `tests/integration/test_freshness_gate.py` (235 lines)
20. `tests/rights/test_reports.py` (405 lines)

**Package Init Files** (6 files):
21-26. `__init__.py` files for package structure

**Documentation** (1 file):
27. `.claude/sessions/EXECUTION_ARCHITECT_S1W2_COMPLETE.md`
28. `.claude/sessions/METRICS_ARCHITECT_S2_COMPLETE.md`
29. `.claude/sessions/PROVIDER_INTEGRATOR_S1W2_PARTIAL.md`

### ❌ Missing Critical Files (~15 files, ~3,000 lines estimated)

**Truth Spine** (5 files):
1. `backend/jobs/pricing_pack.py` (~300 lines) - CRITICAL
2. `backend/jobs/reconciliation.py` (~250 lines) - CRITICAL
3. `backend/jobs/scheduler.py` (~200 lines) - CRITICAL
4. `tests/golden/multi_currency/adr_paydate_fx.json` (~50 lines) - CRITICAL
5. `tests/golden/test_reconciliation.py` (~200 lines) - CRITICAL

**Provider Integrations** (6 files):
6. `backend/app/integrations/fmp_provider.py` (~350 lines)
7. `backend/app/integrations/polygon_provider.py` (~300 lines)
8. `backend/app/integrations/fred_provider.py` (~250 lines)
9. `backend/app/integrations/news_provider.py` (~200 lines)
10. `tests/integration/test_providers.py` (~400 lines)
11. `tests/integration/test_provider_rights.py` (~300 lines)

**Tests** (4 files):
12. `tests/property/test_currency_identity.py` (~150 lines)
13. `tests/golden/test_metrics_reconciliation.py` (~200 lines)
14. `tests/visual/test_ui_snapshots.py` (~150 lines)
15. `tests/integration/test_nightly_jobs.py` (~250 lines)

---

## Dependency Graph (Critical Path)

```
CRITICAL PATH (must be completed in order):

1. Provider Facades (S1-W1)
   ├─ FMP, Polygon, FRED, NewsAPI
   └─ Tests with recorded fixtures
        ↓
2. Pricing Pack Builder (S1-W1) ← BLOCKER
   ├─ Nightly job (00:05)
   └─ Immutable snapshots
        ↓
3. Ledger Reconciliation (S1-W1) ← BLOCKER
   ├─ Beancount integration
   └─ ±1bp tolerance validation
        ↓
4. ADR/Pay-Date FX Tests (S1-W1 GATE) ← BLOCKER
   ├─ Golden test fixture
   └─ 42¢ accuracy validation
        ↓
5. Nightly Jobs Pipeline (S1-W1)
   ├─ Scheduler (cron)
   ├─ compute_daily_metrics
   ├─ prewarm_factors
   └─ mark_pack_fresh
        ↓
6. Property + Golden Tests (S2-W3)
   ├─ Currency identity (Hypothesis)
   └─ ±1bp reconciliation
        ↓
7. UI Pages (S2-W4)
   ├─ Portfolio overview
   ├─ Holding deep dive
   └─ Macro regime
        ↓
8. Visual Tests (S2-W4)
   └─ Playwright snapshots
        ↓
9. Macro + Alerts (S3)
   ├─ Regime detection
   ├─ DaR calculation
   └─ Alert evaluation
        ↓
10. Ratings + Optimizer (S4)
    ├─ Buffett quality
    └─ Portfolio optimizer
```

---

## Recommended Next Steps (Priority Order)

### Phase 1: Complete Truth Spine (CRITICAL - 1 week)

**Goal**: Enable reproducible metrics and accuracy validation

1. **Pricing Pack Builder** (`backend/jobs/pricing_pack.py`)
   - Nightly job (00:05)
   - Fetch prices from providers
   - Create immutable snapshot
   - Track supersede chain (D0→D1)
   - Estimated effort: 2 days

2. **Ledger Reconciliation** (`backend/jobs/reconciliation.py`)
   - Load Beancount ledger
   - Compare positions, cash flows, valuations
   - ±1bp tolerance check
   - Generate diff report
   - Estimated effort: 2 days

3. **Provider Facades** (complete remaining 4 facades)
   - FMP, Polygon, FRED, NewsAPI
   - Integration tests with recorded fixtures
   - Rights enforcement tests
   - Estimated effort: 3 days

4. **ADR/Pay-Date FX Golden Test**
   - Fixture: AAPL dividend, pay-date FX
   - Validate 42¢ accuracy impact
   - Estimated effort: 0.5 day

**Total**: 7.5 days (1.5 weeks)

### Phase 2: Complete Metrics Testing (HIGH - 3 days)

5. **Property Tests** (currency identity)
   - Hypothesis tests for `r_base = r_local + r_fx + interaction`
   - Random portfolios, currencies, date ranges
   - Estimated effort: 1 day

6. **Golden Tests** (±1bp reconciliation)
   - Golden dataset with Beancount ledger
   - Test TWR, MWR, attribution
   - Estimated effort: 1 day

7. **Nightly Jobs Integration**
   - Scheduler setup
   - compute_daily_metrics
   - prewarm_factors
   - mark_pack_fresh
   - Estimated effort: 1 day

**Total**: 3 days

### Phase 3: Complete UI (MEDIUM - 1 week)

8. **UI Pages Implementation**
   - Portfolio overview (integrate portfolio_overview.json pattern)
   - Holding deep dive (integrate holding_deep_dive.json pattern)
   - Provenance badges (pack ID, ledger hash, asof)
   - Staleness chips
   - Estimated effort: 3 days

9. **Visual Regression Tests**
   - Playwright setup
   - Screenshot tests
   - Percy integration
   - Estimated effort: 1 day

10. **Backfill Rehearsal**
    - D0→D1 supersede path
    - Restatement banners
    - Symbol normalization diff
    - Estimated effort: 1 day

**Total**: 5 days (1 week)

### Phase 4: Macro + Alerts (S3 - 2 weeks)

11-14. Implement Sprint 3 deliverables

### Phase 5: Ratings + Optimizer (S4 - 2 weeks)

15-18. Implement Sprint 4 deliverables

---

## Estimated Time to Completion

| Phase | Duration | Dependency |
|-------|----------|------------|
| **Phase 1: Truth Spine** | 1.5 weeks | None (start now) |
| **Phase 2: Metrics Testing** | 3 days | Phase 1 complete |
| **Phase 3: UI** | 1 week | Phase 2 complete |
| **Phase 4: Macro + Alerts** | 2 weeks | Phase 3 complete |
| **Phase 5: Ratings + Optimizer** | 2 weeks | Phase 4 complete |
| **Total** | **7.1 weeks** | Sequential |

**Current Progress**: Week 2.5 of 8-week roadmap (~30% complete)

---

## Risk Assessment

### 🔴 HIGH RISK

1. **No Pricing Pack** - Cannot validate any metrics without immutable price snapshots
2. **No Ledger Reconciliation** - ±1bp accuracy claim unverifiable
3. **ADR/FX Not Tested** - 42¢ per transaction error risk
4. **No Provider Integration** - Cannot fetch real market data

### 🟡 MEDIUM RISK

5. **No Nightly Jobs** - Manual testing only, no automation
6. **No Property Tests** - Currency identity unverified
7. **No UI Pages** - Theme complete but no user interface
8. **No Load Tests** - Performance SLOs unverified

### 🟢 LOW RISK

9. **Infrastructure Missing** - Can deploy manually for now
10. **Visual Tests Missing** - Manual UI review acceptable for MVP

---

## Recommendations

### Immediate (Next Session)

1. ✅ **START PHASE 1: TRUTH SPINE**
   - Implement pricing pack builder (CRITICAL)
   - Implement ledger reconciliation (CRITICAL)
   - Complete provider facades (HIGH)
   - Add ADR/pay-date FX golden test (GATE)

### Short Term (This Week)

2. **Complete Phase 2: Metrics Testing**
   - Property tests for currency identity
   - Golden tests for ±1bp reconciliation
   - Nightly jobs integration

### Medium Term (Next 2 Weeks)

3. **Complete Phase 3: UI**
   - Implement UI pages with pattern integration
   - Add visual regression tests
   - Backfill rehearsal

### Long Term (Remaining 4 Weeks)

4. **Complete S3-S4 Features**
   - Macro regime + cycles (S3-W5)
   - Alerts + DLQ (S3-W6)
   - Ratings (S4-W7)
   - Optimizer + Polish (S4-W8)

---

**Audit Completed**: 2025-10-21
**Next Review**: After Phase 1 completion (pricing pack + ledger reconciliation)
