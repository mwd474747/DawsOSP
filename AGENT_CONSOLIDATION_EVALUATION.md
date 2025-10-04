# Agent Consolidation Plan - Execution Evaluation
**Date:** 2025-10-04
**Branch:** `agent-consolidation`
**Status:** Phase 1-2 Complete, Phases 3-6 Remaining

---

## Executive Summary

**Completed:** Critical production code fixes and archive creation (Phases 1-2)
**Remaining:** Prompts, documentation, old archive cleanup, testing, guardrails (Phases 3-6)

**Impact So Far:**
- ✅ Zero legacy agent calls in production runtime code
- ✅ Clean archive with migration documentation
- ✅ No accidental import risk from new `/archive` location

**Remaining Work:** Non-critical cleanup (prompts, docs, old archive, tests)

---

## What Has Been Done (Phases 1-2) ✅

### ✅ Phase 1: Code Remediation (COMPLETE)

#### Task 1.1: Fixed PatternEngine equity_agent Reference
**File:** `dawsos/core/pattern_engine.py:1579-1606`

**Before:**
```python
equity_agent = self._get_agent('equity_agent') if self.runtime else None
if equity_agent:
    stock_analysis = equity_agent.analyze_stock(symbol)
    # ...extract moat insights
```

**After:**
```python
# Note: Previously called equity_agent (removed in agent consolidation)
# Moat analysis now uses knowledge base templates with pattern-driven approach
sector = context.get('sector', '').lower() if context else ''
if sector:
    moat_templates = self._get_moat_templates_from_knowledge(sector)
    # ...use templates directly
```

**Impact:** Removed dead code path (equity_agent was never registered anyway)

---

#### Task 1.2: Updated Test Mocks
**File:** `dawsos/tests/test_compliance.py:490-493`

**Change:** Added documentation comment
```python
# Note: macro_agent is legacy (removed in agent consolidation)
# Keeping mock registration here for backward-compatible testing
# In production, use financial_analyst with macro_analysis pattern instead
self.registry.register('macro_agent', MockAgent('macro_agent'))
```

**Impact:** Test still passes, now documented as intentional mock

---

### ✅ Phase 2: Archive Management (COMPLETE)

#### Task 2.1: Created Clean Archive Structure
**Location:** `/archive` (outside package namespace)

```
archive/
├── README.md (comprehensive migration guide)
├── agents/
│   ├── equity_agent.py (from backups)
│   ├── macro_agent.py (from backups)
│   └── risk_agent.py (from backups)
└── orchestrators/
    ├── claude_orchestrator.py (from dawsos/archived_legacy/)
    └── orchestrator.py (from dawsos/archived_legacy/)
```

**Actions Taken:**
- Copied 3 legacy agents from `dawsos/storage/backups/.../agents/`
- Moved 2 orchestrators from `dawsos/archived_legacy/`
- Deleted `dawsos/archived_legacy/` directory
- Created comprehensive README with migration examples

**Benefits:**
- Outside `dawsos/` package → no accidental imports
- Preserved for historical reference
- Documented replacements with code examples

---

#### Task 2.2: Created Archive Documentation
**File:** `archive/README.md`

**Contents:**
- Replacement mappings (equity→financial_analyst, etc.)
- Migration code examples (old vs new usage)
- 15 active agents table
- Links to additional migration docs

**Example from README:**
```python
# Old: equity_agent
equity = runtime.get_agent('equity_agent')
result = equity.analyze_stock('AAPL')

# New: financial_analyst with pattern
result = pattern_engine.execute_pattern('company_analysis', {'symbol': 'AAPL'})
```

---

## What Remains (Phases 3-6) ⚠️

### ⚠️ **NEW PHASE 3: Prompt & Pattern Alignment** (HIGH PRIORITY)

Based on system reminder, these critical touchpoints were found:

#### Task 3.1: Clean Legacy Agent Prompts ⚠️ **CRITICAL**
**File:** `dawsos/prompts/agent_prompts.json`

**Issue:** File contains prompt definitions for 4 legacy agents:
- `macro_agent`
- `equity_agent`
- `risk_agent`
- `pattern_agent`

**Action Required:**
```bash
# Remove legacy agent prompt entries
# Map their functionality to active agents:
#   macro_agent → financial_analyst
#   equity_agent → financial_analyst
#   risk_agent → financial_analyst + governance_agent
#   pattern_agent → pattern_spotter
```

**Risk:** Medium
- If patterns reference these prompt keys, they may fail
- Need to search patterns for references first

**Estimated Time:** 1-2 hours

---

#### Task 3.2: Check Pattern References to Legacy Prompts
**Action Required:**
```bash
# Search all pattern files for legacy agent references
grep -r "macro_agent\|equity_agent\|risk_agent\|pattern_agent" dawsos/patterns/ --include="*.json"

# Update any found references to use active agents
```

