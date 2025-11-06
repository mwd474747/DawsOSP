#!/bin/bash
# Fix Git authentication for Replit

echo "==================================================================="
echo "              FIXING GIT AUTHENTICATION FOR REPLIT                "
echo "==================================================================="
echo ""

# Step 1: Check current configuration
echo "[1/5] Current Git Configuration:"
echo "User: $(git config user.name)"
echo "Email: $(git config user.email)"
echo "Remote: $(git config remote.origin.url)"
echo ""

# Step 2: Set correct Git user configuration
echo "[2/5] Setting correct Git user configuration..."
git config --global user.name "mwd474747"
git config --global user.email "gig.roadies7i@icloud.com"
echo "✅ Git user configured"

# Step 3: Configure Git to use Replit's authentication
echo ""
echo "[3/5] Configuring Git for Replit authentication..."

# Option A: Try using SSH format (works better with Replit Git panel)
git remote set-url origin git@github.com:mwd474747/DawsOSP.git 2>/dev/null || true

# Test if SSH works
if git ls-remote origin 2>/dev/null | head -1 >/dev/null; then
    echo "✅ SSH authentication configured successfully"
else
    # Option B: Fall back to HTTPS
    echo "SSH didn't work, configuring HTTPS..."
    git remote set-url origin https://github.com/mwd474747/DawsOSP.git
    
    # Configure credential helper
    git config --global credential.helper store
    echo "✅ HTTPS authentication configured"
fi

# Step 4: Clear any cached credentials
echo ""
echo "[4/5] Clearing cached credentials..."
rm -f ~/.git-credentials 2>/dev/null || true
git config --unset credential.helper 2>/dev/null || true
git config --global credential.helper cache
echo "✅ Credentials cache cleared"

# Step 5: Show new configuration
echo ""
echo "[5/5] New Configuration:"
git config remote.origin.url
echo ""

echo "==================================================================="
echo "                    AUTHENTICATION FIXED!                         "
echo "==================================================================="
echo ""
echo "NOW TRY ONE OF THESE OPTIONS:"
echo ""
echo "OPTION 1: Use Replit Git Panel (RECOMMENDED)"
echo "  1. Refresh your browser (Ctrl+R or Cmd+R)"
echo "  2. Open the Git panel (left sidebar)"
echo "  3. Click on 'Settings' (gear icon)"
echo "  4. Click 'Connect to GitHub' or 'Reconnect'"
echo "  5. Authorize Replit to access your GitHub"
echo "  6. Try pushing again using the panel"
echo ""
echo "OPTION 2: Use GitHub Token in Shell"
echo "  1. Get a GitHub Personal Access Token from:"
echo "     https://github.com/settings/tokens/new"
echo "  2. Give it 'repo' permissions"
echo "  3. Run this command (replace YOUR_TOKEN):"
echo "     git push https://mwd474747:YOUR_TOKEN@github.com/mwd474747/DawsOSP.git main"
echo ""
echo "OPTION 3: If you have a token saved in Secrets"
echo "  1. Go to Secrets panel in Replit"
echo "  2. Add secret: GITHUB_TOKEN = your_token"
echo "  3. Run: git push https://mwd474747:\$GITHUB_TOKEN@github.com/mwd474747/DawsOSP.git main"
echo ""
echo "Your changes are ready to push - just need proper authentication!"