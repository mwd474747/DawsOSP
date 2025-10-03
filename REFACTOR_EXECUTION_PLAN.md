# DawsOS Refactor Execution Plan

**Version**: 1.0
**Target**: Trinity 2.0 Completion (A+ → A++)
**Created**: October 3, 2025
**Estimated Duration**: 3-5 days

---

## Executive Summary

This plan executes the remaining technical debt cleanup to achieve full Trinity 2.0 compliance. Work is organized into **8 phases** with **4 specialist agents** coordinating parallel execution where possible.

**Current Grade**: A+ (98/100)
**Target Grade**: A++ (100/100)
**Risk Level**: Low (non-breaking improvements, comprehensive validation)

---

## Specialist Agent Responsibilities

### 🏛️ Trinity Architect
**Leads**: Phases 2, 5, 8 (enforcement, testing, final validation)
**Focus**: Registry bypass elimination, strict mode enforcement, architectural purity

### 🎯 Pattern Specialist
**Leads**: Phase 3 (capability routing in patterns)
**Focus**: Pattern migration from name-based to capability-based routing

### 📚 Knowledge Curator
**Leads**: Phase 4 (knowledge loader completion)
**Focus**: Dataset _meta headers, refresh scripts, loader validators

### 🤖 Agent Orchestrator
**Leads**: Phase 1 (documentation), partial Phase 2
**Focus**: Agent development guides, capability registration consistency

---

## Phase Dependency Graph

```
Phase 1 (Documentation) ────┐
                             ├─→ Phase 2 (Trinity Enforcement) ──→ Phase 5 (Testing & CI)
Phase 4 (Knowledge Loader) ──┘                                      ↓
                                                                Phase 8 (Final Validation)
Phase 3 (Capability Routing) ────────────────────────────────┘      ↑
                                                                     │
Phase 6 (Cleanup) ──→ Phase 7 (UI/Prompts) ─────────────────────────┘
```

**Parallel Execution Opportunities**:
- Phase 1 & 4 can run concurrently (independent)
- Phase 3 can start once Phase 2 identifies patterns to migrate
- Phase 6 & 7 can run concurrently (independent)

---

## Phase 1: Documentation Set (Agent Orchestrator + Knowledge Curator)

**Duration**: 4-6 hours
**Risk**: None (documentation only)
**Parallelizable**: Yes (3 independent docs)

### Tasks

#### 1.1 Create AgentDevelopmentGuide.md
**Owner**: Agent Orchestrator
**Location**: `docs/AgentDevelopmentGuide.md`
**Content**:
- Agent interface requirements (process, think, analyze methods)
- Registration with AGENT_CAPABILITIES metadata
- AgentAdapter behavior (normalization, graph storage)
- exec_via_registry vs execute_by_capability patterns
- Testing requirements (smoke tests, integration tests)
- Example: Creating a new sentiment_analyzer agent

**Validation**:
```bash
# Document includes all 19 agent registration examples
grep -c "register_agent" docs/AgentDevelopmentGuide.md  # Should be 19+
```

#### 1.2 Create KnowledgeMaintenance.md
**Owner**: Knowledge Curator
**Location**: `docs/KnowledgeMaintenance.md`
**Content**:
- Dataset _meta header format (version, last_updated, source, as_of)
- All 26 datasets with refresh cadence (daily, weekly, monthly, static)
- KnowledgeLoader usage patterns (cache TTL, validators, stale detection)
- Dataset update workflow (edit → validate → clear_cache → reload_all)
- Refresh script usage: `scripts/update_enriched_data.py`

**Validation**:
```bash
# Document covers all 26 datasets
grep -c "\.json" docs/KnowledgeMaintenance.md  # Should be 26+
```

#### 1.3 Create DisasterRecovery.md
**Owner**: Knowledge Curator
**Location**: `docs/DisasterRecovery.md`
**Content**:
- Backup rotation (30-day retention in storage/backups/)
- Checksum verification (storage/checksums.json)
- .meta file structure (timestamp, size, checksum)
- Restore procedures (load backup, verify checksums, validate graph)
- Decisions file rotation (5MB threshold)
- Testing backup/restore flow

**Validation**:
```bash
# Document includes restore command examples
grep -c "restore" docs/DisasterRecovery.md  # Should be 10+
```

#### 1.4 Update README.md
**Owner**: Trinity Architect
**Content**:
- Add "Developer Guides" section linking to 3 new docs
- Update "System Status" to reference SYSTEM_STATUS.md
- Move detailed roadmap to docs/reports/

**Validation**:
```bash
# Verify links work
grep -o '\[.*\](.*.md)' README.md | wc -l  # Should include 3 new docs
```

### Deliverables
- ✅ docs/AgentDevelopmentGuide.md (2-3 pages)
- ✅ docs/KnowledgeMaintenance.md (2-3 pages)
- ✅ docs/DisasterRecovery.md (1-2 pages)
- ✅ README.md updated with links

### Error Prevention
- Use existing docs (CAPABILITY_ROUTING_GUIDE.md) as templates
- Reference specialist agent files for accuracy
- Validate all file paths and commands work

