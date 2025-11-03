# Patterns Reference

**Version:** 1.0
**Last Updated:** November 3, 2025
**Purpose:** Complete reference for DawsOSP pattern system

---

## Pattern System Overview

**Patterns** are declarative JSON workflows that orchestrate multi-step operations across agents.

**Key Concepts:**
- **Pattern:** JSON file defining inputs, steps, and outputs
- **Step:** Single capability call (e.g., `ledger.positions`, `pricing.apply_pack`)
- **Capability:** Agent method exposed as "capability.method" string
- **Template Substitution:** Dynamic values using `{{inputs.x}}`, `{{state.y}}`, `{{ctx.z}}`
- **Orchestrator:** Executes patterns, routes to agents, builds trace

**Location:** `backend/patterns/*.json`

---

## Pattern Inventory (13 patterns)

### Portfolio Patterns (6 patterns)

#### 1. portfolio_overview.json
**Steps:** 6
**Purpose:** Core portfolio metrics, performance, attribution
**Capabilities:** ledger.positions, pricing.apply_pack, metrics.compute_twr, attribution.currency, portfolio.sector_allocation, portfolio.historical_nav
**Inputs:** portfolio_id (required), lookback_days (default: 252)
**Outputs:** positions, valued_positions, perf_metrics, currency_attr, sector_allocation, historical_nav

#### 2. holding_deep_dive.json
**Steps:** 8
**Purpose:** Detailed analysis of individual position
**Capabilities:** get_position_details, compute_position_return, compute_portfolio_contribution, compute_position_currency_attribution, compute_position_risk, get_transaction_history, get_security_fundamentals (conditional), get_comparable_positions (conditional)
**Inputs:** portfolio_id (required), security_id (required), lookback_days (default: 252)
**Outputs:** position_details, position_return, portfolio_contribution, currency_attribution, risk_analysis, transactions, fundamentals (optional), comparables (optional)

#### 3. holdings_detail.json ⭐ NEW
**Steps:** 8
**Purpose:** Individual holding deep dive analysis
**Capabilities:** Similar to holding_deep_dive.json
**Inputs:** portfolio_id (required), security_id (required), lookback_days (default: 252)
**Note:** Recently discovered pattern, not previously documented

#### 4. portfolio_macro_overview.json
**Steps:** 6
**Purpose:** Regime detection + factor exposures
**Capabilities:** macro.detect_regime, risk.compute_factor_exposures, cycles.aggregate_overview, risk.overlay_cycle_phases, ledger.positions, pricing.apply_pack
**Inputs:** portfolio_id (required), asof_date (optional)
**Outputs:** regime, factor_exposures, cycles, cycle_overlay, positions, valued_positions

#### 5. portfolio_cycle_risk.json
**Steps:** 5
**Purpose:** Macro-aware risk mapping
**Capabilities:** cycles.aggregate_overview, ledger.positions, pricing.apply_pack, risk.compute_factor_exposures, risk.overlay_cycle_phases
**Inputs:** portfolio_id (required)
**Outputs:** cycles, positions, valued_positions, factor_exposures, cycle_risk_map

#### 6. portfolio_scenario_analysis.json
**Steps:** 5
**Purpose:** Stress testing with hedge suggestions
**Capabilities:** ledger.positions, pricing.apply_pack, scenarios.deleveraging_austerity, scenarios.deleveraging_default, scenarios.deleveraging_money_printing
**Inputs:** portfolio_id (required)
**Outputs:** positions, valued_positions, austerity_scenario, default_scenario, money_printing_scenario

### Macro Patterns (2 patterns)

#### 7. macro_cycles_overview.json
**Steps:** 4
**Purpose:** Dalio's 4 cycles (STDC, LTDC, Empire, Civil)
**Capabilities:** cycles.compute_short_term, cycles.compute_long_term, cycles.compute_empire, cycles.compute_civil
**Inputs:** asof_date (optional)
**Outputs:** stdc, ltdc, empire, civil
**Note:** ONLY pattern that doesn't require portfolio_id

#### 8. macro_trend_monitor.json
**Steps:** 4
**Purpose:** Trend tracking and regime shifts
**Capabilities:** macro.detect_regime, macro.get_indicators, cycles.aggregate_overview, macro.detect_trend_shifts
**Inputs:** portfolio_id (required), asof_date (optional)
**Outputs:** regime, indicators, cycles, trend_shifts

### Analysis Patterns (2 patterns)

#### 9. buffett_checklist.json
**Steps:** 6
**Purpose:** Quality assessment (moat, dividend, resilience)
**Capabilities:** fundamentals.load, ratings.dividend_safety, ratings.moat_strength, ratings.resilience, ratings.aggregate, ai.explain
**Inputs:** portfolio_id (required), security_id (required)
**Outputs:** fundamentals, dividend_safety, moat_strength, resilience, buffett_score, ai_explanation

