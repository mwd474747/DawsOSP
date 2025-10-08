# Options Trading System - Trinity 2.0 Implementation Plan

**Status**: Design Phase
**Target**: Full Trinity Architecture Compliance
**Scope**: Polygon.io Integration + Smart Money Detection + Greeks Analysis

---

## 🎯 Executive Summary

Rebuild the options trading system with proper Trinity 2.0 architecture:
- **Layer 1**: PolygonOptionsCapability (data source)
- **Layer 2**: OptionsAnalyst Agent (intelligence)
- **Layer 3**: Pattern orchestration (workflows)
- **Layer 4**: UI Dashboard (user interface)

**Key Principle**: Follow Trinity flow exclusively - NO registry bypasses, NO ad-hoc data loading.

---

## 📐 Architecture Design

### Layer 1: Capability (Data Source)

**File**: `dawsos/capabilities/polygon_options.py`

**Purpose**: Polygon.io API wrapper - fetches raw options data

**Methods**:
```python
class PolygonOptionsCapability(APIHelper):
    """Polygon.io options data integration"""

    def get_option_chain(
        self,
        ticker: str,
        expiration: Optional[str] = None,
        strike_gte: Optional[float] = None,
        strike_lte: Optional[float] = None
    ) -> Dict[str, Any]:
        """Fetch option chain (250 contracts max per call)
        Returns: {calls: [], puts: [], metadata: {}}
        """

    def get_historical_options(
        self,
        contract_id: str,
        from_date: str,
        to_date: str
    ) -> List[Dict[str, Any]]:
        """Time series data for specific contract"""

    def get_market_greeks(
        self,
        ticker: str
    ) -> Dict[str, float]:
        """Aggregated Greeks for ticker"""

    def detect_unusual_activity(
        self,
        min_premium: float = 10000,
        volume_oi_ratio: float = 3.0
    ) -> List[Dict[str, Any]]:
        """Scan for unusual options activity
        Returns: [{ticker, type, strike, expiry, volume, oi, premium, signal_strength}]
        """

    def calculate_iv_rank(
        self,
        ticker: str,
        lookback_days: int = 252
    ) -> Dict[str, Any]:
        """IV percentile calculation
        Returns: {current_iv, iv_rank, iv_percentile, high_52w, low_52w}
        """
```

**Configuration**:
- Rate limit: 66 req/sec (Starter plan)
- Cache TTL: 15 minutes (matches data delay)
- Auto-retry: Exponential backoff (3 attempts)
- API key: `POLYGON_API_KEY` from `.env`

**Dependencies**: Add to `requirements.txt`
```
polygon-api-client>=1.12.0
```

---

### Layer 2: Agent (Intelligence)

**File**: `dawsos/agents/options_analyst.py`

**Purpose**: Analyze options data and generate actionable insights

**Capabilities** (add to `AGENT_CAPABILITIES`):
```python
'options_analyst': {
    'description': 'Options flow and Greeks analysis specialist',
    'capabilities': [
        'can_analyze_greeks',
        'can_detect_unusual_activity',
        'can_calculate_iv_rank',
        'can_analyze_flow_sentiment',
        'can_suggest_hedges',
        'can_identify_smart_money',
        'can_calculate_max_pain',
        'can_find_gamma_flip'
    ],
    'requires': [
        'requires_polygon_capability',
        'requires_knowledge_graph'
    ],
    'provides': [
        'provides_options_insights',
        'provides_flow_analysis',
        'provides_hedge_suggestions'
    ],
    'integrates_with': ['data_harvester', 'financial_analyst', 'graph_mind'],
    'stores_results': True,
    'priority': 'high',
    'category': 'analysis'
}
```

