# DawsOS UI Module Documentation

## Overview

The DawsOS UI module provides a comprehensive Streamlit-based interface for interacting with the Trinity Architecture. All UI components follow consistent patterns and leverage the Pattern-Knowledge-Agent system.

## Module Structure

```
dawsos/ui/
├── utils/                          # Shared UI utilities
│   ├── __init__.py
│   └── common.py                   # Common UI helpers (13 functions)
├── alert_panel.py                  # Alert management UI (748 lines, 1 class)
├── api_health_tab.py               # API health monitoring (436 lines, 12 functions)
├── data_integrity_tab.py           # Data integrity dashboard (498 lines, 6 functions)
├── governance_tab.py               # Governance dashboard (1,179 lines, 15 functions)
├── intelligence_display.py         # Intelligence display components (817 lines, 5 classes)
├── intelligence_display_examples.py # Usage examples (451 lines, 11 functions)
├── pattern_browser.py              # Pattern browser (593 lines, 1 class)
├── trinity_dashboard_tabs.py       # Trinity dashboard tabs (1,145 lines, 1 class)
├── trinity_ui_components.py        # Trinity UI components (650 lines, 1 class)
└── workflows_tab.py                # Workflow management (243 lines, 1 function)
```

**Total**: 10 files, 6,760 lines, 144 functions, 9 classes

## Architecture Principles

### 1. Trinity Architecture Compliance

All UI components interact with the system through the Trinity flow:
```
UI → UniversalExecutor → PatternEngine → AgentRuntime → KnowledgeGraph
```

**Never bypass the registry** - Always use `runtime.exec_via_registry()` or `runtime.execute_by_capability()`

### 2. Helper Function Pattern

Large UI files are organized using helper functions with clear naming:
- `_render_*()` - UI rendering functions
- `_get_*()` - Data retrieval functions
- `_execute_*()` - Action execution functions
- `_format_*()` - Data formatting functions

Example from `governance_tab.py`:
```python
def render_governance_tab(runtime, graph):
    """Main entry point - delegates to helpers"""
    _render_header_and_dashboard(graph, graph_metrics, st)
    _render_system_telemetry(runtime, st)
    _render_persistence_health(st)
    # ... more sections
```

### 3. Shared Utilities

Common UI patterns are extracted to `ui/utils/common.py`:
- `render_confidence_display()` - Confidence score display
- `render_metric_card()` - Standardized metrics
- `render_status_badge()` - Status indicators
- `render_error_message()` - Error handling
- `format_timestamp()` - Timestamp formatting
- And 8 more utilities...

Usage:
```python
from ui.utils import render_confidence_display, render_metric_card

render_confidence_display(0.85, "Pattern Match")
render_metric_card("Graph Nodes", 1234, delta="+42")
```

## Component Descriptions

### Core Dashboard Components

#### 1. Trinity Dashboard Tabs (`trinity_dashboard_tabs.py`)
**Purpose**: Main intelligence dashboard with pattern-driven interfaces

**Features**:
- Pattern-enhanced chat interface
- Interactive knowledge graph visualization with sampling (handles 500+ nodes)
- Real-time system health metrics
- Agent performance tracking
- Pattern execution statistics
- Trinity compliance monitoring

**Key Methods**:
- `render_trinity_chat_interface()` - Chat with pattern suggestions
- `render_trinity_knowledge_graph()` - Interactive graph with sampling strategies
- `render_trinity_dashboard()` - System health and metrics
- `render_trinity_markets()` - Market data patterns
- `render_trinity_economy()` - Economic indicators

**Usage**:
```python
trinity_tabs = get_trinity_dashboard_tabs(pattern_engine, runtime, graph)
trinity_tabs.render_trinity_dashboard()
```

#### 2. Governance Tab (`governance_tab.py`)
**Purpose**: Conversational data governance system

**Features**:
- Real-time governance metrics from knowledge graph
- System telemetry (executions, success rates, agent usage)
- Persistence health monitoring with backup verification
- Conversational governance interface
- Live monitoring sidebar with alerts
- Graph quality analysis, data lineage tracing
- Policy management and agent compliance checking

**Sections** (15 helper functions):
- Header and dashboard metrics
- System telemetry
- Persistence and backup health
- Conversational interface
- Live monitoring sidebar
- Quality analysis
- Data lineage explorer
- Policy management
- Agent compliance dashboard
- System oversight

**Usage**:
```python
from ui.governance_tab import render_governance_tab
render_governance_tab(runtime, graph)
```

