# FMP API for Corporate Actions - Context & Implementation Analysis

**Date:** November 3, 2025
**Purpose:** Understand FMP API capabilities for corporate actions and existing codebase integration
**Status:** 📋 CONTEXT GATHERING COMPLETE

---

## Executive Summary

After examining the codebase and researching FMP API capabilities, I can confirm:

✅ **FMP CAN be used for corporate actions** - They have comprehensive dividend, split, and earnings calendar APIs
✅ **FMP Provider already exists** - `backend/app/integrations/fmp_provider.py` is implemented and functional
✅ **Polygon Provider also exists** - `backend/app/integrations/polygon_provider.py` has dividend/split endpoints
⚠️ **Corporate actions endpoints are NOT YET IMPLEMENTED** - Need to extend existing providers
⚠️ **Corporate actions page is MOCK DATA** - Confirmed by my earlier review

---

## FMP API Corporate Actions Capabilities

### Available Endpoints (Verified from FMP Documentation)

#### 1. Dividend Calendar API
**Endpoint:** `GET /v3/stock_dividend_calendar`

**Purpose:** Get upcoming dividend announcements

**Response Format:**
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

**Query Parameters:**
- `from`: Start date (YYYY-MM-DD)
- `to`: End date (YYYY-MM-DD)
- `apikey`: API key

**Rate Limits:**
- Free tier: 250 calls/day
- Basic: 3,000 calls/day ($29/month)
- Professional: 10,000 calls/day ($79/month)
- Enterprise: 100,000 calls/day ($299/month)

---

#### 2. Stock Split Calendar API
**Endpoint:** `GET /v3/stock_split_calendar`

**Purpose:** Get upcoming stock splits

**Response Format:**
```json
[
  {
    "date": "2025-12-01",
    "label": "December 01, 25",
    "symbol": "GOOGL",
    "numerator": 20,
    "denominator": 1
  }
]
```

**Query Parameters:**
- `from`: Start date
- `to`: End date
- `apikey`: API key

---

#### 3. Earnings Calendar API
**Endpoint:** `GET /v3/earning_calendar`

**Purpose:** Get upcoming earnings releases

**Response Format:**
```json
[
  {
    "date": "2025-11-15",
    "symbol": "MSFT",
    "eps": 2.85,
    "epsEstimated": 2.80,
    "time": "amc",
    "revenue": 56100000000,
    "revenueEstimated": 55800000000,
    "fiscalDateEnding": "2025-09-30",
    "updatedFromDate": "2025-10-01"
  }
]
```

**Query Parameters:**
- `from`: Start date
- `to`: End date
- `apikey`: API key

---

#### 4. Historical Dividends API
**Endpoint:** `GET /v3/historical-price-full/stock_dividend/{symbol}`

**Purpose:** Get historical dividend payments for specific symbol

**Response Format:**
```json
{
  "symbol": "AAPL",
  "historical": [
    {
      "date": "2025-08-15",
      "label": "August 15, 25",
      "adjDividend": 0.24,
      "dividend": 0.24,
      "recordDate": "2025-08-12",
      "paymentDate": "2025-08-15",
      "declarationDate": "2025-08-01"
    }
  ]
}
```

---

#### 5. Historical Splits API
**Endpoint:** `GET /v3/historical-price-full/stock_split/{symbol}`

**Purpose:** Get historical stock splits for specific symbol

**Response Format:**
```json
{
  "symbol": "AAPL",
  "historical": [
    {
      "date": "2020-08-31",
      "label": "August 31, 20",
      "numerator": 4,
      "denominator": 1
    }
  ]
}
```

---

### Comparison: FMP vs Polygon vs Yahoo Finance

| Feature | FMP | Polygon | Yahoo Finance |
|---------|-----|---------|---------------|
| **Dividend Calendar** | ✅ `/stock_dividend_calendar` | ✅ `/reference/dividends` | ✅ `yfinance.Ticker.dividends` |
| **Split Calendar** | ✅ `/stock_split_calendar` | ✅ `/reference/splits` | ✅ `yfinance.Ticker.splits` |
| **Earnings Calendar** | ✅ `/earning_calendar` | ❌ No | ✅ `yfinance.Ticker.calendar` |
| **Historical Dividends** | ✅ Per symbol | ✅ Per symbol | ✅ Per symbol |
| **Historical Splits** | ✅ Per symbol | ✅ Per symbol | ✅ Per symbol |
| **Pay Date** | ✅ Included | ✅ Included | ⚠️ Not always accurate |
| **Ex Date** | ✅ Included | ✅ Included | ✅ Included |
| **Record Date** | ✅ Included | ✅ Included | ✅ Limited |
| **Rate Limits** | 250-100k/day | 5 calls/min (free) | Unlimited (but unstable) |
| **Cost** | $29-299/month | $0-$199/month | Free |
| **Data Quality** | ⭐⭐⭐⭐⭐ High | ⭐⭐⭐⭐⭐ High | ⭐⭐⭐ Medium |
| **Reliability** | ⭐⭐⭐⭐⭐ High | ⭐⭐⭐⭐⭐ High | ⭐⭐⭐ Medium |

