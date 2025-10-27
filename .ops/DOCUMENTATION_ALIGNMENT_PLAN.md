# Documentation Alignment Plan - Truth-First Philosophy

**Status**: DRAFT - Comprehensive Audit Complete
**Created**: 2025-10-26
**Purpose**: Align all documentation with actual codebase state, eliminate aspirational claims

---

## Executive Summary

### The Problem: Documentation Drift

DawsOS claims a "truth-first philosophy" but suffers from **systematic documentation drift** where specs, READMEs, and architect docs describe features as "operational" or "current" that are actually stubs, placeholders, or completely unimplemented.

### Impact

- **Trust Erosion**: Contributors discover advertised features don't work
- **Wasted Effort**: Developers troubleshoot "working" features that are stubs
- **Governance Failure**: No audit trail of what was delivered vs. deferred
- **Product Confusion**: Users expect capabilities that don't exist

### Scope of Drift

**Comprehensive Audit Results**:
- **5 major documentation categories** with drift
- **12+ specific misrepresentations** identified
- **6 of 12 patterns** affected by unimplemented dependencies
- **3 critical anti-patterns** (duplicate logic, misleading logs, opt-in observability)

---

## Part 1: Verified Documentation Drift Issues

### Issue 1: Macro Scenarios/DaR Advertised as Current

**Files Making Claims**:
1. **PRODUCT_SPEC.md:231** - Lists `risk.compute_dar` and `macro.scenario_apply` in capability list (no "planned" qualifier)
2. **PRODUCT_SPEC.md:43** - Claims "macro_hound → scenarios, DaR" as delivered
3. **PRODUCT_SPEC.md:222-223** - Describes `portfolio_macro_overview` and `portfolio_scenario_analysis` patterns as operational
4. **README.md:36** - Lists "Macro scenarios & Drawdown-at-Risk" as a feature

