# Backtesting Capabilities Analysis - DawsOS Trinity 2.0

**Date**: October 16, 2025
**Purpose**: Identify existing patterns, data, and APIs that can be used for prediction backtesting

---

## 🎯 Executive Summary

DawsOS has **extensive capabilities** for running prediction backtests across multiple strategies:

- **48 executable patterns** including 8 analysis patterns directly relevant to predictions
- **27 enriched knowledge datasets** with historical benchmarks and relationships
- **FMP API** (Financial Modeling Prep) with historical data, fundamentals, and market metrics
- **FRED API** for economic indicators
- **Knowledge Graph** with 96K+ nodes tracking historical analyses

---

## 📊 Available Data Sources for Backtesting

### 1. Historical Price Data (FMP API)

**API Methods Available**:
```python
MarketDataCapability.get_historical(symbol, period='1M'|'3M'|'6M'|'1Y'|'5Y', interval='1d'|'1h'|'5m')
```

**What you get**:
- Open, High, Low, Close, Volume
- Adjustments for splits/dividends
- Intraday data (5min, 15min, 1hour)
- Up to 5 years of daily data

**Cache**: 1 hour TTL

**Use case**: Compare predictions against actual price movements

---

### 2. Fundamental Data (FMP API)

**API Methods**:
```python
get_financials(symbol, statement='income'|'balance'|'cashflow', period='annual'|'quarter')
get_key_metrics(symbol, period='annual'|'quarter')
get_analyst_estimates(symbol)
```

**What you get**:
- **Income Statement**: Revenue, EPS, operating income, margins
- **Balance Sheet**: Assets, liabilities, debt, equity
- **Cash Flow**: Operating CF, FCF, CapEx
- **Key Metrics**: P/E, P/B, ROE, ROA, debt ratios
- **Analyst Estimates**: EPS forecasts, revenue forecasts

**Cache**: 24 hours TTL

**Use case**:
- Backtest DCF valuations vs actual results
- Test Buffett Checklist predictions
- Validate financial health assessments

---

### 3. Economic Indicators (FRED API via Data Harvester)

**Available Indicators**:
- **GDP**: Real GDP, nominal GDP, GDP growth
- **Inflation**: CPI (CPIAUCSL), Core CPI, PPI
- **Employment**: Unemployment rate (UNRATE), non-farm payrolls, jobless claims
- **Interest Rates**: Fed Funds rate (FEDFUNDS), 10Y Treasury yield
- **Leading Indicators**: ISM PMI, consumer confidence, housing starts

**What you get**:
- Monthly/quarterly data going back decades
- Real-time updates
- Cached with metadata

**Use case**:
- Backtest Dalio cycle predictions
- Test economic regime forecasts
- Validate sector rotation strategies based on macro conditions

---

### 4. Enriched Knowledge Datasets (27 Files)

#### **Historical Benchmarks**:

**`economic_cycles.json`**:
```json
{
  "cycles": [
    {
      "phase": "expansion",
      "start": "2009-06",
      "end": "2020-02",
      "duration_months": 128,
      "characteristics": ["Low unemployment", "Rising GDP", "Moderate inflation"]
    }
  ]
}
```
**Use**: Compare predicted regime vs actual historical regime

**`sector_performance.json`**:
```json
{
  "Technology": {
    "5y_return": 185.3,
    "volatility": 22.1,
    "sharpe": 1.8,
    "max_drawdown": -28.4
  }
}
```
**Use**: Backtest sector rotation predictions

**`earnings_surprises.json`**:
```json
{
  "AAPL": {
    "avg_surprise_pct": 12.5,
    "beat_rate": 0.85,
    "surprise_impact_avg": 3.2
  }
}
```
**Use**: Test earnings prediction accuracy

#### **Strategy Frameworks**:

**`buffett_checklist.json`** (15 criteria):
- Durable competitive advantage?
- Predictable earnings?
- ROE consistently >15%?
- Low debt/equity?
- etc.

