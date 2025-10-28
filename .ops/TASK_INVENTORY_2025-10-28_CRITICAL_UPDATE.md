# DawsOS Task Inventory - CRITICAL UPDATE
**Date**: October 28, 2025
**Status**: 🔴 **CRITICAL ISSUES FOUND**
**Purpose**: Emergency update with critical blockers discovered in comprehensive audit

---

## ⚠️ CRITICAL: DO NOT DEPLOY

**System Status**: 60-65% Complete (NOT 85-90% as previously claimed)

**Reason**: Critical pattern/agent mismatches will cause runtime failures

See [COMPREHENSIVE_SYSTEM_AUDIT_2025-10-28.md](../COMPREHENSIVE_SYSTEM_AUDIT_2025-10-28.md) for full details.

---

## 🔴 PHASE 0: CRITICAL BLOCKERS (Must Fix This Week)

**Status**: BLOCKING ALL OTHER WORK

### BLOCKER 1: Broken Import Paths (7 agents) 🔴

**Impact**: All agent capabilities will fail at runtime

**Files Affected**:
- `backend/app/agents/macro_hound.py:129`
- `backend/app/agents/data_harvester.py:115`
- `backend/app/agents/financial_analyst.py:781-783`
- `backend/app/agents/optimizer_agent.py:67`
- `backend/app/agents/ratings_agent.py:45`

**Problem**: Imports use `from app.` instead of `from backend.app.`

**Fix** (2 hours):
```bash
find backend/app/agents -name "*.py" -exec sed -i 's/from app\./from backend.app./g' {} \;
```

**Assignee**: Backend team
**Priority**: P0 - IMMEDIATE
**Estimated**: 2 hours

---

### BLOCKER 2: Pattern/Capability Mismatches (4 patterns) 🔴

**Impact**: Patterns fail immediately on execution

#### 2.1 News Impact Analysis - Capability Name Mismatch

**File**: `backend/patterns/workflows/news_impact_analysis.json:71`

**Problem**:
```json
"capability": "news.search"  // ❌ Pattern uses this
// Agent declares: "news_search"  // ❌ Name mismatch
```

**Fix Options**:
```json
// Option A: Update pattern
"capability": "news_search"

// Option B: Update agent (backend/app/agents/data_harvester.py:312)
def get_capabilities(self):
    return ["news.search", "news.compute_portfolio_impact"]
```

**Assignee**: Backend team
**Priority**: P0 - IMMEDIATE
**Estimated**: 1 hour

---

#### 2.2 Policy Rebalance - Optimizer Ignores Constraints

**File**: `backend/patterns/smart/policy_rebalance.json:80`

**Problem**:
```json
"inputs": {
    "policies": "{{inputs.policies}}",      // ❌ IGNORED
    "constraints": "{{inputs.constraints}}" // ❌ IGNORED
}
```

**Agent** (`backend/app/agents/optimizer_agent.py:67`):
```python
def propose_trades(self, portfolio_id: str, positions, valuations, **kwargs):
    # ❌ kwargs['policies'] and kwargs['constraints'] never used
```

**Service** (`backend/app/services/optimizer.py:369`):
```python
def propose_trades(self, portfolio_id: str):
    # ❌ No policies/constraints parameters
```

**Fix Required**:
1. Add `policies` and `constraints` parameters to OptimizerService.propose_trades
2. Add constraint application logic
3. Update agent to pass parameters through

**Assignee**: Backend team
**Priority**: P0 - CRITICAL (affects core functionality)
**Estimated**: 1 day

---

#### 2.3 Portfolio Scenario Analysis - Wrong Parameter Type

**File**: `backend/patterns/smart/portfolio_scenario_analysis.json:82`

**Problem**:
```json
"inputs": {
    "scenario_result": "{{steps.run_scenario.result}}"  // ❌ Passes DICT
}
```

