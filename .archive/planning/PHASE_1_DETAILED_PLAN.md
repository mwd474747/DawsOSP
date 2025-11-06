# Phase 1 Detailed Implementation Plan: Emergency User-Facing Fixes

**Date:** January 14, 2025  
**Status:** ✅ **READY FOR EXECUTION**  
**Purpose:** Detailed implementation plan for Phase 1 that addresses root causes and ensures fixes work

---

## Executive Summary

**Goal:** Stop user trust issues immediately, fix broken patterns

**Root Issues:**
1. **Silent Stub Data** - Risk Analytics shows fake data without warnings
2. **Pattern Output Extraction** - Orchestrator fails to extract outputs from 3 different formats
3. **Pattern Format Inconsistency** - 6 patterns use non-standard output formats

**Total Time:** 16 hours (Week 1)

**Success Criteria:**
- ✅ Risk Analytics shows provenance warnings
- ✅ All 6 patterns work correctly
- ✅ No "No data" errors
- ✅ User trust preserved

---

## Task 1.1: Add Provenance Warnings to Stub Data (4 hours)

### Root Issue

**Problem:** `risk.compute_factor_exposures` returns hardcoded fake data without warnings, destroying user trust.

**Current State:**
- ✅ `risk.compute_factor_exposures` already has `_provenance` field (lines 1111-1122)
- ⚠️ Need to verify `macro.compute_dar` has provenance warnings
- ⚠️ Need to verify UI properly displays warnings

**Root Cause:** Stub data lacks explicit provenance metadata, making it appear as real data.

### Implementation Plan

#### Step 1.1.1: Verify Current State (30 minutes)

**Files to Check:**
1. `backend/app/agents/financial_analyst.py` - Line 1111: Check `_provenance` field
2. `backend/app/agents/macro_hound.py` - Line ~738: Check if `macro.compute_dar` has `_provenance`
3. `full_ui.html` - Line 3407: Check if `ProvenanceWarningBanner` works correctly

**Actions:**
1. Verify `risk_compute_factor_exposures` has complete `_provenance` field
2. Check if `macro.compute_dar` returns `_provenance` field
3. Test UI warning banner display

**Expected Findings:**
- `risk_compute_factor_exposures` has `_provenance` field ✅
- `macro.compute_dar` may or may not have `_provenance` field ⚠️
- UI warning banner exists but may not be working correctly ⚠️

---

#### Step 1.1.2: Add Provenance to `macro.compute_dar` (1 hour)

**File:** `backend/app/agents/macro_hound.py`

**Location:** Around line 738 (after DaR computation)

**Current Code:**
```python
dar_result = await scenario_service.compute_dar(
    portfolio_id=str(portfolio_id_uuid),
    regime=regime,
    confidence=confidence,
    horizon_days=horizon_days,
    pack_id=pack_id_str,
    as_of_date=ctx.asof_date,
)
```

**Action:** Check if `dar_result` is stub data. If it is, add `_provenance` field.

**Implementation:**
```python
# After computing DaR
dar_result = await scenario_service.compute_dar(...)

# Check if result is stub data
if isinstance(dar_result, dict):
    # Check if already has provenance
    if "_provenance" not in dar_result:
        # Check if this is stub data (no real implementation)
        # TODO: Determine if DaR is real or stub
        # For now, assume it's real if it comes from scenario_service
        # But add provenance if it's missing and we suspect stub data
        
        # If we detect stub data, add provenance
        if dar_result.get("dar_value") is None or dar_result.get("confidence") == 0.0:
            dar_result["_provenance"] = {
                "type": "stub",
                "warnings": [
                    "DaR computation uses fallback data",
                    "Values may not be accurate for investment decisions"
                ],
                "confidence": 0.0,
                "implementation_status": "stub",
                "recommendation": "Do not use for investment decisions",
                "source": "fallback_stub_data"
            }

return dar_result
```

**Testing:**
1. Call `macro.compute_dar` capability
2. Verify response includes `_provenance` field if stub data
3. Verify UI shows warning banner

**Validation:**
- ✅ `macro.compute_dar` returns `_provenance` field for stub data
- ✅ UI warning banner displays correctly
- ✅ Warning is visible and clear

---

#### Step 1.1.3: Verify UI Warning Banner (1 hour)

**File:** `full_ui.html`

**Location:** Lines 3407-3428 (ProvenanceWarningBanner component)

