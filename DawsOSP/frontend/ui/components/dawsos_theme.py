"""
DawsOS Dark Theme

Purpose: Professional dark theme for portfolio intelligence UI
Updated: 2025-10-21
Priority: P1 (Critical for UI consistency)

Color Palette (HSL):
    - Background: hsl(210, 15%, 12%) - Deep graphite
    - Surface: hsl(210, 12%, 16%) - Elevated slate
    - Border: hsl(210, 10%, 25%) - Subtle borders
    - Text Primary: hsl(210, 15%, 95%) - High contrast
    - Text Secondary: hsl(210, 10%, 70%) - Muted
    - Signal Teal: hsl(185, 100%, 50%) - #00d9ff - Accent
    - Success: hsl(140, 60%, 50%) - Green
    - Warning: hsl(35, 100%, 55%) - Amber
    - Error: hsl(0, 85%, 58%) - Red

Typography:
    - Headings: Inter, -apple-system, BlinkMacSystemFont
    - Body: system-ui, -apple-system, sans-serif
    - Monospace: 'SF Mono', 'Fira Code', Consolas

Usage:
    from ui.components.dawsos_theme import apply_theme
    apply_theme()
"""

import streamlit as st


def apply_theme():
    """
    Apply DawsOS dark theme to Streamlit app.

    Injects custom CSS with professional dark color scheme.
    """
    st.markdown(
        """
        <style>
        /* ========================================================================
           DawsOS Dark Theme - Root Variables
           ======================================================================== */

        :root {
            /* Colors */
            --bg-primary: hsl(210, 15%, 12%);
            --bg-secondary: hsl(210, 12%, 16%);
            --bg-tertiary: hsl(210, 10%, 20%);
            --border-color: hsl(210, 10%, 25%);
            --text-primary: hsl(210, 15%, 95%);
            --text-secondary: hsl(210, 10%, 70%);
            --text-muted: hsl(210, 8%, 50%);

            /* Brand Colors */
            --signal-teal: hsl(185, 100%, 50%);
            --signal-teal-dim: hsl(185, 80%, 40%);
            --success: hsl(140, 60%, 50%);
            --warning: hsl(35, 100%, 55%);
            --error: hsl(0, 85%, 58%);

            /* Spacing */
            --spacing-xs: 4px;
            --spacing-sm: 8px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;

            /* Typography */
            --font-heading: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            --font-body: system-ui, -apple-system, sans-serif;
            --font-mono: 'SF Mono', 'Fira Code', Consolas, monospace;

            /* Border Radius */
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
        }

        /* ========================================================================
           Global Overrides
           ======================================================================== */

        .stApp {
            background: linear-gradient(135deg, hsl(210, 20%, 10%) 0%, hsl(210, 15%, 12%) 100%);
            color: var(--text-primary);
            font-family: var(--font-body);
        }

        /* Main content area */
        .main .block-container {
            padding-top: 0;
            padding-bottom: var(--spacing-xl);
            max-width: 1600px;
        }

        /* Premium Banner */
        .premium-banner {
            position: relative;
            background: linear-gradient(135deg,
                hsl(210, 25%, 8%) 0%,
                hsl(210, 20%, 12%) 50%,
                hsl(210, 25%, 8%) 100%);
            border-bottom: 1px solid hsl(185, 100%, 50%, 0.15);
            padding: var(--spacing-lg) var(--spacing-xl);
            margin: calc(-1 * var(--spacing-xl)) calc(-1 * var(--spacing-xl)) var(--spacing-xl);
            box-shadow:
                0 4px 24px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.02);
            overflow: hidden;
        }

        .premium-banner::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg,
                transparent 0%,
                hsl(185, 100%, 50%, 0.3) 50%,
                transparent 100%);
        }

        .premium-banner::after {
            content: '';
            position: absolute;
            top: 0;
            right: -20%;
            width: 40%;
            height: 100%;
            background: radial-gradient(ellipse at center,
                hsl(185, 100%, 50%, 0.03) 0%,
                transparent 70%);
            pointer-events: none;
        }

        .banner-title {
            font-size: 2.75rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg,
                hsl(210, 20%, 98%) 0%,
                hsl(185, 100%, 85%) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            padding: 0;
            line-height: 1.2;
            text-shadow: 0 2px 8px rgba(0, 217, 255, 0.1);
        }

        .banner-subtitle {
            font-size: 1.125rem;
            color: hsl(210, 12%, 65%);
            font-weight: 400;
            letter-spacing: 0.025em;
            margin-top: var(--spacing-sm);
            margin-bottom: 0;
        }

        .banner-meta {
            display: flex;
            gap: var(--spacing-lg);
            margin-top: var(--spacing-md);
            flex-wrap: wrap;
        }

        .banner-meta-item {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-xs);
        }

        .banner-meta-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: hsl(210, 10%, 55%);
            font-weight: 600;
        }

        .banner-meta-value {
            font-size: 1.5rem;
            font-weight: 700;
            font-family: var(--font-mono);
            color: var(--text-primary);
            letter-spacing: -0.01em;
        }

        .banner-meta-value.positive {
            color: hsl(140, 60%, 60%);
        }

        .banner-meta-value.negative {
            color: hsl(0, 85%, 65%);
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary);
            font-family: var(--font-heading);
            font-weight: 600;
        }

        h1 {
            font-size: 2.5rem;
            margin-bottom: var(--spacing-lg);
            border-bottom: 2px solid var(--signal-teal);
            padding-bottom: var(--spacing-sm);
        }

        h2 {
            font-size: 2rem;
            margin-top: var(--spacing-xl);
            margin-bottom: var(--spacing-md);
        }

        h3 {
            font-size: 1.5rem;
            margin-top: var(--spacing-lg);
            margin-bottom: var(--spacing-sm);
            color: var(--signal-teal);
        }

        /* Paragraphs and text */
        p, .stMarkdown {
            color: var(--text-secondary);
            line-height: 1.6;
        }

        /* Links */
        a {
            color: var(--signal-teal);
            text-decoration: none;
            transition: color 0.2s ease;
        }

        a:hover {
            color: var(--signal-teal-dim);
        }

        /* ========================================================================
           Cards and Panels
           ======================================================================== */

        .stContainer, .element-container {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: var(--spacing-md);
            margin-bottom: var(--spacing-md);
        }

        /* Metric Cards */
        .stMetric {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: var(--spacing-md);
        }

        .stMetric label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stMetric div[data-testid="stMetricValue"] {
            color: var(--text-primary);
            font-size: 2rem;
            font-weight: 700;
            font-family: var(--font-mono);
        }

        .stMetric div[data-testid="stMetricDelta"] {
            font-size: 0.875rem;
            font-weight: 600;
        }

        /* ========================================================================
           Charts
           ======================================================================== */

        /* Plotly charts */
        .js-plotly-plot {
            background-color: var(--bg-secondary) !important;
            border-radius: var(--radius-md);
        }

        .plotly .main-svg {
            background-color: transparent !important;
        }

        /* ========================================================================
           Buttons
           ======================================================================== */

        .stButton > button {
            background-color: var(--signal-teal);
            color: var(--bg-primary);
            border: none;
            border-radius: var(--radius-sm);
            padding: var(--spacing-sm) var(--spacing-md);
            font-weight: 600;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .stButton > button:hover {
            background-color: var(--signal-teal-dim);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 217, 255, 0.3);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Secondary button */
        .stButton.secondary > button {
            background-color: transparent;
            color: var(--signal-teal);
            border: 1px solid var(--signal-teal);
        }

        .stButton.secondary > button:hover {
            background-color: rgba(0, 217, 255, 0.1);
        }

        /* ========================================================================
           Inputs
           ======================================================================== */

        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stNumberInput > div > div > input {
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: var(--spacing-sm);
        }

        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stNumberInput > div > div > input:focus {
            border-color: var(--signal-teal);
            box-shadow: 0 0 0 2px rgba(0, 217, 255, 0.2);
        }

        /* ========================================================================
           Tables
           ======================================================================== */

        .stTable, .stDataFrame {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
        }

        .stTable thead th,
        .stDataFrame thead th {
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
            padding: var(--spacing-sm) var(--spacing-md);
            border-bottom: 2px solid var(--border-color);
        }

        .stTable tbody td,
        .stDataFrame tbody td {
            color: var(--text-secondary);
            padding: var(--spacing-sm) var(--spacing-md);
            border-bottom: 1px solid var(--border-color);
        }

        .stTable tbody tr:hover,
        .stDataFrame tbody tr:hover {
            background-color: var(--bg-tertiary);
        }

        /* ========================================================================
           Sidebar
           ======================================================================== */

        .css-1d391kg, [data-testid="stSidebar"] {
            background-color: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
        }

        .css-1d391kg .stMarkdown,
        [data-testid="stSidebar"] .stMarkdown {
            color: var(--text-secondary);
        }

        /* ========================================================================
           Provenance Chips
           ======================================================================== */

        .provenance-chip {
            display: inline-block;
            background-color: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: 2px 8px;
            font-size: 0.75rem;
            font-family: var(--font-mono);
            color: var(--text-muted);
            margin-left: var(--spacing-xs);
        }

        /* Staleness indicators */
        .staleness-fresh {
            border-color: var(--success);
            color: var(--success);
        }

        .staleness-stale {
            border-color: var(--warning);
            color: var(--warning);
        }

        .staleness-very-stale {
            border-color: var(--error);
            color: var(--error);
        }

        /* ========================================================================
           Explain Drawer
           ======================================================================== */

        .explain-drawer {
            position: fixed;
            right: 0;
            top: 0;
            height: 100vh;
            width: 400px;
            background-color: var(--bg-secondary);
            border-left: 1px solid var(--border-color);
            padding: var(--spacing-lg);
            overflow-y: auto;
            box-shadow: -4px 0 12px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        }

        .explain-drawer.open {
            transform: translateX(0);
        }

        .explain-drawer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-lg);
            padding-bottom: var(--spacing-sm);
            border-bottom: 1px solid var(--border-color);
        }

        .explain-drawer-title {
            color: var(--text-primary);
            font-size: 1.25rem;
            font-weight: 600;
        }

        .explain-drawer-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
        }

        .trace-step {
            background-color: var(--bg-tertiary);
            border-left: 3px solid var(--signal-teal);
            border-radius: var(--radius-sm);
            padding: var(--spacing-sm);
            margin-bottom: var(--spacing-sm);
        }

        .trace-step-name {
            color: var(--text-primary);
            font-weight: 600;
            font-size: 0.875rem;
        }

        .trace-step-duration {
            color: var(--text-muted);
            font-size: 0.75rem;
            font-family: var(--font-mono);
        }

        /* ========================================================================
           Utility Classes
           ======================================================================== */

        .text-success {
            color: var(--success) !important;
        }

        .text-warning {
            color: var(--warning) !important;
        }

        .text-error {
            color: var(--error) !important;
        }

        .text-muted {
            color: var(--text-muted) !important;
        }

        .text-mono {
            font-family: var(--font-mono) !important;
        }

        /* ========================================================================
           Scrollbars
           ======================================================================== */

        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background-color: var(--bg-primary);
        }

        ::-webkit-scrollbar-thumb {
            background-color: var(--border-color);
            border-radius: var(--radius-sm);
        }

        ::-webkit-scrollbar-thumb:hover {
            background-color: var(--signal-teal);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, delta: str = None, provenance: str = None, staleness: str = "fresh"):
    """
    Render a styled metric card.

    Args:
        label: Metric label
        value: Metric value
        delta: Change indicator (optional)
        provenance: Provenance metadata (optional)
        staleness: "fresh", "stale", or "very-stale"
    """
    staleness_class = f"staleness-{staleness.replace('_', '-')}"

    html = f"""
    <div class="stMetric">
        <label>{label}</label>
        <div data-testid="stMetricValue">{value}</div>
    """

    if delta:
        html += f'<div data-testid="stMetricDelta">{delta}</div>'

    if provenance:
        html += f'<span class="provenance-chip {staleness_class}">{provenance}</span>'

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


def trace_step(name: str, duration_ms: float, sources: list = None):
    """
    Render a trace step in explain drawer.

    Args:
        name: Step name
        duration_ms: Duration in milliseconds
        sources: List of data sources
    """
    sources_html = ""
    if sources:
        sources_html = "<br>".join([f"<span class='text-muted'>• {s}</span>" for s in sources])

    html = f"""
    <div class="trace-step">
        <div class="trace-step-name">{name}</div>
        <div class="trace-step-duration">{duration_ms:.1f}ms</div>
        {sources_html}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def premium_banner(title: str, subtitle: str = None, meta_items: list = None):
    """
    Render premium banner with title and optional metadata.

    Args:
        title: Main title text
        subtitle: Subtitle text (optional)
        meta_items: List of (label, value, positive/negative/neutral) tuples
    """
    subtitle_html = f'<p class="banner-subtitle">{subtitle}</p>' if subtitle else ''

    meta_html = ''
    if meta_items:
        meta_items_html = []
        for item in meta_items:
            label = item[0]
            value = item[1]
            value_class = f' {item[2]}' if len(item) > 2 and item[2] in ['positive', 'negative'] else ''
            meta_items_html.append(f"""
                <div class="banner-meta-item">
                    <div class="banner-meta-label">{label}</div>
                    <div class="banner-meta-value{value_class}">{value}</div>
                </div>
            """)
        meta_html = f'<div class="banner-meta">{"".join(meta_items_html)}</div>'

    html = f"""
    <div class="premium-banner">
        <h1 class="banner-title">{title}</h1>
        {subtitle_html}
        {meta_html}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
