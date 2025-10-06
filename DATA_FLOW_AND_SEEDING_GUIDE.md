# DawsOS Data Flow & Seeding Guide

## 🔄 How the System Obtains Data

### **Current Data Flow Architecture**

```
User Request (UI/Chat)
    ↓
UniversalExecutor (entry point)
    ↓
PatternEngine (matches request to pattern)
    ↓
AgentRuntime (executes pattern steps)
    ↓
├─ data_harvester → Calls API Capabilities → Returns Raw Data
├─ data_digester → Normalizes/Enriches → Returns Processed Data
├─ pattern_spotter → Analyzes Patterns → Returns Insights
├─ forecast_dreamer → Makes Predictions → Returns Forecasts
└─ Store Results → KnowledgeGraph → Persists to Disk
```

### **Data Sources (3 Tiers)**

#### **Tier 1: Live API Data** (Real-time, cached)
- **FMP API** → Stock quotes, financials, metrics
- **FRED API** → Economic indicators (GDP, CPI, unemployment)
- **NewsAPI** → News headlines, sentiment
- Accessed via `data_harvester` agent
- Cached 1 min to 24 hours based on data type

#### **Tier 2: Knowledge Graph** (Seeded on startup)
- Investment frameworks (Buffett, Dalio)
- Financial formulas & calculations
- Company database, sector data
- Loaded from `dawsos/storage/knowledge/*.json`
- **26 JSON datasets** auto-loaded on startup

#### **Tier 3: User Interactions** (Session-based)
- Chat history
- Analysis results
- Workflow executions
- Stored in KnowledgeGraph, persisted with backups

---

## 📍 Current Mock/Placeholder Locations

### **1. Pattern Engine Fallbacks** (`core/pattern_engine.py`)
**Function**: `_get_macro_regime_placeholder()`

```python
# When macro data unavailable, returns structured placeholder
return {
    'short_cycle_position': 'Data Pending',
    'unemployment': 'Data Pending',
    'source': 'placeholder'
}
```
**Status**: Partially real - FRED integration works, but falls back when API fails

### **2. Data Harvester Economic Fallback** (`agents/data_harvester.py`)
**Function**: `harvest_economic_data()`

```python
# Last resort when FRED API unavailable
return {
    'GDP': {'value': 'unavailable', 'trend': 'FRED API required'},
    'note': 'Configure FRED_API_KEY for real data'
}
```
**Status**: Real API configured, fallback only triggers on API failure

### **3. Relationship Hunter Correlation** (`agents/relationship_hunter.py`)
**Function**: `find_correlations()`

```python
return f"{target} correlation data unavailable"
```
**Status**: Uses sector correlation matrix from knowledge base when market data unavailable

### **4. Governance Tab Metrics** (documented issue)
- Some governance metrics show static placeholder values
- Real governance hooks exist but display layer uses hardcoded values
- **Location**: `dawsos/ui/governance_tab.py`

---

## 🌱 How to Seed the System

### **Method 1: Automatic Seeding (On Startup)**

The system automatically seeds on first run:

**Location**: `main.py` startup sequence
```python
# Auto-seeds if graph has < 40 nodes
if st.session_state.graph.get_stats()['total_nodes'] < 40:
    import seed_knowledge_graph
    seed_knowledge_graph.seed_buffett_framework(st.session_state.graph)
    seed_knowledge_graph.seed_dalio_framework(st.session_state.graph)
    seed_knowledge_graph.seed_financial_calculations(st.session_state.graph)
    seed_knowledge_graph.seed_investment_examples(st.session_state.graph)
    st.session_state.persistence.save_graph_with_backup(st.session_state.graph)
```

**What Gets Seeded**:
- Buffett investment framework (moats, circle of competence, intrinsic value)
- Dalio economic machine (debt cycles, credit growth, productivity)
- Financial calculation formulas (DCF, ROIC, FCF, Owner Earnings)
- Investment examples (AAPL, JNJ, KO case studies)

### **Method 2: Manual Seeding via Script**

**Run the seeding script**:
```bash
cd dawsos
source ../venv/bin/activate
python3 seed_knowledge_graph.py
```

**Or seed programmatically**:
```python
from core.knowledge_graph import KnowledgeGraph
import seed_knowledge_graph

graph = KnowledgeGraph()
seed_knowledge_graph.seed_buffett_framework(graph)
seed_knowledge_graph.seed_dalio_framework(graph)
graph.save('storage/graph.json')
```

### **Method 3: Load JSON Datasets**

**Existing datasets auto-load** via KnowledgeLoader:
```python
from core.knowledge_loader import KnowledgeLoader

loader = KnowledgeLoader()
loader.load_all_datasets()

# Access loaded data
sp500_companies = loader.get_dataset('sp500_companies')
sector_correlations = loader.get_dataset('sector_correlations')
```

