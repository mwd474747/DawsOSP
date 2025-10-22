# Foundation+ 8-Week Execution Roadmap
**Target User**: Professional and Sophisticated Individual Investors
**Launch Date**: Week 8 (Beta to 50-100 users)
**Success Metric**: 20% conversion to $149/mo professional tier = $3K-15K MRR

---

## 🎯 ROADMAP OVERVIEW

| Week | Focus | Key Deliverables | Individual Investor Value |
|------|-------|------------------|--------------------------|
| **Week 0** | Ledger + Pricing | Beancount integration, Pricing packs | "Upload CSV → Professional accounting" |
| **Week 1** | Macro + KG | Macro exposures, Causal KG | "See how macro affects YOUR holdings" |
| **Week 2** | Patterns + Multi-Currency | Pattern chaining, CAD/EUR support | "Understand causality + International-ready" |
| **Week 3** | Portfolio-Centric UI | Portfolio as PRIMARY view | "Portfolio-first with macro integrated" |
| **Week 4** | Transparency | Execution traces, Provenance | "Audit everything, perfect for taxes" |
| **Week 5** | Ratings + News | Dividend safety, News impact | "Professional analytics for decisions" |
| **Week 6** | Advanced Features | Factor exposure, Correlation | "Bloomberg-level tools at consumer price" |
| **Weeks 7-8** | Launch Prep | Testing, Beta recruitment | "50-100 individual investors using it" |

---

## WEEK 0: LEDGER & PRICING INFRASTRUCTURE ⚡

### Overview
**Focus**: Professional accounting foundation for individual portfolios
**Outcome**: Individual investors can upload CSV → Beancount ledger with lot-level tracking

### Day 1: Beancount Research & Design
**Tasks**:
- [ ] Research python-beancount library documentation
- [ ] Design Beancount ledger structure for individual investors
  - Account structure: `Assets:Brokerage:RRSP`, `Assets:Brokerage:TFSA`, `Assets:Brokerage:Taxable`
  - Transaction types: Buy, Sell, Dividend, Split, Transfer
  - Multi-currency support: CAD, USD, EUR, GBP
- [ ] Design CSV upload schema
  - Support: Questrade CSV, Interactive Brokers CSV, Generic CSV
  - Required fields: Date, Action, Ticker, Shares, Price, Currency, Account
- [ ] Create sample Beancount ledger for Alex (Canadian tech investor, 32 positions)

**Deliverable**: Design document (`docs/beancount_ledger_design.md`)

**Individual Investor Value**: "We'll support your broker's CSV format (Questrade, IB, generic)"

---

### Day 2: Beancount CSV Parser Implementation
**Tasks**:
- [ ] Install python-beancount: `pip install beancount`
- [ ] Implement CSV parser: `core/ledger/csv_parser.py`
  - Function: `parse_questrade_csv(file_path) -> List[Transaction]`
  - Function: `parse_ib_csv(file_path) -> List[Transaction]`
  - Function: `parse_generic_csv(file_path) -> List[Transaction]`
- [ ] Implement Beancount generator: `core/ledger/beancount_generator.py`
  - Function: `generate_ledger(transactions) -> str` (Beancount file content)
- [ ] Handle edge cases:
  - Stock splits (adjust historical prices)
  - Dividends (income vs return of capital)
  - Transfers between accounts

**Deliverable**: CSV → Beancount ledger working

**Test**: Parse Alex's Questrade CSV (32 positions) → Generate Beancount file → Validate with `bean-check`

---

### Day 3: Beancount Integration with Trinity
**Tasks**:
- [ ] Create `core/ledger/ledger_service.py`
  - Class: `LedgerService`
  - Method: `load_from_csv(file_path, broker="generic") -> Portfolio`
  - Method: `get_positions(ledger, as_of_date) -> List[Position]`
  - Method: `get_transactions(ledger, start_date, end_date) -> List[Transaction]`
- [ ] Integrate with existing Portfolio model (`models/portfolio.py`)
  - Add: `ledger_file_path` field
  - Add: `ledger_commit_hash` field (for reproducibility)
- [ ] Create storage directory: `storage/ledgers/<user_id>/`
- [ ] Git-back ledgers (for version control + audit trail)

**Deliverable**: Individual investors can upload CSV → Trinity creates Beancount ledger

**Test**: Upload Alex's CSV → Verify Portfolio object has correct holdings + lot-level tracking

---

### Day 4: Pricing Pack Service Design & Implementation
**Tasks**:
- [ ] Design pricing pack schema: `storage/pricing_packs/<pack_id>.json`
```json
{
  "id": "2025-10-21_close",
  "policy": "WM_4pm",
  "created_at": "2025-10-21T16:00:00Z",
  "prices": {
    "AAPL": {"price": 178.42, "currency": "USD", "source": "Polygon"},
    "NVDA": {"price": 425.67, "currency": "USD", "source": "Polygon"}
  },
  "fx_rates": {
    "USD/CAD": {"rate": 1.3521, "source": "WM_4pm", "timestamp": "2025-10-21T16:00:00Z"},
    "USD/EUR": {"rate": 0.9234, "source": "WM_4pm", "timestamp": "2025-10-21T16:00:00Z"}
  }
}
```
- [ ] Implement `core/pricing/pricing_pack_service.py`
  - Function: `create_pack(pack_id, tickers, fx_pairs) -> PricingPack`
  - Function: `get_pack(pack_id) -> PricingPack`
  - Function: `apply_pack(portfolio, pack_id) -> ValuationSnapshot`
