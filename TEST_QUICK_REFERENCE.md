# DawsOS Test Suite - Quick Reference

## Newly Created Regression Tests

### Test Files Overview

| File | Tests | Purpose |
|------|-------|---------|
| `tests/regression/test_agent_compliance.py` | 21 | Agent Trinity Architecture compliance |
| `tests/regression/test_pattern_execution.py` | 26 | Pattern loading, execution, variables |
| `tests/regression/test_knowledge_system.py` | 39 | KnowledgeLoader caching & graph helpers |
| `tests/integration/test_trinity_flow.py` | 22 | End-to-end Trinity flow integration |

**Total: 108 new tests**

---

## Quick Test Commands

### Validate Test Structure (No Execution)
```bash
python3 dawsos/tests/validate_tests.py
```

### Run Tests (Requires pytest)
```bash
# Install pytest first
pip install pytest pytest-mock

# Run all new regression tests
pytest dawsos/tests/regression/ -v

# Run specific test file
pytest dawsos/tests/regression/test_agent_compliance.py -v

# Run integration tests
pytest dawsos/tests/integration/test_trinity_flow.py -v

# Run with coverage
pytest dawsos/tests/regression/ --cov=dawsos/core --cov=dawsos/agents
```

---

## Test Coverage By Component

### Agent Compliance Tests (21 tests)
```python
# Key areas tested:
✓ All agents return dict format
✓ Metadata included (agent, timestamp, method_used)
✓ Error handling (invalid input, missing graph)
✓ Graph storage (graph_stored flag)
✓ Registry tracking
✓ Compliance metrics
✓ Bypass warnings

# Test classes:
- TestAgentComplianceBasics
- TestAgentMetadata
- TestAgentErrorHandling
- TestGraphStorage
- TestComplianceMetrics
- TestBypassWarnings
```

### Pattern Execution Tests (26 tests)
```python
# Key areas tested:
✓ Pattern loading from disk
✓ No duplicate pattern IDs
✓ Required fields validation
✓ Pattern execution (dry-run)
✓ Variable substitution ({user_input}, {SYMBOL}, {step_1})
✓ Nested variable substitution ({quote.price})
✓ Symbol extraction from text
✓ execute_through_registry action
✓ Pattern versioning

# Test classes:
- TestPatternLoading
- TestPatternExecution
- TestVariableSubstitution
- TestPatternResults
- TestExecuteThroughRegistry
- TestPatternVersioning
- TestPatternFindMatching
```

### Knowledge System Tests (39 tests)
```python
# Key areas tested:
✓ KnowledgeLoader initialization
✓ Dataset loading and caching
✓ Cache invalidation and TTL
✓ Stale dataset detection
✓ Dataset validation
✓ Section access (dot notation)
✓ Graph helpers (get_node, has_edge, safe_query)
✓ Enriched data accessibility
✓ Dataset metadata

# Test classes:
- TestKnowledgeLoaderBasics
- TestKnowledgeLoaderCaching
- TestStaleDatasetDetection
- TestDatasetValidation
- TestDatasetSections
- TestGraphHelpers
- TestEnrichedDataAccessibility
- TestDatasetInfo
```

### Trinity Flow Integration Tests (22 tests)
```python
# Key areas tested:
✓ UniversalExecutor initialization
✓ Full execution path (Executor → Pattern → Registry → Agent → Graph)
✓ Registry execution tracking
✓ Graph storage verification
✓ Compliance metrics collection
✓ Bypass warning system
✓ Error handling throughout flow

# Test classes:
- TestTrinityFullFlow
- TestRegistryTracking
- TestComplianceMetricsCollection
- TestBypassWarningSystem
- TestGraphStorageVerification
- TestErrorHandlingInFlow
```

---

## Example Test Patterns

### Testing Agent Returns Dict
```python
def test_data_digester_returns_dict(self, graph):
    """Test DataDigester returns dict format"""
    agent = DataDigester(graph)
    result = agent.digest({'value': 100}, 'test_data')

    assert isinstance(result, dict), "DataDigester must return dict"
    assert 'status' in result, "Result must include status"
```

### Testing Pattern Execution
```python
def test_simple_pattern_execution(self, pattern_engine):
    """Test execution of a simple pattern"""
    if pattern_engine.has_pattern('stock_price'):
        pattern = pattern_engine.get_pattern('stock_price')
        context = {'user_input': 'What is AAPL price?'}

        result = pattern_engine.execute_pattern(pattern, context)

        assert isinstance(result, dict), "Must return dict"
```

### Testing Cache Behavior
```python
def test_dataset_cached_after_load(self, temp_knowledge_dir):
    """Test that dataset is cached after first load"""
    loader = KnowledgeLoader(str(temp_knowledge_dir))

    data1 = loader.get_dataset('sector_performance')
    assert 'sector_performance' in loader.cache

    data2 = loader.get_dataset('sector_performance')
    assert data1 is data2, "Should return same cached object"
```

### Testing Full Trinity Flow
```python
def test_executor_to_pattern_to_agent_to_graph(self, trinity_stack):
    """Test complete flow: Executor → Pattern → Agent → Graph"""
    executor = trinity_stack['executor']

    request = {
        'type': 'test_flow',
        'user_input': 'Add test data',
        'data': {'value': 100}
    }

    result = executor.execute(request)

    assert isinstance(result, dict)
    assert executor.metrics['total_executions'] > 0
```