**Add new dataset**:
```bash
# 1. Create JSON file
cat > dawsos/storage/knowledge/my_dataset.json << 'EOF'
{
  "name": "My Custom Dataset",
  "version": "1.0",
  "data": {
    "companies": [
      {"ticker": "AAPL", "sector": "Technology", "market_cap": 3000000000000}
    ]
  }
}
EOF

# 2. System auto-loads on next startup
# No code changes needed - KnowledgeLoader scans the directory
```

### **Method 4: Seed Historical Market Data**

**Create bulk loading script**:
```python
# scripts/load_historical_data.py
from core.knowledge_graph import KnowledgeGraph
from capabilities.market_data import MarketDataCapability
from datetime import datetime, timedelta
import time

graph = KnowledgeGraph()
market = MarketDataCapability()

# Load 5 years of daily data for S&P 500
tickers = ['SPY', 'QQQ', 'DIA', 'IWM']  # Start with ETFs
end_date = datetime.now()
start_date = end_date - timedelta(days=365*5)

for ticker in tickers:
    print(f"Loading historical data for {ticker}...")

    # Get historical prices
    historical = market.get_historical_prices(ticker, start_date, end_date)

    # Store in graph
    for data_point in historical:
        node_id = graph.add_node('price_data', {
            'ticker': ticker,
            'date': data_point['date'],
            'open': data_point['open'],
            'high': data_point['high'],
            'low': data_point['low'],
            'close': data_point['close'],
            'volume': data_point['volume']
        })

        # Create relationship
        graph.connect(f"{ticker}_company", node_id, 'has_price_history')

    time.sleep(0.1)  # Rate limiting

graph.save('storage/graph_with_historical.json')
print("Historical data loaded successfully!")
```

**Run it**:
```bash
cd dawsos
source ../venv/bin/activate
python3 scripts/load_historical_data.py
```

### **Method 5: User-Driven Data Population**

**Via UI Chat**:
```
User: "Analyze AAPL financials for the last 5 years"
→ System calls data_harvester
→ Fetches from FMP API
→ Stores in KnowledgeGraph
→ Data persists for future queries
```

**Via Pattern Execution**:
```
User: "Run equity analysis on TSLA"
→ UniversalExecutor finds "equity_analysis" pattern
→ Pattern executes: harvest → digest → analyze → forecast
→ All results stored in graph
→ Checkpointed with backup
```

---

## 🚫 Removing Mock Implementations

### **1. Remove Pattern Engine Fallbacks**

**Current implementation** (`core/pattern_engine.py` - `_empty_macro_data()` method):
```python
def _empty_macro_data(self) -> Dict[str, Any]:
    """Return empty macro data structure when real data unavailable"""
    return {
        'short_cycle_position': 'Data Pending',
        'short_cycle_phase': 'Analysis Required',
        # ... more placeholders
    }
```

**Recommended fix**: Raise exception instead of returning placeholders
```python
def _empty_macro_data(self) -> Dict[str, Any]:
    """Raise error when macro data unavailable"""
    raise ValueError(
        "Macro economic data unavailable. "
        "Ensure FRED_API_KEY is configured and data_harvester agent is operational."
    )
```

### **2. Remove Data Harvester Fallbacks**

**Current implementation** (`agents/data_harvester.py` - `harvest_economic_data()` method):
```python
return {
    'response': 'Economic data source unavailable',
    'data': {
        'GDP': {'value': 'unavailable', 'trend': 'FRED API required'},
        # ...
    }
}
```

**Fix**: Return error dict with clear action needed
```python
if not fred_available:
    return {
        'error': 'FRED API not configured',
        'action_required': 'Set FRED_API_KEY in dawsos/.env',
        'status': 'data_unavailable'
    }
```

### **3. Enforce Real Data Only Mode**

**Add strict mode to UniversalExecutor**:
```python
class UniversalExecutor:
    def __init__(self, graph, registry, runtime, strict_mode=False):
        self.strict_mode = strict_mode  # Fail on missing data instead of fallback

    def execute(self, request):
        try:
            result = self.pattern_engine.execute_pattern(...)
        except DataUnavailableError as e:
            if self.strict_mode:
                raise  # Fail fast
            else:
                return self._graceful_degradation(e)  # Fallback
```

**Enable in production**:
```python
# In dawsos/main.py
st.session_state.executor = UniversalExecutor(
    st.session_state.graph,
    st.session_state.agent_runtime.agent_registry,
    runtime=st.session_state.agent_runtime,
    strict_mode=True  # No fallbacks allowed
)
```

---

## 📊 Data Validation & Quality Checks

### **Check What Data is Real vs Mock**

