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
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-body);
        }

        /* Main content area */
        .main .block-container {
            padding-top: var(--spacing-xl);
            padding-bottom: var(--spacing-xl);
            max-width: 1400px;
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
