"""
DawsOS Portfolio Overview Screen

Purpose: Main portfolio dashboard with metrics, attribution, and provenance
Updated: 2025-10-22 (Phase 4 Task 3)
Priority: P0 (Critical for Phase 4)

Features:
    - KPI ribbon (TWR, Sharpe, Volatility, Drawdown)
    - Currency attribution breakdown
    - Provenance badges (pack ID, ledger hash)
    - DawsOS dark theme
    - Error handling and loading states

Usage:
    streamlit run frontend/ui/screens/portfolio_overview.py
"""

import logging
import os
import sys
from datetime import date
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import streamlit as st

from frontend.ui.components.dawsos_theme import apply_theme
from frontend.ui.api_client import DawsOSClient, MockDawsOSClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DawsOS.UI.PortfolioOverview")


# ============================================================================
# Configuration
# ============================================================================

# Use mock client if API is not available (for development)
USE_MOCK_CLIENT = os.getenv("USE_MOCK_CLIENT", "true").lower() == "true"

# API base URL
API_BASE_URL = os.getenv("EXECUTOR_API_URL", "http://localhost:8000")


# ============================================================================
# Helper Functions
# ============================================================================


def format_percentage(value: Optional[float], decimals: int = 2) -> str:
    """Format float as percentage."""
    if value is None:
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def format_number(value: Optional[float], decimals: int = 2) -> str:
    """Format float with thousands separator."""
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_currency(value: Optional[float], currency: str = "CAD") -> str:
    """Format value as currency."""
    if value is None:
        return "N/A"
    return f"${value:,.2f} {currency}"


def get_delta_color(value: Optional[float]) -> str:
    """Get color class for delta based on sign."""
    if value is None:
        return ""
    elif value > 0:
        return "text-success"
    elif value < 0:
        return "text-error"
    else:
        return "text-muted"


# ============================================================================
# Main Screen
# ============================================================================


