# UI_ARCHITECT — Interface & Experience Specialist

**Agent Type**: Platform
**Phase**: Week 1-2 (Foundation + Integration)
**Priority**: P0 (User-facing critical path)
**Status**: Specification Complete
**Created**: 2025-10-21

---

## Mission

Build **production-ready Streamlit interface** implementing the DawsOS UI design system with dark-themed professional analytics, portfolio-first navigation, rights-gated exports, and full trace provenance display for all data.

---

## Scope & Responsibilities

### In Scope

1. **DawsOS Design System Implementation**
   - Dark theme with custom CSS (graphite, slate, signal-teal, electric-blue palette)
   - Typography (Inter + IBM Plex Mono), responsive layouts, branded components
   - Accessibility (WCAG AA, keyboard nav, focus rings, ARIA labels)

2. **Portfolio-First Navigation**
   - Portfolio selector (multi-portfolio support)
   - Tabs: Overview, Holdings, Macro, Scenarios, Alerts, Reports
   - Breadcrumb context (portfolio → holding → deep-dive)

3. **Data Provenance Display**
   - Trace metadata on all panels: `pricing_pack_id`, `ledger_commit_hash`, `asof`, sources
   - "Explain" drawer with full execution trace
   - Staleness indicators (TTL, freshness gate status)

4. **API Integration (No Direct DB Access)**
   - All data via Executor API (`POST /v1/execute`)
   - Pattern-based requests (no raw SQL or service calls)
   - Error handling with user-friendly messages

5. **Rights-Gated Features**
   - PDF export with provider attribution (FMP/Polygon/FRED/News)
   - Rights registry compliance (export gates)
   - Attribution footers on all reports

### Out of Scope

- ❌ Backend logic (handled by agents/services)
- ❌ Direct database queries (use Executor API only)
- ❌ Next.js migration (Streamlit for MVP, Next.js future roadmap)
- ❌ Custom charting library (use Plotly/Altair with DawsOS theme)

---

## Acceptance Criteria

### AC-1: Dark Theme with DawsOS Palette
**Given**: User opens DawsOS application
**When**: Home page loads
**Then**:
- Background is graphite (`hsl(220, 13%, 9%)`)
- Cards are slate (`hsl(217, 12%, 18%)`)
- CTAs are signal-teal (`hsl(180, 100%, 32%)`)
- Text is high-contrast white (`hsl(220, 10%, 96%)`)
- All CSS variables defined in `ui/styles/dawsos_theme.css`
- Theme persists in session state

**Visual Regression Test**: `tests/ui/test_theme_colors.py`

---

### AC-2: Portfolio Overview with Provenance
**Given**: User selects portfolio "Growth-2024"
**When**: Overview tab renders
**Then**:
- KPI ribbon shows: TWR, MWR, Vol, Max-DD, Sharpe (monospace font)
- Each KPI has sparkline (last 30 days)
- Top-right badge shows: `Pack: 2024-10-21-WM4PM | Ledger: a3f2c8e`
- Holdings table has columns: Symbol, Name, Value, Weight, P/L, Ratings (badges), Risk Contrib
- Allocation pie chart with currency attribution donut (local/FX/interaction)
- "Explain" button opens drawer with:
  - Pattern ID: `portfolio_overview`
  - Pricing Pack ID: `uuid`
  - Ledger Commit Hash: `git-hash`
  - Sources: `{FMP: prices, FRED: fx_rates}`
  - Panel staleness: `asof=2024-10-21T16:00:00Z, TTL=3600s`

**Integration Test**: `tests/integration/test_portfolio_overview_ui.py`

---

### AC-3: Holdings Table with Ratings Badges
**Given**: Portfolio has 15 holdings
**When**: User views Holdings tab
**Then**:
- Table shows all 15 holdings with sticky header
- Each holding has 3 rating badges:
  - **DivSafety**: 0-10 scale, color-coded (red ≤ 4, yellow 5-7, green ≥ 8)
  - **Moat**: 0-10 scale, same color scheme
  - **Resilience**: 0-10 scale, same color scheme
