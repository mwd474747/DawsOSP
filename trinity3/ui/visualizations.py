"""
Trinity Visualizations - Chart and visualization components
Professional financial charts using Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class TrinityVisualizations:
    """Visualization components for Trinity 3.0"""
    
    def __init__(self):
        """Initialize visualization settings"""
        self.default_colors = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'success': '#48bb78',
            'danger': '#f56565',
            'warning': '#ed8936',
            'info': '#4299e1'
        }
        
        self.chart_theme = {
            'layout': {
                'font': {'family': 'Arial, sans-serif'},
                'paper_bgcolor': 'white',
                'plot_bgcolor': 'white',
                'margin': dict(l=40, r=40, t=40, b=40),
                'hoverlabel': dict(bgcolor="white", font_size=12)
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