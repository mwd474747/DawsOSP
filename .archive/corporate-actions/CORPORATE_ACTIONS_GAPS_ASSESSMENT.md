# Corporate Actions Gaps Assessment

**Date:** November 3, 2025  
**Purpose:** Assess corporate actions gaps in database documentation and application functionality  
**Status:** 📋 ASSESSMENT ONLY (No Code Changes)

---

## 📊 Executive Summary

The Corporate Actions feature has **critical gaps** that prevent it from functioning properly. While the UI is fully functional, the backend is entirely mock data with no database integration, no agent capabilities, and no real-world data sources.

**Key Finding:** This is a **complete gap** in the application's functionality - the feature appears to work (UI renders) but returns only hardcoded mock data.

---

## 🔍 Gap Analysis

### 1. Database Schema Gaps

#### Gap 1.1: No `corporate_actions` Table

**Assessment Claim:** Migration 008 exists for corporate actions support

**Reality Check:**
- ✅ **Migration 008 EXISTS:** `backend/db/migrations/008_add_corporate_actions_support.sql`
- ⚠️ **Purpose:** Migration 008 focuses on **past dividends** with FX rate tracking (for transactions table)
- ❌ **Missing:** No table for **upcoming/future corporate actions**
- ❌ **Missing:** No table for **dividend announcements**, **split announcements**, **earnings dates**

**Current Schema:**
- `transactions` table can record **past dividends** (transaction_type = 'DIVIDEND')
- `transactions.fx_rate_id` tracks FX rate for dividend currency conversion
- **NO table** for upcoming corporate actions

**Documentation Need:**
- Document that `transactions` table handles **past** corporate actions (dividends)
- Document that **NO table exists** for **upcoming** corporate actions
- Document gap: Need `corporate_actions` table for upcoming events

---

### 2. API Implementation Gaps

#### Gap 2.1: Mock Data Only

**Location:** `combined_server.py:4645-4724`

**Current Implementation:**
```python
@app.get("/api/corporate-actions")
async def get_corporate_actions(portfolio_id: Optional[str], days_ahead: int = 30):
    # Mock corporate actions data ← ⚠️ HARDCODED MOCK DATA
    actions = {
        "actions": [
            {"symbol": "AAPL", "type": "dividend", ...},  # Hardcoded
            {"symbol": "GOOGL", "type": "split", ...},    # Hardcoded
            {"symbol": "MSFT", "type": "earnings", ...},  # Hardcoded
            {"symbol": "T", "type": "merger", ...}        # Hardcoded
        ]
    }
    return SuccessResponse(data=actions)
```

**Problems:**
1. ❌ **No database query** - Doesn't check `corporate_actions` table (doesn't exist)
2. ❌ **Ignores portfolio_id** - Returns same mock data regardless of portfolio
3. ❌ **Ignores days_ahead** - Returns hardcoded dates, not filtered by time horizon
4. ❌ **Fake impact calculations** - "You own 100 shares" is not based on real holdings
5. ❌ **Static dates** - Hardcoded future dates that will become outdated

**Documentation Need:**
- Document that endpoint exists but returns only mock data
- Document that endpoint doesn't query database
- Document that endpoint doesn't use portfolio_id parameter

---

### 3. Agent Integration Gaps

#### Gap 3.1: No Agent Capabilities

**Reality Check:**
- ❌ **No agent capabilities** for corporate actions
- ❌ **No `corporate_actions.*` capabilities** in any agent
- ❌ **Cannot be used in patterns** - No way to fetch corporate actions via pattern system

**Expected Capabilities (Missing):**
- `corporate_actions.fetch_upcoming` - Fetch upcoming events for portfolio
- `corporate_actions.fetch_historical` - Historical corporate actions
- `corporate_actions.compute_portfolio_impact` - Calculate impact on holdings
- `corporate_actions.filter_by_holdings` - Filter by portfolio positions

**Documentation Need:**
- Document that corporate actions cannot be accessed via patterns
- Document that no agent provides corporate actions capabilities
- Document gap: Need agent integration for pattern-based access

---

### 4. Data Source Integration Gaps

#### Gap 4.1: No Data Fetcher Service

**Reality Check:**
- ❌ **No CorporateActionsFetcher service** exists
- ❌ **No integration** with Yahoo Finance, Alpha Vantage, or other APIs
- ❌ **No scheduled jobs** to refresh corporate actions data
- ❌ **No way to populate** real corporate actions data

**Documentation Need:**
- Document that corporate actions data cannot be fetched from external sources
- Document that no scheduled jobs exist for corporate actions
- Document gap: Need data fetcher service and scheduled jobs

---

### 5. Database Migration Gaps

#### Gap 5.1: Migration 008 Scope

**Migration 008 Contents:**
- ✅ Adds `fx_rate_id` to `transactions` table (for past dividends with FX rates)
- ✅ Adds `dividend_amount`, `dividend_currency` columns
- ❌ **Does NOT create `corporate_actions` table**
- ❌ **Does NOT support upcoming events**

**Documentation Need:**
- Document that migration 008 only handles **past dividends** (via transactions table)
- Document that migration 008 does **NOT** create table for upcoming events
- Document gap: Need new migration for `corporate_actions` table

---

## 📋 Impact Assessment

### Functional Impact

