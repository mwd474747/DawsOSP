# Orphaned Backend Migrations (Oct 23 - Nov 8, 2025)

**Status**: ❌ Never applied to production - Archived Nov 8, 2025

---

## What Happened

These 18 migration files were created during backend modularization but **never applied to production**. They were discovered during Phase -1 architectural reconciliation (Nov 8, 2025).

**Timeline**:
- **Created**: Oct 23 - Nov 8, 2025
- **Location**: `backend/db/migrations/` (not root `migrations/`)
- **Deployment**: `.replit` never configured to run these migrations
- **Result**: Root `migrations/` folder applied to production, backend migrations ignored
- **Discovery**: Nov 8, 2025 during database audit (Phase -1.1)

---

## Why These Were Never Applied

**Production Deployment Configuration**:
```toml
# .replit file
[run]
args = "python combined_server.py"  # ← Root server, not backend/

# No migration runner configured for backend/db/migrations/
# Migration system only checks root migrations/ folder
```

**Database Reality**:
- Root `migrations/001-009` ✅ Applied to production
- Backend `migrations/005-022` ❌ Never applied (this folder)

---

## Contents (18 Files)

### Authentication & Security
- **005_create_rls_policies.sql** - Row-Level Security policies
- **009_jwt_auth.sql** - JWT authentication tables
- **010_add_users_and_audit_log.sql** - Users and audit_log tables (CRITICAL - see Issue 1)
- **010_fix_audit_log_schema.sql** - Audit log schema corrections

### Alerts & Notifications
- **011_alert_delivery_system.sql** - Alert delivery infrastructure
- **012_add_alert_channels.sql** - Alert channel support

### Data & Analytics
- **007_add_lot_qty_tracking.sql** - Tax lot quantity tracking
- **008_add_corporate_actions_support.sql** - Corporate actions
- **009_add_scenario_dar_tables.sql** - Scenario analysis tables
- **013_add_derived_indicators.sql** - Derived market indicators
- **015_add_economic_indicators.sql** - Economic indicator storage

### Data Quality & Consistency
- **014_add_quantity_deprecation_comment.sql** - Field deprecation warnings
- **016_standardize_asof_date_field.sql** - as_of_date standardization
- **017_add_realized_pl_field.sql** - realized_pl field addition
- **018_add_cost_basis_method_field.sql** - Cost basis tracking

### Ratings & Sentiment
- **020_add_security_ratings_table.sql** - Security ratings storage
- **021_add_news_sentiment_table.sql** - News sentiment analysis

### Infrastructure
- **019_add_migration_tracking_table.sql** - Migration tracking
- **022_update_rls_policies_comments.sql** - RLS policy documentation

---

## Critical Issue: The Audit Log Paradox

**Problem**: Migration 010 CREATES audit_log, but root migration 003 DELETES it

**Timeline**:
1. **Oct 23, 2025**: Backend migration 010 creates `audit_log` table (never applied)
2. **Nov 4, 2025**: Root migration 003 deletes `audit_log` table (applied)
3. **Result**: Code expects `audit_log`, but table doesn't exist

**Impact**:
- 14 files reference audit_log (auth.py, audit.py, reports.py)
- 50-100 errors/day in production logs
- Authentication logging broken
- Audit service completely non-functional
- Report export tracking fails

**Resolution**:
- Created `migrations/010_restore_audit_log.sql` to restore table
- See [PRODUCTION_ISSUES_ACTION_PLAN.md](../../PRODUCTION_ISSUES_ACTION_PLAN.md) Issue 1

---

## Useful Features to Extract

Not all migrations were bad - some contain useful features that should be restored:

### ✅ Already Restored (Nov 8, 2025)
- **audit_log table** - Restored via `migrations/010_restore_audit_log.sql`

### 🔄 Consider Restoring (Future)
- **RLS Policies** (005) - Row-Level Security for multi-tenant data
- **Corporate Actions** (008) - Dividends, splits, mergers
- **Scenario Tables** (009) - Scenario analysis (position_factor_betas, scenario_shocks)
- **Economic Indicators** (015) - Macro data storage
- **Security Ratings** (020) - Analyst ratings integration
- **News Sentiment** (021) - Sentiment analysis

### ❌ Not Needed (Already Exist or Deprecated)
- **Migration Tracking** (019) - Root migrations/ already has tracking
- **JWT Auth** (009) - If auth already implemented differently
- **Field Deprecations** (014, 016) - Check if already handled

---

## How to Use This Archive

### If You Need to Restore a Feature:

1. **Review the migration file** to understand what it does
2. **Check if already exists** in production:
   ```sql
   -- Example: Check if audit_log exists
   SELECT EXISTS (
       SELECT FROM information_schema.tables
       WHERE table_schema = 'public' AND table_name = 'audit_log'
   );
   ```
3. **If needed, create new root migration**:
   ```bash
   # Copy useful parts to new root migration
   cp migrations_ORPHANED_OCT23_NOV8/010_add_users_and_audit_log.sql \
      ../../migrations/010_restore_audit_log.sql

   # Edit to handle conflicts, then apply
   psql $DATABASE_URL -f ../../migrations/010_restore_audit_log.sql
   ```

### Do NOT:
- ❌ Try to apply these files directly (wrong schema state)
- ❌ Run them against production (will conflict with root migrations)
- ❌ Delete this folder (useful reference for features)

---

## Lessons Learned

**Anti-Patterns Identified**:

1. **Dual Migration Folders** - Should have ONE migration folder
2. **No Deployment Integration** - Migrations never run on deploy
3. **No Testing** - Migrations created but never validated in prod
4. **Poor Communication** - Backend team unaware of root team's cleanup
5. **Missing Documentation** - No record of which migrations applied

**Best Practices Going Forward**:

✅ **Single Migration Folder**: Only `migrations/` (root)
✅ **Deployment Hook**: Run migrations on every deploy
✅ **Migration Tracking**: Use `schema_migrations` table
✅ **Testing**: Test migrations in staging before production
✅ **Documentation**: Document every migration in CHANGELOG

---

## Related Documents

- [PRODUCTION_ISSUES_ACTION_PLAN.md](../../PRODUCTION_ISSUES_ACTION_PLAN.md) - Issue resolution plan
- [REFACTORING_HISTORY_FORENSICS.md](../../REFACTORING_HISTORY_FORENSICS.md) - How we got here
- [ARCHITECTURAL_DUAL_STRUCTURE_ANALYSIS.md](../../ARCHITECTURAL_DUAL_STRUCTURE_ANALYSIS.md) - Dual architecture discovery
- [UNIFIED_REFACTOR_PLAN_V2.md](../../UNIFIED_REFACTOR_PLAN_V2.md) - Phase -1 reconciliation

---

## Migration Numbering (Going Forward)

**Current State**:
```
migrations/ (ROOT - PRODUCTION)
├── 001-009 ✅ Applied to production
└── 010+ (NEW - starting with audit_log restore)

backend/db/migrations_ORPHANED_OCT23_NOV8/ (ARCHIVED)
└── 005-022 ❌ Never applied, archived for reference
```

**Rule**: All future migrations go in root `migrations/` folder ONLY

---

**Archived**: 2025-11-08
**Reason**: Never applied to production, discovered during Phase -1 database audit
**Action**: Useful features restored via new root migrations
**Status**: Safe to keep as reference, do not delete
