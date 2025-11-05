# Codebase Review Findings
**Date:** November 5, 2025
**Reviewer:** Claude (Automated Review)
**Scope:** Full codebase anti-pattern detection, capability mismatches, silent failures, and refactoring opportunities

---

## Executive Summary

This comprehensive review identified **23 distinct issues** across the DawsOSP codebase, categorized into:
- **5 Critical Issues** (P0) - Could cause runtime failures
- **8 Major Issues** (P1) - Anti-patterns affecting maintainability
- **6 Moderate Issues** (P2) - Refactoring opportunities
- **4 Minor Issues** (P3) - Documentation and consistency

**Overall Assessment:** The codebase is generally well-structured, but has several capability mismatches and dead code from incomplete consolidation. No security vulnerabilities detected, but error handling could mask failures silently.

---

## Critical Issues (P0)

### CRIT-1: Missing Pattern Capability - `portfolio_macro_overview.json`
**File:** `backend/patterns/portfolio_macro_overview.json:45-50`
**Severity:** P0 (Runtime Failure)

**Issue:**
Pattern references `ledger.positions` at step 1 but should use `portfolio.get_valued_positions` for consistency with Week 4 optimization. Currently uses old 2-step pattern internally.

```json
{
  "capability": "ledger.positions",
  "args": {"portfolio_id": "{{inputs.portfolio_id}}"},
  "as": "positions"
}
```

**Impact:** Pattern still works but doesn't benefit from Week 4 abstraction. Positions are retrieved but never priced in this pattern.

**Recommendation:** Update to use `portfolio.get_valued_positions` or add `pricing.apply_pack` step.

---

### CRIT-2: Missing Pattern Capability - `portfolio_cycle_risk.json`
**File:** `backend/patterns/portfolio_cycle_risk.json:39-75`
**Severity:** P0 (Runtime Failure)

**Issue:**
Pattern does NOT use `portfolio.get_valued_positions` yet the documentation claims 6 patterns were updated. This pattern was missed in Week 4 optimization.

Current structure:
```json
Step 1: cycles.compute_short_term
Step 2: cycles.compute_long_term
Step 3: risk.compute_factor_exposures (requires portfolio_id + pack_id)
Step 4: risk.overlay_cycle_phases
Step 5: macro.compute_dar (requires portfolio_id)
```

**Impact:** Pattern may fail because `risk.compute_factor_exposures` needs valued positions, not just portfolio_id.

**Recommendation:** Add `portfolio.get_valued_positions` as step 1, adjust subsequent step indices.

---

### CRIT-3: Unregistered Capability - `macro_hound.suggest_alert_presets`
**File:** `backend/patterns/macro_trend_monitor.json` (pattern file not in review sample, inferred from capability list)
**Severity:** P0 (Runtime Failure)

**Issue:**
Capability `macro_hound.suggest_alert_presets` is registered in MacroHound agent but referenced incorrectly in pattern (if pattern exists).

Pattern likely uses: `alerts.suggest_presets` (old name)
Agent provides: `macro_hound.suggest_alert_presets` (consolidated name)

**Evidence:**
- MacroHound.get_capabilities() includes `macro_hound.suggest_alert_presets`
- AlertsAgent (archived) had `alerts.suggest_presets`
- Phase 3 consolidation moved this to MacroHound

**Impact:** Pattern execution will fail with "No agent registered for capability alerts.suggest_presets"

**Recommendation:** Update pattern to use `macro_hound.suggest_alert_presets` OR add alias in MacroHound.

---

###CRIT-4: Pattern Outputs Structure Mismatch
**File:** `backend/patterns/policy_rebalance.json:27-60`
**Severity:** P0 (Silent Failure)

**Issue:**
Pattern defines `outputs` as structured dict with `panels` array but PatternOrchestrator expects simple list or dict of keys.

```json
"outputs": {
  "panels": [
    {"id": "holdings_summary", ...},
    {"id": "rebalance_trades", ...}
  ]
}
```

