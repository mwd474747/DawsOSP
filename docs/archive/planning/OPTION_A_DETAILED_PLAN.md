# Option A: Fix Then Document - Detailed Execution Plan

**Strategy**: Fix all critical and high-priority gaps, then update documentation to reflect true A+ grade
**Timeline**: 16 hours (2 working days)
**Target Grade**: A+ (98/100) - Accurate
**Risk Level**: Low (surgical fixes, comprehensive validation)

---

## Executive Summary

This plan executes **9 targeted fixes** in **6 phases** with clear scope boundaries to prevent feature creep. Each phase is owned by a specialist agent, includes validation checkpoints, and has rollback procedures.

**Scope Philosophy**:
- ✅ Fix what's broken
- ✅ Align documentation with reality
- ❌ No new features
- ❌ No refactoring beyond fixes
- ❌ No optimization work

---

## Phase Overview

| Phase | Owner | Duration | Risk | Fixes |
|-------|-------|----------|------|-------|
| 1 | Trinity Architect | 1.5h | Low | UniversalExecutor path |
| 2 | Pattern Specialist | 4h | Medium | Meta pattern actions |
| 3 | Agent Orchestrator | 2h | Low | Agent count alignment |
| 4 | Knowledge Curator | 1h | Low | PatternEngine graph |
| 5 | Trinity Architect | 3h | Low | CI, visualization, recovery |
| 6 | All Agents | 4.5h | Low | Testing, persistence, docs |

**Total**: 16 hours

---

## Phase 1: UniversalExecutor Path Fix (Trinity Architect)

**Duration**: 1.5 hours
**Risk**: Low (single-line change + validation)
**Agent**: 🏛️ Trinity Architect

### Objective
Fix UniversalExecutor meta pattern path so Trinity routing becomes functional.

### Current Problem
```python
# dawsos/core/universal_executor.py:57
meta_pattern_dir = Path('patterns/system/meta')  # WRONG
# Actual: dawsos/patterns/system/meta/
```

### Scope Boundaries
- ✅ Fix path to correct location
- ✅ Verify meta patterns load
- ✅ Test fallback still works if meta fails
- ❌ NO changes to meta pattern JSON files
- ❌ NO changes to PatternEngine loading logic
- ❌ NO new meta patterns

### Detailed Steps

#### Step 1.1: Read Trinity Architect Guide (5 min)
**Action**: Review specialist agent for context
```bash
cat .claude/trinity_architect.md | grep -A 10 "UniversalExecutor"
```

**Why**: Ensure we understand Trinity execution flow before modifying

#### Step 1.2: Backup Current File (2 min)
**Action**: Create safety backup
```bash
cp dawsos/core/universal_executor.py dawsos/core/universal_executor.py.backup.$(date +%Y%m%d_%H%M%S)
```

**Validation**: Backup file exists
```bash
ls -la dawsos/core/*.backup.*
```

#### Step 1.3: Fix Path (5 min)
**File**: `dawsos/core/universal_executor.py`
**Line**: 57

**Change**:
```python
# Before
meta_pattern_dir = Path('patterns/system/meta')

# After
meta_pattern_dir = Path('dawsos/patterns/system/meta')
```

**Scope Constraint**: ONLY change this one line. Do not:
- Change path construction logic
- Modify pattern loading
- Add new error handling
- Refactor Path usage

#### Step 1.4: Verify Meta Patterns Exist (5 min)
**Action**: Check files are accessible
```bash
ls -la dawsos/patterns/system/meta/*.json
# Should show: meta_executor.json, architecture_validator.json, etc.

# Count patterns
ls -1 dawsos/patterns/system/meta/*.json | wc -l
# Should be: 5 (per pattern specialist docs)
```

#### Step 1.5: Test Path Resolution (10 min)
**Action**: Create minimal test script

**File**: `tests/validation/test_executor_path.py`
```python
#!/usr/bin/env python3
"""Test UniversalExecutor meta pattern path"""

import sys
from pathlib import Path

# Add dawsos to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'dawsos'))

from core.knowledge_graph import KnowledgeGraph
from core.agent_adapter import AgentRegistry
from core.universal_executor import UniversalExecutor

def test_meta_pattern_path():
    """Verify UniversalExecutor finds meta patterns"""
    graph = KnowledgeGraph()
    registry = AgentRegistry(graph)

    executor = UniversalExecutor(graph, registry)

    # Check warning was NOT logged
    # (If path wrong, __init__ logs "Meta-pattern directory not found")
    # This is indirect but sufficient

    # Direct check: pattern_engine should have meta patterns
    if hasattr(executor, 'pattern_engine') and executor.pattern_engine:
        meta_patterns = [
            p for p in executor.pattern_engine.patterns.values()
            if 'meta' in p.get('id', '').lower()
        ]
        assert len(meta_patterns) > 0, "No meta patterns found"
        print(f"✅ Found {len(meta_patterns)} meta patterns")
    else:
        print("⚠️  Pattern engine not initialized (may need runtime)")

if __name__ == '__main__':
    test_meta_pattern_path()
    print("✅ UniversalExecutor path test passed")
```

**Run**:
```bash
cd /Users/mdawson/Dawson/DawsOSB
python tests/validation/test_executor_path.py
```

**Expected Output**: "✅ UniversalExecutor path test passed"

#### Step 1.6: Test Application Startup (20 min)
**Action**: Verify app still starts

```bash
# Stop current streamlit
pkill -f "streamlit run"

# Start with logging
cd /Users/mdawson/Dawson/DawsOSB
source dawsos/venv/bin/activate
streamlit run dawsos/main.py 2>&1 | grep -i "meta"
```

**Expected**:
- ✅ "Validated N meta-patterns" (not "Meta-pattern directory not found")
- ✅ App loads without errors

**Validation Checkpoint**:
```bash
# Check logs for the OLD error message
tail -100 dawsos/logs/PatternEngine_*.log | grep "Meta-pattern directory not found"
# Should be: NO matches (or only old timestamps)

# Check for SUCCESS message
tail -100 dawsos/logs/PatternEngine_*.log | grep "Validated.*meta-patterns"
# Should be: Recent timestamp with count
```

#### Step 1.7: Test Fallback Still Works (15 min)
**Action**: Temporarily break path to ensure fallback safe

**Test**:
```python
# tests/validation/test_fallback_mode.py
def test_fallback_when_meta_missing():
    """Verify fallback mode works if meta patterns fail"""
    # Temporarily point to wrong path
    executor = UniversalExecutor(graph, registry)
    executor.pattern_engine.patterns['meta_executor'] = None  # Simulate failure

    result = executor.execute({'type': 'test', 'data': 'test'})

    assert result.get('fallback_mode') == True, "Should use fallback"
    print("✅ Fallback mode works")
```

#### Step 1.8: Commit (5 min)
**Action**: Atomic commit
```bash
git add dawsos/core/universal_executor.py tests/validation/test_executor_path.py
git commit -m "fix: correct UniversalExecutor meta pattern path

- Change patterns/system/meta → dawsos/patterns/system/meta
- Add test for path resolution
- Verified fallback mode still works if meta fails

Fixes #1 from GAP_ANALYSIS_CRITICAL.md
Trinity routing now functional instead of always falling back"
```

### Deliverables
- ✅ `universal_executor.py` line 57 corrected
- ✅ Test script validates path resolution
- ✅ App starts without "directory not found" warning
- ✅ Fallback mode verified as safety net
- ✅ Git commit with atomic change

### Rollback Procedure
```bash
# If anything goes wrong:
cp dawsos/core/universal_executor.py.backup.* dawsos/core/universal_executor.py
git checkout dawsos/core/universal_executor.py
streamlit run dawsos/main.py  # Verify app works
```

### Success Criteria
- [ ] No "Meta-pattern directory not found" in logs
- [ ] "Validated N meta-patterns" appears in logs (N ≥ 3)
- [ ] Test script passes
- [ ] App starts successfully
- [ ] Fallback test passes

---

## Phase 2: Meta Pattern Action Handlers (Pattern Specialist)

**Duration**: 4 hours
**Risk**: Medium (new code, multiple handlers)
**Agent**: 🎯 Pattern Specialist

### Objective
Implement the 4 meta pattern actions so UniversalExecutor can actually route through meta_executor.

### Current Problem
Meta patterns reference actions that don't exist:
- `select_router` - No handler
- `execute_pattern` - No handler
- `track_execution` - No handler
- `store_in_graph` - No handler

### Scope Boundaries
- ✅ Add 4 action handlers to PatternEngine
- ✅ Test each handler individually
- ✅ Minimal implementation (no bells and whistles)
- ❌ NO new meta patterns
- ❌ NO changes to existing pattern JSON files
- ❌ NO refactoring of PatternEngine architecture
- ❌ NO performance optimizations

### Detailed Steps

#### Step 2.1: Read Pattern Specialist Guide (10 min)
**Action**: Review action handler patterns
```bash
cat .claude/pattern_specialist.md | grep -A 20 "execute_action"
```