**Actual Code State**:
- [backend/app/agents/macro_hound.py:419](backend/app/agents/macro_hound.py#L419): `return {"error": "Scenario service not yet implemented"}`
- [backend/app/agents/macro_hound.py:490](backend/app/agents/macro_hound.py#L490): `return {"error": "DaR service not yet implemented"}`
- ✅ Service exists: backend/app/services/scenarios.py (538 LOC)
- ❌ Agent doesn't call service (returns error stubs instead)

**Impact**:
- Patterns `portfolio_scenario_analysis`, `portfolio_cycle_risk`, `portfolio_macro_overview` fail with errors
- Users attempting stress testing get "not yet implemented" messages
- Docs claim this is a "core differentiator" but it doesn't work

**Remediation**:
- README: Move to "In Progress" section (already contradictory - line 59 says "Implement macro scenarios/DaR")
- PRODUCT_SPEC: Add `(PENDING - P1)` qualifier to lines 43, 222-223, 231
- Implement wire-up per P1-1 and P1-2 in remediation plan (28 hours)

---

### Issue 2: Ratings Advertised as Complete, But Incomplete

**Files Making Claims**:
1. **README.md**: Doesn't mention ratings limitations
2. **PRODUCT_SPEC.md:231** - Lists `ratings.dividend_safety|moat_strength|resilience` without qualification
3. **.claude/agents/business/RATINGS_ARCHITECT.md:6** - Says "Status: ❌ NOT IMPLEMENTED" (outdated - agent exists now)

**Actual Code State**:
- ✅ Ratings agent exists: backend/app/agents/ratings_agent.py (397 LOC)
- ✅ Ratings service exists: backend/app/services/ratings.py (500+ LOC)
- ❌ Hardcoded 25% weights (not rubric-driven per spec)
- ❌ Fundamentals loading returns stubs even after FMP fetch
- ❌ Governance doc still says "PRE-IMPLEMENTATION REVIEW"

**Documentation Lies**:
1. **backend/app/agents/data_harvester.py:613** - Logs "Successfully fetched real fundamentals" but line 618 returns stubs anyway
2. **Metadata claims** `source: "fundamentals:fmp:AAPL"` but data is actually stub
3. **No WARNING** in user-facing docs that ratings are inaccurate due to hardcoded weights

**Impact**:
- `buffett_checklist` pattern produces identical ratings for all securities (stub data)
- Users trust ratings that are fundamentally inaccurate (equal weight assumption)
- FMP API calls wasted (fetches data but doesn't use it)

**Remediation**:
- README: Add "⚠️ Ratings use hardcoded weights (Phase 1 limitation)"
- RATINGS_ARCHITECT.md: Update status to "✅ IMPLEMENTED (Phase 1 - with limitations)"
- Update `.ops/RATINGS_IMPLEMENTATION_GOVERNANCE.md` from "PRE-IMPLEMENTATION REVIEW" to "PHASE 1 APPROVED (with documented deviations)"
- Fix fundamentals logging to be honest: `logger.warning("FMP data fetched but transformation not implemented, using stubs")`

---

### Issue 3: Optimizer & Exports Advertised as Operational

**Files Making Claims**:
1. **PRODUCT_SPEC.md:600-660** - Describes optimizer-driven rebalancing as delivered
2. **.claude/agents/ORCHESTRATOR.md:60-128** - Lists optimizer/exports as "operational"
3. **README.md:38** - Lists "Rights-enforced PDF exports & alerts pipeline" as a feature

**Actual Code State**:
- ❌ No optimizer service exists (backend/app/services/optimizer.py has stubs)
- ❌ Pattern `policy_rebalance.json` depends on non-existent `optimizer.propose_trades` capability
- ❌ backend/app/services/reports.py is placeholder (outputs text/CSV strings, not PDFs)
- ❌ WeasyPrint integration doesn't exist
- ❌ Rights registry enforcement not implemented

**Impact**:
- `policy_rebalance` pattern fails (capability not registered)
- `export_portfolio_report` pattern returns CSV text, not PDF
- No rights checking happens (advertised as security feature)

**Remediation**:
- README: Move optimizer/exports to "In Progress" section
- PRODUCT_SPEC: Add `(PLANNED - Sprint 4)` qualifier
- ORCHESTRATOR.md: Update status to list missing components
- Implement per P1-3 (optimizer, 40 hours) and reports remediation

---

### Issue 4: Observability Claims vs. Reality

**Files Making Claims**:
1. **PRODUCT_SPEC.md:40-95** - Claims OpenTelemetry, Prometheus, Sentry, `/health/pack` endpoint are "enabled"
2. **PRODUCT_SPEC.md:386-420** - Describes observability as operational with SLO enforcement

**Actual Code State**:
- ✅ Scaffolding exists: backend/observability/ directory
- ❌ All features gated behind `ENABLE_OBSERVABILITY` env var
- ❌ No documentation explaining how to enable
- ❌ `/health/pack` endpoint doesn't exist (only `/health`)
- ❌ Most deployments won't see promised telemetry

**Impact**:
- Default deployment has NO observability (opt-in, undocumented)
- Product guarantees (trace attributes, metrics, SLOs) aren't met by default
- Users expecting monitoring/alerts get nothing

**Remediation**:
- PRODUCT_SPEC: Add "Observability is opt-in via ENABLE_OBSERVABILITY env var"
- Create `.env.example` with observability vars documented
- Implement `/health/pack` endpoint showing pricing pack status
- Update README with observability setup instructions

---

### Issue 5: ORCHESTRATOR.md Outdated Status

**File**: `.claude/agents/ORCHESTRATOR.md`

**Claims**:
- Only Ratings/Optimizer agents missing
- All 12 patterns operational

**Reality**:
- ✅ Ratings agent now exists (status update needed)
- ❌ Key patterns still fail: policy_rebalance, portfolio_scenario_analysis, export_portfolio_report
- ❌ Patterns depend on unimplemented services (scenarios, DaR, optimizer, reports)

**Remediation**:
- Update ORCHESTRATOR.md with current agent status
- List which patterns work vs. which fail with specific errors
- Reference TASK_INVENTORY as canonical backlog

---

## Part 2: Tooling & Script Issues

### Issue 6: test_integration.sh Container Name Assumptions

**Problem**: Script hardcodes `dawsos-postgres` container name

**Files Affected**:
- test_integration.sh:254-432 - Multiple `docker exec dawsos-postgres` commands

**Impact**:
- Developers using "simple" stack (dawsos-dev-postgres) get errors
- README documents simple stack as supported but integration tests fail

**Fix** (4 hours):
```bash
# Detect container name dynamically
POSTGRES_CONTAINER=$(docker ps --filter "name=postgres" --format "{{.Names}}" | head -1)

if [ -z "$POSTGRES_CONTAINER" ]; then
    echo "❌ No PostgreSQL container found"
    exit 1
fi

echo "✅ Using PostgreSQL container: $POSTGRES_CONTAINER"

# Use variable in all docker exec commands
docker exec "$POSTGRES_CONTAINER" psql -U dawsos_app ...
```

**Apply to**: test_integration.sh, backend/run_integration_tests.sh, any other scripts

---

### Issue 7: Legacy Entrypoint Documentation

**Problem**: Comments/docs reference old entrypoints

**Examples**:
- `streamlit run frontend/ui/screens/portfolio_overview.py` (wrong - use `frontend/main.py`)
- `uvicorn backend.app.main:app` (wrong - use `backend.app.api.executor:app`)

**Impact**: Contributors troubleshooting issues follow wrong instructions

**Fix** (2 hours):
```bash
# Find all references
grep -r "streamlit run.*portfolio_overview" . --include="*.md" --include="*.py"
grep -r "backend\.app\.main" . --include="*.md" --include="*.py"

# Update to correct entrypoints
# Frontend: python frontend/main.py OR ./frontend/run_ui.sh
# Backend: ./backend/run_api.sh OR python -m uvicorn app.api.executor:app
```

---

## Part 3: Anti-Patterns Requiring Fixes

### Anti-Pattern 1: Ratings Agent Duplicates Service Logic

**Problem**: Agent has scoring helper methods duplicating service logic

**Location**: (User claim - needs verification, file only has 397 lines total)

**If Confirmed**:
- Violates "single source of truth" guardrail
- Changing thresholds requires edits in two files
- Risk of drift between agent and service

**Fix** (6 hours):
- Move ALL scoring logic to service
- Agent only calls service + attaches metadata
- Verify with code review (may already be fixed)

---

### Anti-Pattern 2: Misleading Fundamentals Logging

**Problem**: Logs success but returns stubs

**Location**: [backend/app/agents/data_harvester.py:613-618](backend/app/agents/data_harvester.py#L613-L618)

**Code**:
```python
logger.info(f"Successfully fetched real fundamentals for {symbol}")
# ...
result = self._stub_fundamentals_for_symbol(symbol)  # Returns stubs!
```

**Impact**:
- Misleading metadata (`source: "fmp:AAPL"` but data is stub)
- Developers trust logs and don't realize data is fake
- Wasted provider API calls

**Fix** (1 hour):
```python
# Be honest in logs
if real_data_available:
    logger.info(f"FMP data fetched but transformation not implemented for {symbol}")
    logger.warning(f"Falling back to stub fundamentals for {symbol}")
    result = self._stub_fundamentals_for_symbol(symbol)
    source = "fundamentals:stub"  # HONEST metadata
else:
    result = self._stub_fundamentals_for_symbol(symbol)
    source = "fundamentals:stub"
```

---

### Anti-Pattern 3: Observability Opt-In Without Documentation

**Problem**: Critical observability features gated behind undocumented env var

**Impact**:
- Default deployment has NO tracing, metrics, error tracking
- Violates product spec promises
- Users don't know how to enable

**Fix** (4 hours):
1. Create `.env.observability.example` with all vars documented
2. Update README with observability setup section
3. Make `/health` endpoint show observability status
4. Consider making basic observability on-by-default (traces/metrics)

---

## Part 4: Master Documentation Alignment Tasks

### Immediate Actions (P0 - This Week)

#### Task 1: Create Honest Feature Matrix (4 hours)
**File**: Create `.ops/FEATURE_STATUS_MATRIX.md`

| Feature | Advertised | Actual Status | Patterns Affected | Remediation Plan |
|---------|-----------|---------------|-------------------|------------------|
| Macro Scenarios | "Operational" | Stub (returns error) | portfolio_scenario_analysis | P1-1 (12h) |
| DaR | "Operational" | Stub (returns error) | portfolio_cycle_risk | P1-2 (16h) |
| Ratings | "Complete" | Partial (hardcoded weights, stub fundamentals) | buffett_checklist | P0-1,P0-2 (34h) |
| Optimizer | "Operational" | Not implemented | policy_rebalance | P1-3 (40h) |
| PDF Exports | "Operational" | Placeholder (CSV only) | export_portfolio_report | P2-3 (20h) |
| Observability | "Enabled" | Opt-in, undocumented | All patterns | P2-4 (4h) |
| Rights Enforcement | "Enforced" | Not implemented | export patterns | P2-5 (16h) |
| Alerts DLQ/Dedupe | "Operational" | On backlog | alert patterns | P3 (TBD) |

**Reference this matrix** in README, PRODUCT_SPEC, CLAUDE.md

#### Task 2: Update README.md (2 hours)
**Changes**:
```markdown
## Features

### ✅ Operational (Production-Ready)
- Portfolio ledger with Beancount reconciliation
- Pricing pack immutability & reproducibility
- Multi-currency attribution
- Macro regime detection (5 regimes)
- Dalio cycle framework (STDC, LTDC, Empire)
- Pattern-based execution (12 patterns defined, 6 fully operational)

### ⚠️ Partial (Phase 1 - Known Limitations)
- **Ratings** (buffett_checklist pattern)
  - ✅ Agent and service implemented
  - ❌ Uses hardcoded 25% weights (not rubric-driven)
  - ❌ Returns stub fundamentals (FMP transformation pending)
  - Impact: Ratings inaccurate, all securities get similar scores
  - Remediation: P0-1, P0-2 (34 hours)

### 🚧 In Progress (P1 - Sprint 3-4)
- Macro scenarios & Drawdown-at-Risk (MacroHound)
- Optimizer-driven rebalancing (RiskfolioLib integration)
- Rights-enforced PDF exports & alerts pipeline
- Nightly job orchestration
- Full observability (OpenTelemetry, Prometheus, Sentry)

### 📋 Planned (P2-P3)
- News impact analysis
- Corporate actions support
- Advanced scenario modeling
- Performance optimization (p95 < 1.2s target)
```

#### Task 3: Update PRODUCT_SPEC.md (6 hours)
**Changes**:
1. Line 43: `├─ macro_hound → FRED/FX, regime, factors, scenarios (P1), DaR (P1)`
2. Line 231: Add status qualifiers to capability list:
   ```
   `risk.compute_dar (P1)`, `macro.scenario_apply (P1)`,
   `ratings.* (PARTIAL - hardcoded weights)`,
   `optimizer.propose_trades (P1)`,
   `reports.render_pdf (P2 - CSV only)`
   ```
3. Section 7 (Macro): Add "⚠️ Scenario/DaR currently return errors - see P1-1, P1-2"
4. Section 10 (Ratings): Add "⚠️ Phase 1 uses hardcoded weights - see P0-1"
5. New Section: "Feature Status Matrix" (reference .ops/FEATURE_STATUS_MATRIX.md)

#### Task 4: Update Agent Architect Docs (8 hours)
**Files to Update**:
1. **.claude/agents/business/RATINGS_ARCHITECT.md**
   - Line 6: Change status to "✅ IMPLEMENTED (Phase 1 - with limitations)"
   - Add section: "Known Limitations (Phase 1)"
   - Link to governance doc and remediation plan

2. **.claude/agents/analytics/MACRO_ARCHITECT.md**
   - Update status to show scenario/DaR pending
   - Link to P1-1, P1-2 remediation tasks

3. **.claude/agents/ORCHESTRATOR.md**
   - Update agent registry status
   - List working patterns vs. failing patterns
   - Reference .ops/FEATURE_STATUS_MATRIX.md

#### Task 5: Restore and Update Governance Docs (4 hours)
**File**: `.ops/RATINGS_IMPLEMENTATION_GOVERNANCE.md`

**Actions**:
1. Restore from git commit 0721468 (if deleted during cleanup)
2. Update status from "PRE-IMPLEMENTATION REVIEW" to "PHASE 1 APPROVED"
3. Document approved deviations:
   - Hardcoded 25% weights (moat, resilience)
   - Stub fundamentals transformation
   - Phase 2 remediation timeline
4. Add sign-off section:
   ```markdown
   ## Phase 1 Approval

   **Status**: APPROVED FOR LIMITED PRODUCTION USE
   **Date**: 2025-10-26
   **Approved By**: [Product Owner Name]

   ### Known Deviations
   1. Hardcoded rating weights (remediation: P0-1, 20 hours)
   2. Stub fundamentals (remediation: P0-2, 14 hours)

   ### Acceptance for Phase 1
   - Ratings produce stable scores (even if inaccurate)
   - Pattern execution doesn't error
   - Metadata clearly indicates Phase 1 status

   ### Phase 2 Requirements
   - Rubric-driven weights from database
   - Real FMP fundamentals transformation
   - Different ratings for different securities
   - Target: 2 weeks from approval
   ```

---

### High Priority (P1 - Week 1-2)

#### Task 6: Fix Integration Script Container Names (4 hours)
**Files**: test_integration.sh, backend/run_integration_tests.sh

**Changes**:
```bash
# Add container detection at top of script
detect_postgres_container() {
    local container=$(docker ps --filter "name=postgres" --format "{{.Names}}" | head -1)
    if [ -z "$container" ]; then
        echo "❌ ERROR: No PostgreSQL container found" >&2
        echo "   Expected: dawsos-postgres OR dawsos-dev-postgres" >&2
        echo "   Running: $(docker ps --format '{{.Names}}' | tr '\n' ' ')" >&2
        exit 1
    fi
    echo "$container"
}

POSTGRES_CONTAINER=$(detect_postgres_container)
echo "✅ Using PostgreSQL container: $POSTGRES_CONTAINER"

# Replace all hardcoded references
# OLD: docker exec dawsos-postgres psql ...
# NEW: docker exec "$POSTGRES_CONTAINER" psql ...
```

**Test**:
```bash
# Test with full stack
docker compose up -d
./test_integration.sh

# Test with simple stack
docker compose -f docker-compose.simple.yml up -d
./test_integration.sh
```

#### Task 7: Fix Misleading Logs and Metadata (2 hours)
**File**: backend/app/agents/data_harvester.py

**Changes**:
```python
# Lines 611-621 - Be honest about stub data
if fundamentals_data.get("_real_data", False) and ratios_data.get("_real_data", False):
    # Transformation not implemented yet - use stubs
    logger.warning(f"FMP data fetched for {symbol} but transformation not implemented")
    logger.info(f"Falling back to stub fundamentals for {symbol}")
    result = self._stub_fundamentals_for_symbol(symbol)
    source = "fundamentals:stub"  # HONEST
    result["_attempted_real_fetch"] = True  # Flag for debugging
else:
    logger.info(f"Provider returned stub data for {symbol}, using fallback stubs")
    result = self._stub_fundamentals_for_symbol(symbol)
    source = "fundamentals:stub"
```

#### Task 8: Add Observability Documentation (4 hours)
**Files**:
1. Create `.env.observability.example`
2. Update README.md with observability section
3. Enhance `/health` endpoint to show observability status

**Example .env.observability.example**:
```bash
# Observability Configuration (Optional - Default: Disabled)

# Enable all observability features
ENABLE_OBSERVABILITY=true

# OpenTelemetry Tracing
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=dawsos-api
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1  # Sample 10% of traces

# Prometheus Metrics
PROMETHEUS_PORT=9090
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus

# Sentry Error Tracking
SENTRY_DSN=https://your-key@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # or 'text' for development
```

**README.md section**:
```markdown
## Observability Setup (Optional)

DawsOS supports OpenTelemetry tracing, Prometheus metrics, and Sentry error tracking.
These are **opt-in** and disabled by default.

### Quick Start
```bash
# Copy example config
cp .env.observability.example .env.observability

# Edit with your endpoints
nano .env.observability

# Enable observability
export ENABLE_OBSERVABILITY=true

# Start with observability
./backend/run_api.sh
```

### Verify Observability Status
```bash
curl http://localhost:8000/health

# Response includes observability status:
{
  "status": "healthy",
  "observability": {
    "tracing": true,
    "metrics": true,
    "error_tracking": true
  }
}
```
```

---

### Medium Priority (P2 - Week 3-4)

#### Task 9: Create Documentation Review Checklist (2 hours)
**File**: `.ops/DOCUMENTATION_REVIEW_CHECKLIST.md`

**Checklist for any new feature**:
- [ ] README.md updated with correct status (Operational / Partial / In Progress / Planned)
- [ ] PRODUCT_SPEC.md includes (STATUS) qualifier in capability lists
- [ ] Agent architect doc updated with implementation status
- [ ] FEATURE_STATUS_MATRIX.md updated with actual state
- [ ] If stubs/placeholders used, metadata accurately reflects this
- [ ] If claiming "operational", pattern execution tested end-to-end
- [ ] Governance doc created and approved (for Phase 1 deviations)
- [ ] Integration tests verify claimed functionality
- [ ] README examples work with actual codebase
- [ ] No logs claim success when returning stubs

#### Task 10: Audit Remaining Documentation (8 hours)
**Systematic review**:
1. All .md files in root directory
2. All .md files in .claude/agents/
3. All .md files in .ops/
4. All pattern JSON descriptions
5. All code comments claiming "operational" features

**For each file**:
- [ ] Verify claims against actual code
- [ ] Add status qualifiers where needed
- [ ] Remove aspirational language
- [ ] Link to remediation plan for pending features

---

## Part 5: Integration with Existing Plans

### Link to Shortcut Remediation Plan

This documentation alignment plan **complements** the [SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md](SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md):

**Remediation Plan** focuses on: **FIXING THE CODE**
- Implementing missing features (scenarios, DaR, optimizer)
- Fixing shortcuts (hardcoded weights, stub fundamentals)
- Removing anti-patterns
- Effort: 245 hours over 10 weeks

**Documentation Alignment Plan** focuses on: **FIXING THE DOCS**
- Making documentation match code reality
- Removing false advertising
- Creating honest feature matrix
- Establishing review process
- Effort: 50 hours over 4 weeks

### Combined Timeline

**Week 1** (Parallel):
- Remediation P0: Fix ratings weights + fundamentals (37h code)
- Alignment P0: Update README, PRODUCT_SPEC, restore governance docs (24h docs)
- **Result**: Code and docs both admit Phase 1 limitations

**Week 2** (Parallel):
- Remediation P0: Integration testing of fixes
- Alignment P1: Fix tooling scripts, misleading logs (10h)
- **Result**: Phase 1 approved with documented limitations

**Week 3-4** (Parallel):
- Remediation P1: Implement scenarios, DaR, optimizer (68h code)
- Alignment P2: Observability docs, remaining audits (14h docs)
- **Result**: Features fully operational, docs updated

**Week 5-6** (Sequential):
- Remediation P2: Polish and performance
- Alignment: Final audit and sign-off
- **Result**: Production-ready code + accurate documentation

---

## Part 6: Success Criteria

### Documentation Alignment Complete When:

**Accuracy**:
- [ ] Zero false claims (all "operational" features actually work)
- [ ] Zero misleading logs (stubs logged as stubs)
- [ ] Zero hidden limitations (all Phase 1 deviations documented)

**Traceability**:
- [ ] FEATURE_STATUS_MATRIX.md is single source of truth
- [ ] All docs reference matrix for current state
- [ ] Governance docs record all approved deviations
- [ ] Remediation plan linked from all "In Progress" claims

**User Trust**:
- [ ] README clearly distinguishes delivered vs. pending
- [ ] Pattern failures explained with remediation timeline
- [ ] Setup instructions match actual entrypoints
- [ ] Integration tests pass for advertised features

**Process**:
- [ ] Documentation review checklist used for all PRs
- [ ] Weekly audit of docs vs. code (automated script)
- [ ] Governance sign-off required for Phase 1 approvals
- [ ] No merge without doc update

---

## Part 7: Effort Summary

| Priority | Tasks | Effort (hours) | Duration (weeks) |
|----------|-------|----------------|------------------|
| **P0** | 5 | 24 | 1 |
| **P1** | 3 | 10 | 1 |
| **P2** | 2 | 14 | 2 |
| **P3** | Ongoing audits | 2/week | Continuous |
| **Total** | 10 | 50 | 4 |

**Combined with Code Remediation**:
- Code fixes: 245 hours
- Doc alignment: 50 hours
- **Total**: 295 hours (37 person-days)

---

## Part 8: Recommendations (from User Feedback)

### ✅ Implemented in This Plan

1. **"Align docs with reality"** → Task 1-5 (Feature matrix, README, PRODUCT_SPEC, architect docs)
2. **"Fix integration tooling"** → Task 6 (Container name detection)
3. **"Clearly defer stubs"** → Task 2 (README Partial/In Progress sections)
4. **"Update governance artifacts"** → Task 5 (RATINGS_IMPLEMENTATION_GOVERNANCE.md)
5. **"Reduce duplication"** → Anti-Pattern 1 (covered in remediation plan)

### Additional Actions Required

6. **Weekly Documentation Audits** (Continuous P3)
   - Automated script to grep for "operational", "enabled", "complete" in docs
   - Cross-reference with actual code capabilities
   - Flag any new drift for immediate fix

7. **Truth-First Enforcement** (Process Change)
   - No PR merges without doc update
   - CI check: docs mention new features → must have status qualifier
   - Quarterly full audit by independent reviewer

---

## Part 9: Implementation Checklist

### Immediate (This Week)
- [ ] Create `.ops/FEATURE_STATUS_MATRIX.md` with honest status
- [ ] Update README.md with Operational/Partial/InProgress sections
- [ ] Update PRODUCT_SPEC.md with status qualifiers
- [ ] Restore `.ops/RATINGS_IMPLEMENTATION_GOVERNANCE.md` and approve Phase 1
- [ ] Update RATINGS_ARCHITECT.md status to "Phase 1 - with limitations"

### Week 1-2
- [ ] Fix test_integration.sh container name detection
- [ ] Fix misleading fundamentals logging
- [ ] Create `.env.observability.example` with full documentation
- [ ] Enhance `/health` endpoint to show observability status
- [ ] Update ORCHESTRATOR.md with current agent/pattern status

### Week 3-4
- [ ] Create DOCUMENTATION_REVIEW_CHECKLIST.md
- [ ] Audit all remaining .md files for drift
- [ ] Update all agent architect docs with current status
- [ ] Document all legacy entrypoint references and fix

### Continuous
- [ ] Weekly automated doc drift detection
- [ ] Quarterly independent audit
- [ ] Process enforcement in PR reviews

---

**Plan Status**: READY FOR APPROVAL
**Dependencies**: None (can start immediately)
**Blocks**: User trust, governance compliance, truth-first philosophy
**Owner**: Documentation team + Tech lead

**Next Action**: Get approval and start P0 tasks (24 hours of work)

---

## Appendix: Quote from User Feedback

> "Without these corrections, the documentation misrepresents the platform,
> governance lacks an audit trail, and key product promises remain unimplemented."

**This plan directly addresses all identified issues.**
