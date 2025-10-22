# Portfolio Platform Build Orchestrator

**Role**: Master coordinator agent for DawsOS Portfolio Intelligence Platform build
**Context**: [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md)
**Status**: Active
**Priority**: P0

---

## Mission

Coordinate the complete build of the DawsOS Portfolio Intelligence Platform according to the Product Spec v1.4, ensuring:

1. **Architecture fidelity**: Single execution path (UI→API→Pattern→Agent→Service)
2. **Reproducibility**: All results traceable to `pricing_pack_id` + `ledger_commit_hash`
3. **Compliance**: Rights registry enforced, RLS secured, IDOR-proof
4. **Performance**: Warm p95 < 1.2s, cold p95 < 2.0s
5. **Multi-currency truth**: Proper FX handling at trade/valuation/dividend levels

---

## Sub-Agents (Delegation Tree)

### Infrastructure Layer
- **[INFRASTRUCTURE_ARCHITECT](./infrastructure/INFRASTRUCTURE_ARCHITECT.md)** → Database, Docker, auth, RLS
  - `DATABASE_BUILDER` → Postgres/Timescale schema, migrations, RLS policies
  - `DOCKER_COMPOSER` → Compose stack (api/worker/scheduler/ui/db/redis)
  - `AUTH_SECURITY` → OAuth, JWT, IDOR fuzz tests

### Data & Truth Spine
- **[SCHEMA_SPECIALIST](./data/SCHEMA_SPECIALIST.md)** → **Database schema authority** (cross-cutting)
  - Authoritative reference for all tables, indexes, RLS policies, migrations
  - Multi-currency patterns and query templates
  - **Referenced by**: ALL agents working with database

- **[LEDGER_ARCHITECT](./data/LEDGER_ARCHITECT.md)** → Beancount integration, reconciliation
  - `BEANCOUNT_INTEGRATOR` → Journal parsing, lot tracking, transaction import
  - `PRICING_PACK_BUILDER` → Daily pack generation, FX rates, pack freshness
  - `RECONCILIATION_ENGINE` → Ledger vs DB ±1bp validation

### Core Execution Stack
- **[EXECUTION_ARCHITECT](./core/EXECUTION_ARCHITECT.md)** → Executor API, Pattern Orchestrator
  - `EXECUTOR_API_BUILDER` → FastAPI routes, RequestCtx, pack freshness gate
  - `PATTERN_ORCHESTRATOR_BUILDER` → DAG runner, capability routing, trace system
  - `AGENT_RUNTIME_BUILDER` → Agent registration, capability injection

### Data Providers
- **[PROVIDER_INTEGRATOR](./providers/PROVIDER_INTEGRATOR.md)** → FMP, Polygon, FRED, NewsAPI
  - `FMP_FACADE` → Fundamentals/ratios facade with rate limits
  - `POLYGON_FACADE` → Prices/corporate actions
  - `FRED_FACADE` → Macro indicators
  - `NEWSAPI_FACADE` → News impact (dev/prod licensing)
  - `RIGHTS_REGISTRY` → Export gates, attributions

### Business Logic
- **[METRICS_ARCHITECT](./business/METRICS_ARCHITECT.md)** → Performance, attribution, risk
  - `PERFORMANCE_CALCULATOR` → TWR, MWR, Sharpe, vol
  - `CURRENCY_ATTRIBUTOR` → Local/FX/interaction decomposition
  - `FACTOR_ANALYZER` → Factor exposures, variance share

- **[MACRO_ARCHITECT](./business/MACRO_ARCHITECT.md)** → Dalio regime, scenarios, DaR
  - `REGIME_CLASSIFIER` → Z-scores, regime probabilities
  - `SCENARIO_ENGINE` → Shock application, factor betas
  - `DAR_CALCULATOR` → Regime-conditioned covariance, calibration panel

- **[RATINGS_ARCHITECT](./business/RATINGS_ARCHITECT.md)** → Buffett quality scores
  - `DIVIDEND_SAFETY_RATER` → Payout/growth/FCF/net cash analysis
  - `MOAT_ANALYZER` → Competitive moat strength
  - `RESILIENCE_RATER` → Balance sheet resilience

- **[OPTIMIZER_ARCHITECT](./business/OPTIMIZER_ARCHITECT.md)** → Policy-based rebalancing
  - `POLICY_ENGINE` → Rating-based constraints
  - `OPTIMIZER_CORE` → Riskfolio-Lib integration, TE/turnover constraints

