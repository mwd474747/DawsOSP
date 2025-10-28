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
from frontend.ui.client_factory import get_client, is_mock_mode, get_api_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DawsOS.UI.PortfolioOverview")


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
    client = get_client()

    if is_mock_mode():
        st.info("ℹ️ Using mock data (API not connected)")

    # Set asof_date to today if not provided
    if asof_date is None:
        asof_date = date.today()

    # ========================================================================
    # Execute portfolio_overview pattern via Executor API
    # ========================================================================

    with st.spinner("Loading portfolio data..."):
        try:
            # Call Executor API with portfolio_overview pattern
            result = client.execute(
                pattern_id="portfolio_overview",
                inputs={
                    "portfolio_id": portfolio_id,
                    "lookback_days": 252,  # 1 year of trading days
                },
                portfolio_id=portfolio_id,
                asof_date=asof_date,
                require_fresh=True,
            )

            # Extract data from pattern result
            metrics = result.get("data", {}).get("perf_metrics", {})
            attribution = result.get("data", {}).get("currency_attr", {})
            holdings = result.get("data", {}).get("valued_positions", [])

            # Extract provenance from metadata
            metadata = result.get("metadata", {})
            pack_id = metadata.get("pricing_pack_id", "unknown")
            ledger_hash = metadata.get("ledger_commit_hash", "unknown")

            # Page header
            st.markdown("## Portfolio Overview")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Portfolio", f"{portfolio_id[:8]}...")
            with col2:
                st.metric("Pricing Pack", f"{pack_id[:12]}...")
            with col3:
                st.metric("As of", asof_date.isoformat())

            # Success state - render KPIs and attribution
            render_kpi_ribbon(metrics)
            render_currency_attribution(attribution)

            # Render holdings table and charts (already fetched from pattern)
            render_holdings_table(holdings)
            render_allocation_charts(holdings)
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
                    - API not running at `{get_api_url()}`
                    - Portfolio ID `{portfolio_id}` not found
                    - Database not populated with metrics
                    - Network connectivity issues

                    **Quick fixes**:
                    - Start API: `./backend/run_api.sh` (or `uvicorn backend.app.api.executor:app --reload`)
                    - Check API health: `curl {get_api_url()}/health`
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


def render_holdings_table(holdings: list):
    """
    Render holdings table with rating badges.

    Args:
        holdings: List of holding dicts
    """
    st.markdown("## Holdings")

    if not holdings:
        st.info("No holdings found in this portfolio")
        return

    # Convert holdings to DataFrame for table display
    import pandas as pd

    df = pd.DataFrame(holdings)

    # Format columns
    if not df.empty:
        # Reorder and select columns for display
        display_cols = [
            "symbol",
            "name",
            "shares",
            "market_value",
            "unrealized_pl",
            "unrealized_pl_pct",
            "weight",
            "div_safety",
            "moat",
            "resilience",
        ]

        # Filter to only existing columns
        display_cols = [col for col in display_cols if col in df.columns]
        df_display = df[display_cols].copy()

        # Format numeric columns
        if "shares" in df_display.columns:
            df_display["shares"] = df_display["shares"].apply(lambda x: f"{x:,.0f}")

        if "market_value" in df_display.columns:
            df_display["market_value"] = df_display["market_value"].apply(
                lambda x: f"${x:,.2f}"
            )

        if "unrealized_pl" in df_display.columns:
            df_display["unrealized_pl"] = df_display["unrealized_pl"].apply(
                lambda x: f"${x:,.2f}"
            )

        if "unrealized_pl_pct" in df_display.columns:
            df_display["unrealized_pl_pct"] = df_display["unrealized_pl_pct"].apply(
                lambda x: f"{x*100:.2f}%"
            )

        if "weight" in df_display.columns:
            df_display["weight"] = df_display["weight"].apply(lambda x: f"{x*100:.1f}%")

        # Rename columns for display
        df_display.columns = [
            col.replace("_", " ").title() for col in df_display.columns
        ]

        # Display table
        st.dataframe(
            df_display,
            use_container_width=True,
            height=min(400, len(df_display) * 35 + 38),
        )

        # Add explanation
        st.markdown("""
        **Rating Badges**:
        - **Div Safety**: Dividend safety score (0-10) - higher is safer
        - **Moat**: Economic moat strength (0-10) - higher is stronger
        - **Resilience**: Financial resilience (0-10) - higher is more resilient
        """)


def render_allocation_charts(holdings: list):
    """
    Render allocation pie chart and treemap.

    Args:
        holdings: List of holding dicts
    """
    st.markdown("## Allocation")

    if not holdings:
        return

    try:
        import plotly.express as px
        import pandas as pd

        df = pd.DataFrame(holdings)

        # Create two columns for charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### By Security")

            # Pie chart by security
            if "symbol" in df.columns and "market_value" in df.columns:
                fig_pie = px.pie(
                    df,
                    values="market_value",
                    names="symbol",
                    title="Portfolio Allocation by Security",
                    hole=0.3,  # Donut chart
                )

                fig_pie.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                )

                fig_pie.update_layout(
                    showlegend=True,
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )

                st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.markdown("### By Currency")

            # Pie chart by currency
            if "currency" in df.columns and "market_value" in df.columns:
                df_currency = df.groupby("currency")["market_value"].sum().reset_index()

                fig_currency = px.pie(
                    df_currency,
                    values="market_value",
                    names="currency",
                    title="Portfolio Allocation by Currency",
                    hole=0.3,
                )

                fig_currency.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                )

                fig_currency.update_layout(
                    showlegend=True,
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )

                st.plotly_chart(fig_currency, use_container_width=True)

    except ImportError:
        st.warning("📊 Install plotly to see allocation charts: `pip install plotly`")


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
