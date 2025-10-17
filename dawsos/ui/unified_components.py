"""Unified UI Components - Reusable, consistent UI elements

Provides standardized components for better visual organization across all tabs:
- Metric cards with consistent styling
- Status indicators for data freshness
- Collapsible sections for advanced features
- Analysis result displays with better formatting
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import pandas as pd


def render_metric_card(
    title: str,
    value: Union[str, float, int],
    icon: str = "📊",
    change: Optional[float] = None,
    change_label: str = "Daily",
    subtitle: Optional[str] = None,
    help_text: Optional[str] = None
) -> None:
    """Render a unified metric card with consistent styling

    Args:
        title: Card title/label
        value: Main value to display
        icon: Emoji icon for the card
        change: Optional change value (percentage or absolute)
        change_label: Label for the change (e.g., "Daily", "YTD", "MTD")
        subtitle: Optional subtitle text
        help_text: Optional help/tooltip text
    """
    with st.container():
        # Header with icon and title
        if help_text:
            st.markdown(f"{icon} **{title}**", help=help_text)
        else:
            st.markdown(f"{icon} **{title}**")

        # Main value (larger font)
        if isinstance(value, (float, int)):
            st.markdown(f"<h2 style='margin:0;'>{value:,.2f}</h2>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h2 style='margin:0;'>{value}</h2>", unsafe_allow_html=True)

        # Change indicator
        if change is not None:
            color = "green" if change >= 0 else "red"
            sign = "+" if change >= 0 else ""
            st.markdown(
                f"<p style='color:{color}; margin:0;'>{sign}{change:.2f}% {change_label}</p>",
                unsafe_allow_html=True
            )

        # Subtitle
        if subtitle:
            st.caption(subtitle)


def render_data_status_bar(
    timestamp: Optional[datetime] = None,
    source: str = "unknown",
    cache_age_seconds: Optional[int] = None,
    show_refresh_hint: bool = True
) -> None:
    """Render a unified status bar showing data freshness and source

    Args:
        timestamp: When the data was last updated
        source: Data source ('live', 'cache', 'fallback')
        cache_age_seconds: Age of cached data in seconds
        show_refresh_hint: Whether to show hint about refreshing
    """
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        # Source indicator
        if source == 'live':
            st.success("🟢 Live Data")
        elif source == 'cache':
            st.info("🔵 Cached Data")
        elif source == 'fallback':
            st.warning("🟡 Fallback Data")
        else:
            st.info(f"📊 Source: {source}")

    with col2:
        # Data age indicator
        if timestamp:
            age_seconds = (datetime.now() - timestamp).total_seconds()
            if age_seconds < 60:
                st.success(f"⏱️ {int(age_seconds)}s old")
            elif age_seconds < 300:  # 5 minutes
                st.info(f"⏱️ {int(age_seconds/60)}m old")
            elif age_seconds < 3600:  # 1 hour
                st.warning(f"⏱️ {int(age_seconds/60)}m old")
            else:
                st.error(f"⏱️ {int(age_seconds/3600)}h old")
        elif cache_age_seconds is not None:
            st.info(f"⏱️ Cache: {int(cache_age_seconds)}s")

    with col3:
        if show_refresh_hint and timestamp:
            age_seconds = (datetime.now() - timestamp).total_seconds()
            if age_seconds > 300:  # > 5 minutes
                st.caption("🔄 Consider refreshing")


def render_collapsible_section(
    title: str,
    content_func: callable,
    icon: str = "📊",
    expanded: bool = False,
    help_text: Optional[str] = None
) -> None:
    """Render a collapsible section with consistent styling

    Args:
        title: Section title
        content_func: Function to call to render the content
        icon: Emoji icon
        expanded: Whether to start expanded
        help_text: Optional help text
    """
    with st.expander(f"{icon} {title}", expanded=expanded):
        if help_text:
            st.caption(help_text)
        content_func()


def render_analysis_result(
    result: Dict[str, Any],
    title: str = "Analysis Results",
    show_raw_data: bool = True
) -> None:
    """Render pattern analysis results with consistent formatting

    Args:
        result: Analysis result dictionary
        title: Title for the results section
        show_raw_data: Whether to show raw JSON data in expander
    """
    if not result:
        st.warning("⚠️ No results available")
        return

    # Success indicator
    if 'error' in result:
        st.error(f"❌ Error: {result['error']}")
        return

    st.success(f"✅ {title} Complete")

    # Display formatted response (priority: formatted_response > output > response)
    if 'formatted_response' in result:
        st.markdown(result['formatted_response'])
    elif 'output' in result:
        st.markdown(result['output'])
    elif 'response' in result:
        st.markdown(result['response'])

    # Display structured data sections
    if 'data' in result:
        data = result['data']

        # Common data fields with nice formatting
        if 'valuation' in data:
            st.markdown("### 💰 Valuation")
            st.markdown(data['valuation'])

        if 'quality_metrics' in data:
            st.markdown("### ⭐ Quality Metrics")
            st.markdown(data['quality_metrics'])

        if 'risks' in data:
            st.markdown("### ⚠️ Risks")
            st.markdown(data['risks'])

        if 'recommendation' in data:
            st.markdown("### 🎯 Recommendation")
            st.markdown(data['recommendation'])

        # Checklist items
        if 'checklist_items' in data:
            st.markdown("### 📋 Checklist")
            for item in data['checklist_items']:
                status = "✅" if item.get('passed') else "❌"
                st.markdown(f"{status} **{item.get('criterion')}**: {item.get('assessment')}")

    # Display confidence if available
    if 'confidence' in result:
        confidence = result['confidence']
        color = "green" if confidence > 0.8 else "orange" if confidence > 0.6 else "red"
        st.markdown(f"**Confidence:** :{color}[{confidence:.1%}]")

    # Show raw data in expander
    if show_raw_data:
        with st.expander("📊 View Raw Analysis Data"):
            st.json(result)


def render_step_results(results: List[Dict[str, Any]], title: str = "Analysis Steps") -> None:
    """Render step-by-step results with consistent formatting

    Args:
        results: List of step results
        title: Title for the steps section
    """
    st.markdown(f"### {title}")

    for i, step_result in enumerate(results):
        action = step_result.get('action', 'Unknown')

        # Determine if step had errors
        has_error = 'error' in step_result
        icon = "❌" if has_error else "✅"

        # Expand last step or error steps by default
        should_expand = (i == len(results) - 1) or has_error

        with st.expander(f"{icon} Step {i+1}: {action}", expanded=should_expand):
            if has_error:
                st.error(f"Error: {step_result['error']}")

            if 'result' in step_result:
                result_data = step_result['result']
                if isinstance(result_data, dict):
                    # Pretty display for dicts
                    for key, value in result_data.items():
                        if key.startswith('_'):  # Skip private keys
                            continue
                        st.write(f"**{key}**: {value}")
                else:
                    st.write(result_data)


def render_quote_card_enhanced(
    symbol: str,
    name: str,
    icon: str,
    data: Dict[str, Any]
) -> None:
    """Render enhanced quote card with multiple timeframe changes

    Args:
        symbol: Stock/ETF symbol
        name: Display name
        icon: Emoji icon
        data: Quote data with price, changes, etc.
    """
    if not data or 'error' in data:
        st.info(f"{icon} {name}\n\nNo data available")
        return

    with st.container():
        # Header
        st.markdown(f"{icon} **{name}**")
        st.caption(symbol)

        # Price
        price = data.get('price', 0)
        st.markdown(f"<h3 style='margin:0;'>${price:.2f}</h3>", unsafe_allow_html=True)

        # Changes (daily, MTD, YTD)
        daily_change = data.get('changesPercentage', 0)
        daily_color = "green" if daily_change >= 0 else "red"
        daily_sign = "+" if daily_change >= 0 else ""
        st.markdown(
            f"<p style='color:{daily_color}; margin:0; font-size:14px;'>{daily_sign}{daily_change:.2f}% Daily</p>",
            unsafe_allow_html=True
        )

        # Additional changes if available
        if 'mtdChange' in data:
            mtd = data['mtdChange']
            mtd_color = "green" if mtd >= 0 else "red"
            mtd_sign = "+" if mtd >= 0 else ""
            st.caption(f":{mtd_color}[{mtd_sign}{mtd:.2f}% MTD]")

        if 'ytdChange' in data:
            ytd = data['ytdChange']
            ytd_color = "green" if ytd >= 0 else "red"
            ytd_sign = "+" if ytd >= 0 else ""
            st.caption(f":{ytd_color}[{ytd_sign}{ytd:.2f}% YTD]")


def render_movers_table_enhanced(movers: List[Dict[str, Any]], show_count: int = 10) -> None:
    """Render enhanced movers table with better formatting

    Args:
        movers: List of mover data dictionaries
        show_count: Number of movers to display
    """
    if not movers:
        st.info("No movers data available")
        return

    # Convert to DataFrame for better display
    df_data = []
    for mover in movers[:show_count]:
        # Handle price - might already be a string or float
        price = mover.get('price', 0)
        if isinstance(price, str):
            price_str = price if price.startswith('$') else f"${price}"
        else:
            price_str = f"${float(price):.2f}"

        # Handle change percentage
        change_pct = mover.get('changesPercentage', 0)
        if isinstance(change_pct, str):
            change_str = change_pct if '%' in change_pct else f"{change_pct}%"
        else:
            change_str = f"{float(change_pct):.2f}%"

        # Handle volume
        volume = mover.get('volume', 0)
        if isinstance(volume, str):
            volume_str = volume
        else:
            volume_str = f"{int(volume):,.0f}"

        df_data.append({
            'Symbol': mover.get('symbol', 'N/A'),
            'Name': mover.get('name', 'N/A')[:30],  # Truncate long names
            'Price': price_str,
            'Change %': change_str,
            'Volume': volume_str
        })

    df = pd.DataFrame(df_data)

    # Style the dataframe
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        height=min(len(df) * 35 + 40, 400)  # Dynamic height with max
    )


def render_section_header(
    title: str,
    icon: str = "📊",
    subtitle: Optional[str] = None,
    divider: bool = True
) -> None:
    """Render a consistent section header

    Args:
        title: Section title
        icon: Emoji icon
        subtitle: Optional subtitle/description
        divider: Whether to add a divider below
    """
    st.markdown(f"### {icon} {title}")
    if subtitle:
        st.caption(subtitle)
    if divider:
        st.markdown("---")


def render_action_buttons(
    buttons: List[Dict[str, Any]],
    columns: int = 3,
    use_full_width: bool = True
) -> Optional[str]:
    """Render a row of action buttons with consistent styling

    Args:
        buttons: List of button configs with 'label', 'key', 'icon', 'type', 'callback'
        columns: Number of columns for button layout
        use_full_width: Whether buttons should use full container width

    Returns:
        Key of clicked button, or None
    """
    cols = st.columns(columns)
    clicked = None

    for i, btn_config in enumerate(buttons):
        with cols[i % columns]:
            label = f"{btn_config.get('icon', '📊')} {btn_config['label']}"
            button_type = btn_config.get('type', 'secondary')

            if st.button(
                label,
                key=btn_config['key'],
                type=button_type,
                width="stretch" if use_full_width else None
            ):
                clicked = btn_config['key']
                if 'callback' in btn_config:
                    btn_config['callback']()

    return clicked


def render_time_range_selector(
    key: str = "time_range",
    default_index: int = 2
) -> str:
    """Render a consistent time range selector

    Args:
        key: Unique key for the selector
        default_index: Default selected index

    Returns:
        Selected time range string
    """
    return st.selectbox(
        "Time Range",
        ["1M", "3M", "6M", "1Y", "5Y"],
        index=default_index,
        key=key
    )


def render_info_box(
    message: str,
    box_type: str = "info",
    icon: Optional[str] = None
) -> None:
    """Render a styled info/warning/success/error box

    Args:
        message: Message to display
        box_type: Type of box ('info', 'success', 'warning', 'error')
        icon: Optional custom icon (overrides default)
    """
    icons = {
        'info': '💡',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
    }

    display_icon = icon or icons.get(box_type, '📊')

    if box_type == 'info':
        st.info(f"{display_icon} {message}")
    elif box_type == 'success':
        st.success(f"{display_icon} {message}")
    elif box_type == 'warning':
        st.warning(f"{display_icon} {message}")
    elif box_type == 'error':
        st.error(f"{display_icon} {message}")
    else:
        st.info(f"{display_icon} {message}")


def render_loading_placeholder(message: str = "Loading data...") -> None:
    """Render a consistent loading placeholder

    Args:
        message: Loading message to display
    """
    with st.spinner(message):
        st.info(f"⏳ {message}")


def render_grid_layout(items: List[Dict[str, Any]], columns: int = 4) -> None:
    """Render items in a grid layout with consistent spacing

    Args:
        items: List of items with 'render_func' callable
        columns: Number of columns in grid
    """
    cols = st.columns(columns)

    for i, item in enumerate(items):
        with cols[i % columns]:
            if 'render_func' in item:
                item['render_func']()
            else:
                st.write(item)
