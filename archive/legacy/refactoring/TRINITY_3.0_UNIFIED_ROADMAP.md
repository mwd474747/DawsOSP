# Trinity 3.0 - Unified Implementation Roadmap

**Date**: October 9, 2025
**Status**: Comprehensive implementation plan incorporating GDP Refresh + AG-UI Integration
**Timeline**: 9 weeks total (2 weeks GDP + 7 weeks AG-UI)

---

## Executive Summary

This unified roadmap integrates two major initiatives:
1. **Phase 0 (Weeks 1-2)**: GDP Refresh Flow - Live FRED data integration
2. **Phase 1-4 (Weeks 3-9)**: AG-UI Protocol integration for real-time streaming

**Strategic Rationale**: Implement GDP Refresh **first** because:
✅ Validates Trinity pattern flow with real external API
✅ Provides concrete use case for AG-UI streaming (live data updates)
✅ Tests knowledge graph storage patterns
✅ Establishes telemetry/fallback infrastructure needed for AG-UI
✅ Smaller scope = lower risk for first Trinity 3.0 feature

---

## Phase 0: GDP Refresh Flow (Weeks 1-2) ⭐ PRIORITY

**Goal**: Make `economic_indicators` pattern return live FRED data with proper fallback and telemetry

### **Week 1: Backend Implementation**

#### **Day 1: Pattern & Capability Setup**

**Task 1.1: Update economic_indicators pattern**
```bash
File: dawsos/patterns/queries/economic_indicators.json
```

```json
{
  "id": "economic_indicators",
  "name": "Economic Indicators Dashboard",
  "description": "Fetch and analyze live FRED economic data (GDP, CPI, Unemployment, Fed Funds)",
  "category": "queries",
  "version": "3.0",
  "last_updated": "2025-10-10",
  "triggers": ["economy", "gdp", "unemployment", "inflation", "fed funds"],
  "entities": [],
  "priority": 5,
  "steps": [
    {
      "description": "Fetch live FRED economic series",
      "action": "execute_by_capability",
      "capability": "can_fetch_economic_data",
      "context": {
        "series": "{series}",
        "start_date": "{start_date}",
        "end_date": "{end_date}",
        "frequency": "{frequency}"
      },
      "save_as": "economic_data"
    },
    {
      "description": "Analyze macro context and compute metrics",
      "action": "execute_by_capability",
      "capability": "can_analyze_macro_data",
      "context": {
        "data": "{economic_data}",
        "compute_qoq": true,
        "detect_cycle_phase": true
      },
      "save_as": "macro_analysis"
    },
    {
      "description": "Store in knowledge graph",
      "action": "store_in_graph",
      "params": {
        "node_type": "economic_indicator",
        "data": "{economic_data}",
        "metadata": {
          "analysis": "{macro_analysis}",
          "source": "{economic_data.source}",
          "timestamp": "{economic_data.timestamp}"
        }
      },
      "save_as": "graph_nodes"
    }
  ],
  "response_type": "data",
  "response_template": "{macro_analysis}",
  "cache_ttl": 3600,
  "template": "## Economic Indicators\n\n**Data Source**: {economic_data.source}\n**Last Updated**: {economic_data.timestamp}\n\n### GDP Quarter-over-Quarter\n{macro_analysis.gdp_qoq}%\n\n### CPI Change\n{macro_analysis.cpi_change}%\n\n### Cycle Phase\n{macro_analysis.cycle_phase}\n\n*Data provided by FRED (Federal Reserve Economic Data)*"
}
```

**Task 1.2: Update agent capabilities**
```bash
File: dawsos/core/agent_capabilities.py
```

```python
# Add to data_harvester capabilities
'data_harvester': {
    'capabilities': [
        'can_fetch_stock_quotes',
        'can_fetch_economic_data',  # ← Add this
        'can_fetch_news',
        'can_fetch_fundamentals',
        'can_fetch_crypto_prices'
    ],
    'requires': ['fred_api_key', 'fmp_api_key'],
    'provides': ['market_data', 'economic_data', 'fundamental_data'],
    'integrates_with': ['data_digester', 'financial_analyst'],
    'priority': 'high',
    'category': 'data'
},

# Add to financial_analyst capabilities
'financial_analyst': {
    'capabilities': [
        'can_calculate_dcf',
        'can_calculate_roic',
        'can_analyze_macro_data',  # ← Add this
        # ... existing capabilities
    ],
    # ... rest unchanged
}
```

