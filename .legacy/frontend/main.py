"""
DawsOS - Main Application Entry Point

Purpose: Multi-screen navigation with sidebar
Updated: 2025-10-22
Priority: P0 (Critical for UI navigation)

Screens:
    - Portfolio Overview: Main dashboard with KPIs and attribution
    - Holdings: Holdings list and deep-dive analysis
    - Macro Dashboard: Regime, cycles, factor exposures, DaR
    - Scenarios: Stress testing and what-if analysis
    - Alerts: Alert management (coming soon)
    - Reports: PDF export (coming soon)
    - Optimizer: Policy rebalancing (coming soon)
    - Settings: Configuration

Usage:
    streamlit run frontend/main.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from frontend.ui.components.dawsos_theme import apply_theme

# Configuration - Use real API by default (set USE_MOCK_CLIENT=true for mock data)
USE_MOCK_CLIENT = os.getenv("USE_MOCK_CLIENT", "false").lower() == "true"
API_BASE_URL = os.getenv("EXECUTOR_API_URL", "http://localhost:8000")


def main():
    """Main application entry point with navigation."""

    # Apply DawsOS dark theme
    st.set_page_config(
        page_title="DawsOS - Portfolio Intelligence",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    # Sidebar navigation
    with st.sidebar:
        st.markdown("# 📊 DawsOS")
        st.markdown("Portfolio Intelligence Platform")
        st.markdown("---")

        # Portfolio selector (multi-portfolio support)
        portfolio_id = st.selectbox(
            "Portfolio",
            options=[
                ("11111111-1111-1111-1111-111111111111", "Core Balanced"),
            ],
            format_func=lambda x: x[1],
            help="Select portfolio to analyze",
        )

        st.markdown("---")

        # Main navigation
        page = st.radio(
            "Navigation",
            options=[
                "Portfolio Overview",
                "Holdings",
                "Macro Dashboard",
                "Scenarios",
                "Alerts",
                "Reports",
                "Optimizer",
                "Settings",
            ],
            help="Select screen to view",
        )

        st.markdown("---")

        # Status indicators
        st.markdown("### System Status")
        if USE_MOCK_CLIENT:
            st.info("🔄 **Mock Mode**\n\nUsing mock data")
        else:
            st.success(f"✅ **API Connected**\n\n{API_BASE_URL}")

        st.markdown("---")
        st.markdown("**Version**: v1.0.0")
        st.markdown("**Build**: 2025-10-22")

    # Route to selected page
    portfolio_id_str = portfolio_id[0] if isinstance(portfolio_id, tuple) else portfolio_id

    if page == "Portfolio Overview":
        from frontend.ui.screens.portfolio_overview import render_portfolio_overview
        render_portfolio_overview(portfolio_id=portfolio_id_str)

    elif page == "Holdings":
        from frontend.ui.screens.holdings import render_holdings
        render_holdings(portfolio_id=portfolio_id_str)

    elif page == "Macro Dashboard":
        from frontend.ui.screens.macro_dashboard import render_macro_dashboard
        render_macro_dashboard()

    elif page == "Scenarios":
        from frontend.ui.screens.scenarios import render_scenarios
        render_scenarios(portfolio_id=portfolio_id_str)

    elif page == "Alerts":
        st.markdown("# 🔔 Alerts")
        st.info("⚠️ Alert management coming soon!")
        st.markdown("""
        **Planned Features**:
        - Alert conditions table (Regime Change, Drawdown, Volatility Spike, etc.)
        - Create/edit alert form
        - Delivery history
        - Alert presets
        """)

    elif page == "Reports":
        st.markdown("# 📄 Reports")
        st.info("📑 PDF export coming soon!")
        st.markdown("""
        **Planned Features**:
        - Report generator (Portfolio Summary, Holdings Detail, Macro Analysis, etc.)
        - Rights gate display (provider attributions)
        - Export history
        - WeasyPrint PDF generation
        """)

    elif page == "Optimizer":
        st.markdown("# ⚙️ Optimizer")
        st.info("🎯 Policy-based rebalancing coming soon!")
        st.markdown("""
        **Planned Features**:
        - Current allocation vs policy targets
        - Policy constraints (asset allocation, tracking error, turnover)
        - Optimizer run (mean-variance, risk parity, etc.)
        - Proposed trades table
        """)

    elif page == "Settings":
        from frontend.ui.screens.settings import render_settings
        render_settings()


if __name__ == "__main__":
    main()
