# DawsOS CI/CD Pipeline v2.0

**Purpose**: End-to-end automated deployment pipeline with canary rollout and automatic rollback
**Updated**: 2025-10-21
**Priority**: P0 (Critical for production readiness)

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 1-7: Quality Gates (Block on Failure)                        │
│ STAGE 8-9: Artifacts & Security                                    │
│ STAGE 10-11: Staging Validation                                    │
│ STAGE 12: Canary Production (Auto-rollback on SLO breach)          │
└─────────────────────────────────────────────────────────────────────┘
```

**Total Pipeline Duration**: ~25 minutes (commit → canary start)
**Canary Duration**: 30 minutes (5% → 25% → 100%)
**Rollback Time**: < 60 seconds (automatic on SLO breach)

---

## Stage 1: Lint & Type Check

**Duration**: ~2 minutes
**Block on**: Any error
**Tools**: ruff, mypy, sqlfluff

### Backend Checks
```bash
# Python linting
ruff check backend/ --config=pyproject.toml
ruff format --check backend/

# Type checking
mypy backend/ --config-file=pyproject.toml --strict

# SQL linting
sqlfluff lint backend/migrations/ --dialect=postgres
```

### Frontend Checks (if applicable)
```bash
# TypeScript/Next.js
eslint frontend/ --ext .ts,.tsx
tsc --noEmit
prettier --check frontend/
```

**Exit Criteria**: Zero errors, zero type violations

---

## Stage 2: Unit Tests

**Duration**: ~3 minutes
**Block on**: < 95% coverage or any failure
**Tools**: pytest, pytest-cov

```bash
cd backend/
pytest tests/unit/ \
  --cov=app \
  --cov-report=term-missing \
  --cov-fail-under=95 \
  --tb=short \
  --maxfail=5

# Required coverage per module
# - app/core/: 98%
# - app/services/: 95%
# - app/api/: 90%
```

**Artifacts**: `coverage.xml` (for SonarQube), `htmlcov/`

**Exit Criteria**:
- Overall coverage ≥ 95%
- Zero test failures
- No flaky tests (3-run verification)

---

## Stage 3: Property Tests

**Duration**: ~5 minutes
**Block on**: Any property violation
**Tools**: Hypothesis

```bash
pytest tests/property/ \
  --hypothesis-profile=ci \
  --hypothesis-seed=random

# Key property tests
# - Multi-currency arithmetic (no rounding errors beyond 1bp)
# - Pricing pack immutability (append-only invariant)
# - TWR calculation (commutative across date ranges)
# - RLS policies (no cross-portfolio leaks)
```

**Exit Criteria**: All properties hold under 1000+ generated inputs

---

## Stage 4: Golden Tests

**Duration**: ~2 minutes
**Block on**: Any diff vs golden outputs
**Tools**: pytest, jsondiff

```bash
pytest tests/golden/ --golden-update=never

# Golden test coverage
# - Attribution calculation (AAPL example from Oct 2023)
# - Factor exposure (60/40 portfolio vs S&P/AGG)
# - Dalio regime (dot-com bubble, 2008 crisis, 2020 COVID)
# - Buffett ratings (KO, WMT, JNJ quality scores)
```

**Exit Criteria**: Byte-for-byte match with approved golden outputs

---

## Stage 5: Integration Tests

**Duration**: ~6 minutes
**Block on**: Any failure, provider outage ignored if circuit breaker works
**Tools**: pytest, Docker Compose (test DB)

```bash
# Spin up test stack
docker-compose -f docker-compose.test.yml up -d postgres timescale redis

# Run integration tests
pytest tests/integration/ \
  --tb=short \
  --maxfail=10 \
  -m "not slow"

