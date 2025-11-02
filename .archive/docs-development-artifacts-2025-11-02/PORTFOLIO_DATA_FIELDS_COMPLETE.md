# Complete Portfolio Data Fields Documentation

## Executive Summary
This document provides a comprehensive listing of all data fields required for portfolio functions in DawsOS, including database schema, data types, formats, and data flows.

---

## 1. User & Authentication Data

### Database Table: `users`
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `id` | UUID | `123e4567-e89b-12d3-a456-426614174000` | Unique user identifier | Yes |
| `email` | TEXT | `user@example.com` | User email (lowercase) | Yes |
| `password_hash` | TEXT | Bcrypt hash | Encrypted password | Yes |
| `role` | TEXT | `VIEWER\|USER\|MANAGER\|ADMIN` | User permissions level | Yes |
| `created_at` | TIMESTAMPTZ | `2025-10-30T00:00:00Z` | Account creation time | Yes |
| `updated_at` | TIMESTAMPTZ | `2025-10-30T00:00:00Z` | Last update time | Yes |
| `last_login_at` | TIMESTAMPTZ | `2025-10-30T00:00:00Z` | Last login timestamp | No |
| `is_active` | BOOLEAN | `true/false` | Account active status | Yes |

### API Request: `LoginRequest`
```json
{
  "email": "user@example.com",    // EmailStr, min=3, max=255
  "password": "secure_password"    // String, min=6, max=100
}
```

