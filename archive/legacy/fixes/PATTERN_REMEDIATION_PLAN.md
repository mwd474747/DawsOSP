# Pattern Remediation Implementation Plan

**Status**: Trinity 2.0 Pattern Infrastructure - Incomplete Migration
**Current Grade**: C+ (75/100)
**Target Grade**: A (95/100)
**Estimated Time**: 6-8 hours (can be parallelized to 3-4 hours)

---

## Executive Summary

Pattern analysis reveals **88 critical anti-patterns** across 48 patterns where patterns claim Trinity 2.0 compatibility but still use legacy agent-based routing instead of capability-based routing. Additionally, 67% of patterns are uncategorized and 79% lack output templates.

**Key Finding**: The automated migration script from earlier successfully migrated 45 patterns to use `capability` routing, but many patterns still have legacy `agent` references that take precedence due to pattern engine's `step.get('params', step.get('parameters', {}))` logic.

---

## Issues Breakdown

### Critical (88 instances - 28 patterns affected)
- **Legacy Agent Routing**: Patterns using `params.agent` instead of `params.capability`
- **Impact**: Claims Trinity 2.0 but bypasses capability-based routing
- **Priority**: P0 - Blocks true Trinity 2.0 completion

### High (16 instances - 11 patterns)
- **Version Inconsistencies**:
  - 3 patterns: version "2.0.0" (should be "2.0")
  - 3 patterns: version "1.0" in system/meta (intentional?)
- **Missing Triggers**: 5 patterns have no trigger phrases
- **Priority**: P1 - Affects discoverability and consistency

### Medium (38 instances - 38 patterns)
- **Missing Templates**: No user-facing output formatting
- **Impact**: Users get raw JSON instead of formatted responses
- **Priority**: P2 - Affects user experience

### Low (40 instances)
- **Uncategorized Patterns**: 32 patterns (67%) not organized into categories
- **Duplicate Triggers**: 8 trigger phrases map to multiple patterns
- **Priority**: P3 - Affects maintainability and organization

---

## Implementation Phases

### Phase 1: Critical - Legacy Agent Routing Fix (2-3 hours)

**Objective**: Convert all 88 legacy `params.agent` calls to capability-based routing

**Affected Patterns** (28 total):
```
sector_rotation.json (1 step)
comprehensive_analysis.json (2 steps)
ui/watchlist_update.json (2 steps)
ui/dashboard_update.json (2 steps)
ui/confidence_display.json (2 steps)
ui/dashboard_generator.json (1 step)
ui/alert_manager.json (4 steps)
ui/help_guide.json (1 step)
analysis/sentiment_analysis.json (1 step)
analysis/risk_assessment.json (2 steps)
analysis/portfolio_analysis.json (2 steps)
analysis/buffett_checklist.json (2 steps)
analysis/dalio_cycle.json (2 steps)
analysis/fundamental_analysis.json (2 steps)
analysis/earnings_analysis.json (1 step)
analysis/technical_analysis.json (1 step)
workflows/deep_dive.json (6 steps)
workflows/morning_briefing.json (4 steps)
workflows/opportunity_scan.json (3 steps)
workflows/portfolio_review.json (3 steps)
queries/company_analysis.json (2 steps)
queries/correlation_finder.json (2 steps)
queries/macro_analysis.json (2 steps)
queries/market_regime.json (2 steps)
queries/sector_performance.json (2 steps)
queries/stock_price.json (1 step)
actions/add_to_portfolio.json (1 step)
actions/generate_forecast.json (2 steps)
```

**Agent → Capability Mapping**:
```python
AGENT_TO_CAPABILITY = {
    'financial_analyst': {
        'dcf': 'can_calculate_dcf',
        'roic': 'can_calculate_roic',
        'moat': 'can_analyze_moat',
        'stock': 'can_analyze_stock',
        'fundamentals': 'can_analyze_fundamentals',
        'greeks': 'can_analyze_greeks',
        'iv_rank': 'can_calculate_iv_rank',
        'unusual': 'can_detect_unusual_activity',
        'options_flow': 'can_analyze_options_flow'
    },
    'data_harvester': {
        'stock': 'can_fetch_stock_quotes',
        'fundamental': 'can_fetch_fundamentals',
        'market': 'can_fetch_market_data',
        'economic': 'can_fetch_economic_data',
        'sentiment': 'can_fetch_sentiment',
        'news': 'can_fetch_news',
        'options': 'can_fetch_options_data'
    },
    'claude': {
        'analyze': 'can_analyze_text',
        'synthesize': 'can_synthesize_insights',
        'orchestrate': 'can_orchestrate_agents'
    },
    'pattern_spotter': 'can_detect_patterns',
    'forecast_dreamer': 'can_generate_forecast',
    'relationship_hunter': 'can_find_relationships',
    'data_digester': 'can_summarize_data',
    'ui_generator': 'can_generate_ui',
    'governance_agent': 'can_enforce_governance',
    'graph_mind': 'can_query_graph',
    'workflow_recorder': 'can_record_workflow',
    'workflow_player': 'can_replay_workflow'
}
```

