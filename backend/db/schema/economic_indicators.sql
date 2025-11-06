
-- Economic Indicators Table
-- Purpose: Store economic indicator data from FRED for factor analysis
-- Created: January 14, 2025 (Phase 3 - Field Name Refactor)

CREATE TABLE IF NOT EXISTS economic_indicators (
    series_id VARCHAR(20) NOT NULL,
    asof_date DATE NOT NULL,
    value NUMERIC(20, 8) NOT NULL,
    unit VARCHAR(20),
    source VARCHAR(50) DEFAULT 'FRED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (series_id, asof_date)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_economic_indicators_date 
    ON economic_indicators(asof_date DESC);

CREATE INDEX IF NOT EXISTS idx_economic_indicators_series 
    ON economic_indicators(series_id, asof_date DESC);

-- Convert to hypertable (TimescaleDB)
-- This will partition data by asof_date for efficient time-series queries
SELECT create_hypertable(
    'economic_indicators',
    'asof_date',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 month'
);

-- Add comment
COMMENT ON TABLE economic_indicators IS 
'Economic indicators from FRED for factor analysis. Series IDs: DFII10 (Real Rate), T10YIE (Inflation), BAMLC0A0CM (Credit), DTWEXBGS (USD), SP500 (Equity).';

COMMENT ON COLUMN economic_indicators.series_id IS 
'FRED series identifier (e.g., DFII10, T10YIE, BAMLC0A0CM, DTWEXBGS, SP500)';

COMMENT ON COLUMN economic_indicators.asof_date IS 
'As-of date for the indicator value';

COMMENT ON COLUMN economic_indicators.value IS 
'Indicator value (level, not return - returns calculated on-the-fly)';

