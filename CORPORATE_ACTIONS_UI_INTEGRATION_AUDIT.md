# Corporate Actions UI Integration - Complete Audit & Implementation Plan

**Date:** November 3, 2025  
**Status:** 🔍 **AUDIT COMPLETE - READY FOR IMPLEMENTATION**  
**Purpose:** Comprehensive audit of corporate actions UI integration and plan to make it work from user holdings

---

## 📊 Executive Summary

The corporate actions feature has a **fully functional UI** but **completely missing backend implementation**. The UI is production-ready, but the endpoint returns empty data. This audit identifies all gaps and provides a complete implementation plan to make it work with user holdings.

**Key Finding:** Polygon provider already has `get_dividends()` and `get_splits()` methods that can fetch upcoming events. We just need to connect them to the user's holdings.

---

## 🎯 Current State Analysis

### 1. UI Component ✅ **PRODUCTION READY**

**Location:** `full_ui.html` lines 11315-11620

**Features:**
- ✅ Fully functional React component
- ✅ Fetches from `/api/corporate-actions?portfolio_id=...&days_ahead=90`
- ✅ Expects `response.data.data.actions` array
- ✅ Handles multiple action types: `dividend`, `split`, `earnings`, `buyback`, `merger`
- ✅ Filters by type and date range
- ✅ Shows loading states and error handling
- ✅ Displays action details with proper formatting
- ✅ Shows "No corporate actions found" when empty

**Expected Data Structure:**
```javascript
{
  actions: [
    {
      id: "uuid",
      symbol: "AAPL",
      type: "dividend",  // or "split", "earnings", "buyback", "merger"
      date: "2024-12-15",  // or ex_date, payment_date, announcement_date
      amount: 0.24,  // for dividends
      ratio: 2.0,  // for splits
      status: "scheduled",  // or "announced", "completed"
      details: "...",
      impact: "..."
    }
  ],
  summary: {
    total_actions: 5,
    dividends_expected: 120.00,
    splits_pending: 1,
    earnings_releases: 2,
    mergers_acquisitions: 0
  }
}
```

**UI Data Processing:**
- Line 11345: `setCorporateActions(response.data.data.actions || [])`
- Line 11357-11360: Filters by `filterType` and `filterDays`
- Line 11363-11379: Formats action details based on type
- Line 11382-11397: Formats dates (handles multiple date field names)

---

### 2. Backend Endpoint ⚠️ **RETURNS EMPTY DATA**

**Location:** `combined_server.py` lines 4645-4700

**Current Implementation:**
```python
@app.get("/api/corporate-actions", response_model=SuccessResponse)
async def get_corporate_actions(
    portfolio_id: str = Query(..., description="Portfolio ID"),
    days_ahead: int = Query(30, ge=1, le=365, description="Number of days to look ahead"),
    user: dict = Depends(require_auth)
):
    # Returns empty array with metadata
    response = {
        "portfolio_id": portfolio_id,
        "time_horizon_days": days_ahead,
        "actions": [],  # ❌ EMPTY
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

**Issues:**
1. ❌ Returns hardcoded empty array
2. ❌ No database query
3. ❌ No external API integration
4. ❌ No holdings lookup

**Expected Response Structure:**
```python
{
    "portfolio_id": "uuid",
    "time_horizon_days": 90,
    "actions": [...],  # List of upcoming corporate actions
    "summary": {
        "total_actions": 5,
        "dividends_expected": 120.00,
        "splits_pending": 1,
        "earnings_releases": 2,
        "mergers_acquisitions": 0
    },
    "notifications": {
        "urgent": [...],  # Actions requiring immediate attention
        "informational": [...]
    },
    "last_updated": "2025-11-03T10:00:00Z",
    "metadata": {...}
}
```

---

### 3. CorporateActionsService ⚠️ **HISTORICAL ONLY**

**Location:** `backend/app/services/corporate_actions.py`

**Current Methods:**
- ✅ `record_dividend()` - Records past dividends
- ✅ `record_split()` - Records past splits
- ✅ `record_withholding_tax()` - Records ADR withholding tax
- ✅ `get_dividend_history()` - Gets historical dividends from `transactions` table
- ❌ **MISSING:** `get_upcoming_actions()` - Gets future events

**Service Purpose:**
- Designed for **recording** corporate actions after they happen
- NOT designed for **fetching** upcoming events
- Works with `transactions` table (historical data)

**Gap:** No method to get upcoming corporate actions for portfolio holdings.

---

### 4. Database Schema ⚠️ **NO TABLE FOR UPCOMING EVENTS**

**Location:** `backend/db/migrations/008_add_corporate_actions_support.sql`

**What Exists:**
- ✅ `transactions` table with `pay_date`, `ex_date`, `pay_fx_rate_id` columns
- ✅ Columns for recording historical corporate actions
- ❌ **NO `corporate_actions` table for upcoming events**

**Migration 008 Adds:**
- Columns to `transactions` table for recording dividends/splits
- FX rate tracking for ADR dividends
- Helper functions for FX rate lookup

**What's Missing:**
- Table to store upcoming corporate actions
- No scheduled data refresh mechanism
- No external data source integration

---

### 5. Polygon Provider ✅ **READY TO USE**

**Location:** `backend/app/integrations/polygon_provider.py`

**Existing Methods:**
```python
async def get_dividends(
    self,
    symbol: Optional[str] = None,
    ex_dividend_date: Optional[date] = None,
    declaration_date: Optional[date] = None,
    limit: int = 1000,
) -> List[Dict]:
    """
    Get dividends from Polygon API.
    Returns both historical AND upcoming dividends.
    """

