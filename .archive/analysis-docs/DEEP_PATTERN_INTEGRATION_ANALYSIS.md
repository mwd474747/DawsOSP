# Deep Pattern Integration Analysis
**Date:** November 5, 2025
**Reviewer:** Claude (Deep Dive)
**Focus:** Pattern structure, integration issues, why patterns were missed, architectural improvements

---

## Executive Summary

After deep analysis of all 13 patterns and their capability dependencies, I've identified **systemic architectural issues** that explain why patterns were missed in Week 4 and reveal deeper integration problems.

**Key Findings:**
1. **Inconsistent Pattern Architecture** - 3 different pattern styles with no clear guidelines
2. **Missing Abstraction Layers** - Some patterns need positions, others need valued positions, leading to confusion
3. **Implicit vs Explicit Dependencies** - Some capabilities internally fetch positions, others require them as arguments
4. **Output Structure Chaos** - 3 incompatible output formats confusing the orchestrator

---

## Pattern Architecture Analysis

### Pattern Classification

After analyzing all 13 patterns, they fall into 3 distinct architectural categories:

#### Category A: Portfolio-Centric Patterns (8 patterns)
**Characteristic:** Need portfolio positions + pricing data
**Pattern:** `ledger.positions` OR `portfolio.get_valued_positions` → downstream analysis

**Patterns in this category:**
1. ✅ portfolio_overview.json (USES abstraction)
2. ✅ portfolio_scenario_analysis.json (USES abstraction)
3. ✅ policy_rebalance.json (USES abstraction)
4. ✅ export_portfolio_report.json (USES abstraction)
5. ✅ cycle_deleveraging_scenarios.json (USES abstraction)
6. ✅ news_impact_analysis.json (USES abstraction)
7. ❌ portfolio_macro_overview.json (MISSED - uses ledger.positions only)
8. ❌ corporate_actions_upcoming.json (MISSED - uses ledger.positions only)

**Why 2 were missed:**
- `portfolio_macro_overview.json` - Uses `ledger.positions` but downstream capabilities (`risk.compute_factor_exposures`, `macro.compute_dar`) need pricing data
- `corporate_actions_upcoming.json` - Uses `ledger.positions` but only needs symbols, not valuations (actually correct!)

#### Category B: Macro-Only Patterns (2 patterns)
**Characteristic:** No portfolio dependency, pure macro analysis
**Pattern:** No positions needed

**Patterns:**
1. macro_cycles_overview.json - Pure cycle analysis
2. macro_trend_monitor.json - Regime/factor trends (has portfolio_id for history)

**These patterns correctly don't use portfolio.get_valued_positions**

#### Category C: Hybrid Patterns (3 patterns)
**Characteristic:** Need positions but NOT for valuation
**Pattern:** Mixed - some steps need positions, others don't

