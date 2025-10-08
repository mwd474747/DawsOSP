# DawsOS Functionality Refactoring Plan

**Date**: October 7, 2025
**Current Status**: A+ (98/100) - Code Quality
**Architecture Status**: Dual-paradigm (Legacy + Modern) - Incomplete Migration
**Target**: Unified Trinity 2.0 Capability-Based Architecture
**Estimated Effort**: 60-80 hours (2-3 weeks)

---

## Executive Summary

**Root Cause Discovery**: The options implementation revealed that DawsOS operates on **two incompatible routing paradigms**:

1. **Legacy (agent + request)**: 43 patterns use text-based routing ✅ WORKS
2. **Modern (capability)**: 3 patterns use structured routing ❌ BROKEN (until commit 7348488)

**Core Issue**: Infrastructure was built for modern capability-based routing (AgentRuntime.execute_by_capability, AGENT_CAPABILITIES registry, 103 capabilities documented), but execution layer (ExecuteThroughRegistryAction, AgentAdapter) only supported legacy text-based routing.

**Recent Fix**: Commit 7348488 added capability routing to ExecuteThroughRegistryAction, but this is only **partial completion** of the modern architecture.

---

## The Architecture Gap

### What Was Built (Trinity 2.0 Vision)

**Infrastructure EXISTS**:
- ✅ `AGENT_CAPABILITIES` registry (103 capabilities across 15 agents)
- ✅ `AgentRuntime.execute_by_capability()` method
- ✅ `CAPABILITY_ROUTING_GUIDE.md` (comprehensive documentation)
- ✅ Capability-based patterns (3 options patterns)
- ✅ README.md promotes capability-based routing

**Infrastructure MISSING**:
- ❌ AgentAdapter doesn't support capability→method mapping
- ❌ Only 3/46 patterns use capability routing (6.5%)
- ❌ Agent methods still expect text-based `request` strings
- ❌ No capability validation or discovery UI
- ❌ No graceful degradation when capabilities missing

### What Actually Works (Legacy Reality)

**Current Reality**:
- 43 patterns use `agent + request` (text parsing)
- Agents have massive if/elif routing methods (70+ lines)
- AgentAdapter calls generic methods: `process()`, `think()`, `analyze()`, `harvest()`
- Methods parse `context['request']` string to determine action
- No type safety, no method signature enforcement

**Example** (FinancialAnalyst.process_request - lines 37-106):
```python
def process_request(self, request: str, context: Dict) -> Dict:
    request_lower = request.lower()

    if any(term in request_lower for term in ['economy', 'macro']):
        return self.analyze_economy(context)
    elif any(term in request_lower for term in ['portfolio risk']):
        return self.analyze_portfolio_risk(holdings, context)
    elif any(term in request_lower for term in ['dcf', 'valuation']):
        return self._perform_dcf_analysis(...)
    # ... 10+ more elif branches
```

---

## Phase 1: Complete Capability Routing Infrastructure (20-25 hours)

**Goal**: Make capability-based routing fully functional across all execution layers

### 1.1 Enhance AgentAdapter for Capability Routing (8-10 hours)
**Priority**: 🔴 CRITICAL
**File**: `dawsos/core/agent_adapter.py`

**Current State** (lines 45-77):
```python
def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute agent through standardized interface"""

    # Determine which method to call based on agent type
    if hasattr(self.agent, 'process'):
        result = self.agent.process(context)
    elif hasattr(self.agent, 'think'):
        result = self.agent.think(context)
    elif hasattr(self.agent, 'analyze'):
        query = context.get('request', context.get('query', ''))
        result = self.agent.analyze(query)
    # ... more elif branches
```

