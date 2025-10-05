# Capability-Based Routing Guide

**Date**: October 4, 2025 (Updated with migrated capabilities)
**Status**: ✅ Implemented & Ready to Use

---

## Overview

DawsOS now supports **capability-based agent routing**, allowing patterns and scripts to request agents by what they can do rather than by name. This makes workflows more flexible and maintainable.

---

## Quick Start

### Traditional Name-Based Routing
```python
# Old way - hardcoded agent name
result = runtime.exec_via_registry('financial_analyst', context)
```

### New Capability-Based Routing
```python
# New way - request by capability
result = runtime.execute_by_capability('can_calculate_dcf', context)
```

---

## Available Capabilities

### Data Capabilities
- `can_fetch_stock_quotes` - Get market data (data_harvester)
- `can_fetch_economic_data` - FRED indicators (data_harvester)
- `can_fetch_news` - News articles (data_harvester)
- `can_fetch_fundamentals` - Financial statements (data_harvester)

### Analysis Capabilities

**Financial Analysis** (financial_analyst):
- `can_calculate_dcf` - DCF valuation with graph-based assumptions
- `can_calculate_roic` - Return on invested capital
- `can_analyze_moat` - Competitive advantage analysis
- `can_analyze_stock_comprehensive` - Full equity analysis with macro influences (migrated Oct 2025)
- `can_compare_stocks` - Side-by-side comparison with peer positioning (migrated Oct 2025)
- `can_analyze_economy` - Economic regime detection (goldilocks/stagflation/recession) (migrated Oct 2025)
- `can_analyze_portfolio_risk` - Portfolio concentration and correlation analysis (migrated Oct 2025)

**Pattern Detection** (pattern_spotter):
- `can_detect_patterns` - Pattern recognition (sequences, cycles, triggers)
- `can_detect_anomalies` - Graph anomaly detection
- `can_analyze_market_regime` - Risk-on/risk-off detection

**Other**:
- `can_calculate_correlations` - Correlation analysis (data_harvester, relationship_hunter)
- `can_analyze_sentiment` - News sentiment (financial_analyst)

### Graph Capabilities
- `can_manage_graph_structure` - Node/edge operations (graph_mind)
- `can_query_relationships` - Graph traversal (graph_mind)
- `can_add_nodes` - Create nodes (graph_mind)
- `can_find_paths` - Path finding (graph_mind)

### Governance Capabilities
- `can_validate_data_quality` - Quality checks (governance_agent)
- `can_enforce_policies` - Policy compliance (governance_agent)
- `can_audit_lineage` - Data lineage (governance_agent)

### Code Capabilities
- `can_generate_code` - Code creation (code_monkey)
- `can_refactor_code` - Code improvements (refactor_elf)
- `can_design_architecture` - System design (structure_bot)

### Workflow Capabilities
- `can_record_workflows` - Capture patterns (workflow_recorder)
- `can_execute_workflows` - Run workflows (workflow_player)

---

## Usage in Patterns

### Pattern JSON with Capability Routing

```json
{
  "id": "smart_analysis",
  "version": "2.0",
  "steps": [
    {
      "description": "Fetch market data using any capable agent",
      "action": "execute_by_capability",
      "params": {
        "capability": "can_fetch_stock_quotes",
        "context": {
          "symbol": "{user_input}",
          "period": "1y"
        }
      },
      "save_as": "market_data"
    },
    {
      "description": "Analyze using any agent that can detect patterns",
      "action": "execute_by_capability",
      "params": {
        "capability": "can_detect_patterns",
        "context": {
          "data": "{market_data}",
          "timeframe": "daily"
        }
      },
      "save_as": "patterns"
    }
  ]
}
```

---

## Usage in Python Code

### AgentRuntime Method
```python
from core.agent_runtime import AgentRuntime

runtime = AgentRuntime()

# Execute by capability
result = runtime.execute_by_capability(
    capability='can_calculate_dcf',
    context={
        'symbol': 'AAPL',
        'projection_years': 5
    }
)
```

