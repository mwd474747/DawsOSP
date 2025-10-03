# Agent Registry Analysis & Fix Plan

## Problem Statement

**Error**: `ModuleNotFoundError: No module named 'core.agent_registry'`

**Root Cause**: `universal_executor.py` imports from non-existent module:
```python
from core.agent_registry import AgentRegistry  # Line 23
```

**Actual Location**: `AgentRegistry` lives in `core/agent_adapter.py:164`

---

## Current State Analysis

### Registry Architecture (What Works)

1. **AgentRegistry Location**: `core/agent_adapter.py:164`
   - Properly defined and functional
   - Used by `AgentRuntime.__init__` (line 16)
   - Has compliance tracking built-in

2. **AgentAdapter**: `core/agent_adapter.py:17`
   - Wraps every agent for consistent interface
   - Auto-detects available methods (process, think, analyze, etc.)
   - Normalizes responses with metadata
   - AUTO-STORES results in graph (Trinity compliance)

3. **AgentRuntime Integration**: `core/agent_runtime.py`
   - Creates `AgentRegistry` instance at line 16
   - All executions route through `registry.execute_with_tracking()`
   - Maintains both raw agents dict AND registry

### The Dual Storage Problem

**Issue**: Redundant agent storage creates bypass paths

```python
# In AgentRuntime
self.agents = {}              # Raw agents (line 12)
self.agent_registry = AgentRegistry()  # Wrapped agents (line 16)

# On registration
self.agents[name] = agent          # Store raw
self.agent_registry.register(...)  # Store wrapped
```

**Consequence**: Code can bypass adapter by accessing `runtime.agents[name]` directly

---

## The Import Error Chain

### File: `universal_executor.py`

**Line 23**:
```python
from core.agent_registry import AgentRegistry
```

**Should be**:
```python
from core.agent_adapter import AgentRegistry
```

### File: `main.py`

**Line 19**:
```python
from core.universal_executor import UniversalExecutor, get_executor
```

When main.py loads, it triggers universal_executor.py import, which fails on line 23.

---

## Missing KnowledgeGraph Methods

`universal_executor.py:151` calls:
```python
agent_node = self.graph.get_nodes_by_type('agent')
```

**Problem**: `KnowledgeGraph` doesn't have `get_nodes_by_type()` method

**Current KnowledgeGraph Methods**:
- `add_node()` ✅
- `connect()` ✅
- `get_node()` ✅
- `get_stats()` ✅
- `get_nodes_by_type()` ❌ MISSING

---

## Architectural Gaps Identified

### 1. Registry Not Enforced

**Pattern Engine** (`core/pattern_engine.py`):
- Has special cases for agent method detection
- Sometimes calls agents directly instead of through registry
- Duplicates adapter logic

**Orchestrators**:
- `core/claude_orchestrator.py` - Pre-registry, does own lookups
- `core/orchestrator.py` - Legacy, bypasses registry

**Result**: Registry not the "single execution path"

### 2. Capability System Weak

**Current State**:
- Most agents don't declare capabilities at registration
- Adapter infers from class name (heuristic, fragile)
- `execute_by_capability()` rarely works

**Example**:
```python
# In main.py registration
runtime.register_agent('claude', claude_agent)
# ^ No capabilities passed, adapter infers from class name
```

### 3. No Validation Layer

**Missing Checks**:
- Patterns reference agent names as strings - no validation
- Invalid agent name = runtime error
- No schema enforcement on pattern JSON
- No guard rails on capability requirements

### 4. Silent Failures

**AgentAdapter.execute()** (line 119):
```python
except Exception as e:
    # Log error but continue trying other methods
    continue
```

**Problem**: Exceptions swallowed, not propagated to compliance metrics

### 5. UniversalExecutor Not Integrated

**Status**: Imported in main.py but not actually used
- Registry path exists but is dormant
- Direct agent calls still happen
- Meta-patterns (meta_executor, architecture_validator) never run

---

## Complete Dependency Map

```
main.py
  ↓ imports
universal_executor.py (BROKEN)
  ↓ tries to import
core.agent_registry (DOESN'T EXIST)
  ↓ should be
core.agent_adapter.py (AgentRegistry lives here)
  ↑ used by
agent_runtime.py
  ↑ used by
main.py (creates runtime, registers agents)
```

---

## Fix Strategy

### Immediate (Fix the Error)

1. **Fix Import** in `universal_executor.py:23`:
   ```python
   from core.agent_adapter import AgentRegistry
   ```

2. **Add Missing Method** to `KnowledgeGraph`:
   ```python
   def get_nodes_by_type(self, node_type: str) -> List[Tuple[str, Dict]]:
       """Return all nodes of a specific type."""
       return [(nid, data) for nid, data in self.nodes.items()
               if data.get('type') == node_type]
   ```

3. **Test the Fix**:
   ```bash
   python3 -c "from core.universal_executor import UniversalExecutor; print('✅ Import works')"
   ```

### Short-term (Make Registry Work)

4. **Enforce Registry Path**:
   - Update PatternEngine to ALWAYS use registry
   - Remove direct agent dict access
   - Make `runtime.agents` private (`_agents`)

5. **Add Capability Declarations**:
   ```python
   # In main.py
   runtime.register_agent('claude', claude_agent, capabilities={
       'can_interpret': True,
       'can_reason': True,
       'requires_llm': True
   })
   ```

6. **Add Pattern Validation**:
   - Schema validation on pattern load
   - Check agent names exist in registry
   - Verify capabilities before execution

### Long-term (Full Trinity Compliance)