**Use**: Backtest value investing strategy
- Score stocks historically
- Track which met criteria
- Compare returns vs benchmark

**`dalio_framework.json`** (Economic regime mapping):
- Regime indicators → Expected outcomes
- Asset class performance by regime
- Risk/opportunity matrix

**Use**: Test economic regime predictions and positioning

**`factor_smartbeta_profiles.json`**:
- Value, Growth, Momentum, Quality, Low Volatility factors
- Historical factor performance
- Factor correlation matrix

**Use**: Test factor-based predictions

#### **Alternative Data**:

**`insider_institutional_activity.json`**:
```json
{
  "AAPL": {
    "insider_buys_3m": 12,
    "insider_sells_3m": 3,
    "institutional_ownership_pct": 61.2,
    "13f_change_qoq": 2.3
  }
}
```
**Use**: Test insider buying as prediction signal

**`alt_data_signals.json`**:
- App downloads, web traffic, satellite imagery proxies
- Social media sentiment indicators

**Use**: Test alternative data signal predictiveness

---

## 🧩 Existing Patterns for Backtesting

### Analysis Patterns (Direct Prediction Relevance)

**1. `dcf_valuation.json`** - DCF valuation model
- **Inputs**: Financials, growth assumptions, discount rate
- **Output**: Intrinsic value estimate
- **Backtest**: Compare DCF value vs actual price over time
- **Capability**: `can_calculate_dcf`

**2. `buffett_checklist.json`** - Quality/value screen
- **Inputs**: Financial metrics, moat analysis
- **Output**: Pass/fail on 15 criteria + quality score
- **Backtest**: Track stocks that passed → measure 1Y/3Y/5Y returns
- **Capability**: `can_analyze_fundamentals`

**3. `dalio_cycle.json`** - Economic regime prediction
- **Inputs**: GDP, inflation, unemployment, debt levels
- **Output**: Current regime (expansion/recession/stagflation/goldilocks)
- **Backtest**: Predicted regime vs actual economic outcomes
- **Capability**: `can_analyze_macro_trends`

**4. `earnings_analysis.json`** - Earnings prediction
- **Inputs**: Historical EPS, analyst estimates, earnings surprises
- **Output**: EPS forecast, beat/miss probability
- **Backtest**: Predicted EPS vs actual reported EPS
- **Capability**: `can_analyze_earnings`

**5. `sector_rotation.json`** - Sector allocation strategy
- **Inputs**: Economic regime, sector correlations, momentum
- **Output**: Recommended sector weights
- **Backtest**: Sector allocation vs actual sector performance
- **Capability**: `can_identify_sector_opportunities`

**6. `risk_assessment.json`** - Portfolio risk prediction
- **Inputs**: Holdings, correlations, volatility, macro risks
- **Output**: VaR, max drawdown estimate, risk score
- **Backtest**: Predicted risk vs actual drawdowns
- **Capability**: `can_analyze_risk`

**7. `technical_analysis.json`** - Price pattern analysis
- **Inputs**: Price history, volume, indicators (RSI, MACD, etc.)
- **Output**: Support/resistance, trend direction, entry/exit signals
- **Backtest**: Predicted trend vs actual price action
- **Capability**: `can_analyze_technical_patterns`

**8. `sentiment_analysis.json`** - Market sentiment gauge
- **Inputs**: News, analyst ratings, social media signals
- **Output**: Sentiment score (bullish/bearish), momentum signals
- **Backtest**: Sentiment signal vs subsequent returns
- **Capability**: `can_analyze_sentiment`

---

## 🔧 Workflow Patterns for Backtesting

**`morning_briefing.json`**:
- Aggregates: Market movers, economic events, top opportunities
- **Backtest use**: Track recommended opportunities → measure performance

**`opportunity_scan.json`**:
- Screens for: Undervalued stocks, earnings catalysts, technical breakouts
- **Backtest use**: Scan results → track subsequent price performance