**Study Existing Actions**:
```bash
grep -n "if action ==" dawsos/core/pattern_engine.py | head -20
```

**Why**: Understand existing action pattern before adding new ones

#### Step 2.2: Read Meta Pattern JSON (10 min)
**Action**: Understand what actions expect

```bash
cat dawsos/patterns/system/meta/meta_executor.json | jq '.steps'
```

**Document Expected Params**:
```json
{
  "select_router": {
    "params": {"request": "...", "context": "..."},
    "outputs": ["routing_decision"]
  },
  "execute_pattern": {
    "params": {"pattern_id": "...", "context": "..."},
    "outputs": ["result"]
  },
  "track_execution": {
    "params": {"result": "...", "start_time": "..."},
    "outputs": ["metrics"]
  },
  "store_in_graph": {
    "params": {"result": "...", "metadata": "..."},
    "outputs": ["node_id"]
  }
}
```

#### Step 2.3: Backup PatternEngine (2 min)
```bash
cp dawsos/core/pattern_engine.py dawsos/core/pattern_engine.py.backup.$(date +%Y%m%d_%H%M%S)
```

#### Step 2.4: Implement select_router (30 min)
**File**: `dawsos/core/pattern_engine.py`
**Location**: Inside `execute_action()` method (around line 780)

**Add Before existing returns**:
```python
        # === META PATTERN ACTIONS (Trinity 2.0) ===

        if action == 'select_router':
            """
            Determine optimal routing strategy for request.
            Returns: routing decision (pattern, agent, direct)
            """
            request = params.get('request', {})
            request_type = request.get('type', 'unknown')

            # Simple routing logic (no creep - just functional)
            routing_decision = {
                'strategy': 'pattern',  # Default to pattern-driven
                'reason': 'Trinity compliance',
                'timestamp': datetime.now().isoformat()
            }

            # Check if specific agent requested
            if 'agent' in request:
                routing_decision['strategy'] = 'agent'
                routing_decision['agent_name'] = request['agent']
                routing_decision['reason'] = 'Explicit agent request'

            # Check if pattern match exists
            elif 'pattern' in request or 'pattern_id' in request:
                routing_decision['strategy'] = 'pattern'
                routing_decision['pattern_id'] = request.get('pattern') or request.get('pattern_id')
                routing_decision['reason'] = 'Pattern-driven execution'

            # Check for user_input that might match pattern triggers
            elif 'user_input' in request:
                matched_pattern = self.find_pattern(request['user_input'])
                if matched_pattern:
                    routing_decision['strategy'] = 'pattern'
                    routing_decision['pattern_id'] = matched_pattern.get('id')
                    routing_decision['reason'] = 'Pattern trigger match'
                else:
                    routing_decision['strategy'] = 'agent'
                    routing_decision['agent_name'] = 'claude'  # Default orchestrator
                    routing_decision['reason'] = 'No pattern match, route to claude'

            self.logger.debug(f"Routing decision: {routing_decision['strategy']}")
            return routing_decision
```

**Scope Notes**:
- Simple if/elif logic only
- No ML/heuristics
- No caching
- No optimization
- Just enough to route correctly

**Test**:
```python
# tests/validation/test_meta_actions.py
def test_select_router():
    """Test select_router action"""
    engine = PatternEngine('dawsos/patterns', runtime=None)

    # Test 1: Explicit agent request
    result = engine.execute_action(
        'select_router',
        {'request': {'type': 'test', 'agent': 'claude'}},
        {},
        {}
    )
    assert result['strategy'] == 'agent'
    assert result['agent_name'] == 'claude'

    # Test 2: Pattern request
    result = engine.execute_action(
        'select_router',
        {'request': {'type': 'test', 'pattern_id': 'moat_analyzer'}},
        {},
        {}
    )
    assert result['strategy'] == 'pattern'
    assert result['pattern_id'] == 'moat_analyzer'

    print("✅ select_router tests passed")
```

#### Step 2.5: Implement execute_pattern (45 min)
**Location**: Same file, after select_router

```python
        if action == 'execute_pattern':
            """
            Execute a pattern by ID with given context.
            Handles nested pattern execution with recursion guard.
            """
            pattern_id = params.get('pattern_id')
            pattern_context = params.get('context', context)

            # Recursion guard (prevent infinite loops)
            recursion_depth = context.get('_recursion_depth', 0)
            if recursion_depth > 5:
                self.logger.error(f"Max recursion depth exceeded for pattern {pattern_id}")
                return {
                    'error': 'Max recursion depth exceeded',
                    'pattern_id': pattern_id,
                    'depth': recursion_depth
                }

            # Get pattern
            pattern = self.get_pattern(pattern_id)
            if not pattern:
                self.logger.error(f"Pattern not found: {pattern_id}")
                return {
                    'error': 'Pattern not found',
                    'pattern_id': pattern_id
                }

            # Add recursion tracking
            pattern_context['_recursion_depth'] = recursion_depth + 1
            pattern_context['_parent_pattern'] = context.get('pattern_id')

            # Execute pattern
            try:
                result = self.execute_pattern(pattern, pattern_context)
                result['nested_execution'] = True
                result['parent_pattern'] = context.get('pattern_id')
                return result
            except Exception as e:
                self.logger.error(f"Nested pattern execution failed: {e}")
                return {
                    'error': str(e),
                    'pattern_id': pattern_id
                }
```

**Scope Notes**:
- Simple recursion guard (depth limit)
- No parallel execution
- No result caching
- Just execute and return

**Test**:
```python
def test_execute_pattern():
    """Test execute_pattern action with recursion guard"""
    engine = PatternEngine('dawsos/patterns', runtime)

    # Test 1: Normal nested execution
    result = engine.execute_action(
        'execute_pattern',
        {'pattern_id': 'company_analysis_query', 'context': {'symbol': 'AAPL'}},
        {'pattern_id': 'meta_executor'},
        {}
    )
    assert 'error' not in result or result.get('nested_execution')

    # Test 2: Recursion guard
    deep_context = {'_recursion_depth': 6}
    result = engine.execute_action(
        'execute_pattern',
        {'pattern_id': 'test', 'context': deep_context},
        {},
        {}
    )
    assert 'error' in result
    assert 'recursion' in result['error'].lower()

    print("✅ execute_pattern tests passed")
```

#### Step 2.6: Implement track_execution (30 min)
**Location**: Same file, after execute_pattern

```python
        if action == 'track_execution':
            """
            Track execution metrics for telemetry.
            Records timing, success, and stores in runtime metrics.
            """
            result = params.get('result', {})
            start_time = params.get('start_time')

            # Calculate duration
            end_time = datetime.now()
            duration_ms = None
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    duration_ms = (end_time - start_dt).total_seconds() * 1000
                except Exception as e:
                    self.logger.warning(f"Could not calculate duration: {e}")

            # Build metrics
            metrics = {
                'success': result.get('success', True),
                'error': result.get('error'),
                'duration_ms': duration_ms,
                'timestamp': end_time.isoformat(),
                'pattern_id': context.get('pattern_id'),
                'agent_used': result.get('agent'),
                'graph_stored': result.get('graph_stored', False)
            }

            # Store in runtime if available
            if self.runtime and hasattr(self.runtime, 'track_execution'):
                try:
                    self.runtime.track_execution(metrics)
                except Exception as e:
                    self.logger.warning(f"Could not store metrics in runtime: {e}")

            # Log for observability
            self.logger.info(
                f"Execution tracked: {metrics['pattern_id']} "
                f"({metrics['duration_ms']:.1f}ms, success={metrics['success']})"
            )

            return metrics
```

**Scope Notes**:
- Simple timing calculation
- No histogram/percentiles
- No metrics aggregation
- Just track and log

**Test**:
```python
def test_track_execution():
    """Test track_execution action"""
    engine = PatternEngine('dawsos/patterns', runtime)

    start = (datetime.now() - timedelta(milliseconds=150)).isoformat()

    metrics = engine.execute_action(
        'track_execution',
        {
            'result': {'success': True, 'agent': 'claude'},
            'start_time': start
        },
        {'pattern_id': 'test_pattern'},
        {}
    )

    assert metrics['success'] == True
    assert metrics['duration_ms'] is not None
    assert metrics['duration_ms'] > 100  # ~150ms
    assert metrics['pattern_id'] == 'test_pattern'

    print("✅ track_execution tests passed")
```

#### Step 2.7: Implement store_in_graph (30 min)
**Location**: Same file, after track_execution

