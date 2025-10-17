"""Comparative Analysis - Side-by-side entity comparison"""

import streamlit as st
from typing import Any, List, Dict, Optional, Tuple
import pandas as pd
from dawsos.ui.utils.graph_utils import get_node_display_name

# Check if plotly is available
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    make_subplots = None

def render_comparative_analysis(graph: Any, runtime: Any) -> None:
    """
    Side-by-side comparison of entities from the knowledge graph

    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## ⚖️ Comparative Analysis")
    st.markdown("Compare two entities side-by-side to understand their differences and similarities")

    # Get graph data
    try:
        if not hasattr(graph, '_graph'):
            st.info("📝 Graph not available. Unable to compare.")
            return

        G = graph._graph
        all_nodes = list(G.nodes())

        if not all_nodes:
            st.info("📝 No data in graph yet. Analyze some entities first!")
            _show_getting_started()
            return

    except Exception as e:
        st.error(f"Error loading graph: {str(e)}")
        return

    # Filter to meaningful nodes
    meaningful_nodes = [n for n in all_nodes if not n.startswith('_') and not n.startswith('system_')]

    if len(meaningful_nodes) < 2:
        st.info("📝 Need at least 2 entities for comparison. Analyze more stocks!")
        _show_getting_started()
        return

    # Clean node names for display
    node_display_map = {node: get_node_display_name(node) for node in meaningful_nodes}
    display_to_node = {v: k for k, v in node_display_map.items()}

    # Sort by display name
    sorted_displays = sorted(node_display_map.values())

    # Entity selection
    st.markdown("### 🎯 Select Entities to Compare")

    col1, col2 = st.columns(2)

    with col1:
        entity1_display = st.selectbox(
            "Entity 1",
            options=sorted_displays,
            key="compare_entity1",
            help="First entity to compare"
        )
        entity1 = display_to_node.get(entity1_display, meaningful_nodes[0])

    with col2:
        # Filter out entity1 from entity2 options
        entity2_options = [d for d in sorted_displays if d != entity1_display]
        entity2_display = st.selectbox(
            "Entity 2",
            options=entity2_options if entity2_options else sorted_displays,
            key="compare_entity2",
            help="Second entity to compare"
        )
        entity2 = display_to_node.get(entity2_display, meaningful_nodes[1] if len(meaningful_nodes) > 1 else meaningful_nodes[0])

    # Comparison options
    st.markdown("### ⚙️ Comparison Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        compare_connections = st.checkbox("Compare Connections", value=True)

    with col2:
        compare_relationships = st.checkbox("Compare Relationships", value=True)

    with col3:
        compare_shared = st.checkbox("Find Shared Entities", value=True)

    # Compare button
    if st.button("⚖️ Compare", type="primary"):
        if entity1 == entity2:
            st.warning("⚠️ Please select two different entities")
            return

        with st.spinner(f"Comparing {entity1_display} vs {entity2_display}..."):
            try:
                # Perform comparison
                comparison_data = _perform_comparison(
                    G,
                    entity1,
                    entity2,
                    compare_connections,
                    compare_relationships,
                    compare_shared
                )

                # Display results
                _render_comparison_results(
                    comparison_data,
                    entity1_display,
                    entity2_display,
                    compare_connections,
                    compare_relationships,
                    compare_shared
                )

            except Exception as e:
                st.error(f"Error performing comparison: {str(e)}")
                st.exception(e)

def _perform_comparison(
    G: Any,
    entity1: str,
    entity2: str,
    include_connections: bool,
    include_relationships: bool,
    include_shared: bool
) -> Dict[str, Any]:
    """Perform the comparison analysis"""
    result = {
        'entity1': entity1,
        'entity2': entity2
    }

    # Basic metrics
    result['metrics'] = {
        'entity1': {
            'total_connections': G.degree(entity1),
            'incoming': G.in_degree(entity1),
            'outgoing': G.out_degree(entity1)
        },
        'entity2': {
            'total_connections': G.degree(entity2),
            'incoming': G.in_degree(entity2),
            'outgoing': G.out_degree(entity2)
        }
    }

    if include_connections:
        # Get all neighbors
        neighbors1 = set(G.neighbors(entity1))
        neighbors2 = set(G.neighbors(entity2))

        result['connections'] = {
            'entity1_only': list(neighbors1 - neighbors2),
            'entity2_only': list(neighbors2 - neighbors1),
            'shared': list(neighbors1.intersection(neighbors2))
        }

    if include_relationships:
        # Analyze relationship types
        rel_types1 = {}
        for neighbor in G.neighbors(entity1):
            edge_data = G.get_edge_data(entity1, neighbor, default={})
            rel_type = edge_data.get('type', 'RELATED')
            rel_types1[rel_type] = rel_types1.get(rel_type, 0) + 1

        rel_types2 = {}
        for neighbor in G.neighbors(entity2):
            edge_data = G.get_edge_data(entity2, neighbor, default={})
            rel_type = edge_data.get('type', 'RELATED')
            rel_types2[rel_type] = rel_types2.get(rel_type, 0) + 1

        result['relationships'] = {
            'entity1': rel_types1,
            'entity2': rel_types2
        }

    if include_shared:
        # Find shared connections
        neighbors1 = set(G.neighbors(entity1))
        neighbors2 = set(G.neighbors(entity2))
        shared = neighbors1.intersection(neighbors2)

        result['shared_details'] = []
        for shared_node in shared:
            # Get edge details for both
            edge1 = G.get_edge_data(entity1, shared_node, default={})
            edge2 = G.get_edge_data(entity2, shared_node, default={})

            result['shared_details'].append({
                'node': shared_node,
                'entity1_type': edge1.get('type', 'RELATED'),
                'entity1_strength': edge1.get('strength', 0.0),
                'entity2_type': edge2.get('type', 'RELATED'),
                'entity2_strength': edge2.get('strength', 0.0)
            })

    return result

def _render_comparison_results(
    data: Dict[str, Any],
    entity1_display: str,
    entity2_display: str,
    show_connections: bool,
    show_relationships: bool,
    show_shared: bool
) -> None:
    """Render the comparison results"""

    st.markdown("### 📊 Comparison Results")

    # Basic metrics comparison
    _render_metrics_comparison(data['metrics'], entity1_display, entity2_display)

    # Connection comparison
    if show_connections and 'connections' in data:
        st.markdown("---")
        _render_connections_comparison(data['connections'], entity1_display, entity2_display)

    # Relationship type comparison
    if show_relationships and 'relationships' in data:
        st.markdown("---")
        _render_relationships_comparison(data['relationships'], entity1_display, entity2_display)

    # Shared entities
    if show_shared and 'shared_details' in data:
        st.markdown("---")
        _render_shared_entities(data['shared_details'], entity1_display, entity2_display)

def _render_metrics_comparison(
    metrics: Dict[str, Dict[str, int]],
    entity1_display: str,
    entity2_display: str
) -> None:
    """Render basic metrics comparison"""
    st.markdown("#### 📈 Basic Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**Total Connections**")
        m1 = metrics['entity1']['total_connections']
        m2 = metrics['entity2']['total_connections']
        delta = m1 - m2

        st.metric(entity1_display, m1, delta=f"{delta:+d} vs {entity2_display}")
        st.metric(entity2_display, m2, delta=f"{-delta:+d} vs {entity1_display}")

    with col2:
        st.markdown(f"**Incoming**")
        m1 = metrics['entity1']['incoming']
        m2 = metrics['entity2']['incoming']
        delta = m1 - m2

        st.metric(entity1_display, m1, delta=f"{delta:+d}")
        st.metric(entity2_display, m2, delta=f"{-delta:+d}")

    with col3:
        st.markdown(f"**Outgoing**")
        m1 = metrics['entity1']['outgoing']
        m2 = metrics['entity2']['outgoing']
        delta = m1 - m2

        st.metric(entity1_display, m1, delta=f"{delta:+d}")
        st.metric(entity2_display, m2, delta=f"{-delta:+d}")

def _render_connections_comparison(
    connections: Dict[str, List[str]],
    entity1_display: str,
    entity2_display: str
) -> None:
    """Render connection comparison"""
    st.markdown("#### 🔗 Connection Comparison")

    entity1_only = connections['entity1_only']
    entity2_only = connections['entity2_only']
    shared = connections['shared']

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(f"Only {entity1_display}", len(entity1_only))

    with col2:
        st.metric("Shared", len(shared))

    with col3:
        st.metric(f"Only {entity2_display}", len(entity2_only))

    # Venn diagram visualization (if plotly available)
    if PLOTLY_AVAILABLE:
        _render_venn_diagram(len(entity1_only), len(shared), len(entity2_only), entity1_display, entity2_display)

    # Lists of unique connections
    with st.expander(f"📋 Unique to {entity1_display} ({len(entity1_only)} connections)"):
        if entity1_only:
            for node in entity1_only[:20]:  # Show first 20
                st.markdown(f"• {get_node_display_name(node)}")
            if len(entity1_only) > 20:
                st.markdown(f"*...and {len(entity1_only) - 20} more*")
        else:
            st.info("No unique connections")

    with st.expander(f"📋 Unique to {entity2_display} ({len(entity2_only)} connections)"):
        if entity2_only:
            for node in entity2_only[:20]:  # Show first 20
                st.markdown(f"• {get_node_display_name(node)}")
            if len(entity2_only) > 20:
                st.markdown(f"*...and {len(entity2_only) - 20} more*")
        else:
            st.info("No unique connections")

def _render_relationships_comparison(
    relationships: Dict[str, Dict[str, int]],
    entity1_display: str,
    entity2_display: str
) -> None:
    """Render relationship type comparison"""
    st.markdown("#### 🎯 Relationship Types")

    rel1 = relationships['entity1']
    rel2 = relationships['entity2']

    if not rel1 and not rel2:
        st.info("No relationship data available")
        return

    # Create comparison chart
    if PLOTLY_AVAILABLE:
        # Get all unique relationship types
        all_types = set(list(rel1.keys()) + list(rel2.keys()))

        # Build data for chart
        entity1_counts = [rel1.get(t, 0) for t in sorted(all_types)]
        entity2_counts = [rel2.get(t, 0) for t in sorted(all_types)]

        fig = go.Figure(data=[
            go.Bar(name=entity1_display, x=sorted(all_types), y=entity1_counts),
            go.Bar(name=entity2_display, x=sorted(all_types), y=entity2_counts)
        ])

        fig.update_layout(
            title="Relationship Type Distribution",
            xaxis_title="Relationship Type",
            yaxis_title="Count",
            barmode='group',
            height=400
        )

        st.plotly_chart(fig, width="stretch")
    else:
        # Fallback: Show as table
        all_types = set(list(rel1.keys()) + list(rel2.keys()))
        data = []
        for rel_type in sorted(all_types):
            data.append({
                'Type': rel_type,
                entity1_display: rel1.get(rel_type, 0),
                entity2_display: rel2.get(rel_type, 0)
            })

        df = pd.DataFrame(data)
        st.dataframe(df, width="stretch", hide_index=True)

def _render_shared_entities(
    shared_details: List[Dict[str, Any]],
    entity1_display: str,
    entity2_display: str
) -> None:
    """Render shared entities details"""
    st.markdown("#### 🤝 Shared Connections")

    if not shared_details:
        st.info("No shared connections found")
        return

    st.markdown(f"Found **{len(shared_details)}** entities connected to both:")

    # Build DataFrame
    data = []
    for detail in shared_details[:20]:  # Show first 20
        node_display = get_node_display_name(detail['node'])

        data.append({
            'Entity': node_display,
            f'{entity1_display} Type': detail['entity1_type'],
            f'{entity1_display} Strength': f"{detail['entity1_strength']:.2f}",
            f'{entity2_display} Type': detail['entity2_type'],
            f'{entity2_display} Strength': f"{detail['entity2_strength']:.2f}"
        })

    df = pd.DataFrame(data)
    st.dataframe(df, width="stretch", hide_index=True)

    if len(shared_details) > 20:
        st.info(f"Showing first 20 of {len(shared_details)} shared connections")

def _render_venn_diagram(
    left_only: int,
    shared: int,
    right_only: int,
    left_label: str,
    right_label: str
) -> None:
    """Render a simple Venn diagram representation"""
    if not PLOTLY_AVAILABLE:
        return

    # Create a simple bar chart to represent the Venn diagram
    fig = go.Figure(data=[
        go.Bar(
            x=[left_label, 'Shared', right_label],
            y=[left_only, shared, right_only],
            marker=dict(color=['lightblue', 'lightgreen', 'lightcoral']),
            text=[left_only, shared, right_only],
            textposition='auto'
        )
    ])

    fig.update_layout(
        title="Connection Distribution",
        xaxis_title="Category",
        yaxis_title="Count",
        height=300,
        showlegend=False
    )

    st.plotly_chart(fig, width="stretch")

def _show_getting_started() -> None:
    """Show getting started guide"""
    st.markdown("### 🚀 Getting Started with Comparative Analysis")
    st.markdown("""
    **Compare entities to understand their similarities and differences:**

    **What You Can Compare:**
    - **Companies**: Compare AAPL vs MSFT, JPM vs BAC, etc.
    - **Sectors**: Compare Technology vs Healthcare sector characteristics
    - **Economic Factors**: Compare inflation vs interest rates impact

    **What You'll Learn:**
    - Connection counts (who's more connected?)
    - Unique vs shared connections (what makes them different?)
    - Relationship types (how do they relate to the world?)
    - Strength comparisons (which connections are stronger?)

    **Build your graph first:**
    1. Analyze multiple entities: "Analyze AAPL", "Analyze MSFT"
    2. Check economic factors: "What's the market regime?"
    3. Return here to compare them side-by-side!

    **Example Comparisons:**
    - AAPL vs GOOGL → See how they differ in their moats and sectors
    - Technology vs Financials → Compare sector characteristics
    - 2024 Inflation vs 2024 Interest Rates → See correlated impacts
    """)
