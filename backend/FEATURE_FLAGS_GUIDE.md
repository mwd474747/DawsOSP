# Feature Flags Guide for Agent Consolidation

## Overview
This document explains how to use the feature flag system implemented for safe agent consolidation in production.

## Quick Start

### 1. Check Current Flag Status
```python
from app.core.feature_flags import get_feature_flags

flags = get_feature_flags()
print(flags.list_flags())  # List all flags
print(flags.get_flag_info("agent_consolidation.optimizer_to_financial"))
```

### 2. Enable a Consolidation (Gradual Rollout)
Edit `backend/config/feature_flags.json`:

```json
{
  "agent_consolidation": {
    "optimizer_to_financial": {
      "enabled": true,
      "rollout_percentage": 10,  // Start with 10%
      "description": "Route optimizer capabilities to FinancialAnalyst"
    }
  }
}
```

### 3. Monitor and Increase Rollout
- Start: 10% rollout - Monitor for 1-2 hours
- If stable: Increase to 50% - Monitor for 4-6 hours  
- If stable: Increase to 100% - Full consolidation

### 4. Emergency Rollback
Set `enabled: false` or `rollout_percentage: 0` to instantly rollback:

```json
{
  "agent_consolidation": {
    "optimizer_to_financial": {
      "enabled": false,  // Instant rollback
      "rollout_percentage": 0
    }
  }
}
```

## Available Flags

### Agent Consolidation Flags

| Flag | Description | Target |
|------|-------------|--------|
| `agent_consolidation.optimizer_to_financial` | Routes optimizer capabilities to FinancialAnalyst | Phase 3a |
| `agent_consolidation.ratings_to_financial` | Routes ratings capabilities to FinancialAnalyst | Phase 3a |
| `agent_consolidation.reports_to_financial` | Routes reports capabilities to FinancialAnalyst | Phase 3a |
| `agent_consolidation.charts_to_financial` | Routes charts capabilities to FinancialAnalyst | Phase 3a |
| `agent_consolidation.alerts_to_macro` | Routes alerts capabilities to MacroHound | Phase 3b |
| `agent_consolidation.harvester_to_macro` | Routes data harvester to MacroHound | Phase 3b |
| `agent_consolidation.unified_consolidation` | Master switch for all consolidations | Phase 3c |

### Performance Flags (Already Enabled)
- `performance_optimizations.aggressive_caching` - ✅ Enabled (100%)
- `performance_optimizations.lazy_loading` - ✅ Enabled (100%)
- `safety_controls.enhanced_logging` - ✅ Enabled (100%)
- `safety_controls.rate_limiting` - ✅ Enabled (100%)

## Phase 3 Rollout Plan

### Phase 3a: Consolidate to FinancialAnalyst (Week 1)
```bash
# Day 1: Enable optimizer consolidation at 10%
# Day 2: Increase to 50% if stable
# Day 3: Increase to 100% if stable
# Day 4-5: Add ratings, reports, charts one by one
```

### Phase 3b: Consolidate to MacroHound (Week 2)
```bash
# Day 6: Enable alerts consolidation at 10%
# Day 7: Increase gradually to 100%
# Day 8: Enable harvester consolidation
```

### Phase 3c: Full Consolidation (Week 3)
```bash
# Day 9-10: Enable unified_consolidation flag
# Day 11-14: Monitor and optimize
```

## How It Works

### Deterministic Rollout
The system uses MD5 hashing of `flag_name + user_id` to deterministically assign users:
- Same user always gets same behavior
- No flip-flopping between old and new
- Predictable rollout distribution

### Runtime Reloading
Flags auto-reload every minute, or manually call:
```python
flags = get_feature_flags()
flags.reload()  # Reload immediately
```

### Integration with AgentRuntime
The AgentRuntime automatically checks flags when routing capabilities:

1. Normal routing: `capability → original_agent`
2. Flag check: Is consolidation enabled for this agent?
3. If yes: Route to consolidated agent
4. If no: Use original routing

## Testing

### Run Test Script
```bash
cd backend
python test_feature_flags.py
```

### Test Specific Consolidation
```python
from app.core.feature_flags import get_feature_flags

flags = get_feature_flags()
context = {"user_id": "test_user_123"}

# Check if this user gets the new routing
if flags.is_enabled("agent_consolidation.optimizer_to_financial", context):
    print("User gets consolidated agent")
else:
    print("User gets original agent")
```

## Monitoring

### Check Logs
Look for these log messages:
```
INFO - Feature flag routing: optimizer.suggest from optimizer_agent to financial_analyst
INFO - Feature flag override: Routing optimizer.suggest from optimizer_agent to financial_analyst
```

### Metrics to Watch
- Error rates per capability
- Response times
- Agent invocation counts
- Cache hit rates

## Safety Features

1. **Backward Compatible**: System works normally with all flags disabled
2. **Instant Rollback**: Change JSON file to rollback immediately  
3. **Gradual Rollout**: Test with small percentage first
4. **Deterministic**: Same user always gets same experience
5. **Enhanced Logging**: All routing decisions are logged

## Common Operations

### Enable Single Consolidation
```json
{
  "agent_consolidation": {
    "optimizer_to_financial": {
      "enabled": true,
      "rollout_percentage": 100
    }
  }
}
```

### Enable All Consolidations
```json
{
  "agent_consolidation": {
    "unified_consolidation": {
      "enabled": true,
      "rollout_percentage": 100
    }
  }
}
```

### A/B Test (50/50 split)
```json
{
  "agent_consolidation": {
    "optimizer_to_financial": {
      "enabled": true,
      "rollout_percentage": 50
    }
  }
}
```

## Troubleshooting

### Flags Not Taking Effect
1. Check JSON syntax is valid
2. Verify flag names are correct
3. Wait 1 minute for auto-reload or call `reload()`
4. Check logs for loading errors

### Unexpected Routing
1. Check if unified_consolidation is enabled
2. Verify target agent has the capability
3. Check user context hash for deterministic routing

### Performance Issues
1. Start with smaller rollout percentage
2. Monitor cache hit rates
3. Check agent latency metrics

## Next Steps

1. **Start Small**: Begin with 10% rollout of one consolidation
2. **Monitor Closely**: Watch error rates and performance
3. **Iterate Gradually**: Increase rollout percentages slowly
4. **Document Issues**: Track any problems for future reference
5. **Celebrate Success**: Full consolidation = cleaner architecture!

## Support

For issues or questions about feature flags:
1. Check test script: `backend/test_feature_flags.py`
2. Review implementation: `backend/app/core/feature_flags.py`
3. Check integration: `backend/app/core/agent_runtime.py`

---

*Feature flag system implemented for safe production deployment of agent consolidation - November 3, 2025*