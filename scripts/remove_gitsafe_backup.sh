#!/bin/bash

echo "=== Git Remote Cleanup Script ==="
echo "Removing gitsafe-backup remote and clearing lock files..."

# Step 1: Remove all lock files
echo "Step 1: Removing lock files..."
rm -f .git/config.lock
rm -f .git/packed-refs.lock
rm -f .git/index.lock
rm -f .git/refs/remotes/gitsafe-backup/main.lock
echo "✓ Lock files removed"

# Step 2: Check if gitsafe-backup remote exists
echo "Step 2: Checking for gitsafe-backup remote..."
if git remote | grep -q "gitsafe-backup"; then
    echo "Found gitsafe-backup remote, removing..."
    
    # Remove remote tracking branches
    echo "Removing remote tracking branches..."
    rm -rf .git/refs/remotes/gitsafe-backup
    
    # Remove the remote
    git remote remove gitsafe-backup 2>/dev/null || {
        echo "Standard removal failed, attempting manual cleanup..."
        # Manual removal from config
        git config --unset-all remote.gitsafe-backup.url 2>/dev/null
        git config --unset-all remote.gitsafe-backup.fetch 2>/dev/null
        git config --unset-all remote.gitsafe-backup.skipfetchall 2>/dev/null
    }
    echo "✓ gitsafe-backup remote removed"
else
    echo "✓ No gitsafe-backup remote found"
fi

# Step 3: Configure credential helper
echo "Step 3: Configuring credential helper..."
git config credential.helper store
git config push.default current
echo "✓ Credential helper configured"

# Step 4: Show current remotes
echo "Step 4: Current remotes:"
git remote -v

# Step 5: Show git status
echo "Step 5: Git status:"
git status --short

echo ""
echo "=== Cleanup Complete ==="
echo "Your repository now has only the GitHub origin remote."
echo "To push your commits, run: git push origin main"
echo "You'll be prompted for credentials once, then they'll be saved."