**Agent** (`backend/app/agents/optimizer_agent.py:311`):
```python
def suggest_hedges(self, scenario_id: str, portfolio_id: str):  # ❌ Expects STRING
```

**Fix Options**:
```json
// Option A: Update pattern to pass scenario_id only
"inputs": {
    "scenario_id": "{{steps.run_scenario.result.scenario_id}}",
    "portfolio_id": "{{inputs.portfolio_id}}"
}

// Option B: Update agent to accept dict
def suggest_hedges(self, scenario_result: Dict, portfolio_id: str):
```

**Assignee**: Backend team
**Priority**: P0 - IMMEDIATE
**Estimated**: 2 hours

---

#### 2.4 Cycle Deleveraging - Missing Regime Parameter

**File**: `backend/patterns/workflows/cycle_deleveraging_scenarios.json:88`

**Problem**:
```json
"inputs": {
    "portfolio_id": "{{inputs.portfolio_id}}"
    // ❌ MISSING: regime parameter
}
```

**Agent** (`backend/app/agents/optimizer_agent.py:409`):
```python
def suggest_deleveraging_hedges(self, portfolio_id: str, regime: str):  # ❌ Requires regime
```

**Fix**:
```json
"inputs": {
    "portfolio_id": "{{inputs.portfolio_id}}",
    "regime": "{{steps.detect_regime.result.current_regime}}"  // ADD
}
```

**Assignee**: Backend team
**Priority**: P0 - IMMEDIATE
**Estimated**: 1 hour

---

### BLOCKER 3: Broken Python Environment 🔴

**Impact**: CI/CD cannot run, tests cannot execute

**Problem**:
```bash
$ pytest backend/tests/
ERROR: virtualenv path points to /Users/.../DawsOSB/DawsOSP/venv
# ❌ Old path (DawsOSB removed during consolidation)
```

**Fix** (1 hour):
```bash
# Delete old venv
rm -rf venv/

# Create new venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Update pyproject.toml paths
sed -i 's|DawsOSB/DawsOSP|DawsOSP|g' pyproject.toml
```

**Assignee**: DevOps/Backend
**Priority**: P0 - IMMEDIATE
**Estimated**: 1 hour

---

### BLOCKER 4: Run UAT Tests 🔴

**Impact**: Unknown failure rate until tested

**Command**:
```bash
pytest backend/tests/integration/test_uat_p0.py -v
```

**Expected**: Several tests will FAIL due to blockers 1-3

**After Fixes**: Re-run to verify all 18 scenarios pass

**Assignee**: QA/Backend
**Priority**: P0 - IMMEDIATE (after blockers 1-3)
**Estimated**: 2 hours

---

## 🟡 PHASE 1: Data Quality (High Priority)

**Status**: Not blocking deployment but critical for accuracy

### Issue 5: Analytics Return Stub Data 🟡

**Impact**: Patterns execute but return meaningless data

**Files**:
- `backend/app/agents/financial_analyst.py:1155-1169` (portfolio contribution)
- `backend/app/agents/financial_analyst.py:817-829` (factor history)
- `backend/app/agents/financial_analyst.py:1688-1715` (comparables)

**Problems**:
```python
# Hard-coded 15% return for ALL positions
def compute_portfolio_contribution(self, portfolio_id: str, position_id: int):
    return {"contribution": 0.15}  # ❌ STUB

# Only returns 1 data point (not time series)
def get_factor_history(self, portfolio_id: str, timeframe: str):
    return {"factors": [{"date": "2025-10-28", "value": 0.15}]}  # ❌ STUB

# Always returns empty list
def find_comparables(self, symbol: str):
    return {"comparables": []}  # ❌ STUB
```

**Fix Required**: Implement real calculations

**Assignee**: Backend team
**Priority**: P1 - HIGH
**Estimated**: 3-4 days

---

### Issue 6: Scenario Persistence Incomplete 🟡

**Impact**: Scenario results not fully persisted

**File**: `backend/app/services/scenarios.py:265-288`

