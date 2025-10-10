"""Economic Dashboard - Trinity 3.0 GDP Refresh Flow UI

Displays real-time economic indicators using FRED data with:
- Multi-indicator comparison charts
- Economic regime detection
- Cycle phase analysis
- Sector recommendations
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
# from ui.utils.common import get_agent_safely  # No longer needed - using capability routing


def render_economic_dashboard(runtime, capabilities: Dict):
    """
    Render comprehensive economic dashboard using Trinity 3.0 architecture.

    Args:
        runtime: AgentRuntime instance for capability routing
        capabilities: Dict with 'fred' capability
    """
    st.title("📊 Economic Indicators Comparison")
    st.markdown("Compare Unemployment Rate, Fed Rate, CPI trends, and GDP growth over 24 months")

    # Check if FRED capability is available
    if 'fred' not in capabilities:
        st.error("⚠️ FRED capability not configured. Set FRED_API_KEY environment variable.")
        st.info("The dashboard will work with cached data if available.")

    # Fetch button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        refresh = st.button("🔄 Fetch Latest Data", type="primary")
    with col2:
        time_range = st.selectbox("Time Range", ["6 months", "12 months", "24 months", "5 years"], index=2)

    # Calculate date range
    end_date = datetime.now()
    if time_range == "6 months":
        start_date = end_date - timedelta(days=180)
    elif time_range == "12 months":
        start_date = end_date - timedelta(days=365)
    elif time_range == "24 months":
        start_date = end_date - timedelta(days=730)
    else:  # 5 years
        start_date = end_date - timedelta(days=1825)

    # Fetch economic data
    with st.spinner("Fetching economic indicators from FRED..."):
        try:
            # Use Trinity-compliant capability routing
            fred_result = runtime.execute_by_capability(
                'can_fetch_economic_data',
                {
                    'indicators': ['GDP', 'CPIAUCSL', 'UNRATE', 'DFF'],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
            )

            if fred_result and 'error' not in fred_result:

                # Display data source indicator
                source = fred_result.get('source', 'unknown')
                cache_age = fred_result.get('cache_age_seconds', 0)

                if source == 'live':
                    st.success(f"✅ Live data from FRED API")
                elif source == 'cache':
                    st.info(f"📦 Cached data ({cache_age // 60} minutes old)")
                elif source == 'fallback':
                    st.warning(f"⚠️ Using stale cached data ({cache_age // 86400} days old) - API unavailable")

                # Extract series data
                series = fred_result.get('series', {})
                gdp_data = series.get('GDP', {})
                cpi_data = series.get('CPIAUCSL', {})
                unemployment_data = series.get('UNRATE', {})
                fed_funds_data = series.get('DFF', {})

                # Create the multi-indicator chart
                render_economic_indicators_chart(
                    gdp_data, cpi_data, unemployment_data, fed_funds_data
                )

                # Get macro analysis
                st.markdown("---")
                st.subheader("🎯 Economic Analysis")

                # Use Trinity-compliant capability routing with pre-fetched data
                analysis = runtime.execute_by_capability(
                    'can_analyze_economy',
                    {
                        'gdp_data': gdp_data,
                        'cpi_data': cpi_data,
                        'unemployment_data': unemployment_data,
                        'fed_funds_data': fed_funds_data
                    }
                )

                if analysis and 'error' not in analysis:
                    render_macro_analysis(analysis)
                else:
                    error_msg = analysis.get('error', 'Unknown error') if analysis else 'No result'
                    st.error(f"❌ Analysis error: {error_msg}")
                    st.info("Economic analysis capability may not be available. Check agent registration.")

                # Display daily events section
                st.markdown("---")
                render_daily_events()

            else:
                # Handle capability routing error
                error_msg = fred_result.get('error', 'Unknown error') if fred_result else 'No result returned'
                st.error(f"❌ Failed to fetch economic data: {error_msg}")
                st.info("Economic data fetching capability may not be available. Check agent registration.")

        except Exception as e:
            st.error(f"Error fetching economic data: {e}")
            import traceback
            st.code(traceback.format_exc())


def render_economic_indicators_chart(
    gdp_data: Dict,
    cpi_data: Dict,
    unemployment_data: Dict,
    fed_funds_data: Dict
):
    """Render the main economic indicators comparison chart."""

    # Extract observations
    gdp_obs = gdp_data.get('observations', [])
    cpi_obs = cpi_data.get('observations', [])
    unemp_obs = unemployment_data.get('observations', [])
    fed_obs = fed_funds_data.get('observations', [])

    # Calculate CPI % change from baseline (first value)
    cpi_baseline = cpi_obs[0]['value'] if cpi_obs else 100
    cpi_pct_change = [
        ((obs['value'] - cpi_baseline) / cpi_baseline) * 100
        for obs in cpi_obs
    ]

    # Calculate GDP QoQ % for each point
    gdp_qoq = []
    for i, obs in enumerate(gdp_obs):
        if i == 0:
            gdp_qoq.append(None)
        else:
            prev_val = gdp_obs[i-1]['value']
            curr_val = obs['value']
            qoq = ((curr_val - prev_val) / prev_val) * 100 if prev_val != 0 else 0
            gdp_qoq.append(qoq)

    # Create figure with secondary y-axis
    fig = go.Figure()

    # Unemployment Rate (left y-axis)
    fig.add_trace(go.Scatter(
        x=[obs['date'] for obs in unemp_obs],
        y=[obs['value'] for obs in unemp_obs],
        name='Unemployment Rate (%)',
        line=dict(color='#ff6b6b', width=2),
        yaxis='y',
        hovertemplate='%{x}<br>Unemployment: %{y:.1f}%<extra></extra>'
    ))

    # Fed Funds Rate (left y-axis)
    fig.add_trace(go.Scatter(
        x=[obs['date'] for obs in fed_obs],
        y=[obs['value'] for obs in fed_obs],
        name='Fed Funds Rate (%)',
        line=dict(color='#4ecdc4', width=2),
        yaxis='y',
        hovertemplate='%{x}<br>Fed Funds: %{y:.2f}%<extra></extra>'
    ))

    # CPI % Change (right y-axis)
    fig.add_trace(go.Scatter(
        x=[obs['date'] for obs in cpi_obs],
        y=cpi_pct_change,
        name='CPI % Change (from baseline)',
        line=dict(color='#95e1d3', width=2),
        yaxis='y2',
        hovertemplate='%{x}<br>CPI Change: %{y:.1f}%<extra></extra>'
    ))

    # GDP Growth QoQ (right y-axis) - dashed line
    fig.add_trace(go.Scatter(
        x=[obs['date'] for obs in gdp_obs],
        y=gdp_qoq,
        name='GDP Growth QoQ (%)',
        line=dict(color='#a29bfe', width=2, dash='dash'),
        yaxis='y2',
        hovertemplate='%{x}<br>GDP QoQ: %{y:.1f}%<extra></extra>',
        # Add text annotations for specific points
        mode='lines+markers+text',
        marker=dict(size=4),
        text=[f'{val:.1f}%' if val and i % 3 == 0 else '' for i, val in enumerate(gdp_qoq)],
        textposition='top center',
        textfont=dict(size=9)
    ))

    # Update layout
    fig.update_layout(
        title="Economic Indicators: Unemployment, Fed Rate, CPI, and GDP Growth",
        xaxis=dict(
            title="Month",
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            title="Rate (%)",
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            side='left'
        ),
        yaxis2=dict(
            title="CPI % Change",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        hovermode='x unified',
        template='plotly_dark',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=60, t=80, b=60)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_macro_analysis(analysis: Dict):
    """Render macro economic analysis results."""

    # Main metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        gdp_qoq = analysis.get('gdp_qoq')
        if gdp_qoq is not None:
            delta_color = "normal" if gdp_qoq > 0 else "inverse"
            st.metric(
                "GDP Growth (QoQ)",
                f"{gdp_qoq:.1f}%",
                delta=f"{gdp_qoq:.1f}%",
                delta_color=delta_color
            )
        else:
            st.metric("GDP Growth (QoQ)", "N/A")

    with col2:
        cpi_yoy = analysis.get('cpi_yoy')
        if cpi_yoy is not None:
            delta_color = "inverse" if cpi_yoy > 3.0 else "normal"
            st.metric(
                "CPI Inflation (YoY)",
                f"{cpi_yoy:.1f}%",
                delta=f"{cpi_yoy:.1f}%",
                delta_color=delta_color
            )
        else:
            st.metric("CPI Inflation (YoY)", "N/A")

    with col3:
        cycle_phase = analysis.get('cycle_phase', 'unknown')
        phase_emoji = {
            'expansion': '📈',
            'peak': '⚠️',
            'contraction': '📉',
            'trough': '🔄',
            'transitional': '🔀'
        }.get(cycle_phase, '❓')
        st.metric("Cycle Phase", f"{phase_emoji} {cycle_phase.title()}")

    with col4:
        regime = analysis.get('regime', 'unknown')
        regime_emoji = {
            'goldilocks': '🌟',
            'stagflation': '⚠️',
            'recession': '📉',
            'overheating': '🔥',
            'transitional': '🔀'
        }.get(regime, '❓')
        st.metric("Economic Regime", f"{regime_emoji} {regime.title()}")

    # Detailed analysis
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⚠️ Macro Risks")
        risks = analysis.get('macro_risks', [])
        if risks:
            for risk in risks:
                st.markdown(f"- {risk}")
        else:
            st.success("No significant macro risks identified")

    with col2:
        st.markdown("### 💡 Sector Opportunities")
        opportunities = analysis.get('opportunities', [])
        if opportunities:
            for opp in opportunities:
                st.markdown(f"- {opp}")
        else:
            st.info("Diversification recommended")

    # Indicator details (expandable)
    with st.expander("📊 Detailed Indicator Data"):
        indicators = analysis.get('indicators', {})

        cols = st.columns(4)

        # GDP
        with cols[0]:
            st.markdown("**GDP**")
            gdp = indicators.get('gdp', {})
            st.write(f"Latest: ${gdp.get('latest', 'N/A'):,.0f}B" if gdp.get('latest') else "Latest: N/A")
            st.write(f"Date: {gdp.get('date', 'N/A')}")
            st.write(f"QoQ: {gdp.get('qoq_growth', 0):.1f}%")

        # CPI
        with cols[1]:
            st.markdown("**CPI**")
            cpi = indicators.get('cpi', {})
            st.write(f"Latest: {cpi.get('latest', 'N/A'):.1f}" if cpi.get('latest') else "Latest: N/A")
            st.write(f"Date: {cpi.get('date', 'N/A')}")
            st.write(f"YoY: {cpi.get('yoy_change', 0):.1f}%")

        # Unemployment
        with cols[2]:
            st.markdown("**Unemployment**")
            unemp = indicators.get('unemployment', {})
            st.write(f"Latest: {unemp.get('latest', 'N/A'):.1f}%" if unemp.get('latest') else "Latest: N/A")
            st.write(f"Date: {unemp.get('date', 'N/A')}")

        # Fed Funds
        with cols[3]:
            st.markdown("**Fed Funds Rate**")
            fed = indicators.get('fed_funds', {})
            st.write(f"Latest: {fed.get('latest', 'N/A'):.2f}%" if fed.get('latest') else "Latest: N/A")
            st.write(f"Date: {fed.get('date', 'N/A')}")

    # Metadata
    metadata = analysis.get('_metadata', {})
    if metadata.get('source') == 'fallback':
        st.warning(f"⚠️ Data is {metadata.get('cache_age_seconds', 0) // 86400} days old - FRED API unavailable")


# analyze_macro_data_directly() removed - was a workaround for broken capability routing
# Now using proper Trinity-compliant runtime.execute_by_capability() instead


def render_daily_events():
    """Render daily events calendar with economic data releases and policy events."""
    st.subheader("📅 Economic Events Calendar")
    st.markdown("Upcoming economic data releases and policy events")

    # Load economic calendar from KnowledgeLoader
    from core.knowledge_loader import get_knowledge_loader
    loader = get_knowledge_loader()
    calendar_data = loader.get_dataset('economic_calendar')

    if not calendar_data or 'events' not in calendar_data:
        st.warning("Economic calendar data not available")
        return

    # Filter controls
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        days_ahead = st.selectbox("Time window:", [7, 14, 30, 60, 90], index=2, key="events_days")

    with col2:
        importance_filter = st.multiselect(
            "Importance:",
            ["critical", "high", "medium"],
            default=["critical", "high"],
            key="events_importance"
        )

    with col3:
        type_filter = st.multiselect(
            "Event type:",
            ["policy", "data_release"],
            default=["policy", "data_release"],
            key="events_type"
        )

    # Filter events
    from datetime import datetime, timedelta
    today = datetime.now().date()
    end_date = today + timedelta(days=days_ahead)

    filtered_events = []
    for event in calendar_data['events']:
        event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
        if (today <= event_date <= end_date and
            event['importance'] in importance_filter and
            event['type'] in type_filter):
            filtered_events.append(event)

    # Sort by date
    filtered_events.sort(key=lambda x: x['date'])

    # Display events
    if not filtered_events:
        st.info(f"No events in the next {days_ahead} days matching your filters")
        return

    st.markdown(f"**{len(filtered_events)} upcoming events**")
    st.markdown("---")

    # Group events by week
    current_week = None
    for event in filtered_events:
        event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
        week_start = event_date - timedelta(days=event_date.weekday())

        # Week header
        if current_week != week_start:
            current_week = week_start
            week_end = week_start + timedelta(days=6)
            st.markdown(f"### Week of {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}")

        # Event card
        col_date, col_event = st.columns([1, 4])

        with col_date:
            # Date badge with importance color
            importance_colors = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡'
            }
            icon = importance_colors.get(event['importance'], '⚪')
            st.markdown(f"**{icon} {event_date.strftime('%b %d')}**")
            st.caption(event_date.strftime('%A'))

        with col_event:
            # Event details
            type_badges = {
                'policy': '🏛️ Policy',
                'data_release': '📊 Data'
            }
            type_badge = type_badges.get(event['type'], event['type'])

            st.markdown(f"**{event['event']}** {type_badge}")
            st.caption(f"{event['agency']} • {event['description']}")

            if event.get('indicator'):
                st.caption(f"Indicator: {event['indicator']}")

        st.markdown("---")
