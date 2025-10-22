# DawsOS Portfolio Platform - Document Index

**Quick Navigation** for all build specification and agent files.

---

## 🎯 Start Here

1. **[PRODUCT_SPEC.md](PRODUCT_SPEC.md)** - Complete product specification (v1.4 + SLOs)
2. **[.ops/IMPLEMENTATION_ROADMAP_V2.md](.ops/IMPLEMENTATION_ROADMAP_V2.md)** ⭐ - 8-week phased delivery plan (v2.0 with all feedback incorporated)
3. **[.claude/CLAUDE_CODE_GUIDE.md](.claude/CLAUDE_CODE_GUIDE.md)** ⭐ - Practical guide to using Claude Code in VS Code for agent-driven development
4. **[DawsOS_Seeding_Plan](DawsOS_Seeding_Plan)** - Complete seed data specification (Dalio cycles, multi-currency, ADR)
5. **[.claude/BUILD_SYSTEM_V2_FINAL_COMPLETION.md](.claude/BUILD_SYSTEM_V2_FINAL_COMPLETION.md)** - Build system v2.0 complete (15/15 deliverables, 100%)

---

## 📋 Product Specification Sections

From [PRODUCT_SPEC.md](PRODUCT_SPEC.md):

0. **Executive Intent** - Portfolio-first, truth-first philosophy
1. **Architecture** - Single execution path (UI→API→Pattern→Agent→Service)
2. **Data Model** - Schemas, invariants, RLS, hypertables
3. **Knowledge Graph** - Nodes, edges, analysis snapshots
4. **Patterns & Capabilities** - Declarative JSON workflows
5. **Providers & Clients** - FMP, Polygon, FRED, NewsAPI integration
6. **Multi-Currency & Corporate Actions** - Trade/valuation/dividend FX handling
7. **Macro (Dalio) & Quality (Buffett)** - Regime → factor → scenario; ratings
8. **Performance, Resiliency, Observability** - Pre-warm, staleness, telemetry
9. **Security & Tenancy** - OAuth, JWT, RLS, IDOR protection
10. **Sequencing** - Week 0.5 → Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4
11. **Acceptance Gates** - Reproducibility, ±1bp truth, rights enforced, p95 < 1.2s
12. **Stress-Test Plan** - 8 break-it-on-purpose scenarios
13. **Implementation Stubs** - Code examples for critical paths
14. **DawsOS UI Design** - Dark theme, color palette, component architecture
15. **UI → API Mapping** - Pattern outputs for each UI element
16. **CI/CD & Coding Standards** - Tooling, tests, feature flags
17. **Open Items** - P0/P1 tasks before code freeze
18. **Done Criteria** - Go/No-Go checklist

---

## 🤖 Agent System

### Master Coordinator
- **[.claude/agents/ORCHESTRATOR.md](.claude/agents/ORCHESTRATOR.md)**
  - Coordinates all phases
  - Maintains build status (single source of truth)
  - Manages dependencies and escalations
  - Enforces quality gates

### Infrastructure Layer (Week 0.5)
- **[.claude/agents/infrastructure/INFRASTRUCTURE_ARCHITECT.md](.claude/agents/infrastructure/INFRASTRUCTURE_ARCHITECT.md)**
  - Sub-agents: `DATABASE_BUILDER`, `DOCKER_COMPOSER`, `AUTH_SECURITY`
  - Deliverables: Postgres+Timescale, Docker Compose, OAuth/JWT, RLS policies, symbol master, demo seed

### Data & Truth Spine (Sprint 1)
- **[.claude/agents/data/SCHEMA_SPECIALIST.md](.claude/agents/data/SCHEMA_SPECIALIST.md)** ⭐ **Cross-Cutting Reference**
  - Authoritative schema catalog (ALL agents must consult for DB work)
  - Complete table DDL, RLS policies, indexes, migrations (001-005)
  - Multi-currency patterns, query templates, validation queries
  - Performance rules and data integrity constraints

- **[.claude/agents/data/LEDGER_ARCHITECT.md](.claude/agents/data/LEDGER_ARCHITECT.md)**
  - Sub-agents: `BEANCOUNT_INTEGRATOR`, `PRICING_PACK_BUILDER`, `RECONCILIATION_ENGINE`
  - Deliverables: Journal parsing, lot tracking, pricing packs, reconciliation (±1bp), nightly jobs

### Core Execution Stack (Sprint 1)
- **[.claude/agents/core/EXECUTION_ARCHITECT.md](.claude/agents/core/EXECUTION_ARCHITECT.md)**
  - Sub-agents: `EXECUTOR_API_BUILDER`, `PATTERN_ORCHESTRATOR_BUILDER`, `AGENT_RUNTIME_BUILDER`
  - Deliverables: `/execute` endpoint, JSON DAG runner, capability routing, tracing, caching

