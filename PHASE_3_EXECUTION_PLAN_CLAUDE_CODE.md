# Phase 3 Execution Plan: Agent Consolidation for Claude Code Agent

**Date:** November 3, 2025  
**Status:** ✅ **READY FOR EXECUTION**  
**Assigned To:** Claude Code Agent  
**Coordinated By:** Claude IDE Agent (PRIMARY)

---

## 📋 Executive Summary

Phase 3 involves consolidating 5 agents into 2 consolidated agents using feature flags for safe, gradual rollout. The system is ready with feature flags, capability routing, and dual registration implemented in Phase 2.

**Timeline:** 3-4 weeks (one agent per week)  
**Risk Level:** ⚠️ **LOW-MEDIUM** (with feature flags and gradual rollout)  
**Status:** Ready to begin Week 1 consolidation

---

## 🎯 Phase 3 Overview

### Consolidation Target: 9 Agents → 4 Agents

**Agents to Consolidate:**
1. **OptimizerAgent** → FinancialAnalyst (Week 1)
2. **RatingsAgent** → FinancialAnalyst (Week 2)
3. **ChartsAgent** → FinancialAnalyst (Week 3)
4. **AlertsAgent** → MacroHound (Week 4)
5. **ReportsAgent** → DataHarvester (Week 5)

**Agents to Keep:**
- FinancialAnalyst (enhanced with consolidated capabilities)
- MacroHound (enhanced with alerts)
- DataHarvester (enhanced with reports)
- ClaudeAgent (unchanged)

---

## 📊 Week 1: OptimizerAgent → FinancialAnalyst

**Timeline:** 1 week  
**Risk Level:** ⚠️ **MEDIUM** (trading decisions require careful migration)

### Capabilities to Consolidate

| Old Capability | New Capability | Risk Level | Dependencies |
|---------------|---------------|------------|--------------|
| `optimizer.propose_trades` | `financial_analyst.propose_trades` | High | `ledger.positions`, `pricing.apply_pack` |
| `optimizer.analyze_impact` | `financial_analyst.analyze_impact` | Medium | `ledger.positions` |
| `optimizer.suggest_hedges` | `financial_analyst.suggest_hedges` | Medium | `macro.run_scenario` |
| `optimizer.suggest_deleveraging_hedges` | `financial_analyst.suggest_deleveraging_hedges` | Medium | `macro.detect_regime` |

### Implementation Steps

#### Step 1: Implement Consolidated Capabilities in FinancialAnalyst (4-6 hours)

**File:** `backend/app/agents/financial_analyst.py`

**Tasks:**
1. ✅ Add consolidated capabilities to `get_capabilities()` (already done - lines 82-98)
2. ❌ **IMPLEMENT** `financial_analyst_propose_trades()` method
   - Copy logic from `optimizer_agent.py::optimizer_propose_trades()`
   - Update capability name references
   - Ensure service dependencies are correct
   - Test with sample portfolio
3. ❌ **IMPLEMENT** `financial_analyst_analyze_impact()` method
   - Copy logic from `optimizer_agent.py::optimizer_analyze_impact()`
   - Update capability name references
   - Test with sample trades
4. ❌ **IMPLEMENT** `financial_analyst_suggest_hedges()` method
   - Copy logic from `optimizer_agent.py::optimizer_suggest_hedges()`
   - Update capability name references
   - Test with sample scenarios
5. ❌ **IMPLEMENT** `financial_analyst_suggest_deleveraging_hedges()` method
   - Copy logic from `optimizer_agent.py::optimizer_suggest_deleveraging_hedges()`
   - Update capability name references
   - Test with sample regimes

**Code Structure:**
```python
async def financial_analyst_propose_trades(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    policy_json: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Generate rebalance trade proposals based on policy constraints.
    
    Capability: financial_analyst.propose_trades
    (Consolidated from optimizer.propose_trades)
    
    Args:
        ctx: Request context
        state: Execution state
        portfolio_id: Portfolio UUID
        policy_json: Policy constraints dict
        **kwargs: Additional arguments
    
    Returns:
        Dict with trades, trade_count, total_value, etc.
    """
    # Implementation: Copy from OptimizerAgent
    # Service: get_optimizer_service()
    # Dependencies: ledger.positions, pricing.apply_pack
    pass
```

