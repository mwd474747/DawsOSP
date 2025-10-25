# Pattern-Capability-Agent Mapping

**Date**: 2025-10-24
**Purpose**: Complete reference for pattern execution architecture
**Status**: Verified against actual code

---

## Overview

DawsOS uses a **pattern-based execution model** where:
1. **Patterns** (JSON files) define declarative workflows
2. **Capabilities** (methods) are the atomic operations patterns invoke
3. **Agents** (Python classes) implement capabilities and route to services

---

## 12 Patterns Implemented

| Pattern ID | Category | Description | Key Capabilities |
|------------|----------|-------------|------------------|
| `portfolio_overview` | Portfolio | Core portfolio snapshot | ledger.positions, pricing.apply_pack, metrics.compute_twr, attribution.currency |
| `portfolio_macro_overview` | Portfolio | Portfolio with macro regime overlay | macro.detect_regime, macro.get_indicators, risk.compute_factor_exposures |
| `buffett_checklist` | Analysis | Buffett quality ratings | fundamentals.load, ratings.dividend_safety, ratings.moat_strength, ratings.resilience, ai.explain |
| `policy_rebalance` | Optimizer | Policy-based rebalancing | optimizer.propose_trades, optimizer.analyze_impact, ratings.aggregate |
| `macro_cycles_overview` | Macro | STDC/LTDC/Empire cycles | cycles.compute_short_term, cycles.compute_long_term, cycles.compute_empire, cycles.aggregate_overview |
| `portfolio_cycle_risk` | Risk | Portfolio risk by cycle phase | cycles.*, risk.compute_factor_exposures, risk.overlay_cycle_phases |
| `cycle_deleveraging_scenarios` | Scenarios | Dalio deleveraging scenarios | cycles.compute_long_term, scenarios.deleveraging_* |
| `news_impact_analysis` | News | News impact on portfolio | news.search, news.compute_portfolio_impact, alerts.create_if_threshold |
| `macro_trend_monitor` | Alerts | Regime shift detection | macro.detect_trend_shifts, macro.get_regime_history, alerts.suggest_presets |
| `portfolio_scenario_analysis` | Scenarios | What-if scenarios | macro.run_scenario, optimizer.suggest_hedges |
| `holding_deep_dive` | Holdings | Individual position analysis | get_position_details, get_transaction_history, get_security_fundamentals |
| `export_portfolio_report` | Reports | PDF generation with rights | reports.render_pdf, (reuses portfolio_overview capabilities) |

---

## 4 Agents Registered

**Location**: [backend/app/api/executor.py](../backend/app/api/executor.py) (lines 117-135)

### 1. FinancialAnalyst
**File**: [backend/app/agents/financial_analyst.py](../backend/app/agents/financial_analyst.py)
**Capabilities**:
- `ledger.positions` - Load portfolio positions from lots table
- `pricing.apply_pack` - Apply pricing pack to positions
- `metrics.compute_twr` - Time-weighted return
- `metrics.compute_sharpe` - Sharpe ratio
- `attribution.currency` - Currency return decomposition

### 2. MacroHound
**File**: [backend/app/agents/macro_hound.py](../backend/app/agents/macro_hound.py)
**Capabilities**:
- `macro.detect_regime` - 5-regime classification
- `macro.compute_dar` - Drawdown at Risk
- `macro.get_indicators` - FRED indicators
- `macro.run_scenario` - Scenario analysis
- `cycles.compute_short_term` - STDC phase
- `cycles.compute_long_term` - LTDC phase
- `cycles.compute_empire` - Empire cycle
- `cycles.aggregate_overview` - All cycles summary
- `risk.compute_factor_exposures` - Factor analysis

### 3. DataHarvester
**File**: [backend/app/agents/data_harvester.py](../backend/app/agents/data_harvester.py)
**Capabilities**:
- `provider.fetch_quote` - Real-time quotes (FMP, Polygon)
- `provider.fetch_fundamentals` - Fundamental data (FMP)
- `provider.fetch_ratios` - Financial ratios (FMP)
- `provider.fetch_macro` - Macro indicators (FRED)
- `provider.fetch_news` - News articles (NewsAPI)

### 4. ClaudeAgent
**File**: [backend/app/agents/claude_agent.py](../backend/app/agents/claude_agent.py)
**Capabilities**:
- `ai.explain` - Natural language explanations
- `ai.analyze` - Analysis and insights
- `ai.summarize` - Summary generation

---

## 44 Unique Capabilities (from patterns)

### ✅ Implemented (18 capabilities)

