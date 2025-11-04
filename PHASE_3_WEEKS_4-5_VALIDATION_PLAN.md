# Phase 3 Weeks 4-5 Validation Plan

**Date:** November 3, 2025  
**Validator:** Claude IDE Agent (PRIMARY)  
**Purpose:** Comprehensive validation plan for Weeks 4-5 consolidations  
**Status:** ✅ **PLAN COMPLETE - Ready for Execution**

---

## 📊 Executive Summary

This plan validates the implemented consolidations for Weeks 4-5:
- **Week 4:** AlertsAgent → MacroHound (2 capabilities)
- **Week 5:** ReportsAgent → DataHarvester (3 capabilities)

**Validation Approach:**
- Phase 1: Code Review & Static Analysis (30 minutes)
- Phase 2: Capability Testing (1-2 hours)
- Phase 3: Pattern Execution Testing (1 hour)
- Phase 4: Feature Flag Routing Validation (30 minutes)
- Phase 5: Cleanup Validation (30 minutes)
- Phase 6: Integration Testing (1 hour)

**Total Estimated Time:** 4-5 hours  
**Risk Level:** ✅ **LOW** (methods exist, need validation)

---

## 🎯 Validation Objectives

### Week 4: AlertsAgent → MacroHound

**Capabilities to Validate:**
1. `macro_hound.suggest_alert_presets` (consolidated from `alerts.suggest_presets`)
2. `macro_hound.create_alert_if_threshold` (consolidated from `alerts.create_if_threshold`)

**Success Criteria:**
- ✅ Methods exist and are properly implemented
- ✅ Feature flag routing works correctly
- ✅ Pattern execution succeeds
- ✅ Output format matches AlertsAgent (functional equivalence)
- ✅ AlertsAgent cleanup opportunities identified

### Week 5: ReportsAgent → DataHarvester

**Capabilities to Validate:**
1. `data_harvester.render_pdf` (consolidated from `reports.render_pdf`)
2. `data_harvester.export_csv` (consolidated from `reports.export_csv`)
3. `data_harvester.export_excel` (consolidated from `reports.export_excel`)

**Success Criteria:**
- ✅ Methods exist and are properly implemented
- ✅ Feature flag routing works correctly
- ✅ Pattern execution succeeds
- ✅ Safety features work (timeouts, size limits)
- ✅ Output format matches ReportsAgent (functional equivalence)
- ✅ ReportsAgent cleanup opportunities identified

---

## 📋 Phase 1: Code Review & Static Analysis (30 minutes)

### Task 1.1: Verify Method Signatures Match

**Week 4: AlertsAgent → MacroHound**

**Files to Compare:**
- `backend/app/agents/alerts_agent.py` (source)
- `backend/app/agents/macro_hound.py` (target)

**Checks:**
1. ✅ `macro_hound_suggest_alert_presets()` signature matches `alerts_suggest_presets()`
   - Parameters: `ctx`, `state`, `trend_analysis`, `portfolio_id`
   - Return type: `Dict[str, Any]`
   - Return structure: `{suggestions: [...], count: int}`

2. ✅ `macro_hound_create_alert_if_threshold()` signature matches `alerts_create_if_threshold()`
   - Parameters: `ctx`, `state`, `portfolio_id`, `news_impact`, `threshold`
   - Return type: `Dict[str, Any]`
   - Return structure: `{alert_created: bool, alert_id: str, ...}`

**Validation Steps:**
```python
# Compare method signatures
grep -A 5 "async def alerts_suggest_presets" backend/app/agents/alerts_agent.py
grep -A 5 "async def macro_hound_suggest_alert_presets" backend/app/agents/macro_hound.py

# Compare return structures
grep -A 20 "return {" backend/app/agents/alerts_agent.py | grep -A 10 "suggestions"
grep -A 20 "return {" backend/app/agents/macro_hound.py | grep -A 10 "suggestions"
```

**Week 5: ReportsAgent → DataHarvester**

**Files to Compare:**
- `backend/app/agents/reports_agent.py` (source)
- `backend/app/agents/data_harvester.py` (target)

**Checks:**
1. ✅ `data_harvester_render_pdf()` signature matches `reports_render_pdf()`
   - Parameters: `ctx`, `state`, `template_name`, `report_data`, `portfolio_id`, `**kwargs`
   - Return type: `Dict[str, Any]`
   - Return structure: `{pdf_base64: str, size_bytes: int, attributions: [...], ...}`

