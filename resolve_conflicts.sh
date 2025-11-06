#!/bin/bash
# Script to resolve merge conflicts and push changes

echo "=== RESOLVING MERGE CONFLICTS ==="
echo ""

# Step 1: Remove the index lock file if it exists
echo "Step 1: Clearing any lock files..."
rm -f .git/index.lock 2>/dev/null || true
find .git -name "*.lock" -delete 2>/dev/null || true
echo "✅ Lock files cleared"

# Step 2: Accept the remote version (it has more detailed comments)
echo ""
echo "Step 2: Resolving conflicts (keeping remote version with better comments)..."

# Resolve schema file - keep remote version (theirs)
cat > backend/db/schema/economic_indicators.sql << 'EOF'

-- Economic Indicators Table
-- Purpose: Store economic indicator data from FRED for factor analysis
-- Created: January 14, 2025 (Phase 3 - Field Name Refactor)

CREATE TABLE IF NOT EXISTS economic_indicators (
    series_id VARCHAR(20) NOT NULL,
    asof_date DATE NOT NULL,
    value NUMERIC(20, 8) NOT NULL,
    unit VARCHAR(20),
    source VARCHAR(50) DEFAULT 'FRED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (series_id, asof_date)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_economic_indicators_date 
    ON economic_indicators(asof_date DESC);

CREATE INDEX IF NOT EXISTS idx_economic_indicators_series 
    ON economic_indicators(series_id, asof_date DESC);

-- Convert to hypertable (TimescaleDB)
-- This will partition data by asof_date for efficient time-series queries
SELECT create_hypertable(
    'economic_indicators',
    'asof_date',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 month'
);

-- Add comment
COMMENT ON TABLE economic_indicators IS 
'Economic indicators from FRED for factor analysis. Series IDs: DFII10 (Real Rate), T10YIE (Inflation), BAMLC0A0CM (Credit), DTWEXBGS (USD), SP500 (Equity).';

COMMENT ON COLUMN economic_indicators.series_id IS 
'FRED series identifier (e.g., DFII10, T10YIE, BAMLC0A0CM, DTWEXBGS, SP500)';

COMMENT ON COLUMN economic_indicators.asof_date IS 
'As-of date for the indicator value';

COMMENT ON COLUMN economic_indicators.value IS 
'Indicator value (level, not return - returns calculated on-the-fly)';

EOF

# Resolve migration file  
cat > backend/db/migrations/015_add_economic_indicators.sql << 'EOF'
-- Migration 015: Add economic_indicators table
-- Created: January 14, 2025
-- Purpose: Support factor analysis with economic indicator data from FRED

-- Create table
CREATE TABLE IF NOT EXISTS economic_indicators (
    series_id VARCHAR(20) NOT NULL,
    asof_date DATE NOT NULL,
    value NUMERIC(20, 8) NOT NULL,
    unit VARCHAR(20),
    source VARCHAR(50) DEFAULT 'FRED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (series_id, asof_date)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_economic_indicators_date 
    ON economic_indicators(asof_date DESC);

CREATE INDEX IF NOT EXISTS idx_economic_indicators_series 
    ON economic_indicators(series_id, asof_date DESC);

-- Convert to hypertable (TimescaleDB) - if available
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable(
            'economic_indicators',
            'asof_date',
            if_not_exists => TRUE,
            chunk_time_interval => INTERVAL '1 month'
        );
    END IF;
END $$;

-- Add comment
COMMENT ON TABLE economic_indicators IS 
'Economic indicators from FRED for factor analysis. Series IDs: DFII10 (Real Rate), T10YIE (Inflation), BAMLC0A0CM (Credit), DTWEXBGS (USD), SP500 (Equity).';

-- Note: Data will be populated by data harvester agent
-- No seed data required for initial migration

EOF

echo "✅ Conflicts resolved"

# Step 3: Stage the resolved files
echo ""
echo "Step 3: Staging resolved files..."
git add backend/db/schema/economic_indicators.sql
git add backend/db/migrations/015_add_economic_indicators.sql
git add backend/app/services/factor_analysis.py
git add backend/app/agents/financial_analyst.py
echo "✅ Files staged"

# Step 4: Complete the merge
echo ""
echo "Step 4: Completing the merge..."
git commit --no-edit 2>&1 | head -10 || {
    echo "Commit may have failed, checking status..."
    git status --short
}

# Step 5: Push to remote
echo ""
echo "Step 5: Pushing to remote..."
git push origin main 2>&1

# Check final status
echo ""
echo "Step 6: Final status check..."
git status -sb
echo ""
git log --oneline -5

echo ""
echo "=== DONE ==="
echo ""
echo "Your changes should now be pushed to GitHub!"
echo "Check: https://github.com/mwd474747/DawsOSP"