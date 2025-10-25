# DawsOS – Portfolio Intelligence Platform

**Version**: 0.7 (in progress)
**Last Updated**: 2025-10-24

DawsOS delivers portfolio-first insights with reproducible outputs. A FastAPI executor, declarative patterns, and Streamlit UI run atop pricing packs and macro seeds to provide explainable analytics.

## Quick Start

```bash
# Clone and seed
git clone <repo-url> && cd DawsOSB/DawsOSP

# Provide ledger truth spine (see data/ledger/README.md)
# git clone <ledger-repo> data/ledger

python scripts/seed_loader.py --all  # symbols, portfolio, prices (PP_2025-10-21), macro, cycles

# Start stack
docker compose up -d --build

# Open UI
open http://localhost:8501  # Streamlit served via frontend/main.py
```

Backend API: http://localhost:8000

## Current Features
- Executor API `/v1/execute` with freshness gate and reproducibility tags
- Pricing service + seed loader (demo data)
- Portfolio overview & holdings patterns with seeded valuations and attribution
- Macro cycle seeds + dashboard scaffolding
- Rights registry, circuit breaker, rate limiter stubs wired into stack

## In Progress / Planned
- Macro scenarios & Drawdown-at-Risk (MacroHound)
- Ratings service (Buffett) and optimizer (Riskfolio)
- Rights-enforced PDF exports & alerts pipeline
- Nightly job orchestration (provider ingestion → pack → reconcile → metrics → alerts)
- Live provider integrations (FMP, Polygon, NewsAPI)
- Observability dashboards & broader test coverage

## Architecture
```
Streamlit UI → POST /v1/execute (FastAPI)
        ↓
Pattern Orchestrator (JSON patterns)
        ↓
Agent Runtime (financial analyst, macro, data harvester, claude)
        ↓
Services (pricing, macro, ledger, providers)
        ↓
PostgreSQL + TimescaleDB (seed data)
```

See [PRODUCT_SPEC.md](PRODUCT_SPEC.md) and [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for guardrails and setup details.

## Remaining Work (Highlights)
1. Implement macro scenarios/DaR
2. Build ratings & optimizer services and UI screens
3. Complete rights-enforced exports + alerts workflow
4. Add JWT auth/RBAC
5. Harden nightly job chain & observability
6. Expand automated tests (unit/integration/visual/chaos)

A detailed backlog lives in [.ops/TASK_INVENTORY_2025-10-24.md](.ops/TASK_INVENTORY_2025-10-24.md).
