# Remaining Steps for Replit - Quick Reference

**Date:** January 15, 2025  
**Purpose:** Quick reference for Replit to complete remaining work  
**Status:** 🚧 READY FOR VALIDATION

---

## Immediate Actions Required

### 1. Sync with Remote
```bash
# Pull latest changes
git pull origin main  # or master

# Review changes
git status
git diff
```

### 2. Review Changes Made
See `REPLIT_VALIDATION_GUIDE.md` for complete details.

**Key Changes:**
- ✅ Phase 0: Module validation fixed
- ✅ Phase 1: SQL injection fix (P0 Critical)
- ✅ Phase 2: Singleton removal (~85% complete)
- ✅ Phase 3: Duplicate code extraction (~70% complete)
- ✅ Phase 4: Legacy artifacts removed
- ✅ Phase 5: Frontend cleanup (100% complete)
- 🚧 Phase 6: Fix TODOs (~15% complete)

---

## Critical Testing Required

### Test 1: Module Loading
- [ ] Open application in browser
- [ ] Check console for module validation messages
- [ ] Verify all modules load successfully
- [ ] Check for race condition errors

### Test 2: SQL Injection Protection
- [ ] Try creating alert with invalid metric name → Should reject
- [ ] Try creating alert with invalid UUID → Should reject
- [ ] Try creating alert with invalid symbol → Should reject
- [ ] Verify SQL injection attempts are blocked

### Test 3: Pattern Execution
- [ ] Execute a pattern via API
- [ ] Verify services initialize correctly
- [ ] Check logs for service initialization
- [ ] Verify no singleton function errors

### Test 4: Frontend Logging
- [ ] Open application in development mode
- [ ] Check console for Logger messages
- [ ] Verify debug/info logs appear
- [ ] Test in production mode (minimal logging)

---

## Database Migrations Required (P1 Critical)

### Migration 1: security_ratings table
**File:** `backend/db/migrations/012_security_ratings.sql` (CREATE)

```sql
CREATE TABLE IF NOT EXISTS security_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID NOT NULL REFERENCES securities(id),
    symbol VARCHAR(10) NOT NULL,
    asof_date DATE NOT NULL,
    dividend_safety DECIMAL(3,1),
    quality_score DECIMAL(3,1),
    moat_score DECIMAL(3,1),
    value_score DECIMAL(3,1),
    growth_score DECIMAL(3,1),
    momentum_score DECIMAL(3,1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(security_id, asof_date)
);

CREATE INDEX idx_security_ratings_symbol_date ON security_ratings(symbol, asof_date DESC);
CREATE INDEX idx_security_ratings_security_id ON security_ratings(security_id);
```

### Migration 2: news_sentiment table
**File:** `backend/db/migrations/013_news_sentiment.sql` (CREATE)

```sql
CREATE TABLE IF NOT EXISTS news_sentiment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(10) NOT NULL,
    article_date DATE NOT NULL,
    sentiment_score DECIMAL(5,4), -- Range: -1.0 to 1.0
    article_title TEXT,
    article_url TEXT,
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, article_date, article_url)
);

CREATE INDEX idx_news_sentiment_symbol_date ON news_sentiment(symbol, article_date DESC);
CREATE INDEX idx_news_sentiment_sentiment ON news_sentiment(sentiment_score);
```

### Migration 3: Update RLS Policies
**File:** `backend/db/migrations/011_alert_delivery_system.sql` (UPDATE)

**Action:** Add comments about future user isolation:

```sql
-- TODO: Update to USING (user_id = current_user_id()) when alert ownership is defined
-- For now, keep USING (true) but add comment
```

---

## API Updates Required (If Report Endpoints Exist)

### Update Report Export Endpoints
If report export endpoints exist, update them to pass IP and user agent:

```python
# In API endpoint (FastAPI)
ip_address = request.client.host if request.client else None
user_agent = request.headers.get("user-agent", "Unknown")

await report_service._audit_log_export(
    ...,
    ip_address=ip_address,
    user_agent=user_agent
)
```

