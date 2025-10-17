"""Connection Tracer - Explore relationships between entities"""

import streamlit as st
from typing import Any, List, Dict, Optional
from dawsos.ui.utils.graph_utils import safe_query, format_path_display, get_node_display_name

# Check if plotly is available
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None

def render_connection_tracer(graph: Any, runtime: Any) -> None:
    """
    Trace connections between entities in the knowledge graph

    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 🔗 Connection Tracer")
    st.markdown("Discover how concepts, companies, and economic factors are interconnected")

    # Get all nodes for selection
    try:
        stats = graph.get_stats()
        all_nodes = list(graph._graph.nodes()) if hasattr(graph, '_graph') else []
    except Exception as e:
        st.error(f"Error loading graph nodes: {str(e)}")
        return

    if not all_nodes:
        st.info("📝 No nodes in the graph yet. Run some analyses to build connections!")
        return

    # Filter nodes to meaningful ones (exclude system nodes)
    meaningful_nodes = [n for n in all_nodes if not n.startswith('_') and not n.startswith('system_')]

    if not meaningful_nodes:
        st.info("📝 No meaningful nodes to trace yet. Try analyzing some stocks or economic data!")
        return

    # Clean node names for display
    node_display_map = {node: get_node_display_name(node) for node in meaningful_nodes}
    display_to_node = {v: k for k, v in node_display_map.items()}

    # Sort by display name
    sorted_displays = sorted(node_display_map.values())

    # Two-column layout for source and target selection
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📍 Starting Point")
        source_display = st.selectbox(
            "Select source node",
            options=sorted_displays,
            key="connection_source",
            help="The starting node for connection tracing"
        )
        source_node = display_to_node.get(source_display, meaningful_nodes[0])

    with col2:
        st.markdown("### 🎯 Destination")
        target_display = st.selectbox(
            "Select target node",
            options=sorted_displays,
            key="connection_target",
            help="The destination node to find paths to"
        )
        target_node = display_to_node.get(target_display, meaningful_nodes[1] if len(meaningful_nodes) > 1 else meaningful_nodes[0])

    # Configuration options
    st.markdown("### ⚙️ Trace Configuration")
    col1, col2, col3 = st.columns(3)

    with col1:
        max_depth = st.slider(
            "Maximum Depth",
            min_value=1,
            max_value=6,
            value=3,
            help="Maximum number of hops to explore"
        )

    with col2:
        min_strength = st.slider(
            "Minimum Strength",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Minimum connection strength (0=weak, 1=strong)"
        )

    with col3:
        max_paths = st.slider(
            "Max Paths to Show",
            min_value=1,
            max_value=10,
            value=5,
            help="Maximum number of paths to display"
        )

    # Trace button
    if st.button("🔍 Trace Connections", type="primary"):
        if source_node == target_node:
            st.warning("⚠️ Source and target are the same. Please select different nodes.")
            return

        with st.spinner(f"Tracing connections from {source_display} to {target_display}..."):
            try:
                # Try to use graph's trace_connections method if available
                if hasattr(graph, 'trace_connections'):
                    paths = graph.trace_connections(
                        source_node,
                        target_node,
                        max_depth=max_depth,
                        min_strength=min_strength,
                        max_paths=max_paths
                    )
                else:
                    # Fallback: Use basic pathfinding
                    paths = _find_paths_fallback(graph, source_node, target_node, max_depth, min_strength, max_paths)

                if not paths:
                    st.warning(f"🔍 No paths found between {source_display} and {target_display} within depth {max_depth} and strength {min_strength}")
                    _suggest_alternatives(graph, source_node, target_node)
                    return

                # Display results
                st.success(f"✅ Found {len(paths)} path(s)")

                # Show each path
                for idx, path in enumerate(paths, 1):
                    with st.expander(f"Path {idx}: {len(path)} hop(s)", expanded=(idx == 1)):
                        _render_path(path, idx)

                        # Visualize path if plotly available
                        if PLOTLY_AVAILABLE and len(path) <= 10:
                            _visualize_path(path, idx)

                # Summary statistics
                _render_path_statistics(paths)

            except Exception as e:
                st.error(f"Error tracing connections: {str(e)}")
                st.exception(e)

def _find_paths_fallback(graph: Any, source: str, target: str, max_depth: int, min_strength: float, max_paths: int) -> List[List[Dict[str, Any]]]:
    """Fallback pathfinding using NetworkX if graph doesn't have trace_connections"""
    try:
        import networkx as nx

        if not hasattr(graph, '_graph'):
            return []

        G = graph._graph

        # Find all simple paths up to max_depth
        all_paths = []
        try:
            for path in nx.all_simple_paths(G, source, target, cutoff=max_depth):
                # Convert to edge list with metadata
                edge_path = []
                for i in range(len(path) - 1):
                    from_node = path[i]
                    to_node = path[i + 1]

                    # Get edge data
                    edge_data = G.get_edge_data(from_node, to_node, default={})
                    strength = edge_data.get('strength', 0.5)
                    rel_type = edge_data.get('type', 'RELATED')

                    # Filter by strength
                    if strength < min_strength:
                        break

                    edge_path.append({
                        'from': from_node,
                        'to': to_node,
                        'type': rel_type,
                        'strength': strength,
                        'metadata': edge_data
                    })

                # Only add if all edges passed strength filter
                if len(edge_path) == len(path) - 1:
                    all_paths.append(edge_path)

                # Limit paths
                if len(all_paths) >= max_paths:
                    break

        except nx.NetworkXNoPath:
            return []

        return all_paths

    except Exception as e:
        st.warning(f"Pathfinding error: {str(e)}")
        return []