# Test coverage
# - Ledger reconciliation (±1bp validation)
# - Pricing pack build (all currencies, ADR dividends)
# - Alert delivery (cooldown, deduplication)
# - Multi-portfolio RLS (user isolation)
# - Provider circuit breaker (graceful degradation)
```

**Exit Criteria**:
- All critical flows pass
- Circuit breaker engages on simulated provider outage
- No DB constraint violations

**Cleanup**:
```bash
docker-compose -f docker-compose.test.yml down -v
```

---

## Stage 6: Security Tests

**Duration**: ~4 minutes
**Block on**: High/Critical findings
**Tools**: Bandit, Safety, Trivy

```bash
# Python security scan
bandit -r backend/ -f json -o bandit-report.json
safety check --json

# Container image scan (after Stage 8)
trivy image dawsos-backend:${GIT_SHA} \
  --severity HIGH,CRITICAL \
  --exit-code 1
```

**Exit Criteria**:
- Zero High/Critical CVEs
- Zero hardcoded secrets
- All dependencies patched

---

## Stage 7: Chaos Tests

**Duration**: ~3 minutes (optional for hotfixes)
**Block on**: Unrecoverable failure
**Tools**: pytest, toxiproxy

```bash
# Chaos scenarios
pytest tests/chaos/ \
  --tb=short \
  -k "provider_outage or db_latency or cache_eviction"

# Scenarios tested
# - Provider timeout (circuit breaker engages)
# - Database failover (< 5s downtime)
# - Redis eviction (cache miss → DB fallback)
# - Pack build during market hours (stale pack served)
```

**Exit Criteria**: System degrades gracefully, no data corruption

---

## Stage 8: Build Images

**Duration**: ~4 minutes
**Block on**: Build failure
**Tools**: Docker BuildKit, multi-stage builds

```bash
# Backend image
docker build \
  --build-arg GIT_SHA=${GIT_SHA} \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --tag dawsos-backend:${GIT_SHA} \
  --tag dawsos-backend:latest \
  --file backend/Dockerfile \
  backend/

# Worker image (nightly jobs)
docker build \
  --tag dawsos-worker:${GIT_SHA} \
  --file backend/Dockerfile.worker \
  backend/

# Frontend image (if applicable)
docker build \
  --tag dawsos-frontend:${GIT_SHA} \
  --file frontend/Dockerfile \
  frontend/
```

**Artifacts**:
- `dawsos-backend:${GIT_SHA}`
- `dawsos-worker:${GIT_SHA}`
- `dawsos-frontend:${GIT_SHA}`

**Exit Criteria**: All images build successfully, < 500MB uncompressed

---

## Stage 9: SBOM & SCA

**Duration**: ~2 minutes
**Block on**: License violation
**Tools**: syft, grype, ort

```bash
# Generate SBOM
syft dawsos-backend:${GIT_SHA} -o spdx-json > sbom.json

# License compliance
ort analyze -i sbom.json -o ort-results.json
# Block on: GPL, AGPL, SSPL (copyleft)
# Allow: MIT, Apache-2.0, BSD-3-Clause

# Vulnerability scan
grype sbom:./sbom.json --fail-on high
```

**Artifacts**: `sbom.json`, `ort-results.json`

**Exit Criteria**:
- No copyleft licenses
- No High/Critical vulns in production dependencies

---

## Stage 10: Deploy Staging

**Duration**: ~3 minutes
**Block on**: Deployment failure, health check timeout
**Tools**: Kubernetes, Helm

```bash
# Deploy to staging namespace
helm upgrade --install dawsos-staging ./charts/dawsos \
  --namespace=staging \
  --set image.tag=${GIT_SHA} \
  --set environment=staging \
  --set replicas=2 \
  --wait --timeout=3m

# Health check
kubectl rollout status deployment/dawsos-backend -n staging
curl https://staging.dawsos.internal/health | jq -e '.status == "healthy"'
```

**Environment**:
- Database: staging RDS (anonymized prod snapshot)
- Providers: Real APIs with test accounts
- Monitoring: Full OTel → staging Prometheus

**Exit Criteria**:
- All pods healthy (2/2 ready)
- `/health` returns 200
- No crash loops

---

## Stage 11: UAT Suites

**Duration**: ~5 minutes
**Block on**: Critical UAT failure (see UAT_CHECKLIST.md)
**Tools**: pytest, playwright (E2E)

```bash
# Smoke tests (critical flows)
pytest tests/uat/ \
  --base-url=https://staging.dawsos.internal \
  -m "smoke" \
  --tb=short

