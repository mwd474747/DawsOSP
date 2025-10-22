# MASTER TASK LIST - Single Source of Truth
**Last Updated**: October 21, 2025 23:00 UTC
**Status**: Living document - ALL future work references this file
**Plan**: Enhanced 6.5-Week Roadmap to 100% Product Vision Alignment
**Validation**: Complete UX simulation performed, 3 critical gaps identified and addressed

---

## CRITICAL: How to Use This Document

**FOR AI ASSISTANTS (Claude)**:
1. ALWAYS read this file at start of session
2. ALWAYS add new discoveries to appropriate section
3. ALWAYS mark items complete when done
4. NEVER create separate task lists or TODO files
5. ALWAYS verify documentation accuracy against this list

**FOR DEVELOPERS**:
- This is the ONLY task tracking document
- All gaps, fixes, and TODOs are here
- Update this file, not scattered comments

---

## CURRENT STATE (Verified October 21, 2025 23:00 UTC)

### Application Status: ✅ PRODUCTION READY

**Location**: Root directory (`./`)
**Main File**: main.py (1,726 lines, fully operational)
**Status**: 100% functional, real data flowing

### Verified Inventory (Post-Audit)

```
Trinity/DawsOS/
├── agents/                  7 files
│   ├── financial_analyst.py    ✅ REGISTERED (main.py:85)
│   ├── claude.py               ✅ REGISTERED (main.py:89)
│   ├── data_harvester.py       ⚠️ NOT REGISTERED (available)
│   ├── forecast_dreamer.py     ⚠️ NOT REGISTERED (available)
│   ├── graph_mind.py           ⚠️ NOT REGISTERED (available)
│   ├── pattern_spotter.py      ⚠️ NOT REGISTERED (available)
│   └── base_agent.py           ℹ️ BASE CLASS (do not register)
│
├── core/                    13 modules + 24 actions/
│   ├── universal_executor.py   ✅ Entry point
│   ├── pattern_engine.py       ✅ Loads 16 patterns
│   ├── agent_runtime.py        ✅ 2 agents registered
│   ├── knowledge_graph.py      ✅ NetworkX (96K+ nodes)
│   ├── knowledge_loader.py     ✅ 27 datasets
│   ├── capability_router.py    ✅ Routes capabilities
│   └── actions/execute_through_registry.py  ✅ use_real_data=True (FIXED Oct 21)
│
├── patterns/                16 JSON files
│   ├── economy/            6 patterns ✅
│   ├── smart/              7 patterns ✅
│   └── workflows/          3 patterns ✅
│
├── storage/knowledge/       27 JSON datasets ✅
├── ui/                      7 components ✅
├── services/                4 services (all active) ✅
├── intelligence/            3 modules ✅
└── main.py                  ✅ 4 dashboard tabs operational
```

**Counts**:
- **7 agents** (2 registered + 4 available + 1 base class)
- **16 patterns** (economy: 6, smart: 7, workflows: 3)
- **27 knowledge datasets**
- **13 core modules + 24 actions**
- **7 UI components**
- **4 services** (all active)
- **87 total Python files**

### Completed Fixes (Oct 21, 2025)

**✅ P0 Critical Bugs Fixed**:
1. use_real_data=False → TRUE (core/actions/execute_through_registry.py:57)
   - ALL patterns now use real data (OpenBB/FRED/yfinance)
2. Empty directories deleted (patterns/analysis/, intelligence/schemas/)

---

## PRODUCT VISION (Refined Oct 21, 2025)

**Trinity/DawsOS Identity**: **Transparent Intelligence Platform** with Portfolio Management

**NOT "just a Seeking Alpha competitor"** - Trinity is:

### Three Unified Layers

**1. Beautiful Market & Economic Dashboards** (Bloomberg-Grade)
- ✅ **70% Built**: Market Overview, Economic Dashboard, Stock Analysis, Prediction Lab
- ✅ Professional Plotly visualizations, real-time data
- ❌ **Missing**: Portfolio Dashboard, Portfolio overlay on existing dashboards

**2. Transparent Conversational Intelligence** (THE Core Differentiator)
- ✅ **Architecture Complete**: Pattern engine, agent routing, knowledge graph
- ❌ **UI Missing**: Execution trace display (pattern → agent → capability → data source)
- ❌ **Missing**: Confidence scores visible, clickable steps for auditing
- **This is what makes Trinity unique** - Users SEE how the system thinks

**3. Portfolio-Centric Analysis** (Contextual Intelligence)
- ✅ **Patterns Exist**: smart_portfolio_review.json, smart_risk_analyzer.json
- ✅ **Code Ready**: analyze_portfolio_risk() in financial_analyst
- ❌ **UI Missing**: Portfolio upload, portfolio dashboard, portfolio context in chat
- ❌ **CRITICAL**: No persistence layer (portfolios not saved between sessions)

### The Integration (Dashboard ↔ Chat ↔ Portfolio)
- Click dashboard chart → Chat explains with execution trace
- Upload portfolio → All dashboards filtered by YOUR holdings
- Chat becomes portfolio-aware: "How does CPI affect MY portfolio?"
- Pattern execution → Updates dashboard + chat simultaneously

