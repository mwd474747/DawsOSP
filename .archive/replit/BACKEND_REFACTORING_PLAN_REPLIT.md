# Backend Refactoring Plan for Replit Agent

**Date:** November 4, 2025  
**Purpose:** Comprehensive backend refactoring plan for Replit agent  
**Status:** 📋 **PLANNING COMPLETE** - Ready for Execution  
**Target Agent:** Replit (Backend)

---

## 🎯 Executive Summary

This plan provides a detailed, step-by-step guide for the Replit agent to execute backend refactoring work, focusing on database field standardization, security fixes, and system improvements. The plan includes goals, risks, common mistakes, validation criteria, and rollback procedures.

**Total Duration:** 5 weeks (25 working days)  
**Work Type:** Backend (Database, Services, Agents, API)  
**Risk Level:** HIGH (affects all layers)  
**Dependencies:** None (Week 0 is the starting point)

---

## 📊 Goals & Objectives

### Primary Goals

1. **Standardize Database Field Names** (Week 0, Days 1-2)
   - Rename `qty_open` → `quantity_open`
   - Rename `qty_original` → `quantity_original`
   - Standardize date fields to `asof_date`
   - **Target:** 100% consistency across all layers

2. **Fix Database Integrity Issues** (Week 0, Days 3-4)
   - Add missing FK constraints (`lots.security_id`)
   - Fix duplicate table definitions
   - Configure connection pooling
   - **Target:** 100% referential integrity

3. **Fix Security Vulnerabilities** (Week 0, Day 5)
   - Replace `eval()` with safe evaluator
   - Add authorization checking
   - **Target:** Zero security vulnerabilities

4. **Prepare Pattern System** (Week 1, Days 3-5)
   - Update pattern JSON files with standardized field names
   - Add panel definitions to backend JSON
   - Create Pydantic schemas
   - **Target:** Backend ready for frontend pattern registry elimination

5. **Complete System Fixes** (Week 3)
   - Add input validation
   - Add transaction management
   - Add rate limiting
   - Standardize error handling
   - **Target:** Production-ready reliability

6. **Optimize Performance** (Week 4, Days 3-4)
   - Fix N+1 queries
   - Implement caching
   - Add performance monitoring
   - **Target:** <50ms response times

---

## ⚠️ Risks & Mitigation

### High-Risk Items

#### 1. Database Migration Breaking Production ⚠️ CRITICAL

**Risk:** Migration 014 could fail or corrupt data, breaking production.

