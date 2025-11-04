-- Migration 002c: Fix reduce_lot() Function
-- Date: 2025-11-04
-- Purpose: Update function to use quantity_open (preparing for column rename)
-- Dependencies: Migration 001_field_standardization
-- Risk: MEDIUM (updates function used by trade execution)

BEGIN;

-- ============================================================================
-- Phase 1: Verify Prerequisites
-- ============================================================================

DO $$
BEGIN
    -- Verify quantity_open column exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'lots' AND column_name = 'quantity_open'
    ) THEN
        RAISE EXCEPTION 'quantity_open column does not exist - run migration 001 first';
    END IF;

    -- Verify reduce_lot function exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc
        WHERE proname = 'reduce_lot'
    ) THEN
        RAISE WARNING 'reduce_lot function does not exist - will create it now';
    END IF;

    RAISE NOTICE 'Prerequisites verified';
END $$;

-- ============================================================================
-- Phase 2: Create Updated Function
-- ============================================================================

-- Update function to use new column names
CREATE OR REPLACE FUNCTION reduce_lot(
    p_lot_id UUID,
    p_qty_to_reduce NUMERIC,
    p_closed_date DATE DEFAULT CURRENT_DATE
) RETURNS VOID AS $$
DECLARE
    v_quantity_open NUMERIC;  -- Renamed from v_qty_open
    v_new_quantity NUMERIC;
BEGIN
    -- Get current open quantity
    SELECT quantity_open INTO v_quantity_open  -- Using new column name
    FROM lots
    WHERE id = p_lot_id
    FOR UPDATE;  -- Added row lock for concurrency

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
        quantity_open = v_new_quantity,  -- Using new column name
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
    v_test_user_id UUID;
    v_test_security_id UUID;
BEGIN
    -- Get a test user (or create one)
    SELECT id INTO v_test_user_id FROM users LIMIT 1;
    IF v_test_user_id IS NULL THEN
        INSERT INTO users (email, password_hash, role)
        VALUES ('test_migration_002c@dawsos.com', 'test_hash', 'USER')
        RETURNING id INTO v_test_user_id;
    END IF;

    -- Get a test security (or create one)
    SELECT id INTO v_test_security_id FROM securities WHERE symbol = 'TEST_MIG_002C' LIMIT 1;
    IF v_test_security_id IS NULL THEN
        INSERT INTO securities (symbol, name, trading_currency)
        VALUES ('TEST_MIG_002C', 'Test Security for Migration 002c', 'USD')
        RETURNING id INTO v_test_security_id;
    END IF;

    -- Create test portfolio
    INSERT INTO portfolios (user_id, name, base_currency)
    VALUES (v_test_user_id, 'Test Portfolio (Migration 002c)', 'USD')
    RETURNING id INTO v_test_portfolio_id;

    -- Create test lot
    INSERT INTO lots (
        id, portfolio_id, security_id, symbol,
        quantity, quantity_open, quantity_original,
        cost_basis, cost_basis_per_share, acquisition_date
    ) VALUES (
        gen_random_uuid(), v_test_portfolio_id, v_test_security_id, 'TEST_MIG_002C',
        100, 100, 100,
        10000, 100, CURRENT_DATE
    )
    RETURNING id INTO v_test_lot_id;

    RAISE NOTICE 'Created test lot: %', v_test_lot_id;

    -- Test reduce_lot function
    PERFORM reduce_lot(v_test_lot_id, 30);

    -- Verify reduction worked
    IF (SELECT quantity_open FROM lots WHERE id = v_test_lot_id) != 70 THEN
        RAISE EXCEPTION 'Test failed: expected quantity_open=70';
    END IF;

    RAISE NOTICE 'Test passed: quantity_open correctly reduced to 70';

    -- Cleanup
    DELETE FROM lots WHERE portfolio_id = v_test_portfolio_id;
    DELETE FROM portfolios WHERE id = v_test_portfolio_id;
    DELETE FROM securities WHERE symbol = 'TEST_MIG_002C' AND id = v_test_security_id;
    RAISE NOTICE 'Test data cleaned up';

EXCEPTION
    WHEN OTHERS THEN
        -- Cleanup on error
        DELETE FROM lots WHERE portfolio_id = v_test_portfolio_id;
        DELETE FROM portfolios WHERE id = v_test_portfolio_id;
        DELETE FROM securities WHERE symbol = 'TEST_MIG_002C' AND id = v_test_security_id;
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