async def get_splits(
    self,
    symbol: Optional[str] = None,
    execution_date: Optional[date] = None,
    limit: int = 1000
) -> List[Dict]:
    """
    Get stock splits from Polygon API.
    Returns both historical AND upcoming splits.
    """
```

**Polygon Response Format:**
```python
# Dividends
{
    "ticker": "AAPL",
    "ex_dividend_date": "2024-12-06",
    "pay_date": "2024-12-12",
    "record_date": "2024-12-07",
    "declaration_date": "2024-11-02",
    "cash_amount": 0.24,
    "currency": "USD"
}

# Splits
{
    "ticker": "AAPL",
    "execution_date": "2024-08-31",
    "split_from": 1,
    "split_to": 4,
    "split_ratio": 0.25  # calculated: split_from / split_to
}
```

**Key Features:**
- ✅ Already implemented and working
- ✅ Returns future events if `ex_dividend_date > today`
- ✅ Includes pay_date (critical for ADR FX accuracy)
- ✅ Rate limited (100 req/min)
- ✅ Has retry logic

**Assessment:** ⭐⭐⭐⭐⭐ **EXCELLENT** - Polygon provider is ready to use!

---

### 6. Pattern System ❌ **NO PATTERN FOR CORPORATE ACTIONS**

**Location:** `backend/patterns/`

**Existing Patterns:**
- `portfolio_overview.json` - Uses `ledger.positions` to get holdings
- `portfolio_scenario_analysis.json` - Uses `ledger.positions`
- `holding_deep_dive.json` - Uses `ledger.positions`

**Pattern Architecture:**
- Patterns are JSON-based declarative workflows
- Use capabilities like `ledger.positions`, `pricing.apply_pack`
- Executed by `PatternOrchestrator`
- Results stored in state

**Assessment:** 
- ❌ No `corporate_actions_upcoming` pattern
- ❌ No `corporate_actions.*` capabilities
- ✅ Could create pattern OR use direct service call

---

## 🔍 Root Cause Analysis

### Architectural Mismatch

**UI Expects:**
- Upcoming/future corporate actions for active holdings
- Real-time data from external sources (Polygon, FMP)
- Scheduled events (dividends, splits, mergers)
- Filtered by date range and type

**Backend Provides:**
- Historical corporate action recording only (via `transactions` table)
- No future event tracking
- No external API integration for upcoming events
- No holdings-to-corporate-actions mapping

**Result:**
- API returns hardcoded empty array
- UI shows "No corporate actions found"
- Feature appears broken but is actually unimplemented

---

## 📋 Implementation Plan

### Phase 1: Get Holdings (2-3 hours)

**Goal:** Get user's current holdings (symbols and quantities)

**Implementation:**
```python
# In get_corporate_actions endpoint
# Option A: Use existing ledger.positions capability
from app.core.pattern_orchestrator import PatternOrchestrator

pattern_result = await pattern_orchestrator.execute_pattern(
    pattern_id="portfolio_overview",
    inputs={"portfolio_id": portfolio_id},
    ctx=request_ctx
)

holdings = pattern_result.outputs.get("positions", {}).get("positions", [])

# Extract symbols
symbols = [h["symbol"] for h in holdings if h.get("qty_open", 0) > 0]
holdings_map = {h["symbol"]: h["qty_open"] for h in holdings}

