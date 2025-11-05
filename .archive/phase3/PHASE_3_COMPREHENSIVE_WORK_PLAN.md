# Phase 3 Comprehensive Work Plan with Agent Delegation Strategy

**Date:** November 3, 2025
**Purpose:** Master plan for Phase 3 cleanup, broader codebase improvements, and strategic agent delegation
**Status:** 🎯 **READY FOR EXECUTION**

---

## 📊 Executive Summary

This comprehensive plan integrates:
1. **Phase 3 Cleanup** (from PHASE_3_CLEANUP_PLAN_V2.md)
2. **Code Quality Improvements** (from CODE_REVIEW_REPORT_V2.md)
3. **Monitoring & Testing** (from PHASE_3_MONITORING_SIMULATION_PLAN.md)
4. **Strategic Agent Delegation** (new - using Task tool with specialized subagents)

**Total Work Identified:**
- **Phase 3 Cleanup:** ~8-10 hours (Phases A, B, C)
- **Broader Cleanup:** ~15-20 hours (additional improvements)
- **Testing & Validation:** ~5-8 hours
- **Total Estimated Effort:** ~28-38 hours

**Recommended Approach:** Delegate work to specialized subagents for parallel execution and faster completion.

---

## 🎯 Strategic Delegation Framework

### Available Subagent Types

Based on the Task tool capabilities, we can delegate to:

1. **general-purpose** - Complex multi-step tasks, code searches, autonomous implementation
   - Best for: Feature implementation, multi-file refactoring, complex migrations

2. **Explore** - Fast codebase exploration with thoroughness levels
   - Best for: Finding patterns, searching for duplications, analyzing code structure
   - Thoroughness: "quick", "medium", "very thorough"

3. **Plan** - Fast planning and design exploration
   - Best for: Creating implementation strategies, architectural decisions

### Delegation Strategy

**Parallel Execution:** Launch multiple agents simultaneously for independent tasks
**Sequential Execution:** Chain agents when tasks have dependencies
**Validation:** Always verify agent output before committing changes

---

## 📋 Work Breakdown with Agent Delegation

### PHASE A: Extract Common Patterns to BaseAgent (HIGH PRIORITY)

**Total Time:** 3-4 hours
**Delegation Strategy:** Single general-purpose agent can handle entire phase sequentially

#### Task A1: Extract TTL Constants (15 min) ⚡ QUICK WIN

**Agent:** general-purpose (model: haiku - simple task)
**Thoroughness:** quick
**Dependencies:** None

**Prompt for Agent:**
```
Extract TTL constants to BaseAgent:

1. Add constants to backend/app/agents/base_agent.py:
   - CACHE_TTL_DAY = 86400
   - CACHE_TTL_HOUR = 3600
   - CACHE_TTL_5MIN = 300
   - CACHE_TTL_NONE = 0

2. Search for all hardcoded instances: 86400, 3600, 300, 0 (in TTL context)

3. Replace in all agent files:
   - financial_analyst.py
   - macro_hound.py
   - data_harvester.py
   - ratings_agent.py
   - optimizer_agent.py
   - charts_agent.py
   - alerts_agent.py
   - reports_agent.py

4. Use self.CACHE_TTL_DAY, self.CACHE_TTL_HOUR, etc.

5. Return: List of files modified and line count saved

Do NOT run tests, just make the changes and report results.
```

---

#### Task A2: Extract AsOf Date Resolution (15 min) ⚡ QUICK WIN

**Agent:** general-purpose (model: haiku)
**Thoroughness:** quick
**Dependencies:** None (can run in parallel with A1)

**Prompt for Agent:**
```
Extract asof_date resolution helper to BaseAgent:

1. Add method to backend/app/agents/base_agent.py:
```python
def _resolve_asof_date(self, ctx: RequestCtx) -> date:
    """Resolve asof_date from context with fallback to today."""
    return ctx.asof_date or date.today()
