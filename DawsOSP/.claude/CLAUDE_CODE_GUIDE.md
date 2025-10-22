# Claude Code Implementation Guide for DawsOS

**Purpose**: Practical guide to using Claude Code inside VS Code to build DawsOS with agent-driven development
**Date**: 2025-10-21
**Version**: 1.0
**Target Audience**: Development team, implementation engineers

---

## Executive Summary

This guide shows how to use **Claude Code in VS Code** as your "build crew" to implement DawsOS agents, following the architectural guardrails and agent specifications. Claude Code can reason across the entire repository, propose multi-file changes, generate tests, and iterate—all while respecting your compliance boundaries.

**Key Benefits**:
- **Repo-scale reasoning**: Understands relationships across `/backend`, `/tests`, `/data/SEEDS`, patterns
- **Multi-file diffs**: Creates/modifies modules, tests, migrations, CI in one pass
- **Agent-driven**: Each `.claude/agents/*.md` spec becomes a buildable contract
- **Guardrail-aware**: Respects RLS, rights registry, reproducibility, SLOs when prompted correctly

---

## Table of Contents

1. [Core Capabilities](#core-capabilities)
2. [Repository Setup](#repository-setup)
3. [Agent Implementation Workflows](#agent-implementation-workflows)
4. [Prompt Patterns](#prompt-patterns)
5. [Testing Strategies](#testing-strategies)
6. [Infrastructure & DevEx](#infrastructure--devex)
7. [Security & Compliance](#security--compliance)
8. [Known Pitfalls & Mitigations](#known-pitfalls--mitigations)
9. [Example Build Sprint](#example-build-sprint)
10. [Reference Templates](#reference-templates)

---

## Core Capabilities

### 1. Repository-Scale Reasoning & Multi-File Edits

**What Claude Code Can Do**:
- Read entire repository (or selected folders) and maintain mental map of relationships
- Propose multi-file diffs: create/modify modules, tests, configs, migrations, CI, infra-as-code
- Refactor safely: rename symbols across files, adjust imports, maintain type integrity

**Use Cases for DawsOS**:
- Stand up `/backend/app` scaffold (FastAPI, services, DTOs, orchestrator)
- Generate **Alembic** migrations for final schema (pricing_pack, lots, transactions, hypertables)
- Implement **capability registry** + patterns; wire macros/ratings/optimizer services
- Build **seed loaders** and **Makefile** targets

**Example Prompt**:
```
Read `/PRODUCT_SPEC.md` and `/backend/app/core/registry.py`. Add capabilities
`cycles.compute_short_term`, `cycles.compute_long_term`, `cycles.compute_empire`
under `/backend/app/services/cycles.py`, create tests in `/tests/unit/test_cycles.py`
with seeded snapshots from `/data/SEEDS/macro_cycles/`. Return a single multi-file
diff. Don't touch unrelated files.
```

---

### 2. Inline & Panel Chat for Tight Loops

**What Claude Code Can Do**:
- **Inline chat**: Select code → "Explain", "Fix", "Refactor", "Write tests", "Document"
- **Panel chat**: High-level tasks (e.g., "Add pack freshness gate and tests"), with follow-ups

**Use Cases for DawsOS**:
- Quickly fix failing unit test
- Convert prototype function into typed, tested code with docstrings
- Generate docstrings & comments matching **method versioning** requirements (e.g., `div_safety_v1`)

**Example Inline Prompt**:
```
Refactor this function to be pure; move provider calls into
`/backend/app/services/providers/fmp_client.py`; add typing & error handling;
update call sites accordingly.
```

---

### 3. Repo-Wide Search & Context Injection

**What Claude Code Can Do**:
- **Add to context**: Point Claude Code at folders/files to inform responses
- Respects repository structure (e.g., `.claude/agents/`, `/data/SEEDS/`)

**Use Cases for DawsOS**:
- Feed in guardrails (architectural boundaries, RLS/rights rules) so all generated code adheres
- Ensure seeds & migrations match **end-state schema**

**Recommended Context Files** (pin at session start):
```
/PRODUCT_SPEC.md
/.ops/IMPLEMENTATION_ROADMAP_V2.md
/.claude/ARCHITECTURAL_GUARDRAILS.md
/data/SEEDS/**
/backend/app/core/*
/backend/app/services/*
/backend/app/db/models.py
/tests/**
```

---

### 4. Apply Diff Mode (Safe Changes)

**What Claude Code Can Do**:
- Proposes **diff preview** for all files it wants to change
- You approve/decline per file
- Keeps PRs clean and reviewable

**Use Cases for DawsOS**:
- Introduce **rights gate** in `reports.render_pdf` and see all changed files (including tests) before commit
- Add **RLS policies** and DB migrations without risky blanket edits

---

### 5. Task Decomposition & "Agents as Checklists"

**What Claude Code Can Do**:
- Follow structured checklists embedded in `.md` files
- Execute step-by-step
- Spawn **sub-tasks** if given sub-sections with clear acceptance criteria

**Use Cases for DawsOS**:
- **PROVIDER_INTEGRATOR**: Create FMPClient, PolygonClient, FREDClient, NewsClient with rate-limit/backoff/breakers + integration tests
- **MACRO_ARCHITECT**: Implement regime classifier, store macro_regime_snapshots, add calibration panel + tests
- **REPORTING_ARCHITECT**: Add rights registry YAML, wire `ensure_allowed()`, watermark fallback + PDF tests

**Example Prompt**:
```
Act as the `PROVIDER_INTEGRATOR` agent. Use `/.claude/agents/data/PROVIDER_INTEGRATOR.md`
as the contract. Produce code & tests for FMP/Polygon/FRED/NewsAPI facades with token
bucket, jittered backoff, and circuit breakers. Include a `RIGHTS_REGISTRY.yaml` loader
and blocking logic in `reports.render_pdf`. Show a single diff.
```

---

## Repository Setup

### 1. Context Files to Create

Before starting Claude Code sessions, ensure these files exist:

**Architectural Guardrails** (`.claude/ARCHITECTURAL_GUARDRAILS.md`):
```markdown
# DawsOS Architectural Guardrails

## 1. Single Execution Path
UI → Executor API → Pattern Orchestrator → Agent Runtime → Services → Data

**Violations to block**:
- Direct database queries from UI
- UI bypassing Executor API
- Services bypassing Pattern Orchestrator

## 2. Reproducibility
Every Result must include:
- `pricing_pack_id` (UUID)
- `ledger_commit_hash` (git SHA)
- `asof` timestamps per panel
- `sources` (provider list)

## 3. RLS Enforcement
All portfolio-scoped queries MUST:
- Set `app.user_id` context variable
- Use RLS-enabled tables
- Block cross-user access (403, not 404)

## 4. Rights Registry Compliance
All exports MUST:
- Call `ensure_allowed(providers, export_type)`
- Block if any provider disallows export
- Include attribution footer on all pages

## 5. Multi-Currency Truth
Three distinct FX types:
- Trade-time FX (locked in lots)
- Valuation-time FX (from pricing pack)
- Pay-date FX (for ADR dividends)

Invariant: `r_base ≈ (1+r_local)(1+r_fx) - 1 ± 0.1bp`

## 6. Method Versioning
All computed values MUST include:
- `method_version` (e.g., "div_safety_v1")
- `inputs_json` (for reproducibility)
- `computed_at` (ISO 8601 timestamp)

## 7. Performance Budgets
- Warm p95 ≤ 1.2s (pre-warmed pack)
- Cold p95 ≤ 2.0s (warming in progress)
- Pack build ≤ 15 minutes (complete by 00:15)
- Alert median ≤ 60s (trigger to delivery)

## 8. Testing Requirements
- Unit tests: ≥ 95% coverage
- Property tests: All invariants (Hypothesis)
- Golden tests: ±1bp tolerance
- Integration tests: End-to-end flows
- Security tests: RLS/IDOR fuzzing
- Chaos tests: Provider outage, DB failover
```

### 2. VS Code Workspace Settings

Create `.vscode/settings.json`:
```json
{
  "claude.contextFiles": [
    "PRODUCT_SPEC.md",
    ".ops/IMPLEMENTATION_ROADMAP_V2.md",
    ".claude/ARCHITECTURAL_GUARDRAILS.md"
  ],
  "claude.maxTokens": 8192,
  "python.linting.mypyEnabled": true,
  "python.linting.enabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests",
    "--cov=backend/app",
    "--cov-report=html"
  ]
}
```

### 3. Pre-Commit Hooks

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

---

## Agent Implementation Workflows

### Workflow 1: Implement PROVIDER_INTEGRATOR Agent

**Step 1: Add Context**
```
Add to context:
- /.claude/agents/data/PROVIDER_INTEGRATOR.md
- /PRODUCT_SPEC.md (Section 5: Providers)
- /.claude/ARCHITECTURAL_GUARDRAILS.md
- /data/SEEDS/providers/
```

**Step 2: Generate Provider Clients**
```
Act as PROVIDER_INTEGRATOR agent. Implement the following:

1. Create `/backend/app/services/providers/fmp_client.py`:
   - FMPClient class with circuit breaker (3 failures → OPEN)
   - Rate limiting (120 req/min via token bucket)
   - Jittered exponential backoff (base: 1s, max: 60s)
   - Methods: get_quote(), get_fundamentals(), get_financials()

2. Create `/backend/app/services/providers/polygon_client.py`:
   - PolygonClient for corporate actions (splits, dividends)
   - Rate limiting (100 req/min)
   - Methods: get_splits(), get_dividends()

3. Create `/backend/app/services/providers/fred_client.py`:
   - FREDClient for macro indicators
   - Methods: get_series(), get_latest()

4. Create `/backend/app/services/providers/newsapi_client.py`:
   - NewsAPIClient (metadata-only for dev tier)
   - Methods: search_news()

5. Create `/tests/integration/test_providers.py`:
   - Circuit breaker tests (3 failures → OPEN → HALF_OPEN → CLOSED)
   - Rate limiting tests (429 retry)
   - Sandbox/prod key separation tests

Requirements:
- Use Pydantic DTOs from `/backend/app/dto/providers.py`
- All secrets from environment variables (no hardcoding)
- Type hints + docstrings
- Error handling with custom exceptions

Return single multi-file diff. Don't touch unrelated files.
```

**Step 3: Add Rights Registry**
```
Add rights enforcement to PROVIDER_INTEGRATOR:

1. Create `/.ops/RIGHTS_REGISTRY.yaml`:
   - FMP: allows_export_pdf=true, allows_export_csv=true
   - Polygon: allows_export_pdf=true, allows_export_csv=true
   - FRED: allows_export_pdf=true, allows_redistribution=true
   - NewsAPI: allows_export_pdf=false (Enterprise only)

2. Create `/backend/app/core/rights_registry.py`:
   - load_rights_registry() → dict
   - ensure_allowed(providers: list[str], export_type: str) → (bool, list[str])
   - get_attribution_text(providers: list[str]) → str

3. Wire into `/backend/app/api/reports.py`:
   - Call ensure_allowed() before PDF generation
   - Raise RightsViolationError if blocked
   - Include attribution footer on all PDF pages

4. Create `/tests/integration/test_rights_enforcement.py`:
   - Test FMP+Polygon export allowed
   - Test NewsAPI export blocked
   - Test attribution text includes all providers

Return diff.
```

**Step 4: Verify Acceptance Criteria**
```
Review PROVIDER_INTEGRATOR acceptance criteria from
`/.claude/agents/data/PROVIDER_INTEGRATOR.md`. For each AC:

1. AC-1: Circuit Breaker Engagement
   - Run: pytest tests/chaos/test_circuit_breaker.py
   - Expected: CLOSED → OPEN → HALF_OPEN → CLOSED

2. AC-2: Rate Limiting (429 Retry)
   - Run: pytest tests/integration/test_rate_limiting.py
   - Expected: Exponential backoff with jitter

3. AC-3: Rights Gate (NewsAPI Blocked)
   - Run: pytest tests/integration/test_rights_enforcement.py
   - Expected: 403 error with "NewsAPI data cannot be exported"

Report which ACs pass/fail. If any fail, propose fixes.
```

---

### Workflow 2: Implement MACRO_ARCHITECT Agent

**Step 1: Add Context**
```
Add to context:
- /.claude/agents/intelligence/MACRO_ARCHITECT.md
- /data/SEEDS/macro_cycles/macro_cycle_definitions.json
- /data/SEEDS/macro_indicators/
- /PRODUCT_SPEC.md (Section 7: Macro)
```

**Step 2: Generate Macro Services**
```
Act as MACRO_ARCHITECT agent. Implement:

1. `/backend/app/services/macro.py`:
   - detect_regime(indicators: dict) → Regime (5 regimes)
   - compute_factor_exposure(portfolio_id, pack_id) → FactorExposure
   - compute_dar(portfolio_id, scenarios, confidence=0.95) → float

2. `/backend/app/services/cycles.py`:
   - Load cycle definitions from `/data/SEEDS/macro_cycles/macro_cycle_definitions.json`
   - detect_cycle_phase(cycle_id, indicators) → CyclePhase
   - Implement STDC, LTDC, Empire cycle detectors

3. `/backend/app/db/models.py` (add):
   - MacroRegimeSnapshot table (regime, probs_json, drivers_json)
   - CyclePhaseSnapshot table (cycle_id, phase, score, drivers_json)

4. `/tests/golden/macro/test_regime_detection.py`:
   - Golden tests for dot-com bubble, 2008 crisis, 2020 COVID
   - Use fixtures from `/data/SEEDS/macro_indicators/`

Requirements:
- Regimes: Early/Mid/Late Expansion, Early/Deep Contraction
- Z-scores for all indicators (T10Y2Y, UNRATE, CPIAUCSL)
- Method versioning: "regime_v1", "stdc_v1", "ltdc_v1", "empire_v1"

Return diff.
```

**Step 3: Add DaR Calculation**
```
Add Drawdown at Risk (DaR) to MACRO_ARCHITECT:

1. `/backend/app/services/risk.py`:
   - compute_dar(portfolio_id, scenarios, confidence=0.95) → float
   - apply_scenario(portfolio_id, scenario) → float (ΔP/L)
   - Scenarios: Rates +50bp, USD +5%, CPI +0.4%

2. `/tests/integration/test_dar.py`:
   - Test DaR calculation for 60/40 portfolio
   - Expected: p95 loss between -8% and -12%

3. UI calibration view stub:
   - `/ui/screens/dar_calibration.py` (placeholder)
   - Show MAD (Mean Absolute Deviation) and hit rate
   - Note: Full implementation in Sprint 4

Return diff.
```

---

### Workflow 3: Implement TEST_ARCHITECT Agent

**Step 1: Generate Test Infrastructure**
```
Act as TEST_ARCHITECT agent. Set up test infrastructure:

1. Create `/tests/conftest.py`:
   - Database fixtures (test_db, test_session)
   - User fixtures (test_user_alice, test_user_bob)
   - Portfolio fixtures (test_portfolio_growth, test_portfolio_income)
   - Pricing pack fixtures (test_pack_2024_10_21)

2. Create `/tests/fixtures/seed_test_data.py`:
   - seed_users() - 5 test users
   - seed_portfolios() - 10 portfolios
   - seed_securities() - S&P 500 top 50
   - seed_transactions() - 200 trades (buys, sells, dividends)
   - seed_pricing_packs() - 30 days historical
   - seed_fx_rates() - USD, CAD, EUR, GBP (30 days)

3. Create `pyproject.toml` (pytest config):
   - Test markers: unit, property, golden, integration, security, chaos, performance
   - Coverage settings: ≥95% overall, ≥98% core, ≥95% services, ≥90% API
   - Hypothesis settings: 1000 examples, 5s deadline

Return diff.
```

**Step 2: Generate Property Tests**
```
Create property tests for currency invariants:

1. `/tests/property/test_currency_attribution.py`:
   - Test: r_base ≈ (1+r_local)(1+r_fx) - 1 ± 0.1bp
   - Use Hypothesis to generate 1000+ input combinations
   - All currencies: USD, CAD, EUR, GBP, JPY, AUD, CHF

2. `/tests/property/test_fx_triangulation.py`:
   - Test: USD→CAD→EUR === USD→EUR (via cross-rate) ± 1¢
   - Generate random exchange rates

3. `/tests/property/test_pricing_pack_immutability.py`:
   - Test: Pricing packs are append-only (no mutations)
   - Verify ImmutabilityViolationError raised on modification attempts

Requirements:
- Use @given decorator from Hypothesis
- All property tests must pass 1000+ examples
- CI profile: max_examples=1000, deadline=5000ms

Return diff.
```

**Step 3: Generate Golden Tests**
```
Create golden tests for regression protection:

1. `/tests/golden/attribution/aapl_oct2023.json`:
   - Fixture with known AAPL attribution (Oct 2023)
   - TWR: 2.35%, Local: 1.80%, FX: 0.50%, Interaction: 0.05%

2. `/tests/golden/attribution/test_attribution.py`:
   - Load golden fixture
   - Compute attribution with pack_id "2023-10-31-WM4PM-CAD"
   - Assert ±1bp tolerance

3. `/tests/golden/multi_currency/adr_paydate_fx.json`:
   - ADR dividend with pay-date FX example
   - AAPL, 100 shares, $0.24/share
   - Ex-date FX: 1.34 USD/CAD, Pay-date FX: 1.36 USD/CAD
   - Correct: $32.64 CAD, Wrong (if ex-date): $32.16 CAD
   - Accuracy impact: 48¢

4. `/tests/golden/regime/dotcom_bubble.json`:
   - Indicators for dot-com bubble (1999-2000)
   - Expected regime: Late Expansion

Return diff for all golden tests.
```

---

## Prompt Patterns

### Pattern 1: Agent-Driven Implementation

**Template**:
```
Act as the {AGENT_NAME} agent. Use `/.claude/agents/{type}/{AGENT_NAME}.md`
as the contract.

Implement:
1. {Deliverable 1}
2. {Deliverable 2}
3. {Deliverable 3}

Requirements:
- {Requirement 1}
- {Requirement 2}
- {Requirement 3}

Return single multi-file diff. Don't touch unrelated files.
```

**Example**:
```
Act as the RATINGS_ARCHITECT agent. Use `/.claude/agents/intelligence/RATINGS_ARCHITECT.md`
as the contract.

Implement:
1. `/backend/app/services/ratings.py`:
   - compute_dividend_safety(symbol, pack_id) → float (0-10 scale)
   - compute_moat_strength(symbol, pack_id) → float
   - compute_resilience(symbol, pack_id) → float

2. Nightly pre-warm job (00:08 local time):
   - Pre-warm ratings for all S&P 500 holdings
   - Store in `ratings` table with method_version and inputs_json

3. `/tests/golden/ratings/ko_wmt_jnj.json`:
   - Golden test for KO, WMT, JNJ quality scores
   - DivSafety, Moat, Resilience (each 0-10)

Requirements:
- DivSafety components: Payout ratio (30%), FCF coverage (35%), growth streak (20%), net cash (15%)
- Moat components: ROE consistency, gross margin, intangibles, switching costs
- Method versioning: "div_safety_v1", "moat_v1", "resilience_v1"

Return diff.
```

---

### Pattern 2: Constrained Multi-File Refactor

**Template**:
```
Refactor {component} to {goal}.

Changes allowed:
- Files under {directory pattern}
- Tests in {test directory}

Changes NOT allowed:
- Don't touch {exclude pattern}
- Don't modify {specific files}

Requirements:
- {Requirement 1}
- {Requirement 2}

Return single diff with before/after for each file.
```

**Example**:
```
Refactor provider clients to use dependency injection.

Changes allowed:
- Files under `/backend/app/services/providers/`
- Tests in `/tests/integration/test_providers.py`

Changes NOT allowed:
- Don't touch `/backend/app/api/`
- Don't modify existing DTOs in `/backend/app/dto/`

Requirements:
- All clients accept config via constructor (not env vars directly)
- Use Protocol for provider interface
- Update tests to use mocked configs

Return single diff.
```

---

### Pattern 3: Test-First Development

**Template**:
```
Implement {feature} using TDD:

1. Write failing tests in {test file}:
   - Test: {test case 1}
   - Test: {test case 2}
   - Test: {test case 3}

2. Implement code in {implementation file} to make tests pass

3. Verify all tests pass and coverage ≥ {threshold}%

Return diff showing tests (red) then implementation (green).
```

**Example**:
```
Implement ledger reconciliation using TDD:

1. Write failing tests in `/tests/integration/test_ledger_reconciliation.py`:
   - Test: reconciliation within ±1bp for single-currency portfolio
   - Test: reconciliation within ±1bp for multi-currency portfolio
   - Test: reconciliation alert triggered when diff > 1bp

2. Implement code in `/backend/app/jobs/reconcile_ledger.py` to make tests pass

3. Verify all tests pass and coverage ≥ 95%

Return diff showing tests (red) then implementation (green).
```

---

### Pattern 4: Performance Budget Enforcement

**Template**:
```
Implement {feature} with performance budget:

- Warm p95 ≤ {warm_threshold}ms
- Cold p95 ≤ {cold_threshold}ms
- No N×M loops over {large collections}
- Use {optimization technique}

Include performance tests in {test file}.
Show profile results.
```

**Example**:
```
Implement portfolio valuation with performance budget:

- Warm p95 ≤ 600ms (pre-warmed pack)
- Cold p95 ≤ 1200ms (warming in progress)
- No N×M loops over positions × prices (use vectorized ops)
- Use bulk lookups for pricing pack prices

Include performance tests in `/tests/performance/test_valuation_latency.py`.
Show profile results (cProfile output).
```

---

## Testing Strategies

### Strategy 1: Golden Test Workflow

**Prompt**:
```
Create golden test for {feature}:

1. Generate fixture in `/tests/golden/{category}/{name}.json`:
   - Include inputs, expected outputs, metadata
   - Schema version, method version, tolerance

2. Create test in `/tests/golden/{category}/test_{name}.py`:
   - Load fixture
   - Run computation with exact inputs from fixture
   - Assert output matches expected ± tolerance

3. Add to CI golden suite:
   - Update `pytest tests/golden/ --golden-update=never`
   - Ensure byte-for-byte match (excluding timestamps)

Example fixture structure:
{
  "description": "...",
  "inputs": {...},
  "expected_output": {...},
  "tolerance_bp": 1,
  "method_version": "...",
  "schema_version": "1.0"
}

Return diff for fixture + test.
```

---

### Strategy 2: Property Test Workflow

**Prompt**:
```
Create property test for invariant: {invariant description}

1. Use Hypothesis @given decorator with strategies:
   - {Strategy 1}
   - {Strategy 2}
   - {Strategy 3}

2. Test invariant holds for 1000+ generated examples

3. Edge cases to include:
   - {Edge case 1}
   - {Edge case 2}
   - {Edge case 3}

4. CI profile:
   - max_examples=1000
   - deadline=5000ms
   - derandomize=false

Return diff for `/tests/property/test_{name}.py`.
```

**Example**:
```
Create property test for invariant: r_base ≈ (1+r_local)(1+r_fx) - 1 ± 0.1bp

1. Use Hypothesis @given decorator with strategies:
   - local_return: st.floats(min_value=-0.5, max_value=0.5)
   - fx_return: st.floats(min_value=-0.3, max_value=0.3)

2. Test invariant holds for 1000+ generated examples

3. Edge cases to include:
   - Large FX swings (±20%)
   - Small local returns (< 0.01%)
   - Negative returns + positive FX
   - Zero returns (identity check)

4. CI profile:
   - max_examples=1000
   - deadline=5000ms
   - derandomize=false

Return diff for `/tests/property/test_currency_attribution.py`.
```

---

### Strategy 3: Chaos Test Workflow

**Prompt**:
```
Create chaos test for scenario: {chaos scenario}

1. Setup:
   - {Infrastructure setup}
   - {Failure injection method}

2. Execute:
   - {System under test}
   - {Expected degraded behavior}

3. Verify:
   - {Recovery condition}
   - {Data integrity check}
   - {No silent failures}

4. Cleanup:
   - {Restore normal state}

Use pytest + toxiproxy/chaos toolkit.
Return diff for `/tests/chaos/test_{name}.py`.
```

**Example**:
```
Create chaos test for scenario: Provider outage → Circuit breaker engagement

1. Setup:
   - Spin up test FMP endpoint (mock)
   - Configure circuit breaker (3 failures → OPEN)

2. Execute:
   - Simulate 3 consecutive FMP failures (HTTP 500)
   - Verify circuit breaker state = OPEN
   - Subsequent requests short-circuit (no timeout wait)

3. Verify:
   - Alert triggered: "FMP circuit breaker OPEN"
   - Fallback to cached pricing pack (if available)
   - After 60s timeout → HALF_OPEN
   - After successful request → CLOSED

4. Cleanup:
   - Restore FMP mock to healthy state

Return diff for `/tests/chaos/test_circuit_breaker.py`.
```

---

## Infrastructure & DevEx

### DevEx 1: Makefile Generation

**Prompt**:
```
Create Makefile with targets:

1. Seed management:
   - make seed:load - Load all seeds from /data/SEEDS/
   - make seed:validate - Validate seed integrity
   - make seed:generate-demo-pack - Generate demo pricing pack

2. Development:
   - make dev-api - Run FastAPI (uvicorn, reload=true)
   - make dev-ui - Run Streamlit UI
   - make dev-worker - Run RQ worker
   - make dev-scheduler - Run APScheduler

3. Database:
   - make migrate - Run Alembic migrations
   - make db-reset - Drop + recreate + seed
   - make db-shell - Open psql shell

4. Testing:
   - make test - Run all tests
   - make test-unit - Unit tests only (≥95% coverage)
   - make test-golden - Golden tests (no updates)
   - make test-chaos - Chaos tests
   - make test-watch - Watch mode (pytest-watch)

5. Quality:
   - make lint - Run ruff + mypy
   - make format - Run ruff format
   - make validate - Lint + type check + tests

6. CI/CD:
   - make ci - Full CI pipeline locally
   - make docker-build - Build all images
   - make docker-push - Push to registry

Return Makefile with proper .PHONY declarations.
```

---

### DevEx 2: VS Code Launch Configurations

**Prompt**:
```
Create `.vscode/launch.json` with configurations:

1. FastAPI Backend:
   - Program: uvicorn
   - Args: backend.app.main:app --reload --host 0.0.0.0 --port 8000
   - Env: DATABASE_URL, REDIS_URL, FMP_API_KEY, etc.

2. Streamlit UI:
   - Program: streamlit
   - Args: run ui/main.py --server.port 8501

3. RQ Worker:
   - Program: rq
   - Args: worker --with-scheduler

4. Pytest (All):
   - Program: pytest
   - Args: tests/ --cov=backend/app --cov-report=html

5. Pytest (Single Test):
   - Program: pytest
   - Args: ${file} (current file)

6. Alembic Migration:
   - Program: alembic
   - Args: upgrade head

Include proper environment variables and cwd settings.
Return `.vscode/launch.json`.
```

---

### DevEx 3: Terraform Infrastructure

**Prompt**:
```
Generate Terraform modules under `/.infra/terraform/`:

1. `/modules/database/`:
   - PostgreSQL + TimescaleDB (RDS Multi-AZ or self-hosted)
   - Instance class: db.r6g.xlarge
   - Storage: 500GB gp3
   - Backup retention: 7 days
   - Hypertables: portfolio_metrics, currency_attribution, factor_exposures

2. `/modules/cache/`:
   - ElastiCache Redis cluster
   - Node type: cache.r6g.large
   - Replicas: 2
   - Eviction policy: volatile-lru

3. `/modules/storage/`:
   - S3 buckets: reports, backups, dlq
   - Lifecycle rules: reports 30d, backups 90d
   - Encryption: SSE-KMS

4. `/modules/secrets/`:
   - AWS Secrets Manager
   - Secrets: DB_PASSWORD, FMP_API_KEY, POLYGON_API_KEY, etc.
   - Rotation: enabled for DB credentials

5. `/modules/monitoring/`:
   - Prometheus (ECS or k8s)
   - Jaeger (ECS or k8s)
   - Alertmanager → PagerDuty

6. Root module:
   - Compose all modules
   - Outputs: db_endpoint, redis_endpoint, s3_buckets, etc.

Include variables.tf, outputs.tf, and example terraform.tfvars (no real secrets).
Return multi-file diff.
```

---

## Security & Compliance

### Security 1: RLS/IDOR Fuzzing

**Prompt**:
```
Create RLS/IDOR fuzz tests:

1. `/tests/security/test_rls_fuzz.py`:
   - Generate 100+ random user/portfolio combinations
   - User A attempts to access User B's portfolio
   - Expected: 403 Forbidden (not 404)
   - Verify RLS policy enforced (query Postgres logs)

2. Fuzzing strategy:
   - Use Hypothesis to generate (user_a_jwt, user_b_portfolio_id) pairs
   - Ensure no PII in error bodies
   - Ensure no data leakage (zero rows returned)

3. CI integration:
   - Run on every PR
   - Fail if any cross-user access succeeds

Return diff for `/tests/security/test_rls_fuzz.py`.
```

---

### Security 2: Secret Scanning

**Prompt**:
```
Add secret scanning to pre-commit and CI:

1. Pre-commit hook:
   - Use detect-secrets
   - Baseline: .secrets.baseline
   - Block commits with new secrets

2. CI job:
   - Run truffleHog or GitGuardian
   - Scan entire history
   - Fail on High severity findings

3. Exception handling:
   - Allow false positives via .secrets.baseline
   - Document exception process (PR + approval)

Return:
- `.pre-commit-config.yaml` update
- `.github/workflows/security.yml` job definition
```

---

### Security 3: SBOM & SCA

**Prompt**:
```
Add SBOM generation and SCA scanning to CI:

1. SBOM generation:
   - Use syft to generate SPDX JSON
   - Store as artifact for each release

2. License compliance:
   - Use ort to analyze SBOM
   - Block on copyleft licenses (GPL, AGPL, SSPL)
   - Allow: MIT, Apache-2.0, BSD-3-Clause

3. Vulnerability scanning:
   - Use grype on SBOM
   - Fail on High/Critical vulns in production deps

4. CI workflow:
   - Stage: SBOM & SCA (after build)
   - Artifacts: sbom.json, ort-results.json, grype-report.json

Return `.github/workflows/security.yml` with SBOM/SCA job.
```

---

## Known Pitfalls & Mitigations

### Pitfall 1: Massive Diffs

**Problem**: Claude Code generates 50-file diffs that are hard to review

**Mitigation**:
```
Ask for scoped diffs per module; run in batches:

Example:
"Implement pricing pack service. Return diff for:
1. /backend/app/services/pricing_pack.py
2. /backend/app/db/models.py (pricing_pack table only)
3. /tests/unit/test_pricing_pack.py

Don't touch other files. After approval, we'll do migrations separately."
```

---

### Pitfall 2: Spec Drift

**Problem**: Generated code doesn't match PRODUCT_SPEC or agent specs

**Mitigation**:
```
Keep PRODUCT_SPEC.md and agent specs pinned to context.

After each task, ask:
"Review this diff against PRODUCT_SPEC.md Section {X} and
/.claude/agents/{type}/{AGENT_NAME}.md. List any violations of:
- Architectural guardrails
- Acceptance criteria
- Performance budgets
- Security requirements

If violations found, propose fixes."
```

---

### Pitfall 3: Provider Costs

**Problem**: Tests hit real APIs and incur costs

**Mitigation**:
```
Embed budget guards into tests:

1. Use sandbox/test API keys (not production)
2. Add caching layer for repeated queries
3. Use seed fixtures instead of live data
4. Add dry-run mode that uses cached responses

Example:
"Update provider tests to use fixtures from /data/SEEDS/providers/.
Only hit real API if PROVIDER_INTEGRATION_TEST=true env var set.
Add warning banner when running live tests."
```

---

### Pitfall 4: Rights Compliance Gaps

**Problem**: Export paths bypass rights registry

**Mitigation**:
```
Force rights check in all export paths:

"Review all endpoints in /backend/app/api/ that return:
- PDF (content-type: application/pdf)
- CSV (content-type: text/csv)
- Excel (content-type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

Ensure all call ensure_allowed() before generating output.
Add tests for each export path.

Return diff showing rights gate wiring + tests."
```

---

## Example Build Sprint

### Day 1: Infrastructure & Truth Spine

**Morning (4 hours)**:
```
Session 1: Terraform Infrastructure
- Generate Terraform modules (DB, Redis, S3, Secrets, Monitoring)
- Apply to staging environment
- Verify outputs (db_endpoint, redis_endpoint)

Session 2: Database Schema
- Generate Alembic migrations (25 tables, RLS policies, hypertables)
- Run migrations on staging
- Verify: 25 tables, 14 RLS policies, 3 hypertables
```

**Afternoon (4 hours)**:
```
Session 3: Provider Integrators
- Implement FMP/Polygon/FRED/NewsAPI clients
- Add circuit breaker, rate limiting, jittered backoff
- Tests: circuit breaker, 429 retry, sandbox/prod separation

Session 4: Pricing Pack Builder
- Implement nightly pack build job (00:05)
- Add immutability enforcement
- Tests: pack creation, immutability violation, superseded path
```

---

### Day 2: Execution Path & Metrics

**Morning (4 hours)**:
```
Session 1: Executor API
- Implement /v1/execute endpoint
- Add freshness gate (reject if pack not fresh)
- Set RLS context (app.user_id)
- Tests: freshness gate, RLS enforcement

Session 2: Pattern Orchestrator
- Implement DAG runner (stub for now)
- Add trace collection (steps, duration, sources)
- Tests: pattern execution, trace metadata
```

**Afternoon (4 hours)**:
```
Session 3: Metrics Service
- Implement TWR/MWR/Sharpe calculations
- Add currency attribution (local/FX/interaction)
- Tests: TWR matches Beancount ±1bp

Session 4: Ledger Reconciliation
- Implement nightly reconciliation job (00:10)
- Add ±1bp tolerance check
- Alert on breach
- Tests: reconciliation pass/fail, alert trigger
```

---

### Day 3: UI & Observability

**Morning (4 hours)**:
```
Session 1: UI Portfolio Overview
- Implement Streamlit Overview screen
- Add DawsOS dark theme (CSS)
- Add provenance badges (pack ID, ledger hash)
- Tests: visual regression (Percy)

Session 2: Holdings Table
- Implement holdings table with rating badges
- Add sortable columns, filters
- Tests: rendering, sorting, filtering
```

**Afternoon (4 hours)**:
```
Session 3: Observability Skeleton
- Wire OpenTelemetry (FastAPI instrumentation)
- Add Prometheus metrics (API latency, pack build duration)
- Configure Sentry error tracking
- Tests: trace propagation, metrics scraping

Session 4: Rights Gate
- Wire rights registry into PDF export
- Add attribution footers
- Tests: NewsAPI blocked, FMP allowed, attribution text
```

---

### Day 4-5: Macro, Ratings, Optimizer

**Day 4**:
```
Morning: MACRO_ARCHITECT
- Implement regime detection (5 regimes)
- Implement macro cycles (STDC/LTDC/Empire)
- Implement DaR calculation
- Tests: golden tests (dot-com, 2008, COVID)

Afternoon: RATINGS_ARCHITECT
- Implement Buffett quality (DivSafety, Moat, Resilience)
- Add nightly pre-warm job (00:08)
- Tests: golden tests (KO, WMT, JNJ)
```

**Day 5**:
```
Morning: OPTIMIZER_ARCHITECT
- Implement mean-variance optimization (Riskfolio-Lib)
- Add policy constraints (sector limits, quality floors)
- Generate rebalance suggestions
- Tests: optimizer output, TE limits

Afternoon: REPORTING_ARCHITECT
- Implement PDF export (WeasyPrint)
- Add multi-page layout (cover, TOC, sections)
- Wire rights gate (already done)
- Tests: PDF generation, reproducibility (same pack → identical PDF)
```

---

## Reference Templates

### Template 1: Agent Implementation Prompt

```markdown
# Agent Implementation: {AGENT_NAME}

## Context Files
Add to context:
- /.claude/agents/{type}/{AGENT_NAME}.md
- /PRODUCT_SPEC.md (Section {X})
- /.claude/ARCHITECTURAL_GUARDRAILS.md
- /data/SEEDS/{relevant_seeds}/

## Implementation Request

Act as the {AGENT_NAME} agent. Use `/.claude/agents/{type}/{AGENT_NAME}.md` as the contract.

### Deliverables

1. **{Deliverable 1}** (`{file_path_1}`):
   - {Requirement 1a}
   - {Requirement 1b}
   - {Requirement 1c}

2. **{Deliverable 2}** (`{file_path_2}`):
   - {Requirement 2a}
   - {Requirement 2b}

3. **Tests** (`{test_file_path}`):
   - {Test case 1}
   - {Test case 2}
   - {Test case 3}

### Requirements

- {Global requirement 1}
- {Global requirement 2}
- {Global requirement 3}

### Constraints

- Use {technology/library}
- Type hints + docstrings required
- Coverage ≥ {threshold}%
- Performance budget: {metric} ≤ {threshold}

### Output

Return single multi-file diff. Don't touch unrelated files.

After implementation, verify against acceptance criteria from agent spec:
- [ ] AC-1: {Acceptance criterion 1}
- [ ] AC-2: {Acceptance criterion 2}
- [ ] AC-3: {Acceptance criterion 3}

Report which ACs pass/fail. If any fail, propose fixes.
```

---

### Template 2: Test Generation Prompt

```markdown
# Test Generation: {Feature Name}

## Test Type: {Unit|Property|Golden|Integration|Security|Chaos|Performance}

### Fixture Setup

1. **Fixtures** (`/tests/fixtures/{category}/`):
   - {Fixture 1}: {Description}
   - {Fixture 2}: {Description}

2. **Seeds** (`/data/SEEDS/{category}/`):
   - Use: {Seed file 1}
   - Use: {Seed file 2}

### Test Cases

**Test File**: `/tests/{type}/test_{name}.py`

1. **Test: {Test case 1}**
   - Given: {Precondition}
   - When: {Action}
   - Then: {Expected outcome}

2. **Test: {Test case 2}**
   - Given: {Precondition}
   - When: {Action}
   - Then: {Expected outcome}

3. **Test: {Test case 3}**
   - Given: {Precondition}
   - When: {Action}
   - Then: {Expected outcome}

### Success Criteria

- [ ] All tests pass
- [ ] Coverage ≥ {threshold}%
- [ ] {Type-specific criterion (e.g., property holds for 1000+ examples)}

### Output

Return diff for:
- Test file(s)
- Fixture file(s)
- Configuration updates (if needed)
```

---

## Summary

This guide provides **proven patterns** for using Claude Code to build DawsOS:

✅ **Repo-scale reasoning** - Understands full architecture, generates multi-file diffs
✅ **Agent-driven workflows** - Each agent spec becomes buildable contract
✅ **Guardrail enforcement** - RLS, rights registry, reproducibility, SLOs respected
✅ **Test automation** - Unit, property, golden, integration, security, chaos, performance
✅ **Infrastructure as code** - Terraform, Helm, ECS, Makefile, VS Code configs
✅ **Security compliance** - RLS/IDOR fuzzing, secret scanning, SBOM/SCA

**Key Success Factors**:
1. Pin context files (PRODUCT_SPEC, ARCHITECTURAL_GUARDRAILS, agent specs)
2. Use scoped prompts (constrain changes, specify file patterns)
3. Test-first development (write failing tests, then implementation)
4. Iterative refinement (verify acceptance criteria after each task)
5. Batch execution (services → tests → patterns → seeds)

**Next Actions**:
1. Create `.claude/ARCHITECTURAL_GUARDRAILS.md`
2. Set up `.vscode/settings.json` with context files
3. Add pre-commit hooks (ruff, mypy, detect-secrets)
4. Start Day 1 sprint (Terraform → Schema → Providers → Pack)

---

**Signed**: Build System Architect
**Date**: 2025-10-21
**Version**: 1.0 (Claude Code integration)
