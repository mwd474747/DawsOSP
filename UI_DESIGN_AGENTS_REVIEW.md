# UI & Design Agents - Configuration Review

**Review Date**: October 28, 2025
**Reviewed By**: Claude (Sonnet 4.5)
**Status**: 📋 Analysis Complete

---

## Executive Summary

DawsOS has **3 agents** related to UI, design, and user-facing reports:

1. **UI_ARCHITECT** (Deleted/Archived) - Streamlit interface specialist
2. **REPORTS_AGENT** (Active) - PDF/CSV export generation
3. **REPORTING_ARCHITECT** (Active) - PDF export & rights compliance specialist

**Key Finding**: The UI_ARCHITECT agent was **deleted** from active agents and moved to archive. This suggests the UI/design work may have been completed, deprioritized, or is being handled differently than originally planned.

---

## Agent 1: UI_ARCHITECT (ARCHIVED)

**Status**: 🗑️ **DELETED** - Found in `.claude/agents/archive/UI_ARCHITECT.md`
**File Location**: Previously at `.claude/agents/archive/UI_ARCHITECT.md`
**Priority**: P0 (User-facing critical path)
**Phase**: Week 1-2 (Foundation + Integration)

### Mission

Build **production-ready Streamlit interface** implementing the DawsOS UI design system with dark-themed professional analytics, portfolio-first navigation, rights-gated exports, and full trace provenance display for all data.

### Key Responsibilities

#### 1. DawsOS Design System
- **Dark Theme**: Graphite, slate, signal-teal, electric-blue palette
- **Typography**: Inter (UI) + IBM Plex Mono (metrics)
- **Accessibility**: WCAG AA compliance
- **Custom CSS Variables**:
  ```css
  --graphite: hsl(220, 13%, 9%)
  --slate: hsl(217, 12%, 18%)
  --signal-teal: hsl(180, 100%, 32%)
  --electric-blue: hsl(212, 100%, 58%)
  --provenance-purple: hsl(264, 67%, 48%)
  --high-contrast-white: hsl(220, 10%, 96%)
  ```

#### 2. Portfolio-First Navigation
- Multi-portfolio selector
- Tab structure:
  - Overview (KPIs, allocations, holdings)
  - Holdings (detailed table with ratings)
  - Macro (regime, factors, DaR)
  - Scenarios (stress testing, hedge suggestions)
  - Alerts (creation, management)
  - Reports (PDF/CSV exports)
- Breadcrumb context (portfolio → holding → deep-dive)

#### 3. Data Provenance Display
- **Every panel shows**:
  - `pricing_pack_id` (first 8 chars)
  - `ledger_commit_hash` (first 7 chars)
  - `asof` timestamp
  - Data sources (FMP, Polygon, FRED, NewsAPI)
- **"Explain" drawer** with full execution trace:
  - Pattern ID
  - Execution time (ms)
  - Step-by-step breakdown
  - Source attribution

#### 4. Key UI Components

**KPI Ribbon**:
```python
metrics = {
    "TWR (YTD)": "8.45%",
    "MWR": "7.82%",
    "Vol (Ann.)": "14.3%",
    "Max DD": "-8.2%",
    "Sharpe": "1.24"
}
```
- Monospace font (IBM Plex Mono)
- Sparklines (last 30 days)
- Provenance badge (top-right)

**Holdings Table**:
- Columns: Symbol, Name, Value, Weight, P/L, Ratings, Risk Contrib
- **Rating Badges** (0-10 scale):
  - DivSafety (D): Red ≤ 4, Yellow 5-7, Green ≥ 8
  - Moat (M): Same color scheme
  - Resilience (R): Same color scheme
- Click badge → tooltip with component breakdown
- Sortable, filterable

**Macro Regime Card**:
- Current regime label (e.g., "Late Expansion")
- Probability (e.g., 78%)
- Drivers (T10Y2Y, UNRATE, CPIAUCSL with z-scores)
- Visual phase timeline (4 phases)
- Factor exposure bars
- DaR gauge with waterfall

**Scenario Analysis**:
- ΔP/L table by holding
- Total portfolio impact
- **Hedge suggestions panel**:
  - Suggested hedges (e.g., "Add TLT 5% allocation")
  - Estimated impact
  - "Preview" button (runs scenario with hedge)

#### 5. Rights-Gated PDF Export

**Pre-export Rights Check**:
```python
sources = trace_providers(portfolio_data)  # ["FMP", "Polygon", "NewsAPI"]

for source in sources:
    if not rights.allows_export(source):
        raise ExportBlockedError(f"{source} data cannot be exported")
```

