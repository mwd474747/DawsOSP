-- Alerts and Notifications Schema
-- Purpose: Alert system with DLQ and deduplication (Sprint 3 Week 6)
-- Updated: 2025-10-22
-- Priority: P1 (Sprint 3)

-- ============================================================================
-- ALERTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS alerts (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,

    -- Condition
    condition_json JSONB NOT NULL,  -- {"metric": "twr_ytd", "operator": ">", "threshold": 0.10}

    -- Notification channels
    notify_email BOOLEAN DEFAULT FALSE,
    notify_inapp BOOLEAN DEFAULT TRUE,

    -- Cooldown (prevent spam)
    cooldown_hours INT DEFAULT 24,
    last_fired_at TIMESTAMPTZ,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_is_active ON alerts(is_active) WHERE is_active = true;
CREATE INDEX idx_alerts_last_fired ON alerts(last_fired_at);

-- Comments
COMMENT ON TABLE alerts IS 'User-defined alerts with condition evaluation';
COMMENT ON COLUMN alerts.condition_json IS 'Alert condition (metric, operator, threshold)';
COMMENT ON COLUMN alerts.cooldown_hours IS 'Minimum hours between notifications (default: 24h)';
COMMENT ON COLUMN alerts.last_fired_at IS 'Last time alert was triggered';

-- ============================================================================
-- NOTIFICATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    alert_id UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,

    -- Content
    message TEXT NOT NULL,

    -- Delivery
    delivered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Read status
    read_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Deduplication constraint: one notification per alert per day
    CONSTRAINT notifications_dedupe UNIQUE (user_id, alert_id, (delivered_at::date))
);

-- Indexes
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_alert_id ON notifications(alert_id);
CREATE INDEX idx_notifications_delivered_at ON notifications(delivered_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id, read_at) WHERE read_at IS NULL;

-- Comments
COMMENT ON TABLE notifications IS 'Delivered alert notifications with deduplication';
COMMENT ON CONSTRAINT notifications_dedupe ON notifications IS
    'Prevents duplicate notifications: one per alert per day per user';

-- ============================================================================
-- DLQ (DEAD LETTER QUEUE) TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS dlq (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Failed alert
    alert_id UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,

    -- Payload (for retry)
    payload JSONB NOT NULL,  -- {"message": "...", "channels": ["email", "inapp"]}

    -- Error tracking
    error_message TEXT,
    retry_count INT DEFAULT 0,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'retrying', 'failed', 'delivered')),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_retry_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_dlq_status ON dlq(status) WHERE status = 'pending';
CREATE INDEX idx_dlq_alert_id ON dlq(alert_id);
CREATE INDEX idx_dlq_created_at ON dlq(created_at);
CREATE INDEX idx_dlq_retry_count ON dlq(retry_count) WHERE retry_count < 5;

-- Comments
COMMENT ON TABLE dlq IS 'Dead letter queue for failed alert notifications with retry logic';
COMMENT ON COLUMN dlq.retry_count IS 'Number of retry attempts (max: 5)';
COMMENT ON COLUMN dlq.status IS 'DLQ entry status: pending, retrying, failed, delivered';

-- ============================================================================
-- REBALANCE_SUGGESTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS rebalance_suggestions (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL,

    -- Suggestions
    suggested_trades JSONB NOT NULL,  -- [{"symbol": "AAPL", "action": "BUY", "shares": 10}, ...]

    -- Risk metrics
    expected_te NUMERIC,  -- Expected tracking error after rebalance
    expected_return NUMERIC,
    expected_risk NUMERIC,

    -- Optimization parameters
    optimization_method TEXT,  -- "mean_variance", "min_variance", etc.
    constraints_json JSONB,  -- {"max_te": 0.02, "min_weight": 0.01, ...}

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'executed')),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_rebalance_suggestions_portfolio_id ON rebalance_suggestions(portfolio_id);
CREATE INDEX idx_rebalance_suggestions_status ON rebalance_suggestions(status);
CREATE INDEX idx_rebalance_suggestions_created_at ON rebalance_suggestions(created_at DESC);

