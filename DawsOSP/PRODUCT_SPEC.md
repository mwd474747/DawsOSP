# DawsOS — Portfolio Intelligence Platform

**Build Spec v2.0 (Master)** • **Date:** 2025-10-21 (America/Toronto) • **Owner:** Mike ("portfolio-first, truth-first")

> This master spec merges the full architecture/flows/data models/provider plan with the **DawsOS UI design system**. It's written to be *code-ready*, reduce drift, and make onboarding new engineers trivial.

---

## 0) Executive intent

Deliver a **portfolio-first, explainable decision engine** that fuses:

* **Dalio macro** — regime → factor → scenario to quantify the environment and shocks.
* **Buffett fundamentals** — quality, moats, margins, conservative balance sheets → ratings & policies.
* **Auditable math** — Beancount **ledger-of-record** + frozen daily **Pricing Pack** (prices/FX) so every number is reproducible.

**Guardrails**

1. **Single path**: UI → **Executor API** → **Pattern Orchestrator** → **Agents** → **Services** → Data.
2. **Reproducibility**: every Result includes `pricing_pack_id` + `ledger_commit_hash`.
3. **Compliance**: provider **rights registry** gates exports & attributions (FMP/Polygon/FRED/News).
4. **Action orientation**: alerts ship with **playbooks** (hedge idea, cap, rebalance diff).
5. **Multi-currency truth**: trade-time FX locked in lots; pack FX for valuation; dividend pay-date FX for ADRs.
6. **Pack health contract**: `/health/pack` endpoint exposes freshness status; executor blocks until `is_fresh=true`.
7. **No UI shortcuts**: UI may ONLY call Executor API; direct provider/DB calls are prohibited.

---

## 1) Architecture (production-ready)

```
UI (Streamlit now / Next.js later)
   │  POST /v1/execute
   ▼
Executor API (FastAPI) – builds RequestCtx, enforces pack freshness, sets RLS context
   │
   ▼
Pattern Orchestrator (declarative DAG runner)
   │
   ▼
Agent Runtime (capability router)
 ├─ financial_analyst  → metrics/ratings/optimizer/pricing_pack
 ├─ macro_hound        → FRED/FX, regime, factors, scenarios, DaR
 ├─ data_harvester     → FMP/Polygon/NewsAPI/OpenBB via facades
 └─ claude             → explanations (trace-aware)

Services (stateless facades)
 prices | fx | corporate_actions | fundamentals | fred | news |
 ratings | metrics | macro_risk | optimizer | ledger_io | pricing_pack |
 reports | alerts | store | knowledge_graph

Data
 Postgres + Timescale (analytics/hypertables)
 Redis (cache/queues)
 Git + Beancount (journals + P-lines)  ← truth spine
```

**Run envelope (compose)**

* **backend** (FastAPI), **worker** (RQ), **frontend** (Streamlit), **postgres** (Timescale/Postgres), **redis**.
* `.env` keys: `DATABASE_URL`, `REDIS_URL`, `FMP_API_KEY`, `POLYGON_API_KEY`, `FRED_API_KEY`, `NEWSAPI_KEY`, `AUTH_JWT_SECRET`, `PRICING_POLICY=WM4PM_CAD`, `EXECUTOR_API_URL`, `CORS_ORIGINS`.

**Nightly job order (sacred)**
`build_pack → reconcile_ledger → compute_daily_metrics → prewarm_factors → mark_pack_fresh → evaluate_alerts`

> **Pack freshness gate**: Executor rejects "fresh" requests until pre-warm finishes.

**Health & Observability Components**

* `/health/pack` endpoint exposes pack freshness:
  ```json
  {
    "status": "warming|fresh|error",
    "pack_id": "2024-10-21-WM4PM-CAD",
    "updated_at": "2024-10-21T00:12:00Z",
    "prewarm_done": true|false,
    "is_fresh": true|false
  }
  ```

* **OpenTelemetry** tracing and **Prometheus** metrics enabled from **S1-W2**:
  - API latency histograms (labelled by `pattern_id`)
  - Pack build/pre-warm durations
  - Queue depth, DLQ size
  - Alert delivery latency

* **Sentry** for error tracking (no PII in error bodies)

**Implementation stub**:
```python
# api/health.py
@app.get("/health/pack")
def pack_health():
    pack = get_latest_pack()
    return {
        "status": "fresh" if pack.is_fresh else "warming",
        "pack_id": pack.id,
        "updated_at": pack.updated_at.isoformat(),
        "prewarm_done": pack.prewarm_done,
        "is_fresh": pack.is_fresh
    }
```

---

## 2) Data model (schemas & invariants)

**Invariants**

* All valuation/metric rows carry `pricing_pack_id`.
* Result traces carry `pricing_pack_id` + `ledger_commit_hash`.
* **RLS** on all portfolio-scoped tables (API sets `app.user_id`); RLS unit tests + IDOR fuzz in CI.
* **Timescale** hypertables: `portfolio_metrics`, `currency_attribution`, `factor_exposures` (+ continuous aggregates for rolling vol/betas).

**Tables (high-level)**