# Option B: Direct database query
query = """
    SELECT DISTINCT symbol, SUM(qty_open) as total_qty
    FROM lots
    WHERE portfolio_id = $1 AND qty_open > 0
    GROUP BY symbol
"""
holdings = await conn.fetch(query, portfolio_id)
symbols = [h["symbol"] for h in holdings]
holdings_map = {h["symbol"]: h["total_qty"] for h in holdings}
```

**Files to Modify:**
- `combined_server.py` - Add holdings lookup to `get_corporate_actions` endpoint

---

### Phase 2: Add Service Method (4-6 hours)

**Goal:** Create `get_upcoming_actions()` method in `CorporateActionsService`

**Implementation:**
```python
# backend/app/services/corporate_actions.py

async def get_upcoming_actions(
    self,
    portfolio_id: UUID,
    symbols: List[str],
    days_ahead: int = 90,
    holdings_map: Optional[Dict[str, Decimal]] = None
) -> Dict[str, Any]:
    """
    Get upcoming corporate actions for portfolio holdings.
    
    Steps:
    1. For each symbol, fetch dividends from Polygon
    2. For each symbol, fetch splits from Polygon
    3. Filter to future dates (today + days_ahead)
    4. Calculate portfolio impact (shares × dividend amount)
    5. Format for UI consumption
    """
    from app.integrations.polygon_provider import PolygonProvider
    from app.core.config import settings
    
    if not symbols:
        return {
            "actions": [],
            "summary": {
                "total_actions": 0,
                "dividends_expected": 0.00,
                "splits_pending": 0,
                "earnings_releases": 0,
                "mergers_acquisitions": 0
            }
        }
    
    provider = PolygonProvider(api_key=settings.POLYGON_API_KEY)
    cutoff_date = date.today() + timedelta(days=days_ahead)
    
    all_actions = []
    total_dividends = Decimal("0")
    splits_count = 0
    
    for symbol in symbols:
        shares = holdings_map.get(symbol, Decimal("0")) if holdings_map else Decimal("0")
        
        # Fetch dividends
        try:
            dividends = await provider.get_dividends(symbol=symbol, limit=100)
            for div in dividends:
                ex_date = datetime.fromisoformat(div["ex_dividend_date"]).date()
                if ex_date > date.today() and ex_date <= cutoff_date:
                    amount = Decimal(str(div.get("cash_amount", 0)))
                    portfolio_impact = shares * amount
                    total_dividends += portfolio_impact
                    
                    all_actions.append({
                        "id": str(uuid4()),
                        "symbol": symbol,
                        "type": "dividend",
                        "ex_date": ex_date.isoformat(),
                        "payment_date": div.get("pay_date"),
                        "record_date": div.get("record_date"),
                        "amount": float(amount),
                        "currency": div.get("currency", "USD"),
                        "shares": float(shares),
                        "portfolio_impact": float(portfolio_impact),
                        "status": "scheduled",
                        "source": "polygon"
                    })
        except Exception as e:
            logger.warning(f"Failed to fetch dividends for {symbol}: {e}")
        
        # Fetch splits
        try:
            splits = await provider.get_splits(symbol=symbol, limit=100)
            for split in splits:
                exec_date = datetime.fromisoformat(split["execution_date"]).date()
                if exec_date > date.today() and exec_date <= cutoff_date:
                    splits_count += 1
                    
                    all_actions.append({
                        "id": str(uuid4()),
                        "symbol": symbol,
                        "type": "split",
                        "date": exec_date.isoformat(),
                        "ratio": float(split["split_ratio"]),
                        "split_from": split["split_from"],
                        "split_to": split["split_to"],
                        "shares": float(shares),
                        "status": "scheduled",
                        "source": "polygon"
                    })
        except Exception as e:
            logger.warning(f"Failed to fetch splits for {symbol}: {e}")
    
    # Sort by date
    all_actions.sort(key=lambda x: x.get("ex_date") or x.get("date") or x.get("payment_date"))
    
    return {
        "actions": all_actions,
        "summary": {
            "total_actions": len(all_actions),
            "dividends_expected": float(total_dividends),
            "splits_pending": splits_count,
            "earnings_releases": 0,  # TODO: Add FMP earnings integration
            "mergers_acquisitions": 0  # TODO: Add FMP M&A integration
        }
    }