**Files to Check:**
- `backend/app/api/routes/reports.py` (if exists)
- Any endpoints calling `ReportService.render_pdf()` or `render_csv()`

---

## Remaining P1 TODOs (11 items)

### Database Schema (3 TODOs)
1. ⏳ Create security_ratings table migration
2. ⏳ Create news_sentiment table migration  
3. ⏳ Update RLS policies (add comments)

### Placeholder Values (8 TODOs)
4-11. ⏳ Review placeholder values in docstrings (may be acceptable as examples)
   - `backend/app/services/notifications.py:24,38` - Example docstrings
   - `backend/app/services/dlq.py:34` - Example docstring
   - `backend/app/core/alert_validators.py:228,283` - Example docstrings
   - `backend/app/services/alerts.py:550,632,968,1071` - Example docstrings

**Note:** These are in example docstrings, not actual code. May be acceptable as-is.

---

## Validation Checklist

### ✅ Phase 0: Browser Infrastructure
- [ ] Modules load correctly
- [ ] No race condition errors
- [ ] Module validation works

### ✅ Phase 1: Exception Handling
- [ ] SQL injection protection works
- [ ] Invalid inputs are rejected
- [ ] Error messages are clear

### ✅ Phase 2: Singleton Removal
- [ ] Services initialize correctly
- [ ] Pattern execution works
- [ ] No singleton function errors

### ✅ Phase 3: Duplicate Code Extraction
- [ ] Agents work correctly
- [ ] Error messages consistent
- [ ] Policy merging works

### ✅ Phase 4: Legacy Removal
- [ ] No import errors
- [ ] Tests pass
- [ ] Application works

### ✅ Phase 5: Frontend Cleanup
- [ ] Logger loads correctly
- [ ] Logging works in dev/prod
- [ ] No console.log errors

### ⏳ Phase 6: Fix TODOs
- [ ] Database migrations created
- [ ] RLS policies updated
- [ ] Report export works with IP/user agent

---

## Files Changed Summary

**Backend Files Changed:** ~20 files
**Frontend Files Changed:** 14 files  
**Files Removed:** 1 folder (5 files)
**New Files Created:** 3 files

**Total Lines Changed:** ~500+ lines
**Total Lines Removed:** ~2,115 lines (archived agents)

---

## Quick Test Commands

```bash
# Run backend tests
pytest backend/tests/

# Check for linting errors
pylint backend/app/ --disable=all --enable=E,F

# Check frontend files
# (Manual browser testing recommended)
```

---

## Key Files to Review

1. **`backend/app/services/alert_validation.py`** (NEW) - SQL injection protection
2. **`frontend/logger.js`** (NEW) - Frontend logging utility
3. **`backend/app/api/executor.py`** - DI container integration
4. **`backend/app/core/di_container.py`** - Helper function added
5. **`backend/app/agents/base_agent.py`** - Duplicate code extracted

---

## Known Issues & Notes

1. **ReportService is Deprecated** - IP/user agent fix applied, but consider migrating to DataHarvester agent
2. **Placeholder Values** - Some "xxx" values in docstrings are examples, not code
3. **Singleton Functions** - Still exist but deprecated (can remove later)
4. **Initialization Order** - May need adjustment (monitor logs)

---

## Next Steps After Validation

1. **If tests pass:** Continue with remaining Phase 6 TODOs
2. **If issues found:** Document and fix before proceeding
3. **If migrations needed:** Create and run database migrations
4. **If API updates needed:** Update endpoints to pass IP/user agent

---

## Documentation References

- **Complete Guide:** `docs/refactoring/REPLIT_VALIDATION_GUIDE.md`
- **TODO Inventory:** `docs/refactoring/PHASE_6_TODO_INVENTORY.md`
- **Progress Tracking:** `docs/refactoring/PHASE_6_PROGRESS.md`
- **Overall Summary:** `docs/refactoring/REFACTOR_SESSION_FINAL_SUMMARY.md`

---

**Status:** 🚧 READY FOR VALIDATION  
**Last Updated:** January 15, 2025

