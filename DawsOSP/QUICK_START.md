# DawsOS Portfolio Platform - Quick Start Guide

> This version assumes the **canonical layout** is the one shown below. If your repo uses `/backend/app/...`, replace the paths accordingly (be consistent across docs and code).

### Prereqs

* Docker & docker compose v2, Python 3.11, Make, `psql`
* Provider dev/sandbox keys (or recorded fixtures for tests)

### 0. Clone & configure

```bash
git clone <repo-url> dawsos
cd dawsos

cp .env.example .env
# Fill in: FMP_API_KEY, POLYGON_API_KEY, FRED_API_KEY, NEWS_API_KEY (dev plan), AUTH_JWT_SECRET
# If you don’t have provider keys yet, tests will replay recorded fixtures; runtime calls still go through facades.
```

### 1. Start the stack

```bash
docker compose up -d
docker compose ps   # Wait for all to be "healthy"
```

### 2. Database migrations **+ Timescale enablement**

```bash
docker compose exec api psql -U dawsos -d dawsos -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
docker compose exec api alembic upgrade head
# (Optional) verify hypertables:
docker compose exec api psql -U dawsos -d dawsos -c \
  "SELECT table_name FROM timescaledb_information.hypertables;"
```

### 3. Seed **foundation + demo data** (packs, FX, ADR dividends)

```bash
# Foundation: symbols, benchmarks, FX (WM 16:00), split-adjusted prices, D0/D1 packs, rights registry, calendars
make seed:foundation

# Demo: CAD-base portfolio P1 (CAD+USD holdings), buy txns, ADR dividend with pay-date FX
make seed:demo

# Macro & cycles (regimes, STDC/LTDC/Empire snapshots)
make seed:macro
make seed:cycles

# Ratings rubrics & optimizer policies
make seed:ratings
make seed:optimizer

# (Optional) news dictionaries for metadata-only impact
make seed:news
```

### 4. Build a pack (if not seeded) & verify **pack freshness**

```bash
# Trigger nightly chain on demand (pack→reconcile→compute→pre-warm→fresh→alerts)
docker compose exec api python -m jobs.scheduler --once

# Health endpoint (must be "fresh"):
curl -s http://localhost:8000/health/pack | jq .
# {"status": "fresh", "pack_id": "PP_YYYY-MM-DD", "prewarm_done": true, ...}
```

### 5. Get a token (demo auth) & run a pattern

```bash
# If demo route exists:
TOKEN=$(curl -s -X POST http://localhost:8000/auth/demo-login | jq -r .access_token)

# Or load a seed JWT from scripts/jwt/dev.jwt (documented in /api/auth/README.md)
# TOKEN=$(cat scripts/jwt/dev.jwt)

# Execute 'portfolio_overview'
curl -s -X POST http://localhost:8000/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "portfolio_overview",
    "portfolio_id": "P1",
    "asof": "YYYY-MM-DD"
  }' | jq '.trace'
# Expect: pricing_pack_id, ledger_commit_hash, panel staleness, sources
```

### 6. Open the UI

```bash
open http://localhost:8501   # Streamlit
# Check: KPI ribbon, holdings table with rating badges, staleness chips, Explain drawer
```

### 7. Run tests (prove truth & guardrails)

```bash
# Unit and integration
docker compose exec api pytest tests/unit -q
docker compose exec api pytest tests/integration -q

# Golden (±1bp Beancount) incl. ADR pay-date FX
docker compose exec api pytest tests/golden -q

# Property (currency identity)
docker compose exec api pytest tests/property -q

# Security (RLS/IDOR fuzz)
docker compose exec api pytest tests/security -q

# Observability sanity
curl -s http://localhost:8000/metrics | grep -q "pattern_latency_seconds_bucket"
```

### 8. Export rights check (should block or watermark without license)

```bash
# Export PDF (rights gate enforced in staging)
curl -s -X POST http://localhost:8000/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern_id":"export_portfolio_report","portfolio_id":"P1","asof":"YYYY-MM-DD"}' \
  -o /tmp/portfolio.pdf
# If your registry forbids export without license, expect a RightsError (400); else, PDF with attributions footer.
```

---

## Troubleshooting (top 10)

| Symptom                               | Likely cause                                                   | Fix                                                                                       |
| ------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `/execute` returns 503 “pack warming” | Pack not built or pre-warm not done                            | Run `python -m jobs.scheduler --once`; re-check `/health/pack`                            |
| Golden tests fail (±1bp)              | ADR dividends not using pay-date FX; split restatement missing | Ensure dividend rows have `pay_fx_rate_id`; run `seed:foundation` & restatement rehearsal |
| Holdings empty                        | RLS context missing                                            | Verify `current_setting('app.user_id', true)` via `psql`; confirm JWT → API sets RLS      |
| Export PDF blocked                    | Rights registry forbids provider                               | Confirm YAML; append attributions or use licensed plan                                    |
| News panel empty                      | NewsAPI dev plan delay (24h)                                   | Dev uses metadata-only and staleness; OK                                                  |
| 429 from FMP/Polygon                  | Rate limit/bandwidth window                                    | Use sandbox/recorded fixtures for tests; let nightly pull bulk                            |
| UI calls provider directly            | Spec drift                                                     | Block via linter; fix to go through services                                              |
| p95 > 1.2s warm                       | No pre-warm; missing Prom spans                                | Verify pre-warm; check `/metrics`; add spans; inspect slow cap                            |
| IDOR tests failing                    | RLS/policies missing                                           | Re-run migrations; confirm policies on all portfolio tables                               |
| Compose healthy but swagger 500s      | Timescale ext missing                                          | `CREATE EXTENSION timescaledb;` and re-run migrations                                     |

---

## First PR checklist (dev confidence)

* [ ] No mocks in app code; tests use recorded fixtures or sandboxes
* [ ] Adds/updates OTel spans & Prom histogram per new capability
* [ ] Pattern results include `pricing_pack_id` + `ledger_commit_hash`
* [ ] Export path calls `reports.ensure_allowed()` + tests for block/watermark/attribution
* [ ] Golden ±1bp passes (incl. ADR pay-date FX)
* [ ] RLS/IDOR fuzz green; no PII in logs/error bodies
* [ ] Feature flag / rollback plan documented (if applicable)

---

## Small edits to your current quick start

* Replace `docker-compose` with `docker compose` (v2).
* Fix repo name typo: `cd DawsOSP` → `cd dawsos` (or consistent repo name).
* Add `CREATE EXTENSION timescaledb;` before migrations.
* Add `/health/pack` check and a one-shot nightly runner.
* Add `make seed:*` (foundation, demo, macro, cycles, ratings, optimizer, news).
* Add `/metrics` sanity check.
* Clarify demo auth route or provide a seed JWT.
* Document that NewsAPI in dev is metadata-only & delayed.

Make these changes and your quick start will let a new engineer spin the full system without “mock now, fix later” traps—and they’ll immediately see the guardrails (freshness, rights, RLS, observability) that keep the product production-honest.
