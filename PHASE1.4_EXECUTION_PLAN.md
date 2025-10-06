# Phase 1.4: Extract Pattern Action Handlers - Execution Plan

**Date**: October 6, 2025
**Status**: 🛑 **PLANNING - NOT STARTED**
**Estimated Effort**: 16-20 hours
**Risk Level**: **HIGH** (Core Execution Logic)

---

## Executive Summary

Extract the 765-line `execute_action()` method in `pattern_engine.py` into 22 separate handler classes. This refactoring will improve maintainability, testability, and extensibility of the pattern action system.

### Current State:
- **File**: `dawsos/core/pattern_engine.py`
- **Method**: `execute_action()` (lines 370-1134)
- **Size**: **765 lines**
- **Actions**: **22 action types**
- **Complexity**: Monolithic if/elif chain

### Target State:
```
dawsos/core/actions/
├── __init__.py                 # ActionHandler base + exports
├── registry.py                 # ActionRegistry
├── knowledge_lookup.py         # Lines 384-422 (38 lines)
├── enriched_lookup.py          # Lines 424-475 (51 lines)
├── evaluate.py                 # Lines 477-541 (64 lines)
├── calculate.py                # Lines 543-581 (38 lines)
├── synthesize.py               # Lines 583-640 (57 lines)
├── fetch_financials.py         # Lines 642-675 (33 lines)
├── dcf_analysis.py             # Lines 677-708 (31 lines)
├── calculate_confidence.py     # Lines 710-747 (37 lines)
├── add_position.py             # Lines 749-767 (18 lines)
├── detect_execution_type.py    # Lines 769-784 (15 lines)
├── fix_constructor_args.py     # Lines 786-797 (11 lines)
├── execute_through_registry.py # Lines 799-814 (15 lines)
├── normalize_response.py       # Lines 816-835 (19 lines)
├── validate_agent.py           # Lines 837-858 (21 lines)
├── inject_capabilities.py      # Lines 860-872 (12 lines)
├── scan_agents.py              # Lines 874-887 (13 lines)
├── check_constructor_compliance.py  # Lines 889-901 (12 lines)
├── apply_fixes.py              # Lines 903-923 (20 lines)
├── select_router.py            # Lines 925-965 (40 lines)
├── execute_pattern.py          # Lines 967-1009 (42 lines)
├── track_execution.py          # Lines 1011-1054 (43 lines)
└── store_in_graph.py           # Lines 1056-1120 (64 lines)
```

**Total**: 24 files, ~765 lines redistributed

---

## Action Inventory & Analysis

### Action Types by Category:

#### **1. Knowledge Access (4 actions)**
| Action | Lines | Complexity | Dependencies |
|--------|-------|------------|--------------|
| `knowledge_lookup` | 38 | Medium | graph, runtime |
| `enriched_lookup` | 51 | Medium | knowledge_loader, graph |
| `fetch_financials` | 33 | Low | runtime capabilities |
| `store_in_graph` | 64 | High | graph, persistence |

#### **2. Calculation & Analysis (5 actions)**
| Action | Lines | Complexity | Dependencies |
|--------|-------|------------|--------------|
| `evaluate` | 64 | High | Python eval() |
| `calculate` | 38 | Medium | Math expressions |
| `calculate_confidence` | 37 | Medium | confidence_calculator |
| `dcf_analysis` | 31 | Medium | Financial formulas |
| `add_position` | 18 | Low | Data structures |

#### **3. Workflow Control (3 actions)**
| Action | Lines | Complexity | Dependencies |
|--------|-------|------------|--------------|
| `execute_through_registry` | 15 | Low | runtime.exec_via_registry |
| `execute_pattern` | 42 | Medium | pattern_engine (recursive) |
| `track_execution` | 43 | Medium | Metrics tracking |

#### **4. Agent Management (7 actions)**
| Action | Lines | Complexity | Dependencies |
|--------|-------|------------|--------------|
| `detect_execution_type` | 15 | Low | Agent introspection |
| `fix_constructor_args` | 11 | Low | Signature analysis |
| `normalize_response` | 19 | Low | Response formatting |
| `validate_agent` | 21 | Low | Validation logic |
| `inject_capabilities` | 12 | Low | Capability injection |
| `scan_agents` | 13 | Low | Agent discovery |
| `check_constructor_compliance` | 12 | Low | Constructor checks |

#### **5. Utility Actions (3 actions)**
| Action | Lines | Complexity | Dependencies |
|--------|-------|------------|--------------|
| `synthesize` | 57 | Medium | LLM client |
| `select_router` | 40 | Medium | Routing logic |
| `apply_fixes` | 20 | Low | Code modifications |

