-- Migration 1: Reproducibility Enhancements
-- Purpose: Add ledger commit hash tracking and pack freshness flag
-- Date: 2025-10-21
-- Phase: Week 0.5 (Foundation)
-- Priority: P0 (Critical for reproducibility guarantee)

-- ============================================================================
-- FORWARD MIGRATION
-- ============================================================================

-- Add ledger commit hash to pricing pack
-- Required for: "Every Result includes pricing_pack_id + ledger_commit_hash"
ALTER TABLE pricing_pack ADD COLUMN IF NOT EXISTS ledger_commit_hash TEXT;
COMMENT ON COLUMN pricing_pack.ledger_commit_hash IS 'Git commit hash of ledger repo at pack build time';

-- Add freshness flag to pricing pack
-- Required for: Executor freshness gate (Section 8 spec)
ALTER TABLE pricing_pack ADD COLUMN IF NOT EXISTS is_fresh BOOLEAN DEFAULT FALSE;
COMMENT ON COLUMN pricing_pack.is_fresh IS 'TRUE after pre-warm completes; Executor blocks until fresh';

-- Add partial index for fast fresh pack lookup
CREATE INDEX IF NOT EXISTS idx_pack_fresh ON pricing_pack (date DESC) WHERE is_fresh = TRUE;

-- Add ledger path to portfolios
-- Required for: Reconciliation jobs to know which journal to parse
ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS ledger_path TEXT;
COMMENT ON COLUMN portfolios.ledger_path IS 'Path to Beancount journal: ledger/portfolios/{portfolio_id}.bean';

-- Add ledger transaction ID to transactions
-- Required for: Beancount traceability
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS ledger_tx_id TEXT;
COMMENT ON COLUMN transactions.ledger_tx_id IS 'Links to Beancount transaction ID for provenance';

-- Add trace ID to telemetry tables for OpenTelemetry correlation
ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS trace_id TEXT;
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS trace_id TEXT;
COMMENT ON COLUMN analytics_events.trace_id IS 'OpenTelemetry trace ID for distributed tracing';
COMMENT ON COLUMN audit_log.trace_id IS 'OpenTelemetry trace ID for distributed tracing';

-- Add cooldown to alerts for rate limiting
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS cooldown_minutes INT DEFAULT 15;
COMMENT ON COLUMN alerts.cooldown_minutes IS 'Minimum minutes between alert deliveries (prevents spam)';

-- ============================================================================
-- ROLLBACK
-- ============================================================================

-- To rollback:
-- DROP INDEX IF EXISTS idx_pack_fresh;
-- ALTER TABLE pricing_pack DROP COLUMN IF EXISTS ledger_commit_hash;
-- ALTER TABLE pricing_pack DROP COLUMN IF EXISTS is_fresh;
-- ALTER TABLE portfolios DROP COLUMN IF EXISTS ledger_path;
-- ALTER TABLE transactions DROP COLUMN IF EXISTS ledger_tx_id;
-- ALTER TABLE analytics_events DROP COLUMN IF EXISTS trace_id;
-- ALTER TABLE audit_log DROP COLUMN IF EXISTS trace_id;
-- ALTER TABLE alerts DROP COLUMN IF EXISTS cooldown_minutes;
