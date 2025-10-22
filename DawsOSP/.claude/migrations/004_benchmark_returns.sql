-- Migration 4: Benchmark Returns
-- Purpose: Add table for benchmark return history (for beta calculation and hedged/unhedged comparison)
-- Date: 2025-10-21
-- Phase: Sprint 1 (Truth Spine)
-- Priority: P0 (Required for beta calculation)

-- ============================================================================
-- FORWARD MIGRATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS benchmark_returns (
  benchmark_id UUID NOT NULL REFERENCES benchmarks(id) ON DELETE CASCADE,
  asof_date DATE NOT NULL,
  return NUMERIC(18,8) NOT NULL,
  pricing_pack_id TEXT NOT NULL REFERENCES pricing_pack(id) ON DELETE RESTRICT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (benchmark_id, asof_date, pricing_pack_id)
);

COMMENT ON TABLE benchmark_returns IS 'Daily returns for benchmarks (hedged and unhedged)';
COMMENT ON COLUMN benchmark_returns.return IS 'Daily return (e.g., 0.0123 for +1.23%)';

-- Convert to hypertable (requires TimescaleDB extension)
SELECT create_hypertable('benchmark_returns', 'asof_date', if_not_exists => TRUE);

-- Index for fast benchmark lookups
CREATE INDEX IF NOT EXISTS idx_benchmark_returns_bench_date
  ON benchmark_returns (benchmark_id, asof_date DESC);

-- Index for pack-based queries
CREATE INDEX IF NOT EXISTS idx_benchmark_returns_pack
  ON benchmark_returns (pricing_pack_id, benchmark_id);

-- ============================================================================
-- CONTINUOUS AGGREGATES
-- ============================================================================

-- 30-day rolling beta (portfolio vs benchmark)
-- NOTE: This requires portfolio_daily_values to exist (from Migration 3)
CREATE MATERIALIZED VIEW IF NOT EXISTS ca_portfolio_rolling_beta_30d
  WITH (timescaledb.continuous) AS
SELECT pdv.portfolio_id,
       p.benchmark_id,
       time_bucket('1 day', pdv.asof_date) AS bucket,
       REGR_SLOPE(
         (pdv.total_value - LAG(pdv.total_value) OVER (PARTITION BY pdv.portfolio_id ORDER BY pdv.asof_date)) / LAG(pdv.total_value) OVER (PARTITION BY pdv.portfolio_id ORDER BY pdv.asof_date),
         br.return
       ) OVER (
         PARTITION BY pdv.portfolio_id, p.benchmark_id
         ORDER BY pdv.asof_date
         ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
       ) AS beta_30d
FROM portfolio_daily_values pdv
JOIN portfolios p ON pdv.portfolio_id = p.id
JOIN benchmark_returns br ON p.benchmark_id = br.benchmark_id AND pdv.asof_date = br.asof_date AND pdv.pricing_pack_id = br.pricing_pack_id
GROUP BY pdv.portfolio_id, p.benchmark_id, bucket, pdv.total_value, pdv.asof_date, br.return;

-- Refresh policy: refresh last 60 days every hour
SELECT add_continuous_aggregate_policy('ca_portfolio_rolling_beta_30d',
  start_offset => INTERVAL '60 days',
  end_offset   => INTERVAL '1 day',
  schedule_interval => INTERVAL '1 hour',
  if_not_exists => TRUE
);

-- ============================================================================
-- SEED DATA (Optional - for testing)
-- ============================================================================

-- Example: Populate SPY (SPXT:CAD) benchmark returns
-- This would be done by a service in production, but shown here for completeness
/*
INSERT INTO benchmark_returns (benchmark_id, asof_date, return, pricing_pack_id)
SELECT
  (SELECT id FROM benchmarks WHERE code = 'SPXT:CAD'),
  generate_series('2024-01-01'::date, '2024-12-31'::date, '1 day'::interval)::date,
  (random() * 0.04 - 0.02), -- Simulated daily return (-2% to +2%)
  (SELECT id FROM pricing_pack WHERE date = generate_series.generate_series LIMIT 1)
WHERE EXISTS (SELECT 1 FROM benchmarks WHERE code = 'SPXT:CAD');
*/

-- ============================================================================
-- ROLLBACK
-- ============================================================================

-- To rollback:
-- DROP MATERIALIZED VIEW IF EXISTS ca_portfolio_rolling_beta_30d;
-- DROP INDEX IF EXISTS idx_benchmark_returns_bench_date;
-- DROP INDEX IF EXISTS idx_benchmark_returns_pack;
-- DROP TABLE IF EXISTS benchmark_returns;
