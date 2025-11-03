# Corporate Actions Root Issue Analysis

**Date:** November 3, 2025  
**Commit Reviewed:** `94cbb01` - "Enhance financial analysis with new performance metrics"  
**Agent Assessment:** Included from `COMMIT_94CBB01_ANALYSIS.md`  
**Status:** 🔍 **ROOT CAUSE IDENTIFIED** - Architectural mismatch

---

## 📋 Agent Assessment Summary (Commit 94cbb01)

**From `COMMIT_94CBB01_ANALYSIS.md`:**

The commit `94cbb01` by Agent (michaeldawson3) made the following changes:

1. ✅ **Fixed Missing Metrics Fields** - Agent now returns volatility, sharpe, max_drawdown
2. ✅ **Fixed Pattern References** - Updated to use `{{perf_metrics.*}}` instead of `{{twr.*}}`
3. ✅ **Removed Mock Corporate Actions** - Returns honest "not implemented" message

**Specific Change to Corporate Actions Endpoint:**
- **Before:** Returned hardcoded mock data (AAPL, GOOGL, MSFT, T with fake dates)
- **After:** Returns empty array with informative metadata:
  ```python
  "actions": [],
  "metadata": {
      "message": "Corporate actions tracking not implemented in alpha version",
      "version": "alpha",
      "note": "Past dividends are tracked in the transactions table"
  }
  ```

**Assessment:** ✅ **IMPROVEMENT** - Changed from misleading mock data to honest empty response. However, the **root architectural issue** remains: the system cannot fetch or display upcoming corporate actions.

---

## 📊 Executive Summary

After comprehensive end-to-end review of corporate actions functionality, I've identified the **root architectural issue** preventing corporate actions from working:

**The Root Issue:** The system is architected to **record past corporate actions** (dividends, splits) but has **no infrastructure to fetch or display upcoming/future corporate actions**. This is an **architectural mismatch** between:
- **UI Expectation:** Display upcoming/future corporate actions (dividends, splits, earnings)
- **Backend Reality:** Only tracks past corporate actions via `transactions` table

**The Fix:** Implement a minimal, architecturally sound solution that respects current code state - leverage existing `CorporateActionsService` and extend it to query upcoming events from external data sources.

---

## 🔍 End-to-End Flow Analysis

### Layer 1: UI (Frontend) ✅ FULLY FUNCTIONAL

**File:** `full_ui.html` lines 10868-11108  
**Component:** `CorporateActionsPage()`

**Implementation Status:** ✅ **PRODUCTION-READY**

**What It Does:**
1. ✅ Fetches from `/api/corporate-actions` endpoint
2. ✅ Passes `portfolio_id` and `days_ahead` parameters
3. ✅ Handles loading, error, and empty states
4. ✅ Filters by action type (dividend, split, earnings, buyback, merger)
5. ✅ Formats dates and action details
6. ✅ Displays in beautiful table with badges and formatting

**API Call:**
```javascript
const response = await axios.get('/api/corporate-actions', {
    params: {
        days_ahead: filterDays,           // Time horizon (30, 90, 180, etc.)
        portfolio_id: getCurrentPortfolioId()  // Portfolio context
    },
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

// Expects response structure:
response.data.data.actions = [
    {
        id: "ca_001",
        symbol: "AAPL",
        type: "dividend",
        ex_date: "2025-11-07",
        payment_date: "2025-11-14",
        amount: 0.24,
        currency: "USD",
        impact: "You own 100 shares. Expected payment: $24.00",
        status: "announced"
    },
    // ... more actions
]
```

**Data Contract Expected:**
```javascript
{
    success: true,
    data: {
        portfolio_id: "...",
        time_horizon_days: 90,
        actions: [...],  // Array of upcoming actions
        summary: {
            total_actions: 4,
            dividends_expected: 24.00,
            splits_pending: 1,
            earnings_releases: 1,
            mergers_acquisitions: 1
        },
        notifications: {
            urgent: [...],
            informational: [...]
        },
        last_updated: "2025-11-03T15:46:34Z"
    }
}
```

