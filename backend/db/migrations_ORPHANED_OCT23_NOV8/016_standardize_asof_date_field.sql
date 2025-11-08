-- Migration 016: Standardize asof_date field naming
-- Date: January 14, 2025
-- Description: Rename valuation_date to asof_date for consistency with financial standards
--
-- ISSUE: Database documentation claims "asof_date" but some tables use "valuation_date"
-- FIX: Standardize all temporal point-in-time fields to "asof_date"
-- IMPACT: holdings, portfolio_values, dar_results tables

-- Check if valuation_date exists in holdings table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'holdings' AND column_name = 'valuation_date'
    ) THEN
        -- Rename valuation_date to asof_date in holdings
        ALTER TABLE holdings RENAME COLUMN valuation_date TO asof_date;
        RAISE NOTICE 'Renamed holdings.valuation_date to asof_date';
    ELSE
        RAISE NOTICE 'holdings.valuation_date does not exist, skipping';
    END IF;
END $$;

-- Check if valuation_date exists in portfolio_values table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'portfolio_values' AND column_name = 'valuation_date'
    ) THEN
        -- Rename valuation_date to asof_date in portfolio_values
        ALTER TABLE portfolio_values RENAME COLUMN valuation_date TO asof_date;
        RAISE NOTICE 'Renamed portfolio_values.valuation_date to asof_date';
    ELSE
        RAISE NOTICE 'portfolio_values.valuation_date does not exist, skipping';
    END IF;
END $$;

-- Check if valuation_date exists in dar_results table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'dar_results' AND column_name = 'valuation_date'
    ) THEN
        -- Rename valuation_date to asof_date in dar_results
        ALTER TABLE dar_results RENAME COLUMN valuation_date TO asof_date;
        RAISE NOTICE 'Renamed dar_results.valuation_date to asof_date';
    ELSE
        RAISE NOTICE 'dar_results.valuation_date does not exist, skipping';
    END IF;
END $$;

-- Update any indexes that reference the old column name
DO $$
DECLARE
    idx_record RECORD;
BEGIN
    FOR idx_record IN
        SELECT indexname
        FROM pg_indexes
        WHERE indexdef LIKE '%valuation_date%'
    LOOP
        RAISE NOTICE 'Found index referencing valuation_date: %', idx_record.indexname;
        -- Indexes will automatically update with column rename in PostgreSQL
    END LOOP;
END $$;

-- Verify the changes
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE column_name = 'asof_date'
    AND table_schema = 'public'
ORDER BY table_name;

COMMENT ON COLUMN holdings.asof_date IS 'Point-in-time date for position valuation (standardized from valuation_date)';
COMMENT ON COLUMN portfolio_values.asof_date IS 'Point-in-time date for portfolio value calculation (standardized from valuation_date)';
COMMENT ON COLUMN dar_results.asof_date IS 'Point-in-time date for Drawdown at Risk calculation (standardized from valuation_date)';
