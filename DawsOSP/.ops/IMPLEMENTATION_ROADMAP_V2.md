# DawsOS Implementation Roadmap v2.0

**Status**: Ready to Build
**Date**: 2025-10-21
**Version**: 2.0 (Feedback incorporated)
**Duration**: 8 weeks (Phase 0 + 4 sprints)
**Team Size**: 8-10 FTEs

---

## Executive Summary

This roadmap delivers a **production-ready portfolio intelligence platform** in 8 weeks through phased delivery:

- **Phase 0** (Week 0.5): Infrastructure, security, observability skeleton, rights stub
- **Sprint 1** (Weeks 1-2): Truth spine (ledger + pack + reconcile) + execution path + observability + rights gate
- **Sprint 2** (Weeks 3-4): Metrics + UI + data backfill rehearsal
- **Sprint 3** (Weeks 5-6): Macro (regime + cycles) + alerts (DLQ/dedupe) + news
- **Sprint 4** (Weeks 7-8): Ratings + optimizer + reporting + polish

**Critical Path**: Provider integration → Pack build → Reconciliation → Metrics → Macro → Ratings → Optimizer

**v2.0 Changes from v1.0**:
1. ✅ Observability skeleton moved to S1-W2 (from S3)
2. ✅ Rights enforcement moved to S1-W2 (from S4)
3. ✅ ADR/pay-date FX golden tests added to S1-W1
4. ✅ DLQ + dedupe moved to S3-W6 (from S4)
5. ✅ Macro cycles (STDC/LTDC/Empire) added to S3
6. ✅ Infra-as-code (Terraform/Helm/ECS) added to Phase 0
7. ✅ SBOM/SCA/SAST added to Phase 0 CI
8. ✅ Backfill rehearsal added to S2-W4
9. ✅ Visual regression tests added to S2-W4
10. ✅ CI gates explicit (property, golden, chaos, RLS, visual)

---

## Resource Allocation (RACI)

| Role | Phase 0 | S1 | S2 | S3 | S4 | Total FTE |
|------|---------|-----|-----|-----|-----|-----------|
| **Infra (DevOps/SRE)** | 1.0 + 0.5 | 0.5 | 0.5 | 0.5 + 0.5 | 0.5 | 2.0 |
| **Backend Engineers** | 0.5 | 2.0 | 1.0 | 2.0 | 2.0 | 3.0 |
| **Data Engineer** | 0.5 | 1.0 | 0.5 | 0.5 | 0.5 | 1.5 |
| **Frontend Engineer** | - | - | 1.0 | 0.5 | 1.0 | 1.0 |
| **QA/SET** | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 1.0 |
| **Product Manager** | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 |

**Total Team**: 8.0-10.0 FTEs (peak in S1/S3/S4)

**RACI**:
- **Orchestrator** (Product Manager): Owns gates, sprint planning, acceptance sign-off
- **Layer Architects** (Backend Leads): Own acceptance artifacts, integration tests
- **DevOps** (SRE): Owns infra, observability, CI/CD, runbooks
- **QA** (SET): Owns test strategy, golden tests, chaos tests, visual regression

---

## Phase 0: Foundation (Week 0.5, Days 1-3)

**Owner**: DevOps + Backend Lead
**Goal**: Production-ready infrastructure, security baseline, observability skeleton, rights stub

### Deliverables

#### 1. Infrastructure as Code
- **Terraform modules** (`infra/terraform/`):
  - `db/` — PostgreSQL + TimescaleDB (RDS or self-hosted)
  - `cache/` — Redis cluster (ElastiCache or self-hosted)
  - `storage/` — S3 buckets (reports, backups, DLQ)
  - `secrets/` — AWS Secrets Manager or HashiCorp Vault
  - `network/` — VPC, subnets, security groups
  - `waf/` — AWS WAF or CloudFlare rules
  - `monitoring/` — Prometheus, Jaeger, Alertmanager (ECS or k8s)

- **Helm charts** (if Kubernetes) (`infra/helm/dawsos/`):
  - `values-staging.yaml`
  - `values-prod.yaml`
  - `templates/` (backend, worker, ui, postgres, redis)

- **ECS task definitions** (if AWS ECS) (`infra/ecs/`):
  - `backend-task.json`
  - `worker-task.json`
  - `ui-task.json`

**Commands**:
```bash
cd infra/terraform/
terraform init
terraform plan -var-file=staging.tfvars
terraform apply -var-file=staging.tfvars

# Verify
terraform output db_endpoint
terraform output redis_endpoint
```

#### 2. Database Schema + RLS
- **Migrations** (`backend/migrations/`):
  - `001_create_users_portfolios.sql`
  - `002_create_securities_lots_transactions.sql`
  - `003_create_pricing_pack_fx_rates.sql`
  - `004_create_metrics_hypertables.sql`
  - `005_create_rls_policies.sql`
  - `006_create_indexes.sql`

- **RLS Policies** (14 portfolio-scoped tables):
  ```sql
  CREATE POLICY portfolio_isolation ON portfolios
    USING (user_id = current_setting('app.user_id')::uuid);

  CREATE POLICY portfolio_holdings_isolation ON lots
    USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id = current_setting('app.user_id')::uuid));
  ```

- **Hypertables** (TimescaleDB):
  ```sql
  SELECT create_hypertable('portfolio_metrics', 'date', chunk_time_interval => INTERVAL '1 month');
  SELECT create_hypertable('currency_attribution', 'date', chunk_time_interval => INTERVAL '1 month');
  SELECT create_hypertable('factor_exposures', 'date', chunk_time_interval => INTERVAL '1 month');
  ```

**Commands**:
```bash
export DATABASE_URL="postgresql://..."
alembic upgrade head

# Verify
psql $DATABASE_URL -c "\dt"  # 25 tables
psql $DATABASE_URL -c "SELECT tablename FROM pg_policies WHERE policyname LIKE '%isolation%';"  # 14 RLS policies
```

#### 3. Security Baseline
- **Threat Model** (`.security/THREAT_MODEL.md`):
  - STRIDE analysis (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation)
  - Attack tree (RLS bypass, JWT forging, SQL injection, export data exfiltration)
  - Mitigations mapped to controls

- **SBOM/SCA/SAST in CI** (`.github/workflows/security.yml`):
  ```yaml
  - name: Generate SBOM
    run: syft . -o spdx-json > sbom.json

  - name: License compliance (no copyleft)
    run: ort analyze -i sbom.json --deny-list GPL,AGPL,SSPL

  - name: Vulnerability scan
    run: grype sbom:./sbom.json --fail-on high

  - name: SAST (CodeQL)
    uses: github/codeql-action/analyze@v2
  ```

- **RLS Fuzz Baseline** (`tests/security/test_rls_fuzz.py`):
  ```python
  @pytest.mark.parametrize("user_a_jwt,user_b_portfolio_id", generate_fuzz_pairs(100))
  def test_rls_blocks_cross_portfolio_access(user_a_jwt, user_b_portfolio_id):
      response = client.get(f"/v1/portfolios/{user_b_portfolio_id}", headers={"Authorization": f"Bearer {user_a_jwt}"})
      assert response.status_code == 403
  ```