**If Export Allowed**:
- Generate PDF with WeasyPrint
- Attribution footer on every page
- Includes: pricing_pack_id, ledger_commit_hash, generated timestamp
- Downloads as `DawsOS_Growth-2024_2024-10-21.pdf`

**If Export Blocked**:
```
Export blocked: NewsAPI data cannot be included in PDF exports per
provider terms. Remove news impact analysis to proceed.
```

#### 6. Alert Creation

**Form Fields**:
- Condition type (dropdown)
- Operator (>, <, =)
- Threshold (%)
- Timeframe (days)
- Notification preferences (email, in-app)

**JSON Normalization**:
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

### Acceptance Criteria (7 ACs)

1. ✅ **AC-1**: Dark theme with DawsOS palette
2. ✅ **AC-2**: Portfolio overview with provenance
3. ✅ **AC-3**: Holdings table with ratings badges
4. ✅ **AC-4**: Macro regime card with Dalio framework
5. ✅ **AC-5**: Scenario analysis with hedge suggestions
6. ✅ **AC-6**: Rights-gated PDF export
7. ✅ **AC-7**: Alert creation with JSON normalization

### Technical Implementation

**API Integration**:
- All data via Executor API (`POST /v1/execute`)
- Pattern-based requests (no direct DB access)
- Example:
  ```python
  client = ExecutorClient()
  result = client.execute(
      pattern_id="portfolio_overview",
      params={"portfolio_id": portfolio_id}
  )
  ```

**Caching**:
```python
@st.cache_data(ttl=3600)
def fetch_portfolio_overview(portfolio_id: str):
    return ExecutorClient().execute("portfolio_overview", {"portfolio_id": portfolio_id})
```

**Accessibility**:
- WCAG AA compliance (color contrast ≥ 4.5:1)
- Keyboard navigation (Tab/Shift+Tab)
- Focus rings (2px signal-teal)
- ARIA labels on all interactive elements
- Screen reader support

### Testing Strategy

**Visual Regression**:
```python
def test_dawsos_theme_colors():
    css = load_css("ui/styles/dawsos_theme.css")
    assert "--graphite: hsl(220, 13%, 9%)" in css
    assert "--signal-teal: hsl(180, 100%, 32%)" in css
```

**Integration**:
```python
def test_portfolio_overview_renders_provenance(mock_executor_client):
    render_portfolio_overview("portfolio-123")
    assert "Pack: a1b2c3d4" in st.get_text()
    assert "Ledger: e5f6g7h" in st.get_text()
```

### Migration Path

**Phase 1 (Streamlit MVP)**: Weeks 1-4
- Full feature parity
- Streamlit custom components

**Phase 2 (Next.js Prototype)**: Weeks 8-12 (future)
- Tailwind CSS
- SSR for faster loads

**Phase 3 (Full Next.js)**: Weeks 16-20 (future)
- Complete migration
- Offline mode, push notifications

### Done Criteria

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

### Why Was This Archived?

**Possible Reasons**:
1. ✅ **Work Complete**: UI implementation finished, agent no longer needed
2. 📦 **Consolidated**: Merged with ORCHESTRATOR or another agent
3. 🎯 **Deprioritized**: Streamlit UI deferred in favor of API-first approach
4. 🔄 **Replaced**: Next.js migration started, Streamlit deprecated

**Evidence**:
- `frontend/` directory exists in repository
- Streamlit listed in `frontend/requirements.txt` (19 packages)
- Git status shows recent work on UI files

**Most Likely**: Work is **complete** and agent was archived after implementation finished.

---

## Agent 2: REPORTS_AGENT (ACTIVE)

**Status**: ✅ **ACTIVE**
**File Location**: `.claude/agents/REPORTS_AGENT.md`
**Priority**: P1
**Implementation Status**: ⚠️ Partial (Service Ready, Agent Implemented)

### Mission

Generate professional PDF and CSV exports of portfolio analysis with rights enforcement, watermarks, and attribution footers. Ensure compliance with data usage policies while providing high-quality reports.

### Current Capabilities

#### ✅ Implemented but Not Fully Integrated

1. **PDF Generation**
   - `reports.render_pdf` - Generate PDF reports with WeasyPrint
   - `reports.export_csv` - Generate CSV exports
   - `reports.export_excel` - Generate Excel exports (future)

### Service Integration Status

- ✅ **Service Class**: `ReportsService` in `backend/app/services/reports.py`
- ✅ **Agent Class**: `ReportsAgent` in `backend/app/agents/reports_agent.py`
- ⚠️ **Pattern Integration**: `export_portfolio_report.json` exists but not fully wired
- ⚠️ **WeasyPrint**: Integration implemented but needs testing

