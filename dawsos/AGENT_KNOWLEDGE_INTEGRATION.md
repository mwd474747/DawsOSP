# Agent Knowledge Integration Strategy
## How Investment Framework Maps to Existing Agents

### Core Insight: Agents Already Have Everything They Need
The seeded knowledge graph becomes the "shared brain" that all agents reference. Each agent's role naturally aligns with investment tasks.

---

## 1. CLAUDE - Investment Analyst Interface
**Current Role**: Natural language understanding
**Investment Enhancement**: Interprets queries through regime lens

### Knowledge Integration:
```python
# Claude now understands investment context
"What's the market outlook?" →
  - Check ECONOMIC_REGIME node
  - Identify current state (GOLDILOCKS/OVERHEATING/etc)
  - Return regime-appropriate response

"Find value stocks" →
  - Query nodes where PE < 20
  - Check sector alignment with regime
  - Return Buffett-style opportunities
```

### Prompt Enhancement (via prompts/claude.txt):
```
When analyzing market queries:
1. First check ECONOMIC_REGIME node for context
2. Consider regime when suggesting sectors/stocks
3. Apply Buffett filters (PE<20, ROE>15) for value
4. Flag Ackman opportunities (activism, catalysts)
```

---

## 2. GRAPH_MIND - Investment Strategy Orchestrator
**Current Role**: Graph intelligence coordinator
**Investment Enhancement**: Regime-aware decision routing

### Knowledge Integration:
```python
# GraphMind routes based on regime
If query about "allocation":
  - Check ECONOMIC_REGIME.current_state
  - If GOLDILOCKS → favor TECHNOLOGY, FINANCIALS
  - If RISK_OFF → favor CONSUMER_STAPLES, UTILITIES
  - Weight edges accordingly
```

### Decision Trees:
```
REGIME = GOLDILOCKS:
  → Activate growth-seeking agents
  → Increase risk tolerance parameters
  → Focus on momentum patterns

REGIME = RISK_OFF:
  → Activate defensive agents
  → Decrease risk parameters
  → Focus on quality/value
```

---

## 3. DATA_HARVESTER - Market Intelligence Collector
**Current Role**: Fetches data from APIs
**Investment Enhancement**: Regime-triggered data collection

### Knowledge Integration:
```python
# Harvester adapts to regime needs
If REGIME = OVERHEATING:
  - Increase frequency of inflation data (CPI, PPI)
  - Monitor Fed speeches
  - Track bond yields closely

If REGIME = RECESSION_RISK:
  - Focus on unemployment claims
  - Monitor credit spreads
  - Track defensive sector performance
```

### Smart Collection Patterns:
- **Goldilocks**: Balance growth and value metrics
- **Risk-Off**: Prioritize safety indicators (VIX, Dollar, Gold)
- **Transition**: Increase all data collection for regime change signals

---

## 4. RELATIONSHIP_HUNTER - Correlation Discovery
**Current Role**: Finds connections between entities
**Investment Enhancement**: Regime-specific relationship strength

### Knowledge Integration:
```python
# Hunter adjusts correlations by regime
In GOLDILOCKS:
  GDP → TECH_STOCKS: strength = 0.8
  RATES → BANKS: strength = 0.7

In RISK_OFF:
  VIX → STOCKS: strength = -0.9
  DOLLAR → GOLD: strength = -0.7
```

### Dalio's "Economic Machine" Patterns:
- Debt Cycle → Interest Rates → Asset Prices
- Productivity → Earnings → Stock Prices
- Money Supply → Inflation → Bond Yields

---

## 5. PATTERN_SPOTTER - Market Regime Detector
**Current Role**: Identifies patterns in graph
**Investment Enhancement**: Regime change detection

### Knowledge Integration:
```python
# Spotter watches for regime transitions
Pattern: "REGIME_SHIFT"
  If GDP_GROWTH < 0 for 2 quarters AND
  If UNEMPLOYMENT > 5% AND
  If FED_RATE decreasing
  Then: Signal "ENTERING_RECESSION"
```

### Critical Patterns to Monitor:
1. **Goldilocks → Overheating**: CPI acceleration + GDP strong
2. **Overheating → Slowdown**: Fed hikes + PMI declining
3. **Slowdown → Recession**: Yield curve inverts + Earnings decline
4. **Recession → Recovery**: Fed cuts + Credit spreads tighten

---

## 6. FORECAST_DREAMER - Portfolio Optimizer
**Current Role**: Makes predictions based on graph
**Investment Enhancement**: Regime-based allocation

### Knowledge Integration:
```python
# Dreamer optimizes for regime
Forecast for "PORTFOLIO":
  1. Get ECONOMIC_REGIME
  2. Apply Dalio's All-Weather weights:
     - GOLDILOCKS: 30% stocks, 40% bonds, 15% commodities, 15% gold
     - RISK_OFF: 20% stocks, 50% bonds, 15% commodities, 15% gold
  3. Adjust for Buffett value opportunities
  4. Consider Ackman catalyst events
```

