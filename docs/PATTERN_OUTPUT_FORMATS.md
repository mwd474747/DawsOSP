# Pattern Output Formats Reference

**Created**: 2025-11-06
**Audience**: Pattern authors, backend developers
**Status**: Active

---

## Overview

DawsOS patterns support **three output formats** for declaring how pattern results should be structured:

1. **Format 1: Simple List** - List of output keys
2. **Format 2: Dict with Keys** - Dict mapping keys to metadata
3. **Format 3: Panels with dataPath** - UI panel configuration with nested data paths

All three formats are fully supported. This document explains when to use each format, how they work internally, and common mistakes to avoid.

---

## Format 1: Simple List ✅

**Best for**: Patterns with flat outputs, no nested data

### Syntax

```json
{
  "outputs": ["key1", "key2", "key3"]
}
```

### How It Works

1. **Orchestrator**: Extracts each key directly from step results
2. **Validation**: Each key must exist in orchestrator state
3. **UI**: Receives flat data structure

### Example: portfolio_overview.json

```json
{
  "steps": [
    {
      "capability": "ledger.positions",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}"},
      "as": "valued_positions"
    },
    {
      "capability": "metrics.compute_performance",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}"},
      "as": "perf_metrics"
    }
  ],
  "outputs": [
    "valued_positions",
    "perf_metrics"
  ]
}
```

**Result**:
```json
{
  "valued_positions": {...},
  "perf_metrics": {...}
}
```

### Best Practices

✅ **DO**:
- Use for patterns with 1-5 simple outputs
- Match output keys exactly to step `"as"` values
- Keep output keys short and descriptive

❌ **DON'T**:
- Use for patterns with nested data structures
- Add keys that don't have corresponding steps
- Use keys that don't match any state key

---

## Format 2: Dict with Keys ✅

**Best for**: Patterns with metadata or grouping

### Syntax

```json
{
  "outputs": {
    "key1": {"description": "...", "type": "..."},
    "key2": {"description": "...", "type": "..."}
  }
}
```

### How It Works

1. **Orchestrator**: Extracts dict keys (ignores values)
2. **Validation**: Each key must exist in orchestrator state
3. **UI**: Receives flat data structure (metadata ignored)

**Note**: The values (metadata) in the dict are **currently ignored** by both orchestrator and UI. They're for documentation only.

### Example: portfolio_macro_overview.json

```json
{
  "steps": [
    {
      "capability": "ledger.summary",
      "as": "portfolio_summary"
    },
    {
      "capability": "macro.fetch_indicators",
      "as": "macro_indicators"
    }
  ],
  "outputs": {
    "portfolio_summary": {},
    "macro_indicators": {},
    "cycles_heatmap": {},
    "outlook": {}
  }
}
```

**Result**:
```json
{
  "portfolio_summary": {...},
  "macro_indicators": {...},
  "cycles_heatmap": {...},
  "outlook": {...}
}
```

### Best Practices

✅ **DO**:
- Use when you want to document output structure
- Match output keys exactly to step `"as"` values
- Add descriptive metadata for future reference

