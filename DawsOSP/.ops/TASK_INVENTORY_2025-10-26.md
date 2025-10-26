# DawsOS Task Inventory - Comprehensive Master Backlog

**Date**: October 26, 2025
**Purpose**: Single source of truth for ALL remaining work (code + documentation)
**Status**: CONSOLIDATED - Integrates remediation plan + documentation alignment + implementation guardrails
**Last Audit**: 2025-10-26 (governance violations identified, 301 hours estimated)
**Guardrails**: [IMPLEMENTATION_GUARDRAILS.md](IMPLEMENTATION_GUARDRAILS.md) - MANDATORY zero-shortcuts policy

---

## Executive Summary

### Current State (Verified 2025-10-26)

**What Works** ✅:
- Core execution stack (Executor API → Pattern Orchestrator → Agent Runtime)
- 6 of 12 patterns fully operational (portfolio_overview, holding_deep_dive partial, etc.)
- Pricing pack immutability & reproducibility
- Multi-currency attribution
- Macro regime detection + Dalio cycles (5 regimes, 3 cycle types)
- Seed loader hydrates demo data (symbols, portfolios, pricing pack, macro cycles)

**What's Broken** ❌:
- 6 of 12 patterns fail or return stubs (buffett_checklist, policy_rebalance, scenarios, exports)
- Ratings use hardcoded 25% weights (not rubric-driven per spec)
- Fundamentals loading returns stubs even after FMP fetch
- Scenarios/DaR return "not yet implemented" errors
- Optimizer doesn't exist (policy_rebalance pattern fails)
- PDF exports return CSV text (WeasyPrint not integrated)
- Observability is opt-in and undocumented

