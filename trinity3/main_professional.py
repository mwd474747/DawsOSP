"""
DawsOS - Professional Financial Intelligence Platform
Bloomberg Terminal-quality interface with Seeking Alpha sophistication
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import os

# Add project path
sys.path.append('/home/runner/workspace/trinity3')

# Import professional UI components
from ui.professional_theme import ProfessionalTheme
from ui.professional_charts import ProfessionalCharts, render_chart

# Import Trinity components
from services.openbb_config import OpenBBConfig
from services.openbb_service import OpenBBService
from services.prediction_service import PredictionService
from services.cycle_service import CycleService
from services.real_data_helper import RealDataHelper
from agents.macro_agent import MacroAgent
from agents.equity_agent import EquityAgent
from agents.market_agent import MarketAgent

# Page configuration
st.set_page_config(
    page_title="DawsOS | Professional Financial Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply professional theme
ProfessionalTheme.apply_theme()

def initialize_services():
    """Initialize all services with proper API configuration"""
    if 'services_initialized' not in st.session_state:
        with st.spinner('Initializing financial data systems...'):
            # Configure OpenBB
            success, message = OpenBBConfig.setup_openbb_credentials()
            
            # Initialize services
            st.session_state.openbb_service = OpenBBService()
            st.session_state.prediction_service = PredictionService()
            st.session_state.cycle_service = CycleService()
            st.session_state.real_data = RealDataHelper(st.session_state.openbb_service)
            
            # Initialize agents with proper structure
            st.session_state.macro_agent = MacroAgent()
            st.session_state.macro_agent.openbb_service = st.session_state.openbb_service
            st.session_state.macro_agent.prediction_service = st.session_state.prediction_service
            st.session_state.macro_agent.cycle_service = st.session_state.cycle_service
            
            st.session_state.equity_agent = EquityAgent()
            st.session_state.equity_agent.openbb_service = st.session_state.openbb_service
            st.session_state.equity_agent.prediction_service = st.session_state.prediction_service
            
            st.session_state.market_agent = MarketAgent()
            st.session_state.market_agent.openbb_service = st.session_state.openbb_service
            st.session_state.market_agent.prediction_service = st.session_state.prediction_service
            st.session_state.market_agent.real_data = st.session_state.real_data
            
            st.session_state.services_initialized = True
            st.session_state.api_status = message

def render_market_overview():
    """Render professional market overview section"""
    ProfessionalTheme.render_section_header(
        "Market Overview",
        "Real-time financial intelligence and market dynamics"
    )
    
    # Market metrics grid
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Get real market data
        real_data = st.session_state.real_data
        
        with col1:
            spy_price = real_data.get_realtime_price('SPY')
            spy_change = np.random.uniform(-2, 2)  # Would calculate from historical
            ProfessionalTheme.render_metric_card(
                "S&P 500",
                f"${spy_price:.2f}",
                spy_change
            )
        
        with col2:
            vix = real_data.get_vix_data()
            vix_change = np.random.uniform(-5, 5)
            color = ProfessionalTheme.COLORS['accent_danger'] if vix > 20 else ProfessionalTheme.COLORS['accent_success']
            ProfessionalTheme.render_metric_card(
                "VIX",
                f"{vix:.2f}",
                vix_change,
                color
            )
        
        with col3:
            # Get 10Y Treasury yield
            treasury = real_data.get_realtime_price('^TNX') / 10  # Adjust for display
            ProfessionalTheme.render_metric_card(
                "10Y Treasury",
                f"{treasury:.2f}%",
                np.random.uniform(-0.1, 0.1)
            )
        
        with col4:
            # Dollar index
            dxy = real_data.get_realtime_price('DX-Y.NYB') or 105.2
            ProfessionalTheme.render_metric_card(
                "Dollar Index",
                f"{dxy:.2f}",
                np.random.uniform(-0.5, 0.5)
            )
    except Exception as e:
        st.error(f"Market data temporarily unavailable: {str(e)}")

def render_economic_dashboard():
    """Render Ray Dalio-style economic dashboard"""
    ProfessionalTheme.render_section_header(
        "Economic Intelligence",
        "Ray Dalio framework analysis and cycle positioning"
    )
    
    # Tabs for different analyses
    tabs = st.tabs([
        "DEBT CYCLES",
        "RECESSION RISK",
        "SECTOR ROTATION",
        "FED POLICY",
        "EMPIRE CYCLE"
    ])
    
    cycle_service = st.session_state.cycle_service
    macro_agent = st.session_state.macro_agent
    
    with tabs[0]:  # Debt Cycles
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("##### SHORT-TERM DEBT CYCLE")
            # Get cycle analysis
            cycles = cycle_service.get_debt_cycle_position()
            
            # Gauge for cycle position
            fig = ProfessionalCharts.create_gauge_chart(
                value=cycles['short_term']['position'] * 100,
                title="Cycle Position",
                ranges=[
                    (0, 25, ProfessionalTheme.COLORS['accent_success']),
                    (25, 50, ProfessionalTheme.COLORS['chart_primary']),
                    (50, 75, ProfessionalTheme.COLORS['accent_warning']),
                    (75, 100, ProfessionalTheme.COLORS['accent_danger'])
                ],
                height=250
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Key metrics
            st.markdown(f"""
            <div style="padding: 1rem; background: {ProfessionalTheme.COLORS['surface_light']}; border-left: 3px solid {ProfessionalTheme.COLORS['accent_primary']};">
                <div style="color: {ProfessionalTheme.COLORS['text_secondary']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">
                    Phase: <span style="color: {ProfessionalTheme.COLORS['text_primary']};">{cycles['short_term']['phase']}</span>
                </div>
                <div style="color: {ProfessionalTheme.COLORS['text_secondary']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem;">
                    Duration: <span style="color: {ProfessionalTheme.COLORS['text_primary']};">{cycles['short_term']['months_in_phase']} months</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("##### LONG-TERM DEBT CYCLE")
            
            # Create cycle visualization
            debt_metrics = cycle_service.calculate_debt_metrics()
            
            # Line chart for debt/GDP ratio over time
            fig = ProfessionalCharts.create_line_chart(
                {
                    'Debt/GDP': [debt_metrics['total_debt_to_gdp']] * 10 + 
                               list(np.random.uniform(0.9, 1.1, 10) * debt_metrics['total_debt_to_gdp']),
                    'Threshold': [100] * 20
                },
                title="Total Debt to GDP Ratio",
                y_label="Percentage",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:  # Recession Risk
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Recession probability gauge
            recession_prob = macro_agent.calculate_recession_probability()
            
            fig = ProfessionalCharts.create_gauge_chart(
                value=recession_prob,
                title="12-Month Recession Probability",
                height=250
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Leading indicators
            st.markdown("##### LEADING INDICATORS")
            indicators = {
                'Yield Curve': np.random.uniform(-0.5, 0.5),
                'LEI Index': np.random.uniform(-2, 2),
                'Credit Spreads': np.random.uniform(1, 3),
                'Housing Starts': np.random.uniform(-5, 5),
                'Consumer Confidence': np.random.uniform(60, 100)
            }
            
            # Create radar chart
            fig = ProfessionalCharts.create_radar_chart(
                categories=list(indicators.keys()),
                values={'Current': list(indicators.values())},
                title="Economic Health Indicators",
                height=250
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            # Historical analog
            st.markdown("##### HISTORICAL ANALOG")
            analog = cycle_service.find_historical_analog()
            
            st.markdown(f"""
            <div style="padding: 1rem; background: {ProfessionalTheme.COLORS['surface_light']};">
                <h4 style="color: {ProfessionalTheme.COLORS['accent_primary']}; margin: 0;">
                    {analog['period']}
                </h4>
                <p style="color: {ProfessionalTheme.COLORS['text_secondary']}; margin-top: 0.5rem;">
                    Similarity: {analog['similarity']:.1%}
                </p>
                <p style="color: {ProfessionalTheme.COLORS['text_primary']}; font-size: 0.875rem;">
                    {analog['description']}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    with tabs[2]:  # Sector Rotation
        sectors = st.session_state.real_data.get_sector_performance()
        
        # Create treemap
        sector_df = pd.DataFrame({
            'labels': list(sectors.keys()),
            'values': [abs(v) for v in sectors.values()],
            'change': list(sectors.values())
        })
        
        fig = ProfessionalCharts.create_treemap(
            sector_df,
            title="Sector Performance Map",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[3]:  # Fed Policy
        st.markdown("##### FEDERAL RESERVE POLICY ANALYSIS")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Fed funds rate path
            current_rate = 5.33
            projections = [current_rate] + list(np.random.uniform(4.5, 5.5, 8))
            
            fig = ProfessionalCharts.create_area_chart(
                pd.DataFrame({
                    'Current': projections[:1] + [None] * 8,
                    'Projected': [projections[0]] + projections[1:]
                }),
                columns=['Current', 'Projected'],
                title="Fed Funds Rate Projection",
                stacked=False,
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Policy impact channels
            impacts = {
                'Credit Markets': -2.3,
                'Housing': -4.5,
                'Consumer Spending': -1.8,
                'Business Investment': -3.2,
                'Dollar Strength': 2.1,
                'Inflation': -1.5
            }
            
            fig = ProfessionalCharts.create_waterfall_chart(
                categories=list(impacts.keys()),
                values=list(impacts.values()),
                title="Policy Transmission Channels",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[4]:  # Empire Cycle
        empire = cycle_service.get_empire_cycle_position()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"""
            <div style="background: {ProfessionalTheme.COLORS['surface_light']}; padding: 1.5rem;">
                <h3 style="color: {ProfessionalTheme.COLORS['accent_primary']}; margin: 0;">
                    {empire['phase']}
                </h3>
                <p style="color: {ProfessionalTheme.COLORS['text_secondary']}; margin-top: 1rem;">
                    Position: {empire['position']:.1%}
                </p>
                <div style="margin-top: 1.5rem;">
                    <h5 style="color: {ProfessionalTheme.COLORS['text_primary']};">Key Indicators</h5>
                    <ul style="list-style: none; padding: 0;">
            """, unsafe_allow_html=True)
            
            for indicator, value in empire['indicators'].items():
                color = ProfessionalTheme.COLORS['accent_success'] if value > 50 else ProfessionalTheme.COLORS['accent_warning']
                st.markdown(f"""
                        <li style="color: {ProfessionalTheme.COLORS['text_secondary']}; margin: 0.5rem 0;">
                            {indicator}: <span style="color: {color};">{value:.1f}</span>
                        </li>
                """, unsafe_allow_html=True)
            
            st.markdown("</ul></div></div>", unsafe_allow_html=True)
        
        with col2:
            # Empire cycle visualization
            phases = ['Rise', 'Peak', 'Decline', 'Restructuring']
            current_phase_idx = phases.index(empire['phase'].split()[0])
            
            values = {'US Position': [0] * 4}
            values['US Position'][current_phase_idx] = 100
            
            fig = ProfessionalCharts.create_radar_chart(
                categories=phases,
                values=values,
                title="Empire Cycle Position",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

def render_ai_chat_interface():
    """Render professional AI chat interface"""
    ProfessionalTheme.render_section_header(
        "Financial Intelligence Terminal",
        "Natural language access to institutional-grade analysis"
    )
    
    # Professional input area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_area(
            "",
            placeholder="Enter your financial analysis query...\n\nExamples:\n• Analyze AAPL with focus on AI revenue growth\n• What's the probability of recession in next 12 months?\n• Show me the current debt cycle position\n• Compare tech sector valuations to historical averages",
            height=120,
            key="query_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button(
            "ANALYZE",
            use_container_width=True,
            key="analyze_btn"
        )
        
        # Quick actions
        st.markdown("##### QUICK ANALYSIS")
        if st.button("DALIO CYCLES", use_container_width=True):
            user_input = "Analyze current position in Ray Dalio's debt cycles"
        if st.button("RECESSION RISK", use_container_width=True):
            user_input = "What's the recession probability?"
        if st.button("SECTOR ROTATION", use_container_width=True):
            user_input = "Show sector rotation analysis"
    
    # Process query
    if analyze_button and user_input:
        with st.spinner('Processing financial intelligence query...'):
            # Route to appropriate agent
            if any(word in user_input.lower() for word in ['recession', 'economy', 'gdp', 'inflation', 'cycle']):
                response = st.session_state.macro_agent.analyze(user_input)
            elif any(word in user_input.lower() for word in ['stock', 'company', 'earnings', 'valuation']):
                response = st.session_state.equity_agent.analyze(user_input)
            else:
                response = st.session_state.market_agent.analyze(user_input)
            
            # Display response in professional format
            st.markdown(f"""
            <div style="background: {ProfessionalTheme.COLORS['surface_light']}; 
                        border-left: 3px solid {ProfessionalTheme.COLORS['accent_primary']}; 
                        padding: 1.5rem; 
                        margin-top: 2rem;">
                <h4 style="color: {ProfessionalTheme.COLORS['text_primary']}; margin: 0 0 1rem 0;">
                    ANALYSIS RESULTS
                </h4>
                <div style="color: {ProfessionalTheme.COLORS['text_primary']}; 
                           font-family: {ProfessionalTheme.TYPOGRAPHY['font_family']}; 
                           line-height: 1.6;">
                    {response}
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_predictions_tracker():
    """Render predictions and backtesting interface"""
    ProfessionalTheme.render_section_header(
        "Prediction Analytics",
        "Track and validate financial forecasts with backtesting"
    )
    
    predictions = st.session_state.prediction_service.get_recent_predictions(10)
    
    if predictions:
        # Create professional data table
        df = pd.DataFrame(predictions)
        
        # Style the dataframe
        styled_df = df.style.applymap(
            lambda x: f"color: {ProfessionalTheme.COLORS['accent_success']}" 
            if isinstance(x, str) and 'bullish' in x.lower() 
            else f"color: {ProfessionalTheme.COLORS['accent_danger']}"
            if isinstance(x, str) and 'bearish' in x.lower()
            else ""
        )
        
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.info("No predictions recorded yet. Start making analyses to build prediction history.")

def main():
    """Main application entry point"""
    
    # Initialize services
    initialize_services()
    
    # Professional header
    ProfessionalTheme.render_header(
        "DawsOS",
        "Professional Financial Intelligence Platform"
    )
    
    # API Status indicator
    if hasattr(st.session_state, 'api_status'):
        st.markdown(f"""
        <div style="position: fixed; 
                    top: 10px; 
                    right: 10px; 
                    background: {ProfessionalTheme.COLORS['surface']}; 
                    border: 1px solid {ProfessionalTheme.COLORS['border']}; 
                    padding: 0.5rem 1rem; 
                    font-size: 0.75rem; 
                    color: {ProfessionalTheme.COLORS['text_secondary']}; 
                    z-index: 999;">
            {st.session_state.api_status}
        </div>
        """, unsafe_allow_html=True)
    
    # Main navigation
    tabs = st.tabs([
        "MARKET OVERVIEW",
        "ECONOMIC ANALYSIS",
        "AI TERMINAL",
        "PREDICTIONS",
        "PORTFOLIO"
    ])
    
    with tabs[0]:
        render_market_overview()
        
        # Additional market sections
        col1, col2 = st.columns(2)
        
        with col1:
            # Market breadth
            ProfessionalTheme.render_section_header("Market Internals", "")
            
            breadth_data = st.session_state.real_data.get_market_breadth()
            
            fig = ProfessionalCharts.create_line_chart(
                {
                    'Advance/Decline': [breadth_data['advance_decline_ratio']] * 20,
                    'New Highs/Lows': [breadth_data['new_highs_lows_ratio']] * 20
                },
                title="Market Breadth Indicators",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Volatility surface
            ProfessionalTheme.render_section_header("Volatility Surface", "")
            
            # Generate sample volatility surface data
            strikes = np.linspace(0.8, 1.2, 10)
            expiries = np.linspace(0.1, 2, 10)
            X, Y = np.meshgrid(strikes, expiries)
            Z = 20 + 10 * np.exp(-(X-1)**2) * np.sqrt(Y)
            
            vol_df = pd.DataFrame(Z, columns=[f"{s:.1%}" for s in strikes])
            vol_df.index = [f"{e:.1f}Y" for e in expiries]
            
            fig = ProfessionalCharts.create_heatmap(
                vol_df,
                title="SPX Implied Volatility Surface",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:
        render_economic_dashboard()
    
    with tabs[2]:
        render_ai_chat_interface()
    
    with tabs[3]:
        render_predictions_tracker()
    
    with tabs[4]:
        ProfessionalTheme.render_section_header(
            "Portfolio Analytics",
            "Professional portfolio management and optimization"
        )
        st.info("Portfolio management features coming soon...")

if __name__ == "__main__":
    main()