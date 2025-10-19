"""
Trinity 3.0 - Main Streamlit Application
Professional Financial Intelligence Platform
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
from typing import Dict, Any, List, Optional
import json

# Import Trinity components
from services.openbb_service import OpenBBService
from services.prediction_service import PredictionService
from agents.macro_agent import MacroAgent
from agents.equity_agent import EquityAgent
from agents.market_agent import MarketAgent
from ui.intelligent_router import IntelligentRouter
from ui.visualizations import TrinityVisualizations

# Configure Streamlit
st.set_page_config(
    page_title="Trinity 3.0 - Financial Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main {
        padding: 0rem 0rem;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
        padding: 10px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .prediction-card {
        background: #f7f7f7;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    .agent-response {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 15px 0;
    }
    h1 {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 48px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class Trinity3App:
    """Main Trinity 3.0 Application"""
    
    def __init__(self):
        """Initialize Trinity application"""
        self.initialize_services()
        self.initialize_agents()
        self.router = IntelligentRouter(self.agents)
        self.viz = TrinityVisualizations()
        
    def initialize_services(self):
        """Initialize core services"""
        try:
            self.openbb = OpenBBService()
            self.prediction_service = PredictionService()
        except Exception as e:
            st.error(f"Failed to initialize services: {str(e)}")
            st.info("Please ensure OpenBB is installed: pip install openbb")
            st.stop()
    
    def initialize_agents(self):
        """Initialize the three core agents"""
        self.agents = {
            'macro': MacroAgent(),
            'equity': EquityAgent(),
            'market': MarketAgent()
        }
    
    def render_header(self):
        """Render application header"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<h1 style='text-align: center'>Trinity 3.0</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 18px; color: #666'>Professional Financial Intelligence Platform</p>", unsafe_allow_html=True)
    
    def render_search_bar(self) -> str:
        """Render the main search/query bar"""
        query = st.text_input(
            "Search",
            placeholder="Ask anything about markets, stocks, or economics... (e.g., 'What's the recession risk?', 'Analyze NVDA', 'Show sector rotation')",
            key="main_search",
            label_visibility="collapsed"
        )
        return query
    
    def render_quick_actions(self):
        """Render quick action buttons"""
        st.markdown("### 🚀 Quick Actions")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("📉 Recession Risk", use_container_width=True):
                st.session_state['query'] = "What's the recession risk?"
        
        with col2:
            if st.button("📊 Market Breadth", use_container_width=True):
                st.session_state['query'] = "Analyze market breadth"
        
        with col3:
            if st.button("🔄 Sector Rotation", use_container_width=True):
                st.session_state['query'] = "Show sector rotation"
        
        with col4:
            if st.button("💹 Fed Impact", use_container_width=True):
                st.session_state['query'] = "Analyze Fed policy impact"
        
        with col5:
            if st.button("📈 Top Stocks", use_container_width=True):
                st.session_state['query'] = "Show top performing stocks"
    
    def render_market_overview(self):
        """Render market overview dashboard"""
        st.markdown("### 📊 Market Overview")
        
        # Get market data
        try:
            spy = self.openbb.get_equity_quote('SPY')
            qqq = self.openbb.get_equity_quote('QQQ')
            dia = self.openbb.get_equity_quote('DIA')
            vix = {'price': 18.5}  # Placeholder for VIX
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                spy_price = spy.get('results', [{}])[0].get('price', 0) if spy else 0
                spy_change = spy.get('results', [{}])[0].get('changesPercentage', 0) if spy else 0
                st.metric("S&P 500", f"${spy_price:.2f}", f"{spy_change:.2f}%")
            
            with col2:
                qqq_price = qqq.get('results', [{}])[0].get('price', 0) if qqq else 0
                qqq_change = qqq.get('results', [{}])[0].get('changesPercentage', 0) if qqq else 0
                st.metric("NASDAQ", f"${qqq_price:.2f}", f"{qqq_change:.2f}%")
            
            with col3:
                dia_price = dia.get('results', [{}])[0].get('price', 0) if dia else 0
                dia_change = dia.get('results', [{}])[0].get('changesPercentage', 0) if dia else 0
                st.metric("DOW", f"${dia_price:.2f}", f"{dia_change:.2f}%")
            
            with col4:
                st.metric("VIX", f"{vix['price']:.2f}", "Normal" if vix['price'] < 20 else "Elevated")
                
        except Exception as e:
            st.info("Market data loading...")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process user query through intelligent router"""
        with st.spinner("Analyzing your query..."):
            # Route query to appropriate agent(s)
            results = self.router.route_query(query)
            
            # Store predictions if any
            if 'predictions' in results:
                for prediction in results['predictions']:
                    self.store_prediction(prediction)
            
            return results
    
    def store_prediction(self, prediction: Dict):
        """Store prediction in database"""
        try:
            self.prediction_service.store_prediction(
                prediction_type=prediction.get('type', 'general'),
                prediction_data=prediction.get('data', {}),
                confidence=prediction.get('confidence', 50),
                target_date=prediction.get('target_date', ''),
                symbol=prediction.get('symbol'),
                agent=prediction.get('agent', 'unknown')
            )
        except Exception as e:
            st.error(f"Failed to store prediction: {str(e)}")
    
    def render_agent_responses(self, results: Dict[str, Any]):
        """Render responses from agents"""
        st.markdown("### 🤖 Analysis Results")
        
        # Create columns for each agent that responded
        agents_data = results.get('agents', {})
        
        if not agents_data:
            st.info("No analysis results available")
            return
        
        cols = st.columns(len(agents_data))
        
        for idx, (agent_name, agent_result) in enumerate(agents_data.items()):
            with cols[idx]:
                self.render_agent_card(agent_name, agent_result)
    
    def render_agent_card(self, agent_name: str, result: Dict[str, Any]):
        """Render individual agent result card"""
        # Agent header
        icon = {"macro": "🌍", "equity": "📈", "market": "📊"}.get(agent_name, "🤖")
        title = {"macro": "Macro Analysis", "equity": "Equity Analysis", "market": "Market Structure"}.get(agent_name, agent_name)
        
        st.markdown(f"#### {icon} {title}")
        
        # Render based on analysis type
        analysis_type = result.get('analysis_type', '')
        data = result.get('data', {})
        confidence = result.get('confidence', 0)
        
        # Confidence indicator
        confidence_color = "🟢" if confidence > 70 else "🟡" if confidence > 50 else "🔴"
        st.markdown(f"**Confidence**: {confidence_color} {confidence}%")
        
        # Render specific visualizations based on type
        if 'recession' in analysis_type:
            self.render_recession_analysis(data)
        elif 'valuation' in analysis_type:
            self.render_valuation_analysis(data)
        elif 'breadth' in analysis_type:
            self.render_breadth_analysis(data)
        elif 'prediction' in analysis_type:
            self.render_prediction(data)
        else:
            # Generic data rendering
            self.render_generic_analysis(data)
    
    def render_recession_analysis(self, data: Dict):
        """Render recession risk analysis"""
        probability = data.get('probability_6m', 0)
        
        # Gauge chart for recession probability
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=probability,
            title={'text': "Recession Risk (6M)"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkred" if probability > 60 else "orange" if probability > 30 else "green"},
                   'steps': [
                       {'range': [0, 30], 'color': "lightgreen"},
                       {'range': [30, 60], 'color': "lightyellow"},
                       {'range': [60, 100], 'color': "lightcoral"}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                                'thickness': 0.75, 'value': 75}}
        ))
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
        # Key risk factors
        if 'key_risks' in data:
            st.markdown("**Key Risk Factors:**")
            for factor, details in data['key_risks'].items():
                if isinstance(details, dict):
                    st.markdown(f"- **{factor}**: {details.get('signal', 'N/A')}")
    
    def render_valuation_analysis(self, data: Dict):
        """Render valuation analysis"""
        current_price = data.get('current_price', 0)
        fair_value = data.get('composite_fair_value', 0)
        upside = data.get('upside_potential', 0)
        
        # Valuation metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Price", f"${current_price:.2f}")
        with col2:
            st.metric("Fair Value", f"${fair_value:.2f}", f"{upside:.1f}% upside")
        
        # Recommendation
        if 'recommendation' in data:
            rec_color = "green" if "BUY" in data['recommendation'] else "red" if "SELL" in data['recommendation'] else "gray"
            st.markdown(f"<div style='padding: 10px; background-color: {rec_color}; color: white; border-radius: 5px; text-align: center'>{data['recommendation']}</div>", unsafe_allow_html=True)
    
    def render_breadth_analysis(self, data: Dict):
        """Render market breadth analysis"""
        if 'advance_decline' in data:
            ad = data['advance_decline']
            
            # A/D ratio visualization
            fig = go.Figure(data=[
                go.Bar(name='Advancing', x=['Stocks'], y=[ad.get('advancing', 0)], marker_color='green'),
                go.Bar(name='Declining', x=['Stocks'], y=[ad.get('declining', 0)], marker_color='red')
            ])
            fig.update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        
        # Market health indicator
        if 'market_health' in data:
            health = data['market_health']
            health_color = "green" if health == "Healthy" else "orange" if health == "Mixed" else "red"
            st.markdown(f"**Market Health**: <span style='color: {health_color}'>{health}</span>", unsafe_allow_html=True)
    
    def render_prediction(self, data: Dict):
        """Render prediction results"""
        st.markdown("**Prediction:**")
        
        if 'target' in data:
            st.markdown(f"- **Target**: {data['target']}")
        if 'horizon' in data:
            st.markdown(f"- **Horizon**: {data['horizon']}")
        if 'probability' in data:
            st.markdown(f"- **Probability**: {data['probability']}%")
        if 'confidence' in data:
            st.progress(data['confidence'] / 100)
    
    def render_generic_analysis(self, data: Dict):
        """Render generic analysis data"""
        # Convert dict to readable format
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (str, int, float)):
                    st.markdown(f"**{key.replace('_', ' ').title()}**: {value}")
                elif isinstance(value, dict):
                    with st.expander(f"{key.replace('_', ' ').title()}"):
                        st.json(value)
                elif isinstance(value, list) and len(value) > 0:
                    st.markdown(f"**{key.replace('_', ' ').title()}**:")
                    for item in value[:5]:  # Limit to 5 items
                        st.markdown(f"- {item}")
        else:
            st.write(data)
    
    def render_prediction_tracker(self):
        """Render prediction tracking section"""
        st.markdown("### 📮 Prediction Tracker")
        
        # Get recent predictions
        predictions = self.prediction_service.get_predictions(limit=10)
        
        if predictions:
            # Convert to DataFrame for display
            df = pd.DataFrame(predictions)
            
            # Select columns to display
            display_cols = ['created_at', 'prediction_type', 'symbol', 'confidence', 'status']
            available_cols = [col for col in display_cols if col in df.columns]
            
            if available_cols:
                st.dataframe(
                    df[available_cols],
                    use_container_width=True,
                    hide_index=True
                )
            
            # Show accuracy metrics
            accuracy_metrics = self.prediction_service.calculate_prediction_accuracy()
            if accuracy_metrics:
                st.markdown("**Prediction Accuracy:**")
                for metric in accuracy_metrics:
                    if isinstance(metric, dict):
                        st.metric(
                            metric.get('prediction_type', 'Unknown'),
                            f"{metric.get('avg_accuracy', 0):.1f}%",
                            f"({metric.get('total', 0)} predictions)"
                        )
        else:
            st.info("No predictions tracked yet. Make queries to start tracking!")
    
    def render_sidebar(self):
        """Render sidebar with additional controls"""
        with st.sidebar:
            st.markdown("## ⚙️ Settings")
            
            # Data provider selection
            st.selectbox(
                "Preferred Data Provider",
                ["Yahoo Finance (Free)", "FMP", "Polygon"],
                key="data_provider"
            )
            
            # Confidence threshold
            st.slider(
                "Minimum Confidence Threshold",
                0, 100, 60,
                key="confidence_threshold"
            )
            
            st.markdown("---")
            
            # Quick tools
            st.markdown("## 🛠️ Quick Tools")
            
            if st.button("🔄 Refresh Market Data"):
                st.rerun()
            
            if st.button("📊 Run Backtest"):
                st.session_state['show_backtest'] = True
            
            if st.button("🎲 Run Simulation"):
                st.session_state['show_simulation'] = True
            
            st.markdown("---")
            
            # About section
            st.markdown("## 📖 About")
            st.markdown("""
            **Trinity 3.0** is a professional financial intelligence platform powered by:
            - OpenBB data infrastructure
            - 3 specialized AI agents
            - Real-time market data
            - Predictive analytics
            - Backtesting engine
            
            Built with ❤️ using Streamlit
            """)
    
    def run(self):
        """Main application loop"""
        # Initialize session state
        if 'query' not in st.session_state:
            st.session_state['query'] = ""
        
        # Render UI components
        self.render_header()
        self.render_market_overview()
        
        st.markdown("---")
        
        # Search bar
        query = self.render_search_bar()
        
        # Quick actions
        self.render_quick_actions()
        
        st.markdown("---")
        
        # Process query if exists
        if query or st.session_state.get('query'):
            query = query or st.session_state.get('query', '')
            if query:
                results = self.process_query(query)
                self.render_agent_responses(results)
                st.session_state['query'] = ""  # Clear after processing
        
        st.markdown("---")
        
        # Prediction tracker
        with st.expander("📮 Prediction Tracker", expanded=False):
            self.render_prediction_tracker()
        
        # Sidebar
        self.render_sidebar()
        
        # Handle special modes
        if st.session_state.get('show_backtest'):
            self.render_backtest_modal()
        
        if st.session_state.get('show_simulation'):
            self.render_simulation_modal()
    
    def render_backtest_modal(self):
        """Render backtesting interface"""
        with st.container():
            st.markdown("### 📊 Backtest Strategy")
            
            col1, col2 = st.columns(2)
            
            with col1:
                symbol = st.text_input("Symbol", "SPY")
                strategy = st.selectbox("Strategy", ["momentum", "mean_reversion", "breakout"])
            
            with col2:
                start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
                end_date = st.date_input("End Date", datetime.now())
            
            if st.button("Run Backtest"):
                with st.spinner("Running backtest..."):
                    # Run backtest through EquityAgent
                    results = self.agents['equity'].backtest_strategy(
                        symbol, strategy, 
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    # Display results
                    if 'metrics' in results:
                        metrics = results['metrics']
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Return", f"{metrics.get('total_return', 0):.2f}%")
                        with col2:
                            st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
                        with col3:
                            st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0):.2f}%")
                        
                        # Plot equity curve
                        if 'equity_curve' in results:
                            df = pd.DataFrame(results['equity_curve'])
                            fig = px.line(df, x='date', y='value', title='Equity Curve')
                            st.plotly_chart(fig, use_container_width=True)
            
            if st.button("Close"):
                st.session_state['show_backtest'] = False
                st.rerun()
    
    def render_simulation_modal(self):
        """Render Monte Carlo simulation interface"""
        with st.container():
            st.markdown("### 🎲 Monte Carlo Simulation")
            
            symbol = st.text_input("Symbol (or 'Market' for index)", "AAPL")
            
            if st.button("Run Simulation"):
                with st.spinner("Running simulations..."):
                    if symbol.lower() == 'market':
                        results = self.agents['market'].simulate_market_scenarios()
                    else:
                        results = self.agents['equity'].simulate_price_scenarios(symbol)
                    
                    # Display results
                    if 'data' in results and 'results' in results['data']:
                        scenarios = results['data']['results']
                        
                        # Create scenario comparison
                        df = pd.DataFrame(scenarios)
                        
                        fig = go.Figure()
                        for scenario in scenarios:
                            fig.add_trace(go.Bar(
                                name=scenario['scenario'],
                                x=['Mean', '5th Percentile', '95th Percentile'],
                                y=[scenario['mean'], scenario['percentile_5'], scenario['percentile_95']]
                            ))
                        
                        fig.update_layout(title='Scenario Analysis', barmode='group')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show probability table
                        st.dataframe(df, use_container_width=True)
            
            if st.button("Close"):
                st.session_state['show_simulation'] = False
                st.rerun()

# Main entry point
if __name__ == "__main__":
    app = Trinity3App()
    app.run()