- [ ] Integrate with OpenBB/yfinance for price fetching
- [ ] Integrate with FX data source (FRED or FMP)

**Deliverable**: Pricing pack service creates frozen price snapshots

**Test**: Create pack "2025-10-21_close" → Verify all prices + FX rates captured

---

### Day 5: Pricing Pack Integration & Reproducibility Testing
**Tasks**:
- [ ] Integrate pricing packs with Portfolio valuation
  - Method: `Portfolio.value_as_of(pack_id) -> Decimal`
  - Ensures: Same pack ID = same valuation (reproducibility)
- [ ] Add provenance to all valuations:
  - `valuation_metadata`: {"pack_id": "2025-10-21_close", "ledger_commit": "a3f9d2c"}
- [ ] Implement UI upload widget (Streamlit)
  - File uploader: CSV → Beancount ledger
  - Display: Holdings table with lot-level breakdown
- [ ] Create daily pricing pack generation (manual for now, automate later)

**Deliverable**: Individual investors upload CSV → See portfolio valued with frozen pricing pack

**Test**:
- Upload Alex's portfolio
- Value with pack "2025-10-21_close"
- Revalue with same pack → Verify exact same result (reproducibility for taxes)

**Individual Investor Value**: "Perfect for tax season. Same pricing pack = same valuation every time."

---

## WEEK 1: MACRO EXPOSURES + CAUSAL KG ⚡

### Overview
**Focus**: Show individual investors how macro affects THEIR specific holdings
**Outcome**: "Your portfolio: -1.2 rate beta (HIGH). Rate hike hurts YOUR holdings."

### Day 1: Macro Exposures Dataset Research & Design
**Tasks**:
- [ ] Research macro factor betas:
  - Duration beta (rate sensitivity): Research papers, Fed studies
  - Inflation beta: Historical regressions (CPI vs stock returns)
  - FX beta (USD strength): Currency correlation analysis
  - Commodity beta: Oil/gold correlation
- [ ] Design `storage/knowledge/macro_exposures.json`:
```json
{
  "_meta": {
    "version": "1.0",
    "last_updated": "2025-10-22",
    "source": "Research papers + Historical regressions (10 years)"
  },
  "exposures": {
    "AAPL": {
      "duration_beta": -0.8,   // Hurt by rising rates
      "inflation_beta": -0.3,  // Slight benefit from disinflation
      "fx_beta": -0.5,         // Hurt by strong USD (international revenue)
      "commodity_beta": 0.1,   // Neutral to oil/gold
      "recession_beta": 0.75   // High cyclical exposure
    }
  }
}
```
- [ ] Prioritize coverage: S&P 500 + TSX 60 + FTSE 100 (covers most individual investors)
- [ ] Target: 500+ stocks covered

**Deliverable**: Design document with methodology + sample exposures

---

### Day 2: Macro Exposures Dataset Creation
**Tasks**:
- [ ] Calculate macro exposures for 500+ stocks:
  - S&P 500: Top 200 by market cap (covers 80% of index)
  - TSX 60: All (Canadian investors like Alex)
  - FTSE 100: Top 50 (European investors like Maria)
- [ ] Use historical regressions (10 years):
  - Duration beta: Stock return vs 10Y yield change
  - Inflation beta: Stock return vs CPI change
  - FX beta: Stock return vs USD index
  - Recession beta: Stock drawdown in 2008, 2020
- [ ] Validate: Sanity check results (Tech should have negative duration beta, Energy positive commodity beta)
- [ ] Save: `storage/knowledge/macro_exposures.json`

**Deliverable**: 500+ stocks with macro factor betas

**Test**: Verify AAPL has negative duration beta, XLE (energy) has positive commodity beta

---

### Day 3: Causal Knowledge Graph Refactor (Part 1)
**Tasks**:
- [ ] Refactor `core/knowledge_graph.py` to support causal edges
- [ ] Add method: `add_causal_edge(source, relationship, target, elasticity=None, evidence=None)`
  - Example: `kg.add_causal_edge("Fed_Rate", "increases", "Tech_Valuations", elasticity=-0.8, evidence="Historical correlation 0.85")`
- [ ] Add method: `query_causal_chain(source, target) -> List[CausalEdge]`
  - Example: `kg.query_causal_chain("Fed_Rate", "AAPL_Valuation")`
  - Returns: `[("Fed_Rate", "increases", "Treasury_Yield", 0.9), ("Treasury_Yield", "increases", "Discount_Rate", 1.0), ("Discount_Rate", "decreases", "AAPL_Valuation", -0.8)]`
- [ ] Update graph schema to store elasticities as edge attributes

**Deliverable**: KG supports causal edges with elasticities

---

### Day 4: Causal Knowledge Graph Seeding (Part 2)
**Tasks**:
- [ ] Create `storage/knowledge/causal_relationships.json`:
```json
{
  "_meta": {
    "version": "1.0",
    "last_updated": "2025-10-25",
    "source": "Economic theory + Historical data"
  },
  "relationships": [
    {
      "source": "Fed_Rate",
      "relationship": "increases",
      "target": "Treasury_Yield_10Y",
      "elasticity": 0.9,
      "evidence": "10Y yield follows Fed Funds with 0.9 correlation"
    },
    {
      "source": "Treasury_Yield_10Y",
      "relationship": "increases",
      "target": "Equity_Discount_Rate",
      "elasticity": 1.0,
      "evidence": "DCF model: Discount rate = Risk-free rate + Equity risk premium"
    },
    {
      "source": "Equity_Discount_Rate",
      "relationship": "increases",
      "target": "Tech_Sector_Valuation",
      "elasticity": -0.8,
      "evidence": "Tech has high duration (long cash flows)"
    }
  ]
}
```
- [ ] Seed 100+ causal relationships:
  - Macro → Sector (Fed Rate → Banks, Oil → Energy, USD → Exporters)
  - Sector → Company (Sector performance → Individual stock)
  - Macro → Company (Recession → Cyclical stocks)

