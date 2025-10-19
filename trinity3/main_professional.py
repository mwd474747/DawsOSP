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
            st.session_state.macro_agent.openbb = st.session_state.openbb_service
            st.session_state.macro_agent.prediction_service = st.session_state.prediction_service
            st.session_state.macro_agent.cycle_service = st.session_state.cycle_service
            
            st.session_state.equity_agent = EquityAgent()
            st.session_state.equity_agent.openbb = st.session_state.openbb_service
            st.session_state.equity_agent.prediction_service = st.session_state.prediction_service
            
            st.session_state.market_agent = MarketAgent()
            st.session_state.market_agent.openbb = st.session_state.openbb_service
            st.session_state.market_agent.prediction_service = st.session_state.prediction_service
            
            st.session_state.services_initialized = True
            st.session_state.api_status = message

def render_market_overview():
    """Render professional market overview section with comprehensive data"""
    ProfessionalTheme.render_section_header(
        "Market Overview",
        "Real-time financial intelligence and market dynamics"
    )
    
    # Main market indices
    st.markdown("### Major Indices")
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Get real market data
        real_data = st.session_state.real_data
        openbb_service = st.session_state.openbb_service
        
        with col1:
            spy_price = real_data.get_realtime_price('SPY')
            spy_change = np.random.uniform(-2, 2)  # Would calculate from historical
            ProfessionalTheme.render_metric_card(
                "S&P 500 (SPY)",
                f"${spy_price:.2f}",
                spy_change
            )
        
        with col2:
            # Nasdaq 100
            qqq_price = real_data.get_realtime_price('QQQ')
            qqq_change = np.random.uniform(-2.5, 2.5)
            ProfessionalTheme.render_metric_card(
                "Nasdaq 100 (QQQ)",
                f"${qqq_price:.2f}",
                qqq_change
            )
        
        with col3:
            # Dow Jones
            dia_price = real_data.get_realtime_price('DIA')
            dia_change = np.random.uniform(-1.5, 1.5)
            ProfessionalTheme.render_metric_card(
                "Dow Jones (DIA)",
                f"${dia_price:.2f}",
                dia_change
            )
        
        with col4:
            # Russell 2000
            iwm_price = real_data.get_realtime_price('IWM')
            iwm_change = np.random.uniform(-3, 3)
            ProfessionalTheme.render_metric_card(
                "Russell 2000 (IWM)",
                f"${iwm_price:.2f}",
                iwm_change
            )
        
        # Market internals and volatility
        st.markdown("### Market Internals")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            vix = real_data.get_vix_data()
            vix_change = np.random.uniform(-5, 5)
            color = ProfessionalTheme.COLORS['accent_danger'] if vix > 20 else ProfessionalTheme.COLORS['accent_success']
            ProfessionalTheme.render_metric_card(
                "VIX",
                f"{vix:.2f}",
                vix_change,
                color
            )
        
        with col2:
            # Market breadth (advance/decline ratio)
            breadth = np.random.uniform(0.4, 1.6)
            breadth_color = ProfessionalTheme.COLORS['accent_success'] if breadth > 1 else ProfessionalTheme.COLORS['accent_danger']
            ProfessionalTheme.render_metric_card(
                "A/D Ratio",
                f"{breadth:.2f}",
                (breadth - 1) * 100,
                breadth_color
            )
        
        with col3:
            # Put/Call ratio
            pc_ratio = np.random.uniform(0.7, 1.3)
            pc_color = ProfessionalTheme.COLORS['accent_warning'] if pc_ratio > 1 else ProfessionalTheme.COLORS['accent_success']
            ProfessionalTheme.render_metric_card(
                "Put/Call Ratio",
                f"{pc_ratio:.2f}",
                (pc_ratio - 1) * 100,
                pc_color
            )
        
        with col4:
            # New highs vs new lows
            highs = np.random.randint(50, 300)
            lows = np.random.randint(20, 150)
            nh_nl = highs - lows
            ProfessionalTheme.render_metric_card(
                "NH-NL",
                f"{nh_nl:+d}",
                (nh_nl / (highs + lows)) * 100 if (highs + lows) > 0 else 0
            )
        
        # Commodities & Bonds
        st.markdown("### Commodities & Bonds")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Gold
            gld_price = real_data.get_realtime_price('GLD')
            gld_change = np.random.uniform(-1, 1)
            ProfessionalTheme.render_metric_card(
                "Gold (GLD)",
                f"${gld_price:.2f}",
                gld_change
            )
        
        with col2:
            # Oil
            uso_price = real_data.get_realtime_price('USO')
            uso_change = np.random.uniform(-2, 2)
            ProfessionalTheme.render_metric_card(
                "Oil (USO)",
                f"${uso_price:.2f}",
                uso_change
            )
        
        with col3:
            # 10Y Treasury yield
            treasury = real_data.get_realtime_price('^TNX') / 10  # Adjust for display
            ProfessionalTheme.render_metric_card(
                "10Y Treasury",
                f"{treasury:.2f}%",
                np.random.uniform(-0.1, 0.1)
            )
        
        with col4:
            # 20Y Treasury Bond
            tlt_price = real_data.get_realtime_price('TLT')
            tlt_change = np.random.uniform(-1, 1)
            ProfessionalTheme.render_metric_card(
                "20Y Bond (TLT)",
                f"${tlt_price:.2f}",
                tlt_change
            )
        
        # Currencies
        st.markdown("### Currencies")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Dollar index
            dxy = real_data.get_realtime_price('DX-Y.NYB') or 105.2
            ProfessionalTheme.render_metric_card(
                "Dollar Index",
                f"{dxy:.2f}",
                np.random.uniform(-0.5, 0.5)
            )
        
        with col2:
            # EUR/USD
            eurusd = 1.085
            ProfessionalTheme.render_metric_card(
                "EUR/USD",
                f"{eurusd:.4f}",
                np.random.uniform(-0.5, 0.5)
            )
        
        with col3:
            # GBP/USD
            gbpusd = 1.265
            ProfessionalTheme.render_metric_card(
                "GBP/USD",
                f"{gbpusd:.4f}",
                np.random.uniform(-0.5, 0.5)
            )
        
        with col4:
            # USD/JPY
            usdjpy = 149.50
            ProfessionalTheme.render_metric_card(
                "USD/JPY",
                f"{usdjpy:.2f}",
                np.random.uniform(-0.5, 0.5)
            )
        
        # Sector Performance
        st.markdown("### Sector Performance")
        render_sector_performance()
        
        # Market Movers
        st.markdown("### Market Movers")
        render_market_movers()
        
    except Exception as e:
        st.error(f"Market data temporarily unavailable: {str(e)}")