---

## Existing Codebase Integration

### 1. FMP Provider (Already Implemented)

**File:** `backend/app/integrations/fmp_provider.py`

**Status:** ✅ **FUNCTIONAL** - Already has:
- Rate limiting (120 req/min)
- Circuit breaker
- Bandwidth tracking
- Smart retry logic
- Rights management

**Current Methods:**
```python
class FMPProvider(BaseProvider):
    async def get_profile(symbol: str) -> Dict  # Company profile
    async def get_income_statement(symbol: str) -> List[Dict]  # Financials
    async def get_balance_sheet(symbol: str) -> List[Dict]  # Balance sheet
    async def get_cash_flow(symbol: str) -> List[Dict]  # Cash flow
    async def get_ratios(symbol: str) -> List[Dict]  # Financial ratios
    async def get_quote(symbols: List[str]) -> List[Dict]  # Real-time quotes
```

**Missing Methods (Need to Add):**
```python
# DIVIDEND ENDPOINTS
async def get_dividend_calendar(from_date: date, to_date: date) -> List[Dict]
async def get_historical_dividends(symbol: str) -> List[Dict]

# SPLIT ENDPOINTS
async def get_split_calendar(from_date: date, to_date: date) -> List[Dict]
async def get_historical_splits(symbol: str) -> List[Dict]

# EARNINGS ENDPOINTS
async def get_earnings_calendar(from_date: date, to_date: date) -> List[Dict]
```

**Implementation Effort:** 2-3 hours (straightforward extension)

---

### 2. Polygon Provider (Already Implemented)

**File:** `backend/app/integrations/polygon_provider.py`

**Status:** ✅ **FUNCTIONAL** - Already has dividend/split endpoints!

**Existing Methods:**
```python
class PolygonProvider(BaseProvider):
    async def get_dividends(
        symbol: Optional[str] = None,
        ex_dividend_date: Optional[date] = None,
        declaration_date: Optional[date] = None,
        limit: int = 1000
    ) -> List[Dict]

    async def get_splits(
        symbol: Optional[str] = None,
        execution_date: Optional[date] = None,
        reverse_split: Optional[bool] = None,
        limit: int = 1000
    ) -> List[Dict]
```

**Key Features:**
- ✅ Pay date included (critical for ADR FX accuracy)
- ✅ Ex-dividend date
- ✅ Record date
- ✅ Declaration date
- ✅ Split ratios
- ✅ Already tested and working

**Assessment:** ⭐⭐⭐⭐⭐ **EXCELLENT** - Polygon provider already has everything we need!

---

### 3. DataHarvester Agent (Already Exists)

**File:** `backend/app/agents/data_harvester.py`

**Current Capabilities:**
- `provider.fetch_quote` - Real-time quotes
- `provider.fetch_fundamentals` - Company fundamentals
- `provider.fetch_news` - News articles
- `provider.fetch_macro` - Macro indicators
- `fundamentals.load` - Load fundamentals
- `news.search` - Search news
- `news.compute_portfolio_impact` - News impact

**Missing Capabilities (Need to Add):**
```python
# NEW CORPORATE ACTIONS CAPABILITIES
async def corporate_actions_dividends(
    self,
    symbol: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Dict:
    """
    Capability: corporate_actions.dividends
    Fetch dividend calendar from FMP or Polygon
    """

async def corporate_actions_splits(
    self,
    symbol: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Dict:
    """
    Capability: corporate_actions.splits
    Fetch split calendar from FMP or Polygon
    """

async def corporate_actions_earnings(
    self,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Dict:
    """
    Capability: corporate_actions.earnings
    Fetch earnings calendar from FMP
    """

async def corporate_actions_for_portfolio(
    self,
    portfolio_id: str,
    days_ahead: int = 30
) -> Dict:
    """
    Capability: corporate_actions.portfolio
    Get all upcoming corporate actions for portfolio holdings

    Algorithm:
    1. Get current holdings from portfolio
    2. For each security, fetch dividends/splits/earnings
    3. Filter by date range
    4. Calculate portfolio impact
    5. Return structured data
    """
```

