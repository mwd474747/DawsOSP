# DawsOS Visual Flow Diagrams

## 🎯 Overview
This document provides visual representations of key user journeys through the DawsOS platform using ASCII art diagrams.

---

## 1. Master Application Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DawsOS Platform                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐      ┌────────────────────────────────────────┐         │
│  │  LOGIN   │ ───→ │            MAIN DASHBOARD               │         │
│  └──────────┘      └────────────────────────────────────────┘         │
│       │                               │                                │
│       ▼                               ▼                                │
│  ┌──────────┐      ┌────────────────────────────────────────┐         │
│  │   JWT    │      │         8 NAVIGATION TABS              │         │
│  │  Token   │      ├────────────────────────────────────────┤         │
│  └──────────┘      │ Overview │ Holdings │ Transactions │   │         │
│                    │ Scenarios │ Alerts │ AI Analysis │     │         │
│                    │ Optimize │ Macro Dashboard │           │         │
│                    └────────────────────────────────────────┘         │
│                                      │                                 │
│                    ┌─────────────────┴─────────────────┐              │
│                    ▼                 ▼                 ▼              │
│           ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│           │   ANALYSIS   │  │   MONITORING │  │   ACTIONS    │       │
│           │              │  │              │  │              │       │
│           │ • Scenarios  │  │ • Alerts     │  │ • Optimize   │       │
│           │ • AI Query   │  │ • Metrics    │  │ • Export     │       │
│           │ • Macro View │  │ • Holdings   │  │ • Trade      │       │
│           └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Authentication & Authorization Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     Authentication Flow                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Entry                   Server Processing                 │
│   ─────────                    ──────────────                  │
│                                                                  │
│   ┌──────┐     ┌──────┐       ┌──────────┐     ┌──────────┐   │
│   │Email │ ──→ │Pass  │ ────→ │Validate  │ ──→ │Generate  │   │
│   └──────┘     └──────┘       │Bcrypt    │     │JWT Token │   │
│                                └──────────┘     └──────────┘   │
│                                     │                 │         │
│                                     ▼                 ▼         │
│                              ┌──────────┐      ┌──────────┐    │
│                              │ Check DB │      │Set Cookie│    │
│                              │  User    │      │& Header  │    │
│                              └──────────┘      └──────────┘    │
│                                     │                 │         │
│                                     ▼                 ▼         │
│                              ┌─────────────────────────┐       │
│                              │    Role Assignment      │       │
│                              ├─────────────────────────┤       │
│                              │ • ADMIN  - Full Access  │       │
│                              │ • MANAGER - Portfolio   │       │
│                              │ • USER   - Standard     │       │
│                              │ • VIEWER - Read Only    │       │
│                              └─────────────────────────┘       │
│                                          │                      │
│                                          ▼                      │
│                              ┌─────────────────────────┐       │
│                              │   Protected Routes      │       │
│                              └─────────────────────────┘       │
│                                                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Portfolio Analysis Workflow

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Portfolio Analysis Flow                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────┐                                                       │
│  │  Overview  │                                                       │
│  │    Tab     │                                                       │
│  └─────┬──────┘                                                       │
│        │                                                               │
│        ▼                                                               │
│  ┌─────────────────────────────────────────┐                        │
│  │        Load Portfolio Metrics           │                        │
│  ├─────────────────────────────────────────┤                        │
│  │ • Total Value    • Sharpe Ratio         │                        │
│  │ • P&L           • Beta                  │                        │
│  │ • Returns       • VaR                   │                        │
│  └──────────┬──────────────────────────────┘                        │
│             │                                                         │
│   ┌─────────┴──────────┬────────────┬────────────┐                  │
│   ▼                    ▼            ▼            ▼                  │
│ ┌──────┐         ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│ │Check │         │ Scenario │ │   AI     │ │  Macro   │           │
│ │Risk? │         │ Analysis │ │ Analysis │ │Dashboard │           │
│ └──┬───┘         └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│    │                  │            │            │                   │
│    ▼                  ▼            ▼            ▼                   │
│ ┌──────────────────────────────────────────────────┐               │
│ │            Consolidated Analysis View            │               │
│ ├──────────────────────────────────────────────────┤               │
│ │                                                  │               │
│ │  Risk Level: [■■■■■■■□□□] 70%                  │               │
│ │                                                  │               │
│ │  Scenarios:                                     │               │
│ │  • Market Crash: -$240,000                      │               │
│ │  • Rate Hike: -$45,000                          │               │
│ │                                                  │               │
│ │  AI Insights:                                   │               │
│ │  "High tech concentration poses risk..."        │               │
│ │                                                  │               │
│ │  Macro Regime: LATE_EXPANSION                   │               │
│ │  Action: Consider defensive positioning         │               │
│ └──────────────────────────────────────────────────┘               │
│                          │                                          │
│                          ▼                                          │
│                ┌─────────────────┐                                 │
│                │ Decision Point  │                                 │
│                ├─────────────────┤                                 │
│                │ • Optimize      │                                 │
│                │ • Set Alerts    │                                 │
│                │ • Execute Trades│                                 │
│                └─────────────────┘                                 │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. Macro Dashboard Reasoning Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Macro Dashboard Data Flow                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐          │
│  │  FRED API  │      │ Indicators │      │  Database  │          │
│  └─────┬──────┘      └─────┬──────┘      └─────┬──────┘          │
│        │                    │                    │                 │
│        └────────────┬───────┴────────────────────┘                │
│                     ▼                                              │
│         ┌──────────────────────┐                                  │
│         │   24 Raw Indicators  │                                  │
│         ├──────────────────────┤                                  │
│         │ • GDP Growth         │                                  │
│         │ • Inflation          │                                  │
│         │ • Interest Rates     │                                  │
│         │ • Credit Growth      │                                  │
│         │ • Debt/GDP           │                                  │
│         │ • ... 19 more        │                                  │
│         └──────────┬───────────┘                                  │
│                    ▼                                               │
│         ┌──────────────────────┐                                  │
│         │  Statistical Process │                                  │
│         ├──────────────────────┤                                  │
│         │ • Z-Score Normalize  │                                  │
│         │ • Calculate Deltas   │                                  │
│         │ • Moving Averages    │                                  │
│         └──────────┬───────────┘                                  │
│                    ▼                                               │
│   ┌─────────────────────────────────────────────┐                │
│   │           4 Dalio Cycles Analysis          │                │
│   ├─────────────────────────────────────────────┤                │
│   │                                             │                │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐ ┌──────────┐    │
│   │  │   STDC   │  │   LTDC   │  │  Empire  │ │ Internal │    │
│   │  │  5-8yr   │  │ 75-100yr │  │  250yr   │ │  100yr   │    │
│   │  └────┬─────┘  └────┬─────┘  └────┬─────┘ └────┬─────┘    │
│   │       │              │              │            │          │
│   └───────┼──────────────┼──────────────┼────────────┼──────────┤
│           ▼              ▼              ▼            ▼          │
│   ┌────────────────────────────────────────────────────┐        │
│   │              Reasoning Chains                      │        │
│   ├────────────────────────────────────────────────────┤        │
│   │                                                    │        │
│   │  For Each Cycle:                                  │        │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐         │        │
│   │  │Raw Data │→ │  Math   │→ │  Logic  │→ Result │        │
│   │  └─────────┘  └─────────┘  └─────────┘         │        │
│   │                                                    │        │
│   │  Example STDC:                                    │        │
│   │  • Credit: 8.2% → Z-Score: +1.8σ                │        │
│   │  • Rates: 5.25% → Inverted curve                 │        │
│   │  • Logic: IF credit>7% AND inverted              │        │
│   │  • Result: LATE_EXPANSION (85% confidence)       │        │
│   │                                                    │        │
│   └────────────────────────────────────────────────────┘        │
│                           │                                      │
│                           ▼                                      │
│           ┌───────────────────────────────┐                     │
│           │   Combined Assessment         │                     │
│           ├───────────────────────────────┤                     │
│           │ • Current Regime: LATE_CYCLE  │                     │
│           │ • Risk Level: HIGH            │                     │
│           │ • Historical Match: 2007      │                     │
│           │ • Recommendation: DEFENSIVE   │                     │
│           └───────────────────────────────┘                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Scenario Analysis Flow