2. ✅ `data_harvester_export_csv()` signature matches `reports_export_csv()`
   - Parameters: `ctx`, `state`, `filename`, `data`, `providers`, `**kwargs`
   - Return type: `Dict[str, Any]`
   - Return structure: `{csv_base64: str, size_bytes: int, filename: str, ...}`

3. ✅ `data_harvester_export_excel()` exists (may be stub)

**Validation Steps:**
```python
# Compare method signatures
grep -A 5 "async def reports_render_pdf" backend/app/agents/reports_agent.py
grep -A 5 "async def data_harvester_render_pdf" backend/app/agents/data_harvester.py

# Check for safety features
grep -A 5 "EXPORT_TIMEOUT\|MAX_PDF_SIZE\|STREAMING_THRESHOLD" backend/app/agents/data_harvester.py
```

### Task 1.2: Verify Service Dependencies

**Week 4: AlertsAgent → MacroHound**

**Expected Dependencies:**
- `PlaybookGenerator` (from `app.services.playbooks`)
- `AlertService` (if used)

**Checks:**
- ✅ Import statements exist
- ✅ Service instantiation correct
- ✅ Service methods called correctly

**Week 5: ReportsAgent → DataHarvester**

**Expected Dependencies:**
- `ReportService` (from `app.services.reports`)
- `RightsRegistry` (for attributions)

**Checks:**
- ✅ Import statements exist
- ✅ Service instantiation correct
- ✅ Safety features implemented (timeout, size limits)

### Task 1.3: Verify BaseAgent Helper Usage

**Week 4: AlertsAgent**

**Checks:**
- ❌ Verify AlertsAgent uses `self.CACHE_TTL_*` constants (or hardcoded values)
- ❌ Verify AlertsAgent uses `self._resolve_asof_date()` (or direct `ctx.asof_date`)
- ❌ Identify cleanup opportunities

**Week 5: ReportsAgent**

**Checks:**
- ❌ Verify ReportsAgent uses `self.CACHE_TTL_*` constants (or hardcoded values)
- ❌ Verify ReportsAgent uses `self._resolve_asof_date()` (or direct `ctx.asof_date`)
- ❌ Identify cleanup opportunities

**Expected Findings:**
- AlertsAgent: May not use BaseAgent helpers (needs extraction)
- ReportsAgent: May not use BaseAgent helpers (needs extraction)

---

## 📋 Phase 2: Capability Testing (1-2 hours)

### Task 2.1: Test Week 4 Capabilities

**Test 2.1.1: `macro_hound.suggest_alert_presets`**

**Test Setup:**
```python
# Mock context
ctx = RequestCtx(
    user_id="test_user",
    portfolio_id="test_portfolio",
    asof_date=date.today()
)

# Mock state
state = {
    "trend_analysis": {
        "regime_shift_detected": True,
        "old_regime": "Expansion",
        "new_regime": "Slowdown",
        "confidence": 0.85,
        "dar_increasing": True,
        "dar_change_pct": 0.15,
        "current_dar": 0.12
    }
}

# Test parameters
trend_analysis = state["trend_analysis"]
portfolio_id = "test_portfolio"
```

**Validation Checks:**
1. ✅ Method executes without errors
2. ✅ Returns correct structure: `{suggestions: [...], count: int}`
3. ✅ Suggestions contain expected fields: `type`, `priority`, `condition`, `playbook`
4. ✅ Regime shift suggestion created when `regime_shift_detected = True`
5. ✅ DaR increase suggestion created when `dar_increasing = True`
6. ✅ Metadata attached correctly
7. ✅ TTL set appropriately (should use `CACHE_TTL_HOUR`)

**Test 2.1.2: `macro_hound.create_alert_if_threshold`**

**Test Setup:**
```python
# Mock context
ctx = RequestCtx(
    user_id="test_user",
    portfolio_id="test_portfolio",
    asof_date=date.today()
)

# Mock state
state = {
    "news_impact": {
        "total_impact_pct": 0.08,  # 8% impact (above threshold)
        "impact_by_security": [...],
        "high_impact_count": 3
    }
}

# Test parameters
portfolio_id = "test_portfolio"
news_impact = state["news_impact"]
threshold = 0.05  # 5% threshold
```

**Validation Checks:**
1. ✅ Method executes without errors
2. ✅ Returns correct structure: `{alert_created: bool, alert_id: str, ...}`
3. ✅ Alert created when `total_impact_pct > threshold`
4. ✅ Alert NOT created when `total_impact_pct <= threshold`
5. ✅ Alert ID returned when alert created
6. ✅ Metadata attached correctly
7. ✅ TTL set appropriately (should use `CACHE_TTL_NONE` for alerts)

