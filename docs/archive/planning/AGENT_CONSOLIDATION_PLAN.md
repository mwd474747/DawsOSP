# DawsOS Agent Consolidation Plan
## Consolidate to 15-Agent Trinity Model & Remove Legacy Code

**Status:** Planning Phase
**Created:** 2025-10-04
**Estimated Effort:** 8-11 hours (1-2 work days)
**Risk Level:** Medium (High risk for PatternEngine changes, Low risk for archive management)

---

## Executive Summary

This plan consolidates DawsOS from legacy 18+ agent architecture to a clean **15-agent Trinity model**, removing dead code and legacy references while preserving all functionality through pattern-driven routing.

**Key Goals:**
1. ✅ Fix `equity_agent` reference in PatternEngine (runtime error)
2. ✅ Archive 3 legacy agents (equity, macro, risk) outside package
3. ✅ Update tests and examples to use current agents
4. ✅ Document migration path for future developers
5. ✅ Achieve zero legacy agent references in active code

---

## CURRENT STATE ANALYSIS

### ✅ Active Agents (15 registered in main.py)
1. **graph_mind** - Knowledge graph operations
2. **claude** - LLM orchestration and reasoning
3. **data_harvester** - External data collection (APIs)
4. **data_digester** - Data normalization and ingestion
5. **relationship_hunter** - Graph relationship discovery
6. **pattern_spotter** - Pattern recognition and analysis
7. **forecast_dreamer** - Forecasting and predictions
8. **code_monkey** - Code generation
9. **structure_bot** - File/directory organization
10. **refactor_elf** - Code refactoring
11. **workflow_recorder** - Workflow capture
12. **workflow_player** - Workflow replay
13. **ui_generator** - UI component generation
14. **financial_analyst** - Financial analysis and metrics
15. **governance_agent** - Compliance and governance

### ❌ Legacy Agents (Found in backups, not registered)
- **equity_agent** (backup: `dawsos/storage/backups/.../equity_agent.py`)
- **macro_agent** (backup: `dawsos/storage/backups/.../macro_agent.py`)
- **risk_agent** (backup: `dawsos/storage/backups/.../risk_agent.py`)

### ⚠️ Legacy References Found
1. **PatternEngine** (`pattern_engine.py:1580-1590`)
   - Calls `equity_agent` for stock analysis
   - Falls back silently if agent not found
   - Should use `financial_analyst` instead

2. **Test Files** (`test_compliance.py`)
   - Registers mock `macro_agent` for testing
   - Should use actual registered agents

3. **Examples** (`analyze_existing_patterns.py`, `compliance_demo.py`)
   - References `macro_agent` and `equity_agent`
   - Educational/demo code only

4. **Archived Orchestrators**
   - `dawsos/archived_legacy/claude_orchestrator.py`
   - `dawsos/archived_legacy/orchestrator.py`
   - Already archived, but could be moved to proper archive

---

## CONSOLIDATION PLAN

### PHASE 1: Code Remediation (Fix Active References)

**Priority: CRITICAL** - Fixes runtime errors

#### Task 1.1: Fix PatternEngine equity_agent Reference
**File:** `dawsos/core/pattern_engine.py` (lines 1580-1590)

**Current Code:**
```python
equity_agent = self._get_agent('equity_agent') if self.runtime else None
if equity_agent:
    stock_analysis = equity_agent.analyze_stock(symbol)
```

**Replacement Strategy:**
```python
financial_analyst = self._get_agent('financial_analyst') if self.runtime else None
if financial_analyst:
    # Financial analyst has analyze_company method - use it
    stock_analysis = financial_analyst.analyze_company({'symbol': symbol})
```

**Impact:**
- Fixes dead code path (equity_agent never registered)
- Uses existing financial_analyst capabilities
- Maintains moat analysis functionality

**Validation:**
- Check FinancialAnalyst has analyze_company or similar method
- Test moat analysis pattern still works
- Verify no runtime errors

---

#### Task 1.2: Update Test Mocks
**File:** `dawsos/tests/test_compliance.py`

**Current Code:**
```python
self.registry.register('macro_agent', MockAgent('macro_agent'))
```

**Replacement Strategy:**
- Replace with registered agent name (e.g., 'financial_analyst' or 'pattern_spotter')
- OR keep as MockAgent but document it's for testing only
- Update test assertions to match real agent behavior