**Key Files to Reference:**
- `backend/app/agents/optimizer_agent.py` - Source implementation
- `backend/app/services/optimizer.py` - Service layer
- `backend/app/core/capability_mapping.py` - Capability mappings (already defined)

#### Step 2: Update Agent Registration (30 min)

**File:** `backend/combined_server.py`

**Tasks:**
1. Ensure FinancialAnalyst is registered with priority 50 (for consolidation)
2. Ensure OptimizerAgent is registered with priority 100 (default)
3. Verify dual registration is enabled

**Code Check:**
```python
# FinancialAnalyst should be registered with priority 50
runtime.register_agent(
    FinancialAnalyst("financial_analyst", services),
    priority=50,  # Higher priority for consolidated capabilities
    allow_dual_registration=True
)

# OptimizerAgent should be registered with priority 100
runtime.register_agent(
    OptimizerAgent("optimizer_agent", services),
    priority=100,  # Lower priority (will be overridden by feature flags)
    allow_dual_registration=True
)
```

#### Step 3: Enable Feature Flag for Gradual Rollout (10 min)

**File:** `backend/config/feature_flags.json`

**Week 1 Process:**
1. **Day 1-2:** Enable at 10% rollout
   ```json
   {
     "agent_consolidation": {
       "optimizer_to_financial": {
         "enabled": true,
         "rollout_percentage": 10
       }
     }
   }
   ```
2. **Day 3-4:** Increase to 50% rollout
   ```json
   {
     "rollout_percentage": 50
   }
   ```
3. **Day 5-7:** Increase to 100% rollout
   ```json
   {
     "rollout_percentage": 100
   }
   ```

#### Step 4: Testing and Validation (2-3 hours)

**Test Cases:**
1. ✅ Test `financial_analyst.propose_trades` with sample portfolio
2. ✅ Test `financial_analyst.analyze_impact` with sample trades
3. ✅ Test `financial_analyst.suggest_hedges` with sample scenarios
4. ✅ Test `financial_analyst.suggest_deleveraging_hedges` with sample regimes
5. ✅ Test feature flag routing (10% → 50% → 100%)
6. ✅ Test rollback (disable flag, verify old agent works)
7. ✅ Test pattern execution (`policy_rebalance.json`)
8. ✅ Test API endpoint (`/api/optimize`)

**Validation Checklist:**
- [ ] All consolidated capabilities work correctly
- [ ] Feature flag routing works (10% → 50% → 100%)
- [ ] Rollback works (disable flag, old agent works)
- [ ] Pattern execution works (`policy_rebalance.json`)
- [ ] API endpoint works (`/api/optimize`)
- [ ] No errors in logs
- [ ] Performance is acceptable

#### Step 5: Monitor for 1 Week (Ongoing)

**Monitoring Tasks:**
1. Check logs for routing decisions
2. Monitor error rates
3. Watch response times
4. Gather user feedback
5. Keep old agent running as fallback

**After 1 Week:**
- If stable: Keep at 100%, proceed to Week 2
- If issues: Rollback to 0%, debug, fix, retry

---

## 📊 Week 2: RatingsAgent → FinancialAnalyst

**Timeline:** 1 week  
**Risk Level:** ✅ **LOW** (read-only ratings, no trading logic)

### Capabilities to Consolidate

| Old Capability | New Capability | Risk Level | Dependencies |
|---------------|---------------|------------|--------------|
| `ratings.dividend_safety` | `financial_analyst.dividend_safety` | Low | `provider.fetch_fundamentals` |
| `ratings.moat_strength` | `financial_analyst.moat_strength` | Low | `provider.fetch_fundamentals` |
| `ratings.resilience` | `financial_analyst.resilience` | Low | `provider.fetch_fundamentals` |
| `ratings.aggregate` | `financial_analyst.aggregate_ratings` | Low | All three ratings above |

