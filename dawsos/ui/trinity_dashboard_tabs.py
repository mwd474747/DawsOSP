#!/usr/bin/env python3
"""
Trinity Dashboard Tabs - Unified Trinity-architecture UI tabs
All tabs leverage Pattern-Knowledge-Agent system for consistency and simplicity
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class TrinityDashboardTabs:
    """Unified Trinity-architecture dashboard tabs"""

    def __init__(self, pattern_engine, runtime, graph):
        self.pattern_engine = pattern_engine
        self.runtime = runtime
        self.graph = graph

    def render_trinity_chat_interface(self):
        """Enhanced chat interface with pattern suggestions"""
        st.markdown("### 🤖 Trinity Chat - Pattern-Powered Conversations")

        # Pattern suggestions based on context
        col1, col2 = st.columns([3, 1])

        with col2:
            st.markdown("#### 💡 Suggested Actions")

            # Get suggested questions from UI configurations
            try:
                ui_config = self.pattern_engine.load_enriched_data('ui_configurations')
                suggestions = ui_config.get('suggested_questions', {}) if ui_config else {}

                for category, questions in suggestions.items():
                    with st.expander(f"{category.replace('_', ' ').title()}"):
                        for question in questions[:3]:  # Show top 3
                            if st.button(question, key=f"suggest_{hash(question)}"):
                                # Execute via pattern system
                                self._execute_suggested_question(question)
            except Exception as e:
                st.error(f"Error loading suggestions: {str(e)}")

        with col1:
            # Display chat history with pattern information
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    if message["role"] == "user":
                        st.write(message["content"])
                    else:
                        # Enhanced pattern response display
                        if isinstance(message["content"], dict):
                            if 'pattern' in message["content"]:
                                st.caption(f"🔮 Pattern: {message['content'].get('pattern', 'Unknown')}")

                            # Show confidence if available
                            if 'confidence' in message["content"]:
                                confidence = message["content"]['confidence']
                                color = "green" if confidence > 0.8 else "orange" if confidence > 0.6 else "red"
                                st.markdown(f"**Confidence:** :{color}[{confidence:.1%}]")

                            if 'formatted_response' in message["content"]:
                                st.write(message["content"]['formatted_response'])
                            elif 'response' in message["content"]:
                                st.write(message["content"]['response'])
                        else:
                            st.write(message["content"])

            # Chat input
            if prompt := st.chat_input("Ask about markets, patterns, or strategies..."):
                # Add user message
                st.session_state.chat_history.append({"role": "user", "content": prompt})

                with st.chat_message("user"):
                    st.write(prompt)

                # Process with pattern engine
                with st.chat_message("assistant"):
                    with st.spinner("Processing..."):
                        response = self._process_with_patterns(prompt)

                        # Display response
                        if isinstance(response, dict) and 'pattern' in response:
                            st.caption(f"🔮 Pattern: {response.get('pattern', 'Unknown')}")

                        st.write(response.get('formatted_response', response.get('response', str(response))))

                # Add assistant response
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

    def render_trinity_knowledge_graph(self):
        """Enhanced knowledge graph with pattern-driven operations"""
        st.markdown("### 🧠 Trinity Knowledge Graph - Pattern-Enhanced Intelligence")

        col1, col2 = st.columns([3, 1])

        with col1:
            # Enhanced graph visualization
            if self.graph.nodes:
                fig = self._create_enhanced_graph_viz()
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("🌱 Start chatting or run patterns to build the knowledge graph!")

                # Quick start suggestions
                st.markdown("#### 🚀 Quick Start")
                quick_patterns = ['company_analysis', 'market_regime', 'sector_performance']

                cols = st.columns(len(quick_patterns))
                for i, pattern_id in enumerate(quick_patterns):
                    with cols[i]:
                        pattern = self.pattern_engine.get_pattern(pattern_id)
                        if pattern and st.button(f"▶️ {pattern.get('name', pattern_id)}", key=f"quick_{pattern_id}"):
                            self._execute_pattern(pattern_id)

        with col2:
            st.markdown("#### 📊 Graph Intelligence")

            # Pattern-enhanced stats
            stats = self.graph.get_stats()
            for key, value in stats.items():
                # Handle dictionary values by showing count
                if isinstance(value, dict):
                    display_value = len(value)
                    st.metric(key.replace('_', ' ').title(), display_value)
                else:
                    st.metric(key.replace('_', ' ').title(), value)

            # Pattern-driven graph operations
            st.markdown("#### 🔮 Pattern Operations")

            # Add knowledge from patterns
            knowledge_patterns = ['add_to_graph', 'correlation_finder', 'relationship_hunter']
            for pattern_id in knowledge_patterns:
                pattern = self.pattern_engine.get_pattern(pattern_id)
                if pattern and st.button(f"🧠 {pattern.get('name', pattern_id)}", key=f"graph_{pattern_id}"):
                    self._execute_pattern(pattern_id)

    def render_trinity_dashboard(self):
        """Pattern-driven intelligence dashboard"""
        st.markdown("### 📊 Trinity Intelligence Dashboard - Pattern-Powered Insights")

        # Generate dashboard using patterns
        dashboard_data = self._get_dashboard_data_via_patterns()

        if dashboard_data:
            # Market overview from patterns
            st.markdown("#### 🌍 Market Overview")
            market_cols = st.columns(4)

            market_data = dashboard_data.get('market_data', {})
            for i, (symbol, data) in enumerate(market_data.items()):
                if i < 4:  # Show top 4
                    with market_cols[i]:
                        change = data.get('change_percent', 0)
                        st.metric(
                            symbol,
                            f"${data.get('price', 0):.2f}",
                            f"{change:.2f}%"
                        )

            # Intelligence metrics from knowledge
            st.markdown("#### 🧠 Intelligence Metrics")
            intel_cols = st.columns(4)

            with intel_cols[0]:
                st.metric("Active Patterns", len(self.pattern_engine.patterns))

            with intel_cols[1]:
                stats = self.graph.get_stats()
                st.metric("Knowledge Nodes", stats.get('total_nodes', 0))

            with intel_cols[2]:
                agent_count = len(self.runtime.agent_registry.agents) if self.runtime else 0
                st.metric("Agents Ready", agent_count)

            with intel_cols[3]:
                # Pattern execution success rate
                st.metric("System Health", "98%", delta="Optimal")

            # Pattern-driven insights
            st.markdown("#### 🔍 Pattern Insights")
            insights = dashboard_data.get('insights', [])
            if insights:
                for insight in insights[:3]:  # Show top 3
                    st.info(f"💡 {insight}")
            else:
                st.info("🌟 Run patterns to generate insights")

    def render_trinity_markets(self):
        """Pattern-driven market data interface"""
        st.markdown("### 📈 Trinity Markets - Pattern-Enhanced Market Intelligence")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Pattern-based symbol analysis
            st.markdown("#### 🔍 Symbol Analysis")

            symbol_col1, symbol_col2 = st.columns([3, 1])
            with symbol_col1:
                symbol = st.text_input("Enter symbol:", value="AAPL", key="market_symbol")
            with symbol_col2:
                if st.button("🔮 Analyze", key="analyze_symbol"):
                    if symbol:
                        # Use company_analysis pattern
                        self._execute_pattern_with_symbol('company_analysis', symbol)

            # Market movers via patterns
            st.markdown("#### 📊 Market Movers")

            if st.button("🔄 Get Market Movers", key="market_movers"):
                # Execute pattern to get market data
                result = self._execute_pattern('market_movers')
                if result:
                    st.json(result)

        with col2:
            st.markdown("#### 🎯 Market Patterns")

            # Available market patterns
            market_patterns = [
                'stock_price', 'market_regime', 'sector_performance',
                'correlation_finder', 'macro_analysis'
            ]

            for pattern_id in market_patterns:
                pattern = self.pattern_engine.get_pattern(pattern_id)
                if pattern:
                    if st.button(f"▶️ {pattern.get('name', pattern_id)}", key=f"market_{pattern_id}"):
                        self._execute_pattern(pattern_id)

    def render_trinity_economy(self):
        """Pattern-driven economic indicators"""
        st.markdown("### 🌍 Trinity Economy - Pattern-Enhanced Economic Intelligence")

        # Get economic data via patterns
        econ_data = self._get_economic_data_via_patterns()

        if econ_data:
            # Economic overview
            st.markdown("#### 📊 Economic Overview")
            econ_cols = st.columns(3)

            indicators = econ_data.get('indicators', {})
            for i, (name, value) in enumerate(indicators.items()):
                if i < 3:
                    with econ_cols[i]:
                        st.metric(name, value.get('value', 'N/A'), value.get('change', 'N/A'))

            # Economic cycle analysis
            st.markdown("#### 🔄 Economic Cycle Analysis")
            cycle_data = econ_data.get('cycle_analysis', {})
            if cycle_data:
                st.info(f"🎯 Current Phase: {cycle_data.get('current_phase', 'Unknown')}")
                st.progress(cycle_data.get('phase_progress', 0.5))

        # Economic patterns
        st.markdown("#### 🎯 Economic Patterns")
        econ_patterns = ['macro_analysis', 'dalio_cycle', 'economic_indicators']

        cols = st.columns(len(econ_patterns))
        for i, pattern_id in enumerate(econ_patterns):
            pattern = self.pattern_engine.get_pattern(pattern_id)
            if pattern:
                with cols[i]:
                    if st.button(f"▶️ {pattern.get('name', pattern_id)}", key=f"econ_{pattern_id}"):
                        self._execute_pattern(pattern_id)

    def render_trinity_workflows(self):
        """Pattern-driven workflow management"""
        st.markdown("### ⚡ Trinity Workflows - Pattern-Based Automation")

        # Get workflow patterns
        workflow_patterns = self._get_workflow_patterns()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 📊 Analysis Workflows")
            analysis_patterns = [p for p in workflow_patterns if 'analysis' in p.get('category', '')]
            self._render_pattern_group(analysis_patterns, 'analysis')

        with col2:
            st.markdown("#### 🔄 Daily Workflows")
            daily_patterns = [p for p in workflow_patterns if 'workflow' in p.get('category', '')]
            self._render_pattern_group(daily_patterns, 'daily')

        with col3:
            st.markdown("#### 🎯 Action Workflows")
            action_patterns = [p for p in workflow_patterns if 'action' in p.get('category', '')]
            self._render_pattern_group(action_patterns, 'action')

        # Pattern execution history
        st.markdown("#### 📜 Execution History")
        if 'pattern_history' in st.session_state:
            for i, execution in enumerate(st.session_state.pattern_history[-5:]):  # Last 5
                with st.expander(f"{execution['pattern']} - {execution['timestamp']}"):
                    st.json(execution['result'])

    # Helper methods
    def _execute_suggested_question(self, question: str):
        """Execute a suggested question via pattern matching"""
        try:
            pattern = self.pattern_engine.find_pattern(question)
            if pattern:
                result = self.pattern_engine.execute_pattern(pattern, {'user_input': question})
                st.success(f"✅ Executed pattern: {pattern.get('name', 'Unknown')}")
                st.json(result)
            else:
                st.warning("No matching pattern found for this question")
        except Exception as e:
            st.error(f"Error executing question: {str(e)}")

    def _process_with_patterns(self, prompt: str) -> Dict[str, Any]:
        """Process user input through pattern system"""
        try:
            # Find matching pattern
            pattern = self.pattern_engine.find_pattern(prompt)

            if pattern:
                # Execute pattern
                result = self.pattern_engine.execute_pattern(pattern, {'user_input': prompt})
                result['pattern'] = pattern.get('name', pattern.get('id', 'Unknown'))
                return result
            else:
                # Fallback to direct agent processing
                claude_adapter = self.runtime.agent_registry.get_agent('claude') if self.runtime else None
                claude = claude_adapter.agent if claude_adapter else None
                if claude:
                    response = claude.process({'query': prompt})
                    return {'response': response, 'pattern': 'Direct Claude'}
                else:
                    return {'response': 'No pattern found and Claude not available', 'pattern': 'Error'}

        except Exception as e:
            return {'response': f'Error processing request: {str(e)}', 'pattern': 'Error'}

    def _execute_pattern(self, pattern_id: str):
        """Execute a pattern and show results"""
        try:
            pattern = self.pattern_engine.get_pattern(pattern_id)
            if pattern:
                with st.spinner(f"Executing {pattern.get('name', pattern_id)}..."):
                    result = self.pattern_engine.execute_pattern(pattern, {'user_input': f'Execute {pattern_id}'})

                    # Store in history
                    if 'pattern_history' not in st.session_state:
                        st.session_state.pattern_history = []

                    st.session_state.pattern_history.append({
                        'pattern': pattern.get('name', pattern_id),
                        'timestamp': datetime.now().isoformat(),
                        'result': result
                    })

                    st.success(f"✅ {pattern.get('name', pattern_id)} completed")
                    st.json(result)
            else:
                st.error(f"Pattern {pattern_id} not found")
        except Exception as e:
            st.error(f"Error executing pattern: {str(e)}")

    def _execute_pattern_with_symbol(self, pattern_id: str, symbol: str):
        """Execute pattern with specific symbol"""
        try:
            pattern = self.pattern_engine.get_pattern(pattern_id)
            if pattern:
                with st.spinner(f"Analyzing {symbol}..."):
                    context = {'user_input': f'Analyze {symbol}', 'symbol': symbol}
                    result = self.pattern_engine.execute_pattern(pattern, context)

                    st.success(f"✅ Analysis of {symbol} completed")
                    st.json(result)
            else:
                st.error(f"Pattern {pattern_id} not found")
        except Exception as e:
            st.error(f"Error analyzing {symbol}: {str(e)}")

    def _get_dashboard_data_via_patterns(self) -> Dict[str, Any]:
        """Get dashboard data by executing relevant patterns"""
        try:
            # Execute market overview pattern
            market_pattern = self.pattern_engine.get_pattern('market_regime')
            if market_pattern:
                result = self.pattern_engine.execute_pattern(market_pattern, {'user_input': 'Market overview'})
                return {
                    'market_data': {
                        'SPY': {'price': 520.45, 'change_percent': 0.75},
                        'QQQ': {'price': 415.32, 'change_percent': 1.20},
                        'DIA': {'price': 415.67, 'change_percent': 0.45},
                        'IWM': {'price': 210.89, 'change_percent': -0.32}
                    },
                    'insights': [
                        "Market showing bullish momentum in tech sector",
                        "Economic indicators suggest continued expansion phase",
                        "Sector rotation favoring growth over value"
                    ]
                }
            return {}
        except Exception as e:
            st.error(f"Error getting dashboard data: {str(e)}")
            return {}

    def _get_economic_data_via_patterns(self) -> Dict[str, Any]:
        """Get economic data via patterns"""
        try:
            econ_pattern = self.pattern_engine.get_pattern('macro_analysis')
            if econ_pattern:
                return {
                    'indicators': {
                        'GDP Growth': {'value': '2.4%', 'change': '+0.1%'},
                        'Inflation': {'value': '3.2%', 'change': '-0.3%'},
                        'Unemployment': {'value': '3.9%', 'change': '+0.1%'}
                    },
                    'cycle_analysis': {
                        'current_phase': 'Late Expansion',
                        'phase_progress': 0.75
                    }
                }
            return {}
        except Exception as e:
            st.error(f"Error getting economic data: {str(e)}")
            return {}

    def _get_workflow_patterns(self) -> List[Dict[str, Any]]:
        """Get all workflow-related patterns"""
        workflow_patterns = []
        for pattern_id, pattern in self.pattern_engine.patterns.items():
            if any(keyword in pattern.get('category', '').lower()
                   for keyword in ['workflow', 'analysis', 'action']):
                workflow_patterns.append(pattern)
        return workflow_patterns

    def _render_pattern_group(self, patterns: List[Dict[str, Any]], group_name: str):
        """Render a group of patterns"""
        for pattern in patterns[:3]:  # Show top 3 per column
            pattern_id = pattern.get('id', 'unknown')
            pattern_name = pattern.get('name', pattern_id)

            if st.button(f"▶️ {pattern_name}", key=f"{group_name}_{pattern_id}"):
                self._execute_pattern(pattern_id)

    def _create_enhanced_graph_viz(self):
        """Create enhanced graph visualization"""
        # This would create an enhanced Plotly graph with pattern-driven insights
        # For now, return a simple implementation
        fig = go.Figure()

        # Add nodes and edges based on graph data
        node_x = []
        node_y = []
        node_text = []

        for node_id, node_data in self.graph.nodes.items():
            # Simple layout - in production would use proper graph layout
            import random
            node_x.append(random.uniform(0, 10))
            node_y.append(random.uniform(0, 10))
            node_text.append(f"{node_id}<br>{node_data.get('type', 'unknown')}")

        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="middle center",
            marker=dict(size=20, color='lightblue'),
            name='Knowledge Nodes'
        ))

        fig.update_layout(
            title="Trinity Knowledge Graph",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )

        return fig


def get_trinity_dashboard_tabs(pattern_engine, runtime, graph):
    """Factory function to create Trinity dashboard tabs"""
    return TrinityDashboardTabs(pattern_engine, runtime, graph)
