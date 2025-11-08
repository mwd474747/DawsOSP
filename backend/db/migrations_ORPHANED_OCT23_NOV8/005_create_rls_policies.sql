-- Row-Level Security (RLS) Policies
-- Purpose: Multi-tenant isolation for portfolio-scoped tables
-- Updated: 2025-10-22
-- Priority: P0 (Critical for production security)

-- ============================================================================
-- CONTEXT
-- ============================================================================
-- DawsOS uses PostgreSQL Row-Level Security (RLS) to enforce multi-tenant
-- isolation. Each database query sets app.user_id via SET LOCAL, and RLS
-- policies ensure users can only access their own portfolios and related data.
--
-- Infrastructure: backend/app/db/connection.py:get_db_connection_with_rls()
-- Usage: async with get_db_connection_with_rls(user_id) as conn: ...
--
-- Security Model:
-- - Base isolation: portfolios.user_id = current_setting('app.user_id')::uuid
-- - Cascading isolation: Related tables check portfolio ownership via FK
-- - Global tables: No RLS (pricing_packs, securities, fx_rates)
-- ============================================================================

-- ============================================================================
-- 1. PORTFOLIOS (Base Isolation)
-- ============================================================================

ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

CREATE POLICY portfolios_isolation ON portfolios
    FOR ALL
    USING (user_id = current_setting('app.user_id', true)::uuid);

COMMENT ON POLICY portfolios_isolation ON portfolios IS
    'Base RLS policy: Users can only access their own portfolios';

-- ============================================================================
-- 2. LOTS (Holdings)
-- ============================================================================

ALTER TABLE lots ENABLE ROW LEVEL SECURITY;

CREATE POLICY lots_isolation ON lots
    FOR ALL
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

COMMENT ON POLICY lots_isolation ON lots IS
    'Users can only access lots in their own portfolios';

-- ============================================================================
-- 3. TRANSACTIONS
-- ============================================================================

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY transactions_isolation ON transactions
    FOR ALL
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

COMMENT ON POLICY transactions_isolation ON transactions IS
    'Users can only access transactions in their own portfolios';

-- ============================================================================
-- 4. PORTFOLIO_METRICS (TimescaleDB Hypertable)
-- ============================================================================

ALTER TABLE portfolio_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY portfolio_metrics_isolation ON portfolio_metrics
    FOR ALL
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

COMMENT ON POLICY portfolio_metrics_isolation ON portfolio_metrics IS
    'Users can only access metrics for their own portfolios';

-- ============================================================================
-- 5. CURRENCY_ATTRIBUTION (TimescaleDB Hypertable)
-- ============================================================================

ALTER TABLE currency_attribution ENABLE ROW LEVEL SECURITY;

CREATE POLICY currency_attribution_isolation ON currency_attribution
    FOR ALL
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

COMMENT ON POLICY currency_attribution_isolation ON currency_attribution IS
    'Users can only access currency attribution for their own portfolios';

-- ============================================================================
-- 6. FACTOR_EXPOSURES (TimescaleDB Hypertable)
-- ============================================================================

ALTER TABLE factor_exposures ENABLE ROW LEVEL SECURITY;

CREATE POLICY factor_exposures_isolation ON factor_exposures
    FOR ALL
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

COMMENT ON POLICY factor_exposures_isolation ON factor_exposures IS
    'Users can only access factor exposures for their own portfolios';

-- ============================================================================
-- 7. ALERTS
-- ============================================================================

ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY alerts_isolation ON alerts
    FOR ALL
    USING (user_id = current_setting('app.user_id', true)::uuid);

COMMENT ON POLICY alerts_isolation ON alerts IS
    'Users can only access their own alerts';

-- ============================================================================
-- 8. NOTIFICATIONS
-- ============================================================================

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY notifications_isolation ON notifications
    FOR ALL
    USING (user_id = current_setting('app.user_id', true)::uuid);

COMMENT ON POLICY notifications_isolation ON notifications IS
    'Users can only access their own notifications';

-- ============================================================================
-- 9. REBALANCE_SUGGESTIONS
-- ============================================================================

ALTER TABLE rebalance_suggestions ENABLE ROW LEVEL SECURITY;

CREATE POLICY rebalance_suggestions_isolation ON rebalance_suggestions
    FOR ALL
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

COMMENT ON POLICY rebalance_suggestions_isolation ON rebalance_suggestions IS
    'Users can only access rebalance suggestions for their own portfolios';

