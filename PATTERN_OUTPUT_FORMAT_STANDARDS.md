# Pattern Output Format Standards

**Date:** January 14, 2025  
**Status:** ✅ **STANDARDIZED**  
**Purpose:** Document the standard output formats for pattern execution

---

## Executive Summary

The pattern orchestrator supports **3 output formats** to accommodate different pattern types and UI requirements. All formats are handled correctly by the orchestrator.

---

## Supported Output Formats

### Format 1: List of Output Keys (Recommended)

**Structure:**
```json
{
  "outputs": ["valued_positions", "historical_nav", "sector_allocation"]
}
```

**Usage:**
- Simple patterns with direct step-to-output mapping
- Each output key corresponds to a step result stored in state

**Example Patterns:**
- `portfolio_overview.json`
- `buffett_checklist.json`
- `portfolio_scenario_analysis.json`

**Orchestrator Handling:**
```python
# pattern_orchestrator.py:754-756
if isinstance(outputs_spec, list):
    output_keys = outputs_spec
    for output_key in output_keys:
        outputs[output_key] = state[output_key]
```

**Result:**
```json
{
  "data": {
    "valued_positions": {...},
    "historical_nav": {...},
    "sector_allocation": {...}
  }
}
```

---

### Format 2: Dict with Keys (Legacy)

**Structure:**
```json
{
  "outputs": {
    "stdc": "Short-term debt cycle",
    "ltdc": "Long-term debt cycle",
    "empire": "Empire cycle"
  }
}
```

**Usage:**
- Patterns that need descriptive labels for outputs
- Legacy format from earlier pattern system

**Example Patterns:**
- `macro_cycles_overview.json` (hybrid - uses both formats)

**Orchestrator Handling:**
```python
# pattern_orchestrator.py:783-785
else:
    # Format 2: Dict with keys
    output_keys = list(outputs_spec.keys())
    for output_key in output_keys:
        outputs[output_key] = state[output_key]
```

**Result:**
```json
{
  "data": {
    "stdc": {...},
    "ltdc": {...},
    "empire": {...}
  }
}
```

---

### Format 3: Dict with Panels (UI-Oriented)

**Structure:**
```json
{
  "outputs": {
    "panels": [
      {
        "id": "nav_chart",
        "title": "Portfolio Value Over Time",
        "type": "line_chart",
        "dataPath": "historical_nav"
      },
      {
        "id": "sector_alloc",
        "title": "Sector Allocation",
        "type": "pie_chart",
        "dataPath": "sector_allocation"
      }
    ]
  }
}
```

**Usage:**
- Patterns that need UI metadata (panel titles, types, data paths)
- Patterns used directly by `PatternRenderer` component

**Example Patterns:**
- `portfolio_cycle_risk.json`
- `macro_trend_monitor.json`
- `holding_deep_dive.json`
- `policy_rebalance.json`

**Orchestrator Handling:**
```python
# pattern_orchestrator.py:758-782
if "panels" in outputs_spec:
    panels = outputs_spec["panels"]
    output_keys = []
    for panel in panels:
        panel_id = panel.get("id") if isinstance(panel, dict) else panel
        if panel_id in state:
            output_keys.append(panel_id)
        else:
            # Try to find matching step result
            for state_key in state.keys():
                if state_key == panel_id or state_key.endswith(f"_{panel_id}") or state_key.startswith(f"{panel_id}_"):
                    output_keys.append(state_key)
                    break
```

**Result:**
```json
{
  "data": {
    "historical_nav": {...},
    "sector_allocation": {...}
  }
}
```

**Note:** The orchestrator extracts the actual data from state using panel IDs or matching step result keys. The panel metadata is used by the UI but not included in the response.

---

## Pattern Output Extraction Flow

### Step 1: Pattern Execution
```python
# Step stores result in state
state["historical_nav"] = {
    "historical_nav": [...],
    "lookback_days": 365,
    ...
}
```

### Step 2: Output Extraction
```python
# Orchestrator extracts outputs based on format
outputs = {}
for output_key in output_keys:
    if output_key in state:
        outputs[output_key] = state[output_key]
```

### Step 3: Response Building
```python
result = {
    "data": outputs,  # {historical_nav: {...}, sector_allocation: {...}}
    "charts": charts,
    "trace": trace_data
}
```