```

**Files to Modify:**
- `backend/app/services/corporate_actions.py` - Add `get_upcoming_actions()` method

---

### Phase 3: Update Endpoint (2-3 hours)

**Goal:** Update `/api/corporate-actions` endpoint to use service method

**Implementation:**
```python
@app.get("/api/corporate-actions", response_model=SuccessResponse)
async def get_corporate_actions(
    portfolio_id: str = Query(..., description="Portfolio ID"),
    days_ahead: int = Query(30, ge=1, le=365),
    user: dict = Depends(require_auth)
):
    try:
        # Validate portfolio_id
        if not portfolio_id or len(portfolio_id) != 36:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid portfolio_id format"
            )
        
        portfolio_uuid = UUID(portfolio_id)
        
        # Get holdings
        if not db_pool:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )
        
        async with db_pool.acquire() as conn:
            # Set RLS context
            await conn.execute("SET app.current_user_id = $1", user.get("id"))
            
            # Get holdings (symbols and quantities)
            holdings_query = """
                SELECT DISTINCT symbol, SUM(qty_open) as total_qty
                FROM lots
                WHERE portfolio_id = $1 AND qty_open > 0
                GROUP BY symbol
            """
            holdings = await conn.fetch(holdings_query, portfolio_uuid)
            
            if not holdings:
                return SuccessResponse(data={
                    "portfolio_id": portfolio_id,
                    "time_horizon_days": days_ahead,
                    "actions": [],
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
                        "message": "No holdings found",
                        "source": "database"
                    }
                })
            
            symbols = [h["symbol"] for h in holdings]
            holdings_map = {h["symbol"]: h["total_qty"] for h in holdings}
            
            # Get upcoming corporate actions
            service = CorporateActionsService(conn)
            actions_data = await service.get_upcoming_actions(
                portfolio_id=portfolio_uuid,
                symbols=symbols,
                days_ahead=days_ahead,
                holdings_map=holdings_map
            )
            
            # Calculate notifications
            urgent = []
            informational = []
            
            cutoff_urgent = date.today() + timedelta(days=7)
            for action in actions_data["actions"]:
                action_date = action.get("ex_date") or action.get("date") or action.get("payment_date")
                if action_date:
                    action_date_obj = datetime.fromisoformat(action_date).date()
                    if action_date_obj <= cutoff_urgent:
                        urgent.append(action)
                    else:
                        informational.append(action)
            
            response = {
                "portfolio_id": portfolio_id,
                "time_horizon_days": days_ahead,
                "actions": actions_data["actions"],
                "summary": actions_data["summary"],
                "notifications": {
                    "urgent": urgent,
                    "informational": informational
                },
                "last_updated": datetime.utcnow().isoformat(),
                "metadata": {
                    "source": "polygon",
                    "holdings_count": len(symbols),
                    "message": "Corporate actions fetched successfully"
                }
            }
            
            return SuccessResponse(data=response)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting corporate actions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get corporate actions"
        )