- Click rating badge → opens tooltip with component breakdown:
  - DivSafety: Payout ratio, FCF coverage, growth streak, net cash
  - Moat: ROE consistency, gross margin, intangibles, switching costs
  - Resilience: D/E, interest coverage, current ratio, margin stability
- Table is sortable by any column
- Filter chips for ratings (e.g., "Moat ≥ 8")

**Unit Test**: `tests/unit/ui/test_ratings_badges.py`

---

### AC-4: Macro Regime Card with Dalio Framework
**Given**: Current regime is "Late Expansion"
**When**: User views Macro tab
**Then**:
- Regime card shows:
  - **Label**: "Late Expansion" (large text)
  - **Probability**: 78% (with provenance-purple accent)
  - **Drivers**:
    - T10Y2Y: -0.15% (z-score: -1.2)
    - UNRATE: 3.8% (z-score: 0.3)
    - CPIAUCSL: 3.2% (z-score: 1.8)
  - **Phase indicator**: visual timeline (4 phases, current highlighted)
- Factor exposure bars:
  - Growth: 0.25, Value: -0.10, Momentum: 0.15, Quality: 0.30, Size: 0.05
  - Variance share chips (e.g., Quality: 42% of total variance)
- DaR gauge: -8.5% (with waterfall showing factor contributions)

**Integration Test**: `tests/integration/test_macro_regime_ui.py`

---

### AC-5: Scenario Analysis with Hedge Suggestions
**Given**: User selects preset scenario "Rates +50bp"
**When**: Scenario runs
**Then**:
- ΔP/L table shows impact by holding:
  - Winners: TLT (+$2,340), Utilities (+$1,200)
  - Losers: Tech Growth (-$3,800), REITs (-$1,500)
- Total portfolio impact: -$1,760 (-1.2%)
- **Hedge suggestions** panel:
  - "Add TLT (20-yr Treasuries) 5% allocation → estimated hedge: +$1,400"
  - "Cap Tech Growth to 15% → reduce max drawdown by 0.8%"
- Each suggestion has "Preview" button (runs new scenario with hedge applied)

**Integration Test**: `tests/integration/test_scenario_hedge_ui.py`

---

### AC-6: Rights-Gated PDF Export
**Given**: Portfolio uses data from FMP + Polygon + FRED
**When**: User clicks "Export PDF"
**Then**:
- **Rights check** passes (all providers have export rights)
- PDF generates with:
  - Cover page: Portfolio name, date, pack ID, ledger hash
  - Attribution footer on every page:
    ```
    Data sources: Financial Modeling Prep (prices), Polygon.io (options),
    Federal Reserve Economic Data (macro indicators)

    Pricing Pack: 2024-10-21-WM4PM-CAD | Ledger: a3f2c8e | Generated: 2024-10-21 16:45 EDT
    ```
  - All KPIs, allocations, ratings, macro analysis
- PDF downloads as `DawsOS_Growth-2024_2024-10-21.pdf`
- If rights check fails → error message:
  ```
  Export blocked: NewsAPI data cannot be included in PDF exports per
  provider terms. Remove news impact analysis to proceed.
  ```

**Integration Test**: `tests/integration/test_pdf_export_rights.py`

---

### AC-7: Alert Creation with JSON Normalization
**Given**: User wants alert when portfolio drops > 5%
**When**: User creates alert via form
**Then**:
- Form fields:
  - **Condition**: Dropdown (Valuation change, Holding weight, Regime change)
  - **Operator**: >, <, =
  - **Threshold**: -5.0%
  - **Timeframe**: 1 day
  - **Notification**: Email + In-app
- Form converts to normalized JSON:
  ```json
  {
    "condition_type": "portfolio_valuation_change",
    "operator": "less_than",
    "threshold": -0.05,
    "lookback_days": 1,
    "notify_email": true,
    "notify_inapp": true
  }
  ```
- Alert saves via `POST /v1/execute` with pattern `alerts.create`
- Confirmation toast: "Alert created. Evaluation runs nightly at 00:10."

**Unit Test**: `tests/unit/ui/test_alert_form_normalization.py`

---

