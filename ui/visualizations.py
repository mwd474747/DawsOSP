"""
Trinity Visualizations - Chart and visualization components
Professional financial charts using Plotly with Professional Theme
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ui.professional_theme import ProfessionalTheme

class TrinityVisualizations:
    """Visualization components for Trinity 3.0"""

    def __init__(self):
        """Initialize visualization settings with Professional Theme colors"""
        # Use Professional Theme colors for consistency
        self.default_colors = {
            'primary': ProfessionalTheme.COLORS['accent_primary'],     # #4A9EFF
            'secondary': ProfessionalTheme.COLORS['chart_secondary'],  # #8B5CF6
            'success': ProfessionalTheme.COLORS['accent_success'],     # #10B981
            'danger': ProfessionalTheme.COLORS['accent_danger'],       # #EF4444
            'warning': ProfessionalTheme.COLORS['accent_warning'],     # #F59E0B
            'info': ProfessionalTheme.COLORS['chart_primary']          # #4A9EFF
        }

        # Updated chart theme to match Professional Theme (dark mode)
        self.chart_theme = {
            'layout': {
                'font': {
                    'family': ProfessionalTheme.TYPOGRAPHY['font_family'],
                    'color': ProfessionalTheme.COLORS['text_secondary']
                },
                'paper_bgcolor': ProfessionalTheme.COLORS['background'],
                'plot_bgcolor': ProfessionalTheme.COLORS['background'],
                'margin': dict(l=40, r=40, t=40, b=40),
                'hoverlabel': dict(
                    bgcolor=ProfessionalTheme.COLORS['surface'],
                    font_size=11,
                    font_family=ProfessionalTheme.TYPOGRAPHY['font_mono'],
                    font_color=ProfessionalTheme.COLORS['text_primary']
                ),
                'xaxis': {
                    'gridcolor': ProfessionalTheme.COLORS['border'],
                    'color': ProfessionalTheme.COLORS['text_secondary']
                },
                'yaxis': {
                    'gridcolor': ProfessionalTheme.COLORS['border'],
                    'color': ProfessionalTheme.COLORS['text_secondary']
                }
            }
        }
    
    def create_gauge_chart(
        self,
        value: float,
        title: str,
        min_value: float = 0,
        max_value: float = 100,
        thresholds: Optional[Dict[str, float]] = None
    ) -> go.Figure:
        """
        Create a gauge chart for metrics like recession risk, confidence, etc.
        """
        if thresholds is None:
            thresholds = {'low': 30, 'medium': 60, 'high': 80}
        
        # Determine color based on value
        if value < thresholds['low']:
            bar_color = self.default_colors['success']
        elif value < thresholds['medium']:
            bar_color = self.default_colors['warning']
        else:
            bar_color = self.default_colors['danger']
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': thresholds.get('medium', 50)},
            gauge={
                'axis': {'range': [min_value, max_value]},
                'bar': {'color': bar_color},
                'steps': [
                    {'range': [min_value, thresholds['low']], 'color': 'lightgreen'},
                    {'range': [thresholds['low'], thresholds['medium']], 'color': 'lightyellow'},
                    {'range': [thresholds['medium'], max_value], 'color': 'lightcoral'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': thresholds.get('high', 80)
                }
            }
        ))
        
        fig.update_layout(
            height=250,
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_time_series_chart(
        self,
        data: pd.DataFrame,
        title: str,
        y_columns: List[str],
        show_volume: bool = False
    ) -> go.Figure:
        """
        Create time series chart for price data, indicators, etc.
        """
        fig = go.Figure()
        
        # Add traces for each column
        colors = px.colors.qualitative.Plotly
        
        for i, col in enumerate(y_columns):
            if col in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index if isinstance(data.index, pd.DatetimeIndex) else data.iloc[:, 0],
                    y=data[col],
                    mode='lines',
                    name=col,
                    line=dict(color=colors[i % len(colors)], width=2)
                ))
        
        # Add volume bars if requested
        if show_volume and 'volume' in data.columns:
            fig.add_trace(go.Bar(
                x=data.index,
                y=data['volume'],
                name='Volume',
                yaxis='y2',
                marker_color='rgba(100, 100, 100, 0.3)'
            ))
            
            fig.update_layout(
                yaxis2=dict(
                    title='Volume',
                    overlaying='y',
                    side='right'
                )
            )
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Value',
            hovermode='x unified',
            showlegend=True,
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_candlestick_chart(
        self,
        data: pd.DataFrame,
        title: str = "Price Chart"
    ) -> go.Figure:
        """
        Create candlestick chart for OHLC data
        """
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name='Price'
        )])
        
        # Add volume
        if 'volume' in data.columns:
            fig.add_trace(go.Bar(
                x=data.index,
                y=data['volume'],
                name='Volume',
                yaxis='y2',
                marker_color='rgba(100, 100, 100, 0.3)'
            ))
            
            fig.update_layout(
                yaxis2=dict(
                    title='Volume',
                    overlaying='y',
                    side='right'
                )
            )
        
        fig.update_layout(
            title=title,
            yaxis_title='Price',
            xaxis_rangeslider_visible=False,
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_heatmap(
        self,
        data: pd.DataFrame,
        title: str = "Correlation Matrix"
    ) -> go.Figure:
        """
        Create heatmap for correlations, sector performance, etc.
        """
        fig = go.Figure(data=go.Heatmap(
            z=data.values,
            x=data.columns,
            y=data.index,
            colorscale='RdYlGn',
            zmid=0,
            text=data.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title=title,
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_sector_rotation_chart(
        self,
        sectors: List[str],
        performance: List[float],
        momentum: List[float]
    ) -> go.Figure:
        """
        Create sector rotation scatter plot
        """
        fig = go.Figure()
        
        # Create scatter plot
        fig.add_trace(go.Scatter(
            x=performance,
            y=momentum,
            mode='markers+text',
            text=sectors,
            textposition='top center',
            marker=dict(
                size=15,
                color=momentum,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Momentum")
            )
        ))
        
        # Add quadrant lines
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.add_vline(x=0, line_dash="dash", line_color="gray")
        
        # Add quadrant labels
        fig.add_annotation(x=0.5, y=0.5, text="Leading", showarrow=False, font=dict(size=12, color="green"))
        fig.add_annotation(x=-0.5, y=0.5, text="Improving", showarrow=False, font=dict(size=12, color="yellow"))
        fig.add_annotation(x=-0.5, y=-0.5, text="Lagging", showarrow=False, font=dict(size=12, color="red"))
        fig.add_annotation(x=0.5, y=-0.5, text="Weakening", showarrow=False, font=dict(size=12, color="orange"))
        
        fig.update_layout(
            title="Sector Rotation Map",
            xaxis_title="Relative Performance",
            yaxis_title="Momentum",
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_prediction_chart(
        self,
        historical: pd.DataFrame,
        predictions: Dict[str, Any],
        title: str = "Prediction Analysis"
    ) -> go.Figure:
        """
        Create chart showing historical data with predictions
        """
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=historical.index,
            y=historical['value'] if 'value' in historical.columns else historical.iloc[:, 0],
            mode='lines',
            name='Historical',
            line=dict(color=self.default_colors['primary'], width=2)
        ))
        
        # Prediction point
        if 'predicted_value' in predictions:
            fig.add_trace(go.Scatter(
                x=[predictions.get('target_date', datetime.now())],
                y=[predictions['predicted_value']],
                mode='markers',
                name='Prediction',
                marker=dict(
                    size=12,
                    color=self.default_colors['secondary'],
                    symbol='star'
                )
            ))
        
        # Confidence bands if available
        if 'upper_bound' in predictions and 'lower_bound' in predictions:
            future_dates = pd.date_range(
                start=historical.index[-1],
                end=predictions.get('target_date', datetime.now()),
                periods=30
            )
            
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=[predictions['upper_bound']] * len(future_dates),
                mode='lines',
                name='Upper Bound',
                line=dict(color='gray', width=1, dash='dash'),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=[predictions['lower_bound']] * len(future_dates),
                mode='lines',
                name='Lower Bound',
                line=dict(color='gray', width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(128, 128, 128, 0.2)',
                showlegend=False
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Value',
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_monte_carlo_chart(
        self,
        simulations: List[List[float]],
        percentiles: Dict[str, float],
        title: str = "Monte Carlo Simulation"
    ) -> go.Figure:
        """
        Create Monte Carlo simulation visualization
        """
        fig = go.Figure()
        
        # Sample paths (show max 100)
        sample_size = min(100, len(simulations))
        for i in range(sample_size):
            fig.add_trace(go.Scatter(
                y=simulations[i],
                mode='lines',
                line=dict(color='lightgray', width=0.5),
                showlegend=False,
                opacity=0.3
            ))
        
        # Percentile lines
        colors = {'p5': 'red', 'p50': 'blue', 'p95': 'green'}
        labels = {'p5': '5th Percentile', 'p50': 'Median', 'p95': '95th Percentile'}
        
        for key, values in percentiles.items():
            if key in colors:
                fig.add_trace(go.Scatter(
                    y=values,
                    mode='lines',
                    name=labels[key],
                    line=dict(color=colors[key], width=2)
                ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Time Steps',
            yaxis_title='Value',
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_risk_dashboard(
        self,
        risk_scores: Dict[str, float],
        title: str = "Risk Dashboard"
    ) -> go.Figure:
        """
        Create comprehensive risk dashboard
        """
        fig = go.Figure()
        
        # Create bar chart of risk scores
        categories = list(risk_scores.keys())
        values = list(risk_scores.values())
        
        # Color based on risk level
        colors = []
        for v in values:
            if v < 30:
                colors.append(self.default_colors['success'])
            elif v < 60:
                colors.append(self.default_colors['warning'])
            else:
                colors.append(self.default_colors['danger'])
        
        fig.add_trace(go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f'{v:.0f}%' for v in values],
            textposition='auto'
        ))
        
        # Add danger zone line
        fig.add_hline(y=60, line_dash="dash", line_color="red", 
                     annotation_text="High Risk Threshold")
        
        fig.update_layout(
            title=title,
            xaxis_title='Risk Category',
            yaxis_title='Risk Score (%)',
            yaxis=dict(range=[0, 100]),
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_portfolio_pie(
        self,
        allocations: Dict[str, float],
        title: str = "Portfolio Allocation"
    ) -> go.Figure:
        """
        Create pie chart for portfolio allocations
        """
        fig = go.Figure(data=[go.Pie(
            labels=list(allocations.keys()),
            values=list(allocations.values()),
            hole=0.3,
            marker=dict(colors=px.colors.qualitative.Set3)
        )])
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='%{label}: %{value:.2f}%<extra></extra>'
        )
        
        fig.update_layout(
            title=title,
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_debt_cycle_chart(
        self,
        cycle_data: Dict[str, Any],
        title: str = "Ray Dalio Debt Cycle Analysis"
    ) -> go.Figure:
        """
        Create comprehensive debt cycle visualization
        """
        fig = go.Figure()
        
        # Short-term cycle gauge
        short_cycle = cycle_data.get('short_term_cycle', {})
        position_value = float(short_cycle.get('position', '50% through cycle').split('%')[0])
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=position_value,
            domain={'x': [0, 0.45], 'y': [0.5, 1]},
            title={'text': f"Short-Term Cycle<br>{short_cycle.get('phase', 'Unknown')}"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 25], 'color': "lightgreen"},
                    {'range': [25, 50], 'color': "lightyellow"},
                    {'range': [50, 75], 'color': "orange"},
                    {'range': [75, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        # Long-term cycle gauge
        long_cycle = cycle_data.get('long_term_cycle', {})
        debt_to_gdp = long_cycle.get('debt_to_gdp', 100)
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=debt_to_gdp,
            domain={'x': [0.55, 1], 'y': [0.5, 1]},
            title={'text': f"Long-Term Debt/GDP<br>{long_cycle.get('phase', 'Unknown')}"},
            gauge={
                'axis': {'range': [0, 150]},
                'bar': {'color': "purple"},
                'steps': [
                    {'range': [0, 60], 'color': "lightgreen"},
                    {'range': [60, 90], 'color': "lightyellow"},
                    {'range': [90, 120], 'color': "orange"},
                    {'range': [120, 150], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 130
                }
            }
        ))
        
        # Paradigm shift risk indicator
        paradigm_risk = cycle_data.get('paradigm_shift_risk', {})
        risk_score = paradigm_risk.get('risk_score', 0)
        
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=risk_score,
            domain={'x': [0.25, 0.75], 'y': [0, 0.4]},
            title={'text': f"Paradigm Shift Risk<br>{paradigm_risk.get('assessment', '')}"},
            delta={'reference': 50, 'increasing': {'color': "red"}}
        ))
        
        fig.update_layout(
            title=title,
            height=500,
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_empire_cycle_chart(
        self,
        empire_data: Dict[str, Any],
        title: str = "Empire Cycle Analysis (Dalio Framework)"
    ) -> go.Figure:
        """
        Create empire cycle radar chart
        """
        scores = empire_data.get('scores', {})
        
        categories = list(scores.keys())
        values = list(scores.values())
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=[cat.replace('_', ' ').title() for cat in categories],
            fill='toself',
            marker=dict(color=self.default_colors['primary'])
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            title=f"{title} - {empire_data.get('country', 'US')}: {empire_data.get('phase', 'Unknown')}",
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_historical_cycles_timeline(
        self,
        historical_analogs: List[Dict],
        title: str = "Historical Cycle Analogs"
    ) -> go.Figure:
        """
        Create timeline of historical cycle analogs
        """
        fig = go.Figure()
        
        if not historical_analogs:
            return fig
        
        # Create timeline bars
        for i, analog in enumerate(historical_analogs):
            fig.add_trace(go.Bar(
                x=[analog.get('similarity', 0)],
                y=[analog.get('period', 'Unknown')],
                orientation='h',
                text=f"{analog.get('years', '')} - {analog.get('outcome', '')}",
                textposition='inside',
                marker=dict(
                    color=analog.get('similarity', 0),
                    colorscale='RdYlGn',
                    showscale=i == 0,
                    cmin=0,
                    cmax=100
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>" +
                    "Similarity: %{x}%<br>" +
                    "Period: %{text}<br>" +
                    "Lessons: " + analog.get('lessons', '') +
                    "<extra></extra>"
                )
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Similarity Score (%)",
            yaxis_title="Historical Period",
            showlegend=False,
            height=300,
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_cycle_predictions_chart(
        self,
        predictions: Dict[str, Any],
        title: str = "Cycle-Based Predictions"
    ) -> go.Figure:
        """
        Create visualization for cycle-based predictions
        """
        fig = go.Figure()
        
        # Extract recession probability if available
        if 'recession_12m' in predictions:
            rec_data = predictions['recession_12m']
            
            # Recession probability gauge
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=rec_data.get('probability', 0),
                domain={'x': [0, 0.45], 'y': [0.5, 1]},
                title={'text': f"Recession Risk (12M)<br>{rec_data.get('timing', '')}"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkred" if rec_data.get('probability', 0) > 60 else "orange"},
                    'steps': [
                        {'range': [0, 30], 'color': "lightgreen"},
                        {'range': [30, 60], 'color': "lightyellow"},
                        {'range': [60, 100], 'color': "lightcoral"}
                    ]
                }
            ))
        
        # Market outlook if available
        if 'market_outlook' in predictions:
            outlook = predictions['market_outlook']
            if '1yr_expected' in outlook:
                returns = outlook['1yr_expected']
                
                # Create bar chart for expected returns
                assets = list(returns.keys())
                expected_returns = list(returns.values())
                
                colors = ['green' if r > 0 else 'red' for r in expected_returns]
                
                fig.add_trace(go.Bar(
                    x=assets,
                    y=expected_returns,
                    marker_color=colors,
                    text=[f"{r:+.1f}%" for r in expected_returns],
                    textposition='auto',
                    name='Expected Returns'
                ))
        
        fig.update_layout(
            title=title,
            height=400,
            **self.chart_theme['layout']
        )
        
        return fig
    
    def create_all_weather_allocation_chart(
        self,
        allocation: Dict[str, float],
        title: str = "All-Weather Portfolio Allocation (Dalio)"
    ) -> go.Figure:
        """
        Create enhanced portfolio allocation visualization
        """
        fig = go.Figure()
        
        # Create sunburst chart for hierarchical allocation
        labels = []
        parents = []
        values = []
        colors = []
        
        # Add asset classes
        for asset, percent in allocation.items():
            labels.append(asset.title())
            parents.append("")
            values.append(percent)
            
            # Color coding
            if 'stock' in asset.lower():
                colors.append('#2ca02c')  # Green
            elif 'bond' in asset.lower():
                colors.append('#1f77b4')  # Blue
            elif 'gold' in asset.lower():
                colors.append('#ff7f0e')  # Orange
            else:
                colors.append('#d62728')  # Red for commodities
        
        fig.add_trace(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(colors=colors),
            textinfo="label+percent parent",
            hovertemplate='<b>%{label}</b><br>Allocation: %{value:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            height=400,
            **self.chart_theme['layout']
        )
        
        return fig