```

**Files to Modify:**
- `combined_server.py` - Update `get_corporate_actions` endpoint

---

### Phase 4: Optional - Create Pattern (4-6 hours)

**Goal:** Create `corporate_actions_upcoming.json` pattern for consistency

**Pattern Definition:**
```json
{
  "id": "corporate_actions_upcoming",
  "name": "Upcoming Corporate Actions",
  "description": "Get upcoming corporate actions for portfolio holdings",
  "version": "1.0.0",
  "category": "corporate_actions",
  "tags": ["corporate-actions", "dividends", "splits", "holdings"],
  "inputs": {
    "portfolio_id": {
      "type": "uuid",
      "required": true,
      "description": "Portfolio UUID"
    },
    "days_ahead": {
      "type": "integer",
      "default": 90,
      "description": "Number of days to look ahead"
    }
  },
  "outputs": {
    "panels": [
      {
        "id": "actions_list",
        "title": "Upcoming Corporate Actions",
        "type": "table",
        "dataPath": "actions"
      },
      {
        "id": "actions_summary",
        "title": "Summary",
        "type": "metrics_grid",
        "dataPath": "summary"
      }
    ]
  },
  "steps": [
    {
      "capability": "ledger.positions",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}"
      },
      "as": "positions"
    },
    {
      "capability": "corporate_actions.upcoming",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "symbols": "{{positions.positions[*].symbol}}",
        "days_ahead": "{{inputs.days_ahead}}"
      },
      "as": "actions"
    }
  ]
}
```

**Note:** This requires creating `corporate_actions.upcoming` capability in an agent.

**Assessment:** 
- ✅ **Pattern approach** - Consistent with other features
- ⚠️ **Direct service call** - Simpler, faster to implement
- **Recommendation:** Start with direct service call, add pattern later if needed

---

## 🚨 Critical Gaps Identified

### Gap 1: Missing Holdings Lookup
**Severity:** CRITICAL  
**Impact:** Cannot get user's symbols  
**Fix:** Add holdings query to endpoint (Phase 1)

### Gap 2: Missing Service Method
**Severity:** CRITICAL  
**Impact:** Cannot fetch upcoming actions  
**Fix:** Add `get_upcoming_actions()` to `CorporateActionsService` (Phase 2)

### Gap 3: Endpoint Returns Empty Data
**Severity:** CRITICAL  
**Impact:** UI always shows "No corporate actions found"  
**Fix:** Update endpoint to call service method (Phase 3)

### Gap 4: No Polygon Integration
**Severity:** MEDIUM  
**Impact:** No data source  
**Fix:** Use existing `PolygonProvider.get_dividends()` and `get_splits()` (Phase 2)

### Gap 5: No Pattern Integration
**Severity:** LOW  
**Impact:** Inconsistent with other features  
**Fix:** Create pattern if needed (Phase 4, optional)

---

## 📊 Implementation Timeline

**Total Estimated Time:** 8-12 hours (MVP)

### Phase 1: Get Holdings (2-3 hours)
- Add holdings query to endpoint
- Extract symbols and quantities
- Handle edge cases (no holdings)

### Phase 2: Add Service Method (4-6 hours)
- Implement `get_upcoming_actions()` in `CorporateActionsService`
- Integrate Polygon provider
- Filter future events
- Calculate portfolio impact
- Format for UI

### Phase 3: Update Endpoint (2-3 hours)
- Wire up service method
- Add error handling
- Calculate notifications
- Return formatted response

### Phase 4: Optional Pattern (4-6 hours)
- Create `corporate_actions.upcoming` capability
- Create `corporate_actions_upcoming.json` pattern
- Update pattern registry

---

## ✅ Validation Checklist

### Phase 1 Validation
- [ ] Holdings query returns correct symbols
- [ ] Handles portfolios with no holdings
- [ ] Handles portfolios with multiple symbols
- [ ] Handles edge cases (empty portfolio, invalid portfolio_id)

### Phase 2 Validation
- [ ] Polygon provider calls work correctly
- [ ] Future events are filtered correctly
- [ ] Portfolio impact is calculated correctly
- [ ] Data format matches UI expectations
- [ ] Error handling for API failures

### Phase 3 Validation
- [ ] Endpoint returns correct data structure
- [ ] UI displays corporate actions correctly
- [ ] Filters work (by type, date range)
- [ ] Summary statistics are correct
- [ ] Notifications are calculated correctly
- [ ] Error messages are user-friendly

### Phase 4 Validation (if implemented)
- [ ] Pattern executes successfully
- [ ] Pattern registry entry is correct
- [ ] UI can use PatternRenderer if desired
- [ ] Data flow matches other patterns

---

## 🎯 Recommended Approach

### MVP Implementation (8-12 hours)
**Use Direct Service Call (No Pattern)**

**Why:**
- ✅ Faster to implement (no pattern/capability needed)
- ✅ Simpler architecture
- ✅ Easier to debug
- ✅ Can add pattern later if needed

**Steps:**
1. Add holdings query to endpoint (2-3 hours)
2. Add `get_upcoming_actions()` to service (4-6 hours)
3. Update endpoint to call service (2-3 hours)
4. Test end-to-end (1-2 hours)

### Full Implementation (12-18 hours)
**Add Pattern Integration**

**Why:**
- ✅ Consistent with other features
- ✅ Reusable pattern
- ✅ Can be used by other features

**Additional Steps:**
5. Create `corporate_actions.upcoming` capability (2-3 hours)
6. Create `corporate_actions_upcoming.json` pattern (2-3 hours)
7. Update UI to optionally use PatternRenderer (1-2 hours)

---

## 📚 Related Documentation

- `CORPORATE_ACTIONS_GUIDE.md` - Complete guide to corporate actions feature
- `backend/app/integrations/polygon_provider.py` - Polygon provider implementation
- `backend/app/services/corporate_actions.py` - Corporate actions service
- `backend/db/migrations/008_add_corporate_actions_support.sql` - Database schema

---

## ✅ Next Steps

1. **Review this audit** - Understand current state and gaps
2. **Choose implementation approach** - MVP (direct service) or Full (pattern)
3. **Allocate resources** - Assign implementation to appropriate agent
4. **Begin Phase 1** - Add holdings lookup
5. **Continue through phases** - Implement service method and update endpoint
6. **Test thoroughly** - Validate with real holdings
7. **Deploy and monitor** - Watch for errors and performance issues

---

**Audit Completed:** November 3, 2025  
**Status:** ✅ **READY FOR IMPLEMENTATION**  
**Estimated Effort:** 8-12 hours (MVP), 12-18 hours (Full)

