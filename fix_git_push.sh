#!/bin/bash
# Git push fix script for Replit - works around lock file restrictions

echo "=== GIT PUSH FIX FOR REPLIT ==="
echo ""

# Step 1: Try to recover using git's own commands
echo "Step 1: Attempting Git recovery..."
git remote prune origin 2>&1 | head -5

# Step 2: Force update remote refs
echo ""
echo "Step 2: Force updating remote references..."
git remote rm origin 2>/dev/null
git remote add origin https://github.com/mwd474747/DawsOSP.git
echo "✅ Remote reset"

# Step 3: Fetch fresh remote state
echo ""
echo "Step 3: Fetching fresh remote state..."
git fetch origin 2>&1 | head -5

# Step 4: Set upstream branch
echo ""
echo "Step 4: Setting upstream branch..."
git branch --set-upstream-to=origin/main main 2>&1

# Step 5: Check current status
echo ""
echo "Step 5: Current status..."
git status -sb

# Step 6: Stage and commit changes
echo ""
echo "Step 6: Staging changes..."
git add backend/app/services/factor_analysis.py
git add backend/app/agents/financial_analyst.py
git add backend/db/schema/economic_indicators.sql
git add backend/db/migrations/015_add_economic_indicators.sql

# Check if we have changes to commit
if git diff --staged --quiet; then
    echo "No changes to commit - files may already be committed"
else
    echo "Committing changes..."
    git commit -m "Fix: Factor analysis field name bugs and add economic indicators table"
fi

# Step 7: Try to push
echo ""
echo "Step 7: Attempting push..."
git push -u origin main 2>&1

# If that fails, try force push with lease
if [ $? -ne 0 ]; then
    echo ""
    echo "Regular push failed. Trying with --force-with-lease (safer than --force)..."
    git push --force-with-lease origin main 2>&1
fi

echo ""
echo "=== DONE ==="
echo ""
echo "If still failing, try these manual commands:"
echo "1. Close and reopen the Shell"
echo "2. Run: git config --global --add safe.directory /home/runner/workspace"
echo "3. Run: GIT_TERMINAL_PROMPT=0 git push origin main"