---

## Phase 2: Trinity Access Enforcement (Trinity Architect)

**Duration**: 6-8 hours
**Risk**: Medium (requires code changes, test updates)
**Parallelizable**: Partially (scan → convert → validate can overlap)

### Tasks

#### 2.1 Scan for runtime.agents Usage
**Owner**: Trinity Architect
**Command**:
```bash
grep -r "runtime\.agents\[" dawsos/ --include="*.py" > /tmp/bypass_scan.txt
grep -r "\.agents\[" dawsos/tests/ --include="*.py" >> /tmp/bypass_scan.txt
grep -r "st\.session_state\.agent_runtime\.agents" dawsos/ui/ --include="*.py" >> /tmp/bypass_scan.txt
```

**Expected Locations**:
- `dawsos/ui/governance_tab.py` (agent listing UI)
- `dawsos/tests/validation/*.py` (test setup)
- `dawsos/ui/trinity_ui_components.py` (agent display)

**Validation**: Document all occurrences with line numbers

#### 2.2 Convert UI Components
**Owner**: Trinity Architect
**Files**:
- `dawsos/ui/governance_tab.py`
- `dawsos/ui/trinity_ui_components.py`
- `dawsos/ui/trinity_dashboard_tabs.py`

**Pattern**:
```python
# ❌ Before
agents = runtime.agents
for name, agent in agents.items():
    result = agent.process(context)

# ✅ After
agent_names = runtime.agent_registry.list_agents()
for name in agent_names:
    result = runtime.exec_via_registry(name, context)
```

**Validation**:
```bash
grep -c "runtime\.agents\[" dawsos/ui/*.py  # Should be 0
```

#### 2.3 Convert Tests
**Owner**: Trinity Architect
**Files**:
- `dawsos/tests/validation/test_trinity_smoke.py`
- `dawsos/tests/validation/test_integration.py`
- `dawsos/tests/validation/test_full_system.py`

**Pattern**:
```python
# ❌ Before
agent = runtime.agents['claude']
assert agent is not None

# ✅ After
assert runtime.has_agent('claude')
# For actual execution:
result = runtime.exec_via_registry('claude', context)
```

**Validation**:
```bash
pytest dawsos/tests/validation/ -v  # All tests pass
```

#### 2.4 Update Pattern Linter
**Owner**: Pattern Specialist
**File**: `scripts/lint_patterns.py`

**Add Check**:
```python
def check_trinity_compliance(pattern):
    """Ensure patterns use execute_through_registry"""
    for step in pattern.get('steps', []):
        if 'agent' in step and 'action' not in step:
            warnings.append(f"Pattern {pattern['id']}: Step uses 'agent' key without 'action: execute_through_registry'")
```

**Validation**:
```bash
python scripts/lint_patterns.py  # Should catch non-compliant patterns
```

#### 2.5 Enable Strict Mode
**Owner**: Trinity Architect
**File**: `dawsos/core/agent_runtime.py`

**Changes**:
```python
# Add strict mode enforcement
TRINITY_STRICT_MODE = os.getenv('TRINITY_STRICT_MODE', 'false').lower() == 'true'

@property
def agents(self):
    if TRINITY_STRICT_MODE:
        raise RuntimeError(
            "Direct agent access blocked in strict mode. "
            "Use exec_via_registry() or execute_by_capability() instead."
        )
    return MappingProxyType(self._agents)
```

**Validation**:
```bash
TRINITY_STRICT_MODE=true pytest dawsos/tests/validation/  # Should pass
```

#### 2.6 Add Strict Mode Test
**Owner**: Trinity Architect
**File**: `dawsos/tests/validation/test_strict_mode.py`

**Content**:
```python
def test_strict_mode_blocks_direct_access():
    """Verify strict mode raises on runtime.agents access"""
    os.environ['TRINITY_STRICT_MODE'] = 'true'
    runtime = AgentRuntime(graph, pattern_engine)

    with pytest.raises(RuntimeError, match="Direct agent access blocked"):
        _ = runtime.agents['claude']
```

**Validation**:
```bash
pytest dawsos/tests/validation/test_strict_mode.py -v
```

### Deliverables
- ✅ All `runtime.agents[]` usage converted to `exec_via_registry()`
- ✅ Pattern linter enforces Trinity compliance
- ✅ Strict mode implemented with env var
- ✅ Regression test for strict mode
- ✅ All existing tests pass with strict mode enabled

### Error Prevention
- Run tests after each file conversion (incremental validation)
- Keep git commits small (one file or logical group per commit)
- Test UI manually after governance_tab changes
- Document any intentional exceptions (if needed for tooling)

---

## Phase 3: Capability Routing Migration (Pattern Specialist)

**Duration**: 4-6 hours
**Risk**: Low (patterns have fallback to name-based routing)
**Parallelizable**: Yes (patterns independent)

### Tasks

#### 3.1 Identify High-Value Patterns
**Owner**: Pattern Specialist
**Criteria**: Patterns used frequently or with swappable agents

