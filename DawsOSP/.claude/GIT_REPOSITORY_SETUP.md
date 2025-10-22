# DawsOSP Git Repository Setup Guide

**Date**: 2025-10-21
**Version**: 2.0
**Status**: Ready to execute

---

## Overview

This guide walks through creating a fresh GitHub repository for DawsOSP (Portfolio Intelligence Platform) with proper Git configuration, branch protection, and workflows aligned with the application's architecture.

---

## Step 1: Create GitHub Repository

### Option A: Via GitHub Web UI

1. Go to [https://github.com/new](https://github.com/new)
2. Fill in:
   - **Repository name**: `DawsOSP`
   - **Description**: "DawsOS Portfolio Intelligence Platform - Production-ready financial analysis platform with Dalio macro + Buffett fundamentals"
   - **Visibility**: Private (recommended initially)
   - **Initialize**: ✅ Do NOT initialize (we have existing code)
   - ❌ Do NOT add .gitignore (we have one)
   - ❌ Do NOT add README (we have one)
   - ❌ Do NOT choose a license yet (add later if needed)
3. Click "Create repository"

### Option B: Via GitHub CLI

```bash
gh repo create DawsOSP \
  --private \
  --description "DawsOS Portfolio Intelligence Platform - Production-ready financial analysis" \
  --source=. \
  --remote=origin \
  --push
```

---

## Step 2: Local Git Configuration

### 2.1 User Configuration (if not set globally)

```bash
git config user.name "Mike Dawson"
git config user.email "your-email@example.com"
```

### 2.2 Branch Configuration

```bash
# Set default branch name to 'main'
git config init.defaultBranch main

# Set pull strategy to rebase (cleaner history)
git config pull.rebase true

# Set push strategy to simple (only current branch)
git config push.default simple
```

### 2.3 Commit Signing (Optional but Recommended)

```bash
# If using GPG
git config commit.gpgsign true
git config user.signingkey <your-gpg-key-id>

# If using SSH (GitHub now supports this)
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519.pub
```

---

## Step 3: Initialize Local Repository (if not already initialized)

**SKIP THIS if `git status` shows an existing repository**

```bash
# Initialize Git repository
git init

# Rename default branch to 'main' (if it's 'master')
git branch -M main
```

---

## Step 4: Clean Up Staged Changes

Based on the current `git status`, you have many staged deletions. Let's start fresh:

```bash
# Reset all staged changes
git reset

# Check status (should show untracked files only)
git status
```

---

## Step 5: Add Files for Initial Commit

### 5.1 Add Documentation

```bash
git add README.md
git add PRODUCT_SPEC.md
git add ARCHITECTURE.md
git add CONFIGURATION.md
git add DEVELOPMENT.md
git add DEPLOYMENT.md
git add TROUBLESHOOTING.md
git add QUICK_START.md
```

### 5.2 Add .claude/ Directory (Agent Specs & Guides)

```bash
git add .claude/
```

### 5.3 Add .ops/ Directory (Operational Docs)

```bash
git add .ops/
```

### 5.4 Add .security/ Directory (Threat Model)

```bash
git add .security/
```

### 5.5 Add Git Configuration

```bash
git add .gitignore
git add .gitattributes
```

### 5.6 Add Application Structure (placeholder - to be built in Phase 0)

```bash
# Create directory structure placeholders
mkdir -p backend/{api,core,services,migrations}
mkdir -p frontend/{components,pages,styles}
mkdir -p tests/{unit,integration,golden,chaos}
mkdir -p infra/{terraform,helm,ecs}

# Create .gitkeep files to preserve empty directories
touch backend/api/.gitkeep
touch backend/core/.gitkeep
touch backend/services/.gitkeep
touch backend/migrations/.gitkeep
touch frontend/components/.gitkeep
touch frontend/pages/.gitkeep
touch frontend/styles/.gitkeep
touch tests/unit/.gitkeep
touch tests/integration/.gitkeep
touch tests/golden/.gitkeep
touch tests/chaos/.gitkeep
touch infra/terraform/.gitkeep
touch infra/helm/.gitkeep
touch infra/ecs/.gitkeep

# Add placeholders
git add backend/ frontend/ tests/ infra/
```

### 5.7 Add Requirements Files

```bash
# Create requirements.txt placeholder
echo "# DawsOSP Python Dependencies (Phase 0)" > requirements.txt
echo "# FastAPI stack" >> requirements.txt
echo "fastapi>=0.104.0" >> requirements.txt
echo "uvicorn[standard]>=0.24.0" >> requirements.txt
echo "pydantic>=2.5.0" >> requirements.txt
echo "sqlalchemy>=2.0.23" >> requirements.txt
echo "alembic>=1.13.0" >> requirements.txt
echo "" >> requirements.txt
echo "# Observability (S1-W2 requirement)" >> requirements.txt
echo "opentelemetry-api>=1.21.0" >> requirements.txt
echo "opentelemetry-sdk>=1.21.0" >> requirements.txt
echo "prometheus-client>=0.19.0" >> requirements.txt
echo "sentry-sdk>=1.39.0" >> requirements.txt

git add requirements.txt
```

### 5.8 Add Example .env File

```bash
# .env.example already exists, add it
git add .env.example
```

---

## Step 6: Create Initial Commit

```bash
git commit -m "$(cat <<'EOF'
feat: Initial DawsOSP repository setup with PRODUCT_SPEC v2.0

- Add PRODUCT_SPEC v2.0 with 9 production-ready refinements
- Add comprehensive documentation (8 files)
- Add .claude/ directory with agent specs and roadmaps
- Add .ops/ directory with IMPLEMENTATION_ROADMAP_V2, CI/CD pipeline, runbooks
- Add .security/ directory with STRIDE threat model
- Add Git configuration (.gitignore, .gitattributes)
- Add directory structure placeholders (backend, frontend, tests, infra)
- Add requirements.txt with FastAPI stack + observability (S1-W2)

Critical v2.0 changes:
- Observability skeleton in S1-W2 (moved from S3)
- Rights gate enforcement in S1-W2 staging (moved from S4)
- ADR/pay-date FX golden tests in S1-W1 (42¢ accuracy)
- DLQ + dedupe in S3-W6 (moved from S4)
- Macro cycles (STDC/LTDC/Empire) added to S3
- Threat model (STRIDE analysis) in Phase 0
- Rights registry YAML with provider rules

Build Spec: v2.0
Roadmap: 8 weeks (Phase 0 + 4 sprints)
Team: 8-10 FTEs
Status: Ready to build

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Step 7: Add Remote and Push

### If GitHub repo was created via web UI:

```bash
# Add remote (replace with your GitHub username/org)
git remote add origin git@github.com:YOUR_USERNAME/DawsOSP.git

# Verify remote
git remote -v

# Push initial commit
git push -u origin main
```

### If GitHub repo was created via CLI:

The `gh repo create` command already set up the remote and pushed. Verify with:

```bash
git remote -v
git branch -vv
```

---

## Step 8: Configure GitHub Repository Settings

### 8.1 Branch Protection (Main Branch)

Go to **Settings → Branches → Add branch protection rule** for `main`:

**Branch name pattern**: `main`

**Settings**:
- ✅ Require a pull request before merging
  - ✅ Require approvals (1 minimum)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - **Required checks** (add these when CI is set up):
    - `test-unit`
    - `test-golden`
    - `test-property`
    - `test-rls-idor`
    - `sast-sca`
    - `lint`
- ✅ Require conversation resolution before merging
- ✅ Require linear history (enforces rebase/squash)
- ❌ Do not allow bypassing (even admins must follow rules)

### 8.2 Repository Settings

Go to **Settings → General**:

**Features**:
- ✅ Issues (for bug tracking)
- ✅ Projects (for sprint planning)
- ✅ Wiki (optional - we use .claude/ docs)
- ❌ Sponsorships (not needed)

**Pull Requests**:
- ✅ Allow squash merging (preferred)
- ❌ Allow merge commits (not needed - enforces linear history)
- ❌ Allow rebase merging (not needed - squash is simpler)
- ✅ Always suggest updating pull request branches
- ✅ Automatically delete head branches

**Merge Button**:
- Default to squash merge

### 8.3 Secrets (for CI/CD)

Go to **Settings → Secrets and variables → Actions**:

**Add the following secrets** (when ready for CI/CD):
- `FMP_API_KEY` (Financial Modeling Prep)
- `POLYGON_API_KEY` (Polygon.io)
- `FRED_API_KEY` (FRED)
- `NEWS_API_KEY` (NewsAPI)
- `SENTRY_DSN` (Sentry for error tracking)
- `DOCKER_USERNAME` (for Docker Hub, if used)
- `DOCKER_PASSWORD` (for Docker Hub, if used)

### 8.4 Topics (for discoverability)

Go to **About** (top right of repo page):

**Topics** (click gear icon):
- `portfolio-intelligence`
- `financial-analysis`
- `dalio-macro`
- `buffett-fundamentals`
- `python`
- `fastapi`
- `timescaledb`
- `opentelemetry`
- `streamlit`

---

## Step 9: Create Development Branch

```bash
# Create development branch
git checkout -b develop

# Push development branch
git push -u origin develop
```

### Set develop as default branch (optional)

Go to **Settings → Branches** → Change default branch to `develop`

**Reasoning**: `develop` is where active development happens; `main` is for production-ready code

---

## Step 10: Create .github/ Directory for Workflows

### 10.1 Create Pull Request Template

```bash
mkdir -p .github/PULL_REQUEST_TEMPLATE
```

```markdown
## Description

<!-- Describe the changes in this PR -->

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Checklist

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published in downstream modules

## Testing

<!-- Describe the tests you ran to verify your changes -->

- [ ] Unit tests pass (`pytest tests/unit/`)
- [ ] Integration tests pass (`pytest tests/integration/`)
- [ ] Golden tests pass (`pytest tests/golden/`)
- [ ] Property tests pass (`pytest tests/property/`)
- [ ] RLS/IDOR tests pass (`pytest tests/security/`)

## Related Issues

<!-- Link to related issues, e.g. "Closes #123" -->

## Acceptance Gates (if applicable)

<!-- Check which acceptance gates this PR addresses (from PRODUCT_SPEC.md §11) -->

- [ ] Reproducibility (same pack/commit → identical results)
- [ ] Accuracy (ledger ±1bp)
- [ ] Compliance (rights enforced)
- [ ] Performance (warm p95 < 1.2s, cold p95 < 2.0s)
- [ ] Alerts (dedupe, median < 60s)
- [ ] Security (no secrets, audit log, SAST/SCA green)
- [ ] Edge Cases (ADR pay-date FX, hedged benchmarks, restatement)
- [ ] Observability (OTel traces, Prom histograms, dashboards)
- [ ] Backfill (D0→D1 rehearsal, symbol normalization)

---

**Generated with Claude Code**
Co-Authored-By: Claude <noreply@anthropic.com>
```

Save as `.github/PULL_REQUEST_TEMPLATE/pull_request_template.md`

### 10.2 Create Issue Templates

```bash
mkdir -p .github/ISSUE_TEMPLATE
```

**Bug Report** (`.github/ISSUE_TEMPLATE/bug_report.md`):

```markdown
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

<!-- A clear and concise description of what the bug is -->

## Steps to Reproduce

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior

<!-- What you expected to happen -->

## Actual Behavior

<!-- What actually happened -->

## Environment

- **Branch**: (e.g., main, develop)
- **Python Version**: (e.g., 3.11)
- **OS**: (e.g., macOS 14.0, Ubuntu 22.04)
- **Browser** (if UI bug): (e.g., Chrome 120, Safari 17)

## Logs / Screenshots

<!-- Add any relevant logs or screenshots -->

## Additional Context

<!-- Add any other context about the problem here -->

## Acceptance Criteria for Fix

- [ ] Bug is reproducible
- [ ] Fix implemented
- [ ] Test added to prevent regression
- [ ] Documentation updated (if needed)
```

**Feature Request** (`.github/ISSUE_TEMPLATE/feature_request.md`):

```markdown
---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Feature Description

<!-- A clear and concise description of the feature -->

## Problem Statement

<!-- What problem does this feature solve? -->

## Proposed Solution

<!-- How should this feature work? -->

## Alternatives Considered

<!-- What other solutions did you consider? -->

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Additional Context

<!-- Add any other context, mockups, or screenshots -->

## Sprint / Roadmap Alignment

<!-- Which sprint or phase should this feature be in? (See .ops/IMPLEMENTATION_ROADMAP_V2.md) -->

- [ ] Phase 0 (Foundation)
- [ ] Sprint 1 (Truth Spine)
- [ ] Sprint 2 (Metrics + UI)
- [ ] Sprint 3 (Macro + Alerts)
- [ ] Sprint 4 (Ratings + Reporting)
- [ ] Post-Launch
```

---

## Step 11: Git Workflow Guidelines

### Branch Naming Convention

**Format**: `<type>/<short-description>`

**Types**:
- `feature/` — New features
- `bugfix/` — Bug fixes
- `hotfix/` — Critical production fixes
- `refactor/` — Code refactoring
- `docs/` — Documentation changes
- `test/` — Test additions/changes
- `chore/` — Build/tooling changes

**Examples**:
- `feature/adr-paydate-fx-golden-test`
- `bugfix/pack-freshness-gate-503`
- `hotfix/security-rls-bypass`
- `refactor/observability-s1w2`
- `docs/threat-model-stride`

### Commit Message Convention

**Format**: `<type>(<scope>): <subject>`

**Types**:
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation
- `style` — Formatting (no code change)
- `refactor` — Code refactoring
- `test` — Adding/updating tests
- `chore` — Build/tooling

**Scopes** (examples):
- `api` — Executor API
- `db` — Database/migrations
- `ui` — Frontend
- `observability` — OTel/Prom/Sentry
- `rights` — Rights registry
- `tests` — Test infrastructure

**Examples**:
```
feat(api): add /health/pack endpoint for freshness status
fix(db): correct ADR pay-date FX constraint in transactions table
docs(security): add STRIDE threat model for Phase 0
test(golden): add AAPL ADR dividend 42¢ accuracy test
refactor(observability): move OTel/Prom to S1-W2 (from S3)
```

### Pull Request Workflow

1. **Create feature branch** from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit** (follow commit message convention):
   ```bash
   git add .
   git commit -m "feat(api): add /health/pack endpoint"
   ```

3. **Push to remote**:
   ```bash
   git push -u origin feature/my-feature
   ```

4. **Create Pull Request** (via GitHub web UI or `gh` CLI):
   ```bash
   gh pr create --base develop --title "feat(api): add /health/pack endpoint" --body "..."
   ```

5. **Request review** (assign reviewers)

6. **Address review comments** (commit and push)

7. **Merge** (squash merge preferred):
   - GitHub will auto-delete branch after merge
   - Delete local branch:
     ```bash
     git checkout develop
     git pull origin develop
     git branch -d feature/my-feature
     ```

---

## Step 12: Pre-Commit Hooks (Optional but Recommended)

### Install pre-commit

```bash
pip install pre-commit
```

### Create .pre-commit-config.yaml

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.7
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Install hooks

```bash
pre-commit install
```

---

## Step 13: Verify Setup

### 13.1 Check Git Configuration

```bash
git config --list | grep -E "user|pull|push|commit"
```

**Expected**:
```
user.name=Mike Dawson
user.email=your-email@example.com
pull.rebase=true
push.default=simple
commit.gpgsign=true  # if signing is enabled
```

### 13.2 Check Remote

```bash
git remote -v
```

**Expected**:
```
origin  git@github.com:YOUR_USERNAME/DawsOSP.git (fetch)
origin  git@github.com:YOUR_USERNAME/DawsOSP.git (push)
```

### 13.3 Check Branch

```bash
git branch -vv
```

**Expected**:
```
* main    abc1234 [origin/main] feat: Initial DawsOSP repository setup
  develop def5678 [origin/develop] chore: create development branch
```

### 13.4 Check Staged Files

```bash
git status
```

**Expected**:
```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

---

## Summary

✅ **Git configuration complete**:
- .gitignore created (secrets, logs, cache, storage protected)
- .gitattributes created (LF line endings, proper diffs)
- Commit signing configured (optional)
- Branch protection configured (main branch)
- GitHub repository created
- Initial commit pushed
- Development branch created
- Pull request template created
- Issue templates created
- Pre-commit hooks configured (optional)

**Next Steps**:
1. **Review** this setup with team
2. **Add team members** to GitHub repository
3. **Configure CI/CD** (GitHub Actions workflows)
4. **Start Phase 0** (Terraform, database schema, CI/CD pipeline)

---

**Status**: ✅ Git repository ready for Phase 0 development
**Date**: 2025-10-21
**Version**: 2.0
