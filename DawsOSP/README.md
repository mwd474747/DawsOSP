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

python scripts/seed_loader.py --all  # symbols, portfolio, prices (PP_2025-10-21), macro, cycles, ratings rubrics
# Optional: seed macro scenarios (22 shocks)
python scripts/seed_loader.py --domain scenarios  # seed ScenarioService library
# (Skip if you only need the core pricing pack)

# Start stack
docker compose up -d --build

# Open UI
open http://localhost:8501  # Streamlit served via frontend/main.py
```

Backend API: http://localhost:8000

## Current Capabilities (Seeded MVP)
- Executor API `/v1/execute` with pricing-pack freshness gate and reproducibility tags
- Seed loader hydrates demo portfolio, pricing pack `PP_2025-10-21`, macro cycles, and rating rubrics
- Pricing/ledger/metrics services power portfolio overview & holdings screens (seeded data only)
- Macro cycle seeds + dashboard scaffolding (regime detection, scenario stress tests, and DaR now powered by ScenarioService + seeded shocks)
- Rights registry + circuit breaker/rate limiter stubs wired into stack

## In Progress / Known Gaps
- Macro scenarios & Drawdown-at-Risk persistence (service + agent implemented; need DB persistence + UI wiring)
- Ratings fundamentals ingestion (service loads DB weights, fundamentals still stubs)
- Optimizer service + Riskfolio-driven policy rebalance (pattern exists, backend TBD)
- Rights-enforced PDF exports + alerts DLQ/dedupe pipeline
- Nightly job orchestration (provider ingestion → pack → reconcile → metrics → alerts)
- Live provider integrations (FMP, Polygon, NewsAPI) with retries/rate limits
- OpenTelemetry/Sentry wiring (opt-in only; defaults to disabled)
- Observability dashboards & broader test coverage

## Architecture (Single Path)
```
Streamlit UI → POST /v1/execute (FastAPI)
        ↓
Pattern Orchestrator (JSON patterns)
        ↓
Agent Runtime (financial analyst, macro, data harvester, ratings, claude)
        ↓
Services (pricing, ledger, macro, ratings, providers, metrics)
        ↓
PostgreSQL + TimescaleDB (seed data + rubrics)
```

See [PRODUCT_SPEC.md](PRODUCT_SPEC.md) and [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for guardrails and setup details.  
Tracing/metrics/error tracking can be enabled by setting `ENABLE_OBSERVABILITY=true` along with `JAEGER_ENDPOINT` / `SENTRY_DSN` in your `.env`.

## Remaining Work (Highlights)
1. Implement macro scenarios/DaR and hook up pattern outputs
2. Build optimizer service + UI (Riskfolio integration)
3. Complete rights-enforced exports + alerts DLQ/dedupe workflow
4. Add JWT auth/RBAC for API access
5. Harden nightly job chain (provider ingestion → pack → reconcile → metrics → alerts)
6. Wire observability (ENABLE_OBSERVABILITY + Jaeger/Sentry) and expand automated tests

A detailed backlog lives in [.ops/TASK_INVENTORY_2025-10-24.md](.ops/TASK_INVENTORY_2025-10-24.md).
