-- Migration 020: Add Security Ratings Table
-- Created: 2025-11-08
-- Purpose: Store security quality ratings for alert conditions

-- Create security_ratings table
CREATE TABLE IF NOT EXISTS security_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    rating_type TEXT NOT NULL,  -- 'moat_strength', 'dividend_safety', 'quality', 'resilience'
    rating_value NUMERIC(5,2) NOT NULL CHECK (rating_value >= 0 AND rating_value <= 100),
    rating_score NUMERIC(5,2),  -- Normalized 0-100 score
    rating_grade TEXT,  -- 'A+', 'A', 'B+', 'B', 'C', 'D', 'F'
    components JSONB,  -- Detailed component scores
    metadata JSONB,  -- Additional metadata (source, confidence, etc.)
    source TEXT DEFAULT 'system',  -- 'system', 'manual', 'external'
    asof_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- When this rating should be refreshed
    UNIQUE(symbol, rating_type, asof_date)
);

-- Indexes for performance
CREATE INDEX idx_security_ratings_symbol ON security_ratings(symbol);
CREATE INDEX idx_security_ratings_portfolio ON security_ratings(portfolio_id);
CREATE INDEX idx_security_ratings_type ON security_ratings(rating_type);
CREATE INDEX idx_security_ratings_date ON security_ratings(asof_date DESC);
CREATE INDEX idx_security_ratings_symbol_type_date ON security_ratings(symbol, rating_type, asof_date DESC);

-- Comments for documentation
COMMENT ON TABLE security_ratings IS 
    'Store security quality ratings for various frameworks (moat strength, dividend safety, etc.)
     Used by alert system to trigger conditions based on rating changes.';

COMMENT ON COLUMN security_ratings.rating_value IS 
    'Raw rating value (0-100 scale)';

COMMENT ON COLUMN security_ratings.rating_score IS 
    'Normalized score for comparison across rating types';

COMMENT ON COLUMN security_ratings.rating_grade IS 
    'Letter grade representation (A+ through F)';

COMMENT ON COLUMN security_ratings.components IS 
    'Detailed breakdown of rating components as JSONB.
     Example: {"roe_consistency": 0.85, "gross_margin": 0.75, "debt_ratio": 0.90}';

COMMENT ON COLUMN security_ratings.metadata IS 
    'Additional metadata like data source, confidence level, calculation method version';

-- Row-Level Security policies
ALTER TABLE security_ratings ENABLE ROW LEVEL SECURITY;

-- Users can read their own portfolio's ratings or public ratings
CREATE POLICY security_ratings_read ON security_ratings
    FOR SELECT
    USING (
        portfolio_id IS NULL  -- Public ratings
        OR portfolio_id IN (
            SELECT id FROM portfolios 
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

-- Users can insert/update ratings for their own portfolios
CREATE POLICY security_ratings_write ON security_ratings
    FOR INSERT
    WITH CHECK (
        portfolio_id IN (
            SELECT id FROM portfolios 
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

CREATE POLICY security_ratings_update ON security_ratings
    FOR UPDATE
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios 
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

-- Users can delete their own ratings
CREATE POLICY security_ratings_delete ON security_ratings
    FOR DELETE
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios 
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON security_ratings TO dawsos_app;
GRANT USAGE ON SEQUENCE security_ratings_id_seq TO dawsos_app;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_security_ratings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_security_ratings_timestamp
    BEFORE UPDATE ON security_ratings
    FOR EACH ROW
    EXECUTE FUNCTION update_security_ratings_updated_at();