**Patterns:**
1. portfolio_cycle_risk.json - Gets positions indirectly through `risk.compute_factor_exposures`
2. holding_deep_dive.json - Single position detail (doesn't need all positions)
3. buffett_checklist.json - Single security analysis (no portfolio positions)

---

## Root Cause Analysis: Why Patterns Were Missed

### Issue 1: Implicit vs Explicit Position Fetching

**Problem:** Some capabilities fetch positions internally, others require them as arguments.

#### Pattern 1: Explicit Position Fetching (CORRECT)
```json
{
  "steps": [
    {"capability": "portfolio.get_valued_positions", "as": "valued"},
    {"capability": "metrics.compute_twr", "args": {"positions": "{{valued.positions}}"}}
  ]
}
```

#### Pattern 2: Implicit Position Fetching (HIDDEN DEPENDENCY)
```json
{
  "steps": [
    {
      "capability": "risk.compute_factor_exposures",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}", "pack_id": "{{ctx.pricing_pack_id}}"}
    }
  ]
}
```

**What happens inside `risk.compute_factor_exposures`:**
```python
# financial_analyst.py:1066
async def risk_compute_factor_exposures(self, ctx, state, portfolio_id, pack_id):
    # THIS METHOD DOESN'T ACTUALLY FETCH POSITIONS!
    # It just returns stub data!
    logger.warning("Using fallback factor exposures - FactorAnalysisService not available")
    return {"factors": {...}}  # Stub data
```

**CRITICAL FINDING:** `risk.compute_factor_exposures` is **not implemented** - it returns stub data!
- `portfolio_macro_overview.json` calls this capability expecting real analysis
- `portfolio_cycle_risk.json` calls this capability expecting real analysis
- Both patterns will get stub data with no indication of failure

**This is a silent failure!**

---

### Issue 2: portfolio_macro_overview.json Deep Dive

**Current Structure:**
```json
{
  "steps": [
    {"capability": "ledger.positions", "as": "positions"},           // Step 1: Get positions
    {"capability": "macro.detect_regime", "as": "regime"},           // Step 2: Macro (independent)
    {"capability": "macro.get_indicators", "as": "indicators"},      // Step 3: Macro (independent)
    {"capability": "risk.compute_factor_exposures", "as": "factors"}, // Step 4: NEEDS VALUED POSITIONS
    {"capability": "macro.compute_dar", "as": "dar"},                // Step 5: NEEDS VALUED POSITIONS
    {"capability": "financial_analyst.macro_overview_charts", "as": "charts"} // Step 6: Chart rendering
  ]
}
```

**Problem Analysis:**

1. **Step 1 gets unpriced positions** from `ledger.positions`
   - Returns: `{"positions": [{"symbol": "AAPL", "quantity": 100, ...}]}`
   - Missing: `market_value`, `current_price`, `total_value`

2. **Step 4 needs priced positions** to compute factor exposures
   - Signature: `risk.compute_factor_exposures(portfolio_id, pack_id)`
   - **Expectation:** Should fetch positions internally and compute real exposures
   - **Reality:** Returns stub data (line 1086: "Using fallback factor exposures")

3. **Step 5 needs priced positions** to compute DaR
   - Signature: `macro.compute_dar(portfolio_id, pack_id, confidence)`
   - **Expectation:** Should run scenarios on valued portfolio
   - **Reality:** Probably also using stub/mock data

**Why it was missed in Week 4:**
- Pattern starts with `ledger.positions` (old style)
- But downstream capabilities (`risk.*`, `macro.*`) take `portfolio_id` not `positions` argument
- Developer assumed these capabilities fetch positions internally
- **Week 4 search looked for patterns using BOTH `ledger.positions` AND `pricing.apply_pack`**
- This pattern only uses `ledger.positions`, so it wasn't flagged

**Correct Fix Options:**

**Option A: Make capabilities self-contained (RECOMMENDED)**
```json
{
  "steps": [
    {"capability": "macro.detect_regime", "as": "regime"},
    {"capability": "macro.get_indicators", "as": "indicators"},
    {
      "capability": "risk.compute_factor_exposures",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "pack_id": "{{ctx.pricing_pack_id}}"
      },
      "as": "factors"
      // This capability should fetch + price positions internally
    },
    {"capability": "macro.compute_dar", "args": {...}, "as": "dar"}
  ]
}
// Remove ledger.positions step entirely
```

**Option B: Pass valued positions explicitly**
```json
{
  "steps": [
    {"capability": "portfolio.get_valued_positions", "as": "valued"},
    {"capability": "macro.detect_regime", "as": "regime"},
    {"capability": "macro.get_indicators", "as": "indicators"},
    {
      "capability": "risk.compute_factor_exposures",
      "args": {
        "positions": "{{valued.positions}}",
        "total_value": "{{valued.total_value}}"
      },
      "as": "factors"
    }
  ]
}
// Requires changing risk.compute_factor_exposures signature
```

---

### Issue 3: portfolio_cycle_risk.json Deep Dive

**Current Structure:**
```json
{
  "steps": [
    {"capability": "cycles.compute_short_term", "as": "stdc"},      // Step 1: Macro (independent)
    {"capability": "cycles.compute_long_term", "as": "ltdc"},       // Step 2: Macro (independent)
    {"capability": "risk.compute_factor_exposures", "as": "factors"}, // Step 3: NEEDS positions
    {"capability": "risk.overlay_cycle_phases", "as": "risk_map"},  // Step 4: Uses step 1-3
    {"capability": "macro.compute_dar", "as": "dar"}                // Step 5: NEEDS positions
  ]
}
```

**Problem:** Pattern **never fetches positions** at all!

**Dependency Analysis:**
1. Steps 1-2: Cycle analysis (no portfolio needed) ✅
2. Step 3: `risk.compute_factor_exposures(portfolio_id, pack_id)` - **Assumes internal position fetch**
3. Step 4: `risk.overlay_cycle_phases(factors, stdc, ltdc)` - Pure computation ✅
4. Step 5: `macro.compute_dar(portfolio_id, cycle_adjusted=true)` - **Assumes internal position fetch**

**Why it works (poorly):**
- Capabilities return stub data
- No actual position analysis happens
- Pattern completes successfully with meaningless results

**Why it was missed in Week 4:**
- Pattern never uses `ledger.positions` at all
- Week 4 search was looking for `ledger.positions` + `pricing.apply_pack` pair
- This pattern has neither, so it wasn't considered

**Architectural Decision Needed:**
Should `risk.compute_factor_exposures` be:
- **Self-contained** (fetches positions internally) → No pattern change needed
- **Pure function** (requires positions as argument) → Pattern needs `portfolio.get_valued_positions` first

---

### Issue 4: corporate_actions_upcoming.json Analysis

**Current Structure:**
```json
{
  "steps": [
    {"capability": "ledger.positions", "as": "positions"},
    {"capability": "corporate_actions.upcoming", "as": "actions"},
    {
      "capability": "corporate_actions.calculate_impact",
      "args": {
        "actions": "{{actions.actions}}",
        "holdings": "{{positions.positions}}"
      },
      "as": "actions_with_impact"
    }
  ]
}
```

**Analysis:** This pattern is **CORRECT AS-IS**!

**Why:**
- Corporate actions only need `symbol` and `quantity` from positions
- Does NOT need `market_value` or `current_price`
- Using `ledger.positions` is appropriate here

**Why it was flagged:**
- Uses `ledger.positions` so I initially thought it needed updating
- But on deeper analysis, it doesn't need pricing data

**Recommendation:** Keep as-is, add comment to pattern:
```json
{
  "steps": [
    {
      "capability": "ledger.positions",
      "as": "positions",
      "description": "Get positions (symbols + quantities only, pricing not needed)"
    }
  ]
}
```

---

## Architectural Problems

### Problem 1: No Clear Capability Contract

**Current State:** Capabilities have unclear interfaces

**Example: Multiple Ways to Get Portfolio Data**

```
ledger.positions → {positions: [...], currency: "USD"}
  └─ Returns: Unpriced positions (quantity, symbol, cost_basis)

pricing.apply_pack → {positions: [...], total_value: X}
  └─ Requires: Positions from ledger.positions
  └─ Returns: Priced positions (+ market_value, current_price)

portfolio.get_valued_positions → {positions: [...], total_value: X}
  └─ Abstraction combining above two
  └─ Returns: Same as pricing.apply_pack
```

**Problem:** No clear guidance on which to use when

**Solution:** Define capability contracts

```python
# backend/app/core/capability_contracts.py

CAPABILITY_CONTRACTS = {
    "ledger.positions": {
        "inputs": ["portfolio_id"],
        "outputs": {
            "positions": "List[Position]",  # Unpriced
            "currency": "str"
        },
        "use_when": "You need position quantities/symbols only (no valuation needed)"
    },

    "portfolio.get_valued_positions": {
        "inputs": ["portfolio_id", "pack_id"],
        "outputs": {
            "positions": "List[ValuedPosition]",  # Priced
            "total_value": "Decimal",
            "currency": "str"
        },
        "use_when": "You need position market values for analysis/metrics"
    },

    "risk.compute_factor_exposures": {
        "inputs": ["portfolio_id", "pack_id"],
        "outputs": {"factors": "Dict[str, float]"},
        "fetches_positions": True,  # Documents internal behavior
        "use_when": "Compute portfolio factor betas"
    }
}
```

---

### Problem 2: Inconsistent Step Dependency Patterns

**Pattern A: Sequential Dependencies (Good)**
```json
{
  "steps": [
    {"capability": "portfolio.get_valued_positions", "as": "valued"},
    {"capability": "metrics.compute_twr", "args": {"positions": "{{valued.positions}}"}},
    {"capability": "charts.overview", "args": {"metrics": "{{metrics}}"}}
  ]
}
```
✅ Clear data flow: valued → metrics → charts

**Pattern B: Parallel + Merge (Good)**
```json
{
  "steps": [
    {"capability": "macro.detect_regime", "as": "regime"},
    {"capability": "cycles.compute_short_term", "as": "stdc"},
    {"capability": "risk.overlay", "args": {"regime": "{{regime}}", "cycle": "{{stdc}}"}}
  ]
}
```
✅ Steps 1-2 can run in parallel, step 3 merges them

**Pattern C: Hidden Dependencies (BAD)**
```json
{
  "steps": [
    {"capability": "ledger.positions", "as": "positions"},  // Gets positions
    {"capability": "macro.compute_dar", "args": {"portfolio_id": "..."}}  // Ignores step 1!
  ]
}
```
❌ Step 2 doesn't use step 1 output - why is step 1 there?

**Found in:** `portfolio_macro_overview.json` - Step 1 (positions) never used!

---

### Problem 3: Output Structure Inconsistency

**Three incompatible formats found:**

#### Format 1: Simple List (3 patterns)
```json
{
  "outputs": ["valued", "metrics", "attribution"]
}
```
**Used by:** buffett_checklist, macro_cycles_overview, portfolio_scenario_analysis

**Orchestrator behavior:**
```python
# pattern_orchestrator.py:726
output_keys = outputs_spec  # List of strings
for output_key in output_keys:
    outputs[output_key] = state[output_key]
```

**Result:** `{"data": {"valued": {...}, "metrics": {...}}}`

---

#### Format 2: Dict with Panels (6 patterns)
```json
{
  "outputs": {
    "panels": [
      {"id": "summary", "title": "Summary", "dataPath": "valued.summary"}
    ]
  }
}
```
**Used by:** portfolio_macro_overview, portfolio_cycle_risk, macro_trend_monitor, corporate_actions_upcoming, holding_deep_dive, policy_rebalance

**Orchestrator behavior:**
```python
# pattern_orchestrator.py:726
if isinstance(outputs_spec, dict):
    output_keys = list(outputs_spec.keys())  # ["panels"]
```

**Result:** `{"data": {"panels": [...]}}`

**PROBLEM:** Orchestrator returns panels structure but not actual step results!

---

#### Format 3: Dict with Keys (4 patterns)
```json
{
  "outputs": {
    "stdc": "Short-term debt cycle",
    "ltdc": "Long-term debt cycle"
  }
}
```
**Used by:** macro_cycles_overview (hybrid - has both formats!)

**Orchestrator behavior:**
```python
output_keys = list(outputs_spec.keys())  # ["stdc", "ltdc"]
```

**Result:** `{"data": {"stdc": {...}, "ltdc": {...}}}`

---

### Problem 3 Impact Analysis

**Current Code (pattern_orchestrator.py:722-744):**
```python
outputs = {}
outputs_spec = spec.get("outputs", {})
if isinstance(outputs_spec, dict):
    output_keys = list(outputs_spec.keys())  # ← GETS WRONG KEYS FOR FORMAT 2!
else:
    output_keys = outputs_spec

# Debug logging for macro pattern issue
if pattern_id == "macro_cycles_overview":
    logger.info(f"DEBUG: outputs_spec type: {type(outputs_spec)}, value: {outputs_spec}")
    logger.info(f"DEBUG: output_keys: {output_keys}")
    logger.info(f"DEBUG: state keys: {list(state.keys())}")

for output_key in output_keys:
    if output_key in state:
        outputs[output_key] = state[output_key]
```

**Actual Behavior for Format 2:**
```python
# portfolio_macro_overview.json
outputs_spec = {
  "panels": [{"id": "regime_card", ...}, {"id": "factor_exposures", ...}]
}

# Orchestrator execution:
output_keys = ["panels"]  # list(outputs_spec.keys())

# Result:
outputs = {
  "panels": [...]  # Returns panels structure, not regime/factors/dar/indicators!
}
```

**Fix Needed:**
```python
outputs_spec = spec.get("outputs", {})

# Handle panels-style outputs
if isinstance(outputs_spec, dict) and "panels" in outputs_spec:
    # Extract step names from all steps
    output_keys = [step.get("as") for step in spec["steps"] if step.get("as")]
elif isinstance(outputs_spec, dict):
    output_keys = list(outputs_spec.keys())
else:
    output_keys = outputs_spec
```

---

## Integration Issues

### Issue 1: macro.compute_dar Doesn't Actually Compute

**Code Analysis (macro_hound.py:639-690):**
```python
async def macro_compute_dar(self, ctx, state, portfolio_id, pack_id, ...):
    """
    Compute Drawdown at Risk (DaR).

    DaR Methodology:
    - DaR = Percentile of scenario drawdowns (e.g., 95th percentile)
    - Runs 9 pre-defined scenarios
    """
    # Current implementation (line 690+):
    # TODO: Actually implement scenario running
    # For now, return stub data

    return {
        "dar_value": -0.185,  # HARDCODED
        "dar_amount": -25900.00,
        "confidence": 0.95,
        "scenarios_run": 9,  # FAKE
        # ...
    }
```

**Impact:**
- `portfolio_macro_overview.json` → Gets stub DaR
- `portfolio_cycle_risk.json` → Gets stub DaR
- Both patterns return successfully with meaningless data
- **Silent failure** - no indication data is stub

**Recommendation:**
```python
result = {
    "dar_value": -0.185,
    "confidence": 0.95,
    "_provenance": {
        "type": "stub",
        "warnings": ["DaR computation not implemented - using fallback data"]
    }
}
```

---

### Issue 2: risk.compute_factor_exposures Uses Stub Data

**Code Analysis (financial_analyst.py:1066-1113):**
```python
async def risk_compute_factor_exposures(self, ctx, state, portfolio_id, pack_id):
    logger.warning("Using fallback factor exposures - FactorAnalysisService not available")

    # Generate reasonable factor exposures based on portfolio
    result = {
        "factors": {
            "Real Rates": 0.5,  # HARDCODED
            "Inflation": 0.3,
            "Credit": 0.7,
            # ...
        },
        "market_beta": 1.15,
        "r_squared": 0.82
    }

    # Return result directly without metadata
    return result
```

**Impact:**
- `portfolio_macro_overview.json` → Gets fake factor exposures
- `portfolio_cycle_risk.json` → Gets fake factor exposures
- `macro_trend_monitor.json` → Gets fake factor exposure history

**Why This is Dangerous:**
1. No `_provenance` field to indicate stub data
2. Returns directly without metadata wrapping
3. Values look plausible (0.3-0.7 range)
4. User sees "factor exposures" and trusts them

**Recommendation:**
```python
result = {
    "factors": {...},
    "_provenance": {
        "type": "stub",
        "warnings": ["FactorAnalysisService not implemented - using fallback data"],
        "confidence": 0.0
    }
}
```

---

### Issue 3: Pattern Outputs Don't Match UI Expectations

**Problem:** UI expects specific panel structure, patterns return different structure

**Example: portfolio_macro_overview.json**

**Pattern Output Structure:**
```json
{
  "data": {
    "panels": [
      {"id": "regime_card", "title": "Current Regime", ...}
    ]
  }
}
```

**UI Expectation (dawsos-ui/src/pages/macro.tsx):**
```typescript
interface MacroData {
  regime: RegimeData;      // ← Expects top-level
  indicators: Indicators;  // ← Expects top-level
  factors: FactorData;     // ← Expects top-level
}
```

**Mismatch:** Pattern returns `panels` structure, UI expects flat structure

**Current Workaround:** Frontend extracts from panels? Or uses direct API calls?

**Recommendation:** Standardize on flat output structure:
```json
{
  "outputs": ["regime", "indicators", "factor_exposures", "dar"]
}
```

---

## Structural Issues

### Issue 1: No Validation of Capability Inputs/Outputs

**Current State:** Capabilities can return anything, no schema validation

**Example:**
```python
async def risk_compute_factor_exposures(self, ...):
    return {"factors": {...}}  # No schema validation
```

**Problem:**
- If method typos field name (`factor_exposures` instead of `factors`), pattern breaks silently
- If method changes return structure, patterns break
- No contract enforcement

**Recommendation:** Add Pydantic schemas
```python
from pydantic import BaseModel

class FactorExposuresOutput(BaseModel):
    factors: Dict[str, float]
    portfolio_volatility: float
    market_beta: float

async def risk_compute_factor_exposures(self, ...) -> FactorExposuresOutput:
    result = FactorExposuresOutput(
        factors={...},
        portfolio_volatility=0.185,
        market_beta=1.15
    )
    return result.dict()
```

---

### Issue 2: No Pattern Dependency Validation

**Current State:** Patterns can reference undefined steps

**Example (hypothetical bad pattern):**
```json
{
  "steps": [
    {"capability": "ledger.positions", "as": "positions"},
    {
      "capability": "metrics.compute_twr",
      "args": {"positions": "{{valued_positions.positions}}"},  // UNDEFINED!
      "as": "metrics"
    }
  ]
}
```

**Current Behavior:**
- Pattern loads successfully
- Executes step 1
- Step 2 tries to resolve `{{valued_positions.positions}}` → None
- Passes None to `metrics.compute_twr`
- Method crashes with confusing error

**Recommendation (Already in findings report):** Add dependency validation in `validate_pattern()`

---

### Issue 3: Duplicate Logic Across Agents

**Finding:** Multiple agents implement similar logic

**Example 1: Position Fetching**
```python
# financial_analyst.py:135
async def ledger_positions(self, ctx, state, portfolio_id):
    async with get_db_connection_with_rls(ctx.user_id) as conn:
        rows = await conn.fetch("""
            SELECT security_id, symbol, quantity_open, ...
            FROM lots WHERE portfolio_id = $1 AND is_open = true
        """, portfolio_id)

# macro_hound.py (hypothetically):
async def macro_compute_dar(self, ctx, state, portfolio_id, pack_id):
    # Needs positions but fetches them internally (duplicate query)
    async with get_db_connection_with_rls(ctx.user_id) as conn:
        rows = await conn.fetch("""
            SELECT security_id, symbol, quantity_open, ...
            FROM lots WHERE portfolio_id = $1
        """, portfolio_id)
```

**Problem:** Same query executed multiple times per request

**Recommendation:** Use AgentRuntime request-level cache (already exists!)
```python
# agent_runtime.py:161
def _get_cached_result(self, request_id: str, cache_key: str):
    # Caches capability results per request
```

---

## Recommendations

### Immediate Fixes (P0)

#### Fix 1: Update portfolio_macro_overview.json
```json
{
  "steps": [
    // Remove ledger.positions step (unused)
    {"capability": "macro.detect_regime", "as": "regime"},
    {"capability": "macro.get_indicators", "as": "indicators"},
    {
      "capability": "risk.compute_factor_exposures",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "pack_id": "{{ctx.pricing_pack_id}}"
      },
      "as": "factor_exposures"
      // This capability should fetch positions internally if needed
    },
    {
      "capability": "macro.compute_dar",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "pack_id": "{{ctx.pricing_pack_id}}",
        "confidence": "{{inputs.confidence_level}}"
      },
      "as": "dar"
    },
    {"capability": "financial_analyst.macro_overview_charts", "as": "charts"}
  ],
  "outputs": ["regime", "indicators", "factor_exposures", "dar"]  // FIX OUTPUT FORMAT
}
```

#### Fix 2: Update portfolio_cycle_risk.json
```json
{
  "steps": [
    {"capability": "cycles.compute_short_term", "as": "stdc"},
    {"capability": "cycles.compute_long_term", "as": "ltdc"},
    {
      "capability": "risk.compute_factor_exposures",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "pack_id": "{{ctx.pricing_pack_id}}"
      },
      "as": "factor_exposures"
    },
    {"capability": "risk.overlay_cycle_phases", "args": {...}, "as": "cycle_risk_map"},
    {"capability": "macro.compute_dar", "args": {...}, "as": "dar"}
  ],
  "outputs": ["stdc", "ltdc", "factor_exposures", "cycle_risk_map", "dar"]  // FIX OUTPUT FORMAT
}
```

#### Fix 3: Add Provenance to Stub Data
```python
# financial_analyst.py:1086
async def risk_compute_factor_exposures(self, ctx, state, portfolio_id, pack_id):
    logger.warning("Using fallback factor exposures - FactorAnalysisService not available")

    result = {
        "factors": {...},
        "_provenance": {  // ADD THIS
            "type": "stub",
            "source": "fallback_data",
            "warnings": ["FactorAnalysisService not implemented"],
            "confidence": 0.0
        }
    }
    return result
```

#### Fix 4: Fix Outputs Extraction in Orchestrator
```python
# pattern_orchestrator.py:722
outputs_spec = spec.get("outputs", {})

# Handle different output formats
if isinstance(outputs_spec, dict):
    if "panels" in outputs_spec:
        # Panel-based format - extract all step results
        output_keys = [step.get("as") for step in spec["steps"] if step.get("as")]
    else:
        # Dict format - use keys
        output_keys = list(outputs_spec.keys())
else:
    # List format
    output_keys = outputs_spec
```

---

### Short-Term Improvements (P1)

#### Improvement 1: Standardize Output Format

**Proposal:** All patterns use list format for outputs
```json
{
  "outputs": ["step1", "step2", "step3"]
}
```

**Move presentation to separate section:**
```json
{
  "outputs": ["regime", "factors"],
  "presentation": {
    "panels": [
      {"id": "regime_card", "dataPath": "regime", ...}
    ]
  }
}
```

#### Improvement 2: Add Capability Contracts

Create `backend/app/core/capability_contracts.py`:
```python
CONTRACTS = {
    "ledger.positions": {
        "inputs": {"portfolio_id": "UUID"},
        "outputs": {"positions": "List[Position]", "currency": "str"},
        "fetches_positions": False,
        "requires_pricing": False
    },
    "portfolio.get_valued_positions": {
        "inputs": {"portfolio_id": "UUID", "pack_id": "str"},
        "outputs": {"positions": "List[ValuedPosition]", "total_value": "Decimal"},
        "fetches_positions": True,
        "requires_pricing": True
    },
    "risk.compute_factor_exposures": {
        "inputs": {"portfolio_id": "UUID", "pack_id": "str"},
        "outputs": {"factors": "Dict[str, float]"},
        "fetches_positions": True,  # Documents internal behavior
        "requires_pricing": True
    }
}
```

#### Improvement 3: Add Pattern Linter

Create `backend/scripts/lint_patterns.py`:
```python
def lint_pattern(pattern_file):
    """Validate pattern structure and dependencies."""
    spec = json.load(pattern_file)
    errors = []

    # Check 1: All step references exist
    step_names = {step.get("as") for step in spec["steps"]}
    for step in spec["steps"]:
        args = step.get("args", {})
        for arg_value in args.values():
            if isinstance(arg_value, str) and "{{" in arg_value:
                ref = extract_ref(arg_value)
                if ref not in ["inputs", "ctx"] and ref not in step_names:
                    errors.append(f"Step references undefined '{ref}'")

    # Check 2: Outputs match step names
    outputs = spec.get("outputs", [])
    if isinstance(outputs, list):
        for output in outputs:
            if output not in step_names:
                errors.append(f"Output '{output}' not produced by any step")

    # Check 3: Capability exists
    for step in spec["steps"]:
        capability = step["capability"]
        if capability not in CAPABILITY_REGISTRY:
            errors.append(f"Unknown capability: {capability}")

    return errors
```

---

### Long-Term Architecture (P2)

#### Architecture 1: Capability Self-Documentation

```python
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class CapabilityMetadata:
    """Metadata for capability registration."""
    name: str
    inputs: Dict[str, type]
    outputs: Dict[str, type]
    fetches_positions: bool = False
    requires_pricing: bool = False
    implementation_status: str = "complete"  # complete, stub, partial

def capability(metadata: CapabilityMetadata):
    """Decorator for capability methods."""
    def decorator(func):
        func._capability_metadata = metadata
        return func
    return decorator

# Usage:
class FinancialAnalyst(BaseAgent):
    @capability(CapabilityMetadata(
        name="risk.compute_factor_exposures",
        inputs={"portfolio_id": UUID, "pack_id": str},
        outputs={"factors": Dict[str, float]},
        fetches_positions=True,
        requires_pricing=True,
        implementation_status="stub"  # DOCUMENTS CURRENT STATE
    ))
    async def risk_compute_factor_exposures(self, ctx, state, portfolio_id, pack_id):
        logger.warning("Using stub data - not implemented")
        return {...}
```

#### Architecture 2: Pattern Dependency Graph

```python
class PatternDependencyAnalyzer:
    """Analyze pattern dependencies and optimize execution."""

    def build_dag(self, pattern_spec):
        """Build dependency graph from pattern steps."""
        dag = nx.DiGraph()

        for idx, step in enumerate(pattern_spec["steps"]):
            step_name = step.get("as", f"step_{idx}")
            dag.add_node(step_name, **step)

            # Find dependencies
            args = step.get("args", {})
            for arg_value in args.values():
                if isinstance(arg_value, str) and "{{" in arg_value:
                    dep = extract_ref(arg_value)
                    if dep not in ["inputs", "ctx"]:
                        dag.add_edge(dep, step_name)

        return dag

    def find_parallel_groups(self, dag):
        """Find steps that can execute in parallel."""
        levels = list(nx.topological_generations(dag))
        return levels

    def optimize_execution(self, pattern_spec):
        """Suggest optimizations for pattern execution."""
        dag = self.build_dag(pattern_spec)
        parallel_groups = self.find_parallel_groups(dag)

        return {
            "parallel_groups": parallel_groups,
            "max_parallelism": max(len(g) for g in parallel_groups),
            "critical_path": nx.dag_longest_path(dag)
        }
```

#### Architecture 3: Capability Composition

```python
class CompositeCapability:
    """Compose multiple capabilities into one."""

    def __init__(self, name: str, steps: List[Dict]):
        self.name = name
        self.steps = steps

    async def execute(self, runtime, ctx, state, **kwargs):
        """Execute all sub-steps and return combined result."""
        for step in self.steps:
            result = await runtime.execute_capability(
                step["capability"],
                ctx,
                state,
                **step.get("args", {})
            )
            state[step["as"]] = result

        # Return final step result
        return state[self.steps[-1]["as"]]

# Define composite capabilities
COMPOSITES = {
    "portfolio.valued_analysis": CompositeCapability(
        name="portfolio.valued_analysis",
        steps=[
            {"capability": "ledger.positions", "as": "positions"},
            {"capability": "pricing.apply_pack", "args": {"positions": "{{positions}}"}, "as": "valued"},
            {"capability": "metrics.compute_twr", "args": {"positions": "{{valued}}"}, "as": "metrics"}
        ]
    )
}
```

---

## Summary

### Why Patterns Were Missed

1. **portfolio_macro_overview.json** - Uses `ledger.positions` alone, Week 4 searched for `ledger.positions` + `pricing.apply_pack` pairs
2. **portfolio_cycle_risk.json** - Never uses `ledger.positions` at all, relies on capabilities to fetch internally
3. **corporate_actions_upcoming.json** - Correctly uses `ledger.positions` (doesn't need pricing)

### Systemic Issues

1. **No clear capability contracts** - Unclear when to use `ledger.positions` vs `portfolio.get_valued_positions`
2. **Inconsistent output formats** - 3 different formats confusing orchestrator
3. **Silent stub data** - Multiple capabilities return fake data with no warnings
4. **Hidden dependencies** - Some capabilities fetch positions internally, others don't
5. **No validation** - Patterns can reference undefined steps, no schema validation

### Estimated Fix Time

**P0 Fixes:**
- Fix 2 pattern outputs: 2 hours
- Add stub data provenance: 2 hours
- Fix orchestrator output extraction: 2 hours
- **Total: 6 hours**

**P1 Improvements:**
- Standardize output format (13 patterns): 4 hours
- Add capability contracts: 4 hours
- Add pattern linter: 4 hours
- **Total: 12 hours**

**P2 Architecture:**
- Self-documenting capabilities: 8 hours
- Dependency analyzer: 6 hours
- Composite capabilities: 6 hours
- **Total: 20 hours**

**Grand Total: 38 hours** to fully resolve all integration issues.
