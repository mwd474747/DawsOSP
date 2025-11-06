-- Migration 015: Add economic_indicators table
-- Created: January 14, 2025
-- Purpose: Support factor analysis with economic indicator data from FRED

-- Create table
CREATE TABLE IF NOT EXISTS economic_indicators (
    series_id VARCHAR(20) NOT NULL,
    asof_date DATE NOT NULL,
    value NUMERIC(20, 8) NOT NULL,
    unit VARCHAR(20),
    source VARCHAR(50) DEFAULT 'FRED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (series_id, asof_date)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_economic_indicators_date 
    ON economic_indicators(asof_date DESC);

CREATE INDEX IF NOT EXISTS idx_economic_indicators_series 
    ON economic_indicators(series_id, asof_date DESC);

-- Convert to hypertable (TimescaleDB) - if available
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable(
            'economic_indicators',
            'asof_date',
            if_not_exists => TRUE,
            chunk_time_interval => INTERVAL '1 month'
        );
    END IF;
END $$;

-- Add comment
COMMENT ON TABLE economic_indicators IS 
'Economic indicators from FRED for factor analysis. Series IDs: DFII10 (Real Rate), T10YIE (Inflation), BAMLC0A0CM (Credit), DTWEXBGS (USD), SP500 (Equity).';

-- Note: Data will be populated by data harvester agent
-- No seed data required for initial migration