**Core Methods**:
```python
class OptionsAnalyst(BaseAgent):
    """Options flow and Greeks analysis"""

    def analyze_greeks(self, ticker: str, context: Dict) -> Dict:
        """Aggregate Greeks across chain
        Returns: {
            net_delta: float,
            total_gamma: float,
            max_pain_strike: float,
            gamma_flip_point: float,
            positioning: 'bullish'|'bearish'|'neutral',
            confidence: float
        }
        """

    def detect_unusual_activity(self, context: Dict) -> Dict:
        """Scan for smart money signals
        Returns: {
            unusual_activities: [],
            top_tickers: [],
            sentiment_score: float,
            smart_money_signals: []
        }
        """

    def calculate_iv_rank(self, ticker: str, context: Dict) -> Dict:
        """IV percentile + strategy suggestions
        Returns: {
            iv_rank: float,
            iv_percentile: float,
            regime: 'high'|'medium'|'low',
            suggested_strategies: []
        }
        """

    def analyze_flow_sentiment(self, tickers: List[str], context: Dict) -> Dict:
        """Put/Call ratio analysis
        Returns: {
            put_call_ratio: float,
            sentiment: 'bullish'|'bearish'|'neutral',
            confidence: float,
            direction: str,
            flow_data: {}
        }
        """

    def suggest_hedges(self, ticker: str, portfolio_value: float, context: Dict) -> Dict:
        """Generate hedge recommendations
        Returns: {
            protective_puts: [],
            collar_strategy: {},
            vix_hedge: {},
            cost_analysis: {monthly: float, annual: float}
        }
        """

    def comprehensive_analysis(self, ticker: str, context: Dict) -> Dict:
        """Full options analysis (all methods)
        Returns: {
            greeks: {},
            iv_rank: {},
            flow: {},
            hedges: {},
            executive_summary: str
        }
        """
```

**Knowledge Graph Integration**:
- Node type: `options_analysis`
- Store: Greeks, IV rank, flow sentiment, unusual activity
- Relationships: `ticker -> has_options_data`, `analysis -> detected_on`
- Metadata: `timestamp`, `confidence`, `signal_type`

---

### Layer 3: Patterns (Orchestration)

**Pattern 1**: `dawsos/patterns/analysis/options_flow.json`

```json
{
  "id": "options_flow_analysis",
  "name": "Options Flow Analysis",
  "description": "Analyze put/call flow across multiple tickers for market sentiment",
  "version": "2.0.0",
  "last_updated": "2025-10-07",
  "category": "analysis",
  "triggers": [
    "analyze options flow",
    "check put call ratio",
    "market sentiment from options"
  ],
  "context_requirements": {
    "required": ["tickers"],
    "optional": ["lookback_period", "min_volume"]
  },
  "steps": [
    {
      "action": "execute_through_registry",
      "capability": "can_fetch_options_flow",
      "description": "Fetch option chain data for tickers",
      "parameters": {
        "tickers": "{{context.tickers}}",
        "lookback_period": "{{context.lookback_period|default:1}}"
      }
    },
    {
      "action": "execute_through_registry",
      "capability": "can_analyze_flow_sentiment",
      "description": "Calculate put/call ratios and sentiment",
      "parameters": {
        "flow_data": "{{step1.result}}",
        "tickers": "{{context.tickers}}"
      }
    },
    {
      "action": "execute_through_registry",
      "capability": "can_add_nodes",
      "description": "Store flow analysis in graph",
      "parameters": {
        "node_type": "options_flow_analysis",
        "data": "{{step2.result}}",
        "metadata": {
          "timestamp": "{{now}}",
          "tickers": "{{context.tickers}}"
        }
      }
    }
  ],
  "output_format": {
    "put_call_ratio": "float",
    "sentiment": "string",
    "confidence": "float",
    "direction": "string",
    "flow_data": "object"
  }
}
```

**Pattern 2**: `dawsos/patterns/analysis/unusual_options_activity.json`

