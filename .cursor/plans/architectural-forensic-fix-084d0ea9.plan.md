<!-- 084d0ea9-74fa-4666-9d28-06966a359471 d270e4ed-9337-4f83-ab3c-f7435461f409 -->
# Architectural Forensic Fix Plan

## Executive Summary

This plan addresses critical architectural failures discovered through forensic analysis:

1. **Phantom Capabilities**: Patterns reference non-existent capabilities (tax.*, metrics.unrealized_pl)
2. **Validation Bypass**: Pattern orchestrator validates but doesn't prevent execution of invalid patterns
3. **Hardcoded Values**: Switching cost scores hardcoded to 5, making moat strength calculations invalid
4. **Silent Degradation**: Errors logged but execution continues, leading to confusing failures

## Phase 1: Immediate Triage (Stop the Bleeding)

### 1.1 Disable Invalid Patterns

- **Action**: Archive or disable patterns with phantom capabilities
- **Files**: 
  - `backend/patterns/tax_harvesting_opportunities.json` (6 missing capabilities)
  - `backend/patterns/portfolio_tax_report.json` (4 missing capabilities)
- **Method**: Move to `.archive/patterns/` or add `"enabled": false` flag
- **Impact**: Prevents runtime failures from missing tax capabilities

### 1.2 Fix Pattern Orchestrator Validation

- **File**: `backend/app/core/pattern_orchestrator.py`
- **Issue**: Lines 612-618 validate but only log warnings, allowing execution to continue
- **Fix**: Make capability validation blocking (raise ValueError if capabilities missing)
- **Change**: Modify `run_pattern()` to fail fast when `validate_pattern()` returns invalid
- **Lines**: 612-634

### 1.3 Add Capability Existence Check

- **File**: `backend/app/core/pattern_orchestrator.py`
- **Action**: Add pre-execution check in `run_pattern()` that validates all capabilities exist before starting
- **Location**: After line 608, before step execution loop
- **Behavior**: Raise ValueError immediately if any capability is missing

## Phase 2: Fix Hardcoded Values

### 2.1 Replace Hardcoded Switching Cost Scores

- **Files**:
  - `backend/app/agents/data_harvester.py` (line 1140)
  - `backend/app/services/fundamentals_transformer.py` (line 149)
- **Current**: `switching_cost_score = Decimal("5")`
- **Fix Options**:
  - **Option A**: Return None and mark as "not calculated" in provenance
  - **Option B**: Implement sector-based lookup table
  - **Option C**: Remove from moat strength calculation until implemented
- **Recommendation**: Option A (return None with provenance warning)

### 2.2 Update Moat Strength Calculation

- **File**: `backend/app/services/ratings.py`
- **Issue**: Moat strength uses switching_cost_score (15% weight) which is always 5
- **Fix**: Handle None switching_cost_score gracefully (exclude from calculation or use 0)
- **Impact**: Moat strength calculations will be more accurate (or clearly marked as incomplete)

## Phase 3: Architectural Improvements

### 3.1 Implement Strict Capability Contracts

- **File**: `backend/app/core/pattern_orchestrator.py`
- **Action**: Enhance `validate_pattern()` to be strict by default
- **Change**: Remove "continuing anyway" behavior (line 614)
- **New Behavior**: Raise ValueError immediately if validation fails

### 3.2 Add Pattern Dependency Validation

- **File**: `backend/app/core/pattern_orchestrator.py`
- **Current**: `validate_pattern_dependencies()` exists but only checks template references
- **Enhancement**: Also validate that all referenced capabilities exist
- **Location**: Enhance existing method at line 1134

### 3.3 Add Provenance Warnings for Stub Data

- **Files**: 
  - `backend/app/agents/data_harvester.py`
  - `backend/app/services/fundamentals_transformer.py`
- **Action**: When returning hardcoded/default values, mark in provenance as "incomplete" or "estimated"
- **Method**: Use `_provenance` dict with `"type": "stub"` and `"warnings": ["switching_cost_score not calculated"]`

## Phase 4: Testing and Validation

### 4.1 Create Pattern Validation Script