**Documentation Drift** 📄:
- README/PRODUCT_SPEC advertise broken features as "operational"
- Governance docs outdated (still say "PRE-IMPLEMENTATION REVIEW")
- No feature status matrix (users can't tell what works)
- Logs mislead (claim "successfully fetched" when returning stubs)

---

## Master Backlog (Integrated View)

This backlog combines:
1. **Code Remediation** ([SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md](SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md)) - 245 hours
2. **Documentation Alignment** ([DOCUMENTATION_ALIGNMENT_PLAN.md](DOCUMENTATION_ALIGNMENT_PLAN.md)) - 50 hours
3. **Previous Task Inventory** (deprecated, superseded by this document)

**Total Remaining Effort**: 295 hours (37 person-days) over 10 weeks with 2-3 engineers

---

## Phase 1: Critical Accuracy Fixes (Week 1-2)

### P0-CODE-1: Rating Rubrics Database Implementation
**Effort**: 20 hours (2.5 days)
**Owner**: Backend Engineer
**Blocks**: buffett_checklist pattern accuracy

**Tasks**:
1. Create `rating_rubrics` table schema (4h)
2. Create 3 rubric seed JSON files from spec (6h)
   - `data/seeds/ratings/dividend_safety_v1.json`
   - `data/seeds/ratings/moat_strength_v1.json`
   - `data/seeds/ratings/resilience_v1.json`
3. Extend seed loader for ratings domain (4h)
4. Implement rubric loading in ratings.py (6h)
   - Add `_load_rubric_weights()` method
   - Update moat_strength(), dividend_safety(), resilience() methods
   - Add fallback logic and metadata flags

**Acceptance**:
- [ ] rating_rubrics table exists and seeded with 3 rubrics
- [ ] All 3 rating methods load weights from database
- [ ] Metadata includes `weights_source: "rubric"` (not "fallback")
- [ ] Integration test: different weights produce different ratings

**Files Modified**:
- backend/db/schema/rating_rubrics.sql (new)
- backend/db/init_database.sh
- data/seeds/ratings/*.json (3 new files)
- scripts/seed_loader.py
- backend/app/services/ratings.py

---

### P0-CODE-2: FMP Fundamentals Transformation
**Effort**: 14 hours (1.75 days)
**Owner**: Backend Engineer
**Blocks**: buffett_checklist pattern accuracy

**Tasks**:
1. Map FMP API response to ratings format (8h)
   - Implement `_transform_fmp_to_ratings_format()`
   - Add helper methods: `_calculate_5y_avg()`, `_calculate_std_dev()`, `_calculate_dividend_streak()`
2. Use real data in fundamentals_load (2h)
   - Update lines 611-621 to use transformation
   - Remove duplicate stub method from ratings_agent.py
3. Integration testing (4h)
   - Test with FMP API key (real data)
   - Test without API key (graceful fallback)
   - Test malformed responses (error handling)

**Acceptance**:
- [ ] FMP data transformed correctly for AAPL, JNJ, KO
- [ ] Different securities produce different fundamentals
- [ ] Stubs only used when API unavailable
- [ ] Metadata accurately reflects source (`fmp:AAPL` vs `stub`)
- [ ] No duplicate stub methods across agents

**Files Modified**:
- backend/app/agents/data_harvester.py
- backend/app/agents/ratings_agent.py (remove duplicate)

---

### P0-CODE-3: Database Schema Migration
**Effort**: 3 hours
**Owner**: DevOps/Backend
**Blocks**: P0-CODE-1

**Tasks**:
1. Add schema to init_database.sh (1h)
2. Create migration 010_add_rating_rubrics.sql (2h)
3. Test migration on staging database

**Acceptance**:
- [ ] New databases auto-create rating_rubrics table
- [ ] Existing databases can migrate without data loss
- [ ] Migration script is idempotent

**Files Modified**:
- backend/db/init_database.sh
- backend/db/migrations/010_add_rating_rubrics.sql

---

### P0-DOCS-1: Create Honest Feature Status Matrix
**Effort**: 4 hours
**Owner**: Tech Lead/PM
**Blocks**: User trust, governance compliance

**Deliverable**: `.ops/FEATURE_STATUS_MATRIX.md`

**Content**:
| Feature | Advertised | Actual Status | Patterns Affected | Remediation |
|---------|-----------|---------------|-------------------|-------------|
| Macro Scenarios | Operational | Stub (error) | portfolio_scenario_analysis | P1-CODE-1 (12h) |
| DaR | Operational | Stub (error) | portfolio_cycle_risk | P1-CODE-2 (16h) |
| Ratings | Complete | Partial (hardcoded weights, stub fundamentals) | buffett_checklist | P0-CODE-1,2 (34h) |
| Optimizer | Operational | Not implemented | policy_rebalance | P1-CODE-3 (40h) |
| PDF Exports | Operational | CSV only | export_portfolio_report | P2-CODE-3 (20h) |
| Observability | Enabled | Opt-in, undocumented | All patterns | P1-DOCS-3 (4h) |

**Acceptance**:
- [ ] All features accurately categorized
- [ ] Remediation effort estimated
- [ ] Referenced by README, PRODUCT_SPEC, CLAUDE.md

---

### P0-DOCS-2: Update Core Documentation
**Effort**: 12 hours (1.5 days)
**Owner**: Tech Lead
**Blocks**: False advertising, user confusion

**Tasks**:
1. Update README.md (2h)
   - Add "✅ Operational", "⚠️ Partial", "🚧 In Progress", "📋 Planned" sections
   - Move scenarios/DaR/optimizer/exports to "In Progress"
   - Add ratings limitations warning
2. Update PRODUCT_SPEC.md (6h)
   - Add `(P0/P1/P2)` qualifiers to all capability lists
   - Update section 7 (Macro) with scenario/DaR status
   - Update section 10 (Ratings) with Phase 1 limitations
   - Link to FEATURE_STATUS_MATRIX.md
3. Update CLAUDE.md (2h)
   - Update "Current State" with honest governance status
   - Link to both remediation plans
4. Update INDEX.md (2h)
   - Update documentation cleanup section
   - Reference feature status matrix

**Acceptance**:
- [ ] No feature claimed as "operational" that returns errors/stubs
- [ ] All limitations clearly documented
- [ ] Remediation plan linked from every "In Progress" item
- [ ] README examples match actual working features

**Files Modified**:
- README.md
- PRODUCT_SPEC.md
- CLAUDE.md
- INDEX.md

---

### P0-DOCS-3: Restore and Update Governance Documents
**Effort**: 4 hours
**Owner**: Tech Lead
**Blocks**: Governance audit trail

**Tasks**:
1. Check if `.ops/RATINGS_IMPLEMENTATION_GOVERNANCE.md` exists
   - If deleted: Restore from git commit 0721468
   - If exists: Update status
2. Update status to "PHASE 1 APPROVED"
3. Document approved deviations:
   - Hardcoded 25% weights (moat, resilience)
   - Stub fundamentals transformation
   - Phase 2 remediation timeline
4. Add sign-off section with approvals

**Acceptance**:
- [ ] Governance doc exists and is up-to-date
- [ ] Status changed from "PRE-IMPLEMENTATION REVIEW" to "PHASE 1 APPROVED"
- [ ] All deviations documented with remediation plans
- [ ] Sign-off recorded

**Files Modified/Created**:
- .ops/RATINGS_IMPLEMENTATION_GOVERNANCE.md

---

### P0-DOCS-4: Update Agent Architect Documentation
**Effort**: 4 hours
**Owner**: Tech Lead
**Blocks**: Developer confusion

**Tasks**:
1. Update `.claude/agents/business/RATINGS_ARCHITECT.md`
   - Change line 6 from "NOT IMPLEMENTED" to "✅ IMPLEMENTED (Phase 1 - with limitations)"
   - Add "Known Limitations (Phase 1)" section
   - Link to governance doc and remediation plan
2. Update `.claude/agents/analytics/MACRO_ARCHITECT.md`
   - Add status for scenario/DaR (pending implementation)
   - Link to P1-CODE-1, P1-CODE-2
3. Update `.claude/agents/ORCHESTRATOR.md`
   - Update agent registry status
   - List working patterns vs. failing patterns
   - Reference FEATURE_STATUS_MATRIX.md

**Acceptance**:
- [ ] No architect doc claims features are "NOT IMPLEMENTED" that exist
- [ ] All limitations clearly documented
- [ ] Links to remediation tasks for pending work

**Files Modified**:
- .claude/agents/business/RATINGS_ARCHITECT.md
- .claude/agents/analytics/MACRO_ARCHITECT.md
- .claude/agents/ORCHESTRATOR.md

---

## Phase 2: Feature Completion (Week 3-4)

### P1-CODE-1: Implement macro.run_scenario
**Effort**: 12 hours
**Owner**: Backend Engineer
**Blocks**: portfolio_scenario_analysis pattern

**Tasks**:
1. Wire macro_hound.py to scenarios service (4h)
   - Remove error stub from lines 419-430
   - Call `scenarios_service.run_scenario()`
   - Transform response to pattern format
2. Create scenario seed files (4h)
   - data/seeds/macro/scenarios/*.json
3. Test portfolio stress scenarios (4h)

**Acceptance**:
- [ ] `portfolio_scenario_analysis` pattern executes without errors
- [ ] Real scenario results returned (not stubs)
- [ ] At least 3 test scenarios seeded

**Files Modified**:
- backend/app/agents/macro_hound.py
- data/seeds/macro/scenarios/ (new files)

---

### P1-CODE-2: Implement macro.compute_dar
**Effort**: 16 hours (2 days)
**Owner**: Backend Engineer
**Blocks**: portfolio_cycle_risk pattern

**Tasks**:
1. Create dar_history schema (4h)
2. Wire agent to scenarios service (4h)
   - Remove error stub from lines 490-499
   - Call `scenarios_service.compute_dar()`
3. Implement DaR calculation logic (6h)
4. Test DaR scenarios (2h)

**Acceptance**:
- [ ] `portfolio_cycle_risk` pattern calculates real DaR
- [ ] dar_history table stores results
- [ ] DaR values match risk model expectations

**Files Modified**:
- backend/app/agents/macro_hound.py
- backend/db/schema/dar_history.sql (new)
- backend/app/services/scenarios.py

---

### P1-CODE-3: Implement Optimizer Service
**Effort**: 40 hours (5 days)
**Owner**: Backend Engineer
**Blocks**: policy_rebalance pattern

**Tasks**:
1. Integrate Riskfolio-Lib (12h)
   - Add to requirements.txt
   - Create optimizer wrapper class
2. Implement policy-based rebalancing (16h)
   - Load policy rules from database
   - Calculate optimal portfolio
   - Generate trade proposals
3. Transaction cost modeling (8h)
4. Test with real portfolio data (4h)

**Acceptance**:
- [ ] `policy_rebalance` pattern proposes trades
- [ ] Trades include transaction costs
- [ ] Optimization respects policy constraints

**Files Modified/Created**:
- backend/app/services/optimizer.py
- backend/app/agents/optimizer_agent.py (may need creation)
- backend/requirements.txt

---

### P1-DOCS-1: Fix Integration Tooling
**Effort**: 4 hours
**Owner**: DevOps
**Blocks**: Developer onboarding, CI/CD

**Tasks**:
1. Add container name detection to test_integration.sh
2. Apply same pattern to backend/run_integration_tests.sh
3. Test with both compose stacks (full + simple)

**Acceptance**:
- [ ] Scripts work with dawsos-postgres AND dawsos-dev-postgres
- [ ] No hardcoded container names
- [ ] Error messages helpful when containers not found

**Files Modified**:
- test_integration.sh
- backend/run_integration_tests.sh

---

### P1-DOCS-2: Fix Misleading Logs and Metadata
**Effort**: 2 hours
**Owner**: Backend Engineer
**Blocks**: Developer trust, debugging

**Tasks**:
1. Update data_harvester.py fundamentals_load logging
   - Change "Successfully fetched real fundamentals" to warning when returning stubs
   - Update metadata to honestly reflect source
2. Add `_attempted_real_fetch` flag for debugging

**Acceptance**:
- [ ] No logs claim success when returning stubs
- [ ] Metadata accurately reflects data source
- [ ] Developers can tell real from stub data

**Files Modified**:
- backend/app/agents/data_harvester.py

---

### P1-DOCS-3: Observability Documentation
**Effort**: 4 hours
**Owner**: DevOps/Backend
**Blocks**: Production monitoring

**Tasks**:
1. Create `.env.observability.example` (2h)
2. Update README with observability setup section (1h)
3. Enhance `/health` endpoint to show observability status (1h)

**Acceptance**:
- [ ] Users can enable observability by following docs
- [ ] `/health` shows tracing/metrics/error_tracking status
- [ ] Default deployment clearly shows observability is off

**Files Created/Modified**:
- .env.observability.example (new)
- README.md
- backend/app/api/routes/health.py (or equivalent)

---

## Phase 3: Polish and Production-Readiness (Week 5-6)

### P2-CODE-1: Replace Placeholder Charts
**Effort**: 16 hours (2 days)
**Owner**: Backend Engineer
**Patterns**: holding_deep_dive, portfolio_overview

**Tasks**:
1. Implement real performance metrics (8h)
   - Replace placeholders in financial_analyst.py:973-981
   - Wire to actual metrics service
2. Implement attribution charts (6h)
   - Replace placeholders in financial_analyst.py:1060-1102
3. Test charts with real portfolio data (2h)

**Acceptance**:
- [ ] Charts show real data (not hardcoded 15%, 0.83 Sharpe)
- [ ] Different portfolios show different charts

**Files Modified**:
- backend/app/agents/financial_analyst.py

---

### P2-CODE-2: Complete Holding Deep Dive
**Effort**: 8 hours (1 day)
**Owner**: Backend Engineer
**Pattern**: holding_deep_dive

**Tasks**:
1. Integrate provider for market cap, P/E, sector (6h)
2. Remove placeholder values (2h)

**Acceptance**:
- [ ] Holding details show real fundamental data
- [ ] Provider integration tested

**Files Modified**:
- backend/app/agents/financial_analyst.py

---

### P2-CODE-3: PDF Export Implementation
**Effort**: 20 hours (2.5 days)
**Owner**: Backend Engineer
**Pattern**: export_portfolio_report

**Tasks**:
1. Integrate WeasyPrint (8h)
2. Create PDF templates (8h)
3. Add watermarking/attribution (4h)

**Acceptance**:
- [ ] Exports produce actual PDFs (not CSV text)
- [ ] PDFs include watermark and attribution

**Files Modified**:
- backend/app/services/reports.py
- backend/requirements.txt

---

### P2-DOCS-1: Documentation Review Process
**Effort**: 2 hours
**Owner**: Tech Lead
**Deliverable**: `.ops/DOCUMENTATION_REVIEW_CHECKLIST.md`

**Content**: Checklist for any new feature PR
- [ ] README.md updated with correct status
- [ ] PRODUCT_SPEC.md includes status qualifier
- [ ] Agent architect doc updated
- [ ] FEATURE_STATUS_MATRIX.md updated
- [ ] Metadata accurately reflects data source
- [ ] Pattern execution tested end-to-end
- [ ] Governance doc created (if Phase 1 deviations)
- [ ] Integration tests verify functionality
- [ ] No misleading logs

---

### P2-DOCS-2: Remaining Documentation Audit
**Effort**: 8 hours (1 day)
**Owner**: Tech Lead

**Tasks**:
1. Audit all .md files in root, .claude/agents/, .ops/
2. Verify claims against actual code
3. Add status qualifiers where needed
4. Remove aspirational language
5. Link to remediation plan for pending features

**Acceptance**:
- [ ] No documentation makes false claims
- [ ] All features have status qualifiers
- [ ] Links to remediation tasks work

---

## Phase 4: Continuous Improvements (Week 7+)

### P3-CODE-1: Provider Integration Cleanup
**Effort**: 20 hours
**Owner**: Backend Engineer

**Tasks**:
1. Polygon price transformation (8h)
2. FRED macro transformation (8h)
3. NewsAPI transformation (4h)

---

### P3-CODE-2: Performance Optimization
**Effort**: 16 hours
**Owner**: Backend Engineer

**Tasks**:
1. Optimize rubric loading (caching)
2. Batch provider requests
3. Query optimization
4. Meet p95 < 1.2s SLO

---

### P3-DOCS-1: Weekly Documentation Audits
**Effort**: 2 hours/week ongoing
**Owner**: Tech Lead

**Process**:
1. Automated script greps for "operational", "enabled", "complete"
2. Cross-reference with capabilities in code
3. Flag any new drift
4. Fix within 1 week

---

## Summary Tables

### Effort by Phase

| Phase | Code (hours) | Docs (hours) | Total (hours) | Duration (weeks) |
|-------|--------------|--------------|---------------|------------------|
| **Phase 1 (P0)** | 37 | 24 | 61 | 2 |
| **Phase 2 (P1)** | 68 | 10 | 78 | 2 |
| **Phase 3 (P2)** | 44 | 10 | 54 | 2 |
| **Phase 4 (P3)** | 96 | 12 | 108 | 4+ |
| **Total** | 245 | 56 | 301 | 10 |

### Effort by Component

| Component | Tasks | Effort (hours) | Files Affected |
|-----------|-------|----------------|----------------|
| **Ratings** | 4 | 40 | ratings.py, ratings_agent.py, data_harvester.py, seed files |
| **Fundamentals** | 2 | 16 | data_harvester.py, providers.py |
| **Macro** | 2 | 28 | macro_hound.py, scenarios.py, schema files |
| **Optimizer** | 1 | 40 | optimizer.py, optimizer_agent.py |
| **Documentation** | 8 | 56 | README, PRODUCT_SPEC, CLAUDE, architect docs |
| **Tooling** | 2 | 6 | test_integration.sh, run_integration_tests.sh |
| **Observability** | 1 | 4 | .env.observability.example, README |
| **Charts/UX** | 2 | 24 | financial_analyst.py |
| **Exports** | 1 | 20 | reports.py |
| **Process** | 2 | 10 | Review checklist, weekly audits |

---

## Critical Path

```
Week 1-2 (P0):
  - Ratings rubrics (20h) + FMP transformation (14h) + Schema migration (3h)
  - Feature matrix (4h) + Core docs (12h) + Governance (4h) + Architect docs (4h)
  → Deliverable: Honest docs + accurate ratings

Week 3-4 (P1):
  - Scenarios (12h) + DaR (16h) + Optimizer (40h)
  - Tooling (4h) + Logs (2h) + Observability (4h)
  → Deliverable: All patterns work + truthful monitoring

Week 5-6 (P2):
  - Charts (16h) + Holding details (8h) + PDF exports (20h)
  - Review process (2h) + Doc audit (8h)
  → Deliverable: Production-ready quality

Week 7+ (P3):
  - Provider integration (20h) + Performance (16h)
  - Weekly audits (2h/week ongoing)
  → Deliverable: Continuous improvement
```

---

## Success Criteria

### Code Remediation Complete When:
- [ ] Zero "GOVERNANCE DEVIATION" comments
- [ ] Zero "Phase 1/Phase 2" markers (use proper TODOs)
- [ ] All 12 patterns execute without errors
- [ ] Different inputs produce different outputs (no universal stubs)
- [ ] Metadata accurately reflects data sources

### Documentation Alignment Complete When:
- [ ] Zero false claims (all "operational" features work)
- [ ] Zero misleading logs (stubs logged as stubs)
- [ ] FEATURE_STATUS_MATRIX.md is single source of truth
- [ ] All docs reference matrix for current state
- [ ] Integration tests pass for advertised features
- [ ] Documentation review checklist used for all PRs

### Production-Ready When:
- [ ] Code remediation complete
- [ ] Documentation alignment complete
- [ ] Integration tests ≥95% pass rate
- [ ] Performance SLOs met (p95 < 1.2s)
- [ ] Governance docs approved and signed off
- [ ] Weekly audit process operational

---

## References

**Detailed Plans**:
- [SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md](SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md) - 245 hours, code fixes
- [DOCUMENTATION_ALIGNMENT_PLAN.md](DOCUMENTATION_ALIGNMENT_PLAN.md) - 50 hours, doc fixes
- [GOVERNANCE_VIOLATIONS_AUDIT_2025-10-26.md](GOVERNANCE_VIOLATIONS_AUDIT_2025-10-26.md) - Audit findings

**Deprecated**:
- ~~TASK_INVENTORY_2025-10-24.md~~ - Replaced by this document
- ~~STABILITY_PLAN.md~~ - Outdated (described pool issue that's fixed)
- ~~IMPLEMENTATION_ROADMAP_V2.md~~ - Original 8-week plan (reality is 10 weeks)

---

**Last Updated**: 2025-10-26
**Next Review**: Weekly (Fridays)
**Owner**: Tech Lead + PM
**Approval Status**: DRAFT - Pending stakeholder sign-off

**This inventory replaces ALL scattered TODO lists. Update HERE whenever scope changes.**