```python
        if action == 'store_in_graph':
            """
            Store execution result in knowledge graph.
            Creates node with result data and metadata.
            """
            result = params.get('result', {})
            metadata = params.get('metadata', {})

            # Check if graph available
            if not self.runtime or not hasattr(self.runtime, 'graph'):
                self.logger.warning("No graph available for storage")
                return {
                    'stored': False,
                    'reason': 'No graph available'
                }

            graph = self.runtime.graph

            try:
                # Build node data
                node_data = {
                    'type': 'execution_result',
                    'result': result,
                    'metadata': {
                        **metadata,
                        'timestamp': datetime.now().isoformat(),
                        'pattern_id': context.get('pattern_id'),
                        'stored_by': 'meta_pattern'
                    }
                }

                # Add node to graph
                node_id = graph.add_node(**node_data)

                # Connect to pattern node if exists
                pattern_id = context.get('pattern_id')
                if pattern_id:
                    pattern_nodes = graph.get_nodes_by_type('pattern')
                    for pid, pdata in pattern_nodes.items():
                        if pdata.get('id') == pattern_id:
                            graph.connect(node_id, pid, 'executed_by')
                            break

                self.logger.debug(f"Stored result in graph: {node_id}")

                return {
                    'stored': True,
                    'node_id': node_id,
                    'timestamp': node_data['metadata']['timestamp']
                }

            except Exception as e:
                self.logger.error(f"Failed to store in graph: {e}")
                return {
                    'stored': False,
                    'error': str(e)
                }
```

**Scope Notes**:
- Simple node creation
- No complex relationships
- No graph validation
- Just store and link

**Test**:
```python
def test_store_in_graph():
    """Test store_in_graph action"""
    engine = PatternEngine('dawsos/patterns', runtime)

    storage_result = engine.execute_action(
        'store_in_graph',
        {
            'result': {'success': True, 'data': 'test'},
            'metadata': {'source': 'test'}
        },
        {'pattern_id': 'test_pattern'},
        {}
    )

    assert storage_result['stored'] == True
    assert 'node_id' in storage_result

    # Verify node exists in graph
    node = runtime.graph.get_node(storage_result['node_id'])
    assert node is not None
    assert node['data']['type'] == 'execution_result'

    print("✅ store_in_graph tests passed")
```

#### Step 2.8: Integration Test (30 min)
**Test all 4 actions together**:

```python
# tests/validation/test_meta_actions_integration.py
def test_meta_executor_full_flow():
    """Test complete meta_executor pattern with all actions"""
    from core.universal_executor import UniversalExecutor

    executor = UniversalExecutor(graph, registry, runtime)

    # Execute a request that should go through meta_executor
    request = {
        'type': 'analysis',
        'user_input': 'analyze moat for AAPL',
        'symbol': 'AAPL'
    }

    result = executor.execute(request)

    # Verify it didn't use fallback
    assert result.get('fallback_mode') != True, "Should not use fallback"

    # Verify routing happened
    assert 'pattern_routed' in result or 'migrated' in result

    # Check graph storage
    assert result.get('graph_stored', False), "Should store in graph"

    print("✅ Meta executor integration test passed")
```

**Run**:
```bash
pytest tests/validation/test_meta_actions_integration.py -v
```

#### Step 2.9: Manual App Test (20 min)
**Action**: Test in running app

```bash
# Start app
streamlit run dawsos/main.py

# In UI:
# 1. Go to Chat tab
# 2. Enter: "analyze moat for Apple"
# 3. Check logs for "Routing decision: pattern" (not "using fallback")
# 4. Verify response appears
```

**Check Logs**:
```bash
tail -50 dawsos/logs/PatternEngine_*.log | grep -i "routing\|fallback"
# Should see: "Routing decision:" messages
# Should NOT see: "using fallback execution" (or only rarely)
```

#### Step 2.10: Commit (10 min)
```bash
git add dawsos/core/pattern_engine.py tests/validation/test_meta_actions*.py
git commit -m "feat: implement meta pattern action handlers

Adds 4 action handlers for Trinity meta patterns:
- select_router: Determines routing strategy (pattern/agent/direct)
- execute_pattern: Nested pattern execution with recursion guard
- track_execution: Telemetry tracking with timing
- store_in_graph: Result persistence in knowledge graph

Each handler:
- Minimal implementation (no feature creep)
- Error handling
- Logging for observability
- Unit tested

Fixes #2 from GAP_ANALYSIS_CRITICAL.md
UniversalExecutor can now route through meta_executor instead of fallback"
```

### Deliverables
- ✅ 4 action handlers implemented in `pattern_engine.py`
- ✅ Unit tests for each handler
- ✅ Integration test for full flow
- ✅ Manual app test confirms routing works
- ✅ Git commit with tested code

### Rollback Procedure
```bash
cp dawsos/core/pattern_engine.py.backup.* dawsos/core/pattern_engine.py
git checkout dawsos/core/pattern_engine.py tests/validation/test_meta_actions*.py
pytest tests/validation/ -v  # Ensure old tests still pass
```

### Success Criteria
- [ ] All 4 action handlers implemented
- [ ] All unit tests pass
- [ ] Integration test passes
- [ ] App logs show "Routing decision:" (not "using fallback")
- [ ] No regressions in existing patterns

---

## Phase 3: Agent Count Alignment (Agent Orchestrator)

**Duration**: 2 hours
**Risk**: Low (documentation updates + optional agent restoration)
**Agent**: 🤖 Agent Orchestrator

### Objective
Align agent count in documentation with reality (15 agents registered).

### Current Problem
- Docs claim 15 agents (consolidated from 19 in Oct 2025)
- Only 15 registered in main.py
- 4 agents (equity, macro, risk, +1?) missing

### Scope Boundaries
- ✅ Update all docs to say "15 agents"
- ✅ Option: Restore missing agents if simple
- ✅ Update AGENT_CAPABILITIES comment
- ❌ NO new agent development
- ❌ NO agent refactoring
- ❌ NO capability system changes

### Detailed Steps

#### Step 3.1: Read Agent Orchestrator Guide (10 min)
```bash
cat .claude/agent_orchestrator.md | grep -A 10 "Registered Agents"
```

#### Step 3.2: Audit Actual Agent Count (15 min)
**Action**: List registered agents

```bash
# Method 1: Count registrations in main.py
grep "register_agent" dawsos/main.py | grep -v "#" | wc -l
# Output: 15

# Method 2: List agent names
grep "register_agent" dawsos/main.py | grep -v "#" | sed "s/.*register_agent('\(.*\)',.*/\1/" | sort
```

**Expected Output**:
```
claude
code_monkey
data_digester
data_harvester
financial_analyst
forecast_dreamer
governance_agent
graph_mind
pattern_spotter
refactor_elf
relationship_hunter
structure_bot
ui_generator
workflow_player
workflow_recorder
```

**Count**: 15 agents

#### Step 3.3: Identify Missing Agents (15 min)
**Action**: Check AGENT_CAPABILITIES vs registrations

```bash
# Get all agents in AGENT_CAPABILITIES
grep "^    '[a-z_]*': {$" dawsos/core/agent_capabilities.py | sed "s/.*'\(.*\)'.*/\1/" | sort > /tmp/caps_agents.txt

# Get registered agents
grep "register_agent" dawsos/main.py | sed "s/.*register_agent('\(.*\)',.*/\1/" | sort > /tmp/registered_agents.txt

# Find difference
comm -23 /tmp/caps_agents.txt /tmp/registered_agents.txt
```

**Expected Missing** (if any documented but not registered):
- Check if equity_agent, macro_agent, risk_agent in capabilities file
- If yes, they're the missing agents

#### Step 3.4: Decision Point - Restore or Document? (10 min)
**Check if missing agents exist in codebase**:

```bash
# Search for agent files
find dawsos -name "*equity*agent*.py" 2>/dev/null
find dawsos -name "*macro*agent*.py" 2>/dev/null
find dawsos -name "*risk*agent*.py" 2>/dev/null

# Check archived
find dawsos/archived_legacy -name "*.py" 2>/dev/null
```

