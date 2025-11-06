# Provider API → Database Mapping

**Created:** 2025-11-05
**Purpose:** Map external provider API responses to DawsOS database schema
**Related:** [provider-api-documentation.md](provider-api-documentation.md), [DATABASE.md](../../DATABASE.md)

---

## Quick Reference

| Provider | API Endpoint | Database Table | Key Fields | Frequency |
|----------|-------------|----------------|-----------|-----------|
| **FMP** | `/v3/quote` | `prices` | close, volume, open, high, low | Daily |
| **FMP** | `/v3/profile` | `securities` | symbol, name, currency, sector, industry | On-demand |
| **FMP** | `/v3/stock_dividend_calendar` | `corporate_actions` | type='DIVIDEND', ex_date, amount, pay_date | Daily ✅ **ACTIVE** |
| **FMP** | `/v3/stock_split_calendar` | `corporate_actions` | type='SPLIT', ex_date, split_ratio | Daily ✅ **ACTIVE** |
| **FRED** | `/series/observations` | `economic_indicators` | series_id, asof_date, value | Daily ✅ **ACTIVE** |
| **Polygon** | `/v2/aggs/ticker` | `prices` | close, open, high, low, volume | Historical backfill ✅ **ACTIVE** |
| **Polygon** | `/v3/reference/dividends` | `corporate_actions` | type='DIVIDEND' | ⚠️ **NOT USED** (methods exist, no callers) |
| **Polygon** | `/v3/reference/splits` | `corporate_actions` | type='SPLIT' | ⚠️ **NOT USED** (methods exist, no callers) |
| **NewsAPI** | `/v2/everything` | (not stored) | Metadata only (dev tier) | On-demand |

---

## FMP → Database Mappings

### 1. FMP Quote → prices table

**API:** `GET /v3/quote/{symbols}`
**Response:**
```json
{
  "symbol": "AAPL",
  "price": 175.43,
  "open": 174.20,
  "dayHigh": 176.20,
  "dayLow": 173.50,
  "volume": 52000000,
  "previousClose": 173.26
}
```

**Database:** `prices`
```sql
INSERT INTO prices (
    pricing_pack_id,     -- From pricing pipeline context
    security_id,         -- Lookup from securities WHERE symbol = 'AAPL'
    asof_date,           -- Pack date
    close,               -- quote.price
    open,                -- quote.open
    high,                -- quote.dayHigh
    low,                 -- quote.dayLow
    volume,              -- quote.volume
    currency,            -- From security.currency
    created_at
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
ON CONFLICT (pricing_pack_id, security_id) DO UPDATE
SET close = EXCLUDED.close, open = EXCLUDED.open, ...
```

**Lineage:**
```python
{
    "entity_type": "price",
    "entity_id": f"{symbol}_{pack_id}",
    "source_type": "external_api",
    "source_id": "FMP Premium",
    "transformation": "direct_mapping",
    "inputs": {"api": "FMP /v3/quote", "symbol": symbol}
}
```

---

### 2. FMP Profile → securities table

**API:** `GET /v3/profile/{symbol}`
**Response:**
```json
{
  "symbol": "AAPL",
  "companyName": "Apple Inc.",
  "currency": "USD",
  "exchange": "NASDAQ",
  "industry": "Consumer Electronics",
  "sector": "Technology",
  "isin": "US0378331005"
}
```

**Database:** `securities`
```sql
INSERT INTO securities (
    id,                  -- UUID generated
    symbol,              -- profile.symbol
    name,                -- profile.companyName
    security_type,       -- 'EQUITY' (default)
    currency,            -- profile.currency
    sector,              -- profile.sector
    industry,            -- profile.industry
    exchange,            -- profile.exchange
    created_at,
    updated_at
) VALUES (uuid_generate_v4(), $1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
ON CONFLICT (symbol) DO UPDATE
SET name = EXCLUDED.name, sector = EXCLUDED.sector, ...
```

**Additional Metadata (if `security_metadata` table exists):**
- `isin`, `cusip`, `description`, `ceo`, `website`, `employees`, `market_cap`

---

### 3. FMP Dividend Calendar → corporate_actions table

**API:** `GET /v3/stock_dividend_calendar?from={date}&to={date}`
**Response:**
```json
{
  "date": "2025-11-07",
  "symbol": "AAPL",
  "dividend": 0.24,
  "recordDate": "2025-11-10",
  "paymentDate": "2025-11-14",
  "declarationDate": "2025-10-28"
}
```