#### 4. Rights Registry Stub
- **Registry YAML** (`.ops/RIGHTS_REGISTRY.yaml`):
  ```yaml
  providers:
    FMP:
      name: Financial Modeling Prep
      allows_display: true
      allows_export_pdf: true
      allows_export_csv: true
      allows_redistribution: false
      attribution_text: "Data provided by Financial Modeling Prep (financialmodelingprep.com)"

    Polygon:
      name: Polygon.io
      allows_display: true
      allows_export_pdf: true
      allows_export_csv: true
      allows_redistribution: false
      attribution_text: "Market data provided by Polygon.io"

    FRED:
      name: Federal Reserve Economic Data
      allows_display: true
      allows_export_pdf: true
      allows_export_csv: true
      allows_redistribution: true  # Public domain
      attribution_text: "Economic data from Federal Reserve Economic Data (FRED)"

    NewsAPI:
      name: NewsAPI
      allows_display: true
      allows_export_pdf: false  # Requires Enterprise license
      allows_export_csv: false
      allows_redistribution: false
      attribution_text: "News data from NewsAPI.org"
  ```

- **Loader** (`backend/app/core/rights_registry.py`):
  ```python
  def load_rights_registry() -> dict:
      with open(".ops/RIGHTS_REGISTRY.yaml") as f:
          return yaml.safe_load(f)

  def ensure_allowed(providers: list[str], export_type: str = "pdf") -> tuple[bool, list[str]]:
      """Returns (allowed, blocked_providers)."""
      registry = load_rights_registry()
      blocked = []
      for provider in providers:
          rules = registry["providers"].get(provider)
          if not rules or not rules.get(f"allows_export_{export_type}"):
              blocked.append(provider)
      return (len(blocked) == 0, blocked)
  ```

#### 5. Pack Health Endpoint
- **Endpoint** (`backend/app/api/health.py`):
  ```python
  @app.get("/health/pack")
  def pack_health():
      latest_pack = get_latest_pack()
      if not latest_pack:
          return {"status": "error", "message": "No packs found"}

      if latest_pack.superseded_by:
          return {"status": "error", "message": "Latest pack superseded (late CA restatement)"}

      if latest_pack.is_fresh:
          return {"status": "fresh", "pack_id": latest_pack.id, "asof": latest_pack.date}
      else:
          return {"status": "warming", "pack_id": latest_pack.id, "asof": latest_pack.date}
  ```

**Test**:
```bash
curl https://staging.dawsos.internal/health/pack
# Expected: {"status": "warming", "pack_id": "...", "asof": "2024-10-21"}
```

### Acceptance Gates (Phase 0)

- [ ] **Terraform apply** succeeds for staging (DB, Redis, S3, Secrets, Monitoring)
- [ ] **Database migrations** run successfully (25 tables, 14 RLS policies, 3 hypertables)
- [ ] **RLS fuzz baseline** passes (100 cross-portfolio access attempts blocked)
- [ ] **Rights registry** loads successfully; `ensure_allowed()` returns correct allow/deny
- [ ] **Pack health endpoint** returns `{"status": "warming"}` (no packs yet)
- [ ] **SBOM/SCA/SAST** CI passes (no High/Critical vulns, no copyleft licenses)
- [ ] **Threat model** documented with STRIDE analysis

---

## Sprint 1: Truth Spine + Execution Path + Observability + Rights (Weeks 1-2)

**Owner**: Backend Lead + Data Engineer + DevOps
**Goal**: Ledger reconciliation (±1bp), pricing pack build, execution path, observability skeleton, rights gate enforcement

### Week 1: Ledger + Pack + Reconciliation

#### Deliverables