### API Response: `LoginResponse`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "role": "USER",
    "permissions": ["read_portfolio", "execute_patterns"]
  }
}
```

---

## 2. Portfolio Core Data

### Database Table: `portfolios`
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `id` | UUID | UUID v4 | Unique portfolio ID | Yes |
| `user_id` | UUID | UUID v4 | Owner user ID | Yes |
| `name` | TEXT | String | Portfolio name | Yes |
| `description` | TEXT | String | Portfolio description | No |
| `base_currency` | TEXT | `USD\|CAD\|EUR` | Base currency (ISO 4217) | Yes |
| `benchmark_id` | TEXT | `SPY\|QQQ` | Benchmark symbol | No |
| `is_active` | BOOLEAN | `true/false` | Active status | Yes |
| `created_at` | TIMESTAMPTZ | ISO 8601 | Creation timestamp | Yes |
| `updated_at` | TIMESTAMPTZ | ISO 8601 | Last update time | Yes |

### Portfolio Response Format
```json
{
  "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Main Portfolio",
  "base_currency": "USD",
  "benchmark": "SPY",
  "total_value": 121145.00,
  "holdings_count": 5,
  "updated_at": "2025-10-30T12:00:00Z"
}
```

---

## 3. Securities & Pricing Data

### Database Table: `securities`
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `id` | UUID | UUID v4 | Unique security ID | Yes |
| `symbol` | TEXT | `AAPL` | Ticker symbol (uppercase) | Yes |
| `name` | TEXT | String | Company/security name | Yes |
| `security_type` | TEXT | `equity\|etf\|bond` | Security classification | Yes |
| `exchange` | TEXT | `NASDAQ\|NYSE` | Exchange code | Yes |
| `trading_currency` | TEXT | `USD\|CAD` | Trading currency | Yes |
| `dividend_currency` | TEXT | `USD\|CAD` | Dividend currency | No |
| `domicile_country` | TEXT | `US\|CA` | Country code (ISO 3166) | No |
| `active` | BOOLEAN | `true/false` | Trading status | Yes |

### Database Table: `prices`
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `id` | UUID | UUID v4 | Unique price record ID | Yes |
| `security_id` | UUID | UUID v4 | Security reference | Yes |
| `pricing_pack_id` | TEXT | `PP_2025-10-30` | Pricing pack reference | Yes |
| `asof_date` | DATE | `2025-10-30` | Price date | Yes |
| `close` | NUMERIC(20,8) | `185.12345678` | Closing price | Yes |
| `open` | NUMERIC(20,8) | `184.00000000` | Opening price | No |
| `high` | NUMERIC(20,8) | `186.50000000` | Daily high | No |
| `low` | NUMERIC(20,8) | `183.25000000` | Daily low | No |
| `volume` | BIGINT | `75000000` | Trading volume | No |
| `currency` | TEXT | `USD` | Price currency | Yes |
| `source` | TEXT | `polygon\|fmp` | Data provider | Yes |

---

## 4. Holdings & Positions

### Database Table: `lots` (Tax Lots)
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `id` | UUID | UUID v4 | Unique lot ID | Yes |
| `portfolio_id` | UUID | UUID v4 | Portfolio reference | Yes |
| `security_id` | UUID | UUID v4 | Security reference | Yes |
| `symbol` | TEXT | `AAPL` | Ticker symbol | Yes |
| `acquisition_date` | DATE | `2024-03-15` | Purchase date | Yes |
| `quantity` | NUMERIC | `100.00000` | Share count | Yes |
| `cost_basis` | NUMERIC | `15000.00` | Total cost | Yes |
| `cost_basis_per_share` | NUMERIC | `150.00` | Per-share cost | Yes |
| `currency` | TEXT | `USD` | Position currency | Yes |
| `is_open` | BOOLEAN | `true/false` | Open position flag | Yes |

### Holdings API Response
```json
{
  "holdings": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc",
      "quantity": 100,
      "average_cost": 150.00,
      "current_price": 185.00,
      "market_value": 18500.00,
      "unrealized_gain": 3500.00,
      "unrealized_gain_pct": 0.2333,
      "currency": "USD",
      "weight": 0.1527,  // 15.27% of portfolio
      "lots": [
        {
          "lot_id": "abc123",
          "acquisition_date": "2024-03-15",
          "quantity": 50,
          "cost_basis": 7500.00
        },
        {
          "lot_id": "def456",
          "acquisition_date": "2024-06-20",
          "quantity": 50,
          "cost_basis": 7500.00
        }
      ]
    }
  ]
}
```

---

## 5. Transactions

### Database Table: `transactions`
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `id` | UUID | UUID v4 | Unique transaction ID | Yes |
| `portfolio_id` | UUID | UUID v4 | Portfolio reference | Yes |
| `transaction_type` | TEXT | `BUY\|SELL\|DIVIDEND\|FEE` | Transaction category | Yes |
| `security_id` | UUID | UUID v4 | Security reference | No |
| `symbol` | TEXT | `AAPL` | Ticker symbol | Yes |
| `transaction_date` | DATE | `2025-10-30` | Trade date | Yes |
| `settlement_date` | DATE | `2025-11-01` | Settlement date (T+2) | No |
| `quantity` | NUMERIC | `10.00000` | Share count | Yes |
| `price` | NUMERIC | `185.50` | Execution price | Yes |
| `amount` | NUMERIC | `1855.00` | Total value | Yes |
| `currency` | TEXT | `USD` | Transaction currency | Yes |
| `fee` | NUMERIC | `1.00` | Transaction fee | No |
| `commission` | NUMERIC | `0.00` | Broker commission | No |
| `lot_id` | UUID | UUID v4 | Tax lot reference | No |
| `narration` | TEXT | String | Transaction notes | No |

### Transaction API Request
```json
{
  "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
  "symbol": "AAPL",
  "trade_type": "buy",
  "qty": 10,
  "price": 185.50,
  "currency": "USD",
  "trade_date": "2025-10-30",
  "fees": 1.00,
  "lot_selection": "fifo",  // fifo|lifo|hifo|specific
  "notes": "Rebalancing trade"
}
```

---

## 6. Performance Metrics

### Database Table: `portfolio_metrics`
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `portfolio_id` | UUID | UUID v4 | Portfolio reference | Yes |
| `asof_date` | DATE | `2025-10-30` | Metric date | Yes |
| `pricing_pack_id` | TEXT | `PP_2025-10-30` | Pricing reference | Yes |
| **Time-Weighted Returns** |
| `twr_1d` | NUMERIC | `0.0125` | 1-day return (1.25%) | No |
| `twr_mtd` | NUMERIC | `0.0450` | Month-to-date (4.5%) | No |
| `twr_ytd` | NUMERIC | `0.1850` | Year-to-date (18.5%) | No |
| `twr_1y` | NUMERIC | `0.2200` | 1-year (22%) | No |
| `twr_3y_ann` | NUMERIC | `0.1500` | 3-year annualized | No |
| **Money-Weighted Returns** |
| `mwr_ytd` | NUMERIC | `0.1750` | YTD IRR | No |
| `mwr_1y` | NUMERIC | `0.2100` | 1-year IRR | No |
| **Risk Metrics** |
| `volatility_30d` | NUMERIC | `0.1800` | 30-day volatility (ann.) | No |
| `sharpe_30d` | NUMERIC | `0.8000` | 30-day Sharpe ratio | No |
| `max_drawdown_1y` | NUMERIC | `-0.0800` | Max drawdown (-8%) | No |
| **Portfolio Values** |
| `portfolio_value_base` | NUMERIC | `121145.00` | Total value (base ccy) | Yes |
| `cash_balance` | NUMERIC | `5000.00` | Cash position | No |

### Metrics API Response
```json
{
  "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
  "asof_date": "2025-10-30",
  "pricing_pack_id": "PP_2025-10-30",
  "returns": {
    "twr_1d": 0.0125,
    "twr_mtd": 0.0450,
    "twr_ytd": 0.1850,
    "twr_1y": 0.2200
  },
  "risk": {
    "volatility_30d": 0.1800,
    "sharpe_30d": 0.8000,
    "max_drawdown_1y": -0.0800,
    "var_95": 2422.90  // 2% of portfolio
  },
  "portfolio_value": 121145.00
}
```

---

## 7. Currency & FX Data

### Database Table: `fx_rates`
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `id` | UUID | UUID v4 | Unique FX record ID | Yes |
| `pricing_pack_id` | TEXT | `PP_2025-10-30` | Pricing pack reference | Yes |
| `base_ccy` | TEXT | `USD` | Base currency | Yes |
| `quote_ccy` | TEXT | `EUR` | Quote currency | Yes |
| `asof_ts` | TIMESTAMPTZ | ISO 8601 | Rate timestamp | Yes |
| `rate` | NUMERIC(20,10) | `1.3456789012` | Exchange rate | Yes |
| `source` | TEXT | `polygon\|ecb` | Data provider | Yes |
| `policy` | TEXT | `WM4PM\|CLOSE` | Rate fixing type | Yes |

### Currency Attribution Response
```json
{
  "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
  "asof_date": "2025-10-30",
  "local_return": 0.0450,    // 4.5% in local currency
  "fx_return": 0.0125,       // 1.25% from FX
  "interaction_return": 0.0006, // 0.06% interaction
  "total_return": 0.0581,    // 5.81% total
  "base_currency": "USD"
}
```

---

## 8. Alerts & Notifications

### Database Table: `alerts`
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `id` | UUID | UUID v4 | Unique alert ID | Yes |
| `user_id` | UUID | UUID v4 | User reference | Yes |
| `portfolio_id` | UUID | UUID v4 | Portfolio reference | No |
| `alert_type` | TEXT | `price\|vol\|macro\|drawdown` | Alert category | Yes |
| `symbol` | TEXT | `AAPL` | Security symbol | No |
| `threshold` | NUMERIC | `100.00` | Trigger value | Yes |
| `condition` | TEXT | `above\|below\|crosses` | Trigger condition | Yes |
| `notification_channel` | TEXT | `email\|sms\|push` | Delivery method | Yes |
| `is_active` | BOOLEAN | `true/false` | Alert status | Yes |
| `last_triggered` | TIMESTAMPTZ | ISO 8601 | Last trigger time | No |
| `cooldown_hours` | INT | `24` | Repeat delay | Yes |

### Alert Configuration Request
```json
{
  "type": "price",
  "symbol": "AAPL",
  "threshold": 200.00,
  "condition": "above",
  "notification_channel": "email"
}
```

---

## 9. Macro Economic Data

### Database Table: `macro_indicators`
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `id` | UUID | UUID v4 | Unique indicator ID | Yes |
| `indicator_code` | TEXT | `UNRATE\|DGS10` | FRED series ID | Yes |
| `asof_date` | DATE | `2025-10-30` | Data date | Yes |
| `value` | NUMERIC | `3.50` | Indicator value | Yes |
| `units` | TEXT | `percent\|index` | Value units | Yes |
| `source` | TEXT | `fred\|ecb\|wb` | Data provider | Yes |
| `frequency` | TEXT | `daily\|monthly` | Update frequency | Yes |

### Macro Regime Response
```json
{
  "asof_date": "2025-10-30",
  "stdc_phase": "late_expansion",
  "ltdc_phase": "deleveraging",
  "empire_phase": "mature",
  "regime": "risk_off",
  "indicators": {
    "unemployment_rate": 3.5,
    "inflation_yoy": 2.8,
    "gdp_growth": 2.1,
    "10y_yield": 4.25
  }
}
```

---

## 10. Pricing Packs (Immutable Snapshots)

### Database Table: `pricing_packs`
| Field | Type | Format | Description | Required |
|-------|------|--------|-------------|----------|
| `id` | TEXT | `PP_2025-10-30` | Pack identifier | Yes |
| `date` | DATE | `2025-10-30` | Pack date | Yes |
| `policy` | TEXT | `WM4PM_CAD\|CLOSE_USD` | Pricing policy | Yes |
| `hash` | TEXT | SHA-256 | Integrity hash | Yes |
| `superseded_by` | TEXT | `PP_2025-10-30_v2` | Replacement pack | No |
| `sources_json` | JSONB | `{"FMP": true}` | Data sources | Yes |
| `status` | TEXT | `warming\|fresh\|error` | Pack status | Yes |
| `is_fresh` | BOOLEAN | `true/false` | Freshness flag | Yes |
| `reconciliation_passed` | BOOLEAN | `true/false` | Reconciliation status | No |
| `reconciliation_error_bps` | NUMERIC | `0.5` | Error in basis points | No |

---

## 11. Data Flow Architecture

### Portfolio Valuation Flow
```
1. User Request → API Endpoint
   ↓
