# Trinity Completion Roadmap - Final Baseline

**Goal**: Eliminate all technical debt, enforce Trinity compliance everywhere, and establish a clean, maintainable baseline.

**Timeline**: 2-3 weeks
**Current Status**: 85% → Target: 100% (Production-Ready)

---

## Executive Summary

DawsOS has a strong Trinity core (85% complete), but needs **4 critical areas** addressed to reach 100% compliance and production readiness:

1. **Enforce Trinity Execution Everywhere** - Add guardrails, eliminate bypass paths
2. **Centralize Data & Pattern Hygiene** - ✅ DONE (knowledge_loader.py exists, patterns migrated)
3. **Clean Up Legacy Components & Tests** - Remove Claude-era logic, add regression tests
4. **Solidify Persistence & Observability** - Enhance PersistenceManager, consolidate docs

**What's Already Done** ✅:
- ✅ `core/knowledge_loader.py` created (centralized, cached dataset loading)
- ✅ All 45 patterns migrated to `execute_through_registry` (100% Trinity-compliant)
- ✅ Pattern versioning added (version, last_updated on all patterns)
- ✅ Pattern linter created (scripts/lint_patterns.py)
- ✅ AgentRegistry enhanced with telemetry (last_success, failure_reasons, capability_tags)
- ✅ Bypass warning logging implemented
- ✅ `exec_via_registry()` helper added to AgentRuntime

**What Remains**:
- ⚠️ Enforce guardrails (prevent direct agent access)
- ⚠️ Add capability metadata to all agent registrations
- ⚠️ Clean up legacy tests and documentation
- ⚠️ Add regression tests for Trinity compliance
- ⚠️ Enhance PersistenceManager
- ⚠️ Consolidate architecture documentation

---

## Phase 1: Enforce Trinity Execution Everywhere (Week 1)

**Goal**: Make it impossible to bypass the registry accidentally

### 1.1 Add Access Guardrails (2 days)

**Problem**: Code can still call `runtime.agents[name]` or `pattern_engine._get_agent()` directly

**Solution**: Runtime access protection

```python
# File: dawsos/core/agent_runtime.py

class AgentRuntime:
    def __init__(self):
        self._agents = {}  # Private
        self.agent_registry = AgentRegistry()
        self._access_warnings_enabled = True

    @property
    def agents(self):
        """Read-only view with deprecation warning"""
        if self._access_warnings_enabled:
            import traceback
            caller = traceback.extract_stack()[-2]
            self.agent_registry.log_bypass_warning(
                caller=f"{caller.filename}:{caller.lineno}",
                agent_name="*",
                method="direct_access"
            )
            self.logger.warning(
                f"Direct agent access at {caller.filename}:{caller.lineno}. "
                f"Use runtime.exec_via_registry() instead."
            )
        return MappingProxyType(self._agents)
```

**Tasks**:
- [ ] Add `_access_warnings_enabled` flag to AgentRuntime
- [ ] Wrap `agents` property with warning logic
- [ ] Add `STRICT_MODE` environment variable to raise errors instead of warnings
- [ ] Update all internal code to use `exec_via_registry()`

**Files to modify**:
- `dawsos/core/agent_runtime.py`
- `dawsos/core/pattern_engine.py` (use registry methods internally)
- `dawsos/ui/*.py` (use `st.session_state.executor.execute()`)

### 1.2 Enforce Capability Metadata (3 days)

**Problem**: Most agents registered without explicit capabilities

**Solution**: Require capabilities at registration

```python
# File: dawsos/main.py

# Before (heuristic inference)
runtime.register_agent('financial_analyst', FinancialAnalyst(graph))

# After (explicit capabilities)
runtime.register_agent('financial_analyst', FinancialAnalyst(graph), capabilities={
    'can_calculate_dcf': True,
    'can_calculate_roic': True,
    'can_calculate_fcf': True,
    'can_value_companies': True,
    'requires_financial_data': True,
    'provides_valuation': True
})
```