**Target Patterns** (8-10):
- `analysis/sector_rotation_strategy.json` (equity_agent → can_analyze_sector_rotation)
- `analysis/risk_assessment.json` (risk_agent → can_assess_portfolio_risk)
- `governance/compliance_audit.json` (governance_agent → can_audit_compliance)
- `queries/market_regime_query.json` (macro_agent → can_identify_market_regime)
- `queries/company_analysis_query.json` (equity_agent → can_analyze_stock)
- `workflows/portfolio_review.json` (multiple agents → capabilities)
- `workflows/morning_briefing.json` (multiple agents → capabilities)
- `ui/dashboard_update.json` (multiple agents → capabilities)

**Validation**: List patterns with agent dependency count

#### 3.2 Add Capability Action Support
**Owner**: Pattern Specialist
**File**: `dawsos/core/pattern_engine.py`

**Add Action**:
```python
def execute_action(self, action, params, context, outputs):
    # ... existing actions ...

    if action == 'execute_by_capability':
        capability = params.get('capability')
        agent_context = params.get('context', context)
        return self.runtime.execute_by_capability(capability, agent_context)
```

**Validation**:
```python
# Test pattern can use capability routing
pattern = {
    "steps": [{
        "action": "execute_by_capability",
        "params": {"capability": "can_calculate_dcf"},
        "outputs": ["valuation"]
    }]
}
```

#### 3.3 Migrate Patterns
**Owner**: Pattern Specialist
**Process per pattern**:

1. **Identify agent → capability mapping**:
```python
# From AGENT_CAPABILITIES
'financial_analyst': ['can_calculate_dcf', 'can_calculate_roic', ...]
```

2. **Update pattern structure**:
```json
{
  "steps": [
    {
      "action": "execute_by_capability",
      "params": {
        "capability": "can_calculate_dcf",
        "context": {
          "symbol": "{SYMBOL}",
          "data": "{financials}"
        }
      },
      "outputs": ["valuation"],
      "fallback_agent": "financial_analyst"
    }
  ]
}
```

3. **Test pattern execution**:
```bash
# Integration test for each pattern
pytest dawsos/tests/validation/test_pattern_capability_routing.py::test_sector_rotation
```

#### 3.4 Update Pattern Documentation
**Owner**: Pattern Specialist
**File**: `.claude/pattern_specialist.md`

**Add Section**:
```markdown
### Capability-Based Pattern Actions (Trinity 2.0)

**Recommended Action**: `execute_by_capability`
- More flexible than hard-coded agent names
- Allows agent swapping without pattern changes
- Graceful fallback if capability unavailable
```

**Validation**: Documentation matches implementation

#### 3.5 Dashboard Capability Metrics
**Owner**: Agent Orchestrator
**File**: `dawsos/ui/governance_tab.py`

**Add UI Section**:
```python
def show_capability_coverage():
    """Display which capabilities are used in patterns"""
    st.subheader("📊 Capability Usage")

    capabilities = runtime.agent_registry.list_all_capabilities()
    patterns = pattern_engine.get_all_patterns()

    used_capabilities = set()
    for pattern in patterns:
        for step in pattern.get('steps', []):
            if step.get('action') == 'execute_by_capability':
                used_capabilities.add(step['params']['capability'])

    st.metric("Capabilities Registered", len(capabilities))
    st.metric("Capabilities Used in Patterns", len(used_capabilities))
    st.metric("Coverage", f"{len(used_capabilities)/len(capabilities)*100:.1f}%")
```

**Validation**: UI displays metrics correctly

### Deliverables
- ✅ 8-10 high-value patterns migrated to capability routing
- ✅ Pattern engine supports `execute_by_capability` action
- ✅ Capability coverage visible in governance dashboard
- ✅ Pattern documentation updated
- ✅ All migrated patterns tested

### Error Prevention
- Keep `fallback_agent` for backwards compatibility
- Test each pattern individually before bulk migration
- Verify AGENT_CAPABILITIES mapping is correct
- Document migration in pattern version field

---

## Phase 4: Knowledge Loader Completion (Knowledge Curator)

**Duration**: 6-8 hours
**Risk**: Low (additive changes, no breaking modifications)
**Parallelizable**: Yes (dataset work independent)

### Tasks

#### 4.1 Audit Dataset _meta Coverage
**Owner**: Knowledge Curator
**Command**:
```bash
cd dawsos/storage/knowledge
for file in *.json; do
  if ! grep -q '"_meta"' "$file"; then
    echo "Missing _meta: $file"
  fi
done
```

**Expected Gaps** (~10-12 files without _meta):
- Investment framework files (buffett_checklist, dalio_framework)
- Factor/alt data files (factor_smartbeta, insider_institutional)
- Market indicator files (fx_commodities, thematic_momentum)

**Validation**: List all files missing _meta headers

#### 4.2 Add _meta Headers
**Owner**: Knowledge Curator
**Template**:
```json
{
  "_meta": {
    "version": "1.0",
    "last_updated": "2025-10-03T00:00:00Z",
    "source": "manual_curation",
    "as_of": "2025-10-02",
    "refresh_cadence": "monthly",
    "description": "Buffett investment checklist criteria"
  },
  "data": {
    ...existing content...
  }
}
```

