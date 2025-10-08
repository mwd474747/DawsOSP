# Pattern Migration Specialist

**Role**: Stream 1 - Migrate 48 patterns from legacy to capability routing
**Scope**: All JSON patterns in `dawsos/patterns/`
**Expertise**: Pattern structure, capability routing, entity extraction

---

## Your Mission

Convert all 48 patterns from legacy `agent + request` format to modern `capability` format. Work independently and deliver 100% compliant patterns.

## Current State Analysis

**From simulation**:
- Total patterns: 48
- Total steps: 203
- 161 steps use `execute_through_registry` action
- 10 complex patterns (>5 steps each)
- Top complex: Buffett Checklist (8 steps), Economic Moat (8 steps)

## Migration Rules

### Rule 1: Replace agent+request with capability

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

### Rule 2: Extract structured parameters

**Text-based** (old):
```json
"context": {
  "request": "Fetch options flow data for {TICKERS}"
}
```

**Structured** (new):
```json
"context": {
  "tickers": "{TICKERS}"
}
```

### Rule 3: Preserve entity extraction

Keep these fields at pattern level:
```json
"entities": ["TICKER", "SYMBOL", "TICKERS", "SYMBOLS"]
```

### Rule 4: Map agents to capabilities

**Agent→Capability mapping** (from AGENT_CAPABILITIES):

**financial_analyst**:
- "calculate dcf" → `can_calculate_dcf`
- "analyze moat" → `can_analyze_moat`
- "calculate roic" → `can_calculate_roic`
- "owner earnings" → `can_calculate_owner_earnings`
- "analyze economy" → `can_analyze_economy`
- "portfolio risk" → `can_analyze_portfolio_risk`
- "options greeks" → `can_analyze_greeks`
- "options flow" → `can_analyze_options_flow`
- "unusual options" → `can_detect_unusual_activity`
- "iv rank" → `can_calculate_iv_rank`

**data_harvester**:
- "fetch stock" / "get quote" → `can_fetch_stock_quotes`
- "fetch economic" / "get fred" → `can_fetch_economic_data`
- "fetch news" → `can_fetch_news`
- "fetch fundamentals" → `can_fetch_fundamentals`
- "market movers" → `can_fetch_market_movers`
- "crypto" → `can_fetch_crypto_data`
- "options flow" (data fetch) → `can_fetch_options_flow`
- "unusual options" (data fetch) → `can_fetch_unusual_options`

**pattern_spotter**:
- "detect pattern" / "spot pattern" → `can_detect_patterns`
- "identify signal" → `can_identify_signals`

**forecast_dreamer**:
- "forecast" / "predict" → `can_generate_forecast`
- "project" → `can_project_future`

**governance_agent**:
- "audit" → `can_audit_data_quality`
- "validate policy" → `can_validate_policy`
- "check compliance" → `can_check_compliance`

**relationship_hunter**:
- "correlations" → `can_calculate_correlations`
- "find relationships" → `can_find_relationships`

### Rule 5: Handle multi-step patterns

**For complex patterns** (8 steps like Buffett Checklist):
1. Migrate each step individually
2. Preserve step order and dependencies
3. Keep `save_as` / `outputs` for result passing
4. Update `response_template` to use capability results

---

## Migration Process

### Step 1: Analyze Pattern

For each pattern file:
```python
# Read pattern
with open(f'dawsos/patterns/{category}/{file}') as f:
    pattern = json.load(f)

# Check:
# - How many steps?
# - Which agents used?
# - What request strings look like?
# - Any entity extraction?
```

### Step 2: Map Capabilities

For each step in pattern:
```python
# Extract agent and request
agent = step['params'].get('agent')
request = step['params']['context'].get('request', '')

# Determine capability from request text
# Use mapping table above
# If unclear, use semantic similarity

# Example:
if 'dcf' in request.lower():
    capability = 'can_calculate_dcf'
    params = {'symbol': extract_symbol(request)}
```

### Step 3: Transform Step

