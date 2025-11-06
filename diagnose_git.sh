#!/bin/bash
# Comprehensive git diagnosis script

echo "=== GIT DIAGNOSIS STARTING ==="
echo ""

# 1. Check current branch
echo "1. CURRENT BRANCH:"
git branch --show-current
echo ""

# 2. Check remote configuration
echo "2. REMOTE CONFIGURATION:"
git remote -v
echo ""

# 3. Check if there are uncommitted changes
echo "3. UNCOMMITTED CHANGES:"
git status --short
echo ""

# 4. Check if local is ahead/behind remote
echo "4. BRANCH STATUS VS REMOTE:"
git status -sb
echo ""

# 5. Check last commit
echo "5. LAST COMMIT:"
git log -1 --oneline
echo ""

# 6. Check if remote is reachable
echo "6. REMOTE CONNECTIVITY:"
git ls-remote --heads origin 2>&1 | head -3
echo ""

# 7. Check for divergence
echo "7. DIVERGENCE CHECK:"
git fetch origin 2>&1
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u} 2>/dev/null)
BASE=$(git merge-base HEAD @{u} 2>/dev/null)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✓ Up to date with remote"
elif [ "$LOCAL" = "$BASE" ]; then
    echo "⚠ Need to pull - remote has new commits"
elif [ "$REMOTE" = "$BASE" ]; then
    echo "✓ Need to push - local is ahead"
else
    echo "⚠ DIVERGED - local and remote have different commits"
    echo "  Local commit: $(git log -1 --oneline HEAD)"
    echo "  Remote commit: $(git log -1 --oneline @{u} 2>/dev/null || echo 'Cannot fetch')"
fi
echo ""

# 8. Check for merge conflicts
echo "8. MERGE STATUS:"
git status | grep -E "(both|conflict|Unmerged)" || echo "No merge conflicts"
echo ""

# 9. Try a dry run push
echo "9. PUSH DRY RUN:"
git push --dry-run origin HEAD 2>&1
echo ""

# 10. Check git config
echo "10. GIT USER CONFIG:"
git config user.name
git config user.email
echo ""

echo "=== DIAGNOSIS COMPLETE ==="
echo ""
echo "SUGGESTED ACTIONS:"
echo "If diverged: git pull --rebase origin main"
echo "If behind: git pull origin main"
echo "If ahead: git push origin main"
echo "If detached: git checkout main"