def _render_path(path: List[Dict[str, Any]], path_num: int) -> None:
    """Render a single path with step-by-step breakdown"""
    total_strength = sum(step.get('strength', 0) for step in path)
    avg_strength = total_strength / len(path) if path else 0

    # Path metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hops", len(path))
    with col2:
        st.metric("Avg Strength", f"{avg_strength:.2f}")
    with col3:
        strength_emoji = "🟢" if avg_strength > 0.7 else "🟡" if avg_strength > 0.4 else "🔴"
        st.metric("Quality", strength_emoji)

    # Step-by-step breakdown
    st.markdown("**Connection Steps:**")
    for idx, step in enumerate(path, 1):
        from_node = get_node_display_name(step.get('from', '?'))
        to_node = get_node_display_name(step.get('to', '?'))
        rel_type = step.get('type', 'RELATED')
        strength = step.get('strength', 0)

        # Strength indicator
        strength_bar = "█" * int(strength * 10)
        strength_color = "🟢" if strength > 0.7 else "🟡" if strength > 0.4 else "🔴"

        st.markdown(f"{idx}. **{from_node}** --[{rel_type}]--> **{to_node}**")
        st.markdown(f"   {strength_color} Strength: {strength:.2f} `{strength_bar}`")

        # Show metadata if available
        metadata = step.get('metadata', {})
        if metadata:
            interesting_keys = [k for k in metadata.keys() if k not in ['type', 'strength', 'timestamp']]
            if interesting_keys:
                st.markdown(f"   *Context: {', '.join(f'{k}={metadata[k]}' for k in interesting_keys[:3])}*")

def _visualize_path(path: List[Dict[str, Any]], path_num: int) -> None:
    """Create a network visualization of the path using Plotly"""
    if not PLOTLY_AVAILABLE:
        return

    # Build node and edge lists
    nodes = []
    edges = []
    node_set = set()

    for step in path:
        from_node = step.get('from', '?')
        to_node = step.get('to', '?')

        if from_node not in node_set:
            nodes.append(from_node)
            node_set.add(from_node)
        if to_node not in node_set:
            nodes.append(to_node)
            node_set.add(to_node)

        edges.append((from_node, to_node, step.get('strength', 0)))

    # Create positions (simple linear layout)
    positions = {node: (idx, 0) for idx, node in enumerate(nodes)}

    # Create edge traces
    edge_traces = []
    for from_node, to_node, strength in edges:
        x0, y0 = positions[from_node]
        x1, y1 = positions[to_node]

        # Color by strength
        color = f'rgba({int(255*(1-strength))}, {int(255*strength)}, 0, 0.6)'

        edge_traces.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=strength*5, color=color),
            hoverinfo='none',
            showlegend=False
        ))

    # Create node trace
    node_x = [positions[node][0] for node in nodes]
    node_y = [positions[node][1] for node in nodes]
    node_text = [get_node_display_name(node) for node in nodes]

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        marker=dict(size=20, color='lightblue', line=dict(width=2, color='darkblue')),
        hoverinfo='text',
        showlegend=False
    )

    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        title=f"Path {path_num} Visualization",
        showlegend=False,
        hovermode='closest',
        height=300,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, width="stretch")

def _render_path_statistics(paths: List[List[Dict[str, Any]]]) -> None:
    """Render summary statistics across all paths"""
    st.markdown("### 📊 Path Analysis")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_paths = len(paths)
        st.metric("Total Paths", total_paths)

    with col2:
        avg_hops = sum(len(p) for p in paths) / len(paths) if paths else 0
        st.metric("Avg Hops", f"{avg_hops:.1f}")

    with col3:
        all_strengths = [step.get('strength', 0) for path in paths for step in path]
        avg_strength = sum(all_strengths) / len(all_strengths) if all_strengths else 0
        st.metric("Avg Strength", f"{avg_strength:.2f}")

    with col4:
        strongest_path = max(paths, key=lambda p: sum(s.get('strength', 0) for s in p) / len(p)) if paths else None
        if strongest_path:
            strength = sum(s.get('strength', 0) for s in strongest_path) / len(strongest_path)
            st.metric("Best Path", f"{strength:.2f}")

    # Relationship type breakdown
    rel_types = {}
    for path in paths:
        for step in path:
            rel_type = step.get('type', 'RELATED')
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

    if rel_types:
        st.markdown("**Relationship Types Used:**")
        for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"- **{rel_type}**: {count} connection(s)")

def _suggest_alternatives(graph: Any, source: str, target: str) -> None:
    """Suggest alternative nodes when no path is found"""
    st.markdown("### 💡 Suggestions")
    st.markdown("Try one of these alternatives:")

    # Find nodes connected to source
    try:
        if hasattr(graph, '_graph'):
            G = graph._graph
            source_neighbors = list(G.neighbors(source))[:5]
            target_neighbors = list(G.neighbors(target))[:5]

            if source_neighbors:
                st.markdown(f"**Nodes connected to {get_node_display_name(source)}:**")
                for node in source_neighbors:
                    st.markdown(f"- {get_node_display_name(node)}")

            if target_neighbors:
                st.markdown(f"**Nodes connected to {get_node_display_name(target)}:**")
                for node in target_neighbors:
                    st.markdown(f"- {get_node_display_name(node)}")
    except Exception:
        st.markdown("• Try increasing the maximum depth")
        st.markdown("• Try lowering the minimum strength threshold")
        st.markdown("• Try different source/target nodes")