**Tasks**:
- [ ] Add capability declarations to all 15 agents in main.py
- [ ] Create capability registry schema (capabilities.json)
- [ ] Add `require_capabilities=True` flag to AgentRegistry
- [ ] Warn on registration without capabilities (or error in strict mode)
- [ ] Update agent documentation with capability lists

**Agent Capability Mapping**:

```python
AGENT_CAPABILITIES = {
    'claude': {
        'can_process_natural_language': True,
        'can_reason': True,
        'has_llm': True
    },
    'data_harvester': {
        'can_fetch_external_data': True,
        'can_fetch_stock_quotes': True,
        'can_fetch_economic_data': True,
        'can_fetch_news': True,
        'has_external_apis': True
    },
    'data_digester': {
        'can_transform_data': True,
        'can_create_graph_nodes': True,
        'can_ingest_data': True
    },
    'financial_analyst': {
        'can_calculate_dcf': True,
        'can_calculate_roic': True,
        'can_calculate_fcf': True,
        'can_value_companies': True,
        'requires_financial_data': True
    },
    'pattern_spotter': {
        'can_detect_patterns': True,
        'can_analyze_trends': True,
        'can_find_anomalies': True
    },
    'relationship_hunter': {
        'can_find_correlations': True,
        'can_analyze_relationships': True,
        'can_map_connections': True
    },
    'forecast_dreamer': {
        'can_forecast': True,
        'can_predict': True,
        'requires_historical_data': True
    },
    'governance_agent': {
        'can_audit': True,
        'can_validate': True,
        'can_enforce_policy': True,
        'provides_governance': True
    },
    # ... complete for all 15 agents
}
```

### 1.3 Add Runtime Compliance Checks (1 day)

**Problem**: No automated enforcement of Trinity compliance

**Solution**: AST/runtime checks

```python
# File: dawsos/core/compliance_checker.py

class ComplianceChecker:
    """Enforces Trinity Architecture compliance at runtime"""

    def check_pattern_execution(self, pattern_id: str):
        """Verify pattern only uses registry actions"""
        pattern = self.pattern_engine.get_pattern(pattern_id)

        for step in pattern.get('steps', []):
            # Check for direct agent references
            if 'agent' in step and step.get('action') != 'execute_through_registry':
                raise ComplianceError(
                    f"Pattern {pattern_id} step {step} bypasses registry. "
                    f"Use 'execute_through_registry' action."
                )

    def check_agent_access(self, caller_module: str):
        """Monitor who's accessing agents directly"""
        # Log in production, raise in dev
        if os.getenv('TRINITY_STRICT_MODE') == 'true':
            raise ComplianceError(
                f"{caller_module} accessed agents directly. "
                f"Use exec_via_registry() instead."
            )
```

**Tasks**:
- [ ] Create `dawsos/core/compliance_checker.py`
- [ ] Add pre-execution pattern validation
- [ ] Add runtime agent access monitoring
- [ ] Create `TRINITY_STRICT_MODE` environment flag
- [ ] Add compliance report to dashboard

**Files to create**:
- `dawsos/core/compliance_checker.py`
- `dawsos/tests/test_compliance.py`

---

## Phase 2: Data & Pattern Hygiene (Week 1-2)

**Status**: ✅ **MOSTLY COMPLETE**

### 2.1 Knowledge Loader Integration ✅ DONE

- ✅ `core/knowledge_loader.py` created
- ✅ 30-minute TTL caching
- ✅ 7 datasets registered
- ✅ Validation on load
- ✅ Singleton pattern
- ✅ PatternEngine integrated

**Remaining**:
- [ ] Wire into PersistenceManager for freshness tracking
- [ ] Add `reload_all()` to startup sequence
- [ ] Monitor stale datasets in dashboard

### 2.2 Pattern Migration ✅ DONE

- ✅ All 45 patterns migrated to `execute_through_registry`
- ✅ Versioning added (version, last_updated)
- ✅ Pattern linter created and validated

**Remaining**:
- [ ] Implement 3 empty governance patterns (or deprecate)
- [ ] Add pattern execution tests
- [ ] Create pattern performance benchmarks

### 2.3 Pattern Linting Enhancement (1 day)

