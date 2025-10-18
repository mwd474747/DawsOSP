# Known Pattern Issues

**Version**: 1.0  
**Date**: October 17, 2025  
**Status**: Documentation Complete - Fixes Pending  
**Total Patterns**: 50 (all operational)  
**Patterns with Issues**: 40+ (documented below)

---

## Overview

This document inventories known issues in DawsOS patterns identified through comprehensive analysis on October 17, 2025. All patterns are operational but have technical debt that should be addressed to improve robustness and maintainability.

**Issue Categories**:
1. Template field fragility (34 patterns)
2. Capability misuse (8-10 patterns)
3. Hybrid routing (20+ patterns)
4. Missing capabilities (2 patterns)
5. Template duplication (34 patterns)

---

## Priority 1: High-Risk Template Fragility

These patterns reference nested fields that may render as literal strings if agent response structure changes.

### buffett_checklist.json
**Location**: `dawsos/patterns/analysis/buffett_checklist.json`

**Issues**:
- Template references: `{step_3.score}`, `{step_3.rating}`, `{step_3.investment_thesis}`
- Risk: If step_3 doesn't return exact structure, fields render as `{step_3.score}` strings
- Capability misuse: Uses `can_fetch_economic_data` to load `buffett_checklist.json` (should use `enriched_lookup`)

**Fix**:
```json
{
  "steps": [
    {
      "action": "enriched_lookup",
      "params": {"knowledge_file": "buffett_checklist.json"},
      "save_as": "framework"
    }
  ],
  "response_template": "{final_analysis}"
}
```

---

### moat_analyzer.json
**Location**: `dawsos/patterns/analysis/moat_analyzer.json`

**Issues**:
- Template references: `{moat_assessment.score}`, `{moat_assessment.competitive_advantages}`
- Capability misuse: Uses `can_fetch_stock_quotes` or `can_fetch_economic_data` for knowledge loading
- Should use `enriched_lookup` action instead

**Fix**: Replace capability-based knowledge loading with `enriched_lookup`

---

### deep_dive.json
**Location**: `dawsos/patterns/workflows/deep_dive.json`

**Issues**:
- Multiple nested field references: `{step_1.fundamentals}`, `{step_2.valuation}`, `{step_3.risks}`
- Template fragility: Requires exact response structure from 3+ steps
- High risk of partial template failures

**Fix**: Use top-level variables only: `{step_1}`, `{step_2}`, `{step_3}`

---

### fundamental_analysis.json
**Location**: `dawsos/patterns/analysis/fundamental_analysis.json`

**Issues**:
- Template references: `{analysis.financial_health}`, `{analysis.growth_metrics}`
- Capability misuse: Uses `can_fetch_fundamentals` to load framework files
- Should separate live data fetch from knowledge loading

**Fix**:
```json
{
  "steps": [
    {
      "action": "enriched_lookup",
      "params": {"knowledge_file": "financial_formulas.json"},
      "save_as": "formulas"
    },
    {
      "action": "execute_by_capability",
      "params": {
        "capability": "can_fetch_fundamentals",
        "context": {"symbol": "{SYMBOL}"}
      },
      "save_as": "live_data"
    }
  ]
}
```

---

### sector_rotation.json
**Location**: `dawsos/patterns/analysis/sector_rotation.json`

**Issues**:
- Nested fields: `{rotation_analysis.recommended_sectors}`, `{rotation_analysis.exit_sectors}`
- Template duplication: Has both `template` and `response_template`

**Fix**: Remove one template field, use top-level vars

---

### portfolio_review.json
**Location**: `dawsos/patterns/workflows/portfolio_review.json`

**Issues**:
- Multiple nested references: `{holdings_analysis.concentration}`, `{risk_assessment.correlation_matrix}`
- Fragile multi-step template
- Hybrid routing: Mixes capability calls with `"agent": "claude"`

**Fix**: Use consistent capability routing, simplify template

---

### market_regime.json
**Location**: `dawsos/patterns/queries/market_regime.json`

