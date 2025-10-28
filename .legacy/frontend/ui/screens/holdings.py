"""
DawsOS Holdings Screen

Purpose: Holdings list and deep-dive analysis with Buffett ratings
Updated: 2025-10-23
Priority: P0 (Critical UAT gap)

Features:
    - Holdings list with positions and valuations
    - Deep-dive analysis for individual holdings
    - Buffett ratings (DivSafety, Moat, Resilience)
    - News sentiment and fundamentals
    - Wired to holding_deep_dive pattern

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
from frontend.ui.client_factory import get_client, is_mock_mode, get_api_url


def render_holdings(portfolio_id: str, asof_date: Optional[date] = None):
    """
    Render holdings screen with list and deep-dive.

    Args:
        portfolio_id: Portfolio ID (UUID)
        asof_date: As-of date (optional, defaults to today)
    """
    apply_theme()

    # Initialize API client
    client = get_client()

    if is_mock_mode():
        st.info("ℹ️ Using mock data (API not connected)")

    if asof_date is None:
        asof_date = date.today()

    st.markdown("# 📊 Holdings")
    st.markdown(f"**Portfolio**: {portfolio_id[:8]}...")
    st.markdown(f"**As of**: {asof_date.isoformat()}")

    # Execute portfolio_overview pattern to get holdings list
    with st.spinner("Loading holdings..."):
        try:
            result = client.execute(
                pattern_id="portfolio_overview",
                inputs={"portfolio_id": portfolio_id},
                portfolio_id=portfolio_id,
                asof_date=asof_date,
                require_fresh=True,
            )

            holdings = result.get("data", {}).get("valued_positions", [])

            if not holdings:
                st.warning("No holdings found for this portfolio.")
                return

            # Render holdings list
            render_holdings_list(holdings)

            # Holding selection for deep-dive
            st.markdown("---")
            st.markdown("## Deep Dive")

            symbols = [h.get("symbol") for h in holdings if h.get("symbol")]
            if symbols:
                selected_symbol = st.selectbox(
                    "Select holding for deep analysis",
                    options=symbols,
                    help="Choose a holding to see ratings, fundamentals, and news",
                )

                if selected_symbol:
                    render_holding_deep_dive(client, selected_symbol, asof_date)

        except Exception as e:
            st.error(f"❌ Error loading holdings: {str(e)}")
            with st.expander("Troubleshooting"):
                st.markdown(
                    f"""
                    **Possible issues**:
                    - API not running at `{get_api_url()}`
                    - Portfolio ID `{portfolio_id}` not found
                    - No positions in portfolio

                    **Quick fixes**:
                    1. Start backend API: `./backend/run_api.sh` (or `uvicorn backend.app.api.executor:app --reload`)
                    2. Verify portfolio exists: Check database
                    3. Execute trades to create positions
                    """
                )


def render_holdings_list(holdings: list):
    """
    Render holdings list as table.

    Args:
        holdings: List of holding dicts with symbol, qty, value, etc.
    """
    st.markdown("## Current Holdings")

    # Create table data
    table_data = []
    for holding in holdings:
        table_data.append({
            "Symbol": holding.get("symbol", "N/A"),
            "Qty": f"{holding.get('qty', 0):,.2f}",
            "Price": f"${holding.get('price', 0):,.2f}",
            "Value": f"${holding.get('value', 0):,.2f}",
            "Weight": f"{holding.get('weight', 0) * 100:.2f}%",
            "Currency": holding.get("currency", "N/A"),
        })

    # Display as dataframe
    if table_data:
        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
        )

        # Summary stats
        total_value = sum(h.get("value", 0) for h in holdings)
        st.markdown(f"**Total Portfolio Value**: ${total_value:,.2f}")
        st.markdown(f"**Number of Holdings**: {len(holdings)}")
    else:
        st.info("No holdings data available")


def render_holding_deep_dive(client, symbol: str, asof_date: date):
    """
    Render deep-dive analysis for a single holding.

    Args:
        client: API client
        symbol: Stock symbol
        asof_date: As-of date
    """
    st.markdown(f"### {symbol} Deep Dive")

    with st.spinner(f"Loading analysis for {symbol}..."):
        try:
            # Execute holding_deep_dive pattern
            result = client.execute(
                pattern_id="holding_deep_dive",
                inputs={"symbol": symbol},
                asof_date=asof_date,
                require_fresh=False,  # Allow slightly stale data for fundamentals
            )

            # Extract data
            ratings = result.get("data", {}).get("ratings", {})
            fundamentals = result.get("data", {}).get("fundamentals", {})
            news = result.get("data", {}).get("news", [])

            # Tabs for different sections
            tab1, tab2, tab3 = st.tabs(["Buffett Ratings", "Fundamentals", "News"])

            with tab1:
                render_buffett_ratings(ratings)

            with tab2:
                render_fundamentals(fundamentals)

            with tab3:
                render_news(news, symbol)

        except Exception as e:
            st.error(f"❌ Error loading deep-dive for {symbol}: {str(e)}")


def render_buffett_ratings(ratings: dict):
    """
    Render Buffett ratings (DivSafety, Moat, Resilience).

    Args:
        ratings: Ratings dict with scores 0-10
    """
    st.markdown("#### Buffett Quality Ratings")

    if not ratings:
        st.warning("⚠️ Ratings service not yet implemented. Showing placeholder.")
        ratings = {
            "dividend_safety": None,
            "moat": None,
            "resilience": None,
        }

    # Display ratings as cards
    col1, col2, col3 = st.columns(3)

    with col1:
        div_safety = ratings.get("dividend_safety")
        if div_safety is not None:
            color = get_rating_color(div_safety)
            st.markdown(
                f"""
                <div style="background-color: var(--bg-secondary); padding: 20px; border-radius: 8px; border-left: 4px solid {color};">
                    <h4 style="margin: 0;">Dividend Safety</h4>
                    <h2 style="margin: 8px 0; color: {color};">{div_safety:.1f}/10</h2>
                    <p style="margin: 0; color: var(--text-muted); font-size: 14px;">Payout sustainability</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Dividend Safety\n\nNot yet calculated")

    with col2:
        moat = ratings.get("moat")
        if moat is not None:
            color = get_rating_color(moat)
            st.markdown(
                f"""
                <div style="background-color: var(--bg-secondary); padding: 20px; border-radius: 8px; border-left: 4px solid {color};">
                    <h4 style="margin: 0;">Economic Moat</h4>
                    <h2 style="margin: 8px 0; color: {color};">{moat:.1f}/10</h2>
                    <p style="margin: 0; color: var(--text-muted); font-size: 14px;">Competitive advantage</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Economic Moat\n\nNot yet calculated")

    with col3:
        resilience = ratings.get("resilience")
        if resilience is not None:
            color = get_rating_color(resilience)
            st.markdown(
                f"""
                <div style="background-color: var(--bg-secondary); padding: 20px; border-radius: 8px; border-left: 4px solid {color};">
                    <h4 style="margin: 0;">Resilience</h4>
                    <h2 style="margin: 8px 0; color: {color};">{resilience:.1f}/10</h2>
                    <p style="margin: 0; color: var(--text-muted); font-size: 14px;">Crisis performance</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Resilience\n\nNot yet calculated")

    st.markdown("---")
    st.markdown(
        """
        **Note**: Buffett ratings are calculated based on:
        - **Dividend Safety**: Payout ratio, coverage, 5Y consistency
        - **Economic Moat**: ROIC, margins, market share, pricing power
        - **Resilience**: Debt/equity, interest coverage, 2008/2020 performance
        """
    )


def render_fundamentals(fundamentals: dict):
    """
    Render fundamental metrics.

    Args:
        fundamentals: Fundamentals dict with income statement, balance sheet, etc.
    """
    st.markdown("#### Fundamental Metrics")

    if not fundamentals:
        st.warning("⚠️ Fundamentals fetcher not yet fully implemented. Showing placeholder.")
        return

    # Display key metrics
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Income Statement**")
        st.metric("Revenue", fundamentals.get("revenue", "N/A"))
        st.metric("Net Income", fundamentals.get("net_income", "N/A"))
        st.metric("Operating Margin", fundamentals.get("operating_margin", "N/A"))

    with col2:
        st.markdown("**Balance Sheet**")
        st.metric("Total Assets", fundamentals.get("total_assets", "N/A"))
        st.metric("Total Debt", fundamentals.get("total_debt", "N/A"))
        st.metric("Debt/Equity", fundamentals.get("debt_to_equity", "N/A"))


def render_news(news: list, symbol: str):
    """
    Render news articles.

    Args:
        news: List of news article dicts
        symbol: Stock symbol
    """
    st.markdown("#### Recent News")

    if not news:
        st.info(f"No recent news available for {symbol}.")
        st.markdown(
            """
            **Note**: News service requires NewsAPI key. Set `NEWSAPI_KEY` environment variable.
            Dev plan restrictions apply (24h delay for free tier).
            """
        )
        return

    # Display news articles
    for article in news[:5]:  # Limit to 5 most recent
        st.markdown(f"**{article.get('title', 'No title')}**")
        st.markdown(f"*{article.get('source', 'Unknown source')} - {article.get('publishedAt', 'N/A')}*")
        st.markdown(article.get('description', 'No description'))
        if article.get('url'):
            st.markdown(f"[Read more]({article['url']})")
        st.markdown("---")


def get_rating_color(score: float) -> str:
    """
    Get color for rating score.

    Args:
        score: Rating score 0-10

    Returns:
        Color hex code
    """
    if score >= 8:
        return "#00e676"  # Green (excellent)
    elif score >= 6:
        return "#76ff03"  # Light green (good)
    elif score >= 4:
        return "#ffd600"  # Yellow (neutral)
    elif score >= 2:
        return "#ff9100"  # Orange (poor)
    else:
        return "#ff1744"  # Red (very poor)


if __name__ == "__main__":
    # Standalone testing
    render_holdings("11111111-1111-1111-1111-111111111111")
