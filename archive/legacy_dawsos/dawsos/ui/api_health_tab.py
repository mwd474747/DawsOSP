#!/usr/bin/env python3
"""
API Health & Fallback Monitoring Tab

Provides transparency into API health, fallback events, and data freshness.
Shows users when cached/fallback data is being used and why.

Phase 3.1: Comprehensive type hints added
Phase 2.3: Refactored into maintainable helper functions
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Tuple
from core.fallback_tracker import get_fallback_tracker
from core.credentials import get_credential_manager


def _render_dashboard_header() -> None:
    """Render the dashboard header and title."""
    st.header("🔌 API Health Monitor")
    st.markdown("Real-time monitoring of API health, fallback events, and data freshness")


def _render_fallback_statistics(stats: Dict[str, Any]) -> None:
    """
    Render fallback event statistics metrics.

    Args:
        stats: Dictionary containing fallback statistics
    """
    st.subheader("📊 Fallback Event Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Fallbacks",
            stats.get('total_fallbacks', 0),
            help="Total number of times cached/fallback data was used"
        )

    with col2:
        st.metric(
            "LLM Fallbacks",
            stats.get('llm_fallbacks', 0),
            help="Times Claude AI used cached responses (API key missing or error)"
        )

    with col3:
        st.metric(
            "API Fallbacks",
            stats.get('api_fallbacks', 0),
            help="Times external APIs used cached data (FRED, market data, etc.)"
        )

    with col4:
        st.metric(
            "Cache Hits",
            stats.get('cache_hits', 0),
            help="Times cache was used for performance (not due to errors)"
        )


def _render_recent_events(stats: Dict[str, Any]) -> None:
    """
    Render recent fallback events with details.

    Args:
        stats: Dictionary containing fallback statistics and recent events
    """
    recent_events = stats.get('recent_events', [])

    if recent_events:
        st.subheader("🕐 Recent Fallback Events")
        st.caption("Most recent fallback events (last 10)")

        for event in reversed(recent_events[-5:]):  # Show last 5
            component = event.get('component', 'Unknown')
            reason = event.get('reason', 'Unknown')
            data_type = event.get('data_type', 'cached')
            timestamp = event.get('timestamp', '')

            # Determine icon based on component
            icon = "🤖" if component == 'llm' else "📡"

            with st.expander(f"{icon} {component} - {timestamp[:19]}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Component:** {component}")
                    st.markdown(f"**Reason:** {reason}")

                with col2:
                    st.markdown(f"**Data Type:** {data_type}")
                    st.markdown(f"**Time:** {timestamp[:19]}")

                # Show explanation based on reason
                if reason == 'api_key_missing':
                    st.info("💡 Configure API key in `.env` file to enable live data")
                elif reason == 'api_error':
                    st.warning("⚠️ API temporarily unavailable - using cached data")
                elif reason == 'rate_limit':
                    st.warning("⏱️ API rate limit reached - using cached data")
    else:
        st.info("No fallback events recorded yet. System is using live API data.")


def _render_api_configuration_status() -> None:
    """Render API key configuration status for all APIs."""
    st.subheader("🔑 API Configuration Status")
    st.caption("Check which API keys are configured")

    creds = get_credential_manager()

    # Define API keys to check
    api_keys: List[Tuple[str, str, str]] = [
        ('ANTHROPIC_API_KEY', 'Claude AI', '🤖'),
        ('FRED_API_KEY', 'Economic Data (FRED)', '📊'),
        ('FMP_API_KEY', 'Market Data (FMP)', '📈'),
        ('NEWSAPI_KEY', 'News Data', '📰'),
        ('POLYGON_API_KEY', 'Options Data (Polygon.io)', '📊'),
        ('OPENAI_API_KEY', 'OpenAI (Optional)', '🔮')
    ]

    for key_name, description, icon in api_keys:
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            st.markdown(f"{icon} **{description}**")

        with col2:
            st.code(key_name, language="text")

        with col3:
            # Fix: Use bool() to correctly detect empty strings
            has_key = bool(creds.get(key_name, required=False))
            if has_key:
                st.success("✓ Configured")
            else:
                st.error("✗ Missing")


def _render_fred_api_health() -> None:
    """Render FRED Economic Data API health status and cache metrics."""
    st.subheader("📊 FRED Economic Data API")

    try:
        from capabilities.fred_data import FredDataCapability
        fred = FredDataCapability()
        cache_stats = fred.cache_stats

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_requests = cache_stats['hits'] + cache_stats['misses']
            st.metric(
                "Total Requests",
                total_requests,
                help="Total number of API requests made"
            )

        with col2:
            hit_rate = (
                cache_stats['hits'] / total_requests * 100
                if total_requests > 0
                else 0
            )
            st.metric(
                "Cache Hit Rate",
                f"{hit_rate:.1f}%",
                help="Percentage of requests served from cache"
            )

        with col3:
            st.metric(
                "Cache Hits",
                cache_stats['hits'],
                help="Requests served from cache"
            )

        with col4:
            st.metric(
                "Expired Fallbacks",
                cache_stats.get('expired_fallbacks', 0),
                help="Times stale cache was used due to API unavailability"
            )

        # Cache health indicator
        if hit_rate > 80:
            st.success("✓ Cache performing well - reducing API load")
        elif hit_rate > 50:
            st.info("ℹ️ Moderate cache usage - some fresh API calls")
        else:
            st.warning("⚠️ Low cache usage - most data from API")

    except Exception as e:
        st.info("FRED API capability not available or not initialized")


def _render_polygon_api_health() -> None:
    """Render Polygon Options Data API health status and cache metrics."""
    st.subheader("📊 Polygon Options Data API")

    try:
        from capabilities.polygon_options import PolygonOptionsCapability
        polygon = PolygonOptionsCapability()
        cache_stats = polygon.get_cache_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_requests = cache_stats['total_requests']
            st.metric(
                "Total Requests",
                total_requests,
                help="Total number of Polygon API requests made"
            )

        with col2:
            hit_rate = cache_stats['hit_rate']
            st.metric(
                "Cache Hit Rate",
                f"{hit_rate:.1f}%",
                help="Percentage of requests served from cache (15min TTL)"
            )

        with col3:
            st.metric(
                "Cache Hits",
                cache_stats['cache_hits'],
                help="Requests served from cache"
            )

        with col4:
            st.metric(
                "Expired Fallbacks",
                cache_stats.get('expired_fallbacks', 0),
                help="Times stale cache was used due to API unavailability"
            )

        # API key status
        if polygon.api_key:
            st.success("✓ Polygon API key configured")
            if total_requests > 0:
                st.info(f"ℹ️ {total_requests} requests made - Rate limit: 300 req/min (Starter plan)")
            else:
                st.info("ℹ️ No requests yet - Options features ready to use")
        else:
            st.warning("⚠️ Polygon API key not configured - Options features will show placeholder data")
            st.caption("💡 Add POLYGON_API_KEY to .env to enable options analysis")

    except Exception as e:
        st.info("Polygon API capability not available or not initialized")


def _render_fmp_api_health() -> None:
    """Render Financial Modeling Prep (FMP) Market Data API health status."""
    st.subheader("📈 Market Data API (FMP)")

    try:
        from capabilities.market_data import MarketDataCapability
        market = MarketDataCapability()
        cache_stats = market.get_cache_stats()

        col1, col2, col3 = st.columns(3)

        with col1:
            total_requests = cache_stats['total_requests']
            st.metric(
                "Total Requests",
                total_requests,
                help="Total number of FMP API requests made"
            )

        with col2:
            hit_rate = cache_stats['hit_rate']
            st.metric(
                "Cache Hit Rate",
                f"{hit_rate:.1f}%",
                help="Percentage of requests served from cache"
            )

        with col3:
            st.metric(
                "Cache Hits",
                cache_stats['cache_hits'],
                help="Requests served from cache"
            )

        # API key status
        if market.api_key:
            st.success("✓ FMP API key configured")
        else:
            st.warning("⚠️ FMP API key not configured")

    except Exception as e:
        st.info("Market Data API capability not available or not initialized")


def _render_data_freshness_guidelines() -> None:
    """Render data freshness guidelines for all data sources."""
    st.subheader("📅 Data Freshness Guidelines")
    st.caption("How often different data sources are updated")

    freshness_data: Dict[str, str] = {
        "Economic Indicators (FRED)": "Daily - 24 hour cache",
        "Stock Quotes (FMP)": "15 minutes - market hours",
        "Options Data (Polygon)": "15 minutes - market hours (15min cache)",
        "Company Fundamentals": "Quarterly - earnings cycle",
        "News Data": "Hourly - breaking news",
        "AI Analysis": "On-demand - cached for session",
        "Knowledge Graph": "Persistent - manual updates"
    }

    for data_type, freshness in freshness_data.items():
        col1, col2 = st.columns([2, 3])
        with col1:
            st.markdown(f"**{data_type}**")
        with col2:
            st.caption(freshness)


def _render_actions(tracker) -> None:
    """
    Render action buttons for clearing statistics and refreshing status.

    Args:
        tracker: FallbackTracker instance
    """
    st.subheader("🔧 Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Fallback Statistics", help="Reset fallback event counters"):
            tracker.clear_stats()
            st.success("Fallback statistics cleared")
            st.rerun()

    with col2:
        if st.button("🔄 Refresh API Status", help="Re-check API configuration"):
            st.rerun()


def _render_setup_instructions() -> None:
    """Render API key setup instructions and help documentation."""
    with st.expander("ℹ️ How to Configure API Keys"):
        st.markdown("""