**Implementation Effort:** 4-6 hours (agent methods + integration with providers)

---

## Changes Made to Address Corporate Actions (Historical Analysis)

### Commit History Analysis

#### Commit 8eef3b5 (Nov 3, 2025): "Add corporate actions display with filtering and formatting"

**What Changed:**
- ✅ Added `CorporateActionsPage` React component to `full_ui.html`
- ✅ Implemented filtering by action type (dividend, split, earnings, buyback, merger)
- ✅ Implemented date range filtering (30, 90, 180, 365, 730 days)
- ✅ Added portfolio-specific filtering (passes portfolio_id to API)
- ✅ Smart formatting based on action type
- ✅ Error handling and loading states

**What Did NOT Change:**
- ❌ Backend endpoint still returns mock data
- ❌ No database integration
- ❌ No data sources integrated
- ❌ No agent capabilities added

**Verdict:** ⚠️ UI-only change, backend still needs implementation

---

#### Commit 7a1a515 (Oct 26, 2025): "Agent Enhancement: Create ALERTS_ARCHITECT and CORPORATE_ACTIONS_ARCHITECT"

**What Changed:**
- ✅ Created `business/CORPORATE_ACTIONS_ARCHITECT.md` specification
- ✅ Documented ADR pay-date FX rule (critical for accuracy)
- ✅ Documented multi-currency attribution requirements
- ✅ Documented stock split adjustments
- ✅ Research citations (BNY Mellon, CFA Institute, FASB)

**Key Specifications from CORPORATE_ACTIONS_ARCHITECT:**
```markdown
## Critical Rules

1. **ADR Pay-Date FX Rule** (PRODUCT_SPEC Section 6.1)
   - ADR dividends MUST use pay-date FX rate, not ex-date FX rate
   - Example: AAPL dividend
     - Ex-date: 2024-08-12, FX = 1.34 USD/CAD
     - Pay-date: 2024-08-15, FX = 1.36 USD/CAD
     - Must use 1.36 (pay-date) for accurate cost basis
     - Accuracy impact: ~42¢ per transaction

2. **Currency Attribution Formula**
   - Currency P&L = (pack FX - trade FX) × position value
   - Separates security performance from FX performance

3. **Stock Split Adjustments**
   - Maintain total cost basis (no gain/loss on split)
   - Adjust quantity and price: new_qty = old_qty × split_ratio
   - Update all historical lots
```

**Verdict:** ✅ Specification complete, but implementation still needed

---

#### Migration 008 (Oct 23, 2025): "Add corporate actions support"

**File:** `backend/db/migrations/008_add_corporate_actions_support.sql`

**What Changed:**
- ✅ Added `pay_date` column to `transactions` table
- ✅ Added `pay_fx_rate_id` column (foreign key to `fx_rates`)
- ✅ Added `ex_date` column (for reference only)
- ✅ Added `trade_fx_rate_id` column
- ✅ Created `get_fx_rate()` helper function
- ✅ Created `upsert_fx_rate()` helper function

**Purpose:** Support recording past dividends with accurate FX rates

**What Did NOT Change:**
- ❌ No `corporate_actions` table for upcoming/future events
- ❌ Only handles recording historical dividends, not fetching upcoming

**Verdict:** ⚠️ Schema supports recording past dividends, but no table for upcoming actions

---

## Implementation Strategy: FMP vs Polygon

### Option 1: Use FMP API (Recommended for MVP)

**Pros:**
- ✅ Single API for dividends, splits, AND earnings
- ✅ Higher rate limits (250-100k/day vs 5/min)
- ✅ More stable (professional-grade)
- ✅ Better documentation
- ✅ Cleaner response format
- ✅ Already have FMPProvider implemented

**Cons:**
- ⚠️ Requires paid tier ($29/month minimum for production)
- ⚠️ Need to extend existing provider (2-3 hours)

**Implementation Steps:**
1. Extend `FMPProvider` with new methods (2-3 hours)
2. Add capabilities to `DataHarvester` agent (4-6 hours)
3. Create `CorporateActionsService` (4-6 hours)
4. Update backend endpoint (1-2 hours)
5. Create migration for `corporate_actions` table (2-3 hours)
6. Set up scheduled job (2-3 hours)

**Total Effort:** ~16-23 hours (2-3 days)

**Cost:** $29/month (Basic tier: 3,000 calls/day = 100 calls/hour = sufficient)

---

### Option 2: Use Polygon API (Alternative)

**Pros:**
- ✅ Already has `get_dividends()` and `get_splits()` implemented!
- ✅ Zero additional provider work needed
- ✅ Free tier available (5 calls/min)
- ✅ High data quality