```

2. Find all instances of: "ctx.asof_date or date.today()"

3. Replace with: self._resolve_asof_date(ctx)

4. Handle variations:
   - ctx.asof_date if ctx.asof_date else date.today()
   - Similar patterns

5. Return: Files modified, instances replaced, line count saved

Do NOT run tests, just make the changes and report results.
```

---

#### Task A3: Extract UUID Conversion (30 min)

**Agent:** general-purpose (model: haiku)
**Thoroughness:** medium
**Dependencies:** None (can run in parallel)

**Prompt for Agent:**
```
Extract UUID conversion helper to BaseAgent:

1. Add method to backend/app/agents/base_agent.py:
```python
def _to_uuid(self, value: Optional[str], param_name: str) -> Optional[UUID]:
    """Convert string to UUID with validation."""
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError as e:
        raise ValueError(f"Invalid {param_name} format: {value}") from e
```

2. Find all instances of: UUID(portfolio_id), UUID(security_id), etc.

3. Replace with: self._to_uuid(portfolio_id, "portfolio_id")

4. Add proper imports if needed

5. Return: Files modified, instances replaced, validation improvements

Do NOT run tests, just make the changes and report results.
```

---

#### Task A4: Extract Portfolio ID Resolution (30 min)

**Agent:** general-purpose (model: sonnet - more complex logic)
**Thoroughness:** medium
**Dependencies:** A3 (UUID helper must exist first)

**Prompt for Agent:**
```
Extract portfolio ID resolution helper to BaseAgent:

PRE-REQUISITE: Verify _to_uuid() helper exists in BaseAgent

1. Add method to backend/app/agents/base_agent.py:
```python
def _resolve_portfolio_id(
    self,
    portfolio_id: Optional[str],
    ctx: RequestCtx,
    capability_name: str
) -> UUID:
    """Resolve and validate portfolio_id from parameter or context."""
    if not portfolio_id:
        portfolio_id = str(ctx.portfolio_id) if ctx.portfolio_id else None
    if not portfolio_id:
        raise ValueError(f"portfolio_id required for {capability_name}")

    return self._to_uuid(portfolio_id, "portfolio_id")
```

2. Find pattern (15+ instances):
```python
if not portfolio_id:
    portfolio_id = str(ctx.portfolio_id) if ctx.portfolio_id else None
if not portfolio_id:
    raise ValueError(...)
portfolio_uuid = UUID(portfolio_id)
```

3. Replace with:
```python
portfolio_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "capability_name")
```

4. Update capability_name parameter with actual capability name

5. Return: Files modified (financial_analyst, optimizer_agent, macro_hound, etc.),
         line count saved (~45 lines expected)

Do NOT run tests, just make the changes and report results.
```

---

#### Task A5: Extract Pricing Pack ID Resolution (30 min)

**Agent:** general-purpose (model: sonnet)
**Thoroughness:** medium
**Dependencies:** None (can run in parallel with A4)

**Prompt for Agent:**
```
Extract TWO pricing pack ID helpers to BaseAgent:

CRITICAL: Two different patterns exist for good reasons - must create TWO helpers

1. Add methods to backend/app/agents/base_agent.py:

```python
def _require_pricing_pack_id(self, ctx: RequestCtx, capability_name: str) -> str:
    """Get pricing_pack_id from context (SACRED - required for reproducibility)."""
    if not ctx.pricing_pack_id:
        raise ValueError(f"pricing_pack_id required in context for {capability_name}")
    return ctx.pricing_pack_id

def _resolve_pricing_pack_id(
    self,
    pack_id: Optional[str],
    ctx: RequestCtx,
    default: Optional[str] = None
) -> str:
    """Resolve pricing_pack_id with fallback."""
    return pack_id or ctx.pricing_pack_id or default or "PP_latest"