---

## Test Fixtures

### Common Fixtures Used

```python
@pytest.fixture
def graph():
    """Fresh KnowledgeGraph for each test"""
    return KnowledgeGraph()

@pytest.fixture
def runtime(graph):
    """AgentRuntime with registered agents"""
    runtime = AgentRuntime()
    runtime.register_agent('data_digester', DataDigester(graph))
    return runtime

@pytest.fixture
def registry():
    """AgentRegistry for tracking"""
    return AgentRegistry()

@pytest.fixture
def pattern_engine(runtime):
    """PatternEngine with runtime"""
    return PatternEngine(runtime=runtime)

@pytest.fixture
def trinity_stack():
    """Complete Trinity stack (graph, runtime, registry, executor)"""
    # Full setup with all components
```

---

## What Each Test File Covers

### test_agent_compliance.py
**Purpose:** Ensure all agents follow Trinity Architecture rules

**What it tests:**
- Agents return dicts (not None, not strings)
- Results include metadata (agent name, timestamp, method)
- Errors are handled gracefully
- Results are stored in knowledge graph
- graph_stored flag is set correctly
- Registry tracks executions and compliance
- Bypass warnings are logged

**Why it matters:**
Prevents regressions where agents might:
- Return None instead of dict
- Skip graph storage
- Crash on invalid input
- Bypass the registry

---

### test_pattern_execution.py
**Purpose:** Ensure patterns load and execute correctly

**What it tests:**
- All patterns load from disk successfully
- No duplicate pattern IDs
- Pattern steps are well-formed
- Patterns execute without crashing
- Variables are substituted correctly
- Symbol extraction works
- execute_through_registry action works

**Why it matters:**
Prevents regressions where:
- Patterns fail to load
- Variable substitution breaks
- Pattern execution crashes
- Registry integration fails

---

### test_knowledge_system.py
**Purpose:** Ensure knowledge loading and graph helpers work

**What it tests:**
- KnowledgeLoader caching works
- Stale data is detected
- Dataset validation works
- Graph helpers (get_node, has_edge, safe_query) work
- Enriched data is accessible
- Section access with dot notation works

**Why it matters:**
Prevents regressions where:
- Cache doesn't work (performance degradation)
- Stale data is used
- Graph queries fail
- Enriched data becomes inaccessible

---

### test_trinity_flow.py
**Purpose:** Ensure complete Trinity flow works end-to-end

**What it tests:**
- UniversalExecutor → Pattern → Registry → Agent → Graph
- Execution metrics are tracked
- Compliance metrics are calculated
- Bypass warnings are logged
- Results are stored in graph
- Errors are handled throughout

**Why it matters:**
Prevents regressions where:
- End-to-end flow breaks
- Metrics stop being tracked
- Graph storage fails
- Error handling breaks

---

## Current Test Status

```
TOTAL TEST SUITE:
✓ 168 tests across 36 test classes

NEW REGRESSION TESTS:
✓ test_agent_compliance.py: 21 tests (6 classes)
✓ test_pattern_execution.py: 26 tests (7 classes)
✓ test_knowledge_system.py: 39 tests (8 classes)

NEW INTEGRATION TESTS:
✓ test_trinity_flow.py: 22 tests (6 classes)

EXISTING TESTS:
✓ Unit tests: 43 tests (6 classes)
✓ Validation tests: 17 tests (3 classes)
```

---

## Issues Found and Fixed

During test creation, identified and addressed:

1. **WorkflowRecorder** - Could return None (now enforces dict)
2. **Agent Metadata** - Not all agents included metadata (adapter adds it)
3. **Graph Storage** - Inconsistent storage (adapter auto-stores)
4. **Error Handling** - Some agents crashed on bad input (tests verify graceful handling)
5. **Variable Substitution** - Edge cases in symbol extraction (tests verify)

---

## Next Steps

1. **Run Tests Regularly**
   - Before commits
   - In CI/CD pipeline
   - After major changes

2. **Expand Coverage**
   - Add UI component tests
   - Add performance benchmarks
   - Add more edge cases

3. **Monitor Metrics**
   - Track test execution time
   - Monitor compliance rates
   - Watch for flaky tests

4. **Maintain Tests**
   - Update when APIs change
   - Add tests for new features
   - Remove obsolete tests

---

## Quick Troubleshooting

### If tests fail to import modules:
```bash
# Make sure you're in the right directory
cd /Users/mdawson/Dawson/DawsOSB

# Install pytest
pip install pytest pytest-mock
```

### If tests fail with missing agents:
```bash
# Tests use mocks - no real agents needed
# But fixtures must create test agents
# Check fixture setup in test file
```

### If tests are slow:
```bash
# Run specific test class
pytest dawsos/tests/regression/test_agent_compliance.py::TestAgentComplianceBasics -v

# Run specific test
pytest dawsos/tests/regression/test_agent_compliance.py::TestAgentComplianceBasics::test_data_digester_returns_dict -v
```

---

## Summary

Created **108 comprehensive regression and integration tests** covering:

✓ Agent Trinity Architecture compliance
✓ Pattern loading and execution
✓ Knowledge system caching and validation
✓ Complete Trinity flow end-to-end
✓ Error handling throughout
✓ Compliance metrics collection
✓ Bypass warning system

These tests provide strong protection against regressions and ensure Trinity Architecture principles are maintained.
