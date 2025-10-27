-- Base Portfolio Schema
-- Purpose: Core tables for portfolio holdings and transactions
-- Updated: 2025-10-22
-- Priority: P0 (Foundation for all portfolio-scoped tables)

-- ============================================================================
-- CONTEXT
-- ============================================================================
-- This is the foundation schema for DawsOS portfolio management.
-- All other tables (portfolio_metrics, currency_attribution, etc.) depend on
-- these base tables via foreign key relationships.
--
-- Design principles:
-- - UUID primary keys for distributed systems
-- - Immutability via audit fields (created_at, updated_at)
-- - PostgreSQL native types (NUMERIC for precision)
-- - Foreign keys with CASCADE for referential integrity
-- ============================================================================

-- ============================================================================
-- 1. PORTFOLIOS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS portfolios (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,

    -- Portfolio details
    name TEXT NOT NULL,
    description TEXT,
    base_currency TEXT NOT NULL DEFAULT 'USD',  -- ISO 4217 currency code

    -- Benchmark
    benchmark_id TEXT,  -- e.g., "SPY", "VTI", custom benchmark ID

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_portfolios_is_active ON portfolios(is_active) WHERE is_active = true;
CREATE INDEX idx_portfolios_benchmark_id ON portfolios(benchmark_id);

-- Comments
COMMENT ON TABLE portfolios IS 'User portfolios with base currency and benchmark configuration';
COMMENT ON COLUMN portfolios.user_id IS 'Owner of this portfolio (RLS isolation key)';
COMMENT ON COLUMN portfolios.base_currency IS 'Base currency for NAV calculation (ISO 4217)';
COMMENT ON COLUMN portfolios.benchmark_id IS 'Benchmark security ID for performance comparison';

-- ============================================================================
-- 2. LOTS TABLE (Holdings)
-- ============================================================================

CREATE TABLE IF NOT EXISTS lots (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,

    -- Security
    security_id UUID NOT NULL,  -- Reference to securities table (global)
    symbol TEXT NOT NULL,  -- Denormalized for convenience

    -- Lot tracking (tax lot accounting)
    acquisition_date DATE NOT NULL,
    quantity NUMERIC NOT NULL CHECK (quantity > 0),
    cost_basis NUMERIC NOT NULL,  -- Total cost in portfolio base currency
    cost_basis_per_share NUMERIC NOT NULL,  -- Per-share cost basis

    -- Currency
    currency TEXT NOT NULL DEFAULT 'USD',  -- Currency of cost basis

    -- Status
    is_open BOOLEAN DEFAULT TRUE,  -- False when lot is fully sold

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_lots_portfolio_id ON lots(portfolio_id);
CREATE INDEX idx_lots_security_id ON lots(security_id);
CREATE INDEX idx_lots_symbol ON lots(symbol);
CREATE INDEX idx_lots_acquisition_date ON lots(acquisition_date);
CREATE INDEX idx_lots_is_open ON lots(is_open) WHERE is_open = true;

-- Comments
COMMENT ON TABLE lots IS 'Tax lot holdings for portfolio positions (FIFO/LIFO/SpecID)';
COMMENT ON COLUMN lots.security_id IS 'Reference to global securities table';
COMMENT ON COLUMN lots.acquisition_date IS 'Date lot was acquired (for tax purposes)';
COMMENT ON COLUMN lots.cost_basis IS 'Total cost basis in portfolio base currency';
COMMENT ON COLUMN lots.is_open IS 'False when lot is fully sold (for tax lot closure)';

-- ============================================================================
-- 3. TRANSACTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,

    -- Transaction type
    transaction_type TEXT NOT NULL CHECK (
        transaction_type IN ('BUY', 'SELL', 'DIVIDEND', 'SPLIT', 'TRANSFER_IN', 'TRANSFER_OUT', 'FEE')
    ),

    -- Security (NULL for fees)
    security_id UUID,
    symbol TEXT,

    -- Transaction details
    transaction_date DATE NOT NULL,
    settlement_date DATE,

    -- Quantities and prices
    quantity NUMERIC,  -- NULL for fees
    price NUMERIC,  -- Per-share price
    amount NUMERIC NOT NULL,  -- Total transaction amount (signed)

    -- Currency
    currency TEXT NOT NULL DEFAULT 'USD',

    -- Fees and commissions
    fee NUMERIC DEFAULT 0,
    commission NUMERIC DEFAULT 0,

    -- Lot tracking (for sells)
    lot_id UUID REFERENCES lots(id) ON DELETE SET NULL,

    -- Narration
    narration TEXT,

    -- Provenance (from ledger or manual entry)
    source TEXT DEFAULT 'manual' CHECK (source IN ('ledger', 'manual', 'import')),
    ledger_commit_hash TEXT,  -- If from Beancount ledger

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_transactions_portfolio_id ON transactions(portfolio_id);
CREATE INDEX idx_transactions_security_id ON transactions(security_id);
CREATE INDEX idx_transactions_symbol ON transactions(symbol);
CREATE INDEX idx_transactions_transaction_date ON transactions(transaction_date DESC);
CREATE INDEX idx_transactions_transaction_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_lot_id ON transactions(lot_id);
CREATE INDEX idx_transactions_ledger_commit_hash ON transactions(ledger_commit_hash);

-- Comments
COMMENT ON TABLE transactions IS 'Portfolio transactions (buys, sells, dividends, etc.)';
COMMENT ON COLUMN transactions.transaction_type IS 'BUY, SELL, DIVIDEND, SPLIT, TRANSFER_IN, TRANSFER_OUT, FEE';
COMMENT ON COLUMN transactions.amount IS 'Total transaction amount (signed: positive for income, negative for outflow)';
COMMENT ON COLUMN transactions.lot_id IS 'For SELL transactions: which lot was sold (tax lot accounting)';
COMMENT ON COLUMN transactions.source IS 'ledger (Beancount), manual (user entry), import (CSV/broker)';
COMMENT ON COLUMN transactions.ledger_commit_hash IS 'Git commit hash if sourced from Beancount ledger';

-- ============================================================================
-- TRIGGERS: Update updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_portfolios_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_portfolios_updated_at
    BEFORE UPDATE ON portfolios
    FOR EACH ROW
    EXECUTE FUNCTION update_portfolios_updated_at();

CREATE OR REPLACE FUNCTION update_lots_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_lots_updated_at
    BEFORE UPDATE ON lots
    FOR EACH ROW
    EXECUTE FUNCTION update_lots_updated_at();

CREATE OR REPLACE FUNCTION update_transactions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_transactions_updated_at();

-- ============================================================================
-- SAMPLE DATA (Development)
-- ============================================================================

-- Sample user (for testing, disabled in production)
-- INSERT INTO portfolios (
--     id,
--     user_id,
--     name,
--     description,
--     base_currency,
--     benchmark_id
-- ) VALUES (
--     '11111111-1111-1111-1111-111111111111',
--     '00000000-0000-0000-0000-000000000001',
--     'My Portfolio',
--     'Sample portfolio for development',
--     'USD',
--     'SPY'
-- );

-- Sample lot (AAPL)
-- INSERT INTO lots (
--     portfolio_id,
--     security_id,
--     symbol,
--     acquisition_date,
--     quantity,
--     cost_basis,
--     cost_basis_per_share,
--     currency
-- ) VALUES (
--     '11111111-1111-1111-1111-111111111111',
--     '22222222-2222-2222-2222-222222222222',
--     'AAPL',
--     '2024-01-15',
--     100,
--     15000.00,
--     150.00,
--     'USD'
-- );

-- Sample transaction (AAPL buy)
-- INSERT INTO transactions (
--     portfolio_id,
--     transaction_type,
--     security_id,
--     symbol,
--     transaction_date,
--     quantity,
--     price,
--     amount,
--     currency,
--     source
-- ) VALUES (
--     '11111111-1111-1111-1111-111111111111',
--     'BUY',
--     '22222222-2222-2222-2222-222222222222',
--     'AAPL',
--     '2024-01-15',
--     100,
--     150.00,
--     -15000.00,  -- Negative = outflow
--     'USD',
--     'manual'
-- );

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'Base portfolio schema created successfully' AS status;

SELECT COUNT(*) AS portfolios_count FROM portfolios;
SELECT COUNT(*) AS lots_count FROM lots;
SELECT COUNT(*) AS transactions_count FROM transactions;

-- Verify indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('portfolios', 'lots', 'transactions')
ORDER BY tablename, indexname;

-- Verify foreign keys
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
  AND tc.table_name IN ('portfolios', 'lots', 'transactions')
ORDER BY tc.table_name;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. This schema uses tax lot accounting (lots table) for accurate cost basis
--    tracking and capital gains calculation.
--
-- 2. Transactions are linked to lots for SELL transactions to support
--    FIFO/LIFO/SpecID tax lot selection strategies.
--
-- 3. All amounts use NUMERIC type for precision (no floating point errors).
--
-- 4. Currency fields are ISO 4217 codes (USD, EUR, GBP, etc.).
--
-- 5. Ledger provenance is tracked via ledger_commit_hash for reconciliation.
--
-- 6. Row-Level Security (RLS) will be enabled on these tables via migration
--    005_create_rls_policies.sql.
--
-- 7. Dependencies:
--    - This schema must be created BEFORE portfolio_metrics schema
--    - This schema must be created BEFORE currency_attribution schema
--    - This schema must be created BEFORE RLS policies migration
-- ============================================================================