**Problems**:
```python
# Hard-coded factor betas
factor_betas = {"equity": -0.20, "rates": 0.10}  # ❌ STUB

# Only writes to dar_history (missing scenario_results table)
# No KG integration
```

**Fix Required**:
1. Create `scenario_results` table migration
2. Compute real factor betas
3. Store full scenario state

**Assignee**: Backend team
**Priority**: P1 - HIGH
**Estimated**: 2-3 days

---

### Issue 7: PDF Export Falls Back to HTML 🟡

**Impact**: PDF export doesn't work without WeasyPrint

**File**: `backend/app/services/reports.py:135-170`

**Problem**:
```python
try:
    import weasyprint
except ImportError:
    return self._generate_html_report()  # ❌ Returns HTML not PDF
```

**Fix Required**:
1. Add WeasyPrint to requirements.txt
2. Better error handling with user message

**Assignee**: Backend team
**Priority**: P1 - MEDIUM
**Estimated**: 1 day

---

## 🔵 PHASE 2: UI Completion (High Priority)

**Status**: 70% complete (not 100% as claimed)

### Issue 8: Charts Not Integrated 🔵

**Impact**: 4 chart components are placeholders

**Files**:
- `dawsos-ui/src/components/PerformanceChart.tsx`
- `dawsos-ui/src/components/DaRVisualization.tsx`
- `dawsos-ui/src/components/BuffettRatingCard.tsx`
- Allocation chart (not created)

**Fix Required**:
```bash
cd dawsos-ui
npm install recharts date-fns
# Implement 4 chart types with divine proportions theme
```

**Assignee**: Frontend team
**Priority**: P1 - HIGH
**Estimated**: 3-5 days

---

### Issue 9: No Backend Integration 🔵

**Impact**: UI shows mock data only

**Missing**:
- API client (`src/lib/api/executor.ts`) ❌
- React Query setup ❌
- Type definitions for backend responses ❌

**Fix Required**:
```bash
cd dawsos-ui
npm install @tanstack/react-query zod
# Create API client
# Connect all 6 pages to backend patterns
```

**Assignee**: Frontend team
**Priority**: P1 - HIGH
**Estimated**: 5-7 days

---

### Issue 10: No shadcn/ui (Accessibility) 🔵

**Impact**: Custom components lack Radix accessibility features

**Fix Required**:
```bash
cd dawsos-ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card table alert toast
# Migrate components to Radix-based
```

**Assignee**: Frontend team
**Priority**: P1 - MEDIUM
**Estimated**: 3-4 days

---

## 📝 PHASE 3: Documentation & Governance

### Issue 11: CLAUDE.md Outdated Counts 📝

**Current Claims**:
```markdown
**Agents**: 7 files, 2 registered
**Patterns**: 16 JSON files
```

**Reality**:
```bash
$ ls backend/app/agents/*.py | wc -l
9  # ✅ 9 agent files (not 7)

$ grep "register_agent" backend/app/api/executor.py | wc -l
9  # ✅ 9 registered (not 2)

$ find backend/patterns -name "*.json" | wc -l
12  # ✅ 12 patterns (not 16)
```

**Fix**: Update CLAUDE.md with correct counts

**Assignee**: Documentation team
**Priority**: P2 - MEDIUM
**Estimated**: 1 hour

---

### Issue 12: Add CI/CD Quality Gates 📝

**Missing**:
- Run `scripts/audit_capabilities.py` in CI
- Run `pytest` in CI
- Prevent pattern/agent drift

**Fix Required**:
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run capability audit
        run: python scripts/audit_capabilities.py
      - name: Run tests
        run: pytest backend/tests/