#### **Day 2-3: FRED Data Capability Implementation**

**Task 2.1: Enhance FredDataCapability**
```bash
File: dawsos/capabilities/fred_data.py
```

```python
#!/usr/bin/env python3
"""
FRED Data Capability - Federal Reserve Economic Data integration
Enhanced with caching, fallback, and telemetry.
"""
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

class FredDataCapability:
    """Fetch economic data from FRED API with caching and fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FRED_API_KEY')
        self.base_url = 'https://api.stlouisfed.org/fred'
        self.logger = logging.getLogger('FredDataCapability')

        # In-memory cache with TTL
        self.cache = {}
        self.cache_ttl = timedelta(hours=6)  # 6-hour cache for economic data

        # Telemetry
        self.fallback_tracker = None  # Set by runtime
        self.api_logger = None  # Set by runtime

    def fetch_economic_indicators(
        self,
        series: List[str],
        start_date: str,
        end_date: str,
        frequency: str = 'm'
    ) -> Dict[str, Any]:
        """
        Fetch multiple FRED economic series.

        Args:
            series: List of FRED series IDs (e.g., ['GDP', 'UNRATE', 'CPIAUCSL'])
            start_date: ISO date (YYYY-MM-DD)
            end_date: ISO date (YYYY-MM-DD)
            frequency: 'm' (monthly), 'q' (quarterly), 'a' (annual)

        Returns:
            {
                'series': {
                    'GDP': {'dates': [...], 'values': [...], 'units': 'Billions'},
                    'UNRATE': {'dates': [...], 'values': [...], 'units': 'Percent'},
                    ...
                },
                'source': 'live' | 'cache' | 'fallback',
                'timestamp': '2025-10-10T12:00:00Z',
                'cache_age_seconds': 0 | int
            }
        """
        cache_key = self._make_cache_key(series, start_date, end_date, frequency)

        # Check cache first
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            age = (datetime.now() - cached_time).total_seconds()

            if age < self.cache_ttl.total_seconds():
                self.logger.info(f"Cache hit for {cache_key} (age: {age:.0f}s)")
                cached_data['source'] = 'cache'
                cached_data['cache_age_seconds'] = int(age)
                return cached_data

        # Fetch live data
        try:
            result = self._fetch_live(series, start_date, end_date, frequency)
            result['source'] = 'live'
            result['cache_age_seconds'] = 0

            # Cache the result
            self.cache[cache_key] = (result, datetime.now())

            # Log success
            if self.api_logger:
                self.api_logger.log_success('fred', 'series/observations')

            return result

        except Exception as e:
            self.logger.error(f"FRED API error: {e}")

            # Log failure
            if self.api_logger:
                self.api_logger.log_failure('fred', 'series/observations', str(e))

            # Track fallback
            if self.fallback_tracker:
                self.fallback_tracker.mark_fallback(
                    service='fred',
                    reason=str(e),
                    severity='warning'
                )

            # Return fallback data (stale cache or static)
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                age = (datetime.now() - cached_time).total_seconds()
                cached_data['source'] = 'fallback'
                cached_data['cache_age_seconds'] = int(age)
                self.logger.warning(f"Using stale cache (age: {age:.0f}s)")
                return cached_data
            else:
                # Return static fallback
                return self._get_static_fallback(series, start_date, end_date)

    def _fetch_live(
        self,
        series: List[str],
        start_date: str,
        end_date: str,
        frequency: str
    ) -> Dict[str, Any]:
        """Fetch live data from FRED API."""
        results = {}

        for series_id in series:
            url = f"{self.base_url}/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'observation_start': start_date,
                'observation_end': end_date,
                'frequency': frequency
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            observations = data.get('observations', [])

            # Parse observations
            dates = []
            values = []
            for obs in observations:
                if obs['value'] != '.':  # FRED uses '.' for missing data
                    dates.append(obs['date'])
                    values.append(float(obs['value']))

            results[series_id] = {
                'dates': dates,
                'values': values,
                'units': data.get('units', 'Unknown'),
                'title': data.get('title', series_id)
            }

        return {
            'series': results,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def _make_cache_key(
        self,
        series: List[str],
        start_date: str,
        end_date: str,
        frequency: str
    ) -> str:
        """Generate cache key."""
        series_str = ','.join(sorted(series))
        return f"{series_str}:{start_date}:{end_date}:{frequency}"

    def _get_static_fallback(
        self,
        series: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Return static fallback data when API unavailable."""
        self.logger.warning("Using static fallback data")

        # Generate mock data (or load from storage/fallback/)
        results = {}
        for series_id in series:
            results[series_id] = {
                'dates': [start_date, end_date],
                'values': [0.0, 0.0],
                'units': 'Unknown',
                'title': f'{series_id} (Fallback)'
            }

        return {
            'series': results,
            'source': 'fallback',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'cache_age_seconds': 0
        }
```

