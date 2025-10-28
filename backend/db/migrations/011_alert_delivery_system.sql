-- Migration: Add alert delivery system tables
-- Date: 2025-10-27
-- Purpose: Support alert delivery with DLQ and deduplication

-- Table for tracking alert deliveries (deduplication)
CREATE TABLE IF NOT EXISTS alert_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id VARCHAR(255) NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- MD5 hash of alert content for deduplication
    delivery_methods JSONB NOT NULL,   -- Array of delivery methods attempted
    delivered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_alert_deliveries_alert_id ON alert_deliveries (alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_deliveries_content_hash ON alert_deliveries (content_hash);
CREATE INDEX IF NOT EXISTS idx_alert_deliveries_delivered_at ON alert_deliveries (delivered_at);

-- Table for Dead Letter Queue (failed alerts)
CREATE TABLE IF NOT EXISTS alert_dlq (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id VARCHAR(255) NOT NULL,
    alert_data JSONB NOT NULL,        -- Full alert data
    error_message TEXT NOT NULL,      -- Error that caused failure
    retry_count INTEGER DEFAULT 0,    -- Number of retry attempts
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_retry_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_alert_dlq_alert_id ON alert_dlq (alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_dlq_created_at ON alert_dlq (created_at);
CREATE INDEX IF NOT EXISTS idx_alert_dlq_retry_count ON alert_dlq (retry_count);

-- Table for alert retry scheduling
CREATE TABLE IF NOT EXISTS alert_retries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id VARCHAR(255) NOT NULL,
    alert_data JSONB NOT NULL,
    delivery_methods JSONB NOT NULL,
    retry_count INTEGER NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' -- pending, processing, completed, failed
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_alert_retries_scheduled_at ON alert_retries (scheduled_at);
CREATE INDEX IF NOT EXISTS idx_alert_retries_status ON alert_retries (status);
CREATE INDEX IF NOT EXISTS idx_alert_retries_alert_id ON alert_retries (alert_id);

-- Add RLS policies for multi-tenancy
ALTER TABLE alert_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_dlq ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_retries ENABLE ROW LEVEL SECURITY;

-- RLS policies (assuming user_id is available in context)
-- Note: These policies assume alerts are user-specific
-- Adjust based on actual alert ownership model

CREATE POLICY alert_deliveries_user_isolation ON alert_deliveries
    FOR ALL TO dawsos_app
    USING (true); -- TODO: Add proper user isolation when alert ownership is defined

CREATE POLICY alert_dlq_user_isolation ON alert_dlq
    FOR ALL TO dawsos_app
    USING (true); -- TODO: Add proper user isolation when alert ownership is defined

CREATE POLICY alert_retries_user_isolation ON alert_retries
    FOR ALL TO dawsos_app
    USING (true); -- TODO: Add proper user isolation when alert ownership is defined

-- Add comments for documentation
COMMENT ON TABLE alert_deliveries IS 'Tracks successful alert deliveries for deduplication';
COMMENT ON TABLE alert_dlq IS 'Dead Letter Queue for failed alert deliveries';
COMMENT ON TABLE alert_retries IS 'Scheduled retries for failed alert deliveries';

COMMENT ON COLUMN alert_deliveries.content_hash IS 'MD5 hash of alert content for deduplication';
COMMENT ON COLUMN alert_deliveries.delivery_methods IS 'JSON array of delivery methods attempted';

COMMENT ON COLUMN alert_dlq.alert_data IS 'Full alert data including condition and context';
COMMENT ON COLUMN alert_dlq.error_message IS 'Error message that caused delivery failure';
COMMENT ON COLUMN alert_dlq.retry_count IS 'Number of retry attempts made';

COMMENT ON COLUMN alert_retries.scheduled_at IS 'When the retry should be attempted';
COMMENT ON COLUMN alert_retries.status IS 'Current status of the retry attempt';
