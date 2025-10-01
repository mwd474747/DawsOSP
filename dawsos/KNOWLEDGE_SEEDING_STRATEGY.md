# DawsOS Knowledge Seeding Strategy
## Top-Down Investment Framework (Buffett + Ackman + Dalio)

### Core Philosophy: Start Wide, Go Deep Only When Needed

The knowledge graph should mirror how legendary investors actually think:
1. **Dalio**: Understand the economic machine first
2. **Buffett**: Find quality businesses within favorable conditions
3. **Ackman**: Identify asymmetric opportunities through deep analysis

---

## Level 1: THE ECONOMIC MACHINE (Dalio's Foundation)
*Start here - these are the master nodes that influence everything*

### Primary Regime Nodes
```
ECONOMIC_REGIME (Master Node)
├── GROWTH_CYCLE
│   ├── Expansion
│   ├── Peak
│   ├── Contraction
│   └── Trough
├── INFLATION_REGIME
│   ├── Deflation (<0%)
│   ├── Low (0-2%)
│   ├── Moderate (2-4%)
│   └── High (>4%)
└── LIQUIDITY_CONDITIONS
    ├── Tightening
    ├── Neutral
    └── Easing
```

### Key Relationships to Seed
- GROWTH_CYCLE → influences(0.9) → CORPORATE_EARNINGS
- INFLATION_REGIME → pressures(0.8) → VALUATIONS
- LIQUIDITY_CONDITIONS → drives(0.85) → RISK_APPETITE
- FED_RATE → determines(0.9) → LIQUIDITY_CONDITIONS

**Why Start Here**: These 3 dimensions explain 80% of market movements. Every Dalio decision starts with "Where are we in the cycle?"

---

## Level 2: RISK ON/OFF FRAMEWORK (Dalio's All-Weather)

### Asset Class Behavior Nodes
```
RISK_SENTIMENT (Secondary Master)
├── RISK_ON
│   ├── Stocks_Outperform
│   ├── Credit_Spreads_Tight
│   └── Commodity_Rally
└── RISK_OFF
    ├── Bonds_Outperform
    ├── Dollar_Strength
    └── Gold_Haven
```

### Critical Correlations to Seed
- RISK_ON → favors(0.8) → [TECH, CONSUMER_DISC, FINANCIALS]
- RISK_OFF → favors(0.8) → [UTILITIES, STAPLES, HEALTHCARE]
- VIX > 30 → triggers(0.9) → RISK_OFF
- CREDIT_SPREADS → inversely_correlates(-0.7) → STOCK_VALUATIONS

---

## Level 3: SECTOR ROTATION (Buffett's Circle of Competence)

### Business Quality Nodes
```
MARKET_SECTORS
├── DEFENSIVE_QUALITY
│   ├── Consumer_Staples (KO, PG)
│   ├── Healthcare (JNJ, UNH)
│   └── Utilities (NEE, NEP)
├── CYCLICAL_GROWTH
│   ├── Technology (AAPL, MSFT)
│   ├── Consumer_Disc (AMZN, TSLA)
│   └── Financials (BRK, JPM)
└── INFLATION_BENEFICIARIES
    ├── Energy (XOM, CVX)
    ├── Materials (FCX, NEM)
    └── Real_Estate (SPG, PLD)
```

### Buffett's Quality Filters
- MOAT_STRENGTH → enhances(0.9) → VALUATION_PREMIUM
- ROE > 15% → indicates(0.8) → QUALITY_BUSINESS
- DEBT/EQUITY < 0.5 → suggests(0.7) → FINANCIAL_STRENGTH
- FCF_YIELD > 5% → signals(0.8) → VALUE_OPPORTUNITY

---

## Level 4: COMPANY FUNDAMENTALS (Ackman's Activist Layer)

### Deep Analysis Nodes (Only When Triggered)
```
COMPANY_ANALYSIS
├── CATALYST_POTENTIAL
│   ├── Management_Change
│   ├── Restructuring
│   └── Spin_offs
├── HIDDEN_VALUE
│   ├── Real_Estate_Assets
│   ├── Brand_Value
│   └── Patent_Portfolio
└── ASYMMETRIC_BETS
    ├── Turnaround_Situations
    ├── Merger_Arbitrage
    └── Activism_Targets
```

### Ackman's Trigger Conditions
- P/B < 1 AND ROE > 10% → investigate(0.9) → HIDDEN_VALUE
- ACTIVIST_FILING → analyze(0.95) → CATALYST_POTENTIAL
- MARGIN_COMPRESSION + MARKET_LEADER → consider(0.8) → TURNAROUND

---

## Seeding Sequence (Order Matters!)

### Phase 1: Master Framework (Week 1)
1. Create ECONOMIC_REGIME with current state
2. Add all FRED indicators linked to regime
3. Create RISK_SENTIMENT from VIX, spreads, dollar
4. Link everything with strong (>0.7) relationships

### Phase 2: Sector Intelligence (Week 2)
1. Add 11 GICS sectors as nodes
2. Create rotation patterns (Early → Mid → Late cycle)
3. Add Buffett quality metrics to each sector
4. Link sectors to regime conditions

### Phase 3: Stock Universe (Week 3)
1. Add S&P 100 stocks (start with quality)
2. Group by sector, link to parents
3. Add fundamental metrics (P/E, ROE, Debt)
4. Create relative strength relationships

### Phase 4: Opportunistic Depth (Week 4+)
1. Only drill deeper on triggered conditions
2. Add company-specific catalysts when detected
3. Build activist/event-driven patterns
4. Create asymmetric risk/reward profiles

---

## Key Principles for Seeding

### 1. Dalio's Principles
- **Cause-Effect**: Every node must have clear causal relationships
- **Timeframes**: Tag relationships with lag times (immediate, 3M, 6M, 12M)
- **Probability**: Weight relationships by historical reliability

### 2. Buffett's Principles
- **Quality First**: Seed quality companies before speculative ones
- **Margin of Safety**: Add valuation context to every stock node
- **Long-term**: Emphasize sustainable competitive advantages

### 3. Ackman's Principles
- **Catalysts**: Flag potential change events
- **Concentration**: Deep knowledge on few vs shallow on many
- **Asymmetry**: Calculate risk/reward for each opportunity

---

## Workflow Patterns to Train

### Essential Workflows for Learning
1. **"What's the regime?"** → Check growth, inflation, liquidity → Determine allocation
2. **"Find value"** → Screen P/E < 15, ROE > 15% → Rank by quality
3. **"Sector rotation"** → Identify regime → Find outperforming sectors
4. **"Risk check"** → Monitor VIX, spreads, sentiment → Adjust exposure
5. **"Catalyst scan"** → Check 13Fs, activism, events → Deep dive triggers

---

## Success Metrics

### Graph Health Indicators
- **Breadth**: All major indices and sectors covered
- **Depth**: 3-5 levels only where needed
- **Connections**: Average 5-10 edges per node
- **Patterns**: 20+ recurring patterns identified
- **Predictions**: 60%+ directional accuracy

### Investment Outcomes
- Regime identification: 80% accuracy
- Sector rotation: Outperform by 200bps
- Stock selection: 65% win rate
- Risk management: Max drawdown < 15%

---

## Implementation Without Code Changes

Using existing DawsOS capabilities:
1. Use natural language to add nodes: "Add economic regime as master node"
2. Create relationships: "Connect GDP growth to corporate earnings with 0.9 strength"
3. Build patterns: "When VIX > 30, mark risk-off regime"
4. Set triggers: "If P/B < 1 and ROE > 10%, flag for deep analysis"

The system learns these patterns through repetition and workflow recording.