```
┌───────────────────────────────────────────────────────────────────┐
│                    Scenario Analysis Pipeline                     │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Current State              Scenario Selection                  │
│   ─────────────              ──────────────                     │
│                                                                   │
│  ┌──────────────┐           ┌─────────────────┐                │
│  │   Portfolio  │           │ Choose Scenario │                │
│  │   Holdings   │           ├─────────────────┤                │
│  │              │           │ • Market Crash  │                │
│  │ AAPL: 100    │           │ • Interest Rate │                │
│  │ GOOGL: 50    │           │ • Inflation     │                │
│  │ TSLA: 75     │           └────────┬────────┘                │
│  └──────┬───────┘                    │                          │
│         │                             ▼                          │
│         │                   ┌─────────────────┐                 │
│         │                   │  Shock Factors  │                 │
│         │                   ├─────────────────┤                 │
│         │                   │ Equity: -20%    │                 │
│         │                   │ Credit: +300bp  │                 │
│         │                   │ Vol: +50%       │                 │
│         │                   └────────┬────────┘                 │
│         │                             │                          │
│         └──────────┬──────────────────┘                          │
│                    ▼                                             │
│         ┌──────────────────────┐                                │
│         │   Factor Exposure    │                                │
│         │   Calculation        │                                │
│         ├──────────────────────┤                                │
│         │ AAPL:                │                                │
│         │ • Beta: 1.2          │                                │
│         │ • Duration: 0        │                                │
│         │ • Credit: Low        │                                │
│         └──────────┬───────────┘                                │
│                    ▼                                             │
│         ┌──────────────────────┐                                │
│         │  Apply Correlation   │                                │
│         │      Matrix          │                                │
│         ├──────────────────────┤                                │
│         │  [1.0  0.7  0.3]     │                                │
│         │  [0.7  1.0  0.5]     │                                │
│         │  [0.3  0.5  1.0]     │                                │
│         └──────────┬───────────┘                                │
│                    ▼                                             │
│         ┌──────────────────────┐                                │
│         │   Impact Results     │                                │
│         ├──────────────────────┤                                │
│         │ Total: -$240,000     │                                │
│         │ By Holding:          │                                │
│         │ • AAPL: -$42,000     │                                │
│         │ • GOOGL: -$26,000    │                                │
│         │ • TSLA: -$37,500     │                                │
│         └──────────┬───────────┘                                │
│                    ▼                                             │
│         ┌──────────────────────┐                                │
│         │  Recommendations     │                                │
│         ├──────────────────────┤                                │
│         │ • Add Put Options    │                                │
│         │ • Reduce Beta        │                                │
│         │ • Increase Cash      │                                │
│         └──────────────────────┘                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Alert System Flow

```
┌────────────────────────────────────────────────────────────────┐
│                      Alert System Flow                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│   Alert Creation                Alert Processing              │
│   ──────────────                ────────────────             │
│                                                                │
│  ┌─────────────┐              ┌─────────────────┐           │
│  │Create Alert │              │  Alert Engine   │           │
│  ├─────────────┤              │   (Every 5min)  │           │
│  │Type: Price  │              └────────┬────────┘           │
│  │Symbol: AAPL │                       │                     │
│  │Op: Below    │                       ▼                     │
│  │Value: $150  │              ┌─────────────────┐           │
│  └──────┬──────┘              │  Load Active    │           │
│         │                      │    Alerts       │           │
│         ▼                      └────────┬────────┘           │
│  ┌─────────────┐                       │                     │
│  │Save to DB   │                       ▼                     │
│  └─────────────┘              ┌─────────────────┐           │
│         │                      │Check Conditions │           │
│         │                      └────────┬────────┘           │
│         │                               │                     │
│         ▼                               ▼                     │
│  ┌──────────────────────────────────────────┐               │
│  │           Alert Monitoring Loop           │               │
│  ├──────────────────────────────────────────┤               │
│  │                                           │               │
│  │  ┌─────────┐     ┌─────────┐            │               │
│  │  │Get Price│ ──→ │Compare  │            │               │
│  │  │AAPL:$149│     │149 < 150│            │               │
│  │  └─────────┘     └────┬────┘            │               │
│  │                        │                  │               │
│  │                        ▼                  │               │
│  │              ┌──────────────┐            │               │
│  │              │   Triggered? │            │               │
│  │              └──────┬───────┘            │               │
│  │                     │                     │               │
│  │            Yes      │      No             │               │
│  │              ┌──────┴──────┐              │               │
│  │              ▼             ▼              │               │
│  │      ┌──────────┐   ┌──────────┐        │               │
│  │      │Check     │   │Continue  │        │               │
│  │      │Cooldown  │   │Monitor   │        │               │
│  │      └────┬─────┘   └──────────┘        │               │
│  │           │                               │               │
│  │           ▼                               │               │
│  │   ┌──────────────┐                       │               │
│  │   │Send          │                       │               │
│  │   │Notification  │                       │               │
│  │   ├──────────────┤                       │               │
│  │   │• Email       │                       │               │
│  │   │• SMS         │                       │               │
│  │   │• Dashboard   │                       │               │
│  │   └──────────────┘                       │               │
│  │                                           │               │
│  └──────────────────────────────────────────┘               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 7. AI Analysis Request Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    AI Analysis Pipeline                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   User Query                  Context Assembly              │
│   ──────────                  ────────────────             │
│                                                              │
│  ┌──────────────┐            ┌──────────────┐              │
│  │Natural Lang  │            │Gather Context│              │
│  │Query:        │            ├──────────────┤              │
│  │"What's my    │            │• Portfolio   │              │
│  │biggest risk?"│            │• Metrics     │              │
│  └──────┬───────┘            │• Regime      │              │
│          │                    │• History     │              │
│          │                    └──────┬───────┘              │
│          │                           │                       │
│          └────────┬──────────────────┘                       │
│                   ▼                                          │
│        ┌──────────────────────┐                            │
│        │  Prompt Engineering  │                            │
│        ├──────────────────────┤                            │
│        │Query: {user_input}   │                            │
│        │Portfolio: {data}     │                            │
│        │Regime: LATE_CYCLE    │                            │
│        │Instructions: ...     │                            │
│        └──────────┬───────────┘                            │
│                   ▼                                          │
│        ┌──────────────────────┐                            │
│        │   Claude API Call    │                            │
│        ├──────────────────────┤                            │
│        │ Model: Claude-3      │                            │
│        │ Tokens: 2000         │                            │
│        │ Temperature: 0.7     │                            │
│        └──────────┬───────────┘                            │
│                   ▼                                          │
│        ┌──────────────────────┐                            │
│        │   Parse Response     │                            │
│        └──────────┬───────────┘                            │
│                   ▼                                          │
│   ┌───────────────────────────────────────┐                │
│   │         Formatted Output              │                │
│   ├───────────────────────────────────────┤                │
│   │                                       │                │
│   │ **Risk Analysis:**                   │                │
│   │                                       │                │
│   │ Your biggest risks are:              │                │
│   │ 1. Tech concentration (72%)          │                │
│   │ 2. No defensive assets               │                │
│   │ 3. High beta in late cycle           │                │
│   │                                       │                │
│   │ **Recommendations:**                 │                │
│   │ • Reduce AAPL to 15%                 │                │
│   │ • Add 20% bonds                      │                │
│   │ • Consider gold hedge                │                │
│   │                                       │                │
│   └───────────────────────────────────────┘                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Optimization Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                  Portfolio Optimization Flow                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Risk Setting              Optimization Engine            │
│   ────────────              ──────────────────            │
│                                                             │
│  ┌──────────────┐          ┌──────────────────┐          │
│  │Risk Tolerance│          │Current Portfolio │          │
│  │   Slider     │          ├──────────────────┤          │
│  │              │          │Stocks: 70%      │          │
│  │ 0 ●────────1 │          │Bonds: 20%       │          │
│  │   0.5        │          │Cash: 10%        │          │
│  └──────┬───────┘          └────────┬─────────┘          │
│         │                            │                     │
│         └─────────┬──────────────────┘                     │
│                   ▼                                        │
│        ┌──────────────────────┐                          │
│        │Historical Returns    │                          │
│        │& Covariance Matrix   │                          │
│        └──────────┬───────────┘                          │
│                   ▼                                        │
│        ┌──────────────────────┐                          │
│        │Mean-Variance         │                          │
│        │Optimization          │                          │
│        ├──────────────────────┤                          │
│        │minimize: σ²          │                          │
│        │maximize: μ           │                          │
│        │subject to: Σw = 1    │                          │
│        └──────────┬───────────┘                          │
│                   ▼                                        │
│        ┌──────────────────────┐                          │
│        │Efficient Frontier    │                          │
│        │Calculation           │                          │
│        └──────────┬───────────┘                          │
│                   ▼                                        │
│   ┌────────────────────────────────────────┐             │
│   │         Optimization Results           │             │
│   ├────────────────────────────────────────┤             │
│   │                                        │             │
│   │  Current vs Optimal                   │             │
│   │  ───────────────────                  │             │
│   │                                        │             │
│   │         Current    Optimal   Change   │             │
│   │  AAPL     25%       18%      -7%     │             │
│   │  GOOGL    20%       15%      -5%     │             │
│   │  Bonds    20%       35%     +15%     │             │
│   │  Gold      0%        5%      +5%     │             │
│   │                                        │             │
│   │  Expected Return: 8.5% → 7.8%        │             │
│   │  Volatility: 16% → 11%               │             │
│   │  Sharpe: 0.53 → 0.71                 │             │
│   │                                        │             │
│   │  Transaction Cost: $340               │             │
│   │                                        │             │
│   └────────────────────────────────────────┘             │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 9. Export/Report Generation Flow