- **File**: `scripts/validate_all_patterns.py` (new)
- **Purpose**: Validate all patterns against current capability registry
- **Output**: Report of missing capabilities, invalid references, hardcoded values
- **Usage**: Run before deployments to catch issues early

### 4.2 Add Integration Tests

- **File**: `backend/tests/test_pattern_validation.py` (new)
- **Tests**:
  - Test that patterns with missing capabilities fail validation
  - Test that valid patterns execute successfully
  - Test that hardcoded values are marked in provenance

## Implementation Details

### Critical Code Changes

**File: `backend/app/core/pattern_orchestrator.py`**

1. **Line 612-618**: Change validation to be blocking
```python
# BEFORE:
if not validation_result["valid"]:
    logger.warning(f"Pattern '{pattern_id}' validation failed (continuing anyway):")
    # ... logs errors but continues

# AFTER:
if not validation_result["valid"]:
    error_msg = f"Pattern '{pattern_id}' validation failed:\n" + "\n".join(validation_result["errors"])
    logger.error(error_msg)
    raise ValueError(error_msg)
```

2. **Line 630-634**: Already raises error for dependency validation (keep as-is)

3. **Add pre-execution capability check** (after line 608):
```python
# Validate all capabilities exist before execution
missing_caps = []
for step in spec["steps"]:
    capability = step.get("capability")
    if capability and not self.agent_runtime.capability_map.get(capability):
        missing_caps.append(capability)
if missing_caps:
    raise ValueError(f"Pattern '{pattern_id}' references missing capabilities: {missing_caps}")
```


**File: `backend/app/agents/data_harvester.py`**

**Line 1139-1140**: Replace hardcoded value

```python
# BEFORE:
# TODO: Implement sector-based lookup for switching costs
switching_cost_score = Decimal("5")

# AFTER:
# TODO: Implement sector-based lookup for switching costs
switching_cost_score = None  # Not calculated - will be excluded from moat strength
```

**File: `backend/app/services/fundamentals_transformer.py`**

**Line 149**: Replace hardcoded value

```python
# BEFORE:
result["switching_cost_score"] = Decimal("5")  # Mid-range default

# AFTER:
result["switching_cost_score"] = None  # Not calculated - requires sector-based lookup
```

**File: `backend/app/services/ratings.py`**

Update moat strength calculation to handle None switching_cost_score:

- If switching_cost_score is None, exclude it from calculation (adjust weights proportionally)
- Or set to 0 and add provenance warning

## Risk Assessment

**Low Risk**:

- Disabling invalid patterns (no production impact if not used)
- Adding validation checks (prevents future issues)

**Medium Risk**:

- Changing validation to be blocking (may break existing patterns that pass validation but fail at runtime)
- Removing hardcoded values (may change moat strength calculations)

**Mitigation**:

- Run validation script first to identify all affected patterns
- Test moat strength calculations with None switching_cost_score
- Add feature flag to allow graceful degradation if needed

## Success Criteria

1. ✅ No patterns reference non-existent capabilities
2. ✅ Pattern orchestrator fails fast when capabilities are missing
3. ✅ No hardcoded values masquerading as calculated metrics
4. ✅ All stub/incomplete data marked in provenance
5. ✅ Validation script catches issues before deployment

### To-dos

- [ ] Archive or disable tax_harvesting_opportunities.json and portfolio_tax_report.json patterns that reference non-existent capabilities
- [ ] Modify pattern_orchestrator.py run_pattern() to fail fast when validate_pattern() returns invalid (lines 612-618)
- [ ] Add pre-execution capability existence check in run_pattern() before step execution loop
- [ ] Replace hardcoded switching_cost_score = Decimal("5") with None in data_harvester.py line 1140
- [ ] Replace hardcoded switching_cost_score = Decimal("5") with None in fundamentals_transformer.py line 149
- [ ] Update ratings.py moat strength calculation to handle None switching_cost_score gracefully
- [ ] Add provenance warnings when returning None/incomplete values for switching_cost_score
- [ ] Create scripts/validate_all_patterns.py to validate all patterns against capability registry
- [ ] Add tests/test_pattern_validation.py with tests for missing capabilities and validation behavior