**Deliverable**: 100+ causal relationships loaded into KG

---

### Day 5: Integration Testing (Macro + KG)
**Tasks**:
- [ ] Test macro exposures loading:
  - `loader.get_dataset("macro_exposures")`
  - Verify 500+ stocks loaded
- [ ] Test causal KG queries:
  - `kg.query_causal_chain("Fed_Rate", "AAPL")`
  - Returns: Fed Rate → Treasury Yield → Discount Rate → AAPL Valuation (with elasticities)
- [ ] Calculate portfolio-level macro exposure:
  - Function: `calculate_portfolio_duration_beta(portfolio, macro_exposures) -> float`
  - Example: Alex's portfolio (60% tech) → -1.2 duration beta
- [ ] Create test pattern: `portfolio_macro_exposure`
  - Input: Portfolio
  - Output: "Your portfolio: Duration beta -1.2 (HIGH). Rate hike hurts YOUR holdings."

**Deliverable**: Individual investors see "Your portfolio: -1.2 rate beta (HIGH)"

**Individual Investor Value**: "Understand how YOUR specific holdings react to macro changes (not generic advice)."

---

## WEEK 2: PATTERN INTEGRATION + MULTI-CURRENCY ⚡

### Overview
**Focus**: Sophisticated workflows + International investor support
**Outcome**: "Recession scenario: Your portfolio -8.2%. Multi-currency: +5.2% CAD = Local +8.1% + FX -2.3%"

### Day 1: Macro-Fundamental Patterns (Part 1)
**Tasks**:
- [ ] Create pattern: `patterns/workflows/portfolio_macro_scenario.json`
  - Input: Portfolio + Scenario ("recession", "rate_hike", "inflation_spike")
  - Steps:
    1. Load macro exposures for portfolio holdings
    2. Apply scenario shock (e.g., "recession" = unemployment 6%, GDP -2%)
    3. Calculate per-holding impact using elasticities
    4. Aggregate to portfolio-level impact
  - Output: "Recession scenario: Your portfolio -8.2%. Top losers: NVDA -12%, TSLA -15%"
- [ ] Test with Alex's portfolio (tech-heavy, 32 positions)

**Deliverable**: Individual investors run "What if recession?" scenario

---

### Day 2: Macro-Fundamental Patterns (Part 2)
**Tasks**:
- [ ] Create pattern: `patterns/smart/macro_impact_on_stock.json`
  - Input: Ticker + Macro change (e.g., "Fed_Rate +0.5%")
  - Steps:
    1. Query causal KG for chain (Fed Rate → ... → Stock)
    2. Load stock's macro exposures
    3. Calculate impact using elasticities
    4. Synthesize explanation
  - Output: "AAPL: Fed rate +0.5% → -3.2% estimated impact. Chain: Fed Rate → Discount Rate (-0.8 beta) → Valuation"
- [ ] Create pattern: `patterns/workflows/regime_aware_risk.json`
  - Input: Portfolio + Current macro regime
  - Adjusts risk model parameters based on regime (e.g., correlations increase in recession)

**Deliverable**: Individual investors understand causality ("WHY does rate hike hurt AAPL?")

---

### Day 3: Pattern Chaining Implementation
**Tasks**:
- [ ] Enhance `core/pattern_engine.py` to support pattern composition
- [ ] Add: Pattern outputs can reference other pattern results
  - Example: `portfolio_macro_scenario` uses output of `detect_macro_regime`
- [ ] Implement shared context:
  - `PatternContext`: Stores intermediate results across pattern chain
  - Pattern A output → Stored in context → Pattern B input
- [ ] Create composite pattern: `smart_morning_briefing`
  - Chains: `detect_macro_regime` → `portfolio_macro_exposure` → `portfolio_macro_scenario` → `news_impact` → Synthesize briefing
  - Output: "Morning Briefing for Alex: Macro regime Late-cycle (recession risk 35%). Your portfolio recession beta 0.72 (HIGH). If recession hits, expect -8% impact. Overnight news: NVDA earnings beat (+2% premarket)."

**Deliverable**: Pattern chaining enables sophisticated workflows

**Individual Investor Value**: "One-click morning briefing customized to YOUR portfolio."

---

### Day 4: Multi-Currency Support (Part 1 - Attribution)
**Tasks**:
- [ ] Create `core/currency/currency_attribution.py`
- [ ] Implement `CurrencyAttribution` class:
  - Method: `decompose_return(local_return, fx_return) -> dict`
    - Returns: {"local": float, "fx": float, "interaction": float, "total": float}
    - Formula: Total = Local + FX + (Local × FX)
- [ ] Support base currencies: CAD, USD, EUR, GBP
- [ ] Integrate with pricing packs (FX rates frozen per pack)
- [ ] Example: Maria's portfolio (EUR base, holds US dividend stocks)
  - AAPL: +5% USD (local) + -2% EUR/USD (FX) = +2.9% EUR total

**Deliverable**: Multi-currency attribution working

---

### Day 5: Multi-Currency Support (Part 2 - UI Integration)
**Tasks**:
- [ ] Add base currency selector to Portfolio settings
  - Dropdown: CAD, USD, EUR, GBP