### Task 2.2: Test Week 5 Capabilities

**Test 2.2.1: `data_harvester.render_pdf`**

**Test Setup:**
```python
# Mock context
ctx = RequestCtx(
    user_id="test_user",
    portfolio_id="test_portfolio",
    pricing_pack_id="PP_test",
    asof_date=date.today()
)

# Mock state
state = {
    "portfolio_id": "test_portfolio",
    "positions": [...],
    "metrics": {...}
}

# Test parameters
template_name = "portfolio_summary"
report_data = None  # Use state
portfolio_id = "test_portfolio"
```

**Validation Checks:**
1. ✅ Method executes without errors
2. ✅ Returns correct structure: `{pdf_base64: str, size_bytes: int, status: "success", ...}`
3. ✅ PDF generated successfully (base64 encoded)
4. ✅ File size within limits (< 10MB)
5. ✅ Timeout protection works (test with slow operation)
6. ✅ Size limit protection works (test with large data)
7. ✅ Metadata attached correctly
8. ✅ Attributions included
9. ✅ Watermark applied if needed
10. ✅ Error handling works (returns structured error on failure)

**Test 2.2.2: `data_harvester.export_csv`**

**Test Setup:**
```python
# Mock context
ctx = RequestCtx(
    user_id="test_user",
    portfolio_id="test_portfolio",
    asof_date=date.today()
)

# Mock state
state = {
    "positions": [...],
    "metrics": {...}
}

# Test parameters
filename = "test_export.csv"
data = None  # Use state
providers = ["FMP", "Polygon"]
```

**Validation Checks:**
1. ✅ Method executes without errors
2. ✅ Returns correct structure: `{csv_base64: str, size_bytes: int, filename: str, status: "success", ...}`
3. ✅ CSV generated successfully (base64 encoded)
4. ✅ File size within limits (< 30MB)
5. ✅ Timeout protection works (10s timeout)
6. ✅ Size limit protection works (test with large data)
7. ✅ Metadata attached correctly
8. ✅ Attributions included
9. ✅ Error handling works (returns structured error on failure)

**Test 2.2.3: `data_harvester.export_excel`**

**Validation Checks:**
1. ✅ Method exists
2. ✅ Returns error message if not implemented: `{status: "error", reason: "not_implemented", ...}`
3. ✅ Provides helpful suggestion: "Use CSV export instead"

---

## 📋 Phase 3: Pattern Execution Testing (1 hour)

### Task 3.1: Test Week 4 Patterns

**Pattern 3.1.1: `macro_trend_monitor.json`**

**Pattern Uses:**
- `alerts.suggest_presets` (should route to `macro_hound.suggest_alert_presets`)

**Validation Steps:**
1. ✅ Load pattern file
2. ✅ Execute pattern via `PatternOrchestrator.run_pattern()`
3. ✅ Verify capability routing: `alerts.suggest_presets` → `macro_hound.suggest_alert_presets`
4. ✅ Verify pattern execution succeeds
5. ✅ Verify result contains `suggestions` array
6. ✅ Verify no errors in logs

**Pattern 3.1.2: `news_impact_analysis.json`**

**Pattern Uses:**
- `alerts.create_if_threshold` (should route to `macro_hound.create_alert_if_threshold`)

**Validation Steps:**
1. ✅ Load pattern file
2. ✅ Execute pattern via `PatternOrchestrator.run_pattern()`
3. ✅ Verify capability routing: `alerts.create_if_threshold` → `macro_hound.create_alert_if_threshold`
4. ✅ Verify pattern execution succeeds
5. ✅ Verify result contains `alert_created` boolean
6. ✅ Verify no errors in logs

### Task 3.2: Test Week 5 Patterns

**Pattern 3.2.1: `export_portfolio_report.json`**

**Pattern Uses:**
- `reports.render_pdf` (should route to `data_harvester.render_pdf`)

**Validation Steps:**
1. ✅ Load pattern file
2. ✅ Execute pattern via `PatternOrchestrator.run_pattern()`
3. ✅ Verify capability routing: `reports.render_pdf` → `data_harvester.render_pdf`
4. ✅ Verify pattern execution succeeds
5. ✅ Verify result contains `pdf_base64` string
6. ✅ Verify PDF size is reasonable (< 10MB)
7. ✅ Verify no errors in logs

---

## 📋 Phase 4: Feature Flag Routing Validation (30 minutes)