**Mitigation:**
- ✅ Create full database backup before migration
- ✅ Test migration on staging database first
- ✅ Use transaction blocks (BEGIN/COMMIT) for atomicity
- ✅ Keep old columns during transition period (don't drop immediately)
- ✅ Create rollback scripts and test them
- ✅ Monitor database during migration
- ✅ Have rollback procedure ready

**Rollback Triggers:**
- Migration fails
- Data integrity check fails
- Application errors after migration
- Performance degradation >20%

---

#### 2. Code Updates Missing Locations ⚠️ HIGH

**Risk:** Missing some locations when updating field names, causing inconsistent behavior.

**Mitigation:**
- ✅ Use `grep` to find all occurrences before updating
- ✅ Create checklist of all files to update
- ✅ Update files systematically (database → agents → services → patterns)
- ✅ Run comprehensive tests after updates
- ✅ Use code search tools to verify all locations updated

**Validation:**
- Run `grep -r "qty_open" backend/` after updates (should return 0 results)
- Run `grep -r "quantity_open" backend/` (should return expected results)
- Run all tests to verify no regressions

---

#### 3. Security Fix Breaking Pattern Execution ⚠️ MEDIUM

**Risk:** Replacing `eval()` with safe evaluator could break pattern condition evaluation.

**Mitigation:**
- ✅ Test safe evaluator with all existing pattern conditions
- ✅ Create comprehensive test suite for condition evaluation
- ✅ Use feature flag to gradually roll out new evaluator
- ✅ Keep old `eval()` code as fallback during transition
- ✅ Monitor pattern execution success rate after change

**Validation:**
- All 13 patterns execute successfully
- Condition evaluation works correctly
- No security vulnerabilities remain

---

#### 4. Pattern JSON Updates Breaking UI ⚠️ MEDIUM

**Risk:** Updating pattern JSON field names could break UI if frontend not updated.

**Mitigation:**
- ✅ Coordinate with frontend agent (Claude IDE)
- ✅ Update frontend `patternRegistry` simultaneously
- ✅ Test end-to-end after updates
- ✅ Use feature flag to gradually roll out changes
- ✅ Keep backwards compatibility during transition

**Validation:**
- All UI pages render correctly
- Charts display data correctly
- Tables display data correctly
- No blank panels

---

## 🚨 Common Mistakes to Avoid

### 1. Updating Code Before Database Migration ❌

**Mistake:** Updating backend code to use `quantity_open` before running migration.

**Why It's Wrong:** Code will fail because `quantity_open` column doesn't exist yet.

**Correct Approach:**
1. Run database migration first (adds `quantity_open` column)
2. Update code to use `quantity_open`
3. Test thoroughly
4. Drop old columns (after verification period)

---

### 2. Dropping Old Columns Too Early ❌

**Mistake:** Dropping `qty_open` column immediately after migration.

**Why It's Wrong:** If something breaks, you can't rollback easily.

**Correct Approach:**
1. Run migration (adds new columns, keeps old columns)
2. Update all code to use new columns
3. Test thoroughly (1-2 days)
4. Verify no regressions
5. Drop old columns (after verification period)

---

### 3. Missing Some Files in Field Name Updates ❌

**Mistake:** Updating only some files, leaving others using old field names.

**Why It's Wrong:** Inconsistent behavior, hard to debug.

**Correct Approach:**
1. Use `grep -r "qty_open" backend/` to find ALL occurrences
2. Create checklist of all files
3. Update files systematically
4. Verify with `grep` after updates (should return 0 results)

---

### 4. Not Testing Rollback Procedures ❌

**Mistake:** Creating rollback scripts but not testing them.

**Why It's Wrong:** If migration fails, rollback might also fail.

**Correct Approach:**
1. Create rollback scripts
2. Test rollback on staging database
3. Verify rollback works correctly
4. Document rollback procedure

---

### 5. Updating Patterns Without Frontend Coordination ❌

**Mistake:** Updating pattern JSON field names without updating frontend.

**Why It's Wrong:** UI will break because `patternRegistry` expects old field names.

**Correct Approach:**
1. Coordinate with frontend agent (Claude IDE)
2. Update backend and frontend simultaneously
3. Test end-to-end after updates
4. Use feature flag for gradual rollout

---

### 6. Using Unsafe eval() in Production ❌

**Mistake:** Leaving `eval()` in production code, even with restricted namespace.

**Why It's Wrong:** Security vulnerability, code injection risk.

**Correct Approach:**
1. Replace `eval()` with `simpleeval` or AST-based evaluator
2. Test all pattern conditions work correctly
3. Remove `eval()` code completely
4. Verify no security vulnerabilities remain

---

### 7. Not Adding FK Constraints ❌

**Mistake:** Skipping FK constraint addition, thinking it's not critical.

**Why It's Wrong:** Data integrity issues, orphaned records, hard to debug.

**Correct Approach:**
1. Clean orphaned records first
2. Add FK constraints
3. Verify constraints work correctly
4. Test that invalid inserts are rejected

---

### 8. Not Testing After Each Step ❌

**Mistake:** Making all changes at once, then testing at the end.

**Why It's Wrong:** If something breaks, hard to identify which change caused it.

**Correct Approach:**
1. Make one change at a time
2. Test after each change
3. Verify no regressions
4. Move to next change

---

## 📋 Week 0: Foundation (5 Days)

### Day 1-2: Database Field Standardization

**Goal:** Standardize quantity field names across database

**Tasks:**

#### Task 1.1: Create Migration 014 (4 hours)

**Steps:**
1. Create `backend/db/migrations/014_standardize_quantity_fields.sql`
2. Add new standardized columns (`quantity_open`, `quantity_original`)
3. Copy data from old columns (`qty_open`, `qty_original`)
4. Set NOT NULL constraints
5. Update indexes
6. Update constraints
7. Create rollback script
8. Test migration on staging database

**Validation:**
```sql
-- Verify columns exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'lots'
  AND column_name IN ('quantity_open', 'quantity_original', 'qty_open', 'qty_original')
ORDER BY column_name;

-- Verify data migration
SELECT
    COUNT(*) AS total_lots,
    COUNT(*) FILTER (WHERE quantity_open = qty_open) AS matching_open,
    COUNT(*) FILTER (WHERE quantity_original = qty_original) AS matching_original
FROM lots
WHERE qty_open IS NOT NULL;
```

**Expected Result:**
- All lots have `quantity_open` = `qty_open`
- All lots have `quantity_original` = `qty_original`
- No NULL values in `quantity_open` or `quantity_original`

**Common Mistakes:**
- ❌ Not testing migration on staging first
- ❌ Not creating rollback script
- ❌ Not verifying data migration

---

#### Task 1.2: Update Backend Code (8 hours)

**Steps:**
1. Find all occurrences: `grep -r "qty_open" backend/`
2. Create checklist of all files to update
3. Update SQL queries to use `quantity_open` instead of `qty_open`
4. Update SQL queries to use `quantity_original` instead of `qty_original`
5. Remove field name transformations (e.g., `qty_open AS qty`)
6. Update all 51 files systematically
7. Test after each file update

**Files to Update:**
- `backend/app/agents/financial_analyst.py` (line 168)
- `backend/app/services/trade_execution.py` (31 references)
- `backend/app/services/corporate_actions.py` (8 references)
- All other agent and service files

**Validation:**
```bash
# Should return 0 results
grep -r "qty_open" backend/

# Should return expected results
grep -r "quantity_open" backend/
```

**Expected Result:**
- No occurrences of `qty_open` or `qty_original` in backend code
- All code uses `quantity_open` and `quantity_original`
- All tests pass

**Common Mistakes:**
- ❌ Missing some files in updates
- ❌ Not removing field name transformations
- ❌ Not testing after updates

---

#### Task 1.3: Update Pattern JSON Files (2 hours)

**Steps:**
1. Find all pattern JSON files: `find backend/patterns -name "*.json"`
2. Update all pattern JSON files to use standardized field names
3. Update pattern templates to use standardized names
4. Test pattern execution

**Validation:**
- All 13 patterns execute successfully
- Pattern outputs use standardized field names
- No regressions in pattern execution

---

#### Task 1.4: Validation (2 hours)

**Steps:**
1. Run validation scripts
2. Test all patterns execute
3. Test all API endpoints
4. Verify no regressions

**Validation Checklist:**
- [ ] Database migration successful
- [ ] All code updated to use standardized names
- [ ] All patterns execute successfully
- [ ] All API endpoints work correctly
- [ ] No regressions in functionality

---

### Day 3-4: Database Integrity + Connection Pooling

**Goal:** Fix database integrity issues and configure connection pooling

**Tasks:**

#### Task 2.1: Create Migration 015 (2 hours)

**Steps:**
1. Create `backend/db/migrations/015_add_fk_constraints.sql`
2. Clean orphaned records (before adding FK)
3. Add FK constraint for `lots.security_id`
4. Add FK constraint for `transactions.security_id`
5. Create rollback script
6. Test migration on staging

**Validation:**
```sql
-- Verify FK constraints exist
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('lots', 'transactions')
  AND kcu.column_name = 'security_id';
```

**Expected Result:**
- FK constraints exist for `lots.security_id` and `transactions.security_id`
- No orphaned records
- Invalid inserts are rejected

---

#### Task 2.2: Fix Duplicate Table Definitions (2 hours)

**Steps:**
1. Identify duplicate tables (migration 009 vs schema/)
2. Remove duplicate table definitions from migration 009
3. Keep only schema/ versions
4. Test that tables still exist

**Validation:**
- No duplicate table definitions
- All tables exist in correct location
- No regressions

---

#### Task 2.3: Configure Connection Pooling (4 hours)

**Steps:**
1. Review current connection pool configuration
2. Configure pool size (min_size, max_size)
3. Add connection timeout
4. Add connection health checks
5. Monitor pool usage

**Configuration:**
```python
# backend/app/core/database.py
pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=5,      # Minimum connections
    max_size=20,     # Maximum connections
    timeout=30,      # Connection timeout
    command_timeout=60  # Query timeout
)
```

**Validation:**
- Connection pool configured correctly
- Pool size appropriate for workload
- Connection health checks working

---

#### Task 2.4: Add Database Indexes (4 hours)

**Steps:**
1. Identify missing indexes (foreign keys, composite queries)
2. Add indexes on foreign keys
3. Add composite indexes for common queries
4. Analyze query performance
5. Optimize slow queries

**Validation:**
- All foreign keys have indexes
- Composite indexes added for common queries
- Query performance improved

---

### Day 5: Security Fixes

**Goal:** Fix security vulnerabilities

**Tasks:**

#### Task 3.1: Replace eval() with Safe Evaluator (4 hours)

**Steps:**
1. Install `simpleeval` package: `pip install simpleeval`
2. Replace `eval()` in `pattern_orchestrator.py:845`
3. Test all pattern conditions work correctly
4. Remove old `eval()` code
5. Test comprehensive pattern execution

**Code Change:**
```python
# Before (UNSAFE)
result = eval(safe_condition, {"__builtins__": {}}, state)

# After (SAFE)
from simpleeval import SimpleEval
evaluator = SimpleEval()
evaluator.names = state
result = evaluator.eval(safe_condition)
```

**Validation:**
- All 13 patterns execute successfully
- All pattern conditions evaluate correctly
- No security vulnerabilities remain

**Common Mistakes:**
- ❌ Not testing all pattern conditions
- ❌ Breaking pattern execution with new evaluator
- ❌ Not removing old `eval()` code

---

#### Task 3.2: Add Authorization Checking (2 hours)

**Steps:**
1. Add rights checking in `PatternOrchestrator`
2. Add rights validation to executor API
3. Test authorization enforcement

**Validation:**
- Authorization checking works correctly
- Users without rights cannot execute patterns
- No regressions in pattern execution

---

#### Task 3.3: Validation (2 hours)

**Steps:**
1. Test security fixes
2. Verify no regressions
3. Security testing

**Validation Checklist:**
- [ ] `eval()` replaced with safe evaluator
- [ ] Authorization checking works
- [ ] No security vulnerabilities remain
- [ ] All patterns execute successfully

---

## 📋 Week 1: Pattern System Preparation (3 Days)

### Days 3-5: Backend Pattern System Preparation

**Goal:** Prepare backend for pattern system refactoring

**Tasks:**

#### Task 4.1: Update Pattern JSON Files (8 hours)

**Steps:**
1. Update all 13 pattern JSON files to use standardized field names
2. Add `display.panels[]` to pattern JSON files
3. Include `dataPath` mappings in JSON
4. Test pattern execution

**Example Pattern JSON Update:**
```json
{
  "id": "portfolio_overview",
  "display": {
    "panels": [
      {
        "id": "holdings_table",
        "title": "Holdings",
        "type": "data_table",
        "dataPath": "valued_positions.positions",
        "columns": [
          { "field": "quantity", "header": "Qty" },
          { "field": "market_value", "header": "Value" }
        ]
      }
    ]
  }
}
```

**Validation:**
- All pattern JSON files updated
- Panel definitions added to backend JSON
- Pattern execution works correctly

---

#### Task 4.2: Create Pydantic Schemas (4 hours)

**Steps:**
1. Create Pydantic schemas for pattern inputs
2. Validate pattern inputs against schemas
3. Return clear validation errors
4. Test validation

**Example Pydantic Schema:**
```python
from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import date

class PortfolioOverviewInput(BaseModel):
    portfolio_id: UUID4
    lookback_days: Optional[int] = 252
    asof_date: Optional[date] = None
```

**Validation:**
- Pydantic schemas created for all patterns
- Input validation works correctly
- Clear validation errors returned

---

#### Task 4.3: Add Panel Definitions to Backend (4 hours)

**Steps:**
1. Move panel definitions from frontend `patternRegistry` to backend JSON
2. Include panel structure in pattern response
3. Test pattern responses include panel metadata

**Validation:**
- Panel definitions in backend JSON
- Pattern responses include panel metadata
- Frontend can read panel definitions from backend

---

## 📋 Week 3: Complete System Fixes (5 Days)

### Days 1-2: Reliability Fixes

**Goal:** Add timeout, cancellation, and template substitution fixes

**Tasks:**

#### Task 5.1: Add Pattern Execution Timeout (4 hours)

**Steps:**
1. Wrap `run_pattern()` with `asyncio.wait_for()`
2. Add configurable timeout per pattern type
3. Add timeout configuration in pattern JSON
4. Test timeout mechanism

**Code Change:**
```python
# backend/app/core/pattern_orchestrator.py
async def run_pattern(self, pattern_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    timeout = self._get_pattern_timeout(pattern_id)
    try:
        result = await asyncio.wait_for(
            self._run_pattern_internal(pattern_id, inputs),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        raise PatternTimeoutError(f"Pattern {pattern_id} exceeded timeout of {timeout}s")
```

**Validation:**
- Timeout mechanism works correctly
- Patterns timeout appropriately
- No regressions in pattern execution

---

#### Task 5.2: Add Cancellation Support (4 hours)

**Steps:**
1. Implement cancellation token mechanism
2. Add cancellation endpoint
3. Clean up resources on cancellation
4. Test cancellation

**Validation:**
- Cancellation works correctly
- Resources cleaned up on cancellation
- No resource leaks

---

#### Task 5.3: Fix Template Substitution (4 hours)

**Steps:**
1. Add optional variable syntax: `{{?variable.name}}`
2. Add default value syntax: `{{variable.name|default:value}}`
3. Update `_resolve_value()` to handle optional variables
4. Test template substitution

**Validation:**
- Optional variables work correctly
- Default values work correctly
- No regressions in template substitution

---

### Days 3-4: Data Integrity Fixes

**Goal:** Add input validation, transaction management, and rate limiting

**Tasks:**

#### Task 6.1: Make Validation Blocking (2 hours)

**Steps:**
1. Change validation from non-blocking to blocking for critical errors
2. Distinguish between warnings and errors
3. Return clear validation errors
4. Test validation

**Validation:**
- Validation blocking works correctly
- Clear validation errors returned
- No regressions

---

#### Task 6.2: Add Transaction Management (4 hours)

**Steps:**
1. Wrap pattern execution in database transaction
2. Use asyncpg transaction context manager
3. Rollback on any step failure
4. Test transaction management

**Code Change:**
```python
# backend/app/core/pattern_orchestrator.py
async def run_pattern(self, pattern_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    async with self.db_pool.acquire() as conn:
        async with conn.transaction():
            # Pattern execution steps
            # If any step fails, transaction rolls back
            ...
```

**Validation:**
- Transaction management works correctly
- Rollback works on failure
- No partial state on failure

---

#### Task 6.3: Add Input Validation (4 hours)

**Steps:**
1. Add Pydantic request models for all API endpoints
2. Validate inputs before processing
3. Return clear validation errors (400 Bad Request)
4. Test input validation

**Validation:**
- Input validation works correctly
- Clear validation errors returned
- No regressions

---

#### Task 6.4: Add Rate Limiting (2 hours)

**Steps:**
1. Implement rate limiter per external API (FMP, Polygon, FRED)
2. Add retry logic with exponential backoff
3. Add circuit breaker for failing APIs
4. Test rate limiting

**Validation:**
- Rate limiting works correctly
- Retry logic works correctly
- Circuit breaker works correctly

---

### Day 5: Error Handling Standardization

**Goal:** Standardize error handling across backend

**Tasks:**

#### Task 7.1: Standardize Error Handling (4 hours)

**Steps:**
1. Standardize error handling pattern (raise exceptions)
2. Create custom exception classes
3. Add structured error responses
4. Consistent error logging

**Validation:**
- Error handling standardized
- Structured error responses
- Consistent error logging

---

#### Task 7.2: Standardize Logging (2 hours)

**Steps:**
1. Standardize logging patterns
2. Use structured logging (JSON)
3. Add context to log messages
4. Remove sensitive data from logs

**Validation:**
- Logging standardized
- Structured logging works
- No sensitive data in logs

---

#### Task 7.3: Resource Management (2 hours)

**Steps:**
1. Use async context managers for all resources
2. Wrap database operations in context managers
3. Ensure proper cleanup on errors
4. Test resource management

**Validation:**
- Resource management works correctly
- Proper cleanup on errors
- No resource leaks

---

## 📋 Week 4: Performance Optimization (2 Days)

### Days 3-4: Backend Performance Optimization

**Goal:** Optimize performance and add monitoring

**Tasks:**

#### Task 8.1: Fix N+1 Query Problem (4 hours)

**Steps:**
1. Implement batch loading for securities
2. Use eager loading for relationships
3. Reduce database round trips
4. Test query optimization

**Validation:**
- N+1 queries fixed
- Query performance improved
- No regressions

---

#### Task 8.2: Add Pattern Execution Caching (4 hours)

**Steps:**
1. Add Redis caching for pattern results
2. Cache key based on pattern + inputs hash
3. Configure TTL per pattern type
4. Test caching

**Validation:**
- Caching works correctly
- Cache hits improve performance
- No regressions

---

#### Task 8.3: Add Performance Monitoring (2 hours)

**Steps:**
1. Add performance metrics (Prometheus)
2. Add slow query logging
3. Track API response times
4. Test monitoring

**Validation:**
- Performance monitoring works
- Metrics collected correctly
- Slow query logging works

---

#### Task 8.4: Optimize Synchronous Operations (2 hours)

**Steps:**
1. Move blocking operations to background tasks
2. Use thread pool for CPU-intensive tasks
3. Use async I/O for all I/O operations
4. Test async optimization

**Validation:**
- Synchronous operations optimized
- Async I/O works correctly
- Performance improved

---

## ✅ Success Criteria

### Week 0 Success Criteria
- [ ] All database migrations successful
- [ ] All backend code updated to use standardized field names
- [ ] All patterns execute successfully
- [ ] Security vulnerabilities resolved
- [ ] Database connection pool configured
- [ ] Database indexes added

### Week 1 Success Criteria
- [ ] Pattern JSON files updated with standardized field names
- [ ] Panel definitions in backend JSON
- [ ] Pydantic schemas created
- [ ] Pattern execution works correctly

### Week 3 Success Criteria
- [ ] Timeout mechanism working
- [ ] Cancellation support working
- [ ] Template substitution fixed
- [ ] Validation blocking errors
- [ ] Transaction management working
- [ ] Input validation at API boundaries
- [ ] Rate limiting on external APIs
- [ ] Error handling standardized
- [ ] Logging standardized

### Week 4 Success Criteria
- [ ] N+1 queries fixed
- [ ] Pattern execution caching added
- [ ] Performance monitoring added
- [ ] Synchronous operations optimized

---

## 📋 Daily Standup Format

**Format:**
```
✅ Completed: [What was done]
🔄 In Progress: [What's being worked on]
⏳ Blocked: [What's blocked and why]
📋 Next: [What's next]
```

**Example:**
```
✅ Completed: Migration 014 created, backend code updated (51 files)
🔄 In Progress: Testing pattern execution with standardized names
⏳ Blocked: None
📋 Next: Create Migration 015 (FK constraints)
```

---

## 🔄 Rollback Procedures

### Migration 014 Rollback

**Trigger:** Migration fails, data integrity check fails, or application errors after migration.

**Steps:**
1. Run rollback script: `psql -d dawsos_prod < backend/db/migrations/014_rollback.sql`
2. Verify old columns restored: `SELECT column_name FROM information_schema.columns WHERE table_name = 'lots' AND column_name IN ('qty_open', 'qty_original');`
3. Revert code changes (git revert)
4. Restart application
5. Verify application works correctly

**Rollback Time:** <15 minutes

---

### Code Update Rollback

**Trigger:** Application errors after code updates.

**Steps:**
1. Revert code changes: `git revert <commit-hash>`
2. Restart application
3. Verify application works correctly

**Rollback Time:** <5 minutes

---

## 📊 Progress Tracking

### Week 0 Progress

**Day 1-2: Database Field Standardization**
- [ ] Migration 014 created
- [ ] Migration 014 tested on staging
- [ ] Migration 014 run on production
- [ ] Backend code updated (51 files)
- [ ] Pattern JSON files updated
- [ ] Validation complete

**Day 3-4: Database Integrity + Connection Pooling**
- [ ] Migration 015 created
- [ ] Migration 015 tested on staging
- [ ] Migration 015 run on production
- [ ] Connection pooling configured
- [ ] Database indexes added
- [ ] Validation complete

**Day 5: Security Fixes**
- [ ] `eval()` replaced with safe evaluator
- [ ] Authorization checking added
- [ ] Security testing complete
- [ ] Validation complete

---

## 🎯 Next Steps

1. **Review This Plan** - Review with team/stakeholders
2. **Start Week 0** - Begin database field standardization
3. **Daily Standups** - Update progress daily
4. **Weekly Reviews** - Review progress at end of each week
5. **Adjust as Needed** - Adjust plan based on actual progress

---

**Status:** ✅ **PLANNING COMPLETE** - Ready for Execution  
**Next Step:** Start Week 0 (Day 1: Create Migration 014)