2. Fetch Latest Pricing Pack
   ↓
3. Query Holdings (lots table)
   ↓
4. Join Prices (prices table)
   ↓
5. Apply FX Rates (fx_rates table)
   ↓
6. Calculate Metrics
   ↓
7. Store in portfolio_metrics
   ↓
8. Return Response
```

### Transaction Processing Flow
```
1. Trade Request → Validation
   ↓
2. Check Available Cash/Securities
   ↓
3. Select Tax Lots (FIFO/LIFO)
   ↓
4. Create Transaction Record
   ↓
5. Update Lot Holdings
   ↓
6. Trigger Metric Recalculation
   ↓
7. Send Confirmation
```

### Alert Evaluation Flow
```
1. Nightly Job Trigger (00:35)
   ↓
2. Fetch Active Alerts
   ↓
3. Get Latest Market Data
   ↓
4. Evaluate Conditions
   ↓
5. Check Cooldown Periods
   ↓
6. Send Notifications
   ↓
7. Update Last Triggered
   ↓
8. Handle Failed Deliveries (DLQ)
```

---

## 12. Data Format Requirements

### Numeric Precision
- **Prices**: NUMERIC(20,8) - 8 decimal places
- **FX Rates**: NUMERIC(20,10) - 10 decimal places
- **Quantities**: NUMERIC - Variable precision
- **Percentages**: NUMERIC - Stored as decimals (0.10 = 10%)
- **Money**: NUMERIC - 2 decimal places for display

### Date/Time Formats
- **Dates**: ISO 8601 (`YYYY-MM-DD`)
- **Timestamps**: ISO 8601 with timezone (`YYYY-MM-DDTHH:MM:SSZ`)
- **Timezone**: All times stored in UTC
- **Display**: Convert to user's local timezone

### Currency Codes
- **Format**: ISO 4217 3-letter codes
- **Examples**: `USD`, `EUR`, `GBP`, `CAD`, `JPY`
- **Validation**: Must match supported currencies

### Symbol Format
- **Stocks**: Uppercase (`AAPL`, `MSFT`)
- **ETFs**: Uppercase (`SPY`, `QQQ`)
- **Validation**: 1-10 characters, alphanumeric

---

## 13. Validation Rules

### Portfolio Constraints
- Base currency must be supported (USD, EUR, GBP, CAD)
- Portfolio name: 1-100 characters
- At least one holding required for active portfolio

### Transaction Validation
- Quantity must be positive for BUY, negative for SELL
- Price must be positive
- Trade date cannot be future
- Settlement date typically T+2 for equities

### Alert Validation
- Threshold must be positive
- Cooldown hours: 1-168 (1 hour to 1 week)
- Symbol required for price alerts
- Portfolio required for portfolio-level alerts

### Performance Metrics
- Returns expressed as decimals (-1.0 to unlimited)
- Volatility annualized and positive
- Sharpe ratio can be negative
- Drawdowns expressed as negative percentages

---

## 14. Data Dependencies

### External Data Sources
| Source | Data Type | Update Frequency | Fields Used |
|--------|-----------|------------------|-------------|
| **Polygon.io** | Prices, FX | Real-time/Daily | OHLCV, Volume |
| **FRED** | Economic | Daily/Monthly | Unemployment, GDP, CPI |
| **FMP** | Fundamentals | Daily | Balance Sheet, Income |
| **NewsAPI** | News | Real-time | Headlines, Sentiment |
| **World Bank** | Economic | Quarterly | Global indicators |
| **ECB** | FX Rates | Daily | EUR cross rates |

### Internal Dependencies
- Pricing packs must exist before metrics calculation
- Securities must be defined before transactions
- Users must exist before portfolios
- Portfolios must exist before holdings

---

## 15. Data Reconciliation

### Reconciliation Points
1. **NAV Reconciliation**: Database ↔ Ledger (±1bp tolerance)
2. **Price Validation**: Multiple sources compared
3. **FX Rate Validation**: WM Reuters vs ECB
4. **Transaction Matching**: Trade confirms vs database

### Reconciliation Fields
```json
{
  "reconciliation_id": "recon_2025-10-30",
  "ledger_nav": 121145.00,
  "database_nav": 121144.50,
  "difference": 0.50,
  "error_bps": 0.41,
  "status": "PASS",
  "timestamp": "2025-10-30T00:40:00Z"
}
```

---

## Summary

The DawsOS portfolio management system requires **45+ distinct tables** with **500+ individual data fields** organized across:
- 8 major data domains
- 15+ API endpoints
- 6 external data sources
- Multiple validation and reconciliation layers

All data flows through immutable pricing packs to ensure point-in-time accuracy and reproducible calculations. The system maintains both real-time and historical data with comprehensive audit trails and reconciliation processes.