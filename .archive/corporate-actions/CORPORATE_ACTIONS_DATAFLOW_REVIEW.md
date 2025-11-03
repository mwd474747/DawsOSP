# Corporate Actions UI Page - Dataflow Review

**Date:** November 3, 2025
**Purpose:** Comprehensive review of corporate actions functionality from database to UI
**Status:** ⚠️ **CRITICAL GAPS IDENTIFIED** - Mock data only, no real implementation

---

## Executive Summary

The Corporate Actions page is **NOT appropriately functioning** to track corporate actions for active holdings. The entire feature is currently **mock data only** with no database integration, no agent capabilities, and no real-world data sources.

**Key Findings:**
- ✅ **UI Implementation**: Fully functional and well-designed
- ✅ **Database Schema**: Tables and columns exist (migration 008)
- ❌ **Backend Endpoint**: Returns only hardcoded mock data
- ❌ **Agent Integration**: No agent capabilities for corporate actions
- ❌ **Data Population**: No mechanism to populate actual corporate actions
- ❌ **Portfolio Integration**: Doesn't query actual portfolio holdings

---

## Dataflow Analysis

### Layer 1: UI (Frontend)

**File:** [full_ui.html](full_ui.html) lines 10868-11108

**Component:** `CorporateActionsPage()`

**Implementation Status:** ✅ **FULLY FUNCTIONAL**

**Capabilities:**
- State management for corporate actions data
- Filtering by action type (dividend, split, earnings, buyback, merger)
- Date range filtering (30, 90, 180, 365, 730 days)
- Portfolio-specific filtering (passes portfolio_id to API)
- Error handling and loading states
- Empty state handling

**API Call:**
```javascript
const response = await axios.get('/api/corporate-actions', {
    params: {
        days_ahead: filterDays,           // ← Time horizon
        portfolio_id: getCurrentPortfolioId()  // ← Portfolio context
    },
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

**Data Contract Expected:**
```javascript
{
    success: true,
    data: {
        actions: [
            {
                id: "ca_001",
                symbol: "AAPL",              // ← Security symbol
                type: "dividend",            // ← Action type
                action: "Quarterly Dividend", // ← Description
                ex_date: "2025-11-07",       // ← Ex-dividend date
                record_date: "2025-11-10",
                payment_date: "2025-11-14",
                amount: 0.24,                // ← Dividend amount per share
                currency: "USD",
                impact: "Expected payment: $24.00", // ← Portfolio impact
                status: "announced"          // ← Status (announced, scheduled, completed)
            }
        ],
        summary: {
            total_actions: 4,
            dividends_expected: 24.00,
            splits_pending: 1,
            earnings_releases: 1,
            mergers_acquisitions: 1
        }
    }
}
```

**UI Features:**
1. **Filtering UI** - Well-designed filter controls
   - Action type dropdown (all, dividend, split, earnings, buyback, merger)
   - Date range selector (30 days to 2 years)
   - Refresh button

2. **Table Display** - Clean table with columns:
   - Date (formatted from ex_date/payment_date/announcement_date)
   - Symbol (security ticker)
   - Type (color-coded badge)
   - Details (formatted based on action type)
   - Status (announced/scheduled/completed)

3. **Smart Formatting** - Type-specific detail formatting:
   - **Dividend**: "$0.24 per share"
   - **Split**: "20:1 stock split"
   - **Earnings**: "EPS: $2.85"
   - **Buyback**: "Share buyback program"
   - **Merger**: "Cash and stock consideration"

**Assessment:** ✅ **PRODUCTION-READY UI** - No changes needed

---

### Layer 2: Backend API Endpoint

**File:** [combined_server.py](combined_server.py) lines 4645-4733

**Endpoint:** `GET /api/corporate-actions`

**Implementation Status:** ❌ **MOCK DATA ONLY**

**Current Implementation:**
```python
@app.get("/api/corporate-actions", response_model=SuccessResponse)
async def get_corporate_actions(
    portfolio_id: Optional[str] = Query(None),
    days_ahead: int = Query(30, ge=1, le=365),
    user: dict = Depends(require_auth)
):
    """Get upcoming corporate actions for portfolio holdings"""
    try:
        # Mock corporate actions data ← ⚠️ PROBLEM: Hardcoded mock data
        actions = {
            "portfolio_id": portfolio_id or "mock-portfolio",
            "time_horizon_days": days_ahead,
            "actions": [
                {
                    "id": "ca_001",
                    "symbol": "AAPL",  # ← Hardcoded, not from portfolio
                    "type": "dividend",
                    "action": "Quarterly Dividend",
                    "ex_date": "2025-11-07",  # ← Hardcoded dates
                    "amount": 0.24,
                    "impact": "You own 100 shares. Expected payment: $24.00",  # ← Fake impact
                    "status": "announced"
                },
                # ... 3 more hardcoded actions
            ]
        }
        return SuccessResponse(data=actions)
    except Exception as e:
        logger.error(f"Error getting corporate actions: {e}")
        raise HTTPException(...)
```

**Problems:**
1. ❌ **No database query** - Doesn't check actual portfolio holdings
2. ❌ **Hardcoded symbols** - Returns AAPL, GOOGL, MSFT, T regardless of portfolio
3. ❌ **Fake impact calculations** - "You own 100 shares" is not based on real data
4. ❌ **Static dates** - Hardcoded future dates that will become outdated
5. ❌ **Ignores portfolio_id** - Parameter accepted but not used
6. ❌ **Ignores days_ahead** - Parameter accepted but not used

**Assessment:** ❌ **NEEDS COMPLETE REWRITE** - Currently non-functional

---

### Layer 3: Database Schema

**File:** [backend/db/migrations/008_add_corporate_actions_support.sql](backend/db/migrations/008_add_corporate_actions_support.sql)

**Implementation Status:** ⚠️ **PARTIAL** - Schema exists but not used

**Schema Analysis:**

#### Option 1: Corporate Actions via Transactions Table (Current Approach)

**Table:** `transactions`

**Columns Added by Migration 008:**
```sql
-- For dividends
pay_date DATE                  -- Payment date (for dividends)
pay_fx_rate_id UUID           -- FX rate at payment date (REQUIRED for non-USD)
ex_date DATE                  -- Ex-dividend date (reference only)

