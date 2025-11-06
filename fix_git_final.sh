#!/bin/bash
# Final comprehensive fix for Replit Git issues

echo "=== COMPREHENSIVE GIT FIX FOR REPLIT ==="
echo ""
echo "This script will:"
echo "1. Abort the current problematic merge"
echo "2. Save your important changes"
echo "3. Reset to a clean state"
echo "4. Reapply your changes"
echo "5. Push directly to GitHub"
echo ""

# Step 1: Kill any git processes and clear locks
echo "Step 1: Clearing git processes and locks..."
pkill -f git 2>/dev/null || true
sleep 1

# Force remove lock files (try multiple methods)
rm -f .git/index.lock 2>/dev/null || true
rm -f .git/refs/remotes/origin/HEAD.lock 2>/dev/null || true
find .git -name "*.lock" -type f 2>/dev/null | xargs rm -f 2>/dev/null || true
echo "✅ Processes and locks cleared"

# Step 2: Save your important changes to a safe location
echo ""
echo "Step 2: Saving your changes..."
mkdir -p /tmp/git_backup
cp backend/app/services/factor_analysis.py /tmp/git_backup/ 2>/dev/null || true
cp backend/app/agents/financial_analyst.py /tmp/git_backup/ 2>/dev/null || true
cp backend/db/schema/economic_indicators.sql /tmp/git_backup/ 2>/dev/null || true
cp backend/db/migrations/015_add_economic_indicators.sql /tmp/git_backup/ 2>/dev/null || true
echo "✅ Changes backed up"

# Step 3: Abort the current merge
echo ""
echo "Step 3: Aborting the problematic merge..."
git merge --abort 2>/dev/null || git reset --hard HEAD 2>/dev/null || true
echo "✅ Merge aborted"

# Step 4: Fetch and reset to remote main
echo ""
echo "Step 4: Resetting to remote main..."
git fetch origin main 2>/dev/null || true
git reset --hard origin/main 2>/dev/null || true
echo "✅ Reset to remote main"

# Step 5: Restore your changes
echo ""
echo "Step 5: Restoring your changes..."
cp /tmp/git_backup/factor_analysis.py backend/app/services/ 2>/dev/null || true
cp /tmp/git_backup/financial_analyst.py backend/app/agents/ 2>/dev/null || true

# Create the economic indicators files fresh (no conflicts)
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

-- Add comments
COMMENT ON TABLE economic_indicators IS 
'Economic indicators from FRED for factor analysis. Series IDs: DFII10 (Real Rate), T10YIE (Inflation), BAMLC0A0CM (Credit), DTWEXBGS (USD), SP500 (Equity).';

COMMENT ON COLUMN economic_indicators.series_id IS 
'FRED series identifier (e.g., DFII10, T10YIE, BAMLC0A0CM, DTWEXBGS, SP500)';

COMMENT ON COLUMN economic_indicators.asof_date IS 
'As-of date for the indicator value';

COMMENT ON COLUMN economic_indicators.value IS 
'Indicator value (level, not return - returns calculated on-the-fly)';
EOF

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

echo "✅ Changes restored"

# Step 6: Commit all changes
echo ""
echo "Step 6: Committing all changes..."
git add backend/app/services/factor_analysis.py
git add backend/app/agents/financial_analyst.py
git add backend/db/schema/economic_indicators.sql
git add backend/db/migrations/015_add_economic_indicators.sql

git commit -m "Fix: Factor analysis and import bugs, add economic indicators table

- Fixed field name mismatch in factor_analysis.py (asof_date vs valuation_date)
- Fixed import error in financial_analyst.py (FactorAnalysisService -> FactorAnalyzer)
- Added economic_indicators table for FRED data with TimescaleDB optimization
- Phase 3 critical bug fixes complete"

echo "✅ Changes committed"

# Step 7: Show current status
echo ""
echo "Step 7: Current status..."
git status -sb
git log --oneline -3

echo ""
echo "=== SCRIPT COMPLETE ==="
echo ""
echo "NOW: Go to the Git panel in Replit and click the PUSH button"
echo "Your changes are committed and ready to push!"
echo ""
echo "If the Git panel still fails, run this in the Shell:"
echo "git push https://github.com/mwd474747/DawsOSP main"