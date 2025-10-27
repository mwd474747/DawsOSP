-- Portfolio Metrics Tables
-- Purpose: Time-series portfolio metrics with TimescaleDB hypertables
-- Updated: 2025-10-22
-- Priority: P0 (Critical for S2-W3)

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- portfolio_metrics (Main Hypertable)
-- ============================================================================

DROP TABLE IF EXISTS portfolio_metrics CASCADE;

CREATE TABLE portfolio_metrics (
    -- Identity
    portfolio_id UUID NOT NULL,
    asof_date DATE NOT NULL,
    pricing_pack_id TEXT NOT NULL REFERENCES pricing_packs(id),

    -- Daily Returns
    twr_1d NUMERIC(12, 8),  -- Time-weighted return (daily)
    twr_1d_base NUMERIC(12, 8),  -- TWR in base currency

    -- Cumulative Returns (Time-Weighted)
    twr_mtd NUMERIC(12, 8),  -- Month-to-date
    twr_qtd NUMERIC(12, 8),  -- Quarter-to-date
    twr_ytd NUMERIC(12, 8),  -- Year-to-date
    twr_1y NUMERIC(12, 8),   -- 1 year
    twr_3y_ann NUMERIC(12, 8),  -- 3 year annualized
    twr_5y_ann NUMERIC(12, 8),  -- 5 year annualized
    twr_inception_ann NUMERIC(12, 8),  -- Since inception annualized

    -- Money-Weighted Returns (IRR)
    mwr_ytd NUMERIC(12, 8),
    mwr_1y NUMERIC(12, 8),
    mwr_3y_ann NUMERIC(12, 8),
    mwr_inception_ann NUMERIC(12, 8),

    -- Volatility (Annualized)
    volatility_30d NUMERIC(12, 8),  -- 30-day rolling
    volatility_60d NUMERIC(12, 8),  -- 60-day rolling
    volatility_90d NUMERIC(12, 8),  -- 90-day rolling
    volatility_1y NUMERIC(12, 8),   -- 1-year rolling

    -- Sharpe Ratio (vs risk-free rate)
    sharpe_30d NUMERIC(12, 8),
    sharpe_60d NUMERIC(12, 8),
    sharpe_90d NUMERIC(12, 8),
    sharpe_1y NUMERIC(12, 8),

    -- Drawdown
    max_drawdown_1y NUMERIC(12, 8),  -- Max drawdown over 1 year
    max_drawdown_3y NUMERIC(12, 8),  -- Max drawdown over 3 years
    current_drawdown NUMERIC(12, 8),  -- Current drawdown from peak

    -- Benchmark Relative (vs benchmark)
    alpha_1y NUMERIC(12, 8),  -- Excess return vs benchmark
    alpha_3y_ann NUMERIC(12, 8),
    beta_1y NUMERIC(12, 8),   -- Systematic risk vs benchmark
    beta_3y NUMERIC(12, 8),
    tracking_error_1y NUMERIC(12, 8),  -- Volatility of excess returns
    information_ratio_1y NUMERIC(12, 8),  -- Alpha / Tracking Error

    -- Trading Statistics
    win_rate_1y NUMERIC(5, 4),  -- % of winning trades
    avg_win NUMERIC(12, 8),  -- Average winning trade return
    avg_loss NUMERIC(12, 8),  -- Average losing trade return

    -- Portfolio Values
    portfolio_value_base NUMERIC(20, 2),  -- Total value in base currency
    portfolio_value_local NUMERIC(20, 2),  -- Total value in local currency
    cash_balance NUMERIC(20, 2),

    -- Metadata
    base_currency TEXT NOT NULL,  -- Portfolio base currency (e.g., CAD)
    benchmark_id TEXT,  -- Benchmark identifier
    reconciliation_error_bps NUMERIC(10, 4),  -- vs Beancount ±1bp

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Primary Key
    PRIMARY KEY (portfolio_id, asof_date, pricing_pack_id)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable(
    'portfolio_metrics',
    'asof_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_portfolio_metrics_portfolio ON portfolio_metrics(portfolio_id, asof_date DESC);
CREATE INDEX idx_portfolio_metrics_pack ON portfolio_metrics(pricing_pack_id);
CREATE INDEX idx_portfolio_metrics_date ON portfolio_metrics(asof_date DESC);

-- Compression (for old data)
ALTER TABLE portfolio_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'portfolio_id'
);

-- Add compression policy (compress data older than 90 days)
SELECT add_compression_policy('portfolio_metrics', INTERVAL '90 days');

-- Comments
COMMENT ON TABLE portfolio_metrics IS 'Time-series portfolio metrics (TWR, MWR, vol, Sharpe, etc.)';
COMMENT ON COLUMN portfolio_metrics.twr_1d IS 'Daily time-weighted return (eliminates cash flow impact)';
COMMENT ON COLUMN portfolio_metrics.mwr_ytd IS 'Money-weighted return (IRR, includes cash flow impact)';
COMMENT ON COLUMN portfolio_metrics.reconciliation_error_bps IS 'Error vs Beancount ledger (must be ≤1bp)';


-- ============================================================================
-- currency_attribution (Currency Return Decomposition)
-- ============================================================================

DROP TABLE IF EXISTS currency_attribution CASCADE;

CREATE TABLE currency_attribution (
    -- Identity
    portfolio_id UUID NOT NULL,
    asof_date DATE NOT NULL,
    pricing_pack_id TEXT NOT NULL REFERENCES pricing_packs(id),

    -- Attribution Components
    local_return NUMERIC(12, 8) NOT NULL,  -- Price return in local currency
    fx_return NUMERIC(12, 8) NOT NULL,     -- FX return (currency movement)
    interaction_return NUMERIC(12, 8) NOT NULL,  -- Cross-term (local * fx)

    -- Validation
    total_return NUMERIC(12, 8) NOT NULL,  -- Sum of components
    base_return_actual NUMERIC(12, 8) NOT NULL,  -- Actual base currency return
    error_bps NUMERIC(10, 4),  -- Difference in basis points (must be ≤0.1bp)

    -- Breakdown by Currency
    attribution_by_currency JSONB,  -- {"USD": {"local": 0.01, "fx": -0.005}, "EUR": {...}}

    -- Metadata
    base_currency TEXT NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Primary Key
    PRIMARY KEY (portfolio_id, asof_date, pricing_pack_id),

    -- Constraint: Attribution identity must hold
    CONSTRAINT chk_currency_attribution_identity
        CHECK (error_bps IS NULL OR error_bps <= 0.1)
);

-- Convert to hypertable
SELECT create_hypertable(
    'currency_attribution',
    'asof_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_currency_attribution_portfolio ON currency_attribution(portfolio_id, asof_date DESC);
CREATE INDEX idx_currency_attribution_pack ON currency_attribution(pricing_pack_id);

-- Comments
COMMENT ON TABLE currency_attribution IS 'Currency return decomposition (local + FX + interaction)';
COMMENT ON COLUMN currency_attribution.local_return IS 'Return from price changes in local currency';
COMMENT ON COLUMN currency_attribution.fx_return IS 'Return from currency movements';
COMMENT ON COLUMN currency_attribution.interaction_return IS 'Cross-term: local_return * fx_return';
COMMENT ON COLUMN currency_attribution.error_bps IS 'Attribution identity error (must be ≤0.1bp)';


-- ============================================================================
-- factor_exposures (Factor Risk Decomposition)
-- ============================================================================

DROP TABLE IF EXISTS factor_exposures CASCADE;

CREATE TABLE factor_exposures (
    -- Identity
    portfolio_id UUID NOT NULL,
    asof_date DATE NOT NULL,
    pricing_pack_id TEXT NOT NULL REFERENCES pricing_packs(id),

    -- Factor Betas (Dalio Framework)
    beta_real_rate NUMERIC(12, 8),  -- Sensitivity to real rates
    beta_inflation NUMERIC(12, 8),  -- Sensitivity to inflation
    beta_credit NUMERIC(12, 8),     -- Sensitivity to credit spreads
    beta_fx NUMERIC(12, 8),         -- Sensitivity to USD strength

    -- Traditional Factors
    beta_market NUMERIC(12, 8),  -- Market beta (vs benchmark)
    beta_size NUMERIC(12, 8),    -- Size factor (SMB)
    beta_value NUMERIC(12, 8),   -- Value factor (HML)
    beta_momentum NUMERIC(12, 8),  -- Momentum factor

    -- Variance Decomposition
    var_factor NUMERIC(12, 8),    -- Variance explained by factors
    var_idiosyncratic NUMERIC(12, 8),  -- Unexplained variance
    r_squared NUMERIC(5, 4),      -- Model fit

    -- Factor Contributions to Return
    factor_contributions JSONB,  -- {"real_rate": 0.002, "inflation": -0.001, ...}

    -- Metadata
    estimation_window_days INTEGER,  -- Rolling window for beta estimation
    benchmark_id TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Primary Key
    PRIMARY KEY (portfolio_id, asof_date, pricing_pack_id)
);

-- Convert to hypertable
SELECT create_hypertable(
    'factor_exposures',
    'asof_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_factor_exposures_portfolio ON factor_exposures(portfolio_id, asof_date DESC);
CREATE INDEX idx_factor_exposures_pack ON factor_exposures(pricing_pack_id);

-- Comments
COMMENT ON TABLE factor_exposures IS 'Portfolio factor exposures and risk decomposition';
COMMENT ON COLUMN factor_exposures.beta_real_rate IS 'Sensitivity to real interest rates (Dalio framework)';
COMMENT ON COLUMN factor_exposures.var_factor IS 'Variance explained by systematic factors';
COMMENT ON COLUMN factor_exposures.var_idiosyncratic IS 'Variance from stock-specific risk';


-- ============================================================================
-- Continuous Aggregates (Rolling Metrics)
-- ============================================================================

-- 30-Day Rolling Volatility
DROP MATERIALIZED VIEW IF EXISTS portfolio_metrics_30d_rolling CASCADE;

CREATE MATERIALIZED VIEW portfolio_metrics_30d_rolling
WITH (timescaledb.continuous) AS
SELECT
    portfolio_id,
    time_bucket('1 day', asof_date) AS day,
    AVG(twr_1d) AS avg_return_30d,
    STDDEV(twr_1d) * SQRT(252) AS volatility_30d_realized,
    MAX(portfolio_value_base) AS peak_value_30d,
    (MAX(portfolio_value_base) - MIN(portfolio_value_base)) / MAX(portfolio_value_base) AS drawdown_30d
FROM portfolio_metrics
GROUP BY portfolio_id, time_bucket('1 day', asof_date);

-- Refresh policy: every hour
SELECT add_continuous_aggregate_policy('portfolio_metrics_30d_rolling',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

COMMENT ON MATERIALIZED VIEW portfolio_metrics_30d_rolling IS 'Rolling 30-day metrics (volatility, avg return, drawdown)';


-- 60-Day Rolling Volatility
DROP MATERIALIZED VIEW IF EXISTS portfolio_metrics_60d_rolling CASCADE;

CREATE MATERIALIZED VIEW portfolio_metrics_60d_rolling
WITH (timescaledb.continuous) AS
SELECT
    portfolio_id,
    time_bucket('1 day', asof_date) AS day,
    AVG(twr_1d) AS avg_return_60d,
    STDDEV(twr_1d) * SQRT(252) AS volatility_60d_realized,
    MAX(portfolio_value_base) AS peak_value_60d
FROM portfolio_metrics
GROUP BY portfolio_id, time_bucket('1 day', asof_date);

-- Refresh policy: every 6 hours
SELECT add_continuous_aggregate_policy('portfolio_metrics_60d_rolling',
    start_offset => INTERVAL '2 months',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '6 hours');


-- 90-Day Rolling Sharpe Ratio
DROP MATERIALIZED VIEW IF EXISTS portfolio_metrics_90d_sharpe CASCADE;

CREATE MATERIALIZED VIEW portfolio_metrics_90d_sharpe
WITH (timescaledb.continuous) AS
SELECT
    portfolio_id,
    time_bucket('1 day', asof_date) AS day,
    AVG(twr_1d) AS avg_return_90d,
    STDDEV(twr_1d) AS stddev_return_90d,
    (AVG(twr_1d) - 0.0001) / NULLIF(STDDEV(twr_1d), 0) * SQRT(252) AS sharpe_90d_realized  -- Assuming 1bp daily risk-free rate
FROM portfolio_metrics
GROUP BY portfolio_id, time_bucket('1 day', asof_date);

-- Refresh policy: daily
SELECT add_continuous_aggregate_policy('portfolio_metrics_90d_sharpe',
    start_offset => INTERVAL '3 months',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 day');


-- 1-Year Rolling Beta
DROP MATERIALIZED VIEW IF EXISTS portfolio_metrics_1y_beta CASCADE;

CREATE MATERIALIZED VIEW portfolio_metrics_1y_beta
WITH (timescaledb.continuous) AS
SELECT
    portfolio_id,
    time_bucket('1 day', asof_date) AS day,
    AVG(beta_1y) AS avg_beta_1y,
    AVG(alpha_1y) AS avg_alpha_1y,
    AVG(tracking_error_1y) AS avg_te_1y
FROM portfolio_metrics
WHERE beta_1y IS NOT NULL
GROUP BY portfolio_id, time_bucket('1 day', asof_date);

-- Refresh policy: daily
SELECT add_continuous_aggregate_policy('portfolio_metrics_1y_beta',
    start_offset => INTERVAL '1 year',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 day');


-- ============================================================================
-- Sample Data (for development)
-- ============================================================================

-- Insert sample metrics
INSERT INTO portfolio_metrics (
    portfolio_id,
    asof_date,
    pricing_pack_id,
    twr_1d,
    twr_ytd,
    volatility_30d,
    sharpe_30d,
    portfolio_value_base,
    base_currency
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    '2025-10-21',
    'PP_2025-10-21',
    0.0012,  -- 12bp daily return
    0.0850,  -- 8.5% YTD
    0.1520,  -- 15.2% annualized vol
    0.5592,  -- Sharpe ratio
    1000000.00,  -- $1M portfolio
    'CAD'
);

-- Insert sample currency attribution
INSERT INTO currency_attribution (
    portfolio_id,
    asof_date,
    pricing_pack_id,
    local_return,
    fx_return,
    interaction_return,
    total_return,
    base_return_actual,
    error_bps,
    base_currency
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    '2025-10-21',
    'PP_2025-10-21',
    0.0015,  -- 15bp local return
    -0.0003,  -- -3bp FX return
    -0.0000045,  -- Interaction
    0.0011955,  -- Total
    0.0012,  -- Actual
    0.045,  -- 0.045bp error (well within ±0.1bp)
    'CAD'
);

-- Insert sample factor exposures
INSERT INTO factor_exposures (
    portfolio_id,
    asof_date,
    pricing_pack_id,
    beta_real_rate,
    beta_inflation,
    beta_credit,
    beta_market,
    r_squared,
    estimation_window_days
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    '2025-10-21',
    'PP_2025-10-21',
    0.35,  -- Positive real rate sensitivity
    -0.12,  -- Negative inflation sensitivity
    0.08,  -- Small credit sensitivity
    0.85,  -- 0.85 market beta
    0.72,  -- 72% variance explained
    252  -- 1-year estimation window
);


-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify hypertables
SELECT
    hypertable_schema,
    hypertable_name,
    num_chunks,
    compression_enabled
FROM timescaledb_information.hypertables
WHERE hypertable_name IN ('portfolio_metrics', 'currency_attribution', 'factor_exposures');

-- Verify continuous aggregates
SELECT
    view_name,
    materialization_hypertable_name,
    compression_enabled
FROM timescaledb_information.continuous_aggregates
ORDER BY view_name;

-- Verify sample data
SELECT 'portfolio_metrics' AS table_name, COUNT(*) AS row_count FROM portfolio_metrics
UNION ALL
SELECT 'currency_attribution', COUNT(*) FROM currency_attribution
UNION ALL
SELECT 'factor_exposures', COUNT(*) FROM factor_exposures;

SELECT 'Schema created successfully' AS status;