- [ ] Update Portfolio valuation to use base currency
  - Display: Holdings in base currency (with FX rate shown)
  - Example: "AAPL: $178.42 USD = $241.23 CAD (FX: 1.3521)"
- [ ] Add Currency Attribution panel to Portfolio Overview
  - Shows: "YTD return: +5.2% CAD = Local +8.1% USD + FX -2.3% + Interaction -0.6%"
- [ ] Test with Maria's EUR-based portfolio

**Deliverable**: International investors see accurate returns in their base currency

**Individual Investor Value**: "Canadian? European? We handle multi-currency properly (local + FX + interaction)."

---

## WEEK 3: PORTFOLIO-CENTRIC UI ⚡

### Overview
**Focus**: Portfolio as PRIMARY dashboard (not afterthought)
**Outcome**: "See YOUR holdings through a macro lens. Every number is about YOUR portfolio."

### Day 1: Portfolio Overview Dashboard (Part 1)
**Tasks**:
- [ ] Redesign Portfolio tab as PRIMARY dashboard
- [ ] Create Holdings Table with macro columns:
  - Columns: Ticker | Name | Value | Weight | Duration Beta | Recession Beta | FX Beta
  - Sort by: Weight (default), Duration Beta, Recession Beta
  - Aggregate row: Portfolio totals (weighted average betas)
- [ ] Add Macro Regime Context panel:
  - Display: "Current regime: Late-cycle (recession risk 35%)"
  - Display: "Your portfolio recession beta: 0.72 (HIGH)"
  - Color-code: GREEN (beta < 0.5), YELLOW (0.5-0.7), RED (>0.7)

**Deliverable**: Portfolio table shows macro betas for every holding

---

### Day 2: Portfolio Overview Dashboard (Part 2 - Visualizations)
**Tasks**:
- [ ] Add Portfolio Exposure Chart (bar chart)
  - X-axis: Macro factors (Duration, Inflation, FX, Commodity, Recession)
  - Y-axis: Portfolio beta
  - Benchmark: S&P 500 average (show comparison)
- [ ] Add Top Exposures widget:
  - "Top recession risk: NVDA ($75K, 0.85 beta), TSLA ($50K, 0.9 beta)"
  - "Top rate sensitivity: AAPL ($120K, -0.8 beta)"
- [ ] Add Scenario Impact widget:
  - Quick scenarios: "Recession", "Rate hike +0.5%", "Inflation spike +2%"
  - Click → Shows estimated portfolio impact

**Deliverable**: Individual investors see portfolio-level macro exposures at a glance

---

### Day 3: Macro-Annotated Stock Analysis
**Tasks**:
- [ ] Enhance Stock Analysis page with macro context
- [ ] Add Macro Sensitivity panel:
  - "NVDA: Duration beta -0.7 (HIGH). Recent Fed hike = ~-3.5% valuation impact"
  - "Recession exposure: 0.85 (HIGH). If unemployment rises to 6%, expect -12% impact"
  - "FX exposure: -0.6 (MODERATE). Strong USD hurts (40% international revenue)"
- [ ] Add Causal Chain visualization:
  - Click "Why does Fed rate hike hurt NVDA?"
  - Shows: Fed Rate → Treasury Yield → Discount Rate → Tech Valuation (with elasticities)
- [ ] Link to portfolio: "You hold $75K NVDA → Fed hike impact = -$2,625"

**Deliverable**: Stock analysis shows macro context + portfolio link

**Individual Investor Value**: "See how macro affects THIS stock AND your specific position."

---

### Day 4: Scenario Analysis Widget
**Tasks**:
- [ ] Create Scenario Analysis widget (Portfolio Overview)
- [ ] Dropdown: Scenario selection
  - Recession (unemployment 6%, GDP -2%)
  - Rate hike (+0.5%)
  - Rate cut (-0.5%)
  - Inflation spike (+2%)
  - Custom (user defines shocks)
- [ ] Display: Impact table
  - Columns: Holding | Current Value | Scenario Value | Impact ($) | Impact (%)
  - Aggregate: Portfolio total impact
- [ ] Display: Winners & Losers
  - "Winners: XLE +$5K, JPM +$3K"
  - "Losers: NVDA -$9K, AAPL -$6K"

**Deliverable**: Individual investors run "What if?" scenarios in one click

**Individual Investor Value**: "Understand how YOUR portfolio reacts to different macro scenarios."

---

### Day 5: Dashboard Integration (Economic ↔ Portfolio)
**Tasks**:
- [ ] Link Economic Dashboard to Portfolio exposure
- [ ] Add "Your Exposure" panel to Economic Dashboard:
  - "Recession risk: 35% → Your portfolio recession beta: 0.72 (HIGH)"
  - Click → Navigates to Portfolio Overview with recession column highlighted
- [ ] Add macro alerts:
  - "Recession risk increased from 30% → 35%. Your portfolio exposure: 0.72 (HIGH)"
  - Click → Shows which holdings contribute most to recession risk
- [ ] Add breadcrumbs: Economic Dashboard → Portfolio → Stock Analysis (connected flow)

**Deliverable**: Portfolio-centric design with macro fully integrated

**Individual Investor Value**: "Everything is connected. See how macro flows to YOUR portfolio."

---

## WEEK 4: TRANSPARENCY UI WITH PROVENANCE ⚡

### Overview
**Focus**: Show individual investors HOW analysis works
**Outcome**: "Understand HOW we reached every conclusion. Perfect for taxes/audits."

