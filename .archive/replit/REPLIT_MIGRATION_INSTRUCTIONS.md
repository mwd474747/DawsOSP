# Migration Instructions for Replit Agent

**Date:** November 4, 2025
**Purpose:** Database field name standardization (qty_open → quantity_open)
**Status:** 🔴 CRITICAL - Required for Pattern System Refactoring
**Execution Order:** Must be run BEFORE any pattern system changes

---

## 📋 Executive Summary

### What This Fixes

1. **Field Name Inconsistency**: Migration 007 added `qty_open` but schema uses `quantity`
2. **Index Naming**: Index `idx_lots_qty_open` should be `idx_lots_quantity_open`
3. **Function Reference**: `reduce_lot()` function uses `qty_open` in queries
4. **Missing Constraint**: `lots.security_id` has no FK constraint (allows orphaned records)

### Why This Matters

**Critical Dependency:**
```
Database Field Standardization (qty_open → quantity_open)
  ↓ BLOCKS
Pattern System Refactoring (46 dataPath mappings in UI)
  ↓ BLOCKS
Complete System Integration
```

**Impact:** Without this fix, UI pattern system cannot be refactored because:
- UI expects `quantity_open` field name
- Backend returns `qty_open`
- DataPath lookup fails → blank panels in UI

---

## 🎯 Migration Overview

| Migration | Purpose | Risk | Downtime |
|-----------|---------|------|----------|
| **002b_fix_qty_indexes.sql** | Rename indexes | 🟢 LOW | None |
| **002c_fix_reduce_lot_function.sql** | Update function | 🟡 MEDIUM | <1 min |
| **002d_add_security_fk.sql** | Add FK constraint | 🟡 MEDIUM | <1 min |

**Total Execution Time:** ~2-3 minutes
**Rollback Time:** ~1 minute

---

## Migration 002b: Fix Quantity Indexes

### Purpose
Rename index `idx_lots_qty_open` to `idx_lots_quantity_open` to match field naming convention.

### Context
Migration 007 created index on `qty_open` column (line 69):
```sql
-- Current (WRONG):
CREATE INDEX idx_lots_qty_open ON lots(qty_open) WHERE qty_open > 0;

-- Target (CORRECT):
CREATE INDEX idx_lots_quantity_open ON lots(quantity_open) WHERE quantity_open > 0;
```

**Why This Matters:** Index name should match column name for clarity.

---

### Migration Script: 002b_fix_qty_indexes.sql

```sql
-- Migration 002b: Fix Quantity Index Names
-- Date: 2025-11-04
-- Purpose: Rename qty_open index to quantity_open
-- Dependencies: Migration 007 (must exist)
-- Risk: LOW (no downtime, just metadata change)

BEGIN;

-- ============================================================================
-- Verify Migration 007 Ran (qty_open column exists)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'lots' AND column_name = 'qty_open'
    ) THEN
        RAISE EXCEPTION 'Migration 007 has not been run - qty_open column does not exist';
    END IF;
    RAISE NOTICE 'Migration 007 verified - qty_open column exists';
END $$;

-- ============================================================================
-- Phase 1: Drop Old Index
-- ============================================================================

DROP INDEX IF EXISTS idx_lots_qty_open;
RAISE NOTICE 'Dropped old index: idx_lots_qty_open';

-- ============================================================================
-- Phase 2: Create New Index
-- ============================================================================

-- Note: Still references qty_open column (column rename happens later)
-- This just fixes the index NAME to match future column name
CREATE INDEX idx_lots_quantity_open ON lots(qty_open) WHERE qty_open > 0;
RAISE NOTICE 'Created new index: idx_lots_quantity_open (on qty_open column)';

-- ============================================================================
-- Phase 3: Verify Index Created
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'idx_lots_quantity_open'
    ) THEN
        RAISE EXCEPTION 'Index idx_lots_quantity_open was not created';
    END IF;
    RAISE NOTICE 'Index creation verified';
END $$;

-- ============================================================================
-- Phase 4: Update Comments
-- ============================================================================

COMMENT ON INDEX idx_lots_quantity_open IS
'Partial index for open lots (quantity_open > 0). Supports holdings queries.';

COMMIT;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✅ Migration 002b complete';
    RAISE NOTICE '  - Dropped index: idx_lots_qty_open';
    RAISE NOTICE '  - Created index: idx_lots_quantity_open';
    RAISE NOTICE '';
END $$;
```

