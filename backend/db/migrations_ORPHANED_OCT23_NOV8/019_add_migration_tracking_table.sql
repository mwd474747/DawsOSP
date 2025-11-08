-- Migration 019: Add Migration Tracking Table
-- Date: November 6, 2025
-- Purpose: Create a table to track which migrations have been executed

BEGIN;

-- Create migration tracking table
CREATE TABLE IF NOT EXISTS migration_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_name TEXT NOT NULL UNIQUE,
    migration_number INTEGER NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    executed_by TEXT DEFAULT CURRENT_USER,
    description TEXT,
    rollback_script TEXT,
    checksum TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Add index for quick lookups
CREATE INDEX idx_migration_history_name ON migration_history(migration_name);
CREATE INDEX idx_migration_history_executed_at ON migration_history(executed_at DESC);

-- Add comments
COMMENT ON TABLE migration_history IS 'Tracks all database migrations that have been executed';
COMMENT ON COLUMN migration_history.migration_name IS 'Unique name of the migration file (e.g., 001_field_standardization)';
COMMENT ON COLUMN migration_history.migration_number IS 'Migration sequence number';
COMMENT ON COLUMN migration_history.executed_at IS 'When the migration was executed';
COMMENT ON COLUMN migration_history.executed_by IS 'Database user who executed the migration';
COMMENT ON COLUMN migration_history.description IS 'Human-readable description of what the migration does';
COMMENT ON COLUMN migration_history.rollback_script IS 'SQL to rollback this migration if needed';
COMMENT ON COLUMN migration_history.checksum IS 'MD5 hash of the migration file to detect changes';
COMMENT ON COLUMN migration_history.success IS 'Whether the migration completed successfully';
COMMENT ON COLUMN migration_history.error_message IS 'Error message if migration failed';

-- Insert records for all migrations we know have been executed
-- Based on our investigation, these migrations have been completed:
INSERT INTO migration_history (migration_name, migration_number, description, executed_at) VALUES
    ('001_field_standardization', 1, 'Renamed qty_open → quantity_open, qty_original → quantity_original', '2025-11-04 00:00:00'::timestamptz),
    ('002_add_constraints', 2, 'Added FK constraints and indexes', '2025-11-04 00:00:00'::timestamptz),
    ('002b_fix_qty_indexes', 2, 'Fixed quantity field indexes', '2025-11-04 00:00:00'::timestamptz),
    ('002c_fix_reduce_lot_function', 2, 'Updated reduce_lot function for new field names', '2025-11-04 00:00:00'::timestamptz),
    ('002d_add_security_fk', 2, 'Added lots.security_id FK constraint', '2025-11-04 00:00:00'::timestamptz),
    ('003_cleanup_unused_tables', 3, 'Removed unused tables', '2025-11-04 00:00:00'::timestamptz),
    ('005_create_rls_policies', 5, 'Created row-level security policies', '2025-11-04 00:00:00'::timestamptz),
    ('007_add_lot_qty_tracking', 7, 'Added quantity_open and quantity_original fields', '2025-10-23 00:00:00'::timestamptz),
    ('008_add_corporate_actions_support', 8, 'Added corporate actions table', '2025-10-23 00:00:00'::timestamptz),
    ('009_add_scenario_dar_tables', 9, 'Added scenario analysis tables', '2025-10-23 00:00:00'::timestamptz),
    ('010_add_users_and_audit_log', 10, 'Added users table', '2025-10-23 00:00:00'::timestamptz),
    ('011_alert_delivery_system', 11, 'Added alert delivery system', '2025-10-23 00:00:00'::timestamptz),
    ('012_add_alert_channels', 12, 'Added alert channels', '2025-10-23 00:00:00'::timestamptz),
    ('013_add_derived_indicators', 13, 'Added derived indicators view', '2025-10-23 00:00:00'::timestamptz),
    ('014_add_quantity_deprecation_comment', 14, 'Added deprecation comment to lots.quantity', '2025-01-14 00:00:00'::timestamptz),
    ('015_add_economic_indicators', 15, 'Added economic indicators table', '2025-01-14 00:00:00'::timestamptz),
    ('016_standardize_asof_date_field', 16, 'Standardized asof_date field naming', '2025-11-06 00:00:00'::timestamptz),
    ('017_add_realized_pl_field', 17, 'Added realized_pl to transactions table', '2025-11-06 00:00:00'::timestamptz),
    ('018_add_cost_basis_method_field', 18, 'Added cost_basis_method to portfolios table', '2025-11-06 00:00:00'::timestamptz)
ON CONFLICT (migration_name) DO NOTHING;  -- Don't insert if already exists

-- Create a function to check if a migration has been executed
CREATE OR REPLACE FUNCTION migration_executed(p_migration_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS(
        SELECT 1 FROM migration_history 
        WHERE migration_name = p_migration_name 
        AND success = TRUE
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION migration_executed IS 'Check if a specific migration has been successfully executed';

-- Create a view for the latest migration status
CREATE OR REPLACE VIEW v_migration_status AS
SELECT 
    migration_number,
    migration_name,
    description,
    executed_at,
    executed_by,
    success
FROM migration_history
ORDER BY migration_number DESC, executed_at DESC;

COMMENT ON VIEW v_migration_status IS 'View showing all migrations and their execution status';

-- Verify the table was created
SELECT 'Migration tracking table created with ' || COUNT(*) || ' migration records' AS status
FROM migration_history;

COMMIT;

-- Rollback script:
-- DROP VIEW IF EXISTS v_migration_status;
-- DROP FUNCTION IF EXISTS migration_executed(TEXT);
-- DROP TABLE IF EXISTS migration_history CASCADE;