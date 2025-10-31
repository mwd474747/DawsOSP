
# Macro Systems Refactoring Plan

## Executive Summary
This plan consolidates and refactors the macro analysis systems to eliminate duplications, fix broken patterns, and align with the Dalio framework while maintaining all existing functionality.

## Current State Analysis

### Problems Identified

1. **Duplicate Patterns**
   - `macro_cycles_overview.json` - Original working pattern
   - `macro_cycles_overview_fixed.json` - Unclear duplicate (possibly broken)
   
2. **Broken Pattern**
   - `cycle_deleveraging_scenarios.json` - Has `custom_shocks` parameter that doesn't exist in agent

3. **Service Architecture Issues**
   - Multiple scenario services: `scenarios.py`, `macro_aware_scenarios.py`
   - Unclear which service handles which use case
   - Potential duplication of deleveraging scenario logic

4. **Missing Documentation**
   - Civil/Internal Order cycle not documented in MACRO_DASHBOARD_AUDIT_REPORT.md
   - Unclear how macro-aware scenarios integrate with base scenarios

## Refactoring Goals

1. **Remove Duplications** - One source of truth per concept
2. **Fix Broken Patterns** - All patterns must execute successfully
3. **Clarify Architecture** - Clear separation of concerns between services
4. **Maintain Functionality** - Zero feature loss during refactoring
5. **Complete Documentation** - All 4 cycles fully documented

## Detailed Refactoring Plan

### Phase 1: Pattern Cleanup

#### Step 1.1: Investigate Duplicate Pattern
**File**: `backend/patterns/macro_cycles_overview_fixed.json`

**Actions**:
- Compare with `macro_cycles_overview.json`
- Determine if "fixed" version has unique features
- If identical or inferior: DELETE
- If superior or has unique features: MERGE into main pattern

**Decision Criteria**:
```
IF fixed_version == original_version:
    DELETE fixed_version
ELIF fixed_version.has_unique_features:
    MERGE unique_features -> original_version
    DELETE fixed_version
ELSE:
    ANALYZE differences
    CONSULT with user
```

#### Step 1.2: Fix Deleveraging Scenarios Pattern
**File**: `backend/patterns/cycle_deleveraging_scenarios.json`

**Problem**: Step references `custom_shocks` parameter that doesn't exist
```json
{
  "capability": "scenarios.deleveraging_money_printing",
  "args": {
    "portfolio_id": "{{inputs.portfolio_id}}",
    "pack_id": "{{ctx.pricing_pack_id}}",
    "custom_shocks": "{{inputs.custom_shocks}}"  // <- DOESN'T EXIST
  }
}
```

**Solution**: Remove `custom_shocks` from all three deleveraging scenario steps

**Verification**: Pattern must execute without errors

### Phase 2: Service Architecture Consolidation

#### Step 2.1: Clarify Service Responsibilities

**Current Services**:
1. `scenarios.py` - Base scenario service with shock library
2. `macro_aware_scenarios.py` - Regime-adjusted scenarios
3. `macro.py` - Regime detection and indicators
4. `cycles.py` - STDC/LTDC/Empire cycle detection

**Proposed Architecture**:
```
MacroService (macro.py)
├── Regime Detection (5 regimes)
├── Indicator Management (FRED API)
└── Regime History

CyclesService (cycles.py)
├── STDC Detection
├── LTDC Detection
├── Empire Detection
└── Civil/Internal Order Detection  // <- ADD THIS

ScenarioService (scenarios.py)
├── Base Shock Library
├── Apply Scenarios
├── Factor Beta Calculation
└── Hedge Suggestions

MacroAwareScenarioService (macro_aware_scenarios.py)
├── Regime-Adjusted Shocks
├── Cycle-Adjusted Probabilities
├── Weighted Scenario Rankings
└── Regime-Appropriate Hedges
```

**Key Principle**: Each service has ONE clear responsibility

#### Step 2.2: Document Service Integration Points

**Integration Flow**:
```
User Request
    ↓
Pattern Orchestrator
    ↓
MacroHound Agent
    ↓
├── macro.detect_regime() → MacroService
├── cycles.compute_civil() → CyclesService
├── scenarios.deleveraging_*() → ScenarioService
└── macro_aware.apply_scenario() → MacroAwareScenarioService
                                        ↓
                                   Uses: MacroService + ScenarioService
```

### Phase 3: Missing Functionality Implementation

#### Step 3.1: Add Civil/Internal Order Cycle

**Files to Modify**:
1. `backend/app/services/cycles.py` - Add CivilOrderDetector class
2. `backend/app/agents/macro_hound.py` - Already has `cycles.compute_civil` capability
3. `backend/patterns/macro_cycles_overview.json` - Already calls it with fallback

**Implementation**:
```python
# In cycles.py
class CivilOrderDetector:
    """
    Civil/Internal Order Cycle detector (6 stages).
    Based on Dalio's framework for social cohesion.
    """
    STAGES = {
        1: "Harmony",
        2: "Rising Tension", 
        3: "Crisis Brewing",
        4: "Severe Conflict",
        5: "Civil War",
        6: "Revolution"
    }
    
    STAGE_WEIGHTS = {
        "Harmony": {
            "gini_coefficient": -2.0,  # Low inequality
            "institutional_trust": 2.0,  # High trust
            "polarization_index": -2.0,  # Low polarization
        },
        # ... etc for all 6 stages
    }
```

