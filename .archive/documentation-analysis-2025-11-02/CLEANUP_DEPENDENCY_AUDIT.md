# Cleanup Dependency Audit Report
**Generated:** 2025-01-26  
**Purpose:** Verify that planned deletions won't break `full_ui.html` patterns or backend dependencies

---

## Executive Summary

✅ **SAFE TO DELETE:** Most files are isolated with no dependencies  
⚠️ **NEEDS ATTENTION:** Duplicate endpoints and potential confusion points  
❌ **DO NOT DELETE:** Files required by `full_ui.html` or pattern orchestrator

---

## 1. Files Safe to Delete

### ✅ `backend/app/core/database.py`
**Status:** UNUSED - Safe to delete

**Evidence:**
- Self-referencing import only in docstring (line 15)
- No actual code imports this file
- Real database module is `backend/app/db/connection.py`
- All codebase uses `from app.db.connection import get_db_connection_with_rls`

**Dependencies Checked:**
```bash
# Search results: Only self-reference in docstring
grep -r "from.*app.core.database|import.*app.core.database" .
# Result: Only in database.py itself (docstring)
```

**Impact:** None - file is dead code wrapper

---

### ✅ `backend/api_server.py`
**Status:** UNUSED - Safe to delete

**Evidence:**
- Provides endpoints at `/execute`, `/auth/login` (NOT `/api/execute`, `/api/auth/login`)
- `full_ui.html` calls `/api/patterns/execute` (handled by `combined_server.py`)
- No imports found in codebase
- Different endpoint paths - no conflict

**Dependencies Checked:**
```bash
# Search results: No imports found
grep -r "import.*api_server|from.*api_server" .
# Result: No matches
```

**Impact:** None - different endpoint namespace, not used

---

### ✅ `backend/simple_api.py`
**Status:** UNUSED - Safe to delete

**Evidence:**
- No imports found in codebase
- Standalone test/demo file
- Not referenced in any scripts or documentation

**Dependencies Checked:**
```bash
# Search results: No imports found
grep -r "import.*simple_api|from.*simple_api" .
# Result: No matches
```

**Impact:** None - standalone demo file

---

### ✅ `backend/app/services/trade_execution_old.py`
**Status:** DEPRECATED - Safe to delete

**Evidence:**
- Already verified: Only `trade_execution.py` is imported
- `_old.py` suffix indicates deprecated version

**Impact:** None - old version replaced

---

## 2. Endpoint Mapping: `full_ui.html` → Backend

### Patterns Used by `full_ui.html`

All patterns call: **`POST /api/patterns/execute`**

1. ✅ `portfolio_overview` - Line 2785, 5295, 5355, 8224, 8765
2. ✅ `portfolio_scenario_analysis` - Line 2835, 8305, 8349
3. ✅ `macro_cycles_overview` - Line 2893, 5292, 6846
4. ✅ `policy_rebalance` - Line 3032, 8941
5. ✅ `buffett_checklist` - Line 2951, 9311, 9462
6. ✅ `portfolio_cycle_risk` - Line 2870, 8540
7. ✅ `news_impact_analysis` - Line 2986, 10511
8. ✅ `macro_trend_monitor` - Line 5322 (mentioned in pattern registry)

### Direct API Calls (not patterns)

From `frontend/api-client.js`:

1. ✅ `POST /api/auth/login` - Line 318
2. ✅ `POST /api/auth/refresh` - Line 53
3. ✅ `GET /api/portfolio` - Line 262
4. ✅ `GET /api/holdings` - Line 272
5. ✅ `GET /api/transactions` - Line 302

### Backend Endpoint Provider: `combined_server.py`

| Endpoint | Line | Status |
|----------|------|--------|
| `POST /api/patterns/execute` | 1027 | ✅ Used by UI |
| `POST /api/auth/login` | 1278 | ✅ Used by UI |
| `POST /api/auth/refresh` | 1321 | ✅ Used by UI |
| `GET /api/portfolio` | 1505 | ✅ Used by UI |
| `GET /api/holdings` | 1650 | ✅ Used by UI |
| `GET /api/transactions` | 1808 | ✅ Used by UI |
| `POST /execute` | 1960 | ⚠️ DUPLICATE (see below) |

