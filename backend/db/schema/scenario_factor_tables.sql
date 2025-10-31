-- Scenario and Factor Analysis Tables
-- Purpose: Support macro-aware scenario analysis and factor-based risk modeling
-- Updated: 2025-10-31
-- Priority: P0 (Critical for macro refactoring)

-- ============================================================================
-- position_factor_betas (Factor Sensitivities by Position)
-- ============================================================================

DROP TABLE IF EXISTS position_factor_betas CASCADE;

CREATE TABLE position_factor_betas (
    -- Identity
    portfolio_id UUID NOT NULL,
    security_id UUID NOT NULL,
    factor_name VARCHAR(50) NOT NULL,
    
    -- Factor Sensitivity
    beta NUMERIC(10, 4) NOT NULL,
    
    -- Metadata
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Primary Key
    PRIMARY KEY (portfolio_id, security_id, factor_name),
    
    -- Foreign Keys (assuming securities table exists)
    -- FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
    -- FOREIGN KEY (security_id) REFERENCES securities(id),
    
    -- Constraints
    CONSTRAINT chk_factor_name CHECK (
        factor_name IN (
            'real_rates',
            'inflation', 
            'credit_spreads',
            'fx_usd',
            'equity_market',
            'size',
            'value',
            'momentum',
            'volatility',
            'liquidity',
            'commodity',
            'duration',
            'convexity',
            'carry',
            'term_structure'
        )
    )
);

-- Indexes for performance
CREATE INDEX idx_position_factor_betas_portfolio ON position_factor_betas(portfolio_id);
CREATE INDEX idx_position_factor_betas_security ON position_factor_betas(security_id);
CREATE INDEX idx_position_factor_betas_factor ON position_factor_betas(factor_name);
CREATE INDEX idx_position_factor_betas_updated ON position_factor_betas(updated_at DESC);

-- Comments
COMMENT ON TABLE position_factor_betas IS 'Factor sensitivities (betas) for each position in portfolios';
COMMENT ON COLUMN position_factor_betas.portfolio_id IS 'UUID of the portfolio containing the position';
COMMENT ON COLUMN position_factor_betas.security_id IS 'UUID of the security/position';
COMMENT ON COLUMN position_factor_betas.factor_name IS 'Name of the risk factor (e.g., real_rates, inflation)';
COMMENT ON COLUMN position_factor_betas.beta IS 'Sensitivity to the factor (beta coefficient)';
COMMENT ON COLUMN position_factor_betas.updated_at IS 'Last update timestamp for this factor beta';


-- ============================================================================
-- scenario_shocks (Scenario Definitions and Shock Parameters)
-- ============================================================================

DROP TABLE IF EXISTS scenario_shocks CASCADE;

CREATE TABLE scenario_shocks (
    -- Identity
    scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_name VARCHAR(100) NOT NULL UNIQUE,
    
    -- Scenario Definition
    shock_definition JSONB NOT NULL,
    /* 
    Example shock_definition structure:
    {
        "description": "Money printing deleveraging scenario",
        "category": "deleveraging",
        "shocks": {
            "real_rates": -0.02,
            "inflation": 0.03,
            "credit_spreads": -0.005,
            "fx_usd": -0.05,
            "equity_market": 0.10,
            "commodity": 0.15
        },
        "regime_adjustments": {
            "LATE_EXPANSION": {
                "probability_multiplier": 2.0,
                "severity_multiplier": 1.5
            }
        },
        "cycle_adjustments": {
            "LTDC_BUBBLE": {
                "risk_multiplier": 1.8,
                "correlation_increase": 0.4
            }
        },
        "metadata": {
            "source": "Dalio Framework",
            "confidence": 0.75,
            "historical_frequency": 0.15,
            "expected_duration_months": 18
        }
    }
    */
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_shock_definition_structure CHECK (
        shock_definition ? 'description' AND
        shock_definition ? 'category' AND
        shock_definition ? 'shocks'
    )
);

-- Indexes
CREATE INDEX idx_scenario_shocks_name ON scenario_shocks(scenario_name);
CREATE INDEX idx_scenario_shocks_category ON scenario_shocks((shock_definition->>'category'));
CREATE INDEX idx_scenario_shocks_created ON scenario_shocks(created_at DESC);

-- GIN index for JSONB queries
CREATE INDEX idx_scenario_shocks_definition ON scenario_shocks USING GIN(shock_definition);

-- Comments
COMMENT ON TABLE scenario_shocks IS 'Scenario definitions with factor shocks for stress testing';
COMMENT ON COLUMN scenario_shocks.scenario_id IS 'Unique identifier for the scenario';
COMMENT ON COLUMN scenario_shocks.scenario_name IS 'Human-readable name for the scenario';
COMMENT ON COLUMN scenario_shocks.shock_definition IS 'JSONB containing shock parameters, regime adjustments, and metadata';


-- ============================================================================
-- Sample Data (for development and testing)
-- ============================================================================