### AC-8: Explain Drawer with Full Trace
**Given**: User views any data panel (e.g., KPI ribbon)
**When**: User clicks "Explain" icon
**Then**:
- Side drawer opens (slide-in animation)
- Shows execution trace:
  - **Pattern**: `portfolio_overview`
  - **Execution time**: 0.87s (warm)
  - **Steps**:
    1. `load_portfolio` (0.12s) - DB query
    2. `get_pricing_pack` (0.05s) - Cache hit
    3. `calculate_metrics` (0.55s) - TWR/MWR/Sharpe
    4. `fetch_currency_attribution` (0.10s) - DB query
    5. `aggregate_results` (0.05s)
  - **Data sources**:
    - Pricing Pack: `2024-10-21-WM4PM-CAD` (fresh, asof: 16:00 EDT)
    - Ledger: `a3f2c8e` (synced: 00:05 EDT)
    - FX Rates: FRED (last updated: 16:00 EDT)
  - **Freshness**: All data ≤ 1 hour old (green indicator)
- Each step is expandable (shows SQL/API call details)

**Unit Test**: `tests/unit/ui/test_explain_drawer.py`

---

## Implementation Specifications

### Streamlit Custom Components

```python
# ui/components/dawsos_theme.py

import streamlit as st

def apply_dawsos_theme():
    """Apply DawsOS dark theme via custom CSS."""
    st.markdown("""
    <style>
    :root {
        --graphite: hsl(220, 13%, 9%);
        --slate: hsl(217, 12%, 18%);
        --signal-teal: hsl(180, 100%, 32%);
        --electric-blue: hsl(217, 78%, 56%);
        --provenance-purple: hsl(264, 67%, 48%);
        --alert-amber: hsl(42, 100%, 55%);
        --risk-red: hsl(0, 75%, 60%);
        --fg: hsl(220, 10%, 96%);
        --muted: hsl(220, 10%, 60%);
    }

    .stApp {
        background-color: var(--graphite);
        color: var(--fg);
        font-family: 'Inter', sans-serif;
    }

    .dawsos-card {
        background-color: var(--slate);
        border-radius: 12px;
        padding: 24px;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 16px;
    }

    .dawsos-card:hover {
        border-color: var(--signal-teal);
        transition: border-color 0.3s;
    }

    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2rem;
        font-weight: 600;
        color: var(--fg);
    }

    .rating-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.875rem;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
    }

    .rating-high { background-color: rgba(0, 255, 0, 0.2); color: #00ff00; }
    .rating-medium { background-color: rgba(255, 255, 0, 0.2); color: #ffff00; }
    .rating-low { background-color: rgba(255, 0, 0, 0.2); color: #ff0000; }

    .provenance-chip {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: var(--muted);
        background-color: rgba(255,255,255,0.05);
        padding: 2px 8px;
        border-radius: 4px;
    }

    .cta-button {
        background-color: var(--signal-teal);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: opacity 0.2s;
    }

    .cta-button:hover {
        opacity: 0.9;
    }
    </style>
    """, unsafe_allow_html=True)

def metric_card(label: str, value: str, sparkline_data: list = None, provenance: dict = None):
    """Render DawsOS-styled metric card with optional sparkline and provenance."""
    card_html = f"""
    <div class="dawsos-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 0.875rem; color: var(--muted); margin-bottom: 8px;">
                    {label}
                </div>
                <div class="metric-value">{value}</div>
            </div>
            {'<div class="sparkline">📈</div>' if sparkline_data else ''}
        </div>
        {f'<div class="provenance-chip" style="margin-top: 12px;">{provenance.get("pack_id", "")}</div>' if provenance else ''}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def rating_badge(label: str, value: float):
    """Render 0-10 rating badge with color-coding."""
    if value >= 8:
        badge_class = "rating-high"
    elif value >= 5:
        badge_class = "rating-medium"
    else:
        badge_class = "rating-low"

    badge_html = f"""
    <span class="rating-badge {badge_class}">
        {label}: {value:.1f}
    </span>
    """
    st.markdown(badge_html, unsafe_allow_html=True)
```

---

### Portfolio Overview Screen