| Capability | Agent | Status |
|------------|-------|--------|
| `ledger.positions` | FinancialAnalyst | ✅ Working |
| `pricing.apply_pack` | FinancialAnalyst | ✅ Working |
| `metrics.compute_twr` | FinancialAnalyst | ✅ Working |
| `metrics.compute_sharpe` | FinancialAnalyst | ✅ Working |
| `attribution.currency` | FinancialAnalyst | ✅ Working |
| `macro.detect_regime` | MacroHound | ✅ Working |
| `macro.compute_dar` | MacroHound | ✅ Working |
| `macro.get_indicators` | MacroHound | ✅ Working |
| `macro.run_scenario` | MacroHound | ✅ Working |
| `cycles.compute_short_term` | MacroHound | ✅ Working |
| `cycles.compute_long_term` | MacroHound | ✅ Working |
| `cycles.compute_empire` | MacroHound | ✅ Working |
| `cycles.aggregate_overview` | MacroHound | ✅ Working |
| `risk.compute_factor_exposures` | MacroHound | ✅ Working |
| `provider.fetch_*` | DataHarvester | ✅ Working (5 methods) |
| `ai.explain` | ClaudeAgent | ✅ Working |
| `ai.analyze` | ClaudeAgent | ✅ Working |
| `ai.summarize` | ClaudeAgent | ✅ Working |

### ❌ Missing (26 capabilities - need implementation)

#### Ratings (buffett_checklist pattern)
- `fundamentals.load` - Load fundamental data (partial: use provider.fetch_fundamentals)
- `ratings.dividend_safety` - **NEED RatingsAgent**
- `ratings.moat_strength` - **NEED RatingsAgent**
- `ratings.resilience` - **NEED RatingsAgent**
- `ratings.aggregate` - **NEED RatingsAgent**

#### Optimizer (policy_rebalance pattern)
- `optimizer.propose_trades` - **NEED OptimizerAgent**
- `optimizer.analyze_impact` - **NEED OptimizerAgent**
- `optimizer.suggest_hedges` - **NEED OptimizerAgent**
- `optimizer.suggest_deleveraging_hedges` - **NEED OptimizerAgent**

#### News (news_impact_analysis pattern)
- `news.search` - **NEED NewsAgent** (partial: use provider.fetch_news)
- `news.compute_portfolio_impact` - **NEED NewsAgent**

#### Alerts (macro_trend_monitor pattern)
- `alerts.suggest_presets` - **NEED AlertsAgent**
- `alerts.create_if_threshold` - **NEED AlertsAgent**

#### Reports (export_portfolio_report pattern)
- `reports.render_pdf` - **NEED ReportsAgent**

#### Charts (visualization)
- `charts.macro_overview` - **NEED ChartsAgent** or move to UI
- `charts.scenario_deltas` - **NEED ChartsAgent** or move to UI

#### Scenarios (deleveraging)
- `scenarios.deleveraging_austerity` - **NEED ScenariosAgent** or extend MacroHound
- `scenarios.deleveraging_default` - **NEED ScenariosAgent** or extend MacroHound
- `scenarios.deleveraging_money_printing` - **NEED ScenariosAgent** or extend MacroHound

#### Holding Deep Dive (holding_deep_dive pattern)
- `get_position_details` - **NEED PositionsAgent** or extend FinancialAnalyst
- `get_transaction_history` - **NEED PositionsAgent** or extend FinancialAnalyst
- `get_security_fundamentals` - Can use provider.fetch_fundamentals
- `compute_position_return` - **NEED PositionsAgent** or extend FinancialAnalyst
- `compute_position_risk` - **NEED PositionsAgent** or extend FinancialAnalyst
- `compute_position_currency_attribution` - **NEED PositionsAgent** or extend FinancialAnalyst
- `compute_portfolio_contribution` - **NEED PositionsAgent** or extend FinancialAnalyst
- `get_comparable_positions` - **NEED PositionsAgent** or extend FinancialAnalyst

#### Macro Enhancements
- `macro.detect_trend_shifts` - **Extend MacroHound**
- `macro.get_regime_history` - **Extend MacroHound**
- `risk.get_factor_exposure_history` - **Extend MacroHound**
- `risk.overlay_cycle_phases` - **Extend MacroHound**

---

## Pattern Execution Flow

```
User Request
    ↓
/v1/execute Endpoint (executor.py)
    ↓
PatternOrchestrator (pattern_orchestrator.py)
    ↓
Load Pattern JSON (backend/patterns/*.json)
    ↓
Parse Steps & Template Substitution
    ↓
AgentRuntime (agent_runtime.py)
    ↓
Route Capability → Agent Method
    ↓
Agent executes (calls Services)
    ↓
Service queries DB / providers
    ↓
Result returned to orchestrator
    ↓
All steps completed
    ↓
Response to user
```

---

## Missing Agent Implementation Plan

### Priority 1: Core Business Logic (1-2 weeks)