**Decision Logic**:
- **If agents exist** in dawsos/agents/ → Option A: Restore (30 min effort)
- **If agents in archived_legacy/** → Option B: Leave archived, update docs (15 min effort)
- **If agents don't exist** → Option C: Remove from AGENT_CAPABILITIES (10 min effort)

**Recommendation**: Option C (Remove from capabilities) - Cleanest, no code risk

#### Step 3.5: Option C - Remove from AGENT_CAPABILITIES (20 min)
**Action**: Update capabilities file to match reality

**File**: `dawsos/core/agent_capabilities.py`

**Change Line 10**:
```python
# Before
# Complete capability definitions for all 15 agents (consolidated from 19 in Oct 2025)

# After
# Complete capability definitions for all 15 agents
```

**If missing agents found**: Remove their sections from AGENT_CAPABILITIES dict

**Example**:
```python
# If equity_agent in file but not registered, remove:
# 'equity_agent': {
#     'description': '...',
#     ...
# },
```

**Scope Constraint**: ONLY remove agents that aren't registered. Don't:
- Modify registered agent capabilities
- Change capability structure
- Add new capabilities

#### Step 3.6: Update Specialist Agent Docs (30 min)
**Files to Update** (search/replace "15 agents (consolidated from 19 in Oct 2025)" → "15 agents"):

1. `.claude/trinity_architect.md`
```bash
sed -i '' 's/19+ agents/15 agents/g' .claude/trinity_architect.md
sed -i '' 's/15 agents (consolidated from 19 in Oct 2025)/15 agents/g' .claude/trinity_architect.md
```

2. `.claude/agent_orchestrator.md`
```bash
sed -i '' 's/all 15 agents (consolidated from 19 in Oct 2025)/all 15 agents/g' .claude/agent_orchestrator.md
sed -i '' 's/across 15 agents (consolidated from 19 in Oct 2025)/across 15 agents/g' .claude/agent_orchestrator.md
```

3. `.claude/README.md`
```bash
sed -i '' 's/All 15/All 15/g' .claude/README.md
sed -i '' 's/19 registered agents/15 registered agents/g' .claude/README.md
```

4. `CLAUDE.md`
```bash
sed -i '' 's/15 agents (consolidated from 19 in Oct 2025)/15 agents/g' CLAUDE.md
sed -i '' 's/across 15 agents (consolidated from 19 in Oct 2025)/across 15 agents/g' CLAUDE.md
```

5. `SYSTEM_STATUS.md`
```bash
sed -i '' 's/**Agents**: 19/**Agents**: 15/g' SYSTEM_STATUS.md
```

6. `CAPABILITY_ROUTING_GUIDE.md`
```bash
sed -i '' 's/50+ capabilities across 15 agents (consolidated from 19 in Oct 2025)/50+ capabilities across 15 agents/g' CAPABILITY_ROUTING_GUIDE.md
```

**Validation**:
```bash
# Verify no "15 agents (consolidated from 19 in Oct 2025)" remain (except in archived docs)
grep -r "15 agents (consolidated from 19 in Oct 2025)" . --include="*.md" --exclude-dir=archived_legacy --exclude-dir=docs/reports
# Should be: No matches (or only in historical/archived contexts)
```

#### Step 3.7: Update Registered Agents List (15 min)
**File**: `.claude/agent_orchestrator.md`

**Update "Registered Agents (19)" section** to list actual 15:

```markdown
## Registered Agents (15)

### Core Agents
- **claude** - Natural language orchestration
- **graph_mind** - Knowledge graph operations
- **data_harvester** - External data fetching
- **data_digester** - Raw data transformation

### Analysis Agents
- **relationship_hunter** - Correlation analysis
- **pattern_spotter** - Pattern detection
- **forecast_dreamer** - Predictions
- **financial_analyst** - Financial metrics (DCF, ROIC, FCF)

### Development Agents
- **code_monkey** - Code generation
- **structure_bot** - Code organization
- **refactor_elf** - Code refactoring

### Workflow Agents
- **workflow_recorder** - Workflow learning
- **workflow_player** - Workflow replay

### Utility Agents
- **ui_generator** - UI generation
- **governance_agent** - Compliance checking
```

**Remove sections** for agents that don't exist (if any were documented)

#### Step 3.8: Test Agent Count Accuracy (10 min)
**Create verification script**:

```python
# tests/validation/test_agent_count.py
def test_agent_count_matches_docs():
    """Verify registered agent count matches documentation"""
    from core.agent_runtime import AgentRuntime
    from core.agent_capabilities import AGENT_CAPABILITIES

    runtime = AgentRuntime()
    # ... register agents (copy from main.py) ...

    registered_count = len(runtime.agent_registry.list_agents())
    documented_count = len(AGENT_CAPABILITIES)

    assert registered_count == documented_count, \
        f"Mismatch: {registered_count} registered vs {documented_count} in AGENT_CAPABILITIES"

    assert registered_count == 15, f"Expected 15 agents, got {registered_count}"

    print(f"✅ Agent count accurate: {registered_count}")

if __name__ == '__main__':
    test_agent_count_matches_docs()
```

**Run**:
```bash
python tests/validation/test_agent_count.py
```

#### Step 3.9: Commit (5 min)
```bash
git add dawsos/core/agent_capabilities.py .claude/*.md CLAUDE.md SYSTEM_STATUS.md CAPABILITY_ROUTING_GUIDE.md tests/validation/test_agent_count.py
git commit -m "docs: align agent count with reality (15 agents)

- Update AGENT_CAPABILITIES comment: 19 → 15
- Remove references to unregistered agents (if any)
- Update all specialist agent docs (.claude/*.md)
- Update CLAUDE.md, SYSTEM_STATUS.md, CAPABILITY_ROUTING_GUIDE.md
- Add test to verify count accuracy

Fixes #3 from GAP_ANALYSIS_CRITICAL.md
Documentation now accurately reflects 15 registered agents"
```

### Deliverables
- ✅ AGENT_CAPABILITIES updated to 15
- ✅ All docs updated (search/replace complete)
- ✅ Registered agents list accurate
- ✅ Test verifies count matches
- ✅ Git commit with documentation alignment

### Rollback Procedure
```bash
git checkout dawsos/core/agent_capabilities.py .claude/*.md CLAUDE.md SYSTEM_STATUS.md
# Revert to "15 agents (consolidated from 19 in Oct 2025)" if needed
```

### Success Criteria
- [ ] `grep -r "15 agents (consolidated from 19 in Oct 2025)"` returns no matches (except archives)
- [ ] AGENT_CAPABILITIES comment says "15 agents"
- [ ] test_agent_count.py passes
- [ ] All specialist agent docs list 15 agents

---

## Phase 4: PatternEngine Graph Reference (Knowledge Curator)

**Duration**: 1 hour
**Risk**: Low (simple parameter addition)
**Agent**: 📚 Knowledge Curator

### Objective
Pass graph reference to PatternEngine so enriched lookups work.

### Current Problem
```python
# dawsos/core/pattern_engine.py:19
def __init__(self, pattern_dir: str = 'patterns', runtime=None):
    # No graph parameter

# dawsos/core/pattern_engine.py:420
if hasattr(self, 'graph') and self.graph:
    # Always fails - no graph attribute
```

### Scope Boundaries
- ✅ Add graph parameter to PatternEngine.__init__
- ✅ Update main.py to pass graph
- ✅ Test enriched lookups work
- ❌ NO changes to enriched lookup logic
- ❌ NO new graph operations
- ❌ NO graph refactoring

### Detailed Steps

#### Step 4.1: Read Knowledge Curator Guide (10 min)
```bash
cat .claude/knowledge_curator.md | grep -A 10 "PatternEngine"
```

#### Step 4.2: Backup Files (2 min)
```bash
cp dawsos/core/pattern_engine.py dawsos/core/pattern_engine.py.backup.$(date +%Y%m%d_%H%M%S)
cp dawsos/main.py dawsos/main.py.backup.$(date +%Y%m%d_%H%M%S)
```

#### Step 4.3: Update PatternEngine.__init__ (10 min)
**File**: `dawsos/core/pattern_engine.py`
**Line**: 19

**Change**:
```python
# Before
def __init__(self, pattern_dir: str = 'patterns', runtime=None):
    """
    Initialize the Pattern Engine

    Args:
        pattern_dir: Directory containing pattern JSON files
        runtime: AgentRuntime instance for executing agents
    """
    # ... existing code ...
    self.runtime = runtime
    # Missing: self.graph = ?

# After
def __init__(self, pattern_dir: str = 'patterns', runtime=None, graph=None):
    """
    Initialize the Pattern Engine

    Args:
        pattern_dir: Directory containing pattern JSON files
        runtime: AgentRuntime instance for executing agents
        graph: KnowledgeGraph instance for enriched lookups (optional)
    """
    # ... existing code ...
    self.runtime = runtime

    # Get graph from runtime or use provided
    self.graph = graph if graph is not None else (runtime.graph if runtime and hasattr(runtime, 'graph') else None)
```

**Scope Constraint**: ONLY add graph parameter and assignment. Don't:
- Change existing initialization logic
- Modify pattern loading
- Add new graph operations
- Refactor __init__ structure

#### Step 4.4: Update main.py Registration (10 min)
**File**: `dawsos/main.py`
**Line**: 204

**Change**:
```python
# Before
runtime.pattern_engine = PatternEngine('dawsos/patterns', runtime)

# After
runtime.pattern_engine = PatternEngine(
    'dawsos/patterns',
    runtime=runtime,
    graph=st.session_state.graph  # ADD THIS
)
```

**Validation**: Check no other PatternEngine instantiations
```bash
grep -n "PatternEngine(" dawsos/**/*.py
# Should only be main.py and tests
```

#### Step 4.5: Update UniversalExecutor (if needed) (10 min)
**Check if UniversalExecutor creates PatternEngine**:

```bash
grep -n "PatternEngine(" dawsos/core/universal_executor.py
```

**If found**: Update those instantiations too
```python
# Add graph parameter
self.pattern_engine = PatternEngine(pattern_dir, runtime, graph=self.graph)
```

#### Step 4.6: Test Enriched Lookup (15 min)
**Create test for graph-backed lookups**:

```python
# tests/validation/test_pattern_graph_lookup.py
def test_pattern_engine_has_graph():
    """Verify PatternEngine receives graph reference"""
    from core.knowledge_graph import KnowledgeGraph
    from core.agent_runtime import AgentRuntime
    from core.pattern_engine import PatternEngine

    graph = KnowledgeGraph()
    runtime = AgentRuntime()
    runtime.graph = graph

    # Test 1: Explicit graph parameter
    engine = PatternEngine('dawsos/patterns', runtime, graph=graph)
    assert engine.graph is not None, "Graph should be set"
    assert engine.graph is graph, "Should be same graph instance"

    # Test 2: Graph from runtime
    engine2 = PatternEngine('dawsos/patterns', runtime)
    assert engine2.graph is not None, "Should get graph from runtime"

    print("✅ PatternEngine graph reference test passed")

