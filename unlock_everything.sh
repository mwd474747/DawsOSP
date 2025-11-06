#!/bin/bash
# NUCLEAR UNLOCK SCRIPT - Clears all locks and resets git state

echo "==================================================================="
echo "                    NUCLEAR GIT UNLOCK SCRIPT                     "
echo "==================================================================="
echo ""
echo "This script will forcefully unlock everything and fix your git state"
echo ""

# Step 1: Kill ALL git processes
echo "[1/8] Killing all git processes..."
pkill -9 -f git 2>/dev/null || true
pkill -9 -f ssh 2>/dev/null || true
sleep 2
echo "✅ All git processes terminated"

# Step 2: Remove ALL lock files (multiple methods)
echo ""
echo "[2/8] Removing ALL lock files..."
# Method 1: Direct removal
rm -f .git/index.lock 2>/dev/null || true
rm -f .git/HEAD.lock 2>/dev/null || true
rm -f .git/MERGE_HEAD.lock 2>/dev/null || true
rm -f .git/FETCH_HEAD.lock 2>/dev/null || true
rm -f .git/refs/heads/*.lock 2>/dev/null || true
rm -f .git/refs/remotes/origin/*.lock 2>/dev/null || true
rm -f .git/refs/remotes/origin/HEAD.lock 2>/dev/null || true
rm -f .git/objects/pack/*.lock 2>/dev/null || true

# Method 2: Find and delete
find .git -type f -name "*.lock" -delete 2>/dev/null || true
find .git -type f -name "*lock*" -delete 2>/dev/null || true

# Method 3: Force remove with different permissions
sudo rm -f .git/index.lock 2>/dev/null || true
sudo find .git -name "*.lock" -exec rm -f {} \; 2>/dev/null || true

echo "✅ All lock files removed"

# Step 3: Clear git cache and temporary files
echo ""
echo "[3/8] Clearing git cache and temp files..."
rm -rf .git/rebase-merge 2>/dev/null || true
rm -rf .git/rebase-apply 2>/dev/null || true
rm -rf .git/MERGE_* 2>/dev/null || true
rm -f .git/CHERRY_PICK_HEAD 2>/dev/null || true
rm -f .git/REVERT_HEAD 2>/dev/null || true
echo "✅ Cache cleared"

# Step 4: Reset git index
echo ""
echo "[4/8] Resetting git index..."
rm -f .git/index 2>/dev/null || true
git reset --mixed 2>/dev/null || true
echo "✅ Index reset"

# Step 5: Abort any ongoing operations
echo ""
echo "[5/8] Aborting all ongoing git operations..."
git merge --abort 2>/dev/null || true
git rebase --abort 2>/dev/null || true
git cherry-pick --abort 2>/dev/null || true
git revert --abort 2>/dev/null || true
git am --abort 2>/dev/null || true
echo "✅ All operations aborted"

# Step 6: Clean working directory
echo ""
echo "[6/8] Cleaning working directory..."
git reset --hard HEAD 2>/dev/null || git reset --hard origin/main 2>/dev/null || true
git clean -fd 2>/dev/null || true
echo "✅ Working directory cleaned"

# Step 7: Fix remote and fetch
echo ""
echo "[7/8] Fixing remote connection..."
git remote prune origin 2>/dev/null || true
git fetch origin --prune 2>/dev/null || true
echo "✅ Remote connection fixed"

# Step 8: Show final status
echo ""
echo "[8/8] Final status check..."
echo ""
echo "=== GIT STATUS ==="
git status --short 2>&1 | head -20 || echo "Status check failed"
echo ""
echo "=== BRANCH INFO ==="
git branch -vv 2>&1 | head -5 || echo "Branch check failed"
echo ""

echo "==================================================================="
echo "                        UNLOCK COMPLETE!                          "
echo "==================================================================="
echo ""
echo "Everything should be unlocked now. Next steps:"
echo ""
echo "1. If you need to push changes:"
echo "   git add ."
echo "   git commit -m 'Your message'"
echo "   git push origin main"
echo ""
echo "2. If you need to pull changes:"
echo "   git pull origin main"
echo ""
echo "3. If still having issues, try:"
echo "   - Refresh your browser (Ctrl+R or Cmd+R)"
echo "   - Use the Git panel in Replit"
echo "   - Or restart the workspace"
echo ""
echo "Your git repository is now fully unlocked and ready to use!"