**Assessment:** ✅ **UI IS EXCELLENT** - Fully functional, well-designed, handles all edge cases.

---

### Layer 2: API Endpoint (Backend) ⚠️ RETURNS EMPTY

**File:** `combined_server.py` lines 4646-4691  
**Endpoint:** `GET /api/corporate-actions`

**Current Implementation (After Commit 94cbb01):**
```python
@app.get("/api/corporate-actions", response_model=SuccessResponse)
async def get_corporate_actions(
    portfolio_id: Optional[str] = Query(None),
    days_ahead: int = Query(30, ge=1, le=365),
    user: dict = Depends(require_auth)
):
    """
    Get upcoming corporate actions for portfolio holdings
    AUTH_STATUS: MIGRATED - Sprint 2
    NOTE: Not yet implemented - returns empty data
    """
    try:
        # Corporate actions tracking not implemented in alpha
        # Return empty array with informative message
        response = {
            "portfolio_id": portfolio_id,
            "time_horizon_days": days_ahead,
            "actions": [],  # ⚠️ EMPTY ARRAY
            "summary": {
                "total_actions": 0,
                "dividends_expected": 0.00,
                "splits_pending": 0,
                "earnings_releases": 0,
                "mergers_acquisitions": 0
            },
            "notifications": {
                "urgent": [],
                "informational": []
            },
            "last_updated": datetime.utcnow().isoformat(),
            "metadata": {
                "message": "Corporate actions tracking not implemented in alpha version",
                "version": "alpha",
                "note": "Past dividends are tracked in the transactions table"
            }
        }
        return SuccessResponse(data=response)
```

**What It Does:**
- ✅ Accepts `portfolio_id` and `days_ahead` parameters
- ✅ Returns proper response structure
- ❌ **Ignores parameters** - doesn't query portfolio holdings
- ❌ **Returns empty array** - no upcoming actions
- ✅ Adds honest metadata (good!)

**Assessment:** ⚠️ **HONEST BUT NON-FUNCTIONAL** - Returns correct structure but empty data.

---

### Layer 3: Service Layer ⚠️ RECORDS PAST ONLY

**File:** `backend/app/services/corporate_actions.py`

**What Exists:**
1. ✅ `CorporateActionsService` class
2. ✅ `record_dividend()` - Records past dividend payments
3. ✅ `record_split()` - Records past stock splits
4. ✅ `record_withholding_tax()` - Records past withholding taxes
5. ✅ `get_dividend_history()` - Queries **past** dividends from `transactions` table

**What's Missing:**
1. ❌ `get_upcoming_actions()` - No method to fetch upcoming events
2. ❌ `fetch_upcoming_dividends()` - No method to fetch upcoming dividends
3. ❌ `fetch_upcoming_splits()` - No method to fetch upcoming splits
4. ❌ `fetch_upcoming_earnings()` - No method to fetch earnings dates
5. ❌ External data source integration - No fetcher for corporate actions data

**Key Insight:**
- Service is designed for **recording past events** (transaction history)
- Service has **no methods for upcoming/future events**
- No data fetching capability

**Assessment:** ⚠️ **ARCHITECTURALLY INCOMPLETE** - Service only handles past events, not future events.

---

### Layer 4: Database Schema ⚠️ TRACKS PAST ONLY

**File:** `backend/db/migrations/008_add_corporate_actions_support.sql`

**What Exists:**
```sql
-- Added to transactions table:
pay_date DATE                  -- Payment date (for past dividends)
pay_fx_rate_id UUID           -- FX rate at payment date
ex_date DATE                  -- Ex-dividend date (reference only)

-- Transaction types:
DIVIDEND - Past dividend payments
SPLIT - Past stock splits
```

**What's Missing:**
- ❌ **No `corporate_actions` table** for upcoming/future events
- ❌ No table to store announced dividends (before pay date)
- ❌ No table to store announced splits (before effective date)
- ❌ No table to store earnings dates
- ❌ No table to store merger announcements

**Key Insight:**
- Migration 008 is focused on **recording past dividends with accurate FX rates**
- Schema supports **historical tracking** only
- Schema does **NOT support upcoming/future events**