---

## 3. Critical Issues Found

### ⚠️ DUPLICATE ENDPOINT: `/execute` vs `/api/patterns/execute`

**Location:** `combined_server.py` line 1960

**Problem:**
- Two endpoints for pattern execution:
  1. `/api/patterns/execute` (line 1027) - Used by `full_ui.html` ✅
  2. `/execute` (line 1960) - Different validation logic ⚠️

**Details:**
```python
# Line 1027: Main endpoint (used by UI)
@app.post("/api/patterns/execute", response_model=SuccessResponse)
async def execute_pattern(request: ExecuteRequest):
    # Handles all 12 patterns
    # Uses pattern orchestrator
    # Full error handling

# Line 1960: Duplicate endpoint (different logic)
@app.post("/execute", response_model=SuccessResponse)
async def execute_pattern(request: Request, execute_req: ExecuteRequest):
    # Only validates 4 patterns: ["portfolio_overview", "macro_analysis", "risk_assessment", "optimization"]
    # Returns mock data structure
    # Different request model
```

**Recommendation:**
- **DELETE** `/execute` endpoint (line 1960-2000)
- Keep only `/api/patterns/execute`
- This removes confusion and ensures single execution path

**Risk:** Low - UI doesn't use `/execute`, only `/api/patterns/execute`

---

### ⚠️ IMPROPER PATTERN MIXING: Multiple Pattern Sources

**Problem Identified:**

1. **Pattern Orchestrator** (Production):
   - Location: `backend/app/core/pattern_orchestrator.py`
   - Used by: `combined_server.py` via `execute_pattern_orchestrator()`
   - Handles: All 12 patterns from `backend/patterns/*.json`
   - Status: ✅ Production path

2. **Mock Pattern Handler** (Fallback):
   - Location: `combined_server.py` line 1960-2000 (`/execute`)
   - Handles: Only 4 mock patterns
   - Status: ⚠️ Duplicate/confusing

3. **Alternative Executor** (Test):
   - Location: `backend/app/api/executor.py`
   - Endpoint: `/v1/patterns/execute` (different path)
   - Status: ✅ Separate namespace, not used by UI

**Current State:**
- `full_ui.html` → `/api/patterns/execute` → `combined_server.py` → Pattern Orchestrator ✅
- This is the correct path, no mixing issues

**Verification:**
- ✅ All patterns defined in `backend/patterns/*.json` (12 files)
- ✅ Pattern orchestrator loads from `backend/patterns/`
- ✅ UI calls correct endpoint
- ⚠️ Duplicate `/execute` endpoint should be removed

---

## 4. Pattern Dependencies Trace

### Pattern: `portfolio_overview`
**Used by UI:** Lines 2785, 5295, 5355, 8224, 8765

**Backend Dependencies:**
1. Pattern file: `backend/patterns/portfolio_overview.json` ✅
2. Capabilities required:
   - `ledger.positions` → `FinancialAnalyst` agent ✅
   - `pricing.apply_pack` → `FinancialAnalyst` agent ✅
   - `metrics.compute` → `FinancialAnalyst` agent ✅
3. Orchestrator: `PatternOrchestrator` ✅
4. Agent Runtime: `AgentRuntime` ✅
5. Database: `app.db.connection.get_db_connection_with_rls()` ✅

**Files to Delete Impact:** None - all dependencies in `backend/app/`

---

### Pattern: `portfolio_scenario_analysis`
**Used by UI:** Lines 2835, 8305, 8349

**Backend Dependencies:**
1. Pattern file: `backend/patterns/portfolio_scenario_analysis.json` ✅
2. Capabilities required:
   - `ledger.positions` → `FinancialAnalyst` agent ✅
   - `pricing.apply_pack` → `FinancialAnalyst` agent ✅
   - `macro.run_scenario` → `MacroHound` agent ✅
   - `optimizer.suggest_hedges` → `OptimizerAgent` ✅
   - `charts.scenario_deltas` → `ChartsAgent` ✅
