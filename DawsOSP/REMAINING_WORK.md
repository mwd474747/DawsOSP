# DawsOS Remaining Work - Roadmap Status

**Date**: 2025-10-22
**Current Status**: Sprint 2 Complete ✅
**Remaining**: Sprints 3-4 (4 weeks, ~16-24 hours development time)

---

## Executive Summary

**Completed**: Phase 0 (partial), Sprint 1 (partial), Sprint 2 (100%)
**Remaining**: Sprint 3 + Sprint 4 + Infrastructure gaps

**Total Remaining Estimate**: 4 weeks (assuming 8-10 FTE team) or ~80-120 hours solo development

---

## What's Complete ✅

### Phase 0: Foundation (Partial)
- ✅ Database schema (pricing_packs, portfolio_metrics, currency_attribution)
- ✅ TimescaleDB hypertables + continuous aggregates
- ✅ RLS infrastructure (get_db_connection_with_rls)
- ⏳ RLS policies (infrastructure ready, policies not created)
- ⏳ Terraform/IaC (not implemented)
- ⏳ Security baseline (no SBOM/SCA/SAST yet)
- ⏳ Rights registry (stub not implemented)

**Status**: ~40% complete (database ready, infrastructure/security gaps)

---

### Sprint 1: Truth Spine + Execution (Partial)
- ✅ Pricing pack schema (immutability via superseded_by)
- ✅ Pack queries (get_latest_pack, get_pack_by_id)
- ✅ Execution path (executor.py /v1/execute)
- ✅ Agent runtime (capability framework)
- ✅ Observability (OpenTelemetry spans, Prometheus metrics)
- ⏳ Ledger integration (Beancount parsing not implemented)
- ⏳ Pack reconciliation (±1bp check not implemented)
- ⏳ Rights enforcement gate (not implemented)
- ⏳ Nightly scheduler (not implemented)

**Status**: ~50% complete (execution path works, ledger/reconcile missing)

---

### Sprint 2: Metrics + UI + Backfill (100% Complete) ✅

**Week 3: Metrics + Currency Attribution**
- ✅ Metrics database (portfolio_metrics hypertable)
- ✅ Continuous aggregates (30d, 60d, 90d, 1y)
- ✅ Currency attribution service (±0.1bp accuracy)
- ✅ Metrics queries (get_latest_metrics, get_rolling_metrics, etc.)
- ✅ Database wiring complete

**Week 4: UI + Backfill + Tests**
- ✅ UI Portfolio Overview (Streamlit)
- ✅ Mock client for offline development
- ✅ Backfill rehearsal tool (D0 → D1 supersede)
- ✅ Visual regression tests (Playwright + custom comparison)
- ✅ E2E integration tests (10 tests)
- ✅ Agent capability wiring (metrics.compute_twr, attribution.currency, metrics.compute_sharpe)

**Status**: ✅ **100% COMPLETE**

---

## What's Remaining ⏳

### Sprint 3: Macro + Alerts + News (Weeks 5-6)

**Estimated**: 2 weeks (team) or ~40-60 hours solo

#### Week 5: Macro Regime + Cycles

**Deliverables**:
1. **Macro Service** (`backend/app/services/macro.py`) - ~400 lines
   - Regime detection (5 regimes: Early/Mid/Late Expansion, Early/Deep Contraction)
   - Z-score normalization for indicators (T10Y2Y, UNRATE, CPIAUCSL)
   - Regime classification logic

2. **Macro Cycles** (`backend/app/services/cycles.py`) - ~500 lines
   - STDC (Short-Term Debt Cycle) detector
   - LTDC (Long-Term Debt Cycle) detector
   - Empire cycle detector
   - Cycle definitions JSON (`storage/macro_cycles/cycle_definitions.json`)
   - Composite score computation
   - Phase matching logic

3. **DaR (Drawdown at Risk)** (`backend/app/services/risk.py`) - ~300 lines
   - Scenario stress testing
   - 95% confidence DaR calculation
   - Scenario application to portfolio

4. **FRED Integration** (`backend/app/services/fred.py`) - ~200 lines
   - Fetch macro indicators (T10Y2Y, UNRATE, CPIAUCSL, etc.)
   - Cache indicators daily
   - Store in `macro_indicators` table

