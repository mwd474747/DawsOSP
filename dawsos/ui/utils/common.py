#!/usr/bin/env python3
"""
Common UI Utilities

Shared UI components and helpers used across DawsOS UI modules.
Consolidates common patterns to reduce duplication and improve maintainability.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime


def render_confidence_display(confidence: float, label: str = "Confidence") -> None:
    """
    Render a confidence score with appropriate styling.

    Args:
        confidence: Confidence score (0.0 to 1.0)
        label: Label for the metric
    """
    color = "green" if confidence > 0.8 else "orange" if confidence > 0.6 else "red"
    st.markdown(f"**{label}:** :{color}[{confidence:.1%}]")


def format_timestamp(timestamp: str, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format an ISO timestamp string for display.

    Args:
        timestamp: ISO format timestamp string
        format: strftime format string

    Returns:
        Formatted timestamp string
    """
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime(format)
    except (ValueError, TypeError):
        return timestamp


def render_metric_card(
    label: str,
    value: Any,
    delta: Optional[Any] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None
) -> None:
    """
    Render a standardized metric card.

    Args:
        label: Metric label
        value: Metric value
        delta: Delta value (optional)
        delta_color: Color for delta ("normal", "inverse", "off")
        help_text: Help tooltip text
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )


def render_status_badge(status: str, custom_colors: Optional[Dict[str, str]] = None) -> None:
    """
    Render a colored status badge.

    Args:
        status: Status text
        custom_colors: Optional dict mapping status to color
    """
    default_colors = {
        'active': 'green',
        'inactive': 'gray',
        'error': 'red',
        'warning': 'orange',
        'success': 'green',
        'pending': 'blue'
    }

    colors = custom_colors or default_colors
    color = colors.get(status.lower(), 'gray')

    st.markdown(
        f'<span style="background-color: {color}; color: white; padding: 3px 8px; '
        f'border-radius: 12px; font-size: 12px;">{status}</span>',
        unsafe_allow_html=True
    )


def render_expandable_json(data: Dict[str, Any], label: str = "View Details") -> None:
    """
    Render JSON data in an expandable section.

    Args:
        data: Dictionary data to display
        label: Expander label
    """
    with st.expander(label):
        st.json(data)


def render_progress_bar(value: float, label: str = "", format: str = "percent") -> None:
    """
    Render a progress bar with label.

    Args:
        value: Progress value (0.0 to 1.0)
        label: Label text
        format: Format ("percent" or "fraction")
    """
    if label:
        st.markdown(f"**{label}**")

    st.progress(value)

    if format == "percent":
        st.caption(f"{value:.0%}")
    else:
        st.caption(f"{value:.2f}")


def render_error_message(error: Exception, context: str = "") -> None:
    """
    Render a standardized error message.

    Args:
        error: Exception object
        context: Additional context about where error occurred
    """
    if context:
        st.error(f"Error in {context}: {str(error)}")
    else:
        st.error(f"Error: {str(error)}")


def render_success_message(message: str, details: Optional[str] = None) -> None:
    """
    Render a standardized success message.

    Args:
        message: Success message
        details: Optional additional details
    """
    st.success(f"✅ {message}")
    if details:
        st.caption(details)


def render_warning_message(message: str, details: Optional[str] = None) -> None:
    """
    Render a standardized warning message.

    Args:
        message: Warning message
        details: Optional additional details
    """
    st.warning(f"⚠️ {message}")
    if details:
        st.caption(details)


def render_info_message(message: str, details: Optional[str] = None) -> None:
    """
    Render a standardized info message.

    Args:
        message: Info message
        details: Optional additional details
    """
    st.info(f"ℹ️ {message}")
    if details:
        st.caption(details)


def render_key_value_pair(key: str, value: Any, format_func: Optional[callable] = None) -> None:
    """
    Render a key-value pair with optional formatting.

    Args:
        key: Key label
        value: Value to display
        format_func: Optional function to format the value
    """
    formatted_value = format_func(value) if format_func else value
    st.markdown(f"**{key}:** {formatted_value}")


def render_section_header(title: str, icon: str = "", subtitle: Optional[str] = None) -> None:
    """
    Render a consistent section header.

    Args:
        title: Section title
        icon: Optional emoji icon
        subtitle: Optional subtitle text
    """
    header_text = f"{icon} {title}" if icon else title
    st.markdown(f"### {header_text}")
    if subtitle:
        st.markdown(f"*{subtitle}*")


def render_data_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    hide_index: bool = True
) -> None:
    """
    Render a data table from list of dictionaries.

    Args:
        data: List of dictionaries
        columns: Optional list of columns to display
        hide_index: Whether to hide the index column
    """
    import pandas as pd

    if not data:
        st.info("No data available")
        return

    df = pd.DataFrame(data)
    if columns:
        df = df[columns]

    st.dataframe(df, hide_index=hide_index)


# Pattern browser is module-specific, keeping in pattern_browser.py
# render_pattern_browser function stays in its dedicated module

# Thinking trace is module-specific, keeping in intelligence_display.py
# render_thinking_trace function stays in its dedicated module

__all__ = [
    'render_confidence_display',
    'format_timestamp',
    'render_metric_card',
    'render_status_badge',
    'render_expandable_json',
    'render_progress_bar',
    'render_error_message',
    'render_success_message',
    'render_warning_message',
    'render_info_message',
    'render_key_value_pair',
    'render_section_header',
    'render_data_table'
]