### Implementation Status

#### ✅ Service Layer Complete
- WeasyPrint integration implemented
- HTML template system implemented
- Rights enforcement implemented
- Watermark and attribution implemented

#### ⚠️ Agent Layer Partial
- Agent class implemented
- Capabilities declared
- Method stubs implemented
- Service integration needs completion

#### ❌ Pattern Integration Pending
- `export_portfolio_report` pattern exists but not fully functional
- UI integration pending
- End-to-end testing pending

### Key Methods

**Agent Method**:
```python
async def reports_render_pdf(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    report_type: str = "portfolio_overview",
    template_data: Dict[str, Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """Generate PDF report with rights enforcement."""

    # Check rights
    if not await reports_service.check_export_rights(ctx.user_id, report_type):
        raise PermissionError("Export rights not granted")

    # Generate PDF
    pdf_result = await reports_service.render_pdf(
        report_type=report_type,
        template_data=template_data or state,
        user_id=ctx.user_id,
        asof_date=ctx.asof_date
    )

    return self._attach_metadata(pdf_result, metadata)
```

**Service Method**:
```python
async def render_pdf(
    self,
    report_type: str,
    template_data: Dict[str, Any],
    user_id: UUID,
    asof_date: date
) -> Dict[str, Any]:
    """Generate PDF report with WeasyPrint."""

    # Load template
    template = await self._load_template(report_type)

    # Apply rights enforcement
    filtered_data = await self._apply_rights_filter(template_data, user_id)

    # Render HTML
    html_content = await self._render_html(template, filtered_data)

    # Generate PDF
    pdf_data = await self._generate_pdf(html_content)

    # Add watermark and attribution
    final_pdf = await self._add_watermark(pdf_data, user_id, asof_date)

    return {
        "pdf_data": final_pdf,
        "report_type": report_type,
        "generated_at": datetime.now(),
        "rights_applied": True
    }
```

### Rights Enforcement Framework

```python
EXPORT_RIGHTS = {
    "portfolio_overview": {
        "required_rights": ["portfolio_read"],
        "watermark_level": "standard",
        "attribution_required": True
    },
    "buffett_checklist": {
        "required_rights": ["ratings_read"],
        "watermark_level": "premium",
        "attribution_required": True
    },
    "macro_analysis": {
        "required_rights": ["macro_read"],
        "watermark_level": "standard",
        "attribution_required": True
    }
}
```

### Template System

**HTML Templates**:
- `portfolio_summary.html` - Portfolio overview
- `buffett_checklist.html` - Quality ratings
- `macro_analysis.html` - Macro analysis
- `base.html` - Base template with styling

**CSS Styling**:
- `dawsos_pdf.css` - PDF-specific styling
- Print-optimized layouts
- Professional color scheme
- Responsive design elements

### WeasyPrint Integration

```python
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

async def _generate_pdf(self, html_content: str) -> bytes:
    """Generate PDF using WeasyPrint."""

    font_config = FontConfiguration()
    html_doc = HTML(string=html_content)

    pdf_bytes = html_doc.write_pdf(
        stylesheets=[CSS('backend/templates/dawsos_pdf.css')],
        font_config=font_config
    )

    return pdf_bytes
```

### Performance Characteristics

**Response Times**:
- `reports.render_pdf`: ~3-10 seconds (template dependent)
- `reports.export_csv`: ~1-3 seconds
- `reports.export_excel`: ~2-5 seconds (future)

**PDF Generation Complexity**:
- Simple reports: ~3 seconds
- Complex reports with charts: ~10 seconds
- Large portfolios: ~15+ seconds

**Caching Strategy**:
- Generated PDFs: 1 hour TTL
- Template rendering: 30 minutes TTL
- Rights checks: 15 minutes TTL

### Error Handling

```python
try:
    pdf_data = await self._generate_pdf(html_content)
except WeasyPrintError as e:
    logger.error(f"WeasyPrint error: {e}")
    return {
        "error": "PDF generation failed",
        "fallback": "CSV export available"
    }
except TemplateError as e:
    logger.error(f"Template error: {e}")
    return {
        "error": "Report template error",
        "suggestion": "Contact support"
    }
```

### Security and Compliance

**Data Protection**:
- Rights-based data filtering
- Watermarking for traceability
- Attribution requirements
- Audit logging

**Watermarking**:
```python
async def _add_watermark(self, pdf_data: bytes, user_id: UUID, asof_date: date) -> bytes:
    """Add watermark and attribution to PDF."""

    watermark_info = {
        "user_id": str(user_id),
        "generated_at": asof_date.isoformat(),
        "system": "DawsOS Portfolio Intelligence",
        "rights": "Confidential - Internal Use Only"
    }

    watermarked_pdf = await self._apply_watermark(pdf_data, watermark_info)

    return watermarked_pdf
```

