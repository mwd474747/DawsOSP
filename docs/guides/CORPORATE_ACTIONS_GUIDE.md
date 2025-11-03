# Corporate Actions Feature - Complete Guide

**Date:** November 3, 2025  
**Status:** 🔍 **ANALYZED - NOT IMPLEMENTED**  
**Purpose:** Comprehensive guide to corporate actions feature analysis, current state, and implementation requirements

---

## 📊 Executive Summary

The corporate actions feature has a fully functional UI component but lacks backend implementation. The system currently returns an empty array with metadata indicating it's not yet implemented. This guide consolidates all analysis, findings, and implementation requirements.

---

## 🎯 Current State

### UI Component ✅ **PRODUCTION READY**

**Location:** `full_ui.html` (lines 10868-11108)

**Features:**
- Fully functional React component
- Fetches data from `/api/corporate-actions`
- Displays upcoming corporate actions (dividends, splits, mergers)
- Shows "No corporate actions scheduled" when empty
- Handles errors gracefully

### Backend Endpoint ⚠️ **RETURNS EMPTY DATA**

**Location:** `combined_server.py` (lines 4645-4733)

**Current Implementation:**
```python
@app.get("/api/corporate-actions")
async def get_corporate_actions(
    portfolio_id: str = Query(..., description="Portfolio UUID"),
    current_user: dict = Depends(require_auth)
):
    # Returns empty array with metadata
    return {
        "data": [],
        "_metadata": {
            "source": "demo",
            "note": "Corporate actions feature not yet implemented"
        }
    }
```

**Improvements Made:**
- ✅ Made `portfolio_id` required parameter
- ✅ Added UUID validation
- ✅ Returns proper error responses (422 for missing portfolio_id, 400 for invalid UUID)
- ✅ Added authentication requirement

### Database ❌ **NO TABLE FOR UPCOMING EVENTS**

**Current State:**
- No `corporate_actions` table for upcoming events
- `transactions` table records past corporate actions (dividends, splits)
- No scheduled data refresh mechanism

---

## 🔍 Root Cause Analysis

### Architectural Mismatch

**UI Expects:**
- Upcoming/future corporate actions for active holdings
- Real-time data from external sources (Polygon, FMP)
- Scheduled events (dividends, splits, mergers)

**Backend Provides:**
- Historical corporate action recording only (via `transactions` table)
- No future event tracking
- No external API integration

**Result:**
- API returns hardcoded empty array
- UI shows "No corporate actions scheduled"
- Feature appears broken but is actually unimplemented

---

## 📋 Implementation Requirements

### 1. Database Schema (4-6 hours)

**Create `corporate_actions` table:**
```sql
CREATE TABLE corporate_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID REFERENCES securities(id),
    symbol TEXT NOT NULL,
    action_type TEXT NOT NULL,  -- 'dividend', 'split', 'merger', 'spinoff'
    ex_date DATE NOT NULL,
    record_date DATE,
    payable_date DATE,
    amount NUMERIC(20,8),  -- For dividends
    ratio NUMERIC(20,8),   -- For splits (e.g., 2:1 = 2.0)
    description TEXT,
    source TEXT,  -- 'polygon', 'fmp', 'manual'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_corporate_actions_symbol ON corporate_actions(symbol);
CREATE INDEX idx_corporate_actions_ex_date ON corporate_actions(ex_date);
CREATE INDEX idx_corporate_actions_security_id ON corporate_actions(security_id);
```

### 2. Service Method (4-6 hours)

**Create `get_upcoming_actions()` method:**

**Location:** `backend/app/services/corporate_actions.py` (new file)

**Requirements:**
- Query `corporate_actions` table for upcoming events
- Filter by portfolio holdings (via `securities` table)
- Return events within next 90 days
- Format data for UI consumption

### 3. External API Integration (8-12 hours)

**Data Sources:**
- **Polygon.io** - Real-time corporate actions data
- **FMP (Financial Modeling Prep)** - Alternative data source
- **Manual Entry** - For custom/verified actions

