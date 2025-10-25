# DawsOSP Capability Audit Report

**Generated**: /Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP/scripts

---

## Executive Summary

- **Patterns analyzed**: 12
- **Agents analyzed**: 5
- **Services analyzed**: 21
- **Total unique capabilities in patterns**: 45
- **Total unique capabilities implemented**: 24
- **Missing capabilities**: 33
- **Coverage**: 53.3%

---

## Pattern Coverage Analysis

| Pattern ID | Total Caps | Implemented | Missing | Status |
|------------|------------|-------------|---------|--------|
| buffett_checklist | 5 | 4 | 1 | ⚠️ Partial (4/5) |
| cycle_deleveraging_scenarios | 7 | 2 | 5 | ⚠️ Partial (2/7) |
| export_portfolio_report | 6 | 5 | 1 | ⚠️ Partial (5/6) |
| holding_deep_dive | 8 | 0 | 8 | ❌ Not Started |
| macro_cycles_overview | 4 | 0 | 4 | ❌ Not Started |
| macro_trend_monitor | 4 | 0 | 4 | ❌ Not Started |
| news_impact_analysis | 5 | 2 | 3 | ⚠️ Partial (2/5) |
| policy_rebalance | 5 | 2 | 3 | ⚠️ Partial (2/5) |
| portfolio_cycle_risk | 5 | 1 | 4 | ⚠️ Partial (1/5) |
| portfolio_macro_overview | 6 | 4 | 2 | ⚠️ Partial (4/6) |
| portfolio_overview | 4 | 4 | 0 | ✅ Complete |
| portfolio_scenario_analysis | 5 | 3 | 2 | ⚠️ Partial (3/5) |

---

## Agent Capability Inventory

### ClaudeAgent

**Capabilities**: 3

- `claude.analyze`
- `claude.explain`
- `claude.summarize`

### DataHarvester

**Capabilities**: 6

- `fundamentals.load`
- `provider.fetch_fundamentals`
- `provider.fetch_macro`
- `provider.fetch_news`
- `provider.fetch_quote`
- `provider.fetch_ratios`

### FinancialAnalyst

**Capabilities**: 7

- `attribution.currency`
- `charts.overview`
- `ledger.positions`
- `metrics.compute`
- `metrics.compute_sharpe`
- `metrics.compute_twr`
- `pricing.apply_pack`

### MacroHound

**Capabilities**: 5

- `macro.compute_cycles`
- `macro.compute_dar`
- `macro.detect_regime`
- `macro.get_indicators`
- `macro.run_scenario`

### RatingsAgent

**Capabilities**: 3

- `ratings.dividend_safety`
- `ratings.moat_strength`
- `ratings.resilience`

---

## Missing Capabilities

### Ai (1 missing)

- `ai.explain` (no service)

### Alerts (2 missing)

- `alerts.create_if_threshold` (service exists)
- `alerts.suggest_presets` (service exists)

### Charts (2 missing)

- `charts.macro_overview` (no service)
- `charts.scenario_deltas` (no service)

### Cycles (4 missing)

- `cycles.aggregate_overview` (service exists)
- `cycles.compute_empire` (service exists)
- `cycles.compute_long_term` (service exists)
- `cycles.compute_short_term` (service exists)

### Macro (2 missing)

- `macro.detect_trend_shifts` (service exists)
- `macro.get_regime_history` (service exists)

### News (2 missing)

- `news.compute_portfolio_impact` (no service)
- `news.search` (no service)

### Optimizer (4 missing)

- `optimizer.analyze_impact` (no service)
- `optimizer.propose_trades` (no service)
- `optimizer.suggest_deleveraging_hedges` (no service)
- `optimizer.suggest_hedges` (no service)

### Other (8 missing)

- `compute_portfolio_contribution` (no service)
- `compute_position_currency_attribution` (no service)
- `compute_position_return` (no service)
- `compute_position_risk` (no service)
- `get_comparable_positions` (no service)
- `get_position_details` (no service)
- `get_security_fundamentals` (no service)
- `get_transaction_history` (no service)

### Ratings (1 missing)

- `ratings.aggregate` (service exists)

### Reports (1 missing)

