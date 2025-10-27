# DawsOS Task Inventory
**Date**: October 24, 2025
**Purpose**: Single source of truth for remaining work (aligned with PRODUCT_SPEC.md)

---

## Snapshot

- Core execution stack, pricing service, seeded patterns, and Streamlit UI are operational.
- Seed loader (`python scripts/seed_loader.py --all`) hydrates demo symbols, portfolios, pricing pack `PP_2025-10-21`, macro indicators, and cycles.
- Remaining effort focuses on sprint 3/4 deliverables: macro scenarios/DaR, ratings, optimizer, rights-enforced exports/alerts, nightly orchestration, observability, and live providers.

---

## Priority Backlog

### P0 (Critical – must ship to meet product vision)
1. **Macro scenarios & Drawdown-at-Risk** ✅ *Delivered 2025-10-26 (commits 2876d86, bc6a7ee, scenario seeds)*
   - ✅ `macro_run_scenario` wired to ScenarioService + 22 seeded scenarios
   - ✅ `macro_compute_dar` implemented in ScenarioService
   - ⏳ Persist results (`scenario_results`, `dar_history`) & add UI panels
2. **Rights-enforced exports & alerts**
   - Finish PDF export pipeline (WeasyPrint, watermarking, attribution) and alert delivery with DLQ/dedupe tests
   - Add rights drill test suite
3. **Authentication & RBAC**
   - Replace stub `X-User-ID` header with JWT validation, role enforcement, audit logging
4. **Testing uplift**
   - Extend backend/unit/integration tests, add visual regression + chaos tests to hit ≥60% coverage

### P1 (High)
5. **Ratings service** (`dividend_safety`, `moat`, `resilience`) + UI badges/patterns
6. **Optimizer service** (Riskfolio-Lib) + Optimizer screen
7. **Nightly job orchestration**
   - Provider ingestion (FMP/Polygon/FRED/News)
   - build_pack → reconcile → metrics → prewarm → alerts
8. **Observability & alerting**
   - Wire OpenTelemetry exporter, Prometheus dashboards, alert routing (pager/email)

### P1/P2
9. **Provider integrations** beyond seeds (FMP, Polygon, NewsAPI) with rate limiting and retries
10. **Documentation & go-live**
    - Update runbooks, UAT checklist, go/no-go sign-off, rights drills, security review

---

## Historical References
- `.ops/IMPLEMENTATION_ROADMAP_V2.md` – sprint plan and sequencing (updated to reflect current priorities)
- `STABILITY_PLAN.md` – current stability focus (macro/ratings/optimizer/observability)
- `.claude/agents/*.md` – agent-specific specs (statuses noted inside each doc)

This inventory replaces scattered TODO lists. Update here whenever scope changes.