#### 3. API Health Tab (`api_health_tab.py`)
**Purpose**: API health and fallback monitoring

**Features** (12 helper functions):
- Fallback event statistics (LLM, API, cache)
- Recent event tracking with explanations
- API configuration status for all keys
- FRED API cache metrics
- Polygon API cache metrics
- FMP API health status
- Data freshness guidelines
- Setup instructions

**Usage**:
```python
from ui.api_health_tab import render_api_health_tab
render_api_health_tab()
```

### Specialized Components

#### 4. Pattern Browser (`pattern_browser.py`)
**Purpose**: Browse, search, and execute all patterns

**Features**:
- Search and filter patterns by name, description, triggers
- Category browsing (queries, analysis, workflows)
- Priority filtering
- Detailed pattern information and step viewing
- Parameter input forms for pattern execution
- Execution results with confidence scores
- Execution history tracking

**Class**: `PatternBrowser`
- `render_pattern_browser()` - Main browser interface
- `render_pattern_execution_form()` - Pattern execution with parameters
- `_execute_pattern()` - Pattern execution handler

**Usage**:
```python
from ui.pattern_browser import render_pattern_browser
render_pattern_browser(runtime)
```

#### 5. Alert Panel (`alert_panel.py`)
**Purpose**: Alert management and monitoring

**Features**:
- Alert analytics dashboard with visualizations
- Create custom alerts from templates
- Manage active alerts with filters
- View alert history
- Acknowledge events
- Real-time notifications in sidebar

**Class**: `AlertPanel`
- Methods: 24 functions including template builders
- Template categories: Stock/Market, System Health, Data Quality, Compliance

**Usage**:
```python
from ui.alert_panel import AlertPanel
alert_panel = AlertPanel(alert_manager, runtime)
alert_panel.render_alert_panel()
```

#### 6. Intelligence Display (`intelligence_display.py`)
**Purpose**: Rich intelligence display components

**Features**:
- Confidence display with visual indicators
- Thinking trace visualization
- Pattern match highlighting
- Multi-agent response formatting
- Evidence and reasoning display

**Classes** (5):
- `IntelligenceDisplay` - Main display orchestrator
- Plus 4 specialized display classes

**Usage**:
```python
from ui.intelligence_display import create_intelligence_display
display = create_intelligence_display()
display.show_analysis_result(result)
```

#### 7. Data Integrity Tab (`data_integrity_tab.py`)
**Purpose**: Real-time data monitoring and management

**Features**:
- Data freshness monitoring
- Integrity checks
- Dataset health metrics
- Data quality scores

**Functions**: 6 helper functions

#### 8. Trinity UI Components (`trinity_ui_components.py`)
**Purpose**: Trinity-powered UI system

**Features**:
- Pattern-driven UI generation
- Knowledge-based content
- Agent-orchestrated components
- Real-time intelligence dashboard

**Class**: `TrinityUI`
- Core dashboard rendering
- API health status
- Pattern-driven components

#### 9. Workflows Tab (`workflows_tab.py`)
**Purpose**: Investment workflow management

**Features**:
- Workflow execution
- History tracking
- Status monitoring

**Functions**: 1 main render function

## Best Practices

### 1. Creating New UI Components

```python
#!/usr/bin/env python3
"""
Module Name - Brief Description
"""

import streamlit as st
from typing import Any, Dict, Optional

def _render_section_header() -> None:
    """Render section header (private helper)."""
    st.markdown("### Section Title")

def _render_main_content(data: Dict[str, Any]) -> None:
    """Render main content (private helper)."""
    # Implementation
    pass

def render_my_tab(runtime: Any, graph: Any) -> None:
    """
    Main entry point for My Tab.

    Delegates to helper functions for organization.

    Args:
        runtime: Agent runtime instance
        graph: Knowledge graph instance
    """
    _render_section_header()
    _render_main_content(data)
```

### 2. Using Shared Utilities

```python
from ui.utils import (
    render_metric_card,
    render_confidence_display,
    format_timestamp
)

# Use shared utilities instead of reimplementing
render_metric_card("Active Agents", 15, delta="+2")
render_confidence_display(0.92, "Pattern Match")
formatted = format_timestamp("2025-10-09T10:30:00", "%H:%M:%S")
```

### 3. Error Handling

```python
from ui.utils import render_error_message, render_success_message

try:
    result = runtime.execute_pattern(pattern_id)
    render_success_message("Pattern executed successfully",
                          f"Matched {result['matches']} items")
except Exception as e:
    render_error_message(e, "Pattern Execution")
```