**Target State**:
```python
def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute agent through standardized interface"""

    # NEW: Check for capability-based routing
    if 'capability' in context:
        return self._execute_by_capability(context)

    # LEGACY: Fall back to request-based routing
    if hasattr(self.agent, 'process'):
        result = self.agent.process(context)
    # ... existing logic

def _execute_by_capability(self, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute agent method via capability routing"""
    capability = context['capability']

    # Map capability to method name
    method_name = self._map_capability_to_method(capability)

    if not method_name or not hasattr(self.agent, method_name):
        return {'error': f'Agent does not support capability: {capability}'}

    # Get method and extract parameters
    method = getattr(self.agent, method_name)
    params = self._extract_method_params(method, context)

    # Call with proper signature
    return method(**params)

def _map_capability_to_method(self, capability: str) -> Optional[str]:
    """Map capability to agent method name"""
    # Capability naming convention: can_<action>_<subject>
    # Method naming convention: <action>_<subject>

    if capability.startswith('can_'):
        return capability[4:]  # Remove 'can_' prefix

    # Fallback to direct lookup in CAPABILITY_METHOD_MAP
    return CAPABILITY_METHOD_MAP.get(capability)

def _extract_method_params(self, method: Callable, context: Dict) -> Dict:
    """Extract method parameters from context using introspection"""
    import inspect

    sig = inspect.signature(method)
    params = {}

    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue

        # Try exact match first
        if param_name in context:
            params[param_name] = context[param_name]
        # Try common variations
        elif param_name == 'symbol' and 'ticker' in context:
            params[param_name] = context['ticker']
        elif param_name == 'tickers' and 'symbols' in context:
            params[param_name] = context['symbols']
        # Use default if available
        elif param.default != inspect.Parameter.empty:
            params[param_name] = param.default

    return params
```

**New File**: `dawsos/core/capability_method_map.py`
```python
"""Maps capabilities to method names for edge cases"""

CAPABILITY_METHOD_MAP = {
    # Options analysis
    'can_fetch_options_flow': 'fetch_options_flow',
    'can_analyze_greeks': 'analyze_greeks',
    'can_detect_unusual_activity': 'detect_unusual_options',
    'can_calculate_iv_rank': 'calculate_iv_rank',

    # Financial analysis
    'can_calculate_dcf': 'calculate_dcf_valuation',
    'can_analyze_moat': 'analyze_moat',

    # Data harvesting
    'can_fetch_market_data': 'fetch_market_overview',
    'can_fetch_economic_data': 'fetch_economic_indicators',

    # Add more as needed...
}
```

**Benefits**:
- Type-safe method calls with proper signatures
- No more text parsing
- Automatic parameter extraction
- Support for both legacy and modern patterns

**Testing**:
```python
# Test capability routing
context = {
    'capability': 'can_fetch_options_flow',
    'tickers': ['SPY', 'QQQ']
}
result = adapter.execute(context)
```

---

### 1.2 Add Capability Discovery API (4-6 hours)
**Priority**: 🔴 HIGH
**File**: `dawsos/core/agent_runtime.py`

**New Methods**:
```python
def get_agents_with_capability(self, capability: str) -> List[str]:
    """Get all agents that support a capability"""
    agents = []
    for agent_name, metadata in self.agent_metadata.items():
        if capability in metadata.get('capabilities', []):
            agents.append(agent_name)
    return agents

def get_capabilities_for_agent(self, agent_name: str) -> List[str]:
    """Get all capabilities for a specific agent"""
    if agent_name not in self.agent_metadata:
        return []
    return self.agent_metadata[agent_name].get('capabilities', [])

def validate_capability(self, capability: str) -> Dict[str, Any]:
    """Validate if capability exists and which agents support it"""
    agents = self.get_agents_with_capability(capability)

    return {
        'capability': capability,
        'exists': len(agents) > 0,
        'agents': agents,
        'count': len(agents)
    }

def list_all_capabilities(self) -> Dict[str, List[str]]:
    """Get all capabilities organized by agent"""
    capabilities_map = {}

    for agent_name, metadata in self.agent_metadata.items():
        capabilities_map[agent_name] = metadata.get('capabilities', [])

    return capabilities_map

def suggest_capability(self, query: str) -> List[Dict[str, Any]]:
    """Suggest capabilities based on query text"""
    query_lower = query.lower()
    suggestions = []

    for agent_name, metadata in self.agent_metadata.items():
        for cap in metadata.get('capabilities', []):
            # Match keywords
            cap_words = cap.replace('can_', '').replace('_', ' ')
            if any(word in query_lower for word in cap_words.split()):
                suggestions.append({
                    'capability': cap,
                    'agent': agent_name,
                    'relevance': self._calculate_relevance(query_lower, cap)
                })

    # Sort by relevance
    suggestions.sort(key=lambda x: x['relevance'], reverse=True)
    return suggestions[:5]  # Top 5
```

