# Phase 2B Standardization - Quick Reference Guide

## Current State Matrix

### Agent Capabilities Returning Lists

```
FINANCIAL ANALYST (7 list-returning capabilities)
├── ledger.positions                      ✅ {positions: [...]}
├── pricing.apply_pack                   ✅ {positions: [...]}
├── get_transaction_history              ✅ {transactions: [...]}
├── compute_position_return              ⚠️  {daily_returns: [...], ...metrics}
├── portfolio.sector_allocation           ❌ {Tech: 30, Finance: 20, ...} FLATTENED!
├── portfolio.historical_nav             ⚠️  {data: [...], labels: [...]}
└── charts.overview                      ✅ {charts: [...]}

MACRO HOUND (7 list-returning capabilities)
├── macro.run_scenario                   ✅ {positions: [...], winners: [...], losers: [...]}
├── macro.compute_dar                    ✅ {scenario_distribution: [...]}
├── macro.get_regime_history             ✅ {history: [...]}
├── scenarios.deleveraging_*             ✅ {positions: [...], winners: [...], losers: [...]}
└── scenarios.macro_aware_rank           ⚠️  {scenarios: [...], most_probable: [...], hedging_priorities: [...]}

DATA HARVESTER (5 list-returning capabilities)
├── provider.fetch_fundamentals          ⚠️  {income_statement: [...], balance_sheet: [...], cash_flow: [...]}
├── provider.fetch_news                  ✅ {articles: [...]}
├── provider.fetch_macro                 ✅ {observations: [...]}
├── news.search                          ⚠️  {news_items: [...], entities_searched: [...]}
└── news.compute_portfolio_impact        ⚠️  {news_with_impact: [...], entity_mentions: [...]}

RATINGS AGENT (1 list-returning capability)
└── ratings.aggregate (portfolio mode)   ✅ {positions: [...], portfolio_avg_rating, portfolio_avg_grade}

OPTIMIZER AGENT (3 list-returning capabilities)
├── optimizer.propose_trades             ✅ {trades: [...]}
├── optimizer.suggest_hedges             ✅ {hedges: [...]}
└── optimizer.suggest_deleveraging_hedges ❌ {recommendations: [...]} NAME INCONSISTENT!

CHARTS AGENT (2 list-returning capabilities)
├── charts.macro_overview                ⚠️  {regime_card: {data: [...]}, ...}
└── charts.scenario_deltas               ✅ {position_deltas: [...]}

REPORTS AGENT (1 list-returning capability)
└── reports.render_pdf                   ✅ {attributions: [...]}

ALERTS AGENT (1 list-returning capability)
└── alerts.suggest_presets               ✅ {suggestions: [...]}

Legend:
✅ Correct pattern ({semantic_key: [...]})
⚠️  Mixed or multiple arrays
❌ Non-standard pattern
```

---

## Inconsistencies at a Glance

### 1. KEY NAMING CONFLICTS

| Array Type | Current Keys | Should Be |
|---|---|---|
| News articles | `articles`, `news_items`, `news_with_impact` | `articles` |
| Hedges | `hedges`, `recommendations` | `hedges` |
| Positions | `positions` | `positions` ✅ |
| Trades | `trades` | `trades` ✅ |
| Suggestions | `suggestions` | `suggestions` ✅ |

### 2. MULTI-ARRAY CAPABILITIES (Unclear Priority)

```
provider.fetch_fundamentals:
  {income_statement: [...], balance_sheet: [...], cash_flow: [...]}
  → Which is "primary"? No metadata, no clear winner

news.compute_portfolio_impact:
  {news_with_impact: [...], entity_mentions: [...]}
  → Are both equally important? How do patterns access?

scenarios.macro_aware_rank:
  {scenarios: [...], most_probable: [...], hedging_priorities: [...]}
  → most_probable is pre-filtered - why separate keys?
```

### 3. FLATTENED vs NESTED

```
portfolio.sector_allocation (FLATTENED - PROBLEM):
  {Tech: 30, Finance: 20, Pharma: 15, total_sectors: 3, total_value: 1000000}
  Problem: Can't distinguish data from metadata

portfolio.historical_nav (MIXED - PROBLEM):
  {data: [...], labels: [...], values: [...]}
  Problem: Multiple arrays with unclear purpose
```

---

## Pattern Template Issues