* `users`, `portfolios(user_id, base_ccy, benchmark_id, settings_json)`
* `securities(symbol, trading_currency, dividend_currency, domicile_country, type)`
* `lots(qty_open, trade_ccy, trade_fx_rate_id, cost_ccy, cost_per_unit_ccy, cost_base, trade_date)`
* `transactions(type, qty, price_ccy, price_base, fees_ccy/base, taxes_ccy/base, fx_rate_id, ts)`
* `pricing_pack(id, date, policy, sources_json, hash, superseded_by)`
* `prices(security_id, asof_date, close, currency, source, pricing_pack_id)`
* `fx_rates(asof_ts, base_ccy, quote_ccy, rate, source, policy, pricing_pack_id)`
* `portfolio_metrics(twr, mwr, vol, sharpe, beta, max_dd, base_ccy, pricing_pack_id)`
* `currency_attribution(local_ret, fx_ret, interaction_ret, pricing_pack_id)`
* `factor_exposures(betas_json, var_share_json, pricing_pack_id)`
* `macro_regime_snapshots(regime, probs_json, drivers_json)`
* `scenario_runs(scenario_id, deltas_json, pricing_pack_id)`
* `ratings(rating_type, value, inputs_json, method, pricing_pack_id)`
* `news_impact(article_id, entities_json, sentiment, impact_score)`
* `alerts(condition_json, notify_inapp/email)` + `notifications`
* `analytics_events` + `audit_log`

### Alerts Delivery Dedupe & DLQ

