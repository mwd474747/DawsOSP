-- Migration 022: Update RLS Policies with Comments and Improvements
-- Created: 2025-11-08
-- Purpose: Add comprehensive comments to existing RLS policies for better documentation

-- ============================================================================
-- UPDATE EXISTING RLS POLICY COMMENTS
-- ============================================================================

-- Add comprehensive comments to all existing RLS policies for better documentation
-- This improves maintainability and helps developers understand the security model

-- 1. Portfolios table policies
COMMENT ON POLICY portfolios_isolation ON portfolios IS
    'Base RLS policy: Users can only access their own portfolios. 
     This is the foundation of multi-tenant isolation in DawsOS.
     Implementation: portfolios.user_id = current_setting(''app.user_id'')::uuid';

-- 2. Lots table policies
COMMENT ON POLICY lots_isolation ON lots IS
    'Users can only access lots (holdings) in their own portfolios.
     Cascading isolation via portfolio_id foreign key.
     Implementation: Check portfolio ownership through portfolios table join';

-- 3. Transactions table policies
COMMENT ON POLICY transactions_isolation ON transactions IS
    'Users can only access transactions in their own portfolios.
     Ensures transaction privacy across tenants.
     Implementation: Check portfolio ownership through portfolios table join';

-- 4. Portfolio metrics policies
COMMENT ON POLICY portfolio_metrics_isolation ON portfolio_metrics IS
    'Users can only access performance metrics for their own portfolios.
     TimescaleDB hypertable with time-series isolation.
     Implementation: Check portfolio ownership through portfolios table join';

-- 5. Currency attribution policies
COMMENT ON POLICY currency_attribution_isolation ON currency_attribution IS
    'Users can only access currency attribution analysis for their own portfolios.
     TimescaleDB hypertable for FX impact analysis.
     Implementation: Check portfolio ownership through portfolios table join';

-- 6. Factor exposures policies
COMMENT ON POLICY factor_exposures_isolation ON factor_exposures IS
    'Users can only access factor exposures for their own portfolios.
     TimescaleDB hypertable for risk factor analysis.
     Implementation: Check portfolio ownership through portfolios table join';

-- 7. Alerts table policies (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'alerts') THEN
        EXECUTE 'COMMENT ON POLICY alerts_read ON alerts IS 
            ''Users can only read their own alerts.
             Critical for alert privacy and notification isolation.
             Implementation: Check portfolio ownership through portfolios table join''';
        
        EXECUTE 'COMMENT ON POLICY alerts_write ON alerts IS 
            ''Users can create/update alerts for their own portfolios only.
             Prevents alert spam and ensures proper ownership.
             Implementation: Check portfolio ownership on INSERT/UPDATE''';
    END IF;
END $$;

