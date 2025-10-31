# DawsOS Capabilities Mapping

## Overview
This document maps all 52 backend capabilities to their corresponding UI endpoints and pages.

## Agent Capabilities Breakdown

### 1. Financial Analyst Agent (18 capabilities)
**Location: Dashboard, Risk Analytics, Attribution pages**

| Capability | Backend Pattern | UI Page | API Endpoint |
|------------|----------------|---------|--------------|
| ledger.positions | portfolio_overview | Dashboard | GET /api/portfolios/1 |
| pricing.apply_pack | portfolio_overview | Dashboard | GET /api/portfolios/1 |
| metrics.compute | portfolio_overview | Dashboard | GET /api/metrics/1 |
| metrics.compute_twr | portfolio_overview | Dashboard | GET /api/metrics/1 |
| metrics.compute_sharpe | portfolio_overview | Risk Analytics | GET /api/metrics/1 |
| attribution.currency | portfolio_overview | Attribution | GET /api/attribution/1 |
| charts.overview | portfolio_overview | Dashboard | GET /api/portfolios/1 |
| risk.compute_factor_exposures | portfolio_overview | Risk Analytics | GET /api/metrics/1 |
| risk.get_factor_exposure_history | portfolio_overview | Risk Analytics | GET /api/metrics/1 |
| risk.overlay_cycle_phases | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| get_position_details | portfolio_overview | Dashboard | GET /api/portfolios/1 |
| compute_position_return | portfolio_overview | Dashboard | GET /api/portfolios/1 |
| compute_portfolio_contribution | portfolio_overview | Attribution | GET /api/attribution/1 |
| compute_position_currency_attribution | portfolio_overview | Attribution | GET /api/attribution/1 |
| compute_position_risk | portfolio_overview | Risk Analytics | GET /api/metrics/1 |
| get_transaction_history | portfolio_overview | Dashboard | GET /api/portfolios/1 |
| get_security_fundamentals | portfolio_overview | Dashboard | GET /api/portfolios/1 |
| get_comparable_positions | portfolio_overview | Dashboard | GET /api/portfolios/1 |

### 2. Macro Hound Agent (14 capabilities)
**Location: Macro Cycles, Scenarios pages**

| Capability | Backend Pattern | UI Page | API Endpoint |
|------------|----------------|---------|--------------|
| macro.detect_regime | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| macro.compute_cycles | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| macro.get_indicators | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| macro.run_scenario | portfolio_scenario_analysis | Scenarios | POST /api/patterns/execute |
| macro.compute_dar | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| macro.get_regime_history | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| macro.detect_trend_shifts | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| cycles.compute_short_term | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| cycles.compute_long_term | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| cycles.compute_empire | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| cycles.aggregate_overview | macro_cycles_overview | Macro Cycles | POST /api/patterns/execute |
| scenarios.deleveraging_austerity | portfolio_scenario_analysis | Scenarios | POST /api/patterns/execute |
| scenarios.deleveraging_default | portfolio_scenario_analysis | Scenarios | POST /api/patterns/execute |
| scenarios.deleveraging_money_printing | portfolio_scenario_analysis | Scenarios | POST /api/patterns/execute |

### 3. Data Harvester Agent (8 capabilities)
**Location: Market Data page**

| Capability | Backend Pattern | UI Page | API Endpoint |
|------------|----------------|---------|--------------|
| provider.fetch_quote | news_impact_analysis | Market Data | POST /api/patterns/execute |
| provider.fetch_fundamentals | news_impact_analysis | Market Data | POST /api/patterns/execute |
| provider.fetch_news | news_impact_analysis | Market Data | POST /api/patterns/execute |
| provider.fetch_macro | news_impact_analysis | Market Data | POST /api/patterns/execute |
| provider.fetch_ratios | news_impact_analysis | Market Data | POST /api/patterns/execute |
| fundamentals.load | news_impact_analysis | Market Data | POST /api/patterns/execute |
| news.search | news_impact_analysis | Market Data | POST /api/patterns/execute |
| news.compute_portfolio_impact | news_impact_analysis | Market Data | POST /api/patterns/execute |