**Testing**:
```python
# Test discovery
runtime.get_agents_with_capability('can_calculate_dcf')
# Returns: ['financial_analyst']

runtime.suggest_capability('options greeks analysis')
# Returns: [
#   {'capability': 'can_analyze_greeks', 'agent': 'financial_analyst', ...},
#   {'capability': 'can_fetch_options_flow', 'agent': 'data_harvester', ...}
# ]
```

---

### 1.3 Add Graceful Degradation (3-4 hours)
**Priority**: ⚠️ MEDIUM
**File**: `dawsos/core/agent_runtime.py`

**Enhanced execute_by_capability**:
```python
def execute_by_capability(
    self,
    capability: str,
    context: Dict,
    fallback: bool = True
) -> Dict[str, Any]:
    """
    Execute by capability with graceful degradation

    Args:
        capability: Capability to execute
        context: Execution context
        fallback: If True, try legacy text-based routing on failure

    Returns:
        Result dictionary
    """
    # Find agents with capability
    agents = self.get_agents_with_capability(capability)

    if not agents:
        logger.warning(f"No agents found for capability: {capability}")

        if fallback:
            # Try to construct legacy request string
            return self._fallback_to_legacy(capability, context)

        return {
            'error': f'No agents support capability: {capability}',
            'suggestion': 'Check CAPABILITY_ROUTING_GUIDE.md for available capabilities'
        }

    # Use first available agent (TODO: add agent selection logic)
    agent_name = agents[0]

    # Add capability to context for AgentAdapter
    enriched_context = {**context, 'capability': capability}

    try:
        result = self.exec_via_registry(agent_name, enriched_context)
        return result
    except Exception as e:
        logger.error(f"Capability execution failed: {capability} - {e}")

        if fallback:
            return self._fallback_to_legacy(capability, context)

        raise

def _fallback_to_legacy(self, capability: str, context: Dict) -> Dict:
    """Fallback to legacy text-based routing"""
    logger.info(f"Falling back to legacy routing for: {capability}")

    # Construct request string from capability
    request = self._capability_to_request(capability, context)

    # Guess agent based on capability prefix
    agent = self._guess_agent_from_capability(capability)

    if not agent:
        return {'error': f'Cannot fallback for capability: {capability}'}

    legacy_context = {**context, 'request': request}
    return self.exec_via_registry(agent, legacy_context)

def _capability_to_request(self, capability: str, context: Dict) -> str:
    """Convert capability to natural language request"""
    # Remove 'can_' prefix
    action = capability.replace('can_', '').replace('_', ' ')

    # Add context parameters
    params = ', '.join(f"{k}={v}" for k, v in context.items()
                      if k not in ['capability', 'request'])

    return f"{action.title()} with {params}" if params else action.title()

def _guess_agent_from_capability(self, capability: str) -> Optional[str]:
    """Guess agent name from capability string"""
    # Common patterns
    if 'fetch' in capability or 'harvest' in capability:
        return 'data_harvester'
    elif 'analyze' in capability or 'calculate' in capability:
        return 'financial_analyst'
    elif 'forecast' in capability or 'predict' in capability:
        return 'forecast_dreamer'
    elif 'governance' in capability or 'quality' in capability:
        return 'governance_agent'

    return None
```

**Benefits**:
- System doesn't break if capability routing fails
- Automatic fallback to legacy patterns
- Clear error messages with suggestions

---

### 1.4 Capability Validation in PatternEngine (4-5 hours)
**Priority**: ⚠️ MEDIUM
**File**: `dawsos/core/pattern_engine.py`