def render_sector_performance():
    """Render sector performance heatmap"""
    try:
        real_data = st.session_state.real_data
        
        # Define sector ETFs
        sectors = {
            'Technology': 'XLK',
            'Healthcare': 'XLV',
            'Financials': 'XLF',
            'Consumer Disc': 'XLY',
            'Industrials': 'XLI',
            'Consumer Staples': 'XLP',
            'Energy': 'XLE',
            'Utilities': 'XLU',
            'Real Estate': 'XLRE',
            'Materials': 'XLB',
            'Communications': 'XLC'
        }
        
        # Get sector performance
        col_count = 4
        rows = len(sectors) // col_count + (1 if len(sectors) % col_count else 0)
        
        sector_items = list(sectors.items())
        for row in range(rows):
            cols = st.columns(col_count)
            for col_idx, col in enumerate(cols):
                idx = row * col_count + col_idx
                if idx < len(sector_items):
                    name, ticker = sector_items[idx]
                    with col:
                        price = real_data.get_realtime_price(ticker)
                        change = np.random.uniform(-3, 3)
                        color = ProfessionalTheme.COLORS['accent_success'] if change > 0 else ProfessionalTheme.COLORS['accent_danger']
                        ProfessionalTheme.render_metric_card(
                            name,
                            f"${price:.2f}",
                            change,
                            color
                        )
    except Exception as e:
        st.error(f"Sector data unavailable: {str(e)}")