```json
{
  "id": "unusual_options_activity",
  "name": "Unusual Options Activity Scanner",
  "description": "Detect smart money activity via unusual volume and premium",
  "version": "2.0.0",
  "last_updated": "2025-10-07",
  "category": "analysis",
  "triggers": [
    "unusual options activity",
    "smart money detector",
    "find option sweeps"
  ],
  "context_requirements": {
    "optional": ["min_premium", "volume_oi_ratio", "lookback_hours"]
  },
  "steps": [
    {
      "action": "execute_through_registry",
      "capability": "can_detect_unusual_activity",
      "description": "Scan market for unusual options activity",
      "parameters": {
        "min_premium": "{{context.min_premium|default:10000}}",
        "volume_oi_ratio": "{{context.volume_oi_ratio|default:3.0}}",
        "lookback_hours": "{{context.lookback_hours|default:24}}"
      }
    },
    {
      "action": "execute_through_registry",
      "capability": "can_identify_smart_money",
      "description": "Filter for institutional-size trades",
      "parameters": {
        "unusual_data": "{{step1.result}}",
        "min_institutional_premium": 100000
      }
    },
    {
      "action": "execute_through_registry",
      "capability": "can_add_nodes",
      "description": "Store unusual activity signals in graph",
      "parameters": {
        "node_type": "unusual_options_signal",
        "data": "{{step2.result}}",
        "metadata": {
          "timestamp": "{{now}}",
          "signal_type": "smart_money"
        }
      }
    }
  ],
  "output_format": {
    "unusual_activities": "array",
    "top_tickers": "array",
    "smart_money_signals": "array",
    "sentiment_score": "float"
  }
}
```

**Pattern 3**: `dawsos/patterns/analysis/greeks_analysis.json`

```json
{
  "id": "greeks_analysis",
  "name": "Greeks Positioning Analysis",
  "description": "Analyze Greeks to determine market positioning and gamma exposure",
  "version": "2.0.0",
  "last_updated": "2025-10-07",
  "category": "analysis",
  "triggers": [
    "analyze greeks for {{ticker}}",
    "gamma exposure {{ticker}}",
    "max pain {{ticker}}"
  ],
  "context_requirements": {
    "required": ["ticker"]
  },
  "steps": [
    {
      "action": "execute_through_registry",
      "capability": "can_analyze_greeks",
      "description": "Calculate aggregated Greeks and positioning",
      "parameters": {
        "ticker": "{{context.ticker}}"
      }
    },
    {
      "action": "execute_through_registry",
      "capability": "can_calculate_max_pain",
      "description": "Find strike with highest open interest",
      "parameters": {
        "greeks_data": "{{step1.result}}"
      }
    },
    {
      "action": "execute_through_registry",
      "capability": "can_find_gamma_flip",
      "description": "Identify price where gamma exposure reverses",
      "parameters": {
        "greeks_data": "{{step1.result}}"
      }
    },
    {
      "action": "execute_through_registry",
      "capability": "can_add_nodes",
      "description": "Store Greeks analysis in graph",
      "parameters": {
        "node_type": "greeks_analysis",
        "data": {
          "ticker": "{{context.ticker}}",
          "net_delta": "{{step1.result.net_delta}}",
          "total_gamma": "{{step1.result.total_gamma}}",
          "max_pain": "{{step2.result.max_pain_strike}}",
          "gamma_flip": "{{step3.result.gamma_flip_point}}",
          "positioning": "{{step1.result.positioning}}"
        },
        "metadata": {
          "timestamp": "{{now}}"
        }
      }
    }
  ],
  "output_format": {
    "net_delta": "float",
    "total_gamma": "float",
    "max_pain_strike": "float",
    "gamma_flip_point": "float",
    "positioning": "string",
    "confidence": "float"
  }
}
```

---

### Layer 4: UI Dashboard

**File**: `dawsos/ui/options_dashboard.py`

**Purpose**: 4-tab interface for options analysis

**Integration**: Import in `main.py`, add to sidebar navigation

**Tabs**:

1. **Market Flow** (Put/Call Ratios)
   - Multi-select: SPY, QQQ, IWM, DIA, NVDA, TSLA, AAPL, etc.
   - Execute: `options_flow_analysis` pattern
   - Display: Metrics cards, bar chart (call vs put volume), data table
   - Store results in graph via pattern

