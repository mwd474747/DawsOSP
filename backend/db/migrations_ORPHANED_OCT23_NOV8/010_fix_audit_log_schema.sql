-- Fix Audit Log Schema Migration
-- Created: 2025-10-27
-- Purpose: Standardize audit_log.details as JSONB for proper structured data

-- Change details column back to JSONB for structured data
ALTER TABLE audit_log ALTER COLUMN details TYPE JSONB USING details::JSONB;

-- Add comment
COMMENT ON COLUMN audit_log.details IS 'Structured JSON data for audit event details';

-- Create index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_audit_log_details_gin ON audit_log USING GIN (details);

-- Test the change with a sample insert
INSERT INTO audit_log (event_type, user_id, details, created_at)
VALUES (
    'schema_test',
    NULL,
    '{"test": "jsonb", "nested": {"value": 123}}'::JSONB,
    NOW()
);

-- Verify the data was inserted correctly
SELECT event_type, details, details->>'test' as test_value, details->'nested'->>'value' as nested_value
FROM audit_log 
WHERE event_type = 'schema_test';

-- Clean up test data
DELETE FROM audit_log WHERE event_type = 'schema_test';
