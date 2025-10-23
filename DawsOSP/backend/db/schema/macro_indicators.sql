-- Macro Indicators Schema
-- Purpose: Store macro economic indicators and regime history (Sprint 3 Week 5)
-- Updated: 2025-10-22
-- Priority: P1 (Sprint 3)

-- ============================================================================
-- CONTEXT
-- ============================================================================
-- This schema stores macro economic indicators fetched from FRED API and
-- tracks historical regime classifications for the macro regime detection
-- system (5 regimes: Early/Mid/Late Expansion, Early/Deep Contraction).
--
-- Data sources:
-- - FRED API (Federal Reserve Economic Data)
-- - T10Y2Y (10Y-2Y Treasury spread)
-- - UNRATE (Unemployment rate)
-- - CPIAUCSL (Consumer Price Index)
-- - GDP (Gross Domestic Product)
-- - And other macro indicators
-- ============================================================================

-- ============================================================================
-- 1. MACRO_INDICATORS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS macro_indicators (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Indicator identification
    indicator_id TEXT NOT NULL,  -- FRED series ID (e.g., "T10Y2Y", "UNRATE", "CPIAUCSL")
    indicator_name TEXT NOT NULL,  -- Human-readable name

    -- Data
    date DATE NOT NULL,
    value NUMERIC NOT NULL,

    -- Metadata
    units TEXT,  -- e.g., "Percent", "Index 1982-1984=100", "Billions of Dollars"
    frequency TEXT,  -- "Daily", "Monthly", "Quarterly", "Annual"

    -- Source tracking
    source TEXT DEFAULT 'FRED',  -- Data source
    last_updated TIMESTAMPTZ,  -- When FRED last updated this data point

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_macro_indicators_indicator_id ON macro_indicators(indicator_id);
CREATE INDEX idx_macro_indicators_date ON macro_indicators(date DESC);
CREATE INDEX idx_macro_indicators_indicator_date ON macro_indicators(indicator_id, date DESC);

-- Unique constraint: one value per indicator per date
CREATE UNIQUE INDEX uq_macro_indicators_indicator_date
    ON macro_indicators(indicator_id, date);

-- Comments
COMMENT ON TABLE macro_indicators IS 'Macro economic indicators from FRED and other sources';
COMMENT ON COLUMN macro_indicators.indicator_id IS 'FRED series ID (e.g., T10Y2Y, UNRATE)';
COMMENT ON COLUMN macro_indicators.value IS 'Indicator value at this date';
COMMENT ON COLUMN macro_indicators.frequency IS 'Data frequency (Daily, Monthly, Quarterly, Annual)';

-- ============================================================================
-- 2. REGIME_HISTORY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS regime_history (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Regime classification
    date DATE NOT NULL,
    regime TEXT NOT NULL CHECK (
        regime IN (
            'EARLY_EXPANSION',
            'MID_EXPANSION',
            'LATE_EXPANSION',
            'EARLY_CONTRACTION',
            'DEEP_CONTRACTION'
        )
    ),

    -- Confidence score (0-1)
    confidence NUMERIC NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

    -- Input indicators (for explainability)
    indicators_json JSONB NOT NULL,  -- {"T10Y2Y": 0.5, "UNRATE": 3.7, "CPIAUCSL_yoy": 2.4}

    -- Z-scores (normalized indicators)
    zscores_json JSONB NOT NULL,  -- {"T10Y2Y_z": -0.5, "UNRATE_z": 1.2, "CPIAUCSL_yoy_z": 0.3}

    -- Regime scoring (for each regime, what was its score)
    regime_scores_json JSONB NOT NULL,  -- {"EARLY_EXPANSION": 0.2, "MID_EXPANSION": 0.7, ...}

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_regime_history_date ON regime_history(date DESC);
CREATE INDEX idx_regime_history_regime ON regime_history(regime);

-- Unique constraint: one regime classification per date
CREATE UNIQUE INDEX uq_regime_history_date
    ON regime_history(date);

-- Comments
COMMENT ON TABLE regime_history IS 'Historical macro regime classifications (5 regimes)';
COMMENT ON COLUMN regime_history.regime IS 'Regime: EARLY_EXPANSION, MID_EXPANSION, LATE_EXPANSION, EARLY_CONTRACTION, DEEP_CONTRACTION';
COMMENT ON COLUMN regime_history.confidence IS 'Confidence score for this regime classification (0-1)';
COMMENT ON COLUMN regime_history.indicators_json IS 'Raw indicator values used for classification';
COMMENT ON COLUMN regime_history.zscores_json IS 'Z-score normalized indicators';
COMMENT ON COLUMN regime_history.regime_scores_json IS 'Score for each regime (highest wins)';

-- ============================================================================
-- 3. CYCLE_PHASES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS cycle_phases (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Cycle identification
    cycle_type TEXT NOT NULL CHECK (
        cycle_type IN ('STDC', 'LTDC', 'EMPIRE')
    ),
    date DATE NOT NULL,

    -- Phase classification
    phase TEXT NOT NULL,  -- Phase name (varies by cycle type)
    phase_number INT NOT NULL,  -- Phase position in cycle (1-N)

    -- Composite score
    composite_score NUMERIC NOT NULL,  -- Weighted composite of indicators

    -- Input indicators (for explainability)
    indicators_json JSONB NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_cycle_phases_cycle_type ON cycle_phases(cycle_type);
CREATE INDEX idx_cycle_phases_date ON cycle_phases(date DESC);
CREATE INDEX idx_cycle_phases_cycle_date ON cycle_phases(cycle_type, date DESC);

-- Unique constraint: one phase per cycle type per date
CREATE UNIQUE INDEX uq_cycle_phases_cycle_date
    ON cycle_phases(cycle_type, date);

-- Comments
COMMENT ON TABLE cycle_phases IS 'Macro cycle phase tracking (STDC, LTDC, Empire)';
COMMENT ON COLUMN cycle_phases.cycle_type IS 'STDC (Short-Term Debt Cycle), LTDC (Long-Term Debt Cycle), EMPIRE';
COMMENT ON COLUMN cycle_phases.phase IS 'Phase name (varies by cycle type)';
COMMENT ON COLUMN cycle_phases.composite_score IS 'Weighted composite score of indicators';

-- ============================================================================
-- SAMPLE DATA (Development)
-- ============================================================================

-- Sample macro indicator (T10Y2Y)
-- INSERT INTO macro_indicators (
--     indicator_id,
--     indicator_name,
--     date,
--     value,
--     units,
--     frequency,
--     source
-- ) VALUES (
--     'T10Y2Y',
--     '10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity',
--     '2025-10-21',
--     0.52,
--     'Percent',
--     'Daily',
--     'FRED'
-- );

-- Sample regime classification
-- INSERT INTO regime_history (
--     date,
--     regime,
--     confidence,
--     indicators_json,
--     zscores_json,
--     regime_scores_json
-- ) VALUES (
--     '2025-10-21',
--     'MID_EXPANSION',
--     0.85,
--     '{"T10Y2Y": 0.52, "UNRATE": 3.7, "CPIAUCSL_yoy": 2.4}'::jsonb,
--     '{"T10Y2Y_z": 0.3, "UNRATE_z": -0.5, "CPIAUCSL_yoy_z": 0.1}'::jsonb,
--     '{"EARLY_EXPANSION": 0.1, "MID_EXPANSION": 0.85, "LATE_EXPANSION": 0.05, "EARLY_CONTRACTION": 0.0, "DEEP_CONTRACTION": 0.0}'::jsonb
-- );

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'Macro indicators schema created successfully' AS status;

SELECT COUNT(*) AS macro_indicators_count FROM macro_indicators;
SELECT COUNT(*) AS regime_history_count FROM regime_history;
SELECT COUNT(*) AS cycle_phases_count FROM cycle_phases;

-- Verify indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('macro_indicators', 'regime_history', 'cycle_phases')
ORDER BY tablename, indexname;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. FRED API rate limit: 120 requests/minute
-- 2. Daily update job should fetch latest values for all tracked indicators
-- 3. Regime classification runs after indicators are updated
-- 4. Z-score normalization uses 252-day rolling window (1 trading year)
-- 5. Regime scores are computed for all 5 regimes, highest wins
-- 6. Confidence = (max_score - second_max_score) / max_score
-- ============================================================================