### Day 1: Execution Trace Panel (Part 1 - Design)
**Tasks**:
- [ ] Design Execution Trace panel (expandable sidebar)
- [ ] Components:
  - Pattern info (name, version, trigger)
  - Steps executed (with timing)
  - Agent invoked (with capability used)
  - Data sources (with timestamps)
  - KG causal chain (if applicable)
  - Confidence score (with breakdown)
- [ ] Example trace for `smart_stock_analysis`:
```
Pattern: smart_stock_analysis (v1.2)
Executed: Oct 21, 2025 14:32 UTC
Confidence: 8.2/10

Steps:
1. ✅ Fetch fundamentals (0.3s)
   Agent: data_harvester (can_fetch_fundamentals)
   Data: FMP API (AAPL financials, updated Oct 20, 2025)

2. ✅ Calculate DCF (0.5s)
   Agent: financial_analyst (can_calculate_dcf)
   Data: FRED (10Y yield: 4.2%), FMP (AAPL FCF: $95B)
   Result: Fair value $185/share

3. ✅ Macro adjustment (0.2s)
   Agent: pattern_spotter (can_detect_macro_regime)
   KG causal chain: Fed Rate 5.3% → Discount rate ↑ → Tech valuation ↓
   Adjustment: -3.5% (duration beta -0.8)
   Result: Adjusted fair value $178/share

4. ✅ Synthesize (0.1s)
   Agent: claude (can_synthesize_analysis)
   Output: "AAPL fair value $178 (current $178). Macro headwind from rates."
```

**Deliverable**: Execution trace design

---

### Day 2: Execution Trace Panel (Part 2 - Implementation)
**Tasks**:
- [ ] Implement `core/execution_trace.py`
  - Class: `ExecutionTrace` (stores pattern execution metadata)
  - Method: `add_step(name, agent, capability, data_sources, result, duration)`
  - Method: `to_dict() -> dict` (for UI rendering)
- [ ] Modify `PatternEngine` to record execution traces
  - Every pattern execution → Creates ExecutionTrace
  - Store in session state (Streamlit)
- [ ] Create Streamlit component: `ui/execution_trace_panel.py`
  - Expandable sidebar (collapsed by default)
  - Click pattern result → Shows trace

**Deliverable**: Execution traces captured and displayable

---

### Day 3: Provenance Display
**Tasks**:
- [ ] Add provenance metadata to all metrics
- [ ] Components:
  - Pricing pack ID (e.g., "2025-10-21_close")
  - Ledger commit hash (e.g., "a3f9d2c")
  - Data sources with timestamps (e.g., "FMP: Oct 20, 2025 16:00 UTC")
  - Calculation timestamp (e.g., "Calculated: Oct 21, 2025 14:32 UTC")
- [ ] Display provenance on hover (tooltip)
  - Example: Hover over "AAPL: $178.42"
  - Tooltip: "Pricing pack: 2025-10-21_close | Source: Polygon | FX: USD/CAD 1.3521 WM 4pm | Calculated: Oct 21, 14:32 UTC"
- [ ] Add "Audit Info" panel to Portfolio Overview
  - Shows: Ledger commit, Pricing pack, Last updated

**Deliverable**: Every metric has traceable provenance

**Individual Investor Value**: "Perfect for tax season. Show your accountant the exact price + FX rate used."

---

### Day 4: Click-to-Explain (Causal Chain Visualization)
**Tasks**:
- [ ] Implement click-to-explain for macro-derived metrics
- [ ] Example: Click "Recession exposure: 0.72"
  - Modal opens with:
    - KG causal chain: Unemployment ↑ → Consumer spending ↓ → Tech sales ↓ → NVDA ↓
    - Calculation breakdown:
      - NVDA: 0.85 recession beta × 50% portfolio weight = 0.425
      - AAPL: 0.75 recession beta × 30% portfolio weight = 0.225
      - Others: 0.4 avg × 20% weight = 0.08
      - Total: 0.73 (weighted average)
    - Confidence: 8.5/10 (strong historical correlation)
- [ ] Create reusable component: `ui/causal_chain_modal.py`

**Deliverable**: Individual investors understand HOW metrics are calculated

**Individual Investor Value**: "Understand the 'why' behind every number. Educational + transparent."

---

### Day 5: Reproducibility Testing & Export
**Tasks**:
- [ ] Test reproducibility:
  - Same pricing pack + ledger = same results
  - Rerun analysis 10 times → Verify exact same output
- [ ] Implement export functionality:
  - Export portfolio valuation report (PDF/Excel)
  - Include: Holdings, Valuations, Pricing pack ID, Ledger commit, Data sources, Timestamps
  - Purpose: Tax documentation, quarterly reviews
- [ ] Add "Export Audit Report" button (Portfolio Overview)
- [ ] Test with Alex's portfolio (accountant can verify pricing pack)

**Deliverable**: Full transparency + auditability for individual investors

**Individual Investor Value**: "Reproducible, auditable, perfect for taxes. Your accountant will love it."

---

## WEEK 5: CUSTOM RATINGS + NEWS IMPACT ⚡

### Overview
**Focus**: Professional analytics for individual decision-making
**Outcome**: "Dividend safety: 7.5/10. Moat: 8.2/10. Recession resilience: 4.1/10. Plus portfolio-weighted news."

### Day 1: Dividend Safety Rating
**Tasks**:
- [ ] Create pattern: `patterns/analysis/dividend_safety_rating.json`
- [ ] Rating components:
  - Payout ratio (< 50% = good, 50-70% = ok, >70% = risky)
  - FCF coverage (FCF / Dividends > 1.5x = good)
  - Balance sheet (Net cash = good, Net debt > 3x EBITDA = risky)
  - Dividend growth history (10-year streak = good)
  - Macro sensitivity (recession beta < 0.5 = defensive)