**Implementation Strategy**:

1. **Automated Script** (80% coverage):
   ```python
   # fix_legacy_routing.py
   # - Read each pattern
   # - For each step with params.agent (exclude 'claude' for orchestration)
   # - Parse context.request or analysis_type to infer capability
   # - Replace params.agent with params.capability
   # - Update params.context to structured parameters
   # - Preserve all other fields (save_as, condition, description)
   ```

2. **Manual Review** (20% - complex patterns):
   - comprehensive_analysis.json (multi-step orchestration)
   - deep_dive.json (6-step workflow)
   - UI patterns with dynamic context

3. **Testing**:
   ```bash
   # After each fix
   python3 scripts/lint_patterns.py
   python3 analyze_patterns.py
   # Expect 0 critical issues
   ```

**Deliverable**: All 88 legacy routing calls converted to capability-based

---

### Phase 2: High Priority - Metadata Fixes (1 hour)

**2.1 Version Normalization**

Fix version inconsistencies:
```json
// BEFORE
{"version": "2.0.0"}  // 3 patterns
{"version": "1.0"}     // 3 patterns (system/meta)

// AFTER
{"version": "2.0"}     // All patterns (or keep meta at 1.0 if intentional)
```

**Affected Patterns**:
- analysis/greeks_analysis.json
- analysis/unusual_options_activity.json
- analysis/options_flow.json
- system/meta/meta_executor.json (keep at 1.0?)
- system/meta/legacy_migrator.json (keep at 1.0?)
- system/meta/execution_router.json (keep at 1.0?)

**2.2 Add Missing Triggers**

Patterns without triggers (5):
```json
// dcf_valuation.json
"triggers": [
  "dcf valuation",
  "discounted cash flow",
  "intrinsic value",
  "fair value calculation"
]

// governance_template.json
"triggers": []  // Intentional - it's a template

// system/meta/* (3 patterns)
"triggers": []  // Intentional - internal use only
```

**Deliverable**:
- All user-facing patterns have 3+ triggers
- Templates/meta patterns explicitly marked with empty triggers + comment

---

### Phase 3: Medium Priority - Output Templates (2-3 hours)

**Objective**: Add formatted output templates to 38 patterns

**Template Strategy**:

1. **Analysis Patterns** (use structured markdown):
   ```json
   "template": "## {pattern_name} Results\n\n**Symbol**: {SYMBOL}\n**Analysis Date**: {timestamp}\n\n### Key Findings\n{analysis_summary}\n\n### Metrics\n{metrics_table}\n\n### Recommendation\n{recommendation}\n\n*Confidence: {confidence_score}%*"
   ```

2. **Query Patterns** (use concise format):
   ```json
   "template": "**{query_type} for {SYMBOL}**\n\n{result_data}\n\n*Source: {data_source} | Updated: {last_updated}*"
   ```

3. **Workflow Patterns** (use step-by-step):
   ```json
   "template": "## {workflow_name} Complete\n\n{#steps}\n### Step {index}: {name}\n{result}\n{/steps}\n\n---\n**Summary**: {summary}"
   ```

4. **UI Patterns** (return UI config JSON):
   ```json
   "template": "{ui_config_json}"  // No markdown, return raw config
   ```

**Affected Patterns** (38):
```
sector_rotation.json
comprehensive_analysis.json
ui/* (6 patterns) - return JSON config
analysis/* (13 patterns)
workflows/* (4 patterns)
queries/* (6 patterns)
actions/* (5 patterns)
governance/* (3 patterns - exclude template)
```

**Implementation**:
- Use specialized agent to generate templates based on pattern purpose
- Follow existing template patterns from working patterns (moat_analyzer, owner_earnings)
- Include confidence scores, timestamps, source attribution

**Deliverable**: All user-facing patterns have markdown templates

---

### Phase 4: Low Priority - Organization & Cleanup (1-2 hours)

**4.1 Categorize 32 Uncategorized Patterns**

Move to proper subdirectories:
```
actions/ (currently 5, add 5 more):
  - add_to_graph.json
  - add_to_portfolio.json
  - create_alert.json
  - export_data.json
  - generate_forecast.json

queries/ (currently 0, add 6):
  - company_analysis.json → queries/
  - correlation_finder.json → queries/
  - macro_analysis.json → queries/
  - market_regime.json → queries/
  - sector_performance.json → queries/
  - stock_price.json → queries/

workflows/ (currently 0, add 4):
  - deep_dive.json → workflows/
  - morning_briefing.json → workflows/
  - opportunity_scan.json → workflows/
  - portfolio_review.json → workflows/

Root patterns (keep 2):
  - sector_rotation.json (composite pattern)
  - comprehensive_analysis.json (meta-pattern)
```

**4.2 Resolve Duplicate Triggers**

