# DawsOS Development Guide

**Audience**: Engineers working on the DawsOSP repository  
**Source of Truth**: This guide complements `README.md` (environment + quick start) and `.ops/TASK_INVENTORY_2025-10-24.md` (active backlog).

---

## 1. Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11.x | For scripts + unit tests (`python3.11 -m venv venv`) |
| Docker / Compose | 24.x / v2 | Primary way to run API + worker + UI + Postgres + Redis |
| Node.js | 18.x (optional) | Only needed if working on the Streamlit-to-Next.js migration |
| Poetry/Pip | Pip (`requirements.txt`) | Backend dependencies installed via `pip install -r backend/requirements.txt` when running without Docker |

Copy `.env.example` → `.env` and fill in provider keys (`FMP_API_KEY`, `POLYGON_API_KEY`, `FRED_API_KEY`, `NEWSAPI_KEY`). `ENABLE_OBSERVABILITY=false` by default; set to `true` only when you also provide Jaeger/Sentry endpoints.

---

## 2. Quick Start (Seeded Stack)

```bash
# 0. Clone
git clone https://github.com/mwd474747/DawsOSP.git && cd DawsOSP

# 1. Create virtualenv for scripts/tests
python3.11 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 2. Seed demo data (pricing pack PP_2025-10-21, macro cycles, ScenarioService shocks)
python scripts/seed_loader.py --all
# Optional: re-run specific domains
python scripts/seed_loader.py --domain scenarios

# 3. Launch full stack
docker compose up -d --build

# API lives at http://localhost:8000, UI at http://localhost:8501
```

Hot reloading is available for the API via `backend/run_api.sh` (uvicorn) when you do not want the entire Compose stack. Streamlit UI can be launched with `streamlit run frontend/main.py`.

---

## 3. Repository Layout (2025-10)

```
├── backend/
│   ├── app/
│   │   ├── api/                # FastAPI routers (executor, health, packs)
│   │   ├── agents/             # financial_analyst, macro_hound, ratings_agent, etc.
│   │   ├── core/               # pattern orchestrator, agent runtime, request ctx
│   │   ├── services/           # pricing, ledger, macro, scenarios, ratings, reports...
│   │   ├── providers/          # FMP/FRED/Polygon/News facades + transforms
│   │   └── db/                 # asyncpg helpers, query builders
│   ├── db/schema/              # SQL files applied via init_database.sh
│   ├── jobs/                   # pack build + mark fresh schedulers, workers
│   ├── patterns/               # JSON pattern definitions executed by orchestrator
│   └── tests/                  # pytest suites (services, agents, integration)
├── frontend/                   # Streamlit UI (MVP)
├── scripts/seed_loader.py      # Seeds symbols, packs, macro cycles, ratings rubrics
├── .ops/                       # Governance + planning inventories/runbooks
└── .claude/agents/             # Agent-specific specs with status blocks
```

Keep all new automation/docs inside this structure; references to `agents/` or `storage/` at repo root indicate stale content.

---

## 4. Daily Workflow

1. **Sync + read the backlog**  
   `git pull --rebase` and skim `.ops/TASK_INVENTORY_2025-10-24.md` → focus on the `P1` items unless you have approval to pick up `P2`.

2. **Work inside the single execution path**  
   UI → `POST /v1/execute` → Pattern Orchestrator → Agent Runtime → Services. No direct DB/provider calls from UI or agents unless specifically documented.

3. **Seed data when needed**  
   - `python scripts/seed_loader.py --domain scenarios` (ScenarioService shocks)  
   - `python scripts/seed_loader.py --domain ratings` (rubrics)  
   - Use `python scripts/seed_loader.py --help` for all domains.

4. **Verify changes**  
   - Unit tests: `pytest backend/tests/services` (or narrower path)  
   - Integration tests: `./backend/run_integration_tests.sh` (requires Docker)  
   - UI smoke: open Streamlit and run `portfolio_overview` pattern.

5. **Document + trace**  
   Update the relevant `.ops/*` doc or agent spec when capability status changes. Every data-affecting change should describe the new `pricing_pack_id` or ledger behavior.

---

## 5. Common Tasks

| Task | Command / Notes |
|------|-----------------|
| Run FastAPI locally | `./backend/run_api.sh` (uses uvicorn with autoreload) |
| Run worker jobs | `docker compose up worker` or invoke `python backend/jobs/scheduler.py` |
| Execute a pattern manually | `uvicorn backend.app.api.executor:app` then `curl -X POST http://localhost:8000/v1/execute -d '{"pattern_id":"portfolio_overview"}'` |
| Rebuild ScenarioService cache | `python scripts/seed_loader.py --domain scenarios` |
| Inspect ScenarioService output | `python backend/app/services/scenarios.py` via `pytest backend/tests/services/test_scenarios_service.py` |
| Run ratings service tests | `pytest backend/tests/services/test_ratings_service.py` |
| Format docs | Markdown manual; no repo-wide auto-format enforced |

---

## 6. Documentation Map

| Topic | File |
|-------|------|
| Quick start + capabilities overview | `README.md` |
| Product/architecture contract | `PRODUCT_SPEC.md` |
| Backlog / remaining work | `.ops/TASK_INVENTORY_2025-10-24.md` |
| Governance + rights registry | `.ops/RIGHTS_REGISTRY.yaml`, `.ops/IMPLEMENTATION_GUARDRAILS.md` |
| Observability + remediation plans | `.ops/SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md`, `.ops/OBSERVABILITY_IMPLEMENTATION_REPORT.md` |
| Agent-specific responsibilities | `.claude/agents/**/*.md` (now include current status blocks) |
| Pricing/Ledger operations | `backend/PRICING_PACK_GUIDE.md`, `backend/LEDGER_RECONCILIATION.md` |

If you need context that used to live in Trinity docs, search git history pre-`0af9ff6` but do **not** link those files in new documentation.

---

## 7. Known Gaps & Warnings

- **ScenarioService & DaR**: Service + seeded shocks exist, but persistence tables (`scenario_results`, `dar_history`) and UI charts are still TODO (see backlog P1 items).  
- **Ratings fundamentals**: Rubrics + rating weights are live; fundamentals ingestion still falls back to the transformed FMP snapshot when API keys are missing. Document limitations in pattern outputs.  
- **Optimizer**: `backend/app/services/optimizer.py` scaffold exists but policy_rebalance pattern is not exposed in the UI yet. Treat the optimizer as experimental until P1-CODE-3 closes.  
- **PDF exports**: `reports.py` returns placeholder text. Communicate this in any user-facing documentation and block rights-sensitive exports.  
- **Observability**: Only enabled when `ENABLE_OBSERVABILITY=true`. Default deployments ship without tracing/metrics; do not claim "always-on" monitoring.

Keep this section updated whenever a major capability switches state so downstream docs stay honest.