**Refresh Cadence Standards**:
- **Daily**: cross_asset_lead_lag, fx_commodities, volatility_stress
- **Weekly**: earnings_surprises, dividend_buyback, insider_institutional
- **Monthly**: economic_cycles, econ_regime_watchlist, thematic_momentum
- **Quarterly**: sector_performance, sector_correlations, factor_smartbeta
- **Static**: buffett_framework, dalio_framework, financial_calculations, agent_capabilities

**Validation**:
```bash
# All 26 datasets have _meta
grep -l '"_meta"' dawsos/storage/knowledge/*.json | wc -l  # Should be 26
```

#### 4.3 Add Dataset Validators
**Owner**: Knowledge Curator
**File**: `dawsos/core/knowledge_loader.py`

**Add Method**:
```python
def validate_dataset(self, dataset_name: str, data: Dict) -> bool:
    """Validate dataset structure and _meta requirements"""
    # Check _meta exists
    if '_meta' not in data:
        self.logger.warning(f"Dataset {dataset_name} missing _meta header")
        return False

    meta = data['_meta']
    required_fields = ['version', 'last_updated', 'source']
    for field in required_fields:
        if field not in meta:
            self.logger.warning(f"Dataset {dataset_name} missing _meta.{field}")
            return False

    # Check as_of is recent (if refresh_cadence specified)
    if 'as_of' in meta and 'refresh_cadence' in meta:
        as_of = datetime.fromisoformat(meta['as_of'])
        age_days = (datetime.now() - as_of).days

        cadence_limits = {
            'daily': 2,
            'weekly': 8,
            'monthly': 32,
            'quarterly': 95
        }

        limit = cadence_limits.get(meta['refresh_cadence'])
        if limit and age_days > limit:
            self.logger.warning(
                f"Dataset {dataset_name} stale: {age_days} days old "
                f"(cadence: {meta['refresh_cadence']})"
            )

    return True
```

**Validation**:
```python
# Test validator catches missing fields
loader = KnowledgeLoader()
loader.validate_dataset('test', {'data': 'test'})  # Should log warning
```

#### 4.4 Create Refresh Script
**Owner**: Knowledge Curator
**File**: `scripts/update_enriched_data.py`

**Content**:
```python
#!/usr/bin/env python3
"""Update enriched datasets based on refresh cadence"""

import json
from pathlib import Path
from datetime import datetime
from core.knowledge_loader import KnowledgeLoader

def check_stale_datasets():
    """Identify datasets needing refresh"""
    loader = KnowledgeLoader()
    stale = []

    for name, filepath in loader.datasets.items():
        data = loader.get_dataset(name)
        if not data or '_meta' not in data:
            continue

        meta = data['_meta']
        if 'as_of' in meta and 'refresh_cadence' in meta:
            as_of = datetime.fromisoformat(meta['as_of'])
            age_days = (datetime.now() - as_of).days

            cadence_limits = {
                'daily': 2, 'weekly': 8,
                'monthly': 32, 'quarterly': 95
            }

            limit = cadence_limits.get(meta['refresh_cadence'])
            if limit and age_days > limit:
                stale.append({
                    'name': name,
                    'age_days': age_days,
                    'cadence': meta['refresh_cadence'],
                    'as_of': meta['as_of']
                })

    return stale

def main():
    stale = check_stale_datasets()

    if not stale:
        print("✅ All datasets current")
        return

    print(f"⚠️  {len(stale)} datasets need refresh:")
    for dataset in stale:
        print(f"  - {dataset['name']}: {dataset['age_days']} days old "
              f"(cadence: {dataset['cadence']})")

    print("\nTo update, edit files in dawsos/storage/knowledge/")
    print("Then run: loader.clear_cache(name); loader.reload_all()")

if __name__ == '__main__':
    main()
```

**Validation**:
```bash
chmod +x scripts/update_enriched_data.py
python scripts/update_enriched_data.py  # Should list stale datasets
```

#### 4.5 Update KnowledgeMaintenance.md
**Owner**: Knowledge Curator
**Add Sections**:
- Dataset refresh workflow
- Running update_enriched_data.py
- Manual update process
- Cache invalidation

**Validation**: Documentation matches script behavior

### Deliverables
- ✅ All 26 datasets have _meta headers
- ✅ KnowledgeLoader validates _meta on load
- ✅ scripts/update_enriched_data.py identifies stale datasets
- ✅ KnowledgeMaintenance.md documents refresh workflow
- ✅ Warnings emitted for stale datasets

### Error Prevention
- Backup storage/knowledge/ before adding _meta headers
- Validate JSON after each _meta addition
- Test loader with and without _meta to ensure backwards compat
- Document refresh_cadence values in KnowledgeMaintenance.md

---

## Phase 5: Testing & CI Integration (Trinity Architect)

**Duration**: 4-6 hours
**Risk**: Low (test improvements, no production changes)
**Parallelizable**: Yes (test conversion independent of CI setup)

