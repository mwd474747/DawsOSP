# Refactoring History Forensics - What Happened and Why

**Date:** 2025-11-08
**Investigator:** Claude Code (Historical Analysis)
**Purpose:** Trace the refactoring timeline, identify what was planned vs executed, and document anti-patterns created
**Verdict:** ⚠️ **PARTIAL SUCCESS** - Frontend completed, backend abandoned midway

---

## Executive Summary

After investigating the git history, refactoring documentation, and codebase structure, I've uncovered the complete timeline of what happened during DawsOS refactoring efforts. The story reveals **incomplete migration**, **abandoned plans**, and **unintentional creation of dual architectures**.

### Key Findings

1. **Frontend Refactoring**: ✅ Successfully completed on **November 7, 2025**
   - `full_ui.html` modularized into `frontend/*.js` files
   - HTML shell approach (2,216 lines) loading modular JS (9,984 lines)
   - **Result**: Hybrid frontend architecture (working in production)

2. **Backend Refactoring**: ❌ Started but never completed
   - `backend/combined_server.py` created on **November 7, 2025** (same day as frontend!)
   - Never integrated into `.replit` deployment
   - Root `combined_server.py` (6,718 lines) continued to be used and maintained
   - **Result**: Orphaned modular backend (never deployed)

3. **Anti-Patterns Created**:
   - Dual code paths (root monolith + modular backend)
   - Update confusion (which file to modify?)
   - 7+ critical bugs in modular frontend code (namespace issues, missing methods)
   - No migration plan documentation for backend

---

## Timeline Reconstruction

### Phase 0: Original Monolithic Architecture (Before Nov 6, 2025)

**Architecture:**
```
DawsOS (Original)
├── combined_server.py (monolithic backend)
└── full_ui.html (11,892-line monolithic frontend)
```

**Characteristics:**
- Single-file deployment
- Embedded React components in HTML
- All JavaScript inline (10,026 lines)
- CSS inline (1,837 lines)
- Fast iteration (no build step)

**Deployment:** `.replit` runs `python combined_server.py`

---

### Phase 1: Analysis and Planning (November 6, 2025)

**Document Created:** `UI_MONOLITH_REFACTORING_ANALYSIS.md`

**Analysis Findings:**
- 11,892-line `full_ui.html` could be safely refactored
- 15.5% CSS (1,837 lines) → Extract to `styles.css`
- 84.3% JavaScript (10,026 lines) → Extract to 7 modules
- 36 React components identified (20 pages, 15+ panels)
- `api-client.js` already extracted (403 lines) ✅ Successful precedent

**3-Phase Refactoring Plan:**
1. **Phase 1** (8-12h): Simple extractions - `styles.css`, `utils.js`, `panels.js`, `pages.js`
2. **Phase 2** (6-8h): Core extraction - `context.js`, `pattern-system.js`
3. **Phase 3** (4-6h): Shell & integration - Minimal HTML shell, testing

**Verdict:** ✅ CAN BE SAFELY REFACTORED (LOW-MEDIUM risk)

**Risk Assessment:**
- **Low risk**: CSS, utils, panels, pages (independent modules)
- **Medium risk**: Context, pattern system (tightly coupled, but extractable as units)
- **Mitigation**: Incremental approach, test after each extraction, rollback capability

---

### Phase 2: Frontend Modularization Execution (November 7, 2025)

**Commit:** `b235e8a` - "Phase 1: UI Monolith Refactoring Complete (Phases 1.2-1.4)"

**Files Created:**
1. ✅ `frontend/utils.js` (571 lines, 20 KB)
   - 14 utility functions and React components
   - `formatValue`, `getColorClass`, `useCachedQuery`, `useCachedMutation`
   - UI components: `ProvenanceWarningBanner`, `DataBadge`, `ErrorMessage`, etc.
   - IIFE pattern, exposed via `DawsOS.Utils` namespace

2. ✅ `frontend/panels.js` (907 lines, 40 KB)
   - 13 panel components for data visualization
   - `MetricsGridPanel`, `TablePanel`, `LineChartPanel`, `PieChartPanel`, etc.
   - Chart.js integration preserved
   - IIFE pattern, exposed via `DawsOS.Panels` namespace

