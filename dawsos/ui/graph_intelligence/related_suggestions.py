"""Related Analysis Suggestions - Discover connected opportunities"""

import streamlit as st
from typing import Any, List, Dict, Tuple
from datetime import datetime, timedelta
from dawsos.ui.utils.graph_utils import get_node_display_name

def render_related_suggestions(graph: Any, runtime: Any) -> None:
    """
    Suggest related analyses based on graph connections

    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 💡 Related Analysis Suggestions")
    st.markdown("Discover connected opportunities and expand your knowledge graph")

    # Get graph data
    try:
        if not hasattr(graph, '_graph'):
            st.info("📝 Graph not available. Unable to generate suggestions.")
            return

        G = graph._graph
        all_nodes = list(G.nodes())

        if not all_nodes:
            st.info("📝 No data in the graph yet. Run some analyses to get suggestions!")
            _show_getting_started()
            return

    except Exception as e:
        st.error(f"Error loading graph: {str(e)}")
        return

    # Create tabs for different suggestion types
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔥 Recent Activity",
        "🏢 Same Sector",
        "🔗 Connected",
        "🎯 Recommended"
    ])

    # Tab 1: Recent Activity
    with tab1:
        _render_recent_activity(graph, all_nodes)

    # Tab 2: Same Sector Analysis
    with tab2:
        _render_same_sector_suggestions(graph, G, all_nodes)

    # Tab 3: Connected Nodes
    with tab3:
        _render_connected_suggestions(graph, G, all_nodes)

    # Tab 4: AI Recommendations
    with tab4:
        _render_ai_recommendations(graph, G, all_nodes)

def _render_recent_activity(graph: Any, all_nodes: List[str]) -> None:
    """Show recent analyses and suggest follow-ups"""
    st.markdown("### 🔥 Recent Activity")
    st.markdown("Based on your recent analyses, here are some follow-up opportunities:")

    # Get recent company nodes (proxy for recent activity)
    company_nodes = [n for n in all_nodes if n.startswith('company_')]

    if not company_nodes:
        st.info("📝 No recent company analyses found. Try analyzing a stock first!")
        return

    # Show most recent 5
    recent = company_nodes[:5]

    for node in recent:
        display_name = get_node_display_name(node)
        symbol = node.replace('company_', '').upper()

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.markdown(f"**{display_name}**")

        with col2:
            st.markdown(f"`{symbol}`")

        with col3:
            if st.button(f"📊 Analyze", key=f"recent_{symbol}"):
                st.info(f"Click here to run: 'Analyze {symbol} with Buffett Checklist'")

def _render_same_sector_suggestions(graph: Any, G: Any, all_nodes: List[str]) -> None:
    """Suggest same-sector companies"""
    st.markdown("### 🏢 Same Sector Opportunities")
    st.markdown("Expand your analysis to peers in the same sector:")

    # Find sectors with companies
    sector_map = {}

    for node in all_nodes:
        if node.startswith('company_'):
            # Find connected sector
            neighbors = list(G.neighbors(node))
            sectors = [n for n in neighbors if n.startswith('sector_')]

            if sectors:
                sector = sectors[0]
                if sector not in sector_map:
                    sector_map[sector] = []
                sector_map[sector].append(node)

    if not sector_map:
        st.info("📝 No sector data available yet. Analyze some stocks to build sector relationships!")
        return

    # Show sectors with multiple companies
    for sector, companies in sorted(sector_map.items(), key=lambda x: len(x[1]), reverse=True)[:3]:
        sector_display = get_node_display_name(sector)

        with st.expander(f"**{sector_display}** ({len(companies)} companies)", expanded=True):
            st.markdown("**Companies in this sector:**")

            cols = st.columns(3)
            for idx, company in enumerate(companies[:6]):  # Show max 6
                company_display = get_node_display_name(company)
                symbol = company.replace('company_', '').upper()

                with cols[idx % 3]:
                    st.markdown(f"• {company_display} (`{symbol}`)")

            if len(companies) > 6:
                st.markdown(f"*...and {len(companies) - 6} more*")

def _render_connected_suggestions(graph: Any, G: Any, all_nodes: List[str]) -> None:
    """Suggest nodes connected to analyzed nodes"""
    st.markdown("### 🔗 Connected Opportunities")
    st.markdown("Explore entities connected to your recent analyses:")

    # Find companies with interesting connections
    company_nodes = [n for n in all_nodes if n.startswith('company_')]

    if not company_nodes:
        st.info("📝 No companies analyzed yet. Start by analyzing a stock!")
        return

    suggestions = []

    for company in company_nodes[:5]:  # Check recent 5
        neighbors = list(G.neighbors(company))

        # Find interesting neighbors (not sectors, not system nodes)
        interesting = [
            n for n in neighbors
            if not n.startswith('sector_')
            and not n.startswith('system_')
            and not n.startswith('_')
            and not n.startswith('company_')
        ]

        if interesting:
            company_display = get_node_display_name(company)

            for neighbor in interesting[:3]:  # Top 3 per company
                edge_data = G.get_edge_data(company, neighbor, default={})
                strength = edge_data.get('strength', 0)
                rel_type = edge_data.get('type', 'RELATED')

                suggestions.append({
                    'from': company_display,
                    'to': get_node_display_name(neighbor),
                    'relationship': rel_type,
                    'strength': strength
                })

    if not suggestions:
        st.info("📝 No connected entities found. The graph needs more data!")
        return

    # Sort by strength
    suggestions = sorted(suggestions, key=lambda x: x['strength'], reverse=True)[:10]

    for idx, sugg in enumerate(suggestions, 1):
        strength_emoji = "🟢" if sugg['strength'] > 0.7 else "🟡" if sugg['strength'] > 0.4 else "🟠"

        st.markdown(
            f"{idx}. {strength_emoji} **{sugg['from']}** --[{sugg['relationship']}]--> "
            f"**{sugg['to']}** (strength: {sugg['strength']:.2f})"
        )

def _render_ai_recommendations(graph: Any, G: Any, all_nodes: List[str]) -> None:
    """Generate AI-powered recommendations"""
    st.markdown("### 🎯 AI-Powered Recommendations")
    st.markdown("Smart suggestions based on graph analysis:")

    # Analyze graph to find opportunities
    recommendations = _generate_recommendations(G, all_nodes)

    if not recommendations:
        st.info("📝 Not enough data yet. Keep building your knowledge graph!")
        return

    for idx, rec in enumerate(recommendations, 1):
        rec_type = rec.get('type', 'general')
        title = rec.get('title', 'Recommendation')
        description = rec.get('description', '')
        priority = rec.get('priority', 'medium')

        # Priority emoji
        if priority == 'high':
            priority_emoji = "🔴"
        elif priority == 'medium':
            priority_emoji = "🟡"
        else:
            priority_emoji = "🟢"

        with st.expander(f"{priority_emoji} {idx}. {title}", expanded=(idx == 1)):
            st.markdown(description)

            # Action buttons
            actions = rec.get('actions', [])
            if actions:
                st.markdown("**Quick Actions:**")
                cols = st.columns(len(actions))
                for col_idx, action in enumerate(actions):
                    with cols[col_idx]:
                        if st.button(action, key=f"rec_{idx}_{col_idx}"):
                            st.info(f"Try asking: '{action}'")

def _generate_recommendations(G: Any, all_nodes: List[str]) -> List[Dict[str, Any]]:
    """Generate smart recommendations based on graph analysis"""
    recommendations = []

    # Count node types
    companies = [n for n in all_nodes if n.startswith('company_')]
    sectors = [n for n in all_nodes if n.startswith('sector_')]
    economic = [n for n in all_nodes if n.startswith('economic_')]

    # Recommendation 1: Diversification
    if len(companies) > 0 and len(companies) < 5:
        recommendations.append({
            'type': 'diversification',
            'title': 'Expand Your Analysis Coverage',
            'description': f"You've analyzed {len(companies)} compan{'y' if len(companies) == 1 else 'ies'}. "
                         f"Consider expanding to at least 5 companies across different sectors for better diversification insights.",
            'priority': 'medium',
            'actions': ['Analyze AAPL', 'Analyze MSFT', 'Analyze JPM']
        })

    # Recommendation 2: Economic context
    if len(companies) > 0 and len(economic) == 0:
        recommendations.append({
            'type': 'economic',
            'title': 'Add Economic Context',
            'description': "Your analysis could benefit from economic indicators. Try checking the current market regime "
                         "or analyzing how inflation affects your holdings.",
            'priority': 'high',
            'actions': ['Check market regime', 'Analyze inflation impact']
        })

    # Recommendation 3: Sector analysis
    if len(sectors) == 0 and len(companies) > 2:
        recommendations.append({
            'type': 'sector',
            'title': 'Explore Sector Relationships',
            'description': "Build sector-level insights by comparing companies within the same sectors. "
                         "This reveals industry trends and competitive dynamics.",
            'priority': 'medium',
            'actions': ['Compare tech stocks', 'Analyze financial sector']
        })

    # Recommendation 4: Connection depth
    avg_connections = sum(G.degree(n) for n in all_nodes) / len(all_nodes) if all_nodes else 0
    if avg_connections < 2:
        recommendations.append({
            'type': 'depth',
            'title': 'Deepen Your Analysis',
            'description': f"Average connections per node: {avg_connections:.1f}. Run more comprehensive analyses "
                         f"to build richer relationships and enable better forecasting.",
            'priority': 'high',
            'actions': ['Run Buffett Checklist', 'Compare multiple stocks']
        })

    # Recommendation 5: Pattern discovery
    if len(all_nodes) > 10:
        recommendations.append({
            'type': 'patterns',
            'title': 'Discover Patterns',
            'description': "Your graph has enough data to discover meaningful patterns. "
                         "Browse the Pattern Browser to see what the system has learned.",
            'priority': 'low',
            'actions': ['View Pattern Browser', 'Check graph stats']
        })

    return recommendations[:5]  # Return top 5

def _show_getting_started() -> None:
    """Show getting started guide"""
    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    **Build your knowledge graph to get personalized suggestions:**

    1. **Analyze a stock** - Try "Analyze AAPL with Buffett Checklist"
    2. **Check market conditions** - Ask "What's the current market regime?"
    3. **Compare companies** - Try "Compare AAPL and MSFT"
    4. **Explore patterns** - Visit the Pattern Browser tab

    As you use the system, this tab will provide intelligent suggestions based on your activity!
    """)