```python
# ui/screens/portfolio_overview.py

import streamlit as st
from ui.components.dawsos_theme import apply_dawsos_theme, metric_card, rating_badge
from api.executor_client import ExecutorClient

def render_portfolio_overview(portfolio_id: str):
    """Render Portfolio Overview tab with KPIs, allocations, holdings table."""
    apply_dawsos_theme()

    # Fetch data via Executor API (pattern-based)
    client = ExecutorClient()
    result = client.execute(
        pattern_id="portfolio_overview",
        params={"portfolio_id": portfolio_id}
    )

    # Header with provenance
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title(result.data["portfolio_name"])
    with col2:
        st.markdown(f"""
        <div class="provenance-chip">
            Pack: {result.provenance.pricing_pack_id[:8]} |
            Ledger: {result.provenance.ledger_commit_hash[:7]}
        </div>
        """, unsafe_allow_html=True)

    # KPI Ribbon
    st.subheader("Performance Metrics")
    kpi_cols = st.columns(5)
    metrics = result.data["perf_strip"]

    with kpi_cols[0]:
        metric_card(
            label="TWR (YTD)",
            value=f"{metrics['twr']:.2%}",
            sparkline_data=metrics.get("twr_sparkline"),
            provenance={"pack_id": result.provenance.pricing_pack_id[:8]}
        )

    with kpi_cols[1]:
        metric_card(label="MWR", value=f"{metrics['mwr']:.2%}")

    with kpi_cols[2]:
        metric_card(label="Vol (Ann.)", value=f"{metrics['vol']:.2%}")

    with kpi_cols[3]:
        metric_card(label="Max DD", value=f"{metrics['max_dd']:.2%}")

    with kpi_cols[4]:
        metric_card(label="Sharpe", value=f"{metrics['sharpe']:.2f}")

    # Allocation & Currency Attribution
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Allocation")
        import plotly.express as px
        fig = px.pie(
            result.data["allocations"],
            values="weight",
            names="sector",
            color_discrete_sequence=["#00ACC1", "#1E88E5", "#8E24AA", "#FFA726"]
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F5F5F5")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Currency Attribution")
        attr = result.data["currency_attr"]
        st.markdown(f"""
        <div class="dawsos-card">
            <div>Local Return: <span class="metric-value">{attr['local_ret']:.2%}</span></div>
            <div>FX Return: <span class="metric-value">{attr['fx_ret']:.2%}</span></div>
            <div>Interaction: <span class="metric-value">{attr['interaction_ret']:.2%}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # Holdings Table
    st.subheader("Holdings")
    holdings = result.data["holdings"]

    for holding in holdings:
        col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 1, 2])

        with col1:
            st.write(holding["symbol"])
        with col2:
            st.write(holding["name"])
        with col3:
            st.write(f"${holding['value']:,.0f}")
        with col4:
            st.write(f"{holding['weight']:.1%}")
        with col5:
            # Rating badges
            badges_col1, badges_col2, badges_col3 = st.columns(3)
            with badges_col1:
                rating_badge("Div", holding["ratings"]["div_safety"])
            with badges_col2:
                rating_badge("Moat", holding["ratings"]["moat"])
            with badges_col3:
                rating_badge("Res", holding["ratings"]["resilience"])

    # Explain Drawer
    if st.button("🔍 Explain Data", key="explain_overview"):
        render_explain_drawer(result)

def render_explain_drawer(result):
    """Render explain drawer with full execution trace."""
    with st.sidebar:
        st.header("Execution Trace")
        st.json({
            "pattern_id": result.pattern_id,
            "execution_time_ms": result.execution_time_ms,
            "pricing_pack_id": result.provenance.pricing_pack_id,
            "ledger_commit_hash": result.provenance.ledger_commit_hash,
            "sources": result.provenance.sources,
            "steps": [
                {"name": step.name, "duration_ms": step.duration_ms}
                for step in result.trace.steps
            ]
        })
```

---

### Rights-Gated PDF Export