**Database:** `corporate_actions`
```sql
INSERT INTO corporate_actions (
    id,                  -- UUID generated
    security_id,         -- Lookup from securities WHERE symbol = 'AAPL'
    action_type,         -- 'DIVIDEND'
    ex_date,             -- div.date
    record_date,         -- div.recordDate
    pay_date,            -- div.paymentDate
    amount,              -- div.dividend
    currency,            -- From security.currency
    status,              -- 'ANNOUNCED' if future, 'COMPLETED' if past
    source,              -- 'FMP'
    created_at
) VALUES (uuid_generate_v4(), $1, 'DIVIDEND', $2, $3, $4, $5, $6, $7, 'FMP', NOW())
ON CONFLICT (security_id, action_type, ex_date) DO NOTHING
```

**Critical for ADRs:**
- **Pay-date FX conversion:** Must convert dividend at `pay_date` FX rate, not `ex_date`
- **Example:** Canadian ADR pays $0.50 CAD on 2025-11-14
  - Ex-date: 2025-11-07 (CAD/USD = 0.73)
  - Pay-date: 2025-11-14 (CAD/USD = 0.74)
  - **Correct:** $0.50 × 0.74 = $0.37 USD (pay-date FX)
  - **Incorrect:** $0.50 × 0.73 = $0.365 USD (ex-date FX)

---

### 4. FMP Stock Split Calendar → corporate_actions table

**API:** `GET /v3/stock_split_calendar?from={date}&to={date}`
**Response:**
```json
{
  "date": "2020-08-31",
  "symbol": "AAPL",
  "numerator": 4,
  "denominator": 1
}
```

**Database:** `corporate_actions`
```sql
INSERT INTO corporate_actions (
    id,
    security_id,
    action_type,         -- 'SPLIT'
    ex_date,             -- split.date
    split_numerator,     -- split.numerator
    split_denominator,   -- split.denominator
    split_ratio,         -- numerator / denominator = 4.0
    status,
    source,
    created_at
) VALUES (uuid_generate_v4(), $1, 'SPLIT', $2, $3, $4, $5, $6, 'FMP', NOW())
ON CONFLICT (security_id, action_type, ex_date) DO NOTHING
```

**Adjustment Logic:**
```python
split_ratio = numerator / denominator  # 4.0 for 4:1 split
new_quantity = old_quantity * split_ratio  # 100 → 400 shares
new_cost_basis_per_share = old_cost_basis_per_share / split_ratio  # $100 → $25
```

---

## FRED → Database Mappings

### FRED Series Observations → economic_indicators table

**API:** `GET /series/observations?series_id=CPIAUCSL`
**Response:**
```json
{
  "observations": [
    {"date": "2024-01-01", "value": "306.746"},
    {"date": "2024-02-01", "value": "308.417"}
  ]
}
```

**Database:** `economic_indicators` (or `macro_indicators`)
```sql
INSERT INTO economic_indicators (
    id,                  -- UUID generated
    series_id,           -- 'CPIAUCSL'
    asof_date,           -- obs.date
    value,               -- CAST(obs.value AS DECIMAL)
    unit,                -- From series metadata (e.g., "Index 1982-1984=100")
    source,              -- 'FRED'
    created_at
) VALUES (uuid_generate_v4(), $1, $2, $3, $4, 'FRED', NOW())
ON CONFLICT (series_id, asof_date) DO UPDATE
SET value = EXCLUDED.value, unit = EXCLUDED.unit
```

**Data Quality:**
- **Missing values:** FRED uses `"."` for missing data → Skip these records
- **Frequency:** Daily, monthly, quarterly (depends on series)
- **Backfill:** Can fetch historical data (e.g., 10 years of CPI)

**Factor Analysis Mapping:**
```python
# From fred_provider.py:get_factor_data()
factor_series = {
    "real_rate": "DFII10",       # 10Y TIPS yield
    "inflation": "T10YIE",       # 10Y breakeven inflation
    "credit": "BAMLC0A0CM",      # AAA corporate spread
    "usd": "DTWEXBGS",           # Trade-weighted USD
    "risk_free": "DGS10",        # 10Y Treasury
}

# These populate economic_indicators table
# Factor analysis service queries this table for regression
```

---

## Polygon → Database Mappings

### 1. Polygon Aggregates → prices table

**API:** `GET /v2/aggs/ticker/{symbol}/range/1/day/{from}/{to}`
**Response:**
```json
{
  "results": [
    {
      "t": 1704153600000,  // Unix timestamp (ms)
      "o": 187.15,
      "h": 188.44,
      "l": 183.89,
      "c": 185.64,
      "v": 82488600
    }
  ]
}
```

