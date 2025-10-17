"""Analysis History - Timeline of valuations and analyses over time"""

import streamlit as st
from typing import Any, List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
from dawsos.ui.utils.graph_utils import get_node_display_name

# Check if plotly is available
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None
    make_subplots = None

def render_analysis_history(graph: Any, runtime: Any) -> None:
    """
    Display timeline of historical analyses and valuations

    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 📜 Analysis History")
    st.markdown("Track how your analyses and valuations have evolved over time")

    # Get graph data
    try:
        if not hasattr(graph, '_graph'):
            st.info("📝 Graph not available. Unable to show history.")
            return

        G = graph._graph
        all_nodes = list(G.nodes())

        if not all_nodes:
            st.info("📝 No data in graph yet. Analyze some entities to build history!")
            _show_getting_started()
            return

    except Exception as e:
        st.error(f"Error loading graph: {str(e)}")
        return

    # View mode selection
    view_mode = st.radio(
        "View Mode",
        options=["Timeline View", "Company Tracking", "Valuation Changes", "Analysis Frequency"],
        horizontal=True,
        help="Choose how to view your analysis history"
    )

    st.markdown("---")

    # Render appropriate view
    if view_mode == "Timeline View":
        _render_timeline_view(graph, G, all_nodes)
    elif view_mode == "Company Tracking":
        _render_company_tracking(graph, G, all_nodes)
    elif view_mode == "Valuation Changes":
        _render_valuation_changes(graph, G, all_nodes)
    else:  # Analysis Frequency
        _render_analysis_frequency(graph, G, all_nodes)

def _render_timeline_view(graph: Any, G: Any, all_nodes: List[str]) -> None:
    """Render chronological timeline of all analyses"""
    st.markdown("### 📅 Chronological Timeline")
    st.markdown("All analyses in chronological order")

    # Extract timestamped nodes (nodes with timestamp metadata)
    timestamped_events = []

    for node in all_nodes:
        try:
            node_data = G.nodes.get(node, {})

            # Check for timestamp in metadata
            if '_meta' in node_data:
                meta = node_data['_meta']
                if 'timestamp' in meta or 'analyzed_at' in meta or 'created_at' in meta:
                    timestamp_str = meta.get('timestamp') or meta.get('analyzed_at') or meta.get('created_at')

                    try:
                        # Parse timestamp
                        if isinstance(timestamp_str, str):
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            timestamp = timestamp_str

                        # Determine event type
                        event_type = "Analysis"
                        if 'valuation' in node_data:
                            event_type = "Valuation"
                        elif 'forecast' in node_data:
                            event_type = "Forecast"

                        timestamped_events.append({
                            'node': node,
                            'timestamp': timestamp,
                            'type': event_type,
                            'data': node_data
                        })
                    except (ValueError, AttributeError):
                        continue
        except Exception:
            continue

    if not timestamped_events:
        st.info("📝 No timestamped analyses found. The system will track your analyses going forward!")

        # Show example of what will be tracked
        with st.expander("📋 What Gets Tracked"):
            st.markdown("""
            The system automatically tracks:
            - **Company analyses** (Buffett Checklist, DCF valuations, etc.)
            - **Valuations** (Intrinsic value calculations)
            - **Forecasts** (Impact predictions, price targets)
            - **Market regime checks** (Economic assessments)

            Each analysis is timestamped and stored in the knowledge graph for historical comparison.
            """)
        return

    # Sort by timestamp
    timestamped_events.sort(key=lambda x: x['timestamp'], reverse=True)

    # Time range filter
    col1, col2 = st.columns(2)

    with col1:
        time_filter = st.selectbox(
            "Time Range",
            options=["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
            help="Filter events by time range"
        )

    with col2:
        if time_filter == "Custom":
            days_back = st.number_input("Days Back", min_value=1, max_value=365, value=30)
        else:
            days_back = {
                "Last 7 Days": 7,
                "Last 30 Days": 30,
                "Last 90 Days": 90,
                "All Time": 99999
            }.get(time_filter, 99999)

    # Filter events
    cutoff_date = datetime.now() - timedelta(days=days_back)
    filtered_events = [e for e in timestamped_events if e['timestamp'] >= cutoff_date]

    if not filtered_events:
        st.warning(f"No events found in selected time range")
        return

    st.success(f"📊 Found {len(filtered_events)} event(s)")

    # Display timeline
    for idx, event in enumerate(filtered_events[:50]):  # Show first 50
        timestamp = event['timestamp']
        node_display = get_node_display_name(event['node'])
        event_type = event['type']

        # Icon based on type
        icon = {
            "Analysis": "📊",
            "Valuation": "💰",
            "Forecast": "🔮"
        }.get(event_type, "📝")

        with st.expander(f"{icon} {timestamp.strftime('%Y-%m-%d %H:%M')} - {node_display} ({event_type})", expanded=(idx == 0)):
            _render_event_details(event)

def _render_company_tracking(graph: Any, G: Any, all_nodes: List[str]) -> None:
    """Track specific company's analysis history"""
    st.markdown("### 🏢 Company Tracking")
    st.markdown("See how your view of a specific company has evolved")

    # Get company nodes
    company_nodes = [n for n in all_nodes if n.startswith('company_')]

    if not company_nodes:
        st.info("📝 No companies analyzed yet. Analyze some stocks to enable tracking!")
        return

    # Company selection
    node_display_map = {node: get_node_display_name(node) for node in company_nodes}
    display_to_node = {v: k for k, v in node_display_map.items()}
    sorted_displays = sorted(node_display_map.values())

    selected_display = st.selectbox(
        "Select Company",
        options=sorted_displays,
        help="Choose a company to track"
    )
    selected_node = display_to_node.get(selected_display, company_nodes[0])

    # Get node history (if stored)
    node_data = G.nodes.get(selected_node, {})

    # Display current state
    st.markdown("### 📊 Current State")

    col1, col2, col3 = st.columns(3)

    with col1:
        degree = G.degree(selected_node)
        st.metric("Graph Connections", degree)

    with col2:
        # Check for valuation
        valuation = node_data.get('valuation', node_data.get('intrinsic_value', 'N/A'))
        st.metric("Latest Valuation", f"${valuation:,.2f}" if isinstance(valuation, (int, float)) else valuation)

    with col3:
        # Check for score
        score = node_data.get('moat_score', node_data.get('score', 'N/A'))
        st.metric("Latest Score", f"{score:.1f}" if isinstance(score, (int, float)) else score)

    # History section (placeholder - would need historical storage)
    st.markdown("### 📜 Historical Changes")

    st.info("""
    **Historical tracking coming soon!**

    The system will track:
    - Valuation changes over time
    - Score changes (moat, financial health, etc.)
    - Relationship changes (new connections discovered)
    - Forecast accuracy (predictions vs outcomes)
    """)