**See**: [TRINITY_PRODUCT_VISION_REFINED.md](TRINITY_PRODUCT_VISION_REFINED.md) for complete vision

---

## CRITICAL VALIDATION FINDINGS (Oct 21, 2025)

**Comprehensive UX Simulation Performed**: [PLAN_VALIDATION_AND_UX_SIMULATION.md](PLAN_VALIDATION_AND_UX_SIMULATION.md)

**Result**: Original 6-week plan is **92% complete** but **MISSING 3 CRITICAL COMPONENTS**

### Gap 1: Portfolio Persistence (P0 - BLOCKER)

**Problem**: Week 2 builds portfolio upload, but NO database/authentication
**Impact**: User uploads portfolio → Closes browser → **PORTFOLIO LOST**
**User Reaction**: "This is useless, I have to re-upload every time?"

**Missing Components**:
1. User authentication system (signup/login/session)
2. Database (SQLite with users, portfolios, positions tables)
3. Multi-portfolio support (user can have multiple portfolios)

**Solution**: **ADD WEEK 0.5 (3 days)** BEFORE Week 1
- Day 1: Database setup (SQLite + SQLAlchemy)
- Day 2: User authentication (signup/login)
- Day 3: Portfolio persistence (CRUD operations)

**Priority**: **P0 - BLOCKER** - Portfolio features are USELESS without persistence

### Gap 2: Data Export Functionality (P1 - HIGH)

**Problem**: User can analyze everything but can't save/export results
**Impact**: "How do I save this? I need a PDF for my advisor."

**Missing Components**:
1. core/report_generator.py (PDF/Excel generation)
2. "Export" buttons on all dashboards
3. Report templates (portfolio report, economic report, stock report)

**Solution**: Add to **Week 2 Day 5**
- Create core/report_generator.py
- Add export buttons
- Implement PDF generation

**Priority**: **P1 - HIGH** - Professional users need export for compliance/sharing

### Gap 3: Alert Configuration UI (P1 - HIGH)

**Problem**: Week 5 has alert_manager.py backend but NO UI to create alerts
**Impact**: Alerts fire automatically, user can't customize

**Missing Components**:
1. ui/alert_configuration.py (alert creation/management form)
2. Notification display in header
3. Alert types (market, portfolio, rating, news, economic)

**Solution**: Enhance **Week 5 Day 4-5**
- Create ui/alert_configuration.py
- Add alert CRUD UI
- Add notification icon in header

**Priority**: **P1 - HIGH** - Users want control over when they're notified

---

## ENHANCED 6.5-WEEK EXECUTION PLAN

**Original Plan**: 6 weeks (92% complete, missing persistence)
**Enhanced Plan**: 6.5 weeks (100% complete, all user needs met)

**Vision Alignment**: 60% → 100% (6.5 weeks)

---

### WEEK 0.5: Critical Infrastructure (3 days) - NEW ⭐

**Goal**: Add persistence layer and authentication BEFORE building portfolio features

**Day 1: Database Setup**
- [ ] Create core/database.py
  - SQLite with SQLAlchemy ORM
  - Schema: users, portfolios, positions, analytics_events
  ```sql
  users (id, email, password_hash, created_at)
  portfolios (id, user_id, name, created_at, updated_at)
  positions (id, portfolio_id, symbol, shares, cost_basis, purchase_date, notes)
  analytics_events (id, user_id, event_type, event_data, timestamp)
  ```
- [ ] Write migrations (Alembic)
- [ ] Test CRUD operations

**Day 2: User Authentication**
- [ ] Create core/user_manager.py
  ```python
  class UserManager:
      def create_user(email, password) -> User
      def authenticate(email, password) -> User | None
      def get_user(user_id) -> User
      def update_user(user_id, **kwargs)
  ```
- [ ] Hash passwords (bcrypt)
- [ ] Session management (st.session_state)
- [ ] Create ui/login_page.py (signup/login forms)
- [ ] Test: User can sign up, log in, session persists

**Day 3: Portfolio Persistence**
- [ ] Enhance core/portfolio_manager.py with database integration
  ```python
  class PortfolioManager:
      def create_portfolio(user_id, name) -> Portfolio
      def get_portfolios(user_id) -> List[Portfolio]
      def add_position(portfolio_id, symbol, shares, cost_basis, purchase_date)
      def get_positions(portfolio_id) -> List[Position]
      def update_position(position_id, **kwargs)
      def delete_position(position_id)
      def delete_portfolio(portfolio_id)
  ```
- [ ] Test: Portfolio saved to database, retrieved on next login
- [ ] Multi-portfolio support (dropdown to switch)

**Deliverable**: ✅ User can create account, portfolio persists between sessions

**Files Created**:
- core/database.py
- core/user_manager.py
- ui/login_page.py
- migrations/ (Alembic)

---

### WEEK 1: Transparency + Real Data (5 days)

**Goal**: Make intelligence layer TRANSPARENT and verify real data

**Day 1: Complete Cleanup** (4 hours)
- [ ] Remove dawsos/ path references
  - core/universal_executor.py lines 94-98 (delete fallback logic)
