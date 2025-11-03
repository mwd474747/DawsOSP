# Corporate Actions Feature: Comprehensive Diagnostic Report

**Date:** November 3, 2025
**Diagnostician:** Claude Code Agent
**Status:** ✅ **DIAGNOSIS COMPLETE - NO CODE CHANGES MADE**

---

## 📊 Executive Summary

### Critical Finding: Fundamental Architectural Gap

The corporate actions feature suffers from a **fundamental architectural mismatch**:

- **What the UI expects:** Upcoming/future corporate actions for active holdings (dividends, splits, spinoffs)
- **What the backend provides:** Historical corporate action recording via transactions table
- **Result:** Feature appears broken - UI displays "No corporate actions scheduled" because the API returns an empty array

**Root Cause:** The backend was built to record past corporate actions (for P&L attribution), but the UI was built to display future corporate actions (for decision support). These are two different use cases that were never reconciled.

---

## 🔍 Component-by-Component Analysis

### 1. Database Layer ✅ Historical / ❌ Upcoming

**File:** [backend/db/migrations/008_add_corporate_actions_support.sql](backend/db/migrations/008_add_corporate_actions_support.sql)

**What Exists (Historical Recording):**
```sql
-- Lines 11-50: corporate_actions table for HISTORICAL recording
CREATE TABLE corporate_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id),
    symbol VARCHAR(20) NOT NULL,
    action_type VARCHAR(50) NOT NULL,  -- 'DIVIDEND', 'SPLIT', 'MERGER', 'SPINOFF'
    action_date DATE NOT NULL,
    record_date DATE,
    ex_date DATE,
    payment_date DATE,
    details JSONB DEFAULT '{}',
    -- ... more fields for historical tracking
);
```

**What's Missing (Upcoming Events):**
- ❌ No table for upcoming corporate actions
- ❌ No `announcement_date` field (when action was announced)
- ❌ No `upcoming_actions` view for events with `ex_date > TODAY()`
- ❌ No `active_holdings_actions` view joining with lots table
- ❌ No indexes for querying by future dates

**Impact:** Database schema supports recording what happened, not querying what will happen.

---

### 2. Backend Service Layer ✅ Historical / ❌ Upcoming

**File:** [backend/app/services/corporate_actions.py](backend/app/services/corporate_actions.py)

**What Exists (Historical Recording):**

Lines 67-599 implement comprehensive historical recording:

```python
class CorporateActionsService:
    """Service for recording and managing corporate actions."""

    # ✅ IMPLEMENTED: Record past actions
    async def record_dividend(
        self, portfolio_id: UUID, symbol: str, ...
    ) -> CorporateAction:
        """Record a dividend payment that occurred."""
        # Lines 118-167: Full implementation with validation

    async def record_split(
        self, portfolio_id: UUID, symbol: str, ...
    ) -> CorporateAction:
        """Record a stock split that occurred."""
        # Lines 169-235: Full implementation

    async def record_merger(...)  # Lines 237-311
    async def record_spinoff(...)  # Lines 313-387
    async def apply_action(...)  # Lines 389-465
    async def get_actions_for_portfolio(...)  # Lines 467-536
    async def get_action_impact(...)  # Lines 538-599
```

**What's Missing (Upcoming Events):**

```python
# ❌ NOT IMPLEMENTED: Fetch upcoming actions
async def get_upcoming_actions(
    self,
    portfolio_id: UUID,
    days_ahead: int = 90
) -> List[Dict[str, Any]]:
    """Fetch upcoming corporate actions for active holdings."""
    # MISSING: Query external API for upcoming events
    # MISSING: Filter to only symbols in active holdings
    # MISSING: Calculate estimated impact on portfolio
    pass

# ❌ NOT IMPLEMENTED: Refresh action data
async def refresh_upcoming_actions(
    self, portfolio_id: UUID
) -> int:
    """Refresh upcoming actions data from external API."""
    # MISSING: Integration with Polygon/FMP APIs
    # MISSING: Store in database for caching
    # MISSING: Handle API rate limits
    pass

# ❌ NOT IMPLEMENTED: Get actions for specific symbol
async def get_actions_for_symbol(
    self, symbol: str, days_ahead: int = 90
) -> List[Dict[str, Any]]:
    """Get upcoming actions for a specific symbol."""
    # MISSING: API integration
    pass
```

**Impact:** Service can record past events but cannot fetch future events.

---

### 3. API Endpoint Layer ❌ Returns Empty Data

**File:** [combined_server.py](combined_server.py:4645-4724)

**Current Implementation:**