2. **Unusual Activity** (Smart Money)
   - Filters: Min volume, min premium ($10k-$1M), lookback period
   - Execute: `unusual_options_activity` pattern
   - Display: Unusual trades table with sentiment color-coding, top tickers
   - Confidence scoring: High/Medium/Low

3. **Greeks Analysis** (Positioning)
   - Input: Single ticker
   - Execute: `greeks_analysis` pattern
   - Display: Net Delta, Total Gamma, Max Pain, Gamma Flip Point
   - Recommendation based on positioning

4. **IV Rank** (Strategy Suggestions)
   - Input: Ticker
   - Execute: `can_calculate_iv_rank` capability
   - Display: IV rank, IV percentile, 52W high/low
   - Strategy suggestions:
     - IV Rank > 80: Sell premium (iron condors, covered calls)
     - IV Rank < 20: Buy options (long calls/puts, debit spreads)
     - IV Rank 20-80: Neutral (butterflies, diagonals)

**UI Components**:
```python
def render_options_dashboard():
    """Main dashboard with 4 tabs"""
    tabs = st.tabs(["📊 Market Flow", "🔍 Unusual Activity", "🧮 Greeks", "📈 IV Rank"])

    with tabs[0]:
        render_market_flow_tab()

    with tabs[1]:
        render_unusual_activity_tab()

    with tabs[2]:
        render_greeks_tab()

    with tabs[3]:
        render_iv_rank_tab()
```

**Trinity Compliance**:
- ✅ Execute patterns via `UniversalExecutor`
- ✅ All API calls through `PolygonOptionsCapability`
- ✅ Agent analysis via `execute_by_capability()`
- ✅ Results stored in graph automatically
- ❌ NO direct agent calls
- ❌ NO registry bypasses

---

## 🔄 Complete Data Flow Example

**User Action**: Clicks "Refresh Flow" for SPY, QQQ, IWM

1. **UI** → Calls `UniversalExecutor.execute(context={'pattern': 'options_flow_analysis', 'tickers': ['SPY', 'QQQ', 'IWM']})`

2. **UniversalExecutor** → Loads pattern from `patterns/analysis/options_flow.json`

3. **PatternEngine** → Executes Step 1:
   - Action: `execute_through_registry`
   - Capability: `can_fetch_options_flow`
   - Routes to: `data_harvester.fetch_options_flow()`
   - `data_harvester` calls `polygon_options.get_option_chain()` for each ticker
   - Returns: Raw option chain data (calls, puts, Greeks, volume, OI)

4. **PatternEngine** → Executes Step 2:
   - Action: `execute_through_registry`
   - Capability: `can_analyze_flow_sentiment`
   - Routes to: `options_analyst.analyze_flow_sentiment()`
   - Calculates: Total call/put volume, P/C ratio, sentiment
   - Returns: `{put_call_ratio: 0.85, sentiment: 'bullish', confidence: 0.72}`

5. **PatternEngine** → Executes Step 3:
   - Action: `execute_through_registry`
   - Capability: `can_add_nodes`
   - Routes to: `graph_mind.add_node()`
   - Stores analysis in graph with timestamp and metadata

6. **UniversalExecutor** → Returns consolidated result to UI

7. **UI** → Renders:
   - Metrics: P/C Ratio (0.85), Sentiment (🐂 Bullish), Confidence (72%)
   - Chart: Call volume vs Put volume bars
   - Table: Detailed flow data per ticker

8. **Knowledge Graph** → Stores:
   - Node: `options_flow_analysis_{{timestamp}}`
   - Relationships: `SPY -> has_flow_data`, `QQQ -> has_flow_data`, `IWM -> has_flow_data`
   - Metadata: `{timestamp, tickers, put_call_ratio, sentiment}`

---

## 📋 Implementation Checklist

### Phase 1: Foundation (Capability + Agent)