```

2. Find SACRED pattern (optimizer capabilities):
   - Pattern: pricing_pack_id = ctx.pricing_pack_id; if not: raise ValueError
   - Replace with: self._require_pricing_pack_id(ctx, "capability_name")
   - Files: financial_analyst.py (propose_trades, analyze_impact, suggest_hedges, suggest_deleveraging_hedges)
   - Files: optimizer_agent.py (all methods)

3. Find Fallback pattern (other capabilities):
   - Pattern: pack_id or ctx.pricing_pack_id or "PP_latest"
   - Replace with: self._resolve_pricing_pack_id(pack_id, ctx)

4. Return: SACRED instances replaced, Fallback instances replaced, line count saved

Do NOT run tests, just make the changes and report results.
```

---

#### Task A6: Extract Ratings Extraction (30 min)

**Agent:** general-purpose (model: sonnet - complex logic)
**Thoroughness:** medium
**Dependencies:** None

**Prompt for Agent:**
```
Extract ratings extraction helper to BaseAgent:

1. Add method to backend/app/agents/base_agent.py:
```python
def _extract_ratings_from_state(
    self,
    state: Dict[str, Any],
    ratings: Optional[Dict[str, float]] = None
) -> Optional[Dict[str, float]]:
    """Extract ratings dict from state if not provided.

    Handles two modes:
    1. Portfolio Ratings Mode: ratings_result["positions"] - Array of position objects
    2. Single Security Ratings Mode: ratings_result["overall_rating"] - Single rating value

    Note:
        - Portfolio mode: Extracts {symbol: rating} from positions array
        - Single mode: Converts overall_rating (0-100) to 0-10 scale (divides by 10)
    """
    if ratings:
        return ratings

    if not state.get("ratings"):
        return None

    ratings_result = state["ratings"]

    # Portfolio ratings mode
    if isinstance(ratings_result, dict) and "positions" in ratings_result:
        return {
            pos["symbol"]: pos.get("rating", 0.0)
            for pos in ratings_result["positions"]
            if pos.get("rating") is not None
        }

    # Single security ratings mode
    elif isinstance(ratings_result, dict) and "overall_rating" in ratings_result:
        symbol = ratings_result.get("symbol")
        if symbol:
            # Convert 0-100 scale to 0-10 scale
            return {symbol: float(ratings_result["overall_rating"]) / 10.0}

    return None
```

2. Find pattern in:
   - financial_analyst.py: financial_analyst_propose_trades() (lines 2254-2269)
   - optimizer_agent.py: optimizer_propose_trades() (lines 176-191)

3. Replace ~16 line blocks with: ratings = self._extract_ratings_from_state(state, ratings)

4. Return: Files modified, line count saved (~48 lines expected)

Do NOT run tests, just make the changes and report results.
```

---

#### Task A7: Extract Policy Merging (45 min) 🔴 COMPLEX

**Agent:** general-purpose (model: sonnet)
**Thoroughness:** very thorough
**Dependencies:** None