**Requirements:**
- Scheduled job to fetch upcoming events (daily)
- Store in `corporate_actions` table
- Handle API rate limits
- Error handling and retry logic

### 4. Scheduled Data Refresh (2-3 hours)

**Requirements:**
- Daily job to fetch new corporate actions
- Update existing records
- Remove past events (older than 90 days)
- Log fetch status and errors

### 5. Endpoint Logic Update (2-3 hours)

**Update `/api/corporate-actions` endpoint:**

**Requirements:**
- Query `corporate_actions` table
- Filter by portfolio holdings
- Return formatted data for UI
- Handle edge cases (no holdings, no upcoming events)

---

## 🚨 Critical Issues Identified

### Issue 1: Missing Database Table
**Severity:** CRITICAL  
**Impact:** Cannot store upcoming corporate actions  
**Fix:** Create `corporate_actions` table (see schema above)

### Issue 2: No Service Method
**Severity:** CRITICAL  
**Impact:** Cannot retrieve upcoming actions  
**Fix:** Implement `get_upcoming_actions()` method

### Issue 3: No External API Integration
**Severity:** HIGH  
**Impact:** No data source for upcoming events  
**Fix:** Integrate Polygon.io or FMP API

### Issue 4: No Scheduled Refresh
**Severity:** HIGH  
**Impact:** Data becomes stale  
**Fix:** Implement daily scheduled job

### Issue 5: Endpoint Returns Empty Data
**Severity:** MEDIUM  
**Impact:** UI shows "No corporate actions scheduled"  
**Fix:** Update endpoint to query database and return real data

---

## 📊 Implementation Timeline

**Total Estimated Time:** 20-30 hours (16-23 hours for MVP)

### MVP Implementation (16-23 hours)
1. Database schema (4-6 hours)
2. Service method (4-6 hours)
3. Basic external API integration (6-8 hours)
4. Endpoint logic update (2-3 hours)

### Full Implementation (24-30 hours)
1. All MVP items (16-23 hours)
2. Scheduled data refresh (2-3 hours)
3. Error handling and retry logic (2-2 hours)
4. Testing and validation (2-2 hours)

---

## 🎯 Implementation Priority

### Phase 1: Database & Service (8-12 hours)
- Create `corporate_actions` table
- Implement `get_upcoming_actions()` method
- Basic endpoint logic

### Phase 2: External API (8-12 hours)
- Integrate Polygon.io or FMP API
- Implement data fetching logic
- Store in database

### Phase 3: Scheduled Refresh (2-3 hours)
- Daily job to refresh data
- Error handling and logging

### Phase 4: Testing & Validation (2-3 hours)
- End-to-end testing
- UI integration verification
- Error scenario testing

---

## 📚 Related Documents

This guide consolidates information from:
- `CORPORATE_ACTIONS_DIAGNOSTIC_REPORT.md` - Original diagnostic analysis
- `CORPORATE_ACTIONS_DATAFLOW_REVIEW.md` - Data flow analysis
- `CORPORATE_ACTIONS_ENDPOINT_DESIGN_ANALYSIS.md` - Endpoint design review
- `CORPORATE_ACTIONS_GAPS_ASSESSMENT.md` - Gap analysis
- `CORPORATE_ACTIONS_ROOT_ISSUE_ANALYSIS.md` - Root cause analysis
- `FMP_CORPORATE_ACTIONS_CONTEXT.md` - FMP API context

**Note:** Original analysis documents have been archived to `.archive/corporate-actions/`

---

## ✅ Next Steps

1. **Review this guide** - Understand current state and requirements
2. **Prioritize implementation** - Decide on MVP vs full implementation
3. **Allocate resources** - Assign implementation to appropriate agent
4. **Create implementation plan** - Break down into specific tasks
5. **Begin implementation** - Start with Phase 1 (Database & Service)

---

**Analysis Completed:** November 3, 2025  
**Status:** ✅ **READY FOR IMPLEMENTATION**  
**Estimated Effort:** 20-30 hours total (16-23 hours for MVP)