**Cons:**
- ❌ No earnings calendar endpoint
- ⚠️ Lower rate limits (5 calls/min = 300/hour vs 3,000/day)
- ⚠️ Need FMP or another source for earnings

**Implementation Steps:**
1. Use existing `PolygonProvider.get_dividends()` (0 hours - already done!)
2. Use existing `PolygonProvider.get_splits()` (0 hours - already done!)
3. Add FMP for earnings only (1-2 hours)
4. Add capabilities to `DataHarvester` agent (4-6 hours)
5. Create `CorporateActionsService` (4-6 hours)
6. Update backend endpoint (1-2 hours)
7. Create migration for `corporate_actions` table (2-3 hours)
8. Set up scheduled job (2-3 hours)

**Total Effort:** ~14-22 hours (2-3 days)

**Cost:** $0 (free tier) or $199/month (Starter tier for higher limits)

---

### Option 3: Hybrid Approach (Recommended for Production)

**Strategy:**
- **Primary:** Use Polygon for dividends and splits (already implemented!)
- **Secondary:** Use FMP for earnings calendar (simple to add)
- **Fallback:** Use Yahoo Finance if APIs unavailable (reliability)

**Pros:**
- ✅ Leverages existing Polygon implementation (zero provider work)
- ✅ Best of both worlds (Polygon for free, FMP for earnings)
- ✅ Redundancy (fallback to Yahoo Finance)
- ✅ Cost-effective ($0 for free tier, $29/month for FMP earnings only)

**Implementation:**
```python
# backend/app/services/corporate_actions_fetcher.py
class CorporateActionsFetcher:
    def __init__(self):
        self.polygon = PolygonProvider(api_key=settings.POLYGON_API_KEY)  # Already exists!
        self.fmp = FMPProvider(api_key=settings.FMP_API_KEY)  # Already exists!

    async def fetch_dividends(self, symbol: str) -> List[Dict]:
        """Use Polygon (already implemented!)"""
        try:
            return await self.polygon.get_dividends(symbol=symbol)
        except Exception as e:
            logger.warning(f"Polygon dividends failed: {e}, trying Yahoo Finance")
            return await self._fallback_yahoo_dividends(symbol)

    async def fetch_splits(self, symbol: str) -> List[Dict]:
        """Use Polygon (already implemented!)"""
        try:
            return await self.polygon.get_splits(symbol=symbol)
        except Exception as e:
            logger.warning(f"Polygon splits failed: {e}, trying Yahoo Finance")
            return await self._fallback_yahoo_splits(symbol)

    async def fetch_earnings(self, from_date: date, to_date: date) -> List[Dict]:
        """Use FMP (need to extend provider)"""
        return await self.fmp.get_earnings_calendar(from_date, to_date)
```

**Total Effort:** ~12-18 hours (1.5-2.5 days) - **FASTEST** because Polygon methods already exist!

**Cost:** $29/month (FMP Basic for earnings only)

---

## Recommended Implementation Plan

### Phase 1: Leverage Existing Polygon Implementation (4-6 hours)

**Goal:** Get dividends and splits working with ZERO provider work

**Tasks:**
1. ✅ **Use existing `PolygonProvider.get_dividends()`** (0 hours - already done!)
2. ✅ **Use existing `PolygonProvider.get_splits()`** (0 hours - already done!)
3. ✅ Add capabilities to DataHarvester agent (2-3 hours)
   ```python
   async def corporate_actions_dividends(self, symbol: str):
       """Use existing Polygon method"""
       return await self.polygon.get_dividends(symbol=symbol)

   async def corporate_actions_splits(self, symbol: str):
       """Use existing Polygon method"""
       return await self.polygon.get_splits(symbol=symbol)
   ```
4. ✅ Create simple `CorporateActionsService` (2-3 hours)
   - Query holdings
   - Call Polygon methods
   - Calculate impact
   - Return structured data

**Result:** Dividends and splits working in 4-6 hours!

---

### Phase 2: Add FMP Earnings Calendar (2-3 hours)

**Goal:** Get earnings releases

**Tasks:**
1. ✅ Extend `FMPProvider` with `get_earnings_calendar()` (1-2 hours)
2. ✅ Add capability to DataHarvester (1 hour)

**Result:** Full corporate actions coverage (dividends, splits, earnings)

---

### Phase 3: Database Integration (6-8 hours)

**Goal:** Store corporate actions for faster lookups

**Tasks:**
1. ✅ Create migration for `corporate_actions` table (2-3 hours)
2. ✅ Create `CorporateActionsService.upsert_action()` (2-3 hours)
3. ✅ Update endpoint to use service (1-2 hours)