**Pre-execution validation**:
```python
def execute_pattern(
    self,
    pattern: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute pattern with capability validation"""

    # NEW: Validate capabilities before execution
    validation = self._validate_pattern_capabilities(pattern)

    if not validation['valid']:
        logger.warning(f"Pattern capability validation failed: {validation}")

        # Continue with warning (don't block execution)
        context['_capability_warnings'] = validation['warnings']

    # Existing execution logic...
    return self._execute_steps(pattern, context)

def _validate_pattern_capabilities(self, pattern: Dict) -> Dict:
    """Validate all capabilities used in pattern exist"""
    warnings = []
    capabilities_used = set()

    # Extract all capabilities from pattern steps
    for step in pattern.get('steps', []):
        action = step.get('action')
        params = step.get('params', {})

        if action == 'execute_through_registry':
            cap = params.get('capability')
            if cap:
                capabilities_used.add(cap)

                # Check if capability exists
                validation = self.runtime.validate_capability(cap)
                if not validation['exists']:
                    warnings.append({
                        'capability': cap,
                        'error': 'No agents support this capability',
                        'step': step.get('name', 'unnamed')
                    })

    return {
        'valid': len(warnings) == 0,
        'warnings': warnings,
        'capabilities': list(capabilities_used)
    }
```

**New Pattern Linting Rule**:
```python
# In scripts/lint_patterns.py

def validate_capabilities(pattern: Dict) -> List[str]:
    """Validate capabilities referenced in pattern"""
    from dawsos.core.agent_runtime import AgentRuntime

    runtime = AgentRuntime(None)
    errors = []

    for step in pattern.get('steps', []):
        if step.get('action') == 'execute_through_registry':
            cap = step.get('params', {}).get('capability')

            if cap:
                validation = runtime.validate_capability(cap)
                if not validation['exists']:
                    errors.append(
                        f"Unknown capability '{cap}' in step: {step.get('name')}"
                    )

    return errors
```

---

## Phase 2: Migrate Legacy Patterns to Capability Routing (25-30 hours)

**Goal**: Convert 43 legacy patterns to modern capability-based routing

### 2.1 Pattern Migration Strategy

**Phased Approach**:
1. **Batch 1** (5 patterns): Simple analysis patterns (5 hours)
2. **Batch 2** (10 patterns): Financial patterns (8 hours)
3. **Batch 3** (15 patterns): Data harvesting patterns (10 hours)
4. **Batch 4** (13 patterns): Remaining patterns (7 hours)

**Migration Template**:

**Before** (legacy):
```json
{
  "action": "execute_through_registry",
  "params": {
    "agent": "financial_analyst",
    "context": {
      "request": "Perform DCF analysis for {SYMBOL}"
    }
  }
}
```

**After** (modern):
```json
{
  "action": "execute_through_registry",
  "params": {
    "capability": "can_calculate_dcf",
    "context": {
      "symbol": "{SYMBOL}"
    }
  }
}
```

### 2.2 Agent Method Refactoring (10-12 hours)

**Goal**: Remove text-parsing routing methods, expose granular methods

**Example - FinancialAnalyst**:

**Current** (70-line routing method):
```python
def process_request(self, request: str, context: Dict) -> Dict:
    """MASSIVE TEXT PARSER"""
    request_lower = request.lower()

    if any(term in request_lower for term in ['economy', 'macro']):
        return self.analyze_economy(context)
    elif any(term in request_lower for term in ['portfolio']):
        # Extract holdings from request string
        holdings = self._parse_holdings(request)
        return self.analyze_portfolio_risk(holdings, context)
    # ... 10+ more branches
```

**Target** (direct method exposure):
```python
# REMOVE process_request() entirely - rely on capability routing

# Keep existing analysis methods with proper signatures
def analyze_economy(self, context: Dict) -> Dict:
    """Analyze economic regime - DIRECTLY CALLABLE"""
    # Implementation...

def analyze_portfolio_risk(self, holdings: List[Dict], context: Dict) -> Dict:
    """Analyze portfolio risk - DIRECTLY CALLABLE"""
    # Implementation...

def calculate_dcf_valuation(
    self,
    symbol: str,
    growth_rate: float = 0.05,
    discount_rate: float = 0.10,
    terminal_growth: float = 0.03
) -> Dict:
    """Calculate DCF valuation - DIRECTLY CALLABLE with type hints"""
    # Implementation...
```

