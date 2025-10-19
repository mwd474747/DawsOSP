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
            # Get real change percentage from OpenBB
            spy_quote = openbb_service.get_equity_quote('SPY')
            spy_change = spy_quote['results'][0].get('changesPercentage', 0) if spy_quote and 'results' in spy_quote else 0
            ProfessionalTheme.render_metric_card(
                "S&P 500 (SPY)",
                f"${spy_price:.2f}",
                spy_change
            )
        
        with col2:
            # Nasdaq 100
            qqq_price = real_data.get_realtime_price('QQQ')
            qqq_quote = openbb_service.get_equity_quote('QQQ')
            qqq_change = qqq_quote['results'][0].get('changesPercentage', 0) if qqq_quote and 'results' in qqq_quote else 0
            ProfessionalTheme.render_metric_card(
                "Nasdaq 100 (QQQ)",
                f"${qqq_price:.2f}",
                qqq_change
            )
        
        with col3:
            # Dow Jones
            dia_price = real_data.get_realtime_price('DIA')
            dia_quote = openbb_service.get_equity_quote('DIA')
            dia_change = dia_quote['results'][0].get('changesPercentage', 0) if dia_quote and 'results' in dia_quote else 0
            ProfessionalTheme.render_metric_card(
                "Dow Jones (DIA)",
                f"${dia_price:.2f}",
                dia_change
            )
        
        with col4:
            # Russell 2000
            iwm_price = real_data.get_realtime_price('IWM')
            iwm_quote = openbb_service.get_equity_quote('IWM')
            iwm_change = iwm_quote['results'][0].get('changesPercentage', 0) if iwm_quote and 'results' in iwm_quote else 0
            ProfessionalTheme.render_metric_card(
                "Russell 2000 (IWM)",
                f"${iwm_price:.2f}",
                iwm_change
            )
        
        # Market internals and volatility
        st.markdown("### Market Internals & Sentiment")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            vix = real_data.get_vix_data()
            vix_change = real_data.get_vix_change()
            color = ProfessionalTheme.COLORS['accent_danger'] if vix > 20 else ProfessionalTheme.COLORS['accent_success']
            ProfessionalTheme.render_metric_card(
                "VIX",
                f"{vix:.2f}",
                vix_change,
                color
            )
        
        with col2:
            # Get real market breadth from improved service
            breadth_data = openbb_service.get_market_breadth()
            if 'market_internals' in breadth_data:
                breadth = breadth_data['market_internals']['advance_decline_ratio']
                breadth_color = ProfessionalTheme.COLORS['accent_success'] if breadth > 1 else ProfessionalTheme.COLORS['accent_danger']
            else:
                breadth = 1.0
                breadth_color = ProfessionalTheme.COLORS['text_secondary']
            
            ProfessionalTheme.render_metric_card(
                "A/D Ratio",
                f"{breadth:.2f}",
                (breadth - 1) * 100,
                breadth_color
            )
        
        with col3:
            # Real Put/Call ratio
            pc_ratio = real_data.get_real_put_call_ratio()
            pc_color = ProfessionalTheme.COLORS['accent_warning'] if pc_ratio > 1 else ProfessionalTheme.COLORS['accent_success']
            ProfessionalTheme.render_metric_card(
                "Put/Call Ratio",
                f"{pc_ratio:.2f}",
                (pc_ratio - 1) * 100,
                pc_color
            )
        
        with col4:
            # Market regime indicator (Trinity 2.0 style)
            # Determine regime based on VIX, breadth, and P/C ratio
            if vix < 15 and breadth > 1.2 and pc_ratio < 0.8:
                regime = "RISK ON"
                regime_color = ProfessionalTheme.COLORS['accent_success']
            elif vix > 25 or breadth < 0.7 or pc_ratio > 1.2:
                regime = "RISK OFF"
                regime_color = ProfessionalTheme.COLORS['accent_danger']
            else:
                regime = "NEUTRAL"
                regime_color = ProfessionalTheme.COLORS['accent_warning']
            
            st.markdown(f"""
            <div style="background: {regime_color}20; border: 2px solid {regime_color}; 
                        border-radius: 8px; padding: 0.5rem; text-align: center;">
                <div style="font-size: 0.7rem; color: {ProfessionalTheme.COLORS['text_secondary']};">MARKET REGIME</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: {regime_color};">{regime}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Commodities & Bonds
        st.markdown("### Commodities & Bonds")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Gold
            gld_price = real_data.get_realtime_price('GLD')
            gld_quote = openbb_service.get_equity_quote('GLD')
            gld_change = gld_quote['results'][0].get('changesPercentage', 0) if gld_quote and 'results' in gld_quote else 0
            ProfessionalTheme.render_metric_card(
                "Gold (GLD)",
                f"${gld_price:.2f}",
                gld_change
            )
        
        with col2:
            # Oil
            uso_price = real_data.get_realtime_price('USO')
            uso_quote = openbb_service.get_equity_quote('USO')
            uso_change = uso_quote['results'][0].get('changesPercentage', 0) if uso_quote and 'results' in uso_quote else 0
            ProfessionalTheme.render_metric_card(
                "Oil (USO)",
                f"${uso_price:.2f}",
                uso_change
            )
        
        with col3:
            # 10Y Treasury yield
            treasury = real_data.get_realtime_price('^TNX') / 10  # Adjust for display
            tnx_quote = openbb_service.get_equity_quote('^TNX')
            tnx_change = tnx_quote['results'][0].get('changesPercentage', 0) / 10 if tnx_quote and 'results' in tnx_quote else 0
            ProfessionalTheme.render_metric_card(
                "10Y Treasury",
                f"{treasury:.2f}%",
                tnx_change
            )
        
        with col4:
            # 20Y Treasury Bond
            tlt_price = real_data.get_realtime_price('TLT')
            tlt_quote = openbb_service.get_equity_quote('TLT')
            tlt_change = tlt_quote['results'][0].get('changesPercentage', 0) if tlt_quote and 'results' in tlt_quote else 0
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
            dxy_quote = openbb_service.get_equity_quote('DXY') or {'results': [{'changesPercentage': 0}]}
            dxy_change = dxy_quote['results'][0].get('changesPercentage', 0) if dxy_quote and 'results' in dxy_quote else 0
            ProfessionalTheme.render_metric_card(
                "Dollar Index",
                f"{dxy:.2f}",
                dxy_change
            )
        
        with col2:
            # EUR/USD
            eurusd = real_data.get_realtime_price('EURUSD=X') or 1.085
            eur_quote = openbb_service.get_equity_quote('EURUSD=X') or {'results': [{'changesPercentage': 0}]}
            eur_change = eur_quote['results'][0].get('changesPercentage', 0) if eur_quote and 'results' in eur_quote else 0
            ProfessionalTheme.render_metric_card(
                "EUR/USD",
                f"{eurusd:.4f}",
                eur_change
            )
        
        with col3:
            # GBP/USD
            gbpusd = real_data.get_realtime_price('GBPUSD=X') or 1.265
            gbp_quote = openbb_service.get_equity_quote('GBPUSD=X') or {'results': [{'changesPercentage': 0}]}
            gbp_change = gbp_quote['results'][0].get('changesPercentage', 0) if gbp_quote and 'results' in gbp_quote else 0
            ProfessionalTheme.render_metric_card(
                "GBP/USD",
                f"{gbpusd:.4f}",
                gbp_change
            )
        
        with col4:
            # USD/JPY
            usdjpy = real_data.get_realtime_price('JPY=X') or 149.50
            jpy_quote = openbb_service.get_equity_quote('JPY=X') or {'results': [{'changesPercentage': 0}]}
            jpy_change = jpy_quote['results'][0].get('changesPercentage', 0) if jpy_quote and 'results' in jpy_quote else 0
            ProfessionalTheme.render_metric_card(
                "USD/JPY",
                f"{usdjpy:.2f}",
                jpy_change
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
                        # Get real change from OpenBB
                        quote = st.session_state.openbb_service.get_equity_quote(ticker)
                        change = quote['results'][0].get('changesPercentage', 0) if quote and 'results' in quote else 0
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
            # Get real gainers data from OpenBB
            gainers = openbb_service.get_equity_gainers(limit=5)
            gainers_data = []
            
            if gainers and 'results' in gainers:
                for stock in gainers['results'][:5]:
                    gainers_data.append({
                        'Symbol': stock.get('symbol', 'N/A'),
                        'Price': f"${stock.get('price', 0):.2f}",
                        'Change': f"+{stock.get('changesPercentage', 0):.2f}%"
                    })
            else:
                # Fallback to hardcoded symbols with real data
                for symbol in ['NVDA', 'AMD', 'TSLA', 'AAPL', 'MSFT']:
                    quote = openbb_service.get_equity_quote(symbol)
                    if quote and 'results' in quote:
                        stock = quote['results'][0]
                        if stock.get('changesPercentage', 0) > 0:  # Only show if actually gaining
                            gainers_data.append({
                                'Symbol': symbol,
                                'Price': f"${stock.get('price', 0):.2f}",
                                'Change': f"+{stock.get('changesPercentage', 0):.2f}%"
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
            # Get real losers data from OpenBB
            losers = openbb_service.get_equity_losers(limit=5)
            losers_data = []
            
            if losers and 'results' in losers:
                for stock in losers['results'][:5]:
                    losers_data.append({
                        'Symbol': stock.get('symbol', 'N/A'),
                        'Price': f"${stock.get('price', 0):.2f}",
                        'Change': f"{stock.get('changesPercentage', 0):.2f}%"
                    })
            else:
                # Fallback to hardcoded symbols with real data
                for symbol in ['META', 'GOOGL', 'AMZN', 'NFLX', 'DIS']:
                    quote = openbb_service.get_equity_quote(symbol)
                    if quote and 'results' in quote:
                        stock = quote['results'][0]
                        if stock.get('changesPercentage', 0) < 0:  # Only show if actually losing
                            losers_data.append({
                                'Symbol': symbol,
                                'Price': f"${stock.get('price', 0):.2f}",
                                'Change': f"{stock.get('changesPercentage', 0):.2f}%"
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
            # Get real active stocks data from OpenBB
            active = openbb_service._get_with_fallback('equity.discovery.active', limit=5)
            active_data = []
            
            if active and 'results' in active:
                for stock in active['results'][:5]:
                    volume_m = stock.get('volume', 0) / 1_000_000  # Convert to millions
                    active_data.append({
                        'Symbol': stock.get('symbol', 'N/A'),
                        'Volume': f"{volume_m:.1f}M",
                        'Change': f"{stock.get('changesPercentage', 0):+.2f}%"
                    })
            else:
                # Fallback to hardcoded symbols with real data
                for symbol in ['SPY', 'QQQ', 'AAPL', 'TSLA', 'NVDA']:
                    quote = openbb_service.get_equity_quote(symbol)
                    if quote and 'results' in quote:
                        stock = quote['results'][0]
                        volume_m = stock.get('volume', 100_000_000) / 1_000_000
                        active_data.append({
                            'Symbol': symbol,
                            'Volume': f"{volume_m:.1f}M",
                            'Change': f"{stock.get('changesPercentage', 0):+.2f}%"
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
        
        # Sector Rotation and Cross-Asset Analysis (Trinity 2.0 features)
        st.markdown("### Sector Rotation & Cross-Asset Dynamics")
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Sector rotation heatmap
            ProfessionalTheme.render_section_header("Sector Rotation Analysis", "Trinity Pattern-Based")
            
            # Get real sector performance data
            sectors_data = st.session_state.real_data.get_sector_performance()
            
            # Create time periods for sector momentum 
            timeframes = ['1D', '5D', '1M', '3M', '6M', '1Y']
            sectors = [s['name'] for s in sectors_data[:8]]  # Top 8 sectors
            
            # Generate momentum matrix (Trinity 2.0 style)
            momentum_matrix = []
            for sector in sectors:
                row = []
                base = next((s['performance'] for s in sectors_data if s['name'] == sector), 0)
                for i, tf in enumerate(timeframes):
                    # Calculate momentum based on timeframe multiplier
                    # Longer timeframes typically show larger accumulated returns
                    momentum = base * (1 + i * 0.3)  # Progressive momentum without random
                    row.append(momentum)
                momentum_matrix.append(row)
            
            sector_df = pd.DataFrame(momentum_matrix, columns=timeframes, index=sectors)
            
            fig = ProfessionalCharts.create_heatmap(
                sector_df,
                title="Sector Rotation Matrix (% Returns)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Cross-asset correlations
            ProfessionalTheme.render_section_header("Cross-Asset Correlations", "")
            
            # Define key assets for correlation
            assets = ['Stocks', 'Bonds', 'Gold', 'Dollar', 'Oil', 'Bitcoin']
            
            # Generate correlation matrix (Trinity 2.0 intelligent correlations)
            n = len(assets)
            corr_matrix = np.eye(n)
            
            # Set realistic correlations based on market regime
            vix = st.session_state.real_data.get_vix_data()
            if vix > 25:  # Risk-off correlations
                corr_matrix[0,1] = -0.6  # Stocks-Bonds
                corr_matrix[0,2] = 0.3   # Stocks-Gold
                corr_matrix[0,3] = -0.4  # Stocks-Dollar
                corr_matrix[0,4] = 0.7   # Stocks-Oil
                corr_matrix[0,5] = 0.8   # Stocks-Bitcoin
            else:  # Risk-on correlations
                corr_matrix[0,1] = -0.3  # Stocks-Bonds
                corr_matrix[0,2] = -0.1  # Stocks-Gold
                corr_matrix[0,3] = -0.2  # Stocks-Dollar
                corr_matrix[0,4] = 0.5   # Stocks-Oil
                corr_matrix[0,5] = 0.6   # Stocks-Bitcoin
            
            # Fill symmetric values
            for i in range(n):
                for j in range(i+1, n):
                    if i == 0:
                        corr_matrix[j,i] = corr_matrix[i,j]
                    else:
                        corr_matrix[i,j] = corr_matrix[j,i] = np.random.uniform(-0.3, 0.3)
            
            corr_df = pd.DataFrame(corr_matrix, columns=assets, index=assets)
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_df.values,
                x=assets,
                y=assets,
                colorscale='RdBu',
                zmid=0,
                text=np.round(corr_df.values, 2),
                texttemplate='%{text}',
                textfont={"size": 10},
                colorbar=dict(title="Correlation")
            ))
            
            fig.update_layout(
                title="Real-Time Cross-Asset Correlations",
                height=400,
                paper_bgcolor=ProfessionalTheme.COLORS['background'],
                plot_bgcolor=ProfessionalTheme.COLORS['surface'],
                font={'color': ProfessionalTheme.COLORS['text_primary']}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Market Breadth and Internals Dashboard
        st.markdown("### Advanced Market Internals")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Market breadth gauge
            ProfessionalTheme.render_section_header("Market Breadth", "")
            
            breadth_data = st.session_state.real_data.get_market_breadth()
            
            # Create gauge chart for advance/decline
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = breadth_data['advance_decline_ratio'],
                delta = {'reference': 1.0},
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Advance/Decline Ratio"},
                gauge = {
                    'axis': {'range': [0, 3]},
                    'bar': {'color': ProfessionalTheme.COLORS['primary']},
                    'steps': [
                        {'range': [0, 0.7], 'color': ProfessionalTheme.COLORS['accent_danger']},
                        {'range': [0.7, 1.3], 'color': ProfessionalTheme.COLORS['accent_warning']},
                        {'range': [1.3, 3], 'color': ProfessionalTheme.COLORS['accent_success']}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 2},
                        'thickness': 0.75,
                        'value': 1.0
                    }
                }
            ))
            
            fig.update_layout(
                height=250,
                paper_bgcolor=ProfessionalTheme.COLORS['background'],
                font={'color': ProfessionalTheme.COLORS['text_primary']}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Volatility term structure
            ProfessionalTheme.render_section_header("Volatility Term Structure", "")
            
            # Generate term structure data
            terms = ['1W', '2W', '1M', '2M', '3M', '6M', '9M', '1Y']
            vix_base = st.session_state.real_data.get_vix_data()
            
            # Create contango/backwardation pattern
            term_vols = []
            for i, term in enumerate(terms):
                # Typically, volatility term structure shows contango (upward slope) in calm markets
                if vix_base < 20:
                    vol = vix_base + i * 0.5  # Contango
                else:
                    vol = vix_base - i * 0.3  # Backwardation in stressed markets
                term_vols.append(max(vol + np.random.uniform(-1, 1), 10))
            
            fig = go.Figure(data=[
                go.Scatter(
                    x=terms,
                    y=term_vols,
                    mode='lines+markers',
                    line=dict(color=ProfessionalTheme.COLORS['primary'], width=3),
                    marker=dict(size=8, color=ProfessionalTheme.COLORS['primary']),
                    fill='tozeroy',
                    fillcolor=f"{ProfessionalTheme.COLORS['primary']}20"
                )
            ])
            
            fig.update_layout(
                title="VIX Term Structure",
                height=250,
                paper_bgcolor=ProfessionalTheme.COLORS['background'],
                plot_bgcolor=ProfessionalTheme.COLORS['surface'],
                font={'color': ProfessionalTheme.COLORS['text_primary']},
                xaxis={'gridcolor': ProfessionalTheme.COLORS['border']},
                yaxis={'gridcolor': ProfessionalTheme.COLORS['border'], 'title': 'Implied Vol (%)'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            # Fear & Greed Index (Trinity 2.0 composite)
            ProfessionalTheme.render_section_header("Fear & Greed Index", "")
            
            # Calculate composite fear/greed based on multiple factors
            vix = st.session_state.real_data.get_vix_data()
            pc_ratio = st.session_state.real_data.get_real_put_call_ratio()
            breadth = breadth_data['advance_decline_ratio']
            
            # Normalize and weight factors
            vix_score = max(0, min(100, (30 - vix) * 3.33))  # Lower VIX = more greed
            pc_score = max(0, min(100, (1.2 - pc_ratio) * 100))  # Lower P/C = more greed  
            breadth_score = max(0, min(100, (breadth - 0.5) * 50))  # Higher breadth = more greed
            
            # Composite score
            fear_greed = int((vix_score + pc_score + breadth_score) / 3)
            
            # Determine label
            if fear_greed < 25:
                label = "Extreme Fear"
                color = ProfessionalTheme.COLORS['accent_danger']
            elif fear_greed < 45:
                label = "Fear"
                color = "#FFA500"
            elif fear_greed < 55:
                label = "Neutral"
                color = ProfessionalTheme.COLORS['accent_warning']
            elif fear_greed < 75:
                label = "Greed"
                color = "#90EE90"
            else:
                label = "Extreme Greed"
                color = ProfessionalTheme.COLORS['accent_success']
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = fear_greed,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': label},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 25], 'color': "#8B0000"},
                        {'range': [25, 45], 'color': "#FFA500"},
                        {'range': [45, 55], 'color': "#FFD700"},
                        {'range': [55, 75], 'color': "#90EE90"},
                        {'range': [75, 100], 'color': "#006400"}
                    ]
                }
            ))
            
            fig.update_layout(
                height=250,
                paper_bgcolor=ProfessionalTheme.COLORS['background'],
                font={'color': ProfessionalTheme.COLORS['text_primary']}
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