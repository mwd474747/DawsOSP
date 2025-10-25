-- Ledger Schema
-- Purpose: Beancount ledger parsing, reconciliation, and audit trail
-- Updated: 2025-10-23
-- Priority: P0 (Truth spine foundation)

-- ============================================================================
-- CONTEXT
-- ============================================================================
-- This schema implements the "ledger as truth" principle:
-- - Beancount ledger stored in Git is the immutable source of truth
-- - Database is a derivative view that must reconcile to ±1 basis point
-- - Every result includes ledger_commit_hash for reproducibility
--
-- Design principles:
-- - Immutability: Ledger snapshots are never updated, only superseded
-- - Auditability: Every reconciliation result is stored with full provenance
-- - Reproducibility: Same commit_hash + pricing_pack_id → identical NAV
-- - Accuracy: Reconciliation tolerance is ±1 basis point (0.0001)
-- ============================================================================

-- ============================================================================
-- 1. LEDGER SNAPSHOTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS ledger_snapshots (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Git provenance
    commit_hash TEXT NOT NULL UNIQUE,  -- Git commit SHA (40 chars)
    repository_url TEXT,  -- Git repo URL (for remote clones)
    branch TEXT DEFAULT 'main',

    -- Parsing metadata
    parsed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    transaction_count INT NOT NULL,  -- Total transactions parsed
    account_count INT NOT NULL,  -- Unique accounts
    earliest_date DATE,  -- Earliest transaction date
    latest_date DATE,  -- Latest transaction date

    -- File integrity
    file_hash TEXT NOT NULL,  -- SHA-256 of ledger file(s)
    file_paths TEXT[],  -- Array of .beancount files parsed

    -- Parsing status
    status TEXT NOT NULL DEFAULT 'parsing' CHECK (
        status IN ('parsing', 'parsed', 'failed', 'superseded')
    ),
    error_message TEXT,  -- If status = 'failed'

    -- Supersession (for restatements)
    superseded_by UUID REFERENCES ledger_snapshots(id) ON DELETE SET NULL,
    superseded_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ledger_snapshots_commit_hash ON ledger_snapshots(commit_hash);
CREATE INDEX idx_ledger_snapshots_parsed_at ON ledger_snapshots(parsed_at DESC);
CREATE INDEX idx_ledger_snapshots_status ON ledger_snapshots(status) WHERE status = 'parsed';
CREATE INDEX idx_ledger_snapshots_date_range ON ledger_snapshots(earliest_date, latest_date);

-- Comments
COMMENT ON TABLE ledger_snapshots IS 'Beancount ledger parsing metadata (immutable snapshots)';
COMMENT ON COLUMN ledger_snapshots.commit_hash IS 'Git commit SHA-1 hash (40 hex chars)';
COMMENT ON COLUMN ledger_snapshots.file_hash IS 'SHA-256 hash of concatenated ledger files';
COMMENT ON COLUMN ledger_snapshots.transaction_count IS 'Total transactions parsed from ledger';
COMMENT ON COLUMN ledger_snapshots.superseded_by IS 'If ledger was restated, points to new snapshot';

-- ============================================================================
-- 2. LEDGER TRANSACTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS ledger_transactions (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ledger_snapshot_id UUID NOT NULL REFERENCES ledger_snapshots(id) ON DELETE CASCADE,

    -- Transaction identity from ledger
    transaction_date DATE NOT NULL,
    transaction_index INT NOT NULL,  -- Order within same date

    -- Beancount transaction metadata
    narration TEXT,
    payee TEXT,
    tags TEXT[],  -- Beancount tags (#portfolio1, etc.)
    links TEXT[],  -- Beancount links (^invoice123, etc.)

    -- Posting details (one row per posting)
    account TEXT NOT NULL,  -- e.g., "Assets:Investments:AAPL"
    commodity TEXT,  -- e.g., "AAPL", "USD", "CAD"
    quantity NUMERIC,  -- Quantity (NULL for balancing postings)
    price NUMERIC,  -- Per-unit price
    price_commodity TEXT,  -- Price currency (e.g., "USD")
    cost NUMERIC,  -- Cost basis per unit
    cost_commodity TEXT,  -- Cost currency

    -- Metadata fields (from Beancount metadata)
    metadata JSONB,  -- Store all key-value pairs

    -- Transaction type classification
    transaction_type TEXT CHECK (
        transaction_type IN ('BUY', 'SELL', 'DIVIDEND', 'SPLIT', 'TRANSFER_IN', 'TRANSFER_OUT', 'FEE', 'BALANCE', 'PAD', 'OTHER')
    ),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ledger_transactions_snapshot_id ON ledger_transactions(ledger_snapshot_id);
CREATE INDEX idx_ledger_transactions_date ON ledger_transactions(transaction_date DESC);
CREATE INDEX idx_ledger_transactions_account ON ledger_transactions(account);
CREATE INDEX idx_ledger_transactions_commodity ON ledger_transactions(commodity);
CREATE INDEX idx_ledger_transactions_type ON ledger_transactions(transaction_type);
CREATE INDEX idx_ledger_transactions_tags ON ledger_transactions USING gin(tags);
CREATE INDEX idx_ledger_transactions_metadata ON ledger_transactions USING gin(metadata);

-- Unique constraint: snapshot + date + index
CREATE UNIQUE INDEX idx_ledger_transactions_unique
    ON ledger_transactions(ledger_snapshot_id, transaction_date, transaction_index, account, commodity);

-- Comments
COMMENT ON TABLE ledger_transactions IS 'Parsed Beancount transactions (postings expanded to rows)';
COMMENT ON COLUMN ledger_transactions.transaction_index IS 'Order of transaction within same date';
COMMENT ON COLUMN ledger_transactions.account IS 'Beancount account (e.g., Assets:Investments:AAPL)';
COMMENT ON COLUMN ledger_transactions.quantity IS 'Quantity (NULL for balancing postings)';
COMMENT ON COLUMN ledger_transactions.metadata IS 'Beancount metadata as JSONB (pay_date, lot_id, etc.)';
COMMENT ON COLUMN ledger_transactions.transaction_type IS 'Classified type for reconciliation';

-- ============================================================================
-- 3. RECONCILIATION RESULTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS reconciliation_results (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reconciliation scope
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    asof_date DATE NOT NULL,

    -- Provenance
    ledger_commit_hash TEXT NOT NULL,
    ledger_snapshot_id UUID NOT NULL REFERENCES ledger_snapshots(id) ON DELETE CASCADE,
    pricing_pack_id TEXT NOT NULL,  -- Reference to pricing_packs.id

    -- NAV calculations
    ledger_nav NUMERIC NOT NULL,  -- NAV computed from ledger
    db_nav NUMERIC NOT NULL,  -- NAV computed from DB transactions

    -- Reconciliation metrics
    difference NUMERIC NOT NULL,  -- ledger_nav - db_nav
    error_bp NUMERIC NOT NULL,  -- Error in basis points (difference / ledger_nav * 10000)

    -- Tolerance check
    status TEXT NOT NULL CHECK (
        status IN ('pass', 'fail', 'warning')
    ),
    tolerance_bp NUMERIC NOT NULL DEFAULT 1.0,  -- Tolerance in basis points (default ±1bp)

    -- Detailed breakdown
    ledger_position_count INT,
    db_position_count INT,
    missing_in_db TEXT[],  -- Symbols present in ledger but not in DB
    missing_in_ledger TEXT[],  -- Symbols present in DB but not in ledger
    quantity_mismatches JSONB,  -- [{symbol, ledger_qty, db_qty, diff}]

    -- Diagnostics
    error_message TEXT,
    diagnostics JSONB,  -- Additional debug info

    -- Execution metadata
    reconciled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reconciliation_duration_ms INT,  -- Time taken to reconcile

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reconciliation_results_portfolio_id ON reconciliation_results(portfolio_id);
CREATE INDEX idx_reconciliation_results_asof_date ON reconciliation_results(asof_date DESC);
CREATE INDEX idx_reconciliation_results_status ON reconciliation_results(status);
CREATE INDEX idx_reconciliation_results_ledger_commit ON reconciliation_results(ledger_commit_hash);
CREATE INDEX idx_reconciliation_results_pricing_pack ON reconciliation_results(pricing_pack_id);
CREATE INDEX idx_reconciliation_results_reconciled_at ON reconciliation_results(reconciled_at DESC);

-- Unique constraint: portfolio + asof_date + ledger_commit + pricing_pack
CREATE UNIQUE INDEX idx_reconciliation_unique
    ON reconciliation_results(portfolio_id, asof_date, ledger_commit_hash, pricing_pack_id);

-- Comments
COMMENT ON TABLE reconciliation_results IS 'Nightly ledger vs DB reconciliation results (±1bp tolerance)';
COMMENT ON COLUMN reconciliation_results.ledger_nav IS 'NAV computed from Beancount ledger';
COMMENT ON COLUMN reconciliation_results.db_nav IS 'NAV computed from database transactions';
COMMENT ON COLUMN reconciliation_results.error_bp IS 'Reconciliation error in basis points (10000 = 1%)';
COMMENT ON COLUMN reconciliation_results.status IS 'pass (≤1bp), fail (>1bp), warning (edge cases)';
COMMENT ON COLUMN reconciliation_results.tolerance_bp IS 'Tolerance threshold in basis points (default 1.0)';

-- ============================================================================
-- TRIGGERS: Update updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_ledger_snapshots_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ledger_snapshots_updated_at
    BEFORE UPDATE ON ledger_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION update_ledger_snapshots_updated_at();

-- ============================================================================
-- VIEWS: Reconciliation Summary
-- ============================================================================

CREATE OR REPLACE VIEW reconciliation_summary AS
SELECT
    portfolio_id,
    asof_date,
    status,
    error_bp,
    ledger_nav,
    db_nav,
    difference,
    ledger_commit_hash,
    pricing_pack_id,
    reconciled_at,
    CASE
        WHEN status = 'pass' THEN 'Reconciled within ±1bp'
        WHEN status = 'warning' THEN 'Warning: edge cases detected'
        ELSE 'FAILED: error exceeds ±1bp tolerance'
    END AS message
FROM reconciliation_results
ORDER BY reconciled_at DESC;

COMMENT ON VIEW reconciliation_summary IS 'Human-readable reconciliation status summary';

-- ============================================================================
-- VIEWS: Latest Ledger Snapshot
-- ============================================================================

CREATE OR REPLACE VIEW latest_ledger_snapshot AS
SELECT
    id,
    commit_hash,
    parsed_at,
    transaction_count,
    account_count,
    earliest_date,
    latest_date,
    status
FROM ledger_snapshots
WHERE status = 'parsed'
  AND superseded_by IS NULL
ORDER BY parsed_at DESC
LIMIT 1;

COMMENT ON VIEW latest_ledger_snapshot IS 'Most recent successfully parsed ledger snapshot';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'Ledger schema created successfully' AS status;

SELECT COUNT(*) AS ledger_snapshots_count FROM ledger_snapshots;
SELECT COUNT(*) AS ledger_transactions_count FROM ledger_transactions;
SELECT COUNT(*) AS reconciliation_results_count FROM reconciliation_results;

-- Verify indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('ledger_snapshots', 'ledger_transactions', 'reconciliation_results')
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
  AND tc.table_name IN ('ledger_snapshots', 'ledger_transactions', 'reconciliation_results')
ORDER BY tc.table_name;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. Ledger snapshots are immutable: once parsed, they are never updated.
--    Restatements create new snapshots with superseded_by linkage.
--
-- 2. ledger_transactions stores one row per posting (Beancount postings are
--    expanded to individual rows for easier querying).
--
-- 3. Reconciliation results store both NAV values and detailed diagnostics
--    for troubleshooting discrepancies.
--
-- 4. The ±1 basis point tolerance is enforced in the reconciliation job,
--    but stored here for auditability.
--
-- 5. All reconciliation results are kept indefinitely for audit trail.
--
-- 6. Tags and metadata from Beancount are stored for portfolio filtering
--    (e.g., #portfolio1, #taxable).
--
-- 7. Dependencies:
--    - This schema must be created AFTER 001_portfolios_lots_transactions.sql
--    - This schema must be created BEFORE nightly reconciliation job runs
-- ============================================================================
