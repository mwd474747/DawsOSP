
-- Portfolio Daily Values Table
-- Purpose: Store daily NAV, cash flows, and position values for TWR/MWR calculations
-- Created: 2025-10-31 (Phase 1.1 - METRICS_IMPLEMENTATION_PLAN.md)

CREATE TABLE IF NOT EXISTS portfolio_daily_values (
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    valuation_date DATE NOT NULL,
    total_value NUMERIC(20,2) NOT NULL,
    cash_balance NUMERIC(20,2) NOT NULL DEFAULT 0,
    positions_value NUMERIC(20,2) NOT NULL DEFAULT 0,
    cash_flows NUMERIC(20,2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'CAD',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (portfolio_id, valuation_date)
);

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_portfolio_daily_values_date 
    ON portfolio_daily_values(valuation_date DESC);

CREATE INDEX IF NOT EXISTS idx_portfolio_daily_values_portfolio 
    ON portfolio_daily_values(portfolio_id, valuation_date DESC);

-- Convert to hypertable (requires TimescaleDB)
-- This will partition data by valuation_date for efficient time-series queries
SELECT create_hypertable(
    'portfolio_daily_values',
    'valuation_date',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 month'
);

-- Add compression policy (optional, for older data)
ALTER TABLE portfolio_daily_values SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'portfolio_id'
);

-- Compress data older than 90 days
SELECT add_compression_policy(
    'portfolio_daily_values',
    INTERVAL '90 days',
    if_not_exists => TRUE
);

COMMENT ON TABLE portfolio_daily_values IS 
'Daily portfolio valuations aggregated from transactions and pricing packs. Source of truth for TWR/MWR calculations.';

COMMENT ON COLUMN portfolio_daily_values.total_value IS 
'Total portfolio NAV = positions_value + cash_balance';

COMMENT ON COLUMN portfolio_daily_values.cash_flows IS 
'Net cash flows for the day (deposits - withdrawals + dividends)';
