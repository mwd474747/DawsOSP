# DawsOS Data Flow Integration Analysis

**Created:** 2025-11-05
**Analyzed By:** Claude (Sonnet 4.5)
**Purpose:** Complete analysis of data flow from external APIs through to the UI

---

## Executive Summary

This report analyzes the complete data flow pipeline in DawsOS, from external API providers through the backend services to the frontend UI. The analysis reveals a well-architected system with **one critical bug**, several **inconsistencies**, and **missing UI-backend integration points**.

### Key Findings

**Critical Issues:**
- 🚨 **CRITICAL BUG**: MacroService calls `get_series_observations()` but FREDProvider only implements `get_series()` - This will cause runtime errors

**High Priority:**
- ⚠️ UI has no error handling for stale data responses
- ⚠️ Pattern execution errors not displayed to user
- ⚠️ No freshness indicators in UI

**Medium Priority:**
- Different error handling patterns across providers
- Inconsistent data transformation approaches
- Documentation doesn't match implementation

---

## 1. Data Flow Map

### Complete Data Pipeline

```
External APIs (FMP, FRED, Polygon, NewsAPI)
    ↓
Provider Layer (FMPProvider, FREDProvider, etc.)
    ↓ [_request() consolidated in BaseProvider]
BaseProvider (retry logic, rate limiting, caching)
    ↓
Agent Layer (DataHarvester)
    ↓ [Normalizes provider responses]
Service Layer (MacroService, CorporateActionsService)
    ↓ [Business logic, database queries]
Database (PostgreSQL + TimescaleDB)
    ↓
API Layer (FastAPI routes)
    ↓ [JSON serialization]
Frontend (api-client.js → axios)
    ↓
UI Components
```

### Provider-Specific Flows

#### FMP Flow (Working ✅)
```
FMP API
  ↓ FMPProvider.get_quote([symbols])
  ↓ BaseProvider._request("GET", url, params)
  ↓ DataHarvester.provider_fetch_quote()
  ↓ {symbol, price, volume, market_cap}
  ↓ prices table (via pricing pipeline)
  ↓ API: GET /api/holdings
  ↓ Frontend: apiClient.getHoldings()
  ↓ UI: Holdings table
```

#### FRED Flow (BROKEN 🚨)
```
FRED API
  ↓ FREDProvider.get_series(series_id)  ← Returns List[Dict]
  ↓ MacroService.fetch_indicators()
      ↓ self.fred_client.get_series_observations()  ← METHOD DOESN'T EXIST
  ↓ ❌ RUNTIME ERROR: AttributeError
```

**Root Cause:** Method name mismatch
- **Provider has:** `get_series()`
- **Service calls:** `get_series_observations()`
- **Impact:** All macro regime detection broken

#### Corporate Actions Flow (Working ✅)
```
FMP API /v3/stock_dividend_calendar
  ↓ FMPProvider.get_dividend_calendar(from_date, to_date)
  ↓ DataHarvester.corporate_actions_dividends()
  ↓ Filters by portfolio symbols
  ↓ Normalizes format (adjDividend → amount)
  ↓ API: POST /v1/corporate-actions/dividends
  ↓ CorporateActionsService.record_dividend()
  ↓ transactions table (with pay_date FX rate)
  ↓ Frontend: No UI implemented yet
```

#### News Flow (Working but Limited ✅)
```
NewsAPI /v2/everything
  ↓ NewsAPIProvider.search(query)
  ↓ Filters content based on tier (dev = metadata only)
  ↓ DataHarvester.provider_fetch_news()
  ↓ Transforms to DawsOS format
  ↓ Returns to pattern (NOT stored in database)
  ↓ API: Pattern response includes news
  ↓ Frontend: No UI component to display news
```

---

## 2. Integration Analysis by Provider

### FMP (Financial Modeling Prep)

#### ✅ What Works Correctly