8 trigger conflicts:
```
'full analysis' → comprehensive_analysis, deep_dive
  Fix: comprehensive_analysis keeps "full analysis"
       deep_dive uses "deep dive analysis" (more specific)

'risk' → risk_assessment, portfolio_analysis, market_regime
  Fix: Use more specific triggers:
       - "risk assessment" → risk_assessment
       - "portfolio risk" → portfolio_analysis
       - "market risk" → market_regime

'earnings'/'revenue' → earnings_analysis, company_analysis
  Fix: earnings_analysis keeps "earnings"
       company_analysis uses "company fundamentals"
```

**Deliverable**:
- All patterns organized into categories
- No duplicate triggers (189 unique)
- Updated category field in all pattern JSONs

---

### Phase 5: Validation & Testing (1 hour)

**5.1 Automated Validation**
```bash
# Pattern linter
python3 scripts/lint_patterns.py
# Expected: 0 errors, 0 warnings

# Pattern analyzer
python3 analyze_patterns.py
# Expected: 0 critical, 0 high priority issues

# Unit tests
pytest dawsos/tests/validation/test_trinity_smoke.py
pytest dawsos/tests/validation/test_integration.py
```

**5.2 Integration Testing**

Test representative patterns from each category:
```python
# Test capability routing
pattern = engine.find_pattern("calculate dcf for AAPL")
result = engine.execute_pattern(pattern, {"SYMBOL": "AAPL"})
assert "capability" in result['steps'][0]['params']
assert result['formatted_response']  # Has template output

# Test categorization
analysis_patterns = engine.find_patterns_by_category("analysis")
assert len(analysis_patterns) == 13

# Test triggers
pattern = engine.find_pattern("unusual options activity")
assert pattern['id'] == 'unusual_options_activity'
```

**5.3 Documentation Update**

Update affected docs:
- README.md - Pattern count by category
- SYSTEM_STATUS.md - Upgrade to A grade
- .claude/pattern_specialist.md - Trinity 2.0 completion
- CAPABILITY_ROUTING_GUIDE.md - Add pattern examples

**Deliverable**: All tests passing, docs updated, A grade achieved

---

## Execution Strategy

### Sequential Approach (6-8 hours)
```
Phase 1: Legacy routing fixes  → 2-3 hours
Phase 2: Metadata fixes        → 1 hour
Phase 3: Templates             → 2-3 hours
Phase 4: Organization          → 1-2 hours
Phase 5: Validation            → 1 hour
```

### Parallel Approach (3-4 hours with specialized agents)

**Agent Assignments**:

1. **Pattern Specialist Agent** (Phases 1, 2):
   - Fix all 88 legacy routing issues
   - Normalize versions
   - Add missing triggers
   - Time: 2 hours

2. **Knowledge Curator Agent** (Phase 3):
   - Generate 38 output templates
   - Follow existing template patterns
   - Time: 2 hours

3. **Agent Orchestrator** (Phase 4):
   - Reorganize directory structure
   - Update category fields
   - Resolve trigger conflicts
   - Time: 1 hour

4. **Trinity Architect** (Phase 5):
   - Run all validation tests
   - Update documentation
   - Generate completion report
   - Time: 1 hour

**Parallel Timeline**:
```
Hour 1-2: Agents 1, 2, 3 work simultaneously
Hour 3:   Agent 4 validates (requires others complete)
Hour 4:   Final review and commit
```

---

## Success Criteria

### Before
- ❌ 88 legacy agent routing issues
- ❌ 67% patterns uncategorized
- ❌ 79% patterns missing templates
- ❌ Version inconsistencies
- **Grade: C+ (75/100)**

### After
- ✅ 0 legacy routing issues (100% capability-based)
- ✅ 100% patterns categorized
- ✅ 100% user-facing patterns have templates
- ✅ All versions normalized to 2.0
- ✅ All patterns have 3+ triggers
- ✅ 0 duplicate triggers
- **Grade: A (95/100)**

---

## Risk Mitigation

1. **Backup Before Changes**:
   ```bash
   cp -r dawsos/patterns dawsos/patterns.backup.$(date +%Y%m%d_%H%M%S)
   ```

2. **Incremental Testing**:
   - Run linter after each pattern fix
   - Commit frequently with descriptive messages

3. **Backward Compatibility**:
   - Keep agent-based routing working in ExecuteThroughRegistryAction
   - Support both `params` and `parameters` (prefer `params`)
   - Document migration in pattern comments

4. **Rollback Plan**:
   ```bash
   # If issues found
   git diff HEAD~1  # Review changes
   git revert HEAD  # Rollback if needed
   ```

---

## Next Steps

**Immediate Action Required**:

1. Choose execution strategy (sequential vs parallel)
2. Create backup of patterns directory
3. Begin Phase 1 (critical fixes)

**Recommendation**: Use **parallel approach** with specialized agents to complete in 3-4 hours instead of 6-8 hours sequential.

---

**Document Version**: 1.0
**Created**: 2025-10-09
**Status**: Ready for implementation
