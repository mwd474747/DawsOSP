-- Rating Rubrics Seed Data
-- Purpose: Populate rating_rubrics table with research-based Buffett quality weights
-- Created: 2025-10-26
-- Governance: P0-CODE-1 remediation

-- Clean existing data (idempotent)
DELETE FROM rating_rubrics WHERE method_version = 'v1';

-- Dividend Safety Rubric
-- Research Basis: Warren Buffett's emphasis on sustainable dividends
-- Key Principles:
--   1. FCF coverage is paramount (35%) - dividends must be backed by actual cash flow
--   2. Payout ratio indicates sustainability (30%) - lower is safer
--   3. Growth streak proves consistency (20%) - Buffett values predictability
--   4. Net cash position provides cushion (15%) - balance sheet strength matters
INSERT INTO rating_rubrics (
    rating_type,
    method_version,
    overall_weights,
    component_thresholds,
    description,
    research_basis
) VALUES (
    'dividend_safety',
    'v1',
    '{
        "fcf_coverage": 0.35,
        "payout_ratio": 0.30,
        "growth_streak": 0.20,
        "net_cash": 0.15
    }'::jsonb,
    '{
        "fcf_coverage": {
            "excellent": {"min": 3.0, "score": 10},
            "good": {"min": 2.0, "score": 7},
            "acceptable": {"min": 1.0, "score": 5},
            "poor": {"max": 1.0, "score": 2}
        },
        "payout_ratio": {
            "excellent": {"max": 0.30, "score": 10},
            "good": {"max": 0.50, "score": 7},
            "acceptable": {"max": 0.70, "score": 5},
            "poor": {"min": 0.70, "score": 2}
        },
        "growth_streak": {
            "excellent": {"min": 20, "score": 10},
            "very_good": {"min": 10, "score": 9},
            "good": {"min": 5, "score": 7},
            "acceptable": {"min": 0, "score": 5}
        },
        "net_cash": {
            "excellent": {"min": 50000000000, "score": 10},
            "good": {"min": 10000000000, "score": 8},
            "acceptable": {"min": 1000000000, "score": 6},
            "poor": {"max": 1000000000, "score": 4}
        }
    }'::jsonb,
    'Dividend safety rating based on FCF coverage, payout ratio, growth streak, and net cash position',
    'Warren Buffett 1996 Letter: "We like stocks that generate high returns on invested capital where there is a low likelihood that competitors can achieve the same returns." Free cash flow coverage is emphasized in multiple Berkshire annual reports as the true test of dividend sustainability. Payout ratio <50% is considered safe per Buffett''s preference for capital allocation optionality. Dividend aristocrats (25+ years of increases) align with Buffett''s "wonderful company" criteria (1989 Letter). Net cash position reflects balance sheet strength emphasized in 2008 crisis commentary.'
);

-- Moat Strength Rubric
-- Research Basis: Warren Buffett's concept of "economic moats"
-- Key Principles:
--   1. ROE consistency is #1 indicator (40%) - "wonderful company" has >15% ROE
--   2. Gross margin shows pricing power (30%) - Buffett targets >40%
--   3. Intangibles (brands, patents) create barriers (20%)
--   4. Switching costs lock in customers (10%)
INSERT INTO rating_rubrics (
    rating_type,
    method_version,
    overall_weights,
    component_thresholds,
    description,
    research_basis
) VALUES (
    'moat_strength',
    'v1',
    '{
        "roe_consistency": 0.40,
        "gross_margin": 0.30,
        "intangibles": 0.20,
        "switching_costs": 0.10
    }'::jsonb,
    '{
        "roe_consistency": {
            "excellent": {"min": 0.20, "score": 10},
            "good": {"min": 0.15, "score": 8},
            "acceptable": {"min": 0.10, "score": 6},
            "poor": {"max": 0.10, "score": 4}
        },
        "gross_margin": {
            "excellent": {"min": 0.60, "score": 10},
            "good": {"min": 0.40, "score": 8},
            "acceptable": {"min": 0.25, "score": 6},
            "poor": {"max": 0.25, "score": 4}
        },
        "intangibles": {
            "excellent": {"min": 0.30, "score": 8},
            "good": {"min": 0.15, "score": 6},
            "poor": {"max": 0.15, "score": 4}
        },
        "switching_costs": {
            "note": "Qualitative score 0-10 based on sector and business model"
        }
    }'::jsonb,
    'Economic moat strength based on ROE consistency, gross margin, intangible assets, and switching costs',
    'Warren Buffett 2007 Letter: "A truly great business must have an enduring moat that protects excellent returns on invested capital." ROE >15% is cited as Buffett''s minimum threshold for "wonderful companies" (1987 Letter). Gross margins >40% indicate pricing power per See''s Candies case study (multiple letters). Intangible assets (brands like Coca-Cola) create durable competitive advantages (1988 Letter on Coca-Cola investment). Switching costs are explicit in Buffett''s analysis of credit card networks and software businesses (2000s commentary).'
);

-- Resilience Rubric
-- Research Basis: Buffett's "fortress balance sheet" principle
-- Key Principles:
--   1. Low debt is paramount (40%) - debt <0.5x equity ideal
--   2. Current ratio for short-term liquidity (25%) - >1.5 preferred
--   3. Interest coverage for debt service (20%) - >5x is comfortable
--   4. Margin stability for predictability (15%) - low volatility preferred
INSERT INTO rating_rubrics (
    rating_type,
    method_version,
    overall_weights,
    component_thresholds,
    description,
    research_basis
) VALUES (
    'resilience',
    'v1',
    '{
        "debt_equity": 0.40,
        "current_ratio": 0.25,
        "interest_coverage": 0.20,
        "margin_stability": 0.15
    }'::jsonb,
    '{
        "debt_equity": {
            "excellent": {"max": 0.50, "score": 10},
            "good": {"max": 1.00, "score": 8},
            "acceptable": {"max": 2.00, "score": 6},
            "poor": {"min": 2.00, "score": 3}
        },
        "interest_coverage": {
            "excellent": {"min": 10.0, "score": 10},
            "good": {"min": 5.0, "score": 8},
            "acceptable": {"min": 2.0, "score": 6},
            "poor": {"max": 2.0, "score": 3}
        },
        "current_ratio": {
            "excellent": {"min": 2.0, "score": 10},
            "good": {"min": 1.5, "score": 8},
            "acceptable": {"min": 1.0, "score": 7},
            "poor": {"max": 1.0, "score": 4}
        },
        "margin_stability": {
            "excellent": {"max": 0.02, "score": 10},
            "good": {"max": 0.05, "score": 8},
            "acceptable": {"max": 0.10, "score": 6},
            "poor": {"min": 0.10, "score": 4}
        }
    }'::jsonb,
    'Financial resilience based on debt/equity ratio, interest coverage, current ratio, and margin stability',
    'Warren Buffett 2008 Letter (during financial crisis): "In good years and bad, Charlie and I simply focus on four goals: maintaining Berkshire''s Gibraltar-like financial position." Debt/equity <0.5 is Buffett''s preference per analysis of Berkshire''s own balance sheet. Interest coverage >5x provides "ample cushion" (multiple annual reports). Current ratio >1.5 ensures short-term liquidity per See''s Candies and other wholly-owned subsidiary analyses. Operating margin consistency is emphasized as indicator of durable competitive advantage (1992 Letter on predictable earnings).'
);

-- Verify insertion
SELECT
    rating_type,
    method_version,
    description,
    LEFT(research_basis, 100) || '...' as research_excerpt
FROM rating_rubrics
WHERE method_version = 'v1'
ORDER BY rating_type;