**Refactoring Process**:
1. Identify all methods called from routing logic
2. Ensure methods have proper type hints and signatures
3. Update AGENT_CAPABILITIES to include all methods
4. Remove/deprecate routing methods (process_request, harvest, etc.)
5. Update patterns to use capability routing
6. Test each method independently

---

### 2.3 Capability Registry Audit (3-4 hours)

**Goal**: Ensure AGENT_CAPABILITIES matches actual agent methods

**Audit Script**:
```python
# scripts/audit_capabilities.py

def audit_agent_capabilities():
    """Compare AGENT_CAPABILITIES with actual agent methods"""
    from dawsos.core.agent_capabilities import AGENT_CAPABILITIES
    from dawsos.core.agent_runtime import AgentRuntime

    runtime = AgentRuntime(None)
    discrepancies = []

    for agent_name, metadata in AGENT_CAPABILITIES.items():
        # Get agent instance
        agent = runtime.agents.get(agent_name)
        if not agent:
            continue

        # Check each capability
        for capability in metadata.get('capabilities', []):
            # Map to method name
            method_name = capability.replace('can_', '')

            # Check if method exists
            if not hasattr(agent, method_name):
                discrepancies.append({
                    'agent': agent_name,
                    'capability': capability,
                    'error': f'Method {method_name} not found'
                })

    # Find methods not in capabilities
    for agent_name, agent in runtime.agents.items():
        public_methods = [m for m in dir(agent)
                         if not m.startswith('_') and callable(getattr(agent, m))]

        declared_caps = set(AGENT_CAPABILITIES.get(agent_name, {}).get('capabilities', []))
        declared_methods = set(cap.replace('can_', '') for cap in declared_caps)

        undeclared = set(public_methods) - declared_methods
        if undeclared:
            discrepancies.append({
                'agent': agent_name,
                'error': f'Undeclared methods: {list(undeclared)}'
            })

    return discrepancies
```

---

## Phase 3: UI and Developer Experience (10-15 hours)

**Goal**: Make capability routing discoverable and usable

### 3.1 Capability Browser UI (6-8 hours)
**Priority**: ⚠️ MEDIUM
**File**: `dawsos/ui/capability_browser_tab.py`

**New Streamlit Tab**:
```python
def render_capability_browser(runtime: AgentRuntime):
    """Interactive capability browser"""
    st.title("🎯 Capability Browser")

    # Search bar
    query = st.text_input("Search capabilities:",
                         placeholder="e.g., 'calculate DCF' or 'fetch options'")

    if query:
        suggestions = runtime.suggest_capability(query)

        st.subheader("Suggested Capabilities")
        for sug in suggestions:
            with st.expander(f"📌 {sug['capability']} (Agent: {sug['agent']})"):
                # Show capability details
                st.write(f"**Relevance**: {sug['relevance']:.2f}")

                # Show example usage
                st.code(f"""
# Pattern usage:
{{
  "action": "execute_through_registry",
  "params": {{
    "capability": "{sug['capability']}",
    "context": {{ ... }}
  }}
}}

# Python usage:
result = runtime.execute_by_capability('{sug['capability']}', context)
                """, language='json')

    # Browse all capabilities
    st.subheader("All Capabilities by Agent")

    capabilities_map = runtime.list_all_capabilities()

    for agent_name, caps in capabilities_map.items():
        with st.expander(f"🤖 {agent_name} ({len(caps)} capabilities)"):
            for cap in sorted(caps):
                st.write(f"- `{cap}`")
```

### 3.2 Pattern Wizard (4-6 hours)
**Priority**: ℹ️ LOW
**File**: `dawsos/ui/pattern_wizard_tab.py`