**Verification**: Pattern `macro_cycles_overview` executes without fallback

#### Step 3.2: Complete Dalio Deleveraging Scenarios

**Current State**: Three scenarios defined in `scenarios.py`:
- `dalio_money_printing_deleveraging`
- `dalio_austerity_deleveraging`
- `dalio_default_deleveraging`

**Verification Needed**:
- ✅ Shock definitions exist in SCENARIO_LIBRARY
- ✅ Agent has capability methods
- ❓ Pattern execution works

**Test**: Execute `cycle_deleveraging_scenarios` pattern after fix

### Phase 4: Documentation Updates

#### Step 4.1: Update MACRO_DASHBOARD_AUDIT_REPORT.md

**Additions Needed**:
1. Civil/Internal Order Cycle section (currently missing)
2. Service architecture diagram
3. Pattern-to-service mapping
4. Integration testing results

**Structure**:
```markdown
## 4️⃣ **Internal Order/Disorder Cycle**
**Coverage: 5/5 (100%)**

| Indicator | Value | Status | Data Source |
|-----------|-------|--------|-------------|
| Wealth Gap (Gini) | 0.418 | ✅ Live | World Bank API |
| Political Polarization | 46.8/100 | ✅ Calculated | ... |
| Social Unrest Score | 30/100 | ✅ Calculated | ... |
| Fiscal Deficit | -6.20% GDP | ✅ Live | FRED API |
| Civil War Risk | 80% | ✅ Calculated | Dalio framework |

**Current Stage**: CRISIS
```

#### Step 4.2: Create Service Integration Guide

**New File**: `MACRO_SERVICES_INTEGRATION.md`

**Contents**:
- Service responsibility matrix
- API endpoint mapping
- Pattern orchestration flow
- Error handling strategies
- Performance considerations

### Phase 5: Validation & Testing

#### Step 5.1: Pattern Execution Tests

**Test Matrix**:
```
Pattern                          | Status | Notes
--------------------------------|--------|------------------
macro_cycles_overview           | ✅     | Working
cycle_deleveraging_scenarios    | ❌     | Fix custom_shocks
portfolio_macro_overview        | ✅     | Working
macro_trend_monitor             | ✅     | Working
```

#### Step 5.2: Service Integration Tests

**Test Cases**:
1. MacroService → CyclesService integration
2. ScenarioService → MacroAwareScenarioService integration
3. Pattern → Agent → Service flow
4. Error propagation and fallbacks
5. Cache coherency across services

#### Step 5.3: Performance Validation

**Metrics to Monitor**:
- Pattern execution time (<5s target)
- Service response time (<1s per capability)
- Database query efficiency
- Cache hit rates

## Implementation Sequence

### Week 1: Investigation & Planning
- [ ] Compare duplicate patterns
- [ ] Document current service interactions
- [ ] Identify all integration points
- [ ] Create detailed test plan

### Week 2: Pattern Fixes
- [ ] Fix cycle_deleveraging_scenarios.json
- [ ] Remove or merge duplicate pattern
- [ ] Update pattern documentation
- [ ] Test all macro patterns

### Week 3: Service Implementation
- [ ] Implement CivilOrderDetector
- [ ] Add cycles.compute_civil to agent
- [ ] Verify deleveraging scenarios
- [ ] Test service integrations

### Week 4: Documentation & Validation
- [ ] Update MACRO_DASHBOARD_AUDIT_REPORT.md
- [ ] Create MACRO_SERVICES_INTEGRATION.md
- [ ] Run full integration test suite
- [ ] Performance benchmarking

## Risk Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: 
- Test each change in isolation
- Maintain fallback logic during transition
- Keep original files until verification complete

### Risk 2: Performance Degradation
**Mitigation**:
- Benchmark before/after each change
- Monitor cache hit rates
- Optimize database queries if needed

### Risk 3: Documentation Drift
**Mitigation**:
- Update docs in same PR as code changes
- Require doc review for merge approval
- Automated doc generation where possible

## Success Criteria

1. ✅ All patterns execute without errors
2. ✅ No duplicate code or patterns
3. ✅ Clear service responsibilities
4. ✅ Complete 4-cycle coverage
5. ✅ <5s pattern execution time
6. ✅ 100% documentation coverage
7. ✅ Zero feature regression

## Rollback Plan

If issues arise during refactoring:

1. **Immediate Rollback**: Git revert to last known good state
2. **Service Isolation**: Disable new service, route to original
3. **Pattern Fallback**: Use fallback data in patterns
4. **Gradual Rollout**: Enable changes per-user or per-pattern

## Conclusion

This refactoring will:
- **Eliminate** duplicate patterns and unclear code
- **Fix** broken cycle_deleveraging_scenarios pattern
- **Clarify** service architecture and responsibilities
- **Complete** Civil/Internal Order cycle implementation
- **Maintain** all existing functionality with zero regression

The phased approach ensures we can validate each change before proceeding, minimizing risk while maximizing clarity and maintainability.