### 4. Consistent Metrics Display

```python
# Use columns for metric rows
col1, col2, col3 = st.columns(3)

with col1:
    render_metric_card("Total Nodes", total_nodes,
                      delta=f"{edges} edges")

with col2:
    render_metric_card("Success Rate", f"{success_rate:.1%}",
                      delta="Good" if success_rate > 0.9 else "Needs attention")
```

### 5. Trinity Compliance

```python
# ✅ CORRECT - Use registry
result = runtime.exec_via_registry('claude', context)

# ✅ CORRECT - Use capability-based routing
result = runtime.execute_by_capability('can_analyze_text', context)

# ❌ WRONG - Direct agent call (bypasses registry)
agent = runtime.agents['claude']
result = agent.think(context)
```

## File Organization Guidelines

### When to Create a New UI File

Create a new file when:
1. The functionality represents a distinct tab or major feature
2. The component will exceed 200 lines
3. The component will be reused in multiple places
4. The component has its own class or complex state

### When to Use Helper Functions

Use helper functions when:
1. A rendering function exceeds 50 lines
2. Logic can be clearly separated by responsibility
3. Code will be called from multiple places within the same file
4. Testing individual components would be beneficial

### When to Use Utils

Add to `ui/utils/common.py` when:
1. The utility is used in 2+ different UI files
2. The utility is a general-purpose UI pattern
3. The utility has no file-specific dependencies
4. The utility is less than 30 lines

## Performance Considerations

### Large Graph Visualization

The Trinity dashboard includes intelligent graph sampling for performance:

```python
# Sampling strategies for graphs > 500 nodes
trinity_tabs.render_trinity_knowledge_graph()
# Uses: importance, recent, connected, or random sampling
```

### Caching Session State

```python
# Cache expensive computations in session state
if 'expensive_calculation' not in st.session_state:
    st.session_state.expensive_calculation = compute_expensive_thing()

result = st.session_state.expensive_calculation
```

### Progressive Loading

```python
# Load data progressively for better UX
with st.spinner("Loading data..."):
    data = load_large_dataset()

with st.expander("View Full Details"):
    st.dataframe(data)  # Only rendered when expanded
```

## Testing UI Components

### Manual Testing Checklist

- [ ] Component renders without errors
- [ ] All buttons and inputs work correctly
- [ ] Error states display helpful messages
- [ ] Loading states show spinners
- [ ] Success states show confirmations
- [ ] Trinity compliance maintained (no registry bypasses)
- [ ] Session state updates correctly
- [ ] Navigation works as expected

### Validation Commands

```bash
# Verify imports
python -c "from ui.utils import render_confidence_display; print('✓ Utils OK')"

# Check for syntax errors
python -m py_compile dawsos/ui/*.py

# Run Streamlit to test UI
streamlit run dawsos/main.py
```

## Troubleshooting

### Common Issues

**Import errors**:
```python
# ❌ Wrong
from dawsos.ui.utils import render_metric_card

# ✅ Correct (from within dawsos/)
from ui.utils import render_metric_card
```

**Session state not persisting**:
```python
# Initialize in init_session_state()
if 'my_state' not in st.session_state:
    st.session_state.my_state = initial_value
```

**UI not updating**:
```python
# Force rerun after state changes
st.session_state.my_value = new_value
st.rerun()
```

## Migration Guide

### Moving from Monolithic to Helper Functions

Before:
```python
def render_my_tab():
    # 500 lines of mixed logic
    st.markdown("### Header")
    # ... 100 lines ...
    # ... 100 lines ...
    # ... 100 lines ...
```

After:
```python
def _render_header():
    """Render header section."""
    st.markdown("### Header")

def _render_section_a():
    """Render section A."""
    # Clear, focused logic

def _render_section_b():
    """Render section B."""
    # Clear, focused logic

def render_my_tab():
    """Main entry point - orchestrates sections."""
    _render_header()
    _render_section_a()
    _render_section_b()
```

## Summary

The DawsOS UI module is **well-organized** and **maintainable**:

✅ **Clear structure**: 10 files with focused responsibilities
✅ **Helper functions**: 144 functions organized for clarity
✅ **Shared utilities**: 13 common utilities to reduce duplication
✅ **Consistent patterns**: Error handling, metrics, formatting
✅ **Trinity compliant**: All components use proper execution flow
✅ **Documented**: Clear docstrings and type hints
✅ **Scalable**: Ready for future growth

**Current Status**: Production-ready, well-refactored, minimal duplication.