**Interactive pattern creator**:
```python
def render_pattern_wizard():
    """Guided pattern creation using capability browser"""
    st.title("🪄 Pattern Wizard")

    # Step 1: Pattern metadata
    pattern_name = st.text_input("Pattern Name")
    description = st.text_area("Description")

    # Step 2: Add steps
    st.subheader("Steps")

    num_steps = st.number_input("Number of steps", min_value=1, max_value=10, value=1)

    steps = []
    for i in range(num_steps):
        with st.expander(f"Step {i+1}"):
            # Capability search
            cap_query = st.text_input(f"Search capability (step {i+1})")

            if cap_query:
                suggestions = runtime.suggest_capability(cap_query)
                cap = st.selectbox("Select capability",
                                  [s['capability'] for s in suggestions])

                # Parameter builder
                st.write("**Parameters:**")
                params = {}
                # ... dynamic parameter form based on method signature

                steps.append({
                    'action': 'execute_through_registry',
                    'params': {
                        'capability': cap,
                        'context': params
                    }
                })

    # Step 3: Generate pattern JSON
    if st.button("Generate Pattern"):
        pattern = {
            'name': pattern_name,
            'description': description,
            'steps': steps
        }

        st.code(json.dumps(pattern, indent=2), language='json')

        # Save button
        if st.button("Save Pattern"):
            # Save to patterns/ directory
            pass
```

---

## Phase 4: Testing and Validation (5-8 hours)

### 4.1 Capability Routing Tests (3-4 hours)

**New Test Suite**: `dawsos/tests/validation/test_capability_routing.py`
```python
import pytest
from dawsos.core.agent_runtime import AgentRuntime
from dawsos.core.knowledge_graph import KnowledgeGraph

@pytest.fixture
def runtime():
    graph = KnowledgeGraph()
    return AgentRuntime(graph)

def test_capability_discovery(runtime):
    """Test capability discovery API"""
    # Test finding agents with capability
    agents = runtime.get_agents_with_capability('can_calculate_dcf')
    assert 'financial_analyst' in agents

    # Test validation
    validation = runtime.validate_capability('can_calculate_dcf')
    assert validation['exists'] == True
    assert len(validation['agents']) > 0

def test_capability_execution(runtime):
    """Test executing by capability"""
    context = {
        'symbol': 'AAPL',
        'growth_rate': 0.08
    }

    result = runtime.execute_by_capability('can_calculate_dcf', context)

    assert 'error' not in result
    assert 'intrinsic_value' in result or 'valuation' in result

def test_capability_fallback(runtime):
    """Test graceful degradation to legacy routing"""
    context = {
        'capability': 'nonexistent_capability'
    }

    # Should not raise exception, should return error dict
    result = runtime.execute_by_capability('nonexistent_capability', context)
    assert 'error' in result

def test_capability_suggestion(runtime):
    """Test capability suggestion"""
    suggestions = runtime.suggest_capability('calculate discounted cash flow')

    assert len(suggestions) > 0
    assert any('dcf' in sug['capability'] for sug in suggestions)

def test_adapter_capability_routing(runtime):
    """Test AgentAdapter capability routing"""
    from dawsos.core.agent_adapter import AgentAdapter

    agent = runtime.agents['financial_analyst']
    adapter = AgentAdapter(agent, 'financial_analyst')

    context = {
        'capability': 'can_calculate_dcf',
        'symbol': 'MSFT'
    }

    result = adapter.execute(context)
    assert 'error' not in result
```

### 4.2 Pattern Migration Tests (2-3 hours)

**Test migrated patterns**:
```python
def test_migrated_pattern_execution(runtime, pattern_engine):
    """Test that migrated patterns execute successfully"""

    migrated_patterns = [
        'options_flow',
        'greeks_analysis',
        'dcf_valuation',
        # ... all migrated patterns
    ]

    for pattern_id in migrated_patterns:
        pattern = pattern_engine.get_pattern(pattern_id)
        assert pattern is not None

        # Execute with test context
        context = {'symbol': 'AAPL', 'tickers': ['SPY']}
        result = pattern_engine.execute_pattern(pattern, context)

        # Should not have errors
        assert 'error' not in result or result['error'] is None
```