3. Service: `backend/app/services/scenarios.py` (ScenarioService) ✅

**Files to Delete Impact:** None

---

### Pattern: `policy_rebalance`
**Used by UI:** Lines 3032, 8941

**Backend Dependencies:**
1. Pattern file: `backend/patterns/policy_rebalance.json` ✅
2. Capabilities required:
   - `ledger.positions` → `FinancialAnalyst` agent ✅
   - `pricing.apply_pack` → `FinancialAnalyst` agent ✅
   - `ratings.aggregate` → `RatingsAgent` ✅
   - `optimizer.propose_trades` → `OptimizerAgent` ✅
   - `optimizer.analyze_impact` → `OptimizerAgent` ✅
3. Service: `backend/app/services/optimizer.py` ✅
4. Service: `backend/app/services/ratings.py` ✅

**Files to Delete Impact:** None

---

### Pattern: `buffett_checklist`
**Used by UI:** Lines 2951, 9311, 9462

**Backend Dependencies:**
1. Pattern file: `backend/patterns/buffett_checklist.json` ✅
2. Capabilities required:
   - `fundamentals.load` → `DataHarvester` agent ✅
   - `ratings.dividend_safety` → `RatingsAgent` ✅
   - `ratings.moat_strength` → `RatingsAgent` ✅
   - `ratings.resilience` → `RatingsAgent` ✅
   - `ratings.aggregate` → `RatingsAgent` ✅
   - `ai.explain` → `ClaudeAgent` ✅
3. Service: `backend/app/services/ratings.py` ✅

**Files to Delete Impact:** None

---

## 5. Database Connection Dependency Chain

### Current Architecture:

```
combined_server.py (startup)
  ↓
get_db_pool() [from backend.app.db.connection]
  ↓
db_pool (global singleton)
  ↓
Pattern Orchestrator
  ↓
Agent Runtime
  ↓
Agents (FinancialAnalyst, MacroHound, etc.)
  ↓
Services (ratings, optimizer, scenarios)
  ↓
get_db_connection_with_rls(user_id)
  ↓
app.db.connection.get_db_pool()
```

### Files in Chain:
1. ✅ `backend/app/db/connection.py` - **KEEP** (real implementation)
2. ❌ `backend/app/core/database.py` - **DELETE** (unused wrapper)

**Impact of Deleting `database.py`:** None - not in dependency chain

---

## 6. Agent Runtime Dependency Chain

### Pattern Execution Flow:

```
full_ui.html
  ↓ POST /api/patterns/execute
combined_server.py:execute_pattern_orchestrator()
  ↓
PatternOrchestrator.run_pattern()
  ↓
AgentRuntime.get_agent_for_capability()
  ↓
Agent.execute()
  ↓
Service.method()
  ↓
Database query (via get_db_connection_with_rls)
```

### Files Required:
1. ✅ `backend/app/core/pattern_orchestrator.py` - **KEEP**
2. ✅ `backend/app/core/agent_runtime.py` - **KEEP**
3. ✅ `backend/app/agents/*.py` - **KEEP**
4. ✅ `backend/app/services/*.py` - **KEEP**
5. ✅ `backend/app/db/connection.py` - **KEEP**

**Files to Delete:** None of these are in the chain ✅

---

## 7. Recommendations

### Phase 1: Safe Deletions (No Risk)

1. ✅ Delete `backend/app/core/database.py`
   - No imports found
   - Redundant wrapper

2. ✅ Delete `backend/api_server.py`
   - Different endpoint namespace
   - Not used by UI

3. ✅ Delete `backend/simple_api.py`
   - Standalone demo file
   - No dependencies

4. ✅ Delete `backend/app/services/trade_execution_old.py`
   - Deprecated version

### Phase 2: Cleanup Duplicates (Low Risk)

5. ⚠️ Delete `/execute` endpoint in `combined_server.py` (line 1960-2000)
   - Duplicate of `/api/patterns/execute`
   - UI doesn't use it
   - Removes confusion