### UI & Reporting
- **[UI_ARCHITECT](./ui/UI_ARCHITECT.md)** → Streamlit/Next.js UI implementation
  - `THEME_BUILDER` → Dark theme, DawsOS design system
  - `PORTFOLIO_OVERVIEW_UI` → KPI ribbon, holdings table, explain drawer
  - `DEEP_DIVE_UI` → Multi-tab holding analysis
  - `MACRO_UI` → Regime card, factor exposures, DaR widget
  - `SCENARIO_UI` → Shock builder, delta tables
  - `ALERTS_UI` → Alert creation, history, playbooks

- **[REPORTING_ARCHITECT](./reporting/REPORTING_ARCHITECT.md)** → PDF exports
  - `PDF_GENERATOR` → WeasyPrint templates
  - `RIGHTS_GATE_ENFORCER` → Pre-export validation

### Knowledge & Intelligence
- **[KNOWLEDGE_ARCHITECT](./intelligence/KNOWLEDGE_ARCHITECT.md)** → Graph, memory
  - `GRAPH_SCHEMA_BUILDER` → Node/edge types, memory storage
  - `ANALYSIS_SNAPSHOT_TRACKER` → Pattern result provenance

### Testing & Quality
- **[TEST_ARCHITECT](./testing/TEST_ARCHITECT.md)** → Comprehensive test suites
  - `UNIT_TEST_BUILDER` → Capability unit tests
  - `INTEGRATION_TEST_BUILDER` → Pattern integration tests
  - `GOLDEN_TEST_BUILDER` → Ledger ±1bp property tests
  - `SECURITY_TEST_BUILDER` → RLS/IDOR fuzz tests
  - `CHAOS_TEST_BUILDER` → Provider outage resilience

### Observability
- **[OBSERVABILITY_ARCHITECT](./observability/OBSERVABILITY_ARCHITECT.md)** → Monitoring, alerting
  - `TELEMETRY_BUILDER` → OpenTelemetry, Prometheus
  - `ALERTING_BUILDER` → Alert evaluator, DLQ, dedupe
  - `LOGGING_BUILDER` → Structured logs, sensitive data redaction

---

## Sequencing (Phase Gates)

### Week 0.5: Foundation
**Owner**: INFRASTRUCTURE_ARCHITECT
- [ ] Docker compose stack operational
- [ ] Postgres + Timescale + Redis running
- [ ] RLS policies implemented and tested
- [ ] OAuth/JWT auth flow
- [ ] Symbol master table (FIGI/CUSIP)
- [ ] Rights registry stub (YAML)
- [ ] Demo seed data
- [ ] CORS configuration

**Gate**: Can authenticate, DB has RLS, can query symbol master

---

### Sprint 1 (2 weeks): Truth Spine + Execution Core
**Owners**: LEDGER_ARCHITECT, EXECUTION_ARCHITECT, PROVIDER_INTEGRATOR

#### Week 1
- [ ] Beancount journal parser
- [ ] Lot tracking implementation
- [ ] Pricing pack daily builder
- [ ] FX rate ingestion (pack policy)
- [ ] Executor API scaffold (FastAPI)
- [ ] RequestCtx construction
- [ ] Pack freshness gate logic

#### Week 2
- [ ] Pattern orchestrator DAG runner
- [ ] Capability registry
- [ ] Agent runtime + registration
- [ ] FMP facade (fundamentals)
- [ ] Polygon facade (prices, CA)
- [ ] FRED facade (macro)
- [ ] Reconciliation job (ledger vs DB)

**Gate**: Can execute simple pattern end-to-end; pack builds nightly; reconciliation passes ±1bp

---

### Sprint 2 (2 weeks): Core Analytics + UI Foundation
**Owners**: METRICS_ARCHITECT, UI_ARCHITECT

#### Week 3
- [ ] TWR/MWR calculation
- [ ] Currency attribution (local/FX/interaction)
- [ ] Factor exposure calculation
- [ ] Portfolio overview pattern
- [ ] Holding deep-dive pattern
- [ ] UI theme implementation (DawsOS design system)
- [ ] Portfolio Overview screen (KPI ribbon, holdings table)

#### Week 4
- [ ] Deep-Dive UI (tabs: overview/valuation/macro/ratings/news)
- [ ] Explain drawer (trace display)
- [ ] Panel staleness chips
- [ ] Charts integration (allocation, attribution donut)
- [ ] Scenario tool pattern

**Gate**: Can view portfolio, drill into holdings, see attribution; UI matches design spec

---

### Sprint 3 (2 weeks): Macro Intelligence + Alerts
**Owners**: MACRO_ARCHITECT, OBSERVABILITY_ARCHITECT

#### Week 5
- [ ] Regime classifier (z-scores, probabilities)
- [ ] Factor analyzer (betas, variance share)
- [ ] DaR calculator (regime-conditioned)
- [ ] Scenario engine (shock application)
- [ ] Macro UI (regime card, factor bars, DaR widget)