**`portfolio_review.json`**:
- Analyzes: Risk, concentration, sector exposure, rebalancing needs
- **Backtest use**: Rebalancing recommendations → compare vs buy-and-hold

---

## 📈 Specific Backtesting Scenarios

### Scenario 1: DCF Prediction Accuracy

**Data needed**:
1. Historical financials (FMP API: `get_financials()`, past 5 years)
2. Historical stock prices (FMP API: `get_historical()`)
3. DCF assumptions (stored in knowledge graph from past analyses)

**Process**:
```
For each quarter from 2020-2025:
  1. Run DCF valuation using data available at that time
  2. Store intrinsic value estimate in graph
  3. Compare vs actual stock price 3/6/12 months later
  4. Calculate prediction error %
  5. Aggregate: Mean error, RMSE, directional accuracy
```

**Existing capabilities**:
- Pattern: `dcf_valuation.json`
- API: `get_financials()`, `get_historical()`
- Storage: Knowledge graph tracks historical DCF analyses (node type: `dcf_analysis_`)

---

### Scenario 2: Buffett Checklist Strategy Backtest

**Data needed**:
1. Historical fundamentals for S&P 500 (FMP API: `get_key_metrics()`)
2. Historical prices (FMP API: `get_historical()`)
3. Buffett criteria thresholds (`buffett_checklist.json`)

**Process**:
```
For each year from 2015-2025:
  1. Screen all S&P 500 stocks using Buffett Checklist
  2. Select stocks passing ≥12/15 criteria
  3. Simulate equal-weight portfolio
  4. Track returns over next 1/3/5 years
  5. Compare vs S&P 500 benchmark
```

**Existing capabilities**:
- Pattern: `buffett_checklist.json`
- Dataset: `buffett_checklist.json`, `sp500_companies.json`
- API: `get_key_metrics()`, `get_historical()`

---

### Scenario 3: Economic Regime Prediction

**Data needed**:
1. Historical economic indicators (FRED API: GDP, CPI, UNRATE, FEDFUNDS)
2. Actual economic regimes (`economic_cycles.json`)
3. Asset class performance by regime (`dalio_framework.json`)

**Process**:
```
For each quarter from 2010-2025:
  1. Use Dalio framework to predict regime
  2. Compare predicted vs actual regime (from economic_cycles.json)
  3. Recommend asset allocation based on predicted regime
  4. Track returns vs benchmark allocation
  5. Calculate regime prediction accuracy %
```

**Existing capabilities**:
- Pattern: `dalio_cycle.json`
- Dataset: `economic_cycles.json`, `dalio_framework.json`
- API: FRED economic indicators (via `data_harvester.py`)

---

### Scenario 4: Earnings Surprise Prediction

**Data needed**:
1. Historical analyst estimates (FMP API: `get_analyst_estimates()`)
2. Actual reported earnings (FMP API: `get_financials()`)
3. Earnings surprise patterns (`earnings_surprises.json`)

**Process**:
```
For each earnings season (quarterly):
  1. Get analyst consensus EPS estimate
  2. Apply earnings surprise model (historical beat rate, surprise %)
  3. Predict: Beat/meet/miss + magnitude
  4. Compare vs actual reported EPS
  5. Track prediction accuracy over time
```

**Existing capabilities**:
- Pattern: `earnings_analysis.json`
- Dataset: `earnings_surprises.json`
- API: `get_analyst_estimates()`, `get_financials()`

---

### Scenario 5: Sector Rotation Strategy

**Data needed**:
1. Economic regime (Dalio framework)
2. Sector performance history (`sector_performance.json`)
3. Sector correlations (`sector_correlations.json`)
4. Historical sector returns (FMP API or calculated)