---

## Implementation Strategy

### Phase 1: Base Infrastructure (2-3 hours)

**Step 1.1: Create Action Handler Base Class**
```python
# dawsos/core/actions/__init__.py
from abc import ABC, abstractmethod
from typing import Dict, Any, TypeAlias

ParamsDict: TypeAlias = Dict[str, Any]
ContextDict: TypeAlias = Dict[str, Any]
OutputsDict: TypeAlias = Dict[str, Any]
ResultDict: TypeAlias = Dict[str, Any]

class ActionHandler(ABC):
    """Base class for all pattern action handlers"""

    def __init__(self, pattern_engine):
        """Initialize with reference to pattern engine for shared resources"""
        self.pattern_engine = pattern_engine
        self.graph = pattern_engine.graph
        self.runtime = pattern_engine.runtime
        self.knowledge_loader = pattern_engine.knowledge_loader
        self.logger = pattern_engine.logger

    @abstractmethod
    def execute(
        self,
        params: ParamsDict,
        context: ContextDict,
        outputs: OutputsDict
    ) -> ResultDict:
        """Execute this action"""
        pass

    @property
    @abstractmethod
    def action_name(self) -> str:
        """Return the action name (e.g., 'knowledge_lookup')"""
        pass
```

**Step 1.2: Create Action Registry**
```python
# dawsos/core/actions/registry.py
from typing import Dict
from .base import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict
import logging

logger = logging.getLogger(__name__)

class ActionRegistry:
    """Registry for all pattern actions"""

    def __init__(self):
        self.handlers: Dict[str, ActionHandler] = {}

    def register(self, handler: ActionHandler):
        """Register an action handler"""
        action_name = handler.action_name
        if action_name in self.handlers:
            logger.warning(f"Overwriting existing handler for action: {action_name}")
        self.handlers[action_name] = handler
        logger.debug(f"Registered action handler: {action_name}")

    def execute(
        self,
        action_name: str,
        params: ParamsDict,
        context: ContextDict,
        outputs: OutputsDict
    ) -> ResultDict:
        """Execute an action by name"""
        handler = self.handlers.get(action_name)
        if not handler:
            raise ValueError(f"Unknown action: {action_name}")

        try:
            return handler.execute(params, context, outputs)
        except Exception as e:
            logger.error(f"Action '{action_name}' failed: {e}", exc_info=True)
            return {
                'error': str(e),
                'action': action_name,
                'params': params
            }

    def list_actions(self) -> list:
        """List all registered actions"""
        return sorted(self.handlers.keys())
```

### Phase 2: Extract Simple Actions (3-4 hours)

**Priority Order** (Low complexity first):
1. ✅ `fix_constructor_args` (11 lines) - Easiest
2. ✅ `inject_capabilities` (12 lines)
3. ✅ `check_constructor_compliance` (12 lines)
4. ✅ `scan_agents` (13 lines)
5. ✅ `detect_execution_type` (15 lines)
6. ✅ `execute_through_registry` (15 lines) - **CRITICAL** (most used)
7. ✅ `add_position` (18 lines)
8. ✅ `normalize_response` (19 lines)
9. ✅ `apply_fixes` (20 lines)
10. ✅ `validate_agent` (21 lines)

**Example Implementation**:
```python
# dawsos/core/actions/execute_through_registry.py
from .base import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict

class ExecuteThroughRegistryAction(ActionHandler):
    """Execute agent through runtime registry (Trinity compliance)"""

    @property
    def action_name(self) -> str:
        return "execute_through_registry"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """Execute agent via registry"""
        agent_name = params.get('agent')
        agent_context = params.get('context', context)

        if not self.runtime:
            return {'error': 'Runtime not available'}

        # Execute through registry (Trinity compliant)
        result = self.runtime.exec_via_registry(agent_name, agent_context)
        return result
```

### Phase 3: Extract Medium Actions (4-5 hours)

**Priority Order** (Medium complexity):
1. ✅ `dcf_analysis` (31 lines)
2. ✅ `fetch_financials` (33 lines)
3. ✅ `calculate_confidence` (37 lines)
4. ✅ `calculate` (38 lines)
5. ✅ `knowledge_lookup` (38 lines)
6. ✅ `select_router` (40 lines)
7. ✅ `execute_pattern` (42 lines) - **RECURSIVE** ⚠️
8. ✅ `track_execution` (43 lines)

