# DawsOS Pattern Integration Implementation Plan
Date: October 31, 2025

## Executive Summary
This plan addresses the integration failures affecting 10 of 12 patterns (83% failure rate) in the DawsOS system. The root causes are template resolution issues, missing capability registrations, data type mismatches, and missing UI inputs.

## Phase 1: Pattern Orchestrator State Management Fix
**Objective**: Fix template resolution failures where {{state.positions}} and similar paths resolve to None

### Problem Analysis
```python
# Current Issue:
# When step 1 stores result as "positions", 
# step 2 cannot access it via {{state.positions}}
# The state is not properly propagated between steps
```

### Solution Design
```python
# File: backend/app/core/pattern_orchestrator.py

class PatternOrchestrator:
    def _store_result(self, state, alias, result):
        """Enhanced state storage with multiple access paths"""
        # 1. Store in state namespace
        state['state'][alias] = result
        
        # 2. Store at top level for convenience
        state[alias] = result
        
        # 3. Store nested fields for direct access
        if isinstance(result, dict):
            for key, value in result.items():
                # Allow {{positions.positions}} syntax
                state[f"{alias}.{key}"] = value
                
    def _apply_defaults(self, inputs, pattern_spec):
        """Apply default values from pattern specification"""
        for key, spec in pattern_spec['inputs'].items():
            if key not in inputs and 'default' in spec:
                inputs[key] = spec['default']
        return inputs
```

### Implementation Steps
1. Modify `run_pattern` to initialize state with both namespaces
2. Update `_resolve_value` to check multiple paths
3. Add `_apply_defaults` before pattern execution
4. Create comprehensive error messages for missing templates

### Testing Requirements
```python
# Test cases for template resolution
test_cases = [
    "{{state.positions}}",          # State namespace
    "{{positions}}",                 # Top-level alias
    "{{positions.positions}}",       # Nested access
    "{{inputs.policies}}",          # With defaults
    "{{ctx.pricing_pack_id}}"       # Context access
]
```

## Phase 2: Missing Agent Capabilities Registration
**Objective**: Register all missing capabilities in agent runtime

### Charts Agent Fix
```python
# File: backend/app/agents/charts_agent.py
class ChartsAgent(BaseAgent):
    def get_capabilities(self) -> List[str]:
        return [
            "charts.macro_overview",
            "charts.scenario_deltas",  # ADD THIS
            "charts.overview"           # ADD THIS if needed
        ]
```

### Registration Verification
```python
# File: backend/app/core/agent_runtime.py
# Ensure ChartsAgent is properly registered
runtime.register_agent(ChartsAgent())
```

### Missing Capabilities List
| Agent | Missing Capability | Pattern Using It |
|-------|-------------------|------------------|
| ChartsAgent | charts.scenario_deltas | portfolio_scenario_analysis |
| ReportsAgent | reports.render_pdf | export_portfolio_report |
| MacroAgent | compute_zscores | portfolio_macro_overview |

## Phase 3: Data Type Alignment (UUID vs Ticker)
**Objective**: Standardize identifier handling across patterns

### Current Mismatches
```javascript
// UI sends: 
{ security_id: "AAPL" }  // Ticker symbol

// Backend expects:
{ security_id: "550e8400-e29b-41d4-a716-446655440000" }  // UUID
```

### Solution Options

#### Option A: Add Lookup Step (Recommended)
```json
// Pattern modification: holding_deep_dive.json
{
  "steps": [
    {
      "capability": "securities.lookup_by_ticker",
      "args": { "ticker": "{{inputs.ticker}}" },
      "as": "security"
    },
    {
      "capability": "get_position_details",
      "args": { "security_id": "{{security.id}}" },
      "as": "details"
    }
  ]
}
```

#### Option B: Modify UI to Send UUIDs
```javascript
// File: full_ui.html
// Before calling pattern, lookup UUID from holdings data
const security = holdings.find(h => h.symbol === ticker);
const params = { security_id: security.security_id };
```

### Affected Patterns
- holding_deep_dive
- buffett_checklist
- Any pattern accepting security_id

## Phase 4: UI Input Completeness
**Objective**: Ensure UI sends all required and optional inputs

### Missing Inputs Matrix
| Pattern | Missing Input | Default Value | UI Change Needed |
|---------|--------------|---------------|------------------|
| policy_rebalance | policies | [] | Add empty array |
| policy_rebalance | constraints | {max_te_pct: 2.0} | Add default object |
| portfolio_macro_overview | confidence_level | 0.95 | Add default |
| export_portfolio_report | include_performance | true | Add boolean |
| export_portfolio_report | include_macro | false | Add boolean |

### UI Update Template
```javascript
// File: full_ui.html
// Update pattern execution calls

// BEFORE:
apiClient.executePattern('policy_rebalance', {
    portfolio_id: portfolioId
})

// AFTER:
apiClient.executePattern('policy_rebalance', {
    portfolio_id: portfolioId,
    policies: [],  // Add default
    constraints: {
        max_te_pct: 2.0,
        max_turnover_pct: 10.0,
        min_lot_value: 500
    }
})
```

## Phase 5: Pattern-Specific Fixes

### 5.1 portfolio_scenario_analysis
```yaml
Issues:
  - Missing charts.scenario_deltas capability
  - Scenario parameters not properly formatted

Fixes:
  1. Register charts.scenario_deltas in ChartsAgent
  2. Ensure UI sends scenario parameters correctly
  3. Verify macro.run_scenario capability exists
```

### 5.2 buffett_checklist
```yaml
Issues:
  - {{state.fundamentals}} resolves to None
  - fundamentals.load returns empty for tickers

Fixes:
  1. Fix state propagation (Phase 1)
  2. Ensure fundamentals.load handles tickers
  3. Add fallback data for missing fundamentals
```