**Process**:
```
For each month from 2018-2025:
  1. Determine current economic regime
  2. Identify favored sectors for that regime
  3. Allocate portfolio accordingly (overweight/underweight)
  4. Track sector returns for next 1/3/6 months
  5. Compare vs equal-weight sector allocation
```

**Existing capabilities**:
- Pattern: `sector_rotation.json`, `market_regime.json`
- Dataset: `sector_performance.json`, `sector_correlations.json`, `dalio_framework.json`
- API: `get_historical()` for sector ETFs

---

### Scenario 6: Insider Trading Signal

**Data needed**:
1. Historical insider transactions (FMP API: `get_insider_trading()`)
2. Stock price history (FMP API: `get_historical()`)
3. Insider activity benchmarks (`insider_institutional_activity.json`)

**Process**:
```
For each month from 2019-2025:
  1. Identify stocks with high insider buying (e.g., >5 buys in 3 months)
  2. Flag as bullish signal
  3. Track stock price performance 1/3/6 months forward
  4. Calculate: Average return, win rate, risk-adjusted return
  5. Compare vs stocks with high insider selling
```

**Existing capabilities**:
- Dataset: `insider_institutional_activity.json`
- API: `get_insider_trading()`, `get_institutional_holders()`

---

## 🚀 Implementation Recommendations

### Phase 1: Infrastructure (Week 1-2)

**Create Backtesting Engine**:
```python
# dawsos/capabilities/backtesting.py

class BacktestEngine:
    def __init__(self, start_date, end_date, strategy):
        self.start_date = start_date
        self.end_date = end_date
        self.strategy = strategy  # Pattern to backtest
        self.market_data = MarketDataCapability()
        self.graph = KnowledgeGraph()

    def run_backtest(self):
        """
        1. Iterate through time periods
        2. Execute strategy at each point
        3. Store predictions in graph
        4. Compare vs actuals
        5. Calculate metrics
        """
        pass

    def generate_report(self):
        """
        - Total return
        - Sharpe ratio
        - Max drawdown
        - Win rate
        - Prediction accuracy
        """
        pass
```

**Pattern**:
```json
// dawsos/patterns/analysis/backtest_strategy.json
{
  "id": "backtest_strategy",
  "name": "Backtest Investment Strategy",
  "triggers": ["backtest", "test strategy", "historical performance"],
  "steps": [
    {
      "action": "execute_through_registry",
      "params": {
        "capability": "can_run_backtest",
        "context": {
          "strategy": "{STRATEGY}",
          "start_date": "{START_DATE}",
          "end_date": "{END_DATE}",
          "universe": "{UNIVERSE}"
        }
      }
    }
  ]
}
```

### Phase 2: Strategy Backtests (Week 3-4)

**Priority Order**:
1. **DCF Valuation Accuracy** - Easiest, clear metrics
2. **Buffett Checklist Strategy** - High-conviction, established criteria
3. **Economic Regime Prediction** - Macro-level, clear regimes
4. **Earnings Surprise** - Quarterly cadence, clear success metric
5. **Sector Rotation** - Monthly rebalancing, benchmark comparison

### Phase 3: UI Integration (Week 5-6)

**Add to Graph Intelligence Module**:
```python
# dawsos/ui/graph_intelligence/backtest_results.py

def render_backtest_results(graph, runtime):
    """
    Display:
    - Strategy performance chart
    - vs benchmark comparison
    - Prediction accuracy metrics
    - Trade log / decision history
    - Parameter sensitivity analysis
    """
```

**Add sub-tab to Knowledge Graph page**:
- "📊 Backtests" tab
- Shows: Historical strategy performance
- Filters: Strategy type, time period, universe
- Drill-down: Individual trades/predictions

---

## 📋 Data Availability Matrix