### portfolio_overview.json
```json
Line 74:  "positions": "{{positions.positions}}"         ✅ Correct
Line 100: "valued_positions": "{{valued_positions.positions}}"  ⚠️ Double nesting?
Line 179: "data": "{{valued_positions.positions}}"        ✅ Using sector data as positions?
```

### policy_rebalance.json
```json
Line 145: "data": "{{rebalance_result.trades}}"           ✅ Correct
```

### holding_deep_dive.json
```json
Line 371: "data": "{{transactions}}"                      ❌ Agent returns {transactions: [...], count}
          Expected: "{{transactions.transactions}}"
```

---

## Phase 2B Three-Step Plan

### Step 1: ADD "DATA" KEY ALONGSIDE SEMANTIC KEYS (Non-Breaking)
```python
# Current:
return {
    "positions": [...],
    "total_positions": 10,
    "_metadata": {...}
}

# Phase 2B.1:
return {
    "data": [...],                    # NEW: Generic data key
    "positions": [...],               # KEEP: For backward compatibility
    "total_positions": 10,
    "_metadata": {...}
}
```

**Benefits:**
- 100% backward compatible
- Templates can gradually migrate
- Clear separation of data from metadata

**Affected Capabilities:** All 27 list-returning capabilities

### Step 2: UPDATE INCONSISTENT KEY NAMES (With Dual Keys)
```python
# Current:
return {
    "recommendations": [...],
    "_metadata": {...}
}

# Phase 2B.1:
return {
    "data": [...],                    # NEW: Standard key
    "hedges": [...],                  # NEW: Standard name
    "recommendations": [...],         # KEEP: Deprecated, for backward compat
    "_metadata": {...}
}
```

**Affected Capabilities:**
- optimizer.suggest_deleveraging_hedges (recommendations → hedges)
- news.search (news_items → articles)
- news.compute_portfolio_impact (consistency)

### Step 3: CLEAN UP FLATTENED STRUCTURES (With New Keys)
```python
# Current (portfolio.sector_allocation):
return {
    "Tech": 30,
    "Finance": 20,
    "total_sectors": 3,
    "_metadata": {...}
}

# Phase 2B.1:
return {
    "data": [
        {"sector": "Tech", "value": 30},
        {"sector": "Finance", "value": 20}
    ],
    "sector_allocation": {...},     # Keep for backward compat
    "total_sectors": 3,
    "_metadata": {...}
}
```

**Affected Capabilities:**
- portfolio.sector_allocation (flattened → nested array)
- portfolio.historical_nav (multiple arrays → single array)

---

## Implementation Roadmap

### Week 1: Analysis & Planning
- [x] Document all inconsistencies (THIS REPORT)
- [ ] Get team consensus on standardization
- [ ] Create detailed implementation plan per agent
- [ ] Set up test cases for each pattern

### Week 2: Core Changes (Least Impact First)
- [ ] FinancialAnalyst: Add "data" keys to all capabilities
- [ ] MacroHound: Add "data" keys to all capabilities
- [ ] DataHarvester: Add "data" keys to all capabilities
- [ ] RatingsAgent: Add "data" key
- [ ] Run regression tests on all patterns

### Week 3: Naming Standardization
- [ ] OptimizerAgent: suggestions_deleveraging_hedges (add hedges key)
- [ ] DataHarvester: news.search (add articles alias)
- [ ] AlertsAgent: validation and consistency check
- [ ] Run integration tests

### Week 4: Structure Fixes
- [ ] FinancialAnalyst: portfolio.sector_allocation (flatten → nest)
- [ ] FinancialAnalyst: portfolio.historical_nav (simplify)
- [ ] MacroHound: scenarios.macro_aware_rank (clarify arrays)
- [ ] DataHarvester: provider.fetch_fundamentals (document priority)
- [ ] Full regression test suite

### Week 5: Template Updates
- [ ] Update all pattern JSON files for "data" key usage
- [ ] Fix holding_deep_dive.json line 371
- [ ] Validate all template references
- [ ] Update documentation

---

## Files to Modify (Priority Order)

### HIGH PRIORITY (Core agent changes)
1. `/backend/app/agents/financial_analyst.py` - 7 capabilities
2. `/backend/app/agents/macro_hound.py` - 7 capabilities
3. `/backend/app/agents/data_harvester.py` - 5 capabilities
4. `/backend/app/agents/optimizer_agent.py` - 3 capabilities