**Risk:** Medium - May break patterns if they depend on legacy prompts

**Estimated Time:** 1 hour

---

### ⚠️ **NEW PHASE 4: Old Archive Cleanup** (MEDIUM PRIORITY)

#### Task 4.1: Handle dawsos/archive/unused_agents/
**Location:** `dawsos/archive/unused_agents/`

**Issue:** Old archive still exists inside package namespace
- Contains: equity_agent.py, macro_agent.py, risk_agent.py, pattern_agent.py
- Plus: crypto.py, fundamentals.py
- **Risk:** Can be accidentally imported (inside dawsos/ package)

**Action Required:**
```bash
# Option A: Delete (already archived in /archive)
rm -rf dawsos/archive/

# Option B: Move to new archive
mv dawsos/archive/unused_agents/* /archive/agents/
rm -rf dawsos/archive/
```

**Recommendation:** Delete (already have clean copies in `/archive`)

**Estimated Time:** 15 minutes

---

### ⚠️ **NEW PHASE 5: Documentation Refresh** (HIGH PRIORITY)

#### Task 5.1: Update SYSTEM_STATUS.md
**File:** `SYSTEM_STATUS.md`

**Issue:** References "19 agents" (should be 15)

**Found References:**
```
- ✅ All 19 agents registered with capability metadata
# Output: 19 agents registered
# Output: 19 agents in both ✅
```

**Action Required:**
- Global replace: `19 agents` → `15 agents`
- Add note about 4 agents archived (equity, macro, risk, pattern)
- Update agent count validations

**Estimated Time:** 30 minutes

---

#### Task 5.2: Update FINAL_ROADMAP_COMPLIANCE.md
**File:** `FINAL_ROADMAP_COMPLIANCE.md`

**Issue:** References "19 agents"

**Found References:**
```
- ✅ All 19 agents have comprehensive capability metadata
```

**Action Required:**
- Update to 15 agents
- Add appendix listing archived components
- Document consolidation rationale

**Estimated Time:** 30 minutes

---

#### Task 5.3: Create Agent Consolidation Appendix
**New File:** `docs/AGENT_CONSOLIDATION_HISTORY.md`

**Purpose:** Historical record of what was consolidated and why

**Contents:**
```markdown
# Agent Consolidation History

## October 2025: 19 → 15 Agents

### Removed Agents
1. equity_agent → financial_analyst
2. macro_agent → financial_analyst (via patterns)
3. risk_agent → financial_analyst + governance_agent
4. pattern_agent → pattern_spotter

### Rationale
- Reduce complexity (fewer agents to maintain)
- Trinity alignment (pattern-driven routing)
- Eliminate code duplication
- Clearer agent responsibilities

### Functionality Preserved
All functionality preserved via:
- Pattern-driven execution
- Capability consolidation
- Knowledge base patterns
```

**Estimated Time:** 1 hour

---

### ⚠️ **NEW PHASE 6: Testing & CI Guardrails** (CRITICAL)

#### Task 6.1: Create Agent Registry Validation Test
**New File:** `dawsos/tests/validation/test_agent_registry_consistency.py`

**Purpose:** Ensure no rogue agent names creep back in

**Test Cases:**
```python
def test_agent_capabilities_match_registration():
    """Verify AGENT_CAPABILITIES keys match registered agents"""
    from main import AGENT_CAPABILITIES
    from core.agent_runtime import AgentRuntime

    runtime = AgentRuntime()
    # ... register agents

    cap_keys = set(AGENT_CAPABILITIES.keys())
    registered = set(runtime._agents.keys())

    # Should be exactly equal (no extras, no missing)
    assert cap_keys == registered

def test_no_legacy_agents_in_prompts():
    """Verify agent_prompts.json has no legacy agents"""
    import json
    with open('dawsos/prompts/agent_prompts.json') as f:
        prompts = json.load(f)

    legacy_agents = ['equity_agent', 'macro_agent', 'risk_agent', 'pattern_agent']
    prompt_keys = set(prompts.keys())

    for legacy in legacy_agents:
        assert legacy not in prompt_keys, f"Legacy agent {legacy} found in prompts"

def test_no_legacy_agents_in_patterns():
    """Verify no patterns reference legacy agents"""
    import json
    from pathlib import Path

    legacy_agents = ['equity_agent', 'macro_agent', 'risk_agent', 'pattern_agent']

    for pattern_file in Path('dawsos/patterns').rglob('*.json'):
        with open(pattern_file) as f:
            pattern = json.load(f)

        # Check steps for agent references
        for step in pattern.get('steps', []):
            agent = step.get('agent')
            assert agent not in legacy_agents, \
                f"Pattern {pattern_file} references legacy agent {agent}"
```

