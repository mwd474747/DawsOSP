# DawsOS Capability Integration Plan
## Bringing Archived Intentions & Product Vision to Life

**Date**: October 3, 2025
**Status**: Planning Phase
**Dependencies**: Option A completion (✅ Done)
**Timeline**: 4-6 weeks (phased rollout)
**Goal**: Transform DawsOS from architectural framework into production-ready investment intelligence system

---

## Executive Summary

DawsOS has a **solid Trinity Architecture** (A+ grade) but operates with:
- **Capability stubs** that return canned data instead of live market feeds
- **15 live agents** but references to 4 archived agents (equity, macro, risk, pattern)
- **26 knowledge datasets** but no automated ingestion/refresh pipeline
- **Meta-pattern routing** newly fixed but not fully wired for production telemetry
- **Graph persistence** enabled but not integrated with backup rotation/checksums

This plan phases in:
1. **Architecture cleanup** - Remove ghost agents, wire meta-pattern telemetry
2. **Data integration** - Connect live APIs (FMP, FRED, NewsAPI, fundamentals)
3. **Knowledge pipeline** - Automated ingestion with provenance tracking
4. **Pattern operationalization** - Real workflows replacing placeholder logic
5. **Production hardening** - Monitoring, backups, CI validation

---

## Current State Analysis

### ✅ What's Working (Trinity Architecture Foundation)
| Component | Status | Evidence |
|-----------|--------|----------|
| **Agent Registry** | ✅ Live | 15 agents registering on startup |
| **Knowledge Graph** | ✅ Live | 2 nodes loaded, add_node/connect working |
| **Pattern Engine** | ✅ Live | 45 patterns loaded successfully |
| **Universal Executor** | ✅ Live | Trinity routing enforced |
| **Meta Pattern Actions** | ✅ Implemented | 4 handlers (select_router, execute_pattern, track_execution, store_in_graph) |
| **Graph Persistence** | ✅ Wired | Auto-save after executions |
| **Test Suite** | ✅ Passing | 37 tests, 0 failures |

### ⚠️ What Needs Integration
| Component | Issue | Impact |
|-----------|-------|--------|
| **Capability Stubs** | Return canned responses | No real market data |
| **API Keys** | Not configured (empty .env) | Services can't authenticate |
| **Ghost Agent References** | AGENT_CAPABILITIES mentions archived agents | Lint/telemetry confusion |
| **Graph Edge Rendering** | Uses edges[0] instead of current edge | UI shows wrong relationships |
| **Knowledge Ingestion** | Manual seeding, no refresh | Stale data |
| **Backup Rotation** | PersistenceManager unused | No checksum validation |
| **CI Pattern Paths** | Fixed but not enforcing meta actions | Could deploy broken patterns |
| **End-to-End Tests** | Only unit tests exist | No workflow validation |

---

## Integration Strategy

### Phase 1: Architecture Cleanup (Week 1) - 12 hours
**Goal**: Remove ghosts, wire telemetry, fix UI bugs

#### 1.1 Agent Registry Alignment
**Problem**: AGENT_CAPABILITIES references archived agents (equity_analyzer, macro_monitor, risk_manager, pattern_optimizer)

**Tasks**:
- [ ] Audit `dawsos/core/agent_capabilities.py` for ghost references
- [ ] Remove or revive archived agents:
  - **Option A**: Remove entirely if not needed
  - **Option B**: Recreate as new agents with live data capabilities
- [ ] Update `scripts/lint_patterns.py` to match live roster
- [ ] Verify all 15 live agents have complete capability definitions

**Files**:
- `dawsos/core/agent_capabilities.py`
- `scripts/lint_patterns.py`
- `dawsos/archived_legacy/` (check for salvageable code)

**Validation**:
```python
# Test script
from core.agent_capabilities import AGENT_CAPABILITIES
from core.agent_adapter import AgentRegistry

registry = AgentRegistry()
# All agents in AGENT_CAPABILITIES should register
assert len(AGENT_CAPABILITIES) == len(registry.agents)
```

---

#### 1.2 Meta-Pattern Telemetry Wiring
**Problem**: Meta patterns execute but don't track to runtime telemetry