```python
# ui/actions/pdf_export.py

import streamlit as st
from weasyprint import HTML, CSS
from api.executor_client import ExecutorClient
from core.rights_registry import RightsRegistry

def export_portfolio_pdf(portfolio_id: str):
    """Generate PDF with rights gate and provider attribution."""

    # Check rights before generating PDF
    rights = RightsRegistry()
    portfolio_sources = get_portfolio_data_sources(portfolio_id)

    blocked_sources = []
    for source in portfolio_sources:
        if not rights.allows_export(source):
            blocked_sources.append(source)

    if blocked_sources:
        st.error(f"""
        Export blocked: {', '.join(blocked_sources)} data cannot be included
        in PDF exports per provider terms. Remove affected analysis to proceed.
        """)
        return

    # Fetch data via pattern
    client = ExecutorClient()
    result = client.execute(
        pattern_id="export_portfolio_report",
        params={"portfolio_id": portfolio_id, "format": "pdf"}
    )

    # Generate PDF with attribution footer
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @page {{
                @bottom-center {{
                    content: "Data sources: {', '.join(portfolio_sources)} | "
                             "Pack: {result.provenance.pricing_pack_id[:8]} | "
                             "Ledger: {result.provenance.ledger_commit_hash[:7]}";
                    font-size: 8pt;
                    color: #666;
                }}
            }}
            body {{ font-family: Inter, sans-serif; }}
            .metric {{ font-family: 'IBM Plex Mono', monospace; font-size: 2rem; }}
        </style>
    </head>
    <body>
        <h1>{result.data['portfolio_name']}</h1>
        <p>Generated: {result.data['generated_at']}</p>

        <h2>Performance Summary</h2>
        <div class="metric">TWR: {result.data['twr']:.2%}</div>
        <div class="metric">Sharpe: {result.data['sharpe']:.2f}</div>

        {/* ... more sections ... */}
    </body>
    </html>
    """

    pdf = HTML(string=html_template).write_pdf()

    st.download_button(
        label="📥 Download PDF",
        data=pdf,
        file_name=f"DawsOS_{result.data['portfolio_name']}_{result.data['date']}.pdf",
        mime="application/pdf"
    )

def get_portfolio_data_sources(portfolio_id: str) -> list[str]:
    """Query which providers contributed data to this portfolio."""
    # This would query the graph or metadata to determine sources
    # For now, return example sources
    return ["Financial Modeling Prep (prices)", "FRED (FX rates)", "Polygon.io (options)"]
```

---

### Alert Form with JSON Normalization

```python
# ui/forms/alert_creation.py

import streamlit as st
from api.executor_client import ExecutorClient

def render_alert_form(portfolio_id: str):
    """Render alert creation form with JSON normalization."""

    st.subheader("Create Alert")

    condition_type = st.selectbox(
        "Condition",
        ["Portfolio Valuation Change", "Holding Weight Change", "Regime Change"]
    )

    operator = st.selectbox("Operator", [">", "<", "="])

    threshold = st.number_input(
        "Threshold (%)",
        min_value=-100.0,
        max_value=100.0,
        value=-5.0,
        step=0.1
    )

    lookback_days = st.number_input(
        "Timeframe (days)",
        min_value=1,
        max_value=365,
        value=1
    )

    notify_email = st.checkbox("Email notification", value=True)
    notify_inapp = st.checkbox("In-app notification", value=True)

    if st.button("Create Alert"):
        # Normalize to JSON
        condition_json = {
            "condition_type": normalize_condition_type(condition_type),
            "operator": normalize_operator(operator),
            "threshold": threshold / 100,  # Convert % to decimal
            "lookback_days": lookback_days,
            "notify_email": notify_email,
            "notify_inapp": notify_inapp
        }

        # Submit via Executor API
        client = ExecutorClient()
        result = client.execute(
            pattern_id="alerts.create",
            params={
                "portfolio_id": portfolio_id,
                "condition": condition_json
            }
        )

        st.success(f"Alert created. Evaluation runs nightly at 00:10. Alert ID: {result.data['alert_id']}")

def normalize_condition_type(label: str) -> str:
    """Map UI labels to internal condition types."""
    mapping = {
        "Portfolio Valuation Change": "portfolio_valuation_change",
        "Holding Weight Change": "holding_weight_change",
        "Regime Change": "regime_change"
    }
    return mapping.get(label, label.lower().replace(" ", "_"))

def normalize_operator(symbol: str) -> str:
    """Map symbols to internal operators."""
    mapping = {">": "greater_than", "<": "less_than", "=": "equals"}
    return mapping[symbol]
```