### 4.3 Performance Benchmarks (1 hour)

**Compare legacy vs capability routing**:
```python
import time

def benchmark_routing_methods():
    """Compare legacy vs capability routing performance"""

    # Legacy routing (text parsing)
    start = time.time()
    for _ in range(100):
        result = runtime.exec_via_registry('financial_analyst', {
            'request': 'Calculate DCF for AAPL'
        })
    legacy_time = time.time() - start

    # Capability routing (direct method call)
    start = time.time()
    for _ in range(100):
        result = runtime.execute_by_capability('can_calculate_dcf', {
            'symbol': 'AAPL'
        })
    capability_time = time.time() - start

    print(f"Legacy routing: {legacy_time:.2f}s")
    print(f"Capability routing: {capability_time:.2f}s")
    print(f"Improvement: {(legacy_time / capability_time):.2f}x faster")
```

---

## Phase 5: Documentation and Migration Guide (3-5 hours)

### 5.1 Update Developer Guides (2-3 hours)

**Files to Update**:
- `docs/AgentDevelopmentGuide.md` - Add capability-first development pattern
- `docs/PatternDevelopmentGuide.md` - NEW: How to create capability-based patterns
- `CAPABILITY_ROUTING_GUIDE.md` - Update with new APIs and examples
- `CLAUDE.md` - Update principles to emphasize capability routing

**New Section in AgentDevelopmentGuide.md**:
```markdown
## Capability-First Development

### 1. Design Agent Methods with Clear Signatures

❌ **Don't** create generic routing methods:
```python
def process_request(self, request: str, context: Dict) -> Dict:
    if 'dcf' in request.lower():
        # Parse parameters from text
        symbol = extract_symbol(request)
        return self.calculate_dcf(symbol)