**Database Schema**:
```sql
CREATE TABLE macro_indicators (
    id UUID PRIMARY KEY,
    indicator_id TEXT NOT NULL,  -- T10Y2Y, UNRATE, etc.
    date DATE NOT NULL,
    value NUMERIC NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE regime_history (
    id UUID PRIMARY KEY,
    date DATE NOT NULL,
    regime TEXT NOT NULL,  -- EARLY_EXPANSION, etc.
    indicators_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Tests**:
- Regime detection tests (5 regimes)
- Cycle phase tests (STDC/LTDC/Empire)
- DaR calculation tests
- FRED API integration tests

**Estimate**: 20-30 hours

---

#### Week 6: Alerts (DLQ + Dedupe) + News

**Deliverables**:
1. **Alert Service** (`backend/app/services/alerts.py`) - ~400 lines
   - Condition evaluation (nightly cron)
   - Cooldown enforcement (24h minimum)
   - Notification delivery

2. **DLQ (Dead Letter Queue)** (`backend/app/jobs/dlq_replay.py`) - ~200 lines
   - Failed notification handler
   - DLQ push/pop/ack/nack
   - Hourly replay job

3. **Deduplication** (`backend/app/db/models/notifications.py`) - ~100 lines
   - Unique constraint on (user_id, alert_id, date)
   - Idempotency key checks

4. **News Service** (`backend/app/services/news.py`) - ~200 lines
   - NewsAPI integration (dev plan: metadata only, 24h delay)
   - Article fetching
   - Sentiment stub (requires paid tier)

**Database Schema**:
```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    condition_json JSONB NOT NULL,
    notify_email BOOLEAN DEFAULT FALSE,
    notify_inapp BOOLEAN DEFAULT TRUE,
    cooldown_hours INT DEFAULT 24,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    alert_id UUID NOT NULL,
    message TEXT NOT NULL,
    delivered_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT notifications_dedupe UNIQUE (user_id, alert_id, delivered_at::date)
);

