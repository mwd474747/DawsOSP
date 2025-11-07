# Project Files Audit

**Date:** November 4, 2025  
**Purpose:** Comprehensive audit of all files in project root  
**Status:** 🔍 **IN PROGRESS**

---

## 📊 Executive Summary

Examining all files in the project folder to understand:
1. What they do
2. How they are used
3. Why they are needed
4. Do they need updating or deletion?

---

## 📁 Root-Level Files Analysis

### Core Application Files (KEEP)

#### 1. `combined_server.py` ⭐ **CRITICAL**
- **Purpose:** Main FastAPI application server (6,043 lines, 53 endpoints)
- **Usage:** Primary entry point for the application
- **Why Needed:** Single-file deployment, serves both API and UI
- **Status:** ✅ **KEEP** - Essential production file
- **Notes:** Referenced in README.md as main entry point

#### 2. `full_ui.html` ⭐ **CRITICAL**
- **Purpose:** React 18 SPA in single HTML file (11,594 lines, 18 pages)
- **Usage:** Served by combined_server.py at root route
- **Why Needed:** No build step required, single-file UI deployment
- **Status:** ✅ **KEEP** - Essential production file
- **Notes:** Referenced in README.md and ARCHITECTURE.md

#### 3. `requirements.txt` ⭐ **CRITICAL**
- **Purpose:** Python dependencies list
- **Usage:** Used by pip install -r requirements.txt
- **Why Needed:** Dependency management
- **Status:** ✅ **KEEP** - Essential for deployment
- **Notes:** Referenced in README.md setup instructions

#### 4. `config.toml` ⭐ **CRITICAL**
- **Purpose:** Application configuration
- **Usage:** Loaded by application at startup
- **Why Needed:** Configuration management
- **Status:** ✅ **KEEP** - Essential configuration file
- **Notes:** Check if it's actually used in codebase

#### 5. `pytest.ini` ⭐ **CRITICAL**
- **Purpose:** Pytest configuration
- **Usage:** Used by pytest for test execution
- **Why Needed:** Test configuration
- **Status:** ✅ **KEEP** - Essential for testing
- **Notes:** Check if tests directory exists and uses this

#### 6. `tsconfig.json` ⚠️ **REVIEW**
- **Purpose:** TypeScript configuration
- **Usage:** TypeScript compiler configuration
- **Why Needed:** If TypeScript is used
- **Status:** ⚠️ **REVIEW** - Check if TypeScript is used (UI is in full_ui.html)
- **Notes:** May not be needed if no TypeScript build step

#### 7. `index.ts` ⚠️ **REVIEW**
- **Purpose:** TypeScript entry point
- **Usage:** TypeScript compilation entry point
- **Why Needed:** If TypeScript is used
- **Status:** ⚠️ **REVIEW** - Check if TypeScript is used
- **Notes:** May not be needed if no TypeScript build step

---

### Documentation Files (KEEP)

#### 8-22. Core Documentation Files ⭐ **KEEP**
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

### Utility Scripts (REVIEW)

#### 23. `activate.sh` ⚠️ **REVIEW**
- **Purpose:** Virtual environment activation script
- **Usage:** Shell script to activate venv
- **Why Needed:** Convenience script for development
- **Status:** ⚠️ **REVIEW** - Standard venv activation, may be redundant
- **Recommendation:** May be redundant if standard `source venv/bin/activate` works

#### 24. `load_env.py` ⚠️ **REVIEW**
- **Purpose:** Environment variable loading utility
- **Usage:** Python script to load environment variables
- **Why Needed:** Environment variable management
- **Status:** ⚠️ **REVIEW** - Check if it's actually used
- **Recommendation:** May be redundant if application uses standard env loading

#### 25. `fix_git_and_push.sh` ⚠️ **REVIEW**
- **Purpose:** Git fix and push script
- **Usage:** Shell script for git operations
- **Why Needed:** Convenience script for git operations
- **Status:** ⚠️ **REVIEW** - May be redundant
- **Recommendation:** May be redundant if standard git commands work

#### 26. `verify_ready.sh` ⚠️ **REVIEW**
- **Purpose:** Verification script
- **Usage:** Shell script to verify setup
- **Why Needed:** Setup verification
- **Status:** ⚠️ **REVIEW** - Check if it's actually used
- **Recommendation:** May be redundant if not used in CI/CD

---

### Data Population Scripts (REVIEW)

#### 27. `populate_portfolio_metrics_simple.py` ⚠️ **REVIEW**
- **Purpose:** Populate portfolio metrics in database
- **Usage:** Data seeding script
- **Why Needed:** Database initialization/seeding
- **Status:** ⚠️ **REVIEW** - Check if it's still used
- **Recommendation:** May be moved to scripts/ directory or archived if not used

