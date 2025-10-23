-- Pricing Packs Table
-- Purpose: Immutable pricing snapshots for reproducible valuation
-- Updated: 2025-10-22
-- Priority: P0 (Critical for S1-W2)

-- Drop table if exists (for development - remove in production)
DROP TABLE IF EXISTS pricing_packs CASCADE;

-- Create pricing_packs table
CREATE TABLE pricing_packs (
    -- Identity
    id TEXT PRIMARY KEY,  -- Format: "PP_YYYY-MM-DD" or "PP_YYYY-MM-DD_POLICY"
    date DATE NOT NULL,
    policy TEXT NOT NULL DEFAULT 'WM4PM_CAD',  -- Pricing policy (e.g., WM4PM_CAD, CLOSE_USD)

    -- Immutability & Versioning
    hash TEXT NOT NULL,  -- SHA-256 hash of (date + policy + sources_json) for integrity
    superseded_by TEXT REFERENCES pricing_packs(id),  -- For restatements (D0 → D1)

    -- Sources
    sources_json JSONB NOT NULL DEFAULT '{}',  -- {"FMP": true, "Polygon": true, "FRED": true}

    -- Status Fields
    status TEXT NOT NULL DEFAULT 'warming',  -- 'warming', 'fresh', 'error'
    is_fresh BOOLEAN NOT NULL DEFAULT false,  -- Main freshness flag (executor gate)
    prewarm_done BOOLEAN NOT NULL DEFAULT false,  -- Pre-warm computation complete

    -- Reconciliation
    reconciliation_passed BOOLEAN NOT NULL DEFAULT false,  -- Ledger vs DB ±1bp
    reconciliation_failed BOOLEAN NOT NULL DEFAULT false,  -- Reconciliation error
    reconciliation_error_bps NUMERIC(10, 4),  -- Error in basis points (if > 1bp)

    -- Error Tracking
    error_message TEXT,  -- Error details if status = 'error'

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_pricing_packs_date ON pricing_packs(date DESC);
CREATE INDEX idx_pricing_packs_status ON pricing_packs(status);
CREATE INDEX idx_pricing_packs_is_fresh ON pricing_packs(is_fresh) WHERE is_fresh = true;
CREATE INDEX idx_pricing_packs_superseded_by ON pricing_packs(superseded_by) WHERE superseded_by IS NOT NULL;

-- Constraints
ALTER TABLE pricing_packs
    ADD CONSTRAINT chk_pricing_packs_status
    CHECK (status IN ('warming', 'fresh', 'error'));

ALTER TABLE pricing_packs
    ADD CONSTRAINT chk_pricing_packs_reconciliation
    CHECK (
        -- If reconciliation passed, error_bps must be <= 1.0
        (reconciliation_passed = true AND (reconciliation_error_bps IS NULL OR reconciliation_error_bps <= 1.0))
        OR
        -- If reconciliation failed, error_bps must be > 1.0 or NULL
        (reconciliation_failed = true AND (reconciliation_error_bps IS NULL OR reconciliation_error_bps > 1.0))
        OR
        -- Neither passed nor failed (in progress)
        (reconciliation_passed = false AND reconciliation_failed = false)
    );

-- Unique constraint: one pack per date+policy (unless superseded)
CREATE UNIQUE INDEX uq_pricing_packs_date_policy
    ON pricing_packs(date, policy)
    WHERE superseded_by IS NULL;

-- Comments
COMMENT ON TABLE pricing_packs IS 'Immutable pricing snapshots for reproducible portfolio valuation';
COMMENT ON COLUMN pricing_packs.id IS 'Pack identifier (e.g., PP_2025-10-21)';
COMMENT ON COLUMN pricing_packs.date IS 'Pack date (asof date for prices)';
COMMENT ON COLUMN pricing_packs.policy IS 'Pricing policy (WM4PM_CAD = 4PM London fixing for CAD)';
COMMENT ON COLUMN pricing_packs.hash IS 'SHA-256 hash for integrity verification';
COMMENT ON COLUMN pricing_packs.superseded_by IS 'ID of pack that supersedes this one (for restatements)';
COMMENT ON COLUMN pricing_packs.sources_json IS 'Data sources used (FMP, Polygon, FRED, etc.)';
COMMENT ON COLUMN pricing_packs.status IS 'Pack status: warming (building), fresh (ready), error (failed)';
COMMENT ON COLUMN pricing_packs.is_fresh IS 'Freshness flag - executor blocks if false';
COMMENT ON COLUMN pricing_packs.prewarm_done IS 'Pre-warm computations complete (factors, ratings)';
COMMENT ON COLUMN pricing_packs.reconciliation_passed IS 'Ledger reconciliation passed (±1bp)';
COMMENT ON COLUMN pricing_packs.reconciliation_failed IS 'Ledger reconciliation failed (>1bp error)';
COMMENT ON COLUMN pricing_packs.reconciliation_error_bps IS 'Reconciliation error in basis points';
COMMENT ON COLUMN pricing_packs.error_message IS 'Error details if status = error';

-- Trigger: Update updated_at on row modification
CREATE OR REPLACE FUNCTION update_pricing_packs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_pricing_packs_updated_at
    BEFORE UPDATE ON pricing_packs
    FOR EACH ROW
    EXECUTE FUNCTION update_pricing_packs_updated_at();

-- Sample data (for development)
INSERT INTO pricing_packs (
    id,
    date,
    policy,
    hash,
    status,
    is_fresh,
    prewarm_done,
    reconciliation_passed,
    sources_json
) VALUES (
    'PP_2025-10-21',
    '2025-10-21',
    'WM4PM_CAD',
    'sha256:abc123def456',
    'fresh',
    true,
    true,
    true,
    '{"FMP": true, "Polygon": true, "FRED": true}'::jsonb
);

-- Verification queries
SELECT 'Pricing packs table created successfully' AS status;
SELECT COUNT(*) AS pack_count FROM pricing_packs;