3. ✅ `frontend/pages.js` (4,553 lines, 253 KB)
   - 20 page components
   - `DashboardPage`, `HoldingsPage`, `TransactionsPage`, etc.
   - IIFE pattern, exposed via `DawsOS.Pages` namespace

**Result:**
- `full_ui.html` reduced from 11,892 → 2,216 lines (81% reduction)
- Now serves as **HTML shell** loading modular JavaScript
- Modular JS files total: 9,984 lines across 16 files

**Deployment Impact:** ✅ **SUCCESSFUL** - `.replit` still runs root `combined_server.py`, which serves updated `full_ui.html`

---

### Phase 3: Backend Modularization Attempt (November 7, 2025)

**Commit:** `c204e12` - "Assistant checkpoint: Add provider registry and API key validation"

**User Prompt:**
> "you are on expert on API usage and data plumbing; review all the patterns related to api usage throughout the application and give me your hoenst findings; this app isnt in production yet, so security isnt a priority, but working is and having a clean understandabe and scalable system of API usage. The api should come from replit secrets"

**Files Created:**
1. ⚠️ `backend/combined_server.py` (269 lines)
   - Modular FastAPI server
   - Imports from `app.routers`, `app.services`, `app.core`
   - Clean separation of concerns
   - **NEVER DEPLOYED TO PRODUCTION**

2. ✅ `backend/app/integrations/provider_registry.py` (157 lines)
   - Centralized API client management
   - Singleton pattern for provider registry

**What Happened:**
- Backend modularization **started** with good intentions
- Modular `backend/combined_server.py` created with clean architecture
- **BUT**: Never integrated into `.replit` deployment config
- Root `combined_server.py` (6,718 lines) **continued to be actively maintained**

**Why It Failed:**
1. ❌ **No deployment migration** - `.replit` never updated to use `backend/combined_server.py`
2. ❌ **No migration plan** - No documentation on how to switch
3. ❌ **No feature parity check** - Unclear if modular version had all endpoints
4. ❌ **Root version kept working** - Easier to keep using monolith than migrate
5. ❌ **Imports from backend/app still worked** - Root server imports from modular services

---

### Phase 4: Continued Root Server Maintenance (Nov 7 - Nov 8, 2025)

**Root `combined_server.py` Commits:**
- `5003a16` - "phase 1 completion of major refractor v3" (Nov 7)
- `978dffa` - "fix: Add ScenarioService to error handling fallback list"
- `36b04dd` - "refactor: Add availability checks for RequestCtx and ScenarioService usage"
- `70ef558` - "refactor: Phase 5 - Remove remaining singleton factory functions"
- `0e51b00` - "refactor: Phase 3 & Phase 6 - None value validation and service usage updates" (Nov 8)

**Backend `backend/combined_server.py` Commits:**
- `c90f560` - "Constants extraction Phase 8 - Network domain COMPLETE" (Nov 7)
- **NO FURTHER UPDATES** (abandoned)

**Analysis:**
- Root server actively maintained for 2 days (Nov 7-8)
- Backend modular version **abandoned after 1 commit**
- Root server imports from `backend/app/` modules, so some modularization exists
- But the **deployment entry point** remained monolithic

---

### Phase 5: Frontend Bug Fixes (November 7-8, 2025)

**Commits:**
- `975dd89` - "Phase 2: Extract Context and Pattern Systems - COMPLETE"
- `4d9d7cd` - "CRITICAL BUG FIX: Correct module load order and dependency imports"
- `5db15b8` - "Phase 2.5: Extract core systems to modules - ARCHITECTURE FIX"
- `4e04dc3` - "CRITICAL FIX: Add missing Utils format functions and fix Panel validation"
- `41cf66c` - "CRITICAL FIX: Move CacheManager dependency check to prevent format function blocking"
- `521e603` - "CRITICAL FIX Phase 1.1.6: Fix namespace mapping in pages.js"
- `c204e15` - "EMERGENCY STABILITY FIX: Add component fallbacks to prevent crashes"
- `ffae36c` - "PHASE 2 COMPLETE: Aggressive namespace refactoring - technical debt eliminated"

**Bugs Encountered:**
1. ❌ **Module load order issues** - Dependencies loaded in wrong sequence
2. ❌ **Namespace mapping errors** - `TokenManager` vs `CacheManager` confusion
3. ❌ **Missing methods** - `isTokenExpired` exported but never defined
4. ❌ **Validation mismatches** - Validator expected generic HTTP methods (`get`, `post`) but actual API has domain-specific methods (`executePattern`, `getPortfolio`)
5. ❌ **Dependency blocking** - `CacheManager` dependency check prevented format functions from loading
6. ❌ **Component crashes** - Missing fallbacks for undefined components