**Quotes:**
- Method: `get_quote(symbols: List[str])`
- Used by: DataHarvester.provider_fetch_quote()
- Database: prices table
- UI: Holdings table, Portfolio value
- Status: **WORKING**

**Fundamentals:**
- Methods: `get_income_statement()`, `get_balance_sheet()`, `get_cash_flow()`, `get_ratios()`
- Used by: DataHarvester.provider_fetch_fundamentals()
- Database: Not stored (returned directly to patterns)
- UI: No UI component yet
- Status: **WORKING** (but unused)

**Corporate Actions:**
- Methods: `get_dividend_calendar()`, `get_split_calendar()`, `get_earnings_calendar()`
- Used by: DataHarvester (corporate_actions_dividends, splits, earnings)
- Database: corporate_actions table (via API, not direct)
- UI: No UI component
- Status: **WORKING** (backend only)

#### ⚠️ What Has Gaps or Issues

**Issue 1: Profile data not persisted**
```python
# FMPProvider.get_profile() returns rich company data
{
    "companyName": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "ceo": "Timothy Cook",
    "description": "...",
    "employees": 161000
}

# But this data is NOT stored in securities table
# Gap: Securities table only has symbol, name, currency
# Recommendation: Create security_metadata table or expand securities
```

**Issue 2: Bulk quote limit not enforced**
```python
# FMPProvider.get_quote() has validation:
if len(symbols) > 100:
    raise ValueError(...)

# But DataHarvester calls it with single symbol always:
quotes = await provider_client.get_quote([symbol])  # Inefficient

# Recommendation: Batch quotes for multiple securities
```

**Issue 3: Rate limiting not coordinated**
```python
# Each method has @rate_limit(requests_per_minute=120)
# But rate limit is PER METHOD, not PER PROVIDER
# If get_quote() uses 60 req/min and get_profile() uses 60 req/min
# Total = 120 req/min ✅ CORRECT

# Current implementation: Token bucket per method ✅ GOOD
```

#### 🚨 What is Broken

**None - FMP integration is solid**

---

### FRED (Federal Reserve Economic Data)

#### ✅ What Works Correctly

**Nothing - see broken section**

#### ⚠️ What Has Gaps or Issues

**Issue 1: Missing metadata storage**
```python
# FREDProvider.get_series_info() returns rich metadata:
{
    "title": "Consumer Price Index...",
    "observation_start": "1947-01-01",
    "frequency": "Monthly",
    "units": "Index 1982-1984=100",
    "seasonal_adjustment": "Seasonally Adjusted"
}

# But MacroService.store_indicator() only stores:
# series_id, date, value, source
# Missing: units, frequency, title

# Impact: UI can't show "what is this indicator?"
```

**Issue 2: Transformation applied twice**
```python
# MacroService.fetch_indicators() line 655:
transformed_value = self.transformation_service.transform_fred_value(...)

# But FRED provider already returns clean data
# Question: Why transform after fetching?
# Answer: For YoY calculations and rate of change

# Status: ✅ CORRECT but needs documentation
```

#### 🚨 What is Broken

**CRITICAL BUG: Method name mismatch**

**File:** `/backend/app/services/macro.py` line 609

```python
# MacroService calls:
observations = await self.fred_client.get_series_observations(
    series_id=indicator_id,
    start_date=start_date.isoformat(),
    end_date=asof_date.isoformat(),
)

# But FREDProvider only has:
async def get_series(self, series_id, start_date, end_date):
    # Returns List[Dict] with {date, value, series_id}
```

**Impact:**
- ❌ All calls to MacroService.fetch_indicators() will fail with `AttributeError`
- ❌ Macro regime detection broken
- ❌ DaR calculations broken
- ❌ Scenario analysis broken

**Fix:**
Change line 609 in `macro.py`:
```python
# OLD (BROKEN):
observations = await self.fred_client.get_series_observations(...)

# NEW (FIXED):
observations = await self.fred_client.get_series(...)
```

