# REPORTING_ARCHITECT — PDF Export & Rights Compliance Specialist

**Agent Type**: Platform
**Phase**: Week 2-3 (Integration + Compliance)
**Priority**: P1 (Legal/compliance critical)
**Status**: 🚧 Planned — reports service currently returns placeholder text; WeasyPrint export pending (see `.ops/TASK_INVENTORY_2025-10-24.md`, P1-DOCS/P1-CODE entries)
**Created**: 2025-10-21

---

## Mission

Build **rights-gated PDF export system** with WeasyPrint, provider attribution enforcement, reproducibility guarantees (pricing pack + ledger hash), and professional multi-page layouts for portfolio/holding reports.

---

## Scope & Responsibilities

### In Scope

1. **PDF Generation (WeasyPrint)**
   - Portfolio summary reports (performance, allocations, holdings)
   - Holding deep-dive reports (fundamentals, ratings, macro, news)
   - Custom date range reports (YTD, QTD, MTD, custom)
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

### Out of Scope

- ❌ Interactive dashboards (handled by UI_ARCHITECT)
- ❌ Email delivery (handled by alert system)
- ❌ Excel/CSV exports (future roadmap)
- ❌ Custom charting (use Plotly exports to static images)

---

## Acceptance Criteria

### AC-1: Rights Gate Enforcement
**Given**: Portfolio uses data from FMP (export allowed), Polygon (export allowed), NewsAPI (export BLOCKED)
**When**: User requests PDF export
**Then**:
- **Pre-export check** queries rights registry:
  ```python
  rights = RightsRegistry()
  sources = trace_providers(portfolio_data)  # Returns ["FMP", "Polygon", "NewsAPI"]

  for source in sources:
      if not rights.allows_export(source):
          raise ExportBlockedError(f"{source} data cannot be exported per license terms")
  ```
- Export **blocked** with error message:
  ```
  Export blocked: NewsAPI data cannot be included in PDF exports.
  Remove news impact analysis or upgrade to NewsAPI Enterprise license.
  ```
- No PDF generated; no partial exports

**Integration Test**: `tests/integration/test_rights_gate_enforcement.py`

---

### AC-2: Provider Attribution Footer
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
- Attribution text matches provider requirements (from rights registry)
- If FMP requires specific text (e.g., "Data provided by FMP"), use verbatim

**Unit Test**: `tests/unit/reporting/test_attribution_footer.py`

---

### AC-3: Reproducibility Guarantee
**Given**: Portfolio "Growth-2024" on 2024-10-21
**When**: Generate PDF twice with same `pricing_pack_id` + `ledger_commit_hash`
**Then**:
- Both PDFs have **identical content**:
  - TWR: 8.45% (same to 2 decimals)
  - Holdings table (same order, values)
  - Charts (same data points)
- Footer metadata matches:
  ```
  Pack: 2024-10-21-WM4PM-CAD | Ledger: a3f2c8e
  ```
- Only **timestamp** differs (generated_at)
- **Golden test**: `tests/golden/reports/portfolio_reproducibility.json`

**Validation**:
```python
pdf1 = generate_pdf(portfolio_id, pack_id, ledger_hash)
pdf2 = generate_pdf(portfolio_id, pack_id, ledger_hash)

# Extract text (ignore timestamp)
text1 = extract_text(pdf1).replace(timestamp1, "")
text2 = extract_text(pdf2).replace(timestamp2, "")

assert text1 == text2  # Identical except timestamp
```

**Golden Test**: `tests/golden/reports/portfolio_summary_2024-10-21.json`

---

### AC-4: Multi-Page Portfolio Report Layout
**Given**: User requests portfolio summary PDF
**When**: PDF generates
**Then**:
- **Page 1: Cover**
  - DawsOS logo (top-left)
  - Portfolio name (centered, 36pt)
  - Date range (e.g., "YTD Performance 2024")
  - Generated timestamp (bottom-right)

- **Page 2: Table of Contents**
  - Performance Summary ..... 3
  - Allocations ............. 4
  - Holdings Breakdown ...... 5
  - Macro Analysis .......... 7
  - Ratings Summary ......... 8

- **Page 3: Performance Summary**
  - KPI table (TWR, MWR, Vol, Max-DD, Sharpe) — monospace font
  - Currency attribution table (local/FX/interaction)
  - Equity curve chart (NAV over time)