### Tasks

#### 5.1 Convert Manual Validation Scripts
**Owner**: Trinity Architect
**Files to Convert**:
- `dawsos/test_system_health.py` → `tests/validation/test_system_health.py`
- Any emoji-based output scripts in root

**Pattern**:
```python
# ❌ Before (manual inspection)
def test_agents():
    print("Testing agents...")
    for name in runtime.agents:
        print(f"✅ {name} registered")

# ✅ After (pytest assertions)
def test_all_agents_registered():
    """Verify all 19 agents are registered"""
    expected_agents = [
        'claude', 'data_harvester', 'data_digester',
        'graph_mind', 'pattern_spotter', 'relationship_hunter',
        # ... all 19
    ]

    for agent_name in expected_agents:
        assert runtime.has_agent(agent_name), \
            f"Agent {agent_name} not registered"
```

**Validation**:
```bash
pytest tests/validation/test_system_health.py -v  # All assertions pass
```

#### 5.2 Add Knowledge Loader Tests
**Owner**: Knowledge Curator
**File**: `tests/validation/test_knowledge_loader.py`

**Tests**:
```python
def test_all_datasets_registered():
    """Verify 26 datasets in loader"""
    loader = KnowledgeLoader()
    assert len(loader.datasets) == 26

def test_all_datasets_have_meta():
    """Verify _meta headers present"""
    loader = KnowledgeLoader()
    for name in loader.datasets:
        data = loader.get_dataset(name)
        assert '_meta' in data, f"Dataset {name} missing _meta"

def test_cache_ttl():
    """Verify 30-min cache behavior"""
    loader = KnowledgeLoader()
    data1 = loader.get_dataset('sector_performance')
    data2 = loader.get_dataset('sector_performance')
    # Second call should be cached (same object)
    assert data1 is data2

def test_stale_detection():
    """Verify stale dataset identification"""
    loader = KnowledgeLoader()
    stale = loader.get_stale_datasets()
    # Should be a list (may be empty if all current)
    assert isinstance(stale, list)
```

**Validation**:
```bash
pytest tests/validation/test_knowledge_loader.py -v
```

#### 5.3 Enhance CI Workflow
**Owner**: Trinity Architect
**File**: `.github/workflows/compliance-check.yml`

**Add Jobs**:
```yaml
name: DawsOS Compliance Check

on: [push, pull_request]

jobs:
  pattern-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Lint Patterns
        run: |
          pip install -r requirements.txt
          python scripts/lint_patterns.py
          # Fail if errors found
          if [ $? -ne 0 ]; then exit 1; fi

  knowledge-loader:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - name: Test Knowledge Loader
        run: |
          pip install -r requirements.txt
          pytest tests/validation/test_knowledge_loader.py -v

  strict-mode:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - name: Test Strict Mode
        env:
          TRINITY_STRICT_MODE: true
        run: |
          pip install -r requirements.txt
          pytest tests/validation/test_strict_mode.py -v

  full-suite:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - name: Run Full Test Suite
        run: |
          pip install -r requirements.txt
          pytest tests/validation/ -v --cov=dawsos/core
```

**Validation**: Push to GitHub and verify all jobs pass

#### 5.4 Add pytest Configuration
**Owner**: Trinity Architect
**File**: `pytest.ini`

**Content**:
```ini
[pytest]
testpaths = tests/validation
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings
markers =
    smoke: Quick smoke tests
    integration: Integration tests
    slow: Slow-running tests
```

**Validation**:
```bash
pytest --collect-only  # Should discover all tests
```

### Deliverables
- ✅ Manual validation scripts converted to pytest
- ✅ Knowledge loader test suite (4+ tests)
- ✅ Strict mode regression test
- ✅ CI workflow runs pattern lint, pytest, strict mode
- ✅ pytest.ini configured
- ✅ All tests passing in CI

### Error Prevention
- Test locally before pushing to CI
- Use `pytest --collect-only` to verify test discovery
- Start with simple assertions, add complexity incrementally
- Mock external dependencies (APIs, file I/O) in unit tests

---

## Phase 6: Repository Cleanup (Trinity Architect)

**Duration**: 2-3 hours
**Risk**: Low (file moves/deletes, no code changes)
**Parallelizable**: Yes (independent cleanup tasks)

### Tasks

#### 6.1 Consolidate Interim Reports
**Owner**: Trinity Architect
**Action**: Move to `docs/reports/archive/`

**Files to Archive**:
```bash
# Identify interim reports
ls -1 *.md | grep -E "(ASSESSMENT|PROGRESS|INTERIM|SNAPSHOT)" > /tmp/to_archive.txt

# Create archive structure
mkdir -p docs/reports/archive/2025-10

# Move files
cat /tmp/to_archive.txt | xargs -I {} mv {} docs/reports/archive/2025-10/
```

**Keep in Root** (essentials only):
- README.md
- CLAUDE.md (persistent context)
- SYSTEM_STATUS.md (current state)
- CAPABILITY_ROUTING_GUIDE.md (reference)
- CORE_INFRASTRUCTURE_STABILIZATION.md (architecture)

