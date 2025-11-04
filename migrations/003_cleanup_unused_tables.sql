-- Migration 003: Remove unused and duplicate tables
-- Date: November 4, 2025
-- Safe to run: These tables have 0 rows and minimal/no code references

BEGIN;

-- Phase 1: Remove completely unused tables (never implemented features)
DROP TABLE IF EXISTS ledger_snapshots CASCADE;  -- Beancount feature never built
DROP TABLE IF EXISTS ledger_transactions CASCADE;  -- Beancount feature never built
DROP TABLE IF EXISTS audit_log CASCADE;  -- Audit logging never implemented
DROP TABLE IF EXISTS reconciliation_results CASCADE;  -- Reconciliation never used

-- Phase 2: Remove unused cache tables (compute-first approach used instead)
DROP TABLE IF EXISTS position_factor_betas CASCADE;  -- Factor analysis not cached
DROP TABLE IF EXISTS rating_rubrics CASCADE;  -- Ratings computed on-demand
DROP TABLE IF EXISTS rebalance_suggestions CASCADE;  -- Optimizer results not cached
DROP TABLE IF EXISTS scenario_shocks CASCADE;  -- Scenarios not implemented

-- Note: Keeping currency_attribution and factor_exposures as they have 1 row each
-- and are referenced in active development code

-- Note: Alert consolidation requires code changes first:
-- - alert_deliveries (redundant with dlq)
-- - alert_dlq (duplicate of dlq table)
-- - alert_retries (can use dlq retry_count)
-- These should be removed after updating alert service code

COMMIT;

-- Verification query (run after migration):
-- SELECT COUNT(*) AS remaining_tables FROM pg_tables WHERE schemaname = 'public';
-- Should show 22 tables (down from 30)