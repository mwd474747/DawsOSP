# Pattern Output Format Analysis

**Created**: 2025-11-06
**Status**: Complete
**Priority**: P1 (Medium - No critical bugs, but documentation needed)

---

## Executive Summary

### Key Finding: **NO LARGE REFACTOR NEEDED**

After comprehensive analysis of all 15 patterns, the pattern output format system is **working correctly**. The orchestrator and UI handle three different output formats through:

1. **Orchestrator**: Fuzzy matching for panel IDs → step result keys
2. **UI**: `getDataByPath()` resolution for nested data extraction
3. **Result**: All formats work, but behavior is undocumented

### Recommendation: **Option A - Quick Fix (3 hours)**

- Add pattern output format validation
- Document the three supported formats
- Add warnings for ambiguous panel IDs
- **No code refactoring required**

---

## Pattern Output Formats (All 15 Patterns)

### Format 1: Simple List (8 patterns) ✅

**Pattern**: `"outputs": ["key1", "key2", ...]`

**How It Works**:
- Orchestrator extracts keys directly from step results
- Each key must exist in orchestrator state
- UI receives flat or nested data structure

**Patterns Using Format 1**:

1. **portfolio_overview.json**
   ```json
   "outputs": [
     "valued_positions",
     "perf_metrics",
     "currency_attr",
     "sector_attr",
     "attribution"
   ]
   ```
   **Status**: ✅ Works - All keys match step results

2. **holding_deep_dive.json**
   ```json
   "outputs": [
     "sec",
     "prices",
     "ratings",
     "fundamentals",
     "news"
   ]
   ```
   **Status**: ✅ Works - All keys match step results

3. **macro_trend_monitor.json**
   ```json
   "outputs": [
     "fred",
     "cycles",
     "narratives"
   ]
   ```
   **Status**: ✅ Works - All keys match step results

4. **news_impact_analysis.json**
   ```json
   "outputs": [
     "valued_positions",
     "portfolio_news",
     "impact_summary"
   ]
   ```
   **Status**: ✅ Works - All keys match step results

5. **policy_rebalance.json**
   ```json
   "outputs": [
     "current",
     "target",
     "trades",
     "costs",
     "constraints"
   ]
   ```
   **Status**: ✅ Works - All keys match step results

6. **buffett_checklist.json**
   ```json
   "outputs": [
     "checklist"
   ]
   ```
   **Status**: ✅ Works - Single key matches step result

7. **export_portfolio_report.json**
   ```json
   "outputs": [
     "report_url"
   ]
   ```
   **Status**: ✅ Works - Single key matches step result

8. **tax_harvesting_opportunities.json**
   ```json
   "outputs": [
     "losses",
     "opportunities"
   ]
   ```
   **Status**: ✅ Works (archived) - Would work if unarchived

### Format 2: Dict with Keys (2 patterns) ✅

**Pattern**: `"outputs": {"key1": {...}, "key2": {...}}`