def _render_valuation_changes(graph: Any, G: Any, all_nodes: List[str]) -> None:
    """Show how valuations have changed over time"""
    st.markdown("### 💰 Valuation Tracking")
    st.markdown("Track how intrinsic value calculations have evolved")

    # Find nodes with valuations
    valued_nodes = []

    for node in all_nodes:
        if node.startswith('company_'):
            node_data = G.nodes.get(node, {})
            if 'valuation' in node_data or 'intrinsic_value' in node_data:
                valued_nodes.append(node)

    if not valued_nodes:
        st.info("📝 No valuations found. Run DCF analyses to track valuations!")

        with st.expander("💡 How to Generate Valuations"):
            st.markdown("""
            To generate valuations that can be tracked:

            1. **Run DCF Analysis**: "Calculate DCF for AAPL"
            2. **Run Buffett Checklist**: "Analyze AAPL with Buffett Checklist"
            3. **Run Financial Analysis**: "Analyze AAPL fundamentals"

            The system will store valuation results with timestamps for historical tracking.
            """)
        return

    # Display valued companies
    st.success(f"📊 Found {len(valued_nodes)} compan{'y' if len(valued_nodes) == 1 else 'ies'} with valuations")

    # Build table
    data = []
    for node in valued_nodes:
        node_data = G.nodes.get(node, {})
        node_display = get_node_display_name(node)

        valuation = node_data.get('valuation') or node_data.get('intrinsic_value')
        market_price = node_data.get('market_price', node_data.get('price'))

        # Calculate margin of safety if both values available
        margin = None
        if valuation and market_price:
            try:
                margin = ((valuation - market_price) / market_price) * 100
            except (TypeError, ZeroDivisionError):
                pass

        data.append({
            'Company': node_display,
            'Valuation': f"${valuation:,.2f}" if isinstance(valuation, (int, float)) else str(valuation),
            'Market Price': f"${market_price:,.2f}" if isinstance(market_price, (int, float)) else 'N/A',
            'Margin of Safety': f"{margin:+.1f}%" if margin is not None else 'N/A'
        })

    df = pd.DataFrame(data)
    st.dataframe(df, width="stretch", hide_index=True)

    # Placeholder for historical chart
    if PLOTLY_AVAILABLE:
        st.markdown("### 📈 Valuation Trend (Coming Soon)")
        st.info("Future versions will show valuation changes over time as you re-analyze companies")