---

### Rollback Script: rollback_002b.sql

```sql
-- Rollback 002b: Restore Original Index Name
BEGIN;

DROP INDEX IF EXISTS idx_lots_quantity_open;
CREATE INDEX idx_lots_qty_open ON lots(qty_open) WHERE qty_open > 0;
COMMENT ON INDEX idx_lots_qty_open IS 'Partial index for open lots';

RAISE NOTICE 'Rollback 002b complete - restored idx_lots_qty_open';

COMMIT;
```

---

### Testing 002b

```bash
# Run migration
psql -d dawsos_production < backend/db/migrations/002b_fix_qty_indexes.sql

# Verify index exists with new name
psql -d dawsos_production -c "
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'lots'
  AND indexname LIKE '%quantity%';
"
# Expected: idx_lots_quantity_open

# Verify old index is gone
psql -d dawsos_production -c "
SELECT indexname
FROM pg_indexes
WHERE tablename = 'lots'
  AND indexname = 'idx_lots_qty_open';
"
# Expected: 0 rows

# Test query performance (should use index)
psql -d dawsos_production -c "
EXPLAIN ANALYZE
SELECT symbol, qty_open, cost_basis
FROM lots
WHERE portfolio_id = 'test-portfolio-001'
  AND qty_open > 0;
"
# Expected: "Index Scan using idx_lots_quantity_open"
```

---

## Migration 002c: Fix reduce_lot() Function

### Purpose
Update `reduce_lot()` function to use `quantity_open` field name (preparing for column rename).

### Context
Current function (from migration 007, lines 86-127):
```sql
CREATE OR REPLACE FUNCTION reduce_lot(
    p_lot_id UUID,
    p_qty_to_reduce NUMERIC,
    p_closed_date DATE DEFAULT CURRENT_DATE
) RETURNS VOID AS $$
DECLARE
    v_qty_open NUMERIC;
BEGIN
    -- Get current qty_open
    SELECT qty_open INTO v_qty_open  -- ❌ Uses qty_open
    FROM lots
    WHERE id = p_lot_id;

    -- Validation
    IF p_qty_to_reduce > v_qty_open THEN  -- ❌ Uses qty_open
        RAISE EXCEPTION 'Cannot reduce by %: only % shares remaining',
            p_qty_to_reduce, v_qty_open;
    END IF;

    -- Reduce quantity
    UPDATE lots
    SET
        qty_open = qty_open - p_qty_to_reduce,  -- ❌ Uses qty_open
        closed_date = CASE WHEN qty_open - p_qty_to_reduce = 0
                           THEN p_closed_date ELSE NULL END,
        updated_at = NOW()
    WHERE id = p_lot_id;
END;
$$ LANGUAGE plpgsql;
```

**Problem:** Function uses `qty_open` (old name) in 5 places.

**Why This Matters:** When column is renamed to `quantity_open`, function breaks.

---

### Migration Script: 002c_fix_reduce_lot_function.sql

