# Runtime Testing Preparation

**Date:** November 4, 2025  
**Author:** Claude IDE Agent  
**Purpose:** Prepare runtime testing cases and validation scripts  
**Status:** 📋 **READY FOR TESTING**

---

## 📊 Executive Summary

**Code Validation Complete:**
- ✅ HoldingsPage migration: Code verified
- ✅ Optimizer routing: Static analysis complete, routing logic verified
- ✅ Database pool: Configuration reviewed
- ✅ Auth refresh: Implementation verified
- ✅ FMP rate limiting: Implementation verified
- ✅ UI error handling: Implementation verified

**Runtime Testing Required:**
1. **HoldingsPage Migration Test** - Verify PatternRenderer loads correctly
2. **Optimizer Routing Test** - Execute `portfolio_scenario_analysis` pattern
3. **Database Pool Stress Test** - Test concurrent agent access

---

## ✅ Code Validation Results

### 1. HoldingsPage Migration ✅ **VERIFIED**

**Code Location:** `full_ui.html` lines 8475-8492

**Implementation:**
```javascript
function HoldingsPage() {
    const { portfolioId } = useUserContext();
    
    return e('div', { className: 'holdings-page' },
        e('div', { className: 'page-header' },
            e('h1', { className: 'page-title' }, 'Holdings'),
            e('p', { className: 'page-description' }, 'Portfolio positions and allocations')
        ),
        e(PatternRenderer, {
            pattern: 'portfolio_overview',
            inputs: { portfolio_id: portfolioId, lookback_days: 252 },
            config: {
                showPanels: ['holdings_table']
            }
        })
    );
}
```

**Validation:**
- ✅ Uses `PatternRenderer` component
- ✅ Uses `portfolio_overview` pattern
- ✅ Uses `config.showPanels` to filter panels
- ✅ Uses `useUserContext()` for portfolio ID
- ✅ Consistent with AttributionPage and AlertsPage

**Runtime Test Required:**
1. Navigate to `/holdings` page
2. Verify `PatternRenderer` loads without errors
3. Verify `holdings_table` panel displays
4. Verify data extraction works (`valued_positions.positions`)
5. Verify no console errors

---

### 2. Optimizer Routing ✅ **VERIFIED (STATIC ANALYSIS)**

**Code Locations:**
- `backend/app/core/capability_mapping.py` lines 56-62
- `backend/app/core/agent_runtime.py` lines 420-450
- `backend/app/agents/financial_analyst.py` lines 2832-2878
- `backend/patterns/portfolio_scenario_analysis.json` line 81
- `backend/config/feature_flags.json` lines 3-9

**Routing Logic:**
```python
# AgentRuntime._get_capability_routing_override()
# 1. Check if capability is in CAPABILITY_CONSOLIDATION_MAP
# 2. Check if feature flag is enabled
# 3. Route to target agent if enabled
# 4. Fall back to original agent if disabled

# Capability Mapping:
"optimizer.suggest_hedges": {
    "target": "financial_analyst.suggest_hedges",
    "target_agent": "financial_analyst",
    "priority": 2,
    "risk_level": "medium",
    "dependencies": ["macro.run_scenario"],
}

# Feature Flag:
"optimizer_to_financial": {
    "enabled": true,
    "rollout_percentage": 100,
}

# Target Method:
async def financial_analyst_suggest_hedges(...)
    # Method exists and is implemented
```

**Validation:**
- ✅ Capability mapping exists
- ✅ Feature flag enabled (100% rollout)
- ✅ Target method exists
- ✅ Pattern uses capability correctly
- ✅ Routing logic checks feature flag

**Runtime Test Required:**
1. Execute `portfolio_scenario_analysis` pattern
2. Verify `optimizer.suggest_hedges` routes to `financial_analyst.suggest_hedges`
3. Verify pattern completes successfully
4. Verify `hedge_suggestions` output structure is correct
5. Check logs for routing decision

**Test Pattern:**
```json
{
  "pattern_id": "portfolio_scenario_analysis",
  "inputs": {
    "portfolio_id": "<valid_portfolio_id>",
    "scenario_id": "rates_up"
  }
}
```

