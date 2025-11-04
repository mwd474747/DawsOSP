-- Migration 002b: Fix Quantity Index Names
-- Date: 2025-11-04
-- Purpose: Rename qty_open index to quantity_open
-- Dependencies: Migration 001_field_standardization.sql (must exist)
-- Risk: LOW (no downtime, just metadata change)

BEGIN;

-- ============================================================================
-- Verify Migration 001 Ran (quantity_open column exists)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'lots' AND column_name = 'quantity_open'
    ) THEN
        RAISE EXCEPTION 'Migration 001 has not been run - quantity_open column does not exist';
    END IF;
    RAISE NOTICE 'Migration 001 verified - quantity_open column exists';
END $$;

-- ============================================================================
-- Phase 1: Drop Old Index
-- ============================================================================

DROP INDEX IF EXISTS idx_lots_qty_open;
RAISE NOTICE 'Dropped old index: idx_lots_qty_open';

-- ============================================================================
-- Phase 2: Create New Index
-- ============================================================================

-- Create index with correct name on quantity_open column
CREATE INDEX idx_lots_quantity_open ON lots(quantity_open) WHERE quantity_open > 0;
RAISE NOTICE 'Created new index: idx_lots_quantity_open (on quantity_open column)';

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