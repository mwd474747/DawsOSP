# DawsOS Pattern Fix Priority Matrix
## Quick Wins vs Strategic Fixes

### Priority 1: High Impact, Low Effort (Quick Wins)
**Timeline: 1-2 days**

#### 1.1 Register Missing Capabilities
**Effort: 30 minutes | Impact: Enables 3 patterns**
```python
# File: backend/app/agents/charts_agent.py
# Line 40-43, add missing capabilities
def get_capabilities(self):
    return [
        "charts.macro_overview",
        "charts.scenario_deltas",  # ADD THIS LINE
        "charts.overview"           # ADD THIS LINE
    ]
```
**Patterns Fixed:**
- portfolio_scenario_analysis ✓
- Partial fix for risk visualizations

---

#### 1.2 Add Default Inputs in UI
**Effort: 1 hour | Impact: Enables 2 patterns**
```javascript
// File: full_ui.html
// Lines ~7900-7920 (Optimization section)
const result = await apiClient.executePattern('policy_rebalance', {
    portfolio_id: '64ff3be6-0ed1-4990-a32b-4ded17f0320c',
    policies: [],  // ADD THIS
    constraints: { // ADD THIS BLOCK
        max_te_pct: 2.0,
        max_turnover_pct: 10.0,
        min_lot_value: 500
    }
});
```
**Patterns Fixed:**
- policy_rebalance ✓
- portfolio_macro_overview (partial)

---

### Priority 2: High Impact, Medium Effort
**Timeline: 2-3 days**

#### 2.1 Fix Pattern Orchestrator State Management
**Effort: 4 hours | Impact: Enables 5+ patterns**
```python
# File: backend/app/core/pattern_orchestrator.py
# Critical changes needed:

# 1. Dual state storage (line ~340)
if as_name:
    state[as_name] = result  # Top level
    if 'state' not in state:
        state['state'] = {}
    state['state'][as_name] = result  # State namespace

# 2. Apply defaults (new method ~line 200)
def _apply_pattern_defaults(self, inputs, pattern_spec):
    for key, spec in pattern_spec.get('inputs', {}).items():
        if key not in inputs and 'default' in spec:
            inputs[key] = spec['default']
    return inputs
```
**Patterns Fixed:**
- buffett_checklist ✓
- news_impact_analysis ✓
- export_portfolio_report ✓
- cycle_deleveraging_scenarios ✓
- All patterns with state dependencies

---

#### 2.2 UUID vs Ticker Resolution
**Effort: 2 hours | Impact: Enables 2 patterns**

**Option A: Add Lookup in UI (Simpler)**
```javascript
// File: full_ui.html
// Before calling buffett_checklist (line ~8360)
const holding = holdings.find(h => h.symbol === selectedSymbol);
if (holding) {
    const result = await apiClient.executePattern('buffett_checklist', {
        security_id: holding.security_id  // Use UUID not ticker
    });
}
```

**Option B: Add Lookup Capability (Better)**
```python
# New capability in FinancialAnalyst
async def securities_lookup_ticker(self, ticker: str) -> str:
    """Convert ticker to UUID"""
    query = "SELECT id FROM securities WHERE symbol = $1"
    result = await execute_query(query, ticker)
    return result[0]['id'] if result else None
```
**Patterns Fixed:**
- holding_deep_dive ✓
- buffett_checklist ✓

---

### Priority 3: Medium Impact, Medium Effort
**Timeline: 3-4 days**

#### 3.1 Implement Missing Agent Methods
**Effort: 6 hours | Impact: Enables advanced features**

```python
# File: backend/app/services/macro_service.py
async def compute_zscores(self, indicators, window_days=252):
    """Compute z-scores for indicators"""
    # Implementation needed
    
# File: backend/app/agents/reports_agent.py
async def reports_render_pdf(self, data):
    """Generate PDF report"""
    # Implementation needed
```
**Features Enabled:**
- PDF export functionality
- Advanced macro analysis

---

#### 3.2 Complete News Integration
**Effort: 4 hours | Impact: Enables news features**
```python
# File: backend/app/agents/data_harvester.py
async def news_compute_portfolio_impact(self, news_items, positions):
    """Calculate news impact on portfolio"""
    # Match news to positions
    # Calculate sentiment impact
    # Return impact scores
```
**Patterns Fixed:**
- news_impact_analysis ✓

---

### Priority 4: Low Impact, High Effort
**Timeline: 1 week+**