**Expected Output:**
```json
{
  "success": true,
  "data": {
    "hedge_suggestions": {
      "hedges": [...],
      "total_notional": ...,
      "expected_offset_pct": ...,
      "scenario_id": "rates_up"
    }
  },
  "trace": {
    "steps": [
      {
        "capability": "optimizer.suggest_hedges",
        "routed_to": "financial_analyst.suggest_hedges",
        "agent": "financial_analyst"
      }
    ]
  }
}
```

---

### 3. Database Pool Configuration ✅ **REVIEWED**

**Code Location:** `backend/app/db/connection.py`

**Configuration:**
```python
# Default pool configuration
min_size = 5
max_size = 20

# RLS connection with user context
async def get_db_connection_with_rls(user_id: UUID):
    # Sets app.user_id for RLS policies
    # Uses connection pool
    # Proper cleanup on exit
```

**Validation:**
- ✅ Connection pool management exists
- ✅ RLS support via `get_db_connection_with_rls()`
- ✅ Connection context managers for proper cleanup
- ✅ Pool size configuration (min=5, max=20)

**Potential Issues:**
- ⚠️ **Pool Size:** 20 connections may be insufficient for concurrent agents
- ⚠️ **Agent Access:** Multiple agents may compete for connections
- ⚠️ **Pattern Execution:** Patterns with multiple steps may hold connections

**Runtime Test Required:**
1. Test concurrent pattern execution (multiple patterns at once)
2. Test connection pool exhaustion scenario
3. Test connection pool recovery after exhaustion
4. Monitor connection pool usage metrics
5. Verify no connection leaks

**Stress Test:**
```python
# Test concurrent pattern execution
async def test_concurrent_patterns():
    patterns = [
        "portfolio_overview",
        "portfolio_scenario_analysis",
        "macro_trend_monitor",
        "buffett_checklist",
        "news_impact_analysis"
    ]
    
    # Execute 5 patterns concurrently
    results = await asyncio.gather(*[
        execute_pattern(pattern, inputs) for pattern in patterns
    ])
    
    # Verify all completed successfully
    # Verify no connection pool errors
```

---

## 📋 Runtime Test Cases

### Test Case 1: HoldingsPage Migration

**Objective:** Verify HoldingsPage loads correctly with PatternRenderer

**Steps:**
1. Navigate to `/holdings` page
2. Wait for PatternRenderer to load
3. Verify `holdings_table` panel displays
4. Verify holdings data is displayed
5. Check browser console for errors

**Expected Results:**
- ✅ Page loads without errors
- ✅ PatternRenderer executes `portfolio_overview` pattern
- ✅ `holdings_table` panel displays with holdings data
- ✅ No console errors
- ✅ Data extraction works correctly (`valued_positions.positions`)

**Validation Points:**
- Pattern execution: `portfolio_overview` executes successfully
- Data extraction: `getDataByPath(data, 'valued_positions.positions')` returns array
- Panel rendering: `TablePanel` receives array of position objects
- Panel filtering: Only `holdings_table` panel displays (no other panels)

---

### Test Case 2: Optimizer Routing

**Objective:** Verify `optimizer.suggest_hedges` routes to `financial_analyst.suggest_hedges`

**Steps:**
1. Execute `portfolio_scenario_analysis` pattern
2. Monitor logs for routing decision
3. Verify pattern completes successfully
4. Verify `hedge_suggestions` output structure
5. Check trace for routing confirmation

**Test Request:**
```json
POST /api/patterns/execute
Authorization: Bearer <token>
{
  "pattern_id": "portfolio_scenario_analysis",
  "inputs": {
    "portfolio_id": "<valid_portfolio_id>",
    "scenario_id": "rates_up"
  }
}
```

**Expected Results:**
- ✅ Pattern executes successfully
- ✅ `optimizer.suggest_hedges` routes to `financial_analyst.suggest_hedges`
- ✅ `hedge_suggestions` output structure is correct
- ✅ Trace shows routing decision
- ✅ No capability missing errors

