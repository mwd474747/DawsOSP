# Portfolio Platform Orchestrator

**Role**: Master coordinator agent for DawsOS Portfolio Intelligence Platform
**Context**: [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md)
**Status**: ⚠️ Partial (Seeded MVP; macro scenarios/DaR shipped, optimizer/exports pending)
**Priority**: P0
**Last Updated**: 2025-10-26

---

## Mission

Coordinate the operational DawsOS Portfolio Intelligence Platform, ensuring:

1. **Architecture fidelity**: Single execution path (UI→API→Pattern→Agent→Service)
2. **Reproducibility**: All results traceable to `pricing_pack_id` + `ledger_commit_hash`
3. **Compliance**: Rights registry enforced, RLS secured, IDOR-proof
4. **Performance**: Warm p95 < 1.2s, cold p95 < 2.0s
5. **Multi-currency truth**: Proper FX handling at trade/valuation/dividend levels

---

## Current System Status

### ✅ Working Today (Seeded Mode)

#### Core Execution Stack (Production)
- **[EXECUTION_ARCHITECT](./core/EXECUTION_ARCHITECT.md)** → [backend/app/api/executor.py](../../backend/app/api/executor.py)
  - ✅ Executor API with `/v1/execute` endpoint
  - ✅ Pattern Orchestrator ([pattern_orchestrator.py](../../backend/app/core/pattern_orchestrator.py)) - DAG runner with trace
  - ✅ Agent Runtime ([agent_runtime.py](../../backend/app/core/agent_runtime.py)) - Capability routing
  - ✅ RequestCtx ([types.py](../../backend/app/core/types.py)) - Request context with tracing

#### Agents (status)

**FinancialAnalyst** *(operational)* — [financial_analyst.py](../../backend/app/agents/financial_analyst.py)
- `ledger.positions`: loads seeded portfolio lots with security IDs
- `pricing.apply_pack`: applies pricing pack valuations (seeded pack `PP_2025-10-21`)
- `metrics.compute*` / `attribution.currency`: wrapper over seeded metrics

**MacroHound** *(scenarios + DaR implemented; persistence pending)* — [macro_hound.py](../../backend/app/agents/macro_hound.py)
- Implemented: `macro.detect_regime`, `macro.compute_cycles`, `macro.get_indicators`
- Implemented: `macro.run_scenario`, `macro.compute_dar` (ScenarioService)
- Planned: Persist scenario/DaR results + expose in UI

**DataHarvester** *(provider scaffolding + transforms)* — [data_harvester.py](../../backend/app/agents/data_harvester.py)
- Implemented: FMP fundamentals transformation, Polygon/FRED/NewsAPI transformations
- Pending: Fundamentals caching + UI wiring for buffett_checklist

**ClaudeAgent** *(operational)* — [claude_agent.py](../../backend/app/agents/claude_agent.py)
- `claude.explain`, `claude.summarize`, `claude.analyze`

#### Patterns (Mixed Status)
Located in [backend/patterns/](../../backend/patterns/):
- ✅ portfolio_overview.json - **Primary pattern** (performance, attribution, holdings)
- ✅ holding_deep_dive.json - Single security analysis
- ✅ portfolio_macro_overview.json - Macro + portfolio integration
- ✅ macro_cycles_overview.json - Regime classification
- ✅ portfolio_cycle_risk.json - Cycle risk exposure
- ✅ portfolio_scenario_analysis.json - Shock scenarios
- ✅ cycle_deleveraging_scenarios.json - Dalio deleveraging
- ⚠️ buffett_checklist.json - Ratings weights/fundamentals implemented, UI still seeded
- 🚧 policy_rebalance.json - Optimizer service not implemented
- ⚠️ news_impact_analysis.json - NewsAPI metadata-only (dev tier restrictions)
- 🚧 export_portfolio_report.json - Placeholder export output
- ✅ macro_trend_monitor.json - Trend monitoring
- ✅ export_portfolio_report.json - PDF export (rights-gated)

