"""Sector Correlation Heatmap - Visual sector relationship analysis"""

import streamlit as st
from typing import Any, List, Dict, Tuple
import pandas as pd
from dawsos.ui.utils.graph_utils import get_node_display_name

# Check if plotly is available
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None

def render_sector_correlations(graph: Any, runtime: Any) -> None:
    """
    Display sector correlation heatmap based on graph relationships

    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 🔥 Sector Correlation Heatmap")
    st.markdown("Visualize how sectors relate to each other based on knowledge graph connections")

    # Get graph data
    try:
        if not hasattr(graph, '_graph'):
            st.info("📝 Graph not available. Unable to generate heatmap.")
            return

        G = graph._graph
        all_nodes = list(G.nodes())

        if not all_nodes:
            st.info("📝 No data in graph yet. Run some analyses to build sector relationships!")
            _show_getting_started()
            return

    except Exception as e:
        st.error(f"Error loading graph: {str(e)}")
        return

    # Find all sectors
    sector_nodes = [n for n in all_nodes if n.startswith('sector_')]

    if len(sector_nodes) < 2:
        st.info("📝 Need at least 2 sectors for correlation analysis. Analyze more stocks!")
        _show_getting_started()
        return

    # Configuration options
    col1, col2 = st.columns(2)

    with col1:
        correlation_method = st.selectbox(
            "Correlation Method",
            options=["Shared Companies", "Common Economic Factors", "Direct Relationships"],
            help="How to measure sector correlation"
        )

    with col2:
        min_threshold = st.slider(
            "Minimum Correlation",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            help="Filter weak correlations"
        )

    # Generate heatmap button
    if st.button("📊 Generate Heatmap", type="primary"):
        with st.spinner("Analyzing sector relationships..."):
            try:
                # Generate correlation matrix
                if correlation_method == "Shared Companies":
                    correlation_matrix = _calculate_company_correlations(G, sector_nodes)
                elif correlation_method == "Common Economic Factors":
                    correlation_matrix = _calculate_economic_correlations(G, sector_nodes)
                else:  # Direct Relationships
                    correlation_matrix = _calculate_direct_correlations(G, sector_nodes)

                # Filter by threshold
                filtered_matrix = _filter_correlations(correlation_matrix, min_threshold)

                if not filtered_matrix or len(filtered_matrix) < 2:
                    st.warning("⚠️ No correlations above threshold. Try lowering the minimum correlation.")
                    return

                # Display heatmap
                _render_heatmap(filtered_matrix, correlation_method)

                # Display insights
                _render_correlation_insights(filtered_matrix)

                # Display detailed table
                _render_correlation_table(filtered_matrix)

            except Exception as e:
                st.error(f"Error generating heatmap: {str(e)}")
                st.exception(e)

def _calculate_company_correlations(G: Any, sector_nodes: List[str]) -> Dict[str, Dict[str, float]]:
    """Calculate correlations based on shared companies"""
    matrix = {}

    for sector1 in sector_nodes:
        matrix[sector1] = {}

        # Find companies in sector1
        companies1 = set()
        for neighbor in G.neighbors(sector1):
            if neighbor.startswith('company_'):
                companies1.add(neighbor)

        for sector2 in sector_nodes:
            if sector1 == sector2:
                matrix[sector1][sector2] = 1.0
                continue

            # Find companies in sector2
            companies2 = set()
            for neighbor in G.neighbors(sector2):
                if neighbor.startswith('company_'):
                    companies2.add(neighbor)

            # Calculate Jaccard similarity (shared companies / total companies)
            if companies1 or companies2:
                shared = len(companies1.intersection(companies2))
                total = len(companies1.union(companies2))
                correlation = shared / total if total > 0 else 0.0
            else:
                correlation = 0.0

            matrix[sector1][sector2] = correlation

    return matrix

def _calculate_economic_correlations(G: Any, sector_nodes: List[str]) -> Dict[str, Dict[str, float]]:
    """Calculate correlations based on common economic factors"""
    matrix = {}

    for sector1 in sector_nodes:
        matrix[sector1] = {}

        # Find economic factors affecting sector1
        economic1 = set()
        for neighbor in G.neighbors(sector1):
            if neighbor.startswith('economic_'):
                economic1.add(neighbor)

        for sector2 in sector_nodes:
            if sector1 == sector2:
                matrix[sector1][sector2] = 1.0
                continue

            # Find economic factors affecting sector2
            economic2 = set()
            for neighbor in G.neighbors(sector2):
                if neighbor.startswith('economic_'):
                    economic2.add(neighbor)

            # Calculate Jaccard similarity (shared factors / total factors)
            if economic1 or economic2:
                shared = len(economic1.intersection(economic2))
                total = len(economic1.union(economic2))
                correlation = shared / total if total > 0 else 0.0
            else:
                correlation = 0.0

            matrix[sector1][sector2] = correlation

    return matrix

def _calculate_direct_correlations(G: Any, sector_nodes: List[str]) -> Dict[str, Dict[str, float]]:
    """Calculate correlations based on direct graph relationships"""
    matrix = {}

    for sector1 in sector_nodes:
        matrix[sector1] = {}

        for sector2 in sector_nodes:
            if sector1 == sector2:
                matrix[sector1][sector2] = 1.0
                continue

            # Check if there's a direct edge
            edge_data = G.get_edge_data(sector1, sector2, default=None)
            if edge_data:
                correlation = edge_data.get('strength', 0.5)
            else:
                # Check reverse direction
                edge_data = G.get_edge_data(sector2, sector1, default=None)
                if edge_data:
                    correlation = edge_data.get('strength', 0.5)
                else:
                    correlation = 0.0

            matrix[sector1][sector2] = correlation

    return matrix

def _filter_correlations(matrix: Dict[str, Dict[str, float]], threshold: float) -> Dict[str, Dict[str, float]]:
    """Filter correlations below threshold"""
    # Find sectors with at least one correlation above threshold
    active_sectors = set()

    for sector1, correlations in matrix.items():
        for sector2, corr in correlations.items():
            if sector1 != sector2 and corr >= threshold:
                active_sectors.add(sector1)
                active_sectors.add(sector2)

    # Build filtered matrix
    filtered = {}
    for sector1 in active_sectors:
        filtered[sector1] = {}
        for sector2 in active_sectors:
            filtered[sector1][sector2] = matrix[sector1][sector2]

    return filtered

def _render_heatmap(matrix: Dict[str, Dict[str, float]], method: str) -> None:
    """Render the correlation heatmap"""
    # Convert to clean names
    sectors = sorted(matrix.keys())
    clean_names = [get_node_display_name(s) for s in sectors]

    # Build correlation data
    corr_data = []
    for s1 in sectors:
        row = []
        for s2 in sectors:
            row.append(matrix[s1][s2])
        corr_data.append(row)

    # Create DataFrame
    df = pd.DataFrame(corr_data, index=clean_names, columns=clean_names)

    if PLOTLY_AVAILABLE:
        # Plotly heatmap
        fig = go.Figure(data=go.Heatmap(
            z=df.values,
            x=df.columns,
            y=df.index,
            colorscale='RdYlGn',
            zmin=0,
            zmax=1,
            text=df.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))

        fig.update_layout(
            title=f"Sector Correlation Heatmap ({method})",
            xaxis_title="Sector",
            yaxis_title="Sector",
            height=600,
            width=800
        )

        st.plotly_chart(fig, width="stretch")
    else:
        # Fallback to dataframe
        st.markdown(f"### Sector Correlation Heatmap ({method})")
        st.dataframe(df.style.background_gradient(cmap='RdYlGn', vmin=0, vmax=1))

def _render_correlation_insights(matrix: Dict[str, Dict[str, float]]) -> None:
    """Render insights from correlation matrix"""
    st.markdown("### 💡 Key Insights")

    # Find strongest correlations
    strong_correlations = []

    for sector1, correlations in matrix.items():
        for sector2, corr in correlations.items():
            if sector1 < sector2:  # Avoid duplicates
                strong_correlations.append((sector1, sector2, corr))

    # Sort by strength
    strong_correlations.sort(key=lambda x: x[2], reverse=True)

    if not strong_correlations:
        st.info("No significant correlations found")
        return

    # Display top 5
    st.markdown("**Strongest Correlations:**")
    for idx, (s1, s2, corr) in enumerate(strong_correlations[:5], 1):
        s1_clean = get_node_display_name(s1)
        s2_clean = get_node_display_name(s2)

        # Strength indicator
        if corr > 0.7:
            strength_text = "Very Strong"
            emoji = "🟢"
        elif corr > 0.4:
            strength_text = "Moderate"
            emoji = "🟡"
        else:
            strength_text = "Weak"
            emoji = "🟠"

        st.markdown(f"{idx}. {emoji} **{s1_clean}** ↔ **{s2_clean}**: {corr:.2f} ({strength_text})")

    # Find weakest (excluding zeros)
    weak_correlations = [c for c in strong_correlations if c[2] > 0]
    weak_correlations.sort(key=lambda x: x[2])

    if weak_correlations:
        st.markdown("**Weakest Correlations:**")
        for idx, (s1, s2, corr) in enumerate(weak_correlations[:3], 1):
            s1_clean = get_node_display_name(s1)
            s2_clean = get_node_display_name(s2)
            st.markdown(f"{idx}. 🔵 **{s1_clean}** ↔ **{s2_clean}**: {corr:.2f}")

def _render_correlation_table(matrix: Dict[str, Dict[str, float]]) -> None:
    """Render detailed correlation table"""
    with st.expander("📋 Detailed Correlation Table", expanded=False):
        # Convert to DataFrame
        sectors = sorted(matrix.keys())
        clean_names = [get_node_display_name(s) for s in sectors]

        corr_data = []
        for s1 in sectors:
            row = []
            for s2 in sectors:
                row.append(f"{matrix[s1][s2]:.2f}")
            corr_data.append(row)

        df = pd.DataFrame(corr_data, index=clean_names, columns=clean_names)
        st.dataframe(df, width="stretch")

def _show_getting_started() -> None:
    """Show getting started guide"""
    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    **Build sector relationships to enable correlation analysis:**

    1. **Analyze multiple stocks** - Each stock adds to its sector's data
    2. **Cover different sectors** - Try Technology, Healthcare, Financials, etc.
    3. **Add economic context** - Economic factors affect all sectors

    **Example queries to build data:**
    - "Analyze AAPL with Buffett Checklist" (Technology)
    - "Analyze JPM" (Financials)
    - "Analyze JNJ" (Healthcare)
    - "Check market regime" (Economic context)

    Once you have data from 2+ sectors, you can generate correlation heatmaps!
    """)
