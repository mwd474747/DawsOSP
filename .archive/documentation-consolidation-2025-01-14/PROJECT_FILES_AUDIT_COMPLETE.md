# Project Files Audit - Complete Analysis

**Date:** November 4, 2025  
**Status:** ✅ **COMPLETE**

---

## 📊 Executive Summary

Comprehensive audit of all files in project root. Analyzed 38 root-level files to determine:
1. What they do
2. How they are used
3. Why they are needed
4. Whether they need updating or deletion

**Result:** 14 files identified for deletion/archival, 24 files kept (with recommendations)

---

## ✅ Core Application Files (KEEP - No Changes Needed)

### 1. `combined_server.py` ⭐ **CRITICAL**
- **Purpose:** Main FastAPI application server (6,043 lines, 53 endpoints)
- **Usage:** Primary entry point - `python combined_server.py`
- **Why Needed:** Single-file deployment, serves both API and UI
- **Status:** ✅ **KEEP** - Essential production file
- **Action:** None - Documented in README.md

### 2. `full_ui.html` ⭐ **CRITICAL**
- **Purpose:** React 18 SPA in single HTML file (11,594 lines, 18 pages)
- **Usage:** Served by combined_server.py at root route
- **Why Needed:** No build step required, single-file UI deployment
- **Status:** ✅ **KEEP** - Essential production file
- **Action:** None - Documented in README.md and ARCHITECTURE.md

### 3. `requirements.txt` ⭐ **CRITICAL**
- **Purpose:** Python dependencies list
- **Usage:** Used by `pip install -r requirements.txt`
- **Why Needed:** Dependency management
- **Status:** ✅ **KEEP** - Essential for deployment
- **Action:** None - Referenced in README.md

### 4. `pytest.ini` ⭐ **CRITICAL**
- **Purpose:** Pytest configuration
- **Usage:** Used by pytest for test execution
- **Why Needed:** Test configuration
- **Status:** ✅ **KEEP** - Essential for testing
- **Action:** None - Used by tests/ directory

---

## ⚠️ Files to Delete (Not Used)

### 5. `config.toml` ❌ **DELETE**
- **Purpose:** Streamlit configuration (headless, port, browser settings)
- **Usage:** Not used - application uses FastAPI, not Streamlit
- **Why Not Needed:** Streamlit is not used in this application
- **Status:** ❌ **DELETE** - Leftover from old version
- **Action:** Delete - No references found in codebase

### 6. `index.ts` ❌ **DELETE**
- **Purpose:** Test file with `console.log("Hello via Bun!")`
- **Usage:** Not used - no TypeScript build step
- **Why Not Needed:** Application uses JavaScript in full_ui.html, not TypeScript
- **Status:** ❌ **DELETE** - Test file, not used
- **Action:** Delete - No references found

### 7. `tsconfig.json` ❌ **DELETE**
- **Purpose:** TypeScript compiler configuration
- **Usage:** Not used - no TypeScript build step
- **Why Not Needed:** Application uses JavaScript in full_ui.html, not TypeScript
- **Status:** ❌ **DELETE** - Not used
- **Action:** Delete - No references found

---

## 📝 Utility Scripts (REVIEW & ORGANIZE)

### 8. `activate.sh` ⚠️ **KEEP BUT DOCUMENT**
- **Purpose:** Virtual environment activation script with API key status
- **Usage:** Convenience script for development
- **Why Needed:** Helpful for development setup
- **Status:** ⚠️ **KEEP** - Useful but not critical
- **Action:** Keep - Consider documenting in DEVELOPMENT_GUIDE.md

### 9. `load_env.py` ⚠️ **KEEP BUT DOCUMENT**
- **Purpose:** Compatibility shim for python-dotenv
- **Usage:** Legacy compatibility for old scripts
- **Why Needed:** Backward compatibility
- **Status:** ⚠️ **KEEP** - Legacy compatibility shim
- **Action:** Keep - May be deprecated in future

### 10. `fix_git_and_push.sh` ❌ **ARCHIVE**
- **Purpose:** One-time script to fix git lock issues
- **Usage:** One-time fix script
- **Why Not Needed:** One-time fix, no longer needed
- **Status:** ❌ **ARCHIVE** - One-time fix script
- **Action:** Move to .archive/scripts/ - Not needed going forward

### 11. `verify_ready.sh` ⚠️ **KEEP BUT DOCUMENT**
- **Purpose:** Setup verification script
- **Usage:** Verifies environment setup
- **Why Needed:** Useful for setup verification
- **Status:** ⚠️ **KEEP** - Useful but not critical
- **Action:** Keep - Consider documenting in DEVELOPMENT_GUIDE.md

