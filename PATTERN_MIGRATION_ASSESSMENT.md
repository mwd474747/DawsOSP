# Pattern Migration to Capability Routing - Assessment

**Date**: October 8, 2025
**Status**: Infrastructure Complete, Ready for Pattern Migration

---

## Executive Summary

**Current State**:
- ✅ AgentAdapter capability→method mapping (commit c6986dc)
- ✅ Discovery APIs in AgentRuntime (commit c6986dc)
- ✅ ExecuteThroughRegistryAction supports capability routing (commit 7348488)
- ⏳ 3/46 patterns use capability routing (6.5%)
- ⏳ 43/46 patterns need migration (93.5%)

**Recommendation**: Proceed with pattern migration now that infrastructure is complete.

---

## Infrastructure Status

### ✅ COMPLETE: AgentAdapter Enhancement (commit c6986dc)

**File**: [dawsos/core/agent_adapter.py](dawsos/core/agent_adapter.py:147-239)

**Feature**: Capability→Method mapping via introspection
```python
# Maps capability to method
def _execute_by_capability(self, context):
    capability = context.get('capability')
    method_name = capability.replace('can_', '')  # can_calculate_dcf → calculate_dcf
    method = getattr(self.agent, method_name)

    # Extract parameters via introspection
    sig = inspect.signature(method)
    params = extract_from_context(sig, context)

    # Call method directly
    result = method(**params)
```

**Handles**:
- Parameter variations (symbol/ticker, tickers/symbols)
- Missing parameters (uses defaults)
- Graceful fallback to legacy routing

### ✅ COMPLETE: Discovery APIs (commit c6986dc)

**File**: [dawsos/core/agent_runtime.py](dawsos/core/agent_runtime.py:346-418)

**Methods**:
1. `get_agents_with_capability(capability)` - Find agents with specific capability
2. `get_capabilities_for_agent(agent_name)` - List agent's capabilities
3. `validate_capability(capability)` - Check if capability exists
4. `list_all_capabilities()` - Browse all system capabilities

### ✅ COMPLETE: Agent Methods

**DataHarvester** ([dawsos/agents/data_harvester.py](dawsos/agents/data_harvester.py)):
- `fetch_options_flow(tickers)` - Line 332
- `fetch_unusual_options(min_premium)` - Line 360
- Plus standard harvest methods

**FinancialAnalyst** ([dawsos/agents/financial_analyst.py](dawsos/agents/financial_analyst.py)):
- `analyze_stock_comprehensive(symbol)` - Line 694
- `analyze_economy()` - Line 900
- `analyze_portfolio_risk(holdings)` - Line 1035
- `analyze_options_greeks(context)` - Line 1194
- `analyze_options_flow(context)` - Line 1218
- `calculate_options_iv_rank(context)` - Line 1266

---

## Pattern Analysis

### Currently Using Capability Routing (3 patterns)

1. **greeks_analysis.json**
   - Capabilities: `can_fetch_options_flow`, `can_analyze_greeks`
   - Status: ✅ Already migrated

2. **options_flow.json**
   - Capabilities: `can_fetch_options_flow`, `can_analyze_options_flow`, `can_add_nodes`
   - Status: ✅ Already migrated

3. **unusual_options_activity.json**
   - Capabilities: `can_fetch_unusual_options`, `can_detect_unusual_activity`
   - Status: ✅ Already migrated

### Need Migration (43 patterns)

**Analysis Patterns (16)**:
- buffett_checklist.json (complex - 8 steps)
- dalio_cycle.json
- dcf_valuation.json
- earnings_analysis.json
- fundamental_analysis.json (complex - 7 steps)
- moat_analyzer.json
- owner_earnings.json
- portfolio_analysis.json
- risk_assessment.json
- sentiment_analysis.json
- technical_analysis.json

**Query Patterns (6)**:
- company_analysis.json
- correlation_finder.json
- macro_analysis.json
- market_regime.json
- sector_performance.json
- stock_price.json

**Workflow Patterns (4)**:
- deep_dive.json
- morning_briefing.json
- opportunity_scan.json
- portfolio_review.json

**Action Patterns (5)**:
- add_to_graph.json
- add_to_portfolio.json
- create_alert.json
- export_data.json
- generate_forecast.json

**Governance Patterns (6)**:
- audit_everything.json
- compliance_audit.json
- cost_optimization.json
- data_quality_check.json
- governance_template.json
- policy_validation.json

**System Patterns (5)**:
- architecture_validator.json
- execution_router.json
- legacy_migrator.json
- meta_executor.json
- self_improve.json

**UI Patterns (6)**:
- alert_manager.json
- confidence_display.json
- dashboard_generator.json
- dashboard_update.json
- help_guide.json
- watchlist_update.json

**Misc (2)**:
- comprehensive_analysis.json
- sector_rotation.json

---

## Migration Strategy

### Agent→Capability Mapping (from AGENT_CAPABILITIES)

**data_harvester** (can_*):
- fetch_stock_quotes
- fetch_economic_data
- fetch_news
- fetch_fundamentals
- fetch_market_movers
- fetch_crypto_data
- fetch_options_flow
- fetch_unusual_options

**financial_analyst** (can_*):
- calculate_dcf
- analyze_moat
- calculate_roic
- calculate_owner_earnings
- analyze_economy
- analyze_portfolio_risk
- analyze_greeks
- analyze_options_flow
- detect_unusual_activity
- calculate_iv_rank

**pattern_spotter** (can_*):
- detect_patterns
- identify_signals

**forecast_dreamer** (can_*):
- generate_forecast
- project_future