- [ ] **1.1** Create `dawsos/capabilities/polygon_options.py`
  - [ ] Implement `get_option_chain()`
  - [ ] Implement `detect_unusual_activity()`
  - [ ] Implement `calculate_iv_rank()`
  - [ ] Add 15-min cache with TTL
  - [ ] Add rate limiting (66 req/sec)
  - [ ] Add auto-retry with exponential backoff
  - [ ] Test with Polygon API key from `.env`

- [ ] **1.2** Create `dawsos/agents/options_analyst.py`
  - [ ] Implement `analyze_greeks()`
  - [ ] Implement `detect_unusual_activity()`
  - [ ] Implement `calculate_iv_rank()`
  - [ ] Implement `analyze_flow_sentiment()`
  - [ ] Implement `suggest_hedges()`
  - [ ] Implement `comprehensive_analysis()`
  - [ ] Add knowledge graph storage for all results

- [ ] **1.3** Update `dawsos/core/agent_capabilities.py`
  - [ ] Add `options_analyst` entry with 8 capabilities
  - [ ] Document requirements: `requires_polygon_capability`
  - [ ] Document integration: `integrates_with: ['data_harvester', 'financial_analyst']`

- [ ] **1.4** Register agent in `dawsos/main.py`
  - [ ] Import `OptionsAnalyst`
  - [ ] Initialize `PolygonOptionsCapability()` in capabilities dict
  - [ ] Register agent: `runtime.register_agent('options_analyst', OptionsAnalyst(...), capabilities=...)`

- [ ] **1.5** Update `dawsos/agents/data_harvester.py`
  - [ ] Add `fetch_options_flow()` method
  - [ ] Add `fetch_option_chain()` method
  - [ ] Use `polygon_options` capability (from capabilities dict)
  - [ ] Add to `AGENT_CAPABILITIES['data_harvester']['capabilities']`:
    - `can_fetch_options_flow`
    - `can_fetch_option_chain`

### Phase 2: Patterns (Orchestration)

- [ ] **2.1** Create `dawsos/patterns/analysis/options_flow.json`
  - [ ] Define triggers: "analyze options flow", "put call ratio"
  - [ ] Step 1: Fetch flow data (`can_fetch_options_flow`)
  - [ ] Step 2: Analyze sentiment (`can_analyze_flow_sentiment`)
  - [ ] Step 3: Store in graph (`can_add_nodes`)
  - [ ] Validate JSON with `scripts/lint_patterns.py`

- [ ] **2.2** Create `dawsos/patterns/analysis/unusual_options_activity.json`
  - [ ] Define triggers: "unusual options", "smart money"
  - [ ] Step 1: Detect unusual activity (`can_detect_unusual_activity`)
  - [ ] Step 2: Filter smart money (`can_identify_smart_money`)
  - [ ] Step 3: Store signals in graph
  - [ ] Validate JSON

- [ ] **2.3** Create `dawsos/patterns/analysis/greeks_analysis.json`
  - [ ] Define triggers: "analyze greeks", "gamma exposure"
  - [ ] Step 1: Calculate Greeks (`can_analyze_greeks`)
  - [ ] Step 2: Find max pain (`can_calculate_max_pain`)
  - [ ] Step 3: Find gamma flip (`can_find_gamma_flip`)
  - [ ] Step 4: Store in graph
  - [ ] Validate JSON

### Phase 3: UI Dashboard

- [ ] **3.1** Create `dawsos/ui/options_dashboard.py`
  - [ ] Implement `render_market_flow_tab()`
    - Multi-select tickers
    - Execute `options_flow_analysis` pattern
    - Display metrics cards (P/C ratio, sentiment, confidence)
    - Plotly bar chart: Call vs Put volume
    - Data table with detailed flow
  - [ ] Implement `render_unusual_activity_tab()`
    - Filters: Min volume, min premium, lookback
    - Execute `unusual_options_activity` pattern
    - Display unusual trades table (color-coded by sentiment)
    - Show top tickers
    - Confidence scoring
  - [ ] Implement `render_greeks_tab()`
    - Single ticker input
    - Execute `greeks_analysis` pattern
    - Display: Net Delta, Total Gamma, Max Pain, Gamma Flip
    - Positioning recommendation
  - [ ] Implement `render_iv_rank_tab()`
    - Ticker input
    - Execute via `execute_by_capability('can_calculate_iv_rank')`
    - Display: IV rank, IV percentile, 52W range
    - Strategy suggestions based on IV level
  - [ ] Add main `render_options_dashboard()` with 4 tabs