-- Comments
COMMENT ON TABLE rebalance_suggestions IS 'Portfolio rebalance suggestions from optimizer';
COMMENT ON COLUMN rebalance_suggestions.expected_te IS 'Expected tracking error (annualized)';
COMMENT ON COLUMN rebalance_suggestions.optimization_method IS 'Optimization algorithm used';

-- ============================================================================
-- RECONCILIATION_RESULTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS reconciliation_results (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL,

    -- Provenance
    pricing_pack_id TEXT NOT NULL,
    ledger_commit_hash TEXT NOT NULL,

    -- Reconciliation
    error_bps NUMERIC NOT NULL,  -- Error in basis points
    passed BOOLEAN NOT NULL,  -- True if error <= 1.0 bp

    -- Details
    ledger_nav NUMERIC NOT NULL,
    pricing_nav NUMERIC NOT NULL,
    difference NUMERIC NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reconciliation_results_portfolio_id ON reconciliation_results(portfolio_id);
CREATE INDEX idx_reconciliation_results_pricing_pack_id ON reconciliation_results(pricing_pack_id);
CREATE INDEX idx_reconciliation_results_passed ON reconciliation_results(passed);
CREATE INDEX idx_reconciliation_results_created_at ON reconciliation_results(created_at DESC);

-- Comments
COMMENT ON TABLE reconciliation_results IS 'Ledger vs pricing pack reconciliation results';
COMMENT ON COLUMN reconciliation_results.error_bps IS 'NAV error in basis points (must be <= 1.0)';
COMMENT ON COLUMN reconciliation_results.passed IS 'True if reconciliation passed (error <= 1bp)';

-- ============================================================================
-- LEDGER_TRANSACTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS ledger_transactions (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Provenance
    ledger_commit_hash TEXT NOT NULL,

    -- Transaction data
    date DATE NOT NULL,
    account TEXT NOT NULL,  -- Beancount account (e.g., "Assets:Portfolio:123:AAPL")
    amount NUMERIC NOT NULL,
    currency TEXT NOT NULL,
    narration TEXT,

    -- Metadata
    metadata_json JSONB,  -- Additional Beancount metadata

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ledger_transactions_ledger_commit_hash ON ledger_transactions(ledger_commit_hash);
CREATE INDEX idx_ledger_transactions_date ON ledger_transactions(date DESC);
CREATE INDEX idx_ledger_transactions_account ON ledger_transactions(account);

-- Comments
COMMENT ON TABLE ledger_transactions IS 'Parsed Beancount ledger transactions';
COMMENT ON COLUMN ledger_transactions.account IS 'Beancount account name (hierarchical)';
COMMENT ON COLUMN ledger_transactions.ledger_commit_hash IS 'Git commit hash of ledger repo';

-- ============================================================================
-- TRIGGER: Update updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_alerts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_alerts_updated_at
    BEFORE UPDATE ON alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_alerts_updated_at();

-- ============================================================================
-- SAMPLE DATA (Development)
-- ============================================================================

-- Sample alert (disabled in production)
-- INSERT INTO alerts (
--     user_id,
--     condition_json,
--     notify_email,
--     notify_inapp
-- ) VALUES (
--     '11111111-1111-1111-1111-111111111111',
--     '{"metric": "twr_ytd", "operator": ">", "threshold": 0.10}'::jsonb,
--     true,
--     true
-- );

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'Alerts and notifications schema created successfully' AS status;

SELECT COUNT(*) AS alerts_count FROM alerts;
SELECT COUNT(*) AS notifications_count FROM notifications;
SELECT COUNT(*) AS dlq_count FROM dlq;
SELECT COUNT(*) AS rebalance_suggestions_count FROM rebalance_suggestions;
SELECT COUNT(*) AS reconciliation_results_count FROM reconciliation_results;
SELECT COUNT(*) AS ledger_transactions_count FROM ledger_transactions;
