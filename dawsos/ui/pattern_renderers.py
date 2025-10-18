"""Pattern-Specific Renderers - Type-specific visualizations for pattern outputs

This module provides specialized renderers for different pattern response types.
Each renderer understands the data structure for a specific pattern category
and creates rich visualizations using the unified_components library.

Response Types Supported:
- stock_quote: Real-time stock quotes with price, change, volume
- economic_data: Economic indicators and time series
- risk_score: Risk assessments with gauges and breakdowns
- portfolio: Portfolio analysis with allocations and performance
- forecast: Predictions and forecasts with confidence intervals
- analysis: General analysis reports with metrics and recommendations
- valuation: DCF and valuation models with scenarios
- briefing: Morning briefings and market summaries
- governance: Governance reports and compliance checks
- ui_component: UI component data (alerts, dashboards, etc.)
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Import unified components
from ui.unified_components import (
    render_metric_card,
    render_gauge_chart,
    render_time_series_chart,
    render_allocation_pie,
    render_comparison_bars,
    render_metric_grid,
    render_heatmap,
    render_candlestick_chart,
    render_section_header,
    render_info_box
)


def render_stock_quote(data: Dict[str, Any], symbol: Optional[str] = None) -> None:
    """Render a stock quote with price, changes, and key metrics
    
    Args:
        data: Stock quote data from pattern execution
        symbol: Optional symbol override
    """
    if not data or 'error' in data:
        render_info_box("No stock quote data available", "warning")
        return
    
    # Extract data
    symbol = symbol or data.get('symbol', 'N/A')
    name = data.get('name', symbol)
    price = data.get('price', 0)
    change = data.get('change', 0)
    change_pct = data.get('changesPercentage', 0)
    
    # Header with symbol and name
    st.markdown(f"## 📈 {name} ({symbol})")
    
    # Price metrics in grid
    metrics = [
        {
            'title': 'Current Price',
            'value': f"${price:.2f}",
            'icon': '💰',
            'change': change_pct,
            'change_label': 'Daily',
            'help_text': 'Latest traded price'
        },
        {
            'title': 'Day Range',
            'value': f"${data.get('dayLow', 0):.2f} - ${data.get('dayHigh', 0):.2f}",
            'icon': '📊',
            'help_text': "Today's price range"
        },
        {
            'title': 'Volume',
            'value': f"{data.get('volume', 0):,.0f}",
            'icon': '📦',
            'help_text': 'Trading volume'
        },
        {
            'title': 'Market Cap',
            'value': f"${data.get('marketCap', 0) / 1e9:.2f}B" if data.get('marketCap') else 'N/A',
            'icon': '🏢',
            'help_text': 'Market capitalization'
        }
    ]
    
    render_metric_grid(metrics, columns=4)
    
    # Additional details in expander
    with st.expander("📋 Additional Details", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Open", f"${data.get('open', 0):.2f}")
            st.metric("Previous Close", f"${data.get('previousClose', 0):.2f}")
            st.metric("52W High", f"${data.get('yearHigh', 0):.2f}")
        with col2:
            st.metric("Avg Volume", f"{data.get('avgVolume', 0):,.0f}")
            st.metric("P/E Ratio", f"{data.get('pe', 0):.2f}")
            st.metric("52W Low", f"${data.get('yearLow', 0):.2f}")


def render_economic_data(data: Dict[str, Any], title: str = "Economic Indicators") -> None:
    """Render economic indicators with time series charts
    
    Args:
        data: Economic data from pattern execution
        title: Chart title
    """
    if not data or 'error' in data:
        render_info_box("No economic data available", "warning")
        return
    
    st.markdown(f"## 📊 {title}")
    
    # Check if data has time series
    if 'series' in data and isinstance(data['series'], dict):
        # Render each series as a separate chart
        for series_name, series_data in data['series'].items():
            if isinstance(series_data, list) and len(series_data) > 0:
                # Convert to DataFrame
                df = pd.DataFrame(series_data)
                
                # Determine columns
                if 'date' in df.columns and 'value' in df.columns:
                    render_time_series_chart(
                        data=df,
                        title=series_name,
                        x_col='date',
                        y_cols='value',
                        height=350
                    )
    
    # Summary metrics if available
    if 'latest_values' in data:
        metrics = []
        for key, value in data['latest_values'].items():
            metrics.append({
                'title': key,
                'value': f"{value:.2f}" if isinstance(value, (int, float)) else str(value),
                'icon': '📈'
            })
        
        if metrics:
            render_metric_grid(metrics, columns=min(len(metrics), 4), title="Latest Values")


def render_risk_dashboard(data: Dict[str, Any]) -> None:
    """Render a risk assessment dashboard with gauges and breakdowns
    
    Args:
        data: Risk assessment data from pattern execution
    """
    if not data or 'error' in data:
        render_info_box("No risk data available", "warning")
        return
    
    st.markdown("## ⚠️ Risk Assessment Dashboard")
    
    # Overall risk score gauge
    if 'overall_risk_score' in data or 'risk_score' in data:
        score = data.get('overall_risk_score', data.get('risk_score', 50))
        render_gauge_chart(
            value=score,
            title="Overall Risk Score",
            min_value=0,
            max_value=100,
            thresholds={'low': 30, 'medium': 70},
            colors=['#22c55e', '#eab308', '#ef4444']
        )
    
    # Risk breakdown if available
    if 'risk_factors' in data or 'components' in data:
        risk_factors = data.get('risk_factors', data.get('components', {}))
        
        if isinstance(risk_factors, dict):
            st.markdown("### 📊 Risk Factor Breakdown")
            render_comparison_bars(
                data=risk_factors,
                title="Risk Factors",
                orientation='horizontal',
                sort_by_value=True,
                height=300
            )
    
    # Risk details
    if 'analysis' in data or 'interpretation' in data:
        with st.expander("📝 Detailed Analysis", expanded=True):
            st.markdown(data.get('analysis', data.get('interpretation', 'No detailed analysis available')))


def render_portfolio_view(data: Dict[str, Any]) -> None:
    """Render a portfolio analysis with allocations and performance
    
    Args:
        data: Portfolio data from pattern execution
    """
    if not data or 'error' in data:
        render_info_box("No portfolio data available", "warning")
        return
    
    st.markdown("## 💼 Portfolio Analysis")
    
    # Performance metrics
    if 'total_value' in data or 'performance' in data:
        metrics = []
        
        if 'total_value' in data:
            metrics.append({
                'title': 'Total Value',
                'value': f"${data['total_value']:,.2f}",
                'icon': '💰',
                'change': data.get('total_return_pct'),
                'change_label': 'Return'
            })
        
        if 'daily_pnl' in data:
            metrics.append({
                'title': 'Daily P&L',
                'value': f"${data['daily_pnl']:,.2f}",
                'icon': '📈',
                'change': data.get('daily_pnl_pct'),
                'change_label': 'Daily'
            })
        
        if metrics:
            render_metric_grid(metrics, columns=len(metrics))
    
    # Asset allocation
    if 'allocations' in data or 'holdings' in data:
        allocations = data.get('allocations', data.get('holdings', {}))
        
        if isinstance(allocations, dict) and allocations:
            render_allocation_pie(
                allocations=allocations,
                title="Asset Allocation",
                height=400
            )
    
    # Holdings table
    if 'positions' in data:
        with st.expander("📋 Position Details", expanded=False):
            positions_df = pd.DataFrame(data['positions'])
            st.dataframe(positions_df, use_container_width=True)


def render_forecast_chart(data: Dict[str, Any]) -> None:
    """Render a forecast with predictions and confidence intervals
    
    Args:
        data: Forecast data from pattern execution
    """
    if not data or 'error' in data:
        render_info_box("No forecast data available", "warning")
        return
    
    st.markdown("## 🔮 Forecast Analysis")
    
    # Forecast confidence
    if 'confidence' in data:
        confidence_pct = data['confidence'] * 100 if data['confidence'] <= 1 else data['confidence']
        render_gauge_chart(
            value=confidence_pct,
            title="Forecast Confidence",
            min_value=0,
            max_value=100,
            unit="%",
            thresholds={'low': 50, 'medium': 75}
        )
    
    # Forecast values
    if 'predictions' in data or 'forecast' in data:
        forecast_data = data.get('predictions', data.get('forecast'))
        
        if isinstance(forecast_data, list):
            df = pd.DataFrame(forecast_data)
            if not df.empty and 'date' in df.columns:
                render_time_series_chart(
                    data=df,
                    title="Forecast Timeline",
                    x_col='date',
                    y_cols=[col for col in df.columns if col != 'date'][:3],  # Max 3 series
                    height=400
                )
    
    # Forecast summary
    if 'summary' in data or 'interpretation' in data:
        with st.expander("📝 Forecast Summary", expanded=True):
            st.markdown(data.get('summary', data.get('interpretation', 'No summary available')))


def render_analysis_report(data: Dict[str, Any], title: str = "Analysis Report") -> None:
    """Render a general analysis report with metrics and recommendations
    
    Args:
        data: Analysis data from pattern execution
        title: Report title
    """
    if not data or 'error' in data:
        render_info_box("No analysis data available", "warning")
        return
    
    st.markdown(f"## 📊 {title}")
    
    # Key metrics if available
    if 'metrics' in data or 'scores' in data:
        metrics_data = data.get('metrics', data.get('scores', {}))
        
        if isinstance(metrics_data, dict):
            metrics = []
            for key, value in metrics_data.items():
                metrics.append({
                    'title': key.replace('_', ' ').title(),
                    'value': f"{value:.2f}" if isinstance(value, (int, float)) else str(value),
                    'icon': '📊'
                })
            
            if metrics:
                render_metric_grid(metrics, columns=min(len(metrics), 4), title="Key Metrics")
    
    # Main analysis text
    if 'analysis' in data or 'response' in data or 'summary' in data:
        analysis_text = data.get('analysis', data.get('response', data.get('summary', '')))
        if analysis_text:
            st.markdown(analysis_text)
    
    # Recommendations
    if 'recommendations' in data or 'action_items' in data:
        with st.expander("💡 Recommendations", expanded=True):
            recommendations = data.get('recommendations', data.get('action_items', []))
            if isinstance(recommendations, list):
                for rec in recommendations:
                    st.markdown(f"- {rec}")
            else:
                st.markdown(recommendations)


def render_pattern_result(
    result: Dict[str, Any],
    response_type: Optional[str] = None
) -> None:
    """Universal pattern result renderer - routes to appropriate type-specific renderer
    
    This is the main entry point for rendering pattern results. It examines the
    response_type and data structure to determine the best visualization approach.
    
    Args:
        result: Pattern execution result dictionary
        response_type: Optional response type hint (from pattern.response_type)
    """
    if not result:
        render_info_box("No result data to display", "warning")
        return
    
    # Check for errors
    if 'error' in result:
        render_info_box(f"Error: {result['error']}", "error")
        return
    
    # Determine response type
    if not response_type:
        response_type = result.get('response_type', 'unknown')
    
    # Extract data - check multiple possible keys
    data = result.get('data', result.get('output', result.get('result', result)))
    
    # Route to appropriate renderer based on response_type
    if response_type == 'stock_quote' or (response_type and 'stock_price' in response_type):
        render_stock_quote(data, symbol=result.get('symbol'))
    
    elif response_type == 'economic_data' or (response_type and 'economic' in response_type):
        render_economic_data(data, title=result.get('title', 'Economic Indicators'))
    
    elif response_type == 'risk_score' or (response_type and 'risk' in response_type):
        render_risk_dashboard(data)
    
    elif response_type == 'portfolio' or (response_type and 'portfolio' in response_type):
        render_portfolio_view(data)
    
    elif response_type == 'forecast' or (response_type and 'prediction' in response_type):
        render_forecast_chart(data)
    
    elif response_type in ['valuation', 'dcf']:
        # Valuation is similar to analysis but with emphasis on price metrics
        render_analysis_report(data, title="Valuation Analysis")
    
    elif response_type in ['briefing', 'summary', 'morning_briefing']:
        # Briefings get special treatment with section headers
        st.markdown("## 📰 Market Briefing")
        if isinstance(data, dict):
            for section, content in data.items():
                st.markdown(f"### {section.replace('_', ' ').title()}")
                st.markdown(content)
        else:
            st.markdown(result.get('formatted_response', data))
    
    elif response_type == 'governance':
        # Governance reports with compliance checklists
        st.markdown("## ✅ Governance Report")
        render_analysis_report(data, title="Governance Analysis")
    
    elif response_type == 'ui_component':
        # UI components might have custom HTML or special rendering
        st.markdown("## 🎨 UI Component")
        st.markdown(data.get('content', data))
    
    elif response_type in ['analysis', 'deep_analysis']:
        # Generic analysis renderer
        render_analysis_report(data, title=result.get('title', 'Analysis Report'))
    
    else:
        # Fallback: smart auto-detection based on data structure
        render_smart_fallback(result, data)


def render_smart_fallback(result: Dict[str, Any], data: Any) -> None:
    """Smart fallback renderer - auto-detects data type and renders appropriately
    
    This function analyzes the data structure and makes intelligent guesses
    about the best visualization approach.
    
    Args:
        result: Full result dictionary
        data: Extracted data to analyze
    """
    # Check for formatted markdown response first
    if 'formatted_response' in result:
        st.markdown(result['formatted_response'])
        return
    
    # Analyze data structure
    if isinstance(data, dict):
        # Check for common indicators of specific types
        if 'price' in data or 'symbol' in data:
            render_stock_quote(data)
        
        elif 'risk_score' in data or 'overall_risk' in data:
            render_risk_dashboard(data)
        
        elif 'allocations' in data or 'holdings' in data:
            render_portfolio_view(data)
        
        elif 'predictions' in data or 'forecast' in data:
            render_forecast_chart(data)
        
        elif 'series' in data or 'indicators' in data:
            render_economic_data(data)
        
        else:
            # Generic dict rendering
            render_analysis_report(data)
    
    elif isinstance(data, str):
        # Plain text/markdown
        st.markdown(data)
    
    elif isinstance(data, (list, pd.DataFrame)):
        # Tabular data
        if isinstance(data, list):
            data = pd.DataFrame(data)
        st.dataframe(data, use_container_width=True)
    
    else:
        # Last resort - JSON view
        st.json(data)