### Implementation Steps

#### Step 1: Implement Consolidated Capabilities (3-4 hours)

**File:** `backend/app/agents/financial_analyst.py`

**Tasks:**
1. ❌ **IMPLEMENT** `financial_analyst_dividend_safety()` method
2. ❌ **IMPLEMENT** `financial_analyst_moat_strength()` method
3. ❌ **IMPLEMENT** `financial_analyst_resilience()` method
4. ❌ **IMPLEMENT** `financial_analyst_aggregate_ratings()` method

**Reference Files:**
- `backend/app/agents/ratings_agent.py` - Source implementation
- `backend/app/services/ratings.py` - Service layer

#### Step 2: Enable Feature Flag (10 min)

**File:** `backend/config/feature_flags.json`

```json
{
  "agent_consolidation": {
    "ratings_to_financial": {
      "enabled": true,
      "rollout_percentage": 10
    }
  }
}
```

#### Step 3: Testing and Validation (1-2 hours)

**Test Cases:**
1. ✅ Test all four consolidated capabilities
2. ✅ Test feature flag routing
3. ✅ Test pattern execution (`buffett_checklist.json`)
4. ✅ Test API endpoints (`/api/ratings/overview`, `/api/ratings/buffett`)

#### Step 4: Monitor for 1 Week

Same monitoring process as Week 1.

---

## 📊 Week 3: ChartsAgent → FinancialAnalyst

**Timeline:** 1 week  
**Risk Level:** ✅ **LOW** (pure formatting, no complex logic)

### Capabilities to Consolidate

| Old Capability | New Capability | Risk Level | Dependencies |
|---------------|---------------|------------|--------------|
| `charts.macro_overview` | `financial_analyst.macro_overview_charts` | Low | `macro.detect_regime` |
| `charts.scenario_deltas` | `financial_analyst.scenario_charts` | Low | `macro.run_scenario` |

### Implementation Steps

#### Step 1: Implement Consolidated Capabilities (2-3 hours)

**File:** `backend/app/agents/financial_analyst.py`

**Tasks:**
1. ❌ **IMPLEMENT** `financial_analyst_macro_overview_charts()` method
2. ❌ **IMPLEMENT** `financial_analyst_scenario_charts()` method

**Reference Files:**
- `backend/app/agents/charts_agent.py` - Source implementation

#### Step 2: Enable Feature Flag (10 min)

**File:** `backend/config/feature_flags.json`

```json
{
  "agent_consolidation": {
    "charts_to_financial": {
      "enabled": true,
      "rollout_percentage": 10
    }
  }
}
```

#### Step 3: Testing and Validation (1-2 hours)

**Test Cases:**
1. ✅ Test both consolidated capabilities
2. ✅ Test feature flag routing
3. ✅ Test pattern execution (`portfolio_macro_overview.json`, `portfolio_scenario_analysis.json`)

#### Step 4: Monitor for 1 Week

Same monitoring process as Week 1.

---

## 📊 Week 4: AlertsAgent → MacroHound

**Timeline:** 1 week  
**Risk Level:** ⚠️ **MEDIUM** (alert creation logic)

### Capabilities to Consolidate

| Old Capability | New Capability | Risk Level | Dependencies |
|---------------|---------------|------------|--------------|
| `alerts.suggest_presets` | `macro_hound.suggest_alerts` | Medium | `macro.detect_trend_shifts` |
| `alerts.create_if_threshold` | `macro_hound.create_alert` | Medium | `news.compute_portfolio_impact` |

### Implementation Steps

#### Step 1: Implement Consolidated Capabilities in MacroHound (3-4 hours)

**File:** `backend/app/agents/macro_hound.py`

**Tasks:**
1. ❌ **IMPLEMENT** `macro_hound_suggest_alerts()` method
2. ❌ **IMPLEMENT** `macro_hound_create_alert()` method