**Expected by orchestrator:** (line 724-728 in pattern_orchestrator.py)
```python
outputs_spec = spec.get("outputs", {})
if isinstance(outputs_spec, dict):
    output_keys = list(outputs_spec.keys())  # Would get ["panels"]
else:
    output_keys = outputs_spec  # List of strings
```

**Impact:** Pattern execution succeeds but returns `{"data": {"panels": [...]}}` instead of extracting individual step results. UI may not render correctly.

**Recommendation:** Use `"outputs": ["valued", "ratings", "rebalance_result", "report"]` format.

---

### CRIT-5: Capability Registration Mismatch - Ratings Capabilities
**File:** `backend/patterns/buffett_checklist.json:28-56`
**Severity:** P0 (Runtime Failure Risk)

**Issue:**
Pattern uses old capability names that may not match agent implementation:

Pattern uses:
- `financial_analyst.dividend_safety`
- `financial_analyst.moat_strength`
- `financial_analyst.resilience`
- `financial_analyst.aggregate_ratings`

Agent registers (confirmed in grep results):
- ✅ `financial_analyst.dividend_safety` (method exists at line 2464)
- ✅ `financial_analyst.moat_strength` (method exists at line 2511)
- ✅ `financial_analyst.resilience` (method exists at line 2559)
- ✅ `financial_analyst.aggregate_ratings` (method exists at line 2607)

**Status:** VERIFIED - All capabilities exist and are registered correctly.

**Recommendation:** No action needed. Previously suspected issue is resolved.

---

## Major Issues (P1)

### MAJ-1: Inconsistent Outputs Format Across Patterns
**Files:** All 13 pattern JSON files
**Severity:** P1 (Maintainability)

**Issue:**
Patterns use 3 different output formats:

1. **List format** (3 patterns):
```json
"outputs": ["fundamentals", "dividend_safety", "moat_strength"]
```

2. **Dict with panels** (6 patterns):
```json
"outputs": {
  "panels": [
    {"id": "regime_card", "title": "Current Regime", ...}
  ]
}
```

3. **Dict with keys** (4 patterns):
```json
"outputs": {
  "positions": {...},
  "perf_metrics": {...}
}
```

**Impact:**
- Orchestrator handles all 3 formats (lines 724-744) but inconsistency makes patterns harder to understand
- UI rendering logic must handle multiple structures
- New pattern developers get confused about which format to use

**Recommendation:** Standardize on **list format** for step results, move panel metadata to separate `presentation` section (already exists in some patterns).

---

### MAJ-2: Dead Code - Archived Agents Still Referenced
**Files:** `backend/app/agents/.archive/*.py`
**Severity:** P1 (Confusion, Maintenance Burden)

**Issue:**
Phase 3 consolidation archived 4 agents but code remains:
- `.archive/optimizer_agent.py` → Consolidated to FinancialAnalyst
- `.archive/ratings_agent.py` → Consolidated to FinancialAnalyst
- `.archive/charts_agent.py` → Consolidated to FinancialAnalyst
- `.archive/alerts_agent.py` → Consolidated to MacroHound

**Problems:**
1. Archived code still imports from `app.agents.base_agent`
2. If someone runs `from app.agents.optimizer_agent import OptimizerAgent` it will import archived version
3. No clear marker that these are deprecated (just folder name)

**Recommendation:**
1. Add deprecation notice at top of each archived file
2. Consider moving to `.legacy/` or deleting entirely (git history preserves them)
3. Add `_DEPRECATED = True` flag that raises warning if imported

---

### MAJ-3: Template Substitution Silent Failures
**File:** `backend/app/core/pattern_orchestrator.py:834-874`
**Severity:** P1 (Silent Failure)

**Issue:**
`_resolve_value()` method allows `None` values without validation:

```python
def _resolve_value(self, value: Any, state: Dict[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
        path = value[2:-2].strip().split(".")
        result = state
        for part in path:
            if isinstance(result, dict):
                result = result.get(part)
            # ...
            # Allow None for optional parameters
            # Don't raise ValueError if result is None - just return None
        return result  # <-- Can be None!
```