| Data Type | Source | Lookback | Update Freq | Cost |
|-----------|--------|----------|-------------|------|
| Stock Prices | FMP API | 5+ years | Real-time | Included |
| Fundamentals | FMP API | 5+ years | Daily | Included |
| Analyst Estimates | FMP API | 2+ years | Daily | Included |
| Economic Data | FRED API | 50+ years | Daily/Monthly | Free |
| Insider Trading | FMP API | 3+ years | Daily | Included |
| Earnings Surprises | Knowledge Dataset | 3+ years | Quarterly | Static |
| Sector Performance | Knowledge Dataset | 5+ years | Monthly | Static |
| Economic Cycles | Knowledge Dataset | 30+ years | Ad-hoc | Static |

**Summary**: All necessary data available with zero additional cost

---

## 💡 Key Insights

### Strengths:
1. **Comprehensive data coverage** - Prices, fundamentals, macro, alternative data
2. **Multiple prediction types** - Valuation, regime, earnings, sentiment
3. **Existing frameworks** - Buffett, Dalio strategies already codified
4. **Knowledge Graph** - Can store historical predictions and track accuracy over time
5. **Pattern System** - Easy to create new backtesting workflows

### Gaps:
1. **Backtesting engine** - Need to build infrastructure
2. **Performance attribution** - Need metrics calculation framework
3. **Historical storage** - Graph tracks analyses, but need systematic historical prediction storage
4. **Benchmark comparison** - Need to fetch/store benchmark returns (SPY, sector ETFs)
5. **Transaction costs** - Backtests should account for slippage, commissions

### Quick Wins:
1. **DCF Accuracy** - Simplest, can extract historical DCF analyses from graph
2. **Earnings Beat Rate** - Clear binary outcome, quarterly data points
3. **Regime Prediction** - Already have labeled historical regimes in `economic_cycles.json`

---

## 🎓 Example Queries for Backtesting

**User**: *"Backtest the Buffett Checklist strategy from 2015 to 2025"*

**System**:
1. Pattern: `backtest_strategy.json` triggered
2. Load: `buffett_checklist.json` criteria
3. API: Fetch historical fundamentals for S&P 500 (2015-2025)
4. Process: Score stocks each year, create portfolio
5. API: Fetch historical prices for selected stocks
6. Calculate: Returns, Sharpe, max drawdown
7. Compare: vs S&P 500 benchmark
8. Store: Results in graph (node: `backtest_buffett_2015_2025`)
9. Display: Performance chart, metrics, top picks

**User**: *"How accurate have our DCF valuations been?"*

**System**:
1. Query graph: Find all `dcf_analysis_*` nodes with intrinsic value
2. Group by symbol and date
3. API: Fetch actual prices at DCF date + 6M/12M later
4. Calculate: Prediction error % (intrinsic value vs actual price)
5. Aggregate: Mean error, RMSE, % within 20% band
6. Display: Accuracy metrics, biggest misses, best calls

**User**: *"Test the Dalio framework's regime predictions"*

**System**:
1. Load: `economic_cycles.json` (actual historical regimes)
2. Load: `dalio_framework.json` (regime identification logic)
3. API: Fetch historical FRED data (GDP, CPI, unemployment, etc.)
4. Process: Apply framework to predict regime each quarter
5. Compare: Predicted regime vs actual regime from economic_cycles
6. Calculate: Accuracy %, precision/recall by regime type
7. Display: Confusion matrix, regime timeline with predictions

---

## 🔗 Next Steps

1. **Review and prioritize** - Which backtests provide most value?
2. **Build infrastructure** - Create `BacktestEngine` capability
3. **Start simple** - DCF accuracy analysis first (data already in graph)
4. **Iterate** - Add more complex strategies (Buffett, Dalio)
5. **UI integration** - Add backtesting tab to Graph Intelligence module
6. **Continuous improvement** - Use backtest results to refine strategies

**Estimated Effort**: 4-6 weeks to production-ready backtesting system

---

**Questions?** See [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) for available capabilities or [FMP_API_CAPABILITIES_GUIDE.md](FMP_API_CAPABILITIES_GUIDE.md) for API details.