- [ ] Scoring: 0-10 scale
  - < 4: WEAK (cut likely in recession)
  - 4-6: MODERATE (monitor closely)
  - 6-8: STRONG (safe through recession)
  - 8-10: EXCELLENT (dividend aristocrat quality)
- [ ] Test with dividend stocks (JNJ, PG, AAPL, T)

**Deliverable**: Dividend safety rating for individual stocks

**Individual Investor Value**: "Maria (dividend investor) sees which dividends are safe in recession."

---

### Day 2: Moat Strength & Recession Resilience Ratings
**Tasks**:
- [ ] Create pattern: `patterns/analysis/moat_strength_rating.json`
- [ ] Rating components:
  - ROIC (> 15% sustained = wide moat)
  - Gross margins (> 40% = pricing power)
  - Market share (top 3 in industry = strong)
  - Network effects (platform business = moat)
  - Switching costs (enterprise software = moat)
- [ ] Create pattern: `patterns/analysis/recession_resilience_rating.json`
- [ ] Rating components:
  - Historical drawdowns (2008, 2020 performance)
  - Recession beta (< 0.5 = resilient)
  - Sector (consumer staples = resilient, tech = cyclical)
  - Balance sheet (net cash = resilient)
- [ ] Test with diverse stocks (AAPL, NVDA, PG, XOM)

**Deliverable**: Moat + Recession resilience ratings

---

### Day 3: Rating Display & Click-to-Explain
**Tasks**:
- [ ] Add Rating panel to Stock Analysis page
  - Display badges:
    - "Dividend Safety: 7.5/10 🟢 (STRONG)"
    - "Moat Strength: 8.2/10 🟢 (WIDE)"
    - "Recession Resilience: 4.1/10 🟡 (WEAK)"
- [ ] Click badge → Shows breakdown
  - Example: Click "Dividend Safety: 7.5/10"
  - Modal shows:
    - Payout ratio: 42% (good) → +2 points
    - FCF coverage: 1.8x (strong) → +2 points
    - Balance sheet: Net cash $50B → +1.5 points
    - Dividend growth: 10-year streak → +2 points
    - Macro sensitivity: -0.3 recession beta → +0.5 points (slightly defensive)
    - Total: 7.5/10
- [ ] Add Rating badges to Portfolio Overview (per holding)

**Deliverable**: Individual investors see ratings with transparent breakdown

**Individual Investor Value**: "Understand WHY AAPL gets 7.5/10 dividend safety (not black box)."

---

### Day 4: News Impact Analysis (Part 1 - Fetching)
**Tasks**:
- [ ] Integrate NewsAPI for portfolio-relevant news
- [ ] Create `services/news_service.py`
  - Method: `fetch_portfolio_news(portfolio) -> List[NewsArticle]`
  - Fetch news for all holdings (last 24 hours)
  - Filter: Relevance > 0.7 (avoid noise)
- [ ] Use Claude for sentiment analysis:
  - Method: `analyze_sentiment(article) -> dict`
  - Returns: {"ticker": "AAPL", "sentiment": 0.8, "summary": "Earnings beat expectations"}
- [ ] Aggregate to portfolio level:
  - Portfolio-weighted sentiment (holding weight × sentiment)

**Deliverable**: Portfolio-relevant news with sentiment analysis

---

### Day 5: News Impact Analysis (Part 2 - Display)
**Tasks**:
- [ ] Add News Impact panel to Portfolio Overview
  - Display: "Portfolio sentiment: 6.2/10 (POSITIVE)"
  - Display: Top positive news: "AAPL earnings beat (+0.8 sentiment, 25% portfolio weight)"
  - Display: Top negative news: "TSLA production miss (-0.3 sentiment, 10% portfolio weight)"
- [ ] Add News panel to Stock Analysis page
  - Display: Recent news for this stock (last 7 days)
  - Display: Sentiment trend chart (7-day rolling average)
- [ ] Test with Alex's portfolio (tech stocks get lots of news)

**Deliverable**: Individual investors see portfolio-weighted news sentiment

**Individual Investor Value**: "See how overnight news affects YOUR portfolio (not generic headlines)."

---

## WEEK 6: ADVANCED FEATURES + POLISH ⚡

### Overview
**Focus**: Bloomberg-level analytics at consumer price
**Outcome**: "Factor exposure, correlation matrix, performance attribution. Professional tools for $149/mo."

### Day 1: Factor Exposure Analysis
**Tasks**:
- [ ] Create `patterns/analysis/factor_exposure_analysis.json`
- [ ] Calculate portfolio factor exposures:
  - Value (P/E, P/B)
  - Growth (revenue growth, earnings growth)
  - Momentum (12-month return)
  - Quality (ROIC, debt/equity)
  - Size (market cap)
- [ ] Compare to S&P 500 benchmark:
  - Portfolio factor tilts vs SPY
  - Example: "Your portfolio: Growth tilt +0.6, Momentum tilt +0.4, Value tilt -0.3"
- [ ] Visualize: Radar chart (5 factors, portfolio vs benchmark)

**Deliverable**: Factor exposure analysis working

---

### Day 2: Correlation Matrix & Concentration Risk
**Tasks**:
- [ ] Calculate holdings correlation matrix (last 12 months)
- [ ] Create heatmap visualization (Plotly)
  - Color: Red (high correlation >0.8), Yellow (moderate 0.5-0.8), Green (low <0.5)
  - Highlight: High correlation pairs (concentration risk)
