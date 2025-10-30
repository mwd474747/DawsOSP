# DawsOS Data Architecture Documentation

Version: 1.0.0  
Date: October 30, 2025  
Status: Authoritative Reference  

## Table of Contents

1. [Overview](#overview)
2. [Database Schema](#database-schema)
3. [Data Dictionary](#data-dictionary)
4. [Entity Relationships](#entity-relationships)
5. [Data Flow Architecture](#data-flow-architecture)
6. [API Data Contracts](#api-data-contracts)
7. [Financial Calculations](#financial-calculations)
8. [Data Transformation Logic](#data-transformation-logic)
9. [Business Rules](#business-rules)
10. [Data Quality & Reconciliation](#data-quality--reconciliation)

---

## Overview

DawsOS is a comprehensive portfolio management platform that combines real-time market data, economic analysis, and AI-powered insights. The architecture is built on:

- **Database**: PostgreSQL with TimescaleDB for time-series data
- **Backend**: FastAPI with async Python
- **Frontend**: Full-stack HTML/JavaScript client
- **Data Sources**: FRED, FMP, Polygon, World Bank, ECB
- **Caching**: In-memory and database-level caching
- **Authentication**: JWT-based with role-based access control (RBAC)

### Core Data Principles

1. **Immutability**: Pricing packs and ledger snapshots are immutable once created
2. **Reproducibility**: Every calculation references a `pricing_pack_id` for point-in-time accuracy
3. **Reconciliation**: All metrics must reconcile to Beancount ledger within ±1 basis point
4. **Provenance**: Every data point tracks its source and timestamp

---

## Database Schema

### Core Tables

#### 1. Users & Authentication
```
users
├── id (UUID, PK)
├── email (TEXT, UNIQUE)
├── password_hash (TEXT)
├── role (TEXT) - VIEWER|USER|MANAGER|ADMIN
├── created_at (TIMESTAMPTZ)
├── updated_at (TIMESTAMPTZ)
├── last_login_at (TIMESTAMPTZ)
└── is_active (BOOLEAN)

audit_log
├── id (UUID, PK)
├── user_id (UUID, FK → users)
├── action (TEXT)
├── resource_type (TEXT)
├── resource_id (TEXT)
├── details (JSONB)
├── timestamp (TIMESTAMPTZ)
├── ip_address (TEXT)
└── user_agent (TEXT)
```

#### 2. Portfolio Management
```
portfolios
├── id (UUID, PK)
├── user_id (UUID, FK → users)
├── name (TEXT)
├── description (TEXT)
├── base_currency (TEXT, DEFAULT 'USD')
├── benchmark_id (TEXT)
├── is_active (BOOLEAN)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

lots (Tax Lot Holdings)
├── id (UUID, PK)
├── portfolio_id (UUID, FK → portfolios)
├── security_id (UUID, FK → securities)
├── symbol (TEXT)
├── acquisition_date (DATE)
├── quantity (NUMERIC)
├── cost_basis (NUMERIC)
├── cost_basis_per_share (NUMERIC)
├── currency (TEXT)
├── is_open (BOOLEAN)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

transactions
├── id (UUID, PK)
├── portfolio_id (UUID, FK → portfolios)
├── transaction_type (TEXT) - BUY|SELL|DIVIDEND|SPLIT|TRANSFER_IN|TRANSFER_OUT|FEE
├── security_id (UUID)
├── symbol (TEXT)
├── transaction_date (DATE)
├── settlement_date (DATE)
├── quantity (NUMERIC)
├── price (NUMERIC)
├── amount (NUMERIC)
├── currency (TEXT)
├── fee (NUMERIC)
├── commission (NUMERIC)
├── lot_id (UUID, FK → lots)
├── narration (TEXT)
├── source (TEXT) - ledger|manual|import
├── ledger_commit_hash (TEXT)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

#### 3. Pricing & Securities
```
pricing_packs (Immutable Snapshots)
├── id (TEXT, PK) - Format: "PP_YYYY-MM-DD"
├── date (DATE)
├── policy (TEXT) - WM4PM_CAD|CLOSE_USD
├── hash (TEXT) - SHA-256 integrity hash
├── superseded_by (TEXT, FK → pricing_packs)
├── sources_json (JSONB) - {"FMP": true, "Polygon": true}
├── status (TEXT) - warming|fresh|error
├── is_fresh (BOOLEAN)
├── prewarm_done (BOOLEAN)
├── reconciliation_passed (BOOLEAN)
├── reconciliation_failed (BOOLEAN)
├── reconciliation_error_bps (NUMERIC)
├── error_message (TEXT)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

securities
├── id (UUID, PK)
├── symbol (TEXT, UNIQUE)
├── name (TEXT)
├── security_type (TEXT) - equity|etf|bond
├── exchange (TEXT)
├── trading_currency (TEXT)
├── dividend_currency (TEXT)
├── domicile_country (TEXT)
├── active (BOOLEAN)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

prices
├── id (UUID, PK)
├── security_id (UUID, FK → securities)
├── pricing_pack_id (TEXT, FK → pricing_packs)
├── asof_date (DATE)
├── close (NUMERIC(20, 8))
├── open (NUMERIC(20, 8))
├── high (NUMERIC(20, 8))
├── low (NUMERIC(20, 8))
├── volume (BIGINT)
├── currency (TEXT)
├── source (TEXT)
├── adjusted_for_splits (BOOLEAN)
├── adjusted_for_dividends (BOOLEAN)
└── created_at (TIMESTAMPTZ)

fx_rates
├── id (UUID, PK)
├── pricing_pack_id (TEXT, FK → pricing_packs)
├── base_ccy (TEXT)
├── quote_ccy (TEXT)
├── asof_ts (TIMESTAMPTZ)
├── rate (NUMERIC(20, 10))
├── source (TEXT)
├── policy (TEXT)
└── created_at (TIMESTAMPTZ)
```

#### 4. Metrics (TimescaleDB Hypertables)
```
portfolio_metrics (Hypertable)
├── portfolio_id (UUID)
├── asof_date (DATE)
├── pricing_pack_id (TEXT, FK → pricing_packs)
├── twr_1d...twr_inception_ann (NUMERIC) - Time-weighted returns
├── mwr_ytd...mwr_inception_ann (NUMERIC) - Money-weighted returns
├── volatility_30d...volatility_1y (NUMERIC)
├── sharpe_30d...sharpe_1y (NUMERIC)
├── max_drawdown_1y, max_drawdown_3y (NUMERIC)
├── current_drawdown (NUMERIC)
├── alpha_1y...alpha_3y_ann (NUMERIC)
├── beta_1y, beta_3y (NUMERIC)
├── tracking_error_1y (NUMERIC)
├── information_ratio_1y (NUMERIC)
├── win_rate_1y (NUMERIC)
├── avg_win, avg_loss (NUMERIC)
├── portfolio_value_base (NUMERIC)
├── portfolio_value_local (NUMERIC)
├── cash_balance (NUMERIC)
├── base_currency (TEXT)
├── benchmark_id (TEXT)
├── reconciliation_error_bps (NUMERIC)
└── created_at (TIMESTAMPTZ)

currency_attribution (Hypertable)
├── portfolio_id (UUID)
├── asof_date (DATE)
├── pricing_pack_id (TEXT)
├── local_return (NUMERIC)
├── fx_return (NUMERIC)
├── interaction_return (NUMERIC)
├── total_return (NUMERIC)
├── base_return_actual (NUMERIC)
├── error_bps (NUMERIC)
├── attribution_by_currency (JSONB)
├── base_currency (TEXT)
└── created_at (TIMESTAMPTZ)

factor_exposures (Hypertable)
├── portfolio_id (UUID)
├── asof_date (DATE)
├── pricing_pack_id (TEXT)
├── beta_real_rate (NUMERIC)
├── beta_inflation (NUMERIC)
├── beta_credit (NUMERIC)
├── beta_fx (NUMERIC)
├── beta_market (NUMERIC)
├── beta_size (NUMERIC)
├── beta_value (NUMERIC)
├── beta_momentum (NUMERIC)
├── var_factor (NUMERIC)
├── var_idiosyncratic (NUMERIC)
├── r_squared (NUMERIC)
├── factor_contributions (JSONB)
├── estimation_window_days (INTEGER)
├── benchmark_id (TEXT)
└── created_at (TIMESTAMPTZ)
```

#### 5. Macro Economic Data
```
macro_indicators
├── id (UUID, PK)
├── indicator_id (TEXT) - FRED series ID
├── indicator_name (TEXT)
├── date (DATE)
├── value (NUMERIC)
├── units (TEXT)
├── frequency (TEXT) - Daily|Monthly|Quarterly|Annual
├── source (TEXT)
├── last_updated (TIMESTAMPTZ)
└── created_at (TIMESTAMPTZ)

regime_history
├── id (UUID, PK)
├── date (DATE, UNIQUE)
├── regime (TEXT) - EARLY_EXPANSION|MID_EXPANSION|LATE_EXPANSION|EARLY_CONTRACTION|DEEP_CONTRACTION
├── confidence (NUMERIC) - 0-1
├── indicators_json (JSONB)
├── zscores_json (JSONB)
├── regime_scores_json (JSONB)
└── created_at (TIMESTAMPTZ)

cycle_phases
├── id (UUID, PK)
├── cycle_type (TEXT) - STDC|LTDC|EMPIRE
├── date (DATE)
├── phase (TEXT)
├── phase_number (INT)
├── composite_score (NUMERIC)
├── indicators_json (JSONB)
└── created_at (TIMESTAMPTZ)
```

#### 6. Alerts & Notifications
```
alerts
├── id (UUID, PK)
├── user_id (UUID)
├── condition_json (JSONB) - {"metric": "twr_ytd", "operator": ">", "threshold": 0.10}
├── notify_email (BOOLEAN)
├── notify_inapp (BOOLEAN)
├── cooldown_hours (INT)
├── last_fired_at (TIMESTAMPTZ)
├── is_active (BOOLEAN)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

notifications
├── id (UUID, PK)
├── user_id (UUID)
├── alert_id (UUID, FK → alerts)
├── message (TEXT)
├── delivered_at (TIMESTAMPTZ)
├── read_at (TIMESTAMPTZ)
└── created_at (TIMESTAMPTZ)

alert_deliveries
├── id (UUID, PK)
├── alert_id (VARCHAR)
├── content_hash (VARCHAR) - MD5 for deduplication
├── delivery_methods (JSONB)
└── delivered_at (TIMESTAMPTZ)

alert_dlq (Dead Letter Queue)
├── id (UUID, PK)
├── alert_id (VARCHAR)
├── alert_data (JSONB)
├── error_message (TEXT)
├── retry_count (INTEGER)
├── created_at (TIMESTAMPTZ)
└── last_retry_at (TIMESTAMPTZ)
```

#### 7. Risk & Scenarios
```
scenario_shocks
├── id (UUID, PK)
├── shock_type (TEXT, UNIQUE)
├── shock_name (TEXT)
├── shock_description (TEXT)
├── real_rates_bps (NUMERIC)
├── inflation_bps (NUMERIC)
├── credit_spread_bps (NUMERIC)
├── usd_pct (NUMERIC)
├── equity_pct (NUMERIC)
├── commodity_pct (NUMERIC)
├── volatility_pct (NUMERIC)
├── is_custom (BOOLEAN)
├── created_by (UUID)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

position_factor_betas
├── id (UUID, PK)
├── portfolio_id (UUID, FK → portfolios)
├── symbol (TEXT)
├── security_id (UUID)
├── asof_date (DATE)
├── real_rate_beta (NUMERIC)
├── inflation_beta (NUMERIC)
├── credit_beta (NUMERIC)
├── usd_beta (NUMERIC)
├── equity_beta (NUMERIC)
├── commodity_beta (NUMERIC)
├── volatility_beta (NUMERIC)
├── methodology (TEXT)
├── r_squared (NUMERIC)
└── created_at (TIMESTAMPTZ)

dar_history (Drawdown at Risk)
├── id (UUID, PK)
├── portfolio_id (UUID, FK → portfolios)
├── user_id (UUID)
├── asof_date (DATE)
├── regime (TEXT)
├── confidence (NUMERIC)
├── horizon_days (INT)
├── num_simulations (INT)
├── dar (NUMERIC)
├── dar_pct (NUMERIC)
├── mean_drawdown (NUMERIC)
├── median_drawdown (NUMERIC)
├── max_drawdown (NUMERIC)
├── current_nav (NUMERIC)
├── pricing_pack_id (TEXT)
└── created_at (TIMESTAMPTZ)
```

#### 8. Ledger Integration
```
ledger_snapshots
├── id (UUID, PK)
├── commit_hash (TEXT, UNIQUE)
├── repository_url (TEXT)
├── branch (TEXT)
├── parsed_at (TIMESTAMPTZ)
├── transaction_count (INT)
├── account_count (INT)
├── earliest_date (DATE)
├── latest_date (DATE)
├── file_hash (TEXT)
├── file_paths (TEXT[])
├── status (TEXT) - parsing|parsed|failed|superseded
├── error_message (TEXT)
├── superseded_by (UUID, FK → ledger_snapshots)
├── superseded_at (TIMESTAMPTZ)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

ledger_transactions
├── id (UUID, PK)
├── ledger_snapshot_id (UUID, FK → ledger_snapshots)
├── transaction_date (DATE)
├── transaction_index (INT)
├── narration (TEXT)
├── payee (TEXT)
├── tags (TEXT[])
├── links (TEXT[])
├── account (TEXT)
├── commodity (TEXT)
├── quantity (NUMERIC)
├── price (NUMERIC)
├── price_commodity (TEXT)
├── cost (NUMERIC)
├── cost_commodity (TEXT)
├── metadata (JSONB)
├── transaction_type (TEXT)
└── created_at (TIMESTAMPTZ)

reconciliation_results
├── id (UUID, PK)
├── portfolio_id (UUID, FK → portfolios)
├── asof_date (DATE)
├── ledger_commit_hash (TEXT)
├── ledger_snapshot_id (UUID, FK → ledger_snapshots)
├── pricing_pack_id (TEXT)
├── ledger_nav (NUMERIC)
├── db_nav (NUMERIC)
├── difference (NUMERIC)
├── error_bp (NUMERIC)
├── status (TEXT) - pass|fail|warning
├── tolerance_bp (NUMERIC)
├── ledger_position_count (INT)
├── db_position_count (INT)
├── missing_in_db (TEXT[])
├── missing_in_ledger (TEXT[])
├── quantity_mismatches (JSONB)
├── error_message (TEXT)
├── diagnostics (JSONB)
├── reconciled_at (TIMESTAMPTZ)
├── reconciliation_duration_ms (INT)
└── created_at (TIMESTAMPTZ)
```

---

## Data Dictionary

### Financial Metrics Definitions

| Field | Type | Definition | Calculation |
|-------|------|------------|------------|
| twr_1d | NUMERIC(12,8) | Daily time-weighted return | (End Value / Start Value) - 1, cash-flow adjusted |
| twr_mtd | NUMERIC(12,8) | Month-to-date TWR | Geometric linking of daily TWRs from month start |
| twr_qtd | NUMERIC(12,8) | Quarter-to-date TWR | Geometric linking of daily TWRs from quarter start |
| twr_ytd | NUMERIC(12,8) | Year-to-date TWR | Geometric linking of daily TWRs from year start |
| twr_1y | NUMERIC(12,8) | 1-year TWR | Geometric linking of 252 trading days |
| twr_3y_ann | NUMERIC(12,8) | 3-year annualized TWR | (Cumulative 3Y return)^(1/3) - 1 |
| twr_5y_ann | NUMERIC(12,8) | 5-year annualized TWR | (Cumulative 5Y return)^(1/5) - 1 |
| twr_inception_ann | NUMERIC(12,8) | Since inception annualized TWR | (Total return)^(365/days) - 1 |
| mwr_ytd | NUMERIC(12,8) | YTD money-weighted return (IRR) | Internal Rate of Return including cash flows |
| volatility_30d | NUMERIC(12,8) | 30-day rolling volatility | Std Dev of daily returns × √252 |
| sharpe_30d | NUMERIC(12,8) | 30-day Sharpe ratio | (Return - Risk Free Rate) / Volatility |
| max_drawdown_1y | NUMERIC(12,8) | Maximum peak-to-trough decline | Max[(Peak - Trough) / Peak] over period |
| alpha_1y | NUMERIC(12,8) | 1-year alpha vs benchmark | Portfolio Return - (Beta × Benchmark Return) |
| beta_1y | NUMERIC(12,8) | 1-year beta vs benchmark | Cov(Portfolio, Benchmark) / Var(Benchmark) |
| tracking_error_1y | NUMERIC(12,8) | Volatility of excess returns | Std Dev(Portfolio Return - Benchmark Return) |
| information_ratio_1y | NUMERIC(12,8) | Risk-adjusted excess return | Alpha / Tracking Error |
| win_rate_1y | NUMERIC(5,4) | Percentage of profitable periods | Count(Positive Days) / Total Days |

### Currency Attribution Components

| Field | Type | Definition | Formula |
|-------|------|------------|---------|
| local_return | NUMERIC(12,8) | Return in security's local currency | (P1 - P0) / P0 |
| fx_return | NUMERIC(12,8) | FX rate change impact | (FX1 - FX0) / FX0 |
| interaction_return | NUMERIC(12,8) | Cross-term effect | local_return × fx_return |
| total_return | NUMERIC(12,8) | Total return in base currency | r_local + r_fx + (r_local × r_fx) |
| error_bps | NUMERIC(10,4) | Attribution error | \|computed - actual\| in basis points |

### Regime Classification

| Regime | Definition | Key Indicators |
|--------|------------|----------------|
| EARLY_EXPANSION | Recovery phase | Yield curve steep (+), unemployment falling (-), inflation low |
| MID_EXPANSION | Growth phase | Yield curve positive, unemployment low, inflation rising |
| LATE_EXPANSION | Overheating phase | Yield curve flattening, unemployment bottoming, inflation high |
| EARLY_CONTRACTION | Initial slowdown | Yield curve inverted, unemployment rising, GDP slowing |
| DEEP_CONTRACTION | Recession phase | Yield curve deeply inverted, unemployment high, GDP negative |

---

## Entity Relationships

```
┌──────────────┐
│    users     │
└──────┬───────┘
       │ 1:N
       ▼
┌──────────────┐     1:N      ┌──────────────┐
│  portfolios  │◄──────────────│     lots     │
└──────┬───────┘               └──────────────┘
       │ 1:N                          │ 1:N
       ▼                              ▼
┌──────────────┐               ┌──────────────┐
│ transactions │               │  securities  │
└──────────────┘               └──────┬───────┘
                                      │ 1:N
                               ┌──────┴───────┐
                               │              │
                        ┌──────▼──────┐ ┌────▼─────┐
                        │   prices    │ │ fx_rates │
                        └─────────────┘ └──────────┘
                               │              │
                               └──────┬───────┘
                                      │ N:1
                               ┌──────▼──────┐
                               │pricing_packs│
                               └─────────────┘

Portfolio Metrics Relationships:
┌──────────────┐
│  portfolios  │
└──────┬───────┘
       │ 1:N
       ├────────────────────────────────┐
       │                                │
┌──────▼──────────┐          ┌─────────▼───────────┐
│portfolio_metrics│          │currency_attribution │
└─────────────────┘          └─────────────────────┘
       │                                │
       └────────────┬───────────────────┘
                    │ N:1
            ┌───────▼────────┐
            │ pricing_packs  │
            └────────────────┘

Ledger Integration:
┌──────────────────┐
│ ledger_snapshots │
└────────┬─────────┘
         │ 1:N
┌────────▼─────────────┐
│ ledger_transactions  │
└──────────────────────┘
         │
         │ reconciles with
         ▼
┌──────────────────┐
│   transactions   │
└──────────────────┘
```

---

## Data Flow Architecture

### 1. Market Data Ingestion Flow
```
External APIs → Pricing Pack Builder → Database Storage → Portfolio Valuation
     │                    │                   │                    │
     ├─ FRED API         ├─ Validate        ├─ pricing_packs    ├─ NAV calc
     ├─ FMP API          ├─ Hash            ├─ prices           ├─ Returns
     ├─ Polygon API      ├─ Immutable      ├─ fx_rates         └─ Risk metrics
     └─ World Bank       └─ Status=fresh    └─ securities
```

### 2. Portfolio Calculation Flow
```
User Request → API Endpoint → Service Layer → Database → Response
      │             │              │            │           │
      ├─ Auth      ├─ Validate   ├─ Business  ├─ Query   ├─ JSON
      ├─ Portfolio ├─ Pack ID    ├─ TWR calc  ├─ Metrics ├─ Cache
      └─ Date      └─ Fresh?     └─ Risk calc └─ Prices  └─ Client
```

### 3. Alert Processing Flow
```
Condition Check → Evaluation → Delivery → Tracking
       │             │            │          │
       ├─ Metrics   ├─ Threshold ├─ Email   ├─ alert_deliveries
       ├─ Schedule  ├─ Cooldown  ├─ In-app  ├─ notifications
       └─ Real-time └─ Fire?     └─ DLQ     └─ Deduplication
```

### 4. Reconciliation Flow
```
Ledger (Git) → Parser → Database → Comparison → Result
      │           │         │           │          │
      ├─ Beancount├─ Extract├─ NAV calc├─ Diff   ├─ Pass/Fail
      ├─ Commit   ├─ Store  ├─ Holdings├─ ±1bp?  ├─ Store
      └─ Immutable└─ Hash   └─ Prices  └─ Error  └─ Alert
```

---

## API Data Contracts

### Authentication Endpoints

#### POST /api/auth/login
**Request:**
```python
class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=100)
```

**Response:**
```python
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
```

### Portfolio Endpoints

#### GET /api/portfolio
**Query Parameters:**
- `pack_id` (optional): Pricing pack identifier
- `asof_date` (optional): As-of date for historical data

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_value": 1000000.00,
      "unrealized_pnl": 85000.00,
      "unrealized_pnl_pct": 8.5,
      "day_return": 0.12,
      "ytd_return": 8.5
    },
    "holdings": [...],
    "metrics": {
      "portfolio_beta": 0.85,
      "sharpe_ratio": 1.2,
      "var_95": -15000,
      "max_drawdown": -12.5
    }
  }
}
```

#### GET /api/holdings
**Response:**
```json
{
  "success": true,
  "data": {
    "holdings": [
      {
        "symbol": "AAPL",
        "quantity": 100,
        "market_value": 15000,
        "cost_basis": 14000,
        "unrealized_pnl": 1000,
        "unrealized_pnl_pct": 7.14,
        "weight": 0.15
      }
    ]
  }
}
```

#### GET /api/transactions
**Query Parameters:**
- `start_date` (optional)
- `end_date` (optional)
- `type` (optional): BUY|SELL|DIVIDEND

**Response:** List of transaction records

### Alert Endpoints

#### POST /api/alerts
**Request:**
```python
class AlertConfig(BaseModel):
    type: AlertType  # price|portfolio|risk|macro
    symbol: Optional[str]
    threshold: float
    condition: AlertCondition  # above|below|change
    notification_channel: str = "email"
```

#### DELETE /api/alerts/{alert_id}
**Response:** Success confirmation

### Analytics Endpoints

#### POST /execute
**Request:**
```python
class ExecuteRequest(BaseModel):
    pattern: str  # Pattern name
    inputs: Dict[str, Any]
    require_fresh: bool = False
```

#### GET /api/macro
**Response:** Macro regime data with indicators

#### POST /api/optimize
**Request:**
```python
class OptimizationRequest(BaseModel):
    target_return: Optional[float]
    max_risk: Optional[float]
    constraints: Dict[str, Any]
```

#### POST /api/scenario
**Request:**
```json
{
  "scenario_type": "market_crash",
  "severity": "moderate"
}
```

**Response:**
```json
{
  "scenario_impact": -150000,
  "impact_percentage": -15,
  "var_95": -200000,
  "cvar_95": -250000,
  "hedge_suggestions": [...]
}
```

---

## Financial Calculations

### 1. Time-Weighted Return (TWR)
```python
# Daily TWR (cash-flow adjusted)
twr_daily = (end_value - cash_flows) / start_value - 1

# Period TWR (geometric linking)
twr_period = ∏(1 + twr_daily[i]) - 1

# Annualized TWR
twr_annual = (1 + twr_cumulative)^(365/days) - 1
```

### 2. Money-Weighted Return (MWR/IRR)
Solves for r in:
```
0 = CF₀ + CF₁/(1+r) + CF₂/(1+r)² + ... + (CFₙ + V)/(1+r)ⁿ
```
Where:
- CF = Cash flows (negative for investments, positive for withdrawals)
- V = Ending value
- r = IRR/MWR

### 3. Volatility
```python
# Daily returns standard deviation
daily_returns = [r1, r2, ..., rn]
daily_vol = std_dev(daily_returns)

# Annualized volatility
annual_vol = daily_vol × √252
```

### 4. Sharpe Ratio
```python
sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
```

### 5. Maximum Drawdown
```python
# For each point in time
peak = max(values[0:i])
drawdown[i] = (values[i] - peak) / peak
max_drawdown = min(drawdown)  # Most negative value
```

### 6. Value at Risk (VaR) - 95% Confidence
```python
# Historical VaR
sorted_returns = sort(daily_returns)
var_95 = percentile(sorted_returns, 5)  # 5th percentile

# Parametric VaR
var_95 = mean - 1.645 × std_dev
```

### 7. Currency Attribution
```python
# Decomposition formula
r_base = r_local + r_fx + (r_local × r_fx)

Where:
r_local = (P1_local - P0_local) / P0_local
r_fx = (FX1 - FX0) / FX0
interaction = r_local × r_fx
```

### 8. Factor Exposures (Regression-based)
```python
# Multi-factor model
r_portfolio = α + β₁×F₁ + β₂×F₂ + ... + ε

Where:
F₁ = real_rates, F₂ = inflation, F₃ = credit_spread
F₄ = usd_index, F₅ = equity_risk_premium
```

### 9. Drawdown at Risk (DaR)
```python
# Monte Carlo simulation
for i in range(10000):
    path = simulate_returns(regime, horizon_days)
    drawdown[i] = max_drawdown(path)

dar_95 = percentile(drawdown, 95)
```

---

## Data Transformation Logic

### 1. Pricing Pack Construction
```
1. Trigger: Daily at 4:30 PM ET
2. Fetch prices from APIs
3. Apply corporate actions (splits/dividends)
4. Fetch FX rates (WM 4PM fixing)
5. Calculate SHA-256 hash
6. Store with status='warming'
7. Run pre-warm calculations
8. Set status='fresh', is_fresh=true
```

### 2. Portfolio Metrics Calculation
```
1. Wait for pricing_pack.is_fresh = true
2. Fetch holdings and transactions
3. Calculate daily TWR
4. Link historical TWRs for period returns
5. Calculate volatility from return series
6. Compute Sharpe ratio
7. Calculate drawdown metrics
8. Store in portfolio_metrics hypertable
```

### 3. Regime Detection
```
1. Fetch FRED indicators (T10Y2Y, UNRATE, CPI, etc.)
2. Calculate 252-day rolling z-scores
3. Apply regime scoring rules:
   - EARLY_EXPANSION: z_yield > 0.5, z_unemployment < -0.5
   - MID_EXPANSION: z_yield > 0, z_unemployment < 0
   - LATE_EXPANSION: z_yield < 0, z_unemployment < -0.5
   - EARLY_CONTRACTION: z_yield < -0.5, z_unemployment > 0
   - DEEP_CONTRACTION: z_yield < -1, z_unemployment > 1
4. Calculate confidence = max_score - second_score
5. Store in regime_history
```

### 4. Alert Evaluation
```
1. Check alert conditions against latest metrics
2. Verify cooldown period (last_fired_at)
3. Calculate content_hash for deduplication
4. Check alert_deliveries for duplicates
5. If unique and conditions met:
   - Create notification
   - Send via channels (email/in-app)
   - Update last_fired_at
6. On failure: Insert to alert_dlq
```

---

## Business Rules

### Portfolio Management Rules

1. **Position Concentration**: Maximum 30% in single position
2. **Diversification**: Minimum 5 positions for diversified status
3. **Base Currency**: All portfolios have defined base currency (default USD)
4. **Tax Lots**: FIFO method for lot selection on sells

### Pricing Rules

1. **Immutability**: Pricing packs cannot be modified after creation
2. **Supersession**: Restatements create new packs with superseded_by link
3. **Freshness Gate**: Calculations blocked until is_fresh = true
4. **Policy**: WM 4PM London fixing for FX rates

### Risk Rules

1. **VaR Confidence**: 95% confidence level, 1-day horizon
2. **DaR Simulations**: Minimum 10,000 Monte Carlo paths
3. **Max Risk Score**: Capped at 1.0
4. **Sharpe Bounds**: [-2.0, 3.0] for display

### Alert Rules

1. **Cooldown**: Default 24 hours between notifications
2. **Deduplication**: MD5 content hash prevents duplicates
3. **Retry Limit**: Maximum 5 retries for failed deliveries
4. **DLQ Retention**: 30 days for failed alerts

### Reconciliation Rules

1. **Tolerance**: ±1 basis point (0.01%)
2. **Frequency**: Nightly reconciliation job
3. **Failure Action**: Alert and prevent downstream calculations
4. **Source of Truth**: Beancount ledger is authoritative

---

## Data Quality & Reconciliation

### Data Quality Checks

1. **Completeness**
   - All required fields populated
   - No gaps in time-series data
   - All securities have prices in pricing pack

2. **Consistency**
   - Currency codes follow ISO 4217
   - Transaction types from defined enum
   - Dates within reasonable bounds

3. **Accuracy**
   - Returns calculation matches ledger ±1bp
   - Attribution components sum to total
   - Factor exposures R² > 0.7 for equity portfolios

4. **Timeliness**
   - Pricing packs created by 5 PM ET daily
   - Metrics calculated within 30 minutes
   - Alerts evaluated within 5 minutes

### Reconciliation Process

```python
# Nightly reconciliation job
async def reconcile_portfolio(portfolio_id, date):
    # 1. Get ledger NAV
    ledger_nav = await compute_ledger_nav(portfolio_id, date)
    
    # 2. Get database NAV
    db_nav = await compute_db_nav(portfolio_id, date)
    
    # 3. Calculate difference
    difference = ledger_nav - db_nav
    error_bps = abs(difference / ledger_nav * 10000)
    
    # 4. Check tolerance
    if error_bps <= 1.0:
        status = 'pass'
    else:
        status = 'fail'
        await send_reconciliation_alert(portfolio_id, error_bps)
    
    # 5. Store result
    await store_reconciliation_result(...)
```

### Data Lineage

Every calculation maintains provenance:
- `pricing_pack_id`: Point-in-time market data
- `ledger_commit_hash`: Ledger state reference  
- `created_at`: Timestamp of calculation
- `source`: Data provider (FRED, FMP, etc.)

---

## Performance Optimization

### Database Optimizations

1. **Hypertables**: TimescaleDB for metrics storage
2. **Compression**: Automatic for data > 90 days old
3. **Continuous Aggregates**: Pre-computed rolling metrics
4. **Indexes**: Covering indexes on frequent queries
5. **Partitioning**: Monthly partitions for time-series

### Caching Strategy

1. **FRED Data**: 1-hour cache for macro indicators
2. **Pricing Packs**: Immutable, infinite cache
3. **Portfolio Metrics**: 5-minute cache for current day
4. **API Responses**: 60-second cache for GET requests

### Query Optimization

```sql
-- Use pricing_pack_id for point-in-time queries
SELECT * FROM portfolio_metrics 
WHERE portfolio_id = $1 
  AND pricing_pack_id = $2  -- Specific pack
  AND asof_date >= $3;

-- Use continuous aggregates for rolling metrics
SELECT * FROM portfolio_metrics_30d_rolling
WHERE portfolio_id = $1
  AND day >= CURRENT_DATE - INTERVAL '30 days';
```

---

## Security & Compliance

### Access Control

1. **Authentication**: JWT tokens with 24-hour expiration
2. **Authorization**: Role-based (VIEWER, USER, MANAGER, ADMIN)
3. **Row-Level Security**: PostgreSQL RLS policies
4. **Audit Trail**: All actions logged with user/timestamp

### Data Privacy

1. **Encryption**: TLS for transit, AES-256 at rest
2. **PII Handling**: Emails hashed, no SSN/account numbers
3. **Data Retention**: 7 years for financial records
4. **Right to Delete**: Soft delete with audit preservation

### Compliance

1. **SOC 2**: Audit logging, access controls
2. **MFA**: Two-factor authentication support
3. **Data Residency**: US-based infrastructure
4. **Backup**: Daily backups with 30-day retention

---

## Appendix

### Common Queries

```sql
-- Get portfolio value over time
SELECT 
    asof_date,
    portfolio_value_base,
    twr_1d,
    twr_ytd
FROM portfolio_metrics
WHERE portfolio_id = ?
ORDER BY asof_date DESC
LIMIT 30;

-- Get current holdings with metrics
SELECT 
    l.symbol,
    l.quantity,
    l.cost_basis,
    p.close * l.quantity as market_value,
    (p.close * l.quantity - l.cost_basis) as unrealized_pnl
FROM lots l
JOIN prices p ON l.security_id = p.security_id
WHERE l.portfolio_id = ?
  AND l.is_open = true
  AND p.pricing_pack_id = (
    SELECT id FROM pricing_packs 
    WHERE is_fresh = true 
    ORDER BY date DESC 
    LIMIT 1
  );

-- Check reconciliation status
SELECT 
    portfolio_id,
    asof_date,
    error_bp,
    status,
    ledger_nav,
    db_nav
FROM reconciliation_results
WHERE portfolio_id = ?
ORDER BY asof_date DESC
LIMIT 10;
```

### Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| E001 | Pricing pack not fresh | Wait for pack completion |
| E002 | Reconciliation failed | Check ledger transactions |
| E003 | Insufficient price data | Verify security coverage |
| E004 | FX rate missing | Check currency pairs |
| E005 | Alert delivery failed | Check DLQ and retry |

### Glossary

- **TWR**: Time-Weighted Return - Performance independent of cash flows
- **MWR**: Money-Weighted Return - IRR including cash flow timing
- **DaR**: Drawdown at Risk - Expected drawdown at confidence level
- **Pack**: Immutable pricing snapshot for reproducibility
- **Regime**: Macro economic phase (expansion/contraction)
- **Attribution**: Decomposition of returns into components
- **Basis Point**: 1/100th of 1% (0.01%)
- **Hypertable**: TimescaleDB optimized time-series table

---

*End of Document*

Version Control:
- v1.0.0 (2025-10-30): Initial comprehensive documentation
- Next Review: 2025-11-30