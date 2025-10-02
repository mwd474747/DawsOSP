# DawsOS Improvement Plan

## Priority 1: Complete Pattern Engine Actions

### 1.1 Fix knowledge_lookup Action
**File**: `core/pattern_engine.py` (line 169-178)
**Current**: Returns mock data
**Solution**:
```python
def execute_action(self, action: str, params: Dict[str, Any], context: Dict[str, Any], outputs: Dict[str, Any]) -> Dict[str, Any]:
    if action == "knowledge_lookup":
        # Query actual knowledge graph
        knowledge_file = params.get('knowledge_file', '')
        section = params.get('section', '')

        # Access the knowledge graph through runtime
        if self.runtime and hasattr(self.runtime, 'agents'):
            # Get any agent that has access to the graph
            for agent_name, agent in self.runtime.agents.items():
                if hasattr(agent, 'graph'):
                    # Query the knowledge graph
                    nodes = agent.graph.get_nodes_by_type(section)
                    if nodes:
                        return {
                            'data': nodes,
                            'found': True
                        }

        return {'data': None, 'found': False}
```

### 1.2 Fix evaluate Action
**File**: `core/pattern_engine.py` (line 180-192)
**Current**: Random scores
**Solution**: Implement actual evaluation logic based on checks

### 1.3 Fix calculate Action
**File**: `core/pattern_engine.py` (line 194-204)
**Current**: Random values
**Solution**: Implement actual formula calculations

## Priority 2: Connect Data Sources

### 2.1 DataHarvester Real Implementation
**File**: `agents/data_harvester.py`
**Tasks**:
- Connect to actual market data APIs
- Implement FRED data fetching
- Add caching mechanism
- Handle API rate limits

### 2.2 Capability Integration
**Files**: `capabilities/market_data.py`, `capabilities/fred_data.py`
**Tasks**:
- Add API key management
- Implement data fetching methods
- Add error handling and retries
- Cache responses

## Priority 3: Knowledge Graph Integration

### 3.1 Pattern-Knowledge Bridge
**Tasks**:
- Create knowledge query methods
- Add graph traversal for relationships
- Implement entity extraction from patterns
- Add knowledge updates from patterns

### 3.2 Agent-Knowledge Integration
**Tasks**:
- Make agents query graph before responding
- Add knowledge storage from agent results
- Implement learning from interactions

## Priority 4: UI Enhancements

### 4.1 Dashboard Real Data
**File**: `main.py`
**Tasks**:
- Connect dashboard tabs to real data sources
- Update visualizations dynamically
- Add refresh mechanisms
- Implement data filtering

### 4.2 Workflow Integration
**Tasks**:
- Complete workflow recorder integration
- Add workflow replay functionality
- Create workflow management UI
- Add workflow sharing capability

## Priority 5: Error Handling & Logging

### 5.1 Comprehensive Error Handling
**Tasks**:
- Add try-catch blocks for all API calls
- Implement graceful degradation
- Add user-friendly error messages
- Create error recovery mechanisms

### 5.2 Logging System
**Tasks**:
- Add structured logging
- Create debug mode
- Add performance metrics
- Implement audit trail

## Implementation Order

### Phase 1: Core Fixes (Week 1)
1. Fix Pattern Engine actions (1.1, 1.2, 1.3)
2. Connect DataHarvester to real APIs (2.1)
3. Basic error handling (5.1)

### Phase 2: Integration (Week 2)
1. Knowledge Graph integration (3.1, 3.2)
2. Capability connections (2.2)
3. Logging system (5.2)

### Phase 3: UI Polish (Week 3)
1. Dashboard real data (4.1)
2. Workflow completion (4.2)
3. User experience improvements

## Quick Wins (Can be done immediately)

1. **Replace hardcoded template values** in `pattern_engine.py`:
   - Lines 415-435: Replace with dynamic lookups

2. **Add knowledge graph queries** in agents:
   - Update `think()` methods to check graph first

3. **Connect existing capabilities**:
   - Wire up MarketDataCapability methods
   - Add FredDataCapability usage

4. **Fix pattern matching**:
   - Add more trigger phrases
   - Improve entity extraction
   - Handle variations better

## Testing Requirements

- Unit tests for each action type
- Integration tests for pattern execution
- API mock tests for external services
- UI automation tests for workflows
- Performance benchmarks

## Success Metrics

- 0 mock data responses in production
- <2s response time for patterns
- 95% pattern match accuracy
- 100% test coverage for core functions
- Real-time data updates in UI