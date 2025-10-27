-- Migration: Add Lot Quantity Tracking
-- Purpose: Enable partial lot reductions for tax lot accounting
-- Date: 2025-10-23
-- Priority: P0 (Required for UAT-003 to UAT-005)

-- ============================================================================
-- CONTEXT
-- ============================================================================
-- The current lots table only has 'quantity' and 'is_open' fields, which
-- don't support partial lot reductions needed for proper tax lot accounting.
--
-- For example:
-- - Buy 100 shares of AAPL (create lot with qty=100)
-- - Sell 60 shares (need to track qty_open=40, qty_original=100)
-- - Sell 40 shares (close lot: qty_open=0)
--
-- This migration adds:
-- - qty_original: Original quantity when lot was created
-- - qty_open: Remaining open quantity
-- - closed_date: Date when lot was fully closed (qty_open=0)
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Add new columns
-- ============================================================================

ALTER TABLE lots
    ADD COLUMN IF NOT EXISTS qty_original NUMERIC,
    ADD COLUMN IF NOT EXISTS qty_open NUMERIC,
    ADD COLUMN IF NOT EXISTS closed_date DATE;

-- ============================================================================
-- Step 2: Migrate existing data
-- ============================================================================

-- For existing lots, set qty_original and qty_open based on quantity
UPDATE lots
SET
    qty_original = quantity,
    qty_open = CASE WHEN is_open THEN quantity ELSE 0 END,
    closed_date = CASE WHEN NOT is_open THEN updated_at::date ELSE NULL END
WHERE qty_original IS NULL;

-- ============================================================================
-- Step 3: Add constraints
-- ============================================================================

-- Make columns NOT NULL (now that we've migrated data)
ALTER TABLE lots
    ALTER COLUMN qty_original SET NOT NULL,
    ALTER COLUMN qty_open SET NOT NULL;

-- Add check constraints
ALTER TABLE lots
    ADD CONSTRAINT lots_qty_original_positive CHECK (qty_original > 0),
    ADD CONSTRAINT lots_qty_open_nonnegative CHECK (qty_open >= 0),
    ADD CONSTRAINT lots_qty_open_lte_original CHECK (qty_open <= qty_original);

-- ============================================================================
-- Step 4: Update indexes
-- ============================================================================

-- Remove old is_open index (will be replaced by qty_open)
DROP INDEX IF EXISTS idx_lots_is_open;

-- Add new index for open lots (qty_open > 0)
CREATE INDEX idx_lots_qty_open ON lots(qty_open) WHERE qty_open > 0;

-- Add index for closed_date (for tax reporting)
CREATE INDEX idx_lots_closed_date ON lots(closed_date) WHERE closed_date IS NOT NULL;

-- ============================================================================
-- Step 5: Add comments
-- ============================================================================

COMMENT ON COLUMN lots.qty_original IS 'Original quantity when lot was created';
COMMENT ON COLUMN lots.qty_open IS 'Remaining open quantity (0 when fully closed)';
COMMENT ON COLUMN lots.closed_date IS 'Date when lot was fully closed (qty_open=0)';

-- ============================================================================
-- Step 6: Create helper function to close/reduce lots
-- ============================================================================

CREATE OR REPLACE FUNCTION reduce_lot(
    p_lot_id UUID,
    p_qty_to_reduce NUMERIC,
    p_disposition_date DATE
) RETURNS NUMERIC AS $$
DECLARE
    v_qty_open NUMERIC;
    v_qty_reduced NUMERIC;
BEGIN
    -- Get current qty_open
    SELECT qty_open INTO v_qty_open
    FROM lots
    WHERE id = p_lot_id;

    IF v_qty_open IS NULL THEN
        RAISE EXCEPTION 'Lot % not found', p_lot_id;
    END IF;

    IF p_qty_to_reduce > v_qty_open THEN
        RAISE EXCEPTION 'Cannot reduce lot by % shares, only % available', p_qty_to_reduce, v_qty_open;
    END IF;

    -- Reduce lot
    v_qty_reduced := p_qty_to_reduce;

    UPDATE lots
    SET
        qty_open = qty_open - v_qty_reduced,
        closed_date = CASE
            WHEN (qty_open - v_qty_reduced) = 0 THEN p_disposition_date
            ELSE NULL
        END,
        is_open = CASE
            WHEN (qty_open - v_qty_reduced) = 0 THEN FALSE
            ELSE TRUE
        END,
        updated_at = NOW()
    WHERE id = p_lot_id;

    RETURN v_qty_reduced;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION reduce_lot IS 'Reduce lot quantity and mark as closed if qty_open reaches 0';

-- ============================================================================
-- Step 7: Verification
-- ============================================================================

-- Verify columns exist
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'lots'
  AND column_name IN ('qty_original', 'qty_open', 'closed_date', 'quantity', 'is_open')
ORDER BY ordinal_position;

-- Verify constraints
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'lots'::regclass
  AND conname LIKE '%qty%'
ORDER BY conname;

-- Verify data migration
SELECT
    COUNT(*) AS total_lots,
    COUNT(*) FILTER (WHERE qty_open > 0) AS open_lots,
    COUNT(*) FILTER (WHERE qty_open = 0) AS closed_lots,
    COUNT(*) FILTER (WHERE qty_open IS NULL) AS invalid_lots
FROM lots;

COMMIT;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. This migration is backwards compatible - the old 'quantity' and 'is_open'
--    columns are preserved but deprecated.
--
-- 2. The reduce_lot() function is a helper for trade execution. It ensures
--    atomic lot reductions and proper closed_date tracking.
--
-- 3. After this migration, application code should use:
--    - qty_original: Total shares purchased in this lot
--    - qty_open: Shares remaining (decreases on sells)
--    - closed_date: When lot was fully sold (NULL if still open)
--
-- 4. The old 'quantity' and 'is_open' fields are kept for backwards
--    compatibility but should be considered deprecated.
--
-- 5. To rollback this migration:
--    DROP FUNCTION reduce_lot(UUID, NUMERIC, DATE);
--    ALTER TABLE lots DROP COLUMN qty_original, DROP COLUMN qty_open, DROP COLUMN closed_date;
-- ============================================================================

SELECT 'Migration 007: Lot quantity tracking added successfully' AS status;
