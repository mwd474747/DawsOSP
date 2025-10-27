-- Rating Rubrics Schema for Buffett Quality Framework
-- Created: 2025-10-26
-- Purpose: Store component weights and thresholds for quality ratings

-- Ratings rubrics table
CREATE TABLE IF NOT EXISTS rating_rubrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rating_type TEXT NOT NULL,  -- 'dividend_safety', 'moat_strength', 'resilience'
    method_version TEXT NOT NULL DEFAULT 'v1',
    overall_weights JSONB NOT NULL,  -- Component weights (must sum to 1.0)
    component_thresholds JSONB NOT NULL,  -- Scoring thresholds per component
    description TEXT,
    research_basis TEXT,  -- Documentation of why these weights were chosen
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(rating_type, method_version)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_rating_rubrics_type_version
    ON rating_rubrics(rating_type, method_version);

CREATE INDEX IF NOT EXISTS idx_rating_rubrics_type
    ON rating_rubrics(rating_type);

-- Comments for documentation
COMMENT ON TABLE rating_rubrics IS
    'Buffett quality scoring rubrics with component weights and thresholds.
     Weights are research-based, derived from Warren Buffett''s investment philosophy.';

COMMENT ON COLUMN rating_rubrics.overall_weights IS
    'Component weights as JSONB: {"component_name": weight, ...}.
     Must sum to 1.0. Example: {"roe_consistency": 0.35, "gross_margin": 0.30, ...}';

COMMENT ON COLUMN rating_rubrics.component_thresholds IS
    'Scoring thresholds for each component.
     Example: {"roe_consistency": [{"min": 0.20, "score": 10}, ...]}';

COMMENT ON COLUMN rating_rubrics.research_basis IS
    'Documentation explaining why these weights were chosen,
     with citations to Buffett''s writings or empirical research.';

-- Row-level security (users can read, only system can write)
ALTER TABLE rating_rubrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY rating_rubrics_read_all ON rating_rubrics
    FOR SELECT
    USING (true);

CREATE POLICY rating_rubrics_system_write ON rating_rubrics
    FOR ALL
    USING (current_setting('app.user_id', true)::uuid = '00000000-0000-0000-0000-000000000000');

-- Grant permissions
GRANT SELECT ON rating_rubrics TO dawsos_app;
GRANT INSERT, UPDATE ON rating_rubrics TO dawsos_app;  -- For seeding and updates