**Prompt for Agent:**
```
Extract policy merging helper to FinancialAnalyst (NOT BaseAgent):

IMPORTANT: This helper goes in financial_analyst.py, not base_agent.py
REASON: Only used by propose_trades capability

1. Add method to backend/app/agents/financial_analyst.py:
```python
def _merge_policies_and_constraints(
    self,
    policies: Optional[Union[Dict, List]],
    constraints: Optional[Dict],
    default_policy: Optional[Dict] = None
) -> Dict[str, Any]:
    """Merge policies and constraints into unified policy dict.

    Used by: propose_trades capability (both old and new)

    Handles:
    - List format: [{type: 'min_quality_score', value: 5}, ...]
    - Dict format: {min_quality_score: 5, ...}
    - None: Uses default policy
    """
    merged_policy = {}

    # Handle policies
    if policies:
        if isinstance(policies, list):
            # Convert list of policies to dict format
            for policy in policies:
                if isinstance(policy, dict) and 'type' in policy:
                    policy_type = policy['type']
                    value = policy.get('value', 0.0)

                    if policy_type == 'min_quality_score':
                        merged_policy['min_quality_score'] = value
                    elif policy_type == 'max_single_position':
                        merged_policy['max_single_position_pct'] = value
                    elif policy_type == 'max_sector':
                        merged_policy['max_sector_pct'] = value
                    elif policy_type == 'target_allocation':
                        category = policy.get('category', '')
                        merged_policy[f'target_{category}'] = value
        else:
            # Use policies as base if it's a dict
            merged_policy = policies.copy() if isinstance(policies, dict) else {}

    # Merge constraints if provided
    if constraints and isinstance(constraints, dict):
        if 'max_turnover_pct' in constraints:
            merged_policy['max_turnover_pct'] = constraints['max_turnover_pct']
        if 'max_te_pct' in constraints:
            merged_policy['max_tracking_error_pct'] = constraints['max_te_pct']
        if 'min_lot_value' in constraints:
            merged_policy['min_lot_value'] = constraints['min_lot_value']

    # Apply default policy if provided and no policies merged
    if not merged_policy and default_policy:
        merged_policy = default_policy.copy()

    # Apply standard defaults if still empty
    if not merged_policy:
        merged_policy = {
            "min_quality_score": 0.0,
            "max_single_position_pct": 20.0,
            "max_sector_pct": 30.0,
            "max_turnover_pct": 20.0,
            "max_tracking_error_pct": 3.0,
            "method": "mean_variance",
        }

    return merged_policy
```

2. Find duplicated logic (~35 lines each) in:
   - financial_analyst.py: financial_analyst_propose_trades() (lines 2201-2236)
   - optimizer_agent.py: optimizer_propose_trades() (lines 123-158)

3. Replace with: merged_policy = self._merge_policies_and_constraints(policies, constraints, default_policy)

4. Verify both implementations are IDENTICAL before replacing

5. Return: Files modified, line count saved (~50 lines expected)

Do NOT run tests, just make the changes and report results.
```

---

### PHASE B: Fix Legacy Agent Duplications (MEDIUM PRIORITY)

**Total Time:** 2-3 hours
**Delegation Strategy:** Single agent after Phase A completes

#### Task B1: Extract Error Result Creation Helper (30 min)

**Agent:** general-purpose (model: sonnet)
**Thoroughness:** medium
**Dependencies:** A1, A2 (needs CACHE_TTL_NONE and _resolve_asof_date)

**Prompt for Agent:**
```
Extract error result creation helper to BaseAgent:

PRE-REQUISITES: Verify CACHE_TTL_NONE and _resolve_asof_date() exist

1. Add method to backend/app/agents/base_agent.py:
```python
def _create_error_result(
    self,
    error: Exception,
    ctx: RequestCtx,
    error_fields: Dict[str, Any],
    source: str
) -> Dict[str, Any]:
    """Create standardized error result with metadata.

    Example:
        # For ratings:
        self._create_error_result(
            e, ctx,
            {"overall": Decimal("0"), "symbol": symbol},
            "ratings_service"
        )

        # For optimizer:
        self._create_error_result(
            e, ctx,
            {"trades": [], "trade_count": 0},
            "optimizer_service"
        )
    """
    error_result = {
        **error_fields,
        "error": str(error),
    }
    metadata = self._create_metadata(
        source=f"{source}:error",
        asof=self._resolve_asof_date(ctx),
        ttl=self.CACHE_TTL_NONE,
    )
    return self._attach_metadata(error_result, metadata)
```

2. Find pattern (10+ instances):
```python
error_result = {
    # capability-specific fields
    "error": str(e),
}
metadata = self._create_metadata(source=..., asof=..., ttl=0)
return self._attach_metadata(error_result, metadata)
```

3. Replace with:
```python
return self._create_error_result(
    e, ctx,
    {capability_specific_fields},
    "service_name"
)
```

4. Return: Files modified, instances replaced (~10), line count saved (~90 lines)

Do NOT run tests, just make the changes and report results.
```