7. **Deprecate Legacy Orchestrators**:
   - Migrate claude_orchestrator.py to patterns
   - Remove orchestrator.py
   - Single execution path through registry

8. **Add Error Propagation**:
   - AgentAdapter failures tracked in metrics
   - Compliance metrics include error counts
   - Alerts on repeated failures

9. **Enable UniversalExecutor**:
   - Route all main.py execution through it
   - Activate meta_executor pattern
   - Self-healing architecture validation

---

## Recommended Implementation Order

### Phase 1: Fix the Crash (10 min)
1. Change import in `universal_executor.py`
2. Add `get_nodes_by_type()` to `KnowledgeGraph`
3. Test Docker container starts

### Phase 2: Validate Registry (30 min)
4. Add capability declarations to all agents in main.py
5. Create pattern validation on load
6. Add tests for registry compliance

### Phase 3: Enforce Single Path (1 hour)
7. Make runtime.agents private
8. Update PatternEngine to use registry exclusively
9. Add deprecation warnings to legacy orchestrators

### Phase 4: Full Compliance (2 hours)
10. Enable UniversalExecutor as default entry point
11. Activate meta-patterns
12. Add compliance monitoring dashboard

---

## Testing Strategy

### Unit Tests
```python
def test_agent_registry_import():
    """Registry imports correctly."""
    from core.agent_adapter import AgentRegistry
    assert AgentRegistry is not None

def test_universal_executor_initialization():
    """UniversalExecutor initializes without errors."""
    from core.universal_executor import get_executor
    from core.knowledge_graph import KnowledgeGraph
    from core.agent_adapter import AgentRegistry

    graph = KnowledgeGraph()
    registry = AgentRegistry()
    executor = get_executor(graph, registry)
    assert executor is not None

def test_knowledge_graph_get_nodes_by_type():
    """KnowledgeGraph can filter by type."""
    graph = KnowledgeGraph()
    nid = graph.add_node('test', {'type': 'agent'})

    agent_nodes = graph.get_nodes_by_type('agent')
    assert len(agent_nodes) == 1
    assert agent_nodes[0][0] == nid
```

### Integration Tests
```python
def test_agent_execution_through_registry():
    """Agents execute through registry with tracking."""
    runtime = AgentRuntime()
    # ... register test agent ...
    result = runtime.execute('test_agent', {'input': 'test'})

    # Verify tracking
    metrics = runtime.get_compliance_metrics()
    assert metrics['agents']['test_agent']['executions'] == 1
    assert 'graph_stored' in result

def test_pattern_uses_registry():
    """PatternEngine uses registry not direct agents."""
    # Create pattern that calls agent
    # Verify execution goes through adapter
    # Check compliance metrics updated
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Docker container starts without import errors
- [ ] Application loads successfully
- [ ] No `ModuleNotFoundError` in logs

### Phase 2 Complete When:
- [ ] All agents have declared capabilities
- [ ] Patterns validated on load
- [ ] Invalid agent names caught before execution

### Phase 3 Complete When:
- [ ] All agent executions go through registry
- [ ] Compliance metrics show 100% adapter usage
- [ ] No direct agent dict access in codebase

### Phase 4 Complete When:
- [ ] UniversalExecutor handles all requests
- [ ] Meta-patterns operational
- [ ] Architecture self-validates on startup

---

## Code Changes Required

### File 1: `core/universal_executor.py`
```python
# Line 23: Change import
from core.agent_adapter import AgentRegistry  # Fixed import
```

### File 2: `core/knowledge_graph.py`
```python
# Add new method
def get_nodes_by_type(self, node_type: str) -> List[Tuple[str, Dict]]:
    """Return all nodes of a specific type."""
    return [(nid, data) for nid, data in self.nodes.items()
            if data.get('type') == node_type]
```

### File 3: `main.py` (Phase 2+)
```python
# Add capabilities to registrations
runtime.register_agent('claude', claude_agent, capabilities={
    'can_interpret': True,
    'can_reason': True,
    'requires_llm': True,
    'purpose': 'natural_language_understanding'
})

runtime.register_agent('data_harvester', data_harvester, capabilities={
    'can_fetch_data': True,
    'data_sources': ['fmp', 'fred', 'crypto'],
    'purpose': 'data_collection'
})
# ... etc for all agents
```

---

## Impact Assessment

### Risk: Low
- Fixing import is safe, no logic changes
- Adding KnowledgeGraph method is additive
- Existing functionality unaffected

### Benefit: High
- Application starts successfully
- UniversalExecutor path becomes available
- Foundation for full Trinity compliance

### Effort: Minimal (Phase 1)
- 2 file changes
- 5 lines of code
- 10 minutes to implement

---

## Recommendation

**Immediate Action**: Implement Phase 1 fixes now
- Change import in universal_executor.py
- Add get_nodes_by_type to KnowledgeGraph
- Rebuild Docker and test

**Next Session**: Implement Phase 2
- Add capability declarations
- Validate patterns on load
- Test registry compliance

**Future Sessions**: Phases 3-4
- Enforce single execution path
- Activate UniversalExecutor
- Full Trinity compliance

---

## Conclusion

The registry architecture is **well-designed but partially implemented**. The core components work, but:

1. **Import path is wrong** (immediate fix required)
2. **Enforcement is weak** (patterns bypass registry)
3. **Validation is missing** (no guard rails)
4. **Integration incomplete** (UniversalExecutor dormant)

**The good news**: Architecture is sound, just needs wiring completed. All the pieces exist, they're just not fully connected.

**Phase 1 fix gets app running. Phases 2-4 unlock the full Trinity vision.**