-- ============================================================================
-- 10. RECONCILIATION_RESULTS
-- ============================================================================

ALTER TABLE reconciliation_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY reconciliation_results_isolation ON reconciliation_results
    FOR ALL
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

COMMENT ON POLICY reconciliation_results_isolation ON reconciliation_results IS
    'Users can only access reconciliation results for their own portfolios';

-- ============================================================================
-- 11. LEDGER_TRANSACTIONS
-- ============================================================================

ALTER TABLE ledger_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY ledger_transactions_isolation ON ledger_transactions
    FOR ALL
    USING (
        -- Match ledger account to portfolio (convention: Assets:Portfolio:<UUID>)
        account LIKE '%' || (
            SELECT id::text FROM portfolios
            WHERE user_id = current_setting('app.user_id', true)::uuid
        ) || '%'
    );

COMMENT ON POLICY ledger_transactions_isolation ON ledger_transactions IS
    'Users can only access ledger transactions for their own portfolios';

-- ============================================================================
-- GLOBAL TABLES (No RLS)
-- ============================================================================
-- These tables are shared across all users and should NOT have RLS enabled:
-- - pricing_packs (global pricing data)
-- - securities (global securities database)
-- - fx_rates (global FX rates)
-- - macro_indicators (global macro data)
-- - regime_history (global regime data)
-- - security_ratings (global ratings, pre-warmed nightly)
-- - dlq (admin-only, no user_id)

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify RLS is enabled on all required tables
DO $$
DECLARE
    missing_rls TEXT[];
BEGIN
    SELECT ARRAY_AGG(tablename)
    INTO missing_rls
    FROM pg_tables
    WHERE schemaname = 'public'
      AND tablename IN (
          'portfolios',
          'lots',
          'transactions',
          'portfolio_metrics',
          'currency_attribution',
          'factor_exposures',
          'alerts',
          'notifications',
          'rebalance_suggestions',
          'reconciliation_results',
          'ledger_transactions'
      )
      AND NOT EXISTS (
          SELECT 1
          FROM pg_class c
          JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE n.nspname = 'public'
            AND c.relname = pg_tables.tablename
            AND c.relrowsecurity = true
      );

    IF missing_rls IS NOT NULL THEN
        RAISE EXCEPTION 'RLS not enabled on tables: %', missing_rls;
    ELSE
        RAISE NOTICE '✅ RLS enabled on all 11 portfolio-scoped tables';
    END IF;
END $$;

-- Verify all policies exist
DO $$
DECLARE
    policy_count INT;
BEGIN
    SELECT COUNT(*)
    INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public'
      AND policyname LIKE '%isolation%';

    IF policy_count < 11 THEN
        RAISE EXCEPTION 'Expected 11 RLS policies, found %', policy_count;
    ELSE
        RAISE NOTICE '✅ All 11 RLS policies created';
    END IF;
END $$;

-- List all RLS policies
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
  AND policyname LIKE '%isolation%'
ORDER BY tablename;

-- ============================================================================
-- TESTING RLS
-- ============================================================================
-- To test RLS enforcement, use these queries:

-- Test 1: Set RLS context for user A
-- SET LOCAL app.user_id = '11111111-1111-1111-1111-111111111111';
-- SELECT * FROM portfolios;  -- Should only see user A's portfolios

-- Test 2: Set RLS context for user B
-- SET LOCAL app.user_id = '22222222-2222-2222-2222-222222222222';
-- SELECT * FROM portfolios;  -- Should only see user B's portfolios

-- Test 3: Try to access user B's portfolio as user A (should return 0 rows)
-- SET LOCAL app.user_id = '11111111-1111-1111-1111-111111111111';
-- SELECT * FROM portfolios WHERE id = '<user_b_portfolio_id>';  -- 0 rows

-- ============================================================================
-- PERFORMANCE NOTES
-- ============================================================================
-- RLS policies are evaluated for EVERY query, so they must be fast.
-- All policies use indexed columns:
-- - portfolios.user_id (indexed in 001_create_users_portfolios.sql)
-- - lots.portfolio_id, transactions.portfolio_id, etc. (indexed via FK)
--
-- The subquery pattern `portfolio_id IN (SELECT id FROM portfolios WHERE ...)`
-- is optimized by PostgreSQL query planner and will use indexes.
--
-- For TimescaleDB hypertables, RLS policies are automatically applied to
-- all chunks, so performance should be consistent.

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
SELECT 'RLS policies migration 005 completed successfully' AS status;
