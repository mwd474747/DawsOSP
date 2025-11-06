# DawsOS External Provider API Documentation

**Created:** 2025-11-05
**Purpose:** Complete documentation of external data provider APIs, data contracts, and integration patterns
**Status:** Production (running on Replit backend)

---

## Table of Contents

1. [Provider Overview](#provider-overview)
2. [FMP (Financial Modeling Prep) - Premium Plan](#fmp-financial-modeling-prep---premium-plan)
3. [FRED (Federal Reserve Economic Data)](#fred-federal-reserve-economic-data)
4. [Polygon.io](#polyg onio)
5. [NewsAPI](#newsapi)
6. [Data Flow Architecture](#data-flow-architecture)
7. [Rate Limiting & Circuit Breakers](#rate-limiting--circuit-breakers)
8. [Data Contracts & Validation](#data-contracts--validation)
9. [Error Handling & Retry Logic](#error-handling--retry-logic)
10. [Provider Rights & Export Restrictions](#provider-rights--export-restrictions)

---

## Provider Overview

### Architecture Pattern

```
Pattern Request
     ↓
Agent (DataHarvester)
     ↓
Provider Facade (FMPProvider, FREDProvider, etc.)
     ↓
BaseProvider (retry logic, rate limiting, DLQ)
     ↓
External API (HTTPS)
     ↓
Response
     ↓
Database (prices, economic_indicators, securities, etc.)
```

### Provider Summary Table

| Provider | Purpose | Rate Limit | Plan | Rights | Status |
|----------|---------|------------|------|--------|--------|
| **FMP** | Stock data, fundamentals, corporate actions | 120 req/min | **Premium** | Restricted export | ✅ Active |
| **FRED** | Economic indicators (inflation, rates, GDP) | 60 req/min | Free | Export allowed | ✅ Active |
| **Polygon** | Prices, splits, dividends (ADR accuracy) | 100 req/min | Paid | Restricted export | ✅ Active |
| **NewsAPI** | News articles, sentiment analysis | 30 req/min | Dev (free) | **NO export** | ✅ Active |

### Base Provider Features

All providers inherit from `BaseProvider` ([base_provider.py:245](backend/app/integrations/base_provider.py#L245)):

**Features:**
- ✅ Exponential backoff retry (1s, 2s, 4s with jitter)
- ✅ Rate limiting (token bucket algorithm)
- ✅ Circuit breaker protection
- ✅ Dead Letter Queue (DLQ) for failed requests
- ✅ Response caching (serves stale data on failure)
- ✅ OpenTelemetry tracing
- ✅ Prometheus metrics (latency, errors, retries)
- ✅ Rights pre-flight checks

**Configuration:**
```python
@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str
    rate_limit_rpm: int          # Requests per minute
    max_retries: int = 3         # Max retry attempts
    retry_base_delay: float = 1.0  # Base delay for exponential backoff
    rights: Dict[str, Any]       # Export/redistribution rights
```

---

## FMP (Financial Modeling Prep) - Premium Plan

**File:** [backend/app/integrations/fmp_provider.py](backend/app/integrations/fmp_provider.py)
**Base URL:** `https://financialmodelingprep.com/api`
**Plan:** **Premium** (all endpoints available on Replit)
**Rate Limit:** 120 requests/minute
**Documentation:** https://site.financialmodelingprep.com/developer/docs

### Key Features (Premium Plan)

The Premium plan provides:
- ✅ **Real-time quotes** (15-minute delay on free, real-time on premium)
- ✅ **Financial statements** (income, balance sheet, cash flow) - 5+ years
- ✅ **Financial ratios** (profitability, liquidity, leverage)
- ✅ **Corporate actions** (dividends, splits, earnings calendars)
- ✅ **Bulk endpoints** (quote up to 100 symbols at once)
- ✅ **Historical prices** (daily OHLCV)
- ✅ **Company profiles** (industry, sector, market cap, CEO, description)

### Endpoints Used

#### 1. Company Profile
```python
GET /v3/profile/{symbol}
```

**Parameters:**
- `symbol`: Stock ticker (e.g., "AAPL")
- `apikey`: FMP API key

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "companyName": "Apple Inc.",
    "currency": "USD",
    "exchange": "NASDAQ",
    "industry": "Consumer Electronics",
    "sector": "Technology",
    "country": "US",
    "isin": "US0378331005",
    "cusip": "037833100",
    "description": "Apple Inc. designs, manufactures...",
    "ceo": "Timothy Cook",
    "website": "https://www.apple.com",
    "employees": 161000,
    "marketCap": 3000000000000,
    "beta": 1.2
  }
]
```

**Database Mapping:**
- `securities` table: symbol, name (companyName), currency, exchange, isin, cusip
- `security_metadata` table: industry, sector, country, description, ceo, website, employees

#### 2. Income Statement
```python
GET /v3/income-statement/{symbol}?period={annual|quarter}&limit=5
```

**Response:**
```json
[
  {
    "date": "2023-09-30",
    "symbol": "AAPL",
    "reportedCurrency": "USD",
    "cik": "0000320193",
    "fillingDate": "2023-11-03",
    "calendarYear": "2023",
    "period": "FY",
    "revenue": 383285000000,
    "costOfRevenue": 214137000000,
    "grossProfit": 169148000000,
    "operatingExpenses": 51345000000,
    "operatingIncome": 117803000000,
    "netIncome": 96995000000,
    "eps": 6.16,
    "epsdiluted": 6.13
  }
]
```

**Database Mapping:**
- `financial_statements` table (if exists)
- Used by: Buffett Checklist pattern (fundamentals analysis)

#### 3. Balance Sheet
```python
GET /v3/balance-sheet-statement/{symbol}?period={annual|quarter}&limit=5
```

**Key Fields:**
- `totalAssets`, `totalCurrentAssets`, `cashAndCashEquivalents`
- `totalLiabilities`, `totalCurrentLiabilities`
- `totalStockholdersEquity`, `retainedEarnings`

#### 4. Cash Flow Statement
```python
GET /v3/cash-flow-statement/{symbol}?period={annual|quarter}&limit=5
```

**Key Fields:**
- `operatingCashFlow`, `capitalExpenditure`, `freeCashFlow`
- `dividendsPaid`, `stockBasedCompensation`

#### 5. Financial Ratios
```python
GET /v3/ratios/{symbol}?period={annual|quarter}&limit=5
```

**Response:**
```json
[
  {
    "date": "2023-09-30",
    "symbol": "AAPL",
    "currentRatio": 1.07,
    "quickRatio": 0.85,
    "debtToEquity": 1.97,
    "returnOnEquity": 1.72,
    "returnOnAssets": 0.28,
    "netProfitMargin": 0.25,
    "operatingProfitMargin": 0.31,
    "priceToBookRatio": 51.2,
    "priceToEarningsRatio": 31.5,
    "dividendYield": 0.0045,
    "payoutRatio": 0.15
  }
]
```

**Used By:** Buffett Checklist (ROE, profit margins, debt ratios)

#### 6. Real-Time Quote (Bulk)
```python
GET /v3/quote/{symbol1,symbol2,...}  # Max 100 symbols
```

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "price": 175.43,
    "changesPercentage": 1.25,
    "change": 2.17,
    "dayLow": 173.50,
    "dayHigh": 176.20,
    "yearHigh": 199.62,
    "yearLow": 124.17,
    "marketCap": 2750000000000,
    "priceAvg50": 182.45,
    "priceAvg200": 165.32,
    "volume": 52000000,
    "avgVolume": 58000000,
    "exchange": "NASDAQ",
    "open": 174.20,
    "previousClose": 173.26,
    "eps": 6.13,
    "pe": 28.6,
    "earningsAnnouncement": "2024-02-01T21:00:00.000+00:00",
    "sharesOutstanding": 15728700000,
    "timestamp": 1698345600
  }
]
```

**Database Mapping:**
- `prices` table: symbol, asof_date, close (price), open, high (dayHigh), low (dayLow), volume
- `pricing_packs` table: Grouped by pack_id + date

**Used By:** Pricing pipeline, portfolio valuation

#### 7. Dividend Calendar
```python
GET /v3/stock_dividend_calendar?from={YYYY-MM-DD}&to={YYYY-MM-DD}
```

**Response:**
```json
[
  {
    "date": "2025-11-07",
    "label": "November 07, 25",
    "adjDividend": 0.24,
    "symbol": "AAPL",
    "dividend": 0.24,
    "recordDate": "2025-11-10",
    "paymentDate": "2025-11-14",
    "declarationDate": "2025-10-28"
  }
]
```

**Database Mapping:**
- `corporate_actions` table: type='DIVIDEND', ex_date (date), amount (dividend), record_date, pay_date (paymentDate)

**Critical:** Used for ADR dividend adjustments (pay-date FX conversion)

#### 8. Stock Split Calendar
```python
GET /v3/stock_split_calendar?from={YYYY-MM-DD}&to={YYYY-MM-DD}
```

**Response:**
```json
[
  {
    "date": "2025-11-07",
    "label": "November 07, 25",
    "symbol": "AAPL",
    "numerator": 4,
    "denominator": 1
  }
]
```

**Database Mapping:**
- `corporate_actions` table: type='SPLIT', ex_date (date), split_ratio (numerator/denominator)

**Adjustment Logic:**
- New quantity = old_quantity / split_ratio
- New price = old_price * split_ratio

#### 9. Earnings Calendar
```python
GET /v3/earning_calendar?from={YYYY-MM-DD}&to={YYYY-MM-DD}
```

**Response:**
```json
[
  {
    "date": "2025-11-07",
    "symbol": "AAPL",
    "eps": 1.42,
    "epsEstimated": 1.38,
    "time": "amc",  # "amc" = after market close, "bmo" = before market open
    "revenue": 90000000000,
    "revenueEstimated": 89000000000
  }
]
```

**Used By:** Corporate actions pattern, earnings surprises

### FMP Data Contract

```python
@dataclass
class FMPQuoteContract:
    symbol: str               # NOT NULL
    price: Decimal            # NOT NULL, > 0
    timestamp: datetime       # NOT NULL
    volume: int              # >= 0
    market_cap: Decimal      # >= 0
    change_pct: Decimal      # Can be negative

    constraints:
        - symbol matches /^[A-Z]{1,5}$/
        - price > 0
        - timestamp <= now()
        - volume >= 0

    provenance:
        source: "FMP Premium"
        confidence: "high"
        freshness: < 15 minutes
        attribution_required: True
```

### FMP Rights & Restrictions

**From** [fmp_provider.py:62-68](backend/app/integrations/fmp_provider.py#L62-L68):
```python
rights={
    "export_pdf": False,        # ❌ BLOCKED
    "export_csv": False,        # ❌ BLOCKED
    "redistribution": False,    # ❌ BLOCKED
    "requires_attribution": True,
    "attribution_text": "Financial data © Financial Modeling Prep",
}
```

**Implications:**
- ✅ Can display data in UI
- ✅ Can store in database for internal use
- ❌ Cannot export to PDF/CSV for user download
- ❌ Cannot redistribute data to third parties
- ✅ Must show attribution in UI

---

## FRED (Federal Reserve Economic Data)

**File:** [backend/app/integrations/fred_provider.py](backend/app/integrations/fred_provider.py)
**Base URL:** `https://api.stlouisfed.org/fred`
**Plan:** Free
**Rate Limit:** 60 requests/minute (conservative)
**Documentation:** https://fred.stlouisfed.org/docs/api/

### Key Features

- ✅ **Economic indicators** (GDP, CPI, unemployment, yields)
- ✅ **Historical time series** (daily, monthly, quarterly)
- ✅ **Metadata** (units, frequency, seasonal adjustment)
- ✅ **Export allowed** (public data with attribution)
- ✅ **No cost** (free API key)

### Series IDs for Factor Analysis

**From** [fred_provider.py:50-94](backend/app/integrations/fred_provider.py#L50-L94):

#### Yield Curve
- `T10Y2Y`: 10Y-2Y Treasury spread (curve steepness)
- `T10Y3M`: 10Y-3M Treasury spread
- `DGS10`: 10Y Treasury constant maturity
- `DGS2`: 2Y Treasury constant maturity

#### Inflation
- `CPIAUCSL`: Consumer Price Index (headline inflation)
- `PCEPI`: PCE Price Index (Fed's preferred measure)
- `T10YIE`: 10Y breakeven inflation (market-implied)
- `T5YIE`: 5Y breakeven inflation

#### Real Rates
- `DFII10`: 10Y TIPS yield (real rate)
- `DFII5`: 5Y TIPS yield

#### Labor Market
- `UNRATE`: Unemployment rate
- `PAYEMS`: Nonfarm payrolls
- `U6RATE`: U6 underemployment rate

#### Credit Spreads
- `BAA10Y`: BAA corporate - 10Y Treasury spread
- `BAMLC0A0CM`: ICE BofA AAA Corporate OAS
- `BAMLH0A0HYM2`: ICE BofA High Yield OAS

#### Growth
- `GDP`: Gross Domestic Product (nominal)
- `GDPC1`: Real GDP
- `GDPPOT`: Potential GDP

#### Currency
- `DTWEXBGS`: Trade-weighted USD index (DXY broad)
- `DEXCAUS`: CAD/USD exchange rate

### Endpoints Used

#### 1. Series Observations
```python
GET /series/observations?series_id={ID}&api_key={KEY}&file_type=json
```

**Parameters:**
- `series_id`: FRED series ID (e.g., "CPIAUCSL")
- `observation_start`: Start date (YYYY-MM-DD, optional)
- `observation_end`: End date (YYYY-MM-DD, optional)
- `frequency`: Frequency (d=daily, w=weekly, m=monthly, q=quarterly, a=annual)
- `aggregation_method`: avg, sum, eop (end of period)
- `file_type`: json

**Response:**
```json
{
  "observations": [
    {
      "realtime_start": "2024-01-01",
      "realtime_end": "2024-01-01",
      "date": "2024-01-01",
      "value": "306.746"
    },
    {
      "date": "2024-02-01",
      "value": "308.417"
    }
  ]
}
```

**Database Mapping:**
- `economic_indicators` table: series_id, asof_date (date), value, unit, source='FRED'

**Data Normalization:**
```python
# From fred_provider.py:224-238
for obs in observations:
    if obs["value"] == ".":  # FRED uses "." for missing values
        continue

    series_data.append({
        "date": obs["date"],
        "value": float(obs["value"]),
        "series_id": series_id,
    })
```

#### 2. Series Metadata
```python
GET /series?series_id={ID}&api_key={KEY}&file_type=json
```

**Response:**
```json
{
  "series": [
    {
      "id": "CPIAUCSL",
      "title": "Consumer Price Index for All Urban Consumers: All Items in U.S. City Average",
      "observation_start": "1947-01-01",
      "observation_end": "2024-01-01",
      "frequency": "Monthly",
      "frequency_short": "M",
      "units": "Index 1982-1984=100",
      "seasonal_adjustment": "Seasonally Adjusted",
      "last_updated": "2024-02-13 07:44:03-06",
      "popularity": 95
    }
  ]
}
```

**Used By:** Factor analysis metadata, regime detection

### Factor Data Fetching

**From** [fred_provider.py:320-368](backend/app/integrations/fred_provider.py#L320-L368):

```python
# Fetches all factor series in parallel
async def get_factor_data(start_date, end_date) -> Dict[str, List[Dict]]:
    return {
        "real_rate": await get_series("DFII10", start_date, end_date),
        "inflation": await get_series("T10YIE", start_date, end_date),
        "credit": await get_series("BAMLC0A0CM", start_date, end_date),
        "usd": await get_series("DTWEXBGS", start_date, end_date),
        "risk_free": await get_series("DGS10", start_date, end_date),
    }
```

**Used By:** [factor_analysis.py](backend/app/services/factor_analysis.py) for portfolio factor exposures

### Regime Indicators

**From** [fred_provider.py:370-415](backend/app/integrations/fred_provider.py#L370-L415):

```python
async def get_regime_indicators(start_date, end_date) -> Dict[str, List[Dict]]:
    return {
        "curve": await get_series("T10Y2Y", start_date, end_date),  # Yield curve
        "cpi": await get_series("CPIAUCSL", start_date, end_date),  # Inflation
        "unemployment": await get_series("UNRATE", start_date, end_date),
        "credit_spread": await get_series("BAA10Y", start_date, end_date),
    }
```

**Used By:** [macro.py](backend/app/services/macro.py) for macro regime detection (inflation, growth quadrants)

### FRED Data Contract

```python
@dataclass
class FREDSeriesContract:
    series_id: str           # NOT NULL, matches FRED_SERIES_IDS
    asof_date: date          # NOT NULL
    value: Decimal           # NOT NULL (or skip if ".")
    unit: str               # Optional (from metadata)
    source: str = "FRED"    # Fixed

    constraints:
        - series_id in FRED_SERIES_IDS
        - asof_date <= today()
        - value != "." (filter out missing)
        - No duplicates: UNIQUE(series_id, asof_date)

    provenance:
        source: "FRED (Federal Reserve Bank of St. Louis)"
        confidence: "very_high" (official government data)
        freshness: depends on series (daily, monthly, quarterly)
        attribution_required: True
```

### FRED Rights & Restrictions

**From** [fred_provider.py:110-116](backend/app/integrations/fred_provider.py#L110-L116):
```python
rights={
    "export_pdf": True,       # ✅ ALLOWED
    "export_csv": True,       # ✅ ALLOWED
    "redistribution": True,   # ✅ ALLOWED with attribution
    "requires_attribution": True,
    "attribution_text": "Source: Federal Reserve Economic Data (FRED®), Federal Reserve Bank of St. Louis",
}
```

**Implications:**
- ✅ Can export to PDF/CSV
- ✅ Can redistribute with attribution
- ✅ Public data, no licensing restrictions
- ✅ Must show attribution

---

## Polygon.io

**File:** [backend/app/integrations/polygon_provider.py](backend/app/integrations/polygon_provider.py)
**Base URL:** `https://api.polygon.io`
**Plan:** Paid (Stocks tier)
**Rate Limit:** 100 requests/minute
**Documentation:** https://polygon.io/docs/stocks

### Key Features

- ✅ **Historical prices** (daily OHLCV aggregates)
- ✅ **Stock splits** with ex-date
- ✅ **Dividends** with ex-date and pay-date (**CRITICAL for ADR accuracy**)
- ✅ **High-quality data** (primary source for corporate actions)
- ❌ **Split-adjusted only** (does NOT adjust for dividends)

### Endpoints Used

#### 1. Daily Aggregates (OHLCV)
```python
GET /v2/aggs/ticker/{symbol}/range/1/day/{from}/{to}?adjusted=true
```

**Parameters:**
- `symbol`: Stock ticker
- `from`, `to`: Date range (YYYY-MM-DD)
- `adjusted`: `true` (split-adjusted) or `false` (unadjusted)
- `sort`: `asc` or `desc`
- `limit`: Max results (default 50000)

**Response:**
```json
{
  "status": "OK",
  "results": [
    {
      "t": 1704153600000,  // Unix timestamp (milliseconds)
      "o": 187.15,         // Open
      "h": 188.44,         // High
      "l": 183.89,         // Low
      "c": 185.64,         // Close
      "v": 82488600,       // Volume
      "vw": 185.92,        // VWAP
      "n": 748523          // Number of transactions
    }
  ]
}
```

**Database Mapping:**
- `prices` table: security_id, pricing_pack_id, asof_date, open, high, low, close, volume

**Important:** Polygon adjusts for splits but NOT dividends. For total return calculations, must apply dividend adjustments separately.

#### 2. Stock Splits
```python
GET /v3/reference/splits?ticker={symbol}&execution_date.gte={from}
```

**Response:**
```json
{
  "results": [
    {
      "ticker": "AAPL",
      "execution_date": "2020-08-31",
      "split_from": 1,
      "split_to": 4
    }
  ]
}
```

**Database Mapping:**
- `corporate_actions` table: type='SPLIT', symbol, ex_date (execution_date), split_ratio (split_from/split_to)

**Adjustment Formula:**
```python
split_ratio = split_from / split_to  # e.g., 1/4 = 0.25 for 4:1 split
new_quantity = old_quantity / split_ratio  # e.g., 100 shares → 400 shares
new_price = old_price * split_ratio        # e.g., $100 → $25
```

#### 3. Dividends
```python
GET /v3/reference/dividends?ticker={symbol}&ex_dividend_date.gte={from}
```

**Response:**
```json
{
  "results": [
    {
      "ticker": "AAPL",
      "ex_dividend_date": "2025-02-09",
      "cash_amount": 0.24,
      "currency": "USD",
      "declaration_date": "2025-02-01",
      "pay_date": "2025-02-16",
      "record_date": "2025-02-12",
      "frequency": 4,  // Quarterly
      "dividend_type": "CD"  // Cash Dividend
    }
  ]
}
```

**Database Mapping:**
- `corporate_actions` table: type='DIVIDEND', symbol, ex_date, amount (cash_amount), currency, pay_date, record_date

**Critical for ADRs:** Pay-date FX conversion (must convert at pay_date FX rate, not ex_date)

### Polygon Data Contract

```python
@dataclass
class PolygonPriceContract:
    symbol: str
    asof_date: date
    open: Decimal            # > 0
    high: Decimal            # >= open, >= low, >= close
    low: Decimal             # > 0, <= high
    close: Decimal           # > 0
    volume: int              # >= 0
    vwap: Optional[Decimal]  # Volume-weighted average price

    constraints:
        - high >= max(open, close, low)
        - low <= min(open, close, high)
        - close > 0, open > 0
        - volume >= 0
        - No duplicates: UNIQUE(symbol, asof_date)

    provenance:
        source: "Polygon.io"
        confidence: "high"
        freshness: End-of-day (T+0)
        adjustment: "split_adjusted_only"  # NOT dividend-adjusted
```

### Polygon Rights & Restrictions

**From** [polygon_provider.py:59-65](backend/app/integrations/polygon_provider.py#L59-L65):
```python
rights={
    "export_pdf": False,        # ❌ BLOCKED
    "export_csv": False,        # ❌ BLOCKED
    "redistribution": False,    # ❌ BLOCKED
    "requires_attribution": True,
    "attribution_text": "Market data © Polygon.io",
}
```

---

## NewsAPI

**File:** [backend/app/integrations/news_provider.py](backend/app/integrations/news_provider.py)
**Base URL:** `https://newsapi.org/v2`
**Plan:** Dev (Free) - **METADATA ONLY**
**Rate Limit:** 30 requests/minute (100 requests/day total)
**Documentation:** https://newsapi.org/docs

### Key Features

- ✅ **News search** by keyword, symbol, date range
- ✅ **Breaking news** (top headlines)
- ⚠️ **Dev tier:** Metadata only (title, description, URL) - **NO article content**
- ⚠️ **Business tier:** Full article content (requires paid license)
- ❌ **Export blocked** on dev tier

### Endpoints Used

#### 1. Everything (Search)
```python
GET /v2/everything?q={query}&from={YYYY-MM-DD}&to={YYYY-MM-DD}
```

**Parameters:**
- `q`: Search query (e.g., "AAPL", "inflation", "Federal Reserve")
- `from`, `to`: Date range
- `language`: Language code (default: "en")
- `sortBy`: `relevancy`, `popularity`, `publishedAt`
- `pageSize`: Results per page (max 100)
- `apiKey`: NewsAPI key

**Response (Dev Tier):**
```json
{
  "status": "ok",
  "totalResults": 1234,
  "articles": [
    {
      "source": {
        "id": "bloomberg",
        "name": "Bloomberg"
      },
      "author": "John Doe",
      "title": "Apple Reports Record Quarter",
      "description": "Apple Inc. reported record revenue...",
      "url": "https://bloomberg.com/...",
      "urlToImage": "https://...",
      "publishedAt": "2024-01-15T14:30:00Z",
      "content": null  // ❌ NULL on dev tier
    }
  ]
}
```

**Response (Business Tier):**
```json
{
  "articles": [
    {
      "content": "Apple Inc. (AAPL) reported record revenue of $123.9B...[+500 chars]"  // ✅ Content available
    }
  ]
}
```

**Database Mapping:**
- `news_articles` table (if exists): source, author, title, description, url, published_at, content (NULL on dev tier)

**Used By:** News impact analysis pattern (portfolio-weighted sentiment)

### NewsAPI Data Contract

```python
@dataclass
class NewsAPIArticleContract:
    source_name: str         # NOT NULL
    title: str              # NOT NULL
    description: str        # Optional
    url: str                # NOT NULL, valid URL
    published_at: datetime  # NOT NULL
    content: Optional[str]  # NULL on dev tier, populated on business tier

    constraints:
        - url matches /^https?:\/\/.+/
        - published_at <= now()
        - No duplicates: UNIQUE(url)

    provenance:
        source: "NewsAPI.org"
        confidence: "medium" (metadata only on dev tier)
        freshness: Real-time
        tier: "dev" or "business"
```

### NewsAPI Rights & Restrictions

**From** [news_provider.py:70-84](backend/app/integrations/news_provider.py#L70-L84):

**Dev Tier:**
```python
rights={
    "export_pdf": False,        # ❌ BLOCKED
    "export_csv": False,        # ❌ BLOCKED
    "redistribution": False,    # ❌ BLOCKED
    "requires_attribution": True,
    "watermark_required": True,  # ⚠️ Must watermark if showing metadata
    "attribution_text": "News metadata via NewsAPI.org",
}
```

**Business Tier:**
```python
rights={
    "export_pdf": True,         # ✅ ALLOWED
    "export_csv": True,         # ✅ ALLOWED
    "redistribution": True,     # ✅ ALLOWED with attribution
    "requires_attribution": True,
}
```

**Production Recommendation:** Upgrade to Business tier to enable full content storage and export.

---

## Data Flow Architecture

### End-to-End Flow

```
1. USER REQUEST
   └─> UI (React) sends pattern request
       └─> POST /api/v1/patterns/execute

2. PATTERN ORCHESTRATOR
   └─> Loads pattern JSON (e.g., portfolio_cycle_risk.json)
       └─> Executes capability sequence

3. AGENT (DataHarvester)
   └─> Receives capability request (e.g., "provider.fetch_macro")
       └─> Calls provider facade

4. PROVIDER FACADE (e.g., FREDProvider)
   └─> Inherits BaseProvider
       └─> call_with_retry() → Exponential backoff
           └─> Rate limiter check
               └─> HTTP request to external API

5. EXTERNAL API
   └─> FRED, FMP, Polygon, NewsAPI
       └─> Returns JSON response

6. RESPONSE PROCESSING
   └─> Provider normalizes response
       └─> Validates data contract
           └─> Adds provenance metadata
               └─> Returns to agent

7. DATABASE INGESTION
   └─> Agent stores data in database
       └─> INSERT INTO economic_indicators, prices, securities, etc.
           └─> Records lineage (source, timestamp, pack_id)

8. RESPONSE TO USER
   └─> Agent returns result to orchestrator
       └─> Orchestrator merges results
           └─> Returns to UI
```

### Pricing Pipeline Example

```python
# 1. Create pricing pack
pack_id = await create_pricing_pack(asof_date=today())

# 2. Fetch prices from FMP (bulk)
fmp = FMPProvider(api_key=settings.FMP_API_KEY)
portfolio_symbols = ["AAPL", "MSFT", "GOOGL", ...]
quotes = await fmp.get_quote(portfolio_symbols)  # Bulk fetch (100 at a time)

# 3. Insert into prices table
for quote in quotes:
    await db.execute("""
        INSERT INTO prices (security_id, pricing_pack_id, asof_date, close, open, high, low, volume)
        SELECT s.id, $1, $2, $3, $4, $5, $6, $7
        FROM securities s
        WHERE s.symbol = $8
    """, pack_id, today(), quote['price'], quote['open'], ...)

# 4. Fetch corporate actions from Polygon
polygon = PolygonProvider(api_key=settings.POLYGON_API_KEY)
dividends = await polygon.get_dividends(symbol=None, from_date=today() - 7 days)
splits = await polygon.get_splits(symbol=None, from_date=today() - 7 days)

# 5. Insert corporate actions
for div in dividends:
    await db.execute("""
        INSERT INTO corporate_actions (type, symbol, ex_date, amount, pay_date, currency)
        VALUES ('DIVIDEND', $1, $2, $3, $4, $5)
        ON CONFLICT (symbol, type, ex_date) DO NOTHING
    """, div['ticker'], div['ex_dividend_date'], div['cash_amount'], ...)

# 6. Mark pack as complete
await db.execute("UPDATE pricing_packs SET status = 'complete' WHERE pack_id = $1", pack_id)

# 7. Compute portfolio valuations
await backfill_portfolio_values(pack_id)  # Updates portfolio_daily_values table
```

### FRED Ingestion Example

```python
# 1. Fetch factor data
fred = FREDProvider(api_key=settings.FRED_API_KEY)
factor_data = await fred.get_factor_data(
    start_date=today() - timedelta(days=365),
    end_date=today()
)

# 2. Insert into economic_indicators table
for factor_name, series_data in factor_data.items():
    for obs in series_data:
        await db.execute("""
            INSERT INTO economic_indicators (series_id, asof_date, value, unit, source)
            VALUES ($1, $2, $3, $4, 'FRED')
            ON CONFLICT (series_id, asof_date) DO UPDATE
            SET value = EXCLUDED.value, unit = EXCLUDED.unit
        """, obs['series_id'], obs['date'], obs['value'], ...)

# 3. Trigger factor analysis recomputation
await recompute_factor_exposures(portfolio_id, pack_id)
```

---

## Rate Limiting & Circuit Breakers

### Rate Limiter Implementation

**File:** [backend/app/integrations/rate_limiter.py](backend/app/integrations/rate_limiter.py) (assumed)

**Algorithm:** Token Bucket

```python
@rate_limit(requests_per_minute=120)
async def get_quote(symbol: str):
    # Decorator enforces rate limit
    pass
```

**How it works:**
1. Bucket starts with N tokens (e.g., 120 for FMP)
2. Each request consumes 1 token
3. Tokens refill at rate R (e.g., 2 tokens/second for 120/min)
4. If bucket empty, request is delayed until token available
5. Prevents exceeding provider rate limits (avoids 429 errors)

### Circuit Breaker Pattern

**From** [base_provider.py:291-430](backend/app/integrations/base_provider.py#L291-L430):

```python
async def call_with_retry(request: ProviderRequest) -> ProviderResponse:
    for attempt in range(max_retries + 1):  # 0, 1, 2, 3 (4 total attempts)
        try:
            response = await self.call(request)
            return response  # Success

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                retry_after = e.response.headers.get('retry-after')
                await asyncio.sleep(float(retry_after))  # Respect server's delay
                continue

            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) * (1 + random.uniform(-0.2, 0.2))
            # Delays: 1s, 2s, 4s (with ±20% jitter)
            await asyncio.sleep(delay)

    # All retries failed
    cached = await self._get_cached(request)
    if cached:
        return cached.with_stale_flag()  # Serve stale data

    raise ProviderError("All retries failed")
```

**Features:**
- ✅ Respects 429 rate limit responses (retry-after header)
- ✅ Exponential backoff (1s → 2s → 4s)
- ✅ Jitter (±20%) to prevent thundering herd
- ✅ Falls back to cached/stale data on failure
- ✅ Records metrics (Prometheus counters)

### Dead Letter Queue (DLQ)

**From** [base_provider.py:145-238](backend/app/integrations/base_provider.py#L145-L238):

```python
class DeadLetterQueue:
    async def enqueue(request: ProviderRequest, error: str):
        entry = DLQEntry(request=request, error=error, retry_count=0)
        self.queue.append(entry)

        # Background retry task (fire-and-forget)
        asyncio.create_task(self._retry_with_backoff(entry))

    async def _retry_with_backoff(entry: DLQEntry):
        for delay in [1, 2, 4]:  # Retry delays
            await asyncio.sleep(delay * (1 + random.uniform(-0.2, 0.2)))

            try:
                await provider.call(entry.request)  # Retry
                self.queue.remove(entry)  # Success
                return
            except Exception:
                entry.retry_count += 1

        # Max retries exceeded
        self.failed_queue.append(entry)  # Move to failed queue for manual review
```

**Use Case:** Transient failures (network blips, temporary provider outages) get retried in background without blocking user requests.

---

## Data Contracts & Validation

### Contract Pattern

```python
@dataclass
class DataContract:
    name: str
    fields: List[Field]
    constraints: List[Constraint]
    provenance_required: bool
    freshness_max_age: timedelta

@dataclass
class Field:
    name: str
    type: type  # str, int, Decimal, date, datetime
    nullable: bool
    default: Any = None

@dataclass
class Constraint:
    type: str  # "range", "enum", "regex", "unique", "foreign_key"
    field: Optional[str]
    params: Dict[str, Any]
```

### Example: FMP Quote Contract

```python
fmp_quote_contract = DataContract(
    name="fmp_quote",
    fields=[
        Field(name="symbol", type=str, nullable=False),
        Field(name="price", type=Decimal, nullable=False),
        Field(name="timestamp", type=datetime, nullable=False),
        Field(name="volume", type=int, nullable=False),
        Field(name="market_cap", type=Decimal, nullable=False),
    ],
    constraints=[
        Constraint(type="regex", field="symbol", params={"pattern": r"^[A-Z]{1,5}$"}),
        Constraint(type="range", field="price", params={"min": 0, "max": 1e9}),
        Constraint(type="range", field="volume", params={"min": 0, "max": 1e12}),
        Constraint(type="custom", field="timestamp", params={"validator": lambda t: t <= datetime.now()}),
    ],
    provenance_required=True,
    freshness_max_age=timedelta(minutes=15)
)
```

### Validation at Ingestion

```python
async def ingest_quote(quote_data: Dict):
    # 1. Validate contract
    errors = validate_contract(fmp_quote_contract, quote_data)
    if errors:
        logger.error(f"Contract validation failed: {errors}")
        raise ValidationError(errors)

    # 2. Check provenance
    if not quote_data.get('_provenance'):
        logger.warning("Missing provenance metadata")

    # 3. Check freshness
    timestamp = quote_data['timestamp']
    age = datetime.now() - timestamp
    if age > fmp_quote_contract.freshness_max_age:
        logger.warning(f"Stale data: {age} old (max: {fmp_quote_contract.freshness_max_age})")

    # 4. Insert into database
    await db.execute("INSERT INTO prices (...) VALUES (...)", ...)
```

---

## Error Handling & Retry Logic

### Error Hierarchy

```
Exception
 └─> ProviderError (base_provider.py:82)
      ├─> ProviderTimeoutError
      ├─> RateLimitError
      └─> ProviderUnavailableError
```

### Retry Decision Tree

```
API Request
    ↓
Success? ──YES──> Return response
    ↓ NO
Status Code?
    ├─> 429 (Rate Limit)
    │   └─> Check retry-after header
    │       ├─> Has header: Sleep(retry_after)
    │       └─> No header: Exponential backoff
    │
    ├─> 5xx (Server Error)
    │   └─> Exponential backoff (retriable)
    │
    ├─> 4xx (Client Error, non-429)
    │   ├─> 401/403: Do NOT retry (auth issue)
    │   └─> 404: Do NOT retry (not found)
    │
    └─> Timeout / Network Error
        └─> Exponential backoff (retriable)

After max_retries:
    ├─> Has cached data? ──YES──> Return cached.with_stale_flag()
    └─> No cached data? ──NO──> Raise ProviderError
```

### Prometheus Metrics

**From** [base_provider.py:45-74](backend/app/integrations/base_provider.py#L45-L74):

```python
# Counters
provider_requests_total{provider, endpoint, status}  # Total requests
provider_errors_total{provider, endpoint, error_type}  # Total errors
provider_retries_total{provider, endpoint, retry_attempt}  # Total retries

# Histograms
provider_latency_seconds{provider, endpoint}  # Latency distribution

# Gauges
dlq_size{provider}  # Dead letter queue size
```

**Dashboard Queries:**
```promql
# Error rate (last 5min)
sum(rate(provider_errors_total[5m])) by (provider)

# P95 latency
histogram_quantile(0.95, provider_latency_seconds)

# Retry rate
sum(rate(provider_retries_total[5m])) / sum(rate(provider_requests_total[5m]))
```

---

## Provider Rights & Export Restrictions

### Rights Matrix

| Provider | PDF Export | CSV Export | Redistribution | Attribution Required |
|----------|------------|------------|----------------|---------------------|
| **FMP** | ❌ | ❌ | ❌ | ✅ |
| **FRED** | ✅ | ✅ | ✅ | ✅ |
| **Polygon** | ❌ | ❌ | ❌ | ✅ |
| **NewsAPI (Dev)** | ❌ | ❌ | ❌ | ✅ (watermark) |
| **NewsAPI (Business)** | ✅ | ✅ | ✅ | ✅ |

### Pre-Flight Rights Check

**From** [base_provider.py:442-467](backend/app/integrations/base_provider.py#L442-L467):

```python
async def _check_rights(ctx: RequestCtx, action: str):
    if action == "export_pdf":
        if not self.rights.get("export_pdf"):
            raise RightsViolationError(f"{self.name} does not allow PDF export")

    if action == "export_csv":
        if not self.rights.get("export_csv"):
            raise RightsViolationError(f"{self.name} does not allow CSV export")

    if action == "redistribution":
        if not self.rights.get("redistribution"):
            raise RightsViolationError(f"{self.name} does not allow data redistribution")
```

### Attribution Requirements

**UI Implementation:**

```jsx
// Risk Analytics Page
<RiskMetricsChart data={factorExposures} />
<Attribution>
  Economic data: Source: Federal Reserve Economic Data (FRED®), Federal Reserve Bank of St. Louis
  Financial data: © Financial Modeling Prep
</Attribution>
```

**PDF Export (if allowed):**
```python
async def export_pdf(data, ctx):
    # Check rights
    await provider._check_rights(ctx, "export_pdf")

    # Generate PDF with attribution footer
    pdf = generate_pdf(data)
    pdf.add_footer(provider.rights["attribution_text"])

    return pdf
```

---

## Summary

### Key Takeaways

1. **FMP Premium Plan** provides all stock data, fundamentals, and corporate actions
2. **FRED** provides economic indicators for factor analysis (free, export allowed)
3. **Polygon** is primary source for corporate actions (splits, dividends) - critical for ADR accuracy
4. **NewsAPI Dev tier** only provides metadata (no article content) - consider Business tier upgrade
5. **Rate limiting** enforced via token bucket + exponential backoff with jitter
6. **Circuit breaker** pattern with DLQ ensures resilience
7. **Data contracts** define expected schema, constraints, and provenance requirements
8. **Export restrictions** vary by provider - check rights before allowing user downloads

### Production Recommendations

1. ✅ **FMP Premium:** Keep current plan (all features needed)
2. ⚠️ **NewsAPI:** Upgrade to Business tier for full article content and export
3. ✅ **Monitoring:** Set up Prometheus dashboards for provider metrics
4. ✅ **Alerting:** Alert on DLQ size > 10, error rate > 5%, P95 latency > 2s
5. ✅ **Caching:** Implement Redis cache for frequently accessed data (quotes, indicators)
6. ⚠️ **Rate limit headroom:** Monitor actual usage vs limits (FMP: 120/min, FRED: 60/min, Polygon: 100/min)

### Integration Health Checklist

- [ ] All providers return 200 OK for test requests
- [ ] Rate limiters prevent 429 errors
- [ ] DLQ size stays < 5 items
- [ ] Circuit breaker serves stale data on failure
- [ ] Provenance metadata attached to all responses
- [ ] Attribution displayed in UI
- [ ] Export restrictions enforced (FMP, Polygon blocked)
- [ ] Data contracts validated at ingestion
- [ ] Prometheus metrics exported
- [ ] Grafana dashboards configured

---

**Last Updated:** 2025-11-05
**Next Review:** When adding new providers or changing plans
