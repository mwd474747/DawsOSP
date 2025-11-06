# Replit Deployment Guardrails 🔴

**Date:** 2025-11-02
**Purpose:** Document critical files that MUST NOT be modified without breaking Replit deployment

---

## ⚠️ CRITICAL WARNING

This application deploys on Replit. Certain files are **SACRED** - modifying them will break the deployment. This document defines the guardrails that ALL development must respect.

---

## 🔴 TIER 1: DO NOT MODIFY (Deployment Will Break)

These files control how Replit deploys and runs the application. Changes will prevent startup.

### 1. `.replit` - Deployment Configuration
**Why Critical:** Tells Replit HOW to run the application
**Contains:**
- Run command: `python combined_server.py`
- Port mapping: 5000 → 80
- Workflow configuration
- Module dependencies

**DO NOT:**
- ❌ Change the run command
- ❌ Modify port mappings
- ❌ Remove required modules
- ❌ Change workflow tasks

**CAN DO:**
- ✅ Add new ports (if needed)
- ✅ Add new modules (carefully)
- ✅ Update comments

**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/.replit`

---

### 2. `combined_server.py` - Application Entry Point
**Why Critical:** This IS the application. Replit runs `python combined_server.py`
**Size:** 6,046 lines (massive monolith)
**Contains:**
- 59 FastAPI endpoints
- Database initialization
- Agent runtime setup
- Full UI serving at `/`

**DO NOT:**
- ❌ Rename this file
- ❌ Move this file to different directory
- ❌ Change port from 5000
- ❌ Remove database initialization
- ❌ Change the root `/` route that serves `full_ui.html`

**CAN DO:**
- ✅ Add new endpoints
- ✅ Fix bugs in existing endpoints
- ✅ Improve error handling

**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/combined_server.py`

---

### 3. `full_ui.html` - Primary User Interface
**Why Critical:** The entire UI. Served at `/` by combined_server.py
**Size:** 14,075 lines (complete React SPA)
**Contains:**
- All 17 UI pages
- React components
- API client integration
- State management

**DO NOT:**
- ❌ Rename this file
- ❌ Move this file
- ❌ Break the self-contained structure
- ❌ Change API endpoint paths without updating backend

**CAN DO:**
- ✅ Fix UI bugs
- ✅ Add new features
- ✅ Improve styling
- ✅ Add new pages

**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/full_ui.html`

---

## 🟡 TIER 2: MODIFY WITH EXTREME CAUTION

These files are critical to application functionality. Changes must be tested carefully.

### 4. `requirements.txt` - Python Dependencies
**Why Important:** Missing packages = import errors on startup
**Current State:** Cleaned (removed observability/redis packages in Phase 3, fully removed January 14, 2025)

**DO NOT:**
- ❌ Remove packages without checking imports
- ❌ Upgrade major versions without testing
- ❌ Add conflicting package versions

**CAN DO:**
- ✅ Add new required packages
- ✅ Update patch versions (carefully)
- ✅ Remove truly unused packages (after verification)

**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/requirements.txt`

**Verification Required:**
```bash
# Before removing a package, verify it's not imported:
grep -r "import package_name" backend/
grep -r "from package_name" backend/
```

---

### 5. `backend/app/db/connection.py` - Database Pool
**Why Important:** All database access depends on this
**Contains:**
- AsyncPG pool management
- Pool registration for combined_server.py
- RLS context management
- 5-priority fallback system

**DO NOT:**
- ❌ Change function signatures used by combined_server.py
- ❌ Remove `get_db_pool()` function
- ❌ Break the registration system
- ❌ Remove fallback priorities

**CAN DO:**
- ✅ Improve error handling
- ✅ Add new helper functions
- ✅ Optimize pool configuration

**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/app/db/connection.py`

---

### 6. `backend/app/core/agent_runtime.py` - Agent System
**Why Important:** Core of the pattern-driven architecture
**Contains:**
- Agent registration (9 agents)
- Capability routing (~70 capabilities)
- Retry mechanism with exponential backoff (3 retries: 1s, 2s, 4s)
- Request context management

**DO NOT:**
- ❌ Remove the singleton `_agent_runtime` instance
- ❌ Change capability registration interface
- ❌ Remove retry mechanism
- ❌ Break agent initialization

**CAN DO:**
- ✅ Fix bugs in capability execution
- ✅ Improve error handling
- ✅ Adjust retry delays/attempts
- ✅ Add new agents/capabilities

**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/app/core/agent_runtime.py`

