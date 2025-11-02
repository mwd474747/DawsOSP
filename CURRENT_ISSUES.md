# Current Issues & Recent Fixes

**Last Updated:** November 2, 2025
**Purpose:** Track active issues and recent fixes for multi-agent coordination

---

## 🟢 NO ACTIVE CRITICAL ISSUES

All previously blocking issues have been resolved as of November 2, 2025.

---

## ✅ RECENTLY FIXED (November 2, 2025)

### 1. Database Pool Registration - FIXED ✅

**Status:** RESOLVED (Commits 4d15246, e54da93)
**Date Fixed:** November 2, 2025
**Priority:** P0 (was blocking)

**Problem:**
- Module instance separation prevented agents from accessing database pool
- MacroHound cycle detection failing with AttributeError
- Circuit breaker opening after 5 failures
- `'NoneType' object has no attribute 'get_pool'` errors

**Root Cause:**
- Python creates separate module instances on import
- Pool registered in combined_server.py module instance
- Agents importing connection.py got NEW module instance
- Module-level variables (_external_pool) reset to None in new instance

**Solution:**
- Cross-module pool storage using `sys.modules['__dawsos_db_pool_storage__']`
- Pool stored once in sys.modules, accessible across all module imports
- Simplified connection.py from 600 lines to 382 lines
- Removed complex 5-priority fallback system

**Technical Details:**
- Implementation: `backend/app/db/connection.py` lines 35-56
- Historical Analysis: `DATABASE_OPERATIONS_VALIDATION.md`
- Architecture Documentation: `ARCHITECTURE.md` (pool architecture section)

**Impact:**
- ✅ MacroHound cycle detection now working
- ✅ All 9 agents can access database
- ✅ Circuit breaker no longer tripping
- ✅ Macro Cycles dashboard fully functional

---

### 2. Macro Cycles Parameter Bug - FIXED ✅

**Status:** RESOLVED (Commit 4f4e7bd)
**Date Fixed:** November 2, 2025
**Priority:** P1

**Problem:**
- TypeError in CyclesService method calls
- Parameter name mismatch: `asof_date` vs `as_of_date`
- Affected 10 locations in macro_hound.py

**Solution:**
- Corrected all parameter names to `as_of_date` (with underscore)
- Fixed in: detect_stdc_phase, detect_ltdc_phase, detect_empire_phase, detect_civil_phase
- Also fixed detect_current_regime() calls (removed incorrect parameter)

**Impact:**
- ✅ All 4 cycle types (STDC, LTDC, Empire, Civil) working
- ✅ Macro analysis patterns functioning correctly

---

### 3. Macro Indicator Configuration System - ADDED ✅

**Status:** IMPLEMENTED (Commits d5d6945, 51b92f3)
**Date Added:** November 2, 2025
**Priority:** P2 (improvement)

**What Changed:**
- **NEW:** `backend/config/macro_indicators_defaults.json` (640 lines)
- **NEW:** `backend/app/services/indicator_config.py` (471 lines)
- **NEW:** `backend/config/INDICATOR_CONFIG_README.md` (122 lines)
- **MODIFIED:** `backend/app/services/cycles.py` (177 lines changed)

**Benefits:**
- ✅ Centralized indicator management (~40 indicators)
- ✅ Update values without code changes
- ✅ Data quality tracking (source, confidence, validation)
- ✅ Scenario support (recession, inflation shock, debt crisis)
- ✅ Proper scaling and alias management

**Impact:**
- ✅ No breaking changes (additive only)
- ✅ All patterns still work
- ✅ Macro cycles dashboard unaffected
- ✅ Better maintainability

**Documentation:** See `backend/config/INDICATOR_CONFIG_README.md`

---

### 4. Database Connection AttributeError - FIXED ✅

**Status:** RESOLVED (Commit 271fe37)
**Date Fixed:** November 2, 2025
**Priority:** P0

**Problem:**
- Line 337 of connection.py called `await coordinator.get_pool()`
- Coordinator was None after redis_pool_coordinator module removed
- AttributeError when get_db_connection() called

**Solution:**
- Changed to use `get_db_pool()` instead (proper fallback logic)
- Later superseded by sys.modules solution (commits above)

---

### 5. Test Files Cleanup - COMPLETE ✅

**Status:** RESOLVED (Commit 58d5e46)
**Date:** November 2, 2025

**Actions:**
- Archived 4 test JSON files to `.archive/test-output-archived-20251102/`
- Removed Python cache files (`__pycache__`, `*.pyc`)
- Cleaned root directory of test output

---

## 📋 For Multi-Agent Coordination

### Before Starting Work:
1. ✅ **Check this file** - See what's already fixed
2. ✅ **Pull latest** - `git pull origin main`
3. ✅ **Check git log** - Review recent commits
4. ✅ **Read related docs** - Links below

### When Finding New Issues:
1. ✅ **Document here** - Add to this file with status "ACTIVE"
2. ✅ **Link to analysis** - Create or link to detailed doc
3. ✅ **Mark in progress** - Add "Working on: [agent-name]"
4. ✅ **Update when complete** - Move to "RECENTLY FIXED"

### Communication:
- **New issue found:** Add section below with 🔴 status
- **Starting work:** Add "IN PROGRESS - Agent [name]" note
- **Blocked:** Add "BLOCKED - [reason]" note
- **Fixed:** Move to "RECENTLY FIXED" section above

---

## 📚 Related Documentation

### For Technical Details:
- **Database Pool Fix:** `ARCHITECTURE.md` (pool architecture section)
- **Historical Analysis:** `DATABASE_OPERATIONS_VALIDATION.md` (root cause investigation)
- **Agent Context:** `.claude/PROJECT_CONTEXT.md` (current state)
- **Development Plan:** `ROADMAP.md` (completed and planned work)

### For Deployment:
- **Critical Guardrails:** `REPLIT_DEPLOYMENT_GUARDRAILS.md`
- **Deployment Guide:** `DEPLOYMENT.md`
- **Replit Setup:** `replit.md`

### For Architecture:
- **System Overview:** `ARCHITECTURE.md`
- **Product Spec:** `PRODUCT_SPEC.md`
- **Troubleshooting:** `TROUBLESHOOTING.md`

---

## 📊 Issue History

**Total Issues Resolved:** 4
**Improvements Added:** 1 (Macro Indicator Configuration System)
**Average Resolution Time:** <1 day
**Last Issue Fixed:** November 2, 2025 (Database pool)
**Last Improvement:** November 2, 2025 (Indicator configuration)
**Days Since Last Issue:** 0

---

**Note:** This document is the single source of truth for issue status.
Keep it updated for effective multi-agent coordination.