### Business Logic (Sprints 2-4)
- **[.claude/agents/business/METRICS_ARCHITECT.md](.claude/agents/business/METRICS_ARCHITECT.md)**
  - Sub-agents: `PERFORMANCE_CALCULATOR`, `CURRENCY_ATTRIBUTOR`, `FACTOR_ANALYZER`
  - Deliverables: TWR, MWR, currency attribution, factor exposures, risk metrics

- **[.claude/agents/analytics/MACRO_ARCHITECT.md](.claude/agents/analytics/MACRO_ARCHITECT.md)** ✅ **Created**
  - Sub-agents: `REGIME_CLASSIFIER`, `SCENARIO_ENGINE`, `DAR_CALCULATOR`
  - Deliverables: Regime detection (5 regimes), Dalio cycles (STDC/LTDC/Empire), DaR scenarios

- **[.claude/agents/business/RATINGS_ARCHITECT.md](.claude/agents/business/RATINGS_ARCHITECT.md)** ✅ **Created**
  - Sub-agents: `DIVIDEND_SAFETY_RATER`, `MOAT_ANALYZER`, `RESILIENCE_RATER`
  - Deliverables: Buffett quality scoring (0-10 scale), seeded rubrics, nightly batch calculation

- **[.claude/agents/business/OPTIMIZER_ARCHITECT.md](.claude/agents/business/OPTIMIZER_ARCHITECT.md)** ✅ **Created**
  - Sub-agents: `POLICY_ENGINE`, `OPTIMIZER_CORE`
  - Deliverables: Policy-based rebalancing, Riskfolio-Lib integration, trade proposals with costs

### Data Providers (Sprint 1)
- **[.claude/agents/integration/PROVIDER_INTEGRATOR.md](.claude/agents/integration/PROVIDER_INTEGRATOR.md)** ✅ **Created**
  - Sub-agents: `FMP_FACADE`, `POLYGON_FACADE`, `FRED_FACADE`, `NEWSAPI_FACADE`, `RIGHTS_REGISTRY`
  - Deliverables: Circuit breakers (3 failures → OPEN), DLQ retry, rights pre-flight checks

### UI (Sprints 2-4)
- **[.claude/agents/platform/UI_ARCHITECT.md](.claude/agents/platform/UI_ARCHITECT.md)** ✅ **Created**
  - Sub-agents: `THEME_BUILDER`, `PORTFOLIO_OVERVIEW_UI`, `DEEP_DIVE_UI`, `MACRO_UI`, `SCENARIO_UI`, `ALERTS_UI`
  - Deliverables: DawsOS dark theme (graphite/slate/signal-teal), 6 major screens, provenance badges, rights-gated exports

### Reporting (Sprint 4)
- **[.claude/agents/platform/REPORTING_ARCHITECT.md](.claude/agents/platform/REPORTING_ARCHITECT.md)** ✅ **Created**
  - Sub-agents: `PDF_GENERATOR`, `RIGHTS_GATE_ENFORCER`
  - Deliverables: WeasyPrint PDF generation, rights registry compliance, multi-page layouts, reproducibility guarantees

### Testing (All Sprints)
- **[.claude/agents/platform/TEST_ARCHITECT.md](.claude/agents/platform/TEST_ARCHITECT.md)** ✅ **Created**
  - Sub-agents: `UNIT_TEST_BUILDER`, `INTEGRATION_TEST_BUILDER`, `GOLDEN_TEST_BUILDER`, `SECURITY_TEST_BUILDER`, `CHAOS_TEST_BUILDER`, `PROPERTY_TEST_BUILDER`, `PERFORMANCE_TEST_BUILDER`
  - Deliverables: 7 test types (Unit, Property, Golden, Integration, Security, Chaos, Performance), ≥95% coverage, SLO enforcement

### Observability (Sprint 3)
- **[.claude/agents/platform/OBSERVABILITY_ARCHITECT.md](.claude/agents/platform/OBSERVABILITY_ARCHITECT.md)** ✅ **Created**
  - Sub-agents: `TELEMETRY_BUILDER`, `ALERTING_BUILDER`, `LOGGING_BUILDER`
  - Deliverables: OpenTelemetry tracing, Prometheus SLO enforcement, Alertmanager + PagerDuty

---

## 🛠️ Operational Documentation