### 5.3 news_impact_analysis
```yaml
Issues:
  - {{state.positions}} not available
  - News API integration incomplete

Fixes:
  1. Fix state propagation (Phase 1)
  2. Verify news API credentials
  3. Implement news.compute_portfolio_impact
```

### 5.4 export_portfolio_report
```yaml
Issues:
  - {{performance}} variable undefined
  - PDF generation not implemented

Fixes:
  1. Add performance calculation step
  2. Implement reports.render_pdf capability
  3. Handle conditional steps properly
```

## Implementation Sequence

### Week 1: Core Infrastructure
1. **Day 1-2**: Fix PatternOrchestrator state management
   - Implement enhanced state storage
   - Add default value application
   - Create unit tests

2. **Day 3-4**: Register missing capabilities
   - Update all agent get_capabilities methods
   - Verify agent runtime registration
   - Test capability discovery

3. **Day 5**: UUID/Ticker alignment
   - Implement lookup service
   - Update affected patterns
   - Test identifier resolution

### Week 2: Pattern-Specific Integration
1. **Day 6-7**: Fix UI input completeness
   - Update all executePattern calls
   - Add default values
   - Test pattern execution

2. **Day 8-9**: Individual pattern fixes
   - portfolio_scenario_analysis
   - buffett_checklist
   - policy_rebalance

3. **Day 10**: Remaining patterns
   - news_impact_analysis
   - export_portfolio_report
   - Others

## Testing Strategy

### Unit Tests
```python
# Test pattern orchestrator state management
def test_state_propagation():
    orchestrator = PatternOrchestrator()
    state = {}
    orchestrator._store_result(state, "positions", {"data": [1,2,3]})
    assert state["state"]["positions"] == {"data": [1,2,3]}
    assert state["positions"] == {"data": [1,2,3]}

# Test capability registration
def test_capability_discovery():
    runtime = AgentRuntime()
    assert "charts.scenario_deltas" in runtime.get_capabilities()
```

### Integration Tests
```python
# Test each pattern end-to-end
patterns_to_test = [
    "portfolio_scenario_analysis",
    "policy_rebalance",
    "buffett_checklist",
    # ... all 12 patterns
]

for pattern in patterns_to_test:
    result = await execute_pattern(pattern, test_inputs)
    assert result["status"] == "success"
```

### UI Tests
```javascript
// Test pattern execution from UI
async function testPatternIntegration() {
    const patterns = [
        'portfolio_overview',
        'macro_cycles_overview',
        // ... test all patterns
    ];
    
    for (const pattern of patterns) {
        const result = await apiClient.executePattern(pattern, getTestInputs(pattern));
        assert(result.status === 'success');
    }
}
```

## Validation Metrics

### Success Criteria
- 100% of patterns execute without errors
- All UI sections display data correctly
- Template resolution success rate: 100%
- Capability discovery: All required capabilities registered
- Data type consistency: No UUID/ticker mismatches

### Performance Targets
- Pattern execution: < 2 seconds average
- UI responsiveness: < 100ms for user actions
- Error recovery: Graceful degradation for failures

## Risk Mitigation

### Potential Risks
1. **Breaking existing functionality**
   - Mitigation: Comprehensive test coverage before changes
   - Rollback plan: Version control, staged deployment

2. **State management complexity**
   - Mitigation: Clear documentation, consistent patterns
   - Monitoring: Log all template resolution attempts

3. **UI/Backend contract changes**
   - Mitigation: Versioned API, backward compatibility
   - Communication: Clear documentation of changes

## Rollout Plan

### Phase 1: Development Environment
- Implement all fixes
- Run comprehensive tests
- Document changes

### Phase 2: Staging
- Deploy to staging environment
- User acceptance testing
- Performance validation

### Phase 3: Production
- Gradual rollout (10% → 50% → 100%)
- Monitor error rates
- Quick rollback capability

## Code Simulation Examples

### Simulated Fix: State Propagation
```python
# BEFORE (broken):
state = {'ctx': ctx, 'inputs': inputs}
result = await capability()
# Result not accessible in next step

# AFTER (fixed):
state = {'ctx': ctx, 'inputs': inputs, 'state': {}}
result = await capability()
state['state']['alias'] = result
state['alias'] = result  # Dual storage
# Result accessible via {{state.alias}} or {{alias}}
```

### Simulated Fix: UI Input Completeness
```javascript
// BEFORE (incomplete):
const executeRebalance = () => {
    apiClient.executePattern('policy_rebalance', {
        portfolio_id: portfolioId
    });
};

// AFTER (complete):
const executeRebalance = () => {
    const defaultConstraints = {
        max_te_pct: 2.0,
        max_turnover_pct: 10.0,
        min_lot_value: 500
    };
    
    apiClient.executePattern('policy_rebalance', {
        portfolio_id: portfolioId,
        policies: selectedPolicies || [],
        constraints: userConstraints || defaultConstraints
    });
};
```

### Simulated Fix: Capability Registration
```python
# BEFORE (missing capability):
class ChartsAgent(BaseAgent):
    def get_capabilities(self):
        return ["charts.macro_overview"]

# AFTER (capability registered):
class ChartsAgent(BaseAgent):
    def get_capabilities(self):
        return [
            "charts.macro_overview",
            "charts.scenario_deltas",
            "charts.overview"
        ]
```

## Conclusion
This plan provides a systematic approach to fixing all pattern integration issues in DawsOS. The key is addressing the root causes (state management, capability registration, data types, and input completeness) rather than applying band-aid fixes to individual patterns. With proper implementation, all 12 patterns should achieve 100% functionality within 2 weeks.