def test_enriched_lookup_with_graph():
    """Test enriched_lookup action can access graph"""
    # ... setup ...

    # Add test node to graph
    graph.add_node('test_enriched_data', type='enriched', data={'value': 'test'})

    engine = PatternEngine('dawsos/patterns', runtime, graph=graph)

    # Attempt enriched lookup
    result = engine.execute_action(
        'enriched_lookup',
        {'node_type': 'enriched'},
        {},
        {}
    )

    # Should succeed (not AttributeError)
    assert 'error' not in result or 'AttributeError' not in str(result.get('error'))

    print("✅ Enriched lookup with graph test passed")
```

**Run**:
```bash
python tests/validation/test_pattern_graph_lookup.py
```

#### Step 4.7: Manual App Test (10 min)
**Action**: Test enriched lookup in app

```bash
streamlit run dawsos/main.py

# In UI:
# 1. Go to Chat
# 2. Enter query that uses enriched data: "what sectors perform best in expansion?"
# 3. Check response includes sector data
# 4. Check logs for NO AttributeError about 'graph'
```

**Check Logs**:
```bash
tail -100 dawsos/logs/PatternEngine_*.log | grep -i "error\|attribute"
# Should NOT see: AttributeError: 'PatternEngine' object has no attribute 'graph'
```

#### Step 4.8: Commit (3 min)
```bash
git add dawsos/core/pattern_engine.py dawsos/main.py dawsos/core/universal_executor.py tests/validation/test_pattern_graph_lookup.py
git commit -m "fix: add graph reference to PatternEngine

- Add optional graph parameter to PatternEngine.__init__
- Falls back to runtime.graph if not provided
- Update main.py to explicitly pass graph
- Update UniversalExecutor if applicable
- Add tests for graph reference and enriched lookups

Fixes #4 from GAP_ANALYSIS_CRITICAL.md
Enriched graph lookups now functional (no AttributeError)"
```

### Deliverables
- ✅ PatternEngine.__init__ accepts graph parameter
- ✅ main.py passes graph to PatternEngine
- ✅ Tests verify graph reference works
- ✅ No AttributeError in logs
- ✅ Git commit with simple change

### Rollback Procedure
```bash
cp dawsos/core/pattern_engine.py.backup.* dawsos/core/pattern_engine.py
cp dawsos/main.py.backup.* dawsos/main.py
git checkout dawsos/core/pattern_engine.py dawsos/main.py
```

### Success Criteria
- [ ] `hasattr(pattern_engine, 'graph')` returns True
- [ ] Enriched lookup test passes
- [ ] No AttributeError in application logs
- [ ] Manual enriched query works in UI

---

## Phase 5: CI, Visualization, Recovery Fixes (Trinity Architect)

**Duration**: 3 hours
**Risk**: Low (independent fixes)
**Agent**: 🏛️ Trinity Architect

### Objective
Fix 3 remaining issues: CI path, graph visualization bug, execute_pattern signature.

### Scope Boundaries
- ✅ Fix CI patterns path
- ✅ Fix graph visualization edge rendering
- ✅ Fix execute_pattern signature in recovery
- ❌ NO CI infrastructure changes beyond path
- ❌ NO graph visualization redesign
- ❌ NO new recovery strategies

### Detailed Steps

#### Fix 5.1: CI Patterns Path (45 min)

**File**: `.github/workflows/compliance-check.yml`

**Step 5.1.1: Backup** (2 min)
```bash
cp .github/workflows/compliance-check.yml .github/workflows/compliance-check.yml.backup.$(date +%Y%m%d_%H%M%S)
```

**Step 5.1.2: Fix Path** (10 min)
**Line**: 9

**Change**:
```yaml
# Before
paths:
  - 'dawsos/**/*.py'
  - 'patterns/**/*.json'  # WRONG PATH

# After
paths:
  - 'dawsos/**/*.py'
  - 'dawsos/patterns/**/*.json'  # FIXED
  - 'scripts/check_compliance.py'
```

**Step 5.1.3: Add Pattern Lint Job** (15 min)
**Add after existing jobs**:

```yaml
  validate-patterns:
    name: Validate Patterns
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Lint patterns
        run: |
          python scripts/lint_patterns.py
          if [ $? -ne 0 ]; then
            echo "❌ Pattern linting failed"
            exit 1
          fi
          echo "✅ All patterns valid"
```

**Scope Constraint**: Only add pattern validation. Don't:
- Add new linting rules
- Change existing jobs
- Add performance tests
- Add deployment steps

**Step 5.1.4: Test CI Locally** (15 min)
**Use act to test GitHub Actions locally** (if available):

```bash
# If act installed: https://github.com/nektos/act
act pull_request

# Otherwise, commit to test branch and push
git checkout -b test/ci-fix
git add .github/workflows/compliance-check.yml
git commit -m "test: CI patterns path fix"
git push origin test/ci-fix
# Check GitHub Actions tab
```

**Step 5.1.5: Commit** (3 min)
```bash
git checkout main  # Or your working branch
git add .github/workflows/compliance-check.yml
git commit -m "fix: correct CI patterns path and add validation job

- Change patterns/**/*.json → dawsos/patterns/**/*.json
- Add validate-patterns job to lint patterns on PR/push
- Fail build if pattern linting errors

Fixes #5 from GAP_ANALYSIS_CRITICAL.md
CI now validates patterns in correct directory"
```

#### Fix 5.2: Graph Visualization Bug (45 min)

**File**: `dawsos/main.py`

**Step 5.2.1: Locate Bug** (5 min)
```bash
grep -n "edge_data = graph.edges\[0\]" dawsos/main.py
# Line 267
```

**Step 5.2.2: Backup** (2 min)
```bash
# Already backed up in Phase 4
```

**Step 5.2.3: Fix Edge Rendering** (15 min)
**Line**: 267

**Change**:
```python
# Before (WRONG)
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_data = graph.edges[0]  # BUG: Always uses first edge

    # Color based on relationship type

# After (FIXED)
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]

    # Find the correct edge data for this edge
    edge_data = next(
        (e for e in graph.edges
         if e['from'] == edge[0] and e['to'] == edge[1]),
        None
    )

    # Fallback if edge not found (shouldn't happen)
    if edge_data is None:
        edge_data = {'type': 'unknown', 'strength': 0.5}

    # Color based on relationship type (now using CORRECT edge)
```

**Scope Constraint**: ONLY fix edge data lookup. Don't:
- Change visualization layout
- Add new edge properties
- Modify color scheme
- Refactor visualization code

**Step 5.2.4: Test Visualization** (20 min)
**Action**: Visual test in app

```bash
streamlit run dawsos/main.py

# 1. Add diverse edges to graph (via Governance tab or code):
# - Correlates edge (should be one color)
# - Part_of edge (should be different color)
# - Influences edge (should be another color)

# 2. Go to Graph Visualization tab

# 3. Verify:
# - Different edge types have different colors
# - Hover shows correct strength for each edge
# - No edges displaying wrong data
```

**Create Test Data** (if needed):
```python
# In Python console or temporary script
from core.knowledge_graph import KnowledgeGraph

graph = KnowledgeGraph()
graph.add_node('test_node_a', type='test', data={'name': 'A'})
graph.add_node('test_node_b', type='test', data={'name': 'B'})
graph.add_node('test_node_c', type='test', data={'name': 'C'})

graph.connect('test_node_a', 'test_node_b', 'correlates', strength=0.9)
graph.connect('test_node_b', 'test_node_c', 'influences', strength=0.5)
graph.connect('test_node_a', 'test_node_c', 'part_of', strength=1.0)

graph.save('storage/graph.json')
```

**Step 5.2.5: Commit** (3 min)
```bash
git add dawsos/main.py
git commit -m "fix: correct graph visualization edge data lookup