---

#### Task B2: Extract Helpers from RatingsAgent (1-2 hours) 🔴 COMPLEX

**Agent:** general-purpose (model: sonnet)
**Thoroughness:** very thorough
**Dependencies:** None (rating-specific, independent)

**Prompt for Agent:**
```
Extract rating helpers from RatingsAgent to match FinancialAnalyst:

CONTEXT: FinancialAnalyst already has these helpers (lines 2585-2730).
GOAL: Extract same helpers from RatingsAgent to reduce duplication (4x each).

1. Examine FinancialAnalyst helpers:
   - _resolve_rating_symbol()
   - _resolve_rating_fundamentals()
   - _transform_rating_fundamentals()
   - _validate_rating_fundamentals()
   - _attach_rating_success_metadata()
   - _attach_rating_error_metadata()
   - _rating_to_grade()

2. Find duplicated patterns in RatingsAgent (4 rating methods):
   - dividend_safety()
   - moat_strength()
   - resilience()
   - aggregate_ratings()

3. Extract helpers to RatingsAgent (same as FinancialAnalyst)

4. CRITICAL DIFFERENCES:
   - _resolve_rating_symbol(): RatingsAgent uses "STUB", FinancialAnalyst queries DB
     ACTION: Add database lookup to RatingsAgent (fix STUB bug)

   - _rating_to_grade(): DIFFERENT IMPLEMENTATIONS
     RatingsAgent: Simple A-F (90+ = A, 80+ = B, etc.)
     FinancialAnalyst: Detailed A+-F (93+ = A+, 90+ = A, 87+ = A-, etc.)
     ACTION: Keep both implementations, they serve different purposes

5. Replace duplicated logic in 4 rating methods

6. Return: Helpers extracted, instances replaced, STUB bug fix applied,
         line count saved (~110 lines expected)

Do NOT run tests, just make the changes and report results.
```

---

### PHASE C: Standardize Patterns (MEDIUM PRIORITY)

**Total Time:** 2-3 hours
**Delegation Strategy:** Can run in parallel (3 independent tasks)

#### Task C1: Standardize Agent Registration Names (30 min)

**Agent:** general-purpose (model: haiku)
**Thoroughness:** quick
**Dependencies:** None

**Prompt for Agent:**
```
Standardize agent registration names:

ISSUE: Agents registered with different names in different files

1. Check current names in:
   - combined_server.py (lines 343-373): ratings_agent, optimizer_agent, etc.
   - backend/app/api/executor.py (lines 141-176): ratings, optimizer, etc.

2. Standardize to: agent name WITHOUT _agent suffix
   - financial_analyst (not financial_analyst_agent)
   - macro_hound (not macro_hound_agent)
   - ratings (not ratings_agent)
   - optimizer (not optimizer_agent)
   - etc.

3. Update both files to use consistent names

4. CRITICAL: Agent names don't affect capability routing (capabilities registered separately)
   This is a safe rename.

5. Return: Files modified, names standardized, verification that routing unaffected

Do NOT run tests, just make the changes and report results.
```

---

#### Task C2: Standardize Exception Handling (1 hour)

**Agent:** Explore + general-purpose (2-step process)
**Thoroughness:** very thorough
**Dependencies:** None

**Step 1 - Explore Agent:**
```
Find all exception handling patterns in agent files:

Search for: "except Exception" in backend/app/agents/

Report:
1. Files with "except Exception as e:" + exc_info=True (GOOD)
2. Files with "except Exception as e:" WITHOUT exc_info=True (NEEDS FIX)
3. Files with "except Exception:" (no variable - NEEDS FIX)

Return comprehensive list of locations and patterns.
```

**Step 2 - general-purpose Agent:**
```
Standardize exception handling based on Explore agent findings:

1. STANDARD PATTERN:
```python
except Exception as e:
    logger.error(
        "Error message with context",
        exc_info=True,  # ← REQUIRED for stack traces
        extra={...}
    )