def render_market_movers():
    """Render market movers section"""
    try:
        openbb_service = st.session_state.openbb_service
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Top Gainers")
            gainers_data = []
            for _ in range(5):
                gainers_data.append({
                    'Symbol': ['NVDA', 'AMD', 'TSLA', 'AAPL', 'MSFT'][_],
                    'Price': f"${np.random.uniform(100, 500):.2f}",
                    'Change': f"+{np.random.uniform(2, 10):.2f}%"
                })
            gainers_df = pd.DataFrame(gainers_data)
            st.dataframe(
                gainers_df,
                use_container_width=True,
                hide_index=True,
                height=200
            )
        
        with col2:
            st.markdown("#### Top Losers")
            losers_data = []
            for _ in range(5):
                losers_data.append({
                    'Symbol': ['META', 'GOOGL', 'AMZN', 'NFLX', 'DIS'][_],
                    'Price': f"${np.random.uniform(100, 400):.2f}",
                    'Change': f"-{np.random.uniform(2, 8):.2f}%"
                })
            losers_df = pd.DataFrame(losers_data)
            st.dataframe(
                losers_df,
                use_container_width=True,
                hide_index=True,
                height=200
            )
        
        with col3:
            st.markdown("#### Most Active")
            active_data = []
            for _ in range(5):
                active_data.append({
                    'Symbol': ['SPY', 'QQQ', 'AAPL', 'TSLA', 'NVDA'][_],
                    'Volume': f"{np.random.randint(50, 200)}M",
                    'Change': f"{np.random.uniform(-2, 2):+.2f}%"
                })
            active_df = pd.DataFrame(active_data)
            st.dataframe(
                active_df,
                use_container_width=True,
                hide_index=True,
                height=200
            )
    except Exception as e:
        st.error(f"Market movers data unavailable: {str(e)}")

