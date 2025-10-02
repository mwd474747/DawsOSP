#!/usr/bin/env python3
"""
Trinity UI Components - Enhanced UI components leveraging the Trinity architecture
Integrates Pattern-Knowledge-Agent system with Streamlit for intelligent UI generation
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from agents.ui_generator import UIGeneratorAgent
from core.pattern_engine import PatternEngine
from core.agent_runtime import AgentRuntime


class TrinityUIComponents:
    """Enhanced UI components that leverage the Trinity architecture"""

    def __init__(self, pattern_engine: PatternEngine = None, runtime: AgentRuntime = None):
        self.pattern_engine = pattern_engine
        self.runtime = runtime
        self.ui_generator = UIGeneratorAgent()

    def render_pattern_browser(self, category_filter: str = None) -> None:
        """Render an interactive pattern browser using Trinity architecture"""
        if not self.pattern_engine:
            st.error("Pattern Engine not available")
            return

        # Get available patterns
        patterns = []
        for pattern_id, pattern in self.pattern_engine.patterns.items():
            pattern_info = {
                'id': pattern_id,
                'name': pattern.get('name', pattern_id),
                'description': pattern.get('description', 'No description'),
                'category': pattern.get('category', 'other'),
                'triggers': pattern.get('triggers', [])
            }

            if category_filter and pattern_info['category'] != category_filter:
                continue

            patterns.append(pattern_info)

        # Generate pattern browser UI
        browser_result = self.ui_generator.generate_pattern_browser(
            {'patterns': patterns},
            'searchable_list'
        )

        if browser_result.get('success'):
            components.html(browser_result['component_html'], height=400)

            # Add pattern execution buttons
            st.markdown("### Execute Pattern")
            selected_pattern = st.selectbox(
                "Choose pattern to execute:",
                options=[p['id'] for p in patterns],
                format_func=lambda x: next(p['name'] for p in patterns if p['id'] == x)
            )

            if st.button("Execute Pattern", key="execute_pattern"):
                if selected_pattern and self.runtime:
                    try:
                        with st.spinner(f"Executing {selected_pattern}..."):
                            pattern = self.pattern_engine.get_pattern(selected_pattern)
                            result = self.pattern_engine.execute_pattern(
                                pattern,
                                {'user_input': f"Execute {selected_pattern}"}
                            )
                            st.success("Pattern executed successfully!")
                            st.json(result)
                    except Exception as e:
                        st.error(f"Pattern execution failed: {str(e)}")
        else:
            st.error("Failed to generate pattern browser")

    def render_confidence_display(self, prediction_data: Dict[str, Any] = None) -> None:
        """Render confidence meter with dynamic data"""
        if not prediction_data:
            prediction_data = {
                'confidence': 85,
                'title': 'System Confidence',
                'factors': [
                    {'name': 'Data Quality', 'value': 92},
                    {'name': 'Model Accuracy', 'value': 88},
                    {'name': 'Historical Success', 'value': 76}
                ]
            }

        confidence_result = self.ui_generator.generate_confidence_meter(
            prediction_data,
            'default'
        )

        if confidence_result.get('success'):
            components.html(confidence_result['component_html'], height=200)
        else:
            st.error("Failed to generate confidence display")

    def render_alert_feed(self, max_alerts: int = 5) -> None:
        """Render live alert feed"""
        # Get alert configuration from knowledge base
        if self.pattern_engine:
            try:
                ui_config = self.pattern_engine.load_enriched_data('ui_configurations')
                alert_thresholds = ui_config.get('alert_thresholds', {}) if ui_config else {}

                # Generate mock alerts based on thresholds
                alerts = []
                current_time = datetime.now()

                # Mock alert generation (in production, this would come from monitoring)
                sample_alerts = [
                    {
                        'title': 'Portfolio Risk Elevated',
                        'message': 'Risk level above warning threshold (0.75)',
                        'severity': 'warning',
                        'timestamp': current_time.strftime('%H:%M:%S')
                    },
                    {
                        'title': 'Market Volatility Spike',
                        'message': 'VIX jumped 15% in last hour',
                        'severity': 'info',
                        'timestamp': (current_time).strftime('%H:%M:%S')
                    }
                ]

                alerts_result = self.ui_generator.generate_alert_feed(
                    {'alerts': sample_alerts[:max_alerts]},
                    'default'
                )

                if alerts_result.get('success'):
                    components.html(alerts_result['component_html'], height=300)
                else:
                    st.error("Failed to generate alert feed")

            except Exception as e:
                st.error(f"Error rendering alerts: {str(e)}")
        else:
            st.warning("Pattern Engine not available for alerts")

    def render_risk_radar(self, portfolio_data: Dict[str, Any] = None) -> None:
        """Render risk radar chart"""
        if not portfolio_data:
            # Use sample risk factors
            portfolio_data = {
                'risk_factors': {
                    'Market Risk': 65,
                    'Credit Risk': 35,
                    'Liquidity Risk': 45,
                    'Concentration': 80,
                    'Correlation Risk': 55,
                    'Volatility': 60
                }
            }

        radar_result = self.ui_generator.generate_risk_radar(
            portfolio_data,
            'radar_chart'
        )

        if radar_result.get('success') and 'plotly_figure' in radar_result:
            st.plotly_chart(radar_result['plotly_figure'], use_container_width=True)
        else:
            st.error("Failed to generate risk radar")

    def render_thinking_trace(self, execution_steps: List[Dict] = None) -> None:
        """Render execution thinking trace"""
        if not execution_steps:
            execution_steps = [
                {'name': 'Pattern Match', 'duration': 0.2, 'status': 'success'},
                {'name': 'Data Fetch', 'duration': 1.1, 'status': 'success'},
                {'name': 'Analysis', 'duration': 0.8, 'status': 'success'},
                {'name': 'Response Gen', 'duration': 0.3, 'status': 'success'}
            ]

        trace_result = self.ui_generator.generate_thinking_trace(
            {'steps': execution_steps},
            'flowchart'
        )

        if trace_result.get('success'):
            components.html(trace_result['component_html'], height=150)
        else:
            st.error("Failed to generate thinking trace")

    def render_dashboard_widget(self, widget_config: Dict[str, Any]) -> None:
        """Render a configurable dashboard widget"""
        widget_result = self.ui_generator.generate_dashboard_widget(
            widget_config,
            'card'
        )

        if widget_result.get('success'):
            components.html(widget_result['component_html'], height=120)
        else:
            st.error("Failed to generate dashboard widget")

    def render_suggested_questions(self) -> None:
        """Render contextual question suggestions"""
        if self.pattern_engine:
            try:
                ui_config = self.pattern_engine.load_enriched_data('ui_configurations')
                suggestions = ui_config.get('suggested_questions', {}) if ui_config else {}

                st.markdown("### 💡 Suggested Questions")

                for category, questions in suggestions.items():
                    with st.expander(f"{category.replace('_', ' ').title()}"):
                        for question in questions:
                            if st.button(question, key=f"suggest_{question[:20]}"):
                                # Simulate sending the question
                                st.session_state['suggested_question'] = question
                                st.rerun()

            except Exception as e:
                st.error(f"Error loading suggestions: {str(e)}")
        else:
            st.warning("Pattern Engine not available for suggestions")

    def render_pattern_shortcuts(self) -> None:
        """Render quick pattern execution shortcuts"""
        if self.pattern_engine:
            try:
                ui_config = self.pattern_engine.load_enriched_data('ui_configurations')
                shortcuts = ui_config.get('pattern_shortcuts', {}) if ui_config else {}

                st.markdown("### ⚡ Quick Actions")

                cols = st.columns(2)
                for i, (shortcut_id, shortcut) in enumerate(shortcuts.items()):
                    col = cols[i % 2]
                    with col:
                        if st.button(
                            f"{shortcut['icon']} {shortcut['description']}",
                            key=f"shortcut_{shortcut_id}",
                            use_container_width=True
                        ):
                            # Execute the pattern
                            pattern = self.pattern_engine.get_pattern(shortcut['pattern'])
                            if pattern and self.runtime:
                                try:
                                    with st.spinner(f"Executing {shortcut['description']}..."):
                                        result = self.pattern_engine.execute_pattern(
                                            pattern,
                                            {'user_input': shortcut['description']}
                                        )
                                        st.success(f"✅ {shortcut['description']} completed!")
                                        with st.expander("View Results"):
                                            st.json(result)
                                except Exception as e:
                                    st.error(f"❌ Failed: {str(e)}")
                            else:
                                st.error("Pattern or runtime not available")

            except Exception as e:
                st.error(f"Error loading shortcuts: {str(e)}")
        else:
            st.warning("Pattern Engine not available for shortcuts")

    def render_trinity_dashboard(self) -> None:
        """Render a complete Trinity-powered dashboard"""
        st.markdown("# 🔮 Trinity Intelligence Dashboard")
        st.markdown("*Powered by Pattern-Knowledge-Agent Architecture*")

        # Top row - Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            self.render_dashboard_widget({
                'title': 'Patterns Active',
                'value': len(self.pattern_engine.patterns) if self.pattern_engine else 0,
                'subtitle': 'Available workflows',
                'trend': 5.2
            })

        with col2:
            self.render_dashboard_widget({
                'title': 'System Health',
                'value': '98%',
                'subtitle': 'All systems operational',
                'trend': 0.1
            })

        with col3:
            self.render_dashboard_widget({
                'title': 'Knowledge Bases',
                'value': 6,
                'subtitle': 'Enriched data sources',
                'trend': 16.7
            })

        with col4:
            self.render_dashboard_widget({
                'title': 'Agents Ready',
                'value': len(self.runtime.agents) if self.runtime else 0,
                'subtitle': 'Specialized AI agents',
                'trend': 0
            })

        # Second row - Core components
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 🎯 Pattern Browser")
            self.render_pattern_browser()

        with col2:
            st.markdown("### 📊 System Confidence")
            self.render_confidence_display()

            st.markdown("### 🚨 Alert Feed")
            self.render_alert_feed()

        # Third row - Analysis components
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📡 Risk Radar")
            self.render_risk_radar()

        with col2:
            st.markdown("### 🧠 Thinking Trace")
            self.render_thinking_trace()

        # Bottom row - Actions
        col1, col2 = st.columns(2)

        with col1:
            self.render_suggested_questions()

        with col2:
            self.render_pattern_shortcuts()


def get_trinity_ui(pattern_engine: PatternEngine = None, runtime: AgentRuntime = None) -> TrinityUIComponents:
    """Factory function to create Trinity UI components"""
    return TrinityUIComponents(pattern_engine, runtime)