**Impact:**
- Tests use actual system agents
- Better integration test coverage
- Catches real agent interface changes

---

### PHASE 2: Archive Management (Organize Legacy Code)

**Priority: HIGH** - Prevents accidental imports

#### Task 2.1: Consolidate Archive Location
**Action:** Move all legacy agents to single archive outside package

**Current Locations:**
- `dawsos/storage/backups/before_fix_duplicates_20251001_220224/agents/`
  - equity_agent.py
  - macro_agent.py
  - risk_agent.py
- `dawsos/archived_legacy/`
  - claude_orchestrator.py
  - orchestrator.py

**Target Location:**
```
archive/
├── README.md (explains what's here and why)
├── agents/
│   ├── equity_agent.py (moved from backups)
│   ├── macro_agent.py (moved from backups)
│   └── risk_agent.py (moved from backups)
└── orchestrators/
    ├── claude_orchestrator.py (moved from archived_legacy)
    └── orchestrator.py (moved from archived_legacy)
```

**Benefits:**
- Clear separation from active codebase
- No accidental imports (outside dawsos/ package)
- Preserves history for reference
- Easy to find and review if needed

**Commands:**
```bash
mkdir -p archive/agents archive/orchestrators
cp dawsos/storage/backups/before_fix_duplicates_20251001_220224/agents/*.py archive/agents/
cp dawsos/archived_legacy/*.py archive/orchestrators/
rm -rf dawsos/archived_legacy/
```

---

#### Task 2.2: Create Archive Documentation
**File:** `archive/README.md`

**Content:**
```markdown
# DawsOS Archived Legacy Code

This directory contains code that has been superseded by the Trinity Architecture.

## Archived Agents (Replaced by 15-Agent Model)

### equity_agent.py
- **Replaced by:** financial_analyst
- **Reason:** Functionality consolidated into financial_analyst
- **Date Archived:** 2025-10-04
- **Last Known Working:** Pre-Trinity (before Oct 2025)

### macro_agent.py
- **Replaced by:** financial_analyst + pattern_spotter
- **Reason:** Macro analysis now handled by pattern-driven approach
- **Date Archived:** 2025-10-04

### risk_agent.py
- **Replaced by:** financial_analyst + governance_agent
- **Reason:** Risk split between financial analysis and compliance
- **Date Archived:** 2025-10-04

## Archived Orchestrators (Replaced by UniversalExecutor)

### claude_orchestrator.py
- **Replaced by:** core/universal_executor.py
- **Reason:** Trinity Architecture uses unified execution path
- **Date Archived:** 2025-10-02

### orchestrator.py
- **Replaced by:** core/universal_executor.py
- **Reason:** Pre-Trinity orchestration logic
- **Date Archived:** 2025-10-02

## Do Not Use

This code is **NOT** imported or used by the active system.
It is kept for historical reference only.

If you need functionality from these agents, use the Trinity replacements listed above.
```

---

### PHASE 3: Example & Documentation Updates

**Priority: MEDIUM** - Educational materials

#### Task 3.1: Update Example Scripts
**Files:**
- `dawsos/examples/analyze_existing_patterns.py`
- `dawsos/examples/compliance_demo.py`

**Changes:**
- Replace `macro_agent` → `financial_analyst`
- Replace `equity_agent` → `financial_analyst`
- Add comments explaining Trinity routing
- Update to use pattern-driven approach where applicable

**Example Update:**
```python
# OLD
macro_agent = runtime.get_agent('macro_agent')
result = macro_agent.analyze_economy()

# NEW - Trinity Pattern-Driven Approach
result = pattern_engine.execute_pattern('macro_analysis', {
    'indicators': ['GDP', 'UNRATE', 'FEDFUNDS']
})
# Internally routes through: PatternEngine → financial_analyst/data_harvester
```

---

#### Task 3.2: Update Pattern Documentation
**Action:** Document which agents handle which patterns

**Create/Update:** `docs/AGENT_PATTERN_MAPPING.md`