### Runbooks & Incident Response
- **[.ops/RUNBOOKS.md](.ops/RUNBOOKS.md)** - 6 operational runbooks (RB-01 through RB-06)
  - **RB-01**: Pricing Pack Build Failure (symptoms, recovery, post-incident)
  - **RB-02**: Provider Outage (circuit breaker, DLQ replay)
  - **RB-03**: Alert Storm (cooldown enforcement, deduplication)
  - **RB-04**: Rights Registry Violation (audit, license check)
  - **RB-05**: Database Incident (failover, PITR restore)
  - **RB-06**: Security Incident (JWT rotation, WAF, RLS validation)

### CI/CD & Deployment
- **[.ops/CI_CD_PIPELINE.md](.ops/CI_CD_PIPELINE.md)** - 12-stage pipeline with canary deployment
  - **Stages 1-7**: Quality gates (lint, unit, property, golden, integration, security, chaos)
  - **Stages 8-9**: Build artifacts + SBOM/SCA
  - **Stages 10-11**: Staging deployment + UAT validation
  - **Stage 12**: Canary production (5% → 25% → 100% with auto-rollback on SLO breach)
  - **Duration**: ~25 minutes (commit → canary start)

- **[.ops/IMPLEMENTATION_ROADMAP_V2.md](.ops/IMPLEMENTATION_ROADMAP_V2.md)** ⭐ - 8-week implementation plan (v2.0)
  - **Phase 0** (Days 1-3): Infrastructure, security baseline, observability skeleton, rights stub
  - **Sprint 1** (Weeks 1-2): Truth spine (ledger + pack + reconcile), execution path, observability, rights gate
  - **Sprint 2** (Weeks 3-4): Metrics + UI + backfill rehearsal
  - **Sprint 3** (Weeks 5-6): Macro (regime + cycles) + alerts (DLQ/dedupe) + news
  - **Sprint 4** (Weeks 7-8): Ratings + optimizer + reporting + polish
  - **Team Size**: 8-10 FTEs
  - **Critical Path**: Provider integration → Pack build → Reconciliation → Metrics → Macro → Ratings → Optimizer

### Testing & Quality Assurance
- **[.ops/UAT_CHECKLIST.md](.ops/UAT_CHECKLIST.md)** - 47 UAT test cases with Go/No-Go criteria
  - **Critical (P0)**: 18 tests - 100% pass rate required for GO
  - **High (P1)**: 19 tests - ≥95% pass rate required for GO
  - **Medium (P2)**: 10 tests - informational only
  - **SLO validation**: Warm p95 ≤ 1.2s, Cold p95 ≤ 2.0s, Alert median ≤ 60s
  - **Includes**: Product owner sign-off, remediation plan template

---

## 📅 Phase Timeline

| Phase | Duration | Owner | Key Deliverables |
|-------|----------|-------|------------------|
| **Week 0.5** | 3-4 days | INFRASTRUCTURE_ARCHITECT | Docker, DB+RLS, Auth, Symbol master, Demo seed |
| **Sprint 1** | 2 weeks | LEDGER_ARCHITECT + EXECUTION_ARCHITECT | Ledger, Pricing pack, Executor API, Pattern orchestrator |
| **Sprint 2** | 2 weeks | METRICS_ARCHITECT + UI_ARCHITECT | TWR/MWR, Currency attribution, Portfolio Overview UI |
| **Sprint 3** | 2 weeks | MACRO_ARCHITECT + OBSERVABILITY_ARCHITECT | Regime, Scenario, DaR, Alerts, News impact |
| **Sprint 4** | 2 weeks | RATINGS_ARCHITECT + OPTIMIZER_ARCHITECT + REPORTING_ARCHITECT | Buffett checklist, Optimizer, PDF exports |

**Total**: 8.5 weeks (2 months)

---

## 🎯 Acceptance Criteria Quick Reference

**Reproducibility**:
- [ ] Same `pricing_pack_id` + `ledger_commit_hash` → identical results

**Accuracy**:
- [ ] Ledger vs DB ±1bp (100 portfolios)
- [ ] Multi-currency attribution reconciles ±1bp

**Compliance**:
- [ ] Rights registry enforced (export drills pass)
- [ ] RLS/IDOR fuzz tests 100% green in CI

**Performance**:
- [ ] Warm p95 < 1.2s, cold p95 < 2.0s

**Alerts**:
- [ ] Single delivery (dedupe), median < 60s

**Security**:
- [ ] No secrets in code, audit log for mutations

**Edge Cases**:
- [ ] ADR pay-date FX, hedged benchmarks, restatement banners

---

## 🔑 Key Invariants