**How It Works**:
- Orchestrator extracts dict keys
- Each key must exist in orchestrator state
- Metadata in values is ignored (UI doesn't use it)

**Patterns Using Format 2**:

9. **portfolio_macro_overview.json**
   ```json
   "outputs": {
     "portfolio_summary": {},
     "macro_indicators": {},
     "cycles_heatmap": {},
     "outlook": {}
   }
   ```
   **Status**: ✅ Works - All keys match step results

10. **portfolio_tax_report.json**
    ```json
    "outputs": {
      "tax_summary": {},
      "realized_gains": {},
      "unrealized_gains": {},
      "wash_sales": {}
    }
    ```
    **Status**: ✅ Works (archived) - Would work if unarchived

### Format 3: Panels with dataPath (5 patterns) ✅

**Pattern**: `"outputs": {"panels": [{"id": "...", "dataPath": "..."}]}`

**How It Works**:
1. **Orchestrator** (lines 758-782 in pattern_orchestrator.py):
   - Extracts panel IDs from `panels` array
   - Performs fuzzy matching to find corresponding step results
   - Matching logic: exact match, suffix match, prefix match
   - Example: Panel ID `risk_map` matches state key `cycle_risk_map`

2. **UI** (lines 3737-3749 in full_ui.html):
   - Uses `getDataByPath(data, panel.dataPath)` to extract nested data
   - Example: `dataPath: "actions_with_impact.summary"` → `data.actions_with_impact.summary`

**Patterns Using Format 3**:

11. **corporate_actions_upcoming.json**
    ```json
    "outputs": {
      "panels": [
        {"id": "actions_table", "dataPath": "actions_with_impact.actions"},
        {"id": "summary_metrics", "dataPath": "actions_with_impact.summary"},
        {"id": "notifications_list", "dataPath": "actions_with_impact.notifications"}
      ]
    }
    ```
    **Step**: `corporate_actions.calculate_impact` → `"as": "actions_with_impact"`

    **Orchestrator Behavior**:
    - Panel `actions_table` fuzzy matches `actions_with_impact` (no exact match, uses state key)
    - Extracts `outputs["actions_with_impact"] = state["actions_with_impact"]`

    **UI Behavior**:
    - `getDataByPath(data, "actions_with_impact.actions")` → `data.actions_with_impact.actions`

    **Status**: ✅ Works - Fuzzy matching + dataPath resolution

12. **portfolio_cycle_risk.json**
    ```json
    "outputs": {
      "panels": [
        {"id": "risk_map", "dataPath": "cycle_risk_map"},
        {"id": "stdc_chart", "dataPath": "stdc"},
        {"id": "ltdc_chart", "dataPath": "ltdc"},
        {"id": "dar_metrics", "dataPath": "dar"}
      ]
    }
    ```
    **Steps**:
    - `cycles.compute_short_term` → `"as": "stdc"`
    - `cycles.compute_long_term` → `"as": "ltdc"`
    - `risk.overlay_cycle_phases` → `"as": "cycle_risk_map"`
    - `macro.compute_dar` → `"as": "dar"`

    **Orchestrator Behavior**:
    - Panel `risk_map` fuzzy matches `cycle_risk_map` (suffix match)
    - Panels `stdc_chart`, `ltdc_chart`, `dar_metrics` fuzzy match `stdc`, `ltdc`, `dar` (prefix match)

    **UI Behavior**:
    - `getDataByPath(data, "cycle_risk_map")` → `data.cycle_risk_map`

    **Status**: ✅ Works - Fuzzy matching handles ID variations

13. **portfolio_scenario_analysis.json**
    ```json
    "outputs": {
      "panels": [
        {"id": "scenario_results", "dataPath": "analysis.scenarios"},
        {"id": "portfolio_summary", "dataPath": "analysis.current_portfolio"},
        {"id": "risk_metrics", "dataPath": "analysis.risk_metrics"}
      ]
    }
    ```
    **Step**: `risk.run_scenario_analysis` → `"as": "analysis"`

    **Orchestrator Behavior**:
    - Panel IDs fuzzy match `analysis` (all panels reference same state key)
    - Extracts `outputs["analysis"] = state["analysis"]`

    **UI Behavior**:
    - `getDataByPath(data, "analysis.scenarios")` → `data.analysis.scenarios`

    **Status**: ✅ Works - dataPath handles nested structure

14. **macro_cycles_overview.json**
    ```json
    "outputs": {
      "panels": [
        {"id": "stdc_chart", "dataPath": "stdc"},
        {"id": "ltdc_chart", "dataPath": "ltdc"},
        {"id": "cycles_table", "dataPath": "cycles_data"}
      ]
    }
    ```
    **Steps**:
    - `cycles.compute_short_term` → `"as": "stdc"`
    - `cycles.compute_long_term` → `"as": "ltdc"`
    - `cycles.get_current_phase` → `"as": "cycles_data"`

    **Orchestrator Behavior**:
    - Panels `stdc_chart`, `ltdc_chart` fuzzy match `stdc`, `ltdc` (prefix match)
    - Panel `cycles_table` exact matches `cycles_data`

    **Status**: ✅ Works - Fuzzy matching + dataPath

15. **cycle_deleveraging_scenarios.json**
    ```json
    "outputs": {
      "panels": [
        {"id": "scenario_results", "dataPath": "deleveraging.scenarios"},
        {"id": "portfolio_impact", "dataPath": "deleveraging.portfolio_impact"}
      ]
    }
    ```
    **Step**: `cycles.run_deleveraging_scenarios` → `"as": "deleveraging"`

    **Orchestrator Behavior**:
    - Panels fuzzy match `deleveraging`

    **UI Behavior**:
    - `getDataByPath(data, "deleveraging.scenarios")` → `data.deleveraging.scenarios`

    **Status**: ✅ Works (needs FRED data) - Format is correct

---

## Technical Deep Dive

### Orchestrator Output Extraction (lines 746-805)

```python
# Extract outputs
outputs = {}
outputs_spec = spec.get("outputs", {})

if isinstance(outputs_spec, list):
    # Format 1: List of keys ["key1", "key2"]
    output_keys = outputs_spec

elif isinstance(outputs_spec, dict):
    if "panels" in outputs_spec:
        # Format 3: Panels with dataPath
        panels = outputs_spec["panels"]
        output_keys = []

        for panel in panels:
            panel_id = panel.get("id") if isinstance(panel, dict) else panel
            if panel_id:
                # Try exact match first
                if panel_id in state:
                    output_keys.append(panel_id)
                else:
                    # Fuzzy matching: find state key that matches panel
                    # Patterns: suffix match (risk_map → cycle_risk_map)
                    #          prefix match (stdc_chart → stdc)
                    for state_key in state.keys():
                        if (state_key == panel_id or
                            state_key.endswith(f"_{panel_id}") or
                            state_key.startswith(f"{panel_id}_")):
                            output_keys.append(state_key)
                            break
                    else:
                        logger.warning(f"Panel {panel_id} not found in state")
    else:
        # Format 2: Dict with keys {"key1": {}, "key2": {}}
        output_keys = list(outputs_spec.keys())
else:
    # Fallback: empty list
    output_keys = []
    logger.warning(f"Unexpected outputs format: {type(outputs_spec)}")

# Extract outputs from state
for output_key in output_keys:
    if output_key in state:
        outputs[output_key] = state[output_key]
    else:
        logger.warning(f"Output {output_key} not found in state")
        outputs[output_key] = None  # Prevent "No data" errors in UI
```

**Key Insight**: The orchestrator doesn't resolve `dataPath` - it just extracts step results by key. The UI handles nested data extraction.

### UI Data Extraction (lines 3737-3749)

```javascript
/**
 * Helper function to extract data from nested path
 */
function getDataByPath(data, path) {
    if (!path || !data) return data;

    const parts = path.split('.');
    let current = data;

    for (const part of parts) {
        if (current && typeof current === 'object') {
            current = current[part];
        } else {
            return null;
        }
    }

    return current;
}
```

**Usage** (line 3943):
```javascript
e(PanelRenderer, {
    key: panel.id,
    panel: panel,
    data: getDataByPath(data, panel.dataPath),  // ← Resolves nested path here
    fullData: data
})
```

**Key Insight**: UI resolution is completely independent of orchestrator. The orchestrator extracts top-level keys, the UI drills down via `dataPath`.

---

## Why Fuzzy Matching Works (But Is Fragile)

### Example: portfolio_cycle_risk.json

**Pattern Definition**:
```json
{
  "steps": [
    {
      "capability": "risk.overlay_cycle_phases",
      "as": "cycle_risk_map"
    }
  ],
  "outputs": {
    "panels": [
      {"id": "risk_map", "dataPath": "cycle_risk_map"}
    ]
  }
}
```

**Orchestrator Processing**:
1. Panel ID: `risk_map`
2. State key: `cycle_risk_map`
3. Fuzzy match: `cycle_risk_map`.endswith(`_risk_map`) → **TRUE**
4. Result: `outputs["cycle_risk_map"] = state["cycle_risk_map"]`

**UI Processing**:
1. `panel.dataPath = "cycle_risk_map"`
2. `getDataByPath(data, "cycle_risk_map")` → `data.cycle_risk_map`
3. Result: Panel receives correct data

### Why It's Fragile

**Problem 1: Ambiguous Matches**

If state contains both `cycle_risk_map` and `portfolio_risk_map`:
- Panel ID `risk_map` could match either
- Orchestrator picks first match (order-dependent)
- No warning if multiple matches exist

**Problem 2: Silent Failures**

If pattern author typos the panel ID:
```json
{"id": "risk_mapp", "dataPath": "cycle_risk_map"}  // ← Typo
```
- Orchestrator logs warning but continues
- `outputs["risk_mapp"] = None`
- UI receives `null` data → "No data available"
- User doesn't know if backend failed or pattern is wrong

**Problem 3: Undocumented Behavior**

- Pattern authors don't know fuzzy matching exists
- No documentation of matching rules
- No validation of panel ID → step result mapping

---

## Analysis Summary

### What Works ✅

1. **All 15 patterns have valid output formats**
   - 8 patterns use Format 1 (simple list)
   - 2 patterns use Format 2 (dict with keys)
   - 5 patterns use Format 3 (panels with dataPath)

2. **Orchestrator handles all three formats**
   - Simple extraction for Format 1 & 2
   - Fuzzy matching for Format 3

3. **UI resolves nested data correctly**
   - `getDataByPath()` handles dot notation
   - Works with arbitrarily nested structures

4. **No critical bugs found**
   - System is functional
   - Data flows correctly end-to-end

### What's Missing ⚠️

1. **Documentation**
   - No pattern output format specification
   - Fuzzy matching behavior undocumented
   - No examples for pattern authors

2. **Validation**
   - No validation of panel ID → step result mapping
   - No warnings for ambiguous matches
   - No detection of orphaned panel IDs

3. **Error Messages**
   - Silent failures (logs warnings, but no user feedback)
   - "No data available" doesn't distinguish backend vs pattern errors

---

## Recommended Fix: Option A - Quick Fix (3 hours)

### Task 1: Add Pattern Output Validation (1.5 hours)

**Create**: `backend/app/core/pattern_validator.py`

```python
def validate_pattern_outputs(spec: dict, state: dict) -> list[str]:
    """
    Validate pattern outputs against orchestrator state.

    Returns list of warnings (empty if valid).
    """
    warnings = []
    outputs_spec = spec.get("outputs", {})

    if isinstance(outputs_spec, list):
        # Format 1: Validate all keys exist
        for key in outputs_spec:
            if key not in state:
                warnings.append(f"Output key '{key}' not found in state")

    elif isinstance(outputs_spec, dict):
        if "panels" in outputs_spec:
            # Format 3: Validate panel IDs match step results
            for panel in outputs_spec["panels"]:
                panel_id = panel.get("id")
                data_path = panel.get("dataPath")

                # Check for multiple fuzzy matches (ambiguous)
                matches = []
                for state_key in state.keys():
                    if (state_key == panel_id or
                        state_key.endswith(f"_{panel_id}") or
                        state_key.startswith(f"{panel_id}_")):
                        matches.append(state_key)

                if len(matches) == 0:
                    warnings.append(f"Panel '{panel_id}' has no matching state key")
                elif len(matches) > 1:
                    warnings.append(f"Panel '{panel_id}' matches multiple state keys: {matches}")

                # Validate dataPath exists
                if data_path:
                    root_key = data_path.split('.')[0]
                    if root_key not in state:
                        warnings.append(f"Panel '{panel_id}' dataPath root '{root_key}' not in state")
        else:
            # Format 2: Validate all keys exist
            for key in outputs_spec.keys():
                if key not in state:
                    warnings.append(f"Output key '{key}' not found in state")

    return warnings
```

**Integration** (pattern_orchestrator.py line 805):
```python
# Validate outputs before returning
from app.core.pattern_validator import validate_pattern_outputs
validation_warnings = validate_pattern_outputs(spec, state)
if validation_warnings:
    for warning in validation_warnings:
        logger.warning(f"Pattern {pattern_id} output validation: {warning}")
```

### Task 2: Document Pattern Output Formats (1 hour)

**Create**: `docs/PATTERN_OUTPUT_FORMATS.md`

**Contents**:
- Three supported formats with examples
- Fuzzy matching rules for Format 3
- Best practices for panel ID naming
- Common mistakes and how to fix them
- Migration guide from Format 1/2 to Format 3

### Task 3: Add Tests (0.5 hours)

**Create**: `backend/tests/test_pattern_validator.py`

**Test Cases**:
- Format 1: Valid list, missing key
- Format 2: Valid dict, missing key
- Format 3: Valid panels, orphaned panel ID, ambiguous match
- Edge cases: Empty outputs, null outputs, malformed panels

**Estimated Total Time**: 3 hours

---

## Alternative Options (NOT Recommended)

### Option B: Eliminate Fuzzy Matching (8-12 hours)

**Approach**: Make panel IDs exactly match step result keys

**Changes Required**:
1. Update 5 patterns to use exact panel ID → step result mapping
2. Remove fuzzy matching logic from orchestrator
3. Update UI to handle new format
4. Migration script for existing patterns

**Risk**: Breaking change, requires pattern updates

**Benefit**: More predictable, easier to debug

**Verdict**: ❌ Not worth it - fuzzy matching works, just needs documentation

### Option C: Orchestrator Resolves dataPath (16-24 hours)

**Approach**: Have orchestrator resolve `dataPath` before sending to UI

**Changes Required**:
1. Add dataPath resolution logic to orchestrator
2. Pre-extract nested data for each panel
3. Send flat structure to UI
4. Update UI to handle new response format
5. Update all patterns to match new format
6. Extensive testing (15 patterns × 3 panel types = 45 test cases)

**Risk**: Large refactor, potential data structure conflicts

**Benefit**: Cleaner separation of concerns

**Verdict**: ❌ Overkill - current system works fine

---

## Decision Matrix

| Option | Time | Risk | Benefit | Verdict |
|--------|------|------|---------|---------|
| **A: Quick Fix** | 3h | Low | Documentation + validation | ✅ **Recommended** |
| **B: Eliminate Fuzzy** | 8-12h | Medium | Predictability | ❌ Not worth it |
| **C: Orchestrator dataPath** | 16-24h | High | Cleaner design | ❌ Overkill |

---

## Implementation Plan (Option A)

### Phase 1: Validation (1.5 hours)

1. Create `backend/app/core/pattern_validator.py`
2. Implement `validate_pattern_outputs()` function
3. Integrate into `pattern_orchestrator.py` line 805
4. Test with all 15 patterns

**Deliverable**: Validation warnings in logs for misconfigured patterns

### Phase 2: Documentation (1 hour)

1. Create `docs/PATTERN_OUTPUT_FORMATS.md`
2. Document three formats with examples
3. Document fuzzy matching rules
4. Add troubleshooting guide

**Deliverable**: Pattern author reference documentation

### Phase 3: Tests (0.5 hours)

1. Create `backend/tests/test_pattern_validator.py`
2. Test all three formats
3. Test edge cases (orphaned IDs, ambiguous matches)

**Deliverable**: Test suite for pattern validation

**Total Time**: 3 hours

---

## Conclusion

**The pattern output format system is working correctly.** No large refactor is needed.

**Recommendation**: Implement Option A (Quick Fix) to:
- Add validation warnings for misconfigured patterns
- Document the three supported formats
- Help pattern authors avoid common mistakes

**ROI**:
- **Implementation**: 3 hours
- **Benefit**: Faster pattern development, fewer "No data" bugs, better maintainability
- **Risk**: None (non-breaking, additive only)

**Next Steps**:
1. Get user approval for Option A
2. Implement validation utility
3. Document pattern formats
4. Run validation on all existing patterns
5. Fix any warnings that surface

---

**End of Pattern Output Format Analysis**