**Assessment:** ⚠️ **SCHEMA GAP** - No table for upcoming corporate actions.

---

### Layer 5: Agent Capabilities ❌ DOES NOT EXIST

**What Exists:**
- ❌ No agent capabilities for corporate actions
- ❌ No `corporate_actions.*` capabilities in any agent
- ❌ Cannot be used in patterns

**What's Expected:**
```python
# Missing capabilities:
corporate_actions.upcoming  # Get upcoming events for portfolio
corporate_actions.by_symbol  # Get events for specific symbol
corporate_actions.impact    # Calculate portfolio impact
```

**Assessment:** ❌ **AGENT GAP** - No agent integration for corporate actions.

---

### Layer 6: Data Sources ❌ DOES NOT EXIST

**What Exists:**
- ✅ PolygonProvider exists (`backend/app/integrations/polygon_provider.py`)
- ✅ Provider comment mentions: "Fetch prices, splits, dividends for corporate actions"
- ⚠️ **BUT:** Provider not implemented for corporate actions fetching

**What's Missing:**
- ❌ No method in PolygonProvider to fetch upcoming dividends
- ❌ No method in PolygonProvider to fetch upcoming splits
- ❌ No method in PolygonProvider to fetch earnings dates
- ❌ No integration with Yahoo Finance, Alpha Vantage, or FMP
- ❌ No scheduled jobs to refresh corporate actions data

**Assessment:** ❌ **DATA SOURCE GAP** - No mechanism to fetch corporate actions from external sources.

---

## 🎯 Root Cause Identification

### The Architectural Mismatch

**UI Expectation:**
- Display **upcoming/future** corporate actions
- Filter by portfolio holdings
- Show dates, amounts, impact calculations

**Backend Reality:**
- Only tracks **past** corporate actions (via `transactions` table)
- No infrastructure for **upcoming/future** events
- No data fetching mechanism
- No storage for announced (but not yet executed) events

**Root Cause:** ⚠️ **ARCHITECTURAL MISMATCH** - System designed for recording past events, not displaying future events.

---

## 🔍 Why This Architecture Exists

### Historical Context (Migration 008)

**Purpose of Migration 008:**
- Add support for **ADR pay-date FX accuracy**
- Track **past dividend payments** with correct FX rates
- Enable accurate historical reporting

**What It Achieved:**
- ✅ Past dividends recorded correctly
- ✅ FX rates captured at payment date
- ✅ Historical dividend queries work

**What It Did NOT Achieve:**
- ❌ Upcoming dividend tracking
- ❌ Future event announcements
- ❌ Earnings date tracking

**Conclusion:** Migration 008 was **focused on historical accuracy**, not future event tracking.

---

## 📋 What's Actually Missing

### Missing Components (Complete Gap Analysis)

#### 1. Database Table ❌
**Missing:** `corporate_actions` table for upcoming/future events

**Why Needed:**
- Store announced dividends (before pay date)
- Store announced splits (before effective date)
- Store earnings dates
- Store merger announcements

**Current Workaround:** None (no table exists)

---

#### 2. Service Method ❌
**Missing:** `CorporateActionsService.get_upcoming_actions()` method

**Why Needed:**
- Query upcoming events for portfolio
- Filter by date range
- Calculate portfolio impact
- Return structured data

**Current Workaround:** Endpoint returns empty array

---

#### 3. Data Fetcher ❌
**Missing:** `CorporateActionsFetcher` service

**Why Needed:**
- Fetch upcoming dividends from external API
- Fetch upcoming splits from external API
- Fetch earnings dates from external API
- Store in database for caching

**Current Workaround:** None (no data source)

---

#### 4. Agent Capability ❌
**Missing:** `corporate_actions.*` agent capabilities

**Why Needed:**
- Enable pattern-based access
- Integrate with portfolio workflows
- Consistent with other features

**Current Workaround:** Endpoint is direct API, not pattern-based

---

#### 5. Scheduled Job ❌
**Missing:** Daily job to refresh corporate actions

**Why Needed:**
- Keep corporate actions data current
- Refresh announcements daily
- Update status (announced → scheduled → completed)