**Notifications Table** (dedupe):
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    alert_id UUID NOT NULL REFERENCES alerts(id),
    message TEXT NOT NULL,
    delivered_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Dedupe: max 1 notification per user/alert/day
    CONSTRAINT uq_notify_user_alert_day
        UNIQUE (user_id, alert_id, (date_trunc('day', delivered_at)))
);
```

**DLQ Table** (failed deliveries):
```sql
CREATE TABLE dlq_jobs (
    id UUID PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,  -- 'alert_delivery', 'pdf_render', etc.
    payload_json JSONB NOT NULL,
    attempts INT NOT NULL DEFAULT 0,
    last_error_at TIMESTAMP,
    last_error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Idempotency**: Workers use `idempotency_key = f"{user_id}:{alert_id}:{date}"` to prevent duplicates.

### Macro Cycle Tables (Optional, for S3)

**Cycle Definitions** (seeded):
```sql
CREATE TABLE macro_cycle_definitions (
    id VARCHAR(50) PRIMARY KEY,  -- 'short_term_debt', 'long_term_debt', 'empire'
    method_version VARCHAR(20) NOT NULL,  -- 'stdc_v1', 'ltdc_v1', 'empire_v1'
    indicators JSONB NOT NULL,  -- [{"id": "T10Y2Y", "weight": 0.35, "transform": "zscore"}, ...]
    phases JSONB NOT NULL  -- [{"label": "Expansion", "rules": {...}}, ...]
);
```

**Cycle Phase Snapshots** (computed nightly):
```sql
CREATE TABLE cycle_phase_snapshots (
    id UUID PRIMARY KEY,
    asof_date DATE NOT NULL,
    cycle_id VARCHAR(50) NOT NULL REFERENCES macro_cycle_definitions(id),
    phase_label VARCHAR(50) NOT NULL,  -- 'Expansion', 'Late', 'Deleveraging', 'Recovery'
    phase_score NUMERIC(10,4),
    drivers_json JSONB,  -- z-scores for each indicator
    confidence NUMERIC(3,2),  -- 0.0-1.0
    method_version VARCHAR(20) NOT NULL
);
```

**Empire Indicators** (seeded or fetched):
```sql
CREATE TABLE empire_indicators (
    asof_date DATE PRIMARY KEY,
    reserve_share NUMERIC(5,2),  -- % of global reserves
    share_world_gdp NUMERIC(5,2),  -- % of world GDP
    financial_center BOOLEAN,  -- dominant financial hub
    military_power NUMERIC(10,2),  -- composite index
    internal_order NUMERIC(3,2),  -- stability score 0-1
    innovation_rate NUMERIC(5,2),  -- patents, R&D % GDP
    composite_index NUMERIC(10,4)  -- weighted composite
);
```

---

## 3) Knowledge Graph (KG)

**Nodes**: Macro Variable, Regime, Factor (real rate, inflation, credit, FX), Sector, Company, Instrument, Pattern, SeriesID, Event (FOMC), **AnalysisSnapshot**.
**Edges**: `influences`, `sensitive_to`, `belongs_to`, `hedged_by`, `derived_from`, `computed_by`.
**Memory**: store each pattern **Result** as `AnalysisSnapshot` with edges to inputs (series, portfolio, pack), outputs and method/version.

---

## 4) Patterns (JSON) & capabilities (Python)

**Core patterns**

* `portfolio_overview` — positions → apply_pack → TWR → currency_attr → ratings.aggregate → charts.overview
* `holding_deep_dive` — fundamentals → ROE/margins/D/E → ratings.* → macro betas → risk contribution → news impact → explain
* `portfolio_macro_overview` — regime → factor_exposures → DaR → explain
* `portfolio_scenario_analysis` — positions → apply_pack → scenario_apply(shock) → charts.deltas → explain
* `buffett_checklist` — quality & moat scorecard (0–10) + explainer
* `news_impact_analysis` — news → entities → portfolio-weighted impact → optional alert
* `export_portfolio_report` — WeasyPrint PDF (rights registry gate)
* `policy_rebalance` — optimizer.propose_trades(policies, constraints) → trade diff + cost/TE
* `macro_trend_monitor` — regime trend → factor trend → suggest alert presets

**Capabilities (selected)**
`ledger.positions`, `pricing.apply_pack`, `metrics.compute_twr`, `metrics.currency_attribution`, `macro.classify_regime`, `macro.scenario_apply`, `risk.compute_dar`, `fundamentals.load(fmp)`, `corporate_actions.load(polygon)`, `ratings.dividend_safety|moat_strength|resilience`, `optimizer.propose_trades`, `news.search`, `reports.render_pdf`, `ai.explain`.

**Trace**
Every Result returns `{ pattern, agents, capabilities, sources, pricing_pack_id, ledger_commit_hash, per-panel asof/TTL, confidence }`.

### Cycles & Cycle-Aware Patterns

**macro_cycles_overview**:
- Computes and displays **Short-Term Debt Cycle**, **Long-Term Debt Cycle**, and **Empire** phases
- Returns: phase labels, scores, drivers (z-scores), timeline, confidence
- UI: Cycle cards with timeline visualization

**portfolio_cycle_risk**:
- Overlays cycle phases with portfolio factor exposures
- Produces macro-aware risk map (which factors amplify risk in current cycle phase)
- Pairs with `risk.compute_dar` for scenario stress testing

**cycle_deleveraging_scenarios**:
- Applies family of deleveraging shocks:
  - Money printing (inflationary)
  - Austerity (deflationary)
  - Default / spreads widening
- Returns: ΔP/L and hedge suggestions

**Pattern example**:
```json
{
  "id": "macro_cycles_overview",
  "name": "Macro Cycles Overview",
  "category": "economy",
  "steps": [
    {"capability": "cycles.compute_short_term", "as": "stdc"},
    {"capability": "cycles.compute_long_term", "as": "ltdc"},
    {"capability": "cycles.compute_empire", "as": "empire"},
    {"capability": "cycles.aggregate_overview", "as": "overview"}
  ],
  "outputs": ["overview"]
}
```

---

## 5) Providers & clients

**FMP Premium (fundamentals)** — profiles/financials/ratios; enforce bandwidth caps & **display/redistribution license** in **rights registry**.
**Polygon (prices/CA)** — `splits`, `dividends` for corporate actions; compute dividend-adjusted TR internally.
**FRED (macro)** — `series/observations` for curve/CPI/unemployment/spreads; cache & aggregate.
**NewsAPI** — portfolio-weighted news impact; **dev plan is delayed/non-prod**; use business tier for production; store metadata if license disallows text.

**Rate-limit & retry**
Token-bucket per provider; jittered exponential backoff; circuit breakers w/ half-open; DLQ for persistent failures; dedupe keys for notifications.

**Rights registry (YAML)**
Enforced in `reports.render_pdf` before export. Block or watermark if restricted; always append mandated attributions.

### Provider Governance (SLOs & Cost Controls)

**Sandbox/Prod Separation**:
- **Staging**: Uses provider sandboxes (FMP demo, Polygon test) or cached seeds
- **Production**: Uses licensed API keys from secrets manager

**Rate Limits & Cost**:
- **Token buckets**: 120 req/min (FMP), 100 req/min (Polygon), 60 req/min (NewsAPI)
- **Jittered exponential backoff**: Base 1s, max 60s, jitter ±20%
- **Circuit breakers**: 3 failures → OPEN (60s timeout)
- **FMP bandwidth window alarms**: Alert at 70% / 85% / 95% of monthly quota

**Rights Enforcement**:
- **Rights registry** loaded from YAML at startup (`/.ops/RIGHTS_REGISTRY.yaml`)
- Enforced by reports service in **staging from S1-W2** onward
- Blocks exports or applies watermarks per provider license

**Cost mitigation**:
- Bulk endpoints for FMP (multi-symbol quotes)
- Caching layer (Redis) with TTLs
- Budget alarms (PagerDuty) if approaching provider limits

**Implementation stub**:
```python
# core/circuit_breaker.py
class CircuitBreaker:
    def __init__(self, threshold=3, timeout=60):
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failures = 0
        self.threshold = threshold
        self.timeout = timeout
        self.opened_at = None

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.opened_at > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError()

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
            return result
        except ProviderError:
            self.failures += 1
            if self.failures >= self.threshold:
                self.state = "OPEN"
                self.opened_at = time.time()
            raise
```

---

## 6) Multi-currency & corporate actions (truth rules)

### ADR & Pay-Date FX (S1 Week-1 Gate)

**Critical invariant**: ADR dividends MUST be recorded with **pay-date FX** (not ex-date FX).

**Table schema**:
```sql
ALTER TABLE transactions ADD COLUMN pay_date DATE;
ALTER TABLE transactions ADD COLUMN pay_fx_rate_id UUID REFERENCES fx_rates(id);

ALTER TABLE transactions ADD CONSTRAINT dividend_pay_fx CHECK (
    NOT(type IN ('dividend','coupon') AND pay_fx_rate_id IS NULL)
);
```

**Acceptance gate (S1-W1)**:
- Golden test: AAPL ADR dividend (100 shares, $0.24/share)
  - Ex-date FX: 1.34 USD/CAD
  - Pay-date FX: 1.36 USD/CAD
  - Expected net CAD: $32.64 (not $32.16 if using ex-date)
  - Accuracy impact: **42¢ per transaction**
- Beancount reconciliation: ±1 basis point including ADR dividends

**Test fixture** (`/tests/golden/multi_currency/adr_paydate_fx.json`):
```json
{
  "symbol": "AAPL",
  "shares": 100,
  "dividend_per_share": 0.24,
  "ex_date": "2024-08-01",
  "pay_date": "2024-08-15",
  "ex_date_fx_usd_cad": 1.34,
  "pay_date_fx_usd_cad": 1.36,
  "gross_usd": 24.00,
  "gross_cad_correct": 32.64,
  "gross_cad_wrong_if_ex_date": 32.16,
  "accuracy_impact_cad": 0.48
}
```

### Multi-Currency Truth Rules

* **Valuation**: `P_base = P_local × FX(local→CAD)` (Pack rate).
* **Returns**: `r_base = (1+r_local)(1+r_fx) − 1` → store **local**, **fx**, **interaction**.
* **Realized P&L**: entry @ **entry FX** vs exit @ **exit FX**; show price vs FX split.
* **Dividends**: record **gross**, **withholding**, **net**; **pay-date FX** conversion (ADR-safe).
* **Splits**: use Polygon to adjust shares/costs; prices adjusted for splits (not dividends).
* **Benchmarks**: CAD unhedged & **hedged toggle** (shows hedge attribution impact).

---

## 7) Macro (Dalio) & quality (Buffett)

* **Regime**: infer from curve/CPI/unemployment/credit spreads (z-scores & probabilities).
* **Scenarios**: shocks on rates/CPI/USD → ΔP/L per holding via factor betas; list winners/losers & hedges.
* **DaR**: regime-conditioned covariance; walk-forward **calibration panel** (MAD vs realized drawdowns).
* **Ratings**: `dividend_safety` (payout/growth/FCF/net cash), `moat_strength`, `resilience`; **versioned inputs & method** for explainability.

---

## 8) Service Level Objectives (SLOs) & Observability

### Observability Timeline

**S1-W2 (Required)**:
- Minimal OTel/Prom/Sentry MUST be enabled
- Dashboards for:
  - API p95 latency by pattern
  - Pack build/pre-warm durations
  - Queue depth, DLQ size
  - Alert delivery latency

**S3** (Expand):
- Add DLQ monitoring (replay success rate, queue depth alerts)
- Add alert deduplication metrics (duplicates prevented/day)

**S4** (Polish):
- DaR calibration panel (MAD, hit rate)
- Cost dashboards (provider bandwidth, request counts)

### Performance SLOs
* **Warm p95 ≤ 1.2s** (pre-warmed pack, cached factors)
* **Cold p95 ≤ 2.0s** (pack warming in progress, banner shown to user)
* **Pack build completes by 00:15 local time** (nightly job deadline)

### Reliability SLOs
* **Alert median latency ≤ 60s** (from trigger to delivery)
* **Uptime: 99.5%** (excludes planned maintenance windows)

### Accuracy SLOs
* **Ledger vs DB reconciliation: ±1 basis point** (100% of portfolios)
* **Multi-currency attribution**: `r_base ≈ (1+r_local)(1+r_fx)-1 ±0.1bp`

### Sacred Nightly Job Order (Non-Negotiable)
```python
# jobs/scheduler.py - SACRED ORDER, DO NOT REORDER
@sched.scheduled_job("cron", hour=0, minute=5)
def nightly():
    """
    1. build_pack → Create immutable pricing snapshot
    2. reconcile_ledger → Validate vs Beancount ±1bp
    3. compute_daily_metrics → TWR, MWR, vol, Sharpe
    4. prewarm_factors → Factor fits, rolling stats
    5. prewarm_ratings → Buffett quality scores
    6. mark_pack_fresh → Enable executor freshness gate
    7. evaluate_alerts → Check conditions, dedupe, deliver
    """
    pack_id = build_pack()
    reconcile_ledger(pack_id)
    compute_daily_metrics(pack_id)
    prewarm_factors(pack_id)
    prewarm_ratings(pack_id)
    mark_pack_fresh(pack_id)
    evaluate_alerts()
```

### SLO Enforcement (Canary Deployment)
- Canary deployment (5% → 25% → 100%)
- Auto-rollback if warm p95 > 1.2s for > 30 minutes
- Prometheus alert → rollback hook

**Implementation stub** (executor freshness gate):
```python
# api/executor.py
@app.post("/v1/execute")
async def execute(req: ExecReq, user: User = Depends(get_current_user)):
    pack = get_latest_pack()

    if not pack.is_fresh and req.require_fresh:
        raise HTTPException(
            status_code=503,
            detail="Pricing pack warming in progress. Try again in a few minutes."
        )

    # ... continue with execution
```

---

## 9) Security & tenancy

* OAuth (Google/GitHub) → JWT bearer for `/v1/execute`.
* **RLS** on portfolio tables; IDOR fuzz tests in CI; minimal error bodies.
* Backups/day; ledger repo mirrored; monthly restore drill.

---

## 10) Sequencing (final)

### Week 0.5 (Foundation)
- **Terraform/Helm/ECS** manifests for staging + prod
- Database schema (25 tables, RLS policies, hypertables)
- `.security/THREAT_MODEL.md` (STRIDE analysis)
- **SAST/SCA** in CI (syft, grype, CodeQL)
- Pack health endpoint stub (`/health/pack` returns `{"status":"warming"}`)

**Acceptance**:
- [ ] Terraform apply succeeds for staging
- [ ] All 25 tables + RLS policies created
- [ ] SAST/SCA CI job green (no High/Critical vulns, no copyleft licenses)

---

### Sprint 1 Week 1: Truth Spine
- Provider integrators (FMP, Polygon, FRED, NewsAPI) with circuit breaker + rate limiting
- Pricing pack builder (nightly 00:05)
- Ledger reconciliation (nightly 00:10, ±1bp tolerance)
- **ADR/pay-date FX golden tests** (S1-W1 gate)
- Symbol normalization test (nightly mapping diff stub)

**Acceptance**:
- [ ] Circuit breaker engages after 3 failures (chaos test passes)
- [ ] Pricing pack builds successfully (immutability enforced)
- [ ] Ledger reconciliation ±1bp for all portfolios
- [ ] **ADR/pay-date FX golden test passes (42¢ accuracy validated)**

---

### Sprint 1 Week 2: Execution Path + Observability + Rights
- Executor API (`/v1/execute` with freshness gate)
- Pattern Orchestrator (DAG runner stub)
- **Observability skeleton** (OTel, Prom, Sentry) ← **MOVED FROM S3**
- **Rights gate enforcement (staging)** ← **MOVED FROM S4**
- Pack health endpoint wired (`/health/pack` returns real status)

**Acceptance**:
- [ ] Executor rejects requests when pack not fresh (503 error)
- [ ] OTel traces visible in Jaeger with `pricing_pack_id`, `ledger_commit_hash`, `pattern_id`
- [ ] Prometheus metrics scraped (API latency by pattern, pack build duration)
- [ ] **Rights gate blocks NewsAPI export in staging** ← **NEW GATE**
- [ ] Pack health endpoint returns `{"status":"fresh"}` after pre-warm

---

### Sprint 2 Week 3: Metrics + Currency Attribution
- TWR/MWR/Sharpe calculations
- Currency attribution (local/FX/interaction with ±0.1bp invariant)
- Continuous aggregates (30-day rolling vol, TimescaleDB)
- Property tests (currency identity, FX triangulation)

**Acceptance**:
- [ ] TWR matches Beancount ±1bp
- [ ] Currency attribution identity holds: `r_base ≈ (1+r_local)(1+r_fx)-1 ±0.1bp`
- [ ] Continuous aggregates update nightly

---

### Sprint 2 Week 4: UI + Backfill Rehearsal
- UI Portfolio Overview (Streamlit with DawsOS dark theme)
- Provenance badges (pack ID, ledger hash, asof timestamps)
- **Backfill/restatement rehearsal** (D0 → D1 supersede path) ← **NEW GATE**
- Visual regression tests (Playwright + Percy)

**Acceptance**:
- [ ] UI Overview renders with provenance badges
- [ ] **Backfill creates D0→D1 supersede chain with banner (no silent mutation)** ← **NEW GATE**
- [ ] Symbol normalization diff report generated (nightly)
- [ ] Visual regression snapshots stored (Percy baseline)

---

### Sprint 3 Week 5: Macro Regime + Cycles
- Regime detection (5 regimes: Early/Mid/Late Expansion, Early/Deep Contraction)
- **Macro cycles** (STDC, LTDC, Empire) ← **NEW**
- DaR calculation (scenario stress testing)
- Cycle cards UI (timeline visualization)

**Acceptance**:
- [ ] Regime detection works for 5 regimes
- [ ] **Macro cycles (STDC/LTDC/Empire) detect phases correctly** ← **NEW**
- [ ] DaR calculation runs for all portfolios (95% confidence)
- [ ] **Cycle cards render with drivers, timeline, confidence** ← **NEW**

---

### Sprint 3 Week 6: Alerts (DLQ + Dedupe) + News
- Alert evaluation (nightly 00:10)
- **DLQ + dedupe** (DB unique index + idempotency keys) ← **MOVED FROM S4**
- News impact (metadata-only for dev tier)
- Redis outage chaos test (alerts queue to DLQ, replay succeeds)

**Acceptance**:
- [ ] **Alerts deliver once per user/alert/day (dedupe enforced)** ← **NEW GATE**
- [ ] **DLQ replays failed notifications (hourly cron)** ← **NEW GATE**
- [ ] **Redis outage chaos test passes (alerts queue to DLQ, no dupes after replay)** ← **NEW**
- [ ] News panel shows metadata-only with dev plan notice

---

### Sprint 4 Week 7: Ratings + Optimizer
- Buffett quality (DivSafety, Moat, Resilience with 0-10 scale)
- Nightly pre-warm (00:08 for S&P 500 holdings)
- Optimizer (mean-variance with policy constraints)
- Rating method versioning (inputs_json for explainability)

**Acceptance**:
- [ ] Ratings compute correctly (0-10 scale, color-coded)
- [ ] Nightly pre-warm completes for all S&P 500 holdings
- [ ] Optimizer generates rebalance suggestions with TE limits

---

### Sprint 4 Week 8: Reporting + Polish
- PDF export (WeasyPrint with rights gate already enforced)
- DaR calibration view (MAD, hit rate)
- Hedged benchmark toggle
- Rights drills (FMP-only allowed, NewsAPI blocked)
- SLO validation (warm p95 ≤ 1.2s, cold p95 ≤ 2.0s)

**Acceptance**:
- [ ] PDF export includes attribution footers
- [ ] **Rights drills pass (FMP-only exports allowed, NewsAPI blocked)** ← **ALREADY ENFORCED IN S1-W2**
- [ ] DaR calibration view shows MAD and hit rate
- [ ] **SLO warm p95 ≤ 1.2s (load test passes)** ← **FINAL VALIDATION**
- [ ] **SLO cold p95 ≤ 2.0s (load test passes)** ← **FINAL VALIDATION**

---

## 11) Acceptance gates

**Reproducibility**:
- [ ] Same `pricing_pack_id` + `ledger_commit_hash` → identical results

**Accuracy**:
- [ ] Ledger vs DB ±1bp (100 portfolios, including ADR dividends with pay-date FX)
- [ ] Multi-currency attribution reconciles: `r_base ≈ (1+r_local)(1+r_fx)-1 ±0.1bp`

**Compliance**:
- [ ] Rights registry enforced (export drills pass in staging from S1-W2)
- [ ] RLS/IDOR fuzz tests 100% green in CI (no cross-user access)

**Performance**:
- [ ] Warm p95 < 1.2s, cold p95 < 2.0s (load tests pass)
- [ ] Pack build completes by 00:15 (nightly job deadline)

**Alerts**:
- [ ] Single delivery per user/alert/day (dedupe via DB unique index)
- [ ] Alert median latency < 60s (trigger to delivery)
- [ ] DLQ replay succeeds after provider/Redis recovery

**Security**:
- [ ] No secrets in code (vault/env only)
- [ ] Audit log for all mutations (portfolio, transactions, settings)
- [ ] SAST/SCA CI green (no High/Critical, no copyleft)

**Edge Cases**:
- [ ] ADR pay-date FX (golden test passes, ±1bp vs Beancount)
- [ ] Hedged benchmarks (currency-stripped return matches local return)
- [ ] Restatement banners (D0→D1 supersede path tested)

**Observability** ← **NEW GATE**:
- [ ] OTel traces include `pricing_pack_id`, `ledger_commit_hash`, `pattern_id`
- [ ] Prometheus histograms emit for API latency (by pattern), pack build, alert latency
- [ ] Dashboards display: p95 by pattern, pack build/pre-warm times, queue depth, DLQ size

**Backfill** ← **NEW GATE**:
- [ ] D0→D1 restatement rehearsal passes (banner shown, no silent mutation)
- [ ] Symbol normalization diff report generated nightly (override table ready)

---

## 12) Stress-test plan (break it on purpose)

1. **Retro CA restatement** (late split): prior pack → `superseded_by`; banner + optional restatement mode; no silent recompute.
2. **ADR dividends**: pay-date FX & withholding vs ledger ±1 bp (golden tests).
3. **T+2 across pack**: pending marker; no mixed state.
4. **Provider outage**: breaker trips; last-good per panel; backoff + DLQ; no crashes.
5. **9:30 herd**: 200 clients → warm p95 < 1.2s.
6. **Rights drills**: polygon-only/fmp-only exports blocked unless license present.
7. **DaR calibration**: walk-forward error display (MAD/hit rate).
8. **Symbol normalization**: nightly "mapping diff" report + override table.
9. **Pack health during warming**: `/health/pack` returns `{"status":"warming"}` → executor returns 503 → UI shows banner "Data warming, try again in X min".
10. **FMP bandwidth near cap**: Bulk request approaches monthly limit → fall back to cached seeds and queue off-peak fetch → alert triggered.

---

## 13) Implementation stubs (selected)

**Executor** (freshness gate)

```python
@app.post("/v1/execute")
async def execute(req: ExecReq, user=Depends(get_user_ctx)):
    ctx = RequestCtx.from_req(req, user)
    ctx.pricing_pack_id = resolve_pack(ctx.asof)
    if not packs.is_fresh(ctx.pricing_pack_id):
        raise HTTPException(503, "Pricing pack warming in progress")
    return await run_pattern(req.pattern_id, ctx, req.inputs)
```

**Pattern Orchestrator**

```python
async def run_pattern(pattern_id, ctx, inputs):
    spec = load_json(f"patterns/{pattern_id}.json")
    state, trace = {"ctx": ctx, "inputs": inputs}, Trace(pattern_id, ctx)
    for step in spec["steps"]:
        fn = CAPABILITIES[step["capability"]]
        out = await fn(ctx=ctx, state=state, **step.get("args", {}))
        state[step.get("as","last")] = out; trace.add_step(step["capability"], out)
    return {"data": {k: state.get(k) for k in spec.get("outputs", []) if k in state},
            "charts": state.get("charts", []), "trace": trace.serialize()}
```

**Metrics (TWR & currency attribution)**

```python
def twr(positions, pack_id):
    df = to_base_series(positions, pack_id)  # base-CCY series by holding
    pf = (df.pct_change().fillna(0) * df.weights).sum(axis=1)
    return {"twr": float((1+pf).prod()-1), "vol": float(pf.std()*np.sqrt(252)), "series": pf.round(8).to_dict()}

def currency_attribution(positions, pack_id):
    # r_base = (1+r_local)(1+r_fx)-1
    # aggregate across holdings by weights
    ...
```

**Macro (regime + scenario)**

```python
def classify_regime(asof):
    z = zscore_bundle({"curve": fred("T10Y2Y", asof), "cpi": fred("CPIAUCSL", asof),
                       "unemp": fred("UNRATE", asof), "baa10y": fred("BAA10Y", asof)})
    return {"label": map_to_regime(z), "probs": probs(z), "drivers": z}

def scenario_apply(positions, pack_id, shock):
    deltas = []
    for p in positions:
        betas = p.factor_betas(pack_id)  # real_rate, inflation, usd
        dp = (betas["real_rate"]*shock.get("rates_bps",0)/10000.0
              + betas["inflation"]*shock.get("cpi_surprise_pct",0)
              + betas["usd"]*shock.get("usd_vs_cad_pct",0)) * p.value_base(pack_id)
        deltas.append({"symbol": p.symbol, "delta_pl": float(dp)})
    return {"delta_table": deltas, "summary": sum(d["delta_pl"] for d in deltas)}
```

**Reports (rights gate)**

```python
def portfolio_pdf(ctx, data, charts):
    providers = trace_providers(data, charts)
    rights.ensure_allowed(providers, export_type="pdf")
    html = render("portfolio_report.html", data=data, charts=charts,
                  footer=f"Pack:{ctx.pricing_pack_id} • Ledger:{ctx.ledger_commit_hash} • {now_iso()}")
    return weasyprint.HTML(string=html).write_pdf()
```

**Jobs (ordering)**

```python
@sched.scheduled_job("cron", hour=0, minute=5)
def nightly():
    pack = build_pack()
    reconcile_ledger()
    compute_daily_metrics(pack)
    prewarm_factors(pack)
    mark_pack_fresh(pack)
    evaluate_alerts()
```

---

## 14) DawsOS UI Design Overview

**Design goal**: modern, professional **dark-themed** decision analytics UI with high trust, high legibility, and fast scannability for financial users.

### 14.1 Color palette & theming

**CSS variables (tailwind config / globals.css)**

```css
:root {
  --graphite: hsl(220, 13%, 9%);     /* Primary dark background */
  --slate: hsl(217, 12%, 18%);        /* Secondary surfaces/cards */
  --signal-teal: hsl(180, 100%, 32%); /* Primary accent (CTAs/actions) */
  --electric-blue: hsl(217, 78%, 56%);/* Secondary accent (highlights) */
  --provenance-purple: hsl(264, 67%, 48%); /* Evidence/provenance */
  --alert-amber: hsl(42, 100%, 55%);  /* Warnings */
  --risk-red: hsl(0, 75%, 60%);       /* Errors/danger */
}

.dark {
  --bg: var(--graphite);
  --card: var(--slate);
  --fg: hsl(220, 10%, 96%);
  --muted: hsl(220, 10%, 60%);
}
```

**Dark mode architecture**

* Tailwind + class-based dark mode (`class` strategy).
* `<ThemeProvider>` manages `dark` class on `<html>`; persist in `localStorage`.
* Smooth transitions: `transition-colors duration-300`.

### 14.2 Typography

* **Sans**: Inter (primary), system fallbacks (`font-display: swap`).
* **Monospace**: IBM Plex Mono (numbers, code, metrics).
* **Hierarchy**:

  * Hero: `text-4xl md:text-6xl`
  * Section: `text-2xl md:text-3xl`
  * Card titles: `text-xl`
  * Body: `text-base leading-relaxed`
  * Captions/meta: `text-sm text-muted`

### 14.3 Layout system

* **Container**: `max-w-7xl mx-auto px-6`
* **Section vertical rhythm**: `py-16 md:py-20`
* **Grids**:

  * 2-col for medium screens (`md:grid-cols-2`)
  * 3-col feature grids on large (`lg:grid-cols-3`)
  * Responsive breakpoints: `md(768px)`, `lg(1024px)`, `xl(1280px)`

### 14.4 Component architecture

**Navigation (fixed top)**

* Backdrop blur + translucent slate bar.
* Brand: **DawsOS** (icon + wordmark).
* Horizontal menu (≈8 links) on desktop; hamburger w/ slide-down on mobile.
* Theme toggle (sun/moon).
* **CTA** "Book a Demo" in **Signal Teal**.

**Cards**

* Rounded (`rounded-lg xl:rounded-xl 2xl:rounded-2xl`), subtle borders (`border border-white/10`).
* Background `bg-[color:var(--card)] shadow-sm`.
* Hover: border accent transition (teal/blue).
* Icon container: brand color @ 20% opacity.

**Buttons**

* **Primary**: bg **Signal Teal**, `text-white`, hover `opacity-90`, `active:scale-[0.98]`, `rounded-lg`.
* **Secondary**: border-2 **Electric Blue**, transparent background; hover fills blue.
* **Ghost/Text**: no bg; colored text + underline on hover.

**Icons**

* Lucide React; nav `w-5 h-5`, features `w-6 h-6`; colored by brand palette; in rounded icon chips.

### 14.5 Visual patterns

**Gradient border utility**

```css
.gradient-border { background: linear-gradient(90deg, var(--signal-teal), var(--electric-blue)); }
```

**Evidence glow**

```css
.evidence-glow { box-shadow: 0 0 20px hsla(180, 100%, 32%, 0.3); }
```

**Status pulse**

```css
@keyframes pulse-gentle { 0%,100%{opacity:1} 50%{opacity:0.7} }
.slo-indicator { animation: pulse-gentle 2s infinite; }
```

### 14.6 Page-specific designs

**Hero (marketing/landing)**

* `min-h-screen`, large gradient headings, 2-column (copy + visual), dual CTAs.

**Feature tiles**

* 3-4 column grid; icon + title + description; hover border accent; consistent spacing.

**Pricing cards**

* Transparent card w/ border; **monospace** for price; color-coded tiers.

**Causal Path Demo**

* Interactive flow (arrows between nodes); color-coded node states; **Provenance Purple** accents for evidence links.

### 14.7 Application screens (product)

**Portfolio Overview (home)**

* **Top band**: Portfolio name, base CCY, benchmark toggle (**Hedged/Unhedged**), last pack ID, ledger hash; small per-panel staleness chips.
* **KPI ribbon** (monospace): TWR, MWR, Vol, Max-DD, Sharpe — each with sparkline.
* **Alloc & risk**: Allocation pies/bar; concentration top-10; **currency attribution donut** (local/FX/interaction).
* **Holdings table**: symbol, name, value, weight, P/L, **ratings badges** (DivSafety/Moat/Resilience), Risk contrib; sticky header; column filters.
* **Explain drawer**: `pattern_id`, `pricing_pack_id`, `ledger_commit_hash`, `sources`, per-panel `asof`/TTL.
* **Playbooks**: contextual suggestions (weight cap, hedge add).

**Holding Deep-Dive**

* Tabs: **Overview** (fundamentals, ROE/margins/D/E), **Valuation** (DCF snapshot), **Macro** (factor betas, scenario ΔP/L), **Ratings** (components and provenance), **News** (portfolio-weighted impact).

**Macro**

* **Regime card**: label + drivers (z-scores) + probs.
* **Factor exposures**: bars w/ variance share chips.
* **DaR**: gauge + factor contribution waterfall.
* **Trend**: WoW changes in regime probability/betas.

**Scenarios**

* Presets (Rates +50bp / USD+5% / CPI +0.4%) + **Custom** (JSON builder).
* **ΔP/L table** & winners/losers; **hedge ideas** with estimated effect.

**Alerts**

* Table of conditions (normalized JSON rendered as human text); create/edit forms; delivery history.
* **"Alerts that mattered"** panel: outcomes 1/5/20-day vs suggested action.

**Reports**

* Generate portfolio/holding PDF; **rights gate** with provider attributions; pack/commit IDs in footer.

### 14.8 Accessibility

* Focus rings: 2px **Signal Teal** with offset (`focus:ring-2 ring-offset-2`).
* Color contrast: WCAG AA.
* Keyboard navigation: full support; skip-links.
* ARIA: labels for icon-only buttons (theme toggle, explain).
* Screen reader text: `.sr-only` helper.

### 14.9 Performance

* Lazy load below fold; route-level code splitting; responsive images `srcset`; WOFF2 + preload; Tailwind purge.

### 14.10 Component library

* **shadcn/ui** primitives, themed to DawsOS palette (Dialog, Modal, Tabs, Accordion, Form controls, Toast, Tooltip).
* **Design tokens** correspond to CSS vars; exported to Tailwind config.

---

## 15) UI → API mapping (no drift)

| UI Element        | Pattern                           | Outputs it expects                                     | Notes                                              |
| ----------------- | --------------------------------- | ------------------------------------------------------ | -------------------------------------------------- |
| Overview KPIs     | `portfolio_overview`              | `perf_strip`, `currency_attr`, `rating_badges`, charts | Requires `pricing_pack_id` & panel `asof` in trace |
| Deep-Dive Ratings | `buffett_checklist` + `ratings.*` | `scorecard`, `flags`, `components`                     | Show method/version + inputs                       |
| Macro Regime      | `portfolio_macro_overview`        | `regime_card`, `factor_bars`, `dar_widget`             | Display z-scores & probs                           |
| Scenario Tool     | `portfolio_scenario_analysis`     | `delta_table`, `winners_losers`                        | Hedge suggestions                                  |
| Alerts            | `alerts.*`                        | list & notifications                                   | JSON normalized conditions                         |
| Report Export     | `export_portfolio_report`         | PDF bytes                                              | Rights gate must pass                              |

---

## 16) CI/CD & coding standards

* **Tooling**: `black`, `ruff`, `isort`, `mypy`, `pytest`; pre-commit hooks.
* **Tests**: unit (capabilities/importers), property (currency identities), golden (ledger ±1 bp), integration (patterns), chaos (provider failures), RLS/IDOR fuzz.
* **Feature flags**: env/DB toggles per pattern/service.
* **Migrations**: Alembic; forward/back compatible; blue/green if needed.

---

## 17) Open items (must close before code freeze)

**P0**

* Provider **rights registry enforcement** in reports (block/watermark + attributions).
* **Pack freshness gate** in Executor; job ordering check.
* **Per-panel staleness** (provider + `asof` + TTL chip on every chart).

**P1**

* ADR **pay-date FX & withholding** normalization + tests.
* **Symbol normalization** (FIGI master, nightly mapping diff + override table).
* Alerts **DLQ + dedupe** (message keys + DB unique constraints).
* **DaR calibration** panel (walk-forward error metrics).

---

## 18) Done-criteria (Go/No-Go)

* Reproducible numbers (same pack/commit → same output).
* Beancount vs metrics ±1 bp daily.
* Rights gate blocks/annotates correctly.
* Warm p95 < 1.2 s, cold < 2.0 s.
* Alerts delivered once, median < 60 s, DLQ drains.
* RLS/IDOR CI green.
* Edge-cases: ADR/pay-date FX; hedged/unhedged; restatement banners.

---

### Appendix: Example snippets

**Rights registry (YAML)**

```yaml
FMP:      { export: restricted, require_license: true,  attribution: "Financial data © FMP" }
Polygon:  { export: restricted, require_license: true,  attribution: "© Polygon.io" }
FRED:     { export: allow,      require_license: false, attribution: "Source: FRED®" }
NewsAPI:  { export: restricted, require_license: true,  attribution: "News metadata via NewsAPI.org" }
```

**Alert condition JSON**

```json
{"type":"macro","entity":"VIX","metric":"level","op":">","value":30,"window":"intraday","notify":{"inapp":true,"email":true},"cooldown_min":15}
```

**Scenario preset**

```json
{"id":"late_cycle_rates_up","shocks":{"rates_bps":50,"usd_vs_cad_pct":0.05,"cpi_surprise_pct":0.004}}
```

**Policy spec**

```json
{
  "policies":[
    {"name":"DivSafetyCap","rule":{"type":"rating","metric":"dividend_safety","op":"<","value":6},
     "action":{"cap_weight_pct":5}},
    {"name":"MoatBias","rule":{"type":"rating","metric":"moat_strength","op":">=","value":8},
     "action":{"min_weight_pct_total":20}}
  ],
  "constraints":{"max_te_pct":2,"max_turnover_pct":10,"min_lot_value":500}
}
```

---

**Final word** — Keep the **ledger + pack** spine sacred, route all work through **patterns**, enforce **rights/freshness/staleness**, and render with the **DawsOS UI** system above. This is the blueprint to build, test, and ship an auditable, pro-grade portfolio intelligence product without drift.
