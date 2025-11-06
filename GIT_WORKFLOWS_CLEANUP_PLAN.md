# Git Workflows Cleanup Plan

**Date:** January 14, 2025  
**Status:** 📋 **PLANNING**  
**Purpose:** Remove or archive outdated GitHub Actions workflows that are incompatible with current application structure

---

## 📊 Executive Summary

**Found Workflows:**
- ❌ `.github/workflows/compliance-check.yml` - **COMPLETELY INCOMPATIBLE**
- ❌ `.github/workflows/integration-tests.yml` - **PARTIALLY INCOMPATIBLE**
- ⚠️ `.pre-commit-config.yaml` - **INCOMPATIBLE PATH REFERENCES**

**Critical Issues:**
1. ❌ All workflows reference `dawsos/` directory that doesn't exist
2. ❌ Current structure uses `backend/app/` not `dawsos/`
3. ❌ Migration paths wrong (`schema/*.sql` vs `migrations/*.sql`)
4. ❌ Test paths wrong (`dawsos/tests` vs `tests/`)
5. ❌ Missing test files referenced
6. ❌ Application deployed on Replit (workflows not needed)

**Recommendation:** **ARCHIVE WORKFLOWS** (keep for reference, remove from active use)

---

## 🔍 Detailed Analysis

### Workflow 1: compliance-check.yml

**Status:** ❌ **COMPLETELY INCOMPATIBLE**

