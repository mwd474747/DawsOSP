-- Migration: Add channels column to alerts table
-- Date: 2025-10-27
-- Purpose: Support unified channel configuration (alternative to notify_email/notify_inapp)

-- Add channels JSONB column (optional, allows gradual migration)
ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS channels JSONB DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN alerts.channels IS 'Unified notification channels config (alternative to notify_email/notify_inapp). Format: {"inapp": true, "email": false}';

-- Create index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_alerts_channels ON alerts USING GIN (channels);

-- Note: This migration is ADDITIVE (does not remove notify_email/notify_inapp)
-- to maintain backward compatibility. The AlertService.normalize_channels()
-- method supports both formats:
-- 1. Legacy format: notify_email, notify_inapp (boolean columns)
-- 2. New format: channels (JSONB column)
--
-- Migration strategy:
-- 1. Add channels column (this migration) ✅
-- 2. Deploy code that supports both formats ✅
-- 3. Gradually backfill channels from notify_email/notify_inapp (future migration)
-- 4. Update application to write to channels column (future)
-- 5. Deprecate notify_email/notify_inapp columns (future)