```

✅ **Do** create specific, type-safe methods:
```python
def calculate_dcf_valuation(
    self,
    symbol: str,
    growth_rate: float = 0.05,
    discount_rate: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate DCF valuation for a symbol

    Args:
        symbol: Stock ticker symbol
        growth_rate: Expected growth rate (default: 5%)
        discount_rate: WACC (default: calculated)

    Returns:
        Dict with intrinsic_value, margin_of_safety, etc.
    """
    # Implementation...
```

### 2. Register Capabilities in AGENT_CAPABILITIES

```python
# In dawsos/core/agent_capabilities.py
AGENT_CAPABILITIES = {
    'financial_analyst': {
        'capabilities': [
            'can_calculate_dcf',  # Maps to calculate_dcf_valuation()
            'can_analyze_moat',   # Maps to analyze_moat()
            # ...
        ]
    }
}
```

### 3. Create Capability-Based Patterns

```json
{
  "action": "execute_through_registry",
  "params": {
    "capability": "can_calculate_dcf",
    "context": {
      "symbol": "{SYMBOL}",
      "growth_rate": 0.08
    }
  }
}
```
```

### 5.2 Migration Playbook (1-2 hours)

**Create**: `docs/LEGACY_TO_CAPABILITY_MIGRATION.md`

```markdown
# Legacy to Capability Migration Playbook

## Step-by-Step Agent Migration

### Step 1: Audit Current Agent

List all methods called from routing logic:
```bash
grep -n "def process_request\|def harvest\|def think" dawsos/agents/your_agent.py
```

### Step 2: Extract Methods

For each routing branch:
1. Create dedicated method with proper signature
2. Add type hints
3. Add docstring
4. Remove text parsing logic

### Step 3: Update AGENT_CAPABILITIES

Add capability for each method:
- Method: `fetch_market_data()` → Capability: `can_fetch_market_data`

### Step 4: Update Patterns

Convert patterns using this agent:
- Find: `grep -r "\"agent\": \"your_agent\"" dawsos/patterns/`
- Convert to capability routing

### Step 5: Test

```python
# Test each capability
result = runtime.execute_by_capability('can_fetch_market_data', {})
assert 'error' not in result
```

### Step 6: Deprecate Legacy Methods

Add deprecation warning:
```python
def process_request(self, request: str, context: Dict) -> Dict:
    warnings.warn(
        "process_request is deprecated, use capability routing",
        DeprecationWarning
    )
    # ... keep for backward compatibility
```
```

---

## Success Criteria

### Phase 1 (Capability Infrastructure)
- ✅ AgentAdapter supports capability→method mapping
- ✅ Capability discovery API operational
- ✅ Graceful degradation works
- ✅ Pattern linter validates capabilities

### Phase 2 (Pattern Migration)
- ✅ 100% of patterns use capability routing (46/46)
- ✅ Agent routing methods deprecated
- ✅ AGENT_CAPABILITIES matches actual methods

### Phase 3 (UI/UX)
- ✅ Capability browser accessible in UI
- ✅ Developers can discover capabilities interactively
- ✅ Pattern wizard functional

### Phase 4 (Testing)
- ✅ 100% capability routing tests pass
- ✅ Performance benchmarks show improvement
- ✅ All migrated patterns execute successfully

### Phase 5 (Documentation)
- ✅ Developer guides updated
- ✅ Migration playbook complete
- ✅ CLAUDE.md reflects capability-first approach

---

## Risk Assessment

### Low Risk
- Phase 1.2-1.4: New APIs, no breaking changes
- Phase 3: UI additions, optional features
- Phase 5: Documentation only

### Medium Risk
- Phase 1.1: AgentAdapter changes affect all executions
  - **Mitigation**: Maintain legacy code path, extensive testing
- Phase 2.3: Capability registry audit may find gaps
  - **Mitigation**: Gradual rollout, fix discrepancies incrementally

### High Risk
- Phase 2.1-2.2: Pattern migration and agent refactoring
  - **Mitigation**: Migrate in small batches, test after each batch
  - **Rollback Plan**: Keep legacy routing methods until 100% migration complete

---

## Timeline

### Week 1: Infrastructure (20-25 hours)
- Days 1-2: AgentAdapter enhancement (1.1)
- Days 3-4: Discovery API (1.2) + Graceful degradation (1.3)
- Day 5: Pattern validation (1.4)

### Week 2: Migration (25-30 hours)
- Days 1-3: Pattern migration batches 1-3 (2.1)
- Days 4-5: Agent refactoring (2.2) + Capability audit (2.3)

### Week 3: Polish (15-20 hours)
- Days 1-2: Capability browser UI (3.1)
- Day 3: Testing (4.1-4.2)
- Days 4-5: Documentation (5.1-5.2) + Pattern wizard (3.2)

**Total**: 60-75 hours over 3 weeks

---

## Metrics Tracking

| Metric | Current | Phase 1 | Phase 2 | Phase 3 | Target |
|--------|---------|---------|---------|---------|--------|
| **Capability Patterns** | 3/46 (6.5%) | 3/46 | 46/46 (100%) | 46/46 | 100% |
| **Agent Routing Methods** | 15 agents | 15 | 0 deprecated | 0 | 0 |
| **Capability Coverage** | 103 declared | 103 | 103 validated | 103 | 100% match |
| **Pattern Lint Errors** | 0 | 0 | 0 | 0 | 0 |
| **Test Coverage** | - | 50% | 75% | 90% | 90% |

---

## Long-Term Vision

**Trinity 3.0 (Future)**:
- AI-powered capability suggestion
- Auto-generate patterns from natural language
- Capability composition (chaining capabilities)
- Dynamic agent creation from capability specs
- Capability marketplace (plugins)

**Foundation**: This refactoring plan lays the groundwork for Trinity 3.0 by:
1. Establishing capability as first-class concept
2. Removing text-parsing brittleness
3. Enabling type-safe, composable execution
4. Creating discoverable, self-documenting system

---

**Status**: Ready for implementation
**Next Step**: Review and approve Phase 1 scope
**Contact**: See CLAUDE.md for development principles