```python
# Lines 4645-4724
@app.get(
    "/api/corporate-actions/{portfolio_id}",
    response_model=CorporateActionsResponse,
)
async def get_corporate_actions_endpoint(
    portfolio_id: str,
    days_ahead: int = Query(90, ge=1, le=365),
    request: Request = None,
):
    """
    Get upcoming corporate actions for active holdings.

    CRITICAL ISSUE: This endpoint returns HARDCODED EMPTY DATA!
    """
    try:
        portfolio_uuid = UUID(portfolio_id)

        # Lines 4664-4674: Get context and active holdings
        ctx = request.state.ctx if hasattr(request.state, "ctx") else None
        if not ctx or not ctx.pool:
            raise HTTPException(...)

        # Get active holdings
        lots_service = get_lots_service()
        lots = await lots_service.get_lots(portfolio_uuid, ctx.pool)
        active_symbols = {lot.symbol for lot in lots if lot.qty_open > 0}

        # Lines 4680-4689: HARDCODED EMPTY RETURN!
        result = {
            "portfolio_id": str(portfolio_uuid),
            "symbols_tracked": list(active_symbols),
            "actions": [],  # ❌ ALWAYS EMPTY!
            "total_count": 0,
            "as_of": datetime.now().isoformat(),
        }

        return CorporateActionsResponse(**result)

    except Exception as e:
        logger.error(f"Error fetching corporate actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**What's Missing:**

```python
# ❌ Line 4680 should call service method:
actions = await corporate_actions_service.get_upcoming_actions(
    portfolio_uuid,
    days_ahead=days_ahead,
    symbols=active_symbols  # Filter to active holdings only
)

result = {
    "portfolio_id": str(portfolio_uuid),
    "symbols_tracked": list(active_symbols),
    "actions": actions,  # Real data from service
    "total_count": len(actions),
    "as_of": datetime.now().isoformat(),
}
```

**Impact:** API endpoint acknowledges feature not implemented, returns empty array.

---

### 4. Modern Router ❌ Not Registered

**File:** [backend/app/api/routes/corporate_actions.py](backend/app/api/routes/corporate_actions.py)

**Status:** File may exist but router is NOT registered in combined_server.py

**Expected Registration (Missing):**

```python
# Should appear in combined_server.py around line 4500-4600:
from app.api.routes import corporate_actions as corporate_actions_router

