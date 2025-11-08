# Critical Database Schema Migrations

**Date:** January 14, 2025
**Status:** READY FOR EXECUTION
**Estimated Time:** 5-10 minutes
**Risk Level:** LOW (all migrations include rollback-safe checks)

## Overview

Three critical migrations address database schema standardization and financial compliance gaps identified in the comprehensive architecture review.

## Migrations

### Migration 016: Standardize asof_date Field Naming
**File:** `016_standardize_asof_date_field.sql`
**Purpose:** Rename `valuation_date` → `asof_date` for consistency
**Impact:** holdings, portfolio_values, dar_results tables
**Breaking Changes:** None (column rename is transparent to queries using column name)

### Migration 017: Add Realized P&L Tracking
**File:** `017_add_realized_pl_field.sql`
**Purpose:** Add `realized_pl` field to transactions table
**Impact:** Enables IRS Form 1099-B compliance and tax reporting
**Breaking Changes:** None (adds new column with DEFAULT NULL)

### Migration 018: Add Cost Basis Method Tracking
**File:** `018_add_cost_basis_method_field.sql`
**Purpose:** Add `cost_basis_method` field to portfolios table
**Impact:** Tracks lot selection method, prevents illegal LIFO for stocks
**Breaking Changes:** None (defaults to FIFO for existing portfolios)

## Pre-Migration Checklist

- [ ] Backup database: `pg_dump dawsos > backup_$(date +%Y%m%d_%H%M%S).sql`
- [ ] Verify DATABASE_URL is set: `echo $DATABASE_URL`
- [ ] Check current schema version: `SELECT MAX(migration_number) FROM schema_migrations;`
- [ ] Stop application services (to prevent mid-migration queries)

## Execution Instructions

### Option 1: Run All Migrations (Recommended)

```bash
# From project root
cd backend/db/migrations

# Run migrations in order
for file in 016_*.sql 017_*.sql 018_*.sql; do
    echo "Running $file..."
    psql "$DATABASE_URL" -f "$file"
    if [ $? -ne 0 ]; then
        echo "ERROR: Migration $file failed"
        exit 1
    fi
    echo "SUCCESS: $file completed"
    echo "---"
done
```

### Option 2: Run Individually

```bash
# Migration 016: asof_date standardization
psql "$DATABASE_URL" -f 016_standardize_asof_date_field.sql

# Migration 017: realized_pl field
psql "$DATABASE_URL" -f 017_add_realized_pl_field.sql

# Migration 018: cost_basis_method field
psql "$DATABASE_URL" -f 018_add_cost_basis_method_field.sql
```

### Option 3: Using Python Migration Runner

```python
# From backend/db/run_migrations.py (if it exists)
python run_migrations.py --from 016 --to 018
```

## Post-Migration Verification

### 1. Verify Schema Changes

```sql
-- Check asof_date columns exist
SELECT table_name, column_name
FROM information_schema.columns
WHERE column_name = 'asof_date' AND table_schema = 'public';

-- Check realized_pl column exists
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'transactions' AND column_name = 'realized_pl';

-- Check cost_basis_method column exists
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'portfolios' AND column_name = 'cost_basis_method';

-- Check audit table was created
SELECT table_name FROM information_schema.tables
WHERE table_name = 'cost_basis_method_audit';
```

### 2. Verify Triggers and Functions

```sql
-- Check cost basis validation trigger
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE event_object_table = 'portfolios';

-- Check audit log function
SELECT proname, prosrc
FROM pg_proc
WHERE proname = 'log_cost_basis_method_change';
```

### 3. Test Cost Basis Method Validation

```sql
-- This should succeed (FIFO is allowed for stocks)
UPDATE portfolios
SET cost_basis_method = 'FIFO'
WHERE id = (SELECT id FROM portfolios LIMIT 1);

-- This should FAIL if portfolio has stock positions (LIFO not allowed)
-- UPDATE portfolios
-- SET cost_basis_method = 'LIFO'
-- WHERE id = (SELECT id FROM portfolios LIMIT 1);
-- Expected: ERROR: LIFO cost basis method is not allowed for portfolios with stock positions
```

### 4. Verify Data Integrity