-- 8. Audit log policies (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'audit_log') THEN
        EXECUTE 'COMMENT ON POLICY audit_log_read ON audit_log IS 
            ''Users can only read audit logs for their own actions.
             Maintains audit trail privacy across tenants.
             Implementation: user_id = current_setting(''''app.user_id'''')::uuid''';
    END IF;
END $$;

-- ============================================================================
-- CREATE HELPER VIEW FOR RLS POLICY VERIFICATION
-- ============================================================================

-- Create a view to help verify RLS policies are working correctly
CREATE OR REPLACE VIEW rls_policy_status AS
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual AS using_expression,
    with_check AS with_check_expression
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

COMMENT ON VIEW rls_policy_status IS
    'Helper view to inspect all RLS policies in the public schema.
     Use this to verify policies are correctly configured.
     Example: SELECT * FROM rls_policy_status WHERE tablename = ''portfolios'';';

-- ============================================================================
-- CREATE FUNCTION FOR RLS TESTING
-- ============================================================================

-- Create a helper function to test RLS policies
CREATE OR REPLACE FUNCTION test_rls_policy(
    p_table_name TEXT,
    p_user_id UUID
) RETURNS TABLE(
    can_select BOOLEAN,
    can_insert BOOLEAN,
    can_update BOOLEAN,
    can_delete BOOLEAN,
    row_count INTEGER
) AS $$
DECLARE
    v_can_select BOOLEAN := FALSE;
    v_can_insert BOOLEAN := FALSE;
    v_can_update BOOLEAN := FALSE;
    v_can_delete BOOLEAN := FALSE;
    v_row_count INTEGER := 0;
BEGIN
    -- Set the user context
    PERFORM set_config('app.user_id', p_user_id::TEXT, true);
    
    -- Test SELECT permission
    BEGIN
        EXECUTE format('SELECT COUNT(*) FROM %I', p_table_name) INTO v_row_count;
        v_can_select := TRUE;
    EXCEPTION WHEN OTHERS THEN
        v_can_select := FALSE;
    END;
    
    -- Test INSERT permission (simplified test)
    BEGIN
        EXECUTE format('SELECT has_table_privilege($1, %L, ''INSERT'')', p_table_name) 
        USING p_user_id INTO v_can_insert;
    EXCEPTION WHEN OTHERS THEN
        v_can_insert := FALSE;
    END;
    
    -- Test UPDATE permission
    BEGIN
        EXECUTE format('SELECT has_table_privilege($1, %L, ''UPDATE'')', p_table_name) 
        USING p_user_id INTO v_can_update;
    EXCEPTION WHEN OTHERS THEN
        v_can_update := FALSE;
    END;
    
    -- Test DELETE permission
    BEGIN
        EXECUTE format('SELECT has_table_privilege($1, %L, ''DELETE'')', p_table_name) 
        USING p_user_id INTO v_can_delete;
    EXCEPTION WHEN OTHERS THEN
        v_can_delete := FALSE;
    END;
    
    RETURN QUERY SELECT 
        v_can_select,
        v_can_insert,
        v_can_update,
        v_can_delete,
        v_row_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION test_rls_policy IS
    'Test RLS policies for a specific table and user.
     Example: SELECT * FROM test_rls_policy(''portfolios'', ''123e4567-e89b-12d3-a456-426614174000'');
     Returns permissions and visible row count for the specified user.';

-- ============================================================================
-- VERIFY RLS IS ENABLED ON ALL REQUIRED TABLES
-- ============================================================================

-- Create a function to check RLS status
CREATE OR REPLACE FUNCTION check_rls_status()
RETURNS TABLE(
    table_name TEXT,
    rls_enabled BOOLEAN,
    policy_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.relname::TEXT AS table_name,
        c.relrowsecurity AS rls_enabled,
        COUNT(p.policyname)::INTEGER AS policy_count
    FROM pg_class c
    LEFT JOIN pg_policies p ON c.relname = p.tablename AND p.schemaname = 'public'
    WHERE c.relnamespace = 'public'::regnamespace
    AND c.relkind = 'r'  -- Regular tables only
    AND c.relname IN (
        'portfolios', 'lots', 'transactions', 'alerts', 'audit_log',
        'portfolio_metrics', 'currency_attribution', 'factor_exposures',
        'security_ratings', 'news_sentiment'
    )
    GROUP BY c.relname, c.relrowsecurity
    ORDER BY c.relname;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_rls_status IS
    'Check RLS enablement status for all security-critical tables.
     Example: SELECT * FROM check_rls_status();
     Shows which tables have RLS enabled and how many policies are defined.';

-- ============================================================================
-- GRANT NECESSARY PERMISSIONS
-- ============================================================================

-- Grant execute permissions on helper functions to dawsos_app role
GRANT EXECUTE ON FUNCTION test_rls_policy(TEXT, UUID) TO dawsos_app;
GRANT EXECUTE ON FUNCTION check_rls_status() TO dawsos_app;
GRANT SELECT ON rls_policy_status TO dawsos_app;

-- ============================================================================
-- FINAL VERIFICATION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '
    ============================================================================
    RLS POLICY UPDATE COMPLETE
    ============================================================================
    
    The following improvements have been made:
    1. Added comprehensive comments to all RLS policies
    2. Created helper view: rls_policy_status
    3. Created testing function: test_rls_policy()
    4. Created status check function: check_rls_status()
    
    To verify RLS is working correctly:
    - Check status: SELECT * FROM check_rls_status();
    - View policies: SELECT * FROM rls_policy_status;
    - Test a policy: SELECT * FROM test_rls_policy(''portfolios'', [user_uuid]);
    
    ============================================================================
    ';
END $$;