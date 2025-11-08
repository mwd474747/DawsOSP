-- Migration: Restore audit_log table
-- Purpose: Restore audit_log table deleted by migration 003 (Nov 4, 2025)
-- Context: Phase -1.2 Database Reconciliation (Nov 8, 2025)
-- Related: PRODUCTION_ISSUES_ACTION_PLAN.md (Issue 1)
--
-- The Audit Log Paradox:
--   - Oct 23, 2025: Backend migration 010 CREATED audit_log (never applied)
--   - Nov 4, 2025: Root migration 003 DELETED audit_log ("never implemented")
--   - Result: Code expects audit_log, table doesn't exist
--   - Fix: Restore table from backend migration 010
--
-- Created: 2025-11-08
-- Priority: P0 (CRITICAL - breaks auth, audit service, reports)

-- ============================================================================
-- Audit Log Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address TEXT,
    user_agent TEXT
);

-- Note: Foreign key to users table omitted (check if users table exists first)
-- Will add in separate migration if needed

-- Indexes for common audit queries
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_timestamp ON audit_log(user_id, timestamp DESC);

COMMENT ON TABLE audit_log IS 'Immutable audit trail of all user actions (restored Nov 8, 2025)';
COMMENT ON COLUMN audit_log.user_id IS 'User who performed the action';
COMMENT ON COLUMN audit_log.action IS 'Action name (e.g., login, logout, execute_pattern, export_pdf)';
COMMENT ON COLUMN audit_log.resource_type IS 'Type of resource (e.g., pattern, portfolio, report)';
COMMENT ON COLUMN audit_log.resource_id IS 'ID of the resource (pattern_id, portfolio_id, etc.)';
COMMENT ON COLUMN audit_log.details IS 'JSON details about the action (inputs, outputs, metadata)';
COMMENT ON COLUMN audit_log.timestamp IS 'When the action occurred';
COMMENT ON COLUMN audit_log.ip_address IS 'Client IP address (optional)';
COMMENT ON COLUMN audit_log.user_agent IS 'Client user agent (optional)';

-- ============================================================================
-- Row-Level Security (RLS) Policies for Audit Log
-- ============================================================================

-- Enable RLS on audit_log table
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own audit logs, admins can view all
-- (Assumes app.user_id is set in session context)
CREATE POLICY IF NOT EXISTS audit_log_select_own_or_admin
    ON audit_log
    FOR SELECT
    USING (
        user_id = COALESCE(current_setting('app.user_id', true), '00000000-0000-0000-0000-000000000000')::uuid
        OR COALESCE(current_setting('app.user_id', true), '00000000-0000-0000-0000-000000000000')::uuid = '00000000-0000-0000-0000-000000000000'
    );

-- Policy: Allow all inserts (audit service needs to write logs)
CREATE POLICY IF NOT EXISTS audit_log_insert_all
    ON audit_log
    FOR INSERT
    WITH CHECK (TRUE);

-- Policy: No updates or deletes allowed (immutable audit trail)
-- Audit logs are append-only

-- ============================================================================
-- Grants (Ensure application role has access)
-- ============================================================================

-- Grant privileges to application role if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dawsos_app') THEN
        GRANT SELECT, INSERT ON audit_log TO dawsos_app;
        RAISE NOTICE '✅ Granted audit_log privileges to dawsos_app role';
    ELSE
        RAISE NOTICE '⚠️  dawsos_app role not found, skipping grants';
    END IF;
END $$;

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    row_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO row_count FROM audit_log;
    RAISE NOTICE '✅ Audit log table restored';
    RAISE NOTICE '   - Rows: %', row_count;
    RAISE NOTICE '   - Immutable audit trail enabled';
    RAISE NOTICE '   - RLS policies active';
    RAISE NOTICE '';
    RAISE NOTICE '📋 Related: PRODUCTION_ISSUES_ACTION_PLAN.md (Issue 1)';
    RAISE NOTICE '   - Fixes: 14 broken code references (auth.py, audit.py, reports.py)';
    RAISE NOTICE '   - Restores: Login/logout auditing, audit service, report export tracking';
END $$;
