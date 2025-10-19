"""
Professional Financial Charts for Trinity 3.0
Using Plotly with Bloomberg Terminal-style theming
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class ProfessionalCharts:
    """Bloomberg Terminal-quality financial charts"""
    
    # Professional color scheme
    CHART_THEME = {
        'bg_color': '#0A0E27',
        'grid_color': '#1E2740',
        'text_color': '#E8E9F3',
        'text_secondary': '#A0A4B8',
        
        # Data colors - sophisticated palette
        'primary': '#4A9EFF',    # Bright blue
        'success': '#10B981',    # Green
        'danger': '#EF4444',     # Red
        'warning': '#F59E0B',    # Amber
        'purple': '#8B5CF6',     # Purple
        'cyan': '#06B6D4',       # Cyan
        
        # Chart-specific
        'candlestick_up': '#10B981',
        'candlestick_down': '#EF4444',
        'volume': '#4A9EFF',
        'ma_primary': '#F59E0B',
        'ma_secondary': '#8B5CF6',
        
        # Font
        'font_family': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
        'font_mono': 'JetBrains Mono, Monaco, monospace'
    }
    
    @classmethod
    def get_layout_template(cls, title: str = "", height: int = 500) -> Dict:
        """Get base layout template for all charts"""
        return {
            'title': {
                'text': title.upper() if title else "",
                'font': {
                    'size': 14,
                    'color': cls.CHART_THEME['text_secondary'],
                    'family': cls.CHART_THEME['font_family']
                },
                'x': 0,
                'xanchor': 'left'
            },
            'height': height,
            'plot_bgcolor': cls.CHART_THEME['bg_color'],
            'paper_bgcolor': cls.CHART_THEME['bg_color'],
            'font': {
                'family': cls.CHART_THEME['font_mono'],
                'size': 11,
                'color': cls.CHART_THEME['text_secondary']
            },
            'xaxis': {
                'gridcolor': cls.CHART_THEME['grid_color'],
                'gridwidth': 1,
                'zeroline': False,
                'tickfont': {'size': 10},
                'showgrid': True,
                'color': cls.CHART_THEME['text_secondary']
            },
            'yaxis': {
                'gridcolor': cls.CHART_THEME['grid_color'],
                'gridwidth': 1,
                'zeroline': False,
                'tickfont': {'size': 10},
                'showgrid': True,
                'color': cls.CHART_THEME['text_secondary']
            },
            'hovermode': 'x unified',
            'hoverlabel': {
                'bgcolor': '#141B35',
                'font': {
                    'family': cls.CHART_THEME['font_mono'],
                    'size': 11,
                    'color': cls.CHART_THEME['text_color']
                },
                'bordercolor': cls.CHART_THEME['primary']
            },
            'margin': {'t': 40, 'l': 60, 'r': 20, 'b': 40},
            'showlegend': False
        }
    
    @classmethod
    def create_candlestick_chart(
        cls,
        df: pd.DataFrame,
        title: str = "Price Action",
        show_volume: bool = True,
        height: int = 600
    ) -> go.Figure:
        """Create professional candlestick chart with volume"""
        
        # Create subplots if volume is shown
        if show_volume:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=('', '')
            )
            
            # Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=df['date'] if 'date' in df else df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    increasing_line_color=cls.CHART_THEME['candlestick_up'],
                    decreasing_line_color=cls.CHART_THEME['candlestick_down'],
                    increasing_fillcolor=cls.CHART_THEME['candlestick_up'],
                    decreasing_fillcolor=cls.CHART_THEME['candlestick_down'],
                    name='OHLC'
                ),
                row=1, col=1
            )
            
            # Volume bars
            colors = [cls.CHART_THEME['candlestick_up'] if close >= open else cls.CHART_THEME['candlestick_down'] 
                     for close, open in zip(df['close'], df['open'])]
            
            fig.add_trace(
                go.Bar(
                    x=df['date'] if 'date' in df else df.index,
                    y=df['volume'],
                    marker_color=colors,
                    opacity=0.5,
                    name='Volume'
                ),
                row=2, col=1
            )
        else:
            fig = go.Figure(
                go.Candlestick(
                    x=df['date'] if 'date' in df else df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    increasing_line_color=cls.CHART_THEME['candlestick_up'],
                    decreasing_line_color=cls.CHART_THEME['candlestick_down'],
                    increasing_fillcolor=cls.CHART_THEME['candlestick_up'],
                    decreasing_fillcolor=cls.CHART_THEME['candlestick_down']
                )
            )
        
        # Apply professional layout
        layout = cls.get_layout_template(title, height)
        fig.update_layout(**layout)
        
        # Remove rangeslider for cleaner look
        fig.update_xaxes(rangeslider_visible=False)
        
        return fig
    
    @classmethod
    def create_line_chart(
        cls,
        data: Dict[str, List],
        title: str = "",
        y_label: str = "Value",
        height: int = 400,
        show_markers: bool = False
    ) -> go.Figure:
        """Create professional line chart"""
        
        fig = go.Figure()
        
        colors = [
            cls.CHART_THEME['primary'],
            cls.CHART_THEME['success'],
            cls.CHART_THEME['warning'],
            cls.CHART_THEME['purple'],
            cls.CHART_THEME['cyan']
        ]
        
        for i, (name, values) in enumerate(data.items()):
            color = colors[i % len(colors)]
            fig.add_trace(go.Scatter(
                y=values,
                x=list(range(len(values))),
                name=name.upper(),
                mode='lines+markers' if show_markers else 'lines',
                line=dict(color=color, width=2),
                marker=dict(size=4 if show_markers else 0, color=color),
                hovertemplate='<b>%{fullData.name}</b><br>Value: %{y:.2f}<extra></extra>'
            ))
        
        layout = cls.get_layout_template(title, height)
        layout['yaxis']['title'] = {
            'text': y_label,
            'font': {'size': 10, 'color': cls.CHART_THEME['text_secondary']}
        }
        layout['showlegend'] = len(data) > 1
        layout['legend'] = {
            'orientation': 'h',
            'y': 1.02,
            'x': 0,
            'font': {'size': 10}
        }
        
        fig.update_layout(**layout)
        return fig
    
    @classmethod
    def create_heatmap(
        cls,
        data: pd.DataFrame,
        title: str = "Correlation Matrix",
        height: int = 500
    ) -> go.Figure:
        """Create professional heatmap"""
        
        fig = go.Figure(data=go.Heatmap(
            z=data.values,
            x=data.columns,
            y=data.index,
            colorscale=[
                [0, cls.CHART_THEME['danger']],
                [0.5, cls.CHART_THEME['bg_color']],
                [1, cls.CHART_THEME['success']]
            ],
            colorbar=dict(
                thickness=10,
                len=0.7,
                tickfont=dict(size=9, color=cls.CHART_THEME['text_secondary'])
            ),
            text=data.values,
            texttemplate="%{text:.2f}",
            textfont={"size": 9, "color": cls.CHART_THEME['text_color']},
            hovertemplate='%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>'
        ))
        
        layout = cls.get_layout_template(title, height)
        layout['xaxis']['tickangle'] = -45
        fig.update_layout(**layout)
        
        return fig
    
    @classmethod
    def create_gauge_chart(
        cls,
        value: float,
        title: str = "",
        ranges: List[tuple] = None,
        height: int = 300
    ) -> go.Figure:
        """Create professional gauge chart for metrics"""
        
        if ranges is None:
            ranges = [(0, 30, cls.CHART_THEME['success']),
                     (30, 70, cls.CHART_THEME['warning']),
                     (70, 100, cls.CHART_THEME['danger'])]
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title.upper(), 'font': {'size': 12, 'color': cls.CHART_THEME['text_secondary']}},
            number={'font': {'size': 28, 'color': cls.CHART_THEME['text_color'], 'family': cls.CHART_THEME['font_mono']}},
            gauge={
                'axis': {
                    'range': [None, 100],
                    'tickwidth': 1,
                    'tickcolor': cls.CHART_THEME['grid_color'],
                    'tickfont': {'size': 9, 'color': cls.CHART_THEME['text_secondary']}
                },
                'bgcolor': cls.CHART_THEME['bg_color'],
                'borderwidth': 1,
                'bordercolor': cls.CHART_THEME['grid_color'],
                'bar': {'color': cls.CHART_THEME['primary']},
                'steps': [
                    {'range': [r[0], r[1]], 'color': r[2]} for r in ranges
                ],
                'threshold': {
                    'line': {'color': cls.CHART_THEME['text_color'], 'width': 2},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        
        layout = cls.get_layout_template("", height)
        fig.update_layout(**layout)
        
        return fig
    
    @classmethod
    def create_area_chart(
        cls,
        df: pd.DataFrame,
        columns: List[str],
        title: str = "",
        stacked: bool = True,
        height: int = 400
    ) -> go.Figure:
        """Create professional area chart"""
        
        fig = go.Figure()
        
        colors = [
            cls.CHART_THEME['primary'],
            cls.CHART_THEME['success'],
            cls.CHART_THEME['warning'],
            cls.CHART_THEME['purple'],
            cls.CHART_THEME['cyan']
        ]
        
        for i, col in enumerate(columns):
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[col],
                name=col.upper(),
                mode='lines',
                line=dict(width=0.5, color=colors[i % len(colors)]),
                stackgroup='one' if stacked else None,
                fillcolor=colors[i % len(colors)],
                fill='tonexty' if i > 0 and not stacked else 'tozeroy'
            ))
        
        layout = cls.get_layout_template(title, height)
        layout['showlegend'] = True
        layout['legend'] = {
            'orientation': 'h',
            'y': 1.02,
            'x': 0,
            'font': {'size': 10}
        }
        
        fig.update_layout(**layout)
        return fig
    
    @classmethod
    def create_treemap(
        cls,
        data: pd.DataFrame,
        title: str = "Market Sectors",
        height: int = 500
    ) -> go.Figure:
        """Create professional treemap for hierarchical data"""
        
        # Determine colors based on values
        colors = []
        for val in data.get('change', [0] * len(data)):
            if val > 0:
                colors.append(cls.CHART_THEME['success'])
            elif val < 0:
                colors.append(cls.CHART_THEME['danger'])
            else:
                colors.append(cls.CHART_THEME['warning'])
        
        fig = go.Figure(go.Treemap(
            labels=data.get('labels', data.index),
            parents=data.get('parents', [""]*len(data)),
            values=data.get('values', [1]*len(data)),
            text=data.get('text', data.get('labels', data.index)),
            textposition="middle center",
            textfont=dict(size=12, color=cls.CHART_THEME['text_color']),
            marker=dict(
                colors=colors,
                line=dict(width=2, color=cls.CHART_THEME['bg_color'])
            ),
            hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Change: %{color}<extra></extra>'
        ))
        
        layout = cls.get_layout_template(title, height)
        fig.update_layout(**layout)
        
        return fig
    
    @classmethod
    def create_waterfall_chart(
        cls,
        categories: List[str],
        values: List[float],
        title: str = "P&L Breakdown",
        height: int = 400
    ) -> go.Figure:
        """Create waterfall chart for financial flows"""
        
        fig = go.Figure(go.Waterfall(
            orientation="v",
            x=categories,
            y=values,
            text=[f"{v:+.1f}" for v in values],
            textposition="outside",
            textfont=dict(size=10, color=cls.CHART_THEME['text_color']),
            connector={"line": {"color": cls.CHART_THEME['grid_color'], "width": 1}},
            increasing={"marker": {"color": cls.CHART_THEME['success']}},
            decreasing={"marker": {"color": cls.CHART_THEME['danger']}},
            totals={"marker": {"color": cls.CHART_THEME['primary']}}
        ))
        
        layout = cls.get_layout_template(title, height)
        fig.update_layout(**layout)
        
        return fig
    
    @classmethod
    def create_scatter_matrix(
        cls,
        df: pd.DataFrame,
        dimensions: List[str],
        color_by: str = None,
        title: str = "Factor Analysis",
        height: int = 700
    ) -> go.Figure:
        """Create scatter matrix for multi-dimensional analysis"""
        
        fig = px.scatter_matrix(
            df,
            dimensions=dimensions,
            color=color_by,
            color_continuous_scale=[
                [0, cls.CHART_THEME['danger']],
                [0.5, cls.CHART_THEME['warning']],
                [1, cls.CHART_THEME['success']]
            ]
        )
        
        # Apply professional theme
        fig.update_traces(
            diagonal_visible=False,
            marker=dict(size=3, opacity=0.7),
            showlowerhalf=True
        )
        
        layout = cls.get_layout_template(title, height)
        layout['font']['size'] = 9
        fig.update_layout(**layout)
        
        return fig
    
    @classmethod
    def create_radar_chart(
        cls,
        categories: List[str],
        values: Dict[str, List[float]],
        title: str = "Risk Profile",
        height: int = 400
    ) -> go.Figure:
        """Create radar chart for multi-factor comparison"""
        
        fig = go.Figure()
        
        colors = [
            cls.CHART_THEME['primary'],
            cls.CHART_THEME['success'],
            cls.CHART_THEME['warning']
        ]
        
        for i, (name, vals) in enumerate(values.items()):
            fig.add_trace(go.Scatterpolar(
                r=vals,
                theta=categories,
                fill='toself',
                name=name.upper(),
                line_color=colors[i % len(colors)],
                opacity=0.6
            ))
        
        layout = cls.get_layout_template(title, height)
        layout['polar'] = dict(
            radialaxis=dict(
                visible=True,
                gridcolor=cls.CHART_THEME['grid_color'],
                tickfont=dict(size=9, color=cls.CHART_THEME['text_secondary']),
                range=[0, 100]
            ),
            angularaxis=dict(
                gridcolor=cls.CHART_THEME['grid_color'],
                tickfont=dict(size=10, color=cls.CHART_THEME['text_color'])
            ),
            bgcolor=cls.CHART_THEME['bg_color']
        )
        layout['showlegend'] = len(values) > 1
        
        fig.update_layout(**layout)
        return fig

# Export convenience functions
def render_chart(chart_type: str, data: Any, **kwargs) -> go.Figure:
    """Render any chart type with professional styling"""
    
    chart_methods = {
        'candlestick': ProfessionalCharts.create_candlestick_chart,
        'line': ProfessionalCharts.create_line_chart,
        'heatmap': ProfessionalCharts.create_heatmap,
        'gauge': ProfessionalCharts.create_gauge_chart,
        'area': ProfessionalCharts.create_area_chart,
        'treemap': ProfessionalCharts.create_treemap,
        'waterfall': ProfessionalCharts.create_waterfall_chart,
        'scatter_matrix': ProfessionalCharts.create_scatter_matrix,
        'radar': ProfessionalCharts.create_radar_chart
    }
    
    if chart_type in chart_methods:
        return chart_methods[chart_type](data, **kwargs)
    else:
        raise ValueError(f"Unknown chart type: {chart_type}")