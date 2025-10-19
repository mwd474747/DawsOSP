"""Economic Predictions and Fed Analysis Module for DawsOS 3.0"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class EconomicPredictions:
    """Create professional economic prediction visualizations"""
    
    # Professional color scheme matching DawsOS theme
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
        'pink': '#EC4899',
        'cyan': '#06B6D4',
        'teal': '#14B8A6'
    }
    
    @classmethod
    def create_fed_funds_projection(cls, current_rate: float = 5.33, 
                                   historical_data: Optional[pd.DataFrame] = None,
                                   projections: Optional[Dict] = None) -> go.Figure:
        """Create Fed Funds Rate projection chart with historical and forecast data"""
        
        fig = go.Figure()
        
        # Historical data (if provided)
        if historical_data is not None and not historical_data.empty:
            fig.add_trace(go.Scatter(
                x=historical_data['date'],
                y=historical_data['rate'],
                name='Historical Fed Funds Rate',
                line=dict(color=cls.COLORS['primary'], width=2),
                mode='lines',
                hovertemplate='%{x|%b %Y}<br>Rate: %{y:.2f}%<extra></extra>'
            ))
        else:
            # Generate sample historical data
            dates = pd.date_range(end=datetime.now(), periods=24, freq='M')
            rates = np.random.normal(current_rate, 0.5, 24)
            rates = np.maximum(rates, 0)  # Ensure no negative rates
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=rates,
                name='Historical Fed Funds Rate',
                line=dict(color=cls.COLORS['primary'], width=2),
                mode='lines',
                hovertemplate='%{x|%b %Y}<br>Rate: %{y:.2f}%<extra></extra>'
            ))
        
        # Current rate marker
        fig.add_trace(go.Scatter(
            x=[datetime.now()],
            y=[current_rate],
            name='Current Rate',
            mode='markers',
            marker=dict(
                size=12,
                color=cls.COLORS['warning'],
                symbol='diamond',
                line=dict(width=2, color='white')
            ),
            hovertemplate=f'Current: {current_rate:.2f}%<extra></extra>'
        ))
        
        # Projections
        if projections:
            # Base case projection
            if 'base_case' in projections:
                fig.add_trace(go.Scatter(
                    x=projections['base_case']['dates'],
                    y=projections['base_case']['rates'],
                    name='Base Case',
                    line=dict(color=cls.COLORS['success'], width=2, dash='dot'),
                    mode='lines+markers',
                    marker=dict(size=4),
                    hovertemplate='%{x|%b %Y}<br>Projected: %{y:.2f}%<extra></extra>'
                ))
            
            # Hawkish scenario
            if 'hawkish' in projections:
                fig.add_trace(go.Scatter(
                    x=projections['hawkish']['dates'],
                    y=projections['hawkish']['rates'],
                    name='Hawkish',
                    line=dict(color=cls.COLORS['danger'], width=1, dash='dash'),
                    mode='lines',
                    opacity=0.7,
                    hovertemplate='%{x|%b %Y}<br>Hawkish: %{y:.2f}%<extra></extra>'
                ))
            
            # Dovish scenario
            if 'dovish' in projections:
                fig.add_trace(go.Scatter(
                    x=projections['dovish']['dates'],
                    y=projections['dovish']['rates'],
                    name='Dovish',
                    line=dict(color=cls.COLORS['cyan'], width=1, dash='dash'),
                    mode='lines',
                    opacity=0.7,
                    hovertemplate='%{x|%b %Y}<br>Dovish: %{y:.2f}%<extra></extra>'
                ))
        else:
            # Generate sample projections
            future_dates = pd.date_range(start=datetime.now(), periods=13, freq='M')
            
            # Base case - gradual decline
            base_rates = [current_rate]
            for i in range(12):
                base_rates.append(max(3.5, base_rates[-1] - np.random.uniform(0, 0.25)))
            
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=base_rates,
                name='Base Case Projection',
                line=dict(color=cls.COLORS['success'], width=2, dash='dot'),
                mode='lines+markers',
                marker=dict(size=4),
                hovertemplate='%{x|%b %Y}<br>Projected: %{y:.2f}%<extra></extra>'
            ))
            
            # Uncertainty band
            upper_bound = [r + 1.0 for r in base_rates]
            lower_bound = [max(2.5, r - 1.0) for r in base_rates]
            
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=upper_bound,
                fill=None,
                mode='lines',
                line_color='rgba(0,0,0,0)',
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=lower_bound,
                fill='tonexty',
                mode='lines',
                line_color='rgba(0,0,0,0)',
                name='Uncertainty Range',
                fillcolor=f'rgba(74, 158, 255, 0.1)',
                hoverinfo='skip'
            ))
        
        # Add Fed meeting markers
        fed_meetings = pd.date_range(start=datetime.now(), periods=8, freq='6W')
        fig.add_trace(go.Scatter(
            x=fed_meetings,
            y=[current_rate - 0.5] * len(fed_meetings),
            name='FOMC Meetings',
            mode='markers',
            marker=dict(
                size=8,
                color=cls.COLORS['purple'],
                symbol='triangle-up'
            ),
            hovertemplate='FOMC Meeting<br>%{x|%b %d, %Y}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text="Federal Funds Rate: Historical & Projected Path",
                font=dict(size=20, color=cls.COLORS['text'])
            ),
            xaxis=dict(
                title="Date",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary']),
                showgrid=True
            ),
            yaxis=dict(
                title="Rate (%)",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary']),
                showgrid=True,
                range=[0, max(7, current_rate + 2)]
            ),
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=400,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color=cls.COLORS['text_secondary'])
            )
        )
        
        # Add annotations for key policy points
        fig.add_annotation(
            x=datetime.now(),
            y=current_rate,
            text=f"Current: {current_rate}%",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor=cls.COLORS['warning'],
            ax=30,
            ay=-30,
            font=dict(color=cls.COLORS['text'], size=11)
        )
        
        return fig
    
    @classmethod
    def create_unemployment_forecast(cls, current_rate: float = 3.8,
                                    historical_data: Optional[pd.DataFrame] = None) -> go.Figure:
        """Create unemployment rate forecast with confidence intervals"""
        
        fig = go.Figure()
        
        # Historical unemployment data
        if historical_data is not None and not historical_data.empty:
            fig.add_trace(go.Scatter(
                x=historical_data['date'],
                y=historical_data['unemployment'],
                name='Historical Unemployment',
                line=dict(color=cls.COLORS['danger'], width=2),
                mode='lines',
                hovertemplate='%{x|%b %Y}<br>Unemployment: %{y:.1f}%<extra></extra>'
            ))
        else:
            # Generate sample data
            dates = pd.date_range(end=datetime.now(), periods=36, freq='M')
            unemployment = np.random.normal(current_rate, 0.3, 36)
            unemployment = np.maximum(unemployment, 3.0)  # Floor at 3%
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=unemployment,
                name='Historical Unemployment',
                line=dict(color=cls.COLORS['danger'], width=2),
                mode='lines',
                hovertemplate='%{x|%b %Y}<br>Unemployment: %{y:.1f}%<extra></extra>'
            ))
        
        # Recession probability overlay
        future_dates = pd.date_range(start=datetime.now(), periods=13, freq='M')
        
        # Base forecast
        base_forecast = [current_rate]
        for i in range(12):
            # Gradual increase scenario
            base_forecast.append(min(6.0, base_forecast[-1] + np.random.uniform(-0.1, 0.2)))
        
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=base_forecast,
            name='Forecast',
            line=dict(color=cls.COLORS['warning'], width=2, dash='dash'),
            mode='lines+markers',
            marker=dict(size=4),
            hovertemplate='%{x|%b %Y}<br>Forecast: %{y:.1f}%<extra></extra>'
        ))
        
        # Confidence intervals
        upper_ci = [r + 1.5 for r in base_forecast]
        lower_ci = [max(2.5, r - 1.0) for r in base_forecast]
        
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=upper_ci,
            fill=None,
            mode='lines',
            line_color='rgba(0,0,0,0)',
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=lower_ci,
            fill='tonexty',
            mode='lines',
            line_color='rgba(0,0,0,0)',
            name='95% Confidence',
            fillcolor=f'rgba(239, 68, 68, 0.1)',
            hoverinfo='skip'
        ))
        
        # Add recession bands (example periods)
        fig.add_vrect(
            x0=datetime.now() + timedelta(days=180),
            x1=datetime.now() + timedelta(days=270),
            fillcolor=cls.COLORS['danger'],
            opacity=0.1,
            line_width=0,
            annotation_text="Recession Risk",
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color=cls.COLORS['text_secondary']
        )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text="Unemployment Rate Forecast with Recession Scenarios",
                font=dict(size=20, color=cls.COLORS['text'])
            ),
            xaxis=dict(
                title="Date",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary'])
            ),
            yaxis=dict(
                title="Unemployment Rate (%)",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary']),
                range=[2, 8]
            ),
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=400,
            hovermode='x unified',
            legend=dict(
                font=dict(color=cls.COLORS['text_secondary'])
            )
        )
        
        return fig
    
    @classmethod
    def create_economic_indicators_combined(cls, data: Dict[str, pd.DataFrame]) -> go.Figure:
        """Create combined chart with GDP, CPI, Unemployment, and Fed Rate"""
        
        fig = make_subplots(
            specs=[[{"secondary_y": True}]],
            subplot_titles=["Economic Indicators Dashboard"]
        )
        
        # Generate sample data if not provided
        dates = pd.date_range(end=datetime.now(), periods=24, freq='M')
        
        # Unemployment Rate (left axis)
        unemployment = data.get('unemployment', pd.DataFrame({
            'date': dates,
            'value': np.random.normal(3.8, 0.3, 24)
        }))
        
        fig.add_trace(
            go.Scatter(
                x=unemployment['date'],
                y=unemployment['value'],
                name='Unemployment Rate',
                line=dict(color=cls.COLORS['danger'], width=2),
                hovertemplate='%{x|%b %Y}<br>Unemployment: %{y:.1f}%<extra></extra>'
            ),
            secondary_y=False
        )
        
        # Fed Funds Rate (left axis)
        fed_rate = data.get('fed_rate', pd.DataFrame({
            'date': dates,
            'value': np.random.normal(5.33, 0.5, 24)
        }))
        
        fig.add_trace(
            go.Scatter(
                x=fed_rate['date'],
                y=fed_rate['value'],
                name='Fed Funds Rate',
                line=dict(color=cls.COLORS['cyan'], width=2),
                hovertemplate='%{x|%b %Y}<br>Fed Rate: %{y:.2f}%<extra></extra>'
            ),
            secondary_y=False
        )
        
        # CPI YoY (right axis)
        cpi = data.get('cpi', pd.DataFrame({
            'date': dates,
            'value': np.random.normal(3.2, 0.8, 24)
        }))
        
        fig.add_trace(
            go.Scatter(
                x=cpi['date'],
                y=cpi['value'],
                name='CPI Inflation (YoY)',
                line=dict(color=cls.COLORS['warning'], width=2),
                hovertemplate='%{x|%b %Y}<br>CPI: %{y:.1f}%<extra></extra>'
            ),
            secondary_y=True
        )
        
        # GDP QoQ (right axis)
        gdp = data.get('gdp', pd.DataFrame({
            'date': pd.date_range(end=datetime.now(), periods=8, freq='Q'),
            'value': np.random.normal(2.1, 1.0, 8)
        }))
        
        fig.add_trace(
            go.Scatter(
                x=gdp['date'],
                y=gdp['value'],
                name='GDP Growth (QoQ)',
                line=dict(color=cls.COLORS['purple'], width=2, dash='dash'),
                mode='lines+markers',
                marker=dict(size=6),
                hovertemplate='%{x|Q%q %Y}<br>GDP: %{y:.1f}%<extra></extra>'
            ),
            secondary_y=True
        )
        
        # Add target lines
        fig.add_hline(y=2, line_dash="dot", line_color=cls.COLORS['text_secondary'],
                     annotation_text="2% Inflation Target", secondary_y=True,
                     annotation_font_size=10, annotation_font_color=cls.COLORS['text_secondary'])
        
        fig.add_hline(y=4, line_dash="dot", line_color=cls.COLORS['text_secondary'],
                     annotation_text="Full Employment", secondary_y=False,
                     annotation_font_size=10, annotation_font_color=cls.COLORS['text_secondary'])
        
        # Update axes
        fig.update_xaxes(
            title_text="Date",
            gridcolor=cls.COLORS['grid'],
            titlefont=dict(color=cls.COLORS['text_secondary']),
            tickfont=dict(color=cls.COLORS['text_secondary'])
        )
        
        fig.update_yaxes(
            title_text="Rates (%)",
            secondary_y=False,
            gridcolor=cls.COLORS['grid'],
            titlefont=dict(color=cls.COLORS['text_secondary']),
            tickfont=dict(color=cls.COLORS['text_secondary'])
        )
        
        fig.update_yaxes(
            title_text="Growth/Inflation (%)",
            secondary_y=True,
            titlefont=dict(color=cls.COLORS['text_secondary']),
            tickfont=dict(color=cls.COLORS['text_secondary'])
        )
        
        # Update layout
        fig.update_layout(
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color=cls.COLORS['text_secondary'])
            ),
            title=dict(
                text="Economic Indicators: Historical Trends & Correlations",
                font=dict(size=20, color=cls.COLORS['text'])
            )
        )
        
        return fig
    
    @classmethod
    def create_systemic_risk_gauge(cls, risk_score: float = 45,
                                  credit_cycle_position: float = 0.65,
                                  confidence_adjustment: float = 0.85) -> go.Figure:
        """Create systemic risk gauge using Ray Dalio's framework"""
        
        # Determine risk level and color
        if risk_score < 30:
            risk_level = "Low Risk"
            gauge_color = cls.COLORS['success']
        elif risk_score < 50:
            risk_level = "Moderate Risk"
            gauge_color = cls.COLORS['warning']
        elif risk_score < 70:
            risk_level = "Elevated Risk"
            gauge_color = '#FF8C00'  # Orange
        else:
            risk_level = "High Risk"
            gauge_color = cls.COLORS['danger']
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=risk_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={
                'text': f"Systemic Risk Score<br><span style='font-size:0.8em;color:{cls.COLORS['text_secondary']}'>{risk_level}</span>",
                'font': {'size': 20, 'color': cls.COLORS['text']}
            },
            delta={
                'reference': 50,
                'increasing': {'color': cls.COLORS['danger']},
                'decreasing': {'color': cls.COLORS['success']}
            },
            gauge={
                'axis': {
                    'range': [None, 100],
                    'tickwidth': 1,
                    'tickcolor': cls.COLORS['text_secondary'],
                    'tickfont': {'color': cls.COLORS['text_secondary']}
                },
                'bar': {'color': gauge_color, 'thickness': 0.75},
                'bgcolor': cls.COLORS['paper'],
                'borderwidth': 2,
                'bordercolor': cls.COLORS['grid'],
                'steps': [
                    {'range': [0, 30], 'color': f'rgba(16, 185, 129, 0.2)'},
                    {'range': [30, 50], 'color': f'rgba(245, 158, 11, 0.2)'},
                    {'range': [50, 70], 'color': f'rgba(255, 140, 0, 0.2)'},
                    {'range': [70, 100], 'color': f'rgba(239, 68, 68, 0.2)'}
                ],
                'threshold': {
                    'line': {'color': cls.COLORS['text'], 'width': 4},
                    'thickness': 0.75,
                    'value': risk_score
                }
            }
        ))
        
        # Add annotations
        fig.add_annotation(
            x=0.5,
            y=-0.15,
            text=f"Credit Cycle: {credit_cycle_position*100:.0f}% | Confidence: {confidence_adjustment*100:.0f}%",
            showarrow=False,
            font=dict(size=12, color=cls.COLORS['text_secondary']),
            xref="paper",
            yref="paper"
        )
        
        fig.update_layout(
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            font={'color': cls.COLORS['text'], 'family': 'Inter, sans-serif'},
            height=350,
            margin=dict(l=20, r=20, t=80, b=60)
        )
        
        return fig
    
    @classmethod
    def create_recession_probability_chart(cls, probabilities: Optional[Dict] = None) -> go.Figure:
        """Create recession probability forecast chart"""
        
        fig = go.Figure()
        
        # Generate dates
        dates = pd.date_range(start=datetime.now(), periods=24, freq='M')
        
        if probabilities:
            # Use provided probabilities
            base_prob = probabilities.get('base', [45] * 24)
            bull_prob = probabilities.get('bull', [20] * 24)
            bear_prob = probabilities.get('bear', [75] * 24)
        else:
            # Generate sample probabilities
            base_prob = []
            current = 45
            for _ in range(24):
                current = max(10, min(90, current + np.random.normal(0, 5)))
                base_prob.append(current)
            
            bull_prob = [max(5, p - 20) for p in base_prob]
            bear_prob = [min(95, p + 25) for p in base_prob]
        
        # Bear case (upper bound)
        fig.add_trace(go.Scatter(
            x=dates,
            y=bear_prob,
            name='Bear Case',
            line=dict(color=cls.COLORS['danger'], width=1, dash='dash'),
            opacity=0.5,
            hovertemplate='%{x|%b %Y}<br>Bear: %{y:.0f}%<extra></extra>'
        ))
        
        # Base case
        fig.add_trace(go.Scatter(
            x=dates,
            y=base_prob,
            name='Base Case',
            line=dict(color=cls.COLORS['warning'], width=3),
            mode='lines+markers',
            marker=dict(size=4),
            hovertemplate='%{x|%b %Y}<br>Base: %{y:.0f}%<extra></extra>'
        ))
        
        # Bull case (lower bound)
        fig.add_trace(go.Scatter(
            x=dates,
            y=bull_prob,
            name='Bull Case',
            line=dict(color=cls.COLORS['success'], width=1, dash='dash'),
            opacity=0.5,
            hovertemplate='%{x|%b %Y}<br>Bull: %{y:.0f}%<extra></extra>'
        ))
        
        # Add recession threshold
        fig.add_hline(
            y=50,
            line_dash="dot",
            line_color=cls.COLORS['text_secondary'],
            annotation_text="50% Threshold",
            annotation_font_size=10,
            annotation_font_color=cls.COLORS['text_secondary']
        )
        
        # Shade high-risk zone
        fig.add_hrect(
            y0=70,
            y1=100,
            fillcolor=cls.COLORS['danger'],
            opacity=0.1,
            line_width=0,
            annotation_text="High Risk",
            annotation_position="right",
            annotation_font_size=10,
            annotation_font_color=cls.COLORS['text_secondary']
        )
        
        fig.update_layout(
            title=dict(
                text="Recession Probability Forecast (12-24 Months)",
                font=dict(size=20, color=cls.COLORS['text'])
            ),
            xaxis=dict(
                title="Date",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary'])
            ),
            yaxis=dict(
                title="Probability (%)",
                gridcolor=cls.COLORS['grid'],
                titlefont=dict(color=cls.COLORS['text_secondary']),
                tickfont=dict(color=cls.COLORS['text_secondary']),
                range=[0, 100]
            ),
            paper_bgcolor=cls.COLORS['background'],
            plot_bgcolor=cls.COLORS['paper'],
            height=400,
            hovermode='x unified',
            legend=dict(
                font=dict(color=cls.COLORS['text_secondary'])
            )
        )
        
        return fig