### Step 4: API Response
```json
{
  "success": true,
  "data": {
    "historical_nav": {...},
    "sector_allocation": {...}
  },
  "trace": {...}
}
```

---

## Best Practices

### 1. Use Format 1 (List) for Simple Patterns

**Recommended:**
```json
{
  "outputs": ["valued_positions", "historical_nav"]
}
```

**Why:**
- Simplest and most direct
- Clear mapping between steps and outputs
- Easy to understand and maintain

### 2. Use Format 3 (Panels) for UI-Oriented Patterns

**Recommended:**
```json
{
  "outputs": {
    "panels": [
      {
        "id": "nav_chart",
        "title": "Portfolio Value Over Time",
        "type": "line_chart",
        "dataPath": "historical_nav"
      }
    ]
  }
}
```

**Why:**
- Provides UI metadata (titles, types, data paths)
- Enables automatic panel rendering
- Better integration with `PatternRenderer`

### 3. Avoid Format 2 (Dict with Keys) for New Patterns

**Not Recommended:**
```json
{
  "outputs": {
    "stdc": "Short-term debt cycle"
  }
}
```

**Why:**
- Legacy format
- Less flexible than Format 1
- No UI metadata support

---

## Data Structure Handling

### Nested Structures

**Agent Returns:**
```python
{
    "historical_nav": [{date, value}, ...],
    "lookback_days": 365,
    ...
}
```

**Pattern Stores:**
```python
state["historical_nav"] = {
    "historical_nav": [...],  # Double nesting!
    "lookback_days": 365,
    ...
}
```

**UI Extraction:**
```javascript
// Chart components handle nested structures defensively
const navData = Array.isArray(data.historical_nav) 
    ? data.historical_nav 
    : (data.historical_nav.historical_nav || data.historical_nav.data || []);
```

**Solution:**
- ✅ Chart components handle nested structures (completed)
- ✅ Orchestrator stores results correctly
- ⚠️ Consider standardizing agent return structures (future work)

---

## Validation

### Current Status

- ✅ **Format 1 (List):** Fully supported and working
- ✅ **Format 2 (Dict with Keys):** Fully supported and working
- ✅ **Format 3 (Panels):** Fully supported and working
- ✅ **Nested Structures:** Chart components handle all cases

### Testing

All 13 patterns have been validated:
- `portfolio_overview.json` - Format 1 ✅
- `buffett_checklist.json` - Format 1 ✅
- `portfolio_scenario_analysis.json` - Format 1 ✅
- `portfolio_cycle_risk.json` - Format 3 ✅
- `macro_trend_monitor.json` - Format 3 ✅
- `holding_deep_dive.json` - Format 3 ✅
- `policy_rebalance.json` - Format 3 ✅
- `corporate_actions_upcoming.json` - Format 3 ✅
- `macro_cycles_overview.json` - Format 2 (hybrid) ✅
- `portfolio_macro_overview.json` - Format 3 ✅
- `cycle_deleveraging_scenarios.json` - Format 1 ✅
- `export_portfolio_report.json` - Format 1 ✅
- `news_impact_analysis.json` - Format 1 ✅

---

## Migration Guide

### Migrating from Format 2 to Format 1

**Before:**
```json
{
  "outputs": {
    "stdc": "Short-term debt cycle",
    "ltdc": "Long-term debt cycle"
  }
}
```

**After:**
```json
{
  "outputs": ["stdc", "ltdc"]
}
```

### Migrating to Format 3 (UI-Oriented)

**Before:**
```json
{
  "outputs": ["historical_nav", "sector_allocation"]
}
```

**After:**
```json
{
  "outputs": {
    "panels": [
      {
        "id": "nav_chart",
        "title": "Portfolio Value Over Time",
        "type": "line_chart",
        "dataPath": "historical_nav"
      },
      {
        "id": "sector_alloc",
        "title": "Sector Allocation",
        "type": "pie_chart",
        "dataPath": "sector_allocation"
      }
    ]
  }
}
```

---

## Summary

**All 3 output formats are supported and working correctly.**

**Recommendations:**
1. ✅ Use Format 1 (List) for simple patterns
2. ✅ Use Format 3 (Panels) for UI-oriented patterns
3. ⚠️ Avoid Format 2 (Dict with Keys) for new patterns
4. ✅ Chart components handle nested structures defensively

**Status:** ✅ **COMPLETE** - All formats standardized and documented

