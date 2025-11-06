# Financial Domain Knowledge - DawsOS Portfolio Management

**Purpose:** Comprehensive financial theory and business logic reference for DawsOS developers
**Audience:** Software engineers implementing portfolio management features
**Scope:** Core finance concepts, regulatory requirements, calculation methodologies
**Last Updated:** 2025-11-05

---

## Table of Contents

1. [Core Portfolio Accounting Concepts](#1-core-portfolio-accounting-concepts)
2. [Corporate Actions Theory](#2-corporate-actions-theory)
3. [Performance Attribution Theory](#3-performance-attribution-theory)
4. [Factor-Based Risk Models](#4-factor-based-risk-models)
5. [Scenario Analysis & Stress Testing](#5-scenario-analysis--stress-testing)
6. [Risk Metrics](#6-risk-metrics)
7. [Macro Regime Detection](#7-macro-regime-detection)
8. [Regulatory & Compliance](#8-regulatory--compliance)
9. [Transaction Processing](#9-transaction-processing)
10. [Portfolio Optimization Theory](#10-portfolio-optimization-theory)

---

## 1. Core Portfolio Accounting Concepts

### 1.1 Cost Basis & Lot Accounting

**Definition:**
Cost basis is the original value of an asset for tax purposes, adjusted for splits, dividends, and return of capital. It determines capital gains/losses when the asset is sold.

**Regulatory Context:**
- **IRS (US):** Requires cost basis reporting for all securities (since 2011)
- **CRA (Canada):** Requires adjusted cost base (ACB) tracking
- **HMRC (UK):** Uses "pooled cost" for shares of same class

**Cost Basis Methods:**

#### FIFO (First-In, First-Out)
- **Definition:** Oldest shares are sold first
- **Tax Default:** IRS default if no method specified
- **Use Case:** Rising markets (sell lower cost basis = higher gains)
- **Example:**
  ```
  Buy 100 AAPL @ $150 (Jan 1)
  Buy 100 AAPL @ $160 (Feb 1)
  Sell 50 AAPL @ $170 (Mar 1)
  → Sells from Jan lot: Gain = 50 × ($170 - $150) = $1,000
  ```

#### LIFO (Last-In, First-Out)
- **Definition:** Newest shares are sold first
- **Allowed For:** Commodities, futures (not allowed for stocks in US since 2011)
- **Use Case:** Declining markets (sell higher cost basis = lower gains)

#### Average Cost
- **Definition:** Weighted average of all purchase prices
- **Required For:** Mutual funds (IRS default)
- **Use Case:** Simplicity, frequent purchases (dollar-cost averaging)
- **Formula:**
  ```
  Average Cost = Total Cost / Total Shares
  Example: ($15,000 + $16,000) / 200 = $155 per share
  ```

#### Specific Lot Identification
- **Definition:** Investor specifies which shares to sell
- **Requirement:** Must identify lots on trade date (not settlement)
- **Use Case:** Tax optimization (tax loss harvesting)
- **Documentation:** Written confirmation to broker required
- **Example:**
  ```
  Portfolio:
  - Lot A: 100 AAPL @ $150 (loss: -$2,000)
  - Lot B: 100 AAPL @ $160 (gain: +$1,000)

  Tax harvesting strategy:
  → Sell Lot A to realize loss, offset other gains
  → Keep Lot B (unrealized gain, no current tax)
  ```

**DawsOS Implementation:**
- File: `backend/app/services/lots.py`
- Database: `lots` table with `acquisition_date`, `qty_open`, `cost_basis`
- **CRITICAL ISSUE:** No `cost_basis_method` field in portfolios table ([FINTECH_UX_ANALYSIS.md](FINTECH_UX_ANALYSIS.md#issue-2))

**Wash Sale Rules (US):**
- **Definition:** Cannot claim loss if repurchase "substantially identical" security within 30 days (before or after)
- **Impact:** Disallowed loss added to cost basis of new purchase
- **Example:**
  ```
  Sell 100 AAPL @ $140 (cost: $150, loss: -$1,000) on Dec 15
  Buy 100 AAPL @ $145 on Dec 20 (within 30 days)
  → Loss disallowed, new cost basis = $145 + $10 = $155
  ```
- **DawsOS Status:** Not implemented (P2 feature)

---

### 1.2 Realized vs Unrealized P&L

**GAAP Definition (ASC 320):**
- **Realized P&L:** Actual profit/loss from closed positions (sales)
- **Unrealized P&L:** Mark-to-market gain/loss on open positions (not sold)

**Key Distinction:**

| Aspect | Realized P&L | Unrealized P&L |
|--------|-------------|----------------|
| **Tax Status** | Taxable in year realized | Not taxable until realized |
| **Cash Impact** | Affects cash balance | No cash impact |
| **Reversibility** | Permanent (locked in) | Can reverse if price changes |
| **Reporting** | Required on tax return | Optional (accounting only) |

**Finance Theory:**
- **Total P&L = Realized P&L + Unrealized P&L**
- Unrealized becomes realized upon sale
- Important for tax planning (harvest losses in Dec, defer gains to Jan)

**Tax Treatment:**
- **Short-term gains:** Held ≤1 year, taxed as ordinary income (up to 37% US)
- **Long-term gains:** Held >1 year, preferential rate (0%, 15%, 20% US)
- **Capital loss limit:** $3,000/year deduction (US), excess carries forward

**Example:**
```
Portfolio on Dec 31, 2024:
- Closed positions (sold in 2024):
  - AAPL: Bought $150, Sold $170 → Realized gain: +$2,000
  - MSFT: Bought $300, Sold $280 → Realized loss: -$2,000

- Open positions (still held):
  - GOOGL: Cost $140, Market $160 → Unrealized gain: +$2,000
  - TSLA: Cost $250, Market $200 → Unrealized loss: -$5,000

Total P&L Summary:
- Realized P&L: +$2,000 - $2,000 = $0 (tax neutral)
- Unrealized P&L: +$2,000 - $5,000 = -$3,000
- Total P&L: $0 - $3,000 = -$3,000

Tax Impact: $0 realized gains → $0 tax owed
```

**DawsOS CRITICAL BUG:**
- File: `full_ui.html:8756-8768`
- **Issue:** UI calculates `totalPnL = currentValue - costBasis` (treats all as unrealized)
- **Missing:** Separation of realized vs unrealized
- **Risk:** Tax reporting errors, investor misrepresentation
- **Fix Required:** Backend must expose `realized_pl` from `transactions` table

**Mark-to-Market Accounting:**
- **Definition:** Revalue assets to current market price daily
- **Required For:** Trading securities (ASC 320), derivatives (ASC 815)
- **Example:** Hedge fund must mark all positions to market daily for NAV calculation

---

### 1.3 Multi-Currency Portfolios

**Base Currency vs Local Currency:**
- **Base Currency:** Reporting currency of portfolio (e.g., CAD for Canadian investor)
- **Local Currency:** Original currency of security (e.g., USD for Apple stock)
- **FX Rate:** Conversion rate between currencies (e.g., USD/CAD = 1.35)

**FX Conversion Dates:**

| Date Type | Use Case | Example |
|-----------|----------|---------|
| **Trade Date** | Establish cost basis | Buy AAPL on Jan 1 @ USD/CAD 1.30 |
| **Settlement Date** | Cash movement (T+2) | Cash debited Jan 3 @ USD/CAD 1.32 |
| **Report Date** | Current valuation | NAV on Mar 1 @ USD/CAD 1.35 |
| **Pay Date** | Corporate actions | Dividend paid Mar 15 @ USD/CAD 1.33 |

**Currency Attribution Methodology:**

Total Return decomposition:
```
Total Return (Base Currency) = Local Return + FX Return + Interaction

Example (CAD investor owns US stocks):
- Stock price: $100 → $110 (local return: +10%)
- FX rate: 1.30 → 1.35 CAD/USD (FX return: +3.85%)
- Total return in CAD: (110 × 1.35) / (100 × 1.30) - 1 = +14.04%

Attribution:
- Local return: +10.00%
- FX return: +3.85%
- Interaction: +0.19% (10% × 3.85% ≈ 0.4%)
- Total: 14.04%
```

**DawsOS Implementation:**
- Service: `backend/app/services/currency_attribution.py`
- Database: `fx_rates` table with daily rates
- FX conversion uses **pay_date** for ADR dividends (critical for withholding tax accuracy)

**IFRS 9 Hedge Accounting:**
- **Net Investment Hedge:** Hedge FX risk of foreign subsidiary
- **Cash Flow Hedge:** Hedge future FX-denominated cash flows
- **Fair Value Hedge:** Hedge FX risk of recognized asset/liability
- **Effectiveness Test:** 80-125% correlation required
- **DawsOS Status:** Not implemented (institutional feature)

**DawsOS CRITICAL BUG:**
- File: `full_ui.html:1741-1746`
- **Issue:** Currency hardcoded to `'USD'`, ignores `portfolio.base_currency`
- **Impact:** CAD/GBP/EUR portfolios display wrong currency symbols
- **Fix:** Dynamic currency from portfolio context

---

## 2. Corporate Actions Theory

### 2.1 Cash Dividends

**Key Dates:**

| Date | Definition | Implication |
|------|------------|-------------|
| **Declaration Date** | Board announces dividend | Creates liability |
| **Ex-Dividend Date** | First day trading without dividend | Must own before this date |
| **Record Date** | Shareholders of record receive dividend | Usually 1 day after ex-date |
| **Pay Date** | Dividend paid to shareholders | Cash received |

**Ex-Dividend Date Mechanics:**
- Stock trades "ex-dividend" = without dividend entitlement
- Stock price typically drops by dividend amount on ex-date
- **Rule:** Must own stock before ex-date to receive dividend
- **Example:**
  ```
  Apple $150, announces $0.24 dividend
  - Dec 10: Declaration date
  - Dec 12: Ex-dividend date → stock opens at ~$149.76
  - Dec 13: Record date
  - Dec 20: Pay date → $0.24 paid to shareholders

  Buy on Dec 11: Get dividend (own before ex-date)
  Buy on Dec 12: No dividend (bought on ex-date)
  ```

**ADR Dividend Withholding Tax:**
- **ADR (American Depositary Receipt):** US-traded foreign stock
- **Withholding Tax:** Foreign country taxes dividends (10-35%)
- **Treaty Rates:** US-Canada treaty = 15% withholding
- **FX Conversion:** Use **pay_date** FX rate (not ex-date!)
- **Example:**
  ```
  Own 100 shares of Canadian bank (ADR) in USD portfolio
  - Dividend declared: C$0.90/share
  - Withholding: 15% = C$0.135/share
  - Net dividend: C$0.765/share
  - Pay date FX: USD/CAD = 1.35
  - USD received: 100 × (0.765/1.35) = $56.67
  ```

**DawsOS Implementation:**
- File: `backend/app/services/corporate_actions.py:91-249`
- **Critical:** Uses pay_date FX rate for ADR accuracy (line 120-145)
- **Formula:**
  ```python
  gross_amount = shares × dividend_per_share
  withholding = gross_amount × withholding_rate
  net_amount = gross_amount - withholding
  net_base_currency = net_amount / pay_fx_rate
  ```

**Tax Treatment (US):**
- **Qualified Dividends:** 15-20% tax rate (hold >60 days)
- **Ordinary Dividends:** Taxed as ordinary income (up to 37%)
- **Foreign Tax Credit:** Can claim withholding tax as credit (Form 1116)

**Dividend Capture Strategy:**
- Buy stock before ex-date, sell after pay date
- Capture dividend while minimizing price risk
- **Risk:** Stock price drop > dividend amount
- **Cost:** Trading commissions, short-term capital gains tax

---

### 2.2 Stock Splits

**Forward Split (2:1 example):**
```
Before: Own 100 shares @ $200 = $20,000
After:  Own 200 shares @ $100 = $20,000

Cost basis adjustment:
- Old: $200/share
- New: $200/2 = $100/share
```

**Reverse Split (1:10 example):**
```
Before: Own 1,000 shares @ $1 = $1,000
After:  Own 100 shares @ $10 = $1,000

Cost basis adjustment:
- Old: $1/share
- New: $1 × 10 = $10/share
```

**Fractional Shares:**
- **Issue:** Reverse split may create fractions (e.g., 105 shares → 10.5 shares)
- **Resolution:** Broker typically cashes out fractions at split price
- **Example:**
  ```
  Own 105 shares @ $1 before 1:10 reverse split
  → 10 full shares @ $10 + 0.5 fractional share
  → Receive $5 cash for fractional (0.5 × $10)
  → Final: 10 shares + $5 cash
  ```

**Cost Basis Adjustment Rules (IRS):**
- Total cost basis remains unchanged
- Per-share cost basis adjusts by split ratio
- Acquisition date stays the same (for tax lot tracking)
- Not a taxable event (no gain/loss recognition)

**DawsOS Implementation:**
- File: `backend/app/services/corporate_actions.py:251-344`
- Adjusts all open lots for the symbol
- Updates `qty_open` and `cost_basis_per_share`
- **Note:** Fractional share handling not yet implemented

---

### 2.3 Spin-offs, Mergers, Rights Offerings

**Tax-Free Spin-off:**
- Parent company separates subsidiary
- Shareholders receive new shares (e.g., 1 SpinCo for every 5 ParentCo)
- **Cost Basis Allocation:** Based on relative market values on distribution date
- **Example:**
  ```
  Own 100 ParentCo @ $100 cost basis ($10,000 total)
  Spin-off: Receive 20 SpinCo (1:5 ratio)

  Day 1 market values:
  - ParentCo: $80 × 100 = $8,000 (80% of combined)
  - SpinCo: $10 × 20 = $200 (20% of combined)

  Cost basis allocation:
  - ParentCo: $10,000 × 80% = $8,000 ($80/share)
  - SpinCo: $10,000 × 20% = $2,000 ($100/share)
  ```

**Taxable Merger:**
- Acquirer purchases target, shareholders receive cash or stock
- Taxable if cash received, tax-deferred if stock-for-stock
- **Example:** Microsoft buys LinkedIn for $196/share cash
  - Cost basis: $50/share
  - Tax: Capital gain = ($196 - $50) × shares

**Rights Offering:**
- Existing shareholders get right to buy additional shares (usually at discount)
- Can exercise (buy more) or sell rights
- Cost basis = exercise price + value of rights used

**DawsOS Status:** Spin-offs and rights offerings not yet implemented (P3 feature)

---

## 3. Performance Attribution Theory

### 3.1 Time-Weighted Return (TWR)

**Definition:**
Return that eliminates the effect of cash flow timing, measuring purely the investment performance.

**Why It Matters:**
- Compares manager skill (independent of investor decisions to add/withdraw cash)
- Industry standard for mutual funds, pension funds
- Required for GIPS (Global Investment Performance Standards) compliance

**Calculation Method:**
```
TWR = [(1 + R1) × (1 + R2) × ... × (1 + Rn)] - 1

Where Ri = (Ending Value - Beginning Value - Cash Flow) / (Beginning Value + Weighted Cash Flow)
```

**Example:**
```
Portfolio performance with cash flows:

Period 1 (Jan 1 - Mar 31):
- Start: $100,000
- End: $110,000 (before deposit)
- Deposit on Mar 31: $50,000
- Return: (110,000 - 100,000) / 100,000 = 10%

Period 2 (Apr 1 - Jun 30):
- Start: $160,000 (110k + 50k deposit)
- End: $168,000
- Return: (168,000 - 160,000) / 160,000 = 5%

TWR = (1.10 × 1.05) - 1 = 15.5%
```

**Geometric vs Arithmetic Linking:**
- **Geometric (correct):** (1 + R1) × (1 + R2) - 1 = 15.5%
- **Arithmetic (wrong):** R1 + R2 = 15.0%
- Geometric accounts for compounding

**DawsOS Implementation:**
- Pattern: `portfolio_overview` includes `twr_1y`, `twr_ytd`
- File: `full_ui.html:2848`
- **Issue:** No explanation of TWR vs MWR ([FINTECH_UX_ANALYSIS.md](FINTECH_UX_ANALYSIS.md#issue-4))

---

### 3.2 Money-Weighted Return (MWR/IRR)

**Definition:**
Return that includes the timing and amount of cash flows, measuring the actual investor experience.

**Why It Matters:**
- Shows what the investor actually earned (timing luck/skill)
- Sensitive to when deposits/withdrawals occurred
- Personal return metric (not for manager comparison)

**Calculation (Internal Rate of Return):**
```
Find r such that: NPV = 0

NPV = CF0 + CF1/(1+r)^t1 + CF2/(1+r)^t2 + ... + CFn/(1+r)^tn = 0

Where:
- CF0 = Initial investment (negative)
- CFi = Cash flows (positive = withdrawal, negative = deposit)
- ti = Time from start in years
- CFn = Final value (positive)
```

**Example:**
```
Same portfolio as TWR example:

Cashflows:
- Jan 1: -$100,000 (initial investment)
- Mar 31: -$50,000 (deposit)
- Jun 30: +$168,000 (final value)

Solving for r (IRR): MWR = 12.3%

Why MWR < TWR?
- Deposited $50k just before period of lower returns (5%)
- Bad timing reduced personal return
- TWR = 15.5% (manager skill) > MWR = 12.3% (investor experience)
```

**When MWR > TWR:**
- Deposit cash before high-return period (good timing)
- Withdraw cash before low-return period (good timing)

**DawsOS Implementation:**
- Pattern includes `mwr_1y`
- File: `full_ui.html:2848`
- **Missing:** Explanation of difference, when to use each

---

### 3.3 Attribution Hierarchy

**Brinson-Fachler Attribution Model:**

Decomposes portfolio excess return vs benchmark into:
1. **Allocation Effect:** Return from over/underweighting sectors
2. **Selection Effect:** Return from picking securities within sectors
3. **Interaction Effect:** Combined effect of allocation + selection

**Formula:**
```
Allocation Effect = Σ(wi - Wi) × (Ri - R)
Selection Effect = Σ Wi × (ri - Ri)
Interaction = Σ(wi - Wi) × (ri - Ri)

Where:
- wi = portfolio weight in sector i
- Wi = benchmark weight in sector i
- ri = portfolio return in sector i
- Ri = benchmark return in sector i
- R = total benchmark return
```

**Example:**
```
Sector: Technology

Portfolio:
- Weight: 40% (overweight vs benchmark 30%)
- Return: 15%

Benchmark:
- Weight: 30%
- Return: 10%
- Total benchmark return: 8%

Attribution:
- Allocation: (40% - 30%) × (10% - 8%) = +0.2% (overweight helped)
- Selection: 30% × (15% - 10%) = +1.5% (stock picking helped)
- Interaction: (40% - 30%) × (15% - 10%) = +0.5% (both helped)
- Total attribution: +2.2%
```

**Attribution Hierarchy:**
```
Total Return
├── Asset Allocation Attribution
│   ├── Equity (60% vs 55% benchmark)
│   ├── Fixed Income (30% vs 35%)
│   └── Cash (10% vs 10%)
├── Sector Attribution (within equity)
│   ├── Technology (+2.3%)
│   ├── Healthcare (-0.8%)
│   └── Financials (+1.1%)
├── Security Selection
│   ├── AAPL: +$12,450
│   ├── MSFT: +$8,230
│   └── GOOGL: -$3,100
└── Factor Attribution
    ├── Market beta: +3.5%
    ├── Value factor: -1.2%
    └── Momentum: +0.8%
```

**DawsOS CRITICAL ISSUE:**
- File: `full_ui.html:9153-9169`
- **Problem:** Attribution page only shows currency attribution
- **Missing:** Sector attribution, security attribution, factor attribution
- **Backend:** Has currency_attribution service but no unified framework

---

## 4. Factor-Based Risk Models

### 4.1 Factor Theory

**Modern Portfolio Theory (MPT) Extension:**
- Traditional MPT: Risk = volatility (standard deviation)
- Factor models: Risk = systematic (factor) risk + idiosyncratic (stock-specific) risk

**Total Risk Decomposition:**
```
Total Risk² = Factor Risk² + Idiosyncratic Risk²

Factor Risk = driven by market-wide factors (non-diversifiable)
Idiosyncratic Risk = stock-specific (diversifiable)
```

**Common Factor Models:**

**1. Fama-French 3-Factor Model:**
```
Ri - Rf = α + β1(Rm - Rf) + β2(SMB) + β3(HML) + εi

Where:
- Ri = Stock return
- Rf = Risk-free rate
- Rm = Market return
- SMB = Small Minus Big (size factor)
- HML = High Minus Low (value factor)
- α = Jensen's alpha (manager skill)
- εi = Idiosyncratic risk
```

**2. Fama-French 5-Factor Model (adds):**
- **RMW:** Robust Minus Weak (profitability)
- **CMA:** Conservative Minus Aggressive (investment)

**3. DawsOS Macro Factor Model:**

File: `backend/app/services/scenarios.py:82-87`

```python
# Factor shocks (5 factors):
real_rates_bps: float = 0.0      # Real interest rate risk
inflation_bps: float = 0.0       # Inflation risk
credit_spread_bps: float = 0.0   # Credit risk
usd_pct: float = 0.0             # Currency risk
equity_pct: float = 0.0          # Equity market risk
```

**Factor Beta Calculation (Regression):**
```
Return_i = α + β × Factor_Return + ε

Example: Technology stock sensitivity to rates
- Run regression: Stock Return vs 10Y Treasury Change
- Result: β = -2.0 (stock drops 2% when rates rise 1%)
- Interpretation: Technology stocks hurt by rising rates (PV of future earnings)
```

**Factor Exposure Limits:**
- **Market Beta:** Typical range 0.8-1.2 for equity portfolios
- **Sector Concentration:** Max 25-30% in single sector
- **Factor Tilt:** Max 0.3-0.5 active exposure vs benchmark

**DawsOS Implementation:**
- File: `backend/app/services/scenarios.py:297-379`
- Database: `position_factor_betas` table stores calculated betas
- **Fallback:** If betas unavailable, estimate from security type/sector

**Beta Estimation by Security Type (lines 325-366):**
```python
# Real rate beta:
BOND: -8.0       # Very sensitive (duration effect)
EQUITY: -2.0     # Moderately sensitive (PV discount rate)

# Inflation beta:
BOND: -6.0       # Negative (inflation erodes fixed payments)
Energy: +2.0     # Positive (commodity correlation)
Materials: +2.0  # Positive (commodity correlation)

# Credit beta:
BOND: +5.0       # Sensitive to spreads
Financial: +1.5  # Exposed to credit markets

# USD beta:
Foreign: -0.5    # FX headwind
Tech: -0.3       # Exporters hurt by strong USD

# Equity beta:
Tech: 1.3        # Higher than market
Financial: 1.1   # Slightly above market
BOND: 0.0        # No equity exposure
```

---

### 4.2 Factor Attribution

**Decomposing Returns by Factor Exposure:**

**Formula:**
```
Factor Contribution = Beta × Factor Return × Market Value

Example:
Position: $100,000 in technology stocks
Real rate beta: -2.0
Factor shock: +100bp (1%)

Delta P&L = -2.0 × 0.01 × $100,000 = -$2,000

Interpretation: Rising rates (100bp) caused $2,000 loss due to negative rate beta
```

**Portfolio-Level Aggregation:**
```
Total Factor Risk = Σ(Positioni × Betai × Factor Volatility)

Example portfolio:
- Tech stocks: $100k × beta -2.0 = -$200k rate exposure
- Bonds: $50k × beta -8.0 = -$400k rate exposure
- Total rate exposure: -$600k equivalent
```

**DawsOS Implementation:**
- File: `backend/app/services/scenarios.py:481-553`
- Method: `_compute_position_delta()`
- Returns `factor_contributions` dict with breakdown by factor

**Factor Timing vs Factor Exposure:**
- **Factor Exposure:** Strategic beta (long-term allocation)
- **Factor Timing:** Tactical beta (overweight/underweight factors based on regime)
- Example:
  - Strategic: Always maintain +0.3 value tilt
  - Tactical: Increase to +0.5 in recession (value outperforms growth)

**Risk-Adjusted Attribution:**
- **Sharpe Ratio by Factor:** Return/Risk for each factor exposure
- **Information Ratio:** Excess return / Tracking error
- **Factor Sharpe:** (Factor Return - Rf) / Factor Volatility

**DawsOS Status:** Factor attribution calculated but not displayed in UI

---

## 5. Scenario Analysis & Stress Testing

### 5.1 Scenario Construction

**Scenario Types:**

**1. Historical Scenarios:**
- 2008 Financial Crisis:
  - Credit spreads: +500bp
  - Equity: -40%
  - Rates: -200bp (flight to quality)
  - USD: +15% (safe haven)

- COVID-19 Crash (Feb-Mar 2020):
  - Equity: -35%
  - Volatility (VIX): 80
  - Oil: -60%
  - Corporate bonds: -20%

**2. Hypothetical Scenarios:**
- Parallel rate shift: +100bp across all maturities
- Curve steepening: +0bp 2Y, +100bp 10Y
- Currency shock: USD +10%
- Inflation surprise: CPI +2%

**3. Dalio Deleveraging Framework:**

File: `backend/app/services/scenarios.py:148-185`

**Money Printing Deleveraging (Inflationary):**
```python
real_rates_bps=25.0,        # Modest rate rise
inflation_bps=150.0,        # High inflation
credit_spread_bps=-50.0,    # Spreads tighten (risk-on)
usd_pct=-0.12,              # USD weakens (debasement)
equity_pct=0.05,            # Stocks up (nominal gains)
```
- **Example:** 1970s US, current Argentina
- **Implication:** Own real assets (commodities, TIPS), avoid bonds

**Austerity Deleveraging (Deflationary):**
```python
real_rates_bps=-75.0,       # Rates fall (recession)
inflation_bps=-50.0,        # Deflation
credit_spread_bps=100.0,    # Spreads widen (risk-off)
usd_pct=0.08,               # USD strengthens (safe haven)
equity_pct=-0.20,           # Stocks down
```
- **Example:** Greece 2010-2015, Japan 1990s
- **Implication:** Own cash, treasuries, avoid equities

**Default Deleveraging (Deep Deflation):**
```python
real_rates_bps=-150.0,      # Rates collapse
inflation_bps=-100.0,       # Severe deflation
credit_spread_bps=300.0,    # Credit markets freeze
usd_pct=0.15,               # Flight to USD
equity_pct=-0.40,           # Severe equity selloff
```
- **Example:** 2008 financial crisis
- **Implication:** Cash is king, treasuries only safe asset

---

### 5.2 Scenario Application

**Shock Transmission Mechanism:**

**Step 1: Define Factor Shocks**
```python
# Rates up +100bp scenario
shock = Shock(
    real_rates_bps=100.0,  # 1% rate increase
    usd_pct=0.02,          # USD +2% (rates attract capital)
    equity_pct=-0.05,      # Equity -5% (P/E compression)
)
```

**Step 2: Apply to Each Position**
```
Delta P&L = Beta × Shock × Market Value

Position: $100,000 in TLT (long-term treasuries)
Beta (real_rates): -8.0  # Very sensitive to rates
Shock: +100bp = +0.01

Delta = -8.0 × 0.01 × $100,000 = -$8,000

Interpretation: Rising rates cause $8,000 loss on bond position
```

**Step 3: Aggregate Portfolio Impact**
```python
# From scenarios.py:429-479
position_results = []
total_delta_pl = Decimal("0")

for pos in positions:
    result = self._compute_position_delta(pos, shock)
    position_results.append(result)
    total_delta_pl += result.delta_pl

# Portfolio-level summary
total_delta_pl_pct = total_delta_pl / pre_shock_nav
```

**DawsOS Implementation:**
- File: `backend/app/services/scenarios.py:381-479`
- Method: `apply_scenario()`
- Returns: `ScenarioResult` with winners/losers, factor contributions

**Example Output:**
```python
ScenarioResult(
    shock_name="Rates Up +100bp",
    pre_shock_nav=Decimal("1000000"),
    post_shock_nav=Decimal("950000"),
    total_delta_pl=Decimal("-50000"),
    total_delta_pl_pct=-0.05,  # -5%
    winners=[
        PositionShockResult(symbol="DXY", delta_pl=+$5,000),  # USD strength
        ...
    ],
    losers=[
        PositionShockResult(symbol="TLT", delta_pl=-$20,000),  # Bond crash
        PositionShockResult(symbol="AAPL", delta_pl=-$15,000),  # Tech hurt
        ...
    ],
    factor_contributions={
        "real_rates": Decimal("-45000"),   # Most of loss
        "usd": Decimal("+5000"),           # Small gain
        "equity": Decimal("-10000"),       # P/E compression
    }
)
```

---

### 5.3 Hedge Recommendations

**Scenario-Specific Hedging Strategies:**

File: `backend/app/services/scenarios.py:555-681`

**Rates Up Scenario:**
```python
# Hedge 1: Treasury Puts
hedge = HedgeRecommendation(
    hedge_type="Treasury Puts",
    rationale="TLT puts protect against rising rates (falling bond prices)",
    notional=abs(total_loss) * Decimal("0.5"),  # Hedge 50%
    instruments=["TLT", "IEF", "TBT"]
)

# Hedge 2: Steepener Trade
# Short 2Y (gains when rates rise), Long 10Y (duration hedge)
# Profits if curve steepens (2Y rises faster than 10Y)
```

**USD Up Scenario:**
```python
# Hedge: FX Forward
# Lock in current USD/CAD rate for future date
# Example: Portfolio has $500k CAD exposure
# Forward contract: Sell CAD $500k @ 1.35 for 3 months
# If USD strengthens (CAD weakens to 1.40), forward offsets FX loss
```

**CPI Surprise (Inflation):**
```python
# Hedge 1: TIPS (Treasury Inflation-Protected Securities)
# Principal adjusts with CPI → natural inflation hedge
# Notional: 75% of inflation exposure

# Hedge 2: Commodity Basket
# Commodities benefit from inflation (input costs rise)
# Instruments: DBC, PDBC, GLD (gold)
```

**Credit Spread Widening:**
```python
# Hedge: HYG Puts (High-Yield Corporate Bond ETF)
# Credit spreads widen → HYG falls → puts profit
# Notional: 60% of credit exposure

# Alternative: Buy CDS (Credit Default Swap) protection
# CDX.IG index protects investment-grade portfolio
```

**Equity Selloff:**
```python
# Hedge 1: SPY Puts
# S&P 500 index puts protect against market crash
# Strike: 10% out-of-money (cost-efficient)
# Notional: 80% of equity exposure

# Hedge 2: VIX Calls
# Volatility spikes during selloffs
# VIX calls profit from fear (non-linear payoff)
# Instruments: VXX, UVXY
```

**DawsOS Implementation:**
- Method: `suggest_hedges()`
- **Input:** Scenario losers + shock type
- **Output:** List of hedge recommendations
- **UI Status:** Not displayed ([FINTECH_UX_ANALYSIS.md](FINTECH_UX_ANALYSIS.md))

---

## 6. Risk Metrics

### 6.1 Drawdown at Risk (DaR)

**Definition:**
Maximum expected drawdown (peak-to-trough decline) at a given confidence level over a specified horizon.

**Comparison to VaR (Value at Risk):**
- **VaR:** "What's the maximum loss in 1 day at 95% confidence?"
- **DaR:** "What's the maximum drawdown in 30 days at 95% confidence?"
- **Key Difference:** DaR measures cumulative decline, VaR measures single-period loss

**Calculation Method (Scenario-Based):**

File: `backend/app/services/scenarios.py:703-937`

**Step 1: Run All Scenarios**
```python
scenario_drawdowns = []

for shock_type in SCENARIO_LIBRARY:
    result = await apply_scenario(portfolio_id, shock_type)
    drawdown_pct = result.total_delta_pl_pct
    scenario_drawdowns.append({
        "scenario": shock_type,
        "drawdown_pct": drawdown_pct,  # e.g., -18.5%
    })
```

**Step 2: Compute Percentile**
```python
# Sort scenarios by drawdown (most negative first)
scenario_drawdowns.sort(key=lambda x: x["drawdown_pct"])

# 95th percentile = 5% worst outcome
import numpy as np
dar_pct = np.percentile(drawdowns, 95)

# Example: If 95th percentile = -18.5%, then:
# "95% confidence that drawdown won't exceed 18.5%"
```

**Example:**
```
Portfolio NAV: $1,000,000
DaR Calculation (30-day horizon, 95% confidence):

11 scenarios run:
1. Default deleveraging: -40%
2. Equity selloff: -28%
3. Credit spread widening: -22%
4. Austerity deleveraging: -20%
5. CPI surprise: -15%
6. Rates up: -12%
7. USD up: -8%
8. Rates down: -5%
9. USD down: -3%
10. Credit tightening: +2%
11. Equity rally: +8%

95th percentile (5% worst) = between scenarios 1-2
DaR = -30% (interpolated)

Interpretation:
- 95% confidence max drawdown ≤ $300,000 in 30 days
- 5% chance drawdown > $300,000 (tail risk)
```

**Regime-Conditional DaR:**
```python
# File: scenarios.py:703
async def compute_dar(
    self,
    regime: str,  # Current macro regime
    ...
)

# DaR varies by regime:
# Goldilocks (low volatility): DaR = -8%
# Stagflation (high volatility): DaR = -22%
# Deflation (crisis risk): DaR = -35%
```

**DaR History Tracking:**
```python
# Persisted to dar_history table (lines 846-904)
INSERT INTO dar_history (
    portfolio_id, asof_date, regime,
    dar, dar_pct, mean_drawdown, max_drawdown,
    ...
)

# Enables trending analysis:
# - Is DaR increasing over time? (rising risk)
# - Actual drawdown vs DaR? (model accuracy)
# - Regime shifts affecting risk?
```

**DawsOS UI ISSUE:**
- Backend tracks DaR history, UI shows single point only
- **Missing:** DaR trend chart, regime breakdown, factor attribution
- **Value:** See if portfolio risk is increasing/stable/decreasing

---

### 6.2 Maximum Drawdown (MDD)

**Definition:**
Largest peak-to-trough decline in portfolio value over a period.

**Calculation:**
```
For each date t:
    Peak[t] = max(NAV[0], NAV[1], ..., NAV[t])
    Drawdown[t] = (NAV[t] - Peak[t]) / Peak[t]

MDD = min(Drawdown[0], Drawdown[1], ..., Drawdown[T])
```

**Example:**
```
Portfolio NAV over time:
Date     NAV        Peak    Drawdown
Jan 1    $1,000,000 $1M     0%
Feb 1    $1,100,000 $1.1M   0%
Mar 1    $1,050,000 $1.1M   -4.5%  ← Drawdown
Apr 1    $950,000   $1.1M   -13.6% ← Larger drawdown
May 1    $1,000,000 $1.1M   -9.1%
Jun 1    $1,200,000 $1.2M   0%     ← New peak, drawdown ends

Maximum Drawdown = -13.6% (Apr 1)
Underwater period = Feb 1 - Jun 1 (4 months)
```

**Key Metrics:**
- **MDD:** -13.6% (magnitude)
- **Duration:** 4 months (peak to new peak)
- **Recovery Time:** 4 months
- **Underwater Period:** Time spent below previous peak

**Comparison to DaR:**
- **MDD:** Historical (what happened)
- **DaR:** Forward-looking (what could happen)
- **Use:** Compare DaR estimate to actual MDD (model validation)

---

### 6.3 Other Risk Metrics

**Volatility (Standard Deviation):**
```
σ = sqrt(Σ(Ri - R_avg)² / (n - 1))

Annualized: σ_annual = σ_daily × sqrt(252)

Example:
Daily returns: [+1%, -0.5%, +0.8%, -1.2%, +0.3%]
Average: 0.08%
Std dev: 0.85% daily
Annualized: 0.85% × sqrt(252) = 13.5%
```

**Sharpe Ratio:**
```
Sharpe = (R_portfolio - R_risk_free) / σ_portfolio

Example:
Portfolio return: 12%
Risk-free rate: 2%
Volatility: 15%
Sharpe = (12% - 2%) / 15% = 0.67

Interpretation:
- Sharpe > 1: Good risk-adjusted return
- Sharpe > 2: Excellent
- Sharpe < 0: Losing money after risk adjustment
```

**Sortino Ratio (Downside Risk Only):**
```
Sortino = (R_portfolio - R_target) / Downside_Deviation

Downside Deviation = sqrt(Σ(min(Ri - R_target, 0))² / n)

# Only penalizes downside volatility (upside volatility is good!)

Example:
Portfolio return: 12%
Target: 5%
Downside dev: 8%  (vs 15% total volatility)
Sortino = (12% - 5%) / 8% = 0.875

# Sortino > Sharpe when upside volatility dominates
```

**Beta (Market Sensitivity):**
```
β = Cov(R_portfolio, R_market) / Var(R_market)

Example:
Portfolio std: 20%
Market std: 15%
Correlation: 0.9
β = 0.9 × (20% / 15%) = 1.2

Interpretation:
- β = 1: Moves with market
- β > 1: More volatile than market (1.2 = 20% more volatile)
- β < 1: Less volatile (defensive)
- β < 0: Inverse (hedge fund)
```

**Tracking Error:**
```
TE = σ(R_portfolio - R_benchmark)

Example:
Portfolio returns: [10%, 12%, 8%, 15%]
Benchmark returns: [9%, 11%, 9%, 14%]
Differences: [+1%, +1%, -1%, +1%]
Std dev of differences: 1.15%

Tracking Error = 1.15%

Interpretation:
- Low TE (< 2%): Index-hugging
- Medium TE (2-5%): Active management
- High TE (> 5%): Highly active/concentrated
```

---

## 7. Macro Regime Detection

### 7.1 Regime Framework

**4-Regime Model:**

File: `backend/app/services/macro.py`

Based on two dimensions:
1. **Growth:** Expanding vs Contracting
2. **Inflation:** Rising vs Falling

```
                Inflation Falling        Inflation Rising
               ┌──────────────────┬──────────────────┐
   Growth Up   │  GOLDILOCKS      │   REFLATION      │
               │  (Best)          │   (Commodity boom)│
               ├──────────────────┼──────────────────┤
   Growth Down │  DEFLATION       │   STAGFLATION    │
               │  (Recession)     │   (Worst)        │
               └──────────────────┴──────────────────┘
```

**Regime Characteristics:**

**1. Goldilocks (Growth ↑, Inflation ↓):**
- **Economic Conditions:** Strong growth, contained inflation
- **Central Bank:** Neutral (no need to tighten)
- **Best For:** Equities (P/E expansion), corporate bonds
- **Examples:** 1995-2000 (tech boom), 2017-2018
- **Asset Allocation:** 70% equity, 20% IG bonds, 10% cash

**2. Reflation (Growth ↑, Inflation ↑):**
- **Economic Conditions:** Economy overheating
- **Central Bank:** Tightening (raising rates)
- **Best For:** Commodities, TIPS, value stocks, banks
- **Examples:** 2004-2006, 2021-2022
- **Asset Allocation:** 50% equity (cyclicals), 30% commodities, 20% TIPS

**3. Stagflation (Growth ↓, Inflation ↑):**
- **Economic Conditions:** Recession + inflation (worst combo)
- **Central Bank:** Trapped (can't ease without worsening inflation)
- **Best For:** Cash, gold, TIPS
- **Examples:** 1970s oil crisis
- **Asset Allocation:** 60% cash/TIPS, 30% gold/commodities, 10% defensive equity

**4. Deflation (Growth ↓, Inflation ↓):**
- **Economic Conditions:** Recession, falling prices
- **Central Bank:** Easing aggressively (cutting rates, QE)
- **Best For:** Treasuries (flight to quality), USD, defensive stocks
- **Examples:** 2008-2009, 2020 COVID crash
- **Asset Allocation:** 50% treasuries, 30% cash/USD, 20% defensive equity

---

### 7.2 Regime Indicators

**Key Indicators & Thresholds:**

File: `backend/app/services/macro.py:94-144`

```python
CORE_INDICATORS = {
    "T10Y2Y": "10Y-2Y Treasury yield spread",   # Growth signal
    "CPIAUCSL": "Consumer Price Index",          # Inflation
    "UNRATE": "Unemployment rate",               # Labor market
    "BAA10Y": "Corporate spread",                # Risk appetite
}

# Regime detection logic:
# Growth signal: Yield curve (T10Y2Y)
#   > 0.5%: Growth expanding (inverted = recession ahead)
#   < 0: Flat/inverted curve (recession)

# Inflation signal: CPI YoY change
#   > 3%: High inflation
#   < 2%: Low inflation (Fed target)

# Risk signal: Credit spreads (BAA10Y)
#   > 2.5%: Wide spreads (recession fears)
#   < 1.5%: Tight spreads (risk-on)
```

**Yield Curve as Leading Indicator:**
```
10Y-2Y Spread     Meaning              Probability of Recession (12mo)
> 1.5%            Steep curve          < 10%
0.5% to 1.5%      Normal               ~15%
0% to 0.5%        Flattening           ~30%
-0.5% to 0%       Inverted             ~50%
< -0.5%           Deep inversion       > 70%

Historical: Every recession preceded by inverted curve (6-18 months lead)
```

**CPI as Inflation Gauge:**
```
CPI YoY Change    Regime              Fed Response
< 1%              Deflation risk      Dovish (cut rates)
1-2%              Target zone         Neutral
2-3%              Moderate            Watch closely
3-4%              Elevated            Start tightening
> 4%              High inflation      Aggressive hikes

Example: 2022 CPI hit 9% → Fed hiked 425bp in 12 months
```

**Credit Spreads as Risk Barometer:**
```
BAA-10Y Spread    Market Sentiment    Regime Signal
< 1.5%            Extreme risk-on     Bubble risk
1.5-2.5%          Normal              Healthy
2.5-3.5%          Caution             Slowdown
> 3.5%            Risk-off            Crisis

Example: 2008 crisis spreads hit 5.5% (credit freeze)
```

**Unemployment Rate:**
```
Change in UNRATE  Signal              Implication
Rising sharply    Recession           Cuts coming
Rising slowly     Slowdown            Monitor
Falling           Expansion           Tighten risk
At lows (<4%)     Tight labor         Inflation risk

Sahm Rule: If 3mo avg rises 0.5pp above 12mo low → recession
```

---

### 7.3 Regime-Based Positioning

**Asset Performance by Regime (Historical):**

```
Asset Class       Goldilocks  Reflation   Stagflation  Deflation
────────────────────────────────────────────────────────────────
Equities          +18%        +8%         -12%         -25%
  - Growth        +25%        +5%         -18%         -15%
  - Value         +12%        +12%        -8%          -30%
  - Cyclicals     +20%        +15%        -20%         -35%
  - Defensives    +10%        +3%         -2%          -5%

Bonds             +5%         -3%         +2%          +15%
  - Treasuries    +4%         -5%         +3%          +20%
  - IG Corporate  +6%         -2%         +1%          +8%
  - HY Corporate  +8%         +2%         -8%          -15%
  - TIPS          +3%         +5%         +8%          -5%

Commodities       -2%         +15%        +12%         -20%
  - Energy        -5%         +20%        +18%         -30%
  - Gold          -3%         +8%         +15%         +5%
  - Agriculture   +2%         +12%        +10%         -15%

Cash (T-Bills)    +2%         +4%         +6%          +1%
USD               -1%         -3%         +5%          +8%
────────────────────────────────────────────────────────────────
```

**Tactical Allocation Rules:**

**Goldilocks → Reflation Transition:**
```
Action: Rotate from growth to value/cyclicals
- Reduce: Growth tech, long-duration bonds
- Increase: Banks, energy, commodities, TIPS
- Reasoning: Rising rates hurt growth multiples, inflation benefits real assets
```

**Reflation → Stagflation Transition:**
```
Action: Defensive posture
- Reduce: Equities (especially cyclicals), corporate bonds
- Increase: Cash, gold, TIPS, defensive stocks (utilities, consumer staples)
- Reasoning: Recession + inflation = worst combo, capital preservation mode
```

**Stagflation → Deflation Transition:**
```
Action: Flight to quality
- Reduce: Commodities, gold
- Increase: Treasuries, USD, high-quality bonds
- Reasoning: Deflation crushes commodities, treasuries rally on rate cuts
```

**Deflation → Goldilocks Transition:**
```
Action: Risk-on
- Reduce: Cash, treasuries
- Increase: Equities (especially growth), IG bonds
- Reasoning: Recovery begins, QE drives asset prices, growth accelerates
```

**Factor Positioning by Regime:**

File: `backend/app/services/scenarios.py` - Factor betas guide positioning

```
Factor            Goldilocks  Reflation   Stagflation  Deflation
────────────────────────────────────────────────────────────────
Real Rates Beta   Negative OK Negative    Positive     Positive
                  (rates low) (some rise) (avoid rate  (want rate
                               expected)   risk)        sensitivity)

Inflation Beta    Low         High        High         Low
                  (not needed)(ride it)   (hedge it)   (not issue)

Credit Beta       Moderate    Moderate    Low          Negative
                  (accept)    (tight)     (avoid)      (spreads widen)

Equity Beta       High        High        Low          Very Low
                  (1.2-1.3)   (1.0-1.1)   (0.6-0.8)    (0.3-0.5)

USD Beta          Neutral     Negative    Positive     Positive
                  (no view)   (USD weak)  (safe haven) (safe haven)
────────────────────────────────────────────────────────────────
```

**DawsOS Implementation:**
- Regime detection: `backend/app/services/macro.py`
- Factor positioning: `backend/app/services/scenarios.py`
- **UI Status:** Regime shown but not actionable ([FINTECH_UX_ANALYSIS.md](FINTECH_UX_ANALYSIS.md))

---

## 8. Regulatory & Compliance

### 8.1 Tax Reporting Requirements

**IRS Form 1099-B (US):**
- **Purpose:** Report proceeds from broker transactions
- **Required For:** All stock sales (since 2011)
- **Information Reported:**
  - Sale proceeds
  - Cost basis
  - Acquisition date
  - Short-term vs long-term
  - Wash sale adjustments

**Cost Basis Reporting (IRS Reg § 1.6045-1):**
- **Effective:** January 1, 2011
- **Requirement:** Brokers must track and report cost basis
- **Methods:**
  - Default: FIFO
  - Allowed: Average cost (mutual funds), specific lot
  - **Not allowed:** LIFO (for stocks)
- **Covered Securities:** Purchased after effective date in account

**Wash Sale Tracking:**
- **Rule (IRC § 1091):** 30 days before or after sale
- **Broker Responsibility:** Track across all accounts (same taxpayer)
- **Reporting:** Disallowed loss shown on Form 1099-B, code "W"

**Qualified Dividend Reporting (IRC § 1(h)(11)):**
- **Requirements:**
  - Hold stock >60 days during 121-day period (60 days before, 60 after ex-date)
  - Not short position or option-hedged
- **Tax Rate:** 0%, 15%, or 20% (vs ordinary income up to 37%)
- **Reporting:** Form 1099-DIV distinguishes qualified vs ordinary

**DawsOS Compliance Status:**
- ✅ Cost basis tracking in `lots` table
- ❌ Cost basis method selection (UI/DB)
- ❌ Wash sale rule implementation
- ❌ Holding period tracking (qualified dividend determination)
- ❌ Form 1099-B generation

---

### 8.2 Financial Reporting Standards

**GAAP (US Generally Accepted Accounting Principles):**

**ASC 320 - Investments in Debt and Equity Securities:**
- **Trading Securities:** Mark-to-market through P&L (held for sale)
- **Available-for-Sale:** Mark-to-market through OCI (Other Comprehensive Income)
- **Held-to-Maturity:** Amortized cost (not mark-to-market)

**ASC 820 - Fair Value Measurement:**
- **Level 1:** Quoted prices in active markets (stocks, ETFs)
- **Level 2:** Observable inputs (bonds, derivatives)
- **Level 3:** Unobservable inputs (private equity, illiquid assets)

**ASC 815 - Derivatives and Hedging:**
- **Fair Value Hedge:** Hedge recognized asset/liability (mark both to market)
- **Cash Flow Hedge:** Hedge forecasted transaction (effective portion to OCI)
- **Net Investment Hedge:** Hedge FX risk of foreign sub (to OCI)
- **Effectiveness Test:** 80-125% correlation required

**IFRS (International Financial Reporting Standards):**

**IFRS 9 - Financial Instruments:**
- **Amortized Cost:** Hold to collect contractual cash flows (loans, bonds)
- **FVOCI (Fair Value through OCI):** Hold to collect + sell (some bonds)
- **FVPL (Fair Value through P&L):** Trading, derivatives

**Differences from GAAP:**
- IFRS 9 uses "business model" test (not intent-based like GAAP)
- IFRS 9 expected credit loss model (forward-looking) vs GAAP incurred loss

**DawsOS Accounting Model:**
- Appears to follow **Trading Securities** model (mark-to-market)
- All unrealized gains/losses impact portfolio NAV
- Suitable for active investment portfolios
- Not suitable for insurance companies (AFS model) or banks (HTM model)

---

### 8.3 Data Disclosure Requirements

**MiFID II (EU Markets in Financial Instruments Directive):**
- **Requirement:** Disclose data age and source
- **Example:** "Prices as of 2025-11-05 16:00:00 CET, source: Bloomberg"
- **DawsOS Issue:** No data age indicators in UI ([FINTECH_UX_ANALYSIS.md](FINTECH_UX_ANALYSIS.md#issue-9))

**Data Source Attribution:**
- Required to disclose data providers
- Example: "Market data © Financial Modeling Prep"
- **DawsOS Status:** Rights defined in provider configs but not shown in UI

**Performance Presentation Standards (GIPS):**
- **Requirement:** CFA Institute standards for presenting performance
- **Key Rules:**
  - Must use time-weighted returns
  - Must include all actual fee-paying accounts
  - Must show gross and net of fees
  - Must disclose calculation methodology
  - Cannot show back-tested performance without disclaimer

**DawsOS Compliance:**
- ✅ Calculates TWR and MWR
- ❌ No fee tracking (gross vs net)
- ❌ No performance disclaimer text
- ❌ No calculation methodology disclosure

---

## 9. Transaction Processing

### 9.1 Trade Lifecycle

**Order → Execution → Settlement:**

```
Day T-2 (Before Trade):
- Client reviews portfolio, decides to buy 100 AAPL
- Places order: "Buy 100 AAPL @ Market"

Day T (Trade Date):
- 9:30am ET: Market opens
- Order executes: 100 AAPL @ $175.50
- **Ownership transfers** (legal title changes)
- Trade confirmed by broker
- Cost basis established: $175.50/share

Day T+1 (T+1):
- Trade details finalized
- Broker sends confirmation
- (For bonds: Would settle today)

Day T+2 (Settlement Date):
- **Cash debited** from account: $17,550
- **Shares credited** to account
- Lot created in portfolio system
- Dividend entitlement begins (if held through ex-date)
```

**Key Points:**
- **Ownership:** T (trade date) - matters for dividends
- **Cash Movement:** T+2 (settlement) - matters for cash balance
- **Margin:** During T to T+2, position on margin (broker credit)

---

### 9.2 Trade Date vs Settlement Date Accounting

**Accounting Methods:**

**1. Trade Date Accounting (Recommended):**
```
Record transaction on trade date (T)

Example:
Nov 1 (Trade Date): Buy 100 AAPL @ $175.50
- Dr. Investment in AAPL: $17,550
- Cr. Payable to Broker: $17,550

Nov 3 (Settlement Date): Cash settles
- Dr. Payable to Broker: $17,550
- Cr. Cash: $17,550

Result: Position shows in portfolio immediately (correct for P&L)
```

**2. Settlement Date Accounting:**
```
Record transaction on settlement date (T+2)

Nov 3 (Settlement Date):
- Dr. Investment in AAPL: $17,550
- Cr. Cash: $17,550

Problem: Portfolio shows no position for 2 days (incorrect for P&L)
```

**Why Trade Date Matters:**

**Dividend Entitlement:**
```
AAPL declares $0.24 dividend:
- Ex-dividend date: Nov 2
- Record date: Nov 3
- Pay date: Nov 10

Scenario 1: Buy on Nov 1 (before ex-date)
- Trade date: Nov 1
- Settlement: Nov 3
- Result: Entitled to dividend (owned on record date)

Scenario 2: Buy on Nov 2 (ex-date)
- Trade date: Nov 2
- Settlement: Nov 4
- Result: NOT entitled (bought ex-dividend)
```

**P&L Accuracy:**
```
Portfolio NAV should include unsettled trades:

Nov 1: Buy 100 AAPL @ $175.50 (trade date)
Nov 2: AAPL closes at $177.00
Nov 3: Settlement date

Correct NAV (trade date accounting):
- Nov 1 end: 100 × $175.50 = $17,550
- Nov 2 end: 100 × $177.00 = $17,700 (unrealized gain: $150)

Wrong NAV (settlement date accounting):
- Nov 1 end: $0 (trade not recorded!)
- Nov 2 end: $0
- Nov 3: 100 × (current price) = suddenly appears

Trade date accounting gives accurate real-time P&L
```

**DawsOS Implementation:**
- Database: `transactions` table has both `transaction_date` (trade date) and potentially settlement date
- **Assumption:** Uses trade date accounting (standard for portfolios)
- **Missing:** Explicit settlement date tracking

---

## 10. Portfolio Optimization Theory

### 10.1 Modern Portfolio Theory (MPT)

**Efficient Frontier:**

Concept: For every level of risk, there exists a portfolio with maximum return
```
Expected Return (%)
        │
    15% │           ●  (Inefficient: can get more return for same risk)
        │         /│\
    12% │       ●  │ ●  ← Efficient Frontier
        │      /   │  \
    10% │    ●     │   ●
        │   /      │    \
     8% │ ●───────●────●  (Minimum variance portfolio)
        │          │
     5% │          ●  (Inefficient: can get same return with less risk)
        │
        └────────────────── Risk (Std Dev %)
            10%   15%  20%

Key Points:
- Portfolios on the frontier are "efficient"
- Portfolios below are "inefficient" (dominated)
- Rational investors choose from the frontier
```

**Risk-Return Tradeoff:**
```
Portfolio A: 100% Stocks
- Return: 12%
- Risk: 18%
- Sharpe: 0.56

Portfolio B: 60% Stocks, 40% Bonds
- Return: 8%
- Risk: 11%
- Sharpe: 0.55

Portfolio C: 40% Stocks, 60% Bonds
- Return: 6%
- Risk: 8%
- Sharpe: 0.50

Despite lower return, Portfolio B has similar Sharpe (better risk-adjusted)
```

**Diversification Benefits:**

**Correlation & Covariance:**
```
Portfolio Risk:
σ²(P) = w₁²σ₁² + w₂²σ₂² + 2w₁w₂ρ₁₂σ₁σ₂

Where:
- w₁, w₂ = weights
- σ₁, σ₂ = individual volatilities
- ρ₁₂ = correlation (-1 to +1)

Example: 50/50 portfolio of Stock A and Stock B

Scenario 1: Perfect correlation (ρ = 1.0)
- Stock A: σ = 20%
- Stock B: σ = 20%
- Portfolio σ = sqrt(0.5² × 20² + 0.5² × 20² + 2 × 0.5 × 0.5 × 1.0 × 20 × 20)
              = sqrt(100 + 100 + 200) = 20%
→ No diversification benefit

Scenario 2: Zero correlation (ρ = 0)
- Portfolio σ = sqrt(100 + 100 + 0) = 14.1%
→ Diversification reduces risk by 29%

Scenario 3: Negative correlation (ρ = -0.5)
- Portfolio σ = sqrt(100 + 100 - 100) = 10%
→ Diversification reduces risk by 50%
```

**Markowitz Optimization:**
```
Minimize: σ²(P) = w' Σ w

Subject to:
- μ'w = target return
- Σw = 1 (weights sum to 100%)
- w ≥ 0 (no short selling)

Where:
- w = weight vector
- Σ = covariance matrix
- μ = expected returns vector

Solution: Quadratic programming (finds efficient frontier)
```

---

### 10.2 Factor-Based Optimization

**Risk Parity:**

Concept: Equal risk contribution from each asset (not equal weight)
```
Traditional 60/40:
- 60% stocks contribute ~90% of risk (high volatility)
- 40% bonds contribute ~10% of risk (low volatility)

Risk Parity:
- ~30% stocks contribute 50% of risk
- ~70% bonds contribute 50% of risk
- Use leverage on bonds to achieve target return

Formula:
Risk Contribution_i = w_i × β_i × σ_portfolio

Set equal: RC_stocks = RC_bonds
```

**Factor Risk Budgeting:**

Allocate risk across factors (not assets)
```
Target factor exposures:
- Market beta: 50% of risk budget
- Value factor: 20%
- Momentum: 20%
- Quality: 10%

Build portfolio with these factor tilts
```

**Risk-Constrained Optimization:**

Maximize expected return subject to risk limit
```
Maximize: μ'w

Subject to:
- σ²(P) ≤ target risk²
- Σw = 1
- w ≥ 0
- Factor constraints (e.g., |β_i| ≤ 0.3)

Example constraints:
- Portfolio volatility ≤ 15%
- Market beta: 0.8 - 1.2
- Max single position: 10%
- Max sector: 25%
```

**Transaction Cost Considerations:**
```
Turnover penalty:
Cost = Σ|w_new - w_old| × transaction_cost

Example:
Rebalance from 5% AAPL to 8% AAPL in $1M portfolio
- Trade: 3% × $1M = $30,000
- Commission: 0.5bp = $15
- Spread: 0.5bp = $15
- Market impact: 1bp = $30
- Total cost: $60 (0.2bp of portfolio)

High turnover strategies must generate excess return > costs
```

**DawsOS Optimization Status:**
- UI has Optimizer page (placeholder)
- Backend lacks optimization engine
- **Suggested Implementation:**
  - Use `cvxpy` (convex optimization library)
  - Inputs: Expected returns (macro-adjusted), covariance matrix, constraints
  - Output: Optimal weights, expected Sharpe, factor exposures

---

## Cross-References to DawsOS Issues

### Critical Finance Bugs ([FINTECH_UX_ANALYSIS.md](FINTECH_UX_ANALYSIS.md))

1. **P&L Calculation:**
   - Issue: No realized vs unrealized separation
   - Theory: Section 1.2
   - Fix: Separate calculation by lot disposition

2. **Currency Formatting:**
   - Issue: Hardcoded USD
   - Theory: Section 1.3
   - Fix: Dynamic from portfolio.base_currency

3. **Cost Basis Method:**
   - Issue: Not specified
   - Theory: Section 1.1
   - Fix: Add field to portfolios table + UI selector

4. **Attribution:**
   - Issue: Only currency shown
   - Theory: Section 3.3
   - Fix: Implement Brinson-Fachler model

5. **DaR Display:**
   - Issue: Single point, no trending
   - Theory: Section 6.1
   - Fix: Chart dar_history table data

### DawsOS File References

| Concept | File | Lines |
|---------|------|-------|
| Cost basis tracking | `backend/app/services/lots.py` | - |
| Realized P&L | `backend/app/services/transactions.py` | - |
| Corporate actions | `backend/app/services/corporate_actions.py` | 91-599 |
| Factor betas | `backend/app/services/scenarios.py` | 297-379 |
| Scenario analysis | `backend/app/services/scenarios.py` | 381-681 |
| DaR calculation | `backend/app/services/scenarios.py` | 703-937 |
| Macro regimes | `backend/app/services/macro.py` | 94-144 |
| Currency attribution | `backend/app/services/currency_attribution.py` | - |

---

## Recommended Reading

### Books
- **Accounting:** "Financial Statements" by Ittelson
- **Portfolio Theory:** "Active Portfolio Management" by Grinold & Kahn
- **Risk Management:** "The Handbook of Fixed Income Securities" by Fabozzi
- **Factor Investing:** "Your Complete Guide to Factor-Based Investing" by Berkin & Swedroe
- **Macro:** "Principles for Navigating Big Debt Crises" by Ray Dalio

### Regulations
- IRS Publication 550 (Investment Income and Expenses)
- IRS Form 1099-B Instructions (Broker Reporting)
- ASC 320, 815, 820 (GAAP)
- IFRS 9 (Financial Instruments)

### Industry Standards
- GIPS Standards (CFA Institute)
- MiFID II (EU Regulation)

---

**Document Maintenance:**
- Review quarterly for regulatory changes
- Update with new DawsOS features
- Add examples from actual usage
- Cross-reference with code changes

**Last Updated:** 2025-11-05
**Next Review:** 2026-02-05