# Full UAT suite
pytest tests/uat/ \
  --base-url=https://staging.dawsos.internal \
  --html=uat-report.html

# E2E tests (if UI exists)
playwright test \
  --config=playwright.config.ts \
  --reporter=html
```

**UAT Coverage** (see UAT_CHECKLIST.md for full list):
- [ ] Pack build completes in staging
- [ ] Ledger reconciliation passes (±1bp)
- [ ] Multi-currency valuation correct
- [ ] Alert delivery works (email/webhook)
- [ ] RLS policies enforce user isolation

**Exit Criteria**: All smoke tests pass, < 5% failure rate on full suite

**Approval Gate**: Product owner must approve UAT report before proceeding to canary

---

## Stage 12: Canary Production

**Duration**: 30 minutes (5% → 25% → 100%)
**Auto-rollback on**: p95 latency > SLO, error rate > 0.5%, pricing pack failure
**Tools**: Kubernetes, Flagger, Prometheus

### Canary Rollout Strategy

```yaml
# flagger-canary.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: dawsos-backend
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dawsos-backend
  service:
    port: 8000
  analysis:
    interval: 1m
    threshold: 5  # rollback after 5 failed checks
    maxWeight: 100
    stepWeight: 20  # 5% → 25% → 45% → 65% → 85% → 100%
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99.5  # < 0.5% error rate
        interval: 1m
      - name: request-duration-p95
        thresholdRange:
          max: 1200  # ≤ 1.2s (warm SLO)
        interval: 1m
      - name: pricing-pack-health
        query: |
          sum(rate(pricing_pack_build_failures_total[1m])) == 0
        thresholdRange:
          max: 0
        interval: 5m
```

### Deployment Steps

#### Step 1: Initial Deployment (5% traffic)
```bash
# Deploy canary
helm upgrade dawsos-prod ./charts/dawsos \
  --namespace=production \
  --set image.tag=${GIT_SHA} \
  --set canary.enabled=true \
  --reuse-values

# Flagger automatically creates canary deployment
# Traffic: 95% stable, 5% canary
```

**Duration**: 5 minutes
**Monitoring**:
```promql
# Error rate
sum(rate(http_requests_total{status=~"5..", deployment="dawsos-backend-canary"}[1m]))
/ sum(rate(http_requests_total{deployment="dawsos-backend-canary"}[1m]))

# p95 latency
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{deployment="dawsos-backend-canary"}[1m])
)
```

**Go/No-Go**: If error rate < 0.5% AND p95 < 1.2s → proceed to 25%

---

#### Step 2: Increase to 25% traffic
**Duration**: 10 minutes
**Monitoring**: Same metrics, larger sample size

**Go/No-Go**: If SLOs hold for 10 minutes → proceed to 45%

---

#### Step 3: Ramp to 100%
**Steps**: 45% → 65% → 85% → 100% (5 minutes each)
**Total Duration**: 15 minutes

**Final Check**: All pods healthy, pricing pack builds successfully

---

### Automatic Rollback

Flagger triggers rollback if:
1. **Error rate > 0.5%** for 5 consecutive minutes
2. **p95 latency > 1.2s** for 5 consecutive minutes
3. **Pricing pack build fails** during canary window
4. **Pod crash loop** (3 restarts in 5 minutes)

```bash
# Rollback happens automatically
# Flagger scales canary to 0, routes 100% traffic to stable

# Check rollback status
kubectl describe canary dawsos-backend -n production | grep "Status:"
# Status: Failed (rolled back due to: request-duration-p95 > 1200ms)
```

**Rollback Time**: < 60 seconds (traffic shift only, no pod replacement)

---

### Manual Rollback

If needed outside of Flagger automation:
```bash
# Immediate rollback
kubectl set image deployment/dawsos-backend-primary \
  backend=dawsos-backend:${PREVIOUS_GOOD_SHA} \
  -n production

