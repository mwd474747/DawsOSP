# Archived CI/CD Configuration

**Date Archived:** January 14, 2025  
**Reason:** Incompatible with current application structure

---

## Archived Files

### GitHub Actions Workflows

1. **compliance-check.yml** - Trinity Compliance Check
   - **Status:** ❌ Completely incompatible
   - **Issues:** References `dawsos/` directory that doesn't exist
   - **Current Structure:** Uses `backend/app/` not `dawsos/`

2. **integration-tests.yml** - Integration Tests
   - **Status:** ❌ Partially incompatible
   - **Issues:** Wrong migration path (`schema/*.sql` vs `migrations/*.sql`)
   - **Current Structure:** Migrations in `backend/db/migrations/`, tests in `tests/`

### Pre-commit Configuration

3. **.pre-commit-config.yaml** - Pre-commit hooks
   - **Status:** ❌ Incompatible
   - **Issues:** All hooks reference `dawsos/` paths that don't exist
   - **Current Structure:** Uses `backend/app/` not `dawsos/`

---

## Current Application Structure

```
DawsOSP/
├── backend/
│   ├── app/                    # Application code (not dawsos/)
│   ├── patterns/                # Pattern definitions
│   └── db/
│       ├── migrations/          # Migration files (*.sql)
│       └── schema/              # Schema definition files
├── tests/                       # Test files
└── combined_server.py           # Main server entry point
```

---

## Restoration

If workflows are needed in the future:

1. **Update paths:**
   - `dawsos/**/*.py` → `backend/app/**/*.py`
   - `dawsos/patterns/**/*.json` → `backend/patterns/**/*.json`
   - `dawsos/tests` → `tests/` or `backend/tests/`

2. **Update migration paths:**
   - `backend/db/schema/*.sql` → `backend/db/migrations/*.sql`

3. **Update test paths:**
   - `dawsos/test_system_health.py` → Remove (doesn't exist)
   - `dawsos/tests/validation` → `tests/integration/`

4. **Update coverage paths:**
   - `--cov=dawsos/core` → `--cov=backend/app/core`

---

## CI/CD Status

**Current:** CI/CD handled by Replit deployment system  
**GitHub Actions:** Archived (incompatible with current structure)  
**Pre-commit:** Archived (incompatible path references)

---

**Archived By:** Claude IDE Agent  
**Date:** January 14, 2025