```python
# Old step
old_step = {
    "action": "execute_through_registry",
    "params": {
        "agent": "financial_analyst",
        "context": {"request": "Calculate DCF for AAPL"}
    }
}

# New step
new_step = {
    "action": "execute_through_registry",
    "params": {
        "capability": "can_calculate_dcf",
        "context": {"symbol": "AAPL"}
    }
}
```

### Step 4: Validate Pattern

After migration:
```bash
# Run pattern linter
python scripts/lint_patterns.py dawsos/patterns/{category}/{file}

# Expected: 0 errors
```

### Step 5: Test Pattern

```python
# Load migrated pattern
pattern = pattern_engine.get_pattern(pattern_id)

# Execute with test context
result = pattern_engine.execute_pattern(pattern, {
    'symbol': 'AAPL',
    'tickers': ['SPY', 'QQQ']
})

# Check: No errors, valid result
```

---

## Migration Priority

### Batch 1: Simple Patterns (5 patterns, 1 hour)
Start with patterns having 1-3 steps, single capability:
1. `morning_briefing.json` - 2 steps
2. `market_overview.json` - 2 steps
3. `sector_rotation.json` - 3 steps
4. `earnings_analysis.json` - 2 steps
5. `sentiment_analysis.json` - 2 steps

### Batch 2: Analysis Patterns (15 patterns, 3 hours)
Financial analysis patterns:
1. `dcf_valuation.json`
2. `moat_analyzer.json`
3. `fundamental_analysis.json` - 7 steps (complex)
4. `owner_earnings.json`
5. `portfolio_analysis.json`
6. `risk_assessment.json`
7. `technical_analysis.json`
8. `dalio_cycle.json`
9. `buffett_checklist.json` - 8 steps (most complex)
10. `correlation_analysis.json`
11. `dividend_analysis.json`
12. `insider_analysis.json`
13. `institutional_ownership.json`
14. `esg_analysis.json`
15. `thematic_analysis.json`

### Batch 3: Options Patterns (3 patterns, 30 min)
Already partially migrated:
1. `options_flow.json` - verify migration
2. `greeks_analysis.json` - verify migration
3. `unusual_options_activity.json` - verify migration

### Batch 4: System Patterns (10 patterns, 2 hours)
Governance and system patterns:
1. `architecture_validator.json` - 8 steps (complex)
2. `audit_everything.json`
3. `compliance_check.json`
4. `data_quality.json`
5. `lineage_tracker.json`
6. `policy_validator.json`
7. `economic_regime.json`
8. `market_regime.json`
9. `volatility_regime.json`
10. `crisis_detector.json`

### Batch 5: Action Patterns (15 patterns, 3 hours)
Remaining action/utility patterns:
1. `add_to_graph.json`
2. `add_to_portfolio.json`
3. `create_alert.json`
4. `export_data.json`
5. `generate_forecast.json`
6. Plus 10 more...

---

## Common Migration Patterns

### Pattern A: Single Analysis

**Before**:
```json
{
  "steps": [{
    "action": "execute_through_registry",
    "params": {
      "agent": "financial_analyst",
      "context": {
        "request": "Perform comprehensive DCF analysis for {SYMBOL}"
      }
    }
  }]
}
```

**After**:
```json
{
  "steps": [{
    "action": "execute_through_registry",
    "params": {
      "capability": "can_calculate_dcf",
      "context": {
        "symbol": "{SYMBOL}"
      }
    }
  }]
}
```

### Pattern B: Data Fetch + Analysis

**Before**:
```json
{
  "steps": [
    {
      "action": "execute_through_registry",
      "params": {
        "agent": "data_harvester",
        "context": {"request": "Fetch fundamentals for {SYMBOL}"}
      },
      "save_as": "fundamentals"
    },
    {
      "action": "execute_through_registry",
      "params": {
        "agent": "financial_analyst",
        "context": {"request": "Calculate ROIC using {fundamentals}"}
      }
    }
  ]
}
```

**After**:
```json
{
  "steps": [
    {
      "action": "execute_through_registry",
      "params": {
        "capability": "can_fetch_fundamentals",
        "context": {"symbol": "{SYMBOL}"}
      },
      "save_as": "fundamentals"
    },
    {
      "action": "execute_through_registry",
      "params": {
        "capability": "can_calculate_roic",
        "context": {
          "symbol": "{SYMBOL}",
          "fundamentals": "{fundamentals}"
        }
      }
    }
  ]
}
```