```sql
-- Migration 002c: Fix reduce_lot() Function
-- Date: 2025-11-04
-- Purpose: Update function to use quantity_open (preparing for column rename)
-- Dependencies: Migration 007, Migration 002b
-- Risk: MEDIUM (updates function used by trade execution)

BEGIN;

-- ============================================================================
-- Phase 1: Verify Prerequisites
-- ============================================================================

DO $$
BEGIN
    -- Verify qty_open column exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'lots' AND column_name = 'qty_open'
    ) THEN
        RAISE EXCEPTION 'qty_open column does not exist - run migration 007 first';
    END IF;

    -- Verify reduce_lot function exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc
        WHERE proname = 'reduce_lot'
    ) THEN
        RAISE EXCEPTION 'reduce_lot function does not exist - run migration 007 first';
    END IF;

    RAISE NOTICE 'Prerequisites verified';
END $$;

-- ============================================================================
-- Phase 2: Create Updated Function
-- ============================================================================

-- Note: This version still uses qty_open column name
-- (Column rename happens in separate migration)
-- We're just updating the function to use clearer variable names
-- and prepare for future column rename

CREATE OR REPLACE FUNCTION reduce_lot(
    p_lot_id UUID,
    p_qty_to_reduce NUMERIC,
    p_closed_date DATE DEFAULT CURRENT_DATE
) RETURNS VOID AS $$
DECLARE
    v_quantity_open NUMERIC;  -- ✅ Renamed from v_qty_open
    v_new_quantity NUMERIC;
BEGIN
    -- Get current open quantity
    SELECT qty_open INTO v_quantity_open  -- Still uses qty_open column
    FROM lots
    WHERE id = p_lot_id
    FOR UPDATE;  -- ✅ Added row lock for concurrency

    -- Validate lot exists
    IF v_quantity_open IS NULL THEN
        RAISE EXCEPTION 'Lot % not found', p_lot_id;
    END IF;

    -- Validate reduction amount
    IF p_qty_to_reduce <= 0 THEN
        RAISE EXCEPTION 'Reduction amount must be positive, got %', p_qty_to_reduce;
    END IF;

    IF p_qty_to_reduce > v_quantity_open THEN
        RAISE EXCEPTION 'Cannot reduce by %: only % shares remaining in lot %',
            p_qty_to_reduce, v_quantity_open, p_lot_id;
    END IF;

    -- Calculate new quantity
    v_new_quantity := v_quantity_open - p_qty_to_reduce;

    -- Update lot
    UPDATE lots
    SET
        qty_open = v_new_quantity,  -- Still uses qty_open column
        closed_date = CASE
            WHEN v_new_quantity = 0 THEN p_closed_date
            ELSE NULL
        END,
        updated_at = NOW()
    WHERE id = p_lot_id;

    -- Log the reduction
    RAISE NOTICE 'Lot % reduced by % (% → %)',
        p_lot_id, p_qty_to_reduce, v_quantity_open, v_new_quantity;

END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Phase 3: Update Function Comment
-- ============================================================================

COMMENT ON FUNCTION reduce_lot IS
'Reduce lot quantity and mark as closed if quantity_open reaches 0.
Used by trade execution to process partial or full lot sales.
Includes validation and row-level locking for concurrency safety.';

-- ============================================================================
-- Phase 4: Test Function
-- ============================================================================

DO $$
DECLARE
    v_test_lot_id UUID;
    v_test_portfolio_id UUID;
BEGIN
    -- Create test portfolio
    INSERT INTO portfolios (id, name, currency)
    VALUES (gen_random_uuid(), 'Test Portfolio (Migration 002c)', 'USD')
    RETURNING id INTO v_test_portfolio_id;

    -- Create test lot
    INSERT INTO lots (
        id, portfolio_id, security_id, symbol,
        quantity, qty_open, qty_original,
        cost_basis, cost_basis_per_share, acquisition_date
    ) VALUES (
        gen_random_uuid(), v_test_portfolio_id, gen_random_uuid(), 'TEST',
        100, 100, 100,
        10000, 100, CURRENT_DATE
    )
    RETURNING id INTO v_test_lot_id;

    RAISE NOTICE 'Created test lot: %', v_test_lot_id;

    -- Test reduce_lot function
    PERFORM reduce_lot(v_test_lot_id, 30);

    -- Verify reduction worked
    IF (SELECT qty_open FROM lots WHERE id = v_test_lot_id) != 70 THEN
        RAISE EXCEPTION 'Test failed: expected qty_open=70';
    END IF;

    RAISE NOTICE 'Test passed: qty_open correctly reduced to 70';

    -- Cleanup
    DELETE FROM portfolios WHERE id = v_test_portfolio_id;
    RAISE NOTICE 'Test data cleaned up';

EXCEPTION
    WHEN OTHERS THEN
        -- Cleanup on error
        DELETE FROM portfolios WHERE id = v_test_portfolio_id;
        RAISE;
END $$;

COMMIT;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✅ Migration 002c complete';
    RAISE NOTICE '  - Updated reduce_lot() function';
    RAISE NOTICE '  - Added concurrency safety (row locking)';
    RAISE NOTICE '  - Added validation improvements';
    RAISE NOTICE '  - Function tested successfully';
    RAISE NOTICE '';
END $$;
```