#### Services Layer (Production)
- ✅ **PricingService** ([pricing.py](../../backend/app/services/pricing.py)) - Price loading (optimized 2025-10-24)
- ✅ **LedgerService** ([ledger.py](../../backend/app/services/ledger.py)) - Lots table queries
- ✅ **MetricsService** ([metrics.py](../../backend/app/services/metrics.py)) - TWR, Sharpe, attribution
- ✅ **MacroService** ([macro.py](../../backend/app/services/macro.py)) - Regime classification
- ✅ **RiskService** ([risk.py](../../backend/app/services/risk.py)) - VaR, factor exposures
- ✅ **CyclesService** ([cycles.py](../../backend/app/services/cycles.py)) - Dalio cycle logic
- ✅ **ProvidersService** ([providers.py](../../backend/app/services/providers.py)) - External API orchestration

#### Governance (Production)
- ✅ **Rights Registry** ([.ops/RIGHTS_REGISTRY.yaml](../../.ops/RIGHTS_REGISTRY.yaml)) - 6 providers configured
- ✅ **Rights Enforcement** ([rights_registry.py](../../backend/app/core/rights_registry.py)) - PDF/CSV export gates
- ✅ **Circuit Breaker** ([circuit_breaker.py](../../backend/app/core/circuit_breaker.py)) - Provider failure handling
- ✅ **Rate Limiter** ([rate_limiter.py](../../backend/app/core/rate_limiter.py)) - API rate limiting

### ❌ Not Implemented

#### Missing Agents
- ❌ **RatingsAgent** - Buffett quality scores (only buffett_checklist pattern exists, no agent)
- ❌ **OptimizerAgent** - Portfolio optimization (only policy_rebalance pattern exists, no agent)

### ⚠️ Known Issues

#### P0 (Blocking Pattern Execution)
**Database Pool Architecture Issue**
- **Problem**: Module-level global `_pool` not accessible across uvicorn --reload contexts
- **Impact**: Pattern execution returns empty data despite agents working
- **Fix Ready**: [DATABASE_POOL_ARCHITECTURE_ISSUE.md](../../DATABASE_POOL_ARCHITECTURE_ISSUE.md) + [STABILITY_PLAN.md](../../STABILITY_PLAN.md) Option A
- **Status**: Fix ready to implement (disable --reload)

#### P1 (Incomplete Features)
1. **Position attributions helper missing** - Currency attribution needs `get_position_attributions()` method in FinancialAnalyst
2. **Duplicate lots data** - 6 lots in DB instead of 3 (query returns correct sum, cleanup needed)
3. **Duplicate transactions** - 16 transactions, 10 unique (data quality issue)

### Recent Changes (2025-10-24)

#### Governance Fixes Completed
Reference: [GOVERNANCE_FIXES_COMPLETE.md](../../GOVERNANCE_FIXES_COMPLETE.md)

1. ✅ **Deleted duplicate pricing function** - Consolidated to PricingService single code path
2. ✅ **Performance optimization** - Added `get_prices_as_decimals()` method (~30% faster)
3. ✅ **JSON serialization fix** - Fixed AsyncPG JSONB type handling in seed loader

### Infrastructure & Data Layer
- **[SCHEMA_SPECIALIST](./data/SCHEMA_SPECIALIST.md)** → Database schema authority
  - Schema files: [backend/db/schema/](../../backend/db/schema/)
  - RLS policies (partially implemented)
  - Multi-currency patterns

- **[LEDGER_ARCHITECT](./data/LEDGER_ARCHITECT.md)** → Beancount integration
  - Lots table operational ([001_portfolios_lots_transactions.sql](../../backend/db/schema/001_portfolios_lots_transactions.sql))
  - Pricing packs ([pricing_packs.sql](../../backend/db/schema/pricing_packs.sql))
  - Reconciliation (status unclear)

- **[PROVIDER_INTEGRATOR](./integration/PROVIDER_INTEGRATOR.md)** → External data providers
  - FMP, Polygon, FRED, NewsAPI, YahooFinance (fallback)
  - Rights registry enforced ([RIGHTS_REGISTRY.yaml](../../.ops/RIGHTS_REGISTRY.yaml))

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
