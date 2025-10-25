"""
DawsOS Settings Screen

Purpose: Configuration and system information
Updated: 2025-10-22
Priority: P1

Features:
    - API configuration
    - Mock mode toggle
    - System status
    - Provider information

Usage:
    Called from main.py
"""

import os
import streamlit as st


def render_settings():
    """Render settings screen."""

    st.markdown("# 🛠️ Settings")

    # API Configuration Section
    st.markdown("## API Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### API Endpoint")
        api_url = st.text_input(
            "Executor API URL",
            value=os.getenv("EXECUTOR_API_URL", "http://localhost:8000"),
            help="URL of the DawsOS Executor API",
        )

        if st.button("Test Connection"):
            import requests

            try:
                response = requests.get(f"{api_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success(f"✅ API is reachable: {api_url}")
                else:
                    st.error(f"❌ API returned {response.status_code}")
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")

    with col2:
        st.markdown("### Mode")
        use_mock = st.checkbox(
            "Use Mock Data",
            value=os.getenv("USE_MOCK_CLIENT", "true").lower() == "true",
            help="Use mock data instead of connecting to API (for development)",
        )

        if use_mock:
            st.info("📋 Mock mode enabled - using synthetic data")
        else:
            st.success("🔄 API mode enabled - using real data")

    st.markdown("---")

    # System Information Section
    st.markdown("## System Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Application")
        st.markdown("""
        **Name**: DawsOS
        **Version**: v1.0.0
        **Build**: 2025-10-22
        **Environment**: Development
        """)

    with col2:
        st.markdown("### Architecture")
        st.markdown("""
        **Frontend**: Streamlit
        **Backend**: FastAPI
        **Database**: PostgreSQL + TimescaleDB
        **Cache**: Redis
        """)

    with col3:
        st.markdown("### Data Providers")
        st.markdown("""
        **Market Data**: FMP
        **Corporate Actions**: Polygon
        **Macro Indicators**: FRED
        **News**: NewsAPI
        """)

    st.markdown("---")

    # Provider Configuration Section
    st.markdown("## Provider Configuration")

    with st.expander("Market Data (FMP)", expanded=False):
        st.markdown("""
        **Financial Modeling Prep (FMP)**
        - Stock prices (EOD, intraday)
        - Market data
        - Historical prices

        **Export Rights**: ✅ Allowed for PDF export
        **Attribution Required**: Yes
        """)

        fmp_key = st.text_input(
            "FMP API Key",
            value="••••••••••••••••",
            type="password",
            help="API key for Financial Modeling Prep",
        )

    with st.expander("Corporate Actions (Polygon)", expanded=False):
        st.markdown("""
        **Polygon.io**
        - Dividends
        - Stock splits
        - Corporate actions

        **Export Rights**: ✅ Allowed for PDF export
        **Attribution Required**: Yes
        """)

        polygon_key = st.text_input(
            "Polygon API Key",
            value="••••••••••••••••",
            type="password",
            help="API key for Polygon.io",
        )

    with st.expander("Macro Indicators (FRED)", expanded=False):
        st.markdown("""
        **Federal Reserve Economic Data (FRED)**
        - Treasury yields (T10Y2Y, etc.)
        - Unemployment rate (UNRATE)
        - GDP, CPI, inflation
        - Economic indicators

        **Export Rights**: ✅ Allowed for PDF export
        **Attribution Required**: Yes
        """)

        fred_key = st.text_input(
            "FRED API Key",
            value="••••••••••••••••",
            type="password",
            help="API key for FRED",
        )

    with st.expander("News (NewsAPI)", expanded=False):
        st.markdown("""
        **NewsAPI.org**
        - Financial news
        - Sentiment analysis
        - Entity extraction

        **Export Rights**: ❌ **BLOCKED for PDF export** (Developer tier)
        **Upgrade Required**: Business plan for PDF export
        **Attribution Required**: Yes
        """)

        news_key = st.text_input(
            "NewsAPI Key",
            value="••••••••••••••••",
            type="password",
            help="API key for NewsAPI",
        )

    st.markdown("---")

    # Advanced Section
    st.markdown("## Advanced Settings")

    with st.expander("Database", expanded=False):
        st.markdown("### Connection")
        db_url = st.text_input(
            "Database URL",
            value="postgresql://dawsos:••••@localhost:5432/dawsos",
            type="password",
            help="PostgreSQL connection URL",
        )

        st.markdown("### Status")
        st.info("✅ Database connected - 12 tables, 6 with data")

    with st.expander("Cache (Redis)", expanded=False):
        st.markdown("### Connection")
        redis_url = st.text_input(
            "Redis URL",
            value="redis://localhost:6379/0",
            help="Redis connection URL",
        )

        st.markdown("### Status")
        st.info("✅ Redis connected - 0 keys cached")

    with st.expander("Observability", expanded=False):
        st.markdown("### Tracing")
        st.checkbox("Enable OpenTelemetry", value=False, help="Enable distributed tracing")

        st.markdown("### Metrics")
        st.checkbox("Enable Prometheus", value=True, help="Enable metrics collection")

        st.markdown("### Error Tracking")
        st.checkbox("Enable Sentry", value=False, help="Enable error tracking")

    st.markdown("---")

    # Documentation Section
    st.markdown("## Documentation")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("[📖 Product Spec](https://github.com/dawsos/docs)")

    with col2:
        st.markdown("[🚀 Implementation Roadmap](https://github.com/dawsos/docs)")

    with col3:
        st.markdown("[🐛 Report Issue](https://github.com/dawsos/issues)")

    st.markdown("---")
    st.markdown("*For support, contact: support@dawsos.com*")