- `reports.render_pdf` (service exists)

### Risk (3 missing)

- `risk.compute_factor_exposures` (service exists)
- `risk.get_factor_exposure_history` (service exists)
- `risk.overlay_cycle_phases` (service exists)

### Scenarios (3 missing)

- `scenarios.deleveraging_austerity` (service exists)
- `scenarios.deleveraging_default` (service exists)
- `scenarios.deleveraging_money_printing` (service exists)

---

## Service Method Inventory

Services available with async method counts:

### alerts.py (13 methods)

- `_evaluate_macro_condition()`
- `_evaluate_metric_condition()`
- `_evaluate_news_sentiment_condition()`
- `_evaluate_price_condition()`
- `_evaluate_rating_condition()`
- `_get_macro_value()`
- `_get_metric_value()`
- `_get_news_sentiment_value()`
- `_get_price_value()`
- `_get_rating_value()`
- `evaluate_condition()`
- `get_alert_value()`
- `should_trigger()`

### benchmarks.py (4 methods)

- `_get_benchmark_prices()`
- `_get_fx_rates()`
- `get_benchmark_returns()`
- `get_benchmark_returns_as_array()`

### corporate_actions.py (6 methods)

- `_get_open_lots()`
- `_get_or_create_fx_rate()`
- `get_dividend_history()`
- `record_dividend()`
- `record_split()`
- `record_withholding_tax()`

### currency_attribution.py (5 methods)

- `_get_base_currency()`
- `_get_pack_date()`
- `_get_portfolio_value()`
- `compute_attribution()`
- `compute_fx_exposure()`

### cycles.py (5 methods)

- `_store_phase()`
- `detect_empire_phase()`
- `detect_ltdc_phase()`
- `detect_stdc_phase()`
- `get_latest_indicators()`

### dlq.py (6 methods)

- `ack_dlq_job()`
- `cleanup_old_jobs()`
- `get_dlq_stats()`
- `nack_dlq_job()`
- `pop_from_dlq()`
- `push_to_dlq()`

### factor_analysis.py (6 methods)

- `_get_factor_covariance()`
- `_get_factor_returns()`
- `_get_pack_date()`
- `_get_portfolio_returns()`
- `compute_factor_exposure()`
- `compute_factor_var()`

### ledger.py (7 methods)

- `compute_ledger_nav()`
- `create_ledger_snapshot()`
- `extract_portfolio_transactions()`
- `main()`
- `mark_snapshot_complete()`
- `parse_and_store()`
- `store_postings()`

### macro.py (10 methods)

- `compute_zscore()`
- `detect_current_regime()`
- `detect_regime()`
- `detect_regime()`
- `fetch_indicators()`
- `get_indicators()`
- `get_latest_indicator()`
- `get_regime_history()`
- `store_indicator()`
- `store_regime_snapshot()`

### metrics.py (6 methods)

- `_get_pack_date()`
- `_get_portfolio_value()`
- `compute_max_drawdown()`
- `compute_mwr()`
- `compute_rolling_volatility()`
- `compute_twr()`

### notifications.py (10 methods)

- `_get_user_email()`
- `_send_email_ses()`
- `_send_email_smtp()`
- `check_deduplication()`
- `delete_notification()`
- `get_user_notifications()`
- `mark_notification_read()`
- `send_email_notification()`
- `send_inapp_notification()`
- `send_notification()`

### pricing.py (10 methods)

- `convert_currency()`
- `get_all_fx_rates()`
- `get_all_prices()`
- `get_fx_rate()`
- `get_latest_pack()`
- `get_pack_by_id()`
- `get_price()`
- `get_prices_as_decimals()`
- `get_prices_for_securities()`
- `is_pack_fresh()`

### providers.py (5 methods)

- `get_dividends()`
- `get_fundamentals()`
- `get_macro_series()`
- `get_prices()`
- `get_splits()`

### ratings.py (3 methods)

- `calculate_dividend_safety()`
- `calculate_moat_strength()`
- `calculate_resilience()`

### reports.py (4 methods)

- `_audit_log_export()`
- `example_usage()`
- `generate_csv()`
- `generate_pdf()`

### rights_registry.py (0 methods)

