# Production Issues Action Plan (Based on Replit Audit)

**Date**: 2025-11-08
**Context**: Phase -1.1 Database Audit Complete - Critical Production Issues Identified
**Priority**: 🔴 CRITICAL - Production Breaking Issues

---

## Executive Summary

Replit's database audit revealed **3 critical production-breaking issues**:

1. 🔴 **CRITICAL**: `audit_log` table missing - breaks auth, audit service, reports (14 files affected)
2. 🔴 **CRITICAL**: `trade_date` field errors - breaks holdings view (frequent runtime errors)
3. ⚠️ **HIGH**: Migration conflict - impossible state in migration tracking

**Estimated Impact**: Auth logging fails on every login, holdings view errors hourly, report exports silently fail

**Recommendation**: Execute emergency fixes in order below (6-8 hours total)

---

## Issue 1: Missing `audit_log` Table (CRITICAL)

### What Replit Found

**Database State**:
```sql
-- audit_log DOES NOT EXIST in production
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'audit_log'
);
-- Result: FALSE ❌
```

**Code Dependencies** (14 references across 3 files):

1. **backend/app/services/auth.py** (2 references):
   ```python
   # Line 718 - Login audit logging
   await db.execute("""
       INSERT INTO audit_log (user_id, action, details, ip_address)
       VALUES ($1, $2, $3, $4)
   """, user_id, "login", login_details, request.client.host)

   # Line 726 - Logout audit logging
   await db.execute("""
       INSERT INTO audit_log (user_id, action, details)
       VALUES ($1, $2, $3)
   """, user_id, "logout", logout_details)
   ```
   **Impact**: Every login/logout attempt fails to log audit (silent failure)

2. **backend/app/services/audit.py** (12 references):
   ```python
   # Lines 65, 118, 191, 247, 338 - Core audit operations
   # ENTIRE SERVICE BROKEN - all methods fail
   async def log_action(user_id, action, details):
       await db.execute("INSERT INTO audit_log ...")  # ❌ FAILS

   async def get_user_audit_trail(user_id):
       return await db.fetch("SELECT * FROM audit_log ...")  # ❌ FAILS

   async def get_audit_report(start_date, end_date):
       return await db.fetch("SELECT * FROM audit_log ...")  # ❌ FAILS
   ```
   **Impact**: Entire audit service non-functional

3. **backend/app/services/reports.py** (multiple references):
   ```python
   # Lines 179, 310, 650, 700, 703 - Report export auditing
   await audit_service.log_action(
       user_id=user.id,
       action="report_export",
       details={"report_type": report_type}
   )  # ❌ FAILS
   ```
   **Impact**: Report exports work but fail to audit (compliance issue)

**Runtime Errors** (from Replit logs):
```
[2025-11-08 14:32:18] ERROR: relation "audit_log" does not exist
[2025-11-08 14:32:18] File: backend/app/services/auth.py, Line 718
[2025-11-08 15:45:22] ERROR: relation "audit_log" does not exist
[2025-11-08 15:45:22] File: backend/app/services/audit.py, Line 65
```

**Frequency**: ~50-100 errors per day (every login attempt + audit service calls)

### Root Cause: The Audit Log Paradox

**Timeline**:
1. **Oct 23, 2025**: Backend migration 010 **CREATES** `audit_log` table
2. **Nov 4, 2025**: Root migration 003 **DELETES** `audit_log` table (comment: "never implemented")
3. **Current**: Code expects table, table doesn't exist

**Why This Happened**:
- Backend team created audit_log in modular migrations (backend/db/migrations/010)
- Root team saw audit_log in schema, assumed it was unused, deleted it (migrations/003)
- Backend migrations **never applied to production** (orphaned)
- Root migrations **applied to production** (deleted the table)
- Code still references audit_log (from backend development)

### Decision Matrix: Restore vs Remove

#### Option A: Restore `audit_log` Table (RECOMMENDED)

**Pros**:
- ✅ Maintains audit trail functionality (critical for compliance)
- ✅ No code changes needed (just restore table)
- ✅ Fast fix (1 migration file)
- ✅ Preserves security features (login tracking)

**Cons**:
- ⚠️ Need to create migration from backend migration 010
- ⚠️ May conflict with future migration numbering

**Effort**: 1-2 hours
**Risk**: LOW

**Implementation**:
```sql
-- migrations/010_restore_audit_log.sql
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

COMMENT ON TABLE audit_log IS 'Restored Nov 8, 2025 - was deleted by migration 003';
```

#### Option B: Remove All Audit Code