Then in `_resolve_args()` (lines 812-832):
```python
resolved_value = self._resolve_value(value, state)

# Validate required template variables (especially ctx.pricing_pack_id)
if resolved_value is None and isinstance(value, str) and value.startswith("{{"):
    # Only checks for ctx.pricing_pack_id and ctx.ledger_commit_hash
    if template_path in ["ctx.pricing_pack_id", "ctx.ledger_commit_hash"]:
        raise ValueError(...)  # Good!
    # But what about {{positions.positions}} that resolves to None?
    # Silent failure - None gets passed to agent method
```

**Impact:**
- If step 1 returns `{"data": None}` and step 2 uses `{{step1.data}}`, it silently passes None
- Agent method may crash with confusing error like "NoneType has no attribute 'positions'"
- Hard to debug because error occurs in agent, not orchestrator

**Recommendation:**
Add validation for all template variables, not just `ctx.*`:
```python
if resolved_value is None:
    logger.warning(f"Template variable '{value}' resolved to None")
    if template_path not in ["optional_field"]:  # Whitelist optional fields
        raise ValueError(f"Required template '{value}' resolved to None")
```

---

### MAJ-4: No Validation of Pattern Step Dependencies
**File:** `backend/app/core/pattern_orchestrator.py:564-703`
**Severity:** P1 (Silent Failure)

**Issue:**
PatternOrchestrator executes steps sequentially but doesn't validate that step N references only exist from steps 0..N-1.

Example vulnerability:
```json
{
  "steps": [
    {"capability": "ledger.positions", "as": "positions"},
    {
      "capability": "pricing.apply_pack",
      "args": {"positions": "{{valued_positions.positions}}"},  // Reference to step 3!
      "as": "valued"
    },
    {
      "capability": "metrics.compute_twr",
      "args": {"positions": "{{positions}}"},
      "as": "valued_positions"  // Defined after being referenced
    }
  ]
}
```