- Change edge_data = graph.edges[0] to find correct edge
- Use next() with generator to match edge by from/to nodes
- Add fallback for safety (shouldn't occur)

Fixes #6 from GAP_ANALYSIS_CRITICAL.md
Graph edges now display correct type, strength, and properties"
```

#### Fix 5.3: execute_pattern Signature (45 min)

**File**: `dawsos/core/universal_executor.py`

**Step 5.3.1: Locate Issues** (5 min)
```bash
grep -n "execute_pattern(" dawsos/core/universal_executor.py
# Lines: 222, 251
```

**Step 5.3.2: Review Signature** (5 min)
```bash
grep -A 3 "def execute_pattern" dawsos/core/pattern_engine.py
# Output:
# def execute_pattern(self, pattern: Dict, context: Dict) -> Dict:
#     """Execute a pattern with given context"""
```

**Signature**: `execute_pattern(pattern_object, context_dict)`
**NOT**: `execute_pattern(pattern_name='...', context=...)`

**Step 5.3.3: Fix Line 222** (15 min)
**File**: `dawsos/core/universal_executor.py`
**Method**: `_attempt_recovery`

**Change**:
```python
# Before (WRONG)
if self.pattern_engine.has_pattern('architecture_validator'):
    recovery_context = {
        'request': request,
        'error': error,
        'recovery_mode': True
    }

    result = self.pattern_engine.execute_pattern(
        pattern_name='architecture_validator',  # WRONG: keyword arg
        context=recovery_context
    )

# After (FIXED)
if self.pattern_engine.has_pattern('architecture_validator'):
    recovery_context = {
        'request': request,
        'error': error,
        'recovery_mode': True
    }

    # Get pattern object first
    pattern = self.pattern_engine.get_pattern('architecture_validator')
    if pattern:
        result = self.pattern_engine.execute_pattern(
            pattern,  # FIXED: positional arg (pattern object)
            recovery_context
        )
    else:
        logger.error("architecture_validator pattern not found despite has_pattern check")
        result = None
```

**Step 5.3.4: Fix Line 251** (10 min)
**Method**: `validate_architecture`

**Change**:
```python
# Before (WRONG)
def validate_architecture(self) -> Dict[str, Any]:
    """Run architecture validation."""
    try:
        result = self.pattern_engine.execute_pattern(
            pattern_name='architecture_validator',  # WRONG
            context={'startup': False}
        )
        return result

# After (FIXED)
def validate_architecture(self) -> Dict[str, Any]:
    """Run architecture validation."""
    try:
        pattern = self.pattern_engine.get_pattern('architecture_validator')
        if not pattern:
            return {'success': False, 'error': 'architecture_validator pattern not found'}

        result = self.pattern_engine.execute_pattern(
            pattern,  # FIXED
            {'startup': False}
        )
        return result
```

**Scope Constraint**: ONLY fix calling convention. Don't:
- Add new recovery strategies
- Modify pattern execution logic
- Add caching
- Refactor error handling

**Step 5.3.5: Test Recovery** (15 min)
**Create test for recovery path**:

```python
# tests/validation/test_recovery.py
def test_recovery_path():
    """Test error recovery uses correct execute_pattern signature"""
    from core.universal_executor import UniversalExecutor

    executor = UniversalExecutor(graph, registry, runtime)

    # Trigger error that should invoke recovery
    bad_request = {
        'type': 'invalid',
        'force_error': True
    }

    # This should attempt recovery (not raise TypeError)
    result = executor.execute(bad_request)

    # Verify no TypeError from execute_pattern
    assert 'TypeError' not in str(result.get('error', '')), \
        "Recovery should not raise TypeError"

    # Verify recovery attempted
    assert result.get('recovery_attempted') == True or result.get('fallback_mode') == True

    print("✅ Recovery path test passed")
```

**Run**:
```bash
python tests/validation/test_recovery.py
```

**Step 5.3.6: Commit** (3 min)
```bash
git add dawsos/core/universal_executor.py tests/validation/test_recovery.py
git commit -m "fix: correct execute_pattern signature in recovery paths

- Change execute_pattern(pattern_name='...') to execute_pattern(pattern_obj, context)
- Fix _attempt_recovery (line 222)
- Fix validate_architecture (line 251)
- Add test for recovery path

Fixes #7 from GAP_ANALYSIS_CRITICAL.md
Error recovery now functional (no TypeError)"
```

### Deliverables
- ✅ CI patterns path fixed + validation job added
- ✅ Graph visualization edge lookup corrected
- ✅ execute_pattern signature fixed (2 locations)
- ✅ Tests for recovery path
- ✅ 3 git commits (one per fix)

### Rollback Procedure
```bash
# CI fix
cp .github/workflows/compliance-check.yml.backup.* .github/workflows/compliance-check.yml

# Graph viz fix
git checkout dawsos/main.py  # (or restore from Phase 4 backup)

# Recovery fix
git checkout dawsos/core/universal_executor.py
```

### Success Criteria
- [ ] CI validates patterns on push (check GitHub Actions)
- [ ] Graph edges display different colors for different types
- [ ] Recovery test passes (no TypeError)
- [ ] All 3 fixes verified independently

---

## Phase 6: Testing, Persistence, Documentation (All Agents)

**Duration**: 4.5 hours
**Risk**: Low (final integration and cleanup)
**Agents**: All 4 specialists

### Objective
Wire up persistence, convert tests, update documentation to reflect true A+ grade.

### Scope Boundaries
- ✅ Wire PersistenceManager to production path
- ✅ Convert print-based tests to assertions
- ✅ Update all documentation to reflect fixes
- ❌ NO new persistence features
- ❌ NO test coverage expansion beyond conversion
- ❌ NO new documentation sections

### Detailed Steps

#### Sub-Phase 6.1: Wire Persistence (1 hour - Knowledge Curator)

**Step 6.1.1: Add Save Helper** (20 min)
**File**: `dawsos/main.py`
**Location**: After initialize_session_state()

**Add Function**:
```python
def save_graph_with_persistence():
    """
    Save graph with backup and rotation.
    Called when graph changes or on app exit.
    """
    if 'persistence' not in st.session_state or 'graph' not in st.session_state:
        return

    try:
        pm = st.session_state.persistence
        graph = st.session_state.graph

        # Save with backup
        pm.save_graph_with_backup(graph)

        # Rotate old backups (>30 days)
        pm.rotate_old_backups(days=30)

        logger.info("Graph saved with persistence and rotation")

    except Exception as e:
        logger.error(f"Failed to save with persistence: {e}")
```

**Step 6.1.2: Add Exit Hook** (15 min)
**Add atexit handler**:

```python
import atexit

# In initialize_session_state() or after it:
if 'persistence_registered' not in st.session_state:
    atexit.register(save_graph_with_persistence)
    st.session_state.persistence_registered = True
```

**Step 6.1.3: Add UI Save Button** (20 min)
**File**: `dawsos/ui/governance_tab.py`
**Location**: In governance tab UI

**Add Button**:
```python
st.subheader("💾 Persistence")

col1, col2 = st.columns(2)

with col1:
    if st.button("Save Graph with Backup"):
        try:
            from dawsos.main import save_graph_with_persistence
            save_graph_with_persistence()
            st.success("✅ Graph saved with backup and rotation")
        except Exception as e:
            st.error(f"❌ Save failed: {e}")

with col2:
    if st.button("View Backups"):
        backups = list(Path('dawsos/storage/backups').glob('*.json'))
        st.write(f"Found {len(backups)} backups:")
        for backup in sorted(backups, reverse=True)[:10]:
            st.text(f"  {backup.name}")
```

**Step 6.1.4: Test Persistence** (15 min)
```bash
streamlit run dawsos/main.py

# 1. Go to Governance tab
# 2. Click "Save Graph with Backup"
# 3. Check: ls -la dawsos/storage/backups/*.json
# 4. Verify: New backup file created with timestamp
# 5. Verify: .meta file created with checksum
```

**Step 6.1.5: Commit** (5 min)
```bash
git add dawsos/main.py dawsos/ui/governance_tab.py
git commit -m "feat: wire PersistenceManager to production paths

- Add save_graph_with_persistence() helper
- Register atexit hook for auto-save on app exit
- Add 'Save Graph with Backup' button in Governance UI
- Call rotate_old_backups(days=30) on each save

Fixes #8 from GAP_ANALYSIS_CRITICAL.md
Backup rotation now functional (not just instantiated)"
```

#### Sub-Phase 6.2: Convert Test Scripts (2 hours - Trinity Architect)

**Step 6.2.1: Identify Print-Based Tests** (15 min)
```bash
# Find tests with print statements
grep -l "print(" dawsos/tests/validation/*.py | sort

# Count print vs assert ratio
for file in dawsos/tests/validation/*.py; do
    prints=$(grep -c "print(" "$file" 2>/dev/null || echo 0)
    asserts=$(grep -c "assert " "$file" 2>/dev/null || echo 0)
    echo "$file: $prints prints, $asserts asserts"
done
```

**Step 6.2.2: Convert test_all_patterns.py** (30 min)
**File**: `dawsos/tests/validation/test_all_patterns.py`

**Before**:
```python
def test_patterns():
    print("Testing patterns...")
    for pattern in patterns:
        print(f"✅ {pattern['id']}")
```

**After**:
```python
def test_all_patterns_load():
    """Verify all patterns load and have required fields"""
    from core.pattern_engine import PatternEngine
    from core.agent_runtime import AgentRuntime

    runtime = AgentRuntime()
    engine = PatternEngine('dawsos/patterns', runtime)

    # Assert count
    assert len(engine.patterns) == 45, f"Expected 45 patterns, got {len(engine.patterns)}"

    # Assert each pattern valid
    for pattern_id, pattern in engine.patterns.items():
        assert 'id' in pattern, f"Pattern {pattern_id} missing 'id'"
        assert 'name' in pattern, f"Pattern {pattern_id} missing 'name'"
        assert 'version' in pattern, f"Pattern {pattern_id} missing 'version'"
        assert 'steps' in pattern or 'workflow' in pattern, \
            f"Pattern {pattern_id} missing 'steps' or 'workflow'"

def test_patterns_reference_valid_agents():
    """Verify patterns only reference registered agents"""
    from core.pattern_engine import PatternEngine
    from core.agent_runtime import AgentRuntime

    runtime = AgentRuntime()
    # ... register agents ...

    engine = PatternEngine('dawsos/patterns', runtime)
    registered_agents = set(runtime.agent_registry.list_agents())

    invalid_refs = []
    for pattern_id, pattern in engine.patterns.items():
        for step in pattern.get('steps', []):
            if 'agent' in step:
                agent_name = step['agent']
                if agent_name not in registered_agents:
                    invalid_refs.append((pattern_id, agent_name))

    assert len(invalid_refs) == 0, \
        f"Patterns reference invalid agents: {invalid_refs}"
```

**Step 6.2.3: Convert test_system_health.py** (30 min)
**Similar pattern**: Replace prints with assertions

**Step 6.2.4: Convert test_integration.py** (30 min)
**Focus**: End-to-end flow assertions

**Step 6.2.5: Run Converted Tests** (20 min)
```bash
pytest dawsos/tests/validation/ -v --tb=short
# All tests should pass with assertions
```

**Step 6.2.6: Commit** (5 min)
```bash
git add dawsos/tests/validation/*.py
git commit -m "test: convert print-based tests to assertions

- Replace print() statements with assert statements
- Add specific error messages to assertions
- Test pattern count, required fields, agent references
- Test integration flows with assertions

Fixes #9 from GAP_ANALYSIS_CRITICAL.md
Tests now fail in CI if conditions not met (not just visual inspection)"
```

#### Sub-Phase 6.3: Update Documentation (1.5 hours - All Agents)

**Step 6.3.1: Update SYSTEM_STATUS.md** (30 min - Trinity Architect)
**File**: `SYSTEM_STATUS.md`

**Changes**:
```markdown
# DawsOS System Status

**Grade**: A+ (98/100) ✅ VERIFIED
**Version**: 2.0.0
**Last Verified**: October 3, 2025

## Recent Fixes (Option A Execution)

### Critical Issues Resolved ✅
1. ✅ UniversalExecutor meta pattern path corrected
2. ✅ Meta pattern actions implemented (select_router, execute_pattern, track_execution, store_in_graph)
3. ✅ Agent count aligned (15 agents, documentation accurate)
4. ✅ PatternEngine graph reference added (enriched lookups functional)
5. ✅ CI patterns path fixed (validation on push)
6. ✅ Graph visualization edge rendering corrected
7. ✅ execute_pattern signature fixed in recovery paths
8. ✅ PersistenceManager wired to production (backups functional)
9. ✅ Tests converted to assertions (CI can catch failures)

### System Metrics ✅ ACCURATE
- **Agents**: 15 registered with capabilities
- **Patterns**: 45 (0 errors)
- **Datasets**: 26 (100% coverage)
- **Tests**: All passing with assertions
- **CI/CD**: Validates patterns on push
- **Trinity Compliance**: 100% (meta routing functional)

### Architecture Components ✅ FUNCTIONAL
1. **UniversalExecutor**: Routes through meta_executor (not fallback) ✅
2. **PatternEngine**: Has graph reference, enriched lookups work ✅
3. **AgentRuntime**: 15 agents registered with AGENT_CAPABILITIES ✅
4. **KnowledgeLoader**: 26 datasets, 30-min TTL cache ✅
5. **PersistenceManager**: Auto-saves with 30-day rotation ✅
6. **CI/CD**: Validates dawsos/patterns/**/*.json ✅
```

**Step 6.3.2: Create FIXES_COMPLETE.md** (20 min - Trinity Architect)
**New File**: `FIXES_COMPLETE.md`

**Content**: Summary of all 9 fixes with before/after, test results, git commits

**Step 6.3.3: Update Specialist Agent Docs** (30 min - Each Agent)

**Trinity Architect** (`.claude/trinity_architect.md`):
- Add note: "UniversalExecutor now routes through meta_executor (v2.0.0+)"
- Update: "Strict mode available but optional (set TRINITY_STRICT_MODE=true)"

**Pattern Specialist** (`.claude/pattern_specialist.md`):
- Add note: "Meta pattern actions implemented (v2.0.0): select_router, execute_pattern, track_execution, store_in_graph"
- Update: "PatternEngine has graph reference for enriched lookups"

**Knowledge Curator** (`.claude/knowledge_curator.md`):
- Add note: "PatternEngine receives graph reference (v2.0.0+)"
- Update: "PersistenceManager wired to production (backups on save/exit)"

**Agent Orchestrator** (`.claude/agent_orchestrator.md`):
- Add note: "15 agents registered (accurate as of v2.0.0)"
- Update: "See main.py lines 127-201 for registration code"

**Step 6.3.4: Update CLAUDE.md** (10 min - All)
**File**: `CLAUDE.md`

**Add Section**:
```markdown
## Recent Fixes (v2.0.0)

All critical gaps from GAP_ANALYSIS_CRITICAL.md have been resolved:

1. ✅ UniversalExecutor path corrected
2. ✅ Meta pattern actions implemented
3. ✅ Agent count aligned (15)
4. ✅ PatternEngine has graph
5. ✅ CI validates patterns
6. ✅ Graph viz edge rendering fixed
7. ✅ Recovery signature corrected
8. ✅ Persistence wired
9. ✅ Tests use assertions

System is now functionally A+ grade (98/100) with all claims verified.
```

**Step 6.3.5: Commit** (5 min)
```bash
git add SYSTEM_STATUS.md FIXES_COMPLETE.md .claude/*.md CLAUDE.md
git commit -m "docs: update documentation to reflect A+ grade fixes

- Update SYSTEM_STATUS.md with verified metrics
- Create FIXES_COMPLETE.md summarizing all 9 fixes
- Update specialist agent docs with v2.0.0 notes
- Update CLAUDE.md with recent fixes section

All documentation now accurately reflects functional system state"
```

### Deliverables
- ✅ PersistenceManager wired (save button + atexit)
- ✅ Tests converted to assertions (pytest-ready)
- ✅ Documentation updated to reflect reality
- ✅ FIXES_COMPLETE.md created
- ✅ All specialist agents updated
- ✅ 3 git commits

### Rollback Procedure
Each sub-phase can be reverted independently via git checkout.

### Success Criteria
- [ ] Save Graph button creates backup files
- [ ] All tests pass with `pytest dawsos/tests/validation/ -v`
- [ ] SYSTEM_STATUS.md claims match reality
- [ ] Documentation references v2.0.0 fixes

---

## Final Validation & Tagging

**Duration**: 30 minutes

### Step 1: Full Test Suite (15 min)
```bash
# Pattern validation
python scripts/lint_patterns.py
# Expected: 45 patterns, 0 errors

# Python tests
pytest dawsos/tests/validation/ -v --cov=dawsos/core --cov-report=html
# Expected: All tests pass, coverage ≥85%

# Manual smoke test
streamlit run dawsos/main.py
# Test: agent execution, pattern execution, graph viz, persistence
```

### Step 2: Verify Fixes (10 min)
**Checklist**:
```bash
# 1. UniversalExecutor path
tail dawsos/logs/PatternEngine_*.log | grep "Validated.*meta-patterns"
# Should see: Validated N meta-patterns

# 2. Meta actions exist
grep -c "if action == 'select_router'" dawsos/core/pattern_engine.py
# Should be: 1

# 3. Agent count
grep -c "register_agent" dawsos/main.py
# Should be: 15

# 4. PatternEngine has graph
python3 -c "from dawsos.core.pattern_engine import PatternEngine; print('graph param' in PatternEngine.__init__.__code__.co_varnames)"
# Should print: True

# 5. CI validates patterns
cat .github/workflows/compliance-check.yml | grep "dawsos/patterns"
# Should show: dawsos/patterns/**/*.json

# 6. Graph viz fixed
grep -c "graph.edges\[0\]" dawsos/main.py
# Should be: 0 (or only in comments/fallback)

# 7. Recovery signature
grep -c "execute_pattern(pattern," dawsos/core/universal_executor.py
# Should be: 2+ (uses pattern object, not name)

# 8. Persistence wired
grep -c "save_graph_with_persistence" dawsos/main.py
# Should be: 2+ (definition + calls)

# 9. Tests use assertions
grep -c "assert " dawsos/tests/validation/test_all_patterns.py
# Should be: 5+ (not 0)
```

### Step 3: Tag Release (5 min)
```bash
git tag -a v2.0.0 -m "Trinity 2.0 - A+ Grade Verified

All critical gaps resolved:
- UniversalExecutor routes through meta_executor
- Meta pattern actions implemented
- Agent count accurate (15)
- PatternEngine has graph reference
- CI validates patterns
- Graph visualization fixed
- Recovery signatures corrected
- Persistence wired to production
- Tests use assertions

Grade: A+ (98/100) ✅ VERIFIED
Documentation: 100% accurate
Tests: All passing
CI/CD: Validated"

git push origin v2.0.0
```

---

## Scope Creep Prevention

### What We Will NOT Do

❌ **Add New Features**
- No new agents
- No new patterns
- No new capabilities
- No new dataset types

❌ **Performance Optimization**
- No caching beyond existing
- No query optimization
- No parallel execution
- No profiling work

❌ **Refactoring**
- No architecture redesign
- No code cleanup beyond fixes
- No naming changes
- No module reorganization

❌ **UI Enhancements**
- No new visualizations
- No layout changes
- No styling updates
- No new tabs/sections

❌ **Infrastructure**
- No Docker changes
- No deployment updates
- No monitoring/logging expansion
- No CI/CD beyond pattern validation

### Scope Discipline Techniques

1. **"Fix Only" Mindset**: If it's not in GAP_ANALYSIS_CRITICAL.md, it's out of scope

2. **Minimal Implementation**: Each fix uses simplest solution that works

3. **No "While We're Here"**: Resist temptation to improve adjacent code

4. **Test Scope**: Only test what was fixed, not expand coverage

5. **Documentation Scope**: Update only what changed, not write new guides

### Red Flags (Stop if You See These)

🚩 "Let's also add..." - STOP
🚩 "This would be better if..." - STOP
🚩 "While we're fixing this, we could..." - STOP
🚩 "I just thought of a feature..." - STOP
🚩 Pull request >500 lines - STOP

### Success Metrics

✅ Total lines changed: <1000
✅ New files created: <10
✅ Time per phase: Within estimate ±30%
✅ Tests passing: 100%
✅ Regressions: 0

---

## Risk Mitigation

### Pre-Execution Checklist

```bash
# 1. Backup entire repository
cp -r /Users/mdawson/Dawson/DawsOSB /Users/mdawson/Dawson/DawsOSB.backup.$(date +%Y%m%d_%H%M%S)

# 2. Create feature branch
cd /Users/mdawson/Dawson/DawsOSB
git checkout -b fix/option-a-gap-fixes

# 3. Verify baseline tests pass
pytest dawsos/tests/validation/ -v

# 4. Document current state
git log -1 --oneline > .git/baseline_commit.txt
```

### During Execution

**After Each Phase**:
```bash
# 1. Run tests
pytest dawsos/tests/validation/ -v

# 2. Manual app test
streamlit run dawsos/main.py
# Verify app starts and basic functions work

# 3. Commit atomically
git add <changed_files>
git commit -m "phase N: <description>"

# 4. Update progress
echo "Phase N complete: $(date)" >> .git/progress.log
```

### Rollback Procedures

**Phase-Level Rollback**:
```bash
# Revert last commit
git reset --hard HEAD~1

# Or revert specific commit
git revert <commit_hash>

# Restore from backup
cp <backup_file> <original_file>
```

**Full Rollback**:
```bash
# Nuclear option - restore entire backup
cd /Users/mdawson/Dawson
rm -rf DawsOSB
cp -r DawsOSB.backup.YYYYMMDD_HHMMSS DawsOSB
cd DawsOSB
git status  # Check state
```

---

## Communication & Progress Tracking

### Progress Dashboard

Create `OPTION_A_PROGRESS.md`:

```markdown
# Option A Execution Progress

## Phase Status

- [x] Phase 1: UniversalExecutor Path (1.5h) ✅ 2025-10-03 10:30
- [x] Phase 2: Meta Pattern Actions (4h) ✅ 2025-10-03 15:00
- [ ] Phase 3: Agent Count (2h) 🔄 In Progress
- [ ] Phase 4: PatternEngine Graph (1h) ⏳ Pending
- [ ] Phase 5: CI/Viz/Recovery (3h) ⏳ Pending
- [ ] Phase 6: Testing/Persistence/Docs (4.5h) ⏳ Pending

## Metrics

- **Total Time**: 4.5h / 16h (28%)
- **Commits**: 2 / 9
- **Tests Passing**: 45 / 45
- **Fixes Complete**: 2 / 9

## Blockers

- None

## Next Steps

1. Complete Phase 3 (agent count alignment)
2. Test agent count accuracy
3. Begin Phase 4 (graph reference)
```

### Daily Standup (If Multi-Day)

**Questions**:
1. What did I complete yesterday?
2. What am I working on today?
3. Any blockers?

**Update OPTION_A_PROGRESS.md** after each phase.

---

## Post-Execution Validation

### Comprehensive Checklist

```bash
# 1. All fixes implemented
grep -r "TODO\|FIXME\|XXX" dawsos/core/*.py
# Should be: 0 matches (or only intentional)

# 2. All tests pass
pytest dawsos/tests/validation/ -v --cov=dawsos/core
# Expected: 100% pass, ≥85% coverage

# 3. Pattern linting passes
python scripts/lint_patterns.py
# Expected: 45 patterns, 0 errors

# 4. CI would pass
# Check .github/workflows/compliance-check.yml paths
# Verify patterns validated

# 5. Documentation accurate
diff <(grep -o "[0-9]* agents" .claude/*.md CLAUDE.md SYSTEM_STATUS.md | cut -d: -f2 | sort -u) <(echo "15 agents")
# Should be: No difference

# 6. Manual smoke test
streamlit run dawsos/main.py
# Test each major feature:
# - Chat (agent execution)
# - Patterns (pattern execution)
# - Graph (visualization)
# - Governance (persistence save)

# 7. Git history clean
git log --oneline | head -10
# Should show: 9 commits with clear messages

# 8. No regressions
git diff v1.x..v2.0.0 --stat
# Review: All changes intentional

# 9. Backup created
ls -la /Users/mdawson/Dawson/DawsOSB.backup.*
# Should exist: Dated backup directory
```

### Success Criteria

- [ ] All 9 fixes implemented
- [ ] All tests passing (pytest)
- [ ] Pattern linter passing
- [ ] CI configuration correct
- [ ] Documentation accurate (15 agents, A+ grade)
- [ ] Manual smoke test passes
- [ ] Git history clean (9 atomic commits)
- [ ] No regressions detected
- [ ] Backup exists
- [ ] v2.0.0 tagged

---

## Estimated Timeline

### Day 1 (8 hours)
- **09:00-10:30**: Phase 1 (UniversalExecutor Path) - 1.5h
- **10:30-10:45**: Break - 15min
- **10:45-14:45**: Phase 2 (Meta Pattern Actions) - 4h
- **14:45-15:30**: Lunch - 45min
- **15:30-17:30**: Phase 3 (Agent Count) - 2h

**Day 1 Total**: 7.5h work + breaks = ~8h

### Day 2 (8 hours)
- **09:00-10:00**: Phase 4 (PatternEngine Graph) - 1h
- **10:00-10:15**: Break - 15min
- **10:15-13:15**: Phase 5 (CI/Viz/Recovery) - 3h
- **13:15-14:00**: Lunch - 45min
- **14:00-18:30**: Phase 6 (Testing/Persistence/Docs) - 4.5h

**Day 2 Total**: 8.5h work + breaks = ~9h

### Total: 16 hours work time over 2 days

**Contingency Buffer**: +2h (10% for unexpected issues)
**Realistic Total**: 16-18 hours

---

## Success Celebration 🎉

**When All Phases Complete**:

1. **Final Commit**:
```bash
git commit -m "chore: Option A execution complete

All 9 critical gaps resolved:
✅ UniversalExecutor path corrected
✅ Meta pattern actions implemented
✅ Agent count aligned (15)
✅ PatternEngine has graph
✅ CI validates patterns
✅ Graph visualization fixed
✅ Recovery signatures corrected
✅ Persistence wired
✅ Tests use assertions

Grade: A+ (98/100) ✅ VERIFIED
Time: 16h over 2 days
Commits: 9 atomic changes
Tests: 100% passing
Regressions: 0

Documentation-reality alignment: 100%
System is production-ready for v2.0.0 release"
```

2. **Tag Release**: `git tag v2.0.0`

3. **Push**: `git push origin main --tags`

4. **Update README**:
```markdown
## Latest Release: v2.0.0 (Trinity 2.0 Complete)

All critical gaps resolved. System achieves verified A+ grade (98/100).

[Full release notes](FIXES_COMPLETE.md)
```

5. **Archive Gap Analysis**:
```bash
mv GAP_ANALYSIS_CRITICAL.md docs/reports/archive/2025-10/
mv OPTION_A_DETAILED_PLAN.md docs/reports/archive/2025-10/
```

6. **Announce**: Share FIXES_COMPLETE.md with team/users

---

**Ready to Execute**: All phases detailed with:
- ✅ Specialist agent ownership
- ✅ Scope boundaries defined
- ✅ Step-by-step instructions
- ✅ Validation checkpoints
- ✅ Rollback procedures
- ✅ Success criteria
- ✅ Time estimates
- ✅ Risk mitigation

**Awaiting your approval to begin Phase 1**.
