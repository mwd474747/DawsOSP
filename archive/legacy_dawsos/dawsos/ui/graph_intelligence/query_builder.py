"""Query Builder - Advanced graph search interface for power users"""

import streamlit as st
from typing import Any, List, Dict, Optional
import pandas as pd
from dawsos.ui.utils.graph_utils import safe_query, get_node_display_name

def render_query_builder(graph: Any, runtime: Any) -> None:
    """
    Advanced query builder for power users to search the knowledge graph

    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 🔍 Query Builder")
    st.markdown("Powerful graph search for advanced users - find exactly what you need")

    # Get graph data
    try:
        if not hasattr(graph, '_graph'):
            st.info("📝 Graph not available. Unable to query.")
            return

        G = graph._graph
        all_nodes = list(G.nodes())

        if not all_nodes:
            st.info("📝 No data in graph yet. Build the graph first by analyzing stocks!")
            _show_getting_started()
            return

    except Exception as e:
        st.error(f"Error loading graph: {str(e)}")
        return

    # Query mode selection
    query_mode = st.radio(
        "Query Mode",
        options=["Simple Search", "Advanced Filters", "Pattern Matching"],
        horizontal=True,
        help="Choose your query complexity level"
    )

    st.markdown("---")

    # Render appropriate query interface
    if query_mode == "Simple Search":
        _render_simple_search(graph, G, all_nodes)
    elif query_mode == "Advanced Filters":
        _render_advanced_filters(graph, G, all_nodes)
    else:  # Pattern Matching
        _render_pattern_matching(graph, G, all_nodes)

def _render_simple_search(graph: Any, G: Any, all_nodes: List[str]) -> None:
    """Simple keyword search interface"""
    st.markdown("### 🔎 Simple Search")
    st.markdown("Search for nodes by keyword or type")

    col1, col2 = st.columns([3, 1])

    with col1:
        search_term = st.text_input(
            "Search Term",
            placeholder="e.g., AAPL, Technology, inflation",
            help="Search for nodes containing this term"
        )

    with col2:
        max_results = st.number_input(
            "Max Results",
            min_value=10,
            max_value=500,
            value=50,
            step=10
        )

    # Node type filters
    st.markdown("**Filter by Type:**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        include_companies = st.checkbox("Companies", value=True)
    with col2:
        include_sectors = st.checkbox("Sectors", value=True)
    with col3:
        include_economic = st.checkbox("Economic", value=True)
    with col4:
        include_other = st.checkbox("Other", value=True)

    if st.button("🔍 Search", type="primary"):
        if not search_term:
            st.warning("Please enter a search term")
            return

        with st.spinner("Searching..."):
            # Filter nodes by type
            filtered_nodes = []
            search_lower = search_term.lower()

            for node in all_nodes:
                # Type filtering
                if node.startswith('company_') and not include_companies:
                    continue
                if node.startswith('sector_') and not include_sectors:
                    continue
                if node.startswith('economic_') and not include_economic:
                    continue
                if not any(node.startswith(p) for p in ['company_', 'sector_', 'economic_']) and not include_other:
                    continue

                # Keyword matching
                if search_lower in node.lower():
                    filtered_nodes.append(node)

            # Limit results
            results = filtered_nodes[:max_results]

            if not results:
                st.warning(f"No results found for '{search_term}'")
                return

            st.success(f"✅ Found {len(results)} result(s) (showing up to {max_results})")

            # Display results
            _display_search_results(G, results)

def _render_advanced_filters(graph: Any, G: Any, all_nodes: List[str]) -> None:
    """Advanced multi-criteria filtering"""
    st.markdown("### ⚙️ Advanced Filters")
    st.markdown("Combine multiple criteria for precise results")

    # Filter criteria
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Node Criteria:**")

        node_type = st.selectbox(
            "Node Type",
            options=["All", "Companies", "Sectors", "Economic", "Other"],
            help="Filter by node type"
        )

        min_connections = st.slider(
            "Minimum Connections",
            min_value=0,
            max_value=20,
            value=0,
            help="Nodes must have at least this many connections"
        )

        keyword_filter = st.text_input(
            "Keyword Contains (optional)",
            placeholder="e.g., tech, financial",
            help="Node ID must contain this text"
        )

    with col2:
        st.markdown("**Connection Criteria:**")

        connection_type = st.selectbox(
            "Has Connection Type",
            options=["Any", "SUPPORTS", "PRESSURES", "STRENGTHENS", "WEAKENS", "CONTAINS", "RELATED"],
            help="Filter by relationship type"
        )

        min_strength = st.slider(
            "Minimum Connection Strength",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            help="At least one connection must be this strong"
        )

        max_results = st.number_input(
            "Max Results",
            min_value=10,
            max_value=500,
            value=100,
            step=10
        )

    if st.button("🔍 Apply Filters", type="primary"):
        with st.spinner("Filtering nodes..."):
            filtered_nodes = []

            for node in all_nodes:
                # Node type filter
                if node_type == "Companies" and not node.startswith('company_'):
                    continue
                if node_type == "Sectors" and not node.startswith('sector_'):
                    continue
                if node_type == "Economic" and not node.startswith('economic_'):
                    continue
                if node_type == "Other" and any(node.startswith(p) for p in ['company_', 'sector_', 'economic_']):
                    continue

                # Keyword filter
                if keyword_filter and keyword_filter.lower() not in node.lower():
                    continue

                # Connection count filter
                degree = G.degree(node)
                if degree < min_connections:
                    continue

                # Connection type and strength filter
                if connection_type != "Any" or min_strength > 0:
                    meets_criteria = False

                    for neighbor in G.neighbors(node):
                        edge_data = G.get_edge_data(node, neighbor, default={})
                        rel_type = edge_data.get('type', 'RELATED')
                        strength = edge_data.get('strength', 0.0)

                        # Check connection type
                        if connection_type != "Any" and rel_type != connection_type:
                            continue

                        # Check strength
                        if strength >= min_strength:
                            meets_criteria = True
                            break

                    if not meets_criteria:
                        continue

                filtered_nodes.append(node)

            # Limit results
            results = filtered_nodes[:max_results]

            if not results:
                st.warning("No nodes match the specified criteria")
                return

            st.success(f"✅ Found {len(results)} result(s) (showing up to {max_results})")

            # Display results
            _display_search_results(G, results)

def _render_pattern_matching(graph: Any, G: Any, all_nodes: List[str]) -> None:
    """Pattern-based graph queries"""
    st.markdown("### 🎯 Pattern Matching")
    st.markdown("Find nodes matching specific graph patterns")

    # Pre-defined patterns
    pattern_type = st.selectbox(
        "Select Pattern",
        options=[
            "Highly Connected Hubs",
            "Isolated Nodes",
            "Bridge Nodes",
            "Mutual Connections",
            "Influence Centers",
            "Custom Pattern"
        ],
        help="Pre-defined graph patterns"
    )

    # Pattern-specific parameters
    if pattern_type == "Highly Connected Hubs":
        min_degree = st.slider("Minimum Connections", 5, 50, 10)
        description = f"Find nodes with {min_degree}+ connections (central to the graph)"

    elif pattern_type == "Isolated Nodes":
        max_degree = st.slider("Maximum Connections", 0, 5, 2)
        description = f"Find nodes with ≤{max_degree} connections (need more analysis)"

    elif pattern_type == "Bridge Nodes":
        description = "Find nodes that connect otherwise disconnected clusters"

    elif pattern_type == "Mutual Connections":
        description = "Find pairs of nodes that connect to each other"

    elif pattern_type == "Influence Centers":
        min_outgoing = st.slider("Minimum Outgoing Connections", 3, 20, 5)
        description = f"Find nodes with {min_outgoing}+ outgoing connections (influence others)"

    else:  # Custom Pattern
        description = "Define your own pattern criteria"

    st.info(f"ℹ️ {description}")

    max_results = st.number_input("Max Results", 10, 200, 50, 10)

    if st.button("🔍 Find Pattern", type="primary"):
        with st.spinner(f"Finding {pattern_type}..."):
            results = []

            if pattern_type == "Highly Connected Hubs":
                results = [n for n in all_nodes if G.degree(n) >= min_degree]

            elif pattern_type == "Isolated Nodes":
                results = [n for n in all_nodes if G.degree(n) <= max_degree]

            elif pattern_type == "Bridge Nodes":
                # Simple bridge detection: nodes whose removal would increase components
                import networkx as nx
                original_components = nx.number_connected_components(G.to_undirected())

                for node in all_nodes[:100]:  # Check first 100 for performance
                    G_temp = G.copy()
                    G_temp.remove_node(node)
                    new_components = nx.number_connected_components(G_temp.to_undirected())

                    if new_components > original_components:
                        results.append(node)

            elif pattern_type == "Mutual Connections":
                checked = set()
                for node in all_nodes:
                    for neighbor in G.neighbors(node):
                        if neighbor in checked:
                            continue
                        # Check if neighbor connects back
                        if node in list(G.neighbors(neighbor)):
                            results.append(f"{node} ↔ {neighbor}")
                    checked.add(node)

            elif pattern_type == "Influence Centers":
                results = [n for n in all_nodes if G.out_degree(n) >= min_outgoing]

            # Limit results
            results = results[:max_results]

            if not results:
                st.warning(f"No nodes match the '{pattern_type}' pattern")
                return

            st.success(f"✅ Found {len(results)} node(s)")

            # Display results
            if pattern_type == "Mutual Connections":
                _display_mutual_connections(results)
            else:
                _display_search_results(G, results)

def _display_search_results(G: Any, results: List[str]) -> None:
    """Display search results in a structured format"""
    st.markdown("### 📊 Results")

    # Summary statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Results", len(results))

    with col2:
        avg_degree = sum(G.degree(n) for n in results) / len(results) if results else 0
        st.metric("Avg Connections", f"{avg_degree:.1f}")

    with col3:
        node_types = {}
        for node in results:
            if node.startswith('company_'):
                node_types['Companies'] = node_types.get('Companies', 0) + 1
            elif node.startswith('sector_'):
                node_types['Sectors'] = node_types.get('Sectors', 0) + 1
            elif node.startswith('economic_'):
                node_types['Economic'] = node_types.get('Economic', 0) + 1
            else:
                node_types['Other'] = node_types.get('Other', 0) + 1

        most_common = max(node_types.items(), key=lambda x: x[1]) if node_types else ("N/A", 0)
        st.metric("Most Common Type", most_common[0])

    # Results table
    st.markdown("**Node Details:**")

    # Build DataFrame
    data = []
    for node in results:
        degree = G.degree(node)
        in_degree = G.in_degree(node)
        out_degree = G.out_degree(node)

        # Get node type
        if node.startswith('company_'):
            node_type = "Company"
        elif node.startswith('sector_'):
            node_type = "Sector"
        elif node.startswith('economic_'):
            node_type = "Economic"
        else:
            node_type = "Other"

        data.append({
            'Node': get_node_display_name(node),
            'Type': node_type,
            'Connections': degree,
            'In': in_degree,
            'Out': out_degree,
            'ID': node
        })

    df = pd.DataFrame(data)

    # Display with column config
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "Node": st.column_config.TextColumn("Node", width="large"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Connections": st.column_config.NumberColumn("Total", width="small"),
            "In": st.column_config.NumberColumn("In", width="small"),
            "Out": st.column_config.NumberColumn("Out", width="small"),
            "ID": st.column_config.TextColumn("Full ID", width="medium")
        }
    )

    # Export option
    if st.button("📥 Export Results as CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="graph_query_results.csv",
            mime="text/csv"
        )

def _display_mutual_connections(results: List[str]) -> None:
    """Display mutual connection pairs"""
    st.markdown("**Mutual Connection Pairs:**")

    for idx, pair in enumerate(results, 1):
        st.markdown(f"{idx}. {pair}")

def _show_getting_started() -> None:
    """Show getting started guide"""
    st.markdown("### 🚀 Getting Started with Query Builder")
    st.markdown("""
    **The Query Builder lets you search the knowledge graph like a database:**

    **Simple Search** - Quick keyword lookup
    - Search: "AAPL" → Find all Apple-related nodes
    - Search: "tech" → Find all technology-related nodes

    **Advanced Filters** - Multi-criteria search
    - Find: Companies with 10+ connections in Technology sector
    - Find: Economic nodes with strong (>0.7) pressure relationships

    **Pattern Matching** - Structural queries
    - Find: Highly connected hubs (central nodes)
    - Find: Bridge nodes (connect clusters)
    - Find: Isolated nodes (need more analysis)

    **Build your graph first:**
    1. Analyze some stocks: "Analyze AAPL with Buffett Checklist"
    2. Check economic conditions: "What's the market regime?"
    3. Compare stocks: "Compare AAPL and MSFT"
    4. Return here to query your knowledge!
    """)
