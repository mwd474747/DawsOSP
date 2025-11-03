# Phase 2 Testing & Validation Checklist

## Pre-Testing Setup
- [ ] Ensure DawsOS server is running on port 5000
- [ ] Verify database connection is active
- [ ] Check that all 9 agents initialize without errors
- [ ] Confirm no duplicate capability registration errors in startup logs

## 1. Pattern Orchestrator Validation (Critical)

### Test Nested Storage Fix
- [ ] Execute `portfolio_overview` pattern
- [ ] Verify response structure doesn't have `result.result.data`
- [ ] Check that `historical_nav` is directly accessible (not `historical_nav.historical_nav`)
- [ ] Confirm `sector_allocation` is directly accessible
- [ ] Validate `currency_attr` fields resolve correctly

### Template Variable Resolution
- [ ] Check `{{currency_attr.local_return}}` resolves correctly
- [ ] Check `{{currency_attr.fx_return}}` resolves correctly
- [ ] Check `{{historical_nav}}` returns array directly
- [ ] Verify all template variables in presentation section work

## 2. Agent Stability Checks

### ChartsAgent Fix
- [ ] Server starts without "charts.overview already registered" error
- [ ] ChartsAgent only registers `charts.macro_overview` and `charts.scenario_deltas`
- [ ] FinancialAnalyst successfully provides `charts.overview`

### Import Cleanup
- [ ] No import errors during server startup
- [ ] All agents load successfully
- [ ] No unused import warnings in logs

## 3. Corporate Actions Endpoint

### Validation Tests
- [ ] Request without portfolio_id returns 422 error
- [ ] Request with invalid UUID returns 400 error
- [ ] Request with valid UUID returns empty array with metadata
- [ ] Response includes "Corporate actions tracking not implemented" message

## 4. Pattern Execution Tests

### Critical Patterns (Most Affected)
- [ ] `portfolio_overview` - Executes without errors
- [ ] `holding_deep_dive` - Currency attribution works
- [ ] `export_portfolio_report` - PDF export generates

### All Other Patterns (Smoke Test)
- [ ] `buffett_checklist` - Executes
- [ ] `cycle_deleveraging_scenarios` - Executes
- [ ] `macro_cycles_overview` - Executes
- [ ] `macro_trend_monitor` - Executes
- [ ] `news_impact_analysis` - Executes
- [ ] `policy_rebalance` - Executes (may have optimizer issues)
- [ ] `portfolio_cycle_risk` - Executes
- [ ] `portfolio_macro_overview` - Executes
- [ ] `portfolio_scenario_analysis` - Executes

## 5. UI/Browser Testing

### Chart Rendering
- [ ] Historical NAV chart displays correctly
- [ ] No JavaScript errors in console
- [ ] Sector allocation pie chart renders
- [ ] Currency attribution display works
- [ ] Data badge shows correct source (cached/real)

### Navigation
- [ ] Portfolio overview page loads
- [ ] Switching between pages works
- [ ] No broken API calls
- [ ] Authentication persists

## 6. Performance & Stability

### Memory & Resources
- [ ] No memory leaks after multiple pattern executions
- [ ] Server remains responsive
- [ ] Database connections properly released

### Error Handling
- [ ] Invalid pattern requests return appropriate errors
- [ ] Missing data handled gracefully
- [ ] Timeout handling works correctly

## Test Execution Commands

### Run Automated Test Suite
```bash
cd /home/runner/workspace
python backend/tests/validate_phase2_changes.py
```

### Monitor Server Logs
```bash
# Check for initialization errors
grep -E "ERROR|WARN|duplicate|already registered" /tmp/logs/DawsOS_*.log

# Check pattern execution
grep -E "Pattern .* completed|failed" /tmp/logs/DawsOS_*.log

# Check agent initialization
grep "Registered agent" /tmp/logs/DawsOS_*.log | wc -l  # Should be 9
```

### Test Individual Patterns via curl
```bash
# Test portfolio_overview
curl -X POST http://localhost:5000/api/patterns/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "portfolio_overview",
    "inputs": {"portfolio_id": "64ff3be6-0ed1-4990-a32b-4ded17f0320c"}
  }'

# Test corporate actions
curl -X GET "http://localhost:5000/api/corporate-actions?portfolio_id=64ff3be6-0ed1-4990-a32b-4ded17f0320c" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Success Criteria

✅ **All tests pass if:**
1. No double-nesting in pattern results
2. All 12 patterns execute without errors
3. No duplicate capability registration errors
4. Corporate actions endpoint validates portfolio_id
5. UI charts render correctly
6. Server remains stable

⚠️ **Acceptable warnings:**
- Optimizer stub data warnings (riskfolio not installed)
- Claude API key missing (uses stub responses)
- Some patterns may have missing optional data

❌ **Critical failures:**
- Any pattern fails to execute
- Double-nesting detected (result.result.data)
- Server crashes or hangs
- Charts don't render in UI
- Authentication failures

## Post-Testing Actions

1. **If all tests pass:**
   - Mark Phase 2 as complete
   - Commit changes
   - Consider deployment

2. **If critical failures:**
   - Review logs for root cause
   - Check specific pattern that failed
   - Verify template resolution
   - Review state storage in pattern_orchestrator.py

3. **If minor issues:**
   - Document in known issues
   - Create tickets for Phase 3
   - Proceed if not blocking

## Notes
- Auth token expires, regenerate if needed
- Some patterns require specific data (e.g., holdings for deep_dive)
- Policy_rebalance may fail due to optimizer limitations (acceptable)