### Testing Needs

**Test Coverage Needed**:
- Unit tests for PDF generation
- Integration tests with WeasyPrint
- Rights enforcement tests
- Template rendering tests

**Test Files to Create**:
- `backend/tests/unit/test_reports_agent.py`
- `backend/tests/integration/test_pdf_generation.py`
- `backend/tests/golden/test_report_outputs.py`

### Configuration

**Environment Variables**:
- `WEASYPRINT_CACHE_SIZE` - PDF cache size
- `PDF_GENERATION_TIMEOUT` - Maximum generation time
- `WATERMARK_ENABLED` - Enable watermarking

**WeasyPrint Configuration**:
```python
WEASYPRINT_CONFIG = {
    "base_url": "backend/templates/",
    "encoding": "utf-8",
    "optimize_images": True,
    "jpeg_quality": 95
}
```

### Monitoring and Observability

**Key Metrics**:
- PDF generation success rate
- Average generation time
- Rights check success rate
- Template rendering performance

**Logging**:
- PDF generation logs
- Rights check logs
- Template rendering logs
- Error logs with context

---

## Agent 3: REPORTING_ARCHITECT (ACTIVE)

**Status**: ✅ **ACTIVE**
**File Location**: `.claude/agents/platform/REPORTING_ARCHITECT.md`
**Priority**: P1 (Legal/compliance critical)
**Implementation Status**: 🚧 Planned

### Mission

Build **rights-gated PDF export system** with WeasyPrint, provider attribution enforcement, reproducibility guarantees (pricing pack + ledger hash), and professional multi-page layouts for portfolio/holding reports.

### Scope & Responsibilities

#### In Scope

1. **PDF Generation (WeasyPrint)**
   - Portfolio summary reports
   - Holding deep-dive reports
   - Custom date range reports
   - Professional layouts with DawsOS branding

2. **Rights Registry Compliance**
   - Pre-export rights check (FMP/Polygon/FRED/NewsAPI licenses)
   - Block exports if restricted data present
   - Mandatory provider attributions in footer
   - Watermark for restricted/demo data

3. **Reproducibility Guarantees**
   - All reports include `pricing_pack_id` + `ledger_commit_hash` in footer
   - Timestamp (timezone-aware, ISO 8601)
   - Data sources with `asof` timestamps
   - Re-run capability (same pack/ledger → identical PDF)

4. **Multi-Page Layouts**
   - Cover page (portfolio name, date, pack/ledger IDs)
   - Table of contents with page numbers
   - Performance summary (KPIs, charts, currency attribution)
   - Holdings breakdown (sector allocations, top 10, ratings)
   - Macro analysis (regime, factors, scenarios)
   - Attribution footers on every page

#### Out of Scope

- ❌ Interactive dashboards (handled by UI_ARCHITECT)
- ❌ Email delivery (handled by alert system)
- ❌ Excel/CSV exports (future roadmap)
- ❌ Custom charting (use Plotly exports to static images)

### Acceptance Criteria (7 ACs)

#### AC-1: Rights Gate Enforcement

**Given**: Portfolio uses data from FMP (export allowed), Polygon (export allowed), NewsAPI (export BLOCKED)

**When**: User requests PDF export

**Then**:
- Pre-export check queries rights registry
- Export **blocked** with error message:
  ```
  Export blocked: NewsAPI data cannot be included in PDF exports.
  Remove news impact analysis or upgrade to NewsAPI Enterprise license.
  ```
- No PDF generated; no partial exports

#### AC-2: Provider Attribution Footer

**Given**: Portfolio uses FMP (prices), FRED (FX rates), Polygon (corporate actions)

**When**: PDF generated successfully

**Then**:
- **Every page** has footer with:
  ```
  Data sources: Financial Modeling Prep (prices, fundamentals), Federal Reserve
  Economic Data (FX rates, macro indicators), Polygon.io (corporate actions)

  Pricing Pack: 2024-10-21-WM4PM-CAD | Ledger: a3f2c8e | Generated: 2024-10-21 16:45 EDT
  ```