---

## 📊 Data Population Scripts (MOVE TO scripts/)

### 12. `populate_portfolio_metrics_simple.py` ⚠️ **MOVE**
- **Purpose:** Populate portfolio metrics in database
- **Usage:** Data seeding script (used Nov 3, 2025)
- **Why Needed:** Database initialization/seeding
- **Status:** ⚠️ **MOVE** - Should be in scripts/ directory
- **Action:** Move to `scripts/data/populate_portfolio_metrics_simple.py`

### 13. `populate_prices.py` ⚠️ **MOVE**
- **Purpose:** Populate prices in database
- **Usage:** Data seeding script (used Nov 3, 2025)
- **Why Needed:** Database initialization/seeding
- **Status:** ⚠️ **MOVE** - Should be in scripts/ directory
- **Action:** Move to `scripts/data/populate_prices.py`

### 14. `update_metrics.py` ⚠️ **MOVE**
- **Purpose:** Update portfolio metrics
- **Usage:** Data update script (used Nov 2, 2025)
- **Why Needed:** Periodic data updates
- **Status:** ⚠️ **MOVE** - Should be in scripts/ directory
- **Action:** Move to `scripts/data/update_metrics.py`

### 15. `fix_dashboard_data.py` ⚠️ **ARCHIVE**
- **Purpose:** Fix dashboard data issues
- **Usage:** One-time fix script (used Nov 3, 2025)
- **Why Not Needed:** One-time fix, may be complete
- **Status:** ⚠️ **ARCHIVE** - One-time fix script
- **Action:** Move to `.archive/scripts/fix_dashboard_data.py` if fix is complete

### 16. `verify_ui_data.py` ⚠️ **MOVE**
- **Purpose:** Verify UI data integrity
- **Usage:** Data verification script (used Nov 3, 2025)
- **Why Needed:** Data validation
- **Status:** ⚠️ **MOVE** - Should be in scripts/ directory
- **Action:** Move to `scripts/validation/verify_ui_data.py`

### 17. `validate_pattern_ui_match.py` ⚠️ **MOVE**
- **Purpose:** Validate pattern UI matching
- **Usage:** Validation script (used Nov 2, 2025)
- **Why Needed:** Pattern/UI validation
- **Status:** ⚠️ **MOVE** - Should be in scripts/ directory
- **Action:** Move to `scripts/validation/validate_pattern_ui_match.py`

---

## 🧪 Test Files (MOVE TO tests/)

### 18. `test_dashboard.html` ⚠️ **MOVE OR ARCHIVE**
- **Purpose:** Test dashboard HTML file
- **Usage:** Test file (used Nov 3, 2025)
- **Why Needed:** Testing dashboard functionality
- **Status:** ⚠️ **MOVE** - Should be in tests/ directory
- **Action:** Move to `tests/integration/test_dashboard.html` or archive if no longer needed

### 19. `test_login_and_macro.js` ⚠️ **MOVE OR ARCHIVE**
- **Purpose:** Test login and macro functionality
- **Usage:** Test file (used Nov 3, 2025)
- **Why Needed:** Testing login and macro functionality
- **Status:** ⚠️ **MOVE** - Should be in tests/ directory
- **Action:** Move to `tests/integration/test_login_and_macro.js` or archive if no longer needed

### 20. `test_risk_page_migration.js` ⚠️ **ARCHIVE**
- **Purpose:** Test risk page migration
- **Usage:** Test file (used Nov 3, 2025)
- **Why Not Needed:** Migration may be complete
- **Status:** ⚠️ **ARCHIVE** - Migration test, may be complete
- **Action:** Move to `.archive/tests/test_risk_page_migration.js` if migration is complete

### 21. `test_optimizer_routing.py` ⚠️ **MOVE**
- **Purpose:** Test optimizer routing
- **Usage:** Test file (used Nov 3, 2025)
- **Why Needed:** Testing optimizer routing
- **Status:** ⚠️ **MOVE** - Should be in tests/ directory
- **Action:** Move to `tests/integration/test_optimizer_routing.py`

### 22. `test_db_pool_config.py` ⚠️ **MOVE**
- **Purpose:** Test database pool configuration
- **Usage:** Test file (used Nov 3, 2025)
- **Why Needed:** Testing database pool configuration
- **Status:** ⚠️ **MOVE** - Should be in tests/ directory
- **Action:** Move to `tests/integration/test_db_pool_config.py`