```

2. Update all inconsistent patterns found

3. Add to BaseAgent docstring:
```python
"""
Exception Handling Guidelines:
- Always use: except Exception as e:
- Always log with exc_info=True for debugging
- Include context in error messages
"""
```

4. Return: Files modified, patterns standardized, guidelines added

Do NOT run tests, just make the changes and report results.
```

---

#### Task C3: Standardize Dictionary Access Patterns (1 hour)

**Agent:** Explore + general-purpose (2-step process)
**Thoroughness:** very thorough
**Dependencies:** None

**Step 1 - Explore Agent:**
```
Find dictionary access patterns in agent files:

Search for patterns:
1. data["key"] - Direct access (KeyError risk)
2. data.get("key") - Safe access (returns None)
3. data.get("key", {}) - Safe with default

Report locations where direct access (pattern 1) is used.
Filter out cases where KeyError is intentional (e.g., required keys).
```

**Step 2 - general-purpose Agent:**
```
Standardize dictionary access patterns based on Explore findings:

1. STANDARD PATTERNS:
   - For optional keys: data.get("key", default)
   - For nested optional: data.get("key", {}).get("subkey", default)
   - For required keys: data["key"] (let it fail fast)

2. Update risky direct access to .get() with defaults

3. Add to BaseAgent docstring:
```python
"""
Dictionary Access Guidelines:
- Optional keys: Use .get("key", default)
- Required keys: Use data["key"] (fail fast)
- Nested access: Use .get() at each level
"""
```

4. Return: Files modified, patterns standardized, guidelines added

Do NOT run tests, just make the changes and report results.
```

---

### PHASE D: Broader Cleanup (LOWER PRIORITY)

**Total Time:** 10-15 hours
**Delegation Strategy:** Multiple parallel agents for independent improvements

#### Task D1: Remove Duplicate Console Logs (30 min) ⚡ QUICK WIN

**Agent:** Explore + general-purpose
**Thoroughness:** quick
**Dependencies:** None

**Explore Agent:**
```
Find all console.log statements in production code:

Search: "console.log" in backend/ (exclude test files, exclude .archive/)

Report: Files and line numbers with console.log statements
```

**general-purpose Agent:**
```
Remove console.log statements from production code:

Based on Explore findings:
1. Remove all console.log statements
2. Replace with proper logger calls if needed
3. Keep in test files if appropriate

Return: Files cleaned, console.log count removed
```

---

#### Task D2: Add Missing Type Hints (4 hours)

**Agent:** general-purpose (model: sonnet)
**Thoroughness:** very thorough
**Dependencies:** None

**Prompt:**
```
Add type hints to functions missing them:

FOCUS: Helper methods in agent files

1. Scan all agent files for functions without type hints
2. Add proper type hints:
   - Parameters: name: Type
   - Return: -> ReturnType
   - Optional: Optional[Type]
   - Dict: Dict[str, Any]

3. PRIORITY: Helper methods extracted in Phase A/B

4. Return: Files modified, functions annotated, type coverage improvement

Do NOT run tests, just make the changes and report results.
```

---

#### Task D3: Standardize Docstrings (2 hours)

**Agent:** general-purpose (model: sonnet)
**Thoroughness:** medium
**Dependencies:** D2 (type hints should exist)

**Prompt:**
```
Standardize docstrings to Google style:

FOCUS: Helper methods in agent files

1. STANDARD FORMAT:
```python
def method_name(self, param: Type) -> ReturnType:
    """Short description (one line).

    Longer description if needed.

    Args:
        param: Description

    Returns:
        Description of return value

    Raises:
        ExceptionType: When and why
    """
```

2. Update all helper methods added in Phase A/B

3. Ensure consistency across all agent files

4. Return: Files modified, docstrings standardized

Do NOT run tests, just make the changes and report results.
```