### 4. Claude Agent (4 capabilities)
**Location: AI Insights page**

| Capability | Backend Pattern | UI Page | API Endpoint |
|------------|----------------|---------|--------------|
| claude.explain | - | AI Insights | GET /api/portfolios/1/analysis |
| claude.summarize | - | AI Insights | GET /api/portfolios/1/analysis |
| claude.analyze | - | AI Insights | GET /api/portfolios/1/analysis |
| ai.explain | - | AI Insights | GET /api/portfolios/1/analysis |

### 5. Ratings Agent (4 capabilities)
**Location: Ratings page**

| Capability | Backend Pattern | UI Page | API Endpoint |
|------------|----------------|---------|--------------|
| ratings.dividend_safety | buffett_checklist | Ratings | POST /api/patterns/execute |
| ratings.moat_strength | buffett_checklist | Ratings | POST /api/patterns/execute |
| ratings.resilience | buffett_checklist | Ratings | POST /api/patterns/execute |
| ratings.aggregate | buffett_checklist | Ratings | POST /api/patterns/execute |

### 6. Optimizer Agent (4 capabilities)
**Location: Optimizer page**

| Capability | Backend Pattern | UI Page | API Endpoint |
|------------|----------------|---------|--------------|
| optimizer.propose_trades | policy_rebalance | Optimizer | POST /api/patterns/execute |
| optimizer.analyze_impact | policy_rebalance | Optimizer | POST /api/patterns/execute |
| optimizer.suggest_hedges | policy_rebalance | Optimizer | POST /api/patterns/execute |
| optimizer.suggest_deleveraging_hedges | policy_rebalance | Optimizer | POST /api/patterns/execute |

## UI Page to Backend Mapping

### Dashboard
- **Endpoint**: GET /api/portfolios/1, GET /api/metrics/1
- **Auto-refresh**: 30 seconds
- **Capabilities**: 10+ from financial_analyst

### Macro Cycles
- **Endpoint**: POST /api/patterns/execute (pattern: macro_cycles_overview)
- **Auto-refresh**: 60 seconds
- **Capabilities**: 11 from macro_hound
- **Visualizations**: Short-term cycle (line), Long-term cycle (area), Empire cycle (timeline), DAR analysis

### Risk Analytics
- **Endpoint**: GET /api/metrics/1, GET /api/attribution/1
- **Auto-refresh**: 30 seconds
- **Capabilities**: 6 from financial_analyst

### Scenarios
- **Endpoint**: POST /api/patterns/execute (pattern: portfolio_scenario_analysis)
- **Capabilities**: 4 from macro_hound

### Optimizer
- **Endpoint**: POST /api/patterns/execute (pattern: policy_rebalance)
- **Capabilities**: 4 from optimizer_agent

### Ratings
- **Endpoint**: POST /api/patterns/execute (pattern: buffett_checklist)
- **Capabilities**: 4 from ratings_agent

### AI Insights
- **Endpoint**: GET /api/portfolios/1/analysis
- **Capabilities**: 4 from claude_agent

### Alerts
- **Endpoints**: GET /api/alerts, POST /api/alerts, GET /api/alerts/triggered
- **Auto-refresh**: 10 seconds

### Attribution
- **Endpoint**: GET /api/attribution/1
- **Capabilities**: 4 from financial_analyst

### Market Data
- **Endpoint**: POST /api/patterns/execute (pattern: news_impact_analysis)
- **Auto-refresh**: 30 seconds
- **Capabilities**: 8 from data_harvester

### Reports
- **Endpoint**: POST /api/patterns/execute (pattern: export_portfolio_report)

## Authentication Flow
1. Login form calls POST /api/auth/login with email/password
2. JWT token stored in localStorage
3. All API calls include Authorization header with JWT
4. 401 responses trigger redirect to login page

## Total Capabilities: 52
- Financial Analyst: 18 ✅
- Macro Hound: 14 ✅
- Data Harvester: 8 ✅
- Claude Agent: 4 ✅
- Ratings Agent: 4 ✅
- Optimizer Agent: 4 ✅

All capabilities are now properly wired and accessible through the DawsOS UI!