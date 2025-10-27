"""
DawsOS Macro Dashboard Screen

Purpose: Macro regime, cycles (STDC/LTDC/Empire), factor exposures, DaR
Updated: 2025-10-22
Priority: P0 (Core differentiator)

Features:
    - Regime card (5 regimes with confidence)
    - Macro cycles (STDC, LTDC, Empire) with timeline visualization
    - Factor exposures (placeholder)
    - DaR (Drawdown at Risk) (placeholder)

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
from typing import Optional

from frontend.ui.components.dawsos_theme import apply_theme
from frontend.ui.client_factory import get_client


def render_macro_dashboard(asof_date: Optional[date] = None):
    """
    Render macro dashboard with regime, cycles, factors, and DaR.

    Args:
        asof_date: As-of date (optional, defaults to latest)
    """
    apply_theme()

    # Initialize API client
    client = get_client()

    if asof_date is None:
        asof_date = date.today()

    st.markdown("# 🌍 Macro Dashboard")
    st.markdown(f"**As of**: {asof_date}")

    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Regime & Cycles", "Factor Exposures", "DaR (Risk)", "Trends"]
    )

    with tab1:
        render_regime_and_cycles(client, asof_date)

    with tab2:
        render_factor_exposures()

    with tab3:
        render_dar()

    with tab4:
        render_trends()


def render_regime_and_cycles(client, asof_date: date):
    """Render regime card and cycle timelines."""

    with st.spinner("Loading macro regime and cycles..."):
        try:
            # Execute macro pattern via Executor API
            result = client.execute(
                pattern_id="portfolio_macro_overview",
                inputs={},
                asof_date=asof_date,
                require_fresh=True,
            )

            # Extract regime and cycles from pattern result
            regime = result.get("data", {}).get("regime", {})
            cycles = result.get("data", {}).get("cycles", {})

            # Regime Card
            render_regime_card(regime)

            st.markdown("---")

            # Cycles Section
            render_cycles_section(cycles)

        except Exception as e:
            st.error(f"❌ Error loading macro data: {str(e)}")


def render_regime_card(regime: dict):
    """
    Render macro regime card.

    Args:
        regime: Regime dict with regime, confidence, indicators
    """
    st.markdown("## Current Macro Regime")

    # Main regime display
    regime_name = regime.get("regime_name", regime.get("regime", "Unknown"))
    confidence = regime.get("confidence", 0.0)

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Large regime display
        st.markdown(
            f"""
            <div style="background-color: var(--bg-secondary); padding: 24px; border-radius: 8px;">
                <h2 style="margin: 0; color: var(--accent-teal);">{regime_name}</h2>
                <p style="margin: 8px 0 0 0; color: var(--text-muted);">Macro Economic Regime</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.metric("Confidence", f"{confidence*100:.1f}%", delta=None)

    with col3:
        st.metric("Date", regime.get("date", "N/A"), delta=None)

    # Indicators
    st.markdown("### Key Indicators")

    indicators = regime.get("indicators", {})
    zscores = regime.get("zscores", {})

    if indicators:
        cols = st.columns(min(4, len(indicators)))

        for idx, (indicator, value) in enumerate(indicators.items()):
            with cols[idx % 4]:
                zscore = zscores.get(indicator, 0.0)
                zscore_str = f"{zscore:+.2f}σ" if zscore else "N/A"

                st.markdown(
                    f"""
                    <div style="background-color: var(--bg-secondary); padding: 12px; border-radius: 4px;">
                        <div style="font-size: 0.75rem; color: var(--text-muted);">{indicator}</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">{value}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Z-score: {zscore_str}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Regime explanation
    with st.expander("ℹ️ About Macro Regimes"):
        st.markdown("""
        **5 Macro Regimes** (Dalio Framework):

        1. **Early Expansion** - Recovery phase, yield curve steepening, unemployment falling
        2. **Mid Expansion** - Strong GDP growth, job creation accelerating
        3. **Late Expansion** - Inflation rising, yield curve flattening, tight labor markets
        4. **Early Contraction** - Yield curve inverted, growth slowing
        5. **Deep Contraction** - Unemployment rising sharply, GDP contracting

        **Confidence Score**: Probability that current indicators match this regime (0-100%)

        **Z-scores**: Standard deviations from 252-day rolling mean (±2σ is significant)
        """)


def render_cycles_section(cycles: dict):
    """
    Render macro cycles section (STDC, LTDC, Empire).

    Args:
        cycles: Dict with stdc, ltdc, empire cycle data
    """
    st.markdown("## Macro Cycles")

    # Create three columns for the three cycles
    col1, col2, col3 = st.columns(3)

    with col1:
        render_cycle_card(cycles.get("stdc", {}), "STDC", "Short-Term Debt Cycle", "5-10 years")

    with col2:
        render_cycle_card(cycles.get("ltdc", {}), "LTDC", "Long-Term Debt Cycle", "50-75 years")

    with col3:
        render_cycle_card(cycles.get("empire", {}), "EMPIRE", "Empire Cycle", "200-300 years")

    # Cycles explanation
    with st.expander("ℹ️ About Macro Cycles"):
        st.markdown("""
        **Three Macro Cycles** (Dalio Framework):

        ### STDC (Short-Term Debt Cycle) - 5-10 years
        Business cycle driven by credit expansion and contraction:
        1. Early Recovery
        2. Mid Expansion
        3. Late Expansion / Boom
        4. Early Recession
        5. Deep Recession

        ### LTDC (Long-Term Debt Cycle) - 50-75 years
        Debt super cycle:
        1. Deleveraging
        2. Reflation
        3. Expansion
        4. Bubble
        5. Top
        6. Debt Crisis
        7. Depression

        ### Empire Cycle - 200-300 years
        Rise and decline of global powers:
        1. Rise
        2. Peak
        3. Decline
        4. Collapse

        **Composite Score**: Strength of indicator match for current phase (0-1)
        """)


def render_cycle_card(cycle_data: dict, cycle_type: str, cycle_name: str, duration: str):
    """
    Render individual cycle card.

    Args:
        cycle_data: Cycle phase data
        cycle_type: Cycle type (STDC, LTDC, EMPIRE)
        cycle_name: Full cycle name
        duration: Cycle duration
    """
    if not cycle_data:
        st.warning(f"No {cycle_type} data available")
        return

    phase = cycle_data.get("phase", "Unknown")
    phase_number = cycle_data.get("phase_number", 0)
    composite_score = cycle_data.get("composite_score", 0.0)

    st.markdown(
        f"""
        <div style="background-color: var(--bg-secondary); padding: 16px; border-radius: 8px; height: 100%;">
            <h4 style="margin: 0; color: var(--accent-blue);">{cycle_type}</h4>
            <p style="margin: 4px 0; font-size: 0.75rem; color: var(--text-muted);">{cycle_name}</p>
            <p style="margin: 4px 0; font-size: 0.75rem; color: var(--text-muted);">{duration}</p>
            <hr style="margin: 12px 0; border: none; border-top: 1px solid var(--border-color);">
            <h3 style="margin: 8px 0; color: var(--text-primary);">{phase}</h3>
            <p style="margin: 4px 0; font-size: 0.875rem; color: var(--text-muted);">Phase {phase_number}</p>
            <p style="margin: 8px 0; font-size: 0.875rem; color: var(--text-muted);">
                Score: <span style="color: var(--accent-teal);">{composite_score:.2f}</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_factor_exposures():
    """Render factor exposures section (placeholder)."""
    st.markdown("## Factor Exposures")
    st.info("📊 Factor exposures (Value, Growth, Quality, Momentum, Low Vol, Size) coming soon!")
    st.markdown("""
    **Planned Features**:
    - Factor bar chart (portfolio vs benchmark)
    - Factor attribution (return contribution)
    - Factor betas
    - Active exposures (portfolio - benchmark)
    """)


def render_dar():
    """Render DaR section (placeholder)."""
    st.markdown("## DaR (Drawdown at Risk)")
    st.info("📉 DaR calculation with scenario stress testing coming soon!")
    st.markdown("""
    **Planned Features**:
    - DaR value (95% confidence)
    - Scenario distribution histogram
    - Worst scenario identification
    - 13 historical scenarios (2008 Crisis, COVID-19, etc.)
    """)


def render_trends():
    """Render trends section (placeholder)."""
    st.markdown("## Macro Trends")
    st.info("📈 Trend monitoring and alert presets coming soon!")
    st.markdown("""
    **Planned Features**:
    - Regime trend (stable/strengthening/weakening)
    - Factor trend (momentum shifts)
    - Alert preset suggestions
    - 90-day regime timeline
    """)


if __name__ == "__main__":
    st.set_page_config(
        page_title="DawsOS - Macro Dashboard",
        page_icon="🌍",
        layout="wide",
    )

    render_macro_dashboard()