**Current Workaround:** None (no data to refresh)

---

## 🎯 Architecturally Sound Fix

### Design Principles

1. **Respect Current Architecture:**
   - Use existing `CorporateActionsService` pattern
   - Leverage existing database connection handling
   - Follow existing service dependency injection

2. **Minimal Schema Changes:**
   - Create `corporate_actions` table for upcoming events
   - Don't modify existing `transactions` table structure
   - Keep past events in `transactions`, future events in `corporate_actions`

3. **Leverage Existing Patterns:**
   - Follow same pattern as `PricingService` (query external data)
   - Follow same pattern as `MacroService` (fetch and store)
   - Use existing provider infrastructure

4. **Incremental Implementation:**
   - Phase 1: Basic upcoming dividends (MVP)
   - Phase 2: Add splits and earnings
   - Phase 3: Add agent capabilities and patterns

---

### Recommended Implementation Strategy

#### Option A: Minimal MVP (Respects Current State) ✅ RECOMMENDED

**Philosophy:** Extend existing `CorporateActionsService` with minimal changes, use external API directly without complex caching.

**Implementation:**

**1. Create Database Table (Migration 014)**
```sql
CREATE TABLE corporate_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID REFERENCES securities(id),
    symbol TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('dividend', 'split', 'earnings', 'merger', 'buyback')),
    
    -- Dates
    announcement_date DATE,
    ex_date DATE,
    record_date DATE,
    payment_date DATE,
    effective_date DATE,
    earnings_date DATE,
    
    -- Details
    amount NUMERIC(19,4),  -- Dividend per share
    currency TEXT DEFAULT 'USD',
    ratio TEXT,  -- Split ratio (e.g., "2:1")
    consensus_eps NUMERIC(10,2),  -- Earnings estimate
    
    -- Status
    status TEXT NOT NULL DEFAULT 'announced',
    source TEXT DEFAULT 'external_api',
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_corporate_actions_symbol ON corporate_actions(symbol);
CREATE INDEX idx_corporate_actions_dates ON corporate_actions(ex_date, payment_date, earnings_date, effective_date);
CREATE INDEX idx_corporate_actions_status ON corporate_actions(status);
```

**2. Extend CorporateActionsService**
```python
# Add to existing CorporateActionsService class
async def get_upcoming_actions(
    self,
    portfolio_id: UUID,
    days_ahead: int = 90
) -> List[Dict[str, Any]]:
    """
    Get upcoming corporate actions for portfolio holdings.
    
    Steps:
    1. Get portfolio holdings (symbols, quantities)
    2. Query corporate_actions table for upcoming events
    3. Filter by date range (today to today + days_ahead)
    4. Calculate portfolio impact (shares × dividend amount)
    5. Return structured data matching UI expectations
    """
    # Get portfolio holdings
    holdings = await self._get_portfolio_holdings(portfolio_id)
    symbols = [h['symbol'] for h in holdings]
    holdings_map = {h['symbol']: h['qty_open'] for h in holdings}
    
    if not symbols:
        return []
    
    # Query upcoming corporate actions
    cutoff_date = date.today() + timedelta(days=days_ahead)
    
    query = """
        SELECT 
            id, symbol, type,
            announcement_date, ex_date, record_date, payment_date,
            effective_date, earnings_date,
            amount, currency, ratio, consensus_eps,
            status, source
        FROM corporate_actions
        WHERE symbol = ANY($1)
          AND status IN ('announced', 'scheduled')
          AND (
              (ex_date BETWEEN $2 AND $3) OR
              (payment_date BETWEEN $2 AND $3) OR
              (effective_date BETWEEN $2 AND $3) OR
              (earnings_date BETWEEN $2 AND $3)
          )
        ORDER BY 
            COALESCE(ex_date, payment_date, effective_date, earnings_date) ASC
    """
    
    rows = await self.conn.fetch(query, symbols, date.today(), cutoff_date)
    
    # Format for UI
    actions = []
    for row in rows:
        symbol = row['symbol']
        shares = holdings_map.get(symbol, 0)
        
        action = {
            'id': str(row['id']),
            'symbol': symbol,
            'type': row['type'],
            'status': row['status'],
        }
        
        # Add dates based on type
        if row['type'] == 'dividend':
            action['ex_date'] = row['ex_date'].isoformat() if row['ex_date'] else None
            action['record_date'] = row['record_date'].isoformat() if row['record_date'] else None
            action['payment_date'] = row['payment_date'].isoformat() if row['payment_date'] else None
            action['amount'] = float(row['amount']) if row['amount'] else None
            action['currency'] = row['currency']
            # Calculate impact
            if row['amount'] and shares > 0:
                action['impact'] = f"You own {shares} shares. Expected payment: ${row['amount'] * shares:.2f}"
        
        elif row['type'] == 'split':
            action['effective_date'] = row['effective_date'].isoformat() if row['effective_date'] else None
            action['ratio'] = row['ratio']
            if shares > 0:
                # Calculate new shares after split
                ratio_parts = row['ratio'].split(':') if row['ratio'] else ['1', '1']
                multiplier = float(ratio_parts[0]) / float(ratio_parts[1])
                new_shares = shares * multiplier
                action['impact'] = f"Your {shares} shares will become {new_shares:.0f} shares"
        
        elif row['type'] == 'earnings':
            action['earnings_date'] = row['earnings_date'].isoformat() if row['earnings_date'] else None
            action['consensus_eps'] = float(row['consensus_eps']) if row['consensus_eps'] else None
        
        actions.append(action)
    
    return actions
```