### Risk Parity Implementation:
- Balance risk contribution across asset classes
- Adjust leverage based on regime volatility
- Rebalance when correlations break

---

## 7. WORKFLOW_RECORDER/PLAYER - Investment Process Automation
**Current Role**: Records and replays successful workflows
**Investment Enhancement**: Builds investment playbooks

### Knowledge Integration:
```python
# Recorder learns investment processes
Workflow: "MONTHLY_REBALANCE"
  1. Check ECONOMIC_REGIME
  2. Run sector rotation analysis
  3. Identify value opportunities
  4. Calculate position sizes
  5. Generate trade list

Save and replay monthly
```

### Key Workflows to Record:
1. **Morning Routine**: Check regime → Review positions → Scan opportunities
2. **Fed Day**: Parse statement → Update regime → Adjust allocations
3. **Earnings Season**: Screen results → Update valuations → Rerank stocks
4. **Risk Check**: Calculate exposures → Check correlations → Hedge if needed

---

## 8. CODE_MONKEY - Strategy Builder
**Current Role**: Writes new code/agents
**Investment Enhancement**: Creates custom strategies

### Knowledge Integration:
```python
# Monkey writes investment strategies
Request: "Create momentum strategy"
CodeMonkey generates:

class MomentumAgent(BaseAgent):
    def score_stocks(self):
        # Get all stocks from graph
        # Calculate 3-month returns
        # Rank by momentum
        # Filter by regime favorability
        # Return top 10
```

### Strategy Templates:
- Value strategies (Buffett-style)
- Momentum strategies (trend-following)
- Arbitrage strategies (Ackman-style)
- Macro strategies (Dalio-style)

---

## Implementation Without Code Changes

### Step 1: Enhance Agent Prompts
Create prompts/investment_context.txt:
```
All agents should consider:
- Current ECONOMIC_REGIME before making decisions
- Sector rotation based on regime
- Value opportunities (P/E < 20)
- Risk management (position sizing, correlations)
```

### Step 2: Train Through Usage
Run these queries repeatedly to train the system:
1. "What's the current regime and what does it mean?"
2. "Show me the best sectors for this regime"
3. "Find value stocks in favored sectors"
4. "Calculate portfolio allocation for current regime"
5. "Alert me to regime change signals"

### Step 3: Record Investment Workflows
Build reusable workflows:
```python
# Morning ritual
runtime.orchestrate("Check regime, scan value opportunities, review risks")

# Rebalancing
runtime.orchestrate("Calculate optimal allocation for current regime")

# Opportunity scanning
runtime.orchestrate("Find stocks with P/E<15 and ROE>20 in favored sectors")
```

---

## Natural Language Commands That Activate Framework

### Regime Analysis (PatternSpotter + Claude)
- "What regime are we in?"
- "Is the regime changing?"
- "Show regime transition signals"

### Sector Rotation (GraphMind + RelationshipHunter)
- "Which sectors for goldilocks?"
- "Rotate from tech to defensives"
- "Show sector momentum"

### Value Investing (DataHarvester + ForecastDreamer)
- "Find Buffett stocks"
- "Screen for value in healthcare"
- "Show quality at reasonable price"

### Risk Management (PatternSpotter + GraphMind)
- "Calculate portfolio risk"
- "Show correlation matrix"
- "Suggest hedges for regime change"

### Catalyst Hunting (RelationshipHunter + Claude)
- "Find activist targets"
- "Show upcoming catalysts"
- "Screen for turnarounds"

---

## Measuring Integration Success

### Knowledge Utilization Metrics
1. **Regime Recognition**: Agents reference ECONOMIC_REGIME in 80%+ decisions
2. **Sector Alignment**: Recommendations match regime preferences
3. **Value Discipline**: Agents apply Buffett filters consistently
4. **Risk Awareness**: Positions sized according to regime volatility

### Investment Performance Metrics
1. **Hit Rate**: 60%+ recommendations profitable
2. **Risk-Adjusted Returns**: Sharpe > 1.0
3. **Regime Timing**: Catch 70%+ of regime transitions
4. **Drawdown Control**: Max loss < 15%

---

## The Magic: Emergent Investment Intelligence

With this knowledge integration, the agents create emergent behaviors:

1. **Regime-Aware Allocation**: System automatically adjusts risk based on conditions
2. **Value Discovery**: Agents collaborate to find mispriced assets
3. **Risk Cascades**: One agent's risk signal triggers protective actions across system
4. **Learning Loops**: Successful strategies get recorded and improved

All without changing a single line of agent code - just by having them reference the seeded knowledge graph!