"""
Trinity 3.0 - Main Streamlit Application
Professional Financial Intelligence Platform
"""

# Load environment variables from .env file (if it exists)
from dotenv import load_dotenv
load_dotenv()  # Automatically loads .env from current directory

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
from typing import Dict, Any, List, Optional
import json

# Import Trinity 3.0 components
from services.openbb_service import OpenBBService
from services.prediction_service import PredictionService

# Trinity 3.0 core architecture
from core.universal_executor import UniversalExecutor
from core.agent_runtime import AgentRuntime
from core.agent_adapter import AgentRegistry
from core.knowledge_graph import KnowledgeGraph
from intelligence.enhanced_chat_processor import EnhancedChatProcessor

# DawsOS agents
from agents import FinancialAnalyst, Claude

# UI components
from ui.visualizations import TrinityVisualizations
from ui.professional_theme import ProfessionalTheme  # Trinity 3.0 Professional Theme

# Configure Streamlit
st.set_page_config(
    page_title="Trinity | Professional Financial Intelligence",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply Trinity 3.0 Professional Theme (Bloomberg Terminal style)
# This replaces the old custom CSS with a sophisticated, minimal design
ProfessionalTheme.apply_theme()

class Trinity3App:
    """
    DawsOS Main Application (Trinity 3.0 Architecture)

    Trinity 3.0 is the execution framework version.
    DawsOS is the product name.

    This class implements the Trinity 3.0 architecture for DawsOS,
    providing pattern-driven financial intelligence with real-time data.
    """

    def __init__(self):
        """Initialize DawsOS application with Trinity 3.0 architecture"""
        self.initialize_services()
        self.initialize_trinity()
        self.viz = TrinityVisualizations()

    def initialize_services(self):
        """Initialize core services (optional - Trinity 3.0 works without them)"""
        # OpenBB Service (optional - for market data dashboard)
        try:
            self.openbb = OpenBBService()
        except Exception as e:
            st.warning(f"OpenBB service not available: {str(e)}")
            st.info("Trinity 3.0 will work without OpenBB. Install for market data: pip install openbb")
            self.openbb = None

        # Prediction Service (optional - for prediction tracking)
        try:
            self.prediction_service = PredictionService()
        except Exception as e:
            st.warning(f"Prediction service using in-memory storage: {str(e)}")
            self.prediction_service = None

    def initialize_trinity(self):
        """Initialize Trinity 3.0 execution stack"""
        # Initialize knowledge graph
        self.graph = KnowledgeGraph()

        # Initialize agent runtime
        self.runtime = AgentRuntime()
        self.runtime.graph = self.graph

        # Register DawsOS agents
        fa = FinancialAnalyst(graph=self.graph)
        self.runtime.register_agent('financial_analyst', fa,
                                   {'capabilities': fa.capabilities if hasattr(fa, 'capabilities') else []})

        claude = Claude(graph=self.graph)
        self.runtime.register_agent('claude', claude,
                                   {'capabilities': claude.capabilities if hasattr(claude, 'capabilities') else []})

        # Register 4 additional agents (from AGENT_CAPABILITIES)
        from agents.data_harvester import DataHarvester
        from agents.forecast_dreamer import ForecastDreamer
        from agents.graph_mind import GraphMind
        from agents.pattern_spotter import PatternSpotter

        dh = DataHarvester(graph=self.graph)
        self.runtime.register_agent('data_harvester', dh, {
            'capabilities': [
                'can_fetch_stock_quotes', 'can_fetch_economic_data', 'can_fetch_news',
                'can_fetch_fundamentals', 'can_fetch_market_movers', 'can_fetch_crypto_data',
                'can_calculate_correlations', 'can_fetch_options_flow', 'can_fetch_unusual_options'
            ]
        })

        fd = ForecastDreamer(graph=self.graph)
        self.runtime.register_agent('forecast_dreamer', fd, {
            'capabilities': [
                'can_generate_forecasts', 'can_project_trends', 'can_estimate_probabilities',
                'can_predict_outcomes', 'can_calculate_confidence', 'can_model_scenarios'
            ]
        })

        gm = GraphMind(graph=self.graph)
        self.runtime.register_agent('graph_mind', gm, {
            'capabilities': [
                'can_manage_graph_structure', 'can_query_relationships', 'can_add_nodes',
                'can_connect_nodes', 'can_traverse_graph', 'can_analyze_graph_topology', 'can_find_paths'
            ]
        })

        ps = PatternSpotter(graph=self.graph)
        self.runtime.register_agent('pattern_spotter', ps, {
            'capabilities': [
                'can_detect_patterns', 'can_analyze_trends', 'can_find_anomalies',
                'can_detect_sequences', 'can_find_cycles', 'can_identify_triggers',
                'can_analyze_macro_trends', 'can_detect_market_regime'
            ]
        })

        # Initialize universal executor
        registry = AgentRegistry()
        self.executor = UniversalExecutor(
            graph=self.graph,
            registry=registry,
            runtime=self.runtime,
            auto_save=False
        )

        # Initialize enhanced chat processor (intelligence layer)
        # Note: EnhancedChatProcessor needs pattern_engine and runtime
        from core.pattern_engine import PatternEngine
        pattern_engine = PatternEngine(runtime=self.runtime, graph=self.graph)
        self.chat_processor = EnhancedChatProcessor(pattern_engine, self.runtime)
    
    def render_header(self):
        """Render application header using Professional Theme"""
        ProfessionalTheme.render_header(
            title="TRINITY",
            subtitle="Institutional-Grade Financial Intelligence"
        )
    
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
        """Render enhanced quick action buttons with categorical organization"""
        st.markdown("### Quick Actions")

        # Create categorical tabs for better organization
        action_tabs = st.tabs(["Economic", "Market", "Analysis"])

        # Tab 1: Economic Analysis
        with action_tabs[0]:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Dalio Cycle Analysis**")
                st.caption("Analyze short-term and long-term debt cycles")
                if st.button("Run Dalio Analysis", key="dalio", use_container_width=True):
                    st.session_state['query'] = "Analyze debt cycles using Ray Dalio framework"

            with col2:
                st.markdown("**Recession Risk Assessment**")
                st.caption("Assess recession probability across indicators")
                if st.button("Run Recession Analysis", key="recession", use_container_width=True):
                    st.session_state['query'] = "What's the recession risk using Dalio framework?"

            with col3:
                st.markdown("**Housing Market Cycle**")
                st.caption("Analyze housing and credit cycle position")
                if st.button("Run Housing Analysis", key="housing", use_container_width=True):
                    st.session_state['query'] = "Analyze housing and credit cycle"

            col4, col5, col6 = st.columns(3)

            with col4:
                st.markdown("**Federal Reserve Policy**")
                st.caption("Analyze Fed policy stance and impact")
                if st.button("Run Fed Analysis", key="fed", use_container_width=True):
                    st.session_state['query'] = "Analyze Fed policy impact"

            with col5:
                st.markdown("**Empire State Analysis**")
                st.caption("Assess US empire cycle position")
                if st.button("Run Empire Analysis", key="empire", use_container_width=True):
                    st.session_state['query'] = "Analyze US empire cycle position"

            with col6:
                st.markdown("**Economic Outlook**")
                st.caption("Multi-timeframe economic forecast")
                if st.button("Run Economic Outlook", key="outlook", use_container_width=True):
                    st.session_state['query'] = "Multi-timeframe economic outlook"

        # Tab 2: Market Analysis
        with action_tabs[1]:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Market Breadth**")
                st.caption("Analyze advance/decline and market internals")
                if st.button("Run Breadth Analysis", key="breadth", use_container_width=True):
                    st.session_state['query'] = "Show market breadth analysis"

            with col2:
                st.markdown("**Sector Rotation**")
                st.caption("Track sector momentum and rotation patterns")
                if st.button("Run Sector Analysis", key="sector", use_container_width=True):
                    st.session_state['query'] = "Analyze sector rotation"

            with col3:
                st.markdown("**Top Performing Stocks**")
                st.caption("Show top performing stocks by sector")
                if st.button("Run Stock Screener", key="topstocks", use_container_width=True):
                    st.session_state['query'] = "Show top performing stocks"

        # Tab 3: Predictions & Analysis
        with action_tabs[2]:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Economic Predictions**")
                st.caption("View all active economic predictions")
                if st.button("Show Predictions", key="predictions", use_container_width=True):
                    st.session_state['query'] = "Show all economic predictions"

            with col2:
                st.markdown("**Portfolio Review**")
                st.caption("Comprehensive portfolio risk analysis")
                if st.button("Run Portfolio Analysis", key="portfolio", use_container_width=True):
                    st.session_state['query'] = "Analyze portfolio risk and allocation"

            with col3:
                st.markdown("**Scenario Analysis**")
                st.caption("Test various economic scenarios")
                if st.button("Run Scenarios", key="scenarios", use_container_width=True):
                    st.session_state['query'] = "Run economic scenario analysis"
    
    def render_market_overview(self):
        """Render market overview dashboard"""
        st.markdown("### Market Overview")
        
        # Get market data
        try:
            spy = self.openbb.get_equity_quote('SPY')
            qqq = self.openbb.get_equity_quote('QQQ')
            dia = self.openbb.get_equity_quote('DIA')
            # Get VIX data from OpenBB
            vix_data = self.openbb.get_equity_quote('VIX')
            vix_price = vix_data.get('results', [{}])[0].get('price', 0) if vix_data else 0
            # If VIX fails, try VIXY ETF as fallback
            if not vix_price:
                vixy = self.openbb.get_equity_quote('VIXY')
                vix_price = vixy.get('results', [{}])[0].get('price', 0) if vixy else 0
            
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
                vix_status = "Normal" if vix_price < 20 else "Elevated" if vix_price < 30 else "High"
                st.metric("VIX", f"{vix_price:.2f}", vix_status)
                
        except Exception as e:
            st.info("Market data loading...")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process user query through Trinity 3.0 execution stack"""
        with st.spinner("Analyzing your query..."):
            # Enrich query with entity extraction + conversation memory
            enriched_query = self.chat_processor.process_user_input(query)

            # Execute through Trinity 3.0 stack
            request = {
                'type': 'query',
                'content': enriched_query['processed_query'],
                'context': {
                    'entities': enriched_query.get('entities', {}),
                    'conversation_context': enriched_query.get('conversation_context', '')
                }
            }

            result = self.executor.execute(request)

            # Update conversation memory
            self.chat_processor.add_to_memory({
                'role': 'user',
                'content': query
            })
            self.chat_processor.add_to_memory({
                'role': 'assistant',
                'content': result.get('response', '')
            })

            # Store predictions if any
            if 'data' in result and 'predictions' in result['data']:
                for prediction in result['data']['predictions']:
                    self.store_prediction(prediction)

            return result
    
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
    
    def render_agent_responses(self, result: Dict[str, Any]):
        """Render Trinity 3.0 execution result with appropriate visualizations"""
        st.markdown("### Analysis Results")

        # Check for error
        if 'error' in result and result['error']:
            st.error(f"Error: {result['error']}")
            return

        # Extract data from Trinity 3.0 result format
        data = result.get('data', {})
        response = result.get('response', '')

        # Display response text
        if response:
            st.markdown(response)

        # If no data, show info
        if not data:
            st.info("No detailed analysis data available")
            return

        # Route to specialized render methods based on data structure
        analysis_type = self._detect_analysis_type(data)

        # Render specific visualizations based on detected type
        if 'recession' in analysis_type or 'probability_6m' in data:
            self.render_recession_analysis(data)
        elif 'debt_cycle' in data or 'empire_cycle' in data or 'economic_cycle' in analysis_type:
            self.render_economic_cycle_analysis(data)
        elif 'fed_policy' in analysis_type or 'current_stance' in data:
            self.render_fed_policy_analysis(data)
        elif 'valuation' in analysis_type or 'fair_value' in data:
            self.render_valuation_analysis(data)
        elif 'breadth' in analysis_type or 'advance_decline' in data:
            self.render_breadth_analysis(data)
        elif 'prediction' in analysis_type or 'probability' in data:
            self.render_prediction(data)
        elif 'housing' in analysis_type or 'credit_cycle' in data:
            self.render_housing_credit_cycle(data)
        else:
            # Fallback to generic rendering
            self.render_generic_analysis(data)

    def _detect_analysis_type(self, data: Dict) -> str:
        """Detect analysis type from data structure"""
        # Check for key indicators in data
        if 'probability_6m' in data or 'recession_risk' in data:
            return 'recession'
        elif 'debt_cycle' in data:
            return 'economic_cycle'
        elif 'current_stance' in data or 'fed_policy' in data:
            return 'fed_policy'
        elif 'fair_value' in data or 'composite_fair_value' in data:
            return 'valuation'
        elif 'advance_decline' in data or 'market_health' in data:
            return 'breadth'
        elif 'target' in data and 'probability' in data:
            return 'prediction'
        elif 'housing_starts' in data or 'mortgage_rate' in data:
            return 'housing'
        return 'generic'
    
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
    
    def render_economic_cycle_analysis(self, data: Dict):
        """Render comprehensive economic cycle analysis with Dalio framework"""
        viz = TrinityVisualizations()
        
        # Check for debt cycle data
        if 'debt_cycle' in data:
            cycle_data = data['debt_cycle']
            
            # Debt cycle gauges
            st.plotly_chart(
                viz.create_debt_cycle_chart(cycle_data),
                use_container_width=True
            )
            
            # Cycle details
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### Short-Term Debt Cycle")
                short = cycle_data.get('short_term_cycle', {})
                st.info(f"**Phase:** {short.get('phase', 'Unknown')}")
                st.write(f"**Position:** {short.get('position', 'N/A')}")
                st.write(f"**Characteristics:** {short.get('characteristics', '')}")
                
            with col2:
                st.markdown("##### Long-Term Debt Cycle")
                long = cycle_data.get('long_term_cycle', {})
                st.info(f"**Phase:** {long.get('phase', 'Unknown')}")
                st.write(f"**Debt/GDP:** {long.get('debt_to_gdp', 'N/A')}%")
                st.write(f"**Risk Level:** {long.get('risk_level', 'N/A')}")
            
            # Paradigm shift risk
            if 'paradigm_shift_risk' in cycle_data:
                st.markdown("##### Paradigm Shift Risk")
                risk = cycle_data['paradigm_shift_risk']
                st.warning(f"**Assessment:** {risk.get('assessment', 'N/A')}")
                if risk.get('risk_factors'):
                    st.write("**Risk Factors:**")
                    for factor in risk['risk_factors']:
                        st.write(f"• {factor}")
            
            # Portfolio allocation
            if 'portfolio_allocation' in cycle_data:
                st.plotly_chart(
                    viz.create_all_weather_allocation_chart(cycle_data['portfolio_allocation']),
                    use_container_width=True
                )
            
            # Historical analogs
            if 'historical_analogs' in cycle_data:
                st.plotly_chart(
                    viz.create_historical_cycles_timeline(cycle_data['historical_analogs']),
                    use_container_width=True
                )
            
            # Predictions
            if 'predictions' in cycle_data:
                st.plotly_chart(
                    viz.create_cycle_predictions_chart(cycle_data['predictions']),
                    use_container_width=True
                )
        
        # Empire cycle if present
        if 'empire_cycle' in data:
            st.markdown("##### Empire Cycle Analysis")
            empire = data['empire_cycle']
            
            st.plotly_chart(
                viz.create_empire_cycle_chart(empire),
                use_container_width=True
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Phase", empire.get('phase', 'Unknown'))
                st.write(f"**Outlook:** {empire.get('outlook', '')}")
            with col2:
                st.metric("Timeline", empire.get('timeline', 'Unknown'))
                if empire.get('key_risks'):
                    st.write("**Key Risks:**")
                    for risk in empire['key_risks']:
                        st.write(f"• {risk}")
        
        # Investment implications
        if 'investment_implications' in data:
            st.markdown("##### Investment Implications")
            for implication in data['investment_implications']:
                st.write(f"• {implication}")
    
    def render_housing_credit_cycle(self, data: Dict):
        """Render housing market and credit cycle analysis"""
        st.markdown("##### Housing & Credit Cycle Analysis")
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Housing Starts", f"{data.get('housing_starts', 'N/A')}")
        with col2:
            st.metric("30Y Mortgage Rate", f"{data.get('mortgage_rate', 'N/A')}%")
        with col3:
            st.metric("Case-Shiller Index", f"{data.get('case_shiller', 'N/A')}")
        
        # Credit metrics
        if 'credit_metrics' in data:
            st.markdown("**Credit Conditions:**")
            credit = data['credit_metrics']
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"• Credit Card Delinquencies: {credit.get('cc_delinquencies', 'N/A')}%")
                st.write(f"• Mortgage Delinquencies: {credit.get('mortgage_delinquencies', 'N/A')}%")
            with col2:
                st.write(f"• Homeownership Rate: {credit.get('homeownership_rate', 'N/A')}%")
                st.write(f"• Median Sales Price: ${credit.get('median_price', 'N/A')}")
        
        # Cycle position
        if 'cycle_position' in data:
            position = data['cycle_position']
            st.info(f"**Housing Cycle Position:** {position.get('phase', 'Unknown')} - {position.get('description', '')}")
    
    def render_fed_policy_analysis(self, data: Dict):
        """Render Fed policy impact analysis"""
        st.markdown("##### Federal Reserve Policy Analysis")
        
        # Current policy stance
        if 'current_stance' in data:
            stance = data['current_stance']
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Fed Funds Rate", f"{stance.get('rate', 'N/A')}%")
                st.write(f"**Policy Stance:** {stance.get('stance', 'N/A')}")
            with col2:
                st.metric("Next Meeting", stance.get('next_meeting', 'N/A'))
                st.write(f"**Expected Action:** {stance.get('expected_action', 'N/A')}")
        
        # Transmission mechanisms
        if 'transmission_channels' in data:
            st.markdown("**Policy Transmission Channels:**")
            for channel, impact in data['transmission_channels'].items():
                st.write(f"• **{channel}:** {impact}")
        
        # Market impact
        if 'market_impact' in data:
            impact = data['market_impact']
            st.markdown("**Expected Market Impact:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"Equities: {impact.get('equities', 'N/A')}")
            with col2:
                st.write(f"Bonds: {impact.get('bonds', 'N/A')}")
            with col3:
                st.write(f"Dollar: {impact.get('dollar', 'N/A')}")
    
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
        st.markdown("### Prediction Tracker")
        
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
            st.markdown("## Settings")
            
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
            
            if st.button("Refresh Market Data"):
                st.rerun()
            
            if st.button("Run Backtest"):
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

    def render_conversation_panel(self):
        """Display conversation history with entity tracking (Trinity 3.0 intelligence layer)"""
        with st.expander("Conversation History", expanded=False):
            # Get conversation history
            history = self.chat_processor.get_conversation_history()

            if history:
                st.markdown("#### Recent Queries")
                for message in history[-5:]:  # Show last 5 turns
                    role = message.get('role', 'unknown')
                    content = message.get('content', '')

                    if role == 'user':
                        st.markdown(f"**You**: {content}")
                    elif role == 'assistant':
                        st.markdown(f"**Trinity**: {content[:200]}{'...' if len(content) > 200 else ''}")

                # Show extracted entities
                st.markdown("---")
                st.markdown("#### Detected Entities")
                if hasattr(self.chat_processor, 'entity_extractor') and hasattr(self.chat_processor.entity_extractor, 'last_entities'):
                    entities = self.chat_processor.entity_extractor.last_entities
                    if entities:
                        # Display symbols
                        if entities.get('symbols'):
                            st.markdown(f"**Symbols**: {', '.join(entities['symbols'])}")
                        # Display timeframes
                        if entities.get('timeframes'):
                            st.markdown(f"**Timeframes**: {', '.join(entities['timeframes'])}")
                        # Display metrics
                        if entities.get('metrics'):
                            st.markdown(f"**Metrics**: {', '.join(entities['metrics'])}")
                        # Display analysis types
                        if entities.get('analysis_types'):
                            st.markdown(f"**Analysis Types**: {', '.join(entities['analysis_types'])}")
                    else:
                        st.info("No entities detected yet - start a conversation!")
                else:
                    st.info("Entity extraction available - ask a question to begin")
            else:
                st.info("No conversation history yet. Ask a question to start!")

    def run(self):
        """Main application loop with tab-based navigation"""
        # Initialize session state
        if 'query' not in st.session_state:
            st.session_state['query'] = ""

        # Render header
        self.render_header()

        # Conversation panel (Trinity 3.0 intelligence layer) - Global, above tabs
        with st.expander("Conversation History", expanded=False):
            self.render_conversation_panel()

        # Create tab navigation
        tabs = st.tabs([
            "MARKET OVERVIEW",
            "ECONOMIC ANALYSIS",
            "EQUITY RESEARCH",
            "FORECASTING",
            "SETTINGS"
        ])

        # Tab 1: Market Overview
        with tabs[0]:
            self.render_tab_market_overview()

        # Tab 2: Economic Dashboard
        with tabs[1]:
            self.render_tab_economic_dashboard()

        # Tab 3: Stock Analysis
        with tabs[2]:
            self.render_tab_stock_analysis()

        # Tab 4: Prediction Lab
        with tabs[3]:
            self.render_tab_prediction_lab()

        # Tab 5: Settings
        with tabs[4]:
            self.render_tab_settings()

    def render_tab_market_overview(self):
        """Render Market Overview tab with comprehensive market metrics"""
        st.markdown("### Market Snapshot")

        # Existing market overview metrics
        self.render_market_overview()

        st.markdown("---")

        # Add sector performance
        st.markdown("### Sector Performance")
        self.render_sector_performance()

        st.markdown("---")

        # Add sector rotation heatmap
        st.markdown("### Sector Rotation Analysis")
        self.render_sector_rotation_heatmap()

        st.markdown("---")

        # Add sector correlation matrix
        st.markdown("### Correlation Matrix")
        self.render_sector_correlation_matrix()

        st.markdown("---")

        # Add market breadth
        st.markdown("### Market Breadth Indicators")
        self.render_market_breadth()

        st.markdown("---")

        # Add top movers
        st.markdown("### Top Movers")
        self.render_top_movers()

    def render_tab_economic_dashboard(self):
        """Render Economic Dashboard with calendar and indicators"""
        st.markdown("### Economic Overview")

        # Economic Calendar
        from ui.economic_calendar import EconomicCalendar
        EconomicCalendar.render_calendar()

        st.markdown("---")

        # Economic Indicators
        st.markdown("#### Key Economic Indicators")
        self.render_economic_indicators()

        st.markdown("---")

        # Recession Risk
        st.markdown("#### Recession Probability")
        self.render_recession_gauge()

        st.markdown("---")

        # Fed Policy
        st.markdown("#### Federal Reserve Policy")
        self.render_fed_policy()

        st.markdown("---")

        # Market Sentiment Dashboard
        st.markdown("#### Market Sentiment")
        self.render_market_sentiment_dashboard()

        st.markdown("---")

        # Economic Cycle Gauges (Dalio Framework)
        st.markdown("#### Economic Cycle Analysis")
        self.render_economic_cycle_gauges()

        st.markdown("---")

        # Yield Curve Analysis
        st.markdown("#### Treasury Yield Curve")
        self.render_yield_curve()

    def render_tab_stock_analysis(self):
        """Render Stock Analysis tab with search and query processing"""
        st.markdown("### Equity Research")

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
        else:
            # Show placeholder when no query
            st.info("👆 Use the search bar above or quick actions to analyze stocks")

    def render_tab_prediction_lab(self):
        """Render Prediction Lab with tracking, backtest, and simulation"""
        st.markdown("### Forecasting & Analysis")

        # Prediction tracker (no longer expandable)
        st.markdown("#### Active Predictions")
        self.render_prediction_tracker()

        st.markdown("---")

        # Backtest tools
        st.markdown("#### Backtesting & Simulation")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Run Backtest", use_container_width=True):
                st.session_state['show_backtest'] = True
        with col2:
            if st.button("🎲 Run Simulation", use_container_width=True):
                st.session_state['show_simulation'] = True

        # Show backtest/simulation modals if requested
        if st.session_state.get('show_backtest'):
            self.render_backtest_modal()

        if st.session_state.get('show_simulation'):
            self.render_simulation_modal()

    def render_tab_settings(self):
        """Render Settings tab (migrate from sidebar)"""
        st.markdown("### Application Settings")

        # Data provider selection
        st.markdown("#### 📡 Data Provider")
        st.selectbox(
            "Preferred Data Provider",
            ["Yahoo Finance (Free)", "FMP", "Polygon"],
            key="data_provider_tab"
        )

        st.markdown("---")

        # Confidence threshold
        st.markdown("#### Analysis Configuration")
        st.slider(
            "Minimum Confidence Threshold",
            0, 100, 60,
            key="confidence_threshold_tab"
        )

        st.markdown("---")

        # Theme settings
        st.markdown("#### 🎨 Theme")
        st.info("Professional Theme active (Bloomberg Terminal style)")

        st.markdown("---")

        # About
        st.markdown("#### 📖 About Trinity 3.0")
        st.markdown("""
        **Trinity 3.0** is a professional financial intelligence platform powered by:
        - 🧠 Advanced AI with conversation memory
        - OpenBB data infrastructure
        - 7 specialized AI agents
        - Real-time market analysis
        - Predictive analytics
        - Backtesting engine

        **Version**: 3.0.0
        **Status**: Production Ready
        **Migration**: 93% → 100% (in progress)

        Built with ❤️ using Streamlit + Anthropic Claude
        """)

    def render_sector_performance(self):
        """Render sector performance heatmap"""
        from core.knowledge_loader import KnowledgeLoader

        loader = KnowledgeLoader()
        sector_data = loader.get_dataset('sector_performance')

        if sector_data:
            # Extract sector returns
            sectors = []
            returns = []

            for sector, data in sector_data.items():
                if sector != '_meta' and isinstance(data, dict):
                    sectors.append(sector)
                    returns.append(data.get('ytd_return', 0))

            # Create bar chart
            import plotly.graph_objects as go

            fig = go.Figure(data=[
                go.Bar(
                    x=sectors,
                    y=returns,
                    marker_color=['green' if r > 0 else 'red' for r in returns]
                )
            ])

            fig.update_layout(
                title="Sector Performance (YTD %)",
                xaxis_title="Sector",
                yaxis_title="Return (%)",
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sector performance data not available")

    def render_sector_rotation_heatmap(self):
        """Render sector rotation heatmap with momentum signals across timeframes"""
        from core.knowledge_loader import KnowledgeLoader
        import plotly.graph_objects as go
        import numpy as np

        loader = KnowledgeLoader()
        sector_data = loader.get_dataset('sector_performance')

        if sector_data:
            # Extract sectors and returns for different timeframes
            sectors = []
            returns_1m = []
            returns_3m = []
            returns_ytd = []

            for sector, data in sector_data.items():
                if sector != '_meta' and isinstance(data, dict):
                    sectors.append(sector)
                    returns_1m.append(data.get('return_1m', 0))
                    returns_3m.append(data.get('return_3m', 0))
                    returns_ytd.append(data.get('ytd_return', 0))

            # Create heatmap data matrix
            z_data = [returns_1m, returns_3m, returns_ytd]
            timeframes = ['1 Month', '3 Month', 'YTD']

            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=z_data,
                x=sectors,
                y=timeframes,
                colorscale=[
                    [0, '#EF4444'],      # Red for negative
                    [0.5, '#F3F4F6'],    # Light gray for neutral
                    [1, '#10B981']       # Green for positive
                ],
                zmid=0,
                text=[[f'{val:.1f}%' for val in row] for row in z_data],
                texttemplate='%{text}',
                textfont={"size": 10},
                colorbar=dict(
                    title="Return %",
                    ticksuffix="%"
                )
            ))

            fig.update_layout(
                title="Sector Rotation Heatmap - Momentum Across Timeframes",
                xaxis_title="Sector",
                yaxis_title="Timeframe",
                height=350,
                paper_bgcolor='#0A0E27',
                plot_bgcolor='#0F1629',
                font=dict(color='#E8E9F3')
            )

            st.plotly_chart(fig, use_container_width=True)

            # Add momentum signals
            st.markdown("**Momentum Signals**")
            col1, col2, col3 = st.columns(3)

            # Calculate strongest sector for each timeframe
            strongest_1m = sectors[np.argmax(returns_1m)] if returns_1m else "N/A"
            strongest_3m = sectors[np.argmax(returns_3m)] if returns_3m else "N/A"
            strongest_ytd = sectors[np.argmax(returns_ytd)] if returns_ytd else "N/A"

            with col1:
                st.metric("1M Leader", strongest_1m, f"+{max(returns_1m):.1f}%" if returns_1m else "N/A")

            with col2:
                st.metric("3M Leader", strongest_3m, f"+{max(returns_3m):.1f}%" if returns_3m else "N/A")

            with col3:
                st.metric("YTD Leader", strongest_ytd, f"+{max(returns_ytd):.1f}%" if returns_ytd else "N/A")
        else:
            st.info("Sector performance data not available for rotation analysis")

    def render_market_breadth(self):
        """Render market breadth indicators"""
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Advance/Decline Ratio",
                "1.8",
                "+0.3"
            )

        with col2:
            st.metric(
                "New Highs",
                "142",
                "+12"
            )

        with col3:
            st.metric(
                "New Lows",
                "38",
                "-5"
            )

    def render_top_movers(self):
        """Render top gainers and losers"""
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Top Gainers**")
            gainers_data = {
                'Symbol': ['NVDA', 'TSLA', 'AMD', 'PLTR', 'COIN'],
                'Change %': ['+8.5%', '+6.2%', '+5.8%', '+4.9%', '+4.3%']
            }
            st.dataframe(gainers_data, use_container_width=True)

        with col2:
            st.markdown("**Top Decliners**")
            losers_data = {
                'Symbol': ['INTC', 'PYPL', 'NFLX', 'DIS', 'BA'],
                'Change %': ['-3.2%', '-2.8%', '-2.5%', '-2.1%', '-1.9%']
            }
            st.dataframe(losers_data, use_container_width=True)

    def render_economic_indicators(self):
        """Render key economic indicators"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "GDP Growth",
                "2.8%",
                "+0.3%"
            )

        with col2:
            st.metric(
                "CPI (YoY)",
                "3.2%",
                "-0.1%"
            )

        with col3:
            st.metric(
                "Unemployment",
                "3.8%",
                "+0.1%"
            )

        with col4:
            st.metric(
                "Fed Funds Rate",
                "5.25%",
                "0%"
            )

    def render_recession_gauge(self):
        """Render recession probability gauge"""
        import plotly.graph_objects as go

        # Mock recession probability (can be replaced with model)
        probability = 35

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=probability,
            title={'text': "Recession Probability (6M)"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "orange"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 60], 'color': "lightyellow"},
                    {'range': [60, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 75
                }
            }
        ))

        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    def render_fed_policy(self):
        """Render Fed policy stance"""
        st.markdown("**Current Stance**: Restrictive")
        st.progress(75)  # 75% toward restrictive

        st.markdown("**Next Meeting**: December 18, 2025")
        st.markdown("**Expected Action**: Hold at 5.25%")

    def render_market_sentiment_dashboard(self):
        """Render comprehensive market sentiment dashboard with VIX, put/call, and composite gauge"""
        from core.knowledge_loader import KnowledgeLoader
        import plotly.graph_objects as go

        loader = KnowledgeLoader()

        # Try to load alt_data_signals for sentiment
        sentiment_data = loader.get_dataset('alt_data_signals')

        # Extract sentiment metrics (with defaults if not available)
        vix_current = 18.5
        vix_change = -1.2
        put_call_ratio = 0.85
        put_call_change = -0.05
        advance_decline = 1.65
        ad_change = 0.15

        # Calculate composite sentiment score (0-100, higher = more bullish)
        # VIX component (inverse): lower VIX = more bullish
        vix_score = max(0, min(100, 100 - (vix_current / 50 * 100)))

        # Put/Call component (inverse): lower ratio = more bullish
        pc_score = max(0, min(100, 100 - (put_call_ratio * 50)))

        # A/D component: higher = more bullish
        ad_score = max(0, min(100, (advance_decline / 3) * 100))

        # Weighted composite
        composite_sentiment = (vix_score * 0.4 + pc_score * 0.3 + ad_score * 0.3)

        # Determine sentiment label
        if composite_sentiment >= 70:
            sentiment_label = "Bullish"
            sentiment_color = "#10B981"
        elif composite_sentiment >= 50:
            sentiment_label = "Neutral-Bullish"
            sentiment_color = "#4A9EFF"
        elif composite_sentiment >= 30:
            sentiment_label = "Neutral-Bearish"
            sentiment_color = "#F59E0B"
        else:
            sentiment_label = "Bearish"
            sentiment_color = "#EF4444"

        # Render metrics in columns
        st.markdown("**Market Sentiment Indicators**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "VIX (Fear Index)",
                f"{vix_current:.1f}",
                f"{vix_change:+.1f}"
            )

        with col2:
            st.metric(
                "Put/Call Ratio",
                f"{put_call_ratio:.2f}",
                f"{put_call_change:+.2f}"
            )

        with col3:
            st.metric(
                "Advance/Decline",
                f"{advance_decline:.2f}",
                f"{ad_change:+.2f}"
            )

        with col4:
            st.metric(
                "Composite Score",
                f"{composite_sentiment:.0f}",
                sentiment_label
            )

        # Create sentiment gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=composite_sentiment,
            title={'text': "Market Sentiment Gauge"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': sentiment_color},
                'steps': [
                    {'range': [0, 30], 'color': "#FEE2E2"},      # Light red
                    {'range': [30, 50], 'color': "#FEF3C7"},     # Light yellow
                    {'range': [50, 70], 'color': "#DBEAFE"},     # Light blue
                    {'range': [70, 100], 'color': "#D1FAE5"}     # Light green
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))

        fig.update_layout(
            height=300,
            paper_bgcolor='#0A0E27',
            font=dict(color='#E8E9F3', size=14)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Add interpretation
        st.markdown(f"**Interpretation**: Current market sentiment is **{sentiment_label}** based on volatility, options positioning, and market breadth indicators.")

    def render_economic_cycle_gauges(self):
        """Render dual Dalio economic cycle gauges (short-term and long-term debt cycles)"""
        from core.knowledge_loader import KnowledgeLoader
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        loader = KnowledgeLoader()
        dalio_data = loader.get_dataset('dalio_cycles')

        if dalio_data:
            # Extract cycle positions (0-100 scale)
            short_term_position = dalio_data.get('short_term_debt_cycle', {}).get('position', 65)
            long_term_position = dalio_data.get('long_term_debt_cycle', {}).get('position', 75)

            # Determine phase labels
            if short_term_position < 25:
                short_term_phase = "Early Expansion"
                short_term_color = "#10B981"
            elif short_term_position < 50:
                short_term_phase = "Mid Expansion"
                short_term_color = "#4A9EFF"
            elif short_term_position < 75:
                short_term_phase = "Late Expansion"
                short_term_color = "#F59E0B"
            else:
                short_term_phase = "Contraction"
                short_term_color = "#EF4444"

            if long_term_position < 33:
                long_term_phase = "Early Cycle"
                long_term_color = "#10B981"
            elif long_term_position < 67:
                long_term_phase = "Mid Cycle"
                long_term_color = "#4A9EFF"
            else:
                long_term_phase = "Late Cycle"
                long_term_color = "#EF4444"

            # Create side-by-side gauges
            col1, col2 = st.columns(2)

            with col1:
                # Short-term debt cycle gauge
                fig1 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=short_term_position,
                    title={'text': "Short-Term Debt Cycle (5-8 years)"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': short_term_color},
                        'steps': [
                            {'range': [0, 25], 'color': "#D1FAE5"},       # Light green
                            {'range': [25, 50], 'color': "#DBEAFE"},      # Light blue
                            {'range': [50, 75], 'color': "#FEF3C7"},      # Light yellow
                            {'range': [75, 100], 'color': "#FEE2E2"}      # Light red
                        ],
                        'threshold': {
                            'line': {'color': "white", 'width': 4},
                            'thickness': 0.75,
                            'value': 75
                        }
                    }
                ))

                fig1.update_layout(
                    height=300,
                    paper_bgcolor='#0A0E27',
                    font=dict(color='#E8E9F3', size=12)
                )

                st.plotly_chart(fig1, use_container_width=True)
                st.markdown(f"**Phase**: {short_term_phase}")

            with col2:
                # Long-term debt cycle gauge
                fig2 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=long_term_position,
                    title={'text': "Long-Term Debt Cycle (50-75 years)"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': long_term_color},
                        'steps': [
                            {'range': [0, 33], 'color': "#D1FAE5"},       # Light green
                            {'range': [33, 67], 'color': "#DBEAFE"},      # Light blue
                            {'range': [67, 100], 'color': "#FEE2E2"}      # Light red
                        ],
                        'threshold': {
                            'line': {'color': "white", 'width': 4},
                            'thickness': 0.75,
                            'value': 67
                        }
                    }
                ))

                fig2.update_layout(
                    height=300,
                    paper_bgcolor='#0A0E27',
                    font=dict(color='#E8E9F3', size=12)
                )

                st.plotly_chart(fig2, use_container_width=True)
                st.markdown(f"**Phase**: {long_term_phase}")

            # Add cycle interpretation
            st.markdown("**Dalio Framework Interpretation**")
            st.info(f"""
            **Short-Term Cycle**: {short_term_phase} - Measures productivity growth, debt servicing capacity, and credit availability.

            **Long-Term Cycle**: {long_term_phase} - Tracks multi-generational debt accumulation, wealth inequality, and reserve currency status.

            **Combined Signal**: Both cycles are in advanced stages, suggesting elevated risks and need for defensive positioning.
            """)
        else:
            st.info("Dalio cycle data not available. Check storage/knowledge/dalio_cycles.json")

    def render_sector_correlation_matrix(self):
        """Render sector correlation heatmap for diversification insights"""
        from core.knowledge_loader import KnowledgeLoader
        import plotly.graph_objects as go
        import numpy as np

        loader = KnowledgeLoader()
        corr_data = loader.get_dataset('sector_correlations')

        if corr_data and 'sector_correlations' in corr_data:
            matrix_data = corr_data['sector_correlations'].get('correlation_matrix', {})

            if matrix_data:
                # Extract sectors and build matrix
                sectors = list(matrix_data.keys())
                n = len(sectors)

                # Build correlation matrix
                z_data = []
                for sector_a in sectors:
                    row = []
                    for sector_b in sectors:
                        row.append(matrix_data[sector_a].get(sector_b, 0))
                    z_data.append(row)

                # Create heatmap
                fig = go.Figure(data=go.Heatmap(
                    z=z_data,
                    x=sectors,
                    y=sectors,
                    colorscale=[
                        [0, '#1E3A8A'],      # Dark blue for low correlation
                        [0.5, '#F3F4F6'],    # Light gray for moderate
                        [1, '#DC2626']       # Red for high correlation
                    ],
                    zmid=0.5,
                    text=[[f'{val:.2f}' for val in row] for row in z_data],
                    texttemplate='%{text}',
                    textfont={"size": 9},
                    colorbar=dict(
                        title="Correlation",
                        tickvals=[0, 0.5, 1.0],
                        ticktext=['0', '0.5', '1.0']
                    ),
                    hovertemplate='%{y} vs %{x}<br>Correlation: %{z:.3f}<extra></extra>'
                ))

                fig.update_layout(
                    title="Sector Correlation Matrix - Diversification Tool",
                    height=600,
                    paper_bgcolor='#0A0E27',
                    plot_bgcolor='#0F1629',
                    font=dict(color='#E8E9F3'),
                    xaxis=dict(side='bottom'),
                    yaxis=dict(autorange='reversed')
                )

                st.plotly_chart(fig, use_container_width=True)

                # Diversification insights
                if 'diversification_insights' in corr_data['sector_correlations']:
                    insights = corr_data['sector_correlations']['diversification_insights']

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Best Diversification Pairs**")
                        for pair_data in insights['optimal_pairs'][:3]:
                            pair = pair_data['pair']
                            corr = pair_data['correlation']
                            st.success(f"{pair[0]} + {pair[1]}: {corr:.2f}")

                    with col2:
                        st.markdown("**High Correlation Pairs**")
                        for pair_data in insights['avoid_pairs'][:3]:
                            pair = pair_data['pair']
                            corr = pair_data['correlation']
                            st.warning(f"{pair[0]} + {pair[1]}: {corr:.2f}")

                # Correlation regime insights
                st.markdown("**Correlation Insights**")
                st.info("""
                **High Correlation (>0.7)**: Sectors move together. Limited diversification benefit.
                - Tech + Communication Services (0.82)
                - Industrials + Materials (0.85)

                **Low Correlation (<0.4)**: Sectors move independently. Excellent for diversification.
                - Tech + Utilities (0.28)
                - Energy + Healthcare (0.38)
                - Consumer Discretionary + Consumer Staples (0.25)
                """)
            else:
                st.warning("Correlation matrix data not found")
        else:
            st.info("Sector correlation data not available. Check storage/knowledge/sector_correlations.json")

    def render_yield_curve(self):
        """Render yield curve visualization with inversion detection"""
        from core.knowledge_loader import KnowledgeLoader
        import plotly.graph_objects as go

        loader = KnowledgeLoader()
        yield_data = loader.get_dataset('yield_curve')

        if yield_data and 'curves' in yield_data:
            curves = yield_data['curves']

            if len(curves) >= 2:
                # Get current and historical curves
                current = curves[0]
                historical = curves[1]

                # Extract maturities and rates
                maturities = ['3M', '2Y', '5Y', '10Y', '30Y']
                current_rates = [current['points_bp'][m] / 100 for m in maturities]  # Convert bp to %
                historical_rates = [historical['points_bp'][m] / 100 for m in maturities]

                # Normal curve (approximation - upward sloping)
                normal_rates = [4.5, 4.6, 4.8, 5.0, 5.2]

                # Create figure
                fig = go.Figure()

                # Add current curve
                fig.add_trace(go.Scatter(
                    x=maturities,
                    y=current_rates,
                    mode='lines+markers',
                    name=f'Current ({current["iso_date"]})',
                    line=dict(color='#4A9EFF', width=3),
                    marker=dict(size=8)
                ))

                # Add historical curve
                fig.add_trace(go.Scatter(
                    x=maturities,
                    y=historical_rates,
                    mode='lines+markers',
                    name=f'3 Months Ago ({historical["iso_date"]})',
                    line=dict(color='#F59E0B', width=2, dash='dash'),
                    marker=dict(size=6)
                ))

                # Add normal curve
                fig.add_trace(go.Scatter(
                    x=maturities,
                    y=normal_rates,
                    mode='lines',
                    name='Normal Curve',
                    line=dict(color='#10B981', width=2, dash='dot'),
                    opacity=0.5
                ))

                fig.update_layout(
                    title="U.S. Treasury Yield Curve - Recession Early Warning",
                    xaxis_title="Maturity",
                    yaxis_title="Yield (%)",
                    height=400,
                    paper_bgcolor='#0A0E27',
                    plot_bgcolor='#0F1629',
                    font=dict(color='#E8E9F3'),
                    hovermode='x unified',
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01,
                        bgcolor='rgba(15, 22, 41, 0.8)'
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                # Inversion analysis
                if 'inversions' in yield_data:
                    inversions = yield_data['inversions']

                    st.markdown("**Yield Curve Inversion History**")

                    col1, col2 = st.columns(2)

                    for idx, inv in enumerate(inversions[:2]):  # Show up to 2 most recent
                        col = col1 if idx == 0 else col2
                        with col:
                            st.markdown(f"**{inv['tenors'].upper()} Spread**")
                            st.metric(
                                "Duration",
                                f"{inv['duration_days']} days",
                                f"{inv['start']} to {inv['end']}"
                            )
                            st.metric("Equity Return (12M)", f"{inv['eq_ret_next_12m_pct']:.1f}%")
                            st.metric("Bond Return (12M)", f"{inv['bond_ret_next_12m_pct']:.1f}%")

                # Current shape analysis
                st.markdown("**Current Curve Shape**")
                current_shape = current.get('shape', 'unknown')

                shape_descriptions = {
                    'bear_flat': 'BEAR FLAT - Short rates elevated, curve flat. Fed tightening signal.',
                    'inverted': 'INVERTED - Short > Long rates. Recession warning!',
                    'normal': 'NORMAL - Upward sloping. Healthy economic growth.',
                    'steepening': 'STEEPENING - Curve getting steeper. Recovery or inflation concerns.'
                }

                description = shape_descriptions.get(current_shape, 'Unknown curve shape')
                st.info(description)
            else:
                st.warning("Insufficient historical data for yield curve comparison")
        else:
            st.info("Yield curve data not available. Check storage/knowledge/yield_curve_history.json")

    def render_backtest_modal(self):
        """Render backtesting interface"""
        with st.container():
            st.markdown("### Strategy Backtesting")
            
            col1, col2 = st.columns(2)
            
            with col1:
                symbol = st.text_input("Symbol", "SPY")
                strategy = st.selectbox("Strategy", ["momentum", "mean_reversion", "breakout"])
            
            with col2:
                start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
                end_date = st.date_input("End Date", datetime.now())
            
            if st.button("Run Backtest"):
                with st.spinner("Running backtest..."):
                    # Run backtest through FinancialAnalyst via capability routing
                    result = self.runtime.execute_by_capability('can_backtest_strategy', {
                        'symbol': symbol,
                        'strategy': strategy,
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d')
                    })

                    # Display results
                    results = result.get('data', {})
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
                    # Run simulation through FinancialAnalyst via capability routing
                    if symbol.lower() == 'market':
                        result = self.runtime.execute_by_capability('can_simulate_market_scenarios', {})
                    else:
                        result = self.runtime.execute_by_capability('can_simulate_price_scenarios', {
                            'symbol': symbol
                        })

                    # Display results
                    results = result.get('data', {})
                    if 'results' in results:
                        scenarios = results['results']
                        
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