- [ ] Add Concentration Risk warning:
  - "Your 5 cloud stocks (NVDA, AMD, SNOW, DDOG, NET) have 0.87 correlation → Diversification is LOW"
- [ ] Add to Portfolio Overview (expandable section)

**Deliverable**: Individual investors see correlation-based concentration risk

**Individual Investor Value**: "James (growth investor) sees his 5 cloud stocks move together → Concentration risk."

---

### Day 3: Performance Attribution
**Tasks**:
- [ ] Create `patterns/analysis/performance_attribution.json`
- [ ] Decompose portfolio returns:
  - Stock selection effect (picking winners vs sector average)
  - Sector allocation effect (overweight/underweight sectors vs benchmark)
  - FX effect (currency movement, for multi-currency portfolios)
  - Cash drag (uninvested cash opportunity cost)
  - Interaction effects
- [ ] Example: Q3 return breakdown
  - Total return: +5.2%
  - Stock selection: +3.1% (picked NVDA, outperformed tech sector)
  - Sector allocation: +2.5% (overweight tech, tech outperformed)
  - FX effect: -0.4% (strong USD hurt CAD-based portfolio)
  - Cash drag: -0.1% (5% cash earning 0%)
  - Interaction: +0.1%
- [ ] Visualize: Waterfall chart

**Deliverable**: Individual investors understand WHERE returns came from

---

### Day 4: Final Polish (UI/UX)
**Tasks**:
- [ ] Consistent styling across all pages
  - Professional color scheme (blues/grays, not garish)
  - Consistent fonts (Inter or Roboto)
  - Consistent spacing/padding
- [ ] Improve loading states:
  - Skeleton loaders (not spinners)
  - Progressive loading (show cached data, fetch fresh in background)
- [ ] Improve error messages:
  - User-friendly (not "AttributeError: 'NoneType'")
  - Actionable ("API rate limit hit. Try again in 60 seconds.")
- [ ] Mobile responsiveness (basic, not full mobile app)

**Deliverable**: Professional, polished UI

---

### Day 5: Edge Cases & Error Handling
**Tasks**:
- [ ] Handle edge cases:
  - Empty portfolio (show example portfolio)
  - Single holding (correlation matrix N/A, show message)
  - All cash (no equity analysis, show bond/cash tools)
  - Missing data (graceful degradation, show confidence 0)
- [ ] Improve error handling:
  - API failures (fallback to cached data)
  - Invalid CSV (clear error message, example CSV link)
  - Missing pricing pack (auto-create or use latest)
- [ ] Add tooltips/help text (? icons with explanations)
- [ ] Test with edge case portfolios

**Deliverable**: Robust error handling, no crashes

**Individual Investor Value**: "Platform works even when data is missing. No frustrating errors."

---

## WEEKS 7-8: BETA LAUNCH PREP ⚡

### Overview
**Focus**: Testing, documentation, beta recruitment
**Outcome**: 50-100 individual investors actively using the platform

---

## WEEK 7: TESTING & DOCUMENTATION

### Day 1: End-to-End Testing (Alex Persona)
**Tasks**:
- [ ] Simulate Alex (Canadian tech investor, 32 positions, CAD base)
- [ ] Test flow:
  1. Upload Questrade CSV → Verify Beancount ledger created
  2. Set base currency CAD → Verify multi-currency working
  3. View Portfolio Overview → Verify macro betas displayed
  4. Run scenario "Recession" → Verify -8.2% impact shown
  5. View NVDA stock analysis → Verify macro context + causal chain
  6. Check execution trace → Verify full transparency
  7. Export audit report → Verify provenance included
- [ ] Log bugs (critical vs nice-to-have)

---

### Day 2: End-to-End Testing (Maria & James Personas)
**Tasks**:
- [ ] Simulate Maria (European dividend investor, EUR base, 28 positions)
  - Test: Multi-currency attribution (EUR base, USD dividends)
  - Test: Dividend safety ratings
- [ ] Simulate James (US growth investor, 18 positions, concentrated)
  - Test: Correlation matrix (high correlation warning)
  - Test: Factor exposure (growth tilt)
- [ ] Log bugs

---

### Day 3: Bug Fixes (Critical Priority)
**Tasks**:
- [ ] Prioritize bugs:
  - P0 (blocker): Crashes, data loss
  - P1 (critical): Major features broken
  - P2 (important): UX issues
  - P3 (nice-to-have): Polish
- [ ] Fix P0 bugs (must fix for launch)
- [ ] Fix P1 bugs (should fix for launch)
- [ ] Defer P2/P3 (post-launch)

---

### Day 4: User Documentation
**Tasks**:
- [ ] Create user guides:
  - "How to upload your portfolio" (CSV format, examples)
  - "How to run a scenario analysis"
  - "How to read execution traces"
  - "Understanding ratings (dividend safety, moat, recession resilience)"
  - "Multi-currency explained (local + FX + interaction)"
- [ ] Create video tutorials (5 min each):
  - "Upload your first portfolio" (screen recording)
  - "Run your first scenario" (screen recording)
- [ ] Add help tooltips throughout UI (? icons)

---

### Day 5: Marketing Site & Demo Video
**Tasks**:
- [ ] Create landing page (simple, 1-page)
  - Hero: "The professional portfolio intelligence platform for individual investors"
  - Value props: Transparency, Causal KG, Multi-currency, Macro-aware
  - Pricing: Free tier + $149/mo professional tier
  - CTA: "Start free beta"
