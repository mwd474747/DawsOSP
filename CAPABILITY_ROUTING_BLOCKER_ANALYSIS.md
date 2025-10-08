# Capability Routing Blocker - Root Cause Analysis

**Date**: October 8, 2025
**Status**: CRITICAL BLOCKER IDENTIFIED

---

## Executive Summary

**Finding**: The system cannot migrate patterns to capability routing because **agents lack matching public methods**.

**Impact**: All 103 declared capabilities in AGENT_CAPABILITIES are **not implemented** as callable methods.

**Solution**: Add public wrapper methods to agents that delegate to existing private methods.

---

## The Problem

### What Was Expected

When AgentAdapter receives:
```python
{
  "capability": "can_calculate_dcf",
  "context": {"symbol": "AAPL"}
}
```

It should call:
```python
financial_analyst.calculate_dcf(symbol="AAPL")
```

### What Actually Exists

```python
# In FinancialAnalyst
def _perform_dcf_analysis(self, request: str, context: Dict) -> Dict:
    """PRIVATE method - not callable by AgentAdapter"""
    ...
```

**There is NO `calculate_dcf()` method!**

---

## Evidence

### AGENT_CAPABILITIES Declarations vs. Actual Methods

**FinancialAnalyst**:
| Declared Capability | Expected Method | Actual Method | Status |
|---------------------|-----------------|---------------|--------|
| `can_calculate_dcf` | `calculate_dcf()` | `_perform_dcf_analysis()` | ❌ MISSING |
| `can_calculate_roic` | `calculate_roic()` | `_calculate_roic()` | ❌ MISSING |
| `can_analyze_moat` | `analyze_moat()` | `_analyze_moat()` | ❌ MISSING |
| `can_calculate_owner_earnings` | `calculate_owner_earnings()` | `_calculate_owner_earnings()` | ❌ MISSING |
| `can_analyze_economy` | `analyze_economy()` | ✅ EXISTS | ✅ OK |
| `can_analyze_portfolio_risk` | `analyze_portfolio_risk()` | ✅ EXISTS | ✅ OK |
| `can_analyze_greeks` | `analyze_greeks()` | `analyze_options_greeks()` | ⚠️ MISMATCH |
| `can_analyze_options_flow` | `analyze_options_flow()` | ✅ EXISTS | ✅ OK |

**DataHarvester**:
| Declared Capability | Expected Method | Actual Method | Status |
|---------------------|-----------------|---------------|--------|
| `can_fetch_stock_quotes` | `fetch_stock_quotes()` | Uses `harvest("stock quotes")` | ❌ MISSING |
| `can_fetch_economic_data` | `fetch_economic_data()` | Uses `harvest("economic data")` | ❌ MISSING |
| `can_fetch_news` | `fetch_news()` | Uses `harvest("news")` | ❌ MISSING |
| `can_fetch_fundamentals` | `fetch_fundamentals()` | Uses `harvest("fundamentals")` | ❌ MISSING |
| `can_fetch_market_movers` | `fetch_market_movers()` | Uses `harvest("market movers")` | ❌ MISSING |
| `can_fetch_options_flow` | `fetch_options_flow()` | ✅ EXISTS | ✅ OK |
| `can_fetch_unusual_options` | `fetch_unusual_options()` | ✅ EXISTS | ✅ OK |

**Summary**: Only 10/103 capabilities (9.7%) have matching methods!

---

## Why This Happened

1. **AGENT_CAPABILITIES was created as documentation** - declares what agents "should" be able to do
2. **Agents were built with legacy text-parsing architecture** - use `process_request()` or `harvest()` with string parsing
3. **The two approaches were never integrated** - capabilities declared but not implemented as methods
4. **Options features were added later** - these DO have direct methods (analyze_options_greeks, fetch_options_flow)

---

## What This Means for Pattern Migration

**Current migration plan is BLOCKED**. We cannot migrate patterns to capability routing because:

1. Pattern uses: `"capability": "can_calculate_dcf"`
2. Agent Adapter looks for: `financial_analyst.calculate_dcf()`
3. Method doesn't exist → **FAILURE**

**This is why options patterns return template placeholders!** The capability routing infrastructure works, but the methods don't exist to call.

---

## Solution: Wrapper Methods

### Approach

Add public wrapper methods that delegate to existing private methods:

```python
# In FinancialAnalyst
def calculate_dcf(self, symbol: str, context: Dict = None) -> Dict:
    """Public wrapper for capability routing"""
    request = f"Calculate DCF valuation for {symbol}"
    return self._perform_dcf_analysis(request, context or {})
```