# Or via Helm
helm rollback dawsos-prod -n production
```

---

## Post-Deployment Verification

After 100% canary promotion:

### 1. Smoke Test Production
```bash
curl https://api.dawsos.com/health | jq
# Expected: {"status": "healthy", "version": "${GIT_SHA}"}

# Verify pricing pack
curl -H "Authorization: Bearer ${TEST_TOKEN}" \
  https://api.dawsos.com/v1/pricing/latest | jq '.pricing_pack_id'
```

### 2. Monitor Nightly Jobs
```bash
# Check next pricing pack build (runs at 00:00 local)
kubectl logs -f job/pricing-pack-build-$(date +%Y%m%d) -n production

# Verify sacred job order
# 1. build_pack
# 2. reconcile_ledger
# 3. compute_metrics
# 4. prewarm_factors
# 5. mark_pack_fresh
# 6. evaluate_alerts
```

### 3. Verify Observability
```bash
# Check traces in Jaeger
# https://jaeger.dawsos.internal/search?service=dawsos-backend

# Check metrics in Grafana
# https://grafana.dawsos.internal/d/dawsos-overview

# Check alerts
curl https://alertmanager.dawsos.internal/api/v2/alerts | jq
```

---

## Rollback Runbook (Manual)

If automated rollback fails or manual intervention needed:

### 1. Identify Last Good Version
```bash
# List recent deployments
helm history dawsos-prod -n production

# Or from Git
git log --oneline --graph --decorate -10
```

### 2. Execute Rollback
```bash
# Via Helm (recommended)
helm rollback dawsos-prod <REVISION> -n production --wait

# Or via kubectl
kubectl set image deployment/dawsos-backend \
  backend=dawsos-backend:<LAST_GOOD_SHA> \
  -n production

kubectl rollout status deployment/dawsos-backend -n production
```

### 3. Verify Health
```bash
# Check all pods
kubectl get pods -n production -l app=dawsos-backend

# Check health endpoint
for i in {1..10}; do
  curl -s https://api.dawsos.com/health | jq -r '.status'
  sleep 2