**Current Code:**
```javascript
// PHASE 1 FIX: Check for provenance warnings in data
const dataResult = result.data || result;
const provenanceWarnings = [];

// Recursively check for _provenance fields in data
function checkProvenance(obj, path = '') {
    if (!obj || typeof obj !== 'object') return;
    
    if (obj._provenance && obj._provenance.type === 'stub') {
        provenanceWarnings.push({
            path: path || 'root',
            warnings: obj._provenance.warnings || [],
            recommendation: obj._provenance.recommendation || 'Do not use for investment decisions'
        });
    }
    
    // Recursively check nested objects
    for (const key in obj) {
        if (key !== '_provenance' && obj.hasOwnProperty(key)) {
            checkProvenance(obj[key], path ? `${path}.${key}` : key);
        }
    }
}

checkProvenance(dataResult);
setProvenanceWarnings(provenanceWarnings);
```

**Actions:**
1. Verify `checkProvenance` function works correctly
2. Test with nested `_provenance` fields
3. Verify warning banner displays correctly
4. Test with Risk Analytics page data

**Implementation:**
```javascript
// Enhanced provenance checking
function checkProvenance(obj, path = '') {
    if (!obj || typeof obj !== 'object') return;
    
    // Check if this object has _provenance
    if (obj._provenance && obj._provenance.type === 'stub') {
        provenanceWarnings.push({
            path: path || 'root',
            warnings: obj._provenance.warnings || [],
            recommendation: obj._provenance.recommendation || 'Do not use for investment decisions',
            confidence: obj._provenance.confidence || 0.0,
            source: obj._provenance.source || 'unknown'
        });
    }
    
    // Recursively check nested objects (but skip _provenance key itself)
    for (const key in obj) {
        if (key !== '_provenance' && obj.hasOwnProperty(key)) {
            const nestedPath = path ? `${path}.${key}` : key;
            checkProvenance(obj[key], nestedPath);
        }
    }
}

// Call on pattern result
checkProvenance(dataResult);

// Set warnings for UI display
if (provenanceWarnings.length > 0) {
    console.warn('Provenance warnings detected:', provenanceWarnings);
    setProvenanceWarnings(provenanceWarnings);
} else {
    setProvenanceWarnings([]);
}
```

**Testing:**
1. Test with Risk Analytics page (should show warning for `factor_exposures._provenance`)
2. Test with Macro Cycles page (should show warning if `dar._provenance` is stub)
3. Verify warning banner is visible and prominent
4. Test with patterns that have no provenance (should not show warning)

**Validation:**
- ✅ Warning banner displays for stub data
- ✅ Warning is visible and clear
- ✅ No false positives (no warnings for real data)

---

#### Step 1.1.4: Test End-to-End (1.5 hours)

**Test Cases:**
1. **Risk Analytics Page:**
   - Navigate to Risk Analytics page
   - Verify `factor_exposures` has `_provenance.type === "stub"`
   - Verify warning banner displays
   - Verify warning message is clear

2. **Macro Cycles Page:**
   - Navigate to Macro Cycles page
   - Verify `dar` has `_provenance.type === "stub"` (if stub)
   - Verify warning banner displays (if stub)
   - Verify no warning for real data

3. **Other Pages:**
   - Navigate to Dashboard, Holdings, Performance pages
   - Verify no false warnings (no warnings for real data)
   - Verify warnings only appear for stub data

**Validation:**
- ✅ All stub data shows warnings
- ✅ No false positives
- ✅ Warnings are visible and clear

---

### Task 1.1 Summary

**Time:** 4 hours  
**Files Changed:** 2 files
- `backend/app/agents/macro_hound.py` (if needed)
- `full_ui.html` (if needed)

**Result:** Users see clear warnings for stub data, trust preserved

---

## Task 1.2: Fix Pattern Output Extraction (4 hours)

### Root Issue

**Problem:** Orchestrator fails to extract outputs from patterns, causing "No data" errors in UI.

**Current State:**
- Orchestrator has code to handle 3 formats (lines 721-771)
- But extraction logic may be incomplete or buggy
- 6 patterns may be using non-standard formats

**Root Cause:** Orchestrator doesn't correctly extract step results from state when patterns use different output formats.

### Implementation Plan

#### Step 1.2.1: Analyze Current Extraction Logic (1 hour)

**File:** `backend/app/core/pattern_orchestrator.py`

**Location:** Lines 721-771