**Documentation:** `REFACTORING_FORENSIC_ANALYSIS.md` created (identifies 7 critical bugs)

---

## What Was Supposed to Happen

### Original Frontend Plan (from UI_MONOLITH_REFACTORING_ANALYSIS.md)

**Phase 1: Simple Extractions (8-12 hours)**
1. ✅ Extract `styles.css` (1,837 lines) - **COMPLETED**
2. ✅ Extract `utils.js` (~300 lines) - **COMPLETED (571 lines)**
3. ✅ Extract `panels.js` (~2,000 lines) - **COMPLETED (907 lines)**
4. ✅ Extract `pages.js` (~4,000 lines) - **COMPLETED (4,553 lines)**

**Result:** `full_ui.html` reduced from 11,892 → ~3,000 lines (75% reduction) ✅

**Phase 2: Core Extraction (6-8 hours)**
1. ✅ Extract `context.js` (~500 lines) - **COMPLETED**
2. ✅ Extract `pattern-system.js` (~800 lines) - **COMPLETED**

**Result:** `full_ui.html` reduced from ~3,000 → ~1,700 lines (43% reduction) ✅

**Phase 3: Shell & Integration (4-6 hours)**
1. ✅ Create minimal `full_ui.html` (<200 lines) - **PARTIALLY COMPLETED** (2,216 lines, not <200)
2. ⚠️ Test all 20 pages - **PARTIALLY COMPLETED** (7+ critical bugs found)
3. ⚠️ Fix integration issues - **IN PROGRESS** (ongoing bug fixes)

**Result:** `full_ui.html` reduced to 2,216 lines (81% reduction from original 11,892) ⚠️

**Overall Frontend Status:**
- ✅ **Modularization**: COMPLETE (all modules extracted)
- ⚠️ **Integration**: PARTIAL (bugs remain but application works)
- ⚠️ **Shell Size**: Did not reach <200 lines goal (ended at 2,216 lines)

---

### Backend Plan (NEVER DOCUMENTED)

**No formal plan exists** for backend refactoring. Evidence suggests:

**Assumed Plan (Inferred):**
1. ⚠️ Create modular `backend/combined_server.py` importing from `app.routers` - **COMPLETED**
2. ❌ Update `.replit` to use `backend/combined_server.py` - **NEVER DONE**
3. ❌ Migrate all endpoints to modular routers - **NEVER DONE**
4. ❌ Test deployment - **NEVER DONE**
5. ❌ Archive root `combined_server.py` - **NEVER DONE**

**Result:** Backend migration **ABANDONED** after creating skeleton file

---

## What Actually Happened

### Frontend: Hybrid Architecture (SUCCESSFUL)

**Current State:**
```
Frontend (Hybrid Model)
├── full_ui.html (2,216 lines) - HTML shell
└── frontend/
    ├── api-client.js (403 lines)
    ├── cache-manager.js
    ├── context.js
    ├── error-handler.js
    ├── form-validator.js
    ├── logger.js
    ├── module-dependencies.js
    ├── namespace-validator.js
    ├── pages.js (4,553 lines)
    ├── panels.js (907 lines)
    ├── pattern-system.js
    ├── styles.css
    ├── utils.js (571 lines)
    └── version.js
```

**How It Works:**
1. User requests `/` from server
2. Root `combined_server.py` serves `full_ui.html`
3. `full_ui.html` loads modular `frontend/*.js` files via `<script>` tags
4. Modular JS files register components in `DawsOS.*` namespaces
5. Application renders using modular components

**Assessment:** ✅ **WORKING** (with some bugs)

---

### Backend: Dual Architecture (INCOMPLETE)

**Current State:**
```
Backend (Dual Architecture - BROKEN)
├── combined_server.py (6,718 lines) - ✅ PRODUCTION (root)
│   └── Imports from backend/app/* (modular services)
│
└── backend/
    ├── combined_server.py (269 lines) - ⚠️ ORPHANED (never used)
    └── app/
        ├── agents/ (modular agents)
        ├── services/ (modular services)
        ├── routers/ (modular routers)
        └── core/ (shared utilities)
```