**Reference Files:**
- `backend/app/agents/alerts_agent.py` - Source implementation
- `backend/app/services/playbooks.py` - PlaybookGenerator

#### Step 2: Update Agent Registration (30 min)

**File:** `backend/combined_server.py`

Register MacroHound with priority 50 for consolidation.

#### Step 3: Enable Feature Flag (10 min)

**File:** `backend/config/feature_flags.json`

```json
{
  "agent_consolidation": {
    "alerts_to_macro": {
      "enabled": true,
      "rollout_percentage": 10
    }
  }
}
```

#### Step 4: Testing and Validation (1-2 hours)

**Test Cases:**
1. ✅ Test both consolidated capabilities
2. ✅ Test feature flag routing
3. ✅ Test pattern execution (`macro_trend_monitor.json`, `news_impact_analysis.json`)

#### Step 5: Monitor for 1 Week

Same monitoring process as Week 1.

---

## 📊 Week 5: ReportsAgent → DataHarvester

**Timeline:** 1 week  
**Risk Level:** ✅ **LOW** (report generation, no trading logic)

### Capabilities to Consolidate

| Old Capability | New Capability | Risk Level | Dependencies |
|---------------|---------------|------------|--------------|
| `reports.render_pdf` | `data_harvester.render_pdf` | Low | ReportService |
| `reports.export_csv` | `data_harvester.export_csv` | Low | ReportService |
| `reports.export_excel` | `data_harvester.export_excel` | Low | ReportService |

### Implementation Steps

#### Step 1: Implement Consolidated Capabilities (2-3 hours)

**File:** `backend/app/agents/data_harvester.py`

**Tasks:**
1. ❌ **IMPLEMENT** `data_harvester_render_pdf()` method
2. ❌ **IMPLEMENT** `data_harvester_export_csv()` method
3. ❌ **IMPLEMENT** `data_harvester_export_excel()` method

**Reference Files:**
- `backend/app/agents/reports_agent.py` - Source implementation
- `backend/app/services/reports.py` - ReportService

#### Step 2: Enable Feature Flag (10 min)

**File:** `backend/config/feature_flags.json`

```json
{
  "agent_consolidation": {
    "reports_to_financial": {
      "enabled": true,
      "rollout_percentage": 10
    }
  }
}
```

#### Step 3: Testing and Validation (1-2 hours)

**Test Cases:**
1. ✅ Test all three consolidated capabilities
2. ✅ Test feature flag routing
3. ✅ Test pattern execution (`export_portfolio_report.json`)
4. ✅ Test API endpoint (`/api/reports`)

#### Step 4: Monitor for 1 Week

Same monitoring process as Week 1.

---

## 🧹 Week 6: Cleanup (Optional)

**Timeline:** 1 week  
**Risk Level:** ✅ **LOW** (after all consolidations stable)

### Cleanup Tasks

1. **Remove Old Agent Files** (after 1 week of stability at 100%)
   - ❌ Delete `backend/app/agents/optimizer_agent.py`
   - ❌ Delete `backend/app/agents/ratings_agent.py`
   - ❌ Delete `backend/app/agents/charts_agent.py`
   - ❌ Delete `backend/app/agents/alerts_agent.py`
   - ❌ Delete `backend/app/agents/reports_agent.py`

2. **Update Agent Registration** (30 min)
   - ❌ Remove old agent registrations from `combined_server.py`

3. **Update Documentation** (1 hour)
   - ❌ Update `ARCHITECTURE.md` with new agent structure
   - ❌ Update `PATTERNS_REFERENCE.md` if needed
   - ❌ Update any other documentation referencing old agents

4. **Final Testing** (2 hours)
   - ✅ Test all patterns execute correctly
   - ✅ Test all API endpoints work
   - ✅ Verify no references to old agents remain

---

## 📋 Implementation Checklist Template (Per Week)

### Pre-Implementation
- [ ] Read shared memory (`AGENT_CONVERSATION_MEMORY.md`)
- [ ] Review capability mappings (`backend/app/core/capability_mapping.py`)
- [ ] Review source agent implementation
- [ ] Review service dependencies
- [ ] Understand feature flag system