- [ ] **3.2** Integrate into `dawsos/main.py`
  - [ ] Import: `from ui.options_dashboard import render_options_dashboard`
  - [ ] Add sidebar navigation: "📊 Options Analysis"
  - [ ] Call `render_options_dashboard()` when selected

### Phase 4: Testing & Validation

- [ ] **4.1** Unit tests
  - [ ] `dawsos/tests/unit/test_polygon_options.py`
    - Test API connection
    - Test cache behavior
    - Test rate limiting
  - [ ] `dawsos/tests/unit/test_options_analyst.py`
    - Test Greeks calculation
    - Test IV rank calculation
    - Test flow sentiment analysis
    - Test graph storage

- [ ] **4.2** Integration tests
  - [ ] `dawsos/tests/validation/test_options_patterns.py`
    - Test `options_flow_analysis` pattern end-to-end
    - Test `unusual_options_activity` pattern
    - Test `greeks_analysis` pattern
    - Verify graph storage
    - Verify Trinity compliance (no registry bypasses)

- [ ] **4.3** Smoke test
  - [ ] Add to `dawsos/tests/validation/test_trinity_smoke.py`
  - [ ] Test options_analyst registration
  - [ ] Test pattern loading (3 new patterns)
  - [ ] Test capability routing

- [ ] **4.4** Manual validation
  - [ ] Launch Streamlit app
  - [ ] Navigate to Options Analysis
  - [ ] Test Market Flow tab (SPY, QQQ)
  - [ ] Test Unusual Activity tab (scan)
  - [ ] Test Greeks tab (SPY)
  - [ ] Test IV Rank tab (NVDA)
  - [ ] Verify data appears correctly
  - [ ] Check graph nodes created (via Graph Explorer tab)

### Phase 5: Documentation

- [ ] **5.1** Create `dawsos/docs/OptionsAnalysis.md`
  - [ ] System architecture diagram
  - [ ] API setup instructions (Polygon key)
  - [ ] Usage guide (4 tabs explained)
  - [ ] Interpretation guide (Greeks, IV rank, flow sentiment)
  - [ ] Strategy suggestions reference

- [ ] **5.2** Update `CLAUDE.md`
  - [ ] Add options_analyst to agent list (20 agents)
  - [ ] Document 8 new capabilities
  - [ ] Note Polygon.io integration
  - [ ] Add options patterns to pattern count (48 patterns)

- [ ] **5.3** Update `README.md`
  - [ ] Add "Options Analysis" to features
  - [ ] Add Polygon API key to setup
  - [ ] Update capabilities count (58 capabilities)

- [ ] **5.4** Update `requirements.txt`
  - [ ] Add `polygon-api-client>=1.12.0`

- [ ] **5.5** Update `.env.example`
  - [ ] Add `POLYGON_API_KEY=your-polygon-key-here`
  - [ ] Document Polygon plan requirements (Starter: $200/mo)

---

## 🎯 Success Criteria

### Functional Requirements
- ✅ Polygon API integration working (rate limiting, caching, retry)
- ✅ Greeks analysis calculates: Net Delta, Total Gamma, Max Pain, Gamma Flip
- ✅ Unusual activity detection with smart money filtering
- ✅ IV rank calculation with strategy suggestions
- ✅ Flow sentiment analysis (P/C ratios, directional bias)
- ✅ All results stored in knowledge graph
- ✅ 4-tab UI dashboard functional