### Setting Up API Keys

1. **Create `.env` file** in the project root:
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys** to `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   FRED_API_KEY=your_fred_key
   FINANCIAL_MODELING_PREP_API_KEY=your_fmp_key
   NEWS_API_KEY=your_news_key
   ```

3. **Restart the application**:
   ```bash
   streamlit run dawsos/main.py
   ```

### Getting API Keys

- **Anthropic Claude**: https://console.anthropic.com/
- **FRED (Economic Data)**: https://fred.stlouisfed.org/docs/api/api_key.html (free)
- **Financial Modeling Prep**: https://financialmodelingprep.com/developer/docs (free tier)
- **News API**: https://newsapi.org/ (free tier)

### Optional Keys

All API keys are **optional**. DawsOS uses cached/fallback data when keys are not configured.
Keys unlock:
- Real-time AI analysis (Anthropic)
- Fresh economic data (FRED)
- Live market quotes (FMP)
- Breaking news (News API)
        """)


def render_api_health_tab() -> None:
    """
    Render API Health & Fallback Monitoring dashboard.

    Main orchestration function that delegates to specialized helper functions
    for each section of the dashboard.
    """
    # Get fallback tracker and stats
    tracker = get_fallback_tracker()
    stats = tracker.get_stats()

    # Render dashboard sections
    _render_dashboard_header()
    _render_fallback_statistics(stats)
    _render_recent_events(stats)
    _render_api_configuration_status()
    _render_fred_api_health()
    _render_polygon_api_health()
    _render_fmp_api_health()
    _render_data_freshness_guidelines()
    _render_actions(tracker)
    _render_setup_instructions()


def render_component_health(component: str, tracker) -> None:
    """
    Render health status for a specific component

    Args:
        component: Component name (e.g., 'llm', 'fred_api')
        tracker: FallbackTracker instance
    """
    stats = tracker.get_component_stats(component)

    st.markdown(f"### {component}")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Events", stats['total_events'])

    with col2:
        reasons = stats.get('reasons', {})
        if reasons:
            most_common = max(reasons.items(), key=lambda x: x[1])
            st.markdown(f"**Most Common**: {most_common[0]} ({most_common[1]} times)")

    if stats['recent_events']:
        with st.expander("Recent Events"):
            for event in stats['recent_events'][-5:]:
                st.json(event)