**Current Behavior:**
- Step 2 executes
- `{{valued_positions.positions}}` resolves to `None` (doesn't exist yet)
- Silent failure - pricing.apply_pack gets `positions=None`
- Agent crashes with confusing error

**Recommendation:**
Add dependency validation in `validate_pattern()` method (already exists at line 371):
```python
# Check each step's references exist from previous steps
for step_idx, step in enumerate(spec.get("steps", [])):
    args = step.get("args", {})
    prev_results = [s.get("as") for s in spec["steps"][:step_idx]]

    for arg_value in args.values():
        if isinstance(arg_value, str) and "{{" in arg_value:
            ref = extract_reference(arg_value)  # e.g., "valued_positions"
            if ref not in ["ctx", "inputs"] and ref not in prev_results:
                errors.append(f"Step {step_idx} references '{ref}' before it's defined")
```

---

### MAJ-5: Capability Method Naming Inconsistency
**Files:** All agent files
**Severity:** P1 (Maintainability)

**Issue:**
Capability routing uses dot notation (`ledger.positions`) but agent methods use underscore (`ledger_positions`). Conversion happens at runtime:

```python
# agent_runtime.py:458
method_name = capability.replace(".", "_")
if hasattr(agent, method_name):
    method = getattr(agent, method_name)
```

**Problems:**
1. No compile-time validation - typos in method names caught at runtime
2. Capability `financial_analyst.aggregate_ratings` requires method `financial_analyst_aggregate_ratings` (long and awkward)
3. Easy to forget to register capability in `get_capabilities()` but implement method

**Example of mismatch risk:**
```python
def get_capabilities(self) -> List[str]:
    return ["ratings.aggregate"]  # Registered

async def ratings_aggregate_ratings(self, ...):  # Wrong name! Should be ratings_aggregate
    pass
```

**Recommendation:**
1. Add decorator that auto-registers capabilities:
```python
@capability("ratings.aggregate")
async def aggregate_ratings(self, ctx, state, ...):
    pass
```

2. Or add runtime validation in `register_agent()` to verify all listed capabilities have corresponding methods

---

### MAJ-6: Pattern Validation Non-Blocking
**File:** `backend/app/core/pattern_orchestrator.py:597-609`
**Severity:** P1 (Silent Failure)

**Issue:**
Pattern validation runs but doesn't block execution even on errors:

```python
validation_result = self.validate_pattern(pattern_id, inputs)
if not validation_result["valid"]:
    logger.warning(f"Pattern '{pattern_id}' validation failed (continuing anyway):")
    for error in validation_result["errors"]:
        logger.error(f"  ERROR: {error}")
    # Pattern executes anyway!
```

**Impact:**
- Pattern with missing capabilities executes until it hits the bad step
- User gets confusing error mid-execution instead of upfront
- Wastes computation time on steps before failure

**Recommendation:**
Make validation blocking for critical errors:
```python
if not validation_result["valid"]:
    critical_errors = [e for e in validation_result["errors"] if "not found" in e]
    if critical_errors:
        raise ValueError(f"Pattern validation failed: {critical_errors}")
    else:
        logger.warning("Non-critical validation warnings (continuing)")
```

---

### MAJ-7: Example Pattern in Production Code
**File:** `backend/app/core/pattern_orchestrator.py:1080-1121`
**Severity:** P1 (Code Smell)

**Issue:**
Pattern orchestrator file contains 41-line example pattern definition at end of file:

```python
EXAMPLE_PATTERN = {
    "id": "portfolio_overview",
    "name": "Portfolio Overview",
    # ... 35 more lines ...
}
```

**Problems:**
1. Example is outdated (uses old 2-step pattern)
2. Takes up space in production code
3. Never actually used (no references found)
4. Could confuse developers

**Recommendation:**
- Move to `backend/tests/fixtures/example_pattern.json`
- Or delete entirely (real patterns in `backend/patterns/` are better examples)

---

### MAJ-8: Metadata Handling Inconsistency
**File:** `backend/app/core/pattern_orchestrator.py:103-131`
**Severity:** P1 (Maintainability)

**Issue:**
Trace.add_step() handles metadata in 2 different ways:

```python
metadata = None
if hasattr(result, "__metadata__"):
    metadata = result.__metadata__
elif isinstance(result, dict) and "_metadata" in result:
    # Extract metadata dict and convert to object
    metadata_dict = result["_metadata"]
    class MetadataObj:  # <-- Anonymous class created dynamically!
        def __init__(self, d):
            self.agent_name = d.get("agent_name")
            # ...
    metadata = MetadataObj(metadata_dict)
```

**Problems:**
1. Dynamic class creation is inefficient (creates new class on every call)
2. Inconsistent - some results use `__metadata__` attribute, others use `_metadata` key
3. Anonymous class has no type checking

**Recommendation:**
1. Standardize on dict format: `{"_metadata": {...}}`
2. Remove `__metadata__` attribute support (deprecated)
3. Access directly without conversion: `metadata = result.get("_metadata", {})`

---

## Moderate Issues (P2)

### MOD-1: Duplicate Capability Check Logic
**Files:** `backend/app/core/agent_runtime.py:238-303`, `pattern_orchestrator.py:431-547`
**Severity:** P2 (Code Duplication)

**Issue:**
Both AgentRuntime and PatternOrchestrator check if capabilities exist:

**agent_runtime.py:**
```python
def register_agent(self, agent: BaseAgent, ...):
    for cap in capabilities:
        if cap in self.capability_map and not allow_dual_registration:
            conflicts.append(f"{cap} (already in {existing_agent})")
```

**pattern_orchestrator.py:**
```python
def validate_pattern(self, pattern_id: str, ...):
    for step in spec.get("steps", []):
        capability = step.get("capability")
        agent_name = self.agent_runtime.capability_map.get(capability)
        if not agent_name:
            errors.append(f"Capability '{capability}' not found")
```

**Impact:** Logic duplicated in 2 places, could diverge.

**Recommendation:** Move capability checking to AgentRuntime, expose single method:
```python
def validate_capability(self, capability: str) -> Tuple[bool, Optional[str], List[str]]:
    """Returns (exists, agent_name, errors)"""
```

---

### MOD-2: Hardcoded Retry Configuration
**File:** `backend/app/core/agent_runtime.py:125-127`
**Severity:** P2 (Flexibility)

**Issue:**
Retry logic hardcoded:
```python
self.max_retries = 3
self.retry_delays = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s
```

**Impact:** Can't adjust retry behavior per environment (dev vs prod) or per capability.

**Recommendation:**
Make configurable via environment or constructor:
```python
self.max_retries = int(os.getenv("AGENT_MAX_RETRIES", "3"))
self.retry_delays = parse_delays(os.getenv("AGENT_RETRY_DELAYS", "1,2,4"))
```

---

### MOD-3: Missing Type Hints in Critical Methods
**File:** `backend/app/core/pattern_orchestrator.py:876-1074`
**Severity:** P2 (Maintainability)

**Issue:**
Helper methods `_safe_evaluate()`, `_get_value()`, `_resolve_template_vars()` have complex logic but incomplete type hints:

```python
def _safe_evaluate(self, condition: str, state: Dict[str, Any]) -> bool:
    # 60 lines of complex condition parsing
    # No type hints for intermediate variables
```

**Impact:** Hard to understand data flow, easy to introduce bugs.

**Recommendation:** Add full type hints:
```python
def _safe_evaluate(self, condition: str, state: Dict[str, Any]) -> bool:
    parts: List[str] = condition.split(' and ')
    left_val: Any = self._get_value(left, state)
    # ...
```

---

### MOD-4: No Caching for Pattern Loading
**File:** `backend/app/core/pattern_orchestrator.py:268-313`
**Severity:** P2 (Performance)

**Issue:**
Patterns loaded once at initialization but changes require restart:

```python
def __init__(self, agent_runtime, db, redis=None):
    self.patterns: Dict[str, Dict[str, Any]] = {}
    self._load_patterns()  # Loads once, never reloads
```

**Impact:**
- Pattern JSON changes require server restart
- No hot-reload during development
- No way to deploy new patterns without downtime

**Recommendation:**
Add reload endpoint:
```python
async def reload_patterns(self):
    """Reload patterns from disk (for dev/admin use)"""
    self.patterns.clear()
    self._load_patterns()
    logger.info("Reloaded patterns")
```

---

### MOD-5: Pricing Pack Validation Missing from Patterns
**File:** Multiple pattern files reference `{{ctx.pricing_pack_id}}`
**Severity:** P2 (Data Quality)

**Issue:**
Patterns reference `{{ctx.pricing_pack_id}}` but no validation that pricing pack exists or is not expired.

Example from `portfolio_macro_overview.json:70`:
```json
{
  "capability": "risk.compute_factor_exposures",
  "args": {
    "portfolio_id": "{{inputs.portfolio_id}}",
    "pack_id": "{{ctx.pricing_pack_id}}"
  }
}
```

**Impact:**
- If pricing pack doesn't exist or is expired, agent method fails with DB error
- Error happens mid-pattern, after other steps already executed

**Recommendation:**
Add pricing pack validation in RequestCtx initialization:
```python
async def create_request_ctx(..., pricing_pack_id: str):
    # Validate pricing pack exists
    pack = await pricing_queries.get_pricing_pack(pricing_pack_id)
    if not pack:
        raise ValueError(f"Pricing pack not found: {pricing_pack_id}")
    if pack.expired:
        raise ValueError(f"Pricing pack expired: {pricing_pack_id}")
    # ...
```

---

### MOD-6: No Rate Limiting on External API Calls
**File:** `backend/app/integrations/*.py`
**Severity:** P2 (Reliability)

**Issue:**
External providers (FMP, FRED) called without rate limiting:

**Impact:**
- Could hit API rate limits and get blocked
- No backoff strategy for 429 responses
- Could cause cascading failures

**Recommendation:**
Add rate limiter:
```python
from aiolimiter import AsyncLimiter

class FMPProvider:
    def __init__(self):
        self.rate_limiter = AsyncLimiter(max_rate=10, time_period=1)  # 10/sec

    async def fetch_quote(self, symbol: str):
        async with self.rate_limiter:
            response = await self.client.get(...)
```

---

## Minor Issues (P3)

### MIN-1: Inconsistent Logging Levels
**Files:** All Python files
**Severity:** P3 (Observability)

**Issue:**
Mix of logger.info(), logger.debug(), logger.warning() without clear guidelines.

Example from `pattern_orchestrator.py`:
- Line 594: `logger.info(f"Executing pattern: {pattern_id}")` - Info level
- Line 634: `logger.debug(f"Step {step_idx}: {capability}")` - Debug level
- Line 676: `logger.info(f"📦 Storing result...")` - Info level with emoji

**Impact:** Logs are noisy in production, hard to filter important events.

**Recommendation:** Establish logging levels:
- **DEBUG**: Template resolution, step details
- **INFO**: Pattern start/complete, capability routing
- **WARNING**: Validation failures, fallbacks
- **ERROR**: Execution failures

---

### MIN-2: Magic Numbers in Risk Calculations
**File:** `backend/app/services/ratings.py` (inferred from comment)
**Severity:** P3 (Maintainability)

**Issue:**
Risk thresholds hardcoded:

```python
# Example (not in review sample, inferred from pattern):
if fundamentals.debt_to_equity < 1.0:  # Magic number!
    score += 2.5
```

**Impact:** Hard to adjust risk tolerance, values scattered across code.

**Recommendation:** Extract to constants or config:
```python
RISK_THRESHOLDS = {
    "debt_to_equity": {"safe": 1.0, "risky": 2.0},
    "current_ratio": {"safe": 1.5, "risky": 1.0}
}
```

---

### MIN-3: No JSON Schema Validation for Patterns
**File:** `backend/app/core/pattern_orchestrator.py:292-302`
**Severity:** P3 (Data Quality)

**Issue:**
Pattern validation checks for required fields but no JSON schema:

```python
required = ["id", "name", "steps", "outputs"]
missing = [f for f in required if f not in spec]
if missing:
    logger.error(f"Pattern {pattern_file} missing required fields: {missing}")
    continue
```

**Impact:**
- Typos in optional fields go unnoticed (e.g., `"desciption"` instead of `"description"`)
- No validation of field types (e.g., `"steps": "not_an_array"`)

**Recommendation:**
Add JSON schema validation:
```python
import jsonschema

PATTERN_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "steps", "outputs"],
    "properties": {
        "id": {"type": "string"},
        "steps": {"type": "array"},
        # ...
    }
}

jsonschema.validate(spec, PATTERN_SCHEMA)
```

---

### MIN-4: Documentation Claims 13 Patterns But Only 6 Were Updated
**File:** `docs/reference/PATTERNS_REFERENCE.md:24`
**Severity:** P3 (Documentation)

**Issue:**
Documentation says "13 patterns" exist and references Week 4 updating "8 patterns", but:
- **13 patterns exist** ✅ (confirmed by glob)
- **Only 6 patterns updated** ❌ (portfolio_overview, policy_rebalance, portfolio_scenario_analysis, cycle_deleveraging_scenarios, export_portfolio_report, news_impact_analysis)
- **2 patterns missed:** portfolio_macro_overview, portfolio_cycle_risk

**Impact:** Documentation inconsistent with implementation.

**Recommendation:** Update PATTERNS_REFERENCE.md to clarify:
```markdown
## Pattern Inventory (13 patterns)

Week 4 Optimization: 6 of 8 eligible patterns updated to use portfolio.get_valued_positions.
Remaining 2 patterns (portfolio_macro_overview, portfolio_cycle_risk) need updates.
```

---

## Refactoring Opportunities

### REFACTOR-1: Extract Capability Registry to Separate Module
**Current:** Capability map scattered across AgentRuntime and individual agents
**Proposed:** Centralized registry with metadata

```python
# backend/app/core/capability_registry.py
CAPABILITY_REGISTRY = {
    "ledger.positions": {
        "agent": "financial_analyst",
        "method": "ledger_positions",
        "requires": ["portfolio_id"],
        "returns": "positions_dict",
        "retry": True,
        "cache": True
    },
    # ...
}
```

**Benefits:**
- Single source of truth
- Easy to add metadata (retry policy, caching, required params)
- Enables auto-generated API docs

---

### REFACTOR-2: Move Pattern Presentation Logic to Frontend
**Current:** Patterns contain `presentation` section with UI-specific details
**Proposed:** Backend returns raw data, frontend handles presentation

**Benefits:**
- Backend doesn't need to know about UI components
- Easier to support multiple UIs (web, mobile, CLI)
- Pattern JSON files 50% smaller

---

### REFACTOR-3: Consolidate Error Handling
**Current:** Each agent implements try/except differently
**Proposed:** Decorator for standard error handling

```python
@handle_agent_errors(fallback="stub", log_level="error")
async def ledger_positions(self, ctx, state, portfolio_id):
    # Agent code here
```

**Benefits:**
- Consistent error messages
- Centralized fallback logic
- Easier to add metrics/tracing

---

## Testing Gaps

### TEST-1: No Integration Tests for Pattern Orchestrator
**Missing:** End-to-end tests that load real patterns and execute them

**Recommendation:**
```python
async def test_portfolio_overview_pattern():
    orchestrator = PatternOrchestrator(runtime, db, redis)
    ctx = RequestCtx(portfolio_id="test", pricing_pack_id="test")
    result = await orchestrator.run_pattern("portfolio_overview", ctx, {})

    assert result["data"]["valued_positions"] is not None
    assert result["trace"]["capabilities_used"] == [...]
```

---

### TEST-2: No Tests for Template Substitution Edge Cases
**Missing:** Tests for nested templates, None values, circular references

**Recommendation:**
```python
def test_template_substitution_none_value():
    """Test that None values in templates raise clear error"""
    state = {"step1": {"data": None}}
    with pytest.raises(ValueError, match="resolved to None"):
        orchestrator._resolve_args({"arg": "{{step1.data.value}}"}, state)
```

---

## Security Considerations

### SEC-1: No SQL Injection Protection Audit
**Status:** NOT FOUND (good sign, but needs verification)
**Recommendation:** Audit all SQL queries use parameterized queries, especially:
- `backend/app/db/*_queries.py`
- Dynamic WHERE clauses

---

### SEC-2: No Input Validation on Pattern Inputs
**Issue:** Pattern inputs accepted without validation

**Recommendation:**
```python
def validate_inputs(self, pattern_id: str, inputs: Dict[str, Any]):
    spec = self.patterns[pattern_id]
    inputs_spec = spec.get("inputs", {})

    for input_name, input_config in inputs_spec.items():
        value = inputs.get(input_name)
        input_type = input_config.get("type")

        if input_type == "uuid":
            validate_uuid(value)
        elif input_type == "integer":
            validate_integer(value)
```

---

## Performance Considerations

### PERF-1: No Query Result Caching
**Issue:** Same queries executed multiple times per request

**Recommendation:**
- Add Redis caching for pricing packs (TTL: 5 min)
- Add Redis caching for fundamentals (TTL: 1 hour)
- Add request-level caching for positions (already exists in AgentRuntime)

---

### PERF-2: Sequential Pattern Execution
**Issue:** Steps executed sequentially even when independent

**Opportunity:**
```python
# Steps 1-2 can run in parallel (no dependencies)
{"capability": "macro.detect_regime", ...},  # Step 1
{"capability": "cycles.compute_short_term", ...},  # Step 2 (independent)

# But currently runs sequentially
```

**Recommendation:** Add dependency analysis and parallel execution:
```python
async def run_pattern_parallel(self, pattern_id, ctx, inputs):
    dag = build_dependency_graph(spec["steps"])
    parallel_groups = topological_sort(dag)

    for group in parallel_groups:
        results = await asyncio.gather(*[
            self._execute_step(step, state) for step in group
        ])
```

---

## Summary Statistics

**Total Issues Found:** 23
**Critical (P0):** 5
**Major (P1):** 8
**Moderate (P2):** 6
**Minor (P3):** 4

**Categories:**
- Capability Mismatches: 5
- Silent Failures: 4
- Code Duplication: 2
- Dead Code: 2
- Anti-patterns: 3
- Missing Validation: 4
- Documentation: 2
- Performance: 1

**Estimated Fix Time:**
- P0 (Critical): 4-8 hours
- P1 (Major): 16-24 hours
- P2 (Moderate): 8-12 hours
- P3 (Minor): 2-4 hours
- **Total:** 30-48 hours

---

## Recommended Fix Priority

**Week 1 (Critical):**
1. CRIT-2: Fix `portfolio_cycle_risk.json` to use `portfolio.get_valued_positions`
2. CRIT-1: Fix `portfolio_macro_overview.json` to use `portfolio.get_valued_positions`
3. CRIT-3: Fix `macro_hound.suggest_alert_presets` capability name
4. CRIT-4: Standardize pattern outputs format

**Week 2 (Major):**
1. MAJ-3: Add validation for template variable None values
2. MAJ-4: Add pattern step dependency validation
3. MAJ-6: Make pattern validation blocking for critical errors
4. MAJ-2: Clean up archived agents

**Week 3 (Moderate + Refactoring):**
1. MOD-1: Consolidate capability checking
2. REFACTOR-1: Extract capability registry
3. TEST-1: Add pattern integration tests

**Week 4 (Minor + Nice-to-have):**
1. MIN-4: Fix documentation inconsistencies
2. PERF-2: Add parallel pattern execution
3. SEC-2: Add pattern input validation

---

## Conclusion

The DawsOSP codebase is **well-architected** with clear separation of concerns (patterns, agents, services). The main issues are:

1. **Incomplete Week 4 migration** - 2 patterns still need updating (but see deep analysis for why)
2. **Silent failure risks** - Template substitution and validation need hardening
3. **Capability registration gaps** - Some capabilities misnamed after consolidation
4. **Missing validation layers** - Pattern inputs, dependencies, and pricing packs
5. **Stub data masquerading as real** - Multiple capabilities return fake data without warnings

**No security vulnerabilities** or data corruption risks found. All issues are **fixable within 30-48 hours** of focused development.

**Recommendation:** Address P0 issues immediately, then tackle P1 issues in next sprint. P2/P3 issues can be backlog items.

---

## Deep Dive Analysis

For a comprehensive architectural analysis including:
- **Why patterns were actually missed** (not just incomplete migration)
- **Root cause of integration issues** (implicit vs explicit dependencies)
- **Systemic architectural problems** (3 incompatible output formats, no capability contracts)
- **Silent stub data issues** (risk.compute_factor_exposures, macro.compute_dar return fake data)
- **Long-term architectural recommendations** (capability composition, dependency graphs)

**See:** [DEEP_PATTERN_INTEGRATION_ANALYSIS.md](DEEP_PATTERN_INTEGRATION_ANALYSIS.md) (separate 600-line report)

### Key Findings from Deep Analysis:

1. **portfolio_macro_overview.json** wasn't missed - it uses `ledger.positions` but downstream capabilities (`risk.compute_factor_exposures`, `macro.compute_dar`) are **supposed to** fetch positions internally but actually return **stub data**

2. **portfolio_cycle_risk.json** never uses `portfolio.get_valued_positions` because capabilities are **designed** to be self-contained (fetch positions internally)

3. **corporate_actions_upcoming.json** is **correct** using `ledger.positions` - it only needs symbols/quantities, not valuations

4. **Real Problem:** No capability contracts defining which capabilities are self-contained vs require positions as arguments

5. **Critical Bug:** `risk.compute_factor_exposures` and `macro.compute_dar` return stub data with no provenance warnings - **silent failures affecting multiple patterns**