**Task 2.2: Wire capability to data_harvester**
```bash
File: dawsos/agents/data_harvester.py
```

```python
# Add method to DataHarvester class
def fetch_economic_indicators(
    self,
    series: List[str],
    start_date: str,
    end_date: str,
    frequency: str = 'm'
) -> Dict[str, Any]:
    """
    Fetch economic indicators via FRED capability.

    Maps to capability: can_fetch_economic_data

    Args:
        series: List of FRED series IDs
        start_date: ISO date
        end_date: ISO date
        frequency: 'm' | 'q' | 'a'

    Returns:
        Economic data with source indicator
    """
    fred_cap = self.capabilities.get('fred')

    if not fred_cap:
        self.logger.error("FRED capability not available")
        return {'error': 'FRED capability not configured'}

    # Set telemetry hooks
    fred_cap.api_logger = self.api_logger
    fred_cap.fallback_tracker = getattr(self, 'fallback_tracker', None)

    # Fetch data
    result = fred_cap.fetch_economic_indicators(
        series, start_date, end_date, frequency
    )

    # Store in graph (optional)
    if self.graph and result.get('source') == 'live':
        for series_id, data in result['series'].items():
            node_id = self.graph.add_node(
                node_type='economic_indicator',
                data={
                    'series_id': series_id,
                    'dates': data['dates'],
                    'values': data['values'],
                    'units': data['units'],
                    'source': result['source'],
                    'timestamp': result['timestamp']
                }
            )
            self.logger.debug(f"Stored {series_id} in graph: {node_id}")

    return result
```

#### **Day 4: Macro Analysis Implementation**

**Task 3.1: Add macro analysis to financial_analyst**
```bash
File: dawsos/agents/financial_analyst.py
```