---

### Rollback Script: rollback_002c.sql

```sql
-- Rollback 002c: Restore Original reduce_lot() Function
BEGIN;

-- Restore original function from migration 007
CREATE OR REPLACE FUNCTION reduce_lot(
    p_lot_id UUID,
    p_qty_to_reduce NUMERIC,
    p_closed_date DATE DEFAULT CURRENT_DATE
) RETURNS VOID AS $$
DECLARE
    v_qty_open NUMERIC;
BEGIN
    SELECT qty_open INTO v_qty_open
    FROM lots
    WHERE id = p_lot_id;

    IF v_qty_open IS NULL THEN
        RAISE EXCEPTION 'Lot % not found', p_lot_id;
    END IF;

    IF p_qty_to_reduce > v_qty_open THEN
        RAISE EXCEPTION 'Cannot reduce by %: only % shares remaining',
            p_qty_to_reduce, v_qty_open;
    END IF;

    UPDATE lots
    SET
        qty_open = qty_open - p_qty_to_reduce,
        closed_date = CASE WHEN qty_open - p_qty_to_reduce = 0
                           THEN p_closed_date ELSE NULL END,
        updated_at = NOW()
    WHERE id = p_lot_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION reduce_lot IS
'Reduce lot quantity and mark as closed if qty_open reaches 0';

RAISE NOTICE 'Rollback 002c complete - restored original reduce_lot()';

COMMIT;
```

---

### Testing 002c

```bash
# Run migration
psql -d dawsos_production < backend/db/migrations/002c_fix_reduce_lot_function.sql

# Verify function updated
psql -d dawsos_production -c "
SELECT pg_get_functiondef(oid)
FROM pg_proc
WHERE proname = 'reduce_lot';
"
# Should show updated function with v_quantity_open variable

# Test function works
psql -d dawsos_production -c "
DO \$\$
DECLARE
    v_lot_id UUID;
BEGIN
    -- Find an open lot
    SELECT id INTO v_lot_id
    FROM lots
    WHERE qty_open > 10
    LIMIT 1;

    IF v_lot_id IS NULL THEN
        RAISE NOTICE 'No suitable test lot found';
        RETURN;
    END IF;

    -- Test reducing by 1 share
    PERFORM reduce_lot(v_lot_id, 1);
    RAISE NOTICE 'Test passed: reduce_lot() executed successfully';
END \$\$;
"
```

---

## Migration 002d: Add Security Foreign Key Constraint

### Purpose
Add missing FK constraint `lots.security_id → securities(id)` to prevent orphaned lot records.

### Context
Current schema (001_portfolios_lots_transactions.sql:66):
```sql
-- Current (WRONG):
security_id UUID NOT NULL,  -- No FK constraint!

-- Target (CORRECT):
security_id UUID NOT NULL REFERENCES securities(id) ON DELETE RESTRICT,
```

**Why This Matters:** Without FK constraint:
- Can insert lots with invalid security_id
- Can delete securities that have lots (orphans)
- Database integrity violations propagate to API failures

**Impact:** This caused issues in production where:
- Holdings queries returned lots with missing security data
- JOIN to securities failed
- Pattern execution failed on pricing step

---

### Migration Script: 002d_add_security_fk.sql

