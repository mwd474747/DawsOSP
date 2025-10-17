"""Impact Forecaster - AI-powered predictions based on graph relationships"""

import streamlit as st
from typing import Any, List, Dict, Optional
from datetime import datetime, timedelta
from dawsos.ui.utils.graph_utils import safe_query, get_node_display_name

# Check if plotly is available
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    make_subplots = None

def render_impact_forecaster(graph: Any, runtime: Any) -> None:
    """
    Generate impact forecasts using graph intelligence

    Args:
        graph: KnowledgeGraph instance
        runtime: AgentRuntime instance
    """
    st.markdown("## 🔮 Impact Forecaster")
    st.markdown("AI-powered predictions based on knowledge graph relationships and historical patterns")

    # Get all nodes for selection
    try:
        all_nodes = list(graph._graph.nodes()) if hasattr(graph, '_graph') else []
    except Exception as e:
        st.error(f"Error loading graph nodes: {str(e)}")
        return

    if not all_nodes:
        st.info("📝 No nodes in the graph yet. Run some analyses to enable forecasting!")
        return

    # Filter to meaningful nodes (companies, sectors, economic indicators)
    meaningful_nodes = [n for n in all_nodes if not n.startswith('_') and not n.startswith('system_')]

    if not meaningful_nodes:
        st.info("📝 No meaningful nodes to forecast yet. Try analyzing some stocks or economic data!")
        return

    # Clean node names for display
    node_display_map = {node: get_node_display_name(node) for node in meaningful_nodes}
    display_to_node = {v: k for k, v in node_display_map.items()}

    # Sort by display name
    sorted_displays = sorted(node_display_map.values())

    # Target selection
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🎯 Forecast Target")
        target_display = st.selectbox(
            "Select target to forecast",
            options=sorted_displays,
            key="forecast_target",
            help="The entity to forecast"
        )
        target_node = display_to_node.get(target_display, meaningful_nodes[0])

    with col2:
        st.markdown("### ⏱️ Horizon")
        horizon_days = st.slider(
            "Forecast horizon (days)",
            min_value=7,
            max_value=90,
            value=30,
            step=7,
            help="How far into the future to forecast"
        )

    # Additional configuration
    st.markdown("### ⚙️ Forecast Configuration")
    col1, col2, col3 = st.columns(3)

    with col1:
        sensitivity = st.select_slider(
            "Sensitivity",
            options=["Low", "Medium", "High"],
            value="Medium",
            help="How sensitive to weak signals"
        )

    with col2:
        include_sentiment = st.checkbox(
            "Include Sentiment",
            value=True,
            help="Factor in market sentiment indicators"
        )

    with col3:
        show_details = st.checkbox(
            "Show Detailed Breakdown",
            value=True,
            help="Display all contributing factors"
        )

    # Generate forecast button
    if st.button("🔮 Generate Forecast", type="primary"):
        with st.spinner(f"Generating {horizon_days}-day forecast for {target_display}..."):
            try:
                # Try to use graph's forecast_impact method if available
                if hasattr(graph, 'forecast_impact'):
                    forecast = graph.forecast_impact(
                        target_node,
                        horizon_days=horizon_days,
                        sensitivity=sensitivity.lower(),
                        include_sentiment=include_sentiment
                    )
                else:
                    # Fallback: Generate forecast using graph analysis
                    forecast = _generate_forecast_fallback(
                        graph,
                        target_node,
                        horizon_days,
                        sensitivity.lower(),
                        include_sentiment
                    )

                if not forecast:
                    st.warning(f"⚠️ Unable to generate forecast for {target_display}. Insufficient data.")
                    return

                # Display forecast results
                _render_forecast_results(forecast, target_display, horizon_days, show_details)

            except Exception as e:
                st.error(f"Error generating forecast: {str(e)}")
                st.exception(e)

