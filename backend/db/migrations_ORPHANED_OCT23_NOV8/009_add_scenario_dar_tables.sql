-- Migration: Add Scenario and DaR Tables
-- Purpose: Enable scenario stress testing and Drawdown at Risk tracking
-- Date: 2025-10-23
-- Priority: P0 (Required for macro risk management)

-- ============================================================================
-- CONTEXT
-- ============================================================================
-- This migration adds tables for:
-- 1. scenario_shocks: Pre-defined and custom scenario shock library
-- 2. position_factor_betas: Factor exposures for positions (for scenario analysis)
-- 3. dar_history: Historical DaR (Drawdown at Risk) calculations
-- 4. scenario_results: Historical scenario stress test results
--
-- These tables support:
-- - Scenario stress testing (apply macro shocks to portfolio)
-- - Regime-conditioned DaR calculation (Monte Carlo)
-- - Historical scenario P&L tracking
-- - Factor exposure tracking
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. SCENARIO_SHOCKS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS scenario_shocks (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Shock identification
    shock_type TEXT NOT NULL UNIQUE,  -- e.g., "rates_up", "usd_down", "credit_spread_widening"
    shock_name TEXT NOT NULL,  -- Human-readable name
    shock_description TEXT,  -- Detailed description

    -- Factor shocks (in basis points or decimal)
    real_rates_bps NUMERIC DEFAULT 0,  -- Real rate shock (basis points)
    inflation_bps NUMERIC DEFAULT 0,  -- Inflation shock (basis points)
    credit_spread_bps NUMERIC DEFAULT 0,  -- Credit spread shock (basis points)
    usd_pct NUMERIC DEFAULT 0,  -- USD appreciation/depreciation (decimal, e.g., 0.05 = 5%)
    equity_pct NUMERIC DEFAULT 0,  -- Equity shock (decimal, e.g., -0.10 = -10%)
    commodity_pct NUMERIC DEFAULT 0,  -- Commodity shock (decimal)
    volatility_pct NUMERIC DEFAULT 0,  -- Volatility shock (decimal)

    -- Metadata
    is_custom BOOLEAN DEFAULT FALSE,  -- User-defined vs pre-defined
    created_by UUID,  -- User who created (if custom)

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_scenario_shocks_shock_type ON scenario_shocks(shock_type);
CREATE INDEX idx_scenario_shocks_is_custom ON scenario_shocks(is_custom);

-- Comments
COMMENT ON TABLE scenario_shocks IS 'Library of scenario shocks for stress testing';
COMMENT ON COLUMN scenario_shocks.shock_type IS 'Unique shock type identifier';
COMMENT ON COLUMN scenario_shocks.real_rates_bps IS 'Real rate shock in basis points';
COMMENT ON COLUMN scenario_shocks.usd_pct IS 'USD shock as decimal (0.05 = 5% appreciation)';
COMMENT ON COLUMN scenario_shocks.is_custom IS 'User-defined shock vs pre-defined library shock';

-- ============================================================================
-- 2. POSITION_FACTOR_BETAS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS position_factor_betas (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Position identification
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    security_id UUID NOT NULL,

    -- As-of date
    asof_date DATE NOT NULL,

    -- Factor exposures (betas)
    real_rate_beta NUMERIC,  -- Sensitivity to real rates (duration-like)
    inflation_beta NUMERIC,  -- Sensitivity to inflation
    credit_beta NUMERIC,  -- Sensitivity to credit spreads
    usd_beta NUMERIC,  -- Sensitivity to USD movements
    equity_beta NUMERIC,  -- Traditional equity beta
    commodity_beta NUMERIC,  -- Commodity exposure
    volatility_beta NUMERIC,  -- Volatility exposure

    -- Metadata
    methodology TEXT,  -- How betas were computed (e.g., "rolling_regression_252d", "fundamental")
    r_squared NUMERIC,  -- Goodness of fit (if regression-based)

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_position_factor_betas_portfolio_id ON position_factor_betas(portfolio_id);
CREATE INDEX idx_position_factor_betas_symbol ON position_factor_betas(symbol);
CREATE INDEX idx_position_factor_betas_asof_date ON position_factor_betas(asof_date DESC);
CREATE INDEX idx_position_factor_betas_portfolio_date ON position_factor_betas(portfolio_id, asof_date DESC);

-- Unique constraint: one beta record per position per date
CREATE UNIQUE INDEX uq_position_factor_betas_portfolio_symbol_date
    ON position_factor_betas(portfolio_id, symbol, asof_date);

-- Comments
COMMENT ON TABLE position_factor_betas IS 'Factor exposures (betas) for portfolio positions';
COMMENT ON COLUMN position_factor_betas.real_rate_beta IS 'Sensitivity to real rate changes (similar to duration)';
COMMENT ON COLUMN position_factor_betas.equity_beta IS 'Traditional market beta (equity exposure)';
COMMENT ON COLUMN position_factor_betas.methodology IS 'Beta calculation method (rolling_regression_252d, fundamental, etc.)';

-- ============================================================================
-- 3. DAR_HISTORY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS dar_history (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Portfolio identification
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,

    -- Calculation date
    asof_date DATE NOT NULL,

    -- Regime context
    regime TEXT NOT NULL CHECK (
        regime IN (
            'EARLY_EXPANSION',
            'MID_EXPANSION',
            'LATE_EXPANSION',
            'EARLY_CONTRACTION',
            'DEEP_CONTRACTION'
        )
    ),

    -- DaR parameters
    confidence NUMERIC NOT NULL CHECK (confidence >= 0 AND confidence <= 1),  -- e.g., 0.95 for 95%
    horizon_days INT NOT NULL,  -- e.g., 30 for 30-day DaR
    num_simulations INT NOT NULL,  -- e.g., 10000 for Monte Carlo

    -- DaR results
    dar NUMERIC NOT NULL,  -- Drawdown at Risk in base currency
    dar_pct NUMERIC NOT NULL,  -- DaR as % of NAV

    -- Distribution statistics
    mean_drawdown NUMERIC NOT NULL,
    median_drawdown NUMERIC NOT NULL,
    max_drawdown NUMERIC NOT NULL,  -- Worst simulated drawdown

    -- Portfolio state
    current_nav NUMERIC NOT NULL,

    -- Provenance
    pricing_pack_id TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_dar_history_portfolio_id ON dar_history(portfolio_id);
CREATE INDEX idx_dar_history_asof_date ON dar_history(asof_date DESC);
CREATE INDEX idx_dar_history_regime ON dar_history(regime);
CREATE INDEX idx_dar_history_portfolio_date ON dar_history(portfolio_id, asof_date DESC);
CREATE INDEX idx_dar_history_user_id ON dar_history(user_id);

-- Unique constraint: one DaR calculation per portfolio per date per regime
CREATE UNIQUE INDEX uq_dar_history_portfolio_date_regime
    ON dar_history(portfolio_id, asof_date, regime);

-- Comments
COMMENT ON TABLE dar_history IS 'Historical Drawdown at Risk (DaR) calculations';
COMMENT ON COLUMN dar_history.regime IS 'Regime DaR was conditioned on';
COMMENT ON COLUMN dar_history.confidence IS 'Confidence level (0.95 = 95th percentile)';
COMMENT ON COLUMN dar_history.dar IS 'Drawdown at Risk in portfolio base currency';
COMMENT ON COLUMN dar_history.dar_pct IS 'DaR as % of NAV';
COMMENT ON COLUMN dar_history.num_simulations IS 'Number of Monte Carlo simulations run';

-- ============================================================================
-- 4. SCENARIO_RESULTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS scenario_results (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Portfolio identification
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,

    -- Scenario identification
    shock_type TEXT NOT NULL,  -- References scenario_shocks.shock_type
    asof_date DATE NOT NULL,

    -- Results
    total_delta_pnl NUMERIC NOT NULL,  -- Total portfolio delta P&L
    total_delta_pnl_pct NUMERIC NOT NULL,  -- Delta P&L as % of NAV

    -- Position-level results (top winners/losers)
    winners_json JSONB,  -- [{symbol, delta_pnl, reason}, ...]
    losers_json JSONB,  -- [{symbol, delta_pnl, reason}, ...]

    -- Hedge suggestions
    suggested_hedges_json JSONB,  -- [{hedge, rationale}, ...]

    -- Shock definition used
    shock_definition_json JSONB,  -- {real_rates_bps: 100, usd_pct: 0.05, ...}

    -- Provenance
    pricing_pack_id TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_scenario_results_portfolio_id ON scenario_results(portfolio_id);
CREATE INDEX idx_scenario_results_shock_type ON scenario_results(shock_type);
CREATE INDEX idx_scenario_results_asof_date ON scenario_results(asof_date DESC);
CREATE INDEX idx_scenario_results_portfolio_date ON scenario_results(portfolio_id, asof_date DESC);
CREATE INDEX idx_scenario_results_user_id ON scenario_results(user_id);

-- Unique constraint: one scenario result per portfolio per shock type per date
CREATE UNIQUE INDEX uq_scenario_results_portfolio_shock_date
    ON scenario_results(portfolio_id, shock_type, asof_date);

-- Comments
COMMENT ON TABLE scenario_results IS 'Historical scenario stress test results';
COMMENT ON COLUMN scenario_results.shock_type IS 'Scenario shock type applied';
COMMENT ON COLUMN scenario_results.total_delta_pnl IS 'Total portfolio delta P&L from shock';
COMMENT ON COLUMN scenario_results.winners_json IS 'Top 5 winners (positive delta P&L)';
COMMENT ON COLUMN scenario_results.losers_json IS 'Top 5 losers (negative delta P&L)';

-- ============================================================================
-- 5. INSERT PRE-DEFINED SCENARIO SHOCKS
-- ============================================================================

-- Rates up (+100bp)
INSERT INTO scenario_shocks (shock_type, shock_name, shock_description, real_rates_bps, is_custom)
VALUES (
    'rates_up',
    'Rates Up +100bp',
    'Real rates increase by 100 basis points (1%)',
    100,
    FALSE
) ON CONFLICT (shock_type) DO NOTHING;

-- Rates down (-100bp)
INSERT INTO scenario_shocks (shock_type, shock_name, shock_description, real_rates_bps, is_custom)
VALUES (
    'rates_down',
    'Rates Down -100bp',
    'Real rates decrease by 100 basis points (1%)',
    -100,
    FALSE
) ON CONFLICT (shock_type) DO NOTHING;

-- USD up (+5%)
INSERT INTO scenario_shocks (shock_type, shock_name, shock_description, usd_pct, is_custom)
VALUES (
    'usd_up',
    'USD Up +5%',
    'USD appreciates by 5% against major currencies',
    0.05,
    FALSE
) ON CONFLICT (shock_type) DO NOTHING;

-- USD down (-5%)
INSERT INTO scenario_shocks (shock_type, shock_name, shock_description, usd_pct, is_custom)
VALUES (
    'usd_down',
    'USD Down -5%',
    'USD depreciates by 5% against major currencies',
    -0.05,
    FALSE
) ON CONFLICT (shock_type) DO NOTHING;

-- CPI surprise (+1%)
INSERT INTO scenario_shocks (shock_type, shock_name, shock_description, inflation_bps, is_custom)
VALUES (
    'cpi_surprise',
    'CPI Surprise +1%',
    'Inflation surprise of +1% (100bp)',
    100,
    FALSE
) ON CONFLICT (shock_type) DO NOTHING;

-- Credit spread widening (+50bp)
INSERT INTO scenario_shocks (shock_type, shock_name, shock_description, credit_spread_bps, is_custom)
VALUES (
    'credit_spread_widening',
    'Credit Spreads Widen +50bp',
    'Corporate credit spreads widen by 50 basis points',
    50,
    FALSE
) ON CONFLICT (shock_type) DO NOTHING;

-- Credit spread tightening (-50bp)
INSERT INTO scenario_shocks (shock_type, shock_name, shock_description, credit_spread_bps, is_custom)
VALUES (
    'credit_spread_tightening',
    'Credit Spreads Tighten -50bp',
    'Corporate credit spreads tighten by 50 basis points',
    -50,
    FALSE
) ON CONFLICT (shock_type) DO NOTHING;

-- Equity selloff (-10%)
INSERT INTO scenario_shocks (shock_type, shock_name, shock_description, equity_pct, is_custom)
VALUES (
    'equity_selloff',
    'Equity Selloff -10%',
    'Broad equity market selloff of 10%',
    -0.10,
    FALSE
) ON CONFLICT (shock_type) DO NOTHING;

-- Equity rally (+10%)
INSERT INTO scenario_shocks (shock_type, shock_name, shock_description, equity_pct, is_custom)
VALUES (
    'equity_rally',
    'Equity Rally +10%',
    'Broad equity market rally of 10%',
    0.10,
    FALSE
) ON CONFLICT (shock_type) DO NOTHING;

-- ============================================================================
-- 6. UPDATE TRIGGERS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_scenario_shocks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_scenario_shocks_updated_at
    BEFORE UPDATE ON scenario_shocks
    FOR EACH ROW
    EXECUTE FUNCTION update_scenario_shocks_updated_at();

-- ============================================================================
-- 7. VERIFICATION
-- ============================================================================

-- Verify tables exist
SELECT
    table_name,
    (
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = t.table_name
    ) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('scenario_shocks', 'position_factor_betas', 'dar_history', 'scenario_results')
ORDER BY table_name;

-- Verify scenario shocks inserted
SELECT
    shock_type,
    shock_name,
    CASE
        WHEN real_rates_bps <> 0 THEN CONCAT(real_rates_bps::text, ' bps')
        WHEN usd_pct <> 0 THEN CONCAT((usd_pct * 100)::text, '%')
        WHEN inflation_bps <> 0 THEN CONCAT(inflation_bps::text, ' bps')
        WHEN credit_spread_bps <> 0 THEN CONCAT(credit_spread_bps::text, ' bps')
        WHEN equity_pct <> 0 THEN CONCAT((equity_pct * 100)::text, '%')
        ELSE 'No shock'
    END AS shock_magnitude
FROM scenario_shocks
ORDER BY shock_type;

-- Verify indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('scenario_shocks', 'position_factor_betas', 'dar_history', 'scenario_results')
ORDER BY tablename, indexname;

COMMIT;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. scenario_shocks contains pre-defined shocks and user-defined custom shocks
-- 2. position_factor_betas are computed nightly via jobs/compute_factor_betas.py
-- 3. dar_history is populated when users request DaR calculations via API
-- 4. scenario_results are stored when users run scenario stress tests
-- 5. All tables are user-scoped (via user_id or portfolio_id → user_id)
-- 6. RLS policies will be added in a future migration if needed
-- ============================================================================

SELECT 'Migration 009: Scenario and DaR tables added successfully' AS status;