-- Insert sample position factor betas
INSERT INTO position_factor_betas (
    portfolio_id,
    security_id,
    factor_name,
    beta
) VALUES 
    ('00000000-0000-0000-0000-000000000001'::UUID, '00000000-0000-0000-0000-000000000010'::UUID, 'real_rates', 0.35),
    ('00000000-0000-0000-0000-000000000001'::UUID, '00000000-0000-0000-0000-000000000010'::UUID, 'inflation', -0.12),
    ('00000000-0000-0000-0000-000000000001'::UUID, '00000000-0000-0000-0000-000000000010'::UUID, 'credit_spreads', 0.08),
    ('00000000-0000-0000-0000-000000000001'::UUID, '00000000-0000-0000-0000-000000000010'::UUID, 'equity_market', 0.85)
ON CONFLICT DO NOTHING;

-- Insert sample scenarios
INSERT INTO scenario_shocks (
    scenario_name,
    shock_definition
) VALUES 
(
    'Money Printing Deleveraging',
    '{
        "description": "Central banks print money to offset deflationary deleveraging",
        "category": "deleveraging",
        "shocks": {
            "real_rates": -0.025,
            "inflation": 0.04,
            "credit_spreads": -0.01,
            "fx_usd": -0.08,
            "equity_market": 0.15,
            "commodity": 0.20,
            "volatility": 0.25
        },
        "regime_adjustments": {
            "DEEP_CONTRACTION": {
                "probability_multiplier": 3.0,
                "severity_multiplier": 1.8
            },
            "LATE_EXPANSION": {
                "probability_multiplier": 1.5,
                "severity_multiplier": 1.3
            }
        },
        "cycle_adjustments": {
            "LTDC_DEPRESSION": {
                "risk_multiplier": 2.5,
                "correlation_increase": 0.6
            }
        },
        "metadata": {
            "source": "Dalio Framework",
            "confidence": 0.80,
            "historical_frequency": 0.12,
            "expected_duration_months": 24,
            "examples": ["2008-2009 QE", "2020 COVID response", "1930s reflation"]
        }
    }'
),
(
    'Austerity Deleveraging',
    '{
        "description": "Governments cut spending and raise taxes to reduce debt",
        "category": "deleveraging",
        "shocks": {
            "real_rates": 0.015,
            "inflation": -0.02,
            "credit_spreads": 0.025,
            "fx_usd": 0.05,
            "equity_market": -0.20,
            "commodity": -0.15,
            "volatility": 0.40
        },
        "regime_adjustments": {
            "DEEP_CONTRACTION": {
                "probability_multiplier": 2.0,
                "severity_multiplier": 2.0
            }
        },
        "cycle_adjustments": {
            "LTDC_DEBT_CRISIS": {
                "risk_multiplier": 2.2,
                "correlation_increase": 0.7
            }
        },
        "metadata": {
            "source": "Dalio Framework",
            "confidence": 0.75,
            "historical_frequency": 0.08,
            "expected_duration_months": 36,
            "examples": ["Greece 2010-2015", "UK 2010-2016", "Canada 1990s"]
        }
    }'
),
(
    'Default and Restructuring',
    '{
        "description": "Debt defaults and restructuring with credit crisis",
        "category": "deleveraging",
        "shocks": {
            "real_rates": 0.03,
            "inflation": -0.03,
            "credit_spreads": 0.08,
            "fx_usd": 0.10,
            "equity_market": -0.35,
            "commodity": -0.25,
            "volatility": 0.60,
            "liquidity": -0.50
        },
        "regime_adjustments": {
            "DEEP_CONTRACTION": {
                "probability_multiplier": 4.0,
                "severity_multiplier": 2.5
            }
        },
        "cycle_adjustments": {
            "LTDC_DEPRESSION": {
                "risk_multiplier": 3.0,
                "correlation_increase": 0.9
            },
            "EMPIRE_DECLINE": {
                "currency_risk": 2.0,
                "structural_risk_multiplier": 2.5
            }
        },
        "metadata": {
            "source": "Dalio Framework",
            "confidence": 0.70,
            "historical_frequency": 0.05,
            "expected_duration_months": 48,
            "examples": ["Argentina 2001", "Russia 1998", "Germany 1923", "US 1930s"]
        }
    }'
)
ON CONFLICT (scenario_name) DO NOTHING;


-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify tables were created
SELECT 
    table_name,
    (SELECT COUNT(*) FROM position_factor_betas) AS position_factor_betas_count,
    (SELECT COUNT(*) FROM scenario_shocks) AS scenario_shocks_count
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('position_factor_betas', 'scenario_shocks');

-- Verify sample data
SELECT 'position_factor_betas' AS table_name, COUNT(*) AS row_count FROM position_factor_betas
UNION ALL
SELECT 'scenario_shocks', COUNT(*) FROM scenario_shocks;

-- Show sample scenario
SELECT 
    scenario_name,
    shock_definition->>'description' AS description,
    shock_definition->>'category' AS category,
    jsonb_pretty(shock_definition->'shocks') AS shocks
FROM scenario_shocks
LIMIT 1;

SELECT 'Tables created successfully' AS status;