**Note:** Phase 0 made compliance/observability imports optional. Observability code fully removed January 14, 2025 - maintain this pattern for any future optional dependencies.

---

### 7. `backend/app/core/pattern_orchestrator.py` - Pattern Execution
**Why Important:** Executes all 12 patterns
**Contains:**
- Template resolution
- Step-by-step execution
- State management
- Context building

**DO NOT:**
- ❌ Break template syntax ({{inputs.x}}, {{state.y}})
- ❌ Change pattern execution flow
- ❌ Remove error handling

**CAN DO:**
- ✅ Fix template resolution bugs
- ✅ Improve error messages
- ✅ Add debugging features

**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/app/core/pattern_orchestrator.py`

---

### 8. `backend/patterns/*.json` - Pattern Definitions
**Why Important:** Business logic is defined here (12 patterns)
**Contains:**
- Portfolio overview
- Macro analysis (4 cycles)
- Buffett ratings
- Risk analysis
- Transactions, alerts, reports

**DO NOT:**
- ❌ Change pattern structure without testing
- ❌ Remove required fields
- ❌ Break template syntax
- ❌ Delete patterns without updating UI

**CAN DO:**
- ✅ Fix bugs in pattern logic
- ✅ Add new steps
- ✅ Improve prompts

**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/patterns/`

---

### 9. `frontend/api-client.js` - API Communication
**Why Important:** How full_ui.html talks to backend
**Contains:**
- HTTP client with auth
- Request/response handling
- Error handling

**DO NOT:**
- ❌ Change export names
- ❌ Break the API client interface
- ❌ Remove error handling

**CAN DO:**
- ✅ Fix bugs
- ✅ Improve error messages
- ✅ Add new API methods

**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/frontend/api-client.js`

---

### 10. `backend/config/macro_indicators_defaults.json` - Macro Indicator Configuration
**Why Important:** Default values for ~40 economic indicators used in cycle detection
**Added:** November 2, 2025 (Commits d5d6945, 51b92f3)
**Size:** 640 lines

**Contains:**
- Configuration for STDC, LTDC, Empire, Civil cycle indicators
- Default values with metadata (source, confidence, validation ranges)
- Scenario configurations (recession, inflation shock, debt crisis)
- Alias mappings for indicator compatibility

**DO NOT:**
- ❌ Delete this file
- ❌ Break the JSON structure
- ❌ Remove required indicators without testing
- ❌ Change indicator keys without updating cycles.py
- ❌ Invalid JSON syntax (will break configuration loading)

**CAN DO:**
- ✅ Update indicator values (change "value" field)
- ✅ Update metadata (source, confidence, last_updated)
- ✅ Add new indicators (following schema)
- ✅ Adjust validation ranges
- ✅ Add new scenarios

**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/config/macro_indicators_defaults.json`

**Related Files:**
- Manager: `backend/app/services/indicator_config.py`
- Consumer: `backend/app/services/cycles.py`
- Docs: `backend/config/INDICATOR_CONFIG_README.md`

**Testing After Changes:**
```bash
# Validate JSON syntax
python3 -c "import json; json.load(open('backend/config/macro_indicators_defaults.json'))"

# Test configuration loading
python3 -c "from backend.app.services.indicator_config import get_config_manager; get_config_manager()"
```

---

## 🟢 TIER 3: SAFE TO MODIFY

These files can be changed, moved, or deleted without breaking deployment.

### Safe to Modify:
- ✅ All `test_*.py` files (test outputs)
- ✅ Documentation files (`*.md`)
- ✅ Scripts in `/scripts` directory
- ✅ Archive directories (`.legacy`, `.archive`)
- ✅ Analysis reports (`*_REPORT.md`, `*_REVIEW.md`)
- ✅ Git-related files (`.gitignore`)

### Safe to Delete:
- ✅ Test output files (`*.json`, `*.pdf` in root)
- ✅ Temporary files (`__pycache__`, `*.pyc`)
- ✅ Old migration files (if not needed)
- ✅ Unused scripts

---

## 🔒 Environment Variables (Required)

These environment variables MUST be set in Replit Secrets:

### Critical (App Won't Start):
- **DATABASE_URL** - PostgreSQL connection string
  - Format: `postgresql://user:pass@host:5432/dbname`
  - Replit provides this automatically

### Important (Features Won't Work):
- **AUTH_JWT_SECRET** - JWT token signing key
- **ANTHROPIC_API_KEY** - Claude API access (for AI features)
- **OPENAI_API_KEY** - OpenAI API access (optional)
- **POLYGON_API_KEY** - Market data access (optional)

### Optional (Nice to Have):
- **CORS_ORIGINS** - CORS configuration
- **ENVIRONMENT** - `development` or `production`
- **LOG_LEVEL** - Logging verbosity

---

## 📊 Port Configuration (DO NOT CHANGE)

**Primary Port:** 5000
**External Mapping:** 80
**Defined In:** `.replit` lines 34-35

```toml
[[ports]]
localPort = 5000
externalPort = 80
```

**Why Critical:**
- `combined_server.py` binds to port 5000 (hardcoded)
- Replit maps 5000 → 80 for public access
- Changing either breaks deployment

---

## 🚨 What Will Break Deployment

### Guaranteed to Break:
1. ❌ Renaming `combined_server.py`
2. ❌ Changing `.replit` run command
3. ❌ Moving `full_ui.html`
4. ❌ Changing port from 5000
5. ❌ Removing required packages from `requirements.txt`
6. ❌ Breaking database pool initialization
7. ❌ Removing agent runtime singleton
8. ❌ Breaking pattern orchestrator

### Likely to Break:
1. ⚠️ Changing `get_db_pool()` signature
2. ⚠️ Removing environment variables
3. ⚠️ Changing API endpoint paths without updating UI
4. ⚠️ Breaking pattern JSON structure
5. ⚠️ Changing agent registration interface

### Safe Changes:
1. ✅ Fixing bugs in existing code
2. ✅ Adding new endpoints/agents/patterns
3. ✅ Improving error handling
4. ✅ Updating documentation
5. ✅ Deleting test files

---

## ✅ Verification Checklist

Before deploying changes, verify:

### Code Compilation:
```bash
python3 -m py_compile combined_server.py
python3 -m py_compile backend/app/core/agent_runtime.py
python3 -m py_compile backend/app/core/pattern_orchestrator.py
python3 -m py_compile backend/app/db/connection.py
```

### Import Verification:
```bash
# Check for missing imports
grep -r "^from" backend/ | grep -v "__pycache__" | sort -u
grep -r "^import" backend/ | grep -v "__pycache__" | sort -u
```

### Critical Files Present:
```bash
# Verify all critical files exist
ls -la .replit combined_server.py full_ui.html
ls -la backend/requirements.txt
ls -la backend/app/db/connection.py
ls -la backend/app/core/agent_runtime.py
ls -la backend/app/core/pattern_orchestrator.py
ls -la backend/config/macro_indicators_defaults.json
```

### Port Configuration:
```bash
# Verify port 5000 in combined_server.py
grep "port.*5000" combined_server.py

# Verify port mapping in .replit
grep -A1 "localPort = 5000" .replit
```

---

## 📋 Phase 0-5 Cleanup Respected These Guardrails

The recent complexity reduction (Phase 0-5) successfully removed ~5000 lines of code while respecting ALL guardrails:

### What Was Changed:
- ✅ Made imports optional (graceful degradation)
- ✅ Removed unused modules (compliance, observability, redis)
- ✅ Fully removed observability code (January 14, 2025) - deleted observability/ directory, removed from requirements.txt
- ✅ Updated requirements.txt (removed 7 packages)
- ✅ Deleted unused files (4 files)

### What Was Protected:
- ✅ `.replit` - Unchanged
- ✅ `combined_server.py` - No structural changes
- ✅ `full_ui.html` - Unchanged
- ✅ Port 5000 - Unchanged
- ✅ Database pool - Enhanced with safety checks
- ✅ Agent runtime - Made more resilient
- ✅ Pattern orchestrator - Made more resilient

### Result:
- ✅ Application still compiles
- ✅ Deployment still works
- ✅ No ImportErrors
- ✅ All functionality preserved

---

## 🎯 Summary

**GOLDEN RULE:** If you're not sure if a file is critical, assume it is. Test changes on a branch first.

**Safe Workflow:**
1. Create a git branch
2. Make changes
3. Run verification checklist
4. Test compilation
5. Verify no ImportErrors
6. Only then commit to main

**When in Doubt:**
- Read this document
- Check git history
- Ask before deleting
- Test before committing

---

**Last Updated:** 2025-11-02
**Maintained By:** Claude Code (AI Assistant)
**Verified By:** Phase 0-5 cleanup (successful)