**Content:**
```markdown
# Agent-Pattern Mapping

## Financial Analysis Patterns
- `fundamental_analysis` → financial_analyst
- `macro_analysis` → financial_analyst + data_harvester
- `dcf_valuation` → financial_analyst
- `buffett_checklist` → financial_analyst
- `moat_analyzer` → financial_analyst

## Market Data Patterns
- `stock_price` → data_harvester
- `sector_performance` → data_harvester + pattern_spotter
- `market_regime` → pattern_spotter + financial_analyst

## Governance Patterns
- `compliance_audit` → governance_agent
- `policy_validation` → governance_agent
- `data_quality_check` → governance_agent

## Legacy Agent Replacement Guide
- `equity_agent` → Use `financial_analyst` with company_analysis pattern
- `macro_agent` → Use `macro_analysis` pattern (routes to financial_analyst)
- `risk_agent` → Use `risk_assessment` pattern (routes to financial_analyst)
```

---

### PHASE 4: Verification & Testing

**Priority: CRITICAL** - Ensure nothing breaks

#### Task 4.1: Search for Remaining References
**Commands:**
```bash
# Search for any remaining legacy agent references
grep -r "equity_agent\|macro_agent\|risk_agent" dawsos \
  --include="*.py" \
  --exclude-dir=__pycache__ \
  --exclude-dir=storage/backups \
  --exclude-dir=archived_legacy

# Should return ZERO results after cleanup
```

---

#### Task 4.2: Run Test Suite
**Commands:**
```bash
# Run compliance tests
python3 -m pytest dawsos/tests/test_compliance.py -v

# Run agent tests
python3 -m pytest dawsos/tests/validation/test_agents.py -v

# Run pattern tests
python3 -m pytest dawsos/tests/validation/test_patterns.py -v

# Run full system test
python3 -m pytest dawsos/tests/validation/test_full_system.py -v
```

**Expected Results:**
- All tests pass
- No references to unregistered agents
- PatternEngine uses financial_analyst correctly

---

#### Task 4.3: Integration Smoke Test
**Script:** Create manual smoke test

```python
# smoke_test_agents.py
import sys
sys.path.insert(0, 'dawsos')

from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from core.pattern_engine import PatternEngine

# Test 1: Verify 15 agents registered
runtime = AgentRuntime()
# ... register agents (copy from main.py)

assert len(runtime._agents) == 15, f"Expected 15 agents, got {len(runtime._agents)}"
print("✅ All 15 agents registered")

# Test 2: Verify no legacy agent calls
try:
    runtime.execute('equity_agent', {})
    print("❌ FAIL: equity_agent should not exist")
except:
    print("✅ equity_agent correctly not registered")

# Test 3: Verify financial_analyst works for stock analysis
result = runtime.execute('financial_analyst', {
    'task': 'analyze_company',
    'symbol': 'AAPL'
})
assert 'error' not in result, f"Financial analyst failed: {result}"
print("✅ financial_analyst handles stock analysis")

# Test 4: Verify pattern routing
g = KnowledgeGraph()
pe = PatternEngine('dawsos/patterns', runtime=runtime, graph=g)
moat_pattern = pe.get_pattern('moat_analyzer')
assert moat_pattern is not None
print("✅ moat_analyzer pattern exists")

print("\n🎉 All smoke tests passed!")
```

---

### PHASE 5: Documentation & Communication

**Priority: MEDIUM** - Team awareness

#### Task 5.1: Update Architecture Docs
**File:** `docs/TRINITY_ARCHITECTURE.md`

**Add Section:**
```markdown
## Agent Consolidation (Oct 2025)

The system was consolidated from 18+ agents to 15 core agents aligned with Trinity principles.

### Removed Agents (Functionality Preserved)
- `equity_agent` → Merged into `financial_analyst`
- `macro_agent` → Handled by `macro_analysis` pattern via `financial_analyst`
- `risk_agent` → Split between `financial_analyst` and `governance_agent`

### Why?
- **Simplicity:** Fewer agents, clearer responsibilities
- **Trinity Alignment:** Pattern-driven routing instead of agent sprawl
- **Maintainability:** Less code duplication, easier testing
- **Performance:** Reduced overhead from fewer agent instances

All functionality is preserved through the pattern-driven approach.
```

---

#### Task 5.2: Create Migration Guide
**File:** `docs/LEGACY_AGENT_MIGRATION.md`