**Validation Points:**
- Routing decision: Logs show `optimizer.suggest_hedges → financial_analyst.suggest_hedges`
- Feature flag: Feature flag check passes
- Capability mapping: Mapping found in `CAPABILITY_CONSOLIDATION_MAP`
- Target method: `financial_analyst_suggest_hedges()` executes successfully
- Output structure: `hedge_suggestions` matches expected format

**Logs to Check:**
```
[AgentRuntime] Routing optimizer.suggest_hedges to financial_analyst.suggest_hedges
[AgentRuntime] Feature flag optimizer_to_financial: enabled=true, rollout=100%
[FinancialAnalyst] Executing financial_analyst_suggest_hedges
```

---

### Test Case 3: Database Pool Stress Test

**Objective:** Verify connection pool handles concurrent agent access

**Steps:**
1. Execute multiple patterns concurrently
2. Monitor connection pool usage
3. Verify no connection pool exhaustion errors
4. Verify all patterns complete successfully
5. Check for connection leaks

**Test Script:**
```python
import asyncio
from app.api.executor import execute_pattern

async def test_concurrent_patterns():
    patterns = [
        ("portfolio_overview", {"portfolio_id": "..."}),
        ("portfolio_scenario_analysis", {"portfolio_id": "...", "scenario_id": "rates_up"}),
        ("macro_trend_monitor", {"portfolio_id": "..."}),
        ("buffett_checklist", {"portfolio_id": "...", "security_id": "..."}),
        ("news_impact_analysis", {"portfolio_id": "..."})
    ]
    
    # Execute 5 patterns concurrently
    results = await asyncio.gather(*[
        execute_pattern(pattern_id, inputs) for pattern_id, inputs in patterns
    ])
    
    # Verify all completed successfully
    for result in results:
        assert result["success"] == True
    
    # Verify no connection pool errors
    # Check logs for connection pool errors
```

**Expected Results:**
- ✅ All patterns execute successfully
- ✅ No connection pool exhaustion errors
- ✅ Connection pool usage stays within limits
- ✅ No connection leaks
- ✅ Patterns complete without timeout

**Validation Points:**
- Connection pool size: Stays within max_size (20)
- Connection acquisition: No timeouts or errors
- Connection cleanup: Proper cleanup after pattern execution
- Concurrent access: Multiple agents can access pool simultaneously
- RLS isolation: User context properly set for each connection

**Metrics to Monitor:**
- Active connections: Should not exceed max_size
- Connection wait time: Should be minimal
- Connection pool errors: Should be zero
- Pattern execution time: Should not increase significantly

---

## 🔍 Validation Scripts

### Script 1: HoldingsPage Validation

**File:** `test_holdings_page.sh`

```bash
#!/bin/bash

# Test HoldingsPage migration
echo "Testing HoldingsPage migration..."

# 1. Navigate to holdings page
curl -X GET "http://localhost:8000/holdings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# 2. Check for PatternRenderer execution
# 3. Verify holdings_table panel displays
# 4. Check browser console for errors
```

---

### Script 2: Optimizer Routing Validation

**File:** `test_optimizer_routing.py`

```python
#!/usr/bin/env python3
"""
Test optimizer.suggest_hedges routing to financial_analyst.suggest_hedges
"""

import asyncio
import json
from app.api.executor import execute_pattern
from app.core.agent_runtime import get_agent_runtime

async def test_optimizer_routing():
    """Test optimizer routing in runtime."""
    
    # Test inputs
    portfolio_id = "<valid_portfolio_id>"
    scenario_id = "rates_up"
    
    # Execute pattern
    result = await execute_pattern(
        pattern_id="portfolio_scenario_analysis",
        inputs={
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id
        }
    )
    
    # Verify routing
    assert result["success"] == True
    assert "hedge_suggestions" in result["data"]
    
    # Check trace for routing decision
    trace = result.get("trace", {})
    steps = trace.get("steps", [])
    
    for step in steps:
        if step.get("capability") == "optimizer.suggest_hedges":
            assert step.get("routed_to") == "financial_analyst.suggest_hedges"
            assert step.get("agent") == "financial_analyst"
            print("✅ Routing verified: optimizer.suggest_hedges → financial_analyst.suggest_hedges")
            break
    
    print("✅ Optimizer routing test passed")

if __name__ == "__main__":
    asyncio.run(test_optimizer_routing())
```