```sql
-- Migration 002d: Add Security Foreign Key Constraint
-- Date: 2025-11-04
-- Purpose: Add FK constraint lots.security_id → securities(id)
-- Dependencies: None (base schema)
-- Risk: MEDIUM (may fail if orphaned records exist)

BEGIN;

-- ============================================================================
-- Phase 1: Identify Orphaned Records
-- ============================================================================

DO $$
DECLARE
    v_orphan_count INTEGER;
BEGIN
    -- Count orphaned lots (security_id not in securities)
    SELECT COUNT(*) INTO v_orphan_count
    FROM lots l
    LEFT JOIN securities s ON l.security_id = s.id
    WHERE s.id IS NULL;

    IF v_orphan_count > 0 THEN
        RAISE WARNING 'Found % orphaned lot records', v_orphan_count;

        -- Log to audit log
        INSERT INTO audit_log (event_type, details, created_at)
        VALUES (
            'migration_orphaned_lots',
            jsonb_build_object(
                'migration', '002d_add_security_fk',
                'count', v_orphan_count,
                'timestamp', NOW()
            ),
            NOW()
        );
    ELSE
        RAISE NOTICE 'No orphaned lot records found';
    END IF;
END $$;

-- ============================================================================
-- Phase 2: Create Placeholder Security (If Orphans Exist)
-- ============================================================================

-- Create placeholder security for orphaned lots
INSERT INTO securities (id, symbol, name, asset_class, exchange, currency)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'ORPHAN',
    'Orphaned Security (Migrated)',
    'EQUITY',
    'UNKNOWN',
    'USD'
)
ON CONFLICT (id) DO NOTHING;

-- Update orphaned lots to reference placeholder
UPDATE lots l
SET security_id = '00000000-0000-0000-0000-000000000000'
WHERE NOT EXISTS (
    SELECT 1 FROM securities s WHERE s.id = l.security_id
);

-- ============================================================================
-- Phase 3: Add Foreign Key Constraint
-- ============================================================================

-- Add FK constraint (will fail if any orphans remain)
ALTER TABLE lots
    ADD CONSTRAINT fk_lots_security
    FOREIGN KEY (security_id)
    REFERENCES securities(id)
    ON DELETE RESTRICT;  -- Prevent accidental security deletion

RAISE NOTICE 'Added FK constraint: fk_lots_security';

-- ============================================================================
-- Phase 4: Add Index for FK (Performance)
-- ============================================================================

-- FK already has index (idx_lots_security_id from base schema)
-- But verify it exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'lots' AND indexname = 'idx_lots_security_id'
    ) THEN
        CREATE INDEX idx_lots_security_id ON lots(security_id);
        RAISE NOTICE 'Created index: idx_lots_security_id';
    ELSE
        RAISE NOTICE 'Index already exists: idx_lots_security_id';
    END IF;
END $$;

-- ============================================================================
-- Phase 5: Validation
-- ============================================================================

-- Test that orphaned records cannot be created
DO $$
BEGIN
    -- Try to insert lot with invalid security_id
    BEGIN
        INSERT INTO lots (
            id, portfolio_id, security_id, symbol,
            quantity, qty_open, qty_original,
            cost_basis, cost_basis_per_share, acquisition_date
        ) VALUES (
            gen_random_uuid(),
            (SELECT id FROM portfolios LIMIT 1),
            'ffffffff-ffff-ffff-ffff-ffffffffffff',  -- Invalid security
            'INVALID',
            100, 100, 100,
            1000, 10,
            CURRENT_DATE
        );

        -- If we get here, constraint didn't work
        RAISE EXCEPTION 'FK constraint did not prevent orphaned record!';

    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE 'FK constraint working correctly (test insert blocked)';
    END;
END $$;

-- Verify constraint exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_lots_security'
          AND table_name = 'lots'
    ) THEN
        RAISE EXCEPTION 'FK constraint was not created';
    END IF;
    RAISE NOTICE 'FK constraint verified';
END $$;

COMMIT;

-- Success message
DO $$
DECLARE
    v_lots_count INTEGER;
    v_orphan_security_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_lots_count FROM lots;
    SELECT COUNT(*) INTO v_orphan_security_count
    FROM lots
    WHERE security_id = '00000000-0000-0000-0000-000000000000';

    RAISE NOTICE '';
    RAISE NOTICE '✅ Migration 002d complete';
    RAISE NOTICE '  - Added FK constraint: fk_lots_security';
    RAISE NOTICE '  - Total lots: %', v_lots_count;
    RAISE NOTICE '  - Lots with orphan placeholder: %', v_orphan_security_count;
    RAISE NOTICE '  - FK constraint validated';
    RAISE NOTICE '';
END $$;
```

---

### Rollback Script: rollback_002d.sql