**Validation**:
```bash
ls -1 *.md | wc -l  # Should be ≤5
```

#### 6.2 Remove Duplicate Storage Directories
**Owner**: Trinity Architect
**Action**:

1. **Verify `./storage/` is empty or duplicate**:
```bash
ls -la storage/  # Check if empty or mirrors dawsos/storage/
```

2. **Add to .gitignore**:
```gitignore
# Root-level storage (auto-generated)
/storage/
```

3. **Document in README**:
```markdown
## Storage Structure

- `dawsos/storage/` - Persistent application data (committed)
- `./storage/` - Auto-generated at runtime (ignored)
```

**Validation**:
```bash
git status  # storage/ should not show as untracked
```

#### 6.3 Clean Archived Logs
**Owner**: Knowledge Curator
**Action**: Move old logs to `dawsos/logs/archive/`

```bash
cd dawsos/logs
mkdir -p archive/2025-09

# Move logs older than 7 days
find . -name "*.log" -mtime +7 -exec mv {} archive/2025-09/ \;

# Update .gitignore
echo "dawsos/logs/*.log" >> .gitignore
echo "!dawsos/logs/archive/" >> .gitignore
```

**Validation**:
```bash
ls dawsos/logs/*.log  # Only recent logs remain
```

#### 6.4 Archive Legacy Scripts
**Owner**: Agent Orchestrator
**Action**: Move to `archived_legacy/scripts/`

**Files to Consider**:
- Any scripts replaced by pytest tests
- Deprecated validation scripts
- One-off migration tools

```bash
mkdir -p archived_legacy/scripts
# Review and move carefully (verify not used in CI)
```

**Validation**: Run full test suite to ensure no dependencies broken

#### 6.5 Update .gitignore
**Owner**: Trinity Architect
**File**: `.gitignore`

**Add**:
```gitignore
# Storage
/storage/
dawsos/logs/*.log
!dawsos/logs/archive/

# Python
__pycache__/
*.pyc
.pytest_cache/
.coverage

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Temporary
*.tmp
*.bak
*~
```

**Validation**:
```bash
git status  # No unwanted files shown
```

### Deliverables
- ✅ Root markdown files ≤5 (essentials only)
- ✅ Interim reports in docs/reports/archive/
- ✅ Duplicate storage/ ignored
- ✅ Old logs archived
- ✅ Legacy scripts moved to archived_legacy/
- ✅ .gitignore comprehensive

### Error Prevention
- Use `git mv` instead of `mv` for tracked files
- Verify no broken links in README/docs after moves
- Test application startup after cleanup
- Keep one commit per logical group (easier rollback)

---

## Phase 7: UI & Prompt Consistency (Pattern Specialist + Knowledge Curator)

**Duration**: 3-4 hours
**Risk**: Low (UI improvements, no core logic changes)
**Parallelizable**: Yes (UI and prompts independent)

### Tasks

#### 7.1 Replace Remaining pass Statements
**Owner**: Pattern Specialist
**Action**: Grep and replace in UI files

```bash
# Find remaining pass statements
grep -rn "pass$" dawsos/ui/ --include="*.py"

# Pattern to replace:
# pass → logger.warning(f"Not implemented: {functionality}")
```

**Files**:
- `dawsos/ui/governance_tab.py`
- `dawsos/ui/trinity_ui_components.py`

**Example**:
```python
# ❌ Before
except KeyError:
    pass

# ✅ After
except KeyError as e:
    logger.warning(f"Key not found in governance data: {e}")
    st.warning(f"⚠️ Unable to load governance metric: {e}")
```

**Validation**:
```bash
grep -c "pass$" dawsos/ui/*.py  # Should be 0
```

#### 7.2 Update System Prompts
**Owner**: Knowledge Curator
**Files**:
- `dawsos/prompts/system_prompt.txt`
- `dawsos/prompts/graph_prompt.txt`
- Agent-specific prompts in `dawsos/agents/*/prompts/`

**Add to All Prompts**:
```
## DawsOS Trinity Architecture

You are part of the DawsOS Trinity 2.0 system (A+ grade, 98/100).

Execution Flow:
Request → UniversalExecutor → PatternEngine → AgentRegistry → KnowledgeGraph

Key Principles:
- All agent calls go through AgentRegistry (no direct agent access)
- All data loaded via KnowledgeLoader (26 datasets, 30-min cache)
- Results stored in KnowledgeGraph (nodes, edges, patterns)
- Use capability-based routing when possible (50+ capabilities)

Available Resources:
- 26 enriched datasets (sector_performance, economic_cycles, buffett_framework, etc.)
- 45 validated patterns (analysis, ui, governance, queries, workflows)
- 19 agents with AGENT_CAPABILITIES metadata
```

**Validation**: Test agent responses reference Trinity architecture

#### 7.3 Refresh UI Messages
**Owner**: Pattern Specialist
**Action**: Update user-facing messages in UI

**Targets**:
- Success messages reference Trinity compliance
- Error messages suggest correct approach
- Help text references documentation