---

#### Task D4: Extract Service Initialization Pattern (1 hour)

**Agent:** Explore + general-purpose
**Thoroughness:** medium
**Dependencies:** None

**Explore Agent:**
```
Find service initialization patterns:

Search for:
1. get_optimizer_service()
2. get_ratings_service()
3. MacroService() (direct instantiation)
4. Other service instantiations

Report: Patterns used, inconsistencies found
```

**general-purpose Agent:**
```
Standardize service initialization:

Based on Explore findings:
1. Ensure all services use get_*_service() singleton pattern
2. Replace MacroService() with get_macro_service()
3. Document pattern in BaseAgent

Return: Files modified, patterns standardized
```

---

### PHASE E: Testing & Validation (CRITICAL)

**Total Time:** 5-8 hours
**Delegation Strategy:** Sequential (depends on all previous phases)

#### Task E1: Integration Testing Plan (2 hours)

**Agent:** Plan
**Thoroughness:** very thorough
**Dependencies:** Phases A-D complete

**Prompt:**
```
Create comprehensive integration testing plan:

CONTEXT: Major refactoring completed (Phases A-D)
GOAL: Verify all capabilities still work

Plan should include:
1. Test all 15 consolidated capabilities
2. Test feature flag routing (100% rollout)
3. Test error handling paths
4. Test concurrent requests
5. Memory usage validation

Return: Detailed test plan with test cases, expected behaviors, pass criteria
```

---

#### Task E2: Execute Integration Tests (3-4 hours)

**Agent:** general-purpose (model: sonnet)
**Thoroughness:** very thorough
**Dependencies:** E1 complete

**Prompt:**
```
Execute integration test plan:

1. Follow test plan from E1
2. Test each capability systematically
3. Verify feature flags work correctly
4. Test error scenarios
5. Monitor memory usage

Return: Test results, pass/fail status, issues found, performance metrics
```

---

#### Task E3: Performance Benchmarking (2 hours)

**Agent:** general-purpose (model: sonnet)
**Thoroughness:** very thorough
**Dependencies:** E2 complete (tests passing)

**Prompt:**
```
Benchmark performance after refactoring:

GOAL: Verify refactoring didn't degrade performance

1. Benchmark key capabilities:
   - propose_trades
   - dividend_safety
   - macro_overview_charts
   - suggest_alert_presets
   - render_pdf

2. Compare to baseline (if available)

3. Measure:
   - Response times (P50, P95, P99)
   - Memory usage
   - Database query counts

4. Return: Performance report, any regressions identified

Do NOT fix issues, just report findings.
```

---

## 🚀 Execution Strategy

### Recommended Execution Order

**Week 1: High-Priority Cleanup (Phase A)**
- Day 1: Tasks A1-A3 (TTL, AsOf, UUID) - Launch 3 agents in parallel
- Day 2: Tasks A4-A5 (Portfolio ID, Pricing Pack ID) - Launch 2 agents in parallel
- Day 3: Tasks A6-A7 (Ratings, Policy Merging) - Sequential execution
- Day 4: Code review + manual verification
- Day 5: Buffer day for issues

**Week 2: Medium-Priority Work (Phases B-C)**
- Day 1: Task B1 (Error Result Helper) - Single agent
- Day 2-3: Task B2 (RatingsAgent Helpers) - Single agent (complex)
- Day 4: Tasks C1-C3 (Standardization) - Launch 3 agents in parallel
- Day 5: Code review + manual verification

**Week 3: Broader Cleanup (Phase D)**
- Day 1: Tasks D1-D2 (Console logs, Type hints) - Parallel
- Day 2: Tasks D3-D4 (Docstrings, Service init) - Parallel
- Day 3-4: Additional improvements as needed
- Day 5: Code review