**Current**: Linter checks schema, agent references, versioning

**Add**:
- [ ] Capability requirement validation
- [ ] Knowledge dependency checks
- [ ] Response template validation
- [ ] Circular dependency detection

```python
# scripts/lint_patterns.py

def _check_capability_requirements(self, pattern: Dict, filepath: Path):
    """Check pattern steps match agent capabilities"""
    for step in pattern.get('steps', []):
        if step.get('action') == 'execute_through_registry':
            agent_name = step['params']['agent']
            # Check if agent has required capabilities
            if agent_name in self.agent_capabilities:
                # Validate step requirements match agent capabilities
                pass
```

---

## Phase 3: Clean Up Legacy Components & Tests (Week 2)

**Goal**: Remove all Claude-era logic, ensure tests reflect Trinity architecture

### 3.1 Remove Legacy Orchestration References (2 days)

**Files to Clean**:

```bash
# Find legacy references
grep -r "claude_orchestrator\|orchestrator\.py" dawsos/ --exclude-dir=venv
grep -r "direct.*agent\[" dawsos/tests/ --exclude-dir=venv
```

**Tasks**:
- [ ] Remove imports of `claude_orchestrator`, `orchestrator`
- [ ] Update tests to use `UniversalExecutor.execute()`
- [ ] Remove `orchestrate()` calls (replaced with `executor.execute()`)
- [ ] Update documentation removing Claude-centric language

**Files to modify**:
- `dawsos/tests/unit/*.py`
- `dawsos/tests/integration/*.py`
- `dawsos/tests/validation/*.py`
- `dawsos/ui/*.py` (remove any orchestrator imports)

### 3.2 Add Regression Tests (3 days)

**Problem**: DataDigester and WorkflowRecorder were flagged; need tests to prevent regressions

**New Test Suites**:

```python
# File: dawsos/tests/regression/test_agent_compliance.py

def test_data_digester_stores_results():
    """Regression: DataDigester must store results in graph"""
    graph = KnowledgeGraph()
    digester = DataDigester(graph)

    result = digester.digest({'test': 'data'}, 'test_type')

    assert 'node_id' in result
    assert 'graph_stored' in result
    assert result['graph_stored'] is True

def test_workflow_recorder_returns_dict():
    """Regression: WorkflowRecorder must return dict, not None"""
    recorder = WorkflowRecorder()

    result = recorder.record({'test': 'workflow', 'success': True})

    assert isinstance(result, dict)
    assert 'status' in result
```

**Test Categories**:

1. **Trinity Compliance Tests**:
   - [ ] All patterns execute through registry
   - [ ] All agent results stored in graph
   - [ ] No direct agent access in production code
   - [ ] Capability-based routing works

2. **Agent Return Tests**:
   - [ ] All agents return dict
   - [ ] All agents include metadata (agent, timestamp, method_used)
   - [ ] All agents handle errors gracefully

3. **Pattern Execution Tests**:
   - [ ] Each pattern loads successfully
   - [ ] Each pattern executes without errors (dry-run)
   - [ ] Variable substitution works
   - [ ] Results include expected fields

4. **Knowledge System Tests**:
   - [ ] KnowledgeLoader caches correctly
   - [ ] Stale datasets detected
   - [ ] Graph helpers work (get_node, safe_query, etc.)
   - [ ] Enriched data accessible in patterns

**Files to create**:
- `dawsos/tests/regression/test_agent_compliance.py`
- `dawsos/tests/regression/test_pattern_execution.py`
- `dawsos/tests/regression/test_knowledge_system.py`
- `dawsos/tests/integration/test_trinity_flow.py`

### 3.3 Add AST Compliance Check (2 days)

**Problem**: Want to catch `runtime.agents[...]` in code review

**Solution**: Static analysis script

