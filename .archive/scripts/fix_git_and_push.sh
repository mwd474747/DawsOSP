#!/bin/bash

# Fix Git and Push Changes Script
echo "🔧 Fixing git lock issue and pushing changes..."

# Step 1: Remove the lock file
echo "Step 1: Removing git lock file..."
rm -f .git/index.lock

# Step 2: Check git status
echo "Step 2: Checking git status..."
git status

# Step 3: Add all changes
echo "Step 3: Adding all changes..."
git add -A

# Step 4: Commit changes
echo "Step 4: Committing changes..."
git commit -m "Update agent conversation memory with Phase 3 Week 1 completion details and critical fixes documentation" || echo "Nothing to commit"

# Step 5: Push to remote
echo "Step 5: Pushing to remote..."
git push origin main

# Step 6: Verify sync
echo "Step 6: Verifying sync with remote..."
git fetch
git status

echo "✅ Git sync complete!"