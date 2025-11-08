#!/bin/bash

echo "=== GitHub Branch Cleanup Script ==="
echo ""
echo "Current branches:"
git branch -a | grep -E "(main|2025-11-07)"
echo ""

# Delete the old Replit branch from GitHub
echo "Deleting obsolete branch from GitHub..."
git push origin --delete 2025-11-07-qxuh-6XUZZ

# Clean up local references to deleted remote branches
echo "Cleaning up local references..."
git remote prune origin

# Delete local replit-agent branch if not needed
if git show-ref --verify --quiet refs/heads/replit-agent; then
    echo "Deleting local replit-agent branch..."
    git branch -d replit-agent 2>/dev/null || git branch -D replit-agent
fi

# Show final state
echo ""
echo "=== Cleanup Complete ==="
echo "Remaining branches:"
git branch -a
echo ""
echo "Your repository now has only the main branch!"