**Week 4: Testing & Validation (Phase E)**
- Day 1: Task E1 (Test planning) - Plan agent
- Day 2-3: Task E2 (Integration tests) - Execute
- Day 4: Task E3 (Performance benchmarking)
- Day 5: Final report + sign-off

---

## 📊 Success Metrics

### Code Quality Improvements
- [ ] ~450 lines of code removed (duplication eliminated)
- [ ] All helpers extracted to BaseAgent/FinancialAnalyst
- [ ] TTL constants used consistently (30+ instances)
- [ ] Error handling standardized across all agents
- [ ] Type hints added to all helper methods

### Testing Validation
- [ ] All 15 consolidated capabilities tested
- [ ] Feature flags verified at 100% rollout
- [ ] No performance regressions detected
- [ ] Memory usage within acceptable limits
- [ ] Error handling paths validated

### Production Readiness
- [ ] All feature flags stable at 100%
- [ ] Legacy agents can be safely removed
- [ ] Documentation updated
- [ ] Monitoring instrumented
- [ ] Team sign-off obtained

---

## 🎯 Agent Delegation Commands

### Parallel Execution Example (Tasks A1-A3)

```
I need to execute Phase A tasks A1, A2, and A3 in parallel.

Please launch 3 general-purpose agents with model=haiku:

Agent 1: Extract TTL Constants
[Use prompt from Task A1]

Agent 2: Extract AsOf Date Resolution
[Use prompt from Task A2]

Agent 3: Extract UUID Conversion
[Use prompt from Task A3]

Report when all 3 agents complete.
```

### Sequential Execution Example (Task A4 depends on A3)

```
Execute Task A4: Extract Portfolio ID Resolution

This depends on A3 (UUID helper) completing first.

Launch 1 general-purpose agent with model=sonnet:
[Use prompt from Task A4]
```

### Explore + Execute Pattern (Task C2)

```
Execute Task C2: Standardize Exception Handling (2-step process)

Step 1: Launch Explore agent to find patterns
[Use Explore prompt from Task C2]

Step 2: After Explore completes, launch general-purpose agent to fix
[Use general-purpose prompt from Task C2]
```

---

## ⚠️ Risk Mitigation

### Before Each Phase
1. **Backup current state:** `git commit` before launching agents
2. **Review agent plan:** Ensure prompts are clear and complete
3. **Check dependencies:** Verify prerequisite tasks completed

### During Execution
1. **Monitor agent output:** Check for errors or unexpected changes
2. **Validate changes:** Review diffs before committing
3. **Test incrementally:** Don't accumulate untested changes

### After Each Phase
1. **Manual code review:** Check agent changes for correctness
2. **Run syntax checks:** `python3 -m py_compile` on modified files
3. **Commit atomically:** One commit per phase with clear message
4. **Push to remote:** Keep remote repo synchronized

---

## 📝 Documentation Updates Required

After completion, update:
1. **PHASE_3_CONSOLIDATION_SUMMARY.md** - Mark cleanup complete
2. **CODE_REVIEW_REPORT_V2.md** - Mark issues resolved
3. **PROJECT_CONTEXT.md** - Update agent status (9→4 agents)
4. **ARCHITECTURE.md** - Document helper methods in BaseAgent
5. **README.md** - Update cleanup completion status

---

## 🎓 Lessons Learned (To Document)

### What Worked Well
- Parallel agent delegation for independent tasks
- Explore agent for pattern discovery before fixes
- Incremental testing after each phase

### What To Improve
- Earlier helper extraction during consolidation
- More upfront planning for shared patterns
- Better documentation of "why" decisions made

### Best Practices Established
- Always extract helpers for patterns repeated 3+ times
- Use Explore agent before implementing fixes
- Test with real data, not just unit tests
- Document unique considerations for each pattern

---

**Last Updated:** November 3, 2025
**Status:** 🎯 **READY FOR EXECUTION**
**Prepared By:** Claude IDE Agent (PRIMARY)

**Next Step:** User approval to begin Phase A execution with parallel agent delegation.
