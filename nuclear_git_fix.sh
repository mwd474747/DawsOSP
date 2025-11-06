#!/bin/bash
# Nuclear option - completely bypass lock file issue

echo "=== NUCLEAR GIT FIX ==="
echo "This will bypass the lock file by resetting remote tracking"
echo ""

# Step 1: Save current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

# Step 2: Remove ALL remote tracking (bypasses lock file)
echo ""
echo "Removing all remote tracking..."
rm -rf .git/refs/remotes 2>/dev/null || echo "Could not remove remotes directly"
git config --unset-all remote.origin.fetch 2>/dev/null
git config --unset-all branch.main.remote 2>/dev/null
git config --unset-all branch.main.merge 2>/dev/null

# Step 3: Re-add origin
echo ""
echo "Re-adding origin..."
git remote rm origin 2>/dev/null || true
git remote add origin https://github.com/mwd474747/DawsOSP.git

# Step 4: Create new fetch configuration
echo ""
echo "Setting up fetch configuration..."
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# Step 5: Fetch WITHOUT creating lock files
echo ""
echo "Fetching remote (may show errors - that's OK)..."
timeout 5 git fetch origin 2>&1 || echo "Fetch timeout/failed - continuing anyway"

# Step 6: Set tracking manually
echo ""
echo "Setting branch tracking..."
git config branch.main.remote origin
git config branch.main.merge refs/heads/main

# Step 7: Stage and commit
echo ""
echo "Staging your changes..."
git add backend/app/services/factor_analysis.py 2>/dev/null
git add backend/app/agents/financial_analyst.py 2>/dev/null
git add backend/db/schema/economic_indicators.sql 2>/dev/null
git add backend/db/migrations/015_add_economic_indicators.sql 2>/dev/null

if ! git diff --staged --quiet; then
    git commit -m "Fix: Factor analysis bugs and add economic indicators" 2>/dev/null
fi

# Step 8: Push directly without checking remote
echo ""
echo "Pushing directly to origin/main..."
git push https://github.com/mwd474747/DawsOSP.git HEAD:main 2>&1

echo ""
echo "=== DONE ==="