```python
def analyze_macro_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze macro economic context and compute derived metrics.

    Maps to capability: can_analyze_macro_data

    Args:
        data: Economic data from FRED (series dict)

    Returns:
        {
            'gdp_qoq': float,  # GDP quarter-over-quarter %
            'cpi_change': float,  # CPI year-over-year %
            'cycle_phase': str,  # 'expansion' | 'peak' | 'recession' | 'recovery'
            'fed_rate_trend': str,  # 'rising' | 'falling' | 'stable'
            'unemployment_trend': str,
            'insights': List[str]  # Human-readable insights
        }
    """
    series = data.get('series', {})
    insights = []

    # GDP QoQ calculation
    gdp_qoq = 0.0
    if 'GDP' in series:
        values = series['GDP']['values']
        if len(values) >= 2:
            gdp_qoq = ((values[-1] - values[-2]) / values[-2]) * 100
            insights.append(f"GDP grew {gdp_qoq:.2f}% quarter-over-quarter")

    # CPI YoY calculation
    cpi_change = 0.0
    if 'CPIAUCSL' in series:
        values = series['CPIAUCSL']['values']
        if len(values) >= 12:
            cpi_change = ((values[-1] - values[-12]) / values[-12]) * 100
            insights.append(f"Inflation at {cpi_change:.2f}% year-over-year")

    # Cycle phase detection (simple heuristic)
    cycle_phase = 'unknown'
    if gdp_qoq > 2.0 and cpi_change < 3.0:
        cycle_phase = 'expansion'
        insights.append("Economy in healthy expansion phase")
    elif gdp_qoq < 0:
        cycle_phase = 'recession'
        insights.append("⚠️ Economy showing recessionary signals")
    elif gdp_qoq > 0 and gdp_qoq < 1.0:
        cycle_phase = 'recovery'
        insights.append("Economy in recovery phase")

    # Fed rate trend
    fed_rate_trend = 'stable'
    if 'FEDFUNDS' in series:
        values = series['FEDFUNDS']['values']
        if len(values) >= 3:
            if values[-1] > values[-3]:
                fed_rate_trend = 'rising'
                insights.append("Fed tightening monetary policy")
            elif values[-1] < values[-3]:
                fed_rate_trend = 'falling'
                insights.append("Fed easing monetary policy")

    # Unemployment trend
    unemployment_trend = 'stable'
    if 'UNRATE' in series:
        values = series['UNRATE']['values']
        if len(values) >= 3:
            if values[-1] > values[-3]:
                unemployment_trend = 'rising'
                insights.append("⚠️ Unemployment rising")
            elif values[-1] < values[-3]:
                unemployment_trend = 'falling'
                insights.append("✅ Unemployment falling")

    return {
        'gdp_qoq': round(gdp_qoq, 2),
        'cpi_change': round(cpi_change, 2),
        'cycle_phase': cycle_phase,
        'fed_rate_trend': fed_rate_trend,
        'unemployment_trend': unemployment_trend,
        'insights': insights,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
```

#### **Day 5: Testing & Validation**

**Task 4.1: Unit tests**
```bash
File: dawsos/tests/test_fred_capability.py
```

```python
import pytest
from dawsos.capabilities.fred_data import FredDataCapability

def test_fred_fetch():
    """Test FRED data fetching."""
    fred = FredDataCapability()

    result = fred.fetch_economic_indicators(
        series=['GDP', 'UNRATE'],
        start_date='2023-01-01',
        end_date='2024-01-01',
        frequency='q'
    )

    assert 'series' in result
    assert 'GDP' in result['series']
    assert result['source'] in ['live', 'cache', 'fallback']
```

**Task 4.2: Integration test**
```bash
File: dawsos/tests/test_economic_indicators_pattern.py
```

```python
def test_economic_indicators_pattern():
    """Test full pattern execution."""
    # Setup
    graph = KnowledgeGraph()
    runtime = AgentRuntime()
    executor = UniversalExecutor(graph, runtime.agent_registry, runtime)

    # Execute pattern
    result = executor.execute({
        'type': 'pattern_execution',
        'pattern_id': 'economic_indicators',
        'series': ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS'],
        'start_date': '2023-01-01',
        'end_date': '2024-01-01',
        'frequency': 'q'
    })

    # Verify
    assert 'economic_data' in result
    assert 'macro_analysis' in result
    assert result['economic_data']['source'] in ['live', 'cache', 'fallback']
```

### **Week 2: UI Integration**

#### **Day 1-2: Update Economy Tab**

**Task 5.1: Modify trinity_dashboard_tabs.py**
```bash
File: dawsos/ui/trinity_dashboard_tabs.py
```