**Issues**:
- Nested fields: `{regime_detection.current_regime}`, `{regime_detection.indicators}`
- Capability misuse: Uses API capability for knowledge loading

**Fix**: Use `enriched_lookup` for `economic_cycles.json`

---

### dcf_valuation.json
**Location**: `dawsos/patterns/analysis/dcf_valuation.json`

**Issues**:
- Template fragility: `{dcf_result.fair_value}`, `{dcf_result.assumptions.growth_rate}`
- Deeply nested field references
- May break if `can_calculate_dcf` response changes

**Fix**: Trust agent to format output, use `{dcf_result}` only

---

### morning_briefing.json
**Location**: `dawsos/patterns/workflows/morning_briefing.json`

**Issues**:
- Multiple nested fields across 4+ steps
- Hybrid routing: Some steps use capability, others use `"agent": "claude"`
- Template duplication

**Fix**: Standardize routing, simplify template

---

### risk_assessment.json
**Location**: `dawsos/patterns/analysis/risk_assessment.json`

**Issues**:
- Nested fields: `{assessment.portfolio_risk}`, `{assessment.concentration_risk}`
- Capability routing inconsistency

**Fix**: Use top-level variables

---

## Priority 2: Capability Misuse

These patterns use API capabilities to load knowledge files, causing unnecessary API calls and slower execution.

### Patterns Affected:
1. **buffett_checklist.json** - Uses `can_fetch_economic_data` for `buffett_checklist.json`
2. **moat_analyzer.json** - Uses `can_fetch_stock_quotes` for framework loading
3. **fundamental_analysis.json** - Uses `can_fetch_fundamentals` for formulas
4. **market_regime.json** - Uses `can_fetch_economic_data` for `economic_cycles.json`
5. **sector_rotation.json** - Uses `can_fetch_stock_quotes` for `sector_performance.json`
6. **dalio_framework.json** - Uses `can_fetch_economic_data` for `dalio_cycles.json`
7. **correlation_analysis.json** - Uses `can_fetch_stock_quotes` for `sector_correlations.json`
8. **yield_curve.json** - Uses `can_fetch_economic_data` for `yield_curve.json` (static file)

**Universal Fix**: Replace with `enriched_lookup` action
```json
{
  "action": "enriched_lookup",
  "params": {"knowledge_file": "KNOWLEDGE_FILE.json"}
}
```

---

## Priority 3: Hybrid Routing Patterns

These patterns mix capability routing with direct agent calls, creating architectural inconsistency.

### Examples:

#### Pattern: company_analysis.json
```json
{
  "steps": [
    {
      "action": "execute_by_capability",
      "params": {"capability": "can_fetch_stock_quotes"}
    },
    {
      "action": "execute_through_registry",
      "params": {
        "agent": "claude",
        "context": {"prompt": "analyze"}
      }
    }
  ]
}
```

**Issue**: Step 1 uses capability routing, Step 2 bypasses it with direct agent call

**Fix**: Use capability for both:
```json
{
  "steps": [
    {
      "action": "execute_by_capability",
      "params": {"capability": "can_fetch_stock_quotes"}
    },
    {
      "action": "execute_by_capability",
      "params": {
        "capability": "can_analyze_text",
        "context": {"text": "{step_1}"}
      }
    }
  ]
}
```

### Patterns with Hybrid Routing (~20 patterns):
- company_analysis.json
- industry_analysis.json
- peer_comparison.json
- trend_analysis.json
- earnings_analysis.json
- dividend_analysis.json
- insider_trading.json
- institutional_holdings.json
- short_interest.json
- options_flow.json
- technical_analysis.json
- support_resistance.json
- volume_analysis.json
- moving_averages.json
- rsi_analysis.json
- macd_analysis.json
- bollinger_bands.json
- fibonacci_retracement.json
- elliott_wave.json
- sentiment_analysis.json

**Universal Fix**: Replace `"agent": "claude"` with appropriate capability

---

## Priority 4: Missing Capabilities

These patterns reference capabilities that are registered but not implemented.

### options_flow.json
**Location**: `dawsos/patterns/analysis/options_flow.json`