- **Page 4: Allocations**
  - Sector pie chart
  - Top 10 holdings bar chart
  - Concentration metrics (HHI, top-10 weight)

- **Page 5-6: Holdings Breakdown**
  - Full holdings table (symbol, name, value, weight, P/L, ratings)
  - Sorted by weight descending
  - Paginated if > 25 holdings

- **Page 7: Macro Analysis**
  - Regime card (label, probability, drivers)
  - Factor exposure bars
  - DaR gauge with breakdown

- **Page 8: Ratings Summary**
  - Histogram of DivSafety scores across holdings
  - Histogram of Moat scores
  - Histogram of Resilience scores
  - List of holdings with ratings < 5 (flags)

**Visual Test**: Manual review of `tests/fixtures/reports/sample_portfolio.pdf`

---

### AC-5: Holding Deep-Dive Report
**Given**: User requests deep-dive PDF for AAPL
**When**: PDF generates
**Then**:
- **Page 1: Cover**
  - Logo + symbol (AAPL)
  - Company name (Apple Inc.)

- **Page 2: Fundamentals**
  - Key metrics: ROE, ROA, Gross Margin, Net Margin, D/E
  - 5-year trend charts
  - Source: FMP

- **Page 3: Valuation**
  - DCF snapshot (intrinsic value, margin of safety)
  - P/E, P/B, PEG ratios
  - Valuation band chart (fair value ± 20%)

- **Page 4: Ratings Breakdown**
  - DivSafety: 8.5/10
    - Payout ratio: 15% (weight: 0.30)
    - FCF coverage: 6.7x (weight: 0.35)
    - Growth streak: 10 years (weight: 0.20)
    - Net cash: $50B (weight: 0.15)
  - Moat: 9.2/10 (components listed)
  - Resilience: 8.0/10 (components listed)

- **Page 5: Macro Exposure**
  - Factor betas (Growth: 0.35, Quality: 0.45, ...)
  - Scenario ΔP/L table (Rates +50bp, USD +5%, CPI +0.4%)

- **Page 6: News Impact** (if NewsAPI allowed)
  - Last 10 articles with sentiment/impact scores
  - Or: **Watermark**: "News data excluded (NewsAPI export restricted)"

**Integration Test**: `tests/integration/test_holding_deepdive_pdf.py`

---

### AC-6: Watermark for Restricted Data
**Given**: Portfolio uses NewsAPI data (export restricted)
**When**: User requests "demo mode" export (instead of blocking)
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
- Rest of report (performance, allocations, ratings) renders normally
- Footer notes: "News analysis excluded per license restrictions"

**Unit Test**: `tests/unit/reporting/test_watermark_restricted_data.py`

---

### AC-7: Custom Date Range Report
**Given**: User requests PDF for Q3 2024 (2024-07-01 to 2024-09-30)
**When**: PDF generates
**Then**:
- Cover page shows: "Q3 2024 Performance Report (Jul 1 - Sep 30)"
- Performance metrics calculated for Q3 only:
  - TWR (Q3): 4.2%
  - Max-DD (Q3): -2.1%
- Holdings snapshot as of 2024-09-30 EOD
- Footer includes date range: "Period: 2024-07-01 to 2024-09-30"

**Unit Test**: `tests/unit/reporting/test_custom_date_range.py`

---

## Implementation Specifications

### Rights Registry