**Root Cause Analysis:**
- FREDProvider was recently refactored (2025-10-21)
- Method was renamed from `get_series_observations()` to `get_series()`
- MacroService was not updated
- No integration tests caught this

---

### Polygon

#### ✅ What Works Correctly

**Historical prices:**
- Method: `get_daily_prices(symbol, start_date, end_date)`
- Used by: DataHarvester (for historical backfill)
- Database: prices table
- Status: **WORKING**

#### ⚠️ What Has Gaps or Issues

**Issue 1: Corporate actions methods exist but unused**
```python
# Polygon provider has these methods (lines 169-178):
# - get_dividends() [REMOVED - see comment]
# - get_splits() [REMOVED - see comment]

# Comment says: "NOTE: Corporate actions methods removed in favor of FMP"

# But documentation (provider-database-mapping.md) says:
# "Corporate Actions: 1. Primary (ACTIVE): FMP, 2. Backup (NOT IMPLEMENTED): Polygon"

# Gap: Documentation is outdated
# Recommendation: Update documentation to match reality
```

**Issue 2: Split-adjusted only, not dividend-adjusted**
```python
# Polygon prices are split-adjusted but NOT dividend-adjusted
# Comment in polygon_provider.py line 288:
# "Important: Polygon prices are split-adjusted only"

# Impact: Total return calculations need separate dividend adjustment
# Status: ✅ Documented, but not validated in code

# Recommendation: Add validation in pricing pipeline
```

---

### NewsAPI

#### ✅ What Works Correctly

**Search with tier filtering:**
- Method: `search(query, from_date, to_date)`
- Tier handling: Dev tier filters out content (metadata only)
- Used by: DataHarvester.provider_fetch_news()
- Status: **WORKING**

**Rights enforcement:**
```python
# Dev tier:
rights = {
    "export_pdf": False,
    "export_csv": False,
    "watermark_required": True
}

# Correctly filters content field in search() method
```

#### ⚠️ What Has Gaps or Issues

**Issue 1: News not stored in database**
```python
# News is fetched on-demand but not persisted
# Impact: Can't show historical news trends
# Impact: Can't correlate news with portfolio moves
# Recommendation: Create news_articles table with metadata only (dev tier)
```

**Issue 2: No UI component**
```python
# Backend returns news in pattern response
# But frontend has no component to display it
# Gap: UI-backend disconnect
```

---

## 3. Gap Analysis

### Missing Database → Service Integration

**Gap 1: FRED metadata not stored**
```sql
-- Current: macro_indicators table
CREATE TABLE macro_indicators (
    indicator_id VARCHAR(50),
    date DATE,
    value NUMERIC,
    source VARCHAR(50)
);

-- Missing: indicator metadata
-- Recommendation: Add indicator_metadata table
CREATE TABLE indicator_metadata (
    indicator_id VARCHAR(50) PRIMARY KEY,
    title TEXT,
    units VARCHAR(100),
    frequency VARCHAR(20),
    seasonal_adjustment VARCHAR(50),
    last_updated TIMESTAMPTZ
);
```

**Gap 2: Corporate actions not linked to transactions**
```sql
-- Current: corporate_actions table exists
-- But: Not used by CorporateActionsService
-- Service creates transactions directly

-- Impact: No audit trail of "what corporate action caused this transaction?"
-- Recommendation: Add corporate_action_id to transactions table
```

**Gap 3: News not persisted**
```sql
-- Missing: news_articles table
-- Recommendation:
CREATE TABLE news_articles (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    source VARCHAR(100),
    symbols TEXT[],  -- Array of related symbols
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Missing Service → API Integration

**Gap 1: Macro regime not exposed**
```python
# MacroService.detect_current_regime() exists
# API route exists: GET /api/v1/macro/regime
# But: No frontend call to this endpoint