**3. Update API Endpoint**
```python
@app.get("/api/corporate-actions", response_model=SuccessResponse)
async def get_corporate_actions(
    portfolio_id: Optional[str] = Query(None),
    days_ahead: int = Query(30, ge=1, le=365),
    user: dict = Depends(require_auth)
):
    """Get upcoming corporate actions for portfolio holdings"""
    try:
        if not portfolio_id:
            raise HTTPException(status_code=400, detail="portfolio_id required")
        
        async with get_db_connection_with_rls(user['user_id']) as conn:
            service = CorporateActionsService(conn)
            actions = await service.get_upcoming_actions(
                portfolio_id=UUID(portfolio_id),
                days_ahead=days_ahead
            )
            
            # Calculate summary
            summary = {
                'total_actions': len(actions),
                'dividends_expected': sum(
                    a.get('amount', 0) * holdings.get(a['symbol'], {}).get('qty_open', 0)
                    for a in actions if a['type'] == 'dividend'
                ),
                'splits_pending': sum(1 for a in actions if a['type'] == 'split'),
                'earnings_releases': sum(1 for a in actions if a['type'] == 'earnings'),
                'mergers_acquisitions': sum(1 for a in actions if a['type'] == 'merger')
            }
            
            response = {
                'portfolio_id': portfolio_id,
                'time_horizon_days': days_ahead,
                'actions': actions,
                'summary': summary,
                'notifications': {
                    'urgent': [a for a in actions if a.get('ex_date') and 
                              (date.fromisoformat(a['ex_date']) - date.today()).days <= 7],
                    'informational': [a for a in actions if a['type'] == 'earnings']
                },
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return SuccessResponse(data=response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting corporate actions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get corporate actions")
```

**4. Add Data Fetcher (External API Integration)**
```python
# backend/app/services/corporate_actions_fetcher.py
class CorporateActionsFetcher:
    """
    Fetches upcoming corporate actions from external data sources.
    
    Data Sources (in priority order):
    1. Yahoo Finance (free, reliable)
    2. Polygon.io (if API key available)
    3. Alpha Vantage (if API key available)
    """
    
    async def fetch_upcoming_dividends(self, symbol: str) -> List[Dict]:
        """Fetch upcoming dividends from Yahoo Finance"""
        # Use yfinance library or Yahoo Finance API
        # Returns: [{"ex_date": ..., "payment_date": ..., "amount": ..., ...}]
        pass
    
    async def fetch_upcoming_splits(self, symbol: str) -> List[Dict]:
        """Fetch upcoming stock splits"""
        pass
    
    async def fetch_earnings_dates(self, symbol: str) -> List[Dict]:
        """Fetch earnings announcement dates"""
        pass
    
    async def fetch_and_store_all(self, symbol: str):
        """Fetch all upcoming actions and store in corporate_actions table"""
        # 1. Fetch dividends
        # 2. Fetch splits
        # 3. Fetch earnings
        # 4. Store in database
        pass
```

