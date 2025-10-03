# DawsOS Trinity Agent Development Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Agent Basics](#agent-basics)
3. [Creating a New Agent](#creating-a-new-agent)
4. [Implementing Core Methods](#implementing-core-methods)
5. [Registering Capabilities](#registering-capabilities)
6. [Integration with AgentRegistry](#integration-with-agentregistry)
7. [Trinity Architecture Compliance](#trinity-architecture-compliance)
8. [Testing Your Agent](#testing-your-agent)
9. [Common Patterns](#common-patterns)
10. [Troubleshooting](#troubleshooting)
11. [Development Checklist](#development-checklist)

---

## Introduction

The DawsOS Trinity system is a multi-agent architecture where specialized agents collaborate through a shared knowledge graph. This guide will walk you through creating new agents that integrate seamlessly with the Trinity ecosystem.

**Key Principles:**
- **Specialized Focus**: Each agent has a specific domain of expertise
- **Knowledge Graph Integration**: All agents store results in the shared knowledge graph
- **Adapter Pattern**: AgentAdapter provides a consistent interface across all agents
- **Automatic Compliance**: Trinity architecture ensures all agent results are tracked and stored

---

## Agent Basics

### What Are Agents?

Agents in DawsOS Trinity are specialized AI components that:
- Perform specific tasks (data retrieval, analysis, forecasting, etc.)
- Store results in the shared knowledge graph
- Integrate with other agents through the graph
- Follow consistent execution patterns via AgentAdapter

### Agent Categories

The system currently supports these agent categories:

| Category | Purpose | Example Agents |
|----------|---------|----------------|
| **orchestration** | Request routing and coordination | claude |
| **core** | Graph operations and management | graph_mind |
| **data** | Data fetching and processing | data_harvester, data_digester |
| **analysis** | Pattern detection and insights | pattern_spotter, relationship_hunter |
| **financial** | Financial modeling and valuation | financial_analyst |
| **development** | Code generation and refactoring | code_monkey, structure_bot, refactor_elf |
| **workflow** | Workflow recording and replay | workflow_recorder, workflow_player |
| **presentation** | UI generation and visualization | ui_generator |
| **governance** | Quality, compliance, and auditing | governance_agent |

### How Agents Fit in Trinity

```
User Request
    ↓
UniversalExecutor (Pattern matching)
    ↓
AgentRuntime (Orchestration)
    ↓
AgentAdapter (Unified interface)
    ↓
Specific Agent (Execution)
    ↓
Knowledge Graph (Storage)
```

---

## Creating a New Agent

### File Structure

All agents live in `/dawsos/agents/`. Create a new file for your agent:

```bash
/dawsos/agents/my_new_agent.py
```

### Base Class Requirements

All agents must inherit from `BaseAgent`:

```python
from agents.base_agent import BaseAgent
from typing import Dict, Any

class MyNewAgent(BaseAgent):
    """Agent that does something amazing"""

    def __init__(self, graph, capabilities: Dict = None, llm_client=None):
        super().__init__(
            graph=graph,
            name="my_new_agent",
            llm_client=llm_client
        )
        self.capabilities = capabilities or {}
        # Add any agent-specific initialization
```

### Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `graph` | KnowledgeGraph | Yes | Shared knowledge graph instance |
| `capabilities` | Dict | No | Dictionary of external capabilities (APIs, services) |
| `llm_client` | LLMClient | No | LLM client for AI-powered agents |

---

## Implementing Core Methods

The `AgentAdapter` looks for these methods in priority order:
1. `process(context)`
2. `think(context)`
3. `analyze(query)`
4. `interpret(user_input)`
5. `harvest(request)`
6. `execute(context)`

### Method: process() - Recommended

The `process()` method is the most flexible and recommended approach:

```python
def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main processing method called by AgentAdapter

    Args:
        context: Dictionary containing:
            - user_input: The user's request
            - query: Alternative to user_input
            - capabilities: Injected capabilities
            - query_node_id: Optional query node for graph linking

    Returns:
        Dictionary with at minimum:
            - response: String response to user
            - data: Optional structured data
            - node_id: Optional graph node ID (if stored)
    """
    user_input = context.get('user_input', '')

    # Your agent logic here
    result = self._do_something_amazing(user_input)

    # Store in knowledge graph (Trinity compliance)
    node_id = self.store_result(result, context)

    return {
        'response': f"Successfully processed: {user_input}",
        'data': result,
        'node_id': node_id
    }
```

### Required Return Format

**All agent methods MUST return a dictionary with a 'response' key:**

```python
# CORRECT ✓
return {
    'response': 'Analysis complete',
    'data': analysis_results,
    'node_id': 'analysis_123'
}

# INCORRECT ✗
return "Analysis complete"  # String not allowed
return analysis_results     # Direct dict without 'response' key
```

### Real Example: DataHarvester

```python
class DataHarvester(BaseAgent):
    def __init__(self, graph, capabilities: Dict = None, llm_client=None):
        super().__init__(graph=graph, name="DataHarvester", llm_client=llm_client)
        self.capabilities = capabilities or {}

    def process(self, request: str) -> Dict[str, Any]:
        """Process method for compatibility"""
        result = self.harvest(request)

        # Store result in knowledge graph (Trinity compliance)
        if self.graph and isinstance(result, dict):
            node_id = self.store_result(result)
            result['node_id'] = node_id

        return result

    def harvest(self, request: str) -> Dict[str, Any]:
        """Main harvest method - fetches requested data"""
        request_lower = request.lower()

        # Extract symbols from request
        import re
        symbols = re.findall(r'\b[A-Z]{1,5}\b', request)

        # Use market capability if available
        if symbols and 'market' in self.capabilities:
            market = self.capabilities['market']
            data = {}

            for symbol in symbols[:5]:  # Limit to 5 symbols
                quote = market.get_quote(symbol)
                if 'error' not in quote:
                    data[symbol] = quote

            if data:
                return {
                    'response': f'Fetched market data for {", ".join(symbols)}',
                    'data': data
                }

        return {
            'response': f'Processed request: {request}',
            'data': {}
        }
```

### Real Example: FinancialAnalyst

```python
class FinancialAnalyst(BaseAgent):
    def __init__(self, graph=None, llm_client=None):
        super().__init__(graph=graph, name="financial_analyst", llm_client=llm_client)
        self.capabilities_needed = ['market', 'enriched_data']

    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process financial analysis requests"""
        if context is None:
            context = {}

        request_lower = request.lower()

        # DCF Valuation
        if any(term in request_lower for term in ['dcf', 'discounted cash flow']):
            return self._perform_dcf_analysis(request, context)

        # ROIC Calculation
        elif any(term in request_lower for term in ['roic', 'return on invested capital']):
            return self._calculate_roic(request, context)

        # Default response
        return {
            'response': 'Please specify a financial analysis type (DCF, ROIC, etc.)',
            'capabilities': ['DCF valuation', 'ROIC calculation', 'FCF analysis']
        }

    def _perform_dcf_analysis(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform DCF analysis with graph storage"""
        symbol = self._extract_symbol(request, context)

        # Perform calculation
        intrinsic_value = self._calculate_dcf(symbol)

        # Store in graph
        dcf_node_data = {
            'symbol': symbol,
            'intrinsic_value': intrinsic_value,
            'timestamp': datetime.now().isoformat()
        }

        node_id = self.add_knowledge('dcf_analysis', dcf_node_data)

        return {
            'response': f'DCF analysis for {symbol} shows intrinsic value of ${intrinsic_value:.2f}',
            'data': dcf_node_data,
            'node_id': node_id
        }
```

---

## Registering Capabilities

### Step 1: Add to agent_capabilities.py

Edit `/dawsos/core/agent_capabilities.py` and add your agent to `AGENT_CAPABILITIES`:

```python
AGENT_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    # ... existing agents ...

    'my_new_agent': {
        'description': 'Brief description of what your agent does',
        'capabilities': [
            'can_do_something',      # Action verbs: can_*, has_*, provides_*
            'can_do_something_else',
            'can_integrate_with_api'
        ],
        'requires': [
            'requires_knowledge_graph',  # Dependencies
            'requires_market_capability',
            'requires_llm_client'
        ],
        'provides': [
            'provides_analysis_results',  # What this agent outputs
            'provides_insights',
            'provides_recommendations'
        ],
        'integrates_with': [
            'data_harvester',    # List of agents this works with
            'pattern_spotter',
            'graph_mind'
        ],
        'stores_results': True,  # True if stores in knowledge graph
        'priority': 'medium',    # critical, high, medium, low
        'category': 'analysis'   # See categories in agent_capabilities.py
    }
}
```

### Capability Naming Conventions

| Prefix | Usage | Examples |
|--------|-------|----------|
| `can_*` | Actions the agent performs | can_fetch_data, can_analyze_patterns |
| `requires_*` | Dependencies needed | requires_llm_client, requires_market_capability |
| `provides_*` | Outputs produced | provides_forecasts, provides_visualizations |
| `has_*` | Built-in features | has_caching, has_rate_limiting |

### Step 2: Add to Category

Add your agent to the appropriate category in `CAPABILITY_CATEGORIES`:

```python
CAPABILITY_CATEGORIES = {
    'analysis': ['relationship_hunter', 'pattern_spotter', 'forecast_dreamer', 'my_new_agent'],
    # ... other categories ...
}
```

### Step 3: Define Integration Matrix (Optional)

If your agent commonly works with specific other agents, add to `AGENT_INTEGRATION_MATRIX`:

```python
AGENT_INTEGRATION_MATRIX = {
    'my_new_agent': ['data_harvester', 'graph_mind', 'pattern_spotter'],
    # ... other integrations ...
}
```

---

## Integration with AgentRegistry

### How Registration Works

The `AgentRegistry` provides automatic Trinity compliance:

1. **Registration**: Agent is wrapped in `AgentAdapter`
2. **Method Detection**: Adapter detects available methods (process, think, analyze, etc.)
3. **Execution Tracking**: All executions are logged with metrics
4. **Graph Storage**: Results are automatically stored in knowledge graph
5. **Compliance Metrics**: System tracks which agents store results properly

### Registering Your Agent

In `/dawsos/main.py` or your initialization code:

```python
from agents.my_new_agent import MyNewAgent
from core.agent_runtime import AgentRuntime

# Initialize runtime
runtime = AgentRuntime()

# Create agent instance
my_agent = MyNewAgent(
    graph=knowledge_graph,
    capabilities={'market': market_capability},
    llm_client=llm_client
)

# Register with runtime
runtime.register_agent(
    name='my_new_agent',
    agent=my_agent,
    capabilities={
        'can_do_something': True,
        'category': 'analysis'
    }
)
```

### What Gets Tracked

The registry automatically tracks:
- Total executions per agent
- Successful graph storage count
- Failure count and reasons
- Last success/failure timestamps
- Compliance rate (% of executions that stored results)

View metrics:

```python
metrics = runtime.get_compliance_metrics()
print(metrics)
# Output:
# {
#     'agents': {
#         'my_new_agent': {
#             'executions': 42,
#             'stored': 40,
#             'compliance_rate': 95.24,
#             'failures': 2
#         }
#     },
#     'overall_compliance': 96.5
# }
```

---

## Trinity Architecture Compliance

### Why Compliance Matters

Trinity Architecture requires all agent results to be stored in the knowledge graph for:
- **Traceability**: Track what agents did and when
- **Knowledge Accumulation**: Build up system intelligence over time
- **Inter-agent Communication**: Agents share insights through the graph
- **Audit Trail**: Governance and debugging capabilities

### Automatic Storage via AgentAdapter

The `AgentAdapter` automatically stores results when:
1. Agent has a `graph` attribute
2. Result is a dictionary
3. Agent method returns successfully

```python
# In AgentAdapter.execute():
if hasattr(self.agent, 'graph') and self.agent.graph:
    try:
        # Use store_result if available
        if hasattr(self.agent, 'store_result'):
            node_id = self.agent.store_result(result, context)
        else:
            # Direct graph access
            node_id = self.agent.graph.add_node(
                f'{self.agent.__class__.__name__.lower()}_result',
                {'result': result, 'context': context}
            )
        result['node_id'] = node_id
        result['graph_stored'] = True
    except Exception:
        result['graph_stored'] = False
```

### Manual Storage with store_result()

For more control, use `BaseAgent.store_result()`:

```python
def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
    # Perform analysis
    analysis_result = self._analyze(context['user_input'])

    # Manually store with custom metadata
    node_id = self.store_result(
        result=analysis_result,
        context=context  # Links to query_node_id if present
    )

    return {
        'response': 'Analysis complete',
        'data': analysis_result,
        'node_id': node_id
    }
```

### Linking Results to Queries

Connect your result to the original query:

```python
# In your agent method
if context.get('query_node_id'):
    self.connect_knowledge(
        from_id=context['query_node_id'],
        to_id=node_id,
        relationship='resulted_in',
        strength=0.9
    )
```

### Best Practices for Graph Storage

1. **Store Structured Data**: Use meaningful node types
2. **Add Timestamps**: Always include `datetime.now().isoformat()`
3. **Link Related Nodes**: Connect to company, sector, or query nodes
4. **Use Appropriate Strengths**: 0.9+ for direct results, 0.5-0.8 for inferred relationships
5. **Include Metadata**: Add confidence scores, methodology, data sources

---

## Testing Your Agent

### Unit Tests

Create `/dawsos/tests/test_my_new_agent.py`:

```python
import pytest
from agents.my_new_agent import MyNewAgent
from core.knowledge_graph import KnowledgeGraph

class TestMyNewAgent:
    @pytest.fixture
    def graph(self):
        """Create test knowledge graph"""
        return KnowledgeGraph()

    @pytest.fixture
    def agent(self, graph):
        """Create test agent"""
        return MyNewAgent(graph=graph)

    def test_process_basic(self, agent):
        """Test basic processing"""
        context = {'user_input': 'test query'}
        result = agent.process(context)

        # Verify return format
        assert isinstance(result, dict)
        assert 'response' in result
        assert 'data' in result

    def test_graph_storage(self, agent, graph):
        """Test that results are stored in graph"""
        initial_node_count = len(graph.nodes)

        context = {'user_input': 'test query'}
        result = agent.process(context)

        # Verify graph storage
        assert len(graph.nodes) > initial_node_count
        assert 'node_id' in result
        assert result['node_id'] in graph.nodes

    def test_with_capabilities(self, agent):
        """Test agent with external capabilities"""
        agent.capabilities = {'test_capability': MockCapability()}

        context = {'user_input': 'use capability'}
        result = agent.process(context)

        assert result['response'] is not None
```

### Integration Tests

Test agent integration with the runtime:

```python
def test_agent_runtime_integration():
    """Test agent works with AgentRuntime"""
    from core.agent_runtime import AgentRuntime

    runtime = AgentRuntime()
    graph = KnowledgeGraph()
    agent = MyNewAgent(graph=graph)

    # Register agent
    runtime.register_agent('my_new_agent', agent)

    # Execute through runtime
    result = runtime.execute('my_new_agent', {
        'user_input': 'test query'
    })

    assert 'response' in result
    assert 'graph_stored' in result
    assert result['graph_stored'] is True
```

### Compliance Validation

Test Trinity compliance:

```python
def test_trinity_compliance():
    """Test agent follows Trinity Architecture"""
    runtime = AgentRuntime()
    graph = KnowledgeGraph()
    agent = MyNewAgent(graph=graph)

    runtime.register_agent('my_new_agent', agent)

    # Execute multiple times
    for i in range(10):
        runtime.execute('my_new_agent', {'user_input': f'test {i}'})

    # Check compliance metrics
    metrics = runtime.get_compliance_metrics()
    agent_metrics = metrics['agents']['my_new_agent']

    assert agent_metrics['executions'] == 10
    assert agent_metrics['compliance_rate'] > 90  # >90% should store successfully
```

### Running Tests

```bash
# Run all tests
pytest dawsos/tests/test_my_new_agent.py -v

# Run specific test
pytest dawsos/tests/test_my_new_agent.py::TestMyNewAgent::test_process_basic -v

# Run with coverage
pytest dawsos/tests/test_my_new_agent.py --cov=agents.my_new_agent --cov-report=html
```

---

## Common Patterns

### Pattern 1: Data Retrieval Agent

**Purpose**: Fetch data from external APIs or databases

```python
class DataRetrieverAgent(BaseAgent):
    def __init__(self, graph, capabilities: Dict = None, llm_client=None):
        super().__init__(graph=graph, name="data_retriever", llm_client=llm_client)
        self.capabilities = capabilities or {}

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        query = context.get('user_input', '')

        # Extract what to fetch
        entity = self._extract_entity(query)

        # Fetch from external source
        if 'api_capability' in self.capabilities:
            data = self.capabilities['api_capability'].fetch(entity)
        else:
            return {'response': 'API capability not available', 'data': {}}

        # Store in graph
        data_node = {
            'entity': entity,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'source': 'external_api'
        }

        node_id = self.add_knowledge('external_data', data_node)

        return {
            'response': f'Successfully fetched data for {entity}',
            'data': data,
            'node_id': node_id
        }
```

### Pattern 2: Analysis Agent

**Purpose**: Analyze data and produce insights

```python
class AnalysisAgent(BaseAgent):
    def __init__(self, graph, capabilities: Dict = None, llm_client=None):
        super().__init__(graph=graph, name="analyzer", llm_client=llm_client)

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        query = context.get('user_input', '')

        # Find relevant data in graph
        relevant_nodes = self._find_relevant_nodes(query)

        # Perform analysis
        insights = []
        for node_id in relevant_nodes:
            connections = self.graph.trace_connections(node_id, max_depth=2)
            insight = self._analyze_connections(connections)
            insights.append(insight)

        # Store analysis result
        analysis_data = {
            'query': query,
            'insights': insights,
            'analyzed_nodes': relevant_nodes,
            'timestamp': datetime.now().isoformat()
        }

        node_id = self.store_result(analysis_data, context)

        return {
            'response': f'Found {len(insights)} insights',
            'data': analysis_data,
            'node_id': node_id
        }
```

### Pattern 3: Synthesis Agent

**Purpose**: Combine multiple data sources into unified insights

```python
class SynthesisAgent(BaseAgent):
    def __init__(self, graph, capabilities: Dict = None, llm_client=None):
        super().__init__(graph=graph, name="synthesizer", llm_client=llm_client)
        self.llm_client = llm_client

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        query = context.get('user_input', '')

        # Gather data from multiple sources
        market_data = self._get_market_data(query)
        news_data = self._get_news_data(query)
        graph_data = self._get_graph_insights(query)

        # Use LLM to synthesize
        if self.llm_client:
            synthesis = self.llm_client.generate(
                prompt=f"Synthesize these data sources: Market: {market_data}, News: {news_data}, Graph: {graph_data}",
                max_tokens=500
            )
        else:
            synthesis = self._rule_based_synthesis(market_data, news_data, graph_data)

        # Store synthesis
        synthesis_data = {
            'query': query,
            'synthesis': synthesis,
            'sources': {
                'market': market_data,
                'news': news_data,
                'graph': graph_data
            },
            'timestamp': datetime.now().isoformat()
        }

        node_id = self.store_result(synthesis_data, context)

        return {
            'response': synthesis,
            'data': synthesis_data,
            'node_id': node_id
        }
```

---

## Troubleshooting

### Common Errors

#### 1. "No execution method found for AgentName"

**Cause**: Agent doesn't implement any recognized methods (process, think, analyze, etc.)

**Solution**: Implement at least one of these methods:
```python
def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
    # Your implementation
    return {'response': 'result'}
```

#### 2. "Agent results not being stored in graph"

**Cause**: Agent doesn't have `graph` attribute or `store_result()` not called

**Solution**: Ensure graph is passed to constructor and stored:
```python
def __init__(self, graph, **kwargs):
    super().__init__(graph=graph, name="my_agent")
    # self.graph is now available
```

#### 3. "Compliance rate is low"

**Cause**: Agent is throwing exceptions or returning invalid formats

**Solution**:
- Always return a dict with 'response' key
- Wrap operations in try/except
- Log errors for debugging

```python
def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = self._do_work(context)
        node_id = self.store_result(result, context)
        return {
            'response': 'Success',
            'data': result,
            'node_id': node_id
        }
    except Exception as e:
        logging.error(f"Agent error: {e}")
        return {
            'response': f'Error: {str(e)}',
            'error': str(e)
        }
```

#### 4. "Capability not found"

**Cause**: Required capability not passed during initialization

**Solution**: Check capabilities before using:
```python
def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
    if 'market' not in self.capabilities:
        return {
            'response': 'Market capability required',
            'error': 'Missing required capability: market'
        }

    market = self.capabilities['market']
    # Use market capability
```

### Debugging Tips

1. **Enable Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MyAgent(BaseAgent):
    def process(self, context):
        logger.debug(f"Processing: {context}")
        # ... your code
```

2. **Check Registry Status**:
```python
# In your code or debugger
runtime = AgentRuntime()
print(runtime.get_status())
print(runtime.get_compliance_metrics())
```

3. **Inspect Graph Nodes**:
```python
# After agent execution
for node_id, node in graph.nodes.items():
    if node['type'] == 'my_agent_result':
        print(f"Node {node_id}: {node}")
```

4. **Test in Isolation**:
```python
# Test agent without runtime
graph = KnowledgeGraph()
agent = MyAgent(graph=graph)
result = agent.process({'user_input': 'test'})
print(result)
print(f"Graph nodes: {len(graph.nodes)}")
```

---

## Development Checklist

Use this checklist when developing a new agent:

### Phase 1: Planning
- [ ] Define agent purpose and scope
- [ ] Identify required capabilities (APIs, services)
- [ ] Choose appropriate category (data, analysis, financial, etc.)
- [ ] List capabilities the agent will provide
- [ ] Identify integration points with other agents

### Phase 2: Implementation
- [ ] Create agent file in `/dawsos/agents/`
- [ ] Inherit from `BaseAgent`
- [ ] Implement constructor with `graph`, `capabilities`, `llm_client`
- [ ] Implement `process(context)` method
- [ ] Return dict with 'response' key
- [ ] Use `store_result()` or `add_knowledge()` to store in graph
- [ ] Add error handling and logging
- [ ] Document methods with docstrings

### Phase 3: Registration
- [ ] Add agent to `AGENT_CAPABILITIES` in `agent_capabilities.py`
- [ ] Define capabilities list (can_*, provides_*, requires_*)
- [ ] Add to appropriate category in `CAPABILITY_CATEGORIES`
- [ ] Update `AGENT_INTEGRATION_MATRIX` if needed
- [ ] Register agent in runtime initialization (`main.py`)

### Phase 4: Testing
- [ ] Create unit tests in `/dawsos/tests/`
- [ ] Test basic functionality
- [ ] Test graph storage (verify nodes created)
- [ ] Test with required capabilities
- [ ] Test error handling
- [ ] Test runtime integration
- [ ] Verify compliance metrics (>90% compliance rate)
- [ ] Run full test suite: `pytest dawsos/tests/ -v`

### Phase 5: Integration
- [ ] Test agent with real data/capabilities
- [ ] Verify integration with other agents
- [ ] Check graph relationships are created correctly
- [ ] Monitor compliance metrics in production
- [ ] Document usage examples
- [ ] Add to system documentation

### Phase 6: Validation
- [ ] Run compliance checker
- [ ] Verify agent appears in governance reports
- [ ] Check execution metrics
- [ ] Validate graph storage
- [ ] Review error logs
- [ ] Get peer review

---

## Example: Complete Agent Template

Here's a complete template you can copy and customize:

```python
#!/usr/bin/env python3
"""
MyNewAgent - Brief description of what this agent does
"""

from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MyNewAgent(BaseAgent):
    """
    Detailed description of agent functionality.

    Capabilities:
        - can_do_something
        - can_do_something_else

    Integrates with:
        - data_harvester
        - graph_mind
    """

    def __init__(self, graph, capabilities: Dict = None, llm_client=None):
        """
        Initialize the agent.

        Args:
            graph: Shared knowledge graph instance
            capabilities: Dict of external capabilities (APIs, services)
            llm_client: Optional LLM client for AI-powered features
        """
        super().__init__(
            graph=graph,
            name="my_new_agent",
            llm_client=llm_client
        )
        self.capabilities = capabilities or {}
        self.capabilities_needed = ['required_capability_1']

        logger.info(f"{self.name} initialized with {len(self.capabilities)} capabilities")

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method called by AgentAdapter.

        Args:
            context: Execution context with user_input, capabilities, etc.

        Returns:
            Dict with 'response', 'data', and 'node_id' keys
        """
        try:
            user_input = context.get('user_input', '')
            logger.debug(f"Processing: {user_input}")

            # Validate capabilities
            if not self._validate_capabilities():
                return {
                    'response': f'Missing required capabilities: {self.capabilities_needed}',
                    'error': 'Missing capabilities'
                }

            # Your agent logic here
            result = self._perform_work(user_input, context)

            # Store result in knowledge graph (Trinity compliance)
            node_id = self.store_result(result, context)

            return {
                'response': f'Successfully processed: {user_input}',
                'data': result,
                'node_id': node_id
            }

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}", exc_info=True)
            return {
                'response': f'Error processing request: {str(e)}',
                'error': str(e)
            }

    def _perform_work(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core agent logic - implement your functionality here.

        Args:
            user_input: User's request
            context: Execution context

        Returns:
            Dict with results
        """
        # Example: Use external capability
        if 'required_capability_1' in self.capabilities:
            capability = self.capabilities['required_capability_1']
            data = capability.fetch_data(user_input)
        else:
            data = {}

        # Example: Query knowledge graph
        relevant_nodes = self._find_relevant_nodes(user_input)

        # Example: Perform analysis
        insights = self._analyze(data, relevant_nodes)

        return {
            'data': data,
            'relevant_nodes': relevant_nodes,
            'insights': insights,
            'timestamp': datetime.now().isoformat()
        }

    def _analyze(self, data: Dict, nodes: List[str]) -> List[str]:
        """
        Perform analysis on data and graph nodes.

        Args:
            data: External data
            nodes: List of relevant graph node IDs

        Returns:
            List of insights
        """
        insights = []

        # Your analysis logic here
        if data:
            insights.append(f"Analyzed {len(data)} data points")

        if nodes:
            insights.append(f"Found {len(nodes)} relevant graph nodes")

        return insights

    def _validate_capabilities(self) -> bool:
        """Check if required capabilities are available"""
        for capability in self.capabilities_needed:
            if capability not in self.capabilities:
                logger.warning(f"Missing required capability: {capability}")
                return False
        return True

    def __repr__(self) -> str:
        return f"MyNewAgent(capabilities={list(self.capabilities.keys())})"
```

---

## Conclusion

You now have everything you need to create powerful, Trinity-compliant agents for DawsOS. Remember:

1. **Inherit from BaseAgent**
2. **Implement process() method**
3. **Return dict with 'response' key**
4. **Store results in knowledge graph**
5. **Register capabilities in agent_capabilities.py**
6. **Write comprehensive tests**
7. **Monitor compliance metrics**

Happy agent development!

---

**Questions or Issues?**
- Check the troubleshooting section
- Review existing agents for examples
- Run compliance checker: `python -m dawsos.core.governance_agent`
- Check logs: `dawsos/logs/`

**Last Updated**: October 3, 2025
**Version**: 1.0