### Task 4.1: Verify Feature Flag Configuration

**Week 4: AlertsAgent → MacroHound**

**Checks:**
1. ✅ Feature flag `alerts_to_macro` exists in `feature_flags.json`
2. ✅ Feature flag enabled: `true`
3. ✅ Rollout percentage: `100`
4. ✅ Capability mapping exists in `capability_mapping.py`
5. ✅ Routing logic in `agent_runtime.py` handles `alerts.*` → `macro_hound.*`

**Week 5: ReportsAgent → DataHarvester**

**Checks:**
1. ✅ Feature flag `reports_to_data_harvester` exists in `feature_flags.json`
2. ✅ Feature flag enabled: `true`
3. ✅ Rollout percentage: `100`
4. ✅ Capability mapping exists in `capability_mapping.py`
5. ✅ Routing logic in `agent_runtime.py` handles `reports.*` → `data_harvester.*`

### Task 4.2: Test Feature Flag Routing

**Test 4.2.1: Test Week 4 Routing**

**Test Cases:**
1. ✅ Call `alerts.suggest_presets` → Should route to `macro_hound.suggest_alert_presets`
2. ✅ Call `alerts.create_if_threshold` → Should route to `macro_hound.create_alert_if_threshold`
3. ✅ Verify routing decision logged correctly
4. ✅ Verify fallback to AlertsAgent if feature flag disabled (rollback test)

**Test 4.2.2: Test Week 5 Routing**

**Test Cases:**
1. ✅ Call `reports.render_pdf` → Should route to `data_harvester.render_pdf`
2. ✅ Call `reports.export_csv` → Should route to `data_harvester.export_csv`
3. ✅ Call `reports.export_excel` → Should route to `data_harvester.export_excel`
4. ✅ Verify routing decision logged correctly
5. ✅ Verify fallback to ReportsAgent if feature flag disabled (rollback test)

---

## 📋 Phase 5: Cleanup Validation (30 minutes)

### Task 5.1: Identify AlertsAgent Cleanup Opportunities

**Checks:**
1. ✅ Review AlertsAgent for hardcoded TTL values
2. ✅ Review AlertsAgent for direct `ctx.asof_date` usage
3. ✅ Review AlertsAgent for UUID conversion patterns
4. ✅ Identify patterns that should use BaseAgent helpers

**Expected Cleanup:**
- Extract TTL constants usage (if any)
- Extract asof date resolution (if any)
- Extract UUID conversion (if any)

### Task 5.2: Identify ReportsAgent Cleanup Opportunities

**Checks:**
1. ✅ Review ReportsAgent for hardcoded TTL values
2. ✅ Review ReportsAgent for direct `ctx.asof_date` usage
3. ✅ Review ReportsAgent for UUID conversion patterns
4. ✅ Identify patterns that should use BaseAgent helpers

**Expected Cleanup:**
- Extract TTL constants usage (if any)
- Extract asof date resolution (if any)
- Extract UUID conversion (if any)

---

## 📋 Phase 6: Integration Testing (1 hour)

### Task 6.1: End-to-End Pattern Execution

**Test Full Patterns:**
1. ✅ Execute `macro_trend_monitor.json` end-to-end
2. ✅ Execute `news_impact_analysis.json` end-to-end
3. ✅ Execute `export_portfolio_report.json` end-to-end
4. ✅ Verify all steps execute successfully
5. ✅ Verify final results are correct
6. ✅ Verify no errors in logs

### Task 6.2: API Endpoint Testing

**Test API Endpoints:**
1. ✅ Test `/api/patterns/macro_trend_monitor` endpoint
2. ✅ Test `/api/patterns/news_impact_analysis` endpoint
3. ✅ Test `/api/patterns/export_portfolio_report` endpoint
4. ✅ Test `/api/reports` endpoint (if exists)
5. ✅ Verify responses are correct
6. ✅ Verify error handling works

### Task 6.3: Performance Testing

**Checks:**
1. ✅ Verify response times are acceptable
2. ✅ Verify memory usage is reasonable
3. ✅ Verify timeout protection works
4. ✅ Verify size limit protection works

---

## 📊 Validation Checklist

### Week 4: AlertsAgent → MacroHound

**Code Review:**
- [ ] Method signatures match
- [ ] Service dependencies correct
- [ ] BaseAgent helper usage identified

**Capability Testing:**
- [ ] `macro_hound.suggest_alert_presets` works
- [ ] `macro_hound.create_alert_if_threshold` works
- [ ] Output format matches AlertsAgent