# Frontend api-client.js has:
getMacro: async () => axios.get('/api/macro')

# But this endpoint doesn't exist!
# Should be: GET /api/v1/macro/indicators
```

**Gap 2: Corporate actions API not called**
```python
# API exists: POST /v1/corporate-actions/dividends
# But: No frontend method to call it
# Gap: Manual dividend entry not implemented in UI
```

**Gap 3: Pattern errors not surfaced**
```python
# Pattern execution can return errors:
{
    "error": "FRED API error: ...",
    "status": "error"
}

# But frontend executePattern() only checks:
if (response.data) { ... }

# Missing: Error handling for pattern failures
```

### Missing API → Frontend Integration

**Gap 1: Stale data indicators**
```python
# Backend can return stale data:
ProviderResponse(stale=True, cached=True)

# But frontend has no UI indicator for stale data
# User doesn't know if data is fresh or stale

# Recommendation: Add staleness badge in UI
```

**Gap 2: Rate limit errors not handled**
```javascript
// Backend returns 429 with retry-after header
// Frontend axios interceptor doesn't handle 429
// Recommendation: Add retry logic for 429 with delay
```

**Gap 3: Freshness requirements**
```javascript
// Backend has:
POST /v1/execute { require_fresh: true }

// Returns 503 if pack not fresh

// Frontend executePattern() doesn't pass require_fresh
// Always defaults to false

// Impact: UI might show stale data without user knowing
```

---

## 4. Pattern Inconsistencies

### Error Handling Inconsistencies

**Pattern 1: Provider-level errors**
```python
# FMPProvider:
try:
    response = await self._request(...)
    if isinstance(response, list) and len(response) > 0:
        return response[0]
    else:
        raise ProviderError("Unexpected response format")
except httpx.HTTPStatusError as e:
    # Handled by BaseProvider retry logic
    raise

# FREDProvider:
response = await self._request(...)
if "error_code" in response:
    raise ProviderError(f"FRED API error: ...")
observations = response.get("observations", [])
return series_data  # Empty list if no observations

# Inconsistency: FMP raises on unexpected format, FRED returns empty
# Recommendation: Standardize - always raise on error
```

**Pattern 2: Service-level errors**
```python
# MacroService.fetch_indicators():
try:
    observations = await self.fred_client.get_series(...)
    # Process observations
    results[indicator_id] = indicators
except Exception as e:
    logger.error(f"Failed to fetch {indicator_id}: {e}")
    results[indicator_id] = []  # Empty list on error

# CorporateActionsService.record_dividend():
try:
    result = await service.record_dividend(...)
    return DividendResponse(**result)
except InsufficientDataError as e:
    raise HTTPException(status_code=400, detail=str(e))
except InvalidCorporateActionError as e:
    raise HTTPException(status_code=400, detail=str(e))

# Inconsistency: Macro returns empty on error, CorporateActions raises HTTP
# Recommendation: Macro should raise, not return empty
```

**Pattern 3: Frontend error handling**
```javascript
// Pattern 1: executePattern()
catch (error) {
    return apiClient.handleApiCallError(`Pattern execution '${patternName}'`, error);
}
// Throws enhanced error

// Pattern 2: getHoldings()
catch (error) {
    return apiClient.handleApiCallError('Fetch holdings', error);
}
// Throws enhanced error

// Pattern 3: getMacro()
catch (error) {
    return apiClient.handleApiCallError('Fetch macro data', error);
}
// Throws enhanced error

// Consistency: ✅ GOOD - all use same error handler
```

### Data Transformation Inconsistencies

**Pattern 1: Date formats**
```python
# FMP returns: "timestamp": 1698345600 (Unix epoch)
# FRED returns: "date": "2024-01-01" (ISO string)
# Polygon returns: "t": 1704153600000 (Unix epoch ms)

