# Git Sync Guide for Replit

**Date:** January 14, 2025  
**Purpose:** Guide for syncing changes between local, Replit, and remote

---

## Current Status

✅ **Local repository is in sync with remote:**
- All local changes committed and pushed
- 13 commits ahead of previous state (now synced)
- No uncommitted changes

---

## Git Workflow for Replit

### Scenario 1: Changes Made in Replit Need to Push to Remote

**Steps:**
1. **In Replit:**
   ```bash
   # Check status
   git status
   
   # Add changes
   git add -A
   
   # Commit
   git commit -m "Description of changes"
   
   # Push to remote
   git push origin main
   ```

2. **If push fails with authentication:**
   - Use GitHub Personal Access Token (PAT)
   - Or set up SSH keys in Replit

3. **If push fails with conflicts:**
   ```bash
   # Pull latest from remote first
   git fetch origin
   git pull origin main
   
   # Resolve conflicts, then push
   git add -A
   git commit -m "Resolved conflicts"
   git push origin main
   ```

---

### Scenario 2: Changes Made Locally Need to Be in Replit

**Steps:**
1. **In Local (already done):**
   ```bash
   git add -A
   git commit -m "Description"
   git push origin main
   ```

2. **In Replit:**
   ```bash
   # Pull latest from remote
   git fetch origin
   git pull origin main
   ```

---

### Scenario 3: Changes Made in Both Places (Conflicts)

**Steps:**
1. **In Replit:**
   ```bash
   # Commit Replit changes first
   git add -A
   git commit -m "Replit changes"
   
   # Pull latest from remote
   git fetch origin
   git pull origin main
   ```

2. **Resolve conflicts:**
   - Git will mark conflicts in files
   - Edit files to resolve conflicts
   - Keep desired changes from both sides

3. **After resolving:**
   ```bash
   git add -A
   git commit -m "Resolved conflicts"
   git push origin main
   ```

---

## Common Issues and Solutions

### Issue 1: Authentication Failed

**Problem:** `remote: Support for password authentication was removed`

**Solution:**
1. Use GitHub Personal Access Token (PAT)
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` scope
   - Use token as password when pushing

2. Or set up SSH keys:
   ```bash
   # In Replit
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Copy public key to GitHub Settings → SSH keys
   ```

---

### Issue 2: Remote Already Has Changes

**Problem:** `Updates were rejected because the remote contains work`

**Solution:**
```bash
# Pull and merge
git pull origin main

# Or rebase (cleaner history)
git pull --rebase origin main

# Then push
git push origin main
```

---

### Issue 3: Branch Diverged

**Problem:** `Your branch and 'origin/main' have diverged`

**Solution:**
```bash
# Option 1: Merge (creates merge commit)
git pull origin main
git push origin main

# Option 2: Rebase (linear history)
git pull --rebase origin main
git push origin main

# Option 3: Force push (DANGEROUS - only if you're sure)
git push --force origin main
```

---

### Issue 4: Large Files / LFS Issues

**Problem:** Files too large for GitHub

**Solution:**
1. Use Git LFS for large files:
   ```bash
   git lfs install
   git lfs track "*.large"
   git add .gitattributes
   ```

2. Or remove large files from history:
   ```bash
   git filter-branch --tree-filter 'rm -f large_file' HEAD
   ```

---

## Best Practices

### 1. Always Pull Before Push
```bash
git fetch origin
git pull origin main
# Make changes
git add -A
git commit -m "Changes"
git push origin main
```

### 2. Commit Frequently
- Small, focused commits
- Clear commit messages
- Commit before switching branches

### 3. Use Branches for Features
```bash
# Create feature branch
git checkout -b feature/phase3-factor-analysis

# Work on feature
git add -A
git commit -m "Feature work"

# Push feature branch
git push origin feature/phase3-factor-analysis

# Merge to main when ready
git checkout main
git pull origin main
git merge feature/phase3-factor-analysis
git push origin main
```

### 4. Keep Remote in Sync
- Pull before starting work
- Push frequently
- Check status before committing

---

## Quick Reference Commands

### Check Status
```bash
git status                    # Local status
git log --oneline -5          # Recent commits
git log origin/main..HEAD     # Commits not in remote
```

### Sync with Remote
```bash
git fetch origin              # Fetch latest (no merge)
git pull origin main          # Fetch and merge
git push origin main          # Push to remote
```

### Resolve Conflicts
```bash
git pull origin main          # May create conflicts
# Edit conflicted files
git add -A                    # Mark conflicts resolved
git commit -m "Resolved"      # Commit resolution
git push origin main          # Push resolved changes
```

---

## Current Repository State

**Remote:** `https://github.com/mwd474747/DawsOSP.git`  
**Branch:** `main`  
**Status:** ✅ **In sync** (all local changes pushed)

**Recent Commits (13 total):**
1. Phase 3 field name refactor (latest)
2. Comprehensive field name analysis
3. Phase 3 database review
4. Phase 3 prerequisites review
5. Phase 2 validation
6. Phase 1 fixes
7. ... (and 6 more)

---

## Next Steps for Replit

**If Replit has changes to push:**
1. Commit changes in Replit
2. Pull latest from remote (to avoid conflicts)
3. Resolve any conflicts
4. Push to remote

**If Replit needs latest changes:**
1. Pull from remote in Replit
2. All local changes are now in remote

---

**Status:** ✅ **Ready for Replit sync**