**Estimated Time:** 2 hours

---

#### Task 6.2: Create Pre-Commit Hook (Optional)
**File:** `.git/hooks/pre-commit`

**Purpose:** Flag legacy agent references before commit

```bash
#!/bin/bash
# Check for legacy agent references

LEGACY_PATTERNS="equity_agent|macro_agent|risk_agent|pattern_agent"

# Check Python files (excluding tests and archive)
if git diff --cached --name-only | grep -E '\.py$' | grep -v test | grep -v archive | xargs grep -l "$LEGACY_PATTERNS" 2>/dev/null; then
    echo "❌ ERROR: Legacy agent reference found in staged files"
    echo "Allowed only in: tests, examples, archive"
    exit 1
fi

# Check JSON files
if git diff --cached --name-only | grep -E '\.json$' | xargs grep -l "$LEGACY_PATTERNS" 2>/dev/null; then
    echo "⚠️  WARNING: Legacy agent reference found in JSON files"
    echo "Review: patterns, prompts, configs"
    # Don't exit - just warn
fi

exit 0
```

**Estimated Time:** 1 hour

---

## Updated Phase Plan (Prioritized)

### **Phase 3: Prompt & Pattern Cleanup** (2-3 hours) - HIGH PRIORITY
- [ ] Task 3.1: Remove legacy agents from agent_prompts.json
- [ ] Task 3.2: Search and update pattern references
- [ ] Commit: "Remove legacy agent prompts"

### **Phase 4: Old Archive Cleanup** (15 min) - MEDIUM PRIORITY
- [ ] Task 4.1: Delete or move dawsos/archive/unused_agents/
- [ ] Commit: "Remove old archive from package namespace"

### **Phase 5: Documentation Refresh** (2 hours) - HIGH PRIORITY
- [ ] Task 5.1: Update SYSTEM_STATUS.md to 15 agents
- [ ] Task 5.2: Update FINAL_ROADMAP_COMPLIANCE.md
- [ ] Task 5.3: Create agent consolidation history doc
- [ ] Commit: "Update documentation for 15-agent model"

### **Phase 6: Testing & Guardrails** (3 hours) - CRITICAL
- [ ] Task 6.1: Create agent registry validation tests
- [ ] Task 6.2: Create pre-commit hook (optional)
- [ ] Task 6.3: Run full test suite
- [ ] Commit: "Add agent registry validation tests"

### **Phase 7: Final Verification & Merge** (1 hour)
- [ ] Run all tests
- [ ] Verify zero legacy references (grep)
- [ ] Test application startup
- [ ] Merge to main
- [ ] Tag release: `v2.0-agent-consolidation`

---

## Total Remaining Effort

**Already Complete (Phases 1-2):** 3 hours
**Remaining (Phases 3-7):** ~9 hours

**Total Project:** ~12 hours (1.5 days)

---

## Risk Assessment Update

### ✅ Risks Mitigated (Phases 1-2)
- ✅ Production runtime errors (equity_agent fixed)
- ✅ Accidental imports (archive moved outside package)

### ⚠️ Remaining Risks

**HIGH:**
- **Prompt file cleanup** - May break patterns if they use legacy prompts
- **Old archive in package** - Can still be imported (inside dawsos/)
- **Doc inconsistency** - New contributors see wrong agent count

**MEDIUM:**
- **Pattern references** - Some patterns may expect legacy agents
- **Test coverage** - No validation tests yet for agent consistency

**LOW:**
- **Example scripts** - Already identified, low impact (demos only)

---

## Recommendations

### Immediate (Next Session)
1. **Execute Phase 3** (Prompt cleanup) - Highest risk remaining
2. **Execute Phase 4** (Delete old archive) - Quick win, removes import risk
3. **Execute Phase 5** (Doc updates) - Important for team alignment

### Short Term (This Week)
4. **Execute Phase 6** (Tests & guardrails) - Prevents regression
5. **Execute Phase 7** (Merge) - Complete consolidation

### Optional (Future)
- Update example scripts (low priority - already documented as legacy)
- Create migration guide for external users
- Add agent architecture diagrams

---

## Success Criteria (Updated)

### ✅ Phase 1-2 Complete
- [x] Zero legacy agent calls in production code
- [x] Archive created outside package namespace
- [x] Archive documented with migration examples

### ⏳ Phase 3-7 Pending
- [ ] Zero legacy agent prompts
- [ ] Zero pattern references to legacy agents
- [ ] Old archive removed from package
- [ ] Documentation reflects 15 agents
- [ ] Validation tests prevent regression
- [ ] Full test suite passes
- [ ] Application starts without errors

---

**Current Branch:** `agent-consolidation` (2 commits)
**Next Action:** Execute Phase 3 (Prompt & Pattern Cleanup)
