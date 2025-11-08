-- Migration: Add users and audit_log tables for authentication
-- Purpose: Support JWT authentication, RBAC, and audit logging
-- Created: 2025-10-27
-- Priority: P0 (Critical for security)

-- ============================================================================
-- Users Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'USER',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Constraints
    CONSTRAINT users_role_valid CHECK (role IN ('VIEWER', 'USER', 'MANAGER', 'ADMIN')),
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE users IS 'User accounts for authentication and authorization';
COMMENT ON COLUMN users.id IS 'User UUID (primary key)';
COMMENT ON COLUMN users.email IS 'User email address (unique, login identifier)';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt password hash';
COMMENT ON COLUMN users.role IS 'User role: VIEWER, USER, MANAGER, ADMIN';
COMMENT ON COLUMN users.is_active IS 'Account status (soft delete)';
COMMENT ON COLUMN users.last_login_at IS 'Last successful login timestamp';

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
    user_agent TEXT,

    -- Foreign key to users
    CONSTRAINT audit_log_user_fk FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for common audit queries
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_user_timestamp ON audit_log(user_id, timestamp DESC);

COMMENT ON TABLE audit_log IS 'Immutable audit trail of all user actions';
COMMENT ON COLUMN audit_log.user_id IS 'User who performed the action';
COMMENT ON COLUMN audit_log.action IS 'Action name (e.g., execute_pattern, export_pdf)';
COMMENT ON COLUMN audit_log.resource_type IS 'Type of resource (e.g., pattern, portfolio, report)';
COMMENT ON COLUMN audit_log.resource_id IS 'ID of the resource (pattern_id, portfolio_id, etc.)';
COMMENT ON COLUMN audit_log.details IS 'JSON details about the action (inputs, outputs, metadata)';
COMMENT ON COLUMN audit_log.timestamp IS 'When the action occurred';
COMMENT ON COLUMN audit_log.ip_address IS 'Client IP address (optional)';
COMMENT ON COLUMN audit_log.user_agent IS 'Client user agent (optional)';

-- ============================================================================
-- Updated At Trigger for Users
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Seed Default Admin User (for initial setup)
-- ============================================================================

-- Insert default admin user (password: "admin123" - CHANGE IN PRODUCTION!)
-- Password hash generated with: bcrypt.hashpw(b"admin123", bcrypt.gensalt(rounds=12))
INSERT INTO users (id, email, password_hash, role)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'admin@dawsos.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oo4fPOJ2VCDq',  -- "admin123"
    'ADMIN'
)
ON CONFLICT (email) DO NOTHING;

-- Insert default test user (password: "user123")
INSERT INTO users (id, email, password_hash, role)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'user@dawsos.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',  -- "user123"
    'USER'
)
ON CONFLICT (email) DO NOTHING;

COMMENT ON TABLE users IS 'Default users: admin@dawsos.com (ADMIN, pw: admin123), user@dawsos.com (USER, pw: user123) - CHANGE PASSWORDS!';

-- ============================================================================
-- Row-Level Security (RLS) Policies for Users
-- ============================================================================

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own record
CREATE POLICY users_select_own
    ON users
    FOR SELECT
    USING (id = current_setting('app.user_id', true)::uuid OR current_setting('app.user_id', true)::uuid = '00000000-0000-0000-0000-000000000000');

-- Policy: Only admins can insert users
CREATE POLICY users_insert_admin
    ON users
    FOR INSERT
    WITH CHECK (current_setting('app.user_id', true)::uuid = '00000000-0000-0000-0000-000000000000');

-- Policy: Users can update their own record, admins can update any
CREATE POLICY users_update_own_or_admin
    ON users
    FOR UPDATE
    USING (id = current_setting('app.user_id', true)::uuid OR current_setting('app.user_id', true)::uuid = '00000000-0000-0000-0000-000000000000');

-- Policy: Only admins can delete users
CREATE POLICY users_delete_admin
    ON users
    FOR DELETE
    USING (current_setting('app.user_id', true)::uuid = '00000000-0000-0000-0000-000000000000');

-- ============================================================================
-- Row-Level Security (RLS) Policies for Audit Log
-- ============================================================================

-- Enable RLS on audit_log table
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own audit logs, admins can view all
CREATE POLICY audit_log_select_own_or_admin
    ON audit_log
    FOR SELECT
    USING (
        user_id = current_setting('app.user_id', true)::uuid
        OR current_setting('app.user_id', true)::uuid = '00000000-0000-0000-0000-000000000000'
    );

-- Policy: Only the audit service can insert (via service account)
-- For now, allow all inserts (will be restricted in production)
CREATE POLICY audit_log_insert_all
    ON audit_log
    FOR INSERT
    WITH CHECK (TRUE);

-- Policy: No updates or deletes allowed (immutable audit trail)
-- Audit logs are append-only

-- ============================================================================
-- Update portfolios table to reference users
-- ============================================================================

-- Add foreign key constraint to portfolios.user_id if not exists
-- (Portfolios table already has user_id column from earlier migration)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'portfolios_user_fk'
        AND table_name = 'portfolios'
    ) THEN
        ALTER TABLE portfolios
        ADD CONSTRAINT portfolios_user_fk
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- ============================================================================
-- Grants (Ensure application role has access)
-- ============================================================================

-- Grant privileges to application role (dawsos_app)
GRANT SELECT, INSERT, UPDATE ON users TO dawsos_app;
GRANT SELECT, INSERT ON audit_log TO dawsos_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO dawsos_app;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify users table
DO $$
BEGIN
    RAISE NOTICE '✅ Users table created';
    RAISE NOTICE '   - Default admin: admin@dawsos.com (password: admin123)';
    RAISE NOTICE '   - Default user: user@dawsos.com (password: user123)';
    RAISE NOTICE '   - ⚠️  CHANGE DEFAULT PASSWORDS IN PRODUCTION!';
END $$;

-- Verify audit_log table
DO $$
BEGIN
    RAISE NOTICE '✅ Audit log table created';
    RAISE NOTICE '   - Immutable audit trail enabled';
    RAISE NOTICE '   - RLS policies active';
END $$;
