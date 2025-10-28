"""
DawsOS Scenarios Screen

Purpose: Scenario analysis and stress testing
Updated: 2025-10-23
Priority: P0 (Core risk management)

Features:
    - Scenario selector (13 preset scenarios)
    - Delta P&L by holding
    - Portfolio impact summary
    - Hedge suggestions
    - Custom scenario builder

Usage:
    Called from main.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
from datetime import date
from typing import Optional, Dict, Any, List
from decimal import Decimal

from frontend.ui.components.dawsos_theme import apply_theme
from frontend.ui.client_factory import get_client


# ============================================================================
# Scenario Definitions (9 pre-defined + 4 historical)
# ============================================================================

PRESET_SCENARIOS = {
    "rates_up": {
        "name": "Rates +100bps",
        "description": "10Y Treasury rates rise by 1% (e.g., Fed tightening)",
        "icon": "📈",
        "category": "macro",
    },
    "rates_down": {
        "name": "Rates -100bps",
        "description": "10Y Treasury rates fall by 1% (e.g., flight to safety)",
        "icon": "📉",
        "category": "macro",
    },
    "usd_up": {
        "name": "USD +10%",
        "description": "US Dollar appreciates 10% vs basket",
        "icon": "💵",
        "category": "currency",
    },
    "usd_down": {
        "name": "USD -10%",
        "description": "US Dollar depreciates 10% vs basket",
        "icon": "💸",
        "category": "currency",
    },
    "equity_crash": {
        "name": "Equity -20%",
        "description": "Broad equity market falls 20% (correction)",
        "icon": "📉",
        "category": "equity",
    },
    "equity_rally": {
        "name": "Equity +20%",
        "description": "Broad equity market rallies 20% (risk-on)",
        "icon": "📈",
        "category": "equity",
    },
    "credit_widening": {
        "name": "Credit Spreads +200bps",
        "description": "Investment-grade spreads widen 2% (risk-off)",
        "icon": "🔴",
        "category": "credit",
    },
    "inflation_shock": {
        "name": "Inflation +3%",
        "description": "CPI jumps 3% (supply shock or overheating)",
        "icon": "🔥",
        "category": "macro",
    },
    "volatility_spike": {
        "name": "VIX +20pts",
        "description": "VIX spikes from 15 to 35 (panic)",
        "icon": "⚠️",
        "category": "volatility",
    },
    "crisis_2008": {
        "name": "2008 Financial Crisis",
        "description": "Sept 2008 - Feb 2009 (Lehman collapse)",
        "icon": "🏦",
        "category": "historical",
    },
    "covid_2020": {
        "name": "2020 COVID Crash",
        "description": "Feb 2020 - Mar 2020 (pandemic panic)",
        "icon": "🦠",
        "category": "historical",
    },
    "russia_2022": {
        "name": "2022 Russia Invasion",
        "description": "Feb 2022 - Mar 2022 (Ukraine war)",
        "icon": "🌍",
        "category": "historical",
    },
    "svb_2023": {
        "name": "2023 Banking Crisis",
        "description": "Mar 2023 (SVB/Credit Suisse)",
        "icon": "🏛️",
        "category": "historical",
    },
}


# ============================================================================
# Main Scenarios Screen
# ============================================================================


def render_scenarios(portfolio_id: str, asof_date: Optional[date] = None):
    """
    Render scenarios screen with scenario analysis.

    Args:
        portfolio_id: Portfolio UUID
        asof_date: As-of date (optional, defaults to latest)
    """
    apply_theme()

    # Initialize API client
    client = get_client()

    if asof_date is None:
        asof_date = date.today()

    st.markdown("# 📈 Scenario Analysis")
    st.markdown(f"**Portfolio**: {portfolio_id}")
    st.markdown(f"**As of**: {asof_date}")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Preset Scenarios", "Custom Scenario", "History"])

    with tab1:
        render_preset_scenarios(client, portfolio_id, asof_date)

    with tab2:
        render_custom_scenario_builder(client, portfolio_id, asof_date)

    with tab3:
        render_scenario_history(client, portfolio_id)


# ============================================================================
# Preset Scenarios Tab
# ============================================================================


def render_preset_scenarios(client, portfolio_id: str, asof_date: date):
    """Render preset scenario selector and results."""

    st.markdown("## Preset Scenarios")
    st.markdown("Select a scenario to analyze impact on your portfolio.")

    # Group scenarios by category
    categories = {
        "macro": "Macro Scenarios",
        "currency": "Currency Scenarios",
        "equity": "Equity Scenarios",
        "credit": "Credit Scenarios",
        "volatility": "Volatility Scenarios",
        "historical": "Historical Scenarios",
    }

    # Category selector
    selected_category = st.selectbox(
        "Category",
        options=list(categories.keys()),
        format_func=lambda x: categories[x],
        help="Filter scenarios by category",
    )

    # Scenario selector (filtered by category)
    filtered_scenarios = {
        k: v
        for k, v in PRESET_SCENARIOS.items()
        if v["category"] == selected_category
    }

    scenario_cols = st.columns(min(3, len(filtered_scenarios)))

    selected_scenario = None
    for idx, (scenario_id, scenario) in enumerate(filtered_scenarios.items()):
        with scenario_cols[idx % 3]:
            if st.button(
                f"{scenario['icon']} {scenario['name']}",
                help=scenario["description"],
                use_container_width=True,
            ):
                selected_scenario = scenario_id

    # Store selected scenario in session state
    if selected_scenario:
        st.session_state["selected_scenario"] = selected_scenario

    # If scenario selected, run analysis
    if "selected_scenario" in st.session_state:
        scenario_id = st.session_state["selected_scenario"]
        scenario_info = PRESET_SCENARIOS[scenario_id]

        st.markdown("---")
        st.markdown(f"## {scenario_info['icon']} {scenario_info['name']}")
        st.markdown(f"_{scenario_info['description']}_")

        # Run scenario analysis via pattern
        with st.spinner(f"Running {scenario_info['name']} analysis..."):
            try:
                result = client.execute(
                    pattern_id="portfolio_scenario_analysis",
                    inputs={
                        "portfolio_id": portfolio_id,
                        "scenario_id": scenario_id,
                    },
                    portfolio_id=portfolio_id,
                    asof_date=asof_date,
                    require_fresh=False,  # Can use cache for scenarios
                )

                # Extract scenario results
                scenario_data = result.get("data", {})
                render_scenario_results(scenario_data, scenario_info)

            except Exception as e:
                st.error(f"❌ Error running scenario analysis: {str(e)}")
                st.markdown(
                    """
                    **Possible Causes**:
                    - Executor API not running (start with `./start.sh`)
                    - Scenario service not implemented
                    - Pattern not registered
                    """
                )


# ============================================================================
# Scenario Results Display
# ============================================================================


def render_scenario_results(scenario_data: Dict[str, Any], scenario_info: Dict[str, str]):
    """
    Render scenario analysis results.

    Args:
        scenario_data: Pattern result data
        scenario_info: Scenario metadata
    """
    if not scenario_data:
        st.warning("No scenario data returned from analysis.")
        return

    # Portfolio-level impact
    st.markdown("### Portfolio Impact")

    portfolio_impact = scenario_data.get("portfolio_impact", {})
    delta_pnl = portfolio_impact.get("delta_pnl", 0)
    delta_pnl_pct = portfolio_impact.get("delta_pnl_pct", 0)
    nav = portfolio_impact.get("nav", 0)

    col1, col2, col3 = st.columns(3)

    with col1:
        delta_color = "green" if delta_pnl >= 0 else "red"
        st.metric(
            "Delta P&L",
            f"${delta_pnl:,.0f}",
            delta=f"{delta_pnl_pct:+.2f}%",
            delta_color=delta_color,
        )

    with col2:
        st.metric("Portfolio NAV", f"${nav:,.0f}")

    with col3:
        stressed_nav = nav + delta_pnl
        st.metric("Stressed NAV", f"${stressed_nav:,.0f}")

    # Holdings-level impact
    st.markdown("---")
    st.markdown("### Delta P&L by Holding")

    holdings_impact = scenario_data.get("holdings_impact", [])

    if holdings_impact:
        # Sort by absolute delta P&L (largest impacts first)
        sorted_holdings = sorted(
            holdings_impact, key=lambda h: abs(h.get("delta_pnl", 0)), reverse=True
        )

        # Table display
        holding_rows = []
        for holding in sorted_holdings:
            symbol = holding.get("symbol", "N/A")
            position_value = holding.get("position_value", 0)
            delta_pnl = holding.get("delta_pnl", 0)
            delta_pnl_pct = holding.get("delta_pnl_pct", 0)

            # Color code
            delta_color = "🟢" if delta_pnl >= 0 else "🔴"

            holding_rows.append({
                "Symbol": symbol,
                "Position Value": f"${position_value:,.0f}",
                "Delta P&L": f"${delta_pnl:,.0f}",
                "Delta %": f"{delta_pnl_pct:+.2f}%",
                "Impact": delta_color,
            })

        import pandas as pd

        df = pd.DataFrame(holding_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Top losers / winners
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🔴 Top Losers")
            losers = [h for h in sorted_holdings if h.get("delta_pnl", 0) < 0][:5]
            if losers:
                for loser in losers:
                    st.markdown(
                        f"**{loser['symbol']}**: ${loser['delta_pnl']:,.0f} ({loser['delta_pnl_pct']:+.2f}%)"
                    )
            else:
                st.info("No losers in this scenario")

        with col2:
            st.markdown("#### 🟢 Top Winners")
            winners = [h for h in sorted_holdings if h.get("delta_pnl", 0) > 0][:5]
            if winners:
                for winner in winners:
                    st.markdown(
                        f"**{winner['symbol']}**: ${winner['delta_pnl']:,.0f} ({winner['delta_pnl_pct']:+.2f}%)"
                    )
            else:
                st.info("No winners in this scenario")

    else:
        st.warning("No holdings impact data available.")

    # Hedge suggestions
    st.markdown("---")
    st.markdown("### 💡 Hedge Suggestions")

    hedge_suggestions = scenario_data.get("hedge_suggestions", [])

    if hedge_suggestions:
        for suggestion in hedge_suggestions:
            hedge_symbol = suggestion.get("symbol", "N/A")
            hedge_rationale = suggestion.get("rationale", "N/A")
            hedge_quantity = suggestion.get("quantity", 0)

            st.markdown(f"**{hedge_symbol}** ({hedge_quantity:,.0f} shares)")
            st.markdown(f"_{hedge_rationale}_")
    else:
        st.info("No hedge suggestions available for this scenario.")

    # Factor exposures (if available)
    factor_exposures = scenario_data.get("factor_exposures", {})
    if factor_exposures:
        st.markdown("---")
        st.markdown("### 🧬 Factor Exposures")

        factor_cols = st.columns(4)
        for idx, (factor, beta) in enumerate(factor_exposures.items()):
            with factor_cols[idx % 4]:
                st.metric(factor.replace("_", " ").title(), f"{beta:.2f}")


# ============================================================================
# Custom Scenario Builder Tab
# ============================================================================


def render_custom_scenario_builder(client, portfolio_id: str, asof_date: date):
    """Render custom scenario builder (JSON editor)."""

    st.markdown("## Custom Scenario Builder")
    st.markdown("Build your own scenario by specifying factor shocks.")

    # Factor shock inputs
    st.markdown("### Factor Shocks")

    col1, col2 = st.columns(2)

    with col1:
        real_rate_shock = st.number_input(
            "Real Rate Shock (bps)",
            min_value=-500,
            max_value=500,
            value=0,
            step=25,
            help="Change in 10Y TIPS yield (basis points)",
        )

        inflation_shock = st.number_input(
            "Inflation Shock (bps)",
            min_value=-500,
            max_value=500,
            value=0,
            step=25,
            help="Change in breakeven inflation (basis points)",
        )

        credit_shock = st.number_input(
            "Credit Spread Shock (bps)",
            min_value=-200,
            max_value=500,
            value=0,
            step=25,
            help="Change in IG credit spreads (basis points)",
        )

        usd_shock = st.number_input(
            "USD Shock (%)",
            min_value=-30.0,
            max_value=30.0,
            value=0.0,
            step=1.0,
            help="Change in USD DXY index (percent)",
        )

    with col2:
        equity_shock = st.number_input(
            "Equity Shock (%)",
            min_value=-50.0,
            max_value=50.0,
            value=0.0,
            step=5.0,
            help="Change in S&P 500 (percent)",
        )

        commodity_shock = st.number_input(
            "Commodity Shock (%)",
            min_value=-50.0,
            max_value=50.0,
            value=0.0,
            step=5.0,
            help="Change in commodity index (percent)",
        )

        volatility_shock = st.number_input(
            "Volatility Shock (pts)",
            min_value=-20.0,
            max_value=50.0,
            value=0.0,
            step=5.0,
            help="Change in VIX (points)",
        )

    # Run button
    if st.button("🚀 Run Custom Scenario", type="primary", use_container_width=True):
        # Build custom scenario JSON
        custom_scenario = {
            "name": "Custom Scenario",
            "shocks": {
                "real_rate": real_rate_shock,
                "inflation": inflation_shock,
                "credit": credit_shock,
                "usd": usd_shock,
                "equity": equity_shock,
                "commodity": commodity_shock,
                "volatility": volatility_shock,
            },
        }

        st.markdown("---")
        st.markdown("### Custom Scenario Results")

        with st.spinner("Running custom scenario analysis..."):
            try:
                result = client.execute(
                    pattern_id="portfolio_scenario_analysis",
                    inputs={
                        "portfolio_id": portfolio_id,
                        "scenario_id": "custom",
                        "custom_shocks": custom_scenario["shocks"],
                    },
                    portfolio_id=portfolio_id,
                    asof_date=asof_date,
                    require_fresh=True,  # Always fresh for custom
                )

                scenario_data = result.get("data", {})
                render_scenario_results(scenario_data, custom_scenario)

            except Exception as e:
                st.error(f"❌ Error running custom scenario: {str(e)}")


# ============================================================================
# Scenario History Tab
# ============================================================================


def render_scenario_history(client, portfolio_id: str):
    """Render historical scenario results."""

    st.markdown("## Scenario History")
    st.info("📊 Historical scenario results coming soon!")
    st.markdown(
        """
    **Planned Features**:
    - Table of past scenario runs (date, scenario, delta P&L)
    - Trend analysis (how portfolio sensitivity has changed)
    - Comparison of scenarios (best/worst case)
    - Export to CSV
    """
    )


# ============================================================================
# Standalone Run
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="DawsOS - Scenarios",
        page_icon="📈",
        layout="wide",
    )

    render_scenarios(
        portfolio_id="11111111-1111-1111-1111-111111111111", asof_date=date.today()
    )
