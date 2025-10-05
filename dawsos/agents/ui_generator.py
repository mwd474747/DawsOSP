#!/usr/bin/env python3
"""
UI Generator Agent - Creates Streamlit components from patterns and data
Leverages the Trinity architecture to generate intelligent, data-driven UI components
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any
import json
from datetime import datetime

class UIGeneratorAgent:
    """
    Generates UI components based on data and styling instructions.
    Enables pattern-driven UI creation instead of manual coding.
    """

    def __init__(self, graph=None):
        self.graph = graph
        self.component_templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load UI component templates"""
        return {
            'confidence_meter': '''
                <div style="background: {bg_color}; padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; color: {text_color};">{title}</span>
                        <span style="font-size: 18px; font-weight: bold; color: {accent_color};">{confidence}%</span>
                    </div>
                    <div style="background: #333; border-radius: 5px; height: 8px; margin: 10px 0;">
                        <div style="background: {bar_color}; height: 100%; width: {confidence}%; border-radius: 5px;"></div>
                    </div>
                    {factors_html}
                </div>
            ''',
            'alert_card': '''
                <div style="background: {bg_color}; border-left: 4px solid {accent_color}; padding: 12px; margin: 8px 0; border-radius: 4px;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 18px; margin-right: 10px;">{icon}</span>
                        <div>
                            <div style="font-weight: bold; color: {text_color};">{title}</div>
                            <div style="color: {subtitle_color}; font-size: 14px;">{message}</div>
                            <div style="color: {time_color}; font-size: 12px;">{timestamp}</div>
                        </div>
                    </div>
                </div>
            ''',
            'pattern_card': '''
                <div style="background: {bg_color}; padding: 15px; margin: 10px; border-radius: 8px; border: 1px solid {border_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: {text_color};">{name}</h4>
                            <p style="margin: 5px 0; color: {subtitle_color}; font-size: 14px;">{description}</p>
                            <span style="background: {tag_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{category}</span>
                        </div>
                        <button style="background: {button_color}; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                            Execute
                        </button>
                    </div>
                </div>
            '''
        }

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method for UI generation requests"""
        try:
            component_type = request.get('component_type', 'default')
            data = request.get('data', {})
            style = request.get('style', 'default')

            if component_type == 'confidence_meter':
                return self.generate_confidence_meter(data, style)
            elif component_type == 'pattern_browser':
                return self.generate_pattern_browser(data, style)
            elif component_type == 'alert_feed':
                return self.generate_alert_feed(data, style)
            elif component_type == 'risk_radar':
                return self.generate_risk_radar(data, style)
            elif component_type == 'thinking_trace':
                return self.generate_thinking_trace(data, style)
            elif component_type == 'dashboard_widget':
                return self.generate_dashboard_widget(data, style)
            else:
                return self.generate_default_component(data, style)

        except Exception as e:
            return {
                'error': f"UI generation failed: {str(e)}",
                'component_html': f'<div style="color: red;">Error generating UI: {str(e)}</div>'
            }

    def generate_confidence_meter(self, data: Dict[str, Any], style: str = 'default') -> Dict[str, Any]:
        """Generate confidence meter component"""
        confidence = data.get('confidence', 0)
        title = data.get('title', 'Confidence')
        factors = data.get('factors', [])

        # Color scheme based on confidence level
        if confidence >= 80:
            bar_color = '#00cc88'
            bg_color = '#1a4c3a'
        elif confidence >= 60:
            bar_color = '#ffaa00'
            bg_color = '#4c3a1a'
        else:
            bar_color = '#ff4444'
            bg_color = '#4c1a1a'

        # Generate factors HTML
        factors_html = ""
        if factors:
            factors_html = "<div style='margin-top: 10px;'>"
            for factor in factors:
                factor_name = factor.get('name', 'Factor')
                factor_value = factor.get('value', 0)
                factors_html += "<div style='display: flex; justify-content: space-between; font-size: 12px; margin: 3px 0;'>"
                factors_html += f"<span style='color: #ccc;'>{factor_name}</span>"
                factors_html += f"<span style='color: #fff;'>{factor_value}%</span></div>"
            factors_html += "</div>"

        html = self.component_templates['confidence_meter'].format(
            bg_color=bg_color,
            text_color='#ffffff',
            accent_color=bar_color,
            bar_color=bar_color,
            confidence=confidence,
            title=title,
            factors_html=factors_html
        )

        return {
            'component_html': html,
            'component_type': 'confidence_meter',
            'data': data,
            'success': True
        }

    def generate_pattern_browser(self, data: Dict[str, Any], style: str = 'searchable_list') -> Dict[str, Any]:
        """Generate pattern browser component"""
        patterns = data.get('patterns', [])

        html = "<div style='background: #262730; border-radius: 10px; padding: 20px;'>"
        html += "<h3 style='color: #fff; margin-bottom: 20px;'>🔍 Available Patterns</h3>"

        # Search box
        html += "<div style='margin-bottom: 20px;'>"
        html += "<input type='text' placeholder='Search patterns...' style='width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #1a1a1a; color: #fff;'>"
        html += "</div>"

        # Pattern categories
        categories = {}
        for pattern in patterns:
            category = pattern.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(pattern)

        for category, category_patterns in categories.items():
            html += "<div style='margin-bottom: 20px;'>"
            html += f"<h4 style='color: #00cc88; margin-bottom: 10px;'>▼ {category} ({len(category_patterns)})</h4>"

            for pattern in category_patterns:
                pattern_html = self.component_templates['pattern_card'].format(
                    bg_color='#1a1a1a',
                    border_color='#444',
                    text_color='#fff',
                    subtitle_color='#ccc',
                    name=pattern.get('name', 'Unknown Pattern'),
                    description=pattern.get('description', 'No description available'),
                    category=category,
                    tag_color='#00cc88',
                    button_color='#00cc88'
                )
                html += pattern_html

            html += "</div>"

        html += "</div>"

        return {
            'component_html': html,
            'component_type': 'pattern_browser',
            'data': data,
            'success': True
        }

    def generate_alert_feed(self, data: Dict[str, Any], style: str = 'default') -> Dict[str, Any]:
        """Generate alert feed component"""
        alerts = data.get('alerts', [])

        html = "<div style='background: #262730; border-radius: 10px; padding: 20px;'>"
        html += "<h3 style='color: #fff; margin-bottom: 20px;'>🚨 Alert Feed</h3>"

        if not alerts:
            html += "<div style='color: #888; text-align: center; padding: 20px;'>No alerts at this time</div>"
        else:
            for alert in alerts:
                severity = alert.get('severity', 'info')

                # Color and icon based on severity
                if severity == 'critical':
                    icon = '🔴'
                    accent_color = '#ff4444'
                    bg_color = '#3a1a1a'
                elif severity == 'warning':
                    icon = '🟡'
                    accent_color = '#ffaa00'
                    bg_color = '#3a2a1a'
                else:
                    icon = '🔵'
                    accent_color = '#4488ff'
                    bg_color = '#1a2a3a'

                alert_html = self.component_templates['alert_card'].format(
                    bg_color=bg_color,
                    accent_color=accent_color,
                    icon=icon,
                    text_color='#fff',
                    subtitle_color='#ccc',
                    time_color='#888',
                    title=alert.get('title', 'Alert'),
                    message=alert.get('message', 'No details available'),
                    timestamp=alert.get('timestamp', datetime.now().strftime('%H:%M:%S'))
                )
                html += alert_html

        html += "</div>"

        return {
            'component_html': html,
            'component_type': 'alert_feed',
            'data': data,
            'success': True
        }

    def generate_risk_radar(self, data: Dict[str, Any], style: str = 'radar_chart') -> Dict[str, Any]:
        """Generate risk radar chart component"""
        risk_factors = data.get('risk_factors', {})

        # Create radar chart
        categories = list(risk_factors.keys())
        values = list(risk_factors.values())

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            fillcolor='rgba(0, 204, 136, 0.3)',
            line=dict(color='#00cc88', width=2),
            name='Risk Level'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(color='white', size=10),
                    gridcolor='#444'
                ),
                angularaxis=dict(
                    tickfont=dict(color='white', size=12),
                    gridcolor='#444'
                )
            ),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400,
            margin=dict(l=50, r=50, t=50, b=50)
        )

        return {
            'plotly_figure': fig,
            'component_type': 'risk_radar',
            'data': data,
            'success': True
        }

    def generate_thinking_trace(self, data: Dict[str, Any], style: str = 'flowchart') -> Dict[str, Any]:
        """Generate thinking trace visualization"""
        steps = data.get('steps', [])

        html = "<div style='background: #262730; border-radius: 10px; padding: 20px;'>"
        html += "<h3 style='color: #fff; margin-bottom: 20px;'>🧠 Thinking Trace</h3>"

        if not steps:
            html += "<div style='color: #888;'>No execution trace available</div>"
        else:
            html += "<div style='display: flex; align-items: center; flex-wrap: wrap;'>"

            for i, step in enumerate(steps):
                step_name = step.get('name', f'Step {i+1}')
                duration = step.get('duration', 0)
                status = step.get('status', 'success')

                # Status icon and color
                if status == 'success':
                    icon = '✅'
                    color = '#00cc88'
                elif status == 'error':
                    icon = '❌'
                    color = '#ff4444'
                else:
                    icon = '⏳'
                    color = '#ffaa00'

                html += f"<div style='background: #1a1a1a; padding: 10px; margin: 5px; border-radius: 5px; border: 2px solid {color};'>"
                html += f"<div style='color: {color}; font-weight: bold;'>{icon} {step_name}</div>"
                html += f"<div style='color: #ccc; font-size: 12px;'>{duration:.2f}s</div>"
                html += "</div>"

                # Arrow between steps
                if i < len(steps) - 1:
                    html += "<div style='color: #666; margin: 0 10px;'>→</div>"

            html += "</div>"

        html += "</div>"

        return {
            'component_html': html,
            'component_type': 'thinking_trace',
            'data': data,
            'success': True
        }

    def generate_dashboard_widget(self, data: Dict[str, Any], style: str = 'card') -> Dict[str, Any]:
        """Generate generic dashboard widget"""
        title = data.get('title', 'Widget')
        value = data.get('value', 'N/A')
        subtitle = data.get('subtitle', '')
        trend = data.get('trend', 0)

        # Trend color and icon
        if trend > 0:
            trend_icon = '↗️'
            trend_color = '#00cc88'
        elif trend < 0:
            trend_icon = '↘️'
            trend_color = '#ff4444'
        else:
            trend_icon = '→'
            trend_color = '#888'

        html = f"""
        <div style="background: #262730; border-radius: 10px; padding: 20px; margin: 10px; border: 1px solid #444;">
            <div style="color: #ccc; font-size: 14px; margin-bottom: 5px;">{title}</div>
            <div style="color: #fff; font-size: 28px; font-weight: bold; margin-bottom: 5px;">{value}</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #888; font-size: 12px;">{subtitle}</span>
                <span style="color: {trend_color}; font-size: 14px;">{trend_icon} {abs(trend):.1f}%</span>
            </div>
        </div>
        """

        return {
            'component_html': html,
            'component_type': 'dashboard_widget',
            'data': data,
            'success': True
        }

    def generate_default_component(self, data: Dict[str, Any], style: str = 'default') -> Dict[str, Any]:
        """Generate default component for unknown types"""
        html = f"""
        <div style="background: #262730; border-radius: 10px; padding: 20px; border: 1px solid #444;">
            <h4 style="color: #fff;">Generated Component</h4>
            <pre style="color: #ccc; background: #1a1a1a; padding: 10px; border-radius: 5px; overflow: auto;">
{json.dumps(data, indent=2)}
            </pre>
        </div>
        """

        return {
            'component_html': html,
            'component_type': 'default',
            'data': data,
            'success': True
        }

    def render_component(self, component_result: Dict[str, Any]) -> None:
        """Render a generated component in Streamlit"""
        if 'component_html' in component_result:
            st.components.v1.html(component_result['component_html'], height=None)
        elif 'plotly_figure' in component_result:
            st.plotly_chart(component_result['plotly_figure'], width="stretch")
        else:
            st.error("Unknown component type")