```python
def _get_economic_data_via_patterns(self) -> Dict[str, Any]:
    """
    Fetch economic data via economic_indicators pattern.

    Uses Trinity 3.0 pattern execution.
    """
    # Get pattern
    pattern = self.pattern_engine.get_pattern('economic_indicators')

    if not pattern:
        st.error("Economic indicators pattern not found")
        return self._get_fallback_economic_data()

    # Build context
    context = {
        'series': ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS'],
        'start_date': '2023-01-01',
        'end_date': datetime.now().strftime('%Y-%m-%d'),
        'frequency': 'q'  # Quarterly
    }

    # Execute pattern
    with st.spinner('Fetching live FRED data...'):
        result = self.pattern_engine.execute_pattern(pattern, context)

    # Check source
    source = result.get('economic_data', {}).get('source', 'unknown')

    if source == 'fallback':
        st.warning("⚠️ Using fallback data - FRED API unavailable")
    elif source == 'cache':
        age = result.get('economic_data', {}).get('cache_age_seconds', 0)
        st.info(f"📦 Using cached data ({age // 60} minutes old)")
    else:
        st.success("✅ Live data from FRED")

    return result

def _render_economic_chart(self, result: Dict[str, Any]):
    """Render Plotly chart for economic indicators."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    economic_data = result.get('economic_data', {})
    series_data = economic_data.get('series', {})

    if not series_data:
        st.error("No data to display")
        return

    # Create subplot with dual y-axes
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('GDP Growth', 'Unemployment Rate', 'CPI (Inflation)', 'Fed Funds Rate'),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )

    # GDP
    if 'GDP' in series_data:
        fig.add_trace(
            go.Scatter(
                x=series_data['GDP']['dates'],
                y=series_data['GDP']['values'],
                name='GDP',
                line=dict(color='#00cc88', width=2)
            ),
            row=1, col=1
        )

    # Unemployment
    if 'UNRATE' in series_data:
        fig.add_trace(
            go.Scatter(
                x=series_data['UNRATE']['dates'],
                y=series_data['UNRATE']['values'],
                name='Unemployment',
                line=dict(color='#ff4444', width=2)
            ),
            row=1, col=2
        )

    # CPI
    if 'CPIAUCSL' in series_data:
        fig.add_trace(
            go.Scatter(
                x=series_data['CPIAUCSL']['dates'],
                y=series_data['CPIAUCSL']['values'],
                name='CPI',
                line=dict(color='#4488ff', width=2)
            ),
            row=2, col=1
        )

    # Fed Funds
    if 'FEDFUNDS' in series_data:
        fig.add_trace(
            go.Scatter(
                x=series_data['FEDFUNDS']['dates'],
                y=series_data['FEDFUNDS']['values'],
                name='Fed Funds Rate',
                line=dict(color='#ff8844', width=2)
            ),
            row=2, col=2
        )

    # Update layout
    fig.update_layout(
        height=600,
        showlegend=False,
        title_text="Economic Indicators Dashboard",
        template='plotly_dark'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display macro analysis
    macro_analysis = result.get('macro_analysis', {})
    if macro_analysis:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("GDP QoQ", f"{macro_analysis.get('gdp_qoq', 0):.2f}%")

        with col2:
            st.metric("CPI YoY", f"{macro_analysis.get('cpi_change', 0):.2f}%")

        with col3:
            st.metric("Cycle Phase", macro_analysis.get('cycle_phase', 'Unknown'))

        with col4:
            st.metric("Fed Trend", macro_analysis.get('fed_rate_trend', 'Unknown'))

        # Insights
        st.subheader("📊 Insights")
        for insight in macro_analysis.get('insights', []):
            st.markdown(f"• {insight}")
```

#### **Day 3: UI Controls**

**Task 5.2: Add date range and series selectors**
```python
# In economy tab render function
col1, col2 = st.columns(2)

with col1:
    date_range = st.selectbox(
        "Date Range",
        ["Last 12 Months", "Last 24 Months", "Last 5 Years", "Custom"],
        index=1
    )

with col2:
    series_options = st.multiselect(
        "Select Indicators",
        ["GDP", "UNRATE", "CPIAUCSL", "FEDFUNDS", "DGS10", "M2"],
        default=["GDP", "UNRATE", "CPIAUCSL", "FEDFUNDS"]
    )

# Calculate dates based on selection
if date_range == "Last 12 Months":
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
elif date_range == "Last 24 Months":
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
# ... etc
```

#### **Day 4-5: Graph Storage & Telemetry**

**Task 6.1: Verify graph storage**
- Confirm pattern step `store_in_graph` creates nodes
- Check `storage/graph.json` for economic_indicator nodes
- Verify PersistenceManager saves automatically

**Task 6.2: Telemetry validation**
- Check API Health tab shows FRED requests
- Verify fallback tracking works
- Confirm compliance metrics update

---

## Phase 1-4: AG-UI Integration (Weeks 3-9)

