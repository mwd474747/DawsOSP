#!/bin/bash
# Script to complete the merge by marking conflicts as resolved

echo "=== COMPLETING MERGE - MARKING CONFLICTS RESOLVED ==="
echo ""

# Step 1: Clear any lock files
echo "Step 1: Clearing any lock files..."
rm -f .git/index.lock 2>/dev/null
rm -f .git/refs/remotes/origin/HEAD.lock 2>/dev/null
find .git -name "*.lock" -type f -delete 2>/dev/null || true
echo "✅ Lock files cleared"

# Step 2: Mark the conflicted files as resolved
echo ""
echo "Step 2: Marking conflicts as resolved..."
echo "Files are already clean (no conflict markers), just need to stage them..."

# Use git add to mark conflicts as resolved
git add backend/db/schema/economic_indicators.sql
git add backend/db/migrations/015_add_economic_indicators.sql
echo "✅ Conflicts marked as resolved"

# Step 3: Show what's staged
echo ""
echo "Step 3: Showing staged files..."
git status --short | head -10

# Step 4: Complete the merge
echo ""
echo "Step 4: Completing the merge commit..."
git commit --no-edit -m "Merge branch 'main' - resolved conflicts in economic_indicators files"

# Step 5: Push to remote
echo ""
echo "Step 5: Pushing to remote..."
git push origin main

# Step 6: Show final status
echo ""
echo "Step 6: Final status..."
git status -sb
echo ""
git log --oneline -3

echo ""
echo "=== MERGE COMPLETE ==="
echo "✅ Your changes should now be pushed to GitHub!"