**Run diagnostic script**:
```python
# scripts/audit_data_sources.py
from core.knowledge_graph import KnowledgeGraph
from capabilities.market_data import MarketDataCapability
from capabilities.fred_data import FredDataCapability

graph = KnowledgeGraph()
market = MarketDataCapability()
fred = FredDataCapability()

print("=== Data Source Audit ===\n")

# Check API connectivity
print("API Status:")
print(f"  FMP API Key: {'✓ Configured' if market.api_key else '✗ Missing'}")
print(f"  FRED API Key: {'✓ Configured' if fred.api_key else '✗ Missing'}")

# Test API calls
try:
    spy_quote = market.get_quote('SPY')
    print(f"  FMP API Call: {'✓ Success' if 'price' in spy_quote else '✗ Failed'}")
except:
    print(f"  FMP API Call: ✗ Failed")

try:
    gdp_data = fred.get_latest('GDP')
    print(f"  FRED API Call: {'✓ Success' if gdp_data.get('value') else '✗ Failed'}")
except:
    print(f"  FRED API Call: ✗ Failed")

# Check graph data
stats = graph.get_stats()
print(f"\nKnowledge Graph:")
print(f"  Total Nodes: {stats['total_nodes']}")
print(f"  Total Edges: {stats['total_edges']}")
print(f"  Node Types: {', '.join(stats['node_types'].keys())}")

# Check for placeholder data
placeholder_count = 0
for node_id, node_data in graph.nodes.items():
    if any(val == 'unavailable' or val == 'Data Pending'
           for val in str(node_data.get('properties', {})).split()):
        placeholder_count += 1

print(f"  Nodes with Placeholder Data: {placeholder_count}")
print(f"  Data Quality: {'✓ Good' if placeholder_count < 10 else '⚠ Needs Attention'}")
```

### **Monitor Real-time Data Usage**

**Add telemetry to capabilities**:
```python
# In MarketDataCapability
def get_quote(self, symbol):
    self.metrics['api_calls'] += 1
    self.metrics['last_call'] = datetime.now()

    result = self._make_api_call(...)

    if 'error' in result:
        self.metrics['api_errors'] += 1
    else:
        self.metrics['api_success'] += 1

    return result

def get_metrics(self):
    return {
        'total_calls': self.metrics['api_calls'],
        'success_rate': self.metrics['api_success'] / self.metrics['api_calls'],
        'cache_hit_rate': self.get_cache_stats()['cache_hit_rate']
    }
```

---

## 🎯 Production Readiness Checklist

### **To Go 100% Real Data**:

- [ ] **Configure all API keys** in `dawsos/.env`
  ```bash
  FMP_API_KEY=your_fmp_key
  FRED_API_KEY=your_fred_key
  NEWSAPI_KEY=your_news_key
  ```

- [ ] **Load historical data** (run bulk loading scripts)
  ```bash
  python3 scripts/load_historical_data.py
  python3 scripts/load_company_fundamentals.py
  python3 scripts/load_economic_history.py
  ```

- [ ] **Remove fallback code**
  - Delete `_empty_macro_data()` method
  - Replace `'unavailable'` returns with exceptions
  - Enable `strict_mode=True` in UniversalExecutor

- [ ] **Add data quality gates**
  ```python
  def validate_data_quality(data):
      if data.get('source') == 'placeholder':
          raise DataQualityError("Placeholder data not allowed in production")
      if data.get('quality') == 'low':
          logger.warning("Low quality data detected")
      return data
  ```

- [ ] **Set up monitoring**
  - Track API call success rates
  - Monitor cache hit rates (target >80%)
  - Alert on placeholder data creation
  - Dashboard for data freshness

- [ ] **Test with real workflows**
  ```bash
  # Test end-to-end with real data
  pytest tests/integration/test_real_data_flow.py --strict
  ```

---

## 🔄 Current Data Bootstrap Sequence

**On app startup** (main.py):
1. Load environment variables (`FRED_API_KEY`, `FMP_API_KEY`, etc.)
2. Initialize KnowledgeGraph (empty)
3. Try to load existing graph from `storage/graph.json`
4. If nodes < 40, run seeding:
   - Buffett framework → 15+ nodes
   - Dalio framework → 20+ nodes
   - Financial calculations → 10+ nodes
   - Investment examples → 5+ nodes
5. Initialize capabilities (FMP, FRED, News APIs)
6. Register 15 agents with capabilities
7. Initialize PatternEngine (loads 45+ patterns)
8. Initialize UniversalExecutor
9. Ready to accept user requests

**All data flows through**:
- **Entry**: UniversalExecutor
- **Routing**: PatternEngine (pattern matching)
- **Execution**: AgentRuntime (agent delegation)
- **Storage**: KnowledgeGraph (persistence)
- **Backup**: PersistenceManager (30-day rotation)

**Zero mock data** once APIs are configured and historical data is loaded!
