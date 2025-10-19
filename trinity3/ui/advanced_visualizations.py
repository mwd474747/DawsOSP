"""Advanced Data Visualizations for DawsOS 3.0"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class AdvancedVisualizations:
    """Create professional-grade financial visualizations"""
    
    # Professional color scheme
    COLORS = {
        'background': '#0A0E27',
        'paper': '#0f1429',
        'grid': '#1a1f3a',
        'text': '#e8e9f3',
        'text_secondary': '#a0a4b8',
        'primary': '#4A9EFF',
        'success': '#10B981',
        'danger': '#EF4444',
        'warning': '#F59E0B',
        'purple': '#8B5CF6',
        'pink': '#EC4899'
    }
    
    @classmethod
    def create_market_heatmap(cls, data: pd.DataFrame, title: str = "Market Heatmap") -> go.Figure:
        """Create a market heatmap visualization"""
        fig = go.Figure(data=go.Treemap(
            labels=data.get('symbol', []),
            parents=data.get('sector', []),
            values=data.get('market_cap', []),
            text=data.get('display_text', []),
            texttemplate='<b>%{label}</b><br>%{text}<br>%{percentParent}',
            marker=dict(
                colorscale=[
                    [0, cls.COLORS['danger']],
                    [0.5, cls.COLORS['paper']],
                    [1, cls.COLORS['success']]
                ],
                cmid=0,
                colorbar=dict(
                    title="Change %",
                    titlefont=dict(color=cls.COLORS['text']),
                    tickfont=dict(color=cls.COLORS['text_secondary'])
                ),
                line=dict(width=1, color=cls.COLORS['grid'])
            ),
            textfont=dict(color='white', size=12),
            hovertemplate='<b>%{label}</b><br>Change: %{color:.2f}%<br>Market Cap: $%{value:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=20, color=cls.COLORS['text'])
            ),
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=600,
            margin=dict(t=50, l=0, r=0, b=0)
        )
        
        return fig
    
    @classmethod
    def create_sector_rotation_chart(cls, sectors: List[str], performances: List[float]) -> go.Figure:
        """Create sector rotation visualization"""
        fig = go.Figure()
        
        # Sort sectors by performance
        sorted_data = sorted(zip(sectors, performances), key=lambda x: x[1], reverse=True)
        sectors, performances = zip(*sorted_data)
        
        colors = [cls.COLORS['success'] if p > 0 else cls.COLORS['danger'] for p in performances]
        
        fig.add_trace(go.Bar(
            x=list(performances),
            y=list(sectors),
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(color=cls.COLORS['grid'], width=1)
            ),
            text=[f"{p:+.2f}%" for p in performances],
            textposition='outside',
            textfont=dict(color=cls.COLORS['text'], size=11),
            hovertemplate='<b>%{y}</b><br>Performance: %{x:+.2f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(
                text="Sector Performance Rotation",
                font=dict(size=18, color=cls.COLORS['text'])
            ),
            xaxis=dict(
                title="Performance (%)",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary']),
                zeroline=True,
                zerolinecolor=cls.COLORS['text_secondary'],
                zerolinewidth=2
            ),
            yaxis=dict(
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text'])
            ),
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=400,
            margin=dict(l=120, r=50, t=50, b=50),
            showlegend=False
        )
        
        return fig
    
    @classmethod
    def create_correlation_matrix(cls, data: pd.DataFrame, title: str = "Asset Correlation Matrix") -> go.Figure:
        """Create correlation matrix heatmap"""
        corr = data.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale=[
                [0, cls.COLORS['danger']],
                [0.5, cls.COLORS['paper']],
                [1, cls.COLORS['success']]
            ],
            zmid=0,
            text=np.round(corr.values, 2),
            texttemplate='%{text}',
            textfont=dict(size=10, color='white'),
            colorbar=dict(
                title="Correlation",
                titlefont=dict(color=cls.COLORS['text']),
                tickfont=dict(color=cls.COLORS['text_secondary'])
            ),
            hovertemplate='%{y} vs %{x}<br>Correlation: %{z:.3f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=18, color=cls.COLORS['text'])
            ),
            xaxis=dict(
                tickfont=dict(color=cls.COLORS['text_secondary']),
                side='bottom'
            ),
            yaxis=dict(
                tickfont=dict(color=cls.COLORS['text_secondary'])
            ),
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=500,
            width=600
        )
        
        return fig
    
    @classmethod
    def create_volume_profile(cls, price_data: pd.DataFrame) -> go.Figure:
        """Create volume profile chart"""
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.7, 0.3],
            horizontal_spacing=0.01,
            specs=[[{"secondary_y": True}, {"secondary_y": False}]]
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=price_data['date'],
                open=price_data['open'],
                high=price_data['high'],
                low=price_data['low'],
                close=price_data['close'],
                name='Price',
                increasing_line_color=cls.COLORS['success'],
                decreasing_line_color=cls.COLORS['danger']
            ),
            row=1, col=1, secondary_y=False
        )
        
        # Volume bars
        colors = [cls.COLORS['success'] if close > open else cls.COLORS['danger'] 
                 for close, open in zip(price_data['close'], price_data['open'])]
        
        fig.add_trace(
            go.Bar(
                x=price_data['date'],
                y=price_data['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.5
            ),
            row=1, col=1, secondary_y=True
        )
        
        # Volume profile histogram
        price_bins = np.linspace(price_data['low'].min(), price_data['high'].max(), 50)
        volume_profile = []
        
        for i in range(len(price_bins) - 1):
            mask = (price_data['low'] <= price_bins[i+1]) & (price_data['high'] >= price_bins[i])
            volume_profile.append(price_data[mask]['volume'].sum())
        
        fig.add_trace(
            go.Bar(
                x=volume_profile,
                y=price_bins[:-1],
                orientation='h',
                name='Volume Profile',
                marker_color=cls.COLORS['primary'],
                opacity=0.7
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title=dict(
                text="Price Action & Volume Profile",
                font=dict(size=18, color=cls.COLORS['text'])
            ),
            xaxis=dict(
                gridcolor=cls.COLORS['grid'],
                tickfont=dict(color=cls.COLORS['text_secondary']),
                rangeslider=dict(visible=False)
            ),
            yaxis=dict(
                title="Price",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary'])
            ),
            yaxis2=dict(
                title="Volume",
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary']),
                showgrid=False
            ),
            xaxis2=dict(
                title="Volume",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary'])
            ),
            yaxis3=dict(
                title="Price Level",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary'])
            ),
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=500,
            showlegend=False,
            hovermode='x unified'
        )
        
        return fig
    
    @classmethod
    def create_momentum_indicators(cls, data: pd.DataFrame) -> go.Figure:
        """Create momentum indicators dashboard"""
        fig = make_subplots(
            rows=3, cols=1,
            row_heights=[0.5, 0.25, 0.25],
            vertical_spacing=0.02,
            subplot_titles=("Price & Moving Averages", "RSI", "MACD")
        )
        
        # Price and moving averages
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['close'],
                name='Price',
                line=dict(color=cls.COLORS['primary'], width=2)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['sma_20'],
                name='SMA 20',
                line=dict(color=cls.COLORS['warning'], width=1, dash='dot')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['sma_50'],
                name='SMA 50',
                line=dict(color=cls.COLORS['purple'], width=1, dash='dot')
            ),
            row=1, col=1
        )
        
        # RSI
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['rsi'],
                name='RSI',
                line=dict(color=cls.COLORS['pink'], width=2)
            ),
            row=2, col=1
        )
        
        # RSI bands
        fig.add_hline(y=70, line_dash="dash", line_color=cls.COLORS['danger'], 
                     row=2, col=1, opacity=0.5)
        fig.add_hline(y=30, line_dash="dash", line_color=cls.COLORS['success'], 
                     row=2, col=1, opacity=0.5)
        
        # MACD
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['macd'],
                name='MACD',
                line=dict(color=cls.COLORS['primary'], width=2)
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['macd_signal'],
                name='Signal',
                line=dict(color=cls.COLORS['warning'], width=1)
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=data['date'],
                y=data['macd_histogram'],
                name='Histogram',
                marker_color=cls.COLORS['text_secondary'],
                opacity=0.3
            ),
            row=3, col=1
        )
        
        # Update layout
        fig.update_xaxes(gridcolor=cls.COLORS['grid'], tickfont=dict(color=cls.COLORS['text_secondary']))
        fig.update_yaxes(gridcolor=cls.COLORS['grid'], tickfont=dict(color=cls.COLORS['text_secondary']))
        
        fig.update_layout(
            title=dict(
                text="Momentum Indicators Dashboard",
                font=dict(size=18, color=cls.COLORS['text'])
            ),
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=700,
            showlegend=True,
            legend=dict(
                font=dict(color=cls.COLORS['text_secondary']),
                bgcolor=cls.COLORS['paper'],
                bordercolor=cls.COLORS['grid'],
                borderwidth=1
            ),
            hovermode='x unified'
        )
        
        # Update subplot titles color
        for annotation in fig['layout']['annotations']:
            annotation['font'] = dict(color=cls.COLORS['text'], size=12)
        
        return fig
    
    @classmethod
    def create_options_flow(cls, options_data: pd.DataFrame) -> go.Figure:
        """Create options flow visualization"""
        fig = go.Figure()
        
        # Separate calls and puts
        calls = options_data[options_data['type'] == 'CALL']
        puts = options_data[options_data['type'] == 'PUT']
        
        # Bubble chart for options flow
        fig.add_trace(go.Scatter(
            x=calls['strike'],
            y=calls['expiry_days'],
            mode='markers',
            name='Calls',
            marker=dict(
                size=calls['volume'] / 100,
                color=calls['premium'],
                colorscale=[[0, cls.COLORS['paper']], [1, cls.COLORS['success']]],
                showscale=True,
                colorbar=dict(
                    title="Premium",
                    x=1.1,
                    titlefont=dict(color=cls.COLORS['text']),
                    tickfont=dict(color=cls.COLORS['text_secondary'])
                ),
                line=dict(width=1, color=cls.COLORS['grid'])
            ),
            text=calls['symbol'],
            hovertemplate='<b>%{text}</b><br>Strike: $%{x}<br>Days to Expiry: %{y}<br>Premium: $%{marker.color:.2f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=puts['strike'],
            y=puts['expiry_days'],
            mode='markers',
            name='Puts',
            marker=dict(
                size=puts['volume'] / 100,
                color=puts['premium'],
                colorscale=[[0, cls.COLORS['paper']], [1, cls.COLORS['danger']]],
                showscale=False,
                line=dict(width=1, color=cls.COLORS['grid'])
            ),
            text=puts['symbol'],
            hovertemplate='<b>%{text}</b><br>Strike: $%{x}<br>Days to Expiry: %{y}<br>Premium: $%{marker.color:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(
                text="Options Flow Analysis",
                font=dict(size=18, color=cls.COLORS['text'])
            ),
            xaxis=dict(
                title="Strike Price ($)",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary'])
            ),
            yaxis=dict(
                title="Days to Expiry",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary'])
            ),
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=500,
            legend=dict(
                font=dict(color=cls.COLORS['text_secondary']),
                bgcolor=cls.COLORS['paper'],
                bordercolor=cls.COLORS['grid'],
                borderwidth=1
            )
        )
        
        return fig
    
    @classmethod
    def create_economic_calendar(cls, events: List[Dict[str, Any]]) -> go.Figure:
        """Create economic calendar visualization"""
        df = pd.DataFrame(events)
        
        # Create Gantt-like chart for events
        fig = go.Figure()
        
        # Group events by importance
        high_importance = df[df['importance'] == 'High']
        medium_importance = df[df['importance'] == 'Medium']
        low_importance = df[df['importance'] == 'Low']
        
        for idx, event in high_importance.iterrows():
            fig.add_trace(go.Scatter(
                x=[event['date'], event['date']],
                y=[idx, idx],
                mode='markers+text',
                marker=dict(size=12, color=cls.COLORS['danger']),
                text=event['event'],
                textposition='middle right',
                textfont=dict(color=cls.COLORS['text'], size=10),
                showlegend=False,
                hovertemplate='<b>%{text}</b><br>Date: %{x}<br>Impact: High<br>Forecast: %{customdata}<extra></extra>',
                customdata=[event.get('forecast', 'N/A')]
            ))
        
        fig.update_layout(
            title=dict(
                text="Economic Calendar - Upcoming Events",
                font=dict(size=18, color=cls.COLORS['text'])
            ),
            xaxis=dict(
                title="Date",
                type='date',
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary'])
            ),
            yaxis=dict(
                title="Events",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary']),
                showticklabels=False
            ),
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=400,
            hovermode='closest'
        )
        
        return fig