**Current Code:**
```python
# Extract outputs
outputs = {}
# PHASE 1 FIX: Handle multiple output formats
# Format 1: List of keys ["perf_metrics", "currency_attr", ...]
# Format 2: Dict with keys {"perf_metrics": {...}, ...}
# Format 3: Dict with panels {"panels": [...]} - extract panel IDs and map to step results
outputs_spec = spec.get("outputs", {})

if isinstance(outputs_spec, list):
    # Format 1: List of keys
    output_keys = outputs_spec
    for output_key in output_keys:
        if output_key in state:
            outputs[output_key] = state[output_key]
        else:
            logger.warning(f"Output key '{output_key}' not found in state for pattern {pattern_id}")
elif isinstance(outputs_spec, dict):
    # Format 2: Dict with keys
    if "panels" in outputs_spec:
        # Format 3: Dict with panels - extract panel IDs and map to step results
        # ... panel extraction logic ...
    else:
        # Format 2: Direct dict
        for output_key in outputs_spec.keys():
            if output_key in state:
                outputs[output_key] = state[output_key]
            else:
                logger.warning(f"Output key '{output_key}' not found in state for pattern {pattern_id}")
else:
    logger.error(f"Unexpected outputs format for pattern {pattern_id}: {type(outputs_spec)}")
```

**Actions:**
1. Review extraction logic carefully
2. Identify bugs or gaps
3. Test with each pattern format
4. Document issues found

**Expected Findings:**
- Format 1 (list) should work correctly ✅
- Format 2 (dict) may have issues ⚠️
- Format 3 (panels) may be incomplete ⚠️

---

#### Step 1.2.2: Fix Output Extraction Logic (2 hours)

**File:** `backend/app/core/pattern_orchestrator.py`

**Location:** Lines 721-771

**Root Cause Analysis:**
1. **Format 1 (List):** Should work, but may not handle nested state correctly
2. **Format 2 (Dict):** May not correctly map output keys to state keys
3. **Format 3 (Panels):** Panel extraction logic may be incomplete

**Implementation:**
```python
# Extract outputs from state
outputs = {}
outputs_spec = spec.get("outputs", [])

# PHASE 1 FIX: Robust output extraction handling all formats
if isinstance(outputs_spec, list):
    # Format 1: List of output keys ["perf_metrics", "currency_attr", ...]
    # These should match step "as" keys
    for output_key in outputs_spec:
        if output_key in state:
            outputs[output_key] = state[output_key]
            logger.debug(f"Extracted output '{output_key}' from state")
        else:
            logger.warning(
                f"Output key '{output_key}' not found in state for pattern {pattern_id}. "
                f"Available keys: {list(state.keys())}"
            )
            # Don't fail - just skip missing outputs
            outputs[output_key] = None

elif isinstance(outputs_spec, dict):
    # Format 2: Dict with keys {"perf_metrics": {...}, ...}
    # OR Format 3: Dict with panels {"panels": [...]}
    
    if "panels" in outputs_spec:
        # Format 3: Dict with panels - extract panel IDs and map to step results
        panels = outputs_spec.get("panels", [])
        logger.debug(f"Extracting outputs from {len(panels)} panels for pattern {pattern_id}")
        
        for panel in panels:
            panel_id = panel.get("id") or panel.get("key") or panel.get("name")
            if not panel_id:
                logger.warning(f"Panel missing id/key/name: {panel}")
                continue
            
            # Try to find matching step result
            # Panel ID might match step "as" key directly
            if panel_id in state:
                outputs[panel_id] = state[panel_id]
                logger.debug(f"Mapped panel '{panel_id}' to state key '{panel_id}'")
            else:
                # Try to find step result that matches panel
                # Common patterns: panel_id might be a prefix or suffix of step result
                found = False
                for state_key in state.keys():
                    if state_key == panel_id or state_key.endswith(f"_{panel_id}") or state_key.startswith(f"{panel_id}_"):
                        outputs[panel_id] = state[state_key]
                        logger.debug(f"Mapped panel '{panel_id}' to state key '{state_key}'")
                        found = True
                        break
                
                if not found:
                    logger.warning(
                        f"Panel '{panel_id}' not found in state for pattern {pattern_id}. "
                        f"Available keys: {list(state.keys())}"
                    )
                    outputs[panel_id] = None
    else:
        # Format 2: Direct dict - output keys should match state keys
        for output_key, output_config in outputs_spec.items():
            if output_key in state:
                outputs[output_key] = state[output_key]
                logger.debug(f"Extracted output '{output_key}' from state")
            else:
                logger.warning(
                    f"Output key '{output_key}' not found in state for pattern {pattern_id}. "
                    f"Available keys: {list(state.keys())}"
                )
                outputs[output_key] = None

else:
    logger.error(
        f"Unexpected outputs format for pattern {pattern_id}: {type(outputs_spec)}. "
        f"Expected list or dict, got {type(outputs_spec)}"
    )
    outputs = {}

# Log extracted outputs for debugging
logger.info(f"Extracted {len(outputs)} outputs for pattern {pattern_id}: {list(outputs.keys())}")

# Return outputs
return {
    "data": outputs,
    "trace": trace.serialize(),
    "pattern_id": pattern_id,
    "status": pattern_status
}
```

