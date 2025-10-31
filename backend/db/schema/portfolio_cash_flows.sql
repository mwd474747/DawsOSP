
-- Portfolio Cash Flows Table
-- Purpose: Track all cash movements (deposits, withdrawals, dividends) for MWR calculation
-- Created: 2025-10-31 (Phase 1.2 - METRICS_IMPLEMENTATION_PLAN.md)

CREATE TABLE IF NOT EXISTS portfolio_cash_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    flow_date DATE NOT NULL,
    flow_type VARCHAR(20) NOT NULL CHECK (flow_type IN ('DEPOSIT', 'WITHDRAWAL', 'DIVIDEND', 'INTEREST', 'FEE')),
    amount NUMERIC(20,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'CAD',
    transaction_id UUID REFERENCES transactions(id),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_portfolio_flow UNIQUE (portfolio_id, flow_date, flow_type, transaction_id)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_portfolio_cash_flows_portfolio 
    ON portfolio_cash_flows(portfolio_id, flow_date DESC);

CREATE INDEX IF NOT EXISTS idx_portfolio_cash_flows_date 
    ON portfolio_cash_flows(flow_date DESC);

CREATE INDEX IF NOT EXISTS idx_portfolio_cash_flows_transaction 
    ON portfolio_cash_flows(transaction_id) 
    WHERE transaction_id IS NOT NULL;

COMMENT ON TABLE portfolio_cash_flows IS 
'All cash flows (deposits, withdrawals, dividends) for MWR/IRR calculations. Extracted from transactions table.';

COMMENT ON COLUMN portfolio_cash_flows.amount IS 
'Cash flow amount (positive for inflows, negative for outflows)';

COMMENT ON COLUMN portfolio_cash_flows.transaction_id IS 
'Link to source transaction (NULL for manual cash flows)';