# Normalization:
# FMP: datetime.fromtimestamp(quote.get("timestamp"))
# FRED: datetime.strptime(obs["date"], "%Y-%m-%d")
# Polygon: datetime.fromtimestamp(bar["t"] / 1000)

# Inconsistency: Different date formats, different parsing
# Recommendation: ✅ CORRECT - providers handle their own format
```

**Pattern 2: Field naming**
```python
# FMP returns: companyName, marketCap, changesPercentage
# FRED returns: series_id, value, observation_date
# Polygon returns: c (close), o (open), h (high), l (low)

# Normalization:
# FMP: Maps to {symbol, price, change_pct, market_cap}
# FRED: Maps to {series_id, value, date}
# Polygon: Maps to {close: bar["c"], open: bar["o"], ...}

# Inconsistency: Different snake_case/camelCase conventions
# Recommendation: ✅ ACCEPTABLE - agents normalize to DawsOS format
```

### Caching Inconsistencies

**Pattern 1: Provider-level caching**
```python
# BaseProvider has built-in caching:
async def _cache_response(self, request, response):
    cache_key = f"{request.endpoint}:{request.params}"
    self._cache[cache_key] = response

# All providers inherit this
# ✅ CONSISTENT
```

**Pattern 2: Agent-level caching**
```python
# DataHarvester attaches metadata with TTL:
metadata = self._create_metadata(
    source="provider:fmp:quote",
    asof=ctx.asof_date,
    ttl=self.CACHE_TTL_5MIN  # 5 minutes for quotes
)

metadata = self._create_metadata(
    source="provider:fred:series",
    asof=ctx.asof_date,
    ttl=self.CACHE_TTL_HOUR  # 1 hour for macro
)

# Different TTLs for different data types
# ✅ CORRECT - reflects data freshness requirements
```

**Pattern 3: Service-level caching**
```python
# MacroService: No caching (always fetches from DB)
# CorporateActionsService: No caching (always fetches from DB)

# Question: Should services cache?
# Answer: No - services should be stateless
# Caching should be at provider or database level
# ✅ CORRECT
```

---

## 5. Recommendations

### Critical Fixes (Do Immediately)

**1. Fix FRED method name mismatch**
```python
# File: backend/app/services/macro.py
# Line: 609

# Change:
observations = await self.fred_client.get_series_observations(...)

# To:
observations = await self.fred_client.get_series(...)
```

**2. Add integration test for FRED flow**
```python
# New file: backend/tests/integration/test_fred_integration.py
@pytest.mark.asyncio
async def test_fred_to_database_flow():
    """Test complete FRED data flow from API to database."""
    fred_provider = FREDProvider(api_key=os.getenv("FRED_API_KEY"))
    macro_service = MacroService(fred_client=fred_provider)

    # Fetch indicators
    results = await macro_service.fetch_indicators(
        asof_date=date.today(),
        lookback_days=30
    )

    # Verify data stored in database
    indicator = await macro_service.get_latest_indicator("CPIAUCSL")
    assert indicator is not None
    assert indicator.value > 0
