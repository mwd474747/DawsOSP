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
        
        -- Note: We can't use audit_log as it was removed in migration 003
        -- Just log to console instead
        RAISE NOTICE 'Migration 002d: Found % orphaned lots that need cleanup', v_orphan_count;
    ELSE
        RAISE NOTICE 'No orphaned lot records found';
    END IF;
END $$;

-- ============================================================================
-- Phase 2: Create Placeholder Security (If Orphans Exist)
-- ============================================================================

-- Create placeholder security for orphaned lots
INSERT INTO securities (id, symbol, name, security_type, exchange, trading_currency)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'ORPHAN',
    'Orphaned Security (Migrated)',
    'equity',
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
-- Phase 3: Check if constraint already exists
-- ============================================================================

DO $$
BEGIN
    -- Check if the FK constraint already exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_lots_security'
          AND table_name = 'lots'
    ) THEN
        RAISE NOTICE 'FK constraint fk_lots_security already exists - skipping creation';
    ELSE
        -- Add FK constraint (will fail if any orphans remain)
        ALTER TABLE lots
            ADD CONSTRAINT fk_lots_security
            FOREIGN KEY (security_id)
            REFERENCES securities(id)
            ON DELETE RESTRICT;  -- Prevent accidental security deletion
        
        RAISE NOTICE 'Added FK constraint: fk_lots_security';
    END IF;
END $$;

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
DECLARE
    v_test_portfolio_id UUID;
    v_test_user_id UUID;
BEGIN
    -- Get a test user (or create one)
    SELECT id INTO v_test_user_id FROM users LIMIT 1;
    IF v_test_user_id IS NULL THEN
        INSERT INTO users (email, password_hash, role)
        VALUES ('test_migration_002d@dawsos.com', 'test_hash', 'USER')
        RETURNING id INTO v_test_user_id;
    END IF;
    
    -- Get a test portfolio
    SELECT id INTO v_test_portfolio_id FROM portfolios LIMIT 1;
    IF v_test_portfolio_id IS NULL THEN
        INSERT INTO portfolios (user_id, name, base_currency)
        VALUES (v_test_user_id, 'Test Portfolio (Migration 002d)', 'USD')
        RETURNING id INTO v_test_portfolio_id;
    END IF;
    
    -- Try to insert lot with invalid security_id
    BEGIN
        INSERT INTO lots (
            id, portfolio_id, security_id, symbol,
            quantity, quantity_open, quantity_original,
            cost_basis, cost_basis_per_share, acquisition_date
        ) VALUES (
            gen_random_uuid(),
            v_test_portfolio_id,
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
    
    -- Cleanup test data
    DELETE FROM portfolios WHERE name = 'Test Portfolio (Migration 002d)';
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