**1. RatingsAgent** (3-4 days)
- File: `backend/app/agents/ratings_agent.py`
- Capabilities: `ratings.dividend_safety`, `ratings.moat_strength`, `ratings.resilience`, `ratings.aggregate`
- Pattern: `buffett_checklist.json`
- Service: Create `backend/app/services/ratings.py` (Buffett scoring logic)

**2. OptimizerAgent** (3-4 days)
- File: `backend/app/agents/optimizer_agent.py`
- Capabilities: `optimizer.propose_trades`, `optimizer.analyze_impact`, `optimizer.suggest_hedges`
- Pattern: `policy_rebalance.json`
- Library: Integrate Riskfolio-Lib (mean-variance optimization)
- Service: Extend `backend/app/services/optimizer.py` (if exists) or create

### Priority 2: Supporting Features (3-5 days)

**3. NewsAgent** (1-2 days)
- File: `backend/app/agents/news_agent.py`
- Capabilities: `news.search`, `news.compute_portfolio_impact`
- Pattern: `news_impact_analysis.json`
- Service: Extend `backend/app/services/news.py` or create (sentiment analysis)

**4. AlertsAgent** (1-2 days)
- File: `backend/app/agents/alerts_agent.py`
- Capabilities: `alerts.suggest_presets`, `alerts.create_if_threshold`
- Pattern: `macro_trend_monitor.json`
- Service: Use existing `backend/app/services/alerts.py`

**5. ReportsAgent** (1 day)
- File: `backend/app/agents/reports_agent.py`
- Capabilities: `reports.render_pdf`
- Pattern: `export_portfolio_report.json`
- Library: WeasyPrint or ReportLab
- Service: Create `backend/app/services/reports.py`

### Priority 3: Extend Existing Agents (2-3 days)

**6. Extend FinancialAnalyst** (1-2 days)
- Add holding_deep_dive capabilities
- Pattern: `holding_deep_dive.json`

**7. Extend MacroHound** (1 day)
- Add scenarios.deleveraging_* capabilities
- Add macro trend/history capabilities
- Pattern: `cycle_deleveraging_scenarios.json`, `macro_trend_monitor.json`

---

## Anti-Patterns to Avoid

❌ **DO NOT**:
1. Implement capabilities as standalone functions (must be agent methods)
2. Bypass pattern orchestrator (no direct service calls from UI)
3. Create duplicate capabilities across agents (single responsibility)
4. Hardcode pattern logic in agents (keep patterns declarative)
5. Skip agent registration in executor.py (patterns will fail silently)

✅ **DO**:
1. Follow existing agent structure (inherit from BaseAgent)
2. Register all agents in executor.py `get_agent_runtime()`
3. Use capability routing (`<domain>.<action>` naming)
4. Implement services layer (agents orchestrate, services execute)
5. Test patterns end-to-end via `/v1/execute` endpoint

---

## Testing Patterns

```bash
# Test portfolio_overview pattern (✅ fully implemented)
curl -X POST http://localhost:8000/v1/execute \
  -H "X-User-ID: 22222222-2222-2222-2222-222222222222" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "portfolio_overview",
    "inputs": {"portfolio_id": "11111111-1111-1111-1111-111111111111"}
  }'

# Test buffett_checklist pattern (❌ missing RatingsAgent)
curl -X POST http://localhost:8000/v1/execute \
  -H "X-User-ID: 22222222-2222-2222-2222-222222222222" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "buffett_checklist",
    "inputs": {"security_id": "aaaa0000-1111-2222-3333-444444444444"}
  }'
# Expected: Error - capability 'ratings.dividend_safety' not found

# Test policy_rebalance pattern (❌ missing OptimizerAgent)
curl -X POST http://localhost:8000/v1/execute \
  -H "X-User-ID: 22222222-2222-2222-2222-222222222222" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "policy_rebalance",
    "inputs": {"portfolio_id": "11111111-1111-1111-1111-111111111111"}
  }'
# Expected: Error - capability 'optimizer.propose_trades' not found
```

---

## Implementation Checklist

### For New Agents

- [ ] Create agent file in `backend/app/agents/`
- [ ] Inherit from `BaseAgent`
- [ ] Implement `__init__` with proper metadata
- [ ] Implement capability methods (async def)
- [ ] Register agent in `backend/app/api/executor.py`
- [ ] Create/extend service layer
- [ ] Test via `/v1/execute` with pattern
- [ ] Update `.claude/agents/ORCHESTRATOR.md`

### For New Capabilities

- [ ] Add method to existing agent
- [ ] Follow naming: `<domain>_<action>` (Python) → `<domain>.<action>` (pattern)
- [ ] Document in agent docstring
- [ ] Test via pattern JSON
- [ ] Update `.claude/agents/<AGENT>.md`

---

**Last Updated**: 2025-10-24
**Verified Against**: backend/patterns/*.json, backend/app/agents/*.py, backend/app/api/executor.py