### AgentRegistry Method
```python
from core.agent_adapter import AgentRegistry

registry = AgentRegistry()

# Find agent by capability
result = registry.execute_by_capability(
    capability='can_fetch_news',
    context={
        'query': 'AI technology',
        'days': 7
    }
)
```

---

## Benefits

### 1. Flexibility
Agents can be swapped without changing patterns:
```python
# Before: Hard to swap data_harvester for a different agent
result = runtime.exec_via_registry('data_harvester', context)

# After: Any agent with capability works
result = runtime.execute_by_capability('can_fetch_stock_quotes', context)
```

### 2. Discoverability
Find agents by what they do:
```python
# List all agents that can fetch data
capable_agents = registry.find_agents_by_capability('can_fetch_stock_quotes')
# Returns: ['data_harvester']
```

### 3. Graceful Degradation
Fallback to alternative agents:
```python
# If primary agent unavailable, use any capable agent
result = runtime.execute_by_capability('can_detect_patterns', context)
# Will use first available: pattern_spotter, financial_analyst, etc.
```

---

## Capability Registry

All agent capabilities are defined in `dawsos/core/agent_capabilities.py`:

```python
AGENT_CAPABILITIES = {
    'financial_analyst': {
        'capabilities': [
            'can_calculate_dcf',
            'can_calculate_owner_earnings',
            'can_analyze_moat',
            'can_calculate_intrinsic_value'
        ],
        'requires': ['requires_llm_client'],
        'provides': ['provides_valuation_data']
    },
    # ... 18 more agents
}
```

---

## Adding New Capabilities

### 1. Define Capability in Agent
```python
# In agent_capabilities.py
'my_new_agent': {
    'capabilities': [
        'can_do_new_thing',  # Add new capability
        'can_analyze_data'
    ],
    'requires': ['requires_api_key'],
    'provides': ['provides_insights']
}
```

### 2. Register Agent with Capabilities
```python
# In main.py
runtime.agent_registry.register(
    'my_new_agent',
    agent_instance,
    capabilities=AGENT_CAPABILITIES['my_new_agent']
)
```

### 3. Use in Patterns
```json
{
  "action": "execute_by_capability",
  "params": {
    "capability": "can_do_new_thing",
    "context": {...}
  }
}
```

---

## Migration Guide

### Step 1: Identify Hardcoded Agent Names
```bash
# Find patterns using agent names
grep -r "agent.*:" dawsos/patterns/
```

### Step 2: Map to Capabilities
```python
# Old pattern
{
  "action": "execute_through_registry",
  "params": {
    "agent": "financial_analyst",
    "context": {"task": "dcf"}
  }
}

# New pattern
{
  "action": "execute_by_capability",
  "params": {
    "capability": "can_calculate_dcf",
    "context": {"task": "dcf"}
  }
}
```

### Step 3: Test Migration
```bash
# Run pattern linter
python3 scripts/lint_patterns.py

# Test execution
python3 -m pytest dawsos/tests/validation/
```

---

## Best Practices

### 1. Use Specific Capabilities
```python
# Good: Specific capability
runtime.execute_by_capability('can_calculate_dcf', context)

# Avoid: Too generic
runtime.execute_by_capability('can_analyze', context)
```

### 2. Provide Context
```python
# Good: Clear context
context = {
    'symbol': 'AAPL',
    'period': '5y',
    'method': 'dcf'
}

# Avoid: Vague context
context = {'data': 'stuff'}
```

### 3. Handle Failures Gracefully
```python
try:
    result = runtime.execute_by_capability('can_fetch_data', context)
except Exception as e:
    # Fallback to alternative
    result = runtime.exec_via_registry('data_harvester', context)
```

---

## Troubleshooting