def _render_analysis_frequency(graph: Any, G: Any, all_nodes: List[str]) -> None:
    """Show analysis frequency and patterns"""
    st.markdown("### 📊 Analysis Activity")
    st.markdown("Understand your analysis patterns and frequency")

    # Count node types
    node_type_counts = {}

    for node in all_nodes:
        if node.startswith('company_'):
            node_type_counts['Companies'] = node_type_counts.get('Companies', 0) + 1
        elif node.startswith('sector_'):
            node_type_counts['Sectors'] = node_type_counts.get('Sectors', 0) + 1
        elif node.startswith('economic_'):
            node_type_counts['Economic'] = node_type_counts.get('Economic', 0) + 1
        else:
            node_type_counts['Other'] = node_type_counts.get('Other', 0) + 1

    # Display metrics
    st.markdown("### 📈 Activity Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Analyses", len(all_nodes))
    with col2:
        st.metric("Companies", node_type_counts.get('Companies', 0))
    with col3:
        st.metric("Sectors", node_type_counts.get('Sectors', 0))
    with col4:
        st.metric("Economic", node_type_counts.get('Economic', 0))

    # Type distribution chart
    if node_type_counts and PLOTLY_AVAILABLE:
        fig = px.pie(
            values=list(node_type_counts.values()),
            names=list(node_type_counts.keys()),
            title="Analysis Distribution by Type"
        )
        st.plotly_chart(fig, width="stretch")
    elif node_type_counts:
        # Fallback to dataframe
        df = pd.DataFrame(list(node_type_counts.items()), columns=['Type', 'Count'])
        st.dataframe(df, width="stretch", hide_index=True)

    # Most analyzed
    st.markdown("### 🏆 Most Connected Entities")
    st.markdown("Entities you've analyzed most thoroughly (by connection count)")

    # Get top 10 by degree
    node_degrees = [(node, G.degree(node)) for node in all_nodes]
    node_degrees.sort(key=lambda x: x[1], reverse=True)

    top_10 = node_degrees[:10]

    data = []
    for node, degree in top_10:
        data.append({
            'Entity': get_node_display_name(node),
            'Connections': degree,
            'Type': 'Company' if node.startswith('company_') else 'Sector' if node.startswith('sector_') else 'Economic' if node.startswith('economic_') else 'Other'
        })

    df = pd.DataFrame(data)
    st.dataframe(df, width="stretch", hide_index=True)

def _render_event_details(event: Dict[str, Any]) -> None:
    """Render details of a single event"""
    node_data = event['data']

    # Display available data
    if 'valuation' in node_data or 'intrinsic_value' in node_data:
        valuation = node_data.get('valuation') or node_data.get('intrinsic_value')
        st.markdown(f"**Valuation**: ${valuation:,.2f}" if isinstance(valuation, (int, float)) else f"**Valuation**: {valuation}")

    if 'moat_score' in node_data:
        st.markdown(f"**Moat Score**: {node_data['moat_score']:.1f}/100")

    if 'score' in node_data:
        st.markdown(f"**Score**: {node_data['score']:.1f}")

    if 'forecast' in node_data:
        forecast = node_data['forecast']
        st.markdown(f"**Forecast**: {forecast}")

    # Show raw data in expander
    with st.expander("🔍 View Raw Data"):
        st.json(node_data)

def _show_getting_started() -> None:
    """Show getting started guide"""
    st.markdown("### 🚀 Getting Started with Analysis History")
    st.markdown("""
    **Track how your understanding evolves over time:**

    **What Gets Tracked:**
    - Company analyses (valuations, scores, forecasts)
    - Economic assessments (market regime, indicators)
    - Sector analyses (performance, correlations)
    - Comparative studies (side-by-side comparisons)

    **How to Build History:**
    1. **Analyze companies**: "Analyze AAPL with Buffett Checklist"
    2. **Calculate valuations**: "Calculate DCF for MSFT"
    3. **Check market conditions**: "What's the current market regime?"
    4. **Re-analyze periodically**: Run the same analysis weekly/monthly

    **What You'll See:**
    - Timeline of all your analyses
    - Valuation changes over time
    - How your view of a company evolved
    - Analysis frequency and patterns

    **Start analyzing to build your history!**
    """)