**Key Improvements:**
1. **Better logging** - Log what's being extracted and what's missing
2. **Graceful degradation** - Don't fail if output key missing, just set to None
3. **Panel mapping** - Improved logic to map panel IDs to step results
4. **Debugging** - Log available state keys when output key not found

**Testing:**
1. Test with each pattern format
2. Verify outputs are correctly extracted
3. Check logs for warnings
4. Verify UI receives correct data

---

#### Step 1.2.3: Test All Patterns (1 hour)

**Test Cases:**
1. **portfolio_cycle_risk:**
   - Execute pattern
   - Verify outputs: `["stdc", "ltdc", "factor_exposures", "cycle_risk_map", "dar"]`
   - Check logs for extraction warnings
   - Verify UI receives correct data

2. **portfolio_scenario_analysis:**
   - Execute pattern
   - Verify outputs: `["valued_base", "scenario_result", "hedge_suggestions", "charts"]`
   - Check logs for extraction warnings
   - Verify UI receives correct data

3. **portfolio_macro_overview:**
   - Execute pattern
   - Verify outputs: `["positions", "regime", "indicators", "factor_exposures", "dar", "charts"]`
   - Check logs for extraction warnings
   - Verify UI receives correct data

4. **cycle_deleveraging_scenarios:**
   - Execute pattern
   - Verify outputs: `["valued_base", "ltdc", "money_printing", "austerity", "default", "hedge_suggestions"]`
   - Check logs for extraction warnings
   - Verify UI receives correct data

5. **macro_trend_monitor:**
   - Execute pattern
   - Verify outputs: `["regime_history", "factor_history", "trend_analysis", "alert_suggestions"]`
   - Check logs for extraction warnings
   - Verify UI receives correct data

6. **holding_deep_dive:**
   - Execute pattern
   - Verify outputs: `["position", "position_perf", "contribution", "currency_attr", "risk", "transactions", "fundamentals", "comparables"]`
   - Check logs for extraction warnings
   - Verify UI receives correct data

**Validation:**
- ✅ All patterns execute successfully
- ✅ All outputs extracted correctly
- ✅ No "No data" errors in UI
- ✅ Logs show correct extraction

---

### Task 1.2 Summary

**Time:** 4 hours  
**Files Changed:** 1 file
- `backend/app/core/pattern_orchestrator.py`

**Result:** All patterns correctly extract outputs, no "No data" errors

---

## Task 1.3: Update 6 Patterns to Standard Format (8 hours)

### Root Issue

**Problem:** 6 patterns use non-standard output formats, causing extraction issues.

**Current State:**
- All 6 patterns already use list format for outputs ✅
- But they may have other format issues ⚠️

**Root Cause:** Patterns may have inconsistent structure or missing step "as" keys.

### Implementation Plan

#### Step 1.3.1: Audit Pattern Formats (1 hour)

**Patterns to Audit:**
1. `portfolio_cycle_risk.json`
2. `portfolio_macro_overview.json`
3. `cycle_deleveraging_scenarios.json`
4. `macro_trend_monitor.json`
5. `holding_deep_dive.json`
6. `portfolio_scenario_analysis.json`

**Check:**
1. ✅ Outputs format (should be list)
2. ✅ Step "as" keys match output keys
3. ✅ Step arguments are correct
4. ✅ Template references are correct

**Expected Findings:**
- All patterns already use list format for outputs ✅
- May need to verify step "as" keys match output keys
- May need to fix template references

---

#### Step 1.3.2: Fix Pattern Format Issues (6 hours)