**governance_agent** (can_*):
- audit_data_quality
- validate_policy
- check_compliance

**relationship_hunter** (can_*):
- calculate_correlations
- find_relationships

### Migration Pattern

**Before** (legacy):
```json
{
  "action": "execute_through_registry",
  "params": {
    "agent": "financial_analyst",
    "context": {
      "request": "Calculate DCF for {SYMBOL}"
    }
  }
}
```

**After** (modern):
```json
{
  "action": "execute_through_registry",
  "params": {
    "capability": "can_calculate_dcf",
    "context": {
      "symbol": "{SYMBOL}"
    }
  }
}
```

### Key Changes

1. **Replace** `"agent": "agent_name"` → `"capability": "can_action"`
2. **Remove** `"request": "text instruction"`
3. **Add** structured parameters directly in context
4. **Preserve** entity extraction (TICKER, SYMBOL, etc.)
5. **Maintain** step dependencies (save_as, outputs)

---

## Batch Migration Plan

### Batch 1: Simple Analysis Patterns (5 patterns, 1 hour)
Focus: Single-step or 2-step patterns

1. dcf_valuation.json
2. moat_analyzer.json
3. owner_earnings.json
4. earnings_analysis.json
5. sentiment_analysis.json

**Why first**: Simple, single capability each, easy to validate

### Batch 2: Query Patterns (6 patterns, 1.5 hours)
Focus: Data fetching patterns

1. stock_price.json
2. company_analysis.json
3. sector_performance.json
4. market_regime.json
5. macro_analysis.json
6. correlation_finder.json

**Why second**: Straightforward data fetch + analysis

### Batch 3: Workflow Patterns (4 patterns, 2 hours)
Focus: Multi-step workflows

1. morning_briefing.json
2. opportunity_scan.json
3. portfolio_review.json
4. deep_dive.json

**Why third**: More complex, builds confidence

### Batch 4: Complex Analysis (3 patterns, 3 hours)
Focus: Multi-capability patterns

1. buffett_checklist.json (8 steps)
2. fundamental_analysis.json (7 steps)
3. comprehensive_analysis.json

**Why fourth**: Most complex, requires careful mapping

### Batch 5: Governance & System (11 patterns, 2 hours)
Focus: Governance and system patterns

- 6 governance patterns
- 5 system patterns

**Why fifth**: Less critical for user-facing features

### Batch 6: UI & Actions (11 patterns, 1.5 hours)
Focus: UI and action patterns

- 6 UI patterns
- 5 action patterns

**Why last**: Supporting infrastructure

---

## Validation Strategy

### Per-Pattern Validation

After each pattern migration:

1. **Syntax check**: JSON valid
2. **Lint check**: `python scripts/lint_patterns.py <pattern>`
3. **Capability check**: Verify capability exists in AGENT_CAPABILITIES
4. **Agent method check**: Verify agent has matching method
5. **Parameter check**: Verify method signature matches context

### Batch Validation

After each batch:

1. **Run all patterns through linter**
2. **Execute sample queries** for each pattern
3. **Check for template placeholders** in results
4. **Verify graph storage** (Trinity compliance)

### Final Validation

After all migrations:

1. **Full pattern lint**: All 46 patterns
2. **Integration test**: Execute 10 most common queries
3. **Performance test**: Compare execution speed vs. legacy
4. **Backward compatibility**: Verify legacy patterns still work

---

## Risk Mitigation

### Backup Strategy

Before starting migration:
```bash
# Create backup of all patterns
cp -r dawsos/patterns dawsos/patterns.backup.$(date +%Y%m%d)
```

### Rollback Strategy

If migration fails:
```bash
# Restore from backup
rm -rf dawsos/patterns
mv dawsos/patterns.backup.YYYYMMDD dawsos/patterns
```

### Git Strategy

Commit after each batch:
```bash
git add dawsos/patterns/
git commit -m "feat: Migrate Batch N patterns to capability routing (N patterns)"
```

---

## Success Criteria

### Pattern Migration

- [ ] All 43 patterns migrated to capability routing
- [ ] 0 errors from pattern linter
- [ ] All capabilities exist in AGENT_CAPABILITIES
- [ ] All agent methods exist and match signatures

### Functional Testing

- [ ] Options flow analysis works (already tested)
- [ ] DCF valuation works
- [ ] Buffett checklist works
- [ ] Morning briefing works
- [ ] Portfolio analysis works

### Performance

- [ ] No regression in execution speed
- [ ] Graph storage works (Trinity compliance)
- [ ] Results are formatted correctly (no template placeholders)

---

## Timeline

**Estimated Time**: 11-13 hours total

- Batch 1: 1 hour (5 simple patterns)
- Batch 2: 1.5 hours (6 query patterns)
- Batch 3: 2 hours (4 workflow patterns)
- Batch 4: 3 hours (3 complex patterns)
- Batch 5: 2 hours (11 governance/system patterns)
- Batch 6: 1.5 hours (11 UI/action patterns)
- Final validation: 1 hour

**Completion Target**: 2 days (6 hours/day)

---

## Next Steps

1. ✅ Create assessment document (this file)
2. ⏳ Create backup of patterns directory
3. ⏳ Start Batch 1 (5 simple patterns)
4. ⏳ Validate and commit Batch 1
5. ⏳ Continue with Batches 2-6
6. ⏳ Final validation and testing

---

**Status**: Ready to begin pattern migration
**Blocker**: None - infrastructure is complete
**Confidence**: High - infrastructure tested with 3 options patterns