**Example**:
```python
# Before
st.success("Agent executed successfully")

# After
st.success("✅ Agent executed via registry (Trinity-compliant)")

# Before
st.error("Agent not found")

# After
st.error(
    "❌ Agent not found. "
    "Available agents listed in Governance → Registry tab. "
    "See docs/AgentDevelopmentGuide.md to add new agents."
)
```

**Validation**: Manual UI testing of error paths

#### 7.4 Add Trinity Status Indicator
**Owner**: Agent Orchestrator
**File**: `dawsos/ui/trinity_ui_components.py`

**Add Component**:
```python
def show_trinity_status():
    """Display Trinity compliance status"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏛️ Trinity Status")

    metrics = runtime.get_compliance_metrics()
    compliance_rate = metrics.get('overall_compliance', 0)

    if compliance_rate >= 95:
        icon = "✅"
        color = "green"
    elif compliance_rate >= 80:
        icon = "⚠️"
        color = "orange"
    else:
        icon = "❌"
        color = "red"

    st.sidebar.markdown(
        f"**Compliance**: :{color}[{icon} {compliance_rate:.1f}%]"
    )

    if st.sidebar.button("View Details"):
        st.sidebar.json(metrics)
```

**Validation**: Verify sidebar shows compliance rate

### Deliverables
- ✅ 0 bare `pass` statements in UI
- ✅ All prompts reference Trinity architecture
- ✅ UI messages include helpful guidance
- ✅ Trinity status indicator in sidebar
- ✅ Error messages reference documentation

### Error Prevention
- Test UI after each change (streamlit hot reload)
- Verify logger imports present before using logger
- Keep user messages concise (no walls of text)
- Add links to docs where helpful

---

## Phase 8: Final Validation & Documentation (Trinity Architect)

**Duration**: 2-3 hours
**Risk**: None (validation only)
**Parallelizable**: No (sequential validation)

### Tasks

#### 8.1 Full Test Suite Execution
**Owner**: Trinity Architect
**Commands**:
```bash
# Pattern validation
python scripts/lint_patterns.py

# Python tests
pytest tests/validation/ -v --cov=dawsos/core --cov-report=html

# Knowledge loader
pytest tests/validation/test_knowledge_loader.py -v

# Strict mode
TRINITY_STRICT_MODE=true pytest tests/validation/ -v

# Manual UI smoke test (checklist):
# - Start app: streamlit run dawsos/main.py
# - Test agent execution
# - Verify governance dashboard
# - Check capability metrics
# - Test pattern execution
```

**Acceptance**: All tests pass, coverage ≥85%

#### 8.2 Update SYSTEM_STATUS.md
**Owner**: Trinity Architect
**File**: `SYSTEM_STATUS.md`

**Update Sections**:
- Grade: A+ (98/100) → A++ (100/100)
- Recent improvements (Phases 1-7 summary)
- Documentation coverage (3 new guides)
- Test coverage metrics
- Trinity compliance: 100% (strict mode enabled)

**Validation**: Status matches actual system state

#### 8.3 Create Refactor Summary
**Owner**: Trinity Architect
**File**: `REFACTOR_COMPLETE.md`

**Content**:
- What was done (8 phases summary)
- Before/after metrics comparison
- Key improvements (documentation, strict mode, capability routing)
- Testing enhancements (CI integration)
- Next steps (Phase 2+ features)

**Validation**: Document accurate and comprehensive

#### 8.4 Update README.md
**Owner**: Trinity Architect
**Sections to Add**:
- Link to REFACTOR_COMPLETE.md
- "Developer Guides" section (3 new docs)
- Updated quick start (reference strict mode)

**Validation**: README reflects current system

#### 8.5 Tag Release
**Owner**: Trinity Architect
**Action**:
```bash
git tag -a v2.0.0 -m "Trinity 2.0 Complete - A++ Grade (100/100)"
git push origin v2.0.0
```

**Validation**: GitHub shows tag with notes

### Deliverables
- ✅ All tests passing (100%)
- ✅ Test coverage ≥85%
- ✅ SYSTEM_STATUS.md updated to A++
- ✅ REFACTOR_COMPLETE.md created
- ✅ README.md updated with new guides
- ✅ v2.0.0 tagged and pushed

### Error Prevention
- Run validation multiple times (ensure consistency)
- Test on clean checkout (verify no local-only files)
- Review all docs for accuracy
- Have someone else review before tagging release

---

## Risk Mitigation

### Pre-Execution Checklist

- [ ] Backup entire repository: `cp -r DawsOSB DawsOSB.backup.$(date +%Y%m%d)`
- [ ] Create feature branch: `git checkout -b refactor/trinity-2.0-completion`
- [ ] Verify all tests pass currently: `pytest tests/validation/ -v`
- [ ] Document current metrics (baseline for comparison)
- [ ] Ensure CLAUDE.md is in place (session continuity)

### During Execution

- [ ] Commit after each phase (atomic changes)
- [ ] Run validation after each phase (catch issues early)
- [ ] Update todo list after each task completion
- [ ] Consult specialist agents before major changes
- [ ] Test UI manually after UI/governance changes

