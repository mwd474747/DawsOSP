-- Migration 2: Reconciliation Tracking
-- Purpose: Add table for ledger vs DB reconciliation results
-- Date: 2025-10-21
-- Phase: Week 0.5 (Foundation)
-- Priority: P0 (Critical for ±1bp validation)

-- ============================================================================
-- FORWARD MIGRATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS reconciliations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asof_date DATE NOT NULL,
  ledger_commit_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('OK', 'FAIL')),
  discrepancies_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (portfolio_id, asof_date)
);

COMMENT ON TABLE reconciliations IS 'Tracks nightly reconciliation between Beancount ledger and DB lots';
COMMENT ON COLUMN reconciliations.status IS 'OK if all positions match ±1bp; FAIL if discrepancies found';
COMMENT ON COLUMN reconciliations.discrepancies_json IS 'Array of {symbol, ledger_qty, db_qty, qty_diff, ledger_cost, db_cost, cost_diff}';

-- Index for latest reconciliation per portfolio
CREATE INDEX IF NOT EXISTS idx_reconciliations_portfolio_date
  ON reconciliations (portfolio_id, asof_date DESC);

-- Enable RLS
ALTER TABLE reconciliations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see reconciliations for their portfolios
CREATE POLICY IF NOT EXISTS reconciliations_rw ON reconciliations
  USING (portfolio_id IN (
    SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)
  ))
  WITH CHECK (portfolio_id IN (
    SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)
  ));

-- ============================================================================
-- ROLLBACK
-- ============================================================================

-- To rollback:
-- DROP POLICY IF EXISTS reconciliations_rw ON reconciliations;
-- ALTER TABLE reconciliations DISABLE ROW LEVEL SECURITY;
-- DROP INDEX IF EXISTS idx_reconciliations_portfolio_date;
-- DROP TABLE IF EXISTS reconciliations;