#### Week 6
- [ ] Alert evaluator
- [ ] Alert condition parser
- [ ] DLQ + dedupe logic
- [ ] Alerts UI (creation, history)
- [ ] NewsAPI facade
- [ ] News impact pattern
- [ ] Panel staleness tracking

**Gate**: Regime displayed correctly; alerts fire and dedupe; news impact shown

---

### Sprint 4 (2 weeks): Quality Ratings + Optimization + Polish
**Owners**: RATINGS_ARCHITECT, OPTIMIZER_ARCHITECT, REPORTING_ARCHITECT

#### Week 7
- [ ] Dividend safety rater
- [ ] Moat analyzer
- [ ] Resilience rater
- [ ] Buffett checklist pattern
- [ ] Rating badges in UI
- [ ] Policy engine
- [ ] Optimizer core (Riskfolio-Lib)
- [ ] Policy rebalance pattern

#### Week 8
- [ ] PDF generator (WeasyPrint)
- [ ] Rights gate enforcer
- [ ] Export report pattern
- [ ] Hedged benchmark toggle
- [ ] DaR calibration panel
- [ ] Performance optimization (pre-warm)
- [ ] Final integration testing

**Gate**: All acceptance criteria met; stress tests pass; ready for staging

---

## Coordination Protocol

### Daily Standups (Async)
Each sub-agent reports to ORCHESTRATOR:
- **Done yesterday**: Completed tasks
- **Doing today**: Current focus
- **Blockers**: Dependencies/issues
- **Drift alerts**: Any spec deviations

### Weekly Reviews
- Sprint goal progress
- Integration test results
- Performance benchmarks
- Security scan results
- Gate readiness assessment

### Escalation Path
1. Sub-agent attempts resolution
2. If blocked >4 hours → escalate to layer architect
3. If cross-layer conflict → escalate to ORCHESTRATOR
4. ORCHESTRATOR makes binding decision, updates spec if needed

---

## Quality Gates (Every Sprint)

### Code Quality
- [ ] Black/ruff/isort/mypy pass
- [ ] Test coverage >80% on new code
- [ ] No critical security issues (Bandit)
- [ ] API docs generated (OpenAPI)

### Functional
- [ ] All acceptance criteria met
- [ ] Integration tests green
- [ ] No regressions on prior sprints

### Performance
- [ ] Warm p95 trends tracked
- [ ] Cold p95 trends tracked
- [ ] Database query plans reviewed

### Security
- [ ] RLS policies cover new tables
- [ ] IDOR tests updated
- [ ] Secrets not in code
- [ ] Audit log events added

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Provider API rate limits hit during dev | Medium | Medium | Use cached fixtures for tests; implement token bucket early |
| Beancount reconciliation edge cases (ADR dividends) | High | High | Golden tests with known multi-currency portfolios; ADR-specific test suite |
| Performance degradation with large portfolios | Medium | High | Pre-warm strategy; pagination; continuous benchmarking |
| Rights registry blocking legitimate exports | Low | Medium | Clear licensing docs; staged rollout with override flag |
| RLS policy gaps (IDOR vulnerability) | Low | Critical | Automated fuzz tests in CI; manual pentest before launch |
| Symbol normalization drift (FIGI mapping changes) | Medium | Medium | Nightly mapping diff report; manual override table |

---

## Success Metrics

### Technical
- **Reproducibility**: 100% of results have pack_id + ledger_hash; same inputs → same outputs
- **Performance**: Warm p95 < 1.2s, cold p95 < 2.0s
- **Accuracy**: Ledger vs metrics ±1bp on 100 random portfolios
- **Uptime**: 99.5% availability (excludes nightly jobs)
- **Security**: 0 critical/high vulnerabilities; RLS/IDOR tests 100% pass

### Functional
- **Patterns**: 9 core patterns operational
- **Agents**: 5 agents registered and routing correctly
- **Providers**: 4 providers integrated with rights gates
- **UI**: 6 major screens implemented per design spec

---

## Handoff to Operations

Upon completion:
1. **Runbook**: Deploy, backup/restore, incident response
2. **Monitoring**: Dashboards, alert thresholds, on-call rotation
3. **Maintenance**: Nightly job monitoring, pack freshness SLA
4. **Training**: User onboarding guide, admin guide
5. **Documentation**: API docs, architecture diagrams, decision log

---

## Notes

- This orchestrator maintains the **single source of truth** for build status
- All agents MUST update their status here before daily standup
- Any spec clarifications/changes propagate from ORCHESTRATOR to sub-agents
- ORCHESTRATOR is responsible for cross-layer integration testing
