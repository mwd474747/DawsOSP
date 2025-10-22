"""Live Graph Statistics Dashboard"""

import streamlit as st
import pandas as pd
from typing import Any, Dict
from dawsos.ui.utils.graph_utils import get_cached_graph_stats

# Check if plotly is available
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    px = None
    go = None

def render_live_stats(graph: Any, runtime: Any) -> None:
    """
    Display real-time graph statistics and health metrics

    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 📊 Live Graph Statistics")
    st.markdown("Real-time metrics showing system knowledge and intelligence growth")

    # Get stats (cached for 5 minutes)
    try:
        stats = get_cached_graph_stats(graph)
    except Exception as e:
        st.error(f"Error loading graph stats: {str(e)}")
        return

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_nodes = stats.get('total_nodes', 0)
        st.metric(
            "Total Nodes",
            f"{total_nodes:,}",
            help="All knowledge nodes in the graph"
        )

    with col2:
        total_edges = stats.get('total_edges', 0)
        st.metric(
            "Connections",
            f"{total_edges:,}",
            help="Relationships between nodes"
        )

    with col3:
        total_patterns = stats.get('total_patterns', 0)
        st.metric(
            "Patterns",
            total_patterns,
            help="Automatically discovered patterns"
        )

    with col4:
        avg_conn = stats.get('avg_connections', 0)
        st.metric(
            "Avg Connections",
            f"{avg_conn:.1f}",
            help="Average connections per node"
        )

    # Check if graph has data
    if total_nodes == 0:
        st.info("📝 No data in the graph yet. Run some analyses to start building knowledge!")
        _show_quick_start_guide()
        return

    # Node types breakdown
    st.markdown("### 📦 Node Types Distribution")
    node_types = stats.get('node_types', {})

    if node_types and PLOTLY_AVAILABLE:
        df = pd.DataFrame(list(node_types.items()), columns=['Type', 'Count'])
        df = df.sort_values('Count', ascending=False)

        fig = px.bar(
            df,
            x='Type',
            y='Count',
            title="Knowledge Node Types",
            color='Count',
            color_continuous_scale='Blues',
            labels={'Type': 'Node Type', 'Count': 'Number of Nodes'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")
    elif node_types:
        # Fallback to dataframe if plotly not available
        df = pd.DataFrame(list(node_types.items()), columns=['Type', 'Count'])
        df = df.sort_values('Count', ascending=False)
        st.dataframe(df, width="stretch")
    else:
        st.info("No node type data available")

    # Edge types breakdown
    st.markdown("### 🔗 Relationship Types")
    edge_types = stats.get('edge_types', {})

    if edge_types and PLOTLY_AVAILABLE:
        df = pd.DataFrame(list(edge_types.items()), columns=['Relationship', 'Count'])
        df = df.sort_values('Count', ascending=False)

        fig = px.pie(
            df,
            names='Relationship',
            values='Count',
            title="Relationship Type Distribution",
            hole=0.3
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")
    elif edge_types:
        # Fallback to dataframe
        df = pd.DataFrame(list(edge_types.items()), columns=['Relationship', 'Count'])
        df = df.sort_values('Count', ascending=False)
        st.dataframe(df, width="stretch")
    else:
        st.info("No relationship data available")

    # Cache performance (if available)
    if hasattr(graph, '_cache_stats'):
        st.markdown("### ⚡ Cache Performance")
        _render_cache_stats(graph._cache_stats)

    # Graph health assessment
    st.markdown("### 🏥 Graph Health Assessment")
    _render_health_assessment(stats)

    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh Stats", help="Clear cache and reload statistics"):
            st.cache_data.clear()
            st.rerun()

    with col2:
        if st.button("📊 Detailed View", help="Show detailed graph statistics"):
            with st.expander("Detailed Statistics", expanded=True):
                st.json(stats)

def _render_cache_stats(cache_stats: Dict[str, int]) -> None:
    """Render cache performance metrics"""
    col1, col2 = st.columns(2)

    with col1:
        total_trace = cache_stats.get('trace_hits', 0) + cache_stats.get('trace_misses', 0)
        if total_trace > 0:
            hit_rate = cache_stats['trace_hits'] / total_trace
            st.metric(
                "Trace Cache Hit Rate",
                f"{hit_rate:.1%}",
                help="Higher is better (less recomputation)"
            )
        else:
            st.metric("Trace Cache Hit Rate", "N/A", help="No trace queries yet")

    with col2:
        total_forecast = cache_stats.get('forecast_hits', 0) + cache_stats.get('forecast_misses', 0)
        if total_forecast > 0:
            hit_rate = cache_stats['forecast_hits'] / total_forecast
            st.metric(
                "Forecast Cache Hit Rate",
                f"{hit_rate:.1%}",
                help="Higher is better (less recomputation)"
            )
        else:
            st.metric("Forecast Cache Hit Rate", "N/A", help="No forecast queries yet")

def _render_health_assessment(stats: Dict[str, Any]) -> None:
    """Assess and display graph health"""
    total_nodes = stats.get('total_nodes', 0)
    total_edges = stats.get('total_edges', 0)
    avg_conn = stats.get('avg_connections', 0)
    total_patterns = stats.get('total_patterns', 0)

    health_score = 0
    health_messages = []

    # Check node count
    if total_nodes > 1000:
        health_score += 30
        health_messages.append("✅ Rich knowledge base (1000+ nodes)")
    elif total_nodes > 100:
        health_score += 20
        health_messages.append("✅ Growing knowledge base (100+ nodes)")
    elif total_nodes > 10:
        health_score += 10
        health_messages.append("⚠️ Small knowledge base (consider running more analyses)")
    else:
        health_messages.append("📝 Very small graph (run analyses to build knowledge)")

    # Check connectivity
    if avg_conn > 3:
        health_score += 40
        health_messages.append("✅ Highly connected (excellent for forecasting)")
    elif avg_conn > 1.5:
        health_score += 25
        health_messages.append("✅ Moderately connected (good intelligence)")
    elif avg_conn > 0.5:
        health_score += 15
        health_messages.append("⚠️ Low connectivity (limited forecasting capability)")
    else:
        health_messages.append("📝 Sparse connections (add relationships to improve)")

    # Check patterns
    if total_patterns > 10:
        health_score += 30
        health_messages.append("✅ Pattern-rich (system actively learning)")
    elif total_patterns > 5:
        health_score += 20
        health_messages.append("✅ Some patterns discovered (learning in progress)")
    elif total_patterns > 0:
        health_score += 10
        health_messages.append("⚠️ Few patterns (needs more data)")
    else:
        health_messages.append("📝 No patterns yet (accumulating data)")

    # Display health score with color coding
    if health_score >= 70:
        health_color = "green"
        health_status = "Excellent"
    elif health_score >= 40:
        health_color = "orange"
        health_status = "Good"
    else:
        health_color = "red"
        health_status = "Developing"

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown(f"### :{health_color}[{health_status}]")
        st.metric("Health Score", f"{health_score}/100")

    with col2:
        st.markdown("**Assessment:**")
        for msg in health_messages:
            st.write(msg)

    # Recommendations based on health
    if health_score < 70:
        st.markdown("**💡 Recommendations:**")
        if total_nodes < 100:
            st.write("• Run more analyses to build the knowledge base")
        if avg_conn < 2:
            st.write("• Explore connection patterns to build relationships")
        if total_patterns < 5:
            st.write("• Continue using the system to discover patterns")

def _show_quick_start_guide() -> None:
    """Show quick start guide for empty graph"""
    st.markdown("### 🚀 Quick Start Guide")
    st.markdown("""
    **To build the knowledge graph, try these:**

    1. **Analyze a stock** - Go to Chat tab and ask "Analyze AAPL with Buffett Checklist"
    2. **Check market regime** - Ask "What's the current market regime?"
    3. **Compare stocks** - Ask "Compare AAPL and MSFT"
    4. **Explore patterns** - Browse the Pattern Browser tab

    Each analysis adds nodes and connections to the graph, enabling:
    - Connection tracing (see how factors relate)
    - Impact forecasting (predict outcomes)
    - Pattern discovery (find recurring trends)
    """)