**Tasks**:
- [ ] Verify `track_execution` action writes to `runtime.telemetry`
- [ ] Add telemetry dashboard in UI (Governance tab)
- [ ] Display: execution counts, success rates, agent usage, pattern frequencies
- [ ] Wire `store_in_graph` to create execution history nodes

**Files**:
- `dawsos/core/pattern_engine.py:998-1041` (track_execution)
- `dawsos/ui/governance_tab.py` (new telemetry panel)
- `dawsos/core/agent_runtime.py` (add telemetry storage)

**Success Criteria**:
- Every execution creates telemetry entry
- Governance tab shows real-time metrics
- Graph contains execution_result nodes with timing data

---

#### 1.3 Graph Edge Rendering Fix
**Problem**: `dawsos/main.py:267` uses `graph.edges[0]` for all edge visualizations

**Tasks**:
- [ ] Find edge rendering code in main.py
- [ ] Fix to iterate over edges correctly or pass edge to render function
- [ ] Test with multiple relationships (should show different colors/weights)

**Files**:
- `dawsos/main.py:267` (edge visualization)
- `dawsos/ui/trinity_ui_components.py` (if edge rendering helper exists)

**Validation**:
- Create 3 edges with different relationship types
- Verify UI shows correct labels/colors for each

---

### Phase 2: Data Integration (Week 2-3) - 24 hours
**Goal**: Connect live APIs, establish credential management

#### 2.1 API Credential Management
**Current**: `.env` exists but empty, capabilities check `os.getenv()` and fail silently