```python
# File: scripts/check_compliance.py

import ast
import sys
from pathlib import Path

class AgentAccessChecker(ast.NodeVisitor):
    """Find direct agent access in Python code"""

    def __init__(self):
        self.violations = []

    def visit_Subscript(self, node):
        # Detect runtime.agents[...] or runtime.agents.get(...)
        if isinstance(node.value, ast.Attribute):
            if node.value.attr == 'agents':
                self.violations.append({
                    'line': node.lineno,
                    'type': 'direct_agent_access',
                    'message': 'Use runtime.exec_via_registry() instead'
                })
        self.generic_visit(node)

def check_file(filepath: Path):
    """Check a Python file for compliance violations"""
    with open(filepath) as f:
        tree = ast.parse(f.read(), filename=str(filepath))

    checker = AgentAccessChecker()
    checker.visit(tree)

    return checker.violations

# Run on all Python files
for py_file in Path('dawsos').rglob('*.py'):
    violations = check_file(py_file)
    if violations:
        print(f"{py_file}: {len(violations)} violations")
```

**Tasks**:
- [ ] Create `scripts/check_compliance.py`
- [ ] Add to pre-commit hooks
- [ ] Run on CI/CD pipeline
- [ ] Add exceptions for sanctioned usage (e.g., AgentRuntime internals)

---

## Phase 4: Solidify Persistence & Observability (Week 2-3)

**Goal**: Production-grade persistence and consolidated documentation

### 4.1 Enhance PersistenceManager (3 days)

**Current State**: Basic save/load functionality

**Add**:

```python
# File: dawsos/core/persistence.py

class PersistenceManager:
    def __init__(self, backup_retention_days: int = 30):
        self.backup_dir = Path('storage/backups')
        self.retention_days = backup_retention_days

    def save_graph_with_backup(self, graph: KnowledgeGraph):
        """Save graph with automatic backup and rotation"""
        # Create timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f'graph_{timestamp}.json'

        # Calculate checksum
        checksum = self._calculate_checksum(graph)

        # Save with metadata
        self._save_with_metadata(graph, backup_path, checksum)

        # Rotate old backups
        self._rotate_backups()

    def _calculate_checksum(self, graph: KnowledgeGraph) -> str:
        """Calculate SHA-256 checksum of graph data"""
        import hashlib
        data = json.dumps(graph.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def _rotate_backups(self):
        """Remove backups older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)

        for backup in self.backup_dir.glob('graph_*.json'):
            # Parse timestamp from filename
            timestamp_str = backup.stem.split('_', 1)[1]
            timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

            if timestamp < cutoff:
                backup.unlink()
                self.logger.info(f"Rotated old backup: {backup}")

    def verify_integrity(self, filepath: Path) -> bool:
        """Verify graph file integrity using checksum"""
        metadata_path = filepath.with_suffix('.meta')

        if not metadata_path.exists():
            return False

        with open(metadata_path) as f:
            metadata = json.load(f)

        # Recalculate checksum
        with open(filepath) as f:
            graph_data = json.load(f)

        current_checksum = self._calculate_checksum_from_dict(graph_data)

        return current_checksum == metadata['checksum']

    def list_backups(self) -> List[Dict]:
        """List available backups with metadata"""
        backups = []
        for backup in sorted(self.backup_dir.glob('graph_*.json')):
            metadata_path = backup.with_suffix('.meta')
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                backups.append({
                    'path': backup,
                    'timestamp': metadata['timestamp'],
                    'checksum': metadata['checksum'],
                    'node_count': metadata.get('node_count'),
                    'edge_count': metadata.get('edge_count')
                })
        return backups

    def restore_from_backup(self, backup_path: Path) -> KnowledgeGraph:
        """Restore graph from backup with verification"""
        if not self.verify_integrity(backup_path):
            raise IntegrityError(f"Backup {backup_path} failed integrity check")

        graph = KnowledgeGraph()
        graph.load(backup_path)
        return graph
```

**Tasks**:
- [ ] Add backup rotation (retain last 30 days)
- [ ] Add checksum calculation (SHA-256)
- [ ] Add integrity verification
- [ ] Add backup metadata (timestamp, node/edge counts)
- [ ] Add restore functionality with verification
- [ ] Document recovery procedures
- [ ] Wire KnowledgeLoader freshness into persistence metadata

**Files to modify**:
- `dawsos/core/persistence.py`
- `dawsos/tests/validation/test_persistence.py`