**Pros**:
- ✅ No database changes
- ✅ Removes unused code (if we don't want auditing)

**Cons**:
- ❌ Loses audit trail functionality
- ❌ 14 code changes across 3 files
- ❌ Potential security/compliance issue
- ❌ More testing required
- ❌ Higher risk of breaking other features

**Effort**: 4-6 hours
**Risk**: MEDIUM-HIGH

**Implementation**: Would require:
1. Remove auth.py audit logging calls (2 locations)
2. Delete entire audit.py service (12 references)
3. Remove reports.py audit calls (multiple locations)
4. Remove audit endpoints from combined_server.py
5. Test all affected functionality

### Recommended Fix: Option A (Restore Table)

**Step 1**: Create migration file
```bash
# File: migrations/010_restore_audit_log.sql
# Copy from backend/db/migrations/010_create_audit_log.sql
```

**Step 2**: Apply migration
```bash
psql $DATABASE_URL -f migrations/010_restore_audit_log.sql
```

**Step 3**: Verify table exists
```sql
SELECT table_name FROM information_schema.tables
WHERE table_name = 'audit_log';
-- Expected: audit_log
```

**Step 4**: Test affected services
```bash
# Test login (should create audit entry)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

# Verify audit entry created
psql $DATABASE_URL -c "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 1;"
```

**Estimated Time**: 1-2 hours
**Priority**: 🔴 CRITICAL - Fix immediately

---

## Issue 2: Field Name Errors (`trade_date` vs `transaction_date`)

### What Replit Found

**Database Reality** (verified by Replit):
```sql
-- transactions table uses 'transaction_date' (NOT 'trade_date')
SELECT column_name FROM information_schema.columns
WHERE table_name = 'transactions' AND column_name LIKE '%date%';
-- Result: transaction_date ✅
```

**Runtime Errors** (from Replit logs):
```
[2025-11-08 10:15:32] ERROR: column "trade_date" does not exist
[2025-11-08 10:15:32] Query: SELECT symbol, trade_date, quantity FROM transactions
[2025-11-08 10:15:32] File: holding_deep_dive pattern

[2025-11-08 11:22:45] ERROR: column "trade_date" does not exist
[2025-11-08 11:22:45] File: portfolio_cash_flows query
```

**Frequency**: 20-30 errors per day (every holdings view access)

### Root Cause

**DATABASE.md Section 6** (from Replit, Nov 4):
```markdown
## Field Naming Corrections

The following field names are CORRECT in production:
- ✅ transaction_date (NOT trade_date)
- ✅ transaction_type (NOT action)
- ✅ realized_pl (NOT realized_pnl)
- ✅ flow_date (NOT trade_date in cash_flows)
```

**Why This Happened**:
- Original database schema used `transaction_date`
- Backend code mistakenly used `trade_date` in some queries
- Pattern system (holding_deep_dive) uses incorrect field name
- No validation caught the mismatch

### Files to Fix

**Search Results** (need to verify these):
```bash
# Files that may reference "trade_date"
grep -r "trade_date" backend/app --include="*.py" -n
grep -r "trade_date" frontend/ --include="*.js" -n
```

**Known Issues**:
1. **frontend/pattern-system.js** - holding_deep_dive pattern likely uses trade_date
2. **backend queries** - check transaction queries for trade_date references

### Recommended Fix

**Step 1**: Find all trade_date references
```bash
cd /Users/mdawson/Documents/GitHub/DawsOSP
grep -r "trade_date" --include="*.py" --include="*.js" -n > /tmp/trade_date_refs.txt
cat /tmp/trade_date_refs.txt
```

**Step 2**: Replace trade_date → transaction_date
```bash
# For each file found, replace:
# trade_date → transaction_date
```

**Step 3**: Verify no other field name mismatches
```bash
# Check for other documented mismatches:
grep -r "\.action" --include="*.py" -n  # Should be transaction_type
grep -r "realized_pnl" --include="*.py" -n  # Should be realized_pl
grep -r "debt_to_equity" --include="*.py" -n  # Should be debt_equity_ratio
```

**Estimated Time**: 2-3 hours
**Priority**: 🔴 CRITICAL - Breaks holdings view

---

## Issue 3: Migration Conflict (Impossible State)

### What Replit Found

**Migration Tracking Table** (schema_migrations):
```sql
SELECT version, applied_at FROM schema_migrations ORDER BY version;

-- Results show:
-- 001 | 2025-10-15 08:30:00
-- 002 | 2025-10-20 14:15:00
-- 003 | 2025-11-04 09:22:00  ← DELETES audit_log
-- ...
-- 009 | 2025-11-06 16:45:00
```

**Backend Migrations** (never applied):
```bash
backend/db/migrations/
├── 005_add_currency_attribution.sql (Oct 23)
├── 006_add_factor_analysis.sql (Oct 24)
├── ...
├── 010_create_audit_log.sql (Oct 25) ← CREATES audit_log
├── ...
└── 022_add_scenario_tables.sql (Nov 8)
```

**The Paradox**:
- Migration 003 (Nov 4) deletes audit_log
- Migration 010 (Oct 23) creates audit_log
- **But 010 came BEFORE 003 chronologically**
- **And 010 was never applied to production**

### Root Cause

**What Actually Happened**:
1. Oct 23-28: Backend team develops in `backend/db/migrations/` (migrations 005-022)
2. Backend migrations include 010_create_audit_log.sql
3. Nov 4: Root team sees audit_log in schema (maybe from dev database?)
4. Nov 4: Root team creates migration 003 to "clean up unused table"
5. Migration 003 applied to production ✅
6. Backend migrations 005-022 **never applied to production** ❌
7. Code still references audit_log (from backend development)

**Why Migration Tracking Shows 003 Applied**:
- Root migrations/ folder migrations applied correctly
- Backend backend/db/migrations/ folder **completely ignored by deployment**
- No migration runner configured for backend folder

### Recommended Fix

**Step 1**: Archive orphaned backend migrations
```bash
# Rename backend migrations folder
mv backend/db/migrations backend/db/migrations_ORPHANED_OCT23_NOV8

# Create explanation file
cat > backend/db/migrations_ORPHANED_OCT23_NOV8/README.md << 'EOF'
# Orphaned Backend Migrations (Oct 23 - Nov 8, 2025)

**Status**: Never applied to production

These 18 migration files were created during backend modularization
but never applied to production. They were discovered during Phase -1
architectural reconciliation (Nov 8, 2025).

**What Happened**:
- Created: Oct 23 - Nov 8, 2025
- Location: backend/db/migrations/ (not root migrations/)
- Deployment: .replit never configured to run these
- Result: Root migrations/ applied, backend migrations ignored

**Contents**:
- Migrations 005-022 (18 files)
- Include: audit_log, factor_analysis, currency_attribution, scenarios

**Action Taken**:
- Moved to migrations_ORPHANED_OCT23_NOV8 (Nov 8, 2025)
- Useful features restored via new root migrations (010+)
- See PRODUCTION_ISSUES_ACTION_PLAN.md

**Related Docs**:
- REFACTORING_HISTORY_FORENSICS.md (timeline)
- PRODUCTION_ISSUES_ACTION_PLAN.md (reconciliation)
EOF
```

**Step 2**: Extract useful migrations to root
```bash
# Review backend migrations for useful features
ls -lh backend/db/migrations_ORPHANED_OCT23_NOV8/

# Extract only what's needed:
# - 010_create_audit_log.sql → Already handled in Issue 1
# - Check if other migrations add useful features
```

**Step 3**: Document migration numbering
```markdown
## Migration Numbering Convention (Going Forward)

**Root migrations/** (PRODUCTION - ONLY location used):
- 001-009: Initial schema + cleanup (applied Oct-Nov 2025)
- 010+: New migrations (Nov 8, 2025+)

**backend/db/migrations_ORPHANED_OCT23_NOV8/** (ARCHIVED):
- 005-022: Never applied, archived for reference

**Rule**: All future migrations go in root migrations/ folder ONLY
```

**Estimated Time**: 1 hour
**Priority**: ⚠️ HIGH - Prevents future confusion

---

## Updated Phase -1 Timeline

### Original Phase -1 Estimate: 8-16 hours

### Revised Based on Replit Findings:

| Task | Original | Revised | Status |
|------|----------|---------|--------|
| -1.1: Audit Production Database | 1-2h | 1-2h | ✅ COMPLETE (Replit) |
| -1.2: Database Reconciliation | 4-6h | 6-8h | ⬅️ IN PROGRESS |
| -1.3: Archive Orphaned Backend | 2-4h | 30min | PENDING |
| -1.4: Frontend Bug Fixes | 2-4h | 0h | ✅ COMPLETE (already fixed) |
| -1.5: Update Documentation | 1-2h | 2-3h | PENDING |
| **TOTAL** | **8-16h** | **10-14h** | **40% complete** |

### Phase -1.2 Breakdown (Database Reconciliation)

**Now Includes**:

1. **Issue 1: Restore audit_log** (1-2h) 🔴 CRITICAL
   - Create migration 010_restore_audit_log.sql
   - Apply to production
   - Test auth/audit services

2. **Issue 2: Fix field name errors** (2-3h) 🔴 CRITICAL
   - Find all trade_date references
   - Replace with transaction_date
   - Test holdings view and patterns

3. **Issue 3: Archive orphaned migrations** (1h) ⚠️ HIGH
   - Move backend/db/migrations to _ORPHANED
   - Document migration numbering
   - Update migration docs

4. **Verify all other field names** (1-2h) ⚠️ MEDIUM
   - Check for action vs transaction_type
   - Check for realized_pnl vs realized_pl
   - Check for debt_to_equity vs debt_equity_ratio
   - Fix any found

5. **Testing** (1-2h) ⚠️ HIGH
   - Test login/logout (audit_log)
   - Test holdings view (transaction_date)
   - Test all patterns
   - Verify no new errors in logs

**Total Phase -1.2**: 6-10 hours (revised up from 4-6h due to complexity)

---

## Execution Order (Recommended)

### Emergency Fixes (Do First - 3-5 hours)

1. ✅ **Issue 1: Restore audit_log** (1-2h)
   - Blocking: Auth logging, audit service, reports
   - Impact: 50-100 errors/day
   - Risk: LOW (just restore table)

2. ✅ **Issue 2: Fix trade_date errors** (2-3h)
   - Blocking: Holdings view, patterns
   - Impact: 20-30 errors/day
   - Risk: LOW (find and replace)

### Cleanup (Do Second - 3-4 hours)

3. ✅ **Issue 3: Archive orphaned migrations** (1h)
   - Blocking: Future confusion
   - Impact: Documentation only
   - Risk: NONE (just moving files)

4. ✅ **Verify other field names** (1-2h)
   - Blocking: Potential hidden bugs
   - Impact: Unknown (no errors yet)
   - Risk: LOW (verification only)

5. ✅ **Testing** (1-2h)
   - Blocking: Deployment
   - Impact: Critical (validate fixes)
   - Risk: NONE (read-only testing)

### Documentation (Do Last - 2-3 hours)

6. ✅ **Phase -1.3: Archive orphaned backend** (30min)
   - Already documented in Issue 3

7. ✅ **Phase -1.5: Update documentation** (2-3h)
   - Update ARCHITECTURE.md
   - Update DATABASE.md
   - Update README.md

---

## Success Criteria

**Phase -1.2 Complete When**:
- ✅ audit_log table exists in production
- ✅ Auth/audit services work without errors
- ✅ Holdings view loads without trade_date errors
- ✅ All patterns execute successfully
- ✅ No "column does not exist" errors in logs
- ✅ Backend migrations archived with explanation
- ✅ All field names verified against DATABASE.md

**Verification Commands**:
```bash
# 1. Check audit_log exists
psql $DATABASE_URL -c "\dt audit_log"

# 2. Check no trade_date references in code
grep -r "trade_date" backend/ frontend/ --include="*.py" --include="*.js"

# 3. Check application logs for errors
tail -100 <production-logs> | grep -i "does not exist"

# 4. Test login creates audit entry
curl -X POST http://localhost:5000/api/auth/login ...
psql $DATABASE_URL -c "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 1;"

# 5. Test holdings view loads
curl http://localhost:5000/api/holdings
```

---

## Risk Assessment

| Issue | Current Impact | Fix Risk | Recommended Priority |
|-------|----------------|----------|---------------------|
| Missing audit_log | 🔴 CRITICAL (50-100 errors/day, auth broken) | LOW | 1 - DO FIRST |
| trade_date errors | 🔴 CRITICAL (20-30 errors/day, holdings broken) | LOW | 2 - DO SECOND |
| Migration conflict | ⚠️ MEDIUM (confusion, no active errors) | NONE | 3 - DO THIRD |
| Other field names | ⚠️ LOW (no errors yet, potential bugs) | LOW | 4 - DO FOURTH |

**Overall Risk**: If we don't fix Issues 1-2, production remains broken with 70-130 errors per day.

---

## Next Steps

**Immediate (Me - Claude Code)**:
1. Execute Issue 1 fix (restore audit_log)
2. Execute Issue 2 fix (trade_date → transaction_date)
3. Execute Issue 3 cleanup (archive orphaned migrations)
4. Run verification tests
5. Update documentation

**User Decision Required**:
- **None** - All decisions made based on Replit audit findings
- Recommended path is clear (restore audit_log, fix field names)

**Estimated Total Time**: 6-10 hours for Phase -1.2 completion

---

## Related Documents

- [REPLIT_PHASE_MINUS_1_PROMPTS.md](REPLIT_PHASE_MINUS_1_PROMPTS.md) - Original audit prompts
- [ARCHITECTURE_CORRECTIONS_NOV8_2025.md](ARCHITECTURE_CORRECTIONS_NOV8_2025.md) - Architecture updates
- [UNIFIED_REFACTOR_PLAN_V2.md](UNIFIED_REFACTOR_PLAN_V2.md) - Overall refactor plan
- [DATABASE.md](DATABASE.md) - Source of truth for field names
- [REFACTORING_HISTORY_FORENSICS.md](REFACTORING_HISTORY_FORENSICS.md) - How we got here

---

**Created**: 2025-11-08
**Status**: READY TO EXECUTE - All decisions made based on Replit audit
**Next Action**: Execute Issue 1 (restore audit_log table)
