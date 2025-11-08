-- Migration 014: Add Deprecation Comment for Legacy quantity Field
-- Date: 2025-01-14
-- Purpose: Add deprecation comment to legacy quantity field in lots table
-- Priority: P1 (Documentation for field naming consistency)

-- ============================================================================
-- CONTEXT
-- ============================================================================
-- The lots table has a legacy 'quantity' field that was replaced by
-- 'quantity_open' and 'quantity_original' in Migration 007.
--
-- Migration 007 added:
-- - quantity_original: Original quantity when lot was created
-- - quantity_open: Remaining open quantity (decreases on sells)
--
-- The legacy 'quantity' field was kept for backwards compatibility but is
-- deprecated and should not be used in new code.
--
-- This migration adds a deprecation comment to document this.
-- ============================================================================

BEGIN;

-- Add deprecation comment to legacy quantity field
COMMENT ON COLUMN lots.quantity IS 
'⚠️ DEPRECATED: Use quantity_open for current positions. This field is kept for backwards compatibility (Migration 007) but will be removed in a future version. Do not use in new code.';

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. This migration only adds documentation - no schema changes
-- 2. The quantity field is still maintained for backwards compatibility
-- 3. All new code should use quantity_open instead of quantity
-- 4. See FIELD_NAMING_COMPREHENSIVE_ANALYSIS.md for complete migration plan
-- ============================================================================

SELECT 'Migration 014: Deprecation comment added to legacy quantity field' AS status;

