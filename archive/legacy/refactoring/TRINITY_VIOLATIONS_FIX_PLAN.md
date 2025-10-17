# Trinity 3.0 Violations - Root Cause & Fix Plan

**Date**: October 10, 2025  
**Status**: 🔧 Ready to Fix  
**Estimated Time**: 2 hours  
**Risk Level**: Low

---

## Root Cause (In Plain English)

**Problem**: Capability-based routing (`runtime.execute_by_capability()`) doesn't work.

**Why**: There are TWO different "capabilities" concepts that got confused:
1. **AGENT_CAPABILITIES** (metadata) = List of capability STRINGS like `['can_fetch_data', 'can_analyze']`
2. **agent.capabilities** (runtime) = Dict of capability OBJECTS like `{'market': <MarketDataCapability>}`

When AgentRegistry stores capabilities, it saves the OBJECTS instead of the STRINGS. When you search for `'can_fetch_economic_data'`, it looks in `{'market': <obj>, 'fred': <obj>}` and finds nothing!

**Result**: Capability routing silently fails → Developers use direct agent calls as workaround → Trinity violations.

---

## The Fix (7 Steps)

### Step 1: Store Metadata Separately
**File**: `dawsos/core/agent_adapter.py`  
**Change**: Store metadata capabilities when creating adapter

```python
# Line ~90 (AgentAdapter.__init__)
def __init__(self, agent: Any, metadata_capabilities: Optional[Dict] = None):
    self.agent = agent
    self.metadata_capabilities = metadata_capabilities  # NEW
    self.available_methods = self._discover_methods()
```

### Step 2: Return Metadata from get_capabilities()
**File**: `dawsos/core/agent_adapter.py`  
**Change**: Return metadata instead of agent.capabilities

```python
# Line ~241 (get_capabilities)
def get_capabilities(self) -> Dict[str, Any]:
    # Return metadata capabilities if available
    if self.metadata_capabilities:
        # Convert list to dict format if needed
        if isinstance(self.metadata_capabilities.get('capabilities'), list):
            caps_dict = {cap: True for cap in self.metadata_capabilities['capabilities']}
            return caps_dict
        return self.metadata_capabilities

    # Fallback: agent.capabilities or infer
    if hasattr(self.agent, 'capabilities'):
        return self.agent.capabilities
    ...
```

### Step 3: Fix find_capable_agent()
**File**: `dawsos/core/agent_adapter.py`  
**Change**: Handle both dict and list formats

```python
# Line ~309 (find_capable_agent)
def find_capable_agent(self, capability: str) -> Optional[str]:
    for name, caps in self.capabilities_map.items():
        # Handle dict: {'can_fetch_data': True}
        if isinstance(caps, dict) and (capability in caps or caps.get(capability)):
            return name
        # Handle list: ['can_fetch_data']
        elif isinstance(caps, list) and capability in caps:
            return name
    return None
```

### Step 4: Replace Direct Agent Call #1
**File**: `dawsos/ui/economic_dashboard.py`  
**Change**: Use capability routing

```python
# Line ~60-66: REPLACE
data_harvester = get_agent_safely(runtime, 'data_harvester')
fred_result = data_harvester.fetch_economic_data(...)

# WITH
fred_result = runtime.execute_by_capability(
    'can_fetch_economic_data',
    {
        'indicators': ['GDP', 'CPIAUCSL', 'UNRATE', 'DFF'],
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }
)
```

### Step 5: Replace Direct Agent Call #2
**File**: `dawsos/ui/economic_dashboard.py`  
**Change**: Use capability routing

```python
# Line ~95-105: REPLACE
financial_analyst = get_agent_safely(runtime, 'financial_analyst')
analysis = analyze_macro_data_directly(...)

# WITH
analysis = runtime.execute_by_capability(
    'can_analyze_economy',
    {
        'gdp_data': gdp_data,
        'cpi_data': cpi_data,
        'unemployment_data': unemployment_data,
        'fed_funds_data': fed_funds_data
    }
)
```

### Step 6: Delete Workaround
**File**: `dawsos/ui/economic_dashboard.py`  
**Change**: Delete `analyze_macro_data_directly()` function (lines 370-449)

This was only a workaround and is no longer needed.

### Step 7: Add Tests
**File**: `dawsos/tests/validation/test_capability_routing.py` (NEW)

```python
def test_capability_routing_works():
    runtime = AgentRuntime()
    result = runtime.execute_by_capability(
        'can_fetch_economic_data',
        {'indicators': ['GDP']}
    )
    assert 'error' not in result
    assert result.get('agent') == 'DataHarvester'
```

---

## Files to Modify

1. `dawsos/core/agent_adapter.py` - AgentAdapter class (3 methods)
2. `dawsos/ui/economic_dashboard.py` - Replace 2 violations + delete workaround
3. `dawsos/tests/validation/test_capability_routing.py` - NEW test file

---

## Testing Plan

1. ✅ Fix AgentAdapter
2. ✅ Test capability routing manually  
3. ✅ Replace violations in economic_dashboard  
4. ✅ Test economic dashboard end-to-end  
5. ✅ Add automated tests  
6. ✅ Run full test suite

---

## Success Criteria

- ✅ `runtime.execute_by_capability('can_fetch_economic_data', ...)` works
- ✅ Economic dashboard loads without errors
- ✅ Daily Events calendar displays
- ✅ No direct agent method calls in UI code
- ✅ All tests pass

---

**Ready to implement? See detailed analysis in:**
- TRINITY_3.0_ARCHITECTURE_REVIEW.md (full review)
- TRINITY_3.0_ROOT_CAUSE_ANALYSIS.md (detailed root cause)
