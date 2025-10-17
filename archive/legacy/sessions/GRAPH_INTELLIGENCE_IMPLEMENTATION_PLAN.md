# Knowledge Graph Intelligence - Detailed Implementation Plan

**Version**: 1.0  
**Date**: October 16, 2025  
**Status**: 📋 Ready for Implementation  
**Estimated Total Time**: 28-32 hours (3-4 weeks at 8-10 hours/week)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Design](#architecture-design)
3. [Phase 1: Foundation & Quick Wins](#phase-1-foundation--quick-wins-8-10-hours)
4. [Phase 2: Visual Intelligence](#phase-2-visual-intelligence-8-10-hours)
5. [Phase 3: Advanced Features](#phase-3-advanced-features-10-12-hours)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Plan](#deployment-plan)
8. [Acceptance Criteria](#acceptance-criteria)

---

## Project Overview

### Objective
Transform the hidden Knowledge Graph into a user-facing intelligence platform that exposes:
- Connection tracing (causal chains)
- Impact forecasting (predictive analytics)
- Historical analysis tracking
- Visual graph exploration
- Pattern discovery

### Success Metrics
- **User Engagement**: +50% session time
- **Feature Discovery**: +200% (users find 10+ capabilities)
- **Return Visits**: +80% (historical context drives engagement)
- **User Satisfaction**: Graph reasoning increases trust in recommendations

### Technical Constraints
- ✅ **Zero backend changes** - All graph capabilities exist
- ✅ **Backward compatible** - No breaking changes to existing features
- ✅ **Performance first** - LRU caching, pagination, sampling
- ✅ **Mobile responsive** - Works on tablets/phones

---

## Architecture Design

### File Structure

```
dawsos/
├── ui/
│   ├── trinity_dashboard_tabs.py          # MODIFY: Add new render methods
│   ├── graph_intelligence/                # NEW MODULE
│   │   ├── __init__.py
│   │   ├── connection_tracer.py           # Feature 1: Connection Tracer
│   │   ├── impact_forecaster.py           # Feature 2: Impact Forecaster
│   │   ├── analysis_history.py            # Feature 3: Analysis History
│   │   ├── graph_visualizer.py            # Feature 4: Interactive Viz
│   │   ├── sector_correlations.py         # Feature 5: Correlation Heatmap
│   │   ├── pattern_discovery.py           # Feature 6: Pattern Discovery
│   │   ├── query_builder.py               # Feature 7: Query Builder
│   │   ├── comparative_analysis.py        # Feature 8: Comparative Analysis
│   │   ├── live_stats.py                  # Feature 9: Live Stats
│   │   └── related_suggestions.py         # Feature 10: Related Suggestions
│   └── utils/
│       └── graph_utils.py                 # NEW: Shared graph utilities
├── core/
│   └── knowledge_graph.py                 # NO CHANGES (already has all methods)
└── tests/
    └── ui/
        └── test_graph_intelligence.py     # NEW: UI component tests
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Streamlit UI Layer                         │
│  ┌────────────────────────────────────────────────┐   │
│  │   trinity_dashboard_tabs.py                     │   │
│  │   - render_trinity_knowledge_graph()            │   │
│  │   - _render_graph_intelligence_subtabs()  NEW   │   │
│  └────────────────────────────────────────────────┘   │
│                       ↓                                 │
│  ┌────────────────────────────────────────────────┐   │
│  │   graph_intelligence/ (10 modules)              │   │
│  │   Each exposes: render(graph, runtime) → None   │   │
│  └────────────────────────────────────────────────┘   │
│                       ↓                                 │
│  ┌────────────────────────────────────────────────┐   │
│  │   graph_utils.py (shared helpers)               │   │
│  │   - safe_query(pattern, max=100)                │   │
│  │   - format_node_display(node)                   │   │
│  │   - create_plotly_graph(nodes, edges)           │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│           KnowledgeGraph (No Changes)                   │
│  - trace_connections(node, depth, min_strength)         │
│  - forecast_impact(target, horizon)                     │
│  - query(pattern) → List[NodeID]                        │
│  - get_stats() → Dict[str, Any]                         │
│  - get_node(node_id) → Optional[NodeData]               │
│  - get_all_edges() → List[EdgeData]                     │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Action (UI)
    ↓
graph_intelligence module
    ↓
graph_utils.safe_query()  [validates, limits results]
    ↓
KnowledgeGraph API  [existing methods]
    ↓
NetworkX backend  [96K+ nodes, LRU cached]
    ↓
graph_intelligence module  [formats for display]
    ↓
Streamlit renders  [plotly charts, dataframes, metrics]
```

---

## Phase 1: Foundation & Quick Wins (8-10 hours)

### Sprint 1.1: Infrastructure Setup (2 hours)

#### Task 1.1.1: Create Module Structure
**File**: `dawsos/ui/graph_intelligence/__init__.py`
**Time**: 15 minutes

```python
"""
Graph Intelligence Module
Exposes Knowledge Graph capabilities to users
"""

from .connection_tracer import render_connection_tracer
from .impact_forecaster import render_impact_forecaster
from .analysis_history import render_analysis_history
from .live_stats import render_live_stats
from .related_suggestions import render_related_suggestions

__all__ = [
    'render_connection_tracer',
    'render_impact_forecaster',
    'render_analysis_history',
    'render_live_stats',
    'render_related_suggestions',
]
```

**Acceptance Criteria**:
- ✅ Module imports without errors
- ✅ All 5 Phase 1 modules listed

#### Task 1.1.2: Create Shared Utilities
**File**: `dawsos/ui/utils/graph_utils.py`
**Time**: 45 minutes

```python
"""Shared utilities for graph intelligence features"""

import streamlit as st
from typing import Dict, List, Any, Optional
import pandas as pd

def safe_query(graph, pattern: Dict[str, Any], max_results: int = 100) -> List[str]:
    """
    Query graph with result limiting for UI safety
    
    Args:
        graph: KnowledgeGraph instance
        pattern: Query pattern dict
        max_results: Maximum results to return
        
    Returns:
        List of node IDs (limited to max_results)
    """
    try:
        results = graph.query(pattern)
        if len(results) > max_results:
            st.warning(f"⚠️ Found {len(results)} results, showing first {max_results}")
            return results[:max_results]
        return results
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        return []

def format_node_display(node: Dict[str, Any]) -> str:
    """Format node for user-friendly display"""
    node_type = node.get('type', 'unknown')
    node_id = node.get('id', 'N/A')
    created = node.get('created', 'Unknown')
    
    # Extract key data fields
    data = node.get('data', {})
    if 'symbol' in data:
        return f"📊 {data['symbol']} ({node_type})"
    elif 'name' in data:
        return f"🏷️ {data['name']} ({node_type})"
    else:
        return f"🔹 {node_id} ({node_type})"

def format_path_display(path: List[Dict[str, Any]]) -> str:
    """Format connection path for readable display"""
    if not path:
        return "No path"
    
    parts = []
    for step in path:
        from_node = step.get('from', '?')
        to_node = step.get('to', '?')
        rel_type = step.get('type', 'connected')
        strength = step.get('strength', 0)
        
        # Clean up node IDs (remove prefix)
        from_clean = from_node.replace('company_', '').replace('sector_', '').replace('economic_', '')
        to_clean = to_node.replace('company_', '').replace('sector_', '').replace('economic_', '')
        
        parts.append(f"{from_clean} --[{rel_type} {strength:.2f}]--> {to_clean}")
    
    return "\n".join(parts)

@st.cache_data(ttl=300)
def get_cached_graph_stats(_graph) -> Dict[str, Any]:
    """Get graph stats with 5-minute caching"""
    return _graph.get_stats()

def create_metric_card(label: str, value: Any, delta: Optional[str] = None):
    """Consistent metric card styling"""
    col = st.columns(1)[0]
    col.metric(label, value, delta)
```

**Acceptance Criteria**:
- ✅ All functions have type hints
- ✅ Error handling in safe_query
- ✅ Streamlit caching for performance
- ✅ Unit tests pass (5 functions × 2 test cases = 10 tests)

#### Task 1.1.3: Update Main Dashboard
**File**: `dawsos/ui/trinity_dashboard_tabs.py`
**Time**: 1 hour

**Changes**:
1. Add import: `from ui.graph_intelligence import *`
2. Modify `render_trinity_knowledge_graph()` to add sub-tabs
3. Add new method `_render_graph_intelligence_subtabs()`

```python
def render_trinity_knowledge_graph(self) -> None:
    """Enhanced knowledge graph with intelligence sub-tabs"""
    st.markdown("### 🧠 Trinity Knowledge Graph - Pattern-Enhanced Intelligence")
    
    # Sub-tabs for graph intelligence features
    tab_names = [
        "📊 Overview",
        "🔗 Connection Tracer", 
        "📈 Impact Forecast",
        "📜 Analysis History",
        "💡 Suggestions"
    ]
    
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        self._render_graph_overview()  # Existing functionality
    
    with tabs[1]:
        from ui.graph_intelligence import render_connection_tracer
        render_connection_tracer(self.graph, self.runtime)
    
    with tabs[2]:
        from ui.graph_intelligence import render_impact_forecaster
        render_impact_forecaster(self.graph, self.runtime)
    
    with tabs[3]:
        from ui.graph_intelligence import render_analysis_history
        render_analysis_history(self.graph, self.runtime)
    
    with tabs[4]:
        from ui.graph_intelligence import render_related_suggestions
        render_related_suggestions(self.graph, self.runtime)

def _render_graph_overview(self) -> None:
    """Original graph overview (existing code moved here)"""
    # ... existing visualization code ...
    pass
```

**Acceptance Criteria**:
- ✅ Sub-tabs render without errors
- ✅ Each tab shows placeholder message if feature not complete
- ✅ No regression in existing graph visualization
- ✅ Mobile responsive (tabs work on small screens)

---

### Sprint 1.2: Live Stats Dashboard (1 hour)

#### Task 1.2.1: Implement Live Stats
**File**: `dawsos/ui/graph_intelligence/live_stats.py`
**Time**: 1 hour

```python
"""Live Graph Statistics Dashboard"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Any

def render_live_stats(graph: Any, runtime: Any) -> None:
    """
    Display real-time graph statistics and health metrics
    
    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 📊 Live Graph Statistics")
    
    # Get stats (cached)
    from ui.utils.graph_utils import get_cached_graph_stats
    stats = get_cached_graph_stats(graph)
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Nodes",
            f"{stats['total_nodes']:,}",
            help="All knowledge nodes in the graph"
        )
    
    with col2:
        st.metric(
            "Connections",
            f"{stats['total_edges']:,}",
            help="Relationships between nodes"
        )
    
    with col3:
        st.metric(
            "Patterns",
            stats.get('total_patterns', 0),
            help="Automatically discovered patterns"
        )
    
    with col4:
        avg_conn = stats.get('avg_connections', 0)
        st.metric(
            "Avg Connections",
            f"{avg_conn:.1f}",
            help="Average connections per node"
        )
    
    # Node types breakdown
    st.markdown("### 📦 Node Types Distribution")
    node_types = stats.get('node_types', {})
    if node_types:
        df = pd.DataFrame(list(node_types.items()), columns=['Type', 'Count'])
        df = df.sort_values('Count', ascending=False)
        
        fig = px.bar(
            df,
            x='Type',
            y='Count',
            title="Node Types",
            color='Count',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No nodes yet. Start analyzing to build the graph!")
    
    # Edge types breakdown
    st.markdown("### 🔗 Relationship Types")
    edge_types = stats.get('edge_types', {})
    if edge_types:
        df = pd.DataFrame(list(edge_types.items()), columns=['Relationship', 'Count'])
        df = df.sort_values('Count', ascending=False)
        
        fig = px.pie(
            df,
            names='Relationship',
            values='Count',
            title="Relationship Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Cache performance (if available)
    if hasattr(graph, '_cache_stats'):
        st.markdown("### ⚡ Cache Performance")
        cache_stats = graph._cache_stats
        
        col1, col2 = st.columns(2)
        
        with col1:
            total_trace = cache_stats['trace_hits'] + cache_stats['trace_misses']
            hit_rate = cache_stats['trace_hits'] / total_trace if total_trace > 0 else 0
            st.metric(
                "Trace Cache Hit Rate",
                f"{hit_rate:.1%}",
                help="Higher is better (less recomputation)"
            )
        
        with col2:
            total_forecast = cache_stats['forecast_hits'] + cache_stats['forecast_misses']
            hit_rate = cache_stats['forecast_hits'] / total_forecast if total_forecast > 0 else 0
            st.metric(
                "Forecast Cache Hit Rate",
                f"{hit_rate:.1%}",
                help="Higher is better (less recomputation)"
            )
    
    # Graph health assessment
    st.markdown("### 🏥 Graph Health")
    
    total_nodes = stats['total_nodes']
    total_edges = stats['total_edges']
    avg_conn = stats.get('avg_connections', 0)
    
    health_score = 0
    health_messages = []
    
    # Check node count
    if total_nodes > 1000:
        health_score += 30
        health_messages.append("✅ Rich knowledge base (1000+ nodes)")
    elif total_nodes > 100:
        health_score += 20
        health_messages.append("✅ Growing knowledge base (100+ nodes)")
    else:
        health_messages.append("⚠️ Small knowledge base (run more analyses)")
    
    # Check connectivity
    if avg_conn > 3:
        health_score += 40
        health_messages.append("✅ Highly connected (good for forecasting)")
    elif avg_conn > 1.5:
        health_score += 25
        health_messages.append("✅ Moderately connected")
    else:
        health_messages.append("⚠️ Low connectivity (limited forecasting)")
    
    # Check patterns
    if stats.get('total_patterns', 0) > 10:
        health_score += 30
        health_messages.append("✅ Pattern-rich (system learning)")
    elif stats.get('total_patterns', 0) > 0:
        health_score += 15
        health_messages.append("✅ Some patterns discovered")
    else:
        health_messages.append("ℹ️ No patterns yet (needs more data)")
    
    # Display health score
    health_color = "green" if health_score >= 70 else "orange" if health_score >= 40 else "red"
    st.markdown(f"**Overall Health Score:** :{health_color}[{health_score}/100]")
    
    for msg in health_messages:
        st.write(msg)
    
    # Refresh button
    if st.button("🔄 Refresh Stats"):
        st.cache_data.clear()
        st.rerun()
```

**Acceptance Criteria**:
- ✅ All metrics display correctly
- ✅ Charts render (bar chart for node types, pie chart for relationships)
- ✅ Health assessment shows actionable messages
- ✅ Refresh button clears cache and updates
- ✅ Handles empty graph gracefully

**Testing Checklist**:
- [ ] Empty graph (0 nodes) shows informative message
- [ ] Small graph (10 nodes) shows basic stats
- [ ] Large graph (1000+ nodes) shows all features
- [ ] Cache stats display when available
- [ ] Refresh updates data

---

### Sprint 1.3: Connection Tracer (3 hours)

#### Task 1.3.1: Implement Connection Tracer
**File**: `dawsos/ui/graph_intelligence/connection_tracer.py`
**Time**: 3 hours

```python
"""Connection Tracer - Trace causal chains through the graph"""

import streamlit as st
from typing import Any, List, Dict
from ui.utils.graph_utils import format_path_display

def render_connection_tracer(graph: Any, runtime: Any) -> None:
    """
    Interactive connection tracer to show how nodes connect
    
    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 🔗 Connection Tracer")
    st.markdown("Discover how economic factors, sectors, and companies connect")
    
    # Input controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Get available nodes for dropdown
        node_options = _get_node_options(graph)
        
        start_node = st.selectbox(
            "Start Node",
            options=node_options,
            index=0 if node_options else None,
            help="Select a node to trace connections from"
        )
        
        # Allow custom node ID input
        custom_node = st.text_input(
            "Or enter custom node ID",
            placeholder="e.g., company_AAPL, sector_Technology",
            help="Advanced: Enter any node ID directly"
        )
        
        if custom_node:
            start_node = custom_node
    
    with col2:
        max_depth = st.slider(
            "Max Depth",
            min_value=1,
            max_value=5,
            value=3,
            help="How many hops to trace"
        )
    
    with col3:
        min_strength = st.slider(
            "Min Strength",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Filter weak connections"
        )
    
    # Trace button
    if st.button("🔍 Trace Connections", type="primary"):
        if not start_node:
            st.error("Please select or enter a start node")
            return
        
        with st.spinner(f"Tracing connections from {start_node}..."):
            paths = _trace_connections_safe(graph, start_node, max_depth, min_strength)
        
        if not paths:
            st.warning(f"No connections found from {start_node} (depth={max_depth}, strength>={min_strength})")
            st.info("💡 Try increasing max depth or lowering min strength")
            return
        
        # Display results
        st.success(f"✅ Found {len(paths)} connection paths")
        
        # Path statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Paths", len(paths))
        with col2:
            avg_strength = sum(p[-1].get('strength', 0) for p in paths) / len(paths)
            st.metric("Avg Strength", f"{avg_strength:.2f}")
        with col3:
            max_path_len = max(len(p) for p in paths)
            st.metric("Longest Path", f"{max_path_len} hops")
        
        # Group paths by target node
        paths_by_target = _group_paths_by_target(paths)
        
        # Display paths
        st.markdown("### 📍 Connection Paths")
        
        # Filter controls
        show_all = st.checkbox("Show all paths", value=False)
        max_display = len(paths) if show_all else 20
        
        for i, path in enumerate(paths[:max_display]):
            with st.expander(f"Path {i+1}: {len(path)} hops (strength: {path[-1].get('strength', 0):.2f})"):
                # Visual path display
                st.code(format_path_display(path), language=None)
                
                # Detailed step-by-step
                st.markdown("**Step-by-Step:**")
                for j, step in enumerate(path, 1):
                    from_node = step.get('from', '?')
                    to_node = step.get('to', '?')
                    rel_type = step.get('type', 'connected')
                    strength = step.get('strength', 0)
                    
                    # Color based on relationship type
                    if rel_type in ['causes', 'supports', 'strengthens']:
                        icon = "📈"
                    elif rel_type in ['pressures', 'weakens', 'inverse']:
                        icon = "📉"
                    else:
                        icon = "↔️"
                    
                    st.write(f"{j}. {icon} **{from_node}** --[{rel_type}]--> **{to_node}** (strength: {strength:.2f})")
        
        if len(paths) > max_display:
            st.info(f"Showing {max_display} of {len(paths)} paths. Enable 'Show all paths' to see more.")

def _get_node_options(graph: Any) -> List[str]:
    """Get list of interesting nodes for dropdown"""
    try:
        stats = graph.get_stats()
        node_types = stats.get('node_types', {})
        
        options = []
        
        # Get sample nodes of each type
        for node_type in ['company', 'sector', 'economic_indicator']:
            type_nodes = graph.query({'type': node_type})
            options.extend(type_nodes[:5])  # Top 5 of each type
        
        return sorted(set(options))
    except Exception:
        return []

def _trace_connections_safe(graph: Any, start_node: str, max_depth: int, min_strength: float) -> List[List[Dict]]:
    """Safely trace connections with error handling"""
    try:
        paths = graph.trace_connections(start_node, max_depth=max_depth, min_strength=min_strength)
        return paths
    except Exception as e:
        st.error(f"Tracing failed: {str(e)}")
        return []

def _group_paths_by_target(paths: List[List[Dict]]) -> Dict[str, List[List[Dict]]]:
    """Group paths by their target node"""
    grouped = {}
    for path in paths:
        if path:
            target = path[-1].get('to', 'unknown')
            if target not in grouped:
                grouped[target] = []
            grouped[target].append(path)
    return grouped
```

**Acceptance Criteria**:
- ✅ Node selection dropdown works
- ✅ Custom node ID input works
- ✅ Depth and strength sliders work
- ✅ Trace button triggers graph.trace_connections()
- ✅ Paths display in readable format
- ✅ Step-by-step breakdown shows
- ✅ Icons indicate relationship types
- ✅ Error handling for invalid nodes
- ✅ Performance acceptable for 100+ paths

**Testing Checklist**:
- [ ] Valid node traces connections successfully
- [ ] Invalid node shows error message
- [ ] Max depth=1 shows only direct connections
- [ ] Max depth=5 shows deep paths
- [ ] Min strength=0.9 filters to strong connections only
- [ ] Path display shows correct node names and relationships

---

### Sprint 1.4: Impact Forecaster (2 hours)

#### Task 1.4.1: Implement Impact Forecaster
**File**: `dawsos/ui/graph_intelligence/impact_forecaster.py`
**Time**: 2 hours

```python
"""Impact Forecaster - AI-powered predictions based on graph relationships"""

import streamlit as st
from typing import Any
import plotly.graph_objects as go

def render_impact_forecaster(graph: Any, runtime: Any) -> None:
    """
    Generate impact forecasts using graph intelligence
    
    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 📈 Impact Forecaster")
    st.markdown("AI-powered predictions based on knowledge graph relationships")
    
    # Input controls
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get target options
        target_options = _get_forecast_targets(graph)
        target_node = st.selectbox(
            "Target for Forecast",
            options=target_options,
            help="Select what to forecast"
        )
        
        custom_target = st.text_input(
            "Or enter custom target",
            placeholder="e.g., company_AAPL",
            help="Advanced: Enter any node ID"
        )
        
        if custom_target:
            target_node = custom_target
    
    with col2:
        horizon = st.slider(
            "Forecast Horizon (days)",
            min_value=7,
            max_value=90,
            value=30,
            step=7,
            help="How far ahead to forecast"
        )
    
    # Forecast button
    if st.button("🔮 Generate Forecast", type="primary"):
        if not target_node:
            st.error("Please select or enter a target node")
            return
        
        with st.spinner(f"Analyzing {target_node} with AI..."):
            forecast = _generate_forecast_safe(graph, target_node, horizon)
        
        if not forecast or 'error' in forecast:
            st.error(f"Forecast failed: {forecast.get('error', 'Unknown error')}")
            return
        
        # Display forecast result
        _display_forecast_result(forecast, target_node, horizon)
        
        # Display key drivers
        _display_key_drivers(forecast)
        
        # Display influence breakdown
        _display_influence_breakdown(forecast)

def _get_forecast_targets(graph: Any) -> List[str]:
    """Get interesting nodes suitable for forecasting"""
    try:
        # Companies and sectors are good forecast targets
        companies = graph.query({'type': 'company'})[:10]
        sectors = graph.query({'type': 'sector'})[:5]
        return sorted(set(companies + sectors))
    except Exception:
        return []

def _generate_forecast_safe(graph: Any, target: str, horizon: int) -> Dict[str, Any]:
    """Safely generate forecast with error handling"""
    try:
        return graph.forecast_impact(target, horizon=horizon)
    except Exception as e:
        return {'error': str(e)}

def _display_forecast_result(forecast: Dict[str, Any], target: str, horizon: int):
    """Display main forecast result with visual indicator"""
    st.markdown("### 🎯 Forecast Result")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        forecast_val = forecast.get('forecast', 'neutral').upper()
        
        # Color based on forecast
        if forecast_val == 'BULLISH':
            color = "green"
            icon = "📈"
        elif forecast_val == 'BEARISH':
            color = "red"
            icon = "📉"
        else:
            color = "gray"
            icon = "↔️"
        
        st.markdown(f"### {icon} :{color}[{forecast_val}]")
    
    with col2:
        confidence = forecast.get('confidence', 0)
        st.metric(
            "Confidence",
            f"{confidence:.0%}",
            help="Based on connection strength and influence count"
        )
    
    with col3:
        signal_strength = forecast.get('signal_strength', 0)
        st.metric(
            "Signal Strength",
            f"{signal_strength:.2f}",
            help="Net positive/negative signal"
        )
    
    # Interpretation
    st.markdown(f"""
    **Interpretation**: Based on {forecast.get('influences', 0)} influencing factors,
    the knowledge graph predicts a **{forecast_val}** outlook for {target}
    over the next {horizon} days with {confidence:.0%} confidence.
    """)

def _display_key_drivers(forecast: Dict[str, Any]):
    """Display key drivers affecting the forecast"""
    st.markdown("### 🔑 Key Drivers")
    
    key_drivers = forecast.get('key_drivers', [])
    
    if not key_drivers:
        st.info("No specific drivers identified")
        return
    
    for i, driver in enumerate(key_drivers[:5], 1):
        factor = driver.get('factor', 'Unknown factor')
        impact = driver.get('impact', 0)
        
        # Color based on impact
        if impact > 0:
            icon = "📈"
            impact_str = f"+{impact:.2f}"
            color = "green"
        else:
            icon = "📉"
            impact_str = f"{impact:.2f}"
            color = "red"
        
        st.markdown(f"{i}. {icon} **{factor}**: :{color}[{impact_str} impact]")

def _display_influence_breakdown(forecast: Dict[str, Any]):
    """Display breakdown of positive vs negative influences"""
    st.markdown("### 📊 Influence Breakdown")
    
    # Get influence data from forecast internals (if available)
    positive = forecast.get('positive_factors', 0)
    negative = forecast.get('negative_factors', 0)
    
    if positive == 0 and negative == 0:
        st.info("No influence data available")
        return
    
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = positive - negative,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Net Influence"},
        delta = {'reference': 0},
        gauge = {
            'axis': {'range': [-5, 5]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [-5, -1], 'color': "lightcoral"},
                {'range': [-1, 1], 'color': "lightgray"},
                {'range': [1, 5], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0
            }
        }
    ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Numeric breakdown
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Positive Factors", f"+{positive:.2f}")
    with col2:
        st.metric("Negative Factors", f"{negative:.2f}")
```

**Acceptance Criteria**:
- ✅ Target selection works
- ✅ Horizon slider works
- ✅ Forecast button triggers graph.forecast_impact()
- ✅ Results display with color-coded indicators
- ✅ Key drivers list shows with impact values
- ✅ Gauge chart visualizes net influence
- ✅ Error handling for invalid targets

---

### Sprint 1.5: Related Suggestions (2 hours)

#### Task 1.5.1: Implement Related Suggestions
**File**: `dawsos/ui/graph_intelligence/related_suggestions.py`
**Time**: 2 hours

```python
"""Related Analysis Suggestions - Discover connected opportunities"""

import streamlit as st
from typing import Any, List, Dict

def render_related_suggestions(graph: Any, runtime: Any) -> None:
    """
    Suggest related analyses based on graph connections
    
    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 💡 Related Analysis Suggestions")
    st.markdown("Discover related investment opportunities based on graph intelligence")
    
    # Check if user has recent activity
    recent_analyses = _get_recent_analyses(graph)
    
    if not recent_analyses:
        st.info("📝 No recent analyses found. Run a pattern to get personalized suggestions!")
        return
    
    # Display recent activity
    st.markdown("### 📜 Your Recent Activity")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.metric("Recent Analyses", len(recent_analyses))
    
    with col2:
        for analysis in recent_analyses[:3]:
            symbol = analysis.get('symbol', 'N/A')
            analysis_type = analysis.get('type', 'analysis')
            created = analysis.get('created', 'Unknown')
            st.write(f"• {symbol} - {analysis_type} ({created})")
    
    # Generate suggestions based on most recent analysis
    most_recent = recent_analyses[0]
    suggestions = _generate_suggestions(graph, most_recent)
    
    if not suggestions:
        st.info("No related suggestions available yet. Analyze more companies to build connections!")
        return
    
    # Display suggestions
    st.markdown("### 🎯 Suggested Analyses")
    
    for category, items in suggestions.items():
        st.markdown(f"#### {category}")
        
        cols = st.columns(min(len(items), 3))
        
        for i, item in enumerate(items[:3]):
            with cols[i]:
                st.markdown(f"**{item['symbol']}**")
                st.caption(item['reason'])
                
                if st.button(f"Analyze {item['symbol']}", key=f"analyze_{item['symbol']}_{category}"):
                    _trigger_analysis(runtime, item['symbol'], item.get('pattern', 'company_analysis'))

def _get_recent_analyses(graph: Any) -> List[Dict[str, Any]]:
    """Get user's recent analyses from graph"""
    try:
        # Query for recent DCF analyses
        dcf_nodes = graph.query({'type': 'dcf_analysis'})
        
        # Get node details
        analyses = []
        for node_id in dcf_nodes[:10]:  # Last 10
            node = graph.get_node(node_id)
            if node:
                data = node.get('data', {})
                analyses.append({
                    'symbol': data.get('symbol', 'N/A'),
                    'type': 'DCF Analysis',
                    'created': node.get('created', 'Unknown'),
                    'node_id': node_id
                })
        
        # Sort by created date (most recent first)
        analyses.sort(key=lambda x: x['created'], reverse=True)
        return analyses
        
    except Exception:
        return []

def _generate_suggestions(graph: Any, recent_analysis: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """Generate related suggestions based on recent analysis"""
    suggestions = {}
    
    symbol = recent_analysis.get('symbol')
    if not symbol:
        return suggestions
    
    company_node = f"company_{symbol}"
    
    # Same sector companies
    same_sector = _find_same_sector_companies(graph, company_node)
    if same_sector:
        suggestions["📊 Same Sector"] = same_sector
    
    # Correlated companies
    correlated = _find_correlated_companies(graph, company_node)
    if correlated:
        suggestions["↔️ Correlated"] = correlated
    
    # Competitive alternatives
    competitors = _find_competitors(graph, company_node)
    if competitors:
        suggestions["⚔️ Competitors"] = competitors
    
    return suggestions

def _find_same_sector_companies(graph: Any, company_node: str) -> List[Dict[str, Any]]:
    """Find companies in the same sector"""
    try:
        # Get company's sector
        sector_nodes = []
        if hasattr(graph._graph, 'successors'):
            for successor in graph._graph.successors(company_node):
                node = graph._graph.nodes.get(successor, {})
                if node.get('type') == 'sector':
                    sector_nodes.append(successor)
        
        if not sector_nodes:
            return []
        
        # Get other companies in same sector
        sector = sector_nodes[0]
        peers = []
        
        if hasattr(graph._graph, 'predecessors'):
            for predecessor in graph._graph.predecessors(sector):
                node = graph._graph.nodes.get(predecessor, {})
                if node.get('type') == 'company' and predecessor != company_node:
                    symbol = predecessor.replace('company_', '')
                    peers.append({
                        'symbol': symbol,
                        'reason': f"Same sector peer",
                        'pattern': 'buffett_checklist'
                    })
        
        return peers[:5]
        
    except Exception:
        return []

def _find_correlated_companies(graph: Any, company_node: str) -> List[Dict[str, Any]]:
    """Find correlated companies via graph relationships"""
    # Placeholder - would use relationship_hunter data
    return []

def _find_competitors(graph: Any, company_node: str) -> List[Dict[str, Any]]:
    """Find competitor companies"""
    # Placeholder - would use COMPETES_WITH edges
    return []

def _trigger_analysis(runtime: Any, symbol: str, pattern: str):
    """Trigger analysis for suggested symbol"""
    st.info(f"Triggering {pattern} for {symbol}...")
    # Implementation would execute pattern via runtime
    # For now, just update session state
    st.session_state['suggested_symbol'] = symbol
    st.session_state['suggested_pattern'] = pattern
```

**Acceptance Criteria**:
- ✅ Recent analyses display
- ✅ Suggestions generate based on graph connections
- ✅ Same sector suggestions work
- ✅ Analyze button triggers pattern execution
- ✅ Empty state shows helpful message

---

## Phase 1 Completion Criteria

### Functional Requirements
- ✅ All 5 modules render without errors
- ✅ Each module integrates with KnowledgeGraph API
- ✅ Sub-tabs navigation works smoothly
- ✅ Performance acceptable (<2s load time per tab)

### Code Quality
- ✅ Type hints on all functions
- ✅ Error handling in all graph operations
- ✅ Streamlit caching where appropriate
- ✅ No regression in existing features

### Documentation
- ✅ Each module has docstrings
- ✅ README.md updated with new features
- ✅ User guide created (screenshots + instructions)

---

*[Continued in next response due to length...]*