CREATE TABLE dlq (
    id UUID PRIMARY KEY,
    alert_id UUID NOT NULL,
    payload JSONB NOT NULL,
    error_message TEXT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Tests**:
- Alert condition evaluation tests
- Cooldown tests
- DLQ replay tests
- Deduplication tests
- Chaos test: Redis outage (alerts queue to DLQ, replay succeeds)

**Estimate**: 20-30 hours

---

### Sprint 4: Ratings + Optimizer + Reporting (Weeks 7-8)

**Estimated**: 2 weeks (team) or ~40-60 hours solo

#### Week 7: Ratings + Optimizer

**Deliverables**:
1. **Ratings Service** (`backend/app/services/ratings.py`) - ~600 lines
   - DivSafety score (0-10 scale)
     - Payout ratio (30%)
     - FCF coverage (35%)
     - Growth streak (20%)
     - Net cash (15%)
   - Moat score (0-10 scale)
     - Brand strength
     - Switching costs
     - Network effects
     - Cost advantages
   - Resilience score (0-10 scale)
     - Balance sheet strength
     - Operating leverage
     - Cyclicality
   - Method versioning (inputs_json stored for explainability)

2. **Fundamentals Fetcher** (`backend/app/services/fundamentals.py`) - ~300 lines
   - FMP API integration
   - Income statement fetching
   - Balance sheet fetching
   - Cash flow statement fetching
   - Dividend history fetching

3. **Optimizer Service** (`backend/app/services/optimizer.py`) - ~500 lines
   - Mean-variance optimization (Markowitz)
   - Tracking error constraints
   - Rebalance suggestions
   - Transaction cost modeling

4. **Nightly Pre-warm Job** (`backend/jobs/prewarm_ratings.py`) - ~200 lines
   - Fetch S&P 500 holdings
   - Pre-compute ratings for all holdings
   - Store in `security_ratings` table

**Database Schema**:
```sql
CREATE TABLE security_ratings (
    id UUID PRIMARY KEY,
    security_id UUID NOT NULL,
    pricing_pack_id TEXT NOT NULL,
    method_version TEXT NOT NULL,
    inputs_json JSONB NOT NULL,
    div_safety NUMERIC,
    moat NUMERIC,
    resilience NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE rebalance_suggestions (
    id UUID PRIMARY KEY,
    portfolio_id UUID NOT NULL,
    suggested_trades JSONB NOT NULL,
    expected_te NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Tests**:
- DivSafety calculation tests
- Moat calculation tests
- Resilience calculation tests
- Method versioning tests
- Optimizer tests (TE constraints)
- Pre-warm job tests

**Estimate**: 25-35 hours

---

#### Week 8: Reporting + Polish

**Deliverables**:
1. **PDF Exporter** (`backend/app/services/reporting.py`) - ~400 lines
   - HTML template rendering
   - Rights gate enforcement
   - Attribution footer generation
   - PDF generation (WeasyPrint or wkhtmltopdf)

2. **Hedged Benchmark** (`backend/app/services/benchmarks.py`) - ~200 lines
   - Toggle for currency hedging
   - Strip out FX return when hedged

3. **DaR Calibration View** (`ui/screens/dar_calibration.py`) - ~300 lines
   - Walk-forward calibration
   - MAD (Mean Absolute Deviation) calculation
   - Hit rate calculation (95% threshold)
   - Actual vs forecast chart

4. **Rights Drills** (final validation) - ~100 lines tests
   - FMP-only export allowed
   - NewsAPI export blocked
   - Attribution text validation

5. **Performance SLO Validation** - ~200 lines tests
   - Warm p95 ≤ 1.2s (load test)
   - Cold p95 ≤ 2.0s (load test)

**Tests**:
- PDF export tests (rights gate)
- Hedged benchmark tests
- DaR calibration tests
- Rights drill tests
- Performance SLO tests

**Estimate**: 15-25 hours

---

## Infrastructure Gaps (Critical)

### 1. Ledger Integration (Sprint 1 Gap)
**Estimate**: 10-15 hours

**Deliverables**:
- `backend/app/services/ledger.py` - Beancount parser (~400 lines)
- Parse Beancount ledger from git repo
- Extract transactions, balances
- Reconciliation job (±1bp check)
- Nightly scheduler

**Schema**:
```sql
CREATE TABLE ledger_transactions (
    id UUID PRIMARY KEY,
    ledger_commit_hash TEXT NOT NULL,
    date DATE NOT NULL,
    account TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    currency TEXT NOT NULL,
    narration TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE reconciliation_results (
    id UUID PRIMARY KEY,
    portfolio_id UUID NOT NULL,
    pricing_pack_id TEXT NOT NULL,
    ledger_commit_hash TEXT NOT NULL,
    error_bps NUMERIC NOT NULL,
    passed BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 2. RLS Policies (Phase 0 Gap)
**Estimate**: 2-4 hours

**Deliverables**:
- SQL migration: `005_create_rls_policies.sql`
- Enable RLS on 14 portfolio-scoped tables
- Create policies for multi-tenant isolation

**Example**:
```sql
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

CREATE POLICY portfolio_isolation ON portfolios
    USING (user_id = current_setting('app.user_id')::uuid);

ALTER TABLE lots ENABLE ROW LEVEL SECURITY;

CREATE POLICY lots_isolation ON lots
    USING (portfolio_id IN (
        SELECT id FROM portfolios
        WHERE user_id = current_setting('app.user_id')::uuid
    ));
```

---

### 3. Rights Registry (Phase 0 Gap)
**Estimate**: 4-6 hours

**Deliverables**:
- `.ops/RIGHTS_REGISTRY.yaml` - Provider rights definitions
- `backend/app/core/rights_registry.py` - Loader (~200 lines)
- Rights gate in executor (`ensure_allowed()`)
- PDF export rights check

**Example**:
```yaml
providers:
  FMP:
    name: Financial Modeling Prep
    allows_display: true
    allows_export_pdf: true
    allows_export_csv: true
    allows_redistribution: false
    attribution_text: "Data provided by Financial Modeling Prep"
```

---

### 4. Infrastructure as Code (Phase 0 Gap)
**Estimate**: 8-12 hours

**Deliverables**:
- `infra/terraform/` - Terraform modules for:
  - PostgreSQL + TimescaleDB (RDS or self-hosted)
  - Redis cluster (ElastiCache)
  - S3 buckets (reports, backups, DLQ)
  - Secrets Manager
  - VPC, subnets, security groups
  - WAF rules
  - Monitoring (Prometheus, Jaeger)

---

### 5. Security Baseline (Phase 0 Gap)
**Estimate**: 6-10 hours

**Deliverables**:
- `.security/THREAT_MODEL.md` - STRIDE analysis
- `.github/workflows/security.yml` - SBOM/SCA/SAST CI
  - Syft (SBOM generation)
  - ORT (license compliance)
  - Grype (vulnerability scan)
  - CodeQL (SAST)
- `tests/security/test_rls_fuzz.py` - RLS fuzz tests

---

## Summary Table

| Component | Status | Estimate (Solo) | Priority |
|-----------|--------|-----------------|----------|
| **Sprint 2** | ✅ 100% | 0 hours | N/A |
| **Sprint 3 Week 5** (Macro + Cycles) | ⏳ 0% | 20-30 hours | P1 |
| **Sprint 3 Week 6** (Alerts + News) | ⏳ 0% | 20-30 hours | P1 |
| **Sprint 4 Week 7** (Ratings + Optimizer) | ⏳ 0% | 25-35 hours | P2 |
| **Sprint 4 Week 8** (Reporting + Polish) | ⏳ 0% | 15-25 hours | P2 |
| **Ledger Integration** | ⏳ 0% | 10-15 hours | P0 |
| **RLS Policies** | ⏳ 0% | 2-4 hours | P0 |
| **Rights Registry** | ⏳ 0% | 4-6 hours | P1 |
| **Infrastructure (Terraform)** | ⏳ 0% | 8-12 hours | P1 |
| **Security Baseline** | ⏳ 0% | 6-10 hours | P1 |
| **TOTAL** | ~48% | **110-167 hours** | - |

**Solo Development**: ~3-4 weeks full-time (40 hours/week)
**Team Development**: ~2-3 weeks (8-10 FTEs as per roadmap)

---

## Critical Path

1. ✅ **Sprint 2 Complete** (Metrics + UI + Tests)
2. ⏳ **Ledger Integration** (P0) - Blocks reconciliation
3. ⏳ **RLS Policies** (P0) - Blocks production security
4. ⏳ **Rights Registry** (P1) - Blocks PDF export
5. ⏳ **Sprint 3** (Macro + Alerts) - Feature completeness
6. ⏳ **Sprint 4** (Ratings + Optimizer + Reporting) - Feature completeness
7. ⏳ **Infrastructure** (Terraform) - Blocks production deployment
8. ⏳ **Security** (SBOM/SCA/SAST) - Blocks production deployment

---

## Recommendations

### Option 1: MVP (Minimum Viable Product)
**Goal**: Production-ready with core features
**Scope**: Sprint 2 (done) + Ledger + RLS + Rights + Infrastructure
**Estimate**: 24-37 hours
**Features**: Metrics, UI, Pack immutability, Security, Export

### Option 2: Feature Complete (No Macro/Ratings)
**Goal**: All metrics + UI + security, skip advanced features
**Scope**: MVP + Alerts + News + Reporting
**Estimate**: 59-102 hours
**Features**: MVP + Alerts + PDF export + Hedged benchmark

### Option 3: Full Roadmap
**Goal**: All planned features (Macro, Ratings, Optimizer)
**Scope**: Everything
**Estimate**: 110-167 hours
**Features**: Complete DawsOS as per roadmap

---

## Next Steps

### Immediate (P0 - Critical)
1. ✅ Complete Sprint 2 (DONE)
2. ⏳ Implement RLS policies (2-4 hours)
3. ⏳ Integrate Beancount ledger (10-15 hours)
4. ⏳ Implement rights registry (4-6 hours)

### Short-term (P1 - High Priority)
5. ⏳ Implement Sprint 3 Week 5 (Macro regime + cycles) (20-30 hours)
6. ⏳ Implement Sprint 3 Week 6 (Alerts + News) (20-30 hours)
7. ⏳ Create Terraform infrastructure (8-12 hours)

### Medium-term (P2 - Feature Completeness)
8. ⏳ Implement Sprint 4 Week 7 (Ratings + Optimizer) (25-35 hours)
9. ⏳ Implement Sprint 4 Week 8 (Reporting + Polish) (15-25 hours)
10. ⏳ Add security baseline (SBOM/SCA/SAST) (6-10 hours)

---

**Status**: Sprint 2 Complete (48% of roadmap)
**Remaining**: 110-167 hours (~3-4 weeks solo, ~2-3 weeks team)
**Critical Path**: Ledger → RLS → Rights → Sprint 3 → Sprint 4 → Infrastructure → Security