#### 4.1 Full Optimizer Implementation
- Complete optimizer agent capabilities
- Implement constraint solver
- Add backtesting framework

#### 4.2 Advanced Charting
- Interactive scenario waterfall charts
- Real-time risk surface visualization
- Factor exposure heat maps

---

## Implementation Roadmap

### Day 1 (2 hours)
✅ Morning:
- [ ] Register charts.scenario_deltas capability (30 min)
- [ ] Add default inputs for policy_rebalance (30 min)
- [ ] Add default inputs for portfolio_macro_overview (30 min)
- [ ] Test these 3 patterns (30 min)

**Result: 3 patterns working (25% → 42%)**

### Day 2 (4 hours)
✅ Fix State Management:
- [ ] Implement dual state storage (2 hours)
- [ ] Add default value application (1 hour)
- [ ] Test all affected patterns (1 hour)

**Result: 8 patterns working (42% → 67%)**

### Day 3 (4 hours)
✅ Complete Integration:
- [ ] Fix UUID/ticker mismatch (2 hours)
- [ ] Implement missing capabilities (2 hours)

**Result: 12 patterns working (67% → 100%)**

### Day 4-5
✅ Polish & Testing:
- [ ] Add error handling
- [ ] Implement fallbacks
- [ ] Create integration tests
- [ ] Documentation

---

## Cost-Benefit Analysis

### Quick Wins (Day 1)
**Cost**: 2 developer hours
**Benefit**: 
- 25% more patterns working
- Scenarios feature unlocked
- Optimization feature unlocked
**ROI**: Very High

### Core Fixes (Day 2-3)
**Cost**: 8 developer hours
**Benefit**:
- 100% patterns working
- Full feature set available
- Professional UX
**ROI**: High

### Polish (Day 4-5)
**Cost**: 16 developer hours
**Benefit**:
- Better error handling
- Higher reliability
- Easier maintenance
**ROI**: Medium

---

## Testing Checklist

### After Each Fix
```bash
# Quick test script
curl -X POST http://localhost:5000/api/patterns/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern": "PATTERN_NAME", "inputs": {...}}'
```

### Pattern Test Matrix
| Pattern | Pre-Fix | Post-Day1 | Post-Day2 | Post-Day3 |
|---------|---------|-----------|-----------|-----------|
| portfolio_overview | ✅ | ✅ | ✅ | ✅ |
| macro_cycles_overview | ✅ | ✅ | ✅ | ✅ |
| portfolio_scenario_analysis | ❌ | ✅ | ✅ | ✅ |
| policy_rebalance | ❌ | ✅ | ✅ | ✅ |
| buffett_checklist | ❌ | ❌ | ✅ | ✅ |
| news_impact_analysis | ❌ | ❌ | ✅ | ✅ |
| holding_deep_dive | ❌ | ❌ | ❌ | ✅ |
| export_portfolio_report | ❌ | ❌ | ✅ | ✅ |
| Others | ❌ | ❌ | ✅ | ✅ |

---

## Success Metrics

### Immediate (Day 1)
- [ ] Scenarios tab shows data
- [ ] Optimization tab shows trades
- [ ] No "capability not found" errors

### Short-term (Day 3)
- [ ] All UI tabs functional
- [ ] Pattern success rate: 100%
- [ ] Average response < 2s

### Long-term (Week 2)
- [ ] Error rate < 0.1%
- [ ] User satisfaction > 90%
- [ ] Zero critical bugs

---

## Risk Mitigation

### If Quick Wins Don't Work
1. Check agent registration in __init__.py
2. Verify capability method signatures
3. Check UI is sending correct data

### If State Management Fix Breaks
1. Revert pattern orchestrator changes
2. Test with single pattern first
3. Add extensive logging

### If UUID Fix Causes Issues
1. Keep both ticker and UUID support
2. Add fallback logic
3. Create mapping table

---

## One-Line Fixes Worth Trying First

```python
# Fix 1: ChartsAgent capability (1 line)
return ["charts.macro_overview", "charts.scenario_deltas"]  # Add second item

# Fix 2: UI policies default (1 line)
policies: policies || [],  // Add || []

# Fix 3: State storage (2 lines)
state['state'] = state.get('state', {})
state['state'][as_name] = result  # Store in state namespace
```

## Conclusion
Start with Priority 1 fixes (Quick Wins) to get immediate value. These require minimal effort but unlock major features. Then systematically work through Priority 2 (Core Fixes) to achieve full functionality. Priority 3 and 4 can be deferred based on user needs and available resources.