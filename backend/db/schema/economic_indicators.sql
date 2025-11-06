-- Economic Indicators Table
-- Purpose: Store time-series economic indicators from FRED for factor analysis
-- Updated: 2025-01-14
-- Priority: P0 (Critical for factor analysis)

CREATE TABLE IF NOT EXISTS economic_indicators (
    series_id VARCHAR(20) NOT NULL,
    asof_date DATE NOT NULL,
    value NUMERIC(20, 8) NOT NULL,
    unit VARCHAR(20),
    source VARCHAR(50) DEFAULT 'FRED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (series_id, asof_date)
);

CREATE INDEX IF NOT EXISTS idx_economic_indicators_date 
    ON economic_indicators(asof_date DESC);

CREATE INDEX IF NOT EXISTS idx_economic_indicators_series 
    ON economic_indicators(series_id, asof_date DESC);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable(
    'economic_indicators',
    'asof_date',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 month'
);

COMMENT ON TABLE economic_indicators IS 
'Economic indicators from FRED for factor analysis. Series IDs: DFII10 (Real Rate), T10YIE (Inflation), BAMLC0A0CM (Credit), DTWEXBGS (USD), SP500 (Equity).';