def _generate_forecast_fallback(
    graph: Any,
    target_node: str,
    horizon_days: int,
    sensitivity: str,
    include_sentiment: bool
) -> Optional[Dict[str, Any]]:
    """Fallback forecast generation using graph analysis"""
    try:
        if not hasattr(graph, '_graph'):
            return None

        G = graph._graph

        # Get all edges connected to target
        if target_node not in G:
            return None

        # Analyze incoming influences (what affects this node)
        incoming = list(G.predecessors(target_node))
        incoming_influences = []

        for source in incoming:
            edge_data = G.get_edge_data(source, target_node, default={})
            strength = edge_data.get('strength', 0.5)
            rel_type = edge_data.get('type', 'RELATED')

            # Sensitivity threshold
            threshold = {'low': 0.7, 'medium': 0.5, 'high': 0.3}.get(sensitivity, 0.5)

            if strength >= threshold:
                incoming_influences.append({
                    'from': source,
                    'type': rel_type,
                    'strength': strength,
                    'impact': _estimate_impact(rel_type, strength)
                })

        # Calculate overall sentiment
        bullish_score = sum(1 for inf in incoming_influences if inf['impact'] > 0)
        bearish_score = sum(1 for inf in incoming_influences if inf['impact'] < 0)
        neutral_score = sum(1 for inf in incoming_influences if inf['impact'] == 0)

        total = bullish_score + bearish_score + neutral_score
        if total == 0:
            return None

        # Determine overall direction
        if bullish_score > bearish_score * 1.5:
            direction = "Bullish"
            confidence = (bullish_score / total) * 100
        elif bearish_score > bullish_score * 1.5:
            direction = "Bearish"
            confidence = (bearish_score / total) * 100
        else:
            direction = "Neutral"
            confidence = max((neutral_score / total) * 100, 50)

        # Key drivers (top 5 by strength)
        key_drivers = sorted(incoming_influences, key=lambda x: x['strength'], reverse=True)[:5]

        return {
            'target': target_node,
            'direction': direction,
            'confidence': round(confidence, 1),
            'horizon_days': horizon_days,
            'bullish_factors': bullish_score,
            'bearish_factors': bearish_score,
            'neutral_factors': neutral_score,
            'key_drivers': key_drivers,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        st.warning(f"Forecast generation error: {str(e)}")
        return None

def _estimate_impact(rel_type: str, strength: float) -> int:
    """Estimate impact direction based on relationship type"""
    # Positive relationships
    if rel_type in ['SUPPORTS', 'STRENGTHENS', 'BOOSTS', 'IMPROVES', 'INCREASES']:
        return 1
    # Negative relationships
    elif rel_type in ['PRESSURES', 'WEAKENS', 'HURTS', 'DECREASES', 'THREATENS']:
        return -1
    # Neutral
    else:
        return 0

def _render_forecast_results(
    forecast: Dict[str, Any],
    target_display: str,
    horizon_days: int,
    show_details: bool
) -> None:
    """Render the forecast results"""
    direction = forecast.get('direction', 'Neutral')
    confidence = forecast.get('confidence', 50)

    # Color coding
    if direction == "Bullish":
        direction_color = "green"
        direction_emoji = "📈"
    elif direction == "Bearish":
        direction_color = "red"
        direction_emoji = "📉"
    else:
        direction_color = "orange"
        direction_emoji = "➡️"

    # Main forecast display
    st.markdown(f"### {direction_emoji} Forecast: :{direction_color}[{direction}]")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Direction", direction)

    with col2:
        st.metric("Confidence", f"{confidence:.1f}%")

    with col3:
        st.metric("Horizon", f"{horizon_days} days")

    # Factor breakdown
    st.markdown("### 📊 Factor Analysis")

    bullish = forecast.get('bullish_factors', 0)
    bearish = forecast.get('bearish_factors', 0)
    neutral = forecast.get('neutral_factors', 0)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🟢 Bullish Factors", bullish)

    with col2:
        st.metric("🔴 Bearish Factors", bearish)

    with col3:
        st.metric("🟡 Neutral Factors", neutral)

    # Visualize factor balance
    if PLOTLY_AVAILABLE and (bullish + bearish + neutral) > 0:
        fig = go.Figure(data=[go.Pie(
            labels=['Bullish', 'Bearish', 'Neutral'],
            values=[bullish, bearish, neutral],
            marker=dict(colors=['green', 'red', 'orange']),
            hole=0.3
        )])
        fig.update_layout(
            title="Factor Distribution",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, width="stretch")

    # Key drivers
    key_drivers = forecast.get('key_drivers', [])
    if key_drivers and show_details:
        st.markdown("### 🔑 Key Drivers")

        for idx, driver in enumerate(key_drivers, 1):
            from_node = get_node_display_name(driver.get('from', '?'))
            rel_type = driver.get('type', 'RELATED')
            strength = driver.get('strength', 0)
            impact = driver.get('impact', 0)

            # Impact emoji
            if impact > 0:
                impact_emoji = "🟢"
                impact_text = "Positive"
            elif impact < 0:
                impact_emoji = "🔴"
                impact_text = "Negative"
            else:
                impact_emoji = "🟡"
                impact_text = "Neutral"

            with st.expander(f"{idx}. {impact_emoji} {from_node} ({impact_text} Impact)", expanded=(idx == 1)):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Relationship**: {rel_type}")
                    st.markdown(f"**Strength**: {strength:.2f}")

                with col2:
                    st.markdown(f"**Impact**: {impact_text}")
                    strength_bar = "█" * int(strength * 10)
                    st.markdown(f"**Visual**: `{strength_bar}`")

    # Forecast timeline (simple projection)
    if show_details:
        st.markdown("### 📅 Forecast Timeline")
        _render_forecast_timeline(forecast, horizon_days)

    # Disclaimer
    st.markdown("---")
    st.info("⚠️ **Disclaimer**: This forecast is generated using AI and graph-based analysis. It should not be used as the sole basis for investment decisions. Always conduct your own research and consult with financial advisors.")

def _render_forecast_timeline(forecast: Dict[str, Any], horizon_days: int) -> None:
    """Render a simple forecast timeline"""
    direction = forecast.get('direction', 'Neutral')
    confidence = forecast.get('confidence', 50)

    # Generate milestone dates
    today = datetime.now()
    milestones = [
        (today, "Today", "Current State"),
        (today + timedelta(days=horizon_days // 3), "1/3 Horizon", f"Early {direction.lower()} signals"),
        (today + timedelta(days=2 * horizon_days // 3), "2/3 Horizon", f"{direction} trend developing"),
        (today + timedelta(days=horizon_days), "Target Date", f"Forecasted {direction.lower()} outcome")
    ]

    for date, label, description in milestones:
        col1, col2, col3 = st.columns([1, 2, 3])
        with col1:
            st.markdown(f"**{label}**")
        with col2:
            st.markdown(f"`{date.strftime('%Y-%m-%d')}`")
        with col3:
            st.markdown(description)