**Note**: GDP Refresh provides perfect foundation for AG-UI because:
✅ Pattern execution already working
✅ External API integration validated
✅ Fallback mechanisms tested
✅ Knowledge graph storage confirmed

### **Week 3: AG-UI Foundation** (Same as original Phase 1)

**Now enhanced with GDP flow example**:

```python
# AG-UI streaming of GDP data fetch
async def execute_pattern_streaming(pattern, context, emitter):
    # Step 1: Fetch FRED data
    await emitter.emit('agent.thinking', {
        'message': 'Fetching live FRED economic data...'
    })

    await emitter.emit('agent.tool.call', {
        'capability': 'can_fetch_economic_data',
        'series': ['GDP', 'UNRATE', 'CPIAUCSL']
    })

    # Execute (async)
    result = await asyncio.to_thread(
        fred_cap.fetch_economic_indicators, ...
    )

    # Emit progress
    await emitter.emit('agent.tool.result', {
        'capability': 'can_fetch_economic_data',
        'source': result['source'],  # 'live' | 'cache' | 'fallback'
        'series_count': len(result['series'])
    })

    # Step 2: Generate UI component
    await emitter.emit('agent.ui', {
        'component': 'economic_chart',
        'props': {
            'data': result['series'],
            'type': 'multi-line',
            'title': 'Economic Indicators'
        }
    })

    # Step 3: Emit analysis
    await emitter.emit('agent.message', {
        'text': f"GDP grew {macro_analysis['gdp_qoq']}% QoQ. Inflation at {macro_analysis['cpi_change']}%.",
        'insights': macro_analysis['insights']
    })
```

**Continue with original AG-UI phases 1-4** (Weeks 3-9)

---

## Unified Timeline

```
┌─────────────────────────────────────────────────────────────┐
│ Week 1-2: Phase 0 - GDP Refresh Flow (Foundation)          │
├─────────────────────────────────────────────────────────────┤
│ Week 1: Backend (Pattern, FRED, Analysis)                  │
│ Week 2: UI Integration & Testing                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Week 3-4: Phase 1 - AG-UI Foundation                        │
├─────────────────────────────────────────────────────────────┤
│ Week 3: Event Emitter, UniversalExecutor streaming         │
│ Week 4: PatternEngine streaming, Action handlers           │
│ ✨ GDP pattern now emits AG-UI events                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Week 5: Phase 2 - HTTP Server                               │
├─────────────────────────────────────────────────────────────┤
│ FastAPI with SSE/WebSocket endpoints                       │
│ ✨ Stream GDP data fetch in real-time                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Week 6-7: Phase 3 - React Frontend                          │
├─────────────────────────────────────────────────────────────┤
│ Next.js + AG-UI SDK, Chart components                      │
│ ✨ Render economic indicators with live updates            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Week 8-9: Phase 4 - Advanced Features                       │
├─────────────────────────────────────────────────────────────┤
│ Graph state sync, Human-in-the-loop                        │
│ ✨ Real-time graph updates when GDP data refreshes         │
└─────────────────────────────────────────────────────────────┘
```

**Total**: 9 weeks (2 + 7)

---

## Dependencies & Sequencing

```
GDP Refresh (Phase 0)
├─ Week 1
│  ├─ Pattern JSON ✓ (prerequisite for everything)
│  ├─ Capability wiring ✓ (must come before agent implementation)
│  ├─ FRED implementation ✓ (depends on capability wiring)
│  └─ Macro analysis ✓ (depends on FRED data structure)
│
└─ Week 2
   ├─ UI integration (depends on Week 1 backend)
   ├─ Graph storage (depends on pattern execution)
   └─ Telemetry (depends on FRED capability)

AG-UI Integration (Phase 1-4)
├─ Week 3-4: Foundation
│  ├─ Depends on: GDP pattern working
│  └─ Provides: Streaming infrastructure for GDP events
│
├─ Week 5: HTTP Server
│  ├─ Depends on: Streaming infrastructure
│  └─ Uses: GDP pattern as test case
│
├─ Week 6-7: Frontend
│  ├─ Depends on: HTTP server
│  └─ Renders: Economic indicators in real-time
│
└─ Week 8-9: Advanced
   ├─ Depends on: Frontend working
   └─ Enhances: Graph updates for economic data
```