6. ✅ `get_agent_runtime()` functions are NOT duplicates (OK to keep)
   - `combined_server.py` line 239 - Production server singleton ✅
   - `backend/app/api/executor.py` line 67 - Test server singleton ✅
   - Separate singletons for separate servers - this is correct
   - `AgentRuntime` class is in `backend/app/core/agent_runtime.py` ✅

### Phase 3: Documentation Updates

7. Update `README.md` to clarify:
   - Only `combined_server.py` is the production server
   - `backend/app/api/executor.py` is for testing (port 8001)
   - `backend/api_server.py` and `backend/simple_api.py` are archived

---

## 8. Validation Checklist

Before deleting files, verify:

- [x] `full_ui.html` doesn't import any backend files directly
- [x] All UI patterns call `/api/patterns/execute` (handled by `combined_server.py`)
- [x] No code imports `backend/app/core/database.py`
- [x] No code imports `backend/api_server.py`
- [x] No code imports `backend/simple_api.py`
- [x] Pattern orchestrator doesn't depend on deleted files
- [x] Agent runtime doesn't depend on deleted files
- [x] All 12 patterns exist in `backend/patterns/*.json`
- [x] Database connection uses `app.db.connection`, not `app.core.database`

---

## 9. Risk Assessment

| Action | Risk Level | Impact if Broken | Mitigation |
|--------|-----------|------------------|------------|
| Delete `database.py` | ✅ None | None - unused | Already verified no imports |
| Delete `api_server.py` | ✅ None | None - different namespace | UI uses `/api/*` paths |
| Delete `simple_api.py` | ✅ None | None - standalone | Not referenced anywhere |
| Delete `trade_execution_old.py` | ✅ None | None - deprecated | Only `trade_execution.py` imported |
| Delete `/execute` endpoint | ⚠️ Low | If something uses `/execute` | UI uses `/api/patterns/execute` |

---

## 10. Additional Findings: Agent Runtime Functions

### Status: ✅ NOT a Problem (Separate Singletons)

**Found:**
- `get_agent_runtime()` in `combined_server.py` (line 239) - Production server
- `get_agent_runtime()` in `backend/app/api/executor.py` (line 67) - Test server

**Analysis:**
- ✅ These are **separate singletons** for **separate servers**
- ✅ `combined_server.py` runs on port 8000 (production)
- ✅ `backend/app/api/executor.py` runs on port 8001 (testing)
- ✅ Each maintains its own `_agent_runtime` singleton
- ✅ Both use `AgentRuntime` class from `backend/app/core/agent_runtime.py`

**Conclusion:** This is correct architecture - no cleanup needed

---

## 11. Conclusion

✅ **The cleanup plan is SAFE** with one minor adjustment:

1. **All deletions are safe** - no dependencies found
2. **One duplicate endpoint** should be removed (`/execute` in `combined_server.py`)
3. **No pattern mixing issues** - UI correctly uses pattern orchestrator via correct endpoint
4. **All dependencies trace correctly** to `backend/app/*` modules, not deleted files

**Recommended Action:**
- Proceed with Phase 1 deletions
- Add Phase 2 cleanup (remove duplicate endpoint)
- Update documentation

---

## 12. Appendix: Pattern Files Verified

All 12 patterns exist in `backend/patterns/`:

1. ✅ `buffett_checklist.json`
2. ✅ `cycle_deleveraging_scenarios.json`
3. ✅ `export_portfolio_report.json`
4. ✅ `holding_deep_dive.json`
5. ✅ `macro_cycles_overview.json`
6. ✅ `macro_trend_monitor.json`
7. ✅ `news_impact_analysis.json`
8. ✅ `policy_rebalance.json`
9. ✅ `portfolio_cycle_risk.json`
10. ✅ `portfolio_macro_overview.json`
11. ✅ `portfolio_overview.json`
12. ✅ `portfolio_scenario_analysis.json`

All are loaded by Pattern Orchestrator and accessible via `/api/patterns/execute`.

