-- Migration 001: Standardize field names
-- Date: November 4, 2025
-- CRITICAL: Must run BEFORE migration 002 (constraints)
-- WARNING: DO NOT modify pricing_packs table or its relationships (7+ tables depend on it)

BEGIN;

-- Standardize field names in lots table
-- Change qty_open and qty_original to use full 'quantity' word
ALTER TABLE lots 
  RENAME COLUMN qty_open TO quantity_open;

ALTER TABLE lots 
  RENAME COLUMN qty_original TO quantity_original;

-- Verify changes
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'lots' 
  AND column_name IN ('quantity_open', 'quantity_original');

COMMIT;

-- Rollback script (if needed):
-- BEGIN;
-- ALTER TABLE lots RENAME COLUMN quantity_open TO qty_open;
-- ALTER TABLE lots RENAME COLUMN quantity_original TO qty_original;
-- COMMIT;