**How It Works (Current):**
1. `.replit` runs `python combined_server.py` (root version)
2. Root server is 6,718-line monolith
3. Root server **DOES** import from `backend/app/*` modules
4. Modular `backend/combined_server.py` is **NEVER EXECUTED**

**Assessment:** ⚠️ **PARTIALLY MODULAR**
- Services layer: ✅ Modular (in `backend/app/services/`)
- Agents layer: ✅ Modular (in `backend/app/agents/`)
- Entry point: ❌ Still monolithic (root `combined_server.py`)

---

## Anti-Patterns Created

### 1. Dual Code Paths (Backend)

**Problem:** Two versions of `combined_server.py` exist
- Root `combined_server.py` (6,718 lines) - production
- `backend/combined_server.py` (269 lines) - orphaned

**Impact:**
- ❌ **Update confusion**: Developers don't know which file to modify
- ❌ **Wasted effort**: Time spent creating modular version never used
- ❌ **Tech debt**: Orphaned file adds confusion
- ❌ **Missed opportunity**: Clean modular architecture abandoned

**Why It Happened:**
- Backend modularization started but never finished
- No migration plan documented
- Root server kept working, so easier to maintain than migrate
- `.replit` never updated

**Fix:**
- Complete backend migration (update `.replit` to use `backend/combined_server.py`)
- OR delete orphaned `backend/combined_server.py` and document root as canonical

---

### 2. Namespace Confusion (Frontend)

**Problem:** Multiple namespace systems overlap
- `DawsOS.Core.API` (from `api-client.js`)
- `DawsOS.Utils` (from `utils.js`)
- `DawsOS.Panels` (from `panels.js`)
- `DawsOS.Pages` (from `pages.js`)
- Global `apiClient` variable
- Global `TokenManager` object

**Impact:**
- ❌ **Naming conflicts**: `TokenManager` vs `CacheManager` confusion
- ❌ **Validation errors**: Validator expects `get`/`post` methods that don't exist
- ❌ **Missing methods**: `isTokenExpired` exported but undefined
- ❌ **Brittle code**: Refactoring broke due to incorrect assumptions

**Why It Happened:**
- IIFE pattern with global namespace registration
- Incremental extraction without consistent naming
- Validator written with assumptions about API structure
- No schema validation for exported objects

**Fix:**
- Use ES6 modules instead of IIFE + global namespace
- Create TypeScript interfaces for namespace contracts
- Validate exports match expected schema

---

### 3. Module Load Order Dependencies (Frontend)

**Problem:** Modules have implicit load order dependencies
- `utils.js` must load before `panels.js` (needs `formatValue`)
- `context.js` must load before `pages.js` (needs `useUserContext`)
- `api-client.js` must load before `pattern-system.js` (needs `apiClient`)

**Impact:**
- ❌ **Brittle**: Changing `<script>` tag order breaks application
- ❌ **Hard to debug**: "X is not defined" errors far from root cause
- ❌ **No enforcement**: No build step to validate dependencies

**Why It Happened:**
- Used `<script>` tags instead of module bundler
- IIFE pattern doesn't declare dependencies
- No dependency graph documentation

**Fix:**
- Use ES6 modules with explicit `import`/`export`
- OR add dependency documentation to each file
- OR use module bundler (Webpack, Vite)

---

### 4. Missing Method Exports (Frontend)

**Problem:** Exported methods that don't exist
- `TokenManager.isTokenExpired` - exported but never defined
- `apiClient.get`, `apiClient.post`, `apiClient.delete` - expected but don't exist

**Impact:**
- ❌ **Runtime errors**: `TypeError: Cannot read property 'bind' of undefined`
- ❌ **Validation failures**: Namespace validator expects non-existent methods
- ❌ **Broken assumptions**: Code assumes generic HTTP client, but API is domain-specific

**Why It Happened:**
- Copy-paste from example code without verification
- Assumed methods existed without checking actual implementation
- Validator written based on assumptions, not actual code
- No runtime type checking (TypeScript would catch this)

**Fix:**
- Remove non-existent exports from `api-client.js`
- Update validator to check actual methods (not assumed)
- Add TypeScript for compile-time type checking

---

### 5. No Migration Rollback Plan (Both)

**Problem:** No documented rollback strategy if refactoring fails

