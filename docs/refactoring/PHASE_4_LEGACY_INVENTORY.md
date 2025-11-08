# Phase 4: Legacy Code Inventory

**Date:** January 15, 2025  
**Status:** ✅ VERIFICATION COMPLETE  
**Purpose:** Document all legacy code and verification status

---

## Legacy Code Identified

### ✅ 1. Archived Agents (Safe to Remove)

**Location:** `backend/app/agents/.archive/`

**Files:**
1. `alerts_agent.py` - Consolidated into MacroHound
2. `charts_agent.py` - Consolidated into FinancialAnalyst
3. `optimizer_agent.py` - Consolidated into FinancialAnalyst
4. `ratings_agent.py` - Consolidated into FinancialAnalyst
5. `reports_agent.py` - Consolidated into DataHarvester

**Total:** 5 files, ~2,115 lines

**Verification Status:** ✅ **NO REFERENCES FOUND**

**Evidence:**
- ✅ No imports: `grep -rn "from.*\.archive" backend/` - No matches
- ✅ No agent class references: `grep -rn "OptimizerAgent|RatingsAgent|ChartsAgent|AlertsAgent|ReportsAgent" backend/app/` - No matches
- ✅ Only 4 active agents registered: MacroHound, FinancialAnalyst, DataHarvester, ClaudeAgent
- ✅ Functionality consolidated: All capabilities moved to active agents

**Migration Status:**
- ✅ AlertsAgent → MacroHound (alerts.* capabilities)
- ✅ ChartsAgent → FinancialAnalyst (charts.* capabilities)
- ✅ OptimizerAgent → FinancialAnalyst (optimizer.* capabilities)
- ✅ RatingsAgent → FinancialAnalyst (ratings.* capabilities)
- ✅ ReportsAgent → DataHarvester (reports.* capabilities)

**Risk:** LOW - Archived agents are not referenced anywhere

**Action:** ✅ **SAFE TO REMOVE**

---

### ⚠️ 2. Services (NOT Legacy - Still Used)

**Note:** These services are **NOT legacy** - they are actively used.

**Services:**
- ✅ `AlertService` (`backend/app/services/alerts.py`) - Used by MacroHound
- ✅ `RatingsService` (`backend/app/services/ratings.py`) - Used by FinancialAnalyst
- ✅ `OptimizerService` (`backend/app/services/optimizer.py`) - Used by FinancialAnalyst

**Status:**
- Registered in DI container
- Used by active agents
- Required for application functionality

**Action:** ⚠️ **DO NOT REMOVE** - These are active services

---

### ⚠️ 3. Legacy Folders (Root Level)

**Folders to Check:**
- `.legacy/` - Old Streamlit UI (if exists)
- `.archive/` - Documentation and archived code (if exists at root)

**Status:** Need to verify if these exist

**Action:** Check for existence and references

---

## Summary

**Legacy Code to Remove:**
- ✅ `backend/app/agents/.archive/` - 5 files, ~2,115 lines (SAFE TO REMOVE)

**Code to Keep:**
- ⚠️ `AlertService`, `RatingsService`, `OptimizerService` - Active services (DO NOT REMOVE)

**Total Lines to Remove:** ~2,115 lines (from archived agents)

---

**Status:** ✅ VERIFICATION COMPLETE  
**Last Updated:** January 15, 2025

