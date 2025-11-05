# Phase 3 Week 3: ChartsAgent Consolidation - Rollout Checklist

**Date Created:** November 3, 2025  
**Target Rollout:** Week of November 11-15, 2025  
**Status:** ✅ READY FOR GRADUAL ROLLOUT  
**Feature Flag:** `charts_to_financial`

---

## 📊 Executive Summary

ChartsAgent consolidation into FinancialAnalyst is complete with 100% functional equivalence confirmed. This was the simplest consolidation in Phase 3, involving only 2 formatting methods and 5 helper functions with no external dependencies. The consolidation is pure formatting logic, making it the lowest risk migration.

---

## ✅ Pre-Rollout Validation Checklist

### Code Quality Verification
- [x] All 2 methods implemented (`macro_overview_charts`, `scenario_charts`)
- [x] 5 helper methods created for formatting logic
- [x] Type hints added to all methods
- [x] Comprehensive docstrings included
- [x] Error handling for empty data scenarios
- [x] Metadata attachment working correctly

### Testing Verification
- [x] All 15 tests passing (10 unit tests + 5 comparison tests)
- [x] 100% functional equivalence confirmed
- [x] Regime cards format correctly
- [x] Factor exposure charts working
- [x] Waterfall charts rendering properly
- [x] DaR gauge widgets formatted correctly

### Infrastructure Verification
- [x] Feature flag configured: `charts_to_financial`
- [x] Feature flag currently DISABLED
- [x] Dual registration working (both agents registered)
- [x] Capability routing configured
- [x] Server starts without errors
- [x] No import errors

### Documentation Verification
- [x] This rollout checklist created
- [x] Test results saved to charts_comparison_results.json
- [x] AGENT_CONVERSATION_MEMORY.md updated
- [x] Test suites documented

---

## 🚦 Gradual Rollout Schedule

### Day 1-2: Initial Testing (Monday-Tuesday)
**Target:** 10% of traffic

#### Configuration Steps:
1. Update `/backend/config/feature_flags.json`:
```json
{
  "agent_consolidation": {
    "charts_to_financial": {
      "enabled": true,
      "rollout_percentage": 10,
      "description": "Route charts agent capabilities to FinancialAnalyst agent",
      "created_at": "2025-11-03",
      "updated_at": "2025-11-11"
    }
  }
}
```

2. Monitor logs for routing decisions:
```bash
grep "Routing capability charts" /tmp/logs/dawsos*.log
```

#### Validation Metrics (10%):
- [ ] No errors in chart formatting
- [ ] UI visualizations render correctly
- [ ] Response times unchanged
- [ ] Metadata structure preserved
- [ ] No console errors

### Day 3: Confidence Building (Wednesday)
**Target:** 50% of traffic

#### Configuration:
Update rollout_percentage to 50 in feature_flags.json

#### Validation Metrics (50%):
- [ ] Error rate remains at 0%
- [ ] All chart types rendering
- [ ] Color coding working correctly
- [ ] Waterfall charts displaying properly
- [ ] Performance metrics stable

### Day 4-5: Full Rollout (Thursday-Friday)
**Target:** 100% of traffic

#### Configuration:
Update rollout_percentage to 100 in feature_flags.json

#### Final Validation:
- [ ] All patterns using charts capabilities working
- [ ] No regression in visualization quality
- [ ] Server memory usage stable
- [ ] All test suites passing

---

## 🔍 Monitoring Commands

### Check Feature Flag Status
```bash
cat backend/config/feature_flags.json | jq '.agent_consolidation.charts_to_financial'
```

### Monitor Routing Decisions
```bash
tail -f /tmp/logs/dawsos*.log | grep -E "charts\.(macro_overview|scenario_deltas)"
```

### Check Error Rate
```bash
grep -c "ERROR.*charts" /tmp/logs/dawsos*.log
```

### Verify Chart Rendering (via API)
```bash
curl -X POST http://localhost:8000/api/patterns/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"pattern_name": "portfolio_macro_overview", "inputs": {"portfolio_id": "64ff3be6-0ed1-4990-a32b-4ded17f0320c"}}'
```

---

## 🚨 Rollback Procedure

If issues are detected:

1. **Immediate Rollback:**
```json
{
  "charts_to_financial": {
    "enabled": false,
    "rollout_percentage": 0
  }
}
```

2. **No Server Restart Required** - Feature flags are checked on each request

3. **Verify Rollback:**
```bash
grep "ChartsAgent handling capability" /tmp/logs/dawsos*.log
```

---

## ✅ Success Criteria

Before marking complete:
- [ ] 100% rollout for 24+ hours
- [ ] Zero chart-related errors
- [ ] All visualizations confirmed working
- [ ] Performance metrics unchanged
- [ ] No user complaints about charts

---

## 📈 Benefits of Consolidation

1. **Code Reduction:** ~350 lines of duplicate code eliminated
2. **Simpler Architecture:** One less agent to maintain
3. **Better Organization:** All financial visualizations in one place
4. **Zero Risk:** Pure formatting logic with no external dependencies
5. **Improved Testing:** Consolidated test suites easier to maintain

---

## 🎯 Next Steps After Success

1. **Week 4:** AlertsAgent consolidation (complexity: MEDIUM)
2. **Week 5:** ReportsAgent consolidation (complexity: HIGH)
3. **Week 6:** Cleanup and deprecation

---

**Last Updated:** November 3, 2025  
**Updated By:** Phase 3 Implementation Team  
**Risk Level:** LOW (pure formatting logic)  
**Confidence:** HIGH (100% functional equivalence confirmed)