- Footer font: 8pt, gray (#666), centered
- Attribution text matches provider requirements

#### AC-3: Reproducibility Guarantee

**Given**: Portfolio "Growth-2024" on 2024-10-21

**When**: Generate PDF twice with same `pricing_pack_id` + `ledger_commit_hash`

**Then**:
- Both PDFs have **identical content**:
  - TWR: 8.45% (same to 2 decimals)
  - Holdings table (same order, values)
  - Charts (same data points)
- Footer metadata matches
- Only **timestamp** differs

#### AC-4: Multi-Page Portfolio Report Layout

**Page 1**: Cover
- DawsOS logo
- Portfolio name (36pt)
- Date range
- Generated timestamp

**Page 2**: Table of Contents
- Performance Summary ..... 3
- Allocations ............. 4
- Holdings Breakdown ...... 5
- Macro Analysis .......... 7
- Ratings Summary ......... 8

**Page 3**: Performance Summary
- KPI table (TWR, MWR, Vol, Max-DD, Sharpe)
- Currency attribution table
- Equity curve chart

**Page 4**: Allocations
- Sector pie chart
- Top 10 holdings bar chart
- Concentration metrics

**Page 5-6**: Holdings Breakdown
- Full holdings table
- Sorted by weight descending
- Paginated if > 25 holdings

**Page 7**: Macro Analysis
- Regime card
- Factor exposure bars
- DaR gauge

**Page 8**: Ratings Summary
- Histogram of DivSafety scores
- Histogram of Moat scores
- Histogram of Resilience scores
- List of holdings with ratings < 5

#### AC-5: Holding Deep-Dive Report

**Page 1**: Cover
**Page 2**: Fundamentals
**Page 3**: Valuation
**Page 4**: Ratings Breakdown
**Page 5**: Macro Exposure
**Page 6**: News Impact (if allowed) or Watermark

#### AC-6: Watermark for Restricted Data

**Given**: Portfolio uses NewsAPI data (export restricted)

**When**: User requests "demo mode" export

**Then**:
- PDF generates with **watermark** on news pages:
  ```
  ┌─────────────────────────────────────┐
  │  DATA EXCLUDED - LICENSE RESTRICTED │
  │  NewsAPI Enterprise required for    │
  │  news impact export                 │
  └─────────────────────────────────────┘
  ```
- Watermark: 45° diagonal, light gray, semi-transparent
- Rest of report renders normally

#### AC-7: Custom Date Range Report

**Given**: User requests PDF for Q3 2024 (2024-07-01 to 2024-09-30)

**Then**:
- Cover page shows: "Q3 2024 Performance Report (Jul 1 - Sep 30)"
- Performance metrics calculated for Q3 only
- Holdings snapshot as of 2024-09-30 EOD
- Footer includes date range

### Implementation Specifications

#### Rights Registry

```python
from dataclasses import dataclass
from typing import Literal

ExportType = Literal["pdf", "csv", "excel", "api"]

@dataclass
class ProviderRights:
    """Provider-specific license rights."""
    provider: str
    allows_display: bool
    allows_export_pdf: bool
    allows_export_csv: bool
    allows_redistribution: bool
    attribution_text: str

class RightsRegistry:
    """Enforce provider license terms for exports."""

    def __init__(self):
        self.rights = {
            "FMP": ProviderRights(
                provider="Financial Modeling Prep",
                allows_export_pdf=True,
                attribution_text="Data provided by Financial Modeling Prep (financialmodelingprep.com)"
            ),
            "NewsAPI": ProviderRights(
                provider="NewsAPI",
                allows_export_pdf=False,  # Requires Enterprise license
                attribution_text="News data from NewsAPI.org"
            )
        }

    def allows_export(self, provider: str, export_type: ExportType = "pdf") -> bool:
        """Check if provider allows export."""
        rights = self.rights.get(provider)
        if not rights:
            return False

        if export_type == "pdf":
            return rights.allows_export_pdf
        return False

    def check_export_allowed(self, providers: list[str], export_type: ExportType = "pdf") -> tuple[bool, list[str]]:
        """
        Check if export is allowed for all providers.

        Returns:
            (allowed: bool, blocked_providers: list[str])
        """
        blocked = []
        for provider in providers:
            if not self.allows_export(provider, export_type):
                blocked.append(provider)

        return (len(blocked) == 0, blocked)
```

#### PDF Generator (WeasyPrint)

```python
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from core.rights_registry import RightsRegistry

class ReportingService:
    """Generate PDF reports with rights gates and reproducibility."""

    def __init__(self):
        self.rights = RightsRegistry()
        self.jinja_env = Environment(loader=FileSystemLoader("templates/reports"))

    def generate_portfolio_pdf(
        self,
        portfolio_id: str,
        ctx: ExecutorContext,
        date_range: tuple[datetime.date, datetime.date] = None
    ) -> bytes:
        """Generate portfolio summary PDF with rights gate."""

        # 1. Fetch data via executor (pattern-based)
        data = self._fetch_portfolio_data(portfolio_id, ctx, date_range)

        # 2. Trace providers used
        providers = self._trace_providers(data)

        # 3. Rights gate
        allowed, blocked = self.rights.check_export_allowed(providers, "pdf")
        if not allowed:
            raise ExportBlockedError(
                f"Export blocked: {', '.join(blocked)} data cannot be exported. "
                f"Remove restricted analysis or upgrade license."
            )

        # 4. Render HTML template
        attribution = self.rights.get_attribution_text(providers)

        html = self.jinja_env.get_template("portfolio_summary.html").render(
            portfolio_name=data["portfolio_name"],
            kpis=data["kpis"],
            holdings=data["holdings"],
            footer={
                "attribution": attribution,
                "pricing_pack_id": ctx.pricing_pack_id,
                "ledger_commit_hash": ctx.ledger_commit_hash,
                "generated_at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            }
        )

        # 5. Generate PDF with custom CSS
        css = CSS(filename="templates/reports/dawsos_pdf.css")
        pdf_bytes = HTML(string=html).write_pdf(stylesheets=[css])

        return pdf_bytes
```

#### Jinja2 HTML Template

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        @page {
            size: letter;
            margin: 0.75in;

            @bottom-center {
                content: "{{ footer.attribution }}";
                font-size: 8pt;
                color: #666;
            }

            @bottom-right {
                content: "Pack: {{ footer.pricing_pack_id[:8] }} | Ledger: {{ footer.ledger_commit_hash[:7] }}";
                font-size: 8pt;
                color: #666;
            }
        }

        body {
            font-family: 'Inter', sans-serif;
            color: #333;
        }

        .metric-table {
            font-family: 'IBM Plex Mono', monospace;
        }
    </style>
</head>
<body>
    <div class="cover">
        <h1>{{ portfolio_name }}</h1>
        <p>Generated: {{ footer.generated_at }}</p>
    </div>

    <h2>Performance Summary</h2>
    <table class="metric-table">
        <tr><td>TWR (YTD)</td><td>{{ "%.2f"|format(kpis.twr * 100) }}%</td></tr>
        <tr><td>Sharpe Ratio</td><td>{{ "%.2f"|format(kpis.sharpe) }}</td></tr>
    </table>

    <h2>Holdings Breakdown</h2>
    <table>
        {% for holding in holdings %}
        <tr>
            <td>{{ holding.symbol }}</td>
            <td>{{ holding.name }}</td>
            <td>${{ "{:,.0f}".format(holding.value) }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
```

### Dependencies

```txt
weasyprint==60.1
jinja2==3.1.2
pillow==10.0.1
plotly==5.17.0
kaleido==0.2.1  # Plotly static image export
```

### Testing Strategy

**Integration Tests**:
```python
def test_newsapi_export_blocked():
    """Verify NewsAPI data blocks PDF export."""
    portfolio = create_test_portfolio_with_news()

    with pytest.raises(ExportBlockedError, match="NewsAPI data cannot be exported"):
        ReportingService().generate_portfolio_pdf(
            portfolio_id=portfolio.id,
            ctx=mock_executor_context()
        )
```

**Golden Tests**:
```python
def test_identical_pdf_from_same_pack_ledger():
    """Verify same pack+ledger produces identical PDF (ignoring timestamp)."""
    ctx = ExecutorContext(
        pricing_pack_id="2024-10-21-WM4PM-CAD",
        ledger_commit_hash="a3f2c8e"
    )

    pdf1 = ReportingService().generate_portfolio_pdf("portfolio-123", ctx)
    pdf2 = ReportingService().generate_portfolio_pdf("portfolio-123", ctx)

    text1 = extract_text(pdf1).replace(extract_timestamp(pdf1), "")
    text2 = extract_text(pdf2).replace(extract_timestamp(pdf2), "")

    assert text1 == text2  # Identical content
```

### Done Criteria

- [x] RightsRegistry with FMP/Polygon/FRED/NewsAPI rules
- [x] Pre-export rights gate (blocks if restricted)
- [x] Provider attribution footers on all pages
- [x] Reproducibility guarantee (same pack/ledger → identical PDF)
- [x] Multi-page portfolio report layout (cover, TOC, 8 sections)
- [x] Holding deep-dive report with ratings breakdown
- [x] Watermark for restricted data (demo mode)
- [x] Custom date range support (YTD, QTD, MTD, custom)
- [x] Integration tests for rights enforcement
- [x] Golden tests for reproducibility
- [x] Jinja2 templates with DawsOS branding
- [x] WeasyPrint PDF generation with custom CSS

---

## Comparison Matrix

| Feature | UI_ARCHITECT (Archived) | REPORTS_AGENT (Active) | REPORTING_ARCHITECT (Active) |
|---------|-------------------------|------------------------|------------------------------|
| **Status** | 🗑️ Deleted/Archived | ✅ Active (Partial) | ✅ Active (Planned) |
| **Focus** | Streamlit UI/UX | PDF/CSV Export Service | PDF Export Architecture |
| **Priority** | P0 (Critical) | P1 (High) | P1 (Legal/Compliance) |
| **Rights Enforcement** | ✅ Pre-export checks | ✅ Service layer | ✅ Registry-based |
| **PDF Generation** | ✅ WeasyPrint integration | ✅ WeasyPrint service | ✅ WeasyPrint + Jinja2 |
| **Provenance Display** | ✅ UI badges | ⚠️ PDF footers (partial) | ✅ Multi-page layouts |
| **Template System** | ✅ Streamlit components | ✅ HTML templates | ✅ Jinja2 templates |
| **Multi-Page Reports** | ❌ N/A (UI only) | ⚠️ Partial | ✅ Full spec (8 pages) |
| **Watermarking** | ❌ N/A | ✅ Implemented | ✅ With demo mode |
| **Reproducibility** | ❌ N/A | ⚠️ Planned | ✅ Pack + Ledger hash |
| **Testing Strategy** | ✅ Visual regression | ⚠️ Needs tests | ✅ Integration + Golden |
| **Implementation** | ✅ Complete (archived) | ⚠️ Partial | 🚧 Planned |

---

## Key Findings

### 1. UI_ARCHITECT Agent Was Archived

**Status**: The UI_ARCHITECT agent specification was **deleted** from active agents and is only found in git history.

**Implications**:
- UI work may be **complete**
- OR UI implementation **deprioritized**
- OR UI being handled by different team/approach

**Evidence of Completion**:
- `frontend/` directory exists with Streamlit code
- `frontend/requirements.txt` has 19 packages including Streamlit
- Recent git activity shows UI file modifications

**Recommendation**: **Verify with team** whether:
1. UI work is complete and agent was archived post-implementation
2. Streamlit UI is deprecated in favor of API-first approach
3. Next.js migration started (Phase 2 of migration plan)

---

### 2. Reports Agent Overlap

**Two active agents** handling PDF reports:
- **REPORTS_AGENT**: Service-level implementation
- **REPORTING_ARCHITECT**: Architecture/specification

**Overlap Areas**:
- Both specify WeasyPrint integration
- Both define rights enforcement
- Both describe PDF generation flows
- Both mention provider attribution

**Differences**:
- REPORTS_AGENT: Focuses on **service implementation**
- REPORTING_ARCHITECT: Focuses on **architecture and compliance**

**Recommendation**: These agents may need **consolidation** to avoid:
- Duplicate specifications
- Conflicting implementation details
- Maintenance overhead

**Suggested Approach**:
1. Use REPORTING_ARCHITECT as **design spec**
2. Use REPORTS_AGENT as **implementation guide**
3. Ensure both stay in sync

---

### 3. Implementation Status Gap

**REPORTS_AGENT Status**: ⚠️ Partial
- Service layer: ✅ Complete
- Agent layer: ⚠️ Partial
- Pattern integration: ❌ Pending
- Testing: ❌ Missing

**REPORTING_ARCHITECT Status**: 🚧 Planned
- All acceptance criteria defined
- Implementation specs provided
- Testing strategy documented
- But no indication of actual implementation

**Risk**: Specifications exist but **implementation may be incomplete**.

**Recommendation**:
1. Review actual code in `backend/app/services/reports.py`
2. Check `backend/app/agents/reports_agent.py` completeness
3. Verify pattern `export_portfolio_report.json` exists and works
4. Run integration tests (if they exist)

---

### 4. Rights Registry Critical Path

**All three agents rely on Rights Registry**:
- UI_ARCHITECT: Pre-export rights checks
- REPORTS_AGENT: Service-level enforcement
- REPORTING_ARCHITECT: Registry-based compliance

**Implementation**:
```python
# backend/app/core/rights_registry.py (should exist)

class RightsRegistry:
    def allows_export(self, provider: str, export_type: str) -> bool:
        """Check if provider allows export."""
        pass

    def get_attribution_text(self, providers: list[str]) -> str:
        """Get combined attribution text."""
        pass

    def check_export_allowed(self, providers: list[str]) -> tuple[bool, list[str]]:
        """Check if export is allowed for all providers."""
        pass
```

**Recommendation**:
1. Verify `backend/app/core/rights_registry.py` exists
2. Check provider rules (FMP, Polygon, FRED, NewsAPI)
3. Ensure audit logging implemented

---

### 5. Template System Needs Verification

**Both reports agents specify templates**:
- `backend/templates/portfolio_report.html`
- `backend/templates/holding_report.html`
- `backend/templates/macro_report.html`
- `backend/static/css/report_styles.css`
- `backend/templates/dawsos_pdf.css`

**Also mentioned**: `backend/templates/portfolio_report.html` (verified exists in repo)

**Recommendation**:
1. Verify all templates exist
2. Check CSS styling matches DawsOS theme
3. Ensure Jinja2 environment configured
4. Test PDF rendering with real data

---

### 6. Testing Gaps

**UI_ARCHITECT**: Specified tests but status unknown
- Visual regression tests
- Integration tests
- Accessibility tests

**REPORTS_AGENT**: Testing needed
- Unit tests for PDF generation
- Integration tests with WeasyPrint
- Rights enforcement tests
- Template rendering tests

**REPORTING_ARCHITECT**: Testing strategy defined
- Integration tests for rights enforcement
- Golden tests for reproducibility
- Multi-page layout validation

**Recommendation**:
1. Check `backend/tests/` directory for existing tests
2. Implement missing tests based on agent specs
3. Add to CI/CD pipeline

---

## Recommendations

### Immediate Actions

1. **Clarify UI_ARCHITECT Status**
   - Ask team: Why was it archived?
   - Verify: Is Streamlit UI complete?
   - Confirm: Next.js migration plans?

2. **Consolidate Reports Agent Specs**
   - Merge REPORTS_AGENT and REPORTING_ARCHITECT
   - Create single source of truth
   - Avoid specification drift

3. **Verify Rights Registry Implementation**
   - Check `backend/app/core/rights_registry.py` exists
   - Test provider rules (FMP, Polygon, FRED, NewsAPI)
   - Ensure export blocking works

4. **Complete Reports Agent Implementation**
   - Finish pattern integration (`export_portfolio_report.json`)
   - Wire agent methods to service
   - Add UI integration (if Streamlit still active)

5. **Create Missing Tests**
   - Unit tests for PDF generation
   - Integration tests for rights enforcement
   - Golden tests for reproducibility
   - Visual regression tests for templates

### Medium-Term Actions

6. **Template System Audit**
   - Verify all templates exist
   - Ensure styling matches DawsOS theme
   - Test PDF rendering with real data

7. **Performance Testing**
   - Measure PDF generation times
   - Optimize for large portfolios (15+ seconds → target < 5s)
   - Implement caching (1 hour TTL)

8. **Accessibility Audit**
   - If Streamlit UI active, verify WCAG AA compliance
   - Test keyboard navigation
   - Validate ARIA labels

### Long-Term Actions

9. **Next.js Migration Planning**
   - If UI_ARCHITECT archived due to migration
   - Plan Phase 2 (Next.js prototype)
   - Define migration timeline

10. **Advanced Features**
    - Interactive PDF reports
    - Custom report templates
    - Scheduled report generation
    - Multi-format exports (Excel, CSV)

---

## Conclusion

DawsOS has **well-defined UI and reporting architecture** with three agents covering:
1. **UI_ARCHITECT** (archived): Streamlit interface design
2. **REPORTS_AGENT** (active, partial): PDF/CSV export service
3. **REPORTING_ARCHITECT** (active, planned): PDF architecture and compliance

**Key Issues**:
- UI_ARCHITECT archived (reason unclear)
- Reports agents have overlap and may need consolidation
- Implementation status uncertain (specs exist but code verification needed)
- Testing gaps (especially for PDF generation and rights enforcement)

**Next Steps**:
1. Verify UI_ARCHITECT archival reason
2. Consolidate reports agent specifications
3. Complete reports agent implementation
4. Verify rights registry implementation
5. Create comprehensive test suite

**Overall Assessment**: 🟡 **Good Architecture, Implementation Verification Needed**

The agent specifications are comprehensive and well-thought-out, but actual code implementation status needs verification to ensure alignment with specs.

---

**Review Date**: October 28, 2025
**Reviewed By**: Claude (Sonnet 4.5)
**Files Reviewed**:
- `.claude/agents/archive/UI_ARCHITECT.md` (deleted, 779 lines)
- `.claude/agents/REPORTS_AGENT.md` (active, 409 lines)
- `.claude/agents/platform/REPORTING_ARCHITECT.md` (active, 856 lines)

**Status**: 📋 Analysis Complete - Recommendations Provided