**Recursive Action Handling**:
```python
# dawsos/core/actions/execute_pattern.py
class ExecutePatternAction(ActionHandler):
    """Execute a sub-pattern (recursive pattern execution)"""

    @property
    def action_name(self) -> str:
        return "execute_pattern"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """Execute a pattern recursively"""
        pattern_id = params.get('pattern_id')
        pattern_context = params.get('context', context)

        # Get pattern
        pattern = self.pattern_engine.get_pattern(pattern_id)
        if not pattern:
            return {'error': f'Pattern not found: {pattern_id}'}

        # IMPORTANT: Recursive call back to pattern_engine
        result = self.pattern_engine.execute_pattern(pattern, pattern_context)
        return result
```

### Phase 4: Extract Complex Actions (5-6 hours)

**Priority Order** (High complexity):
1. ✅ `enriched_lookup` (51 lines) - Graph queries
2. ✅ `synthesize` (57 lines) - LLM integration
3. ✅ `evaluate` (64 lines) - Python eval() **⚠️ SECURITY**
4. ✅ `store_in_graph` (64 lines) - Graph mutations

**Security Considerations**:
```python
# dawsos/core/actions/evaluate.py
class EvaluateAction(ActionHandler):
    """Evaluate Python expressions (SECURITY: Use safe_eval)"""

    @property
    def action_name(self) -> str:
        return "evaluate"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """Evaluate expression with safety constraints"""
        expression = params.get('expression', '')

        # SECURITY: Whitelist allowed operations
        allowed_names = {
            'abs', 'min', 'max', 'round', 'sum', 'len',
            'float', 'int', 'str', 'bool',
            'True', 'False', 'None'
        }

        # Build safe context
        eval_context = {
            **{name: __builtins__.get(name) for name in allowed_names},
            'context': context,
            'outputs': outputs
        }

        try:
            result = eval(expression, {"__builtins__": {}}, eval_context)
            return {'result': result, 'evaluated': True}
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}", exc_info=True)
            return {'error': str(e), 'expression': expression}
```

### Phase 5: Integration & Testing (2-3 hours)

**Step 5.1: Update PatternEngine**
```python
# dawsos/core/pattern_engine.py (MODIFIED)
from core.actions import ActionRegistry
# Import all action handlers
from core.actions.knowledge_lookup import KnowledgeLookupAction
from core.actions.execute_through_registry import ExecuteThroughRegistryAction
# ... import all 22 handlers

class PatternEngine:
    def __init__(self, pattern_dir: str = 'patterns', runtime=None, graph=None):
        # ... existing init code ...

        # Initialize action registry
        self.action_registry = ActionRegistry()
        self._register_action_handlers()

    def _register_action_handlers(self):
        """Register all built-in action handlers"""
        handlers = [
            KnowledgeLookupAction(self),
            EnrichedLookupAction(self),
            EvaluateAction(self),
            CalculateAction(self),
            SynthesizeAction(self),
            FetchFinancialsAction(self),
            DCFAnalysisAction(self),
            CalculateConfidenceAction(self),
            AddPositionAction(self),
            DetectExecutionTypeAction(self),
            FixConstructorArgsAction(self),
            ExecuteThroughRegistryAction(self),  # Most important!
            NormalizeResponseAction(self),
            ValidateAgentAction(self),
            InjectCapabilitiesAction(self),
            ScanAgentsAction(self),
            CheckConstructorComplianceAction(self),
            ApplyFixesAction(self),
            SelectRouterAction(self),
            ExecutePatternAction(self),  # Recursive!
            TrackExecutionAction(self),
            StoreInGraphAction(self)
        ]

        for handler in handlers:
            self.action_registry.register(handler)

        self.logger.info(f"Registered {len(handlers)} action handlers")

    def execute_action(self, action: ActionName, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """Execute an action through the registry (SIMPLIFIED)"""
        return self.action_registry.execute(action, params, context, outputs)
```

**Step 5.2: Write Tests**
```python
# dawsos/tests/unit/test_action_handlers.py
import pytest
from core.actions import ActionRegistry
from core.actions.execute_through_registry import ExecuteThroughRegistryAction

def test_action_registry_basic():
    """Test basic registry operations"""
    registry = ActionRegistry()

    # Create mock handler
    handler = ExecuteThroughRegistryAction(mock_pattern_engine)
    registry.register(handler)

    assert 'execute_through_registry' in registry.list_actions()

def test_execute_through_registry_action():
    """Test execute_through_registry action"""
    # ... test implementation
```