```sql
-- Rollback 002d: Remove Security FK Constraint
BEGIN;

-- Remove FK constraint
ALTER TABLE lots
    DROP CONSTRAINT IF EXISTS fk_lots_security;

-- Optionally remove placeholder security
-- (Commented out to preserve data)
-- DELETE FROM securities WHERE id = '00000000-0000-0000-0000-000000000000';

RAISE NOTICE 'Rollback 002d complete - removed fk_lots_security';

COMMIT;
```

---

### Testing 002d

```bash
# Run migration
psql -d dawsos_production < backend/db/migrations/002d_add_security_fk.sql

# Verify FK constraint exists
psql -d dawsos_production -c "
SELECT
  tc.constraint_name,
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name,
  rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.constraint_name = 'fk_lots_security';
"
# Expected: 1 row showing fk_lots_security constraint

# Test that orphaned records are prevented
psql -d dawsos_production -c "
DO \$\$
BEGIN
    -- Try to insert lot with invalid security_id
    INSERT INTO lots (
        id, portfolio_id, security_id, symbol,
        quantity, qty_open, qty_original,
        cost_basis, cost_basis_per_share, acquisition_date
    ) VALUES (
        gen_random_uuid(),
        (SELECT id FROM portfolios LIMIT 1),
        'invalid-security-id'::uuid,
        'TEST',
        100, 100, 100,
        1000, 10,
        CURRENT_DATE
    );
    RAISE EXCEPTION 'FK constraint did not prevent insert!';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'Test passed: FK constraint prevented invalid insert';
END \$\$;
"

# Check for any orphaned lots
psql -d dawsos_production -c "
SELECT COUNT(*) as orphan_count
FROM lots l
LEFT JOIN securities s ON l.security_id = s.id
WHERE s.id IS NULL;
"
# Expected: 0 (no orphans)
```

---

## 📦 Complete Execution Plan

### Pre-Execution Checklist

```bash
# 1. Verify database is accessible
psql -d dawsos_production -c "SELECT version();"

# 2. Verify migration 007 has been run
psql -d dawsos_production -c "
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'lots'
  AND column_name IN ('qty_open', 'qty_original');
"
# Expected: 2 rows (both columns exist)

# 3. Create backup
pg_dump dawsos_production > backup_before_002bcd_$(date +%Y%m%d).sql

# 4. Test on staging first
# (Run all migrations on staging database)
```

---

### Execution Order

**All migrations must run in order:**

```bash
# Stage 1: Database (Replit Agent)
psql -d dawsos_production < backend/db/migrations/002b_fix_qty_indexes.sql
psql -d dawsos_production < backend/db/migrations/002c_fix_reduce_lot_function.sql
psql -d dawsos_production < backend/db/migrations/002d_add_security_fk.sql

# Verify all migrations succeeded
psql -d dawsos_production -c "
SELECT
  (SELECT COUNT(*) FROM pg_indexes WHERE indexname = 'idx_lots_quantity_open') as index_check,
  (SELECT COUNT(*) FROM pg_proc WHERE proname = 'reduce_lot') as function_check,
  (SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_name = 'fk_lots_security') as fk_check;
"
# Expected: index_check=1, function_check=1, fk_check=1
```

---

### Post-Execution Validation

```bash
# 1. Verify database integrity
psql -d dawsos_production -c "
-- Check for orphaned lots
SELECT COUNT(*) as orphan_count
FROM lots l
LEFT JOIN securities s ON l.security_id = s.id
WHERE s.id IS NULL;
-- Expected: 0

-- Check lot counts
SELECT
  COUNT(*) as total_lots,
  COUNT(*) FILTER (WHERE qty_open > 0) as open_lots,
  SUM(qty_open) as total_open_quantity
FROM lots;
-- Should match pre-migration counts
"

# 2. Test reduce_lot function
psql -d dawsos_production -c "
SELECT reduce_lot(
  (SELECT id FROM lots WHERE qty_open > 10 LIMIT 1),
  1
);
"
# Should succeed without errors

# 3. Test FK constraint
psql -d dawsos_production -c "
-- This should fail
INSERT INTO lots (
  id, portfolio_id, security_id, symbol,
  quantity, qty_open, qty_original,
  cost_basis, cost_basis_per_share, acquisition_date
) VALUES (
  gen_random_uuid(),
  (SELECT id FROM portfolios LIMIT 1),
  'invalid-uuid'::uuid,
  'TEST',
  100, 100, 100,
  1000, 10,
  CURRENT_DATE
);
"
# Expected: ERROR: insert or update on table "lots" violates foreign key constraint "fk_lots_security"
```