**For Each Pattern (1 hour each):**

**1. portfolio_cycle_risk.json**

**Current State:**
```json
{
  "outputs": ["stdc", "ltdc", "factor_exposures", "cycle_risk_map", "dar"],
  "steps": [
    {"capability": "cycles.compute_short_term", "as": "stdc"},
    {"capability": "cycles.compute_long_term", "as": "ltdc"},
    {"capability": "risk.compute_factor_exposures", "as": "factor_exposures"},
    {"capability": "risk.overlay_cycle_phases", "as": "cycle_risk_map"},
    {"capability": "macro.compute_dar", "as": "dar"}
  ]
}
```

**Actions:**
1. Verify all step "as" keys match output keys ✅
2. Verify template references are correct
3. Test pattern execution
4. Verify outputs are extracted correctly

**2. portfolio_macro_overview.json**

**Actions:**
1. Verify all step "as" keys match output keys
2. Verify template references are correct
3. Test pattern execution
4. Verify outputs are extracted correctly

**3. cycle_deleveraging_scenarios.json**

**Actions:**
1. Verify all step "as" keys match output keys
2. Verify template references are correct
3. Test pattern execution
4. Verify outputs are extracted correctly

**4. macro_trend_monitor.json**

**Actions:**
1. Verify all step "as" keys match output keys
2. Verify template references are correct
3. Test pattern execution
4. Verify outputs are extracted correctly

**5. holding_deep_dive.json**

**Actions:**
1. Verify all step "as" keys match output keys
2. Verify template references are correct
3. Test pattern execution
4. Verify outputs are extracted correctly

**6. portfolio_scenario_analysis.json**

**Actions:**
1. Verify all step "as" keys match output keys
2. Verify template references are correct
3. Test pattern execution
4. Verify outputs are extracted correctly

---

#### Step 1.3.3: Test All Patterns (1 hour)

**Test Cases:**
1. Execute each pattern via API
2. Verify outputs are correctly extracted
3. Verify UI receives correct data
4. Check for "No data" errors

**Validation:**
- ✅ All 6 patterns execute successfully
- ✅ All outputs extracted correctly
- ✅ UI displays correct data
- ✅ No "No data" errors

---

### Task 1.3 Summary

**Time:** 8 hours  
**Files Changed:** 6 pattern files (if needed)

**Result:** All patterns use standard format, outputs extracted correctly

---

## Phase 1 Complete Validation

### Success Criteria

**Task 1.1: Provenance Warnings**
- ✅ Risk Analytics shows provenance warnings
- ✅ Macro Cycles shows provenance warnings (if stub)
- ✅ Warning banner is visible and clear
- ✅ No false positives

**Task 1.2: Pattern Output Extraction**
- ✅ All patterns extract outputs correctly
- ✅ No "No data" errors
- ✅ Logs show correct extraction

**Task 1.3: Pattern Format Standardization**
- ✅ All 6 patterns use standard format
- ✅ Step "as" keys match output keys
- ✅ Template references are correct

### End-to-End Testing

**Test Scenarios:**
1. **Risk Analytics Page:**
   - Navigate to page
   - Verify pattern executes successfully
   - Verify outputs extracted correctly
   - Verify provenance warnings display
   - Verify no "No data" errors

2. **All 6 Patterns:**
   - Execute each pattern via API
   - Verify outputs extracted correctly
   - Verify UI receives correct data
   - Verify no errors

3. **Other Pages:**
   - Verify no regressions
   - Verify existing functionality still works

**Validation:**
- ✅ All success criteria met
- ✅ No regressions
- ✅ User trust preserved

---

## Phase 1 Summary

**Total Time:** 16 hours  
**Files Changed:** 3-9 files (depending on findings)
- `backend/app/agents/macro_hound.py` (if needed)
- `full_ui.html` (if needed)
- `backend/app/core/pattern_orchestrator.py`
- 6 pattern JSON files (if needed)

**Result:**
- ✅ Users see clear warnings for stub data
- ✅ All patterns work correctly
- ✅ No "No data" errors
- ✅ User trust preserved

---

## Next Steps

**After Phase 1:**
1. **Phase 2:** Foundation & validation (32 hours)
2. **Phase 3:** Feature implementation (48 hours)
3. **Phase 4:** Technical debt cleanup (conditional)
4. **Phase 5:** Quality & testing (24 hours)

---

**Status:** Ready for execution