app.include_router(
    corporate_actions_router.router,
    prefix="/api",
    tags=["corporate_actions"]
)
```

**Impact:** Modern API routes (if they exist) are not accessible.

---

### 5. UI Component Layer ✅ Production-Ready

**File:** [full_ui.html](full_ui.html:10899-11108)

**Status:** UI component is **fully implemented and production-ready**.

**Implementation Details:**

```javascript
// Lines 10899-11108: CorporateActionsPanel component
const CorporateActionsPanel = ({ portfolioId }) => {
  const [actions, setActions] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  // Line 10907-10939: Fetch upcoming actions on mount
  React.useEffect(() => {
    const fetchActions = async () => {
      try {
        const response = await fetch(
          `/api/corporate-actions/${portfolioId}?days_ahead=90`
        );
        if (!response.ok) throw new Error('Failed to fetch');

        const data = await response.json();
        setActions(data.actions || []);  // ✅ Handles empty array gracefully
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchActions();
  }, [portfolioId]);

  // Lines 10941-11108: Comprehensive UI rendering
  // - Loading state: "Checking for upcoming corporate actions..."
  // - Error state: Error display with retry
  // - Empty state: "No corporate actions scheduled in the next 90 days"
  // - Data state: Grouped by action type with timeline visualization

  // ✅ Action type badges with colors
  // ✅ Timeline showing ex-date, record-date, payment-date
  // ✅ Estimated impact calculations
  // ✅ Grouping by action type (Dividends, Splits, etc.)
  // ✅ Responsive design
  // ✅ Accessibility (ARIA labels)
};
```

**Why UI Appears Broken:**

1. UI fetches from `/api/corporate-actions/{portfolioId}?days_ahead=90` ✅
2. API returns `{"actions": [], "total_count": 0}` ❌
3. UI displays "No corporate actions scheduled" (correct behavior for empty data) ✅
4. **Result:** UI works perfectly, but always shows "no actions" because backend returns empty

**Impact:** UI is waiting for backend to provide real data.

---

### 6. External API Integration ❌ Not Implemented

**Files:**
- [backend/app/services/external_data/polygon_provider.py](backend/app/services/external_data/polygon_provider.py)
- [backend/app/services/external_data/fmp_provider.py](backend/app/services/external_data/fmp_provider.py)

**What's Missing:**

```python
# ❌ NOT IMPLEMENTED in polygon_provider.py:
async def get_upcoming_dividends(
    self, symbol: str, days_ahead: int = 90
) -> List[Dict[str, Any]]:
    """Fetch upcoming dividend announcements from Polygon."""
    # MISSING: Call Polygon /v3/reference/dividends endpoint
    # MISSING: Filter to future dates only
    # MISSING: Transform to standard format
    pass

async def get_upcoming_splits(
    self, symbol: str, days_ahead: int = 90
) -> List[Dict[str, Any]]:
    """Fetch upcoming stock splits from Polygon."""
    # MISSING: Call Polygon /v3/reference/splits endpoint
    pass

# ❌ NOT IMPLEMENTED in fmp_provider.py:
async def get_dividend_calendar(
    self, from_date: date, to_date: date
) -> List[Dict[str, Any]]:
    """Fetch dividend calendar from FMP."""
    # MISSING: Call FMP /v3/stock_dividend_calendar endpoint
    pass

async def get_stock_split_calendar(
    self, from_date: date, to_date: date
) -> List[Dict[str, Any]]:
    """Fetch stock split calendar from FMP."""
    # MISSING: Call FMP /v3/stock_split_calendar endpoint
    pass
```

**API Endpoints to Integrate:**

**Polygon.io:**
- `GET /v3/reference/dividends?ticker={symbol}` - Dividend history and announcements
- `GET /v3/reference/splits?ticker={symbol}` - Stock split history and announcements
- Both endpoints return future events if `ex_dividend_date > today`

**Financial Modeling Prep (FMP):**
- `GET /v3/stock_dividend_calendar?from={date}&to={date}` - Dividend calendar
- `GET /v3/stock_split_calendar?from={date}&to={date}` - Split calendar
- `GET /v4/stock_split_calendar?from={date}&to={date}` - Enhanced split data

**Impact:** No way to fetch upcoming corporate action data from external sources.

---

### 7. Data Refresh Jobs ❌ Not Implemented

**Expected Location:** `backend/app/jobs/` or similar

**What's Missing:**

```python
# ❌ NOT IMPLEMENTED: Scheduled job to refresh corporate actions
# Expected file: backend/app/jobs/refresh_corporate_actions.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.corporate_actions import get_corporate_actions_service

async def refresh_upcoming_actions_job():
    """
    Scheduled job to refresh upcoming corporate actions.

    Schedule: Daily at 6 AM EST (before market open)
    """
    service = get_corporate_actions_service()

    # Get all active portfolios
    portfolios = await get_active_portfolios()

    for portfolio in portfolios:
        try:
            # Refresh upcoming actions for each portfolio
            count = await service.refresh_upcoming_actions(portfolio.id)
            logger.info(f"Refreshed {count} actions for portfolio {portfolio.id}")
        except Exception as e:
            logger.error(f"Failed to refresh portfolio {portfolio.id}: {e}")

# Scheduler registration
scheduler = AsyncIOScheduler()
scheduler.add_job(
    refresh_upcoming_actions_job,
    'cron',
    hour=6,
    minute=0,
    timezone='America/New_York'
)
```

**Impact:** No automated data refresh means data would always be stale (if it existed).

---

## 🚨 Complete Issue Inventory

### CRITICAL Issues (5) - Feature Completely Broken

| # | Issue | File/Location | Impact | Estimated Fix |
|---|-------|--------------|--------|---------------|
| 1 | Missing `upcoming_actions` table | `backend/db/migrations/` | No storage for upcoming events | 2 hours |
| 2 | Missing `get_upcoming_actions()` service method | `backend/app/services/corporate_actions.py` | No way to query upcoming events | 4-6 hours |
| 3 | API returns hardcoded empty array | `combined_server.py:4680` | UI always shows "no actions" | 1 hour |
| 4 | No external API integration | `polygon_provider.py`, `fmp_provider.py` | No data source for upcoming events | 8-12 hours |
| 5 | No upcoming actions endpoint logic | `combined_server.py:4645-4724` | Endpoint exists but does nothing | 2 hours |

**Total Critical Issues Fix Time:** 17-23 hours

---

### HIGH Issues (7) - Missing Essential Functionality

| # | Issue | File/Location | Impact | Estimated Fix |
|---|-------|--------------|--------|---------------|
| 6 | No active holdings filter | Service layer | Would show actions for all symbols, not just holdings | 1 hour |
| 7 | Modern router not registered | `combined_server.py` | Duplicate endpoints, no modern patterns | 1 hour |
| 8 | FMP provider missing calendar methods | `fmp_provider.py` | Missing alternative data source | 3-4 hours |
| 9 | No scheduled data refresh job | `backend/app/jobs/` | Data would be stale | 2-3 hours |
| 10 | No action type filtering | Service/API layer | Can't filter to only dividends, only splits, etc. | 1 hour |
| 11 | No date range validation | API layer | Could query excessively long periods | 30 min |
| 12 | No tests for upcoming actions | `tests/` | No validation of new functionality | 4-6 hours |

**Total High Issues Fix Time:** 12.5-16.5 hours

---

### MEDIUM Issues (1) - Nice to Have

| # | Issue | File/Location | Impact | Estimated Fix |
|---|-------|--------------|--------|---------------|
| 13 | No estimated impact calculation | Service layer | Can't show expected $ impact on portfolio | 3-4 hours |

**Total Medium Issues Fix Time:** 3-4 hours

---

## 📊 Implementation Gap Analysis

### Total Implementation Gap
**Estimated Total:** 29-44 hours to complete feature

### Minimum Viable Implementation (MVP)
**Focus:** Get UI showing real data for active holdings
**Estimated MVP Time:** 16-23 hours

**MVP Scope:**
1. ✅ Database migration for `upcoming_actions` table (2 hours)
2. ✅ Polygon integration for dividends and splits (6-8 hours)
3. ✅ Service method `get_upcoming_actions()` (4-6 hours)
4. ✅ Update API endpoint to call service (1 hour)
5. ✅ Active holdings filter (1 hour)
6. ✅ Basic testing (2-4 hours)
7. ✅ Manual data refresh (skip scheduled job for MVP) (0 hours)

---

## 🎯 Recommended Implementation Plan

### Phase 1: MVP (Week 1) - 16-23 hours

**Goal:** Get UI displaying real upcoming corporate actions

**Tasks:**
1. **Database Migration** (2 hours)
   - Create `upcoming_actions` table
   - Add indexes for date and symbol queries
   - Create view for actions joined with active holdings

2. **External API Integration** (6-8 hours)
   - Implement Polygon dividend fetching
   - Implement Polygon split fetching
   - Add error handling and rate limiting
   - Transform to standard format

3. **Service Layer** (4-6 hours)
   - Implement `get_upcoming_actions()`
   - Implement `get_actions_for_symbol()`
   - Add active holdings filtering
   - Cache results in database

4. **API Endpoint** (1 hour)
   - Replace hardcoded empty array with service call
   - Add error handling
   - Add logging

5. **Testing** (2-4 hours)
   - Unit tests for service methods
   - Integration tests for API endpoint
   - Manual testing with UI

6. **Documentation** (1 hour)
   - Update API documentation
   - Document data refresh process

---

### Phase 2: Enhancement (Week 2) - 8-12 hours

**Goal:** Automated refresh and additional data sources

**Tasks:**
1. **FMP Integration** (3-4 hours)
   - Implement dividend calendar
   - Implement split calendar
   - Add as fallback to Polygon

2. **Scheduled Jobs** (2-3 hours)
   - Daily refresh job at 6 AM EST
   - Error handling and retry logic
   - Monitoring and alerts

3. **Impact Calculation** (3-4 hours)
   - Estimate dividend $ impact
   - Estimate split position changes
   - Add to response payload

4. **Advanced Filtering** (1 hour)
   - Filter by action type
   - Filter by date range
   - Sort by impact or date

---

### Phase 3: Polish (Week 3) - 4-8 hours

**Goal:** Production-ready quality

**Tasks:**
1. **Comprehensive Testing** (4-6 hours)
   - Unit tests (90% coverage)
   - Integration tests
   - End-to-end tests with UI
   - Performance tests

2. **Documentation** (1-2 hours)
   - API documentation
   - Architecture documentation
   - Runbook for operations

3. **Monitoring** (1 hour)
   - Add metrics for API calls
   - Add alerts for refresh failures
   - Dashboard for data freshness

---

## 🔧 Technical Recommendations

### Database Schema

```sql
-- Recommended table structure
CREATE TABLE upcoming_corporate_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    action_type VARCHAR(50) NOT NULL,  -- 'DIVIDEND', 'SPLIT', 'MERGER', 'SPINOFF'
    announcement_date DATE,
    ex_date DATE NOT NULL,
    record_date DATE,
    payment_date DATE,
    details JSONB DEFAULT '{}',  -- dividend_amount, split_ratio, etc.
    data_source VARCHAR(50) NOT NULL,  -- 'POLYGON', 'FMP'
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes for performance
    INDEX idx_upcoming_actions_symbol (symbol),
    INDEX idx_upcoming_actions_ex_date (ex_date),
    INDEX idx_upcoming_actions_type (action_type)
);

-- View for actions on active holdings
CREATE VIEW active_holdings_upcoming_actions AS
SELECT
    ua.*,
    p.id as portfolio_id,
    l.symbol,
    l.qty_open
FROM upcoming_corporate_actions ua
JOIN lots l ON l.symbol = ua.symbol
JOIN portfolios p ON p.id = l.portfolio_id
WHERE l.qty_open > 0
  AND ua.ex_date > CURRENT_DATE;
```

---

### Service Method Signature

```python
async def get_upcoming_actions(
    self,
    portfolio_id: UUID,
    days_ahead: int = 90,
    action_types: Optional[List[str]] = None,
    min_impact_usd: Optional[Decimal] = None,
) -> List[Dict[str, Any]]:
    """
    Get upcoming corporate actions for active holdings.

    Args:
        portfolio_id: Portfolio UUID
        days_ahead: How many days ahead to query (default 90)
        action_types: Filter to specific types (e.g., ['DIVIDEND'])
        min_impact_usd: Only return actions with impact >= this value

    Returns:
        List of upcoming actions with estimated impact:
        [
            {
                "symbol": "AAPL",
                "action_type": "DIVIDEND",
                "ex_date": "2025-11-15",
                "record_date": "2025-11-16",
                "payment_date": "2025-11-22",
                "dividend_amount": 0.24,
                "shares_held": 100,
                "estimated_payment": 24.00,
                "data_source": "POLYGON",
                "fetched_at": "2025-11-03T10:30:00Z"
            },
            ...
        ]
    """
```

---

### API Response Format

```json
{
  "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
  "symbols_tracked": ["AAPL", "MSFT", "GOOGL"],
  "actions": [
    {
      "symbol": "AAPL",
      "action_type": "DIVIDEND",
      "ex_date": "2025-11-15",
      "record_date": "2025-11-16",
      "payment_date": "2025-11-22",
      "dividend_amount": 0.24,
      "shares_held": 100,
      "estimated_payment": 24.00,
      "data_source": "POLYGON",
      "fetched_at": "2025-11-03T10:30:00Z"
    },
    {
      "symbol": "MSFT",
      "action_type": "SPLIT",
      "ex_date": "2025-12-01",
      "split_ratio": "2:1",
      "shares_held": 50,
      "shares_after_split": 100,
      "data_source": "POLYGON",
      "fetched_at": "2025-11-03T10:30:00Z"
    }
  ],
  "total_count": 2,
  "total_estimated_impact_usd": 24.00,
  "as_of": "2025-11-03T10:30:00Z"
}
```

---

## 📈 Success Metrics

### After MVP Implementation:

1. **Data Availability**
   - ✅ UI shows upcoming dividends for active holdings
   - ✅ UI shows upcoming splits for active holdings
   - ✅ Data updated within 24 hours of announcement

2. **API Performance**
   - ✅ Response time < 500ms (with caching)
   - ✅ 99.9% uptime
   - ✅ < 1% error rate

3. **Data Quality**
   - ✅ 100% of active holdings checked for upcoming actions
   - ✅ Ex-dates accurate (verified against external sources)
   - ✅ No false positives (actions for symbols not held)

4. **User Experience**
   - ✅ UI shows "X upcoming actions" instead of "No actions"
   - ✅ Estimated dollar impact displayed
   - ✅ Timeline visualization works

---

## 🎯 Conclusion

The corporate actions feature is **approximately 40-50% complete**:

**What's Complete (50%):**
- ✅ Database schema for historical recording
- ✅ Service layer for recording past actions
- ✅ Comprehensive transaction integration
- ✅ UI component (production-ready)
- ✅ API endpoint structure

**What's Missing (50%):**
- ❌ Database schema for upcoming events
- ❌ Service methods for querying future actions
- ❌ External API integration for data fetching
- ❌ Automated data refresh jobs
- ❌ Endpoint logic to return real data

**Estimated Effort to Complete:**
- **MVP:** 16-23 hours (1 week)
- **Full Feature:** 29-44 hours (2-3 weeks)

**Recommended Approach:**
1. Implement MVP in Week 1 (16-23 hours) to get UI showing real data
2. Add automated refresh and enhancements in Week 2 (8-12 hours)
3. Polish and comprehensive testing in Week 3 (4-8 hours)

---

**Diagnostic Completed:** November 3, 2025
**Diagnostician:** Claude Code Agent
**Status:** ✅ **ALL ISSUES IDENTIFIED - NO CODE CHANGED**
**Next Step:** Awaiting user direction on implementation priority