**Issues:**
- References `dawsos/**/*.py` (doesn't exist)
- References `dawsos/patterns/**/*.json` (should be `backend/patterns/**/*.json`)
- References `dawsos/test_system_health.py` (doesn't exist)
- References `dawsos/tests/validation` (should be `tests/integration/`)
- References `dawsos/core` for coverage (should be `backend/app/core`)

**Assessment:** **100% incompatible** - Would fail on every run

---

### Workflow 2: integration-tests.yml

**Status:** ❌ **PARTIALLY INCOMPATIBLE**

**Issues:**
- ✅ Correctly references `backend/requirements.txt`
- ✅ Correctly references `backend/tests/integration/test_*.py`
- ❌ Wrong migration path: `backend/db/schema/*.sql` (should be `backend/db/migrations/*.sql`)
- ❌ References test files that may not exist:
  - `backend/tests/integration/test_uat_p0.py`
  - `backend/tests/integration/test_security.py`
  - `backend/tests/integration/test_patterns.py`
  - `backend/tests/integration/test_provider_integration.py`
  - `backend/tests/integration/test_performance.py`

**Assessment:** **80% incompatible** - Would fail on migration step and possibly test steps

---

### Pre-commit Config

**Status:** ⚠️ **INCOMPATIBLE PATH REFERENCES**

**Issues:**
- References `dawsos/` paths throughout
- Black/isort/flake8 hooks reference `^dawsos/.*\.py$`
- Mypy references `dawsos/core/.*\.py$`
- Pattern linter references `patterns/.*\.json$` (should be `backend/patterns/.*\.json$`)

**Assessment:** **Would not work** - All hooks reference non-existent paths

---

## 🎯 Cleanup Plan

### Option 1: Archive Workflows (Recommended)

**Rationale:**
- Application deployed on Replit (not GitHub Actions)
- Workflows completely incompatible with current structure
- No benefit to fixing workflows that aren't used
- Preserves history for reference

**Action Plan:**

1. **Create archive directory:**
   ```bash
   mkdir -p .archive/ci-cd/github-workflows
   ```

2. **Archive workflows:**
   ```bash
   mv .github/workflows/compliance-check.yml .archive/ci-cd/github-workflows/
   mv .github/workflows/integration-tests.yml .archive/ci-cd/github-workflows/
   ```

3. **Archive pre-commit config:**
   ```bash
   mv .pre-commit-config.yaml .archive/ci-cd/
   ```

4. **Remove .github directory:**
   ```bash
   rmdir .github/workflows 2>/dev/null || true
   rmdir .github 2>/dev/null || true
   ```

5. **Update documentation:**
   - Update `DEPLOYMENT.md` to note workflows archived
   - Add note about Replit deployment

**Benefits:**
- ✅ No more failed workflow notifications
- ✅ Cleaner repository
- ✅ No confusion about CI/CD status
- ✅ Workflows preserved for reference
- ✅ Can be restored/updated later if needed

---

### Option 2: Update Workflows (If Needed Later)

**If workflows are needed in the future, update:**

1. **compliance-check.yml:**
   ```yaml
   paths:
     - 'backend/app/**/*.py'
     - 'backend/patterns/**/*.json'
   
   run: |
     python3 scripts/check_compliance.py --root backend/app --format github --strict
   ```

2. **integration-tests.yml:**
   ```yaml
   run: |
     for migration in backend/db/migrations/*.sql; do
       if [ -f "$migration" ]; then
         echo "Applying: $(basename $migration)"
         psql "$TEST_DATABASE_URL" -f "$migration" || true
       fi
     done
   ```

3. **pre-commit-config.yaml:**
   ```yaml
   files: '^backend/app/.*\.py$'
   files: '^backend/patterns/.*\.json$'
   ```

**But:** This requires significant work and may not be needed if deploying on Replit.

---

## ✅ Recommended Action: Archive Workflows

**Step 1: Create Archive Directory (1 minute)**
```bash
mkdir -p .archive/ci-cd/github-workflows
```

**Step 2: Archive Workflows (1 minute)**
```bash
mv .github/workflows/compliance-check.yml .archive/ci-cd/github-workflows/
mv .github/workflows/integration-tests.yml .archive/ci-cd/github-workflows/
```

**Step 3: Archive Pre-commit Config (1 minute)**
```bash
mv .pre-commit-config.yaml .archive/ci-cd/
```

**Step 4: Remove .github Directory (1 minute)**
```bash
rmdir .github/workflows 2>/dev/null || true
rmdir .github 2>/dev/null || true
```

**Step 5: Update Documentation (5 minutes)**
- Update `DEPLOYMENT.md` to note:
  - CI/CD is handled by Replit
  - GitHub Actions workflows archived (outdated)
  - Can be re-added later if needed

**Total Time:** 10 minutes

---

## 📋 Execution Checklist

- [ ] Create `.archive/ci-cd/github-workflows/` directory
- [ ] Archive `compliance-check.yml`
- [ ] Archive `integration-tests.yml`
- [ ] Archive `.pre-commit-config.yaml`
- [ ] Remove `.github/` directory if empty
- [ ] Update `DEPLOYMENT.md` with archive note
- [ ] Verify no workflows remain in `.github/workflows/`
- [ ] Commit changes with clear message

---

## 🎯 Impact

### Before Cleanup:
- ❌ Workflows failing on every push/PR
- ❌ Confusing error messages
- ❌ No value provided (wrong paths)
- ❌ Maintenance burden

### After Cleanup:
- ✅ No failed workflow notifications
- ✅ Cleaner repository
- ✅ No confusion about CI/CD
- ✅ Workflows preserved for reference
- ✅ Can add workflows later if needed

---

## ✅ Summary

**Recommendation:** **ARCHIVE WORKFLOWS**

**Rationale:**
1. ✅ Application deployed on Replit (not GitHub Actions)
2. ✅ Workflows completely incompatible with current structure
3. ✅ No benefit to fixing workflows that aren't used
4. ✅ Preserves history for reference
5. ✅ Can be restored/updated later if needed

**Action:**
1. Archive workflows to `.archive/ci-cd/github-workflows/`
2. Archive pre-commit config to `.archive/ci-cd/`
3. Remove `.github/` directory if empty
4. Update `DEPLOYMENT.md` to note CI/CD handled by Replit

**Time:** 10 minutes

---

**Report Generated:** January 14, 2025  
**Status:** 📋 **PLANNING COMPLETE - READY FOR EXECUTION**