- *(No async methods found)*

### risk.py (6 methods)

- `apply_scenario()`
- `compute_dar()`
- `get_dar_scenarios()`
- `get_portfolio_factor_betas()`
- `get_portfolio_holdings()`
- `simulate_scenarios()`

### risk_metrics.py (7 methods)

- `_get_benchmark_returns()`
- `_get_pack_date()`
- `_get_portfolio_returns()`
- `compute_cvar()`
- `compute_risk_decomposition()`
- `compute_tracking_error()`
- `compute_var()`

### scenarios.py (4 methods)

- `apply_scenario()`
- `get_position_betas()`
- `rank_winners_losers()`
- `suggest_hedges()`

### trade_execution.py (6 methods)

- `_close_lots()`
- `_create_lot()`
- `_get_open_lots()`
- `execute_buy()`
- `execute_sell()`
- `get_portfolio_positions()`

### trade_execution_old.py (7 methods)

- `_close_lots()`
- `_create_lot()`
- `_get_open_lots()`
- `execute_buy()`
- `execute_sell()`
- `get_portfolio_positions()`
- `get_realized_pnl()`

---

## Recommendations

### Priority Actions

**1. Wire existing services (16 capabilities)**

These capabilities likely just need agent methods added:
- `alerts.create_if_threshold` → Check if `alerts.py` has `create_if_threshold()` method
- `alerts.suggest_presets` → Check if `alerts.py` has `suggest_presets()` method
- `cycles.aggregate_overview` → Check if `cycles.py` has `aggregate_overview()` method
- `cycles.compute_empire` → Check if `cycles.py` has `compute_empire()` method
- `cycles.compute_long_term` → Check if `cycles.py` has `compute_long_term()` method
- `cycles.compute_short_term` → Check if `cycles.py` has `compute_short_term()` method
- `macro.detect_trend_shifts` → Check if `macro.py` has `detect_trend_shifts()` method
- `macro.get_regime_history` → Check if `macro.py` has `get_regime_history()` method
- `ratings.aggregate` → Check if `ratings.py` has `aggregate()` method
- `reports.render_pdf` → Check if `reports.py` has `render_pdf()` method
- `risk.compute_factor_exposures` → Check if `risk.py` has `compute_factor_exposures()` method
- `risk.get_factor_exposure_history` → Check if `risk.py` has `get_factor_exposure_history()` method
- `risk.overlay_cycle_phases` → Check if `risk.py` has `overlay_cycle_phases()` method
- `scenarios.deleveraging_austerity` → Check if `scenarios.py` has `deleveraging_austerity()` method
- `scenarios.deleveraging_default` → Check if `scenarios.py` has `deleveraging_default()` method
- `scenarios.deleveraging_money_printing` → Check if `scenarios.py` has `deleveraging_money_printing()` method

**2. Implement missing services (17 capabilities)**

These capabilities need new service files or methods:
- Create/update `ai.py` (1 methods)
  - `ai.explain`
- Create/update `charts.py` (2 methods)
  - `charts.macro_overview`
  - `charts.scenario_deltas`
- Create/update `compute_portfolio_contribution.py` (1 methods)
  - `compute_portfolio_contribution`
- Create/update `compute_position_currency_attribution.py` (1 methods)
  - `compute_position_currency_attribution`
- Create/update `compute_position_return.py` (1 methods)
  - `compute_position_return`
- Create/update `compute_position_risk.py` (1 methods)
  - `compute_position_risk`
- Create/update `get_comparable_positions.py` (1 methods)
  - `get_comparable_positions`
- Create/update `get_position_details.py` (1 methods)
  - `get_position_details`
- Create/update `get_security_fundamentals.py` (1 methods)
  - `get_security_fundamentals`
- Create/update `get_transaction_history.py` (1 methods)
  - `get_transaction_history`
- Create/update `news.py` (2 methods)
  - `news.compute_portfolio_impact`
  - `news.search`
- Create/update `optimizer.py` (4 methods)
  - `optimizer.analyze_impact`
  - `optimizer.propose_trades`
  - `optimizer.suggest_deleveraging_hedges`
  - `optimizer.suggest_hedges`

