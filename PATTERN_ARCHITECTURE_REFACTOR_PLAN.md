# Pattern Architecture Refactor Plan

**Date**: 2025-01-15  
**Purpose**: Simplify and extend pattern architecture with minimal feature breaks  
**Status**: 📋 **PLAN READY FOR REVIEW**

---

## Executive Summary

This plan focuses on **pattern architecture improvements** that will:
1. **Simplify** pattern development and maintenance
2. **Extend** pattern capabilities with minimal breaking changes
3. **Reduce** complexity in pattern orchestration
4. **Improve** developer experience for pattern creation

**Key Principle**: Make patterns easier to write, test, and extend without breaking existing functionality.

---

## Current Architecture Analysis

### Strengths ✅
- **JSON-driven**: Business logic separated from code
- **Template system**: Flexible `{{inputs.x}}`, `{{ctx.y}}`, `{{step_result}}` syntax
- **Capability abstraction**: Patterns don't know which agent implements capabilities
- **Reproducibility**: Immutable pricing packs and request context
- **Traceability**: Full execution trace for debugging

### Pain Points 🔴
1. **Large orchestrator file** (1,375 lines) - Hard to maintain
2. **Mixed concerns** - Loading, validation, execution, template resolution all in one class
3. **Complex template resolution** - Nested logic, hard to debug
4. **Limited pattern composition** - Can't easily reuse pattern steps
5. **No pattern inheritance** - Can't extend base patterns
6. **Manual output mapping** - Must manually list outputs in `outputs` array
7. **No pattern versioning** - Can't evolve patterns without breaking changes
8. **Limited error recovery** - Fail-fast, no retry or fallback strategies

---

## Refactor Phases

### Phase 1: Extract Pattern Components (4-6 hours) - **HIGH IMPACT**

**Goal**: Separate concerns by extracting pattern loading, validation, and template resolution into dedicated classes.

#### 1.1 Extract PatternLoader (2 hours)
**File**: New `backend/app/core/patterns/loader.py`

**Current State**:
- Pattern loading logic in `PatternOrchestrator._load_patterns()` (lines 284-352)
- Mixed with validation and error handling

**Action**:
```python
class PatternLoader:
    """Load and cache pattern definitions from JSON files."""
    
    def __init__(self, patterns_dir: Path):
        self.patterns_dir = patterns_dir
        self.patterns: Dict[str, Dict[str, Any]] = {}
    
    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """Load all patterns from directory."""
        # Move _load_patterns() logic here
        
    def load_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Load a single pattern by ID."""
        
    def reload_pattern(self, pattern_id: str) -> bool:
        """Reload a pattern (for hot-reloading during development)."""
```

**Benefits**:
- ✅ Single responsibility (loading only)
- ✅ Testable independently
- ✅ Can add hot-reloading for development
- ✅ Can add pattern caching

**Impact**: **LOW RISK** - Pure extraction, no behavior change

---

#### 1.2 Extract TemplateResolver (2 hours)
**File**: New `backend/app/core/patterns/resolver.py`

**Current State**:
- Template resolution in `PatternOrchestrator._resolve_args()` and `_resolve_value()` (lines 922-1010)
- Complex nested logic for `{{foo}}`, `{{ctx.bar}}`, `{{inputs.baz}}`

**Action**:
```python
class TemplateResolver:
    """Resolve template variables in pattern arguments."""
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
    
    def resolve_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve all template variables in args dict."""
        # Move _resolve_args() logic here
        
    def resolve_value(self, value: Any) -> Any:
        """Resolve a single value (supports nested dicts/lists)."""
        # Move _resolve_value() logic here
        
    def resolve_template_string(self, text: str) -> str:
        """Resolve template variables in a string."""
        # Move _resolve_template_vars() logic here
```

**Benefits**:
- ✅ Single responsibility (template resolution only)
- ✅ Testable independently (can test template syntax)
- ✅ Can add better error messages
- ✅ Can add template validation

**Impact**: **LOW RISK** - Pure extraction, no behavior change

---

#### 1.3 Extract PatternValidator (1-2 hours)
**File**: New `backend/app/core/patterns/validator.py`

**Current State**:
- Validation logic in `PatternOrchestrator.validate_pattern()` and `validate_pattern_dependencies()` (lines 437-1284)
- Complex validation with multiple concerns