```

**Assignee**: DevOps
**Priority**: P2 - HIGH
**Estimated**: 2-3 days

---

## ⚪ PHASE 4: Future Work (Post-MVP)

### Knowledge Graph (0% Complete)

**Status**: NO CODE EXISTS - Plan only

**Required**:
1. `backend/app/services/neo4j.py` (Neo4j connection)
2. `backend/app/services/knowledge_graph.py` (KG operations)
3. `backend/db/neo4j_migrations/` (Cypher schema)
4. Neo4j in docker-compose.yml
5. `backend/app/services/graphrag.py` (RAG service)

**Assignee**: Future sprint
**Priority**: P3 - LOW (post-MVP)
**Estimated**: 2-3 weeks

---

## Updated Completion Status

| Component | Previous Claim | Actual Status | Completion |
|-----------|---------------|---------------|------------|
| **Backend Core** | 85-90% | Broken imports, pattern mismatches | 65% |
| **Patterns** | Production-ready | 4 patterns broken | 70% |
| **Agents** | Operational | Import errors, stubs | 70% |
| **Services** | Complete | Missing parameters, stubs | 75% |
| **Frontend** | 100% | Charts/API missing | 70% |
| **Testing** | Comprehensive | Broken venv, can't run | 50% |
| **Documentation** | Accurate | Outdated counts | 60% |
| **KG/RAG** | Planned | Non-existent | 0% |
| **Overall** | **85-90%** | **REALITY CHECK** | **60-65%** |

---

## Critical Timeline

### Week 1: Fix Blockers (Phase 0)
- Day 1: Fix import paths (BLOCKER 1)
- Day 2-3: Fix pattern/capability mismatches (BLOCKER 2)
- Day 4: Fix Python environment (BLOCKER 3)
- Day 5: Run UAT tests (BLOCKER 4)

**Deliverable**: Backend patterns execute without errors

### Week 2: Data Quality (Phase 1)
- Days 1-3: Implement real analytics (Issue 5)
- Days 4-5: Complete scenario persistence (Issue 6)

**Deliverable**: Patterns return real data

### Week 3-4: UI Completion (Phase 2)
- Week 3: Charts + API integration (Issues 8-9)
- Week 4: shadcn/ui + accessibility (Issue 10)

**Deliverable**: Functional UI with real data

### Week 5: Quality & Governance (Phase 3)
- Update documentation (Issue 11)
- Add CI/CD (Issue 12)
- Full UAT regression

**Deliverable**: Production-ready system at true 80%

---

## Action Items by Role

### Backend Team (Immediate)
1. 🔴 Fix import paths (7 files, 2 hours)
2. 🔴 Fix news capability mismatch (1 hour)
3. 🔴 Fix optimizer constraints (1 day)
4. 🔴 Fix scenario parameter types (3 hours)
5. 🟡 Implement real analytics (3-4 days)

### Frontend Team (This Week)
1. 🔵 Install Recharts and implement charts (3-5 days)
2. 🔵 Create API client (2-3 days)
3. 🔵 Install shadcn/ui (3-4 days)

### DevOps Team (This Week)
1. 🔴 Recreate Python venv (1 hour)
2. 🔴 Run UAT tests (2 hours)
3. 📝 Set up CI/CD (2-3 days)

### Documentation Team (This Week)
1. 📝 Update CLAUDE.md counts (1 hour)
2. 📝 Update PRODUCT_SPEC.md statuses (1 hour)

---

## References

- **Full Audit**: [COMPREHENSIVE_SYSTEM_AUDIT_2025-10-28.md](../COMPREHENSIVE_SYSTEM_AUDIT_2025-10-28.md)
- **UI Verification**: [UI_IMPLEMENTATION_VERIFICATION_REPORT.md](../UI_IMPLEMENTATION_VERIFICATION_REPORT.md)
- **Product Spec**: [PRODUCT_SPEC.md](../PRODUCT_SPEC.md)
- **Previous Inventory**: [TASK_INVENTORY_2025-10-24.md](TASK_INVENTORY_2025-10-24.md) (SUPERSEDED)

---

**Status**: 🔴 CRITICAL - Address Phase 0 blockers before ANY other work

**Next Update**: After Phase 0 completion (estimated 1 week)