```sql
-- Check all portfolios have valid cost_basis_method
SELECT portfolio_name, cost_basis_method, cost_basis_method_changed_at
FROM portfolios;

-- Check SELL transactions missing realized_pl (needs backfill)
SELECT
    COUNT(*) as total_sell_transactions,
    COUNT(realized_pl) as with_realized_pl,
    COUNT(*) - COUNT(realized_pl) as missing_realized_pl
FROM transactions
WHERE transaction_type = 'SELL';
```

## Rollback Instructions (If Needed)

### Rollback Migration 018 (Cost Basis Method)

```sql
-- Drop triggers
DROP TRIGGER IF EXISTS trigger_validate_cost_basis_method ON portfolios;
DROP TRIGGER IF EXISTS trigger_log_cost_basis_method_change ON portfolios;

-- Drop functions
DROP FUNCTION IF EXISTS validate_cost_basis_method_for_asset_type();
DROP FUNCTION IF EXISTS log_cost_basis_method_change();

-- Drop audit table
DROP TABLE IF EXISTS cost_basis_method_audit;

-- Remove columns
ALTER TABLE portfolios DROP COLUMN IF EXISTS cost_basis_method_changed_at;
ALTER TABLE portfolios DROP COLUMN IF EXISTS cost_basis_method;
```

### Rollback Migration 017 (Realized P&L)

```sql
-- Drop indexes
DROP INDEX IF EXISTS idx_transactions_tax_year;
DROP INDEX IF EXISTS idx_transactions_realized_pl;

-- Remove column
ALTER TABLE transactions DROP COLUMN IF EXISTS realized_pl;
```

### Rollback Migration 016 (asof_date)

```sql
-- Rename back to valuation_date
ALTER TABLE holdings RENAME COLUMN asof_date TO valuation_date;
ALTER TABLE portfolio_values RENAME COLUMN asof_date TO valuation_date;
ALTER TABLE dar_results RENAME COLUMN asof_date TO valuation_date;
```

## Next Steps After Migration

1. **Update DATABASE.md** to reflect actual schema (Migration 016-018 applied)
2. **Backfill realized_pl** for existing SELL transactions (use backfill query from 017)
3. **Update Python code** to use new fields:
   - Use `asof_date` instead of `valuation_date`
   - Set `realized_pl` when executing SELL transactions
   - Allow users to select `cost_basis_method` in portfolio settings
4. **Update API routes** to expose cost_basis_method in portfolio endpoints
5. **Update UI** to display cost basis method selection

## Code Changes Required

### After Migration 016: Update queries using valuation_date

```python
# Before:
df = await conn.fetch("SELECT portfolio_id, valuation_date, market_value FROM holdings")

# After:
df = await conn.fetch("SELECT portfolio_id, asof_date, market_value FROM holdings")
```

### After Migration 017: Calculate realized_pl on SELL

```python
# In trade_execution.py, after executing SELL transaction:
realized_pl = sell_proceeds - total_cost_basis

await conn.execute("""
    UPDATE transactions
    SET realized_pl = $1
    WHERE id = $2
""", realized_pl, transaction_id)
```

### After Migration 018: Use portfolio cost_basis_method

```python
# Get portfolio's cost basis method
portfolio = await conn.fetchrow("""
    SELECT cost_basis_method FROM portfolios WHERE id = $1
""", portfolio_id)

method = portfolio["cost_basis_method"]  # "FIFO", "LIFO", "HIFO", etc.

# Use method for lot selection
lots = await lots_repo.get_open_lots(portfolio_id, symbol, method=method)
```

## Support

If migrations fail:
1. Check PostgreSQL logs: `tail -f /var/log/postgresql/postgresql-*.log`
2. Verify DATABASE_URL points to correct database
3. Ensure user has ALTER TABLE privileges
4. Review error message and check specific migration file

## Migration Status Tracking

```sql
-- If you have a schema_migrations table, record these migrations:
INSERT INTO schema_migrations (migration_number, description, applied_at)
VALUES
    (16, 'Standardize asof_date field naming', NOW()),
    (17, 'Add realized P&L tracking', NOW()),
    (18, 'Add cost basis method tracking', NOW());
```