**Current State:** ❌ **NOT FUNCTIONAL**
- Feature appears to work (UI renders)
- Returns only mock data
- Cannot track real corporate actions for active holdings

**User Impact:**
- Users see corporate actions page but data is fake
- Portfolio-specific filtering doesn't work
- Impact calculations are incorrect
- Dates will become outdated

### Documentation Impact

**Current DATABASE.md Status:**
- ⚠️ Does NOT mention `corporate_actions` table (because it doesn't exist)
- ⚠️ Does NOT mention migration 008 limitations
- ⚠️ Does NOT document that corporate actions endpoint returns mock data
- ⚠️ Does NOT document gaps in agent integration

**Documentation Need:**
- Document `transactions` table handles past dividends
- Document gap: No table for upcoming corporate actions
- Document that API endpoint returns mock data
- Document missing agent capabilities
- Document missing data source integration

---

## ✅ Recommendations for Documentation

### Priority 1: Document Current State (IMMEDIATE)

1. **Document transactions table for past dividends:**
   - Migration 008 adds `fx_rate_id`, `dividend_amount`, `dividend_currency` to `transactions`
   - This supports recording **past** dividends with accurate FX rates
   - Does NOT support upcoming/future corporate actions

2. **Document gap: No corporate_actions table:**
   - No table exists for upcoming corporate actions
   - No table exists for dividend announcements, split announcements, earnings dates
   - This is a functional gap preventing real corporate actions tracking

3. **Document mock API endpoint:**
   - `/api/corporate-actions` endpoint exists but returns only hardcoded mock data
   - Does not query database
   - Does not use `portfolio_id` or `days_ahead` parameters

### Priority 2: Document Missing Components (SOON)

4. **Document missing agent capabilities:**
   - No agent provides corporate actions capabilities
   - Cannot access corporate actions via patterns
   - Need `CorporateActionsAgent` or extension to existing agents

5. **Document missing data source integration:**
   - No service to fetch corporate actions from external APIs
   - No scheduled jobs to refresh corporate actions data
   - Need `CorporateActionsFetcher` service and scheduled jobs

### Priority 3: Document Implementation Plan (REFERENCE)

6. **Document proposed solution:**
   - Create `corporate_actions` table migration (migration 014)
   - Implement `CorporateActionsService`
   - Build `CorporateActionsFetcher` (Yahoo Finance integration)
   - Rewrite API endpoint to query database
   - Add scheduled daily job
   - Add agent capabilities

---

## 🔍 Comparison with Other Gaps

### Similar to Other Missing Features

**Pattern:**
- UI exists and works ✅
- Backend endpoint exists but returns mock/incomplete data ❌
- Database schema partially exists ⚠️
- No agent capabilities ❌
- No data source integration ❌

**Other Features with Same Pattern:**
- Corporate Actions (this assessment)
- Potentially other features need review

**Documentation Approach:**
- Document current state (what exists, what doesn't)
- Document functional gaps (what doesn't work)
- Document missing components (what needs to be built)

---

## 📊 Summary

### Tables Status

| Table | Exists | Used | Status |
|-------|--------|------|--------|
| `transactions` (past dividends) | ✅ | ✅ | Handles past dividends only |
| `corporate_actions` (upcoming) | ❌ | ❌ | **DOES NOT EXIST** |

### API Status

| Component | Status | Notes |
|-----------|--------|-------|
| Endpoint exists | ✅ | `/api/corporate-actions` |
| Returns real data | ❌ | **MOCK DATA ONLY** |
| Uses portfolio_id | ❌ | Parameter ignored |
| Uses days_ahead | ❌ | Parameter ignored |

### Agent Status

| Component | Status | Notes |
|-----------|--------|-------|
| Agent capabilities | ❌ | **NONE EXIST** |
| Pattern integration | ❌ | Cannot use in patterns |
| Service layer | ❌ | **NO SERVICE EXISTS** |

### Data Source Status

| Component | Status | Notes |
|-----------|--------|-------|
| External API integration | ❌ | **NONE** |
| Scheduled jobs | ❌ | **NONE** |
| Data fetcher service | ❌ | **DOES NOT EXIST** |

---

## ✅ Final Recommendations

### For DATABASE.md Documentation:

1. ✅ **Document transactions table capabilities:**
   - Handles past dividends (with FX rate tracking via migration 008)
   - Does NOT handle upcoming corporate actions

2. ✅ **Document missing corporate_actions table:**
   - No table exists for upcoming events
   - This is a functional gap

3. ✅ **Document API endpoint limitations:**
   - Endpoint exists but returns mock data only
   - Does not query database

4. ✅ **Document missing components:**
   - No agent capabilities
   - No data source integration
   - No scheduled jobs

### Don't Document:

1. ❌ **Don't document corporate_actions table** as if it exists (it doesn't)
2. ❌ **Don't document agent capabilities** as if they exist (they don't)
3. ❌ **Don't document data fetcher** as if it exists (it doesn't)

### Action Items:

1. ✅ Add section to DATABASE.md: "Corporate Actions Gaps"
2. ✅ Document current state (transactions table, mock API)
3. ✅ Document missing components (corporate_actions table, agent capabilities, data integration)
4. ✅ Add to "Known Issues" section

---

**Status:** Assessment complete. Ready to update DATABASE.md with corporate actions gaps documentation.