- [ ] Register 4 agents
  - main.py after line 90: data_harvester, forecast_dreamer, graph_mind, pattern_spotter
  ```python
  from agents.data_harvester import DataHarvester
  dh = DataHarvester()
  self.runtime.register_agent('data_harvester', dh, {'capabilities': [...]})
  # ... repeat for forecast_dreamer, graph_mind, pattern_spotter
  ```
- [ ] Test all 16 patterns with real data
- [ ] Verify dashboards show real market data (FRED, OpenBB, yfinance)

**Day 2-3: Build Transparency UI** (2 days)
- [ ] Create ui/execution_trace_panel.py
  - Display: Pattern → Agent → Capability → Data Source chain
  - Show confidence scores ("Data confidence: 8.5/10 - fresh from FRED")
  - Add "Explain this step" buttons (click → see raw data)
  - Show calculation breakdown
  ```python
  class ExecutionTracePanel:
      def render(self, execution_trace: Dict):
          st.subheader("Execution Trace")
          for step in execution_trace['steps']:
              with st.expander(f"Step {step['number']}: {step['description']}"):
                  st.write(f"Pattern: {step['pattern']}")
                  st.write(f"Agent: {step['agent']}")
                  st.write(f"Capability: {step['capability']}")
                  st.write(f"Data Source: {step['data_source']}")
                  st.write(f"Confidence: {step['confidence']}/10")
                  if st.button("Show Raw Data", key=f"raw_{step['number']}"):
                      st.json(step['raw_data'])
  ```
- [ ] Integrate into main.py chat panel
- [ ] Test: Every pattern shows full execution trace

**Day 4: Dashboard → Chat Integration** (1 day)
- [ ] Add "Explain" button to all dashboard charts
  ```python
  # In render_tab_economic_dashboard():
  col1, col2 = st.columns([4, 1])
  with col1:
      st.plotly_chart(recession_risk_chart)
  with col2:
      if st.button("🔍 Explain"):
          open_chat_with_context(pattern_id='recession_risk_dashboard', chart_data=...)
  ```
- [ ] onClick handler: open_chat_with_context(pattern_id, chart_data)
- [ ] Chat pre-loads: "You clicked recession risk analysis..."
- [ ] Show execution trace in chat
- [ ] Test: Economic Dashboard → Click chart → Chat explains with trace

**Day 5: Test Transparency Flow** (1 day)
- [ ] User journey: Dashboard → Click → Explain → See trace
- [ ] Verify all 16 patterns show transparent execution
- [ ] Performance: <2s trace display
- [ ] Test: "Why did you make this decision?" → System shows reasoning
- [ ] Document any issues

**Deliverable**: ✅ Transparent execution visible in chat, real data flowing, click-to-explain working

**Files Created**:
- ui/execution_trace_panel.py
- Updated: main.py (click handlers, chat integration)
- Updated: core/universal_executor.py (remove dawsos/ paths)

---

### WEEK 2: Portfolio Foundation (5 days)

**Goal**: Build portfolio features WITH persistence + export

**Day 1-2: Portfolio Manager + Upload** (2 days)
- [ ] UI connects to persistent PortfolioManager (from Week 0.5)
- [ ] Create ui/portfolio_upload.py
  ```python
  def render_portfolio_upload(user_id):
      st.subheader("Upload Portfolio")

      # Option 1: CSV upload
      uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
      if uploaded_file:
          df = pd.read_csv(uploaded_file)
          # Expected columns: symbol, shares, cost_basis, purchase_date
          portfolio = portfolio_manager.create_portfolio(user_id, "My Portfolio")
          for _, row in df.iterrows():
              portfolio_manager.add_position(portfolio.id, ...)

      # Option 2: Manual entry
      with st.form("manual_entry"):
          symbol = st.text_input("Symbol")
          shares = st.number_input("Shares", min_value=0.0)
          cost_basis = st.number_input("Cost Basis ($)", min_value=0.0)
          purchase_date = st.date_input("Purchase Date")
          if st.form_submit_button("Add Position"):
              portfolio_manager.add_position(...)
  ```
- [ ] Portfolios saved to database (Week 0.5 integration)
- [ ] Multi-portfolio support (dropdown to switch)
- [ ] Test: Upload portfolio, close browser, log back in → Portfolio still there

**Day 3: Portfolio Dashboard** (1 day)
- [ ] Create ui/portfolio_dashboard.py
  - Holdings table (symbol, shares, current value, % of portfolio, P/L, rating badges)
  - Asset allocation pie chart (by sector)
  - Performance line chart (portfolio value over time)
  - Risk metrics panel (beta, volatility, Sharpe, max drawdown, concentration)
  ```python
  def render_portfolio_dashboard(portfolio_id):
      positions = portfolio_manager.get_positions(portfolio_id)

      # Holdings table
      st.dataframe(holdings_df)  # With rating badges

      # Charts
      col1, col2 = st.columns(2)
      with col1:
          st.plotly_chart(asset_allocation_pie)
      with col2:
          st.plotly_chart(performance_line)

      # Risk metrics
      st.metric("Portfolio Beta", beta)
      st.metric("Volatility", f"{volatility}%")
      st.metric("Sharpe Ratio", sharpe)
  ```