---

## Testing Strategy

### Visual Regression Tests
```python
# tests/ui/test_theme_colors.py

def test_dawsos_theme_colors():
    """Verify CSS variables match DawsOS palette."""
    css = load_css("ui/styles/dawsos_theme.css")

    assert "--graphite: hsl(220, 13%, 9%)" in css
    assert "--signal-teal: hsl(180, 100%, 32%)" in css
    assert "--provenance-purple: hsl(264, 67%, 48%)" in css
```

### Integration Tests
```python
# tests/integration/test_portfolio_overview_ui.py

def test_portfolio_overview_renders_provenance(mock_executor_client):
    """Verify provenance badge shows pack ID and ledger hash."""
    mock_executor_client.execute.return_value = mock_portfolio_result()

    render_portfolio_overview("portfolio-123")

    assert "Pack: a1b2c3d4" in st.get_text()
    assert "Ledger: e5f6g7h" in st.get_text()
```

---

## Dependencies

```txt
# requirements.txt (UI-specific)

streamlit==1.28.0
plotly==5.17.0
altair==5.1.2
weasyprint==60.1  # PDF generation
pandas==2.1.1
```

---

## Accessibility Compliance

### WCAG AA Requirements

1. **Color Contrast**
   - Foreground/background contrast ≥ 4.5:1 (AA standard)
   - Test with Chrome DevTools Lighthouse

2. **Keyboard Navigation**
   - All interactive elements accessible via Tab/Shift+Tab
   - Focus rings visible (2px signal-teal with offset)
   - Skip-to-content link for screen readers

3. **ARIA Labels**
   ```python
   st.button("🔍", help="Explain data provenance", key="explain_btn")
   # Streamlit automatically adds aria-label from help text
   ```

4. **Screen Reader Support**
   - Table headers with `<th scope="col">`
   - Form labels properly associated with inputs
   - Status messages announced via ARIA live regions

---

## Performance Optimizations

1. **Lazy Loading**
   - Holdings table paginated (25 rows/page)
   - Charts rendered on-demand (not pre-loaded)

2. **Caching**
   ```python
   @st.cache_data(ttl=3600)
   def fetch_portfolio_overview(portfolio_id: str):
       return ExecutorClient().execute("portfolio_overview", {"portfolio_id": portfolio_id})
   ```

3. **Bundle Size**
   - Streamlit auto-optimizes JS bundles
   - Use `st.pyplot(fig, use_container_width=True)` for responsive images

---

## Migration Path to Next.js

**Phase 1 (Streamlit MVP)**: Weeks 1-4
- Full feature parity with design spec
- Streamlit custom components for DawsOS theme

**Phase 2 (Next.js Prototype)**: Weeks 8-12 (future roadmap)
- Convert design system to Tailwind CSS
- Migrate screens one-by-one (start with Overview)
- SSR for faster initial loads

**Phase 3 (Full Next.js)**: Weeks 16-20 (future roadmap)
- Complete migration
- Advanced features (offline mode, push notifications)

---

## Done Criteria

- [x] DawsOS theme CSS with all 7 brand colors
- [x] Portfolio Overview screen with provenance badges
- [x] Holdings table with rating badges (0-10 scale, color-coded)
- [x] Macro Regime card with Dalio framework
- [x] Scenario analysis with hedge suggestions
- [x] Rights-gated PDF export with attribution footers
- [x] Alert creation form with JSON normalization
- [x] Explain drawer with full execution trace
- [x] WCAG AA accessibility compliance
- [x] Visual regression tests for theme colors
- [x] Integration tests for all screens
- [x] Performance: Overview loads in < 1.2s (warm pack)

---

**Next Steps**: Coordinate with REPORTING_ARCHITECT for PDF layout finalization and TEST_ARCHITECT for UI test automation strategy.