**Impact:**
- ❌ **Risk**: If bugs found in production, no clear way to revert
- ❌ **Confidence**: Developers hesitant to deploy without safety net
- ❌ **Incomplete migration**: Backend stuck in limbo

**Why It Happened:**
- Focus on forward progress, not contingency planning
- Assumed refactoring would "just work"
- No staged rollout (all-or-nothing deployment)

**Fix:**
- Document rollback procedure (git tags, feature flags)
- Create staged rollout plan (10% → 50% → 100%)
- Test rollback procedure before full deployment

---

### 6. Undocumented Hybrid Architecture (Frontend)

**Problem:** `full_ui.html` is now a "hybrid shell" but this isn't documented

**Current Reality:**
- `full_ui.html` (2,216 lines) is **NOT** a monolith
- It's a **minimal shell** loading modular JS
- But nowhere is this architecture explained

**Impact:**
- ❌ **Confusion**: Independent agents think it's still monolithic (11,892 lines)
- ❌ **Wrong assessments**: Reviews judge based on outdated assumptions
- ❌ **Missed context**: Developers don't understand the design

**Why It Happened:**
- Refactoring documentation focused on "before" state
- No "after" architecture diagram created
- Assumed structure would be self-evident

**Fix:**
- Create architecture diagram showing hybrid model
- Update README with frontend architecture explanation
- Document `full_ui.html` as "shell that loads modules"

---

### 7. Incomplete Testing (Frontend)

**Problem:** 7+ critical bugs shipped despite refactoring being "complete"