```python
# core/rights_registry.py

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
    attribution_text: str  # Mandatory footer text

class RightsRegistry:
    """Enforce provider license terms for exports."""

    def __init__(self):
        self.rights = {
            "FMP": ProviderRights(
                provider="Financial Modeling Prep",
                allows_display=True,
                allows_export_pdf=True,
                allows_export_csv=True,
                allows_redistribution=False,
                attribution_text="Data provided by Financial Modeling Prep (financialmodelingprep.com)"
            ),
            "Polygon": ProviderRights(
                provider="Polygon.io",
                allows_display=True,
                allows_export_pdf=True,
                allows_export_csv=True,
                allows_redistribution=False,
                attribution_text="Market data provided by Polygon.io"
            ),
            "FRED": ProviderRights(
                provider="Federal Reserve Economic Data",
                allows_display=True,
                allows_export_pdf=True,
                allows_export_csv=True,
                allows_redistribution=True,  # Public domain
                attribution_text="Economic data from Federal Reserve Economic Data (FRED)"
            ),
            "NewsAPI": ProviderRights(
                provider="NewsAPI",
                allows_display=True,
                allows_export_pdf=False,  # Requires Enterprise license
                allows_export_csv=False,
                allows_redistribution=False,
                attribution_text="News data from NewsAPI.org"
            )
        }

    def allows_export(self, provider: str, export_type: ExportType = "pdf") -> bool:
        """Check if provider allows export."""
        rights = self.rights.get(provider)
        if not rights:
            return False  # Unknown provider → block

        if export_type == "pdf":
            return rights.allows_export_pdf
        elif export_type == "csv":
            return rights.allows_export_csv
        else:
            return False

    def get_attribution_text(self, providers: list[str]) -> str:
        """Get combined attribution text for footer."""
        attributions = []
        for provider in providers:
            rights = self.rights.get(provider)
            if rights:
                attributions.append(rights.attribution_text)

        return " | ".join(attributions)

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

---

### PDF Generator (WeasyPrint)

```python
# services/reporting.py

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from core.rights_registry import RightsRegistry, ExportType
from core.executor import ExecutorContext
import datetime

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
        """
        Generate portfolio summary PDF with rights gate.

        Args:
            portfolio_id: Portfolio UUID
            ctx: Executor context (with pricing_pack_id, ledger_commit_hash)
            date_range: Optional (start, end) for custom range

        Returns:
            PDF bytes

        Raises:
            ExportBlockedError: If any provider blocks export
        """

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
            date_range=date_range or "YTD",
            kpis=data["kpis"],
            allocations=data["allocations"],
            holdings=data["holdings"],
            macro=data["macro"],
            ratings=data["ratings"],
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

    def generate_holding_deepdive_pdf(
        self,
        portfolio_id: str,
        symbol: str,
        ctx: ExecutorContext
    ) -> bytes:
        """Generate holding deep-dive PDF with rights gate."""

        data = self._fetch_holding_data(portfolio_id, symbol, ctx)
        providers = self._trace_providers(data)

        allowed, blocked = self.rights.check_export_allowed(providers, "pdf")

        # If NewsAPI blocked, apply watermark instead of full block
        watermark_pages = []
        if "NewsAPI" in blocked:
            watermark_pages = ["news_impact"]  # Watermark just the news page
            blocked.remove("NewsAPI")  # Don't block entire export

        if blocked:
            raise ExportBlockedError(f"Export blocked: {', '.join(blocked)}")

        attribution = self.rights.get_attribution_text([p for p in providers if p not in watermark_pages])

        html = self.jinja_env.get_template("holding_deepdive.html").render(
            symbol=symbol,
            company_name=data["company_name"],
            fundamentals=data["fundamentals"],
            valuation=data["valuation"],
            ratings=data["ratings"],
            macro=data["macro"],
            news=data.get("news") if "NewsAPI" not in watermark_pages else None,
            watermark_pages=watermark_pages,
            footer={
                "attribution": attribution,
                "pricing_pack_id": ctx.pricing_pack_id,
                "ledger_commit_hash": ctx.ledger_commit_hash,
                "generated_at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            }
        )

        css = CSS(filename="templates/reports/dawsos_pdf.css")
        pdf_bytes = HTML(string=html).write_pdf(stylesheets=[css])

        return pdf_bytes

    def _fetch_portfolio_data(self, portfolio_id: str, ctx: ExecutorContext, date_range) -> dict:
        """Fetch portfolio data via executor."""
        # Call executor with pattern "export_portfolio_report"
        # Returns all necessary data: kpis, allocations, holdings, macro, ratings
        pass

    def _fetch_holding_data(self, portfolio_id: str, symbol: str, ctx: ExecutorContext) -> dict:
        """Fetch holding deep-dive data via executor."""
        # Call executor with pattern "export_holding_report"
        pass

    def _trace_providers(self, data: dict) -> list[str]:
        """Extract list of providers from data sources."""
        sources = data.get("_sources", {})
        providers = []

        if sources.get("prices"):
            providers.append("FMP")
        if sources.get("corporate_actions"):
            providers.append("Polygon")
        if sources.get("fx_rates") or sources.get("macro_indicators"):
            providers.append("FRED")
        if sources.get("news"):
            providers.append("NewsAPI")

        return list(set(providers))


class ExportBlockedError(Exception):
    """Raised when export is blocked by rights registry."""
    pass
```

---

### Jinja2 HTML Template

```html
<!-- templates/reports/portfolio_summary.html -->

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ portfolio_name }} - DawsOS Report</title>
    <style>
        @page {
            size: letter;
            margin: 0.75in;

            @bottom-center {
                content: "{{ footer.attribution }}";
                font-size: 8pt;
                color: #666;
                text-align: center;
            }

            @bottom-right {
                content: "Pack: {{ footer.pricing_pack_id[:8] }} | Ledger: {{ footer.ledger_commit_hash[:7] }}";
                font-size: 8pt;
                color: #666;
            }

            @bottom-left {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 8pt;
                color: #666;
            }
        }

        body {
            font-family: 'Inter', 'Helvetica Neue', sans-serif;
            color: #333;
            line-height: 1.6;
        }

        h1 { font-size: 24pt; margin-bottom: 0.5em; }
        h2 { font-size: 18pt; margin-top: 1em; border-bottom: 2px solid #00ACC1; padding-bottom: 0.2em; }

        .cover {
            text-align: center;
            margin-top: 3in;
        }

        .cover h1 {
            font-size: 36pt;
            color: #00ACC1;
        }

        .metric-table {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10pt;
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }

        .metric-table th, .metric-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: right;
        }

        .metric-table th {
            background-color: #f5f5f5;
            text-align: left;
        }

        .chart {
            margin: 1em 0;
            text-align: center;
        }

        .holdings-table {
            font-size: 9pt;
            border-collapse: collapse;
            width: 100%;
        }

        .holdings-table th, .holdings-table td {
            border: 1px solid #ddd;
            padding: 6px;
        }

        .holdings-table th {
            background-color: #00ACC1;
            color: white;
        }

        .rating-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 8pt;
        }

        .rating-high { background-color: #c8e6c9; color: #2e7d32; }
        .rating-medium { background-color: #fff9c4; color: #f57f17; }
        .rating-low { background-color: #ffcdd2; color: #c62828; }
    </style>
</head>
<body>

<!-- Cover Page -->
<div class="cover">
    <img src="static/dawsos_logo.png" width="150" />
    <h1>{{ portfolio_name }}</h1>
    <p style="font-size: 18pt; color: #666;">{{ date_range }} Performance Report</p>
    <p style="font-size: 12pt; color: #999;">Generated: {{ footer.generated_at }}</p>
</div>

<div style="page-break-after: always;"></div>

<!-- Table of Contents -->
<h1>Table of Contents</h1>
<ul style="font-size: 14pt; line-height: 2;">
    <li>Performance Summary ........... 3</li>
    <li>Allocations ................... 4</li>
    <li>Holdings Breakdown ............ 5</li>
    <li>Macro Analysis ................ 7</li>
    <li>Ratings Summary ............... 8</li>
</ul>

<div style="page-break-after: always;"></div>

<!-- Performance Summary -->
<h2>Performance Summary</h2>

<table class="metric-table">
    <thead>
        <tr>
            <th>Metric</th>
            <th>Value</th>
        </tr>
    </thead>
    <tbody>
        <tr><td>TWR (YTD)</td><td>{{ "%.2f"|format(kpis.twr * 100) }}%</td></tr>
        <tr><td>MWR</td><td>{{ "%.2f"|format(kpis.mwr * 100) }}%</td></tr>
        <tr><td>Volatility (Ann.)</td><td>{{ "%.2f"|format(kpis.vol * 100) }}%</td></tr>
        <tr><td>Max Drawdown</td><td>{{ "%.2f"|format(kpis.max_dd * 100) }}%</td></tr>
        <tr><td>Sharpe Ratio</td><td>{{ "%.2f"|format(kpis.sharpe) }}</td></tr>
    </tbody>
</table>

<h3>Currency Attribution</h3>
<table class="metric-table">
    <thead>
        <tr><th>Component</th><th>Contribution</th></tr>
    </thead>
    <tbody>
        <tr><td>Local Return</td><td>{{ "%.2f"|format(kpis.local_ret * 100) }}%</td></tr>
        <tr><td>FX Return</td><td>{{ "%.2f"|format(kpis.fx_ret * 100) }}%</td></tr>
        <tr><td>Interaction</td><td>{{ "%.2f"|format(kpis.interaction_ret * 100) }}%</td></tr>
    </tbody>
</table>

<div style="page-break-after: always;"></div>

<!-- Allocations -->
<h2>Allocations</h2>

<div class="chart">
    <img src="{{ allocations.sector_pie_base64 }}" width="500" />
    <p style="font-size: 10pt; color: #666;">Sector Allocation</p>
</div>

<div style="page-break-after: always;"></div>

<!-- Holdings -->
<h2>Holdings Breakdown</h2>

<table class="holdings-table">
    <thead>
        <tr>
            <th>Symbol</th>
            <th>Name</th>
            <th>Value</th>
            <th>Weight</th>
            <th>P/L</th>
            <th>Ratings</th>
        </tr>
    </thead>
    <tbody>
        {% for holding in holdings %}
        <tr>
            <td>{{ holding.symbol }}</td>
            <td>{{ holding.name }}</td>
            <td>${{ "{:,.0f}".format(holding.value) }}</td>
            <td>{{ "%.1f"|format(holding.weight * 100) }}%</td>
            <td>{{ "%.2f"|format(holding.pl * 100) }}%</td>
            <td>
                {% if holding.ratings.div_safety >= 8 %}
                <span class="rating-badge rating-high">D:{{ "%.1f"|format(holding.ratings.div_safety) }}</span>
                {% elif holding.ratings.div_safety >= 5 %}
                <span class="rating-badge rating-medium">D:{{ "%.1f"|format(holding.ratings.div_safety) }}</span>
                {% else %}
                <span class="rating-badge rating-low">D:{{ "%.1f"|format(holding.ratings.div_safety) }}</span>
                {% endif %}

                {% if holding.ratings.moat >= 8 %}
                <span class="rating-badge rating-high">M:{{ "%.1f"|format(holding.ratings.moat) }}</span>
                {% elif holding.ratings.moat >= 5 %}
                <span class="rating-badge rating-medium">M:{{ "%.1f"|format(holding.ratings.moat) }}</span>
                {% else %}
                <span class="rating-badge rating-low">M:{{ "%.1f"|format(holding.ratings.moat) }}</span>
                {% endif %}

                {% if holding.ratings.resilience >= 8 %}
                <span class="rating-badge rating-high">R:{{ "%.1f"|format(holding.ratings.resilience) }}</span>
                {% elif holding.ratings.resilience >= 5 %}
                <span class="rating-badge rating-medium">R:{{ "%.1f"|format(holding.ratings.resilience) }}</span>
                {% else %}
                <span class="rating-badge rating-low">R:{{ "%.1f"|format(holding.ratings.resilience) }}</span>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div style="page-break-after: always;"></div>

<!-- Macro Analysis -->
<h2>Macro Analysis</h2>

<h3>Regime: {{ macro.regime.label }} ({{ "%.0f"|format(macro.regime.probability * 100) }}%)</h3>

<table class="metric-table">
    <thead>
        <tr><th>Driver</th><th>Value</th><th>Z-Score</th></tr>
    </thead>
    <tbody>
        {% for driver in macro.regime.drivers %}
        <tr>
            <td>{{ driver.indicator }}</td>
            <td>{{ driver.value }}</td>
            <td>{{ "%.2f"|format(driver.zscore) }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<h3>Factor Exposures</h3>
<table class="metric-table">
    <thead>
        <tr><th>Factor</th><th>Beta</th><th>Variance Share</th></tr>
    </thead>
    <tbody>
        {% for factor in macro.factors %}
        <tr>
            <td>{{ factor.name }}</td>
            <td>{{ "%.2f"|format(factor.beta) }}</td>
            <td>{{ "%.1f"|format(factor.variance_share * 100) }}%</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

</body>
</html>
```

---

## Testing Strategy

### Integration Tests
```python
# tests/integration/test_rights_gate_enforcement.py

def test_newsapi_export_blocked():
    """Verify NewsAPI data blocks PDF export."""
    portfolio = create_test_portfolio_with_news()

    with pytest.raises(ExportBlockedError, match="NewsAPI data cannot be exported"):
        ReportingService().generate_portfolio_pdf(
            portfolio_id=portfolio.id,
            ctx=mock_executor_context()
        )
```

### Golden Tests
```python
# tests/golden/reports/test_reproducibility.py

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

---

## Dependencies

```txt
# requirements.txt (reporting-specific)

weasyprint==60.1
jinja2==3.1.2
pillow==10.0.1  # Image processing for charts
plotly==5.17.0  # Chart exports to base64
kaleido==0.2.1  # Plotly static image export
```

---

## Done Criteria

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

**Next Steps**: Coordinate with UI_ARCHITECT for export button integration and TEST_ARCHITECT for PDF visual regression testing.