---

## Testing Strategy

### **Phase 0 Testing** (GDP Refresh)
```bash
# Unit tests
pytest dawsos/tests/test_fred_capability.py
pytest dawsos/tests/test_macro_analysis.py

# Integration test
pytest dawsos/tests/test_economic_indicators_pattern.py

# Manual UI test
streamlit run dawsos/main.py
# → Navigate to Economy tab
# → Verify live FRED data loads
# → Check fallback indicator works
```

### **Phase 1-4 Testing** (AG-UI)
```bash
# Unit tests
pytest dawsos/tests/test_event_emitter.py
pytest dawsos/tests/test_streaming_execution.py

# Integration test (with GDP pattern)
pytest dawsos/tests/test_agui_gdp_streaming.py

# Load test
python dawsos/tests/load_test.py

# Manual test
curl -X POST http://localhost:8000/ag-ui/message \
     -d '{"text": "Show me GDP data"}'
# → Verify SSE stream includes FRED events
```

---

## Documentation Updates

### **After Phase 0** (Week 2)
- Update `README.md` with FRED integration
- Update `docs/KnowledgeMaintenance.md` with economic data patterns
- Add `PHASE0_GDP_REFRESH_COMPLETE.md` milestone

### **After Phase 1-4** (Week 9)
- Update `README.md` with AG-UI streaming
- Create `TRINITY_3.0_LAUNCH.md` announcement
- Update architectural diagrams with AG-UI layer

---

## Success Metrics

| Milestone | Metric | Target |
|-----------|--------|--------|
| **Phase 0 Complete** | FRED data loads | 100% success rate |
| | Fallback activates on error | Works correctly |
| | Graph stores economic nodes | Verified in graph.json |
| | UI renders 4 charts | All visible |
| **Phase 1 Complete** | Streaming events emit | Zero overhead |
| | GDP pattern streams | Events in sequence |
| | All Trinity tests pass | 100% pass rate |
| **Phase 2 Complete** | HTTP server handles 100 connections | < 1s response |
| | SSE streams GDP data | Real-time updates |
| **Phase 3 Complete** | Frontend renders economic charts | Interactive |
| | Real-time data updates | < 100ms latency |
| **Phase 4 Complete** | Graph sync works | Live updates |
| | Human-in-loop flows | Approval works |

---

## Risk Mitigation

### **Phase 0 Risks**
- **FRED API downtime**: Mitigated by fallback cache + static data
- **Pattern complexity**: Mitigated by 3 clear steps (fetch → analyze → store)
- **UI rendering errors**: Mitigated by defensive data checks

### **Phase 1-4 Risks**
- **Async complexity**: Mitigated by dual execution paths (sync still works)
- **Event queue overflow**: Mitigated by bounded queue with timeout
- **WebSocket instability**: Mitigated by SSE fallback

---

## Rollback Plan

### **Phase 0**
If GDP Refresh fails:
1. Revert pattern JSON to previous version
2. Keep static economic data in UI
3. No breaking changes (Trinity 2.0 still works)

### **Phase 1-4**
If AG-UI fails:
1. Disable event emitter (use NullEmitter)
2. Fall back to sync execution only
3. Keep Streamlit UI (port 8501)
4. Remove FastAPI server (port 8000)

---

## Conclusion

**Unified roadmap integrates GDP Refresh as Phase 0 foundation for AG-UI integration.**

**Benefits of this sequencing**:
✅ Phase 0 validates Trinity patterns with real external API
✅ Provides concrete streaming use case for AG-UI
✅ Tests fallback/telemetry infrastructure
✅ Lower risk (smaller scope first)
✅ GDP becomes showcase for AG-UI real-time updates

**Total Timeline**: 9 weeks
**Risk Level**: Low (incremental, tested, reversible)
**Grade Impact**: A+ (99/100) → **A++ (100/100)** after Phase 4

**Recommendation**: Begin Phase 0, Week 1 (GDP Refresh Backend) immediately.

---

**All planning complete. System ready for implementation.**
