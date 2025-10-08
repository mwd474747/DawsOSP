# Pattern Architecture Audit - Complete Analysis

## Executive Summary

**Date**: October 7, 2025
**Total Patterns**: 48
**Critical Finding**: 3 modern "capability-based" patterns (options) are architecturally incompatible with the existing agent execution system.

## Routing Paradigm Breakdown

| Paradigm | Count | Status |
|----------|-------|--------|
| **Legacy (agent + request)** | 43 | ✅ WORKS |
| **Modern (capability)** | 3 | ❌ BROKEN |
| **Hybrid** | 0 | N/A |
| **Inconsistent** | 2 | ⚠️ REVIEW |

## The Root Architectural Incompatibility

### Legacy Pattern Format (WORKS)
```json
{
  "action": "execute_through_registry",
  "params": {
    "agent": "data_harvester",
    "context": {
      "request": "Fetch options flow data for SPY"
    }
  }
}
```

**Execution Flow:**
1. PatternEngine → AgentRegistry → AgentAdapter
2. AgentAdapter calls `agent.process(context)` or `agent.harvest(context)`
3. Agent extracts `request` string from context
4. Agent **parses text** to determine action
5. Agent routes internally to appropriate method

### Modern Pattern Format (BROKEN)
```json
{
  "action": "execute_through_registry",
  "params": {
    "capability": "can_fetch_options_flow",
    "context": {
      "tickers": "SPY"
    }
  }
}
```

**Execution Flow:**
1. PatternEngine → AgentRegistry → AgentAdapter
2. AgentAdapter calls `agent.process(context)` or `agent.harvest(context)`
3. Context = `{tickers: 'SPY'}` - **NO 'request' field!**
4. Agent expects `request` string → **NOT FOUND**
5. Agent cannot route → **FAILURE**

## Why Options Patterns Are Broken

**The 3 broken patterns:**
- `greeks_analysis`
- `unusual_options_activity`
- `options_flow_analysis`

**Problem**: AgentAdapter only knows how to call these methods:
- `process(context)` - expects `context['request']`
- `think(context)` - expects `context['request']`
- `analyze(query)` - expects a string
- `harvest(request)` - expects a string

**But**: Options methods have specific signatures:
```python
def fetch_options_flow(self, tickers: List[str]) -> Dict
def analyze_options_flow(self, context: Dict) -> Dict
```

These methods are **never called** because:
1. No `request` field for text-based routing
2. No capability→method mapping in AgentAdapter

## Detailed Field Usage

```
agent:        160 occurrences (legacy routing)
request:       67 occurrences (text-based instructions)
capability:     8 occurrences (3 patterns × ~2-3 steps each)
```

**Key insight**: Only 8 capability uses vs. 160 agent uses shows capability-based routing is experimental, not production.

## Working Legacy Patterns (Sample)

All these work because they have **`request` field**:
- ✅ `fundamental_analysis` - "Get comprehensive financial data for {symbol}..."
- ✅ `buffett_checklist` - "Load Buffett and Dalio investment frameworks"
- ✅ `morning_briefing` - "Fetch market movers, news, economic calendar"
- ✅ `dcf_valuation` - Uses agent routing (though missing request - partial issue)

## The Three Refactoring Options

### Option 1: Enhance AgentAdapter (Architecture Change)
**Change**: Make AgentAdapter support capability→method mapping

```python
# In AgentAdapter.execute()
if 'capability' in context:
    # Map capability to method
    method_name = self._map_capability_to_method(context['capability'])
    method = getattr(self.agent, method_name)
    # Extract params from context
    params = self._extract_method_params(method, context)
    result = method(**params)
```

**Pros:**
- Modern, type-safe, scalable
- Proper separation of concerns
- Supports method signatures directly

**Cons:**
- Significant architecture change
- Affects 189 total step executions
- Requires method introspection/mapping
- Risk of breaking existing patterns

### Option 2: Convert to Legacy Format (Pattern Change) ⭐ RECOMMENDED
**Change**: Modify 3 options patterns to use agent + request

**Before:**
```json
{
  "capability": "can_fetch_options_flow",
  "context": {"tickers": "{TICKERS}"}
}
```

**After:**
```json
{
  "agent": "data_harvester",
  "context": {"request": "Fetch options flow for {TICKERS}"}
}
```

Then update `DataHarvester.harvest()` to parse "options flow":
```python
def harvest(self, request: str) -> Dict:
    request_lower = request.lower()

    # Existing patterns...
    if 'price' in request_lower:
        # ... price logic

    # NEW: Options patterns
    if 'options flow' in request_lower:
        symbols = re.findall(r'\b[A-Z]{1,5}\b', request)
        return self.fetch_options_flow(symbols)
```

**Pros:**
- Works immediately with ZERO architecture changes
- Follows 43 existing working patterns
- Simple text parsing (already proven pattern)
- Low risk

**Cons:**
- Text parsing instead of structured params
- Less type-safe
- "Legacy" approach

### Option 3: Hybrid (Temporary Bridge)
**Change**: Add `request` field to capability patterns

```json
{
  "capability": "can_fetch_options_flow",
  "context": {
    "request": "Fetch options flow for {TICKERS}",
    "tickers": "{TICKERS}"
  }
}
```

**Pros:**
- Works immediately
- Preserves capability routing for future
- Backward compatible

**Cons:**
- Redundant fields
- Doesn't solve underlying issue
- Technical debt

## Recommendation: Option 2

**Rationale:**
1. **Proven Pattern**: 43 patterns already work this way
2. **Zero Risk**: No architecture changes
3. **Immediate Fix**: Can be deployed in < 30 minutes
4. **Maintainable**: Follows existing codebase conventions

## Implementation Plan (Option 2)

### Step 1: Update 3 Options Patterns (5 minutes)
Convert capability-based steps to agent + request format.

### Step 2: Add Options Routing to DataHarvester (10 minutes)
Update `harvest()` method to recognize options keywords:
- "options flow" → `fetch_options_flow()`
- "unusual options" → `fetch_unusual_options()`

### Step 3: Add Options Routing to FinancialAnalyst (10 minutes)
Update `process_request()` router to handle:
- "greeks" → `analyze_options_greeks()`
- "options flow" → `analyze_options_flow()`
- "unusual options" → `detect_unusual_options()`
- "iv rank" → `calculate_options_iv_rank()`

### Step 4: Test & Deploy (5 minutes)
Test "Analyze options flow for SPY" → should work end-to-end.

## Long-Term Architectural Consideration

**Future Enhancement (Post-Fix):**
Consider adding proper capability→method mapping to AgentAdapter as a v2.0 feature, but only after:
1. All 48 patterns are stable
2. Clear use cases for structured routing emerge
3. Team bandwidth for architecture changes exists

For now: **Make it work with legacy pattern, enhance architecture later.**

---

**Status**: Ready for implementation
**Estimated Time**: 30 minutes
**Risk Level**: LOW (follows existing patterns)
**Impact**: HIGH (fixes broken options analysis)