### 4.2 Add Recovery Documentation (1 day)

**Create**: `docs/DISASTER_RECOVERY.md`

```markdown
# DawsOS Disaster Recovery Procedures

## Backup Strategy

- **Automatic backups**: Every graph save creates timestamped backup
- **Retention**: 30 days of backups
- **Location**: `storage/backups/graph_YYYYMMDD_HHMMSS.json`
- **Integrity**: SHA-256 checksums in `.meta` files

## Recovery Scenarios

### 1. Corrupted Graph File

python
from core.persistence import PersistenceManager

pm = PersistenceManager()
backups = pm.list_backups()
latest_backup = backups[-1]
graph = pm.restore_from_backup(latest_backup['path'])


### 2. Pattern Migration Rollback

bash
rm -rf dawsos/patterns/*
cp -r storage/backups/patterns_pre_migration/* dawsos/patterns/
```

**Tasks**:
- [ ] Document backup strategy
- [ ] Document recovery procedures
- [ ] Add runbook for common failures
- [ ] Test recovery procedures

### 4.3 Consolidate Documentation (2 days)

**Goal**: Single source of truth for Trinity Architecture

**Current State**: Fragmented across multiple files

**Target Structure**:
```
dawsos/
├── README.md                           # Quick start, overview
├── docs/
│   ├── TrinityExecutionFlow.md         # ⭐ CANONICAL architecture doc
│   ├── DISASTER_RECOVERY.md            # Recovery procedures
│   ├── AGENT_DEVELOPMENT.md            # How to create agents
│   ├── PATTERN_DEVELOPMENT.md          # How to create patterns
│   ├── TESTING_GUIDE.md                # Testing strategy
│   ├── DEPLOYMENT.md                   # Production deployment
│   └── archive/                        # Historical plans
│       ├── PHASE1_COMPLETE_SUMMARY.md
│       ├── PATTERN_MIGRATION_PLAN.md
│       ├── etc.
```

**Tasks**:
- [ ] Make `docs/TrinityExecutionFlow.md` the canonical reference
- [ ] Update `README.md` to point to Trinity docs
- [ ] Create `AGENT_DEVELOPMENT.md` guide
- [ ] Create `PATTERN_DEVELOPMENT.md` guide
- [ ] Create `TESTING_GUIDE.md`
- [ ] Archive old planning docs in `docs/archive/`
- [ ] Remove contradictory or outdated info

**Trinity Execution Flow Doc** (expand existing):

```markdown
# Trinity Execution Flow - Canonical Reference

## Architecture Overview

All execution in DawsOS flows through the Trinity path:

Request → UniversalExecutor → PatternEngine → AgentRegistry → Agent → KnowledgeGraph


## Components

### UniversalExecutor
- **Single entry point** for all requests
- Routes to `meta_executor` pattern
- Tracks execution metrics
- Handles fallback

### PatternEngine
- Loads 45+ JSON patterns from `dawsos/patterns/`
- Matches triggers to user input
- Executes steps sequentially
- Resolves variables
- Integrates enriched knowledge

### AgentRegistry
- Maintains 19 registered agents
- Wraps agents in AgentAdapter
- Tracks compliance metrics
- Logs bypass warnings
- Routes by capability

### AgentAdapter
- Normalizes agent interfaces
- Auto-stores results in graph
- Adds metadata (timestamp, method_used)
- Enforces Trinity compliance

### KnowledgeGraph
- Shared persistence layer
- Nodes, edges, patterns, forecasts
- Helper methods (get_node, safe_query, etc.)
- Seeded frameworks (Buffett, Dalio)

## Execution Rules

1. **ALL requests** must go through `executor.execute(request)`
2. **ALL agent calls** must use `runtime.exec_via_registry(agent, context)`
3. **ALL results** must be stored in the graph
4. **ALL data** must be loaded via `KnowledgeLoader`
5. **ALL patterns** must use `execute_through_registry` action

## Anti-Patterns (DO NOT DO)

❌ Direct agent access:
python
agent = runtime.agents['claude']  # WRONG
result = agent.think(context)     # WRONG


✅ Registry execution:
python
result = runtime.exec_via_registry('claude', context)  # CORRECT


❌ Direct pattern agent reference:
json
{"agent": "claude", "params": {...}}  # WRONG


✅ Registry action:
json
{
  "action": "execute_through_registry",
  "params": {"agent": "claude", "context": {...}}
}

```