### Rollback Strategy

**If Phase Fails**:
1. Revert last commit: `git reset --hard HEAD~1`
2. Review failure in logs/test output
3. Consult specialist agent for guidance
4. Fix issue in isolation
5. Re-run phase validation

**If Multiple Phases Fail**:
1. Return to main branch: `git checkout main`
2. Delete feature branch: `git branch -D refactor/trinity-2.0-completion`
3. Restore from backup if needed
4. Review plan with fresh perspective
5. Restart with incremental approach

### Common Pitfalls

| Issue | Prevention | Recovery |
|-------|-----------|----------|
| Tests fail after code change | Run `pytest` after each file edit | Revert file, fix incrementally |
| UI breaks after governance changes | Test UI manually after each change | Revert UI file, check imports |
| Pattern lint fails | Validate JSON syntax before commit | Use `jq` to fix formatting |
| Import errors after moves | Use relative imports, test thoroughly | Check sys.path, fix imports |
| Git conflicts | Small commits, frequent pulls | Use `git mergetool` |

---

## Execution Timeline

### Day 1 (6-8 hours)
- **Morning**: Phase 1 (Documentation) - 4 hours
- **Afternoon**: Phase 4 (Knowledge Loader) - 4 hours
- **Deliverable**: 3 dev guides, 26 datasets with _meta

### Day 2 (8-10 hours)
- **Morning**: Phase 2 (Trinity Enforcement) - 6 hours
- **Afternoon**: Phase 3 (Capability Routing) - 4 hours
- **Deliverable**: Strict mode enabled, 8-10 patterns migrated

### Day 3 (6-8 hours)
- **Morning**: Phase 5 (Testing & CI) - 4 hours
- **Afternoon**: Phase 6 (Cleanup) + Phase 7 (UI/Prompts) - 4 hours
- **Deliverable**: CI integrated, repo cleaned, UI polished

### Day 4 (2-3 hours)
- **Morning**: Phase 8 (Final Validation) - 2 hours
- **Afternoon**: Review, tag, celebrate - 1 hour
- **Deliverable**: A++ grade, v2.0.0 released

**Total Estimated Time**: 22-29 hours (3-5 days with breaks)

---

## Success Criteria

### Objective Metrics

- [ ] Pattern lint: 0 errors, 0 warnings
- [ ] Test coverage: ≥85%
- [ ] All tests passing: 100%
- [ ] Trinity compliance: 100% (strict mode)
- [ ] Documentation: 3 new guides completed
- [ ] Knowledge loader: 26/26 datasets with _meta
- [ ] Capability routing: 8-10 patterns migrated
- [ ] CI/CD: All jobs passing

### Qualitative Metrics

- [ ] Code is cleaner and more maintainable
- [ ] New developers can onboard with guides
- [ ] System behavior is predictable (strict mode)
- [ ] Error messages are helpful
- [ ] UI reflects Trinity architecture
- [ ] Repository is professional and organized

### Grade Progression

**Before**: A+ (98/100)
- Patterns: 45 ✅
- Tests: Manual validation ⚠️
- Documentation: Partial ⚠️
- Trinity enforcement: Optional ⚠️
- Knowledge _meta: ~50% ⚠️

**After**: A++ (100/100)
- Patterns: 45 ✅, capability-based routing ✅
- Tests: Automated pytest ✅, CI integrated ✅
- Documentation: Complete with guides ✅
- Trinity enforcement: Strict mode ✅
- Knowledge _meta: 100% ✅

---

## Post-Execution

### Immediate Next Steps (Optional Phase 2 Features)

1. **Enhanced Telemetry Dashboard**
   - Real-time execution graphs
   - Capability usage heatmaps
   - Performance bottleneck identification

2. **Automated Dataset Refresh**
   - Scheduled jobs for daily/weekly/monthly updates
   - API integration for live data sources
   - Notification system for stale data

3. **Pattern Auto-Generation**
   - LLM-based pattern creation from natural language
   - Pattern optimization suggestions
   - A/B testing for pattern variations

4. **Multi-Agent Orchestration**
   - Parallel agent execution (async)
   - Agent collaboration patterns
   - Distributed execution support

### Maintenance Cadence

- **Daily**: Monitor CI pipeline
- **Weekly**: Review bypass warnings, update stale datasets
- **Monthly**: Run full compliance audit, update documentation
- **Quarterly**: Review capabilities, consider new agents

---

## Specialist Agent Sign-Off

**🏛️ Trinity Architect**: Approved - Plan maintains architectural purity, strict mode enforcement sound

**🎯 Pattern Specialist**: Approved - Capability routing migration strategy solid, fallback mechanisms in place

**📚 Knowledge Curator**: Approved - _meta headers comprehensive, refresh workflow practical

**🤖 Agent Orchestrator**: Approved - Documentation guides complete, capability system well-covered

---

**Ready for Execution**: Yes ✅
**Approval Date**: October 3, 2025
**Execution Start**: Awaiting user confirmation