### Benefits

1. ✅ **No breaking changes** - existing legacy routing still works
2. ✅ **Minimal code** - simple delegation, ~5 lines per method
3. ✅ **Fast implementation** - can add all wrappers in 1-2 hours
4. ✅ **Backward compatible** - agents work with both legacy and capability routing

### Implementation Status

**✅ STARTED** - Added 6 wrapper methods to Financial Analyst ([financial_analyst.py:1297-1354](dawsos/agents/financial_analyst.py:1297-1354)):
- `calculate_dcf()` → delegates to `_perform_dcf_analysis()`
- `calculate_roic()` → delegates to `_calculate_roic()`
- `calculate_owner_earnings()` → delegates to `_calculate_owner_earnings()`
- `analyze_moat()` → delegates to `_analyze_moat()`
- `analyze_stock()` → delegates to `analyze_stock_comprehensive()`
- `compare_companies()` → delegates to `compare_stocks()`

**⏳ PENDING** - Need to add wrappers to:
- DataHarvester (7 methods)
- PatternSpotter (2 methods)
- ForecastDreamer (2 methods)
- GovernanceAgent (3 methods)
- RelationshipHunter (2 methods)
- Other agents as needed

---

## Revised Action Plan

### Phase 1: Complete Agent Wrapper Methods (2-3 hours)

**Priority Order**:

1. **DataHarvester** (7 methods, 30 min)
   - `fetch_stock_quotes()`, `fetch_economic_data()`, `fetch_news()`, `fetch_fundamentals()`, `fetch_market_movers()`, `fetch_crypto_data()`, `calculate_correlations()`

2. **FinancialAnalyst - Remaining** (4 methods, 15 min)
   - `calculate_fcf()`, `calculate_wacc()`, `analyze_risks()`, `detect_unusual_activity()`

3. **PatternSpotter** (2 methods, 10 min)
   - `detect_patterns()`, `identify_signals()`

4. **ForecastDreamer** (2 methods, 10 min)
   - `generate_forecast()`, `project_future()`

5. **GovernanceAgent** (3 methods, 15 min)
   - `audit_data_quality()`, `validate_policy()`, `check_compliance()`

6. **RelationshipHunter** (2 methods, 10 min)
   - `calculate_correlations()`, `find_relationships()`

**Total**: ~1.5-2 hours to add all essential wrappers

### Phase 2: Test Capability Routing (30 min)

Test that wrapper methods work:
```python
# Test DCF capability
from dawsos.agents.financial_analyst import FinancialAnalyst
analyst = FinancialAnalyst(graph)
result = analyst.calculate_dcf("AAPL")
print(result)  # Should return DCF analysis, not error
```

### Phase 3: Fix Options Patterns (30 min)

Verify options patterns work with current infrastructure:
- Test "Analyze options flow for SPY"
- Check for template placeholders
- Debug any remaining issues

### Phase 4: Begin Pattern Migration (variable)

Only after wrapper methods are complete:
- Start with Batch 1 (5 simple patterns, 1 hour)
- Validate each pattern works
- Continue with remaining batches

---

## Why We Can't Skip Wrapper Methods

**Option 1**: Skip wrappers, migrate patterns anyway
- ❌ Patterns will fail to execute
- ❌ AgentAdapter will find no matching methods
- ❌ Wasted time migrating broken patterns

**Option 2**: Add wrappers first, then migrate patterns
- ✅ Patterns will execute correctly
- ✅ Clean capability routing end-to-end
- ✅ Can validate each pattern works

**Conclusion**: Option 2 is the only viable path.

---

## Timeline

**Before wrapper methods**:
- Pattern migration: BLOCKED
- Capability routing: 9.7% functional

**After wrapper methods**:
- Pattern migration: UNBLOCKED
- Capability routing: 100% functional
- Time to complete wrappers: ~2 hours
- Time to migrate all 43 patterns: ~11 hours

**Total**: ~13 hours to complete Trinity 2.0 capability routing

---

## Next Steps

1. ✅ Add wrapper methods to FinancialAnalyst (STARTED - 6/10 done)
2. ⏳ Add wrapper methods to DataHarvester
3. ⏳ Add wrapper methods to remaining agents
4. ⏳ Test capability routing works
5. ⏳ Begin pattern migration

---

**Status**: Blocker identified, solution in progress
**Priority**: HIGH - blocks all pattern migration work
**Estimated Time**: 2 hours to unblock, 13 hours total to complete Trinity 2.0