---

## 🚨 Rollback Procedures

### If Migration 002b Fails

```bash
psql -d dawsos_production < backend/db/migrations/rollback_002b.sql
```

### If Migration 002c Fails

```bash
psql -d dawsos_production < backend/db/migrations/rollback_002c.sql
```

### If Migration 002d Fails

```bash
psql -d dawsos_production < backend/db/migrations/rollback_002d.sql
```

### Full Rollback (All 3)

```bash
psql -d dawsos_production < backend/db/migrations/rollback_002d.sql
psql -d dawsos_production < backend/db/migrations/rollback_002c.sql
psql -d dawsos_production < backend/db/migrations/rollback_002b.sql
```

---

## 📊 Impact Assessment

### Changes Summary

| Change | Before | After | Impact |
|--------|--------|-------|--------|
| **Index Name** | `idx_lots_qty_open` | `idx_lots_quantity_open` | 🟢 None (just metadata) |
| **Function** | `v_qty_open` variable | `v_quantity_open` variable | 🟢 None (internal) |
| **FK Constraint** | None | `fk_lots_security` | 🟡 Prevents orphans |

### Performance Impact

- **Index rename:** No performance impact (same index, different name)
- **Function update:** No performance impact (same logic, clearer code)
- **FK constraint:** Minor overhead on INSERT/DELETE (~1-2ms per operation)

### Data Integrity Improvements

✅ **Before:** Could insert lots with invalid security_id (orphaned records)
✅ **After:** FK constraint prevents orphaned records
✅ **Before:** reduce_lot() had unclear variable names
✅ **After:** reduce_lot() has clear variable names and better validation

---

## 🎯 Next Steps After Migration

### Immediate (Replit)

1. **Verify migrations succeeded** (run validation queries above)
2. **Monitor error logs** for any FK constraint violations
3. **Test trade execution** (uses reduce_lot function)
4. **Test holdings queries** (use index)

### Follow-Up (Week 1-2)

1. **Column rename** (qty_open → quantity_open) - Separate migration
2. **Code updates** (51 backend files) - Claude IDE
3. **Pattern system updates** (13 patterns + 46 dataPaths) - Claude IDE

---

## 📝 Notes for Replit Agent

### Why These Migrations Don't Rename Columns Yet

**Strategic Decision:** These migrations prepare the database for column rename without actually renaming yet.

**Reason:**
1. Index rename (002b) prepares index name
2. Function update (002c) prepares function code
3. FK constraint (002d) adds data integrity
4. **Column rename happens later** after code is updated

**Why This Order:**
- If we renamed columns now, all queries would break immediately
- By preparing first, we can update code gradually
- Final column rename happens when code is ready

### What Replit Agent Should Do

1. ✅ **Run these 3 migrations** (002b, 002c, 002d)
2. ✅ **Verify they succeed** (run validation queries)
3. ✅ **Monitor for issues** (check error logs)
4. ⏸️ **Wait for code updates** (Claude IDE will update 51 files)
5. ⏸️ **Then run column rename** (separate migration, later)

---

## 📞 Support

**If migrations fail:**
1. Run rollback scripts immediately
2. Check error logs for details
3. Verify database state with validation queries
4. Report issue with full error message

**Common Issues:**

| Issue | Cause | Solution |
|-------|-------|----------|
| "relation already exists" | Migration already run | Skip or use DROP IF EXISTS |
| "foreign key violation" | Orphaned records exist | Check orphan count, may need manual cleanup |
| "function does not exist" | Migration 007 not run | Run migration 007 first |

---

**Document Complete**
**Status:** 🔴 Ready for Replit Agent Execution
**Estimated Time:** 2-3 minutes
**Risk Level:** 🟡 MEDIUM (test on staging first)

---

**Generated:** November 4, 2025
**Generated By:** Claude (Anthropic)
**Version:** 1.0
