# Intelligence Display Component

## Overview

The `intelligence_display.py` component provides comprehensive visualization of agent intelligence, decision-making, and execution flows within the DawsOS Trinity architecture.

## Features

### A. Confidence Score Display
- Visual gauges with color coding (Green >80%, Yellow 50-80%, Red <50%)
- Multiple confidence metrics side-by-side
- Historical confidence trends
- Progressive disclosure from summary to details

### B. Thinking Trace Visualizer
- Step-by-step agent execution timeline
- Expandable details for each step
- Execution time per step
- Success/failure indicators
- Timeline/Gantt chart view

### C. Agent Flow Diagram
- Visual representation of Trinity execution path
- Mermaid flowcharts showing: UniversalExecutor → PatternEngine → AgentRegistry → Agents → KnowledgeGraph
- Highlights parallel vs sequential execution
- Agent capability cards

### D. Decision Provenance
- Reasoning steps behind each decision
- Contributing factors and data sources
- Knowledge graph connections
- Transparency into "why" the system made recommendations

### E. System Health Intelligence
- Overall Trinity compliance metrics
- Per-agent performance tracking
- Knowledge graph statistics
- Node type distributions

## Quick Start

```python
from ui.intelligence_display import create_intelligence_display

# Create display with Trinity components
display = create_intelligence_display(
    graph=runtime.graph,
    registry=runtime.agent_registry,
    runtime=runtime
)

# After pattern execution
result = pattern_engine.execute_pattern(pattern, context)
display.render_intelligence_summary(result)
```

## Usage Examples

### 1. Standalone Confidence Display
```python
from ui.intelligence_display import quick_confidence_display

quick_confidence_display(85.5, "Prediction Confidence")
```

### 2. Show Execution Trace
```python
from ui.intelligence_display import quick_thinking_trace

execution_history = [
    {
        'agent': 'DataHarvester',
        'action': 'fetch_data',
        'duration_ms': 350,
        'result': {'data_points': 100}
    }
]

quick_thinking_trace(execution_history)
```

### 3. Full Intelligence Summary
```python
display = create_intelligence_display(graph, registry, runtime)
display.render_intelligence_summary(execution_result, show_all_sections=False)
```

### 4. System Health Dashboard
```python
display = create_intelligence_display(graph, registry, runtime)
display.render_system_intelligence()
```

## Integration Points

### Pattern Browser Integration
```python
# After executing a pattern
result = pattern_engine.execute_pattern(pattern, context)
display.render_intelligence_summary(result)
```

### Dashboard Tab Integration
```python
def create_intelligence_tab(runtime):
    display = create_intelligence_display(
        graph=runtime.graph,
        registry=runtime.agent_registry,
        runtime=runtime
    )
    display.render_system_intelligence()
```

### Agent Result Analysis
```python
# After agent execution
result = runtime.agent_registry.execute_with_tracking(agent_name, context)
display.render_intelligence_summary(result)
```

## Component Functions

### Confidence Display
- `render_confidence_gauge(confidence, label, show_history)` - Single gauge with optional trend
- `render_multi_confidence(scores)` - Multiple scores side-by-side
- `_render_mini_gauge(confidence, label)` - Compact gauge display

### Thinking Trace
- `render_thinking_trace(execution_history, expand_by_default)` - Step-by-step execution
- `render_execution_timeline(execution_history)` - Timeline/Gantt chart view
- `_render_execution_step(idx, step, expand)` - Individual step display

### Agent Flow
- `render_agent_flow_diagram(agents_used, execution_path)` - Flowchart visualization
- `render_trinity_architecture_flow()` - Complete Trinity architecture diagram
- `_render_mermaid_flow(execution_path)` - Mermaid diagram generator

### Decision Provenance
- `render_decision_provenance(decision_node, show_data_sources)` - Full provenance display
- `_render_data_sources(decision_node)` - Data source listing
- `_render_graph_connections(node_id)` - Knowledge graph connections

### System Health
- `render_system_intelligence()` - Overall system metrics and health
- Agent performance tracking
- Knowledge graph statistics

### Main Display
- `render_intelligence_summary(result, show_all_sections)` - Complete intelligence analysis

## Data Structures

### Execution Result Format
```python
{
    'confidence': 0.85,  # or 85 for percentage
    'confidence_breakdown': {
        'Overall': 85,
        'Data Quality': 92,
        'Analysis': 88
    },
    'execution_history': [
        {
            'agent': 'AgentName',
            'action': 'method_name',
            'duration_ms': 350,
            'timestamp': '2025-10-03T10:30:00',
            'result': {}
        }
    ],
    'agents_used': ['Agent1', 'Agent2'],
    'reasoning': ['Step 1', 'Step 2'],
    'factors': {'factor1': 0.85},
    'node_id': 'decision_123'
}
```

### Execution Step Format
```python
{
    'agent': 'AgentName',
    'action': 'method_name',
    'method_used': 'execute',  # Alternative to action
    'duration_ms': 350,
    'timestamp': '2025-10-03T10:30:00.000',
    'result': {
        'response': 'Result data',
        # or 'error': 'Error message'
    }
}
```

## Dependencies

- `streamlit` - UI framework
- `plotly` - Interactive charts and gauges
- `json` - Data handling
- `datetime` - Timestamps

## File Structure

- `/Users/mdawson/Dawson/DawsOSB/dawsos/ui/intelligence_display.py` - Main component (816 lines)
- `/Users/mdawson/Dawson/DawsOSB/dawsos/ui/intelligence_display_examples.py` - Integration examples (457 lines)

## Best Practices

1. **Progressive Disclosure**: Use expanders to hide complex details by default
2. **Color Coding**: Green (>80%), Yellow (50-80%), Red (<50%) for confidence
3. **Context Awareness**: Provide graph, registry, and runtime when available
4. **Error Handling**: Component gracefully handles missing data
5. **Performance**: Limit historical displays to last 20 executions

## Example Usage Code

See `intelligence_display_examples.py` for 10 complete integration examples:
1. Pattern Execution Intelligence
2. Standalone Confidence Display
3. Agent Result Intelligence
4. System Health Dashboard
5. Decision Provenance Deep Dive
6. Execution Trace for Debugging
7. Agent Flow Visualization
8. Confidence with Historical Trend
9. Pattern Browser Integration
10. Custom Intelligence Tab

## Demo

Run the examples demo:
```bash
streamlit run dawsos/ui/intelligence_display_examples.py
```

## Architecture Alignment

This component fully aligns with the Trinity architecture:
- **UniversalExecutor**: Entry point tracking
- **PatternEngine**: Pattern execution visualization
- **AgentRegistry**: Agent performance and compliance
- **Agents**: Individual execution traces
- **KnowledgeGraph**: Decision nodes and connections

All execution flows through the proper Trinity path and are visualized accordingly.