---

## 💾 Database Files (MOVE TO migrations/ OR scripts/)

### 23. `seed_portfolio_data.sql` ⚠️ **MOVE**
- **Purpose:** Seed portfolio data SQL script
- **Usage:** Database seeding script
- **Why Needed:** Database initialization/seeding
- **Status:** ⚠️ **MOVE** - Should be in migrations/ or scripts/ directory
- **Action:** Move to `migrations/seeds/seed_portfolio_data.sql` or `backend/db/seeds/seed_portfolio_data.sql`

---

## 📚 Documentation Files (KEEP - Already Organized)

### 24-38. Documentation Files ✅ **ALL KEEP**
- `README.md` - Main entry point
- `ARCHITECTURE.md` - System architecture
- `DATABASE.md` - Database documentation
- `DEVELOPMENT_GUIDE.md` - Development guide
- `DEPLOYMENT.md` - Deployment guide
- `TROUBLESHOOTING.md` - Troubleshooting
- `ROADMAP.md` - Product roadmap
- `API_CONTRACT.md` - API documentation
- `PRODUCT_SPEC.md` - Product specification
- `FEATURE_FLAGS_EXPLANATION.md` - Feature flags
- `MIGRATION_HISTORY.md` - Migration history
- `AGENT_CONVERSATION_MEMORY.md` - Agent coordination
- `PRICING_PACK_ARCHITECTURE.md` - Pricing pack docs
- `DOCUMENTATION.md` - Documentation index
- `replit.md` - Replit deployment guide

**Status:** ✅ **ALL KEEP** - Essential documentation

---

## 🗑️ Additional Files to Clean Up

### Coverage Files (DELETE)
- `.coverage` - Test coverage data (generated)
- `.coverage 2` - Duplicate coverage file (generated)
- `.coveragerc` - Coverage configuration (keep if needed for CI/CD)

**Action:** Delete `.coverage` and `.coverage 2` (generated files), keep `.coveragerc` if used

### Legacy Directory (REVIEW)
- `.legacy/` - Legacy code directory
- **Action:** Review and archive if not needed

### Attached Assets (REVIEW)
- `attached_assets/` - 28 files (25 .txt, 3 .png)
- **Action:** Review and archive if not needed

---

## 📋 Execution Plan

### Phase 1: Delete Unused Files
1. Delete `config.toml` (Streamlit config, not used)
2. Delete `index.ts` (test file, not used)
3. Delete `tsconfig.json` (TypeScript config, not used)
4. Delete `.coverage` and `.coverage 2` (generated files)

### Phase 2: Archive One-Time Scripts
1. Move `fix_git_and_push.sh` to `.archive/scripts/`
2. Move `fix_dashboard_data.py` to `.archive/scripts/` (if fix is complete)
3. Move `test_risk_page_migration.js` to `.archive/tests/` (if migration is complete)

### Phase 3: Organize Files into Directories
1. Move data population scripts to `scripts/data/`
   - `populate_portfolio_metrics_simple.py`
   - `populate_prices.py`
   - `update_metrics.py`
2. Move validation scripts to `scripts/validation/`
   - `verify_ui_data.py`
   - `validate_pattern_ui_match.py`
3. Move test files to `tests/integration/`
   - `test_dashboard.html`
   - `test_login_and_macro.js`
   - `test_optimizer_routing.py`
   - `test_db_pool_config.py`
4. Move database seed file to `migrations/seeds/` or `backend/db/seeds/`
   - `seed_portfolio_data.sql`

### Phase 4: Update Documentation
1. Update DEVELOPMENT_GUIDE.md with utility scripts documentation
2. Update README.md if file locations change
3. Document script organization in DEVELOPMENT_GUIDE.md

---

## ✅ Summary

**Files to Delete:** 3 files
- `config.toml` (Streamlit config, not used)
- `index.ts` (test file, not used)
- `tsconfig.json` (TypeScript config, not used)

**Files to Archive:** 3 files
- `fix_git_and_push.sh` (one-time fix)
- `fix_dashboard_data.py` (one-time fix, if complete)
- `test_risk_page_migration.js` (migration test, if complete)

**Files to Move:** 10 files
- 3 data population scripts → `scripts/data/`
- 2 validation scripts → `scripts/validation/`
- 4 test files → `tests/integration/`
- 1 database seed file → `migrations/seeds/` or `backend/db/seeds/`

**Files to Keep:** 22 files
- 4 core application files
- 15 documentation files
- 3 utility scripts (keep but document)

---

**Status:** Ready for execution