#### 10. news_impact_analysis.json
**Steps:** 5
**Purpose:** Portfolio-weighted sentiment analysis
**Capabilities:** ledger.positions, pricing.apply_pack, news.search, news.compute_portfolio_impact, ai.explain (conditional)
**Inputs:** portfolio_id (required), lookback_days (default: 7)
**Outputs:** positions, valued_positions, news, impact_analysis, ai_explanation (optional)

### Workflow Patterns (3 patterns)

#### 11. export_portfolio_report.json
**Steps:** 6
**Purpose:** PDF generation with full portfolio data
**Capabilities:** ledger.positions, pricing.apply_pack, metrics.compute_twr, attribution.currency, macro.detect_regime (conditional), reports.render_pdf
**Inputs:** portfolio_id (required), report_format (default: "pdf")
**Outputs:** positions, valued_positions, performance, attribution, regime (optional), pdf_report

#### 12. policy_rebalance.json
**Steps:** 5
**Purpose:** Buffett-style portfolio rebalancing
**Capabilities:** ledger.positions, pricing.apply_pack, ratings.aggregate, optimizer.rebalance, reports.render_pdf (conditional)
**Inputs:** portfolio_id (required), rebalance_threshold (default: 0.05)
**Outputs:** positions, valued_positions, ratings, rebalance_result, report (optional)

#### 13. cycle_deleveraging_scenarios.json
**Steps:** 7
**Purpose:** Dalio-style deleveraging shock analysis
**Capabilities:** ledger.positions, pricing.apply_pack, scenarios.deleveraging_austerity, scenarios.deleveraging_default, scenarios.deleveraging_money_printing, scenarios.macro_aware_apply, scenarios.macro_aware_rank
**Inputs:** portfolio_id (required)
**Outputs:** positions, valued_positions, austerity, default, money_printing, scenario_comparison, ranked_hedges

---

## Pattern Execution

### Execution Flow

```
User → POST /api/patterns/execute
  ↓
PatternOrchestrator.run_pattern()
  ↓
1. Load pattern JSON
2. Validate inputs
3. Execute steps sequentially
4. Apply template substitution
5. Route capabilities to agents
6. Build execution trace
7. Return aggregated results
```

### Request Format

```json
{
  "pattern_name": "portfolio_overview",
  "inputs": {
    "portfolio_id": "11111111-1111-1111-1111-111111111111",
    "lookback_days": 252
  }
}
```

### Response Format

```json
{
  "success": true,
  "data": {
    "positions": {...},
    "valued_positions": {...},
    "perf_metrics": {...},
    "currency_attr": {...},
    "sector_allocation": {...},
    "historical_nav": {...}
  },
  "trace": {
    "pattern_id": "portfolio_overview",
    "pricing_pack_id": "...",
    "ledger_commit_hash": "...",
    "steps": [...],
    "agents_used": ["financial_analyst"],
    "capabilities_used": ["ledger.positions", "pricing.apply_pack", ...],
    "sources": [...]
  }
}
```

---

## Template Substitution

### Available Variables

**{{inputs.field}}** - From pattern inputs
```json
{
  "capability": "ledger.positions",
  "args": {
    "portfolio_id": "{{inputs.portfolio_id}}"
  }
}
```

**{{ctx.field}}** - From RequestCtx (immutable context)
```json
{
  "capability": "pricing.apply_pack",
  "args": {
    "pricing_pack_id": "{{ctx.pricing_pack_id}}",
    "asof_date": "{{ctx.asof_date}}"
  }
}
```