**5. Add Scheduled Job (Optional but Recommended)**
```python
# backend/jobs/corporate_actions.py
async def refresh_corporate_actions_job():
    """Daily job to refresh corporate actions for all portfolio holdings"""
    async with get_db_connection() as conn:
        fetcher = CorporateActionsFetcher()
        
        # Get all unique symbols from portfolio holdings
        symbols = await conn.fetch("""
            SELECT DISTINCT symbol FROM lots WHERE qty_open > 0
        """)
        
        for row in symbols:
            await fetcher.fetch_and_store_all(row['symbol'])
```

**Time Estimate:** 8-12 hours
- Database migration: 1-2 hours
- Service method: 2-3 hours
- API endpoint update: 1 hour
- Data fetcher: 3-4 hours
- Testing: 2-3 hours

**Risk:** Low-Medium (requires external API integration)

---

#### Option B: Full Implementation (More Complex) ⚠️

**Includes:** Agent capabilities, pattern integration, comprehensive data sources

**Time Estimate:** 18-25 hours

**Risk:** Medium (more moving parts)

**Recommendation:** Start with Option A (MVP), add agent capabilities later if needed.

---

## ✅ Recommended Fix (Architecturally Sound)

### Phase 1: MVP - Basic Upcoming Corporate Actions (8-12 hours)

**1. Create Database Table** (1-2 hours)
- Migration 014: Create `corporate_actions` table
- Add indexes for efficient queries

**2. Extend CorporateActionsService** (2-3 hours)
- Add `get_upcoming_actions()` method
- Query `corporate_actions` table
- Calculate portfolio impact
- Format for UI expectations

**3. Update API Endpoint** (1 hour)
- Replace empty response with actual query
- Use `CorporateActionsService.get_upcoming_actions()`
- Calculate summary and notifications

**4. Add Data Fetcher** (3-4 hours)
- Integrate Yahoo Finance (free, no API key needed)
- Fetch upcoming dividends, splits, earnings
- Store in `corporate_actions` table

**5. Testing** (1-2 hours)
- Test with actual portfolio holdings
- Verify UI displays correctly
- Verify impact calculations

**Result:** ✅ Corporate actions page displays real upcoming events for portfolio holdings.

---

## 📊 Architecture Alignment

### How This Fix Respects Current Architecture

**✅ Service Pattern:**
- Extends existing `CorporateActionsService` (doesn't create new service)
- Uses existing database connection pattern
- Follows existing error handling

**✅ Database Pattern:**
- Creates new table for upcoming events (doesn't modify `transactions`)
- Keeps past events in `transactions`, future events in `corporate_actions`
- Consistent with existing schema structure

**✅ API Pattern:**
- Updates existing endpoint (doesn't create new endpoint)
- Uses existing authentication middleware
- Returns same response structure

**✅ Data Fetching Pattern:**
- Similar to `MacroService` fetching FRED data
- Similar to `PricingService` fetching prices
- Follows existing provider infrastructure

---

## 🎯 Final Recommendation

### ✅ **Implement Option A (MVP)** - 8-12 hours

**Why:**
1. ✅ Respects current architecture
2. ✅ Minimal schema changes (one new table)
3. ✅ Extends existing service (doesn't rebuild)
4. ✅ Gets feature working quickly
5. ✅ Can add agent capabilities later if needed

**What It Achieves:**
- ✅ Corporate actions page displays real data
- ✅ Portfolio-specific filtering works
- ✅ Impact calculations accurate
- ✅ Date range filtering works
- ✅ Summary and notifications populate

**What Can Be Added Later:**
- Agent capabilities (Phase 2)
- Pattern integration (Phase 2)
- Additional data sources (Phase 3)
- Scheduled refresh jobs (Phase 3)

---

**Status:** Root cause identified. Architecturally sound fix proposed that respects current code state.