1. **Single Execution Path**: UI → Executor API → Pattern Orchestrator → Agent Runtime → Services
2. **Reproducibility**: Every result has `pricing_pack_id` + `ledger_commit_hash`
3. **Multi-Currency**: Trade FX ≠ Valuation FX ≠ Dividend FX
4. **Pack Freshness**: Executor blocks (503) until pre-warm completes
5. **RLS Enforcement**: Every query sets `app.user_id` context
6. **Rights Registry**: Exports gated by provider licenses

---

## 📊 Analysis & Validation

- **[.claude/analysis/SCHEMA_VALIDATION.md](.claude/analysis/SCHEMA_VALIDATION.md)** - Comprehensive schema audit
  - **Score**: 95/100 (100/100 with migrations) - ✅ **APPROVED for Production**
  - **Exec Summary**: Multi-currency (100/100), RLS (100/100), Performance (100/100)
  - **Gaps**: 5 minor gaps (all additive, no breaking changes)

- **[.claude/migrations/](.claude/migrations/)** - 5 additive migrations to close gaps
  - `001_reproducibility_enhancements.sql` - Ledger commit hash + `is_fresh` flag
  - `002_reconciliation_tracking.sql` - ±1bp validation tracking table
  - `003_portfolio_daily_values.sql` - TWR calculation inputs (hypertable)
  - `004_benchmark_returns.sql` - Beta calculation support
  - `005_knowledge_graph.sql` - Pattern memory (Sprint 3)

---

## 📞 Support

- **Product questions**: Review [PRODUCT_SPEC.md](PRODUCT_SPEC.md) section-by-section
- **Schema questions**: See [.claude/agents/data/SCHEMA_SPECIALIST.md](.claude/agents/data/SCHEMA_SPECIALIST.md) (authoritative reference)
- **Implementation details**: Check agent `.md` file in `.claude/agents/`
- **Sequencing/dependencies**: See [.ops/IMPLEMENTATION_ROADMAP_V2.md](.ops/IMPLEMENTATION_ROADMAP_V2.md)
- **Operational procedures**: See [.ops/RUNBOOKS.md](.ops/RUNBOOKS.md) for incident response
- **Blockers**: Update agent status → escalate to ORCHESTRATOR

---

## 📊 Status Dashboard

Build system status is maintained in **[.claude/BUILD_SYSTEM_V2_FINAL_COMPLETION.md](.claude/BUILD_SYSTEM_V2_FINAL_COMPLETION.md)**:
- **Progress**: ✅ **100% complete** (15/15 deliverables)
- **Agent Specifications**: 9/9 complete (PROVIDER_INTEGRATOR, MACRO_ARCHITECT, RATINGS_ARCHITECT, OPTIMIZER_ARCHITECT, OBSERVABILITY_ARCHITECT, UI_ARCHITECT, REPORTING_ARCHITECT, TEST_ARCHITECT + SCHEMA_SPECIALIST)
- **Operational Docs**: 4/4 complete (RUNBOOKS, CI_CD_PIPELINE, UAT_CHECKLIST, IMPLEMENTATION_ROADMAP_V2)
- **Type System**: 1/1 complete (backend/app/core/types.py)
- **Documentation**: 3/3 enhancements complete (PRODUCT_SPEC SLOs, SCHEMA_SPECIALIST ADR dividends, INDEX updates)
- **Total Specs**: ~50,000+ lines of comprehensive specifications

**Implementation Readiness** (from [.ops/IMPLEMENTATION_ROADMAP_V2.md](.ops/IMPLEMENTATION_ROADMAP_V2.md)):
- ✅ Phase 0: Infrastructure as code (Terraform/Helm/ECS), security baseline, rights stub - Ready
- ✅ Sprint 1: Truth spine (ledger + pack), execution path, observability, rights gate - Ready
- ✅ Sprint 2: Metrics + UI + backfill rehearsal - Ready
- ✅ Sprint 3: Macro (regime + cycles) + alerts (DLQ/dedupe) + news - Ready
- ✅ Sprint 4: Ratings + optimizer + reporting + polish - Ready

**Development Tools**:
- ✅ **[.claude/CLAUDE_CODE_GUIDE.md](.claude/CLAUDE_CODE_GUIDE.md)** - Agent-driven development with Claude Code in VS Code
- ✅ **[.claude/ARCHITECTURAL_GUARDRAILS.md](.claude/ARCHITECTURAL_GUARDRAILS.md)** - Guardrails for AI-assisted development (see guide)
- ✅ All agent specs include: Mission, Scope, Acceptance Criteria, Implementation Specs, Testing Strategy, Done Criteria

---

**Last Updated**: 2025-10-21
**Maintained by**: ORCHESTRATOR agent
