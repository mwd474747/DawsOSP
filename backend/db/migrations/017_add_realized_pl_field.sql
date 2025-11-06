-- Migration 017: Add realized P&L tracking to transactions
-- Date: January 14, 2025
-- Description: Add realized_pl field to track realized profit/loss for tax reporting
--
-- COMPLIANCE ISSUE: IRS requires separation of realized vs unrealized gains/losses
-- FIX: Add realized_pl field to transactions table
-- IMPACT: Enables proper Form 1099-B reporting and wash sale detection
--
-- Related: IRC § 1001 (Determination of amount of and recognition of gain or loss)
--          IRC § 1091 (Loss from wash sales of stock or securities)

-- Add realized_pl column to transactions table
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS realized_pl NUMERIC(20, 2) DEFAULT NULL;

COMMENT ON COLUMN transactions.realized_pl IS
'Realized profit/loss for SELL transactions (proceeds - cost_basis). NULL for BUY transactions. Required for IRS Form 1099-B compliance and tax reporting.';

-- Create index for realized P&L queries (tax reporting, performance analysis)
CREATE INDEX IF NOT EXISTS idx_transactions_realized_pl
ON transactions(realized_pl)
WHERE realized_pl IS NOT NULL;

-- Create index for tax year reporting queries
CREATE INDEX IF NOT EXISTS idx_transactions_tax_year
ON transactions(portfolio_id, EXTRACT(YEAR FROM transaction_date), realized_pl)
WHERE realized_pl IS NOT NULL;

-- Verify the column was added
SELECT
    table_name,
    column_name,
    data_type,
    numeric_precision,
    numeric_scale,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'transactions' AND column_name = 'realized_pl';

-- Count existing SELL transactions that need realized_pl calculation
SELECT
    COUNT(*) as total_sell_transactions,
    COUNT(realized_pl) as transactions_with_realized_pl,
    COUNT(*) - COUNT(realized_pl) as transactions_missing_realized_pl
FROM transactions
WHERE transaction_type = 'SELL';

-- BACKFILL STRATEGY (to be run separately after migration):
--
-- UPDATE transactions t
-- SET realized_pl = (
--     SELECT
--         t.total_amount - SUM(l.cost_basis_per_share * l.quantity_closed)
--     FROM lots l
--     WHERE l.closing_transaction_id = t.id
-- )
-- WHERE t.transaction_type = 'SELL'
--   AND t.realized_pl IS NULL;
--
-- Note: This backfill should be run after verifying lot closure data integrity