---

### Script 3: Database Pool Stress Test

**File:** `test_db_pool_stress.py`

```python
#!/usr/bin/env python3
"""
Test database connection pool with concurrent agent access
"""

import asyncio
from app.api.executor import execute_pattern
from app.db.connection import get_db_pool

async def test_concurrent_patterns():
    """Test concurrent pattern execution."""
    
    patterns = [
        ("portfolio_overview", {"portfolio_id": "..."}),
        ("portfolio_scenario_analysis", {"portfolio_id": "...", "scenario_id": "rates_up"}),
        ("macro_trend_monitor", {"portfolio_id": "..."}),
        ("buffett_checklist", {"portfolio_id": "...", "security_id": "..."}),
        ("news_impact_analysis", {"portfolio_id": "..."})
    ]
    
    # Execute patterns concurrently
    results = await asyncio.gather(*[
        execute_pattern(pattern_id, inputs) for pattern_id, inputs in patterns
    ])
    
    # Verify all completed successfully
    for i, result in enumerate(results):
        pattern_id = patterns[i][0]
        assert result["success"] == True, f"Pattern {pattern_id} failed"
        print(f"✅ Pattern {pattern_id} completed successfully")
    
    # Check connection pool stats
    pool = get_db_pool()
    print(f"Connection pool stats: {pool.get_stats()}")
    
    print("✅ Database pool stress test passed")

if __name__ == "__main__":
    asyncio.run(test_concurrent_patterns())
```

---

## 📊 Testing Checklist

### HoldingsPage Migration Test

- [ ] Navigate to `/holdings` page
- [ ] Verify PatternRenderer loads
- [ ] Verify `holdings_table` panel displays
- [ ] Verify holdings data is displayed
- [ ] Check browser console for errors
- [ ] Verify data extraction works (`valued_positions.positions`)
- [ ] Verify panel filtering works (only `holdings_table` panel)

### Optimizer Routing Test

- [ ] Execute `portfolio_scenario_analysis` pattern
- [ ] Verify pattern completes successfully
- [ ] Verify `optimizer.suggest_hedges` routes to `financial_analyst.suggest_hedges`
- [ ] Verify `hedge_suggestions` output structure
- [ ] Check trace for routing confirmation
- [ ] Verify no capability missing errors
- [ ] Check logs for routing decision

### Database Pool Stress Test

- [ ] Execute multiple patterns concurrently
- [ ] Verify all patterns complete successfully
- [ ] Verify no connection pool exhaustion errors
- [ ] Verify connection pool usage stays within limits
- [ ] Verify no connection leaks
- [ ] Monitor connection pool metrics
- [ ] Verify RLS isolation works correctly

---

## 🎯 Success Criteria

### HoldingsPage Migration Test

- ✅ Page loads without errors
- ✅ PatternRenderer executes `portfolio_overview` pattern
- ✅ `holdings_table` panel displays with holdings data
- ✅ No console errors
- ✅ Data extraction works correctly

### Optimizer Routing Test

- ✅ Pattern executes successfully
- ✅ `optimizer.suggest_hedges` routes to `financial_analyst.suggest_hedges`
- ✅ `hedge_suggestions` output structure is correct
- ✅ Trace shows routing decision
- ✅ No capability missing errors

### Database Pool Stress Test

- ✅ All patterns execute successfully
- ✅ No connection pool exhaustion errors
- ✅ Connection pool usage stays within limits
- ✅ No connection leaks
- ✅ Patterns complete without timeout

---

## 📝 Notes

### Replit Agent Testing

**Recommended Testing Approach:**
1. **HoldingsPage:** Visual testing in browser (Replit provides browser preview)
2. **Optimizer Routing:** API testing via curl or Postman
3. **Database Pool:** Load testing with concurrent requests

**Replit-Specific Considerations:**
- Browser preview available for UI testing
- API endpoints accessible via curl
- Database connection pool limits may differ from local
- Monitor connection pool usage in Replit logs

---

**Last Updated:** November 4, 2025  
**Status:** 📋 **READY FOR RUNTIME TESTING**

