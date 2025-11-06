-- Migration 018: Add cost basis method tracking to portfolios
-- Date: January 14, 2025
-- Description: Add cost_basis_method field to track lot selection method per portfolio
--
-- COMPLIANCE ISSUE: IRS requires consistent cost basis method and tracking
-- FIX: Add cost_basis_method field with validation and audit logging
-- IMPACT: Enables proper tax reporting and prevents LIFO usage for stocks (illegal since 2011)
--
-- Related: IRS Pub 550 (Investment Income and Expenses)
--          TD 9811 (2017) - Average cost method regulations
--          Energy Improvement and Extension Act of 2008 (banned LIFO for stocks)

-- Add cost_basis_method column to portfolios table
ALTER TABLE portfolios
ADD COLUMN IF NOT EXISTS cost_basis_method VARCHAR(20) DEFAULT 'FIFO'
    CHECK (cost_basis_method IN ('FIFO', 'LIFO', 'HIFO', 'SPECIFIC_LOT', 'AVERAGE_COST'));

COMMENT ON COLUMN portfolios.cost_basis_method IS
'Cost basis method for lot selection: FIFO (First In First Out), LIFO (Last In First Out - mutual funds/ETFs only), HIFO (Highest In First Out), SPECIFIC_LOT (manual selection), AVERAGE_COST (mutual funds only). Default: FIFO per IRS regulations.';

-- Add timestamp for tracking when method was last changed (IRS audit requirement)
ALTER TABLE portfolios
ADD COLUMN IF NOT EXISTS cost_basis_method_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

COMMENT ON COLUMN portfolios.cost_basis_method_changed_at IS
'Timestamp when cost_basis_method was last changed. Required for IRS audit trail per TD 9811 regulations.';

-- Create audit log table for cost basis method changes
CREATE TABLE IF NOT EXISTS cost_basis_method_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    old_method VARCHAR(20),
    new_method VARCHAR(20) NOT NULL,
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reason TEXT,
    CONSTRAINT fk_portfolio FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
);

COMMENT ON TABLE cost_basis_method_audit IS
'Audit log for cost basis method changes. Required for IRS compliance and tracking when investor changed lot selection method.';

CREATE INDEX IF NOT EXISTS idx_cost_basis_audit_portfolio
ON cost_basis_method_audit(portfolio_id, changed_at DESC);

CREATE INDEX IF NOT EXISTS idx_cost_basis_audit_changed_by
ON cost_basis_method_audit(changed_by);

-- Create trigger to log cost basis method changes
CREATE OR REPLACE FUNCTION log_cost_basis_method_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only log if the method actually changed
    IF OLD.cost_basis_method IS DISTINCT FROM NEW.cost_basis_method THEN
        INSERT INTO cost_basis_method_audit (
            portfolio_id,
            old_method,
            new_method,
            changed_at
        ) VALUES (
            NEW.id,
            OLD.cost_basis_method,
            NEW.cost_basis_method,
            NOW()
        );

        -- Update the changed_at timestamp
        NEW.cost_basis_method_changed_at := NOW();
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_cost_basis_method_change
BEFORE UPDATE ON portfolios
FOR EACH ROW
EXECUTE FUNCTION log_cost_basis_method_change();

-- Create validation function to prevent LIFO for stocks
CREATE OR REPLACE FUNCTION validate_cost_basis_method_for_asset_type()
RETURNS TRIGGER AS $$
DECLARE
    has_stock_positions BOOLEAN;
BEGIN
    -- Check if portfolio has any stock positions
    SELECT EXISTS(
        SELECT 1
        FROM lots l
        JOIN portfolios p ON l.portfolio_id = p.id
        LEFT JOIN securities s ON l.symbol = s.symbol
        WHERE l.portfolio_id = NEW.id
          AND l.qty_open > 0
          AND (s.asset_type = 'STOCK' OR s.asset_type IS NULL) -- Assume STOCK if not in securities table
    ) INTO has_stock_positions;

    -- Prevent LIFO for portfolios with stock positions
    IF NEW.cost_basis_method = 'LIFO' AND has_stock_positions THEN
        RAISE EXCEPTION 'LIFO cost basis method is not allowed for portfolios with stock positions per IRS regulations (Energy Improvement and Extension Act of 2008). Use FIFO, HIFO, or SPECIFIC_LOT instead.'
            USING HINT = 'LIFO is only allowed for mutual funds and ETFs';
    END IF;

    -- Prevent AVERAGE_COST for anything except mutual funds
    IF NEW.cost_basis_method = 'AVERAGE_COST' THEN
        IF EXISTS(
            SELECT 1
            FROM lots l
            LEFT JOIN securities s ON l.symbol = s.symbol
            WHERE l.portfolio_id = NEW.id
              AND l.qty_open > 0
              AND s.asset_type NOT IN ('MUTUAL_FUND', 'ETF')
        ) THEN
            RAISE EXCEPTION 'AVERAGE_COST method is only allowed for mutual funds per IRS regulations'
                USING HINT = 'Use FIFO, HIFO, or SPECIFIC_LOT for stocks and other securities';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_cost_basis_method
BEFORE INSERT OR UPDATE ON portfolios
FOR EACH ROW
EXECUTE FUNCTION validate_cost_basis_method_for_asset_type();

-- Verify the changes
SELECT
    table_name,
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'portfolios'
  AND column_name IN ('cost_basis_method', 'cost_basis_method_changed_at')
ORDER BY ordinal_position;

-- Show current portfolios and their cost basis methods
SELECT
    id,
    portfolio_name,
    cost_basis_method,
    cost_basis_method_changed_at
FROM portfolios
ORDER BY portfolio_name;

-- MIGRATION NOTES:
-- 1. All existing portfolios will default to FIFO (most conservative, IRS default)
-- 2. Portfolios with stock positions cannot change to LIFO (will be rejected by trigger)
-- 3. Changes to cost_basis_method are automatically logged to cost_basis_method_audit
-- 4. IRS allows changing method, but requires consistent application going forward