### Implementation
- [ ] Implement consolidated capabilities in target agent
- [ ] Update agent registration (priority 50)
- [ ] Test consolidated capabilities locally
- [ ] Verify service dependencies work
- [ ] Check for any breaking changes

### Feature Flag Rollout
- [ ] Enable feature flag at 10% rollout
- [ ] Monitor for 24-48 hours
- [ ] Increase to 50% rollout
- [ ] Monitor for 24 hours
- [ ] Increase to 100% rollout
- [ ] Monitor for 1 week

### Testing
- [ ] Test all consolidated capabilities
- [ ] Test feature flag routing (10% → 50% → 100%)
- [ ] Test rollback (disable flag)
- [ ] Test pattern execution
- [ ] Test API endpoints
- [ ] Check logs for errors
- [ ] Verify performance

### Documentation
- [ ] Update shared memory with status
- [ ] Document any issues found
- [ ] Document any changes needed
- [ ] Report completion status

---

## ⚠️ Risk Mitigation

### Risk 1: Consolidated Capabilities Don't Work
**Mitigation:**
- Test thoroughly before enabling feature flag
- Keep old agent running as fallback
- Use gradual rollout (10% → 50% → 100%)
- Monitor logs closely

### Risk 2: Feature Flag Routing Fails
**Mitigation:**
- Test feature flag system before consolidation
- Verify capability mapping is correct
- Test rollback mechanism
- Monitor routing decisions in logs

### Risk 3: Service Dependencies Break
**Mitigation:**
- Review service dependencies before implementation
- Test service calls independently
- Verify service initialization order
- Check for any service-level changes needed

### Risk 4: Pattern Execution Fails
**Mitigation:**
- Test all affected patterns after consolidation
- Verify capability names in patterns match new names
- Check for any hardcoded agent references
- Test with sample data

### Risk 5: Performance Degradation
**Mitigation:**
- Monitor response times during rollout
- Compare before/after performance metrics
- Check for any inefficient code paths
- Optimize if needed

---

## 📊 Success Criteria

### Week 1 (OptimizerAgent)
- ✅ All 4 consolidated capabilities work correctly
- ✅ Feature flag routing works (10% → 50% → 100%)
- ✅ Pattern `policy_rebalance.json` executes successfully
- ✅ API endpoint `/api/optimize` works correctly
- ✅ No errors in logs
- ✅ Performance is acceptable

### Week 2 (RatingsAgent)
- ✅ All 4 consolidated capabilities work correctly
- ✅ Pattern `buffett_checklist.json` executes successfully
- ✅ API endpoints `/api/ratings/*` work correctly

### Week 3 (ChartsAgent)
- ✅ All 2 consolidated capabilities work correctly
- ✅ Patterns `portfolio_macro_overview.json` and `portfolio_scenario_analysis.json` execute successfully

### Week 4 (AlertsAgent)
- ✅ All 2 consolidated capabilities work correctly
- ✅ Patterns `macro_trend_monitor.json` and `news_impact_analysis.json` execute successfully

### Week 5 (ReportsAgent)
- ✅ All 3 consolidated capabilities work correctly
- ✅ Pattern `export_portfolio_report.json` executes successfully
- ✅ API endpoint `/api/reports` works correctly

### Week 6 (Cleanup)
- ✅ All old agent files removed
- ✅ All patterns execute correctly
- ✅ All API endpoints work
- ✅ Documentation updated

---

## 🎯 Next Steps

1. **Claude Code Agent:** Begin Week 1 implementation (OptimizerAgent consolidation)
2. **Claude IDE Agent:** Review and validate implementation
3. **Replit Agent:** Test and validate in production environment
4. **All Agents:** Update shared memory with progress

---

**Created:** November 3, 2025  
**Status:** ✅ **READY FOR EXECUTION**  
**Next Step:** Claude Code Agent begins Week 1 implementation