**Pattern Execution:**
- [ ] `macro_trend_monitor.json` executes successfully
- [ ] `news_impact_analysis.json` executes successfully

**Feature Flag Routing:**
- [ ] Routing works correctly
- [ ] Rollback works correctly

**Cleanup:**
- [ ] AlertsAgent cleanup opportunities identified

### Week 5: ReportsAgent → DataHarvester

**Code Review:**
- [ ] Method signatures match
- [ ] Service dependencies correct
- [ ] Safety features implemented
- [ ] BaseAgent helper usage identified

**Capability Testing:**
- [ ] `data_harvester.render_pdf` works
- [ ] `data_harvester.export_csv` works
- [ ] `data_harvester.export_excel` handles stub correctly
- [ ] Timeout protection works
- [ ] Size limit protection works
- [ ] Output format matches ReportsAgent

**Pattern Execution:**
- [ ] `export_portfolio_report.json` executes successfully

**Feature Flag Routing:**
- [ ] Routing works correctly
- [ ] Rollback works correctly

**Cleanup:**
- [ ] ReportsAgent cleanup opportunities identified

---

## 🎯 Success Criteria

### Must Pass (Critical)
- ✅ All consolidated methods exist and are properly implemented
- ✅ Feature flag routing works correctly
- ✅ Pattern execution succeeds
- ✅ No runtime errors
- ✅ Safety features work (timeouts, size limits)

### Should Pass (Important)
- ✅ Output format matches legacy agents (functional equivalence)
- ✅ Performance is acceptable
- ✅ Error handling works correctly
- ✅ Cleanup opportunities identified

### Can Have Warnings (Acceptable)
- ⚠️ Excel export not implemented (documented stub)
- ⚠️ Some edge cases may need additional testing

---

## 📋 Execution Plan

### Step 1: Code Review (30 minutes)
1. Read and compare method signatures
2. Verify service dependencies
3. Identify cleanup opportunities
4. Document findings

### Step 2: Capability Testing (1-2 hours)
1. Create test cases for each capability
2. Execute tests manually or via test script
3. Verify output format and functionality
4. Document results

### Step 3: Pattern Execution (1 hour)
1. Load pattern files
2. Execute patterns via PatternOrchestrator
3. Verify routing and execution
4. Document results

### Step 4: Feature Flag Validation (30 minutes)
1. Verify feature flag configuration
2. Test routing logic
3. Test rollback scenario
4. Document results

### Step 5: Cleanup Validation (30 minutes)
1. Review legacy agents for cleanup opportunities
2. Document findings
3. Create cleanup plan

### Step 6: Integration Testing (1 hour)
1. Execute full patterns end-to-end
2. Test API endpoints
3. Test performance
4. Document results

---

## 🚨 Risk Assessment

### Low Risk ✅
- Methods exist and are implemented
- Feature flags are configured
- Patterns are simple

### Medium Risk ⚠️
- Safety features need validation (timeouts, size limits)
- Performance may vary with large datasets
- Error handling needs testing

### Mitigation Strategies
1. Test with small datasets first
2. Test timeout scenarios with delays
3. Test size limit scenarios with large data
4. Verify error messages are helpful

---

## 📊 Expected Findings

### Week 4: AlertsAgent → MacroHound

**Expected Status:**
- ✅ Methods properly implemented
- ✅ Feature flag routing works
- ✅ Patterns execute successfully
- ⚠️ AlertsAgent may need BaseAgent helper extraction

**Expected Issues:**
- None (methods exist, should work)

### Week 5: ReportsAgent → DataHarvester

**Expected Status:**
- ✅ Methods properly implemented
- ✅ Safety features implemented
- ✅ Feature flag routing works
- ✅ Patterns execute successfully
- ⚠️ Excel export is stub (documented)
- ⚠️ ReportsAgent may need BaseAgent helper extraction

**Expected Issues:**
- Excel export not implemented (expected)

---

## 📋 Validation Report Template

After validation, create a report with:

1. **Executive Summary**
   - Overall status
   - Key findings
   - Recommendations

2. **Detailed Findings**
   - Week 4 validation results
   - Week 5 validation results
   - Cleanup opportunities

3. **Test Results**
   - Capability tests
   - Pattern execution tests
   - Feature flag routing tests

4. **Recommendations**
   - Cleanup tasks
   - Next steps
   - Risk assessment

---

**Last Updated:** November 3, 2025  
**Status:** ✅ **PLAN COMPLETE - Ready for Execution**

