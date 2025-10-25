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

-- ============================================================================
-- SECURITIES TABLE (Dependency for prices)
-- ============================================================================

DROP TABLE IF EXISTS securities CASCADE;

CREATE TABLE securities (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,  -- Ticker symbol (e.g., AAPL, RY.TO, XIU.TO)

    -- Security details
    name TEXT,  -- Company/fund name
    security_type TEXT NOT NULL DEFAULT 'equity',  -- equity, etf, bond, etc.
    exchange TEXT,  -- Exchange code (e.g., NASDAQ, TSX, NYSE)

    -- Currency
    trading_currency TEXT NOT NULL DEFAULT 'USD',  -- Currency for trading
    dividend_currency TEXT,  -- Currency for dividends (can differ for ADRs)

    -- Domicile
    domicile_country TEXT,  -- Country of incorporation

    -- Status
    active BOOLEAN DEFAULT TRUE,  -- Whether security is actively tracked

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_securities_symbol ON securities(symbol);
CREATE INDEX idx_securities_active ON securities(active) WHERE active = TRUE;
CREATE INDEX idx_securities_exchange ON securities(exchange);

-- Comments
COMMENT ON TABLE securities IS 'Master securities table (stocks, ETFs, bonds)';
COMMENT ON COLUMN securities.symbol IS 'Ticker symbol (normalized format)';
COMMENT ON COLUMN securities.trading_currency IS 'Currency for trading (ISO 4217)';
COMMENT ON COLUMN securities.dividend_currency IS 'Currency for dividends (may differ for ADRs)';

-- Trigger
CREATE OR REPLACE FUNCTION update_securities_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_securities_updated_at
    BEFORE UPDATE ON securities
    FOR EACH ROW
    EXECUTE FUNCTION update_securities_updated_at();


-- ============================================================================
-- PRICES TABLE (Daily security prices)
-- ============================================================================

DROP TABLE IF EXISTS prices CASCADE;

CREATE TABLE prices (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID NOT NULL REFERENCES securities(id) ON DELETE CASCADE,
    pricing_pack_id TEXT NOT NULL REFERENCES pricing_packs(id) ON DELETE CASCADE,

    -- Price details
    asof_date DATE NOT NULL,  -- Date of the price
    close NUMERIC(20, 8) NOT NULL,  -- Closing price (8 decimals for precision)

    -- Optional OHLC data
    open NUMERIC(20, 8),
    high NUMERIC(20, 8),
    low NUMERIC(20, 8),
    volume BIGINT,

    -- Currency and source
    currency TEXT NOT NULL,  -- Currency of the price
    source TEXT NOT NULL,  -- Provider source (polygon, fmp, etc.)

    -- Adjustment
    adjusted_for_splits BOOLEAN DEFAULT TRUE,  -- Whether split-adjusted
    adjusted_for_dividends BOOLEAN DEFAULT FALSE,  -- Whether dividend-adjusted (usually false)

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_prices_security ON prices(security_id, asof_date DESC);
CREATE INDEX idx_prices_pack ON prices(pricing_pack_id);
CREATE INDEX idx_prices_asof_date ON prices(asof_date DESC);
CREATE UNIQUE INDEX idx_prices_unique ON prices(security_id, pricing_pack_id);

-- Comments
COMMENT ON TABLE prices IS 'Daily security prices tied to pricing packs';
COMMENT ON COLUMN prices.close IS 'Closing price (usually split-adjusted)';
COMMENT ON COLUMN prices.pricing_pack_id IS 'Reference to immutable pricing pack';
COMMENT ON COLUMN prices.adjusted_for_splits IS 'Whether price is split-adjusted';
COMMENT ON COLUMN prices.adjusted_for_dividends IS 'Whether price is dividend-adjusted (rarely true)';


-- ============================================================================
-- FX_RATES TABLE (Foreign exchange rates)
-- ============================================================================

DROP TABLE IF EXISTS fx_rates CASCADE;

CREATE TABLE fx_rates (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pricing_pack_id TEXT NOT NULL REFERENCES pricing_packs(id) ON DELETE CASCADE,

    -- FX pair
    base_ccy TEXT NOT NULL,  -- Base currency (e.g., USD)
    quote_ccy TEXT NOT NULL,  -- Quote currency (e.g., CAD)

    -- Rate details
    asof_ts TIMESTAMPTZ NOT NULL,  -- Timestamp of FX rate
    rate NUMERIC(20, 10) NOT NULL,  -- Exchange rate (10 decimals for precision)

    -- Source and policy
    source TEXT NOT NULL,  -- Provider source (fred, fmp, etc.)
    policy TEXT,  -- Pricing policy (WM4PM, CLOSE, etc.)

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_fx_rates_pair ON fx_rates(base_ccy, quote_ccy, asof_ts DESC);
CREATE INDEX idx_fx_rates_pack ON fx_rates(pricing_pack_id);
CREATE UNIQUE INDEX idx_fx_rates_unique ON fx_rates(base_ccy, quote_ccy, pricing_pack_id);

-- Comments
COMMENT ON TABLE fx_rates IS 'Foreign exchange rates tied to pricing packs';
COMMENT ON COLUMN fx_rates.rate IS 'Exchange rate (quote_ccy per 1 unit of base_ccy)';
COMMENT ON COLUMN fx_rates.policy IS 'FX rate policy (e.g., WM4PM = WM/Reuters 4PM fixing)';
COMMENT ON COLUMN fx_rates.pricing_pack_id IS 'Reference to immutable pricing pack';


-- ============================================================================
-- SAMPLE DATA (Development)
-- ============================================================================

-- ============================================================================
-- SAMPLE DATA REMOVED
-- ============================================================================
-- Securities, prices, and FX rates are now loaded via seed_loader.py
-- See: data/seeds/symbols/securities.csv
--      data/seeds/prices/2025-10-21.csv
--      scripts/seed_loader.py --all
-- ============================================================================


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

SELECT 'Pricing packs schema created successfully' AS status;

SELECT 'pricing_packs' AS table_name, COUNT(*) AS row_count FROM pricing_packs
UNION ALL
SELECT 'securities', COUNT(*) FROM securities
UNION ALL
SELECT 'prices', COUNT(*) FROM prices
UNION ALL
SELECT 'fx_rates', COUNT(*) FROM fx_rates;

-- Verify indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('pricing_packs', 'securities', 'prices', 'fx_rates')
ORDER BY tablename, indexname;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. pricing_packs: Immutable snapshot records (status lifecycle: warming → fresh)
-- 2. securities: Master security table (normalized symbols, currency info)
-- 3. prices: Daily security prices tied to packs (split-adjusted by default)
-- 4. fx_rates: FX rates tied to packs (policy-driven, e.g., WM 4PM fixing)
-- 5. All prices and FX rates carry pricing_pack_id for reproducibility
-- 6. Pack supersession chain: old_pack.superseded_by = new_pack_id
-- 7. Stub data provided for development/testing (10 securities, 10 prices, 5 FX rates)
-- ============================================================================
