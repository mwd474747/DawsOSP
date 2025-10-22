-- Migration 3: Portfolio Daily Values
-- Purpose: Add table for TWR calculation inputs
-- Date: 2025-10-21
-- Phase: Sprint 1 (Truth Spine)
-- Priority: P0 (Required for TWR calculation)

-- ============================================================================
-- FORWARD MIGRATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS portfolio_daily_values (
  portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asof_date DATE NOT NULL,
  total_value NUMERIC(28,10) NOT NULL,
  cash_flows NUMERIC(28,10) NOT NULL DEFAULT 0,
  pricing_pack_id TEXT NOT NULL REFERENCES pricing_pack(id) ON DELETE RESTRICT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (portfolio_id, asof_date, pricing_pack_id)
);

COMMENT ON TABLE portfolio_daily_values IS 'Daily portfolio valuations and cash flows for TWR calculation';
COMMENT ON COLUMN portfolio_daily_values.total_value IS 'Total portfolio value in base currency (from valued positions)';
COMMENT ON COLUMN portfolio_daily_values.cash_flows IS 'Net cash flows on this date (contributions - withdrawals)';

-- Convert to hypertable (requires TimescaleDB extension)
SELECT create_hypertable('portfolio_daily_values', 'asof_date', if_not_exists => TRUE);

-- Index for fast portfolio lookups
CREATE INDEX IF NOT EXISTS idx_daily_values_portfolio_date
  ON portfolio_daily_values (portfolio_id, asof_date DESC);

-- Index for pack-based queries
CREATE INDEX IF NOT EXISTS idx_daily_values_pack
  ON portfolio_daily_values (pricing_pack_id, portfolio_id);

-- Enable RLS
ALTER TABLE portfolio_daily_values ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see values for their portfolios
CREATE POLICY IF NOT EXISTS daily_values_rw ON portfolio_daily_values
  USING (portfolio_id IN (
    SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)
  ))
  WITH CHECK (portfolio_id IN (
    SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)
  ));

-- ============================================================================
-- CONTINUOUS AGGREGATES (Optional but recommended)
-- ============================================================================

-- 7-day rolling average value
CREATE MATERIALIZED VIEW IF NOT EXISTS ca_portfolio_7d_avg_value
  WITH (timescaledb.continuous) AS
SELECT portfolio_id,
       time_bucket('1 day', asof_date) AS bucket,
       AVG(total_value) OVER (
         PARTITION BY portfolio_id
         ORDER BY asof_date
         ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ) AS avg_value_7d
FROM portfolio_daily_values
GROUP BY portfolio_id, bucket, total_value, asof_date;

-- Refresh policy: refresh last 30 days every hour
SELECT add_continuous_aggregate_policy('ca_portfolio_7d_avg_value',
  start_offset => INTERVAL '30 days',
  end_offset   => INTERVAL '1 day',
  schedule_interval => INTERVAL '1 hour',
  if_not_exists => TRUE
);

-- ============================================================================
-- ROLLBACK
-- ============================================================================

-- To rollback:
-- DROP MATERIALIZED VIEW IF EXISTS ca_portfolio_7d_avg_value;
-- DROP POLICY IF EXISTS daily_values_rw ON portfolio_daily_values;
-- ALTER TABLE portfolio_daily_values DISABLE ROW LEVEL SECURITY;
-- DROP INDEX IF EXISTS idx_daily_values_portfolio_date;
-- DROP INDEX IF EXISTS idx_daily_values_pack;
-- DROP TABLE IF EXISTS portfolio_daily_values;