- [ ] Test: Portfolio displays with real-time data

**Day 4: Portfolio Integration** (1 day)
- [ ] Portfolio overlay on existing dashboards
  - Market Overview: Add "Your Portfolio" line to charts
  - Economic Dashboard: Color-code indicators by YOUR risk
  ```python
  # In render_tab_market_overview():
  if st.session_state.get('portfolio_id'):
      portfolio_data = get_portfolio_overlay_data(portfolio_id)
      # Add portfolio line to SPY chart
      fig.add_trace(go.Scatter(y=portfolio_data['values'], name="Your Portfolio"))
  ```
- [ ] Portfolio-aware chat
  - Every query includes portfolio context
  - Test: "How does Fed policy affect my holdings?" → Shows impact by stock

**Day 5: Export Functionality** (1 day) - NEW ⭐
- [ ] Create core/report_generator.py
  ```python
  class ReportGenerator:
      def generate_portfolio_report(portfolio_id, format='pdf') -> bytes:
          # Template: Cover page, holdings table, charts, risk metrics, ratings
          # Use ReportLab or WeasyPrint for PDF

      def generate_economic_report(date, format='pdf') -> bytes:
          # Template: Recession risk, Fed policy, sector performance

      def generate_stock_report(symbol, format='pdf') -> bytes:
          # Template: Fundamentals, technical, news, ratings
  ```
- [ ] Add "Export" buttons to all dashboards
  ```python
  if st.button("📄 Export Portfolio Report"):
      pdf_bytes = report_gen.generate_portfolio_report(portfolio_id)
      st.download_button("Download PDF", pdf_bytes, "portfolio_report.pdf")
  ```
- [ ] Test: Export portfolio report as PDF, verify all data present

**Deliverable**: ✅ Upload portfolio → Saved to database → See on dashboards → Export as PDF

**Files Created**:
- ui/portfolio_upload.py
- ui/portfolio_dashboard.py
- core/report_generator.py
- Updated: main.py (portfolio tab, overlay logic)

---

### WEEK 3: Pattern Restoration + Integration (5 days)

**Goal**: Restore 11 critical patterns, enhance integration

**Day 1-2: Restore Analysis Patterns** (2 days)
- [ ] Create patterns/analysis/ directory
- [ ] Restore 8 analysis/ patterns from git
  ```bash
  mkdir -p patterns/analysis
  git show HEAD:dawsos/patterns/analysis/dcf_valuation.json > patterns/analysis/dcf_valuation.json
  git show HEAD:dawsos/patterns/analysis/fundamental_analysis.json > patterns/analysis/fundamental_analysis.json
  git show HEAD:dawsos/patterns/analysis/technical_analysis.json > patterns/analysis/technical_analysis.json
  git show HEAD:dawsos/patterns/analysis/sentiment_analysis.json > patterns/analysis/sentiment_analysis.json
  git show HEAD:dawsos/patterns/analysis/portfolio_analysis.json > patterns/analysis/portfolio_analysis.json
  git show HEAD:dawsos/patterns/analysis/risk_assessment.json > patterns/analysis/risk_assessment.json
  git show HEAD:dawsos/patterns/analysis/options_flow.json > patterns/analysis/options_flow.json
  git show HEAD:dawsos/patterns/analysis/greeks_analysis.json > patterns/analysis/greeks_analysis.json
  ```
- [ ] Update templates for Trinity 3.0 (use real data, capability routing)
- [ ] Test with portfolio context

**Day 3: Restore System Patterns** (1 day)
- [ ] Create patterns/system/meta/ directory
- [ ] Restore 2 system/ patterns from git
  ```bash
  mkdir -p patterns/system/meta
  git show HEAD:dawsos/patterns/system/meta/meta_executor.json > patterns/system/meta/meta_executor.json
  git show HEAD:dawsos/patterns/system/meta/execution_router.json > patterns/system/meta/execution_router.json
  ```
- [ ] Enable self-aware routing
- [ ] Test: Meta patterns route correctly

**Day 4: Restore Market Pattern + Dashboard Enhancement** (1 day)
- [ ] Create patterns/market/ directory
- [ ] Restore macro_sector_allocation.json from git
  ```bash
  mkdir -p patterns/market
  git show HEAD:dawsos/patterns/market/macro_sector_allocation.json > patterns/market/macro_sector_allocation.json
  ```
- [ ] Add mini-chart embeds in chat responses
- [ ] Add dashboard links in chat (`[View Economic Dashboard](dashboard://economic)`)
- [ ] Test: "What sectors work?" → Uses macro_sector_allocation pattern

**Day 5: Click-to-Drill-Down** (1 day)
- [ ] Click holding in portfolio → Opens detailed analysis modal
  ```python
  # In portfolio dashboard holdings table:
  if st.button(f"Analyze {symbol}"):
      st.session_state['analyze_stock'] = symbol
      # Modal shows: Fundamentals, Technical, News, Risk Contribution tabs
  ```
