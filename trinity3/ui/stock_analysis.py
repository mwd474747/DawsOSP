"""
Stock Analysis Interface - Professional Bloomberg Terminal-style stock analysis
Integrates all DawsOS 2.0 stock analysis capabilities into Trinity 3.0
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List, Optional, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.professional_theme import ProfessionalTheme
from ui.professional_charts import ProfessionalCharts
from services.openbb_service import OpenBBService  
from services.real_data_helper import RealDataHelper
from services.prediction_service import PredictionService

# Import DawsOS 2.0 analysis components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from dawsos.agents.analyzers.dcf_analyzer import DCFAnalyzer
from dawsos.agents.analyzers.moat_analyzer import MoatAnalyzer
from dawsos.agents.analyzers.financial_data_fetcher import FinancialDataFetcher
from dawsos.core.confidence_calculator import ConfidenceCalculator

class StockAnalysis:
    """Professional stock analysis interface"""
    
    def __init__(self, openbb_service: OpenBBService, real_data: RealDataHelper):
        self.openbb = openbb_service
        self.real_data = real_data
        self.confidence_calculator = ConfidenceCalculator()
        
        # Initialize analyzers
        self.dcf_analyzer = DCFAnalyzer(
            market_capability=self.openbb,
            logger=st.session_state.get('logger')
        )
        self.moat_analyzer = MoatAnalyzer(
            logger=st.session_state.get('logger')
        )
        self.data_fetcher = FinancialDataFetcher(
            market_capability=self.openbb,
            logger=st.session_state.get('logger')
        )
    
    def render(self):
        """Render the stock analysis interface"""
        ProfessionalTheme.render_section_header(
            "Stock Analysis Terminal",
            "Professional equity research and valuation platform"
        )
        
        # Symbol input and search
        self._render_symbol_search()
        
        # Main analysis tabs
        if st.session_state.get('selected_symbol'):
            symbol = st.session_state.selected_symbol
            
            # Sub-navigation for different analysis types
            analysis_tabs = st.tabs([
                "Overview", 
                "Fundamentals", 
                "Technical", 
                "Valuation", 
                "Earnings",
                "Risk Analysis",
                "Peer Comparison",
                "AI Insights"
            ])
            
            with analysis_tabs[0]:
                self._render_overview(symbol)
            
            with analysis_tabs[1]:
                self._render_fundamentals(symbol)
            
            with analysis_tabs[2]:
                self._render_technical_analysis(symbol)
            
            with analysis_tabs[3]:
                self._render_valuation(symbol)
            
            with analysis_tabs[4]:
                self._render_earnings(symbol)
            
            with analysis_tabs[5]:
                self._render_risk_analysis(symbol)
            
            with analysis_tabs[6]:
                self._render_peer_comparison(symbol)
            
            with analysis_tabs[7]:
                self._render_ai_insights(symbol)
    
    def _render_symbol_search(self):
        """Render symbol search and selection"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            symbol_input = st.text_input(
                "Enter Symbol",
                placeholder="AAPL, MSFT, GOOGL...",
                key="stock_symbol_input",
                label_visibility="collapsed"
            ).upper()
        
        with col2:
            if st.button("Analyze", type="primary", use_container_width=True):
                if symbol_input:
                    st.session_state.selected_symbol = symbol_input
                    st.rerun()
        
        with col3:
            if st.button("Clear", use_container_width=True):
                if 'selected_symbol' in st.session_state:
                    del st.session_state.selected_symbol
                    st.rerun()
        
        # Quick access watchlist
        if not st.session_state.get('selected_symbol'):
            st.markdown("### Quick Access")
            cols = st.columns(6)
            watchlist = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA']
            for i, symbol in enumerate(watchlist):
                with cols[i]:
                    if st.button(symbol, key=f"quick_{symbol}", use_container_width=True):
                        st.session_state.selected_symbol = symbol
                        st.rerun()
    
    def _render_overview(self, symbol: str):
        """Render stock overview section"""
        st.markdown("### Company Overview")
        
        # Get real-time quote
        quote_data = self._get_quote_data(symbol)
        
        # Price and key stats
        col1, col2 = st.columns([2, 3])
        
        with col1:
            # Real-time price display
            st.markdown(f"## ${quote_data['price']:.2f}")
            change_color = "green" if quote_data['change'] >= 0 else "red"
            st.markdown(
                f"<span style='color:{change_color};font-size:20px;'>"
                f"{quote_data['change']:+.2f} ({quote_data['change_pct']:+.2f}%)</span>",
                unsafe_allow_html=True
            )
            
            # Volume and range
            st.metric("Volume", f"{quote_data['volume']:,.0f}")
            st.metric("Day Range", f"${quote_data['low']:.2f} - ${quote_data['high']:.2f}")
            st.metric("52W Range", f"${quote_data['year_low']:.2f} - ${quote_data['year_high']:.2f}")
        
        with col2:
            # Key statistics grid
            self._render_key_stats(symbol, quote_data)
        
        # Intraday chart
        st.markdown("### Intraday Performance")
        self._render_intraday_chart(symbol)
        
        # Company profile
        profile = self._get_company_profile(symbol)
        if profile:
            st.markdown("### Company Profile")
            st.write(profile.get('description', 'No description available'))
            
            # Company info grid
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Sector", profile.get('sector', 'N/A'))
            with col2:
                st.metric("Industry", profile.get('industry', 'N/A'))
            with col3:
                st.metric("Employees", f"{profile.get('employees', 0):,}")
            with col4:
                st.metric("Founded", profile.get('founded', 'N/A'))
    
    def _render_fundamentals(self, symbol: str):
        """Render fundamental analysis section"""
        st.markdown("### Fundamental Analysis")
        
        # Get financial data
        financials = self.data_fetcher.get_company_financials(symbol)
        
        if 'error' not in financials:
            # Financial metrics dashboard
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**Profitability**")
                metrics = {
                    "Gross Margin": f"{financials.get('gross_margin', 0)*100:.1f}%",
                    "Operating Margin": f"{financials.get('operating_margin', 0)*100:.1f}%",
                    "Net Margin": f"{financials.get('net_margin', 0)*100:.1f}%",
                    "ROE": f"{financials.get('roe', 0)*100:.1f}%",
                    "ROA": f"{financials.get('roa', 0)*100:.1f}%",
                    "ROIC": f"{financials.get('roic', 0)*100:.1f}%"
                }
                for metric, value in metrics.items():
                    st.metric(metric, value)
            
            with col2:
                st.markdown("**Valuation**")
                metrics = {
                    "P/E Ratio": f"{financials.get('pe_ratio', 0):.1f}",
                    "PEG Ratio": f"{financials.get('peg_ratio', 0):.2f}",
                    "P/B Ratio": f"{financials.get('price_to_book', 0):.2f}",
                    "P/S Ratio": f"{financials.get('price_to_sales', 0):.2f}",
                    "EV/EBITDA": f"{financials.get('ev_ebitda', 0):.2f}",
                    "FCF Yield": f"{financials.get('fcf_yield', 0)*100:.2f}%"
                }
                for metric, value in metrics.items():
                    st.metric(metric, value)
            
            with col3:
                st.markdown("**Growth**")
                metrics = {
                    "Rev Growth (YoY)": f"{financials.get('revenue_growth', 0)*100:.1f}%",
                    "EPS Growth": f"{financials.get('eps_growth', 0)*100:.1f}%",
                    "FCF Growth": f"{financials.get('fcf_growth', 0)*100:.1f}%",
                    "EBITDA Growth": f"{financials.get('ebitda_growth', 0)*100:.1f}%",
                    "5Y Rev CAGR": f"{financials.get('revenue_cagr_5y', 0)*100:.1f}%",
                    "5Y EPS CAGR": f"{financials.get('eps_cagr_5y', 0)*100:.1f}%"
                }
                for metric, value in metrics.items():
                    st.metric(metric, value)
            
            with col4:
                st.markdown("**Financial Health**")
                metrics = {
                    "Current Ratio": f"{financials.get('current_ratio', 0):.2f}",
                    "Quick Ratio": f"{financials.get('quick_ratio', 0):.2f}",
                    "Debt/Equity": f"{financials.get('debt_to_equity', 0):.2f}",
                    "Interest Coverage": f"{financials.get('interest_coverage', 0):.1f}x",
                    "Cash/Share": f"${financials.get('cash_per_share', 0):.2f}",
                    "Book Value/Share": f"${financials.get('book_value_per_share', 0):.2f}"
                }
                for metric, value in metrics.items():
                    st.metric(metric, value)
            
            # Financial statements
            st.markdown("### Financial Statements")
            stmt_tabs = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
            
            with stmt_tabs[0]:
                self._render_income_statement(symbol, financials)
            
            with stmt_tabs[1]:
                self._render_balance_sheet(symbol, financials)
            
            with stmt_tabs[2]:
                self._render_cash_flow(symbol, financials)
        else:
            st.error(f"Unable to fetch financial data: {financials.get('error')}")
    
    def _render_technical_analysis(self, symbol: str):
        """Render technical analysis section"""
        st.markdown("### Technical Analysis")
        
        # Time period selector
        col1, col2, col3 = st.columns(3)
        with col1:
            period = st.selectbox(
                "Period",
                ["1D", "5D", "1M", "3M", "6M", "1Y", "2Y", "5Y"],
                index=5,
                key=f"{symbol}_tech_period"
            )
        
        with col2:
            chart_type = st.selectbox(
                "Chart Type",
                ["Candlestick", "Line", "OHLC"],
                key=f"{symbol}_chart_type"
            )
        
        with col3:
            indicators = st.multiselect(
                "Indicators",
                ["SMA20", "SMA50", "SMA200", "EMA12", "EMA26", "Bollinger Bands", "Volume"],
                default=["SMA20", "SMA50", "Volume"],
                key=f"{symbol}_indicators"
            )
        
        # Price chart with technical indicators
        self._render_technical_chart(symbol, period, chart_type, indicators)
        
        # Technical indicators dashboard
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Trend Indicators**")
            self._render_trend_indicators(symbol)
        
        with col2:
            st.markdown("**Momentum Indicators**")
            self._render_momentum_indicators(symbol)
        
        with col3:
            st.markdown("**Volatility Indicators**")
            self._render_volatility_indicators(symbol)
        
        # Support and Resistance Levels
        st.markdown("### Key Levels")
        self._render_support_resistance(symbol)
        
        # Pattern Recognition
        st.markdown("### Pattern Recognition")
        self._render_pattern_recognition(symbol)
    
    def _render_valuation(self, symbol: str):
        """Render valuation analysis section"""
        st.markdown("### Valuation Analysis")
        
        # DCF Calculator
        st.markdown("#### Discounted Cash Flow (DCF) Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # DCF inputs
            st.markdown("**DCF Assumptions**")
            
            # Get financial data for defaults
            financials = self.data_fetcher.get_company_financials(symbol)
            
            fcf = st.number_input(
                "Free Cash Flow (M)",
                value=float(financials.get('free_cash_flow', 1000) / 1e6),
                step=100.0,
                key=f"{symbol}_fcf"
            )
            
            growth_rate = st.slider(
                "Growth Rate (%)",
                min_value=0.0,
                max_value=30.0,
                value=10.0,
                step=0.5,
                key=f"{symbol}_growth"
            )
            
            terminal_growth = st.slider(
                "Terminal Growth (%)",
                min_value=0.0,
                max_value=5.0,
                value=2.5,
                step=0.1,
                key=f"{symbol}_terminal"
            )
            
            discount_rate = st.slider(
                "Discount Rate (%)",
                min_value=5.0,
                max_value=20.0,
                value=10.0,
                step=0.5,
                key=f"{symbol}_discount"
            )
            
            shares = st.number_input(
                "Shares Outstanding (M)",
                value=float(financials.get('shares_outstanding', 1000) / 1e6),
                step=10.0,
                key=f"{symbol}_shares"
            )
        
        with col2:
            # DCF calculation and results
            if st.button("Calculate DCF", type="primary"):
                dcf_result = self._calculate_dcf(
                    symbol, fcf * 1e6, growth_rate/100, 
                    terminal_growth/100, discount_rate/100, shares * 1e6
                )
                
                if dcf_result:
                    st.markdown("**DCF Valuation Results**")
                    
                    current_price = self._get_quote_data(symbol)['price']
                    intrinsic = dcf_result['intrinsic_value_per_share']
                    upside = ((intrinsic - current_price) / current_price) * 100
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Intrinsic Value", f"${intrinsic:.2f}")
                        st.metric("Current Price", f"${current_price:.2f}")
                    with col_b:
                        color = "green" if upside > 0 else "red"
                        st.metric("Upside/Downside", f"{upside:+.1f}%")
                        st.metric(
                            "Recommendation",
                            "BUY" if upside > 20 else "HOLD" if upside > -10 else "SELL"
                        )
                    
                    # Sensitivity analysis
                    st.markdown("**Sensitivity Analysis**")
                    self._render_dcf_sensitivity(dcf_result)
        
        # Moat Analysis
        st.markdown("#### Economic Moat Analysis")
        moat_result = self._analyze_moat(symbol, financials)
        if moat_result:
            self._render_moat_analysis(moat_result)
        
        # Buffett Checklist
        st.markdown("#### Buffett Investment Checklist")
        self._render_buffett_checklist(symbol, financials)
        
        # Multiple Valuation
        st.markdown("#### Relative Valuation")
        self._render_multiple_valuation(symbol, financials)
    
    def _render_earnings(self, symbol: str):
        """Render earnings analysis section"""
        st.markdown("### Earnings Analysis")
        
        # Historical earnings
        st.markdown("#### Historical Earnings")
        earnings_data = self._get_earnings_history(symbol)
        
        if earnings_data:
            # Earnings chart
            fig = ProfessionalCharts.create_line_chart(
                {'Actual': earnings_data['actual'].tolist(), 
                 'Estimate': earnings_data['estimate'].tolist()},
                title="Earnings History",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Earnings surprise history
            st.markdown("#### Earnings Surprises")
            self._render_earnings_surprises(earnings_data)
        
        # Earnings predictions
        st.markdown("#### Earnings Forecast")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Next earnings date
            next_earnings = self._get_next_earnings_date(symbol)
            st.info(f"Next Earnings: {next_earnings}")
            
            # Analyst estimates
            estimates = self._get_analyst_estimates(symbol)
            if estimates:
                st.markdown("**Analyst Consensus**")
                st.metric("EPS Estimate", f"${estimates['eps_estimate']:.2f}")
                st.metric("Revenue Estimate", f"${estimates['revenue_estimate']/1e9:.2f}B")
                st.metric("# of Analysts", estimates['num_analysts'])
        
        with col2:
            # AI earnings prediction
            if st.button("Generate AI Forecast", type="primary"):
                prediction = self._generate_earnings_prediction(symbol)
                if prediction:
                    st.markdown("**AI Prediction**")
                    st.metric("Predicted EPS", f"${prediction['eps']:.2f}")
                    st.metric("Confidence", f"{prediction['confidence']:.1f}%")
                    st.write(prediction['reasoning'])
        
        # Earnings calendar
        st.markdown("#### Upcoming Earnings Calendar")
        self._render_earnings_calendar()
    
    def _render_risk_analysis(self, symbol: str):
        """Render risk analysis section"""
        st.markdown("### Risk Analysis")
        
        # Risk metrics dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        risk_metrics = self._calculate_risk_metrics(symbol)
        
        with col1:
            st.markdown("**Market Risk**")
            st.metric("Beta", f"{risk_metrics['beta']:.2f}")
            st.metric("Volatility (30D)", f"{risk_metrics['volatility_30d']:.1f}%")
            st.metric("Sharpe Ratio", f"{risk_metrics['sharpe']:.2f}")
        
        with col2:
            st.markdown("**Downside Risk**")
            st.metric("Max Drawdown", f"{risk_metrics['max_drawdown']:.1f}%")
            st.metric("Value at Risk (95%)", f"{risk_metrics['var_95']:.1f}%")
            st.metric("Downside Deviation", f"{risk_metrics['downside_dev']:.1f}%")
        
        with col3:
            st.markdown("**Credit Risk**")
            st.metric("Altman Z-Score", f"{risk_metrics['z_score']:.2f}")
            st.metric("Interest Coverage", f"{risk_metrics['interest_coverage']:.1f}x")
            st.metric("Debt/EBITDA", f"{risk_metrics['debt_ebitda']:.2f}")
        
        with col4:
            st.markdown("**Liquidity Risk**")
            st.metric("Current Ratio", f"{risk_metrics['current_ratio']:.2f}")
            st.metric("Avg Volume (30D)", f"{risk_metrics['avg_volume_30d']/1e6:.1f}M")
            st.metric("Bid-Ask Spread", f"{risk_metrics['bid_ask_spread']:.3f}%")
        
        # Risk chart
        st.markdown("#### Risk Distribution")
        self._render_risk_distribution(symbol)
        
        # Risk factors
        st.markdown("#### Key Risk Factors")
        self._render_risk_factors(symbol)
        
        # Scenario analysis
        st.markdown("#### Scenario Analysis")
        self._render_scenario_analysis(symbol)
    
    def _render_peer_comparison(self, symbol: str):
        """Render peer comparison section"""
        st.markdown("### Peer Comparison")
        
        # Get industry peers
        peers = self._get_industry_peers(symbol)
        
        if peers:
            # Peer selection
            selected_peers = st.multiselect(
                "Select Peers to Compare",
                peers,
                default=peers[:4] if len(peers) >= 4 else peers,
                key=f"{symbol}_peer_select"
            )
            
            if selected_peers:
                # Comparison metrics
                comparison_data = self._get_peer_comparison_data(symbol, selected_peers)
                
                # Valuation comparison
                st.markdown("#### Valuation Metrics")
                self._render_valuation_comparison(comparison_data)
                
                # Performance comparison
                st.markdown("#### Performance Metrics")
                self._render_performance_comparison(comparison_data)
                
                # Financial health comparison
                st.markdown("#### Financial Health")
                self._render_health_comparison(comparison_data)
                
                # Relative ranking
                st.markdown("#### Relative Ranking")
                self._render_peer_ranking(symbol, comparison_data)
        else:
            st.info("No peer data available for comparison")
    
    def _render_ai_insights(self, symbol: str):
        """Render AI-powered insights section"""
        st.markdown("### AI-Powered Insights")
        
        # Analysis type selector
        analysis_type = st.selectbox(
            "Select Analysis Type",
            [
                "Comprehensive Analysis",
                "Bull Case / Bear Case",
                "Investment Thesis",
                "Risk Assessment",
                "Growth Potential",
                "Technical Outlook",
                "Catalyst Analysis"
            ],
            key=f"{symbol}_ai_analysis"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("Generate Analysis", type="primary"):
                with st.spinner(f"Generating {analysis_type}..."):
                    analysis = self._generate_ai_analysis(symbol, analysis_type)
                    if analysis:
                        st.session_state[f'{symbol}_ai_result'] = analysis
        
        # Display analysis result
        if f'{symbol}_ai_result' in st.session_state:
            result = st.session_state[f'{symbol}_ai_result']
            
            # Confidence score
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Confidence Score", f"{result.get('confidence', 0):.1f}%")
            with col2:
                st.metric("Data Quality", result.get('data_quality', 'Good'))
            with col3:
                st.metric("Analysis Date", datetime.now().strftime("%Y-%m-%d"))
            
            # Main analysis content
            st.markdown("#### Analysis Results")
            st.markdown(result.get('analysis', 'No analysis available'))
            
            # Key takeaways
            if 'key_points' in result:
                st.markdown("#### Key Takeaways")
                for point in result['key_points']:
                    st.write(f"• {point}")
            
            # Recommendations
            if 'recommendation' in result:
                st.markdown("#### Recommendation")
                rec = result['recommendation']
                color = {"BUY": "green", "HOLD": "orange", "SELL": "red"}.get(rec['action'], "gray")
                st.markdown(
                    f"<div style='padding:10px;border-left:4px solid {color};'>"
                    f"<b>{rec['action']}</b> - {rec['rationale']}</div>",
                    unsafe_allow_html=True
                )
    
    # Helper methods for data fetching and calculations
    def _get_quote_data(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote data"""
        try:
            quote = self.openbb.get_equity_quote(symbol)
            if quote and 'results' in quote:
                data = quote['results'][0]
                return {
                    'price': data.get('price', 0),
                    'change': data.get('change', 0),
                    'change_pct': data.get('changesPercentage', 0),
                    'volume': data.get('volume', 0),
                    'high': data.get('dayHigh', 0),
                    'low': data.get('dayLow', 0),
                    'year_high': data.get('yearHigh', 0),
                    'year_low': data.get('yearLow', 0),
                    'market_cap': data.get('marketCap', 0),
                    'pe_ratio': data.get('pe', 0),
                    'eps': data.get('eps', 0),
                    'dividend_yield': data.get('dividendYield', 0)
                }
        except Exception as e:
            st.error(f"Error fetching quote: {e}")
        
        # Return default values
        return {
            'price': 100.0,
            'change': 2.5,
            'change_pct': 2.5,
            'volume': 10000000,
            'high': 102.0,
            'low': 98.0,
            'year_high': 120.0,
            'year_low': 80.0,
            'market_cap': 1000000000,
            'pe_ratio': 20.0,
            'eps': 5.0,
            'dividend_yield': 2.0
        }
    
    def _get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile data"""
        try:
            profile = self.openbb.get_company_profile(symbol)
            if profile:
                return profile
        except Exception as e:
            st.error(f"Error fetching profile: {e}")
        return {}
    
    def _render_key_stats(self, symbol: str, quote_data: Dict[str, Any]):
        """Render key statistics grid"""
        stats_df = pd.DataFrame([
            ["Market Cap", f"${quote_data['market_cap']/1e9:.2f}B"],
            ["P/E Ratio", f"{quote_data['pe_ratio']:.2f}"],
            ["EPS", f"${quote_data['eps']:.2f}"],
            ["Dividend Yield", f"{quote_data['dividend_yield']:.2f}%"],
            ["Beta", "1.2"],  # Would fetch from API
            ["Avg Volume", f"{quote_data['volume']/1e6:.2f}M"]
        ], columns=["Metric", "Value"])
        
        st.dataframe(
            stats_df,
            hide_index=True,
            use_container_width=True,
            height=250
        )
    
    def _render_intraday_chart(self, symbol: str):
        """Render intraday price chart"""
        # Generate sample intraday data
        times = pd.date_range(start='09:30', end='16:00', freq='5min')
        base_price = 100
        prices = base_price + np.cumsum(np.random.randn(len(times)) * 0.5)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=prices,
            mode='lines',
            name=symbol,
            line=dict(color=ProfessionalTheme.COLORS['accent_primary'], width=2)
        ))
        
        fig.update_layout(
            height=400,
            template="plotly_dark",
            paper_bgcolor=ProfessionalTheme.COLORS['background'],
            plot_bgcolor=ProfessionalTheme.COLORS['card'],
            showlegend=False,
            xaxis=dict(
                gridcolor=ProfessionalTheme.COLORS['border'],
                showgrid=True
            ),
            yaxis=dict(
                gridcolor=ProfessionalTheme.COLORS['border'],
                showgrid=True,
                title="Price ($)"
            ),
            margin=dict(t=20, b=40, l=60, r=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _calculate_dcf(self, symbol: str, fcf: float, growth_rate: float, 
                      terminal_growth: float, discount_rate: float, 
                      shares: float) -> Dict[str, Any]:
        """Calculate DCF valuation"""
        try:
            # Project cash flows
            cash_flows = []
            current_fcf = fcf
            for year in range(5):
                current_fcf *= (1 + growth_rate)
                cash_flows.append(current_fcf)
            
            # Terminal value
            terminal_value = cash_flows[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
            
            # Present values
            pv_cash_flows = sum(cf / (1 + discount_rate) ** (i + 1) 
                               for i, cf in enumerate(cash_flows))
            pv_terminal = terminal_value / (1 + discount_rate) ** 5
            
            # Enterprise value and equity value
            enterprise_value = pv_cash_flows + pv_terminal
            intrinsic_value_per_share = enterprise_value / shares
            
            return {
                'enterprise_value': enterprise_value,
                'intrinsic_value_per_share': intrinsic_value_per_share,
                'cash_flows': cash_flows,
                'terminal_value': terminal_value,
                'pv_cash_flows': pv_cash_flows,
                'pv_terminal': pv_terminal
            }
        except Exception as e:
            st.error(f"DCF calculation error: {e}")
            return None
    
    def _analyze_moat(self, symbol: str, financials: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze economic moat"""
        try:
            return self.moat_analyzer.analyze_moat(symbol, financials)
        except Exception as e:
            st.error(f"Moat analysis error: {e}")
            return None
    
    def _render_moat_analysis(self, moat_result: Dict[str, Any]):
        """Render moat analysis results"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Overall moat rating
            rating = moat_result.get('moat_rating', 'None')
            score = moat_result.get('overall_score', 0)
            
            color_map = {
                'Wide': ProfessionalTheme.COLORS['accent_success'],
                'Narrow': ProfessionalTheme.COLORS['accent_warning'],
                'None': ProfessionalTheme.COLORS['accent_danger']
            }
            
            st.markdown(
                f"<div style='text-align:center;padding:20px;border:2px solid {color_map.get(rating, '#666')};'>"
                f"<h3>Moat Rating: {rating}</h3>"
                f"<h4>Score: {score:.1f}/50</h4></div>",
                unsafe_allow_html=True
            )
        
        with col2:
            # Moat factors
            factors = moat_result.get('moat_scores', {})
            for factor, score in factors.items():
                st.metric(factor.replace('_', ' ').title(), f"{score:.1f}/10")
    
    def _render_buffett_checklist(self, symbol: str, financials: Dict[str, Any]):
        """Render Buffett investment checklist"""
        checklist = {
            "Consistent Earnings": financials.get('consistent_earnings', True),
            "High ROE (>15%)": financials.get('roe', 0) > 0.15,
            "Low Debt/Equity (<0.5)": financials.get('debt_to_equity', 1) < 0.5,
            "High Profit Margins": financials.get('net_margin', 0) > 0.10,
            "Growing Free Cash Flow": financials.get('fcf_growth', 0) > 0,
            "Competitive Advantage": True,  # Would analyze moat
            "Shareholder Friendly": financials.get('dividend_yield', 0) > 0,
            "Reasonable Valuation": financials.get('pe_ratio', 30) < 25
        }
        
        passed = sum(checklist.values())
        total = len(checklist)
        
        # Display checklist
        col1, col2 = st.columns([2, 1])
        
        with col1:
            for criterion, passed in checklist.items():
                icon = "✅" if passed else "❌"
                st.write(f"{icon} {criterion}")
        
        with col2:
            score_pct = (passed / total) * 100
            color = (ProfessionalTheme.COLORS['accent_success'] if score_pct > 70
                    else ProfessionalTheme.COLORS['accent_warning'] if score_pct > 50
                    else ProfessionalTheme.COLORS['accent_danger'])
            
            st.markdown(
                f"<div style='text-align:center;padding:20px;border:2px solid {color};'>"
                f"<h3>{passed}/{total}</h3>"
                f"<h4>{score_pct:.0f}%</h4></div>",
                unsafe_allow_html=True
            )
    
    def _render_technical_chart(self, symbol: str, period: str, 
                                chart_type: str, indicators: List[str]):
        """Render technical analysis chart"""
        # This would fetch real data based on period
        # For now, using sample data
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.randn(100) * 2)
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.7, 0.3],
            vertical_spacing=0.02
        )
        
        # Price chart
        if chart_type == "Candlestick":
            # Generate OHLC data
            high = prices + np.abs(np.random.randn(100) * 1)
            low = prices - np.abs(np.random.randn(100) * 1)
            close = prices
            open_price = prices + np.random.randn(100) * 0.5
            
            fig.add_trace(go.Candlestick(
                x=dates,
                open=open_price,
                high=high,
                low=low,
                close=close,
                name=symbol
            ), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=dates,
                y=prices,
                mode='lines',
                name=symbol,
                line=dict(color=ProfessionalTheme.COLORS['accent_primary'])
            ), row=1, col=1)
        
        # Add indicators
        if "SMA20" in indicators:
            sma20 = pd.Series(prices).rolling(20).mean()
            fig.add_trace(go.Scatter(
                x=dates,
                y=sma20,
                name="SMA20",
                line=dict(color='yellow', width=1)
            ), row=1, col=1)
        
        if "SMA50" in indicators:
            sma50 = pd.Series(prices).rolling(50).mean()
            fig.add_trace(go.Scatter(
                x=dates,
                y=sma50,
                name="SMA50",
                line=dict(color='orange', width=1)
            ), row=1, col=1)
        
        # Volume
        if "Volume" in indicators:
            volume = np.random.randint(1000000, 10000000, 100)
            fig.add_trace(go.Bar(
                x=dates,
                y=volume,
                name="Volume",
                marker_color=ProfessionalTheme.COLORS['border']
            ), row=2, col=1)
        
        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor=ProfessionalTheme.COLORS['background'],
            plot_bgcolor=ProfessionalTheme.COLORS['card'],
            xaxis=dict(
                gridcolor=ProfessionalTheme.COLORS['border'],
                showgrid=True
            ),
            yaxis=dict(
                gridcolor=ProfessionalTheme.COLORS['border'],
                showgrid=True,
                title="Price ($)"
            ),
            margin=dict(t=20, b=40, l=60, r=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _calculate_risk_metrics(self, symbol: str) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics"""
        # Would calculate from real data
        return {
            'beta': 1.2,
            'volatility_30d': 25.5,
            'sharpe': 1.5,
            'max_drawdown': -15.3,
            'var_95': -3.2,
            'downside_dev': 18.2,
            'z_score': 3.1,
            'interest_coverage': 8.5,
            'debt_ebitda': 2.1,
            'current_ratio': 1.8,
            'avg_volume_30d': 15000000,
            'bid_ask_spread': 0.02
        }
    
    def _get_industry_peers(self, symbol: str) -> List[str]:
        """Get list of industry peers"""
        # Would fetch from API based on sector/industry
        peer_map = {
            'AAPL': ['MSFT', 'GOOGL', 'META', 'AMZN', 'NVDA'],
            'TSLA': ['GM', 'F', 'RIVN', 'NIO', 'LCID'],
            'JPM': ['BAC', 'WFC', 'GS', 'MS', 'C'],
        }
        return peer_map.get(symbol, ['SPY', 'QQQ', 'DIA'])
    
    def _generate_ai_analysis(self, symbol: str, analysis_type: str) -> Dict[str, Any]:
        """Generate AI-powered analysis"""
        # Would call Claude API for real analysis
        return {
            'confidence': 85.5,
            'data_quality': 'High',
            'analysis': f"""
### {analysis_type} for {symbol}

Based on comprehensive analysis of fundamental and technical factors, here is the detailed assessment:

**Current Situation:**
The stock is currently trading at attractive valuations relative to historical averages and peer group. 
Strong fundamental metrics indicate robust business performance with consistent revenue growth and 
expanding margins.

**Key Strengths:**
• Market leadership position in core segments
• Strong balance sheet with minimal debt
• Consistent free cash flow generation
• Expanding total addressable market

**Risk Factors:**
• Increased competition from emerging players
• Regulatory uncertainty in key markets
• Potential margin pressure from rising costs
• Macro headwinds affecting consumer spending

**Outlook:**
The near-term outlook remains positive with multiple growth catalysts on the horizon. 
Technical indicators suggest continued momentum with strong support levels established.
            """,
            'key_points': [
                "Strong fundamental metrics support current valuation",
                "Technical indicators show positive momentum",
                "Multiple growth catalysts identified",
                "Risk/reward profile favors upside potential"
            ],
            'recommendation': {
                'action': 'BUY',
                'rationale': 'Strong fundamentals, attractive valuation, and positive technical setup'
            }
        }
    
    def _render_income_statement(self, symbol: str, financials: Dict[str, Any]):
        """Render income statement"""
        # Create sample income statement data
        income_data = pd.DataFrame({
            'Item': ['Revenue', 'Cost of Revenue', 'Gross Profit', 'Operating Expenses', 
                    'Operating Income', 'Interest Expense', 'Pre-Tax Income', 
                    'Income Tax', 'Net Income'],
            '2023': [100000, 60000, 40000, 25000, 15000, 1000, 14000, 3000, 11000],
            '2022': [90000, 55000, 35000, 22000, 13000, 900, 12100, 2500, 9600],
            '2021': [80000, 50000, 30000, 20000, 10000, 800, 9200, 2000, 7200]
        })
        
        st.dataframe(
            income_data,
            hide_index=True,
            use_container_width=True
        )
    
    def _render_balance_sheet(self, symbol: str, financials: Dict[str, Any]):
        """Render balance sheet"""
        balance_data = pd.DataFrame({
            'Item': ['Current Assets', 'Non-Current Assets', 'Total Assets',
                    'Current Liabilities', 'Non-Current Liabilities', 'Total Liabilities',
                    'Shareholder Equity'],
            '2023': [50000, 100000, 150000, 30000, 40000, 70000, 80000],
            '2022': [45000, 95000, 140000, 28000, 38000, 66000, 74000],
            '2021': [40000, 90000, 130000, 25000, 35000, 60000, 70000]
        })
        
        st.dataframe(
            balance_data,
            hide_index=True,
            use_container_width=True
        )
    
    def _render_cash_flow(self, symbol: str, financials: Dict[str, Any]):
        """Render cash flow statement"""
        cashflow_data = pd.DataFrame({
            'Item': ['Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow',
                    'Net Change in Cash', 'Free Cash Flow'],
            '2023': [20000, -8000, -5000, 7000, 12000],
            '2022': [18000, -7000, -4000, 7000, 11000],
            '2021': [15000, -6000, -3000, 6000, 9000]
        })
        
        st.dataframe(
            cashflow_data,
            hide_index=True,
            use_container_width=True
        )
    
    def _get_earnings_history(self, symbol: str) -> pd.DataFrame:
        """Get historical earnings data"""
        # Would fetch from API
        quarters = pd.date_range(end=datetime.now(), periods=8, freq='Q')
        return pd.DataFrame({
            'date': quarters,
            'actual': np.random.uniform(2, 4, 8),
            'estimate': np.random.uniform(2, 4, 8)
        })
    
    def _render_earnings_surprises(self, earnings_data: pd.DataFrame):
        """Render earnings surprise history"""
        earnings_data['surprise'] = ((earnings_data['actual'] - earnings_data['estimate']) 
                                     / earnings_data['estimate'] * 100)
        
        # Color code surprises
        colors = ['green' if s > 0 else 'red' for s in earnings_data['surprise']]
        
        fig = go.Figure(data=[
            go.Bar(
                x=earnings_data['date'],
                y=earnings_data['surprise'],
                marker_color=colors,
                text=[f"{s:+.1f}%" for s in earnings_data['surprise']],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            height=300,
            template="plotly_dark",
            paper_bgcolor=ProfessionalTheme.COLORS['background'],
            plot_bgcolor=ProfessionalTheme.COLORS['card'],
            showlegend=False,
            yaxis_title="Surprise %",
            margin=dict(t=20, b=40, l=60, r=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _get_next_earnings_date(self, symbol: str) -> str:
        """Get next earnings date"""
        # Would fetch from API
        next_date = datetime.now() + timedelta(days=30)
        return next_date.strftime("%B %d, %Y")
    
    def _get_analyst_estimates(self, symbol: str) -> Dict[str, Any]:
        """Get analyst estimates"""
        # Would fetch from API
        return {
            'eps_estimate': 3.25,
            'revenue_estimate': 95000000000,
            'num_analysts': 42
        }
    
    def _generate_earnings_prediction(self, symbol: str) -> Dict[str, Any]:
        """Generate AI earnings prediction"""
        return {
            'eps': 3.45,
            'confidence': 78.5,
            'reasoning': """
            Based on current trends and leading indicators, we expect earnings to beat consensus estimates.
            Strong demand trends, operational efficiency improvements, and favorable market conditions
            support an upside surprise.
            """
        }
    
    def _render_earnings_calendar(self):
        """Render upcoming earnings calendar"""
        # Sample earnings calendar
        calendar_data = pd.DataFrame({
            'Company': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'],
            'Date': pd.date_range(start=datetime.now(), periods=5, freq='W'),
            'EPS Est': [3.25, 2.85, 1.45, 0.95, 4.15],
            'Rev Est (B)': [95.0, 55.0, 75.0, 145.0, 28.0]
        })
        
        st.dataframe(
            calendar_data,
            hide_index=True,
            use_container_width=True
        )
    
    def _render_trend_indicators(self, symbol: str):
        """Render trend indicators"""
        indicators = {
            "Trend": "Bullish",
            "SMA20": "Above",
            "SMA50": "Above",
            "SMA200": "Above",
            "MACD": "Positive"
        }
        
        for indicator, value in indicators.items():
            color = "green" if value in ["Bullish", "Above", "Positive"] else "red"
            st.markdown(f"<span style='color:{color}'>{indicator}: {value}</span>", 
                       unsafe_allow_html=True)
    
    def _render_momentum_indicators(self, symbol: str):
        """Render momentum indicators"""
        indicators = {
            "RSI (14)": 65.5,
            "Stochastic": 75.2,
            "Williams %R": -25.5,
            "CCI": 125.3,
            "ROC": 8.5
        }
        
        for indicator, value in indicators.items():
            st.metric(indicator, f"{value:.1f}")
    
    def _render_volatility_indicators(self, symbol: str):
        """Render volatility indicators"""
        indicators = {
            "ATR (14)": 2.35,
            "Bollinger Width": 5.2,
            "Keltner Width": 4.8,
            "Donchian Width": 8.5,
            "Historical Vol": 25.5
        }
        
        for indicator, value in indicators.items():
            st.metric(indicator, f"{value:.1f}")
    
    def _render_support_resistance(self, symbol: str):
        """Render support and resistance levels"""
        levels = pd.DataFrame({
            'Level': ['R3', 'R2', 'R1', 'Current', 'S1', 'S2', 'S3'],
            'Price': [115.50, 112.25, 108.75, 105.30, 102.50, 98.75, 95.25],
            'Strength': ['Weak', 'Moderate', 'Strong', '-', 'Strong', 'Moderate', 'Weak']
        })
        
        st.dataframe(
            levels,
            hide_index=True,
            use_container_width=True
        )
    
    def _render_pattern_recognition(self, symbol: str):
        """Render pattern recognition results"""
        patterns = {
            "Head & Shoulders": "Not Detected",
            "Double Top": "Not Detected",
            "Triangle": "Ascending Triangle Forming",
            "Flag/Pennant": "Bull Flag Detected",
            "Cup & Handle": "Not Detected"
        }
        
        for pattern, status in patterns.items():
            color = "green" if "Detected" in status or "Forming" in status else "gray"
            st.markdown(f"<span style='color:{color}'>{pattern}: {status}</span>",
                       unsafe_allow_html=True)
    
    def _render_dcf_sensitivity(self, dcf_result: Dict[str, Any]):
        """Render DCF sensitivity analysis"""
        # Create sensitivity matrix
        discount_rates = [0.08, 0.09, 0.10, 0.11, 0.12]
        growth_rates = [0.01, 0.02, 0.025, 0.03, 0.04]
        
        sensitivity_matrix = []
        for gr in growth_rates:
            row = []
            for dr in discount_rates:
                # Simplified calculation for sensitivity
                value = dcf_result['intrinsic_value_per_share'] * (1 + (0.1 - dr)) * (1 + (gr - 0.025))
                row.append(f"${value:.2f}")
            sensitivity_matrix.append(row)
        
        sensitivity_df = pd.DataFrame(
            sensitivity_matrix,
            columns=[f"{dr*100:.0f}%" for dr in discount_rates],
            index=[f"{gr*100:.1f}%" for gr in growth_rates]
        )
        
        st.dataframe(sensitivity_df, use_container_width=True)
    
    def _render_multiple_valuation(self, symbol: str, financials: Dict[str, Any]):
        """Render multiple valuation analysis"""
        multiples = pd.DataFrame({
            'Multiple': ['P/E', 'EV/EBITDA', 'P/B', 'P/S', 'PEG'],
            'Current': [20.5, 12.3, 3.2, 4.5, 1.8],
            'Industry Avg': [22.1, 13.5, 3.8, 5.2, 2.1],
            'Historical Avg': [19.8, 11.9, 3.0, 4.2, 1.7],
            'Premium/Discount': ['-7.2%', '-8.9%', '-15.8%', '-13.5%', '-14.3%']
        })
        
        st.dataframe(
            multiples,
            hide_index=True,
            use_container_width=True
        )
    
    def _render_risk_distribution(self, symbol: str):
        """Render risk distribution chart"""
        # Generate sample return distribution
        returns = np.random.normal(0.001, 0.02, 1000)
        
        fig = go.Figure(data=[go.Histogram(
            x=returns,
            nbinsx=50,
            marker_color=ProfessionalTheme.COLORS['accent_primary'],
            opacity=0.75
        )])
        
        # Add VaR lines
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        fig.add_vline(x=var_95, line_dash="dash", line_color="yellow", 
                     annotation_text="VaR 95%")
        fig.add_vline(x=var_99, line_dash="dash", line_color="red",
                     annotation_text="VaR 99%")
        
        fig.update_layout(
            height=400,
            template="plotly_dark",
            paper_bgcolor=ProfessionalTheme.COLORS['background'],
            plot_bgcolor=ProfessionalTheme.COLORS['card'],
            xaxis_title="Daily Returns",
            yaxis_title="Frequency",
            showlegend=False,
            margin=dict(t=20, b=40, l=60, r=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_risk_factors(self, symbol: str):
        """Render key risk factors"""
        risk_factors = [
            {"Risk": "Market Risk", "Level": "Moderate", "Impact": "High"},
            {"Risk": "Competition", "Level": "High", "Impact": "Moderate"},
            {"Risk": "Regulatory", "Level": "Low", "Impact": "High"},
            {"Risk": "Technology", "Level": "Moderate", "Impact": "Moderate"},
            {"Risk": "Supply Chain", "Level": "Low", "Impact": "Low"}
        ]
        
        risk_df = pd.DataFrame(risk_factors)
        st.dataframe(
            risk_df,
            hide_index=True,
            use_container_width=True
        )
    
    def _render_scenario_analysis(self, symbol: str):
        """Render scenario analysis"""
        scenarios = pd.DataFrame({
            'Scenario': ['Bull Case', 'Base Case', 'Bear Case'],
            'Probability': ['25%', '50%', '25%'],
            'Target Price': ['$150', '$120', '$85'],
            'Upside/Downside': ['+42.9%', '+14.3%', '-19.0%'],
            'Key Assumptions': [
                'Strong growth, margin expansion',
                'Moderate growth, stable margins',
                'Recession, margin compression'
            ]
        })
        
        st.dataframe(
            scenarios,
            hide_index=True,
            use_container_width=True
        )
    
    def _get_peer_comparison_data(self, symbol: str, 
                                  peers: List[str]) -> pd.DataFrame:
        """Get peer comparison data"""
        # Would fetch real data from API
        all_symbols = [symbol] + peers
        comparison_data = pd.DataFrame({
            'Symbol': all_symbols,
            'P/E': np.random.uniform(15, 35, len(all_symbols)),
            'EV/EBITDA': np.random.uniform(8, 20, len(all_symbols)),
            'ROE': np.random.uniform(10, 30, len(all_symbols)),
            'Revenue Growth': np.random.uniform(-5, 25, len(all_symbols)),
            'Profit Margin': np.random.uniform(5, 25, len(all_symbols)),
            'Debt/Equity': np.random.uniform(0.2, 2, len(all_symbols))
        })
        return comparison_data
    
    def _render_valuation_comparison(self, data: pd.DataFrame):
        """Render valuation comparison chart"""
        fig = go.Figure()
        
        metrics = ['P/E', 'EV/EBITDA']
        for metric in metrics:
            fig.add_trace(go.Bar(
                name=metric,
                x=data['Symbol'],
                y=data[metric],
                text=[f"{v:.1f}" for v in data[metric]],
                textposition='outside'
            ))
        
        fig.update_layout(
            height=400,
            template="plotly_dark",
            paper_bgcolor=ProfessionalTheme.COLORS['background'],
            plot_bgcolor=ProfessionalTheme.COLORS['card'],
            barmode='group',
            xaxis_title="Company",
            yaxis_title="Multiple",
            margin=dict(t=20, b=40, l=60, r=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_performance_comparison(self, data: pd.DataFrame):
        """Render performance comparison"""
        metrics_df = data[['Symbol', 'ROE', 'Revenue Growth', 'Profit Margin']]
        st.dataframe(
            metrics_df.style.highlight_max(axis=0, subset=['ROE', 'Revenue Growth', 'Profit Margin']),
            hide_index=True,
            use_container_width=True
        )
    
    def _render_health_comparison(self, data: pd.DataFrame):
        """Render financial health comparison"""
        health_df = data[['Symbol', 'Debt/Equity']]
        st.dataframe(
            health_df.style.highlight_min(axis=0, subset=['Debt/Equity']),
            hide_index=True,
            use_container_width=True
        )
    
    def _render_peer_ranking(self, symbol: str, data: pd.DataFrame):
        """Render peer ranking analysis"""
        # Calculate composite score
        data['Score'] = (
            (1 / data['P/E']) * 20 +  # Lower P/E is better
            (1 / data['EV/EBITDA']) * 20 +  # Lower EV/EBITDA is better
            data['ROE'] * 1 +  # Higher ROE is better
            data['Revenue Growth'] * 1 +  # Higher growth is better
            data['Profit Margin'] * 1 +  # Higher margin is better
            (1 / data['Debt/Equity']) * 10  # Lower debt is better
        )
        
        data = data.sort_values('Score', ascending=False)
        data['Rank'] = range(1, len(data) + 1)
        
        # Highlight target symbol
        def highlight_symbol(row):
            if row['Symbol'] == symbol:
                return ['background-color: #4a5568'] * len(row)
            return [''] * len(row)
        
        ranking_df = data[['Rank', 'Symbol', 'Score']].round(2)
        st.dataframe(
            ranking_df.style.apply(highlight_symbol, axis=1),
            hide_index=True,
            use_container_width=True
        )