**Action**:
```python
class PatternValidator:
    """Validate pattern structure, dependencies, and contracts."""
    
    def __init__(self, agent_runtime):
        self.agent_runtime = agent_runtime
    
    def validate_structure(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Validate pattern JSON structure."""
        
    def validate_dependencies(self, pattern_id: str, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Validate pattern dependencies (capabilities, inputs)."""
        
    def validate_contracts(self, pattern: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate capability contracts (parameters, types)."""
```

**Benefits**:
- ✅ Single responsibility (validation only)
- ✅ Testable independently
- ✅ Can add more validation rules
- ✅ Can add validation caching

**Impact**: **LOW RISK** - Pure extraction, no behavior change

---

#### 1.4 Refactor PatternOrchestrator (1 hour)
**File**: `backend/app/core/pattern_orchestrator.py`

**Action**:
- Use extracted classes:
  ```python
  class PatternOrchestrator:
      def __init__(self, agent_runtime, db, redis=None):
          self.agent_runtime = agent_runtime
          self.db = db
          self.redis = redis
          self.loader = PatternLoader(Path(__file__).parent.parent.parent / "patterns")
          self.validator = PatternValidator(agent_runtime)
          self.patterns = self.loader.load_all()
  ```

**Benefits**:
- ✅ Orchestrator becomes much smaller (~400 lines vs 1,375)
- ✅ Clear separation of concerns
- ✅ Easier to test and maintain

**Impact**: **LOW RISK** - Refactoring only, no behavior change

---

### Phase 2: Simplify Pattern Development (3-4 hours) - **HIGH IMPACT**

#### 2.1 Auto-Detect Outputs (1-2 hours)
**Goal**: Automatically detect outputs from step results instead of manual `outputs` array.

**Current State**:
- Patterns must manually list outputs: `"outputs": ["perf_metrics", "currency_attr", ...]`
- Easy to forget outputs or have typos
- Must manually map outputs to state keys

**Action**:
```python
def _extract_outputs(self, spec: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract outputs from state based on pattern spec."""
    outputs = {}
    
    # If outputs array specified, use it (backwards compatible)
    if "outputs" in spec and isinstance(spec["outputs"], list):
        output_keys = spec["outputs"]
    else:
        # Auto-detect: use all step "as" keys as outputs
        output_keys = [step.get("as") for step in spec.get("steps", []) if step.get("as")]
    
    # Extract outputs from state
    for output_key in output_keys:
        if output_key in state:
            outputs[output_key] = state[output_key]
        else:
            outputs[output_key] = None  # Missing output
    
    return outputs
```

**Benefits**:
- ✅ Patterns can omit `outputs` array (auto-detected from steps)
- ✅ Reduces boilerplate
- ✅ Less error-prone (no typos in output names)
- ✅ Backwards compatible (still supports explicit `outputs`)

**Impact**: **LOW RISK** - Backwards compatible, optional feature

---

#### 2.2 Pattern Step Composition (2 hours)
**Goal**: Allow patterns to reference other patterns as steps (composition).

**Current State**:
- Patterns can only call capabilities directly
- Can't reuse pattern logic
- Must duplicate steps across patterns

**Action**:
```python
# Pattern can now have:
{
  "steps": [
    {
      "pattern": "portfolio_overview",  # Reference another pattern
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}"
      },
      "as": "overview"
    },
    {
      "capability": "charts.overview",  # Still supports capabilities
      "args": {...},
      "as": "charts"
    }
  ]
}
```

**Implementation**:
```python
async def _execute_step(self, step: Dict[str, Any], state: Dict[str, Any], ctx: RequestCtx) -> Any:
    """Execute a single step (capability or pattern)."""
    if "pattern" in step:
        # Execute nested pattern
        pattern_id = step["pattern"]
        pattern_inputs = self.resolver.resolve_args(step.get("args", {}))
        result = await self.run_pattern(pattern_id, ctx, pattern_inputs)
        return result
    elif "capability" in step:
        # Execute capability (existing logic)
        capability = step["capability"]
        args = self.resolver.resolve_args(step.get("args", {}))
        result = await self.agent_runtime.execute_capability(capability, ctx=ctx, state=state, **args)
        return result
    else:
        raise ValueError(f"Step must have 'pattern' or 'capability': {step}")
```