**Issue**: 
- Uses `can_fetch_options_flow` - registered in AGENT_CAPABILITIES but no agent implements it
- Uses `can_analyze_options_flow` - same issue
- Pattern will fail at runtime with "capability not found"

**Fix Options**:
1. Implement capabilities in an agent (preferred)
2. Use fallback capability like `can_fetch_stock_quotes` + `can_analyze_text`
3. Remove pattern until capabilities are implemented

---

### unusual_options.json
**Location**: `dawsos/patterns/analysis/unusual_options.json`

**Issue**: Same as options_flow.json - missing capability implementation

**Fix**: Same as above

---

## Priority 5: Template Duplication

34 patterns have both `template` and `response_template` fields. It's unclear which takes precedence.

### Patterns Affected (Partial List):
- buffett_checklist.json
- moat_analyzer.json
- dcf_valuation.json
- sector_rotation.json
- portfolio_review.json
- morning_briefing.json
- fundamental_analysis.json
- technical_analysis.json
- risk_assessment.json
- correlation_analysis.json
- (24 more patterns)

**Fix**: Keep only `response_template`, remove `template`

---

## Priority 6: Variable Resolution Edge Cases

These patterns may fail if user input is ambiguous.

### Patterns Requiring Clear Symbols:
- All stock analysis patterns expecting `{SYMBOL}`
- Company-specific patterns

**Issue**: 
- "analyze meta platforms" may not resolve to META ticker
- "what about apple?" works (company_database lookup)
- "tell me about that tech company" fails

**Fix**: Document expected input in `description` field
```json
{
  "description": "Analyzes XYZ. Expects clear ticker symbol (e.g., 'AAPL') or company name (e.g., 'Apple Inc').",
  "triggers": ["analyze", "evaluation"]
}
```

---

## Silent Failure Edge Cases (No Pattern Changes Needed)

PatternEngine handles these automatically but developers should be aware:

1. **Meta Executor Missing** - System falls back to direct execution
2. **Max Recursion** (5 levels) - Prevents infinite nested pattern loops
3. **Unresolved Variables** - Renders as empty string or literal `{VAR}`
4. **Invalid JSON** - Pattern not loaded, logged
5. **Duplicate Pattern IDs** - Last one loaded wins
6. **Template Variables Not Found** - Renders as `{var}` string
7. **Missing Runtime/Graph** - Operations fail gracefully
8. **Unknown Actions** - Logged as warning
9. **Nested Pattern Not Found** - Error logged, step skipped
10. **Missing Capability** - Error logged, step skipped

---

## Remediation Priority

**Phase 1** (High Priority - Week 1):
1. Fix capability misuse in 8-10 patterns (simple find/replace)
2. Add `enriched_lookup` examples to patterns
3. Test critical patterns: buffett_checklist, moat_analyzer, deep_dive

**Phase 2** (Medium Priority - Week 2):
4. Fix template fragility in top 10 most-used patterns
5. Standardize hybrid routing patterns
6. Remove template duplication

**Phase 3** (Low Priority - Week 3):
7. Implement missing capabilities or remove patterns
8. Add variable resolution documentation to all patterns
9. Comprehensive testing of all 50 patterns

---

## Pattern-by-Pattern Inventory

### Analysis Patterns (11 total)

| Pattern | Template Fragility | Capability Misuse | Hybrid Routing | Notes |
|---------|-------------------|-------------------|----------------|-------|
| buffett_checklist.json | ✓ | ✓ | ✗ | High priority |
| moat_analyzer.json | ✓ | ✓ | ✗ | High priority |
| dcf_valuation.json | ✓ | ✗ | ✗ | Template only |
| fundamental_analysis.json | ✓ | ✓ | ✓ | All issues |
| sector_rotation.json | ✓ | ✓ | ✗ | Multiple issues |
| risk_assessment.json | ✓ | ✗ | ✓ | Hybrid routing |
| correlation_analysis.json | ✓ | ✓ | ✗ | Capability misuse |
| portfolio_optimization.json | ✓ | ✗ | ✓ | Template + routing |
| options_flow.json | ✗ | ✓ | ✗ | Missing capability |
| unusual_options.json | ✗ | ✓ | ✗ | Missing capability |
| market_regime.json | ✓ | ✓ | ✗ | Multiple issues |