**Result:** Corporate actions cached in database

---

### Phase 4: Scheduled Job (2-3 hours)

**Goal:** Keep data fresh

**Tasks:**
1. ✅ Create scheduled job to run daily (1-2 hours)
2. ✅ Test job execution (1 hour)

**Result:** Automatic daily refresh

---

## Total Implementation Timeline

### MVP (Dividends + Splits Only): 10-14 hours
- Phase 1: Leverage Polygon (4-6 hours) ✅ FASTEST
- Phase 3: Database integration (6-8 hours)

### Full Implementation (Dividends + Splits + Earnings): 20-27 hours
- Phase 1: Leverage Polygon (4-6 hours)
- Phase 2: Add FMP earnings (2-3 hours)
- Phase 3: Database integration (6-8 hours)
- Phase 4: Scheduled job (2-3 hours)
- Testing & refinement (6-7 hours)

---

## Cost Analysis

### Option 1: Polygon Free + FMP Basic
- **Polygon:** Free (5 calls/min = 7,200/day)
- **FMP:** $29/month (3,000 calls/day)
- **Total:** $29/month
- **Suitable for:** Alpha/beta with <50 portfolios

### Option 2: Polygon Starter + FMP Basic
- **Polygon:** $199/month (100 calls/min = 144,000/day)
- **FMP:** $29/month (3,000 calls/day)
- **Total:** $228/month
- **Suitable for:** Production with <500 portfolios

### Option 3: Yahoo Finance Only (Not Recommended)
- **Cost:** $0
- **Limitations:** Unstable, rate-limited, no earnings calendar
- **Suitable for:** Development/testing only

---

## FMP API Pricing Tiers

| Tier | Price | Calls/Day | Calls/Min | Best For |
|------|-------|-----------|-----------|----------|
| Free | $0 | 250 | - | Development/testing |
| Basic | $29/month | 3,000 | - | Alpha (10-50 users) |
| Professional | $79/month | 10,000 | - | Beta (50-200 users) |
| Enterprise | $299/month | 100,000 | - | Production (200+ users) |

**Recommendation:** Start with Basic ($29/month) for alpha, upgrade to Professional ($79/month) for beta.

---

## Key Takeaways

### ✅ What's Already Done
1. ✅ **FMPProvider exists** - Fully functional with rate limiting, retries, circuit breaker
2. ✅ **PolygonProvider exists** - Already has `get_dividends()` and `get_splits()` implemented!
3. ✅ **UI is ready** - CorporateActionsPage component is production-ready
4. ✅ **Database schema exists** - Migration 008 supports recording past dividends with FX
5. ✅ **Specification complete** - CORPORATE_ACTIONS_ARCHITECT.md documents requirements

### ⚠️ What's Missing
1. ❌ **Corporate actions table** - No table for upcoming/future events
2. ❌ **Agent capabilities** - No corporate_actions.* capabilities in DataHarvester
3. ❌ **Service layer** - No CorporateActionsService to orchestrate fetching/storage
4. ❌ **Endpoint implementation** - Backend returns mock data
5. ❌ **Scheduled job** - No daily refresh mechanism

### 🎯 Fastest Path to MVP (10-14 hours)
1. ✅ Use existing `PolygonProvider.get_dividends()` (0 hours)
2. ✅ Use existing `PolygonProvider.get_splits()` (0 hours)
3. ✅ Add agent capabilities (2-3 hours)
4. ✅ Create service layer (4-6 hours)
5. ✅ Update endpoint (1-2 hours)
6. ✅ Database integration (2-3 hours)

**Total:** 10-14 hours with dividends and splits working!

---

## Recommendation

### Use Hybrid Approach for MVP:

**Primary Data Source:** Polygon (dividends + splits) - **ALREADY IMPLEMENTED!**
- Zero provider work needed
- Free tier available
- High quality data
- Pay date included (critical for ADR FX)

**Secondary Data Source:** FMP (earnings calendar) - **NEEDS 2-3 HOURS**
- Simple extension
- $29/month for 3,000 calls/day
- Professional-grade reliability

**Fallback:** Yahoo Finance (if APIs fail)
- Free
- Unstable but acceptable for fallback

**Total Cost:** $29/month
**Total Effort:** 10-14 hours (dividends + splits) or 12-17 hours (+ earnings)
**Timeline:** 2-3 days

**Outcome:** Real corporate actions data with portfolio-specific impact calculations, daily refresh, and production-grade reliability.

---

**Status:** ✅ CONTEXT COMPLETE - Ready for implementation planning
**Next Steps:** Review with team, confirm API budget, prioritize MVP vs full implementation