**Database:** `prices`
```sql
INSERT INTO prices (
    pricing_pack_id,
    security_id,
    asof_date,           -- FROM_UNIXTIME(bar.t / 1000)
    open,                -- bar.o
    high,                -- bar.h
    low,                 -- bar.l
    close,               -- bar.c
    volume,              -- bar.v
    currency,
    created_at
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
ON CONFLICT (pricing_pack_id, security_id) DO UPDATE
SET close = EXCLUDED.close, ...
```

**Important:** Polygon prices are **split-adjusted only**, NOT dividend-adjusted.
For total return calculations, must apply dividend adjustments separately from `corporate_actions` table.

---

### 2. Polygon Dividends → corporate_actions table

**API:** `GET /v3/reference/dividends?ticker={symbol}`
**Response:**
```json
{
  "ticker": "AAPL",
  "ex_dividend_date": "2025-02-09",
  "cash_amount": 0.24,
  "currency": "USD",
  "pay_date": "2025-02-16",
  "record_date": "2025-02-12"
}
```

**Database:** `corporate_actions`
```sql
INSERT INTO corporate_actions (
    id,
    security_id,
    action_type,         -- 'DIVIDEND'
    ex_date,             -- div.ex_dividend_date
    record_date,         -- div.record_date
    pay_date,            -- div.pay_date
    amount,              -- div.cash_amount
    currency,            -- div.currency
    status,
    source,              -- 'Polygon'
    created_at
) VALUES (uuid_generate_v4(), $1, 'DIVIDEND', $2, $3, $4, $5, $6, $7, 'Polygon', NOW())
ON CONFLICT (security_id, action_type, ex_date) DO NOTHING
```

**Data Quality:** Polygon is considered **primary source** for corporate actions (higher quality than FMP).

---

## Data Lineage Tracking

### Lineage Record Structure

```python
@dataclass
class LineageRecord:
    lineage_id: UUID
    entity_type: str      # "price", "economic_indicator", "corporate_action"
    entity_id: str        # "{symbol}_{pack_id}" or "{series_id}_{date}"
    source_type: str      # "external_api"
    source_id: str        # "FMP Premium", "FRED", "Polygon"
    transformation: str   # "direct_mapping", "aggregation", "computation"
    transformation_config: Dict
    inputs: Dict          # {"api": "FMP /v3/quote", "symbol": "AAPL"}
    metadata: Dict        # {"confidence": "high", "freshness": "2025-11-05T10:30:00Z"}
    created_at: datetime
```

### Example Lineage Records

#### Price from FMP
```json
{
  "lineage_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity_type": "price",
  "entity_id": "AAPL_PP_2025-11-05",
  "source_type": "external_api",
  "source_id": "FMP Premium",
  "transformation": "direct_mapping",
  "transformation_config": {},
  "inputs": {
    "api_endpoint": "FMP /v3/quote/AAPL",
    "request_timestamp": "2025-11-05T16:00:00Z",
    "rate_limit_used": "120/min"
  },
  "metadata": {
    "confidence": "high",
    "freshness_seconds": 30,
    "provider_latency_ms": 145,
    "attribution": "Financial data © Financial Modeling Prep"
  }
}
```

#### Economic Indicator from FRED
```json
{
  "lineage_id": "660e9500-f39c-52e5-b827-557766551111",
  "entity_type": "economic_indicator",
  "entity_id": "CPIAUCSL_2025-01-01",
  "source_type": "external_api",
  "source_id": "FRED",
  "transformation": "direct_mapping",
  "transformation_config": {"missing_value_handling": "skip_dots"},
  "inputs": {
    "api_endpoint": "FRED /series/observations",
    "series_id": "CPIAUCSL",
    "observation_date": "2025-01-01"
  },
  "metadata": {
    "confidence": "very_high",
    "freshness_days": 0,
    "frequency": "monthly",
    "seasonal_adjustment": "Seasonally Adjusted",
    "attribution": "Source: Federal Reserve Economic Data (FRED®)"
  }
}
```

---

## Data Quality Checks

### Validation Rules by Provider

#### FMP Quotes
```python
@dataclass
class FMPQuoteValidation:
    symbol: Constraint(regex=r"^[A-Z]{1,5}$")
    price: Constraint(range=(0.01, 1e9), not_null=True)
    volume: Constraint(range=(0, 1e12))
    timestamp: Constraint(custom=lambda t: t <= now())

    # Cross-field validation
    high: Constraint(custom=lambda row: row.high >= row.low)
    low: Constraint(custom=lambda row: row.low <= row.close)
```

#### FRED Series
```python
@dataclass
class FREDSeriesValidation:
    series_id: Constraint(in_list=FRED_SERIES_IDS)
    asof_date: Constraint(range=(date(1900, 1, 1), date.today()))
    value: Constraint(custom=lambda v: v != ".", not_null=True)

    # Unique constraint
    unique_key: (series_id, asof_date)
```