**{{step_name}}** or **{{step_name.field}}** - From previous step result (use step's "as" name)
```json
{
  "capability": "pricing.apply_pack",
  "args": {
    "positions": "{{positions.positions}}"
  },
  "as": "valued_positions"
}
```

**Note**: All patterns now use direct references to step results. The `{{state.foo}}` style has been deprecated and all patterns have been migrated to use `{{foo}}` where `foo` is the step's `"as"` key.
```json
{
  "capability": "metrics.compute_twr",
  "args": {
    "positions": "{{valued_positions.positions}}",
    "total_value": "{{valued_positions.total_value}}"
  }
}
```

### Nested Path Access

```json
{
  "capability": "portfolio.sector_allocation",
  "args": {
    "positions": "{{valued_positions.positions}}"
  }
}
```

Resolves to: `data['valued_positions']['positions']`

---

## Agent Capabilities

### FinancialAnalyst (17 capabilities)
- ledger.positions
- pricing.apply_pack
- metrics.compute_twr
- metrics.compute_sharpe
- attribution.currency
- portfolio.sector_allocation
- portfolio.historical_nav
- get_position_details
- compute_position_return
- compute_portfolio_contribution
- compute_position_currency_attribution
- compute_position_risk
- get_transaction_history
- get_security_fundamentals
- get_comparable_positions
- risk.compute_factor_exposures
- risk.overlay_cycle_phases

### MacroHound (16 capabilities)
- macro.detect_regime
- macro.compute_cycles
- macro.get_indicators
- macro.detect_trend_shifts
- cycles.compute_short_term
- cycles.compute_long_term
- cycles.compute_empire
- cycles.compute_civil
- cycles.aggregate_overview
- scenarios.deleveraging_austerity
- scenarios.deleveraging_default
- scenarios.deleveraging_money_printing
- scenarios.macro_aware_apply
- scenarios.macro_aware_rank

### DataHarvester (8 capabilities)
- provider.fetch_quote
- provider.fetch_fundamentals
- provider.fetch_news
- provider.fetch_macro
- provider.fetch_ratios
- fundamentals.load
- news.search
- news.compute_portfolio_impact

### ClaudeAgent (7 capabilities)
- claude.explain
- claude.summarize
- claude.analyze
- claude.portfolio_advice
- claude.financial_qa
- claude.scenario_analysis
- ai.explain (alias)

### RatingsAgent (5 capabilities)
- ratings.dividend_safety
- ratings.moat_strength
- ratings.resilience
- ratings.aggregate
- ratings.compute_buffett_score

### OptimizerAgent, ChartsAgent, ReportsAgent, AlertsAgent
- Capabilities TBD (need examination)

---

## Pattern Development

### Creating a Pattern

**1. Define Pattern Structure:**
```json
{
  "id": "my_pattern",
  "name": "My Pattern",
  "description": "What this pattern does",
  "version": "1.0.0",
  "category": "analysis",
  "tags": ["portfolio", "analysis"],
  "author": "DawsOS",
  "created": "2025-11-03",

  "inputs": {
    "portfolio_id": {
      "type": "uuid",
      "required": true,
      "description": "Portfolio to analyze"
    },
    "lookback_days": {
      "type": "integer",
      "default": 252,
      "description": "Analysis period"
    }
  },

  "steps": [...],

  "outputs": ["step1_result", "step2_result"],

  "presentation": {...},
  "rights_required": [],
  "export_allowed": true
}
```

**2. Define Steps:**
```json
{
  "steps": [
    {
      "capability": "ledger.positions",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}"
      },
      "as": "positions",
      "description": "Get portfolio positions"
    },
    {
      "capability": "my.analysis",
      "args": {
        "data": "{{positions.positions}}"
      },
      "as": "analysis",
      "description": "Analyze positions",
      "condition": "{{positions.positions|length}} > 0"
    }
  ]
}
```

**3. Define Presentation (Optional):**
```json
{
  "presentation": {
    "summary": {
      "type": "metrics_grid",
      "dataPath": "analysis.summary"
    },
    "details": {
      "type": "table",
      "dataPath": "analysis.details"
    }
  }
}
```

**4. Test Pattern:**
```bash
curl -X POST http://localhost:8000/api/patterns/execute \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"pattern_name":"my_pattern","inputs":{"portfolio_id":"..."}}'
```

---

## Best Practices

### Pattern Design

1. ✅ **Single Responsibility** - One pattern = one business workflow
2. ✅ **Clear Naming** - Use descriptive pattern IDs
3. ✅ **Input Validation** - Define types and required fields
4. ✅ **Conditional Steps** - Use conditions for optional steps
5. ✅ **Meaningful Outputs** - Return only necessary data

### Performance

1. ✅ **Minimize Steps** - Fewer steps = faster execution
2. ✅ **Parallel Execution** - Use async where possible (future)
3. ✅ **Cache Results** - Pattern orchestrator caches intermediate results
4. ✅ **Limit Data** - Don't return massive datasets

### Debugging

1. ✅ **Check Trace** - Response includes execution trace
2. ✅ **Verify Inputs** - Ensure all required inputs provided
3. ✅ **Test Capabilities** - Test each capability individually first
4. ✅ **Validate Templates** - Ensure template substitution works

---

## References

**Code:**
- [backend/patterns/](backend/patterns/) - Pattern JSON files (13 patterns)
- [backend/app/core/pattern_orchestrator.py](backend/app/core/pattern_orchestrator.py) - Orchestrator implementation
- [backend/app/core/agent_runtime.py](backend/app/core/agent_runtime.py) - Agent routing

**Archived Documentation:**
- [.archive/investigations/PATTERNS_DEEP_CONTEXT_REPORT.md](.archive/investigations/) - Deep pattern analysis (794 lines)
- [.archive/deprecated/PATTERN_RESPONSE_STRUCTURE_VERIFICATION.md](.archive/deprecated/) - Response structure verification

**Related:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development guide

---

**Last Updated:** November 3, 2025