**Bugs Found:**
1. `TokenManager.isTokenExpired` doesn't exist (line 401)
2. Validator expects `get`/`post`/`put`/`delete` methods (don't exist)
3. Module load order breaks application
4. `CacheManager` dependency blocks format functions
5. Missing component fallbacks cause crashes
6. Namespace mapping errors (`TokenManager` vs `clearToken`)
7. Multiple validation mismatches

**Impact:**
- ❌ **Quality**: Refactoring marked "complete" but broken
- ❌ **Trust**: Future refactorings questioned
- ❌ **Emergency fixes**: Multiple "CRITICAL FIX" commits needed

**Why It Happened:**
- No automated testing before declaring complete
- No manual smoke testing of all pages
- Assumed "it compiles" = "it works"
- Focus on extraction, not validation

**Fix:**
- Add E2E tests for all pages
- Create smoke test checklist
- Require testing before marking refactoring "complete"

---

## Root Cause Analysis

### Why Frontend Succeeded (Partially)

**Success Factors:**
1. ✅ **Clear plan**: UI_MONOLITH_REFACTORING_ANALYSIS.md documented 3-phase approach
2. ✅ **Precedent**: `api-client.js` extraction proved it was possible
3. ✅ **Incremental**: Extracted one module at a time
4. ✅ **Dependency graph**: Understood which components coupled
5. ✅ **Working prototype**: Application remained functional throughout

**Failure Factors:**
1. ❌ **No testing**: Bugs shipped because no validation
2. ❌ **Assumptions**: Exported methods that didn't exist
3. ❌ **Namespace confusion**: Multiple overlapping systems
4. ❌ **No rollback plan**: All-or-nothing deployment

**Overall:** 70% success (modular, but buggy)

---

### Why Backend Failed Completely

**Failure Factors:**
1. ❌ **No documented plan**: Backend migration never planned
2. ❌ **No deployment update**: `.replit` never changed
3. ❌ **Easier to abandon**: Root server kept working
4. ❌ **Split focus**: Frontend refactoring took all attention
5. ❌ **No forcing function**: Nothing required completing migration
6. ❌ **Partial benefits**: Root server imports from `backend/app/`, so some modularization exists

**Result:** Backend migration **abandoned** after skeleton created

---

## Lessons Learned

### What Worked

1. ✅ **Incremental extraction**: Extracting one module at a time reduced risk
2. ✅ **Precedent-driven**: Success with `api-client.js` proved approach viable
3. ✅ **HTML shell approach**: Hybrid model allows no-build-step deployment
4. ✅ **Namespace pattern**: IIFE + global namespace works (though has issues)
5. ✅ **Modular services**: `backend/app/services/` successfully modularized

### What Failed

1. ❌ **No testing before "complete"**: 7+ bugs shipped
2. ❌ **Assumptions without verification**: Exported non-existent methods
3. ❌ **No backend plan**: Migration started without roadmap
4. ❌ **No deployment update**: Modular backend never integrated
5. ❌ **No rollback plan**: All-or-nothing approach
6. ❌ **Undocumented architecture**: Hybrid model not explained

### What to Do Differently

#### For Future Refactorings:

1. **Document the plan FIRST**
   - Write migration roadmap before coding
   - Include rollback procedure
   - Define success criteria
   - Identify dependencies

2. **Test BEFORE marking complete**
   - Manual smoke test checklist
   - Automated E2E tests
   - Validate all exports exist
   - Check module load order

3. **Update deployment config**
   - If creating new entry point, update `.replit`
   - Test deployment before merging
   - Document which files are production

4. **Complete OR revert, no halfway**
   - Don't leave orphaned files
   - Either finish migration or delete skeleton
   - No dual code paths

5. **Document architecture changes**
   - Create "after" diagram
   - Update README
   - Explain hybrid models
   - Prevent future confusion

---

## Current Status Summary

### Frontend

**Status:** ✅ **WORKING** (with known bugs)

**Architecture:** Hybrid (HTML shell + modular JS)
- `full_ui.html` (2,216 lines) - shell
- `frontend/*.js` (9,984 lines) - modules

**Known Issues:**
- 7+ namespace/validation bugs (documented in REFACTORING_FORENSIC_ANALYSIS.md)
- Module load order dependencies
- Missing method exports

**Recommendation:**
- Fix known bugs (2-4 hours)
- Add E2E tests (4-8 hours)
- Document hybrid architecture (1 hour)

### Backend

**Status:** ⚠️ **PARTIALLY MODULAR** (incomplete migration)

**Architecture:** Dual (root monolith + modular services)
- Root `combined_server.py` (6,718 lines) - **PRODUCTION**
- `backend/combined_server.py` (269 lines) - **ORPHANED**
- `backend/app/*` - **MODULAR** (used by root server)

**Known Issues:**
- Orphaned modular entry point
- No migration plan
- Dual code paths
- Update confusion

**Recommendation:**
- **Option 1**: Complete migration (update `.replit`, test, deploy)
- **Option 2**: Delete orphaned file, document root as canonical
- **Option 3**: Document current hybrid state (interim)

---

## Recommendations

### Immediate (Fix Known Issues)

1. **Fix frontend namespace bugs** (2-4 hours)
   - Remove `TokenManager.isTokenExpired` export
   - Update validator to check actual methods
   - Fix module load order issues
   - Document in REFACTORING_FORENSIC_ANALYSIS_CORRECTED.md

2. **Document hybrid architecture** (1 hour)
   - Create architecture diagram
   - Update README
   - Explain frontend hybrid model
   - Clarify backend dual structure

### Short-Term (Complete or Revert)

3. **Backend migration decision** (1 hour planning + execution)
   - **Option A**: Complete migration to `backend/combined_server.py`
     - Update `.replit` to use backend version
     - Verify all endpoints exist
     - Test deployment
     - Archive root version
   - **Option B**: Delete orphaned `backend/combined_server.py`
     - Document root as canonical
     - Remove confusion
     - Accept modular services with monolithic entry point

4. **Add testing infrastructure** (4-8 hours)
   - E2E tests for all 20 pages
   - Smoke test checklist
   - Namespace validation tests
   - Module export validation

### Long-Term (Improve Architecture)

5. **Migrate to ES6 modules** (16-24 hours)
   - Replace IIFE pattern
   - Use native `import`/`export`
   - Add module bundler (Vite)
   - Eliminate namespace confusion

6. **Add TypeScript** (40-60 hours)
   - Type-safe namespaces
   - Compile-time validation
   - Better IDE support
   - Prevent "method doesn't exist" bugs

---

**Investigation Date:** 2025-11-08
**Investigated By:** Claude Code (Historical Forensics)
**Sources Analyzed:**
- Git history (`git log`, `git show`)
- Refactoring documentation (29 `*REFACTOR*.md` files)
- `.replit` deployment config
- File structure and imports
- Bug documentation (REFACTORING_FORENSIC_ANALYSIS.md)

**Key Learning:** Refactoring requires **complete plan → test → deploy** cycle. Partial migrations create worse problems than monoliths.