- [ ] Create demo video (3-5 min)
  - Show: CSV upload → Portfolio overview → Macro scenario → Execution trace
  - Emphasize: Transparency (show causal chain)
- [ ] Deploy landing page (Vercel/Netlify)

---

## WEEK 8: BETA LAUNCH

### Day 1: Beta Recruitment (Reddit, HN, Product Hunt)
**Tasks**:
- [ ] Reddit posts (r/investing, r/CanadianInvestor, r/eupersonalfinance):
  - "I built a portfolio intelligence platform that shows macro→stock causality. Looking for 50 beta testers."
  - Emphasize: Free professional tier for 3 months, transparency differentiator
- [ ] Hacker News (Show HN):
  - "Show HN: Portfolio intelligence with causal knowledge graph"
  - Technical audience appreciates architecture
- [ ] Product Hunt launch:
  - "Professional portfolio tools without Bloomberg's $24K price tag"
- [ ] Target: 100+ signups Day 1

---

### Day 2: Onboarding (1-on-1 Calls)
**Tasks**:
- [ ] Schedule 1-on-1 calls with first 20 users (15 min each)
- [ ] Help upload portfolios (troubleshoot CSV issues)
- [ ] Walk through key features (scenario analysis, execution traces)
- [ ] Collect feedback (what's confusing? what's missing?)
- [ ] Send onboarding email to remaining users (video tutorial + docs)

---

### Day 3: Early Feedback Collection
**Tasks**:
- [ ] Send survey to all beta users:
  - "What's your biggest pain point with current tools?"
  - "Which DawsOS feature is most valuable?"
  - "Would you pay $149/mo for this? Why or why not?"
  - NPS: "How likely are you to recommend to a friend?"
- [ ] Monitor usage analytics:
  - Activation: % who uploaded portfolio
  - Engagement: % who return 3+ times in first week
  - Feature usage: Which patterns most popular?
- [ ] Identify power users (high engagement, detailed feedback)

---

### Day 4: Quick Wins & Bug Fixes
**Tasks**:
- [ ] Implement quick wins from user feedback:
  - Example: "Add keyboard shortcuts"
  - Example: "Support Schwab CSV format"
  - Example: "Add GBP base currency"
- [ ] Fix critical bugs reported by users
- [ ] Deploy updates (rapid iteration)
- [ ] Communicate to users: "We listened. Here's what we fixed."

---

### Day 5: Week 1 Retrospective & Roadmap Adjustment
**Tasks**:
- [ ] Analyze Week 1 metrics:
  - Signups: 100+ (target met?)
  - Activation: 80% (target met?)
  - Engagement: 20% return 3+ times (target met?)
  - Feedback: NPS > 40? (qualitative: "I'd pay for this"?)
- [ ] Identify: What's working? What's not?
- [ ] Adjust roadmap for Weeks 9-12 (PMF validation phase)
- [ ] Communicate to team: "Here's what we learned. Here's what's next."

---

## 🎯 SUCCESS METRICS (8-Week Roadmap)

### Week 8 (Beta Launch) - MUST ACHIEVE:
- ✅ **50-100 signups** (sophisticated individual investors)
- ✅ **80% activation** (uploaded portfolio, ran ≥1 pattern)
- ✅ **20% engagement** (return 3+ times in first week)
- ✅ **5+ users** say "I'd pay $149/mo for this" (qualitative PMF signal)

### Week 12 (PMF Validation) - TARGETS:
- ✅ **100-200 users** total (50% from referrals = viral)
- ✅ **20% conversion** to professional tier ($149/mo)
- ✅ **$3K-15K MRR** (20-100 paying users)
- ✅ **80% retention** after month 1
- ✅ **NPS > 40** (professionals recommend to peers)

### Week 20 (Scale Decision) - TARGETS:
- ✅ **$15K-30K MRR** (100-200 professional tier users)
- ✅ **60% retention** after month 3 (strong PMF signal)
- ✅ **Clear use cases** (tax season, quarterly reviews, scenario analysis)

**If metrics hit**: Raise seed ($500K-1M), migrate to scale infrastructure

---

## 🚧 DEFERRED (Post-8 Weeks)

### Not in MVP (Add if PMF Validated):
- Advisor features (multi-client, white-label)
- Automated portfolio sync (Questrade/IB APIs)
- Mobile app (iOS/Android)
- Advanced analytics (options, backtesting, tax-loss harvesting)
- Database migration (Postgres + TimescaleDB)
- Service layer (FastAPI)
- Background workers (Celery)

---

## 📋 SUMMARY

**8-Week Foundation+ Roadmap for Individual Investors**:
- Week 0: Beancount + Pricing packs (professional infrastructure)
- Week 1: Macro exposures + Causal KG (understand cause/effect)
- Week 2: Pattern integration + Multi-currency (sophisticated + international)
- Week 3: Portfolio-centric UI (portfolio-first design)
- Week 4: Transparency UI (full auditability)
- Week 5: Ratings + News (professional analytics)
- Week 6: Advanced features + Polish (Bloomberg-level)
- Weeks 7-8: Testing + Beta launch (50-100 users)

**Target User**: Professional and sophisticated individual investors ($250K-$10M portfolios)

**Differentiation**: Transparency + Causal KG + Multi-currency + Professional infrastructure

**Pricing**: $149/mo professional tier (between Morningstar $250/yr and Bloomberg $24K/yr)

**Success**: $3K-15K MRR by Week 12 (20-100 paying individual investors)

---

**Status**: 🎯 **8-week roadmap ready for execution. Individual investor focus validated.**