#### 28. `populate_prices.py` ⚠️ **REVIEW**
- **Purpose:** Populate prices in database
- **Usage:** Data seeding script
- **Why Needed:** Database initialization/seeding
- **Status:** ⚠️ **REVIEW** - Check if it's still used
- **Recommendation:** May be moved to scripts/ directory or archived if not used

#### 29. `update_metrics.py` ⚠️ **REVIEW**
- **Purpose:** Update portfolio metrics
- **Usage:** Data update script
- **Why Needed:** Periodic data updates
- **Status:** ⚠️ **REVIEW** - Check if it's still used
- **Recommendation:** May be moved to scripts/ directory or archived if not used

#### 30. `fix_dashboard_data.py` ⚠️ **REVIEW**
- **Purpose:** Fix dashboard data issues
- **Usage:** Data fix script
- **Why Needed:** One-time data fixes
- **Status:** ⚠️ **REVIEW** - May be one-time fix script
- **Recommendation:** May be archived if fix is complete

#### 31. `verify_ui_data.py` ⚠️ **REVIEW**
- **Purpose:** Verify UI data integrity
- **Usage:** Data verification script
- **Why Needed:** Data validation
- **Status:** ⚠️ **REVIEW** - Check if it's still used
- **Recommendation:** May be moved to scripts/ directory or archived if not used

#### 32. `validate_pattern_ui_match.py` ⚠️ **REVIEW**
- **Purpose:** Validate pattern UI matching
- **Usage:** Validation script
- **Why Needed:** Pattern/UI validation
- **Status:** ⚠️ **REVIEW** - Check if it's still used
- **Recommendation:** May be moved to scripts/ directory or archived if not used

---

### Test Files (REVIEW)

#### 33. `test_dashboard.html` ⚠️ **REVIEW**
- **Purpose:** Test dashboard HTML file
- **Usage:** Test file for dashboard
- **Why Needed:** Testing dashboard functionality
- **Status:** ⚠️ **REVIEW** - Check if it's still used
- **Recommendation:** May be moved to tests/ directory or archived if not used

#### 34. `test_login_and_macro.js` ⚠️ **REVIEW**
- **Purpose:** Test login and macro functionality
- **Usage:** Test file for login and macro
- **Why Needed:** Testing login and macro functionality
- **Status:** ⚠️ **REVIEW** - Check if it's still used
- **Recommendation:** May be moved to tests/ directory or archived if not used

#### 35. `test_risk_page_migration.js` ⚠️ **REVIEW**
- **Purpose:** Test risk page migration
- **Usage:** Test file for risk page migration
- **Why Needed:** Testing risk page migration
- **Status:** ⚠️ **REVIEW** - Check if it's still used (migration may be complete)
- **Recommendation:** May be archived if migration is complete

#### 36. `test_optimizer_routing.py` ⚠️ **REVIEW**
- **Purpose:** Test optimizer routing
- **Usage:** Test file for optimizer routing
- **Why Needed:** Testing optimizer routing
- **Status:** ⚠️ **REVIEW** - Check if it's still used
- **Recommendation:** May be moved to tests/ directory or archived if not used

#### 37. `test_db_pool_config.py` ⚠️ **REVIEW**
- **Purpose:** Test database pool configuration
- **Usage:** Test file for DB pool config
- **Why Needed:** Testing database pool configuration
- **Status:** ⚠️ **REVIEW** - Check if it's still used
- **Recommendation:** May be moved to tests/ directory or archived if not used

---

### Database Files (REVIEW)

#### 38. `seed_portfolio_data.sql` ⚠️ **REVIEW**
- **Purpose:** Seed portfolio data SQL script
- **Usage:** Database seeding script
- **Why Needed:** Database initialization/seeding
- **Status:** ⚠️ **REVIEW** - Check if it's still used
- **Recommendation:** May be moved to migrations/ or scripts/ directory

---

## 🔍 Next Steps

### Phase 1: Verify Usage
1. Check if TypeScript files (`index.ts`, `tsconfig.json`) are actually used
2. Verify utility scripts are referenced/used
3. Check if data population scripts are still needed
4. Verify test files are still used
5. Check if database seed file is still used

### Phase 2: Organize
1. Move utility scripts to `scripts/` directory
2. Move test files to `tests/` directory
3. Move data population scripts to `scripts/` directory
4. Archive one-time fix scripts

### Phase 3: Clean Up
1. Delete redundant files
2. Remove unused TypeScript files if not used
3. Archive completed test files
4. Remove one-time fix scripts if fixes are complete

---

**Status:** Audit in progress - need to verify actual usage of each file