```

### High Priority (Next Sprint)

**3. Add stale data UI indicators**
```javascript
// frontend/components/StaleDataBadge.js
function StaleDataBadge({ metadata }) {
    if (metadata?.stale) {
        return <span className="badge badge-warning">Stale Data</span>;
    }
    if (metadata?.cached) {
        return <span className="badge badge-info">Cached</span>;
    }
    return null;
}
```

**4. Handle pattern execution errors in UI**
```javascript
// frontend/api-client.js
executePattern: async (patternName, inputs, options) => {
    try {
        const response = await axios.post(...);

        // Check for error in response data
        if (response.data.error || response.data.status === 'error') {
            throw new Error(response.data.error || 'Pattern execution failed');
        }

        return response.data;
    } catch (error) {
        // Show error to user
        console.error(`Pattern '${patternName}' failed:`, error);
        throw error;
    }
}
```

**5. Add 429 rate limit handling**
```javascript
// frontend/api-client.js - enhance interceptor
if (error.response?.status === 429) {
    const retryAfter = error.response.headers['retry-after'];
    if (retryAfter && originalRequest._retryCount === 0) {
        const delay = parseInt(retryAfter) * 1000;
        console.log(`Rate limited, retrying after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
        originalRequest._retryCount++;
        return axios(originalRequest);
    }
}
```

### Medium Priority (Backlog)

**6. Standardize error handling across services**
```python
# Create base service class with consistent error handling
class BaseService:
    def handle_provider_error(self, error: Exception, context: str):
        """Standardized error handling for all services."""
        if isinstance(error, ProviderError):
            logger.error(f"{context}: Provider error: {error}")
            raise ServiceError(f"External API error: {error}")
        elif isinstance(error, DatabaseError):
            logger.error(f"{context}: Database error: {error}")
            raise ServiceError(f"Database error: {error}")
        else:
            logger.error(f"{context}: Unexpected error: {error}")
            raise ServiceError(f"Internal error: {error}")
```

**7. Add metadata storage for FRED indicators**
```sql
-- Migration: Add indicator_metadata table
CREATE TABLE indicator_metadata (
    indicator_id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    units VARCHAR(100),
    frequency VARCHAR(20),
    seasonal_adjustment VARCHAR(50),
    source VARCHAR(50) DEFAULT 'FRED',
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Populate from FRED API
INSERT INTO indicator_metadata (indicator_id, title, units, frequency)
SELECT DISTINCT
    indicator_id,
    indicator_name,
    units,
    frequency
FROM macro_indicators;
```

**8. Update documentation to match implementation**
```markdown
# provider-database-mapping.md

## Corporate Actions Priority (UPDATED 2025-11-05)

1. **Primary (ACTIVE):** FMP Premium
   - Methods: get_dividend_calendar(), get_split_calendar(), get_earnings_calendar()
   - Called by: DataHarvester agent
   - Status: ✅ Production

2. **Backup (NOT IMPLEMENTED):** Polygon
   - Methods: Removed in favor of FMP
   - Status: ❌ Not used
```

---

## 6. Architecture Strengths

Despite the issues found, the system has several strong architectural patterns:

### 1. Consistent Provider Pattern
```python
# All providers inherit from BaseProvider
# Provides: retry logic, rate limiting, caching, tracing
# ✅ EXCELLENT - reduces code duplication
```

### 2. Clear Layer Separation
```
Providers → Agents → Services → API → Frontend
# Each layer has clear responsibility
# ✅ GOOD - maintainable and testable
```

### 3. Error Recovery
```python
# BaseProvider serves stale data on failure
if cached:
    return cached.with_stale_flag()
# ✅ EXCELLENT - graceful degradation
```

### 4. Rights Enforcement
```python
# Each provider declares export rights
rights = {
    "export_pdf": False,
    "requires_attribution": True
}
# ✅ GOOD - legal compliance built-in
```

---

## 7. Testing Recommendations

### Unit Tests Needed

**Test 1: FRED method name**
```python
def test_fred_provider_has_get_series():
    """Ensure FREDProvider has expected method."""
    provider = FREDProvider(api_key="test")
    assert hasattr(provider, 'get_series')
    assert callable(provider.get_series)
```

**Test 2: MacroService calls correct method**
```python
@pytest.mark.asyncio
async def test_macro_service_calls_get_series():
    """Ensure MacroService calls correct FRED method."""
    mock_fred = Mock(spec=FREDProvider)
    mock_fred.get_series = AsyncMock(return_value=[
        {"date": "2024-01-01", "value": 306.746, "series_id": "CPIAUCSL"}
    ])

    service = MacroService(fred_client=mock_fred)
    results = await service.fetch_indicators()

    # Verify correct method called
    mock_fred.get_series.assert_called()
    assert "CPIAUCSL" in results
```

### Integration Tests Needed

**Test 3: End-to-end FRED flow**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_fred_to_ui_flow():
    """Test complete FRED data flow."""
    # 1. Provider fetches from FRED API
    provider = FREDProvider(api_key=os.getenv("FRED_API_KEY"))
    series_data = await provider.get_series("T10Y2Y")
    assert len(series_data) > 0

    # 2. Service stores in database
    service = MacroService(fred_client=provider)
    results = await service.fetch_indicators(lookback_days=30)
    assert "T10Y2Y" in results

    # 3. API returns data
    response = await test_client.get("/api/v1/macro/indicators")
    assert response.status_code == 200
    assert "T10Y2Y" in response.json()["indicators"]
```

---

## 8. Monitoring Recommendations

### Metrics to Track

**Provider Health:**
- `provider_requests_total{provider, endpoint, status}`
- `provider_latency_seconds{provider, endpoint}`
- `provider_errors_total{provider, error_type}`
- `provider_rate_limit_hits{provider}`

**Data Freshness:**
- `data_staleness_seconds{data_type}`
- `cache_hit_rate{provider}`
- `stale_data_served_total{provider}`

**API Health:**
- `api_request_duration_seconds{endpoint, status}`
- `pattern_execution_duration_seconds{pattern}`
- `pattern_errors_total{pattern, error_type}`

### Alerts to Configure

**Critical:**
- Provider down for > 5 minutes
- FRED data not updated in > 24 hours
- Pattern execution failures > 10% in 5 minutes

**Warning:**
- Provider latency > 5 seconds
- Cache hit rate < 50%
- Stale data served > 20% of requests

---

## Appendix A: File Reference

### Provider Files
- `/backend/app/integrations/base_provider.py` - Base provider with retry logic
- `/backend/app/integrations/fmp_provider.py` - FMP integration (✅ Working)
- `/backend/app/integrations/fred_provider.py` - FRED integration (🚨 Bug found)
- `/backend/app/integrations/polygon_provider.py` - Polygon integration (✅ Working)
- `/backend/app/integrations/news_provider.py` - NewsAPI integration (✅ Working)

### Agent Files
- `/backend/app/agents/data_harvester.py` - Lines 100-600, 2500-2900

### Service Files
- `/backend/app/services/macro.py` - Lines 400-650 (🚨 Bug at line 609)
- `/backend/app/services/corporate_actions.py` - Lines 67-196

### API Files
- `/backend/app/api/routes/macro.py` - Macro regime endpoints
- `/backend/app/api/routes/corporate_actions.py` - Corporate action endpoints
- `/backend/app/api/executor.py` - Pattern execution

### Frontend Files
- `/frontend/api-client.js` - API client with retry logic

### Documentation
- `/.claude/knowledge/provider-database-mapping.md` - Provider mappings
- `/.claude/knowledge/provider-api-documentation.md` - API docs

---

## Appendix B: Quick Reference

### Data Flow Checklist

**FMP Quote → UI:**
- [x] Provider method exists
- [x] Agent calls provider
- [x] Data stored in database
- [x] API endpoint exists
- [x] Frontend method exists
- [x] UI component displays

**FRED Series → UI:**
- [x] Provider method exists
- [ ] Agent calls provider (🚨 **BROKEN** - wrong method name)
- [x] Data stored in database
- [x] API endpoint exists
- [ ] Frontend method exists (wrong endpoint)
- [ ] UI component displays

**Corporate Action → Database:**
- [x] Provider method exists
- [x] Agent calls provider
- [ ] Data stored in database (via API only)
- [x] API endpoint exists
- [ ] Frontend method exists
- [ ] UI component displays

**News → UI:**
- [x] Provider method exists
- [x] Agent calls provider
- [ ] Data stored in database (not persisted)
- [x] Pattern returns data
- [ ] Frontend displays news

---

**Report End**