done
```

### 4. Post-Incident
- Tag rollback commit: `git tag rollback-$(date +%Y%m%d-%H%M) <LAST_GOOD_SHA>`
- Update incident channel with root cause
- Schedule post-mortem (within 48 hours)
- Update RUNBOOKS.md if new failure mode discovered

---

## SLO Alignment

This pipeline enforces the following SLOs:

| SLO | Verification Stage | Threshold |
|-----|-------------------|-----------|
| Warm p95 ≤ 1.2s | Stage 12 (Canary) | Auto-rollback if breached |
| Cold p95 ≤ 2.0s | Stage 11 (UAT) | Measured in staging |
| Pack build by 00:15 | Stage 11 (UAT) | Simulated nightly job |
| Alert median ≤ 60s | Stage 5 (Integration) | End-to-end alert delivery |
| RLS isolation | Stage 3 (Property) | Cross-portfolio leak tests |
| ±1bp reconciliation | Stage 5 (Integration) | Ledger vs DB diff |

---

## Pipeline Configuration (GitHub Actions Example)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

env:
  GIT_SHA: ${{ github.sha }}

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      # Stage 1: Lint & Type Check
      - name: Lint Backend
        run: |
          pip install ruff mypy
          ruff check backend/
          mypy backend/ --strict

      # Stage 2: Unit Tests
      - name: Unit Tests
        run: |
          pip install -r backend/requirements-dev.txt
          pytest tests/unit/ --cov=app --cov-fail-under=95

      # Stage 3: Property Tests
      - name: Property Tests
        run: pytest tests/property/ --hypothesis-profile=ci

      # Stage 4: Golden Tests
      - name: Golden Tests
        run: pytest tests/golden/ --golden-update=never

      # Stage 5: Integration Tests
      - name: Integration Tests
        run: |
          docker-compose -f docker-compose.test.yml up -d
          pytest tests/integration/
          docker-compose -f docker-compose.test.yml down -v

      # Stage 6: Security Tests
      - name: Security Scan
        run: |
          pip install bandit safety
          bandit -r backend/ -ll
          safety check

      # Stage 7: Chaos Tests
      - name: Chaos Tests
        run: pytest tests/chaos/ -k "provider_outage or db_latency"

  build-artifacts:
    needs: quality-gates
    runs-on: ubuntu-latest
    steps:
      # Stage 8: Build Images
      - name: Build Docker Images
        run: |
          docker build -t dawsos-backend:${{ env.GIT_SHA }} backend/
          docker build -t dawsos-worker:${{ env.GIT_SHA }} -f backend/Dockerfile.worker backend/

      # Stage 9: SBOM & SCA
      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          image: dawsos-backend:${{ env.GIT_SHA }}
          format: spdx-json
          output-file: sbom.json

      - name: Push Images
        run: |
          docker tag dawsos-backend:${{ env.GIT_SHA }} gcr.io/dawsos/backend:${{ env.GIT_SHA }}
          docker push gcr.io/dawsos/backend:${{ env.GIT_SHA }}

  deploy-staging:
    needs: build-artifacts
    runs-on: ubuntu-latest
    steps:
      # Stage 10: Deploy Staging
      - name: Deploy to Staging
        run: |
          helm upgrade --install dawsos-staging ./charts/dawsos \
            --namespace=staging \
            --set image.tag=${{ env.GIT_SHA }} \
            --wait --timeout=3m

      # Stage 11: UAT Suites
      - name: Run UAT
        run: |
          pytest tests/uat/ --base-url=https://staging.dawsos.internal -m smoke

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://api.dawsos.com
    steps:
      # Stage 12: Canary Production
      - name: Deploy Canary
        run: |
          helm upgrade dawsos-prod ./charts/dawsos \
            --namespace=production \
            --set image.tag=${{ env.GIT_SHA }} \
            --set canary.enabled=true \
            --reuse-values

      - name: Monitor Canary
        run: |
          # Flagger handles progressive rollout
          # Wait for completion or rollback
          kubectl wait --for=condition=Promoted \
            canary/dawsos-backend -n production \
            --timeout=30m
```

---

## Related Documents

- **[RUNBOOKS.md](./RUNBOOKS.md)** - Incident response procedures
- **[UAT_CHECKLIST.md](./UAT_CHECKLIST.md)** - User acceptance criteria
- **[PRODUCT_SPEC.md](../.claude/PRODUCT_SPEC.md)** - Application requirements
- **[BUILD_SYSTEM_V2_UPDATES.md](../BUILD_SYSTEM_V2_UPDATES.md)** - v2.0 tracking

---

## Monitoring & Alerts

### Pipeline Metrics (Prometheus)
```promql
# Pipeline success rate
sum(rate(ci_pipeline_runs_total{result="success"}[1h]))
/ sum(rate(ci_pipeline_runs_total[1h]))

# Pipeline duration (target: < 25 minutes)
histogram_quantile(0.95, rate(ci_pipeline_duration_seconds_bucket[1h]))

# Canary rollback rate (should be < 5%)
sum(rate(canary_rollbacks_total[1d]))
/ sum(rate(canary_deployments_total[1d]))
```

### Alerts
```yaml
# alerts.yml
groups:
  - name: CI/CD
    rules:
      - alert: PipelineFailureRate
        expr: |
          sum(rate(ci_pipeline_runs_total{result="failure"}[1h]))
          / sum(rate(ci_pipeline_runs_total[1h])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CI/CD pipeline failure rate > 10%"

      - alert: CanaryRollback
        expr: increase(canary_rollbacks_total[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Canary deployment rolled back"
          description: "Check Flagger events and Prometheus alerts"
```

---

**Last Updated**: 2025-10-21
**Owner**: Platform Team
**Review Cycle**: Quarterly (or after each incident)