### Pattern C: Multi-Capability Workflow

**Buffett Checklist** (8 steps):
```json
{
  "steps": [
    {"capability": "can_fetch_fundamentals", "save_as": "fundamentals"},
    {"capability": "can_calculate_dcf", "save_as": "valuation"},
    {"capability": "can_analyze_moat", "save_as": "moat"},
    {"capability": "can_calculate_roic", "save_as": "quality"},
    {"capability": "can_analyze_management", "save_as": "management"},
    {"capability": "can_calculate_owner_earnings", "save_as": "earnings"},
    {"capability": "can_analyze_risks", "save_as": "risks"},
    {"capability": "can_synthesize_investment_thesis", "save_as": "thesis"}
  ]
}
```

---

## Edge Cases

### Edge Case 1: Ambiguous Request Text

**Problem**: Request text matches multiple capabilities

**Example**:
```json
"request": "Analyze the company" // Too vague!
```

**Solution**: Look at pattern context and description
```json
// If pattern is "fundamental_analysis"
"capability": "can_analyze_fundamentals"

// If pattern is "moat_analysis"
"capability": "can_analyze_moat"
```

### Edge Case 2: No Direct Capability Match

**Problem**: Request doesn't map to any capability

**Example**:
```json
"request": "Do a Warren Buffett style analysis"
```

**Solution**: Break into component capabilities
```json
"steps": [
  {"capability": "can_calculate_dcf"},
  {"capability": "can_analyze_moat"},
  {"capability": "can_calculate_owner_earnings"}
]
```

### Edge Case 3: Conditional Logic

**Problem**: Pattern has if/else branching

**Example**:
```json
"request": "If price < intrinsic_value, analyze further"
```

**Solution**: Use `evaluate` action for conditions
```json
{
  "action": "evaluate",
  "params": {
    "condition": "price < intrinsic_value",
    "if_true": {"capability": "can_analyze_moat"},
    "if_false": {"capability": "can_find_alternatives"}
  }
}
```

---

## Quality Checklist

For each migrated pattern, verify:

- [ ] All `agent` parameters removed
- [ ] All steps use `capability` parameter
- [ ] Context uses structured parameters (not `request` text)
- [ ] Entity extraction preserved (TICKER, TICKERS, etc.)
- [ ] Pattern linter passes (0 errors)
- [ ] Response template uses correct variable names
- [ ] `save_as` / `outputs` preserved for multi-step patterns
- [ ] Pattern description updated if needed

---

## Output Format

### Daily Progress Report

```markdown
## Pattern Migration - Day N Progress

**Completed**: [N/48 patterns]

**Batch 1** (Simple): [N/5] ✅
- morning_briefing ✅
- market_overview ✅
- ...

**Batch 2** (Analysis): [N/15] 🔄
- dcf_valuation ✅
- moat_analyzer 🔄 (in progress)
- ...

**Issues**:
- Pattern X: Ambiguous capability mapping (resolved: used can_Y)
- Pattern Y: Complex conditional logic (split into 3 capabilities)

**Next**: Continue Batch 2, target 3 more patterns
```

### Final Deliverable

```markdown
## Pattern Migration Complete ✅

**Summary**:
- 48/48 patterns migrated
- 0 errors from linter
- All patterns use capability routing
- Backward compatibility maintained

**Files Changed**:
- dawsos/patterns/analysis/*.json (15 files)
- dawsos/patterns/system/*.json (10 files)
- dawsos/patterns/actions/*.json (15 files)
- dawsos/patterns/governance/*.json (6 files)
- dawsos/patterns/macro/*.json (2 files)

**Commit**: Ready for `feature/pattern-migration` branch
```

---

## Start Command

When coordinator says "Start Stream 1":
1. Begin with Batch 1 (5 simple patterns)
2. Report progress after each batch
3. Flag any blockers immediately
4. Complete within 10-12 hours

**Your expertise**: Pattern structure, capability mapping, maintaining pattern integrity while modernizing execution.