---

## Implementation Timeline

### Week 1: Enforcement & Guardrails

| Task | Days | Owner | Status |
|------|------|-------|--------|
| Add access guardrails to AgentRuntime | 2 | Dev | Pending |
| Add capability metadata to all 15 agents | 3 | Dev | Pending |
| Create ComplianceChecker | 1 | Dev | Pending |
| Update pattern linter with capability checks | 1 | Dev | Pending |

### Week 2: Testing & Cleanup

| Task | Days | Owner | Status |
|------|------|-------|--------|
| Remove legacy orchestration references | 2 | Dev | Pending |
| Add regression tests (agent compliance) | 3 | Dev | Pending |
| Create AST compliance checker | 2 | Dev | Pending |
| Enhance PersistenceManager | 3 | Dev | Pending |

### Week 3: Documentation & Polish

| Task | Days | Owner | Status |
|------|------|-------|--------|
| Consolidate Trinity documentation | 2 | Dev | Pending |
| Create recovery procedures | 1 | Dev | Pending |
| Write development guides | 2 | Dev | Pending |
| Final testing & validation | 2 | Dev | Pending |

---

## Success Criteria

### Phase 1: Enforcement
- [ ] No code can access `runtime.agents[...]` without warning/error
- [ ] All 15 agents registered with explicit capabilities
- [ ] ComplianceChecker validates all pattern executions
- [ ] Bypass warnings logged and monitored

### Phase 2: Testing & Cleanup
- [ ] Zero legacy orchestration references
- [ ] 100% regression test coverage for Trinity flow
- [ ] AST checker integrated into CI/CD
- [ ] PersistenceManager has backup rotation & integrity checks

### Phase 3: Documentation
- [ ] Single canonical architecture doc (TrinityExecutionFlow.md)
- [ ] Recovery procedures documented and tested
- [ ] Development guides complete
- [ ] Old plans archived

---

## Post-Completion State

### What You'll Have:

1. **Enforced Trinity Execution**
   - ✅ Impossible to bypass registry accidentally
   - ✅ All agents have explicit capabilities
   - ✅ Runtime compliance monitoring
   - ✅ Automated validation on every execution

2. **Production-Grade Persistence**
   - ✅ Automatic backups with rotation
   - ✅ Integrity verification (checksums)
   - ✅ Documented recovery procedures
   - ✅ Knowledge freshness tracking

3. **Comprehensive Testing**
   - ✅ Regression tests prevent backsliding
   - ✅ Compliance tests enforce architecture
   - ✅ AST checks in CI/CD
   - ✅ Pattern execution tests

4. **Clean Documentation**
   - ✅ Single source of truth (TrinityExecutionFlow.md)
   - ✅ Development guides for agents & patterns
   - ✅ Recovery runbooks
   - ✅ Historical context archived

### Maintainability Improvements:

- 📊 **Observability**: Know exactly what's running and how
- 🔒 **Safety**: Can't accidentally break Trinity compliance
- 📚 **Documentation**: Clear guide for future developers
- 🧪 **Testability**: Catch regressions before production
- 🔄 **Recoverability**: Documented procedures for all failure modes

---

## Next Steps After Completion

Once Trinity baseline is solid:

1. **UI Enhancement** (APPLICATION_COMPLETION_STATUS.md Phase 1)
   - Pattern browser
   - Intelligence display
   - Dashboard enhancement

2. **Advanced Features**
   - Conditional pattern execution
   - Pattern versioning & migration
   - Performance optimization

3. **Production Deployment**
   - Docker containerization
   - CI/CD pipeline
   - Monitoring & alerting

---

**This roadmap eliminates all technical debt and locks the system to the Trinity Architecture, giving you a clean, maintainable baseline to build on.**