**Content:**
```markdown
# Legacy Agent Migration Guide

If you have code referencing old agents, update as follows:

## equity_agent → financial_analyst

**Before:**
```python
equity = runtime.get_agent('equity_agent')
result = equity.analyze_stock('AAPL')
```

**After (Direct):**
```python
analyst = runtime.get_agent('financial_analyst')
result = analyst.analyze_company({'symbol': 'AAPL'})
```

**After (Pattern-Driven - Recommended):**
```python
result = pattern_engine.execute_pattern('company_analysis', {
    'symbol': 'AAPL'
})
```

## macro_agent → macro_analysis pattern

**Before:**
```python
macro = runtime.get_agent('macro_agent')
result = macro.analyze_economy()
```

**After:**
```python
result = pattern_engine.execute_pattern('macro_analysis', {
    'indicators': ['GDP', 'UNRATE', 'CPI']
})
```

## risk_agent → risk_assessment pattern

**Before:**
```python
risk = runtime.get_agent('risk_agent')
result = risk.assess_risk('AAPL')
```

**After:**
```python
result = pattern_engine.execute_pattern('risk_assessment', {
    'symbol': 'AAPL'
})
```
```

---

## EXECUTION CHECKLIST

### Pre-Flight Checks
- [ ] Backup current codebase: `git commit -am "Pre-consolidation backup"`
- [ ] Create feature branch: `git checkout -b agent-consolidation`
- [ ] Document current test results as baseline

### Phase 1: Code Remediation
- [ ] Fix PatternEngine equity_agent reference (Task 1.1)
- [ ] Update test mocks (Task 1.2)
- [ ] Test changes locally
- [ ] Commit: "Fix legacy agent references in PatternEngine"

### Phase 2: Archive Management
- [ ] Create archive/ directory structure (Task 2.1)
- [ ] Move legacy agents from backups
- [ ] Move archived orchestrators
- [ ] Create archive README (Task 2.2)
- [ ] Delete old dawsos/archived_legacy/
- [ ] Commit: "Consolidate legacy code into archive/"

### Phase 3: Examples & Docs
- [ ] Update example scripts (Task 3.1)
- [ ] Create agent-pattern mapping doc (Task 3.2)
- [ ] Commit: "Update examples to use Trinity agents"

### Phase 4: Verification
- [ ] Run grep for remaining legacy refs (Task 4.1)
- [ ] Fix any found references
- [ ] Run full test suite (Task 4.2)
- [ ] Run smoke test (Task 4.3)
- [ ] Commit: "Verify agent consolidation complete"

### Phase 5: Documentation
- [ ] Update Trinity architecture docs (Task 5.1)
- [ ] Create migration guide (Task 5.2)
- [ ] Update README if needed
- [ ] Commit: "Add agent consolidation documentation"

### Final Steps
- [ ] Merge to main: `git checkout main && git merge agent-consolidation`
- [ ] Tag release: `git tag v2.0-agent-consolidation`
- [ ] Push: `git push origin main --tags`
- [ ] Test production deployment
- [ ] Monitor for issues

---

## RISK ASSESSMENT

### Low Risk
- Archive management (Phase 2) - Just moving files
- Documentation (Phase 5) - No code changes

### Medium Risk
- Example updates (Phase 3) - May break demo scripts
- Test updates (Task 1.2) - May require test rewrites

### High Risk
- PatternEngine fix (Task 1.1) - Used in production moat analysis
  - **Mitigation:** Thoroughly test moat_analyzer pattern before/after
  - **Rollback:** Keep equity_agent logic as fallback temporarily

### Critical Success Factors
1. **No runtime errors** - System must start and run
2. **Pattern functionality preserved** - All 45 patterns still work
3. **No import errors** - No references to unregistered agents
4. **Tests pass** - Full test suite green

---

## ESTIMATED EFFORT

- Phase 1: 2-3 hours (careful code changes)
- Phase 2: 1 hour (file moving + README)
- Phase 3: 2 hours (example updates)
- Phase 4: 2-3 hours (testing + fixes)
- Phase 5: 1-2 hours (documentation)

**Total: 8-11 hours** (1-2 work days)

---

## SUCCESS CRITERIA

✅ **Code Quality**
- Zero references to equity_agent, macro_agent, risk_agent in active code
- All imports resolve successfully
- No dead code paths in PatternEngine

✅ **Functionality**
- All 45 patterns execute successfully
- Moat analysis works (uses financial_analyst)
- All 15 agents registered and callable

✅ **Testing**
- Full test suite passes
- No errors in smoke test
- Integration tests use real agents

✅ **Documentation**
- Archive explains what's there and why
- Migration guide helps users update code
- Trinity docs reflect current architecture

✅ **Production Readiness**
- Application starts without errors
- No warnings about missing agents
- Performance unchanged or improved