**Benefits**:
- ✅ Patterns can compose other patterns
- ✅ Reusable pattern building blocks
- ✅ DRY principle (Don't Repeat Yourself)
- ✅ Can build complex patterns from simple ones

**Impact**: **MEDIUM RISK** - New feature, but backwards compatible (existing patterns still work)

---

### Phase 3: Enhance Pattern Capabilities (4-6 hours) - **MEDIUM IMPACT**

#### 3.1 Pattern Inheritance (2-3 hours)
**Goal**: Allow patterns to extend base patterns (inheritance).

**Current State**:
- Patterns are completely independent
- Can't share common steps
- Must duplicate common logic

**Action**:
```json
{
  "id": "portfolio_overview_enhanced",
  "extends": "portfolio_overview",  // Inherit from base pattern
  "steps": [
    // Can override or add steps
    {
      "capability": "ai.explain",
      "args": {...},
      "as": "explanation"
    }
  ]
}
```

**Implementation**:
```python
def _merge_patterns(self, base_pattern: Dict[str, Any], derived_pattern: Dict[str, Any]) -> Dict[str, Any]:
    """Merge derived pattern with base pattern."""
    merged = base_pattern.copy()
    
    # Merge steps (derived steps override base steps with same "as" key)
    base_steps = {step.get("as"): step for step in merged.get("steps", [])}
    derived_steps = {step.get("as"): step for step in derived_pattern.get("steps", [])}
    base_steps.update(derived_steps)  # Derived overrides base
    merged["steps"] = list(base_steps.values())
    
    # Merge inputs (derived inputs override base inputs)
    merged["inputs"] = {**merged.get("inputs", {}), **derived_pattern.get("inputs", {})}
    
    # Merge outputs (union of both)
    merged["outputs"] = list(set(merged.get("outputs", []) + derived_pattern.get("outputs", [])))
    
    return merged
```

**Benefits**:
- ✅ Patterns can extend base patterns
- ✅ Share common logic
- ✅ Override specific steps
- ✅ DRY principle

**Impact**: **MEDIUM RISK** - New feature, backwards compatible

---

#### 3.2 Pattern Versioning (2-3 hours)
**Goal**: Support pattern versioning and evolution.

**Current State**:
- Patterns have `version` field but it's not used
- Can't evolve patterns without breaking changes
- No migration path for pattern changes

**Action**:
```json
{
  "id": "portfolio_overview",
  "version": "2.0.0",  // Semantic versioning
  "migration": {
    "from": "1.0.0",
    "changes": [
      "Added 'explanation' output",
      "Renamed 'perf_metrics' to 'performance_metrics'"
    ],
    "compatibility": "breaking"  // or "backwards_compatible"
  }
}
```

**Implementation**:
```python
def _migrate_pattern(self, pattern: Dict[str, Any], requested_version: Optional[str] = None) -> Dict[str, Any]:
    """Migrate pattern to requested version or latest."""
    current_version = pattern.get("version", "1.0.0")
    
    if requested_version and requested_version != current_version:
        # Apply migration rules
        migration = pattern.get("migration", {})
        if migration.get("compatibility") == "breaking":
            logger.warning(f"Pattern {pattern['id']} has breaking changes")
        
        # Apply migration transformations
        migrated = self._apply_migration(pattern, migration)
        return migrated
    
    return pattern
```

**Benefits**:
- ✅ Patterns can evolve without breaking clients
- ✅ Version-aware pattern execution
- ✅ Migration path for breaking changes
- ✅ Better API versioning

**Impact**: **LOW RISK** - Optional feature, backwards compatible

---

### Phase 4: Improve Error Handling (2-3 hours) - **MEDIUM IMPACT**

#### 4.1 Step-Level Error Recovery (2-3 hours)
**Goal**: Allow patterns to handle errors gracefully with retry/fallback.

**Current State**:
- Fail-fast on any step error
- No retry logic
- No fallback strategies

**Action**:
```json
{
  "steps": [
    {
      "capability": "provider.fetch_quote",
      "args": {...},
      "as": "quote",
      "error_handling": {
        "retry": {
          "max_attempts": 3,
          "backoff": "exponential",  // or "linear", "fixed"
          "delay": 1000  // milliseconds
        },
        "fallback": {
          "capability": "cache.get_quote",  // Fallback capability
          "args": {...}
        },
        "on_error": "skip"  // or "fail", "retry", "fallback"
      }
    }
  ]
}
```

**Implementation**:
```python
async def _execute_step_with_recovery(self, step: Dict[str, Any], state: Dict[str, Any], ctx: RequestCtx) -> Any:
    """Execute step with error recovery."""
    error_handling = step.get("error_handling", {})
    on_error = error_handling.get("on_error", "fail")
    
    if on_error == "retry":
        retry_config = error_handling.get("retry", {})
        max_attempts = retry_config.get("max_attempts", 1)
        backoff = retry_config.get("backoff", "fixed")
        delay = retry_config.get("delay", 1000)
        
        for attempt in range(max_attempts):
            try:
                return await self._execute_step(step, state, ctx)
            except Exception as e:
                if attempt < max_attempts - 1:
                    wait_time = self._calculate_backoff(attempt, backoff, delay)
                    await asyncio.sleep(wait_time / 1000)
                    continue
                raise
    
    elif on_error == "fallback":
        try:
            return await self._execute_step(step, state, ctx)
        except Exception as e:
            logger.warning(f"Step failed, using fallback: {e}")
            fallback = error_handling.get("fallback", {})
            return await self._execute_step(fallback, state, ctx)
    
    elif on_error == "skip":
        try:
            return await self._execute_step(step, state, ctx)
        except Exception as e:
            logger.warning(f"Skipping step due to error: {e}")
            return None  # Skip step, continue execution
    
    else:  # "fail" (default)
        return await self._execute_step(step, state, ctx)
```

**Benefits**:
- ✅ Patterns can handle transient errors
- ✅ Retry logic for flaky services
- ✅ Fallback strategies
- ✅ More resilient patterns

**Impact**: **LOW RISK** - Optional feature, backwards compatible (default: fail-fast)

---

## Implementation Priority

### P1 (High Impact, Low Risk) - Do First
1. **Phase 1.1**: Extract PatternLoader (2 hours)
2. **Phase 1.2**: Extract TemplateResolver (2 hours)
3. **Phase 1.3**: Extract PatternValidator (1-2 hours)
4. **Phase 1.4**: Refactor PatternOrchestrator (1 hour)
   - **Total**: 6-7 hours
   - **Impact**: High (better maintainability)
   - **Risk**: Low (pure extraction)

### P2 (High Impact, Medium Risk) - Do Next
5. **Phase 2.1**: Auto-Detect Outputs (1-2 hours)
6. **Phase 2.2**: Pattern Step Composition (2 hours)
   - **Total**: 3-4 hours
   - **Impact**: High (easier pattern development)
   - **Risk**: Medium (new features, but backwards compatible)

### P3 (Medium Impact, Low Risk) - Nice to Have
7. **Phase 3.1**: Pattern Inheritance (2-3 hours)
8. **Phase 3.2**: Pattern Versioning (2-3 hours)
   - **Total**: 4-6 hours
   - **Impact**: Medium (better pattern organization)
   - **Risk**: Low (optional features)

### P4 (Medium Impact, Low Risk) - Future
9. **Phase 4.1**: Step-Level Error Recovery (2-3 hours)
   - **Total**: 2-3 hours
   - **Impact**: Medium (more resilient patterns)
   - **Risk**: Low (optional feature)

---

## Success Metrics

### Code Quality
- ✅ Reduced orchestrator complexity (1,375 → ~400 lines)
- ✅ Better separation of concerns
- ✅ Improved testability (each component testable independently)
- ✅ Reduced code duplication

### Developer Experience
- ✅ Easier pattern development (auto-detect outputs, composition)
- ✅ Better error messages (template resolution, validation)
- ✅ Pattern reusability (inheritance, composition)
- ✅ Faster development cycle (hot-reloading, better tooling)

### System Maintainability
- ✅ Easier to add new features (extracted components)
- ✅ Easier to debug (clear separation of concerns)
- ✅ Better documentation (focused components)
- ✅ Reduced technical debt

---

## Risks & Mitigation

### Risk 1: Breaking Changes
**Mitigation**:
- All changes are backwards compatible
- Existing patterns continue to work
- New features are optional

### Risk 2: Performance Impact
**Mitigation**:
- Extracted components are lightweight
- No additional overhead
- Can add caching if needed

### Risk 3: Testing Complexity
**Mitigation**:
- Each component is independently testable
- Can test template resolution, validation, loading separately
- Better test coverage

---

## Next Steps

1. **Review and Approve Plan** - Get stakeholder approval
2. **Start with Phase 1** - Extract components (low risk, high impact)
3. **Test Thoroughly** - Ensure backwards compatibility
4. **Incremental Delivery** - One phase at a time
5. **Document Changes** - Update architecture docs

---

**Status**: 📋 **PLAN READY FOR REVIEW**  
**Estimated Total Time**: 15-20 hours  
**Risk Level**: **LOW** (all changes backwards compatible)  
**Impact Level**: **HIGH** (significantly improves pattern development)