**Step 5.3: Integration Testing**
```python
# dawsos/tests/validation/test_pattern_actions.py
def test_all_actions_registered():
    """Ensure all 22 actions are registered"""
    engine = PatternEngine()
    actions = engine.action_registry.list_actions()

    expected = [
        'knowledge_lookup', 'enriched_lookup', 'evaluate',
        'calculate', 'synthesize', 'fetch_financials',
        'dcf_analysis', 'calculate_confidence', 'add_position',
        'detect_execution_type', 'fix_constructor_args',
        'execute_through_registry', 'normalize_response',
        'validate_agent', 'inject_capabilities', 'scan_agents',
        'check_constructor_compliance', 'apply_fixes',
        'select_router', 'execute_pattern', 'track_execution',
        'store_in_graph'
    ]

    assert sorted(actions) == sorted(expected)

def test_pattern_execution_unchanged():
    """Ensure pattern execution still works"""
    engine = PatternEngine()
    pattern = engine.get_pattern('dcf_valuation')
    result = engine.execute_pattern(pattern, {'symbol': 'AAPL'})

    assert 'error' not in result
    assert 'response' in result
```

---

## Risk Assessment

### HIGH RISK AREAS:

1. **execute_pattern Action** (Recursive)
   - Risk: Infinite loops if not careful
   - Mitigation: Add recursion depth limit
   - Test: Unit test with nested patterns

2. **evaluate Action** (Python eval())
   - Risk: Code injection vulnerability
   - Mitigation: Strict whitelist, sandboxed context
   - Test: Security audit, penetration testing

3. **Backward Compatibility**
   - Risk: Existing patterns break
   - Mitigation: Keep old method as wrapper
   - Test: Run full pattern suite

4. **Performance**
   - Risk: Registry lookup overhead
   - Mitigation: Dict lookup is O(1), negligible
   - Test: Benchmark before/after

### MEDIUM RISK AREAS:

1. **store_in_graph Action** (64 lines, complex)
   - Risk: Graph corruption
   - Mitigation: Transaction-like operations
   - Test: Graph integrity checks

2. **synthesize Action** (LLM integration)
   - Risk: LLM client failures
   - Mitigation: Existing error handling
   - Test: Mock LLM responses

### LOW RISK AREAS:

1. **Simple Actions** (11-21 lines each)
   - Risk: Minimal
   - Mitigation: Direct code copy, no logic changes
   - Test: Basic unit tests

---

## Testing Strategy

### Unit Tests (Required):
- ✅ Test each action handler individually
- ✅ Mock dependencies (graph, runtime, knowledge_loader)
- ✅ Test error paths
- ✅ Test edge cases

### Integration Tests (Required):
- ✅ Test pattern execution with real actions
- ✅ Test recursive pattern execution
- ✅ Test action registry registration
- ✅ Test all 22 actions are registered

### Regression Tests (Critical):
- ✅ Run all existing pattern tests
- ✅ Ensure no patterns break
- ✅ Ensure performance unchanged
- ✅ Ensure error messages unchanged

### Security Tests (For evaluate action):
- ✅ Test code injection attempts
- ✅ Test whitelist enforcement
- ✅ Test sandboxed context

---

## Migration Path

### Option A: Big Bang (NOT RECOMMENDED)
- Replace entire execute_action() method at once
- High risk, hard to debug
- **Timeline**: 16-20 hours continuous

### Option B: Gradual Migration (RECOMMENDED) ⭐
1. **Phase 1**: Create infrastructure (2-3 hours)
2. **Phase 2**: Extract 10 simple actions (3-4 hours)
3. **Deploy & Test**: Validate in staging (1-2 days)
4. **Phase 3**: Extract 8 medium actions (4-5 hours)
5. **Deploy & Test**: Validate in staging (1-2 days)
6. **Phase 4**: Extract 4 complex actions (5-6 hours)
7. **Deploy & Test**: Final validation (1-2 days)

**Total**: 14-18 hours coding + 3-6 days testing

### Option C: Hybrid Wrapper (SAFEST)
- Keep old method as fallback wrapper
- Gradually migrate actions to registry
- Both systems coexist during transition

```python
def execute_action(self, action: ActionName, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
    """Execute action (supports both old and new system)"""

    # Try new registry first
    if action in self.action_registry.list_actions():
        return self.action_registry.execute(action, params, context, outputs)

    # Fallback to old system
    self.logger.warning(f"Action '{action}' not in registry, using legacy handler")
    return self._execute_action_legacy(action, params, context, outputs)
```

---

## Success Criteria

### Code Quality:
- ✅ Single Responsibility Principle (each action is a class)
- ✅ Open/Closed Principle (easy to add new actions)
- ✅ Dependency Injection (handlers get dependencies via constructor)
- ✅ Type Safety (all handlers type-hinted)