### Workflow Patterns (4 total)

| Pattern | Template Fragility | Capability Misuse | Hybrid Routing | Notes |
|---------|-------------------|-------------------|----------------|-------|
| deep_dive.json | ✓ | ✗ | ✓ | High complexity |
| portfolio_review.json | ✓ | ✗ | ✓ | Multiple steps |
| morning_briefing.json | ✓ | ✓ | ✓ | All issues |
| investment_thesis.json | ✓ | ✗ | ✓ | Template + routing |

### Query Patterns (6 total)

| Pattern | Template Fragility | Capability Misuse | Hybrid Routing | Notes |
|---------|-------------------|-------------------|----------------|-------|
| sector_performance.json | ✓ | ✓ | ✗ | Capability misuse |
| company_lookup.json | ✗ | ✗ | ✓ | Routing only |
| earnings_calendar.json | ✗ | ✗ | ✓ | Routing only |
| dividend_calendar.json | ✗ | ✗ | ✓ | Routing only |
| economic_calendar.json | ✗ | ✓ | ✗ | Capability misuse |
| analyst_ratings.json | ✓ | ✗ | ✓ | Template + routing |

### UI Patterns (6 total)

| Pattern | Template Fragility | Capability Misuse | Hybrid Routing | Notes |
|---------|-------------------|-------------------|----------------|-------|
| update_dashboard.json | ✗ | ✗ | ✗ | Clean |
| show_alert.json | ✗ | ✗ | ✗ | Clean |
| display_chart.json | ✗ | ✗ | ✗ | Clean |
| update_watchlist.json | ✗ | ✗ | ✗ | Clean |
| show_confidence.json | ✗ | ✗ | ✗ | Clean |
| render_table.json | ✗ | ✗ | ✗ | Clean |

### Governance Patterns (6 total)

| Pattern | Template Fragility | Capability Misuse | Hybrid Routing | Notes |
|---------|-------------------|-------------------|----------------|-------|
| data_quality_check.json | ✗ | ✗ | ✗ | Clean |
| compliance_audit.json | ✓ | ✗ | ✗ | Template only |
| policy_validation.json | ✗ | ✗ | ✗ | Clean |
| lineage_tracking.json | ✗ | ✗ | ✗ | Clean |
| access_control.json | ✗ | ✗ | ✗ | Clean |
| audit_log.json | ✗ | ✗ | ✗ | Clean |

### System/Meta Patterns (5 total)

| Pattern | Template Fragility | Capability Misuse | Hybrid Routing | Notes |
|---------|-------------------|-------------------|----------------|-------|
| meta_executor.json | ✗ | ✗ | ✗ | Core - clean |
| architecture_validator.json | ✗ | ✗ | ✗ | Clean |
| legacy_migrator.json | ✗ | ✗ | ✗ | Clean |
| pattern_validator.json | ✗ | ✗ | ✗ | Clean |
| capability_mapper.json | ✗ | ✗ | ✗ | Clean |

### Additional Patterns (12+ more)

All other patterns follow similar issues - primarily template fragility and hybrid routing.

---

## Testing Recommendations

**Before Fixing**:
1. Create snapshot of current pattern outputs
2. Document expected vs actual behavior
3. Identify most-used patterns for priority testing

**After Fixing**:
1. Regression test all 50 patterns
2. Compare outputs with snapshots
3. Verify no breaking changes
4. Update pattern version numbers

---

## Reference Documentation

- **Pattern Authoring Guide**: [PATTERN_AUTHORING_GUIDE.md](PATTERN_AUTHORING_GUIDE.md)
- **Capability Reference**: [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Architecture**: [.claude/trinity_architect.md](.claude/trinity_architect.md)

---

**Last Updated**: October 17, 2025  
**Next Review**: After Phase 1 remediation  
**Maintained By**: DawsOS Architecture Team