**Tasks**:
- [ ] Create secure credential manager (`dawsos/core/credentials.py`)
- [ ] Support: environment variables, AWS Secrets Manager, local encrypted vault
- [ ] Add credential validation on startup (warn if missing, don't crash)
- [ ] Update `.env.example` with all required keys:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  FMP_API_KEY=...           # Financial Modeling Prep
  FRED_API_KEY=...          # Federal Reserve Economic Data
  NEWSAPI_KEY=...           # News API
  ALPHA_VANTAGE_KEY=...     # Alpha Vantage (fallback)
  ```

**Files**:
- `dawsos/core/credentials.py` (new)
- `dawsos/.env.example` (update)
- All capability files to use credential manager

**Security**:
- Never log actual keys
- Rotate credentials quarterly
- Use least-privilege API plans

---

#### 2.2 Market Data Capability (FMP API)
**Current**: `dawsos/capabilities/market_data.py` has full implementation but returns None if no API key

**Tasks**:
- [ ] Test with real FMP API key (validate quote, financials, news endpoints)
- [ ] Add error handling for rate limits (FMP Pro = 750 calls/min)
- [ ] Implement exponential backoff for transient failures
- [ ] Add fallback to cached data if API down
- [ ] Cache responses for 1-5 minutes (already implemented)

**Endpoints to Validate**:
1. `get_quote(symbol)` - Real-time prices
2. `get_company_profile(symbol)` - Company metadata
3. `get_key_metrics(symbol)` - P/E, ROE, debt ratios
4. `get_financial_statements(symbol)` - Income, balance sheet, cash flow
5. `get_historical_prices(symbol, period)` - OHLCV data
6. `get_stock_news(symbol)` - Company-specific news

**Success Criteria**:
- Query AAPL quote, receive < 1 second response
- Financial statements return 5+ years of data
- News returns 10+ recent articles

---

#### 2.3 Economic Data Capability (FRED API)
**Current**: `dawsos/capabilities/fred_data.py` exists, needs key validation

**Tasks**:
- [ ] Test with real FRED API key (free, unlimited calls)
- [ ] Validate economic series retrieval (GDP, unemployment, inflation, interest rates)
- [ ] Add series metadata (units, frequency, last updated)
- [ ] Implement 24-hour cache for economic data (updates daily at most)

**Key Series**:
- `GDP` - Quarterly GDP
- `UNRATE` - Unemployment rate
- `CPIAUCSL` - Consumer Price Index (inflation)
- `DFF` - Federal Funds Rate
- `T10Y2Y` - 10Y-2Y Treasury spread (recession indicator)
- `SP500` - S&P 500 index

**Success Criteria**:
- Retrieve 10 years of GDP data in < 2 seconds
- Cache prevents redundant calls
- Metadata includes last observation date

---

#### 2.4 News Capability (NewsAPI)
**Current**: `dawsos/capabilities/news.py` has basic structure

**Tasks**:
- [ ] Test with real NewsAPI key (free tier = 100 calls/day, upgrade if needed)
- [ ] Implement keyword/symbol-based search
- [ ] Add sentiment scoring (integrate with existing sentiment analysis pattern)
- [ ] Cache articles for 6 hours (news doesn't change that fast)
- [ ] Filter spam/low-quality sources

**Features**:
1. `get_company_news(symbol, days=7)` - Symbol-specific
2. `get_market_news(category, days=7)` - Sector/market-wide
3. `analyze_sentiment(articles)` - Use Claude agent for sentiment
4. `extract_key_events(articles)` - Timeline of major news

**Success Criteria**:
- Search "Tesla" returns 20+ relevant articles
- Sentiment analysis shows positive/negative/neutral split
- Response time < 3 seconds

---

#### 2.5 Fundamentals Capability
**Current**: `dawsos/capabilities/fundamentals.py` - check if stub or implemented

**Tasks**:
- [ ] Audit current implementation
- [ ] If stub: integrate with FMP financial statements API
- [ ] If implemented: test and validate
- [ ] Add calculated metrics: owner earnings, FCF yield, ROIC, debt coverage
- [ ] Support multi-year trend analysis

**Metrics**:
- Revenue growth (5Y CAGR)
- Gross/operating/net margins
- ROE, ROA, ROIC
- Debt-to-equity
- Free cash flow
- Owner earnings (Buffett method)

---

### Phase 3: Knowledge Pipeline (Week 3-4) - 20 hours
**Goal**: Automated ingestion, provenance tracking, backup rotation

#### 3.1 Ingestion Pipeline Architecture

**Design**:
```
┌─────────────────┐
│ Data Sources    │
│ - FMP API       │
│ - FRED API      │
│ - NewsAPI       │
│ - CSV uploads   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Ingestion Mgr   │
│ - Scheduling    │
│ - Deduplication │
│ - Validation    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Knowledge Graph │
│ - add_node()    │
│ - connect()     │
│ - provenance    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Persistence     │
│ - Auto-save     │
│ - Checksum      │
│ - Rotation      │
└─────────────────┘
```

**Tasks**:
- [ ] Create `dawsos/core/ingestion_manager.py`
- [ ] Support batch ingestion (load historical data)
- [ ] Support scheduled refresh (cron-like, or StreamLit periodic rerun)
- [ ] Add deduplication (don't re-add existing nodes)
- [ ] Track provenance: source, timestamp, freshness

**Configuration** (`dawsos/config/ingestion_schedule.json`):
```json
{
  "schedules": [
    {
      "source": "fmp_quotes",
      "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
      "frequency": "5m",
      "enabled": true
    },
    {
      "source": "fred_economic",
      "series": ["GDP", "UNRATE", "CPIAUCSL"],
      "frequency": "1d",
      "enabled": true
    },
    {
      "source": "news",
      "keywords": ["stocks", "market", "economy"],
      "frequency": "1h",
      "enabled": true
    }
  ]
}
```

---

#### 3.2 Provenance & Metadata

**Problem**: Current knowledge graph nodes lack:
- Data source
- Ingestion timestamp
- Freshness indicators
- Quality scores

**Tasks**:
- [ ] Extend `add_node` calls to include `_meta` field:
  ```python
  graph.add_node(
      node_type='quote',
      data={
          'symbol': 'AAPL',
          'price': 175.43,
          '_meta': {
              'source': 'fmp_api',
              'ingested_at': '2025-10-03T16:45:00Z',
              'freshness': 'real-time',  # real-time | daily | weekly | static
              'quality_score': 0.95,
              'last_validated': '2025-10-03T16:45:00Z'
          }
      }
  )
  ```
- [ ] Add `get_freshness(node_id)` to KnowledgeGraph
- [ ] Create UI indicators for stale data (> 24 hours old)

**Validation**:
- Query node, check `_meta.freshness`
- UI shows warning if data > 1 day old for real-time sources

---

#### 3.3 Backup Rotation & Checksums

**Current**: `PersistenceManager` exists but never called

**Tasks**:
- [ ] Wire `PersistenceManager.save_graph_with_backup()` in:
  1. On app shutdown (Streamlit `on_shutdown` hook)
  2. Every 1000 executions
  3. Manual trigger in Governance tab
- [ ] Implement rotation:
  ```
  dawsos/storage/backups/
    graph_20251003_160000.json      (current)
    graph_20251003_120000.json      (4h ago)
    graph_20251002_160000.json      (1d ago)
    graph_20251001_160000.json      (2d ago)
  ```
- [ ] Keep: last 24 hours (all), last 7 days (daily), last 4 weeks (weekly)
- [ ] Add checksum validation on restore

**Files**:
- `dawsos/core/persistence.py:37` (save_graph_with_backup)
- `dawsos/main.py` (wire shutdown hook)
- `dawsos/ui/governance_tab.py` (manual backup button)

**Success Criteria**:
- Backup created every 1000 executions
- Rotation keeps 24h + 7d + 4w
- Restore validates checksum before loading

---

#### 3.4 Dataset Expansion & Quality

**Current**: 26 knowledge datasets, but some may be static or stale

**Tasks**:
- [ ] Audit all 26 datasets for:
  - Last updated timestamp
  - Source/provenance
  - Completeness (missing fields?)
- [ ] Add quality alerts:
  - Warn if dataset > 7 days old (for dynamic data)
  - Error if required dataset missing
- [ ] Expand datasets:
  - S&P 500 constituents (updated quarterly)
  - Sector performance (daily)
  - Economic cycles (quarterly)
  - Risk-free rates (daily)
  - Volatility indices (daily)

**Files**:
- `dawsos/storage/knowledge/*.json` (all datasets)
- `dawsos/core/knowledge_loader.py` (add quality checks)

---

### Phase 4: Pattern Operationalization (Week 4-5) - 24 hours
**Goal**: Replace placeholder logic with real workflows

#### 4.1 Pattern Audit

**Process**:
1. Review all 45 patterns in `dawsos/patterns/`
2. Identify patterns with:
   - Hardcoded fallbacks (`result = {'status': 'demo'}`)
   - Direct agent access (should use `execute_through_registry`)
   - Missing validation steps
   - Unrealistic data assumptions

**Priority Patterns** (investment workflows):
1. `company_analysis` - Deep dive on single stock
2. `sector_performance` - Compare sector returns
3. `market_regime` - Bull/bear/transition detection
4. `portfolio_review` - Risk-adjusted performance
5. `morning_briefing` - Daily market summary
6. `opportunity_scan` - Find undervalued stocks
7. `governance_audit` - Compliance check

---

#### 4.2 Company Analysis Pattern

**Current**: `dawsos/patterns/workflows/company_analysis.json`

**Enhancement Tasks**:
- [ ] Step 1: Get quote data (market_data capability)
- [ ] Step 2: Fetch financials (fundamental_analysis agent)
- [ ] Step 3: Analyze competitive moat (moat_analyzer pattern)
- [ ] Step 4: Calculate intrinsic value (dcf_valuation pattern)
- [ ] Step 5: Check news sentiment (news capability + sentiment agent)
- [ ] Step 6: Generate report (claude agent)
- [ ] Step 7: Store findings in graph

**Input**:
```json
{
  "pattern_id": "company_analysis",
  "context": {
    "symbol": "AAPL",
    "depth": "comprehensive"  // quick | standard | comprehensive
  }
}
```

**Output**:
```json
{
  "symbol": "AAPL",
  "recommendation": "BUY",
  "target_price": 195.00,
  "confidence": 0.82,
  "moat_rating": "Wide",
  "valuation_upside": 0.15,
  "key_risks": ["Regulatory", "Competition"],
  "report_url": "storage/reports/AAPL_20251003.md"
}
```

---

#### 4.3 Market Regime Detection

**Purpose**: Classify current market as bull/bear/transition

**Tasks**:
- [ ] Fetch market indices (S&P 500, VIX, treasury yields)
- [ ] Calculate technical indicators (50-day MA, 200-day MA, breadth)
- [ ] Analyze economic data (GDP growth, unemployment, inflation)
- [ ] Apply Dalio's economic cycle framework
- [ ] Output regime with confidence score

**Regimes**:
1. **Bull Market**: Uptrend, low volatility, positive breadth
2. **Bear Market**: Downtrend, high volatility, negative breadth
3. **Transition**: Mixed signals, indecisive
4. **Correction**: Short-term pullback in bull market
5. **Rally**: Short-term bounce in bear market

**Integration**:
- Store regime in knowledge graph
- Update daily
- Alert on regime changes
- Adjust portfolio patterns based on regime

---

#### 4.4 End-to-End Workflow Tests

**New Test Suite**: `dawsos/tests/integration/test_investment_workflows.py`

**Test Cases**:
1. **test_company_analysis_workflow()**
   - Execute company_analysis pattern for AAPL
   - Assert: recommendation exists, target price > 0, report generated

2. **test_portfolio_review_workflow()**
   - Create sample portfolio
   - Execute portfolio_review pattern
   - Assert: returns, risk metrics, recommendations

3. **test_market_briefing_workflow()**
   - Execute morning_briefing pattern
   - Assert: market summary, top movers, key events

4. **test_opportunity_scan_workflow()**
   - Execute opportunity_scan with filters
   - Assert: returns list of stocks, sorted by score

5. **test_governance_audit_workflow()**
   - Execute governance_audit pattern
   - Assert: compliance status, violations (if any), telemetry

**Run in CI**: Add to `.github/workflows/compliance-check.yml`

---

### Phase 5: Production Hardening (Week 5-6) - 16 hours
**Goal**: Monitoring, CI validation, operational readiness

#### 5.1 CI Enhancements

**Current**: CI validates pattern JSON syntax and Trinity compliance

**Additions**:
- [ ] **Meta Action Validation**: Fail if pattern uses undefined actions
- [ ] **Agent Existence Check**: Fail if pattern routes to non-existent agent
- [ ] **Dataset Availability**: Warn if pattern depends on missing dataset
- [ ] **Integration Tests**: Run end-to-end workflow tests
- [ ] **Performance Benchmarks**: Alert if pattern execution > 10 seconds

**Files**:
- `.github/workflows/compliance-check.yml` (add new jobs)
- `scripts/validate_patterns.py` (new validator)

---

#### 5.2 Health Checks & Monitoring

**Dashboard**: Add "System Health" tab to UI

**Metrics to Display**:

**Agent Metrics** (from registry):
- Total agents registered
- Executions per agent (last hour/day/week)
- Success rate per agent
- Average execution time

**Pattern Metrics**:
- Total patterns loaded
- Executions per pattern
- Success rate per pattern
- Most used patterns (top 10)

**Graph Metrics**:
- Total nodes
- Total edges
- Growth rate (nodes/day)
- Largest connected component size

**Data Freshness**:
- Datasets with age > 24 hours
- API call success rates
- Cache hit rates

**Storage**:
- Graph size (MB)
- Last backup time
- Backup count
- Oldest backup age

**Example Panel**:
```python
# dawsos/ui/system_health_tab.py
def render_system_health(runtime, graph):
    st.header("🏥 System Health")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Agents", len(runtime.registry.agents))
        st.metric("Patterns", len(runtime.pattern_engine.patterns))
        st.metric("Executions (24h)", runtime.metrics['total_executions'])

    with col2:
        st.metric("Graph Nodes", len(graph.nodes))
        st.metric("Graph Edges", len(graph.edges))
        st.metric("Last Backup", format_time_ago(get_last_backup_time()))

    with col3:
        success_rate = runtime.metrics['successful'] / runtime.metrics['total']
        st.metric("Success Rate", f"{success_rate:.1%}")
        st.metric("Avg Exec Time", f"{runtime.metrics['avg_time_ms']:.0f}ms")
        st.metric("Cache Hit Rate", f"{get_cache_stats()['hit_rate']:.1%}")
```

---

#### 5.3 Logging & Telemetry

**Current**: Basic logging to `dawsos/logs/`

**Enhancements**:
- [ ] **Structured Logging**: JSON format for easy parsing
- [ ] **Log Levels**: DEBUG (development), INFO (production), ERROR (always)
- [ ] **Request Tracing**: Add request_id to track execution flow
- [ ] **Performance Profiling**: Log slow operations (> 1 second)
- [ ] **Error Aggregation**: Group similar errors, alert on spikes

**Example Structured Log**:
```json
{
  "timestamp": "2025-10-03T16:45:23.123Z",
  "level": "INFO",
  "request_id": "req_abc123",
  "component": "UniversalExecutor",
  "action": "execute",
  "pattern_id": "company_analysis",
  "agent": "financial_analyst",
  "duration_ms": 234,
  "success": true,
  "user": "analyst_01"
}
```

**Files**:
- `dawsos/core/logger.py` (create structured logger)
- Update all components to use structured logger

---

#### 5.4 Error Handling & Recovery

**Current**: Some try/catch blocks, but inconsistent

**Tasks**:
- [ ] **Centralized Error Handler**: Catch all exceptions in UniversalExecutor
- [ ] **Graceful Degradation**: Return partial results if some steps fail
- [ ] **Retry Logic**: Exponential backoff for transient failures
- [ ] **Circuit Breaker**: Stop calling failing services temporarily
- [ ] **User-Friendly Errors**: Don't show stack traces to end users

**Example**:
```python
# dawsos/core/error_handler.py
class ErrorHandler:
    def __init__(self):
        self.circuit_breakers = {}

    def handle(self, error, context):
        """
        Classify error, log, optionally retry, return user-friendly message
        """
        if isinstance(error, RateLimitError):
            return self._handle_rate_limit(error, context)
        elif isinstance(error, NetworkError):
            return self._handle_network_error(error, context)
        else:
            return self._handle_unknown_error(error, context)
```

---

### Phase 6: Use-Case Enablement (Week 6+) - Ongoing
**Goal**: Support real analyst workflows

#### 6.1 Analyst Workflow 1: Daily Market Brief

**User Story**:
> As an analyst, I want a daily market summary so I can quickly understand what happened overnight.

**Implementation**:
1. Schedule `morning_briefing` pattern to run at 9:00 AM EST
2. Fetch overnight news, pre-market movers, economic calendar
3. Analyze sentiment, identify themes
4. Generate 1-page PDF report
5. Email to analyst team

**Tasks**:
- [ ] Add scheduling to ingestion manager
- [ ] Create PDF report template
- [ ] Add email notification (optional)
- [ ] Store report in `storage/reports/briefings/`

---

#### 6.2 Analyst Workflow 2: Stock Deep Dive

**User Story**:
> As an analyst, I want to analyze a stock comprehensively so I can make a BUY/SELL/HOLD recommendation.

**Implementation**:
1. User enters symbol in UI
2. Execute `company_analysis` pattern
3. Display results in structured format:
   - Company overview (sector, market cap, description)
   - Financial metrics (revenue, margins, growth)
   - Valuation (P/E, DCF, target price)
   - Competitive moat (wide/narrow/none)
   - News sentiment (positive/negative/neutral)
   - Recommendation with confidence
4. Export to PDF or add to portfolio

**UI**: Create dedicated "Stock Analysis" tab

---

#### 6.3 Analyst Workflow 3: Portfolio Risk Review

**User Story**:
> As a portfolio manager, I want to review portfolio risk so I can identify concentration and tail risks.

**Implementation**:
1. Load portfolio from CSV or manual entry
2. Execute `portfolio_review` pattern
3. Calculate:
   - Total return, alpha, beta, Sharpe ratio
   - Sector concentration
   - Geographic concentration
   - Top 10 holdings weight
   - Value-at-Risk (VaR)
   - Correlation to S&P 500
4. Identify risks:
   - Over-concentration (> 10% in single stock)
   - High correlation (> 0.9 between holdings)
   - Sector overweight (> 30% in one sector)
5. Generate recommendations:
   - Rebalance suggestions
   - Diversification opportunities
   - Hedge recommendations

**UI**: Add "Portfolio" tab with upload + analysis

---

#### 6.4 Analyst Workflow 4: Governance Audit

**User Story**:
> As a compliance officer, I want to audit system activity so I can ensure regulatory compliance.

**Implementation**:
1. Execute `governance_audit` pattern
2. Check:
   - All executions logged in `storage/agent_memory/decisions.json`
   - No direct agent access (all through registry)
   - Graph backups exist and valid
   - Data provenance tracked
   - Sensitive data encrypted
3. Generate compliance report
4. Flag violations

**UI**: Already exists in Governance tab, enhance with audit results

---

## Implementation Roadmap

### Week 1: Architecture Cleanup
- [ ] Remove ghost agents from AGENT_CAPABILITIES
- [ ] Wire meta-pattern telemetry to runtime
- [ ] Fix graph edge rendering bug
- [ ] Add telemetry dashboard to UI

### Week 2: API Integration (Part 1)
- [ ] Create credential manager
- [ ] Test FMP API (quotes, financials, news)
- [ ] Test FRED API (economic data)
- [ ] Add error handling + rate limiting

### Week 3: API Integration (Part 2) + Knowledge Pipeline
- [ ] Test NewsAPI (articles, sentiment)
- [ ] Create ingestion manager
- [ ] Add provenance tracking
- [ ] Implement batch ingestion for historical data

### Week 4: Knowledge Pipeline + Pattern Audit
- [ ] Wire PersistenceManager backup rotation
- [ ] Expand datasets with live data
- [ ] Audit all 45 patterns
- [ ] Enhance company_analysis pattern

### Week 5: Pattern Operationalization
- [ ] Implement market regime detection
- [ ] Create end-to-end workflow tests
- [ ] Replace placeholder logic in top 10 patterns
- [ ] Add CI workflow validation

### Week 6: Production Hardening
- [ ] Add health check dashboard
- [ ] Implement structured logging
- [ ] Create error handler with circuit breaker
- [ ] Performance profiling + optimization

### Week 6+: Use-Case Enablement (Ongoing)
- [ ] Daily market brief workflow
- [ ] Stock deep dive workflow
- [ ] Portfolio risk review workflow
- [ ] Governance audit enhancements

---

## Success Metrics

### Technical Metrics
- **API Integration**: 95%+ success rate on API calls
- **Data Freshness**: 90%+ of nodes < 24 hours old
- **Test Coverage**: 80%+ code coverage, 100% pattern coverage
- **Performance**: Patterns execute in < 5 seconds (90th percentile)
- **Reliability**: 99%+ uptime, < 1% error rate

### Product Metrics
- **Analyst Adoption**: 5+ daily active users within 3 months
- **Workflow Completion**: 80%+ of started analyses completed
- **Report Generation**: 20+ reports generated per week
- **Graph Growth**: 1000+ new nodes per month
- **Time Savings**: 2+ hours saved per analyst per week

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **API Rate Limits** | High | Medium | Implement caching, exponential backoff, upgrade plans if needed |
| **Data Quality Issues** | Medium | High | Add validation, provenance tracking, manual review for critical data |
| **Pattern Complexity** | Medium | Medium | Start with simple patterns, iterate based on feedback |
| **Performance Degradation** | Medium | Medium | Profile early, optimize hot paths, consider async execution |
| **User Adoption Low** | Low | High | Weekly feedback sessions, iterative improvements, training sessions |
| **Security Breach** | Low | Critical | Encrypt credentials, audit logs, regular security reviews |

---

## Dependencies & Prerequisites

### External Services
- [ ] FMP API Pro subscription ($50/month for 750 calls/min)
- [ ] FRED API key (free)
- [ ] NewsAPI subscription ($449/month for Developer plan)
- [ ] Claude API access (Anthropic)

### Infrastructure
- [ ] StreamLit Cloud or self-hosted server
- [ ] PostgreSQL for persistent storage (optional, currently using JSON)
- [ ] Redis for caching (optional, currently in-memory)
- [ ] Email service for notifications (SendGrid, AWS SES)

### Team
- [ ] 1 Backend Engineer (API integration, pipeline)
- [ ] 1 Data Engineer (knowledge graph, ingestion)
- [ ] 1 Frontend Engineer (UI enhancements)
- [ ] 1 QA Engineer (testing, validation)
- [ ] 1 Analyst (requirements, validation)

---

## Conclusion

This plan transforms DawsOS from a **well-architected framework** into a **production-ready investment intelligence system** by:

1. **Cleaning up ghost references** and wiring telemetry
2. **Connecting live data sources** (FMP, FRED, NewsAPI)
3. **Establishing automated ingestion** with provenance tracking
4. **Operationalizing patterns** with real workflows
5. **Hardening for production** with monitoring and error handling
6. **Enabling analyst workflows** that save time and improve decision quality

**Timeline**: 6 weeks for core integration, ongoing refinement for use-case enablement

**Next Step**: Review and approve plan, then begin Week 1 tasks (Architecture Cleanup)

---

**Status**: ✅ Plan Complete - Ready for Review
**Author**: Claude Agent (Sonnet 4.5)
**Date**: October 3, 2025