1. **Provider Integrator** (`backend/app/services/providers/`)
   - `fmp_client.py` — Prices, fundamentals (circuit breaker, rate limit)
   - `polygon_client.py` — Corporate actions (splits, dividends)
   - `fred_client.py` — Macro indicators (T10Y2Y, UNRATE, CPIAUCSL)
   - `newsapi_client.py` — News search (metadata-only for dev)

   **Circuit Breaker**:
   ```python
   class CircuitBreaker:
       def __init__(self, failure_threshold=3, timeout=60):
           self.state = "CLOSED"
           self.failures = 0
           self.threshold = failure_threshold
           self.timeout = timeout

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

2. **Pricing Pack Builder** (`backend/app/services/pricing_pack.py`)
   - **Nightly job** (00:05 local time):
     ```python
     @scheduler.scheduled_job("cron", hour=0, minute=5)
     def build_nightly_pack():
         symbols = get_all_portfolio_symbols()
         prices = fetch_prices_bulk(symbols)  # FMP bulk endpoint
         fx_rates = fetch_fx_rates(["USD/CAD", "EUR/CAD", "GBP/CAD", ...])  # FRED

         pack_id = create_pack(date.today(), prices, fx_rates)
         mark_pack_fresh(pack_id, is_fresh=False)  # Warming flag

         logger.info(f"Pack {pack_id} created, warming in progress")
     ```

   - **Immutability enforcement**:
     ```python
     class PricingPack(BaseModel):
         id: uuid.UUID
         date: date
         prices: dict  # Immutable (frozen)
         fx_rates: dict  # Immutable (frozen)
         hash: str  # SHA-256 of prices + fx_rates
         superseded_by: uuid.UUID | None = None

         def __setattr__(self, name, value):
             if name in ["prices", "fx_rates", "hash"]:
                 raise ImmutabilityViolationError(f"Cannot modify {name}")
             super().__setattr__(name, value)
     ```

3. **Ledger Reconciliation** (`backend/app/jobs/reconcile_ledger.py`)
   - **Nightly job** (00:10 local time):
     ```python
     @scheduler.scheduled_job("cron", hour=0, minute=10)
     def reconcile_ledger():
         portfolios = get_all_portfolios()

         for portfolio in portfolios:
             db_valuation = compute_portfolio_valuation(portfolio.id, latest_pack_id())
             ledger_balance = get_beancount_balance(portfolio.name, date.today())

             diff = abs(db_valuation - ledger_balance)
             tolerance = ledger_balance * 0.0001  # 1bp

             if diff > tolerance:
                 logger.error(f"Reconciliation FAILED for {portfolio.name}: {diff:.2f} > {tolerance:.2f}")
                 create_alert("Ledger reconciliation failed", portfolio.id, diff)
             else:
                 logger.info(f"Reconciliation PASSED for {portfolio.name}: {diff:.2f} bp")

             store_reconciliation_result(portfolio.id, db_valuation, ledger_balance, diff)
     ```

4. **ADR/Pay-Date FX Golden Tests** (`tests/golden/multi_currency/adr_paydate_fx.json`)
   - **Golden fixture**:
     ```json
     {
       "description": "Apple ADR dividend with pay-date FX",
       "symbol": "AAPL",
       "dividend_per_share": 0.24,
       "ex_date": "2024-08-01",
       "pay_date": "2024-08-15",
       "ex_date_fx_usd_cad": 1.34,
       "pay_date_fx_usd_cad": 1.36,
       "shares": 100,
       "gross_usd": 24.00,
       "gross_cad_correct": 32.64,
       "gross_cad_wrong_if_ex_date_fx": 32.16,
       "accuracy_impact_cad": 0.48
     }
     ```

   - **Test**:
     ```python
     def test_adr_paydate_fx_golden():
         golden = load_golden("multi_currency/adr_paydate_fx.json")

         result = compute_dividend_conversion(
             gross_usd=golden["gross_usd"],
             pay_date=golden["pay_date"],
             target_ccy="CAD"
         )

         assert abs(result.gross_cad - golden["gross_cad_correct"]) <= 0.01
         assert result.fx_rate_used == golden["pay_date_fx_usd_cad"]
     ```

5. **Symbol Normalization Test** (`tests/integration/test_symbol_normalization.py`)
   - **Nightly mapping diff** (stub for now):
     ```python
     def test_symbol_normalization_noop():
         """Verify symbol normalization doesn't mutate existing holdings."""
         holdings = get_all_holdings()
         normalized = [normalize_symbol(h.symbol) for h in holdings]
         assert holdings == normalized  # No changes yet
     ```

### Week 2: Execution Path + Observability + Rights Gate

#### Deliverables

1. **Executor API** (`backend/app/api/executor.py`)
   - **Freshness gate**:
     ```python
     @app.post("/v1/execute")
     async def execute(req: ExecReq, user: User = Depends(get_current_user)):
         pack = get_latest_pack()

         if not pack.is_fresh and req.require_fresh:
             raise PackNotFreshError("Pricing pack warming in progress. Try again in a few minutes.")

         ctx = ExecutorContext(
             user_id=user.id,
             pricing_pack_id=pack.id,
             ledger_commit_hash=get_ledger_commit(),
             timestamp=datetime.now(timezone.utc)
         )

         # Set RLS context
         db.execute(f"SET app.user_id = '{user.id}'")

         result = orchestrator.execute(req.pattern_id, req.params, ctx)
         return result
     ```

2. **Pattern Orchestrator** (`backend/app/core/orchestrator.py`)
   - **DAG runner** (stub):
     ```python
     def execute(pattern_id: str, params: dict, ctx: ExecutorContext) -> Result:
         pattern = load_pattern(pattern_id)

         trace_steps = []
         start = time.time()

         for step in pattern["steps"]:
             step_start = time.time()
             step_result = run_step(step, params, ctx)
             trace_steps.append({
                 "name": step["name"],
                 "duration_ms": (time.time() - step_start) * 1000
             })

         duration_ms = (time.time() - start) * 1000

         return Result(
             pattern_id=pattern_id,
             data=step_result,
             provenance={
                 "pricing_pack_id": ctx.pricing_pack_id,
                 "ledger_commit_hash": ctx.ledger_commit_hash,
                 "sources": extract_sources(trace_steps)
             },
             trace=trace_steps,
             execution_time_ms=duration_ms
         )
     ```

3. **Observability Skeleton** (`backend/app/core/telemetry.py`)
   - **OpenTelemetry setup**:
     ```python
     from opentelemetry import trace
     from opentelemetry.exporter.jaeger.thrift import JaegerExporter
     from opentelemetry.sdk.trace import TracerProvider
     from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

     tracer_provider = TracerProvider(
         resource=Resource.create({"service.name": "dawsos-backend"})
     )
     trace.set_tracer_provider(tracer_provider)

     jaeger_exporter = JaegerExporter(
         agent_host_name="jaeger",
         agent_port=6831
     )
     tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

     FastAPIInstrumentor.instrument_app(app)
     ```

   - **Prometheus metrics**:
     ```python
     from prometheus_client import Histogram, Counter

     API_LATENCY = Histogram(
         "http_request_duration_seconds",
         "API request latency",
         ["endpoint", "pattern_id"]
     )

     PACK_BUILD_DURATION = Histogram(
         "pricing_pack_build_duration_seconds",
         "Pack build duration"
     )

     RECONCILIATION_DIFF = Histogram(
         "ledger_reconciliation_diff_bp",
         "Reconciliation difference in basis points",
         ["portfolio_id"]
     )

     @app.post("/v1/execute")
     async def execute(req: ExecReq, user: User = Depends(get_current_user)):
         with API_LATENCY.labels(endpoint="/execute", pattern_id=req.pattern_id).time():
             result = orchestrator.execute(req.pattern_id, req.params, ctx)
         return result
     ```

   - **Sentry error tracking**:
     ```python
     import sentry_sdk
     sentry_sdk.init(
         dsn=os.getenv("SENTRY_DSN"),
         environment="staging",
         traces_sample_rate=0.1
     )
     ```

4. **Rights Gate Enforcement** (`backend/app/api/reports.py`)
   - **Export PDF with rights check**:
     ```python
     @app.post("/v1/portfolios/{portfolio_id}/export/pdf")
     async def export_pdf(portfolio_id: uuid.UUID, user: User = Depends(get_current_user)):
         data = fetch_portfolio_data(portfolio_id)
         providers = extract_providers(data)

         allowed, blocked = ensure_allowed(providers, "pdf")
         if not allowed:
             raise RightsViolationError(
                 f"Export blocked: {', '.join(blocked)} data cannot be exported. "
                 f"Remove restricted analysis or upgrade license."
             )

         pdf_bytes = generate_pdf(data, providers)
         return Response(content=pdf_bytes, media_type="application/pdf")
     ```

   - **Test**:
     ```python
     def test_rights_gate_blocks_newsapi_export():
         portfolio = create_test_portfolio_with_news()

         response = client.post(f"/v1/portfolios/{portfolio.id}/export/pdf")

         assert response.status_code == 403
         assert "NewsAPI" in response.json()["detail"]
     ```

### Acceptance Gates (Sprint 1)

- [ ] **Provider integrators** fetch data successfully (FMP, Polygon, FRED)
- [ ] **Circuit breaker** engages after 3 failures (chaos test passes)
- [ ] **Pricing pack** builds nightly at 00:05 (immutability enforced)
- [ ] **Ledger reconciliation** passes ±1bp for all portfolios
- [ ] **ADR/pay-date FX** golden test passes (42¢ accuracy)
- [ ] **Executor API** rejects requests when pack not fresh
- [ ] **Observability**: OTel traces visible in Jaeger, Prometheus metrics scraped
- [ ] **Rights gate**: PDF export blocked for NewsAPI data (staging)
- [ ] **Pack health endpoint** returns `{"status": "fresh"}` after pre-warm

---

## Sprint 2: Metrics + UI + Backfill Rehearsal (Weeks 3-4)

**Owner**: Backend Engineer + Frontend Engineer + QA
**Goal**: Portfolio metrics (TWR/MWR/Sharpe), UI Overview/Deep-Dive, backfill rehearsal, visual regression tests

### Week 3: Metrics + Currency Attribution

#### Deliverables

1. **Metrics Service** (`backend/app/services/metrics.py`)
   - **TWR calculation**:
     ```python
     def compute_twr(portfolio_id: uuid.UUID, start_date: date, end_date: date, pack_id: uuid.UUID) -> float:
         lots = get_lots(portfolio_id)
         transactions = get_transactions(portfolio_id, start_date, end_date)

         nav_series = []
         for d in date_range(start_date, end_date):
             prices = get_pack_prices(pack_id, d)
             nav = sum(lot.qty * prices[lot.security_id] for lot in lots)
             nav_series.append(nav)

         # Geometric linking
         twr = 1.0
         for i in range(1, len(nav_series)):
             daily_ret = (nav_series[i] - nav_series[i-1]) / nav_series[i-1]
             twr *= (1 + daily_ret)

         return twr - 1.0
     ```

2. **Currency Attribution** (`backend/app/services/currency_attribution.py`)
   - **Decomposition**:
     ```python
     def compute_currency_attribution(portfolio_id: uuid.UUID, pack_id: uuid.UUID) -> CurrencyAttribution:
         holdings = get_holdings(portfolio_id)

         local_ret = 0.0
         fx_ret = 0.0

         for holding in holdings:
             local_r = holding.price_change_local / holding.price_start_local
             fx_r = holding.fx_rate_end / holding.fx_rate_start - 1.0

             local_ret += holding.weight * local_r
             fx_ret += holding.weight * fx_r

         interaction_ret = sum(
             holding.weight * (local_r * fx_r)
             for holding in holdings
         )

         # Verify invariant: r_base ≈ (1+r_local)(1+r_fx) - 1
         base_ret = compute_twr(portfolio_id, start_date, end_date, pack_id)
         expected_base = (1 + local_ret) * (1 + fx_ret) - 1

         assert abs(base_ret - expected_base) <= 0.0001  # ±0.1bp

         return CurrencyAttribution(
             local_ret=local_ret,
             fx_ret=fx_ret,
             interaction_ret=interaction_ret,
             base_ret=base_ret
         )
     ```

3. **Continuous Aggregates (TimescaleDB)**
   - **Rolling 30-day volatility**:
     ```sql
     CREATE MATERIALIZED VIEW portfolio_metrics_30d_vol
     WITH (timescaledb.continuous) AS
     SELECT
       portfolio_id,
       time_bucket('1 day', date) AS bucket,
       stddev(twr) OVER (PARTITION BY portfolio_id ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS vol_30d
     FROM portfolio_metrics
     GROUP BY portfolio_id, bucket;
     ```

4. **Property Tests** (`tests/property/test_currency_identity.py`)
   - **Currency triangulation**:
     ```python
     @given(
         amount_usd=st.floats(min_value=1.0, max_value=1e6),
         usd_cad=st.floats(min_value=1.0, max_value=2.0),
         cad_eur=st.floats(min_value=0.5, max_value=1.5)
     )
     def test_fx_triangulation_identity(amount_usd, usd_cad, cad_eur):
         """Verify USD → CAD → EUR === USD → EUR (via cross-rate)."""
         amount_cad = amount_usd * usd_cad
         amount_eur_via_cad = amount_cad * cad_eur

         usd_eur_cross = usd_cad * cad_eur
         amount_eur_direct = amount_usd * usd_eur_cross

         assert abs(amount_eur_via_cad - amount_eur_direct) <= 0.01  # ±1¢
     ```

### Week 4: UI Overview + Backfill Rehearsal

#### Deliverables

1. **UI Portfolio Overview** (`ui/screens/portfolio_overview.py`)
   - **Streamlit implementation**:
     ```python
     import streamlit as st
     from ui.components.dawsos_theme import apply_dawsos_theme, metric_card

     def render_portfolio_overview(portfolio_id: str):
         apply_dawsos_theme()

         result = client.execute("portfolio_overview", {"portfolio_id": portfolio_id})

         # Header with provenance
         col1, col2 = st.columns([2, 1])
         with col1:
             st.title(result.data["portfolio_name"])
         with col2:
             st.markdown(f"""
             <div class="provenance-chip">
                 Pack: {result.provenance.pricing_pack_id[:8]} |
                 Ledger: {result.provenance.ledger_commit_hash[:7]}
             </div>
             """, unsafe_allow_html=True)

         # KPI Ribbon
         kpi_cols = st.columns(5)
         metrics = result.data["perf_strip"]

         with kpi_cols[0]:
             metric_card("TWR (YTD)", f"{metrics['twr']:.2%}")
         with kpi_cols[1]:
             metric_card("MWR", f"{metrics['mwr']:.2%}")
         with kpi_cols[2]:
             metric_card("Vol (Ann.)", f"{metrics['vol']:.2%}")
         with kpi_cols[3]:
             metric_card("Max DD", f"{metrics['max_dd']:.2%}")
         with kpi_cols[4]:
             metric_card("Sharpe", f"{metrics['sharpe']:.2f}")
     ```

2. **Backfill Rehearsal** (`backend/jobs/backfill_packs.py`)
   - **Tool**:
     ```python
     def backfill_packs(start_date: date, end_date: date):
         """
         Backfill pricing packs for historical dates.
         Marks D0 pack as superseded, creates D1 pack.
         """
         for d in date_range(start_date, end_date):
             if pack_exists(d):
                 logger.info(f"Pack for {d} already exists, skipping")
                 continue

             prices = fetch_historical_prices(d)
             fx_rates = fetch_historical_fx(d)

             pack_id = create_pack(d, prices, fx_rates)
             logger.info(f"Created backfill pack {pack_id} for {d}")
     ```

   - **Restatement path test**:
     ```python
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

3. **Visual Regression Tests** (`tests/visual/test_overview_screenshots.py`)
   - **Playwright + Percy**:
     ```python
     from playwright.sync_api import sync_playwright
     from percy import percy_snapshot

     def test_portfolio_overview_visual():
         with sync_playwright() as p:
             browser = p.chromium.launch()
             page = browser.new_page()
             page.goto("https://staging.dawsos.internal/portfolio/123")

             # Wait for metrics to load
             page.wait_for_selector(".metric-card")

             # Take snapshot
             percy_snapshot(browser, page, "Portfolio Overview")

             browser.close()
     ```

### Acceptance Gates (Sprint 2)

- [ ] **TWR/MWR** calculations match Beancount ±1bp
- [ ] **Currency attribution** identity holds: `r_base ≈ (1+r_local)(1+r_fx) - 1 ± 0.1bp`
- [ ] **Continuous aggregates** (30-day vol) update nightly
- [ ] **Property tests** pass (FX triangulation, currency identity)
- [ ] **UI Overview** renders with provenance badges (pack ID, ledger hash)
- [ ] **Backfill rehearsal** completes successfully (D0 → D1 supersede path works)
- [ ] **Restatement banner** appears for superseded packs
- [ ] **Visual regression** snapshots stored (Percy baseline)

---

## Sprint 3: Macro (Regime + Cycles) + Alerts (DLQ/Dedupe) + News (Weeks 5-6)

**Owner**: Backend Lead + Data Engineer + DevOps
**Goal**: Dalio cycles (STDC/LTDC/Empire), regime detection, DaR, alerts with DLQ/dedupe, news impact

### Week 5: Macro Regime + Cycles

#### Deliverables

1. **Macro Service** (`backend/app/services/macro.py`)
   - **Regime detection** (5 regimes):
     ```python
     def detect_regime(indicators: dict) -> Regime:
         """
         Classify regime based on Dalio framework.
         Regimes: Early Expansion, Mid Expansion, Late Expansion, Early Contraction, Deep Contraction
         """
         t10y2y = indicators["T10Y2Y"]
         unrate = indicators["UNRATE"]
         cpi = indicators["CPIAUCSL"]

         # Z-scores
         z_yield_curve = zscore(t10y2y)
         z_unemployment = zscore(unrate)
         z_inflation = zscore(cpi)

         if z_yield_curve > 0 and z_unemployment < 0:
             return Regime.EARLY_EXPANSION
         elif z_yield_curve > 0 and z_inflation > 0:
             return Regime.MID_EXPANSION
         elif z_yield_curve <= 0 and z_inflation > 1:
             return Regime.LATE_EXPANSION
         elif z_yield_curve < 0 and z_unemployment > 0:
             return Regime.EARLY_CONTRACTION
         else:
             return Regime.DEEP_CONTRACTION
     ```

2. **Macro Cycles** (`backend/app/services/cycles.py`)
   - **STDC/LTDC/Empire indicators** (`storage/macro_cycles/cycle_definitions.json`):
     ```json
     {
       "cycles": [
         {
           "id": "short_term_debt",
           "method_version": "stdc_v1",
           "indicators": [
             {"id": "T10Y2Y", "weight": 0.35, "transform": "zscore"},
             {"id": "UNRATE", "weight": 0.25, "transform": "zscore"},
             {"id": "CPIAUCSL", "weight": 0.25, "transform": "zscore"},
             {"id": "BAA10Y", "weight": 0.15, "transform": "zscore"}
           ],
           "phases": [
             {"label": "Expansion", "rules": {"T10Y2Y": ">0", "UNRATE": "down"}},
             {"label": "Late", "rules": {"T10Y2Y": "<=0"}},
             {"label": "Deleveraging", "rules": {"UNRATE": "up"}},
             {"label": "Recovery", "rules": {"UNRATE": "down"}}
           ]
         },
         {
           "id": "long_term_debt",
           "method_version": "ltdc_v1",
           "indicators": [
             {"id": "GFDEGDQ188S", "weight": 0.40, "transform": "zscore"},
             {"id": "MORTGAGE30US", "weight": 0.30, "transform": "zscore"},
             {"id": "DEXCHUS", "weight": 0.30, "transform": "zscore"}
           ]
         },
         {
           "id": "empire",
           "method_version": "empire_v1",
           "indicators": [
             {"id": "DEXCHUS", "weight": 0.50, "transform": "zscore"},
             {"id": "SOFR", "weight": 0.30, "transform": "zscore"},
             {"id": "VIX", "weight": 0.20, "transform": "zscore"}
           ]
         }
       ]
     }
     ```

   - **Cycle detector**:
     ```python
     def detect_cycle_phase(cycle_id: str, indicators: dict) -> CyclePhase:
         cycle_def = load_cycle_definition(cycle_id)

         # Compute composite score
         score = 0.0
         for ind in cycle_def["indicators"]:
             value = indicators[ind["id"]]
             transformed = apply_transform(value, ind["transform"])
             score += ind["weight"] * transformed

         # Match phase
         for phase in cycle_def["phases"]:
             if match_rules(phase["rules"], indicators):
                 return CyclePhase(
                     cycle_id=cycle_id,
                     label=phase["label"],
                     score=score,
                     drivers=extract_drivers(indicators, cycle_def["indicators"])
                 )
     ```

3. **DaR (Drawdown at Risk)** (`backend/app/services/risk.py`)
   - **Scenario stress testing**:
     ```python
     def compute_dar(portfolio_id: uuid.UUID, scenarios: list[Scenario], confidence=0.95) -> float:
         """
         Compute Drawdown at Risk (DaR) at 95% confidence.
         Returns maximum drawdown under worst 5% of scenarios.
         """
         results = []
         for scenario in scenarios:
             delta_pl = apply_scenario(portfolio_id, scenario)
             results.append(delta_pl)

         # Sort descending (worst scenarios first)
         results.sort()

         # p5 threshold
         idx = int(len(results) * (1 - confidence))
         dar = results[idx]

         return dar
     ```

4. **DaR Calibration View** (stub for now):
   ```python
   def render_dar_calibration(portfolio_id: uuid.UUID):
       """
       Show walk-forward DaR calibration (MAD, hit rate).
       TODO: Implement in Sprint 4.
       """
       st.info("DaR calibration view coming in Sprint 4")
   ```

### Week 6: Alerts (DLQ + Dedupe) + News

#### Deliverables

1. **Alert Service** (`backend/app/services/alerts.py`)
   - **Condition evaluation** (nightly):
     ```python
     @scheduler.scheduled_job("cron", hour=0, minute=10)
     def evaluate_alerts():
         alerts = get_active_alerts()

         for alert in alerts:
             condition = alert.condition_json

             if evaluate_condition(condition):
                 # Check cooldown
                 last_fired = get_last_fired(alert.id)
                 if last_fired and (datetime.now() - last_fired) < timedelta(hours=24):
                     logger.info(f"Alert {alert.id} in cooldown, skipping")
                     continue

                 # Send notification
                 send_notification(alert)

                 # Mark as fired
                 mark_fired(alert.id, datetime.now())
     ```

2. **DLQ (Dead Letter Queue)** (`backend/app/jobs/dlq_replay.py`)
   - **Failed notification handler**:
     ```python
     def send_notification(alert: Alert):
         try:
             if alert.notify_email:
                 send_email(alert.user.email, alert.message)
             if alert.notify_inapp:
                 create_inapp_notification(alert.user_id, alert.message)
         except Exception as e:
             logger.error(f"Notification failed for alert {alert.id}: {e}")
             dlq_push(alert)  # Send to DLQ for retry
     ```

   - **DLQ replay** (hourly):
     ```python
     @scheduler.scheduled_job("cron", minute=0)
     def replay_dlq():
         messages = dlq_pop_batch(limit=100)

         for msg in messages:
             try:
                 send_notification(msg.alert)
                 dlq_ack(msg.id)
             except Exception as e:
                 logger.error(f"DLQ replay failed for {msg.id}: {e}")
                 dlq_nack(msg.id)  # Back to DLQ
     ```

3. **Deduplication** (`backend/app/db/models/notifications.py`)
   - **Unique constraint**:
     ```sql
     CREATE TABLE notifications (
       id UUID PRIMARY KEY,
       user_id UUID NOT NULL,
       alert_id UUID NOT NULL,
       message TEXT NOT NULL,
       delivered_at TIMESTAMP NOT NULL,

       CONSTRAINT notifications_dedupe UNIQUE (user_id, alert_id, delivered_at::date)
     );
     ```

   - **Idempotency key** (for workers):
     ```python
     def send_notification(alert: Alert):
         idempotency_key = f"{alert.id}:{datetime.now().date()}"

         # Check if already delivered today
         if notification_exists(idempotency_key):
             logger.info(f"Notification {idempotency_key} already delivered, skipping")
             return

         # Send
         send_email(alert.user.email, alert.message)

         # Record
         create_notification(alert, idempotency_key)
     ```

4. **News Impact** (`backend/app/services/news.py`)
   - **Dev plan label** (metadata-only, 24h delay):
     ```python
     def fetch_news(symbol: str) -> list[NewsArticle]:
         articles = newsapi_client.search(symbol, from_date=date.today() - timedelta(days=2))

         # For dev tier: metadata only, no full text
         return [
             NewsArticle(
                 title=a["title"],
                 url=a["url"],
                 published_at=a["publishedAt"],
                 sentiment=None,  # Requires paid tier
                 impact_score=None  # Requires paid tier
             )
             for a in articles
         ]
     ```

   - **Panel with dev plan notice**:
     ```python
     st.subheader("News Impact (Dev Plan)")
     st.warning("Metadata-only, 24h delay. Upgrade to Enterprise for real-time sentiment analysis.")

     for article in news:
         st.markdown(f"- [{article.title}]({article.url}) ({article.published_at})")
     ```

### Acceptance Gates (Sprint 3)

- [ ] **Regime detection** works for 5 regimes (Early/Mid/Late Expansion, Early/Deep Contraction)
- [ ] **Macro cycles** (STDC/LTDC/Empire) detect phases correctly
- [ ] **DaR** calculation runs for all portfolios (95% confidence)
- [ ] **Cycle cards** render with drivers, timeline, confidence
- [ ] **Alerts** deliver once (dedupe enforced via unique constraint)
- [ ] **DLQ** replays failed notifications (hourly)
- [ ] **Redis outage** chaos test passes (alerts queue to DLQ, replay succeeds)
- [ ] **News** panel shows metadata-only with dev plan notice

---

## Sprint 4: Ratings + Optimizer + Reporting + Polish (Weeks 7-8)

**Owner**: Backend Lead + Frontend Engineer + DevOps
**Goal**: Buffett quality ratings, mean-variance optimizer, PDF exports with rights, DaR calibration, polish

### Week 7: Ratings + Optimizer

#### Deliverables

1. **Ratings Service** (`backend/app/services/ratings.py`)
   - **Buffett quality framework**:
     ```python
     def compute_dividend_safety(symbol: str, pack_id: uuid.UUID) -> float:
         """
         DivSafety score (0-10 scale).
         Components: Payout ratio (30%), FCF coverage (35%), growth streak (20%), net cash (15%)
         """
         fundamentals = fetch_fundamentals(symbol, pack_id)

         # 1. Payout ratio (lower is better, < 50% ideal)
         payout_ratio = fundamentals["dividendsPaid"] / fundamentals["netIncome"]
         payout_score = 10.0 if payout_ratio < 0.3 else max(0, 10 - (payout_ratio - 0.3) * 20)

         # 2. FCF coverage (higher is better, > 2x ideal)
         fcf_coverage = fundamentals["freeCashFlow"] / fundamentals["dividendsPaid"]
         fcf_score = min(10.0, fcf_coverage * 3)

         # 3. Growth streak (years of consecutive dividend growth)
         growth_streak = compute_growth_streak(symbol)
         streak_score = min(10.0, growth_streak)

         # 4. Net cash (positive is good, negative is bad)
         net_cash = fundamentals["cashAndEquivalents"] - fundamentals["totalDebt"]
         cash_score = 10.0 if net_cash > 0 else 5.0

         # Weighted average
         div_safety = (
             0.30 * payout_score +
             0.35 * fcf_score +
             0.20 * streak_score +
             0.15 * cash_score
         )

         return round(div_safety, 1)
     ```

   - **Moat & Resilience** (similar structure):
     ```python
     def compute_moat_strength(symbol: str, pack_id: uuid.UUID) -> float:
         # ROE consistency, gross margin, intangibles, switching costs
         pass

     def compute_resilience(symbol: str, pack_id: uuid.UUID) -> float:
         # D/E, interest coverage, current ratio, margin stability
         pass
     ```

   - **Nightly pre-warm** (00:08 local time):
     ```python
     @scheduler.scheduled_job("cron", hour=0, minute=8)
     def prewarm_ratings():
         symbols = get_sp500_symbols()
         pack_id = latest_pack_id()

         for symbol in symbols:
             div_safety = compute_dividend_safety(symbol, pack_id)
             moat = compute_moat_strength(symbol, pack_id)
             resilience = compute_resilience(symbol, pack_id)

             store_rating(symbol, pack_id, "dividend_safety", div_safety)
             store_rating(symbol, pack_id, "moat_strength", moat)
             store_rating(symbol, pack_id, "resilience", resilience)

         logger.info(f"Pre-warmed ratings for {len(symbols)} symbols")
     ```

2. **Optimizer Service** (`backend/app/services/optimizer.py`)
   - **Mean-variance optimization** (Riskfolio-Lib):
     ```python
     import riskfolio as rp

     def optimize_portfolio(portfolio_id: uuid.UUID, constraints: dict) -> OptimizerResult:
         """
         Mean-variance optimization with policy constraints.
         Constraints: sector limits, single-name caps, quality floors, TE limits
         """
         holdings = get_holdings(portfolio_id)

         # Fetch returns (historical)
         returns = fetch_returns(holdings, lookback_days=252)

         # Build portfolio object
         port = rp.Portfolio(returns=returns)
         port.assets_stats(method_mu="hist", method_cov="hist")

         # Apply constraints
         # 1. Sector limits (e.g., Tech <= 30%)
         for sector, limit in constraints.get("sector_limits", {}).items():
             sector_symbols = get_sector_symbols(sector)
             port.ainequality = f"sum({sector_symbols}) <= {limit}"

         # 2. Single-name caps (e.g., any single stock <= 10%)
         port.upperlng = constraints.get("single_name_cap", 0.10)

         # 3. Quality floors (e.g., Moat >= 6)
         quality_floor = constraints.get("quality_floor", {})
         if quality_floor:
             eligible_symbols = [
                 s for s in holdings
                 if get_rating(s, "moat_strength") >= quality_floor.get("moat", 0)
             ]
             port.assetslist = eligible_symbols

         # Optimize
         weights = port.optimization(model="Classic", rm="MV", obj="Sharpe")

         # Compute tracking error vs current
         current_weights = {h.symbol: h.weight for h in holdings}
         te = tracking_error(current_weights, weights)

         # Generate trade diff
         trades = generate_trade_diff(current_weights, weights)

         return OptimizerResult(
             weights=weights,
             expected_return=port.mu.T @ weights,
             expected_vol=np.sqrt(weights.T @ port.cov @ weights),
             sharpe=port.sharpe,
             tracking_error=te,
             trades=trades
         )
     ```

3. **Rating Method Versioning** (`backend/app/db/models/ratings.py`)
   - **Versioned inputs**:
     ```python
     class Rating(Base):
         __tablename__ = "ratings"

         id = Column(UUID, primary_key=True)
         symbol = Column(String, nullable=False)
         pricing_pack_id = Column(UUID, ForeignKey("pricing_packs.id"))
         rating_type = Column(String, nullable=False)  # "dividend_safety", "moat_strength", "resilience"
         value = Column(Numeric(3, 1), nullable=False)  # 0-10 scale
         method_version = Column(String, nullable=False)  # "div_safety_v1"
         inputs_json = Column(JSON, nullable=False)  # {"payout_ratio": 0.35, "fcf_coverage": 3.2, ...}
     ```

   - **Explainer**:
     ```python
     def explain_rating(rating_id: uuid.UUID) -> dict:
         rating = get_rating(rating_id)

         return {
             "symbol": rating.symbol,
             "type": rating.rating_type,
             "value": rating.value,
             "method": rating.method_version,
             "inputs": rating.inputs_json,
             "component_scores": decompose_rating(rating)
         }
     ```

### Week 8: Reporting + Polish

#### Deliverables

1. **PDF Exporter** (`backend/app/services/reporting.py`)
   - **Full implementation** (from REPORTING_ARCHITECT spec):
     ```python
     def generate_portfolio_pdf(portfolio_id: uuid.UUID, ctx: ExecutorContext) -> bytes:
         data = fetch_portfolio_data(portfolio_id, ctx)
         providers = extract_providers(data)

         # Rights gate
         allowed, blocked = ensure_allowed(providers, "pdf")
         if not allowed:
             raise RightsViolationError(f"Export blocked: {', '.join(blocked)}")

         # Attribution text
         attribution = get_attribution_text(providers)

         # Render HTML
         html = render_template("portfolio_summary.html",
             portfolio=data,
             footer={
                 "attribution": attribution,
                 "pricing_pack_id": ctx.pricing_pack_id,
                 "ledger_commit_hash": ctx.ledger_commit_hash,
                 "generated_at": datetime.now(timezone.utc).isoformat()
             }
         )

         # Generate PDF
         pdf_bytes = HTML(string=html).write_pdf(stylesheets=[CSS(filename="dawsos_pdf.css")])

         return pdf_bytes
     ```

2. **Hedged Benchmark** (`backend/app/services/benchmarks.py`)
   - **Toggle for currency hedging**:
     ```python
     def compute_benchmark_return(benchmark_id: str, hedged: bool = False) -> float:
         if not hedged:
             return get_benchmark_return(benchmark_id)

         # If hedged, strip out FX return
         local_return = get_benchmark_local_return(benchmark_id)
         return local_return
     ```

3. **DaR Calibration View** (`ui/screens/dar_calibration.py`)
   - **MAD (Mean Absolute Deviation) & hit rate**:
     ```python
     def render_dar_calibration(portfolio_id: uuid.UUID):
         calibration = compute_dar_calibration(portfolio_id, lookback_days=252)

         st.subheader("DaR Calibration (Walk-Forward)")

         col1, col2 = st.columns(2)
         with col1:
             st.metric("MAD (Mean Absolute Deviation)", f"{calibration.mad:.2%}")
         with col2:
             st.metric("Hit Rate (95% threshold)", f"{calibration.hit_rate:.1%}")

         st.line_chart(calibration.actual_vs_forecast)
     ```

4. **Rights Drills** (final validation):
   ```python
   def test_rights_drill_fmp_only():
       """Verify FMP-only export allowed."""
       portfolio = create_test_portfolio(providers=["FMP"])
       pdf = export_pdf(portfolio.id)
       assert "FMP" in extract_attribution(pdf)

   def test_rights_drill_newsapi_blocked():
       """Verify NewsAPI export blocked."""
       portfolio = create_test_portfolio(providers=["FMP", "NewsAPI"])
       with pytest.raises(RightsViolationError, match="NewsAPI"):
           export_pdf(portfolio.id)
   ```

5. **Performance SLO Validation**:
   ```python
   def test_slo_warm_p95_under_1200ms():
       """Verify warm p95 latency ≤ 1.2s."""
       results = load_test(endpoint="/v1/portfolios/123/valuation", users=100, duration=300)

       p95 = results.percentile(0.95)
       assert p95 <= 1200, f"SLO breach: p95 {p95}ms > 1200ms"

   def test_slo_cold_p95_under_2000ms():
       """Verify cold p95 latency ≤ 2.0s."""
       # Clear cache, force cold start
       clear_cache()

       results = load_test(endpoint="/v1/portfolios/123/valuation", users=50, duration=180)

       p95 = results.percentile(0.95)
       assert p95 <= 2000, f"SLO breach: p95 {p95}ms > 2000ms"
   ```

### Acceptance Gates (Sprint 4)

- [ ] **Ratings** (DivSafety, Moat, Resilience) compute correctly (0-10 scale)
- [ ] **Rating method versioning** works (inputs_json stored for explainability)
- [ ] **Nightly pre-warm** completes for all S&P 500 holdings
- [ ] **Optimizer** generates rebalance suggestions with TE limits
- [ ] **PDF export** includes rights attribution footers
- [ ] **Rights drills** pass (FMP-only allowed, NewsAPI blocked)
- [ ] **Hedged benchmark** toggle impacts currency attribution
- [ ] **DaR calibration** view shows MAD and hit rate
- [ ] **SLO warm p95** ≤ 1.2s (load test passes)
- [ ] **SLO cold p95** ≤ 2.0s (load test passes)

---

## Cross-Phase CI Gates (Merge-Only-On-Green)

### Test Matrix (All PRs)

1. **Unit Tests** (≥ 95% coverage)
   - Core modules (metrics, currency, ledger): ≥ 98%
   - Services (pricing_pack, ratings, optimizer): ≥ 95%
   - API endpoints: ≥ 90%

2. **Property Tests** (Hypothesis)
   - Currency identity: `r_base ≈ (1+r_local)(1+r_fx) - 1 ± 0.1bp`
   - FX triangulation: `USD→CAD→EUR === USD→EUR (cross-rate)`
   - Pricing pack immutability: No mutations allowed

3. **Golden Tests** (Byte-for-byte match)
   - ADR/pay-date FX: 42¢ accuracy (AAPL example)
   - Attribution calculation: AAPL Oct 2023 (±1bp tolerance)
   - Regime detection: Dot-com bubble, 2008 crisis, 2020 COVID
   - Buffett ratings: KO, WMT, JNJ quality scores

4. **Integration Tests**
   - Ledger reconciliation: ±1bp for all portfolios
   - Pricing pack build: All currencies + ADR dividends
   - Alert delivery: Cooldown + deduplication
   - PDF export: Rights gate enforcement

5. **Security Tests**
   - RLS/IDOR fuzz: 100+ cross-portfolio access attempts blocked
   - SQL injection: Parameterized query validation
   - JWT validation: Expiry, signature, claims
   - Secret scanning: No hardcoded credentials

6. **Chaos Tests**
   - Provider outage: Circuit breaker engages after 3 failures
   - Database failover: < 5s downtime recovery
   - Cache eviction: Redis → DB fallback
   - Pack build during market hours: Stale pack served with banner

7. **Visual Tests** (Playwright + Percy)
   - Portfolio Overview: KPIs, allocations, holdings table
   - Holdings Deep-Dive: Fundamentals, ratings, macro, news
   - Macro Dashboard: Regime card, factor exposures, DaR

---

## Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Rights enforcement late** | Medium | High | Moved to S1-W2; rights drills & tests; YAML overrides |
| **ADR/pay-date FX drift** | Medium | High | Added golden tests S1-W1; fixtures; reconciliation gates |
| **Observability late → perf unknown** | Medium | High | OTel/Prom in S1-W2; dashboards; perf budgets |
| **Alerts storms** | Medium | Medium | DLQ + dedupe S3-W6; global cooldown; playbook |
| **Provider costs (FMP BW)** | Medium | Medium | Bulk endpoints; caching; budget alarms; sandbox keys |
| **Cycles mis-specified** | Low | Medium | Versioned JSON methods; ADR for changes; seed snapshots |
| **Backfill restatement messy** | Medium | Medium | Rehearsal S2-W4; banners; no silent mutate |
| **Symbol normalization drift** | Low | Medium | Nightly mapping diff; override table; governance |
| **Macro cycles missing** | Medium | High | Added to S3; patterns + seeds; cycle cards in UI |
| **DLQ/dedupe late** | Medium | High | Moved to S3-W6; unique constraint; idempotency keys |

---

## Critical Path Dependencies

```
Phase 0 (Infra)
    │
    ├──> DB + RLS + Hypertables + Seeds
    ├──> Terraform/Helm/ECS
    ├──> Rights registry stub
    ├──> Pack health endpoint
    └──> SBOM/SCA/SAST CI
         │
         ▼
S1-W1 (Pack + Ledger)
    │
    ├──> Provider integrators (FMP, Polygon, FRED)
    ├──> Circuit breaker
    ├──> Pack build (nightly 00:05)
    ├──> Ledger reconciliation (nightly 00:10, ±1bp)
    └──> ADR/pay-date FX golden tests
         │
         ▼
S1-W2 (Execution + Observability + Rights)
    │
    ├──> Executor API (/v1/execute)
    ├──> Freshness gate
    ├──> OTel + Prom + Sentry (observability skeleton)
    ├──> Rights gate (staging)
    └──> Pack health endpoint wired
         │
         ▼
S2-W3 (Metrics)
    │
    ├──> TWR/MWR/Sharpe
    ├──> Currency attribution (local/FX/interaction)
    ├──> Continuous aggregates (30-day vol)
    └──> Property tests (FX triangulation)
         │
         ▼
S2-W4 (UI + Backfill)
    │
    ├──> UI Overview (Streamlit)
    ├──> Provenance display (pack ID, ledger hash)
    ├──> Backfill rehearsal (D0 → D1 supersede path)
    └──> Visual regression tests (Percy)
         │
         ▼
S3-W5 (Macro + Cycles)
    │
    ├──> Regime detection (5 regimes)
    ├──> Macro cycles (STDC/LTDC/Empire)
    ├──> DaR (scenario stress testing)
    └──> Cycle cards (UI)
         │
         ▼
S3-W6 (Alerts + News)
    │
    ├──> Alert evaluation (nightly 00:10)
    ├──> DLQ + dedupe
    ├──> News impact (metadata-only for dev)
    └──> Chaos tests (Redis outage → DLQ replay)
         │
         ▼
S4-W7 (Ratings + Optimizer)
    │
    ├──> Buffett quality (DivSafety, Moat, Resilience)
    ├──> Nightly pre-warm (00:08)
    ├──> Optimizer (mean-variance with constraints)
    └──> Rating method versioning
         │
         ▼
S4-W8 (Reporting + Polish)
    │
    ├──> PDF export (rights gate enforced)
    ├──> DaR calibration view (MAD, hit rate)
    ├──> Hedged benchmark toggle
    ├──> Rights drills (FMP-only, NewsAPI blocked)
    └──> SLO validation (warm p95 ≤ 1.2s, cold p95 ≤ 2.0s)
```

---

## Final Checklist (Ready to Build v2.0)

### Phase 0 Additions
- [x] Terraform/Helm/ECS files (infra-as-code)
- [x] Threat model (.security/THREAT_MODEL.md)
- [x] CI SAST/SCA (syft, grype, CodeQL)
- [x] RLS fuzz baseline (tests/security/test_rls_fuzz.py)
- [x] Rights registry YAML + loader stub
- [x] Pack health endpoint stub

### S1 Additions
- [x] Observability skeleton moved to S1-W2 (OTel, Prom, Sentry)
- [x] Rights gate moved to S1-W2 (staging enforcement)
- [x] ADR/pay-date FX golden tests added to S1-W1
- [x] Freshness gate wired to pack health endpoint
- [x] Symbol normalization test (nightly mapping diff stub)

### S2 Additions
- [x] Continuous aggregates (30-day vol, TimescaleDB)
- [x] Property tests (FX triangulation, currency identity)
- [x] Backfill rehearsal added to S2-W4
- [x] Visual regression tests added to S2-W4 (Playwright + Percy)

### S3 Additions
- [x] Macro cycles (STDC/LTDC/Empire) added to S3-W5
- [x] DLQ + dedupe moved to S3-W6 (from S4)
- [x] Cycle cards render with drivers, timeline, confidence
- [x] News dev plan label (metadata-only, 24h delay)

### S4 Additions
- [x] Rating method versioning (inputs_json for explainability)
- [x] Hedged benchmark toggle
- [x] DaR calibration view (MAD, hit rate)
- [x] Rights drills final validation (FMP-only, NewsAPI blocked)

### CI Gates
- [x] Unit tests (≥ 95% coverage)
- [x] Property tests (Hypothesis, currency invariants)
- [x] Golden tests (ADR, attribution, regime, ratings)
- [x] Integration tests (ledger ±1bp, pack build, alerts, exports)
- [x] Security tests (RLS/IDOR, SQL injection, JWT, secrets)
- [x] Chaos tests (provider outage, DB failover, cache eviction)
- [x] Visual tests (Portfolio Overview, Deep-Dive, Macro Dashboard)

### RACI
- [x] Resource allocation defined (8-10 FTEs)
- [x] RACI matrix (Orchestrator, Layer Architects, DevOps, QA)
- [x] Critical path identified (Provider → Pack → Reconcile → Metrics → Macro → Ratings → Optimizer)

---

## Conclusion

**DawsOS Implementation Roadmap v2.0** is **ready to build** with all feedback incorporated:

✅ **Observability skeleton** moved to S1-W2 (from S3) — enables early p95 visibility
✅ **Rights enforcement** moved to S1-W2 (from S4) — prevents late "oops we exported restricted data"
✅ **ADR/pay-date FX golden tests** added to S1-W1 — 42¢ accuracy enforced early
✅ **DLQ + dedupe** moved to S3-W6 (from S4) — prevents alert storms before news goes live
✅ **Macro cycles** (STDC/LTDC/Empire) added to S3 — fills analytics layer gap
✅ **Infra-as-code** (Terraform/Helm/ECS) added to Phase 0 — environment reproducibility
✅ **SBOM/SCA/SAST** added to Phase 0 CI — security baseline from day 1
✅ **Backfill rehearsal** added to S2-W4 — restatement path validated early
✅ **Visual regression tests** added to S2-W4 — UI regressions caught early
✅ **CI gates explicit** — merge-only-on-green across 7 test types

**Total duration**: 8 weeks (Phase 0 + 4 sprints)
**Team size**: 8-10 FTEs
**Risk mitigation**: 10 major risks addressed with concrete mitigations
**Critical path**: Provider integration → Pack build → Reconciliation → Metrics → Macro → Ratings → Optimizer

**Next action**: Sprint 0 kickoff (infra team starts Terraform, backend team reviews agent specs)

---

**Signed**: Build System Architect
**Date**: 2025-10-21
**Version**: 2.0 (Feedback incorporated, ready to build)