```
┌──────────────────────────────────────────────────────────┐
│                 Export Generation Pipeline                │
├──────────────────────────────────────────────────────────┤
│                                                           │
│   Export Request           Data Collection               │
│   ──────────────           ───────────────              │
│                                                           │
│  ┌─────────────┐          ┌─────────────────┐          │
│  │Export Button│          │Gather All Data  │          │
│  │   Clicked   │          ├─────────────────┤          │
│  └──────┬──────┘          │• Portfolio      │          │
│         │                  │• Holdings       │          │
│         ▼                  │• Transactions   │          │
│  ┌─────────────┐          │• Metrics        │          │
│  │Choose Format│          │• Analysis       │          │
│  │• PDF        │          └────────┬────────┘          │
│  │• CSV        │                   │                    │
│  └──────┬──────┘                   │                    │
│         │                           ▼                    │
│         └──────────┬────────────────┘                    │
│                    ▼                                     │
│                                                          │
│        PDF Path                CSV Path                 │
│        ─────────                ────────                │
│                                                          │
│  ┌──────────────┐         ┌──────────────┐            │
│  │HTML Template │         │CSV Generator  │            │
│  │Generation    │         │               │            │
│  └──────┬───────┘         └──────┬───────┘            │
│         │                         │                     │
│         ▼                         ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │Apply Styling │         │Format Columns │            │
│  │& Charts      │         │Add Headers    │            │
│  └──────┬───────┘         └──────┬───────┘            │
│         │                         │                     │
│         ▼                         ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │PDF Renderer  │         │CSV Writer     │            │
│  └──────┬───────┘         └──────┬───────┘            │
│         │                         │                     │
│         └────────┬────────────────┘                     │
│                  ▼                                      │
│         ┌─────────────┐                                │
│         │  Download   │                                │
│         │   Trigger   │                                │
│         └─────────────┘                                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 10. Data Flow Between Mock and Production Modes

```
┌────────────────────────────────────────────────────────────┐
│              Mock vs Production Data Flow                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   MOCK MODE                    PRODUCTION MODE            │
│   ─────────                    ───────────────            │
│                                                            │
│  ┌──────────┐                 ┌──────────┐               │
│  │  Request │                 │  Request │               │
│  └────┬─────┘                 └────┬─────┘               │
│       │                             │                      │
│       ▼                             ▼                      │
│  ┌──────────┐                 ┌──────────┐               │
│  │Check Mode│                 │Check Mode│               │
│  │USE_MOCK  │                 │USE_MOCK  │               │
│  │  =true   │                 │  =false  │               │
│  └────┬─────┘                 └────┬─────┘               │
│       │                             │                      │
│       ▼                             ▼                      │
│  ┌──────────┐                 ┌──────────┐               │
│  │Hardcoded │                 │  Query   │               │
│  │   Data   │                 │Database  │               │
│  ├──────────┤                 ├──────────┤               │
│  │Holdings: │                 │SELECT *  │               │
│  │[AAPL,    │                 │FROM      │               │
│  │ GOOGL,   │                 │holdings  │               │
│  │ ...]     │                 │WHERE ... │               │
│  └────┬─────┘                 └────┬─────┘               │
│       │                             │                      │
│       ▼                             ▼                      │
│  ┌──────────┐                 ┌──────────┐               │
│  │  Simple  │                 │ Complex  │               │
│  │   Calc   │                 │Analytics │               │
│  ├──────────┤                 ├──────────┤               │
│  │Beta only │                 │• Factors │               │
│  │Linear    │                 │• Correlat│               │
│  └────┬─────┘                 │• History │               │
│       │                       └────┬─────┘               │
│       │                             │                      │
│       └─────────┬───────────────────┘                      │
│                 ▼                                          │
│           ┌──────────┐                                    │
│           │ Response │                                    │
│           └──────────┘                                    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Summary

These visual flow diagrams illustrate:

1. **Master Application Flow** - Overall system architecture
2. **Authentication Flow** - Login and authorization process
3. **Portfolio Analysis** - Complete analysis workflow
4. **Macro Dashboard** - Dalio framework reasoning chains
5. **Scenario Analysis** - Stress testing pipeline
6. **Alert System** - Creation and monitoring flow
7. **AI Analysis** - Natural language processing
8. **Optimization** - Mean-variance optimization
9. **Export Generation** - PDF/CSV creation
10. **Mock vs Production** - Data flow differences

Each diagram shows:
- **Input sources** (user actions, APIs, databases)
- **Processing steps** (calculations, validations)
- **Decision points** (branching logic)
- **Output destinations** (UI updates, files, notifications)

The flows are designed to be:
- **Sequential** where dependencies exist
- **Parallel** where operations are independent
- **Fault-tolerant** with error handling paths
- **Optimized** for performance and user experience