### Trinity Compliance
- ✅ All execution through UniversalExecutor
- ✅ Patterns use `execute_through_registry` action
- ✅ No direct agent calls in UI
- ✅ No registry bypasses
- ✅ All data loaded via capabilities (not ad-hoc file reads)
- ✅ Results auto-stored via AgentAdapter

### Testing
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Smoke tests pass
- ✅ Manual validation successful
- ✅ Pattern linter passes (0 errors)

### Documentation
- ✅ OptionsAnalysis.md complete
- ✅ CLAUDE.md updated
- ✅ README.md updated
- ✅ API setup documented

---

## 🚨 Common Pitfalls to Avoid

1. **Registry Bypass** ❌
   ```python
   # WRONG - Direct agent call
   analyst = runtime.agents['options_analyst']
   result = analyst.analyze_greeks(ticker)

   # RIGHT - Via registry
   result = runtime.execute_by_capability('can_analyze_greeks', context)
   ```

2. **Ad-hoc API Calls** ❌
   ```python
   # WRONG - Direct API call in UI
   import polygon
   client = polygon.RESTClient(api_key)
   data = client.get_options_chain('SPY')

   # RIGHT - Via capability
   result = executor.execute(context={'pattern': 'options_flow_analysis', 'tickers': ['SPY']})
   ```

3. **Pattern Direct Agent Calls** ❌
   ```json
   // WRONG - Deprecated action
   {"action": "analyze", "agent": "options_analyst"}

   // RIGHT - Capability routing
   {"action": "execute_through_registry", "capability": "can_analyze_greeks"}
   ```

4. **Missing Graph Storage** ❌
   ```python
   # WRONG - Analysis not stored
   def analyze_greeks(self, ticker):
       result = self._calculate_greeks(ticker)
       return result  # Lost after request

   # RIGHT - Auto-stored via pattern
   # Pattern includes step: {"action": "execute_through_registry", "capability": "can_add_nodes"}
   ```

---

## 📊 Expected Metrics After Implementation

- **Agents**: 19 → 20 (+options_analyst)
- **Capabilities**: 50 → 58 (+8 options capabilities)
- **Patterns**: 45 → 48 (+options_flow, unusual_options_activity, greeks_analysis)
- **Datasets**: 26 (no new datasets, but graph nodes will grow)
- **UI Tabs**: Add 1 new dashboard ("Options Analysis" with 4 sub-tabs)
- **External APIs**: 5 → 6 (+Polygon.io)

---

## 🔗 Related Documentation

- [CLAUDE.md](CLAUDE.md) - Trinity development principles
- [.claude/pattern_specialist.md](.claude/pattern_specialist.md) - Pattern creation guide
- [.claude/agent_orchestrator.md](.claude/agent_orchestrator.md) - Agent development
- [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) - Capability-based routing
- [docs/AgentDevelopmentGuide.md](docs/AgentDevelopmentGuide.md) - Agent standards

---

## 💡 Future Enhancements (Post-MVP)

### Advanced Analytics
- [ ] Options chain heatmaps (strike vs expiry)
- [ ] Implied volatility surface 3D visualization
- [ ] Historical IV rank trends (time series)
- [ ] Gamma exposure by strike (dealer positioning)
- [ ] Dark pool integration (TBD data source)

### Machine Learning
- [ ] Unusual activity pattern recognition
- [ ] Smart money signal classification
- [ ] Flow sentiment prediction model
- [ ] IV rank mean reversion signals

### Alerts & Automation
- [ ] Real-time unusual activity alerts
- [ ] Greeks threshold alerts (gamma flip, max pain)
- [ ] IV rank extremes notifications
- [ ] Automated hedge suggestions

### Strategy Backtesting
- [ ] Historical options data loading
- [ ] Strategy P&L calculation
- [ ] Greeks-based strategy testing
- [ ] IV rank strategy validation

---

**Next Steps**: Review this plan, then proceed with Phase 1.1 (PolygonOptionsCapability).