### MEDIUM PRIORITY (Naming fixes)
5. `/backend/app/agents/optimizer_agent.py` - suggest_deleveraging_hedges
6. `/backend/app/agents/alerts_agent.py` - 1 capability

### PATTERN TEMPLATES
7. `/backend/patterns/portfolio_overview.json`
8. `/backend/patterns/policy_rebalance.json`
9. `/backend/patterns/holding_deep_dive.json`
10. All other pattern JSON files (audit)

---

## Testing Strategy

### Unit Tests (Per Capability)
```python
def test_ledger_positions_returns_data_key():
    result = await agent.ledger_positions(ctx, state)
    assert "data" in result
    assert isinstance(result["data"], list)
    assert "positions" in result  # Backward compat

def test_pricing_apply_pack_returns_data_key():
    result = await agent.pricing_apply_pack(ctx, state)
    assert "data" in result
    assert "total_value" in result
    assert result["data"] == result["positions"]  # Backward compat
```

### Integration Tests (Per Pattern)
```python
def test_portfolio_overview_pattern():
    # Execute full pattern
    # Verify all data keys are accessible
    # Verify backward compat with old key names
    pass

def test_policy_rebalance_pattern():
    # Execute full pattern
    # Verify trades array is accessible
    # Verify impact analysis still works
    pass
```

### Regression Tests (Full Suite)
- All 27 patterns execute without error
- All template references resolve
- All array data is accessible
- No data loss in conversion

---

## Estimated Effort

- Analysis: 2 hours ✅ DONE
- Implementation: 30-40 hours
  - Agent code changes: 15-20 hours
  - Pattern updates: 10-15 hours
  - Testing: 5-10 hours
- Documentation: 5 hours
- Review & refinement: 5 hours

**Total: 45-55 hours (1-1.5 weeks with standard dev)</**

---

## Risk Mitigation

### Risk 1: Breaking Existing Templates
**Mitigation:** Keep semantic keys alongside new "data" key
- Dual-key approach: No code breaks
- Gradual migration path
- Can revert individual capabilities if needed

### Risk 2: Inconsistent Implementation
**Mitigation:** Create base class helper method
```python
class BaseAgent:
    def _wrap_list_data(self, data: List, semantic_key: str, **metadata):
        return {
            "data": data,                    # Standard key
            semantic_key: data,              # Backward compat
            **metadata
        }
```

### Risk 3: Pattern Engine Compatibility
**Mitigation:** Validate pattern engine can access both keys
- Test `{{result.data}}` and `{{result.positions}}`
- Ensure state merging works correctly
- May need pattern engine update for template validation

---

## Success Criteria

1. All 27 list-returning capabilities have "data" key
2. All inconsistent key names have dual keys (semantic + semantic_correct)
3. All flattened structures are converted to nested arrays
4. All pattern templates use "data" key (or semantic key with dual keys)
5. Zero breaking changes to existing pattern execution
6. Full test coverage (unit + integration + regression)
7. Documentation updated with new standard

---

## Questions for Team

1. **Naming Decision:** Should we use "data" or more semantic names?
   - Option A: {data: [...], positions: [...]} (current proposal)
   - Option B: {positions: [...], _data_key: "positions"} (metadata-based)
   - Option C: {position_data: [...]} (semantic + clear)

2. **Multi-Array Priority:** For capabilities like `provider.fetch_fundamentals`, should we:
   - Option A: Add "data" as pointer to primary array (which one?)
   - Option B: Keep all three separate with no "data" key
   - Option C: Create sub-object {financial_statements: {income_statement: [...], ...}}

3. **Timeline:** Can we do Phase 2B in 1-2 weeks or should we spread it?

4. **Pattern Engine:** Should we enhance pattern engine to validate array access?
   - Would catch template issues before execution
   - Requires pattern engine code review/update

---

## Next Steps

1. Review this analysis with team
2. Get approval on three-step implementation plan
3. Create GitHub issues for each agent (15+ PRs)
4. Start Week 1: Core agent changes
5. Weekly retrospectives on progress

---

**Report Generated:** 2025-11-03  
**Analysis Complete:** 100% of agent capabilities reviewed  
**Status:** Ready for Phase 2B Implementation