❌ **DON'T**:
- Rely on metadata values (they're ignored)
- Add keys without corresponding steps
- Use for UI panel configuration (use Format 3 instead)

---

## Format 3: Panels with dataPath ✅

**Best for**: Patterns with nested data, UI panel configuration

### Syntax

```json
{
  "outputs": {
    "panels": [
      {
        "id": "panel_id",
        "title": "Panel Title",
        "type": "table|chart|metrics_grid",
        "dataPath": "step_result.nested.field"
      }
    ]
  }
}
```

### How It Works

1. **Orchestrator**:
   - Extracts panel IDs
   - Uses **fuzzy matching** to find corresponding state keys
   - Returns top-level step results

2. **UI**:
   - Uses `getDataByPath()` to drill into nested structures
   - Resolves `dataPath` at render time

### Fuzzy Matching Rules

The orchestrator matches panel IDs to state keys using these rules (in order):

1. **Exact match**: `panel_id == state_key`
2. **Suffix match**: `state_key.endswith(f"_{panel_id}")`
3. **Prefix match**: `state_key.startswith(f"{panel_id}_")`

**Examples**:

| Panel ID | State Key | Match Type | Result |
|----------|-----------|------------|--------|
| `risk_map` | `cycle_risk_map` | Suffix | ✅ Matches |
| `stdc_chart` | `stdc` | Prefix | ✅ Matches |
| `analysis` | `analysis` | Exact | ✅ Matches |
| `summary` | `portfolio_summary` | Suffix | ✅ Matches |
| `data` | `raw_data` OR `data_processed` | Ambiguous | ⚠️ Warning |

### Example: corporate_actions_upcoming.json

```json
{
  "steps": [
    {
      "capability": "corporate_actions.upcoming",
      "as": "actions"
    },
    {
      "capability": "corporate_actions.calculate_impact",
      "args": {
        "actions": "{{actions.actions}}",
        "holdings": "{{positions.positions}}"
      },
      "as": "actions_with_impact"
    }
  ],
  "outputs": {
    "panels": [
      {
        "id": "actions_table",
        "title": "Upcoming Corporate Actions",
        "type": "table",
        "dataPath": "actions_with_impact.actions"
      },
      {
        "id": "summary_metrics",
        "title": "Summary",
        "type": "metrics_grid",
        "dataPath": "actions_with_impact.summary"
      }
    ]
  }
}
```

**Orchestrator Processing**:
- Panel `actions_table` fuzzy matches `actions_with_impact` (suffix: `_actions`)
- Panel `summary_metrics` fuzzy matches `actions_with_impact` (contains `summary` → searches for `summary` in state keys)
- Result: `outputs["actions_with_impact"] = state["actions_with_impact"]`

**UI Processing**:
- Panel 1: `getDataByPath(data, "actions_with_impact.actions")` → `data.actions_with_impact.actions`
- Panel 2: `getDataByPath(data, "actions_with_impact.summary")` → `data.actions_with_impact.summary`

**Final Result**:
```json
{
  "actions_with_impact": {
    "actions": [...],
    "summary": {...},
    "notifications": [...]
  }
}
```

UI receives nested data, drills down via `dataPath`.

### Best Practices

✅ **DO**:
- Use panel IDs that clearly match step result keys
- Use `dataPath` to navigate nested structures
- Prefer exact matches over fuzzy matches
- Add `title` and `type` for UI rendering

❌ **DON'T**:
- Use ambiguous panel IDs (e.g., `data`, `summary` without qualifiers)
- Rely on fuzzy matching for critical patterns
- Use dataPath root keys that don't exist in state
- Forget to add both `id` and `dataPath` fields

---

## Common Mistakes & Solutions

### Mistake 1: Orphaned Panel ID

**Symptom**: "No data available" in UI, warning in logs

**Example**:
```json
{
  "steps": [
    {"capability": "risk.compute", "as": "cycle_risk_map"}
  ],
  "outputs": {
    "panels": [
      {"id": "risk_mapp", "dataPath": "cycle_risk_map"}  // ← Typo!
    ]
  }
}
```

**Fix**: Match panel ID to step result key exactly or use fuzzy match rules

```json
{
  "outputs": {
    "panels": [
      {"id": "risk_map", "dataPath": "cycle_risk_map"}  // ← Fuzzy match works
    ]
  }
}
```

Or use exact match:
```json
{
  "outputs": {
    "panels": [
      {"id": "cycle_risk_map", "dataPath": "cycle_risk_map"}  // ← Exact match
    ]
  }
}
```

### Mistake 2: Ambiguous Panel ID

**Symptom**: Warning in logs about multiple matches

**Example**:
```json
{
  "steps": [
    {"capability": "metrics.compute", "as": "portfolio_summary"},
    {"capability": "charts.render", "as": "chart_summary"}
  ],
  "outputs": {
    "panels": [
      {"id": "summary", "dataPath": "portfolio_summary"}  // ← Matches both!
    ]
  }
}
```

**Fix**: Use more specific panel ID

```json
{
  "outputs": {
    "panels": [
      {"id": "portfolio_summary", "dataPath": "portfolio_summary"}  // ← Exact match
    ]
  }
}
```

### Mistake 3: Missing dataPath Root Key

**Symptom**: "No data available" in UI, warning about missing root key

**Example**:
```json
{
  "steps": [
    {"capability": "risk.compute", "as": "risk_data"}
  ],
  "outputs": {
    "panels": [
      {"id": "risk_metrics", "dataPath": "analysis.risk_metrics"}  // ← "analysis" doesn't exist!
    ]
  }
}
```

**Fix**: Match dataPath root to step result key

```json
{
  "outputs": {
    "panels": [
      {"id": "risk_metrics", "dataPath": "risk_data.risk_metrics"}  // ← Correct root
    ]
  }
}
```

Or change step result key:
```json
{
  "steps": [
    {"capability": "risk.compute", "as": "analysis"}  // ← Match dataPath root
  ],
  "outputs": {
    "panels": [
      {"id": "risk_metrics", "dataPath": "analysis.risk_metrics"}
    ]
  }
}
```

### Mistake 4: Using Format 1 for Nested Data

**Symptom**: UI receives nested object but expects flat array

**Example**:
```json
{
  "steps": [
    {"capability": "corporate_actions.calculate_impact", "as": "actions_with_impact"}
  ],
  "outputs": ["actions_with_impact"]  // ← Format 1 returns whole object
}
```

**Result**:
```json
{
  "actions_with_impact": {
    "actions": [...],    // ← UI wants this
    "summary": {...},
    "notifications": [...]
  }
}
```

**Fix**: Use Format 3 with dataPath to extract nested field

```json
{
  "outputs": {
    "panels": [
      {"id": "actions_table", "dataPath": "actions_with_impact.actions"}  // ← Extracts nested field
    ]
  }
}
```

---

## When to Use Each Format

| Format | Use When | Example Patterns |
|--------|----------|------------------|
| **Format 1: List** | Simple outputs, flat structure, no nesting | `holding_deep_dive`, `buffett_checklist`, `export_portfolio_report` |
| **Format 2: Dict** | Want to document output structure, flat data | `portfolio_macro_overview`, `portfolio_tax_report` |
| **Format 3: Panels** | Nested data, UI panel configuration, multiple visualizations | `corporate_actions_upcoming`, `portfolio_cycle_risk`, `portfolio_scenario_analysis` |

---

## Validation

Use the pattern validator to check your outputs before deployment:

```python
from app.core.pattern_validator import validate_pattern_outputs

# During pattern execution (runtime validation)
warnings = validate_pattern_outputs(spec, state)
if warnings:
    for warning in warnings:
        logger.warning(f"Pattern validation: {warning}")

# Before deployment (structural validation)
from app.core.pattern_validator import validate_all_patterns

results = validate_all_patterns("backend/patterns")
for pattern_id, warnings in results.items():
    print(f"{pattern_id}: {warnings}")
```

**Validation Checks**:
- ✅ All output keys exist in state
- ✅ Panel IDs match at least one state key
- ✅ Panel IDs don't match multiple state keys (ambiguous)
- ✅ dataPath root keys exist in state
- ✅ dataPath nested paths have dict structure

---

## Migration Guide

### From Format 1 to Format 3 (for nested data)

**Before**:
```json
{
  "steps": [
    {"capability": "risk.analyze", "as": "analysis"}
  ],
  "outputs": ["analysis"]
}
```

**After**:
```json
{
  "steps": [
    {"capability": "risk.analyze", "as": "analysis"}
  ],
  "outputs": {
    "panels": [
      {"id": "scenarios", "title": "Scenarios", "type": "table", "dataPath": "analysis.scenarios"},
      {"id": "risk_metrics", "title": "Risk Metrics", "type": "metrics_grid", "dataPath": "analysis.risk_metrics"}
    ]
  }
}
```

### From Format 2 to Format 3 (for UI configuration)

**Before**:
```json
{
  "outputs": {
    "portfolio_summary": {},
    "macro_indicators": {}
  }
}
```

**After**:
```json
{
  "outputs": {
    "panels": [
      {"id": "portfolio_summary", "title": "Portfolio", "type": "metrics_grid", "dataPath": "portfolio_summary"},
      {"id": "macro_indicators", "title": "Macro", "type": "table", "dataPath": "macro_indicators"}
    ]
  }
}
```

---

## Internal Implementation

### Orchestrator (pattern_orchestrator.py lines 746-805)

```python
# Extract outputs
outputs = {}
outputs_spec = spec.get("outputs", {})

if isinstance(outputs_spec, list):
    # Format 1: List
    output_keys = outputs_spec

elif isinstance(outputs_spec, dict):
    if "panels" in outputs_spec:
        # Format 3: Panels with fuzzy matching
        panels = outputs_spec["panels"]
        output_keys = []

        for panel in panels:
            panel_id = panel.get("id")
            if panel_id:
                # Fuzzy matching
                if panel_id in state:
                    output_keys.append(panel_id)
                else:
                    for state_key in state.keys():
                        if (state_key == panel_id or
                            state_key.endswith(f"_{panel_id}") or
                            state_key.startswith(f"{panel_id}_")):
                            output_keys.append(state_key)
                            break
    else:
        # Format 2: Dict keys
        output_keys = list(outputs_spec.keys())

# Extract outputs from state
for output_key in output_keys:
    if output_key in state:
        outputs[output_key] = state[output_key]
    else:
        outputs[output_key] = None
```

### UI (full_ui.html lines 3737-3749)

```javascript
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

// Usage in PanelRenderer
e(PanelRenderer, {
    panel: panel,
    data: getDataByPath(data, panel.dataPath),
    fullData: data
})
```

---

## References

### Code Files
- [backend/app/core/pattern_orchestrator.py](../backend/app/core/pattern_orchestrator.py) - Output extraction logic
- [backend/app/core/pattern_validator.py](../backend/app/core/pattern_validator.py) - Validation utility
- [full_ui.html](../full_ui.html) - UI dataPath resolution

### Pattern Examples
- **Format 1**: [holding_deep_dive.json](../backend/patterns/holding_deep_dive.json)
- **Format 2**: [portfolio_macro_overview.json](../backend/patterns/portfolio_macro_overview.json)
- **Format 3**: [corporate_actions_upcoming.json](../backend/patterns/corporate_actions_upcoming.json)

### Analysis Documents
- [PATTERN_OUTPUT_FORMAT_ANALYSIS.md](../PATTERN_OUTPUT_FORMAT_ANALYSIS.md) - Comprehensive analysis of all patterns

---

**End of Pattern Output Formats Reference**