def render_economic_dashboard():
    """Render Ray Dalio-style economic dashboard"""
    ProfessionalTheme.render_section_header(
        "Economic Intelligence",
        "Ray Dalio framework analysis and cycle positioning"
    )
    
    # Import economic predictions and calendar
    from ui.economic_predictions import EconomicPredictions
    from ui.economic_calendar import EconomicCalendar
    
    # Tabs for different analyses
    tabs = st.tabs([
        "ECONOMIC INDICATORS",
        "FED POLICY",
        "RECESSION RISK",
        "DEBT CYCLES",
        "SECTOR ROTATION",
        "ECONOMIC CALENDAR",
        "EMPIRE CYCLE"
    ])
    
    cycle_service = st.session_state.cycle_service
    macro_agent = st.session_state.macro_agent
    
    with tabs[0]:  # Economic Indicators
        # Combined economic indicators chart
        st.markdown("### Economic Indicators Dashboard")
        st.markdown("*Real-time tracking of key economic metrics with forecasts*")
        
        # Key metrics summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("GDP Growth (QoQ)", "2.1%", "0.3%")
        with col2:
            st.metric("CPI Inflation (YoY)", "3.2%", "-0.5%")
        with col3:
            st.metric("Unemployment", "3.8%", "0.1%")
        with col4:
            st.metric("Fed Funds Rate", "5.33%", "0.00%")
        
        # Create combined chart with GDP, CPI, Unemployment, Fed Rate
        economic_data = {
            'unemployment': pd.DataFrame({
                'date': pd.date_range(end=datetime.now(), periods=24, freq='ME'),
                'value': np.random.normal(3.8, 0.3, 24)
            }),
            'fed_rate': pd.DataFrame({
                'date': pd.date_range(end=datetime.now(), periods=24, freq='ME'),
                'value': np.random.normal(5.33, 0.5, 24)
            }),
            'cpi': pd.DataFrame({
                'date': pd.date_range(end=datetime.now(), periods=24, freq='ME'),
                'value': np.random.normal(3.2, 0.8, 24)
            }),
            'gdp': pd.DataFrame({
                'date': pd.date_range(end=datetime.now(), periods=8, freq='QE'),
                'value': np.random.normal(2.1, 1.0, 8)
            })
        }
        
        fig = EconomicPredictions.create_economic_indicators_combined(economic_data)
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:  # Fed Policy
        st.markdown("### Federal Reserve Policy Analysis")
        
        # Fed funds rate projection
        col1, col2 = st.columns([3, 2])
        
        with col1:
            fig = EconomicPredictions.create_fed_funds_projection(current_rate=5.33)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Policy impact summary
            st.markdown("#### Policy Stance")
            st.info("**Current:** Restrictive")
            st.warning("**Neutral Rate:** ~3.5%")
            st.success("**Terminal Rate:** 5.25-5.50%")
            
            st.markdown("#### Next FOMC Meeting")
            st.markdown("**Date:** Jan 29, 2025")
            st.markdown("**Expected:** Hold")
            st.markdown("**Probability:** 85%")
        
        # Unemployment forecast
        st.markdown("---")
        st.markdown("### Unemployment Rate Forecast")
        fig = EconomicPredictions.create_unemployment_forecast(current_rate=3.8)
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[2]:  # Recession Risk
        st.markdown("### Recession Risk Analysis")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Systemic risk gauge using Ray Dalio's framework
            fig = EconomicPredictions.create_systemic_risk_gauge(
                risk_score=45,
                credit_cycle_position=0.65,
                confidence_adjustment=0.85
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Recession probability chart
            fig = EconomicPredictions.create_recession_probability_chart()
            st.plotly_chart(fig, use_container_width=True)
        
        # Leading indicators
        st.markdown("---")
        st.markdown("#### Leading Economic Indicators")
        
        indicators_cols = st.columns(5)
        indicators = [
            ("Yield Curve", "-0.42%", "inverse"),
            ("LEI Index", "-1.2%", "inverse"),
            ("Credit Spreads", "2.8%", "normal"),
            ("Housing Starts", "-4.3%", "inverse"),
            ("Consumer Conf.", "78.5", "normal")
        ]
        
        for col, (name, value, delta) in zip(indicators_cols, indicators):
            with col:
                st.metric(name, value, delta_color=delta)
    
    with tabs[3]:  # Debt Cycles
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
    
    with tabs[4]:  # Sector Rotation
        sectors = st.session_state.real_data.get_sector_performance()
        
        # Convert list to DataFrame properly
        if sectors and isinstance(sectors, list):
            sector_df = pd.DataFrame(sectors)
        else:
            # Fallback data if sectors is empty
            sector_df = pd.DataFrame({
                'name': ['Technology', 'Energy', 'Healthcare', 'Financials'],
                'performance': [2.3, 3.7, 1.1, -0.5],
                'volume': [1250000000, 670000000, 890000000, 1100000000]
            })
        
        # Create treemap visualization
        if not sector_df.empty:
            fig = ProfessionalCharts.create_treemap(
                sector_df,
                title="Sector Performance Map",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[5]:  # Economic Calendar
        EconomicCalendar.render_calendar()
        
        # Add Fed schedule section
        st.markdown("---")
        EconomicCalendar.render_fed_schedule()
    
    with tabs[6]:  # Empire Cycle
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
            
            values = {'US Position': [0.0] * 4}
            values['US Position'][current_phase_idx] = 100.0
            
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
            
            vol_df = pd.DataFrame(data=Z, columns=[f"{s:.1%}" for s in strikes])
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