### Maintainability:
- ✅ Each action in separate file (easy to find)
- ✅ Consistent structure across handlers
- ✅ Clear documentation for each action
- ✅ Easy to add new actions

### Testability:
- ✅ Each handler can be unit tested independently
- ✅ Easy to mock dependencies
- ✅ Clear test coverage per action

### Performance:
- ✅ No regression in pattern execution time
- ✅ Registry lookup is O(1)
- ✅ No additional memory overhead

---

## Estimated Timeline

| Phase | Effort | Timeline | Risk |
|-------|--------|----------|------|
| Infrastructure | 2-3 hours | Day 1 | Low |
| Simple Actions (10) | 3-4 hours | Day 1-2 | Low |
| **CHECKPOINT 1** | - | - | - |
| Medium Actions (8) | 4-5 hours | Day 2-3 | Medium |
| **CHECKPOINT 2** | - | - | - |
| Complex Actions (4) | 5-6 hours | Day 3-4 | High |
| Integration & Testing | 2-3 hours | Day 4-5 | Medium |
| **TOTAL** | **16-21 hours** | **5 days** | **HIGH** |

**Validation Between Checkpoints**: 1-2 days each

---

## Recommendation

### 🛑 **DO NOT START PHASE 1.4 YET**

**Reasons**:
1. ✅ Phases 1.1-1.3 are production-ready (A- grade)
2. ⚠️ Phase 1.4 is HIGH RISK (core execution logic)
3. 📊 Need to validate current changes in production first
4. ⏰ 16-20 hour effort requires dedicated focus
5. 🧪 Requires comprehensive testing (3-6 days)

### Alternative Path:

**RECOMMENDED**: Deploy & Validate First
1. Deploy Phases 1.1-1.3 to staging ✅
2. Run integration tests with real patterns ✅
3. Monitor for errors/issues (1-2 weeks) ✅
4. **THEN** return to Phase 1.4 with confidence

**Benefits**:
- Validate current improvements work in production
- Catch any issues with FMP API integration
- Gain confidence before major refactor
- Allow time for proper Phase 1.4 planning

### If You Must Continue:

**Choose Option C: Hybrid Wrapper** (Safest)
- Both old and new systems coexist
- Gradual migration, one action at a time
- Easy rollback if issues arise
- Lower risk, longer timeline

---

## Appendix: File Structure

### Before (1 file):
```
dawsos/core/pattern_engine.py (1,903 lines)
├── execute_action() [765 lines]  ← MONOLITHIC
```

### After (24 files):
```
dawsos/core/
├── pattern_engine.py (1,180 lines)  ← REDUCED
└── actions/
    ├── __init__.py (50 lines)
    ├── registry.py (60 lines)
    ├── knowledge_lookup.py (40 lines)
    ├── enriched_lookup.py (55 lines)
    ├── evaluate.py (70 lines)
    ├── calculate.py (45 lines)
    ├── synthesize.py (60 lines)
    ├── fetch_financials.py (40 lines)
    ├── dcf_analysis.py (35 lines)
    ├── calculate_confidence.py (40 lines)
    ├── add_position.py (25 lines)
    ├── detect_execution_type.py (20 lines)
    ├── fix_constructor_args.py (18 lines)
    ├── execute_through_registry.py (20 lines)
    ├── normalize_response.py (25 lines)
    ├── validate_agent.py (28 lines)
    ├── inject_capabilities.py (18 lines)
    ├── scan_agents.py (20 lines)
    ├── check_constructor_compliance.py (18 lines)
    ├── apply_fixes.py (28 lines)
    ├── select_router.py (45 lines)
    ├── execute_pattern.py (50 lines)
    ├── track_execution.py (48 lines)
    └── store_in_graph.py (70 lines)
```

**Total Lines**: ~1,900 (no change, just reorganized)
**Maintainability**: ↑↑↑ Significantly improved
**Testability**: ↑↑↑ Significantly improved
**Extensibility**: ↑↑↑ Easy to add new actions

---

## Summary

**Phase 1.4 Status**: 🛑 **DEFERRED**

**Current State**: ✅ Phases 1.1-1.3 Complete (A- grade)

**Next Action**: 🚀 **Deploy to Staging & Validate**

**Phase 1.4 Plan**: 📋 **Ready for execution when needed**

**Estimated Effort**: 16-21 hours + 3-6 days testing

**Risk Level**: **HIGH** (requires careful execution)

**Recommendation**: Validate current work first, then return to Phase 1.4 with confidence.
