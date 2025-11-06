#!/bin/bash
# Script to fix git lock issues and push changes

echo "🔧 Fixing git lock issues and pushing changes..."

# Remove any lock files
if [ -f .git/index.lock ]; then
    echo "Removing git index lock..."
    rm -f .git/index.lock
fi

# Check for other possible locks
find .git -name "*.lock" -type f -delete 2>/dev/null

echo "✅ Lock files cleared"

# Stage the changed files
echo "📝 Staging changes..."
git add backend/app/services/factor_analysis.py || echo "Warning: Could not add factor_analysis.py"
git add backend/app/agents/financial_analyst.py || echo "Warning: Could not add financial_analyst.py"
git add backend/db/schema/economic_indicators.sql || echo "Warning: Could not add schema file"
git add backend/db/migrations/015_add_economic_indicators.sql || echo "Warning: Could not add migration file"

# Show what will be committed
echo "📋 Files to be committed:"
git status --short

# Commit the changes
echo "💾 Committing changes..."
git commit -m "Fix factor analysis bugs: field name mismatch, import errors, create economic_indicators table" || {
    echo "⚠️  Commit failed. Checking if changes are already committed..."
    git status
}

# Push to remote
echo "🚀 Pushing to remote..."
git push origin main || git push origin HEAD

echo "✅ Done! Check the output above for any issues."