### No Agent Found for Capability
```python
# Error: No agent registered with capability
result = runtime.execute_by_capability('nonexistent_capability', context)

# Solution: Check capability spelling
print(registry.list_all_capabilities())
```

### Multiple Agents Have Capability
```python
# Behavior: First registered agent wins
result = runtime.execute_by_capability('can_analyze_data', context)

# To control: Use specific capability
result = runtime.execute_by_capability('can_calculate_correlations', context)
```

### Capability Not Registered
```python
# Error: Agent has capability but not registered
# Solution: Update AGENT_CAPABILITIES in agent_capabilities.py
AGENT_CAPABILITIES['my_agent']['capabilities'].append('can_new_feature')
```

---

## Examples

### Example 1: Dynamic Market Analysis
```python
def analyze_stock(symbol: str):
    """Analyze stock using capability routing"""

    # Fetch data with any capable agent
    market_data = runtime.execute_by_capability(
        'can_fetch_stock_quotes',
        {'symbol': symbol, 'period': '1y'}
    )

    # Analyze with any pattern detection agent
    patterns = runtime.execute_by_capability(
        'can_detect_patterns',
        {'data': market_data, 'timeframe': 'daily'}
    )

    # Calculate valuation with any capable agent
    valuation = runtime.execute_by_capability(
        'can_calculate_dcf',
        {'symbol': symbol, 'data': market_data}
    )

    return {
        'data': market_data,
        'patterns': patterns,
        'valuation': valuation
    }
```

### Example 2: Governance Workflow
```python
def run_governance_check(node_id: str):
    """Run governance using capabilities"""

    # Validate quality
    quality = runtime.execute_by_capability(
        'can_validate_data_quality',
        {'node_id': node_id}
    )

    # Audit lineage
    lineage = runtime.execute_by_capability(
        'can_audit_lineage',
        {'node_id': node_id, 'depth': 3}
    )

    # Enforce policies
    compliance = runtime.execute_by_capability(
        'can_enforce_policies',
        {'node_id': node_id, 'policies': ['data_retention']}
    )

    return {
        'quality_score': quality,
        'lineage_depth': lineage,
        'compliant': compliance
    }
```

---

## API Reference

### AgentRuntime.execute_by_capability
```python
def execute_by_capability(
    self,
    capability: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute first agent with specified capability.

    Args:
        capability: Capability string (e.g., 'can_fetch_data')
        context: Execution context

    Returns:
        Agent execution result

    Raises:
        ValueError: If no agent has capability
    """
```

### AgentRegistry.find_agents_by_capability
```python
def find_agents_by_capability(
    self,
    capability: str
) -> List[str]:
    """
    Find all agents with specified capability.

    Args:
        capability: Capability to search for

    Returns:
        List of agent names with capability
    """
```

---

## Future Enhancements

### Priority-Based Selection
```python
# Future: Select agent by priority
result = runtime.execute_by_capability(
    'can_fetch_data',
    context,
    prefer_priority='high'  # Select high-priority agent
)
```

### Capability Composition
```python
# Future: Combine capabilities
result = runtime.execute_by_capabilities(
    ['can_fetch_data', 'can_analyze_data'],
    context,
    mode='pipeline'  # Execute in sequence
)
```

### Capability Metrics
```python
# Future: Track capability usage
metrics = registry.get_capability_metrics('can_calculate_dcf')
# Returns: {uses: 150, success_rate: 0.98, avg_duration: 2.3}
```

---

## Resources

- **Capability Definitions**: `dawsos/core/agent_capabilities.py`
- **Runtime Implementation**: `dawsos/core/agent_runtime.py:200`
- **Registry Implementation**: `dawsos/core/agent_adapter.py`
- **Pattern Examples**: `dawsos/patterns/analysis/`
- **Tests**: `dawsos/tests/validation/test_trinity_smoke.py`

---

**Last Updated**: October 3, 2025
**Status**: ✅ Production Ready
**Version**: 2.0
