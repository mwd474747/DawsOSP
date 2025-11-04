-- Migration 002: Add missing constraints and indexes
-- Created: 2025-11-04
-- Priority: CRITICAL - Data integrity and performance
-- Risk: LOW (all changes are additive)
-- Estimated execution time: < 5 minutes

BEGIN;

-- ============================================================================
-- STEP 1: Add missing foreign key constraints
-- ============================================================================

-- Enforce portfolio ownership by user
ALTER TABLE portfolios 
  ADD CONSTRAINT fk_portfolios_user 
  FOREIGN KEY (user_id) 
  REFERENCES users(id) 
  ON DELETE CASCADE;

-- Ensure transactions reference valid securities
ALTER TABLE transactions 
  ADD CONSTRAINT fk_transactions_security 
  FOREIGN KEY (security_id) 
  REFERENCES securities(id) 
  ON DELETE RESTRICT;

-- ============================================================================
-- STEP 2: Add missing check constraints for data validation
-- ============================================================================

-- Ensure positive transaction quantities
ALTER TABLE transactions 
  ADD CONSTRAINT chk_transactions_quantity_positive 
  CHECK (quantity > 0);

-- Validate currency codes
ALTER TABLE portfolios
  ADD CONSTRAINT chk_portfolios_base_currency_valid
  CHECK (base_currency IN ('USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'HKD', 'SGD'));

-- Limit symbol length to reasonable size
ALTER TABLE securities
  ADD CONSTRAINT chk_securities_symbol_length
  CHECK (LENGTH(symbol) <= 12);

-- ============================================================================
-- STEP 3: Add composite indexes for query performance
-- ============================================================================

-- Optimize portfolio transaction history queries
CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_date 
  ON transactions(portfolio_id, transaction_date DESC);

-- Optimize open position queries
CREATE INDEX IF NOT EXISTS idx_lots_portfolio_open 
  ON lots(portfolio_id, is_open) 
  WHERE is_open = true;

-- Optimize portfolio transaction type analysis
CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_type_date
  ON transactions(portfolio_id, transaction_type, transaction_date DESC);

-- ============================================================================
-- STEP 4: Add unique constraints
-- ============================================================================

-- Prevent duplicate portfolio names per user
ALTER TABLE portfolios
  ADD CONSTRAINT unq_portfolios_user_name
  UNIQUE (user_id, name);

-- ============================================================================
-- STEP 5: Add helpful indexes for common queries
-- ============================================================================

-- Index for finding recent transactions
CREATE INDEX IF NOT EXISTS idx_transactions_recent
  ON transactions(created_at DESC)
  WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

-- Index for active portfolios
CREATE INDEX IF NOT EXISTS idx_portfolios_active
  ON portfolios(user_id, is_active)
  WHERE is_active = true;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (save this separately as 002_rollback.sql)
-- ============================================================================
/*
-- To rollback this migration if needed:

BEGIN;

-- Drop constraints
ALTER TABLE portfolios DROP CONSTRAINT IF EXISTS fk_portfolios_user;
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS fk_transactions_security;
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS chk_transactions_quantity_positive;
ALTER TABLE portfolios DROP CONSTRAINT IF EXISTS chk_portfolios_base_currency_valid;
ALTER TABLE securities DROP CONSTRAINT IF EXISTS chk_securities_symbol_length;
ALTER TABLE portfolios DROP CONSTRAINT IF EXISTS unq_portfolios_user_name;

-- Drop indexes
DROP INDEX IF EXISTS idx_transactions_portfolio_date;
DROP INDEX IF EXISTS idx_lots_portfolio_open;
DROP INDEX IF EXISTS idx_transactions_portfolio_type_date;
DROP INDEX IF EXISTS idx_transactions_recent;
DROP INDEX IF EXISTS idx_portfolios_active;

COMMIT;
*/

-- ============================================================================
-- VALIDATION QUERIES (run after migration)
-- ============================================================================
/*
-- Check foreign key enforcement works
SELECT 'Foreign keys working' as test,
       COUNT(*) = 0 as passed
FROM portfolios p
WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = p.user_id);

-- Check constraint enforcement
SELECT 'Check constraints working' as test,
       COUNT(*) = 0 as passed  
FROM transactions
WHERE quantity <= 0;

-- Test index performance improvement
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM transactions
WHERE portfolio_id = (SELECT id FROM portfolios LIMIT 1)
AND transaction_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY transaction_date DESC;
*/