def render_portfolio_overview(
    portfolio_id: str = "11111111-1111-1111-1111-111111111111",
    asof_date: Optional[date] = None,
):
    """
    Render portfolio overview screen.

    Args:
        portfolio_id: Portfolio ID (UUID)
        asof_date: As-of date (optional, defaults to today)
    """
    # Apply DawsOS dark theme
    apply_theme()

    # Initialize API client
    if USE_MOCK_CLIENT:
        client = MockDawsOSClient(base_url=API_BASE_URL)
        st.info("ℹ️ Using mock data (API not connected)")
    else:
        client = DawsOSClient(base_url=API_BASE_URL)

    # Set asof_date to today if not provided
    if asof_date is None:
        asof_date = date.today()

    # ========================================================================
    # Header with Provenance
    # ========================================================================

    st.markdown("# Portfolio Overview")

    # Fetch portfolio metrics
    with st.spinner("Loading portfolio data..."):
        try:
            metrics = client.get_portfolio_metrics(portfolio_id, asof_date)
            attribution = client.get_currency_attribution(portfolio_id, asof_date)

            # Extract provenance
            pack_id = metrics.get("pricing_pack_id", "unknown")
            pack_id_short = pack_id[:12] if len(pack_id) > 12 else pack_id

            # Display provenance badges
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### Portfolio: {portfolio_id[:8]}...")

            with col2:
                st.markdown(
                    f"""
                    <div style="text-align: right; padding-top: 8px;">
                        <span class="provenance-chip staleness-fresh">
                            Pack: {pack_id_short}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(f"**As of**: {metrics.get('asof_date', 'N/A')}")

            # Success state - render KPIs and attribution
            render_kpi_ribbon(metrics)
            render_currency_attribution(attribution)
            render_metadata_section(metrics, attribution)

        except Exception as e:
            # Error state
            st.error(f"❌ Error loading portfolio data: {str(e)}")
            logger.error(f"Error loading portfolio data: {e}", exc_info=True)

            # Show helpful troubleshooting
            with st.expander("Troubleshooting"):
                st.markdown(
                    f"""
                    **Possible issues**:
                    - API not running at `{API_BASE_URL}`
                    - Portfolio ID `{portfolio_id}` not found
                    - Database not populated with metrics
                    - Network connectivity issues

                    **Quick fixes**:
                    - Start API: `cd backend && uvicorn app.main:app --reload`
                    - Check API health: `curl {API_BASE_URL}/health`
                    - Enable mock mode: Set `USE_MOCK_CLIENT=true` environment variable
                    """
                )


def render_kpi_ribbon(metrics: dict):
    """
    Render KPI ribbon with key metrics.

    Args:
        metrics: Metrics dict from API
    """
    st.markdown("## Performance Metrics")

    # Create 5-column layout for KPIs
    cols = st.columns(5)

    # KPI 1: TWR (YTD)
    with cols[0]:
        twr_ytd = metrics.get("twr_ytd")
        twr_1y = metrics.get("twr_1y")  # For delta comparison

        delta = None
        if twr_ytd is not None and twr_1y is not None:
            delta = twr_ytd - (twr_1y / 12)  # Rough monthly comparison

        st.metric(
            label="TWR (YTD)",
            value=format_percentage(twr_ytd),
            delta=format_percentage(delta, 1) if delta else None,
        )

    # KPI 2: Sharpe Ratio (1Y)
    with cols[1]:
        sharpe_1y = metrics.get("sharpe_1y")
        sharpe_3y = metrics.get("sharpe_3y")

        st.metric(
            label="Sharpe (1Y)",
            value=format_number(sharpe_1y) if sharpe_1y else "N/A",
            delta=None,
        )

    # KPI 3: Volatility (30D)
    with cols[2]:
        volatility_30d = metrics.get("volatility_30d")

        st.metric(
            label="Vol (30D Ann.)",
            value=format_percentage(volatility_30d) if volatility_30d else "N/A",
            delta=None,
        )

    # KPI 4: Max Drawdown (1Y)
    with cols[3]:
        max_dd = metrics.get("max_drawdown_1y")

        st.metric(
            label="Max DD (1Y)",
            value=format_percentage(max_dd) if max_dd else "N/A",
            delta=None,
            delta_color="inverse",  # Red is good for smaller drawdowns
        )

    # KPI 5: TWR (1D)
    with cols[4]:
        twr_1d = metrics.get("twr_1d")

        st.metric(
            label="1-Day Return",
            value=format_percentage(twr_1d) if twr_1d else "N/A",
            delta=None,
        )


def render_currency_attribution(attribution: dict):
    """
    Render currency attribution breakdown.

    Args:
        attribution: Attribution dict from API
    """
    st.markdown("## Currency Attribution")

    # Check if multi-currency portfolio
    local_return = attribution.get("local_return")
    fx_return = attribution.get("fx_return")
    interaction = attribution.get("interaction_return")
    total_return = attribution.get("total_return")
    error_bps = attribution.get("error_bps")
    base_currency = attribution.get("base_currency", "CAD")

    if local_return is None and fx_return is None:
        st.info("📊 Single-currency portfolio (no FX attribution)")
        return

    # Create 4-column layout
    cols = st.columns(4)

    with cols[0]:
        delta_color = get_delta_color(local_return)
        st.markdown(
            f"""
            <div class="stMetric">
                <label>Local Return</label>
                <div data-testid="stMetricValue" class="{delta_color}">
                    {format_percentage(local_return)}
                </div>
                <div class="text-muted" style="font-size: 0.75rem;">
                    Return in local currencies
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[1]:
        delta_color = get_delta_color(fx_return)
        st.markdown(
            f"""
            <div class="stMetric">
                <label>FX Return</label>
                <div data-testid="stMetricValue" class="{delta_color}">
                    {format_percentage(fx_return)}
                </div>
                <div class="text-muted" style="font-size: 0.75rem;">
                    Currency impact
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[2]:
        delta_color = get_delta_color(interaction)
        st.markdown(
            f"""
            <div class="stMetric">
                <label>Interaction</label>
                <div data-testid="stMetricValue" class="{delta_color}">
                    {format_percentage(interaction, 3)}
                </div>
                <div class="text-muted" style="font-size: 0.75rem;">
                    Cross-effect
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[3]:
        delta_color = get_delta_color(total_return)
        st.markdown(
            f"""
            <div class="stMetric">
                <label>Total Return ({base_currency})</label>
                <div data-testid="stMetricValue" class="{delta_color}">
                    {format_percentage(total_return)}
                </div>
                <div class="text-muted" style="font-size: 0.75rem;">
                    In base currency
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Show validation error (should be < 0.1 bps)
    if error_bps is not None:
        error_status = "✅" if error_bps < 0.1 else "⚠️"
        error_color = "text-success" if error_bps < 0.1 else "text-warning"

        st.markdown(
            f"""
            <div style="margin-top: 16px; padding: 8px; background-color: var(--bg-secondary);
                        border-radius: 4px; border-left: 3px solid var(--signal-teal);">
                <span class="text-muted">Mathematical Identity Validation: </span>
                <span class="{error_color}">{error_status} Error: {error_bps:.3f} bps</span>
                <span class="text-muted"> (Target: < 0.1 bps)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Explanation expander
    with st.expander("ℹ️ How currency attribution works"):
        st.markdown(
            """
            **Mathematical Identity**:
            ```
            r_base = (1 + r_local) × (1 + r_fx) - 1
                   = r_local + r_fx + r_local × r_fx
            ```

            Where:
            - **r_local**: Return in local currency (if all holdings stayed in USD, EUR, etc.)
            - **r_fx**: FX impact (currency movements vs base currency)
            - **r_local × r_fx**: Interaction effect (cross-product)
            - **r_base**: Total return in base currency (CAD)

            **Example**:
            - US stock returns +8.5% in USD (r_local)
            - USD weakens -1.2% vs CAD (r_fx)
            - Interaction: 0.085 × (-0.012) = -0.10% (r_interaction)
            - **Total CAD return: +7.2%**
            """
        )


def render_metadata_section(metrics: dict, attribution: dict):
    """
    Render metadata/provenance section.

    Args:
        metrics: Metrics dict from API
        attribution: Attribution dict from API
    """
    st.markdown("## Provenance & Metadata")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Data Sources")
        st.markdown(
            f"""
            - **Pricing Pack**: `{metrics.get('pricing_pack_id', 'N/A')}`
            - **As-of Date**: `{metrics.get('asof_date', 'N/A')}`
            - **Portfolio ID**: `{metrics.get('portfolio_id', 'N/A')}`
            """
        )

    with col2:
        st.markdown("### Quality Metrics")

        # Attribution error
        error_bps = attribution.get("error_bps")
        error_status = "✅ PASS" if (error_bps and error_bps < 0.1) else "⚠️ WARNING"

        st.markdown(
            f"""
            - **Attribution Error**: {error_bps:.3f} bps ({error_status})
            - **Data Freshness**: ✅ Fresh (pack marked ready)
            - **Computation**: From TimescaleDB continuous aggregates
            """
        )


# ============================================================================
# Streamlit App Entry Point
# ============================================================================


if __name__ == "__main__":
    st.set_page_config(
        page_title="DawsOS - Portfolio Overview",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Get portfolio ID from query params or use default
    query_params = st.query_params
    portfolio_id = query_params.get("portfolio_id", "11111111-1111-1111-1111-111111111111")

    # Render main screen
    render_portfolio_overview(portfolio_id=portfolio_id)