- [ ] Modal shows: Fundamentals, Technical, News, Risk Contribution
- [ ] Uses restored patterns (fundamental_analysis, technical_analysis, sentiment_analysis, risk_assessment)
- [ ] Test: Click AAPL → See full analysis with execution trace

**Deliverable**: ✅ 27 patterns operational (16 + 11 restored), full dashboard-chat-portfolio integration

**Files Created**:
- patterns/analysis/*.json (8 files)
- patterns/system/meta/*.json (2 files)
- patterns/market/*.json (1 file)
- Updated: main.py (modal logic, mini-charts, dashboard links)

**Total Patterns**: 27 (economy: 6, smart: 7, workflows: 3, analysis: 8, system: 2, market: 1)

---

### WEEK 4: Custom Rating Systems (5 days)

**Goal**: Build proprietary quantitative ratings for differentiation

**Day 1-2: Rating Engine** (2 days)
- [ ] Create core/rating_engine.py
  ```python
  class RatingEngine:
      def calculate_dividend_safety(symbol: str) -> Dict:
          # Returns: {score: 7.5, breakdown: {...}, confidence: 8.5, data_sources: [...]}
          # Calculation:
          # - Payout ratio (0-40%: +2.5, 40-60%: +2.0, >60%: +0-1.5)
          # - 10-year dividend growth (>10%: +2.5, 5-10%: +2.0, <5%: +1.0)
          # - FCF coverage (>2x: +2.5, 1.5-2x: +2.0, <1.5x: +1.0)
          # - Balance sheet strength (AA+: +2.5, A: +2.0, <A: +1.0)
          # Total: 0-10 score

      def calculate_moat_strength(symbol: str) -> Dict:
          # Network effects, switching costs, brand value, cost advantages
          # Returns 0-10 score with breakdown

      def calculate_recession_resilience(symbol: str) -> Dict:
          # Revenue stability, sector defensiveness, balance sheet, dividend consistency
          # Returns 0-10 score with breakdown
  ```
- [ ] Store ratings in knowledge graph with history
- [ ] Test: AAPL dividend safety = 7.5, breakdown shown

**Day 3: Rating Patterns** (1 day)
- [ ] Create patterns/ratings/ directory
- [ ] Create dividend_safety.json, moat_strength.json, recession_resilience.json
  ```json
  {
    "id": "dividend_safety",
    "steps": [
      {"action": "execute_through_registry", "capability": "can_fetch_fundamentals", "save_as": "financials"},
      {"action": "execute_through_registry", "capability": "can_calculate_rating", "params": {"rating_type": "dividend_safety", "data": "{financials}"}, "save_as": "rating"}
    ],
    "template": "Dividend Safety: {rating.score}/10\n\nBreakdown:\n- Payout ratio: {rating.breakdown.payout_ratio}\n- 10yr growth: {rating.breakdown.growth}\n- FCF coverage: {rating.breakdown.fcf}\n- Balance sheet: {rating.breakdown.balance_sheet}\n\nData sources: {rating.data_sources}\nConfidence: {rating.confidence}/10"
  }
  ```
- [ ] Each pattern shows step-by-step calculation in execution trace
- [ ] Test: Run dividend_safety pattern → See full transparency

**Day 4: Rating Display** (1 day)
- [ ] Add rating badges to portfolio holdings table
  ```python
  # In portfolio dashboard:
  df['Dividend Safety'] = df['symbol'].apply(lambda s: get_rating(s, 'dividend_safety'))
  df['Moat'] = df['symbol'].apply(lambda s: get_rating(s, 'moat_strength'))
  df['Recession'] = df['symbol'].apply(lambda s: get_rating(s, 'recession_resilience'))
  st.dataframe(df)
  ```
- [ ] Click rating → Modal shows full calculation
  ```python
  if rating_clicked:
      rating_detail = rating_engine.calculate_dividend_safety(symbol)
      st.modal("Dividend Safety: How It's Calculated")
      st.write(rating_detail['breakdown'])
      st.write(f"Data sources: {rating_detail['data_sources']}")
  ```
- [ ] Rating trend chart (historical changes over 6 months)

**Day 5: Portfolio-Level Ratings** (1 day)
- [ ] Aggregate holdings ratings
  ```python
  portfolio_avg_dividend = weighted_average([pos.rating for pos in positions], [pos.weight for pos in positions])
  st.metric("Portfolio Avg Dividend Safety", f"{portfolio_avg_dividend}/10")
  ```
- [ ] Dashboard shows distribution ("3 stocks: 8+, 1 stock: 5-7, 1 stock: <5")
- [ ] Compare to benchmarks ("Your portfolio: 6.8 vs S&P 500: 6.2")
- [ ] Test: Portfolio with 10 holdings → See aggregated ratings

**Deliverable**: ✅ Custom quantitative ratings with full transparency, visible in portfolio

**Files Created**:
- core/rating_engine.py
- patterns/ratings/*.json (3 files)
- Updated: ui/portfolio_dashboard.py (rating display)

---

### WEEK 5: News Impact + Alert System (5 days)

**Goal**: Real-time awareness with portfolio-specific news and customizable alerts

**Day 1: Portfolio-Filtered News** (1 day)
- [ ] Fetch news for all holdings (NewsAPI)
- [ ] Display in portfolio dashboard: News feed panel
  ```python
  def render_news_feed(portfolio_id):
      positions = get_positions(portfolio_id)
      symbols = [p.symbol for p in positions]

      news_articles = []
      for symbol in symbols:
          articles = news_api.get_news(symbol)
          news_articles.extend(articles)

      # Sort by: position_size × sentiment_score
      news_articles.sort(key=lambda a: a['impact_score'], reverse=True)

      for article in news_articles[:10]:
          st.write(f"{article['title']} - Impact: {article['impact_score']}")
  ```
- [ ] Sort by relevance (position_size × sentiment_score)
- [ ] Test: News feed shows AAPL/NVDA news (largest holdings first)

**Day 2-3: News Impact Analysis** (2 days)
- [ ] Create patterns/portfolio/news_impact_analysis.json
  ```json
  {
    "id": "news_impact_analysis",
    "steps": [
      {"action": "fetch_news", "params": {"symbols": "{holdings}"}, "save_as": "news"},
      {"action": "execute_through_registry", "capability": "can_analyze_sentiment", "params": {"articles": "{news}"}, "save_as": "sentiment"},
      {"action": "calculate_portfolio_impact", "params": {"sentiment": "{sentiment}", "portfolio": "{holdings}"}, "save_as": "impact"}
    ]
  }
  ```
- [ ] For each article:
  - Extract entities (which stocks mentioned)
  - Sentiment analysis (-1 to +1)
  - Portfolio impact = sentiment × position_weight
  - **Transparency**: Show calculation for each article
- [ ] UI: Color-coded impact scores (-10 to +10)
  - Green: Positive impact (+5 to +10)
  - Yellow: Neutral (-5 to +5)
  - Red: Negative (-10 to -5)
- [ ] Test: "Fed Minutes Hawkish" → Impact: -8 (negative for tech holdings)

**Day 4-5: Alert System + Configuration UI** (2 days) - ENHANCED ⭐
- [ ] Create core/alert_manager.py (backend)
  ```python
  class AlertManager:
      def create_alert(user_id, name, alert_type, condition, notify_inapp, notify_email):
          # Store in database

      def check_alerts(user_id):
          # Check conditions, trigger if met
          # Return list of triggered alerts

      def get_alerts(user_id) -> List[Alert]:
          # Retrieve user's alerts

      def trigger_alert(alert_id, data):
          # Create notification, send email if configured
  ```
- [ ] Create ui/alert_configuration.py (UI) - NEW
  ```python
  def render_alert_configuration(user_id):
      st.header("Alert Configuration")

      # Create new alert
      with st.form("new_alert"):
          name = st.text_input("Alert Name")
          alert_type = st.selectbox("Type", ["Market", "Portfolio", "Rating", "News", "Economic"])
          condition = st.text_input("Condition (e.g., VIX > 30)")
          notify_inapp = st.checkbox("In-app notification", value=True)
          notify_email = st.checkbox("Email notification", value=False)
          if st.form_submit_button("Create Alert"):
              alert_manager.create_alert(user_id, name, alert_type, condition, ...)

      # List existing alerts
      alerts = alert_manager.get_alerts(user_id)
      for alert in alerts:
          col1, col2, col3 = st.columns([3, 1, 1])
          col1.write(f"{alert.name}: {alert.condition}")
          col2.button("Edit", key=f"edit_{alert.id}")
          col3.button("Delete", key=f"delete_{alert.id}")
  ```
- [ ] Add notification icon in header
  ```python
  # In main.py header:
  notifications = alert_manager.get_unread_notifications(user_id)
  if notifications:
      if st.button(f"🔔 {len(notifications)}", key="notifications"):
          st.session_state['show_notifications'] = True
  ```
- [ ] Alert types:
  - Market: "VIX > 30", "SPY < 400"
  - Portfolio: "Portfolio value < $100K", "Portfolio beta > 1.5"
  - Rating: "Any holding dividend safety < 5", "Moat strength drops > 2 points"
  - News: "High-impact news (|impact| > 10)"
  - Economic: "Recession risk > 40%"
- [ ] Background task: Check alerts every 5 minutes
- [ ] Test: Create alert "VIX > 25" → VIX spikes to 28 → Notification fires

**Deliverable**: ✅ Real-time portfolio-specific news, customizable alerts with UI

**Files Created**:
- patterns/portfolio/news_impact_analysis.json
- core/alert_manager.py
- ui/alert_configuration.py
- Updated: main.py (notification icon, alert checking)

---

### WEEK 6: Advanced Analytics + Polish (5 days)

**Goal**: Bloomberg-level analytics, onboarding, analytics tracking

**Day 1-2: Factor Exposure Analysis** (2 days)
- [ ] Decompose portfolio into factors (value, growth, momentum, quality, size)
- [ ] Use storage/knowledge/factor_smartbeta_profiles.json
  ```python
  def calculate_factor_exposure(portfolio_id):
      positions = get_positions(portfolio_id)
      factor_profiles = knowledge_loader.get_dataset('factor_smartbeta_profiles')

      exposures = {
          'value': 0, 'growth': 0, 'momentum': 0, 'quality': 0, 'size': 0
      }
      for pos in positions:
          profile = factor_profiles.get(pos.symbol, {})
          for factor in exposures:
              exposures[factor] += pos.weight * profile.get(factor, 0)

      return exposures
  ```
- [ ] UI: Factor exposure radar chart
  ```python
  fig = go.Figure(data=go.Scatterpolar(
      r=list(exposures.values()),
      theta=list(exposures.keys()),
      fill='toself'
  ))
  st.plotly_chart(fig)
  ```
- [ ] Compare to S&P 500 benchmark
- [ ] **Transparency**: Show factor loadings by holding
- [ ] Test: Portfolio shows 60% growth, 20% quality, 10% momentum

**Day 3: Correlation Matrix** (1 day)
- [ ] Calculate correlation matrix for holdings
  ```python
  import numpy as np
  returns = get_historical_returns(symbols, period='1y')
  corr_matrix = returns.corr()
  ```
- [ ] Visual heatmap for holdings
  ```python
  fig = go.Figure(data=go.Heatmap(
      z=corr_matrix.values,
      x=corr_matrix.columns,
      y=corr_matrix.index,
      colorscale='RdYlGn'
  ))
  st.plotly_chart(fig)
  ```
- [ ] Identify concentration risk (high correlation = not truly diversified)
- [ ] **Transparency**: Click correlation → Show calculation window, data points
- [ ] Test: AAPL-MSFT correlation = 0.85 (high, both tech)

**Day 4: Performance Attribution** (1 day)
- [ ] Decompose returns: Stock selection vs sector allocation vs timing
  ```python
  def performance_attribution(portfolio_id, period='1m'):
      # Brinson attribution model
      # Returns: {
      #   'stock_selection': 2.5%,  # Picking good stocks within sectors
      #   'sector_allocation': 1.2%,  # Overweight/underweight sectors
      #   'timing': 0.3%,  # Entry/exit timing
      #   'interaction': -0.1%
      # }
  ```
- [ ] UI: Waterfall chart showing contribution to returns
  ```python
  fig = go.Figure(go.Waterfall(
      x=['Stock Selection', 'Sector Allocation', 'Timing', 'Total Return'],
      y=[2.5, 1.2, 0.3, 4.0],
      ...
  ))
  st.plotly_chart(fig)
  ```
- [ ] **Transparency**: Show calculation for each component
- [ ] Test: Portfolio return 4% → 2.5% from stock selection, 1.2% from sector

**Day 5: Rebalancing + Onboarding + Analytics** (1 day)
- [ ] Rebalancing Suggestions
  ```python
  def suggest_rebalancing(portfolio_id, target_allocation):
      current = get_current_allocation(portfolio_id)
      suggestions = []
      for sector in current:
          diff = target_allocation[sector] - current[sector]
          if abs(diff) > 5:  # >5% deviation
              suggestions.append(f"{'Buy' if diff > 0 else 'Sell'} {sector}: {abs(diff)}%")
      return suggestions
  ```
- [ ] Show projected impact on risk metrics
- [ ] **First-Time User Onboarding** - NEW ⭐
  ```python
  if st.session_state.get('first_login'):
      st.info("Welcome to Trinity! Let's take a quick tour...")
      # Interactive walkthrough (use st.info boxes with 'Next' buttons)
      # Step 1: "This is Market Overview..."
      # Step 2: "Click 'Explain' to see transparency..."
      # Step 3: "Upload your portfolio here..."
      # Step 4: "Try asking a question in chat..."
  ```
- [ ] Contextual help ("?" icons everywhere)
- [ ] **Usage Analytics Tracking** - NEW ⭐
  ```python
  def track_event(user_id, event_type, event_data):
      analytics_event = AnalyticsEvent(
          user_id=user_id,
          event_type=event_type,  # 'page_view', 'button_click', 'pattern_execution'
          event_data=json.dumps(event_data),
          timestamp=datetime.now()
      )
      db.session.add(analytics_event)
      db.session.commit()
  ```
- [ ] Track: Page views, button clicks, pattern executions, time spent
- [ ] Test: New user sees walkthrough, analytics events logged

**Deliverable**: ✅ Bloomberg-level analytics, onboarding complete, usage tracked

**Files Created**:
- Updated: ui/portfolio_dashboard.py (factor exposure, correlation matrix, performance attribution, rebalancing)
- Updated: main.py (onboarding walkthrough, contextual help)
- Updated: core/database.py (analytics_events table)

---

## SUCCESS CRITERIA

### Week 0.5 Complete
- ✅ User can create account and log in
- ✅ Portfolio saved to database
- ✅ Portfolio persists between sessions
- ✅ Multi-user support working

### Week 1 Complete
- ✅ Execution trace visible in chat (pattern → agent → capability → data source)
- ✅ "Explain" buttons on all dashboards
- ✅ Confidence scores displayed
- ✅ Users understand HOW Trinity thinks
- ✅ 6 agents registered (financial_analyst, claude, data_harvester, forecast_dreamer, graph_mind, pattern_spotter)

### Week 2 Complete
- ✅ Portfolio upload working (CSV + manual)
- ✅ Portfolio dashboard operational (holdings, charts, risk panel)
- ✅ All dashboards have portfolio overlay ("Market vs YOU")
- ✅ Chat is portfolio-aware ("Analyzing for YOUR holdings...")
- ✅ Export portfolio report as PDF

### Week 3 Complete
- ✅ 27 patterns operational (economy: 6, smart: 7, workflows: 3, analysis: 8, system: 2, market: 1)
- ✅ All patterns tested with portfolio context
- ✅ Click holding → Full analysis modal
- ✅ Mini-charts in chat, dashboard links

### Week 4 Complete
- ✅ Custom ratings visible (dividend safety, moat strength, recession resilience)
- ✅ Rating badges on holdings table
- ✅ Click rating → See full calculation with transparency
- ✅ Portfolio-level aggregated ratings

### Week 5 Complete
- ✅ Portfolio-filtered news feed
- ✅ News impact analysis (portfolio-weighted)
- ✅ Alert system fully functional (backend + UI)
- ✅ Users can create/manage custom alerts
- ✅ Notification icon in header

### Week 6.5 Complete (FINAL)
- ✅ Factor exposure analysis (radar chart)
- ✅ Correlation matrix (heatmap)
- ✅ Performance attribution (waterfall chart)
- ✅ Rebalancing suggestions
- ✅ First-time user onboarding (walkthrough)
- ✅ Contextual help ("?" icons)
- ✅ Usage analytics tracking
- ✅ **100% vision alignment achieved**

---

## ARCHITECTURAL CONSISTENCY RULES

**ALWAYS enforce these patterns:**

### 1. Execution Flow
```
User Login → Authentication (Week 0.5) →
  Load Portfolio from Database →
    User Query → EnhancedChatProcessor → EntityExtraction →
      UniversalExecutor → PatternEngine → AgentRuntime →
        Agent (via capability) → Data (OpenBB/FRED/yfinance) →
          Results → KnowledgeGraph (store) + Database (persist) →
            Display in UI with Execution Trace (Week 1)
```

### 2. Real Data Only
```python
use_real_data = True  # ALWAYS (fixed in execute_through_registry.py:57)
```

### 3. Capability-Based Routing
```python
# Pattern step
{
  "action": "execute_through_registry",
  "params": {
    "capability": "can_calculate_dcf",  # Not agent name
    "context": {...}
  }
}
```

### 4. Knowledge Graph Storage
```
All pattern results → store_in_graph() → KnowledgeGraph → Persistence
```

### 5. Transparency Display
```
Every analysis → Show execution trace → Confidence scores → Clickable steps → Auditable
```

---

## REFERENCE DOCUMENTS

**Planning & Vision**:
- [TRINITY_PRODUCT_VISION_REFINED.md](TRINITY_PRODUCT_VISION_REFINED.md) - Transparency-first vision (9,500 words)
- [PLAN_VALIDATION_AND_UX_SIMULATION.md](PLAN_VALIDATION_AND_UX_SIMULATION.md) - UX validation (12,000 words)
- [PROJECT_STATE_AUDIT.md](PROJECT_STATE_AUDIT.md) - Complete inventory (8,500 words)
- [FINAL_CONSOLIDATED_STATE.md](FINAL_CONSOLIDATED_STATE.md) - Current state + 6-week plan (5,500 words)

**Architecture & Development**:
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) - Agent capabilities
- [PATTERN_AUTHORING_GUIDE.md](PATTERN_AUTHORING_GUIDE.md) - Pattern creation
- [DEVELOPMENT.md](DEVELOPMENT.md) - Developer guide

**Execution**:
- [.claude/trinity_execution_lead.md](.claude/trinity_execution_lead.md) - Week-by-week execution specialist

**Operations**:
- [CONFIGURATION.md](CONFIGURATION.md) - API setup
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

---

## NEXT SESSION CHECKLIST

**Start Here**:
1. [ ] Read [FINAL_CONSOLIDATED_STATE.md](FINAL_CONSOLIDATED_STATE.md) (5 min)
2. [ ] Read [.claude/trinity_execution_lead.md](.claude/trinity_execution_lead.md) (3 min)
3. [ ] Review this file (MASTER_TASK_LIST.md)
4. [ ] Check Week 0.5 checklist (database setup)
5. [ ] Begin Day 1: Database setup (SQLite + SQLAlchemy)

**Don't**:
- ❌ Create new planning documents (use this file)
- ❌ Reference deleted directories (dawsos/, trinity3/)
- ❌ Use mock data (use_real_data=True enforced)
- ❌ Bypass execution flow (always use UniversalExecutor)

---

**END OF MASTER TASK LIST**

**Last Updated**: October 21, 2025 23:00 UTC
**Status**: ✅ Complete 6.5-week roadmap validated through UX simulation
**Vision Alignment**: 60% → 100% (6.5 weeks)
**Next**: Execute Week 0.5 (Critical Infrastructure)