#### Corporate Actions
```python
@dataclass
class CorporateActionValidation:
    action_type: Constraint(in_list=["DIVIDEND", "SPLIT", "MERGER"])
    ex_date: Constraint(not_null=True)
    amount: Constraint(range=(0, 1e6), required_if=lambda row: row.action_type == "DIVIDEND")
    split_ratio: Constraint(range=(0.01, 100), required_if=lambda row: row.action_type == "SPLIT")

    # Date consistency
    pay_date: Constraint(custom=lambda row: row.pay_date >= row.ex_date if row.pay_date else True)
```

---

## Provider Data Priority

When multiple providers offer the same data, use this priority order:

### Prices
1. **Primary:** FMP (real-time via Premium plan)
2. **Backup:** Polygon (end-of-day)
3. **Fallback:** Cached data from previous pack

### Corporate Actions
1. **Primary (ACTIVE):** FMP Premium (dividends, splits, earnings)
2. **Backup (NOT IMPLEMENTED):** Polygon (methods exist but unused)
3. **Note:** Despite documentation claims, Polygon is NOT used for corporate actions in production

### Economic Indicators
1. **Only source:** FRED (official government data)

### News
1. **Only source:** NewsAPI (dev tier = metadata only)

---

## Schema Migration Notes

### Missing Tables

If these tables don't exist, create them:

#### economic_indicators
```sql
CREATE TABLE economic_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    series_id VARCHAR(50) NOT NULL,
    asof_date DATE NOT NULL,
    value NUMERIC(20,8) NOT NULL,
    unit VARCHAR(100),
    source VARCHAR(50) NOT NULL DEFAULT 'FRED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (series_id, asof_date)
);

CREATE INDEX idx_economic_indicators_series ON economic_indicators(series_id, asof_date DESC);
```

#### corporate_actions
```sql
CREATE TABLE corporate_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id UUID NOT NULL REFERENCES securities(id),
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('DIVIDEND', 'SPLIT', 'MERGER', 'SPINOFF')),
    ex_date DATE NOT NULL,
    record_date DATE,
    pay_date DATE,
    amount NUMERIC(20,8),
    currency VARCHAR(3),
    split_numerator INTEGER,
    split_denominator INTEGER,
    split_ratio NUMERIC(10,4),
    status VARCHAR(20) NOT NULL DEFAULT 'ANNOUNCED',
    source VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (security_id, action_type, ex_date)
);

CREATE INDEX idx_corporate_actions_security ON corporate_actions(security_id, ex_date DESC);
CREATE INDEX idx_corporate_actions_type_status ON corporate_actions(action_type, status);
```

---

## Data Freshness Requirements

| Data Type | Freshness | Update Frequency | Staleness Threshold |
|-----------|-----------|------------------|---------------------|
| **FMP Quotes** | < 15 min | Real-time (Premium) | 1 hour |
| **FRED Economic** | < 1 day | Daily/Monthly | 7 days |
| **Polygon Prices** | T+0 | End-of-day | 2 days |
| **Corporate Actions** | < 1 day | Daily | 1 day |
| **News Articles** | < 1 hour | Real-time | 24 hours |

**Staleness Alerts:**
- ⚠️ Warning: Data older than freshness requirement
- 🚨 Critical: Data older than staleness threshold
- 🔴 Fail: Use cached/stale data with flag

---

## Summary

### Provider → Database Flow

```
External API
    ↓
Provider Facade (FMPProvider, FREDProvider, etc.)
    ↓
BaseProvider (retry logic, rate limiting)
    ↓
Response Normalization (contract validation)
    ↓
Lineage Recording (source, timestamp, confidence)
    ↓
Database Ingestion (INSERT or UPDATE)
    ↓
Tables: prices, securities, economic_indicators, corporate_actions
```

### Key Principles

1. **Idempotency:** Use `ON CONFLICT ... DO UPDATE` for all inserts
2. **Lineage:** Track source, timestamp, and transformation for every record
3. **Validation:** Enforce data contracts at ingestion time
4. **Freshness:** Monitor staleness and alert on threshold breaches
5. **Priority:** Use highest-quality source when multiple providers available
6. **Attribution:** Store provider name for legal compliance

---

**Last Updated:** 2025-11-05
**Related Documentation:**
- [provider-api-documentation.md](provider-api-documentation.md) - Complete API reference
- [data-contracts.md](data-contracts.md) - Data contract specifications
- [data-lineage.md](data-lineage.md) - Lineage tracking patterns
- [DATABASE.md](../../DATABASE.md) - Database schema reference
