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

    # Initialize economic data cache in session state
    if 'economic_data' not in st.session_state:
        st.session_state.economic_data = None
        st.session_state.economic_data_timestamp = None

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

    # Auto-fetch on first load or when refresh button clicked
    should_fetch = (
        st.session_state.economic_data is None or  # First load
        refresh or  # Manual refresh
        (st.session_state.economic_data_timestamp and
         (datetime.now() - st.session_state.economic_data_timestamp).total_seconds() > 3600)  # Data older than 1 hour
    )

    # Fetch economic data
    if should_fetch:
        with st.spinner("Fetching economic indicators from FRED..."):
            try:
                # Use Trinity-compliant capability routing
                fred_result = runtime.execute_by_capability(
                'can_fetch_economic_data',
                {
                    'capability': 'can_fetch_economic_data',  # CRITICAL: Required for AgentAdapter introspection
                    'indicators': ['GDP', 'CPIAUCSL', 'UNRATE', 'DFF'],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
                )

                # Cache the result
                st.session_state.economic_data = fred_result
                st.session_state.economic_data_timestamp = datetime.now()

            except Exception as e:
                st.error(f"❌ Error fetching economic data: {str(e)}")
                st.session_state.economic_data = None

    # Use cached data for display
    fred_result = st.session_state.economic_data

    if fred_result and 'error' not in fred_result:
        try:
            # Display data source indicator
            source = fred_result.get('source', 'unknown')
            cache_age = fred_result.get('cache_age_seconds', 0)
            data_timestamp = st.session_state.economic_data_timestamp

            col_status1, col_status2 = st.columns([3, 1])
            with col_status1:
                if source == 'live':
                    st.success(f"✅ Live data from FRED API")
                elif source == 'cache':
                    st.info(f"📦 Cached data ({cache_age // 60} minutes old)")
                elif source == 'fallback':
                    st.warning(f"⚠️ Using stale cached data ({cache_age // 86400} days old) - API unavailable")

            with col_status2:
                if data_timestamp:
                    age_seconds = (datetime.now() - data_timestamp).total_seconds()
                    if age_seconds < 60:
                        st.caption(f"📍 {int(age_seconds)}s ago")
                    elif age_seconds < 3600:
                        st.caption(f"📍 {int(age_seconds/60)}m ago")
                    else:
                        st.caption(f"📍 {int(age_seconds/3600)}h ago")

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
                'can_analyze_macro_data',
                {
                    'capability': 'can_analyze_macro_data',  # CRITICAL: Required for AgentAdapter introspection
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

            # Fetch and display systemic risk analysis
            st.markdown("---")
            
            # Initialize systemic data cache
            if 'systemic_data' not in st.session_state:
                st.session_state.systemic_data = None
                st.session_state.systemic_data_timestamp = None
            
            # Auto-fetch systemic data (if not cached or stale)
            should_fetch_systemic = (
                st.session_state.systemic_data is None or
                refresh or
                (st.session_state.systemic_data_timestamp and
                 (datetime.now() - st.session_state.systemic_data_timestamp).total_seconds() > 3600)
            )
            
            if should_fetch_systemic:
                with st.spinner("Fetching systemic risk indicators..."):
                    try:
                        # Fetch systemic FRED series
                        systemic_result = runtime.execute_by_capability(
                            'can_fetch_economic_data',
                            {
                                'capability': 'can_fetch_economic_data',
                                'indicators': ['GFDEGDQ188S', 'SIPOVGINIUSA', 'HDTGPDUSQ163N', 'TDSP', 'DRCCLACBS', 'EPUSOVDEBT'],
                                'start_date': start_date.strftime('%Y-%m-%d'),
                                'end_date': end_date.strftime('%Y-%m-%d')
                            }
                        )
                        
                        if systemic_result and 'error' not in systemic_result:
                            # Call systemic risk analysis capability
                            systemic_analysis = runtime.execute_by_capability(
                                'can_analyze_systemic_risk',
                                {
                                    'capability': 'can_analyze_systemic_risk',
                                    'gdp_data': gdp_data,
                                    'cpi_data': cpi_data,
                                    'unemployment_data': unemployment_data,
                                    'fed_funds_data': fed_funds_data,
                                    'systemic_data': systemic_result.get('series', {}),
                                    'start_date': start_date.strftime('%Y-%m-%d'),
                                    'end_date': end_date.strftime('%Y-%m-%d')
                                }
                            )
                            
                            st.session_state.systemic_data = systemic_analysis
                            st.session_state.systemic_data_timestamp = datetime.now()
                        else:
                            st.session_state.systemic_data = None
                    
                    except Exception as e:
                        st.session_state.systemic_data = None
            
            # Render systemic risk panel with cached data
            systemic_data = st.session_state.systemic_data
            if systemic_data and 'error' not in systemic_data:
                render_systemic_risk_panel(systemic_data)
            else:
                # Show placeholder when systemic data not available
                render_systemic_risk_panel(None)

            # Display daily events section
            st.markdown("---")
            render_daily_events()

        except Exception as e:
            st.error(f"❌ Error rendering economic dashboard: {str(e)}")
            import traceback
            with st.expander("View error details"):
                st.code(traceback.format_exc())
    else:
        # No data available
        st.warning("📊 No economic data available yet")
        st.info("Data will load automatically on first visit or click '🔄 Fetch Latest Data' to refresh")


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

    st.plotly_chart(fig, width="stretch")


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


def render_systemic_risk_panel(systemic_analysis: Optional[Dict]):
    """
    Render systemic risk analysis panel with visual gauges.
    
    Displays credit cycle, empire cycle, and systemic risk metrics with
    interactive Plotly gauges and phase indicators.
    
    Args:
        systemic_analysis: Dict containing systemic_analysis from deep macro analysis
    """
    st.subheader("⚠️ Systemic Risk Analysis")
    st.markdown("Long-term structural risk assessment using Ray Dalio's Big Debt Cycle framework")
    
    if not systemic_analysis or 'systemic_analysis' not in systemic_analysis:
        st.info("💡 Enable systemic risk analysis by fetching deep macro data")
        st.caption("Systemic analysis includes credit cycles, empire cycles, and long-term risk scoring")
        return
    
    systemic = systemic_analysis['systemic_analysis']
    
    # Top row: Main risk score and confidence adjustment
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Systemic Risk Score Gauge (0-100)
        if 'systemic_risk' in systemic:
            risk_data = systemic['systemic_risk']
            risk_score = risk_data.get('systemic_risk_score', 0)
            risk_level = risk_data.get('risk_level', 'Unknown')
            
            # Color coding based on risk level
            if risk_score < 30:
                gauge_color = '#00cc88'  # Green
            elif risk_score < 50:
                gauge_color = '#ffd700'  # Yellow
            elif risk_score < 70:
                gauge_color = '#ff8c00'  # Orange
            else:
                gauge_color = '#ff4444'  # Red
            
            # Create gauge chart
            fig_risk = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=risk_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Systemic Risk Score<br><span style='font-size:0.8em'>{risk_level}</span>", 'font': {'size': 20}},
                delta={'reference': 50, 'increasing': {'color': "#ff4444"}, 'decreasing': {'color': "#00cc88"}},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': gauge_color},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "white",
                    'steps': [
                        {'range': [0, 30], 'color': 'rgba(0, 204, 136, 0.3)'},
                        {'range': [30, 50], 'color': 'rgba(255, 215, 0, 0.3)'},
                        {'range': [50, 70], 'color': 'rgba(255, 140, 0, 0.3)'},
                        {'range': [70, 100], 'color': 'rgba(255, 68, 68, 0.3)'}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': risk_score
                    }
                }
            ))
            
            fig_risk.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "white", 'family': "Arial"},
                height=300,
                margin=dict(l=20, r=20, t=60, b=20)
            )
            
            st.plotly_chart(fig_risk, use_container_width=True)
    
    with col2:
        # Forecast Confidence Adjustment
        if 'forecast_confidence' in systemic_analysis:
            conf = systemic_analysis['forecast_confidence']
            base_conf = conf.get('base_confidence', 'N/A')
            adj_conf = conf.get('adjusted_confidence', 'N/A')
            change_pct = conf.get('change_percent', 0)
            
            st.metric(
                "Forecast Confidence",
                adj_conf,
                delta=f"{change_pct:+.1f}%",
                delta_color="inverse" if change_pct < 0 else "normal",
                help="Base confidence adjusted by systemic risk factors"
            )
            
            st.caption(f"Base: {base_conf}")
            
            # Adjustment explanation
            explanation = conf.get('explanation', '')
            if explanation:
                with st.expander("ℹ️ Why adjusted?"):
                    st.caption(explanation)
    
    st.markdown("---")
    
    # Second row: Credit Cycle and Empire Cycle
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💳 Credit Cycle")
        
        if 'credit_cycle' in systemic:
            cc = systemic['credit_cycle']
            cycle_phase = cc.get('cycle_phase', 'Unknown')
            stress_level = cc.get('stress_level', 'Unknown')
            
            # Phase indicator with color coding
            phase_colors = {
                'expansion': '🟢',
                'peak': '🟡',
                'contraction': '🔴',
                'trough': '🔵'
            }
            phase_icon = phase_colors.get(cycle_phase.lower(), '⚪')
            
            st.markdown(f"**Phase:** {phase_icon} {cycle_phase.title()}")
            st.markdown(f"**Stress Level:** {stress_level}")
            
            # Debt metrics
            if 'debt_metrics' in cc:
                dm = cc['debt_metrics']
                
                # Mini gauge for Debt/GDP
                debt_gdp = dm.get('federal_debt_gdp', 0)
                
                st.markdown("**Key Metrics:**")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Fed Debt/GDP", f"{debt_gdp:.1f}%")
                    household_debt = dm.get('household_debt_gdp', 0)
                    st.metric("HH Debt/GDP", f"{household_debt:.1f}%")
                with col_b:
                    delinquency = dm.get('credit_delinquency', 0)
                    st.metric("CC Delinquency", f"{delinquency:.2f}%")
                    debt_service = dm.get('debt_service_ratio', 0)
                    st.metric("Debt Service", f"{debt_service:.1f}%")
            
            # Risks
            risks = cc.get('risks', [])
            if risks:
                with st.expander("⚠️ Credit Cycle Risks"):
                    for risk in risks:
                        st.markdown(f"- {risk}")
    
    with col2:
        st.markdown("### 🏛️ Empire Cycle")
        
        if 'empire_cycle' in systemic:
            ec = systemic['empire_cycle']
            empire_stage = ec.get('empire_stage', 'Unknown')
            structural_risk = ec.get('structural_risk', 'Unknown')
            long_term_outlook = ec.get('long_term_outlook', 'N/A')
            
            # Stage indicator with color coding
            stage_colors = {
                'rising empire': '🟢',
                'peak empire': '🟡',
                'declining empire': '🟠',
                'crisis': '🔴'
            }
            stage_icon = stage_colors.get(empire_stage.lower(), '⚪')
            
            st.markdown(f"**Stage:** {stage_icon} {empire_stage.title()}")
            st.markdown(f"**Structural Risk:** {structural_risk}")
            st.markdown(f"**Long-term Outlook:** {long_term_outlook}")
            
            # Dalio Framework Proxies
            if 'dalio_proxies' in ec:
                proxies = ec['dalio_proxies']
                
                st.markdown("**Ray Dalio Indicators:**")
                col_a, col_b = st.columns(2)
                with col_a:
                    debt_burden = proxies.get('debt_burden', 0)
                    st.metric("Debt Burden", f"{debt_burden:.1f}% GDP")
                    inequality = proxies.get('inequality', 0)
                    st.metric("Gini Index", f"{inequality:.3f}")
                with col_b:
                    currency_stress = proxies.get('currency_stress', 0)
                    st.metric("Sovereign Stress", f"{currency_stress:.0f}")
            
            # Risk factors
            risk_factors = ec.get('risk_factors', [])
            if risk_factors:
                with st.expander("⚠️ Structural Risk Factors"):
                    for factor in risk_factors:
                        st.markdown(f"- {factor}")
    
    # Bottom row: Component scores and interpretation guide
    st.markdown("---")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📊 Risk Score Components")
        
        if 'systemic_risk' in systemic and 'components' in systemic['systemic_risk']:
            components = systemic['systemic_risk']['components']
            
            # Create horizontal bar chart for components
            component_data = {
                'Credit Cycle': components.get('credit_cycle_score', 0),
                'Empire Cycle': components.get('empire_cycle_score', 0),
                'Amplifier': components.get('amplifier', 0)
            }
            
            fig_components = go.Figure()
            
            colors = ['#4ecdc4', '#a29bfe', '#ff6b6b']
            for i, (label, value) in enumerate(component_data.items()):
                fig_components.add_trace(go.Bar(
                    y=[label],
                    x=[value],
                    orientation='h',
                    marker_color=colors[i],
                    text=f"{value:.1f}",
                    textposition='auto',
                    name=label,
                    hovertemplate=f'{label}: {value:.1f}<extra></extra>'
                ))
            
            fig_components.update_layout(
                showlegend=False,
                xaxis=dict(title="Score", range=[0, max(50, max(component_data.values()) + 10)]),
                yaxis=dict(title=""),
                height=200,
                margin=dict(l=10, r=10, t=10, b=40),
                template='plotly_dark',
                hovermode='y unified'
            )
            
            st.plotly_chart(fig_components, use_container_width=True)
    
    with col2:
        st.markdown("### 📖 Interpretation Guide")
        
        st.markdown("""
        **Risk Score Ranges:**
        - 🟢 **0-30**: Low risk
        - 🟡 **31-50**: Moderate risk
        - 🟠 **51-70**: Elevated risk
        - 🔴 **71-100**: High risk (crisis likely)
        
        **Credit Cycle:**
        - Expansion: Healthy leverage
        - Peak: Elevated debt levels
        - Contraction: Deleveraging
        - Trough: Reset complete
        """)
    
    st.markdown("---")
    st.caption("📚 Framework: Ray Dalio's Big Debt Cycle Theory | Data: Federal Reserve Economic Data (FRED)")


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
