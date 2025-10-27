# DawsOS Task Inventory — Archive (2025-10-26)

**Status**: Archived snapshot (superseded by [.ops/TASK_INVENTORY_2025-10-24.md](./TASK_INVENTORY_2025-10-24.md))  
**Reason**: This draft was produced before the ScenarioService, ratings rubric loaders, and provider transforms shipped. It contradicted the authoritative 2025-10-24 backlog, so it is now preserved only for historical context.

> 📌 **Use the 2025-10-24 inventory as the live backlog.** This file documents the corrections that were applied after verifying the codebase on 2025-10-26.

---

## Corrections to the 2025-10-26 Draft

| Area | Draft Claim | Actual State (2025-10-26) |
|------|-------------|---------------------------|
| Macro scenarios & DaR | "return 'not yet implemented' errors" | ✅ ScenarioService + MacroHound deliver shocks/DaR (commits `2876d86`, `bc6a7ee`). Remaining work: persist scenario/DaR runs + surface UI. |
| Ratings weights | "hardcoded 25% weights" | ✅ Rubrics now live in `rating_rubrics` with loader + service wiring (commits `5d24e04`, `8fd4d9e`, `e5cf939`). |
| Fundamentals | "stub transforms" | ⚠️ FMP transform + metadata shipped (`fa8bcf8`, `72de052`); caching/UI wiring still pending. |
| Provider transforms | "missing transforms" | ✅ Polygon/FRED/NewsAPI transforms completed (`5e28827`). |
| Missing agents | "RatingsAgent absent" | ✅ `backend/app/agents/ratings_agent.py` implements scoring + metadata. |
| Pattern failures | "6 of 12 fail" | ⚠️ Scenario patterns now execute against seeded shocks; remaining partials: `buffett_checklist` (UI), `policy_rebalance` (optimizer), `export_portfolio_report` (PDF placeholder), provider-live ingest. |
| Observability | "enabled from S1-W2" | ⚠️ Instrumentation exists but is opt-in via `ENABLE_OBSERVABILITY`; defaults remain disabled. |

---

## Completed Work Since 2025-10-24 Snapshot

| Workstream | Description | Commits |
|------------|-------------|---------|
| **P0-CODE-1** | Rating rubric schema, seeds, loader, service wiring | `5d24e04`, `8fd4d9e`, `e5cf939` |
| **P0-CODE-2** | Fundamentals transform + metadata source tracking | `fa8bcf8`, `72de052` |
| **P0-CODE-3** | Database bootstrap + migrations updated for rubrics | `7f00f3e` |
| **Scenario Service** | `macro.run_scenario` + `macro.compute_dar` implemented | `2876d86`, `bc6a7ee` |
| **Provider transforms** | FMP/POLYGON/FRED/NewsAPI normalization + fallbacks | `5e28827` |

These completions mean the remediation plan now focuses on persistence, UI wiring, and optimizer/reporting work (see `.ops/TASK_INVENTORY_2025-10-24.md` sections **P1-CODE** and **P1-DOCS**).

---

## Active Backlog (See 2025-10-24 Inventory for detail)

1. **Scenario/DaR Persistence + UI Surfacing** (P1-CODE-1/2 follow-ups)  
2. **Optimizer Service Integration** – riskfolio wiring + policy_rebalance pattern  
3. **Rights-enforced exports** – replace placeholder PDF output with WeasyPrint + rights footer  
4. **Observability Defaults** – document opt-in path and decide on default telemetry posture  
5. **Documentation Cleanup** – DEVELOPMENT_GUIDE rewrite, PRODUCT_SPEC status callouts, agent doc status blocks (tracked in **P1-DOCS**)

---

## How to Use This Archive

- **Governance reviews**: point to the corrections table above to explain why this document is not the single source of truth.  
- **Historical context**: the original backlog estimates (295 hours) live in git history; refer to commit `39902e7` if you need the unedited text.  
- **New contributors**: skip this file and consume `README.md`, `PRODUCT_SPEC.md`, `DEVELOPMENT_GUIDE.md`, and `.ops/TASK_INVENTORY_2025-10-24.md` for accurate instructions.

If additional drift is discovered, update the 2025-10-24 inventory (not this archive) and reference the relevant commits for auditability.