-- For trades
trade_fx_rate_id UUID         -- FX rate at trade date
```

**Purpose:** Track dividend payments with accurate FX rates (especially for ADRs)

**Transaction Types in `transactions` table:**
- `DIVIDEND` - Dividend payments (historical)
- `BUY` - Buy transactions
- `SELL` - Sell transactions
- `FEE` - Fee transactions
- `SPLIT` (likely) - Stock split adjustments
- `SPINOFF` (likely) - Spinoff transactions

**Key Insight:** Migration 008 is focused on **recording past dividends with accurate FX rates**, not tracking **future/upcoming corporate actions**.

#### Option 2: Dedicated Corporate Actions Table (Does Not Exist)

**Expected Structure (if it existed):**
```sql
CREATE TABLE corporate_actions (
    id UUID PRIMARY KEY,
    security_id UUID REFERENCES securities(id),
    type TEXT,  -- 'dividend', 'split', 'earnings', 'merger', 'buyback'
    announcement_date DATE,
    ex_date DATE,
    record_date DATE,
    payment_date DATE,
    effective_date DATE,
    amount NUMERIC,  -- For dividends
    ratio TEXT,      -- For splits (e.g., "20:1")
    terms TEXT,      -- For mergers
    consensus_eps NUMERIC,  -- For earnings
    status TEXT,     -- 'announced', 'scheduled', 'completed'
    source TEXT,     -- Data source
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

**Status:** ❌ **DOES NOT EXIST**

**Assessment:** ⚠️ **SCHEMA GAP** - No table for upcoming/future corporate actions

---

### Layer 4: Agent Capabilities

**Expected:** Agent or service to fetch/manage corporate actions data

**Status:** ❌ **DOES NOT EXIST**

**What's Missing:**

#### 4A: DataHarvester Agent Extension

**Current DataHarvester capabilities** ([backend/app/agents/data_harvester.py](backend/app/agents/data_harvester.py)):
- `provider.fetch_quote` - Real-time quotes
- `provider.fetch_fundamentals` - Company fundamentals
- `provider.fetch_news` - News articles
- `provider.fetch_macro` - Macro indicators
- `fundamentals.load` - Load fundamentals
- `news.search` - Search news
- `news.compute_portfolio_impact` - News impact

**Missing capabilities:**
- ❌ `corporate_actions.fetch_upcoming` - Fetch upcoming events
- ❌ `corporate_actions.fetch_historical` - Historical events
- ❌ `corporate_actions.compute_portfolio_impact` - Calculate impact on holdings
- ❌ `corporate_actions.filter_by_holdings` - Filter by portfolio positions

#### 4B: CorporateActionsAgent (Recommended New Agent)

**Suggested capabilities:**
```python
class CorporateActionsAgent:
    """Specialized agent for corporate actions tracking"""

    async def corporate_actions_upcoming(self, portfolio_id: str, days_ahead: int = 30):
        """
        Get upcoming corporate actions for portfolio holdings

        Steps:
        1. Get current portfolio holdings (symbols)
        2. For each symbol, query corporate actions data source
        3. Filter by date range (next N days)
        4. Calculate portfolio impact (shares owned × dividend amount)
        5. Return structured data
        """

    async def corporate_actions_historical(self, portfolio_id: str, days_back: int = 90):
        """Get historical corporate actions for portfolio"""

    async def corporate_actions_by_symbol(self, symbol: str, days_ahead: int = 90):
        """Get corporate actions for specific symbol"""

    async def corporate_actions_impact(self, portfolio_id: str, action_id: str):
        """Calculate impact of specific action on portfolio"""
```

**Assessment:** ❌ **AGENT GAP** - No agent capabilities for corporate actions

---

### Layer 5: Data Sources

**Expected:** External API or data provider for corporate actions

**Status:** ❌ **NO DATA SOURCE CONFIGURED**

**Options for Data Sources:**

#### Option 1: Free/Open-Source APIs
1. **Yahoo Finance API** (via yfinance library)
   - Dividends: Available via `ticker.dividends`
   - Splits: Available via `ticker.splits`
   - Earnings: Available via `ticker.calendar`
   - **Limitations**: Rate limited, no mergers/buybacks

2. **Alpha Vantage** (Free tier: 5 calls/minute)
   - Endpoint: `EARNINGS_CALENDAR`
   - Endpoint: `DIVIDENDS`
   - **Limitations**: Limited data types

3. **IEX Cloud** (Free tier: 50K messages/month)
   - Endpoint: `/stock/{symbol}/dividends/{range}`
   - Endpoint: `/stock/{symbol}/splits/{range}`
   - **Limitations**: US stocks only

#### Option 2: Premium APIs
1. **Polygon.io** ($199/month)
   - Comprehensive dividend data
   - Stock splits
   - Ticker news (for earnings/mergers)

2. **Financial Modeling Prep** ($29/month)
   - Earnings calendar API
   - Dividend calendar API
   - Stock splits calendar

3. **Intrinio** ($75/month)
   - Corporate actions feed
   - Earnings calendar
   - Dividend announcements

#### Option 3: Manual Data Entry
- Admin UI to manually input corporate actions
- CSV import for bulk actions
- **Use case**: For small portfolios or specific holdings

**Assessment:** ❌ **NO DATA SOURCE** - Zero integration with real data

---

## Gap Analysis

### Critical Gaps (P0 - Blocking Functionality)

#### Gap 1: No Database Table for Upcoming Corporate Actions
**Current State:** Migration 008 adds columns to `transactions` for *recording past dividends*, but there's no table for *upcoming/future* corporate actions.

**Impact:** Cannot store or query upcoming dividends, splits, earnings releases, etc.

**Required:**
```sql
CREATE TABLE corporate_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID REFERENCES securities(id) NOT NULL,
    type TEXT NOT NULL,  -- 'dividend', 'split', 'earnings', 'merger', 'buyback', 'spinoff'

    -- Dates (varies by type)
    announcement_date DATE,
    ex_date DATE,          -- Dividends, splits
    record_date DATE,      -- Dividends
    payment_date DATE,     -- Dividends
    effective_date DATE,   -- Splits, mergers
    earnings_date DATE,    -- Earnings

    -- Details (varies by type)
    amount NUMERIC(19, 4),      -- Dividend amount per share
    currency TEXT DEFAULT 'USD',
    ratio TEXT,                 -- Split ratio (e.g., "2:1", "3:2")
    consensus_eps NUMERIC(10, 2), -- Earnings estimate
    prior_eps NUMERIC(10, 2),     -- Prior quarter EPS
    terms TEXT,                   -- Merger/acquisition terms
    description TEXT,             -- General description

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'announced',  -- 'announced', 'scheduled', 'completed', 'cancelled'
    source TEXT,                  -- Data source (e.g., 'yahoo_finance', 'manual')

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    CONSTRAINT chk_corporate_action_type CHECK (type IN ('dividend', 'split', 'earnings', 'merger', 'buyback', 'spinoff'))
);

CREATE INDEX idx_corporate_actions_security ON corporate_actions(security_id);
CREATE INDEX idx_corporate_actions_dates ON corporate_actions(ex_date, payment_date, earnings_date, effective_date);
CREATE INDEX idx_corporate_actions_status ON corporate_actions(status);
```

**Estimated Effort:** 2-3 hours (migration + testing)

#### Gap 2: No Backend Service for Corporate Actions
**Current State:** Endpoint returns hardcoded mock data.

**Impact:** No real data displayed, portfolio-specific actions not shown.

**Required:** Service layer to:
1. Query `corporate_actions` table
2. Join with portfolio `lots` to find relevant actions
3. Calculate portfolio impact (shares × dividend amount)
4. Filter by date range
5. Format response

**Implementation:**
```python
# backend/app/services/corporate_actions.py
class CorporateActionsService:
    """Service for managing corporate actions"""

    async def get_upcoming_actions(
        self,
        conn,
        portfolio_id: str,
        days_ahead: int = 30
    ) -> Dict:
        """
        Get upcoming corporate actions for portfolio holdings

        Algorithm:
        1. Get current holdings (lots) for portfolio
        2. Extract unique security_ids
        3. Query corporate_actions for those securities
        4. Filter by date range (today + days_ahead)
        5. Calculate impact based on shares owned
        6. Return formatted results
        """

        # Step 1: Get holdings
        holdings = await conn.fetch("""
            SELECT DISTINCT security_id, SUM(qty) as total_qty
            FROM lots
            WHERE portfolio_id = $1 AND qty > 0
            GROUP BY security_id
        """, portfolio_id)

        if not holdings:
            return {"actions": [], "summary": {}}

        security_ids = [h['security_id'] for h in holdings]

        # Step 2: Get upcoming actions
        actions = await conn.fetch("""
            SELECT
                ca.id,
                ca.type,
                ca.ex_date,
                ca.payment_date,
                ca.earnings_date,
                ca.announcement_date,
                ca.amount,
                ca.currency,
                ca.ratio,
                ca.consensus_eps,
                ca.terms,
                ca.status,
                s.symbol,
                s.name
            FROM corporate_actions ca
            JOIN securities s ON ca.security_id = s.id
            WHERE ca.security_id = ANY($1)
              AND ca.status IN ('announced', 'scheduled')
              AND (
                  ca.ex_date >= CURRENT_DATE AND ca.ex_date <= CURRENT_DATE + $2 OR
                  ca.payment_date >= CURRENT_DATE AND ca.payment_date <= CURRENT_DATE + $2 OR
                  ca.earnings_date >= CURRENT_DATE AND ca.earnings_date <= CURRENT_DATE + $2
              )
            ORDER BY COALESCE(ca.ex_date, ca.payment_date, ca.earnings_date) ASC
        """, security_ids, days_ahead)

        # Step 3: Calculate impact
        holdings_map = {h['security_id']: h['total_qty'] for h in holdings}

        enriched_actions = []
        for action in actions:
            enriched = dict(action)

            if action['type'] == 'dividend':
                qty = holdings_map.get(action['security_id'], 0)
                expected_payment = qty * action['amount']
                enriched['impact'] = f"You own {qty} shares. Expected payment: ${expected_payment:.2f}"

            elif action['type'] == 'split':
                qty = holdings_map.get(action['security_id'], 0)
                # Parse ratio (e.g., "20:1" → 20)
                ratio_parts = action['ratio'].split(':')
                new_qty = qty * int(ratio_parts[0]) / int(ratio_parts[1])
                enriched['impact'] = f"Your {qty} shares will become {int(new_qty)} shares"

            # ... other types

            enriched_actions.append(enriched)

        return {
            "actions": enriched_actions,
            "summary": self._calculate_summary(enriched_actions)
        }
```

**Estimated Effort:** 4-6 hours (service + endpoint rewrite + testing)

#### Gap 3: No Data Population Mechanism
**Current State:** No way to get real corporate actions data into the system.

**Impact:** Even with schema + service, no data to display.

**Required:** Data fetcher to populate corporate_actions table.

**Options:**

**Option A: Yahoo Finance Integration (Recommended for MVP)**
```python
# backend/app/services/corporate_actions_fetcher.py
import yfinance as yf
from datetime import datetime, timedelta

class CorporateActionsFetcher:
    """Fetch corporate actions from external sources"""

    async def fetch_dividends_for_symbol(self, conn, symbol: str, days_ahead: int = 90):
        """Fetch upcoming dividends from Yahoo Finance"""
        ticker = yf.Ticker(symbol)

        # Get dividend history (includes upcoming if announced)
        dividends = ticker.dividends

        # Get security_id from database
        security = await conn.fetchrow(
            "SELECT id FROM securities WHERE symbol = $1", symbol
        )

        if not security:
            logger.warning(f"Security {symbol} not found in database")
            return

        # Insert into corporate_actions table
        for date, amount in dividends.items():
            if date >= datetime.now():  # Future dividends only
                await conn.execute("""
                    INSERT INTO corporate_actions (
                        security_id, type, ex_date, amount, currency, status, source
                    ) VALUES ($1, 'dividend', $2, $3, 'USD', 'announced', 'yahoo_finance')
                    ON CONFLICT DO NOTHING
                """, security['id'], date, amount)

    async def fetch_splits_for_symbol(self, conn, symbol: str):
        """Fetch upcoming splits from Yahoo Finance"""
        ticker = yf.Ticker(symbol)
        splits = ticker.splits

        # Similar logic to dividends...

    async def fetch_all_holdings_actions(self, conn, portfolio_id: str):
        """Fetch corporate actions for all holdings in portfolio"""
        holdings = await conn.fetch("""
            SELECT DISTINCT s.symbol
            FROM lots l
            JOIN securities s ON l.security_id = s.id
            WHERE l.portfolio_id = $1 AND l.qty > 0
        """, portfolio_id)

        for holding in holdings:
            await self.fetch_dividends_for_symbol(conn, holding['symbol'])
            await self.fetch_splits_for_symbol(conn, holding['symbol'])
```

**Scheduled Job:**
```python
# Run daily at 6am to update corporate actions
@scheduler.scheduled_job('cron', hour=6)
async def update_corporate_actions():
    """Daily job to update corporate actions for all portfolios"""
    async with get_db_connection() as conn:
        fetcher = CorporateActionsFetcher()

        # Get all portfolios
        portfolios = await conn.fetch("SELECT id FROM portfolios")

        for portfolio in portfolios:
            await fetcher.fetch_all_holdings_actions(conn, portfolio['id'])
```

**Estimated Effort:** 6-8 hours (fetcher + scheduler + testing + error handling)

#### Gap 4: No Agent Capability
**Current State:** No agent method to call from patterns.

**Impact:** Cannot use corporate actions in patterns (e.g., portfolio_overview with upcoming dividends).

**Required:** Add capabilities to FinancialAnalyst or create CorporateActionsAgent.

**Implementation:**
```python
# backend/app/agents/financial_analyst.py (add to existing agent)
class FinancialAnalyst:
    # ... existing capabilities ...

    async def corporate_actions_upcoming(self, portfolio_id: str, days_ahead: int = 30):
        """
        Capability: corporate_actions.upcoming
        Get upcoming corporate actions for portfolio
        """
        service = CorporateActionsService()
        async with self.get_connection() as conn:
            result = await service.get_upcoming_actions(conn, portfolio_id, days_ahead)
        return result
```

**Pattern Integration:**
```json
{
  "id": "portfolio_overview_with_actions",
  "steps": [
    {"capability": "ledger.positions", "args": {"portfolio_id": "{{inputs.portfolio_id}}"}, "as": "positions"},
    {"capability": "corporate_actions.upcoming", "args": {"portfolio_id": "{{inputs.portfolio_id}}"}, "as": "upcoming_actions"},
    {"capability": "metrics.compute_twr", "args": {"portfolio_id": "{{inputs.portfolio_id}}"}, "as": "performance"}
  ]
}
```

**Estimated Effort:** 2-3 hours (agent method + pattern updates)

---

### Medium Priority Gaps (P1 - Enhanced Functionality)

#### Gap 5: No Historical Corporate Actions Tracking
**Current State:** Can see past dividends in transactions, but no historical view of other action types.

**Impact:** Cannot analyze historical earnings reactions, past splits, etc.

**Required:**
- Service method: `get_historical_actions(portfolio_id, days_back=90)`
- UI tab to switch between "Upcoming" and "Historical"

**Estimated Effort:** 3-4 hours

#### Gap 6: No Portfolio Impact Calculations
**Current State:** Mock data shows fake impact ("You own 100 shares...").

**Impact:** Cannot see real financial impact of upcoming actions.

**Required:**
- Calculate expected dividend payments (shares × dividend amount)
- Show split impact on position size
- Highlight earnings releases for high-weight positions

**Estimated Effort:** 2-3 hours (part of service implementation)

#### Gap 7: No Notifications/Alerts
**Current State:** No way to get notified about upcoming actions.

**Impact:** User must manually check the page.

**Required:**
- Alert when dividend ex-date approaches (7 days before)
- Alert when earnings release scheduled (1 day before)
- Integration with existing AlertsAgent

**Estimated Effort:** 4-5 hours

---

### Low Priority Gaps (P2 - Nice to Have)

#### Gap 8: No Calendar View
**Current State:** Table view only.

**Impact:** Hard to visualize upcoming events over time.

**Required:** Calendar UI component showing actions by date.

**Estimated Effort:** 6-8 hours

#### Gap 9: No Export Functionality
**Current State:** Cannot export corporate actions list.

**Impact:** Cannot share or analyze in Excel.

**Required:** CSV/PDF export via ReportsAgent.

**Estimated Effort:** 2-3 hours

#### Gap 10: No Multi-Portfolio View
**Current State:** Shows one portfolio at a time.

**Impact:** Cannot see all corporate actions across all portfolios.

**Required:** Aggregated view with portfolio filter.

**Estimated Effort:** 3-4 hours

---

## Recommendations

### Phase 1: MVP Implementation (P0 - Critical)
**Goal:** Get basic corporate actions working with real data

**Tasks:**
1. ✅ Create migration for `corporate_actions` table (2-3 hours)
2. ✅ Implement CorporateActionsService (4-6 hours)
3. ✅ Rewrite `/api/corporate-actions` endpoint to use service (1-2 hours)
4. ✅ Integrate Yahoo Finance data fetcher (6-8 hours)
5. ✅ Add agent capability `corporate_actions.upcoming` (2-3 hours)
6. ✅ Set up daily scheduled job to fetch data (2-3 hours)

**Total Effort:** ~18-25 hours (3-4 days)

**Outcome:**
- Real upcoming dividends displayed for portfolio holdings
- Real stock splits displayed
- Portfolio-specific impact calculations
- Data refreshes daily

### Phase 2: Enhanced Functionality (P1)
**Goal:** Make feature production-ready

**Tasks:**
1. ✅ Add historical corporate actions view (3-4 hours)
2. ✅ Implement earnings calendar integration (4-5 hours)
3. ✅ Add alerts for upcoming actions (4-5 hours)
4. ✅ Improve error handling and data quality checks (2-3 hours)

**Total Effort:** ~13-17 hours (2-3 days)

### Phase 3: Advanced Features (P2)
**Goal:** Best-in-class corporate actions tracking

**Tasks:**
1. ✅ Calendar view UI (6-8 hours)
2. ✅ Export functionality (2-3 hours)
3. ✅ Multi-portfolio aggregation (3-4 hours)
4. ✅ Manual action entry UI (4-5 hours)

**Total Effort:** ~15-20 hours (2-3 days)

---

## Database Schema Proposal

### Migration: `014_create_corporate_actions_table.sql`

```sql
-- Migration: Create Corporate Actions Table
-- Purpose: Track upcoming and historical corporate actions for portfolio holdings
-- Date: 2025-11-03

BEGIN;

-- ============================================================================
-- Step 1: Create corporate_actions table
-- ============================================================================

CREATE TABLE IF NOT EXISTS corporate_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID NOT NULL REFERENCES securities(id) ON DELETE CASCADE,

    -- Action type
    type TEXT NOT NULL,

    -- Dates (varies by action type)
    announcement_date DATE,      -- All types
    ex_date DATE,                 -- Dividends, splits
    record_date DATE,             -- Dividends
    payment_date DATE,            -- Dividends
    effective_date DATE,          -- Splits, mergers
    earnings_date DATE,           -- Earnings
    expected_close_date DATE,     -- Mergers

    -- Financial details
    amount NUMERIC(19, 4),        -- Dividend amount per share
    currency TEXT DEFAULT 'USD',
    ratio TEXT,                   -- Split ratio (e.g., "20:1", "3:2")
    consensus_eps NUMERIC(10, 2), -- Earnings consensus estimate
    prior_eps NUMERIC(10, 2),     -- Prior quarter EPS

    -- Text details
    terms TEXT,                   -- Merger/acquisition terms
    description TEXT,             -- General description
    impact_note TEXT,             -- Portfolio-specific impact notes

    -- Status and source
    status TEXT NOT NULL DEFAULT 'announced',
    source TEXT NOT NULL,         -- 'yahoo_finance', 'alpha_vantage', 'manual', etc.

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    fetched_at TIMESTAMPTZ DEFAULT NOW(),  -- When data was last fetched

    -- Constraints
    CONSTRAINT chk_corporate_action_type CHECK (
        type IN ('dividend', 'split', 'earnings', 'merger', 'buyback', 'spinoff')
    ),
    CONSTRAINT chk_corporate_action_status CHECK (
        status IN ('announced', 'scheduled', 'completed', 'cancelled')
    ),

    -- Unique constraint: Same security + type + date should not duplicate
    CONSTRAINT uq_corporate_action_identity UNIQUE (
        security_id, type,
        COALESCE(ex_date, payment_date, earnings_date, effective_date)
    )
);

-- ============================================================================
-- Step 2: Create indexes for performance
-- ============================================================================

-- Primary lookups by security
CREATE INDEX idx_corporate_actions_security_id ON corporate_actions(security_id);

-- Date range queries (most common)
CREATE INDEX idx_corporate_actions_ex_date ON corporate_actions(ex_date)
    WHERE ex_date IS NOT NULL;
CREATE INDEX idx_corporate_actions_payment_date ON corporate_actions(payment_date)
    WHERE payment_date IS NOT NULL;
CREATE INDEX idx_corporate_actions_earnings_date ON corporate_actions(earnings_date)
    WHERE earnings_date IS NOT NULL;

-- Status filtering
CREATE INDEX idx_corporate_actions_status ON corporate_actions(status);

-- Type filtering
CREATE INDEX idx_corporate_actions_type ON corporate_actions(type);

-- Composite index for common query pattern
CREATE INDEX idx_corporate_actions_security_status_dates ON corporate_actions(
    security_id, status,
    COALESCE(ex_date, payment_date, earnings_date, effective_date)
);

-- ============================================================================
-- Step 3: Add comments
-- ============================================================================

COMMENT ON TABLE corporate_actions IS 'Upcoming and historical corporate actions for securities';
COMMENT ON COLUMN corporate_actions.type IS 'Action type: dividend, split, earnings, merger, buyback, spinoff';
COMMENT ON COLUMN corporate_actions.ex_date IS 'Ex-dividend/ex-split date (used for dividends and splits)';
COMMENT ON COLUMN corporate_actions.payment_date IS 'Dividend payment date';
COMMENT ON COLUMN corporate_actions.earnings_date IS 'Earnings release date';
COMMENT ON COLUMN corporate_actions.amount IS 'Dividend amount per share (in currency specified)';
COMMENT ON COLUMN corporate_actions.ratio IS 'Split ratio (e.g., "2:1", "3:2") - new:old';
COMMENT ON COLUMN corporate_actions.status IS 'Action status: announced, scheduled, completed, cancelled';
COMMENT ON COLUMN corporate_actions.source IS 'Data source: yahoo_finance, alpha_vantage, manual, etc.';

-- ============================================================================
-- Step 4: Create helper function to get upcoming actions for portfolio
-- ============================================================================

CREATE OR REPLACE FUNCTION get_upcoming_corporate_actions(
    p_portfolio_id UUID,
    p_days_ahead INT DEFAULT 30
) RETURNS TABLE (
    action_id UUID,
    symbol TEXT,
    security_name TEXT,
    action_type TEXT,
    action_date DATE,
    amount NUMERIC,
    ratio TEXT,
    shares_owned NUMERIC,
    impact TEXT,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ca.id AS action_id,
        s.symbol,
        s.name AS security_name,
        ca.type AS action_type,
        COALESCE(ca.ex_date, ca.payment_date, ca.earnings_date, ca.effective_date) AS action_date,
        ca.amount,
        ca.ratio,
        holdings.total_qty AS shares_owned,
        CASE
            WHEN ca.type = 'dividend' THEN
                format('Expected payment: $%.2f', holdings.total_qty * ca.amount)
            WHEN ca.type = 'split' THEN
                format('Your %.0f shares will adjust', holdings.total_qty)
            WHEN ca.type = 'earnings' THEN
                'Potential volatility'
            ELSE ca.description
        END AS impact,
        ca.status
    FROM corporate_actions ca
    JOIN securities s ON ca.security_id = s.id
    JOIN (
        SELECT security_id, SUM(qty) AS total_qty
        FROM lots
        WHERE portfolio_id = p_portfolio_id AND qty > 0
        GROUP BY security_id
    ) holdings ON ca.security_id = holdings.security_id
    WHERE ca.status IN ('announced', 'scheduled')
      AND COALESCE(ca.ex_date, ca.payment_date, ca.earnings_date, ca.effective_date)
          BETWEEN CURRENT_DATE AND CURRENT_DATE + p_days_ahead
    ORDER BY action_date ASC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_upcoming_corporate_actions IS
    'Get upcoming corporate actions for a portfolio with impact calculations';

-- ============================================================================
-- Step 5: Insert sample data for testing
-- ============================================================================

-- Note: This would normally be populated by the CorporateActionsFetcher service
-- Here we add just one example for testing

DO $$
DECLARE
    v_security_id UUID;
BEGIN
    -- Find AAPL security (if it exists)
    SELECT id INTO v_security_id FROM securities WHERE symbol = 'AAPL' LIMIT 1;

    IF v_security_id IS NOT NULL THEN
        -- Insert sample upcoming dividend
        INSERT INTO corporate_actions (
            security_id, type, ex_date, record_date, payment_date,
            amount, currency, status, source, description
        ) VALUES (
            v_security_id,
            'dividend',
            CURRENT_DATE + 14,  -- 2 weeks from now
            CURRENT_DATE + 16,
            CURRENT_DATE + 21,
            0.24,
            'USD',
            'announced',
            'manual',
            'Quarterly dividend'
        )
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

-- ============================================================================
-- Step 6: Verification
-- ============================================================================

-- Verify table created
SELECT
    table_name,
    (SELECT COUNT(*) FROM corporate_actions) AS row_count
FROM information_schema.tables
WHERE table_name = 'corporate_actions';

-- Verify indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'corporate_actions'
ORDER BY indexname;

-- Test helper function (if there's data)
-- SELECT * FROM get_upcoming_corporate_actions(
--     '11111111-1111-1111-1111-111111111111'::UUID,  -- portfolio_id
--     30  -- days_ahead
-- );

COMMIT;

SELECT 'Migration 014: Corporate actions table created successfully' AS status;
```

---

## Service Layer Proposal

### File: `backend/app/services/corporate_actions.py`

```python
"""
Corporate Actions Service
Handles fetching, storing, and querying corporate actions for portfolio holdings
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

class CorporateActionsService:
    """Service for managing corporate actions data"""

    async def get_upcoming_actions(
        self,
        conn,
        portfolio_id: str,
        days_ahead: int = 30,
        action_type: Optional[str] = None
    ) -> Dict:
        """
        Get upcoming corporate actions for portfolio holdings

        Args:
            conn: Database connection
            portfolio_id: Portfolio UUID
            days_ahead: Number of days to look ahead (default: 30)
            action_type: Filter by type ('dividend', 'split', etc.) or None for all

        Returns:
            {
                "portfolio_id": "...",
                "time_horizon_days": 30,
                "actions": [...],
                "summary": {...}
            }
        """
        try:
            # Build query with optional type filter
            type_filter = ""
            params = [portfolio_id, days_ahead]

            if action_type and action_type != 'all':
                type_filter = "AND ca.type = $3"
                params.append(action_type)

            query = f"""
                SELECT
                    ca.id,
                    ca.type,
                    ca.announcement_date,
                    ca.ex_date,
                    ca.record_date,
                    ca.payment_date,
                    ca.earnings_date,
                    ca.effective_date,
                    ca.amount,
                    ca.currency,
                    ca.ratio,
                    ca.consensus_eps,
                    ca.prior_eps,
                    ca.terms,
                    ca.description,
                    ca.status,
                    s.symbol,
                    s.name AS security_name,
                    holdings.total_qty AS shares_owned
                FROM corporate_actions ca
                JOIN securities s ON ca.security_id = s.id
                JOIN (
                    SELECT security_id, SUM(qty) AS total_qty
                    FROM lots
                    WHERE portfolio_id = $1 AND qty > 0
                    GROUP BY security_id
                ) holdings ON ca.security_id = holdings.security_id
                WHERE ca.status IN ('announced', 'scheduled')
                  AND COALESCE(ca.ex_date, ca.payment_date, ca.earnings_date, ca.effective_date)
                      BETWEEN CURRENT_DATE AND CURRENT_DATE + $2
                  {type_filter}
                ORDER BY COALESCE(ca.ex_date, ca.payment_date, ca.earnings_date, ca.effective_date) ASC
            """

            rows = await conn.fetch(query, *params)

            # Transform rows to dicts and add calculated impact
            actions = []
            for row in rows:
                action = dict(row)
                action['impact'] = self._calculate_impact(action)
                action['date'] = self._get_primary_date(action)
                actions.append(action)

            summary = self._calculate_summary(actions)

            return {
                "portfolio_id": portfolio_id,
                "time_horizon_days": days_ahead,
                "actions": actions,
                "summary": summary,
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching corporate actions: {e}")
            raise

    def _calculate_impact(self, action: Dict) -> str:
        """Calculate portfolio-specific impact of corporate action"""
        action_type = action['type']
        shares = action.get('shares_owned', 0)

        if action_type == 'dividend':
            amount = action.get('amount', 0)
            currency = action.get('currency', 'USD')
            expected = shares * amount
            return f"You own {shares:.0f} shares. Expected payment: ${expected:.2f} {currency}"

        elif action_type == 'split':
            ratio = action.get('ratio', '1:1')
            # Parse ratio (e.g., "2:1" means 2 new shares for 1 old)
            try:
                new_shares, old_shares = map(int, ratio.split(':'))
                new_qty = shares * new_shares / old_shares
                return f"Your {shares:.0f} shares will become {new_qty:.0f} shares"
            except:
                return f"Stock split {ratio} announced"

        elif action_type == 'earnings':
            eps = action.get('consensus_eps')
            if eps:
                return f"Earnings expected: EPS ${eps:.2f}. Potential volatility."
            return "Earnings release. Potential volatility."

        elif action_type == 'merger':
            terms = action.get('terms', 'Review terms')
            return f"Merger announced. {terms}. Review position for tax implications."

        elif action_type == 'buyback':
            return "Share buyback program. May support stock price."

        elif action_type == 'spinoff':
            return "Spinoff announced. Review new entity details."

        return action.get('description', '--')

    def _get_primary_date(self, action: Dict) -> str:
        """Get the most relevant date for display"""
        # Priority: ex_date > payment_date > earnings_date > effective_date > announcement_date
        for field in ['ex_date', 'payment_date', 'earnings_date', 'effective_date', 'announcement_date']:
            date = action.get(field)
            if date:
                return date.isoformat() if hasattr(date, 'isoformat') else str(date)
        return '--'

    def _calculate_summary(self, actions: List[Dict]) -> Dict:
        """Calculate summary statistics"""
        summary = {
            "total_actions": len(actions),
            "dividends_expected": 0.0,
            "splits_pending": 0,
            "earnings_releases": 0,
            "mergers_acquisitions": 0,
            "buybacks": 0
        }

        for action in actions:
            action_type = action['type']

            if action_type == 'dividend':
                amount = action.get('amount', 0)
                shares = action.get('shares_owned', 0)
                summary['dividends_expected'] += (amount * shares)

            elif action_type == 'split':
                summary['splits_pending'] += 1

            elif action_type == 'earnings':
                summary['earnings_releases'] += 1

            elif action_type == 'merger':
                summary['mergers_acquisitions'] += 1

            elif action_type == 'buyback':
                summary['buybacks'] += 1

        return summary

    async def get_historical_actions(
        self,
        conn,
        portfolio_id: str,
        days_back: int = 90,
        action_type: Optional[str] = None
    ) -> Dict:
        """
        Get historical corporate actions for portfolio holdings

        Similar to get_upcoming_actions but looks backwards in time
        and filters for status = 'completed'
        """
        # Similar implementation to get_upcoming_actions
        # but with date range: CURRENT_DATE - days_back to CURRENT_DATE
        # and status = 'completed'
        pass

    async def get_action_by_id(self, conn, action_id: UUID) -> Optional[Dict]:
        """Get specific corporate action by ID"""
        row = await conn.fetchrow("""
            SELECT
                ca.*,
                s.symbol,
                s.name AS security_name
            FROM corporate_actions ca
            JOIN securities s ON ca.security_id = s.id
            WHERE ca.id = $1
        """, action_id)

        if row:
            return dict(row)
        return None

    async def upsert_action(
        self,
        conn,
        security_id: UUID,
        action_type: str,
        **kwargs
    ) -> UUID:
        """
        Insert or update a corporate action

        Used by CorporateActionsFetcher to populate data
        """
        query = """
            INSERT INTO corporate_actions (
                security_id, type, announcement_date, ex_date, record_date,
                payment_date, effective_date, earnings_date,
                amount, currency, ratio, consensus_eps, prior_eps,
                terms, description, status, source
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
            )
            ON CONFLICT (security_id, type, COALESCE(ex_date, payment_date, earnings_date, effective_date))
            DO UPDATE SET
                announcement_date = EXCLUDED.announcement_date,
                amount = EXCLUDED.amount,
                ratio = EXCLUDED.ratio,
                consensus_eps = EXCLUDED.consensus_eps,
                terms = EXCLUDED.terms,
                description = EXCLUDED.description,
                status = EXCLUDED.status,
                updated_at = NOW(),
                fetched_at = NOW()
            RETURNING id
        """

        action_id = await conn.fetchval(
            query,
            security_id,
            action_type,
            kwargs.get('announcement_date'),
            kwargs.get('ex_date'),
            kwargs.get('record_date'),
            kwargs.get('payment_date'),
            kwargs.get('effective_date'),
            kwargs.get('earnings_date'),
            kwargs.get('amount'),
            kwargs.get('currency', 'USD'),
            kwargs.get('ratio'),
            kwargs.get('consensus_eps'),
            kwargs.get('prior_eps'),
            kwargs.get('terms'),
            kwargs.get('description'),
            kwargs.get('status', 'announced'),
            kwargs.get('source', 'manual')
        )

        return action_id
```

---

## Data Fetcher Proposal

### File: `backend/app/services/corporate_actions_fetcher.py`

```python
"""
Corporate Actions Data Fetcher
Fetches corporate actions data from external APIs (Yahoo Finance, Alpha Vantage, etc.)
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import logging

from backend.app.services.corporate_actions import CorporateActionsService

logger = logging.getLogger(__name__)

class CorporateActionsFetcher:
    """Fetch corporate actions from external sources"""

    def __init__(self):
        self.service = CorporateActionsService()

    async def fetch_dividends_for_symbol(
        self,
        conn,
        symbol: str,
        days_ahead: int = 90
    ) -> int:
        """
        Fetch upcoming dividends from Yahoo Finance for a symbol

        Returns:
            Number of actions fetched
        """
        try:
            # Get security from database
            security = await conn.fetchrow(
                "SELECT id FROM securities WHERE symbol = $1", symbol
            )

            if not security:
                logger.warning(f"Security {symbol} not found in database")
                return 0

            # Fetch from Yahoo Finance
            ticker = yf.Ticker(symbol)

            # Get dividend history (includes future announced dividends)
            dividends = ticker.dividends

            # Filter for future dividends (within days_ahead)
            cutoff_date = datetime.now() + timedelta(days=days_ahead)
            count = 0

            for date, amount in dividends.items():
                if datetime.now() < date.to_pydatetime() <= cutoff_date:
                    # Insert into database
                    await self.service.upsert_action(
                        conn,
                        security_id=security['id'],
                        action_type='dividend',
                        ex_date=date.date(),
                        payment_date=date.date() + timedelta(days=7),  # Estimate
                        amount=float(amount),
                        currency='USD',
                        status='announced',
                        source='yahoo_finance',
                        description=f'{symbol} quarterly dividend'
                    )
                    count += 1

            logger.info(f"Fetched {count} dividends for {symbol}")
            return count

        except Exception as e:
            logger.error(f"Error fetching dividends for {symbol}: {e}")
            return 0

    async def fetch_splits_for_symbol(self, conn, symbol: str) -> int:
        """Fetch upcoming stock splits from Yahoo Finance"""
        try:
            security = await conn.fetchrow(
                "SELECT id FROM securities WHERE symbol = $1", symbol
            )

            if not security:
                return 0

            ticker = yf.Ticker(symbol)
            splits = ticker.splits

            # Filter for future splits (announced but not yet effective)
            cutoff_date = datetime.now() + timedelta(days=90)
            count = 0

            for date, ratio in splits.items():
                if datetime.now() < date.to_pydatetime() <= cutoff_date:
                    # Convert ratio to string (e.g., 2.0 → "2:1")
                    ratio_str = f"{int(ratio)}:1" if ratio.is_integer() else f"{ratio}:1"

                    await self.service.upsert_action(
                        conn,
                        security_id=security['id'],
                        action_type='split',
                        effective_date=date.date(),
                        ratio=ratio_str,
                        status='announced',
                        source='yahoo_finance',
                        description=f'{symbol} stock split'
                    )
                    count += 1

            logger.info(f"Fetched {count} splits for {symbol}")
            return count

        except Exception as e:
            logger.error(f"Error fetching splits for {symbol}: {e}")
            return 0

    async def fetch_earnings_for_symbol(self, conn, symbol: str) -> int:
        """Fetch upcoming earnings dates from Yahoo Finance"""
        try:
            security = await conn.fetchrow(
                "SELECT id FROM securities WHERE symbol = $1", symbol
            )

            if not security:
                return 0

            ticker = yf.Ticker(symbol)

            # Get earnings calendar (if available)
            calendar = ticker.calendar

            if calendar is not None and 'Earnings Date' in calendar:
                earnings_date = calendar['Earnings Date']

                if isinstance(earnings_date, (list, tuple)):
                    earnings_date = earnings_date[0]  # Take first date if range

                # Only add if in future
                if earnings_date > datetime.now():
                    await self.service.upsert_action(
                        conn,
                        security_id=security['id'],
                        action_type='earnings',
                        earnings_date=earnings_date.date(),
                        status='scheduled',
                        source='yahoo_finance',
                        description=f'{symbol} earnings release'
                    )

                    logger.info(f"Fetched earnings date for {symbol}")
                    return 1

            return 0

        except Exception as e:
            logger.error(f"Error fetching earnings for {symbol}: {e}")
            return 0

    async def fetch_all_holdings_actions(
        self,
        conn,
        portfolio_id: str,
        days_ahead: int = 90
    ) -> Dict[str, int]:
        """
        Fetch corporate actions for all holdings in a portfolio

        Returns:
            {"AAPL": 3, "GOOGL": 2, ...}  # Count of actions per symbol
        """
        # Get all holdings
        holdings = await conn.fetch("""
            SELECT DISTINCT s.symbol
            FROM lots l
            JOIN securities s ON l.security_id = s.id
            WHERE l.portfolio_id = $1 AND l.qty > 0
        """, portfolio_id)

        results = {}
        total = 0

        for holding in holdings:
            symbol = holding['symbol']

            # Fetch dividends
            div_count = await self.fetch_dividends_for_symbol(conn, symbol, days_ahead)

            # Fetch splits
            split_count = await self.fetch_splits_for_symbol(conn, symbol)

            # Fetch earnings
            earn_count = await self.fetch_earnings_for_symbol(conn, symbol)

            count = div_count + split_count + earn_count
            results[symbol] = count
            total += count

        logger.info(f"Fetched {total} corporate actions for portfolio {portfolio_id}")
        return results

    async def fetch_all_portfolios(self, conn) -> int:
        """
        Fetch corporate actions for all portfolios

        Should be run as a daily scheduled job
        """
        portfolios = await conn.fetch("SELECT id FROM portfolios")

        total = 0
        for portfolio in portfolios:
            results = await self.fetch_all_holdings_actions(conn, portfolio['id'])
            total += sum(results.values())

        logger.info(f"Fetched {total} total corporate actions for all portfolios")
        return total
```

---

## Endpoint Rewrite Proposal

### File: `combined_server.py` (updated endpoint)

```python
@app.get("/api/corporate-actions", response_model=SuccessResponse)
async def get_corporate_actions(
    portfolio_id: Optional[str] = Query(None),
    days_ahead: int = Query(30, ge=1, le=365),
    action_type: Optional[str] = Query('all'),
    user: dict = Depends(require_auth)
):
    """
    Get upcoming corporate actions for portfolio holdings
    AUTH_STATUS: MIGRATED - Sprint 2

    Query Parameters:
        - portfolio_id: Portfolio UUID (optional, defaults to user's default portfolio)
        - days_ahead: Number of days to look ahead (default: 30, max: 365)
        - action_type: Filter by type ('all', 'dividend', 'split', 'earnings', 'merger', 'buyback')

    Returns:
        {
            "success": true,
            "data": {
                "portfolio_id": "...",
                "time_horizon_days": 30,
                "actions": [...],
                "summary": {...},
                "last_updated": "2025-11-03T..."
            }
        }
    """
    try:
        # Get portfolio_id (use default if not provided)
        if not portfolio_id:
            # Get user's default portfolio
            async with get_db_connection_with_rls(user_id=user["id"]) as conn:
                portfolio = await conn.fetchrow(
                    "SELECT id FROM portfolios WHERE user_id = $1 LIMIT 1",
                    user["id"]
                )
                if not portfolio:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No portfolio found for user"
                    )
                portfolio_id = str(portfolio['id'])

        # Fetch corporate actions
        service = CorporateActionsService()
        async with get_db_connection_with_rls(user_id=user["id"]) as conn:
            actions_data = await service.get_upcoming_actions(
                conn,
                portfolio_id,
                days_ahead,
                action_type if action_type != 'all' else None
            )

        return SuccessResponse(data=actions_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting corporate actions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get corporate actions"
        )
```

---

## Testing Plan

### Unit Tests

1. **Service Tests** (`test_corporate_actions_service.py`)
   - Test `get_upcoming_actions()` with various portfolios
   - Test impact calculations for each action type
   - Test date filtering
   - Test type filtering
   - Test empty portfolio
   - Test portfolio with no upcoming actions

2. **Fetcher Tests** (`test_corporate_actions_fetcher.py`)
   - Mock Yahoo Finance API responses
   - Test dividend fetching
   - Test split fetching
   - Test earnings fetching
   - Test error handling (API timeout, invalid symbol)

3. **Endpoint Tests** (`test_corporate_actions_endpoint.py`)
   - Test GET /api/corporate-actions with auth
   - Test without auth (should fail)
   - Test with invalid portfolio_id
   - Test date range boundaries
   - Test type filtering

### Integration Tests

1. **End-to-End Test**
   - Create test portfolio with holdings (AAPL, MSFT)
   - Run fetcher to populate corporate_actions table
   - Query endpoint and verify results
   - Verify impact calculations match expected values

2. **Scheduled Job Test**
   - Run daily job manually
   - Verify all portfolios updated
   - Check for duplicate prevention

### Manual Testing Checklist

- [ ] UI loads without errors
- [ ] Filter controls work
- [ ] Date range selector updates results
- [ ] Action type filter works
- [ ] Refresh button fetches new data
- [ ] Table displays correctly
- [ ] Empty state shows when no actions
- [ ] Error state shows on API failure
- [ ] Impact calculations are accurate
- [ ] Portfolio switching works
- [ ] Real dividend amounts displayed
- [ ] Real split ratios displayed
- [ ] Real earnings dates displayed

---

## Migration from Mock to Real Data

### Step-by-Step Migration Plan

1. **Create database table** (1 hour)
   - Run migration 014
   - Verify table exists
   - Verify indexes created

2. **Implement service layer** (4 hours)
   - Create `corporate_actions.py` service
   - Implement `get_upcoming_actions()`
   - Implement helper methods
   - Write unit tests

3. **Implement data fetcher** (6 hours)
   - Create `corporate_actions_fetcher.py`
   - Implement Yahoo Finance integration
   - Add error handling and retries
   - Write tests with mocked API

4. **Update endpoint** (2 hours)
   - Rewrite `get_corporate_actions()` to use service
   - Remove mock data
   - Test with real data

5. **Set up scheduled job** (2 hours)
   - Add APScheduler (if not already installed)
   - Create daily job to run fetcher
   - Test job execution
   - Add logging

6. **Integration testing** (3 hours)
   - End-to-end testing
   - Manual UI testing
   - Performance testing
   - Error scenario testing

7. **Documentation** (1 hour)
   - Update API docs
   - Add admin guide for manual action entry
   - Document data sources

**Total: ~19 hours (2-3 days)**

---

## Alternative Approaches

### Approach 1: Use External API Directly from Frontend (Not Recommended)
**Pros:**
- No backend work needed
- Real-time data

**Cons:**
- ❌ API keys exposed in frontend
- ❌ Rate limits applied per user
- ❌ No caching
- ❌ Cannot calculate portfolio-specific impact
- ❌ Doesn't integrate with database

**Verdict:** ❌ Not suitable for production

### Approach 2: Manual Data Entry Only (Acceptable for MVP)
**Pros:**
- No external API integration needed
- Full control over data
- No rate limits

**Cons:**
- ⚠️ Requires manual effort to keep updated
- ⚠️ Scales poorly with portfolio size
- ⚠️ May miss actions

**Verdict:** ⚠️ Acceptable for alpha, but should add API integration later

### Approach 3: Hybrid (Recommended)
**Pros:**
- API integration for dividends/splits (reliable data)
- Manual entry for mergers/buybacks (less structured data)
- Best of both worlds

**Cons:**
- More complex implementation

**Verdict:** ✅ Recommended for production

---

## Conclusion

### Current State: ❌ NOT FUNCTIONAL

The Corporate Actions page is **currently a mock implementation** with:
- ✅ Excellent UI design
- ❌ No database integration
- ❌ No real data sources
- ❌ No portfolio-specific calculations
- ❌ Hardcoded mock data

### Required to Make Functional (P0 - MVP):

1. **Database table** for corporate_actions (2-3 hours)
2. **Service layer** to query and format data (4-6 hours)
3. **Data fetcher** to populate from Yahoo Finance (6-8 hours)
4. **Endpoint rewrite** to use service (1-2 hours)
5. **Scheduled job** to keep data fresh (2-3 hours)

**Total Effort: ~18-25 hours (3-4 business days)**

### Post-Implementation State: ✅ FUNCTIONAL

After implementation:
- ✅ Real dividend data for portfolio holdings
- ✅ Real stock splits
- ✅ Real earnings dates
- ✅ Portfolio-specific impact calculations
- ✅ Daily data refresh
- ✅ Filtering and date range controls

### Recommendation:

**PRIORITY: HIGH (P0)** - This feature should be implemented soon because:
1. Users expect accurate dividend tracking
2. Split announcements can significantly impact portfolio value
3. Earnings dates create volatility risk
4. Current mock data is misleading

**TIMELINE: Sprint 3 (next 1-2 weeks)**

**OWNER: Backend developer with database/API integration experience**

---

**Report Created:** November 3, 2025
**Status:** ✅ COMPREHENSIVE REVIEW COMPLETE
**Next Steps:** Present to team, prioritize implementation, assign developer
